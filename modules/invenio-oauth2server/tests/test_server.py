# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test server views."""

from flask_principal import AnonymousIdentity


def test_user_identity_init(resource_fixture):
    """Test that user identity is loaded properly when a token is used."""
    app = resource_fixture
    with app.test_client() as client:
        # test without token (anonymous user)
        request_res = client.get(app.url_for_test0resource)
        assert request_res.status_code == 200
        assert isinstance(app.identity, AnonymousIdentity)

        # test with token
        request_res = client.get(app.url_for_test0resource_token)
        assert request_res.status_code == 200
        assert app.identity.user.id == app.user_id
