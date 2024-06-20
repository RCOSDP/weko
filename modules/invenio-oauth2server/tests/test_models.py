# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAuth2Server models test cases."""

import pytest
from invenio_accounts.models import User
from invenio_db import db

from invenio_oauth2server.errors import ScopeDoesNotExists
from invenio_oauth2server.models import Client, Token
from invenio_oauth2server.proxies import current_oauth2server


def test_empty_redirect_uri_and_scope(models_fixture):
    app = models_fixture
    with app.app_context():
        client = Client(
            client_id="dev2",
            client_secret="dev2",
            name="dev2",
            description="",
            is_confidential=False,
            user=app.test_user(),
            _redirect_uris="",
            _default_scopes="",
        )
        with db.session.begin_nested():
            db.session.add(client)

        assert client.default_redirect_uri is None
        assert client.redirect_uris == []
        assert client.default_scopes == []

        client.default_scopes = [
            "test:scope1",
            "test:scope2",
            "test:scope2",
        ]

        assert set(client.default_scopes) == set(["test:scope1", "test:scope2"])
        with pytest.raises(ScopeDoesNotExists):
            client.default_scopes = ["invalid"]

        with db.session.begin_nested():
            db.session.delete(client)


def test_token_scopes(models_fixture):
    app = models_fixture
    with app.app_context():
        client = Client(
            client_id="dev2",
            client_secret="dev2",
            name="dev2",
            description="",
            is_confidential=False,
            user=app.test_user(),
            _redirect_uris="",
            _default_scopes="",
        )
        token = Token(
            client=client,
            user=app.test_user(),
            token_type="bearer",
            access_token="dev_access",
            refresh_token="dev_refresh",
            expires=None,
            is_personal=False,
            is_internal=False,
            _scopes="",
        )
        token.scopes = ["test:scope1", "test:scope2", "test:scope2"]
        with db.session.begin_nested():
            db.session.add(client)
            db.session.add(token)

        assert set(token.scopes) == set(["test:scope1", "test:scope2"])
        with pytest.raises(ScopeDoesNotExists):
            token.scopes = ["invalid"]
        assert token.get_visible_scopes() == ["test:scope1"]

        with db.session.begin_nested():
            db.session.delete(client)


def test_registering_invalid_scope(models_fixture):
    app = models_fixture
    with app.app_context():
        with pytest.raises(TypeError):
            current_oauth2server.register_scope("test:scope")


def test_deletion_of_consumer_resource_owner(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture
    with app.app_context():
        # delete consumer
        with db.session.begin_nested():
            db.session.delete(User.query.get(app.consumer_id))

            # assert that t2 deleted
            assert (
                db.session.query(
                    Token.query.filter(Token.id == app.u1c1u2t2_id).exists()
                ).scalar()
                is False
            )
            # still exist resource_owner and client_1 and token_1
            assert (
                db.session.query(
                    User.query.filter(User.id == app.resource_owner_id).exists()
                ).scalar()
                is True
            )

            assert (
                db.session.query(
                    Client.query.filter(Client.client_id == app.u1c1_id).exists()
                ).scalar()
                is True
            )

            assert (
                db.session.query(
                    Token.query.filter(Token.id == app.u1c1u1t1_id).exists()
                ).scalar()
                is True
            )

            # delete resource_owner
            db.session.delete(User.query.get(app.resource_owner_id))

            # still resource_owner and client_1 and token_1 deleted
            assert (
                db.session.query(
                    Client.query.filter(Client.client_id == app.u1c1_id).exists()
                ).scalar()
                is False
            )

            assert (
                db.session.query(
                    Token.query.filter(Token.id == app.u1c1u1t1_id).exists()
                ).scalar()
                is False
            )


def test_deletion_of_resource_owner_consumer(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(User.query.get(app.resource_owner_id))

        # assert that c1, t1, t2 deleted
        assert (
            db.session.query(
                Client.query.filter(Client.client_id == app.u1c1_id).exists()
            ).scalar()
            is False
        )

        assert (
            db.session.query(
                Token.query.filter(Token.id == app.u1c1u1t1_id).exists()
            ).scalar()
            is False
        )

        assert (
            db.session.query(
                Token.query.filter(Token.id == app.u1c1u2t2_id).exists()
            ).scalar()
            is False
        )

        # still exist consumer
        assert (
            db.session.query(
                User.query.filter(User.id == app.consumer_id).exists()
            ).scalar()
            is True
        )

        # delete consumer
        db.session.delete(User.query.get(app.consumer_id))


def test_deletion_of_client1(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    # delete client_1
    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(Client.query.get(app.u1c1_id))

            # assert that token_1, token_2 deleted
            assert (
                db.session.query(
                    Token.query.filter(Token.id == app.u1c1u1t1_id).exists()
                ).scalar()
                is False
            )

            assert (
                db.session.query(
                    Token.query.filter(Token.id == app.u1c1u2t2_id).exists()
                ).scalar()
                is False
            )

            # still exist resource_owner, consumer
            assert (
                db.session.query(
                    User.query.filter(User.id == app.resource_owner_id).exists()
                ).scalar()
                is True
            )

            assert (
                db.session.query(
                    User.query.filter(User.id == app.consumer_id).exists()
                ).scalar()
                is True
            )

            # delete consumer
            db.session.delete(User.query.get(app.consumer_id))


def test_deletion_of_token1(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    # delete token_1
    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(Token.query.get(app.u1c1u1t1_id))

        # still exist resource_owner, consumer, client_1, token_2
        assert (
            db.session.query(
                User.query.filter(User.id == app.resource_owner_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                User.query.filter(User.id == app.consumer_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                Client.query.filter(Client.client_id == app.u1c1_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                Token.query.filter(Token.id == app.u1c1u2t2_id).exists()
            ).scalar()
            is True
        )

        # delete consumer
        db.session.delete(User.query.get(app.consumer_id))


def test_deletion_of_token2(models_fixture):
    """Test deleting of connected user."""
    app = models_fixture

    # delete token_2
    with app.app_context():
        with db.session.begin_nested():
            db.session.delete(Token.query.get(app.u1c1u2t2_id))

        # still exist resource_owner, consumer, client_1, token_1
        assert (
            db.session.query(
                User.query.filter(User.id == app.resource_owner_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                User.query.filter(User.id == app.consumer_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                Client.query.filter(Client.client_id == app.u1c1_id).exists()
            ).scalar()
            is True
        )

        assert (
            db.session.query(
                Token.query.filter(Token.id == app.u1c1u1t1_id).exists()
            ).scalar()
            is True
        )

        # delete consumer
        db.session.delete(User.query.get(app.consumer_id))
