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
