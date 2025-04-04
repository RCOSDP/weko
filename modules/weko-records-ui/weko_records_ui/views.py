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

from datetime import datetime
import re
import os
import uuid

import six
import werkzeug
from flask import Blueprint, abort, current_app, escape, flash, json, \
    jsonify, make_response, redirect, render_template, request, url_for
from flask_babelex import gettext as _
from flask_login import login_required
from flask_security import current_user
from invenio_cache import cached_unless_authenticated
from invenio_db import db
from invenio_files_rest.models import ObjectVersion, FileInstance
from invenio_files_rest.permissions import has_update_version_role
from invenio_i18n.ext import current_i18n
from invenio_oaiserver.response import getrecord
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records_ui.signals import record_viewed
from invenio_files_rest.signals import file_downloaded
from invenio_records_ui.utils import obj_or_import_string
from lxml import etree
from weko_accounts.views import _redirect_method
from weko_admin.models import AdminSettings
from weko_admin.utils import get_search_setting
from weko_deposit.api import WekoRecord
from weko_deposit.pidstore import get_record_without_version
from weko_index_tree.api import Indexes
from weko_index_tree.models import IndexStyle
from weko_index_tree.utils import get_index_link_list
from weko_records.api import ItemLink, Mapping, ItemTypes, RequestMailList
from weko_records.serializers import citeproc_v1
from weko_records.serializers.utils import get_mapping
from weko_records.utils import custom_record_medata_for_export, \
    remove_weko2_special_character, selected_value_by_language
from weko_search_ui.api import get_search_detail_keyword
from weko_schema_ui.models import PublishStatus
from weko_user_profiles.models import UserProfile
from weko_workflow.api import WorkFlow

from weko_records_ui.fd import add_signals_info
from weko_records_ui.utils import check_items_settings, get_file_info_list
from weko_workflow.utils import get_item_info, process_send_mail, set_mail_info

from .ipaddr import check_site_license_permission
from .models import FilePermission, PDFCoverPageSettings
from .permissions import check_content_clickable, check_created_id, \
    check_file_download_permission, check_original_pdf_download_permission, \
    check_permission_period, file_permission_factory, get_permission
from .utils import create_secret_url, get_billing_file_download_permission, \
    get_google_detaset_meta, get_google_scholar_meta, get_groups_price, \
    get_min_price_billing_file_download, get_record_permalink, hide_by_email, \
    delete_version, is_show_email_of_creator,hide_by_itemtype
from .utils import restore as restore_imp
from .utils import soft_delete as soft_delete_imp
from .api import get_s3_bucket_list, copy_bucket_to_s3, replace_file_bucket


