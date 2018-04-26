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

"""
Views for weko-accounts.

Set the templates and static folders as well as the test case by
flask Blueprint.
"""

import json

import redis
from flask import abort, Blueprint, current_app, render_template, redirect, \
    request, session, url_for, flash
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

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)

blueprint = Blueprint(
    'weko_accounts',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix="/weko",
)


def _has_admin_access():
    """Use to check if a user has any admin access."""
    return current_user.is_authenticated and current_admin \
        .permission_factory(current_admin.admin.index_view).can()


@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        "weko_accounts/index.html",
        module_name=_('WEKO-Accounts'))


@blueprint.route("/confim/user", methods=['POST'])
def confirm_user():
    """
    check weko user info
    :return:
    """
    form_weko_user_chk = request.form.get('WEKO_USER_CHK', None)
    if form_weko_user_chk is None:
        return redirect(url_for_security('login'))
    shib_session_id = request.form.get('SHIB_ATTR_SESSION_ID', None)
    if shib_session_id is None or len(shib_session_id) == 0:
        return redirect(url_for_security('login'))
    datastore = RedisStore(redis.StrictRedis.from_url(
        current_app.config['CACHE_REDIS_URL']))
    cache_key = config.SHIB_CACHE_PREFIX + shib_session_id
    if not datastore.redis.exists(cache_key):
        return redirect(url_for_security('login'))
    cache_val = datastore.get(cache_key)
    if cache_val is None:
        return redirect(url_for_security('login'))
    cache_val = json.loads(str(cache_val, encoding='utf-8'))
    if cache_val.get('needchk', 'false') == 'true':
        del cache_val['needchk']
    shib_user = ShibUser(cache_val)
    account = request.form.get('WEKO_ATTR_ACCOUNT', None)
    password = request.form.get('WEKO_ATTR_PWD', None)
    if not shib_user.check_weko_user(account, password):
        datastore.delete(cache_key)
        return redirect(url_for_security('login'))
    shib_user.bind_relation_info()
    if shib_user.shib_user is not None:
        session['user_id'] = shib_user.user.id
        session['user_src'] = 'Shib'
        shib_user.shib_user_login()
    datastore.delete(cache_key)
    return redirect('/')


@blueprint.route('/shib/login', methods=['GET'])
def shib_login():
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
    if cache_val.get('needchk', 'false') == 'true':
        return render_template(
            config.WEKO_ACCOUNTS_CONFIRM_USER_TEMPLATE,
            shib_session_id=shib_session_id,
            email=cache_val['shib_mail'])
    shib_user = ShibUser(cache_val)
    shib_user.get_relation_info()
    if shib_user.shib_user is not None:
        session['user_id'] = shib_user.user.id
        session['user_src'] = 'Shib'
        shib_user.shib_user_login()
    datastore.delete(cache_key)
    return redirect('/')


@blueprint.route("/shib/login", methods=['POST'])
def shib_sp_login():
    """temp uri for test shibboleth user login
       the request from shibboleth sp
    """
    shib_session_id = request.form.get('SHIB_ATTR_SESSION_ID', None)
    if shib_session_id is None or len(shib_session_id) == 0:
        return abort(400, 'shib_session_id error')
    shib_attr, error = parse_attributes()
    if error:
        return abort(400, 'shib_attr error')
    shib_user = ShibUser(shib_attr)
    rst = shib_user.get_relation_info()
    datastore = RedisStore(redis.StrictRedis.from_url(
        current_app.config['CACHE_REDIS_URL']))
    # shibboleth session info cached on Redis
    ttl_sec = int(current_app.config['SHIB_ACCOUNTS_LOGIN_CACHE_TTL'])
    if isinstance(rst, str) and rst == 'chk':
        shib_attr['needchk'] = 'true'
    datastore.put(config.SHIB_CACHE_PREFIX + shib_session_id,
                  json.dumps(shib_attr),
                  ttl_secs=ttl_sec)
    query_string = {
        "SHIB_ATTR_SESSION_ID": shib_session_id,
        "SHIB_ATTR_MAIL": shib_attr.get('shib_mail'),
        "SHIB_ATTR_LOGIN_ID": shib_attr.get('shib_uid'),
        "_method": 'GET'
    }
    return redirect(url_for('weko_accounts.shib_login', **query_string))


@blueprint.route("/shib/sp/login", methods=['GET'])
def shib_stub_login():
    return render_template(config.WEKO_ACCOUNTS_STUB_USER_TEMPLATE)


@blueprint.route("/shib/logout")
def shib_logout():
    ShibUser.shib_user_logout()
    return "logout success"


def parse_attributes():
    """Parse arguments from environment variables."""
    attrs = {}
    error = False
    for header, attr in current_app.config['SSO_ATTRIBUTE_MAP'].items():
        required, name = attr
        value = request.form.get(header, None) if request.method == 'POST' \
            else request.args.get(header, None)

        attrs[name] = value
        if not value or value == '':
            if required:
                error = True
    return attrs, error


@blueprint.route('/shibboleth', methods=['GET', 'POST'])
@register_menu(
    blueprint, 'settings.shibuser',
    _('%(icon)s Shibboleth', icon='<i class="fa fa-user fa-fw"></i>'),
    order=14
)
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.shibuser',
    _('Shibboleth')
)
@login_required
def set_shibboleth_user():
    """
    Loading session setting page.

    :return: Lifetime in minutes.
    """
    shib_flg = '0'
    if current_app.config['SHIB_ACCOUNTS_LOGIN_ENABLED']:
        shib_flg = '1'

    if request.method == 'POST':
        # Process forms
        form = request.form.get('submit', None)
        if form == 'shib_form':
            shib_flg = request.form.get('shibbolethRadios', '0')
            if shib_flg == '1':
                _app.config['SHIB_ACCOUNTS_LOGIN_ENABLED'] = True
            else:
                _app.config['SHIB_ACCOUNTS_LOGIN_ENABLED'] = False
            flash(_('Shibboleth flag was updated.'), category='success')

    return render_template(config.WEKO_ACCOUNTS_SET_SHIB_TEMPLATE,
                           shib_flg=shib_flg)
