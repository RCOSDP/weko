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

from datetime import datetime

from dateutil.tz import tzoffset
from flask import current_app, request
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from resync import CapabilityList, Resource
from resync.list_base_with_index import ListBaseWithIndex

from .api import ChangeListHandler, ResourceListHandler
from .config import INVENIO_SOURCE_DESC_URL
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
    cap.up = INVENIO_SOURCE_DESC_URL.format(request.url_root)

    list_resource = ResourceListHandler.get_capability_content()
    list_change = ChangeListHandler.get_capability_content()
    total_list = [*list_resource, *list_change]
    for item in total_list:
        cap.add(item)

    return cap.as_xml()


def render_well_know_resourcesync():
    """Generate source description xml."""
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


def query_record_changes(repository_id,
                         date_from,
                         date_until,
                         max_changes_size=None,
                         change_tracking_state=None):
    """
    Delete unregister bucket by pid.

    Find all bucket have same object version but link with unregister records.
    Arguments:
        record_uuid     -- record uuid link to checking bucket.
    Returns:
        None.

    """
    record_changes = []
    hits = get_item_changes_by_index(repository_id,
                                     date_from,
                                     date_until)
    states = change_tracking_state.split('&')

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
            result['record_version'] = 0

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
            elif recids[1] == '0':
                continue
            else:
                result['status'] = 'updated'

        record_changes.append(result)

    ret = []
    for record in record_changes:
        if record.get('status') in states:
            ret.append(record)
    if ret:
        return ret[max_changes_size * -1:]
    return ret


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


def parse_date(date):
    """Parse a string to datetime format."""
    # try format without timezone:
    formats = ["%Y-%m-%d", "%Y%m%d"]
    for date_format in formats:
        try:
            # use UTC timezone if no offset
            return datetime.strptime(date, date_format).replace(
                tzinfo=tzoffset(None, 0))
        except ValueError as e:
            current_app.logger.error(str(e))
            pass
    (date, offset) = get_timezone(date)
    iso_formats = "%Y-%m-%dT%H:%M:%S.%f"
    try:
        return datetime.strptime(date, iso_formats).replace(
            tzinfo=tzoffset(None, offset))
    except ValueError as e:
        current_app.logger.error(str(e))
        pass


def get_timezone(date):
    """Get timezone of a date, then return date & timezone."""
    parts = date.rsplit('+', 1)
    offset = 0
    if len(parts) > 1:
        date = parts[0]
        tz = parts[1]
        tz_parts = tz.split(':')
        tz_hour = tz_parts[0]
        tz_min = tz_parts[1]
        offset = int(tz_hour) * 60 * 60 + int(tz_min) * 60
        return date, offset
    else:
        parts = date.rsplit('-', 1)
        if len(parts) > 1:
            date = parts[0]
            tz = parts[1]
            tz_parts = tz.split(':')
            if len(tz_parts > 1):
                tz_hour = tz_parts[0]
                tz_min = tz_parts[1]
                offset = -(int(tz_hour) * 60 * 60 + int(tz_min) * 60)
                return date, offset
    return date, offset


def get_pid(pid):
    """Get record by pid."""
    try:
        pid = PersistentIdentifier.get('depid', pid)
        if pid:
            return pid
        else:
            return None
    except Exception as ex:
        current_app.logger.debug(ex)
        return None
