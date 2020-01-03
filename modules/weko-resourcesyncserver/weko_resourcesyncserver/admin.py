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

from flask_admin import BaseView, expose
from flask import Response, abort, current_app, jsonify, make_response, request
from flask_babelex import gettext as _
from .api import ResourceSync
from .utils import to_dict


class AdminResourceSyncView(BaseView):
    """BaseView for Admin Import."""

    @expose('/', methods=['GET'])
    def index(self):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """

        return self.render(
            current_app.config['WEKO_RESOURCESYNCSERVER_ADMIN_TEMPLATE'],
        )

    @expose('/get_list', methods=['GET'])
    def get_list(self):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        list_resource = ResourceSync.get_list_resource()
        result = list(map(lambda item: to_dict(item), list_resource))
        return jsonify(result)

    @expose('/get_resource/<id>', methods=['GET'])
    def get_resource(self, id):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        resource = ResourceSync.get_resource(id)
        return jsonify(resource)

    @expose('/create', methods=['POST'])
    def create(self):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        data = request.get_json()
        resource = ResourceSync.create(data)
        if resource:
            return jsonify(data=to_dict(resource), success=True)
        else:
            return jsonify(data=None, success=False)

    @expose('/update/<id>', methods=['POST'])
    def update(self, id):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        data = request.get_json()
        resource = ResourceSync.update(id, data)
        if resource:
            return jsonify(data=to_dict(resource), success=True)
        else:
            return jsonify(data=None, success=False)

    @expose('/delete/<id>', methods=['POST'])
    def delete(self, id):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        resource = ResourceSync.delete(id)
        if resource:
            return jsonify(data=to_dict(resource), success=True)
        else:
            return jsonify(data=None, success=False)


weko_admin_resource = {
    'view_class': AdminResourceSyncView,
    'kwargs': {
        'category': _('Resource Sync'),
        'name': _('Resource Sync'),
        'endpoint': 'resource'
    }
}

__all__ = (
    'weko_admin_resource'
)
