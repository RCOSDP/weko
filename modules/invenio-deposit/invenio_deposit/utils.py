# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Implementention of various utility functions."""

from __future__ import absolute_import, print_function

from flask import request
from invenio_oauth2server import require_api_auth, require_oauth_scopes

from .scopes import write_scope


def mark_as_action(f):
    """Decorator for marking method as deposit action.

    Allows creation of new REST API action on ``Deposit`` subclass.
    Following example shows possible `cloning` of a deposit instance.

    .. code-block:: python

        from invenio_deposit.api import Deposit

        class CustomDeposit(Deposit):
            @mark_as_action
            def clone(self, pid=None):
                new_bucket = self.files.bucket.clone()
                new_deposit = Deposit.create(self.dumps())
                new_deposit.files.bucket = new_bucket
                new_deposit.commit()

            @mark_as_action
            def edit(self, pid=None):
                # Extend existing action.
                self['_last_editor'] = current_user.get_id()
                return super(CustomDeposit, self).edit(pid=pid)

            # Disable publish action from REST API.
            def publish(self, pid=None):
                return super(CustomDeposit, self).publish(pid=pid)

    :param f: Decorated method.
    """
    f.__deposit_action__ = True
    return f


def extract_actions_from_class(record_class):
    """Extract actions from class."""
    for name in dir(record_class):
        method = getattr(record_class, name, None)
        if method and getattr(method, '__deposit_action__', False):
            yield method.__name__


def check_oauth2_scope(can_method, *myscopes):
    """Base permission factory that check OAuth2 scope and can_method.

    :param can_method: Permission check function that accept a record in input
        and return a boolean.
    :param myscopes: List of scopes required to permit the access.
    :returns: A :class:`flask_principal.Permission` factory.
    """
    def check(record, *args, **kwargs):
        @require_api_auth()
        @require_oauth_scopes(*myscopes)
        def can(self):
            return can_method(record)

        return type('CheckOAuth2Scope', (), {'can': can})()
    return check


def can_elasticsearch(record):
    """Check if a given record is indexed.

    :param record: A record object.
    :returns: If the record is indexed returns `True`, otherwise `False`.
    """
    search = request._methodview.search_class()
    search = search.get_record(str(record.id))
    return search.count() == 1


check_oauth2_scope_write = check_oauth2_scope(lambda x: True, write_scope.id)
"""Permission factory that check oauth2 scope.

The scope :class:`invenio_deposit.scopes.write_scope` is checked.
"""

check_oauth2_scope_write_elasticsearch = check_oauth2_scope(
    can_elasticsearch, write_scope.id)
"""Permission factory that check oauth2 scope and if the record is indexed.

The scope :class:`invenio_deposit.scopes.write_scope` is checked.
"""
