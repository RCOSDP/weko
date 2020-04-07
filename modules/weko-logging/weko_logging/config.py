# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.


"""Configuration for WEKO-Logging.

Sentry can, in addition to the configuration variables listed, be further
configured with the folllowing configuration variables (see
`Raven <https://docs.sentry.io/clients/python/integrations/flask/#settings>`_
for further details):

- ``SENTRY_AUTO_LOG_STACKS``
- ``SENTRY_EXCLUDE_PATHS``
- ``SENTRY_INCLUDE_PATHS``
- ``SENTRY_MAX_LENGTH_LIST``
- ``SENTRY_MAX_LENGTH_STRING``
- ``SENTRY_NAME``
- ``SENTRY_PROCESSORS``
- ``SENTRY_RELEASE``
- ``SENTRY_SITE_NAME``
- ``SENTRY_TAGS``
- ``SENTRY_TRANSPORT``


.. note::

   Celery does not deal well with the threaded Sentry transport, so you should
   make sure that your **Celery workers** are configured with:

   .. code-block:: python

      SENTRY_TRANSPORT = 'raven.transport.http.HTTPTransport'
"""

# ----------
# FILESYSTEM
# ----------
WEKO_LOGGING_FS_LOGFILE = '{instance_path}/weko-logging.log'
"""Enable logging to the filesystem."""

WEKO_LOGGING_FS_PYWARNINGS = False
"""Enable logging of Python warnings to filesystem logging."""

WEKO_LOGGING_FS_WHEN = 'D'
"""Number of rotated log files to keep.

Set to a valid Python level: ``H``, ``D``.
H - Hours
D - Days
"""

WEKO_LOGGING_FS_INTERVAL = 1
"""Number of rotated log files to keep."""

WEKO_LOGGING_FS_BACKUPCOUNT = 31
"""Number of rotated log files to keep."""

WEKO_LOGGING_FS_LEVEL = 'ERROR'
"""Filesystem logging level.

Set to a valid Python logging level: ``CRITICAL``, ``ERROR``, ``WARNING``,
``INFO``, ``DEBUG``, or ``NOTSET``.
"""
