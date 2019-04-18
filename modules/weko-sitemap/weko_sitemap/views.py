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

from flask import Blueprint, abort, current_app, render_template, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _

blueprint = Blueprint(
    'weko_sitemap',
    __name__,
    url_prefix='/weko/sitemaps',
    template_folder='templates',
    static_folder='static',
)
