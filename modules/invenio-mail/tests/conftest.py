# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile
from datetime import datetime

import pytest
from flask import Blueprint, Flask
from flask_admin import Admin
from flask_celeryext import FlaskCeleryExt
from invenio_db import InvenioDB, db
from six import StringIO
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_mail import InvenioMail, config
from invenio_mail.admin import mail_adminview
from invenio_mail.models import MailConfig


@pytest.yield_fixture()
def email_admin_app():
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    base_app = Flask(__name__, instance_path=instance_path)
    base_app.config.update(
        SECRET_KEY='SECRET KEY',
        SESSION_TYPE='memcached',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite://'),
    )
    InvenioDB(base_app)
    InvenioMail(base_app)
    base_app.jinja_loader.searchpath.append('tests/templates')
    admin = Admin(base_app)
    view_class = mail_adminview['view_class']
    admin.add_view(view_class(**mail_adminview['kwargs']))
    with base_app.app_context():
        if str(db.engine.url) != "sqlite://" and \
                not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.metadata.create_all(db.engine, tables=[MailConfig.__table__])

    yield base_app

    with base_app.app_context():
        drop_database(str(db.engine.url))
    shutil.rmtree(instance_path)


@pytest.fixture(scope='session')
def email_task_app(request):
    """Flask application fixture."""
    app = Flask('testapp')
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite://'),
        CELERY_ALWAYS_EAGER=True,
        CELERY_RESULT_BACKEND='cache',
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        MAIL_SUPPRESS_SEND=True
    )
    FlaskCeleryExt(app)
    InvenioMail(app, StringIO())

    return app


@pytest.fixture(scope='session')
def email_api_app(email_task_app):
    """Flask application fixture."""
    email_task_app.register_blueprint(
        Blueprint('invenio_mail_test', __name__, template_folder='templates')
    )

    return email_task_app


@pytest.fixture
def email_params():
    """Email parameters fixture."""
    return {
        'subject': 'subject',
        'recipients': ['recipient@inveniosoftware.com'],
        'sender': 'sender@inveniosoftware.com',
        'cc': 'cc@inveniosoftware.com',
        'bcc': 'bcc@inveniosoftware.com',
        'reply_to': 'reply_to@inveniosoftware.com',
        'date': datetime.now(),
        'attachments': [],
        'charset': None,
        'extra_headers': None,
        'mail_options': [],
        'rcpt_options': [],
    }


@pytest.fixture
def email_ctx():
    """Email context fixture."""
    return {
        'user': 'User',
        'content': 'This a content.',
        'sender': 'sender',
    }
