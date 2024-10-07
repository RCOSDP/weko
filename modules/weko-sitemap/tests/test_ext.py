
import pytest
from mock import patch
from datetime import datetime
from flask import current_app,make_response, url_for
from flask_babel import format_datetime

from invenio_cache import InvenioCache, current_cache

from weko_sitemap import WekoSitemap


# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_create_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_create_page(create_app):
    mock_cache = patch("weko_sitemap.ext.WekoSitemap.set_cache_page")
    patch("weko_sitemap.ext.format_datetime",return_value="2022-10-01T01:02:03")
    app = create_app()

    with app.app_context():
        url_set = ["http://test1.com","http://test2.com"]
        current_app.extensions["weko-sitemap"].create_page(1,url_set)

        args,kwargs = mock_cache.call_args
        assert args[0] == "sitemap_0001"
        assert args[1]["lastmod"] == "2022-10-01T01:02:03"

# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_load_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_load_page(create_app):
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

# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_get_cache_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_get_cache_page(create_app):
    app = create_app(CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis")
    InvenioCache(app)
    with app.app_context():
        current_cache.set("sitemap_page_keys",{"key1","key2"})
        current_app.extensions["weko-sitemap"].get_cache_page("sitemap_page_keys")

# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_sitemap -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_sitemap(create_app):
    app = create_app(CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis")
    def mock_load():
        data = [
            {"loc":"https://localhost/weko/sitemaps/sitemap_1.xml.gz","lastmod":"2023-01-12T10:01:02+0000"},
            {"loc":"https://localhost/weko/sitemaps/sitemap_2.xml.gz","lastmod":"2023-01-21T10:01:02+0000"}
        ]
        for d in data:
            yield d
    patch("weko_sitemap.ext.WekoSitemap._load_cache_pages",side_effect=mock_load)
    with app.app_context():
        mock_render = patch("weko_sitemap.ext.render_template", return_value=make_response())
        res = current_app.extensions["weko-sitemap"].sitemap()
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == "flask_sitemap/sitemapindex.xml"

# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_page(create_app):
    app = create_app(CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis")
    InvenioCache(app)
    with app.app_context():
        current_cache.set("sitemap_0001",{"page":"test_data"})
        mock_zip = patch("weko_sitemap.ext.WekoSitemap.gzip_response",return_value=make_response())
        current_app.extensions["weko-sitemap"].page(1)
        mock_zip.assert_called_with("test_data")

        mock_page = patch("weko_sitemap.ext.WekoSitemap.render_page",return_value=make_response())
        current_app.extensions["weko-sitemap"].page(2)
        mock_page.assert_called_with(urlset=[None])


# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_gzip_response -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_gzip_response(create_app):
    test_data = "test_data"

    app = create_app(CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis")
    InvenioCache(app)
    with app.app_context():
        result = current_app.extensions["weko-sitemap"].gzip_response(test_data)
        assert result.headers["Content-Type"] == "application/x-gzip"

# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_generate_all_item_urls -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_generate_all_item_urls(app,records):
    with app.test_request_context():
        result = iter(current_app.extensions["weko-sitemap"]._generate_all_item_urls())
        for i,r in enumerate(result):
            if i==0:
                assert r["loc"] == "http://test_server/records/1"
            if i==1:
                assert r["loc"] == "http://test_server/records/2"

# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_load_cache_pages -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_load_cache_pages(create_app):
    app = create_app(CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis")
    InvenioCache(app)
    with app.app_context():
        with app.test_request_context():
            current_cache.set("sitemap_page_keys",["key1","key1000"])
            current_cache.set("key1",{"lastmod":format_datetime(datetime(2023,1,12,10,1,2,123),'yyyy-MM-ddTHH:mm:ssz','full')})
            current_cache.set("key2",{"lastmod":format_datetime(datetime(2023,1,21,10,1,2,123),'yyyy-MM-ddTHH:mm:ssz','full')})
            result = iter(current_app.extensions["weko-sitemap"]._load_cache_pages())
            for i,r in enumerate(result):
                if i==0:
                    assert r == {"loc": "https://localhost/weko/sitemaps/sitemap_1.xml.gz", "lastmod":"2023-01-12T10:01:02+0000"}
            current_cache.delete("sitemap_page_keys")
            current_cache.delete("key1")
            current_cache.delete("key2")

# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_ext.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_dbsession_clean(app,db, db_sessionlifetime):
    from weko_records.models import ItemTypeName
    url = url_for("flask_sitemap.sitemap")
    with app.test_request_context(url):
        itemtype_name1 = ItemTypeName(id=1,name="テスト1",has_site_license=True, is_active=True)
        db.session.add(itemtype_name1)
    assert ItemTypeName.query.filter_by(id=1).first().name == "テスト1"

    with patch("weko_sitemap.ext.db.session.commit", side_effect=Exception("test_error")):
        with app.test_request_context(url):
            itemtype_name1 = ItemTypeName(id=1,name="テスト1",has_site_license=True, is_active=True)
            db.session.add(itemtype_name1)
        assert ItemTypeName.query.filter_by(id=2).first() is None
    assert ItemTypeName.query.filter_by(id=1).first().name == "テスト1"

    current_cache.set("sitemap_page_keys",{"key1","key1000"})
    current_cache.set("key1",{"test":"value"})
    try:
        with app.test_client() as client:
            itemtype_name3 = ItemTypeName(id=3,name="テスト3",has_site_license=True, is_active=True)
            db.session.add(itemtype_name3)
            res = client.get(url)
    except Exception:
        assert ItemTypeName.query.filter_by(id=3).first() is None
