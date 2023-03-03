
from mock import patch
from weko_index_tree.models import Index

from invenio_oaiharvester.models import OAIHarvestConfig

from invenio_oaiharvester.views import _app, dbsession_clean

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp

def test_dbsession_clean(app,db):
    # exist exception
    config1 = OAIHarvestConfig(id=1,baseurl="http://test1.org",name="test_config1",setspecs="test")
    db.session.add(config1)
    dbsession_clean(None)
    assert OAIHarvestConfig.query.filter_by(id=1).first().baseurl=="http://test1.org"
    
    # raise exception
    config2 = OAIHarvestConfig(id=2,baseurl="http://test2.org",name="test_config2",setspecs="test")
    db.session.add(config2)
    with patch("invenio_oaiharvester.views.db.session.commit",side_effect=Exception):
        dbsession_clean(None)
        assert OAIHarvestConfig.query.filter_by(id=2).first() is None
    
    # not exist exception
    config3 = OAIHarvestConfig(id=3,baseurl="http://test3.org",name="test_config3",setspecs="test")
    db.session.add(config3)
    dbsession_clean(Exception)
    assert OAIHarvestConfig.query.filter_by(id=3).first() is None