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

import requests
from flask import current_app
from invenio_db import db
from sqlalchemy import text

from .models import LogAnalysisRestrictedCrawlerList, \
    LogAnalysisRestrictedIpAddress


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
        current_app.logger.error(e)
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
        raw_res = requests.get(restricted_agent_list.list_url).text
        if not raw_res:
            continue
        restrict_list = raw_res.split('\n')
        restrict_list = [
            agent for agent in restrict_list if not agent.startswith('#')]
        if user_info['user_agent'] in restrict_list or \
           user_info['ip_address'] in restrict_list:
            return True
    return False
