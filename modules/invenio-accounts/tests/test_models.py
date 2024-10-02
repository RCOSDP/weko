# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2024 CERN.
# Copyright (C)      2022 TU Wien.
# Copyright (C) 2022 KTH Royal Institute of Technology
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test invenio-accounts models."""

import pytest
from invenio_db import db
from marshmallow import Schema, fields
from sqlalchemy import inspect

from invenio_accounts import testutils
from invenio_accounts.models import (
    Domain,
    DomainCategory,
    DomainOrg,
    DomainStatus,
    SessionActivity,
    User,
)


class CustomProfile(Schema):
    """A custom user profile schema."""

    file_descriptor = fields.Integer(strict=True)


def test_session_activity_model(app):
    """Test SessionActivity model."""
    with app.app_context():
        # SessionActivity table is in the database
        inspector = inspect(db.engine)
        assert "accounts_user_session_activity" in inspector.get_table_names()

        user = testutils.create_test_user("test@test.org")

        # Create a new SessionActivity object, put it in the db
        session_activity = SessionActivity(user_id=user.get_id(), sid_s="teststring")
        database = db

        # the `created` field is magicked in via the Timestamp mixin class
        assert not session_activity.created
        database.session.add(session_activity)
        # Commit it to the books.
        database.session.commit()
        assert session_activity.created
        assert len(user.active_sessions) == 1

        # Now how does this look on the user object?
        assert session_activity == user.active_sessions[0]

        session_two = SessionActivity(user_id=user.get_id(), sid_s="testring_2")
        database.session.add(session_two)
        # Commit it to the books.
        database.session.commit()

        assert len(user.active_sessions) == 2
        # Check #columns in table
        queried = database.session.query(SessionActivity)
        assert queried.count() == 2
        active_sessions = queried.all()
        assert session_activity.sid_s in [x.sid_s for x in active_sessions]
        assert session_two in queried.filter(SessionActivity.sid_s == session_two.sid_s)
        assert queried.count() == 2  # `.filter` doesn't change the query

        # Test session deletion
        session_to_delete = user.active_sessions[0]
        database.session.delete(session_to_delete)
        assert len(user.active_sessions) == 2  # Not yet updated.
        assert queried.count() == 1
        # Deletion is visible on `user` once database session is commited.
        database.session.commit()
        assert len(user.active_sessions) == 1
        assert user.active_sessions[0].sid_s != session_to_delete.sid_s


def test_profiles(app):
    """Test the user profile."""
    user = User(email="admin@inveniosoftware.org")
    profile = {
        "full_name": "Invenio Admin",
    }

    with pytest.raises(ValueError):
        # the profile doesn't expect an 'email' value
        user.user_profile = {
            **profile,
            "email": "admin@inveniosoftware.org",
        }

    assert user.user_profile == {}

    # a valid profile should be accepted
    user.user_profile = profile
    assert dict(user.user_profile) == profile

    # setting expected properties should work
    assert len(user.user_profile) == 1
    assert user.user_profile["full_name"] == "Invenio Admin"

    # but setting unexpected properties should not work
    with pytest.raises(ValueError):
        user.user_profile["invalid"] = "value"

    # similar with wrong types for expected fields
    with pytest.raises(ValueError):
        user.user_profile["email"] = 1

    assert len(user.user_profile) == 1
    assert user.user_profile["full_name"] == "Invenio Admin"
    assert (
        app.config["ACCOUNTS_DEFAULT_EMAIL_VISIBILITY"]
        == user.preferences["email_visibility"]
    )
    assert (
        app.config["ACCOUNTS_DEFAULT_USER_VISIBILITY"] == user.preferences["visibility"]
    )


def test_custom_profiles(app):
    """Test if the customization mechanism for user profiles works."""
    app.config["ACCOUNTS_USER_PROFILE_SCHEMA"] = CustomProfile()
    user = User(email="admin@inveniosoftware.org")

    # the default fields aren't allowed in the custom schema
    with pytest.raises(ValueError):
        user.user_profile = {
            "full_name": "Invenio Admin",
        }

    # the expected properties should work...
    user.user_profile = {"file_descriptor": 1}
    assert dict(user.user_profile) == {"file_descriptor": 1}

    # ... but not with unexpected types!
    with pytest.raises(ValueError):
        user.user_profile["file_descriptor"] = "1"

    assert dict(user.user_profile) == {"file_descriptor": 1}


def test_user_domain_attr(app):
    u = User(email="admin@CERN.CH")
    db.session.commit()
    assert u.domain == "cern.ch"


def test_user_username_case_insensitive_comparator(app):
    ds = app.extensions["invenio-accounts"].datastore
    ds.create_user(username="UserName")
    ds.commit()

    u = ds.find_user(username="uSERnAME")
    assert u is not None
    assert u.username == "UserName"


def test_domain_model(app):
    d = Domain.create("CERN.CH")
    assert d.domain == "cern.ch"
    assert d.tld == "ch"
    assert d.status == DomainStatus.new
    assert d.flagged == False
    assert d.flagged_source == ""
    assert d.org is None
    assert d.category is None
    db.session.commit()

    # Support top level domains like
    d = Domain.create("cern")
    assert d.domain == "cern"
    assert d.tld == "cern"
    db.session.commit()

    # Normalise domain names
    d = Domain.create("zenodo.org.")
    assert d.domain == "zenodo.org"
    assert d.tld == "org"
    db.session.commit()

    with pytest.raises(Exception):
        Domain.create("cern.ch.")
        db.session.commit()


def test_domain_org(app):
    parent = DomainOrg.create(
        "https://ror.org/01cwqze88",
        "National Institutes of Health",
        json={"country": "us"},
    )

    child = DomainOrg.create(
        "https://ror.org/040gcmg81",
        "National Cancer Institute",
        json={"country": "us"},
        parent=parent,
    )
    db.session.commit()

    d = Domain.create("cancer.gov", status=DomainStatus.verified, org=child)
    db.session.commit()

    assert d.org == child
    assert child.parent == parent


def test_domain_category(app):
    c1 = DomainCategory.create("spammer")
    c2 = DomainCategory.create("organisation")
    db.session.commit()

    c = DomainCategory.get("spammer")
    assert c.label == "spammer"
