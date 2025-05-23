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
import os
import six
import datetime
from datetime import datetime as dt
from datetime import timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from urllib.parse import quote

from flask import abort, current_app, json, request, Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babelex import gettext as _
from flask_babelex import to_utc
from flask_login import current_user
from sqlalchemy import desc
from invenio_accounts.models import Role, User
from invenio_cache import current_cache
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_oaiserver.response import getrecord
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_records_ui.utils import obj_or_import_string
from lxml import etree
from passlib.handlers.oracle import oracle10
from weko_admin.models import AdminSettings
from weko_admin.utils import UsageReport, get_restricted_access
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_records.api import FeedbackMailList, ItemTypes, Mapping
from weko_records.serializers.utils import get_mapping
from weko_records.utils import custom_record_medata_for_export, replace_fqdn
from weko_records.models import ItemReference
from weko_schema_ui.models import PublishStatus
from weko_workflow.api import WorkActivity, WorkFlow, UpdateItem
from weko_workflow.models import ActivityStatusPolicy

from weko_records_ui.models import InstitutionName
from weko_workflow.models import Activity

from .models import FileOnetimeDownload, FilePermission, FileSecretDownload
from .permissions import check_create_usage_report, \
    check_file_download_permission, check_user_group_permission, \
    is_open_restricted


def is_future(date):
    """Checks if a date is in the future."""
    res = True
    if date:
        try:
            if isinstance(date, str):
                pdt = None
                if len(date) == 10:
                    pdt = dt.strptime(date, '%Y-%m-%d')
                else:
                    if 'T' in date:
                        pdt = dt.strptime(date[:19], '%Y-%m-%dT%H:%M:%S')
                    else:
                        pdt = dt.strptime(date[:19], '%Y-%m-%d %H:%M:%S')
                if pdt:
                    res = to_utc(pdt) > dt.utcnow()
            elif isinstance(date, dt):
                res = to_utc(date) > dt.utcnow()
        except Exception as ex:
            current_app.logger.error(ex)
    return res

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


def is_workflow_activity_work(item_id):
    is_work = True
    workflow = WorkActivity()
    acitvity = workflow.get_workflow_activity_by_item_id(item_id)
    if not acitvity or acitvity.activity_status in [
            ActivityStatusPolicy.ACTIVITY_FINALLY,
            ActivityStatusPolicy.ACTIVITY_CANCEL]:
        is_work = False
    return is_work


def get_latest_version(id_without_version):
    """Get latest version ID to store item of before updating."""
    version_id = 1
    pid_value = "{}.%".format(id_without_version)
    pid = PersistentIdentifier.query\
        .filter_by(pid_type='recid', status=PIDStatus.REGISTERED)\
        .filter(PersistentIdentifier.pid_value.like(pid_value)).all()
    if pid:
        for idx in pid:
            rec = RecordMetadata.query.filter_by(
                id=idx.object_uuid).first()
            if rec and rec.json and \
                    rec.json.get('_deposit', {}).get('status') == 'published':
                temp_ver = int(idx.pid_value.split('.')[-1])
                version_id = temp_ver if temp_ver > version_id else version_id
    return "{}.{}".format(id_without_version, version_id)


