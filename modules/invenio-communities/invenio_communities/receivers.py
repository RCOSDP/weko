# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Community module receivers."""

from __future__ import absolute_import, print_function

from flask import current_app
from invenio_db import db

from .models import InclusionRequest
from .utils import send_community_request_email


def new_request(sender, request=None, notify=True, **kwargs):
    """New request for inclusion."""
    if current_app.config['COMMUNITIES_MAIL_ENABLED'] and notify:
        send_community_request_email(request)


def inject_provisional_community(sender, json=None, record=None, index=None,
                                 **kwargs):
    """Inject 'provisional_communities' key to ES index."""
    if index and not index.startswith(
            current_app.config['COMMUNITIES_INDEX_PREFIX']):
        return

    json['provisional_communities'] = list(sorted([
        r.id_community for r in InclusionRequest.get_by_record(record.id)
    ]))


def create_oaipmh_set(mapper, connection, community):
    """Signal for creating OAI-PMH sets during community creation."""
    from invenio_oaiserver.models import OAISet
    with db.session.begin_nested():
        obj = OAISet(spec=community.oaiset_spec,
                     name=community.title,
                     description=community.description)
        db.session.add(obj)


def destroy_oaipmh_set(mapper, connection, community):
    """Signal for creating OAI-PMH sets during community creation."""
    from invenio_oaiserver.models import OAISet
    with db.session.begin_nested():
        oaiset = OAISet.query.filter_by(
            spec=community.oaiset_spec).one_or_none()
        if oaiset is None:
            raise Exception(
                "OAISet for community {0} is missing".format(community.id))
        db.session.delete(oaiset)
