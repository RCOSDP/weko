# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2023-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Domain blocking listener."""

from .models import DomainStatus


def on_user_confirmed(app, user):
    """Listener for when a user is confirmed."""
    security = app.extensions["security"]
    datastore = security.datastore

    # Domain is inserted on domain list when a user confirms their email.
    domain = datastore.find_domain(user.domain)
    if domain is None:
        domain = datastore.create_domain(user.domain)
        datastore.mark_changed(id(datastore.db.session), model=domain)

    # Verify user if domain is verified.
    if domain.status == DomainStatus.verified:
        user.verified_at = security.datetime_factory()
    # Happens if e.g. user register an account, domain is later blocked,
    # and user requests to resend email confirmation or link is still valid.
    elif domain.status == DomainStatus.blocked:
        user.blocked_at = security.datetime_factory()
        user.active = False
        user.verified_at = None

    # Needed otherwise users are not indexed when they confirm their email
    # address
    datastore.mark_changed(id(datastore.db.session), model=user)
