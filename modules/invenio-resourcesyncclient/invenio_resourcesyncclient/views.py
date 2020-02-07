# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncClient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of invenio-resourcesyncclient."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

from flask import Blueprint, render_template, jsonify, \
    make_response
from flask_babelex import gettext as _
from .utils import read_capability, sync_baseline, sync_audit, sync_incremental
from .api import ResyncHandler

try:  # python3
    from urllib.parse import urlsplit, urlunsplit
except ImportError:  # pragma: no cover  python2
    from urlparse import urlsplit, urlunsplit

blueprint = Blueprint(
    'invenio_resourcesyncclient',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        "invenio_resourcesyncclient/index.html",
        module_name=_('INVENIO-ResourceSyncClient'))


@blueprint.route("/resync/sync/<resync_id>")
def sync(resync_id):
    """Sync a resource sync. Save data to local"""
    resync_index = ResyncHandler.get_resource_sync_by_id(resync_id)
    if not resync_index:
        raise ValueError('No Resync Index found')
    # Validate base_url
    base_url = resync_index.base_url
    capability = read_capability(base_url)
    print(capability)

    mode = resync_index.resync_mode
    save_dir = resync_index.resync_save_dir
    map = [base_url]
    if save_dir:
        map.append(save_dir)

    parts = urlsplit(map[0])
    uri_host = urlunsplit([parts[0], parts[1], '', '', ''])

    # map = [base_url, save_dir]
    # if mode == current_app.config.get[
    #         'INVENIO_RESYNC_INDEXES_MODE'
    #     ].get('baseline'):
    if mode == 'Baseline':
        if not capability or (
                capability != 'resourcelist' and capability != 'resourcedump'):
            raise ValueError('Bad URL')
        result = False
        while map[0] != uri_host and not result:
            result = sync_baseline(map=map, base_url=base_url, dryrun=False)
        return make_response('OK', 200)
    # elif mode == current_app.config.get[
    #     'INVENIO_RESYNC_INDEXES_MODE'
    # ].get('audit'):
    elif mode == 'Audit':
        if not capability or (
                capability != 'resourcelist' and capability != 'changelist'):
            raise ValueError('Bad URL')
        # do the same logic with Baseline
        # to make sure right url is used
        result = False
        while map[0] != uri_host and not result:
            result = sync_baseline(map=map, base_url=base_url, dryrun=True)
        return jsonify(sync_audit(map))
    elif mode == 'Incremental':
        if not capability or (
                capability != 'changelist' and capability != 'changedump'):
            raise (
                'Bad URL, not a changelist/changedump, cannot sync incremental')
        result = False
        while map[0] != uri_host and not result:
            # TODO : handle from date here
            resync_index.from_date = '2020-23-01'
            result = sync_incremental(map, base_url, resync_index.from_date)
            return jsonify({'result': result})


@blueprint.route("/resync/import")
def import_resync_data():
    """Import local data to weko system"""
    return None
