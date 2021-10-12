# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
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

from __future__ import absolute_import, print_function

from .ext import InvenioAccounts, InvenioAccountsREST, InvenioAccountsUI
from .proxies import current_accounts
from .version import __version__

__all__ = (
    '__version__',
    'current_accounts',
    'InvenioAccounts',
    'InvenioAccountsUI',
    'InvenioAccountsREST',
)
