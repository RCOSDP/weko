"""
/index/:post, get
"""
import json

def test_IndexSearchResource_post_guest(client_rest, users):
    res = client_rest.post("/index/",
                           data=json.dumps({}),
                           content_type="application/json")
    assert res.status_code == 300