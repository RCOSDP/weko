..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Alembic for Invenio
===================

Alembic is a database migration library used with SQLAlchemy ORM. Invenio works with the Flask-Alembic library, its documentation can be found here: http://flask-alembic.readthedocs.io/en/latest/

Invenio-DB fully supports alembic and each Invenio module having a database model is also expected to provide the corresponding alembic revisions.
Alembic migrations do not work with SQLite.

Adding alembic support to existing modules
------------------------------------------

The following procedures assume ``invenio_foo`` is the name of the module for which you are adding alembic support.

The first step would be to add the entrypoint ``invenio_db.alembic`` in your ``invenio_foo`` setup.py as follows:

.. code-block:: python

    setup(
        ...
        entry_points={
            ...
            'invenio_db.alembic': [
                'invenio_foo = invenio_foo:alembic',
            ]
    })

This will register the ``invenio_foo/alembic`` directory in alembic's ``version_locations``.

Each module should create a branch for its revisions. In order to create a new branch, and in consequence the first revision, one should run:

.. code-block:: console

   $ invenio alembic revision "Create foo branch." -b invenio_foo -p <parent-revision> -d <dependencies> --empty

| -b  sets the branch label (conventionally the name of the module)
| -p  sets the parent revision, as default all branches should root from the revision ``dbdbc1b19cf2`` in invenio-db
| -d  sets the dependencies if they exist. For example when there is a foreign key pointing to the table of another invenio module, we need to make sure that table exists before applying this revision, so we add the necessary revision tag as a dependency.

The second revision typically has the message "Create foo tables." and will create the tables defined in the models. This can be created following the procedure below.

Creating a new revision
-----------------------

After making changes to the models of a module, we need to create a new alembic revision so we are able to apply these changes in the DB during a migration. Firstly, to make sure that the DB is up to date we apply any pending revisions with:

.. code-block:: console

    $ invenio alembic upgrade heads

and now we can create the new revision with:

.. code-block:: console

    $ invenio alembic revision "Revision message." --path ``invenio_foo/alembic``

A short message describing the changes is required and the path parameter should point to the alembic directory of the module. If the path is not given the new revision will be placed in the invenio_db/alembic directory and should be moved.

Show current state
------------------

To see the list of revisions in the order they will be applied, run:

.. code-block:: console

    $ invenio alembic log


The list of heads for all branches is given by:

.. code-block:: console

    $ invenio alembic heads

in this list, revisions will be labeled as ``(head)`` or ``(effective head)``. The difference being that effective heads are not shown in the ``alembic_version`` table in your database. As they are dependencies of other branches, they will be overwritten. ``alembic_version`` is a table created by alembic to keep the current revision state.

The list of the revisions that have been applied to the current database can be seen with:

.. code-block:: console

    $ invenio alembic current

Enabling alembic migrations in existing invenio instances
---------------------------------------------------------

In order to integrate alembic when there is already a DB in place, we have to create an ``alembic_version`` table stamped with the revisions matching the current state of the DB:

.. code-block:: console

    $ invenio alembic stamp

Assuming that there have been no changes in the DB, and the models match the alembic revisions, alembic upgrades and downgrades will be working now.

Note that if there are any unnamed constraints, they will get the default names from the DB which can be different from the ones in the alembic revisions.

Naming Constraints
------------------

In http://alembic.zzzcomputing.com/en/latest/naming.html, the need for naming constraints in the models is explained. In invenio-db the '35c1075e6360' revision applies the naming convention for invenio. If models contain constraints that are unnamed an ``InvalidRequestError`` will be raised.

The naming convention rules are:

+---------------+----------------------------------------------------------------+
| index         |  'ix_%(column_0_label)s'                                       |
+---------------+----------------------------------------------------------------+
| unique        |  'uq_%(table_name)s_%(column_0_name)s'                         |
+---------------+----------------------------------------------------------------+
| check         |  'ck_%(table_name)s_%(constraint_name)s'                       |
+---------------+----------------------------------------------------------------+
| foreign key   |  'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s' |
+---------------+----------------------------------------------------------------+
| primary key   |  'pk_%(table_name)s'                                           |
+---------------+----------------------------------------------------------------+

The constraints that produce a name longer that 64 characters will have to be named explicitly to a truncated form.

Testing revisions
-----------------

When initially creating alembic revisions one has to provide a test case for them.

The test for the created revisions starts from an empty DB, upgrades to the last branch revision and then downgrades to the base. We can check that there are no discrepancies in the state of the DB between the revisions and the models, by asserting that alembic.compare_metadata() returns an empty list. An example can be found here: `test_app.py#L130 <https://github.com/inveniosoftware/invenio-oauthclient/blob/d46de4d5e8269395b69230694ba073af88406404/tests/test_app.py#L130>`_