def delete_version(recid):
    """Soft delete item version."""

    # get user id
    if current_user:
        current_user_id = current_user.get_id()
    else:
        current_user_id = '1'

    # check item version is exists
    pid = PersistentIdentifier.query.filter_by(
        pid_type='recid', pid_value=recid).first()
    if not pid:
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', object_uuid=recid).first()
    if pid.status == PIDStatus.DELETED:
        return

    id_without_version = recid.split('.')[0]
    latest_version = get_latest_version(id_without_version)
    is_latest_version = recid == latest_version

    # delete item version
    del_files = {}
    del_bucket = []
    depid = PersistentIdentifier.query.filter_by(
            pid_type='depid', object_uuid=pid.object_uuid).first()
    if depid:
        rec = RecordMetadata.query.filter_by(
                id=pid.object_uuid).first()
        dep = WekoDeposit(rec.json, rec)
        dep['publish_status'] = PublishStatus.DELETE.value
        dep.indexer.update_es_data(dep, update_revision=False, field='publish_status')
        FeedbackMailList.delete(pid.object_uuid)
        dep.remove_feedback_mail()
        for f in dep.files:
            if f.bucket not in del_bucket:
                del_bucket.append(f.bucket)
            if f.file.uri not in del_files:
                del_files[f.file.uri] = {
                    'storage': f.file.storage(),
                    'bucket': f.bucket,
                    'size': f.file.size
                }
        dep.commit()
        pids = PersistentIdentifier.query.filter_by(
            object_uuid=pid.object_uuid)
        for p in pids:
            p.status = PIDStatus.DELETED
    # delete file if only in the version
    versioning = PIDVersioning(child=pid)
    if versioning.exists:
        all_ver = versioning.children.all()
        for ver in all_ver:
            if '.' not in ver.pid_value and is_latest_version:
                continue
            if ver.object_uuid != pid.object_uuid:
                depid = PersistentIdentifier.query.filter_by(
                        pid_type='depid', object_uuid=ver.object_uuid).first()
                if depid:
                    rec = RecordMetadata.query.filter_by(
                            id=ver.object_uuid).first()
                    dep = WekoDeposit(rec.json, rec)
                    for f in dep.files:
                        if f.file.uri in del_files:
                            del_files.pop(f.file.uri)
    for v in del_files.values():
        v.get('storage').delete()
        bucket = v.get('bucket')
        bucket.location.size -= v.get('size')
    for b in del_bucket:
        b.deleted = True

    updated_item = UpdateItem()
    latest_version = get_latest_version(id_without_version)
    latest_pid = PersistentIdentifier.query.filter_by(
        pid_type='recid', pid_value=latest_version).first()
    latest_record = WekoDeposit.get_record(latest_pid.object_uuid)
    _publish_status = latest_record.get('publish_status', PublishStatus.PUBLIC.value)
    # update parent item
    if is_latest_version:
        pid_without_ver = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=id_without_version).first()
        parent_record = WekoDeposit.get_record(
            pid_without_ver.object_uuid)
        parent_deposit = WekoDeposit(parent_record, parent_record.model)

        new_parent_record = parent_deposit. \
            merge_data_to_record_without_version(latest_pid)
        feedback_mail_list = FeedbackMailList.get_mail_list_by_item_id(
                latest_pid.object_uuid)
        if feedback_mail_list:
            FeedbackMailList.update(
                item_id=pid_without_ver.object_uuid,
                feedback_maillist=feedback_mail_list
            )
        parent_deposit["relation_version_is_last"] = True
        parent_deposit.publish()
        new_parent_record.commit()
        updated_item.publish(new_parent_record, _publish_status)
        weko_record = WekoRecord.get_record_by_pid(
            pid_without_ver.pid_value)
        if weko_record:
            weko_record.update_item_link(latest_pid.pid_value)
    # update draft item
    draft_pid = PersistentIdentifier.get(
        'recid',
        '{}.0'.format(id_without_version)
    )
    if not is_workflow_activity_work(draft_pid.object_uuid):
        draft_deposit = WekoDeposit.get_record(
            draft_pid.object_uuid)
        new_draft_record = draft_deposit. \
            merge_data_to_record_without_version(latest_pid)
        feedback_mail_list = FeedbackMailList.get_mail_list_by_item_id(
                latest_pid.object_uuid)
        if feedback_mail_list:
            FeedbackMailList.update(
                item_id=draft_pid.object_uuid,
                feedback_maillist=feedback_mail_list
            )
        draft_deposit["relation_version_is_last"] = True
        draft_deposit.publish()
        new_draft_record.commit()
        updated_item.publish(new_draft_record, _publish_status)
        # update item link info of draft record
        weko_record = WekoRecord.get_record_by_pid(
            draft_deposit.pid.pid_value)
        if weko_record:
            weko_record.update_item_link(latest_pid.pid_value)
    # delete item link
    db.session.query(ItemReference).filter(
        ItemReference.src_item_pid == recid
    ).delete(synchronize_session='fetch')

    current_app.logger.info(
        'user({0}) deleted record version({1}).'.format(current_user_id, recid))


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
            for f in dep.files:
                if f.file.uri not in del_files:
                    del_files[f.file.uri] = f.file.storage()
                    f.bucket.location.size -= f.file.size
                    f.bucket.deleted = True
            dep.commit()
            pids = PersistentIdentifier.query.filter_by(
                object_uuid=ver.object_uuid)
            for p in pids:
                p.status = PIDStatus.DELETED
            #db.session.commit()
    for file_storage in del_files.values():
        file_storage.delete()

    current_app.logger.info(
        'user({0}) deleted record id({1}).'.format(current_user_id, recid))


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