blueprint = Blueprint(
    'weko_records_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.app_template_filter()
def record_from_pid(pid_value):
    """Get record from PID."""
    try:
        return WekoRecord.get_record_by_pid(pid_value)
    except Exception as e:
        current_app.logger.debug('Unable to get version record: ')
        current_app.logger.debug(e)
        return {}


@blueprint.app_template_filter()
def url_to_link(field):
    pattern = ".*/record/\d+/files/.*"
    if field.startswith("http"):
        if re.match(pattern, field):
            return False
        else:
            return True
    return False


@blueprint.app_template_filter()
def pid_value_version(pid_value):
    """Get version from pid_value."""
    try:
        lists = str(pid_value).split('.')
        return lists[-1] if len(lists) > 1 else None
    except Exception as e:
        current_app.logger.debug('Unable to get version from pid_value: ')
        current_app.logger.debug(e)
        return None


def publish(pid, record, template=None, **kwargs):
    """Record publish  status change view.

    Change record publish status with given status and renders record export
    template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param kwargs: Additional view arguments based on URL rule.
    :return: The rendered template.
    """
    from weko_deposit.api import WekoIndexer
    status = request.values.get('status')
    publish_status = record.get('publish_status')

    pid_ver = PIDVersioning(child=pid)
    last_record = WekoRecord.get_record_by_pid(pid_ver.last_child.pid_value)

    if not publish_status:
        record.update({'publish_status': (status or PublishStatus.PUBLIC.value)})
        last_record.update({'publish_status': (status or PublishStatus.PUBLIC.value)})
    else:
        record['publish_status'] = (status or PublishStatus.PUBLIC.value)
        last_record['publish_status'] = (status or PublishStatus.PUBLIC.value)

    record.commit()
    last_record.commit()
    db.session.commit()

    indexer = WekoIndexer()
    indexer.update_es_data(record, update_revision=False, field='publish_status')
    indexer.update_es_data(last_record, update_revision=False, field='publish_status')

    return redirect(url_for('.recid', pid_value=pid.pid_value))


def export(pid, record, template=None, **kwargs):
    """Record serialization view.

    Serializes record with given format and renders record export template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param kwargs: Additional view arguments based on URL rule.
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
        # Custom Record Metadata for export JSON
        custom_record_medata_for_export(record)
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
def get_license_icon(license_type):
    """Get License type icon.

    :param license_type:
    :return:
    """
    list_license_dict = current_app.config['WEKO_RECORDS_UI_LICENSE_DICT']
    license_icon_location = \
        current_app.config['WEKO_RECORDS_UI_LICENSE_ICON_LOCATION']
    # In case of current lang is not JA, set to default.
    current_lang = 'default' if current_i18n.language != 'ja' \
        else current_i18n.language
    src, lic, href = '', '', '#'
    for item in list_license_dict:
        if item['value'] != "license_free" and license_type \
                and item['value'] in license_type:
            src = item['src']
            lic = item['name']
            href = item['href_' + current_lang]
            break
    src = license_icon_location + src if len(src) > 0 else ''
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

    Args:
        record (weko_deposit.api.WekoRecord): _description_
        fjson (dict): _description_

    """
    return check_file_download_permission(record, fjson)


@blueprint.app_template_filter('check_file_permission_period')
def check_file_permission_period(record, fjson):
    """Check File Download Permission.

    :param record
    :param fjson
    :return: result
    """
    return check_permission_period(get_permission(record, fjson))


@blueprint.app_template_filter('get_permission')
def get_file_permission(record, fjson):
    """Get File Download Permission.

    :param record
    :param fjson
    :return: result
    """
    return get_permission(record, fjson)


@blueprint.app_template_filter('check_content_file_clickable')
def check_content_file_clickable(record, fjson):
    """Check If content file is clickable.

    :param record
    :param fjson
    :return: result
    """
    return check_content_clickable(record, fjson)


@blueprint.app_template_filter('get_usage_workflow')
def get_usage_workflow(file_json):
    """Get correct usage workflow to redirect user.

    :param file_json
    :return: result
    """
    if not current_user.is_authenticated:
        # In case guest user
        from invenio_accounts.models import Role
        roles = [Role(id="none_loggin")]
    else:
        roles = current_user.roles
    if file_json and isinstance(file_json.get("provide"), list):
        provide = file_json.get("provide")
        for role in roles:
            for data in provide:
                if str(role.id) == data.get("role_id"):
                    return data.get("workflow_id")
    return None


@blueprint.app_template_filter('get_workflow_detail')
def get_workflow_detail(workflow_id):
    """Get workflow detail.

    :param
    :return: result
    """
    workflow_detail = WorkFlow().get_workflow_by_id(workflow_id)
    if workflow_detail:
        return workflow_detail
    else:
        abort(404)


def default_view_method(pid, record, filename=None, template=None, **kwargs):
    """Display default view.

    Sends record_viewed signal and renders template.
    :param pid: PID object.
    :param record: Record object.
    :param filename: File name.
    :param template: Template to render.
    :param kwargs: Additional view arguments based on URL rule.
    :returns: The rendered template.
    """
    def _get_rights_title(result, rights_key_str, rights_values, current_lang, meta_options):
        """Get multi-lang rights title."""
        for rights_key in rights_key_str.split(','):
            item_key = rights_key.split('.')[0]
            if item_key in meta_options:
                if meta_options[item_key].get('title'):
                    item_title = meta_options[item_key]['title']
                if meta_options[item_key]['title_i18n'].get(current_lang, None):
                    item_title = meta_options[item_key]['title_i18n'][current_lang]
                elif meta_options[item_key]['title_i18n'].get('en', None):
                    item_title = meta_options[item_key]['title_i18n']['en']
            if rights_values:
                result[item_key] = {
                    'item_title': item_title,
                    'item_values': rights_values
                }

    item_type_id = record.get('item_type_id', -1)
    item_type = ItemTypes.get_by_id(item_type_id)
    # Check file permision if request is File Information page.
    file_order = int(request.args.get("file_order", -1))
    if filename:
        check_file = None
        if item_type:
            _files = record.get_file_data(item_type)
        else:
            _files = record.get_file_data()
        if not _files:
            abort(404)

        if filename == '[No FileName]':
            if file_order == -1 or file_order >= len(_files):
                abort(404)
            check_file = _files[file_order]
        else:
            find_filenames = [file for file in _files if file.get(
                'filename', '') == filename]
            if not find_filenames:
                abort(404)
            check_file = find_filenames[0]

        # Check file contents permission
        if not file_permission_factory(record, fjson=check_file, item_type=item_type).can():
            if not current_user.is_authenticated:
                return _redirect_method(has_next=True)
            abort(403)

    path_name_dict = {'ja': {}, 'en': {}}
    for navi in record.navi:
        path_arr = navi.path.split('/')
        for path in path_arr:
            index = Indexes.get_index(index_id=path)
            idx_name = index.index_name or ""
            idx_name_en = index.index_name_english
            path_name_dict['ja'][path] = idx_name.replace(
                "\n", r"<br\>").replace("&EMPTY&", "")
            path_name_dict['en'][path] = idx_name_en.replace(
                "\n", r"<br\>").replace("&EMPTY&", "")
            if not path_name_dict['ja'][path]:
                path_name_dict['ja'][path] = path_name_dict['en'][path]
    # Get PID version object to retrieve all versions of item
    pid_ver = PIDVersioning(child=pid)
    if not pid_ver.exists or pid_ver.is_last_child:
        abort(404)
    active_versions = list(pid_ver.children or [])
    all_versions = list(pid_ver.get_children(ordered=True, pid_status=PIDStatus.REGISTERED)
                        or [])
    try:
        if WekoRecord.get_record(id_=active_versions[-1].object_uuid)[
                '_deposit']['status'] == 'draft':
            active_versions.pop()
        if WekoRecord.get_record(id_=all_versions[-1].object_uuid)[
                '_deposit']['status'] == 'draft':
            all_versions.pop()
    except Exception:
        pass
    if active_versions:
        # active_versions.remove(pid_ver.last_child)
        active_versions.pop()

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
        if comm is not None:
            community_id = comm.id

    # Get index style
    style = IndexStyle.get(
        current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    width = style.width if style else '3'
    height = style.height if style else None

    detail_condition = get_search_detail_keyword('')

    # Add Item Reference data to Record Metadata
    res = ItemLink.get_item_link_info(record.get("recid"))
    if res:
        record["relation"] = res
    else:
        record["relation"] = {}

    recstr = etree.tostring(
        getrecord(
            identifier=record['_oai'].get('id'),
            metadataPrefix='jpcoar',
            verb='getrecord'
        )
    )
    et=etree.fromstring(recstr)
    google_scholar_meta = get_google_scholar_meta(record,record_tree=et)
    google_dataset_meta = get_google_detaset_meta(record,record_tree=et)

    current_lang = current_i18n.language \
        if hasattr(current_i18n, 'language') else None
    # get title name
    from weko_search_ui.utils import get_data_by_property
    from weko_items_ui.utils import get_options_and_order_list, get_hide_list_by_schema_form
    from weko_workflow.utils import get_sub_item_value

    title_name = ''
    rights_values = {}
    accessRight = ''
    hide_list = []
    if item_type:
        meta_options = get_options_and_order_list(
            item_type_id,
            item_type_data=ItemTypes(item_type.schema, model=item_type),
            mapping_flag=False)
        hide_list = get_hide_list_by_schema_form(schemaform=item_type.render.get('table_row_map', {}).get('form', []))
    else:
        meta_options = get_options_and_order_list(item_type_id, mapping_flag=False)
    item_map = get_mapping(item_type_id, 'jpcoar_mapping', item_type=item_type)

    # get title info
    title_value_key = 'title.@value'
    title_lang_key = 'title.@attributes.xml:lang'
    if title_value_key in item_map:
        title_languages = []
        _title_key_str = ''
        if title_lang_key in item_map:
            # get language
            title_languages, _title_key_str = get_data_by_property(
                record, item_map, title_lang_key)
        # get value
        title_values, _title_key1_str = get_data_by_property(
            record, item_map, title_value_key)
        title_name = selected_value_by_language(
            title_languages,
            title_values,
            _title_key_str,
            _title_key1_str,
            current_lang,
            record,
            meta_options,
            hide_list)
    # get rights info
    rights_value_key = 'rights.@value'
    if rights_value_key in item_map:
        key_list = item_map.get(rights_value_key)
        for k in key_list.split(","):
            subkey_list = k.split('.')
            _rights_values = []
            attribute = record.get(subkey_list[0])
            if attribute:
                data_result = get_sub_item_value(attribute, subkey_list[-1])
                if data_result:
                    if isinstance(data_result, list):
                        for value in data_result:
                            _rights_values.append(value)
                    elif isinstance(data_result, str):
                        _rights_values.append(data_result)
            prop_hidden = meta_options.get(subkey_list[0], {}).get('option', {}).get('hidden', False)
            if not prop_hidden and (subkey_list[0] not in hide_list or subkey_list[-1] not in hide_list):
                _get_rights_title(rights_values, k, _rights_values,
                                    current_lang, meta_options)
    # get accessRights info
    accessRights_value_key = 'accessRights.@value'
    if accessRights_value_key in item_map:
        key_list = item_map.get(accessRights_value_key)
        for k in key_list.split(","):
            subkey_list = k.split('.')
            prop_hidden = meta_options.get(subkey_list[0], {}).get('option', {}).get('hidden', False)
            attribute = record.get(subkey_list[0])
            if attribute and not prop_hidden and (subkey_list[0] not in hide_list or subkey_list[-1] not in hide_list):
                data_result = get_sub_item_value(attribute, subkey_list[-1])
                if data_result:
                    if isinstance(data_result, list) and len(data_result) > 0:
                        accessRight = data_result[0]
                        break
                    elif isinstance(data_result, str):
                        accessRight = data_result
                        break

    pdfcoverpage_set_rec = PDFCoverPageSettings.find(1)
    # Check if user has the permission to download original pdf file
    # and the cover page setting is set and its value is enable (not disabled)
    can_download_original = check_original_pdf_download_permission(record) \
        and pdfcoverpage_set_rec and pdfcoverpage_set_rec.avail != 'disable'

    # Get item meta data
    record['permalink_uri'] = None
    permalink = get_record_permalink(record)
    if not permalink:
        if record.get('system_identifier_doi') and \
            record.get('system_identifier_doi').get(
                'attribute_value_mlt')[0]:
            record['permalink_uri'] = \
                record['system_identifier_doi'][
                    'attribute_value_mlt'][0][
                    'subitem_systemidt_identifier']
        else:
            record['permalink_uri'] = '{}records/{}'.format(
                request.url_root, record.get("recid"))
    else:
        record['permalink_uri'] = permalink

    can_update_version = has_update_version_role(current_user)

    display_setting = AdminSettings.get(name='display_stats_settings',
                                        dict_to_object=False)
    if display_setting:
        display_stats = display_setting.get('display_stats')
    else:
        display_stats = True

    items_display_settings = AdminSettings.get(name='items_display_settings',
                                        dict_to_object=False)
    if items_display_settings:
        search_author_flg = items_display_settings.get('items_search_author')
    else:
        search_author_flg = "name"

    groups_price = get_groups_price(record)
    billing_files_permission = get_billing_file_download_permission(
        groups_price) if groups_price else None
    billing_files_prices = get_min_price_billing_file_download(
        groups_price,
        billing_files_permission) if groups_price else None

    from weko_theme.utils import get_design_layout

    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        request.args.get('community') or current_app.config[
            'WEKO_THEME_DEFAULT_COMMUNITY'])

    # if current_lang:
    #     index_link_list = get_index_link_list(current_lang)
    # else:
    #     index_link_list = get_index_link_list()

    index_link_list = get_index_link_list()

    files_thumbnail = []
    if record.files:
        files_thumbnail = ObjectVersion.get_by_bucket(
            record.files.bucket.id, asc_sort=True).\
            filter_by(is_thumbnail=True).all()
    is_display_file_preview, files = get_file_info_list(record, item_type=item_type)
    # Flag: can edit record
    can_edit = True if pid == get_record_without_version(pid) else False

    open_day_display_flg = current_app.config.get('OPEN_DATE_DISPLAY_FLG')
    # Hide email of creator in pdf cover page
    is_show_email = is_show_email_of_creator(item_type_id, item_type=item_type)
    if not is_show_email:
        # list_hidden = get_ignore_item(record['item_type_id'])
        # record = hide_by_itemtype(record, list_hidden)
        record = hide_by_email(record, item_type=item_type)

    # Remove hide item
    from weko_items_ui.utils import get_ignore_item
    list_hidden = []
    if item_type:
        list_hidden = get_ignore_item(item_type_id, item_type_data=ItemTypes(item_type.schema, model=item_type))
    record = hide_by_itemtype(record, list_hidden)

    # Get Facet search setting.
    display_facet_search = get_search_setting().get("display_control", {}).get(
        'display_facet_search', {}).get('status', False)
    ctx.update({
        "display_facet_search": display_facet_search
    })

    # Get index tree setting.
    display_index_tree = get_search_setting().get("display_control", {}).get(
        'display_index_tree', {}).get('status', False)
    ctx.update({
        "display_index_tree": display_index_tree
    })

    # Get display_community setting.
    display_community = get_search_setting().get("display_control", {}).get(
        'display_community', {}).get('status', False)
    ctx.update({
        "display_community": display_community
    })

    current_app.logger.debug("template :{}".format(template))

    file_url = ''
    if file_order >= 0 and files and files[file_order].get('url') and files[file_order]['url'].get('url'):
        file_url = files[file_order]['url']['url']

    # Get Settings
    enable_request_maillist = False
    items_display_settings = AdminSettings.get(name='items_display_settings',
                                        dict_to_object=False)
    if items_display_settings:
        enable_request_maillist = items_display_settings.get('display_request_form', False)

    # Get request recipients
    request_recipients = RequestMailList.get_mail_list_by_item_id(pid.object_uuid)
    is_display_request_form = enable_request_maillist and (True if request_recipients else False)

    return render_template(
        template,
        pid=pid,
        pid_versioning=pid_ver,
        active_versions=active_versions,
        all_versions=all_versions,
        record=record,
        files=files,
        file_url=file_url,
        display_stats=display_stats,
        is_display_request_form = is_display_request_form,
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
        google_dataset_meta=google_dataset_meta,
        billing_files_permission=billing_files_permission,
        billing_files_prices=billing_files_prices,
        files_thumbnail=files_thumbnail,
        can_edit=can_edit,
        open_day_display_flg=open_day_display_flg,
        path_name_dict=path_name_dict,
        is_display_file_preview=is_display_file_preview,
        # experimental implementation 20210502
        title_name=title_name,
        rights_values=rights_values,
        accessRight=accessRight,
        thumbnail_width = current_app.config.get('WEKO_RECORDS_UI_DEFAULT_MAX_WIDTH_THUMBNAIL') ,
        analysis_url=current_app.config.get(
            'WEKO_RECORDS_UI_ONLINE_ANALYSIS_URL'),
        flg_display_itemtype = current_app.config.get('WEKO_RECORDS_UI_DISPLAY_ITEM_TYPE') ,
        flg_display_resourcetype = current_app.config.get('WEKO_RECORDS_UI_DISPLAY_RESOURCE_TYPE') ,
        search_author_flg=search_author_flg,
        show_secret_URL=_get_show_secret_url_button(record,filename),
        **ctx,
        **kwargs
    )


def create_secret_url_and_send_mail(pid:PersistentIdentifier, record:WekoRecord, filename:str, **kwargs) -> str:
    """on click button 'Secret URL'
    generate secret URL and send mail.
    about entrypoint settings, see at .config RECORDS_UI_ENDPOINTS.recid_secret_url

    Args:
        pid: PID object.
        record: Record object.
        filename: File name.

    Returns:
        result status and message text.
    """
    current_app.logger.info("pid:" + pid.pid_value)
    current_app.logger.info("record:" + str(record.id))
    current_app.logger.info("filename:" + filename)

    #permission check
    # "Someone who can show Secret URL button" can also use generate Secret URL function.
    if not _get_show_secret_url_button(record ,filename):
        abort(403)

    userprof:UserProfile = UserProfile.get_by_userid(current_user.id)
    restricted_fullname = userprof._displayname or '' if userprof else ''
    restricted_data_name = record.get('item_title','')

    #generate url and regist db(FileSecretDownload)
    result = create_secret_url(pid.pid_value,filename,current_user.email , restricted_fullname , restricted_data_name)

    #send mail
    mail_pattern_name:str = current_app.config.get('WEKO_RECORDS_UI_MAIL_TEMPLATE_SECRET_URL')

    mail_info = set_mail_info(get_item_info(pid.object_uuid), type("" ,(object,),dict(activity_id = '')))
    mail_info.update(result)
    if process_send_mail( mail_info = mail_info, mail_pattern_name=mail_pattern_name) :
        return _('Success Secret URL Generate')
    else:
        abort(500)

def _get_show_secret_url_button(record : WekoRecord, filename :str) -> bool:
    """
        Args:
            WekoRecord : records_metadata for target item
            str : target content name
        Returns:
            bool : return true if be able to show Secret URL button. or false.
    """

    #1.check secret url function is enabled
    restricted_access = AdminSettings.get('restricted_access', False)
    if not restricted_access:
        restricted_access = current_app.config[
            'WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS']

    enable:bool = restricted_access.get('secret_URL_file_download',{}).get('secret_enable',False)

    #2.check the user has permittion
    has_parmission = False
    # Registered user
    owner_user_id = [int(record['owner'])] if record.get('owner') else []
    shared_user_id = [int(record['weko_shared_id'])] if int(record.get('weko_shared_id', -1)) != -1 else []
    if current_user and current_user.is_authenticated and \
        current_user.id in owner_user_id + shared_user_id:
        has_parmission = True
    # Super users
    supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']
    for role in list(current_user.roles or []):
        if role.name in supers:
            has_parmission = True

    #3.check the file's accessrole is "open_no" ,or "open_date" and not open yet.
    is_secret_file = False
    current_app.logger.info(record.get_file_data())
    for content in record.get_file_data():
        if content.get('filename') == filename:
            if content.get('accessrole') == "open_no":
                is_secret_file = True
            elif content.get('accessrole') == "open_date" and \
                datetime.now() < datetime.strptime(content.get('date',[{"dateValue" :'1970-01-01'}])[0].get("dateValue" ,'1970-01-01'), '%Y-%m-%d')  :
                is_secret_file = True

    # all true is show
    return enable and has_parmission and is_secret_file

@blueprint.route('/r/<parent_pid_value>', methods=['GET'])
@blueprint.route('/r/<parent_pid_value>.<int:version>', methods=['GET'])
@login_required
def doi_ish_view_method(parent_pid_value=0, version=0):
    """DOI-like item version endpoint view.

    :param pid: PID value.
    :returns: Redirect to correct version.
    """
    try:
        p_pid = PersistentIdentifier.get('parent',
                                         'parent:' + str(parent_pid_value))
    except PIDDoesNotExistError:
        p_pid = None

    if p_pid:
        pid_ver = PIDVersioning(parent=p_pid)
        all_versions = list(
            pid_ver.get_children(
                ordered=True,
                pid_status=None))
        if version == 0 or version == len(all_versions):
            return redirect(url_for('invenio_records_ui.recid',
                                    pid_value=pid_ver.last_child.pid_value))
        elif version <= len(all_versions):
            version_pid = all_versions[(version - 1)]
            current_app.logger.info(version_pid.__dict__)
            if version_pid.status == PIDStatus.REGISTERED:
                return redirect(url_for('invenio_records_ui.recid',
                                        pid_value=version_pid.pid_value))

    return abort(404)


@blueprint.route('/records/parent:<pid_value>', methods=['GET'])
@login_required
def parent_view_method(pid_value=0):
    """Parent view method to display latest version.

    :param pid_value: PID value.
    :returns: Redirect to original view.
    """
    try:
        p_pid = PersistentIdentifier.get('parent', 'parent:' + str(pid_value))
    except PIDDoesNotExistError:
        p_pid = None

    if p_pid:
        pid_version = PIDVersioning(parent=p_pid)
        if pid_version.last_child:
            return redirect(
                url_for('invenio_records_ui.recid',
                        pid_value=pid_version.last_child.pid_value))
    return abort(404)


@blueprint.route('/admin/pdfcoverpage', methods=['GET', 'POST'])
def set_pdfcoverpage_header():
    """Set pdfcoverage header."""
    @blueprint.errorhandler(werkzeug.exceptions.RequestEntityTooLarge)
    def handle_over_max_file_size(error):
        return 'result : file size is overed.'

    # Save PDF Cover Page Header settings
    if request.method == 'POST':
        try:
            record = PDFCoverPageSettings.find(1)
            avail = request.form.get('availability')
            header_display_type = request.form.get('header-display')
            header_output_string = request.form.get('header-output-string')
            header_output_image_file = request.files.get('header-output-image')
            header_output_image_filename = header_output_image_file.filename
            header_output_image = record.header_output_image
            if not header_output_image_filename == '':
                upload_dir = current_app.instance_path + current_app.config.get(
                    'WEKO_RECORDS_UI_PDF_HEADER_IMAGE_DIR')
                if not os.path.isdir(upload_dir):
                    os.makedirs(upload_dir)
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
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)

    return redirect('/admin/pdfcoverpage')


