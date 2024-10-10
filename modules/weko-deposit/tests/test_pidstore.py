
from unittest import mock
from unittest.mock import patch
import uuid

from sqlalchemy.exc import SQLAlchemyError

from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.models import PersistentIdentifier,RecordIdentifier,PIDStatus

from weko_deposit.pidstore import weko_deposit_minter,weko_deposit_fetcher,get_latest_version_id,get_record_identifier,get_record_identifier,get_record_without_version

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_pidstore.py -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp


# def weko_deposit_minter(record_uuid, data, recid=None):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_pidstore.py::test_weko_deposit_minter -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_weko_deposit_minter(app,db):

    with patch('weko_deposit.pidstore.weko_logger') as mock_logger:

      # not recid
      rec_id = uuid.uuid4()
      data = {
        "recid": "1",
        "title": ["test item1"],
      }
      result = weko_deposit_minter(rec_id,data)
      assert result.object_uuid == rec_id

      assert mock_logger.call_count == 2
      mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='recid is None')
      mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
      mock_logger.reset_mock()

      # exist recid, recid is int
      rec_id = uuid.uuid4()
      data = {
        "recid": "2",
        "title": ["test item2"],
      }
      result = weko_deposit_minter(rec_id,data,recid=2)
      assert result.object_uuid == rec_id

      assert mock_logger.call_count == 3
      mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='recid is not None')
      mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='recid is int')
      mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
      mock_logger.reset_mock()

      # exist recid, recid is not int
      rec_id = uuid.uuid4()
      data = {
        "recid": "3",
        "title": ["test item3"],
      }
      result = weko_deposit_minter(rec_id,data,recid="3")
      assert result.object_uuid == rec_id

      assert mock_logger.call_count == 2
      mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='recid is not None')
      mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)

# def weko_deposit_fetcher(record_uuid, data):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_pidstore.py::test_weko_deposit_fetcher -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_weko_deposit_fetcher(app):

    with patch('weko_deposit.pidstore.weko_logger') as mock_logger:

      # exist pid_value
      record_uuid = uuid.uuid4()
      data = {
        "recid": "1",
        "title": ["test item1"],
        "_deposit": {
          "id": "1",
          "pid": { "type": "depid", "value": "1", "revision_id": 0 },
          "owner": "1",
          "owners": [1],
          "status": "published",
          "created_by": 1,
          "owners_ext": {
            "email": "wekosoftware@nii.ac.jp",
            "username": "",
            "displayname": ""
          }
        }
      }
      result = weko_deposit_fetcher(record_uuid, data)
      assert result.provider == None
      assert result.pid_type == "depid"
      assert result.pid_value == "1"
      mock_logger.assert_called_once_with(key='WEKO_COMMON_RETURN_VALUE', value=result)
      mock_logger.reset_mock()

      # not exist pid_value
      record_uuid = uuid.uuid4()
      data = {
        "recid": "1",
        "title": ["test item1"],
        "_deposit": {
        }
      }
      result = weko_deposit_fetcher(record_uuid, data)
      assert result == None
      mock_logger.assert_called_once_with(key='WEKO_COMMON_RETURN_VALUE', value=None)


# def get_latest_version_id(recid):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_pidstore.py::test_get_latest_version_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_get_latest_version_id(app,db, location, records):
    pids = list()
    pids.append(PersistentIdentifier.create('recid', "1.0",object_type='rec', object_uuid=uuid.uuid4(),status="R"))
    pids.append(PersistentIdentifier.create('recid', "1.1",object_type='rec', object_uuid=uuid.uuid4(),status="R"))
    pids.append(PersistentIdentifier.create('recid', "1.2",object_type='rec', object_uuid=uuid.uuid4(),status="R"))
    db.session.add_all(pids)
    db.session.commit()

    result = get_latest_version_id("1")
    assert result == 3

    result = get_latest_version_id("1000")
    assert result == 1


# # def get_record_identifier(recid):
# # .tox/c1/bin/pytest --cov=weko_deposit tests/test_pidstore.py::test_get_record_identifier -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
# def test_get_record_identifier(app,db,es_records):
#     RecordIdentifier.next()
#     result = get_record_identifier("1")
#     assert result.recid == 1

#     result = get_record_identifier("not int")
#     assert result == None

