# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Weko-Schema-UI admin."""

from flask import abort, current_app, flash, jsonify, make_response, \
    redirect, request, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _

from .permissions import schema_permission
from .schema import delete_schema, delete_schema_cache, schema_list_render


class OAISchemaSettingView(BaseView):
    """OAI Schema Settings."""

    @schema_permission.require(http_exception=403)
    @expose('/', methods=['GET'])
    def list(self):
        """Render schema list view."""
        records = schema_list_render()
        return self.render(
            current_app.config['WEKO_SCHEMA_UI_ADMIN_LIST'],
            records=records)

    @schema_permission.require(http_exception=403)
    @expose('/add', methods=['GET'])
    def add(self):
        """Render schema add view."""
        return self.render(
            current_app.config['WEKO_SCHEMA_UI_ADMIN_UPLOAD'],
            record={})

    @schema_permission.require(http_exception=403)
    @expose('/delete', methods=['POST'])
    def delete(self, pid=None):
        """Delete schema with pid."""
        pid = pid or request.values.get('pid')
        schema_name = delete_schema(pid)
        # delete schema cache on redis
        delete_schema_cache(schema_name)

        schema_name = schema_name.replace("_mapping", "")
        # for k, v in current_app.config["RECORDS_UI_EXPORT_FORMATS"].items():
        #     if isinstance(v, dict):
        #         for v1 in v.values():
        #             if v.get(schema_name):
        #                 v.pop(schema_name)
        #                 break
        return redirect(url_for("schemasettings.list"))


oai_schema_adminview = {
    'view_class': OAISchemaSettingView,
    'kwargs': {
        'category': _('Item Types'),
        'name': _('OAI Schema'),
        'endpoint': 'schemasettings'
    }
}

__all__ = (
    'oai_schema_adminview',
)
