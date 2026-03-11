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

author_search_scope = Scope(
    id_='author:search',
    group='author',
    help_text=_('Allow search authors.'),
)

author_create_scope = Scope(
    id_='author:create',
    group='author',
    help_text=_('Allow create authors.'),
)

author_update_scope = Scope(
    id_='author:update',
    group='author',
    help_text=_('Allow update authors.'),
)

author_delete_scope = Scope(
    id_='author:delete',
    group='author',
    help_text=_('Allow delete authors.'),
)
