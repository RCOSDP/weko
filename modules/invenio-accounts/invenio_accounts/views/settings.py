# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio user management and authentication."""

from __future__ import absolute_import, print_function

from flask import Blueprint, current_app
from flask_babelex import lazy_gettext as _
from flask_menu import current_menu

blueprint = Blueprint(
    'invenio_accounts',
    __name__,
    url_prefix='/account/settings',
    template_folder='../templates',
    static_folder='static',
)


@blueprint.record_once
def post_ext_init(state):
    """."""
    app = state.app

    app.config.setdefault(
        "ACCOUNTS_SITENAME",
        app.config.get("THEME_SITENAME", "Invenio"))
    app.config.setdefault(
        "ACCOUNTS_BASE_TEMPLATE",
        app.config.get("BASE_TEMPLATE",
                       "invenio_accounts/base.html"))
    app.config.setdefault(
        "ACCOUNTS_COVER_TEMPLATE",
        app.config.get("COVER_TEMPLATE",
                       "invenio_accounts/base_cover.html"))
    app.config.setdefault(
        "ACCOUNTS_SETTINGS_TEMPLATE",
        app.config.get("SETTINGS_TEMPLATE",
                       "invenio_accounts/settings/base.html"))


@blueprint.before_app_first_request
def init_menu():
    """Initialize menu before first request."""
    # Register breadcrumb root
    item = current_menu.submenu('breadcrumbs.settings')
    item.register('', _('Account'))
    item = current_menu.submenu('breadcrumbs.{0}'.format(
        current_app.config['SECURITY_BLUEPRINT_NAME']))

    if current_app.config.get('SECURITY_CHANGEABLE', True):
        item.register('', _('Change password'))

        # Register settings menu
        item = current_menu.submenu('settings.change_password')
        item.register(
            "{0}.change_password".format(
                current_app.config['SECURITY_BLUEPRINT_NAME']),
            # NOTE: Menu item text (icon replaced by a user icon).
            _('%(icon)s Change password',
                icon='<i class="fa fa-key fa-fw"></i>'),
            order=1)

        # Register breadcrumb
        item = current_menu.submenu('breadcrumbs.{0}.change_password'.format(
            current_app.config['SECURITY_BLUEPRINT_NAME']))
        item.register(
            "{0}.change_password".format(
                current_app.config['SECURITY_BLUEPRINT_NAME']),
            _("Change password"),
            order=0,
        )


@blueprint.before_app_first_request
def check_security_settings():
    """Warn if session cookie is not secure in production."""
    in_production = not (current_app.debug or current_app.testing)
    secure = current_app.config.get('SESSION_COOKIE_SECURE')
    if in_production and not secure:
        current_app.logger.warning(
            "SESSION_COOKIE_SECURE setting must be set to True to prevent the "
            "session cookie from being leaked over an insecure channel."
        )
