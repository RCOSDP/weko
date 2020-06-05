# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Celery application for Invenio flavours."""

from __future__ import absolute_import, print_function

from flask_celeryext import create_celery_app

from .factory import create_ui

celery = create_celery_app(create_ui(
    SENTRY_TRANSPORT='raven.transport.http.HTTPTransport',
    RATELIMIT_ENABLED=False,
))
"""Celery application for Invenio.

Overrides SENTRY_TRANSPORT wih synchronous HTTP transport since Celery does not
deal nicely with the default threaded transport.
"""

# Trigger an app log message upon import. This makes Sentry logging
# work with `get_task_logger(__name__)`.
celery.flask_app.logger.info('Created Celery app')
