# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-gridlayout."""
from __future__ import absolute_import, print_function

import json
from datetime import date, timedelta

import six
from flask import Blueprint, abort, current_app, jsonify, render_template, \
    request
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from invenio_cache import current_cache, current_cache_ext
from invenio_stats.utils import QueryCommonReportsHelper
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import NotFound
from invenio_db import db

from .api import WidgetItems
from .config import WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE
from .models import WidgetDesignPage
from .services import WidgetDataLoaderServices, WidgetDesignPageServices, \
    WidgetDesignServices, WidgetItemServices
from .utils import WidgetBucket, get_default_language, \
    get_elasticsearch_result_by_date, get_system_language, \
    get_widget_design_setting, get_widget_type_list, validate_upload_file

blueprint = Blueprint(
    'weko_gridlayout',
    __name__,
    template_folder='templates',
    static_folder='static',
)

blueprint_rss = Blueprint(
    'weko_gridlayout_rss',
    __name__,
    url_prefix='/rss',
    template_folder='templates',
    static_folder='static',
)

blueprint_api = Blueprint(
    'weko_gridlayout_api',
    __name__,
    url_prefix='/admin',
    template_folder='templates',
    static_folder='static',
)

blueprint_pages = Blueprint(
    'weko_gridlayout_pages',
    # 'weko_gridlayout',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/',
)


@blueprint_pages.before_app_first_request
def preload_pages():
    """Register all widget pages before the first application request."""
    try:
        _add_url_rule([page.url for page in WidgetDesignPage.get_all()])
    except Exception:
        current_app.logger.warn('Pages were not loaded.')
        raise


@blueprint.route("/")
@login_required
def index():
    """Render a basic view."""
    return render_template(
        "weko_gridlayout/index.html",
        module_name=_('weko-gridlayout'))


@blueprint_api.route('/load_repository', methods=['GET'])
@login_required
def load_repository():
    """Get Repository list, to display on the combobox on UI.

    :return: Example
        {
           'repositories': [
            {
                'id': 'repository id',
                'title': 'repository title'
            }
           ],
            'error': ''
        }
    """
    result = WidgetDesignServices.get_repository_list()
    return jsonify(result)


@blueprint_api.route(
    '/load_widget_design_setting', methods=['POST'])
@blueprint_api.route('/load_widget_design_setting/'
                     '<string:current_language>', methods=['POST'])
def load_widget_design_setting(current_language=''):
    """Load  Widget design setting from DB by repository id.

    :param current_language: The language default
    :return:
    """
    data = request.get_json()
    if not isinstance(data, dict):
        current_app.logger.error('Invalid request data.')
        abort(400)
    repository_id = data.get('repository_id', '')
    response = get_widget_design_setting(repository_id, current_language)
    return response


@blueprint_api.route(
    '/load_widget_design_page_setting/<string:page_id>', methods=['GET'])
@blueprint_api.route('/load_widget_design_page_setting/<string:page_id>/'
                     '<string:current_language>',
                     methods=['GET'])
# TODO: Temporary, must eventually make WidgetDesignPage have its own class
def load_widget_design_page_setting(page_id: str, current_language=''):
    """Load  Widget design page setting from DB by page id.

    :param page_id: Identifier of the page.
    :param current_language: The language default
    :return:
    """
    response = get_widget_design_setting("", current_language,
                                         page_id)
    return response


@blueprint_api.route('/load_widget_list_design_setting',
                     methods=['POST'])
@login_required
def load_widget_list_design_setting():
    """Get Widget list, to display on the Widget List panel on UI.

    :return: Example
            "widget-list": [
                {
                    "widgetId": "widget id",
                    "widgetLabel": "Widget label"
                }
            ],
            "error": ""
    """
    result = dict()
    data = request.get_json()
    if not isinstance(data, dict):
        current_app.logger.error('Invalid request data.')
        abort(400)
    repository_id = data.get('repository_id')
    lang_default = get_default_language()
    result["widget-list"] = WidgetDesignServices.get_widget_list(
        repository_id, lang_default)
    result["widget-preview"] = WidgetDesignServices.get_widget_preview(
        repository_id, lang_default)
    # result["page-list"] = WidgetDesignPageServices.get_page_list(
    #     repository_id, lang_default)

    result["error"] = result["widget-list"].get("error") or \
        result["widget-preview"].get("error")
    # result["page-list"].get("error")

    return jsonify(result)


