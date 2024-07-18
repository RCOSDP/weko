# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2024 CERN.
# Copyright (C) 2022 KTH Royal Institute of Technology
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database models for accounts."""

import uuid
from datetime import datetime

from flask import current_app, session
from flask_babel import refresh
from flask_security import RoleMixin, UserMixin
from invenio_db import db
from sqlalchemy import func
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy.orm import validates
from sqlalchemy_utils import IPAddressType, Timestamp
from sqlalchemy_utils.types import ChoiceType, JSONType

from .errors import AlreadyLinkedError
from .profiles import UserPreferenceDict, UserProfileDict
from .utils import DomainStatus, split_emailaddr, validate_username

json_field = (
    db.JSON()
    .with_variant(
        postgresql.JSONB(none_as_null=True),
        "postgresql",
    )
    .with_variant(
        JSONType(),
        "sqlite",
    )
    .with_variant(
        JSONType(),
        "mysql",
    )
)


userrole = db.Table(
    "accounts_userrole",
    db.Column(
        "user_id",
        db.Integer(),
        db.ForeignKey("accounts_user.id", name="fk_accounts_userrole_user_id"),
    ),
    db.Column(
        "role_id",
        db.String(80),
        db.ForeignKey("accounts_role.id", name="fk_accounts_userrole_role_id"),
    ),
)
"""Relationship between users and roles."""


class CaseInsensitiveComparator(Comparator):
    """Class allowing case-insensitive comparisons on an attribute."""

    def __eq__(self, other):
        """Case-insensitive equal operation."""
        return func.lower(self.__clause_element__()) == func.lower(other)


class Role(db.Model, Timestamp, RoleMixin):
    """Role data model."""

    __tablename__ = "accounts_role"

    id = db.Column(db.String(80), primary_key=True, default=lambda x: str(uuid.uuid4()))

    name = db.Column(db.String(80), unique=True)
    """Role name."""

    description = db.Column(db.String(255))
    """Role description."""

    is_managed = db.Column(db.Boolean(), default=True, nullable=False)
    """True when the role is managed by Invenio, and not externally provided."""

    # Enables SQLAlchemy version counter
    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {"version_id_col": version_id}

    def __str__(self):
        """Return the name and description of the role."""
        return "{0.name} - {0.description}".format(self)


class User(db.Model, Timestamp, UserMixin):
    """User data model."""

    __tablename__ = "accounts_user"

    id = db.Column(db.Integer, primary_key=True)

    _username = db.Column("username", db.String(255), nullable=True, unique=True)
    """Lower-case version of the username, to assert uniqueness."""

    _displayname = db.Column("displayname", db.String(255), nullable=True)
    """Case-preserving version of the username."""

    _email = db.Column("email", db.String(255), unique=True)
    """User email."""

    domain = db.Column(db.String(255), nullable=True)
    """Domain of email."""

    password = db.Column(db.String(255))
    """User password."""

    active = db.Column(db.Boolean(name="active"))
    """Flag to say if the user is active or not ."""

    confirmed_at = db.Column(db.DateTime)
    """When the user confirmed the email address."""

    roles = db.relationship(
        "Role", secondary=userrole, backref=db.backref("users", lazy="dynamic")
    )
    """List of the user's roles."""

    # Enables SQLAlchemy version counter
    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    _user_profile = db.Column(
        "profile",
        json_field,
        default=lambda: dict(),
        nullable=True,
    )
    """The user profile as a JSON field."""

    _preferences = db.Column(
        "preferences",
        json_field,
        default=lambda: dict(),
        nullable=True,
    )
    """The user's preferences stored in a JSON field."""

    __mapper_args__ = {"version_id_col": version_id}

    login_info = db.relationship(
        "LoginInformation", back_populates="user", uselist=False, lazy="joined"
    )

    blocked_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    verified_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    def __init__(self, *args, **kwargs):
        """Constructor."""
        self.verified_at = (
            datetime.utcnow()
            if current_app.config.get("ACCOUNTS_DEFAULT_USERS_VERIFIED")
            else None
        )
        user_profile = kwargs.pop("user_profile", {})
        preferences = kwargs.pop("preferences", {})
        preferences.setdefault(
            "visibility",
            current_app.config.get("ACCOUNTS_DEFAULT_USER_VISIBILITY", "restricted"),
        )
        preferences.setdefault(
            "email_visibility",
            current_app.config.get("ACCOUNTS_DEFAULT_EMAIL_VISIBILITY", "restricted"),
        )
        preferences.setdefault(
            "locale",
            current_app.config.get("BABEL_DEFAULT_LOCALE", "en"),
        )
        preferences.setdefault(
            "timezone",
            current_app.config.get("BABEL_DEFAULT_TIMEZONE", "Europe/Zurich"),
        )
        super().__init__(*args, **kwargs)
        self.user_profile = user_profile
        self.preferences = preferences

    @hybrid_property
    def username(self):
        """Get username."""
        return self._displayname

    @username.setter
    def username(self, username):
        """Set username.

        .. note:: The username will be converted to lowercase.
                  The display name will contain the original version.
        """
        if username is None:
            # if the username can't be validated, a ValueError will be raised
            self._displayname = None
            self._username = None
        else:
            validate_username(username)
            self._displayname = username
            self._username = username.lower()

    @username.comparator
    def username(cls):
        return CaseInsensitiveComparator(cls._username)

    @hybrid_property
    def email(self):
        """Get email."""
        return self._email

    @email.setter
    def email(self, email):
        """Set lowercase email."""
        self._email = email.lower()
        prefix, domain = split_emailaddr(email)
        self.domain = domain

    @hybrid_property
    def user_profile(self):
        """Get the user profile."""
        # NOTE: accessing this property requires an initialized app for config
        if self._user_profile is None:
            return None
        elif not isinstance(self._user_profile, UserProfileDict):
            return UserProfileDict(**self._user_profile)

        return self._user_profile

    @user_profile.setter
    def user_profile(self, value):
        """Set the user profile."""
        if value is None:
            self._user_profile = None
        else:
            self._user_profile = UserProfileDict(**value)

    @hybrid_property
    def preferences(self):
        """Get the user preferences."""
        # NOTE: accessing this property requires an initialized app for config
        if self._preferences is None:
            return None
        elif not isinstance(self._preferences, UserPreferenceDict):
            return UserPreferenceDict(**self._preferences)

        return self._preferences

    @preferences.setter
    def preferences(self, value):
        """Set the user preferences."""
        if value is None:
            self._preferences = None
        else:
            self._preferences = UserPreferenceDict(**value)
            refresh()

    def _get_login_info_attr(self, attr_name):
        if self.login_info is None:
            return None
        return getattr(self.login_info, attr_name)

    def _set_login_info_attr(self, attr_name, value):
        if self.login_info is None:
            self.login_info = LoginInformation()
        setattr(self.login_info, attr_name, value)

    @property
    def current_login_at(self):
        """When user logged into the current session."""
        return self._get_login_info_attr("current_login_at")

    @property
    def current_login_ip(self):
        """Current user IP address."""
        return self._get_login_info_attr("current_login_ip")

    @property
    def last_login_at(self):
        """When the user logged-in for the last time."""
        return self._get_login_info_attr("last_login_at")

    @property
    def last_login_ip(self):
        """Last user IP address."""
        return self._get_login_info_attr("last_login_ip")

    @property
    def login_count(self):
        """Count how many times the user logged in."""
        return self._get_login_info_attr("login_count")

    @current_login_at.setter
    def current_login_at(self, value):
        return self._set_login_info_attr("current_login_at", value)

    @current_login_ip.setter
    def current_login_ip(self, value):
        return self._set_login_info_attr("current_login_ip", value)

    @last_login_at.setter
    def last_login_at(self, value):
        return self._set_login_info_attr("last_login_at", value)

    @last_login_ip.setter
    def last_login_ip(self, value):
        return self._set_login_info_attr("last_login_ip", value)

    @login_count.setter
    def login_count(self, value):
        return self._set_login_info_attr("login_count", value)

    def __str__(self):
        """Representation."""
        return "User <id={0.id}, email={0.email}>".format(self)


