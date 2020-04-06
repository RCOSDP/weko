# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Minimal Flask application example.

SPHINX-START

First install weko-admin, setup the application and load
fixture data by running:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Next, start the development server:

.. code-block:: console

   $ export FLASK_APP=app.py FLASK_DEBUG=1
   $ flask run

and open the example application in your browser:

.. code-block:: console

    $ open http://127.0.0.1:5000/

To reset the example application run:

.. code-block:: console

    $ ./app-teardown.sh

SPHINX-END
"""

import os

import pkg_resources
from flask import Flask, redirect, url_for
from flask_babelex import Babel
from flask_menu import Menu
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint
from invenio_admin import InvenioAdmin
from invenio_admin.views import blueprint as blueprint_admin_ui
from invenio_db import InvenioDB
from invenio_i18n import InvenioI18N
from invenio_mail import InvenioMail
from wtforms.i18n import messages_path

from weko_admin import WekoAdmin

# Create Flask application
try:
    pkg_resources.get_distribution('invenio_assets')
    from invenio_assets import InvenioAssets
    INVENIO_ASSETS_AVAILABLE = True
except pkg_resources.DistributionNotFound:
    INVENIO_ASSETS_AVAILABLE = False

try:
    pkg_resources.get_distribution('invenio_theme')
    from invenio_theme import InvenioTheme
    INVENIO_THEME_AVAILABLE = True
except pkg_resources.DistributionNotFound:
    INVENIO_THEME_AVAILABLE = False


# Create Flask application
app = Flask(__name__)
app.config.update(
    ACCOUNTS_USE_CELERY=False,
    BABEL_DEFAULT_LOCALE='en',
    I18N_TRASNLATION_PATHS=[messages_path()],
    MAIL_SUPPRESS_SEND=True,
    SECRET_KEY='1q2w3edr4rfgt5567yghgy77',
    SQLALCHEMY_DATABASE_URI=os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///instance/test.db'
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    SQLALCHEMY_ECHO=False,
    WTF_CSRF_ENABLED=False,
)
app.testing = True
os.environ['CI'] = 'false'
Babel(app)
Menu(app)
InvenioMail(app)
InvenioI18N(app)
InvenioDB(app)
if INVENIO_ASSETS_AVAILABLE:
    InvenioAssets(app)
if INVENIO_THEME_AVAILABLE:
    InvenioTheme(app)
InvenioAccess(app)
InvenioAccounts(app=app, sessionstore=None)
app.register_blueprint(blueprint)
WekoAdmin(app)

InvenioAdmin(app)
app.register_blueprint(blueprint_admin_ui)


@app.route('/')
def index():
    """Example index page route."""
    return redirect(url_for('weko_admin.session_info_offline'))
