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

"""Blueprint for weko-deposit."""

from flask import Blueprint, render_template, json, jsonify, request, \
    current_app, abort
from flask_babelex import gettext as _
import redis
from simplekv.memory.redisstore import RedisStore

blueprint = Blueprint(
    'weko_deposit',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/deposits/items/index/<string:pid>", methods=['PUT', 'POST'])
def wokao(pid):
    """Render a basic view."""
    data = request.get_json()

    try:
        # item metadata cached on Redis by pid
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        cache_key = current_app.config[
            'WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(pid_value=pid)
        ttl_sec = int(current_app.config['WEKO_DEPOSIT_ITEMS_CACHE_TTL'])
        datastore.put(cache_key, json.dumps(data), ttl_secs=ttl_sec)
    except:
        abort(400, "Failed to register item")

    return jsonify({'status': 'success'})
