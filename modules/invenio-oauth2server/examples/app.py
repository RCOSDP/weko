# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


r"""Minimal Flask application example for development.

SPHINX-START

Run example development server:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ ./app-setup.sh
   $ ./app-fixtures.sh
   $ FLASK_APP=app.py flask run -p 5000

Open settings page to generate a token:

.. code-block:: console

   $ open http://127.0.0.1:5000/account/settings/applications

Login with:

    | username: admin\@inveniosoftware.org
    | password: 123456

Click on "New token" and compile the form:
insert the name "foobar", check scope "test:scope" and click "create".
The server will show you the generated Access Token.

Make a request to test the token:

.. code-block:: console

    export TOKEN=<generated Access Token>
    curl -i -X GET -H "Content-Type:application/json" http://127.0.0.1:5000/ \
        -H "Authorization:Bearer $TOKEN"

To end and remove any traces of example application, stop the example
application and run:
.. code-block:: console

   $ ./app-teardown.sh


SPHINX-END
"""

from __future__ import absolute_import, print_function

import os

from flask import Flask, render_template
from flask_breadcrumbs import Breadcrumbs
from flask_oauthlib.provider import OAuth2Provider
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccountsREST, InvenioAccountsUI
from invenio_accounts.views import blueprint as blueprint_account
from invenio_admin import InvenioAdmin
from invenio_admin.views import blueprint as blueprint_admin_ui
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB
from invenio_i18n import InvenioI18N
from invenio_theme import InvenioTheme

from invenio_oauth2server import InvenioOAuth2Server, \
    InvenioOAuth2ServerREST, current_oauth2server, require_api_auth, \
    require_oauth_scopes
from invenio_oauth2server.models import Scope
from invenio_oauth2server.views import server_blueprint, settings_blueprint

# Create Flask application
app = Flask(__name__)
app.config.update(
    APP_ENABLE_SECURE_HEADERS=False,
    CELERY_ALWAYS_EAGER=True,
    CELERY_CACHE_BACKEND='memory',
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_RESULT_BACKEND='cache',
    OAUTH2_CACHE_TYPE='simple',
    OAUTHLIB_INSECURE_TRANSPORT=True,
    TESTING=True,
    DEBUG=True,  # needed to register localhost addresses as callback_urls
    SECRET_KEY='test_key',
    SECURITY_PASSWORD_HASH='plaintext',
    SECURITY_PASSWORD_SCHEMES=['plaintext'],
    SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
    LOGIN_DISABLED=False,
    TEMPLATE_AUTO_RELOAD=True,
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    SQLALCHEMY_DATABASE_URI=os.getenv(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///example.db'),
    I18N_LANGUAGES=[
        ('de', 'German'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('it', 'Italian'),
    ],
)
InvenioAssets(app)
InvenioTheme(app)
InvenioI18N(app)
Breadcrumbs(app)
InvenioDB(app)
InvenioAdmin(app)
InvenioAccess(app)
OAuth2Provider(app)
InvenioOAuth2ServerREST(app)

accounts = InvenioAccountsUI(app)
InvenioAccountsREST(app)
app.register_blueprint(blueprint_account)

InvenioOAuth2Server(app)

# Register blueprints
app.register_blueprint(settings_blueprint)
app.register_blueprint(server_blueprint)
app.register_blueprint(blueprint_admin_ui)

with app.app_context():
    # Register a test scope
    current_oauth2server.register_scope(
        Scope('test:scope', help_text='Access to the homepage',
              group='test'))


# @app.route('/jwt', methods=['GET'])
# def jwt():
#     """JWT."""
#     return render_template('jwt.html')


@app.route('/', methods=['GET', 'POST'])
@require_api_auth()
@require_oauth_scopes('test:scope')
def index():
    """Protected endpoint."""
    return 'hello world'
