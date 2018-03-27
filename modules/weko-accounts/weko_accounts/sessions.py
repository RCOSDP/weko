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

"""Setting of weko sessions."""

from flask import after_this_request, current_app, session

from .utils import get_remote_addr


def login_listener(app, user):
    """Connect to the user_logged_in signal for table population.

    :param app: The Flask application.
    :param user: The :class:`invenio_accounts.models.User` instance.
    """
    @after_this_request
    def logger_user_session_login(response):
        """Regenerate current session and add to the SessionActivity table.

        :param response:
        .. note:: `flask.session.regenerate()` actually calls Flask-KVSession's
            `flask_kvsession.KVSession.regenerate`.
        """
        user_id, sid_s = user.id, session.sid_s
        login_ip = get_remote_addr()
        current_app.logger.info(
            'auth login success: {user_id},{session_id},{login_ip}'.format(
                user_id=user_id, session_id=sid_s, login_ip=login_ip))

        return response


def logout_listener(app, user):
    """Connect to the user_logged_in signal for table population.

    :param app: The Flask application.
    :param user: The :class:`invenio_accounts.models.User` instance.
    """
    @after_this_request
    def logger_user_session_logout(response):
        """Regenerate current session and add to the SessionActivity table.

        :param response:
        .. note:: `flask.session.regenerate()` actually calls Flask-KVSession's
            `flask_kvsession.KVSession.regenerate`.
        """
        user_id, login_date = user.id, user.current_login_at
        logout_ip = get_remote_addr()
        current_app.logger.info(
            'auth logout success: {user_id},{login_date},{logout_ip}'.format(
                user_id=user_id, login_date=login_date, logout_ip=logout_ip))

        return response
