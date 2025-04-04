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

from flask import current_app, escape, request
from invenio_db import db
from sqlalchemy import Sequence, asc
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import desc
from sqlalchemy_utils import Timestamp
from sqlalchemy_utils.types import JSONType


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
        return cls.query.filter_by(is_delete=False).first()

    @property
    def is_anonymous(self):
        """Return whether this UserProfile is anonymous."""
        return False


class SearchManagement(db.Model):
    """Search setting model."""

    __tablename__ = 'search_management'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    default_dis_num = db.Column(db.Integer, nullable=False, default=20)
    """ Default display number of search results"""

    default_dis_sort_index = db.Column(db.Text, nullable=True, default="")
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

    display_control = db.Column(
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
    """ The status of display control """

    init_disp_setting = db.Column(
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
    """ The Main Screen Initial Display Setting """

    create_date = db.Column(db.DateTime, default=datetime.now)
    """Create Time"""

    @classmethod
    def create(cls, data):
        """Create data."""
        try:
            data_obj = SearchManagement()
            with db.session.begin_nested():
                data_obj.default_dis_num = data.get('dlt_dis_num_selected')
                data_obj.default_dis_sort_index = data.get(
                    'dlt_index_sort_selected')
                data_obj.default_dis_sort_keyword = data.get(
                    'dlt_keyword_sort_selected')
                data_obj.sort_setting = data.get('sort_options')
                data_obj.search_conditions = data.get('detail_condition')
                data_obj.display_control = data.get('display_control')
                data_obj.init_disp_setting = data.get('init_disp_setting')
                data_obj.search_setting_all = data
                db.session.add(data_obj)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise
        return cls

    @classmethod
    def get(cls):
        """Get setting."""
        _id = db.session.query(func.max(SearchManagement.id)).first()[0]
        if _id is None:
            return None
        return cls.query.filter_by(id=_id).one_or_none()

    @classmethod
    def update(cls, id, data):
        """Update setting."""
        try:
            with db.session.begin_nested():
                setting_data = cls.query.filter_by(id=id).one()
                setting_data.default_dis_num = data.get('dlt_dis_num_selected')
                setting_data.default_dis_sort_index = data.get(
                    'dlt_index_sort_selected')
                setting_data.default_dis_sort_keyword = data.get(
                    'dlt_keyword_sort_selected')
                setting_data.sort_setting = data.get('sort_options')
                setting_data.search_conditions = data.get('detail_condition')
                setting_data.display_control = data.get('display_control')
                setting_data.init_disp_setting = data.get('init_disp_setting')
                setting_data.search_setting_all = data
                db.session.merge(setting_data)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise
        return cls


class AdminLangSettings(db.Model):
    """System Language Display Setting.

    Stored target language and registered language
    """

    __tablename__ = 'admin_lang_settings'

    lang_code = db.Column(db.String(3), primary_key=True, nullable=False,
                          unique=True)

    lang_name = db.Column(db.String(30), nullable=False)

    is_registered = db.Column(db.Boolean(name='registered'), default=True)

    sequence = db.Column(db.Integer, default=0)

    is_active = db.Column(db.Boolean(name='active'), default=True)

    @classmethod
    def parse_result(cls, in_result):
        """Parse results."""
        obj = {}
        for k in in_result:
            record = dict()
            record['lang_code'] = k.lang_code
            record['lang_name'] = k.lang_name
            record['is_registered'] = k.is_registered
            record['sequence'] = k.sequence
            record['is_active'] = k.is_active
            obj[k.lang_code] = record

        json_list = []
        for key in obj:
            json_list.append({
                'lang_code': '{0}'.format(obj[key]['lang_code']),
                'lang_name': '{0}'.format(obj[key]['lang_name']),
                'is_registered': obj[key]['is_registered'],
                'sequence': obj[key]['sequence']
            })
        sorted_list = sorted(json_list, key=lambda k: k['sequence'])
        return sorted_list

    @classmethod
    def load_lang(cls):
        """Get language list.

        :return: A list of language
        """
        lang_list = cls.query.all()

        return cls.parse_result(lang_list)

    @classmethod
    def create(cls, lang_code, lang_name, is_registered, sequence, is_active):
        """Create language."""
        try:
            data_obj = AdminLangSettings()
            with db.session.begin_nested():
                data_obj.lang_code = lang_code
                data_obj.lang_name = lang_name
                data_obj.is_registered = is_registered
                data_obj.sequence = sequence
                data_obj.is_active = is_active
                db.session.add(data_obj)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise
        return cls

    @classmethod
    def update_lang(cls, lang_code=None, lang_name=None, is_registered=None,
                    sequence=None, is_active=None):
        """Save list language into database.

        :param lang_code: input language code
        :param lang_name: input language name
        :param is_registered: input boolean is language registered
        :param sequence: input order number of language
        :param is_active: input boolean is active of language
        :return: Updated record
        """
        with db.session.begin_nested():
            lang_setting_data = cls.query.filter_by(lang_code=lang_code).one()
            if lang_name is not None:
                lang_setting_data.lang_name = lang_name
            if is_registered is not None:
                lang_setting_data.is_registered = is_registered
            if sequence is not None:
                lang_setting_data.sequence = sequence
            if is_active is not None:
                lang_setting_data.is_active = is_active
            db.session.merge(lang_setting_data)

    @classmethod
    def get_registered_language(cls):
        """Get registered languages.

        :return: All language have registered
        """
        result = cls.query.filter_by(is_registered=True).order_by(
            asc('admin_lang_settings_sequence'))

        return cls.parse_result(result)

    @classmethod
    def get_active_language(cls):
        """Get active languages.

        :return: All languages have activated
        """
        result = cls.query.filter_by(is_active=True).order_by(
            asc('admin_lang_settings_sequence'))
        return cls.parse_result(result)


class ApiCertificate(db.Model):
    """Database for API Certificate."""

    __tablename__ = 'api_certificate'

    api_code = db.Column(db.String(3), primary_key=True, nullable=False,
                         unique=True)

    api_name = db.Column(db.String(25), nullable=False, unique=True)

    cert_data = db.Column(
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
        """Get all information about certificates in database.

        :return: list of pair (api short name, api full name, certificate data)
        """
        query_result = cls.query.all()
        result = []
        for record in query_result:
            data = dict()
            data['api_code'] = record.api_code
            data['api_name'] = record.api_name
            data['cert_data'] = record.cert_data
            result.append(data)
        return result

    @classmethod
    def select_by_api_code(cls, api_code):
        """Get certificate value by certificate type.

        :param api_code: input api short name
        :return: certificate data corresponding with api code
        """
        query_result = cls.query.filter_by(api_code=api_code).one_or_none()
        data = {}
        if query_result is not None:
            data['api_code'] = query_result.api_code
            data['api_name'] = query_result.api_name
            data['cert_data'] = query_result.cert_data

            return data
        else:
            return None

    @classmethod
    def update_cert_data(cls, api_code, cert_data):
        """Update certification data.

        Overwrite if certificate existed,
        otherwise insert new certificate into database.

        :param api_code: input api short name
        :param cert_data: input certificate value
        :return: true if success, otherwise false
        """
        query_result = cls.query.filter_by(api_code=api_code).one_or_none()
        # Update in case certificate already existed in database
        if query_result is None:
            return False
        else:
            try:
                with db.session.begin_nested():
                    query_result.cert_data = cert_data
                    db.session.merge(query_result)
                db.session.commit()
                return True
            except Exception as ex:
                current_app.logger.debug(ex)
                db.session.rollback()
                return False

    @classmethod
    def insert_new_api_cert(cls, api_code, api_name, cert_data=None):
        """Insert new certificate.

        :param api_code: input api code
        :param api_name: input api name
        :param cert_data: input certificate value with json format
        :return: True if success, otherwise False
        """
        try:
            data_obj = ApiCertificate()
            with db.session.begin_nested():
                if api_code is not None:
                    data_obj.api_code = api_code
                    data_obj.api_name = api_name
                if cert_data is not None:
                    data_obj.cert_data = cert_data
                db.session.add(data_obj)
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            return False

    @classmethod
    def update_api_cert(cls, api_code, api_name, cert_data):
        """Update API certification.

        Overwrite if certificate existed,
        otherwise insert new certificate into database.

        :param api_code: input api code
        :param api_name: input api name
        :param cert_data: input certificate value
        :return: true if success, otherwise false
        """
        # Get current api data
        query_result = cls.query.filter_by(api_code=api_code).one_or_none()

        if query_result is None:
            return False
        else:
            try:
                with db.session.begin_nested():
                    query_result.api_name = api_name
                    query_result.cert_data = cert_data
                    db.session.merge(query_result)
                db.session.commit()
                return True
            except Exception as ex:
                current_app.logger.debug(ex)
                db.session.rollback()
                return False


class StatisticUnit(db.Model):
    """Statistic Report Unit."""

    __tablename__ = 'stats_report_unit'

    unit_id = db.Column(db.String(100), primary_key=True, nullable=False,
                        unique=True)

    unit_name = db.Column(db.String(255), nullable=False)

    @classmethod
    def get_all_stats_report_unit(cls):
        """Get all stats report unit.

        :return: List of unit
        """
        query_result = cls.query.all()
        result = []
        for res in query_result:
            data = dict()
            data['id'] = res.unit_id
            data['data'] = res.unit_name
            result.append(data)
        return result

    @classmethod
    def create(cls, unit_id, unit_name):
        """Create new unit.

        :param unit_id: The unit ID
        :param unit_name: The unit name
        :return: Unit if create succesfully
        """
        try:
            data_obj = StatisticUnit()
            with db.session.begin_nested():
                data_obj.unit_id = unit_id
                data_obj.unit_name = unit_name
                db.session.add(data_obj)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise

        return cls


class StatisticTarget(db.Model):
    """Statistic Report Target."""

    __tablename__ = 'stats_report_target'

    target_id = db.Column(db.String(100), primary_key=True, nullable=False,
                          unique=True)

    target_name = db.Column(db.String(255), nullable=False)

    target_unit = db.Column(db.String(100), nullable=True)

    @classmethod
    def get_all_stats_report_target(cls):
        """Get all stats report target.

        :return: List of target
        """
        query_result = cls.query.all()
        result = []
        for res in query_result:
            data = dict()
            data['id'] = res.target_id
            data['data'] = res.target_name
            data['unit'] = res.target_unit
            result.append(data)
        return result

    @classmethod
    def get_target_by_id(cls, target_id):
        """Get target by ID.

        :param target_id: the target ID
        :return: the target
        """
        query_result = cls.query.filter_by(target_id=target_id).one_or_none()
        return query_result

    @classmethod
    def create(cls, target_id, target_name, target_unit):
        """Create new target.

        :param target_id: The target ID
        :param target_name: The target name
        :param target_unit: The target unit
        :return: The Target if create succesfully
        """
        try:
            data_obj = StatisticTarget()
            with db.session.begin_nested():
                data_obj.target_id = target_id
                data_obj.target_name = target_name
                data_obj.target_unit = target_unit
                db.session.add(data_obj)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise

        return cls


class LogAnalysisRestrictedIpAddress(db.Model):
    """Represent restricted addresses to be restricted from logging.

    The SiteLicenseIpAddress object contains a ``created`` and  a
    ``updated`` properties that are automatically updated.
    """

    __tablename__ = 'loganalysis_restricted_ip_address'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )

    ip_address = db.Column(
        db.String(16),
        nullable=False,
        unique=True
    )

    @classmethod
    def get_all(cls):
        """Get all Ip Addresses.

        :return:  list.
        """
        try:
            all = cls.query.all()
        except Exception as ex:
            current_app.logger.debug(ex)
            all = []
            raise
        return all

    @classmethod
    def update_table(cls, ip_addresses):
        """Delete all rows and insert new ones."""
        try:
            with db.session.begin_nested():
                all_addresses = [LogAnalysisRestrictedIpAddress(ip_address=i)
                                 for i in ip_addresses]
                LogAnalysisRestrictedIpAddress.query.delete()
                db.session.add_all(all_addresses)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise
        return cls

    def __iter__(self):
        """TODO: __iter__."""
        for name in dir(LogAnalysisRestrictedIpAddress):
            if not name.startswith('__') and not name.startswith('_'):
                value = getattr(self, name)
                if isinstance(value, str):
                    yield (name, value)


class LogAnalysisRestrictedCrawlerList(db.Model):
    """Represent restricted users from txt list to be restricted from logging.

    The LogAnalysisRestrictedCrawlerList object contains a ``created`` and  a
    ``updated`` properties that are automatically updated.
    """

    __tablename__ = 'loganalysis_restricted_crawler_list'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )

    list_url = db.Column(
        db.String(255),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean(name='activated'),
        default=True
    )

    @classmethod
    def get_all(cls):
        """Get all crawler lists.

        :return: All crawler lists.
        """
        try:
            all = cls.query.order_by(asc(cls.id)).all()
        except Exception as ex:
            current_app.logger.debug(ex)
            all = []
            raise
        return all

    @classmethod
    def get_all_active(cls):
        """Get all active crawler lists.

        :return: All active crawler lists.
        """
        try:
            all = cls.query.filter(cls.is_active.is_(True)) \
                .filter(func.length(cls.list_url) > 0).all()
        except Exception as ex:
            current_app.logger.debug(ex)
            all = []
            raise
        return all

    @classmethod
    def add_list(cls, crawler_lists):
        """Add all crawler lists."""
        for list_url in crawler_lists:
            try:
                with db.session.begin_nested():
                    record = LogAnalysisRestrictedCrawlerList(
                        list_url=list_url)
                    db.session.add(record)
                db.session.commit()
            except Exception as ex:
                current_app.logger.debug(ex)
                db.session.rollback()
                raise
        return cls

    @classmethod
    def update_or_insert_list(cls, crawler_list):
        """Update or insert LogAnalysisRestrictedCrawlerList list."""
        for data in crawler_list:
            try:
                new_list = data.get('list_url', '')
                id = data.get('id', 0)
                is_active = data.get('is_active', True)
                with db.session.begin_nested():
                    current_record = cls.query.filter_by(id=id).one_or_none()
                    if current_record:
                        current_record.list_url = new_list
                        current_record.is_active = is_active
                        db.session.merge(current_record)
                    else:
                        db.session.add(
                            LogAnalysisRestrictedCrawlerList(
                                list_url=new_list))
                db.session.commit()
            except BaseException as ex:
                current_app.logger.debug(ex)
                db.session.rollback()
                raise
        return cls

    def __iter__(self):
        """TODO: __iter__."""
        for name in dir(LogAnalysisRestrictedCrawlerList):
            if not name.startswith('__') and not name.startswith('_'):
                value = getattr(self, name)
                if isinstance(value, str):
                    yield (name, value)


class BillingPermission(db.Model):
    """Database for Billing Permission."""

    __tablename__ = 'billing_permission'

    user_id = db.Column(
        db.Integer(),
        primary_key=True,
        nullable=False,
        unique=True
    )

    is_active = db.Column(
        db.Boolean(name='active'),
        default=True,
        nullable=False
    )

    @classmethod
    def create(cls, user_id, is_active=True):
        """Create new user can access billing file.

        :param user_id: user's id
        :param is_active: access state
        :return: Unit if create succesfully
        """
        try:
            obj = BillingPermission()
            with db.session.begin_nested():
                obj.user_id = user_id
                obj.is_active = is_active
                db.session.add(obj)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise

        return cls

    @classmethod
    def activation(cls, user_id, is_active):
        """Change access state of user.

        :param user_id: user's id
        :param is_active: access state
        :return: Updated records
        """
        try:
            with db.session.begin_nested():
                new_data_flg = False
                billing_data = cls.query.filter_by(
                    user_id=user_id).one_or_none()
                if not billing_data:
                    new_data_flg = True
                    billing_data = BillingPermission()
                    billing_data.user_id = user_id
                billing_data.is_active = is_active
                if new_data_flg:
                    db.session.add(billing_data)
                else:
                    db.session.merge(billing_data)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise

        return cls

    @classmethod
    def get_billing_information_by_id(cls, user_id):
        """Get billing information by user id.

        :param user_id: user's id
        :return: Record or none
        """
        try:
            billing_information = cls.query.filter_by(
                user_id=user_id).one_or_none()
        except Exception as ex:
            current_app.logger.debug(ex)
            raise
        return billing_information


class StatisticsEmail(db.Model):
    """Save Email Address."""

    __tablename__ = 'stats_email_address'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email_address = db.Column(db.String(255), nullable=False)
    repository_id = db.Column(db.String(100), nullable=True, default='Root Index')

    @classmethod
    def insert_email_address(cls, email_address ,repository_id):
        """Insert Email Address."""
        try:
            data_obj = StatisticsEmail()
            with db.session.begin_nested():
                data_obj.email_address = email_address
                data_obj.repository_id = repository_id
                db.session.add(data_obj)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise ex
        return cls

    @classmethod
    def get_all_emails(cls):
        """Get all recipient emails as a list."""
        all_objects = cls.query.all()
        return [row.email_address for row in all_objects]
    
    @classmethod
    def get_emails_by_repo(cls, repository_id):
        """Get all recipient emails as a list."""
        all_objects = cls.query.filter_by(repository_id=repository_id).all()
        return [row.email_address for row in all_objects]

    @classmethod
    def get_all(cls):
        """Get all email address."""
        try:
            all = cls.query.all()
        except Exception as ex:
            current_app.logger.debug(ex)
            all = []
            raise
        return all

    @classmethod
    def delete_all_row(cls):
        """Delete all."""
        try:
            with db.session.begin_nested():
                delete_all = cls.query.delete()
            db.session.commit()
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            raise ex
        return delete_all
    
    @classmethod
    def delete_by_repo(cls, repository_id):
        """Delete all."""
        try:
            with db.session.begin_nested():
                delete_by_repo = cls.query.filter_by(repository_id=repository_id).delete()
            db.session.commit()
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            raise ex
        return delete_by_repo


class RankingSettings(db.Model):
    """Ranking settings."""

    __tablename__ = 'ranking_settings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    is_show = db.Column(db.Boolean(name='show'), nullable=False, default=False)

    new_item_period = db.Column(db.Integer, nullable=False, default=14)

    statistical_period = db.Column(db.Integer, nullable=False, default=365)

    display_rank = db.Column(db.Integer, nullable=False, default=10)

    rankings = db.Column(
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
    def get(cls, id=0):
        """Get ranking settings."""
        return cls.query.filter_by(id=id).first()

    @classmethod
    def update(cls, id=0, data=None):
        """Update/Create ranking settings."""
        try:
            with db.session.begin_nested():
                new_data_flag = False
                settings = cls.query.filter_by(id=id).first()
                if not settings:
                    settings = RankingSettings()
                    new_data_flag = True
                settings.id = id
                settings.is_show = data.is_show
                settings.new_item_period = data.new_item_period
                settings.statistical_period = data.statistical_period
                settings.display_rank = data.display_rank
                settings.rankings = data.rankings
                if new_data_flag:
                    db.session.add(settings)
                else:
                    db.session.merge(settings)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise
        return cls

    @classmethod
    def delete(cls, id=0):
        """Delete settings."""
        try:
            with db.session.begin_nested():
                cls.query.filter_by(id=id).delete()
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise ex
        return cls


class FeedbackMailSetting(db.Model, Timestamp):
    """Feedback email setting.

    The FeedbackMailSetting object contains a ``created``, a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'feedback_email_setting'

    id = db.Column(
        db.Integer,
        primary_key=True)
    """FeedbackMailSetting identifier."""

    account_author = db.Column(
        db.Text,
        nullable=False
    )
    """Author identifier."""

    manual_mail = db.Column(
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

    is_sending_feedback = db.Column(
        db.Boolean(name='is_sending_feedback'),
        nullable=False,
        default=False)
    """Setting to send or not send feedback mail."""

    root_url = db.Column(
        db.String(100)
    )
    """Store system root url."""
    
    repository_id = db.Column(
        db.String(100),
        nullable=False,
        default='Root Index'
    )

    @classmethod
    def create(cls, account_author, manual_mail,
               is_sending_feedback, root_url, repo_id):
        """Create a feedback mail setting.

        Arguments:
            account_author {string} -- author data
            is_sending_feedback {bool} -- is sending feedback

        Returns:
            bool -- True if success

        """
        try:
            new_record = FeedbackMailSetting()
            with db.session.begin_nested():
                new_record.account_author = account_author
                new_record.manual_mail = manual_mail
                new_record.is_sending_feedback = is_sending_feedback
                new_record.root_url = root_url
                new_record.repository_id = repo_id
                db.session.add(new_record)
            db.session.commit()
        except BaseException:
            db.session.rollback()
            return False
        return True

    @classmethod
    def get_all_feedback_email_setting(cls):
        """Get all feedback email setting.

        Returns:
            class -- this class

        """
        try:
            with db.session.no_autoflush:
                feedback_settings = cls.query.all()
                return feedback_settings
        except Exception:
            return []
        
    @classmethod
    def get_feedback_email_setting_by_repo(cls, repo_id):
        """Get all feedback email setting.

        Returns:
            class -- this class

        """
        if not repo_id:
            repo_id = 'Root Index'
        try:
            with db.session.no_autoflush:
                feedback_settings = cls.query.filter_by(repository_id=repo_id).all()
                return feedback_settings
        except Exception:
            return []

    @classmethod
    def update(cls, account_author,
               manual_mail, is_sending_feedback, root_url, repo_id):
        """Update existed feedback mail setting.

        Arguments:
            account_author {string} -- author data
            is_sending_feedback {bool} -- is sending feedback

        Keyword Arguments:
            id {int} -- the id (default: {1})

        Returns:
            bool -- True if success

        """
        try:
            with db.session.begin_nested():
                settings = cls.query.filter_by(repository_id=repo_id).first()
                settings.account_author = account_author
                settings.manual_mail = manual_mail
                settings.is_sending_feedback = is_sending_feedback
                settings.root_url = root_url
                settings.repository_id = repo_id
                db.session.merge(settings)
            db.session.commit()
            return True
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            return False

    @classmethod
    def delete(cls, id=1):
        """Delete the settings. default delete first setting.

        Keyword Arguments:
            id {int} -- The setting id (default: {1})

        Returns:
            bool -- true if delete success

        """
        try:
            with db.session.begin_nested():
                cls.query.delete()
            db.session.commit()
            return True
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            return False

    @classmethod
    def delete_by_repo(cls, repo_id):
        """Delete the settings. default delete first setting.

        Keyword Arguments:
            id {int} -- The setting id (default: {1})

        Returns:
            bool -- true if delete success

        """
        try:
            with db.session.begin_nested():
                cls.query.filter_by(repository_id=repo_id).delete()
            db.session.commit()
            return True
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            return False


class AdminSettings(db.Model):
    """settings."""

    __tablename__ = 'admin_settings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String(30), unique=True)

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

    class Dict2Obj(object):
        """Dict to obj."""

        def __init__(self, data):
            """Init object."""
            for key in data:
                setattr(self, key, data[key])

    def _get_count():
        count = db.session.query(db.func.max(AdminSettings.id)).first()
        if count[0]:
            return count[0]
        return 0

    @classmethod
    def get(cls, name, dict_to_object=True):
        """Get settings by name."""
        try:
            admin_setting_object = cls.query.filter_by(name=name).first()
            if admin_setting_object:
                if dict_to_object:
                    return cls.Dict2Obj(admin_setting_object.settings)
                else:
                    return admin_setting_object.settings
        except Exception as ex:
            current_app.logger.debug('dict to object')
            current_app.logger.error(ex)
        return None

    @classmethod
    def update(cls, name, settings, id=None):
        """Update/Create settings."""
        try:
            with db.session.begin_nested():
                new_setting_flag = False
                o = cls.query.filter_by(name=name).first()
                if not o:
                    o = AdminSettings()
                    o.id = AdminSettings._get_count() + 1
                    new_setting_flag = True
                if id:
                    o.id = id
                o.name = name
                o.settings = settings
                if new_setting_flag:
                    db.session.add(o)
                else:
                    db.session.merge(o)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise

        return cls

    @classmethod
    def delete(cls, name):
        """Delete settings."""
        try:
            with db.session.begin_nested():
                cls.query.filter_by(name=name).delete()
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise ex

        return cls


class SiteInfo(db.Model):
    """Site information.

    The SiteInfo object contains a ``created``, a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'site_info'

    id = db.Column(
        db.Integer,
        primary_key=True)
    """SiteInfo identifier."""

    copy_right = db.Column(
        db.Text,
        nullable=True
    )
    """copy right."""

    description = db.Column(
        db.Text,
        nullable=True
    )
    """description."""

    keyword = db.Column(
        db.Text,
        nullable=True
    )
    """keyword."""

    favicon = db.Column(
        db.Text,
        nullable=True
    )

    favicon_name = db.Column(
        db.Text,
        nullable=True
    )
    """url of favicon file."""

    site_name = db.Column(
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
        nullable=False
    )
    """site name info."""

    notify = db.Column(
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
        nullable=False
    )
    """notify."""

    google_tracking_id_user = db.Column(
        db.Text,
        nullable=True
    )
    """tracking id."""

    addthis_user_id = db.Column(
        db.Text,
        nullable=True
    )
    """add this id."""

    ogp_image = db.Column(
        db.Text,
        nullable=True
    )

    ogp_image_name = db.Column(
        db.Text,
        nullable=True
    )
    """url of ogp image file."""

    @classmethod
    def get(cls):
        """Get site infomation."""
        try:
            with db.session.begin_nested():
                query_object = SiteInfo.query.filter_by().one_or_none()
                if query_object:
                    return query_object
                else:
                    return {}
        except SQLAlchemyError as e:
            import traceback
            current_app.logger.error(traceback.format_exc())
            return {}
        except Exception as e:
            import traceback
            current_app.logger.error(traceback.format_exc())
            return {}

    @classmethod
    def update(cls, site_info):
        """Update/Create settings."""
        from invenio_files_rest.utils import update_ogp_image
        try:
            with db.session.begin_nested():
                new_site_info_flag = False
                query_object = SiteInfo.query.filter_by().one_or_none()
                if not query_object:
                    query_object = SiteInfo()
                    new_site_info_flag = True
                site_name = []
                list_site_name = site_info.get('site_name') or []
                for sn in list_site_name:
                    site_name.append({
                        "index": escape(sn.get('index')),
                        "name": escape(sn.get('name').strip()),
                        "language": escape(sn.get('language')),
                    })
                notify = []
                list_notify = site_info.get('notify') or []
                for nt in list_notify:
                    notify.append({
                        "notify_name": escape(nt.get('notify_name').strip()),
                        "language": escape(nt.get('language')),
                    })
                query_object.copy_right = escape(site_info.get(
                    "copy_right").strip())
                query_object.description = escape(site_info.get(
                    "description").strip())
                query_object.keyword = escape(site_info.get("keyword").strip())
                query_object.favicon = escape(site_info.get("favicon").strip())
                query_object.favicon_name = escape(site_info.get(
                    "favicon_name").strip())
                query_object.site_name = site_name
                query_object.notify = notify
                query_object.google_tracking_id_user = escape(site_info.get(
                    "google_tracking_id_user").strip())
                query_object.addthis_user_id = escape(site_info.get(
                    "addthis_user_id").strip())
                ogp_image_data = site_info.get("ogp_image").strip()
                if ogp_image_data and request.url_root not in ogp_image_data:
                    url_ogp_image = update_ogp_image(ogp_image_data,
                                                     query_object.ogp_image)
                    if url_ogp_image:
                        query_object.ogp_image = url_ogp_image
                        query_object.ogp_image_name = escape(
                            site_info.get("ogp_image_name").strip())
                if new_site_info_flag:
                    db.session.add(query_object)
                else:
                    db.session.merge(query_object)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            raise

        return cls


class FeedbackMailHistory(db.Model):
    """History, Logs of sending mail."""

    __tablename__ = 'feedback_mail_history'

    id = db.Column(
        db.Integer,
        primary_key=True,
        nullable=False
    )

    parent_id = db.Column(
        db.Integer
    )

    start_time = db.Column(
        db.DateTime,
        nullable=False
    )

    end_time = db.Column(
        db.DateTime,
        nullable=False
    )

    stats_time = db.Column(
        db.String(7),
        nullable=False
    )

    count = db.Column(
        db.Integer,
        nullable=False
    )

    error = db.Column(
        db.Integer
    )

    is_latest = db.Column(
        db.Boolean(name='lastest'),
        nullable=False
    )
    
    repository_id = db.Column(
        db.String(100),
        nullable=False,
        default='Root Index'
    )

    @classmethod
    def get_by_id(cls, id):
        """Get history by id.

        Arguments:
            id {string} -- The history id

        Returns:
            dictionary -- history data

        """
        result = cls.query.filter_by(id=id).one_or_none()
        return result

    @classmethod
    def get_sequence(cls, session):
        """Get session sequence.

        Arguments:
            session {sessiosn} -- The DB session

        Returns:
            number -- The next id

        """
        if not session:
            session = db.session
        seq = Sequence('feedback_mail_history_id_seq')
        next_id = session.execute(seq)
        return next_id

    @classmethod
    def get_all_history(cls, repo_id=None):
        """Get all history record.

        Returns:
            list -- history

        """
        query = cls.query
        if repo_id:
            query = query.filter_by(repository_id=repo_id)
        return query.order_by(desc(cls.id)).all()

    @classmethod
    def create(cls,
               session,
               id,
               start_time,
               end_time,
               stats_time,
               count,
               error,
               parent_id=None,
               is_latest=True,
               repository_id=None):
        """Create history record.

        Arguments:
            start_time {timestamp} -- Start time
            end_time {timestamp} -- End time
            stats_time {string} -- Statistic time
            count {integer} -- Total sent mail
            error {integer} -- Total failed mail

        Keyword Arguments:
            parent_id {integer} -- Parent id if resend (default: {None})

        """
        if not session:
            session = db.session
        try:
            data = FeedbackMailHistory()
            with session.begin_nested():
                data.id = id
                if parent_id:
                    data.parent_id = parent_id
                data.start_time = start_time
                data.end_time = end_time
                data.stats_time = stats_time
                data.count = count
                data.error = error
                data.is_latest = is_latest
                data.repository_id = repository_id
                session.add(data)
            session.commit()
        except BaseException as ex:
            session.rollback()
            current_app.logger.error(ex)

    @classmethod
    def update_lastest_status(cls, id, status):
        """Update latest status by id.

        Arguments:
            id {string} -- History id
            status {boolean} -- Lastest status

        """
        try:
            with db.session.begin_nested():
                data = cls.query.filter_by(id=id).one_or_none()
                data.is_latest = status
                db.session.merge(data)
            db.session.commit()
        except BaseException as ex:
            db.session.rollback()
            current_app.logger.debug(ex)
            raise


class FeedbackMailFailed(db.Model):
    """Storage of mail which failed to send."""

    __tablename__ = 'feedback_mail_failed'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    history_id = db.Column(
        db.Integer,
        nullable=False
    )

    author_id = db.Column(
        db.String(50)
    )

    mail = db.Column(
        db.String(255),
        nullable=False
    )

    @classmethod
    def get_by_history_id(cls, history_id):
        """Get list mail by history id.

        Arguments:
            history_id {integer} -- The history id

        Returns:
            list -- list of mail

        """
        result = cls.query.filter_by(
            history_id=history_id
        ).all()
        return result

    @classmethod
    def get_mail_by_history_id(cls, history_id):
        """Get list mail by history id.

        Arguments:
            history_id {integer} -- The history id

        Returns:
            list -- list of mail

        """
        data = cls.query.filter_by(
            history_id=history_id
        ).all()
        result = list()
        for item in data:
            result.append(item.mail)
        return result

    @classmethod
    def delete_by_history_id(cls, session, history_id):
        """Delete all mail by history id.

        Arguments:
            history_id {integer} -- The history id

        """
        if not session:
            session = db.session
        try:
            with session.begin_nested():
                cls.query.filter_by(
                    history_id=history_id
                ).delete()
            session.commit()
        except BaseException as ex:
            session.rollback()
            current_app.logger.debug(ex)

    @classmethod
    def create(cls, session, history_id, author_id, mail):
        """Create mail record.

        Arguments:
            history_id {integer} -- history_id
            author_id {string} -- The author id
            mail {string} -- mail

        """
        if not session:
            session = db.session
        try:
            with session.begin_nested():
                data = FeedbackMailFailed()
                data.history_id = history_id
                data.author_id = author_id
                data.mail = mail
                session.add(data)
            session.commit()
        except BaseException as ex:
            session.rollback()
            current_app.logger.error(ex)


class Identifier(db.Model):
    """
    Represent an Identifier.

    The Identifier object contains a ``created``, a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'doi_identifier'

    id = db.Column(db.BigInteger, primary_key=True, unique=True)
    """ Identifier of the index """

    repository = db.Column(db.String(100), nullable=False)
    """ Repository of the community """

    jalc_flag = db.Column(db.Boolean(name='jalc_flag'), default=True)
    """ Jalc_flag of the Identifier """

    jalc_crossref_flag = db.Column(db.Boolean(name='jalc_crossref_flag'),
                                   default=True)
    """ Jalc_crossref_flag of the Identifier """

    jalc_datacite_flag = db.Column(db.Boolean(name='jalc_datacite_flag'),
                                   default=True)
    """ Jalc_datacite_flag of the Identifier """

    ndl_jalc_flag = db.Column(db.Boolean(name='ndl_jalc_flag'), default=True)
    """ Ndl_jalc_flag of the Identifier """

    jalc_doi = db.Column(db.String(100), nullable=True)
    """ Jalc_doi of the Identifier """

    jalc_crossref_doi = db.Column(db.String(100), nullable=True)
    """ Jalc_crossref_doi of the Identifier """

    jalc_datacite_doi = db.Column(db.String(100), nullable=True)
    """ Jalc_datacite_doi of the Identifier """

    ndl_jalc_doi = db.Column(db.String(100), nullable=True)
    """ Ndl_jalc_doi of the Identifier """

    suffix = db.Column(db.String(100), nullable=True)
    """ Suffix of the Identifier """

    created_userId = db.Column(db.String(50), nullable=False)
    """ Created by user """

    created_date = db.Column(db.DateTime, nullable=False)
    """ Created date """

    updated_userId = db.Column(db.String(50), nullable=False)
    """ Updated by user """

    updated_date = db.Column(db.DateTime, nullable=True)
    """ Created date """

    def __repr__(self):
        """String representation of the Pidstore Identifier object."""
        return '<Identifier {}, Repository: {}>'.format(self.id,
                                                        self.repository)


class FacetSearchSetting(db.Model):
    """Database for Facet Search."""

    __tablename__ = 'facet_search_setting'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    """Unique number of rows in this table."""

    name_en = db.Column(db.String(255), nullable=False)
    """English name of facet search."""

    name_jp = db.Column(db.String(255), nullable=True)
    """Japanese name of facet search."""

    mapping = db.Column(db.String(255), nullable=False)
    """Base on this mapping to search columns in ES."""

    aggregations = db.Column(
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
    """Facet Search Agg."""

    active = db.Column(db.Boolean(name='active'), default=True)
    """True: display this facet search on screen, else hide this."""

    ui_type = db.Column(db.String(20), nullable=False)
    """Indicates the type of Facet search UI component."""

    display_number = db.Column(db.Integer)
    """Indicates the number of items displayed in the list view in CheckboxUI."""

    is_open = db.Column(db.Boolean(name='is_open'), default=True, nullable=False)
    """Indicates whether the faceted search item is open or closed, and if true, it is open."""

    search_condition = db.Column(db.String(20), nullable=False)
    """Indicates search conditions for faceted search items; OR or AND can be set."""

    def __init__(self, name_en, name_jp, mapping, aggregations, active, ui_type, display_number, is_open, search_condition):
        """Initial Facet search setting.

        Args:
            name_en: Name fix
            name_jp:
            mapping:
            aggregations:
            active:
            ui_type:
            display_number:
            is_open:
            search_condition:
        """
        self.name_en = name_en
        self.name_jp = name_jp
        self.mapping = mapping
        self.aggregations = aggregations
        self.active = active
        self.ui_type = ui_type
        self.display_number = display_number
        self.is_open = is_open
        self.search_condition = search_condition

    def to_dict(self) -> dict:
        """Convert object to dictionary.

        Returns:
            dict: the object is converted to dictionary.

        """
        return {
            "name_en": self.name_en,
            "name_jp": self.name_jp,
            "mapping": self.mapping,
            "aggregations": self.aggregations,
            "active": self.active,
            "ui_type": self.ui_type,
            "display_number": self.display_number,
            "is_open": self.is_open,
            "search_condition": self.search_condition
        }

    @classmethod
    def get_by_id(cls, id):
        """Get a facet search by id."""
        return cls.query.filter_by(id=id).one_or_none()

    @classmethod
    def get_all(cls):
        """Get all facet search."""
        return cls.query.all()

    @classmethod
    def get_activated_facets(cls):
        """Get all activated facets search."""
        return cls.query.filter_by(active=True).all()

    @classmethod
    def create(cls, faceted_search_dict):
        """Create facet search item.

        :param faceted_search_dict: facet search data
        :return:
        """
        try:
            with db.session.begin_nested():
                faceted_search = cls(**faceted_search_dict)
                db.session.add(faceted_search)
            db.session.commit()
            return faceted_search
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return None

    @classmethod
    def delete(cls, id):
        """Delete settings."""
        if id is not None:
            try:
                with db.session.begin_nested():
                    cls.query.filter_by(id=id).delete()
                db.session.commit()
                return True
            except BaseException as ex:
                db.session.rollback()
                current_app.logger.error(ex)

        return False

    @classmethod
    def update_by_id(cls, id, faceted_search_dict):
        """Update facet search item.

        Args:
            id: id of facet search
            faceted_search_dict: facet search data update

        Returns: True if update success.

        """
        facet_search = cls.get_by_id(id)
        if facet_search:
            try:
                with db.session.begin_nested():
                    for k, v in faceted_search_dict.items():
                        setattr(facet_search, k, v)
                    db.session.merge(facet_search)
                db.session.commit()
                return True
            except BaseException as ex:
                db.session.rollback()
                current_app.logger.error(ex)

        return False

    @classmethod
    def get_activated_facets_mapping(cls):
        """Get activated facet mapping.

        Returns: Facet mapping.

        """
        activated_facet_search = cls.get_activated_facets()
        result = dict()
        for item in activated_facet_search:
            result.update({item.name_en: item.mapping})
        return result

    @classmethod
    def get_by_name(cls, name_en, name_jp):
        """Get all facet search by name_en, name_jp."""
        return cls.query.filter_by(name_en=name_en,
                                   name_jp=name_jp).one_or_none()

    @classmethod
    def get_by_mapping(cls, mapping):
        """Get all facet search by mapping."""
        return cls.query.filter_by(mapping=mapping).one_or_none()


__all__ = ([
    'SearchManagement',
    'AdminLangSettings',
    'ApiCertificate',
    'StatisticUnit',
    'StatisticTarget',
    'LogAnalysisRestrictedIpAddress',
    'LogAnalysisRestrictedCrawlerList',
    'StatisticsEmail',
    'RankingSettings',
    'BillingPermission',
    'FeedbackMailSetting',
    'AdminSettings',
    'SiteInfo',
    'FeedbackMailHistory',
    'FeedbackMailFailed',
    'Identifier',
    'FacetSearchSetting',
])
