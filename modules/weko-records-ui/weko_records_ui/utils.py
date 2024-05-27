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

import base64
import orjson
from datetime import datetime as dt
from datetime import timedelta
from decimal import Decimal
from typing import NoReturn, Tuple, Dict
from urllib.parse import quote

from elasticsearch_dsl import Q
from flask import abort, current_app, request
from flask_babelex import gettext as _
from flask_babelex import to_utc
from flask_security import current_user
from invenio_accounts.models import Role
from invenio_cache import current_cache
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_oaiserver.response import getrecord
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from lxml import etree
from passlib.handlers.oracle import oracle10
from weko_admin.models import AdminSettings
from weko_admin.utils import UsageReport, get_restricted_access
from weko_deposit.api import WekoDeposit
from weko_index_tree.api import Indexes
from weko_records.api import FeedbackMailList, ItemTypes, Mapping
from weko_records.models import ItemBilling
from weko_records.serializers.utils import get_mapping
from weko_records.utils import replace_fqdn
from weko_records_ui.models import InstitutionName
from weko_schema_ui.models import PublishStatus
from weko_workflow.api import WorkActivity, WorkFlow

from .models import FileOnetimeDownload, FilePermission
from .permissions import check_create_usage_report, \
    check_file_download_permission, check_user_group_permission, \
    is_open_restricted, get_file_price




def check_items_settings(settings=None):
    """Check items setting."""
    if settings is None:
        settings = AdminSettings.get('items_display_settings',dict_to_object=False)
    if settings is not None:
        if isinstance(settings,dict):
            if 'items_display_email' in settings:
                current_app.config['EMAIL_DISPLAY_FLG'] = settings['items_display_email']
            if 'items_search_author' in settings:    
                current_app.config['ITEM_SEARCH_FLG'] = settings['items_search_author']
            if 'item_display_open_date' in settings:    
                current_app.config['OPEN_DATE_DISPLAY_FLG'] = \
                settings['item_display_open_date']
        else:
            if hasattr(settings,'items_display_email'):
                current_app.config['EMAIL_DISPLAY_FLG'] = settings.items_display_email
            if hasattr(settings,'items_search_author'):
                current_app.config['ITEM_SEARCH_FLG'] = settings.items_search_author
            if hasattr(settings,'item_display_open_date'):
                current_app.config['OPEN_DATE_DISPLAY_FLG'] = settings.item_display_open_date


