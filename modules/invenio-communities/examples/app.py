# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Minimal Flask application example for development.

Run example development server:

.. code-block:: console

   $ cd examples
   $ flask -a app.py --debug run
"""

from __future__ import absolute_import, print_function

import os

from flask import Flask
from flask_babelex import Babel
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB
from invenio_records import InvenioRecords

from invenio_communities import InvenioCommunities
from invenio_communities.views.api import blueprint as api_blueprint
from invenio_communities.views.ui import blueprint as ui_blueprint

# Create Flask application
app = Flask(__name__)

app.config.update(
    SECRET_KEY="CHANGE_ME",
    SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
    SQLALCHEMY_DATABASE_URI=os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
)

app.register_blueprint(blueprint)
Babel(app)
InvenioDB(app)
InvenioAssets(app)
Menu(app)
InvenioRecords(app)
InvenioAccounts(app)
InvenioAdmin(app, permission_factory=lambda x: x,
             view_class_factory=lambda x: x)
InvenioCommunities(app)
app.register_blueprint(ui_blueprint)
app.register_blueprint(api_blueprint)
