# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module that implements OAI-PMH server.

Invenio-OAIServer is exposing records via OAI-PMH protocol. The core part
is reponsible for managing OAI sets that are defined using queries.

OAIServer consists of:

- OAI-PMH 2.0 compatible endpoint.
- Persistent identifier minters, fetchers and providers.
- Backend for formatting Elasticsearch results.

Initialization
--------------

.. note::
   You need to have Elasticsearch and a message queue service (e.g. RabbitMQ)
   running and available on their default ports at 127.0.0.1.

First create a Flask application (Flask-CLI is not needed for Flask
version 1.0+):

>>> from flask import Flask
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
>>> app.config['CELERY_ALWAYS_EAGER'] = True
>>> if not hasattr(app, 'cli'):
...     from flask_cli import FlaskCLI
...     ext_cli = FlaskCLI(app)

There are several dependencies that should be initialized in order to make
OAIServer work correctly.

>>> from invenio_db import InvenioDB
>>> from invenio_indexer import InvenioIndexer
>>> from invenio_pidstore import InvenioPIDStore
>>> from invenio_records import InvenioRecords
>>> from invenio_search import InvenioSearch
>>> from flask_celeryext import FlaskCeleryExt
>>> ext_db = InvenioDB(app)
>>> ext_indexer = InvenioIndexer(app)
>>> ext_pidstore = InvenioPIDStore(app)
>>> ext_records = InvenioRecords(app)
>>> ext_search = InvenioSearch(app)
>>> ext_celery = FlaskCeleryExt(app)

Then you can initialize OAIServer like a normal Flask extension, however
you need to set following configuration options first:

>>> app.config['OAISERVER_RECORD_INDEX'] = 'marc21',
>>> app.config['OAISERVER_ID_PREFIX'] = 'oai:example:',
>>> from invenio_oaiserver import InvenioOAIServer
>>> ext_oaiserver = InvenioOAIServer(app)

Register the Flask Blueprint for OAIServer. If you use InvenioOAIServer as
part of the invenio-base setup, the Blueprint will be registered automatically
through an entry point.

>>> from invenio_oaiserver.views.server import blueprint
>>> app.register_blueprint(blueprint)

In order for the following examples to work, you need to work within an
Flask application context so let's push one:

>>> ctx = app.app_context()
>>> ctx.push()

Also, for the examples to work we need to create the database and tables (note,
in this example we use an in-memory SQLite database):

>>> from invenio_db import db
>>> db.create_all()

And create the indices on Elasticsearch.

>>> indices = list(ext_search.create(ignore=[400]))
>>> ext_search.flush_and_refresh('_all')

Creating OAI sets
-----------------
"A set is an optional construct for grouping records for the purpose of
selective harvesting" [OAISet]_. The easiest way to create new OAI set is
using database model.

>>> from invenio_oaiserver.models import OAISet
>>> oaiset = OAISet(spec='higgs', name='Higgs', description='...')
>>> oaiset.search_pattern = 'title:higgs'
>>> db.session.add(oaiset)
>>> db.session.commit()

The above set will group all records that contain word "higgs" in the title.

We can now see the set by using verb ``ListSets``:

>>> with app.test_client() as client:
...     res = client.get('/oai2d?verb=ListSets')
>>> res.status_code
200
>>> b'Higgs' in res.data
True

.. [OAISet] https://www.openarchives.org/OAI/openarchivesprotocol.html#Set

Data model
----------
Response serializer, indexer and search expect ``_oai`` key in record data
with following structure.

.. code-block:: text

    {
        "_oai": {
            "id": "oai:example:1",
            "sets": ["higgs", "demo"],
            "updated": "2012-07-04T15:00:00Z"
        }
    }

There **must** exist an ``id`` key with a non-null value otherwise the record
is not exposed via OAI-PHM interface (``listIdentifiers``, ``listRecords``).
The value of this field should be regitered in PID store. We provide default
:func:`~invenio_oaiserver.minters.oaiid_minter` that can register existing
value or mint new one by concatenating a configuration option
``OAISERVER_ID_PREFIX`` and record value from ``control_number`` field.

All values in ``sets`` must exist in ``spec`` column in ``oaiserver_set``
table or they will be removed when record updater is executed. The last
field ``updated`` contains ISO8601 datetime of the last record metadata
modification according to following rules for `selective harvesting`_.

.. _selective harvesting: https://www.openarchives.org/OAI/openarchivesprotocol.html#SelectiveHarvestingandDatestamps

XSL Stylesheet
--------------
OAI 2.0 results can be nicely presented to the user navigating to the OAI
Server by defining an XSL Stylesheet to transform XML into HTML.

You can configure the module to use a static XSL file or to fetch it from a
remote server.

To use a local XSL Stylesheet, place the file in a `static` folder, and set
the relative url in the config `OAISERVER_XSL_URL`. For example:

.. code-block:: python

    OAISERVER_XSL_URL = '/static/xsl/oai2.xsl'

To use a remote XSL Stylesheet, set the config variable to an absolute url:

.. code-block:: python

    OAISERVER_XSL_URL = 'https://www.mydomain.com/oai2.xsl'

Be aware of CORS restrictions when fetching content from remote servers.

You can obtain an already defined XSL Stylesheet for OAIS 2.0 on `EPrints
repository
<https://raw.githubusercontent.com/eprints/eprints/3.3/lib/static/oai2.xsl>`_
(GPLv3 licensed).
"""

from __future__ import absolute_import, print_function

from .ext import InvenioOAIServer
from .proxies import current_oaiserver
from .version import __version__

__all__ = ('__version__', 'InvenioOAIServer', 'current_oaiserver')
