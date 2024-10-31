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

import orjson
import sys

import redis
from redis import sentinel
from flask import Blueprint, abort, current_app, flash, redirect, \
    render_template, request, session, url_for
from flask_babelex import gettext as _
from flask_login import current_user
from flask_menu import current_menu
from flask_security import url_for_security
from invenio_admin.proxies import current_admin
from simplekv.memory.redisstore import RedisStore
from weko_redis.redis import RedisConnection
from werkzeug.local import LocalProxy
from invenio_db import db
from sqlalchemy.exc import SQLAlchemyError

from .api import ShibUser
from .utils import generate_random_str, parse_attributes

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


@blueprint.before_app_first_request
def init_menu():
    """Initialize menu before first request."""
    # current_app.logger.debug(current_menu)
    item = current_menu.submenu('settings.admin')
    item.register(
        "admin.index",
        # NOTE: Menu item text (icon replaced by a cogs icon).
        _('%(icon)s Administration', icon='<i class="fa fa-cogs fa-fw"></i>'),
        visible_when=_has_admin_access,
        order=100)


def _redirect_method(has_next=False):
    """Redirect method for instance login to IdP."""
    shib_login = current_app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED']
    shib_login_url = current_app.config['WEKO_ACCOUNTS_SHIB_IDP_LOGIN_URL']
    idp_login = current_app.config['WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED']
    idp_login_inst = current_app.config[
        'WEKO_ACCOUNTS_SHIB_INST_LOGIN_DIRECTLY_ENABLED']

    if shib_login and idp_login and idp_login_inst:
        url = shib_login_url.format(request.url_root)
        if has_next:
            url += '?next=' + request.full_path
        return redirect(url)
    else:
        return redirect(url_for_security(
            'login',
            next=request.full_path if has_next else None))


@blueprint.route('/')
def index():
    """Render a basic view."""
    return render_template(
        'weko_accounts/index.html',
        module_name=_('WEKO-Accounts'))


@blueprint.route('/auto/login', methods=['GET'])
def shib_auto_login():
    """Create new account and auto login when shibboleth user first login.

    :return: next url
    """
    try:
        is_auto_bind = False
        shib_session_id = request.args.get('SHIB_ATTR_SESSION_ID', None)
        session['next'] = request.args.get('next', '/')

        if not shib_session_id:
            shib_session_id = session['shib_session_id']
            is_auto_bind = True

        if not shib_session_id:
            return _redirect_method()

        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        cache_key = current_app.config[
            'WEKO_ACCOUNTS_SHIB_CACHE_PREFIX'] + shib_session_id
        if not datastore.redis.exists(cache_key):
            return _redirect_method()

        cache_val = datastore.get(cache_key)
        if not cache_val:
            datastore.delete(cache_key)
            return _redirect_method()

        cache_val = orjson.loads(str(cache_val, encoding='utf-8'))
        shib_user = ShibUser(cache_val)
        
        try:
            if not is_auto_bind:
                shib_user.get_relation_info()
            else:
                shib_user.new_relation_info()
        except SQLAlchemyError as e:
            flash(_("Failed login cause failed update user data."), category='danger')
            return _redirect_method()

        error = shib_user.check_in()

        if error:
            datastore.delete(cache_key)
            current_app.logger.error(error)
            flash(error, category='denger')
            return _redirect_method()

        if shib_user.shib_user:
            shib_user.shib_user_login()

        datastore.delete(cache_key)
        return redirect(session['next'] if 'next' in session else '/')
    except BaseException:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
    return abort(400)


