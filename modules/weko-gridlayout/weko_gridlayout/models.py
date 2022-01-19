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
from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy import Sequence
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy_utils.models import Timestamp
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
            current_app.logger.error(ex)
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


class WidgetItem(db.Model, Timestamp):
    """Database for WidgetItem."""

    __tablename__ = 'widget_items'

    widget_id = db.Column(db.Integer, primary_key=True, nullable=False)
    """Widget identifier."""

    repository_id = db.Column(db.String(100), nullable=False)
    """Community identifier."""

    widget_type = db.Column(db.String(100), nullable=False)
    """Widget type."""

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
    """Widget settings"""

    is_enabled = db.Column(db.Boolean(name='enable'), default=True)
    """Enable widget"""

    is_deleted = db.Column(db.Boolean(name='deleted'), default=False)
    """Delete flag."""

    locked = db.Column(db.Boolean(name='locked'), default=False)
    """Edit locked"""

    locked_by_user = db.Column(db.Integer(), db.ForeignKey(User.id),
                               nullable=True, default=None)
    """Locked by user"""

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
        is_commit = False
        if not session:
            is_commit = True
            session = db.session
        widget = cls.get_by_id(widget_item_id)
        if not widget:
            return
        for k, v in widget_data.items():
            setattr(widget, k, v)
        session.merge(widget)
        if is_commit:
            try:
                with session.begin_nested():
                    session.merge(widget)
                session.commit()
                return widget
            except Exception as ex:
                session.rollback()
                current_app.logger.error(ex)
                return False
        else:
            session.merge(widget)
            return widget

    @classmethod
    def update_setting_by_id(cls, widget_id, settings):
        """Update widget setting by widget id.

        :param widget_id:
        :param settings:
        :return: True if update successful
        """
        try:
            widget_item = cls.get_by_id(widget_id)
            with db.session.begin_nested():
                widget_item.settings = settings
                db.session.merge(widget_item)
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            return False

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
        setattr(widget, 'is_deleted', True)
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
        """Get list widget multi language data by widget ID.

        Arguments:
            widget_id {Integer} -- The widget id

        Returns:
            data -- List widget multi language data

        """
        list_data = cls.query.filter_by(
            widget_id=widget_id, is_deleted=False).all()
        return list_data

    @classmethod
    def update_by_id(cls, widget_item_id, data):
        """Update widget multi language data by id.

        Arguments:
            id {Integer} -- The id
            data {WidgetMultiLangData} -- The Widget multi language data

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
            setattr(data, 'is_deleted', True)
        return True


class WidgetDesignSetting(db.Model):
    """Database for admin WidgetDesignSetting."""

    __tablename__ = 'widget_design_setting'

    repository_id = db.Column(db.String(100), nullable=False, primary_key=True)

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
                current_app.logger.error(ex)
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
            current_app.logger.error(ex)
            return False


class WidgetDesignPage(db.Model):
    """Database for menu pages."""

    __tablename__ = 'widget_design_page'

    id = db.Column(db.Integer, primary_key=True, nullable=False)

    title = db.Column(db.String(100), nullable=True)

    repository_id = db.Column(db.String(100), nullable=False)

    url = db.Column(db.String(100), nullable=False, unique=True)

    template_name = db.Column(  # May be used in the future
        db.String(100),
        nullable=True
    )

    content = db.Column(db.Text(), nullable=True, default='')

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

    is_main_layout = db.Column(db.Boolean(name='is_main_layout'), nullable=True)

    multi_lang_data = db.relationship(
        'WidgetDesignPageMultiLangData',
        backref='widget_design_page',
        cascade='all, delete-orphan',
        collection_class=attribute_mapped_collection('lang_code')
    )

    @classmethod
    def create_or_update(cls, repository_id, title, url, content,
                         page_id=0, settings=None, multi_lang_data={},
                         is_main_layout=False):
        """Insert new widget design page.

        :param repository_id: Identifier of the repository
        :param title: Page title
        :param url: Page URL
        :param content: HTML content
        :param page_id: Page identifier
        :param settings: Page widget setting data
        :param multi_lang_data: Multi language data
        :param is_main_layout: Main layout flash
        :return: True if successful, otherwise False
        """
        try:
            prev = cls.query.filter_by(id=int(page_id)).one_or_none()
            if prev:
                repository_id = prev.repository_id
            page = prev or WidgetDesignPage()

            if not repository_id:
                raise ValueError('Invalid repository.')
            if not url:
                raise ValueError('URL cannot be empty.')

            cur_urls = map(
                lambda design_page: design_page.url,
                db.session.query(cls).add_columns(WidgetDesignPage.url)
                .filter(WidgetDesignPage.id != page_id).all()
            )
            if url in cur_urls:
                raise ValueError('URL is already in use.')

            with db.session.begin_nested():
                page.repository_id = repository_id
                page.title = title
                page.url = url
                page.content = content
                if settings is not None:
                    page.settings = settings
                page.is_main_layout = is_main_layout
                for lang in multi_lang_data:
                    page.multi_lang_data[lang] = \
                        WidgetDesignPageMultiLangData(
                            lang, multi_lang_data[lang])
                db.session.merge(page)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise ex

    @classmethod
    def delete(cls, page_id):
        """Delete widget design page.

        :param page_id: Page model's id
        :return: True if successful or False
        """
        if page_id:
            try:
                with db.session.begin_nested():
                    cls.query.filter_by(id=int(page_id)).delete()
                db.session.commit()
                return True
            except BaseException as ex:
                db.session.rollback()
                current_app.logger.error(ex)
                raise ex
        return False

    @classmethod
    def update_settings(cls, page_id, settings=None):
        """Update design page setting.

        :param page_id: Identifier of the page.
        :param settings: Page widget setting data.
        :return: True if successful, otherwise False.
        """
        try:
            page = cls.query.filter_by(id=int(page_id)).one_or_none()
            if page:
                with db.session.begin_nested():
                    page.settings = settings
                    db.session.merge(page)
                db.session.commit()
                return True
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise ex
        return False

    @classmethod
    def update_settings_by_repository_id(cls, repository_id, settings=None):
        """Update design page setting by repository id.

        Note: ALL pages belonging to repository will have the same settings.
        Could be used to make all pages uniform in design.
        :param repository_id: Repository id.
        :param settings: Page widget setting data.
        :return: True if successful, otherwise False.
        """
        try:
            pages = cls.query.filter_by(repository_id=int(repository_id)).all()
            for page in pages:
                with db.session.begin_nested():
                    page.settings = settings
                    db.session.merge(page)
                db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            return False

    @classmethod
    def get_all(cls):
        """
        Get all pages.

        :return: List of all pages.
        """
        return db.session.query(cls).all()

    @classmethod
    def get_all_valid(cls):
        """
        Get all pages with widget settings.

        :return: List of all pages.
        """
        return db.session.query(cls).filter(cls.settings is not None).all()

    @classmethod
    def get_by_id(cls, id):
        """
        Get widget page by id.

        Raises error if not found etc.
        :return: Single page object or exception raised.
        """
        return db.session.query(cls).filter_by(id=int(id)).one()

    @classmethod
    def get_by_id_or_none(cls, id):
        """
        Get widget page by id without raising exception.

        :return: Single page object or none.
        """
        return db.session.query(cls).filter_by(id=int(id)).one_or_none()

    @classmethod
    def get_by_url(cls, url):
        """
        Get widget page by url.

        :return: Single page objects or none.
        """
        return db.session.query(cls).filter_by(url=url).one()

    @classmethod
    def get_by_repository_id(cls, repository_id):
        """
        Get widget pages for community/repo.

        :return: Multiple page objects or empty list.
        """
        return db.session.query(cls).filter_by(
            repository_id=repository_id).all()


class WidgetDesignPageMultiLangData(db.Model):
    """Table for widget multiple language data for pages."""

    __tablename__ = 'widget_design_page_multi_lang_data'

    id = db.Column(db.Integer, primary_key=True, nullable=False)

    widget_design_page_id = db.Column(
        db.Integer(),
        db.ForeignKey(WidgetDesignPage.id),
        nullable=False
    )

    lang_code = db.Column(db.String(3), nullable=False)

    title = db.Column(db.String(100))

    def __init__(self, lang_code, title):
        """Initialize."""
        self.lang_code = lang_code
        self.title = title

    @classmethod
    def get_by_id(cls, id):
        """Get widget multi language data by id."""
        return cls.query.filter_by(id=id).one_or_none()

    @classmethod
    def delete_by_page_id(cls, page_id):
        """Delete widget page multi language by page id.

        :param page_id: Page model's id
        :return: True if successful or False
        """
        if page_id:
            try:
                with db.session.begin_nested():
                    cls.query.filter_by(widget_design_page_id=page_id).delete()
                db.session.commit()
                return True
            except Exception as ex:
                db.session.rollback()
                current_app.logger.error(ex)
                raise ex
        return False


__all__ = ([
    'WidgetType',
    'WidgetItem',
    'WidgetDesignSetting',
    'WidgetMultiLangData',
    'WidgetDesignPage',
    'WidgetDesignPageMultiLangData'
])