def get_record_permalink(record):
    """
    Get latest doi/cnri's value of record.

    :param record: index_name_english
    :return: pid value of doi/cnri.
    """
    doi = record.pid_doi
    cnri = record.pid_cnri

    if doi or cnri:
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

    Args:
        groups_price (list): The prices of Billing files set in each group [{'file_name': '003.jpg', 'groups_price': [{'group': '1', 'price': '100'}]}]

    Returns:
        dict: Billing file permission dictionary.
    """
    # current_app.logger.debug("groups_price:{}".format(groups_price))
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
    # current_app.logger.debug("groups_price:{}".format(groups_price))
    # current_app.logger.debug("billing_file_permission:{}".format(billing_file_permission))
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


def is_billing_item(record: Dict) -> bool:
    """Checks if item is a billing item based on its meta data schema."""

    for value in record.values():
        if not isinstance(value, dict):
            continue
        if value.get('attribute_type', '') != 'file':
            continue
        for file in value.get('attribute_value_mlt', []):
            if file.get('billing') and len(file.get('billing')) > 0 and file.get('billing')[0] == 'billing_file':
                if file.get('priceinfo'):
                    return True

    return False


def is_open_access(record: Dict) -> bool:
    """Checks if item is a open access item based on its meta data schema.

    Args:
        record (dict): item's meta data
    
    Returns:
        bool: open access item or not
    
    """
    target_index_list = record['path']
    public_index_list = Indexes.get_public_indexes_list()

    if not set(public_index_list).isdisjoint(set(target_index_list)):
        for value in record.values():
            if not isinstance(value, dict):
                continue
            if value.get('attribute_type', '') != 'file':
                continue
            for file in value.get('attribute_value_mlt', []):
                access_role = file.get('accessrole')
                open_access_date = dt.strptime(file.get('date')[0].get('dateValue'),
                                                '%Y-%m-%d').date()
                if access_role == 'open_access':
                    return True
                elif access_role == 'open_date' and open_access_date <= dt.now().date():
                    return True
    return False


def soft_delete(recid):
    """Soft delete item."""
    def get_cache_data(key: str):
        """Get cache data.

        :param key: Cache key.

        :return: Cache value.
        """
        return current_cache.get(key) or str()

    def check_an_item_is_locked(item_id=None):
        """Check if an item is locked.

        :param item_id: Item id.

        :return
        """
        locked_data = get_cache_data('item_ids_locked') or dict()
        ids = locked_data.get('ids', set())
        return item_id in ids

    try:
        if current_user:
            current_user_id = current_user.get_id()
        else:
            current_user_id = '1'
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=recid).first()
        if not pid:
            pid = PersistentIdentifier.query.filter_by(
                pid_type='recid', object_uuid=recid).first()
        if pid.status == PIDStatus.DELETED:
            return

        # Check Record is in import progress
        if check_an_item_is_locked(int(pid.pid_value.split(".")[0])):
            raise Exception({
                'is_locked': True,
                'msg': _('Item cannot be deleted because '
                         'the import is in progress.')
            })

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
        del_files = {}
        for ver in all_ver:
            depid = PersistentIdentifier.query.filter_by(
                pid_type='depid', object_uuid=ver.object_uuid).first()
            if depid:
                rec = RecordMetadata.query.filter_by(
                    id=ver.object_uuid).first()
                dep = WekoDeposit(rec.json, rec)
                #dep['path'] = []
                dep['publish_status'] = PublishStatus.DELETE.value
                dep.indexer.update_es_data(dep, update_revision=False, field='publish_status')
                FeedbackMailList.delete(ver.object_uuid)
                dep.remove_feedback_mail()
                for i in range(len(dep.files)):
                    if dep.files[i].file.uri not in del_files:
                        del_files[dep.files[i].file.uri] = dep.files[i].file.storage()
                        dep.files[i].bucket.location.size -= dep.files[i].file.size
                    dep.files[i].bucket.deleted = True
                dep.commit()
            pids = PersistentIdentifier.query.filter_by(
                object_uuid=ver.object_uuid)
            for p in pids:
                p.status = PIDStatus.DELETED
            db.session.commit()
        for file_storage in del_files.values():
            file_storage.delete()

        current_app.logger.info(
            'user({0}) deleted record id({1}).'.format(current_user_id, recid))
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
        all_ver = versioning.get_children(
            pid_status=PIDStatus.DELETED, ordered=True).all()
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
                rec = RecordMetadata.query.filter_by(
                    id=ver.object_uuid).first()
                dep = WekoDeposit(rec.json, rec)
                dep['publish_status'] = PublishStatus.PUBLIC.value
                dep.indexer.update_es_data(dep, update_revision=False, field='publish_status')
                dep.commit()
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

    # current_app.logger.debug("license:{}".format(license))
    # current_app.logger.debug("item_metadata_json:{}".format(item_metadata_json))
    # current_app.logger.debug("pdf:{}".format(pdf))
    # current_app.logger.debug("file_item_id:{}".format(file_item_id))
    # current_app.logger.debug("footer_w:{}".format(footer_w))
    # current_app.logger.debug("footer_h:{}".format(footer_h))
    # current_app.logger.debug("cc_logo_xposition:{}".format(cc_logo_xposition))
    # current_app.logger.debug("item:{}".format(item))
        
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
    current_app.logger.debug("name_keys:{}".format(name_keys))
    current_app.logger.debug("lang_keys:{}".format(lang_keys))
    current_app.logger.debug("datas:{}".format(datas))
    
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


def hide_item_metadata(record, settings=None, item_type_mapping=None,
                       item_type_data=None):
    """Hiding emails and hidden item metadata.

    :param record:
    :param settings:
    :param item_type_mapping:
    :param item_type_data:
    :return:
    """
    from weko_items_ui.utils import get_ignore_item, hide_meta_data_for_role
    check_items_settings(settings)

    record['weko_creator_id'] = record.get('owner')

    if hide_meta_data_for_role(record):
        list_hidden = get_ignore_item(
            record['item_type_id'], item_type_mapping, item_type_data
        )
        record = hide_by_itemtype(record, list_hidden)
        
        hide_email = hide_meta_data_for_role(record)
        if hide_email:
            # Hidden owners_ext.email
            if record.get('_deposit') and \
                record['_deposit'].get('owners_ext') and record['_deposit']['owners_ext'].get('email'):
                del record['_deposit']['owners_ext']['email']

        if hide_email and not current_app.config['EMAIL_DISPLAY_FLG']:
            record = hide_by_email(record)


        record = hide_by_file(record)

        return True

    record.pop('weko_creator_id')
    return False


def hide_item_metadata_email_only(record):
    """Hiding emails only.

    :param record:
    :return:
    """
    from weko_items_ui.utils import hide_meta_data_for_role
    check_items_settings()

    record['weko_creator_id'] = record.get('owner')
    
    hide_email = hide_meta_data_for_role(record)
    if hide_email:
        # Hidden owners_ext.email
        if record.get('_deposit') and \
            record['_deposit'].get('owners_ext') and record['_deposit']['owners_ext'].get('email'):
            del record['_deposit']['owners_ext']['email']

    if hide_email and not current_app.config['EMAIL_DISPLAY_FLG']:
        record = hide_by_email(record)
        return True

    record.pop('weko_creator_id')
    return False


def hide_by_file(item_metadata):
    """Hiding file info.

    :param item_metadata:
    :return:
    """
    for key, value in item_metadata.items():
        if isinstance(value, dict) \
                and 'attribute_type' in value \
                and value['attribute_type'] == 'file' \
                and 'attribute_value_mlt' in value \
                and len(value['attribute_value_mlt']) > 0:
            for v in value['attribute_value_mlt'].copy():
                if 'accessrole' in v \
                        and v['accessrole'] == 'open_no':
                    value['attribute_value_mlt'].remove(v)

    return item_metadata


def hide_by_email(item_metadata):
    """Hiding emails.

    :param item_metadata:
    :return:
    """
    subitem_keys = current_app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS']

    # Hidden owners_ext.email
    if item_metadata.get('_deposit') and \
        item_metadata['_deposit'].get('owners_ext') and item_metadata['_deposit']['owners_ext'].get('email'):
        del item_metadata['_deposit']['owners_ext']['email']

    for item in item_metadata:
        _item = item_metadata[item]
        if isinstance(_item, dict) and \
                _item.get('attribute_value_mlt'):
            for _idx, _value in enumerate(_item['attribute_value_mlt']):
                if _value is not None:
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
        settings = AdminSettings.get('items_display_settings',dict_to_object=False)
        if settings and 'items_display_email' in settings:
            is_display = settings['items_display_email']
        else:
            is_display = False
        return is_display

    is_hide = item_type_show_email(item_type_id)
    is_display = item_setting_show_email()
    
    return not is_hide and is_display


def replace_license_free(record_metadata, is_change_label=True):
    """Change the item name 'licensefree' to 'license_note'.

    If 'licensefree' is not output as a value.
    The value of 'licensetype' is 'license_note'.

    :param record_metadata:
    :param is_change_label:
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


