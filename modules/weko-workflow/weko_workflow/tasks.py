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

"""Task for workflow module."""

from celery import shared_task
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_indexer.api import RecordIndexer
from invenio_records.models import RecordMetadata

from .utils import cancel_expired_usage_reports


@shared_task(ignore_results=True)
def cancel_expired_usage_report_activities():
    """Cancel usage report activities are expired."""
    with current_app.app_context():
        cancel_expired_usage_reports()


@shared_task(ignore_results=True)
def update_set_info(pid):
    """Update the set information to ES."""
    try:
        record = RecordMetadata.query.get(pid.object_uuid)
        like_value = 'oai:invenio:{}%'.format(record.json['control_number'].zfill(8))
        query = (x[0] for x in PersistentIdentifier.query.filter_by(
            object_type='rec', status=PIDStatus.REGISTERED
        ).filter(
            PersistentIdentifier.pid_type.in_(['oai'])
        ).filter(
            PersistentIdentifier.pid_value.like(like_value)
        ).values(
            PersistentIdentifier.object_uuid
        ))
        RecordIndexer().bulk_index(query)
        RecordIndexer().process_bulk_queue(
            es_bulk_kwargs={'raise_on_error': True})
    except Exception as ex:
        current_app.logger.error('Failed to update the setting information to ES.')
        current_app.logger.exception(str(ex))
