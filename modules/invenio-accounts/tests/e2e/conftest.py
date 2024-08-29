# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

import multiprocessing
import os
import shutil
import tempfile
import time

import pytest
from flask import Flask
from flask_mail import Mail
from flask_menu import Menu
from invenio_db import InvenioDB, db
from invenio_i18n import Babel
from selenium import webdriver
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from invenio_accounts import InvenioAccounts
from invenio_accounts.views.settings import create_settings_blueprint


@pytest.fixture(scope="session")
def app(request):
    """Flask application fixture for E2E/integration/selenium tests.

    Overrides the `app` fixture found in `../conftest.py`. Tests/files in this
    folder and subfolders will see this variant of the `app` fixture.
    """
    instance_path = tempfile.mkdtemp()
    app = Flask("testapp", instance_path=instance_path)
    app.config.update(
        ACCOUNTS_USE_CELERY=False,
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        TESTING=True,
    )
    Menu(app)
    Babel(app)
    Mail(app)
    InvenioDB(app)
    InvenioAccounts(app)
    app.register_blueprint(create_settings_blueprint(app))

    with app.app_context():
        if not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            drop_database(str(db.engine.url))
        shutil.rmtree(instance_path)

    request.addfinalizer(teardown)
    return app


def pytest_generate_tests(metafunc):
    """Override pytest's default test collection function.

    For each test in this directory which uses the `env_browser` fixture, said
    test is called once for each value found in the `E2E_WEBDRIVER_BROWSERS`
    environment variable.
    """
    browsers = os.environ.get("E2E_WEBDRIVER_BROWSERS", "").split()

    if not browsers:
        pytest.skip("E2E_WEBDRIVER_BROWSERS not set, " "end-to-end tests skipped.")

    if "env_browser" in metafunc.fixturenames:
        # In Python 2.7 the fallback kwarg of os.environ.get is `failobj`,
        # in 3.x it's `default`.
        metafunc.parametrize("env_browser", browsers, indirect=True)


@pytest.fixture()
def env_browser(request):
    """Create a webdriver instance of the browser specified by request.

    The default browser is Firefox.  The webdriver instance is killed after the
    number of seconds specified by the ``E2E_WEBDRIVER_TIMEOUT`` variable or
    defaults to 300 (five minutes).
    """
    timeout = int(os.environ.get("E2E_WEBDRIVER_TIMEOUT", 300))

    def wait_kill():
        time.sleep(timeout)
        browser.quit()

    def finalizer():
        browser.quit()
        timeout_process.terminate()

    timeout_process = multiprocessing.Process(target=wait_kill)

    # Create instance of webdriver.`request.param`()
    browser = getattr(webdriver, request.param)()
    # Add finalizer to quit the webdriver instance
    request.addfinalizer(finalizer)

    timeout_process.start()
    return browser
