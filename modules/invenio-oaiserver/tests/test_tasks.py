
import uuid
import datetime
import pytest
from flask import current_app
from invenio_records.models import RecordMetadata
from invenio_files_rest.models import Location, ObjectVersion, Bucket
from invenio_oaiserver.models import OAISet
from mock import patch, MagicMock
from lxml import etree
from lxml.etree import Element, ElementTree, SubElement

from invenio_oaiserver.utils import datetime_to_datestamp
from invenio_oaiserver.tasks import _records_commit,update_records_sets, update_affected_records,\
    create_data, delete_data_json_data, get_data_json, create_data_json, get_create_file_location, \
    save_item_data, update_data_json_data
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_tasks.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp

NS_OAIPMH = 'http://www.openarchives.org/OAI/2.0/'
NS_OAIPMH_XSD = 'http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd'
NS_XSI = 'http://www.w3.org/2001/XMLSchema-instance'
NS_OAIDC = 'http://www.openarchives.org/OAI/2.0/oai_dc/'
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_JPCOAR = "https://irdb.nii.ac.jp/schema/jpcoar/1.0/"

NSMAP = {
    None: NS_OAIPMH,
}


# def _records_commit(record_ids):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_tasks.py::test_records_commit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_records_commit(app,records):
    res = RecordMetadata.query.all()
    ids = [rec.id for rec in res]
    _records_commit(ids)


# def update_records_sets(record_ids):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_tasks.py::test_update_records_sets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_update_records_sets(app,records, mocker):
    mocker.patch("invenio_oaiserver.tasks._records_commit")
    res = RecordMetadata.query.all()
    ids = [rec.id for rec in res]
    
    class MockIndexer:
        def bulk_index(self,query):
            for q in query:
                a=q
        def process_bulk_queue(self,es_bulk_kwargs):
            pass
    mocker.patch("invenio_oaiserver.tasks.RecordIndexer",side_effect=MockIndexer)
    update_records_sets(ids)

# def update_affected_records(spec=None, search_pattern=None):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_tasks.py::test_update_affected_records -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_update_affected_records(app,db,without_oaiset_signals,mocker):
    uuids = [uuid.uuid4() for i in range(5)]
    def mock_get_affected_records(spec,search_pattern):
        for i in uuids:
            yield i
    current_app.config.update(OAISERVER_CELERY_TASK_CHUNK_SIZE=5)
    mocker.patch("invenio_oaiserver.tasks.get_affected_records",side_effect=mock_get_affected_records)
    mocker.patch("invenio_oaiserver.tasks._records_commit")
    mocker.patch("invenio_oaiserver.tasks.sleep")
    class MockIndexer:
        def bulk_index(self,query):
            pass
        def process_bulk_queue(self,es_bulk_kwargs):
            pass
    mocker.patch("invenio_oaiserver.tasks.RecordIndexer",side_effect=MockIndexer)
    oai = OAISet(id=1,
        spec='test',
        name='test_name',
        description='some test description',
        search_pattern='test search')

    db.session.add(oai)
    db.session.commit()
    update_affected_records.delay(oai.spec,oai.search_pattern)



def test_create_data(batch_app,db,dummy_location,data_json_obj, data_json):

    # Location None
    with patch('invenio_oaiserver.tasks.get_create_file_location', return_value=None):
        create_data()

    with patch('invenio_oaiserver.tasks.update_data_json_data', return_value=None):
        create_data()

    # data_json None
    with patch('invenio_oaiserver.tasks.get_data_json', return_value=[None, None]):
        with patch('invenio_oaiserver.tasks.update_data_json_data', return_value=None):
            create_data()

    # format None
    batch_app.config.update(OAISERVER_FILE_BATCH_FORMATS=[])
    with patch('invenio_oaiserver.tasks.update_data_json_data', return_value=None):
        create_data()

    # exception case
    with patch('invenio_oaiserver.tasks.update_data_json_data', side_effect=Exception()):
        create_data()


