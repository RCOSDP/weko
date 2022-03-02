# -*- coding: utf-8 -*-

from collections import OrderedDict

import pytest

from weko_records.utils import convert_date_range_value, convert_range_value, \
    copy_value_json_path, copy_values_json_path, makeDateRangeValue


@pytest.fixture
def identifiers():
    identifier = ['oai:weko3.example.org:00000965']
    return identifiers

@pytest.fixture
def k_v():
    k_v = [{'id': 'date_range1', 'mapping': [], 'contents': '', 'inputType': 'dateRange', 'input_Type': 'range', 'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}, '12': {'path': {'gte': '$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211', 'lte': '$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211'}, 'path_type': {'gte': 'json', 'lte': 'json'}}}, 'mappingFlg': False, 'inputVal_to': '', 'mappingName': '', 'inputVal_from': '', 'contents_value': {'en': 'date_EN_1', 'ja': 'date_JA_1'}, 'useable_status': True, 'default_display': True}, {"id": "text3", "mapping": [], "contents": "", "inputVal": "", "inputType": "text", "input_Type": "text", "item_value":  {"1": {"path": "", "path_type": "json"}, "12": {"path": "$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890", "path_type": "json"}, "20": {"path": "$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890", "path_type": "json"}}, "mappingFlg": False, "mappingName": "", "contents_value": {"en": "Summary", "ja": "概要"}, "useable_status": True, "default_display": True}
           ]
    return k_v




@pytest.fixture
def jsonpath():
    return ['$.item_1551264418667.attribute_value_mlt[*].subitem_1551257245638[*].subitem_1551257276108', '$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211', 
    '$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890',
    '$.item_1551264846237.attribute_value_mlt[1:3].subitem_1551255577890']


@pytest.fixture
def meta():
    return [OrderedDict(
        [('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2021-10-26'}),
         ('item_1551264308487', {'attribute_name': 'Title', 'attribute_value_mlt': [
             {'subitem_1551255647225': 'タイトル日本語', 'subitem_1551255648112': 'ja'},
             {'subitem_1551255647225': 'Title', 'subitem_1551255648112': 'en'}]}),
         ('item_1551264340087', {'attribute_name': 'Creator', 'attribute_value_mlt':
                                 [{'subitem_1551255898956': [{'subitem_1551255905565': '作者', 'subitem_1551255907416': 'ja'}]}]}),
         ('item_1551264447183', {'attribute_name': 'Access Rights', 'attribute_value_mlt':
                                 [{'subitem_1551257553743': 'open access', 'subitem_1551257578398': 'http://purl.org/coar/access_right/c_abf2'}]}),
         ('item_1551264418667', {'attribute_name': 'Contributor', 'attribute_value_mlt':
                                 [{'subitem_1551257036415': 'Distributor', 'subitem_1551257339190':
                                   [{'subitem_1551257342360': ''}], 'subitem_1551257245638':
                                   [{'subitem_1551257276108': '寄与者', 'subitem_1551257279831': 'ja'},
                                    {'subitem_1551257276108': 'Contributor', 'subitem_1551257279831': 'en'}]}]}),
         ('item_1551264822581', {'attribute_name': 'Subject', 'attribute_value_mlt':
                                 [{'subitem_1551257315453': '日本史', 'subitem_1551257323812': 'ja', 'subitem_1551257329877': 'NDC'},
                                  {'subitem_1551257315453': 'General History of Japan', 'subitem_1551257323812': 'en',
                                   'subitem_1551257329877': 'NDC'}]}), ('item_1551265227803',
                                                                        {'attribute_name': 'Relation', 'attribute_value_mlt':
                                                                         [{'subitem_1551256388439': 'references', 'subitem_1551256465077':
                                                                           [{'subitem_1551256478339': 'localid', 'subitem_1551256629524': 'Local'}]}]}),
         ('item_1551264974654', {'attribute_name': 'Date', 'attribute_value_mlt':
                                 [{'subitem_1551255753471': '2000-01-01'}, {'subitem_1551255753471': '2012-06-11'},
                                  {'subitem_1551255753471': '2016-05-24'}]}),
         ('item_1551264846237', {'attribute_name': 'Description', 'attribute_value_mlt':
                                 [{'subitem_1551255577890': '概要', 'subitem_1551255592625': 'ja', 'subitem_1551255637472': 'Abstract'},
                                  {'subitem_1551255577890': 'その他', 'subitem_1551255592625': 'ja',
                                      'subitem_1551255637472': 'Other'},
                                  {'subitem_1551255577890': 'materials: text', 'subitem_1551255592625': 'en', 'subitem_1551255637472': 'Other'}]}),
         ('item_1551265002099', {'attribute_name': 'Language', 'attribute_value_mlt': [
          {'subitem_1551255818386': 'jpn'}]}),
         ('item_1551265032053', {'attribute_name': 'Resource Type', 'attribute_value_mlt':
                                 [{'resourcetype': 'manuscript', 'resourceuri': 'http://purl.org/coar/resource_type/c_0040'}]}),
         ('item_1551265302120', {'attribute_name': 'Temporal', 'attribute_value_mlt': [
          {'subitem_1551256918211': '2000-01-01/2021-03-30'}]}),
         ('item_title', 'タイトル日本語'),
         ('item_type_id', '12'), ('control_number', '870')])]


