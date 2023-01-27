"""
/index/:post, get
"""
import json
import pytest
from mock import patch, MagicMock
from flask import current_app
from elasticsearch_dsl import response, Search
from tests.conftest import json_data

from invenio_records_rest.errors import MaxResultWindowRESTError
from invenio_rest import ContentNegotiatedMethodView

from weko_records.api import ItemTypes
from weko_search_ui.rest import create_blueprint, IndexSearchResource, get_heading_info


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

def test_IndexSearchResource_get_facet(i18n_app,client_rest, db, users, item_type, facet_search_setting):
    i18n_app.config['WEKO_SEARCH_TYPE_INDEX'] = 'index'
    sname = current_app.config["SERVER_NAME"]
    def dummy_response(data):
        if isinstance(data, str):
            data = json_data(data)
        dummy=response.Response(Search(), data)
        return dummy
    param = {"page":"1",
            "size":"20",
            "sort":"wtl",
            "Data Language":"jpn",
            "Time Period(s)":"1899--2018",
            "Data Type":"公的統計: 集計データ、統計表",
            "is_facet_search":"true"}
    titleFacet={},{},{},{},{},{'Data Language': 'OR', 'Access': 'OR', 'Location': 'OR', 'Time Period(s)': 'AND', 'Topic': 'OR', 'Distributor': 'OR', 'Data Type': 'AND'}
    facets_mapping={'Data Language': 'language', 'Access': 'accessRights', 'Location': 'geoLocation.geoLocationPlace', 'Time Period(s)': 'temporal', 'Topic': 'subject.value', 'Distributor': 'contributor.contributorName', 'Data Type': 'description.value'}
    facet = json_data("data/search/facet_02.json")
    with patch("weko_admin.utils.get_facet_search_query", return_value=facet):
        with patch("weko_search_ui.rest.Indexes.get_self_list",side_effect=mock_path(**path1)):
            with patch("weko_admin.utils.get_title_facets", return_value=titleFacet):
                with patch("weko_admin.models.FacetSearchSetting.get_activated_facets_mapping", return_value=facets_mapping):
                    with patch("invenio_search.api.RecordsSearch.execute", return_value=dummy_response("data/search/execute_result01_02_03.json")):
                        res =  client_rest.get(url("/index/", param))
                        assert res.status_code == 200


# class IndexSearchResource(ContentNegotiatedMethodView):
# def __init__
# def get(self, **kwargs):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_rest.py::test_IndexSearchResource_get -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_IndexSearchResource_get(app,i18n_app, users, client_request_args):
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
