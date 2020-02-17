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
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from weko_admin.models import AdminSettings
from weko_deposit.api import WekoDeposit
from weko_records.api import ItemsMetadata, ItemTypes

from .permissions import check_user_group_permission


def check_items_settings():
    """Check items setting."""
    settings = AdminSettings.get('items_display_settings')
    current_app.config['EMAIL_DISPLAY_FLG'] = settings.items_display_email
    current_app.config['ITEM_SEARCH_FLG'] = settings.items_search_author


def get_record_permalink(record):
    """
    Get identifier of record.

    :param record: index_name_english
    :return: dict of item type info
    """
    pid_doi = record.pid_doi
    pid_cnri = record.pid_cnri

    if pid_doi and pid_cnri:
        if pid_doi.updated > pid_cnri.updated:
            return record.pid_doi.pid_value
        else:
            return record.pid_cnri.pid_value
    elif record.pid_doi:
        return record.pid_doi.pid_value
    elif record.pid_cnri:
        return record.pid_cnri.pid_value
    else:
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
        depid = PersistentIdentifier.query.filter_by(
            pid_type='depid', object_uuid=pid.object_uuid).first()
        if depid:
            rec = RecordMetadata.query.filter_by(id=pid.object_uuid).first()
            dep = WekoDeposit(rec.json, rec)
            dep['path'] = []
            dep.indexer.update_path(dep, update_revision=False)
        pids = PersistentIdentifier.query.filter_by(
            object_uuid=pid.object_uuid)
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
        pid.status = PIDStatus.REGISTERED
        depid = PersistentIdentifier.query.filter_by(
            pid_type='depid', object_uuid=pid.object_uuid).first()
        if depid:
            depid.status = PIDStatus.REGISTERED
            rec = RecordMetadata.query.filter_by(id=pid.object_uuid).first()
            dep = WekoDeposit(rec.json, rec)
            dep.indexer.update_path(dep, update_revision=False)
        pids = PersistentIdentifier.query.filter_by(
            object_uuid=pid.object_uuid)
        for p in pids:
            p.status = PIDStatus.REGISTERED
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        raise ex


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
