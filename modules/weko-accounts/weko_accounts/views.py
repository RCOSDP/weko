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
import re
import traceback
from urllib.parse import quote_plus

from flask import Blueprint, abort, current_app, flash, redirect, \
    render_template, request, session, url_for
from flask_babelex import gettext as _
from flask_login import current_user
from flask_menu import current_menu
from flask_security import url_for_security
from invenio_admin.proxies import current_admin
from weko_redis.redis import RedisConnection
from werkzeug.local import LocalProxy
from invenio_db import db
from weko_admin.models import AdminSettings, db
from weko_logging.activity_logger import UserActivityLogger

from .api import ShibUser, sync_shib_gakunin_map_groups
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

@blueprint.before_app_first_request
def _adjust_shib_admin_DB():
    """
    Create or Update Shibboleth Admin database table.
    """
    if current_app.config.get('TESTING', False):  # テスト環境では何もしない
        return

    with _app.app_context():
        if AdminSettings.query.filter_by(name='blocked_user_settings').first() is None:
            max_id = db.session.query(db.func.max(AdminSettings.id)).scalar()
            new_setting = AdminSettings(
                id=max_id + 1,
                name="blocked_user_settings",
                settings={"blocked_ePPNs": []}
            )
            db.session.add(new_setting)
            db.session.commit()

        if AdminSettings.query.filter_by(name='shib_login_enable').first() is None:
            max_id = db.session.query(db.func.max(AdminSettings.id)).scalar()
            new_setting = AdminSettings(
                id=max_id + 1,
                name="shib_login_enable",
                settings={"shib_flg": _app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED']}
            )
            db.session.add(new_setting)
            db.session.commit()
        else:
            setting = AdminSettings.query.filter_by(name='shib_login_enable').first()
            setting.settings = {"shib_flg": _app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED']}
            db.session.commit()

        if AdminSettings.query.filter_by(name='default_role_settings').first() is None:
            max_id = db.session.query(db.func.max(AdminSettings.id)).scalar()
            new_setting = AdminSettings(
                id=max_id + 1,
                name="default_role_settings",
                settings={
                    "gakunin_role": _app.config['WEKO_ACCOUNTS_GAKUNIN_ROLE']['defaultRole'],
                    "orthros_outside_role": _app.config['WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE']['defaultRole'],
                    "extra_role": _app.config['WEKO_ACCOUNTS_EXTRA_ROLE']['defaultRole']}
            )
            db.session.add(new_setting)
            db.session.commit()
        else:
            setting = AdminSettings.query.filter_by(name='default_role_settings').first()
            setting.settings = {
                "gakunin_role": _app.config['WEKO_ACCOUNTS_GAKUNIN_ROLE']['defaultRole'],
                "orthros_outside_role": _app.config['WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE']['defaultRole'],
                "extra_role": _app.config['WEKO_ACCOUNTS_EXTRA_ROLE']['defaultRole']}
            db.session.commit()

        if AdminSettings.query.filter_by(name='attribute_mapping').first() is None:
            max_id = db.session.query(db.func.max(AdminSettings.id)).scalar()
            new_setting = AdminSettings(
                id=max_id + 1,
                name="attribute_mapping",
                settings=_app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']
            )
            db.session.add(new_setting)
            db.session.commit()
        else:
            setting = AdminSettings.query.filter_by(name='attribute_mapping').first()
            setting.settings = _app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']
            db.session.commit()


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
        shib_session_id = request.args.get('Shib-Session-ID', None)
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

        cache_val = json.loads(str(cache_val, encoding='utf-8'))
        shib_user = ShibUser(cache_val)
        if not is_auto_bind:
            shib_user.get_relation_info()
        else:
            shib_user.new_relation_info()

        error = shib_user.check_in()

        if error:
            datastore.delete(cache_key)
            current_app.logger.error(error)
            flash(error, category='error')
            return _redirect_method()

        if shib_user.shib_user:
            shib_user.shib_user_login()

        datastore.delete(cache_key)
        db.session.commit()
        UserActivityLogger.info(
            operation="LOGIN",
            target_key=shib_user.user.id,
            remarks="Shibboleth login"
        )
        return redirect(session['next'] if 'next' in session else '/')
    except BaseException:
        db.session.rollback()
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
        exec_info = sys.exc_info()
        tb_info = traceback.format_tb(exec_info[2])
        UserActivityLogger.error(
            operation="LOGIN",
            remarks=tb_info[0]
        )
    return abort(400)


@blueprint.route('/confim/user', methods=['POST'])
def confirm_user():
    """Check weko user info.

    :return:
    """
    try:
        if request.form.get('csrf_random', '') != session['csrf_random']:
            flash('csrf_random', category='error')
            return _redirect_method()

        shib_session_id = session['shib_session_id']
        if not shib_session_id:
            flash('shib_session_id', category='error')
            return _redirect_method()

        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        cache_key = current_app.config[
            'WEKO_ACCOUNTS_SHIB_CACHE_PREFIX'] + shib_session_id

        if not datastore.redis.exists(cache_key):
            flash('cache_key', category='error')
            return _redirect_method()

        cache_val = datastore.get(cache_key)
        if not cache_val:
            flash('cache_val', category='error')
            datastore.delete(cache_key)
            return _redirect_method()

        cache_val = json.loads(str(cache_val, encoding='utf-8'))
        shib_user = ShibUser(cache_val)
        account = request.form.get('WEKO_ATTR_ACCOUNT', None)
        password = request.form.get('WEKO_ATTR_PWD', None)
        if not shib_user.check_weko_user(account, password):
            flash('check_weko_user', category='error')
            datastore.delete(cache_key)
            return _redirect_method()

        if not shib_user.bind_relation_info(account):
            flash('FAILED bind_relation_info!', category='error')
            return _redirect_method()

        error = shib_user.check_in()

        if error:
            datastore.delete(cache_key)
            flash(error, category='error')
            return _redirect_method()

        if shib_user.shib_user:
            shib_user.shib_user_login()
        datastore.delete(cache_key)
        UserActivityLogger.info(
            operation="LOGIN",
            target_key=shib_user.user.id,
            remarks="Shibboleth login"
        )
        return redirect(session['next'] if 'next' in session else '/')
    except BaseException:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
        exec_info = sys.exc_info()
        tb_info = traceback.format_tb(exec_info[2])
        UserActivityLogger.error(
            operation="LOGIN",
            remarks=tb_info[0]
        )
    return abort(400)


@blueprint.route('/confim/user/skip', methods=['GET'])
def confirm_user_without_page():
    """Check weko user info without page.

    :return:
    """
    try:
        # get shib_session_id from session
        shib_session_id = request.args.get('Shib-Session-ID', None)
        if not shib_session_id:
            flash('shib_session_id', category='error')
            return _redirect_method()

        # get cache from redis
        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        cache_key = current_app.config[
            'WEKO_ACCOUNTS_SHIB_CACHE_PREFIX'] + shib_session_id

        # check cache
        if not datastore.redis.exists(cache_key):
            flash('cache_key', category='error')
            return _redirect_method()

        cache_val = datastore.get(cache_key)
        if not cache_val:
            flash('cache_val', category='error')
            datastore.delete(cache_key)
            return _redirect_method()

        cache_val = json.loads(str(cache_val, encoding='utf-8'))
        shib_user = ShibUser(cache_val)

        # bind relation info
        if not shib_user.bind_relation_info(cache_val.get('shib_mail')):
            flash('FAILED bind_relation_info!', category='error')
            datastore.delete(cache_key)
            return _redirect_method()

        # check in
        error = shib_user.check_in()

        if error:
            datastore.delete(cache_key)
            flash(error, category='error')
            return _redirect_method()

        if shib_user.shib_user:
            shib_user.shib_user_login()
        datastore.delete(cache_key)
        return redirect(request.args.get('next', '/'))
    except BaseException:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
    return abort(400)


@blueprint.route('/shib/login', methods=['GET'])
def shib_login():
    """Get shibboleth user login page.

    :return: confirm user page when relation is empty
    """
    try:
        shib_session_id = request.args.get('Shib-Session-ID', None)
        session['next'] = request.args.get('next', '/')

        if not shib_session_id:
            current_app.logger.error(_("Missing Shib-Session-ID!"))
            flash(_("Missing Shib-Session-ID!"), category='error')
            return _redirect_method()

        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        cache_key = current_app.config[
            'WEKO_ACCOUNTS_SHIB_CACHE_PREFIX'] + shib_session_id

        if not datastore.redis.exists(cache_key):
            current_app.logger.error(_("Missing SHIB_CACHE_PREFIX!"))
            flash(_("Missing SHIB_CACHE_PREFIX!"), category='error')
            return _redirect_method()

        cache_val = datastore.get(cache_key)

        if not cache_val:
            current_app.logger.error(_("Missing SHIB_ATTR!"))
            flash(_("Missing SHIB_ATTR!"), category='error')
            datastore.delete(cache_key)
            return _redirect_method()

        cache_val = json.loads(str(cache_val, encoding='utf-8'))
        session['shib_session_id'] = shib_session_id
        csrf_random = generate_random_str(length=64)
        session['csrf_random'] = csrf_random

        user = find_user_by_email(cache_val)

        return render_template(
            current_app.config['WEKO_ACCOUNTS_CONFIRM_USER_TEMPLATE'],
            csrf_random=csrf_random,
            email=user.email if user else ''
        )
    except BaseException:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
    return abort(400)

def find_user_by_email(shib_attributes):
    """Find user by email."""
    _datastore = LocalProxy(
            lambda: current_app.extensions['security'].datastore)
    user = _datastore.find_user(email=shib_attributes.get('shib_mail'))

    return user

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
        # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPSがTrueのときの処理
        if current_app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS']:
            sync_shib_gakunin_map_groups()

        shib_session_id = request.form.get('Shib-Session-ID', None)
        if not shib_session_id and not _shib_enable:
            flash(_("Missing Shib-Session-ID!"), category='error')
            return redirect(url_for_security('login'))

        shib_attr, error = parse_attributes()

        # Check SHIB_ATTR_EPPN and SHIB_ATTR_USER_NAME:
        if error or not (
                shib_attr.get('shib_eppn', None)
                or _shib_username_config and shib_attr.get('shib_user_name')):
            flash(_("Missing SHIB_ATTRs!"), category='error')
            return _redirect_method()

        # Check if shib_eppn is not included in the blocked user list
        if AdminSettings.query.filter_by(name='blocked_user_settings').first():
            block_user_settings = AdminSettings.get('blocked_user_settings', dict_to_object=False)
            if isinstance(block_user_settings, str):
                block_user_settings = json.loads(block_user_settings)
            block_user_list = block_user_settings.get('blocked_ePPNs', [])
            shib_eppn = shib_attr.get('shib_eppn')

            # Convert wildcards to regular expressions
            def _wildcard_to_regex(pattern):
                regex_pattern = pattern.replace("*", ".*")
                return re.compile(f"^{regex_pattern}$")

            blocked = any(_wildcard_to_regex(pattern).match(shib_eppn) or pattern == shib_eppn for pattern in block_user_list)

            if blocked:
                flash(_("Failed to login."), category='error')
                return _redirect_method()

        # Redis connection
        redis_connection = RedisConnection()
        datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
        ttl_sec = int(current_app.config[
            'WEKO_ACCOUNTS_SHIB_LOGIN_CACHE_TTL'])
        datastore.put(
            current_app.config[
                'WEKO_ACCOUNTS_SHIB_CACHE_PREFIX'] + shib_session_id,
            bytes(json.dumps(shib_attr), encoding='utf-8'),
            ttl_secs=ttl_sec)

        shib_user = ShibUser(shib_attr)
        # Check the relation of shibboleth user with weko account.
        rst = shib_user.get_relation_info()

        next_url = 'weko_accounts.shib_auto_login'

        query_string = {
            'Shib-Session-ID': shib_session_id,
            'next': next,
            '_method': 'GET'
        }

        if not rst:
            if current_app.config['WEKO_ACCOUNTS_SKIP_CONFIRMATION_PAGE']:
                user = find_user_by_email(shib_attr)
                if user:
                    next_url = 'weko_accounts.confirm_user_without_page'
                else:
                    session['shib_session_id'] = shib_session_id
                    del query_string['Shib-Session-ID']
            else:
                # Relation is not existed, cache shibboleth info to redis.
                next_url = 'weko_accounts.shib_login'

        return url_for(next_url, **query_string)
    except BaseException:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
        return _redirect_method()


@blueprint.route('/shib/sp/login', methods=['GET'])
def shib_stub_login():
    """Shibboleth SP login redirect.

    :return:
    """
    _shib_login_url = current_app.config['WEKO_ACCOUNTS_SHIB_IDP_LOGIN_URL']
    if not current_app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED']:
        return abort(403)

    session['next'] = request.args.get('next', '/')
    return_url = _shib_login_url.format(request.url_root)

    sp_entityID = "https://" + current_app.config["WEB_HOST_NAME"]+"/shibboleth-sp"
    if 'SP_ENTITYID' in current_app.config:
        sp_entityID = current_app.config['SP_ENTITYID']

    sp_handlerURL = "https://" + current_app.config["WEB_HOST_NAME"]+"/Shibboleth.sso"
    if 'SP_HANDLERURL' in current_app.config:
        sp_handlerURL = current_app.config['SP_HANDLERURL']

    # LOGIN USING JAIROCLOUD PAGE
    if current_app.config['WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED']:
        return redirect(_shib_login_url.format(request.url_root)+ '?next=' + request.args.get('next', '/'))
    else:
        return render_template(
            current_app.config[
                'WEKO_ACCOUNTS_SECURITY_LOGIN_SHIB_USER_TEMPLATE'],
            sp_entityID = sp_entityID,
            sp_handlerURL = sp_handlerURL,
            return_url = return_url,
            module_name=_('WEKO-Accounts'))


@blueprint.app_template_filter('urlencode')
def urlencode(value):
    """Encode url value."""
    return quote_plus(value)

@blueprint.route('/shib/logout')
def shib_logout():
    """Shibboleth user logout.

    :return:
    """
    user_id = current_user.id
    ShibUser.shib_user_logout()
    UserActivityLogger.info(
        operation="LOGOUT",
        target_key=user_id,
        remarks="Shibboleth logout"
    )
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
