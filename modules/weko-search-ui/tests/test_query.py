import pytest
import copy
from flask import request, url_for, current_app
from re import L
from elasticsearch_dsl.query import Match, Range, Terms, Bool
from mock import patch, MagicMock
from werkzeug import ImmutableMultiDict
from werkzeug.datastructures import MultiDict, CombinedMultiDict
from invenio_accounts.testutils import login_user_via_session

from invenio_search import RecordsSearch
from weko_admin.config import WEKO_ADMIN_MANAGEMENT_OPTIONS
from weko_search_ui.config import WEKO_SEARCH_KEYWORDS_DICT, WEKO_SEARCH_UI_OPENSEARCH_ID_PARAM

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
        assert res==([Match(publish_status='0'), Range(publish_date={'lte': 'now/d','time_zone':'UTC'}), Terms(path=['33']), Bool(must=[Match(publish_status='0'), Match(relation_version_is_last='true')])], ['33','33/44'])
        mock_searchperm = MagicMock(side_effect=MockSearchPerm)
        with patch('weko_search_ui.query.search_permission', mock_searchperm):
            res = get_permission_filter()
            assert res==([Bool(must=[Terms(path=['33','44'])], should=[Match(weko_creator_id='5'), Match(weko_shared_id='5'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d','time_zone':'UTC'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['33','33/44'])

def is_exist_key(dictionary, key):
    for dic1 in dictionary:
        if type(dic1)==dict and key in dic1.keys():
            return True
        else:
            if type(dic1)==dict and is_exist_key(dic1, key):
                return True
    return False

def is_exist_recursive(target, search_list):
    if type(target) == dict:
        for t_val in target.values():
            for s_item in search_list[:]:
                if t_val == s_item:
                    search_list.remove(s_item)
        if len(search_list) == 0:
            return True
        for t_vals in target.values():
            if is_exist_recursive(t_vals, search_list):
                return True
    elif type(target) == list:
        for t_item in target:
            for s_item in search_list[:]:
                if t_item == s_item:
                    search_list.remove(s_item)
        if len(search_list) == 0:
            return True
        for t_item in target:
            if is_exist_recursive(t_item, search_list):
                return True
        
    return False


# def default_search_factory(self, search, query_parser=None, search_type=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_default_search_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_default_search_factory(db, app, users, communities, db_index2, item_type, mocker):
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
        'text1': 'test_text',
        'sort': 'controlnumber'
    }
    with app.test_client() as client:
        login_user_via_session(client, email=users[3]["email"])
    search = RecordsSearch()
    app.config['WEKO_SEARCH_KEYWORDS_DICT'] = WEKO_SEARCH_KEYWORDS_DICT
    app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS
    mocker.patch("flask_login.utils._get_user", return_value=users[3]['obj'])
    filter_value = ([Bool(must=[Terms(path=[])], should=[Match(weko_creator_id='5'), Match(weko_shared_id='5'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['3', '4', '5'])
    mocker.patch("weko_search_ui.query.get_permission_filter", return_value=filter_value)
    mocker.patch("weko_search_ui.permissions.search_permission", side_effect=MockSearchPerm)
    mocker.patch("weko_search_ui.query.search_permission", side_effect=MockSearchPerm)
    mocker.patch("weko_search_ui.permissions.search_permission", side_effect=MockSearchPerm)

    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            mock_searchperm = MagicMock(side_effect=MockSearchPerm)
            with patch('weko_search_ui.query.search_permission', mock_searchperm):
                _rv = (search, MultiDict([]))
                with patch('invenio_records_rest.facets.default_facets_factory', return_value=_rv):
                    assert default_search_factory(self=None, search=search)

    # _get_search_index_query
    _data['index_id'] = '4'
    _data['idx'] = '0,1'
    _data['recursive'] = '1'
    expected = [
        {'match': {'path.tree': 0}},
        {'match': {'path.tree': 1}},
        {'match': {'path.tree': 2}},
        {'match': {'path.tree': 3}},
        {'match': {'path.tree': 4}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data['index_id'] = '2'
    _data['idx'] = '3,4'
    _data['recursive'] = '0'
    expected = [
        {'match': {'path.tree': 2}},
        {'match': {'path.tree': 3}},
        {'match': {'path.tree': 4}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data['index_id'] = '2'
    _data['idx'] = 'abc,edf'
    _data['recursive'] = '0'
    expected = [
        {'match': {'path.tree': 2}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data['date_range1_from'] = '2022'
    _data['date_range1_to'] = '2022'
    expected = [
        {'range': {'date_range1': {'gte': '2022', 'lte': '2022'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data['date_range1_from'] = '202211'
    _data['date_range1_to'] = '202212'
    expected = [
        {'range': {'date_range1': {'gte': '2022-11', 'lte': '2022-12'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data['date_range1_from'] = '20'
    _data['date_range1_to'] = '20221111111'
    expected = [
        {'range': {'date_range1': {'lte': '20221111111'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'date_range1_from': 'abcd',
        'date_range1_to': 'abcd'
    }
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert not is_exist_key(q_list[0], 'date_range1')
    # _get_search_type_query
    _data = {
        'typeList': '1,2,3,a,b',
    }
    expected = [
        {'match': {'type.raw': {'operator': 'and', 'query': 'bachelor thesis'}}},
        {'match': {'type.raw': {'operator': 'and', 'query': 'master thesis'}}},
        {'match': {'type.raw': {'operator': 'and', 'query': 'doctoral thesis'}}},
        {'match': {'type.raw': {'operator': 'and', 'query': 'departmental bulletin paper'}}},
        {'match': {'type.raw': {'operator': 'and', 'query': 'conference paper'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    # _get_search_id_query
    _data = {
        'idDes': '1',
        'idList': '1,2,3'
    }
    expected = [
        {'nested': {'path': 'identifier', 'query': {'bool': {'must': [{'match': {'identifier.value': {'operator': 'and', 'query': '1'}}}]}}}},
        {'nested': {'path': 'file.URI', 'query': {'bool': {'must': [{'match': {'file.URI.value': {'operator': 'and', 'query': '1'}}}]}}}},
        {'nested': {'path': 'identifierRegistration', 'query': {'bool': {'must': [{'match': {'identifierRegistration.value': {'operator': 'and', 'query': '1'}}}]}}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    # _get_search_license_query
    _data = {
        'riDes': '1',
        'riList': '101,102,999,free_input'
    }
    expected = [
        {'terms': {'content.licensetype.raw': ['license_0', 'license_6', 'license_1', 'license_7']}},
        {'terms': {'content.licensetype.raw': ['license_free']}},
        {"terms": {"content.licensefree.raw": ["1"]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'riDes': '1'
    }
    expected = [
        {'terms': {'content.licensetype.raw': ['license_free']}},
        {'terms': {"content.licensefree.raw": ['1']}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'riDes': '1',
        'riList': 'free_input'
    }
    expected = [
        {'terms': {'content.licensetype.raw': ['license_free']}},
        {'terms': {"content.licensefree.raw": ['1']}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'riDes': '0',
        'riList': 'free_input'
    }
    expected = [
        {'terms': {'content.licensetype.raw': ['license_free']}},
        {'terms': {"content.licensefree.raw": ['0']}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'riDes': '1',
        'riList': '101,102,999'
    }
    expected = [
        {'terms': {'content.licensetype.raw': ['license_0', 'license_6', 'license_1', 'license_7']}},
        {"terms": {"content.licensefree.raw": ['1']}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'riList': 'free_input'
    }
    expected = [
        {'terms': {'content.licensetype.raw': ['license_free']}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    # _get_date_query_for_opensearch
    _data = {
        'date': '202303',
        'pubYearFrom': '2021',
        'pubYearUntil': '2023',
        'pubDateFrom': '2021',
        'pubDateUntil': '2023'
    }
    expected = [
        {'range': {'file.date.value': {'gte': '2021', 'lte': '2023'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'pubYearFrom': '2021',
        'pubDateFrom': '2021'
    }
    expected = [
        {'range': {'file.date.value': {'gte': '2021'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'pubYearUntil': '2023',
        'pubDateUntil': '2023'
    }
    expected = [
        {'range': {'file.date.value': {'lte': '2023'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    current_app.config['WEKO_SEARCH_KEYWORDS_DICT'] = NG_FORMAT_WEKO_SEARCH_KEYWORDS_DICT
    _data = {
        'pubYearFrom': '2021',
        'pubDateFrom': '2021'
    }
    expected = [
        {'range': {'file.date.value': {'gte': '2021'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    current_app.config['WEKO_SEARCH_KEYWORDS_DICT'] = WEKO_SEARCH_KEYWORDS_DICT

    _data = {
        'date_range1_from': '2021333333333',
        'date_range1_to': '2021333333333'
    }
    expected = [
        {'range': {'date_range1': {'gte': '2021333333333', 'lte': '2021333333333'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'date_range1_to': '202112'
    }
    expected = [
        {'range': {'date_range1': {'lte': '2021-12'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    # default_parser FULL TEXT
    _data = {
        'search_type': '0',
        'all': 'information',
        'meta': 'information',
        'cur_index_id': 0,
        'recursive': 1
    }
    expected = [
        {'match': {'path.tree': 0}},
        {'match': {'path.tree': 1}},
        {'match': {'path.tree': 2}},
        {'match': {'path.tree': 3}},
        {'match': {'path.tree': 4}},
        {'query': 'information', 'default_operator': 'and', 'fields': ['search_*', 'search_*.ja']},
        {'query': 'information', 'default_operator': 'and', 'fields': ['search_*', 'search_*.ja']}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'search_type': '0',
        'all': 'information',
        'meta': 'information'
    }
    expected = [
        {'query': 'information', 'default_operator': 'and', 'fields': ['search_*', 'search_*.ja']},
        {'query': 'information', 'default_operator': 'and', 'fields': ['search_*', 'search_*.ja']}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    # _default_parser_community 
    _data = {
        'search_type': 0,
        'community': 'comm1',
        'all': 'information',
        'meta': 'information',
        'cur_index_id': 0,
        'recursive': 1
    }
    expected = [
        {'match': {'path.tree': 0}},
        {'match': {'path.tree': 1}},
        {'match': {'path.tree': 2}},
        {'match': {'path.tree': 3}},
        {'match': {'path.tree': 4}},
        {'terms': {'path': []}},
        {'query': 'information', 'default_operator': 'and', 'fields': ['search_*', 'search_*.ja']},
        {'query': 'information', 'default_operator': 'and', 'fields': ['search_*', 'search_*.ja']}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'search_type': 0,
        'community': 'comm1',
        'all': 'information',
        'meta': 'information'
    }
    expected = [
        {'terms': {'path': []}},
        {'query': 'information', 'default_operator': 'and', 'fields': ['search_*', 'search_*.ja']},
        {'query': 'information', 'default_operator': 'and', 'fields': ['search_*', 'search_*.ja']}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'search_type': '0',
        'index_id': '0'
    }
    expected = [
        {'terms': {'path': []}},
        {'bool': {'should': [{'match': {'path.tree': 0}}]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        mocker.patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=[0,1])
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    # _get_opensearch_parameter
    _data = {
        'pub': 'pub1'
    }
    expected = [
        {'multi_match': {'query': 'pub1', 'type': 'most_fields', 'minimum_should_match': '75%', 'operator': 'and', 'fields': ['search_publisher', 'search_publisher.ja']}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        print(q_list)
        assert is_exist_recursive(q_list, expected)
    _data = {
        'con': 'con1'
    }
    expected = [
        {'multi_match': {'query': 'con1', 'type': 'most_fields', 'minimum_should_match': '75%', 'operator': 'and', 'fields': ['search_contributor', 'search_contributor.ja']}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'form': 'text'
    }
    expected = [
        {'match': {'file.mimeType': {'operator': 'and', 'query': 'text'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'jtitle': 'sample title'
    }
    expected = [
        {'multi_match': {'query': 'sample title', 'type': 'most_fields', 'minimum_should_match': '75%', 'operator': 'and', 'fields': ['sourceTitle', 'sourceTitle.ja']}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'sp': 'sp-value'
    }
    expected = [
        {'match': {'geoLocation.geoLocationPlace': {'operator': 'and', 'query': 'sp-value'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'era': 'era-value'
    }
    expected = [
        {"match": {"temporal": {"operator": "and", "query": "era-value"}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'textver': '1.0'
    }
    expected = [
        {"match": {"versionType": {"operator": "and", "query": "1.0"}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'grantid': '2'
    }
    expected = [
        {"match": {"dissertationNumber": {"operator": "and", "query": "2"}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'grantor': 'sample'
    }
    expected = [
        {"multi_match": {"query": "sample", "type": "most_fields", "minimum_should_match": "75%", "operator": "and", "fields": ["dgName", "dgName.ja"]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'ln': 'fr',
        'itemTypeList': '1,2,3'
    }
    expected = [
        {'match': {'language': {'operator': 'and', 'query': 'fra'}}},
        {"bool": {"should": [{"match": {"itemtype.keyword": "test"}}, {"match": {"itemtype.keyword": "test2"}}, {"match": {"itemtype.keyword": "test3"}}]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    _data = {
        'lang': 'eng'
    }
    expected = [
        {'match': {'language': {'operator': 'and', 'query': 'eng'}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    # _get_object_query
    _data = {
        'subject': 'subject1',
        'kw': 'test_kw'
    }
    expected = [
        {'bool': {'must': [{'term': {'subject.value': 'subject1'}}]}}
    ]
    current_app.config["WEKO_SEARCH_KEYWORDS_DICT"] = WEKO_SEARCH_KEYWORDS_DICT
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)
    # keyword
    _data = {
        'kw': 'test_kw'
    }
    expected = [
        {"bool": {"must": [{"term": {"subject.value": "test_kw"}}]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert is_exist_recursive(q_list, expected)


#for community
# def default_search_factory(self, search, query_parser=None, search_type=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_default_search_factory2 -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_default_search_factory2(db, app, users, communities, db_index2, item_type, mocker):
    _data = {
        'lang': 'en',
        'sort': 'controlnumber'
    }
    with app.test_client() as client:
        login_user_via_session(client, email=users[3]["email"])
    search = RecordsSearch()
    app.config['WEKO_SEARCH_KEYWORDS_DICT'] = WEKO_SEARCH_KEYWORDS_DICT
    app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS
    mocker.patch("flask_login.utils._get_user", return_value=users[3]['obj'])
    #filter_value = ([Bool(must=[Terms(path=[])], should=[Match(weko_creator_id='5'), Match(weko_shared_id='5'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['3', '4', '5'])
    #mocker.patch("weko_search_ui.query.get_permission_filter", return_value=filter_value)
    mocker.patch("weko_search_ui.permissions.search_permission", side_effect=MockSearchPerm)
    mocker.patch("weko_search_ui.query.search_permission", side_effect=MockSearchPerm)
    mocker.patch("weko_search_ui.permissions.search_permission", side_effect=MockSearchPerm)

    _data['community'] = "comm1"
    expected = [
        {"terms": {"path": ["33"]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        print(q_list)
        assert is_exist_recursive(q_list, expected)

    _data['community'] = None
    expected = [
        {"terms": {"path": ["33"]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        print(q_list)
        assert not is_exist_recursive(q_list, expected)

# for not is_exist_recursive
# def default_search_factory(self, search, query_parser=None, search_type=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_default_search_factory3 -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_default_search_factory3(db, app, users, communities, db_index2, item_type, mocker):
    _data = {
        'lang': 'en'
    }
    with app.test_client() as client:
        login_user_via_session(client, email=users[3]["email"])
    search = RecordsSearch()
    app.config['WEKO_SEARCH_KEYWORDS_DICT'] = WEKO_SEARCH_KEYWORDS_DICT
    app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS
    mocker.patch("flask_login.utils._get_user", return_value=users[3]['obj'])
    filter_value = ([Bool(must=[Terms(path=[])], should=[Match(weko_creator_id='5'), Match(weko_shared_id='5'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['3', '4', '5'])
    mocker.patch("weko_search_ui.query.get_permission_filter", return_value=filter_value)
    mocker.patch("weko_search_ui.permissions.search_permission", side_effect=MockSearchPerm)
    mocker.patch("weko_search_ui.query.search_permission", side_effect=MockSearchPerm)
    mocker.patch("weko_search_ui.permissions.search_permission", side_effect=MockSearchPerm)

    _data = {
        'idDes': '1',
        'idList': '1,2,3'
    }
    expected = [
        {'nested': {'path': 'identifier', 'query': {'bool': {'must': [{'match': {'identifier.value': {'operator': 'and', 'query': '1'}}}]}}}},
        {'nested': {'path': 'file.URI', 'query': {'bool': {'must': [{'match': {'file.URI.value': {'operator': 'and', 'query': '1'}}}]}}}},
        {'nested': {'path': 'identifierRegistration', 'query': {'bool': {'must': [{'match': {'identifierRegistration.value': {'operator': 'and', 'query': '1'}}}]}}}}
    ]
    current_app.config["WEKO_SEARCH_UI_OPENSEARCH_ID_PARAM"] = NG_FORMAT_WEKO_SEARCH_UI_OPENSEARCH_ID_PARAM
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert not is_exist_recursive(q_list, expected)
    current_app.config["WEKO_SEARCH_UI_OPENSEARCH_ID_PARAM"] = WEKO_SEARCH_UI_OPENSEARCH_ID_PARAM
    _data = {
        'idDes': '1',
        'idList': '1,2,3'
    }
    expected = [
        {'nested': {'path': 'identifier', 'query': {'bool': {'must': [{'match': {'identifier.value': {'operator': 'and', 'query': '1'}}}]}}}},
    ]
    current_app.config["WEKO_SEARCH_UI_OPENSEARCH_ID_PARAM"] = []
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert not is_exist_recursive(q_list, expected)
    current_app.config["WEKO_SEARCH_UI_OPENSEARCH_ID_PARAM"] = WEKO_SEARCH_UI_OPENSEARCH_ID_PARAM
    _data = {
        'idDes': '1',
        'idList': 'xxxx'
    }
    expected = [
        {'nested': {'path': 'identifier', 'query': {'bool': {'must': [{'match': {'identifier.value': {'operator': 'and', 'query': '1'}}}]}}}},
        {'nested': {'path': 'file.URI', 'query': {'bool': {'must': [{'match': {'file.URI.value': {'operator': 'and', 'query': '1'}}}]}}}},
        {'nested': {'path': 'identifierRegistration', 'query': {'bool': {'must': [{'match': {'identifierRegistration.value': {'operator': 'and', 'query': '1'}}}]}}}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert not is_exist_recursive(q_list, expected)
    _data = {
        'idDes': '0',
        'idList': 'xxxx'
    }
    expected = [
        {"multi_match":{"query":"0","type":"most_fields","minimum_should_match":"75%","operator":"and","fields":["search_title","search_title.ja"]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert not is_exist_recursive(q_list, expected)
    _data = {
        'idDes': '0',
        'idList': ''
    }
    expected = [
        {"multi_match":{"query":"0","type":"most_fields","minimum_should_match":"75%","operator":"and","fields":["search_title","search_title.ja"]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert not is_exist_recursive(q_list, expected)
    _data = {
        'riList': '101,102,999,free_input'
    }
    expected = [
        {'terms': {'content.licensetype.raw': ['license_0', 'license_6', 'license_1', 'license_7']}},
        {'terms': {'content.licensetype.raw': ['license_free']}},
        {"terms": {"content.licensefree.raw": ["0"]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert not is_exist_recursive(q_list, expected)
    _data = {
        'riDes': '0',
        'riList': ''
    }
    expected = [
        {'terms': {'content.licensetype.raw': ['license_0', 'license_6', 'license_1', 'license_7']}},
        {'terms': {'content.licensetype.raw': ['license_free']}},
        {"terms": {"content.licensefree.raw": ["0"]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert not is_exist_recursive(q_list, expected)
    _data = {
        'itemTypeList': None
    }
    expected = [
        {"bool": {"should": [{"match": {"itemtype.keyword": "test"}}, {"match": {"itemtype.keyword": "test2"}}, {"match": {"itemtype.keyword": "test3"}}]}}
    ]
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert not is_exist_recursive(q_list, expected)
    _data = {
        'subject': 'test_subject',
        'kw': 'test_kw'
    }
    expected = [
        {'bool': {'must': [{'term': {'subject.value': 'test_subject'}}]}}
    ]
    current_app.config["WEKO_SEARCH_KEYWORDS_DICT"] = WEKO_SEARCH_KEYWORDS_DICT_1
    with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        res, _ = default_search_factory(self=None, search=search)
        result = (res.query()).to_dict()
        q_list = result['query']['bool']['filter'][0]['bool']['must']
        assert not is_exist_recursive(q_list, expected)
    current_app.config["WEKO_SEARCH_KEYWORDS_DICT"] = WEKO_SEARCH_KEYWORDS_DICT

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


        # keyword search
        data = {
            "page":"1","size":"20","sort":"-createdate","creator":"","subject":"sub","sbjscheme":"","id":"","id_attr":"","type":"","itemtype":"","lang":"",
            "search_type":"0",
            "q":"",
            "title":"aaa",
            "community":"comm1",
            "kw":"test"
        }
        with app.test_request_context(headers=[("Accept-Language","en")],data=data):
            app.extensions['invenio-oauth2server'] = 1
            app.extensions['invenio-queues'] = 1
            test4 = copy.deepcopy(test)
            test4.append(
                {"multi_match":{"query":"aaa","type":"most_fields","minimum_should_match":"75%","operator":"and","fields":["search_title","search_title.ja"]}}
            )
            test4.append({"bool":{"must":[{"term":{"subject.value":"sub"}}]}})
            res,urlkwargs = default_search_factory(self=None, search=search)
            result = (res.query()).to_dict()
            result = result["query"]["bool"]["filter"][0]["bool"]["must"]
            assert result == test4

NG_FORMAT_WEKO_SEARCH_KEYWORDS_DICT = {
    "nested": {
        "id": (
            "",
            {
                "id_attr": {
                    "identifier": ("relation.relatedIdentifier", "identifierType=*"),
                    "URI": ("identifier", "identifierType=*"),
                    "fullTextURL": ("file.URI", "objectType=*"),
                    "selfDOI": ("identifierRegistration", "identifierType=*"),
                    "ISBN": ("relation.relatedIdentifier", "identifierType=ISBN"),
                    "ISSN": ("sourceIdentifier", "identifierType=ISSN"),
                    "NCID": [
                        ("relation.relatedIdentifier", "identifierType=NCID"),
                        ("sourceIdentifier", "identifierType=NCID"),
                    ],
                    "pmid": ("relation.relatedIdentifier", "identifierType=PMID"),
                    "doi": ("relation.relatedIdentifier", "identifierType=DOI"),
                    "NAID": ("relation.relatedIdentifier", "identifierType=NAID"),
                    "ichushi": ("relation.relatedIdentifier", "identifierType=ICHUSHI"),
                }
            },
        ),
        "license": ("content", {"license": ("content.licensetype.raw")}),
    },
    "string": {
        "title": ["search_title", "search_title.ja"],
        "creator": ["search_creator", "search_creator.ja"],
        "des": ["search_des", "search_des.ja"],
        "publisher": ["search_publisher", "search_publisher.ja"],
        "cname": ["search_contributor", "search_contributor.ja"],
        "itemtype": ("itemtype.keyword", str),
        "type": {
            "type.raw": [
                "conference paper",
                "data paper",
                "departmental bulletin paper",
                "editorial",
                "journal article",
                "newspaper",
                "periodical",
                "review article",
                "software paper",
                "article",
                "book",
                "book part",
                "cartographic material",
                "map",
                "conference object",
                "conference proceedings",
                "conference poster",
                "dataset",
                "interview",
                "image",
                "still image",
                "moving image",
                "video",
                "lecture",
                "patent",
                "internal report",
                "report",
                "research report",
                "technical report",
                "policy report",
                "report part",
                "working paper",
                "data management plan",
                "sound",
                "thesis",
                "bachelor thesis",
                "master thesis",
                "doctoral thesis",
                "interactive resource",
                "learning object",
                "manuscript",
                "musical notation",
                "research proposal",
                "software",
                "technical documentation",
                "workflow",
                "other",
            ]
        },
        "mimetype": "file.mimeType",
        "language": {
            "language": [
                "jpn",
                "eng",
                "fra",
                "ita",
                "deu",
                "spa",
                "zho",
                "rus",
                "lat",
                "msa",
                "epo",
                "ara",
                "ell",
                "kor",
                "-",
            ]
        },
        "srctitle": ["sourceTitle", "sourceTitle.ja"],
        "spatial": "geoLocation.geoLocationPlace",
        "temporal": "temporal",
        "version": "versionType",
        "dissno": "dissertationNumber",
        "degreename": ["degreeName", "degreeName.ja"],
        "dgname": ["dgName", "dgName.ja"],
        "wid": ("creator.nameIdentifier", str),
        "iid": ("path.tree", int),
    },
    "date": {
        "dategranted": "dateGranted",
        "date_range1": [],
        "date_range2": [("from", "to"), "date_range2"]
    },
    "object": {
        "subject": (
            "subject",
            {
                "sbjscheme": {
                    "subject.subjectScheme": [
                        "BSH",
                        "DDC",
                        "LCC",
                        "LCSH",
                        "MeSH",
                        "NDC",
                        "NDLC",
                        "NDLSH",
                        "UDC",
                        "Other",
                        "SciVal",
                    ]
                }
            },
        ),
        "scDes": (
            "subject",
            {
                "scList": {
                    "subject.subjectScheme": [
                        "BSH",
                        "DDC",
                        "LCC",
                        "LCSH",
                        "MeSH",
                        "NDC",
                        "NDLC",
                        "NDLSH",
                        "UDC",
                        "Other",
                        "SciVal",
                    ]
                }
            },
        ),
    },
    "text": {
        "text1": "text1",
        "text2": "text2",
        "text3": "text3",
        "text4": "text4",
        "text5": "text5",
        "text6": "text6",
        "text7": "text7",
        "text8": "text8",
        "text9": "text9",
        "text10": "text10",
        "text11": "text11",
        "text12": "text12",
        "text13": "text13",
        "text14": "text14",
        "text15": "text15",
        "text16": "text16",
        "text17": "text17",
        "text18": "text18",
        "text19": "text19",
        "text20": "text20",
        "text21": "text21",
        "text22": "text22",
        "text23": "text23",
        "text24": "text24",
        "text25": "text25",
        "text26": "text26",
        "text27": "text27",
        "text28": "text28",
        "text29": "text29",
        "text30": "text30",
    },
    "range": {
        "integer_range1": [("from", "to"), "integer_range1"],
        "integer_range2": [("from", "to"), "integer_range2"],
        "integer_range3": [("from", "to"), "integer_range3"],
        "integer_range4": [("from", "to"), "integer_range4"],
        "integer_range5": [("from", "to"), "integer_range5"],
        "float_range1": [("from", "to"), "float_range1"],
        "float_range2": [("from", "to"), "float_range2"],
        "float_range3": [("from", "to"), "float_range3"],
        "float_range4": [("from", "to"), "float_range4"],
        "float_range5": [("from", "to"), "float_range5"],
    },
    "geo_distance": {"geo_point1": [("lat", "lon", "distance"), "geo_point1"]},
    "geo_shape": {"geo_shape1": [("lat", "lon", "distance"), "geo_shape1"]},
}

WEKO_SEARCH_KEYWORDS_DICT_1 = {
    "nested": {
        "id": (
            "",
            {
                "id_attr": {
                    "identifier": ("relation.relatedIdentifier", "identifierType=*"),
                    "URI": ("identifier", "identifierType=*"),
                    "fullTextURL": ("file.URI", "objectType=*"),
                    "selfDOI": ("identifierRegistration", "identifierType=*"),
                    "ISBN": ("relation.relatedIdentifier", "identifierType=ISBN"),
                    "ISSN": ("sourceIdentifier", "identifierType=ISSN"),
                    "NCID": [
                        ("relation.relatedIdentifier", "identifierType=NCID"),
                        ("sourceIdentifier", "identifierType=NCID"),
                    ],
                    "pmid": ("relation.relatedIdentifier", "identifierType=PMID"),
                    "doi": ("relation.relatedIdentifier", "identifierType=DOI"),
                    "NAID": ("relation.relatedIdentifier", "identifierType=NAID"),
                    "ichushi": ("relation.relatedIdentifier", "identifierType=ICHUSHI"),
                }
            },
        ),
        "license": ("content", {"license": ("content.licensetype.raw")}),
    },
    "string": {
        "title": ["search_title", "search_title.ja"],
        "creator": ["search_creator", "search_creator.ja"],
        "des": ["search_des", "search_des.ja"],
        "publisher": ["search_publisher", "search_publisher.ja"],
        "cname": ["search_contributor", "search_contributor.ja"],
        "itemtype": ("itemtype.keyword", str),
        "type": {
            "type.raw": [
                "conference paper",
                "data paper",
                "departmental bulletin paper",
                "editorial",
                "journal article",
                "newspaper",
                "periodical",
                "review article",
                "software paper",
                "article",
                "book",
                "book part",
                "cartographic material",
                "map",
                "conference object",
                "conference proceedings",
                "conference poster",
                "dataset",
                "interview",
                "image",
                "still image",
                "moving image",
                "video",
                "lecture",
                "patent",
                "internal report",
                "report",
                "research report",
                "technical report",
                "policy report",
                "report part",
                "working paper",
                "data management plan",
                "sound",
                "thesis",
                "bachelor thesis",
                "master thesis",
                "doctoral thesis",
                "interactive resource",
                "learning object",
                "manuscript",
                "musical notation",
                "research proposal",
                "software",
                "technical documentation",
                "workflow",
                "other",
            ]
        },
        "mimetype": "file.mimeType",
        "language": {
            "language": [
                "jpn",
                "eng",
                "fra",
                "ita",
                "deu",
                "spa",
                "zho",
                "rus",
                "lat",
                "msa",
                "epo",
                "ara",
                "ell",
                "kor",
                "-",
            ]
        },
        "srctitle": ["sourceTitle", "sourceTitle.ja"],
        "spatial": "geoLocation.geoLocationPlace",
        "temporal": "temporal",
        "version": "versionType",
        "dissno": "dissertationNumber",
        "degreename": ["degreeName", "degreeName.ja"],
        "dgname": ["dgName", "dgName.ja"],
        "wid": ("creator.nameIdentifier", str),
        "iid": ("path.tree", int),
    },
    "date": {
        "filedate": [
            ("from", "to"),
            (
                "file.date",
                {
                    "fd_attr": {
                        "file.date.dateType": [
                            "Accepted",
                            "Available",
                            "Collected",
                            "Copyrighted",
                            "Created",
                            "Issued",
                            "Submitted",
                            "Updated",
                            "Valid",
                        ]
                    }
                },
            ),
        ],
        "dategranted": [("from", "to"), "dateGranted"],
        "date_range1": [("from", "to"), "date_range1"],
        "date_range2": [("from", "to"), "date_range2"],
        "date_range3": [("from", "to"), "date_range3"],
        "date_range4": [("from", "to"), "date_range4"],
        "date_range5": [("from", "to"), "date_range5"],
    },
    "object": {
        "scDes": (
            "subject",
            {
                "scList": {
                    "subject.subjectScheme": [
                        "BSH",
                        "DDC",
                        "LCC",
                        "LCSH",
                        "MeSH",
                        "NDC",
                        "NDLC",
                        "NDLSH",
                        "UDC",
                        "Other",
                        "SciVal",
                    ]
                }
            },
        ),
    },
    "text": {
        "text1": "text1",
        "text2": "text2",
        "text3": "text3",
        "text4": "text4",
        "text5": "text5",
        "text6": "text6",
        "text7": "text7",
        "text8": "text8",
        "text9": "text9",
        "text10": "text10",
        "text11": "text11",
        "text12": "text12",
        "text13": "text13",
        "text14": "text14",
        "text15": "text15",
        "text16": "text16",
        "text17": "text17",
        "text18": "text18",
        "text19": "text19",
        "text20": "text20",
        "text21": "text21",
        "text22": "text22",
        "text23": "text23",
        "text24": "text24",
        "text25": "text25",
        "text26": "text26",
        "text27": "text27",
        "text28": "text28",
        "text29": "text29",
        "text30": "text30",
    },
    "range": {
        "integer_range1": [("from", "to"), "integer_range1"],
        "integer_range2": [("from", "to"), "integer_range2"],
        "integer_range3": [("from", "to"), "integer_range3"],
        "integer_range4": [("from", "to"), "integer_range4"],
        "integer_range5": [("from", "to"), "integer_range5"],
        "float_range1": [("from", "to"), "float_range1"],
        "float_range2": [("from", "to"), "float_range2"],
        "float_range3": [("from", "to"), "float_range3"],
        "float_range4": [("from", "to"), "float_range4"],
        "float_range5": [("from", "to"), "float_range5"],
    },
    "geo_distance": {"geo_point1": [("lat", "lon", "distance"), "geo_point1"]},
    "geo_shape": {"geo_shape1": [("lat", "lon", "distance"), "geo_shape1"]},
}

NG_FORMAT_WEKO_SEARCH_UI_OPENSEARCH_ID_PARAM = [ dict() ]