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

"""Module of weko-records-ui utils."""

from decimal import Decimal

from flask import current_app
from invenio_db import db
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from weko_admin.models import AdminSettings
from weko_deposit.api import WekoDeposit
from weko_records.api import FeedbackMailList, ItemTypes, Mapping
from weko_records.serializers.utils import get_mapping

from .permissions import check_user_group_permission, is_open_restricted, \
    check_file_download_permission
from flask import request
from datetime import datetime as dt
from flask_babelex import gettext as _


def check_items_settings():
    """Check items setting."""
    settings = AdminSettings.get('items_display_settings')
    current_app.config['EMAIL_DISPLAY_FLG'] = settings.items_display_email
    current_app.config['ITEM_SEARCH_FLG'] = settings.items_search_author
    if hasattr(settings, 'item_display_open_date'):
        current_app.config['OPEN_DATE_DISPLAY_FLG'] = \
            settings.item_display_open_date


def get_record_permalink(record):
    """
    Get latest doi/cnri's value of record.

    :param record: index_name_english
    :return: pid value of doi/cnri.
    """
    doi = record.pid_doi
    cnri = record.pid_cnri

    if doi and cnri:
        if doi.updated > cnri.updated:
            return doi.pid_value
        else:
            return cnri.pid_value
    elif doi or cnri:
        return doi.pid_value if doi else cnri.pid_value

    return None


def get_groups_price(record: dict) -> list:
    """Get the prices of Billing files set in each group.

    :param record: Record metadata.
    :return: The prices of Billing files set in each group.
    """
    groups_price = list()
    for _, value in record.items():
        if isinstance(value, dict):
            attr_value = value.get('attribute_value_mlt')
            if attr_value and isinstance(attr_value, list):
                for attr in attr_value:
                    group_price = attr.get('groupsprice')
                    file_name = attr.get('filename')
                    if file_name and group_price:
                        result_data = {
                            'file_name': file_name,
                            'groups_price': group_price
                        }
                        groups_price.append(result_data)

    return groups_price


def get_billing_file_download_permission(groups_price: list) -> dict:
    """Get billing file download permission.

    :param groups_price: The prices of Billing files set in each group
    :return:Billing file permission dictionary.
    """
    billing_file_permission = dict()
    for data in groups_price:
        file_name = data.get('file_name')
        group_price_list = data.get('groups_price')
        if file_name and isinstance(group_price_list, list):
            is_ok = False
            for group_price in group_price_list:
                if isinstance(group_price, dict):
                    group_id = group_price.get('group')
                    is_ok = check_user_group_permission(group_id)
                    if is_ok:
                        break
            billing_file_permission[file_name] = is_ok

    return billing_file_permission


def get_min_price_billing_file_download(groups_price: list,
                                        billing_file_permission: dict) -> dict:
    """Get min price billing file download.

    :param groups_price: The prices of Billing files set in each group
    :param billing_file_permission: Billing file permission dictionary.
    :return:Billing file permission dictionary.
    """
    min_prices = dict()
    for data in groups_price:
        file_name = data.get('file_name')
        group_price_list = data.get('groups_price')
        if not billing_file_permission.get(file_name):
            continue
        if file_name and isinstance(group_price_list, list):
            min_price = None
            for group_price in group_price_list:
                if isinstance(group_price, dict):
                    price = group_price.get('price')
                    group_id = group_price.get('group')
                    is_ok = check_user_group_permission(group_id)
                    try:
                        price = Decimal(price)
                    except Exception as error:
                        current_app.logger.debug(error)
                        price = None
                    if is_ok and price \
                            and (not min_price or min_price > price):
                        min_price = price
            if min_price:
                min_prices[file_name] = min_price

    return min_prices


def is_billing_item(item_type_id):
    """Checks if item is a billing item based on its meta data schema."""
    item_type = ItemTypes.get_by_id(id_=item_type_id)
    if item_type:
        properties = item_type.schema['properties']
        for meta_key in properties:
            if properties[meta_key]['type'] == 'object' and \
               'groupsprice' in properties[meta_key]['properties'] or \
                properties[meta_key]['type'] == 'array' and 'groupsprice' in \
                    properties[meta_key]['items']['properties']:
                return True
        return False


