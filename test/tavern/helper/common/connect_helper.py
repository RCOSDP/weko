import psycopg2
import redis

from helper.config import DATABASE, REDIS


def connect_db():
    """Connect to the PostgreSQL database.

    Returns:
        psycopg2.extensions.connection: Connection to the database.
    """
    conn = psycopg2.connect(
        dbname=DATABASE["dbname"],
        user=DATABASE["user"],
        password=DATABASE["password"],
        host=DATABASE["host"],
        port=DATABASE["port"],
    )
    return conn


def connect_redis(db=0):
    """Connect to the Redis server.

    Returns:
        redis.Redis: Connection to the Redis server.
    """
    r = redis.Redis(
        host=REDIS["host"],
        port=REDIS["port"],
        db=db,
    )
    return r
