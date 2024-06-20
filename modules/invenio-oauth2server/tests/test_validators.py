# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test invenio_oauth2server validators."""

import pytest
from oauthlib.oauth2.rfc6749.errors import (
    InsecureTransportError,
    InvalidRedirectURIError,
)
from wtforms.validators import ValidationError

from invenio_oauth2server.validators import URLValidator, validate_redirect_uri


@pytest.mark.parametrize(
    "input,expected",
    [
        ("example.org/", InvalidRedirectURIError()),
        ("http://", InvalidRedirectURIError()),
        ("http://example.org/", InsecureTransportError()),
        ("https://example.org/", None),
        ("https://localhost/", None),
        ("https://127.0.0.1", None),
    ],
)
def test_validate_redirect_uri(input, expected):
    """Test redirect URI validator."""
    try:
        validate_redirect_uri(input)
    except Exception as e:
        assert type(e) is type(expected)


def test_url_validator(app):
    """Test url validator."""

    class Field(object):
        def __init__(self, data):
            self.data = data

        def gettext(self, *args, **kwargs):
            return "text"

    with app.app_context():
        # usually if localhost, validation is failing
        with pytest.raises(ValidationError):
            URLValidator()(form=None, field=Field(data="http://localhost:5000"))
        URLValidator()(form=None, field=Field(data="http://mywebsite.it:5000"))

        # enable debug mode to accept also localhost
        app.config["DEBUG"] = True
        URLValidator()(form=None, field=Field(data="http://localhost:5000"))
        URLValidator()(form=None, field=Field(data="http://mywebsite.it:5000"))
