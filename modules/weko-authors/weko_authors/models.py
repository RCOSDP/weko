# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Models for weko-index-tree."""

import json
from datetime import datetime

from flask import current_app
from invenio_db import db
from sqlalchemy import Sequence
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType
from weko_records.models import Timestamp

# from invenio_records.models import RecordMetadata


class Authors(db.Model, Timestamp):
    """
    Represent an index.

    The Index object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'authors'

    id = db.Column(db.BigInteger, primary_key=True, unique=True)
    """id of the authors."""

    gather_flg = db.Column(
        db.BigInteger,
        primary_key=False,
        unique=False,
        default=0)
    """gather_flg of the authors."""

    is_deleted = db.Column(
        db.Boolean(name='is_deleted'),
        nullable=False,
        default=False)
    """Delete status of the authors."""

    json = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: dict(),
        nullable=True
    )
    """json for author info"""
    
    repository_id = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: dict(),
        nullable=True
    )
    """repository_id of the authors"""

    @classmethod
    def get_sequence(cls, session):
        """Get author id next sequence.

        :param session: Session
        :return: Next sequence.
        """
        if not session:
            session = db.session
        seq = Sequence('authors_id_seq')
        next_id = session.execute(seq)
        return next_id

    @classmethod
    def get_emails_by_id(cls, author_id):
        """Get emails of author by id.

        Arguments:
            author_id {int} -- author id

        Returns:
            list -- emails

        """
        try:
            author = cls.query.filter_by(id=author_id).one_or_none()
            if not author:
                return []
            json_data = author.json
            email_info = json_data.get('emailInfo')
            return [e.get('email') for e in email_info if e.get('email')]
        except Exception:
            return []

    @classmethod
    def get_author_by_id(cls, author_id):
        """Get author data by id.

        Arguments:
            author_id {string} -- author id

        Returns:
            dictionary -- author data

        """
        try:
            with db.session.begin_nested():
                author = cls.query.filter_by(id=author_id).one_or_none()
                if not author:
                    return None
                json_data = author.json
                return json_data
        except Exception:
            return None


class AuthorsPrefixSettings(db.Model, Timestamp):
    """Represent an author prefix setting."""

    __tablename__ = 'authors_prefix_settings'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    """ Id of the authors prefix settings."""

    name = db.Column(db.Text, nullable=False)
    """ The name of prefix organization."""

    scheme = db.Column(db.Text, nullable=True, unique=True)
    """ The scheme of prefix organization."""

    url = db.Column(db.Text, nullable=True)
    """ The url of prefix organization."""

    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    """ Created date."""

    updated = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)
    """ Updated date."""
    
    repository_id = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: dict(),
        nullable=True
    )
    """repository_id of prefix settings"""

    @classmethod
    def create(cls, name, scheme, url):
        """Create settings."""
        try:
            data = AuthorsPrefixSettings()
            with db.session.begin_nested():
                data.name = name
                data.url = url
                if scheme:
                    data.scheme = scheme.strip()
                db.session.add(data)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise
        return cls

    @classmethod
    def update(cls, id, name, scheme, url):
        """Update settings."""
        try:
            with db.session.begin_nested():
                data = cls.query.filter_by(id=id).first()
                data.name = name
                data.url = url
                if scheme:
                    data.scheme = scheme.strip()
                db.session.merge(data)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise
        return cls

    @classmethod
    def delete(cls, id):
        """Delete settings."""
        try:
            with db.session.begin_nested():
                cls.query.filter_by(id=id).delete()
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise
        return cls


class AuthorsAffiliationSettings(db.Model, Timestamp):
    """Represent an author affiliation setting."""

    __tablename__ = 'authors_affiliation_settings'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    """ Id of the authors affiliation settings."""

    name = db.Column(db.Text, nullable=False)
    """ The name of affiliation organization."""

    scheme = db.Column(db.Text, nullable=True, unique=True)
    """ The scheme of affiliation organization."""

    url = db.Column(db.Text, nullable=True)
    """ The url of affiliation organization."""

    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    """ Created date."""

    updated = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)
    """ Updated date."""
    
    repository_id = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: dict(),
        nullable=True
    )
    """repository_id of affiliation organization."""

    @classmethod
    def create(cls, name, scheme, url):
        """Create settings."""
        try:
            data = AuthorsAffiliationSettings()
            with db.session.begin_nested():
                data.name = name
                data.url = url
                if scheme:
                    data.scheme = scheme.strip()
                db.session.add(data)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise
        return cls

    @classmethod
    def update(cls, id, name, scheme, url):
        """Update settings."""
        try:
            with db.session.begin_nested():
                data = cls.query.filter_by(id=id).first()
                data.name = name
                data.url = url
                if scheme:
                    data.scheme = scheme.strip()
                db.session.merge(data)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise
        return cls

    @classmethod
    def delete(cls, id):
        """Delete settings."""
        try:
            with db.session.begin_nested():
                cls.query.filter_by(id=id).delete()
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise
        return cls

__all__ = ('Authors', 'AuthorsPrefixSettings', 'AuthorsAffiliationSettings')