def test_copy_value_json_path(meta, jsonpath):
    assert copy_value_json_path(meta[0], jsonpath[0]) == '寄与者'
    assert copy_value_json_path(
        meta[0], jsonpath[1]) == '2000-01-01/2021-03-30'
    assert copy_value_json_path(
        meta[0], jsonpath[2]) == '概要'


def test_copy_values_json_path(meta, jsonpath):
    assert copy_values_json_path(meta[0], jsonpath[0]) == [
        '寄与者', 'Contributor']
    assert copy_values_json_path(meta[0], jsonpath[1]) == [
        '2000-01-01/2021-03-30']
    assert copy_values_json_path(meta[0], jsonpath[2]) == [
        '概要', 'その他', 'materials: text']
    assert copy_values_json_path(meta[0], jsonpath[3]) == [
        'その他', 'materials: text']


def test_convert_date_range_value():
    assert convert_date_range_value('1762-01-26/1762-02-23') == {'gte': '1762-01-26',
                                                                 'lte': '1762-02-23'}
    assert convert_date_range_value('2000-01-01/2021-03-30') == {'gte': '2000-01-01',
                                                                 'lte': '2021-03-30'}

    assert convert_date_range_value(' 1762-01-26/1762-02-23 ') == {'gte': '1762-01-26',
                                                                   'lte': '1762-02-23'}

    assert convert_date_range_value('2000-01/2021-03') == {'gte': '2000-01',
                                                           'lte': '2021-03'}
    assert convert_date_range_value('2000/2021') == {'gte': '2000',
                                                     'lte': '2021'}
    assert convert_date_range_value('2000-01-01') == {'gte': '2000-01-01',
                                                      'lte': '2000-01-01'}
    assert convert_date_range_value('2000-01') == {'gte': '2000-01',
                                                   'lte': '2000-01'}
    assert convert_date_range_value('2000') == {'gte': '2000',
                                                'lte': '2000'}
    assert convert_date_range_value('2000-01-01', '2000-12-01') == {'gte': '2000-01-01',
                                                                    'lte': '2000-12-01'}


def test_convert_range_value():
    assert convert_range_value('1', '2') == {'gte': '1', 'lte': '2'}


def test_convert_date_range_value():
    assert convert_date_range_value(
        '1979-01-01/1960-01-01') == {'gte': '1960-01-01', 'lte': '1979-01-01'}


def test_makeDateRangeValue():
    assert makeDateRangeValue('1979', '1960') == {
        'gte': '1960', 'lte': '1979'}
    assert makeDateRangeValue('1979-01-01', '1960-01-01') == {
        'gte': '1960-01-01', 'lte': '1979-01-01'}
    assert makeDateRangeValue('1979-01', '1960-01') == {
        'gte': '1960-01', 'lte': '1979-01'}
    assert makeDateRangeValue('1979-01-01', '1979-12-30') == {
        'gte': '1979-01-01', 'lte': '1979-12-30'}
    assert makeDateRangeValue('1979-01-01', '1979-01-01') == {
        'gte': '1979-01-01', 'lte': '1979-01-01'}
    assert makeDateRangeValue('1979/01/01', '1979/12/30') == None
