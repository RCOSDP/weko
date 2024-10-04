# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp

"""Module tests."""

from re import T
import json
from datetime import datetime
from typing_extensions import reveal_type
import pytest
from unittest import mock
from unittest.mock import patch
# from mock import patch
import uuid
import copy
from collections import OrderedDict
from werkzeug.exceptions import HTTPException
import time
from flask import session
from flask_login import login_user
import redis
from weko_redis.errors import WekoRedisError
# from .errors import WekoDepositError
from weko_redis.redis import RedisConnection

from opensearchpy.exceptions import NotFoundError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from invenio_pidstore.errors import PIDInvalidAction
from invenio_pidrelations.models import PIDRelation
from invenio_records.errors import MissingModelError
from invenio_records_rest.errors import PIDResolveRESTError
from invenio_records_files.models import RecordsBuckets
from invenio_records_files.api import Record
from invenio_files_rest.models import Bucket, ObjectVersion,FileInstance
from invenio_records.api import RecordRevision
from six import BytesIO
from weko_records.utils import get_options_and_order_list
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import OperationalError
from weko_admin.models import AdminSettings
from weko_records.api import FeedbackMailList, ItemLink, ItemsMetadata, ItemTypes, Mapping,WekoRecord
from invenio_pidrelations.serializers.utils import serialize_relations
from weko_deposit.api import WekoDeposit, WekoFileObject, WekoIndexer, \
    WekoRecord, _FormatSysBibliographicInformation, _FormatSysCreator
from weko_deposit.config import WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS
from invenio_accounts.testutils import login_user_via_view,login_user_via_session
from invenio_accounts.models import User
from weko_items_ui.config import WEKO_ITEMS_UI_MS_MIME_TYPE,WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT
from weko_workflow.models import Activity
from sqlalchemy.exc import SQLAlchemyError
# from .errors import WekoDepositError

from tests.helpers import login
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
            


