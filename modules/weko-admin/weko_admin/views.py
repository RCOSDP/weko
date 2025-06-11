# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Views for weko-admin."""

import calendar
import json
import sys
import time
from datetime import timedelta, datetime

from flask import Blueprint, Response, abort, current_app, flash, json, \
    jsonify, render_template, request
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from flask_wtf import Form,FlaskForm
from invenio_admin.proxies import current_admin
from invenio_stats.utils import QueryCommonReportsHelper
from invenio_db import db
from sqlalchemy.orm import session
from weko_accounts.utils import roles_required
from weko_records.models import SiteLicenseInfo
from weko_index_tree.utils import delete_index_trees_from_redis
from werkzeug.local import LocalProxy

from .api import send_site_license_mail
from .config import WEKO_ADMIN_PERMISSION_ROLE_REPO, \
    WEKO_ADMIN_PERMISSION_ROLE_SYSTEM
from .models import FacetSearchSetting, SessionLifetime, SiteInfo
from .utils import FeedbackMail, StatisticMail, UsageReport, \
    format_site_info_data, get_admin_lang_setting, \
    get_api_certification_type, get_current_api_certification, \
    get_init_display_index, get_initial_stats_report, get_selected_language, \
    get_unit_stats_report, is_exits_facet, \
    overwrite_the_memory_config_with_db, save_api_certification, \
    store_facet_search_query_in_redis, update_admin_lang_setting, \
    update_restricted_access, validate_certification, validation_site_info

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)


blueprint = Blueprint(
    'weko_admin',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/accounts/settings',
)

blueprint_api = Blueprint(
    'weko_admin',
    __name__,
    url_prefix='/admin',
    template_folder='templates',
    static_folder='static',
)


def _has_admin_access():
    """Use to check if a user has any admin access."""
    from invenio_access.utils import get_identity
    id = get_identity(current_user)
    permission = current_admin.permission_factory(current_admin.admin.index_view)
    # return (current_user.is_authenticated and current_admin \
    #     .permission_factory(current_admin.admin.index_view).can())
    return (current_user.is_authenticated and permission.allows(id))



@blueprint.route('/session/lifetime/<int:minutes>', methods=['GET'])
@login_required
def set_lifetime(minutes):
    """Update session lifetime in db.

    :param minutes:
    :return: Session lifetime updated message.
    """
    try:
        db_lifetime = SessionLifetime.get_validtime()
        if db_lifetime is None:
            db_lifetime = SessionLifetime(lifetime=minutes)
        else:
            db_lifetime.lifetime = minutes
        db_lifetime.create()
        _app.permanent_session_lifetime = timedelta(
            minutes=db_lifetime.lifetime)
        return jsonify(code=0, msg='Session lifetime was updated.')
    except BaseException:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
        return abort(400)


@blueprint.route('/session', methods=['GET', 'POST'])
@blueprint.route('/session/', methods=['GET', 'POST'])
@register_menu(
    blueprint, 'settings.lifetime',
    _('%(icon)s Session', icon='<i class="fa fa-cogs fa-fw"></i>'),
    visible_when=_has_admin_access,
    order=14
)
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.session',
    _('Session')
)
@login_required
def lifetime():
    """Loading session setting page.

    :return: Lifetime in minutes.
    """
    if not _has_admin_access():
        return abort(403)
    try:
        db_lifetime = SessionLifetime.get_validtime()
        if db_lifetime is None:
            db_lifetime = SessionLifetime(lifetime=30)

        form = FlaskForm(request.form)
        if request.method == 'POST' and form.validate():
            # Process forms
            form = request.form.get('submit', None)
            if form == 'lifetime':
                new_lifetime = request.form.get('lifetimeRadios', '30')
                db_lifetime.lifetime = int(new_lifetime)
                db_lifetime.create()
                _app.permanent_session_lifetime = timedelta(
                    minutes=db_lifetime.lifetime)
                flash(_('Session lifetime was updated.'), category='success')

        return render_template(
            current_app.config['WEKO_ADMIN_LIFETIME_TEMPLATE'],
            current_lifetime=str(db_lifetime.lifetime),
            map_lifetime=[('15', _('15 mins')),
                          ('30', _('30 mins')),
                          ('45', _('45 mins')),
                          ('60', _('60 mins')),
                          ('180', _('180 mins')),
                          ('360', _('360 mins')),
                          ('720', _('720 mins')),
                          ('1440', _('1440 mins'))],
            form=form
        )
    except ValueError as valueErr:
        current_app.logger.error(
            'Could not convert data to an integer: {0}'.format(valueErr))
        abort(400)
    except BaseException:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
        return abort(400)


