..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Configuration
=============

You can modify the default location of the instance folder and/or static folder
by setting the environment variables:

- ``INVENIO_INSTANCE_PATH`` (default: ``<sys.prefix>/var/instance/``)

- ``INVENIO_STATIC_FOLDER``  (default: ``<instance-path>/static/``)

Instance specific configuration is loaded from:

- ``<instance-path>/invenio.cfg``
- via environment variables prefixed with ``INVENIO_`` (e.g.
  ``INVENIO_SQLALCHEMY_DATABASE_URI``)

Templates are loaded from:

- ``<instance-path>/templates/``

.. automodule:: invenio_app.config
   :members:
