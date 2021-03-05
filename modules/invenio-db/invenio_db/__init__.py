# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database management for Invenio.

First make sure you have Flask application with Click support (meaning
Flask 0.11+):

    >>> from flask import Flask
    >>> app = Flask('myapp')

Next, initialize your extension:

    >>> from invenio_db import InvenioDB
    >>> db = InvenioDB(app)

Command-line interface
~~~~~~~~~~~~~~~~~~~~~~
Invenio-DB installs the ``db`` command group on your application with the
following commands:

 * ``create`` - Create database tables.
 * ``drop`` - Drop database tables.
 * ``init`` - Initialize database.
 * ``destroy`` - Destroy database.

and ``alembic`` command group for managing upgrade recipes:

 * ``branches`` - Show branch points.
 * ``current`` - Show current revision.
 * ``downgrade`` - Run downgrade migrations.
 * ``heads`` - Show latest revisions.
 * ``log`` - Show revision log.
 * ``merge`` - Create merge revision.
 * ``mkdir`` - Make migration directory.
 * ``revision`` - Create new migration.
 * ``show`` - Show the given revisions.
 * ``stamp`` - Set current revision.
 * ``upgrade`` - Run upgrade migrations.

For more information about how to setup alembic revisions in your module,
please read the section about :doc:`alembic </alembic>`.

Models
~~~~~~

Database models are created by inheriting from the declarative base
``db.Model``:

.. code-block:: python

   # models.py
   from invenio_db import db

   class User(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       username = db.Column(db.String(80), unique=True)
       email = db.Column(db.String(120), unique=True)

Setuptools integration
~~~~~~~~~~~~~~~~~~~~~~

In order for the CLI commands to be aware of your models and upgrade recipies,
you must either import your models in the application factory, or better simply
specify the entry point item in ``invenio_db.models`` group. Invenio-DB then
takes care of loading the models automatically. Alembic configuration of
version locations is assembled from ``invenio_db.alembic`` entry point group.

.. code-block:: python

   # setup.py
   # ...
   setup(
       entry_points={
           'invenio_db.alembic': [
               'branch_name = mymodule:alembic',
           ],
           'invenio_db.models': [
               'mymodule = mymodule.models',
           ],
       },
   )

"""

from __future__ import absolute_import, print_function

from .ext import InvenioDB
from .shared import db
from .version import __version__

__all__ = (
    '__version__',
    'db',
    'InvenioDB',
)