class LoginInformation(db.Model):
    """Login information for a user."""

    __tablename__ = "accounts_user_login_information"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(User.id, name="fk_accounts_login_information_user_id"),
        primary_key=True,
    )
    """ID of user to whom this information belongs."""

    user = db.relationship("User", back_populates="login_info")
    """User to whom this information belongs."""

    last_login_at = db.Column(db.DateTime)
    """When the user logged-in for the last time."""

    current_login_at = db.Column(db.DateTime)
    """When user logged into the current session."""

    last_login_ip = db.Column(IPAddressType, nullable=True)
    """Last user IP address."""

    current_login_ip = db.Column(IPAddressType, nullable=True)
    """Current user IP address."""

    login_count = db.Column(db.Integer)
    """Count how many times the user logged in."""

    @validates("last_login_ip", "current_login_ip")
    def validate_ip(self, key, value):
        """Hack untrackable IP addresses."""
        # NOTE Flask-Security stores 'untrackable' value to IPAddressType
        #      field. This incorrect value causes ValueError on loading
        #      user object.
        if value == "untrackable":  # pragma: no cover
            value = None
        return value


class SessionActivity(db.Model, Timestamp):
    """User Session Activity model.

    Instances of this model correspond to a session belonging to a user.
    """

    __tablename__ = "accounts_user_session_activity"

    sid_s = db.Column(db.String(255), primary_key=True)
    """Serialized Session ID. Used as the session's key in the kv-session
    store employed by `flask-kvsession`.
    Named here as it is in `flask-kvsession` to avoid confusion.
    """

    user_id = db.Column(
        db.Integer, db.ForeignKey(User.id, name="fk_accounts_session_activity_user_id")
    )
    """ID of user to whom this session belongs."""

    user = db.relationship(User, backref="active_sessions")

    ip = db.Column(db.String(80), nullable=True)
    """IP address."""

    country = db.Column(db.String(3), nullable=True)
    """Country name."""

    browser = db.Column(db.String(80), nullable=True)
    """User browser."""

    browser_version = db.Column(db.String(30), nullable=True)
    """Browser version."""

    os = db.Column(db.String(80), nullable=True)
    """User operative system name."""

    device = db.Column(db.String(80), nullable=True)
    """User device."""

    @classmethod
    def query_by_expired(cls):
        """Query to select all expired sessions."""
        lifetime = current_app.permanent_session_lifetime
        expired_moment = datetime.utcnow() - lifetime
        return cls.query.filter(cls.created < expired_moment)

    @classmethod
    def query_by_user(cls, user_id):
        """Query to select user sessions."""
        return cls.query.filter_by(user_id=user_id)

    @classmethod
    def is_current(cls, sid_s):
        """Check if the session is the current one."""
        return session.sid_s == sid_s


