# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Handle is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-handle."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.
#
# NOTE: The /retrieve, /register and /delete routes were removed. They exposed
# weko_handle.api.Handle over unauthenticated POST (anyone could register or
# delete a handle), and nothing in WEKO called them: handle registration goes
# through Handle() directly from weko-workflow. Use the Python API instead.

from __future__ import absolute_import, print_function

from flask import Blueprint, current_app, render_template
from flask_babelex import gettext as _
from invenio_db import db

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
