"""
/index/:post, get
"""
import json
import pytest
from mock import patch
from flask import current_app
from elasticsearch_dsl import response, Search
from tests.conftest import json_data

from invenio_records_rest.errors import MaxResultWindowRESTError
from invenio_rest import ContentNegotiatedMethodView

from weko_records.api import ItemTypes
from weko_search_ui.rest import create_blueprint, IndexSearchResource, get_heading_info


def test_IndexSearchResource_post_guest(app, client_rest, esindex, users, indices):
    app.config['WEKO_SEARCH_TYPE_INDEX'] = 'index'
    with patch('weko_search_ui.query.get_item_type_aggs', return_value={}):
        res = client_rest.get("/index/?page=1&size=20&sort=controlnumber&search_type=2&q=0&is_search=1")
        assert res.status_code==200
        res = client_rest.get("/index/?page=1&size=20&sort=controlnumber&search_type=2&q=0")
        assert res.status_code==200


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


def test_IndexSearchResource_get_Exception(client_rest, users, item_type, record, facet_search_setting, index, mock_es_execute):
    sname = current_app.config["SERVER_NAME"]

    facet = json_data("tests/data/search/facet.json")
    links = {"self":"?page=1&size=20"}
    for l in links:
        links[l]="http://"+sname+"/index/"+links[l]
    with patch("weko_admin.utils.get_facet_search_query", return_value=facet):
        with patch("weko_search_ui.rest.Indexes.get_self_list",side_effect=mock_path(**path1)):
            with patch("invenio_search.api.RecordsSearch.execute", return_value=mock_es_execute("tests/data/search/execute_result01_02_03.json")):
                with patch("weko_search_ui.rest.get_heading_info", side_effect=Exception):
                    res = client_rest.get(url("/index/",{"self":"?page=1&size=20"}))
                    result = json.loads(res.get_data(as_text=True))
                    rd = json_data("tests/data/search/rd_result01_02_03_Exception.json")
                    rd["links"] = links
                    assert result == rd


def test_IndexSearchResource_get_MaxResultWindowRESTError(client_rest):
    #MaxResultWindowRESTError発生
    param = {"size":1000,"page":1000}
    with patch("weko_admin.utils.get_facet_search_query", return_value={}):
        res =  client_rest.get(url("/index/", param))
        assert res.status_code == 404



# def create_blueprint(app, endpoints):
def test_create_blueprint(i18n_app, app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        endpoints = app.config['WEKO_SEARCH_REST_ENDPOINTS']
        assert create_blueprint(app, endpoints)


# class IndexSearchResource(ContentNegotiatedMethodView):
# def __init__
# def get(self, **kwargs):
# def test_IndexSearchResource_get(i18n_app, users, client_request_args):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         test = IndexSearchResource(ContentNegotiatedMethodView)
#         assert test.get()

# def get_heading_info(data, lang, item_type):
def test_get_heading_info(i18n_app, app, users, item_type, records):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        it = ItemTypes.get_by_id(1)
        assert not get_heading_info(records['hits']['hits'][0], "en", item_type=it)

        # Test 2
        # assert get_heading_info(records['hits']['hits'][0], "en", db_itemtype['item_type'])
