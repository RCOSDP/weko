
import pytest
from flask import Flask,current_app

from invenio_cache import InvenioCache, current_cache

from weko_sitemap import WekoSitemap


# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_create_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_create_page(create_app,mocker):
    mock_cache = mocker.patch("weko_sitemap.ext.WekoSitemap.set_cache_page")
    mocker.patch("weko_sitemap.ext.format_datetime",return_value="2022-10-01T01:02:03")
    app = create_app()

    with app.app_context():
        url_set = ["http://test1.com","http://test2.com"]
        current_app.extensions["weko-sitemap"].create_page(1,url_set)

        args,kwargs = mock_cache.call_args
        assert args[0] == "sitemap_0001"
        assert args[1]["lastmod"] == "2022-10-01T01:02:03"
# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_load_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_load_page(create_app,mocker):
    app = create_app(CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis")
    InvenioCache(app)
    with app.app_context():
        current_cache.set("sitemap_0001",{"page":"exist_test_page"})
        
        result = current_app.extensions["weko-sitemap"].load_page(lambda page:page)(page="test_page")
        assert result == "test_page"
        result = current_app.extensions["weko-sitemap"].load_page(lambda page:page)(page="1")
        assert result == "exist_test_page"
# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_clear_cache_pages -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_clear_cache_pages(create_app):
    app = create_app(CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis")
    InvenioCache(app)
    with app.app_context():
        current_cache.set("sitemap_page_keys",["key1","key2"])
        current_cache.set("key1","value1")
        current_cache.set("key2","value2")
        current_cache.set("key3","value3")
        
        current_app.extensions["weko-sitemap"].clear_cache_pages()
        assert current_cache.get("sitemap_page_keys") == None
        assert current_cache.get("key1") == None
        assert current_cache.get("key2") == None
        assert current_cache.get("key3") == "value3"
# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_set_cache_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp

def test_set_cache_page(create_app):
    app = create_app(CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis")
    InvenioCache(app)
    with app.app_context():
        current_cache.set("sitemap_page_keys",{"key1","key2"})
        current_cache.set("key1","value1")
        current_cache.set("key2","value2")
        current_app.extensions["weko-sitemap"].set_cache_page("key_x","value_x")
        
        assert current_cache.get("sitemap_page_keys")=={"key1","key2","key_x"}
        assert current_cache.get("key1") == "value1"
        assert current_cache.get("key_x") == "value_x"

def test_get_cache_page(create_app):
    app = create_app(CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis")
    InvenioCache(app)
    with app.app_context():
        current_cache.set("sitemap_page_keys",{"key1","key2"})
        result = current_app.extensions["weko-sitemap"].get_cache_page("sitemap_page_keys")
        assert result == {"key1","key2"}