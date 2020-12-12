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

r"""Invenio module for previewing files.

Invenio-Previewer provides extensible file previewers for Invenio. It
integrates with Invenio-Records-UI via a custom view function. Currently the
module comes with viewers for the following files types:

- PDF (using PDF.js)
- ZIP
- CSV (using d3.js)
- Markdown (using Mistune library)
- XML and JSON (using Prism.js)
- Simple images (PNG, JPG, GIF)

Invenio-Previewer only provides the front-end layer for displaying previews
of files. Specifically Invenio-Previewer does not take care of generating
derived formats such thumbnails etc.

Initialization
--------------
First create a Flask application (Flask-CLI is not needed for Flask
version 1.0+):

>>> from flask import Flask
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

Configuration
~~~~~~~~~~~~~
Invenio-Previewer is enabled by adding a Records-UI endpoint with a custom
view function set to ``invenio_previewer.views:preview``:

>>> app.config.update(
...     SQLALCHEMY_TRACK_MODIFICATIONS=False,
...     RECORDS_UI_DEFAULT_PERMISSION_FACTORY=None,
...     RECORDS_UI_ENDPOINTS=dict(
...         recid=dict(
...             pid_type='recid',
...             route='/records/<pid_value>',
...             template='invenio_records_ui/detail.html',
...         ),
...         recid_previewer=dict(
...             pid_type='recid',
...             route='/records/<pid_value>/preview/<filename>',
...             view_imp='invenio_previewer.views:preview',
...             record_class='invenio_records_files.api:Record',
...         ),
...     )
... )

Here, we configure the URL route to ``/records/<pid_value>/preview``, but you
can set it to whatever you like. Records-UI takes care resolving
the URL to a record and check access control for the record.

Extensions
~~~~~~~~~~
Now that we have configured the Flask application, let's initialize all
dependent Invenio extensions:

>>> from flask_babelex import Babel
>>> from invenio_assets import InvenioAssets
>>> from invenio_db import InvenioDB, db
>>> from invenio_records import InvenioRecords
>>> from invenio_records_ui import InvenioRecordsUI
>>> from invenio_files_rest import InvenioFilesREST
>>> ext_babel = Babel(app)
>>> ext_assets = InvenioAssets(app)
>>> ext_db = InvenioDB(app)
>>> ext_records = InvenioRecords(app)
>>> ext_records_ui = InvenioRecordsUI(app)
>>> ext_files_rest = InvenioFilesREST(app)

The above modules provides the following features to Invenio-Previewer:

- Invenio-Assets: JavaScript/CSS bundling for interactive previewers.
- Invenio-Records-UI: Retrieval of record and access control.
- Invenio-Files-REST: Access to local files (required only if the previewer
  plugin needs access to the content of a file).

Lastly, initialize Invenio-Previewer and create an Flask application context:

>>> from invenio_previewer import InvenioPreviewer
>>> ext_previewer = InvenioPreviewer(app)

In order for the following examples to work, you need to work within an Flask
application context so let's push one:

>>> app.app_context().push()

Also, for the examples to work we need to create the database and tables
(note, in this example we use an in-memory SQLite database):

>>> from invenio_db import db
>>> db.create_all()

Previewing a file
-----------------
Invenio-Previewer looks into record's metadata to find which files can be
viewed, so first we need to create a record with a persistent identifier and
add a file into it.

Creating a record
~~~~~~~~~~~~~~~~~

Let's start by creating a persistent identifier:

>>> from uuid import uuid4
>>> from invenio_pidstore.providers.recordid import RecordIdProvider
>>> rec_uuid = uuid4()
>>> provider = RecordIdProvider.create(
...     object_type='rec', object_uuid=rec_uuid)

Also, let's create the record:

>>> from invenio_records_files.api import Record, RecordsBuckets
>>> data = {
...     'control_number': provider.pid.pid_value,
... }
>>> record = Record.create(data, id_=rec_uuid)
>>> db.session.commit()

Creating a file
~~~~~~~~~~~~~~~
Next, let's create an Invenio-Files-REST location + bucket and assign it to the
record:

>>> import tempfile
>>> from six import BytesIO
>>> from invenio_files_rest.models import Bucket, Location, \
...    ObjectVersion
>>> tmpdir = tempfile.mkdtemp()
>>> loc = Location(name='local', uri=tmpdir, default=True)
>>> bucket = Bucket.create(loc)
>>> rb = RecordsBuckets(record_id=record.id, bucket_id=bucket.id)
>>> db.session.add(rb)
>>> db.session.commit()

We can then add a file into the record:

>>> record.files['markdown.md'] = BytesIO(b'# Test MD')
>>> db.session.commit()

Previewing file
~~~~~~~~~~~~~~~

We should be able to see now the result HTML generated from the markdown file:

>>> with app.test_client() as client:
...     res = client.get('/records/1/preview/markdown.md')
>>> res.status_code
200

A lot is happening here so let's take it in steps:

1. Records-UI resolves ``/records/1/preview/markdown.md`` into a record and
   persistent identifier which is then passed to Invenio-Previewer.
2. Invenio-Previewer looks to the ``files`` key in the record and expect to
   find a list of dictionaries, with each dictionary representing a file
   (note: by default the first file in the list will be previewed).
3. Invenio-Previewer determines the file extensions and searchers for a
   preview plugin to handle the request.
4. The preview plugin now finally takes care of all rendering.


Bundled previewers
------------------
This module contains several previewers out-of-the-box:

- ``Markdown``: Previews a markdown file. It is based on python `mistune`
  library.

- ``JSON/XML``: Previews JSON and XML files. It pretty-prints the contents
  and applies syntax highlighting using the `Prism.js` library.
  You can also configure the maximum file size in order to avoid client and
  server freezes. By default it is set to 1MB.

- ``CSV`` - Previews `CSV` files but it can actually works
  with any other tabular data format in plain text based on the idea of
  separated values due to it is detecting the delimiter between the characters
  automatically. On the client side, the file is previewed using `d3.js`
  library.

- ``PDF`` - Previews a PDF file in your browser using `PDF.JS` library.

- ``Simple Images``: Previews simple images. Supported formats are JPG, PNG
  and GIF. There is also a configurable file size limit, which by default is
  set to 512KB.

- ``ZIP`` - Previews file tree inside the archive. You can specify a files
  limit to avoid a temporary lock in both of client and server side when you
  are dealing with large ZIP files. By default, this limit is set 1000 files.

- ``Default`` - This previewer is intended to be a fallback previewer to those
  cases when there is no previewer to deal with some file type. It is showing a
  simple message that the file cannot be previewed.

Local vs. remote files
~~~~~~~~~~~~~~~~~~~~~~
Some of the bundled previewers are only working with locally managed  files
(i.e. files stored in Invenio-Files-REST, which supports many different storage
backends). This is the case for JSON, XML, CSV, Markdown and ZIP previewers.
The PDF and Image previewer doesn't need to have the files stored locally.

Override default previewer
--------------------------
The default previewer for a file can be overridden in two ways:

1. By providing a ``previewer`` key in the file, with the name of the previewer
   to use. This works on a per-file basis.
2. By list the previewer plugin search order in ``PREVIEWER_PREFERENCES``. The
   first item in the list is the most prioritized previewer in case of
   collision.

Custom previewer
----------------
The implementation of a custom previewer is an easy process. You basically only
need to write two methods and declare the entry point and the priority of your
previewer.

Let's try to create a ``.txt.`` file previewer. We need to provide two methods
in a Python module: ``can_preview()`` and ``preview()`` and also a variable
specifying which extensions can preview: ``previewable_extensions`` .

1. ``can_preview()`` is called in order to check if a given file can be
   previewed and should return a boolean.
2. ``preview()`` is called to actually render the preview.
3. ``previewable_extensions`` is a list of string saying which files extensions
   can preview.

Both methods is passed a ``PreviewFile`` instance, which contains the extract
file dictionary, the record and the persistent identifier. ``PreviewFile`` also
provides a method which can be used to open the file, in case it is managed by
Invenio-Files-REST.

For our ``txt`` previewer, we can create a file with the following content:

>>> previewable_extensions = ['txt']
>>> def can_preview(file):
...     return file.file['uri'].endswith('.txt')
>>> def preview(file):
...     fp = file.open()
...     content = fp.read().decode('utf-8')
...     fp.close()
...     return content

Configuration:
Once we have our code, we should register our previewer in the previwer entry
point. So, go to your ``setup.py`` and create a new entry (If it doesn't exist)
to declare ``invenio_previewer.previewers`` entry points. Then, you should add
a new entry with specifying the python path of your module:
>>> 'invenio_previewer.previewers': [
>>>     'tex_previewer = myproject.modules.previewer.extensions.txt_previewer',
>>> ]

The configuration above made it is only making to our project to be aware of
the module but the previewer can not be used. As we said before, you need to
add it to ``PREVIEWER_PREFERENCES`` in the correct position. The first position
is going to be perfect in the case of this TXT previewer:
>>> PREVIEWER_PREVIEWERS_ORDER=
>>>     [
>>>         'invenio_previewer.extensions.csv_dthreejs',
>>>         'invenio_previewer.extensions.json_prismjs',
>>>         'invenio_previewer.extensions.xml_prismjs',
>>>         'invenio_previewer.extensions.simple_image',
>>>         'invenio_previewer.extensions.mistune',
>>>         'invenio_previewer.extensions.pdfjs',
>>>         'invenio_previewer.extensions.zip',
>>>         'invenio_previewer.extensions.default',
>>>     ]

Now, the previewer is ready to be used.

Bundles:
In the previously described previewer, we were returning a simple string as
response  but a real implementation should return a HTML. This HTML should
extends ``invenio_previewer/abstract_previewer.html`` in order to take
advantage of many presentation features.

But when you are defining a new template, maybe you are requiring some files
like javascript or style documents. For those cases, you need to create a
bundle. Check ``Invenio-Assets`` out to learn how to add them.
"""

from __future__ import absolute_import, print_function

from .ext import InvenioPreviewer
from .proxies import current_previewer
from .version import __version__

__all__ = ('__version__', 'current_previewer', 'InvenioPreviewer')
