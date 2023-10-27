# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp

from flask import url_for

# def display_robots_txt():
# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_views.py::test_display_robots_txt -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_display_robots_txt(client,db_sessionlifetime):
    url = url_for("weko_sitemap.display_robots_txt", _external=True)
    ret = client.get(url)
    assert ret.status_code==200
    
