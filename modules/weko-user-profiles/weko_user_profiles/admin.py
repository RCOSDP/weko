# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
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

"""Admin views for weko-user-profiles."""

from flask_admin.contrib.sqla import ModelView
from wtforms import SelectField

from .config import USERPROFILES_LANGUAGE_LIST, USERPROFILES_TIMEZONE_LIST
from .models import UserProfile


def _(x):
    """Identity."""
    return x


class UserProfileView(ModelView):
    """Userprofiles view. Link User ID to user/full/display name."""

    can_view_details = True
    can_create = False
    can_delete = True

    column_list = (
        'user_id',
        '_displayname',
        # 'full_name',
        'timezone',
        'language',
    )

    column_searchable_list = \
        column_filters = \
        column_details_list = \
        columns_sortable_list = \
        column_list

    form_columns = (
        'username',
        # 'full_name',
        'timezone',
        'language')

    column_labels = {
        '_displayname': _('Username'),
        'timezone': _('Timezone'),
        'language': _('Language'),
    }

    column_choices = {
        'timezone': USERPROFILES_TIMEZONE_LIST,
        'language': USERPROFILES_LANGUAGE_LIST
    }

    form_args = dict(
        timezone=dict(
            choices=USERPROFILES_TIMEZONE_LIST,
        ),
        language=dict(
            choices=USERPROFILES_LANGUAGE_LIST
        )
    )
    form_overrides = dict(
        timezone=SelectField,
        language=SelectField
    )


user_profile_adminview = {
    'model': UserProfile,
    'modelview': UserProfileView,
    'category': _('User Management'),
}