class UserIdentity(db.Model, Timestamp):
    """Represent a UserIdentity record."""

    __tablename__ = "accounts_useridentity"

    id = db.Column(db.String(255), primary_key=True, nullable=False)
    method = db.Column(db.String(255), primary_key=True, nullable=False)
    id_user = db.Column(db.Integer(), db.ForeignKey(User.id), nullable=False)

    user = db.relationship(User, backref="external_identifiers")

    __table_args__ = (
        db.Index("accounts_useridentity_id_user_method", id_user, method, unique=True),
    )

    @classmethod
    def get_user(cls, method, external_id):
        """Get the user for a given identity."""
        identity = cls.query.filter_by(id=external_id, method=method).one_or_none()
        if identity is not None:
            return identity.user
        return None

    @classmethod
    def create(cls, user, method, external_id):
        """Link a user to an external id.

        :param user: A :class:`invenio_accounts.models.User` instance.
        :param method: The identity source (e.g. orcid, github)
        :param method: The external identifier.
        :raises AlreadyLinkedError: Raised if already exists a link.
        """
        try:
            with db.session.begin_nested():
                db.session.add(cls(id=external_id, method=method, id_user=user.id))
        except IntegrityError:
            raise AlreadyLinkedError(
                # dict used for backward compatibility (came from oauthclient)
                user,
                {"id": external_id, "method": method},
            )

    @classmethod
    def delete_by_external_id(cls, method, external_id):
        """Unlink a user from an external id."""
        with db.session.begin_nested():
            cls.query.filter_by(id=external_id, method=method).delete()

    @classmethod
    def delete_by_user(cls, method, user):
        """Unlink a user from an external id."""
        with db.session.begin_nested():
            cls.query.filter_by(id_user=user.id, method=method).delete()


