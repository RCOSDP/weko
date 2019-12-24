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

"""Invenio module that adds support for communities."""

from __future__ import absolute_import, print_function

from invenio_indexer.signals import before_record_index
from sqlalchemy.event import listen
from werkzeug.utils import cached_property

from . import config
from .cli import communities as cmd
from .models import Community
from .permissions import permission_factory
from .receivers import create_oaipmh_set, destroy_oaipmh_set, \
    inject_provisional_community, new_request
from .signals import inclusion_request_created


class InvenioCommunities(object):
    """Invenio-Communities extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.cli.add_command(cmd)
        app.extensions['invenio-communities'] = self
        # Register the jinja do extension
        app.jinja_env.add_extension('jinja2.ext.do')
        self.register_signals(app)

    def register_signals(self, app):
        """Register the signals."""
        before_record_index.connect(inject_provisional_community)
        if app.config['COMMUNITIES_OAI_ENABLED']:
            listen(Community, 'after_insert', create_oaipmh_set)
            listen(Community, 'after_delete', destroy_oaipmh_set)
        inclusion_request_created.connect(new_request)

    def init_config(self, app):
        """Initialize configuration."""
        app.config.setdefault(
            "COMMUNITIES_BASE_TEMPLATE",
            app.config.get("BASE_TEMPLATE",
                           "invenio_communities/base.html"))

        # Set default configuration
        for k in dir(config):
            if k.startswith("COMMUNITIES_"):
                app.config.setdefault(k, getattr(config, k))

    @cached_property
    def permission_factory(self):
        """Load default permission factory."""
        return permission_factory
