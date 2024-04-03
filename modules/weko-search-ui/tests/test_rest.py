"""
/index/:post, get
"""
import json
import pytest
from mock import patch, MagicMock
from flask import current_app
from elasticsearch_dsl import response, Search
from redis import RedisError
from tests.conftest import json_data

from invenio_records_rest.errors import MaxResultWindowRESTError
from invenio_rest import ContentNegotiatedMethodView

from weko_records.api import ItemTypes
from weko_search_ui.rest import create_blueprint, IndexSearchResource, get_heading_info, GetFacetSearchConditions


def url(root, kwargs={}):
    args = ["{key}={value}".format(key=key, value=value) for key, value in kwargs.items()]
    url = "{root}?{param}".format(root=root, param="&".join(args)) if kwargs else root
    return url


class mock_path:
    def __init__(self, **data):
        self.pid = data.get("pid")
        self.cid = data.get("cid")
        self.path = data.get("path")
        self.name = data.get("name")
        self.name_en = data.get("name_en")
        self.lev = data.get("lev")
        self.public_state = data.get("public_state")
        self.public_date = data.get("public_date")
        self.comment = data.get("comment")
        self.browsing_role = data.get("browsing_role")
        self.browsing_group = data.get("browsing_group")
        self.harvest_public_state = data.get("harvest_public_state")

path1 = dict(
    pid=0,
    cid=1557820086539,
    path="1557820086539",
    name= '人文社会系 (Faculty of Humanities and Social Sciences)',
    name_en ='Faculty of Humanities and Social Sciences',
    lev = 1,
    public_state=True,
    public_date=None,
    comment="",
    browsing_role='3,-98,-99',
    browsing_group="",
    harvest_public_state=True
)
path2 = dict(
    pid=0,
    cid=1557819733276,
    path="1557819692844/1557819733276",
    name= '会議発表論文',
    name_en ='conference paper',
    lev = 1,
    public_state=True,
    public_date=None,
    comment="",
    browsing_role='3,-98,-99',
    browsing_group="",
    harvest_public_state=True,
)

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_IndexSearchResource_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
test_patterns =[
    ({},
     "facet_not_post_filters.json",
     {"self":"?page=1&size=20"},
     [[mock_path(**path1)]],
     "rd_result01_02_03_no_agp.json",
     "execute_result01_02_03_no_agp.json"
     ),
    ({},
     "facet.json",
     {"self":"?page=1&size=20"},
     BaseException,
     "rd_result01_02_03_BaseException.json",
     "execute_result01_02_03.json"
     ),
    ({"size":1,"page":2,"q":"1557820086539","Access":"open access"},
     "facet.json", 
     {"next":"?page=3&q=1557820086539&size=1","prev":"?page=1&q=1557820086539&size=1","self":"?page=2&q=1557820086539&size=1"},
     [[mock_path(**path2),mock_path(**path1)]], # path not in agp
     "rd_result01_02_03.json",
     "execute_result01_02_03.json")
    ]
@pytest.mark.parametrize("params, facet_file, links, paths, rd_file, execute", test_patterns)
def test_IndexSearchResource_get(client_rest, users, item_type, record, facet_search_setting, index, mock_es_execute, 
                                 params, facet_file, links, paths, rd_file, execute):
    sname = current_app.config["SERVER_NAME"]
    facet = json_data("tests/data/search/"+facet_file)
    for l in links:
        links[l]="http://"+sname+"/index/"+links[l]
    with patch("weko_admin.utils.get_facet_search_query", return_value=facet):
        with patch("weko_search_ui.rest.Indexes.get_self_list",side_effect=paths):
            with patch("invenio_search.api.RecordsSearch.execute", return_value=mock_es_execute("tests/data/search/"+execute)):
                res = client_rest.get(url("/index/",params))
                result = json.loads(res.get_data(as_text=True))
                rd = json_data("tests/data/search/"+rd_file)
                rd["links"] = links
                assert result == rd

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_IndexSearchResource_get_Exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_IndexSearchResource_get_Exception(client_rest, db, users, item_type, db_records, facet_search_setting):
    sname = current_app.config["SERVER_NAME"]
    #from weko_index_tree.models import Index
    #datas = json_data("data/index.json")
    #indexes = list()
    #for index in datas:
    #    indexes.append(Index(**datas[index]))
    #with db.session.begin_nested():
    #    db.session.add_all(indexes)
    #db.session.commit()
    
    def dummy_response(data):
        if isinstance(data, str):
            data = json_data(data)
        dummy=response.Response(Search(), data)
        return dummy
    facet = json_data("data/search/facet.json")
    links = {"self":"?page=1&size=20"}
    for l in links:
        links[l]="http://"+sname+"/index/"+links[l]
    with patch("weko_admin.utils.get_facet_search_query", return_value=facet):
        with patch("weko_search_ui.rest.Indexes.get_self_list",side_effect=mock_path(**path1)):
            with patch("invenio_search.api.RecordsSearch.execute", return_value=dummy_response("data/search/execute_result01_02_03.json")):
                with patch("weko_search_ui.rest.get_heading_info", side_effect=Exception):
                    res = client_rest.get(url("/index/",{"self":"?page=1&size=20"}))
                    result = json.loads(res.get_data(as_text=True))
                    rd = json_data("data/search/rd_result01_02_03_Exception.json")
                    rd["links"] = links
                    assert result == rd

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_IndexSearchResource_get_MaxResultWindowRESTError -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_IndexSearchResource_get_MaxResultWindowRESTError(client_rest,db_register2):
    #MaxResultWindowRESTError発生
    param = {"size":1000,"page":1000}
    with patch("weko_admin.utils.get_facet_search_query", return_value={}):
        res =  client_rest.get(url("/index/", param))
        assert res.status_code == 400