class DomainOrg(db.Model):
    """Domain organisation."""

    __tablename__ = "accounts_domain_org"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    pid = db.Column(db.String(255), unique=True, nullable=True)
    """Persistent identifier for organisation."""

    name = db.Column(db.String(255), nullable=False)
    """Name of organisation."""

    json = db.Column(
        json_field,
        default=lambda: dict(),
        nullable=False,
    )
    """Store additional metadata about the organisation."""

    parent_id = db.Column(
        db.Integer(), db.ForeignKey("accounts_domain_org.id"), nullable=True
    )
    """Link to parent organisation."""

    parent = db.relationship("DomainOrg", remote_side=[id])
    """Relationship to parent."""

    @classmethod
    def create(cls, pid, name, json=None, parent=None):
        """Create a domain organisation."""
        obj = cls(pid=pid, name=name, json=json or {}, parent=parent)
        db.session.add(obj)
        return obj


class DomainCategory(db.Model):
    """Model for storing different domain categories."""

    __tablename__ = "accounts_domain_category"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)

    label = db.Column(db.String(255))

    @classmethod
    def create(cls, label):
        """Create a new domain category."""
        obj = cls(label=label)
        db.session.add(obj)
        return obj

    @classmethod
    def get(cls, label):
        """Get a domain category."""
        return cls.query.filter_by(label=label).one_or_none()


class Domain(db.Model, Timestamp):
    """User domains model."""

    __tablename__ = "accounts_domains"

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    """Domain ID"""

    _domain = db.Column("domain", db.String(255), unique=True, nullable=False)
    """Domain name."""

    tld = db.Column(db.String(255), nullable=False)
    """Top-level domain."""

    status = db.Column(
        ChoiceType(DomainStatus, impl=db.Integer()),
        default=DomainStatus.new,
        nullable=False,
    )
    """Status of domain.

    Use to control possibility and capability of users registering with this domain.
    """

    flagged = db.Column(db.Boolean(), default=False, nullable=False)
    """Flag domain - used by automatic processes to flag domain."""

    flagged_source = db.Column(db.String(255), default="", nullable=False)
    """Source of flag."""

    org_id = db.Column(db.Integer(), db.ForeignKey(DomainOrg.id), nullable=True)
    """Organisation associated with domain."""

    org = db.relationship("DomainOrg", backref="domains")

    # spammer, mail-provider, organisation, company
    category = db.Column(db.Integer(), db.ForeignKey(DomainCategory.id), nullable=True)
    """Category of domain."""

    category_name = db.relationship("DomainCategory", backref="domains")
    """Relationship to category"""

    num_users = db.Column(db.Integer(), default=0, nullable=False)
    """Computed property to store number of users in domain."""

    num_active = db.Column(db.Integer(), default=0, nullable=False)
    """Computed property to store number of active users in domain."""

    num_inactive = db.Column(db.Integer(), default=0, nullable=False)
    """Computed property to store number of inactive users in domain."""

    num_confirmed = db.Column(db.Integer(), default=0, nullable=False)
    """Computed property to store number of confirmed users in domain."""

    num_verified = db.Column(db.Integer(), default=0, nullable=False)
    """Computed property to store number of verified users in domain."""

    num_blocked = db.Column(db.Integer(), default=0, nullable=False)
    """Computed property to store number of blocked users in domain."""

    @classmethod
    def create(
        cls,
        domain,
        status=DomainStatus.new,
        flagged=False,
        flagged_source="",
        org=None,
        category=None,
    ):
        """Create a new domain."""
        obj = cls(
            domain=domain,
            status=status,
            flagged=flagged,
            flagged_source=flagged_source,
            org=org,
            category=category,
        )
        db.session.add(obj)
        return obj

    @hybrid_property
    def domain(self):
        """Get domain name."""
        return self._domain

    @domain.setter
    def domain(self, value):
        """Set domain name."""
        if value[-1] == ".":
            value = value[:-1]
        self._domain = value.lower()
        self.tld = self._domain.split(".")[-1]
