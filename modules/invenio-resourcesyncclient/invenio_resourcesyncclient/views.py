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

from flask import Blueprint, render_template,current_app
from flask_babelex import gettext as _

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

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