@blueprint.route("/file_version/update", methods=['PUT'])
@login_required
def file_version_update():
    """Bulk delete items and index trees."""
    # Only allow authorised users to update object version
    if has_update_version_role(current_user):

        bucket_id = request.values.get('bucket_id')
        key = request.values.get('key')
        version_id = request.values.get('version_id')
        is_show = request.values.get('is_show')
        if not bucket_id and not key and not version_id:
            object_version = ObjectVersion.get(bucket=bucket_id, key=key,
                                               version_id=version_id)
            if object_version:
                # Do update the path on record
                object_version.is_show = True if is_show == '1' else False
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(e)

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
        if not has_update_version_role(current_user):
            abort(403)
        if recid.startswith('del_ver_'):
            recid = recid.replace('del_ver_', '')
            delete_version(recid)
            current_app.logger.info(f"Delete version: {recid}")
        else:
            soft_delete_imp(recid)
            current_app.logger.info(f"Delete item: {recid}")
        db.session.commit()
        return make_response('PID: ' + str(recid) + ' DELETED', 200)
    except Exception as ex:
        db.session.rollback()
        current_app.logger.error(ex)
        if ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                and ex.args[0].get('is_locked'):
            return jsonify(
                code=-1,
                is_locked=True,
                msg=str(ex.args[0].get('msg', ''))
            )
        abort(500)


