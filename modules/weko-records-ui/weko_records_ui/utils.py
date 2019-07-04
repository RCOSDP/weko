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

"""Module of weko-records-ui utils."""

from invenio_db import db
from weko_records.api import ItemsMetadata
from weko_workflow.models import ActionStatusPolicy, Activity
from flask import current_app

import redis
from simplekv.memory.redisstore import RedisStore

def check_email_display_setting():
    datastore = RedisStore(redis.StrictRedis.from_url(
        current_app.config['CACHE_REDIS_URL']))
    cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
        format(name='email_display')
    if not datastore.redis.exists(cache_key):
        datastore.put(cache_key,
                      str(current_app.config['EMAIL_DISPLAY_FLG']).encode('utf-8'))
    current_app.config['EMAIL_DISPLAY_FLG'] = eval(datastore.get(cache_key))


def get_item_pidstore_identifier(object_uuid):
    """
    Get identifier value from ItemsMetadata.

    :param: index_name_english
    :return: dict of item type info
    """
    with db.session.no_autoflush:
        action_status = Activity.query.filter_by(
            item_id=object_uuid).one_or_none()
        meta = ItemsMetadata.get_record(object_uuid)
        if meta and action_status:
            pidstore_identifier = meta.get('pidstore_identifier')
            if pidstore_identifier is not None \
                and action_status.action_status == \
                    ActionStatusPolicy.ACTION_DONE:
                identifier = pidstore_identifier.get('identifier')
                if identifier:
                    return identifier.get('value')

    return None