# def get_record_identifier(recid):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_pidstore.py::TestGetRecordIdentifier -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_get_record_identifier(app, db, es_records):
    
    # exsit record
    recid = "1"
    record_id = RecordIdentifier(recid=1)

    with patch('weko_deposit.pidstore.RecordIdentifier.query') as mock_query:
        mock_query.filter_by.return_value.one_or_none.return_value = record_id
        with patch('weko_deposit.pidstore.weko_logger') as mock_logger:
            mock_logger.return_value = None

            result = get_record_identifier(recid)

            mock_query.filter_by.assert_called_once_with(recid=1)
            mock_logger.assert_called_once_with(key='WEKO_COMMON_RETURN_VALUE', value=record_id)
            assert result.recid == 1

    # not exist record
    recid = "2"

    with patch('weko_deposit.pidstore.RecordIdentifier.query') as mock_query:
        mock_query.filter_by.return_value.one_or_none.return_value = None
        with patch('weko_deposit.pidstore.weko_logger') as mock_logger:
            mock_logger.return_value = None

            result = get_record_identifier(recid)

            mock_query.filter_by.assert_called_once_with(recid=2)
            mock_logger.assert_called_once_with(key='WEKO_COMMON_RETURN_VALUE', value=None)
            assert result == None

    # recid not int(raise ValueError)
    recid = "not int"

    with patch('weko_deposit.pidstore.RecordIdentifier.query') as mock_query:
        mock_query.filter_by.return_value.one_or_none.return_value = None
        with patch('weko_deposit.pidstore.weko_logger') as mock_logger:
            mock_logger.return_value = None

            result = get_record_identifier(recid)

            mock_query.filter_by.assert_not_called()
            assert mock_logger.call_count == 2
            mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=None)
            assert result == None

    # raise SQLAlchemyError
    recid = "1"
    ex = SQLAlchemyError('test error')

    with patch('weko_deposit.pidstore.RecordIdentifier.query') as mock_query:
        mock_query.filter_by.return_value.one_or_none.side_effect = ex
        with patch('weko_deposit.pidstore.weko_logger') as mock_logger:
            mock_logger.return_value = None

            result = get_record_identifier(recid)

            mock_query.filter_by.assert_called_once_with(recid=1)
            assert mock_logger.call_count == 2
            mock_logger.assert_any_call(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=None)
            assert result == None

# def get_record_without_version(pid):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_pidstore.py::test_get_record_without_version -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_get_record_without_version(app, db):
    obj_p1 = PersistentIdentifier.create('parent', "parent:1",object_type='rec', object_uuid=uuid.uuid4(),status=PIDStatus.REGISTERED)
    obj_c1 = PersistentIdentifier.create('recid', "1.1",object_type='rec', object_uuid=uuid.uuid4(),status=PIDStatus.REGISTERED)
    obj_without_ver = PersistentIdentifier.create('recid', "1",object_type='rec', object_uuid=uuid.uuid4(),status=PIDStatus.REGISTERED)
    rel1 = PIDRelation.create(obj_p1,obj_c1,2,0)
    rel2 = PIDRelation.create(obj_p1,obj_without_ver,2,0)
    db.session.add(rel1)
    db.session.add(rel2)
    other_obj = PersistentIdentifier.create('recid', "2",object_type='rec', object_uuid=uuid.uuid4(),status=PIDStatus.REGISTERED)
    db.session.commit()

    with patch('weko_deposit.pidstore.weko_logger') as mock_logger:
      
      # not exist parent_relations
      result = get_record_without_version(other_obj)
      assert result == None
      mock_logger.assert_called_once_with(key='WEKO_COMMON_RETURN_VALUE', value=None)
      mock_logger.reset_mock()

      # parent_pid is not None
      result = get_record_without_version(obj_c1)
      assert result == obj_without_ver
      mock_logger.call_count == 3
      mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='parent_relations is not None')
      mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='parent_pid is not None')
      mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=obj_without_ver)
      mock_logger.reset_mock()

      # parent_pid is None
      with patch('weko_deposit.pidstore.PersistentIdentifier.query') as mock_query:
        mock_query.filter_by.return_value.one_or_none.return_value = None
        result = get_record_without_version(obj_c1)
        assert result == None
        mock_logger.call_count == 2
        mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='parent_relations is not None')
        mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=None)