@blueprint.route("/records/restore/<recid>", methods=['POST'])
@login_required
def restore(recid):
    """Restore item."""
    try:
        if not has_update_version_role(current_user):
            abort(403)
        restore_imp(recid)
        return make_response('PID: ' + str(recid) + ' RESTORED', 200)
    except Exception as ex:
        current_app.logger.error(ex)
        abort(500)


@blueprint.route("/records/permission/<recid>", methods=['POST'])
@login_required
def init_permission(recid):
    """Create file permission in database."""
    user_id = current_user.get_id()
    data = request.get_json()
    file_name = data.get('file_name')
    activity_id = data.get('activity_id')
    try:
        permission = FilePermission.init_file_permission(user_id, recid,
                                                         file_name,
                                                         activity_id)
        db.session.commit()
        if permission:
            return make_response(
                'File permission: ' + file_name + 'of record: ' + recid
                + ' CREATED', 200)
    except Exception as ex:
        db.session.rollback()
        current_app.logger.debug(ex)
        abort(500)


@blueprint.app_template_filter('escape_str')
def escape_str(s):
    r"""Process escape, replace \n to <br/>, convert &EMPTY& to blank char.

    :param s: string
    :return: result
    """
    if s:
        s = remove_weko2_special_character(s)
        s = str(escape(s))
        s = escape_newline(s)
    return s


