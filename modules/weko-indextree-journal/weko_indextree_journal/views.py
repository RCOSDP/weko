# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-indextree-journal."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

import json
import os
import sys

import numpy
from flask import Blueprint, abort, current_app, json, jsonify, render_template
from flask_babelex import gettext as _
from flask_login import login_required
from invenio_i18n.ext import current_i18n
from invenio_db import db
from weko_groups.api import Group
from weko_records.api import ItemTypes

from .api import Journals
from .permissions import indextree_journal_permission
from .tasks import export_journal_task

blueprint = Blueprint(
    'weko_indextree_journal',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/indextree/journal',
)


# @blueprint.route("/index/<int:index_id>")
# def get_journal_by_index_id(index_id=0):
#     """Get journal by index id."""
#     try:
#         result = None
#         if index_id > 0:
#             journal = Journals.get_journal_by_index_id(index_id)
#
#         if journal is None:
#             journal = '{}'
#         return jsonify(journal)
#     except BaseException:
#         current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
#     return abort(400)


@blueprint.route("/export", methods=['GET'])
@login_required
def export_journals():
    """Export journals information to file."""
    try:
        # Get all journal records in journal table.
        journals = Journals.get_all_journals()
        results = [obj.__dict__ for obj in journals]
        data = numpy.asarray(results)
        file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
        file_delimiter = '\t' if file_format == 'tsv' else ','
        file_name = 'journal.{}'.format(file_format)
        numpy.savetxt(file_name, data, delimiter=file_delimiter)

        # jsonList = json.dumps({"results" : results})
        # Save journals information to file
        return jsonify({"result": True})
    except Exception as ex:
        current_app.logger.debug(ex)
    return jsonify({"result": False})


def obj_dict(obj):
    """Return a dict."""
    return obj.__dict__


@blueprint.route('/save/kbart', methods=['GET'])
@login_required
def check_view(item_type_id=0):
    """Render a check view."""
    result = export_journal_task(p_path='')
    return jsonify(result)



@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_indextree_journal dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()