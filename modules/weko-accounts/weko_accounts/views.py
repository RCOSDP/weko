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

from flask import Blueprint, current_app, render_template, redirect, request, \
    session
from flask_babelex import gettext as _

from .api import ShibUser

blueprint = Blueprint(
    'weko_accounts',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix="/weko",
)


@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        "weko_accounts/index.html",
        module_name=_('WEKO-Accounts'))


@blueprint.route("/shib/login", methods=['GET', 'POST'])
def shib_login():
    """temp uri for test shibboleth user login"""
    shib_attr, error = parse_attributes()
    if error:
        return "login failed"
    shib_user = ShibUser(shib_attr)
    shib_user.get_relation_info()
    if shib_user.shib_user is not None:
        session['user_id'] = shib_user.user.id
        session['user_src'] = 'Shib'
        shib_user.shib_user_login()
    return redirect('/')


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
        value = request.form.get(header, None)

        attrs[name] = value
        if not value or value == '':
            if required:
                error = True
    return attrs, error
