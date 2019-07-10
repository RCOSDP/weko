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

"""API for user profiles."""

from flask import g, current_app
from flask_security import current_user
from werkzeug.local import LocalProxy
import pytz

from .config import USERPROFILES_LANGUAGE_DEFAULT, \
    USERPROFILES_TIMEZONE_DEFAULT
from .models import AnonymousUserProfile, UserProfile


def _get_current_userprofile():
    """Get current user profile.

    .. note:: If the user is anonymous, then a
        :class:`invenio_userprofiles.models.AnonymousUserProfile` instance is
        returned.

    :returns: The :class:`invenio_userprofiles.models.UserProfile` instance.
    """
    if current_user.is_anonymous:
        return AnonymousUserProfile()

    profile = g.get(
        'userprofile',
        UserProfile.get_by_userid(current_user.get_id()))

    if profile is None:
        profile = UserProfile(user_id=int(current_user.get_id()),
                              timezone=USERPROFILES_TIMEZONE_DEFAULT,
                              language=USERPROFILES_LANGUAGE_DEFAULT)
        g.userprofile = profile
    return profile


current_userprofile = LocalProxy(lambda: _get_current_userprofile())
"""Proxy to the user profile of the currently login user."""


def localize_time(dtime):
    try:
        if current_userprofile:
            tz = pytz.timezone(current_userprofile.timezone)
            return pytz.utc.localize(dtime).astimezone(tz)
        elif 'BABEL_DEFAULT_TIMEZONE' in current_app.config:
            tz = pytz.timezone(current_app.config['BABEL_DEFAULT_TIMEZONE'])
            return pytz.utc.localize(dtime).astimezone(tz)
        else:
            return pytz.utc.localize(dtime)
    except:
        return pytz.utc.localize(dtime)


