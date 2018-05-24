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

"""Views for weko-accounts.

Set the templates and static folders as well as the test case by flask
Blueprint.
"""

import json
import sys

import redis
from flask import Blueprint, abort, current_app, flash, \
    redirect, render_template, request, session, url_for
from flask_babelex import gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from flask_security import url_for_security
from invenio_admin.proxies import current_admin
from simplekv.memory.redisstore import RedisStore
from werkzeug.local import LocalProxy

from . import config
from .api import ShibUser
from .utils import generate_random_str

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)

blueprint = Blueprint(
    'weko_accounts',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/weko',
)


def _has_admin_access():
    """Use to check if a user has any admin access."""
    return current_user.is_authenticated and current_admin \
        .permission_factory(current_admin.admin.index_view).can()


@blueprint.route('/')
def index():
    """Render a basic view."""
    return render_template(
        'weko_accounts/index.html',
        module_name=_('WEKO-Accounts'))


@blueprint.route('/auto/login', methods=['GET'])
def shib_auto_login():
    """create new account and auto login when shibboleth user first login.

    :return: next url
    """
    try:
        is_auto_bind = False
        shib_session_id = request.args.get('SHIB_ATTR_SESSION_ID', None)
        if shib_session_id is None:
            shib_session_id = session['shib_session_id']
            is_auto_bind = True
        if shib_session_id is None or len(shib_session_id) == 0:
            return redirect(url_for_security('login'))
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        cache_key = config.SHIB_CACHE_PREFIX + shib_session_id
        if not datastore.redis.exists(cache_key):
            return redirect(url_for_security('login'))
        cache_val = datastore.get(cache_key)
        if cache_val is None:
            datastore.delete(cache_key)
            return redirect(url_for_security('login'))
        cache_val = json.loads(str(cache_val, encoding='utf-8'))
        shib_user = ShibUser(cache_val)
        if not is_auto_bind:
            shib_user.get_relation_info()
        else:
            shib_user.new_relation_info()
        if shib_user.shib_user is not None:
            shib_user.shib_user_login()
        datastore.delete(cache_key)
        return redirect(session['next'] if 'next' in session else '/')
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/confim/user', methods=['POST'])
def confirm_user():
    """check weko user info.

    :return:
    """
    try:
        csrf_random = request.form.get('csrf_random', '')
        if csrf_random != session['csrf_random']:
            return redirect(url_for_security('login'))
        shib_session_id = session['shib_session_id']
        if shib_session_id is None or len(shib_session_id) == 0:
            return redirect(url_for_security('login'))
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        cache_key = config.SHIB_CACHE_PREFIX + shib_session_id
        if not datastore.redis.exists(cache_key):
            return redirect(url_for_security('login'))
        cache_val = datastore.get(cache_key)
        if cache_val is None:
            datastore.delete(cache_key)
            return redirect(url_for_security('login'))
        cache_val = json.loads(str(cache_val, encoding='utf-8'))
        shib_user = ShibUser(cache_val)
        account = request.form.get('WEKO_ATTR_ACCOUNT', None)
        password = request.form.get('WEKO_ATTR_PWD', None)
        if not shib_user.check_weko_user(account, password):
            datastore.delete(cache_key)
            return redirect(url_for_security('login'))
        shib_user.bind_relation_info(account)
        if shib_user.shib_user is not None:
            shib_user.shib_user_login()
        datastore.delete(cache_key)
        return redirect(session['next'] if 'next' in session else '/')
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/shib/login', methods=['GET'])
def shib_login():
    """get shibboleth user login page.

    :return: confirm user page when relation is empty
    """
    try:
        shib_session_id = request.args.get('SHIB_ATTR_SESSION_ID', None)
        if shib_session_id is None or len(shib_session_id) == 0:
            return redirect(url_for_security('login'))
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        cache_key = config.SHIB_CACHE_PREFIX + shib_session_id
        if not datastore.redis.exists(cache_key):
            return redirect(url_for_security('login'))
        cache_val = datastore.get(cache_key)
        if cache_val is None:
            datastore.delete(cache_key)
            return redirect(url_for_security('login'))
        cache_val = json.loads(str(cache_val, encoding='utf-8'))
        session['shib_session_id'] = shib_session_id
        csrf_random = generate_random_str(length=64)
        session['csrf_random'] = csrf_random
        return render_template(
            config.WEKO_ACCOUNTS_CONFIRM_USER_TEMPLATE,
            csrf_random=csrf_random,
            email=cache_val['shib_mail'] if len(
                cache_val['shib_mail']) > 0 else '')
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/shib/login', methods=['POST'])
def shib_sp_login():
    """the request from shibboleth sp.

    :return: confirm page when relation is empty
    """
    try:
        if not current_app.config['SHIB_ACCOUNTS_LOGIN_ENABLED']:
            return url_for_security('login')
        shib_session_id = request.form.get('SHIB_ATTR_SESSION_ID', None)
        if shib_session_id is None or len(shib_session_id) == 0:
            return url_for_security('login')
        shib_attr, error = parse_attributes()
        if error:
            return url_for_security('login')
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        ttl_sec = int(current_app.config['SHIB_ACCOUNTS_LOGIN_CACHE_TTL'])
        datastore.put(config.SHIB_CACHE_PREFIX + shib_session_id,
                      bytes(json.dumps(shib_attr), encoding='utf-8'),
                      ttl_secs=ttl_sec)
        shib_user = ShibUser(shib_attr)
        rst = shib_user.get_relation_info()
        """ check the relation of shibboleth user with weko account"""
        next_url = 'weko_accounts.shib_auto_login'
        if rst is None:
            """relation is not existed, cache shibboleth info to redis."""
            next_url = 'weko_accounts.shib_login'
        query_string = {
            'SHIB_ATTR_SESSION_ID': shib_session_id,
            '_method': 'GET'
        }
        return url_for(next_url, **query_string)
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return url_for_security('login')


@blueprint.route('/shib/sp/login', methods=['GET'])
def shib_stub_login():
    """shibboleth sp test page.

    :return:
    """
    if not current_app.config['SHIB_ACCOUNTS_LOGIN_ENABLED']:
        return abort(403)
    session['next'] = request.args.get('next', '/')
    return redirect(config.SHIB_IDP_LOGIN_URL)


@blueprint.route('/shib/logout')
def shib_logout():
    """shibboleth user logout.

    :return:
    """
    ShibUser.shib_user_logout()
    return 'logout success'


def parse_attributes():
    """Parse arguments from environment variables."""
    attrs = {}
    error = False
    for header, attr in current_app.config['SSO_ATTRIBUTE_MAP'].items():
        required, name = attr
        value = request.form.get(header, '') if request.method == 'POST' \
            else request.args.get(header, '')
        current_app.logger.debug('Shib    {0}: {1}'.format(name, value))
        attrs[name] = value
        if not value or value == '':
            if required:
                error = True
    return attrs, error
