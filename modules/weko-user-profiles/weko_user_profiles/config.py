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

"""Configuration for weko-user-profiles."""

from flask_babelex import lazy_gettext as _

USERPROFILES = True
"""Enable or disable module extensions."""

USERPROFILES_EMAIL_ENABLED = True
"""Include the user email in the profile form."""

USERPROFILES_EXTEND_SECURITY_FORMS = False
"""Extend the Invenio-Accounts user registration forms."""

USERPROFILES_PROFILE_TEMPLATE = 'weko_user_profiles/settings/profile.html'
"""Default profile template."""

USERPROFILES_PROFILE_URL = '/account/settings/profile/'
"""Default profile URL endpoint."""

USERPROFILES_BASE_TEMPLATE = None
"""Base templates for user profile module."""

USERPROFILES_SETTINGS_TEMPLATE = None
"""Settings base templates for user profile module."""

USERPROFILES_TIMEZONE_LIST = [
    ('-12:00', _('(GMT-12:00) Eniwetok, Kwajalein')),
    ('-11:00', _('(GMT-11:00) Midway Island, Samoa')),
    ('-10:00', _('(GMT-10:00) Hawaii')),
    ('-09:00', _('(GMT-9:00) Alaska')),
    ('-08:00', _('(GMT-8:00) Pacific Time (US & Canada)')),
    ('-07:00', _('(GMT-7:00) Mountain Time (US & Canada)')),
    ('-06:00', _('(GMT-6:00) Central Time (US & Canada), Mexico City')),
    ('-05:00', _('(GMT-5:00) Eastern Time (US & Canada), Bogota, Lima, Quito')),
    ('-04:00', _('(GMT-4:00) Atlantic Time (Canada), Caracas, La Paz')),
    ('-03:30', _('(GMT-3:30) Newfoundland')),
    ('-03:00', _('(GMT-3:00) Brasilia, Buenos Aires, Georgetown')),
    ('-02:00', _('(GMT-2:00) Mid-Atlantic')),
    ('-01:00', _('(GMT-1:00) Azores, Cape Verde Islands')),
    ('00:00', _('(GMT) Greenwich Mean Time, London, Dublin, Lisbon,'
                ' Casablanca, Monrovia')),
    ('+01:00', _('(GMT+1:00) Amsterdam, Berlin, Rome, Copenhagen,'
                 ' Brussels, Madrid, Paris')),
    ('+02:00', _('(GMT+2:00) Athens, Istanbul, Minsk, Helsinki,'
                 ' Jerusalem, South Africa')),
    ('+03:00', _('(GMT+3:00) Baghdad, Kuwait, Riyadh, Moscow, St. Petersburg')),
    ('+03:30', _('(GMT+3:30) Tehran')),
    ('+04:00', _('(GMT+4:00) Abu Dhabi, Muscat, Baku, Tbilisi')),
    ('+04:30', _('(GMT+4:30) Kabul')),
    ('+05:00', _('(GMT+5:00) Ekaterinburg, Islamabad, Karachi, Tashkent')),
    ('+05:30', _('(GMT+5:30) Bombay, Calcutta, Madras, New Delhi')),
    ('+06:00', _('(GMT+6:00) Almaty, Dhaka, Colombo')),
    ('+07:00', _('(GMT+7:00) Bangkok, Hanoi, Jakarta')),
    ('+08:00', _('(GMT+8:00) Beijing, Perth, Singapore, Hong Kong,'
                 ' Urumqi, Taipei')),
    ('+09:00', _('(GMT+9:00) Tokyo, Seoul, Osaka, Sapporo, Yakutsk')),
    ('+09:30', _('(GMT+9:30) Adelaide, Darwin')),
    ('+10:00', _('(GMT+10:00) Brisbane, Canberra, Melbourne, Sydney,'
                 'Guam, Vlasdiostok')),
    ('+11:00', _('(GMT+11:00) Magadan, Solomon Islands, New Caledonia')),
    ('+12:00', _('(GMT+12:00) Auckland, Wellington, Fiji, Kamchatka,'
                 'Marshall Island'))
]
"""Settings timezone list for user profile module."""

USERPROFILES_TIMEZONE_DEFAULT = '+09:00'
"""Settings default value of timezone for user profile module."""

USERPROFILES_LANGUAGE_LIST = [('', _('Automatic')),
                              ('ja', _('Japanese')),
                              ('en', _('English'))]
"""Settings language list for user profile module."""

USERPROFILES_LANGUAGE_DEFAULT = 'ja'
"""Settings default value of language for user profile module."""
