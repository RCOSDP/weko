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

import pytest
import responses
from mock import patch
from invenio_db import db
from weko_index_tree.models import Index
from lxml import etree

from invenio_oaiharvester.errors import InvenioOAIHarvesterError
from invenio_oaiharvester.models import HarvestSettings
from invenio_oaiharvester.signals import oaiharvest_finished
from invenio_oaiharvester.tasks import create_indexes, event_counter, \
    get_specific_records, list_records_from_dates, map_indexes, \
    process_item, run_harvesting


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
    finally:
        oaiharvest_finished.disconnect(foo)


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
    finally:
        oaiharvest_finished.disconnect(bar)


@responses.activate
def test_list_records_from_dates(app, sample_list_xml):
    """Check harvesting of records from multiple setspecs."""
    try:
        with app.app_context():
            index = Index()
            db.session.add(index)
            db.session.commit()

            harvesting = HarvestSettings(
                repository_name='name',
                base_url='https://jpcoar.repo.nii.ac.jp/oai',
                metadata_prefix='jpcoar_1.0',
                index_id=index.id,
                update_style='0',
                auto_distribution='0')
            db.session.add(harvesting)
            db.session.commit()

            # run_harvesting(
            #     harvesting.id,
            #     datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'),
            #     {'ip_address': '0.0,0.0',
            #         'user_agent': '',
            #         'user_id': 1,
            #         'session_id': '1'}
            # )
    finally:
        return


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


def test_map_indexes(app, db):
    """Check harvesting of records from multiple setspecs."""
    with app.app_context():
        index = Index()
        db.session.add(index)
        db.session.commit()

        map_indexes({
            '1': 'set_name_1',
            '2': 'set_name_2'
        }, index.id)


def test_event_counter(app):
    """Check harvesting of records from multiple setspecs."""
    counter = {}

    event_counter('a', counter)
    event_counter('a', counter)


# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_process_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_process_item(app, db, esindex, location, db_itemtype, harvest_setting):
    # jpcoar
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2022-10-25T07:35:11Z</responseDate><request verb="ListRecords" metadataPrefix="jpcoar_1.0">https://repository.dl.itc.u-tokyo.ac.jp/oai</request><ListRecords><record><header><identifier>oai:repository.dl.itc.u-tokyo.ac.jp:00000007</identifier><datestamp>2021-03-02T08:39:23Z</datestamp></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title>A new insight into the growth mode of metals on TiO2(110)</dc:title><jpcoar:creator><jpcoar:creatorName>Hu, Minghui</jpcoar:creatorName></jpcoar:creator><jpcoar:creator><jpcoar:creatorName>Noda, Suguru</jpcoar:creatorName></jpcoar:creator><jpcoar:creator><jpcoar:creatorName>Komiyama, Hiroshi</jpcoar:creatorName></jpcoar:creator><jpcoar:subject subjectScheme="NDC">431.86</jpcoar:subject><jpcoar:subject subjectScheme="Other">Growth</jpcoar:subject><jpcoar:subject subjectScheme="Other">Single crystal surfaces</jpcoar:subject><jpcoar:subject subjectScheme="Other">Titanium oxide</jpcoar:subject><jpcoar:subject subjectScheme="Other">Metallic films</jpcoar:subject><jpcoar:subject subjectScheme="Other">Surface chemical reaction</jpcoar:subject><jpcoar:subject subjectScheme="Other">Wetting</jpcoar:subject><datacite:description descriptionType="Other">application/pdf</datacite:description><dc:publisher>Elsevier</dc:publisher><datacite:date dateType="Issued">2002-08-01</datacite:date><dc:language>eng</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_6501">journal article</dc:type><jpcoar:identifier identifierType="HDL">http://hdl.handle.net/2261/12</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://repository.dl.itc.u-tokyo.ac.jp/records/7</jpcoar:identifier><jpcoar:sourceIdentifier identifierType="NCID">AA00853803</jpcoar:sourceIdentifier><jpcoar:sourceIdentifier identifierType="ISSN">00396028</jpcoar:sourceIdentifier><jpcoar:sourceTitle>Surface science</jpcoar:sourceTitle><jpcoar:volume>513</jpcoar:volume><jpcoar:issue>3</jpcoar:issue><jpcoar:pageStart>530</jpcoar:pageStart><jpcoar:pageEnd>538</jpcoar:pageEnd><jpcoar:file><jpcoar:URI label="2002SS_hu.pdf">https://repository.dl.itc.u-tokyo.ac.jp/record/7/files/2002SS_hu.pdf</jpcoar:URI><jpcoar:mimeType>application/pdf</jpcoar:mimeType><jpcoar:extent>247.5 kB</jpcoar:extent><datacite:date dateType="Available">2017-05-30</datacite:date></jpcoar:file></jpcoar:jpcoar></metadata></record></ListRecords></OAI-PMH>')
    _records = _etree.findall('./ListRecords/record', namespaces=_etree.nsmap)
    _counter = {}

    with patch('weko_search_ui.utils.send_item_created_event_to_es', return_value=None):
        res = process_item(_records[0], harvest_setting[0], _counter, None)
        assert res==None

    # ddi
    _etree = etree.fromstring('<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2022-11-01T07:24:43Z</responseDate><request verb="GetRecord" metadataPrefix="ddi" identifier="oai:invenio:00000002">https://data.lib.keio.ac.jp/oai</request><GetRecord><record><header><identifier>oai:invenio:00000002</identifier><datestamp>2021-06-24T14:23:51Z</datestamp></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="en"><titlStmt><titl xml:lang="en">Japanese Panel Survey of Consumers: 1994</titl><altTitl xml:lang="en">JPSC</altTitl><IDNo>JPSC2</IDNo></titlStmt><rspStmt><AuthEnty xml:lang="en">Institute for Research on Household ECONOMICS</AuthEnty></rspStmt><prodStmt><producer xml:lang="en">Panel Data Research Center at Keio University</producer><copyright xml:lang="en">Before your application, you need to agree with our written pledge (e.g. the data will be only use for research purpose, will not be provided any third party etc).</copyright></prodStmt><distStmt><distrbtr xml:lang="en">Panel Data Research Center at Keio University</distrbtr></distStmt><serStmt><serName xml:lang="en">Japanese Panel Survey of Consumers(JPSC) Series</serName></serStmt><verStmt><notes>jpn</notes><notes>eng</notes></verStmt><biblCit xml:lang="en">Publications in academic journals, academic societies, and media articles based on analysis of data provided by the PDRC must be credited to the Panel Data Research Center at Keio University.\n\n(Example)\nThe data for this analysis, Japanese Panel Survey of Consumers (JPSC), was provided by the Keio University Panel Data Research Center.</biblCit><holdings URI="https://data.lib.keio.ac.jp/records/2"/></citation><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">消費生活に関するパネル調査 (JPSC) 1994</titl><altTitl xml:lang="ja">JPSC</altTitl><IDNo>JPSC2</IDNo></titlStmt><rspStmt><AuthEnty xml:lang="ja">家計経済研究所</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">慶應義塾大学パネルデータ設計・解析センター</producer><copyright xml:lang="ja">詳しくは、データ申請時に表示される誓約書を確認してください。</copyright></prodStmt><distStmt><distrbtr xml:lang="ja">慶應義塾大学パネルデータ設計・解析センター</distrbtr></distStmt><serStmt><serName xml:lang="ja">消費生活に関するパネル調査(JPSC)シリーズ</serName></serStmt><verStmt><notes>jpn</notes><notes>eng</notes></verStmt><biblCit xml:lang="ja">学術誌あるいは学会等で分析結果を発表する際は、慶應義塾大学パネルデータ設計・解析センターから各データの個票データの提供を受けた旨を必ず明記して下さい。\n\n例: 本稿の分析に際しては、慶應義塾大学パネルデータ設計・解析センターによる「消費生活に関するパネル調査(JPSC)」の個票データの提供を受けた。\n\nThe data for this analysis, Japanese Panel Survey of Consumers (JPSC), was provided by the Keio University Panel Data Research Center.</biblCit><holdings URI="https://data.lib.keio.ac.jp/records/2"/></citation><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">ECONOMICS</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Income, property and investment/saving</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">HEALTH</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Drug abuse, alcohol and smoking</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">General health and well-being</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Reproductive health</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">HOUSING AND LAND USE</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Housing</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">LABOUR AND EMPLOYMENT</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Employment</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Working conditions</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">SOCIAL STRATIFICATION AND GROUPINGS</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Family life and marriage</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Gender and gender roles</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Social and occupational mobility</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">SOCIETY AND CULTURE</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Time use</topcClas></subject><abstract xml:lang="en">The JPSC started in 1993 with a sample of 1,500 young woman (aged from 24 to 34 years) and their spouses. The objective was to examine the lifestyles of relatively young woman from a wide spectrum of factors, including income, expenditure, savings, work patterns, and family relationships. Since then, the survey has been conducted annually and expanded to include new cohorts in 1997 (500 respondents), 2003 (836 respondents), 2008 (636 respondents), and 2013 (672 respondents).</abstract><sumDscr><timePrd event="start">1993</timePrd><timePrd event="end">1994</timePrd><collDate>1994</collDate><geogCover xml:lang="en">Japan</geogCover><anlyUnit xml:lang="en">Individual</anlyUnit><anlyUnit xml:lang="en">Family</anlyUnit><anlyUnit xml:lang="en">Family: Household family</anlyUnit><anlyUnit xml:lang="en">Household</anlyUnit><universe xml:lang="en">Japanese female over 24</universe><dataKind xml:lang="en">quantitative research: micro data</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="ja"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">経済</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">所得、財産、投資・貯蓄</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">健康</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">薬物乱用、アルコール、喫煙</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">健康一般とウェルビーイング</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">リプロダクティブヘルス</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">住宅と土地利用</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">住宅</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">労働と雇用</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">雇用</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">労働条件</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">社会階層と社会集団</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">家族生活と結婚</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">ジェンダーと性別役割</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">社会移動と職業移動</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">社会と文化</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">生活時間</topcClas></subject><abstract xml:lang="ja">1993年に当時24歳から34歳の女性1,500名とその配偶者を対象に、若年女性の生活実態を、収入・支出・貯蓄、就業行動、家族関係などの諸側面から明らかにすることを目的としています。1997年(500名)、2003年(836名)、2008年(636名)、2013年(672名)に新規調査対象者が追加され、現在まで調査が続いています。</abstract><sumDscr><timePrd event="start">1993</timePrd><timePrd event="end">1994</timePrd><collDate>1994</collDate><geogCover xml:lang="ja">日本</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><anlyUnit xml:lang="ja">家族</anlyUnit><anlyUnit xml:lang="ja">家族: 世帯家族</anlyUnit><anlyUnit xml:lang="ja">世帯</anlyUnit><universe xml:lang="ja">日本の24歳以上の女性</universe><dataKind xml:lang="ja">量的調査: ミクロデータ</dataKind></sumDscr></stdyInfo><method xml:lang="en"><dataColl><sampProc xml:lang="en">Mixed probability and non-probability</sampProc><collMode xml:lang="en">Self-administered questionnaire</collMode></dataColl></method><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">混合確率と非確率</sampProc><collMode xml:lang="ja">自記式調査票</collMode></dataColl></method><dataAccs xml:lang="en"><setAvail><accsPlac>https://www.pdrc.keio.ac.jp/pdrc/</accsPlac><avlStatus xml:lang="en">restricted access</avlStatus></setAvail></dataAccs><dataAccs xml:lang="ja"><setAvail><accsPlac>https://www.pdrc.keio.ac.jp/pdrc/</accsPlac><avlStatus xml:lang="ja">制約付きアクセス</avlStatus></setAvail></dataAccs><othrStdyMat><relStdy ID="https://www.pdrc.keio.ac.jp/en/paneldata/datasets/"/><relPubl ID="https://www.pdrc.keio.ac.jp/jpsc/bunken/result-1994/"/></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>')
    _records = _etree.findall('./GetRecord/record', namespaces=_etree.nsmap)
    _counter = {}
    with patch('weko_search_ui.utils.send_item_created_event_to_es', return_value=None):
        res = process_item(_records[0], harvest_setting[1], _counter, None)
        assert res==None


# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_tasks.py::test_run_harvesting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_run_harvesting(app, db, harvest_setting):
    with patch('invenio_oaiharvester.tasks.is_harvest_running', return_value=False):
        res = run_harvesting(1, '2022-10-01T00:00:00', '2022-10-01T23:59:59', {})
        assert res==({'task_state': 'SUCCESS', 'start_time': '2022-10-01T00:00:00', 'end_time': res[0]['end_time'], 'total_records': 0, 'execution_time': res[0]['execution_time'], 'task_name': 'harvest', 'repository_name': 'weko', 'task_id': None}, '2022-10-01T23:59:59')
