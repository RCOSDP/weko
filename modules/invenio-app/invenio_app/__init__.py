# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""WSGI, Celery and CLI applications for Invenio flavours.

Invenio-App provides the default Flask, WSGI, Celery and CLI applications which
is needed in order to run Invenio. All which is needed to run your Inveno
instance is to provide a base configuration should via the
``invenio_config.module`` entry point.

Setting up your instance
------------------------
Your base configuration e.g. defines the default language, name of your site as
well as the data model you are using. Usually this base configuration is put in
Python module inside a package. For instance like this (assuming your instance
is called ``mysite``)

.. code-block:: python

    # mysite/config.py

    BABEL_DEFAULT_LANGUAGE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'Europe/Zurich'
    # ...

In order to tell the Invenio-App applications to load your base module, you
should set the config module import path in the ``invenio_config.module`` entry
point group like the example below:

.. code-block:: python

    # setup.py
    setup(
        # ...
        entry_points={
            'invenio_config.module': [
                'mysite = mysite.config',
            ],
        }
    )

The entry point ``'mysite = mysite.config'`` defines an entry point named
``mysite`` pointing to the Python module ``mysite.config`` (i.e. the config
module above).

After you edited setup.py, you should always remember to install your Python
package again, as otherwise the newly added entry points won't be picked up.

Applications
------------

CLI
~~~
The command-line interface application is named ``invenio`` and you use it to
e.g. run a development server or initialize the database:

.. code-block:: console

    $ invenio --help
    Usage: invenio [OPTIONS] COMMAND [ARGS]...

      Command Line Interface for Invenio.

    ...

Celery
~~~~~~
In order to start a Celery worker for Invenio, you need to point Celery to the
Invenio Celery application (``invenio_app.celery``) in the following manner:

.. code-block:: console

    $ celery worker --app invenio_app.celery --loglevel INFO

WSGI
~~~~
Python web applications are usually run by a WSGI server such as Gunicorn,
UWSGI or mod_wsgi for Apache. Similar to Celery, you need to point the WSGI
servers to the Invenio WSGI application.

Here is e.g. an example with `Gunicorn <http://gunicorn.org>`_:

.. code-block:: console

    $ pip install gunicorn
    $ gunicorn invenio_app.wsgi

Invenio-App provides three different WSGI applications depending on your needs:

- ``invenio_app.wsgi``: Combined UI + REST API application with the REST API
  mounted under ``/api``.
- ``invenio_app.wsgi_ui``: UI-only application.
- ``invenio_app.wsgi_rest``: REST API-only application.

The individual UI and REST API applications are useful if you want to run
the UI and API on different servers or domains (e.g. ``www.example.org`` and
``api.example.org``), whereas the combined application is useful if you want to
run everything on the same server (e.g. ``www.example.org`` and
``www.example.org/api/``).

Deployment
----------
Deploying the applications in a production environment among other things
involve:

- daemonizing the applications
- setting instance specific configuration (e.g. database hostname)
- securing your instance

Daemonizing the applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In a production system you would usually need to daemonize the WSGI and Celery
application. A full guide on doing this is outside the scope of this
documentation, but usually it involves setting up e.g.
`Supervisord <http://supervisord.org>`_ or another process management tool to
manage the automatic starting/stopping ot the application.

For a full guide on how to deploy Invenio, please see the general
`Invenio documentation <http://invenio.readthedocs.io>`_.

Instance configuration
~~~~~~~~~~~~~~~~~~~~~~
The instance configuration defines e.g. hostnames of your database server and
other values which change depending on where you are running the applications
(e.g. local development machine vs. production system). In comparison the base
configuration is the same no matter where you run the application (e.g. site
name).

The instance configuration can be provided either in
``<instance-path>/invenio.cfg`` or via environment variables prefixed with
``INVENIO_``, e.g.:

.. code-block:: console

   $ export INVENIO_SQLALCHEMY_DATABASE_URI = ...

The instance path is defined by the environment variable
``INVENIO_INSTANCE_PATH`` or if not set defaults to
``<sys.prefix>/var/instance/`` where <sys.prefix> is your Python root prefix
(e.g. ``/usr/``)

Securing your instance
~~~~~~~~~~~~~~~~~~~~~~
The Invenio `documentation <https://invenio.readthedocs.io/en/latest/
deployment/securing-your-instance.html>`_ explains in details how to secure
an Invenio instance. It is important to note that if you deploy your
Invenio instance with at least one reverse proxy in front of it,
then you will have to set the configuration variable `WSGI_PROXIES
<https://invenio.readthedocs.io/en/latest/deployment/
securing-your-instance.html#number-of-proxies>`_
accordingly to correctly handle the `X-Forwarded-*` headers.

Templates and static files
~~~~~~~~~~~~~~~~~~~~~~~~~~
You can add templates and static files in the following folders respectively:

- ``<instance-path>/templates/``
- ``<instance-path>/static/``

This should only be done for small number of templates/files, as it is usually
better to provide them via an installabled Python package. Do take care not
to overwrite any existing Invenio files.
"""

from __future__ import absolute_import, print_function

from .ext import InvenioApp
from .version import __version__

__all__ = ('__version__', 'InvenioApp', )
