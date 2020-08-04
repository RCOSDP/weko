..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Configuration
=============

The default values of configuration options are guessed based on installed
packages.

.. data:: SQLALCHEMY_DATABASE_URI

   The database URI that should be used for the connection. Defaults to
   ``'sqlite:///<instance_path>/<app.name>.db'``.

.. data:: SQLALCHEMY_ECHO

   Enables debug output containing database queries. Defaults to ``True``
   if application is in debug mode (``app.debug == True``).


.. data:: DB_VERSIONING

   Enables versioning support using SQLAlchemy-Continuum. Defaults to ``True``
   if ``sqlalchemy_continuum`` package is installed.


.. data:: DB_VERSIONING_USER_MODEL

   User class used by versioning manager. Defaults to ``'User'`` if
   ``invenio_accounts`` package is installed.

.. data:: ALEMBIC

   Dictionary containing general configuration for Flask-Alembic. It contains
   defaults for following keys:

   * ``'script_location'`` points to location of the migrations directory.
     It is **required** key and defaults to location of ``invenio_db.alembic``
     package resource.

   * ``'version_locations'`` lists location of all independent named branches
     specified by Invenio packages in ``invenio_db.alembic`` entry point
     group.


Please check following packages for further configuration options:

1. `Flask-SQLAlchemy <https://flask-sqlalchemy.readthedocs.io/en/stable/config/>`_
2. `Flask-Alembic <https://flask-alembic.readthedocs.io/en/stable/#configuration>`_
3. `SQLAlchemy-Continuum <https://sqlalchemy-continuum.readthedocs.io/en/latest/configuration.html>`_
