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

import redis
from redis import sentinel
from flask import current_app
from simplekv.memory.redisstore import RedisStore

class RedisConnection:
    "Redis Connection for app"
    def __init__(self):
        self.redis_type = current_app.config['CACHE_TYPE']


    def connection(self, db, kv = False):
        datastore = None
        try:
            if self.redis_type == 'redis':
                store = self.redis_connection(db)
            elif self.redis_type == 'redissentinel':
                store = self.sentinel_connection(db)
        except Exception as ex:
            raise ex

        if kv == True:
            datastore = RedisStore(store)
        else:
            datastore = store

        return datastore

    def redis_connection(self, db):
        store = None
        try:
            redis_url = 'redis://' + current_app.config['CACHE_REDIS_HOST'] + ':' + current_app.config['REDIS_PORT'] + '/' + str(db)
            store = redis.StrictRedis.from_url(redis_url)
        except Exception as ex:
            raise ex

        return store

    def sentinel_connection(self, db):
        store = None
        try:
            sentinels = sentinel.Sentinel(current_app.config['CACHE_REDIS_SENTINELS'], decode_responses=False)
            store = sentinels.master_for(
                current_app.config['CACHE_REDIS_SENTINEL_MASTER'], db= db)
        except Exception as ex:
            raise ex
            
        return store

class RedisConnectionExtension:
    "Redis Connection for ext.py"
    def redis_connection(self, host, port, db, kv = False):
        store = None
        try:
            redis_url = 'redis://' + host + ':' + str(port) + '/' + str(db)
            store = redis.StrictRedis.from_url(redis_url)
        except Exception as ex:
            raise ex

        if kv == True:
            datastore = RedisStore(store)
        else:
            datastore = store

        return datastore

    def sentinel_connection(self, host, mymaster, db, kv = False):
        store = None
        try:
            sentinels = sentinel.Sentinel(host, decode_responses=False)
            store = sentinels.master_for(
                mymaster, db= db)
        except Exception as ex:
            raise ex
            
        if kv == True:
            datastore = RedisStore(store)
        else:
            datastore = store

        return datastore