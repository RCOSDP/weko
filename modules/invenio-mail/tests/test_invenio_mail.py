# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from __future__ import absolute_import, print_function

import sys

from flask import Flask
from flask_mail import Message

from invenio_mail import InvenioMail

PY3 = sys.version_info[0] == 3

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO


def test_version():
    """Test version import."""
    from invenio_mail import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioMail(app)
    assert 'invenio-mail' in app.extensions

    app = Flask('testapp')
    ext = InvenioMail()
    assert 'invenio-mail' not in app.extensions
    ext.init_app(app)
    assert 'invenio-mail' in app.extensions


def test_print_email():
    """Test printing of email."""
    app = Flask('testapp')
    app.config.update(MAIL_SUPPRESS_SEND=True)

    output = StringIO()
    InvenioMail(app, stream=output)

    with app.app_context():
        msg = Message(
            'Test subject', sender='from@example.com',
            recipients=['to@example.com'], body='Test Body')
        app.extensions['mail'].send(msg)

    email = output.getvalue()
    output.close()

    sep = '\r\n' if PY3 else '\n'

    assert 'Subject: Test subject{0}'.format(sep) in email
    assert 'From: from@example.com{0}'.format(sep) in email
    assert 'To: to@example.com{0}'.format(sep) in email
    assert '{0}{0}Test Body'.format(sep) in email
