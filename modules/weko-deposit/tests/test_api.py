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

import json
import copy
import os
import shutil
import jsonschema
import pytest
import tempfile
import uuid
from collections import OrderedDict
from datetime import datetime
from unittest import mock
from unittest.mock import patch, PropertyMock, MagicMock
from six import BytesIO

from flask import session, abort
from flask_login import login_user
from redis import RedisError
from invenio_accounts.testutils import login_user_via_session
from invenio_accounts.models import User
from invenio_files_rest.models import Bucket, Location, ObjectVersion, FileInstance
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.errors import PIDInvalidAction
from invenio_search.engine import search
from invenio_records.errors import MissingModelError
from invenio_records_rest.errors import PIDResolveRESTError
from invenio_records_files.api import FileObject, Record
from invenio_records.api import RecordRevision
from invenio_records.models import RecordMetadata
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from weko_admin.models import AdminSettings
from weko_items_ui.config import WEKO_ITEMS_UI_MS_MIME_TYPE
from weko_records.api import FeedbackMailList, ItemLink, ItemsMetadata, WekoRecord
from weko_records.models import ItemMetadata
from weko_records.utils import get_options_and_order_list
from weko_redis.errors import WekoRedisError
from weko_workflow.models import Activity
from weko_workflow.utils import get_url_root

from weko_deposit.api import (
    WekoDeposit, WekoFileObject, WekoIndexer, serialize_relations,
    WekoRecord, _FormatSysBibliographicInformation, _FormatSysCreator)
from weko_deposit.config import WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS, WEKO_DEPOSIT_ES_PARSING_ERROR_KEYWORD
from weko_deposit.errors import WekoDepositError


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp


class MockClient():
    def __init__(self):
        self.is_get_error = True

    def update_get_error(self, flg):
        self.is_get_error = flg

    def search(self, index=None, doc_type=None, body=None, scroll=None):
        return None

    def index(self, index=None, doc_type=None, id=None, body=None, version=None, version_type=None):
        return {}

    def get(self, index=None, doc_type=None, id=None, body=None):
        return {"_source": {"authorNameInfo": {},
                            "authorIdInfo": {},
                            "emailInfo": {},
                            "affiliationInfo": {}
                            }
                }

    def update(self, index=None, doc_type=None, id=None, body=None):
        if self.is_get_error:
            raise search.exceptions.NotFoundError
        else:
            return None

    def delete(self, index=None, doc_type=None, id=None, routing=None):
        return None

    def exists(self, index=None, doc_type=None, id=None):
        return None

# class WekoFileObject(FileObject):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoFileObject -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp


class TestWekoFileObject:

    # def __init__(self, obj, data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoFileObject::test___init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test___init__(self, app, location):

        with patch('weko_deposit.api.weko_logger') as mock_logger:
            bucket = Bucket.create()
            key = 'hello.txt'
            stream = BytesIO(b'helloworld')
            obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
            with app.test_request_context():
                file = WekoFileObject(obj, {})
                assert type(file) == WekoFileObject

            mock_logger.assert_any_call(
                key='WEKO_COMMON_CALLED_ARGUMENT', arg=mock.ANY)
            mock_logger.reset_mock()

    # def info(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoFileObject::test_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_info(self, app, location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            bucket = Bucket.create()
            key = 'hello.txt'
            stream = BytesIO(b'helloworld')
            obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
            with app.test_request_context():
                file = WekoFileObject(obj, {})
                assert file.info() == {'bucket': '{}'.format(file.bucket.id), 'checksum': 'sha256:936a185caaa266bb9cbe981e9e05cb78cd732b0b3280eb944412bb6f8f8f07af',
                                       'key': 'hello.txt', 'size': 10, 'version_id': '{}'.format(file.version_id)}
                file.filename = key
                file['filename'] = key
                assert file.info() == {'bucket': '{}'.format(file.bucket.id), 'checksum': 'sha256:936a185caaa266bb9cbe981e9e05cb78cd732b0b3280eb944412bb6f8f8f07af',
                                       'key': 'hello.txt', 'size': 10, 'version_id': '{}'.format(file.version_id), 'filename': 'hello'}

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch='filename exsisted')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #  def file_preview_able(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoFileObject::test_file_preview_able -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_file_preview_able(self, app, location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            bucket = Bucket.create()
            key = 'hello.txt'
            stream = BytesIO(b'helloworld')
            obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
            with app.test_request_context():
                file = WekoFileObject(obj, {})
                assert file.file_preview_able() == True
                app.config["WEKO_ITEMS_UI_MS_MIME_TYPE"] = WEKO_ITEMS_UI_MS_MIME_TYPE
                app.config["WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT+"] = {
                    'ms_word': 30, 'ms_powerpoint': 20, 'ms_excel': 10}
                assert file.file_preview_able() == True
                file.data['format'] = 'application/vnd.ms-excel'
                assert file.file_preview_able() == True
                file.data['size'] = 10000000+1
                assert file.file_preview_able()==False

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()


