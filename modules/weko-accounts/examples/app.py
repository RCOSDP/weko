# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Minimal Flask application example.

SPHINX-START

First install weko-accounts, setup the application and load
fixture data by running:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Next, start the development server:

.. code-block:: console

   $ export FLASK_APP=app.py FLASK_DEBUG=1
   $ flask run --host 0.0.0.0

and open the example application in your browser:

.. code-block:: console

    $ open http://127.0.0.1:5000/login/?next=weko

You can login with:

- User: ``wekosoftware@nii.ac.jp``
- Password: ``123456``

You can confirm login log on console like this:
- ``auth login success: 1,515cc1c6e476da02_5a56feec,b'202.246.252.97'``

.. code-block:: console

    $ open http://127.0.0.1:5000/logout

You can confirm logout log on console like this:
- ``auth logout success: 1,2018-01-11 06:06:36.293250,b'202.246.252.97'``

To reset the example application run:

.. code-block:: console

    $ ./app-teardown.sh

SPHINX-END
"""

import os

from flask import Flask, current_app
from flask_babelex import Babel
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as blueprint_accounts
from invenio_admin import InvenioAdmin
from invenio_db import InvenioDB
from invenio_logging.console import InvenioLoggingConsole
from invenio_logging.fs import InvenioLoggingFS
from weko_accounts import WekoAccounts

# Create Flask application
app = Flask(__name__)
app.config.update({
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
})
app.config.update(
    ACCOUNTS_USE_CELERY=False,
    CELERY_ALWAYS_EAGER=True,
    CELERY_CACHE_BACKEND="memory",
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_RESULT_BACKEND="cache",
    MAIL_SUPPRESS_SEND=True,
    SECRET_KEY="1q2w3e4r5t!Q",
    SECURITY_PASSWORD_SALT="1q2w3e4r5t!Qw#E$R%T6",
)
app.secret_key = 'ExampleApp'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'SQLALCHEMY_DATABASE_URI', 'sqlite:///instance/test.db'
)
app.testing = True
os.environ['CI'] = 'false'
Babel(app)
Menu(app)
InvenioDB(app)
InvenioAccounts(app=app, sessionstore=None)
InvenioAdmin(app)
app.register_blueprint(blueprint_accounts)
console = InvenioLoggingConsole(app)
fs = InvenioLoggingFS(app)
WekoAccounts(app)
app.app_context().push()


@app.before_request
def check_session_time():
    current_app.logger.info('first check session timeout')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
