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

from flask import Blueprint, render_template, current_app, jsonify
from flask_babelex import gettext as _

from .api import Handle

blueprint = Blueprint(
    'weko_handle',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/handle',
)

@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        "weko_handle/index.html",
        module_name=_('WEKO-Handle'))
