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

"""OAuth2 scopes."""

from __future__ import absolute_import, print_function

from flask_babelex import lazy_gettext as _
from invenio_oauth2server.models import Scope


class IndexScope(Scope):
    """Basic index scope."""

    def __init__(self, id_, *args, **kwargs):
        """Define the scope."""
        super(IndexScope, self).__init__(
            id_='index:{0}'.format(id_),
            group='index', *args, **kwargs
        )


create_index_scope = IndexScope('create', help_text=_('Allow create index.'))
"""Allow create."""

read_index_scope = IndexScope('read', help_text=_('Allow read index.'))
"""Allow read."""

update_index_scope = IndexScope('update', help_text=_('Allow update index.'))
"""Allow update index."""

delete_index_scope = IndexScope('delete', help_text=_('Allow delete index.'))
"""Allow delete."""
