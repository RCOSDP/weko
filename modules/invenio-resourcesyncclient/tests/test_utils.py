import json
import pytest
from mock import patch, MagicMock
from lxml import etree
from urllib.error import URLError
from resync.client_utils import ClientFatalError
from resync.url_or_file_open import url_or_file_open
from resync.sitemap import Sitemap
from resync.resource import Resource
from invenio_resourcesyncclient.models import ResyncIndexes
from invenio_resourcesyncclient.utils import (
    read_capability,
    get_resync_list,
    read_url_list,
    sync_baseline,
    sync_audit,
    sync_incremental,
    single_sync_incremental,
    set_query_parameter,
    get_list_records,
    process_item,
    process_sync,
    update_counter,
    gen_resync_pid_value
)


#def read_capability(url):

#def sync_baseline(_map, base_url, counter, dryrun=False,
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_sync_baseline -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_sync_baseline(app):
    _map = ['https//test_server','/tmp/resync136']
    _counter = {
        'processed_items': 0,
        'created_items': 0,
        'updated_items': 0,
        'deleted_items': 0,
        'error_items': 0,
        'list': []
    }
    _base_url = 'http://localhost/'
    _from_date = '2022-10-01'
    _to_date = '2022-10-02'

    with patch('invenio_resourcesyncclient.utils.get_resync_list', return_value='https://test.com/'):
        with patch('invenio_resourcesyncclient.resync.Client.baseline_or_audit', return_value=None):
            res = sync_baseline(_map, _base_url, _counter, False, _from_date, _to_date)
            assert res == True


#def sync_audit(_map, counter):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_sync_audit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_sync_audit(app):
    _map = ['https//test_server']
    _counter = {
        'processed_items': 0,
        'created_items': 0,
        'updated_items': 0,
        'deleted_items': 0,
        'error_items': 0,
        'list': []
    }

    with pytest.raises(Exception) as e:
        res = sync_audit(_map, _counter)
    assert e.type == ClientFatalError


#def sync_incremental(_map, counter, base_url, from_date, to_date):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_sync_incremental -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_sync_incremental(app):
    _map = ['https//localhost']
    _counter = {
        'processed_items': 0,
        'created_items': 0,
        'updated_items': 0,
        'deleted_items': 0,
        'error_items': 0,
        'list': []
    }
    _base_url = 'http://localhost/'
    _from_date = '2022-10-01'
    _to_date = '2022-10-02'

    with pytest.raises(Exception) as e:
        res = sync_incremental(_map, _counter, _base_url, _from_date, _to_date)
    assert e.type == URLError

    with patch('invenio_resourcesyncclient.utils.get_resync_list', return_value='https://test.com/'):
        with patch('invenio_resourcesyncclient.resync.Client.incremental', return_value=None):
            res = sync_incremental(_map, _counter, _base_url, _from_date, _to_date)
            assert res == True


#def single_sync_incremental(_map, counter, url, from_date, to_date):


#def set_query_parameter(url, param_name, param_value):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_set_query_parameter -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_set_query_parameter(app):
    res = set_query_parameter('http://localhost/test/?a=v1&b=v2', 'c', 'v3')
    assert res == 'http://localhost/test/?a=v1&b=v2&c=v3'


#def get_list_records(resync_id):


