# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Module tests."""

import re
from datetime import datetime
import os

import signal

import pytest
import responses
from mock import patch
from invenio_db import db
from weko_index_tree.models import Index
from lxml import etree

from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from invenio_oaiharvester.errors import InvenioOAIHarvesterError
from invenio_oaiharvester.models import HarvestSettings,HarvestLogs
from invenio_oaiharvester.signals import oaiharvest_finished
from invenio_oaiharvester.tasks import create_indexes, event_counter, \
    get_specific_records, list_records_from_dates, map_indexes, \
    process_item, run_harvesting,link_success_handler,link_error_handler,\
        is_harvest_running,check_schedules_and_run

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_get_specific_records -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
@responses.activate
def test_get_specific_records(app, sample_record_xml):
    """Test that getting records via identifiers work with prefix."""
    def foo(request, records, name):
        assert len(records) == 1

    responses.add(
        responses.GET,
        'http://export.arxiv.org/oai2',
        body=sample_record_xml,
        content_type='text/xml'
    )
    oaiharvest_finished.connect(foo)
    try:
        with app.app_context():
            get_specific_records(
                'oai:arXiv.org:1507.03011',
                metadata_prefix="arXiv",
                url='http://export.arxiv.org/oai2'
            )
            # As a list of identifiers
            get_specific_records(
                ['oai:arXiv.org:1507.03011'],
                metadata_prefix="arXiv",
                url='http://export.arxiv.org/oai2'
            )
            # signals is False
            get_specific_records(
                ['oai:arXiv.org:1507.03011'],
                metadata_prefix="arXiv",
                url='http://export.arxiv.org/oai2',
                signals=False
            )
    finally:
        oaiharvest_finished.disconnect(foo)

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_list_records_from_dates -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
@responses.activate
def test_list_records_from_dates(app, sample_list_xml):
    """Check harvesting of records from multiple setspecs."""
    def bar(request, records, name):
        assert len(records) == 150

    responses.add(
        responses.GET,
        re.compile(r'http?://export.arxiv.org/oai2.*set=physics.*'),
        body=sample_list_xml,
        content_type='text/xml'
    )
    oaiharvest_finished.connect(bar)
    try:
        with app.app_context():
            list_records_from_dates(
                metadata_prefix='arXiv',
                from_date='2015-01-15',
                until_date='2015-01-20',
                url='http://export.arxiv.org/oai2',
                name=None,
                setspecs='physics'
            )

            # signals is False
            list_records_from_dates(
                metadata_prefix='arXiv',
                from_date='2015-01-15',
                until_date='2015-01-20',
                url='http://export.arxiv.org/oai2',
                name=None,
                setspecs='physics',
                signals=False
            )
    finally:
        oaiharvest_finished.disconnect(bar)


#@responses.activate
#def test_list_records_from_dates(app, sample_list_xml):
#    """Check harvesting of records from multiple setspecs."""
#    try:
#        with app.app_context():
#            index = Index()
#            db.session.add(index)
#            db.session.commit()
#
#            harvesting = HarvestSettings(
#                repository_name='name',
#                base_url='https://jpcoar.repo.nii.ac.jp/oai',
#                metadata_prefix='jpcoar_1.0',
#                index_id=index.id,
#                update_style='0',
#                auto_distribution='0')
#            db.session.add(harvesting)
#            db.session.commit()
#
#            # run_harvesting(
#            #     harvesting.id,
#            #     datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'),
#            #     {'ip_address': '0.0,0.0',
#            #         'user_agent': '',
#            #         'user_id': 1,
#            #         'session_id': '1'}
#            # )
#    finally:
#        return

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_create_indexes -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_create_indexes(app, db):
    """Check harvesting of records from multiple setspecs."""
    with app.app_context():
        index = Index()
        db.session.add(index)
        db.session.commit()

        create_indexes(index.id, {
            '1': 'set_name_1',
            '2': 'set_name_2'
        })
        assert Index.query.filter_by(harvest_spec="1").first().index_name == "set_name_1"
        assert Index.query.filter_by(harvest_spec="2").first().index_name == "set_name_2"
        
        # set in specs
        create_indexes(index.id, {
            '1': 'new_index',
        })
        assert Index.query.filter_by(index_name="new_index").first() is None



# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_map_indexes -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_map_indexes(app, db):
    """Check harvesting of records from multiple setspecs."""
    with app.app_context():
        index = Index()
        db.session.add(index)

        index2 = Index()
        index2.parent = 1
        index2.position = 1
        index2.harvest_spec = '1'
        index2.is_deleted = True
        db.session.add(index2)

        index3 = Index()
        index3.parent = 1
        index3.position = 2
        index3.harvest_spec = '2'
        db.session.add(index3)

        db.session.commit()

        res = map_indexes({
            '1': 'set_name_1',
            '2': 'set_name_2'
        }, index.id)
        assert not 2 in res
        assert 3 in res


def test_event_counter(app):
    """Check harvesting of records from multiple setspecs."""
    counter = {}

    event_counter('a', counter)
    event_counter('a', counter)


# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_process_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_process_item(app, db, esindex, location, db_itemtype, harvest_setting, db_records, mocker, monkeypatch):
    app.config["WEKO_SCHEMA_JPCOAR_V2_SCHEMA_NAME"] = 'jpcoar_mapping'
    app.config["WEKO_SCHEMA_JPCOAR_V2_RESOURCE_TYPE_REPLACE"] = {
            'periodical':'journal',
            'interview':'other',
            'internal report':'other',
            'report part':'other',
        }
    app.config["WEKO_SCHEMA_JPCOAR_V2_NAMEIDSCHEME_REPLACE"] = {'e-Rad':'e-Rad_Researcher'}
    monkeypatch.setenv("TIKA_JAR_FILE_PATH", "/code/tika/tika-app-2.6.0.jar")
    mocker.patch("weko_search_ui.utils.send_item_created_event_to_es")
    mock_resource_type_map={
        'conference paper':'Harvesting dc'
    }
    mocker.patch("invenio_oaiharvester.harvester.RESOURCE_TYPE_MAP",mock_resource_type_map)
    # jpcoar
    # mapper.is_deleted is true
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-01T02:07:10Z</responseDate><request metadataPrefix="oai_dc" identifier="oai:weko3.example.org:00000001" verb="GetRecord">https://192.168.56.103/oai</request><GetRecord><record><header status="deleted"><identifier>oai:weko3.example.org:00000005</identifier><datestamp>2023-02-20T06:24:47Z</datestamp></header></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[0], _counter, None)
    assert res==None
    
    ## pubdate > mapper.datestamp, update_style=1
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2020-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    jpcoar_setting2 = HarvestSettings(
        id=10,
        repository_name="jpcoar_test2",
        base_url="http://export.arxiv.org/oai2",
        from_date=datetime(2022, 10, 1),
        until_date=datetime(2022, 10, 2),
        metadata_prefix="jpcoar_1.0",
        index_id=2,
        update_style="1",
        auto_distribution="0"
    )
    with db.session.begin_nested():
        db.session.add(jpcoar_setting2)
    db.session.commit()
    res = process_item(_records[0], jpcoar_setting2, _counter, None)
    assert res==None
    
    ## json_data is none
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>11</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    with patch('invenio_oaiharvester.tasks.JPCOARMapper.map', return_value=[]):
        res = process_item(_records[0], harvest_setting[0], _counter, None)
        assert res == None
        
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[0], _counter, None)
    assert res == None
    
    ## dep.pid.status == deleted
    dep_pid = PersistentIdentifier.query.filter_by(pid_type="depid",pid_value='1').one()
    dep_pid.status = PIDStatus.DELETED
    db.session.merge(dep_pid)
    db.session.commit()
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[0], _counter, None)
    assert res == None
    
    ## new harvest
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000002</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[0], _counter, None)
    assert res == None
    
    
    # ddi
    ## item_1593074267803 not in json_data
    ##_etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2022-11-01T07:24:43Z</responseDate><request verb="GetRecord" metadataPrefix="ddi" identifier="oai:invenio:00000002">https://data.lib.keio.ac.jp/oai</request><GetRecord><record><header><identifier>oai:invenio:00000002</identifier><datestamp>2021-06-24T14:23:51Z</datestamp></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="en"><titlStmt><titl xml:lang="en">Japanese Panel Survey of Consumers: 1994</titl><altTitl xml:lang="en">JPSC</altTitl><IDNo>JPSC2</IDNo></titlStmt><rspStmt><AuthEnty xml:lang="en">Institute for Research on Household ECONOMICS</AuthEnty></rspStmt><prodStmt><producer xml:lang="en">Panel Data Research Center at Keio University</producer><copyright xml:lang="en">Before your application, you need to agree with our written pledge (e.g. the data will be only use for research purpose, will not be provided any third party etc).</copyright></prodStmt><distStmt><distrbtr xml:lang="en">Panel Data Research Center at Keio University</distrbtr></distStmt><serStmt><serName xml:lang="en">Japanese Panel Survey of Consumers(JPSC) Series</serName></serStmt><verStmt><notes>jpn</notes><notes>eng</notes></verStmt><biblCit xml:lang="en">Publications in academic journals, academic societies, and media articles based on analysis of data provided by the PDRC must be credited to the Panel Data Research Center at Keio University.\n\n(Example)\nThe data for this analysis, Japanese Panel Survey of Consumers (JPSC), was provided by the Keio University Panel Data Research Center.</biblCit><holdings URI="https://data.lib.keio.ac.jp/records/2"/></citation><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">消費生活に関するパネル調査 (JPSC) 1994</titl><altTitl xml:lang="ja">JPSC</altTitl><IDNo>JPSC2</IDNo></titlStmt><rspStmt><AuthEnty xml:lang="ja">家計経済研究所</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">慶應義塾大学パネルデータ設計・解析センター</producer><copyright xml:lang="ja">詳しくは、データ申請時に表示される誓約書を確認してください。</copyright></prodStmt><distStmt><distrbtr xml:lang="ja">慶應義塾大学パネルデータ設計・解析センター</distrbtr></distStmt><serStmt><serName xml:lang="ja">消費生活に関するパネル調査(JPSC)シリーズ</serName></serStmt><verStmt><notes>jpn</notes><notes>eng</notes></verStmt><biblCit xml:lang="ja">学術誌あるいは学会等で分析結果を発表する際は、慶應義塾大学パネルデータ設計・解析センターから各データの個票データの提供を受けた旨を必ず明記して下さい。\n\n例: 本稿の分析に際しては、慶應義塾大学パネルデータ設計・解析センターによる「消費生活に関するパネル調査(JPSC)」の個票データの提供を受けた。\n\nThe data for this analysis, Japanese Panel Survey of Consumers (JPSC), was provided by the Keio University Panel Data Research Center.</biblCit><holdings URI="https://data.lib.keio.ac.jp/records/2"/></citation><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">ECONOMICS</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Income, property and investment/saving</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">HEALTH</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Drug abuse, alcohol and smoking</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">General health and well-being</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Reproductive health</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">HOUSING AND LAND USE</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Housing</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">LABOUR AND EMPLOYMENT</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Employment</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Working conditions</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">SOCIAL STRATIFICATION AND GROUPINGS</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Family life and marriage</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Gender and gender roles</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Social and occupational mobility</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">SOCIETY AND CULTURE</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Time use</topcClas></subject><abstract xml:lang="en">The JPSC started in 1993 with a sample of 1,500 young woman (aged from 24 to 34 years) and their spouses. The objective was to examine the lifestyles of relatively young woman from a wide spectrum of factors, including income, expenditure, savings, work patterns, and family relationships. Since then, the survey has been conducted annually and expanded to include new cohorts in 1997 (500 respondents), 2003 (836 respondents), 2008 (636 respondents), and 2013 (672 respondents).</abstract><sumDscr><timePrd event="start">1993</timePrd><timePrd event="end">1994</timePrd><collDate>1994</collDate><geogCover xml:lang="en">Japan</geogCover><anlyUnit xml:lang="en">Individual</anlyUnit><anlyUnit xml:lang="en">Family</anlyUnit><anlyUnit xml:lang="en">Family: Household family</anlyUnit><anlyUnit xml:lang="en">Household</anlyUnit><universe xml:lang="en">Japanese female over 24</universe><dataKind xml:lang="en">quantitative research: micro data</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="ja"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">経済</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">所得、財産、投資・貯蓄</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">健康</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">薬物乱用、アルコール、喫煙</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">健康一般とウェルビーイング</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">リプロダクティブヘルス</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">住宅と土地利用</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">住宅</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">労働と雇用</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">雇用</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">労働条件</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">社会階層と社会集団</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">家族生活と結婚</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">ジェンダーと性別役割</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">社会移動と職業移動</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">社会と文化</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">生活時間</topcClas></subject><abstract xml:lang="ja">1993年に当時24歳から34歳の女性1,500名とその配偶者を対象に、若年女性の生活実態を、収入・支出・貯蓄、就業行動、家族関係などの諸側面から明らかにすることを目的としています。1997年(500名)、2003年(836名)、2008年(636名)、2013年(672名)に新規調査対象者が追加され、現在まで調査が続いています。</abstract><sumDscr><timePrd event="start">1993</timePrd><timePrd event="end">1994</timePrd><collDate>1994</collDate><geogCover xml:lang="ja">日本</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><anlyUnit xml:lang="ja">家族</anlyUnit><anlyUnit xml:lang="ja">家族: 世帯家族</anlyUnit><anlyUnit xml:lang="ja">世帯</anlyUnit><universe xml:lang="ja">日本の24歳以上の女性</universe><dataKind xml:lang="ja">量的調査: ミクロデータ</dataKind></sumDscr></stdyInfo><method xml:lang="en"><dataColl><sampProc xml:lang="en">Mixed probability and non-probability</sampProc><collMode xml:lang="en">Self-administered questionnaire</collMode></dataColl></method><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">混合確率と非確率</sampProc><collMode xml:lang="ja">自記式調査票</collMode></dataColl></method><dataAccs xml:lang="en"><setAvail><accsPlac>https://www.pdrc.keio.ac.jp/pdrc/</accsPlac><avlStatus xml:lang="en">restricted access</avlStatus></setAvail></dataAccs><dataAccs xml:lang="ja"><setAvail><accsPlac>https://www.pdrc.keio.ac.jp/pdrc/</accsPlac><avlStatus xml:lang="ja">制約付きアクセス</avlStatus></setAvail></dataAccs><othrStdyMat><relStdy ID="https://www.pdrc.keio.ac.jp/en/paneldata/datasets/"/><relPubl ID="https://www.pdrc.keio.ac.jp/jpsc/bunken/result-1994/"/></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>')
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000075">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt><distrbtr URI="https://test.distributor.affiliation" abbr="TDN" xml:lang="ja" affiliation="Test Distributor Affiliation">Test Distributor Name</distrbtr></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75" /></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe><dataKind xml:lang="ja">量的調査</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit><dataKind xml:lang="en">quantatitive research</dataKind></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo /></method><dataAccs xml:lang="jp"><setAvail><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[1], _counter, None)
    assert res==None
    
    ## creatorNames not in json_data['item_1593074267803']
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000077">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><rspStmt><AuthEnty ID="4" affiliation="author.affiliation"></AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt><distrbtr URI="https://test.distributor.affiliation" abbr="TDN" xml:lang="ja" affiliation="Test Distributor Affiliation">Test Distributor Name</distrbtr></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75" /></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe><dataKind xml:lang="ja">量的調査</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit><dataKind xml:lang="en">quantatitive research</dataKind></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo /></method><dataAccs xml:lang="jp"><setAvail><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[1], _counter, None)
    assert res==None
    
    ## creatorNameLang not in json_data['item_1593074267803'][0]['creatorNames']
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000078">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><rspStmt><AuthEnty ID="4" affiliation="author.affiliation">テスト, 太郎</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt><distrbtr URI="https://test.distributor.affiliation" abbr="TDN" xml:lang="ja" affiliation="Test Distributor Affiliation">Test Distributor Name</distrbtr></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75" /></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe><dataKind xml:lang="ja">量的調査</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit><dataKind xml:lang="en">quantatitive research</dataKind></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo /></method><dataAccs xml:lang="jp"><setAvail><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[1], _counter, None)
    assert res==None
    
    ## json_data['item_1593074267803'][0]['creatorNames'][0]['creatorNameLang'] == json_data['item_1593074267803'][n]['creatorNames'][0]['creatorNameLang']
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000079">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><rspStmt><AuthEnty ID="4" xml:lang="ja" affiliation="author.affiliation">テスト, 太郎</AuthEnty><AuthEnty ID="5" xml:lang="ja" affiliation="author.affiliation">test, taro</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt><distrbtr URI="https://test.distributor.affiliation" abbr="TDN" xml:lang="ja" affiliation="Test Distributor Affiliation">Test Distributor Name</distrbtr></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75" /></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe><dataKind xml:lang="ja">量的調査</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit><dataKind xml:lang="en">quantatitive research</dataKind></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo /></method><dataAccs xml:lang="jp"><setAvail><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[1], _counter, None)
    assert res==None
    
    ## json_data['item_1593074267803'][0]['creatorNames'][0]['creatorNameLang'] != json_data['item_1593074267803'][n]['creatorNames'][0]['creatorNameLang']
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000080">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><rspStmt><AuthEnty ID="4" xml:lang="en" affiliation="author.affiliation">test, taro</AuthEnty><AuthEnty xml:lang="ja" affiliation="author.affiliation">テスト, 太郎</AuthEnty><AuthEnty xml:lang="ja" affiliation="author.affiliation">テスト, 花子</AuthEnty><AuthEnty xml:lang="en" affiliation="author.affiliation">test, hanako</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt><distrbtr URI="https://test.distributor.affiliation" abbr="TDN" xml:lang="ja" affiliation="Test Distributor Affiliation">Test Distributor Name</distrbtr></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75" /></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe><dataKind xml:lang="ja">量的調査</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit><dataKind xml:lang="en">quantatitive research</dataKind></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo /></method><dataAccs xml:lang="jp"><setAvail><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[1], _counter, None)
    assert res==None
    
    ## exist item_1588260046718,item_1592405734122,item_1600078832557 in json_data
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000081">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><rspStmt><AuthEnty ID="4" xml:lang="ja" affiliation="author.affiliation">テスト, 太郎</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt><distrbtr URI="https://test.distributor.affiliation" abbr="TDN" xml:lang="ja" affiliation="Test Distributor Affiliation">Test Distributor Name</distrbtr></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75" /></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe><dataKind xml:lang="ja">量的調査</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit><dataKind xml:lang="en">quantatitive research</dataKind></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo /></method><dataAccs xml:lang="jp"><setAvail><accsPlac>http://test.url.com</accsPlac><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><accsPlac>http://test.url.com</accsPlac><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[1], _counter, None)
    assert res==None
    
    ## exist item_1588260046718,item_1592405734122,item_1600078832557 not in json_data
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000082">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><rspStmt><AuthEnty ID="4" xml:lang="ja" affiliation="author.affiliation">テスト, 太郎</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75" /></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo /></method><dataAccs xml:lang="jp"><setAvail><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[1], _counter, None)
    assert res==None
    
    ## exist identifier
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000083">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><rspStmt><AuthEnty ID="4" xml:lang="ja" affiliation="author.affiliation">テスト, 太郎</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75" /><holdings>http://doi.org/test_doi1</holdings><holdings>http://doi.org/test_doi2</holdings><holdings>http://hdl.handle.net/test_doi</holdings></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo /></method><dataAccs xml:lang="jp"><setAvail><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    res = process_item(_records[0], harvest_setting[1], _counter, None)
    assert res==None

    
    # oai_dc
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-01T02:07:10Z</responseDate><request metadataPrefix="oai_dc" identifier="oai:weko3.example.org:00000021" verb="GetRecord">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns="http://www.w3.org/2001/XMLSchema" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"><dc:title xml:lang="ja">test full item</dc:title><dc:creator>テスト, 太郎</dc:creator><dc:creator>1</dc:creator><dc:creator>1234</dc:creator><dc:subject>テスト主題</dc:subject><dc:description>this is test abstract.</dc:description><dc:publisher>test publisher</dc:publisher><dc:contributor>test, smith</dc:contributor><dc:contributor>2</dc:contributor><dc:contributor>5678</dc:contributor><dc:date>2022-10-20</dc:date><dc:type>conference paper</dc:type><dc:identifier>1111</dc:identifier><dc:source>test collectibles</dc:source><dc:language>jpn</dc:language><dc:relation>1111111</dc:relation><dc:coverage>1 to 2</dc:coverage><dc:rights>metadata only access</dc:rights><dc:format>text/plain</dc:format></oai_dc:dc></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    with patch('weko_search_ui.utils.send_item_created_event_to_es', return_value=None):
        res = process_item(_records[0], harvest_setting[2], _counter, None)
        assert res==None
        
    # other_prefix
    with patch('weko_search_ui.utils.send_item_created_event_to_es', return_value=None):
        res = process_item(_records[0], harvest_setting[3], _counter, None)
        assert res==None
    
    # hvstid is none, is_deleted is True
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-01T02:07:10Z</responseDate><request metadataPrefix="jpcoar_1.0" identifier="oai:weko3.example.org:00000001" verb="GetRecord">https://192.168.56.103/oai</request><GetRecord><record><header status="deleted"><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp></header></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    mock_delete = mocker.patch("invenio_oaiharvester.tasks.soft_delete")
    res = process_item(_records[0], harvest_setting[0], _counter, None)
    mock_delete.assert_called_with("1")
    assert res == None

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_process_item_for_jpcoar2_coverage_and_no_errors -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_process_item_for_jpcoar2_coverage_and_no_errors(app, db, esindex, location, db_itemtype, harvest_setting, db_records):
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2020-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    jpcoar_setting2 = HarvestSettings(
        id=10,
        repository_name="jpcoar_test2",
        base_url="http://export.arxiv.org/oai2",
        from_date=datetime(2022, 10, 1),
        until_date=datetime(2022, 10, 2),
        metadata_prefix="jpcoar_2.0",
        index_id=2,
        update_style="1",
        auto_distribution="0"
    )
    with db.session.begin_nested():
        db.session.add(jpcoar_setting2)
    db.session.commit()
    res = process_item(_records[0], jpcoar_setting2, _counter, None)

    # line 168 elif harvesting.metadata_prefix == 'jpcoar_2.0' coverage and no errors
    assert res==None
    

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_link_success_handler -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_link_success_handler(app,mocker):
    mock_send = mocker.patch("invenio_oaiharvester.tasks.oaiharvest_finished.send")
    link_success_handler.delay([{"task_id":"test_task"},{"user":"data"}])
    args, kwargs = mock_send.call_args
    assert kwargs["exec_data"] == {"task_id":"test_task"}
    assert kwargs["user_data"] == {"user":"data"}
    
    
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_link_error_handler -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_link_error_handler(app,mocker):
    from celery.worker.request import Request
    headers = {
        "id":"test_id",
        "task":"test_task",
        "argsrepr":'["","2022-10-01T12:01:22","user_data"]'
    }
    class Message:
        body=("test_args","test_kwargs","")
        decoded=True
        payload="test_payload"
        delivery_info=None
        properties=None
    req = Request(Message,headers=headers,task="test_task",decoded=True)
    mock_send = mocker.patch("invenio_oaiharvester.tasks.oaiharvest_finished.send")
    link_error_handler(req,None,None)
    args, kwargs = mock_send.call_args
    exec_data = kwargs["exec_data"]
    assert exec_data["task_state"] == "FAILURE"
    assert exec_data["start_time"] == "2022-10-01T12:01:22"
    assert kwargs["user_data"] == "user_data"

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_is_harvest_running -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_is_harvest_running(app,mocker):
    # return true
    data = {
        "celery@7c520e3d1839":[
            {
                "id":"test_task1",
                "name":"invenio_oaiharvester.tasks.run_harvesting",
                "args":[
                    "test_id"
                ]
            }
        ]
    }
    with patch("celery.app.control.Inspect.active",return_value=data):
        result = is_harvest_running("test_id","task_id")
        assert result == True
    
    # return false
    data = {
        "celery@7c520e3d1839":[
            {# task[args][0] != id
                "id":"test_task1",
                "name":"invenio_oaiharvester.tasks.run_harvesting",
                "args":["not_id"]
            },
            {# task[name] != invenio_oaiharvester.tasks.run_harvesting
                "id":"test_task2",
                "name":"weko_search_ui.tasks.import_item",
                "args":[]
            },
        ]
    }
    with patch("celery.app.control.Inspect.active",return_value=data):
        result = is_harvest_running("test_id","task_id")
        assert result == False


# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_run_harvesting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
@responses.activate
def test_run_harvesting(app, db,mocker):
    mocker.patch("invenio_oaiharvester.tasks.send_run_status_mail")
    index = Index()
    db.session.add(index)
    db.session.commit()
    # result with resumptiontoken
    body1 = \
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
        '<responseDate>2023-03-01T10:54:40Z</responseDate>'\
        '<request verb="ListRecords" metadataPrefix="jpcoar_1.0">https://192.168.56.103/oai</request>'\
        '<ListRecords>'\
        '<resumptionToken>test_token</resumptionToken>'\
        '<record>test_record1</record>'\
        '<record>test_record2</record>'\
        '</ListRecords>'\
        '</OAI-PMH>'
    # result without resummptiontoken
    body2 = \
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
        '<responseDate>2023-03-01T10:54:40Z</responseDate>'\
        '<request verb="ListRecords" metadataPrefix="jpcoar_1.0">https://192.168.56.103/oai</request>'\
        '<ListRecords>'\
        '<record>test_record3</record>'\
        '<record>test_record4</record>'\
        '</ListRecords>'\
        '</OAI-PMH>'
    responses.add(
        responses.GET,
        "http://export.arxiv.org/oai2/?verb=ListRecords&from=2022-10-01&until=2022-10-02&metadataPrefix=jpcoar_1.0",
        body=body1,
        content_type='text/xml'
    )
    responses.add(
        responses.GET,
        "http://export.arxiv.org/oai2/?verb=ListRecords&metadataPrefix=jpcoar_1.0&resumptionToken=test_token",
        body=body2,
        content_type='text/xml'
    )
    body3 = \
    '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
        '<request verb="ListSets">https://192.168.56.103/oai</request>'\
        '<ListSets>'\
            '<set>'\
                '<setSpec>test_repo3</setSpec>'\
            '</set>'\
            '<set>'\
                '<setSpec>test_repo4</setSpec>'\
            '</set>'\
        '</ListSets>'\
    '</OAI-PMH>'
    responses.add(
        responses.GET,
        "http://export.arxiv.org/oai2/?verb=ListSets",
        body=body3,
        content_type='text/xml'
    )
    
    jpcoar_setting1 = HarvestSettings(
        id=1,
        repository_name="jpcoar_test1",
        base_url="http://export.arxiv.org/oai2/",
        from_date=datetime(2022, 10, 1),
        until_date=datetime(2022, 10, 2),
        metadata_prefix="jpcoar_1.0",
        index_id=1,
        update_style="0",
        auto_distribution="1"
    )
    jpcoar_setting2 = HarvestSettings(
        id=2,
        repository_name="jpcoar_test2",
        base_url="http://export.arxiv.org/oai2/",
        from_date=datetime(2022, 10, 1),
        until_date=datetime(2022, 10, 2),
        metadata_prefix="jpcoar_1.0",
        index_id=1,
        update_style="0",
        auto_distribution="0",
        resumption_token="test_token"
    )
    logs = HarvestLogs(
        id=1,
        harvest_setting_id=2
    )
    with db.session.begin_nested():
        db.session.add(jpcoar_setting1)
        db.session.add(jpcoar_setting2)
        db.session.add(logs)
        db.session.execute("SELECT setval('harvest_logs_id_seq', 1)")
    db.session.commit()

    # is_harvest_running is True
    with patch('invenio_oaiharvester.tasks.is_harvest_running', return_value=True):
        res = run_harvesting(1, '2022-10-01T00:00:00', '2022-10-01T23:59:59', {})
        assert res == ({"task_state":"SUCCESS","task_id":None},"2022-10-01T23:59:59")
        #assert res==({'task_state': 'SUCCESS', 'start_time': '2022-10-01T00:00:00', 'end_time': res[0]['end_time'], 'total_records': 0, 'execution_time': res[0]['execution_time'], 'task_name': 'harvest', 'repository_name': 'weko', 'task_id': None}, '2022-10-01T23:59:59')
    
    with patch('invenio_oaiharvester.tasks.is_harvest_running', return_value=False):
        with patch("invenio_oaiharvester.tasks.process_item"):
            res = run_harvesting(1, '2022-10-01T00:00:00', '2022-10-01T23:59:59', {})
            assert res == ({"task_state":"SUCCESS","start_time":"2022-10-01T00:00:00","end_time":res[0]["end_time"],"total_records":0,"execution_time":res[0]['execution_time'],"task_name":"harvest","repository_name":"weko","task_id":None},"2022-10-01T23:59:59")
            log = HarvestLogs.query.filter_by(id=2,harvest_setting_id=1).one()
            assert log.status == "Successful"
            
            res = run_harvesting(2, '2022-10-01T00:00:00', '2022-10-01T23:59:59', {})
            log = HarvestLogs.query.filter_by(id=1,harvest_setting_id=2).one()
            assert log.status == "Successful"
        
        with patch("invenio_oaiharvester.tasks.process_item",side_effect=Exception("test_error")):
            res = run_harvesting(1, '2022-10-01T00:00:00', '2022-10-01T23:59:59', {})
            assert res == ({'task_state': 'SUCCESS', 'start_time': '2022-10-01T00:00:00', 'end_time': res[0]["end_time"], 'total_records': 0, 'execution_time': res[0]['execution_time'], 'task_name': 'harvest', 'repository_name': 'weko', 'task_id': None}, '2022-10-01T23:59:59')
            log = HarvestLogs.query.filter_by(id=3,harvest_setting_id=1).one()
            assert log.counter == {'processed_items': 0, 'created_items': 0, 'updated_items': 0, 'deleted_items': 0, 'error_items': 4}
            assert log.status == "Successful"
        
        with patch("invenio_oaiharvester.tasks.DCMapper.update_itemtype_map",side_effect=Exception("test_error")):
            res = run_harvesting(1, '2022-10-01T00:00:00', '2022-10-01T23:59:59', {})
            assert res == ({'task_state': 'SUCCESS', 'start_time': '2022-10-01T00:00:00', 'end_time': res[0]["end_time"], 'total_records': 0, 'execution_time': res[0]['execution_time'], 'task_name': 'harvest', 'repository_name': 'weko', 'task_id': None}, '2022-10-01T23:59:59')
            log = HarvestLogs.query.filter_by(id=4,harvest_setting_id=1).one()
            assert log.counter == {'processed_items': 0, 'created_items': 0, 'updated_items': 0, 'deleted_items': 0, 'error_items': 0}
            assert log.status == "Failed"
            
        import time
        def mock_process_item(record=None,harvesting=None,counter=None,request_info=None):
            pid = os.getpid()
            os.kill(pid, signal.SIGTERM)
        with patch("invenio_oaiharvester.tasks.process_item",side_effect=mock_process_item):
            res = run_harvesting(1, '2022-10-01T00:00:00', '2022-10-01T23:59:59', {})
            
            assert res == ({'task_state': 'SUCCESS', 'start_time': '2022-10-01T00:00:00', 'end_time': res[0]["end_time"], 'total_records': 0, 'execution_time': res[0]['execution_time'], 'task_name': 'harvest', 'repository_name': 'weko', 'task_id': None}, '2022-10-01T23:59:59')
        

# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_check_schedules_and_run -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_check_schedules_and_run(app,db,mocker):
    index = Index()
    db.session.add(index)
    db.session.commit()
    now = datetime.utcnow()
    # schedule_enable is true,schedule_frequency is daily
    setting1 = HarvestSettings(
        id=1,
        repository_name="setting1",
        base_url="http://test.org",
        metadata_prefix="jpcoar_1.0",
        index_id=1,
        schedule_enable=True,
        schedule_frequency="daily"
    )
    # schedule_enable is true,schedule_frequency is weekly and schedule_details != weekday
    setting2 = HarvestSettings(
        id=2,
        repository_name="setting2",
        base_url="http://test.org",
        metadata_prefix="jpcoar_1.0",
        index_id=1,
        schedule_enable=True,
        schedule_frequency="weekly",
        schedule_details=now.weekday()+1
    )
    # schedule_enable is false
    setting3 = HarvestSettings(
        id=3,
        repository_name="setting3",
        base_url="http://test.org",
        metadata_prefix="jpcoar_1.0",
        index_id=1,
        schedule_enable=False
    )
    db.session.add_all([setting1,setting2,setting3])
    db.session.commit()
    mock_delay = mocker.patch("invenio_oaiharvester.tasks.run_harvesting.delay")
    check_schedules_and_run.delay()
    mock_delay.assert_called_once()
    args,kwargs = mock_delay.call_args
    assert args[0] == 1
    assert args[2] == {'ip_address': "",'user_agent': "",'user_id': -1,'session_id': ""}
    assert args[3] == {"remote_addr": "","referrer": "","hostname": "","user_id": -1,"action":"HARVEST"}