def get_values_by_selected_lang(source_title, current_lang):
    """Get value by selected lang.

    @param source_title: e.g. [('None Language': 'test'), ('ja': 'テスト1'), ('ja', 'テスト2')]
    @param current_lang: e.g. 'ja'
    @return: e.g. ['テスト1','テスト2'] 
    """
    value_cur = []
    value_en = []
    value_latn = []
    title_data_langs = []
    title_data_langs_none = []
    for lang, value in source_title:
        title = {}
        if not value:
            continue
        elif current_lang == lang:
            value_cur.append(value)
        else:
            title[lang] = value
            if lang == "en":
                value_en.append(value)
            elif lang == "ja-Latn":
                value_latn.append(value)
            elif lang == "None Language":
                title_data_langs_none.append(value)
            elif lang:
                title_data_langs.append(title)
    if len(value_cur) > 0:
        return value_cur
    
    if len(title_data_langs_none)>0:
        source = source_title[0][1]
        target = title_data_langs_none[0]
        if source==target:
            return title_data_langs_none
        
    if len(value_latn) > 0:
        return value_latn

    if len(value_en) > 0 and (
        current_lang != "ja"
        or not current_app.config.get("WEKO_RECORDS_UI_LANG_DISP_FLG", False)
    ):
        return value_en

    if len(title_data_langs) > 0:
        if current_lang == "en":
            target_lang = ""
            for t in title_data_langs:
                
                if list(t)[0] != "ja" or not current_app.config.get(
                    "WEKO_RECORDS_UI_LANG_DISP_FLG", False
                ):
                    target_lang = list(t)[0]
            if target_lang:
                return [title_data[target_lang] for title_data in title_data_langs if target_lang in title_data]
                
        else:
            target_lang = list(title_data_langs[0].keys())[0]
            return [title_data[target_lang] for title_data in title_data_langs if target_lang in title_data]

    if len(title_data_langs_none) > 0:
        return title_data_langs_none
    else:
        return None


def hide_item_metadata(record, settings=None, item_type_data=None):
    """Hiding emails and hidden item metadata.

    :param record:
    :param settings:
    :param item_type_data:
    :return:
    """
    from weko_items_ui.utils import get_ignore_item, hide_meta_data_for_role
    check_items_settings(settings)

    record['weko_creator_id'] = record.get('owner')

    if hide_meta_data_for_role(record):
        list_hidden = get_ignore_item(
            record['item_type_id'], item_type_data
        )
        record = hide_by_itemtype(record, list_hidden)
        
        hide_email = hide_meta_data_for_role(record)
        if hide_email:
            # Hidden owners_ext.email
            if record.get('_deposit') and \
                record['_deposit'].get('owners_ext') and record['_deposit']['owners_ext'].get('email'):
                del record['_deposit']['owners_ext']['email']

        if hide_email and not current_app.config['EMAIL_DISPLAY_FLG']:
            record = hide_by_email(record, True)


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
        record = hide_by_email(record, True)
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


def hide_by_email(item_metadata, force_flag=False, item_type=None):
    """Hiding emails.

    :param item_metadata:
    :param force_flag: force to hide
    :param item_type: item type data
    :return:
    """
    from weko_items_ui.utils import get_options_and_order_list, get_hide_list_by_schema_form
    show_email_flag = item_setting_show_email()
    subitem_keys = current_app.config['WEKO_RECORDS_UI_EMAIL_ITEM_KEYS']

    item_type_id = item_metadata.get('item_type_id')

    if item_type_id:
        hide_list = []
        if item_type:
            meta_options = get_options_and_order_list(
                item_type_id,
                item_type_data=ItemTypes(item_type.schema, model=item_type),
                mapping_flag=False)
            hide_list = get_hide_list_by_schema_form(schemaform=item_type.render.get('table_row_map', {}).get('form', []))
        else:
            meta_options = get_options_and_order_list(item_type_id, mapping_flag=False)

        # Hidden owners_ext info
        if item_metadata.get('_deposit') and \
                item_metadata['_deposit'].get('owners_ext'):
            del item_metadata['_deposit']['owners_ext']

        for item in item_metadata:
            _item = item_metadata[item]
            prop_hidden = meta_options.get(item, {}).get('option', {}).get('hidden', False)
            if isinstance(_item, dict) and \
                    _item.get('attribute_value_mlt'):
                for _idx, _value in enumerate(_item['attribute_value_mlt']):
                    if _value is not None:
                        for key in subitem_keys:
                            for h in hide_list:
                                if h.startswith(item) and h.endswith(key):
                                    prop_hidden = True
                            if key in _value.keys() and (force_flag or not show_email_flag or prop_hidden):
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


