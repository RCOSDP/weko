# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-ResourceSyncServer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-resourcesyncserver."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

from flask import Blueprint, render_template, jsonify, Response
from flask_babelex import gettext as _
from .utils import render_resource_dump_xml, render_resource_list_xml, \
    get_file_content
blueprint = Blueprint(
    'weko_resourcesyncserver',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/resource/<index_id>/resource_list")
def resource_list(index_id):
    """Render a basic view."""
    r = render_resource_list_xml(index_id)
    return Response(r, mimetype='text/xml')


@blueprint.route("/resource/<index_id>/resource_dump")
def resource_dump(index_id):
    """Render a basic view."""
    r = render_resource_dump_xml(index_id)
    return Response(r, mimetype='text/xml')


@blueprint.route("/resource/<index_id>/file_content.zip")
def file_content(index_id):
    """Render a basic view."""
    r = get_file_content(index_id)
    return r
