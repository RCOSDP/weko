# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

from click.testing import CliRunner

from invenio_oauth2server.cli import tokens_create, tokens_delete
from invenio_oauth2server.models import Client, Token

"""
$ invenio tokens create "my-token" \
    --email foobar@example.com --internal \
    --scopes user:email,records:read
abcdef1234567890abcdef1234567890

# Delete a token
$ invenio tokens delete --name "my-token" --email foobar@example.com
Token "abcdef1234567890abcdef1234567890" deleted

# ...or...
$ invenio tokens delete
Enter token: <password-like input>
Token "abcdef1234567890abcdef1234567890" deleted
"""


def test_cli_tokens(app, script_info, settings_fixture):
    """Test create user CLI."""
    runner = CliRunner()

    result = runner.invoke(
        tokens_create,
        ["--name", "test-token", "--user", "info@inveniosoftware.org"],
        obj=script_info,
    )
    assert result.exit_code == 0
    access_token = result.output.strip()

    with app.app_context():
        client = Client.query.one()
        assert client.user.email == "info@inveniosoftware.org"

        token = Token.query.one()
        assert token.access_token == access_token
        assert token.scopes == []

    result = runner.invoke(
        tokens_delete,
        ["--name", "test-token", "--user", "info@inveniosoftware.org", "--force"],
        obj=script_info,
    )
    assert result.exit_code == 0

    with app.app_context():
        assert Token.query.count() == 0