def test_delete_data_json_data(batch_app,db,dummy_location,data_json_obj):

    # 0 deleted data
    data_json = {
        "current_data": "20250414203611626869",
        "datas": [
            {
                "create_time": "2025-04-14T20:36:11Z",
                "expired_time": "2025-05-14T20:36:11Z",
                "id": "20250414203611626869"
            }
        ]
    }
    new_obj, new_data_json = delete_data_json_data(data_json_obj, data_json)

    assert new_obj != data_json_obj
    assert new_data_json['current_data'] == data_json['current_data']

    # 1 deleted data
    data_json = {
        "current_data": "20250414203611626869",
        "datas": [
            {
                "create_time": "2025-04-13T20:36:11Z",
                "expired_time": "2025-05-13T20:36:11Z",
                "id": "20250413203611626869"
            },
            {
                "create_time": "2025-04-14T20:36:11Z",
                "expired_time": "2025-05-14T20:36:11Z",
                "id": "20250414203611626869"
            },
        ]}

    bucket1 = Bucket.create(dummy_location)
    ObjectVersion.create(bucket1, 'OAI_SERVER_FILE_CREATE/20250413203611626869')
    bucket2 = Bucket.create(dummy_location)
    ObjectVersion.create(bucket2, 'OAI_SERVER_FILE_CREATE/20250414203611626869')
    db.session.commit()

    new_obj, new_data_json = delete_data_json_data(data_json_obj, data_json)
    assert new_obj != data_json_obj
    assert len(new_data_json['datas']) == 1
    assert new_data_json['current_data'] == '20250414203611626869'
    assert new_data_json['datas'][0]['id'] == '20250414203611626869'

    # 2 deleted data
    data_json = {
        "current_data": "20250414203611626869",
        "datas": [
            {
                "create_time": "2025-04-12T20:36:11Z",
                "expired_time": "2025-05-12T20:36:11Z",
                "id": "20250412203611626869"
            },
            {
                "create_time": "2025-04-13T20:36:11Z",
                "expired_time": "2025-05-13T20:36:11Z",
                "id": "20250413203611626869"
            },
            {
                "create_time": "2025-04-14T20:36:11Z",
                "expired_time": "2025-05-14T20:36:11Z",
                "id": "20250414203611626869"
            },
        ]}
    bucket3 = Bucket.create(dummy_location)
    ObjectVersion.create(bucket3, 'OAI_SERVER_FILE_CREATE/20250412203611626869')
    bucket4 = Bucket.create(dummy_location)
    ObjectVersion.create(bucket4, 'OAI_SERVER_FILE_CREATE/20250413203611626869')
    db.session.commit()

    new_obj, new_data_json = delete_data_json_data(data_json_obj, data_json)
    assert new_obj != data_json_obj
    assert len(new_data_json['datas']) == 1
    assert new_data_json['current_data'] == '20250414203611626869'
    assert new_data_json['datas'][0]['id'] == '20250414203611626869'

    # exception case
    with patch('invenio_oaiserver.tasks.ObjectVersion.create', side_effect=Exception()):
        with pytest.raises(Exception) as e:
            delete_data_json_data(new_obj, new_data_json)
            assert False


def test_get_data_json_data_notfound(batch_app,db,bucket,dummy_location):

    # If no data exists.
    with patch('invenio_oaiserver.tasks.ObjectVersion.query.filter_by', return_value=None):
        obj, result = get_data_json(dummy_location)
        assert obj is None
        assert result is None


def test_get_data_json_data_found(batch_app,db,bucket,dummy_location,data_json_obj):

    # If there are data_json with different locations
    other_location = Location(
        name='dummy',
        uri='dummy',
        default=False
    )
    obj, result = get_data_json(other_location)
    assert obj is None
    assert result is None

    # Only folder definitions are available and data_json cannot be retrieved.
    with patch('invenio_oaiserver.tasks.ObjectVersion.get', return_value=None):
        obj, result = get_data_json(dummy_location)
        assert obj is None
        assert result is None

    # data_json can be retrieved.
    with patch('invenio_oaiserver.tasks.ObjectVersion.get', return_value=data_json_obj):
        obj, result = get_data_json(dummy_location)
        assert obj == data_json_obj
        assert result['current_data'] == '20250414203611626869'

    # exception case
    mock = MagicMock()
    mock.file.side_effect = Exception()

    with patch('invenio_oaiserver.tasks.ObjectVersion.get', return_value=mock):
        with pytest.raises(Exception) as e:
            obj, result = get_data_json(dummy_location)
            assert False


