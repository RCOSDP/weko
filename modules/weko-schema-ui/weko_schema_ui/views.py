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

"""Blueprint for weko-schema-ui."""

from flask import (
    Blueprint, current_app, redirect, render_template, request, url_for)
from flask_login import login_required

from .permissions import schema_permission
from .schema import delete_schema, delete_schema_cache, schema_list_render

blueprint = Blueprint(
    'weko_schema_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/schema", methods=['GET'])
@blueprint.route("/schema/", methods=['GET'])
@login_required
@schema_permission.require(http_exception=403)
def index():
    """Render a basic view."""
    return render_template(
        current_app.config['WEKO_SCHEMA_UI_UPLOAD'],
        record={})


# @blueprint.route("/schema/formats/edit", methods=['GET'])
# @login_required
# @schema_permission.require(http_exception=403)
# def formats():
#     """Render a format edit view."""
#     # record = {"schemas": [{"fmo": {"prefix": "11", "namespace": "22", "schema": "33"}},
#     #           {"fmo": {"prefix": "44", "namespace": "55", "schema": "66"}}]}
# return render_template(current_app.config['WEKO_SCHEMA_UI_FORMAT_EDIT'],
# record={})


@blueprint.route("/schema/list", methods=['GET'])
@blueprint.route("/schema/list/", methods=['GET'])
@login_required
@schema_permission.require(http_exception=403)
def list():
    """Render a schema list view."""
    records = schema_list_render()
    return render_template(
        current_app.config['WEKO_SCHEMA_UI_LIST'],
        records=records)


@blueprint.route("/schema", methods=['POST'])
@blueprint.route("/schema/<pid>", methods=['POST'])
@login_required
@schema_permission.require(http_exception=403)
def delete(pid=None):
    """
    :param pid:
    :return:
    """
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
    oaif = current_app.config["OAISERVER_METADATA_FORMATS"]
    if oaif.get(schema_name):
        oaif.pop(schema_name)

    return redirect(url_for(".list"))
