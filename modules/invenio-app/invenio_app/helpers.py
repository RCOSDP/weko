# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Helpers."""

from __future__ import absolute_import, print_function

import six
from flask import current_app, request
from uritools import uricompose, urisplit
from werkzeug.utils import import_string


class TrustedHostsMixin(object):
    """Mixin for reading trusted hosts from application config."""

    @property
    def trusted_hosts(self):
        """Get list of trusted hosts."""
        if current_app:
            return current_app.config.get('APP_ALLOWED_HOSTS', None)


def get_safe_redirect_target(arg='next', _target=None):
    """Get URL to redirect to and ensure that it is local.

    :param arg: URL argument.
    :returns: The redirect target or ``None``.
    """
    for target in _target, request.args.get(arg), request.referrer:
        if target:
            redirect_uri = urisplit(target)
            allowed_hosts = current_app.config.get('APP_ALLOWED_HOSTS', [])
            if redirect_uri.host in allowed_hosts:
                return target
            elif redirect_uri.path:
                return uricompose(
                    path=redirect_uri.path,
                    query=redirect_uri.query,
                    fragment=redirect_uri.fragment)
    return None


def obj_or_import_string(value, default=None):
    """Import string or return object.

    :params value: Import path or class object to instantiate.
    :params default: Default object to return if the import fails.
    :returns: The imported object.
    """
    if isinstance(value, six.string_types):
        return import_string(value)
    elif value:
        return value
    return default
