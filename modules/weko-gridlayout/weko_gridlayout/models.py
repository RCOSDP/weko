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

"""Database models for weko-gridlayout."""

from flask import current_app
from invenio_db import db
from sqlalchemy import Sequence
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType


class WidgetType(db.Model):
    """Database for WidgetType."""

    __tablename__ = 'widget_type'

    type_id = db.Column(db.String(100), primary_key=True, nullable=False)

    type_name = db.Column(db.String(100), nullable=False)

    @classmethod
    def create(cls, data):
        """Create data."""
        try:
            data_obj = WidgetType()
            with db.session.begin_nested():
                data_obj.type_id = data.get('type_id')
                data_obj.type_name = data.get('type_name')
                db.session.add(data_obj)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise
        return cls

    @classmethod
    def get(cls, widget_type_id):
        """Get setting."""
        return cls.query.filter_by(type_id=str(widget_type_id)).one_or_none()

    @classmethod
    def get_all_widget_types(cls):
        """
        Get all widget_type in widget_type table.

        :return: List of widget_type object.
        """
        widget_types = db.session.query(WidgetType).all()

        if widget_types is None:
            return None

        return widget_types


class WidgetItem(db.Model):
    """Database for WidgetItem."""

    __tablename__ = 'widget_items'

    widget_id = db.Column(db.Integer,
                          primary_key=True,
                          nullable=False)
    repository_id = db.Column(db.String(100),
                              nullable=False)
    widget_type = db.Column(db.String(100),
                            db.ForeignKey(WidgetType.type_id),
                            nullable=False)
    settings = db.Column(db.JSON().with_variant(
                                               postgresql.JSONB(
                                                   none_as_null=True
                                                   ),
                                               'postgresql',)
                                  .with_variant(JSONType(),
                                                'sqlite',)
                                  .with_variant(JSONType(),
                                                'mysql',),
                         default=lambda: dict(),
                         nullable=True)
    browsing_role = db.Column(db.Text,
                              nullable=True)
    edit_role = db.Column(db.Text,
                          nullable=True)
    is_enabled = db.Column(db.Boolean(name='enable'),
                           default=True)
    is_deleted = db.Column(db.Boolean(name='deleted'),
                           default=False)

    #
    # Relation
    #
    widgettype = db.relationship(WidgetType,
                                 backref=db.backref('repositories',
                                                    cascade='all, \
                                                    delete-orphan'))

    #
    # Query Operation
    #
    @classmethod
    def get_by_id(cls, widget_item_id):
        """Get a widget item by id."""
        widget = cls.query.filter_by(widget_id=widget_item_id).one_or_none()
        return widget

    @classmethod
    def get_id_by_repository_and_type(cls, repository, widget_type):
        """Get id by repository id and widget type.

        :param repository: Repository id
        :param widget_type: Widget type
        :return:Widget Item
        """
        widget_data = cls.query.filter_by(
            repository_id=repository,
            widget_type=widget_type,
            is_deleted=False
            ).all()
        if not widget_data:
            return None

        list_id = list()
        for data in widget_data:
            list_id.append(data.widget_id)
        return list_id

    @classmethod
    def get_sequence(cls, session):
        """Get widget item next sequence.

        :param session: Session
        :return: Next sequence.
        """
        if not session:
            session = db.session
        seq = Sequence('widget_items_widget_id_seq')
        next_id = session.execute(seq)
        return next_id

    @classmethod
    def create(cls, widget_data, session):
        """Create widget item.

        :param widget_data: widget data
        :param session: session
        :return:
        """
        if not session:
            return None
        data = cls(**widget_data)
        session.add(data)

    @classmethod
    def update_by_id(cls, widget_item_id, widget_data, session=None):
        """Update the widget by id.

        Arguments:
            widget_item_id {Integer} -- Id of widget
            widget_data {Dictionary} -- data

        Returns:
            widget -- if success

        """
        if not session:
            session = db.session
        widget = cls.get_by_id(widget_item_id)
        if not widget:
            return
        for k, v in widget_data.items():
            setattr(widget, k, v)
        session.merge(widget)
        return widget

    @classmethod
    def delete_by_id(cls, widget_id, session):
        """Delete the widget by id.

        Arguments:
            widget_id {Integer} -- The widget id

        Returns:
            widget -- If success

        """
        widget = cls.get_by_id(widget_id)
        if not widget:
            return
        setattr(widget, 'is_deleted', 'True')
        session.merge(widget)
        return widget


