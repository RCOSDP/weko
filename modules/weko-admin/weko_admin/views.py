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

from datetime import timedelta

from flask import Blueprint, Flask, current_app, flash, jsonify, \
    render_template, request, session
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import default_breadcrumb_root, register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from werkzeug.local import LocalProxy

from . import config
from .models import SessionLifetime

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)

blueprint = Blueprint(
    'weko_admin',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/accounts/settings',
)


@blueprint.route('/session/lifetime/<int:minutes>', methods=['GET'])
def set_lifetime(minutes):
    """
    Update session lifetime in db.

    :param minutes:
    :return: Session lifetime updated message.
    """
    db_lifetime = SessionLifetime.get_validtime()
    if db_lifetime is None:
        db_lifetime = SessionLifetime(lifetime=minutes)
    else:
        db_lifetime.lifetime = minutes
    db_lifetime.create()
    _app.permanent_session_lifetime = timedelta(
        minutes=db_lifetime.lifetime)
    return jsonify(code=0, msg='Session lifetime was updated.')


@blueprint.route('/session', methods=['GET', 'POST'])
@blueprint.route('/session/', methods=['GET', 'POST'])
@register_menu(
    blueprint, 'settings.lifetime',
    _('%(icon)s Session', icon='<i class="fa fa-cogs fa-fw"></i>'),
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

    return render_template(current_app.config['WEKO_ADMIN_LIFETIME_TEMPLATE'],
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
