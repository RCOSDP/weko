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
        if meta is not None:
            pidstore_identifier = meta.get('pidstore_identifier')
            if pidstore_identifier is not None \
                and action_status.action_status == \
                    ActionStatusPolicy.ACTION_DONE:
                identifier = pidstore_identifier.get('identifier')
                if identifier:
                    return identifier.get('value')

    return None
