# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Items-Autofill is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-items-autofill."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

from flask import Blueprint, render_template
from flask_babelex import gettext as _

blueprint = Blueprint(
    'weko_items_autofill',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/items/autofill',
)


@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        "weko_items_autofill/index.html",
        module_name=_('WEKO-Items-Autofill'))
