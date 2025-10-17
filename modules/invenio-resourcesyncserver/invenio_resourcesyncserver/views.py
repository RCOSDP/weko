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

from flask import Blueprint, Response, abort, redirect, url_for, current_app, jsonify
from flask_login import current_user
from invenio_db import db
from invenio_oaiserver.response import getrecord
from lxml import etree
from weko_index_tree.models import Index

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
    """Render resource list."""
    resource = ResourceListHandler.get_resource_by_repository_id(index_id)
    if not resource or not resource.status:
        abort(404)
    output_xml = resource.get_resource_list_xml()
    if not output_xml:
        abort(404)
    return Response(
        output_xml,
        mimetype='application/xml')


@blueprint.route("/resync/<index_id>/resourcedump.xml")
def resource_dump(index_id):
    """Render resource dump."""
    resource = ResourceListHandler.get_resource_by_repository_id(index_id)
    if not resource or not resource.status:
        abort(404)
    output_xml = resource.get_resource_dump_xml()
    if not output_xml:
        abort(404)
    return Response(
        output_xml,
        mimetype='application/xml')


@blueprint.route("/resync/<index_id>/<record_id>/file_content.zip")
def file_content(index_id, record_id):
    """Download file content."""
    resource = ResourceListHandler.get_resource_by_repository_id(index_id)
    if resource:
        result = resource.get_record_content_file(record_id)
        if result:
            return result
    abort(404)


@blueprint.route("/resync/capability.xml")
def capability():
    """Render capability list xml."""
    cap_list = render_capability_xml()
    if not cap_list:
        abort(404)
    return Response(cap_list, mimetype='application/xml')


@blueprint.route("/resync/<index_id>/<record_id>/resourcedump_manifest.xml")
def resource_dump_manifest(index_id, record_id):
    """Render resource dump manifest."""
    resource = ResourceListHandler.get_resource_by_repository_id(index_id)
    if resource:
        result = resource.get_resource_dump_manifest(record_id)
        if result:
            return Response(
                result,
                mimetype='application/xml'
            )
    abort(404)


@blueprint.route("/resync/<index_id>/changelist.xml")
def change_list_index(index_id):
    """Render change list index."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if cl:
        r = cl.get_change_list_index()
        if r:
            return Response(r, mimetype='application/xml')
    abort(404)


@blueprint.route("/resync/<index_id>/<from_date>/changelist.xml")
def change_list(index_id, from_date):
    """Render change list."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if cl:
        r = cl.get_change_list_content_xml(from_date)
        if r:
            return Response(r, mimetype='application/xml')
    abort(404)


@blueprint.route("/resync/<index_id>/changedump.xml")
def change_dump_index(index_id):
    """Render change dump index."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if cl:
        r = cl.get_change_dump_index()
        if r:
            return Response(r, mimetype='application/xml')
    abort(404)


@blueprint.route("/resync/<index_id>/<from_date>/changedump.xml")
def change_dump(index_id, from_date):
    """Render change dump."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if cl:
        r = cl.get_change_dump_xml(from_date)
        if r:
            return Response(r, mimetype='application/xml')
    abort(404)


@blueprint.route("/resync/<index_id>/<record_id>/changedump_manifest.xml")
def change_dump_manifest(index_id, record_id):
    """Render change dump manifest."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if cl:
        r = cl.get_change_dump_manifest_xml(record_id)
        if r:
            return Response(r, mimetype='application/xml')
    abort(404)


@blueprint.route("/resync/<index_id>/<record_id>/change_dump_content.zip")
def change_dump_content(index_id, record_id):
    """Render change dump content."""
    cl = ChangeListHandler.get_change_list_by_repo_id(index_id)
    if cl:
        r = cl.get_record_content_file(record_id)
        if r:
            return r
    abort(404)


@blueprint.route("/.well-known/resourcesync")
def well_know_resourcesync():
    """Render well know resourcesync."""
    return Response(
        render_well_know_resourcesync(),
        mimetype='application/xml'
    )


@blueprint.route("/resync/source.xml")
def source_description():
    """Render well know resourcesync."""
    return Response(
        render_well_know_resourcesync(),
        mimetype='application/xml'
    )


@blueprint.route("/resync/<index_id>/records/<record_id>")
def record_detail_in_index(index_id, record_id):
    """Alternate route for record detail."""

    recid_zfill=record_id.zfill(current_app.config.get('OAISERVER_CONTROL_NUMBER_LEN', 0))
    pid = current_app.config.get('OAISERVER_ID_PREFIX', '') + str(recid_zfill)
    et = etree.XML(etree.tostring(getrecord(identifier=pid,metadataPrefix='jpcoar',verb='getrecord')))
    records = et.findall('./getrecord/record/metadata/{https://github.com/JPCOAR/schema/blob/master/1.0/}jpcoar', namespaces=et.nsmap)
    xml =  ''
    if len(records)==1:
      xml = etree.tostring(records[0], encoding='utf-8').decode()

    return Response(xml,mimetype='application/xml')
    #return redirect(
    #    url_for('invenio_records_ui.recid',
    #            pid_value=record_id))


@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("invenio_resourcesyncserver dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()
