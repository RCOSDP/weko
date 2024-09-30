# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test password hashing."""

from binascii import hexlify, unhexlify

import flask
import pytest
from flask_security.utils import hash_password, verify_password

from invenio_accounts.hash import (
    _to_binary,
    _to_string,
    mysql_aes_decrypt,
    mysql_aes_encrypt,
)
from invenio_accounts.testutils import (
    client_authenticated,
    create_test_user,
    login_user_via_view,
)


def test_mysql_aes_encrypt():
    """Test mysql_aes_encrypt."""
    assert (
        hexlify(mysql_aes_encrypt("test", "key")) == b"9e9ce44cd9df2b201f51947e03bccbe2"
    )
    assert (
        hexlify(mysql_aes_encrypt("test", "key")) == b"9e9ce44cd9df2b201f51947e03bccbe2"
    )
    assert (
        hexlify(mysql_aes_encrypt("test", "key")) == b"9e9ce44cd9df2b201f51947e03bccbe2"
    )
    assert (
        hexlify(mysql_aes_encrypt("test", "key")) == b"9e9ce44cd9df2b201f51947e03bccbe2"
    )
    pytest.raises(AssertionError, mysql_aes_encrypt, object(), "key")
    pytest.raises(AssertionError, mysql_aes_encrypt, "val", object())


def test_mysql_aes_decrypt():
    """Test mysql_aes_encrypt."""
    assert (
        mysql_aes_decrypt(unhexlify(b"9e9ce44cd9df2b201f51947e03bccbe2"), "key")
        == "test"
    )
    assert (
        mysql_aes_decrypt(unhexlify("9e9ce44cd9df2b201f51947e03bccbe2"), "key")
        == "test"
    )
    pytest.raises(AssertionError, mysql_aes_decrypt, object(), "key")
    pytest.raises(AssertionError, mysql_aes_decrypt, "val", object())


def test_context(app):
    """Test passlib password context."""
    with app.app_context():
        ctx = flask.current_app.extensions["security"].pwd_context
        hashval = hash_password("test")
        assert hashval != "test"
        assert verify_password("test", hashval)
        assert not ctx.needs_update(hashval)
        assert ctx.hash("test") != ctx.hash("test")


def test_conversion():
    """Test conversion between bytes and text."""
    str = "abcd1234"
    byte_str = b"abcd1234"
    u_str = "abcd1234"
    assert _to_binary(str) == byte_str
    assert _to_string(byte_str) == str
    assert _to_string(str) == str
    assert _to_binary(byte_str) == byte_str
    assert _to_string(u_str) == u_str


def test_unicode_regression(app):
    """Test legacy encryption with Unicode encoding."""
    with app.app_context():
        user = create_legacy_user(password="κωδικός")
        assert verify_password("κωδικός", user.password)


def test_invenio_aes_encrypted_email(app):
    """Test legacy encryption."""
    with app.app_context():
        ctx = flask.current_app.extensions["security"].pwd_context
        user = create_legacy_user()
        assert verify_password(user.password_plaintext, user.password)
        assert ctx.needs_update(user.password)


def test_user_login(app):
    """Test users' high-level login process."""
    with app.app_context():
        user = create_test_user("test@TEST.org")
        with app.test_client() as client:
            login_user_via_view(client, user.email, user.password_plaintext)
            assert client_authenticated(client)


def test_legacy_user_login(app):
    """Test legacy users' high-level login process."""
    with app.app_context():
        user = create_legacy_user()
        old_hashval = user.password
        with app.test_client() as client:
            login_user_via_view(client, user.email, user.password_plaintext)
            # Verify user is authenticated
            assert client_authenticated(client)
            # Verify password hash is upgraded
            ds = flask.current_app.extensions["security"].datastore
            user2 = ds.find_user(email=user.email)
            assert old_hashval != user2.password


def test_monkey_patch(app):
    """Test monkey-patching of Flask-Security's get_hmac function."""
    with app.app_context():
        user = create_test_user("test@test.org")
        assert verify_password(user.password_plaintext, user.password)


def test_monkey_patch_legacy(app):
    """Test monkey-patching of Flask-Security's get_hmac function."""
    with app.app_context():
        user = create_legacy_user()
        assert verify_password(user.password_plaintext, user.password)


def create_legacy_user(email="test@test.org", password="qwert1234", **kwargs):
    """Create a legacy user in the datastore.

    A legacy user's password has been encrypted with the legacy mechanism,
    namely 'invenio_aes_encrypted_email'.
    """
    assert flask.current_app.testing
    ds = flask.current_app.extensions["security"].datastore

    # Encrypt password
    ctx = flask.current_app.extensions["security"].pwd_context
    encrypted_password = ctx.encrypt(
        password,
        scheme="invenio_aes_encrypted_email",
        salt=email,
    )

    # Update datastore
    user = ds.create_user(email=email, password=encrypted_password, **kwargs)
    ds.commit()
    user.password_plaintext = password

    return user
