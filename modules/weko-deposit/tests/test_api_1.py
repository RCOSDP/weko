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

from elasticsearch.exceptions import NotFoundError
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
from elasticsearch import Elasticsearch
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

class MockClient():
    def __init__(self):
        self.is_get_error=True
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
                            "affiliationInfo":{}
                            }
                }

    def update(self, index=None, doc_type=None, id=None, body=None):
        if self.is_get_error:
            raise NotFoundError
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
    def test___init__(self,app,location):

        with patch('weko_deposit.api.weko_logger') as mock_logger:   
            bucket = Bucket.create()
            key = 'hello.txt'
            stream = BytesIO(b'helloworld')
            obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
            with app.test_request_context():
                file = WekoFileObject(obj,{})
                assert type(file)==WekoFileObject

            mock_logger.assert_any_call(key='WEKO_COMMON_CALLED_ARGUMENT', arg=mock.ANY)
            mock_logger.reset_mock()
       
    # def info(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoFileObject::test_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_info(self,app,location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            bucket = Bucket.create()
            key = 'hello.txt'
            stream = BytesIO(b'helloworld')
            obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
            with app.test_request_context():
                file = WekoFileObject(obj,{})
                assert file.info()=={'bucket': '{}'.format(file.bucket.id), 'checksum': 'sha256:936a185caaa266bb9cbe981e9e05cb78cd732b0b3280eb944412bb6f8f8f07af', 'key': 'hello.txt', 'size': 10, 'version_id': '{}'.format(file.version_id)}
                file.filename=key
                file['filename']=key
                assert file.info()=={'bucket': '{}'.format(file.bucket.id), 'checksum': 'sha256:936a185caaa266bb9cbe981e9e05cb78cd732b0b3280eb944412bb6f8f8f07af', 'key': 'hello.txt', 'size': 10, 'version_id': '{}'.format(file.version_id), 'filename': 'hello'}

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='filename exsisted')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
    
    #  def file_preview_able(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoFileObject::test_file_preview_able -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_file_preview_able(self,app,location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            bucket = Bucket.create()
            key = 'hello.txt'
            stream = BytesIO(b'helloworld')
            obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
            with app.test_request_context():
                file = WekoFileObject(obj,{})
                assert file.file_preview_able()==True
                app.config["WEKO_ITEMS_UI_MS_MIME_TYPE"] = WEKO_ITEMS_UI_MS_MIME_TYPE
                app.config["WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT+"] = {'ms_word': 30,'ms_powerpoint': 20,'ms_excel': 10}
                assert file.file_preview_able()==True
                file.data['format'] = 'application/vnd.ms-excel'
                assert file.file_preview_able()==True
                file.data['size'] = 10000000+1
                assert file.file_preview_able()==False
      
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()
            
    



