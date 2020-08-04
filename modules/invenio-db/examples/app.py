# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Simple example application for Invenio-DB package.

SPHINX-START

Setup the application:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ export FLASK_APP=app.py
   $ flask db init
   $ flask db create

Teardown the application:

.. code-block:: console

   $ flask db drop --yes-i-know

SPHINX-END
"""

import os

from flask import Flask

from invenio_db import InvenioDB

app = Flask('demo')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
)
InvenioDB(app)
