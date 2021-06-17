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
    resp = make_response(render_template('weko_sitemap/robots.txt.tmpl',sitemapindex = url_for('flask_sitemap.sitemap', _external=True)))
    resp.headers['Content-Type'] = "text/plain"
    return resp
