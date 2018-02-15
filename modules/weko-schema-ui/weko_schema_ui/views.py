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

import shutil, json
from flask import Blueprint, render_template, current_app, request, redirect, url_for
from flask_babelex import gettext as _
from flask_login import login_required
from .schema import SchemaConverter
from invenio_db import db

from .api import WekoSchema

blueprint = Blueprint(
    'weko_schema_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/schema", methods=['GET'])
@blueprint.route("/schema/", methods=['GET'])
# @login_required
def index():
    """Render a basic view."""
    return render_template(current_app.config['WEKO_SCHEMA_UI_UPLOAD'], record={})


@blueprint.route("/schema/list", methods=['GET'])
@blueprint.route("/schema/list/", methods=['GET'])
# @login_required
def list():
    """Render a schema list view."""
    records = schema_list_render()
    return render_template(current_app.config['WEKO_SCHEMA_UI_LIST'], records=records)


@blueprint.route("/schema", methods=['POST'])
@blueprint.route("/schema/<pid>", methods=['POST'])
def delete(pid=None):
    """aaa"""
    pid = pid or request.values.get('pid')
    schema_name = WekoSchema.delete_by_id(pid)
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


def schema_list_render(pid=None, **kwargs):
    """aaa"""

    lst = WekoSchema.get_all()

    records = []
    for r in lst:
        sc = r.form_data.copy()
        sc.update(dict(schema_name=r.schema_name))
        sc.update(dict(pid=str(r.id)))
        sc.update(dict(dis="disabled" if r.isfixed else None))
        records.append(sc)

    del lst

    return records


# @blueprint.route("/schemas/<pid>", methods=['POST'])
# def save(pid):
#     """"""
#     xsd_location_folder = current_app.config['WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER']. \
#         format(current_app.config['INSTANCE_PATH'])
#     furl = xsd_location_folder + "tmp/" + pid + "/"
#     dst = xsd_location_folder + pid + "/"
#     data = request.get_json()
#     data.pop('$schema')
#     sn = data.get('name')
#
#     fn = furl + sn + ".xsd"
#
#     xsd = SchemaConverter(fn, data.get('root_name'))
#     WekoSchema.create(pid, sn + "_mapping", data, xsd.to_dict(), xsd.namespaces)
#     db.session.commit()
#
#     # move out those files from tmp folder
#     shutil.move(furl, dst)
#
#     return redirect(url_for(".list"), code=303)
