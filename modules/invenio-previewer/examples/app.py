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
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

r"""Minimal Flask application example for development.

1. Create the database and the tables:

.. code-block:: console

   $ cd examples
   $ pip install -r requirements.txt
   $ flask -a app.py db init
   $ flask -a app.py db create


2. Create the database and the tables:

.. code-block:: console

   $ flask -a app.py users create info@inveniosoftware.org -a


3. Collect npm, requirements from registered bundles:

.. code-block:: console

   $ flask -a app.py npm


4. Install the npm packages:

.. code-block:: console

   $ cd static
   $ npm install
   $ cd ..


5. Copy the static files from the Python packages into the Flask
application's static folder:

.. code-block:: console

   $ flask -a app.py collect -v


6. Build the assets as they are defined in bundle.py.
This assumes that uglifyjs and r.js commands are available. To install
them, run `npm install -g uglifyjs requirejs`.

.. code-block:: console

   $ flask -a app.py assets build


7. Run the fixture CLI tool in order to populate the database with
example data:

.. code-block:: console

   $ flask -a app.py fixtures files


8. Run the test server:

.. code-block:: console

   $ flask -a app.py run


9. Login into the application. Open in a web browser
`http://localhost:5000/login/ and use the user previously created
(user: info@inveniosoftware.org).


10. Open a web browser and enter to the url
`http://localhost:5000/records/RECORD_PID/preview` where
`RECORD_ID` is a number between 1 and 10.


11. Open now a record that contains several files (The last record created).
By default, it is showing the first document, but you can set another file
using a query string like
`http://localhost:5000/records/6/preview?filename=csvfile.csv`
You can use (`csvfile.csv`, `markdown.md`, `pdffile.pdf`)
"""

from __future__ import absolute_import, print_function

import os
from uuid import uuid4

from flask import Flask
from flask_babelex import Babel
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB, db
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_i18n import InvenioI18N
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_records import InvenioRecords, Record
from invenio_records_ui import InvenioRecordsUI

from invenio_previewer import InvenioPreviewer

# Create Flask application
app = Flask(__name__)
app.config.update(
    SECRET_KEY='CHANGEME',
    SQLALCHEMY_DATABASE_URI=os.environ.get(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=True,
    RECORDS_UI_DEFAULT_PERMISSION_FACTORY=None,
    RECORDS_UI_ENDPOINTS=dict(
        recid=dict(
            pid_type='recid',
            route='/records/<pid_value>',
            template='invenio_records_ui/detail.html',
        ),
        recid_previewer=dict(
            pid_type='recid',
            route='/records/<pid_value>/preview',
            view_imp='invenio_previewer.views:preview',
        ),
    )
)
Babel(app)
InvenioI18N(app)
InvenioAccounts(app)
InvenioAccess(app)
InvenioDB(app)
InvenioAssets(app)
InvenioRecords(app)
InvenioFilesREST(app)
InvenioPreviewer(app)
InvenioRecordsUI(app)


@app.cli.group()
def fixtures():
    """Command for working with test data."""


def create_object(bucket, file_name, stream):
    """Object creation inside the bucket using the file and its content."""
    obj = ObjectVersion.create(bucket, file_name, stream=stream)
    rec_uuid = uuid4()
    provider = RecordIdProvider.create(object_type='rec', object_uuid=rec_uuid)
    data = {
        'pid_value': provider.pid.pid_value,
        'files': [
            {
                'uri': '/files/{0}/{1}'.format(str(bucket.id), file_name),
                'key': file_name,
                'size': obj.file.size,
                'bucket': str(bucket.id),
                'local': True
            }
        ]
    }
    Record.create(data, id_=rec_uuid)


@fixtures.command()
def files():
    """Load files."""
    data_path = os.path.join(os.path.dirname(__file__), 'data')

    # Create location
    loc = Location(name='local', uri=data_path, default=True)
    db.session.commit()

    # Bucket
    bucket = Bucket.create(loc)

    # Example files from the data folder
    example_files = (
        'markdown.md',
        'csvfile.csv',
        'zipfile.zip',
        'jsonfile.json',
        'xmlfile.xml',
        'notebook.ipynb',
        'jpgfile.jpg',
        'pngfile.png',
    )

    # Create single file records
    for f in example_files:
        with open(os.path.join(data_path, f), 'rb') as fp:
            create_object(bucket, f, fp)

    # Create a multi-file record
    rec_uuid = uuid4()
    provider = RecordIdProvider.create(object_type='rec', object_uuid=rec_uuid)
    data = {
        'pid_value': provider.pid.pid_value,
        'files': []
    }

    # Template to create different files
    template_file = {
        'uri': '/files/{0}/{1}',
        'key': '',
        'bucket': str(bucket.id),
        'local': True
    }

    for filename in example_files:
        file_data = template_file.copy()
        file_data['uri'] = file_data['uri'].format(str(bucket.id), filename)
        file_data['key'] = filename
        data['files'].append(file_data)

    Record.create(data, id_=rec_uuid)

    db.session.commit()