def replace_license_free_for_opensearch(search_result, is_change_label=True):
    """Change the item name 'licensefree' to 'license_note'.

    If 'licensefree' is not output as a value.
    The value of 'licensetype' is 'license_note'.

    :param search_result:
    :param is_change_label:
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

    for i in range(len(search_result['hits']['hits'])):
      for val in search_result['hits']['hits'][i]['_source']['_item_metadata'].values():
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

    :param record: all metadata of a record.
    :return: json files.
    """
    def get_file_size(p_file):
        """Get file size and convert to byte."""
        file_size = p_file.get('filesize', [{}])[0]
        file_size_value = file_size.get('value', 0)
        defined_unit = {'b': 1, 'kb': 1000, 'mb': 1000000,
                        'gb': 1000000000, 'tb': 1000000000000}
        if type(file_size_value) is str and ' ' in file_size_value:
            size_num = file_size_value.split(' ')[0]
            size_unit = file_size_value.split(' ')[1]
            unit_num = defined_unit.get(size_unit.lower(), 0)
            try:
                file_size_value = float(size_num) * unit_num
            except:
                file_size_value = -1
        return file_size_value

    def set_message_for_file(p_file):
        """Check Opendate is future date."""
        p_file['future_date_message'] = ""
        p_file['download_preview_message'] = ""
        access = p_file.get("accessrole", '')
        date = p_file.get('date')
        if access == "open_login" and not current_user.get_id():
            if not 'billing' in p_file:
                p_file['future_date_message'] = _("Restricted Access")
        elif access == "open_date":
            if date and isinstance(date, list) and date[0]:
                adt = date[0].get('dateValue')
                if adt is None:
                    adt = dt.date.max
                pdt = to_utc(dt.strptime(adt, '%Y-%m-%d'))
                if pdt > dt.utcnow():
                    message = "Download is available from {}/{}/{}."
                    p_file['future_date_message'] = _(message).format(
                        pdt.year, pdt.month, pdt.day)
                    message = "Download / Preview is available from {}/{}/{}."
                    p_file['download_preview_message'] = _(message).format(
                        pdt.year, pdt.month, pdt.day)

    def get_data_by_key_array_json(key, array_json, get_key):
        for item in array_json:
            if str(item.get('id')) == str(key):
                return item.get(get_key)

    def add_billing_info(p_file):
        '''ファイル情報に課金ファイルに関する情報を追加する'''

        # 課金ファイルのアクセス権限
        download_status = {}
        p_file['billing_file_permission'] = check_file_download_permission(record, p_file, check_billing_file=True, download_status=download_status)
        p_file['download_status'] = download_status
        if not p_file['billing_file_permission']:
            # 課金額
            p_file['file_price'], p_file['currency_unit'] = get_file_price(record['_deposit']['id'])

        user_role_name_list = list(current_user.roles or [])
        for priceinfo in p_file['priceinfo']:
            # 税込/税抜
            itemBilling = ItemBilling.query.filter_by(
                item_id=record['_deposit']['id'], role_id=int(priceinfo['billingrole'])).one_or_none()
            priceinfo['tax'] = 'include_tax' if itemBilling and itemBilling.include_tax else 'without_tax'

            # ロールIDをロール名に変換
            role = next(filter(lambda x: x['id'] == int(priceinfo['billingrole']), roles), None)
            if role:
                priceinfo['billingrole'] = role['name']

            # ユーザーがこのロールをもっているかどうか
            priceinfo['has_role'] = priceinfo['billingrole'] in user_role_name_list

    workflows = get_workflows()
    roles = get_roles()
    terms = get_terms()

    is_display_file_preview = False
    files = []
    file_order = 0
    for key in record:
        meta_data = record.get(key)
        if type(meta_data) == dict and \
                meta_data.get('attribute_type', '') == "file":
            file_metadata = meta_data.get("attribute_value_mlt", [])
            for f in file_metadata:
                if check_file_download_permission(record, f, True)\
                        or is_open_restricted(f):
                    # Set default version_id.
                    f["version_id"] = f.get('version_id', '')
                    # Set is_thumbnail flag.
                    f["is_thumbnail"] = f.get('is_thumbnail', False)
                    # Check Opendate is future date.
                    set_message_for_file(f)
                    # Check show preview area.
                    base_url = "/record/{}/files/{}".format(
                        record.get('recid'),
                        f.get("filename")
                    )
                    url = f.get("url", {}).get("url", '')
                    if url and f["version_id"]:
                        # Check and change FQDN.
                        url = replace_fqdn(url)
                        f['url']['url'] = url
                    if base_url in url:
                        is_display_file_preview = True

                    #current_app.logger.error("base_url: {0}".format(base_url))
                    #current_app.logger.error("url: {0}".format(url))
                    # current_app.logger.debug(
                    #     "is_display_file_preview: {0}".format(is_display_file_preview))

                    # Get file size and convert to byte.
                    f['size'] = get_file_size(f)
                    f['mimetype'] = f.get('format', '')
                    f['filename'] = f.get('filename', '')
                    term = f.get("terms")
                    if term and term == 'term_free':
                        f["terms"] = 'term_free'
                        f["terms_content"] = f.get("termsDescription", '')
                    elif term:
                        f["terms"] = get_data_by_key_array_json(
                            term, terms, 'name')
                        f["terms_content"] = \
                            get_data_by_key_array_json(term, terms, 'content')
                    provide = f.get("provide")
                    if provide:
                        for p in provide:
                            workflow = p.get('workflow')
                            if workflow:
                                p['workflow_id'] = workflow
                                p['workflow'] = get_data_by_key_array_json(
                                    workflow, workflows, 'flows_name')
                            role = p.get('role')
                            if role:
                                p['role_id'] = role
                                p['role'] = get_data_by_key_array_json(
                                    role, roles, 'name')
                    f['file_order'] = file_order
                    if 'billing' in f:
                        add_billing_info(f)
                    files.append(f)
                file_order += 1
    return is_display_file_preview, files


