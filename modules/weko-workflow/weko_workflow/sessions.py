# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""WEKO3 module docstring."""

import os

import redis
from flask import current_app, session
from simplekv.memory.redisstore import RedisStore

from .api import WorkActivity


def upt_activity_item(app, user_id, item_id, item_title):
    """Connect to the item_created signal.

    :param app:
    :param user_id:
    :param item_id:
    :param item_title
    :return:
    """
    if 'activity_info' in session:
        activity = session['activity_info']
        workactivity = WorkActivity()
        rtn = workactivity.upt_activity_item(
            activity, item_id.object_uuid)
        if rtn:
            del session['activity_info']
            sessionstore = RedisStore(redis.StrictRedis.from_url(
                'redis://{host}:{port}/1'.format(
                    host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
                    port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
            activity_id = activity.get('activity_id', None)
            if activity_id and sessionstore.redis.exists(
                    'activity_item_' + activity_id):
                sessionstore.delete('activity_item_' + activity_id)
