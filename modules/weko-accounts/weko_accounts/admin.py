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
            shib_flg = '0' if not current_app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED'] else '1'
            role_list = current_app.config['WEKO_ACCOUNTS_ROLE_LIST']
            attr_list = current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_LIST']
            set_language = _('language')

            # 'blocked_user_settings' が存在しない場合、新しいレコードを追加
            if AdminSettings.query.filter_by(name='blocked_user_settings').first() is None:
                new_setting = AdminSettings(
                    id=6,
                    name="blocked_user_settings",
                    settings={"blocked_ePPNs": []}
                )
                db.session.add(new_setting)
                db.session.commit()
            block_user_settings = AdminSettings.get('blocked_user_settings')
            block_user_list = block_user_settings.__dict__['blocked_ePPNs']

            # デフォルトロール
            roles = {
                'gakunin_role': current_app.config.get('WEKO_ACCOUNTS_GAKUNIN_ROLE', {}).get('defaultRole', '0'),
                'orthros_outside_role': current_app.config.get('WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE', {}).get('defaultRole', '0'),
                'extra_role': current_app.config.get('WEKO_ACCOUNTS_EXTRA_ROLE', {}).get('defaultRole', '0')
            }

            # 属性マッピング
            attributes = {
                'weko_eppn_value': current_app.config.get('WEKO_ACCOUNTS_ATTRIBUTE_MAP', {}).get('shib_eppn', '0'),
                'weko_role_authority_name_value': current_app.config.get('WEKO_ACCOUNTS_ATTRIBUTE_MAP', {}).get('shib_role_authority_name', '0'),
                'weko_mail_value': current_app.config.get('WEKO_ACCOUNTS_ATTRIBUTE_MAP', {}).get('shib_mail', '0'),
                'weko_user_name_value': current_app.config.get('WEKO_ACCOUNTS_ATTRIBUTE_MAP', {}).get('shib_user_name', '0')
            }

            if request.method == 'POST':
                # Process forms
                form = request.form.get('submit', None)
                new_shib_flg = request.form.get('shibbolethRadios', '0')
                new_roles = {key: request.form.get(f'role-lists{i}', '0') for i, key in enumerate(roles)}

                if form == 'shib_form':
                    if shib_flg != new_shib_flg:
                        shib_flg = new_shib_flg
                        _app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED'] = (shib_flg == '1')
                        flash(_('Shibboleth flag was updated.'), category='success')
                    
                    for key in roles:
                        if roles[key] != new_roles[key]:
                            roles[key] = new_roles[key]
                            _app.config[f'WEKO_ACCOUNTS_{key.upper()}']['defaultRole'] = new_roles[key]
                            flash(_(f'{key.replace("_", " ").title()} was updated.'), category='success')

            return self.render(
                current_app.config['WEKO_ACCOUNTS_SET_SHIB_TEMPLATE'],
                shib_flg=shib_flg, set_language=set_language, role_list=role_list, attr_list=attr_list, block_user_list=block_user_list, **roles, **attributes )
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