# class WekoIndexer(RecordIndexer):

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestWekoIndexer:

    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_es_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_es_index(self, app):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer = WekoIndexer()
            assert isinstance(indexer, WekoIndexer)

            # def get_es_index(self):
            with app.test_request_context():
                indexer.get_es_index()
                assert indexer.es_index == app.config['SEARCH_UI_SEARCH_INDEX']
                assert indexer.es_doc_type == app.config['INDEXER_DEFAULT_DOCTYPE']
                assert indexer.file_doc_type == 'content'

    #  def upload_metadata(self, jrc, item_id, revision_id, skip_files=False):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_upload_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_upload_metadata(self, app, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record_data = records[0]['record_data']
            item_id = records[0]['recid'].id
            revision_id = 5
            skip_files = False
            title = 'UPDATE{}'.format(uuid.uuid4())
            record_data['title'] = title
            indexer.upload_metadata(
                record_data, item_id, revision_id, skip_files)
            ret = indexer.get_metadata_by_item_id(item_id)
            assert ret['_source']['title'] == title

            # mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def delete_file_index(self, body, parent_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_delete_file_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_file_index(self, app, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            dep = WekoDeposit(record, record.model)
            indexer.delete_file_index([record.id], record.pid)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

            # Elastic Search Not Found Error
            with pytest.raises(search.exceptions.NotFoundError):
                indexer.get_metadata_by_item_id(record.pid)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.assert_any_call(
                    key='WEKO_DEPOSIT_FAILED_DELETE_FILE_INDEX', record_id=mock.ANY, ex=mock.ANY)
                mock_logger.reset_mock()

            # Elastic Search Unexpected Error
            with patch("invenio_search.engine.search.OpenSearch.delete", side_effect=Exception("test_error")):
                indexer.delete_file_index([record.id], record.pid)
                # mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
                mock_logger.reset_mock()

    # def update_relation_version_is_last(self, version):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_relation_version_is_last -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_relation_version_is_last(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            version = records[0]['record']
            pid = records[0]['recid']
            relations = serialize_relations(pid)
            relations_ver = relations['version'][0]
            relations_ver['id'] = pid.object_uuid
            relations_ver['is_last'] = relations_ver.get('index') == 0
            assert indexer.update_relation_version_is_last(relations_ver) == {'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': '{}'.format(
                pid.object_uuid), '_version': 2, 'result': 'noop', '_shards': {'total': 0, 'successful': 0, 'failed': 0}}

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def update_es_data(self, record, update_revision=True,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_es_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_es_data(self, es_records_1, db):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records_1
            record = records[0]['record']
            # update_oai=False
            result = indexer.update_es_data(record, update_revision=False, update_oai=False, is_deleted=False)
            assert result["_index"] == "test-weko-item-v1.0.0"
            assert result["_id"] == str(records[0]["rec_uuid"])
            assert result["_primary_term"] == 1
            assert result["_seq_no"] == 9
            assert result["_version"] == 4
            assert result["_shards"] == {'total': 2, 'successful': 1, 'failed': 0}
            assert result["result"] == "updated"

            # update_oai=True
            result = indexer.update_es_data(record, update_revision=False, update_oai=True, is_deleted=False)
            assert result["_index"] == "test-weko-item-v1.0.0"
            assert result["_id"] == str(records[0]["rec_uuid"])
            assert result["_primary_term"] == 1
            assert result["_seq_no"] == 10
            assert result["_shards"] == {'failed': 0, 'successful': 1, 'total': 2}
            assert result["_version"] == 5
            assert result["result"] == "updated"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            record = records[1]['record']
            record.model.version_id = 4
            db.session.merge(record.model)
            db.session.commit()
            result = indexer.update_es_data(record, update_revision=True, update_oai=True, is_deleted=False)
            assert result["_index"] == "test-weko-item-v1.0.0"
            assert result["_id"] == str(records[1]["rec_uuid"])
            assert result["_primary_term"] == 1
            assert result["_seq_no"] == 11
            assert result["_shards"] == {'failed': 0, 'successful': 1, 'total': 2}
            assert result["_version"] == 4
            assert result["result"] == "updated"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def index(self, record):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_index(self, es_records):
        indexer, records = es_records
        record = records[0]['record']
        indexer.index(record)

    # def delete(self, record):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete(self, es_records):
        indexer, records = es_records
        record = records[0]['record']
        indexer.delete(record)
        with pytest.raises(search.exceptions.NotFoundError):
            indexer.get_metadata_by_item_id(record.pid)

    #     def delete_by_id(self, uuid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_delete_by_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_by_id(self, es_records):
        indexer, records = es_records
        record = records[0]['record']
        indexer.delete_by_id(record.id)
        with pytest.raises(search.exceptions.NotFoundError):
            indexer.get_metadata_by_item_id(record.pid)

        indexer.delete_by_id(record.id)

        with patch("invenio_search.engine.search.OpenSearch.delete", side_effect=Exception("test_error")):
            indexer.delete_by_id(record.id)

    # def get_count_by_index_id(self, tree_path):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_count_by_index_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_count_by_index_id(self, es_records):
        # with patch('weko_deposit.api.weko_logger') as mock_logger:
        indexer, records = es_records
        metadata = records[0]['record_data']
        ret = indexer.get_count_by_index_id("1")
        assert ret == 4
        ret = indexer.get_count_by_index_id("2")
        assert ret == 5

        # mock_logger.assert_any_call(
        #     key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
        # mock_logger.reset_mock()

    #     def get_pid_by_es_scroll(self, path):
    #         def get_result(result):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_pid_by_es_scroll -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_pid_by_es_scroll(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            ret = indexer.get_pid_by_es_scroll(1)
            assert isinstance(next(ret), list)
            assert isinstance(next(ret), dict)
            assert ret is not None

            ret = indexer.get_pid_by_es_scroll(None)
            assert ret is not None

            ret = indexer.get_pid_by_es_scroll('non_existent_path_12345')

            assert ret is not None
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def get_metadata_by_item_id(self, item_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_metadata_by_item_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_metadata_by_item_id(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:

            indexer, records = es_records
            record = records[0]['record']
            record_data = records[0]['record_data']
            ret = indexer.get_metadata_by_item_id(record.id)
            assert ret['_index'] == 'test-weko-item-v1.0.0'

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def update_feedback_mail_list(self, feedback_mail):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_feedback_mail_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_feedback_mail_list(selft, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            feedback_mail = {'id': record.id, 'mail_list': [
                {'email': 'wekosoftware@nii.ac.jp', 'author_id': ''}]}
            ret = indexer.update_feedback_mail_list(feedback_mail)
            assert ret == {'_index': 'test-weko-item-v1.0.0', '_id': '{}'.format(
                record.id), '_version': 3, 'result': 'updated', '_shards': {'total': 2, 'successful': 1, 'failed': 0}, '_seq_no': 9, '_primary_term': 1}

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def update_author_link(self, author_link):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_author_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_author_link(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            author_link_info = {
                "id": record.id,
                "author_link": ['0']
            }
            # todo19
            ret = indexer.update_author_link(author_link_info)
            assert ret == {'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': '{}'.format(record.id), '_version': 3, 'result': 'updated', '_shards': {'total': 2, 'successful': 1, 'failed': 0}, '_seq_no': 9, '_primary_term': 1}

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def update_jpcoar_identifier(self, dc, item_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_jpcoar_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_jpcoar_identifier(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record_data = records[0]['record_data']
            record = records[0]['record']
            assert indexer.update_jpcoar_identifier(record_data, record.id) == {'_index': 'test-weko-item-v1.0.0', '_id': '{}'.format(
                record.id), '_version': 3, 'result': 'updated', '_shards': {'total': 2, 'successful': 1, 'failed': 0}, '_seq_no': 9, '_primary_term': 1}

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def __build_bulk_es_data(self, updated_data):
    #     def bulk_update(self, updated_data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_bulk_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_bulk_update(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            # es_data is None
            indexer, records = es_records
            res = []

            with patch("weko_deposit.api.bulk", side_effect=search.helpers.bulk) as mock_bulk:
                indexer.bulk_update(res)
                assert mock_bulk.call_count == 1

            res.append(records[0]['record'])
            res.append(records[1]['record'])
            res.append(records[2]['record'])
            indexer.bulk_update(res)

            with patch("weko_deposit.api.search.helpers.bulk", return_value=(0, ["test_error1", "test_error2"])):
                indexer.bulk_update(res)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

# class WekoDeposit(Deposit):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
# @pytest.mark.usefixtures("app", "db", "location", "es_records", "es_records_1", "client", "users", "db_index", "db_activity", "db_itemtype", "bucket")
class TestWekoDeposit():
    # def item_metadata(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_item_metadata(self, app, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            deposit = records[0]['deposit']
            assert deposit.item_metadata == {'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'title', 'owners': [1], 'status': 'published', '$schema': '/items/jsonschema/1', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {
                'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}}

            deposit = WekoDeposit({})
            with pytest.raises(NoResultFound):
                assert deposit.item_metadata == ""

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def is_published(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_is_published -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_published(self, app, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            deposit = records[0]['deposit']
            assert deposit.is_published() == True

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def merge_with_published(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_merge_with_published -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_merge_with_published(self, app, db, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            dep = records[0]['deposit']
            ret = dep.merge_with_published()
            assert isinstance(ret, RecordRevision) == True

            dep = records[1]["deposit"]
            dep["$schema"] = "https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"
            dep["control_number"] = "1"
            db.session.commit()
            ret = dep.merge_with_published()
            assert isinstance(ret, RecordRevision) == True

            from dictdiffer.merge import UnresolvedConflictsException
            with patch("weko_deposit.api.Merger.run",side_effect=UnresolvedConflictsException("Some error has occurred in weko_deposit")):
                with pytest.raises(WekoDepositError):
                    ret = dep.merge_with_published()


            with patch("weko_deposit.api.Merger.run", side_effect=Exception("test_error")):
                with pytest.raises(WekoDepositError):
                    ret = dep.merge_with_published()
                    mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

            # if '_deposit' in args: is false
            pid, first = dep.fetch_published()
            if '_deposit' in first:
                del first['_deposit']
            with patch("invenio_deposit.api.Deposit.fetch_published") as mock_fetch_published:
                mock_fetch_published.return_value = (pid, first)
                ret = dep.merge_with_published()
                assert isinstance(ret, RecordRevision) == True

    # def _patch(diff_result, destination, in_place=False):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__patch -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__patch(self, app, location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                dep = WekoDeposit.create({})
                # diff_result = [('change', '_buckets.deposit', ('753ff0d7-0659-4460-9b1a-fd1ef38467f2', '688f2d41-be61-468f-95e2-a06abefdaf60')), ('change', '_buckets.deposit', ('753ff0d7-0659-4460-9b1a-fd1ef38467f2', '688f2d41-be61-468f-95e2-a06abefdaf60')), ('add', '', [('_oai', {})]), ('add', '', [('_oai', {})]), ('add', '_oai', [('id', 'oai:weko3.example.org:00000013')]), ('add', '_oai', [('id', 'oai:weko3.example.org:00000013')]), ('add', '_oai', [('sets', [])]), ('add', '_oai', [('sets', [])]), ('add', '_oai.sets', [(0, '1661517684078')]), ('add', '_oai.sets', [(0, '1661517684078')]), ('add', '', [('author_link', [])]), ('add', '', [('author_link', [])]), ('add', 'author_link', [(0, '4')]), ('add', 'author_link', [(0, '4')]), ('add', '', [('item_1617186331708', {})]), ('add', '', [('item_1617186331708', {})]), ('add', 'item_1617186331708', [('attribute_name', 'Title')]), ('add', 'item_1617186331708', [('attribute_name', 'Title')]), ('add', 'item_1617186331708', [('attribute_value_mlt', [])]), ('add', 'item_1617186331708', [('attribute_value_mlt', [])]), ('add', 'item_1617186331708.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186331708.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255647225', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255647225', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255648112', 'ja')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255648112', 'ja')]), ('add', 'item_1617186331708.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186331708.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255647225', 'en_conference paperITEM00000001(public_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255647225', 'en_conference paperITEM00000001(public_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255648112', 'en')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255648112', 'en')]), ('add', '', [('item_1617186385884', {})]), ('add', '', [('item_1617186385884', {})]), ('add', 'item_1617186385884', [('attribute_name', 'Alternative Title')]), ('add', 'item_1617186385884', [('attribute_name', 'Alternative Title')]), ('add', 'item_1617186385884', [('attribute_value_mlt', [])]), ('add', 'item_1617186385884', [('attribute_value_mlt', [])]), ('add', 'item_1617186385884.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186385884.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255721061', 'en')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255721061', 'en')]), ('add', 'item_1617186385884.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186385884.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255721061', 'ja')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255721061', 'ja')]), ('add', '', [('item_1617186419668', {})]), ('add', '', [('item_1617186419668', {})]), ('add', 'item_1617186419668', [('attribute_name', 'Creator')]), ('add', 'item_1617186419668', [('attribute_name', 'Creator')]), ('add', 'item_1617186419668', [('attribute_type', 'creator')]), ('add', 'item_1617186419668', [('attribute_type', 'creator')]), ('add', 'item_1617186419668', [('attribute_value_mlt', [])]), ('add', 'item_1617186419668', [('attribute_value_mlt', [])]), ('add', 'item_1617186419668.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186419668.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorAffiliations', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorAffiliations', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifier', '0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifier', '0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierScheme', 'ISNI')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierScheme', 'ISNI')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierURI', 'http://isni.org/isni/0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierURI', 'http://isni.org/isni/0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationName', 'University')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationName', 'University')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', '4')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', '4')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'WEKO')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'WEKO')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(3, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(3, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', 'item_1617186419668.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186419668.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', 'item_1617186419668.attribute_value_mlt', [(2, {})]), ('add', 'item_1617186419668.attribute_value_mlt', [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', '', [('item_1617186476635', {})]), ('add', '', [('item_1617186476635', {})]), ('add', 'item_1617186476635', [('attribute_name', 'Access Rights')]), ('add', 'item_1617186476635', [('attribute_name', 'Access Rights')]), ('add', 'item_1617186476635', [('attribute_value_mlt', [])]), ('add', 'item_1617186476635', [('attribute_value_mlt', [])]), ('add', 'item_1617186476635.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186476635.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1522299639480', 'open access')]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1522299639480', 'open access')]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1600958577026', 'http://purl.org/coar/access_right/c_abf2')]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1600958577026', 'http://purl.org/coar/access_right/c_abf2')]), ('add', '', [('item_1617186499011', {})]), ('add', '', [('item_1617186499011', {})]), ('add', 'item_1617186499011', [('attribute_name', 'Rights')]), ('add', 'item_1617186499011', [('attribute_name', 'Rights')]), ('add', 'item_1617186499011', [('attribute_value_mlt', [])]), ('add', 'item_1617186499011', [('attribute_value_mlt', [])]), ('add', 'item_1617186499011.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186499011.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650717957', 'ja')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650717957', 'ja')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650727486', 'http://localhost')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650727486', 'http://localhost')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522651041219', 'Rights Information')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522651041219', 'Rights Information')]), ('add', '', [('item_1617186609386', {})]), ('add', '', [('item_1617186609386', {})]), ('add', 'item_1617186609386', [('attribute_name', 'Subject')]), ('add', 'item_1617186609386', [('attribute_name', 'Subject')]), ('add', 'item_1617186609386', [('attribute_value_mlt', [])]), ('add', 'item_1617186609386', [('attribute_value_mlt', [])]), ('add', 'item_1617186609386.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186609386.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522299896455', 'ja')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522299896455', 'ja')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300014469', 'Other')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300014469', 'Other')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300048512', 'http://localhost/')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300048512', 'http://localhost/')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1523261968819', 'Sibject1')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1523261968819', 'Sibject1')]), ('add', '', [('item_1617186626617', {})]), ('add', '', [('item_1617186626617', {})]), ('add', 'item_1617186626617', [('attribute_name', 'Description')]), ('add', 'item_1617186626617', [('attribute_name', 'Description')]), ('add', 'item_1617186626617', [('attribute_value_mlt', [])]), ('add', 'item_1617186626617', [('attribute_value_mlt', [])]), ('add', 'item_1617186626617.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186626617.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description', 'Description\nDescription<br/>Description')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description', 'Description\nDescription<br/>Description')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_language', 'en')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_language', 'en')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_type', 'Abstract')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_type', 'Abstract')]), ('add', 'item_1617186626617.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186626617.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description', '概要\n概要\n概要\n概要')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description', '概要\n概要\n概要\n概要')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_language', 'ja')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_language', 'ja')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_type', 'Abstract')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_type', 'Abstract')]), ('add', '', [('item_1617186643794', {})]), ('add', '', [('item_1617186643794', {})]), ('add', 'item_1617186643794', [('attribute_name', 'Publisher')]), ('add', 'item_1617186643794', [('attribute_name', 'Publisher')]), ('add', 'item_1617186643794', [('attribute_value_mlt', [])]), ('add', 'item_1617186643794', [('attribute_value_mlt', [])]), ('add', 'item_1617186643794.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186643794.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300295150', 'en')]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300295150', 'en')]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300316516', 'Publisher')]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300316516', 'Publisher')]), ('add', '', [('item_1617186660861', {})]), ('add', '', [('item_1617186660861', {})]), ('add', 'item_1617186660861', [('attribute_name', 'Date')]), ('add', 'item_1617186660861', [('attribute_name', 'Date')]), ('add', 'item_1617186660861', [('attribute_value_mlt', [])]), ('add', 'item_1617186660861', [('attribute_value_mlt', [])]), ('add', 'item_1617186660861.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186660861.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300695726', 'Available')]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300695726', 'Available')]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300722591', '2021-06-30')]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300722591', '2021-06-30')]), ('add', '', [('item_1617186702042', {})]), ('add', '', [('item_1617186702042', {})]), ('add', 'item_1617186702042', [('attribute_name', 'Language')]), ('add', 'item_1617186702042', [('attribute_name', 'Language')]), ('add', 'item_1617186702042', [('attribute_value_mlt', [])]), ('add', 'item_1617186702042', [('attribute_value_mlt', [])]), ('add', 'item_1617186702042.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186702042.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186702042', 'attribute_value_mlt', 0], [('subitem_1551255818386', 'jpn')]), ('add', ['item_1617186702042', 'attribute_value_mlt', 0], [('subitem_1551255818386', 'jpn')]), ('add', '', [('item_1617186783814', {})]), ('add', '', [('item_1617186783814', {})]), ('add', 'item_1617186783814', [('attribute_name', 'Identifier')]), ('add', 'item_1617186783814', [('attribute_name', 'Identifier')]), ('add', 'item_1617186783814', [('attribute_value_mlt', [])]), ('add', 'item_1617186783814', [('attribute_value_mlt', [])]), ('add', 'item_1617186783814.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186783814.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_type', 'URI')]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_type', 'URI')]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_uri', 'http://localhost')]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_uri', 'http://localhost')]), ('add', '', [('item_1617186859717', {})]), ('add', '', [('item_1617186859717', {})]), ('add', 'item_1617186859717', [('attribute_name', 'Temporal')]), ('add', 'item_1617186859717', [('attribute_name', 'Temporal')]), ('add', 'item_1617186859717', [('attribute_value_mlt', [])]), ('add', 'item_1617186859717', [('attribute_value_mlt', [])]), ('add', 'item_1617186859717.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186859717.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658018441', 'en')]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658018441', 'en')]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658031721', 'Temporal')]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658031721', 'Temporal')]), ('add', '', [('item_1617186882738', {})]), ('add', '', [('item_1617186882738', {})]), ('add', 'item_1617186882738', [('attribute_name', 'Geo Location')]), ('add', 'item_1617186882738', [('attribute_name', 'Geo Location')]), ('add', 'item_1617186882738', [('attribute_value_mlt', [])]), ('add', 'item_1617186882738', [('attribute_value_mlt', [])]), ('add', 'item_1617186882738.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186882738.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0], [('subitem_geolocation_place', [])]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0], [('subitem_geolocation_place', [])]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place'], [(0, {})]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place'], [(0, {})]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place', 0], [('subitem_geolocation_place_text', 'Japan')]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place', 0], [('subitem_geolocation_place_text', 'Japan')]), ('add', '', [('item_1617186901218', {})]), ('add', '', [('item_1617186901218', {})]), ('add', 'item_1617186901218', [('attribute_name', 'Funding Reference')]), ('add', 'item_1617186901218', [('attribute_name', 'Funding Reference')]), ('add', 'item_1617186901218', [('attribute_value_mlt', [])]), ('add', 'item_1617186901218', [('attribute_value_mlt', [])]), ('add', 'item_1617186901218.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186901218.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399143519', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399143519', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399281603', 'ISNI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399281603', 'ISNI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399333375', 'http://xxx')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399333375', 'http://xxx')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399412622', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399412622', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522399416691', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522399416691', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522737543681', 'Funder Name')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522737543681', 'Funder Name')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399571623', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399571623', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399585738', 'Award URI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399585738', 'Award URI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399628911', 'Award Number')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399628911', 'Award Number')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399651758', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399651758', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721910626', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721910626', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721929892', 'Award Title')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721929892', 'Award Title')]), ('add', '', [('item_1617186920753', {})]), ('add', '', [('item_1617186920753', {})]), ('add', 'item_1617186920753', [('attribute_name', 'Source Identifier')]), ('add', 'item_1617186920753', [('attribute_name', 'Source Identifier')]), ('add', 'item_1617186920753', [('attribute_value_mlt', [])]), ('add', 'item_1617186920753', [('attribute_value_mlt', [])]), ('add', 'item_1617186920753.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186920753.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646500366', 'ISSN')]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646500366', 'ISSN')]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646572813', 'xxxx-xxxx-xxxx')]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646572813', 'xxxx-xxxx-xxxx')]), ('add', '', [('item_1617186941041', {})]), ('add', '', [('item_1617186941041', {})]), ('add', 'item_1617186941041', [('attribute_name', 'Source Title')]), ('add', 'item_1617186941041', [('attribute_name', 'Source Title')]), ('add', 'item_1617186941041', [('attribute_value_mlt', [])]), ('add', 'item_1617186941041', [('attribute_value_mlt', [])]), ('add', 'item_1617186941041.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186941041.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650068558', 'en')]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650068558', 'en')]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650091861', 'Source Title')]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650091861', 'Source Title')]), ('add', '', [('item_1617186959569', {})]), ('add', '', [('item_1617186959569', {})]), ('add', 'item_1617186959569', [('attribute_name', 'Volume Number')]), ('add', 'item_1617186959569', [('attribute_name', 'Volume Number')]), ('add', 'item_1617186959569', [('attribute_value_mlt', [])]), ('add', 'item_1617186959569', [('attribute_value_mlt', [])]), ('add', 'item_1617186959569.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186959569.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186959569', 'attribute_value_mlt', 0], [('subitem_1551256328147', '1')]), ('add', ['item_1617186959569', 'attribute_value_mlt', 0], [('subitem_1551256328147', '1')]), ('add', '', [('item_1617186981471', {})]), ('add', '', [('item_1617186981471', {})]), ('add', 'item_1617186981471', [('attribute_name', 'Issue Number')]), ('add', 'item_1617186981471', [('attribute_name', 'Issue Number')]), ('add', 'item_1617186981471', [('attribute_value_mlt', [])]), ('add', 'item_1617186981471', [('attribute_value_mlt', [])]), ('add', 'item_1617186981471.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186981471.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186981471', 'attribute_value_mlt', 0], [('subitem_1551256294723', '111')]), ('add', ['item_1617186981471', 'attribute_value_mlt', 0], [('subitem_1551256294723', '111')]), ('add', '', [('item_1617186994930', {})]), ('add', '', [('item_1617186994930', {})]), ('add', 'item_1617186994930', [('attribute_name', 'Number of Pages')]), ('add', 'item_1617186994930', [('attribute_name', 'Number of Pages')]), ('add', 'item_1617186994930', [('attribute_value_mlt', [])]), ('add', 'item_1617186994930', [('attribute_value_mlt', [])]), ('add', 'item_1617186994930.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186994930.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186994930', 'attribute_value_mlt', 0], [('subitem_1551256248092', '12')]), ('add', ['item_1617186994930', 'attribute_value_mlt', 0], [('subitem_1551256248092', '12')]), ('add', '', [('item_1617187024783', {})]), ('add', '', [('item_1617187024783', {})]), ('add', 'item_1617187024783', [('attribute_name', 'Page Start')]), ('add', 'item_1617187024783', [('attribute_name', 'Page Start')]), ('add', 'item_1617187024783', [('attribute_value_mlt', [])]), ('add', 'item_1617187024783', [('attribute_value_mlt', [])]), ('add', 'item_1617187024783.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187024783.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187024783', 'attribute_value_mlt', 0], [('subitem_1551256198917', '1')]), ('add', ['item_1617187024783', 'attribute_value_mlt', 0], [('subitem_1551256198917', '1')]), ('add', '', [('item_1617187045071', {})]), ('add', '', [('item_1617187045071', {})]), ('add', 'item_1617187045071', [('attribute_name', 'Page End')]), ('add', 'item_1617187045071', [('attribute_name', 'Page End')]), ('add', 'item_1617187045071', [('attribute_value_mlt', [])]), ('add', 'item_1617187045071', [('attribute_value_mlt', [])]), ('add', 'item_1617187045071.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187045071.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187045071', 'attribute_value_mlt', 0], [('subitem_1551256185532', '3')]), ('add', ['item_1617187045071', 'attribute_value_mlt', 0], [('subitem_1551256185532', '3')]), ('add', '', [('item_1617187112279', {})]), ('add', '', [('item_1617187112279', {})]), ('add', 'item_1617187112279', [('attribute_name', 'Degree Name')]), ('add', 'item_1617187112279', [('attribute_name', 'Degree Name')]), ('add', 'item_1617187112279', [('attribute_value_mlt', [])]), ('add', 'item_1617187112279', [('attribute_value_mlt', [])]), ('add', 'item_1617187112279.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187112279.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256126428', 'Degree Name')]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256126428', 'Degree Name')]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256129013', 'en')]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256129013', 'en')]), ('add', '', [('item_1617187136212', {})]), ('add', '', [('item_1617187136212', {})]), ('add', 'item_1617187136212', [('attribute_name', 'Date Granted')]), ('add', 'item_1617187136212', [('attribute_name', 'Date Granted')]), ('add', 'item_1617187136212', [('attribute_value_mlt', [])]), ('add', 'item_1617187136212', [('attribute_value_mlt', [])]), ('add', 'item_1617187136212.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187136212.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187136212', 'attribute_value_mlt', 0], [('subitem_1551256096004', '2021-06-30')]), ('add', ['item_1617187136212', 'attribute_value_mlt', 0], [('subitem_1551256096004', '2021-06-30')]), ('add', '', [('item_1617187187528', {})]), ('add', '', [('item_1617187187528', {})]), ('add', 'item_1617187187528', [('attribute_name', 'Conference')]), ('add', 'item_1617187187528', [('attribute_name', 'Conference')]), ('add', 'item_1617187187528', [('attribute_value_mlt', [])]), ('add', 'item_1617187187528', [('attribute_value_mlt', [])]), ('add', 'item_1617187187528.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187187528.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711633003', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711633003', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711636923', 'Conference Name')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711636923', 'Conference Name')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711645590', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711645590', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711655652', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711655652', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711660052', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711660052', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711680082', 'Sponsor')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711680082', 'Sponsor')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711686511', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711686511', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711699392', {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711699392', {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711704251', '2020/12/11')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711704251', '2020/12/11')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711712451', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711712451', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711727603', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711727603', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711731891', '2000')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711731891', '2000')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711735410', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711735410', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711739022', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711739022', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711743722', '2020')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711743722', '2020')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711745532', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711745532', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711758470', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711758470', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711769260', 'Conference Venue')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711769260', 'Conference Venue')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711775943', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711775943', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711788485', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711788485', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711798761', 'Conference Place')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711798761', 'Conference Place')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711803382', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711803382', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711813532', 'JPN')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711813532', 'JPN')]), ('add', '', [('item_1617258105262', {})]), ('add', '', [('item_1617258105262', {})]), ('add', 'item_1617258105262', [('attribute_name', 'Resource Type')]), ('add', 'item_1617258105262', [('attribute_name', 'Resource Type')]), ('add', 'item_1617258105262', [('attribute_value_mlt', [])]), ('add', 'item_1617258105262', [('attribute_value_mlt', [])]), ('add', 'item_1617258105262.attribute_value_mlt', [(0, {})]), ('add', 'item_1617258105262.attribute_value_mlt', [(0, {})]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourcetype', 'conference paper')]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourcetype', 'conference paper')]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourceuri', 'http://purl.org/coar/resource_type/c_5794')]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourceuri', 'http://purl.org/coar/resource_type/c_5794')]), ('add', '', [('item_1617265215918', {})]), ('add', '', [('item_1617265215918', {})]), ('add', 'item_1617265215918', [('attribute_name', 'Version Type')]), ('add', 'item_1617265215918', [('attribute_name', 'Version Type')]), ('add', 'item_1617265215918', [('attribute_value_mlt', [])]), ('add', 'item_1617265215918', [('attribute_value_mlt', [])]), ('add', 'item_1617265215918.attribute_value_mlt', [(0, {})]), ('add', 'item_1617265215918.attribute_value_mlt', [(0, {})]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1522305645492', 'AO')]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1522305645492', 'AO')]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1600292170262', 'http://purl.org/coar/version/c_b1a7d7d4d402bcce')]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1600292170262', 'http://purl.org/coar/version/c_b1a7d7d4d402bcce')]), ('add', '', [('item_1617349709064', {})]), ('add', '', [('item_1617349709064', {})]), ('add', 'item_1617349709064', [('attribute_name', 'Contributor')]), ('add', 'item_1617349709064', [('attribute_name', 'Contributor')]), ('add', 'item_1617349709064', [('attribute_value_mlt', [])]), ('add', 'item_1617349709064', [('attribute_value_mlt', [])]), ('add', 'item_1617349709064.attribute_value_mlt', [(0, {})]), ('add', 'item_1617349709064.attribute_value_mlt', [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorMails', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorMails', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails', 0], [('contributorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails', 0], [('contributorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('contributorName', '情報, 太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('contributorName', '情報, 太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('lang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('lang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('contributorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('contributorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('lang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('lang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('contributorName', 'Joho, Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('contributorName', 'Joho, Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('lang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('lang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorType', 'ContactPerson')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorType', 'ContactPerson')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', '', [('item_1617349808926', {})]), ('add', '', [('item_1617349808926', {})]), ('add', 'item_1617349808926', [('attribute_name', 'Version')]), ('add', 'item_1617349808926', [('attribute_name', 'Version')]), ('add', 'item_1617349808926', [('attribute_value_mlt', [])]), ('add', 'item_1617349808926', [('attribute_value_mlt', [])]), ('add', 'item_1617349808926.attribute_value_mlt', [(0, {})]), ('add', 'item_1617349808926.attribute_value_mlt', [(0, {})]), ('add', ['item_1617349808926', 'attribute_value_mlt', 0], [('subitem_1523263171732', 'Version')]), ('add', ['item_1617349808926', 'attribute_value_mlt', 0], [('subitem_1523263171732', 'Version')]), ('add', '', [('item_1617351524846', {})]), ('add', '', [('item_1617351524846', {})]), ('add', 'item_1617351524846', [('attribute_name', 'APC')]), ('add', 'item_1617351524846', [('attribute_name', 'APC')]), ('add', 'item_1617351524846', [('attribute_value_mlt', [])]), ('add', 'item_1617351524846', [('attribute_value_mlt', [])]), ('add', 'item_1617351524846.attribute_value_mlt', [(0, {})]), ('add', 'item_1617351524846.attribute_value_mlt', [(0, {})]), ('add', ['item_1617351524846', 'attribute_value_mlt', 0], [('subitem_1523260933860', 'Unknown')]), ('add', ['item_1617351524846', 'attribute_value_mlt', 0], [('subitem_1523260933860', 'Unknown')]), ('add', '', [('item_1617353299429', {})]), ('add', '', [('item_1617353299429', {})]), ('add', 'item_1617353299429', [('attribute_name', 'Relation')]), ('add', 'item_1617353299429', [('attribute_name', 'Relation')]), ('add', 'item_1617353299429', [('attribute_value_mlt', [])]), ('add', 'item_1617353299429', [('attribute_value_mlt', [])]), ('add', 'item_1617353299429.attribute_value_mlt', [(0, {})]), ('add', 'item_1617353299429.attribute_value_mlt', [(0, {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306207484', 'isVersionOf')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306207484', 'isVersionOf')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306287251', {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306287251', {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306382014', 'arXiv')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306382014', 'arXiv')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306436033', 'xxxxx')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306436033', 'xxxxx')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1523320863692', [])]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1523320863692', [])]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692'], [(0, {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692'], [(0, {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320867455', 'en')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320867455', 'en')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320909613', 'Related Title')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320909613', 'Related Title')]), ('add', '', [('item_1617605131499', {})]), ('add', '', [('item_1617605131499', {})]), ('add', 'item_1617605131499', [('attribute_name', 'File')]), ('add', 'item_1617605131499', [('attribute_name', 'File')]), ('add', 'item_1617605131499', [('attribute_type', 'file')]), ('add', 'item_1617605131499', [('attribute_type', 'file')]), ('add', 'item_1617605131499', [('attribute_value_mlt', [])]), ('add', 'item_1617605131499', [('attribute_value_mlt', [])]), ('add', 'item_1617605131499.attribute_value_mlt', [(0, {})]), ('add', 'item_1617605131499.attribute_value_mlt', [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('accessrole', 'open_access')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('accessrole', 'open_access')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('date', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('date', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateType', 'Available')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateType', 'Available')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateValue', '2021-07-12')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateValue', '2021-07-12')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('displaytype', 'simple')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('displaytype', 'simple')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filename', '1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filename', '1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filesize', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filesize', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize', 0], [('value', '1 KB')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize', 0], [('value', '1 KB')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('format', 'text/plain')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('format', 'text/plain')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('mimetype', 'application/pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('mimetype', 'application/pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('url', {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('url', {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'url'], [('url', 'https://weko3.example.org/record/13/files/1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'url'], [('url', 'https://weko3.example.org/record/13/files/1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('version_id', '7cdce099-fe63-445f-b78b-cf2909a8163f')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('version_id', '7cdce099-fe63-445f-b78b-cf2909a8163f')]), ('add', '', [('item_1617610673286', {})]), ('add', '', [('item_1617610673286', {})]), ('add', 'item_1617610673286', [('attribute_name', 'Rights Holder')]), ('add', 'item_1617610673286', [('attribute_name', 'Rights Holder')]), ('add', 'item_1617610673286', [('attribute_value_mlt', [])]), ('add', 'item_1617610673286', [('attribute_value_mlt', [])]), ('add', 'item_1617610673286.attribute_value_mlt', [(0, {})]), ('add', 'item_1617610673286.attribute_value_mlt', [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxx')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxx')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('rightHolderNames', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('rightHolderNames', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderLanguage', 'ja')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderLanguage', 'ja')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderName', 'Right Holder Name')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderName', 'Right Holder Name')]), ('add', '', [('item_1617620223087', {})]), ('add', '', [('item_1617620223087', {})]), ('add', 'item_1617620223087', [('attribute_name', 'Heading')]), ('add', 'item_1617620223087', [('attribute_name', 'Heading')]), ('add', 'item_1617620223087', [('attribute_value_mlt', [])]), ('add', 'item_1617620223087', [('attribute_value_mlt', [])]), ('add', 'item_1617620223087.attribute_value_mlt', [(0, {})]), ('add', 'item_1617620223087.attribute_value_mlt', [(0, {})]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671149650', 'ja')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671149650', 'ja')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671178623', 'Subheading')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671178623', 'Subheading')]), ('add', 'item_1617620223087.attribute_value_mlt', [(1, {})]), ('add', 'item_1617620223087.attribute_value_mlt', [(1, {})]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671149650', 'en')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671149650', 'en')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671178623', 'Subheding')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671178623', 'Subheding')]), ('add', '', [('item_1617944105607', {})]), ('add', '', [('item_1617944105607', {})]), ('add', 'item_1617944105607', [('attribute_name', 'Degree Grantor')]), ('add', 'item_1617944105607', [('attribute_name', 'Degree Grantor')]), ('add', 'item_1617944105607', [('attribute_value_mlt', [])]), ('add', 'item_1617944105607', [('attribute_value_mlt', [])]), ('add', 'item_1617944105607.attribute_value_mlt', [(0, {})]), ('add', 'item_1617944105607.attribute_value_mlt', [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256015892', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256015892', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256027296', 'xxxxxx')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256027296', 'xxxxxx')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256029891', 'kakenhi')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256029891', 'kakenhi')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256037922', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256037922', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256042287', 'Degree Grantor Name')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256042287', 'Degree Grantor Name')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256047619', 'en')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256047619', 'en')]), ('add', '', [('item_title', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', '', [('item_title', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', '', [('item_type_id', '15')]), ('add', '', [('item_type_id', '15')]), ('add', '', [('owner', '1')]), ('add', '', [('owner', '1')]), ('add', '', [('path', [])]), ('add', '', [('path', [])]), ('add', 'path', [(0, '1661517684078')]), ('add', 'path', [(0, '1661517684078')]), ('add', '', [('pubdate', {})]), ('add', '', [('pubdate', {})]), ('add', 'pubdate', [('attribute_name', 'PubDate')]), ('add', 'pubdate', [('attribute_name', 'PubDate')]), ('add', 'pubdate', [('attribute_value', '2021-08-06')]), ('add', 'pubdate', [('attribute_value', '2021-08-06')]), ('add', '', [('publish_date', '2021-08-06')]), ('add', '', [('publish_date', '2021-08-06')]), ('add', '', [('publish_status', '0')]), ('add', '', [('publish_status', '0')]), ('add', '', [('relation_version_is_last', True)]), ('add', '', [('relation_version_is_last', True)]), ('add', '', [('title', [])]), ('add', '', [('title', [])]), ('add', 'title', [(0, 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', 'title', [(0, 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', '', [('weko_shared_id', -1)]), ('add', '', [('weko_shared_id', -1)]), ('remove', '', [('test_1', "")]), ('remove', '', [('test_2', "")])]
                # distination = {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, 'test_1': {'key1': 'value1'}, 'test_2': [{'key2': 'value2'}]}
                # ret = dep._patch(diff_result,distination)
                # assert ret=={'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '688f2d41-be61-468f-95e2-a06abefdaf60'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, '_oai': {'id': 'oai:weko3.example.org:00000013', 'sets': ['1661517684078', '1661517684078']}, 'author_link': ['4', '4'], 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}, {}, {}]}, 'item_1617186385884': {'attribute_name': 'Alternative Title', 'attribute_value_mlt': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}, {}, {}]}, 'item_1617186419668': {'attribute_name': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}, {}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}, {}]}, {}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}, {}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {}, {}, {}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}, {}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}, {}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {}, {}, {}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}, {}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {}, {}, {}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}]}, {}, {}, {}]}, 'item_1617186476635': {'attribute_name': 'Access Rights', 'attribute_value_mlt': [{'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, {}]}, 'item_1617186499011': {'attribute_name': 'Rights', 'attribute_value_mlt': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}, {}]}, 'item_1617186609386': {'attribute_name': 'Subject', 'attribute_value_mlt': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}, {}]}, 'item_1617186626617': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}, {}, {}]}, 'item_1617186643794': {'attribute_name': 'Publisher', 'attribute_value_mlt': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}, {}]}, 'item_1617186660861': {'attribute_name': 'Date', 'attribute_value_mlt': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}, {}]}, 'item_1617186702042': {'attribute_name': 'Language', 'attribute_value_mlt': [{'subitem_1551255818386': 'jpn'}, {}]}, 'item_1617186783814': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}, {}]}, 'item_1617186859717': {'attribute_name': 'Temporal', 'attribute_value_mlt': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}, {}]}, 'item_1617186882738': {'attribute_name': 'Geo Location', 'attribute_value_mlt': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}, {}]}, {}]}, 'item_1617186901218': {'attribute_name': 'Funding Reference', 'attribute_value_mlt': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}, {}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}, {}]}, {}]}, 'item_1617186920753': {'attribute_name': 'Source Identifier', 'attribute_value_mlt': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}, {}]}, 'item_1617186941041': {'attribute_name': 'Source Title', 'attribute_value_mlt': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}, {}]}, 'item_1617186959569': {'attribute_name': 'Volume Number', 'attribute_value_mlt': [{'subitem_1551256328147': '1'}, {}]}, 'item_1617186981471': {'attribute_name': 'Issue Number', 'attribute_value_mlt': [{'subitem_1551256294723': '111'}, {}]}, 'item_1617186994930': {'attribute_name': 'Number of Pages', 'attribute_value_mlt': [{'subitem_1551256248092': '12'}, {}]}, 'item_1617187024783': {'attribute_name': 'Page Start', 'attribute_value_mlt': [{'subitem_1551256198917': '1'}, {}]}, 'item_1617187045071': {'attribute_name': 'Page End', 'attribute_value_mlt': [{'subitem_1551256185532': '3'}, {}]}, 'item_1617187112279': {'attribute_name': 'Degree Name', 'attribute_value_mlt': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}, {}]}, 'item_1617187136212': {'attribute_name': 'Date Granted', 'attribute_value_mlt': [{'subitem_1551256096004': '2021-06-30'}, {}]}, 'item_1617187187528': {'attribute_name': 'Conference', 'attribute_value_mlt': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}, {}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}, {}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}, {}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}, {}], 'subitem_1599711813532': 'JPN'}, {}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, {}]}, 'item_1617265215918': {'attribute_name': 'Version Type', 'attribute_value_mlt': [{'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, {}]}, 'item_1617349709064': {'attribute_name': 'Contributor', 'attribute_value_mlt': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}, {}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}, {}, {}, {}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}]}, {}]}, 'item_1617349808926': {'attribute_name': 'Version', 'attribute_value_mlt': [{'subitem_1523263171732': 'Version'}, {}]}, 'item_1617351524846': {'attribute_name': 'APC', 'attribute_value_mlt': [{'subitem_1523260933860': 'Unknown'}, {}]}, 'item_1617353299429': {'attribute_name': 'Relation', 'attribute_value_mlt': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}, {}]}, {}]}, 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}, {}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}, {}], 'format': 'text/plain', 'mimetype': 'application/pdf', 'url': {'url': 'https://weko3.example.org/record/13/files/1KB.pdf'}, 'version_id': '7cdce099-fe63-445f-b78b-cf2909a8163f'}, {}]}, 'item_1617610673286': {'attribute_name': 'Rights Holder', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}, {}]}, {}]}, 'item_1617620223087': {'attribute_name': 'Heading', 'attribute_value_mlt': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}, {}, {}]}, 'item_1617944105607': {'attribute_name': 'Degree Grantor', 'attribute_value_mlt': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}, {}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}, {}]}, {}]}, 'item_title': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'item_type_id': '15', 'owner': '1', 'path': ['1661517684078', '1661517684078'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2021-08-06'}, 'publish_date': '2021-08-06', 'publish_status': '0', 'relation_version_is_last': True, 'title': ['ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)'], 'weko_shared_id': -1}

                distination = {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [
                    1], 'status': 'draft'}, '_oai': {'sets1': {1, 2, 3}, 'sets2': {1, 2, 3, 4, 5, 6}}, 'test_1': {"dict": {"key1": "value1", "key2": "value2"}, "list": [1, 2, 3, 4], "str": "test_str"}, "test_list": [1]}
                diff_result = [
                    ("add", "_oai.sets1", [("", {3, 4, 5})]),  # dest is set
                    ("change", "test_list.0", ("", 2)),  # dest is list
                    ("remove", "_oai.sets2", [("", {3, 4, 5})]),  # dest is set
                    ("remove", "test_1.list", [(1, "")]),
                    ("remove", "test_1.str", [("key2", "")])
                ]
                ret = dep._patch(diff_result, distination, True)
                assert ret == {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [
                    1], 'status': 'draft'}, '_oai': {'sets1': {1, 2, 3, 4, 5}, 'sets2': {1, 2, 6}}, 'test_1': {"dict": {"key1": "value1", "key2": "value2"}, "list": [1, 3, 4], "str": "test_str"}, "test_list": [2]}

                dep = WekoDeposit.create({})
                distination = {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {
                    'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, 'test_1': {"dict": {"name": "Alice", "age": "30"}}}
                diff_result = [
                    ("remove", "test_1.dict", [
                        ('name', 'Alice'), ('age', 30)]),  # dest is dict
                ]
                ret = dep._patch(diff_result, distination, True)
                assert ret == {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {
                    'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, 'test_1': {"dict": {}}}

                dep = WekoDeposit.create({})
                distination = {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [
                    1], 'status': 'draft'}, '_oai': {'sets1': {1, 2, 3}, 'sets2': {1, 2, 3, 4, 5, 6}}, 'test_1': {"dict": {"key1": "value1", "key2": "value2"}, "list": [1, 2, 3, 4], "str": "test_str"}, "test_list": [1]}
                diff_result = [
                    ("add", "_oai.sets1", [("", {3, 4, 5})]),  # dest is set
                ]
                ret = dep._patch(diff_result, distination, False)
                assert ret == {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [
                    1], 'status': 'draft'}, '_oai': {'sets1': {1, 2, 3, 4, 5}, 'sets2': {1, 2, 3, 4, 5, 6}}, 'test_1': {"dict": {"key1": "value1", "key2": "value2"}, "list": [1, 2, 3, 4], "str": "test_str"}, "test_list": [1]}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

    # def add(node, changes):
    # def change(node, changes):
    # def remove(node, changes):

    # def _publish_new(self, id_=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__publish_new -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__publish_new(self, app, location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                dep = WekoDeposit.create({})
                record = dep._publish_new()
                assert isinstance(record, Record) == True

                mock_logger.assert_any_call(
                    key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

    # def _update_version_id(self, metas, bucket_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__update_version_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__update_version_id(self, app, location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                dep = WekoDeposit.create({})
                bucket = Bucket.create(location)
                ret = dep._update_version_id({}, bucket.id)
                assert ret == False
                i = 1
                meta = {"_oai": {"id": "oai:weko3.example.org:000000{:02d}".format(i), "sets": ["{}".format((i % 2) + 1)]}, "path": ["{}".format((i % 2) + 1)], "owner": "1", "recid": "{}".format(i), "title": ["title"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-08-20"}, "_buckets": {"deposit": "3e99cfca-098b-42ed-b8a0-20ddd09b3e02"}, "_deposit": {"id": "{}".format(i), "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0}, "owner": "1", "owners": [1], "status": "draft", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}}, "item_title": "title", "author_link": [], "item_type_id": "1", "publish_date": "2022-08-20", "publish_status": "0", "weko_shared_id": -1, "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": "title", "subitem_1551255648112": "ja"}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}]}, "relation_version_is_last": True, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [
                        {
                            "accessrole": "open_access",
                            "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                            "displaytype": "simple",
                            "filename": "1KB.pdf",
                            "filesize": [{"value": "1 KB"}],
                            "format": "text/plain",
                            "mimetype": "application/pdf",
                            "url": {
                                "url": "https://localhost:8443/record/{}/files/1KB.pdf".format(
                                    i
                                )
                            },
                            "version_id": "08725856-0ded-4b39-8231-394a80b297df",
                        }
                        ]}}
                ret = dep._update_version_id(meta, bucket.id)
                assert ret == True

                i = 1
                meta = {
                    "_oai": {
                        "id": "oai:weko3.example.org:000000{:02d}".format(i),
                        "sets": ["{}".format((i % 2) + 1)]
                    },
                    "path": ["{}".format((i % 2) + 1)],
                    "owner": "1",
                    "recid": "{}".format(i),
                    "title": ["title"],
                    "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-08-20"},
                    "_buckets": {"deposit": "3e99cfca-098b-42ed-b8a0-20ddd09b3e02"},
                    "_deposit": {
                        "id": "{}".format(i),
                        "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0},
                        "owner": "1",
                        "owners": [1],
                        "status": "draft",
                        "created_by": 1,
                        "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}
                    },
                    "item_title": "title",
                    "author_link": [],
                    "item_type_id": "1",
                    "publish_date": "2022-08-20",
                    "publish_status": "0",
                    "weko_shared_id": -1,
                    "item_1617186331708": {
                        "attribute_name": "Title",
                        "attribute_value_mlt": [{"subitem_1551255647225": "title", "subitem_1551255648112": "ja"}]
                    },
                    "item_1617258105262": {
                        "attribute_name": "Resource Type",
                        "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}]
                    },
                    "relation_version_is_last": True,
                    "item_1617258105262": {
                        "attribute_name": "Resource Type",
                        "attribute_value_mlt": {
                            "accessrole": "open_access",
                            "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                            "displaytype": "simple",
                            "filename": "1KB.pdf",
                            "filesize": [{"value": "1 KB"}],
                            "format": "text/plain",
                            "mimetype": "application/pdf",
                            "url": {
                                "url": "https://localhost:8443/record/{}/files/1KB.pdf".format(i)
                            },
                            "version_id": "08725856-0ded-4b39-8231-394a80b297df",
                        }
                    }
                }
                ret = dep._update_version_id(meta, bucket.id)
                assert ret == True

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def publish(self, pid=None, id_=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_publish(self, app, location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            deposit = WekoDeposit.create({})
            assert deposit['_deposit']['id']
            assert 'draft' == deposit.status
            assert 0 == deposit.revision_id
            deposit.publish()
            assert 'published' == deposit.status
            assert deposit.revision_id == 2

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def publish_without_commit(self, pid=None, id_=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_publish_without_commit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_publish_without_commit(self, app, db, location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():

                # search_hosts = app.config["SEARCH_ELASTIC_HOSTS"]
                # search_client_config = app.config["SEARCH_CLIENT_CONFIG"]
                # es = OpenSearch(
                #     hosts=[{'host': search_hosts, 'port': 9200}],
                #     http_auth=search_client_config['http_auth'],
                #     use_ssl=search_client_config['use_ssl'],
                #     verify_certs=search_client_config['verify_certs'],
                # )

                # self.data is not None, "control_number" not in self,
                # "$schema" in self, "version" in relations
                deposit = WekoDeposit.create({})
                deposit.data = deposit.get('_deposit', {})
                assert deposit['_deposit']['id']
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id

                deposit.publish_without_commit()
                assert deposit['_deposit']['id']
                assert 'published' == deposit.status
                assert deposit.revision_id == 2
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

                # self.data is None, "control_number" in self
                # "$schema" not in self, "version" not in relations
                with patch("weko_deposit.api.serialize_relations", return_value={}):
                    deposit = WekoDeposit.create({})
                    deposit["control_number"] = "2"
                    if '$schema' in deposit:
                        del deposit['$schema']
                    deposit.publish_without_commit()
                    assert deposit['_deposit']['id']
                    assert 'published' == deposit.status
                    assert deposit.revision_id == 2
                    assert deposit.data is not None

                    mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                    mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                    mock_logger.reset_mock()


                # invalid schema
                deposit = WekoDeposit.create({})
                deposit["$schema"] = "http://localhost/schemas/deposits/invalid-v1.0.0.json"
                with pytest.raises(jsonschema.exceptions.RefResolutionError):
                    deposit.publish_without_commit()


    # def create(cls, data, id_=None, recid=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_create(sel, app, client, db, location, users, db_activity):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                deposit = WekoDeposit.create({})
                assert isinstance(deposit, WekoDeposit)
                assert deposit['_deposit']['id'] == "1"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                id = uuid.uuid4()
                deposit = WekoDeposit.create({}, id_=id)
                assert isinstance(deposit, WekoDeposit)
                assert deposit['_deposit']['id'] == "2"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id

                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

            # login(app,client,obj=users[2]["obj"])
            with app.test_request_context():
                login_user(users[2]["obj"])
                session["activity_info"] = {
                    "activity_id": db_activity[0].activity_id}
                data = {
                    "$schema": "https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"}
                id = uuid.uuid4()
                deposit = WekoDeposit.create(data, id_=id)
                assert isinstance(deposit, WekoDeposit)
                assert deposit['_deposit']['id'] == "3"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id

                with patch("weko_deposit.api.PersistentIdentifier.create",side_effect=BaseException("test_error")):
                    session["activity_info"] = {"activity_id":db_activity[1].activity_id}
                    data = {"$schema":"https://127.0.0.1/schema/deposits/deposit-v1.0.0.json","_deposit":{"id":"2","owners":[1],"status":"draft","created_by":1}}
                    id = uuid.uuid4()
                    with pytest.raises(BaseException):
                        deposit = WekoDeposit.create(data, id_=id)

                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

    # def update(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update(sel,app,db,location,db_index,redis_connect,db_itemtype):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                deposit = WekoDeposit.create({})
                assert deposit['_deposit']['id'] == "1"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                deposit.update()
                assert deposit['_deposit']['id'] == "1"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id

                index_obj = {'index': ['1'], 'actions': '1'}
                data = {'pubdate': '2023-12-07', 'item_1617187056579': 'item_1617187056579', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                deposit = WekoDeposit.create(index_obj)
                cache_key = app.config[
                    'WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(
                    pid_value=deposit.pid.pid_value)
                redis_connect.put(cache_key,bytes(json.dumps(data),"utf-8"))
                deposit.update(index_obj)
                # deposit.update({'actions': 'publish', 'index': '0', })
                assert deposit['_deposit']['id'] == "2"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                redis_connect.delete(cache_key)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.reset_mock()

    # def clear(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_clear -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_clear(sel, app, db, location, base_app, es_records_1):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records_1
            record = records[0]
            deposit = record['deposit']
            deposit['_deposit']['status'] = 'draft'

            search_hosts = app.config["SEARCH_ELASTIC_HOSTS"]
            search_client_config = app.config["SEARCH_CLIENT_CONFIG"]
            es = search.client.OpenSearch(
                 hosts=[{'host': search_hosts, 'port': 9200}],
                 http_auth=search_client_config['http_auth'],
                 use_ssl=search_client_config['use_ssl'],
                 verify_certs=search_client_config['verify_certs'],
            )

            ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'],
                                doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'], id=deposit.id)
            deposit.clear()
            ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'],
                                 doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'], id=deposit.id)
            assert ret == ret2

            indexer, records = es_records_1
            record = records[1]
            deposit = record['deposit']

            es = OpenSearch(
                 hosts=[{'host': search_hosts, 'port': 9200}],
                 http_auth=search_client_config['http_auth'],
                 use_ssl=search_client_config['use_ssl'],
                 verify_certs=search_client_config['verify_certs'],
            )

            ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
            deposit.clear()
            ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
            assert ret==ret2
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.reset_mock()

    # def delete(self, force=True, pid=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete(sel, app, base_app, db, location, es_records_1):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records_1
            record = records[0]
            deposit = record['deposit']

            search_hosts = app.config["SEARCH_ELASTIC_HOSTS"]
            search_client_config = app.config["SEARCH_CLIENT_CONFIG"]
            es = search.client.OpenSearch(
                 hosts=[{'host': search_hosts, 'port': 9200}],
                 http_auth=search_client_config['http_auth'],
                 use_ssl=search_client_config['use_ssl'],
                 verify_certs=search_client_config['verify_certs'],
            )

            ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'],
                                doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'], id=deposit.id)
            deposit.delete()
            ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'],
                                 doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'], id=deposit.id, ignore=[404])
            assert ret2 == {'error': {'root_cause': [{'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(
                deposit.id)}], 'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(deposit.id)}, 'status': 404}

            record = records[1]
            deposit = record['deposit']

            es = search.client.OpenSearch(
                 hosts=[{'host': search_hosts, 'port': 9200}],
                 http_auth=search_client_config['http_auth'],
                 use_ssl=search_client_config['use_ssl'],
                 verify_certs=search_client_config['verify_certs'],
            )
            ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'],
                                doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'], id=deposit.id)
            deposit.pid
            deposit.delete()
            ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'],
                                 doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'], id=deposit.id, ignore=[404])
            assert ret2 == {'error': {'root_cause': [{'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(
                deposit.id)}], 'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(deposit.id)}, 'status': 404}

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # recid.status == PIDStatus.RESERVED is false
            record = records[2]
            deposit = record['deposit']

            es = OpenSearch(
                 hosts=[{'host': search_hosts, 'port': 9200}],
                 http_auth=search_client_config['http_auth'],
                 use_ssl=search_client_config['use_ssl'],
                 verify_certs=search_client_config['verify_certs'],
            )

            ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'],
                                doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'], id=deposit.id)
            recid = PersistentIdentifier.get(
                pid_type='recid', pid_value=deposit.pid.pid_value
            )
            recid.status = PIDStatus.REGISTERED
            db.session.commit()

            deposit.delete()

            ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'],
                                    doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'], id=deposit.id, ignore=[404])
            assert ret2 == {'error': {'root_cause': [{'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(
                deposit.id)}], 'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(deposit.id)}, 'status': 404}

    # def commit(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_commit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_commit(self, app, db, location, db_index, db_activity, db_itemtype, bucket):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                deposit = WekoDeposit.create({})
                assert deposit['_deposit']['id'] == "1"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                deposit.commit()
                assert deposit['_deposit']['id'] == "1"
                assert 'draft' == deposit.status
                assert 2 == deposit.revision_id

                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.reset_mock()

                # deposit_bucket and deposit_bucket.location: is false
                deposit = WekoDeposit.create({})
                index_obj = {'index': ['3'], 'actions': 'private', "content": [
                    {"test": "content"}, {"file": "test"}]}
                data = {
                    "content": [{"test": "content"}, {"file": "test"}],
                    'pubdate': '2023-12-07',
                    'item_1617186331708': [{
                        'subitem_1551255647225': 'test',
                        'subitem_1551255648112': 'ja'
                    }],
                    'item_1617258105262': {
                        'resourcetype': 'conference paper',
                        'resourceuri': 'http://purl.org/coar/resource_type/c_5794'
                    },
                    'shared_user_id': -1,
                    'title': 'test',
                    'lang': 'ja',
                    'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011',
                                    'item_1617186609386', 'item_1617186626617', 'item_1617186643794',
                                    'item_1617186660861', 'item_1617186702042', 'item_1617186783814',
                                    'item_1617186859717', 'item_1617186882738', 'item_1617186901218',
                                    'item_1617186920753', 'item_1617186941041', 'item_1617187112279',
                                    'item_1617187187528', 'item_1617349709064', 'item_1617353299429',
                                    'item_1617605131499', 'item_1617610673286', 'item_1617620223087',
                                    'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'],
                    '$schema': '/items/jsonschema/1'
                }
                deposit['_buckets']['deposit'] = "1a23bfcd-456e-78ab-c0d1-23eee45a6b78"
                deposit.update(index_obj, data)
                deposit.commit()

                # self.jrc is false
                deposit = WekoDeposit.create({})
                index_obj = {'index': ['3'], 'actions': 'private', "content": [
                    {"test": "content"}, {"file": "test"}]}
                data = {
                    "content": [{"test": "content"}, {"file": "test"}],
                    'pubdate': '2023-12-07',
                    'item_1617186331708': [{
                        'subitem_1551255647225': 'test',
                        'subitem_1551255648112': 'ja'
                    }],
                    'item_1617258105262': {
                        'resourcetype': 'conference paper',
                        'resourceuri': 'http://purl.org/coar/resource_type/c_5794'
                    },
                    'shared_user_id': -1,
                    'title': 'test',
                    'lang': 'ja',
                    'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011',
                                    'item_1617186609386', 'item_1617186626617', 'item_1617186643794',
                                    'item_1617186660861', 'item_1617186702042', 'item_1617186783814',
                                    'item_1617186859717', 'item_1617186882738', 'item_1617186901218',
                                    'item_1617186920753', 'item_1617186941041', 'item_1617187112279',
                                    'item_1617187187528', 'item_1617349709064', 'item_1617353299429',
                                    'item_1617605131499', 'item_1617610673286', 'item_1617620223087',
                                    'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'],
                    '$schema': '/items/jsonschema/1'
                }
                deposit['_buckets']['deposit'] = "1a23bfcd-456e-78ab-c0d1-23eee45a6b78"
                deposit.update(index_obj, data)
                deposit.jrc = {}
                deposit.commit()

                # record is None, '_oai' is None, '$schema' is None
                deposit = WekoDeposit.create({})
                index_obj = {'index': ['3'], 'actions': 'private', "content": [
                    {"test": "content"}, {"file": "test"}]}
                data = {
                    "content": [{"test": "content"}, {"file": "test"}],
                    'pubdate': '2023-12-07',
                    'item_1617186331708': [{
                        'subitem_1551255647225': 'test',
                        'subitem_1551255648112': 'ja'
                    }],
                    'item_1617258105262': {
                        'resourcetype': 'conference paper',
                        'resourceuri': 'http://purl.org/coar/resource_type/c_5794'
                    },
                    'shared_user_id': -1,
                    'title': 'test',
                    'lang': 'ja',
                    'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011',
                                    'item_1617186609386', 'item_1617186626617', 'item_1617186643794',
                                    'item_1617186660861', 'item_1617186702042', 'item_1617186783814',
                                    'item_1617186859717', 'item_1617186882738', 'item_1617186901218',
                                    'item_1617186920753', 'item_1617186941041', 'item_1617187112279',
                                    'item_1617187187528', 'item_1617349709064', 'item_1617353299429',
                                    'item_1617605131499', 'item_1617610673286', 'item_1617620223087',
                                    'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'],
                    '$schema': '/items/jsonschema/1'
                }
                deposit['_buckets']['deposit'] = "1a23bfcd-456e-78ab-c0d1-23eee45a6b78"
                deposit.update(index_obj, data)
                deposit.jrc = {
                    'type': ['conference paper'],
                    'title': ['test'],
                    'control_number': '2',
                    '_oai': {'id': '2', 'sets': ['1']},
                    '_item_metadata': OrderedDict([
                        ('pubdate', {'attribute_name': 'PubDate',
                         'attribute_value': '2023-12-07'}),
                        ('item_1617186331708', {
                            'attribute_name': 'Title',
                            'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]
                        }),
                        ('item_1617258105262', {
                            'attribute_name': 'Resource Type',
                            'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]
                        }),
                        ('item_title', 'test'),
                        ('item_type_id', '1'),
                        ('control_number', '2'),
                        ('author_link', []),
                        ('_oai', {'id': '2', 'sets': ['1']}),
                        ('publish_date', '2023-12-07'),
                        ('title', ['test']),
                        ('relation_version_is_last', True),
                        ('path', ['1']),
                        ('publish_status', '2')
                    ]),
                    'itemtype': 'テストアイテムタイプ',
                    'publish_date': '2023-12-07',
                    'author_link': [],
                    'path': ['1'],
                    'publish_status': '2',
                    '_created': '2024-09-25T07:58:24.680172+00:00',
                    '_updated': '2024-09-25T07:58:25.436334+00:00',
                    'content': [{"test": "content"}, {"file": "test"}]
                }
                with patch("invenio_records.models.RecordMetadata.query") as mock_json:
                    mock_json.return_value.filter_by.return_value.first.return_value = None
                    deposit.commit()

                # setspec_list is None, record.json.get('_buckets) is None
                deposit = WekoDeposit.create({})
                index_obj = {'index': ['3'], 'actions': 'private', "content": [
                    {"test": "content"}, {"file": "test"}]}
                data = {
                    "content": [{"test": "content"}, {"file": "test"}],
                    'pubdate': '2023-12-07',
                    'item_1617186331708': [{
                        'subitem_1551255647225': 'test',
                        'subitem_1551255648112': 'ja'
                    }],
                    'item_1617258105262': {
                        'resourcetype': 'conference paper',
                        'resourceuri': 'http://purl.org/coar/resource_type/c_5794'
                    },
                    'shared_user_id': -1,
                    'title': 'test',
                    'lang': 'ja',
                    'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011',
                                    'item_1617186609386', 'item_1617186626617', 'item_1617186643794',
                                    'item_1617186660861', 'item_1617186702042', 'item_1617186783814',
                                    'item_1617186859717', 'item_1617186882738', 'item_1617186901218',
                                    'item_1617186920753', 'item_1617186941041', 'item_1617187112279',
                                    'item_1617187187528', 'item_1617349709064', 'item_1617353299429',
                                    'item_1617605131499', 'item_1617610673286', 'item_1617620223087',
                                    'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'],
                    '$schema': '/items/jsonschema/1'
                }

                deposit.update(index_obj, data)
                deposit.jrc = {
                    'type': ['conference paper'],
                    'title': ['test'],
                    'control_number': '2',
                    '_oai': {'id': '2', 'sets': ['1']},
                    '_item_metadata': OrderedDict([
                        ('pubdate', {'attribute_name': 'PubDate',
                         'attribute_value': '2023-12-07'}),
                        ('item_1617186331708', {
                            'attribute_name': 'Title',
                            'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]
                        }),
                        ('item_1617258105262', {
                            'attribute_name': 'Resource Type',
                            'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]
                        }),
                        ('item_title', 'test'),
                        ('item_type_id', '1'),
                        ('control_number', '2'),
                        ('author_link', []),
                        ('_oai', {'id': '2', 'sets': ['1']}),
                        ('publish_date', '2023-12-07'),
                        ('title', ['test']),
                        ('relation_version_is_last', True),
                        ('path', []),
                        ('publish_status', '2')
                    ]),
                    'itemtype': 'テストアイテムタイプ',
                    'publish_date': '2023-12-07',
                    'author_link': [],
                    'path': [],
                    'publish_status': '2',
                    '_created': '2024-09-25T07:58:24.680172+00:00',
                    '_updated': '2024-09-25T07:58:25.436334+00:00',
                    'content': [{"test": "content"}, {"file": "test"}],
                    '$schema': '/items/jsonschema/1',
                }
                deposit.commit()

                # record.json.get('_buckets'): is None
                deposit = WekoDeposit.create({})
                record = RecordMetadata.query.get(deposit.pid.object_uuid)
                del deposit["_buckets"]
                db.session.merge(record)
                db.session.commit()
                deposit.commit()

                # exist feedback_mail_list
                deposit = WekoDeposit.create({})
                item_id = deposit.pid.object_uuid
                index_obj = {'index': ['1'], 'actions': 'private'}
                data = {'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794',
                                                                                                                                                                                                                                                                                                                                          'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                deposit.update(index_obj, data)
                FeedbackMailList.update(
                    item_id, [{"email": "test.taro@test.org", "author_id": "1"}])
                db.session.commit()
                deposit.commit()
                es_data = deposit.indexer.get_metadata_by_item_id(item_id)
                assert es_data["_source"]["feedback_mail_list"] == [
                    {"email": "test.taro@test.org", "author_id": "1"}]

                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.reset_mock()

                # not exist feedback_mail_list
                FeedbackMailList.delete(item_id)
                deposit.commit()
                es_data = deposit.indexer.get_metadata_by_item_id(item_id)
                assert es_data["_source"]["feedback_mail_list"] == []
                mockjrc = {'title': ['test'], 'type': ['conference paper'], 'control_number': '2', '_oai': {'id': '2'}, '_item_metadata': OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2023-12-07'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [
                                                                                                                                                      {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]}), ('item_title', 'test'), ('item_type_id', '1'), ('control_number', '2'), ('author_link', []), ('_oai', {'id': '2'}), ('publish_date', '2023-12-07'), ('title', ['test']), ('relation_version_is_last', True), ('path', ['1']), ('publish_status', '2')]), 'itemtype': 'テストアイテムタイプ', 'publish_date': '2023-12-07', 'author_link': [], 'path': ['1'], 'publish_status': '2', 'content': '123123123'}
                # activity_info
                deposit = WekoDeposit.create({})
                item_id = deposit.pid.object_uuid
                index_obj = {'content': {'content': 'content'},
                             'index': ['2'], 'actions': 'private'}
                data = {'content': {'content': 'content'}, 'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617',
                                                                                                                                                                                                                                                                                                                                                                             'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                deposit.update(index_obj, data)
                FeedbackMailList.update(
                    item_id, [{"email": "test.taro@test.org", "author_id": "1"}])
                session["activity_info"] = {
                    "activity_id": "1",
                    "action_id": 1,
                    "action_version": "1.0.1",
                    "action_status": "M",
                    "commond": "",
                }
                # db.session.merge(bucket)
                deposit['content'] = {'content': 'content'}
                db.session.commit()
                deposit.commit()
                es_data = deposit.indexer.get_metadata_by_item_id(item_id)
                assert es_data["_source"]["feedback_mail_list"] == [
                    {"email": "test.taro@test.org", "author_id": "1"}]

                # workflow_storage_location != None
                deposit = WekoDeposit.create({})
                item_id = deposit.pid.object_uuid
                index_obj = {'index': ['3'], 'actions': 'private', "content": [
                    {"test": "content"}, {"file": "test"}]}
                # data = {'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                data = {"content": [{"test": "content"}, {"file": "test"}], 'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617',
                                                                                                                                                                                                                                                                                                                                                                                              'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                # deposit['_buckets']['deposit'] = "3e99cfca-098b-42ed-b8a0-20ddd09b3e01"
                deposit.update(index_obj, data)
                FeedbackMailList.update(
                    item_id, [{"email": "test.taro@test.org", "author_id": "1"}])
                session["activity_info"] = {
                    "activity_id": "2",
                    "action_id": 1,
                    "action_version": "1.0.1",
                    "action_status": "M",
                    "commond": "",
                }

                tmppath1 = tempfile.mkdtemp()
                # loc = Location(id="2",name="testloc1", uri=tmppath1, default=True)
                loc1 = Location(name="testloc1", uri=tmppath1, default=True)
                db.session.add(loc1)

                db.session.commit()
                bucket2 = Bucket.create(loc1)
                db.session.merge(bucket2)
                db.session.commit()
                deposit['_buckets']['deposit']=str(bucket2.id)
                deposit.commit()
                es_data = deposit.indexer.get_metadata_by_item_id(item_id)
                assert es_data["_source"]["feedback_mail_list"] == [
                    {"email": "test.taro@test.org", "author_id": "1"}]
                shutil.rmtree(tmppath1)

                deposit.jrc = {
                    'type': ['conference paper'],
                    'title': ['test'],
                    'control_number': '2',
                    '_oai': {'id': '2', 'sets': ['1']},
                    '_item_metadata': OrderedDict([
                        ('pubdate', {'attribute_name': 'PubDate',
                         'attribute_value': '2023-12-07'}),
                        ('item_1617186331708', {
                            'attribute_name': 'Title',
                            'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]
                        }),
                        ('item_1617258105262', {
                            'attribute_name': 'Resource Type',
                            'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]
                        }),
                        ('item_title', 'test'),
                        ('item_type_id', '1'),
                        ('control_number', '2'),
                        ('author_link', []),
                        ('_oai', {'id': '2', 'sets': ['1']}),
                        ('publish_date', '2023-12-07'),
                        ('title', ['test']),
                        ('relation_version_is_last', True),
                        ('path', ['1']),
                        ('publish_status', '2')
                    ]),
                    'itemtype': 'テストアイテムタイプ',
                    'publish_date': '2023-12-07',
                    'author_link': [],
                    'path': ['1'],
                    'publish_status': '2',
                    '_created': '2024-09-25T07:58:24.680172+00:00',
                    '_updated': '2024-09-25T07:58:25.436334+00:00',
                    'content': [{"test": "content"}, {"file": "test"}]
                }

                deposit.commit()

                assert not any(("file" in e.keys()) for e in deposit.jrc.get('content'))
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch='content is in jrc')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch='file is in content')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

                with patch("weko_deposit.api.WekoIndexer.upload_metadata") as mock_upload:
                    mock_upload.side_effect = [seacrh.exceptions.TransportError(500,"test_error",{"error":{"reason": WEKO_DEPOSIT_ES_PARSING_ERROR_KEYWORD}}), "Mocked Data"]
                    deposit.commit()

                    with pytest.raises(WekoDepositError):
                        result = deposit.commit()

                with patch("weko_deposit.api.WekoIndexer.upload_metadata") as mock_upload:
                    mock_upload.side_effect = [seacrh.exceptions.TransportError(500,"test_error",{"error":{"reason":""}}), "test error"]
                    with pytest.raises(WekoDepositError) as ex:
                        deposit.commit()

                # Exception to occur
                with patch("weko_deposit.api.WekoIndexer.upload_metadata", side_effect=Exception("test_error")):
                    with pytest.raises(WekoDepositError):
                        deposit.commit()

    # def newversion(self, pid=None, is_draft=False):
    #             # NOTE: We call the superclass `create()` method, because
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_newversion -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_newversion(sel, app, db, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            with patch("weko_deposit.api.WekoDeposit.is_published", return_value=None):
                with pytest.raises(PIDInvalidAction):
                    ret = deposit.newversion()

            with pytest.raises(AttributeError):
                ret = deposit.newversion()

            ret = deposit.newversion(deposit.pid, True)
            assert ret == None

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            ret = deposit.newversion(deposit.pid)
            assert ret == None

            record2 = records[1]
            pid2 = record2["recid"]
            pid2.status = "K"
            db.session.merge(pid2)
            db.session.commit()
            with pytest.raises(WekoDepositError):
                ret = deposit.newversion(pid2)

            record = records[2]
            deposit = record['deposit']
            pid = record["recid"]
            ret = deposit.newversion(pid, True)
            assert ret is not None

            record = records[3]
            deposit = record['deposit']
            pid = record["recid"]
            ret = deposit.newversion(pid, False)
            assert ret is not None

            record = records[4]
            deposit = record['deposit']
            session["activity_info"] = {
                "activity_id": "A-20220818-00001",
                "action_id": 4,
                "action_version": "1.0.1",
                "action_status": "M",
                "commond": "",
            }
            db.session.commit()
            ret = deposit.newversion(pid, False)
            assert ret is not None

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def get_content_files(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_get_content_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_content_files(self, app, db, location, es_records_1):
        # fmd is empty list
        with app.app_context():
            with patch('weko_deposit.api.weko_logger') as mock_logger:
                with patch('weko_deposit.api.WekoDeposit.get_file_data', return_value=[]):
                    deposit = WekoDeposit(data={})
                    deposit.get_content_files()
                    assert mock_logger.call_count == 0

        # fmd has file_data
        with app.app_context():
            with patch('weko_deposit.api.weko_logger') as mock_logger:
                # mock self.files
                with patch.object(WekoDeposit, 'files', new_callable=PropertyMock) as mock_files:

                    # fmd is not List
                    with patch('weko_deposit.api.WekoDeposit.get_file_data') as mock_get_file_data:
                        fmd_dict = {'file': 'data'}
                        mock_get_file_data.return_value = fmd_dict

                        def init(self, key, mimetype,version_id):
                            self.key = key
                            self.mimetype = mimetype
                            self.version_id = version_id
                            self.file = FileInstance.create()

                        filename = "filename"
                        mimetype_correct = "application/pdf"
                        version_id = "1"
                        # return value of mock self.files = [file]
                        mock_files.return_value = [
                            # file with correct mimetype
                            FileObject(
                                type("test_obj",(),
                                    {"__init__": init})(filename, mimetype_correct, version_id),
                                {"title": [{"title": "item", "filename": "filename"}]}
                            )
                        ]
                        deposit = copy.deepcopy(es_records_1[1][0]['deposit'])
                        jrc = {
                            'type': ['conference paper'],
                            'title': ['test'],
                            'control_number': '2',
                            '_oai': {'id': '2', 'sets': ['1']},
                            '_item_metadata': OrderedDict([
                                ('pubdate', {'attribute_name': 'PubDate',
                                'attribute_value': '2023-12-07'}),
                                ('item_1617186331708', {
                                    'attribute_name': 'Title',
                                    'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]
                                }),
                                ('item_1617258105262', {
                                    'attribute_name': 'Resource Type',
                                    'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]
                                }),
                                ('item_title', 'test'),
                                ('item_type_id', '1'),
                                ('control_number', '2'),
                                ('author_link', []),
                                ('_oai', {'id': '2', 'sets': ['1']}),
                                ('publish_date', '2023-12-07'),
                                ('title', ['test']),
                                ('relation_version_is_last', True),
                                ('path', ['1']),
                                ('publish_status', '2')
                            ]),
                            'itemtype': 'テストアイテムタイプ',
                            'publish_date': '2023-12-07',
                            'author_link': [],
                            'path': ['1'],
                            'publish_status': '2',
                            '_created': '2024-09-25T07:58:24.680172+00:00',
                            '_updated': '2024-09-25T07:58:25.436334+00:00',
                            'content': [{"test": "content"}, {"file": "test"}]
                        }
                        deposit.jrc = jrc

                        deposit.get_content_files()

                        mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='fmd is not empty')
                        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                        mock_get_file_data.reset_mock()
                        mock_logger.reset_mock()

                    # file.obj.mimetype not in mimetypes
                    with patch('weko_deposit.api.WekoDeposit.get_file_data') as mock_get_file_data:
                        fmd = [{'file': 'data'}, {"filename": "filename"}]
                        mock_get_file_data.return_value = fmd
                        # splited_content = "content1\ncontent2\ncontent3"
                        # with patch('weko_deposit.api.parser.from_file') as mock_parser:
                        #     mock_parser.return_value = {"content": splited_content}
                        def init(self, key, mimetype, version_id):
                            self.key = key
                            self.mimetype = mimetype
                            self.version_id = version_id
                            self.file = FileInstance.create()

                        filename = "filename"
                        mimetype_correct = "application/csv"
                        version_id = "1"
                        # return value of mock self.files = [file]
                        mock_files.return_value = [
                            # file
                            FileObject(
                                # file with incorrect mimetype
                                type("test_obj",(),
                                    {"__init__": init})(filename, mimetype_correct, version_id),
                                {"title": [{"title": "item", "filename": "filename"}]}
                            )
                        ]
                        deposit = copy.deepcopy(es_records_1[1][0]['deposit'])
                        jrc = {
                            'type': ['conference paper'],
                            'title': ['test'],
                            'control_number': '2',
                            '_oai': {'id': '2', 'sets': ['1']},
                            '_item_metadata': OrderedDict([
                                ('pubdate', {'attribute_name': 'PubDate',
                                'attribute_value': '2023-12-07'}),
                                ('item_1617186331708', {
                                    'attribute_name': 'Title',
                                    'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]
                                }),
                                ('item_1617258105262', {
                                    'attribute_name': 'Resource Type',
                                    'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]
                                }),
                                ('item_title', 'test'),
                                ('item_type_id', '1'),
                                ('control_number', '2'),
                                ('author_link', []),
                                ('_oai', {'id': '2', 'sets': ['1']}),
                                ('publish_date', '2023-12-07'),
                                ('title', ['test']),
                                ('relation_version_is_last', True),
                                ('path', ['1']),
                                ('publish_status', '2')
                            ]),
                            'itemtype': 'テストアイテムタイプ',
                            'publish_date': '2023-12-07',
                            'author_link': [],
                            'path': ['1'],
                            'publish_status': '2',
                            '_created': '2024-09-25T07:58:24.680172+00:00',
                            '_updated': '2024-09-25T07:58:25.436334+00:00',
                            'content': [{"test": "content"}, {"file": "test"}]
                        }
                        deposit.jrc = jrc

                        deposit.get_content_files()

                        result = deposit.jrc.get('content')
                        assert 'filename' in result[0]
                        assert result[0]['filename'] == filename
                        assert 'version_id' in result[0]
                        assert result[0]['version_id'] == version_id
                        assert 'url' in result[0]
                        assert result[0]['url']['url'] == '{}record/{}/files/{}'.format(get_url_root(), deposit['recid'], filename)
                        assert 'attachment' in result[0]
                        # assert "".join(splited_content.splitlines()) in result[0]['attachment']['content']

                        # assert 'content' in deposit.jrc
                        # assert any(("file" in e.keys()) for e in deposit.jrc.get('content'))
                        mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='fmd is not empty')
                        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                        mock_logger.reset_mock()
                        mock_get_file_data.reset_mock()

                    # fmd is list
                    with patch('weko_deposit.api.WekoDeposit.get_file_data') as mock_get_file_data:
                        # fmd   [lst0, lst1]
                        fmd = [{'file': 'data'}, {"filename": "filename"}]
                        mock_get_file_data.return_value = fmd
                        splited_content = "content1\ncontent2\ncontent3"
                        with patch('weko_deposit.api.parser.from_file') as mock_parser:
                            mock_parser.return_value = {"content": splited_content}
                            def init(self, key, mimetype, version_id):
                                self.key = key
                                self.mimetype = mimetype
                                self.version_id = version_id
                                self.file = FileInstance.create()

                            filename = "filename"
                            mimetype_correct = "application/pdf"
                            mimetype_incorrect = "application/csv"

                            version_id = "1"
                            # return value of mock self.files = [file]
                            mock_files.return_value = [
                                # file with correct mimetype
                                FileObject(
                                    type("test_obj",(),
                                        {"__init__": init})(filename, mimetype_correct, version_id),
                                    {"title": [{"title": "item", "filename": "filename"}]}
                                ),
                                # file with incorrect mimetype
                                FileObject(
                                    type("test_obj",(),
                                        {"__init__": init})(filename, mimetype_incorrect, version_id),
                                    {"title": [{"title": "item", "filename": "filename"}]}
                            )
                            ]
                            deposit = copy.deepcopy(es_records_1[1][0]['deposit'])
                            jrc = {
                                'type': ['conference paper'],
                                'title': ['test'],
                                'control_number': '2',
                                '_oai': {'id': '2', 'sets': ['1']},
                                '_item_metadata': OrderedDict([
                                    ('pubdate', {'attribute_name': 'PubDate',
                                    'attribute_value': '2023-12-07'}),
                                    ('item_1617186331708', {
                                        'attribute_name': 'Title',
                                        'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]
                                    }),
                                    ('item_1617258105262', {
                                        'attribute_name': 'Resource Type',
                                        'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]
                                    }),
                                    ('item_title', 'test'),
                                    ('item_type_id', '1'),
                                    ('control_number', '2'),
                                    ('author_link', []),
                                    ('_oai', {'id': '2', 'sets': ['1']}),
                                    ('publish_date', '2023-12-07'),
                                    ('title', ['test']),
                                    ('relation_version_is_last', True),
                                    ('path', ['1']),
                                    ('publish_status', '2')
                                ]),
                                'itemtype': 'テストアイテムタイプ',
                                'publish_date': '2023-12-07',
                                'author_link': [],
                                'path': ['1'],
                                'publish_status': '2',
                                '_created': '2024-09-25T07:58:24.680172+00:00',
                                '_updated': '2024-09-25T07:58:25.436334+00:00',
                                'content': [{"test": "content"}, {"file": "test"}]
                            }
                            deposit.jrc = jrc

                            deposit.get_content_files()

                            result = deposit.jrc.get('content')
                            assert 'filename' in result[0]
                            assert result[0]['filename'] == filename
                            assert 'mimetype' in result[0]
                            assert result[0]['mimetype'] == mimetype_correct
                            assert 'version_id' in result[0]
                            assert result[0]['version_id'] == version_id
                            assert 'url' in result[0]
                            assert result[0]['url']['url'] == '{}record/{}/files/{}'.format(get_url_root(), deposit['recid'], filename)
                            assert 'attachment' in result[0]
                            assert "".join(splited_content.splitlines()) in result[0]['attachment']['content']

                            # assert 'content' in deposit.jrc
                            # assert any(("file" in e.keys()) for e in deposit.jrc.get('content'))
                            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='fmd is not empty')
                            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                            mock_logger.reset_mock()

                        # FileNotFoundError
                        with patch('weko_deposit.api.parser.from_file') as mock_parser:
                            mock_parser.side_effect=FileNotFoundError("File not found")
                            # It should be raised
                            # with pytest.raises(WekoDepositError):
                            deposit = copy.deepcopy(es_records_1[1][0]['deposit'])
                            deposit.jrc = jrc
                            deposit.get_content_files()
                            mock_logger.assert_any_call(key='WEKO_DEPOSIT_FAILED_FIND_FILE', ex=mock.ANY)
                            mock_logger.reset_mock()
                            mock_parser.rest_mock()

                        # inner Exception
                            mock_parser.side_effect=Exception("test_error")
                            # It should be raised
                            # with pytest.raises(WekoDepositError):
                            deposit = copy.deepcopy(es_records_1[1][0]['deposit'])
                            deposit.jrc = jrc
                            deposit.get_content_files()
                            mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
                            mock_logger.reset_mock()
                            mock_parser.rest_mock()

                        # outer Exception
                        # with patch("weko_deposit.api.copy") as mock_lst_copy:
                        del app.config['WEKO_MIMETYPE_WHITELIST_FOR_ES']
                        deposit = copy.deepcopy(es_records_1[1][0]['deposit'])
                        deposit.jrc = jrc
                        deposit.get_content_files()
                        mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)

    # def get_file_data(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_get_file_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_file_data(sel, app, db, location, es_records_1):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records_1
            record = records[0]
            deposit = record['deposit']
            ret = deposit.get_file_data()
            assert ret == [{'filename': 'hello.txt', 'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {
                'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def save_or_update_item_metadata(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_save_or_update_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_save_or_update_item_metadata(sel, app, db, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with patch("weko_deposit.api.ItemsMetadata.get_record", side_effect=ItemsMetadata.get_record) as mock_metaRecord:
                # if owner: is true
                indexer, records = es_records
                record = records[0]
                deposit = record['deposit']
                index_obj = {'index': ['1'], 'actions': 'private'}
                data = {'pubdate': '2023-12-07', 'item_1617187056579':'item_1617187056579', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                deposit.update(index_obj,data)
                deposit.save_or_update_item_metadata()
                mock_metaRecord.assert_called_once()

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()
                mock_metaRecord.reset_mock()

                # if not dc_owner: is false
                indexer, records = es_records
                record = records[1]
                deposit = record['deposit']

                index_obj = {'index': ['1'], 'actions': 'private'}
                data = {'pubdate': '2023-12-07', 'item_1617187056579':'item_1617187056579', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1', 'owner': '1'}
                deposit.update(index_obj,data)
                deposit.save_or_update_item_metadata()
                mock_metaRecord.assert_called_once()
                mock_metaRecord.reset_mock()

                # if owner: is false
                record = records[2]
                deposit = record['deposit']
                deposit['_deposit']['owners'] = [""]
                index_obj = {'index': ['1'], 'actions': 'private'}
                data = {'pubdate': '2023-12-07', 'item_1617187056579':'item_1617187056579', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                deposit.update(index_obj,data)
                deposit.save_or_update_item_metadata()
                mock_metaRecord.assert_called_once()
                mock_metaRecord.reset_mock()

                # exists ItemMetadata and has not 'deleted_items'
                record = records[3]
                deposit = record['deposit']
                deposit['_deposit']['owners'] = [""]
                index_obj = {'index': ['1'], 'actions': 'private'}
                data = {'pubdate': '2023-12-07', 'item_1617187056579':'item_1617187056579', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja',
                        'deleted_items': [], '$schema': '/items/jsonschema/1'}
                deposit.update(index_obj,data)
                deposit.save_or_update_item_metadata()
                mock_metaRecord.reset_mock()

            # ItemMetadata not exists
            with patch("weko_deposit.api.ItemsMetadata.create", side_effect=ItemsMetadata.create) as mock_metaCreate:
                record = records[4]
                deposit = record['deposit']
                deposit['_deposit']['owners'] = [""]
                rec_uuid = record['rec_uuid']
                metadata = ItemMetadata.query.filter_by(id=rec_uuid).first()
                db.session.delete(metadata)
                index_obj = {'index': ['1'], 'actions': 'private'}
                data = {'pubdate': '2023-12-07', 'item_1617187056579':'item_1617187056579', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                deposit.update(index_obj,data)
                deposit.save_or_update_item_metadata()
                mock_metaCreate.assert_called_once()
                mock_metaCreate.reset_mock()

                # ItemMetadata not exists and has not 'deleted_items'
                record = records[5]
                deposit = record['deposit']
                deposit['_deposit']['owners'] = [""]
                rec_uuid = record['rec_uuid']
                metadata = ItemMetadata.query.filter_by(id=rec_uuid).first()
                db.session.delete(metadata)
                index_obj = {'index': ['1'], 'actions': 'private'}
                data = {'pubdate': '2023-12-07', 'item_1617187056579':'item_1617187056579', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja',
                        'deleted_items': [], '$schema': '/items/jsonschema/1'}
                deposit.update(index_obj,data)
                deposit.save_or_update_item_metadata()
                mock_metaCreate.assert_called_once()

    # def delete_old_file_index(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_old_file_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_old_file_index(sel, app, db, location,es_records, es_records_8):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            # not is_edit
            deposit.delete_old_file_index()
            # is_edit
            deposit.is_edit = True
            deposit.delete_old_file_index()

            # klst is none
            indexer, records = es_records_8
            record = records[1]
            deposit = record['deposit']
            deposit.is_edit = True
            deposit.delete_old_file_index()

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def delete_item_metadata(self, data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_item_metadata(sel, app, db, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            item_data = record['item_data']

            deposit.delete_item_metadata(item_data)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_record_data_from_act_temp -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_record_data_from_act_temp(sel, app, db, db_activity, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            _, records = es_records

            # not exist pid
            record = records[8]
            pid = record["recid"]
            pid.delete()
            db.session.commit()
            deposit = record["deposit"]
            deposit["recid"] = "xxx"
            result = deposit.record_data_from_act_temp()
            assert result == None

            # not exist activity
            record = records[0]
            rec_uuid = record["recid"].object_uuid
            deposit = record["deposit"]
            result = deposit.record_data_from_act_temp()
            assert result == None

            # not exist activity.temp_data
            activity = Activity(activity_id='3', workflow_id=1, flow_id=1,
                                item_id=rec_uuid,
                                action_id=1, activity_login_user=1,
                                activity_update_user=1,
                                activity_start=datetime.strptime(
                                    '2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                                activity_community_id=3,
                                activity_confirm_term_of_use=True,
                                title='test_title', shared_user_id=-1, extra_info={},
                                action_order=1,
                                )
            db.session.add(activity)
            db.session.commit()
            result = deposit.record_data_from_act_temp()
            assert result == None

            # exist activity.temp_data
            temp_data = {"metainfo": {"pubdate": "2023-10-10", "none_str": "", "empty_list": [], "item_1617186331708": [{"subitem_1551255647225": "test_title", "subitem_1551255648112": "ja"}], "item_1617186385884": [{"subitem_1551255720400": "alter title"}], "item_1617186419668": [{"creatorAffiliations": [{"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}], "creatorAlternatives": [{}], "creatorMails": [{}], "creatorNames": [{}], "familyNames": [{"familyName": "test_family_name"}], "givenNames": [{}], "nameIdentifiers": [{}]}], "item_1617186499011": [{}], "item_1617186609386": [{}], "item_1617186626617": [{}], "item_1617186643794": [{}], "item_1617186660861": [{}], "item_1617186702042": [{}], "item_1617186783814": [{}], "item_1617186859717": [{}], "item_1617186882738": [{"subitem_geolocation_place": [{}]}], "item_1617186901218": [{"subitem_1522399412622": [{}], "subitem_1522399651758": [{}]}], "item_1617186920753": [{}], "item_1617186941041": [{}], "item_1617187112279": [{}], "item_1617187187528": [
                {"subitem_1599711633003": [{}], "subitem_1599711660052": [{}], "subitem_1599711758470": [{}], "subitem_1599711788485": [{}]}], "item_1617349709064": [{"contributorAffiliations": [{"contributorAffiliationNameIdentifiers": [{}], "contributorAffiliationNames": [{}]}], "contributorAlternatives": [{}], "contributorMails": [{}], "contributorNames": [{}], "familyNames": [{}], "givenNames": [{}], "nameIdentifiers": [{}]}], "item_1617353299429": [{"subitem_1523320863692": [{}]}], "item_1617605131499": [{"date": [{}], "fileDate": [{}], "filesize": [{}]}], "item_1617610673286": [{"nameIdentifiers": [{}], "rightHolderNames": [{}]}], "item_1617620223087": [{}], "item_1617944105607": [{"subitem_1551256015892": [{}], "subitem_1551256037922": [{}]}], "item_1617187056579": {"bibliographic_titles": [{}]}, "shared_user_id": -1, "item_1617258105262": {"resourcetype": "conference paper", "resourceuri": "http://purl.org/coar/resource_type/c_5794"}}, "files": [], "endpoints": {"initialization": "/api/deposits/items"}}
            activity.temp_data = json.dumps(temp_data)
            db.session.merge(activity)
            db.session.commit()
            result = deposit.record_data_from_act_temp()
            test = {"pubdate": "2023-10-10", "item_1617186331708": [{"subitem_1551255647225": "test_title", "subitem_1551255648112": "ja"}], "item_1617186385884": [{"subitem_1551255720400": "alter title"}], "item_1617186419668": [{"familyNames": [{"familyName": "test_family_name"}]}], "shared_user_id": -1, "item_1617258105262": {"resourcetype": "conference paper", "resourceuri": "http://purl.org/coar/resource_type/c_5794"}, "deleted_items": ["none_str", "empty_list", "item_1617186499011", "item_1617186609386","item_1617186626617", "item_1617186643794", "item_1617186660861", "item_1617186702042", "item_1617186783814", "item_1617186859717", "item_1617186882738", "item_1617186901218", "item_1617186920753", "item_1617186941041", "item_1617187112279", "item_1617187187528", "item_1617349709064", "item_1617353299429", "item_1617605131499", "item_1617610673286", "item_1617620223087", "item_1617944105607", "item_1617187056579"], "$schema": "/items/jsonschema/1", "title": "test_title", "lang": "ja"}
            assert result == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # title is dict
            temp_data = {"metainfo": {"pubdate": "2023-10-10", "none_str": "", "empty_list": [], "item_1617186331708": {"subitem_1551255647225": "test_title", "subitem_1551255648112": "ja"}, "item_1617186385884": [{"subitem_1551255720400": "alter title"}], "item_1617186419668": [{"creatorAffiliations": [{"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}], "creatorAlternatives": [{}], "creatorMails": [{}], "creatorNames": [{}], "familyNames": [{"familyName": "test_family_name"}], "givenNames": [{}], "nameIdentifiers": [{}]}], "item_1617186499011": [{}], "item_1617186609386": [{}], "item_1617186626617": [{}], "item_1617186643794": [{}], "item_1617186660861": [{}], "item_1617186702042": [{}], "item_1617186783814": [{}], "item_1617186859717": [{}], "item_1617186882738": [{"subitem_geolocation_place": [{}]}], "item_1617186901218": [{"subitem_1522399412622": [{}], "subitem_1522399651758": [{}]}], "item_1617186920753": [{}], "item_1617186941041": [{}], "item_1617187112279": [{}], "item_1617187187528": [
                {"subitem_1599711633003": [{}], "subitem_1599711660052": [{}], "subitem_1599711758470": [{}], "subitem_1599711788485": [{}]}], "item_1617349709064": [{"contributorAffiliations": [{"contributorAffiliationNameIdentifiers": [{}], "contributorAffiliationNames": [{}]}], "contributorAlternatives": [{}], "contributorMails": [{}], "contributorNames": [{}], "familyNames": [{}], "givenNames": [{}], "nameIdentifiers": [{}]}], "item_1617353299429": [{"subitem_1523320863692": [{}]}], "item_1617605131499": [{"date": [{}], "fileDate": [{}], "filesize": [{}]}], "item_1617610673286": [{"nameIdentifiers": [{}], "rightHolderNames": [{}]}], "item_1617620223087": [{}], "item_1617944105607": [{"subitem_1551256015892": [{}], "subitem_1551256037922": [{}]}], "item_1617187056579": {"bibliographic_titles": [{}]}, "shared_user_id": -1, "item_1617258105262": {"resourcetype": "conference paper", "resourceuri": "http://purl.org/coar/resource_type/c_5794"}}, "files": [], "endpoints": {"initialization": "/api/deposits/items"}}
            activity.temp_data = json.dumps(temp_data)
            db.session.merge(activity)
            db.session.commit()
            result = deposit.record_data_from_act_temp()
            test = {"pubdate": "2023-10-10", "item_1617186331708": {"subitem_1551255647225": "test_title", "subitem_1551255648112": "ja"}, "item_1617186385884": [{"subitem_1551255720400": "alter title"}], "item_1617186419668": [{"familyNames": [{"familyName": "test_family_name"}]}], "shared_user_id": -1, "item_1617258105262": {"resourcetype": "conference paper", "resourceuri": "http://purl.org/coar/resource_type/c_5794"}, "deleted_items": [
                "none_str", "empty_list", "item_1617186499011", "item_1617186609386", "item_1617186626617", "item_1617186643794", "item_1617186660861", "item_1617186702042", "item_1617186783814", "item_1617186859717", "item_1617186882738", "item_1617186901218", "item_1617186920753", "item_1617186941041", "item_1617187112279", "item_1617187187528", "item_1617349709064", "item_1617353299429", "item_1617605131499", "item_1617610673286", "item_1617620223087", "item_1617944105607", "item_1617187056579"], "$schema": "/items/jsonschema/1", "title": "test_title", "lang": "ja"}
            assert result == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # title data is not exist
            temp_data = {"metainfo": {"pubdate": "2023-10-10","none_str": "","empty_list": [],"item_1617186331708": [],"item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"creatorAffiliations": [{"affiliationNameIdentifiers": [{}],"affiliationNames": [{}]}],"creatorAlternatives": [{}],"creatorMails": [{}],"creatorNames": [{}],"familyNames": [{"familyName": "test_family_name"}],"givenNames": [{}],"nameIdentifiers": [{}]}],"item_1617186499011": [{}],"item_1617186609386": [{}],"item_1617186626617": [{}],"item_1617186643794": [{}],"item_1617186660861": [{}],"item_1617186702042": [{}],"item_1617186783814": [{}],"item_1617186859717": [{}],"item_1617186882738": [{"subitem_geolocation_place": [{}]}],"item_1617186901218": [{"subitem_1522399412622": [{}],"subitem_1522399651758": [{}]}],"item_1617186920753": [{}],"item_1617186941041": [{}],"item_1617187112279": [{}],"item_1617187187528": [{"subitem_1599711633003": [{}],"subitem_1599711660052": [{}],"subitem_1599711758470": [{}],"subitem_1599711788485": [{}]}],"item_1617349709064": [{"contributorAffiliations": [{"contributorAffiliationNameIdentifiers": [{}],"contributorAffiliationNames": [{}]}],"contributorAlternatives": [{}],"contributorMails": [{}],"contributorNames": [{}],"familyNames": [{}],"givenNames": [{}],"nameIdentifiers": [{}]}],"item_1617353299429": [{"subitem_1523320863692": [{}]}],"item_1617605131499": [{"date": [{}],"fileDate": [{}],"filesize": [{}]}],"item_1617610673286": [{"nameIdentifiers": [{}],"rightHolderNames": [{}]}],"item_1617620223087": [{}],"item_1617944105607": [{"subitem_1551256015892": [{}],"subitem_1551256037922": [{}]}],"item_1617187056579": {"bibliographic_titles": [{}]},"shared_user_id": -1,"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"}},"files": [],"endpoints": {"initialization": "/api/deposits/items"}}
            activity.temp_data=json.dumps(temp_data)
            db.session.merge(activity)
            db.session.commit()
            result = deposit.record_data_from_act_temp()
            test = {"pubdate": "2023-10-10", "item_1617186385884": [{"subitem_1551255720400": "alter title"}], "item_1617186419668": [{"familyNames": [{"familyName": "test_family_name"}]}], "shared_user_id": -1, "item_1617258105262": {"resourcetype": "conference paper", "resourceuri": "http://purl.org/coar/resource_type/c_5794"}, "deleted_items": ["none_str", "empty_list", "item_1617186331708", "item_1617186499011", "item_1617186609386", "item_1617186626617",
                                                                                                                                                                                                                                                                                                                                                              "item_1617186643794", "item_1617186660861", "item_1617186702042", "item_1617186783814", "item_1617186859717", "item_1617186882738", "item_1617186901218", "item_1617186920753", "item_1617186941041", "item_1617187112279", "item_1617187187528", "item_1617349709064", "item_1617353299429", "item_1617605131499", "item_1617610673286", "item_1617620223087", "item_1617944105607", "item_1617187056579"], "$schema": "/items/jsonschema/1", "title": "test_title", "lang": ""}
            assert result == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # not exist title_parent_key in path
            mock_path = {
                "title": {},
                "pubDate": ""
            }
            with patch("weko_items_autofill.utils.get_title_pubdate_path", return_value=mock_path):
                result = deposit.record_data_from_act_temp()
                assert result == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # not exist title_value_lst_key, title_lang_lst_key
            mock_path = {
                "title": {
                    "title_parent_key": "item_1617186331708",
                },
                "pubDate": ""
            }
            with patch("weko_items_autofill.utils.get_title_pubdate_path", return_value=mock_path):
                result = deposit.record_data_from_act_temp()
                assert result == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def convert_item_metadata(self, index_obj, data=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_convert_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_convert_item_metadata(sel, app, db, es_records, redis_connect):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            record_data = record['item_data']
            index_obj = {'index': ['1'], 'actions': '1'}

            test1 = OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [
                                {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}), ('item_title', 'title'), ('item_type_id', '1'), ('control_number', '1'), ('author_link', []), ('_oai', {'id': '1'}), ('publish_date', '2022-08-20'), ('title', ['title']), ('relation_version_is_last', True), ('path', ['1']), ('publish_status', '0')])
            test2 = None
            ret1, ret2 = deposit.convert_item_metadata(index_obj, record_data)
            assert ret1 == test1
            assert ret2 == test2

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

            redis_data = {
                'pubdate': '2023-12-07',
                'item_1617187056579': 'item_1617187056579',
                'item_1617186331708': [{
                    'subitem_1551255647225': 'test',
                    'subitem_1551255648112': 'ja'
                }],
                'item_1617258105262': {
                    'resourcetype': 'conference paper',
                    'resourceuri': 'http://purl.org/coar/resource_type/c_5794'
                },
                'shared_user_id': -1,
                'title': 'test',
                'lang': 'ja',
                'deleted_items': [
                    'item_1617186385884',
                    'item_1617186419668',
                    'item_1617186499011',
                    'item_1617186609386',
                    'item_1617186626617',
                    'item_1617186643794',
                    'item_1617186660861',
                    'item_1617186702042',
                    'item_1617186783814',
                    'item_1617186859717',
                    'item_1617186882738',
                    'item_1617186901218',
                    'item_1617186920753',
                    'item_1617186941041',
                    'item_1617187112279',
                    'item_1617187187528',
                    'item_1617349709064',
                    'item_1617353299429',
                    'item_1617605131499',
                    'item_1617610673286',
                    'item_1617620223087',
                    'item_1617944105607',
                    'item_1617187056579',
                    'approval1',
                    'approval2'
                ],
                '$schema': '/items/jsonschema/1'
            }

            index_obj = {'index': ['1'], 'actions': '1'}

            # if datastore.redis.exists(cache_key) is false
            prefix = app.config['WEKO_DEPOSIT_ITEMS_CACHE_PREFIX']
            cache_key = app.config[
                'WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(
                pid_value=deposit.pid.pid_value)
            redis_connect.put(cache_key,bytes(json.dumps(redis_data),"utf-8"))
            app.config['WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'] = 'test_{pid_value}'
            dc = OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2023-12-07'}), ('item_1617187056579', {'attribute_name': 'Bibliographic Information', 'attribute_value': 'item_1617187056579'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]}), ('item_title', 'test'), ('item_type_id', '1'), ('control_number', '1'), ('author_link', []), ('publish_date', '2023-12-07'), ('title', ['test']), ('relation_version_is_last', True), ('path', ['1']), ('publish_status', '2')])
            with patch('weko_deposit.api.abort', side_effect=abort) as mock_abort:
                with pytest.raises(Exception):
                    deposit.convert_item_metadata(index_obj)
                    mock_abort.assert_called_once_with(500, 'MAPPING_ERROR')
                # mock_logger.assert_any_call(key="WEKO_COMMON_ERROR_UNEXPECTED", ex=mock.ANY)
                # mock_abort.reset_mock()
                # mock_logger.reset_mock()
            app.config['WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'] = prefix

            # if datastore.redis.exists(cache_key) is true
            dc = OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2023-12-07'}), ('item_1617187056579', {'attribute_name': 'Bibliographic Information', 'attribute_value': 'item_1617187056579'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]}), ('item_title', 'test'), ('item_type_id', '1'), ('control_number', '1'), ('author_link', []), ('publish_date', '2023-12-07'), ('title', ['test']), ('relation_version_is_last', True), ('path', ['1']), ('publish_status', '2')])
            cache_key = app.config[
                'WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(
                pid_value=deposit.pid.pid_value)
            redis_connect.put(cache_key,bytes(json.dumps(redis_data),"utf-8"))

            # index_obj.get('index', []) not exists
            index_obj = {'actions': '1', 'is_save_path': True}
            with pytest.raises(PIDResolveRESTError):
                deposit.convert_item_metadata(index_obj)

            # index_obj.get('is_save_path') exists
            index_obj = {'index': ['1'], 'actions': '1', 'is_save_path': True}
            ret1, ret2 = deposit.convert_item_metadata(index_obj)
            assert ret1 == dc
            assert ret2 == redis_data['deleted_items']
            assert redis_connect.redis.exists(cache_key) == True

            # index_obj.get('is_save_path') not exists, deletes cache_key
            index_obj = {'index': ['1'], 'actions': '1'}
            dc = OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2023-12-07'}), ('item_1617187056579', {'attribute_name': 'Bibliographic Information', 'attribute_value': 'item_1617187056579'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]}), ('item_title', 'test'), ('item_type_id', '1'), ('control_number', '1'), ('author_link', []), ('publish_date', '2023-12-07'), ('title', ['test']), ('relation_version_is_last', True), ('path', ['1']), ('publish_status', '2')])
            ret1, ret2 = deposit.convert_item_metadata(index_obj)
            assert ret1 == dc
            assert ret2 == redis_data['deleted_items']
            assert redis_connect.redis.exists(cache_key) == False

            # RedisError
            with patch('weko_deposit.api.RedisConnection.connection') as mock_redis:
                mock_redis.side_effect = RedisError("redis_error")
                with patch('weko_deposit.api.abort', side_effect=abort) as mock_abort:
                    with pytest.raises(Exception):
                        ret = deposit.convert_item_metadata(index_obj)
                        mock_redis.assert_called_once_with(500, 'Failed to register item!')
            # WekoRedisError
                mock_redis.side_effect = WekoRedisError("weko_redis_error")
                with patch('weko_deposit.api.abort', side_effect=abort) as mock_abort:
                    with pytest.raises(Exception):
                        ret = deposit.convert_item_metadata(index_obj)
                        mock_redis.assert_called_once_with(500, 'Failed to register item!')
            # Exception
                mock_redis.side_effect = Exception("error")
                with patch('weko_deposit.api.abort', side_effect=abort) as mock_abort:
                    with pytest.raises(Exception):
                        ret = deposit.convert_item_metadata(index_obj)
                        mock_redis.assert_called_once_with(500, 'Failed to register item!')

            # RuntimeError
            with patch('weko_deposit.api.json_loader', side_effect=RuntimeError):
                with pytest.raises(WekoDepositError):
                    ret = deposit.convert_item_metadata(index_obj)
                    mock_logger.assert_any_call(key='WEKO_DEPOSIT_FAILED_CONVERT_ITEM_METADATA', pid=mock.ANY, ex=mock.ANY)

            # index_obj.get('actions') is 'publish'
            index_obj = {'index': ['1'], 'actions': 'publish'}
            cache_key = app.config[
                'WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(
                pid_value=deposit.pid.pid_value)
            redis_connect.put(cache_key,bytes(json.dumps(redis_data),"utf-8"))
            dc = OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2023-12-07'}), ('item_1617187056579', {'attribute_name': 'Bibliographic Information', 'attribute_value': 'item_1617187056579'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]}), ('item_title', 'test'), ('item_type_id', '1'), ('control_number', '1'), ('author_link', []), ('publish_date', '2023-12-07'), ('title', ['test']), ('relation_version_is_last', True), ('path', ['1']), ('publish_status', '0')])
            ret1, ret2 = deposit.convert_item_metadata(index_obj)
            assert ret1 == dc
            assert ret2 == redis_data['deleted_items']

    # def _convert_description_to_object(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__convert_description_to_object -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__convert_description_to_object(sel, app, db, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            deposit._convert_description_to_object()
            jrc = {"description": "test_description"}
            deposit.jrc = jrc
            deposit._convert_description_to_object()

            jrc = {"description": ["test_description1",
                                   {"value": "test_description2"}]}
            deposit.jrc = jrc
            deposit._convert_description_to_object()
            assert deposit.jrc["description"] == [
                {"value": "test_description1"}, {"value": "test_description2"}]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def _convert_jpcoar_data_to_es(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__convert_jpcoar_data_to_es -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__convert_jpcoar_data_to_es(sel, app, db, location, es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']
        deposit._convert_jpcoar_data_to_es()

    # def _convert_data_for_geo_location(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__convert_data_for_geo_location -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__convert_data_for_geo_location(sel, app, db, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            deposit._convert_data_for_geo_location()

            jrc = {"geoLocation":{
                "geoLocationPlace":"test_location_place",
                "geoLocationPoint":{
                    "pointLongitude":"not_list_value",
                    "pointLatitude": "not_list_value"
                },
                "geoLocationPoint": {
                    "pointLongitude": ["1", "2", "3", "4"],
                    "pointLatitude": ["5", "6", "7", "8"]
                },
                "geoLocationBox": {
                    "northBoundLatitude": "not_list_value",
                    "eastBoundLongitude": "not_list_value",
                    "southBoundLatitude": "not_list_value",
                    "westBoundLongitude": "not_list_value"
                },
                "geoLocationBox": {
                    "northBoundLatitude": ["1", "2", "3"],
                    "eastBoundLongitude": ["4", "5", "6"],
                    "southBoundLatitude": ["7", "8", "9"],
                    "westBoundLongitude": ["0", "1", "2"]
                },
                "other": ""}}
            deposit.jrc = jrc
            test = {
                "geoLocationPlace": "test_location_place",
                "geoLocationPoint": [{"lat": "5", "lon": "1"}, {"lat": "6", "lon": "2"}, {"lat": "7", "lon": "3"}, {"lat": "8", "lon": "4"},],
                "geoLocationBox": {
                    "northEastPoint": [{"lat": "1", "lon": "4"}, {"lat": "2", "lon": "5"}, {"lat": "3", "lon": "6"},],
                    "southWestPoint": [{"lat": "7", "lon": "0"}, {"lat": "8", "lon": "1"}, {"lat": "9", "lon": "2"},],
                },
            }
            deposit._convert_data_for_geo_location()
            assert deposit.jrc["geoLocation"] == test

            record = records[1]
            deposit = record['deposit']
            deposit._convert_data_for_geo_location()

            jrc = {"geoLocation":{
                "geoLocationPlace":"test_location_place",
                "geoLocationPoint":{
                    "pointLongitude":"not_list_value",
                    "pointLatitude": "not_list_value"
                },
                "geoLocationPoint": {
                    "pointLongitude": {"1", "2", "3", "4"},
                    "pointLatitude": ["5", "6", "7", "8"]
                },
                "geoLocationBox": {
                    "northBoundLatitude": "not_list_value",
                    "eastBoundLongitude": "not_list_value",
                    "southBoundLatitude": "not_list_value",
                    "westBoundLongitude": "not_list_value"
                },
                "geoLocationBox": {
                    "northBoundLatitude": ["1", "2", "3"],
                    "eastBoundLongitude": ["4", "5", "6"],
                    "southBoundLatitude": ["7", "8", "9"],
                    "westBoundLongitude": ["0", "1", "2"]
                },
                "other": ""}}
            deposit.jrc = jrc
            test1 = {
                'geoLocationBox': {'northEastPoint': [{'lat': '1', 'lon': '4'},
                                                      {'lat': '2', 'lon': '5'},
                                                      {'lat': '3', 'lon': '6'}],
                                    'southWestPoint': [{'lat': '7', 'lon': '0'},
                                                       {'lat': '8', 'lon': '1'},
                                                       {'lat': '9', 'lon': '2'}]},
                'geoLocationPlace': 'test_location_place'
            }
            deposit._convert_data_for_geo_location()
            assert deposit.jrc["geoLocation"] == test1


            record = records[2]
            deposit = record['deposit']
            deposit._convert_data_for_geo_location()

            jrc = {"geoLocation":{
                "geoLocationPlace":"test_location_place",
                "geoLocationPoint":{
                    "pointLongitude":"not_list_value",
                    "pointLatitude": "not_list_value"
                },
                "geoLocationPoint": {
                    "pointLongitude": {"1", "2", "3", "4"},
                    "pointLatitude": {"5", "6", "7", "8"}
                },
                "geoLocationBox": {
                    "northBoundLatitude": "not_list_value",
                    "eastBoundLongitude": "not_list_value",
                    "southBoundLatitude": "not_list_value",
                    "westBoundLongitude": "not_list_value"
                },
                "geoLocationBox": {
                    "northBoundLatitude": {"1", "2", "3"},
                    "eastBoundLongitude": {"4", "5", "6"},
                    "southBoundLatitude": {"7", "8", "9"},
                    "westBoundLongitude": {"0", "1", "2"}
                },
                "other": ""}}
            deposit.jrc = jrc
            test2 = {
                'geoLocationPlace': 'test_location_place'
            }
            deposit._convert_data_for_geo_location()
            assert deposit.jrc["geoLocation"] == test2

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

            record = records[3]
            deposit = record['deposit']
            deposit._convert_data_for_geo_location()

            jrc = {"geoLocation":{
                "test":"test_location_place",
                "other": ""}}
            deposit.jrc = jrc
            test3 = {'other': '', 'test': 'test_location_place'}
            deposit._convert_data_for_geo_location()
            assert deposit.jrc["geoLocation"] == test3

    #         def _convert_geo_location(value):
    #         def _convert_geo_location_box():

    # def delete_by_index_tree_id(cls, index_id: str, ignore_items: list = []):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_by_index_tree_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_by_index_tree_id(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            deposit.delete_by_index_tree_id('1', [])

            record = records[1]
            deposit = record['deposit']
            deposit['9'] = '9'
            deposit.delete_by_index_tree_id('2', record['deposit'])

            record = records[2]
            deposit = record['deposit']
            deposit['path']='2'
            deposit.delete_by_index_tree_id('3',record['deposit'])

            record = records[3]
            deposit = record['deposit']
            deposit['path']='2'
            deposit.delete_by_index_tree_id('',record['deposit'])

            with patch("invenio_records.models.RecordMetadata.query") as mock_json:
                with pytest.raises(seacrh.exceptions.TransportError):
                    mock_json.return_value = True
                    record = records[1]
                    deposit = record['deposit']
                    deposit['path']='3'
                    deposit.delete_by_index_tree_id('2',record['deposit'])

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def update_pid_by_index_tree_id(self, path):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_pid_by_index_tree_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_pid_by_index_tree_id(sel, app, db, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            assert deposit.update_pid_by_index_tree_id('1') == True

            with patch("invenio_db.db.session.begin_nested", side_effect=SQLAlchemyError("test_error")):
                assert deposit.update_pid_by_index_tree_id('1')==False

            with patch("invenio_db.db.session.begin_nested", side_effect=Exception("test_error")):
                assert deposit.update_pid_by_index_tree_id('1') == False

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def update_item_by_task(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_item_by_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_item_by_task(sel, app, db, location, es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']
        record_data = record['record_data']
        ret = deposit.update_item_by_task()
        assert ret == deposit

    # def delete_es_index_attempt(self, pid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_es_index_attempt -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_es_index_attempt(sel, app, db, location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            # deposit = WekoDeposit.create({})
            session["activity_info"] = {"activity_id": '1'}
            data = {
                "$schema": "https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"}
            id = uuid.uuid4()
            deposit = WekoDeposit.create(data, id_=id)
            deposit.pid.status = "D"
            # deposit.pid = "1"
            db.session.commit()
            deposit.delete_es_index_attempt(deposit.pid)


            with patch("invenio_search.ext.Elasticsearch.delete", side_effect=Exception("test_error")):
                deposit = WekoDeposit.create({})
                deposit.pid.status = "D"
                db.session.commit()
                deposit.delete_es_index_attempt(deposit.pid)

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.reset_mock()

    # def update_author_link(self, author_link):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_author_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_author_link(sel, app, db, client, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with patch("weko_deposit.api.WekoIndexer.update_author_link") as mock_indexer_update_author_link:
                # author_link is empty
                _, records = es_records
                deposit = records[0]['deposit']
                author_link = {}
                deposit.update_author_link(author_link)
                mock_indexer_update_author_link.assert_not_called

                # author_link is not empty
                _, records = es_records
                deposit = records[1]['deposit']
                author_link = {
                        "id": deposit.id,
                        "author_link": ['0']
                    }
                deposit.update_author_link(author_link)
                author_link_info = {
                        "id": deposit.id,
                        "author_link": author_link
                    }
                mock_indexer_update_author_link.assert_called_once_with(author_link_info)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='author_link is not empty')
                mock_logger.reset_mock()

    # def update_feedback_mail(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_feedback_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_feedback_mail(sel, app, db, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            # indexer, records = es_records
            # record = records[0]
            # deposit = record['deposit']
            # assert deposit.update_feedback_mail()==None

            indexer, records = es_records
            record = records[1]
            deposit = record['deposit']
            assert deposit.update_feedback_mail()==None


    # def remove_feedback_mail(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_remove_feedback_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_remove_feedback_mail(sel, app, db, location, es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']
        assert deposit.remove_feedback_mail() == None

    # def clean_unuse_file_contents(self, item_id, pre_object_versions,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_clean_unuse_file_contents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_clean_unuse_file_contents(sel, app, db, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            bucket = Bucket.create()
            objs = list()
            for i in range(5):
                file = FileInstance(uri="/var/tmp/test_dir%s" %
                                    i, storage_class="S", size=18)
                objs.append(ObjectVersion.create(bucket=bucket.id,
                            key="test%s.txt" % i, _file_id=file))
            pre = objs[:3]
            new = objs[-3:]
            with patch("invenio_files_rest.storage.pyfs.PyFSFileStorage.delete"):
                deposit.clean_unuse_file_contents(1,pre,new)
                deposit.clean_unuse_file_contents(1,pre,new,is_import=True)

            record = records[1]
            deposit = record['deposit']
            bucket = Bucket.create()
            objs = list()
            for i in range(5):
                file = FileInstance(uri="/var/tmp/test1_dir%s" %
                                    i, storage_class="S", size=18)
                objs.append(ObjectVersion.create(bucket=bucket.id,
                            key="test%s.txt" % i, _file_id=file))
            pre = objs[:2]
            new = objs[-2:]
            with patch("invenio_files_rest.storage.pyfs.PyFSFileStorage.delete"):
                # deposit.clean_unuse_file_contents(1,pre,new)
                deposit.clean_unuse_file_contents(1, pre, new, is_import=True)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def merge_data_to_record_without_version(self, pid, keep_version=False,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_merge_data_to_record_without_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_merge_data_to_record_without_version(sel, app, db, location, es_records,es_records_8):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            recid = record['recid']

            assert deposit.merge_data_to_record_without_version(recid)
            assert deposit.merge_data_to_record_without_version(recid, keep_version=True)

            from invenio_records_files.models import RecordsBuckets
            from invenio_files_rest.models import Bucket
            indexer, records = es_records
            record = records[1]
            deposit = record['deposit']
            recid = record['recid']
            record_bucket=RecordsBuckets.query.filter_by(record_id=deposit.id).one_or_none()
            rd=RecordsBuckets(record_id=records[2]["recid"].object_uuid,bucket_id=record_bucket.bucket.id)
            db.session.add(rd)
            db.session.commit()
            assert deposit.merge_data_to_record_without_version(recid)


            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            record_bucket=RecordsBuckets.query.filter_by(record_id=deposit.id).one_or_none()
            if record_bucket:
                db.session.delete(record_bucket)
                db.session.commit()
            recid = record['recid']
            assert deposit.merge_data_to_record_without_version(recid)

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def prepare_draft_item(self, recid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_prepare_draft_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_prepare_draft_item(sel, app, db, location, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            recid = record['recid']
            with app.test_request_context():
                with patch("weko_deposit.api.WekoDeposit.newversion",return_value="new_version"):
                    assert deposit.prepare_draft_item(recid)=="new_version"

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
    # def delete_content_files(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_content_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_content_files(sel,app,db,location,es_records, es_records_4,es_records_7):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']

            ret = indexer.get_metadata_by_item_id(deposit.id)
            # 正しくない手法だが、Elasticsearchの結果を前提としている
            deposit.jrc = copy.deepcopy(ret['_source'])
            deposit.delete_content_files()
            ret['_source']['content'][0].pop('file')
            assert deposit.jrc==ret['_source']

            indexer, records = es_records_4
            record = records[0]
            deposit = record['deposit']
            ret = indexer.get_metadata_by_item_id(deposit.id)
            deposit.jrc = copy.deepcopy(ret['_source'])
            deposit.delete_content_files()

            indexer, records = es_records_7
            record = records[0]
            deposit = record['deposit']
            # del deposit['date']['file']
            ret = indexer.get_metadata_by_item_id(deposit.id)
            deposit.jrc = copy.deepcopy(ret['_source'])
            deposit.delete_content_files()
            assert deposit.jrc==ret['_source']

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

# class WekoRecord(Record):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp


class TestWekoRecord:
    #     def pid(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                assert record.pid == ""
            indexer, results = es_records
            result = results[0]
            record = result['record']
            pid = record.pid
            assert isinstance(pid, PersistentIdentifier) == True
            assert pid.pid_type == "depid"
            assert pid.pid_value == "1"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def pid_recid(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_recid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_recid(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                record.pid_recid

            indexer, results = es_records
            result = results[0]
            record = result['record']
            assert isinstance(record, WekoRecord) == True
            pid = record.pid_recid
            assert isinstance(pid, PersistentIdentifier) == True
            assert pid.pid_type == "recid"
            assert pid.pid_value == "1"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def pid_recid(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_recid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_recid(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                record.pid_recid

            indexer, results = es_records
            result = results[0]
            record = result['record']
            assert isinstance(record, WekoRecord) == True
            pid = record.pid_recid
            assert isinstance(pid, PersistentIdentifier) == True
            assert pid.pid_type == "recid"
            assert pid.pid_value == "1"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # TODO:
    #     def hide_file(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_hide_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_hide_file(self, es_records, es_records_2, es_records_5):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            # some value of 'attribute_type' is "file"
            # all option "hidden" is False
            _, results = es_records
            result = results[0]
            record = result['record']
            assert record.hide_file == False

            # contain option "hidden" is True
            _, results = es_records_2
            result = results[1]
            record = result['record']
            assert record.hide_file == True

            # all value of 'attribute_type' not "file"
            _, results = es_records_5
            result = results[1]
            record = result['record']
            assert record.hide_file ==  False
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    #     def navi(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_navi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_navi(self, app, users, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with app.test_request_context():
                assert record.navi == []
            indexer, results = es_records
            result = results[0]
            record = result['record']
            # assert record.navi==[]
            with app.test_request_context(query_string={"community": "test_com"}):
                assert record.navi == []

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def item_type_info(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_item_type_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_item_type_info(self, app, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with app.test_request_context():
                with pytest.raises(AttributeError):
                    assert record.item_type_info == ""
            indexer, results = es_records
            result = results[0]
            record = result['record']
            assert record.item_type_info == 'テストアイテムタイプ(1)'

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def switching_language(data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_switching_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_switching_language(self, app, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            # language = current_language
            with app.test_request_context(headers=[('Accept-Language', 'en')]):
                data = [{"language": "en", "title": "test_title"}]
                result = record.switching_language(data)
                assert result == "test_title"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # language != current_language, language=en
            with app.test_request_context(headers=[('Accept-Language', 'ja')]):
                data = [{"language": "en", "title": "test_title"}]
                result = record.switching_language(data)
                assert result == "test_title"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # language != en, exist language
            with app.test_request_context(headers=[('Accept-Language', 'da')]):
                data = [{"language": "ja", "title": "test_title"}]
                result = record.switching_language(data)
                assert result == "test_title"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # not exist language
            with app.test_request_context(headers=[('Accept-Language', 'da')]):
                data = [{"title": "test_title"}]
                result = record.switching_language(data)
                assert result == "test_title"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # len(data) <= 0
            with app.test_request_context(headers=[('Accept-Language', 'da')]):
                data = {}
                result = record.switching_language(data)
                assert result == ""

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # no language
            with app.test_request_context(headers=[('Accept-Language', 'da')]):
                data = [{"title": "title"}, {
                    "title": "en_title", "language": "en"}]
                result = record.switching_language(data)
                assert result == "title"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # no language
            with app.test_request_context(headers=[('Accept-Language', 'en')]):
                data = [{"title": "title"}, {
                    "title": "en_title", "language": "en"}]
                result = record.switching_language(data)
                assert result == "en_title"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # no language
            with app.test_request_context(headers=[('Accept-Language', 'ja')]):
                data = [{"title": "en_title", "language": "en"},
                        {"title": "title"}]
                result = record.switching_language(data)
                assert result == "en_title"

            # language != current_language, language=en
            with app.test_request_context(headers=[('Accept-Language', 'en')]):
                data = [{"language": "", "title": "test_title"},
                        {"language": "", "title": "test_title"}]
                result = record.switching_language(data)
                assert result == "test_title"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #.tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test__get_titles_key -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_titles_key(self,app,es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record["deposit"]
        meta_option, item_type_mapping = get_options_and_order_list(
            deposit.get('item_type_id'))
        meta_option ={
            "item_1617186609386":{
                "option":{
                    "hidden":False
                }
            },
            "key2":{}
        }
        item_type_mapping={"item_1617186609386": {
                "lom_mapping": "",
                "lido_mapping": "",
                "spase_mapping": "",
                "jpcoar_mapping": {
                    "title": {
                            "@value": "test1_subitem1",
                            "@attributes": {"xml:lang": "test1_subitem2"},
                            "model_id": "test_item1"
                    },
                    "subject": {
                        "@value": "subitem_1523261968819",
                        "@attributes": {
                            "xml:lang": "subitem_1522299896455",
                            "subjectURI": "subitem_1522300048512",
                            "subjectScheme": "subitem_1522300014469"
                        }
                    }
                },
                "junii2_mapping": "",
                "oai_dc_mapping": {
                    "subject": {
                        "@value": "subitem_1523261968819"
                    }
                },
                "display_lang_type": "",
                "jpcoar_v1_mapping": {
                    "subject": {
                        "@value": "subitem_1523261968819",
                        "@attributes": {
                            "xml:lang": "subitem_1522299896455",
                            "subjectURI": "subitem_1522300048512",
                            "subjectScheme": "subitem_1522300014469"
                        }
                    }
                }
            }}
        hide_list=["item_1617186609386.subitem_1523261968819","item_1617186609386","test1_subitem1"]
        app.config['BABEL_DEFAULT_LOCALE'] = 'ja'
        with app.test_request_context():
            assert record["record"]._WekoRecord__get_titles_key(item_type_mapping, meta_option,hide_list)

        record = records[1]
        deposit = record["deposit"]
        meta_option, item_type_mapping = get_options_and_order_list(
            deposit.get('item_type_id'))
        meta_option ={
            "item_1617186609386":{
                "option":{
                    "hidden":False
                }
            },
            "key2":{}
        }
        item_type_mapping={"item_1617186609386": {
                "lom_mapping": "",
                "lido_mapping": "",
                "spase_mapping": "",
                "jpcoar_mapping": {
                    "title": {
                            "@value": "test1_subitem1",
                            "@attributes": {"xml:lang": "test1_subitem2"},
                            "model_id": "test_item1"
                    },
                    "subject": {
                        "@value": "subitem_1523261968819",
                        "@attributes": {
                            "xml:lang": "subitem_1522299896455",
                            "subjectURI": "subitem_1522300048512",
                            "subjectScheme": "subitem_1522300014469"
                        }
                    }
                },
                "junii2_mapping": "",
                "oai_dc_mapping": {
                    "subject": {
                        "@value": "subitem_1523261968819"
                    }
                },
                "display_lang_type": "",
                "jpcoar_v1_mapping": {
                    "subject": {
                        "@value": "subitem_1523261968819",
                        "@attributes": {
                            "xml:lang": "subitem_1522299896455",
                            "subjectURI": "subitem_1522300048512",
                            "subjectScheme": "subitem_1522300014469"
                        }
                    }
                }
            }}
        hide_list=[{"item_1617186609386","test1_subitem2","test1_subitem1"}]
        app.config['BABEL_DEFAULT_LOCALE'] = 'ja'
        with app.test_request_context():
            assert record["record"]._WekoRecord__get_titles_key(item_type_mapping, meta_option,hide_list)

        record = records[2]
        deposit = record["deposit"]
        meta_option, item_type_mapping = get_options_and_order_list(
            deposit.get('item_type_id'))
        meta_option ={
            "item_1617186609386":{
                "option":{
                    "hidden":False
                }
            },
            "key2":{}
        }
        item_type_mapping={"item_1617186609386": {
                "lom_mapping": "",
                "lido_mapping": "",
                "spase_mapping": "",
                "jpcoar_mapping": {
                    "title": {
                            "@value": "test1_subitem1",
                            "@attributes": {"xml:lang": "test1_subitem2"},
                            "model_id": "test_item1"
                    },
                    "subject": {
                        "@value": "subitem_1523261968819",
                        "@attributes": {
                            "xml:lang": "subitem_1522299896455",
                            "subjectURI": "subitem_1522300048512",
                            "subjectScheme": "subitem_1522300014469"
                        }
                    }
                },
                "junii2_mapping": "",
                "oai_dc_mapping": {
                    "subject": {
                        "@value": "subitem_1523261968819"
                    }
                },
                "display_lang_type": "",
                "jpcoar_v1_mapping": {
                    "subject": {
                        "@value": "subitem_1523261968819",
                        "@attributes": {
                            "xml:lang": "subitem_1522299896455",
                            "subjectURI": "subitem_1522300048512",
                            "subjectScheme": "subitem_1522300014469"
                        }
                    }
                }
            }}
        hide_list=["item_1617186609386.subitem_1523261968819","item_1617186609386","test1_subitem1"]
        app.config['BABEL_DEFAULT_LOCALE'] = 'ja'
        with app.test_request_context():

            assert record["record"]._WekoRecord__get_titles_key(item_type_mapping, meta_option,hide_list)

    #     def get_titles(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_titles -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_titles(self,app,es_records,db_itemtype,db_oaischema,es_records_3,es_records_4):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with app.test_request_context():
                assert record.get_titles == ""
            indexer, results = es_records
            result = results[0]
            record = result['record']
            assert record['item_type_id'] == "1"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            with app.test_request_context():
                assert record.get_titles == "title"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            with app.test_request_context(headers=[("Accept-Language", "en")]):
                assert record.get_titles == "title"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            app.config['BABEL_DEFAULT_LOCALE'] = 'ja'
            # from flask_babelex import refresh; refresh()
            with app.test_request_context():
                assert record.get_titles == "タイトル"

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
            # from flask_babelex import refresh; refresh()
            with app.test_request_context():
                assert record.get_titles=="title"

            indexer, results = es_records_3
            result = results[0]
            record = result['record']
            with app.test_request_context(headers=[("Accept-Language", "ja")]):
                assert record.get_titles==""

            indexer, results = es_records_4
            result = results[0]
            record = result['record']
            with app.test_request_context(headers=[("Accept-Language", "en")]):
                assert record.get_titles=="title"

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def items_show_list(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_items_show_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_items_show_list(self, app, es_records, es_records_2, es_records_5, es_records_6, users, db_itemtype, db_admin_settings):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with app.test_request_context():
                with pytest.raises(AttributeError):
                    assert record.items_show_list == ""

            _, results = es_records
            result = results[0]
            record = result['record']
            version_id = str(result['version_id'])
            with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
                assert record.items_show_list == [{'attribute_name': 'PubDate', 'attribute_value': '2022-08-20', 'attribute_name_i18n': 'PubDate'}, {'attribute_name': 'Title', 'attribute_name_i18n': 'Title', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Title': 'タイトル'}], [{'Language': 'ja'}]]], [[[{'Title': 'title'}], [{'Language': 'en'}]]]]}, {'attribute_name': 'Resource Type', 'attribute_name_i18n': 'Resource Type', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Resource Type': 'conference paper'}], [{'Resource Type Identifier': 'http://purl.org/coar/resource_type/c_5794'}]]]]}, {'attribute_name': 'File', 'attribute_name_i18n': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [[[[{'dateType': 'Available', 'item_1617605131499[].date[0].dateValue': '2022-09-07'}]], [{'item_1617605131499[].url': 'https://weko3.example.org/record/1/files/hello.txt'}], [[{'item_1617605131499[].filesize[].value': '146 KB'}]], {'version_id': version_id, 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk', 'filename': 'hello.txt', 'filename.name': 'ファイル名', 'item_1617605131499[].format': 'plain/text', 'item_1617605131499[].accessrole': 'open_access'}]]}]

            _, results = es_records
            result = results[1]
            record = result['record']
            version_id = str(result['version_id'])
            with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
                assert record.items_show_list == [{'attribute_name': 'PubDate', 'attribute_value': '2022-08-20', 'attribute_name_i18n': 'PubDate'}, {'attribute_name': 'Title', 'attribute_name_i18n': 'Title', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Title': 'タイトル'}], [{'Language': 'ja'}]]], [[[{'Title': 'title'}], [{'Language': 'en'}]]]]}, {'attribute_name': 'Resource Type', 'attribute_name_i18n': 'Resource Type', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Resource Type': 'conference paper'}], [{'Resource Type Identifier': 'http://purl.org/coar/resource_type/c_5794'}]]]]}, {'attribute_name': 'File', 'attribute_name_i18n': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [[[[{'dateType': 'Available', 'item_1617605131499[].date[0].dateValue': '2022-09-07'}]], [{'item_1617605131499[].url': 'https://weko3.example.org/record/2/files/hello.txt'}], [[{'item_1617605131499[].filesize[].value': '146 KB'}]], {'version_id': version_id, 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk', 'filename': 'hello.txt', 'filename.name': 'ファイル名', 'item_1617605131499[].format': 'plain/text', 'item_1617605131499[].accessrole': 'open_access'}]]}]


            # contain hidden record
            _, results = es_records_2
            result = results[0]
            record = result['record']
            version_id = str(result['version_id'])
            with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
                assert record.items_show_list == [{'attribute_name': 'PubDate', 'attribute_value': '2022-08-20', 'attribute_name_i18n': 'PubDate'}, {'attribute_name': 'Creator', 'attribute_name_i18n': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'name': [], 'order_lang': []}, {'name': ['givenNames'], 'order_lang': [{'NoLanguage': {'givenName': ['givenNames'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': ['mei'], 'order_lang': [{'NoLanguage': {'familyName': ['mei'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': ['mei'], 'order_lang': [{'NoLanguage': {'familyName': ['mei'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': [], 'order_lang': []}, {'name': ['name'], 'order_lang': [{'NoLanguage': {'creatorName': ['name'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': [], 'order_lang': [], 'nameIdentifiers': [{'nameIdentifier': '識別'}, {'nameIdentifierURI': 'tets.com'}]}, {'name': [], 'order_lang': []}, {'name': ['別名'], 'order_lang': [{'NoLanguage': {'creatorAlternative': ['別名'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}]}, {'attribute_name': 'Resource Type', 'attribute_name_i18n': 'Resource Type', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Resource Type': 'conference paper'}], [{'Resource Type Identifier': 'http://purl.org/coar/resource_type/c_5794'}]]]]}, {'attribute_name': 'thumbnail', 'attribute_name_i18n': 'thumbnail', 'attribute_type': 'object', 'is_thumbnail': True}]

            #
            _, results = es_records_5
            result = results[1]
            record = result['record']
            version_id = str(result['version_id'])
            with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
                assert record.items_show_list == [{'attribute_name': 'PubDate', 'attribute_value': '2022-08-20', 'attribute_name_i18n': 'PubDate'}, {'attribute_name': 'Creator', 'attribute_name_i18n': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'name': [], 'order_lang': []}, {'name': ['givenNames'], 'order_lang': [{'NoLanguage': {'givenName': ['givenNames'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': ['mei'], 'order_lang': [{'NoLanguage': {'familyName': ['mei'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': ['mei'], 'order_lang': [{'NoLanguage': {'familyName': ['mei'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': [], 'order_lang': []}, {'name': ['name'], 'order_lang': [{'NoLanguage': {'creatorName': ['name'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': [], 'order_lang': [], 'nameIdentifiers': [{'nameIdentifier': '識別'}, {'nameIdentifierURI': 'tets.com'}]}, {'name': [], 'order_lang': []}, {'name': ['別名'], 'order_lang': [{'NoLanguage': {'creatorAlternative': ['別名'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}]}, {'attribute_name': 'Reference', 'attribute_name_i18n': 'Resource Type', 'attribute_type': None, 'attribute_value_mlt': [[{'item_1617258105262.resourcetype': 'conference paper', 'item_1617258105262.resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]]}, {'attribute_name': 'Bibliographic Information', 'attribute_name_i18n': 'Bibliographic Information', 'attribute_type': 'object', 'attribute_value_mlt': [{'title_attribute_name': [], 'magazine_attribute_name': [{'p.': '終了ページ'}], 'length': 1}, {'title_attribute_name': ['タイトル', 'ja : '], 'magazine_attribute_name': [], 'length': 0}, {'title_attribute_name': [], 'magazine_attribute_name': [{'p.': '開始ページ'}], 'length': 1}, {'title_attribute_name': [], 'magazine_attribute_name': [], 'length': 0}, {'title_attribute_name': [], 'magazine_attribute_name': [{'Issue Number': '号'}], 'length': 1}, {'title_attribute_name': [], 'magazine_attribute_name': [{'Number of Page': 'ページ数'}], 'length': 1}]}, {'attribute_name': 'thumbnail', 'attribute_name_i18n': 'thumbnail', 'attribute_type': 'object', 'attribute_value_mlt': []}]

            # contain 'input_type' == 'text', 'interim', contain BibliographicInfo
            _, results = es_records_6
            result = results[2]
            record = result['record']
            version_id = str(result['version_id'])
            # with patch("weko_deposit.api._FormatSysBibliographicInformation.is_bibliographic", return_value=True):
            assert record.items_show_list == [{'attribute_name': 'PubDate', 'attribute_value': '2022-08-20', 'attribute_name_i18n': 'PubDate'}, {'attribute_name': 'Creator', 'attribute_name_i18n': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'name': [], 'order_lang': []}, {'name': ['givenNames'], 'order_lang': [{'NoLanguage': {'givenName': ['givenNames'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': ['mei'], 'order_lang': [{'NoLanguage': {'familyName': ['mei'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': ['mei'], 'order_lang': [{'NoLanguage': {'familyName': ['mei'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': [], 'order_lang': []}, {'name': ['name'], 'order_lang': [{'NoLanguage': {'creatorName': ['name'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}, {'name': [], 'order_lang': [], 'nameIdentifiers': [{'nameIdentifier': '識別'}, {'nameIdentifierURI': 'tets.com'}]}, {'name': [], 'order_lang': []}, {'name': ['別名'], 'order_lang': [{'NoLanguage': {'creatorAlternative': ['別名'], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'ja': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}]}]}, {'attribute_name': 'Reference', 'attribute_type': 'file', 'content': [{'test': 'content'}, {'file': 'test'}], 'attribute_name_i18n': 'Resource Type'}, {'attribute_name': 'Bibliographic Information', 'attribute_name_i18n': 'Bibliographic Information', 'attribute_type': 'object', 'attribute_value_mlt': [{'title_attribute_name': [], 'magazine_attribute_name': [{'p.': '終了ページ'}], 'length': 1}, {'title_attribute_name': ['タイトル', 'ja : '], 'magazine_attribute_name': [], 'length': 0}, {'title_attribute_name': [], 'magazine_attribute_name': [{'p.': '開始ページ'}], 'length': 1}, {'title_attribute_name': [], 'magazine_attribute_name': [], 'length': 0}, {'title_attribute_name': [], 'magazine_attribute_name': [{'Issue Number': '号'}], 'length': 1}, {'title_attribute_name': [], 'magazine_attribute_name': [{'Number of Page': 'ページ数'}], 'length': 1}]}, {'attribute_name': 'Bibliographic Information', 'attribute_name_i18n': 'Bibliographic Information', 'attribute_type': 'object', 'attribute_value_mlt': [{'title_attribute_name': [], 'magazine_attribute_name': [{'p.': '終了ページ'}], 'length': 1}, {'title_attribute_name': ['タイトル', 'ja : '], 'magazine_attribute_name': [], 'length': 0}, {'title_attribute_name': [], 'magazine_attribute_name': [{'p.': '開始ページ'}], 'length': 1}, {'title_attribute_name': [], 'magazine_attribute_name': [], 'length': 0}, {'title_attribute_name': [], 'magazine_attribute_name': [{'Issue Number': '号'}], 'length': 1}, {'title_attribute_name': [], 'magazine_attribute_name': [{'Number of Page': 'ページ数'}], 'length': 1}]}, {'attribute_name': 'Bibliographic Information', 'attribute_name_i18n': 'Bibliographic Information', 'attribute_type': 'object', 'attribute_value_mlt': [[[]], [[]], [[]]]}, {'attribute_name': 'Information', 'attribute_type': 'object', 'attribute_value': '2022-08-20', 'attribute_name_i18n': 'Information'}, {'attribute_name': 'Information', 'attribute_type': 'nothing', 'attribute_name_i18n': 'Information'}, {'attribute_name': 'thumbnail', 'attribute_name_i18n': 'thumbnail', 'attribute_type': 'object', 'is_thumbnail': True}]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_display_file_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_display_file_info(self, app, es_records, es_records_6, es_records_5):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with app.test_request_context():
                with pytest.raises(AttributeError):
                    assert record.display_file_info == ""

            _, results = es_records
            result = results[0]
            record = result['record']
            with app.test_request_context("/test?filename=hello.txt"):
                assert record.display_file_info == [{'attribute_name': 'File', 'attribute_name_i18n': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [[[[{'Opendate': '2022-09-07'}], [
                    {'FileName': 'hello.txt'}], [{'Text URL': [[[{'Text URL': 'https://weko3.example.org/record/1/files/hello.txt'}]]]}], [{'Format': 'plain/text'}], [{'Size': [[[[{'Size': '146 KB'}]]]]}]]]]}]

            # invalid filename
            result = results[1]
            record = result['record']
            with app.test_request_context("/test?filename=no_hello.txt"):
                assert record.display_file_info == [{'attribute_name': 'File', 'attribute_name_i18n': 'File', 'attribute_type': 'file', 'attribute_value_mlt': []}]

            _, results = es_records_6
            result = results[0]
            record = result['record']
            with app.test_request_context("/test?filename=hello.txt"):
                assert record.display_file_info == [{'attribute_name': 'Reference', 'attribute_type': 'file', 'content': [{'test': 'content'}, {'file': 'test'}], 'attribute_name_i18n': 'Resource Type', 'attribute_value_mlt': [[[[{'Resource Type': ''}]]]]}]

        with patch('weko_deposit.api.weko_logger') as mock_logger:
            # nval['attribute_type'] == 'file
            _, results = es_records_5
            result = results[0]
            record = result['record']
            with app.test_request_context("/test?filename=hello.txt"):
                assert record.display_file_info == []

    #     def __remove_special_character_of_weko2(self, metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test__remove_special_character_of_weko2 -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__remove_special_character_of_weko2(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            indexer, results = es_records
            record = results[0]
            deposit = record["deposit"]
            metadata = ['url','date']
            assert record["record"]._WekoRecord__remove_special_character_of_weko2(metadata) is None

            metadata = ''
            assert record["record"]._WekoRecord__remove_special_character_of_weko2(metadata) is None

            metadata = [{''},'']
            assert record["record"]._WekoRecord__remove_special_character_of_weko2(metadata) is None

    #     def _get_creator(meta_data, hide_email_flag):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test__get_creator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            assert record._get_creator({}, False) == []

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
            assert record._get_creator({},True)==[]

            metadata = [{'url': {'url': 'https://weko3.example.org/record/2/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-07'}], 'format': 'plain/text', 'creatorMails': 'creatorMails', 'nameIdentifiers': 'nameIdentifiers', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_access', 'version_id': '18b2736a-fa2b-4b05-9582-86ffa87ebce9', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'}]
            assert record._get_creator(metadata,False)==[{'creatorMails': 'creatorMails','name': [],'nameIdentifiers': 'nameIdentifiers','order_lang': []}]
            assert record._get_creator(metadata,True)==[{'name': [], 'nameIdentifiers': 'nameIdentifiers', 'order_lang': []}]

            metadata = [{'url': {'url': 'https://weko3.example.org/record/2/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-07'}], 'format': 'plain/text', 'creatorMails': 'creatorMails', 'Identifiers': 'nameIdentifiers', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_access', 'version_id': '18b2736a-fa2b-4b05-9582-86ffa87ebce9', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'}]
            assert record._get_creator(metadata,True)==[{'name': [], 'order_lang': []}]
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def __remove_file_metadata_do_not_publish(self, file_metadata_list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test___remove_file_metadata_do_not_publish -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test___remove_file_metadata_do_not_publish(self,es_records,users):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, results = es_records
            record = results[0]
            file_metadata = [{'url': {'url': 'https://weko3.example.org/record/2/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-07'}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_date', 'version_id': '2dfc9468-6a1f-4204-928d-0795625b79c8', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'}]
            assert record["record"]._WekoRecord__remove_file_metadata_do_not_publish(file_metadata) ==[{'url': {'url': 'https://weko3.example.org/record/2/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-07'}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_date', 'version_id': '2dfc9468-6a1f-4204-928d-0795625b79c8', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'}]

            record = results[1]
            file_metadata = [{'url': {'url': 'https://weko3.example.org/record/2/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': ''}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_date', 'version_id': '2dfc9468-6a1f-4204-928d-0795625b79c8', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'}]
            assert record["record"]._WekoRecord__remove_file_metadata_do_not_publish(file_metadata) ==[]

            record = results[2]
            file_metadata = [{'url': {'url': 'https://weko3.example.org/record/2/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': ''}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'version_id': '2dfc9468-6a1f-4204-928d-0795625b79c8', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'}]
            assert record["record"]._WekoRecord__remove_file_metadata_do_not_publish(file_metadata) ==[{'url': {'url': 'https://weko3.example.org/record/2/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': ''}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'version_id': '2dfc9468-6a1f-4204-928d-0795625b79c8', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'}]

            record = results[3]
            user = users[0]
            with patch("flask_login.utils._get_user", return_value=user["obj"]):

                file_metadata = [{'url': {'url': 'https://weko3.example.org/record/2/files/hello.txt'}, 'accessrole': 'open_no', 'date': [{'dateType': 'Available', 'dateValue': ''}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'version_id': '2dfc9468-6a1f-4204-928d-0795625b79c8', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'}]
                assert record["record"]._WekoRecord__remove_file_metadata_do_not_publish(file_metadata) ==[]


    #     def __check_user_permission(user_id_list):
    #.tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test___check_user_permission -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test___check_user_permission(self,es_records,users):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, results = es_records
            record = results[0]
            user_id_list = ["1","2"]
            assert record["record"]._WekoRecord__check_user_permission(user_id_list) ==False

            record = results[1]
            user = users[6]
            with patch("flask_login.utils._get_user", return_value=user["obj"]):
                user_id_list = ["1","2","3","4","5"]
                assert record["record"]._WekoRecord__check_user_permission(user_id_list) ==True

            user = users[6]
            with patch("flask_login.utils._get_user", return_value=user["obj"]):
                user_id_list = [1,2,3,4,5,6,7,8]
                assert record["record"]._WekoRecord__check_user_permission(user_id_list) ==True

            user = users[7]
            with patch("flask_login.utils._get_user", return_value=user["obj"]):
                user_id_list = ["1","2","3","4","5"]
                assert record["record"]._WekoRecord__check_user_permission(user_id_list) ==False

            user = users[5]
            with patch("flask_login.utils._get_user", return_value=user["obj"]):
                user_id_list = ["1","2","3","4","5"]
                assert record["record"]._WekoRecord__check_user_permission(user_id_list) ==False

    #     def is_input_open_access_date(file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_is_input_open_access_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp

    def test_is_input_open_access_date(self):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            assert record.is_input_open_access_date({}) == False

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def is_do_not_publish(file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_is_do_not_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_do_not_publish(self):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            assert record.is_do_not_publish({}) == False

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def get_open_date_value(file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_open_date_value -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_open_date_value(self):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            assert record.get_open_date_value({}) == None

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def is_future_open_date(self, file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_is_future_open_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_future_open_date(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            assert record.is_future_open_date(record, {}) == True
            assert record.is_future_open_date(record, {'url': {'url': 'https://weko3.example.org/record/1/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-07'}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [
                                              {'value': '146 KB'}], 'accessrole': 'open_access', 'version_id': 'e131046c-291f-4065-b4b4-ca3bf1fac6e3', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'}) == False

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def pid_doi(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp

    def test_pid_doi(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                assert record.pid_doi == ""
            indexer, records = es_records
            record = records[0]['record']
            pid = record.pid_doi
            assert isinstance(pid, PersistentIdentifier) == True
            assert pid.pid_type == 'doi'

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def pid_cnri(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_cnri -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_cnri(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                assert record.pid_cnri == ""
            indexer, records = es_records
            record = records[0]['record']
            pid = record.pid_cnri
            assert isinstance(pid, PersistentIdentifier) == True
            assert pid.pid_type == 'hdl'

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def pid_parent(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_parent -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_parent(self,db,es_records_with_draft):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                assert record.pid_parent == ""

            indexer, records = es_records_with_draft
            record = records['record']
            pid = record.pid_parent
            assert isinstance(pid,PersistentIdentifier)==False


            es_records_with_draft[0]["record"].pid_parent
            assert isinstance(pid,PersistentIdentifier)==False

            es_records_with_draft[1]["record"].pid_parent
            assert isinstance(pid,PersistentIdentifier)==False
    #     def get_record_by_pid(cls, pid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_record_by_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_record_by_pid(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            recid = records[0]['recid']

            rec = WekoRecord.get_record_by_pid(1)
            assert isinstance(rec, WekoRecord)
            assert rec.pid_recid == recid

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def get_record_by_uuid(cls, uuid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_record_by_uuid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_record_by_uuid(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            recid = records[0]['recid']
            rec = WekoRecord.get_record_by_uuid(record.id)
            assert isinstance(rec, WekoRecord) == True
            assert rec.pid_recid == recid

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def get_record_cvs(cls, uuid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_record_cvs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_record_cvs(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            assert WekoRecord.get_record_cvs(record.id) == False

            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def _get_pid(self, pid_type):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test__get_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_pid(self, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            record = WekoRecord({})
            with pytest.raises(AttributeError):
                record._get_pid('')

            indexer, results = es_records
            result = results[0]
            result["record"]._get_pid('doi')

            with patch("weko_deposit.api.get_record_without_version") as mock_pid:
                mock_pid.return_value = False
                result = results[1]
                assert result["record"]._get_pid('doi') == None

            from invenio_pidstore.models import PersistentIdentifier, PIDStatus
            from invenio_pidstore.errors import PIDDoesNotExistError, PIDInvalidAction
            from weko_deposit.errors import WekoDepositError
            with patch("weko_deposit.api.db.desc", side_effect=PIDDoesNotExistError("test pid_type","test pid_value")):
                result = results[1]
                assert result["record"]._get_pid('doi') == None

            with patch("weko_deposit.api.db.desc", side_effect=SQLAlchemyError("test_error")):
                 with pytest.raises(WekoDepositError, match="Some error has occurred in weko_deposit."):
                     indexer, results = es_records
                     result = results[0]
                     record = result['record']
                     pid = record.pid
                     record._get_pid("recid")
                     mock_logger.assert_any_call(key='WEKO_COMMON_FAILED_GET_PID', value=mock.ANY)
                     mock_logger.reset_mock()

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()



    #     def update_item_link(self, pid_value):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_update_item_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_item_link(self,db, es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            from weko_records.models import ItemMetadata, ItemReference
            ir = ItemReference(
                src_item_pid='1', dst_item_pid='1', reference_type='1')
            db.session.add(ir)
            db.session.commit()
            indexer, records = es_records

            record = records[0]['record']
            recid = records[0]['recid']
            record.update_item_link(record.pid.pid_value)
            item_link = ItemLink.get_item_link_info(recid.pid_value)
            assert item_link == [
                {'item_links': '1', 'item_title': 'title', 'value': '1'}]
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    #     def get_file_data(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_file_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_file_data(self,app,es_records,es_records_3):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]["record"]
            with app.test_request_context():
                result = record.get_file_data()
                assert result[0]["accessrole"] == "open_access"
                assert result[0]["filename"] == "hello.txt"

            indexer, records = es_records_3
            record = records[0]["record"]
            with app.test_request_context():
                result = record.get_file_data()
                assert result == []

            with app.test_request_context():
                pass

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


# class _FormatSysCreator:
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class Test_FormatSysCreator:
    # def __init__(self, creator):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test___init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test___init__(self, app, prepare_creator):
        with app.test_request_context():
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True

#     def _get_creator_languages_order(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_languages_order -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_languages_order(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj, _FormatSysCreator) == True
                obj._get_creator_languages_order()
                assert obj.languages == ['ja', 'ja-Kana', 'en', 'cn']

            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj, _FormatSysCreator) == True
                obj._get_creator_languages_order()
                assert obj.languages == ['ja', 'ja-Kana', 'en', 'cn']

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def _format_creator_to_show_detail(self, language: str, parent_key: str,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_to_show_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_to_show_detail(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                language = 'en'
                parent_key = 'creatorNames'
                lst = []
                obj._format_creator_to_show_detail(language, parent_key, lst)
                assert lst == ['Joho, Taro']

                prepare_creator={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': []}
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                language = 'en'
                parent_key = 'creatorNames'
                lst = []
                obj._format_creator_to_show_detail(language,parent_key,lst)
                assert lst==[]

                prepare_creator={'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName_1': 'Joho, Taro', 'creatorNameLang': 'en'}]}
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                language = 'en'
                parent_key = 'creatorNames'
                lst = []
                obj._format_creator_to_show_detail(language,parent_key,lst)
                assert lst==[]

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    # * This is for testing only for the changes regarding creatorType
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
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    #     def _get_creator_to_show_popup(self, creators: Union[list, dict],
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_to_show_popup -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_to_show_popup(self, app, prepare_creator):
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

                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creators={'givenNames': [{'givenName': '太郎', 'givenNameLang': ''}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}]}
                language=''
                creator_list=["1","2"]
                creator_list_temp=["1","2"]
                obj._get_creator_to_show_popup(creators,language,creator_list,creator_list_temp)
                assert creators=={'givenNames': [{'givenName': '太郎', 'givenNameLang': ''}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}]}
                assert language==""
                assert creator_list==['1', '2']
                assert creator_list_temp==['1', '2']

                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creators={'givenNames': [{'givenName': '太郎', 'test1': 'ja'}, {'givenName': 'タロウ', 'test2': 'ja-Kana'}, {'givenName': 'Taro', 'test3': 'en'}]}
                language=''
                creator_list=[]
                creator_list_temp=None
                obj._get_creator_to_show_popup(creators,language,creator_list,creator_list_temp)
                assert creators=={'givenNames': [{'givenName': '太郎', 'test1': 'ja'}, {'givenName': 'タロウ', 'test2': 'ja-Kana'}, {'givenName': 'Taro', 'test3': 'en'}]}
                assert language==""
                assert creator_list==[{'NoLanguage': [{'givenName': '太郎', 'test1': 'ja'},{'givenName': 'タロウ', 'test2': 'ja-Kana'},{'givenName': 'Taro', 'test3': 'en'}]}]
                assert creator_list_temp==None

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    # * This is for testing only for the changes regarding creatorType
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
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()


    # def format_affiliation(affiliation_data):
    # def _run_format_affiliation(affiliation_max, affiliation_min,
    # def _get_creator_based_on_language(creator_data: dict,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_based_on_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_based_on_language(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj, _FormatSysCreator) == True
                creator_data = {'givenName': '太郎', 'givenNameLang': 'ja'}
                creator_list_temp = []
                language = 'ja'
                obj._get_creator_based_on_language(creator_data, creator_list_temp, language)
                assert creator_list_temp == [
                    {'givenName': '太郎', 'givenNameLang': 'ja'}]

                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj, _FormatSysCreator) == True
                creator_data = {'givenName': '太郎', 'givenNameLang': 'ja'}
                creator_list_temp = []
                language = ''
                obj._get_creator_based_on_language(
                    creator_data, creator_list_temp, language)
                assert creator_list_temp == []

                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creator_data ={}
                creator_list_temp=[]
                language=''
                obj._get_creator_based_on_language(creator_data,creator_list_temp,language)
                assert creator_list_temp==[{}]

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    # def format_creator(self) -> dict:
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test_format_creator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_format_creator(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                # assert obj.format_creator()=={'name': ['Joho, Taro','Joho', 'Taro', 'Alternative Name'], 'order_lang': [{'ja': {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}}, {'ja-Kana': {'creatorName': ['ジョウホウ, タロウ'], 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'cn': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [' Affilication Name'], 'affiliationNameIdentifier': [{'identifier': '', 'uri': ''}]}}]}
                # assert obj.format_creator()=={'name': ['Joho, Taro','Joho', 'Taro', 'Alternative Name'], 'order_lang': [{'ja': {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}}, {'ja-Kana': {'creatorName': ['ジョウホウ, タロウ'], 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'en': {'affiliationName': [],'affiliationNameIdentifier': [], 'creatorAlternative': ['Alternative Name'], 'creatorName': ['Joho, Taro']}},{'cn': {'affiliationName': [' Affilication Name'],'affiliationNameIdentifier': [{'identifier': '','uri': ''}],'creatorAlternative': [],'creatorName': None}}]}
                assert obj.format_creator()=={'name': ['Joho, Taro','Joho', 'Taro', 'Alternative Name'], 'order_lang': [{'ja': {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}}, {'ja-Kana': {'creatorName': ['ジョウホウ, タロウ'], 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'en': {'affiliationName': [],'affiliationNameIdentifier': [], 'creatorAlternative': ['Alternative Name'], 'creatorName': ['Joho, Taro']}},{'cn': {'affiliationName': [' Affilication Name'],'affiliationNameIdentifier': [{'identifier': '','uri': ''}],'creatorAlternative': [],'creatorName': None}}]}
                assert obj.format_creator()=={'name': ['Joho, Taro','Joho', 'Taro', 'Alternative Name'], 'order_lang': [{'ja': {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}}, {'ja-Kana': {'creatorName': ['ジョウホウ, タロウ'], 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'en': {'affiliationName': [],'affiliationNameIdentifier': [], 'creatorAlternative': ['Alternative Name'], 'creatorName': ['Joho, Taro']}},{'cn': {'creatorName': None, 'creatorAlternative': [], 'affiliationName': [' Affilication Name'], 'affiliationNameIdentifier': [{'identifier': '', 'uri': ''}]}}]}

                # with app.test_request_context(headers=[("Accept-Language", "en")]):
                #     prepare_creator_1={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}],'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}]}
                #     obj = _FormatSysCreator(prepare_creator_1)
                # assert obj.format_creator()== {'name': [], 'order_lang': []}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    # * This is for testing only for the changes regarding creatorType
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
                        assert "creatorType" not in list(
                            item.get("ja-Kana").keys())
                    elif item.get("en"):
                        assert "creatorType" not in list(item.get("en").keys())

    # def _format_creator_on_creator_popup(self, creators: Union[dict, list],
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_on_creator_popup -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_on_creator_popup(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator({})
                assert isinstance(obj, _FormatSysCreator) == True
                formatted_creator_list = []
                creator_list=[{'ja': {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}}, {'ja-Kana': {'givenName': ['タロウ'], 'givenNameLang': ['ja-Kana'], 'familyName': ['ジョウホウ'], 'familyNameLang': ['ja-Kana'], 'creatorName': ['ジョウホウ, タロウ'], 'creatorNameLang': ['ja-Kana']}}, {'en': {'givenName': ['Taro'], 'givenNameLang': ['en'], 'familyName': ['Joho'], 'familyNameLang': ['en'], 'creatorName': ['Joho, Taro'], 'creatorNameLang': ['en'], 'affiliationName': ['Affilication Name'], 'affiliationNameLang': ['en'], 'creatorAlternative': ['Alternative Name'], 'creatorAlternativeLang': ['en']}}]
                obj._format_creator_on_creator_popup(creator_list,formatted_creator_list)
                assert formatted_creator_list==[{'ja': {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}}, {'ja-Kana': {'creatorName': ['ジョウホウ, タロウ'], 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'en': {'creatorName': ['Joho, Taro'], 'creatorAlternative': ['Alternative Name'], 'affiliationName': [' Affilication Name'], 'affiliationNameIdentifier': [{'identifier': '', 'uri': ''}]}}]

                formatted_creator_list = []
                creator_list='givenName'
                obj._format_creator_on_creator_popup(creator_list,formatted_creator_list)
                assert formatted_creator_list==[]

                obj = _FormatSysCreator({})
                assert isinstance(obj, _FormatSysCreator) == True
                formatted_creator_list = []
                creator_list=[{'NoLanguage': {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'affiliationNameIdentifierScheme': '情報'}}]

                obj._format_creator_on_creator_popup(creator_list,formatted_creator_list)
                assert formatted_creator_list==[{'NoLanguage': {'affiliationName': ['情', '報'],'affiliationNameIdentifier': [{'identifier': '', 'uri': ''},{'identifier': '', 'uri': ''}],'affiliationNameIdentifierScheme': '情報','givenName': ['太郎'],'givenNameLang': ['ja']}}]

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    # def _format_creator_name(creator_data: dict,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_name(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj, _FormatSysCreator) == True
                creator_data1 = {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': [
                    'ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
                tmp = {}
                obj._format_creator_name(creator_data1, tmp)
                assert tmp == {'creatorName': ['情報, 太郎']}
                creator_data2 = {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': [
                    'ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
                tmp = {}
                obj._format_creator_name(creator_data2, tmp)
                assert tmp == {'creatorName': ['情報 太郎']}
                creator_data3 = {'familyName': ['情報']}
                tmp = {}
                obj._format_creator_name(creator_data3, tmp)
                assert tmp == {"creatorName": ['情報']}
                creator_data4 = {'givenName': ['太郎']}
                tmp = {}
                obj._format_creator_name(creator_data4, tmp)
                assert tmp == {"creatorName": ['太郎']}
                creator_data5 = {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報1', '情報2', '情報3'], 'familyNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': [
                    'ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
                tmp = {}
                obj._format_creator_name(creator_data5,tmp)
                assert tmp=={'creatorName': ['情報1 太郎', '情報2', '情報3']}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    # def _format_creator_affiliation(creator_data: dict,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_affiliation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_affiliation(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj,_FormatSysCreator)==True
                creator_data = {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
                des_creator = {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名']}
                obj._format_creator_affiliation(creator_data,des_creator)
                assert des_creator=={'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}

                creator_data = { 'affiliationName': [], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
                des_creator = {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名']}
                obj._format_creator_affiliation(creator_data,des_creator)
                assert des_creator=={'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}


                mock_logger.assert_any_call(key='WEKO_COMMON_WHILE_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_WHILE_END')
                mock_logger.reset_mock()

    #         def _get_max_list_length() -> int:
    # def _get_creator_to_display_on_popup(self, creator_list: list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_to_display_on_popup -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_to_display_on_popup(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context(headers=[("Accept-Language", "en")]):
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj, _FormatSysCreator) == True
                creator_list = []
                obj._get_creator_to_display_on_popup(creator_list)
                assert creator_list==[{'ja': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}, {'ja-Kana': [{'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}]}, {'en': [{'givenName': 'Taro', 'givenNameLang': 'en'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}]},{'cn': [{'affiliationName': 'Affilication Name','affiliationNameLang': 'cn'}]}]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def _merge_creator_data(self, creator_data: Union[list, dict],
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__merge_creator_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__merge_creator_data(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj, _FormatSysCreator) == True
                creator_data = [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja',
                                                                                                                                                                               'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]
                merged_data = {}
                obj._merge_creator_data(creator_data, merged_data)
                assert merged_data == {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': [
                    'ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

                creator_data = [{'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja',
                                                                                                                                   'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]
                merged_data = {'givenName': '次郎', 'givenNameLang': 'ja'}
                obj._merge_creator_data(creator_data, merged_data)
                assert merged_data == {'givenName': '次郎', 'givenNameLang': 'ja', 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': [
                    'ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

                creator_data = "not_dict_or_list"
                merged_data = {}
                obj._merge_creator_data(creator_data, merged_data)
                assert merged_data == {}

                creator_data = {'givenName': ['太郎']}
                merged_data = {}
                obj._merge_creator_data(creator_data, merged_data)
                assert merged_data == {}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

                creator_data = {'givenName': '太郎'}
                merged_data = {'givenName': ['次郎']}
                obj._merge_creator_data(creator_data, merged_data)
                assert merged_data == {'givenName': ['次郎', '太郎']}
                # todo37
                creator_data={'givenName': '太郎'}
                merged_data={'givenName': ['次郎']}
                obj._merge_creator_data(creator_data,merged_data)
                assert merged_data == {'givenName': ['次郎','太郎']}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

    #         def merge_data(key, value):
    # def _get_default_creator_name(self, list_parent_key: list,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_default_creator_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_default_creator_name(self, app, prepare_creator):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj, _FormatSysCreator) == True
                list_parent_key = ['creatorNames', 'familyNames',
                                   'givenNames', 'creatorAlternatives']
                creator_name = []
                obj.languages=["ja","en"]
                obj._get_default_creator_name(list_parent_key,creator_name)
                assert creator_name==['Joho, Taro', 'Joho', 'Taro', 'Alternative Name']

                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj, _FormatSysCreator) == True
                list_parent_key = []
                creator_name = []
                obj.languages = ["ja", "en"]
                obj._get_default_creator_name(list_parent_key, creator_name)
                assert creator_name == []

                obj = _FormatSysCreator(prepare_creator)
                assert isinstance(obj, _FormatSysCreator) == True
                list_parent_key = ['myNames']
                creator_name = []
                obj.languages = ["ja"]
                obj._get_default_creator_name(list_parent_key, creator_name)
                assert creator_name == []

                prepare_creator ={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'en'}, ]}
                with app.test_request_context(headers=[("Accept-Language", "ja")]):
                    obj = _FormatSysCreator(prepare_creator)
                    assert isinstance(obj, _FormatSysCreator) == True
                    list_parent_key = ['givenNames']

                    creator_name = []
                    obj.languages = ["en"]
                    obj._get_default_creator_name(list_parent_key, creator_name)
                    assert creator_name == ['太郎']

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.reset_mock()

#         def _get_creator(_language):

# class _FormatSysBibliographicInformation:
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp


class Test__FormatSysBibliographicInformation():
    # def __init__(self, bibliographic_meta_data_lst, props_lst):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test___init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test___init__(self, prepare_formatsysbib):
        meta, props = prepare_formatsysbib
        obj = _FormatSysBibliographicInformation(
            copy.deepcopy(meta), copy.deepcopy(props))
        assert isinstance(obj, _FormatSysBibliographicInformation) == True

    # def is_bibliographic(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test_is_bibliographic -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_bibliographic(self, app, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            obj = _FormatSysBibliographicInformation(
                copy.deepcopy(mlt), copy.deepcopy(solst))
            assert isinstance(obj, _FormatSysBibliographicInformation) == True
            assert obj.is_bibliographic() == True

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            obj.bibliographic_meta_data_lst = {"bibliographic_titles": "title"}
            assert obj.is_bibliographic() == True

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            obj.bibliographic_meta_data_lst = "str_value"
            assert obj.is_bibliographic() == False

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #         def check_key(_meta_data):
    # def get_bibliographic_list(self, is_get_list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test_get_bibliographic_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_bibliographic_list(self, app, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            obj = _FormatSysBibliographicInformation(
                copy.deepcopy(mlt), copy.deepcopy(solst))
            assert isinstance(obj, _FormatSysBibliographicInformation) == True
            with app.test_request_context(headers=[("Accept-Language", "en")]):
                # assert obj.get_bibliographic_list(True) == [{'title_attribute_name': 'Journal Title', 'magazine_attribute_name': [
                #     {'Volume': '1'}, {'Issue': '12'}, {'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 'length': 5}]
                assert obj.get_bibliographic_list(True) == [{'length': 5,'magazine_attribute_name': [{'Volume': '1'},{'Issue': '12'},{'p.': '1-100'},{'Number of Pages': '99'},{'Issued Date': '2022-08-29'}],'title_attribute_name': 'Journal Title'},{'length': 5,'magazine_attribute_name': [{'Volume': '1'},{'Issue': '12'},{'p.': '1'},{'Number of Pages': '99'},{'Issued Date': '2022-08-29'}],'title_attribute_name': []}]

                assert obj.get_bibliographic_list(False) == [{'length': 5,'magazine_attribute_name': [{'Volume Number': '1'},{'Issue Number': '12'},{'p.': '1-100'},{'Number of Page': '99'},{'Issue Date': '2022-08-29'}],'title_attribute_name': ['ja : 雑誌タイトル', 'en : Journal Title']},{'length': 5,'magazine_attribute_name': [{'Volume Number': '1'},{'Issue Number': '12'},{'p.': '1'},{'Number of Page': '99'},{'Issue Date': '2022-08-29'}],'title_attribute_name': []}]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def _get_bibliographic(self, bibliographic, is_get_list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_bibliographic -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_bibliographic(self, app, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            with app.test_request_context(headers=[("Accept-Language", "en")]):
                assert obj._get_bibliographic(bibliographic,True)==('Journal Title', [{'Volume': '1'}, {'Issue': '12'}, {'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 5)
                assert obj._get_bibliographic(bibliographic,False)==(['ja : 雑誌タイトル', 'en : Journal Title'], [{'Volume Number': '1'}, {'Issue Number': '12'}, {'p.': '1-100'}, {'Number of Page': '99'}, {'Issue Date': '2022-08-29'}], 5)

            with app.test_request_context(headers=[("Accept-Language", "")]):
                assert obj._get_bibliographic(bibliographic, True) == ('Journal Title', [{'Volume': '1'}, {
                    'Issue': '12'}, {'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 5)
                assert obj._get_bibliographic(bibliographic, False) == (['ja : 雑誌タイトル', 'en : Journal Title'], [{'Volume Number': '1'}, {
                    'Issue Number': '12'}, {'p.': '1-100'}, {'Number of Page': '99'}, {'Issue Date': '2022-08-29'}], 5)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

            bibliographic = mlt[1]
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True
            with app.test_request_context(headers=[("Accept-Language", "en")]):
               assert obj._get_bibliographic(bibliographic,True)==([],[{'Volume': '1'},{'Issue': '12'},{'p.': '1'},{'Number of Pages': '99'},{'Issued Date': '2022-08-29'}],5)
            with app.test_request_context(headers=[("Accept-Language", "")]):
                assert obj._get_bibliographic(bibliographic,True)==([],[{'Volume': '1'},{'Issue': '12'},{'p.': '1'},{'Number of Pages': '99'},{'Issued Date': '2022-08-29'}],5)


    # def _get_property_name(self, key):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_property_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_property_name(self, app, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            obj = _FormatSysBibliographicInformation(
                copy.deepcopy(mlt), copy.deepcopy(solst))
            assert isinstance(obj, _FormatSysBibliographicInformation) == True
            assert obj._get_property_name('subitem_1551255647225') == 'Title'

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            result = obj._get_property_name('not_exist_key')
            assert result == "not_exist_key"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def _get_translation_key(key, lang):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_translation_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_translation_key(self, app, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            obj = _FormatSysBibliographicInformation(
                copy.deepcopy(mlt), copy.deepcopy(solst))
            assert isinstance(obj, _FormatSysBibliographicInformation) == True
            for key in WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS:
                assert obj._get_translation_key(
                    key, "en") == WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS[key]["en"]

                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

            result = obj._get_translation_key("not_exist_key", "")
            assert result == None


    # def _get_bibliographic_information(self, bibliographic):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_bibliographic_information -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_bibliographic_information(self, app, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj = _FormatSysBibliographicInformation(
                copy.deepcopy(mlt), copy.deepcopy(solst))
            assert isinstance(obj, _FormatSysBibliographicInformation) == True
            assert obj._get_bibliographic_information(bibliographic) == ([{'Volume Number': '1'}, {
                'Issue Number': '12'}, {'p.': '1-100'}, {'Number of Page': '99'}, {'Issue Date': '2022-08-29'}], 5)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def _get_bibliographic_show_list(self, bibliographic, language):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_bibliographic_show_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_bibliographic_show_list(self, app, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj = _FormatSysBibliographicInformation(
                copy.deepcopy(mlt), copy.deepcopy(solst))
            assert isinstance(obj, _FormatSysBibliographicInformation) == True
            with app.test_request_context():
                assert obj._get_bibliographic_show_list(bibliographic, "ja") == (
                    [{'巻': '1'}, {'号': '12'}, {'p.': '1-100'}, {'ページ数': '99'}, {'発行年': '2022-08-29'}], 5)
                assert obj._get_bibliographic_show_list(bibliographic, "en") == ([{'Volume': '1'}, {'Issue': '12'}, {
                    'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 5)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def _get_source_title(source_titles):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test___get_source_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test___get_source_title(self, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
            assert isinstance(obj,_FormatSysBibliographicInformation) == True

            assert obj._get_source_title(bibliographic.get('bibliographic_titles'))==['ja : 雑誌タイトル', 'en : Journal Title']

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def _get_source_title_show_list(source_titles, current_lang):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_source_title_show_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_source_title_show_list(self, app, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj = _FormatSysBibliographicInformation(
                copy.deepcopy(mlt), copy.deepcopy(solst))
            assert isinstance(obj, _FormatSysBibliographicInformation) == True
            with app.test_request_context():
                assert obj._get_source_title_show_list(bibliographic.get(
                    'bibliographic_titles'), "en") == ('Journal Title', 'en')
                assert obj._get_source_title_show_list(bibliographic.get(
                    'bibliographic_titles'), "ja") == ('雑誌タイトル', 'ja')
                assert obj._get_source_title_show_list(bibliographic.get(
                    'bibliographic_titles'), "ja-Latn") == ('Journal Title', 'en')
                _title1 = bibliographic.get('bibliographic_titles').copy()
                _title1.pop()
                assert obj._get_source_title_show_list(
                    _title1, "ja-Latn") == ('雑誌タイトル', 'ja')

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.assert_any_call(
                    key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

            data = [{"bibliographic_titleLang": "ja-Latn",
                     "bibliographic_title": "ja-Latn_title"}]
            value, lang = obj._get_source_title_show_list(data, "en")
            assert value == "ja-Latn_title"
            assert lang == "ja-Latn"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


            data =[{"bibliographic_title":"not_key_title"},{"bibliographic_titleLang":"ja-Latn","bibliographic_title":"ja-Latn_title"}]
            value, lang = obj._get_source_title_show_list(data, "en")
            assert value == "not_key_title"
            assert lang == ""

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            app.config.update(WEKO_RECORDS_UI_LANG_DISP_FLG=True)
            data = [{}, {"bibliographic_title": "not_key_title"}, {"bibliographic_titleLang": "ja",
                                                                   "bibliographic_title": "ja_title"}, {"bibliographic_titleLang": "zh", "bibliographic_title": "zh_title"}]
            value, lang = obj._get_source_title_show_list(data, "en")
            assert value == "zh_title"
            assert lang == "zh"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            data = [{}, {"bibliographic_title": "not_key_title"}]
            value, lang = obj._get_source_title_show_list(data, "en")
            assert value == "not_key_title"
            assert lang == "ja"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            app.config.update(WEKO_RECORDS_UI_LANG_DISP_FLG=True)
            data = [{}, {"bibliographic_title": "not_key_title"}, {"bibliographic_titleLang": "ja","bibliographic_title": "ja_title"}, {"bibliographic_titleLang": "ja","bibliographic_title": "ja_title"}]

            value, lang = obj._get_source_title_show_list(data, "en")
            assert value == "not_key_title"
            assert lang == "ja"

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def _get_page_tart_and_page_end(page_start, page_end):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_page_tart_and_page_end -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_page_tart_and_page_end(self, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj = _FormatSysBibliographicInformation(
                copy.deepcopy(mlt), copy.deepcopy(solst))
            assert isinstance(obj, _FormatSysBibliographicInformation) == True
            assert obj._get_page_tart_and_page_end(bibliographic.get('bibliographicPageStart'),
                                                   bibliographic.get('bibliographicPageEnd')) == "{0}-{1}".format(bibliographic.get('bibliographicPageStart'),
                                                                                                                  bibliographic.get('bibliographicPageEnd'))

            bibliographic = mlt[1]
            bibliographic['bibliographicPageEnd'] is None
            assert obj._get_page_tart_and_page_end(bibliographic.get('bibliographicPageStart'),
                        bibliographic.get('bibliographicPageEnd'))=="1".format(bibliographic.get('bibliographicPageStart'),
                        bibliographic.get('bibliographicPageEnd'))

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def _get_issue_date(issue_date):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_issue_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_issue_date(self, prepare_formatsysbib):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            mlt, solst = prepare_formatsysbib
            bibliographic = mlt[0]
            obj = _FormatSysBibliographicInformation(
                copy.deepcopy(mlt), copy.deepcopy(solst))
            assert isinstance(obj, _FormatSysBibliographicInformation) == True
            assert obj._get_issue_date(bibliographic.get('bibliographicIssueDates')) == [
                bibliographic.get('bibliographicIssueDates').get('bibliographicIssueDate')]

            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
            data = [{"bibliographicIssueDate":'2022-08-29', 'bibliographicIssueDateType': 'Issued'},{"key":"value"}]
            result = obj._get_issue_date(data)
            assert result == ["2022-08-29"]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(
                key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(
                key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            data = "str_data"
            result = obj._get_issue_date(data)
            assert result == []
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


def test_missing_location(app, location, record ):
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
def test_weko_record(app, client, db, users, location):
    """Test record files property."""
    user = User.query.filter_by(email=users[4]['email']).first()
    login_user_via_session(client=client, user=user)
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
    with app.test_request_context(headers=[('Accept-Language', 'en')]):
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
    with app.test_request_context(headers=[('Accept-Language', 'en')]):
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
    indexer.client = MockClient()
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
    with pytest.raises(search.exceptions.NotFoundError):
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
    indexer.client = MockClient()
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
    with patch('weko_deposit.api.WekoIndexer.update_relation_version_is_last', side_effect=search.exceptions.NotFoundError):
        with pytest.raises(search.exceptions.NotFoundError):
            deposit.publish()


def test_delete_item_metadata(app, db, location):
    a = {'_oai': {'id': 'oai:weko3.example.org:00000002.1', 'sets': []}, 'path': ['1031'], 'owner': '1', 'recid': '2.1', 'title': ['ja_conference paperITEM00000002(public_open_access_open_access_simple)'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2021-02-13'}, '_buckets': {'deposit': '9766676f-0a12-439b-b5eb-6c39a61032c6'}, '_deposit': {'id': '2.1', 'pid': {'type': 'depid', 'value': '2.1', 'revision_id': 0}, 'owners': [1], 'status': 'draft'}, 'item_title': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'author_link': ['1', '2', '3'], 'item_type_id': '15', 'publish_date': '2021-02-13', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000002(public_open_access_simple)', 'subitem_1551255648112': 'en'}]}, 'item_1617186385884': {'attribute_name': 'Alternative Title', 'attribute_value_mlt': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}]}, 'item_1617186419668': {'attribute_name': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '1', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI'}]}]}, {'givenNames': [{'givenName': '次郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 次郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '2', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}, {'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 三郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '3', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}]}, 'item_1617186476635': {'attribute_name': 'Access Rights', 'attribute_value_mlt': [{'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}]}, 'item_1617186499011': {'attribute_name': 'Rights', 'attribute_value_mlt': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}]}, 'item_1617186609386': {'attribute_name': 'Subject', 'attribute_value_mlt': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}]}, 'item_1617186626617': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'Description\\nDescription<br/>Description&EMPTY&\\nDescription', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'en'}, {'subitem_description': '概要\\n概要&EMPTY&\\n概要\\n概要', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'ja'}]}, 'item_1617186643794': {'attribute_name': 'Publisher', 'attribute_value_mlt': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}]}, 'item_1617186660861': {'attribute_name': 'Date', 'attribute_value_mlt': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}]}, 'item_1617186702042': {'attribute_name': 'Language', 'attribute_value_mlt': [{'subitem_1551255818386': 'jpn'}]}, 'item_1617186783814': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_identifier_uri': 'http://localhost', 'subitem_identifier_type': 'URI'}]}, 'item_1617186859717': {'attribute_name': 'Temporal', 'attribute_value_mlt': [
        {'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}]}, 'item_1617186882738': {'attribute_name': 'Geo Location', 'attribute_value_mlt': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}]}, 'item_1617186901218': {'attribute_name': 'Funding Reference', 'attribute_value_mlt': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}]}, 'item_1617186920753': {'attribute_name': 'Source Identifier', 'attribute_value_mlt': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}]}, 'item_1617186941041': {'attribute_name': 'Source Title', 'attribute_value_mlt': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}]}, 'item_1617186959569': {'attribute_name': 'Volume Number', 'attribute_value_mlt': [{'subitem_1551256328147': '1'}]}, 'item_1617186981471': {'attribute_name': 'Issue Number', 'attribute_value_mlt': [{'subitem_1551256294723': '111'}]}, 'item_1617186994930': {'attribute_name': 'Number of Pages', 'attribute_value_mlt': [{'subitem_1551256248092': '12'}]}, 'item_1617187024783': {'attribute_name': 'Page Start', 'attribute_value_mlt': [{'subitem_1551256198917': '1'}]}, 'item_1617187045071': {'attribute_name': 'Page End', 'attribute_value_mlt': [{'subitem_1551256185532': '3'}]}, 'item_1617187112279': {'attribute_name': 'Degree Name', 'attribute_value_mlt': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}]}, 'item_1617187136212': {'attribute_name': 'Date Granted', 'attribute_value_mlt': [{'subitem_1551256096004': '2021-06-30'}]}, 'item_1617187187528': {'attribute_name': 'Conference', 'attribute_value_mlt': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'item_1617265215918': {'attribute_name': 'Version Type', 'attribute_value_mlt': [{'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}]}, 'item_1617349709064': {'attribute_name': 'Contributor', 'attribute_value_mlt': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'contributorType': 'ContactPerson', 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'lang': 'ja', 'contributorName': '情報, 太郎'}, {'lang': 'ja-Kana', 'contributorName': 'ジョウホウ, タロウ'}, {'lang': 'en', 'contributorName': 'Joho, Taro'}]}]}, 'item_1617349808926': {'attribute_name': 'Version', 'attribute_value_mlt': [{'subitem_1523263171732': 'Version'}]}, 'item_1617351524846': {'attribute_name': 'APC', 'attribute_value_mlt': [{'subitem_1523260933860': 'Unknown'}]}, 'item_1617353299429': {'attribute_name': 'Relation', 'attribute_value_mlt': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}]}, 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'url': {'url': 'https://weko3.example.org/record/2.1/files/1KB.pdf'}, 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'format': 'text/plain', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'mimetype': 'application/pdf', 'accessrole': 'open_access', 'version_id': '6f80e3cb-f681-45eb-bd54-b45be0f7d3ee', 'displaytype': 'simple'}]}, 'item_1617610673286': {'attribute_name': 'Rights Holder', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}], 'rightHolderNames': [{'rightHolderName': 'Right Holder Name', 'rightHolderLanguage': 'ja'}]}]}, 'item_1617620223087': {'attribute_name': 'Heading', 'attribute_value_mlt': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}]}, 'item_1617944105607': {'attribute_name': 'Degree Grantor', 'attribute_value_mlt': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}]}, 'relation_version_is_last': True}
    b = {'pid': {'type': 'depid', 'value': '2.0', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'owners': [1], 'status': 'published', '$schema': '15', 'pubdate': '2021-02-13', 'edit_mode': 'keep', 'created_by': 1, 'deleted_items': ['item_1617187056579', 'approval1', 'approval2'], 'shared_user_id': -1, 'weko_shared_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000002(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}]}, {'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 三郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '3', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\\nDescription<br/>Description&EMPTY&\\nDescription', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'en'}, {'subitem_description': '概要\\n概要&EMPTY&\\n概要\\n概要', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'ja'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617186783814': [{'subitem_identifier_uri': 'http://localhost', 'subitem_identifier_type': 'URI'}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {
        'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617349709064': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'contributorType': 'ContactPerson', 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'lang': 'ja', 'contributorName': '情報, 太郎'}, {'lang': 'ja-Kana', 'contributorName': 'ジョウホウ, タロウ'}, {'lang': 'en', 'contributorName': 'Joho, Taro'}]}], 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617605131499': [{'url': {'url': 'https://weko3.example.org/record/2/files/1KB.pdf'}, 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'format': 'text/plain', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'mimetype': 'application/pdf', 'accessrole': 'open_access', 'version_id': 'c92410f6-ed23-4d2e-a8c5-0b3b06cc79c8', 'displaytype': 'simple'}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}], 'rightHolderNames': [{'rightHolderName': 'Right Holder Name', 'rightHolderLanguage': 'ja'}]}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}], 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}]}
    # deposit = WekoDeposit.create(a)
