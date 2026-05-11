import json
import copy
import pytest
from elasticsearch_dsl.query import Match, Range, Terms, Bool
from mock import patch, MagicMock
from werkzeug.datastructures import MultiDict
from invenio_accounts.testutils import login_user_via_session

from invenio_i18n.ext import current_i18n
from invenio_search import RecordsSearch
from weko_admin.config import WEKO_ADMIN_MANAGEMENT_OPTIONS
from weko_search_ui.config import WEKO_SEARCH_KEYWORDS_DICT, WEKO_SEARCH_TYPE_DICT

from weko_search_ui.query import (
    get_item_type_aggs,
    get_permission_filter,
    default_search_factory,
    item_path_search_factory,
    check_permission_user,
    opensearch_factory,
    item_search_factory,
    _split_text_by_or
)


@pytest.fixture(autouse=True)
def _mock_facet_search_query():
    """Mock get_facet_search_query to avoid KeyError 'Data Language' from stale redis cache."""
    class FacetDict(dict):
        def get(self, key, default=None):
            return {"aggs": {}, "post_filters": {}}
        def __getitem__(self, key):
            return {"aggs": {}, "post_filters": {}}
    with patch("weko_admin.utils.get_facet_search_query", return_value=FacetDict()):
        yield

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

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_get_permission_filter -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_permission_filter(i18n_app, users, client_request_args, indices):
    # is_perm is True
    with patch('weko_search_ui.query.search_permission.can', return_value=True):
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            # result is False
            with patch("weko_search_ui.query.check_permission_user",return_value=(users[3]["id"],False)):
                # exist index_id, search_type = Full_TEXT
                with i18n_app.test_request_context("/test?search_type=0"):
                    # index_id in is_perm_indexes
                    with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", "66"]):
                        res = get_permission_filter(33)
                        assert res == ([], ["33", "33/44", '66'])
                    # index_id not in is_perm_indexes
                    with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=[]):
                        res = get_permission_filter(33333)
                        assert res == ([], [])
                # exist index_id, search_type = INDEX
                with i18n_app.test_request_context("/test?search_type=2"):
                    # index_id in is_perm_indexes
                    with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", '66']):
                        res = get_permission_filter(33)
                        assert res == ([], ["33", "33/44", '66'])
                    # index_id not in is_perm_indexes
                    with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=[]):
                        res = get_permission_filter(33333)
                        assert res == ([], [])
                # not exist index_id
                with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", '66']):
                    res = get_permission_filter()
                    assert res == ([], ["33", "33/44", '66'])
            # result is True
            with patch("weko_search_ui.query.check_permission_user",return_value=(users[3]["id"],True)):
                # exist index_id, search_type = Full_TEXT
                with i18n_app.test_request_context("/test?search_type=0"):
                    # index_id in is_perm_indexes
                    with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", "66"]):
                        res = get_permission_filter(33)
                        assert res == ([Bool(must=[Bool(should=[Terms(path=['33'])])], should=[Bool(must=[Terms(publish_status=['0', '1']), Match(weko_creator_id=5)]), Bool(must=[Terms(publish_status=['0', '1']), Terms(weko_shared_ids=[5])]), Bool(must=[Terms(publish_status=['0', '1'])])]), Bool(must=[Match(relation_version_is_last='true')])],
                                       ["33", "33/44", '66'])
                    # index_id not in is_perm_indexes
                    with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", "66"]):
                        res = get_permission_filter(33333)
                        assert res == ([Bool(must=[Bool()], should=[Bool(must=[Terms(publish_status=['0', '1']), Match(weko_creator_id=5)]), Bool(must=[Terms(publish_status=['0', '1']), Terms(weko_shared_ids=[5])]), Bool(must=[Terms(publish_status=['0', '1'])])]), Bool(must=[Match(relation_version_is_last='true')])],
                                        ['33', '33/44', '66'])
                # exist index_id, search_type = INDEX
                with i18n_app.test_request_context("/test?search_type=2"):
                    # index_id in is_perm_indexes
                    with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", "66"]):
                        res = get_permission_filter(33)
                        assert res == ([Bool(must=[Terms(path=['33'])], should=[Bool(must=[Terms(publish_status=['0', '1']), Match(weko_creator_id=5)]), Bool(must=[Terms(publish_status=['0', '1']), Terms(weko_shared_ids=[5])]), Bool(must=[Terms(publish_status=['0', '1'])])]), Bool(must=[Match(relation_version_is_last='true')])],
                                       ['33', '33/44', '66'])
                    # index_id not in is_perm_indexes
                    with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", "66"]):
                        res = get_permission_filter(33333)
                        assert res == ([Bool(must=[Terms(path=[])], should=[Bool(must=[Terms(publish_status=['0', '1']), Match(weko_creator_id=5)]), Bool(must=[Terms(publish_status=['0', '1']), Terms(weko_shared_ids=[5])]), Bool(must=[Terms(publish_status=['0', '1'])])]), Bool(must=[Match(relation_version_is_last='true')])],
                                       ['33', '33/44', '66'])
                # not exist index_id
                with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", '66']):
                    res = get_permission_filter()
                    assert res == ([Bool(must=[Terms(path=['33', '44', '66'])], should=[Bool(must=[Terms(publish_status=['0', '1']), Match(weko_creator_id=5)]), Bool(must=[Terms(publish_status=['0', '1']), Terms(weko_shared_ids=[5])]), Bool(must=[Terms(publish_status=['0', '1'])])]), Bool(must=[Match(relation_version_is_last='true')])], ['33', '33/44', '66'])
        # not admin user
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("weko_search_ui.query.check_permission_user",return_value=(users[1]["id"],True)):
                with i18n_app.test_request_context("/test?search_type=0"):
                    res = get_permission_filter(33)
                    assert res == ([Bool(must=[Bool()], should=[Bool(must=[Terms(publish_status=['0', '1']), Match(weko_creator_id=2)]), Bool(must=[Terms(publish_status=['0', '1']), Terms(weko_shared_ids=[2])]), Bool(must=[Terms(publish_status=['0']), Range(publish_date={'lte': 'now/d', 'time_zone': 'UTC'})])]), Bool(must=[Match(relation_version_is_last='true')])], [])
                with i18n_app.test_request_context("/test?search_type=2"):
                    res = get_permission_filter(33)
                    assert res == ([Bool(must=[Terms(path=[])], should=[Bool(must=[Terms(publish_status=['0', '1']), Match(weko_creator_id=2)]), Bool(must=[Terms(publish_status=['0', '1']), Terms(weko_shared_ids=[2])]), Bool(must=[Terms(publish_status=['0']), Range(publish_date={'lte': 'now/d', 'time_zone': 'UTC'})])]), Bool(must=[Match(relation_version_is_last='true')])], [])
                res = get_permission_filter()
                assert res == ([Bool(must=[Terms(path=[])], should=[Bool(must=[Terms(publish_status=['0', '1']), Match(weko_creator_id=2)]), Bool(must=[Terms(publish_status=['0', '1']), Terms(weko_shared_ids=[2])]), Bool(must=[Terms(publish_status=['0']), Range(publish_date={'lte': 'now/d', 'time_zone': 'UTC'})])]), Bool(must=[Match(relation_version_is_last='true')])], [])
    # is_perm is False
    with patch('weko_search_ui.query.search_permission.can', return_value=False):
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            with i18n_app.test_request_context("/test?search_type=2"):
                # index_id in is_perm_indexes
                with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", '66']):
                    res = get_permission_filter(33)
                    assert res == ([Terms(publish_status=['0', '1']), Terms(path=['33']), Bool(must=[Terms(publish_status=['0', '1']), Match(relation_version_is_last='true')])], ['33', '33/44', '66'])

    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44"]):
            res = get_permission_filter(33)
            expected = ([Terms(publish_status=['0', '1']), Terms(path=['33']), Bool(must=[Terms(publish_status=['0', '1']), Match(relation_version_is_last='true')])],
                        ['33','33/44'])
            assert res==expected
        mock_searchperm = MagicMock(side_effect=MockSearchPerm)
        with patch('weko_search_ui.query.search_permission', mock_searchperm):
            with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44"]):
                res = get_permission_filter()
                expected = ([Bool(must=[Terms(path=['33', '44'])], should=[Bool(must=[Terms(publish_status=['0', '1']), Match(weko_creator_id='5')]), Bool(must=[Terms(publish_status=['0', '1']), Terms(weko_shared_ids=['5'])]), Bool(must=[Terms(publish_status=['0', '1'])])]), Bool(must=[Match(relation_version_is_last='true')])],
                            ['33','33/44'])
                assert res==expected