# class WekoRecord(Record):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestWekoRecord:
    #     def pid(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                assert record.pid==""

            indexer, results = es_records
            result = results[0]
            record = result['record']
            pid = record.pid
            assert isinstance(pid,PersistentIdentifier)==True
            assert pid.pid_type=="depid"
            assert pid.pid_value=="1"

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def pid_recid(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_recid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_recid(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                record.pid_recid
            
            indexer, results = es_records
            result = results[0]
            record = result['record']
            assert isinstance(record,WekoRecord)==True
            pid = record.pid_recid
            assert isinstance(pid,PersistentIdentifier)==True
            assert pid.pid_type=="recid"
            assert pid.pid_value=="1"

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


    #     def hide_file(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_hide_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_hide_file(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, results = es_records
            result = results[0]
            record = result['record']
            assert record.hide_file==False

            result = results[1]
            record = result['record']
            record["item_1617186609386"] = {"attribute_type":"file","attribute_name":"subject","attribute_value_mlt":["test_subject"]}
            assert record.hide_file==False

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    #     def navi(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_navi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_navi(self,app,users,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with app.test_request_context():
                assert record.navi==[]
            indexer, results = es_records
            result = results[0]
            record = result['record']
            # assert record.navi==[]
            with app.test_request_context(query_string={"community":"test_com"}):
                assert record.navi==[]

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def item_type_info(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_item_type_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_item_type_info(self,app,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with app.test_request_context():
                with pytest.raises(AttributeError):
                    assert record.item_type_info==""
            indexer, results = es_records
            result = results[0]
            record = result['record']
            assert record.item_type_info=='テストアイテムタイプ(1)'

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def switching_language(data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_switching_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_switching_language(self,app,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            # language = current_language
            with app.test_request_context(headers=[('Accept-Language', 'en')]):
                data = [{"language":"en","title":"test_title"}]
                result = record.switching_language(data)
                assert result == "test_title"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # language != current_language, language=en
            with app.test_request_context(headers=[('Accept-Language', 'ja')]):
                data = [{"language":"en","title":"test_title"}]
                result = record.switching_language(data)
                assert result == "test_title"

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # language != en, exist language
            with app.test_request_context(headers=[('Accept-Language', 'da')]):
                data = [{"language":"ja","title":"test_title"}]
                result = record.switching_language(data)
                assert result == "test_title"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # not exist language
            with app.test_request_context(headers=[('Accept-Language', 'da')]):
                data = [{"title":"test_title"}]
                result = record.switching_language(data)
                assert result == "test_title"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # len(data) <= 0
            with app.test_request_context(headers=[('Accept-Language', 'da')]):
                data = {}
                result = record.switching_language(data)
                assert result == ""

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # no language
            with app.test_request_context(headers=[('Accept-Language', 'da')]):
                data = [{"title":"title"},{"title":"en_title","language":"en"}]
                result = record.switching_language(data)
                assert result == "title"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # no language
            with app.test_request_context(headers=[('Accept-Language', 'en')]):
                data = [{"title":"title"},{"title":"en_title","language":"en"}]
                result = record.switching_language(data)
                assert result == "en_title"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # no language
            with app.test_request_context(headers=[('Accept-Language', 'ja')]):
                data = [{"title":"en_title","language":"en"},{"title":"title"}]
                result = record.switching_language(data)
                assert result == "en_title"

            # language != current_language, language=en
            with app.test_request_context(headers=[('Accept-Language', 'en')]):
                data = [{"language":"","title":"test_title"},{"language":"","title":"test_title"}]
                result = record.switching_language(data)
                assert result == "test_title"

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
           

    #     def __get_titles_key(item_type_mapping):
    #     def get_titles(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_titles -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_titles(self,app,es_records,db_itemtype,db_oaischema):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with app.test_request_context():
                assert record.get_titles==""
            indexer, results = es_records
            result = results[0]
            record = result['record']
            assert record['item_type_id']=="1"

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            with app.test_request_context():
                assert record.get_titles=="title"

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
            
            with app.test_request_context(headers=[("Accept-Language", "en")]):
                assert record.get_titles=="title"

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            app.config['BABEL_DEFAULT_LOCALE'] = 'ja'
            with app.test_request_context():
                assert record.get_titles=="タイトル"

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
            with app.test_request_context():
                assert record.get_titles=="title"
            # todo25
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


    #     def items_show_list(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_items_show_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_items_show_list(self,app,es_records,users,db_itemtype,db_admin_settings):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with app.test_request_context():
                with pytest.raises(AttributeError):
                    assert record.items_show_list==""

            indexer, results = es_records
            result = results[0]
            record = result['record']
            with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
                assert record.items_show_list==[{'attribute_name': 'PubDate', 'attribute_value': '2022-08-20', 'attribute_name_i18n': 'PubDate'}, {'attribute_name': 'Title', 'attribute_name_i18n': 'Title', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Title': 'タイトル'}], [{'Language': 'ja'}]]], [[[{'Title': 'title'}], [{'Language': 'en'}]]]]}, {'attribute_name': 'Resource Type', 'attribute_name_i18n': 'Resource Type', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Resource Type': 'conference paper'}], [{'Resource Type Identifier': 'http://purl.org/coar/resource_type/c_5794'}]]]]}, {'attribute_name': 'File', 'attribute_name_i18n': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [[[[{'dateType': 'Available', 'item_1617605131499[].date[0].dateValue': '2022-09-07'}]], [{'item_1617605131499[].url': 'https://weko3.example.org/record/1/files/hello.txt'}], [[{'item_1617605131499[].filesize[].value': '146 KB'}]], {'version_id': '{}'.format(record.files['hello.txt'].version_id), 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk', 'item_1617605131499[].filename': 'hello.txt', 'item_1617605131499[].format': 'plain/text', 'item_1617605131499[].accessrole': 'open_access'}]]}]


            indexer, results = es_records
            result = results[1]
            record = result['record']
            with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
                assert record.items_show_list==[{'attribute_name': 'PubDate', 'attribute_value': '2022-08-20', 'attribute_name_i18n': 'PubDate'}, {'attribute_name': 'Title', 'attribute_name_i18n': 'Title', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Title': 'タイトル'}], [{'Language': 'ja'}]]], [[[{'Title': 'title'}], [{'Language': 'en'}]]]]}, {'attribute_name': 'Resource Type', 'attribute_name_i18n': 'Resource Type', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Resource Type': 'conference paper'}], [{'Resource Type Identifier': 'http://purl.org/coar/resource_type/c_5794'}]]]]}, {'attribute_name': 'File', 'attribute_name_i18n': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [[[[{'dateType': 'Available', 'item_1617605131499[].date[0].dateValue': '2022-09-07'}]], [{'item_1617605131499[].url': 'https://weko3.example.org/record/2/files/hello.txt'}], [[{'item_1617605131499[].filesize[].value': '146 KB'}]], {'version_id': '{}'.format(record.files['hello.txt'].version_id), 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk', 'item_1617605131499[].filename': 'hello.txt', 'item_1617605131499[].format': 'plain/text', 'item_1617605131499[].accessrole': 'open_access'}]]}]

            # todo26
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


    #     def display_file_info(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_display_file_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_display_file_info(self,app,es_records,db_itemtype):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with app.test_request_context():
                with pytest.raises(AttributeError):
                    assert record.display_file_info==""

            indexer, results = es_records
            result = results[0]
            record = result['record']
            with app.test_request_context("/test?filename=hello.txt"):
                assert record.display_file_info==[{'attribute_name': 'File', 'attribute_name_i18n': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [[[[{'Opendate': '2022-09-07'}],[{'FileName': 'hello.txt'}],[{'Text URL': [[[{'Text URL': 'https://weko3.example.org/record/1/files/hello.txt'}]]]}],[{'Format': 'plain/text'}],[{'Size': [[[[{'Size': '146 KB'}]]]]}]]]]}]

            record["item_1617186609386"] = {"attribute_type":"file","attribute_name":"subject","attribute_value_mlt":["test_subject"]}
            record["item_1617186626617"] = {"attribute_name":"description","attribute_type":"file"}

            with app.test_request_context("/test?filename=not_hello.txt"):
                assert record.display_file_info==[]

            indexer, results = es_records
            result = results[2]
            record = result['record']
            record['hidden']=True

            with app.test_request_context("/test?filename=hello.txt"):
                assert record.display_file_info==[]
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def __remove_special_character_of_weko2(self, metadata):
    #     def _get_creator(meta_data, hide_email_flag):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test__get_creator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            assert record._get_creator({},False)==[]

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
            assert record._get_creator({},True)==[]
            # todo28
            # record = WekoRecord({})
            # print(record)
            # indexer, results = es_records
            # record = results[0]
            # record = WekoRecord(record)
            # deposit = record['item']
            metadata = {"title": "fuu"}
            record._get_creator(metadata,False)
            assert record._get_creator(record,True)==[]
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


    #     def __remove_file_metadata_do_not_publish(self, file_metadata_list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test___remove_file_metadata_do_not_publish -vv -s --cov-branch 
    #     def __check_user_permission(user_id_list):
    #     def is_input_open_access_date(file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_is_input_open_access_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_input_open_access_date(self):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            assert record.is_input_open_access_date({})==False

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def is_do_not_publish(file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_is_do_not_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_do_not_publish(self):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            assert record.is_do_not_publish({})==False

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def get_open_date_value(file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_open_date_value -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_open_date_value(self):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            assert record.get_open_date_value({})==None

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def is_future_open_date(self, file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_is_future_open_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_future_open_date(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            assert record.is_future_open_date(record,{})==True
            assert record.is_future_open_date(record,{'url': {'url': 'https://weko3.example.org/record/1/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-07'}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_access', 'version_id': 'e131046c-291f-4065-b4b4-ca3bf1fac6e3', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'})==False

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
     



    #     def pid_doi(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_doi(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                assert record.pid_doi==""
            indexer, records = es_records
            record = records[0]['record']
            pid = record.pid_doi
            assert isinstance(pid,PersistentIdentifier)==True
            assert pid.pid_type=='doi'

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def pid_cnri(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_cnri -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_cnri(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                assert record.pid_cnri==""
            indexer, records = es_records
            record = records[0]['record']
            pid = record.pid_cnri
            assert isinstance(pid,PersistentIdentifier)==True
            assert pid.pid_type=='hdl'

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
        

    #     def pid_parent(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_parent -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_parent(self,db,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                assert record.pid_parent==""

            # indexer, records = es_records
            # record = records[0]['record']
            # pid = record.pid_parent
            # assert isinstance(pid,PersistentIdentifier)==True
            # assert pid.pid_type=='parent'

            
            indexer, records = es_records
            record = records[1]['record']
            # record['recid']="2.0"
            # record.model.recid="2.0"
            # db.session.merge(record.model)
            record.pid.pid_value="2.0"
            record['_deposit']['pid']="2.0"
            # record.pid_recid.pid_value="2.0"
            # record['recid']="2.0"
            print(999999)
            print(record)
            # print(record.pid_recid.pid_value)
            # db.session.merge(record)
            db.session.commit()
            pid = record.pid_parent
            assert isinstance(pid,PersistentIdentifier)==True
            assert pid.pid_type=='parent'
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def get_record_by_pid(cls, pid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_record_by_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_record_by_pid(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            recid = records[0]['recid']

            rec = WekoRecord.get_record_by_pid(1)
            assert isinstance(rec,WekoRecord)
            assert rec.pid_recid==recid

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


    #     def get_record_by_uuid(cls, uuid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_record_by_uuid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_record_by_uuid(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            recid = records[0]['recid']
            rec =  WekoRecord.get_record_by_uuid(record.id)
            assert isinstance(rec,WekoRecord)==True
            assert rec.pid_recid == recid

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def get_record_cvs(cls, uuid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_record_cvs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_record_cvs(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            assert WekoRecord.get_record_cvs(record.id)==False

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def _get_pid(self, pid_type):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test__get_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_pid(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                record._get_pid('')

            indexer, results = es_records
            result = results[0]
            from invenio_pidstore.models import PersistentIdentifier, PIDStatus
            from invenio_pidstore.errors import PIDDoesNotExistError, PIDInvalidAction
            from weko_deposit.errors import WekoDepositError
            # with patch("invenio_pidstore.models.PersistentIdentifier", side_effect=PIDDoesNotExistError(record[0].pid_type,record[0].pid_value)):

            
            
            with patch("invenio_pidstore.models.PersistentIdentifier", side_effect=Exception("test_error")):
                with pytest.raises(WekoDepositError, match="Could not encoding/decoding file"):
                    # record._get_pid(record['_deposit']['pid']['type'])
                    # record._get_pid(record['pid']['type'])
                    # record._get_pid('doi')
                    # indexer, results = es_records
                    # result = results[0]
                    # record = result['depid']
                    # print(999)
                    # print(record)
                    # pid = record.pid
                    record._get_pid("recid")
                    mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', value=mock.ANY)
                    mock_logger.reset_mock()
            
            # with patch("invenio_pidstore.models.PersistentIdentifier", side_effect=PIDDoesNotExistError("test pid_type","test pid_value")):
            with patch("invenio_db.db.session.begin_nested", side_effect=SQLAlchemyError("test_error")):
                with pytest.raises(WekoDepositError, match="Could not encoding/decoding file"):               
                    indexer, results = es_records
                    result = results[0]
                    record = result['record']
                    pid = record.pid
                    print(99999)
                    print(pid)
                    print(99999)
                    record._get_pid(pid)
                    mock_logger.assert_any_call(key='WEKO_COMMON_FAILED_GET_PID', value=mock.ANY)
                    mock_logger.reset_mock()
            with patch("invenio_pidstore.models.PersistentIdentifier", side_effect=PIDDoesNotExistError(record[0].pid_type,record[0].pid_value)):
                record._get_pid('')
                mock_logger.assert_any_call(key='WEKO_COMMON_FAILED_GET_PID', value=mock.ANY)
                mock_logger.reset_mock()



            # todo31
            # mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            # mock_logger.reset_mock()
        


    #     def update_item_link(self, pid_value):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_update_item_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_item_link(self,db, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger: 
            from weko_records.models import ItemMetadata, ItemReference
            ir = ItemReference(src_item_pid='1',dst_item_pid='1',reference_type='1')
            db.session.add(ir)
            db.session.commit()
            indexer, records = es_records
            #record = records[0]['record']
            #recid = records[0]['recid']
            #record2 = records[2]['record']
            #print("pid:{}".format(record.pid.pid_value))
            #record.update_item_link(record2.pid.pid_value)
            #item_link = ItemLink.get_item_link_info(recid.pid_value)
            #assert item_link==[]

            record = records[0]['record']
            recid = records[0]['recid']
            record.update_item_link(record.pid.pid_value)
            item_link = ItemLink.get_item_link_info(recid.pid_value)
            assert item_link==[{'item_links': '1', 'item_title': 'title', 'value': '1'}]
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()


    #     def get_file_data(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_file_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_file_data(self,app,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]["record"]
            with app.test_request_context():
                result = record.get_file_data()
                assert result[0]["accessrole"] == "open_access"
                assert result[0]["filename"] == "hello.txt"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
        
        
# class _FormatSysCreator:
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class Test_FormatSysCreator:
    # def __init__(self, creator):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test___init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test___init__(self,app,prepare_creator):
        with app.test_request_context():
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True
        
#     def _get_creator_languages_order(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_languages_order -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_languages_order(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                obj._get_creator_languages_order()
                assert obj.languages==['ja', 'ja-Kana', 'en', 'cn']

            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                obj._get_creator_languages_order()
                assert obj.languages==['ja', 'ja-Kana', 'en', 'cn']
            # todo33
            # mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            # mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            # mock_logger.reset_mock()

    # def _format_creator_to_show_detail(self, language: str, parent_key: str,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_to_show_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_to_show_detail(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True 
                language = 'en'
                parent_key = 'creatorNames'
                lst = []
                obj._format_creator_to_show_detail(language,parent_key,lst)
                assert lst==['Joho, Taro']

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    #* This is for testing only for the changes regarding creatorType
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_to_show_detail_2 -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_to_show_detail_2(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                prepare_creator["creatorType"] = "creator_type_test"
                obj = _FormatSysCreator(prepare_creator)
                language = 'en'
                parent_key = 'creatorType'
                lst = []

                assert obj._format_creator_to_show_detail(
                    language,
                    parent_key,
                    lst
                ) is None
                
                assert len(lst) == 0

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    #     def _get_creator_to_show_popup(self, creators: Union[list, dict],
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_to_show_popup -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_to_show_popup(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True 
                creators={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': '所属機関', 'affiliationNameLang': 'ja'}, {'affiliationName': 'Affilication Name', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}]}], 'creatorAlternatives': [{'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}
                language='ja'
                creator_list=[]
                creator_list_temp=None
                obj._get_creator_to_show_popup(creators,language,creator_list,creator_list_temp)
                assert creators=={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'affiliationName': 'Affilication Name', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}]}], 'creatorAlternatives': [{'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}
                assert language=="ja"
                assert creator_list==[{'ja': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}]
                assert creator_list_temp==None
                # todo34
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True 
                creators={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}]}], 'creatorAlternatives': [{'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}
                language='ja'
                creator_list=[]
                creator_list_temp=None
                obj._get_creator_to_show_popup(creators,language,creator_list,creator_list_temp)
                assert creators=={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}]}], 'creatorAlternatives': [{'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}
                assert language=="ja"
                assert creator_list==[{'ja': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}]
                assert creator_list_temp==None

                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True 
                creators={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': '所属機関', 'affiliationNameLang': 'ja'}, {'affiliationName': 'Affilication Name', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}]}], 'creatorAlternatives': [{'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}
                language=''
                creator_list=[]
                creator_list_temp=None
                # creator_list=[{'givenName': '太郎', 'givenNameLang': 'en'}]
                # creator_list_temp=[{'givenName': '太郎', 'givenNameLang': 'en'}]
                obj._get_creator_to_show_popup(creators,language,creator_list,creator_list_temp)
                assert creators=={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'affiliationName': 'Affilication Name', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}]}], 'creatorAlternatives': [{'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}
                assert language==""
                assert creator_list==[]
                assert creator_list_temp==None

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    #* This is for testing only for the changes regarding creatorType
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_to_show_popup_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_to_show_popup_2(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                prepare_creator["creatorType"] = "creator_type_test"
                obj = _FormatSysCreator(prepare_creator)

                creators = {
                    'creatorType': 'creator_type_test'
                }

                language = 'ja'
                creator_list = []
                creator_list_temp = None

                obj._get_creator_to_show_popup(
                    creators,
                    language,
                    creator_list,
                    creator_list_temp
                )

                assert len(creator_list) == 0

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

#         def _run_format_affiliation(affiliation_max, affiliation_min,
#         def format_affiliation(affiliation_data):
    # def _get_creator_based_on_language(creator_data: dict,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_based_on_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_based_on_language(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creator_data ={'givenName': '太郎', 'givenNameLang': 'ja'}
                creator_list_temp=[]
                language='ja'
                obj._get_creator_based_on_language(creator_data,creator_list_temp,language)
                assert creator_list_temp==[{'givenName': '太郎', 'givenNameLang': 'ja'}]
                # todo35
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creator_data ={'givenName': '太郎', 'givenNameLang': 'ja'}
                creator_list_temp=[]
                language=''
                obj._get_creator_based_on_language(creator_data,creator_list_temp,language)
                assert creator_list_temp==[]

                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creator_data ={}
                creator_list_temp=[]
                language=''
                obj._get_creator_based_on_language(creator_data,creator_list_temp,language)
                assert creator_list_temp==[{}]
                                
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    # def format_creator(self) -> dict:
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test_format_creator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_format_creator(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                assert obj.format_creator()=={'name': ['Joho, Taro'], 'order_lang': [{'ja': {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}}, {'ja-Kana': {'creatorName': ['ジョウホウ, タロウ'], 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'en': {'creatorName': ['Joho, Taro'], 'creatorAlternative': ['Alternative Name'], 'affiliationName': [' Affilication Name'], 'affiliationNameIdentifier': [{'identifier': '', 'uri': ''}]}}]}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    #* This is for testing only for the changes regarding creatorType
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test_format_creator_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_format_creator_2(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                prepare_creator["creatorType"] = "creator_type_test"
                obj = _FormatSysCreator(prepare_creator)
                
                assert isinstance(
                    obj,
                    _FormatSysCreator
                ) == True

                returnData = obj.format_creator()

                for item in returnData.get("order_lang"):
                    if item.get("ja"):
                        assert "creatorType" not in list(item.get("ja").keys())
                    elif item.get("ja-Kana"):
                        assert "creatorType" not in list(item.get("ja-Kana").keys())
                    elif item.get("en"):
                        assert "creatorType" not in list(item.get("en").keys())

                    mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                    mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                    mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                    mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                    mock_logger.reset_mock()
                    
    # def _format_creator_on_creator_popup(self, creators: Union[dict, list],
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_on_creator_popup -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_on_creator_popup(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator({})
                assert isinstance(obj,_FormatSysCreator)==True
                formatted_creator_list = []
                creator_list=[{'ja': {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}}, {'ja-Kana': {'givenName': ['タロウ'], 'givenNameLang': ['ja-Kana'], 'familyName': ['ジョウホウ'], 'familyNameLang': ['ja-Kana'], 'creatorName': ['ジョウホウ, タロウ'], 'creatorNameLang': ['ja-Kana']}}, {'en': {'givenName': ['Taro'], 'givenNameLang': ['en'], 'familyName': ['Joho'], 'familyNameLang': ['en'], 'creatorName': ['Joho, Taro'], 'creatorNameLang': ['en'], 'affiliationName': ['Affilication Name'], 'affiliationNameLang': ['en'], 'creatorAlternative': ['Alternative Name'], 'creatorAlternativeLang': ['en']}}]
                obj._format_creator_on_creator_popup(creator_list,formatted_creator_list)
                assert formatted_creator_list==[{'ja': {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}}, {'ja-Kana': {'creatorName': ['ジョウホウ, タロウ'], 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'en': {'creatorName': ['Joho, Taro'], 'creatorAlternative': ['Alternative Name'], 'affiliationName': [' Affilication Name'], 'affiliationNameIdentifier': [{'identifier': '', 'uri': ''}]}}]
                # todo36
                obj = _FormatSysCreator({})
                assert isinstance(obj,_FormatSysCreator)==True
                formatted_creator_list = []
                # creator_list=['ja','givenName']
                creator_list=[{'ja': [{'givenName': '太郎'}, {'givenNameLang': ['ja']}]}]
                # creator_list=[{'ja': ({'givenName': '太郎'}, {'givenNameLang': ['ja']})}]
                # creator_list=[{'ja': ['givenName', '太郎' ]}]

                obj._format_creator_on_creator_popup(creator_list,formatted_creator_list)
                # assert formatted_creator_list==[{'ja': {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}}, {'ja-Kana': {'creatorName': ['ジョウホウ, タロウ'], 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'en': {'creatorName': ['Joho, Taro'], 'creatorAlternative': ['Alternative Name'], 'affiliationName': [' Affilication Name'], 'affiliationNameIdentifier': [{'identifier': '', 'uri': ''}]}}]
 
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()
    
    # def _format_creator_name(creator_data: dict,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_name(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creator_data1 = {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
                tmp = {}
                obj._format_creator_name(creator_data1,tmp)
                assert tmp=={'creatorName': ['情報, 太郎']}
                creator_data2 = {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
                tmp = {}
                obj._format_creator_name(creator_data2,tmp)
                assert tmp=={'creatorName': ['情報 太郎']}
                creator_data3 = {'familyName': ['情報']}
                tmp = {}
                obj._format_creator_name(creator_data3,tmp)
                assert tmp=={"creatorName":['情報']}
                creator_data4 = {'givenName': ['太郎']}
                tmp = {}
                obj._format_creator_name(creator_data4,tmp)
                assert tmp=={"creatorName":['太郎']}
                creator_data5 = {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報1','情報2','情報3'], 'familyNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
                tmp = {}
                obj._format_creator_name(creator_data5,tmp)
                assert tmp=={'creatorName': ['情報1 太郎', '情報2', '情報3']}
 
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()


    # def _format_creator_affiliation(creator_data: dict,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_affiliation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_affiliation(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creator_data = {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
                des_creator = {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名']}
                obj._format_creator_affiliation(creator_data,des_creator)
                assert des_creator=={'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}
 
                mock_logger.assert_any_call(key='WEKO_COMMON_WHILE_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_WHILE_END')
                mock_logger.reset_mock()

    #         def _get_max_list_length() -> int:
    # def _get_creator_to_display_on_popup(self, creator_list: list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_to_display_on_popup -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_to_display_on_popup(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context(headers=[("Accept-Language", "en")]):
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creator_list = []
                obj._get_creator_to_display_on_popup(creator_list)
                assert creator_list==[{'ja': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}, {'ja-Kana': [{'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}]}, {'en': [{'givenName': 'Taro', 'givenNameLang': 'en'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {'affiliationName': 'Affilication Name', 'affiliationNameLang': 'en'}, {'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}]}]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()


    # def _merge_creator_data(self, creator_data: Union[list, dict],
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__merge_creator_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__merge_creator_data(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creator_data = [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]
                merged_data = {}
                obj._merge_creator_data(creator_data,merged_data)
                assert merged_data=={'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

                creator_data = [ {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]
                merged_data = {'givenName': '次郎', 'givenNameLang': 'ja'}
                obj._merge_creator_data(creator_data,merged_data)
                assert merged_data=={'givenName': '次郎', 'givenNameLang': 'ja', 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

                creator_data="not_dict_or_list"
                merged_data={}
                obj._merge_creator_data(creator_data,merged_data)
                assert merged_data == {}

                creator_data={'givenName': ['太郎']}
                merged_data={}
                obj._merge_creator_data(creator_data,merged_data)
                assert merged_data == {}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()
                
                creator_data={'givenName': '太郎'}
                merged_data={'givenName': ['次郎']}
                obj._merge_creator_data(creator_data,merged_data)
                assert merged_data == {'givenName': ['次郎','太郎']}
                # todo37
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()
    
    #         def merge_data(key, value):
    # def _get_default_creator_name(self, list_parent_key: list,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_default_creator_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_default_creator_name(self,app,prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                list_parent_key = ['creatorNames', 'familyNames', 'givenNames', 'creatorAlternatives']
                creator_name = []
                obj.languages=["ja","en"]
                obj._get_default_creator_name(list_parent_key,creator_name)
                assert creator_name==['Joho, Taro', 'Joho', 'Taro', 'Alternative Name']
                # todo38
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                list_parent_key = []
                creator_name = []
                obj.languages=["ja","en"]
                obj._get_default_creator_name(list_parent_key,creator_name)
                assert creator_name==[]

                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                list_parent_key = ['myNames']
                creator_name = []
                obj.languages=["ja"]
                obj._get_default_creator_name(list_parent_key,creator_name)
                assert creator_name==[]
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

#         def _get_creator(_language):

# class _FormatSysBibliographicInformation:
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class Test__FormatSysBibliographicInformation():
    # def __init__(self, bibliographic_meta_data_lst, props_lst):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test___init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test___init__(self,prepare_formatsysbib):
        meta,props = prepare_formatsysbib
        obj=_FormatSysBibliographicInformation(copy.deepcopy(meta),copy.deepcopy(props))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True

    # def is_bibliographic(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test_is_bibliographic -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_bibliographic(self,app,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            assert obj.is_bibliographic()==True

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
            
            obj.bibliographic_meta_data_lst={"bibliographic_titles":"title"}
            assert obj.is_bibliographic() == True

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
            
            obj.bibliographic_meta_data_lst="str_value"
            assert obj.is_bibliographic() == False
            # todo39
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


    #         def check_key(_meta_data):
    # def get_bibliographic_list(self, is_get_list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test_get_bibliographic_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_bibliographic_list(self,app,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            with app.test_request_context(headers=[("Accept-Language", "en")]):
                assert obj.get_bibliographic_list(True)==[{'title_attribute_name': 'Journal Title', 'magazine_attribute_name': [{'Volume': '1'}, {'Issue': '12'}, {'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 'length': 5}]
                assert obj.get_bibliographic_list(False)==[{'title_attribute_name': ['ja : 雑誌タイトル', 'en : Journal Title'], 'magazine_attribute_name': [{'Volume Number': '1'}, {'Issue Number': '12'}, {'p.': '1-100'}, {'Number of Page': '99'}, {'Issue Date': '2022-08-29'}], 'length': 5}]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
 
    # def _get_bibliographic(self, bibliographic, is_get_list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_bibliographic -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_bibliographic(self,app,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            # with app.test_request_context(headers=[("Accept-Language", "en")]):
            #     assert obj._get_bibliographic(bibliographic,True)==('Journal Title', [{'Volume': '1'}, {'Issue': '12'}, {'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 5)
            #     assert obj._get_bibliographic(bibliographic,False)==(['ja : 雑誌タイトル', 'en : Journal Title'], [{'Volume Number': '1'}, {'Issue Number': '12'}, {'p.': '1-100'}, {'Number of Page': '99'}, {'Issue Date': '2022-08-29'}], 5)
                # todo40
            with app.test_request_context(headers=[("Accept-Language", "")]):
                assert obj._get_bibliographic(bibliographic,True)==('Journal Title', [{'Volume': '1'}, {'Issue': '12'}, {'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 5)
                assert obj._get_bibliographic(bibliographic,False)==(['ja : 雑誌タイトル', 'en : Journal Title'], [{'Volume Number': '1'}, {'Issue Number': '12'}, {'p.': '1-100'}, {'Number of Page': '99'}, {'Issue Date': '2022-08-29'}], 5)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()
        
  
    # def _get_property_name(self, key):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_property_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_property_name(self,app,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            assert obj._get_property_name('subitem_1551255647225')=='Title'

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            result = obj._get_property_name('not_exist_key')
            assert result == "not_exist_key"
            # todo41
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


    # def _get_translation_key(key, lang):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_translation_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_translation_key(self,app,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            for key in WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS:
                assert obj._get_translation_key(key,"en")==WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS[key]["en"]

                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()
 
            result = obj._get_translation_key("not_exist_key","")
            assert result == None

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
  
    # def _get_bibliographic_information(self, bibliographic):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_bibliographic_information -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_bibliographic_information(self,app,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            assert obj._get_bibliographic_information(bibliographic)==([{'Volume Number': '1'}, {'Issue Number': '12'}, {'p.': '1-100'}, {'Number of Page': '99'}, {'Issue Date': '2022-08-29'}], 5)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
    
    # def _get_bibliographic_show_list(self, bibliographic, language):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_bibliographic_show_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_bibliographic_show_list(self,app,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            with app.test_request_context():
                assert obj._get_bibliographic_show_list(bibliographic,"ja")==([{'巻': '1'}, {'号': '12'}, {'p.': '1-100'}, {'ページ数': '99'}, {'発行年': '2022-08-29'}], 5)
                assert obj._get_bibliographic_show_list(bibliographic,"en")==([{'Volume': '1'}, {'Issue': '12'}, {'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 5)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
 
    # def _get_source_title(source_titles):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test___get_source_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test___get_source_title(self,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            
            assert obj._get_source_title(bibliographic.get('bibliographic_titles'))==['ja : 雑誌タイトル', 'en : Journal Title'] 

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def _get_source_title_show_list(source_titles, current_lang):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_source_title_show_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_source_title_show_list(self,app,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            with app.test_request_context():
                assert obj._get_source_title_show_list(bibliographic.get('bibliographic_titles'), "en")==('Journal Title', 'en')
                assert obj._get_source_title_show_list(bibliographic.get('bibliographic_titles'), "ja")==('雑誌タイトル', 'ja')
                assert obj._get_source_title_show_list(bibliographic.get('bibliographic_titles'), "ja-Latn")==('Journal Title', 'en')
                _title1 = bibliographic.get('bibliographic_titles').copy()
                _title1.pop()
                assert obj._get_source_title_show_list(_title1, "ja-Latn")==('雑誌タイトル', 'ja')

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

            data =[{"bibliographic_titleLang":"ja-Latn","bibliographic_title":"ja-Latn_title"}]
            value, lang = obj._get_source_title_show_list(data, "en")
            assert value == "ja-Latn_title"
            assert lang == "ja-Latn"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
            
            
            data =[{"bibliographic_title":"not_key_title"},{"bibliographic_titleLang":"ja-Latn","bibliographic_title":"ja-Latn_title"}]
            value, lang = obj._get_source_title_show_list(data, "en")
            assert value == "not_key_title"
            assert lang == ""

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
            
            app.config.update(WEKO_RECORDS_UI_LANG_DISP_FLG=True)
            data = [{},{"bibliographic_title":"not_key_title"},{"bibliographic_titleLang":"ja","bibliographic_title":"ja_title"},{"bibliographic_titleLang":"zh","bibliographic_title":"zh_title"}]
            value, lang = obj._get_source_title_show_list(data, "en")
            assert value == "zh_title"
            assert lang == "zh"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            data = [{},{"bibliographic_title":"not_key_title"}]
            value, lang = obj._get_source_title_show_list(data, "en")
            assert value == "not_key_title"
            assert lang == "ja"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
            
    # def _get_page_tart_and_page_end(page_start, page_end):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_page_tart_and_page_end -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_page_tart_and_page_end(self,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            assert obj._get_page_tart_and_page_end(bibliographic.get('bibliographicPageStart'),
                        bibliographic.get('bibliographicPageEnd'))=="{0}-{1}".format(bibliographic.get('bibliographicPageStart'),
                        bibliographic.get('bibliographicPageEnd'))

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
    
    # def _get_issue_date(issue_date):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_issue_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_issue_date(self,prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt,solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            assert obj._get_issue_date(bibliographic.get('bibliographicIssueDates'))==[bibliographic.get('bibliographicIssueDates').get('bibliographicIssueDate')]

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            data = [{"bibliographicIssueDate":'2022-08-29', 'bibliographicIssueDateType': 'Issued'},{"key":"value"}]
            result = obj._get_issue_date(data)
            assert result == ["2022-08-29"]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            data = "str_data"
            result = obj._get_issue_date(data)
            assert result == []
            # todo42
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


def test_missing_location(app, record):
    """Test missing location."""
    with pytest.raises(AttributeError):
        WekoRecord.create({}).file
    # for file in record.files:
        # file_info = file.info()


def test_record_create(app, db, location):
    """Test record creation with only bucket."""
    record = WekoRecord.create({'title': 'test'})
    db.session.commit()
    # assert record['_bucket'] == record.bucket_id
    assert '_files' not in record
    # assert len(record.pid)


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::test_weko_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_weko_record(app,client, db, users, location):
    """Test record files property."""
    user = User.query.filter_by(email=users[4]['email']).first()
    login_user_via_session(client=client,user=user)
    with pytest.raises(MissingModelError):
        WekoRecord({}).files

    AdminSettings.update(
        'items_display_settings',
        {'items_search_author': 'name', 'items_display_email': True},
        1
    )

    # item_type = ItemTypes.create(item_type_name='test', name='test')

    # deposit = WekoDeposit.create({'item_type_id': item_type.id})
    deposit = WekoDeposit.create({})
    db.session.commit()

    record = WekoRecord.get_record_by_pid(deposit.pid.pid_value)

    record.pid

    record.pid_recid

    # record.hide_file

    # record.navi

    # record.item_type_info
    with pytest.raises(AttributeError):
        record.items_show_list

    with pytest.raises(AttributeError):
        record.display_file_info

    with app.test_request_context(headers=[("Accept-Language", "en")]):
        record._get_creator([{}], True)

    record._get_creator({}, False)


def test_files_property(app, db, location):
    """Test record files property."""
    with pytest.raises(MissingModelError):
        WekoRecord({}).files

    deposit = WekoDeposit.create({})
    db.session.commit()

    record = WekoRecord.get_record_by_pid(deposit.pid.pid_value)

    assert 0 == len(record.files)
    assert 'invalid' not in record.files
    # make sure that _files key is not added after accessing record.files
    assert '_files' not in record

    with pytest.raises(KeyError):
        record.files['invalid']

    bucket = record.files.bucket
    assert bucket


def test_format_sys_creator(app, db):
    with app.test_request_context(headers=[('Accept-Language','en')]):
        creator = {
            'creatorNames': [{
                'creatorName': 'test',
                'creatorNameLang': 'en'
            }]
        }

        format_creator = _FormatSysCreator(creator)


def test_format_sys_bibliographic_information_multiple(app, db):
    metadata = [
        {
            "bibliographic_titles":
            [
                {
                    "bibliographic_title": "test",
                    "bibliographic_titleLang": "en"
                }
            ],
            "bibliographicPageEnd": "",
            "bibliographicIssueNumber": "",
            "bibliographicPageStart": "",
            "bibliographicVolumeNumber": "",
            "bibliographicNumberOfPages": "",
            "bibliographicIssueDates": ""
        }
    ]
    with app.test_request_context(headers=[('Accept-Language','en')]):
        sys_bibliographic = _FormatSysBibliographicInformation(metadata, [])

        sys_bibliographic.is_bibliographic()

        sys_bibliographic.get_bibliographic_list(True)

        sys_bibliographic.get_bibliographic_list(False)


def test_weko_deposit(app, db, location):
    deposit = WekoDeposit.create({})
    db.session.commit()

    with pytest.raises(PIDResolveRESTError):
        deposit.update({'actions': 'publish', 'index': '0', }, {})

    with pytest.raises(NoResultFound):
        deposit.item_metadata

    deposit.is_published()

    deposit['_deposit'] = {
        'pid': {
            'revision_id': 1,
            'type': 'pid',
            'value': '1'
        }
    }


def test_weko_indexer(app, db, location):
    deposit = WekoDeposit.create({})
    db.session.commit()

    indexer = WekoIndexer()
    indexer.client=MockClient()
    indexer.client.update_get_error(True)
    indexer.client.update_get_error(False)
    indexer.get_es_index()

    indexer.upload_metadata(
        jrc={},
        item_id=deposit.id,
        revision_id=0,
        skip_files=True
    )
    indexer.client.update_get_error(True)
    with pytest.raises(NotFoundError):
        indexer.update_relation_version_is_last({
            'id': 1,
            'is_last': True
        })
    indexer.client.update_get_error(False)
    indexer.update_es_data(deposit, update_revision=False)

    indexer.delete_file_index([deposit.id], 0)

    indexer.get_pid_by_es_scroll('')


def test_weko_indexer(app, db, location):
    deposit = WekoDeposit.create({})
    db.session.commit()

    indexer = WekoIndexer()
    indexer.client=MockClient()
    indexer.client.update_get_error(True)
    indexer.client.update_get_error(False)
    indexer.get_es_index()

    indexer.upload_metadata(
        jrc={},
        item_id=deposit.id,
        revision_id=0,
        skip_files=True
    )

    indexer.get_pid_by_es_scroll('')


def test_weko_file_object(app, db, location, testfile):
    record = WekoFileObject(
        obj=testfile,
        data={
            'size': 1,
            'format': 'application/msword',
        }
    )


def test_weko_deposit_new(app, db, location):
    recid = '1'
    deposit = WekoDeposit.create({}, recid=int(recid))
    db.session.commit()

    pid = PersistentIdentifier.query.filter_by(
        pid_type='recid',
        pid_value=recid
    ).first()

    record = WekoDeposit.get_record(pid.object_uuid)
    deposit = WekoDeposit(record, record.model)
    with patch('weko_deposit.api.WekoIndexer.update_relation_version_is_last', side_effect=NotFoundError):
        with pytest.raises(NotFoundError):
            deposit.publish()


def test_delete_item_metadata(app, db, location):
    a = {'_oai': {'id': 'oai:weko3.example.org:00000002.1', 'sets': []}, 'path': ['1031'], 'owner': '1', 'recid': '2.1', 'title': ['ja_conference paperITEM00000002(public_open_access_open_access_simple)'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2021-02-13'}, '_buckets': {'deposit': '9766676f-0a12-439b-b5eb-6c39a61032c6'}, '_deposit': {'id': '2.1', 'pid': {'type': 'depid', 'value': '2.1', 'revision_id': 0}, 'owners': [1], 'status': 'draft'}, 'item_title': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'author_link': ['1', '2', '3'], 'item_type_id': '15', 'publish_date': '2021-02-13', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000002(public_open_access_simple)', 'subitem_1551255648112': 'en'}]}, 'item_1617186385884': {'attribute_name': 'Alternative Title', 'attribute_value_mlt': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}]}, 'item_1617186419668': {'attribute_name': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '1', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI'}]}]}, {'givenNames': [{'givenName': '次郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 次郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '2', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}, {'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 三郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '3', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}]}, 'item_1617186476635': {'attribute_name': 'Access Rights', 'attribute_value_mlt': [{'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}]}, 'item_1617186499011': {'attribute_name': 'Rights', 'attribute_value_mlt': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}]}, 'item_1617186609386': {'attribute_name': 'Subject', 'attribute_value_mlt': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}]}, 'item_1617186626617': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'Description\\nDescription<br/>Description&EMPTY&\\nDescription', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'en'}, {'subitem_description': '概要\\n概要&EMPTY&\\n概要\\n概要', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'ja'}]}, 'item_1617186643794': {'attribute_name': 'Publisher', 'attribute_value_mlt': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}]}, 'item_1617186660861': {'attribute_name': 'Date', 'attribute_value_mlt': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}]}, 'item_1617186702042': {'attribute_name': 'Language', 'attribute_value_mlt': [{'subitem_1551255818386': 'jpn'}]}, 'item_1617186783814': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_identifier_uri': 'http://localhost', 'subitem_identifier_type': 'URI'}]}, 'item_1617186859717': {'attribute_name': 'Temporal', 'attribute_value_mlt': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}]}, 'item_1617186882738': {'attribute_name': 'Geo Location', 'attribute_value_mlt': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}]}, 'item_1617186901218': {'attribute_name': 'Funding Reference', 'attribute_value_mlt': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}]}, 'item_1617186920753': {'attribute_name': 'Source Identifier', 'attribute_value_mlt': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}]}, 'item_1617186941041': {'attribute_name': 'Source Title', 'attribute_value_mlt': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}]}, 'item_1617186959569': {'attribute_name': 'Volume Number', 'attribute_value_mlt': [{'subitem_1551256328147': '1'}]}, 'item_1617186981471': {'attribute_name': 'Issue Number', 'attribute_value_mlt': [{'subitem_1551256294723': '111'}]}, 'item_1617186994930': {'attribute_name': 'Number of Pages', 'attribute_value_mlt': [{'subitem_1551256248092': '12'}]}, 'item_1617187024783': {'attribute_name': 'Page Start', 'attribute_value_mlt': [{'subitem_1551256198917': '1'}]}, 'item_1617187045071': {'attribute_name': 'Page End', 'attribute_value_mlt': [{'subitem_1551256185532': '3'}]}, 'item_1617187112279': {'attribute_name': 'Degree Name', 'attribute_value_mlt': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}]}, 'item_1617187136212': {'attribute_name': 'Date Granted', 'attribute_value_mlt': [{'subitem_1551256096004': '2021-06-30'}]}, 'item_1617187187528': {'attribute_name': 'Conference', 'attribute_value_mlt': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'item_1617265215918': {'attribute_name': 'Version Type', 'attribute_value_mlt': [{'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}]}, 'item_1617349709064': {'attribute_name': 'Contributor', 'attribute_value_mlt': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'contributorType': 'ContactPerson', 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'lang': 'ja', 'contributorName': '情報, 太郎'}, {'lang': 'ja-Kana', 'contributorName': 'ジョウホウ, タロウ'}, {'lang': 'en', 'contributorName': 'Joho, Taro'}]}]}, 'item_1617349808926': {'attribute_name': 'Version', 'attribute_value_mlt': [{'subitem_1523263171732': 'Version'}]}, 'item_1617351524846': {'attribute_name': 'APC', 'attribute_value_mlt': [{'subitem_1523260933860': 'Unknown'}]}, 'item_1617353299429': {'attribute_name': 'Relation', 'attribute_value_mlt': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}]}, 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'url': {'url': 'https://weko3.example.org/record/2.1/files/1KB.pdf'}, 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'format': 'text/plain', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'mimetype': 'application/pdf', 'accessrole': 'open_access', 'version_id': '6f80e3cb-f681-45eb-bd54-b45be0f7d3ee', 'displaytype': 'simple'}]}, 'item_1617610673286': {'attribute_name': 'Rights Holder', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}], 'rightHolderNames': [{'rightHolderName': 'Right Holder Name', 'rightHolderLanguage': 'ja'}]}]}, 'item_1617620223087': {'attribute_name': 'Heading', 'attribute_value_mlt': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}]}, 'item_1617944105607': {'attribute_name': 'Degree Grantor', 'attribute_value_mlt': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}]}, 'relation_version_is_last': True}
    b = {'pid': {'type': 'depid', 'value': '2.0', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'owners': [1], 'status': 'published', '$schema': '15', 'pubdate': '2021-02-13', 'edit_mode': 'keep', 'created_by': 1, 'deleted_items': ['item_1617187056579', 'approval1', 'approval2'], 'shared_user_id': -1, 'weko_shared_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000002(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}]}, {'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 三郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '3', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\\nDescription<br/>Description&EMPTY&\\nDescription', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'en'}, {'subitem_description': '概要\\n概要&EMPTY&\\n概要\\n概要', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'ja'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617186783814': [{'subitem_identifier_uri': 'http://localhost', 'subitem_identifier_type': 'URI'}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617349709064': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'contributorType': 'ContactPerson', 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'lang': 'ja', 'contributorName': '情報, 太郎'}, {'lang': 'ja-Kana', 'contributorName': 'ジョウホウ, タロウ'}, {'lang': 'en', 'contributorName': 'Joho, Taro'}]}], 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617605131499': [{'url': {'url': 'https://weko3.example.org/record/2/files/1KB.pdf'}, 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'format': 'text/plain', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'mimetype': 'application/pdf', 'accessrole': 'open_access', 'version_id': 'c92410f6-ed23-4d2e-a8c5-0b3b06cc79c8', 'displaytype': 'simple'}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}], 'rightHolderNames': [{'rightHolderName': 'Right Holder Name', 'rightHolderLanguage': 'ja'}]}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}], 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}]}
    # deposit = WekoDeposit.create(a)
    # print("deposit: {}".format(deposit))
