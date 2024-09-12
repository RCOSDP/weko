# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

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
