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

"""Unauthorized handling for ``login_required``.

flask_login's default is to redirect to ``security.login``. That is right for
a page the user typed in, and wrong for everything else:

- On the **API app** there is no ``security`` blueprint at all, so ``url_for``
  raises BuildError and the request comes back as a 500 instead of a 401.
- On the **UI app** an AJAX call gets 302 -> the login page's HTML. The caller
  asked for JSON, so it fails while parsing, usually without any error
  handling, and the feature disappears from the screen with no message.

This module returns 401 JSON whenever the request looks like it came from
code rather than from the address bar, and leaves ordinary page requests on
the usual redirect.
"""

from flask import current_app, flash, jsonify, redirect, request
from flask_login import login_url
from werkzeug.exceptions import Unauthorized


def wants_json():
    """Tell an API/AJAX call apart from a browser navigating to a page.

    Ordered from the most explicit signal to the weakest.
    """
    # The API app only ever serves machine callers.
    if request.path.startswith('/api/'):
        return True

    # jQuery sets this; angular's $http and fetch() do not.
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True

    # A JSON request body implies a JSON caller.
    if request.mimetype == 'application/json':
        return True

    # Sent by current browsers on every request: 'document' for a navigation,
    # 'empty' for fetch()/XHR. This is what catches the fetch() callers that
    # send no Accept header of their own (e.g. bucket.js, detail.js).
    dest = request.headers.get('Sec-Fetch-Dest')
    if dest:
        return dest != 'document'

    # Redirecting a state-changing request to a login page is never useful:
    # the browser would follow it with a GET and the caller would get HTML.
    if request.method not in ('GET', 'HEAD'):
        return True

    accept = request.accept_mimetypes
    return accept['application/json'] > accept['text/html']


def json_unauthorized():
    """Build the 401 to raise.

    Raised rather than returned: flask_login *returns* whatever the callback
    gives back, and ContentNegotiatedMethodView (every invenio-records-rest
    resource) passes a view's return value to ``make_response(*result)``,
    where a response tuple is unpacked as ``(pid, record)`` and fails with a
    500. Raising makes it travel as an exception, which both plain views and
    the REST resources handle correctly.
    """
    response = jsonify(status=401, message='Authentication required.')
    response.status_code = 401
    # werkzeug 0.15's Unauthorized.__init__ takes (description,
    # www_authenticate) and does not accept ``response``, so attach it
    # afterwards; HTTPException.get_response() returns it when set.
    exception = Unauthorized()
    exception.response = response
    return exception


def redirect_to_login():
    """Reproduce flask_login's default redirect for page requests."""
    login_manager = current_app.login_manager
    if not login_manager.login_view:
        raise json_unauthorized()
    if login_manager.login_message:
        flash(login_manager.login_message,
              category=login_manager.login_message_category)
    return redirect(login_url(login_manager.login_view, request.url))


def install(app, api_only=False):
    """Register the unauthorized handler on ``app``.

    :param app: The flask application.
    :param api_only: When True every unauthorized request gets 401 JSON.
        Use it for the API app, which has no login screen to redirect to.
    """
    if not app.config.get('WEKO_ACCOUNTS_UNAUTHORIZED_JSON', True):
        return

    def _unauthorized():
        if api_only or wants_json():
            raise json_unauthorized()
        return redirect_to_login()

    def _install():
        login_manager = getattr(app, 'login_manager', None)
        # Defer to another extension that already installed a handler.
        if login_manager is not None \
                and login_manager.unauthorized_callback is None:
            login_manager.unauthorized_handler(_unauthorized)

    _install()
    if getattr(app, 'login_manager', None) is None:
        # Entry point load order is not guaranteed, so retry once the app is
        # fully initialized.
        app.before_first_request(_install)
