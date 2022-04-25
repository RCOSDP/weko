# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.


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
WEKO_LOGGING_FS_LOGFILE = "{instance_path}/weko-logging.log"
"""Enable logging to the filesystem."""

WEKO_LOGGING_FS_PYWARNINGS = None
"""Enable logging of Python warnings to filesystem logging."""

WEKO_LOGGING_FS_WHEN = "D"
"""Number of rotated log files to keep.

Set to a valid Python level: ``H``, ``D``.
H - Hours
D - Days
"""

WEKO_LOGGING_FS_INTERVAL = 1
"""Number of rotated log files to keep."""

WEKO_LOGGING_FS_BACKUPCOUNT = 31
"""Number of rotated log files to keep."""

WEKO_LOGGING_FS_LEVEL = "ERROR"
"""Filesystem logging level.

Set to a valid Python logging level: ``CRITICAL``, ``ERROR``, ``WARNING``,
``INFO``, ``DEBUG``, or ``NOTSET``.
"""