# class WekoIndexer(RecordIndexer):

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestWekoIndexer:

    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_es_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_es_index(self,app):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer = WekoIndexer()
            assert isinstance(indexer,WekoIndexer)

            # def get_es_index(self):
            with app.test_request_context():
                indexer.get_es_index()
                assert indexer.es_index==app.config['SEARCH_UI_SEARCH_INDEX']
                assert indexer.es_doc_type==app.config['INDEXER_DEFAULT_DOCTYPE']
                assert indexer.file_doc_type=='content'

    #  def upload_metadata(self, jrc, item_id, revision_id, skip_files=False):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_upload_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_upload_metadata(self,app,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record_data = records[0]['record_data']
            item_id = records[0]['recid'].id
            revision_id=5
            skip_files=False
            title = 'UPDATE{}'.format(uuid.uuid4())
            record_data['title'] = title
            indexer.upload_metadata(record_data,item_id,revision_id,skip_files)
            ret = indexer.get_metadata_by_item_id(item_id)
            assert ret['_source']['title'] == title

            # mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def delete_file_index(self, body, parent_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_delete_file_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_file_index(self,app,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            dep = WekoDeposit(record,record.model)
            indexer.delete_file_index([record.id],record.pid)
                
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

            # Elastic Search Not Found Error
            from elasticsearch.exceptions import NotFoundError
            with pytest.raises(NotFoundError):
                indexer.get_metadata_by_item_id(record.pid)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.assert_any_call(key='WEKO_DEPOSIT_FAILED_DELETE_FILE_INDEX', record_id=mock.ANY, ex=mock.ANY)
                mock_logger.reset_mock()

            # Elastic Search Unexpected Error
            with patch("invenio_search.ext.Elasticsearch.delete", side_effect=Exception("test_error")):
                indexer.delete_file_index([record.id],record.pid)
                # mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
                mock_logger.reset_mock()


    # def update_relation_version_is_last(self, version):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_relation_version_is_last -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_relation_version_is_last(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            version = records[0]['record']
            pid = records[0]['recid']
            relations = serialize_relations(pid)
            relations_ver = relations['version'][0]
            relations_ver['id'] = pid.object_uuid
            relations_ver['is_last'] = relations_ver.get('index') == 0
            assert indexer.update_relation_version_is_last(relations_ver)=={'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': '{}'.format(pid.object_uuid), '_version': 2, 'result': 'noop', '_shards': {'total': 0, 'successful': 0, 'failed': 0}}

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def update_es_data(self, record, update_revision=True,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_es_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_es_data(self,es_records_1,db):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records_1
            record = records[0]['record']
            assert indexer.update_es_data(record, update_revision=False,update_oai=False, is_deleted=False)=={'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': '{}'.format(record.id), '_version': 4, 'result': 'updated', '_shards': {'total': 2, 'successful': 1, 'failed': 0}, '_seq_no': 9, '_primary_term': 1}
            res = indexer.update_es_data(record, update_revision=False,update_oai=True, is_deleted=False)
            assert res=={'_id': res['_id'], '_index': 'test-weko-item-v1.0.0', '_primary_term': 1, '_seq_no': 10, '_shards': {'failed': 0, 'successful': 1, 'total': 2}, '_type': 'item-v1.0.0', '_version': 5, 'result': 'updated'}

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            record = records[1]['record']
            record.model.version_id=4
            db.session.merge(record.model)
            db.session.commit()
            res = indexer.update_es_data(record, update_revision=True,update_oai=True, is_deleted=False)
            assert res=={'_id': res['_id'], '_index': 'test-weko-item-v1.0.0', '_primary_term': 1, '_seq_no': 11, '_shards': {'failed': 0, 'successful': 1, 'total': 2}, '_type': 'item-v1.0.0', '_version': 1, 'result': 'updated'}

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def index(self, record):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_index(self,es_records):
        indexer, records = es_records
        record = records[0]['record']
        indexer.index(record)

    # def delete(self, record):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete(self,es_records):
        indexer, records = es_records
        record = records[0]['record']
        indexer.delete(record)
        from elasticsearch.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            indexer.get_metadata_by_item_id(record.pid)

    #     def delete_by_id(self, uuid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_delete_by_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_by_id(self,es_records):
        indexer, records = es_records
        record = records[0]['record']
        indexer.delete_by_id(record.id)
        from elasticsearch.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            indexer.get_metadata_by_item_id(record.pid)

        indexer.delete_by_id(record.id)
        
        with patch("invenio_search.ext.Elasticsearch.delete", side_effect=Exception("test_error")):
            indexer.delete_by_id(record.id)
        

    # def get_count_by_index_id(self, tree_path):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_count_by_index_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_count_by_index_id(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            metadata = records[0]['record_data']
            ret = indexer.get_count_by_index_id(1)
            assert ret==4
            ret = indexer.get_count_by_index_id(2)
            assert ret==5

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def get_pid_by_es_scroll(self, path):
    #         def get_result(result):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_pid_by_es_scroll -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_pid_by_es_scroll(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            ret = indexer.get_pid_by_es_scroll(1)
            assert isinstance(next(ret),list)
            assert isinstance(next(ret),dict)
            assert ret is not None

            # todo2
            # indexer['']
            ret = indexer.get_pid_by_es_scroll( 'non_existent_path_12345' )

            # assert isinstance(next(ret),list)
            # assert isinstance(next(ret),dict)
            assert ret is None
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def get_metadata_by_item_id(self, item_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_metadata_by_item_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_metadata_by_item_id(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:

            indexer, records = es_records
            record = records[0]['record']
            record_data = records[0]['record_data']
            ret = indexer.get_metadata_by_item_id(record.id)
            assert ret['_index']=='test-weko-item-v1.0.0'

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def update_feedback_mail_list(self, feedback_mail):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_feedback_mail_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_feedback_mail_list(selft,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]['record']
            feedback_mail= {'id': record.id, 'mail_list': [{'email': 'wekosoftware@nii.ac.jp', 'author_id': ''}]}
            ret = indexer.update_feedback_mail_list(feedback_mail)
            assert ret == {'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': '{}'.format(record.id), '_version': 3, 'result': 'updated', '_shards': {'total': 2, 'successful': 1, 'failed': 0}, '_seq_no': 9, '_primary_term': 1}

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()


    #     def update_author_link(self, author_link):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_author_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_author_link(self,es_records):
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

                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()
       

    #     def update_jpcoar_identifier(self, dc, item_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_jpcoar_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_jpcoar_identifier(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record_data = records[0]['record_data']
            record = records[0]['record']
            assert indexer.update_jpcoar_identifier(record_data,record.id)=={'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': '{}'.format(record.id), '_version': 3, 'result': 'updated', '_shards': {'total': 2, 'successful': 1, 'failed': 0}, '_seq_no': 9, '_primary_term': 1}

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    #     def __build_bulk_es_data(self, updated_data):
    #     def bulk_update(self, updated_data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_bulk_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_bulk_update(self,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            res = []
            res.append(records[0]['record'])
            res.append(records[1]['record'])
            res.append(records[2]['record'])
            indexer.bulk_update(res)
            
            with patch("weko_deposit.api.bulk",return_value=(0,["test_error1","test_error2"])):
                indexer.bulk_update(res)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()


# class WekoDeposit(Deposit):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestWekoDeposit:
    # def item_metadata(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_item_metadata(self,app,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            deposit = records[0]['deposit']
            assert deposit.item_metadata=={'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'title', 'owners': [1], 'status': 'published', '$schema': '/items/jsonschema/1', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_id': -1, 'item_1617186331708': [{'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}}

            deposit = WekoDeposit({})
            from sqlalchemy.orm.exc import NoResultFound
            with pytest.raises(NoResultFound):
                assert deposit.item_metadata == ""

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def is_published(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_is_published -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_published(self,app,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            deposit = records[0]['deposit']        
            assert deposit.is_published()==True

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def merge_with_published(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_merge_with_published -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_merge_with_published(self,app,db,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            dep = records[0]['deposit']
            ret = dep.merge_with_published()
            assert isinstance(ret,RecordRevision)==True
            
            dep = records[1]["deposit"]
            dep["$schema"] = "https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"
            dep["control_number"] = "1"
            db.session.commit()
            ret = dep.merge_with_published()
            assert isinstance(ret,RecordRevision)==True


            from dictdiffer.merge import UnresolvedConflictsException
            from invenio_deposit.errors import MergeConflict
            from weko_deposit.errors import WekoDepositError
            # with patch("weko_deposit.api.WekoDeposit.fetch_published",return_value=(records[0]["depid"],record)):
            # with patch("weko_deposit.api.Merger.run",side_effect=UnresolvedConflictsException(["test_conflict"])):
            #     with patch("weko_deposit.api.Merger.run", side_effect=WekoDepositError("test_error")):
            #         ret = dep.merge_with_published()

            # todo3
            # with patch("weko_deposit.api.Merger.run", side_effect=Exception("test_error")):
            #     with patch("weko_deposit.api.Merger.run", side_effect=WekoDepositError("test_error")):
            #         ret = dep.merge_with_published()
            #         mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)  
            
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def _patch(diff_result, destination, in_place=False):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__patch -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__patch(self,app,location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                dep = WekoDeposit.create({})
                #diff_result = [('change', '_buckets.deposit', ('753ff0d7-0659-4460-9b1a-fd1ef38467f2', '688f2d41-be61-468f-95e2-a06abefdaf60')), ('change', '_buckets.deposit', ('753ff0d7-0659-4460-9b1a-fd1ef38467f2', '688f2d41-be61-468f-95e2-a06abefdaf60')), ('add', '', [('_oai', {})]), ('add', '', [('_oai', {})]), ('add', '_oai', [('id', 'oai:weko3.example.org:00000013')]), ('add', '_oai', [('id', 'oai:weko3.example.org:00000013')]), ('add', '_oai', [('sets', [])]), ('add', '_oai', [('sets', [])]), ('add', '_oai.sets', [(0, '1661517684078')]), ('add', '_oai.sets', [(0, '1661517684078')]), ('add', '', [('author_link', [])]), ('add', '', [('author_link', [])]), ('add', 'author_link', [(0, '4')]), ('add', 'author_link', [(0, '4')]), ('add', '', [('item_1617186331708', {})]), ('add', '', [('item_1617186331708', {})]), ('add', 'item_1617186331708', [('attribute_name', 'Title')]), ('add', 'item_1617186331708', [('attribute_name', 'Title')]), ('add', 'item_1617186331708', [('attribute_value_mlt', [])]), ('add', 'item_1617186331708', [('attribute_value_mlt', [])]), ('add', 'item_1617186331708.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186331708.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255647225', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255647225', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255648112', 'ja')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255648112', 'ja')]), ('add', 'item_1617186331708.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186331708.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255647225', 'en_conference paperITEM00000001(public_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255647225', 'en_conference paperITEM00000001(public_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255648112', 'en')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255648112', 'en')]), ('add', '', [('item_1617186385884', {})]), ('add', '', [('item_1617186385884', {})]), ('add', 'item_1617186385884', [('attribute_name', 'Alternative Title')]), ('add', 'item_1617186385884', [('attribute_name', 'Alternative Title')]), ('add', 'item_1617186385884', [('attribute_value_mlt', [])]), ('add', 'item_1617186385884', [('attribute_value_mlt', [])]), ('add', 'item_1617186385884.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186385884.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255721061', 'en')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255721061', 'en')]), ('add', 'item_1617186385884.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186385884.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255721061', 'ja')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255721061', 'ja')]), ('add', '', [('item_1617186419668', {})]), ('add', '', [('item_1617186419668', {})]), ('add', 'item_1617186419668', [('attribute_name', 'Creator')]), ('add', 'item_1617186419668', [('attribute_name', 'Creator')]), ('add', 'item_1617186419668', [('attribute_type', 'creator')]), ('add', 'item_1617186419668', [('attribute_type', 'creator')]), ('add', 'item_1617186419668', [('attribute_value_mlt', [])]), ('add', 'item_1617186419668', [('attribute_value_mlt', [])]), ('add', 'item_1617186419668.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186419668.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorAffiliations', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorAffiliations', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifier', '0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifier', '0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierScheme', 'ISNI')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierScheme', 'ISNI')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierURI', 'http://isni.org/isni/0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierURI', 'http://isni.org/isni/0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationName', 'University')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationName', 'University')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', '4')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', '4')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'WEKO')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'WEKO')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(3, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(3, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', 'item_1617186419668.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186419668.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', 'item_1617186419668.attribute_value_mlt', [(2, {})]), ('add', 'item_1617186419668.attribute_value_mlt', [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', '', [('item_1617186476635', {})]), ('add', '', [('item_1617186476635', {})]), ('add', 'item_1617186476635', [('attribute_name', 'Access Rights')]), ('add', 'item_1617186476635', [('attribute_name', 'Access Rights')]), ('add', 'item_1617186476635', [('attribute_value_mlt', [])]), ('add', 'item_1617186476635', [('attribute_value_mlt', [])]), ('add', 'item_1617186476635.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186476635.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1522299639480', 'open access')]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1522299639480', 'open access')]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1600958577026', 'http://purl.org/coar/access_right/c_abf2')]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1600958577026', 'http://purl.org/coar/access_right/c_abf2')]), ('add', '', [('item_1617186499011', {})]), ('add', '', [('item_1617186499011', {})]), ('add', 'item_1617186499011', [('attribute_name', 'Rights')]), ('add', 'item_1617186499011', [('attribute_name', 'Rights')]), ('add', 'item_1617186499011', [('attribute_value_mlt', [])]), ('add', 'item_1617186499011', [('attribute_value_mlt', [])]), ('add', 'item_1617186499011.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186499011.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650717957', 'ja')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650717957', 'ja')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650727486', 'http://localhost')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650727486', 'http://localhost')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522651041219', 'Rights Information')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522651041219', 'Rights Information')]), ('add', '', [('item_1617186609386', {})]), ('add', '', [('item_1617186609386', {})]), ('add', 'item_1617186609386', [('attribute_name', 'Subject')]), ('add', 'item_1617186609386', [('attribute_name', 'Subject')]), ('add', 'item_1617186609386', [('attribute_value_mlt', [])]), ('add', 'item_1617186609386', [('attribute_value_mlt', [])]), ('add', 'item_1617186609386.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186609386.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522299896455', 'ja')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522299896455', 'ja')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300014469', 'Other')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300014469', 'Other')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300048512', 'http://localhost/')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300048512', 'http://localhost/')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1523261968819', 'Sibject1')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1523261968819', 'Sibject1')]), ('add', '', [('item_1617186626617', {})]), ('add', '', [('item_1617186626617', {})]), ('add', 'item_1617186626617', [('attribute_name', 'Description')]), ('add', 'item_1617186626617', [('attribute_name', 'Description')]), ('add', 'item_1617186626617', [('attribute_value_mlt', [])]), ('add', 'item_1617186626617', [('attribute_value_mlt', [])]), ('add', 'item_1617186626617.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186626617.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description', 'Description\nDescription<br/>Description')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description', 'Description\nDescription<br/>Description')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_language', 'en')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_language', 'en')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_type', 'Abstract')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_type', 'Abstract')]), ('add', 'item_1617186626617.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186626617.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description', '概要\n概要\n概要\n概要')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description', '概要\n概要\n概要\n概要')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_language', 'ja')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_language', 'ja')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_type', 'Abstract')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_type', 'Abstract')]), ('add', '', [('item_1617186643794', {})]), ('add', '', [('item_1617186643794', {})]), ('add', 'item_1617186643794', [('attribute_name', 'Publisher')]), ('add', 'item_1617186643794', [('attribute_name', 'Publisher')]), ('add', 'item_1617186643794', [('attribute_value_mlt', [])]), ('add', 'item_1617186643794', [('attribute_value_mlt', [])]), ('add', 'item_1617186643794.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186643794.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300295150', 'en')]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300295150', 'en')]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300316516', 'Publisher')]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300316516', 'Publisher')]), ('add', '', [('item_1617186660861', {})]), ('add', '', [('item_1617186660861', {})]), ('add', 'item_1617186660861', [('attribute_name', 'Date')]), ('add', 'item_1617186660861', [('attribute_name', 'Date')]), ('add', 'item_1617186660861', [('attribute_value_mlt', [])]), ('add', 'item_1617186660861', [('attribute_value_mlt', [])]), ('add', 'item_1617186660861.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186660861.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300695726', 'Available')]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300695726', 'Available')]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300722591', '2021-06-30')]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300722591', '2021-06-30')]), ('add', '', [('item_1617186702042', {})]), ('add', '', [('item_1617186702042', {})]), ('add', 'item_1617186702042', [('attribute_name', 'Language')]), ('add', 'item_1617186702042', [('attribute_name', 'Language')]), ('add', 'item_1617186702042', [('attribute_value_mlt', [])]), ('add', 'item_1617186702042', [('attribute_value_mlt', [])]), ('add', 'item_1617186702042.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186702042.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186702042', 'attribute_value_mlt', 0], [('subitem_1551255818386', 'jpn')]), ('add', ['item_1617186702042', 'attribute_value_mlt', 0], [('subitem_1551255818386', 'jpn')]), ('add', '', [('item_1617186783814', {})]), ('add', '', [('item_1617186783814', {})]), ('add', 'item_1617186783814', [('attribute_name', 'Identifier')]), ('add', 'item_1617186783814', [('attribute_name', 'Identifier')]), ('add', 'item_1617186783814', [('attribute_value_mlt', [])]), ('add', 'item_1617186783814', [('attribute_value_mlt', [])]), ('add', 'item_1617186783814.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186783814.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_type', 'URI')]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_type', 'URI')]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_uri', 'http://localhost')]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_uri', 'http://localhost')]), ('add', '', [('item_1617186859717', {})]), ('add', '', [('item_1617186859717', {})]), ('add', 'item_1617186859717', [('attribute_name', 'Temporal')]), ('add', 'item_1617186859717', [('attribute_name', 'Temporal')]), ('add', 'item_1617186859717', [('attribute_value_mlt', [])]), ('add', 'item_1617186859717', [('attribute_value_mlt', [])]), ('add', 'item_1617186859717.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186859717.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658018441', 'en')]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658018441', 'en')]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658031721', 'Temporal')]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658031721', 'Temporal')]), ('add', '', [('item_1617186882738', {})]), ('add', '', [('item_1617186882738', {})]), ('add', 'item_1617186882738', [('attribute_name', 'Geo Location')]), ('add', 'item_1617186882738', [('attribute_name', 'Geo Location')]), ('add', 'item_1617186882738', [('attribute_value_mlt', [])]), ('add', 'item_1617186882738', [('attribute_value_mlt', [])]), ('add', 'item_1617186882738.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186882738.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0], [('subitem_geolocation_place', [])]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0], [('subitem_geolocation_place', [])]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place'], [(0, {})]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place'], [(0, {})]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place', 0], [('subitem_geolocation_place_text', 'Japan')]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place', 0], [('subitem_geolocation_place_text', 'Japan')]), ('add', '', [('item_1617186901218', {})]), ('add', '', [('item_1617186901218', {})]), ('add', 'item_1617186901218', [('attribute_name', 'Funding Reference')]), ('add', 'item_1617186901218', [('attribute_name', 'Funding Reference')]), ('add', 'item_1617186901218', [('attribute_value_mlt', [])]), ('add', 'item_1617186901218', [('attribute_value_mlt', [])]), ('add', 'item_1617186901218.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186901218.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399143519', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399143519', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399281603', 'ISNI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399281603', 'ISNI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399333375', 'http://xxx')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399333375', 'http://xxx')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399412622', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399412622', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522399416691', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522399416691', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522737543681', 'Funder Name')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522737543681', 'Funder Name')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399571623', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399571623', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399585738', 'Award URI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399585738', 'Award URI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399628911', 'Award Number')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399628911', 'Award Number')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399651758', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399651758', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721910626', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721910626', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721929892', 'Award Title')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721929892', 'Award Title')]), ('add', '', [('item_1617186920753', {})]), ('add', '', [('item_1617186920753', {})]), ('add', 'item_1617186920753', [('attribute_name', 'Source Identifier')]), ('add', 'item_1617186920753', [('attribute_name', 'Source Identifier')]), ('add', 'item_1617186920753', [('attribute_value_mlt', [])]), ('add', 'item_1617186920753', [('attribute_value_mlt', [])]), ('add', 'item_1617186920753.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186920753.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646500366', 'ISSN')]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646500366', 'ISSN')]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646572813', 'xxxx-xxxx-xxxx')]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646572813', 'xxxx-xxxx-xxxx')]), ('add', '', [('item_1617186941041', {})]), ('add', '', [('item_1617186941041', {})]), ('add', 'item_1617186941041', [('attribute_name', 'Source Title')]), ('add', 'item_1617186941041', [('attribute_name', 'Source Title')]), ('add', 'item_1617186941041', [('attribute_value_mlt', [])]), ('add', 'item_1617186941041', [('attribute_value_mlt', [])]), ('add', 'item_1617186941041.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186941041.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650068558', 'en')]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650068558', 'en')]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650091861', 'Source Title')]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650091861', 'Source Title')]), ('add', '', [('item_1617186959569', {})]), ('add', '', [('item_1617186959569', {})]), ('add', 'item_1617186959569', [('attribute_name', 'Volume Number')]), ('add', 'item_1617186959569', [('attribute_name', 'Volume Number')]), ('add', 'item_1617186959569', [('attribute_value_mlt', [])]), ('add', 'item_1617186959569', [('attribute_value_mlt', [])]), ('add', 'item_1617186959569.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186959569.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186959569', 'attribute_value_mlt', 0], [('subitem_1551256328147', '1')]), ('add', ['item_1617186959569', 'attribute_value_mlt', 0], [('subitem_1551256328147', '1')]), ('add', '', [('item_1617186981471', {})]), ('add', '', [('item_1617186981471', {})]), ('add', 'item_1617186981471', [('attribute_name', 'Issue Number')]), ('add', 'item_1617186981471', [('attribute_name', 'Issue Number')]), ('add', 'item_1617186981471', [('attribute_value_mlt', [])]), ('add', 'item_1617186981471', [('attribute_value_mlt', [])]), ('add', 'item_1617186981471.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186981471.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186981471', 'attribute_value_mlt', 0], [('subitem_1551256294723', '111')]), ('add', ['item_1617186981471', 'attribute_value_mlt', 0], [('subitem_1551256294723', '111')]), ('add', '', [('item_1617186994930', {})]), ('add', '', [('item_1617186994930', {})]), ('add', 'item_1617186994930', [('attribute_name', 'Number of Pages')]), ('add', 'item_1617186994930', [('attribute_name', 'Number of Pages')]), ('add', 'item_1617186994930', [('attribute_value_mlt', [])]), ('add', 'item_1617186994930', [('attribute_value_mlt', [])]), ('add', 'item_1617186994930.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186994930.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186994930', 'attribute_value_mlt', 0], [('subitem_1551256248092', '12')]), ('add', ['item_1617186994930', 'attribute_value_mlt', 0], [('subitem_1551256248092', '12')]), ('add', '', [('item_1617187024783', {})]), ('add', '', [('item_1617187024783', {})]), ('add', 'item_1617187024783', [('attribute_name', 'Page Start')]), ('add', 'item_1617187024783', [('attribute_name', 'Page Start')]), ('add', 'item_1617187024783', [('attribute_value_mlt', [])]), ('add', 'item_1617187024783', [('attribute_value_mlt', [])]), ('add', 'item_1617187024783.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187024783.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187024783', 'attribute_value_mlt', 0], [('subitem_1551256198917', '1')]), ('add', ['item_1617187024783', 'attribute_value_mlt', 0], [('subitem_1551256198917', '1')]), ('add', '', [('item_1617187045071', {})]), ('add', '', [('item_1617187045071', {})]), ('add', 'item_1617187045071', [('attribute_name', 'Page End')]), ('add', 'item_1617187045071', [('attribute_name', 'Page End')]), ('add', 'item_1617187045071', [('attribute_value_mlt', [])]), ('add', 'item_1617187045071', [('attribute_value_mlt', [])]), ('add', 'item_1617187045071.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187045071.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187045071', 'attribute_value_mlt', 0], [('subitem_1551256185532', '3')]), ('add', ['item_1617187045071', 'attribute_value_mlt', 0], [('subitem_1551256185532', '3')]), ('add', '', [('item_1617187112279', {})]), ('add', '', [('item_1617187112279', {})]), ('add', 'item_1617187112279', [('attribute_name', 'Degree Name')]), ('add', 'item_1617187112279', [('attribute_name', 'Degree Name')]), ('add', 'item_1617187112279', [('attribute_value_mlt', [])]), ('add', 'item_1617187112279', [('attribute_value_mlt', [])]), ('add', 'item_1617187112279.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187112279.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256126428', 'Degree Name')]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256126428', 'Degree Name')]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256129013', 'en')]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256129013', 'en')]), ('add', '', [('item_1617187136212', {})]), ('add', '', [('item_1617187136212', {})]), ('add', 'item_1617187136212', [('attribute_name', 'Date Granted')]), ('add', 'item_1617187136212', [('attribute_name', 'Date Granted')]), ('add', 'item_1617187136212', [('attribute_value_mlt', [])]), ('add', 'item_1617187136212', [('attribute_value_mlt', [])]), ('add', 'item_1617187136212.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187136212.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187136212', 'attribute_value_mlt', 0], [('subitem_1551256096004', '2021-06-30')]), ('add', ['item_1617187136212', 'attribute_value_mlt', 0], [('subitem_1551256096004', '2021-06-30')]), ('add', '', [('item_1617187187528', {})]), ('add', '', [('item_1617187187528', {})]), ('add', 'item_1617187187528', [('attribute_name', 'Conference')]), ('add', 'item_1617187187528', [('attribute_name', 'Conference')]), ('add', 'item_1617187187528', [('attribute_value_mlt', [])]), ('add', 'item_1617187187528', [('attribute_value_mlt', [])]), ('add', 'item_1617187187528.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187187528.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711633003', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711633003', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711636923', 'Conference Name')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711636923', 'Conference Name')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711645590', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711645590', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711655652', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711655652', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711660052', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711660052', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711680082', 'Sponsor')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711680082', 'Sponsor')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711686511', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711686511', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711699392', {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711699392', {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711704251', '2020/12/11')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711704251', '2020/12/11')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711712451', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711712451', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711727603', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711727603', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711731891', '2000')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711731891', '2000')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711735410', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711735410', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711739022', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711739022', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711743722', '2020')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711743722', '2020')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711745532', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711745532', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711758470', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711758470', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711769260', 'Conference Venue')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711769260', 'Conference Venue')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711775943', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711775943', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711788485', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711788485', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711798761', 'Conference Place')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711798761', 'Conference Place')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711803382', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711803382', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711813532', 'JPN')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711813532', 'JPN')]), ('add', '', [('item_1617258105262', {})]), ('add', '', [('item_1617258105262', {})]), ('add', 'item_1617258105262', [('attribute_name', 'Resource Type')]), ('add', 'item_1617258105262', [('attribute_name', 'Resource Type')]), ('add', 'item_1617258105262', [('attribute_value_mlt', [])]), ('add', 'item_1617258105262', [('attribute_value_mlt', [])]), ('add', 'item_1617258105262.attribute_value_mlt', [(0, {})]), ('add', 'item_1617258105262.attribute_value_mlt', [(0, {})]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourcetype', 'conference paper')]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourcetype', 'conference paper')]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourceuri', 'http://purl.org/coar/resource_type/c_5794')]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourceuri', 'http://purl.org/coar/resource_type/c_5794')]), ('add', '', [('item_1617265215918', {})]), ('add', '', [('item_1617265215918', {})]), ('add', 'item_1617265215918', [('attribute_name', 'Version Type')]), ('add', 'item_1617265215918', [('attribute_name', 'Version Type')]), ('add', 'item_1617265215918', [('attribute_value_mlt', [])]), ('add', 'item_1617265215918', [('attribute_value_mlt', [])]), ('add', 'item_1617265215918.attribute_value_mlt', [(0, {})]), ('add', 'item_1617265215918.attribute_value_mlt', [(0, {})]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1522305645492', 'AO')]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1522305645492', 'AO')]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1600292170262', 'http://purl.org/coar/version/c_b1a7d7d4d402bcce')]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1600292170262', 'http://purl.org/coar/version/c_b1a7d7d4d402bcce')]), ('add', '', [('item_1617349709064', {})]), ('add', '', [('item_1617349709064', {})]), ('add', 'item_1617349709064', [('attribute_name', 'Contributor')]), ('add', 'item_1617349709064', [('attribute_name', 'Contributor')]), ('add', 'item_1617349709064', [('attribute_value_mlt', [])]), ('add', 'item_1617349709064', [('attribute_value_mlt', [])]), ('add', 'item_1617349709064.attribute_value_mlt', [(0, {})]), ('add', 'item_1617349709064.attribute_value_mlt', [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorMails', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorMails', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails', 0], [('contributorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails', 0], [('contributorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('contributorName', '情報, 太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('contributorName', '情報, 太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('lang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('lang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('contributorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('contributorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('lang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('lang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('contributorName', 'Joho, Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('contributorName', 'Joho, Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('lang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('lang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorType', 'ContactPerson')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorType', 'ContactPerson')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', '', [('item_1617349808926', {})]), ('add', '', [('item_1617349808926', {})]), ('add', 'item_1617349808926', [('attribute_name', 'Version')]), ('add', 'item_1617349808926', [('attribute_name', 'Version')]), ('add', 'item_1617349808926', [('attribute_value_mlt', [])]), ('add', 'item_1617349808926', [('attribute_value_mlt', [])]), ('add', 'item_1617349808926.attribute_value_mlt', [(0, {})]), ('add', 'item_1617349808926.attribute_value_mlt', [(0, {})]), ('add', ['item_1617349808926', 'attribute_value_mlt', 0], [('subitem_1523263171732', 'Version')]), ('add', ['item_1617349808926', 'attribute_value_mlt', 0], [('subitem_1523263171732', 'Version')]), ('add', '', [('item_1617351524846', {})]), ('add', '', [('item_1617351524846', {})]), ('add', 'item_1617351524846', [('attribute_name', 'APC')]), ('add', 'item_1617351524846', [('attribute_name', 'APC')]), ('add', 'item_1617351524846', [('attribute_value_mlt', [])]), ('add', 'item_1617351524846', [('attribute_value_mlt', [])]), ('add', 'item_1617351524846.attribute_value_mlt', [(0, {})]), ('add', 'item_1617351524846.attribute_value_mlt', [(0, {})]), ('add', ['item_1617351524846', 'attribute_value_mlt', 0], [('subitem_1523260933860', 'Unknown')]), ('add', ['item_1617351524846', 'attribute_value_mlt', 0], [('subitem_1523260933860', 'Unknown')]), ('add', '', [('item_1617353299429', {})]), ('add', '', [('item_1617353299429', {})]), ('add', 'item_1617353299429', [('attribute_name', 'Relation')]), ('add', 'item_1617353299429', [('attribute_name', 'Relation')]), ('add', 'item_1617353299429', [('attribute_value_mlt', [])]), ('add', 'item_1617353299429', [('attribute_value_mlt', [])]), ('add', 'item_1617353299429.attribute_value_mlt', [(0, {})]), ('add', 'item_1617353299429.attribute_value_mlt', [(0, {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306207484', 'isVersionOf')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306207484', 'isVersionOf')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306287251', {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306287251', {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306382014', 'arXiv')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306382014', 'arXiv')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306436033', 'xxxxx')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306436033', 'xxxxx')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1523320863692', [])]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1523320863692', [])]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692'], [(0, {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692'], [(0, {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320867455', 'en')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320867455', 'en')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320909613', 'Related Title')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320909613', 'Related Title')]), ('add', '', [('item_1617605131499', {})]), ('add', '', [('item_1617605131499', {})]), ('add', 'item_1617605131499', [('attribute_name', 'File')]), ('add', 'item_1617605131499', [('attribute_name', 'File')]), ('add', 'item_1617605131499', [('attribute_type', 'file')]), ('add', 'item_1617605131499', [('attribute_type', 'file')]), ('add', 'item_1617605131499', [('attribute_value_mlt', [])]), ('add', 'item_1617605131499', [('attribute_value_mlt', [])]), ('add', 'item_1617605131499.attribute_value_mlt', [(0, {})]), ('add', 'item_1617605131499.attribute_value_mlt', [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('accessrole', 'open_access')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('accessrole', 'open_access')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('date', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('date', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateType', 'Available')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateType', 'Available')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateValue', '2021-07-12')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateValue', '2021-07-12')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('displaytype', 'simple')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('displaytype', 'simple')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filename', '1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filename', '1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filesize', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filesize', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize', 0], [('value', '1 KB')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize', 0], [('value', '1 KB')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('format', 'text/plain')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('format', 'text/plain')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('mimetype', 'application/pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('mimetype', 'application/pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('url', {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('url', {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'url'], [('url', 'https://weko3.example.org/record/13/files/1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'url'], [('url', 'https://weko3.example.org/record/13/files/1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('version_id', '7cdce099-fe63-445f-b78b-cf2909a8163f')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('version_id', '7cdce099-fe63-445f-b78b-cf2909a8163f')]), ('add', '', [('item_1617610673286', {})]), ('add', '', [('item_1617610673286', {})]), ('add', 'item_1617610673286', [('attribute_name', 'Rights Holder')]), ('add', 'item_1617610673286', [('attribute_name', 'Rights Holder')]), ('add', 'item_1617610673286', [('attribute_value_mlt', [])]), ('add', 'item_1617610673286', [('attribute_value_mlt', [])]), ('add', 'item_1617610673286.attribute_value_mlt', [(0, {})]), ('add', 'item_1617610673286.attribute_value_mlt', [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxx')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxx')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('rightHolderNames', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('rightHolderNames', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderLanguage', 'ja')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderLanguage', 'ja')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderName', 'Right Holder Name')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderName', 'Right Holder Name')]), ('add', '', [('item_1617620223087', {})]), ('add', '', [('item_1617620223087', {})]), ('add', 'item_1617620223087', [('attribute_name', 'Heading')]), ('add', 'item_1617620223087', [('attribute_name', 'Heading')]), ('add', 'item_1617620223087', [('attribute_value_mlt', [])]), ('add', 'item_1617620223087', [('attribute_value_mlt', [])]), ('add', 'item_1617620223087.attribute_value_mlt', [(0, {})]), ('add', 'item_1617620223087.attribute_value_mlt', [(0, {})]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671149650', 'ja')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671149650', 'ja')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671178623', 'Subheading')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671178623', 'Subheading')]), ('add', 'item_1617620223087.attribute_value_mlt', [(1, {})]), ('add', 'item_1617620223087.attribute_value_mlt', [(1, {})]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671149650', 'en')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671149650', 'en')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671178623', 'Subheding')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671178623', 'Subheding')]), ('add', '', [('item_1617944105607', {})]), ('add', '', [('item_1617944105607', {})]), ('add', 'item_1617944105607', [('attribute_name', 'Degree Grantor')]), ('add', 'item_1617944105607', [('attribute_name', 'Degree Grantor')]), ('add', 'item_1617944105607', [('attribute_value_mlt', [])]), ('add', 'item_1617944105607', [('attribute_value_mlt', [])]), ('add', 'item_1617944105607.attribute_value_mlt', [(0, {})]), ('add', 'item_1617944105607.attribute_value_mlt', [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256015892', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256015892', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256027296', 'xxxxxx')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256027296', 'xxxxxx')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256029891', 'kakenhi')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256029891', 'kakenhi')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256037922', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256037922', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256042287', 'Degree Grantor Name')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256042287', 'Degree Grantor Name')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256047619', 'en')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256047619', 'en')]), ('add', '', [('item_title', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', '', [('item_title', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', '', [('item_type_id', '15')]), ('add', '', [('item_type_id', '15')]), ('add', '', [('owner', '1')]), ('add', '', [('owner', '1')]), ('add', '', [('path', [])]), ('add', '', [('path', [])]), ('add', 'path', [(0, '1661517684078')]), ('add', 'path', [(0, '1661517684078')]), ('add', '', [('pubdate', {})]), ('add', '', [('pubdate', {})]), ('add', 'pubdate', [('attribute_name', 'PubDate')]), ('add', 'pubdate', [('attribute_name', 'PubDate')]), ('add', 'pubdate', [('attribute_value', '2021-08-06')]), ('add', 'pubdate', [('attribute_value', '2021-08-06')]), ('add', '', [('publish_date', '2021-08-06')]), ('add', '', [('publish_date', '2021-08-06')]), ('add', '', [('publish_status', '0')]), ('add', '', [('publish_status', '0')]), ('add', '', [('relation_version_is_last', True)]), ('add', '', [('relation_version_is_last', True)]), ('add', '', [('title', [])]), ('add', '', [('title', [])]), ('add', 'title', [(0, 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', 'title', [(0, 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', '', [('weko_shared_id', -1)]), ('add', '', [('weko_shared_id', -1)]), ('remove', '', [('test_1', "")]), ('remove', '', [('test_2', "")])]
                # distination = {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, 'test_1': {'key1': 'value1'}, 'test_2': [{'key2': 'value2'}]}
                # ret = dep._patch(diff_result,distination)
                # assert ret=={'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '688f2d41-be61-468f-95e2-a06abefdaf60'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, '_oai': {'id': 'oai:weko3.example.org:00000013', 'sets': ['1661517684078', '1661517684078']}, 'author_link': ['4', '4'], 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}, {}, {}]}, 'item_1617186385884': {'attribute_name': 'Alternative Title', 'attribute_value_mlt': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}, {}, {}]}, 'item_1617186419668': {'attribute_name': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}, {}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}, {}]}, {}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}, {}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {}, {}, {}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}, {}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}, {}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {}, {}, {}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}, {}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {}, {}, {}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}]}, {}, {}, {}]}, 'item_1617186476635': {'attribute_name': 'Access Rights', 'attribute_value_mlt': [{'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, {}]}, 'item_1617186499011': {'attribute_name': 'Rights', 'attribute_value_mlt': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}, {}]}, 'item_1617186609386': {'attribute_name': 'Subject', 'attribute_value_mlt': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}, {}]}, 'item_1617186626617': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}, {}, {}]}, 'item_1617186643794': {'attribute_name': 'Publisher', 'attribute_value_mlt': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}, {}]}, 'item_1617186660861': {'attribute_name': 'Date', 'attribute_value_mlt': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}, {}]}, 'item_1617186702042': {'attribute_name': 'Language', 'attribute_value_mlt': [{'subitem_1551255818386': 'jpn'}, {}]}, 'item_1617186783814': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}, {}]}, 'item_1617186859717': {'attribute_name': 'Temporal', 'attribute_value_mlt': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}, {}]}, 'item_1617186882738': {'attribute_name': 'Geo Location', 'attribute_value_mlt': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}, {}]}, {}]}, 'item_1617186901218': {'attribute_name': 'Funding Reference', 'attribute_value_mlt': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}, {}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}, {}]}, {}]}, 'item_1617186920753': {'attribute_name': 'Source Identifier', 'attribute_value_mlt': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}, {}]}, 'item_1617186941041': {'attribute_name': 'Source Title', 'attribute_value_mlt': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}, {}]}, 'item_1617186959569': {'attribute_name': 'Volume Number', 'attribute_value_mlt': [{'subitem_1551256328147': '1'}, {}]}, 'item_1617186981471': {'attribute_name': 'Issue Number', 'attribute_value_mlt': [{'subitem_1551256294723': '111'}, {}]}, 'item_1617186994930': {'attribute_name': 'Number of Pages', 'attribute_value_mlt': [{'subitem_1551256248092': '12'}, {}]}, 'item_1617187024783': {'attribute_name': 'Page Start', 'attribute_value_mlt': [{'subitem_1551256198917': '1'}, {}]}, 'item_1617187045071': {'attribute_name': 'Page End', 'attribute_value_mlt': [{'subitem_1551256185532': '3'}, {}]}, 'item_1617187112279': {'attribute_name': 'Degree Name', 'attribute_value_mlt': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}, {}]}, 'item_1617187136212': {'attribute_name': 'Date Granted', 'attribute_value_mlt': [{'subitem_1551256096004': '2021-06-30'}, {}]}, 'item_1617187187528': {'attribute_name': 'Conference', 'attribute_value_mlt': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}, {}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}, {}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}, {}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}, {}], 'subitem_1599711813532': 'JPN'}, {}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, {}]}, 'item_1617265215918': {'attribute_name': 'Version Type', 'attribute_value_mlt': [{'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, {}]}, 'item_1617349709064': {'attribute_name': 'Contributor', 'attribute_value_mlt': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}, {}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}, {}, {}, {}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}]}, {}]}, 'item_1617349808926': {'attribute_name': 'Version', 'attribute_value_mlt': [{'subitem_1523263171732': 'Version'}, {}]}, 'item_1617351524846': {'attribute_name': 'APC', 'attribute_value_mlt': [{'subitem_1523260933860': 'Unknown'}, {}]}, 'item_1617353299429': {'attribute_name': 'Relation', 'attribute_value_mlt': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}, {}]}, {}]}, 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}, {}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}, {}], 'format': 'text/plain', 'mimetype': 'application/pdf', 'url': {'url': 'https://weko3.example.org/record/13/files/1KB.pdf'}, 'version_id': '7cdce099-fe63-445f-b78b-cf2909a8163f'}, {}]}, 'item_1617610673286': {'attribute_name': 'Rights Holder', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}, {}]}, {}]}, 'item_1617620223087': {'attribute_name': 'Heading', 'attribute_value_mlt': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}, {}, {}]}, 'item_1617944105607': {'attribute_name': 'Degree Grantor', 'attribute_value_mlt': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}, {}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}, {}]}, {}]}, 'item_title': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'item_type_id': '15', 'owner': '1', 'path': ['1661517684078', '1661517684078'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2021-08-06'}, 'publish_date': '2021-08-06', 'publish_status': '0', 'relation_version_is_last': True, 'title': ['ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)'], 'weko_shared_id': -1}

                distination = {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, '_oai': {'sets1':{1,2,3}, 'sets2':{1,2,3,4,5,6}}, 'test_1': {"dict":{"key1":"value1","key2":"value2"},"list":[1,2,3,4],"str":"test_str"},"test_list":[1]}
                diff_result = [
                    ("add", "_oai.sets1",[("",{3,4,5})]), # dest is set
                    ("change", "test_list.0", ("",2)), # dest is list
                    ("remove", "_oai.sets2",[("",{3,4,5})]), # dest is set
                    ("remove", "test_1.list",[(1,"")]),
                    ("remove", "test_1.str",[("key2","")])
                ]
                ret = dep._patch(diff_result,distination,True)
                assert ret == {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, '_oai': {'sets1':{1,2,3,4,5}, 'sets2':{1,2,6}}, 'test_1': {"dict":{"key1":"value1","key2":"value2"},"list":[1,3,4],"str":"test_str"},"test_list":[2]}

                # todo4
                dep = WekoDeposit.create({})
                distination = {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, 'test_1': {"dict":{"name":"Alice","age":"30"}}}
                diff_result = [
                    ("remove", "test_1.dict",[('name', 'Alice'), ('age', 30)]), # dest is dict
                ]
                ret = dep._patch(diff_result,distination,True)
                assert ret == {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, 'test_1': {"dict":{}}}

                dep = WekoDeposit.create({})
                distination = {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, '_oai': {'sets1':{1,2,3}, 'sets2':{1,2,3,4,5,6}}, 'test_1': {"dict":{"key1":"value1","key2":"value2"},"list":[1,2,3,4],"str":"test_str"},"test_list":[1]}
                diff_result = [
                    ("add", "_oai.sets1",[("",{3,4,5})]), # dest is set
                ]
                ret = dep._patch(diff_result,distination,False)
                assert ret == {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, '_oai': {'sets1':{1,2,3,4,5}, 'sets2':{1,2,3,4,5,6}}, 'test_1': {"dict":{"key1":"value1","key2":"value2"},"list":[1,2,3,4],"str":"test_str"},"test_list":[1]}

                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

    # def add(node, changes):
    # def change(node, changes):
    # def remove(node, changes):
    
    # def _publish_new(self, id_=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__publish_new -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__publish_new(self,app,location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                dep = WekoDeposit.create({})
                record=dep._publish_new()
                from invenio_records_files.api import Record
                assert isinstance(record,Record)==True
            
                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()
           

    # def _update_version_id(self, metas, bucket_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__update_version_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__update_version_id(self,app,location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                dep = WekoDeposit.create({})
                bucket = Bucket.create(location)
                ret = dep._update_version_id({},bucket.id)
                assert ret==False
                i = 1
                meta =  {"_oai": {"id": "oai:weko3.example.org:000000{:02d}".format(i), "sets": ["{}".format((i % 2) + 1)]}, "path": ["{}".format((i % 2) + 1)], "owner": "1", "recid": "{}".format(i), "title": ["title"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-08-20"}, "_buckets": {"deposit": "3e99cfca-098b-42ed-b8a0-20ddd09b3e02"}, "_deposit": {"id": "{}".format(i), "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0}, "owner": "1", "owners": [1], "status": "draft", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}}, "item_title": "title", "author_link": [], "item_type_id": "1", "publish_date": "2022-08-20", "publish_status": "0", "weko_shared_id": -1, "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": "title", "subitem_1551255648112": "ja"}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}]}, "relation_version_is_last": True, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [
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
                ret = dep._update_version_id(meta,bucket.id)
                assert ret==True

                i = 1
                meta =  {"_oai": {"id": "oai:weko3.example.org:000000{:02d}".format(i), "sets": ["{}".format((i % 2) + 1)]}, "path": ["{}".format((i % 2) + 1)], "owner": "1", "recid": "{}".format(i), "title": ["title"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-08-20"}, "_buckets": {"deposit": "3e99cfca-098b-42ed-b8a0-20ddd09b3e02"}, "_deposit": {"id": "{}".format(i), "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0}, "owner": "1", "owners": [1], "status": "draft", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}}, "item_title": "title", "author_link": [], "item_type_id": "1", "publish_date": "2022-08-20", "publish_status": "0", "weko_shared_id": -1, "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": "title", "subitem_1551255648112": "ja"}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}]}, "relation_version_is_last": True, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt":
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
                    }}
                ret = dep._update_version_id(meta,bucket.id)
                assert ret==True

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def publish(self, pid=None, id_=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_publish(self,app,location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            deposit = WekoDeposit.create({})
            assert deposit['_deposit']['id']
            assert 'draft' == deposit.status
            assert 0 == deposit.revision_id
            deposit.publish()
            assert 'published' == deposit.status
            assert deposit.revision_id==2

            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def publish_without_commit(self, pid=None, id_=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_publish_without_commit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_publish_without_commit(self,app,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
                
                # テストケース1
                # deposit['recid']='2'
                deposit = WekoDeposit.create({})
                assert deposit['_deposit']['id']
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                deposit.publish_without_commit()
                assert deposit['_deposit']['id']
                assert 'published' == deposit.status
                assert deposit.revision_id == 2

                # テストケース2
                deposit = WekoDeposit.create({})
                assert deposit['_deposit']['id']
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                
                # self.data を None に設定
                deposit.data = None

                indexer, records = es_records
                deposit["$schema"] = "https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"
                deposit["control_number"] = "1"
                deposit.publish_without_commit()
                assert deposit['_deposit']['id']
                assert 'published' == deposit.status
                assert deposit.revision_id == 2
                assert deposit.data is not None 

                # テストケース3
                deposit = WekoDeposit.create({})
                assert deposit['_deposit']['id']
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                
                indexer, records = es_records
                deposit = records[1]["deposit"]
                deposit["$schema"] = None
                deposit["control_number"] = "1"
                deposit.publish_without_commit()
                assert deposit['_deposit']['id']
                assert 'published' == deposit.status
                assert deposit.revision_id == 2
                assert deposit["$schema"] is not None 

                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

    # def create(cls, data, id_=None, recid=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_create(sel,app,client,db,location,users,db_activity):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                deposit = WekoDeposit.create({})
                assert isinstance(deposit,WekoDeposit)
                assert deposit['_deposit']['id']=="1"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                id = uuid.uuid4()
                deposit = WekoDeposit.create({},id_=id)
                assert isinstance(deposit,WekoDeposit)
                assert deposit['_deposit']['id']=="2"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id

                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

            #login(app,client,obj=users[2]["obj"])
            with app.test_request_context():
                login_user(users[2]["obj"])
                session["activity_info"] = {"activity_id":db_activity[0].activity_id}
                data = {"$schema":"https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"}
                id = uuid.uuid4()
                deposit = WekoDeposit.create(data,id_=id)
                assert isinstance(deposit,WekoDeposit)
                assert deposit['_deposit']['id']=="3"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                
                with patch("weko_deposit.api.PersistentIdentifier.create",side_effect=BaseException("test_error")):
                    session["activity_info"] = {"activity_id":db_activity[1].activity_id}
                    data = {"$schema":"https://127.0.0.1/schema/deposits/deposit-v1.0.0.json","_deposit":{"id":"2","owners":[1],"status":"draft","created_by":1}}
                    id = uuid.uuid4()
                    with pytest.raises(BaseException):
                        deposit = WekoDeposit.create(data,id_=id)

                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
                mock_logger.reset_mock()

    # def update(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update(sel,app,db,location,db_index):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                deposit = WekoDeposit.create({})
                assert deposit['_deposit']['id']=="1"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                deposit.update()
                assert deposit['_deposit']['id']=="1"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id

                # todo6
                # deposit = WekoDeposit.create({})
                # assert deposit['_deposit']['id']=="2"
                # assert 'draft' == deposit.status
                # assert 0 == deposit.revision_id
                # deposit.update({'url': "https://test1"})
                # assert deposit['_deposit']['id']=="2"
                # assert 'draft' == deposit.status
                # assert 0 == deposit.revision_id
                # todo6
                #deposit = WekoDeposit.create({})
                # index_obj = {'index': '2', 'actions': 'private'}
                index_obj = {'index': '2'}
                data = {'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                deposit = WekoDeposit.create(data)
                deposit.update(index_obj)
                # deposit.update({'actions': 'publish', 'index': '0', })
                assert deposit['_deposit']['id']=="2"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id

                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.reset_mock()

    # def clear(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_clear -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_clear(sel,app,db,location,es_records_1):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records_1
            record = records[0]
            deposit = record['deposit']
            deposit['_deposit']['status'] = 'draft'
            es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
            ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
            deposit.clear()
            ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
            assert ret==ret2

            indexer, records = es_records_1
            record = records[1]
            deposit = record['deposit']
            es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
            ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
            deposit.clear()  
            ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
            assert ret==ret2          
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.reset_mock()

    # def delete(self, force=True, pid=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete(sel,app,db,location,es_records_1):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records_1
            record = records[0]
            deposit = record['deposit']
            es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
            ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
            deposit.delete()
            ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id,ignore = [404])
            assert ret2=={'error': {'root_cause': [{'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(deposit.id)}], 'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(deposit.id)}, 'status': 404}

            record = records[1]
            deposit = record['deposit']
            es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
            ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
            deposit.pid
            deposit.delete()
            ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id,ignore = [404])
            assert ret2=={'error': {'root_cause': [{'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(deposit.id)}], 'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(deposit.id)}, 'status': 404}

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def commit(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_commit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_commit(sel,app,db,location, db_index, db_activity, db_itemtype,bucket):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            with app.test_request_context():
                deposit = WekoDeposit.create({})
                assert deposit['_deposit']['id']=="1"
                assert 'draft' == deposit.status
                assert 0 == deposit.revision_id
                deposit.commit()
                assert deposit['_deposit']['id']=="1"
                assert 'draft' == deposit.status
                assert 2 == deposit.revision_id

                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.reset_mock()

                # exist feedback_mail_list
                deposit = WekoDeposit.create({})
                item_id = deposit.pid.object_uuid
                index_obj = {'index': ['1'], 'actions': 'private'}
                data = {'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                deposit.update(index_obj,data)
                FeedbackMailList.update(item_id,[{"email":"test.taro@test.org","author_id":"1"}])
                db.session.commit()
                deposit.commit()
                es_data = deposit.indexer.get_metadata_by_item_id(item_id)
                assert es_data["_source"]["feedback_mail_list"] == [{"email":"test.taro@test.org","author_id":"1"}]

                mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
                mock_logger.reset_mock()
    
                # not exist feedback_mail_list
                FeedbackMailList.delete(item_id)
                deposit.commit()
                es_data = deposit.indexer.get_metadata_by_item_id(item_id)
                assert es_data["_source"]["feedback_mail_list"] == []
                mockjrc = {'title': ['test'], 'type': ['conference paper'], 'control_number': '2', '_oai': {'id': '2'}, '_item_metadata': OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2023-12-07'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]}), ('item_title', 'test'), ('item_type_id', '1'), ('control_number', '2'), ('author_link', []), ('_oai', {'id': '2'}), ('publish_date', '2023-12-07'), ('title', ['test']), ('relation_version_is_last', True), ('path', ['1']), ('publish_status', '2')]), 'itemtype': 'テストアイテムタイプ', 'publish_date': '2023-12-07', 'author_link': [], 'path': ['1'], 'publish_status': '2','content':'123123123'}
                # activity_info
                deposit = WekoDeposit.create({})
                item_id = deposit.pid.object_uuid
                index_obj = {'content':{'content':'content'}, 'index': ['2'], 'actions': 'private'}
                data = {'content':{'content':'content'}, 'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                deposit.update(index_obj,data)
                FeedbackMailList.update(item_id,[{"email":"test.taro@test.org","author_id":"1"}])
                session["activity_info"] = {
                "activity_id": "2",
                "action_id": 1,
                "action_version": "1.0.1",
                "action_status": "M",
                "commond": "",
                }
                # db.session.merge(bucket)
                deposit['content']={'content':'content'}
                db.session.commit()
                deposit.commit()
                es_data = deposit.indexer.get_metadata_by_item_id(item_id)
                assert es_data["_source"]["feedback_mail_list"] == [{"email":"test.taro@test.org","author_id":"1"}]

                # workflow_storage_location != None
                deposit = WekoDeposit.create({})
                item_id = deposit.pid.object_uuid
                index_obj = {'index': ['3'], 'actions': 'private',"content":[{"test":"content"},{"file":"test"}]}
                # data = {'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                data = {"content":[{"test":"content"},{"file":"test"}],'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                #deposit['_buckets']['deposit'] = "3e99cfca-098b-42ed-b8a0-20ddd09b3e01"
                deposit.update(index_obj,data)
                FeedbackMailList.update(item_id,[{"email":"test.taro@test.org","author_id":"1"}])
                session["activity_info"] = {
                    "activity_id": "2",
                    "action_id": 1,
                    "action_version": "1.0.1",
                    "action_status": "M",
                    "commond": "",
                }
                
                import tempfile
                from invenio_files_rest.models import Bucket, Location, ObjectVersion
                import shutil             
                tmppath1 = tempfile.mkdtemp()
                # loc = Location(id="2",name="testloc1", uri=tmppath1, default=True)
                loc1 = Location(name="testloc1", uri=tmppath1, default=True)
                db.session.add(loc1)

                db.session.commit()
                bucket2 = Bucket.create(loc1)
                #bucket2.id="3e99cfca-098b-42ed-b8a0-20ddd09b3e00"
                db.session.merge(bucket2)
                db.session.commit()
                # db.session.merge(bucket)
                print(999)
                print(bucket2)
                deposit['_buckets']['deposit']=str(bucket2.id)
                deposit.commit()
                es_data = deposit.indexer.get_metadata_by_item_id(item_id)
                assert es_data["_source"]["feedback_mail_list"] == [{"email":"test.taro@test.org","author_id":"1"}]
                shutil.rmtree(tmppath1)
                from elasticsearch.exceptions import ElasticsearchException
                from weko_deposit.errors import WekoDepositError
                with patch("weko_deposit.api.WekoIndexer.upload_metadata", side_effect=ElasticsearchException("test_error")):
                    deposit.commit()

                # self.jrc.get('content')
                deposit = WekoDeposit.create({})
                # indexer, records = es_records
                # record = records[0]
                # deposit = record['deposit']
                item_id = deposit.pid.object_uuid
                index_obj = {'index': ['3'], 'actions': 'private',"content":[{"test":"content"},{"file":"test"}]}
                # data = {'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                # data = {"content":[{"test":"content"},{"file":"test"}],'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja',"content":[{"test":"content"},{"file":"test"}]}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
                #deposit['_buckets']['deposit'] = "3e99cfca-098b-42ed-b8a0-20ddd09b3e01"
                deposit['item_1617605131499'] = {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'url': {'url': 'https://weko3.example.org/record/{}/files/hello.txt'.format(1)}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-07'}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_access', 'version_id': '', 'mimetype': 'application/pdf',"file": "",}]}
                data = {'pubdate': '2023-12-07', "item_1617605131499":{'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'url': {'url': 'https://weko3.example.org/record/{}/files/hello.txt'.format(1)}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-07'}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_access', 'version_id': '', 'mimetype': 'application/pdf',"file": "",}]}, '$schema': '/items/jsonschema/1'}
                deposit.update(index_obj,data)
                FeedbackMailList.update(item_id,[{"email":"test.taro@test.org","author_id":"1"}])
                session["activity_info"] = {
                    "activity_id": "2",
                    "action_id": 1,
                    "action_version": "1.0.1",
                    "action_status": "M",
                    "commond": "",
                }

                deposit.commit()

                from weko_deposit.errors import WekoDepositError
                # with patch("weko_deposit.api.WekoIndexer.upload_metadata", side_effect=ElasticsearchException("test_error")):
                #     with pytest.raises(WekoDepositError):
                #         deposit.commit()

                with patch("weko_deposit.api.WekoIndexer.upload_metadata", side_effect=Exception("test_error")):
                    with pytest.raises(WekoDepositError):
                        deposit.commit()  


    # def newversion(self, pid=None, is_draft=False):
    #             # NOTE: We call the superclass `create()` method, because
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_newversion -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_newversion(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            with patch("weko_deposit.api.WekoDeposit.is_published",return_value=None):
                with pytest.raises(PIDInvalidAction):
                    ret = deposit.newversion()

            with pytest.raises(AttributeError):
                ret = deposit.newversion()
        
            ret = deposit.newversion(deposit.pid,True)
            assert ret==None

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            ret = deposit.newversion(deposit.pid)
            assert ret==None

            record2 = records[1]
            pid2 = record2["recid"]
            pid2.status = "K"
            db.session.merge(pid2)
            db.session.commit()
            from weko_deposit.errors import WekoDepositError
            with pytest.raises(WekoDepositError):
                ret = deposit.newversion(pid2)

            record = records[2]
            deposit = record['deposit']
            pid = record["recid"]
            ret = deposit.newversion(pid,True)
            assert ret is not None

            record = records[3]
            deposit = record['deposit']
            pid = record["recid"]
            ret = deposit.newversion(pid,False)
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
            ret = deposit.newversion(pid,False)
            assert ret is not None

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
        
    # def get_content_files(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_get_content_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_content_files(sel,app,db,location,es_records_1):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records_1
            record = records[0]
            deposit = record['deposit']
            ret = deposit.get_content_files()
            assert ret==None
            # todo11
            record = records[1]
            deposit = record['deposit']
            ret = deposit.get_content_files()
            assert ret==None
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def get_file_data(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_get_file_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_file_data(sel,app,db,location,es_records_1):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records_1
            record = records[0]
            deposit = record['deposit']
            ret = deposit.get_file_data()
            assert ret == [{'filename': 'hello.txt', 'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)           
            mock_logger.reset_mock()

    # def save_or_update_item_metadata(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_save_or_update_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_save_or_update_item_metadata(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            print(999)
            print(deposit)
            db.session.commit()
            deposit.save_or_update_item_metadata()
            # todo13
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def delete_old_file_index(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_old_file_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_old_file_index(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            # not is_edit
            deposit.delete_old_file_index()
            # is_edit
            deposit.is_edit=True
            deposit.delete_old_file_index()

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()


    # def delete_item_metadata(self, data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_item_metadata(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            item_data = record['item_data']
            
            deposit.delete_item_metadata(item_data)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_record_data_from_act_temp -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_record_data_from_act_temp(sel,app,db,db_activity,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            _, records = es_records
            
            # not exist pid
            record = records[8]
            pid = record["recid"]
            pid.delete()
            db.session.commit()
            deposit = record["deposit"]
            deposit["recid"]="xxx"
            result = deposit.record_data_from_act_temp()
            assert result == None
       
            # not exist activity
            record = records[0]
            rec_uuid = record["recid"].object_uuid
            deposit=record["deposit"]
            result = deposit.record_data_from_act_temp()
            assert result == None

            # not exist activity.temp_data
            activity = Activity(activity_id='3',workflow_id=1, flow_id=1,
                        item_id=rec_uuid,
                        action_id=1, activity_login_user=1,
                        activity_update_user=1,
                        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
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
            temp_data = {"metainfo": {"pubdate": "2023-10-10", "none_str":"","empty_list":[],"item_1617186331708": [{"subitem_1551255647225": "test_title", "subitem_1551255648112": "ja"}], "item_1617186385884": [{"subitem_1551255720400": "alter title"}], "item_1617186419668": [{"creatorAffiliations": [{"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}], "creatorAlternatives": [{}], "creatorMails": [{}], "creatorNames": [{}], "familyNames": [{"familyName": "test_family_name"}], "givenNames": [{}], "nameIdentifiers": [{}]}], "item_1617186499011": [{}], "item_1617186609386": [{}], "item_1617186626617": [{}], "item_1617186643794": [{}], "item_1617186660861": [{}], "item_1617186702042": [{}], "item_1617186783814": [{}], "item_1617186859717": [{}], "item_1617186882738": [{"subitem_geolocation_place": [{}]}], "item_1617186901218": [{"subitem_1522399412622": [{}], "subitem_1522399651758": [{}]}], "item_1617186920753": [{}], "item_1617186941041": [{}], "item_1617187112279": [{}], "item_1617187187528": [{"subitem_1599711633003": [{}], "subitem_1599711660052": [{}], "subitem_1599711758470": [{}], "subitem_1599711788485": [{}]}], "item_1617349709064": [{"contributorAffiliations": [{"contributorAffiliationNameIdentifiers": [{}], "contributorAffiliationNames": [{}]}], "contributorAlternatives": [{}], "contributorMails": [{}], "contributorNames": [{}], "familyNames": [{}], "givenNames": [{}], "nameIdentifiers": [{}]}], "item_1617353299429": [{"subitem_1523320863692": [{}]}], "item_1617605131499": [{"date": [{}], "fileDate": [{}], "filesize": [{}]}], "item_1617610673286": [{"nameIdentifiers": [{}], "rightHolderNames": [{}]}], "item_1617620223087": [{}], "item_1617944105607": [{"subitem_1551256015892": [{}], "subitem_1551256037922": [{}]}], "item_1617187056579": {"bibliographic_titles": [{}]}, "shared_user_id": -1, "item_1617258105262": {"resourcetype": "conference paper", "resourceuri": "http://purl.org/coar/resource_type/c_5794"}}, "files": [], "endpoints": {"initialization": "/api/deposits/items"}}
            activity.temp_data=json.dumps(temp_data)
            db.session.merge(activity)
            db.session.commit()
            result = deposit.record_data_from_act_temp()
            test = {"pubdate": "2023-10-10","item_1617186331708": [{"subitem_1551255647225": "test_title","subitem_1551255648112": "ja"}],"item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"familyNames": [{"familyName": "test_family_name"}]}],"shared_user_id": -1,"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"},"deleted_items": ["none_str","empty_list","item_1617186499011","item_1617186609386","item_1617186626617","item_1617186643794","item_1617186660861","item_1617186702042","item_1617186783814","item_1617186859717","item_1617186882738","item_1617186901218","item_1617186920753","item_1617186941041","item_1617187112279","item_1617187187528","item_1617349709064","item_1617353299429","item_1617605131499","item_1617610673286","item_1617620223087","item_1617944105607","item_1617187056579"],"$schema": "/items/jsonschema/1","title": "test_title","lang": "ja"}
            assert result == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # title is dict
            temp_data = {"metainfo": {"pubdate": "2023-10-10","none_str": "","empty_list": [],"item_1617186331708": {"subitem_1551255647225": "test_title","subitem_1551255648112": "ja"},"item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"creatorAffiliations": [{"affiliationNameIdentifiers": [{}],"affiliationNames": [{}]}],"creatorAlternatives": [{}],"creatorMails": [{}],"creatorNames": [{}],"familyNames": [{"familyName": "test_family_name"}],"givenNames": [{}],"nameIdentifiers": [{}]}],"item_1617186499011": [{}],"item_1617186609386": [{}],"item_1617186626617": [{}],"item_1617186643794": [{}],"item_1617186660861": [{}],"item_1617186702042": [{}],"item_1617186783814": [{}],"item_1617186859717": [{}],"item_1617186882738": [{"subitem_geolocation_place": [{}]}],"item_1617186901218": [{"subitem_1522399412622": [{}],"subitem_1522399651758": [{}]}],"item_1617186920753": [{}],"item_1617186941041": [{}],"item_1617187112279": [{}],"item_1617187187528": [{"subitem_1599711633003": [{}],"subitem_1599711660052": [{}],"subitem_1599711758470": [{}],"subitem_1599711788485": [{}]}],"item_1617349709064": [{"contributorAffiliations": [{"contributorAffiliationNameIdentifiers": [{}],"contributorAffiliationNames": [{}]}],"contributorAlternatives": [{}],"contributorMails": [{}],"contributorNames": [{}],"familyNames": [{}],"givenNames": [{}],"nameIdentifiers": [{}]}],"item_1617353299429": [{"subitem_1523320863692": [{}]}],"item_1617605131499": [{"date": [{}],"fileDate": [{}],"filesize": [{}]}],"item_1617610673286": [{"nameIdentifiers": [{}],"rightHolderNames": [{}]}],"item_1617620223087": [{}],"item_1617944105607": [{"subitem_1551256015892": [{}],"subitem_1551256037922": [{}]}],"item_1617187056579": {"bibliographic_titles": [{}]},"shared_user_id": -1,"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"}},"files": [],"endpoints": {"initialization": "/api/deposits/items"}}
            activity.temp_data=json.dumps(temp_data)
            db.session.merge(activity)
            db.session.commit()
            result = deposit.record_data_from_act_temp()
            test = {"pubdate": "2023-10-10","item_1617186331708": {"subitem_1551255647225": "test_title","subitem_1551255648112": "ja"},"item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"familyNames": [{"familyName": "test_family_name"}]}],"shared_user_id": -1,"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"},"deleted_items": ["none_str","empty_list","item_1617186499011","item_1617186609386","item_1617186626617","item_1617186643794","item_1617186660861","item_1617186702042","item_1617186783814","item_1617186859717","item_1617186882738","item_1617186901218","item_1617186920753","item_1617186941041","item_1617187112279","item_1617187187528","item_1617349709064","item_1617353299429","item_1617605131499","item_1617610673286","item_1617620223087","item_1617944105607","item_1617187056579"],"$schema": "/items/jsonschema/1","title": "test_title","lang": "ja"}
            assert result == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
        
            # title data is not exist 
            temp_data = {"metainfo": {"pubdate": "2023-10-10","none_str": "","empty_list": [],"item_1617186331708": [],"item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"creatorAffiliations": [{"affiliationNameIdentifiers": [{}],"affiliationNames": [{}]}],"creatorAlternatives": [{}],"creatorMails": [{}],"creatorNames": [{}],"familyNames": [{"familyName": "test_family_name"}],"givenNames": [{}],"nameIdentifiers": [{}]}],"item_1617186499011": [{}],"item_1617186609386": [{}],"item_1617186626617": [{}],"item_1617186643794": [{}],"item_1617186660861": [{}],"item_1617186702042": [{}],"item_1617186783814": [{}],"item_1617186859717": [{}],"item_1617186882738": [{"subitem_geolocation_place": [{}]}],"item_1617186901218": [{"subitem_1522399412622": [{}],"subitem_1522399651758": [{}]}],"item_1617186920753": [{}],"item_1617186941041": [{}],"item_1617187112279": [{}],"item_1617187187528": [{"subitem_1599711633003": [{}],"subitem_1599711660052": [{}],"subitem_1599711758470": [{}],"subitem_1599711788485": [{}]}],"item_1617349709064": [{"contributorAffiliations": [{"contributorAffiliationNameIdentifiers": [{}],"contributorAffiliationNames": [{}]}],"contributorAlternatives": [{}],"contributorMails": [{}],"contributorNames": [{}],"familyNames": [{}],"givenNames": [{}],"nameIdentifiers": [{}]}],"item_1617353299429": [{"subitem_1523320863692": [{}]}],"item_1617605131499": [{"date": [{}],"fileDate": [{}],"filesize": [{}]}],"item_1617610673286": [{"nameIdentifiers": [{}],"rightHolderNames": [{}]}],"item_1617620223087": [{}],"item_1617944105607": [{"subitem_1551256015892": [{}],"subitem_1551256037922": [{}]}],"item_1617187056579": {"bibliographic_titles": [{}]},"shared_user_id": -1,"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"}},"files": [],"endpoints": {"initialization": "/api/deposits/items"}}
            activity.temp_data=json.dumps(temp_data)
            db.session.merge(activity)
            db.session.commit()
            result = deposit.record_data_from_act_temp()
            test = {"pubdate": "2023-10-10","item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"familyNames": [{"familyName": "test_family_name"}]}],"shared_user_id": -1,"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"},"deleted_items": ["none_str","empty_list","item_1617186331708","item_1617186499011","item_1617186609386","item_1617186626617","item_1617186643794","item_1617186660861","item_1617186702042","item_1617186783814","item_1617186859717","item_1617186882738","item_1617186901218","item_1617186920753","item_1617186941041","item_1617187112279","item_1617187187528","item_1617349709064","item_1617353299429","item_1617605131499","item_1617610673286","item_1617620223087","item_1617944105607","item_1617187056579"],"$schema": "/items/jsonschema/1","title": "test_title","lang": ""}
            assert result == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
        
            # not exist title_parent_key in path
            mock_path = {
            "title": {},
            "pubDate": ""
            }
            with patch("weko_items_autofill.utils.get_title_pubdate_path",return_value=mock_path):
                result = deposit.record_data_from_act_temp()
                assert result == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()
            
            # not exist title_value_lst_key, title_lang_lst_key
            mock_path = {
            "title": {
                "title_parent_key": "item_1617186331708",
            },
            "pubDate": ""
            }
            with patch("weko_items_autofill.utils.get_title_pubdate_path",return_value=mock_path):
                result = deposit.record_data_from_act_temp()
                assert result == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def convert_item_metadata(self, index_obj, data=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_convert_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_convert_item_metadata(sel,app,db,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            record_data = record['item_data']
            index_obj = {'index': ['1'], 'actions': '1'}
            test1 = OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}), ('item_title', 'title'), ('item_type_id', '1'), ('control_number', '1'), ('author_link', []), ('_oai', {'id': '1'}), ('publish_date', '2022-08-20'), ('title', ['title']), ('relation_version_is_last', True), ('path', ['1']), ('publish_status','0')])
            test2 = None
            ret1,ret2 = deposit.convert_item_metadata(index_obj,record_data)
            assert ret1 == test1
            assert ret2 == test2

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

            # indexer, records = es_records
            # record = records[1]
            # deposit = record['deposit']
            # record_data = record['item_data']
            # index_obj = {'index': ['1'], 'actions': '1'}
            # test1 = OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}), ('item_title', 'title'), ('item_type_id', '1'), ('control_number', '2'), ('author_link', []), ('_oai', {'id': '2'}), ('publish_date', '2022-08-20'), ('title', ['title']), ('relation_version_is_last', True), ('path', ['1']), ('publish_status','0')])
            # test2 = None
            # ret1,ret2 = deposit.convert_item_metadata(index_obj,record_data)
            # assert ret1 == test1
            # assert ret2 == test2
            # # redis_connection = RedisConnection()
            # # datastore = redis_connection.connection(db=app.config['CACHE_REDIS_DB'], kv = True)
            # # datastore.put(
            # #     app.config['WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(pid_value=recid.pid_value),
            # #     (json.dumps(record)).encode('utf-8'))
            # mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            # mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            # mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            # mock_logger.reset_mock()

            # with patch("weko_deposit.api.RedisConnection.connection",side_effect=BaseException("test_error")):
            #     with pytest.raises(HTTPException) as httperror:
            #         ret = deposit.convert_item_metadata(index_obj,{})
            #         assert httperror.value.code == 500
            #         assert httperror.value.data == "Failed to register item!"

            # with patch("weko_deposit.api.json_loader",side_effect=RuntimeError):
            #     with pytest.raises(RuntimeError):
            #         ret = deposit.convert_item_metadata(index_obj,record_data)
            # with patch("weko_deposit.api.json_loader",side_effect=BaseException("test_error")):
            #     with pytest.raises(HTTPException) as httperror:
            #         ret = deposit.convert_item_metadata(index_obj,record_data)
            #         assert httperror.value.code == 500
            #         assert httperror.value.data == "MAPPING_ERROR"

            with patch("weko_deposit.api.RedisConnection.connection",side_effect=Exception("test_error")):
                with pytest.raises(HTTPException) as httperror:
                    deposit.convert_item_metadata(index_obj,{})
                    mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY, element=mock.ANY)
                    mock_logger.reset_mock()

            with patch("weko_deposit.api.RedisConnection.connection",side_effect=redis.RedisError("test_redis_error")):
                with pytest.raises(HTTPException) as httperror:
                    # ret = deposit.convert_item_metadata(index_obj,{})
                    deposit.convert_item_metadata(index_obj,{})
                    assert httperror.value.code == 500
                    assert httperror.value.data == "Failed to register item!"
                    mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_REDIS', ex=mock.ANY)
                    mock_logger.reset_mock()


            from weko_deposit.errors import WekoDepositError
            with patch("weko_deposit.api.json_loader",side_effect=Exception("")):
                with pytest.raises(Exception) as ex:
                    ret = deposit.convert_item_metadata(index_obj,record_data)
                    assert ex.value.code == 500
                    assert ex.value.data == "MAPPING_ERROR"


            with patch("weko_deposit.api.json_loader",side_effect=RuntimeError("test_redis_error")):
                with pytest.raises(WekoDepositError):
                    ret = deposit.convert_item_metadata(index_obj,record_data)
                    mock_logger.assert_any_call(key='WEKO_DEPOSIT_FAILED_CONVERT_ITEM_METADATA', ex=mock.ANY)
                    mock_logger.reset_mock()   
                    # raise WekoDepositError(ex=ex, msg="Convert item metadata error.") from ex
            
            with patch("weko_deposit.api.RedisConnection.connection",side_effect=WekoRedisError("test_redis_error")):
                # with pytest.raises(WekoRedisError) as ex:
                    # ret = deposit.convert_item_metadata(index_obj,{})
                deposit.convert_item_metadata(index_obj,{})
                    # assert ex.value.code == 500
                    # assert ex.value.data == "Failed to register item!"
                mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_REDIS')
                mock_logger.reset_mock()
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()
            
    # def _convert_description_to_object(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__convert_description_to_object -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__convert_description_to_object(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            deposit._convert_description_to_object()
            jrc = {"description":"test_description"}
            deposit.jrc=jrc
            deposit._convert_description_to_object()

            jrc = {"description":["test_description1",{"value":"test_description2"}]}
            deposit.jrc=jrc
            deposit._convert_description_to_object()
            assert deposit.jrc["description"] == [{"value":"test_description1"},{"value":"test_description2"}]

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def _convert_jpcoar_data_to_es(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__convert_jpcoar_data_to_es -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__convert_jpcoar_data_to_es(sel,app,db,location,es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']
        deposit._convert_jpcoar_data_to_es()

    # def _convert_data_for_geo_location(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__convert_data_for_geo_location -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__convert_data_for_geo_location(sel,app,db,location,es_records):
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
                "geoLocationPoint":{
                    "pointLongitude":["1","2","3","4"],
                    "pointLatitude": ["5","6","7","8"]
                },
                "geoLocationBox":{
                    "northBoundLatitude":"not_list_value",
                    "eastBoundLongitude":"not_list_value",
                    "southBoundLatitude":"not_list_value",
                    "westBoundLongitude":"not_list_value"
                },
                "geoLocationBox":{
                    "northBoundLatitude":["1","2","3"],
                    "eastBoundLongitude":["4","5","6"],
                    "southBoundLatitude":["7","8","9"],
                    "westBoundLongitude":["0","1","2"]
                },
                "other":""}}
            deposit.jrc = jrc
            test = {
                "geoLocationPlace":"test_location_place",
                "geoLocationPoint":[{"lat":"5","lon":"1"},{"lat":"6","lon":"2"},{"lat":"7","lon":"3"},{"lat":"8","lon":"4"},],
                "geoLocationBox":{
                    "northEastPoint":[{"lat":"1","lon":"4"},{"lat":"2","lon":"5"},{"lat":"3","lon":"6"},],
                    "southWestPoint":[{"lat":"7","lon":"0"},{"lat":"8","lon":"1"},{"lat":"9","lon":"2"},],
                },
            }
            deposit._convert_data_for_geo_location()
            assert deposit.jrc["geoLocation"] == test

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()
    
    #         def _convert_geo_location(value):
    #         def _convert_geo_location_box():

    # def delete_by_index_tree_id(cls, index_id: str, ignore_items: list = []):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_by_index_tree_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_by_index_tree_id(sel,app,db,location,es_records_2):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records_2
            record = records[0]
            deposit = record['deposit']
            deposit.delete_by_index_tree_id('1',[])

            record = records[1]
            deposit = record['deposit']
            deposit['9']='9'
            deposit.delete_by_index_tree_id('2',record['deposit'])

            record = records[2]
            deposit = record['deposit']
            # deposit['path']='2'
            deposit.delete_by_index_tree_id('3',record['deposit'])

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()


    # def update_pid_by_index_tree_id(self, path):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_pid_by_index_tree_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_pid_by_index_tree_id(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            assert deposit.update_pid_by_index_tree_id('1')==True

            with patch("invenio_db.db.session.begin_nested", side_effect=SQLAlchemyError("test_error")):
                assert deposit.update_pid_by_index_tree_id('1')==False
            
            with patch("invenio_db.db.session.begin_nested", side_effect=Exception("test_error")):
                assert deposit.update_pid_by_index_tree_id('1')==False

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

    # def update_item_by_task(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_item_by_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_item_by_task(sel,app,db,location,es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']
        record_data = record['record_data']
        ret = deposit.update_item_by_task()
        assert ret==deposit

    # def delete_es_index_attempt(self, pid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_es_index_attempt -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_es_index_attempt(sel,app,db,location):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            # deposit = WekoDeposit.create({})
            session["activity_info"] = {"activity_id":'1'}
            data = {"$schema":"https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"}
            id = uuid.uuid4()
            deposit = WekoDeposit.create(data,id_=id)
            deposit.pid.status = "D"
            # deposit.pid = "1"
            db.session.commit()
            deposit.delete_es_index_attempt(deposit.pid)

                        
            with patch("invenio_search.ext.Elasticsearch.delete", side_effect=Exception("test_error")):
                deposit = WekoDeposit.create({})
                deposit.pid.status = "D"
                db.session.commit()
                deposit.delete_es_index_attempt(deposit.pid)

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.reset_mock()

    # def update_author_link(self, author_link):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_author_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_author_link(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            
            deposit = record['deposit']
            record = records[0]['record']
            author_link_info = {
                    
                    "id": deposit.id,
                    "author_link": ['0']
                }
            # ret = indexer.update_author_link(author_link_info)
            # assert deposit.update_author_link({})==None
            # deposit.update_author_link(author_link_info)
            assert deposit.update_author_link(author_link_info) is not None
            # todo19
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='author_link is not empty')
            mock_logger.reset_mock()


    # def update_feedback_mail(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_feedback_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_feedback_mail(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            # indexer, records = es_records
            # record = records[0]
            # deposit = record['deposit']
            # assert deposit.update_feedback_mail()==None

            indexer, records = es_records
            record = records[1]
            deposit = record['deposit']
            assert deposit.update_feedback_mail()==None
            # todo20
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch='mail_list is not empty')
            mock_logger.reset_mock()

    # def remove_feedback_mail(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_remove_feedback_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_remove_feedback_mail(sel,app,db,location,es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']
        assert deposit.remove_feedback_mail()==None

    # def clean_unuse_file_contents(self, item_id, pre_object_versions,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_clean_unuse_file_contents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_clean_unuse_file_contents(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            bucket = Bucket.create()
            objs = list()
            for i in range(5):
                file = FileInstance(uri="/var/tmp/test_dir%s"%i,storage_class="S",size=18)
                objs.append(ObjectVersion.create(bucket=bucket.id,key="test%s.txt"%i,_file_id=file))
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
                file = FileInstance(uri="/var/tmp/test1_dir%s"%i,storage_class="S",size=18)
                objs.append(ObjectVersion.create(bucket=bucket.id,key="test%s.txt"%i,_file_id=file))
            pre = objs[:2]
            new = objs[-2:]
            with patch("invenio_files_rest.storage.pyfs.PyFSFileStorage.delete"):
                # deposit.clean_unuse_file_contents(1,pre,new)
                deposit.clean_unuse_file_contents(1,pre,new,is_import=True)

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()


    # def merge_data_to_record_without_version(self, pid, keep_version=False,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_merge_data_to_record_without_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_merge_data_to_record_without_version(sel,app,db,location,es_records):
        with patch('weko_deposit.api.weko_logger') as mock_logger:
            indexer, records = es_records
            record = records[0]
            deposit = record['deposit']
            recid = record['recid']
            
            assert deposit.merge_data_to_record_without_version(recid)

            assert deposit.merge_data_to_record_without_version(recid, keep_version=True)

            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

    # def prepare_draft_item(self, recid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_prepare_draft_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_prepare_draft_item(sel,app,db,location,es_records):
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
    def test_delete_content_files(sel,app,db,location,es_records):
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

            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
            mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
            mock_logger.reset_mock()

# class WekoRecord(Record):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
