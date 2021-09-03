# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Session-aware datastore."""

from __future__ import absolute_import, print_function

from flask_security import SQLAlchemyUserDatastore

from .sessions import delete_user_sessions


class SessionAwareSQLAlchemyUserDatastore(SQLAlchemyUserDatastore):
    """Datastore which deletes active session when a user is deactivated."""

    def deactivate_user(self, user):
        """Deactivate a  user.

        :param user: A :class:`invenio_accounts.models.User` instance.
        :returns: The datastore instance.
        """
        res = super(SessionAwareSQLAlchemyUserDatastore, self).deactivate_user(
            user)
        if res:
            delete_user_sessions(user)
        return res