def soft_delete(recid):
    """Soft delete item."""
    try:
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=recid).first()
        if not pid:
            pid = PersistentIdentifier.query.filter_by(
                pid_type='recid', object_uuid=recid).first()
        if pid.status == PIDStatus.DELETED:
            return

        versioning = PIDVersioning(child=pid)
        if not versioning.exists:
            return
        all_ver = versioning.children.all()
        draft_pid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            pid_value="{}.0".format(pid.pid_value.split(".")[0])
        ).one_or_none()

        if draft_pid:
            all_ver.append(draft_pid)

        for ver in all_ver:
            depid = PersistentIdentifier.query.filter_by(
                pid_type='depid', object_uuid=ver.object_uuid).first()
            if depid:
                rec = RecordMetadata.query.filter_by(
                    id=ver.object_uuid).first()
                dep = WekoDeposit(rec.json, rec)
                dep['path'] = []
                dep.indexer.update_path(dep, update_revision=False)
                FeedbackMailList.delete(ver.object_uuid)
                dep.remove_feedback_mail()
            pids = PersistentIdentifier.query.filter_by(
                object_uuid=ver.object_uuid)
            for p in pids:
                p.status = PIDStatus.DELETED
            db.session.commit()
    except Exception as ex:
        db.session.rollback()
        raise ex


def restore(recid):
    """Restore item."""
    try:
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=recid).first()
        if not pid:
            pid = PersistentIdentifier.query.filter_by(
                pid_type='recid', object_uuid=recid).first()
        if pid.status != PIDStatus.DELETED:
            return

        versioning = PIDVersioning(child=pid)
        if not versioning.exists:
            return
        all_ver = versioning.children.all()
        draft_pid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            pid_value="{}.0".format(pid.pid_value.split(".")[0])
        ).one_or_none()

        if draft_pid:
            all_ver.append(draft_pid)

        for ver in all_ver:
            ver.status = PIDStatus.REGISTERED
            depid = PersistentIdentifier.query.filter_by(
                pid_type='depid', object_uuid=ver.object_uuid).first()
            if depid:
                depid.status = PIDStatus.REGISTERED
                rec = RecordMetadata.query.filter_by(id=ver.object_uuid).first()
                dep = WekoDeposit(rec.json, rec)
                dep.indexer.update_path(dep, update_revision=False)
            pids = PersistentIdentifier.query.filter_by(
                object_uuid=ver.object_uuid)
            for p in pids:
                p.status = PIDStatus.REGISTERED
            db.session.commit()
    except Exception as ex:
        db.session.rollback()
        raise ex


def get_list_licence():
    """Get list license.

    @return:
    """
    list_license_result = []
    list_license_from_config = \
        current_app.config['WEKO_RECORDS_UI_LICENSE_DICT']
    for license_obj in list_license_from_config:
        list_license_result.append({'value': license_obj.get('value', ''),
                                    'name': license_obj.get('name', '')})
    return list_license_result


def get_registration_data_type(record):
    """Get registration data type."""
    attribute_value_key = 'attribute_value_mlt'
    data_type_key = 'subitem_data_type'

    for item in record:
        values = record.get(item)
        if isinstance(values, dict) and values.get(attribute_value_key):
            attribute = values.get(attribute_value_key)
            if isinstance(attribute, list):
                for data in attribute:
                    if data_type_key in data:
                        return data.get(data_type_key)


def get_license_pdf(license, item_metadata_json, pdf, file_item_id, footer_w,
                    footer_h, cc_logo_xposition, item):
    """Get license pdf.

    @param license:
    @param item_metadata_json:
    @param pdf:
    @param file_item_id:
    @param footer_w:
    @param footer_h:
    @param cc_logo_xposition:
    @param item:
    @return:
    """
    from .views import blueprint
    license_icon_pdf_location = \
        current_app.config['WEKO_RECORDS_UI_LICENSE_ICON_PDF_LOCATION']
    if license == 'license_free':
        txt = item_metadata_json[file_item_id][0].get('licensefree')
        if txt is None:
            txt = ''
        pdf.multi_cell(footer_w, footer_h, txt, 0, 'L', False)
    else:
        src = blueprint.root_path + license_icon_pdf_location + item['src_pdf']
        txt = item['txt']
        lnk = item['href_pdf']
        pdf.multi_cell(footer_w, footer_h, txt, 0, 'L', False)
        pdf.ln(h=2)
        pdf.image(
            src,
            x=cc_logo_xposition,
            y=None,
            w=0,
            h=0,
            type='',
            link=lnk)


