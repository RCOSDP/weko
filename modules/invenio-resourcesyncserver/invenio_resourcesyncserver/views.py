# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncServer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of invenio-resourcesyncserver."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

from flask import Blueprint, redirect, Response, request, abort
from flask_babelex import gettext as _
from .utils import render_resource_dump_xml, render_resource_list_xml, \
    get_file_content, get_resourcedump_marnifest, public_index_checked
from .api import ResourceListHandler

blueprint = Blueprint(
    'invenio_resourcesyncserver',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/resync/<index_id>/resourcelist.xml")
@public_index_checked
def resource_list(index_id):
    """Render a basic view."""
    r = render_resource_list_xml(index_id)
    if r is None:
        abort(404)
    return Response(r, mimetype='text/xml')


@blueprint.route("/resync/<index_id>/resourcedump.xml")
@public_index_checked
def resource_dump(index_id):
    """Render a basic view."""
    r = render_resource_dump_xml(index_id)
    if r is None:
        abort(404)
    return Response(r, mimetype='text/xml')


@blueprint.route("/resync/<index_id>/file_content.zip")
def file_content(index_id):
    """Render a basic view."""
    r = get_file_content(index_id)
    if r:
        return r
    else:
        return redirect(request.url_root)


@blueprint.route("/resync/capability.xml")
def capability():
    """Render a basic view."""
    caplist = ResourceListHandler.get_capability_list()
    if caplist is None:
        abort(404)
    return Response(caplist, mimetype='text/xml')


@blueprint.route("/resync/<record_id>/resourcedump_manifest.xml")
def resourcedump_manifest(record_id):
    """Render a basic view."""
    res_manifest = get_resourcedump_marnifest(record_id)
    if res_manifest is None:
        abort(404)
    return Response(res_manifest, mimetype='text/xml')
