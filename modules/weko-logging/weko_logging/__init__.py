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

"""Module providing logging capabilities.

WEKO-Logging is a core component of Weko3 responsible for configuring
the Flask application logger. The Flask application logger exposes the standard
Python logging interface for creating log records and installing predefined
handlers.

The following logger extensions exists:

- :class:`~weko_logging.fs.WekoLoggingFS`

Initialization
--------------
First make sure you have Flask application with Click support (meaning
Flask 0.11+):

>>> from flask import Flask
>>> app = Flask('myapp')

Next, initialize your logging extensions:

>>> from weko_logging.fs import WekoLoggingFS
>>> fs = WekoLoggingFS(app)

In order for the following examples to work, you need to work within an
Flask application context so let's push one:

>>> app.app_context().push()

Logging
-------
All application logging should happen via the Flask application logger to
ensure that you only have to configure one logger in order to route log
messages to your desired logging infrastructure.

In Invenio modules this is easily achieved by simply using the Flask current
application context:

>>> from flask import current_app
>>> current_app.logger.debug('Where am I?')
>>> current_app.logger.info('Hello world!')
>>> current_app.logger.warning('Be carefull with overlogging.')
>>> current_app.logger.error('Connection could not be initialized.')
>>> current_app.logger.exception('You should not divide by zero!')

Note that ``logger.exception()`` will automatically include the exception
stacktrace in the log record, which each log handler may decide to include or
not in its output.

You may also manually include exception information in the logger using the
``exc_info`` keyword argument:

>>> current_app.logger.critical("My message", exc_info=1)

Warnings
--------
Warnings are useful to alert developers and system administrators about
possible problems, e.g. usage of obsolete modules, deprecated APIs etc.

By default warnings are only sent to the console when the Flask application
is in debug mode. This can however be changed via the configuration variables:
:data:`weko_logging.config.WEKO_LOGGING_FS_PYWARNINGS`

>>> import warnings
>>> warnings.warn('This feature is deprecated.', PendingDeprecationWarning)

For more information about logging please see:

 * http://flask.pocoo.org/docs/0.11/quickstart/#logging
 * https://docs.python.org/3/library/logging.html
"""

from .version import __version__

__all__ = ("__version__",)