def check_and_create_usage_report(record, file_object):
    """Check and create usage report.

    :param file_object:
    :param record:
    :return:
    """
    access_role = file_object.get('accessrole', '')
    if 'open_restricted' in access_role:
        permission = check_create_usage_report(record, file_object)
        if permission is not None:
            from weko_workflow.utils import create_usage_report
            activity_id = create_usage_report(
                permission.usage_application_activity_id)
            if activity_id is not None:
                FilePermission.update_usage_report_activity_id(permission,
                                                               activity_id)


def create_usage_report_for_user(onetime_download_extra_info: dict):
    """Create usage report for user.

    @param onetime_download_extra_info:
    @return:
    """
    current_app.logger.debug("onetime_download_extra_info:{}".format(onetime_download_extra_info))
    activity_id = onetime_download_extra_info.get(
        'usage_application_activity_id')
    is_guest = onetime_download_extra_info.get('is_guest', False)

    # Get Usage Application Activity.
    from weko_workflow.utils import create_record_metadata_for_user
    usage_application_activity = WorkActivity().get_activity_by_id(
        activity_id)

    extra_info_application = usage_application_activity.extra_info

    # Get usage report WF.
    usage_report_workflow = WorkFlow().find_workflow_by_name(
        current_app.config['WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME'])

    if not usage_report_workflow:
        return ""

    # Get usage application record meta data
    rec = RecordMetadata.query.filter_by(
        id=usage_application_activity.item_id).first()
    record_metadata = rec.json
    data_dict = dict()
    get_data_usage_application_data(record_metadata, data_dict)
    # Prepare data for activity.
    activity_data = {
        'workflow_id': usage_report_workflow.id,
        'flow_id': usage_report_workflow.flow_id,
        'activity_confirm_term_of_use': True,
        'extra_info': {
            "record_id": extra_info_application.get('record_id'),
            "related_title": extra_info_application.get('related_title'),
            "file_name": extra_info_application.get('file_name'),
            "usage_record_id": str(usage_application_activity.item_id),
            "usage_activity_id": str(activity_id),
            "is_guest": is_guest,
            "usage_application_record_data": data_dict,
        }
    }

    if is_guest:
        # Setting user mail.
        activity_data['extra_info']['guest_mail'] = extra_info_application.get(
            'guest_mail')
        # Create activity and URL for guest user.
        from weko_workflow.utils import init_activity_for_guest_user
        activity, __ = init_activity_for_guest_user(
            activity_data, True)
    else:
        # Setting user mail.
        activity_data['extra_info']['user_mail'] = extra_info_application.get(
            'user_mail')
        activity_data['activity_login_user'] = usage_application_activity \
            .activity_login_user
        activity_data['activity_update_user'] = usage_application_activity \
            .activity_login_user
        # Create activity and URL for registered user.
        activity = WorkActivity().init_activity(activity_data)
    create_record_metadata_for_user(usage_application_activity, activity)
    return activity


def get_data_usage_application_data(record_metadata, data_result: dict):
    """Get usage application data.

    Args:
        record_metadata (Union[list, dict]):
        data_result (dict):
    """
    current_app.logger.debug("record_metadata:{}".format(record_metadata))
    current_app.logger.debug("data_result:{}".format(data_result))

    if isinstance(record_metadata, dict):
        for k, v in record_metadata.items():
            if isinstance(v, str) and k.startswith("subitem_") \
                    and "_guarantor_" not in k:
                data_result[k] = v
            else:
                get_data_usage_application_data(v, data_result)
    elif isinstance(record_metadata, list):
        for metadata in record_metadata:
            get_data_usage_application_data(metadata, data_result)


def send_usage_report_mail_for_user(guest_mail: str, temp_url: str):
    """Send usage application mail for user.

    @param guest_mail:
    @param temp_url:
    @return:
    """
    current_app.logger.debug("guest_mail:{}".format(guest_mail))
    current_app.logger.debug("temp_url:{}".format(temp_url))
    # Mail information
    mail_info = {
        'template': current_app.config.get(
            "WEKO_WORKFLOW_USAGE_REPORT_ACTIVITY_URL"),
        'mail_address': guest_mail,
        'url_guest_user': temp_url
    }
    from weko_workflow.utils import send_mail_url_guest_user
    return send_mail_url_guest_user(mail_info)


