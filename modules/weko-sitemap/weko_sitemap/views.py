# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-sitemap."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

from flask import Blueprint, abort, current_app, render_template, request, url_for,make_response
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from invenio_db import db

blueprint = Blueprint(
    'weko_sitemap',
    __name__,
    url_prefix='/',
    template_folder='templates',
    static_folder='static',
)

@blueprint.route('/robots.txt')
def display_robots_txt():
    # return current_app.send_static_file('robots.txt')
    robot_txt = ""
    if "WEKO_SITEMAP__ROBOT_TXT" in current_app.config:
        robot_txt = current_app.config.get("WEKO_SITEMAP__ROBOT_TXT","")
    resp = make_response(render_template('weko_sitemap/robots.txt.tmpl',robot_txt = robot_txt,sitemapindex = url_for('flask_sitemap.sitemap', _external=True)))
    resp.headers['Content-Type'] = "text/plain"
    return resp

@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_sitemap dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()