#def process_item(record, resync, counter):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_process_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_process_item(app, db, esindex, location, test_resync, db_itemtype, db_oaischema):
    _data = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2022-11-14T06:45:01Z</responseDate><request verb="GetRecord" metadataPrefix="jpcoar_1.0" identifier="oai:repository.dl.itc.u-tokyo.ac.jp:00049042">https://repository.dl.itc.u-tokyo.ac.jp/oai</request><GetRecord><record><header><identifier>oai:repository.dl.itc.u-tokyo.ac.jp:00049042</identifier><datestamp>2021-03-01T20:28:59Z</datestamp></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title>Decolonizing One Petition at the Time : A Review of the Practice of Accepting Petitions and Granting Oral Hearings in the Fourth Committee of the UN General Assembly</dc:title><jpcoar:creator><jpcoar:creatorName>Scartozzi, Cesare Marco</jpcoar:creatorName></jpcoar:creator><jpcoar:subject subjectScheme="Other">Decolonization</jpcoar:subject><jpcoar:subject subjectScheme="Other">Fourth Committee</jpcoar:subject><jpcoar:subject subjectScheme="Other">Petitions</jpcoar:subject><jpcoar:subject subjectScheme="Other">Revitalization of the General Assembly</jpcoar:subject><jpcoar:subject subjectScheme="Other">United Nations</jpcoar:subject><dc:publisher>International Association for Political Science Students (IAPSS)</dc:publisher><datacite:date dateType="Issued">2017-10</datacite:date><dc:language>eng</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_6501">journal article</dc:type><jpcoar:identifier identifierType="HDL">http://hdl.handle.net/2261/00074166</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://repository.dl.itc.u-tokyo.ac.jp/records/49042</jpcoar:identifier><jpcoar:relation><jpcoar:relatedIdentifier identifierType="DOI">info:doi/10.22151/politikon.34.4</jpcoar:relatedIdentifier></jpcoar:relation><jpcoar:sourceTitle>POLITIKON : The IAPSS Journal of Political Science</jpcoar:sourceTitle><jpcoar:volume>34</jpcoar:volume><jpcoar:pageStart>49</jpcoar:pageStart><jpcoar:pageEnd>67</jpcoar:pageEnd><jpcoar:file><jpcoar:URI label="Politikon_vol.-34_49-67.pdf">https://repository.dl.itc.u-tokyo.ac.jp/record/49042/files/Politikon_vol.-34_49-67.pdf</jpcoar:URI><jpcoar:mimeType>application/pdf</jpcoar:mimeType><jpcoar:extent>559.4 kB</jpcoar:extent><datacite:date dateType="Available">2018-02-23</datacite:date></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>'
    _tree = etree.fromstring(_data)
    _record = _tree.findall('./GetRecord/record', namespaces=_tree.nsmap)[0]
    _resync = db.session.query(ResyncIndexes).filter_by(id=30).first()
    _counter = {
        'processed_items': 0,
        'created_items': 0,
        'updated_items': 0,
        'deleted_items': 0,
        'error_items': 0,
        'list': []
    }

    process_item(_record, _resync, _counter)
    assert _counter['created_items'] == 1

    process_item(_record, _resync, _counter)
    assert _counter['updated_items'] == 1


# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_process_item_validation_enabled_new -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_process_item_validation_enabled_new(app, mocker):
    """C1: WEKO_ADMIN_VALIDATION_ENABLE=True on the new-item path.

    Covers the True branch of the **first** occurrence of
        if current_app.config.get('WEKO_ADMIN_VALIDATION_ENABLE')
    in process_item (resyncid is None -> dep.update(route='ResouceSync',
    item_id=pid_created)).

    Heavy mapping/DB infrastructure is stubbed so the test does not
    depend on db_itemtype / db_oaischema / esindex fixtures or the real
    JPCOARMapper (which has a pre-existing MAPPING_ERROR in some envs).
    """
    import types

    class _StopHere(Exception):
        """Sentinel used to short-circuit process_item after dep.update."""

    app.config['WEKO_ADMIN_VALIDATION_ENABLE'] = True

    # 1) Stub JPCOARMapper.
    mock_mapper = MagicMock()
    mock_mapper.identifier.return_value = 'val_resync_new_id'
    mock_mapper.is_deleted.return_value = False
    mock_mapper.map.return_value = {'sample_field': 'value'}
    mock_mapper.itemtype = MagicMock()
    mock_mapper.itemtype.id = 1
    mocker.patch("invenio_resourcesyncclient.utils.JPCOARMapper",
                 return_value=mock_mapper)

    # 2) Replace gen_resync_pid_value so it does not need the resync to
    # be a real DB row.
    mocker.patch(
        "invenio_resourcesyncclient.utils.gen_resync_pid_value",
        return_value='resync-pid-for-new-item')

    # 3) Replace PersistentIdentifier so query.filter_by(...).with_lockmode(
    # 'update').one_or_none() returns None (i.e. resyncid does not exist),
    # and PID.create(...) returns a known fake PID we can assert on.
    fake_pid = MagicMock()
    fake_pid.pid_type = 'syncid'
    fake_pid.pid_value = 'resync-pid-for-new-item'

    mock_pid_cls = mocker.patch(
        "invenio_resourcesyncclient.utils.PersistentIdentifier")
    (mock_pid_cls.query.filter_by.return_value
        .with_lockmode.return_value.one_or_none.return_value) = None
    mock_pid_cls.create.return_value = fake_pid

    # 4) Replace WekoDeposit.create so dep.update raises _StopHere right
    # after the new conditional fires.
    mock_dep = MagicMock()
    mock_dep.pid.object_type = 'rec'
    mock_dep.pid.object_uuid = 'dep-uuid'
    mock_dep.update.side_effect = _StopHere
    mocker.patch("invenio_resourcesyncclient.utils.WekoDeposit.create",
                 return_value=mock_dep)

    resync = types.SimpleNamespace(
        saving_format='JPCOAR-XML',
        index_id=1,
    )
    counter = {
        'processed_items': 0,
        'created_items': 0,
        'updated_items': 0,
        'deleted_items': 0,
        'error_items': 0,
        'list': []
    }
    record = etree.fromstring(
        b'<record xmlns="http://www.openarchives.org/OAI/2.0/">'
        b'<header><identifier>x</identifier>'
        b'<datestamp>2020-01-01T00:00:00Z</datestamp></header>'
        b'<metadata/></record>')

    with pytest.raises(_StopHere):
        process_item(record, resync, counter)

    assert mock_dep.update.call_count == 1
    call_kwargs = mock_dep.update.call_args.kwargs
    assert call_kwargs.get('route') == 'ResouceSync'
    assert call_kwargs.get('item_id') is fake_pid


# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_process_item_validation_enabled_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_process_item_validation_enabled_update(app, mocker):
    """C1: WEKO_ADMIN_VALIDATION_ENABLE=True on the update (existing) path.

    Covers the True branch of the **second** occurrence of
        if current_app.config.get('WEKO_ADMIN_VALIDATION_ENABLE')
    in process_item (resyncid exists, mapper.is_deleted()=False ->
    dep.update(route='ResouceSync', item_id=resyncid)).
    """
    import types

    class _StopHere(Exception):
        pass

    app.config['WEKO_ADMIN_VALIDATION_ENABLE'] = True

    mock_mapper = MagicMock()
    mock_mapper.identifier.return_value = 'val_resync_upd_id'
    mock_mapper.is_deleted.return_value = False
    mock_mapper.map.return_value = {'sample_field': 'value'}
    mock_mapper.itemtype = MagicMock()
    mock_mapper.itemtype.id = 1
    mocker.patch("invenio_resourcesyncclient.utils.JPCOARMapper",
                 return_value=mock_mapper)

    mocker.patch(
        "invenio_resourcesyncclient.utils.gen_resync_pid_value",
        return_value='resync-pid-for-existing-item')

    # Existing resyncid; recid lookup also needs to succeed.
    fake_resyncid = MagicMock()
    fake_resyncid.pid_type = 'syncid'
    fake_resyncid.pid_value = 'resync-pid-for-existing-item'
    fake_resyncid.object_uuid = 'rec-uuid-1'

    fake_recid = MagicMock()
    fake_recid.pid_value = '1'
    fake_recid.object_uuid = 'rec-uuid-1'
    fake_recid.status = None

    mock_pid_cls = mocker.patch(
        "invenio_resourcesyncclient.utils.PersistentIdentifier")
    (mock_pid_cls.query.filter_by.return_value
        .with_lockmode.return_value.one_or_none.return_value) = fake_resyncid
    mock_pid_cls.query.filter_by.return_value.one_or_none.return_value = \
        fake_recid

    # RecordMetadata.query.filter_by(id=...).one_or_none()
    mock_record_meta_cls = mocker.patch(
        "invenio_resourcesyncclient.utils.RecordMetadata")
    fake_record_metadata = MagicMock(json={})
    (mock_record_meta_cls.query.filter_by.return_value
        .one_or_none.return_value) = fake_record_metadata

    # WekoDeposit(r.json, r) constructor returns mock_dep; dep.update
    # short-circuits via _StopHere.
    mock_dep = MagicMock()
    mock_dep.__contains__ = MagicMock(return_value=False)  # 'path' not in dep
    mock_dep.update.side_effect = _StopHere
    mocker.patch("invenio_resourcesyncclient.utils.WekoDeposit",
                 return_value=mock_dep)

    resync = types.SimpleNamespace(
        saving_format='JPCOAR-XML',
        index_id=1,
    )
    counter = {
        'processed_items': 0,
        'created_items': 0,
        'updated_items': 0,
        'deleted_items': 0,
        'error_items': 0,
        'list': []
    }
    record = etree.fromstring(
        b'<record xmlns="http://www.openarchives.org/OAI/2.0/">'
        b'<header><identifier>x</identifier>'
        b'<datestamp>2020-01-01T00:00:00Z</datestamp></header>'
        b'<metadata/></record>')

    with pytest.raises(_StopHere):
        process_item(record, resync, counter)

    assert mock_dep.update.call_count == 1
    call_kwargs = mock_dep.update.call_args.kwargs
    assert call_kwargs.get('route') == 'ResouceSync'
    assert call_kwargs.get('item_id') is fake_resyncid


# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_process_item_validation_disabled -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_process_item_validation_disabled(app, mocker):
    """C1: WEKO_ADMIN_VALIDATION_ENABLE=False keeps the legacy dep.update.

    Mirror of test_process_item_validation_enabled_new - covers the
    False branch (no route/item_id kwargs forwarded to dep.update).
    """
    import types

    class _StopHere(Exception):
        pass

    app.config['WEKO_ADMIN_VALIDATION_ENABLE'] = False

    mock_mapper = MagicMock()
    mock_mapper.identifier.return_value = 'val_resync_dis_id'
    mock_mapper.is_deleted.return_value = False
    mock_mapper.map.return_value = {'sample_field': 'value'}
    mock_mapper.itemtype = MagicMock()
    mock_mapper.itemtype.id = 1
    mocker.patch("invenio_resourcesyncclient.utils.JPCOARMapper",
                 return_value=mock_mapper)
    mocker.patch(
        "invenio_resourcesyncclient.utils.gen_resync_pid_value",
        return_value='resync-pid-disabled')

    mock_pid_cls = mocker.patch(
        "invenio_resourcesyncclient.utils.PersistentIdentifier")
    (mock_pid_cls.query.filter_by.return_value
        .with_lockmode.return_value.one_or_none.return_value) = None
    mock_pid_cls.create.return_value = MagicMock()

    mock_dep = MagicMock()
    mock_dep.pid.object_type = 'rec'
    mock_dep.pid.object_uuid = 'dep-uuid'
    mock_dep.update.side_effect = _StopHere
    mocker.patch("invenio_resourcesyncclient.utils.WekoDeposit.create",
                 return_value=mock_dep)

    resync = types.SimpleNamespace(
        saving_format='JPCOAR-XML',
        index_id=1,
    )
    counter = {
        'processed_items': 0,
        'created_items': 0,
        'updated_items': 0,
        'deleted_items': 0,
        'error_items': 0,
        'list': []
    }
    record = etree.fromstring(
        b'<record xmlns="http://www.openarchives.org/OAI/2.0/">'
        b'<header><identifier>x</identifier>'
        b'<datestamp>2020-01-01T00:00:00Z</datestamp></header>'
        b'<metadata/></record>')

    with pytest.raises(_StopHere):
        process_item(record, resync, counter)

    assert mock_dep.update.call_count == 1
    call_kwargs = mock_dep.update.call_args.kwargs
    assert call_kwargs.get('route') is None
    assert call_kwargs.get('item_id') is None


#def process_sync(resync_id, counter):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_process_sync -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_process_sync(app, test_resync):
    _counter = {
        'processed_items': 0,
        'created_items': 0,
        'updated_items': 0,
        'deleted_items': 0,
        'error_items': 0,
        'list': []
    }

    with patch('invenio_resourcesyncclient.utils.read_capability', return_value=None):
        with pytest.raises(Exception) as e:
            res = process_sync(30, _counter)
        assert e.type == ValueError
        with pytest.raises(Exception) as e:
            res = process_sync(40, _counter)
        assert e.type == ValueError
        with pytest.raises(Exception) as e:
            res = process_sync(50, _counter)
        assert e.type == ValueError


    with patch('invenio_resourcesyncclient.utils.read_capability', return_value='test'):
        with pytest.raises(Exception) as e:
            res = process_sync(30, _counter)
        assert e.type == ValueError
        with pytest.raises(Exception) as e:
            res = process_sync(40, _counter)
        assert e.type == ValueError
        with pytest.raises(Exception) as e:
            res = process_sync(50, _counter)
        assert e.type == ValueError

    with patch('invenio_resourcesyncclient.utils.read_capability', return_value='resourcelist'):
        with patch('invenio_resourcesyncclient.utils.sync_baseline', return_value=True):
            res = process_sync(30, _counter)
            assert json.loads(res.data) == {'success': True}
            with patch('invenio_resourcesyncclient.utils.sync_audit', return_value=dict(same=0, updated=0, deleted=0, created=0)):
                with pytest.raises(Exception) as e:
                    res = process_sync(50, _counter)
                assert e.type == TypeError

    with patch('invenio_resourcesyncclient.utils.read_capability', return_value='changelist'):
        with patch('invenio_resourcesyncclient.utils.sync_incremental', return_value=True):
                res = process_sync(80, _counter)
                assert json.loads(res.data) == {'result': True}

