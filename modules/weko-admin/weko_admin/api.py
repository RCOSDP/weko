# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Weko-Admin API."""

from __future__ import absolute_import, print_function

import ast
import sys
import traceback

import redis
import re
from redis import RedisError
import requests
from flask import current_app, render_template
from flask_babelex import lazy_gettext as _
from invenio_db import db
from invenio_mail.api import send_mail
from weko_redis.redis import RedisConnection
from flask_wtf import FlaskForm
from wtforms.validators import ValidationError
from flask_wtf.csrf import validate_csrf,same_origin,CSRFError

from .models import LogAnalysisRestrictedCrawlerList, \
    LogAnalysisRestrictedIpAddress
from .utils import get_system_default_language

def is_restricted_user(user_info):
    """Check if user is restricted based on IP Address and User Agent.

    :param user_info: Dictionary containing IP Address and User Agent.

    :return: Boolean.
    """
    try:
        restricted_ip = db.session.query(LogAnalysisRestrictedIpAddress) \
            .filter_by(ip_address=user_info['ip_address']).one_or_none()
        is_crawler = _is_crawler(user_info)
    except Exception as e:
        current_app.logger.error('Could not check for restricted users: ')
        traceback.print_exc(file=sys.stdout)
        return False
    restricted_ip = False if restricted_ip is None else True
    return (restricted_ip or is_crawler)


def _is_crawler(user_info):
    """Check if user agent is contained in URLs.

    :param user_agent: User agent.

    :return: Boolean.
    """

    restricted_agent_lists = LogAnalysisRestrictedCrawlerList.get_all_active()
    for restricted_agent_list in restricted_agent_lists:
        empty_list = False
        try:
            redis_connection = RedisConnection()
            connection = redis_connection.connection(db=current_app.config['CRAWLER_REDIS_DB'], kv = False)

            if current_app.config['WEKO_ADMIN_USE_REGEX_IN_CRAWLER_LIST']:
                bot_regex_str = connection.get(restricted_agent_list.list_url)
                if bot_regex_str == "":
                    current_app.logger.info("Crawler List is expired : " + str(restricted_agent_list.list_url))
                    empty_list = True
            else:
                restrict_list = connection.smembers(restricted_agent_list.list_url)
                if len(restrict_list) == 0:
                    current_app.logger.info("Crawler List is expired : " + str(restricted_agent_list.list_url))
                    empty_list = True
        except RedisError:
            current_app.logger.info("Crawler List is expired : " + str(restricted_agent_list.list_url))
            empty_list = True

        if  empty_list:
            raw_res = requests.get(restricted_agent_list.list_url).text
            if not raw_res:
                continue

            crawler_list = raw_res.split('\n')
            if current_app.config['WEKO_ADMIN_USE_REGEX_IN_CRAWLER_LIST']:
                crawler_list = [agent.lower() for agent in crawler_list if agent and not agent.startswith('#')]
                bot_regex_str = '|'.join(crawler_list)
                connection.set(restricted_agent_list.list_url, bot_regex_str)
                connection.expire(restricted_agent_list.list_url, current_app.config["CRAWLER_REDIS_TTL"])
            else:
                crawler_list = [agent for agent in crawler_list if not agent.startswith('#')]
                for restrict_ip in crawler_list:
                    connection.sadd(restricted_agent_list.list_url,restrict_ip)
                connection.expire(restricted_agent_list.list_url, current_app.config["CRAWLER_REDIS_TTL"])
                restrict_list = set(crawler_list)

        if current_app.config['WEKO_ADMIN_USE_REGEX_IN_CRAWLER_LIST']:
            if bot_regex_str and (
                re.search(bot_regex_str, user_info['user_agent'].lower()) or
                re.search(bot_regex_str, user_info['ip_address'].lower())
            ):
                return True
        else:
            if (user_info['user_agent']).encode('utf-8') in restrict_list or \
            (user_info['ip_address']).encode('utf-8') in restrict_list:
                return True
    return False


def send_site_license_mail(organization_name, mail_list, agg_date, data):
    """Send site license statistics mail."""
    try:
        # mail title
        subject = '[{0}] {1} '.format(organization_name, agg_date) + \
            _('statistics report')

        with current_app.test_request_context() as ctx:
            default_lang = get_system_default_language()
            # setting locale
            setattr(ctx, 'babel_locale', default_lang)
            # send alert mail
            send_mail(
                subject,
                mail_list,
                body=str(
                    render_template(
                        'weko_admin/email_templates/site_license_report.html',
                        agg_date=agg_date,
                        data=data,
                        lang_code=default_lang)))
    except Exception as ex:
        current_app.logger.error(ex)


class TempDirInfo(object):
    """Handle's collection of storage Temporary Directory Information."""

    def __init__(cls, key=None) -> None:
        """Tempdirinfo initialization.

        Args:
            key (str, optional): Cache key. Defaults to None.
        """
        if not key:
            key = current_app.config[
                'WEKO_ADMIN_CACHE_TEMP_DIR_INFO_KEY_DEFAULT']
        cls.key = key

        redis_connection = RedisConnection()
        cls.redis = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'])

    def set(cls, temp_path, extra_info=None):
        """Add or update data.

        Args:
            temp_path (str): Path of temporary directory.
            extra_info (dict, optional): Extra information. Defaults to None.

        Returns:
            int: Action status.

        """
        return cls.redis.hset(cls.key, temp_path, extra_info)

    def delete(cls, temp_path):
        """Delete data.

        Args:
            temp_path (str): Path of temporary directory.

        Returns:
            int: Action status.

        """
        return cls.redis.hdel(cls.key, temp_path)

    def get(cls, temp_path):
        """Get data by temp_path.

        Args:
            temp_path (str): Path of temporary directory.

        Returns:
            dict: Extended information according temp_path.

        """
        val = cls.redis.hget(cls.key, temp_path)
        return ast.literal_eval(val.decode("UTF-8")) if val else None

    def get_all(cls):
        """Get all data.

        Returns:
            dict: All data.

        """
        result = {}
        for idx, val in cls.redis.hgetall(cls.key).items():
            path = idx.decode("UTF-8")
            result[path] = ast.literal_eval(val.decode("UTF-8") or '{}')
        return result


def validate_csrf_header(request,csrf_header="X-CSRFToken"):
    """Validate CSRF header

    Args:
        csrf_header (str, optional): CSRF Token Header. Defaults to "X-CSRFToken".

    Raises:
        CSRFError: _description_
        CSRFError: _description_
        CSRFError: _description_
    """
    try:
        csrf_token = request.headers.get(csrf_header)
        validate_csrf(csrf_token)
    except ValidationError as e:
        raise CSRFError(e.args[0])

    if request.is_secure:
        if not request.referrer:
            raise CSRFError("The referrer header is missing.")

        good_referrer = f"https://{request.host}/"

        if not same_origin(request.referrer, good_referrer):
            raise CSRFError("The referrer does not match the host.")
