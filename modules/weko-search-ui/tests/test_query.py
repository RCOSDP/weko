import pytest
import json
import copy
from flask import request, url_for
from re import L
from elasticsearch_dsl.query import Match, Range, Terms, Bool
from mock import patch, MagicMock
from werkzeug import ImmutableMultiDict
from werkzeug.datastructures import MultiDict, CombinedMultiDict
from invenio_accounts.testutils import login_user_via_session

from invenio_search import RecordsSearch
from weko_admin.config import WEKO_ADMIN_MANAGEMENT_OPTIONS
from weko_search_ui.config import WEKO_SEARCH_KEYWORDS_DICT

from weko_search_ui.query import (
    get_item_type_aggs,
    get_permission_filter,
    default_search_factory,
    item_path_search_factory,
    check_permission_user,
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
        assert res==([Match(publish_status='0'), Range(publish_date={'lte': 'now/d','time_zone':'UTC'}), Terms(path=['33']), Bool(must=[Match(publish_status='0'), Match(relation_version_is_last='true')])], ['33','33/44'])
        mock_searchperm = MagicMock(side_effect=MockSearchPerm)
        with patch('weko_search_ui.query.search_permission', mock_searchperm):
            res = get_permission_filter()
            assert res==([Bool(must=[Terms(path=['33','44'])], should=[Match(weko_creator_id='5'), Match(weko_shared_id='5'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d','time_zone':'UTC'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['33','33/44'])


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
    with app.test_client() as client:
        login_user_via_session(client, email=users[3]["email"])
        search = RecordsSearch()
        app.config['WEKO_SEARCH_KEYWORDS_DICT'] = WEKO_SEARCH_KEYWORDS_DICT
        app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS
        with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
            app.extensions['invenio-oauth2server'] = 1
            app.extensions['invenio-queues'] = 1
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


# def check_permission_user():
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_check_permission_user -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_check_permission_user(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res = check_permission_user()
        assert res==('5', True)


# def opensearch_factory(self, search, query_parser=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_opensearch_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_opensearch_factory(i18n_app, users, indices, mocker):
    search = RecordsSearch()
    mocker.patch("weko_search_ui.query.search_permission",side_effect=MockSearchPerm)
    mocker.patch("weko_search_ui.permissions.search_permission",side_effect=MockSearchPerm)

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

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_function_issue35902 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_function_issue35902(app, users, communities, mocker):
    with app.test_client() as client:
        login_user_via_session(client, email=users[3]["email"])
        search = RecordsSearch()
        app.config['WEKO_SEARCH_KEYWORDS_DICT'] = WEKO_SEARCH_KEYWORDS_DICT
        app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS
        mocker.patch("weko_search_ui.query.search_permission",side_effect=MockSearchPerm)
        mocker.patch("weko_search_ui.permissions.search_permission",side_effect=MockSearchPerm)
        test = [
            {"bool":{"should":[{"match":{"weko_creator_id":None}},{"match":{"weko_shared_id":None}},{"bool":{"must":[{"match":{"publish_status":"0"}},{"range":{"publish_date":{"lte":"now/d","time_zone":"UTC"}}}]}}],"must":[{"terms":{"path":[]}}]}},
            {"bool":{"must":[{"match":{"relation_version_is_last":"true"}}]}},
        ]
        # not exist community
        # full text, detail search
        data = {
            "page":"1","size":"20","sort":"-createdate","creator":"","subject":"","sbjscheme":"","id":"","id_attr":"","type":"","itemtype":"","lang":"",
            "search_type":"0",
            "q":"test_data",
            "title":"aaa",
        }
        with app.test_request_context(headers=[("Accept-Language","en")],data=data):
            app.extensions['invenio-oauth2server'] = 1
            app.extensions['invenio-queues'] = 1
            test1 = copy.deepcopy(test)
            test1.append(
                {"multi_match":{"query":"aaa","type":"most_fields","minimum_should_match":"75%","operator":"and","fields":["search_title","search_title.ja"]}}
            )
            test1.append(
                {"bool":{"should":[
                    {"nested":{"query":{"multi_match":{"query":"test_data","operator":"and","fields":["content.attachment.content"]}},"path":"content"}},
                    {"query_string":{"query":"test_data","default_operator":"and","fields":["search_*","search_*.ja"]}}
                ]}}
            )
            res,urlkwargs = default_search_factory(self=None, search=search)
            result = (res.query()).to_dict()
            result = result["query"]["bool"]["filter"][0]["bool"]["must"]
            assert result == test1
        
        # detail search
        data = {
            "page":"1","size":"20","sort":"-createdate","creator":"","subject":"","sbjscheme":"","id":"","id_attr":"","type":"","itemtype":"","lang":"",
            "search_type":"0",
            "q":"",
            "title":"aaa",
        }
        with app.test_request_context(headers=[("Accept-Language","en")],data=data):
            app.extensions['invenio-oauth2server'] = 1
            app.extensions['invenio-queues'] = 1
            test2 = copy.deepcopy(test)
            test2.append(
                {"multi_match":{"query":"aaa","type":"most_fields","minimum_should_match":"75%","operator":"and","fields":["search_title","search_title.ja"]}}
            )
            res,urlkwargs = default_search_factory(self=None, search=search)
            result = (res.query()).to_dict()
            result = result["query"]["bool"]["filter"][0]["bool"]["must"]
            assert result == test2
            
        # full text search
        data = {
            "page":"1","size":"20","sort":"-createdate",
            "search_type":"0","q":"test_data"
        }
        with app.test_request_context(headers=[("Accept-Language","en")],data=data):
            app.extensions['invenio-oauth2server'] = 1
            app.extensions['invenio-queues'] = 1
            test3 = copy.deepcopy(test)
            test3.append(
                {"bool":{"should":[
                    {"nested":{"query":{"multi_match":{"query":"test_data","operator":"and","fields":["content.attachment.content"]}},"path":"content"}},
                    {"query_string":{"query":"test_data","default_operator":"and","fields":["search_*","search_*.ja"]}}
                ]}}
            )
            res,urlkwargs = default_search_factory(self=None, search=search)
            result = (res.query()).to_dict()
            result = result["query"]["bool"]["filter"][0]["bool"]["must"]
            assert result == test3
        
        # exist community
        test = [
            {"bool":{"should":[{"match":{"weko_creator_id":None}},{"match":{"weko_shared_id":None}},{"bool":{"must":[{"match":{"publish_status":"0"}},{"range":{"publish_date":{"lte":"now/d","time_zone":"UTC"}}}]}}],"must":[{"bool":{}}]}},
            {"bool":{"must":[{"match":{"relation_version_is_last":"true"}}]}},
        ]
        # full text, detail search
        data = {
            "page":"1","size":"20","sort":"-createdate","creator":"","subject":"","sbjscheme":"","id":"","id_attr":"","type":"","itemtype":"","lang":"",
            "search_type":"0",
            "q":"test_data",
            "title":"aaa",
            "community":"comm1"
        }
        with app.test_request_context(headers=[("Accept-Language","en")],data=data):
            app.extensions['invenio-oauth2server'] = 1
            app.extensions['invenio-queues'] = 1
            test1 = copy.deepcopy(test)
            test1.append(
                {"multi_match":{"query":"aaa","type":"most_fields","minimum_should_match":"75%","operator":"and","fields":["search_title","search_title.ja"]}}
            )
            test1.append(
                {"bool":{"should":[
                    {"nested":{"query":{"multi_match":{"query":"test_data","operator":"and","fields":["content.attachment.content"]}},"path":"content"}},
                    {"query_string":{"query":"test_data","default_operator":"and","fields":["search_*","search_*.ja"]}}
                ]}}
            )
            res,urlkwargs = default_search_factory(self=None, search=search)
            result = (res.query()).to_dict()
            result = result["query"]["bool"]["filter"][0]["bool"]["must"]
            assert result == test1
        
        # detail search
        data = {
            "page":"1","size":"20","sort":"-createdate","creator":"","subject":"","sbjscheme":"","id":"","id_attr":"","type":"","itemtype":"","lang":"",
            "search_type":"0",
            "q":"",
            "title":"aaa",
            "community":"comm1"
        }
        with app.test_request_context(headers=[("Accept-Language","en")],data=data):
            app.extensions['invenio-oauth2server'] = 1
            app.extensions['invenio-queues'] = 1
            test2 = copy.deepcopy(test)
            test2.append(
                {"multi_match":{"query":"aaa","type":"most_fields","minimum_should_match":"75%","operator":"and","fields":["search_title","search_title.ja"]}}
            )
            res,urlkwargs = default_search_factory(self=None, search=search)
            result = (res.query()).to_dict()
            result = result["query"]["bool"]["filter"][0]["bool"]["must"]
            assert result == test2
            
        # full text search
        data = {
            "page":"1","size":"20","sort":"-createdate",
            "search_type":"0","q":"test_data",
            "community":"comm1"
        }
        with app.test_request_context(headers=[("Accept-Language","en")],data=data):
            app.extensions['invenio-oauth2server'] = 1
            app.extensions['invenio-queues'] = 1
            test3 = copy.deepcopy(test)
            test3.append(
                {"bool":{"should":[
                    {"nested":{"query":{"multi_match":{"query":"test_data","operator":"and","fields":["content.attachment.content"]}},"path":"content"}},
                    {"query_string":{"query":"test_data","default_operator":"and","fields":["search_*","search_*.ja"]}}
                ]}}
            )
            res,urlkwargs = default_search_factory(self=None, search=search)
            result = (res.query()).to_dict()
            result = result["query"]["bool"]["filter"][0]["bool"]["must"]
            assert result == test3
        