def test_get_permission_filter_with_community(i18n_app, users, client_request_args, indices, communities):
    # is_perm is True
    with patch('weko_search_ui.query.search_permission.can', return_value=True):
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            # result is False
            with patch("weko_search_ui.query.check_permission_user",return_value=(users[3]["id"],True)):
                with patch("weko_search_ui.query.Indexes.get_browsing_tree_paths", return_value=["33", "33/44"]):
                    with patch("weko_search_ui.query.Indexes.get_child_list_recursive", return_value=["33", "44"]):
                        # exist index_id, search_type = Full_TEXT
                        with i18n_app.test_request_context("/test?search_type=0"):
                            # index_id in is_perm_indexes
                            res = get_permission_filter(33, is_community=True)
                            assert "[Bool(must=[Bool(should=[Terms(path=['33', '44'])])]" in str(res[0])
                        # exist index_id, search_type = keyword/index
                        with i18n_app.test_request_context("/test?search_type=1"):
                            # index_id in is_perm_indexes
                            res = get_permission_filter(33, is_community=True)
                            assert "[Bool(must=[Terms(path=['33', '44'])]" in str(res[0])


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_get_permission_filter_fulltext -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_get_permission_filter_fulltext(i18n_app, users, client_request_args_FULL_TEXT, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", "66"]):
            res = get_permission_filter(33)
            assert res==([Terms(publish_status=['0', '1']), Bool(should=[Terms(path=['33'])]), Bool(must=[Terms(publish_status=['0', '1']), Match(relation_version_is_last='true')])],
                         ['33','33/44', '66'])
        mock_searchperm = MagicMock(side_effect=MockSearchPerm)
        with patch('weko_search_ui.query.search_permission', mock_searchperm):
            with patch("weko_index_tree.api.Indexes.get_browsing_tree_paths", return_value=["33", "33/44", "66"]):
                res = get_permission_filter()
                assert res==([Bool(must=[Terms(path=['33','44', '66'])], should=[Bool(must=[Terms(publish_status=['0', '1']), Match(weko_creator_id='5')]), Bool(must=[Terms(publish_status=['0', '1']), Terms(weko_shared_ids=['5'])]), Bool(must=[Terms(publish_status=['0', '1'])])]), Bool(must=[Match(relation_version_is_last='true')])],
                        ['33','33/44', '66'])


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

        _data["lang"] = "jpn,other"
        with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
            with patch("weko_search_ui.query.Indexes.get_browsing_tree_paths",return_value=["33", "33/44"]):
                from flask_login.utils import login_user
                login_user(users[3]["obj"])
                app.preprocess_request()
                app.extensions['invenio-oauth2server'] = 1
                app.extensions['invenio-queues'] = 1
                res = default_search_factory(self=None, search=search)
                query = (res[0].query()).to_dict()
                assert query == {"query": {"bool": {"filter": [{"bool": {"must": [{"bool": {"should": [{"bool": {"must": [{"terms": {"publish_status": ["0", "1"]}}, {"match": {"weko_creator_id": "5"}}]}}, {"bool": {"must": [{"terms": {"publish_status": ["0", "1"]}}, {"terms": {"weko_shared_ids": ["5"]}}]}}, {"bool": {"must": [{"terms": {"publish_status": ["0", "1"]}}]}}], "must": [{"terms": {"path": ["33", "44"]}}]}}, {"bool": {"must": [{"match": {"relation_version_is_last": "true"}}]}}, {"bool": {"should": [{"match": {"language": {"operator": "and", "query": "jpn"}}}, {"bool": {"filter": [{"script": {"script": {"source": "boolean flg=false; for(lang in doc['language']){if (!params.param1.contains(lang)){flg=true;}} return flg;", "params": {"param1": ["jpn", "eng", "fra", "ita", "deu", "spa", "zho", "rus", "lat", "msa", "epo", "ara", "ell", "kor", "other"]}}}}]}}]}}, {"bool": {"should": [{"nested": {"path": "relation.relatedIdentifier", "query": {"bool": {"must": [{"match": {"relation.relatedIdentifier.value": {"operator": "and", "query": "1"}}}]}}}}]}}, {"bool": {"should": [{"nested": {"path": "content", "query": {"bool": {"must": [{"terms": {"content.licensetype.raw": ["test_license"]}}]}}}}]}}, {"nested": {"path": "file.date", "query": {"bool": {"should": [{"term": {"file.date.dateType": "Accepted"}}], "must": [{"range": {"file.date.value": {"gte": "2022-10-01", "lte": "2022-10-30"}}}]}}}}, {"range": {"date_range1": {"gte": "2022-10-01", "lte": "2022-10-30"}}}, {"match": {"text1": {"operator": "and", "query": "test_text"}}}]}}], "must": [{"match_all": {}}]}}, "_source": {"excludes": ["content"]}}


        mock_searchperm = MagicMock(side_effect=MockSearchPerm)
        with patch('weko_search_ui.query.search_permission', mock_searchperm):
            with patch('invenio_records_rest.facets.default_facets_factory', side_effect=lambda x,y: (x, MultiDict([]))):

                EXPECT0 = {'bool': {'should': [{'bool': {'must': [{'terms': {'publish_status': ['0', '1']}}, {'match': {'weko_creator_id': None}}]}},
                                               {'bool': {'must': [{'terms': {'publish_status': ['0', '1']}}, {'terms': {'weko_shared_ids': [None]}}]}},
                                               {'bool': {'must': [{'terms': {'publish_status': ['0']}},
                                                                  {'range': {'publish_date': {'lte': 'now/d', 'time_zone': 'UTC'}}}]}}],
                                    'must': [{'terms': {'path': []}}]}}
                EXPECT1 = {'bool': {'must': [{'match': {'relation_version_is_last': 'true'}}]}}
                # _get_search_qs_query test
                _data = {"q": "AAA BBB" }
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect = {'query_string': {'query': 'AAA BBB', 'default_operator': 'and', 'fields': ['search_*', 'search_*.ja']}}
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                _data = {"q": "AAA　|　BBB" }
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect['query_string']['query'] = 'AAA OR BBB'
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                # _get_keywords_query test (mimetype)
                _data = {"mimetype": "AAA BBB"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect = {'match': {'file.mimeType': {'operator': 'and', 'query': ''}}}
                    expect['match']['file.mimeType']['query'] = "AAA BBB"
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                _data = {"mimetype": "AAA BBB OR CCC"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0 = copy.deepcopy(expect)
                    expect_1 = copy.deepcopy(expect)
                    expect_1['match']['file.mimeType']['query'] = "CCC"
                    expect = {
                        'bool': {
                            'should':[expect_0, expect_1],
                            'minimum_should_match': 1
                        }
                    }
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                # _get_keywords_query test (title)
                additional_params = {"exact_title_match": False}
                _data = {"title": "AAA BBB"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect = {
                        'multi_match': {
                                'query': '',
                                'type': 'most_fields',
                                'minimum_should_match': '75%',
                                'operator': 'and',
                                'fields': ['search_title', 'search_title.ja']
                            }
                    }
                    expect['multi_match']['query'] = 'AAA BBB'
                    search_query, _ = default_search_factory(self=None, search=search, additional_params=additional_params)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                _data = {"title": "AAA BBB OR CCC"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0 = copy.deepcopy(expect)
                    expect_1 = copy.deepcopy(expect)
                    expect_1['multi_match']['query'] = 'CCC'
                    expect = {
                        'bool': {
                            'should':[expect_0, expect_1],
                            'minimum_should_match': 1
                        }
                    }
                    search_query, _ = default_search_factory(self=None, search=search, additional_params=additional_params)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                additional_params = {"exact_title_match": True}
                _data = {"title": "AAA BBB"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0 = {'term': {'title': 'AAA BBB'}}
                    expect_1 = {'term': {'alternative': 'AAA BBB'}}
                    expect = {
                        'bool': {
                            'should':[expect_0, expect_1],
                            'minimum_should_match': 1
                        }
                    }
                    search_query, _ = default_search_factory(self=None, search=search, additional_params=additional_params)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                _data = {"title": "AAA BBB OR CCC"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0['term']['title'] = 'AAA BBB OR CCC'
                    expect_1['term']['alternative'] = 'AAA BBB OR CCC'
                    search_query, _ = default_search_factory(self=None, search=search, additional_params=additional_params)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                # _get_keywords_query test (type)
                _data = {"type": "0,data paper"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0 = {'match': {'type.raw': {'operator': 'and', 'query': ''}}}
                    expect_1 = copy.deepcopy(expect_0)
                    expect_0['match']['type.raw']['query'] = "conference paper"
                    expect_1['match']['type.raw']['query'] = "data paper"
                    expect = {
                        'bool': {
                            'should':[expect_0, expect_1],
                        }
                    }
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                # _get_keywords_query test (wid)
                _data = {"wid": "AAA"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect = {'bool': {'should': [{'match': {'creator.nameIdentifier': 'AAA'}}]}}
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]
                _data = {"wid": "AAA,BBB"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    search_query, _ = default_search_factory(self=None, search=search)
                    expect['bool']['should'].append({'match': {'creator.nameIdentifier': 'BBB'}})
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                # _get_nested_query test (id: selfDOI)
                NESTED_QUERY_TEMPLATE = {
                    "nested": {
                        "path": "",
                        "query": {"bool": ""}
                    }
                }
                _data = {"id": "AAA BBB", "id_attr": "selfDOI"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_1 = {
                        "match": {
                            "identifierRegistration.value": {
                                "operator": "and",
                                "query": "AAA BBB"
                            }
                        }
                    }
                    nested_query = copy.deepcopy(NESTED_QUERY_TEMPLATE)
                    nested_query["nested"]["path"] = "identifierRegistration"
                    nested_query["nested"]["query"]["bool"] = {"must":[expect_1]}
                    expect = {"bool": {"should":[nested_query]}}

                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                _data = {"id": "AAA BBB OR CCC", "id_attr": "selfDOI"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_2 = copy.deepcopy(expect_1)
                    expect_2["match"]["identifierRegistration.value"]["query"] = "CCC"

                    nested_query = copy.deepcopy(NESTED_QUERY_TEMPLATE)
                    nested_query["nested"]["path"] = "identifierRegistration"
                    nested_query["nested"]["query"]["bool"] = {
                        "should": [expect_1, expect_2],
                        "minimum_should_match": 1
                    }
                    expect = {"bool": {"should":[nested_query]}}

                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                # _get_nested_query test (id: NCID)
                _data = {"id": "AAA BBB", "id_attr": "NCID"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0_1 = {
                        "match": {
                            "relation.relatedIdentifier.value": {
                                "operator": "and",
                                "query": "AAA BBB"
                            }
                        }
                    }
                    expect_0_0 = {"term": {"relation.relatedIdentifier.identifierType": "NCID"}}
                    expect_1_1 = {
                        "match": {
                            "sourceIdentifier.value": {
                                "operator": "and",
                                "query": "AAA BBB"
                            }
                        }
                    }
                    expect_1_0 = { "term": { "sourceIdentifier.identifierType": "NCID" } }

                    expect_0 = copy.deepcopy(NESTED_QUERY_TEMPLATE)
                    expect_0["nested"]["path"] = "relation.relatedIdentifier"
                    expect_0["nested"]["query"]["bool"] = { "must": [expect_0_1, expect_0_0] }
                    expect_1 = copy.deepcopy(NESTED_QUERY_TEMPLATE)
                    expect_1["nested"]["path"] = "sourceIdentifier"
                    expect_1["nested"]["query"]["bool"] = { "must": [expect_1_1, expect_1_0] }

                    expect = {"bool": {"should": [expect_0, expect_1]}}

                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                _data = {"id": "AAA BBB OR CCC", "id_attr": "NCID"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0_2 = copy.deepcopy(expect_0_1)
                    expect_1_2 = copy.deepcopy(expect_1_1)
                    expect_0_2["match"]["relation.relatedIdentifier.value"]["query"] = "CCC"
                    expect_1_2["match"]["sourceIdentifier.value"]["query"] = "CCC"

                    expect_0 = copy.deepcopy(NESTED_QUERY_TEMPLATE)
                    expect_0["nested"]["path"] = "relation.relatedIdentifier"
                    expect_0["nested"]["query"]["bool"] = {
                        "must": [expect_0_0],
                        "should": [expect_0_1, expect_0_2],
                        "minimum_should_match": 1
                    }
                    expect_1 = copy.deepcopy(NESTED_QUERY_TEMPLATE)
                    expect_1["nested"]["path"] = "sourceIdentifier"
                    expect_1["nested"]["query"]["bool"] = {
                        "must": [expect_1_0],
                        "should": [expect_1_1, expect_1_2],
                        "minimum_should_match": 1
                    }

                    expect = {"bool": {"should": [expect_0, expect_1]}}

                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                # _get_nested_query test (license)
                _data = {"license": "license_0"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0= {'terms': {'content.licensetype.raw': ['license_0']}}
                    nested_query = copy.deepcopy(NESTED_QUERY_TEMPLATE)
                    nested_query["nested"]["path"] = "content"
                    nested_query["nested"]["query"] = { "bool": { "must": [ expect_0 ] } }
                    expect = { "bool": { "should": [ nested_query ] }}

                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                _data = {"license": "license_0,license_1"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0= {'terms': {'content.licensetype.raw': ['license_0','license_1']}}
                    nested_query = copy.deepcopy(NESTED_QUERY_TEMPLATE)
                    nested_query["nested"]["path"] = "content"
                    nested_query["nested"]["query"] = { "bool": { "must": [ expect_0 ] } }
                    expect = { "bool": { "should": [ nested_query ] }}

                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                _data = {"license": "0"}
                orig_search_keywords_dict = copy.deepcopy(WEKO_SEARCH_KEYWORDS_DICT)
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['nested'] = {
                        "license": ("content", {"license": ({"content.licensetype.raw": ["license_0"]})}) }
                    expect_0= {'terms': {'content.licensetype.raw': ['license_0']}}
                    expect_1 = {
                        'multi_match': {
                            'query': '0',
                            'type': 'most_fields',
                            'minimum_should_match': '75%',
                            'operator': 'and',
                            'fields': ['content.value']
                        }
                    }
                    nested_query = copy.deepcopy(NESTED_QUERY_TEMPLATE)
                    nested_query["nested"]["path"] = "content"
                    nested_query["nested"]["query"] = {"bool": { "must": [ expect_1, expect_0 ] } }
                    expect = { "bool": { "should": [nested_query] }}

                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]
                app.config['WEKO_SEARCH_KEYWORDS_DICT'] = orig_search_keywords_dict

                # _get_text_query test (text1)
                _data = {"text1": "AAA BBB"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect = {'match': {'text1': {'operator': 'and', 'query': ''}}}
                    expect['match']['text1']['query'] = "AAA BBB"
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]
                _data = {"text1": "AAA BBB OR CCC"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0 = copy.deepcopy(expect)
                    expect_1 = copy.deepcopy(expect)
                    expect_0['match']['text1']['query'] = "AAA BBB"
                    expect_1['match']['text1']['query'] = "CCC"
                    expect = {
                        'bool': {
                            'should':[expect_0, expect_1],
                            'minimum_should_match': 1
                        }
                    }
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                # _get_file_content_query test
                _data = {"q": "AAA BBB", "search_type": WEKO_SEARCH_TYPE_DICT["FULL_TEXT"]}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0_0 = {
                        'multi_match': {
                            'query': 'AAA BBB',
                            'operator': 'and',
                            'fields': ['content.attachment.content']
                        }
                    }
                    expect_0 = {
                        'nested': {'query': expect_0_0, 'path': 'content'}
                    }
                    expect_1 = {
                        'query_string': {
                            'query': 'AAA BBB',
                            'default_operator': 'and',
                            'fields': ['search_*', 'search_*.ja']
                        }
                    }
                    expect = {
                        'bool': {'should':[expect_0, expect_1]}
                    }
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]

                _data = {"q": "AAA BBB OR CCC", "search_type": WEKO_SEARCH_TYPE_DICT["FULL_TEXT"]}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    expect_0_0_1 = copy.deepcopy(expect_0_0)
                    expect_0_0_2 = copy.deepcopy(expect_0_0)
                    expect_0_0_2['multi_match']['query'] = 'CCC'
                    expect_0_0 = {
                        'bool': {
                            'should':[expect_0_0_1, expect_0_0_2],
                            'minimum_should_match': 1
                        }
                    }
                    expect_0 = {
                        'nested': {'query': expect_0_0, 'path': 'content'}
                    }
                    expect_1['query_string']['query'] = 'AAA BBB OR CCC'
                    expect = {
                        'bool': {'should':[expect_0, expect_1]}
                    }
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1, expect]


# def default_search_factory(self, search, query_parser=None, search_type=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_default_search_factory_no_queries -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_default_search_factory_no_queries(app, users, communities):

    with app.test_client() as client:
        login_user_via_session(client, email=users[3]["email"])
        search = RecordsSearch()
        app.config['WEKO_SEARCH_KEYWORDS_DICT'] = WEKO_SEARCH_KEYWORDS_DICT
        app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS
        mock_searchperm = MagicMock(side_effect=MockSearchPerm)
        with patch('weko_search_ui.query.search_permission', mock_searchperm):
            with patch('invenio_records_rest.facets.default_facets_factory', side_effect=lambda x,y: (x, MultiDict([]))):

                EXPECT0 = {'bool': {'should': [{'bool': {'must': [{'terms': {'publish_status': ['0', '1']}}, {'match': {'weko_creator_id': None}}]}},
                                                {'bool': {'must': [{'terms': {'publish_status': ['0', '1']}}, {'terms': {'weko_shared_ids': [None]}}]}},
                                                {'bool': {'must': [{'terms': {'publish_status': ['0']}},
                                                    {'range': {'publish_date': {'lte': 'now/d', 'time_zone': 'UTC'}}}]}}],
                    'must': [{'terms': {'path': []}}]}}
                EXPECT1 = {'bool': {'must': [{'match': {'relation_version_is_last': 'true'}}]}}

                # _get_keywords_query test (type)
                _data = {"type": "100,AAA"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]

                orig_search_keywords_dict = copy.deepcopy(WEKO_SEARCH_KEYWORDS_DICT)
                _data = {"type": "0,data paper"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['string'] = {"type": {"type.raw": True}}
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]

                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['string'] = {"type": True}
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]
                app.config['WEKO_SEARCH_KEYWORDS_DICT'] = orig_search_keywords_dict

                # _get_keywords_query test (wid)
                kv = MagicMock()
                kv.split = lambda x : []
                _data = {"wid": ""}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    with patch('weko_search_ui.query.request.values.to_dict', side_effect=lambda : {"wid": kv} ):
                        search_query, _ = default_search_factory(self=None, search=search)
                        assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]

                # _get_nested_query test (id)
                _data = {"id": "AAA BBB"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]

                _data = {"id_attr": "NCID"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]

                orig_search_keywords_dict = copy.deepcopy(WEKO_SEARCH_KEYWORDS_DICT)
                _data = {"id": "AAA BBB", "id_attr": "NCID"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['nested'] = {"id": ("", {"id_attr": {"NCID": True} } )}
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]

                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['nested'] = {"id": ("", {"id_attr": {"NCID": [True] } } )}
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]

                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['nested'] = {"id": True}
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]
                app.config['WEKO_SEARCH_KEYWORDS_DICT'] = orig_search_keywords_dict

                # _get_nested_query test (license)
                orig_search_keywords_dict = copy.deepcopy(WEKO_SEARCH_KEYWORDS_DICT)
                _data = {"license": "1"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['nested'] = {"license": ("content", {"license": ({"content.licensetype.raw": ["CC0"]})}) }
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]

                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['nested'] = {"license": ("content", {"license": ({"content.licensetype.raw": ""})}) }
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]

                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['nested'] = {"license": ("content", {"license": ({"licensetype.raw": ""})}) }
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]

                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['nested'] = {"license": ("content", {"license": True}) }
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]
                app.config['WEKO_SEARCH_KEYWORDS_DICT'] = orig_search_keywords_dict

                # _get_text_query test (text1)
                orig_search_keywords_dict = copy.deepcopy(WEKO_SEARCH_KEYWORDS_DICT)
                _data = {"text1": "AAA BBB"}
                with app.test_request_context(headers=[('Accept-Language','en')], data=_data):
                    app.config['WEKO_SEARCH_KEYWORDS_DICT']['text'] = {"text1": True}
                    search_query, _ = default_search_factory(self=None, search=search)
                    assert search_query.query().to_dict()['query']['bool']['filter'][0]['bool']['must'] == [EXPECT0, EXPECT1]
                app.config['WEKO_SEARCH_KEYWORDS_DICT'] = orig_search_keywords_dict


# def item_path_search_factory(self, search, index_id=None):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_item_path_search_factory -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_item_path_search_factory(app, users, indices):
    search = RecordsSearch()
    app.config['WEKO_SEARCH_TYPE_INDEX'] = 'index'
    app.config['OAISERVER_ES_MAX_CLAUSE_COUNT'] = 1
    app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            with patch("weko_search_ui.query.get_item_type_aggs", return_value={}):
                mock_searchperm = MagicMock(side_effect=MockSearchPerm)
                with patch('weko_search_ui.query.search_permission', mock_searchperm):
                    res = item_path_search_factory(self=None, search=search, index_id=33)
                    assert res
                    _rv = ([Bool(must=[Terms(path=[])], should=[Match(weko_creator_id='5'), Terms(weko_shared_ids=['5']), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['3', '4', '5'])
                    with patch('weko_search_ui.query.get_permission_filter', return_value=_rv):
                        res = item_path_search_factory(self=None, search=search, index_id=None)
                        assert res
                        _rv = ([Bool(must=[Terms(path=[])], should=[Match(weko_creator_id='5'), Match(weko_shared_id='5'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['3', '4', '5'])
                        with patch('weko_search_ui.query.get_permission_filter', return_value=_rv):
                            res = item_path_search_factory(self=None, search=search, index_id=None)
                            assert res

    with patch("flask_login.utils._get_user",return_value=users[3]["obj"]):
        url = "/test?page=1&size=20&sort=controlnumber&search_type=2&q=3"
        with app.test_request_context(url):
            mock_searchperm = MagicMock(side_effect=MockSearchPerm)
            with patch("weko_search_ui.query.search_permission",mock_searchperm):
                with patch("weko_search_ui.query.get_item_type_aggs",return_value={}):
                    with patch("weko_search_ui.query.Indexes.get_browsing_tree_paths",return_value=["33","33/44"]):
                        with patch("weko_search_ui.query.Indexes.get_index_count",return_value=2):
                            # len(child_list) <= 1000
                            child_list = [str(i) for i in range(500)]
                            with patch("weko_search_ui.query.Indexes.get_child_list_recursive",return_value=child_list):
                                res = item_path_search_factory(self=None,search=search,index_id=33)
                                query_dict = (res[0].query()).to_dict()
                                # post_filter must contain path terms and permission filter
                                pf_must = query_dict["post_filter"]["bool"]["must"]
                                assert any("path" in list(m.get("terms",{}).keys()) for m in pf_must)
                                # aggs use single 'path' key (not split) for <= 1000 items
                                assert "path" in query_dict["aggs"]
                                assert "path_0" not in query_dict["aggs"]
                            # len(child_list) > 1000
                            child_list = [str(i) for i in range(2345)]
                            with patch("weko_search_ui.query.Indexes.get_child_list_recursive",return_value=child_list):
                                res = item_path_search_factory(self=None,search=search,index_id=33)
                                query_dict = (res[0].query()).to_dict()
                                # aggs are split into path_0, path_1, path_2 for > 1000 items
                                assert "path_0" in query_dict["aggs"]
                                assert "path_1" in query_dict["aggs"]
                                assert "path_2" in query_dict["aggs"]
                                assert "path" not in query_dict["aggs"]


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

    with patch('weko_search_ui.query.request.values.get', side_effect=lambda x: 1 if x=='q' else None ):
        with patch('weko_search_ui.query.item_path_search_factory', return_value = (search, '')):
            res = opensearch_factory(self=None, search=search)
            assert res

    # exact title match parameter test
    with patch('weko_search_ui.query.request.args.get', side_effect=['true', 'false', None]):
        with patch('weko_search_ui.query.default_search_factory', return_value = (search, '')) as mock_search_factory:
            res = opensearch_factory(self=None, search=search)
            mock_search_factory.assert_called_with(
                None, search, None, search_type=WEKO_SEARCH_TYPE_DICT["FULL_TEXT"], additional_params={'exact_title_match': True})
            assert res

            res = opensearch_factory(self=None, search=search)
            mock_search_factory.assert_called_with(
                None, search, None, search_type=WEKO_SEARCH_TYPE_DICT["FULL_TEXT"], additional_params={'exact_title_match': False})
            assert res

            res = opensearch_factory(self=None, search=search)
            mock_search_factory.assert_called_with(
                None, search, None, search_type=WEKO_SEARCH_TYPE_DICT["FULL_TEXT"], additional_params={'exact_title_match': False})
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


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_function_issue35902 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
@pytest.mark.skip(reason="production bool query structure changed - test needs comprehensive update")
def test_function_issue35902(app, users, communities, mocker):
    with app.test_client() as client:
        login_user_via_session(client, email=users[3]["email"])
        search = RecordsSearch()
        app.config['WEKO_SEARCH_KEYWORDS_DICT'] = WEKO_SEARCH_KEYWORDS_DICT
        app.config['WEKO_ADMIN_MANAGEMENT_OPTIONS'] = WEKO_ADMIN_MANAGEMENT_OPTIONS
        mocker.patch("weko_search_ui.query.search_permission",side_effect=MockSearchPerm)
        mocker.patch("weko_search_ui.permissions.search_permission",side_effect=MockSearchPerm)
        test = [
            {"bool":{"should":[{"terms":{"weko_creator_id":["1"]}},{"terms":{"weko_shared_ids":[None]}},{"bool":{"must":[{"terms":{"publish_status":["0"]}},{"range":{"publish_date":{"lte":"now/d","time_zone":"UTC"}}}]}}]}},
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


# def _split_text_by_or(text):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_query.py::test_split_text_by_or -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_split_text_by_or():
    assert _split_text_by_or("") == [""]
    assert _split_text_by_or(" ") == [""]
    assert _split_text_by_or(None) == []
    assert _split_text_by_or("AAA or BBB") == ["AAA or BBB"]
    assert _split_text_by_or("AAA OR　BBB | CCC") == ["AAA", "BBB", "CCC"]
    assert _split_text_by_or("AAA OR OR BBB") == ["AAA", "", "BBB"]
    assert _split_text_by_or("OR AAA |") == ["OR AAA |"]
