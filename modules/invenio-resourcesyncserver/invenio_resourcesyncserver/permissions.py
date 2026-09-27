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

"""Permissions for ResourceSync Server."""

from functools import wraps

from flask import abort, current_app


def is_public_record(record_id):
    """Check that the record is available to the public.

    The record must be published, its publication date must have come and
    it must belong to a public index. For a versioned identifier
    ("<recid>.<version>") the parent record must satisfy the same
    conditions.

    :param record_id: Identifier of the record.
    :return: True if the record can be distributed.
    """
    from invenio_oaiserver.response import is_private_index
    from weko_deposit.api import WekoRecord
    from weko_records_ui.permissions import check_publish_status

    record_ids = [str(record_id)]
    if '.' in record_ids[0]:
        record_ids.append(record_ids[0].split('.')[0])

    for _id in record_ids:
        try:
            record = WekoRecord.get_record_by_pid(_id)
        except Exception as ex:
            current_app.logger.debug(ex)
            return False
        if not record or not check_publish_status(record) \
                or is_private_index(record):
            return False
    return True


def public_record_required(param='record_id'):
    """Abort with 404 unless the record in the URL is public.

    :param param: name of the view argument holding the record identifier.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            record_id = kwargs.get(param)
            if record_id is None or not is_public_record(record_id):
                abort(404)
            return f(*args, **kwargs)
        return decorated
    return decorator
