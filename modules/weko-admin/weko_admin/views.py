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

"""Views for weko-admin."""

import sys

from datetime import timedelta

from flask import abort, Blueprint, current_app, flash, jsonify, \
    render_template, request, session
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from invenio_admin.proxies import current_admin
from werkzeug.local import LocalProxy

from .models import SessionLifetime

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)

blueprint = Blueprint(
    'weko_admin',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/accounts/settings',
)


def _has_admin_access():
    """Use to check if a user has any admin access."""
    return current_user.is_authenticated and current_admin \
        .permission_factory(current_admin.admin.index_view).can()


@blueprint.route('/session/lifetime/<int:minutes>', methods=['GET'])
def set_lifetime(minutes):
    """
    Update session lifetime in db.

    :param minutes:
    :return: Session lifetime updated message.
    """
    try:
        db_lifetime = SessionLifetime.get_validtime()
        if db_lifetime is None:
            db_lifetime = SessionLifetime(lifetime=minutes)
        else:
            db_lifetime.lifetime = minutes
        db_lifetime.create()
        _app.permanent_session_lifetime = timedelta(
            minutes=db_lifetime.lifetime)
        return jsonify(code=0, msg='Session lifetime was updated.')
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        return abort(400)


@blueprint.route('/session', methods=['GET', 'POST'])
@blueprint.route('/session/', methods=['GET', 'POST'])
@register_menu(
    blueprint, 'settings.lifetime',
    _('%(icon)s Session', icon='<i class="fa fa-cogs fa-fw"></i>'),
    visible_when=_has_admin_access,
    order=14
)
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.session',
    _('Session')
)
@login_required
def lifetime():
    """
    Loading session setting page.

    :return: Lifetime in minutes.
    """
    if not _has_admin_access():
        return abort(403)
    try:
        db_lifetime = SessionLifetime.get_validtime()
        if db_lifetime is None:
            db_lifetime = SessionLifetime(lifetime=30)

        if request.method == 'POST':
            # Process forms
            form = request.form.get('submit', None)
            if form == 'lifetime':
                new_lifetime = request.form.get('lifetimeRadios', '30')
                db_lifetime.lifetime = int(new_lifetime)
                db_lifetime.create()
                _app.permanent_session_lifetime = timedelta(
                    minutes=db_lifetime.lifetime)
                flash(_('Session lifetime was updated.'), category='success')

        return render_template(
            current_app.config['WEKO_ADMIN_LIFETIME_TEMPLATE'],
            current_lifetime=str(db_lifetime.lifetime),
            map_lifetime=[('15', _('15 mins')),
                          ('30', _('30 mins')),
                          ('45', _('45 mins')),
                          ('60', _('60 mins')),
                          ('180', _('180 mins')),
                          ('360', _('360 mins')),
                          ('720', _('720 mins')),
                          ('1440', _('1440 mins'))]
        )
    except ValueError as valueErr:
        current_app.logger.error(
            'Could not convert data to an integer: {0}'.format(valueErr))
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        return abort(400)


@blueprint.route("/session/offline/info", methods=['GET'])
def session_info_offline():
    """
    Get session lifetime from app setting.

    :return: Session information offline in json.
    """
    current_app.logger.info('request session_info by offline')
    session_id = session.sid_s if hasattr(session, 'sid_s') else 'None'
    lifetime_str = str(current_app.config['PERMANENT_SESSION_LIFETIME'])
    return jsonify(user_id=current_user.get_id(),
                   session_id=session_id,
                   lifetime=lifetime_str,
                   _app_lifetime=str(_app.permanent_session_lifetime),
                   current_app_name=current_app.name)


@blueprint.route("/admin/site-license")
@blueprint.route("/admin/site-license/")
def site_license():
    """
    Site license setting page.

    """
    current_app.logger.info('site-license setting page')
    return render_template(
        current_app.config['WEKO_ADMIN_SITE_LICENSE_TEMPLATE'])


@blueprint.route("/admin/block-style", methods=['GET', 'POST'])
@blueprint.route("/admin/block-style/", methods=['GET', 'POST'])
def block_style():
    """
    Block style setting page.

    """
    body_bg = '#fff'
    footer_default_bg = '#8a8a8a'
    navbar_default_bg = '#f8f8f8'
    panel_default_border = '#ddd'
    scss_file = '/home/invenio/.virtualenvs/invenio/var/instance/static/css/weko_theme/_variables.scss'
    try:
        if request.method == 'POST':
            form_lines = []
            body_bg = request.form.get('body-bg', '#fff')
            footer_default_bg = request.form.get('footer-default-bg', '#8a8a8a')
            navbar_default_bg = request.form.get('navbar-default-bg', '#f8f8f8')
            panel_default_border = request.form.get(
                'panel-default-border', '#ddd')
            form_lines.append(
                '$body-bg: ' + body_bg + ';')
            form_lines.append(
                '$footer-default-bg: ' + footer_default_bg + ';')
            form_lines.append(
                '$navbar-default-bg: ' + navbar_default_bg + ';')
            form_lines.append(
                '$panel-default-border: ' + panel_default_border + ';')
            with open(scss_file, 'w', encoding='utf-8') as fp:
                fp.writelines('\n'.join(form_lines))
        if request.method == 'GET':
            with open(scss_file, 'r', encoding='utf-8') as fp:
                for line in fp.readlines():
                    line = line.strip()
                    if '$body-bg:' in line:
                        body_bg = line[line.find('#'):-1]
                    if '$footer-default-bg:' in line:
                        footer_default_bg = line[line.find('#'):-1]
                    if '$navbar-default-bg:' in line:
                        navbar_default_bg = line[line.find('#'):-1]
                    if '$panel-default-border:' in line:
                        panel_default_border = line[line.find('#'):-1]
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return render_template(
        current_app.config['WEKO_ADMIN_BlOCK_STYLE_TEMPLATE'],
        body_bg=body_bg,
        footer_default_bg=footer_default_bg,
        navbar_default_bg=navbar_default_bg,
        panel_default_border=panel_default_border
    )