@blueprint.route('/confim/user', methods=['POST'])
def confirm_user():
    """Check weko user info.

    :return:
    """
    try:
        if request.form.get('csrf_random', '') != session['csrf_random']:
            flash('csrf_random error', category='denger')
            return _redirect_method()

        shib_session_id = session['shib_session_id']
        if not shib_session_id:
            flash('shib_session_id error', category='denger')
            return _redirect_method()

        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        cache_key = current_app.config[
            'WEKO_ACCOUNTS_SHIB_CACHE_PREFIX'] + shib_session_id

        if not datastore.redis.exists(cache_key):
            flash('cache_key error', category='denger')
            return _redirect_method()

        cache_val = datastore.get(cache_key)
        if not cache_val:
            flash('cache_val error', category='denger')
            datastore.delete(cache_key)
            return _redirect_method()

        cache_val = orjson.loads(str(cache_val, encoding='utf-8'))
        shib_user = ShibUser(cache_val)
        account = request.form.get('WEKO_ATTR_ACCOUNT', None)
        password = request.form.get('WEKO_ATTR_PWD', None)
        if not shib_user.check_weko_user(account, password):
            flash('check_weko_user error', category='denger')
            datastore.delete(cache_key)
            return _redirect_method()

        if not shib_user.bind_relation_info(account):
            flash('FAILED bind_relation_info!', category='denger')
            datastore.delete(cache_key)
            return _redirect_method()

        error = shib_user.check_in()

        if error:
            datastore.delete(cache_key)
            flash(error, category='denger')
            return _redirect_method()

        if shib_user.shib_user:
            shib_user.shib_user_login()
        datastore.delete(cache_key)
        return redirect(session['next'] if 'next' in session else '/')
    except BaseException:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
        if cache_key and datastore.redis.exists(cache_key):
            datastore.delete(cache_key)
    return abort(400)


@blueprint.route('/shib/login', methods=['GET'])
def shib_login():
    """Get shibboleth user login page.

    :return: confirm user page when relation is empty
    """
    try:
        shib_session_id = request.args.get('SHIB_ATTR_SESSION_ID', None)
        session['next'] = request.args.get('next', '/')

        if not shib_session_id:
            current_app.logger.error(_("Missing SHIB_ATTR_SESSION_ID!"))
            flash(_("Missing SHIB_ATTR_SESSION_ID!"), category='denger')
            return _redirect_method()

        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        cache_key = current_app.config[
            'WEKO_ACCOUNTS_SHIB_CACHE_PREFIX'] + shib_session_id

        if not datastore.redis.exists(cache_key):
            current_app.logger.error(_("Missing SHIB_CACHE_PREFIX!"))
            flash(_("Missing SHIB_CACHE_PREFIX!"), category='denger')
            return _redirect_method()

        cache_val = datastore.get(cache_key)

        if not cache_val:
            current_app.logger.error(_("Missing SHIB_ATTR!"))
            flash(_("Missing SHIB_ATTR!"), category='denger')
            datastore.delete(cache_key)
            return _redirect_method()

        cache_val = orjson.loads(str(cache_val, encoding='utf-8'))
        session['shib_session_id'] = shib_session_id
        csrf_random = generate_random_str(length=64)
        session['csrf_random'] = csrf_random

        _datastore = LocalProxy(
            lambda: current_app.extensions['security'].datastore)
        user = _datastore.find_user(
            email=cache_val.get('shib_mail'))

        return render_template(
            current_app.config['WEKO_ACCOUNTS_CONFIRM_USER_TEMPLATE'],
            csrf_random=csrf_random,
            email=user.email if user else ''
        )
    except BaseException:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
    return abort(400)


