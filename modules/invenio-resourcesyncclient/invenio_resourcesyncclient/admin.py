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

"""WEKO3 module docstring."""
import json
from flask import Response, abort, current_app, jsonify, make_response, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from .config import INVENIO_RESYNC_INDEXES_STATUS, INVENIO_RESYNC_INDEXES_MODE,\
    INVENIO_RESYNC_INDEXES_SAVING_FORMAT

class AdminResyncClient(BaseView):
    """BaseView for Admin Resource List."""

    @expose('/', methods=['GET'])
    def index(self):
        """Renders an admin resource list view.

        :param
        :return: The rendered template.
        """
        return self.render(
            current_app.config['INVENIO_RESOURCESYNCCLIENT_ADMIN_TEMPLATE'],
            status=json.dumps(current_app.config.get(
                'INVENIO_RESYNC_INDEXES_STATUS',
                INVENIO_RESYNC_INDEXES_STATUS
            )),
            resync_mode=json.dumps(current_app.config.get(
                'INVENIO_RESYNC_INDEXES_MODE',
                INVENIO_RESYNC_INDEXES_MODE
            )),
            saving_format=json.dumps(current_app.config.get(
                'INVENIO_RESYNC_INDEXES_SAVING_FORMAT',
                INVENIO_RESYNC_INDEXES_SAVING_FORMAT
            )),

        )


invenio_admin_resync_client = {
    'view_class': AdminResyncClient,
    'kwargs': {
        'category': _('Resource Sync'),
        'name': _('Resync'),
        'endpoint': 'resync'
    }
}


__all__ = (
    'invenio_admin_resync_client',
)
