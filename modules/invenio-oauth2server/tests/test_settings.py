# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test settings views."""

from flask import url_for
from helpers import login
from invenio_i18n import gettext as _

from invenio_oauth2server.models import Client, Token


def test_personal_token_management(settings_fixture):
    """Test managing personal tokens through the views."""
    app = settings_fixture
    with app.test_request_context():
        with app.test_client() as client:
            login(client)

            # Non-existing token should return 404
            resp = client.get(
                url_for("invenio_oauth2server_settings.token_view", token_id=1000)
            )
            resp.status_code == 404

            # Get the new token form
            resp = client.get(url_for("invenio_oauth2server_settings.token_new"))
            resp.status_code == 200
            assert _("New personal access token") in str(resp.get_data())
            assert '<label for="scopes-test:scope"' in str(resp.get_data())
            assert '<label for="scopes-test:scope2"' in str(resp.get_data())

            # Create a new token with invalid form data
            resp = client.post(
                url_for("invenio_oauth2server_settings.token_new"),
                data={
                    "name": "x" * (40 + 1),  # max length is 40
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200
            assert "name must be less than 40 char" in str(resp.get_data())

            # Create a new token
            resp = client.post(
                url_for("invenio_oauth2server_settings.token_new"),
                data={
                    "name": "Test_Token",
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200
            assert "Personal access token / Test_Token" in str(resp.get_data())
            assert "test:scope" in str(resp.get_data())
            assert "test:scope2" in str(resp.get_data())

            token = Token.query.first()

            # Rename the token
            resp = client.post(
                url_for("invenio_oauth2server_settings.token_view", token_id=token.id),
                data=dict(name="Test_Token_Renamed"),
            )
            assert resp.status_code == 200
            assert "Test_Token_Renamed" in str(resp.get_data())

            # Token should be visible on index
            resp = client.get(url_for("invenio_oauth2server_settings.index"))
            assert resp.status_code == 200
            assert "Test_Token_Renamed" in str(resp.get_data())

            # Delete the token
            resp = client.post(
                url_for("invenio_oauth2server_settings.token_view", token_id=1),
                data=dict(delete=True),
                follow_redirects=True,
            )
            assert resp.status_code == 200
            # Token should no longer exist on index
            assert "Test_Token_Renamed" not in str(resp.get_data())


def test_authorized_app_revocation(developer_app_fixture):
    """Test managing authorized application tokens through the views."""
    app = developer_app_fixture
    with app.test_request_context():
        with app.test_client() as client:
            login(client)

            # Check that there is a single token for the authorized application
            assert Token.query.count() == 1

            # Check that the authorized application is visible on index view
            resp = client.get(url_for("invenio_oauth2server_settings.index"))
            assert resp.status_code == 200
            assert "Test description" in str(resp.get_data())
            assert "Test name" in str(resp.get_data())

            # Revoke the authorized application token
            resp = client.get(
                url_for("invenio_oauth2server_settings.token_revoke", token_id=1),
                follow_redirects=True,
            )
            assert resp.status_code == 200
            # Authorized application should no longer exist on index
            assert "Test description" not in str(resp.get_data())
            assert "Test name" not in str(resp.get_data())
            # Check that the authorized application token was actually deleted
            assert Token.query.count() == 0


def test_client_management(settings_fixture):
    """Test managing clients through the views."""
    app = settings_fixture
    with app.test_request_context():
        with app.test_client() as client:
            login(client)

            # Non-existing client should return 404
            resp = client.get(
                url_for("invenio_oauth2server_settings.client_view", client_id=1000)
            )
            assert resp.status_code == 404

            # Create a new client
            resp = client.post(
                url_for("invenio_oauth2server_settings.client_new"),
                data=dict(
                    name="Test_Client",
                    description="Test description for Test_Client.",
                    website="http://inveniosoftware.org/",
                    redirect_uris=url_for(
                        "invenio_oauth2server_settings.index", _external=True
                    ),
                    is_confditential=1,
                ),
                follow_redirects=True,
            )
            assert resp.status_code == 200
            assert "Application / Test_Client" in str(resp.get_data())
            test_client = Client.query.first()
            assert test_client.client_id in str(resp.get_data())

            # Client should be visible on index
            resp = client.get(url_for("invenio_oauth2server_settings.index"))
            assert resp.status_code == 200
            assert "Test_Client" in str(resp.get_data())

            # Reset client secret
            original_client_secret = test_client.client_secret
            resp = client.post(
                url_for(
                    "invenio_oauth2server_settings.client_reset",
                    client_id=test_client.client_id,
                ),
                data=dict(reset="yes"),
                follow_redirects=True,
            )
            assert resp.status_code == 200
            assert test_client.client_secret in str(resp.get_data())
            assert original_client_secret not in str(resp.get_data())

            # Invalid redirect uri should error
            original_redirect_uris = test_client.redirect_uris
            resp = client.post(
                url_for(
                    "invenio_oauth2server_settings.client_view",
                    client_id=test_client.client_id,
                ),
                data=dict(
                    name="Test_Client",
                    description="Test description for Test_Client",
                    website="http://inveniosoftware.org/",
                    redirect_uris="https:/invalid",
                ),
            )
            assert resp.status_code == 200
            assert test_client.redirect_uris == original_redirect_uris

            # Modify the client
            resp = client.post(
                url_for(
                    "invenio_oauth2server_settings.client_view",
                    client_id=test_client.client_id,
                ),
                data=dict(
                    name="Modified_Name",
                    description="Modified Description",
                    website="http://modified-url.org",
                    redirect_uris="https://example.org",
                ),
            )
            assert resp.status_code == 200
            assert "Modified_Name" in str(resp.get_data())
            assert "Modified Description" in str(resp.get_data())
            assert "http://modified-url.org" in str(resp.get_data())

            # Delete the client
            resp = client.post(
                url_for(
                    "invenio_oauth2server_settings.client_view",
                    client_id=test_client.client_id,
                ),
                follow_redirects=True,
                data=dict(delete=True),
            )
            assert resp.status_code == 200
            assert test_client.name not in str(resp.get_data())
