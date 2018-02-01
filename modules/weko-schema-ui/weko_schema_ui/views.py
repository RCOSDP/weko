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

import shutil
from flask import Blueprint, render_template, current_app, request, redirect,url_for
from flask_babelex import gettext as _
from flask_login import login_required
from .schema import SchemaConventer
from invenio_db import db

from .api import WekoSchema

blueprint = Blueprint(
    'weko_schema_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/schema", methods=['GET'])
# @login_required
def index():
    """Render a basic view."""
    return render_template(current_app.config['WEKO_SCHEMA_UI_UPLOAD'], record={})


@blueprint.route("/schema/list", methods=['GET'])
# @login_required
def list():
    """Render a schema list view."""
    records, m_url, del_url = schema_list_render()
    return render_template(current_app.config['WEKO_SCHEMA_UI_LIST'], records=records, m_url=m_url, del_url=del_url)


def schema_list_render(pid=None, **kwargs):
    """aaa"""

    m_url = request.host_url
    del_url = m_url + "schema/"
    m_url = m_url + "items/"
    lst = WekoSchema.get_all()

    records = []
    for r in lst:
        sc = r.form_data.copy()
        sc.update(dict(schema_name=r.schema_name))
        sc.update(dict(pid=str(r.id)))
        sc.update(dict(is_mapping=r.is_mapping))
        records.append(sc)

    del lst

    return records, m_url, del_url


@blueprint.route("/schema/<pid>", methods=['DELETE'])
def delete(pid):
    """aaa"""
    WekoSchema.delete_by_id(pid)

    return redirect(url_for(".list"), code=303)


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
#     xsd = SchemaConventer(fn, data.get('root_name'))
#     WekoSchema.create(pid, sn + "_mapping", data, xsd.to_dict(), xsd.namespaces)
#     db.session.commit()
#
#     # move out those files from tmp folder
#     shutil.move(furl, dst)
#
#     return redirect(url_for(".list"), code=303)
