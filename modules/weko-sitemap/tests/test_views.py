# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp

from mock import patch
from flask import url_for, current_app
from weko_sitemap.views import dbsession_clean

# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp

# def display_robots_txt():
# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_views.py::test_display_robots_txt -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
def test_display_robots_txt(client,db_sessionlifetime):
    url = url_for("weko_sitemap.display_robots_txt", _external=True)
    ret = client.get(url)
    assert ret.status_code==200
    
    current_app.config.pop("WEKO_SITEMAP__ROBOT_TXT")
    ret = client.get(url)
    assert ret.status_code==200


# .tox/c1/bin/pytest --cov=weko_admin tests/test_views.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_dbsession_clean(app, db):
    from weko_records.models import ItemTypeName
    # exist exception
    itemtype_name1 = ItemTypeName(id=1,name="テスト1",has_site_license=True, is_active=True)
    db.session.add(itemtype_name1)
    dbsession_clean(None)
    assert ItemTypeName.query.filter_by(id=1).first().name == "テスト1"

    # raise Exception
    itemtype_name2 = ItemTypeName(id=2,name="テスト2",has_site_license=True, is_active=True)
    db.session.add(itemtype_name2)
    with patch("weko_items_autofill.views.db.session.commit",side_effect=Exception):
        dbsession_clean(None)
        assert ItemTypeName.query.filter_by(id=2).first() is None

    # not exist exception
    itemtype_name3 = ItemTypeName(id=3,name="テスト3",has_site_license=True, is_active=True)
    db.session.add(itemtype_name3)
    dbsession_clean(Exception)
    assert ItemTypeName.query.filter_by(id=3).first() is None