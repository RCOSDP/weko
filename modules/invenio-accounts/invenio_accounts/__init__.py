# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio user management and authentication.

Adminstration interface
-----------------------
You can view and manage users and roles via the administration interface. Below
is a screenshot from the user creation:

.. image:: admin.png

Command-line interface
----------------------
Users and roles can be created via the CLI. Below is a simple example of
creating a user, a role and assining the user to the role:

.. code-block:: console

    $ flask users create --active info@inveniosoftware.org
    $ flask roles create admins
    $ flask roles add info@inveniosoftware.org admins

You can also e.g. deactive users:

.. code-block:: console

    $ flask users deactivate info@inveniosoftware.org
"""

# Monkey patch Werkzeug 2.1
# Flask-Login uses the safe_str_cmp method which has been removed in Werkzeug
# 2.1. Flask-Login v0.6.0 (yet to be released at the time of writing) fixes the
# issue. Once we depend on Flask-Login v0.6.0 as the minimal version in
# Flask-Security-Invenio/Invenio-Accounts we can remove this patch again.
try:
    # Werkzeug <2.1
    from werkzeug import security

    security.safe_str_cmp
except AttributeError:
    # Werkzeug >=2.1
    import hmac

    from werkzeug import security

    security.safe_str_cmp = hmac.compare_digest

from .ext import InvenioAccounts, InvenioAccountsREST, InvenioAccountsUI
from .proxies import current_accounts

__version__ = "5.0.1"

__all__ = (
    "__version__",
    "current_accounts",
    "InvenioAccounts",
    "InvenioAccountsUI",
    "InvenioAccountsREST",
)
