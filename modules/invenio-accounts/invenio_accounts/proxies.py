# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Helper proxy to the state object."""

from flask import current_app, g
from werkzeug.local import LocalProxy

from .api import DBUsersChangeHistory

current_accounts = LocalProxy(lambda: current_app.extensions["invenio-accounts"])
"""Proxy to the current Invenio-Accounts extension."""

current_security = LocalProxy(lambda: current_app.extensions["security"])
"""Proxy to the Flask-Security extension."""

current_datastore = LocalProxy(lambda: current_app.extensions["security"].datastore)
"""Proxy to the current Flask-Security user datastore."""


def get_db_change_history():
    """Proxy funtion to db change history.

    The "g" object is local to the Flask application context. An app context
    is pushed on every request or CLI command. This means that the users
    change history is automatically cleared with on tear down of the app
    context. This matches up with the database session is also tied to the
    app context.
    """
    if "db_change_history" not in g:
        g.db_change_history = DBUsersChangeHistory()

    return g.db_change_history


current_db_change_history = LocalProxy(get_db_change_history)
"""Proxy for the currently instantiated users db change history."""
