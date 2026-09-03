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

"""Tests for weko_redis.redis."""

import pytest
import redis as redis_lib
from mock import patch
from simplekv.memory.redisstore import RedisStore

from weko_redis.redis import RedisConnection, RedisConnectionExtension


# .tox/c1/bin/pytest --cov=weko_redis tests/test_redis.py::test_init -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-redis/.tox/c1/tmp
def test_init(app):
    """The connection type is taken from CACHE_TYPE."""
    assert RedisConnection().redis_type == "redis"

    app.config["CACHE_TYPE"] = "redissentinel"
    assert RedisConnection().redis_type == "redissentinel"


# .tox/c1/bin/pytest --cov=weko_redis tests/test_redis.py::test_redis_connection -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-redis/.tox/c1/tmp
def test_redis_connection(app):
    """A direct connection is built from host, port and db."""
    store = RedisConnection().redis_connection(1)

    assert isinstance(store, redis_lib.StrictRedis)
    kwargs = store.connection_pool.connection_kwargs
    assert kwargs["host"] == app.config["CACHE_REDIS_HOST"]
    assert kwargs["port"] == int(app.config["REDIS_PORT"])
    assert kwargs["db"] == 1

    # The service is up in the test environment, so the store is usable.
    assert store.ping() is True


# .tox/c1/bin/pytest --cov=weko_redis tests/test_redis.py::test_redis_connection_error -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-redis/.tox/c1/tmp
def test_redis_connection_error(app):
    """A failure to build the connection is re-raised, not swallowed."""
    with patch("weko_redis.redis.redis.StrictRedis.from_url",
               side_effect=ValueError("boom")):
        with pytest.raises(ValueError):
            RedisConnection().redis_connection(0)


# .tox/c1/bin/pytest --cov=weko_redis tests/test_redis.py::test_sentinel_connection -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-redis/.tox/c1/tmp
def test_sentinel_connection(app):
    """The sentinel connection asks for the configured master."""
    with patch("weko_redis.redis.sentinel.Sentinel") as mock_sentinel:
        store = RedisConnection().sentinel_connection(2)

    mock_sentinel.assert_called_once_with(
        app.config["CACHE_REDIS_SENTINELS"], decode_responses=False)
    mock_sentinel.return_value.master_for.assert_called_once_with(
        app.config["CACHE_REDIS_SENTINEL_MASTER"], db=2)
    assert store is mock_sentinel.return_value.master_for.return_value


# .tox/c1/bin/pytest --cov=weko_redis tests/test_redis.py::test_connection -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-redis/.tox/c1/tmp
def test_connection(app):
    """connection() picks the store by CACHE_TYPE and wraps it when kv."""
    store = RedisConnection().connection(0)
    assert isinstance(store, redis_lib.StrictRedis)

    datastore = RedisConnection().connection(0, kv=True)
    assert isinstance(datastore, RedisStore)

    app.config["CACHE_TYPE"] = "redissentinel"
    with patch("weko_redis.redis.sentinel.Sentinel") as mock_sentinel:
        datastore = RedisConnection().connection(0, kv=True)
    assert isinstance(datastore, RedisStore)
    assert datastore.redis is mock_sentinel.return_value.master_for.return_value


# .tox/c1/bin/pytest --cov=weko_redis tests/test_redis.py::test_connection_unknown_type -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-redis/.tox/c1/tmp
def test_connection_unknown_type(app):
    """An unknown CACHE_TYPE leaves nothing to wrap."""
    app.config["CACHE_TYPE"] = "simple"

    # No branch matches, so `store` is never assigned and the reference below
    # the try raises, whether or not the store is wrapped.
    with pytest.raises(UnboundLocalError):
        RedisConnection().connection(0)
    with pytest.raises(UnboundLocalError):
        RedisConnection().connection(0, kv=True)


# .tox/c1/bin/pytest --cov=weko_redis tests/test_redis.py::test_extension_redis_connection -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-redis/.tox/c1/tmp
def test_extension_redis_connection(app):
    """The ext variant takes host and port as arguments."""
    host = app.config["CACHE_REDIS_HOST"]
    port = app.config["REDIS_PORT"]

    store = RedisConnectionExtension().redis_connection(host, port, 1)
    assert isinstance(store, redis_lib.StrictRedis)
    assert store.connection_pool.connection_kwargs["db"] == 1
    assert store.ping() is True

    datastore = RedisConnectionExtension().redis_connection(host, port, 1, kv=True)
    assert isinstance(datastore, RedisStore)

    with patch("weko_redis.redis.redis.StrictRedis.from_url",
               side_effect=ValueError("boom")):
        with pytest.raises(ValueError):
            RedisConnectionExtension().redis_connection(host, port, 1)


# .tox/c1/bin/pytest --cov=weko_redis tests/test_redis.py::test_extension_sentinel_connection -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-redis/.tox/c1/tmp
def test_extension_sentinel_connection(app):
    """The ext variant takes the sentinel list and master name as arguments."""
    hosts = [("sentinel", 26379)]

    with patch("weko_redis.redis.sentinel.Sentinel") as mock_sentinel:
        store = RedisConnectionExtension().sentinel_connection(
            hosts, "mymaster", 3)
        datastore = RedisConnectionExtension().sentinel_connection(
            hosts, "mymaster", 3, kv=True)

    mock_sentinel.assert_called_with(hosts, decode_responses=False)
    mock_sentinel.return_value.master_for.assert_called_with("mymaster", db=3)
    assert store is mock_sentinel.return_value.master_for.return_value
    assert isinstance(datastore, RedisStore)

    with patch("weko_redis.redis.sentinel.Sentinel",
               side_effect=ValueError("boom")):
        with pytest.raises(ValueError):
            RedisConnectionExtension().sentinel_connection(hosts, "mymaster", 3)
