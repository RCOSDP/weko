# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Backend session management for accounts.

The actual backend sessions are provided by ``flask-kvsession``.
This module provides management functionality and populates the
:class:`invenio_accounts.models.SessionActivity` table as new sessions are
created.
"""

from __future__ import absolute_import, print_function

from flask import after_this_request, current_app, request, session
from geolite2 import geolite2
from invenio_db import db
from ua_parser import user_agent_parser
from werkzeug.local import LocalProxy

from .models import SessionActivity
from .proxies import current_accounts

_sessionstore = LocalProxy(lambda: current_app.kvsession_store)


def _ip2country(ip):
    """Get user country."""
    if ip:
        match = geolite2.reader().get(ip)
        return match.get('country', {}).get('iso_code') if match else None


def _extract_info_from_useragent(user_agent):
    """Extract extra informations from user."""
    parsed_string = user_agent_parser.Parse(user_agent)
    return {
        'os': parsed_string.get('os', {}).get('family'),
        'browser': parsed_string.get('user_agent', {}).get('family'),
        'browser_version': parsed_string.get('user_agent', {}).get('major'),
        'device': parsed_string.get('device', {}).get('family'),
    }


def get_remote_addr():
    """
    Get remote ip address.

    # An 'X-Forwarded-For' header includes a comma separated list of the
    # addresses, the first address being the actual remote address.
    """
    if not request:
        return None

    address = request.headers.get('X-Real-IP', None)

    if address is None:
        address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if address is not None:
            address = address.encode('utf-8').split(b',')[0].strip().decode()

    return address


def add_session(session=None):
    r"""Add a session to the SessionActivity table.

    :param session: Flask Session object to add. If None, ``session``
        is used. The object is expected to have a dictionary entry named
        ``"user_id"`` and a field ``sid_s``
    """
    user_id, sid_s = session['user_id'], session.sid_s

    request_data = request.get_json()
    orgniazation_name = request_data.get('jao') if request_data else None

    with db.session.begin_nested():
        session_activity = SessionActivity(
            user_id=user_id,
            sid_s=sid_s,
            ip=get_remote_addr(),
            country=_ip2country(get_remote_addr()),
            **_extract_info_from_useragent(
                request.headers.get('User-Agent', '')
            ),
            orgniazation_name=orgniazation_name
        )
        db.session.merge(session_activity)


def login_listener(app, user):
    """Connect to the user_logged_in signal for table population.

    :param app: The Flask application.
    :param user: The :class:`invenio_accounts.models.User` instance.
    """
    @after_this_request
    def add_user_session(response):
        """Regenerate current session and add to the SessionActivity table.

        .. note:: `flask.session.regenerate()` actually calls Flask-KVSession's
            `flask_kvsession.KVSession.regenerate`.
        """
        # Regenerate the session to avoid session fixation vulnerabilities.
        session.regenerate()
        # Save the session first so that the sid_s gets generated.
        app.session_interface.save_session(app, session, response)
        add_session(session)
        current_accounts.datastore.commit()
        return response


def logout_listener(app, user):
    """Connect to the user_logged_out signal.

    :param app: The Flask application.
    :param user: The :class:`invenio_accounts.models.User` instance.
    """
    @after_this_request
    def _commit(response=None):
        if hasattr(session, 'sid_s'):
            delete_session(session.sid_s)
        # Regenerate the session to avoid session fixation vulnerabilities.
        session.regenerate()
        current_accounts.datastore.commit()
        return response


def delete_session(sid_s):
    """Delete entries in the data- and kvsessionstore with the given sid_s.

    On a successful deletion, the flask-kvsession store returns 1 while the
    sqlalchemy datastore returns None.

    :param sid_s: The session ID.
    :returns: ``1`` if deletion was successful.
    """
    # Remove entries from sessionstore
    _sessionstore.delete(sid_s)
    # Find and remove the corresponding SessionActivity entry
    with db.session.begin_nested():
        SessionActivity.query.filter_by(sid_s=sid_s).delete()
    return 1


def delete_user_sessions(user):
    """Delete all active user sessions.

    :param user: User instance.
    :returns: If ``True`` then the session is successfully deleted.
    """
    with db.session.begin_nested():
        for s in user.active_sessions:
            _sessionstore.delete(s.sid_s)

        SessionActivity.query.filter_by(user=user).delete()

    return True


def session_update(app):
    
    @app.teardown_request
    def session_ttl_update(arg):
        if 'user_id' not in session and hasattr(session, 'sid_s'):
            if request.path == '/ping':
                _sessionstore.redis.expire(session.sid_s, 1)
            else:
                _sessionstore.redis.expire(session.sid_s,900)
        elif request.path.startswith('/admin/items/import/') and hasattr(session, 'sid_s'):
            _sessionstore.redis.expire(
                session.sid_s,
                current_app.config.get('WEKO_ADMIN_IMPORT_PAGE_LIFETIME', 43200))