def check_and_send_usage_report(extra_info, user_mail):
    """Check and send usage report for user.

    @param extra_info:
    @param user_mail:
    @return:
    """
    current_app.logger.debug("extra_info:{}".format(extra_info))
    current_app.logger.debug("user_mail:{}".format(user_mail))

    if not extra_info.get('send_usage_report'):
        return
    activity = create_usage_report_for_user(extra_info)
    mail_template = current_app.config.get(
        "WEKO_WORKFLOW_USAGE_REPORT_ACTIVITY_URL")
    usage_report = UsageReport()
    if not activity:
        return _("Unexpected error occurred.")
    if not usage_report.send_reminder_mail([], mail_template, [activity]):
        return _("Failed to send mail.")
    extra_info['send_usage_report'] = False


def generate_one_time_download_url(
    file_name: str, record_id: str, guest_mail: str
) -> str:
    """Generate one time download URL.

    :param file_name: File name
    :param record_id: File Version ID
    :param guest_mail: guest email
    :return:
    """    
    secret_key = current_app.config['WEKO_RECORDS_UI_SECRET_KEY']
    download_pattern = current_app.config[
        'WEKO_RECORDS_UI_ONETIME_DOWNLOAD_PATTERN']
    current_date = dt.utcnow().strftime("%Y-%m-%d")
    hash_value = download_pattern.format(file_name, record_id, guest_mail,
                                         current_date)
    secret_token = oracle10.hash(secret_key, hash_value)

    token_pattern = "{} {} {} {}"
    token = token_pattern.format(record_id, guest_mail, current_date,
                                 secret_token)
    token_value = base64.b64encode(token.encode()).decode()
    host_name = request.host_url
    url = "{}record/{}/file/onetime/{}?token={}" \
        .format(host_name, record_id, file_name, token_value)
    return url


def parse_one_time_download_token(token: str) -> Tuple[str, Tuple]:
    """Parse onetime download token.

    @param token:
    @return:
    """
    # current_app.logger.debug("token:{}".format(token))
    error = _("Token is invalid.")
    if token is None:
        return error, ()
    try:
        decode_token = base64.b64decode(token.encode()).decode()
        param = decode_token.split(" ")
        if not param or len(param) != 4:
            return error, ()

        return "", (param[0], param[1], param[2], param[3])
    except Exception as err:
        current_app.logger.error(err)
        return error, ()


def validate_onetime_download_token(
    onetime_download: FileOnetimeDownload, file_name: str, record_id: str,
    guest_mail: str, date: str, token: str
) -> Tuple[bool, str]:
    """Validate onetime download token.

    @param onetime_download:
    @param file_name:
    @param record_id:
    @param guest_mail:
    @param date:
    @param token:
    @return:
    """
    # current_app.logger.debug("onetime_download:{}".format(onetime_download))
    # current_app.logger.debug("file_name:{}".format(file_name))
    # current_app.logger.debug("record_id:{}".format(record_id))
    # current_app.logger.debug("guest_mail:{}".format(guest_mail))
    # current_app.logger.debug("date:{}".format(date))
    # current_app.logger.debug("token:{}".format(token))

    token_invalid = _("Token is invalid.")
    secret_key = current_app.config['WEKO_RECORDS_UI_SECRET_KEY']
    download_pattern = current_app.config[
        'WEKO_RECORDS_UI_ONETIME_DOWNLOAD_PATTERN']
    hash_value = download_pattern.format(
        file_name, record_id, guest_mail, date)
    if not oracle10.verify(secret_key, token, hash_value):
        current_app.logger.debug('Validate token error: {}'.format(hash_value))
        return False, token_invalid
    try:
        if not onetime_download:
            return False, token_invalid
        try:
            expiration_date = timedelta(onetime_download.expiration_date)
            download_date = onetime_download.created.date() + expiration_date
            current_date = dt.utcnow().date()
            if current_date > download_date:
                return False, _(
                    "The expiration date for download has been exceeded.")
        except OverflowError:
            current_app.logger.error('date value out of range:',
                                     onetime_download.expiration_date)

        if onetime_download.download_count <= 0:
            return False, _("The download limit has been exceeded.")
        return True, ""
    except Exception as err:
        current_app.logger.error('Validate onetime download token error:')
        current_app.logger.error(err)
        return False, token_invalid


def is_private_index(record):
    """Check index of workflow is private.

    :param record:Record data.
    :return:
    """
    from weko_index_tree.api import Indexes
    list_index = record.get("path")
    indexes = Indexes.get_path_list(list_index)
    publish_state = 6
    for index in indexes:
        if len(indexes) == 1:
            if not index[publish_state]:
                return True
        else:
            if index[publish_state]:
                return False
    return False


def validate_download_record(record: dict):
    """Validate record.

    :param record:
    """
    if record['publish_status'] != PublishStatus.PUBLIC.value:
        abort(403)
    if is_private_index(record):
        abort(403)


def get_onetime_download(file_name: str, record_id: str,
                         user_mail: str):
    """Get onetime download count.

    @param file_name:
    @param record_id:
    @param user_mail:
    @return:
    """
    file_downloads = FileOnetimeDownload.find(
        file_name=file_name, record_id=record_id, user_mail=user_mail
    )
    if file_downloads and len(file_downloads) > 0:
        return file_downloads[0]
    else:
        return None