@blueprint.route('/shib/login', methods=['POST'])
def shib_sp_login():
    """The request from shibboleth sp.

    :return: confirm page when relation is empty
    """
    _shib_enable = current_app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED']
    _shib_username_config = current_app.config[
        'WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN']
    next = request.args.get('next', '/')
    try:
        shib_session_id = request.form.get('SHIB_ATTR_SESSION_ID', None)
        if not shib_session_id and not _shib_enable:
            current_app.logger.error("Missing SHIB_ATTR_SESSION_ID.")
            error_redirect_params = {
                'SHIB_ATTR_SESSION_ID': '',
                'next': next,
                'msg': _("Missing SHIB_ATTR_SESSION_ID!"),
                '_method': 'GET'
            }
            return url_for("weko_accounts.shib_login_error", **error_redirect_params)

        shib_attr, error = parse_attributes()
        error_msg = None

        # Check SHIB_ATTR_EPPN and SHIB_ATTR_USER_NAME:
        if error or not (
                shib_attr.get('shib_eppn', None)
                or _shib_username_config and shib_attr.get('shib_user_name')):
            error_msg = _("Missing SHIB_ATTRs.")
            current_app.logger.error("Missing SHIB_ATTRs!")
        
        # Check SHIB_ATTR_ACTIVE_FLAG:
        if shib_attr.get('shib_active_flag', None) == "FALSE": # `shib_active_flag=''` is not error
            error_msg = _("shib_active_flag_error")
            current_app.logger.error("shib_active_flag_error({})".format(shib_attr.get('shib_eppn', None)))
        
        # Check SHIB_ATTR_SITE_USER_WITHIN_IP_RANGE_FLAG:
        if shib_attr.get('shib_ip_range_flag', None) == "FALSE": # `shib_ip_range_flag=''` is not error
            error_msg = _("shib_ip_range_flag_error")
            current_app.logger.error("shib_ip_range_flag_error({})".format(shib_attr.get('shib_eppn', None)))
        
        if error_msg:
            error_redirect_params = {
                'SHIB_ATTR_SESSION_ID': shib_session_id,
                'next': next,
                'msg': error_msg,
                '_method': 'GET'
            }
            return url_for("weko_accounts.shib_login_error", **error_redirect_params)

        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        ttl_sec = int(current_app.config[
            'WEKO_ACCOUNTS_SHIB_LOGIN_CACHE_TTL'])
        datastore.put(
            current_app.config[
                'WEKO_ACCOUNTS_SHIB_CACHE_PREFIX'] + shib_session_id,
            orjson.dumps(shib_attr),
            ttl_secs=ttl_sec)

        shib_user = ShibUser(shib_attr)

        # Check the relation of shibboleth user with weko account.
        try:
            rst = shib_user.get_relation_info()
        except SQLAlchemyError as e:
            # Failed to update user data.
            current_app.logger.error("SQLAlchemyError: {}".format(e))
            error_redirect_params = {
                'SHIB_ATTR_SESSION_ID': shib_session_id,
                'next': next,
                'msg': _('Failed login cause failed update user data.'),
                '_method': 'GET'
            }
            return url_for("weko_accounts.shib_login_error", **error_redirect_params)

        next_url = 'weko_accounts.shib_auto_login'
        if not rst:
            # Relation is not existed, cache shibboleth info to redis.
            next_url = 'weko_accounts.shib_login'

        query_string = {
            'SHIB_ATTR_SESSION_ID': shib_session_id,
            'next': next,
            '_method': 'GET'
        }
        return url_for(next_url, **query_string)
    except BaseException:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
        error_redirect_params = {
            'SHIB_ATTR_SESSION_ID': shib_session_id,
            'next': next,
            'msg': _('Unexpected error occurred.'),
            '_method': 'GET'
        }
        return url_for("weko_accounts.shib_login_error", **error_redirect_params)


@blueprint.route('/shib/sp/login', methods=['GET'])
def shib_stub_login():
    """Shibboleth SP login redirect.

    :return:
    """
    _shib_login_url = current_app.config['WEKO_ACCOUNTS_SHIB_IDP_LOGIN_URL']
    if not current_app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED']:
        return abort(403)

    session['next'] = request.args.get('next', '/')

    # LOGIN USING JAIROCLOUD PAGE
    if current_app.config['WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED']:
        return redirect(_shib_login_url.format(request.url_root)
                        + '?next='
                        + request.args.get('next', '/'))
    else:
        return render_template(
            current_app.config[
                'WEKO_ACCOUNTS_SECURITY_LOGIN_SHIB_USER_TEMPLATE'],
            module_name=_('WEKO-Accounts'))


@blueprint.route('/shib/error', methods=['GET'])
def shib_login_error():
    """Shibboleth SP login error.

    :return:
    """
    msg = request.args.get('msg', '')
    if msg:
        flash(msg, category='danger')
        """
        Note:
            category can be one of ['info', 'danger', 'warning', 'success'], otherwise it will be 'info'.
            
            The cause is invenio_theme@1.0.0b4
                invenio_theme/templates/invenio_theme/macros/messages.html
        """
    next = request.args.get('next', '/')
    return redirect(next)


@blueprint.route('/shib/logout')
def shib_logout():
    """Shibboleth user logout.

    :return:
    """
    ShibUser.shib_user_logout()
    return 'logout success'

@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_accounts dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()