def escape_newline(s):
    """replace \n to <br/>
    :param s: string
    :return: result
    """
    br_char = '<br/>'
    s = s.replace('\r\n', br_char).replace(
        '\r', br_char).replace('\n', br_char)
    s = '<br />'.join(s.splitlines())

    return s

def json_string_escape(s):
    opt = ''
    if s.endswith('"'):
        opt = '"'
    s = json.dumps(s, ensure_ascii=False)
    s = s.strip('"')
    return s+opt


def xml_string_escape(s):
    return escape(s)


@blueprint.app_template_filter('preview_able')
def preview_able(file_json):
    """Check whether file can be previewed or not.

    Args:
        file_json (dict): _description_

    Returns:
        bool: _description_
    """
    file_type = ''
    file_size = file_json.get('size')
    file_format = file_json.get('format', '')
    for k, v in current_app.config['WEKO_ITEMS_UI_MS_MIME_TYPE'].items():
        if file_format in v:
            file_type = k
            break
    if file_type in current_app.config[
            'WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT'].keys():
        # Convert MB to Bytes in decimal
        file_size_limit = current_app.config[
            'WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT'][
            file_type] * 1000000
        if file_size > file_size_limit:
            return False
    return True

@blueprint.route("/get_uri", methods=['POST'])
def get_uri():
    """_summary_
    ---
      post:
        description:
        requestBody:
            required: true
            content:
            application/json: {"uri":"https://localhost/record/1/files/001.jpg","pid_value":"1","accessrole":"1"}
        responses:
          200:
    """
    data = request.get_json()
    uri = data.get('uri')
    pid_value = data.get('pid_value')
    accessrole = data.get('accessrole')
    pattern = re.compile('^/record/{}/files/.*'.format(pid_value))
    if not pattern.match(uri):
        pid = PersistentIdentifier.get('recid', pid_value)
        record = WekoRecord.get_record_by_pid(pid_value)
        bucket_id = record.get('_buckets', {}).get('deposit')
        file_id_key = '{}_{}'.format(bucket_id, uri)

        file_obj = ObjectVersion()
        file_obj.file = FileInstance()
        file_obj.file.size = 0
        file_obj.file.json = {'url':{'url':uri}, 'accessrole': accessrole}
        file_obj.bucket_id = bucket_id
        file_obj.file_id = uuid.uuid3(uuid.NAMESPACE_URL, file_id_key)
        file_obj.root_file_id = uuid.uuid3(uuid.NAMESPACE_URL, file_id_key)
        file_obj.key = uri
        add_signals_info(record, file_obj)
        file_downloaded.send(current_app._get_current_object(), obj=file_obj)
    return jsonify({'status': True})

@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_records_ui dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()


@blueprint.route("/records/get_bucket_list", methods=['GET'])
def get_bucket_list():
    bucket_list = get_s3_bucket_list()
    return jsonify(bucket_list)

@blueprint.route("/records/copy_bucket", methods=['POST'])
def copy_bucket():
    data = request.get_json()
    pid = data.get('pid')
    filename = data.get('filename')
    bucket_id = data.get('bucket_id')
    checked = data.get('checked')
    bucket_name = data.get('bucket_name')
    try:
        uri = copy_bucket_to_s3(pid, filename, bucket_id, checked=checked, bucket_name=bucket_name)
        return jsonify(uri)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@blueprint.route("/records/replace_file", methods=['POST'])
def replace_file():
    pid = request.form.get('pid')
    bucket_id = request.form.get('bucket_id')
    file = request.files['file']

    try:
        uri = replace_file_bucket(pid, bucket_id, file)
        return jsonify(uri)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
