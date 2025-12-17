# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database models for accounts."""

from __future__ import absolute_import, print_function

from datetime import datetime

from flask import current_app, session
from flask_security import RoleMixin, UserMixin
from invenio_db import db
from sqlalchemy.orm import validates
from sqlalchemy_utils import IPAddressType, Timestamp

from invenio_mail.models import MailTemplateUsers

userrole = db.Table(
    'accounts_userrole',
    db.Column('user_id', db.Integer(), db.ForeignKey(
        'accounts_user.id', name='fk_accounts_userrole_user_id')),
    db.Column('role_id', db.Integer(), db.ForeignKey(
        'accounts_role.id', name='fk_accounts_userrole_role_id')),
)
"""Relationship between users and roles."""


class Role(db.Model, RoleMixin):
    """Role data model."""

    __tablename__ = "accounts_role"

    id = db.Column(db.Integer(), primary_key=True)

    name = db.Column(db.String(80), unique=True)
    """Role name."""

    description = db.Column(db.String(255))
    """Role description."""

    def __str__(self):
        """Return the name and description of the role."""
        return '{0.name} - {0.description}'.format(self)


class User(db.Model, UserMixin):
    """User data model."""

    __tablename__ = "accounts_user"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True)
    """User email."""

    password = db.Column(db.String(255))
    """User password."""

    active = db.Column(db.Boolean(name='active'))
    """Flag to say if the user is active or not ."""

    confirmed_at = db.Column(db.DateTime)
    """When the user confirmed the email address."""

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

    roles = db.relationship('Role', secondary=userrole,
                            backref=db.backref('users', lazy='dynamic'))
    """List of the user's roles."""

    template = db.relationship('MailTemplateUsers', cascade='all, delete')

    @validates('last_login_ip', 'current_login_ip')
    def validate_ip(self, key, value):
        """Hack untrackable IP addresses."""
        # NOTE Flask-Security stores 'untrackable' value to IPAddressType
        #      field. This incorrect value causes ValueError on loading
        #      user object.
        if value == 'untrackable':  # pragma: no cover
            value = None
        return value

    def __str__(self):
        """Representation."""
        return 'User <id={0.id}, email={0.email}>'.format(self)

    @classmethod
    def get_email_by_id(cls, id):
        """Get id, name by user_id. """
        query = db.session.query(cls).with_entities(cls.email).filter(cls.id == id)
        return query.first()

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

    user_id = db.Column(db.Integer, db.ForeignKey(
        User.id, name='fk_accounts_session_activity_user_id'))
    """ID of user to whom this session belongs."""

    user = db.relationship(User, backref='active_sessions')

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

    orgniazation_name = db.Column(db.String(255), nullable=True)
    """User Organization."""

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