@blueprint.route('/session/offline/info', methods=['GET'])
def session_info_offline():
    """Get session lifetime from app setting.

    :return: Session information offline in json.
    """
    current_app.logger.info('request session_info by offline')
    session_id = session.sid_s if hasattr(session, 'sid_s') else 'None'
    lifetime_str = str(current_app.config['PERMANENT_SESSION_LIFETIME'])
    return jsonify(user_id=current_user.get_id(),
                   session_id=session_id,
                   lifetime=lifetime_str,
                   _app_lifetime=str(_app.permanent_session_lifetime),
                   current_app_name=current_app.name)

@blueprint_api.route('/get_server_date',methods=['GET'])
def get_server_date():
    now = datetime.now()
    return jsonify(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        second=now.second
    )

@blueprint_api.route('/load_lang', methods=['GET'])
def get_lang_list():
    """Get Language List."""
    results = dict()
    try:
        results['results'] = get_admin_lang_setting()
        results['msg'] = 'success'
    except Exception as e:
        results['msg'] = str(e)

    return jsonify(results)


@blueprint_api.route('/save_lang', methods=['POST'])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def save_lang_list():
    """Save Language List."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg='Header Error')
    result = 'success'
    data = request.get_json()
    for lang_code in [lang["lang_code"] for lang in data if not lang["is_registered"]]:
        delete_index_trees_from_redis(lang_code)
        
    try:
        update_admin_lang_setting(data)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        result = str(e)

    return jsonify(msg=result)


@blueprint_api.route('/get_selected_lang', methods=['GET'])
def get_selected_lang():
    """Get selected language."""
    try:
        result = get_selected_language()
    except Exception as e:
        result = {'error': str(e)}
    return jsonify(result)


@blueprint_api.route('/get_api_cert_type', methods=['GET'])
def get_api_cert_type():
    """Get list of supported API, to display on the combobox on UI.

    :return: Example
    {
        'result':[
        {
            'api_code': 'DOI',
            'api_name': 'CrossRef API'
        },
        {
            'api_code': 'AMA',
            'api_name': 'Amazon'
        }],
        'error':''
    }
    """
    result = {
        'results': '',
        'error': ''
    }
    try:
        result['results'] = get_api_certification_type()
    except Exception as e:
        result['error'] = str(e)
    return jsonify(result)


@blueprint_api.route('/get_curr_api_cert/<string:api_code>', methods=['GET'])
def get_curr_api_cert(api_code=''):
    """Get current API certification data, to display on textbox on UI.

    :param api_code: API code
    :return:
    {
        'results':
        {
            'api_code': 'DOI',
            'api_name': 'CrossRef API',
            'cert_data':
            {
                'account': 'abc@xyz.com'
            }
        },
        'error':''
    }
    """
    result = {
        'results': '',
        'error': ''
    }
    try:
        result['results'] = get_current_api_certification(api_code)
    except Exception as e:
        result['error'] = str(e)
    return jsonify(result)


@blueprint_api.route('/save_api_cert_data', methods=['POST'])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM])
def save_api_cert_data():
    """Save api certification data to database.

    :return: Example
    {
        'results': true // true if save successfully
        'error':''
    }
    """
    result = dict()

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    api_code = data.get('api_code', '')
    cert_data = data.get('cert_data', '')
    if not cert_data:
        result['error'] = _(
            'Account information is invalid. Please check again.')
    elif validate_certification(cert_data):
        result = save_api_certification(api_code, cert_data)
    else:
        result['error'] = _(
            'Account information is invalid. Please check again.')

    return jsonify(result)


@blueprint_api.route('/get_init_selection/<string:selection>', methods=['GET'])
def get_init_selection(selection=""):
    """Get initial data for unit and target.

    :param selection:
    """
    result = dict()
    try:
        if selection == 'target':
            result = get_initial_stats_report()
        else:
            result = get_unit_stats_report(selection)
    except Exception as e:
        result['error'] = str(e)

    return jsonify(result)


@blueprint_api.route("/search_email", methods=['POST'])
@login_required
def get_email_author():
    """Get all authors."""
    data = request.get_json()
    result = FeedbackMail.search_author_mail(data)

    return jsonify(result)


@blueprint_api.route('/update_feedback_mail', methods=['POST'])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def update_feedback_mail():
    """API allow to save feedback mail setting.

    Returns:
        json -- response result

    """
    result = {
        'success': '',
        'error': ''
    }
    root_url = request.url_root
    root_url = str(root_url).replace('/api/', '')
    data = request.get_json()
    response = FeedbackMail.update_feedback_email_setting(
        data.get('data', ''),
        data.get('is_sending_feedback', False),
        root_url)

    if not response.get('error'):
        result['success'] = True
        return jsonify(result)
    else:
        result['error'] = response.get('error')
        result['success'] = False
        return jsonify(result)


@blueprint_api.route('/get_feedback_mail', methods=['POST'])
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def get_feedback_mail():
    """API allow get feedback email setting.

    Returns:
        json -- email settings

    """
    result = {
        'data': '',
        'is_sending_feedback': '',
        'error': ''
    }

    data = FeedbackMail.get_feed_back_email_setting()
    if data.get('error'):
        result['error'] = data.get('error')
        return jsonify(result)
    result['data'] = data.get('data')
    result['is_sending_feedback'] = data.get('is_sending_feedback')
    return jsonify(result)


@blueprint_api.route('/get_send_mail_history', methods=['GET'])
def get_send_mail_history():
    """API allow to get send mail history.

    Returns:
        json -- response list mail data if no error occurs

    """
    try:
        data = request.args
        page = int(data.get('page'))
    except Exception as ex:
        current_app.logger.debug("Cannot convert parameter: {}".format(ex))
        page = 1
    result = FeedbackMail.load_feedback_mail_history(page)
    return jsonify(result)


@blueprint_api.route('/get_failed_mail', methods=['POST'])
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def get_failed_mail():
    """Get list failed mail.

    Returns:
        json -- List data if no error occurs

    """
    try:
        data = request.form
        page = int(data.get('page'))
        history_id = int(data.get('id'))
    except Exception as ex:
        current_app.logger.debug("Cannot convert parameter: {}".format(ex))
        page = 1
        history_id = 1
    result = FeedbackMail.load_feedback_failed_mail(history_id, page)
    return jsonify(result)


@blueprint_api.route('/resend_failed_mail', methods=['POST'])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def resend_failed_mail():
    """Resend failed mail.

    :return:
    """
    data = request.get_json()
    history_id = data.get('history_id')
    result = {
        'success': True,
        'error': ''
    }
    try:
        mail_data = FeedbackMail.get_mail_data_by_history_id(history_id)
        StatisticMail.send_mail_to_all(
            mail_data.get('data'),
            mail_data.get('stats_date')
        )
        FeedbackMail.update_history_after_resend(history_id)
    except Exception as ex:
        current_app.logger.debug("Cannot resend mail:{}".format(ex))
        result['success'] = False
        result['error'] = 'Request package is invalid'
    return jsonify(result)


@blueprint_api.route('/sitelicensesendmail/send/<start_month>/<end_month>',
                     methods=['POST'])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def manual_send_site_license_mail(start_month, end_month):
    """Send site license mail by manual."""
    send_list = SiteLicenseInfo.query.filter_by(receive_mail_flag='T').all()
    if send_list:
        start_date = start_month + '-01'
        _, lastday = calendar.monthrange(int(end_month[:4]),
                                         int(end_month[5:]))
        end_date = end_month + '-' + str(lastday).zfill(2)

        agg_date = start_month.replace('-', '.') + '-' + \
            end_month.replace('-', '.')
        res = QueryCommonReportsHelper.get(start_date=start_date,
                                           end_date=end_date,
                                           event='site_access')
        for s in send_list:
            mail_list = s.mail_address.split('\n')
            send_flag = False
            for r in res['institution_name']:
                if s.organization_name == r['name']:
                    send_site_license_mail(r['name'], mail_list, agg_date, r)
                    send_flag = True
                    break
            if not send_flag:
                data = {'file_download': 0,
                        'file_preview': 0,
                        'record_view': 0,
                        'search': 0,
                        'top_view': 0}
                send_site_license_mail(s.organization_name,
                                       mail_list, agg_date, data)

        return 'finished'


@blueprint_api.route('/update_site_info', methods=['POST'])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def update_site_info():
    """Update site info.

    :return: result

    """
    site_info = request.get_json()
    format_data = format_site_info_data(site_info)
    validate = validation_site_info(format_data)
    
    if validate.get('error'):
        return jsonify(validate)
    else:
        site_info = SiteInfo.update(format_data)
        overwrite_the_memory_config_with_db(current_app, site_info)
        return jsonify(format_data)


@blueprint_api.route('/get_site_info', methods=['GET'])
@login_required
def get_site_info():
    """Get site info.

    :return: result

    """
    site_info = SiteInfo.get()

    result = dict()
    if not site_info:
        try:
            result['google_tracking_id_user'] = current_app.config[
                'GOOGLE_TRACKING_ID_USER']
        except BaseException:
            pass
        return jsonify(result)

    result['copy_right'] = site_info.copy_right
    result['description'] = site_info.description
    result['keyword'] = site_info.keyword
    result['favicon'] = site_info.favicon
    result['favicon_name'] = site_info.favicon_name
    result['site_name'] = site_info.site_name
    result['notify'] = site_info.notify
    result['google_tracking_id_user'] = site_info.google_tracking_id_user
    
    if site_info.ogp_image and site_info.ogp_image_name:
        ts = time.time()
        result['ogp_image'] = request.host_url + \
            'api/admin/ogp_image'
        result['ogp_image_name'] = site_info.ogp_image_name
    
    return jsonify(result)


@blueprint_api.route('/favicon', methods=['GET'])
def get_avatar():
    """Get favicon.

    :return: result

    """
    import base64
    import io

    from werkzeug import FileWrapper
    site_info = SiteInfo.get()
    if not site_info:
        return jsonify({})
    favicon = site_info.favicon.split(',')[1]
    favicon = base64.b64decode(favicon)
    b = io.BytesIO(favicon)
    w = FileWrapper(b)
    return Response(b, mimetype="image/x-icon", direct_passthrough=True)


@blueprint_api.route('/ogp_image', methods=['GET'])
def get_ogp_image():
    """Get ogp image.

    :return: result

    """
    from invenio_files_rest.models import FileInstance

    site_info = SiteInfo.get()
    if not site_info or not( site_info.ogp_image and site_info.ogp_image_name):
        return jsonify({})
    file_instance = FileInstance.get_by_uri(site_info.ogp_image)
    if not file_instance:
        return jsonify({})
    return file_instance.send_file(
        site_info.ogp_image_name,
        mimetype='application/octet-stream',
        as_attachment=True
    )


@blueprint_api.route('/search/init_display_index/<string:selected_index>',
                     methods=['GET'])
def get_search_init_display_index(selected_index=None):
    """Get search init display index.

    :param selected_index: selected index.
    :return:
    """
    indexes = get_init_display_index(selected_index)
    return jsonify(indexes=indexes)


@blueprint_api.route("/restricted_access/save", methods=['POST'])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def save_restricted_access():
    """Save registered access settings.

    :return:
    """
    result = {
        "status": True,
        "msg": _("Restricted Access was successfully updated.")
    }
    restricted_access = request.get_json()
    if not update_restricted_access(restricted_access):
        result['status'] = False
        result['msg'] = _("Could not save data.")
    return jsonify(result), 200


@blueprint_api.route("/restricted_access/get_usage_report_activities",
                     methods=["GET", "POST"])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def get_usage_report_activities():
    """Get usage report activities.

    :return: [json, int]: Usage report activity.
    """
    if request.method == "POST":
        json_data = request.get_json()
        activities_id = json_data.get('activity_ids')
        page = json_data.get('page', 1)
        size = json_data.get('size', 25)
    else:
        data = request.args
        page = data.get('page', 1)
        size = data.get('size', 25)
        activities_id = None
    usage_report = UsageReport()
    result = usage_report.get_activities_per_page(activities_id, int(size),
                                                  int(page))
    return jsonify(result), 200


@blueprint_api.route("/restricted_access/send_mail_reminder", methods=["POST"])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def send_mail_reminder_usage_report():
    """Send email to request user for register usage report.

    :return: [json, int]: Send mail status.
    """
    json_data = request.get_json()
    result = False
    if json_data and json_data.get('activity_ids'):
        activities_id = json_data.get('activity_ids')
        usage_report = UsageReport()
        result = usage_report.send_reminder_mail(activities_id, forced_send=True)

    return jsonify(status=result), 200


@blueprint_api.route("/facet-search/save", methods=['POST'])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def save_facet_search():
    """Save facet search.

    :return:
    """
    result = {
        "status": True,
        "msg": _("Success")
    }
    data = request.get_json()
    id = data.pop('id', '')
    if not is_exits_facet(data, id):
        if id and len(id) > 0:
            # Edit facet search.
            if not FacetSearchSetting.update_by_id(id, data):
                result['status'] = False
                result['msg'] = _("Failed to update due to server error.")
        else:
            # Create facet search.
            if not FacetSearchSetting.create(data):
                result['status'] = False
                result['msg'] = _("Failed to create due to server error.")
    else:
        result['status'] = False
        result['msg'] = _('The item name/mapping is already exists.'
                          + ' Please input other faceted item/mapping.')
        # Store query facet search in redis.
    store_facet_search_query_in_redis()
    return jsonify(result), 200


@blueprint_api.route("/facet-search/remove", methods=['POST'])
@login_required
@roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
                 WEKO_ADMIN_PERMISSION_ROLE_REPO])
def remove_facet_search():
    """Remove facet search.

    :return:
    """
    result = {
        "status": True,
        "msg": _("Success")
    }
    data = request.get_json()
    id_facet = json.loads(json.dumps(data))["id"]
    if id_facet:
        if not FacetSearchSetting.delete(id_facet):
            result['status'] = False
            result['msg'] = _("Failed to delete due to server error.")
    else:
        result['status'] = False
        result['msg'] = _("Failed to delete due to server error.")
    # Store query facet search in redis.
    store_facet_search_query_in_redis()
    return jsonify(result), 200


@blueprint.teardown_request
@blueprint_api.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_admin dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()