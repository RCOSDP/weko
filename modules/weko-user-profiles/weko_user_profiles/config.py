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
    ('Etc/GMT+12', _('(GMT-12:00) Eniwetok, Kwajalein')),
    ('Etc/GMT+11', _('(GMT-11:00) Midway Island, Samoa')),
    ('Etc/GMT+10', _('(GMT-10:00) Hawaii')),
    ('Etc/GMT+9', _('(GMT-9:00) Alaska')),
    ('Etc/GMT+8', _('(GMT-8:00) Pacific Time (US & Canada)')),
    ('Etc/GMT+7', _('(GMT-7:00) Mountain Time (US & Canada)')),
    ('Etc/GMT+6', _('(GMT-6:00) Central Time (US & Canada), Mexico City')),
    ('Etc/GMT+5', _('(GMT-5:00) Eastern Time (US & Canada), Bogota, Lima, Quito')),
    ('Etc/GMT+4', _('(GMT-4:00) Atlantic Time (Canada), Caracas, La Paz')),
    ('Canada/Newfoundland', _('(GMT-3:30) Newfoundland')),
    ('Etc/GMT+3', _('(GMT-3:00) Brasilia, Buenos Aires, Georgetown')),
    ('Etc/GMT+2', _('(GMT-2:00) Mid-Atlantic')),
    ('Etc/GMT+1', _('(GMT-1:00) Azores, Cape Verde Islands')),
    ('Etc/GMT', _('(GMT) Greenwich Mean Time, London, Dublin, Lisbon,'
                  ' Casablanca, Monrovia')),
    ('Etc/GMT-1', _('(GMT+1:00) Amsterdam, Berlin, Rome, Copenhagen,'
                    ' Brussels, Madrid, Paris')),
    ('Etc/GMT-2', _('(GMT+2:00) Athens, Istanbul, Minsk, Helsinki,'
                    ' Jerusalem, South Africa')),
    ('Etc/GMT-3', _('(GMT+3:00) Baghdad, Kuwait, Riyadh, Moscow, St. Petersburg')),
    ('Asia/Tehran', _('(GMT+3:30) Tehran')),
    ('Etc/GMT-4', _('(GMT+4:00) Abu Dhabi, Muscat, Baku, Tbilisi')),
    ('Asia/Kabul', _('(GMT+4:30) Kabul')),
    ('Etc/GMT-5', _('(GMT+5:00) Ekaterinburg, Islamabad, Karachi, Tashkent')),
    ('Asia/Calcutta', _('(GMT+5:30) Bombay, Calcutta, Madras, New Delhi')),
    ('Etc/GMT-6', _('(GMT+6:00) Almaty, Dhaka, Colombo')),
    ('Etc/GMT-7', _('(GMT+7:00) Bangkok, Hanoi, Jakarta')),
    ('Etc/GMT-8', _('(GMT+8:00) Beijing, Perth, Singapore, Hong Kong,'
                    ' Urumqi, Taipei')),
    ('Etc/GMT-9', _('(GMT+9:00) Tokyo, Seoul, Osaka, Sapporo, Yakutsk')),
    ('Australia/Adelaide', _('(GMT+9:30) Adelaide, Darwin')),
    ('Etc/GMT-10', _('(GMT+10:00) Brisbane, Canberra, Melbourne, Sydney,'
                     'Guam, Vlasdiostok')),
    ('Etc/GMT-11', _('(GMT+11:00) Magadan, Solomon Islands, New Caledonia')),
    ('Etc/GMT-12', _('(GMT+12:00) Auckland, Wellington, Fiji, Kamchatka,'
                     'Marshall Island'))
]
"""Settings timezone list for user profile module."""

USERPROFILES_TIMEZONE_DEFAULT = 'Etc/GMT-9'
"""Settings default value of timezone for user profile module."""

USERPROFILES_LANGUAGE_LIST = [('', _('Automatic')),
                              ('ja', _('Japanese')),
                              ('en', _('English'))]
"""Settings language list for user profile module."""

USERPROFILES_LANGUAGE_DEFAULT = 'ja'
"""Settings default value of language for user profile module."""

WEKO_USERPROFILES_OTHERS_INPUT_DETAIL = "Others (Input Detail)"
"""Other input detail"""

WEKO_USERPROFILES_POSITION_LIST_GENERAL = [
    ('', ''),
    ('Professor', _('Professor')),
    ('Assistant Professor', _('Assistant Professor')),
    ('Full-time Instructor', _('Full-time Instructor')),
    ('Assistant Teacher', _('Assistant Teacher')),
    ('Full-time Researcher', _('Full-time Researcher')),
    (WEKO_USERPROFILES_OTHERS_INPUT_DETAIL, _('Others (Input Detail)')),
    ('JSPS Research Fellowship for Young Scientists (PD, SPD etc.)',
        _('JSPS Research Fellowship for Young Scientists (PD, SPD etc.)'))
]
"""General Position list"""

WEKO_USERPROFILES_POSITION_LIST_GRADUATED_STUDENT = [
    ('JSPS Research Fellowship for Young Scientists (DC1, DC2)',
     _('JSPS Research Fellowship for Young Scientists (DC1, DC2)')),
    ('Doctoral Course (Doctoral Program)',
     _('Doctoral Course (Doctoral Program)')),
    ('Master Course (Master Program)', _('Master Course (Master Program)')),
    ('Fellow Researcher', _('Fellow Researcher')),
    ('Listener', _('Listener'))
]
"""Graduated Student Position list"""

WEKO_USERPROFILES_POSITION_LIST_STUDENT = [('Student', _('Student'))]
"""Student Position list"""

WEKO_USERPROFILES_POSITION_LIST = \
    WEKO_USERPROFILES_POSITION_LIST_GENERAL + \
    WEKO_USERPROFILES_POSITION_LIST_GRADUATED_STUDENT + \
    WEKO_USERPROFILES_POSITION_LIST_STUDENT
"""Position list"""

WEKO_USERPROFILES_INSTITUTE_POSITION_LIST = [
    ('', ''),
    ('Member', _('Member')),
    ('Committee member', _('Committee member')),
    ('Director/Officer', _('Director/Officer')),
    ('President', _('President'))
]
"""Institute Position list"""

WEKO_USERPROFILES_ADMINISTRATOR_ROLE = 'Administrator'
"""Administrator Role"""

WEKO_USERPROFILES_GENERAL_ROLE = 'General'
"""General Role"""

WEKO_USERPROFILES_GRADUATED_STUDENT_ROLE = 'Graduated Student'
"""Graduated Student Role"""

WEKO_USERPROFILES_STUDENT_ROLE = 'Student'
"""Student Role"""

WEKO_USERPROFILES_ROLE_MAPPING_ENABLED = False
"""Enable role mapping"""

WEKO_USERPROFILES_ROLES = [
    WEKO_USERPROFILES_ADMINISTRATOR_ROLE,
    WEKO_USERPROFILES_GENERAL_ROLE,
    WEKO_USERPROFILES_GRADUATED_STUDENT_ROLE,
    WEKO_USERPROFILES_STUDENT_ROLE
]
"""Roles"""

WEKO_USERPROFILES_ROLE_MAPPING = {}
"""Role mapping"""

WEKO_USERPROFILES_FORM_COLUMN = ["username", "timezone", "language", "email",
                                 "email_repeat", "access_key", "secret_key", "s3_endpoint_url", "s3_region_name"]
"""User profile form column"""

WEKO_USERPROFILES_READONLY_EMAILFIELD = False
