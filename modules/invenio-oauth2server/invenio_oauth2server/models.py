# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAuth2Server models."""

from __future__ import absolute_import, print_function

import six
from flask import current_app
from flask_babelex import lazy_gettext as _
from flask_login import current_user
from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy.schema import Index
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types import URLType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from werkzeug.security import gen_salt
from wtforms import validators

from .errors import ScopeDoesNotExists
from .proxies import current_oauth2server
from .validators import validate_redirect_uri, validate_scopes


def secret_key():
    """Return secret key as bytearray."""
    return current_app.config['SECRET_KEY'].encode('utf-8')


class NoneAesEngine(AesEngine):
    """Filter None values from encrypting."""

    def encrypt(self, value):
        """Encrypt a value on the way in."""
        if value is not None:
            return super(NoneAesEngine, self).encrypt(value)

    def decrypt(self, value):
        """Decrypt value on the way out."""
        if value is not None:
            return super(NoneAesEngine, self).decrypt(value)


class OAuthUserProxy(object):
    """Proxy object to an Invenio User."""

    def __init__(self, user):
        """Initialize proxy object with user instance."""
        self._user = user

    def __getattr__(self, name):
        """Pass any undefined attribute to the underlying object."""
        return getattr(self._user, name)

    def __getstate__(self):
        """Return the id."""
        return self.id

    def __setstate__(self, state):
        """Set user info."""
        self._user = current_app.extensions['security'].datastore.get_user(
            state)

    @property
    def id(self):
        """Return user identifier."""
        return self._user.get_id()

    def check_password(self, password):
        """Check user password."""
        return self.password == password

    @classmethod
    def get_current_user(cls):
        """Return an instance of current user object."""
        return cls(current_user._get_current_object())


class Scope(object):
    """OAuth scope definition."""

    def __init__(self, id_, help_text='', group='', internal=False):
        """Initialize scope values."""
        self.id = id_
        self.group = group
        self.help_text = help_text
        self.is_internal = internal


class Client(db.Model):
    """A client is the app which want to use the resource of a user.

    It is suggested that the client is registered by a user on your site, but
    it is not required.

    The client should contain at least these information:

        client_id: A random string
        client_secret: A random string
        client_type: A string represents if it is confidential
        redirect_uris: A list of redirect uris
        default_redirect_uri: One of the redirect uris
        default_scopes: Default scopes of the client

    But it could be better, if you implemented:

        allowed_grant_types: A list of grant types
        allowed_response_types: A list of response types
        validate_scopes: A function to validate scopes
    """

    __tablename__ = 'oauth2server_client'

    name = db.Column(
        db.String(40),
        info=dict(
            label=_('Name'),
            description=_('Name of application (displayed to users).'),
            validators=[validators.DataRequired()]
        )
    )
    """Human readable name of the application."""

    description = db.Column(
        db.Text(),
        default=u'',
        info=dict(
            label=_('Description'),
            description=_('Optional. Description of the application'
                          ' (displayed to users).'),
        )
    )
    """Human readable description."""

    website = db.Column(
        URLType(),
        info=dict(
            label=_('Website URL'),
            description=_('URL of your application (displayed to users).'),
        ),
        default=u'',
    )

    user_id = db.Column(
        db.ForeignKey(User.id, ondelete='CASCADE',),
        nullable=True, index=True)
    """Creator of the client application."""

    client_id = db.Column(db.String(255), primary_key=True)
    """Client application ID."""

    client_secret = db.Column(
        db.String(255), unique=True, index=True, nullable=False
    )
    """Client application secret."""

    is_confidential = db.Column(
        db.Boolean(name='is_confidential'),
        default=True
    )
    """Determine if client application is public or not."""

    is_internal = db.Column(db.Boolean(name='is_internal'), default=False)
    """Determins if client application is an internal application."""

    _redirect_uris = db.Column(db.Text)
    """A newline-separated list of redirect URIs. First is the default URI."""

    _default_scopes = db.Column(db.Text)
    """A space-separated list of default scopes of the client.

    The value of the scope parameter is expressed as a list of space-delimited,
    case-sensitive strings.
    """

    user = db.relationship(
        User,
        backref=db.backref(
            "oauth2clients",
            cascade="all, delete-orphan",
        )
    )
    """Relationship to user."""

    @property
    def allowed_grant_types(self):
        """Return allowed grant types."""
        return current_app.config['OAUTH2SERVER_ALLOWED_GRANT_TYPES']

    @property
    def allowed_response_types(self):
        """Return allowed response types."""
        return current_app.config['OAUTH2SERVER_ALLOWED_RESPONSE_TYPES']

    # def validate_scopes(self, scopes):
    #     return self._validate_scopes

    @property
    def client_type(self):
        """Return client type."""
        if self.is_confidential:
            return 'confidential'
        return 'public'

    @property
    def redirect_uris(self):
        """Return redirect uris."""
        if self._redirect_uris:
            return self._redirect_uris.splitlines()
        return []

    @redirect_uris.setter
    def redirect_uris(self, value):
        """Validate and store redirect URIs for client."""
        if isinstance(value, six.text_type):
            value = value.split("\n")

        value = [v.strip() for v in value]

        for v in value:
            validate_redirect_uri(v)

        self._redirect_uris = "\n".join(value) or ""

    @property
    def default_redirect_uri(self):
        """Return default redirect uri."""
        try:
            return self.redirect_uris[0]
        except IndexError:
            pass

    @property
    def default_scopes(self):
        """List of default scopes for client."""
        if self._default_scopes:
            return self._default_scopes.split(" ")
        return []

    @default_scopes.setter
    def default_scopes(self, scopes):
        """Set default scopes for client."""
        validate_scopes(scopes)
        self._default_scopes = " ".join(set(scopes)) if scopes else ""

    def validate_scopes(self, scopes):
        """Validate if client is allowed to access scopes."""
        try:
            validate_scopes(scopes)
            return True
        except ScopeDoesNotExists:
            return False

    def gen_salt(self):
        """Generate salt."""
        self.reset_client_id()
        self.reset_client_secret()

    def reset_client_id(self):
        """Reset client id."""
        self.client_id = gen_salt(
            current_app.config.get('OAUTH2SERVER_CLIENT_ID_SALT_LEN')
        )

    def reset_client_secret(self):
        """Reset client secret."""
        self.client_secret = gen_salt(
            current_app.config.get('OAUTH2SERVER_CLIENT_SECRET_SALT_LEN')
        )

    @property
    def get_users(self):
        """Get number of users."""
        no_users = Token.query.filter_by(
            client_id=self.client_id,
            is_personal=False,
            is_internal=False
        ).count()
        return no_users

    @classmethod
    def get_client_id_by_user_id(cls, user_id):
        """Get client_id, name by user_id. """
        query = db.session.query(cls).with_entities(cls.client_id, cls.name).filter(cls.user_id == user_id)
        return query.all()

    @classmethod
    def get_client_id_all(cls):
        """Get client_id all. """
        query = db.session.query(cls).with_entities(cls.client_id, cls.name)
        return query.all()

    @classmethod
    def get_name_by_client_id(cls, client_id):
        """Get name by client_id. """
        query = db.session.query(cls).with_entities(cls.name).filter(cls.client_id == client_id)
        return query.first()

    @classmethod
    def get_user_id_by_client_id(cls, client_id):
        """Get user_id by client_id. """
        query = db.session.query(cls).with_entities(cls.user_id).filter(cls.client_id == client_id)
        return query.first()

