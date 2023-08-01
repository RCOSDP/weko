
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.proxies import current_oaiserver
from invenio_oaiserver.receivers import (
    OAIServerUpdater,
    after_update_oai_set,
    after_delete_oai_set,
    after_insert_oai_set
)
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_receivers.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp

# class OAIServerUpdater(object):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_receivers.py::test_OAIServerUpdater -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_OAIServerUpdater(app, db,mocker):
    mocker.patch("invenio_oaiserver.receivers.get_record_sets",return_value=["test1","test2"])
    updater = OAIServerUpdater()
    
    # not _oai.id
    record = {}
    updater(None,record)
    assert record == {}
    
    # old_sets != new_sets
    record = {"_oai":{"id":"test_id","sets":["value1","value2"]}}
    updater(None,record)
    assert len(record["_oai"]["sets"]) == 2
    assert "test2" in record["_oai"]["sets"]
    assert "test1" in record["_oai"]["sets"]
    
    # old_sets == new_sets
    record = {"_oai":{"id":"test_id","sets":["test1","test2"]}}
    updater(None,record)
    assert len(record["_oai"]["sets"]) == 2
    assert "test2" in record["_oai"]["sets"]
    assert "test1" in record["_oai"]["sets"]

# def after_insert_oai_set(mapper, connection, target):
def test_after_insert_oai_set(app,db,mocker):
    mocker.patch("invenio_oaiserver.receivers._new_percolator")
    mocker.patch("invenio_oaiserver.receivers.update_affected_records.delay")
    class Target:
        @property
        def search_pattern(self):
            return "test_search_pattern"
        @property
        def spec(self):
            return "test_spec"
    after_insert_oai_set(None,None,Target())

# def after_update_oai_set(mapper, connection, target):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_receivers.py::test_after_update_oai_set -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_after_update_oai_set(app,db,mocker):
    class Target:
        @property
        def search_pattern(self):
            return "test_search_pattern"
        @property
        def spec(self):
            return "test_spec"
    mocker.patch("invenio_oaiserver.receivers._delete_percolator")
    mocker.patch("invenio_oaiserver.receivers._new_percolator")
    mocker.patch("invenio_oaiserver.receivers.update_affected_records.delay")
    after_update_oai_set(None,None,Target())

# def after_delete_oai_set(mapper, connection, target):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_receivers.py::test_after_delete_oai_set -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_after_delete_oai_set(app,db,mocker):
    class Target:
        @property
        def search_pattern(self):
            return "test_search_pattern"
        @property
        def spec(self):
            return "test_spec"
    mocker.patch("invenio_oaiserver.receivers._delete_percolator")
    mocker.patch("invenio_oaiserver.receivers.update_affected_records.delay")
    after_delete_oai_set(None,None,Target())