@blueprint_api.route('/save_widget_layout_setting', methods=['POST'])
@login_required
# TODO: Allow this to be used for both or make a different path
def save_widget_layout_setting():
    """Save Widget design setting into DB.

    :return:
    """
    result = dict()

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    if not isinstance(data, dict):
        current_app.logger.error('Invalid request data.')
        abort(400)
    result = WidgetDesignServices.update_widget_design_setting(data)
    return jsonify(result)


@blueprint_api.route(
    '/load_widget_design_pages', methods=['POST'])
@blueprint_api.route(
    '/load_widget_design_pages/<string:lang>',
    methods=['POST']
)
@login_required
def load_widget_design_pages(lang=''):
    """Get widget page list for repository.

    :return: Example
            "page-list": [
                {
                    "id": "id",
                    "title": "Page title",
                }
            ],
            "error": ""
    """
    result = dict()
    data = request.get_json()
    if not isinstance(data, dict):
        current_app.logger.error('Invalid request data.')
        abort(400)
    repository_id = data.get('repository_id')
    lang_default = get_default_language()
    lang_default = lang_default.get('lang_code') if lang_default else None

    result["page-list"] = WidgetDesignPageServices.get_page_list(
        repository_id, lang or lang_default)
    result["error"] = result["page-list"].get("error")

    return jsonify(result)


@blueprint_api.route('/load_widget_design_page',
                     methods=['POST'])
@login_required
def load_widget_design_page():
    """Get widget page list for repository.

    :return: Example
            "data": {}
            "error": ""
    """
    data = request.get_json()
    if not isinstance(data, dict):
        current_app.logger.error('Invalid request data.')
        abort(400)
    page_id = data.get('page_id')
    repository_id = data.get('repository_id')
    return jsonify(WidgetDesignPageServices.get_page(page_id, repository_id))


@blueprint_api.route('/save_widget_design_page', methods=['POST'])
@login_required
def save_widget_design_page():
    """Save Widget design page into DB.

    :return: result JSON
    """
    result = dict()

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    if not isinstance(data, dict):
        current_app.logger.error('Invalid request data.')
        abort(400)
    result = WidgetDesignPageServices.add_or_update_page(data)
    return jsonify(result)


@blueprint_api.route('/delete_widget_design_page', methods=['POST'])
@login_required
def delete_widget_design_page():
    """Delete Widget design page into DB.

    :return: result JSON
    """
    result = dict()

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    if not isinstance(data, dict):
        current_app.logger.error('Invalid request data.')
        abort(400)
    result = WidgetDesignPageServices.delete_page(data.get('page_id'))
    return jsonify(result)


@blueprint_api.route('/load_widget_type', methods=['GET'])
@login_required
def load_widget_type():
    """Get Widget Type List."""
    results = get_widget_type_list()
    return jsonify(results)


@blueprint_api.route('/save_widget_item', methods=['POST'])
@login_required
def save_widget_item():
    """Save Language List."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg='Header Error')
    data = request.get_json()
    return jsonify(WidgetItemServices.save_command(data))


@blueprint_api.route('/delete_widget_item', methods=['POST'])
@login_required
def delete_widget_item():
    """Delete Language List."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg='Header Error')
    data = request.get_json()
    if not isinstance(data, dict):
        current_app.logger.error('Invalid request data.')
        abort(400)
    return jsonify(WidgetItemServices.delete_by_id(data.get('data_id')))


@blueprint_api.route('/get_account_role', methods=['GET'])
@login_required
def get_account_role():
    """Get Account role.

    :return:
    """
    role = WidgetItems().get_account_role()
    return jsonify(role)


@blueprint_api.route('/get_system_lang', methods=['GET'])
def get_system_lang():
    """Get system language.

    Returns:
        language -- list

    """
    result = get_system_language()
    return jsonify(result)


@blueprint_api.route('/get_new_arrivals/<int:widget_id>', methods=['GET'])
def get_new_arrivals_data(widget_id):
    """Get new arrivals data.

    Returns:
        json -- new arrivals data

    """
    data = jsonify(
        WidgetDataLoaderServices.get_new_arrivals_data(widget_id))

    return data


