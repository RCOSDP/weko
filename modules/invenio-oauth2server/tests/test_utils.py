# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test case for rebuilding access tokens."""

import sys

import pytest
from invenio_db import db

from invenio_oauth2server.models import Token
from invenio_oauth2server.utils import rebuild_access_tokens


def test_rebuilding_access_tokens(models_fixture):
    """Test rebuilding access tokens with random new SECRET_KEY."""
    app = models_fixture
    with app.app_context():
        old_secret_key = app.secret_key
        tokens_before = Token.query.order_by(Token.id).all()

        # Changing application SECRET_KEY
        app.secret_key = "NEW_SECRET_KEY"
        db.session.expunge_all()

        # Asserting the decoding error occurs with the stale SECRET_KEY
        if sys.version_info[0] < 3:  # python 2
            token = Token.query.filter(Token.id == tokens_before[0].id).one()
            assert token.access_token != tokens_before[0].access_token
        else:  # python 3
            with pytest.raises(ValueError):
                Token.query.filter(Token.id == tokens_before[0].id).one()

        db.session.expunge_all()
        rebuild_access_tokens(old_secret_key)
        tokens_after = Token.query.order_by(Token.id).all()

        for token_before, token_after in list(zip(tokens_before, tokens_after)):
            assert token_before.access_token == token_after.access_token
            assert token_before.refresh_token == token_after.refresh_token