def create_onetime_download_url(
    activity_id: str, file_name: str, record_id: str, user_mail: str,
    is_guest: bool = False
):
    """Create onetime download.

    :param activity_id:
    :param file_name:
    :param record_id:
    :param user_mail:
    :param is_guest:
    :return:
    """
    content_file_download = get_restricted_access('content_file_download')
    if isinstance(content_file_download, dict):
        expiration_date = content_file_download.get("expiration_date", 30)
        download_limit = content_file_download.get("download_limit", 10)
        extra_info = dict(
            usage_application_activity_id=activity_id,
            send_usage_report=True,
            is_guest=is_guest
        )
        file_onetime = FileOnetimeDownload.create(**{
            "file_name": file_name,
            "record_id": record_id,
            "user_mail": user_mail,
            "expiration_date": expiration_date,
            "download_count": download_limit,
            "extra_info": extra_info,
        })
        return file_onetime
    return False


def update_onetime_download(**kwargs) -> NoReturn:
    """Update onetime download.

    @param kwargs:
    @return:
    """
    return FileOnetimeDownload.update_download(**kwargs)


def get_workflows():
    """Get workflow.

    @return:
    """
    workflow = WorkFlow()
    workflows = workflow.get_workflow_list()
    init_workflows = []
    for workflow in workflows:
        if workflow.open_restricted:
            init_workflows.append(
                {'id': workflow.id, 'flows_name': workflow.flows_name})
    return init_workflows


def get_roles():
    """Get roles.

    @return:
    """
    roles = Role.query.all()
    init_roles = [{'id': 'none_loggin', 'name': _('Guest')}]
    for role in roles:
        init_roles.append({'id': role.id, 'name': role.name})
    return init_roles


def get_terms():
    """Get all terms and conditions.

    @return:
    """
    terms_result = [{'id': 'term_free', 'name': _('Free Input')}]
    terms_list = get_restricted_access('terms_and_conditions')
    current_lang = current_i18n.language
    for term in terms_list:
        terms_result.append(
            {'id': term.get("key"), "name": term.get("content", {}).
                get(current_lang, "en").get("title", ""),
                "content": term.get("content", {}).
                get(current_lang, "en").get("content", "")}
        )
    return terms_result


def display_oaiset_path(record_metadata):
    """Display _oai.sets in metadata by path.

    Args:
        record_metadata ([type]): [description]
    """
    from weko_index_tree.api import Indexes

    sets = record_metadata.get('path', [])
    index_paths = []
    if sets:
        paths = Indexes.get_path_name(sets)
        for path in paths:
            if path.public_state and path.harvest_public_state:
                index_paths.append(path.path.replace('/', ':'))

    record_metadata['_oai']['sets'] = index_paths


def get_google_scholar_meta(record, record_tree=None):
    """
    _get_google_scholar_meta [make a google scholar metadata]

    [extended_summary]

    Args:
        record ([type]): [description]
        record_tree (etree): Return value of getrecord method

    Returns:
        [type]: [description]
    """
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

    if '_oai' not in record and 'id' not in record['_oai']:
        return
    if record_tree is None:
        recstr = etree.tostring(
            getrecord(
                identifier=record['_oai'].get('id'),
                metadataPrefix='jpcoar',
                verb='getrecord'))
        et = etree.fromstring(recstr)
    else:
        et = record_tree

    mtdata = et.find('getrecord/record/metadata/', namespaces=et.nsmap)
    if mtdata is None:
        return

    # Check to outputable resource type by config
    resource_type_allowed = False
    for resource_type in mtdata.findall('dc:type', namespaces=mtdata.nsmap):
        if resource_type.text in current_app.config['WEKO_RECORDS_UI_GOOGLE_SCHOLAR_OUTPUT_RESOURCE_TYPE']:
            resource_type_allowed = True
            break
    if not resource_type_allowed:
        return

    res = []
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
            'jpcoar:relation/jpcoar:relatedIdentifier',
            namespaces=mtdata.nsmap):
        if 'identifierType' in relatedIdentifier.attrib and \
            relatedIdentifier.attrib[
                'identifierType'] == 'DOI':
            res.append({'name': 'citation_doi',
                        'data': relatedIdentifier.text})
    for creator in mtdata.findall(
            'jpcoar:creator/jpcoar:creatorName',
            namespaces=mtdata.nsmap):
        res.append({'name': 'citation_author', 'data': creator.text})
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
                    'data': quote(pdf_url.text,'/:%')})

    res.append({'name': 'citation_dissertation_institution',
                'data': InstitutionName.get_institution_name()})
    record_route = current_app.config['RECORDS_UI_ENDPOINTS']['recid']['route']
    record_url = '{protocol}://{host}{path}'.format(
        protocol=request.environ['wsgi.url_scheme'],
        host=request.environ['HTTP_HOST'],
        path=record_route.replace('<pid_value>', record['recid'])
    )
    res.append({'name': 'citation_abstract_html_url', 'data': record_url})
    return res

