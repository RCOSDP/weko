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

from invenio_db import db
from weko_records.api import ItemsMetadata
from weko_workflow.models import ActionStatusPolicy, Activity

from .permissions import check_user_group_permission


def get_item_pidstore_identifier(object_uuid):
    """
    Get identifier value from ItemsMetadata.

    :param: index_name_english
    :return: dict of item type info
    """
    with db.session.no_autoflush:
        action_status = Activity.query.filter_by(
            item_id=object_uuid).one_or_none()
        meta = ItemsMetadata.get_record(object_uuid)
        if meta and action_status:
            pidstore_identifier = meta.get('pidstore_identifier')
            if pidstore_identifier is not None \
                and action_status.action_status == \
                    ActionStatusPolicy.ACTION_DONE:
                identifier = pidstore_identifier.get('identifier')
                if identifier:
                    return identifier.get('value')

    return None


def get_groups_price(record: dict) -> list:
    """Get the prices of Billing files set in each group.

    :param record: Record metadata.
    :return: The prices of Billing files set in each group.
    """
    groups_price = list()
    for key, value in record.items():
        if type(value) is dict:
            attr_value = value.get('attribute_value_mlt')
            if attr_value and type(attr_value) is list:
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
        if file_name and type(group_price_list) is list:
            is_ok = False
            for group_price in group_price_list:
                if type(group_price) is dict:
                    group_id = group_price.get('group')
                    is_ok = check_user_group_permission(group_id)
                    if is_ok:
                        break
            billing_file_permission[file_name] = is_ok

    return billing_file_permission
