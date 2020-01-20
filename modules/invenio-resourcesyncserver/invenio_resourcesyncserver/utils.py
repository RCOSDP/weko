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

"""Utilities for convert response json."""

from flask import abort, request, send_file
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from resync import CapabilityList, Resource
from resync.list_base_with_index import ListBaseWithIndex

from .api import ChangeListHandler, ResourceListHandler
from .query import get_item_changes_by_index


def get_real_path(path):
    """Generate list index id from path."""
    result = []
    for item in path:
        if '/' in item:
            fl = item.split("/")
            result.extend(fl)
        else:
            result.append(item)
    return list(set(result))


def render_capability_xml():
    """Generate capability xml."""
    cap = CapabilityList()
    list_resource = ResourceListHandler.get_capability_content()
    list_change = ChangeListHandler.get_capability_content()
    total_list = [*list_resource, *list_change]
    for item in total_list:
        cap.add(item)

    return cap.as_xml()


def render_well_know_resourcesync():
    """Generate capability xml."""
    cap = ListBaseWithIndex(
        capability_name='description',
        ln=[
            {
                'href': request.url_root,
                'rel': 'describedby'
            }
        ]
    )
    cap.add(Resource(
        '{}resync/capability.xml'.format(request.url_root),
        capability='capability')
    )

    return cap.as_xml()


def query_record_changes(repository_id, date_from, date_until):
    """
    Delete unregister bucket by pid.

    Find all bucket have same object version but link with unregister records.
    Arguments:
        record_uuid     -- record uuid link to checking bucket.
    Returns:
        None.

    """
    record_changes = []
    hits = get_item_changes_by_index(repository_id, date_from, date_until)
    for hit in hits:
        _source = hit.get("_source")
        result = {
            'record_id': 0,
            'record_version': 0,
            'status': '',
            'created': _source.get('_created', None),
            'updated': _source.get('_updated', None)
        }

        recids = str(_source.get('control_number')).split('.')
        if len(recids) == 1:
            recid = int(recids[0])
            result['record_id'] = recid
            result['record_version'] = '0'

            pid = PersistentIdentifier.get('recid', recid)
            is_belong = check_existing_record_in_list(recid, record_changes)
            if pid.status == PIDStatus.DELETED and is_belong:
                result['status'] = 'deleted'
            else:
                continue
        elif len(recids) > 1:
            result['record_id'] = int(recids[0])
            result['record_version'] = int(recids[1])
            if recids[1] == '1':
                result['status'] = 'created'
            else:
                result['status'] = 'updated'

        record_changes.append(result)

    return record_changes


def check_existing_record_in_list(record_id, results):
    """
    Delete unregister bucket by pid.

    Find all bucket have same object version but link with unregister records.
    Arguments:
        record_uuid     -- record uuid link to checking bucket.
    Returns:
        None.

    """
    for result in results:
        if result.get('record_id') == record_id:
            return True

    return False
