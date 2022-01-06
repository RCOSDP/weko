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

"""WEKO3 module docstring."""

import sys

from flask import abort, current_app, flash, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from werkzeug.local import LocalProxy

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)


class ShibSettingView(BaseView):
    """ShibSettingView."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Index."""
        try:
            shib_flg = '0'
            if current_app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED']:
                shib_flg = '1'

            if request.method == 'POST':
                # Process forms
                form = request.form.get('submit', None)
                if form == 'shib_form':
                    shib_flg = request.form.get('shibbolethRadios', '0')
                    if shib_flg == '1':
                        _app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED'] = True
                    else:
                        _app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED'] = False
                    flash(
                        _('Shibboleth flag was updated.'),
                        category='success')

            return self.render(
                current_app.config['WEKO_ACCOUNTS_SET_SHIB_TEMPLATE'],
                shib_flg=shib_flg)
        except BaseException:
            current_app.logger.error(
                'Unexpected error: {}'.format(sys.exc_info()))
        return abort(400)


shib_adminview = {
    'view_class': ShibSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Shibboleth'),
        'endpoint': 'shibboleth'
    }
}

__all__ = (
    'shib_adminview',
    'ShibSettingView',
)
