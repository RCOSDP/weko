import redis
from redis import sentinel
from flask import current_app
from simplekv.memory.redisstore import RedisStore

class RedisConnection:
    def __init__(self):
        self.redis_type = current_app.config['CACHE_TYPE']


    def connection(self, db):
        datastore = None
        if self.redis_type == 'redis':
            datastore = self.redis_connection(db)
        elif self.redis_type == 'redissentinel':
            datastore = self.sentinel_connection(db)

        return datastore

    def redis_connection(self, db):
        redis_url = current_app.config['CACHE_REDIS_HOST'] + ':' + current_app.config['REDIS_PORT'] + '/' + str(db)
        datastore = RedisStore(redis.StrictRedis.from_url(redis_url))

        return datastore

    def sentinel_connection(self, db):
        sentinels = sentinel.Sentinel(current_app.config['CACHE_REDIS_SENTINELS'], decode_responses=False)
        datastore = RedisStore(sentinels.master_for(
            current_app.config['CACHE_REDIS_SENTINEL_MASTER'], db= db))

        return datastore