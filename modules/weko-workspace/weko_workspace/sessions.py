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

import os

import redis
from flask import current_app, session
from simplekv.memory.redisstore import RedisStore

from .api import WorkActivity


def upt_activity_item(app, user_id, item_id, item_title, admin_action=None):
    """Connect to the item_created signal.

    :param app:
    :param user_id:
    :param item_id:
    :param item_title:
    :param action_action
    :return:
    """
    if 'activity_info' in session:
        activity = session['activity_info']
        workactivity = WorkActivity()
        rtn = workactivity.upt_activity_item(
            activity, item_id.object_uuid)
        if rtn:
            del session['activity_info']