def get_google_detaset_meta(record,record_tree=None):
    """
    _get_google_detaset_meta [summary]

    [extended_summary]

    Args:
        record ([type]): [description]
        record_tree (etree): Return value of getrecord method

    Returns:
        [type]: [description]
    """
    from .config import WEKO_RECORDS_UI_GOOGLE_DATASET_RESOURCE_TYPE, \
    WEKO_RECORDS_UI_GOOGLE_DATASET_DESCRIPTION_MIN, \
    WEKO_RECORDS_UI_GOOGLE_DATASET_DESCRIPTION_MAX, \
    WEKO_RECORDS_UI_GOOGLE_DATASET_DISTRIBUTION_BUNDLE

    current_app.logger.debug("get_google_detaset_meta: {}".format(record.id))

    if not current_app.config['WEKO_RECORDS_UI_GOOGLE_SCHOLAR_OUTPUT_RESOURCE_TYPE']:
        return

    if '_oai' not in record and 'id' not in record['_oai']:
        return
    if record_tree is None:
        recstr = etree.tostring(
            getrecord(
                identifier=record['_oai'].get('id'),
                metadataPrefix='jpcoar',
                verb='getrecord'))
        et = etree.fromstring(recstr)
    else:
        et = record_tree
    mtdata = et.find('getrecord/record/metadata/', namespaces=et.nsmap)
    if mtdata is None:
        return

    output_resource_types = current_app.config.get('WEKO_RECORDS_UI_GOOGLE_DATASET_RESOURCE_TYPE',WEKO_RECORDS_UI_GOOGLE_DATASET_RESOURCE_TYPE)
    # Check resource type is 'dataset'
    resource_type_allowed = False
    for resource_type in mtdata.findall('dc:type', namespaces=mtdata.nsmap):
        if resource_type.text in output_resource_types:
            resource_type_allowed = True
            break

    if not resource_type_allowed:
        current_app.logger.debug("resource_type_allowed: {}".format(resource_type_allowed))
        return

    res_data = {'@context': 'https://schema.org/', '@type': 'Dataset'}

    # Required property check
    min_length = current_app.config.get('WEKO_RECORDS_UI_GOOGLE_DATASET_DESCRIPTION_MIN',WEKO_RECORDS_UI_GOOGLE_DATASET_DESCRIPTION_MIN)
    max_length = current_app.config.get('WEKO_RECORDS_UI_GOOGLE_DATASET_DESCRIPTION_MAX',WEKO_RECORDS_UI_GOOGLE_DATASET_DESCRIPTION_MAX)
    
    for title in mtdata.findall('dc:title', namespaces=mtdata.nsmap):
        res_data['name'] = title.text
    for description in mtdata.findall('datacite:description', namespaces=mtdata.nsmap):
        description_text = description.text
        if len(description_text) >= min_length:
            if len(description_text) > max_length:
                description_text = description_text[:max_length]
            res_data['description'] = description_text

    if 'name' not in res_data or 'description' not in res_data:
        current_app.logger.debug("resource_type_allowed: {}".format(resource_type_allowed))
        return

    # includedInDataCatalog
    repository_url = current_app.config['THEME_SITEURL']
    res_data['includedInDataCatalog'] = {
        '@type': 'DataCatalog', 'name': repository_url}

    # jpcoar:creator
    creators_data = []
    for creator in mtdata.findall('jpcoar:creator', namespaces=mtdata.nsmap):
        givenName = creator.find('jpcoar:givenName', namespaces=creator.nsmap)
        familyName = creator.find(
            'jpcoar:familyName', namespaces=creator.nsmap)
        name = creator.find('jpcoar:creatorName', namespaces=creator.nsmap)
        identifier = creator.find(
            'jpcoar:nameIdentifier', namespaces=creator.nsmap)
        alternateName = creator.find(
            'jpcoar:creatorAlternative', namespaces=creator.nsmap)
        affiliations = []
        for affiliation in mtdata.findall('jpcoar:affiliation', namespaces=mtdata.nsmap):
            affiliation_data = {'@type': 'Organization'}
            affiliationNameIdentifier = affiliation.find(
                'jpcoar:nameIdentifier', namespaces=affiliation.nsmap)
            affiliationName = affiliation.find(
                'jpcoar:nameIdentifier', namespaces=affiliation.nsmap)
            if affiliationNameIdentifier is not None and len(affiliationNameIdentifier.text) > 0:
                affiliation_data['identifier'] = affiliationNameIdentifier.text
            if affiliationName is not None and len(affiliationName.text) > 0:
                affiliation_data['name'] = affiliationName.text
            affiliations.append(affiliation_data)

        creator_data = {'@type': 'Person'}
        if givenName is not None and len(givenName.text) > 0:
            creator_data['givenName'] = givenName.text
        if familyName is not None and len(familyName.text) > 0:
            creator_data['familyName'] = familyName.text
        if name is not None and len(name.text) > 0:
            creator_data['name'] = name.text
        if identifier is not None and len(identifier.text) > 0:
            creator_data['identifier'] = identifier.text
        if alternateName is not None and len(alternateName.text) > 0:
            creator_data['alternateName'] = alternateName.text
        if len(affiliations) > 0:
            creator_data['affiliation'] = affiliations

        creators_data.append(creator_data)

    if len(creators_data) > 0:
        res_data['creator'] = creators_data

    # jpcoar:identifier
    identifiers = []
    for identifier in mtdata.findall('jpcoar:identifier', namespaces=mtdata.nsmap):
        identifiers.append(identifier.text)
    if len(identifiers) > 0:
        res_data['citation'] = identifiers

    # jpcoar:subject
    subjects = []
    for subject in mtdata.findall('jpcoar:subject', namespaces=mtdata.nsmap):
        subjects.append(subject.text)
    if len(subjects) > 0:
        res_data['keywords'] = subjects

    # dc:rights
    rights_list = []
    for rights in mtdata.findall('dc:rights', namespaces=mtdata.nsmap):
        rights_list.append(rights.text)
    if len(rights_list) > 0:
        res_data['license'] = rights_list

    # datacite:geoLocation
    geo_locations = []
    for geo_location in mtdata.findall('datacite:geoLocation', namespaces=mtdata.nsmap):
        # geoLocationPoint
        point_longitude = geo_location.find(
            'datacite:geoLocationPoint/datacite:pointLongitude', namespaces=geo_location.nsmap)
        point_latitude = geo_location.find(
            'datacite:geoLocationPoint/datacite:pointLatitude', namespaces=geo_location.nsmap)
        if point_longitude is not None and len(point_longitude.text) > 0 and point_latitude is not None and len(point_latitude.text) > 0:
            geo_locations.append({
                '@type': 'Place',
                'geo': {
                    '@type': 'GeoCoordinates',
                    'latitude': point_latitude.text,
                    'longitude': point_longitude.text,
                }
            })

        # geoLocationBox
        box_west_bound_longitude = geo_location.find(
            'datacite:geoLocationBox/datacite:westBoundLongitude', namespaces=geo_location.nsmap)
        box_east_bound_longitude = geo_location.find(
            'datacite:geoLocationBox/datacite:eastBoundLongitude', namespaces=geo_location.nsmap)
        box_south_bound_latitude = geo_location.find(
            'datacite:geoLocationBox/datacite:southBoundLatitude', namespaces=geo_location.nsmap)
        box_north_bound_latitude = geo_location.find(
            'datacite:geoLocationBox/datacite:northBoundLatitude', namespaces=geo_location.nsmap)
        if box_west_bound_longitude is not None and len(box_west_bound_longitude.text) > 0 \
                and box_east_bound_longitude is not None and len(box_east_bound_longitude.text) > 0 \
                and box_south_bound_latitude is not None and len(box_south_bound_latitude.text) > 0 \
                and box_north_bound_latitude is not None and len(box_north_bound_latitude.text) > 0:
            geo_locations.append({
                '@type': 'Place',
                'geo': {
                    '@type': 'GeoShape',
                    'box': '{} {} {} {}'.format(
                        box_west_bound_longitude.text,
                        box_south_bound_latitude.text,
                        box_east_bound_longitude.text,
                        box_north_bound_latitude.text)
                }
            })

        # geoLocationPlace
        for geo_location_place in geo_location.findall('datacite:geoLocationPlace', namespaces=geo_location.nsmap):
            if len(geo_location_place.text) > 0:
                geo_locations.append(geo_location_place.text)

    if len(geo_locations) > 0:
        res_data['spatialCoverage'] = geo_locations

    # dcterms:temporal
    temporal_coverages = []
    for temporal_coverage in mtdata.findall('dcterms:temporal', namespaces=mtdata.nsmap):
        temporal_coverages.append(temporal_coverage.text)
    if len(temporal_coverages) > 0:
        res_data['temporalCoverage'] = temporal_coverages

    # jpcoar:file
    distributions = []
    for file in mtdata.findall('jpcoar:file', namespaces=mtdata.nsmap):
        uri = file.find('jpcoar:URI', namespaces=file.nsmap)
        mime_type = file.find('jpcoar:mimeType', namespaces=file.nsmap)

        distribution = {'@type': 'DataDownload'}
        if uri is not None and len(uri.text) > 0:
            distribution['contentUrl'] = quote(uri.text,'/:%')
        if mime_type is not None and len(mime_type.text) > 0:
            distribution['encodingFormat'] = mime_type.text
        distributions.append(distribution)
    if len(distributions) > 0:
        adding_bundles = current_app.config.get('WEKO_RECORDS_UI_GOOGLE_DATASET_DISTRIBUTION_BUNDLE',WEKO_RECORDS_UI_GOOGLE_DATASET_DISTRIBUTION_BUNDLE)
        if adding_bundles is not None:
            for bundle in adding_bundles:
                distribution = {'@type': 'DataDownload'}
                if 'contentUrl' in bundle:
                    distribution['contentUrl'] = quote(bundle['contentUrl'],'/:%')
                    if 'encodingFormat' in bundle:
                        distribution['encodingFormat'] = bundle['encodingFormat']
                    distributions.append(distribution)
        res_data['distribution'] = distributions

    current_app.logger.debug("res_data: {}".format(orjson.dumps(res_data).decode()))

    return orjson.dumps(res_data).decode()

def get_billing_role(record: Dict) -> Tuple[str, str]:
    """Get the lowest price and roll.

    Args:
        record (dict): Record metadata

    Returns:
        tuple[str, str]: role, price(min)
    """
    user_roles = current_user.roles
    user_role_ids = [role.id for role in user_roles]

    price_info_key = 'priceinfo'

    billing_role_key = 'billingrole'
    billing_price_key = 'price'

    min_price_info = None
    role_prices = []
    for _, value in record.items():
        if not isinstance(value, dict):
            continue

        if value.get('attribute_type') == 'file':
            for file_item in value.get('attribute_value_mlt', []):
                price_info = file_item.get(price_info_key, [])
                role_prices.extend([role_price for role_price in price_info \
                                    if int(role_price.get(billing_role_key, '-1')) in user_role_ids \
                                        and billing_price_key in role_price.keys()])

    if len(role_prices) > 0:
        min_price_info = min(role_prices, key=lambda info: int(info[billing_price_key]))

    if min_price_info is None or billing_role_key not in min_price_info.keys():
        return 'guest', ''

    min_role = Role.query.get(int(min_price_info.get(billing_role_key)))
    return min_role.name, min_price_info.get(billing_price_key, '')
