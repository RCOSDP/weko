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

from flask import Blueprint, Response, abort, redirect, request
from flask_babelex import gettext as _

from .api import ChangeListHandler, ResourceListHandler
from .utils import render_capability_xml, render_well_know_resourcesync

blueprint = Blueprint(
    'invenio_resourcesyncserver',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/resync/<index_id>/resourcelist.xml")
def resource_list(index_id):
    """Render a basic view."""
    resource = ResourceListHandler.get_resource_by_repository_id(index_id)
    if not resource or not resource.status:
        abort(404)
    return Response(
        resource.get_resource_list_xml(),
        mimetype='application/xml')


@blueprint.route("/resync/<index_id>/resourcedump.xml")
def resource_dump(index_id):
    """Render a basic view."""
    resource = ResourceListHandler.get_resource_by_repository_id(index_id)
    if not resource or not resource.status:
        abort(404)
    return Response(
        resource.get_resource_dump_xml(),
        mimetype='application/xml')


@blueprint.route("/resync/<index_id>/<record_id>/file_content.zip")
def file_content(index_id, record_id):
    """Render a basic view."""
    resource = ResourceListHandler.get_resource_by_repository_id(index_id)
    if not resource or not resource.is_validate(record_id):
        abort(404)
    else:
        return resource.get_record_content_file(record_id)


@blueprint.route("/resync/capability.xml")
def capability():
    """Render a basic view."""
    caplist = render_capability_xml()
    if caplist is None:
        abort(404)
    return Response(caplist, mimetype='text/xml')


@blueprint.route("/resync/<index_id>/<record_id>/resource_dump_manifest.xml")
def resource_dump_manifest(index_id, record_id, date):
    """Render a basic view."""
    resource = ResourceListHandler.get_resource_by_repository_id(index_id)

    validate = not resource or not resource.is_validate(
        record_id) or not resource.resource_dump_manifest
    if validate:
        abort(404)
    return Response(
        resource.get_resource_dump_manifest(record_id),
        mimetype='text/xml'
    )


@blueprint.route("/resync/<index_id>/changelist")
def change_list_index(index_id):
    """Render a basic view."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if not cl:
        abort(404)
    r = cl.get_change_list_index()
    if r is None:
        abort(404)
    return Response(r, mimetype='application/xml')


@blueprint.route("/resync/<index_id>/<from_date>/changelist.xml")
def change_list(index_id, from_date):
    """Render a basic view."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if not cl or not cl.status:
        abort(404)
    r = cl.get_change_list_content_xml(from_date)
    if r is None:
        abort(404)
    return Response(r, mimetype='application/xml')


@blueprint.route("/resync/<index_id>/<from_date>/changedump.xml")
def change_dump(index_id, from_date):
    """Render a basic view."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if cl is None or not cl.status:
        abort(404)
    r = cl.get_change_dump_xml(from_date)
    if r is None:
        abort(404)
    return Response(r, mimetype='application/xml')


@blueprint.route("/resync/<index_id>/<record_id>/changedump_manifest.xml")
def change_dump_manifest(index_id, record_id):
    """Render a basic view."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if not cl or not cl.status or not cl.is_record_in_index(record_id):
        abort(404)
    r = cl.get_change_dump_manifest_xml(record_id)
    return Response(r, mimetype='application/xml')


@blueprint.route("/resync/<index_id>/<record_id>/change_dump_content.zip")
def change_dump_content(index_id, record_id):
    """Render a basic view."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if cl is None or not cl.status or not cl.is_record_in_index(record_id):
        abort(404)
    r = cl.get_record_content_file(record_id)
    if r:
        return r
    else:
        abort(404)


@blueprint.route("/well_know_resourcesync")
def well_know_resourcesync():
    """Render a basic view."""
    return Response(
        render_well_know_resourcesync(),
        mimetype='application/xml'
    )