def get_pair_value(name_keys, lang_keys, datas):
    """Get pairs value of name and language.

    :param name_keys:
    :param lang_keys:
    :param datas:
    :return:
    """
    if len(name_keys) == 1 and len(lang_keys) == 1:
        if isinstance(datas, list):
            for data in datas:
                for name, lang in get_pair_value(name_keys, lang_keys, data):
                    yield name, lang
        elif isinstance(datas, dict) and (
                name_keys[0] in datas or lang_keys[0] in datas):
            yield datas.get(name_keys[0], ''), datas.get(lang_keys[0], '')
    else:
        if isinstance(datas, list):
            for data in datas:
                for name, lang in get_pair_value(name_keys, lang_keys, data):
                    yield name, lang
        elif isinstance(datas, dict):
            for name, lang in get_pair_value(name_keys[1:], lang_keys[1:],
                                             datas.get(name_keys[0])):
                yield name, lang


def hide_item_metadata(record):
    """Hiding emails and hidden item metadata.

    :param record:
    :return:
    """
    from weko_items_ui.utils import get_ignore_item, hide_meta_data_for_role
    check_items_settings()

    record['weko_creator_id'] = record.get('owner')

    if hide_meta_data_for_role(record):
        list_hidden = get_ignore_item(record['item_type_id'])
        record = hide_by_itemtype(record, list_hidden)

        if not current_app.config['EMAIL_DISPLAY_FLG']:
            record = hide_by_email(record)

        return True

    record.pop('weko_creator_id')
    return False


def hide_item_metadata_email_only(record):
    """Hiding emails only.

    :param name_keys:
    :param lang_keys:
    :param datas:
    :return:
    """
    from weko_items_ui.utils import hide_meta_data_for_role
    check_items_settings()

    record['weko_creator_id'] = record.get('owner')

    if hide_meta_data_for_role(record) and \
            not current_app.config['EMAIL_DISPLAY_FLG']:
        record = hide_by_email(record)

        return True

    record.pop('weko_creator_id')
    return False


def hide_by_email(item_metadata):
    """Hiding emails.

    :param item_metadata:
    :return:
    """
    subitem_keys = current_app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS']

    # Hidden owners_ext.email
    if item_metadata.get('_deposit') and \
            item_metadata['_deposit'].get('owners_ext'):
        del item_metadata['_deposit']['owners_ext']['email']

    for item in item_metadata:
        _item = item_metadata[item]
        if isinstance(_item, dict) and \
                _item.get('attribute_value_mlt'):
            for _idx, _value in enumerate(_item['attribute_value_mlt']):
                for key in subitem_keys:
                    if key in _value.keys():
                        del _item['attribute_value_mlt'][_idx][key]

    return item_metadata


def hide_by_itemtype(item_metadata, hidden_items):
    """Hiding item type metadata.

    :param item_metadata:
    :param hidden_items:
    :return:
    """
    def del_hide_sub_metadata(keys, metadata):
        """Delete hide metadata."""
        if isinstance(metadata, dict):
            data = metadata.get(keys[0])
            if data:
                if len(keys) > 1:
                    del_hide_sub_metadata(keys[1:], data)
                else:
                    del metadata[keys[0]]
        elif isinstance(metadata, list):
            count = len(metadata)
            for index in range(count):
                del_hide_sub_metadata(keys, metadata[index])

    for hide_key in hidden_items:
        if isinstance(hide_key, str) \
                and item_metadata.get(hide_key):
            del item_metadata[hide_key]
        elif isinstance(hide_key, list) and \
                item_metadata.get(hide_key[0]):
            del_hide_sub_metadata(
                hide_key[1:],
                item_metadata[
                    hide_key[0]]['attribute_value_mlt'])

    return item_metadata


