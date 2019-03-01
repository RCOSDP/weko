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

"""Database models for weko-admin."""

from datetime import datetime

from flask import current_app, json
from invenio_db import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils.types import JSONType
from sqlalchemy.sql import func
from sqlalchemy.dialects import mysql, postgresql


class SessionLifetime(db.Model):
    """Session Lifetime model.

    Stores session life_time create_date for Session.
    """

    __tablename__ = 'session_lifetime'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    _lifetime = db.Column('lifetime', db.Integer,
                          nullable=False, default=30)
    """ Session Life Time default units: minutes """

    create_date = db.Column(db.DateTime, default=datetime.now)

    is_delete = db.Column(db.Boolean(name='delete'),
                          default=False, nullable=False)

    @hybrid_property
    def lifetime(self):
        """
        Get lifetime.

        :return: Lifetime.
        """
        return self._lifetime

    @lifetime.setter
    def lifetime(self, lifetime):
        """
        Set lifetime.

        :param lifetime:
        :return: Lifetime.
        """
        self._lifetime = lifetime

    def create(self, lifetime=None):
        """
        Save session lifetime.

        :param lifetime: default None
        :return:
        """
        try:
            with db.session.begin_nested():
                if lifetime:
                    self.lifetime = lifetime
                self.is_delete = False
                db.session.add(self)
            db.session.commit()
        except BaseException:
            db.session.rollback()
            raise
        return self

    @classmethod
    def get_validtime(cls):
        """Get valid lifetime.

        :returns: A :class:`~weko_admin.models.SessionLifetime` instance
            or ``None``.
        """
        return cls.query.filter_by(is_delete=False).one_or_none()

    @property
    def is_anonymous(self):
        """Return whether this UserProfile is anonymous."""
        return False


class SearchManagement(db.Model):
    """Search setting model"""

    __tablename__ = 'search_management'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    default_dis_num = db.Column( db.Integer, nullable=False, default=20)
    """ Default display number of search results"""

    default_dis_sort_index = db.Column( db.Text, nullable=True, default="")
    """ Default display sort of index search"""

    default_dis_sort_keyword = db.Column(db.Text, nullable=True, default="")
    """ Default display sort of keyword search"""

    sort_setting = db.Column(
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
    """ The list of sort setting"""

    search_conditions = db.Column(
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
    """ The list of search condition """

    search_setting_all = db.Column(
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
    """ The list of search condition """

    create_date = db.Column(db.DateTime, default=datetime.now)
    """Create Time"""

    @classmethod
    def create(cls, data):
        """Create data"""
        try:
            dataObj = SearchManagement()
            with db.session.begin_nested():
                dataObj.default_dis_num = data.get('dlt_dis_num_selected')
                dataObj.default_dis_sort_index = data.get('dlt_index_sort_selected')
                dataObj.default_dis_sort_keyword = data.get('dlt_keyword_sort_selected')
                dataObj.sort_setting = data.get('sort_options')
                dataObj.search_conditions = data.get('detail_condition')
                dataObj.search_setting_all= data
                db.session.add(dataObj)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise
        return cls

    @classmethod
    def get(cls):
        """Get setting"""
        id = db.session.query(func.max(SearchManagement.id)).first()[0]
        if id is None:
            return  None
        return cls.query.filter_by(id=id).one_or_none()

    @classmethod
    def update(cls, id, data):
        """Update setting"""
        try:
            with db.session.begin_nested():
                setting_data = cls.query.filter_by(id=id).one()
                setting_data.default_dis_num = data.get('dlt_dis_num_selected')
                setting_data.default_dis_sort_index = data.get('dlt_index_sort_selected')
                setting_data.default_dis_sort_keyword = data.get('dlt_keyword_sort_selected')
                setting_data.sort_setting = data.get('sort_options')
                setting_data.search_conditions = data.get('detail_condition')
                setting_data.search_setting_all = data
                db.session.merge(setting_data)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise
        return cls

__all__ = ([
    'SearchManagement',
])
