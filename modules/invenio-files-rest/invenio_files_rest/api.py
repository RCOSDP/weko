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

"""API for invenio files rest."""

from flask import current_app, render_template
from flask_babel import gettext as _
from invenio_mail.api import send_mail
from weko_accounts.api import get_user_info_by_role_name
from weko_admin.models import AdminLangSettings

from .models import Location


def send_alert_mail(threshold_rate, name, use_rate, used_size, use_limit):
    """Send storage use rate alert mail."""
    try:
        # mail title
        subject = '[{0}] '.format(current_app.config['THEME_SITENAME']) + \
            _('Storage usage report')
        # recipient mail list
        users = []
        users += get_user_info_by_role_name('Repository Administrator')
        mail_list = []
        for user in users:
            mail_list.append(user.email)

        current_app.logger.debug('mail_list:{0}'.format(mail_list))
        with current_app.test_request_context() as ctx:
            default_lang = AdminLangSettings.get_registered_language()[0]
            # setting locale
            setattr(ctx, 'babel_locale', default_lang['lang_code'])
            # send alert mail
            send_mail(subject, mail_list,
                      html=render_template('admin/alert_mail.html',
                                           location_name=name,
                                           use_rate=use_rate,
                                           used_size=used_size,
                                           use_limit=use_limit,
                                           lang_code=default_lang['lang_code']))
    except Exception as ex:
        current_app.logger.error(ex)
