# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Consumer is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-inbox-consumer."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

from flask import Blueprint, render_template
from flask_babelex import gettext as _

from .api import blueprint_api


blueprint = Blueprint(
    'weko_inbox_consumer',
    __name__,
    template_folder='templates',
    static_folder='static',
)


blueprint_ui_init = Blueprint(
    'weko_inbox_consumer_ui_init',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint_ui_init.record_once
def init_ui(state):
    app = state.app
    app.register_blueprint(
        blueprint_api,
        url_prefix='/check_inbox'
    )


@blueprint.route('/')
def index():
    """Render a basic view."""
    return render_template(
        'weko_inbox_consumer/index.html',
        module_name=_('WEKO-Inbox-Consumer'))
