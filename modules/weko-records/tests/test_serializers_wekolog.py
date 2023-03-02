import pytest
from tests.helpers import json_data
from lxml import etree
from weko_records.serializers.wekolog import (
    WekologBaseExtension,
    WekologEntryExtension)

WEKOLOGELEMENTS_NS = 'http://wekolog.org/namespaces/basic/1.0/'

# def extend_ns(self):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_wekolog.py::test_extend_ns -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_extend_ns():
    wbe = WekologBaseExtension()
    result = wbe.extend_ns()
    assert result == {'wekolog': WEKOLOGELEMENTS_NS}

# def _extend_xml(self, mapping_type):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_wekolog.py::test_extend_xml -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_extend_xml():
    entry = '<test xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    entry += '</test>'
    entry_xml = etree.fromstring(entry)
    expected = '<test xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    expected += '</test>'
    expected_xml = etree.fromstring(expected)
    wbe = WekologBaseExtension()
    wbe.terms(None)
    wbe.view(None)
    wbe.download(None)
    wbe._extend_xml(entry_xml)
    res = etree.tostring(entry_xml).decode()
    expected_xml = etree.tostring(expected_xml).decode()
    assert res == expected_xml

    entry = '<test xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    entry += '</test>'
    entry_xml = etree.fromstring(entry)
    expected = '<test xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    expected += '<wekolog:terms>2023-03</wekolog:terms>'
    expected += '<wekolog:view>50</wekolog:view>'
    expected += '<wekolog:download>2</wekolog:download>'
    expected += '</test>'
    expected_xml = etree.fromstring(expected)
    wbe = WekologBaseExtension()
    wbe.terms('2023-03')
    wbe.view('50')
    wbe.download('2')
    wbe._extend_xml(entry_xml)
    res = etree.tostring(entry_xml).decode()
    expected_xml = etree.tostring(expected_xml).decode()
    assert res == expected_xml

# def extend_atom(self, atom_feed):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_wekolog.py::test_extend_atom -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_extend_atom():
    atom_feed = '<feed xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    atom_feed += '</feed>'
    atom_feed_xml = etree.fromstring(atom_feed)

    expected = '<feed xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    expected += '<wekolog:terms>2023-03</wekolog:terms>'
    expected += '<wekolog:view>50</wekolog:view>'
    expected += '<wekolog:download>2</wekolog:download>'
    expected += '</feed>'
    expected_xml = etree.fromstring(expected)

    wbe = WekologBaseExtension()
    wbe.terms('2023-03')
    wbe.view('50')
    wbe.download('2')
    res = wbe.extend_atom(atom_feed_xml)
    res = etree.tostring(res).decode()
    expected_xml = etree.tostring(expected_xml).decode()
    assert res == expected_xml

# def extend_rss(self, rss_feed):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_wekolog.py::test_extend_rss -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_extend_rss():
    rss_feed = '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    rss_feed += '</rdf:RDF>'
    rss_feed_xml = etree.fromstring(rss_feed)

    expected = '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    expected += '<wekolog:terms>2023-03</wekolog:terms>'
    expected += '<wekolog:view>50</wekolog:view>'
    expected += '<wekolog:download>2</wekolog:download>'
    expected += '</rdf:RDF>'
    expected_xml = etree.fromstring(expected)

    wbe = WekologBaseExtension()
    wbe.terms('2023-03')
    wbe.view('50')
    wbe.download('2')
    res = wbe.extend_rss([rss_feed_xml])
    print(etree.tostring(res[0]))
    res = etree.tostring(res[0]).decode()
    
    expected_xml = etree.tostring(expected_xml).decode()
    assert res == expected_xml

