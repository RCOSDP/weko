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

"""Utils for weko-accounts."""
import random
import string
from functools import wraps

from flask import abort, current_app, request, session, Flask
from flask_limiter import Limiter
from flask_login import current_user
from flask_login.config import EXEMPT_METHODS
import hashlib

from .config import WEKO_API_LIMIT_RATE_DEFAULT

limiter = Limiter(
    app=None,
    key_func=lambda: f"{request.endpoint}_{get_remote_addr()}",
    default_limits=WEKO_API_LIMIT_RATE_DEFAULT
)
"""Limiter for API rate per user.

Limit the access rate for each endpoint.

Example:

    @blueprint.route("/")
    @limiter.limit("10 per minute")
    def api_view():
        return "OK", 200

"""


def get_remote_addr():
    """
    Get remote ip address.

    # An 'X-Forwarded-For' header includes a comma separated list of the
    # addresses, the first address being the actual remote address.
    """

    if not request:
        return None

    # current_app.logger.debug('{0} {1} {2}: {3}'.format(
    #     __file__, 'get_remote_addr()', 'request.headers', request.headers))

    address = None
    if "WEKO_ACCOUNTS_REAL_IP" not in current_app.config or current_app.config["WEKO_ACCOUNTS_REAL_IP"] == None:
        address = request.headers.get('X-Real-IP', None)
        if address is None:
            address = request.headers.get('X-Forwarded-For', None)
            if address is not None:
                address = address.encode('utf-8').split(b',')[0].strip().decode()
    elif current_app.config["WEKO_ACCOUNTS_REAL_IP"] == "remote_addr":
        address =request.remote_addr
    elif current_app.config["WEKO_ACCOUNTS_REAL_IP"] == "x_real_ip":
        address = request.headers.get('X-Real-IP', None)
    elif current_app.config["WEKO_ACCOUNTS_REAL_IP"] == "x_forwarded_for":
        address = request.headers.get('X-Forwarded-For', None)
        if address is not None:
            _tmp = address.encode('utf-8').split(b',')
            address = _tmp[0].strip().decode()
    elif current_app.config["WEKO_ACCOUNTS_REAL_IP"] == "x_forwarded_for_rev":
        address = request.headers.get('X-Forwarded-For', None)
        if address is not None:
            _tmp = address.encode('utf-8').split(b',')
            address = _tmp[len(_tmp)-1].strip().decode()

    if address == None or len(address)==0:
        address = request.remote_addr

    current_app.logger.debug("IP Address:{}".format(address))

    return address


def generate_random_str(length=128):
    """Generate secret key."""
    rng = random.SystemRandom()

    return ''.join(
        rng.choice(string.ascii_letters + string.digits)
        for _ in range(0, length)
    )


def parse_attributes():
    """Parse arguments from environment variables."""
    attrs = {}
    error = False

    for header, attr in current_app.config[
            'WEKO_ACCOUNTS_SSO_ATTRIBUTE_MAP'].items():
        required, name = attr
        value = request.form.get(header, '') if request.method == 'POST' \
            else request.args.get(header, '')
        attrs[name] = value

        if required and not value:
            error = True

    if not error and not attrs.get('shib_user_name') and attrs.get('shib_eppn'):
        if len(attrs['shib_eppn']) > current_app.config[
                'WEKO_ACCOUNTS_SHIB_USER_NAME_NO_HASH_LENGTH']:
            eppn = hashlib.sha256(attrs['shib_eppn'].encode('utf-8')).hexdigest()
        else:
            eppn = attrs['shib_eppn']
        attrs['shib_user_name'] = current_app.config['WEKO_ACCOUNTS_GAKUNIN_USER_NAME_PREFIX'] + eppn

    return attrs, error


def login_required_customize(func):
    """Login required custom.

    If you decorate a view with this, it will ensure that the current user is
    logged in and authenticated before calling the actual view. (If they are
    not, it calls the :attr:`LoginManager.unauthorized` callback.) For
    example::

        @app.route('/post')
        @login_required_customize
        def post():
            pass

    If there are only certain times you need to require that your user is
    logged in, you can do so with::

        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()

    ...which is essentially the code that this function adds to your views.

    It can be convenient to globally turn off authentication when unit testing.
    To enable this, if the application configuration variable `LOGIN_DISABLED`
    is set to `True`, this decorator will be ignored.

    .. Note ::

        Per `W3 guidelines for CORS preflight requests
        <http://www.w3.org/TR/cors/#cross-origin-request-with-preflight-0>`_,
        HTTP ``OPTIONS`` requests are exempt from login checks.

    :param func: The view function to decorate.
    :type func: function
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in EXEMPT_METHODS:
            return func(*args, **kwargs)
        elif current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            guest_token = session.get('guest_token')
            if guest_token:
                return func(*args, **kwargs)
            return current_app.login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view


def roles_required(roles, allow_anonymous=False):
    """Roles required.

    Args:
        roles (list): List roles.
    """
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if request.method in EXEMPT_METHODS:
                return func(*args, **kwargs)
            elif current_app.login_manager._login_disabled:
                return func(*args, **kwargs)
            elif not current_user.is_authenticated:
                guest_token = session.get('guest_token')
                if guest_token:
                    return func(*args, **kwargs)
                abort(401)
            else:
                if allow_anonymous:
                    return func(*args, **kwargs)
                can = False
                for role in current_user.roles:
                    if role and role.name in roles:
                        can = True
                        break
                if not can:
                    abort(403)
            return func(*args, **kwargs)
        return decorated_view
    return decorator

def get_sp_info():
    """Get Service Provider (SP) information for Shibboleth login.
    
    Returns:
        dict: A dictionary containing SP entityID, handlerURL, and return URL.
    """
    _shib_login_url = current_app.config['WEKO_ACCOUNTS_SHIB_IDP_LOGIN_URL']

    session['next'] = request.args.get('next', '/')
    return_url = _shib_login_url.format(request.url_root)

    sp_entityID = 'https://' + current_app.config['WEB_HOST_NAME'] + '/shibboleth-sp'
    if 'SP_ENTITYID' in current_app.config:
        sp_entityID = current_app.config['SP_ENTITYID']
    
    sp_handlerURL = 'https://' + current_app.config['WEB_HOST_NAME'] + '/Shibboleth.sso'
    if 'SP_HANDLERURL' in current_app.config:
        sp_handlerURL = current_app.config['SP_HANDLERURL']

    return {
        'sp_entityID': sp_entityID,
        'sp_handlerURL': sp_handlerURL,
        'return_url': return_url,
    }
