import pytest
from flask import request, url_for
from re import L
from elasticsearch_dsl.query import Match, Range, Terms, Bool
from mock import patch, MagicMock
from werkzeug import ImmutableMultiDict
from werkzeug.datastructures import MultiDict, CombinedMultiDict

from invenio_search import RecordsSearch
from weko_admin.config import WEKO_ADMIN_MANAGEMENT_OPTIONS
from weko_search_ui.config import WEKO_SEARCH_KEYWORDS_DICT

from weko_search_ui.query import (
    get_item_type_aggs,
    get_permission_filter,
    default_search_factory,
    item_path_search_factory,
    check_admin_user,
    opensearch_factory,
    item_search_factory,
    feedback_email_search_factory
)

# def get_item_type_aggs(search_index):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_get_item_type_aggs -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_item_type_aggs(i18n_app, users, client_request_args, db_records2, records):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert not get_item_type_aggs("test-weko")


# def get_permission_filter(index_id: str = None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_get_permission_filter -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
class MockSearchPerm:
    def __init__(self):
        pass
    
    def can(self):
        return True

def test_get_permission_filter(i18n_app, users, client_request_args, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = get_permission_filter(33)
        assert res==([Match(publish_status='0'), Range(publish_date={'lte': 'now/d'}), Terms(path=[]), Bool(must=[Match(publish_status='0'), Match(relation_version_is_last='true')])], ['1'])
        mock_searchperm = MagicMock(side_effect=MockSearchPerm)
        with patch('weko_search_ui.query.search_permission', mock_searchperm):
            res = get_permission_filter()
            assert res==([Bool(must=[Terms(path=['1'])], should=[Match(weko_creator_id='5'), Match(weko_shared_id='5'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['1'])


# def default_search_factory(self, search, query_parser=None, search_type=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_default_search_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_default_search_factory(app, users, communities):
    _data = {
        'lang': 'en',
        'subject': 'test_subject',
        'id': '1',
        'id_attr': 'identifier',
        'license': 'test_license',
        'date_range1_from': '20221001',
        'date_range1_to': '20221030',
        'filedate_from': '20221001',
        'filedate_to': '20221030',
        'fd_attr': 'Accepted',
        'text1': 'test_text'
    }
    search = RecordsSearch()
    app.config['WEKO_SEARCH_KEYWORDS_DICT'] = WEKO_SEARCH_KEYWORDS_DICT
    app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            mock_searchperm = MagicMock(side_effect=MockSearchPerm)
            with patch('weko_search_ui.query.search_permission', mock_searchperm):
                _rv = (search, MultiDict([]))
                with patch('invenio_records_rest.facets.default_facets_factory', return_value=_rv):
                    res = default_search_factory(self=None, search=search)
                    assert res
    _data['community'] = 'comm1'
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            mock_searchperm = MagicMock(side_effect=MockSearchPerm)
            with patch('weko_search_ui.query.search_permission', mock_searchperm):
                _rv = (search, MultiDict([]))
                with patch('invenio_records_rest.facets.default_facets_factory', return_value=_rv):
                    res = default_search_factory(self=None, search=search)
                    assert res
    _data['search_type'] = '0'
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            mock_searchperm = MagicMock(side_effect=MockSearchPerm)
            with patch('weko_search_ui.query.search_permission', mock_searchperm):
                _rv = (search, MultiDict([]))
                with patch('invenio_records_rest.facets.default_facets_factory', return_value=_rv):
                    res = default_search_factory(self=None, search=search)
                    assert res
    _data['community'] = None
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            mock_searchperm = MagicMock(side_effect=MockSearchPerm)
            with patch('weko_search_ui.query.search_permission', mock_searchperm):
                _rv = (search, MultiDict([]))
                with patch('invenio_records_rest.facets.default_facets_factory', return_value=_rv):
                    res = default_search_factory(self=None, search=search)
                    assert res


# def item_path_search_factory(self, search, index_id=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_item_path_search_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_item_path_search_factory(i18n_app, users, indices):
    search = RecordsSearch()
    i18n_app.config['WEKO_SEARCH_TYPE_INDEX'] = 'index'
    i18n_app.config['OAISERVER_ES_MAX_CLAUSE_COUNT'] = 1
    i18n_app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with patch("weko_search_ui.query.get_item_type_aggs", return_value={}):
            mock_searchperm = MagicMock(side_effect=MockSearchPerm)
            with patch('weko_search_ui.query.search_permission', mock_searchperm):
                res = item_path_search_factory(self=None, search=search, index_id=33)
                assert res
                _rv = ([Bool(must=[Terms(path=[])], should=[Match(weko_creator_id='5'), Match(weko_shared_id='5'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['3', '4', '5'])
                with patch('weko_search_ui.query.get_permission_filter', return_value=_rv):
                    res = item_path_search_factory(self=None, search=search, index_id=None)
                    assert res


# def check_admin_user():
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_check_admin_user -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_admin_user(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = check_admin_user()
        assert res==('5', True)


# def opensearch_factory(self, search, query_parser=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_opensearch_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_opensearch_factory(i18n_app, users, indices):
    search = RecordsSearch()
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = opensearch_factory(self=None, search=search)
        assert res


# def item_search_factory(self, search, start_date, end_date, list_index_id=None, ignore_publish_status=False, ranking=False):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_item_search_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_item_search_factory(i18n_app, users, indices):
    search = RecordsSearch()
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = item_search_factory(
            self=None,
            search=search,
            start_date='2022-09-01',
            end_date='2022-09-30',
            list_index_id=[33])
        assert res


# def feedback_email_search_factory(self, search):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_feedback_email_search_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_feedback_email_search_factory(i18n_app, users, indices):
    search = RecordsSearch()
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = feedback_email_search_factory(self=None, search=search)
        assert res
