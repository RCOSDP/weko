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

"""Blueprint for weko-records-ui."""

import redis
import six
import werkzeug
from flask import Blueprint, abort, current_app, flash, jsonify, \
    make_response, redirect, render_template, request, url_for
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from flask_security import current_user
from invenio_cache import current_cache
from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from invenio_files_rest.views import ObjectResource, check_permission, \
    file_downloaded
from invenio_i18n.ext import current_i18n
from invenio_oaiserver.response import getrecord
from invenio_records_ui.signals import record_viewed
from invenio_records_ui.utils import obj_or_import_string
from lxml import etree
from simplekv.memory.redisstore import RedisStore
from weko_deposit.api import WekoIndexer, WekoRecord
from weko_index_tree.models import IndexStyle
from weko_index_tree.utils import get_index_link_list
from weko_records.serializers import citeproc_v1
from weko_search_ui.api import get_search_detail_keyword
from weko_workflow.api import WorkActivity
from weko_workflow.models import ActionStatusPolicy

from weko_records_ui.models import InstitutionName
from weko_records_ui.utils import check_items_settings

from .ipaddr import check_site_license_permission
from .models import PDFCoverPageSettings
from .permissions import check_created_id, check_file_download_permission, \
    check_original_pdf_download_permission
from .utils import get_billing_file_download_permission, get_groups_price, \
    get_min_price_billing_file_download, get_record_permalink
from .utils import restore as restore_imp
from .utils import soft_delete as soft_delete_imp

