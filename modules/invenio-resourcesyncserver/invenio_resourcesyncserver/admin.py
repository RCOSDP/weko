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

from flask import Response, abort, current_app, jsonify, make_response, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _

from .config import INVENIO_RESOURCESYNC_CHANGE_LIST_ADMIN
from .api import ResourceListHandler, ChangeListHandler


class AdminResourceListView(BaseView):
    """BaseView for Admin Resource sync."""

    @expose('/', methods=['GET'])
    def index(self):
        """Renders an admin resource view.

        :param
        :return: The rendered template.
        """
        return self.render(
            current_app.config['INVENIO_RESOURCESYNCSERVER_ADMIN_TEMPLATE'],
        )

    @expose('/get_list', methods=['GET'])
    def get_list(self):
        """Renders an list resource sync.

        :param
        :return: The rendered template.
        """
        list_resource = ResourceListHandler.get_list_resource()
        result = list(map(lambda item: item.to_dict(), list_resource))
        return jsonify(result)

    # @expose('/get_resource/<resource_id>', methods=['GET'])
    # def get_resource(self, resource_id):
    #     """Renders an item import view.
    #
    #     :param
    #     :return: The rendered template.
    #     """
    #     resource = ResourceListHandler.ge
    #     return jsonify(resource)

    @expose('/create', methods=['POST'])
    def create(self):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        data = request.get_json()
        resource = ResourceListHandler.create(data)
        if resource:
            return jsonify(data=resource.to_dict(), success=True)
        else:
            return jsonify(data=None, success=False)

    @expose('/update/<resource_id>', methods=['POST'])
    def update(self, resource_id):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        data = request.get_json()
        resource = ResourceListHandler.get_resource(resource_id)

        if resource:
            result = resource.update(data)
            if result:
                return jsonify(data=result.to_dict(), success=True)
        return jsonify(data=None, success=False)

    @expose('/delete/<resource_id>', methods=['POST'])
    def delete(self, resource_id):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        resource = ResourceListHandler.get_resource(resource_id)
        if resource:
            result = resource.delete()
            if result:
                return jsonify(data=None, success=True)
        return jsonify(data=None, success=False)


class AdminChangeListView(BaseView):
    """BaseView for Admin Change list."""

    @expose('/', methods=['GET'])
    def index(self):
        """Renders an admin resource view.

        :param
        :return: The rendered template.
        """
        return self.render(
            current_app.config.get(
                'INVENIO_RESOURCESYNC_CHANGE_LIST_ADMIN',
                INVENIO_RESOURCESYNC_CHANGE_LIST_ADMIN
            )
        )

    @expose('/get_all', methods=['GET'])
    def get_list(self):
        """Renders an list resource sync.

        :param
        :return: The rendered template.
        """
        change_lists = ChangeListHandler.get_all()
        response = [c.to_dict() for c in change_lists]
        return jsonify(response)

    @expose('/get_change_list/<id>', methods=['GET'])
    def get_change_list(self, id):
        """Renders an item import view.

        :param id: Identifer of ChangeListIndexes
        :return: The rendered template.
        """
        resource = ChangeListHandler.get_change_list(id)
        return jsonify(resource.to_dict())

    @expose('/create', methods=['POST'])
    def create(self):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        data = request.get_json()
        resource = ChangeListHandler(**data)
        result = resource.save()
        if result:
            return jsonify(data=result.to_dict(), success=True)
        else:
            return jsonify(data=None, success=False)

    @expose('/update/<id>', methods=['POST'])
    def update(self, id):
        """Renders an item import view.

        :param:
        :return: The rendered template.
        """
        data = request.get_json()
        data['id'] = id
        resource = ChangeListHandler(**data)
        result = resource.save()
        if result:
            return jsonify(data=result.to_dict(), success=True)
        else:
            return jsonify(data=None, success=False)

    @expose('/delete/<id>', methods=['POST'])
    def delete(self, id):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        resource = ChangeListHandler.delete(id)
        if resource:
            return jsonify(data=None, success=True)
        else:
            return jsonify(data=None, success=False)


invenio_admin_resource_list = {
    'view_class': AdminResourceListView,
    'kwargs': {
        'category': _('Resource Sync'),
        'name': _('Resource List'),
        'endpoint': 'resource_list'
    }
}


invenio_admin_change_list = {
    'view_class': AdminChangeListView,
    'kwargs': {
        'category': _('Resource Sync'),
        'name': _('Change List'),
        'endpoint': 'change_list'
    }
}


__all__ = (
    'invenio_admin_resource_list',
    'invenio_admin_change_list',
)