# def extend_jpcoar(self, jpcoar_feed):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_wekolog.py::test_extend_jpcoar -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_extend_jpcoar():
    jpcoar_feed = '<jpcoar xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    jpcoar_feed += '</jpcoar>'
    jpcoar_feed_xml = etree.fromstring(jpcoar_feed)

    expected = '<jpcoar xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    expected += '<wekolog:terms>2023-03</wekolog:terms>'
    expected += '<wekolog:view>50</wekolog:view>'
    expected += '<wekolog:download>2</wekolog:download>'
    expected += '</jpcoar>'
    expected_xml = etree.fromstring(expected)

    wbe = WekologBaseExtension()
    wbe.terms('2023-03')
    wbe.view('50')
    wbe.download('2')
    res = wbe.extend_jpcoar([jpcoar_feed_xml])
    res = etree.tostring(res[0]).decode()
    expected_xml = etree.tostring(expected_xml).decode()
    assert res == expected_xml

# def terms(self, terms=None, replace=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_wekolog.py::test_terms -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_terms():
    wbe = WekologBaseExtension()
    # No.1
    assert wbe.terms() == None
    # No.2
    terms = '2023-03'
    result = wbe.terms(terms=terms)
    assert result == ['2023-03']
    # No.3
    terms = ['2023-04']
    result = wbe.terms(terms=terms, replace=True)
    assert result == ['2023-04']
    # No4.
    wbe.terms('2023-05')
    terms = '2023-04'
    result = wbe.terms(terms=terms, replace=True)
    assert result == ['2023-04']

# def view(self, view=None, replace=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_wekolog.py::test_view -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_view():
    wbe = WekologBaseExtension()
    # No.1
    assert wbe.view() == None
    # No.2
    view = '1'
    result = wbe.view(view=view)
    assert result == ['1']
    # No.3
    view = ['2']
    result = wbe.view(view=view, replace=True)
    assert result == ['2']
    # No4.
    wbe.view('3')
    view = '10'
    result = wbe.view(view=view, replace=True)
    assert result == ['10']

# def download(self, view=None, replace=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_wekolog.py::test_download -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_download():
    wbe = WekologBaseExtension()
    # No.1
    assert wbe.download() == None
    # No.2
    download = '100'
    result = wbe.download(download=download)
    assert result == ['100']
    # No.3
    download = ['50']
    result = wbe.download(download=download, replace=True)
    assert result == ['50']
    # No4.
    wbe.download('20')
    download = '22'
    result = wbe.download(download=download, replace=True)
    assert result == ['22']


# def WekologEntryExtension.extend_atom(self, entry):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_wekolog.py::test_wekolog_entry_extension_extend_atom -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_wekolog_entry_extension_extend_atom():
    entry = '<entry xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    entry += '<title>item title 1</title>'
    entry += '</entry>'
    entry_xml = etree.fromstring(entry)
    expected = '<entry xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    expected += '<title>item title 1</title>'
    expected += '<wekolog:terms>2023-03</wekolog:terms>'
    expected += '<wekolog:view>50</wekolog:view>'
    expected += '<wekolog:download>2</wekolog:download>'
    expected += '</entry>'
    expected_xml = etree.fromstring(expected)

    wbe = WekologEntryExtension()
    wbe.terms('2023-03')
    wbe.view('50')
    wbe.download('2')
    res = wbe.extend_atom(entry_xml)

    res = etree.tostring(res).decode()
    expected_xml = etree.tostring(expected_xml).decode()
    assert res == expected_xml

# def WekologEntryExtension.extend_rss(self, entry):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_wekolog.py::test_wekolog_entry_extension_extend_rss -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_wekolog_entry_extension_extend_rss():
    item = '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    item += '</rdf:RDF>'
    item_xml = etree.fromstring(item)

    expected = '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:wekolog="%s">' % WEKOLOGELEMENTS_NS
    expected += '<wekolog:terms>2023-03</wekolog:terms>'
    expected += '<wekolog:view>50</wekolog:view>'
    expected += '<wekolog:download>2</wekolog:download>'
    expected += '</rdf:RDF>'
    expected_xml = etree.fromstring(expected)

    wbe = WekologEntryExtension()
    wbe.terms('2023-03')
    wbe.view('50')
    wbe.download('2')
    res = wbe.extend_rss(item_xml)
    res = etree.tostring(res).decode()
    expected_xml = etree.tostring(expected_xml).decode()
    assert res == expected_xml
