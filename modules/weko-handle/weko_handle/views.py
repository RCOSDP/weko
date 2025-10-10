# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Handle is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-handle."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_babelex import gettext as _
from invenio_db import db

from .api import Handle

blueprint = Blueprint(
    'weko_handle',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/handle',
)

blueprint_api = Blueprint(
    'weko_handle_api',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/handle',
)


@blueprint.route("/")
def index():
    """Renders a Page-Not-found screen"""
    return render_template("invenio_theme/404.html")


@blueprint.route('/retrieve', methods=['POST'])
def retrieve_handle():
    """Retrieve a handle."""
    try:
        handle = request.form['handle']
        handle_obj = Handle()
        if handle:
            return handle_obj.retrieve_handle(handle)
        else:
            return jsonify(code=0, msg='Retrieved handle not found!')
    except Exception as e:
        current_app.logger.error('Unexpected error: ', e)


@blueprint.route('/register', methods=['POST'])
def register_handle():
    """Register a handle."""
    try:
        location = request.form['location']
        handle_obj = Handle()
        if location:
            handle = handle_obj.register_handle(location)
            return jsonify(handle)

        return jsonify({'code': -1, 'msg': 'error'})
    except Exception as e:
        current_app.logger.error('Unexpected error: ', e)

@blueprint.route('/delete', methods=['POST'])
def delete_handle():
    """Delete a handle."""
    try:
        hdl = request.form['hdl']
        handle_obj = Handle()
        if hdl:
            handle = handle_obj.delete_handle(hdl)
            return jsonify(handle)

        return jsonify({'code': -1, 'msg': 'error'})
    except Exception as e:
        current_app.logger.error('Unexpected error: ', e)

@blueprint.teardown_request
@blueprint_api.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_handle dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()
