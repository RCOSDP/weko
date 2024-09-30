..
    This file is part of Invenio.
    Copyright (C) 2015-2023 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 1.1.5 (released 2023-09-11)

- shared: removed 'text()' from cursor.execute for SQLite

Version 1.1.4 (released 2023-08-18)

- shared: fix sqlalchemy op.execute statements due to latest sqlalchemy-continuum

Version 1.1.3 (released 2023-08-17)

- alembic: fix sqlalchemy op.execute statements due to latest sqlalchemy-continuum

Version 1.1.2 (released 2023-05-23)

- fix db engine dependencies

Version 1.1.1 (released 2023-05-22)

- upgrade minimal python version
- code formatting
- force installing greenlet dependency
- upper pin alembic dependency version

Version 1.0.15 (released 2023-05-17)

- yanked due to mixed commits in the release

Version 1.1.0 (released 2023-04-06)

- yanked, because of an incompatibility with Flask-SQLAlchemy v3.

Version 1.0.14 (released 2022-03-30)

- Adds support for SQLAlchemy 1.4 and Flask v2.1.

Version 1.0.13 (released 2022-02-21)

- Changes alembic migrations to run a single migration in one transaction
  instead of all migrations in a single transaction.

Version 1.0.12 (released 2022-02-14)

- Fixes a deprecation warning.

Version 1.0.11 (released 2022-02-08)

- Fixed issue with alembic version locations introduced in v1.0.10 due to the
  importlib change.

Version 1.0.10 (released 2022-02-08)

- Adds a utility for creating an alembic test context to centrally manage
  fixes for alembic migration tests in other modules.

- Replaces pkg_resources with importlib

Version 1.0.9 (released 2021-03-18)

- Pins Flask-SQLAlchemy below 2.5 due to breaking changes. Perhaps to revisit when fixed.

Version 1.0.8 (released 2020-11-16)

- Pins SQLAlchemy to >=1.2.18 and <1.4 due to incompatibility between
  SQLAlchemy and SQLAlchemy-Utils.

Version 1.0.7 (released 2020-11-08)

- Hides password from output when running db init or db create.
- Disables MySQL 8 tests due to issue with Alembic

Version 1.0.6 (released 2020-10-02)

- Bump SQLAlchemy version to ``>=1.2.18`` to add support for PostgreSQL 12
- Integrate ``pytest-invenio`` and ``docker-services-cli`` for testing
- Support Python 3.8

Version 1.0.5 (released 2020-05-11)

- Deprecated Python versions lower than 3.6.0. Now supporting 3.6.0 and 3.7.0
- Use centrally managed Flask version (through Invenio-Base)
- Bumped SQLAlchemy version to ``>=1.1.0``
- SQLAlchemy-Utils set to ``<0.36`` due to breaking changes with MySQL
  (``VARCHAR`` length)
- Enriched documentation on DB session management
- Stop using example app

Version 1.0.4 (released 2019-07-29)

- Unpin sqlalchemy-continuum
- Added tests for postgresql 10

Version 1.0.3 (released 2019-02-22)

- Added handling in case of missing Sqlite db file.

Version 1.0.2 (released 2018-06-22)

- Pin SQLAlchemy-Continuum.

Version 1.0.1 (released 2018-05-16)

- Minor fixes in documenation links and the license file.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
