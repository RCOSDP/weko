# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""E2E/integration tests for Invenio-Accounts."""

from __future__ import absolute_import, print_function

from time import sleep

import flask
from six.moves.urllib.request import urlopen

from invenio_accounts import testutils


def test_live_server(live_server):
    """Test that the login page of `live_server` is reachable.

    The `live_server` fixture is provided by pytest-flask.  When a test using
    said fixture is run, the return object of the `app` fixture is run in a
    background process.  For this test pytest will use the `app` fixture
    defined in `./conftest.py` instead of the one in `../conftest.py`.
    """
    # With pytest-flask we don't need to be in the application context
    # to use `flask.url_for`.
    url = flask.url_for('security.login', _external=True)
    response = urlopen(url)
    assert response
    assert response.code == 200


def test_webdriver_not_authenticated(live_server, env_browser):
    """Test unauthenticated webdriver client redirect.

    Test that an unauthenticated webdriver client is redirected from
    the change password page to the login page.
    """
    browser = env_browser
    browser.get(flask.url_for('security.change_password', _external=True))
    assert (flask.url_for('security.login', _external=True) in
            browser.current_url)


def test_user_registration(live_server, env_browser):
    """E2E user registration and login test."""
    browser = env_browser
    # 1. Go to user registration page
    browser.get(flask.url_for('security.register', _external=True))
    assert (flask.url_for('security.register', _external=True) in
            browser.current_url)
    # 2. Input user data
    signup_form = browser.find_element_by_name('register_user_form')
    input_email = signup_form.find_element_by_name('email')
    input_password = signup_form.find_element_by_name('password')
    # input w/ name "email"
    # input w/ name "password"
    user_email = 'test@example.org'
    user_password = '12345_SIx'
    input_email.send_keys(user_email)
    input_password.send_keys(user_password)

    # 3. submit form
    signup_form.submit()
    sleep(1)  # we need to wait after each form submission for redirect

    # ...and get redirected to the "home page" ('/')
    # This isn't a very important part of the process, and the '/' url isn't
    # even registered for the Invenio-Accounts e2e app. So we don't check it.

    # 3.5: After registering we should be logged in.
    browser.get(flask.url_for('security.change_password', _external=True))
    assert (flask.url_for('security.change_password', _external=True) in
            browser.current_url)

    # 3.5: logout.
    browser.get(flask.url_for('security.logout', _external=True))
    assert not testutils.webdriver_authenticated(browser)

    # 4. go to login-form
    browser.get(flask.url_for('security.login', _external=True))
    assert (flask.url_for('security.login', _external=True) in
            browser.current_url)
    login_form = browser.find_element_by_name('login_user_form')
    # 5. input registered info
    login_form.find_element_by_name('email').send_keys(user_email)
    login_form.find_element_by_name('password').send_keys(user_password)
    # 6. Submit!
    # check if authenticated at `flask.url_for('security.change_password')`
    login_form.submit()
    sleep(1)

    assert testutils.webdriver_authenticated(browser)

    browser.get(flask.url_for('security.change_password', _external=True))
    assert (flask.url_for('security.change_password', _external=True) in
            browser.current_url)