class Token(db.Model):
    """A bearer token is the final token that can be used by the client."""

    __tablename__ = 'oauth2server_token'
    __table_args__ = (
        Index('ix_oauth2server_token_access_token',
              'access_token',
              unique=True,
              mysql_length=255),
        Index('ix_oauth2server_token_refresh_token',
              'refresh_token',
              unique=True,
              mysql_length=255),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """Object ID."""

    client_id = db.Column(
        db.String(255),
        db.ForeignKey(Client.client_id, ondelete='CASCADE'),
        nullable=False, index=True
    )
    """Foreign key to client application."""

    client = db.relationship(
        'Client',
        backref=db.backref(
            'oauth2tokens',
            cascade="all, delete-orphan"
        ))
    """SQLAlchemy relationship to client application."""

    user_id = db.Column(
        db.Integer, db.ForeignKey(User.id, ondelete='CASCADE'), nullable=True,
        index=True
    )
    """Foreign key to user."""

    user = db.relationship(
        User,
        backref=db.backref(
            "oauth2tokens",
            cascade="all, delete-orphan",
        )
    )
    """SQLAlchemy relationship to user."""

    token_type = db.Column(db.String(255), default='bearer')
    """Token type - only bearer is supported at the moment."""

    access_token = db.Column(
        EncryptedType(
            type_in=db.String(255),
            key=secret_key,
        ),
    )

    refresh_token = db.Column(
        EncryptedType(
            type_in=db.String(255),
            key=secret_key,
            engine=NoneAesEngine,
        ),
        nullable=True,
    )

    expires = db.Column(db.DateTime, nullable=True)

    _scopes = db.Column(db.Text)

    is_personal = db.Column(db.Boolean(name='is_personal'), default=False)
    """Personal accesss token."""

    is_internal = db.Column(db.Boolean(name='is_internal'), default=False)
    """Determines if token is an internally generated token."""

    @property
    def scopes(self):
        """Return all scopes.

        :returns: A list of scopes.
        """
        if self._scopes:
            return self._scopes.split()
        return []

    @scopes.setter
    def scopes(self, scopes):
        """Set scopes.

        :param scopes: The list of scopes.
        """
        validate_scopes(scopes)
        self._scopes = " ".join(set(scopes)) if scopes else ""

    def get_visible_scopes(self):
        """Get list of non-internal scopes for token.

        :returns: A list of scopes.
        """
        return [k for k, s in current_oauth2server.scope_choices()
                if k in self.scopes]

    @classmethod
    def create_personal(cls, name, user_id, scopes=None, is_internal=False):
        """Create a personal access token.

        A token that is bound to a specific user and which doesn't expire, i.e.
        similar to the concept of an API key.

        :param name: Client name.
        :param user_id: User ID.
        :param scopes: The list of permitted scopes. (Default: ``None``)
        :param is_internal: If ``True`` it's a internal access token.
             (Default: ``False``)
        :returns: A new access token.
        """
        with db.session.begin_nested():
            scopes = " ".join(scopes) if scopes else ""

            c = Client(
                name=name,
                user_id=user_id,
                is_internal=True,
                is_confidential=False,
                _default_scopes=scopes
            )
            c.gen_salt()

            t = Token(
                client_id=c.client_id,
                user_id=user_id,
                access_token=gen_salt(
                    current_app.config.get(
                        'OAUTH2SERVER_TOKEN_PERSONAL_SALT_LEN')
                ),
                expires=None,
                _scopes=scopes,
                is_personal=True,
                is_internal=is_internal,
            )

            db.session.add(c)
            db.session.add(t)

        return t