#def update_counter(counter, result):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_update_counter -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_update_counter(app):
    _counter = {
        'processed_items': 0,
        'created_items': 0,
        'updated_items': 0,
        'deleted_items': 0,
        'error_items': 0,
        'list': []
    }
    _result = {
        'created': [1, 2],
        'updated': [3, 4],
        'deleted': [5, 6],
        'resource': [7, 8, 9]
    }

    update_counter(_counter, _result)
    assert _counter == {'created_items': 2, 'deleted_items': 2, 'error_items': 0, 'list': [7, 8, 9], 'processed_items': 0, 'resource_items': 3, 'updated_items': 2}


#def get_from_date_from_url(url):


#def gen_resync_pid_value(resync, pid):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_utils.py::test_gen_resync_pid_value -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_gen_resync_pid_value(app):
    res = gen_resync_pid_value(None, 'test_pid')
    assert res == 'test_pid'


def test_get_resync_list(app):
    with patch('invenio_resourcesyncclient.utils.read_capability', return_value='test'):
        with pytest.raises(Exception) as e:
            res = get_resync_list('https://test.com', 'baselist')
        assert e.type == ValueError

    with patch('invenio_resourcesyncclient.utils.read_capability', side_effect=['description', 'baselist']):
        with patch('invenio_resourcesyncclient.utils.read_url_list', side_effect=[['https://data1.com'], ['https://data2.com']]):
            res = get_resync_list('https://test.com', 'baselist')
            assert res == ['https://data1.com', 'https://data2.com']

    with patch('invenio_resourcesyncclient.utils.read_capability', return_value='capabilitylist'):
        with patch('invenio_resourcesyncclient.utils.read_url_list', return_value=['https://data1.com', 'https://data2.com']):
            res = get_resync_list('https://test.com', 'baselist')
            assert res == ['https://data1.com', 'https://data2.com']

    with patch('invenio_resourcesyncclient.utils.read_capability', return_value='changelist'):
        with patch('invenio_resourcesyncclient.utils.url_or_file_open', return_value=None):
            with patch('invenio_resourcesyncclient.utils.Sitemap') as m:
                m.return_value.parse_xml.return_value = None
                m.return_value.parsed_index = False
                res = get_resync_list('https://test.com', 'changelist')
                assert res == ['https://test.com']

    document = MagicMock()
    resource = MagicMock()
    resource.uri = 'https://data1.com'
    document.resources = [resource]
    with patch('invenio_resourcesyncclient.utils.read_capability', return_value='changelist'):
        with patch('invenio_resourcesyncclient.utils.url_or_file_open', return_value=None):
            with patch('invenio_resourcesyncclient.utils.Sitemap') as m:
                m.return_value.parse_xml.return_value = document
                m.return_value.parsed_index = True
                res = get_resync_list('https://test.com', 'changelist')
                assert res == ['https://data1.com']


def test_read_url_list(app):

    with patch('invenio_resourcesyncclient.utils.url_or_file_open', return_value='https://test.com'):
        with pytest.raises(IOError) as e:
            res = read_url_list('https://test.com', 'baselist')
        assert e.type == FileNotFoundError

    document = MagicMock()
    document.resources = []
    with patch('invenio_resourcesyncclient.utils.url_or_file_open', return_value=None):
        with patch('invenio_resourcesyncclient.utils.Sitemap.parse_xml', return_value=document):
            res = read_url_list('https://test.com', 'baselist')
            assert res == []

    document = MagicMock()
    resource = MagicMock()
    resource.uri = 'https://data1.com'
    document.resources = [resource]
    child = MagicMock()
    child.md = {'capability': 'baselist'}

    with patch('invenio_resourcesyncclient.utils.url_or_file_open', return_value=None):
        with patch('invenio_resourcesyncclient.utils.Sitemap.parse_xml', side_effect=[document, child]):
            res = read_url_list('https://test.com', 'baselist')
            assert res == ['https://data1.com']

    document = MagicMock()
    resource = MagicMock()
    resource.uri = 'https://data1.com'
    document.resources = [resource]
    child = MagicMock()
    child.md = {'capability': 'changelist'}
    resource2 = MagicMock()
    resource2.uri = 'https://data2.com'
    child.resources = [resource2]

    with patch('invenio_resourcesyncclient.utils.url_or_file_open', return_value=None):
        with patch('invenio_resourcesyncclient.utils.Sitemap') as m:
            m.return_value.parse_xml.side_effect=[document, child]
            m.return_value.parsed_index = True
            res = read_url_list('https://test.com', 'changelist')
            assert res == ['https://data2.com']
