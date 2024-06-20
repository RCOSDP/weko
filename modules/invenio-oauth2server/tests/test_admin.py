# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

from flask import url_for
from flask_admin import Admin
from invenio_db import db

from invenio_oauth2server import InvenioOAuth2Server
from invenio_oauth2server.admin import (
    oauth2server_clients_adminview,
    oauth2server_tokens_adminview,
)


def test_admin(models_fixture):
    """Test flask-admin interface."""
    app = models_fixture
    InvenioOAuth2Server(app)

    assert isinstance(oauth2server_tokens_adminview, dict)
    assert isinstance(oauth2server_clients_adminview, dict)

    assert "view_class" in oauth2server_tokens_adminview
    assert "view_class" in oauth2server_clients_adminview

    admin = Admin(app, name="Test")

    clients_view = oauth2server_clients_adminview.pop("view_class")
    clients_model, clients_session = oauth2server_clients_adminview.pop("args")
    clients_kwargs = oauth2server_clients_adminview.pop("kwargs")
    tokens_view = oauth2server_tokens_adminview.pop("view_class")
    tokens_model, tokens_session = oauth2server_tokens_adminview.pop("args")
    tokens_kwargs = oauth2server_tokens_adminview.pop("kwargs")
    admin.add_view(clients_view(clients_model, db.session, **clients_kwargs))
    admin.add_view(tokens_view(tokens_model, db.session, **tokens_kwargs))

    menu_items = {str(item.name): item for item in admin.menu()}
    assert "User Management" in menu_items
    assert menu_items["User Management"].is_category()

    submenu_items = {
        str(item.name): item for item in menu_items["User Management"].get_children()
    }
    assert "OAuth Applications" in submenu_items
    assert "OAuth Application Tokens" in submenu_items

    with app.test_request_context():
        token_request_url = url_for("token.index_view")
        client_request_url = url_for("client.index_view")
        client_view_url = url_for(
            "invenio_oauth2server_settings.client_view", client_id="client_test_u1c1"
        )
        client_reset_url = url_for(
            "invenio_oauth2server_settings.client_reset", client_id="client_test_u1c1"
        )
        token_view_url = url_for(
            "invenio_oauth2server_settings.token_view", token_id="1"
        )
        token_revoke_url = url_for(
            "invenio_oauth2server_settings.token_revoke", token_id="1"
        )

    with app.app_context():
        with app.test_client() as client:
            res = client.get(token_request_url, follow_redirects=True)
            assert res.status_code == 200
            res = client.get(client_request_url, follow_redirects=True)
            assert res.status_code == 200
            res = client.get(client_view_url, follow_redirects=True)
            assert res.status_code == 200
            res = client.post(client_reset_url, follow_redirects=True)
            assert res.status_code == 200
            res = client.get(token_view_url, follow_redirects=True)
            assert res.status_code == 200
            res = client.post(token_revoke_url, follow_redirects=True)
            assert res.status_code == 405