def item_setting_show_email():
    # Display email from setting item admin.
    settings = AdminSettings.get('items_display_settings',dict_to_object=False)
    if settings and 'items_display_email' in settings:
        is_display = settings['items_display_email']
    else:
        is_display = False
    return is_display

def is_show_email_of_creator(item_type_id, item_type=None):
    """Check setting show/hide email for 'Detail' and 'PDF Cover Page' screen.

    :param item_type_id: item type id of current record.
    :param item_type: item type data
    :return: True/False, True: show, False: hide.
    """
    def get_creator_id(item_type_id, item_type):
        item_map = get_mapping(item_type_id, "jpcoar_mapping", item_type=item_type)
        creator = 'creator.creatorName.@value'
        creator_id = None
        if creator in item_map:
            creator_id = item_map[creator].split('.')[0]
        return creator_id

    def item_type_show_email(item_type_id, item_type):
        # Get flag of creator's email hide from item type.
        if not item_type:
            item_type = ItemTypes.get_by_id(item_type_id)
        creator_id = get_creator_id(item_type_id, item_type)
        if not creator_id:
            return None
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

    is_hide = item_type_show_email(item_type_id, item_type)
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

def get_data_by_key_array_json(key, array_json, get_key):
    for item in array_json:
        if str(item.get('id')) == str(key):
            return item.get(get_key)

def get_file_info_list(record, item_type=None):
    """File Information of all file in record.

    :param record: all metadata of a record.
    :param item_type: item type data
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
            p_file['future_date_message'] = _("Restricted Access")
        elif access == "open_date":
            if date and isinstance(date, list) and date[0]:
                adtv = date[0].get('dateValue')
                if adtv is None:
                    adt = datetime.date.max
                else:
                    adt = dt.strptime(adtv, "%Y-%m-%d")
                if is_future(adt):
                    message = "Download is available from {}/{}/{}."
                    p_file['future_date_message'] = _(message).format(
                        adt.year, adt.month, adt.day)
                    message = "Download / Preview is available from {}/{}/{}."
                    p_file['download_preview_message'] = _(message).format(
                        adt.year, adt.month, adt.day)

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
                if check_file_download_permission(record, f, True, item_type=item_type)\
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
                    # add role
                    role_list = f.get("roles")
                    if role_list:
                        for r in role_list:
                            role = r.get('role')
                            if role:
                                r['role_id'] = role
                                r['role'] = get_data_by_key_array_json(role, roles, 'name')

                    f['file_order'] = file_order
                    files.append(f)
                file_order += 1
    return is_display_file_preview, files


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


def check_and_send_usage_report(extra_info:dict, user_mail:str ,record:dict, file_object:dict):
    """Check and send usage report for user.
    Args
        extra_info:dict
        user_mail:str
        record:dict
        file_object:dict
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

    activity_id = activity.activity_id
    user =  User.query.filter_by(email=user_mail).one_or_none()
    permission = check_create_usage_report(record, file_object , user.id if user else None)
    if permission is not None and activity_id is not None:
        FilePermission.update_usage_report_activity_id(permission,activity_id)


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
                         user_mail: str) -> Optional[FileOnetimeDownload]:
    """Get onetime download count.

    Args:
        str:file_name:
        str:record_id:
        str:user_mail:
    Returns: 
        FileOnetimeDownload or None
    """
    file_downloads = FileOnetimeDownload.find(
        file_name=file_name, record_id=record_id, user_mail=user_mail
    )
    if file_downloads and len(file_downloads) > 0:
        return file_downloads[0]
    else:
        return None
    
