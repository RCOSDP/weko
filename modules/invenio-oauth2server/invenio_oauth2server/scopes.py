# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAuth2 scopes."""

from __future__ import absolute_import, print_function

from flask_babelex import lazy_gettext as _

from invenio_oauth2server.models import Scope

email_scope = Scope(
    id_='user:email',
    group='user',
    help_text=_('Allow access to email address (read-only).'),
)
"""Scope to protect the user's email address."""
