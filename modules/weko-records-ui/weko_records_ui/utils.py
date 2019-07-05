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

from flask import current_app
from invenio_db import db
from weko_admin.settings import AdminSettings
from weko_records.api import ItemsMetadata, ItemTypes
from weko_workflow.models import ActionStatusPolicy, Activity


def check_items_settings():
    """Check items setting."""
    settings = AdminSettings()
    current_app.config['EMAIL_DISPLAY_FLG'] = settings.items_display_email
    current_app.config['ITEM_SEARCH_FLG'] = settings.items_search_author


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


def is_billing_item(item_type_id):
    """Checks if item is a billing item based on its meta data schema."""
    item_type = ItemTypes.get_by_id(id_=item_type_id)
    if item_type:
        properties = item_type.schema['properties']
        for meta_key in properties:
            if properties[meta_key]['type'] == 'object' and \
               'groupsprice' in properties[meta_key]['properties']:
                return True
            elif properties[meta_key]['type'] == 'array' and \
                    'groupsprice' in properties[meta_key]['items']['properties']:
                return True
        return False