def get_valid_onetime_download(file_name: str, record_id: str,user_mail: str) -> Optional[FileOnetimeDownload]:
    """Get file_onetime_download 
        if expiration_date and download_count is set downloadable

    Args:
        str:file_name:
        str:record_id:
        str:user_mail:
    Returns: 
        FileOnetimeDownload or None
    """
                
    file_downloads:List[FileOnetimeDownload] = FileOnetimeDownload \
    .find_downloadable_only(
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
    if content_file_download and isinstance(content_file_download, dict):
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


def update_onetime_download(**kwargs) -> Optional[List[FileOnetimeDownload]]:
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
    if terms_list and isinstance(terms_list, list):
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

    current_app.logger.debug("res_data: {}".format(json.dumps(res_data, ensure_ascii=False)))

    return json.dumps(res_data, ensure_ascii=False)

def create_secret_url(record_id:str ,file_name:str ,user_mail:str ,restricted_fullname='',restricted_data_name='') -> dict:
    """
    Save in FileSecretDownload
    and Generate Secret Download URL.
    
    Args:
        str :record_id:
        str :file_name:
        str :user_mail
        str :restricted_fullname  :embed mail string
        str :restricted_data_name :embed mail string
    Return: 
        dict: created info 
    """
    # Save to Database.
    secret_obj:FileSecretDownload = _create_secret_download_url(
        file_name, record_id, user_mail)
    
    # generate url
    secret_file_url = _generate_secret_download_url(
        file_name, record_id, secret_obj.id, secret_obj.created)

    return_dict: dict = {
        "secret_url": secret_file_url,
        "mail_recipient": secret_obj.user_mail,
        "file_name": file_name,
        "restricted_expiration_date": "",
        "restricted_expiration_date_ja": "",
        "restricted_expiration_date_en": "",
        "restricted_download_count": "",
        "restricted_download_count_ja": "",
        "restricted_download_count_en": "",
        "restricted_fullname": restricted_fullname,
        "restricted_data_name": restricted_data_name,
    }

    max_int :int = current_app.config["WEKO_ADMIN_RESTRICTED_ACCESS_MAX_INTEGER"]
    if secret_obj.expiration_date < max_int:
        expiration_date = timedelta(days=secret_obj.expiration_date)
        expiration_date = dt.today() + expiration_date
        expiration_date = expiration_date.strftime("%Y-%m-%d")
        return_dict['restricted_expiration_date'] = expiration_date
    else:
        return_dict["restricted_expiration_date_ja"] = "無制限"
        return_dict["restricted_expiration_date_en"] = "Unlimited"
            

    if secret_obj.download_count < max_int :
        return_dict["restricted_download_count"] = str(secret_obj.download_count)
    else:
        return_dict["restricted_download_count_ja"] = "無制限"
        return_dict["restricted_download_count_en"] = "Unlimited"
            
    return return_dict


def _generate_secret_download_url(file_name: str, record_id: str, id: str ,created :dt) -> str:
    """Generate Secret download URL.
    
    Args
        str: file_name: File name
        str: record_id: File Version ID
        str: id: FileSecretDownload id
        datetime :created :FileSecretDownload created
    
    Returns
        str: generated url
    """    
    secret_key = current_app.config['WEKO_RECORDS_UI_SECRET_KEY']
    download_pattern = current_app.config[
        'WEKO_RECORDS_UI_SECRET_DOWNLOAD_PATTERN']
    current_date = created
    hash_value = download_pattern.format(file_name, record_id, id,
                                         current_date.isoformat())
    secret_token = oracle10.hash(secret_key, hash_value)

    token_pattern = "{} {} {} {}"
    token = token_pattern.format(record_id, id, current_date.isoformat(),
                                 secret_token)
    token_value = base64.b64encode(token.encode()).decode()
    host_name = request.host_url
    url = "{}record/{}/file/secret/{}?token={}" \
        .format(host_name, record_id, file_name, token_value)
    current_app.logger.debug("secret_file_url:{}".format(url))
    return url


def parse_secret_download_token(token: str) -> Tuple[str, Tuple]:
    """Parse secret download token.

    Args
        token:
    Returns: 
        str   : error message
        Tuple : (record_id, id, date, secret_token)
    """
    # current_app.logger.debug("token:{}".format(token))
    error = _("Token is invalid.")
    if token is None:
        return error, ()
    try:
        decode_token = base64.b64decode(token.encode()).decode()
        current_app.logger.debug("decode_token:{}".format(decode_token))
        param = decode_token.split(" ")
        if not param or len(param) != 5:
            return error, ()
        return "", (param[0], param[1], param[2] + " " + param[3] , param[4]) #record_id, id, current_date(date + time), secret_token
    except Exception as err:
        current_app.logger.error(err)
        return error, ()


def validate_secret_download_token(
    secret_download: FileSecretDownload , file_name: str, record_id: str,
    id: str, date: str, token: str
) -> Tuple[bool, str]:
    """Validate secret download token.

    Args
        FileSecretDownload:secret_download:
        str:file_name:
        str:record_id:
        str:id:
        str:date:
        str:token:
    Returns 
        Tuple:
            bool : is valid 
            str  : error message
    """
    token_invalid = _("Token is invalid.")
    secret_key = current_app.config['WEKO_RECORDS_UI_SECRET_KEY']
    download_pattern = current_app.config[
        'WEKO_RECORDS_UI_SECRET_DOWNLOAD_PATTERN']
    hash_value = download_pattern.format(
        file_name, record_id, id, date)
    
    if not oracle10.verify(secret_key, token, hash_value):
        current_app.logger.error('Validate token error: {}'.format(hash_value))
        return False, token_invalid
    try:
        if not secret_download:
            return False, token_invalid
        try:
            expiration_date = timedelta(secret_download.expiration_date)
            download_date = secret_download.created.date() + expiration_date
            current_date = dt.utcnow().date()
            if current_date > download_date:
                return False, _(
                    "The expiration date for download has been exceeded.")
        except OverflowError:
            # in case of "Unlimited"
            current_app.logger.debug('date value out of range:'+
                                    str(secret_download.expiration_date))

        if secret_download.download_count <= 0:
            return False, _("The download limit has been exceeded.")
        return True, ""
    except Exception as err:
        current_app.logger.error('Validate secret download token error:')
        current_app.logger.error(err)
        return False, token_invalid
        
def get_secret_download(file_name: str, record_id: str,
                        id: str , created :dt ) -> Optional[FileSecretDownload]:
    """Get secret download count.

    Args :
        str:file_name
        str:record_id
        str:id
        dt :created
    @return:
        FileSecretDownload or None
    """
    file_downloads = FileSecretDownload.find(
        file_name=file_name, record_id=record_id, id=id ,created=created
    )
    if file_downloads and len(file_downloads) == 1:
        return file_downloads[0]
    else:
        return None

def _create_secret_download_url(file_name: str, record_id: str, user_mail: str) -> FileSecretDownload:
    """Create secret download.

    Args:
        str : file_name:
        str : record_id:
        str : user_mail:
    Returns:
        FileSecretDownload : inserted record
    """
    secret_url_file_download:dict = get_restricted_access('secret_URL_file_download')
        
    expiration_date = secret_url_file_download.get("secret_expiration_date", 30)
    download_limit = secret_url_file_download.get("secret_download_limit", 10)

    file_secret = FileSecretDownload.create(**{
        "file_name": file_name,
        "record_id": record_id,
        "user_mail": user_mail,
        "expiration_date": expiration_date,
        "download_count": download_limit,
    })
    return file_secret
    


def update_secret_download(**kwargs) -> Optional[List[FileSecretDownload]]:
    """Update secret download.

    Args
        kwargs:
    Returns
        updated List[FileSecretDownload] or None
    """
    current_app.logger.debug("update_secret_download:{}".format(kwargs))
    return FileSecretDownload.update_download(**kwargs)


def create_limmiter():
    from .config import WEKO_RECORDS_UI_API_LIMIT_RATE_DEFAULT
    return Limiter(app=Flask(__name__), key_func=get_remote_address, default_limits=WEKO_RECORDS_UI_API_LIMIT_RATE_DEFAULT)

def export_preprocess(pid, record, schema_type):
    """Preprocess for export.

    Args:
        PersistentIdentifier : pid:
        WekoRecord : record:
        str : schema_type:
    Returns:
        str : data for export
    """
    formats = current_app.config.get('RECORDS_UI_EXPORT_FORMATS', {}).get(pid.pid_type, {})
    fmt = formats.get(schema_type)

    if fmt is False:
        # If value is set to False, it means it was deprecated.
        abort(410)
    elif fmt is None:
        abort(404)
    else:
        custom_record_medata_for_export(record)

        if 'json' not in schema_type and 'bibtex' not in schema_type:
            record.update({'@export_schema_type': schema_type})

        serializer = obj_or_import_string(fmt['serializer'])
        data = serializer.serialize(pid, record)

        if isinstance(data, six.binary_type):
            data = data.decode('utf8')

        return data
