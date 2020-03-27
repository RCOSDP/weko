# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Minimal Flask application example for development.

SPHINX-START

Initialization
--------------

Install requirements:

.. code-block:: console

   $ pip install -e .[all]
   $ cd examples
   $ ./app-setup.sh
   $ ./app-fixtures.sh

Run example development server:

.. code-block:: console

   $ FLASK_APP=app.py flask run --debugger -p 5000

Run example worker:

.. code-block:: console

   $ celery worker -A app.celery -l info --purge

.. note::

   You must have a Redis running on localhost.


Endpoints
---------

Administration interface is available on::

   http://localhost:5000/admin/

To access the admin interface the user needs to have superuser access rights.

.. code-block:: console

   $ flask access allow superuser-access user <inser_user_email>

REST API is available on::

   http://localhost:5000/files/

REST API
--------
Below are some example queries you can make to the REST API. Most queries will
be operating on a bucket, so let's first define a env variable:

.. code-block:: console

   $ B=11111111-1111-1111-1111-111111111111

Bucket operations
~~~~~~~~~~~~~~~~~

Create a bucket:

.. code-block:: console

   $ curl -X POST http://localhost:5000/files

List objects:

.. code-block:: console

   $ curl http://localhost:5000/files/$B

List object versions:

.. code-block:: console

   $ curl http://localhost:5000/files/$B?versions

List multipart uploads:

.. code-block:: console

   $ curl http://localhost:5000/files/$B?uploads

Check bucket existence:

.. code-block:: console

   $ curl -i -X HEAD http://localhost:5000/files/$B

Object operations
~~~~~~~~~~~~~~~~~

Download a file:

.. code-block:: console

   $ curl -i http://localhost:5000/files/$B/AUTHORS.rst

Upload a file:

.. code-block:: console

   $ curl -i -X PUT --data-binary @../INSTALL.rst \
     http://localhost:5000/files/$B/INSTALL.rst

Delete a file (creates a delete marker):

.. code-block:: console

   $ curl -i -X DELETE http://localhost:5000/files/$B/INSTALL.rst

Remove a specific version (removes file from disk):

.. code-block:: console

   $ curl -i -X DELETE http://localhost:5000/files/$B/INSTALL.rst?versionId=...

Multipart file upload
~~~~~~~~~~~~~~~~~~~~~

Create a multipart upload:

.. code-block:: console

   $ curl -i -X POST \
     "http://localhost:5000/files/$B/LICENSE?uploads&size=8&partSize=4"

List parts of a multipart upload:

.. code-block:: console

   $ curl http://localhost:5000/files/$B/LICENSE?uploadId=...

Upload parts:

.. code-block:: console

    $ echo -n "aaaa" | curl -i -X PUT --data-binary @- \
      "http://localhost:5000/files/$B/LICENSE?uploadId=...&partNumber=0"
    $ echo -n "bbbb" | curl -i -X PUT --data-binary @- \
      "http://localhost:5000/files/$B/LICENSE?uploadId=...&partNumber=1"

Complete a multipart upload (Celery must be running):

.. code-block:: console

   $ curl -i -X POST http://localhost:5000/files/$B/LICENSE?uploadId=...

Abort a multipart upload (Celery must be running):

.. code-block:: console

   $ curl -i -X DELETE http://localhost:5000/files/$B/LICENSE?uploadId=...

SPHINX-END
"""

from __future__ import absolute_import, print_function

import os
import shutil
from os import environ, makedirs
from os.path import dirname, exists, join

from flask import Flask, current_app
from flask_babelex import Babel
from flask_menu import Menu
from invenio_access import ActionSystemRoles, InvenioAccess, any_user
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_admin import InvenioAdmin
from invenio_celery import InvenioCelery
from invenio_db import InvenioDB, db
from invenio_rest import InvenioREST

from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, FileInstance, Location, \
    MultipartObject, ObjectVersion, Part
from invenio_files_rest.views import blueprint


def allow_all(*args, **kwargs):
    """Return permission that always allow an access.
    :returns: A object instance with a ``can()`` method.
    """
    return type('Allow', (), {'can': lambda self: True})()


# Create Flask application
app = Flask(__name__)
app.config.update(dict(
    BROKER_URL='redis://',
    CELERY_RESULT_BACKEND='redis://',
    DATADIR=join(dirname(__file__), 'data'),
    FILES_REST_MULTIPART_CHUNKSIZE_MIN=4,
    REST_ENABLE_CORS=True,
    SECRET_KEY='CHANGEME',
    SQLALCHEMY_ECHO=False,
    SQLALCHEMY_DATABASE_URI=os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
    ),
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    FILES_REST_PERMISSION_FACTORY=allow_all,
))

Babel(app)
Menu(app)
InvenioDB(app)
InvenioREST(app)
InvenioAdmin(app)
InvenioAccounts(app)
InvenioAccess(app)
InvenioFilesREST(app)

app.register_blueprint(accounts_blueprint)
app.register_blueprint(blueprint)

celery = InvenioCelery(app).celery


@app.cli.group()
def fixtures():
    """Command for working with test data."""


@fixtures.command()
def files():
    """Load files."""
    srcroot = dirname(dirname(__file__))
    d = current_app.config['DATADIR']
    if exists(d):
        shutil.rmtree(d)
    makedirs(d)

    # Clear data
    Part.query.delete()
    MultipartObject.query.delete()
    ObjectVersion.query.delete()
    Bucket.query.delete()
    FileInstance.query.delete()
    Location.query.delete()
    db.session.commit()

    # Create location
    loc = Location(name='local', uri=d, default=True)
    db.session.add(loc)
    db.session.commit()

    # Bucket 0
    b1 = Bucket.create(loc)
    b1.id = '00000000-0000-0000-0000-000000000000'
    for f in ['README.rst', 'LICENSE']:
        with open(join(srcroot, f), 'rb') as fp:
            ObjectVersion.create(b1, f, stream=fp)

    # Bucket 1
    b2 = Bucket.create(loc)
    b2.id = '11111111-1111-1111-1111-111111111111'
    k = 'AUTHORS.rst'
    with open(join(srcroot, 'CHANGES.rst'), 'rb') as fp:
        ObjectVersion.create(b2, k, stream=fp)
    with open(join(srcroot, 'AUTHORS.rst'), 'rb') as fp:
        ObjectVersion.create(b2, k, stream=fp)

    k = 'RELEASE-NOTES.rst'
    with open(join(srcroot, 'RELEASE-NOTES.rst'), 'rb') as fp:
        ObjectVersion.create(b2, k, stream=fp)
    with open(join(srcroot, 'CHANGES.rst'), 'rb') as fp:
        ObjectVersion.create(b2, k, stream=fp)
    ObjectVersion.delete(b2.id, k)

    # Bucket 2
    b2 = Bucket.create(loc)
    b2.id = '22222222-2222-2222-2222-222222222222'

    db.session.commit()
