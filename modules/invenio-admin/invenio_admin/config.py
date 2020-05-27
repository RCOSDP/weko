# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Configuration for Invenio-Admin."""

ADMIN_BASE_TEMPLATE = None
"""Admin panel base template.
By default (``None``) uses the Flask-Admin template."""

ADMIN_APPNAME = 'Invenio'
"""Name of the Flask-Admin app (also the page title of admin panel)."""

ADMIN_LOGIN_ENDPOINT = 'security.login'
"""Endpoint name of the login view. Anonymous users trying to access admin
panel will be redirected to this endpoint."""

ADMIN_LOGOUT_ENDPOINT = 'security.logout'
"""Endpoint name of logout view."""

ADMIN_TEMPLATE_MODE = 'bootstrap3'
"""Flask-Admin template mode. Either ``bootstrap2`` or ``bootstrap3``."""

ADMIN_PERMISSION_FACTORY = 'invenio_admin.permissions.admin_permission_factory'
"""Permission factory for the admin views."""
