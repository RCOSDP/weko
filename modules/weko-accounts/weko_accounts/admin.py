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
            shib_flg = '0'
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

            if current_app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED']:
                shib_flg = '1'

            # デフォルトロール
            if current_app.config['WEKO_ACCOUNTS_GAKUNIN_ROLE']:
                gakunin_role = current_app.config['WEKO_ACCOUNTS_GAKUNIN_ROLE']['defaultRole']
            if current_app.config['WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE']:
                orthros_role = current_app.config['WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE']['defaultRole']
            if current_app.config['WEKO_ACCOUNTS_OTHERS_ROLE']:
                others_role = current_app.config['WEKO_ACCOUNTS_OTHERS_ROLE']['defaultRole']

            # 属性マッピング
            if current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']: 
                weko_eppn_value = current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']['shib_eppn']
                weko_role_authority_name_value = current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']['shib_role_authority_name']
                weko_mail_value = current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']['shib_mail']
                weko_user_name_value = current_app.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP']['shib_user_name']

            if request.method == 'POST':
                # Process forms
                form = request.form.get('submit', None)
                new_shib_flg = request.form.get('shibbolethRadios', '0')

                if form == 'shib_form':
                    if shib_flg != new_shib_flg:
                        shib_flg = new_shib_flg
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
                shib_flg=shib_flg, set_language=set_language, role_list=role_list, attr_list=attr_list, block_user_list=block_user_list, gakunin_role=gakunin_role, orthros_role=orthros_role, others_role=others_role, \
                weko_eppn_value=weko_eppn_value, weko_role_authority_name_value=weko_role_authority_name_value, \
                weko_mail_value=weko_mail_value, weko_user_name_value=weko_user_name_value, )
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