# def create_blueprint(app, endpoints):
def test_create_blueprint(i18n_app, app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        endpoints = app.config['WEKO_SEARCH_REST_ENDPOINTS']
        assert create_blueprint(app, endpoints)


# class IndexSearchResource(ContentNegotiatedMethodView):
# def __init__
# def get(self, **kwargs):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_IndexSearchResource_get -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_IndexSearchResource_get(i18n_app, users, client_request_args):
    total_hit_count = 30
    top_page = "http://test_server/index/?page=1&size=20"
    next_page = "http://test_server/index/?page=2&size=20"

    return_data_1 = MagicMock()
    return_data_1.path = ""
    return_data_1.name = "test"

    return_data_2 = MagicMock()
    return_data_2.path = "q"
    return_data_2.name = "test"

    with patch("invenio_pidstore.current_pidstore.fetchers", return_value=1):
    
        def search_class():
            search_class_data = MagicMock()

            return search_class_data

        def search_factory(x, y):
            def execute():
                def to_dict():
                    dict_1 = {
                        "hits": {
                            "total": total_hit_count,
                            "hits": [{
                                "_source": {
                                    "title": [1],
                                    "_comment": "test",
                                    "control_number": 1,
                                    "custom_sort": "custom_sort",
                                    "_item_metadata": {"item_type_id": 1}
                                }
                            }]
                        },
                        "aggregations": {
                            "path": {
                                "buckets": [{
                                    "key": "",
                                    "doc_count": 1,
                                    "no_available": {
                                        "doc_count": 1
                                    },
                                    "date_range": {
                                        "available": {
                                            "buckets": [{}]
                                        }
                                    }
                                }]
                            }
                        }
                    }

                    return dict_1

                data_3 = MagicMock()
                data_3.hits = MagicMock()
                data_3.hits.total = 30
                data_3.to_dict = to_dict

                return data_3

            data_1 = MagicMock()
            data_1.execute = execute

            data_2 = MagicMock()

            return (data_1, data_2)

        def make_response(pid_fetcher, search_result, links, item_links_factory):
            return (pid_fetcher, search_result, links, item_links_factory)
        

        ctx = {
            "pid_fetcher": "",
            "max_result_window": 10000,
            "search_class": search_class,
            "search_factory": search_factory,
            "links_factory": "test",
            "make_response": make_response
        }

        test = IndexSearchResource(
            ctx=ctx,
            search_serializers=None, 
            record_serializers=None, 
            default_media_type=None
        )

        with patch("weko_index_tree.api.Indexes.get_index", return_value=MagicMock()):
            with patch("weko_index_tree.api.Indexes.get_self_list", return_value=[return_data_1]):
                assert isinstance(test.get(), tuple)
                assert isinstance(test.get()[1], dict)
                assert test.get()[1]["hits"]["total"] == total_hit_count
                assert test.get()[2]["self"] == top_page
                assert test.get()[2]["next"] == next_page

            with patch("weko_index_tree.api.Indexes.get_self_list", return_value=[return_data_2]):
                assert isinstance(test.get(), tuple)
                assert isinstance(test.get()[1], dict)
                assert test.get()[1]["hits"]["total"] == total_hit_count
                assert test.get()[2]["self"] == top_page
                assert test.get()[2]["next"] == next_page

# def get_heading_info(data, lang, item_type):
def test_get_heading_info(i18n_app):
    subitem_heading_banner_headline = "test1"
    subitem_heading_headline = "test2"

    data_1 = {
        "_source": {
            "_item_metadata": {
                "prop1": {
                    "attribute_value_mlt": [
                        {
                            "subitem_heading_banner_headline": subitem_heading_banner_headline,
                            "subitem_heading_headline": subitem_heading_headline,
                            "subitem_heading_language": "en"
                        },
                        {
                            "subitem_heading_banner_headline": subitem_heading_banner_headline,
                            "subitem_heading_headline": subitem_heading_headline,
                            "subitem_heading_language": "en"
                        },
                    ]
                }
            }
        }
    }

    data_2 = MagicMock()
    data_2.schema = {
        "properties": {
            "prop1": {
                "properties": ["subitem_heading_banner_headline"],
                "type": "object"
            },
        }
    }

    data_3 = MagicMock()
    data_3.schema = {
        "properties": {
            "prop1": {
                "items": {"properties": ["subitem_heading_banner_headline"]},
                "type": "array"
            },
        }
    }

    assert subitem_heading_banner_headline in get_heading_info(data_1, "en", data_2)
    assert subitem_heading_headline in get_heading_info(data_1, "en", data_2)

    data_1["_source"]["_item_metadata"]["prop1"]["attribute_value_mlt"] = [{
        "subitem_heading_banner_headline": subitem_heading_banner_headline,
        "subitem_heading_headline": subitem_heading_headline,
        "subitem_heading_language": "en"
    }]

    assert subitem_heading_banner_headline in get_heading_info(data_1, "en", data_3)
    assert subitem_heading_headline in get_heading_info(data_1, "en", data_3)

    data_1["_source"]["_item_metadata"] = {}

    assert not subitem_heading_banner_headline in get_heading_info(data_1, "en", data_3)
    assert not subitem_heading_headline in get_heading_info(data_1, "en", data_3)

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get(client_rest, facet_test_data):
    endpoint = "/facet-search/condition"

    # no require params : key
    api_url = url(endpoint,{"search_type":0})
    res = client_rest.get(api_url)
    assert res.status_code==400
    # no require params : search_type
    api_url = url(endpoint,{"key":"Data%20Language,Access"})
    res = client_rest.get(api_url)
    assert res.status_code==400

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_index_search_check_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_index_search_check_key(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"

    sysadmin = users[3]["obj"]

    # Index Search
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            # active facet in key / search root index (q=0)
            api_url = url(endpoint,{"search_type":2, "key":"Data%20Language,Access", "q": 0})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert "Access" in res_data

            # deactive facet in key
            api_url = url(endpoint,{"search_type":2, "key":"Topic", "q": 0})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Topic" not in res_data
            
            # active facet not in key
            api_url = url(endpoint,{"search_type":2, "key":"testfacet001", "q": 0})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "testfacet001" not in res_data

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_index_search_root_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_index_search_root_index(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"

    sysadmin = users[3]["obj"]

    # search root index
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            # q=0
            api_url = url(endpoint,{"search_type":2, "key":"Data%20Language,Access", "q": 0})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert {'name': 'ja', 'count': 16} in res_data["Data Language"]
            assert {'name': 'en', 'count': 3} in res_data["Data Language"]
            assert {'name': 'fr', 'count': 3} in res_data["Data Language"]
            assert "Access" in res_data
            assert {'name': 'access_A', 'count': 16} in res_data["Access"]
            assert {'name': 'access_B', 'count': 3} in res_data["Access"]
            assert {'name': 'access_C', 'count': 3} in res_data["Access"]

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_index_search_exists_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_index_search_exists_index(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"

    sysadmin = users[3]["obj"]

    # search exists index
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            # q=1111
            api_url = url(endpoint,{"search_type":2, "key":"Data%20Language,Access", "q": 1111})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert {'name': 'ja', 'count': 4} in res_data["Data Language"]
            assert {'name': 'en', 'count': 3} in res_data["Data Language"]
            assert {'name': 'fr', 'count': 3} in res_data["Data Language"]
            assert "Access" in res_data
            assert {'name': 'access_A', 'count': 4} in res_data["Access"]
            assert {'name': 'access_B', 'count': 3} in res_data["Access"]
            assert {'name': 'access_C', 'count': 3} in res_data["Access"]
            
            # q=2222
            api_url = url(endpoint,{"search_type":2, "key":"Data%20Language,Access", "q": 2222})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert {'name': 'ja', 'count': 4} in res_data["Data Language"]
            assert "Access" in res_data
            assert {'name': 'access_A', 'count': 4} in res_data["Access"]

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_index_search_not_exists_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_index_search_not_exists_index(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"

    sysadmin = users[3]["obj"]

    # search not exists index
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            # q=9999
            api_url = url(endpoint,{"search_type":2, "key":"Data%20Language,Access", "q": 9999})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data and res_data["Data Language"] == []
            assert "Access" in res_data and res_data["Access"] == []

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_index_search_with_facet_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_index_search_with_facet_search(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"

    sysadmin = users[3]["obj"]

    # With facet search
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            # q=1111
            api_url = url(endpoint,{"search_type":2, "key":"Data%20Language,Access", "q": 1111, "Access":"access_A"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert {'name': 'ja', 'count': 4} in res_data["Data Language"]
            assert {'name': 'en', 'count': 3} in res_data["Data Language"]
            assert {'name': 'fr', 'count': 3} in res_data["Data Language"]
            assert "Access" in res_data
            assert {'name': 'access_A', 'count': 4} in res_data["Access"]
            assert {'name': 'access_B', 'count': 3} in res_data["Access"]
            assert {'name': 'access_C', 'count': 3} in res_data["Access"]

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_index_search_contributor -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_index_search_contributor(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"

    contributor = users[1]["obj"]

    # Contributor
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=contributor):
            # search root index (q=0)
            api_url = url(endpoint,{"search_type":2, "key":"Data%20Language,Access", "q": 0})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert {'name': 'ja', 'count': 4} in res_data["Data Language"]
            assert {'name': 'en', 'count': 3} in res_data["Data Language"]
            assert {'name': 'fr', 'count': 3} in res_data["Data Language"]
            assert "Access" in res_data
            assert {'name': 'access_A', 'count': 4} in res_data["Access"]
            assert {'name': 'access_B', 'count': 3} in res_data["Access"]
            assert {'name': 'access_C', 'count': 3} in res_data["Access"]

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_index_search_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_index_search_guest(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"

    # not login user
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        # search root index (q=0)
        api_url = url(endpoint,{"search_type":2, "key":"Data%20Language,Access", "q": 0})
        res = client_rest.get(api_url)
        res_data = json.loads(res.data)
        assert res.status_code==200
        assert "Data Language" in res_data
        assert {'name': 'ja', 'count': 4} in res_data["Data Language"]
        assert {'name': 'en', 'count': 3} in res_data["Data Language"]
        assert {'name': 'fr', 'count': 3} in res_data["Data Language"]
        assert "Access" in res_data
        assert {'name': 'access_A', 'count': 4} in res_data["Access"]
        assert {'name': 'access_B', 'count': 3} in res_data["Access"]
        assert {'name': 'access_C', 'count': 3} in res_data["Access"]


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_index_search_MaxResultWindowRESTError -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_index_search_MaxResultWindowRESTError(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"
    
    # MaxResultWindowRESTError
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        api_url = url(endpoint,{"search_type":2, "key":"Data%20Language,Access", "q": 1111, "page":500, "size":500})
        res = client_rest.get(api_url)
        assert res.status_code==400

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_keyword_search_check_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_keyword_search_check_key(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"
    
    sysadmin = users[3]["obj"]

    # Keyword Search
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            # active facet in key / q="item"
            api_url = url(endpoint,{"search_type":0, "key":"Data%20Language,Access", "q": "item"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert "Access" in res_data

            # deactive facet in key
            api_url = url(endpoint,{"search_type":0, "key":"Topic", "q": "item"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Topic" not in res_data

            # active facet not in key
            api_url = url(endpoint,{"search_type":0, "key":"testfacet001", "q": "item"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "testfacet001" not in res_data

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_keyword_search_hit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_keyword_search_hit(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"
    
    sysadmin = users[3]["obj"]

    # hit keyword: q=item17
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            api_url = url(endpoint,{"search_type":0, "key":"Data%20Language,Access", "q": "item17"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert res_data["Data Language"] == [{'name': 'en', 'count': 1}]
            assert "Access" in res_data
            assert res_data["Access"] == [{'name': 'access_B', 'count': 1}]

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_keyword_search_not_hit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_keyword_search_not_hit(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"
    
    sysadmin = users[3]["obj"]

    # not hit keyword: q=item99999
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            api_url = url(endpoint,{"search_type":0, "key":"Data%20Language,Access", "q": "item99999"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert res_data["Data Language"] == []
            assert "Access" in res_data
            assert res_data["Access"] == []

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_keyword_search_with_detail_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_keyword_search_with_detail_search(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"
    
    sysadmin = users[3]["obj"]

    # detail search
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            # subject=topic_B
            api_url = url(endpoint,{"search_type":0, "key":"Data%20Language,Access", "subject": "topic_B"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert {'name': 'en', 'count': 2} in res_data["Data Language"]
            assert {'name': 'fr', 'count': 1} in res_data["Data Language"]
            assert "Access" in res_data
            assert {'name': 'access_B', 'count': 1} in res_data["Access"]
            assert {'name': 'access_C', 'count': 2} in res_data["Access"]


# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_keyword_search_with_multi_detail_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_keyword_search_with_multi_detail_search(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"
    
    sysadmin = users[3]["obj"]

    # detail search
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            # subject=topic_B, des=description_A
            api_url = url(endpoint,{"search_type":0, "key":"Data%20Language,Access", "subject": "topic_B", "des": "description_A"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert res_data["Data Language"] == [{'name': 'fr', 'count': 1}]
            assert "Access" in res_data
            assert res_data["Access"] == [{'name': 'access_C', 'count': 1}]

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_keyword_search_sysadmin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_keyword_search_sysadmin(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"
    
    sysadmin = users[3]["obj"]

    # Contributor
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=sysadmin):
            # serch keyword: q="item"
            api_url = url(endpoint,{"search_type":1, "key":"Data%20Language,Access", "q": "item"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert {'name': 'ja', 'count': 16} in res_data["Data Language"]
            assert {'name': 'en', 'count': 3} in res_data["Data Language"]
            assert {'name': 'fr', 'count': 3} in res_data["Data Language"]
            assert "Access" in res_data
            assert {'name': 'access_A', 'count': 16} in res_data["Access"]
            assert {'name': 'access_B', 'count': 3} in res_data["Access"]
            assert {'name': 'access_C', 'count': 3} in res_data["Access"]

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_keyword_search_contributor -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_keyword_search_contributor(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"
    
    contributor = users[1]["obj"]

    # Contributor
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=contributor):
            # serch keyword: q="item"
            api_url = url(endpoint,{"search_type":1, "key":"Data%20Language,Access", "q": "item"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert {'name': 'ja', 'count': 1} in res_data["Data Language"]
            assert {'name': 'en', 'count': 3} in res_data["Data Language"]
            assert {'name': 'fr', 'count': 3} in res_data["Data Language"]
            assert "Access" in res_data
            assert {'name': 'access_A', 'count': 1} in res_data["Access"]
            assert {'name': 'access_B', 'count': 3} in res_data["Access"]
            assert {'name': 'access_C', 'count': 3} in res_data["Access"]

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_keyword_search_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_keyword_search_guest(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"

    # not login user
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        # serch keyword: q="item"
        api_url = url(endpoint,{"search_type":1, "key":"Data%20Language,Access", "q": "item"})
        res = client_rest.get(api_url)
        res_data = json.loads(res.data)
        assert res.status_code==200
        assert "Data Language" in res_data
        assert {'name': 'ja', 'count': 1} in res_data["Data Language"]
        assert {'name': 'en', 'count': 3} in res_data["Data Language"]
        assert {'name': 'fr', 'count': 3} in res_data["Data Language"]
        assert "Access" in res_data
        assert {'name': 'access_A', 'count': 1} in res_data["Access"]
        assert {'name': 'access_B', 'count': 3} in res_data["Access"]
        assert {'name': 'access_C', 'count': 3} in res_data["Access"]

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_GetFacetSearchConditions_get_keyword_search_with_facet_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_GetFacetSearchConditions_get_keyword_search_with_facet_search(users, client_rest, esindex, facet_test_data, facet_es_records):
    endpoint = "/facet-search/condition"
    
    contributor = users[1]["obj"]

    # facet search
    with patch("weko_search_ui.rest.db.session.remove", return_value=""):
        with patch("flask_login.utils._get_user", return_value=contributor):
            # q="item", "Access":"access_A"
            api_url = url(endpoint,{"search_type":0, "key":"Data%20Language,Access", "q": "item", "Access":"access_A"})
            res = client_rest.get(api_url)
            res_data = json.loads(res.data)
            assert res.status_code==200
            assert "Data Language" in res_data
            assert {'name': 'ja', 'count': 1} in res_data["Data Language"]
            assert {'name': 'en', 'count': 3} in res_data["Data Language"]
            assert {'name': 'fr', 'count': 3} in res_data["Data Language"]
            assert "Access" in res_data
            assert {'name': 'access_A', 'count': 1} in res_data["Access"]
            assert {'name': 'access_B', 'count': 3} in res_data["Access"]
            assert {'name': 'access_C', 'count': 3} in res_data["Access"]