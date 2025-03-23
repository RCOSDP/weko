# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""OpenAIRE service integration for Invenio repositories."""

from __future__ import absolute_import, print_function

from datetime import datetime

from celery import shared_task
from flask import current_app
from invenio_db import db

from .models import Community, InclusionRequest
from weko_handle.api import Handle


# @shared_task(ignore_result=True)
# def delete_marked_communities():
#     """Delete communities after holdout time."""
#     # TODO: Delete the community ID from all records metadata first
#     raise NotImplementedError()
#     Community.query.filter_by(
#         Community.delete_time > datetime.utcnow()).delete()
#     db.session.commit()


@shared_task(ignore_result=True)
def delete_expired_requests():
    """Delete expired inclusion requests."""
    try:
        InclusionRequest.query.filter(
            InclusionRequest.expires_at > datetime.utcnow()).delete()
        db.session.commit()
    except Exception as ex:
        db.session.rollback()

@shared_task(ignore_result=True)
def delete_handle(hdl):
        weko_handle = Handle()
        handle = weko_handle.delete_handle(hdl)
        if handle:
            current_app.logger.info(hdl + ' handle deleted successfully.')
        else:
            current_app.logger.info( hdl + " handle delete failed.")
