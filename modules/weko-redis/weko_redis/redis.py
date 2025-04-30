# -*- coding: utf-8 -*-

import redis
from redis import sentinel
from flask import current_app
from simplekv.memory.redisstore import RedisStore

class RedisConnection:
    """
    Redis Connection for app.

    This class provides methods to establish connections with Redis servers based on the configuration of the Flask app.

    Attributes:
        redis_type (str): The type of Redis connection (e.g., 'redis' or 'redissentinel').

    Methods:
        connection(db, kv=False): Establishes a Redis connection and returns the datastore object.
        redis_connection(db): Establishes a direct Redis connection and returns the Redis store object.
        sentinel_connection(db): Establishes a Redis Sentinel connection and returns the Redis store object.
    """
    def __init__(self):
        self.redis_type = current_app.config['CACHE_TYPE']
        self.socket_timeout = current_app.config.get('REDIS_SOCKET_TIMEOUT',0.1)

    def connection(self, db, kv = False):
        """
        Establishes a Redis connection and returns the datastore object.

        Args:
            db (int): The Redis database index to connect to.
            kv (bool, optional): Specifies whether to wrap the Redis store with a RedisStore object. Default is False.

        Returns:
            object: The Redis datastore object.
        """
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
        """
        Establishes a direct Redis connection and returns the Redis store object.

        Args:
            db (int): The Redis database index to connect to.

        Returns:
            object: The Redis store object.
        """
        store = None
        try:
            redis_url = 'redis://' + current_app.config['CACHE_REDIS_HOST'] + ':' + current_app.config['REDIS_PORT'] + '/' + str(db)
            store = redis.StrictRedis.from_url(redis_url)
        except Exception as ex:
            raise ex

        return store

    def sentinel_connection(self, db):
        """
        Establishes a Redis Sentinel connection and returns the Redis store object.

        Args:
            db (int): The Redis database index to connect to.

        Returns:
            object: The Redis store object.
        """
        store = None
        try:
            sentinels = sentinel.Sentinel(current_app.config['CACHE_REDIS_SENTINELS'], decode_responses=False, socket_timeout=self.socket_timeout)
            store = sentinels.master_for(
                current_app.config['CACHE_REDIS_SENTINEL_MASTER'], db= db)
        except Exception as ex:
            raise ex
            
        return store

class RedisConnectionExtension:
    """
    Redis Connection for ext.py.

    This class provides methods to establish connections with Redis servers for an extension module.

    Methods:
        redis_connection(host, port, db, kv=False): Establishes a direct Redis connection and returns the datastore object.
        sentinel_connection(host, mymaster, db, kv=False): Establishes a Redis Sentinel connection and returns the datastore object.
    """
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
        """
        Establishes a direct Redis connection and returns the datastore object.

        Args:
            host (str): The Redis server hostname or IP address.
            port (int): The Redis server port number.
            db (int): The Redis database index to connect to.
            kv (bool, optional): Specifies whether to wrap the Redis store with a RedisStore object. Default is False.

        Returns:
            object: The Redis datastore object.
        """
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