blueprint = Blueprint(
    'weko_records_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)


def publish(pid, record, template=None, **kwargs):
    r"""Record publish  status change view.

    Change record publish status with given status and renders record export
    template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :return: The rendered template.
    """
    from weko_deposit.api import WekoIndexer
    status = request.values.get('status')
    publish_status = record.get('publish_status')
    if not publish_status:
        record.update({'publish_status': (status or '0')})
    else:
        record['publish_status'] = (status or '0')

    record.commit()
    db.session.commit()

    indexer = WekoIndexer()
    indexer.update_publish_status(record)

    return redirect(url_for('.recid', pid_value=pid.pid_value))


def export(pid, record, template=None, **kwargs):
    r"""Record serialization view.

    Serializes record with given format and renders record export template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :return: The rendered template.
    """
    formats = current_app.config.get('RECORDS_UI_EXPORT_FORMATS', {}).get(
        pid.pid_type)
    schema_type = request.view_args.get('format')
    fmt = formats.get(schema_type)

    if fmt is False:
        # If value is set to False, it means it was deprecated.
        abort(410)
    elif fmt is None:
        abort(404)
    else:
        if 'json' not in schema_type and 'bibtex' not in schema_type:
            record.update({'@export_schema_type': schema_type})

        serializer = obj_or_import_string(fmt['serializer'])
        data = serializer.serialize(pid, record)
        if isinstance(data, six.binary_type):
            data = data.decode('utf8')

        response = make_response(data)

        if 'json' in schema_type or 'bibtex' in schema_type:
            response.headers['Content-Type'] = 'text/plain'
        else:
            response.headers['Content-Type'] = 'text/xml'

        return response


@blueprint.app_template_filter('get_image_src')
def get_image_src(mimetype):
    """Get image src by file type.

    :param mimetype:
    :return src: dict
    """
    if 'text/' in mimetype:
        src = 'icon_16_txt.jpg'
    elif 'officedocument.wordprocessingml' in mimetype:
        src = 'icon_16_doc.jpg'
    elif 'officedocument.spreadsheetml' in mimetype:
        src = 'icon_16_xls.jpg'
    elif 'officedocument.presentationml' in mimetype:
        src = 'icon_16_ppt.jpg'
    elif 'msword' in mimetype:
        src = 'icon_16_doc.jpg'
    elif 'excel' in mimetype:
        src = 'icon_16_xls.jpg'
    elif 'powerpoint' in mimetype:
        src = 'icon_16_ppt.jpg'
    elif 'zip' in mimetype or 'rar' in mimetype:
        src = 'icon_16_zip.jpg'
    elif 'audio/' in mimetype:
        src = 'icon_16_music.jpg'
    elif 'xml' in mimetype:
        src = 'icon_16_xml.jpg'
    elif 'image/' in mimetype:
        src = 'icon_16_picture.jpg'
    elif 'pdf' in mimetype:
        src = 'icon_16_pdf.jpg'
    elif 'video/' in mimetype:
        if 'flv' in mimetype:
            src = 'icon_16_flash.jpg'
        else:
            src = 'icon_16_movie.jpg'
    else:
        src = 'icon_16_others.jpg'

    return '/static/images/icon/' + src


@blueprint.app_template_filter('get_license_icon')
def get_license_icon(type):
    """Get License type icon.

    :param type:
    :return:
    """
    lic_dict = {
        'license_0': _('Creative Commons : Attribution'),
        'license_1': _('Creative Commons : Attribution - ShareAlike'),
        'license_2': _('Creative Commons : Attribution - NoDerivatives'),
        'license_3': _('Creative Commons : Attribution - NonCommercial'),
        'license_4': _('Creative Commons : Attribution - NonCommercial - '
                       'ShareAlike'),
        'license_5': _('Creative Commons : Attribution - NonCommercial - '
                       'NoDerivatives'),
    }

    href_dict = {
        'license_0': 'https://creativecommons.org/licenses/by/4.0/deed.ja',
        'license_1': 'https://creativecommons.org/licenses/by-sa/4.0/deed.ja',
        'license_2': 'https://creativecommons.org/licenses/by-nd/4.0/deed.ja',
        'license_3': 'https://creativecommons.org/licenses/by-nc/4.0/deed.ja',
        'license_4': 'https://creativecommons.org/'
                     'licenses/by-nc-sa/4.0/deed.ja',
        'license_5': 'https://creativecommons.org/'
                     'licenses/by-nc-nd/4.0/deed.ja',
    }

    if 'license_0' in type:
        src = '88x31(1).png'
        lic = lic_dict.get('license_0')
        href = href_dict.get('license_0')
    elif 'license_1' in type:
        src = '88x31(2).png'
        lic = lic_dict.get('license_1')
        href = href_dict.get('license_1')
    elif 'license_2' in type:
        src = '88x31(3).png'
        lic = lic_dict.get('license_2')
        href = href_dict.get('license_2')
    elif 'license_3' in type:
        src = '88x31(4).png'
        lic = lic_dict.get('license_3')
        href = href_dict.get('license_3')
    elif 'license_4' in type:
        src = '88x31(5).png'
        lic = lic_dict.get('license_4')
        href = href_dict.get('license_4')
    elif 'license_5' in type:
        src = '88x31(6).png'
        lic = lic_dict.get('license_5')
        href = href_dict.get('license_5')
    else:
        src = ''
        lic = ''
        href = '#'

    src = '/static/images/default/' + src if len(src) > 0 else ''
    lst = (src, lic, href)

    return lst


@blueprint.app_template_filter('check_permission')
def check_permission(record):
    """Check Permission on Page.

    :param record:
    :return: result
    """
    return check_created_id(record)


@blueprint.app_template_filter('check_file_permission')
def check_file_permission(record, fjson):
    """Check File Download Permission.

    :param record
    :param fjson
    :return: result
    """
    return check_file_download_permission(record, fjson)


def _get_google_scholar_meta(record):
    target_map = {
        'dc:title': 'citation_title',
        'jpcoar:creatorName': 'citation_author',
        'dc:publisher': 'citation_publisher',
        'jpcoar:subject': 'citation_keywords',
        'jpcoar:sourceTitle': 'citation_journal_title',
        'jpcoar:volume': 'citation_volume',
        'jpcoar:issue': 'citation_issue',
        'jpcoar:pageStart': 'citation_firstpage',
        'jpcoar:pageEnd': 'citation_lastpage', }
    recstr = etree.tostring(
        getrecord(
            identifier=record['_oai']['id'],
            metadataPrefix='jpcoar',
            verb='getrecord'))
    et = etree.fromstring(recstr)
    mtdata = et.find('getrecord/record/metadata/', namespaces=et.nsmap)
    res = []
    if mtdata:
        for target in target_map:
            found = mtdata.find(target, namespaces=mtdata.nsmap)
            if found is not None:
                res.append({'name': target_map[target], 'data': found.text})
        for date in mtdata.findall('datacite:date', namespaces=mtdata.nsmap):
            if date.attrib.get('dateType') == 'Available':
                res.append({'name': 'citation_online_date', 'data': date.text})
            elif date.attrib.get('dateType') == 'Issued':
                res.append(
                    {'name': 'citation_publication_date', 'data': date.text})
        for relatedIdentifier in mtdata.findall(
                'jpcoar:relatedIdentifier',
                namespaces=mtdata.nsmap):
            if 'identifierType' in relatedIdentifier.attrib and \
                relatedIdentifier.attrib[
                    'identifierType'] == 'DOI':
                res.append({'name': 'citation_doi',
                            'data': relatedIdentifier.text})
        for sourceIdentifier in mtdata.findall(
                'jpcoar:sourceIdentifier',
                namespaces=mtdata.nsmap):
            if 'identifierType' in sourceIdentifier.attrib and \
                sourceIdentifier.attrib[
                    'identifierType'] == 'ISSN':
                res.append({'name': 'citation_issn',
                            'data': sourceIdentifier.text})
        for pdf_url in mtdata.findall('jpcoar:file/jpcoar:URI',
                                      namespaces=mtdata.nsmap):
            res.append({'name': 'citation_pdf_url',
                        'data': request.url.replace('records', 'record')
                        + '/files/' + pdf_url.text})
    res.append({'name': 'citation_dissertation_institution',
                'data': InstitutionName.get_institution_name()})
    res.append({'name': 'citation_abstract_html_url', 'data': request.url})
    return res


def default_view_method(pid, record, filename=None, template=None, **kwargs):
    r"""Display default view.

    Sends record_viewed signal and renders template.
    :param pid: PID object.
    :param record: Record object.
    :param filename: File name.
    :param template: Template to render.
    :returns: The rendered template.
    """
    check_site_license_permission()
    check_items_settings()
    send_info = {}
    send_info['site_license_flag'] = True \
        if hasattr(current_user, 'site_license_flag') else False
    send_info['site_license_name'] = current_user.site_license_name \
        if hasattr(current_user, 'site_license_name') else ''
    record_viewed.send(
        current_app._get_current_object(),
        pid=pid,
        record=record,
        info=send_info
    )
    community_arg = request.args.get('community')
    community_id = ""
    ctx = {'community': None}
    if community_arg:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(community_arg)
        ctx = {'community': comm}
        community_id = comm.id

    # Get index style
    style = IndexStyle.get(
        current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    width = style.width if style else '3'
    height = style.height if style else None

    detail_condition = get_search_detail_keyword('')

    weko_indexer = WekoIndexer()
    res = weko_indexer.get_item_link_info(pid=record.get("control_number"))
    if res is not None:
        record["relation"] = res
    else:
        record["relation"] = {}

    google_scholar_meta = _get_google_scholar_meta(record)

    pdfcoverpage_set_rec = PDFCoverPageSettings.find(1)
    # Check if user has the permission to download original pdf file
    # and the cover page setting is set and its value is enable (not disabled)
    can_download_original = check_original_pdf_download_permission(record) \
        and pdfcoverpage_set_rec is not None \
        and pdfcoverpage_set_rec.avail != 'disable'

    # Get item meta data
    record['permalink_uri'] = None
    permalink = get_record_permalink(pid.object_uuid)
    if not permalink:
        record['permalink_uri'] = request.url
    else:
        record['permalink_uri'] = permalink

    from invenio_files_rest.permissions import has_update_version_role
    can_update_version = has_update_version_role(current_user)

    datastore = RedisStore(redis.StrictRedis.from_url(
        current_app.config['CACHE_REDIS_URL']))
    cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
        format(name='display_stats')
    if datastore.redis.exists(cache_key):
        curr_display_setting = datastore.get(cache_key).decode('utf-8')
        display_stats = True if curr_display_setting == 'True' else False
    else:
        display_stats = True

    groups_price = get_groups_price(record)
    billing_files_permission = None
    billing_files_prices = None
    if groups_price:
        billing_files_permission = \
            get_billing_file_download_permission(groups_price)
        billing_files_prices = \
            get_min_price_billing_file_download(groups_price,
                                                billing_files_permission)

    from weko_theme.utils import get_design_layout
    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        request.args.get('community') or current_app.config[
            'WEKO_THEME_DEFAULT_COMMUNITY'])

    if hasattr(current_i18n, 'language'):
        index_link_list = get_index_link_list(current_i18n.language)
    else:
        index_link_list = get_index_link_list()

    files_thumbnail = []
    if record.files:
        files_thumbnail = ObjectVersion.get_by_bucket(
            record.get('_buckets').get('deposit')).\
            filter_by(is_thumbnail=True).all()

    return render_template(
        template,
        pid=pid,
        record=record,
        display_stats=display_stats,
        filename=filename,
        can_download_original_pdf=can_download_original,
        is_logged_in=current_user and current_user.is_authenticated,
        can_update_version=can_update_version,
        page=page,
        render_widgets=render_widgets,
        community_id=community_id,
        width=width,
        detail_condition=detail_condition,
        height=height,
        index_link_enabled=style.index_link_enabled,
        index_link_list=index_link_list,
        google_scholar_meta=google_scholar_meta,
        billing_files_permission=billing_files_permission,
        billing_files_prices=billing_files_prices,
        files_thumbnail=files_thumbnail,
        **ctx,
        **kwargs
    )


@blueprint.route('/admin/pdfcoverpage', methods=['GET', 'POST'])
def set_pdfcoverpage_header():
    """Set pdfcoverage header."""
    @blueprint.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
    def handle_over_max_file_size(error):
        return 'result : file size is overed.'

    # Save PDF Cover Page Header settings
    if request.method == 'POST':
        record = PDFCoverPageSettings.find(1)
        avail = request.form.get('availability')
        header_display_type = request.form.get('header-display')
        header_output_string = request.form.get('header-output-string')
        header_output_image_file = request.files.get('header-output-image')
        header_output_image_filename = header_output_image_file.filename
        header_output_image = record.header_output_image
        if not header_output_image_filename == '':
            upload_dir = "/code/header-icons/"
            header_output_image = upload_dir + header_output_image_filename
            header_output_image_file.save(header_output_image)
        header_display_position = request.form.get('header-display-position')

        # update PDF cover page settings
        PDFCoverPageSettings.update(1,
                                    avail,
                                    header_display_type,
                                    header_output_string,
                                    header_output_image,
                                    header_display_position
                                    )

        flash(_('PDF cover page settings have been updated.'),
              category='success')
        return redirect('/admin/pdfcoverpage')

    return redirect('/admin/pdfcoverpage')


@blueprint.route("/file_version/update", methods=['PUT'])
@login_required
def file_version_update():
    """Bulk delete items and index trees."""
    # Only allow authorised users to update object version
    from invenio_files_rest.permissions import has_update_version_role
    if has_update_version_role(current_user):

        bucket_id = request.values.get('bucket_id')
        key = request.values.get('key')
        version_id = request.values.get('version_id')
        is_show = request.values.get('is_show')
        if not bucket_id and not key and not version_id:
            from invenio_files_rest.models import ObjectVersion
            object_version = ObjectVersion.get(bucket=bucket_id, key=key,
                                               version_id=version_id)
            if object_version is not None:
                # Do update the path on record
                object_version.is_show = True if is_show == '1' else False
                db.session.commit()

                return jsonify({'status': 1})
            else:
                return jsonify({'status': 0, 'msg': 'Version not found'})
        else:
            return jsonify({'status': 0, 'msg': 'Invalid data'})
    else:
        return jsonify({'status': 0, 'msg': 'Insufficient permission'})


@blueprint.app_template_filter('citation')
def citation(record, pid, style=None, ln=None):
    """Render citation for record according to style and language."""
    locale = ln or "en-US"  # ln or current_i18n.language
    style = style or "aapg-bulletin"  # style or 'science'
    try:
        _record = WekoRecord.get_record(pid.object_uuid)
        return citeproc_v1.serialize(pid, _record, style=style, locale=locale)
    except Exception:
        current_app.logger.exception(
            'Citation formatting for record {0} failed.'.format(str(
                record.id)))
        return None


@blueprint.route("/records/soft_delete/<recid>", methods=['POST'])
@login_required
def soft_delete(recid):
    """Soft delete item."""
    try:
        from invenio_files_rest.permissions import has_update_version_role
        if not has_update_version_role(current_user):
            abort(403)
        soft_delete_imp(recid)
        return make_response('PID: ' + str(recid) + ' DELETED', 200)
    except Exception as ex:
        print(str(ex))
        abort(500)


@blueprint.route("/records/restore/<recid>", methods=['POST'])
@login_required
def restore(recid):
    """Restore item."""
    try:
        from invenio_files_rest.permissions import has_update_version_role
        if not has_update_version_role(current_user):
            abort(403)
        restore_imp(recid)
        return make_response('PID: ' + str(recid) + ' RESTORED', 200)
    except Exception as ex:
        print(str(ex))
        abort(500)
