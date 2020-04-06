# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

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

        return response