class WidgetMultiLangData(db.Model):
    """Database for widget multiple language data."""

    __tablename__ = 'widget_multi_lang_data'

    id = db.Column(db.Integer,
                   primary_key=True,
                   nullable=False)
    widget_id = db.Column(db.Integer,
                          nullable=False)
    lang_code = db.Column(db.String(3),
                          nullable=False)
    label = db.Column(db.String(100),
                      nullable=False)
    description_data = db.Column(db.JSON().with_variant(
                                                postgresql.JSONB(
                                                    none_as_null=True
                                                ),
                                                'postgresql',)
                                          .with_variant(
                                              JSONType(),
                                              'sqlite',)
                                          .with_variant(
                                              JSONType(),
                                              'mysql',),
                                 default=lambda: dict(),
                                 nullable=True)

    is_deleted = db.Column(db.Boolean(name='deleted'),
                           default=False)

    #
    # Query Operation
    #
    @classmethod
    def get_by_id(cls, widget_multi_lang_id):
        """Get widget multi language data by id.

        Arguments:
            widget_multilanguage_id {Integer} -- The ID

        Returns:
            data -- Widget multi language data

        """
        data = cls.query.filter_by(id=widget_multi_lang_id).one_or_none()
        return data

    @classmethod
    def create(cls, data, session):
        """Create Widget multi language data.

        :param data: WWidget multi language data
        :param session: session
        :return:
        """
        if not data:
            return None
        obj = cls(**data)
        session.add(obj)
        return obj

    @classmethod
    def get_by_widget_id(cls, widget_id):
        """Get list widget multilanguage data by widget ID.

        Arguments:
            widget_id {Integer} -- The widget id

        Returns:
            data -- List widget multilanguage data

        """
        list_data = cls.query.filter_by(widget_id=widget_id).all()
        return list_data

    @classmethod
    def update_by_id(cls, widget_item_id, data):
        """Update widget multilanguage data by id.

        Arguments:
            id {Integer} -- The id
            data {WidgetMultiLangData} -- The Widget multilanguage data

        Returns:
            True -- If deleted

        """
        widget_multi_lang = cls.get_by_id(widget_item_id)
        if not data:
            return
        for k, v in data.items():
            setattr(widget_multi_lang, k, v)
        db.session.merge(widget_multi_lang)
        return widget_multi_lang

    @classmethod
    def delete_by_widget_id(cls, widget_id, session):
        """Delete widget by id.

        :param widget_id: id of widget
        :param session: session of delete
        :return:
        """
        if not session:
            session = db.session
        multi_data = cls.get_by_widget_id(widget_id)
        if not multi_data:
            return False
        for data in multi_data:
            setattr(data, 'is_deleted', 'True')
        return True


class WidgetDesignSetting(db.Model):
    """Database for admin WidgetDesignSetting."""

    __tablename__ = 'widget_design_setting'

    repository_id = db.Column(db.String(100),
                              nullable=False, primary_key=True)

    settings = db.Column(
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

    @classmethod
    def select_all(cls):
        """Get all information about widget setting in database.

        :return: Widget setting list.
        """
        query_result = cls.query.all()
        result = []
        if query_result:
            for record in query_result:
                data = dict()
                data['repository_id'] = record.repository_id
                data['settings'] = record.settings
                result.append(data)
        return result

    @classmethod
    def select_by_repository_id(cls, repository_id):
        """Get widget setting value by repository id.

        :param repository_id: Identifier of the repository
        :return: Widget setting
        """
        query_result = cls.query.filter_by(
            repository_id=str(repository_id)).one_or_none()
        data = {}
        if query_result is not None:
            data['repository_id'] = query_result.repository_id
            data['settings'] = query_result.settings

        return data

    @classmethod
    def update(cls, repository_id, settings):
        """Update widget setting.

        :param repository_id: Identifier of the repository
        :param settings: The setting data
        :return: True if success, otherwise False
        """
        query_result = cls.query.filter_by(
            repository_id=str(repository_id)).one_or_none()
        if query_result is None:
            return False
        else:
            try:
                with db.session.begin_nested():
                    query_result.settings = settings
                    db.session.merge(query_result)
                db.session.commit()
                return True
            except Exception as ex:
                current_app.logger.debug(ex)
                db.session.rollback()
                return False

    @classmethod
    def create(cls, repository_id, settings=None):
        """Insert new widget setting.

        :param repository_id: Identifier of the repository
        :param settings: The setting data
        :return: True if success, otherwise False
        """
        try:
            widget_setting = WidgetDesignSetting()
            with db.session.begin_nested():
                if repository_id is not None:
                    widget_setting.repository_id = repository_id
                    widget_setting.settings = settings
                db.session.add(widget_setting)
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            return False


__all__ = ([
    'WidgetType',
    'WidgetItem',
    'WidgetDesignSetting',
    'WidgetMultiLangData'
])
