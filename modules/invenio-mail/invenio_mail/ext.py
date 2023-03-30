# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio mail module."""

from __future__ import absolute_import, print_function

import sys
import threading

from flask_mail import Mail, email_dispatched

from . import config
from .views import blueprint


def print_email(message, app):
    """Print mail to stream.

    Signal handler for email_dispatched signal. Prints by default the output
    to the stream specified in the constructor of InvenioMail.

    :param message: Message object.
    :param app: Flask application object.
    """
    invenio_mail = app.extensions['invenio-mail']
    with invenio_mail._lock:
        invenio_mail.stream.write(
            '{0}\n{1}\n'.format(message.as_string(), '-' * 79))
        invenio_mail.stream.flush()


class InvenioMail(object):
    """Invenio-Mail extension."""

    def __init__(self, app=None, stream=None):
        """Extension initialization.

        Mails are only printed to the stream if ``MAIL_SUPPRESS_SEND`` is
        ``True``.

        :param app: Flask application object.
        :param stream: Stream to print emails to. Defaults to ``sys.stdout``.
        """
        self.stream = stream or sys.stdout
        self._lock = threading.RLock()
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        The initialization will:

         * Set default values for the configuration variables.
         * Initialise the Flask mail extension.
         * Configure the extension to avoid the email sending in case of debug
           or ``MAIL_SUPPRESS_SEND`` config variable set. In this case, the
           email will be written in the stream configured in the extension.

        :param app: Flask application object.
        """
        self.init_config(app)
        if 'mail' not in app.extensions:
            Mail(app)
        if app.config.get('MAIL_SUPPRESS_SEND', False) or app.debug:
            email_dispatched.connect(print_email)
        app.register_blueprint(blueprint)
        app.extensions['invenio-mail'] = self

    @staticmethod
    def init_config(app):
        """Initialize configuration.

        :param app: Flask application object.
        """
        app.config.setdefault('MAIL_DEBUG', app.debug)
        app.config.setdefault('MAIL_SUPPRESS_SEND', app.debug or app.testing)
        for k in dir(config):
            if k.startswith('INVENIO_MAIL_'):
                app.config.setdefault(k, getattr(config, k))

