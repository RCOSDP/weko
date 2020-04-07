# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Minimal Flask application example.

SPHINX-START

First install weko-itemtypes-ui, setup the application and load
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

from flask import Flask
from flask_babelex import Babel
from invenio_db import InvenioDB, db
from invenio_i18n import InvenioI18N
from weko_records import WekoRecords

from weko_itemtypes_ui import WekoItemtypesUI

# Create Flask application
app = Flask(__name__)
app.config.update(
    ACCOUNTS_USE_CELERY=False,
    CELERY_ALWAYS_EAGER=True,
    CELERY_CACHE_BACKEND='memory',
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_RESULT_BACKEND='cache',
    MAIL_SUPPRESS_SEND=True,
    SECRET_KEY='CHANGE_ME',
    SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    WTF_CSRF_ENABLED=False,
    SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://invenio:dbpass123@localhost:5438/invenio',
)
Babel(app)
InvenioDB(app)
InvenioI18N(app)
WekoRecords(app)
WekoItemtypesUI(app)


@app.route('/')
def index():
    """Example index page route."""
    return 'Welcome to weko-itemtypes-ui'


if __file__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=1)
