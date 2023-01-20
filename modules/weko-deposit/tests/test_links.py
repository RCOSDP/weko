
import uuid

from invenio_pidstore.models import PersistentIdentifier

from weko_deposit.links import links_factory,base_factory

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_links.py -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp

# def links_factory(pid, **kwargs):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_links.py::test_links_factory -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_links_factory(app, db,mocker):
    pids = list()
    pids.append(PersistentIdentifier.create('recid', "1.0",object_type='rec', object_uuid=uuid.uuid4(),status="R"))
    pids.append(PersistentIdentifier.create('recid', "1.1",object_type='rec', object_uuid=uuid.uuid4(),status="R"))
    pids.append(PersistentIdentifier.create('recid', "1.2",object_type='rec', object_uuid=uuid.uuid4(),status="R"))
    db.session.add_all(pids)
    db.session.commit()
    base = {
        "self":"/records/1.1"
    }
    new_url = {
        "index":"/api/deposits/redirect/1.1",
        "r":"/items/index/1.1",
        "iframe_tree":"/items/iframe/index/1.1",
        "iframe_tree_upgrade":"/items/iframe/index/1.3"
    }
    mocker.patch("weko_deposit.links.deposit_links_factory",return_value=base)
    mocker.patch("weko_deposit.links.base_factory",return_value=new_url)
    test = {
        "self":"/records/1.1",
        "index":"/api/deposits/redirect/1.1",
        "r":"/items/index/1.1",
        "iframe_tree":"/items/iframe/index/1.1",
        "iframe_tree_upgrade":"/items/iframe/index/1.3"
    }
    result = links_factory(pids[1])
    assert result == test


# def base_factory(pid, **kwargs):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_links.py -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_base_factory(app,db):
    pids = list()
    pids.append(PersistentIdentifier.create('recid', "1.0",object_type='rec', object_uuid=uuid.uuid4(),status="R"))
    pids.append(PersistentIdentifier.create('recid', "1.1",object_type='rec', object_uuid=uuid.uuid4(),status="R"))
    pids.append(PersistentIdentifier.create('recid', "1.2",object_type='rec', object_uuid=uuid.uuid4(),status="R"))
    db.session.add_all(pids)
    db.session.commit()
    test = {
        "index":"/api/deposits/redirect/1.1",
        "r":"/items/index/1.1",
        "iframe_tree":"/items/iframe/index/1.1",
        "iframe_tree_upgrade":"/items/iframe/index/1.3"
    }
    result = base_factory(pids[1])
    assert result == test