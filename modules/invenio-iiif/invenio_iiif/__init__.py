# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to serve images complying with IIIF standard.

Invenio-IIIF integrates
`Invenio-Records-Files <https://invenio-records-files.rtfd.io>`_ with
`Flask-IIIF <https://flask-iiif.rtfd.io>`_ to provide an endpoint for serving
images complying with the `International Image Interoperability Framework
(IIIF) <https://iiif.io/>`_ API standards.

Invenio-IIIF registers the REST API endpoint provided by Flask-IIIF in the
Invenio instance through entry points. On each image request, it delegates
authorization check and file retrieval to
`Invenio-Files-REST <https://invenio-files-rest.rtfd.io>`_ and it serves the
image after adaptation by Flask-IIIF.

Basics
------

Preview
~~~~~~~

Invenio-IIIF can be used in a combination with
`Invenio-Previewer <https://invenio-previewer.rtfd.io>`_ to preview images.
It provides an extension to preview the most common image formats and it is
exposed via the entry point named ``iiif_image``.

The template used to render the image can be configured with the configuration
``IIIF_PREVIEW_TEMPLATE``.

To use it with an existing Invenio instance you should update your
``PREVIEWER_PREFERENCE`` configuration by adding ``iiif_image`` to the list of
available previewers with the desired precedence order. For example:

.. code-block:: python

    PREVIEWER_PREFERENCE = [
        'iiif_image',
        'json_prismjs',
        'xml_prismjs',
        'pdfjs',
        'zip',
    ]

Caching
~~~~~~~

Image caching is provided by ``Flask-IIIF``. You can change cache expiration
by setting the ``IIIF_CACHE_TIME``.

.. code-block:: python

    # 60 seconds * 60 (1 hour) * 24 (1 day)
    IIIF_CACHE_TIME = 60 * 60 * 24

By default ``Flask-IIIF`` caches images in memory. You can cache images on
Redis by using the available ``ImageRedisCache`` handler (providing Redis URL)
or point to your own custom handler by setting it in ``IIIF_CACHE_HANDLER``.

.. code-block:: python

    # Cache handler
    IIIF_CACHE_HANDLER = 'flask_iiif.cache.redis:ImageRedisCache'

    # Redis URL
    IIIF_CACHE_REDIS_URL = 'redis://localhost:6379/0'


PDF cover
~~~~~~~~~

When the retrieved file is a PDF and with ImageMagick/Wand installed in your
environment (see :ref:`install` documentation), then a cover image with the
first page of the PDF file can be generated and served it as preview.

Authorization
~~~~~~~~~~~~~

Permissions to retrieve the requested images are delegated to
`Invenio-Files-REST <https://invenio-files-rest.rtfd.io>`_. At each request,
authorization is checked to ensure that the user has sufficient privileges.

Thumbnails
~~~~~~~~~~

The module can pre-cache thumbnails of requested images. It provides a celery
task that will fetch a given image and resize it to create a thumbnail. It is
then cached so it can be served efficiently.

.. code-block:: python

    from invenio_iiif.tasks import create_thumbnail
    create_thumbnail(image_key, '250')


Initialization
--------------

First create a Flask application:

>>> from flask import Flask
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

Then, you can define the IIIF API prefix by setting the Invenio configuration
``IIIF_UI_URL``.

>>> app.config.update(IIIF_UI_URL='/iiif-demo')

The example below will demonstrate how Invenio-IIIF works with a simple image.
First, initialize the needed Invenio extensions:

>>> from invenio_db import InvenioDB, db
>>> from invenio_files_rest import InvenioFilesREST
>>> ext_db = InvenioDB(app)
>>> ext_files_rest = InvenioFilesREST(app)
>>> app.app_context().push()
>>> db.create_all()

Add sample images
~~~~~~~~~~~~~~~~~

To be able to add the files to Invenio, let's create a default location first:

>>> import tempfile
>>> tmpdir = tempfile.mkdtemp()
>>> from invenio_files_rest.models import Location
>>> loc = Location(name='local', uri=tmpdir, default=True)
>>> db.session.add(loc)
>>> db.session.commit()

And a bucket with the previously created location:

>>> from invenio_files_rest.models import Bucket
>>> b1 = Bucket.create(loc)

Now, add a few sample images:

>>> import os
>>> from invenio_files_rest.models import ObjectVersion
>>> demo_files_path = 'examples/demo_files'
>>> demo_files = (
...     'img.jpg',
...     'img.png')
>>> for f in demo_files:
...     with open(os.path.join(demo_files_path, f), 'rb') as fp:
...         img = ObjectVersion.create(b1, f, stream=fp)
>>> db.session.commit()

Serving an image
----------------

While Flask-IIIF requires the UUID of the image to retrieve as part of the URL,
Invenio needs the bucket id, version id and the key of the file so that it can
be retrieved via `Invenio-Files-REST <https://invenio-files-rest.rtfd.io>`_.
Invenio-IIIF provides an utility to prepare such URLs, e.g.
``/v2/<uuid>/<path>``, and convert the ``uuid`` parameter to a concatenation of
``<bucket_id>:<version_id>:<key>``.

Given a previously created image object:

>>> img_obj = ObjectVersion.get_versions(bucket=b1,
...                                      key=demo_files[1]).first()

you can create the corresponding IIIF URL:

>>> from invenio_iiif.utils import ui_iiif_image_url
>>> image_url = ui_iiif_image_url(
...       obj=img_obj, version='v2', region='full', size='full', rotation=0,
...       quality='default', image_format='png')

The result will be
``/iiif-demov2/<bucket_id>:<version_id>:img.png/full/full/0/default.png``
"""

from __future__ import absolute_import, print_function

from .ext import InvenioIIIF, InvenioIIIFAPI
from .version import __version__

__all__ = ('__version__', 'InvenioIIIF')
