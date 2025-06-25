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
from weko_accounts.models import ShibbolethUser, db

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)

class ShibSettingView(BaseView):
    """ShibSettingView."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Index."""
        try:
            # Shibbolethログイン可否
            shib_login_enable = AdminSettings.get('shib_login_enable', dict_to_object=False)
            shib_flg = '0' if not shib_login_enable.get('shib_flg', current_app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED']) else '1'

            role_list = current_app.config['WEKO_ACCOUNTS_ROLE_LIST']
            attr_list = current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_LIST']
            set_language = _('language')

            shib_eppns = db.session.query(ShibbolethUser.shib_eppn).all()
            enable_login_user_list = [shib_eppn[0] for shib_eppn in shib_eppns]

            # デフォルトロール
            default_roles = AdminSettings.get('default_role_settings', dict_to_object=False)
            roles = {
                'gakunin_role': default_roles.get('gakunin_role', current_app.config['WEKO_ACCOUNTS_GAKUNIN_ROLE']['defaultRole']),
                'orthros_outside_role': default_roles.get('orthros_outside_role', current_app.config['WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE']['defaultRole']),
                'extra_role': default_roles.get('extra_role', current_app.config['WEKO_ACCOUNTS_EXTRA_ROLE']['defaultRole'])
            }

            # 属性マッピング
            attribute_mappings = AdminSettings.get('attribute_mapping', dict_to_object=False)
            attributes = {
                'shib_eppn': attribute_mappings.get('shib_eppn', current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']['shib_eppn']),
                'shib_role_authority_name': attribute_mappings.get('shib_role_authority_name', current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']['shib_role_authority_name']),
                'shib_mail': attribute_mappings.get('shib_mail', current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']['shib_mail']),
                'shib_user_name': attribute_mappings.get('shib_user_name', current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']['shib_user_name'])
            }

            # ブロックユーザー
            block_user_settings = AdminSettings.get('blocked_user_settings', dict_to_object=False)
            block_user_list = block_user_settings.get('blocked_ePPNs', [])

            if request.method == 'POST':
                # Process forms
                form = request.form.get('submit', None)
                new_shib_flg = request.form.get('shibbolethRadios', '0')
                new_roles = {key: request.form.get(f'role-lists{i}', []) for i, key in enumerate(roles)}
                new_attributes = {key: request.form.get(f'attr-lists{i}', []) for i, key in enumerate(attributes)}
                new_block_user_list = request.form.get('block-eppn-option-list', "[]")

                if form == 'shib_form':
                    is_edit = False
                    if shib_flg != new_shib_flg:
                        shib_flg = new_shib_flg
                        AdminSettings.update('shib_login_enable', {"shib_flg": (shib_flg == '1')})
                        flash(_('Shibboleth flag was updated.'), category='success')
                        is_edit = True

                    # デフォルトロールの更新
                    for key in roles:
                        if roles[key] != new_roles[key]:
                            roles[key] = new_roles[key]
                            flash(_(f'{key.replace("_", " ").title()} was updated.'), category='success')
                            is_edit = True
                        AdminSettings.update('default_role_settings', roles)

                    # 属性マッピングの更新
                    for key in attributes:
                        if attributes[key] != new_attributes[key]:
                            attributes[key] = new_attributes[key]
                            flash(_(f'{key.replace("_", " ").title()} mapping was updated.'), category='success')
                            is_edit = True
                        AdminSettings.update('attribute_mapping', attributes)

                    # ブロックユーザーの更新
                    if block_user_list != json.loads(new_block_user_list):
                        new_eppn_list = json.loads(new_block_user_list)
                        new_eppn_list.sort()
                        updateSettings = {'blocked_ePPNs': new_eppn_list}
                        AdminSettings.update('blocked_user_settings', updateSettings)
                        flash(
                            _('Blocked user list was updated.'),
                            category='success')
                        is_edit = True
                        block_user_list = str(new_eppn_list).replace('"', '\\"')
                    
                    if not is_edit:
                        flash(_('Shibboleth settings have been saved'), category='success')

            self.get_latest_current_app()

            return self.render(
                current_app.config['WEKO_ACCOUNTS_SET_SHIB_TEMPLATE'],
                shib_flg=shib_flg, set_language=set_language, role_list=role_list, attr_list=attr_list, block_user_list=block_user_list, enable_login_user_list=enable_login_user_list, **roles, **attributes )
        except BaseException:
            current_app.logger.error(
                'Unexpected error: {}'.format(sys.exc_info()))
        return abort(400)

    def get_latest_current_app(self):
        _app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED'] = AdminSettings.get('shib_login_enable', dict_to_object=False)['shib_flg']
        default_roles = AdminSettings.get('default_role_settings', dict_to_object=False)
        _app.config['WEKO_ACCOUNTS_GAKUNIN_ROLE']['defaultRole'] = default_roles['gakunin_role']
        _app.config['WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE']['defaultRole'] = default_roles['orthros_outside_role']
        _app.config['WEKO_ACCOUNTS_EXTRA_ROLE']['defaultRole'] = default_roles['extra_role']
        _app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP'] = AdminSettings.get('attribute_mapping', dict_to_object=False)

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
