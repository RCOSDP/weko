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
import json

from flask import abort, current_app, flash, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from werkzeug.local import LocalProxy

from weko_admin.models import AdminSettings, db

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)

class ShibSettingView(BaseView):
    """ShibSettingView."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Index."""
        try:
            shib_flg = '0' if not AdminSettings.get('shib_login_enable').__dict__['shib_flg'] else '1'
            role_list = current_app.config['WEKO_ACCOUNTS_ROLE_LIST']
            attr_list = current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_LIST']
            set_language = _('language')

            # デフォルトロール
            default_roles = AdminSettings.get('default_role_settings')
            roles = {
                'gakunin_role': default_roles.__dict__['gakunin_role'],
                'orthros_outside_role': default_roles.__dict__['orthros_outside_role'],
                'extra_role': default_roles.__dict__['extra_role']
            }

            # 属性マッピング
            attribute_mappings = AdminSettings.get('attribute_mapping')
            attributes = {
                'shib_eppn': attribute_mappings.__dict__['shib_eppn'],
                'shib_role_authority_name': attribute_mappings.__dict__['shib_role_authority_name'],
                'shib_mail': attribute_mappings.__dict__['shib_mail'],
                'shib_user_name': attribute_mappings.__dict__['shib_user_name']
            }

            # ブロックユーザー
            block_user_settings = AdminSettings.get('blocked_user_settings')
            block_user_list = block_user_settings.__dict__['blocked_ePPNs']


            if request.method == 'POST':
                # Process forms
                form = request.form.get('submit', None)
                new_shib_flg = request.form.get('shibbolethRadios', '0')
                new_roles = {key: request.form.get(f'role-lists{i}', '0') for i, key in enumerate(roles)}

                if form == 'shib_form':
                    if shib_flg != new_shib_flg:
                        shib_flg = new_shib_flg
                        AdminSettings.update('shib_login_enable', {"shib_flg": (shib_flg == '1')})
                        
                        flash(_('Shibboleth flag was updated.'), category='success')
                    
                    for key in roles:
                        if roles[key] != new_roles[key]:
                            roles[key] = new_roles[key]
                            flash(_(f'{key.replace("_", " ").title()} was updated.'), category='success')
                        AdminSettings.update('default_role_settings', roles)
            
            self.get_latest_current_app()

            return self.render(
                current_app.config['WEKO_ACCOUNTS_SET_SHIB_TEMPLATE'],
                shib_flg=shib_flg, set_language=set_language, role_list=role_list, attr_list=attr_list, block_user_list=block_user_list, **roles, **attributes )
        
        except BaseException:
            current_app.logger.error(
                'Unexpected error: {}'.format(sys.exc_info()))
        return abort(400)
    
    def get_latest_current_app(self):
        _app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED'] = AdminSettings.get('shib_login_enable').__dict__['shib_flg']
        _app.config['WEKO_ACCOUNTS_GAKUNIN_ROLE']['defaultRole'] = AdminSettings.get('default_role_settings').__dict__['gakunin_role']
        _app.config['WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE']['defaultRole'] = AdminSettings.get('default_role_settings').__dict__['orthros_outside_role']
        _app.config['WEKO_ACCOUNTS_EXTRA_ROLE']['defaultRole'] = AdminSettings.get('default_role_settings').__dict__['extra_role']
        _app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP'] = AdminSettings.get('attribute_mapping').__dict__

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
