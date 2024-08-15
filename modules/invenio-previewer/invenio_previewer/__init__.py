# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

r"""Invenio module for previewing files.

Invenio-Previewer provides extensible file previewers for Invenio. It can be
easily integrated with
`Invenio-Records-UI <https://invenio-records-ui.rtfd.io>`_ to serve the file
preview under a simple URL path like ``/records/<pid_value>/preview``.

It includes previewers for the following file types:

- PDF (using PDF.js)
- ZIP
- CSV (using d3.js)
- Markdown (using Mistune library)
- XML and JSON (using Prism.js)
- Simple images (PNG, JPG, GIF)
- Jupyter Notebooks

Invenio-Previewer only provides the front-end layer for displaying previews
of files. Specifically, Invenio-Previewer does not take care of generating
derived formats such thumbnails etc. This could be done by
`Invenio-IIIF <https://invenio-iiif.readthedocs.io>`_.

Initialization
--------------

First create a Flask application (Flask-CLI is not needed for Flask
version 1.0+):

>>> from flask import Flask
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

Configuration
~~~~~~~~~~~~~

Invenio-Previewer is enabled by adding a
:py:data:`invenio_records_ui.config.RECORDS_UI_ENDPOINTS`
endpoint with a custom view function set to
:py:data:`invenio_previewer.views.preview`

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
the URL to a record and checks access control for the record's file.

Extensions
~~~~~~~~~~

Now that we have configured the Flask application, let's initialize all
dependent Invenio extensions:

>>> from invenio_i18n import Babel
>>> from invenio_assets import InvenioAssets
>>> from invenio_db import InvenioDB, db
>>> from invenio_records import InvenioRecords
>>> from invenio_records_ui import InvenioRecordsUI
>>> from invenio_files_rest import InvenioFilesREST
>>> from invenio_records_ui.views import create_blueprint_from_app
>>> ext_babel = Babel(app)
>>> ext_assets = InvenioAssets(app)
>>> ext_db = InvenioDB(app)
>>> ext_records = InvenioRecords(app)
>>> ext_records_ui = InvenioRecordsUI(app)
>>> ext_files_rest = InvenioFilesREST(app)
>>> ext_blueprints = app.register_blueprint(create_blueprint_from_app(app))

The above modules provide the following features to Invenio-Previewer:

- `Invenio-Assets <https://invenio-assets.rtfd.io/>`_: JavaScript/CSS bundling
  for interactive previewers.
- `Invenio-Records-UI <https://invenio-records-ui.rtfd.io>`_: Retrieval of
  record and access control.
- `Invenio-Files-REST <https://invenio-files-rest.rtfd.io/>`_: Access to local
  files (required only if the previewer plugin needs access to the content of a
  file).

Lastly, initialize Invenio-Previewer:

>>> from invenio_previewer import InvenioPreviewer
>>> ext_previewer = InvenioPreviewer(app)

In order for the following examples to work, you need to work within a Flask
application context. Let's push one:

>>> app.app_context().push()

Also, for the examples to work we need to create the database and tables
(note, in this example we use an in-memory SQLite database):

>>> from invenio_db import db
>>> db.create_all()

Previewing files
----------------

Invenio-Previewer looks into record's metadata to find which files can be
previewed. First, we need to create a record and attach a file to it.

Creating a record
~~~~~~~~~~~~~~~~~

When creating a record, by default a bucket is created and associated to the
record. Therefore, before creating the record, we need to initialize a
default location:

>>> import tempfile
>>> from six import BytesIO
>>> from invenio_files_rest.models import Bucket, Location, \
...    ObjectVersion
>>> from invenio_records_files.api import RecordsBuckets
>>> tmpdir = tempfile.mkdtemp()
>>> loc = Location(name='local', uri=tmpdir, default=True)
>>> db.session.add(loc)
>>> db.session.commit()

Now we can create the record and its persistent identifier:

>>> from uuid import uuid4
>>> from invenio_pidstore.providers.recordid import RecordIdProvider
>>> rec_uuid = uuid4()
>>> provider = RecordIdProvider.create(
...     object_type='rec', object_uuid=rec_uuid)
>>> from invenio_records_files.api import Record
>>> data = {
...     'pid_value': provider.pid.pid_value,
... }
>>> record = Record.create(data, id_=rec_uuid)
>>> db.session.commit()

Adding files
~~~~~~~~~~~~

We can then add a few demo files into the record:

>>> import os
>>> demo_files_path = 'examples/demo_files'
>>> demo_files = (
...     'markdown.md',
...     'csvfile.csv',
...     'zipfile.zip',
...     'jsonfile.json',
...     'xmlfile.xml',
...     'notebook.ipynb',
...     'jpgfile.jpg',
...     'pngfile.png',
... )

>>> for f in demo_files:
...     with open(os.path.join(demo_files_path, f), 'rb') as fp:
...         record.files[f] = fp

>>> record.files.flush()
>>> _ = record.commit()
>>> db.session.commit()

Previewing a file
~~~~~~~~~~~~~~~~~

Let's try to preview the MarkDown file. What we expect is that the previewer
will be able to convert the MarkDown to HTML on the fly and we will see a nice
MarkDown preview:

>>> with app.test_client() as client:
...     res = client.get('/records/1/preview/markdown.md')

Here a more detailed explanation:

1. When calling the url ``/records/1/preview/markdown.md``, Invenio-Records-UI
   resolves the record from the PID 1 and it passes it to Invenio-Previewer.
2. Invenio-Previewer retrieves the file object by the filename ``markdown.md``
   using the ``invenio_previewer.ext.record_file_factory`` property
   (implemented by
   `Invenio-Records-Files <https://invenio-records-files.rtfd.io>`_ if
   installed).
3. With the file object, Invenio-Previewer iterates the list of configured
   previewers until it finds the first that is able to preview the file.
4. The preview plugin finally takes care of rendering the file.


Bundled previewers
------------------

This module contains several previewers out-of-the-box:

- ``Markdown``: Previews a markdown file. It is based on python
  `mistune <http://mistune.readthedocs.io>`_ library.

- ``JSON/XML``: Previews JSON and XML files. It pretty-prints the contents
  and applies syntax highlighting using the `Prism.js <https://prismjs.com>`_
  library. You can also configure the maximum file size in order to avoid
  client and server freezes. By default it is set to 1MB.

- ``CSV`` - Previews `CSV` files but it can actually work
  with any other tabular data format in plain text based on the idea of
  separated values due to it is detecting the delimiter between the characters
  automatically. On the client side, the file is previewed using
  `d3.js <https://d3js.org>`_ library.

- ``PDF`` - Previews a PDF file in your browser using
  `PDF.js <https://mozilla.github.io/pdf.js/>`_ library.

- ``Simple Images`` - Previews simple images. Supported formats are JPG, PNG
  and GIF. There is also a configurable file size limit, which by default is
  set to 512KB.

- ``ZIP`` - Previews file tree inside the archive. You can specify a files
  limit to avoid a temporary lock in both of client and server side when you
  are dealing with large ZIP files. By default, this limit is set 1000 files.

- ``Jupyter Notebook`` - Previews a Jupyter Notebook in your browser using
  `Jupyter notebook <https://jupyter.org>`_ python converter.

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

1. By providing a ``previewer`` key in the file object, with the name of the
   previewer to use. This works on a per-file basis.

   .. code-block:: python

      fileobj['previewer'] = 'zip'

2. By listing the previewer plugin search order in ``PREVIEWER_PREFERENCES``.
   The first item in the list is the most prioritized previewer in case of
   collision.

Custom previewer
----------------

The implementation of a custom previewer is an easy process. You need to
implement the preview function, declare the previewer in the related entry
points and define its priority.

Let's try to create a ``txt`` file previewer. We need to implement:

1. ``can_preview()`` method: called in order to check if a given file can be
   previewed and should return a boolean.
2. ``preview()`` method: called to render the preview.
3. ``previewable_extensions`` property: string list of previewer's supported
   file extensions.

Here an example code:

>>> class TxtPreviewer(object):
...     previewable_extensions = ['txt']
...     def can_preview(file):
...         return file.file['uri'].endswith('.txt')
...     def preview(file):
...         with file.open() as fp:
...             content = fp.read().decode('utf-8')
...         return content
>>> txt_previewer = TxtPreviewer()

Once we have our code, we have to register the previewer in the previewer entry
points:

>>> entry_points = {
...   'invenio_previewer.previewers': [
...     'tex_previewer = \
...         myproject.modules.previewer.extensions.txt_previewer',
...   ]}

Now define the priority for all previewers by adding the newly created
``txt_previewer`` to the 1st position, so it has the highest priority:

>>> PREVIEWER_PREVIEWERS_ORDER = [
...     'invenio_previewer.extensions.txt_previewer',
...     'invenio_previewer.extensions.csv_papaparsejs',
...     'invenio_previewer.extensions.json_prismjs',
...     'invenio_previewer.extensions.xml_prismjs',
...     'invenio_previewer.extensions.simple_image',
...     'invenio_previewer.extensions.mistune',
...     'invenio_previewer.extensions.pdfjs',
...     'invenio_previewer.extensions.zip',
...     'invenio_previewer.extensions.default',
... ]
"""

from .ext import InvenioPreviewer
from .proxies import current_previewer

__version__ = "2.2.1"

__all__ = ("__version__", "current_previewer", "InvenioPreviewer")