def test_create_data_json_data_notfound(batch_app,db,dummy_location):

    # If no data exists.
    with patch('invenio_oaiserver.tasks.ObjectVersion.create', return_value=None):
        with patch('invenio_oaiserver.tasks.Bucket.create', return_value=None):
            obj, result = create_data_json(dummy_location)
            assert result == {}


def test_create_data_json_data_found(batch_app,db,dummy_location,data_json_obj):

    # If there are data_json with different locations
    other_location = Location(
        name='dummy',
        uri='dummy',
        default=False
    )
    with patch('invenio_oaiserver.tasks.ObjectVersion.query.filter_by', return_value=data_json_obj):
        with patch('invenio_oaiserver.tasks.ObjectVersion.create', return_value=None):
            with patch('invenio_oaiserver.tasks.Bucket.create', return_value=None):
                obj, result = create_data_json(other_location)
                assert result == {}


    # exception pattern
    with patch('invenio_oaiserver.tasks.ObjectVersion.query.filter_by', return_value=data_json_obj):
        with patch('invenio_oaiserver.tasks.ObjectVersion.create', return_value=None):
            with pytest.raises(Exception) as e:
                obj, result = create_data_json(other_location)
                assert False


def test_get_create_file_location(batch_app,db,dummy_location):
    batch_app.config.update(OAISERVER_FILE_BATCH_STORAGE_LOACTION=None)
    result = get_create_file_location()
    assert result is None

    batch_app.config.update(OAISERVER_FILE_BATCH_STORAGE_LOACTION='DUMMY')
    result = get_create_file_location()
    assert result is None

    batch_app.config.update(OAISERVER_FILE_BATCH_STORAGE_LOACTION='testloc')
    result = get_create_file_location()
    assert result.name == 'testloc'


def test_save_item_data(batch_app,db,dummy_location,data_json_obj, data_json):
    batch_time = datetime.datetime.now()
    batch_time_str = batch_time.strftime('%Y%m%d%H%M%S%f')

    e_oaipmh = Element(etree.QName(NS_OAIPMH, 'OAI-PMH'), nsmap=NSMAP)
    e_oaipmh.set(etree.QName(NS_XSI, 'schemaLocation'),
                 '{0} {1}'.format(NS_OAIPMH, NS_OAIPMH_XSD))
    e_tree = ElementTree(element=e_oaipmh)
    e_element = SubElement(e_oaipmh, etree.QName(NS_OAIPMH, 'ListRecords'))


    # data unavailable
    with patch('invenio_oaiserver.tasks.listrecords', return_value=e_tree):
        with patch('invenio_files_rest.tasks.ObjectVersion.create', return_value=None):
            save_item_data(data_json_obj.bucket, 'ddi', batch_time_str)

    # deleted data
    e_record1 = SubElement(e_element, etree.QName(NS_OAIPMH, 'record'))
    e_header1 = SubElement(e_record1, etree.QName(NS_OAIPMH, 'header'))
    e_header1.set('status', 'deleted')
    e_identifier1 = SubElement(e_header1, etree.QName(NS_OAIPMH, 'identifier'))
    e_identifier1.text = 'identifier1'
    e_datestamp1 = SubElement(e_header1, etree.QName(NS_OAIPMH, 'datestamp'))
    e_datestamp1.text = datetime_to_datestamp(batch_time)
    e_setspec1 = SubElement(e_header1, etree.QName(NS_OAIPMH, 'setSpec'))
    e_setspec1.text = 'test_setspec1'

    # update data
    e_record2 = SubElement(e_element, etree.QName(NS_OAIPMH, 'record'))
    e_header2 = SubElement(e_record2, etree.QName(NS_OAIPMH, 'header'))
    e_identifier2 = SubElement(e_header2, etree.QName(NS_OAIPMH, 'identifier'))
    e_identifier2.text = 'identifier2'
    e_datestamp2 = SubElement(e_header2, etree.QName(NS_OAIPMH, 'datestamp'))
    e_datestamp2.text = datetime_to_datestamp(batch_time)
    e_setspec2 = SubElement(e_header2, etree.QName(NS_OAIPMH, 'setSpec'))
    e_setspec2.text = 'test_setspec2'

    # Token data
    e_token = SubElement(e_element, etree.QName(NS_OAIPMH, 'resumptionToken'))
    e_token.text = 'test_token'

    # repetitive data
    e_oaipmh2 = Element(etree.QName(NS_OAIPMH, 'OAI-PMH'), nsmap=NSMAP)
    e_oaipmh2.set(etree.QName(NS_XSI, 'schemaLocation'),
                 '{0} {1}'.format(NS_OAIPMH, NS_OAIPMH_XSD))
    e_tree2 = ElementTree(element=e_oaipmh2)
    e_element2 = SubElement(e_oaipmh2, etree.QName(NS_OAIPMH, 'ListRecords'))
    e_token = SubElement(e_element2, etree.QName(NS_OAIPMH, 'resumptionToken'))


    # Token present with data
    with patch('invenio_oaiserver.tasks.listrecords', side_effect=[e_tree, e_tree2]):
        with patch('invenio_oaiserver.tasks.ObjectVersion.create', return_value=None):
            with patch('invenio_oaiserver.tasks.URLSafeTimedSerializer.loads', return_value={}):
                save_item_data(data_json_obj.bucket, 'ddi', batch_time_str)


    # Exception case 1.
    with patch('invenio_oaiserver.tasks.listrecords', side_effect=[e_tree, e_tree2]):
        with patch('invenio_oaiserver.tasks.ObjectVersion.create', side_effect=[None, Exception()]):
            with patch('invenio_oaiserver.tasks.URLSafeTimedSerializer.loads', return_value={}):
                with pytest.raises(Exception) as e:
                    save_item_data(data_json_obj.bucket, 'ddi', batch_time_str)
                    assert False

    # Exception case 2.
    with patch('invenio_oaiserver.tasks.listrecords', side_effect=[e_tree, e_tree2]):
        with patch('invenio_oaiserver.tasks.ObjectVersion.create', side_effect=[None, None, None, Exception()]):
            with patch('invenio_oaiserver.tasks.URLSafeTimedSerializer.loads', return_value={}):
                with pytest.raises(Exception) as e:
                    save_item_data(data_json_obj.bucket, 'ddi', batch_time_str)
                    assert False


