# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""WEKO3 module docstring."""

import sys

from flask import abort, current_app, flash, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from werkzeug.local import LocalProxy

from . import config

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)


class ShibSettingView(BaseView):
    """ShibSettingView."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Index."""
        try:
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
                    flash(
                        _('Shibboleth flag was updated.'),
                        category='success')

            return self.render(config.WEKO_ACCOUNTS_SET_SHIB_TEMPLATE,
                               shib_flg=shib_flg)
        except BaseException:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
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
