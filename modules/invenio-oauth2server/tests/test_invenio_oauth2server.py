# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

import pytest
from flask import Flask

from invenio_oauth2server import InvenioOAuth2Server, InvenioOAuth2ServerREST
from invenio_oauth2server.ext import verify_oauth_token_and_set_current_user


def test_version():
    """Test version import."""
    from invenio_oauth2server import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioOAuth2Server(app)
    assert "invenio-oauth2server" in app.extensions
    assert ext.app is app

    app = Flask("testapp")
    ext = InvenioOAuth2Server()
    assert "invenio-oauth2server" not in app.extensions
    state = ext.init_app(app)
    assert "invenio-oauth2server" in app.extensions
    assert state.app is app


def test_init_rest():
    """Test REST extension initialization."""
    app = Flask("testapp")
    ext = InvenioOAuth2ServerREST(app)
    assert verify_oauth_token_and_set_current_user in app.before_request_funcs[None]

    app = Flask("testapp")
    ext = InvenioOAuth2ServerREST()
    assert verify_oauth_token_and_set_current_user not in app.before_request_funcs.get(
        None, []
    )
    ext.init_app(app)
    assert verify_oauth_token_and_set_current_user in app.before_request_funcs[None]


def test_init_rest_with_oauthlib_monkeypatch():
    """Test REST OAuthlib monkeypatching."""
    app = Flask("testapp")

    from oauthlib.common import urlencoded

    assert "^" not in urlencoded
    old_urlencoded = set(urlencoded)

    app.config["OAUTH2SERVER_ALLOWED_URLENCODE_CHARACTERS"] = "^"

    with pytest.warns(RuntimeWarning):
        InvenioOAuth2ServerREST(app)
    assert verify_oauth_token_and_set_current_user in app.before_request_funcs[None]

    from oauthlib.common import urlencoded

    assert old_urlencoded != urlencoded
    assert "^" in urlencoded