@blueprint_rss.route('/records', methods=['GET'])
def get_rss_data():
    """Get rss data based on term.

    Returns:
        xml -- RSS data

    """
    try:
        data = request.args
        term = int(data.get('term'))
        count = int(data.get('count'))
    except Exception:
        count = -1
        term = -1
    if term < 0 or count < 0:
        return WidgetDataLoaderServices.get_arrivals_rss(None, 0, 0)
    current_date = date.today()
    end_date = current_date.strftime("%Y-%m-%d")
    start_date = (current_date - timedelta(days=term)).strftime("%Y-%m-%d")
    rd = get_elasticsearch_result_by_date(start_date, end_date)
    return WidgetDataLoaderServices.get_arrivals_rss(rd, term, count)


@blueprint_api.route('/get_page_endpoints/<int:widget_id>', methods=['GET'])
@blueprint_api.route(
    '/get_page_endpoints/<int:widget_id>/<string:lang>', methods=['GET'])
def get_widget_page_endpoints(widget_id, lang=''):
    """Get menu pages urls and data."""
    if request.headers['Content-Type'] == 'application/json':
        lang_default = get_default_language()
        lang_default = lang_default.get('lang_code') if lang_default else None
        return jsonify(WidgetDataLoaderServices.get_widget_page_endpoints(
            widget_id, lang or lang_default)
        )
    else:
        return abort(403)


# Based on invenio_pages.views
def view_widget_page():
    """View user-created WidgetDesignPages."""

    from weko_theme.utils import get_community_id
    community_id, ctx = get_community_id(request.args)
    try:
        page = WidgetDesignPage.get_by_url(request.path)

        # Check if has main and if it does use different template
        from weko_theme.utils import get_weko_contents
        if page.settings:
            main_type = current_app.config['WEKO_GRIDLAYOUT_MAIN_TYPE']
            settings = json.loads(page.settings) \
                if isinstance(page.settings, str) else page.settings
            for item in settings:
                if item['type'] == main_type:
                    return render_template(
                        current_app.config['THEME_FRONTPAGE_TEMPLATE'],
                        page=page,
                        render_widgets=True,
                        **get_weko_contents(request.args))

        return render_template(
            page.template_name
            or current_app.config['WEKO_GRIDLAYOUT_DEFAULT_PAGES_TEMPLATE'],
            page=page,
            community_id=community_id,
            **ctx,)
    except Exception as e:
        current_app.logger.error(e)
        abort(404)


# Based on invenio_pages.views
# FIXME: Refactor with above
def handle_not_found(exception, **extra):
    """Custom blueprint exception handler."""
    assert isinstance(exception, NotFound)  # Only handle 404 errors

    from weko_theme.utils import get_community_id
    community_id, ctx = get_community_id(request.args)
    try:  # Check if the page exists
        page = WidgetDesignPage.get_by_url(request.path)
    except NoResultFound:
        page = None

    from weko_theme.utils import get_weko_contents
    if page:
        _add_url_rule(page.url)
        if page.settings:
            main_type = current_app.config['WEKO_GRIDLAYOUT_MAIN_TYPE']
            settings = json.loads(page.settings) \
                if isinstance(page.settings, str) else page.settings
            for item in settings:
                if item['type'] == main_type:
                    return render_template(
                        current_app.config['THEME_FRONTPAGE_TEMPLATE'],
                        page=page,
                        **get_weko_contents(request.args))

        return render_template(
            page.template_name
            or current_app.config['WEKO_GRIDLAYOUT_DEFAULT_PAGES_TEMPLATE'],
            page=page,
            community_id=community_id,
            **ctx,
        )
    elif extra['current_handler']:
        return extra['current_handler'](exception)
    else:
        return exception


# Based on invenio_pages.views
def _add_url_rule(url_or_urls):
    """Register URL rule to application URL map."""
    old = current_app._got_first_request
    # This is bit of cheating to overcome @flask.app.setupmethod decorator.
    current_app._got_first_request = False
    if isinstance(url_or_urls, six.string_types):
        url_or_urls = [url_or_urls]
    map(lambda url:
        current_app.add_url_rule(url, 'weko_gridlayout.view_widget_page',
                                 view_widget_page), url_or_urls)
    current_app._got_first_request = old


