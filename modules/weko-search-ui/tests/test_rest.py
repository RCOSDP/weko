"""
/index/:post, get
"""
import json
import pytest
from mock import patch

from invenio_records_rest.errors import MaxResultWindowRESTError
def test_IndexSearchResource_post_guest(client_rest, users):
    res = client_rest.post("/index/",
                           data=json.dumps({}),
                           content_type="application/json")
    assert res.status_code == 300

def data_from_jsonfile(filename):
    with open(filename, "r") as f:
        return json.load(f)
    
def test_IndexSearchResource_get(client_rest, users, item_type, record):
    from elasticsearch_dsl import response, Search
    import json
    sname = current_app.config["SERVER_NAME"]
    def url(root, kwargs={}):
        args = ["{key}={value}".format(key=key, value=value) for key, value in kwargs.items()]
        url = "{root}?{param}".format(root=root, param="&".join(args)) if kwargs else root
        print("url:{}".format(url))
        return url
    
    dummy_response = data_from_jsonfile("tests/data/search/execute_result01_02_03.json")
    for i, rec in enumerate(record):
        dummy_response["hits"]["hits"][i]["_id"] = str(rec["id"])
    res_execute = response.Response(Search(),dummy_response)
    facet = data_from_jsonfile("tests/data/search/facet.json")
    
    # MaxResultWindowRESTError発生
    # param = {"size":1000,"page":1000}
    # with patch("weko_admin.utils.get_facet_search_query", return_value={}):
    #     with pytest.raises(MaxResultWindowRESTError):
    #        client_rest.get(url("/index/", param))
    
    # facetなし
    with patch("weko_admin.utils.get_facet_search_query", return_value={}):
        with patch("invenio_search.api.RecordsSearch.execute", return_value=res_execute):
            
    
    # すべてのパラメータがなし
    with patch("weko_admin.utils.get_facet_search_query", return_value=facet):
        with patch("invenio_search.api.RecordsSearch.execute", return_value=res_execute):
            res = client_rest.get(url("/index/"))
            result = json.loads(res.get_data(as_text=True))
            rd = json_data("tests/data/search/rd_result01_02_03.json")
            rd["links"] = {"self":"http://"+sname+"/index/?page=1&size=20"}
            assert result == rd
    
    # すべてのパラメータあり
    param = {"size":1,"page":2,"q":"test"}
    with patch("weko_admin.utils.get_facet_search_query", return_value=facet):
        with patch("invenio_search.api.RecordsSearch.execute", return_value=res_execute):
            res = client_rest.get(url("/index/", param))
            result = json.loads(res.get_data(as_text=True))
            rd = data_from_jsonfile("tests/data/search/rd_result01_02_03.json")
            rd["links"] = {"next":"http://"+sname+"/index/?page=3&q=test&size=1",
                           "prev":"http://"+sname+"/index/?page=1&q=test&size=1",
                           "self":"http://"+sname+"/index/?page=2&q=test&size=1"}
            assert result == rd
    
