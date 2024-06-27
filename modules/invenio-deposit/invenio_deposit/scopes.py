# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAuth2 scopes."""

from __future__ import absolute_import, print_function

from flask_babelex import lazy_gettext as _
from invenio_oauth2server.models import Scope


class DepositScope(Scope):
    """Basic deposit scope."""

    def __init__(self, id_, *args, **kwargs):
        """Define the scope."""
        super(DepositScope, self).__init__(
            id_='deposit:{0}'.format(id_),
            group='deposit', *args, **kwargs
        )

write_scope = DepositScope('write',
                           help_text=_('Allow upload (but not publishing).'))
"""Allow upload (but not publishing)."""

actions_scope = DepositScope('actions',
                             help_text=_('Allow publishing of uploads.'))
"""Allow publishing of uploads."""