def test_update_data_json_data(batch_app,db,dummy_location,data_json_obj):
    batch_time = datetime.datetime.now()
    batch_time_str = batch_time.strftime('%Y%m%d%H%M%S%f')
    batch_app.config.update(OAISERVER_FILE_BATCH_FILE_EXPIRY=24)
    expiry_time = batch_time + datetime.timedelta(hours=24)
    create_time_str = datetime_to_datestamp(batch_time)
    expiry_time_str = datetime_to_datestamp(expiry_time)

    # in case of empty
    data_json = {}
    with patch('invenio_oaiserver.tasks.ObjectVersion.create', return_value=None):
        update_data_json_data(data_json_obj, data_json, batch_time, batch_time_str)
        assert data_json['current_data'] == batch_time_str
        assert len(data_json['datas']) == 1
        assert data_json['datas'][0]['id'] == batch_time_str
        assert data_json['datas'][0]['create_time'] == create_time_str
        assert data_json['datas'][0]['expired_time'] == expiry_time_str

    # Normal case (2 data items)
    batch_time = datetime.datetime.now()
    batch_time_str = batch_time.strftime('%Y%m%d%H%M%S%f')
    batch_app.config.update(OAISERVER_FILE_BATCH_FILE_EXPIRY=24)
    expiry_time = batch_time + datetime.timedelta(hours=24)
    create_time_str = datetime_to_datestamp(batch_time)
    expiry_time_str = datetime_to_datestamp(expiry_time)

    with patch('invenio_oaiserver.tasks.ObjectVersion.create', return_value=None):
        update_data_json_data(data_json_obj, data_json, batch_time, batch_time_str)
        assert data_json['current_data'] == batch_time_str
        assert len(data_json['datas']) == 2
        assert data_json['datas'][1]['id'] == batch_time_str
        assert data_json['datas'][1]['create_time'] == create_time_str
        assert data_json['datas'][1]['expired_time'] == expiry_time_str

    # exception case
    with patch('invenio_oaiserver.tasks.ObjectVersion.create', side_effect=Exception()):
        with pytest.raises(Exception) as e:
            update_data_json_data(data_json_obj, data_json, batch_time, batch_time_str)
            assert False

