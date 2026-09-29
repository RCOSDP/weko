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

"""Permissions for invenio-stats."""

import uuid
from functools import wraps

from flask import abort
from invenio_access import Permission, action_factory
from sqlalchemy.orm.exc import NoResultFound

stats_api_access = action_factory('stats-api-access')
stats_api_permission = Permission(stats_api_access)


def _can_view_record(record):
    """Check the record detail page permission of the current user."""
    from weko_records_ui.permissions import page_permission_factory

    return page_permission_factory(record).can()


def record_view_permission_required(f):
    """Require the permission to view the record given by ``record_id``.

    Uses the same permission as the record detail page.
    Aborts with 400 for a malformed id, 404 for an unknown record and
    403 when the current user cannot view the record.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from weko_deposit.api import WekoRecord

        try:
            record_uuid = uuid.UUID(str(kwargs.get('record_id')))
        except ValueError:
            abort(400)
        try:
            record = WekoRecord.get_record(record_uuid)
        except NoResultFound:
            abort(404)
        if not _can_view_record(record):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def bucket_view_permission_required(f):
    """Require the permission to view a record owning ``bucket_id``.

    Uses the same permission as the record detail page.
    Aborts with 400 for a malformed id, 404 when no record owns the
    bucket and 403 when the current user cannot view the record.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from invenio_records_files.models import RecordsBuckets
        from weko_deposit.api import WekoRecord

        try:
            bucket_uuid = uuid.UUID(str(kwargs.get('bucket_id')))
        except ValueError:
            abort(400)
        found = False
        for rb in RecordsBuckets.query.filter_by(bucket_id=bucket_uuid).all():
            try:
                record = WekoRecord.get_record(rb.record_id)
            except NoResultFound:
                continue
            found = True
            if _can_view_record(record):
                return f(*args, **kwargs)
        abort(403 if found else 404)
    return decorated