def is_show_email_of_creator(item_type_id):
    """Check setting show/hide email for 'Detail' and 'PDF Cover Page' screen.

    :param item_type_id: item type id of current record.
    :return: True/False, True: show, False: hide.
    """
    def get_creator_id(item_type_id):
        type_mapping = Mapping.get_record(item_type_id)
        item_map = get_mapping(type_mapping, "jpcoar_mapping")
        creator = 'creator.creatorName.@value'
        creator_id = None
        if creator in item_map:
            creator_id = item_map[creator].split('.')[0]
        return creator_id

    def item_type_show_email(item_type_id):
        # Get flag of creator's email hide from item type.
        creator_id = get_creator_id(item_type_id)
        if not creator_id:
            return None
        item_type = ItemTypes.get_by_id(item_type_id)
        schema_editor = item_type.render.get('schemaeditor', {})
        schema = schema_editor.get('schema', {})
        creator = schema.get(creator_id)
        if not creator:
            return None
        properties = creator.get('properties', {})
        creator_mails = properties.get('creatorMails', {})
        items = creator_mails.get('items', {})
        properties = items.get('properties', {})
        creator_mail = properties.get('creatorMail', {})
        is_hide = creator_mail.get('isHide', None)
        return is_hide

    def item_setting_show_email():
        # Display email from setting item admin.
        settings = AdminSettings.get('items_display_settings')
        is_display = settings.items_display_email
        return is_display

    is_hide = item_type_show_email(item_type_id)
    is_display = item_setting_show_email()
    return not is_hide and is_display


def replace_license_free(record_metadata, is_change_label=True):
    """Change the item name 'licensefree' to 'license_note'.

    If 'licensefree' is not output as a value.
    The value of 'licensetype' is 'license_note'.

    :param record:
    :return: None
    """
    _license_type = 'licensetype'
    _license_free = 'licensefree'
    _license_note = 'license_note'
    _license_type_free = 'license_free'
    _attribute_type = 'file'
    _attribute_value_mlt = 'attribute_value_mlt'

    _license_dict = current_app.config['WEKO_RECORDS_UI_LICENSE_DICT']
    if _license_dict:
        _license_type_free = _license_dict[0].get('value')

    for val in record_metadata.values():
        if isinstance(val, dict) and \
                val.get('attribute_type') == _attribute_type:
            for attr in val[_attribute_value_mlt]:
                if attr.get(_license_type) == _license_type_free:
                    attr[_license_type] = _license_note
                    if attr.get(_license_free) and is_change_label:
                        attr[_license_note] = attr[_license_free]
                        del attr[_license_free]



def get_file_info_list(record):
    """File Information of all file in record.

    :param files: all metadata of a record.
    :param is_display_file_preview: all metadata of a record.
    :param record: all metadata of a record.
    :return: json files.
    """
    is_display_file_preview = False
    files = []
    for key in record:
        meta_data = record.get(key)
        if type(meta_data) == dict and \
            meta_data.get('attribute_type') == "file":
            file_metadata = meta_data.get("attribute_value_mlt", [])
            for f in file_metadata:
                if check_file_download_permission(record, f, True)\
                        or is_open_restricted(f):
                    # Set default version_id.
                    if f.get("version_id") is None:
                        f["version_id"] = ''
                    # Set default version_id.
                    if f.get("is_thumbnail") is None:
                        f["is_thumbnail"] = False
                    # Check Opendate is future date.
                    f['future_date_message'] = ""
                    f['download_preview_message'] = ""
                    date = f.get('date')
                    if date and isinstance(date, list) and date[0]:
                        adt = date[0].get('dateValue')
                        pdt = dt.strptime(adt, '%Y-%m-%d')
                        if pdt > dt.today():
                            message = "Download is available from {}/{}/{}."
                            f['future_date_message'] = _(message).format(
                                pdt.year, pdt.month, pdt.day)
                            message = "Download / Preview is available from {}/{}/{}."
                            f['download_preview_message'] = _(message).format(
                                pdt.year, pdt.month, pdt.day)
                    # Check show preview area.
                    # If f is uploaded in this system => show 'Preview' area.
                    base_url = "{}record/{}/files/{}".format(
                        request.url_root,
                        record.get('recid'),
                        f.get("filename")
                    )
                    url = f.get("url", {}).get("url")
                    if base_url in url and not f['future_date_message']:
                        is_display_file_preview = True
                    files.append(f)
    return is_display_file_preview, files
