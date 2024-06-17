# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

import os
from datetime import datetime

import pytest
from flask import Blueprint, Flask
from flask_celeryext import FlaskCeleryExt
from six import StringIO

from invenio_mail import InvenioMail


@pytest.fixture(scope="session")
def email_task_app(request):
    """Flask application fixture."""
    app = Flask("testapp")
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite://"),
        CELERY_ALWAYS_EAGER=True,
        CELERY_RESULT_BACKEND="cache",
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        MAIL_SUPPRESS_SEND=True,
        MAIL_MAX_ATTACHMENT_SIZE=30,
    )
    FlaskCeleryExt(app)

    InvenioMail(app, StringIO())

    return app


@pytest.fixture(scope="session")
def email_api_app(email_task_app):
    """Flask application fixture."""
    email_task_app.register_blueprint(
        Blueprint("invenio_mail", __name__, template_folder="templates")
    )

    return email_task_app


@pytest.fixture
def email_params():
    """Email parameters fixture."""
    return {
        "subject": "subject",
        "recipients": ["recipient@inveniosoftware.com"],
        "sender": "sender@inveniosoftware.com",
        "cc": "cc@inveniosoftware.com",
        "bcc": "bcc@inveniosoftware.com",
        "reply_to": "reply_to@inveniosoftware.com",
        "date": datetime.now(),
        "attachments": [],
        "charset": None,
        "extra_headers": None,
        "mail_options": [],
        "rcpt_options": [],
    }


@pytest.fixture
def email_ctx():
    """Email context fixture."""
    return {
        "user": "User",
        "content": "This a content.",
        "sender": "sender",
    }