@blueprint_api.route('/access_counter_record/<string:repository_id>'
                     '/<path:path>/<string:current_language>', methods=['GET'])
def get_access_counter_record(repository_id, path, current_language):
    """Get access Top page value."""
    cached_data = current_cache.get('access_counter')
    if path == "main":
        widget_design_setting = WidgetDesignServices.get_widget_design_setting(
            repository_id, current_language or get_default_language())
    else:
        page_id = WidgetDesignPage.get_by_url("/"+path).id
        widget_design_setting = WidgetDesignPageServices.get_widget_design_setting(
            page_id, current_language or get_default_language())

    widget_ids = [
        str(widget.get("widget_id")) for widget in widget_design_setting.get("widget-settings", {})
        if widget.get("type") == WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE
    ]
    if len(widget_ids) == 0:
        return abort(404)

    if not cached_data or set(list(json.loads(cached_data.data).keys())) != set(widget_ids):
        result = {}
        # need to logic check
        if widget_design_setting.get('widget-settings'):
            for widget in widget_design_setting['widget-settings']:
                if str(widget.get('type')) == \
                        WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE:
                    if widget.get('count_start_date'):
                        start_date = widget.get('count_start_date')
                    else:
                        start_date = widget.get('created_date')

                    if start_date:
                        end_date = date.today().strftime("%Y-%m-%d")
                        top_view_total_by_widget_id = QueryCommonReportsHelper.get(
                            start_date=start_date, end_date=end_date,
                            event='top_page_access')
                        count = 0
                        for item in top_view_total_by_widget_id['all'].values():
                            count = count + int(item['count'])

                        top_view_total_by_widget_id['all'] = {} # clear all data
                        top_view_total_by_widget_id['all'].update(
                            {'count': count})
                        top_view_total_by_widget_id.update(
                            {'access_counter': widget.get('access_counter')})
                        if not result.get(widget.get('widget_id')):
                            result[widget.get('widget_id')] = {
                                start_date: top_view_total_by_widget_id}
                        else:
                            result[widget.get('widget_id')].update(
                                {start_date: top_view_total_by_widget_id})

        if result and len(result) > 0:
            cached_data = jsonify(result)
            ttl = current_app.config.get('INVENIO_CACHE_TTL', 50)
            current_cache.set('access_counter', cached_data, ttl)

    return cached_data


@blueprint.route('/widget/uploads/',
                 defaults={"community_id": 'Root Index'},
                 methods=["POST"]
                 )
@blueprint.route('/widget/uploads/<string:community_id>', methods=["POST"])
def upload_file(community_id):
    """Upload widget static file.

    :param community_id: community identifier.
    :return:
    """
    error_msg = validate_upload_file(community_id)
    file = request.files['file']
    if error_msg:
        return jsonify(msg=error_msg), 200
    return jsonify(
        WidgetBucket().save_file(file, file.filename, file.content_type,
                                 community_id)
    ), 200


@blueprint.route('/widget/uploaded/<string:filename>',
                 defaults={"community_id": 0}, methods=["GET"]
                 )
@blueprint.route('/widget/uploaded/<string:filename>/<string:community_id>',
                 methods=["GET"]
                 )
def uploaded_file(filename, community_id=0):
    """Get widget static file.

    :param filename: file name.
    :param community_id: community identifier.
    :return:
    """
    return WidgetBucket().get_file(filename, community_id)


@blueprint_api.route('/widget/unlock', methods=["POST"])
def unlocked_widget():
    """Get widget static file.

    :return:
    """
    data = request.get_json()
    if not isinstance(data, dict):
        current_app.logger.error('Invalid request data.')
        abort(400)
    widget_id = data.get('widget_id')
    if WidgetItemServices.unlock_widget(widget_id):
        return jsonify(success=True), 200
    else:
        return jsonify(success=False, msg=_("Can't unlock widget.")), 200

# @blueprint.teardown_request
# @blueprint_api.teardown_request
# @blueprint_pages.teardown_request
# @blueprint_rss.teardown_request
# def dbsession_clean(exception):
#     current_app.logger.debug("weko_gridlayout dbsession_clean: {}".format(exception))
#     if exception is None:
#         try:
#             db.session.commit()
#         except:
#             db.session.rollback()
#     db.session.remove()
