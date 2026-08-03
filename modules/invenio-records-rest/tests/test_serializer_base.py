# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio serializer tests."""

from __future__ import absolute_import, print_function

from datetime import datetime
from mock import patch, MagicMock

from tests.helpers import create_record, json_data
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record

from invenio_records_rest.serializers.base import PreprocessorMixin
from weko_records.api import ItemType

keys = ['pid', 'metadata', 'links', 'revision', 'created', 'updated']


def test_preprocessor_mixin_record(app, db,item_type_mapping):
    """Test preprocessor mixin."""
    pid, record = create_record({'title': 'test', 'aref': {'$ref': '#/title'}})
    record.model.created = datetime(2015, 10, 1, 11, 11, 11, 1)
    db.session.commit()

    data = PreprocessorMixin().preprocess_record(pid, record)
    for k in keys:
        assert k in data

    assert data['metadata']['title'] == 'test'
    assert data['metadata']['aref'] == {'$ref': '#/title'}
    assert data['created'] == '2015-10-01T11:11:11.000001+00:00'
    assert data['revision'] == 1

    data = PreprocessorMixin(replace_refs=True).preprocess_record(
        pid, Record({'title': 'test2', 'aref': {'$ref': '#/title'}}))
    assert data['created'] is None
    assert data['updated'] is None
    assert data['metadata']['aref'] == 'test2'

    pid, record = create_record({'title': 'test3', 'aref':{'$ref':'#/title'},'item_type_id':1})
    record.model.created = datetime(2015, 10, 1, 11, 11, 11, 1)
    db.session.commit()
    ret = {'pubdate': {'title': 'PubDate', 'option': {'crtf': False, 'hidden': False, 'multiple': False, 'required': True, 'showlist': False}, 'input_type': 'datetime', 'title_i18n': {'en': 'PubDate', 'ja': '公開日'}, 'input_value': ''}, 'item_1617186331708': {'title': 'Title', 'option': {'crtf': True, 'hidden': False, 'oneline': False, 'multiple': True, 'required': True, 'showlist': True}, 'input_type': 'cus_67', 'title_i18n': {'en': 'Title', 'ja': 'タイトル'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186385884': {'title': 'Alternative Title', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_69', 'title_i18n': {'en': 'Alternative Title', 'ja': 'その他のタイトル'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186419668': {'title': 'Creator', 'option': {'crtf': True, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_60', 'title_i18n': {'en': 'Creator', 'ja': '作成者'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186476635': {'title': 'Access Rights', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_4', 'title_i18n': {'en': 'Access Rights', 'ja': 'アクセス権'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186499011': {'title': 'Rights', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_14', 'title_i18n': {'en': 'Rights', 'ja': '権利情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186609386': {'title': 'Subject', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_6', 'title_i18n': {'en': 'Subject', 'ja': '主題'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186626617': {'title': 'Description', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_17', 'title_i18n': {'en': 'Description', 'ja': '内容記述'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186643794': {'title': 'Publisher', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_5', 'title_i18n': {'en': 'Publisher', 'ja': '出版者'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186660861': {'title': 'Date', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_11', 'title_i18n': {'en': 'Date', 'ja': '日付'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186702042': {'title': 'Language', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_71', 'title_i18n': {'en': 'Language', 'ja': '言語'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186783814': {'title': 'Identifier', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_176', 'title_i18n': {'en': 'Identifier', 'ja': '識別子'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186819068': {'title': 'Identifier Registration', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_16', 'title_i18n': {'en': 'Identifier Registration', 'ja': 'ID登録'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186859717': {'title': 'Temporal', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_18', 'title_i18n': {'en': 'Temporal', 'ja': '時間的範囲'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186882738': {'title': 'Geo Location', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_19', 'title_i18n': {'en': 'Geo Location', 'ja': '位置情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186901218': {'title': 'Funding Reference', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_21', 'title_i18n': {'en': 'Funding Reference', 'ja': '助成情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186920753': {'title': 'Source Identifier', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_10', 'title_i18n': {'en': 'Source Identifier', 'ja': '収録物識別子'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186941041': {'title': 'Source Title', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_13', 'title_i18n': {'en': 'Source Title', 'ja': '収録物名'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186959569': {'title': 'Volume Number', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_88', 'title_i18n': {'en': 'Volume Number', 'ja': '巻'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186981471': {'title': 'Issue Number', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_87', 'title_i18n': {'en': 'Issue Number', 'ja': '号'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617186994930': {'title': 'Number of Pages', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_85', 'title_i18n': {'en': 'Number of Pages', 'ja': 'ページ数'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187024783': {'title': 'Page Start', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_84', 'title_i18n': {'en': 'Page Start', 'ja': '開始ページ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187045071': {'title': 'Page End', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_83', 'title_i18n': {'en': 'Page End', 'ja': '終了ページ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187056579': {'title': 'Bibliographic Information', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_102', 'title_i18n': {'en': 'Bibliographic Information', 'ja': '書誌情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187087799': {'title': 'Dissertation Number', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_82', 'title_i18n': {'en': 'Dissertation Number', 'ja': '学位授与番号'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187112279': {'title': 'Degree Name', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_80', 'title_i18n': {'en': 'Degree Name', 'ja': '学位名'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187136212': {'title': 'Date Granted', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'input_type': 'cus_79', 'title_i18n': {'en': 'Date Granted', 'ja': '学位授与年月日'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617187187528': {'title': 'Conference', 'option': {'crtf': True, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_75', 'title_i18n': {'en': 'Conference', 'ja': '会議記述'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617258105262': {'title': 'Resource Type', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': True, 'showlist': False}, 'input_type': 'cus_8', 'title_i18n': {'en': 'Resource Type', 'ja': '資源タイプ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617265215918': {'title': 'Version Type', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_9', 'title_i18n': {'en': 'Version Type', 'ja': '出版タイプ'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617349709064': {'title': 'Contributor', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_62', 'title_i18n': {'en': 'Contributor', 'ja': '寄与者'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617349808926': {'title': 'Version', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_28', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617351524846': {'title': 'APC', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_27', 'title_i18n': {'en': 'APC', 'ja': 'APC'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617353299429': {'title': 'Relation', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_12', 'title_i18n': {'en': 'Relation', 'ja': '関連情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617605131499': {'title': 'File', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_65', 'title_i18n': {'en': 'File', 'ja': 'ファイル情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617610673286': {'title': 'Rights Holder', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_3', 'title_i18n': {'en': 'Rights Holder', 'ja': '権利者情報'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617620223087': {'title': 'Heading', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'input_type': 'cus_119', 'title_i18n': {'en': 'Heading', 'ja': '見出し'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1617944105607': {'title': 'Degree Grantor', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_78', 'title_i18n': {'en': 'Degree Grantor', 'ja': '学位授与機関'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}, 'item_1662046377046': {'title': 'サムネイル', 'option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'input_type': 'cus_1037', 'title_i18n': {'en': 'thumbnail', 'ja': 'サムネイル'}, 'input_value': '', 'input_maxItems': '9999', 'input_minItems': '1'}}
    item_type_mapping = json_data("data/item_type_with_hide/mapping.json")
    item_type = MagicMock()
    item_type.render.get.return_value = json_data("data/item_type_with_hide/render.json").get('table_row')
    with patch("weko_items_ui.utils.get_options_and_order_list", return_value=(ret, item_type_mapping)), \
         patch("weko_items_ui.utils.get_hide_list_by_schema_form", return_value=["description.@value"]), \
         patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type):
        data = PreprocessorMixin().preprocess_record(pid, record)
    assert data['metadata']['title'] == 'test3'
    assert data['created'] == '2015-10-01T11:11:11.000001+00:00'
    assert data['revision'] == 1
    assert data['metadata']['aref'] == {'$ref': '#/title'}


def test_preprocessor_mixin_searchhit():
    """Test preprocessor mixin."""
    pid = PersistentIdentifier(
        pid_type='doi', pid_value='10.1234/foo', status='R')

    data = PreprocessorMixin.preprocess_search_hit(pid, {
        '_source': {
            'title': 'test',
            '_created': '2015-10-01T11:11:11.000001+00:00',
            '_updated': '2015-12-01T11:11:11.000001+00:00',
        },
        '_version': 1,
    })

    for k in keys:
        assert k in data

    assert data['metadata']['title'] == 'test'
    assert data['created'] == '2015-10-01T11:11:11.000001+00:00'
    assert data['revision'] == 1
    assert '_created' not in data['metadata']
    assert '_updated' not in data['metadata']

    data = PreprocessorMixin.preprocess_search_hit(pid, {
        '_source': {'title': 'test'},
        '_version': 1,
    })
    assert data['created'] is None
    assert data['updated'] is None
