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
from .api import ResyncHandler
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

    @expose('/get_list', methods=['GET'])
    def get_list(self):
        """Renders an admin resource list view.

        :param
        :return: The rendered template.
        """
        result = ResyncHandler.get_list_resync()
        result = list(map(lambda item: item.to_dict(), result))
        return jsonify(data=result)

    @expose('/create', methods=['POST'])
    def create_resync(self):
        """Renders an admin resource list view.

        :param
        :return: The rendered template.
        """
        resync = ResyncHandler(**request.get_json())
        result = resync.create()
        if result.get('success'):
            return jsonify(
                success=result.get('success'),
                data=result.get("data")
            )
        else:
            return jsonify(
                success=result.get('success'),
                errmsg=result.get("errmsg")
            )

    @expose('/update/<resync_id>', methods=['POST'])
    def update_resync(self, resync_id):
        """Renders an admin resource list view.

        :param
        :return: The rendered template.
        """
        resync = ResyncHandler.get_resync(resync_id)
        if resync:
            result = resync.update(request.get_json())
            if result.get('success'):
                return jsonify(
                    success=result.get('success'),
                    data=result.get("data")
                )
            else:
                return jsonify(
                    success=result.get('success'),
                    errmsg=result.get("errmsg")
                )
        else:
            return jsonify(
                success=False,
                errmsg=["Resync is not exist"]
            )

    @expose('/delete/<resync_id>', methods=['POST'])
    def delete_resync(self, resync_id):
        """Renders an admin resource list view.

        :param
        :return: The rendered template.
        """
        resync = ResyncHandler.get_resync(resync_id)
        if not resync:
            return jsonify(
                success=False,
                errmsg=["Resync is not exist"]
            )
        result = resync.update(request.get_json())
        if result.get('success'):
            return jsonify(
                success=result.get('success'),
                data=result.get("data")
            )
        else:
            return jsonify(
                success=result.get('success'),
                errmsg=result.get("errmsg")
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
