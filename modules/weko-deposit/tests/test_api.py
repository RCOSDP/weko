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
from pytest_mock import mocker
from mock import Mock, patch, MagicMock
import uuid
import copy
from collections import OrderedDict
from werkzeug.exceptions import HTTPException
import time
from flask import session, current_app, make_response
from flask_login import login_user
from flask_security import current_user, url_for_security
import json

from elasticsearch.exceptions import NotFoundError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from invenio_pidstore.errors import PIDInvalidAction
from invenio_pidrelations.models import PIDRelation
from invenio_records.errors import MissingModelError
from invenio_records.models import RecordMetadata
from invenio_records_rest.errors import PIDResolveRESTError
from invenio_records_files.models import RecordsBuckets
from invenio_records_files.api import Record
from invenio_records.models import RecordMetadata
from invenio_files_rest.models import Bucket, ObjectVersion,FileInstance
from invenio_records.api import RecordRevision
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.contrib.records import RecordDraft
from six import BytesIO
from weko_records.utils import get_options_and_order_list
from elasticsearch import Elasticsearch
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import OperationalError
from weko_admin.models import AdminSettings
from weko_records.models import ItemMetadata, ItemTypeProperty
from weko_records.api import FeedbackMailList, ItemLink, ItemsMetadata, ItemTypes, Mapping, WekoRecord
from invenio_pidrelations.serializers.utils import serialize_relations
from weko_deposit.api import WekoDeposit, WekoFileObject, WekoIndexer, \
    WekoRecord, _FormatSysBibliographicInformation, _FormatSysCreator
from weko_deposit.config import WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS
from invenio_accounts.testutils import login_user_via_view,login_user_via_session
from invenio_accounts.models import User
from weko_items_ui.config import WEKO_ITEMS_UI_MS_MIME_TYPE,WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT
from weko_workflow.models import Activity
from weko_redis.redis import RedisConnection

from tests.helpers import login, create_record_with_pdf
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
        bucket = Bucket.create()
        key = 'hello.txt'
        stream = BytesIO(b'helloworld')
        obj = ObjectVersion.create(bucket=bucket, key=key, stream=stream)
        with app.test_request_context():
            file = WekoFileObject(obj,{})
            assert type(file)==WekoFileObject

    # def info(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoFileObject::test_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_info(self,app,location):
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


    #  def file_preview_able(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoFileObject::test_file_preview_able -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_file_preview_able(self,app,location):
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






# class WekoIndexer(RecordIndexer):

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestWekoIndexer:

    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_es_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_es_index(self,app):
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


    # def delete_file_index(self, body, parent_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_delete_file_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_file_index(self,app,es_records):
        indexer, records = es_records
        record = records[0]['record']
        dep = WekoDeposit(record,record.model)
        indexer.delete_file_index([record.id],record.pid)
        from elasticsearch.exceptions import NotFoundError
        with pytest.raises(NotFoundError):
            indexer.get_metadata_by_item_id(record.pid)


    # def update_relation_version_is_last(self, version):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_relation_version_is_last -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_relation_version_is_last(self,es_records):
        indexer, records = es_records
        version = records[0]['record']
        pid = records[0]['recid']
        relations = serialize_relations(pid)
        relations_ver = relations['version'][0]
        relations_ver['id'] = pid.object_uuid
        relations_ver['is_last'] = relations_ver.get('index') == 0
        assert indexer.update_relation_version_is_last(relations_ver)=={'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': '{}'.format(pid.object_uuid), '_version': 2, 'result': 'noop', '_shards': {'total': 0, 'successful': 0, 'failed': 0}}

    # def update_es_data(self, record, update_revision=True,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_es_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_es_data(self,es_records):
        indexer, records = es_records
        record = records[0]['record']
        assert indexer.update_es_data(record, update_revision=False,update_oai=False, is_deleted=False)=={'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': '{}'.format(record.id), '_version': 3, 'result': 'updated', '_shards': {'total': 2, 'successful': 1, 'failed': 0}, '_seq_no': 9, '_primary_term': 1}
        res = indexer.update_es_data(record, update_revision=False,update_oai=True, is_deleted=False)
        assert res=={'_id': res['_id'], '_index': 'test-weko-item-v1.0.0', '_primary_term': 1, '_seq_no': 10, '_shards': {'failed': 0, 'successful': 1, 'total': 2}, '_type': 'item-v1.0.0', '_version': 4, 'result': 'updated'}

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


    # def get_count_by_index_id(self, tree_path):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_count_by_index_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_count_by_index_id(self,es_records):
        indexer, records = es_records
        metadata = records[0]['record_data']
        ret = indexer.get_count_by_index_id(1)
        assert ret==4
        ret = indexer.get_count_by_index_id(2)
        assert ret==5

    #     def get_pid_by_es_scroll(self, path):
    #         def get_result(result):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_pid_by_es_scroll -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_pid_by_es_scroll(self,es_records):
        def get_recids(ret):
            recids = []
            for obj_uuid in ret:
                r = RecordMetadata.query.filter_by(id=obj_uuid).first()
                recids.append(r.json['recid'])
            return recids

        indexer, records = es_records
        ret = indexer.get_pid_by_es_scroll(1)
        assert isinstance(next(ret),list)
        assert isinstance(next(ret),dict)
        assert ret is not None

        # get all versions
        ret = next(indexer.get_pid_by_es_scroll(4), [])
        recids = get_recids(ret)
        assert '10' in recids
        assert '10.2' in recids

        # get only latest version
        ret = next(indexer.get_pid_by_es_scroll(4, only_latest_version=True), [])
        recids = get_recids(ret)
        assert '10' in recids
        assert not '10.2' in recids

    #     def get_metadata_by_item_id(self, item_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_get_metadata_by_item_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_metadata_by_item_id(self,es_records):
        indexer, records = es_records
        record = records[0]['record']
        record_data = records[0]['record_data']
        ret = indexer.get_metadata_by_item_id(record.id)
        assert ret['_index']=='test-weko-item-v1.0.0'

    #     def update_feedback_mail_list(self, feedback_mail):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_feedback_mail_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_feedback_mail_list(selft,es_records):
        indexer, records = es_records
        record = records[0]['record']
        feedback_mail= {'id': record.id, 'mail_list': [{'email': 'wekosoftware@nii.ac.jp', 'author_id': ''}]}
        ret = indexer.update_feedback_mail_list(feedback_mail)
        assert ret == {'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': '{}'.format(record.id), '_version': 3, 'result': 'updated', '_shards': {'total': 2, 'successful': 1, 'failed': 0}, '_seq_no': 9, '_primary_term': 1}

    #     def update_request_mail_list(self, request_mail):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_request_mail_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_request_mail_list(selft,es_records):
        indexer, records = es_records
        record = records[0]['record']
        request_mail= {'id': record.id, 'mail_list': [{'email': 'wekosoftware@nii.ac.jp', 'author_id': ''}]}
        ret = indexer.update_request_mail_list(request_mail)
        assert ret['_id'] == '{}'.format(record.id) and ret['result'] == 'updated' and ret['_shards'] == {'total': 2, 'successful': 1, 'failed': 0}


    #     def update_author_link_and_weko_link(self, author_link):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_author_link_and_weko_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_author_link_and_weko_link(self,es_records):
        indexer, records = es_records
        record = records[0]['record']
        author_link_info = {
                "id": record.id,
                "author_link": ['1'],
                "weko_link": {"1":"13"}
            }
        ret = indexer.update_author_link_and_weko_link(author_link_info)
        assert ret == {'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': str(record.id), '_version': 2, 'result': 'updated', '_shards': {'total': 2, 'successful': 1, 'failed': 0}, '_seq_no': 12, '_primary_term': 1}

    #     def update_jpcoar_identifier(self, dc, item_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_update_jpcoar_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_jpcoar_identifier(self,es_records):
        indexer, records = es_records
        record_data = records[0]['record_data']
        record = records[0]['record']
        assert indexer.update_jpcoar_identifier(record_data,record.id)=={'_index': 'test-weko-item-v1.0.0', '_type': 'item-v1.0.0', '_id': '{}'.format(record.id), '_version': 3, 'result': 'updated', '_shards': {'total': 2, 'successful': 1, 'failed': 0}, '_seq_no': 9, '_primary_term': 1}

    #     def __build_bulk_es_data(self, updated_data):
    #     def bulk_update(self, updated_data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoIndexer::test_bulk_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_bulk_update(self,es_records):
        indexer, records = es_records
        res = []
        res.append(records[0]['record'])
        res.append(records[1]['record'])
        res.append(records[2]['record'])
        indexer.bulk_update(res)

        with patch("weko_deposit.api.bulk",return_value=(0,["test_error1","test_error2"])):
            indexer.bulk_update(res)

# class WekoDeposit(Deposit):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestWekoDeposit:
    # def item_metadata(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_item_metadata(self, app, es_records):
        _, records, item_metadata = es_records
        deposit = records[0]['deposit']

        expected = {'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'title', 'owners': [1], 'status': 'published', '$schema': '/items/jsonschema/1', 'pubdate': '2022-08-20', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}, 'shared_user_ids': [], 'item_1617186331708': [{'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}}

        print(json.loads(json.dumps(item_metadata)))
        assert json.loads(json.dumps(item_metadata)) == json.loads(json.dumps(expected))


        deposit = WekoDeposit({})
        
        from sqlalchemy.orm.exc import NoResultFound
        with pytest.raises(NoResultFound):
            assert deposit.item_metadata == ""

    # def is_published(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_is_published -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_published(self,app,location,es_records):
        indexer, records = es_records
        deposit = records[0]['deposit']
        assert deposit.is_published()==True

    # def merge_with_published(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_merge_with_published -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_merge_with_published(self,app,db,es_records):
        indexer, records = es_records
        dep = records[0]['deposit']
        ret = dep.merge_with_published()
        assert isinstance(ret,RecordRevision)==True

        record = records[0]["record"]
        record["$schema"] = "https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"
        record["control_number"] = "1"
        from dictdiffer.merge import UnresolvedConflictsException
        from invenio_deposit.errors import MergeConflict
        with patch("weko_deposit.api.WekoDeposit.fetch_published",return_value=(records[0]["depid"],record)):
            with patch('invenio_records.api.Record.revisions', return_value=record):
                with patch("weko_deposit.api.Merger.run",side_effect=UnresolvedConflictsException(["test_conflict"])):
                    with pytest.raises(MergeConflict):
                        ret = dep.merge_with_published()
    
    # def _patch(diff_result, destination, in_place=False):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__patch -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__patch(self,app,location):
        with app.test_request_context():
            dep = WekoDeposit.create({})
            #diff_result = [('change', '_buckets.deposit', ('753ff0d7-0659-4460-9b1a-fd1ef38467f2', '688f2d41-be61-468f-95e2-a06abefdaf60')), ('change', '_buckets.deposit', ('753ff0d7-0659-4460-9b1a-fd1ef38467f2', '688f2d41-be61-468f-95e2-a06abefdaf60')), ('add', '', [('_oai', {})]), ('add', '', [('_oai', {})]), ('add', '_oai', [('id', 'oai:weko3.example.org:00000013')]), ('add', '_oai', [('id', 'oai:weko3.example.org:00000013')]), ('add', '_oai', [('sets', [])]), ('add', '_oai', [('sets', [])]), ('add', '_oai.sets', [(0, '1661517684078')]), ('add', '_oai.sets', [(0, '1661517684078')]), ('add', '', [('author_link', [])]), ('add', '', [('author_link', [])]), ('add', 'author_link', [(0, '4')]), ('add', 'author_link', [(0, '4')]), ('add', '', [('item_1617186331708', {})]), ('add', '', [('item_1617186331708', {})]), ('add', 'item_1617186331708', [('attribute_name', 'Title')]), ('add', 'item_1617186331708', [('attribute_name', 'Title')]), ('add', 'item_1617186331708', [('attribute_value_mlt', [])]), ('add', 'item_1617186331708', [('attribute_value_mlt', [])]), ('add', 'item_1617186331708.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186331708.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255647225', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255647225', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255648112', 'ja')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 0], [('subitem_1551255648112', 'ja')]), ('add', 'item_1617186331708.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186331708.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255647225', 'en_conference paperITEM00000001(public_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255647225', 'en_conference paperITEM00000001(public_open_access_simple)')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255648112', 'en')]), ('add', ['item_1617186331708', 'attribute_value_mlt', 1], [('subitem_1551255648112', 'en')]), ('add', '', [('item_1617186385884', {})]), ('add', '', [('item_1617186385884', {})]), ('add', 'item_1617186385884', [('attribute_name', 'Alternative Title')]), ('add', 'item_1617186385884', [('attribute_name', 'Alternative Title')]), ('add', 'item_1617186385884', [('attribute_value_mlt', [])]), ('add', 'item_1617186385884', [('attribute_value_mlt', [])]), ('add', 'item_1617186385884.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186385884.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255721061', 'en')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 0], [('subitem_1551255721061', 'en')]), ('add', 'item_1617186385884.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186385884.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255720400', 'Alternative Title')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255721061', 'ja')]), ('add', ['item_1617186385884', 'attribute_value_mlt', 1], [('subitem_1551255721061', 'ja')]), ('add', '', [('item_1617186419668', {})]), ('add', '', [('item_1617186419668', {})]), ('add', 'item_1617186419668', [('attribute_name', 'Creator')]), ('add', 'item_1617186419668', [('attribute_name', 'Creator')]), ('add', 'item_1617186419668', [('attribute_type', 'creator')]), ('add', 'item_1617186419668', [('attribute_type', 'creator')]), ('add', 'item_1617186419668', [('attribute_value_mlt', [])]), ('add', 'item_1617186419668', [('attribute_value_mlt', [])]), ('add', 'item_1617186419668.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186419668.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorAffiliations', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorAffiliations', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifier', '0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifier', '0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierScheme', 'ISNI')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierScheme', 'ISNI')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierURI', 'http://isni.org/isni/0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNameIdentifiers', 0], [('affiliationNameIdentifierURI', 'http://isni.org/isni/0000000121691048')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0], [('affiliationNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationName', 'University')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationName', 'University')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorAffiliations', 0, 'affiliationNames', 0], [('affiliationNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', '4')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', '4')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'WEKO')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'WEKO')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(3, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(3, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 0, 'nameIdentifiers', 3], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', 'item_1617186419668.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186419668.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 1, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', 'item_1617186419668.attribute_value_mlt', [(2, {})]), ('add', 'item_1617186419668.attribute_value_mlt', [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorMails', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorMails', 0], [('creatorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('creatorNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorName', '情報, 太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 0], [('creatorNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 1], [('creatorNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorName', 'Joho, Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'creatorNames', 2], [('creatorNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('familyNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('givenNames', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2], [('nameIdentifiers', [])]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifier', 'zzzzzzz')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617186419668', 'attribute_value_mlt', 2, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', '', [('item_1617186476635', {})]), ('add', '', [('item_1617186476635', {})]), ('add', 'item_1617186476635', [('attribute_name', 'Access Rights')]), ('add', 'item_1617186476635', [('attribute_name', 'Access Rights')]), ('add', 'item_1617186476635', [('attribute_value_mlt', [])]), ('add', 'item_1617186476635', [('attribute_value_mlt', [])]), ('add', 'item_1617186476635.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186476635.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1522299639480', 'open access')]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1522299639480', 'open access')]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1600958577026', 'http://purl.org/coar/access_right/c_abf2')]), ('add', ['item_1617186476635', 'attribute_value_mlt', 0], [('subitem_1600958577026', 'http://purl.org/coar/access_right/c_abf2')]), ('add', '', [('item_1617186499011', {})]), ('add', '', [('item_1617186499011', {})]), ('add', 'item_1617186499011', [('attribute_name', 'Rights')]), ('add', 'item_1617186499011', [('attribute_name', 'Rights')]), ('add', 'item_1617186499011', [('attribute_value_mlt', [])]), ('add', 'item_1617186499011', [('attribute_value_mlt', [])]), ('add', 'item_1617186499011.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186499011.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650717957', 'ja')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650717957', 'ja')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650727486', 'http://localhost')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522650727486', 'http://localhost')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522651041219', 'Rights Information')]), ('add', ['item_1617186499011', 'attribute_value_mlt', 0], [('subitem_1522651041219', 'Rights Information')]), ('add', '', [('item_1617186609386', {})]), ('add', '', [('item_1617186609386', {})]), ('add', 'item_1617186609386', [('attribute_name', 'Subject')]), ('add', 'item_1617186609386', [('attribute_name', 'Subject')]), ('add', 'item_1617186609386', [('attribute_value_mlt', [])]), ('add', 'item_1617186609386', [('attribute_value_mlt', [])]), ('add', 'item_1617186609386.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186609386.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522299896455', 'ja')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522299896455', 'ja')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300014469', 'Other')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300014469', 'Other')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300048512', 'http://localhost/')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1522300048512', 'http://localhost/')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1523261968819', 'Sibject1')]), ('add', ['item_1617186609386', 'attribute_value_mlt', 0], [('subitem_1523261968819', 'Sibject1')]), ('add', '', [('item_1617186626617', {})]), ('add', '', [('item_1617186626617', {})]), ('add', 'item_1617186626617', [('attribute_name', 'Description')]), ('add', 'item_1617186626617', [('attribute_name', 'Description')]), ('add', 'item_1617186626617', [('attribute_value_mlt', [])]), ('add', 'item_1617186626617', [('attribute_value_mlt', [])]), ('add', 'item_1617186626617.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186626617.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description', 'Description\nDescription<br/>Description')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description', 'Description\nDescription<br/>Description')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_language', 'en')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_language', 'en')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_type', 'Abstract')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 0], [('subitem_description_type', 'Abstract')]), ('add', 'item_1617186626617.attribute_value_mlt', [(1, {})]), ('add', 'item_1617186626617.attribute_value_mlt', [(1, {})]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description', '概要\n概要\n概要\n概要')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description', '概要\n概要\n概要\n概要')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_language', 'ja')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_language', 'ja')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_type', 'Abstract')]), ('add', ['item_1617186626617', 'attribute_value_mlt', 1], [('subitem_description_type', 'Abstract')]), ('add', '', [('item_1617186643794', {})]), ('add', '', [('item_1617186643794', {})]), ('add', 'item_1617186643794', [('attribute_name', 'Publisher')]), ('add', 'item_1617186643794', [('attribute_name', 'Publisher')]), ('add', 'item_1617186643794', [('attribute_value_mlt', [])]), ('add', 'item_1617186643794', [('attribute_value_mlt', [])]), ('add', 'item_1617186643794.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186643794.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300295150', 'en')]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300295150', 'en')]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300316516', 'Publisher')]), ('add', ['item_1617186643794', 'attribute_value_mlt', 0], [('subitem_1522300316516', 'Publisher')]), ('add', '', [('item_1617186660861', {})]), ('add', '', [('item_1617186660861', {})]), ('add', 'item_1617186660861', [('attribute_name', 'Date')]), ('add', 'item_1617186660861', [('attribute_name', 'Date')]), ('add', 'item_1617186660861', [('attribute_value_mlt', [])]), ('add', 'item_1617186660861', [('attribute_value_mlt', [])]), ('add', 'item_1617186660861.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186660861.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300695726', 'Available')]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300695726', 'Available')]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300722591', '2021-06-30')]), ('add', ['item_1617186660861', 'attribute_value_mlt', 0], [('subitem_1522300722591', '2021-06-30')]), ('add', '', [('item_1617186702042', {})]), ('add', '', [('item_1617186702042', {})]), ('add', 'item_1617186702042', [('attribute_name', 'Language')]), ('add', 'item_1617186702042', [('attribute_name', 'Language')]), ('add', 'item_1617186702042', [('attribute_value_mlt', [])]), ('add', 'item_1617186702042', [('attribute_value_mlt', [])]), ('add', 'item_1617186702042.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186702042.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186702042', 'attribute_value_mlt', 0], [('subitem_1551255818386', 'jpn')]), ('add', ['item_1617186702042', 'attribute_value_mlt', 0], [('subitem_1551255818386', 'jpn')]), ('add', '', [('item_1617186783814', {})]), ('add', '', [('item_1617186783814', {})]), ('add', 'item_1617186783814', [('attribute_name', 'Identifier')]), ('add', 'item_1617186783814', [('attribute_name', 'Identifier')]), ('add', 'item_1617186783814', [('attribute_value_mlt', [])]), ('add', 'item_1617186783814', [('attribute_value_mlt', [])]), ('add', 'item_1617186783814.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186783814.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_type', 'URI')]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_type', 'URI')]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_uri', 'http://localhost')]), ('add', ['item_1617186783814', 'attribute_value_mlt', 0], [('subitem_identifier_uri', 'http://localhost')]), ('add', '', [('item_1617186859717', {})]), ('add', '', [('item_1617186859717', {})]), ('add', 'item_1617186859717', [('attribute_name', 'Temporal')]), ('add', 'item_1617186859717', [('attribute_name', 'Temporal')]), ('add', 'item_1617186859717', [('attribute_value_mlt', [])]), ('add', 'item_1617186859717', [('attribute_value_mlt', [])]), ('add', 'item_1617186859717.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186859717.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658018441', 'en')]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658018441', 'en')]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658031721', 'Temporal')]), ('add', ['item_1617186859717', 'attribute_value_mlt', 0], [('subitem_1522658031721', 'Temporal')]), ('add', '', [('item_1617186882738', {})]), ('add', '', [('item_1617186882738', {})]), ('add', 'item_1617186882738', [('attribute_name', 'Geo Location')]), ('add', 'item_1617186882738', [('attribute_name', 'Geo Location')]), ('add', 'item_1617186882738', [('attribute_value_mlt', [])]), ('add', 'item_1617186882738', [('attribute_value_mlt', [])]), ('add', 'item_1617186882738.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186882738.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0], [('subitem_geolocation_place', [])]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0], [('subitem_geolocation_place', [])]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place'], [(0, {})]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place'], [(0, {})]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place', 0], [('subitem_geolocation_place_text', 'Japan')]), ('add', ['item_1617186882738', 'attribute_value_mlt', 0, 'subitem_geolocation_place', 0], [('subitem_geolocation_place_text', 'Japan')]), ('add', '', [('item_1617186901218', {})]), ('add', '', [('item_1617186901218', {})]), ('add', 'item_1617186901218', [('attribute_name', 'Funding Reference')]), ('add', 'item_1617186901218', [('attribute_name', 'Funding Reference')]), ('add', 'item_1617186901218', [('attribute_value_mlt', [])]), ('add', 'item_1617186901218', [('attribute_value_mlt', [])]), ('add', 'item_1617186901218.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186901218.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399143519', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399143519', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399281603', 'ISNI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399281603', 'ISNI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399333375', 'http://xxx')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399143519'], [('subitem_1522399333375', 'http://xxx')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399412622', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399412622', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522399416691', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522399416691', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522737543681', 'Funder Name')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399412622', 0], [('subitem_1522737543681', 'Funder Name')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399571623', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399571623', {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399585738', 'Award URI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399585738', 'Award URI')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399628911', 'Award Number')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399571623'], [('subitem_1522399628911', 'Award Number')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399651758', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0], [('subitem_1522399651758', [])]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758'], [(0, {})]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721910626', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721910626', 'en')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721929892', 'Award Title')]), ('add', ['item_1617186901218', 'attribute_value_mlt', 0, 'subitem_1522399651758', 0], [('subitem_1522721929892', 'Award Title')]), ('add', '', [('item_1617186920753', {})]), ('add', '', [('item_1617186920753', {})]), ('add', 'item_1617186920753', [('attribute_name', 'Source Identifier')]), ('add', 'item_1617186920753', [('attribute_name', 'Source Identifier')]), ('add', 'item_1617186920753', [('attribute_value_mlt', [])]), ('add', 'item_1617186920753', [('attribute_value_mlt', [])]), ('add', 'item_1617186920753.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186920753.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646500366', 'ISSN')]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646500366', 'ISSN')]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646572813', 'xxxx-xxxx-xxxx')]), ('add', ['item_1617186920753', 'attribute_value_mlt', 0], [('subitem_1522646572813', 'xxxx-xxxx-xxxx')]), ('add', '', [('item_1617186941041', {})]), ('add', '', [('item_1617186941041', {})]), ('add', 'item_1617186941041', [('attribute_name', 'Source Title')]), ('add', 'item_1617186941041', [('attribute_name', 'Source Title')]), ('add', 'item_1617186941041', [('attribute_value_mlt', [])]), ('add', 'item_1617186941041', [('attribute_value_mlt', [])]), ('add', 'item_1617186941041.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186941041.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650068558', 'en')]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650068558', 'en')]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650091861', 'Source Title')]), ('add', ['item_1617186941041', 'attribute_value_mlt', 0], [('subitem_1522650091861', 'Source Title')]), ('add', '', [('item_1617186959569', {})]), ('add', '', [('item_1617186959569', {})]), ('add', 'item_1617186959569', [('attribute_name', 'Volume Number')]), ('add', 'item_1617186959569', [('attribute_name', 'Volume Number')]), ('add', 'item_1617186959569', [('attribute_value_mlt', [])]), ('add', 'item_1617186959569', [('attribute_value_mlt', [])]), ('add', 'item_1617186959569.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186959569.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186959569', 'attribute_value_mlt', 0], [('subitem_1551256328147', '1')]), ('add', ['item_1617186959569', 'attribute_value_mlt', 0], [('subitem_1551256328147', '1')]), ('add', '', [('item_1617186981471', {})]), ('add', '', [('item_1617186981471', {})]), ('add', 'item_1617186981471', [('attribute_name', 'Issue Number')]), ('add', 'item_1617186981471', [('attribute_name', 'Issue Number')]), ('add', 'item_1617186981471', [('attribute_value_mlt', [])]), ('add', 'item_1617186981471', [('attribute_value_mlt', [])]), ('add', 'item_1617186981471.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186981471.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186981471', 'attribute_value_mlt', 0], [('subitem_1551256294723', '111')]), ('add', ['item_1617186981471', 'attribute_value_mlt', 0], [('subitem_1551256294723', '111')]), ('add', '', [('item_1617186994930', {})]), ('add', '', [('item_1617186994930', {})]), ('add', 'item_1617186994930', [('attribute_name', 'Number of Pages')]), ('add', 'item_1617186994930', [('attribute_name', 'Number of Pages')]), ('add', 'item_1617186994930', [('attribute_value_mlt', [])]), ('add', 'item_1617186994930', [('attribute_value_mlt', [])]), ('add', 'item_1617186994930.attribute_value_mlt', [(0, {})]), ('add', 'item_1617186994930.attribute_value_mlt', [(0, {})]), ('add', ['item_1617186994930', 'attribute_value_mlt', 0], [('subitem_1551256248092', '12')]), ('add', ['item_1617186994930', 'attribute_value_mlt', 0], [('subitem_1551256248092', '12')]), ('add', '', [('item_1617187024783', {})]), ('add', '', [('item_1617187024783', {})]), ('add', 'item_1617187024783', [('attribute_name', 'Page Start')]), ('add', 'item_1617187024783', [('attribute_name', 'Page Start')]), ('add', 'item_1617187024783', [('attribute_value_mlt', [])]), ('add', 'item_1617187024783', [('attribute_value_mlt', [])]), ('add', 'item_1617187024783.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187024783.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187024783', 'attribute_value_mlt', 0], [('subitem_1551256198917', '1')]), ('add', ['item_1617187024783', 'attribute_value_mlt', 0], [('subitem_1551256198917', '1')]), ('add', '', [('item_1617187045071', {})]), ('add', '', [('item_1617187045071', {})]), ('add', 'item_1617187045071', [('attribute_name', 'Page End')]), ('add', 'item_1617187045071', [('attribute_name', 'Page End')]), ('add', 'item_1617187045071', [('attribute_value_mlt', [])]), ('add', 'item_1617187045071', [('attribute_value_mlt', [])]), ('add', 'item_1617187045071.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187045071.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187045071', 'attribute_value_mlt', 0], [('subitem_1551256185532', '3')]), ('add', ['item_1617187045071', 'attribute_value_mlt', 0], [('subitem_1551256185532', '3')]), ('add', '', [('item_1617187112279', {})]), ('add', '', [('item_1617187112279', {})]), ('add', 'item_1617187112279', [('attribute_name', 'Degree Name')]), ('add', 'item_1617187112279', [('attribute_name', 'Degree Name')]), ('add', 'item_1617187112279', [('attribute_value_mlt', [])]), ('add', 'item_1617187112279', [('attribute_value_mlt', [])]), ('add', 'item_1617187112279.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187112279.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256126428', 'Degree Name')]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256126428', 'Degree Name')]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256129013', 'en')]), ('add', ['item_1617187112279', 'attribute_value_mlt', 0], [('subitem_1551256129013', 'en')]), ('add', '', [('item_1617187136212', {})]), ('add', '', [('item_1617187136212', {})]), ('add', 'item_1617187136212', [('attribute_name', 'Date Granted')]), ('add', 'item_1617187136212', [('attribute_name', 'Date Granted')]), ('add', 'item_1617187136212', [('attribute_value_mlt', [])]), ('add', 'item_1617187136212', [('attribute_value_mlt', [])]), ('add', 'item_1617187136212.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187136212.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187136212', 'attribute_value_mlt', 0], [('subitem_1551256096004', '2021-06-30')]), ('add', ['item_1617187136212', 'attribute_value_mlt', 0], [('subitem_1551256096004', '2021-06-30')]), ('add', '', [('item_1617187187528', {})]), ('add', '', [('item_1617187187528', {})]), ('add', 'item_1617187187528', [('attribute_name', 'Conference')]), ('add', 'item_1617187187528', [('attribute_name', 'Conference')]), ('add', 'item_1617187187528', [('attribute_value_mlt', [])]), ('add', 'item_1617187187528', [('attribute_value_mlt', [])]), ('add', 'item_1617187187528.attribute_value_mlt', [(0, {})]), ('add', 'item_1617187187528.attribute_value_mlt', [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711633003', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711633003', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711636923', 'Conference Name')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711636923', 'Conference Name')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711645590', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711633003', 0], [('subitem_1599711645590', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711655652', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711655652', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711660052', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711660052', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711680082', 'Sponsor')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711680082', 'Sponsor')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711686511', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711660052', 0], [('subitem_1599711686511', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711699392', {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711699392', {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711704251', '2020/12/11')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711704251', '2020/12/11')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711712451', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711712451', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711727603', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711727603', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711731891', '2000')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711731891', '2000')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711735410', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711735410', '1')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711739022', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711739022', '12')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711743722', '2020')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711743722', '2020')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711745532', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711699392'], [('subitem_1599711745532', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711758470', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711758470', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711769260', 'Conference Venue')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711769260', 'Conference Venue')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711775943', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711758470', 0], [('subitem_1599711775943', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711788485', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711788485', [])]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485'], [(0, {})]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711798761', 'Conference Place')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711798761', 'Conference Place')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711803382', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0, 'subitem_1599711788485', 0], [('subitem_1599711803382', 'ja')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711813532', 'JPN')]), ('add', ['item_1617187187528', 'attribute_value_mlt', 0], [('subitem_1599711813532', 'JPN')]), ('add', '', [('item_1617258105262', {})]), ('add', '', [('item_1617258105262', {})]), ('add', 'item_1617258105262', [('attribute_name', 'Resource Type')]), ('add', 'item_1617258105262', [('attribute_name', 'Resource Type')]), ('add', 'item_1617258105262', [('attribute_value_mlt', [])]), ('add', 'item_1617258105262', [('attribute_value_mlt', [])]), ('add', 'item_1617258105262.attribute_value_mlt', [(0, {})]), ('add', 'item_1617258105262.attribute_value_mlt', [(0, {})]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourcetype', 'conference paper')]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourcetype', 'conference paper')]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourceuri', 'http://purl.org/coar/resource_type/c_5794')]), ('add', ['item_1617258105262', 'attribute_value_mlt', 0], [('resourceuri', 'http://purl.org/coar/resource_type/c_5794')]), ('add', '', [('item_1617265215918', {})]), ('add', '', [('item_1617265215918', {})]), ('add', 'item_1617265215918', [('attribute_name', 'Version Type')]), ('add', 'item_1617265215918', [('attribute_name', 'Version Type')]), ('add', 'item_1617265215918', [('attribute_value_mlt', [])]), ('add', 'item_1617265215918', [('attribute_value_mlt', [])]), ('add', 'item_1617265215918.attribute_value_mlt', [(0, {})]), ('add', 'item_1617265215918.attribute_value_mlt', [(0, {})]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1522305645492', 'AO')]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1522305645492', 'AO')]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1600292170262', 'http://purl.org/coar/version/c_b1a7d7d4d402bcce')]), ('add', ['item_1617265215918', 'attribute_value_mlt', 0], [('subitem_1600292170262', 'http://purl.org/coar/version/c_b1a7d7d4d402bcce')]), ('add', '', [('item_1617349709064', {})]), ('add', '', [('item_1617349709064', {})]), ('add', 'item_1617349709064', [('attribute_name', 'Contributor')]), ('add', 'item_1617349709064', [('attribute_name', 'Contributor')]), ('add', 'item_1617349709064', [('attribute_value_mlt', [])]), ('add', 'item_1617349709064', [('attribute_value_mlt', [])]), ('add', 'item_1617349709064.attribute_value_mlt', [(0, {})]), ('add', 'item_1617349709064.attribute_value_mlt', [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorMails', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorMails', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails', 0], [('contributorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorMails', 0], [('contributorMail', 'wekosoftware@nii.ac.jp')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('contributorName', '情報, 太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('contributorName', '情報, 太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('lang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 0], [('lang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('contributorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('contributorName', 'ジョウホウ, タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('lang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 1], [('lang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('contributorName', 'Joho, Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('contributorName', 'Joho, Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('lang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'contributorNames', 2], [('lang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorType', 'ContactPerson')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('contributorType', 'ContactPerson')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('familyNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyName', '情報')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 0], [('familyNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyName', 'ジョウホウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 1], [('familyNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyName', 'Joho')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'familyNames', 2], [('familyNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('givenNames', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenName', '太郎')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 0], [('givenNameLang', 'ja')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenName', 'タロウ')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 1], [('givenNameLang', 'ja-Kana')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenName', 'Taro')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'givenNames', 2], [('givenNameLang', 'en')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(1, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierScheme', 'CiNii')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 1], [('nameIdentifierURI', 'https://ci.nii.ac.jp/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(2, {})]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifier', 'xxxxxxx')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierScheme', 'KAKEN2')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', ['item_1617349709064', 'attribute_value_mlt', 0, 'nameIdentifiers', 2], [('nameIdentifierURI', 'https://kaken.nii.ac.jp/')]), ('add', '', [('item_1617349808926', {})]), ('add', '', [('item_1617349808926', {})]), ('add', 'item_1617349808926', [('attribute_name', 'Version')]), ('add', 'item_1617349808926', [('attribute_name', 'Version')]), ('add', 'item_1617349808926', [('attribute_value_mlt', [])]), ('add', 'item_1617349808926', [('attribute_value_mlt', [])]), ('add', 'item_1617349808926.attribute_value_mlt', [(0, {})]), ('add', 'item_1617349808926.attribute_value_mlt', [(0, {})]), ('add', ['item_1617349808926', 'attribute_value_mlt', 0], [('subitem_1523263171732', 'Version')]), ('add', ['item_1617349808926', 'attribute_value_mlt', 0], [('subitem_1523263171732', 'Version')]), ('add', '', [('item_1617351524846', {})]), ('add', '', [('item_1617351524846', {})]), ('add', 'item_1617351524846', [('attribute_name', 'APC')]), ('add', 'item_1617351524846', [('attribute_name', 'APC')]), ('add', 'item_1617351524846', [('attribute_value_mlt', [])]), ('add', 'item_1617351524846', [('attribute_value_mlt', [])]), ('add', 'item_1617351524846.attribute_value_mlt', [(0, {})]), ('add', 'item_1617351524846.attribute_value_mlt', [(0, {})]), ('add', ['item_1617351524846', 'attribute_value_mlt', 0], [('subitem_1523260933860', 'Unknown')]), ('add', ['item_1617351524846', 'attribute_value_mlt', 0], [('subitem_1523260933860', 'Unknown')]), ('add', '', [('item_1617353299429', {})]), ('add', '', [('item_1617353299429', {})]), ('add', 'item_1617353299429', [('attribute_name', 'Relation')]), ('add', 'item_1617353299429', [('attribute_name', 'Relation')]), ('add', 'item_1617353299429', [('attribute_value_mlt', [])]), ('add', 'item_1617353299429', [('attribute_value_mlt', [])]), ('add', 'item_1617353299429.attribute_value_mlt', [(0, {})]), ('add', 'item_1617353299429.attribute_value_mlt', [(0, {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306207484', 'isVersionOf')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306207484', 'isVersionOf')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306287251', {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1522306287251', {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306382014', 'arXiv')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306382014', 'arXiv')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306436033', 'xxxxx')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1522306287251'], [('subitem_1522306436033', 'xxxxx')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1523320863692', [])]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0], [('subitem_1523320863692', [])]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692'], [(0, {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692'], [(0, {})]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320867455', 'en')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320867455', 'en')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320909613', 'Related Title')]), ('add', ['item_1617353299429', 'attribute_value_mlt', 0, 'subitem_1523320863692', 0], [('subitem_1523320909613', 'Related Title')]), ('add', '', [('item_1617605131499', {})]), ('add', '', [('item_1617605131499', {})]), ('add', 'item_1617605131499', [('attribute_name', 'File')]), ('add', 'item_1617605131499', [('attribute_name', 'File')]), ('add', 'item_1617605131499', [('attribute_type', 'file')]), ('add', 'item_1617605131499', [('attribute_type', 'file')]), ('add', 'item_1617605131499', [('attribute_value_mlt', [])]), ('add', 'item_1617605131499', [('attribute_value_mlt', [])]), ('add', 'item_1617605131499.attribute_value_mlt', [(0, {})]), ('add', 'item_1617605131499.attribute_value_mlt', [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('accessrole', 'open_access')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('accessrole', 'open_access')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('date', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('date', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateType', 'Available')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateType', 'Available')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateValue', '2021-07-12')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'date', 0], [('dateValue', '2021-07-12')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('displaytype', 'simple')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('displaytype', 'simple')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filename', '1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filename', '1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filesize', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('filesize', [])]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize'], [(0, {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize', 0], [('value', '1 KB')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'filesize', 0], [('value', '1 KB')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('format', 'text/plain')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('format', 'text/plain')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('mimetype', 'application/pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('mimetype', 'application/pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('url', {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('url', {})]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'url'], [('url', 'https://weko3.example.org/record/13/files/1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0, 'url'], [('url', 'https://weko3.example.org/record/13/files/1KB.pdf')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('version_id', '7cdce099-fe63-445f-b78b-cf2909a8163f')]), ('add', ['item_1617605131499', 'attribute_value_mlt', 0], [('version_id', '7cdce099-fe63-445f-b78b-cf2909a8163f')]), ('add', '', [('item_1617610673286', {})]), ('add', '', [('item_1617610673286', {})]), ('add', 'item_1617610673286', [('attribute_name', 'Rights Holder')]), ('add', 'item_1617610673286', [('attribute_name', 'Rights Holder')]), ('add', 'item_1617610673286', [('attribute_value_mlt', [])]), ('add', 'item_1617610673286', [('attribute_value_mlt', [])]), ('add', 'item_1617610673286.attribute_value_mlt', [(0, {})]), ('add', 'item_1617610673286.attribute_value_mlt', [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('nameIdentifiers', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxx')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifier', 'xxxxxx')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierScheme', 'ORCID')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'nameIdentifiers', 0], [('nameIdentifierURI', 'https://orcid.org/')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('rightHolderNames', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0], [('rightHolderNames', [])]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames'], [(0, {})]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderLanguage', 'ja')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderLanguage', 'ja')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderName', 'Right Holder Name')]), ('add', ['item_1617610673286', 'attribute_value_mlt', 0, 'rightHolderNames', 0], [('rightHolderName', 'Right Holder Name')]), ('add', '', [('item_1617620223087', {})]), ('add', '', [('item_1617620223087', {})]), ('add', 'item_1617620223087', [('attribute_name', 'Heading')]), ('add', 'item_1617620223087', [('attribute_name', 'Heading')]), ('add', 'item_1617620223087', [('attribute_value_mlt', [])]), ('add', 'item_1617620223087', [('attribute_value_mlt', [])]), ('add', 'item_1617620223087.attribute_value_mlt', [(0, {})]), ('add', 'item_1617620223087.attribute_value_mlt', [(0, {})]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671149650', 'ja')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671149650', 'ja')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671178623', 'Subheading')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 0], [('subitem_1565671178623', 'Subheading')]), ('add', 'item_1617620223087.attribute_value_mlt', [(1, {})]), ('add', 'item_1617620223087.attribute_value_mlt', [(1, {})]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671149650', 'en')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671149650', 'en')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671169640', 'Banner Headline')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671178623', 'Subheding')]), ('add', ['item_1617620223087', 'attribute_value_mlt', 1], [('subitem_1565671178623', 'Subheding')]), ('add', '', [('item_1617944105607', {})]), ('add', '', [('item_1617944105607', {})]), ('add', 'item_1617944105607', [('attribute_name', 'Degree Grantor')]), ('add', 'item_1617944105607', [('attribute_name', 'Degree Grantor')]), ('add', 'item_1617944105607', [('attribute_value_mlt', [])]), ('add', 'item_1617944105607', [('attribute_value_mlt', [])]), ('add', 'item_1617944105607.attribute_value_mlt', [(0, {})]), ('add', 'item_1617944105607.attribute_value_mlt', [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256015892', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256015892', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256027296', 'xxxxxx')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256027296', 'xxxxxx')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256029891', 'kakenhi')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256015892', 0], [('subitem_1551256029891', 'kakenhi')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256037922', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0], [('subitem_1551256037922', [])]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922'], [(0, {})]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256042287', 'Degree Grantor Name')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256042287', 'Degree Grantor Name')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256047619', 'en')]), ('add', ['item_1617944105607', 'attribute_value_mlt', 0, 'subitem_1551256037922', 0], [('subitem_1551256047619', 'en')]), ('add', '', [('item_title', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', '', [('item_title', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', '', [('item_type_id', '15')]), ('add', '', [('item_type_id', '15')]), ('add', '', [('owner', 1)]), ('add', '', [('owner', 1)]), ('add', '', [('path', [])]), ('add', '', [('path', [])]), ('add', 'path', [(0, '1661517684078')]), ('add', 'path', [(0, '1661517684078')]), ('add', '', [('pubdate', {})]), ('add', '', [('pubdate', {})]), ('add', 'pubdate', [('attribute_name', 'PubDate')]), ('add', 'pubdate', [('attribute_name', 'PubDate')]), ('add', 'pubdate', [('attribute_value', '2021-08-06')]), ('add', 'pubdate', [('attribute_value', '2021-08-06')]), ('add', '', [('publish_date', '2021-08-06')]), ('add', '', [('publish_date', '2021-08-06')]), ('add', '', [('publish_status', '0')]), ('add', '', [('publish_status', '0')]), ('add', '', [('relation_version_is_last', True)]), ('add', '', [('relation_version_is_last', True)]), ('add', '', [('title', [])]), ('add', '', [('title', [])]), ('add', 'title', [(0, 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', 'title', [(0, 'ja_conference paperITEM00000001(public_open_access_open_access_simple)')]), ('add', '', [('weko_shared_ids', [])]), ('add', '', [('weko_shared_ids', [])]), ('remove', '', [('test_1', "")]), ('remove', '', [('test_2', "")])]
            #distination = {'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '753ff0d7-0659-4460-9b1a-fd1ef38467f2'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, 'test_1': {'key1': 'value1'}, 'test_2': [{'key2': 'value2'}]}
            #ret = dep._patch(diff_result,distination)
            #assert ret=={'recid': '13', '$schema': 'https://127.0.0.1/schema/deposits/deposit-v1.0.0.json', '_buckets': {'deposit': '688f2d41-be61-468f-95e2-a06abefdaf60'}, '_deposit': {'id': '13', 'owners': [1], 'status': 'draft'}, '_oai': {'id': 'oai:weko3.example.org:00000013', 'sets': ['1661517684078', '1661517684078']}, 'author_link': ['4', '4'], 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000001(public_open_access_simple)', 'subitem_1551255648112': 'en'}, {}, {}]}, 'item_1617186385884': {'attribute_name': 'Alternative Title', 'attribute_value_mlt': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}, {}, {}]}, 'item_1617186419668': {'attribute_name': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}, {}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}, {}]}, {}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}, {}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {}, {}, {}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}, {}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}, {}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {}, {}, {}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}, {}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {}, {}, {}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}]}, {}, {}, {}]}, 'item_1617186476635': {'attribute_name': 'Access Rights', 'attribute_value_mlt': [{'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, {}]}, 'item_1617186499011': {'attribute_name': 'Rights', 'attribute_value_mlt': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}, {}]}, 'item_1617186609386': {'attribute_name': 'Subject', 'attribute_value_mlt': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}, {}]}, 'item_1617186626617': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}, {}, {}]}, 'item_1617186643794': {'attribute_name': 'Publisher', 'attribute_value_mlt': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}, {}]}, 'item_1617186660861': {'attribute_name': 'Date', 'attribute_value_mlt': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}, {}]}, 'item_1617186702042': {'attribute_name': 'Language', 'attribute_value_mlt': [{'subitem_1551255818386': 'jpn'}, {}]}, 'item_1617186783814': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}, {}]}, 'item_1617186859717': {'attribute_name': 'Temporal', 'attribute_value_mlt': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}, {}]}, 'item_1617186882738': {'attribute_name': 'Geo Location', 'attribute_value_mlt': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}, {}]}, {}]}, 'item_1617186901218': {'attribute_name': 'Funding Reference', 'attribute_value_mlt': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}, {}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}, {}]}, {}]}, 'item_1617186920753': {'attribute_name': 'Source Identifier', 'attribute_value_mlt': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}, {}]}, 'item_1617186941041': {'attribute_name': 'Source Title', 'attribute_value_mlt': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}, {}]}, 'item_1617186959569': {'attribute_name': 'Volume Number', 'attribute_value_mlt': [{'subitem_1551256328147': '1'}, {}]}, 'item_1617186981471': {'attribute_name': 'Issue Number', 'attribute_value_mlt': [{'subitem_1551256294723': '111'}, {}]}, 'item_1617186994930': {'attribute_name': 'Number of Pages', 'attribute_value_mlt': [{'subitem_1551256248092': '12'}, {}]}, 'item_1617187024783': {'attribute_name': 'Page Start', 'attribute_value_mlt': [{'subitem_1551256198917': '1'}, {}]}, 'item_1617187045071': {'attribute_name': 'Page End', 'attribute_value_mlt': [{'subitem_1551256185532': '3'}, {}]}, 'item_1617187112279': {'attribute_name': 'Degree Name', 'attribute_value_mlt': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}, {}]}, 'item_1617187136212': {'attribute_name': 'Date Granted', 'attribute_value_mlt': [{'subitem_1551256096004': '2021-06-30'}, {}]}, 'item_1617187187528': {'attribute_name': 'Conference', 'attribute_value_mlt': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}, {}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}, {}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}, {}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}, {}], 'subitem_1599711813532': 'JPN'}, {}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, {}]}, 'item_1617265215918': {'attribute_name': 'Version Type', 'attribute_value_mlt': [{'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, {}]}, 'item_1617349709064': {'attribute_name': 'Contributor', 'attribute_value_mlt': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}, {}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}, {}, {}, {}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {}, {}, {}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}, {}, {}, {}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}, {}, {}, {}]}, {}]}, 'item_1617349808926': {'attribute_name': 'Version', 'attribute_value_mlt': [{'subitem_1523263171732': 'Version'}, {}]}, 'item_1617351524846': {'attribute_name': 'APC', 'attribute_value_mlt': [{'subitem_1523260933860': 'Unknown'}, {}]}, 'item_1617353299429': {'attribute_name': 'Relation', 'attribute_value_mlt': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}, {}]}, {}]}, 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}, {}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}, {}], 'format': 'text/plain', 'mimetype': 'application/pdf', 'url': {'url': 'https://weko3.example.org/record/13/files/1KB.pdf'}, 'version_id': '7cdce099-fe63-445f-b78b-cf2909a8163f'}, {}]}, 'item_1617610673286': {'attribute_name': 'Rights Holder', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}, {}]}, {}]}, 'item_1617620223087': {'attribute_name': 'Heading', 'attribute_value_mlt': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}, {}, {}]}, 'item_1617944105607': {'attribute_name': 'Degree Grantor', 'attribute_value_mlt': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}, {}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}, {}]}, {}]}, 'item_title': 'ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'item_type_id': '15', 'owner': '1', 'path': ['1661517684078', '1661517684078'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2021-08-06'}, 'publish_date': '2021-08-06', 'publish_status': '0', 'relation_version_is_last': True, 'title': ['ja_conference paperITEM00000001(public_open_access_open_access_simple)', 'ja_conference paperITEM00000001(public_open_access_open_access_simple)'], 'weko_shared_ids': []}

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
    # def add(node, changes):
    # def change(node, changes):
    # def remove(node, changes):

    # def _publish_new(self, id_=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__publish_new -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__publish_new(self,app,location):
        with app.test_request_context():
            dep = WekoDeposit.create({})
            record=dep._publish_new()
            from invenio_records_files.api import Record
            assert isinstance(record,Record)==True



    # def _update_version_id(self, metas, bucket_id):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__update_version_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__update_version_id(self,app,location):
        with app.test_request_context():
            dep = WekoDeposit.create({})
            bucket = Bucket.create(location)
            ret = dep._update_version_id({},bucket.id)
            assert ret==False
            i = 1
            meta =  {"_oai": {"id": "oai:weko3.example.org:000000{:02d}".format(i), "sets": ["{}".format((i % 2) + 1)]}, "path": ["{}".format((i % 2) + 1)], "owner": "1", "recid": "{}".format(i), "title": ["title"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-08-20"}, "_buckets": {"deposit": "3e99cfca-098b-42ed-b8a0-20ddd09b3e02"}, "_deposit": {"id": "{}".format(i), "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0}, "owner": 1, "owners": [1], "status": "draft", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}}, "item_title": "title", "author_link": [], "item_type_id": "1", "publish_date": "2022-08-20", "publish_status": "0", "weko_shared_ids": [], "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": "title", "subitem_1551255648112": "ja"}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}]}, "relation_version_is_last": True, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [
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

    # def publish(self, pid=None, id_=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_publish(self,app,location):
        deposit = WekoDeposit.create({})
        assert deposit['_deposit']['id']
        assert 'draft' == deposit.status
        assert 0 == deposit.revision_id
        deposit.publish()
        assert 'published' == deposit.status
        assert deposit.revision_id==2

    # def publish_without_commit(self, pid=None, id_=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_publish_without_commit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_publish_without_commit(self,app,location):
        with app.test_request_context():
            # es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
            # print(es.cat.indices())
            deposit = WekoDeposit.create({})
            assert deposit['_deposit']['id']
            assert 'draft' == deposit.status
            assert 0 == deposit.revision_id
            deposit.publish_without_commit()
            assert deposit['_deposit']['id']
            assert 'published' == deposit.status
            assert deposit.revision_id==2

    # def create(cls, data, id_=None, recid=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_create(self, app, client, db, location, users, db_activity, db_userprofile):
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
        #login {'email': 'repoadmin@test.org', 'id': 4, 'obj': <User 4>}
        with app.test_request_context():

            login_user = User.query.filter_by(id=4).first()
            with patch("flask_login.utils._get_user", return_value=login_user):
                with patch("flask_security.current_user", return_value=login_user):
                    activity = Activity.query.all()

                    session["activity_info"] = {"activity_id":activity[0].activity_id}
                    data = {"$schema":"https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"}
                    id = uuid.uuid4()
                    deposit = WekoDeposit.create(data, id_=id)
                    assert isinstance(deposit,WekoDeposit)
                    assert deposit['_deposit']['id']=="3"
                    assert 'draft' == deposit.status
                    assert 0 == deposit.revision_id

                    id = uuid.uuid4()
                    deposit = WekoDeposit.create(data, id_=id, recid=100)
                    assert isinstance(deposit,WekoDeposit)
                    assert deposit['_deposit']['id']=="100"
                    assert 'draft' == deposit.status
                    assert 0 == deposit.revision_id

                    with patch("weko_deposit.api.PersistentIdentifier.create",side_effect=BaseException("test_error")):
                        session["activity_info"] = {"activity_id":activity[1].activity_id}
                        data = {"$schema":"https://127.0.0.1/schema/deposits/deposit-v1.0.0.json","_deposit":{"id":"2","owners":[1],"status":"draft","created_by":1}}
                        id = uuid.uuid4()
                        with pytest.raises(BaseException):
                            deposit = WekoDeposit.create(data, id_=id)

    # def update(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update(self, app, users, location, db_index, db_itemtype):
        with app.test_request_context():
            deposit = WekoDeposit.create({})
            assert deposit['_deposit']['id']=="1"
            assert 'draft' == deposit.status
            assert 0 == deposit.revision_id
            deposit.update()
            assert deposit['_deposit']['id']=="1"
            assert 'draft' == deposit.status
            assert 0 == deposit.revision_id

            update_param = {'$schema': '/items/jsonschema/1', 
                            'recid': '1',
                            'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 
                            'owners': [2], 
                            'owner': '2', 
                            'shared_user_ids': [2, 3],
                            'title': 'test deposit', 'lang': 'ja', 
                            'pubdate': '2025-06-07', 
                            'item_1617186331708': [{'subitem_1551255647225': 'test deposit', 'subitem_1551255648112': 'ja'}], 
                            'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'},
                            'status': 'published', 
                            'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}
                            }
            
            update_param_json = json.loads(json.dumps(update_param))
            with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
                deposit.update({'index': ['1'], 'actions': '1'}, update_param_json)
                assert [2, 3] == deposit['weko_shared_ids']

                # 更新されない
                update_param_json = json.loads(json.dumps(update_param))
                deposit.update({'index': ['1'], 'actions': '1'})
                assert [2, 3] == deposit['weko_shared_ids']


    # def clear(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_clear -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_clear(sel,app,db,location,es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']
        es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
        ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
        deposit.clear()
        ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
        assert ret==ret2


    # def delete(self, force=True, pid=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete(sel,app,db,location,es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']
        es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
        ret = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id)
        deposit.delete()
        ret2 = es.get_source(index=app.config['INDEXER_DEFAULT_INDEX'], doc_type=app.config['INDEXER_DEFAULT_DOC_TYPE'],id=deposit.id,ignore = [404])
        assert ret2=={'error': {'root_cause': [{'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(deposit.id)}], 'type': 'resource_not_found_exception', 'reason': 'Document not found [test-weko-item-v1.0.0]/[item-v1.0.0]/[{}]'.format(deposit.id)}, 'status': 404}

    # def commit(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_commit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_commit(sel,app,db,location, db_index, db_itemtype, mocker):
        app.config["WEKO_SCHEMA_JPCOAR_V2_SCHEMA_NAME"] = 'jpcoar_mapping'
        app.config["WEKO_SCHEMA_JPCOAR_V2_RESOURCE_TYPE_REPLACE"] = {
            'periodical':'journal',
            'interview':'other',
            'internal report':'other',
            'report part':'other',
        }
        mock_task = mocker.patch("weko_deposit.tasks.extract_pdf_and_update_file_contents")
        mock_task.apply_async = MagicMock()
        with app.test_request_context():
            deposit = WekoDeposit.create({})
            assert deposit['_deposit']['id']=="1"
            assert 'draft' == deposit.status
            assert 0 == deposit.revision_id
            deposit.commit()
            assert deposit['_deposit']['id']=="1"
            assert 'draft' == deposit.status
            assert 2 == deposit.revision_id

            # exist feedback_mail_list
            deposit = WekoDeposit.create({})
            item_id = deposit.pid.object_uuid
            index_obj = {'index': ['1'], 'actions': 'private'}
            data = {'pubdate': '2023-12-07', 'item_1617186331708': [{'subitem_1551255647225': 'test', 'subitem_1551255648112': 'ja'}], 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1, 'title': 'test', 'lang': 'ja', 'deleted_items': ['item_1617186385884', 'item_1617186419668', 'item_1617186499011', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186660861', 'item_1617186702042', 'item_1617186783814', 'item_1617186859717', 'item_1617186882738', 'item_1617186901218', 'item_1617186920753', 'item_1617186941041', 'item_1617187112279', 'item_1617187187528', 'item_1617349709064', 'item_1617353299429', 'item_1617605131499', 'item_1617610673286', 'item_1617620223087', 'item_1617944105607', 'item_1617187056579', 'approval1', 'approval2'], '$schema': '/items/jsonschema/1'}
            deposit.update(index_obj,data)
            deposit.commit()
            FeedbackMailList.update(item_id,[{"email":"test.taro@test.org","author_id":""}])
            db.session.commit()
            fd = FeedbackMailList.get_mail_list_by_item_id(item_id)
            assert fd == [{"email":"test.taro@test.org","author_id":""}]

            # not exist feedback_mail_list
            FeedbackMailList.delete(item_id)
            deposit.commit()
            db.session.commit()
            fd = FeedbackMailList.get_mail_list_by_item_id(item_id)
            assert fd == []


    # def newversion(self, pid=None, is_draft=False):
    #             # NOTE: We call the superclass `create()` method, because
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_newversion -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_newversion(self, app, db, location, db_itemtype, es_records, users, mocker):
        _, records = es_records
        record = records[0]
        depid = record['depid']
        recid = record['recid']

        deposit = record['deposit']

        with patch("weko_deposit.api.WekoDeposit.is_published",return_value=None):
            with pytest.raises(PIDInvalidAction):
                ret = deposit.newversion()

        with pytest.raises(AttributeError):
            ret = deposit.newversion()

        # No row was found for one()
        ret = deposit.newversion(depid,True)
        assert ret==None

        # No row was found for one()
        ret = deposit.newversion(depid)
        assert ret==None

        # PIDResolveRESTError
        rec_uuid = uuid.uuid4()

        recid_1 = PersistentIdentifier.create('recid', "11", object_type='rec', object_uuid=rec_uuid, status=PIDStatus.REGISTERED)
        depid_1 = PersistentIdentifier.create('depid', "11", object_type='rec', object_uuid=rec_uuid, status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(recid_1, depid_1, 2, 0)
        es_records[1][0]['record_data']['owners'] = [1]
        es_records[1][0]['record_data']['created_by'] = 1
        es_records[1][0]['record_data']['recid'] = 11
        es_records[1][0]['record_data']['_deposit']['id'] = 11
        es_records[1][0]['record_data']['_deposit']['pid']['value'] = 11
        es_records[1][0]['item_data']['owners'] = [1]
        es_records[1][0]['item_data']['created_by'] = 1
        es_records[1][0]['item_data']['id'] = 11
        es_records[1][0]['item_data']['pid']['value'] = 11
        es_records[1][0]['item_data']['id'] = 11
        rec = WekoRecord.create(es_records[1][0]['record_data'], id_=rec_uuid)
        dep = WekoDeposit(rec, rec.model)
        ItemsMetadata.create(es_records[1][0]['item_data'], id_=rec_uuid)
        rec_meta = RecordMetadata(id=rec_uuid, json=es_records[1][0]['record_data'], version_id=1)
        record_metadata = RecordMetadata.query.filter_by(id=rec_uuid).first()

        db.session.add(recid_1)
        db.session.add(depid_1)
        db.session.add(rel)
        db.session.commit()

        with app.test_request_context():
            with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
                with patch("flask_security.current_user", return_value=users[2]["obj"]):
                    with patch("weko_index_tree.api.Indexes.get_path_list", return_value=[2]):
                        session["activity_info"] = {"activity_id":0}

                        ret = deposit.newversion(depid_1)
                        assert '11.1' == ret['recid']
                        assert 1 == ret['owner']
                        assert [1] == ret['owners']
                        assert [] == ret['weko_shared_ids']
                        assert '11.1' == ret['_deposit']['id']
                        assert 1 == ret['_deposit']['owner']
                        assert [1] == ret['_deposit']['owners']
                        assert 5 == ret['_deposit']['created_by']
                        assert [] == ret['_deposit']['weko_shared_ids']

                        # return None
                        depid_none = PersistentIdentifier.create('depid', "12", object_type='rec', object_uuid=rec_uuid, status=PIDStatus.REGISTERED)
                        assert None == deposit.newversion(depid_none)

                        # is_draft = true
                        ret = deposit.newversion(depid_1, is_draft=True)
                        assert '11.0' == ret['recid']
                        assert '11.0' == ret['_deposit']['id']


    # def get_content_files(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_get_content_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_content_files(sel,app,db,location,es_records):
        # Setup common mocks
        mock_self = MagicMock()
        mock_self.recid = "123"
        mock_self.jrc = {}
        mock_self.files = []
        # Mock external dependencies
        with patch("weko_workflow.utils.get_url_root", return_value="http://test.org"), \
            patch("weko_workflow.utils.get_non_extract_files_by_recid", return_value=[]):

            # Configure app config mocks
            app.config.WEKO_MIMETYPE_WHITELIST_FOR_ES = ["text/plain", "application/pdf"]
            app.config.WEKO_DEPOSIT_TEXTMIMETYPE_WHITELIST_FOR_ES = ["text/plain"]
            app.config.WEKO_DEPOSIT_FILESIZE_LIMIT = 1024

            # No file data
            mock_self.get_file_data.return_value = None
            result = WekoDeposit.get_content_files(mock_self)
            assert result == {}

            # Empty file data list
            mock_self.get_file_data.return_value = []
            result = WekoDeposit.get_content_files(mock_self)
            assert result == {}

            # Text file extraction (success)
            mock_file = MagicMock()
            mock_file.obj = MagicMock()
            mock_file.obj.key = "test.txt"
            mock_file.obj.mimetype = "text/plain"
            mock_file.obj.version_id = "1"
            mock_file.obj.file = MagicMock()
            mock_file.obj.file.storage.return_value.open.return_value = BytesIO(b"Hello World")

            mock_self.files = [mock_file]
            mock_self.non_extract = []
            mock_self.get_file_data.return_value = [{"filename": "test.txt", "url": {}}]

            with patch("chardet.detect", return_value={"encoding": "utf-8"}):
                result = WekoDeposit.get_content_files(mock_self)
                assert result == {}
                assert "content" in mock_self.jrc
                assert mock_self.jrc["content"][0]["attachment"]["content"] == "Hello World"

            # Text file extraction (success) mimType is not in the WEKO_DEPOSIT_TEXTMIMETYPE_WHITELIST_FOR_ES
            mock_file = MagicMock()
            mock_file.obj = MagicMock()
            mock_file.obj.key = "test.txt"
            mock_file.obj.mimetype = "application/msword"
            mock_file.obj.version_id = "1"
            mock_file.obj.file = MagicMock()
            mock_file.obj.file.storage.return_value.open.return_value = BytesIO(b"Hello World")

            mock_self.files = [mock_file]
            mock_self.non_extract = []
            mock_self.get_file_data.return_value = [{"filename": "test.txt", "url": {}}]

            with patch("chardet.detect", return_value={"encoding": "utf-8"}):
                result = WekoDeposit.get_content_files(mock_self)
                assert result != {}
                assert mock_self.jrc["content"][0]["attachment"]["content"] == ""

            # non_extract attribute does not exist
            mock_self = MagicMock()
            mock_self.recid = "123"
            mock_self.jrc = {}
            del mock_self.non_extract  # Ensure attribute doesn't exist

            mock_file = MagicMock()
            mock_file.obj = MagicMock()
            mock_file.obj.key = "test.txt"
            mock_file.obj.mimetype = "text/plain"
            mock_file.obj.version_id = "1"
            mock_file.obj.file = MagicMock()
            mock_file.obj.file.storage.return_value.open.return_value = BytesIO(b"Hello World")

            mock_self.files = [mock_file]
            mock_self.get_file_data.return_value = [{"filename": "test.txt", "url": {}}]

            with patch("weko_workflow.utils.get_non_extract_files_by_recid", return_value=[]), \
                patch("chardet.detect", return_value={"encoding": "utf-8"}):
                result = WekoDeposit.get_content_files(mock_self)
                assert result == {}
                assert "content" in mock_self.jrc
                # Should extract content since non_extract is None and get_non_extract_files_by_recid returns empty list
                assert mock_self.jrc["content"][0]["attachment"]["content"] == "Hello World"

            # File in non_extract list
            mock_self.non_extract = ["test.txt"]
            mock_file = MagicMock()
            mock_file.obj = MagicMock()
            mock_file.obj.key = "test.txt"
            mock_file.obj.mimetype = "text/plain"
            mock_file.obj.version_id = "1"

            mock_self.files = [mock_file]
            mock_self.get_file_data.return_value = [{"filename": "test.txt", "url": {}}]

            result = WekoDeposit.get_content_files(mock_self)
            assert result == {}
            assert mock_self.jrc["content"][0]["attachment"] == {}


    # def get_pdf_info(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_get_pdf_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_pdf_info(sel, app, db, location):
        rec_uuid = uuid.uuid4()
        pdf_files, deposit = create_record_with_pdf(rec_uuid, 1)
        test = {}
        for file_name, file_obj in pdf_files.items():
            test[file_name]={"uri":file_obj.obj.file.uri,"size":file_obj.obj.file.size}
        res = deposit.get_pdf_info()
        assert res == test


    # def get_file_data(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_get_file_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_file_data(sel,app,db,location,es_records):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        ret = deposit.get_file_data()
        assert ret==[]

    # def save_or_update_item_metadata(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_save_or_update_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_save_or_update_item_metadata(self, app, db, location, es_records, mocker):
        indexer, records = es_records
        record = records[0]
        recid = record['recid']
        depid = record['depid']
        deposit = record['deposit']

        deposit.data = record['record_data']
        # len(deposit_owners)>0 and owner_id
        deposit['_deposit']['owners'] = [1]
        deposit['owner'] = 1
        deposit.save_or_update_item_metadata()
        assert 1 == deposit.data['owner']
        assert [1] == deposit.data['owners']

        # len(deposit_owners)==0 and owner_id
        deposit['_deposit']['owners'] = []
        deposit['owner'] = 1
        deposit.save_or_update_item_metadata()
        assert ItemMetadata.query.filter_by(id=recid.object_uuid).first()
        assert [1] == deposit.data['owners']

        # len(deposit_owners)>0 and not owner_id
        deposit['_deposit']['owners'] = [1]
        deposit['owner'] = None
        deposit.save_or_update_item_metadata()
        assert [1] ==  deposit.data['owners']

        # len(deposit_owners)==0 and not owner_id
        deposit['_deposit']['owners'] = []
        deposit.pop('owner')
        deposit.save_or_update_item_metadata()
        assert [1] == deposit.data['owners']
        assert 1 == deposit.data['owner']

        # deleted_items
        deposit['_deposit']['owners'] = [1]
        deposit['owner'] = 1
        deposit.data['deleted_items'] = {"item_1617258105262": {"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}}
        deposit.save_or_update_item_metadata()
        metadata = ItemsMetadata.get_record(deposit.id)
        assert 'item_1617258105262' not in metadata


    # def get_file_data_with_item_type(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_get_file_data_with_item_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_file_data_with_item_type(sel,app,db,location,es_records,db_itemtype):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']
        ret = deposit.get_file_data(item_type=db_itemtype["item_type"])
        assert ret==[]

    # def delete_old_file_index(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_old_file_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_old_file_index(sel,app,db,location,es_records):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        # not is_edit
        deposit.delete_old_file_index()
        # is_edit
        deposit.is_edit=True
        deposit.delete_old_file_index()



    # def delete_item_metadata(self, data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_item_metadata(self, app, db, location, es_records):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        item_data = record['item_data']

        deposit.delete_item_metadata(item_data)
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_record_data_from_act_temp -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_record_data_from_act_temp(sel,app,db,db_activity,es_records):
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
                    title='test_title', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
        db.session.add(activity)
        db.session.commit()
        result = deposit.record_data_from_act_temp()
        assert result == None

        # exist activity.temp_data
        temp_data = {"metainfo": {"pubdate": "2023-10-10", "none_str":"","empty_list":[],"item_1617186331708": [{"subitem_1551255647225": "test_title", "subitem_1551255648112": "ja"}], "item_1617186385884": [{"subitem_1551255720400": "alter title"}], "item_1617186419668": [{"creatorAffiliations": [{"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}], "creatorAlternatives": [{}], "creatorMails": [{}], "creatorNames": [{}], "familyNames": [{"familyName": "test_family_name"}], "givenNames": [{}], "nameIdentifiers": [{}]}], "item_1617186499011": [{}], "item_1617186609386": [{}], "item_1617186626617": [{}], "item_1617186643794": [{}], "item_1617186660861": [{}], "item_1617186702042": [{}], "item_1617186783814": [{}], "item_1617186859717": [{}], "item_1617186882738": [{"subitem_geolocation_place": [{}]}], "item_1617186901218": [{"subitem_1522399412622": [{}], "subitem_1522399651758": [{}]}], "item_1617186920753": [{}], "item_1617186941041": [{}], "item_1617187112279": [{}], "item_1617187187528": [{"subitem_1599711633003": [{}], "subitem_1599711660052": [{}], "subitem_1599711758470": [{}], "subitem_1599711788485": [{}]}], "item_1617349709064": [{"contributorAffiliations": [{"contributorAffiliationNameIdentifiers": [{}], "contributorAffiliationNames": [{}]}], "contributorAlternatives": [{}], "contributorMails": [{}], "contributorNames": [{}], "familyNames": [{}], "givenNames": [{}], "nameIdentifiers": [{}]}], "item_1617353299429": [{"subitem_1523320863692": [{}]}], "item_1617605131499": [{"date": [{}], "fileDate": [{}], "filesize": [{}]}], "item_1617610673286": [{"nameIdentifiers": [{}], "rightHolderNames": [{}]}], "item_1617620223087": [{}], "item_1617944105607": [{"subitem_1551256015892": [{}], "subitem_1551256037922": [{}]}], "item_1617187056579": {"bibliographic_titles": [{}]}, "shared_user_ids": [], "item_1617258105262": {"resourcetype": "conference paper", "resourceuri": "http://purl.org/coar/resource_type/c_5794"}}, "files": [], "endpoints": {"initialization": "/api/deposits/items"}}
        activity.temp_data=json.dumps(temp_data)
        db.session.merge(activity)
        db.session.commit()
        result = deposit.record_data_from_act_temp()
        test = {"pubdate": "2023-10-10","item_1617186331708": [{"subitem_1551255647225": "test_title","subitem_1551255648112": "ja"}],"item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"familyNames": [{"familyName": "test_family_name"}]}],"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"},"deleted_items": ["none_str","empty_list","item_1617186499011","item_1617186609386","item_1617186626617","item_1617186643794","item_1617186660861","item_1617186702042","item_1617186783814","item_1617186859717","item_1617186882738","item_1617186901218","item_1617186920753","item_1617186941041","item_1617187112279","item_1617187187528","item_1617349709064","item_1617353299429","item_1617605131499","item_1617610673286","item_1617620223087","item_1617944105607","item_1617187056579",'shared_user_ids'],"$schema": "/items/jsonschema/1","title": "test_title","lang": "ja"}
        assert result == test

        # title is dict
        temp_data = {"metainfo": {"pubdate": "2023-10-10","none_str": "","empty_list": [],"item_1617186331708": {"subitem_1551255647225": "test_title","subitem_1551255648112": "ja"},"item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"creatorAffiliations": [{"affiliationNameIdentifiers": [{}],"affiliationNames": [{}]}],"creatorAlternatives": [{}],"creatorMails": [{}],"creatorNames": [{}],"familyNames": [{"familyName": "test_family_name"}],"givenNames": [{}],"nameIdentifiers": [{}]}],"item_1617186499011": [{}],"item_1617186609386": [{}],"item_1617186626617": [{}],"item_1617186643794": [{}],"item_1617186660861": [{}],"item_1617186702042": [{}],"item_1617186783814": [{}],"item_1617186859717": [{}],"item_1617186882738": [{"subitem_geolocation_place": [{}]}],"item_1617186901218": [{"subitem_1522399412622": [{}],"subitem_1522399651758": [{}]}],"item_1617186920753": [{}],"item_1617186941041": [{}],"item_1617187112279": [{}],"item_1617187187528": [{"subitem_1599711633003": [{}],"subitem_1599711660052": [{}],"subitem_1599711758470": [{}],"subitem_1599711788485": [{}]}],"item_1617349709064": [{"contributorAffiliations": [{"contributorAffiliationNameIdentifiers": [{}],"contributorAffiliationNames": [{}]}],"contributorAlternatives": [{}],"contributorMails": [{}],"contributorNames": [{}],"familyNames": [{}],"givenNames": [{}],"nameIdentifiers": [{}]}],"item_1617353299429": [{"subitem_1523320863692": [{}]}],"item_1617605131499": [{"date": [{}],"fileDate": [{}],"filesize": [{}]}],"item_1617610673286": [{"nameIdentifiers": [{}],"rightHolderNames": [{}]}],"item_1617620223087": [{}],"item_1617944105607": [{"subitem_1551256015892": [{}],"subitem_1551256037922": [{}]}],"item_1617187056579": {"bibliographic_titles": [{}]},"shared_user_ids": [],"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"}},"files": [],"endpoints": {"initialization": "/api/deposits/items"}}
        activity.temp_data=json.dumps(temp_data)
        db.session.merge(activity)
        db.session.commit()
        result = deposit.record_data_from_act_temp()
        test = {"pubdate": "2023-10-10","item_1617186331708": {"subitem_1551255647225": "test_title","subitem_1551255648112": "ja"},"item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"familyNames": [{"familyName": "test_family_name"}]}],"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"},"deleted_items": ["none_str","empty_list","item_1617186499011","item_1617186609386","item_1617186626617","item_1617186643794","item_1617186660861","item_1617186702042","item_1617186783814","item_1617186859717","item_1617186882738","item_1617186901218","item_1617186920753","item_1617186941041","item_1617187112279","item_1617187187528","item_1617349709064","item_1617353299429","item_1617605131499","item_1617610673286","item_1617620223087","item_1617944105607","item_1617187056579",'shared_user_ids'],"$schema": "/items/jsonschema/1","title": "test_title","lang": "ja"}
        assert result == test

        # title data is not exist
        temp_data = {"metainfo": {"pubdate": "2023-10-10","none_str": "","empty_list": [],"item_1617186331708": [],"item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"creatorAffiliations": [{"affiliationNameIdentifiers": [{}],"affiliationNames": [{}]}],"creatorAlternatives": [{}],"creatorMails": [{}],"creatorNames": [{}],"familyNames": [{"familyName": "test_family_name"}],"givenNames": [{}],"nameIdentifiers": [{}]}],"item_1617186499011": [{}],"item_1617186609386": [{}],"item_1617186626617": [{}],"item_1617186643794": [{}],"item_1617186660861": [{}],"item_1617186702042": [{}],"item_1617186783814": [{}],"item_1617186859717": [{}],"item_1617186882738": [{"subitem_geolocation_place": [{}]}],"item_1617186901218": [{"subitem_1522399412622": [{}],"subitem_1522399651758": [{}]}],"item_1617186920753": [{}],"item_1617186941041": [{}],"item_1617187112279": [{}],"item_1617187187528": [{"subitem_1599711633003": [{}],"subitem_1599711660052": [{}],"subitem_1599711758470": [{}],"subitem_1599711788485": [{}]}],"item_1617349709064": [{"contributorAffiliations": [{"contributorAffiliationNameIdentifiers": [{}],"contributorAffiliationNames": [{}]}],"contributorAlternatives": [{}],"contributorMails": [{}],"contributorNames": [{}],"familyNames": [{}],"givenNames": [{}],"nameIdentifiers": [{}]}],"item_1617353299429": [{"subitem_1523320863692": [{}]}],"item_1617605131499": [{"date": [{}],"fileDate": [{}],"filesize": [{}]}],"item_1617610673286": [{"nameIdentifiers": [{}],"rightHolderNames": [{}]}],"item_1617620223087": [{}],"item_1617944105607": [{"subitem_1551256015892": [{}],"subitem_1551256037922": [{}]}],"item_1617187056579": {"bibliographic_titles": [{}]},"shared_user_ids": [],"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"}},"files": [],"endpoints": {"initialization": "/api/deposits/items"}}
        activity.temp_data=json.dumps(temp_data)
        db.session.merge(activity)
        db.session.commit()
        result = deposit.record_data_from_act_temp()
        test = {"pubdate": "2023-10-10","item_1617186385884": [{"subitem_1551255720400": "alter title"}],"item_1617186419668": [{"familyNames": [{"familyName": "test_family_name"}]}],"item_1617258105262": {"resourcetype": "conference paper","resourceuri": "http://purl.org/coar/resource_type/c_5794"},"deleted_items": ["none_str","empty_list","item_1617186331708","item_1617186499011","item_1617186609386","item_1617186626617","item_1617186643794","item_1617186660861","item_1617186702042","item_1617186783814","item_1617186859717","item_1617186882738","item_1617186901218","item_1617186920753","item_1617186941041","item_1617187112279","item_1617187187528","item_1617349709064","item_1617353299429","item_1617605131499","item_1617610673286","item_1617620223087","item_1617944105607","item_1617187056579",'shared_user_ids'],"$schema": "/items/jsonschema/1","title": "test_title","lang": ""}
        assert result == test

        # not exist title_parent_key in path
        mock_path = {
          "title": {},
          "pubDate": ""
        }
        with patch("weko_items_autofill.utils.get_title_pubdate_path",return_value=mock_path):
            result = deposit.record_data_from_act_temp()
            assert result == test

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

        assert 'attribute_name' not in deposit
        assert [] == deposit['weko_shared_ids']

    # def convert_item_metadata(self, index_obj, data=None):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_convert_item_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_convert_item_metadata(self, app, db, db_itemtype, es_records, users):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        pid = record['depid']
        cid = record['recid']
        record_data = record['item_data']
        index_obj = {'index': ['1'], 'actions': '1'}
        index_obj_1 = {'index': ['1'], 'actions': '0'}
        test1 = OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'}), 
                            ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}]}), 
                            ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}), 
                            ('item_title', 'title'), ('item_type_id', '1'), ('control_number', 1), ('author_link', []), 
                            ('_oai', {'id': '1'}), ('weko_shared_ids', []), ('owner', 1), ('owners', [1]), ('publish_date', '2022-08-20'), 
                            ('title', ['title']), ('relation_version_is_last', True), ('path', ['1']), ('publish_status','0')])
        test2 = None

        with patch("weko_index_tree.api.Indexes.get_path_list", return_value=['1']):

            ret1,ret2 = deposit.convert_item_metadata(index_obj,record_data)
            assert set(ret1) == set(test1)
            assert ret2 == test2

            with patch("weko_deposit.api.RedisConnection.connection",side_effect=BaseException("test_error")):
                with pytest.raises(HTTPException) as httperror:
                    ret = deposit.convert_item_metadata(index_obj,{})
                    assert httperror.value.code == 500
                    assert httperror.value.data == "Failed to register item!"

            with patch("weko_deposit.api.json_loader",side_effect=RuntimeError):
                with pytest.raises(RuntimeError):
                    ret = deposit.convert_item_metadata(index_obj,record_data)
            with patch("weko_deposit.api.json_loader",side_effect=ValueError):
                with pytest.raises(ValueError):
                    deposit.convert_item_metadata(index_obj,record_data)
            with patch("weko_deposit.api.json_loader",side_effect=BaseException("test_error")):
                with pytest.raises(HTTPException) as httperror:
                    ret = deposit.convert_item_metadata(index_obj,record_data)
                    assert httperror.value.code == 500
                    assert httperror.value.data == "MAPPING_ERROR"

            with patch("weko_deposit.api.WekoDeposit.convert_type_shared_user_ids",return_value={}):
                record['item_data']['shared_user_ids'] = []
                deposit = record['deposit']
                record_data = record['item_data']
                ret3, _ = deposit.convert_item_metadata(index_obj, record_data)
                assert ret3['weko_shared_ids'] == []
            with app.test_client() as client:
                # ログインする
                response = client.post(url_for_security('login'),
                                   data={'email': users[0]["email"], 'password': '123456'},
                                   environ_base={'REMOTE_ADDR': '127.0.0.1'})
                assert response.status_code == 302
                record['item_data']['shared_user_ids'] = []
                deposit = record['deposit']
                record_data = record['item_data']
                ret3, _ = deposit.convert_item_metadata(index_obj, record_data)
                assert ret3['weko_shared_ids'] == []

            record['item_data']['shared_user_ids'] = []
            deposit = record['deposit']
            record_data = record['item_data']
            ret3, _ = deposit.convert_item_metadata(index_obj, record_data)
            assert ret3['weko_shared_ids'] == []

            record['item_data']['shared_user_ids'] = [2,3]
            deposit = record['deposit']
            record_data = record['item_data']
            ret3, _ = deposit.convert_item_metadata(index_obj, record_data)
            assert ret3['weko_shared_ids'] == [2,3]

            # data = None
            with pytest.raises(BaseException):
                record['item_data']['shared_user_ids'] = []
                deposit = record['deposit']
                ret, _ = deposit.convert_item_metadata(index_obj)
                assert error.value.code == 500

            # data = None and radis exist
            redis_connection = RedisConnection()
            datastore = redis_connection.connection(db=app.config['CACHE_REDIS_DB'], kv = True)
            cache_key = app.config['WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(pid_value=deposit.pid.pid_value)
            print("cache_key:{}".format(cache_key))
            datastore.put(cache_key, json.dumps(record['item_data']).encode('utf-8'))
            deposit = record['deposit']
            ret, _ = deposit.convert_item_metadata(index_obj)
            assert ret['weko_shared_ids'] == []

            # actions == 'publish'
            deposit = record['deposit']
            record_data = record['item_data']
            ret, _ = deposit.convert_item_metadata(index_obj_1, record_data)
            assert ret['publish_status'] == '0'

            # 'shared_user_ids' in self
            deposit = record['deposit']
            deposit['shared_user_ids'] = [1]
            record_data = record['item_data']
            ret, _ = deposit.convert_item_metadata(index_obj, record_data)
            assert 'shared_user_ids' not in ret

        with patch("weko_index_tree.api.Indexes.get_path_list", return_value=[]):
            with pytest.raises(PIDResolveRESTError) as error:
                ret = deposit.convert_item_metadata(index_obj, record_data)
                assert error.value.code == 500
                assert error.value.data == "Any tree index has been deleted"

    # def _convert_description_to_object(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__convert_description_to_object -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__convert_description_to_object(sel,app,db,location,es_records):
        _, records = es_records
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
    # def _convert_jpcoar_data_to_es(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__convert_jpcoar_data_to_es -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__convert_jpcoar_data_to_es(sel,app,db,location,es_records):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        deposit._convert_jpcoar_data_to_es()

    # def _convert_data_for_geo_location(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test__convert_data_for_geo_location -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__convert_data_for_geo_location(sel,app,db,location,es_records):
        _, records = es_records
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

    #         def _convert_geo_location(value):
    #         def _convert_geo_location_box():

    # def delete_by_index_tree_id(cls, index_id: str, ignore_items: list = []):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_by_index_tree_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_by_index_tree_id(sel,app,db,location,es_records):
        def check_status(pid, status):
            assert PersistentIdentifier.get('depid', pid).status == status

        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        deposit.delete_by_index_tree_id('1',['2'])
        check_status(2, "R")

        time.sleep(1)
        deposit.delete_by_index_tree_id('1',[])
        check_status(2, "D")

        # not delete item
        deposit.delete_by_index_tree_id('3',[]) # 10.1 in 3
        check_status(10, "R")

        # delete item
        deposit.delete_by_index_tree_id('4',[]) # 10, 10.2 in 4
        check_status(10, "D")

    # def update_pid_by_index_tree_id(self, path):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_pid_by_index_tree_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_pid_by_index_tree_id(sel,app,db,location,es_records):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        assert deposit.update_pid_by_index_tree_id('1')==True

    # def update_item_by_task(self, *args, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_item_by_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_item_by_task(sel,app,db,location,es_records):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        record_data = record['record_data']
        ret = deposit.update_item_by_task()
        assert ret==deposit

    # def delete_es_index_attempt(self, pid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_es_index_attempt -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_es_index_attempt(sel,app,db,location):
        deposit = WekoDeposit.create({})
        db.session.commit()
        deposit.delete_es_index_attempt(deposit.pid)

    # def update_author_link_and_weko_link(self, author_link):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_author_link_and_weko_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_author_link_and_weko_link(sel,app,db,location,es_records, mocker):
        with patch("weko_deposit.api.WekoIndexer.update_author_link_and_weko_link") as mocker_indexer_update:
            _, records = es_records
            record = records[0]
            deposit = record['deposit']
            assert deposit.update_author_link_and_weko_link([], {"1":"123"})==None
            mocker_indexer_update.assert_not_called()
            assert deposit.update_author_link_and_weko_link(["1"], {})==None
            mocker_indexer_update.assert_not_called()
            assert deposit.update_author_link_and_weko_link(["1"], {"1":"123"})==None
            mocker_indexer_update.assert_called()


    # def update_feedback_mail(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_feedback_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_feedback_mail(sel,app,db,location,es_records, mocker):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        assert deposit.update_feedback_mail()==None

        mail_list = [{'email': 'test_email', 'author_id': ''}]
        with patch('weko_deposit.api.FeedbackMailList.get_mail_list_by_item_id', return_value=mail_list):
            mock = mocker.patch('weko_deposit.api.WekoIndexer.update_feedback_mail_list' , return_value=make_response())
            deposit.update_feedback_mail()
            mock.assert_called()

    # def remove_feedback_mail(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_remove_feedback_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_remove_feedback_mail(sel,app,db,location,es_records):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        assert deposit.remove_feedback_mail()==None

    # def update_request_mail(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_update_request_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_request_mail(sel,app,db,location,es_records,mocker):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        assert deposit.update_request_mail()==None
        with patch("weko_deposit.api.RequestMailList.get_mail_list_by_item_id", return_value=[{'email': 'wekosoftware@nii.ac.jp', 'author_id': ''}]):
            mock = mocker.patch('weko_deposit.api.WekoIndexer.update_request_mail_list' , return_value=make_response())
            deposit.update_request_mail()
            mock.assert_called()

    # def remove_request_mail(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_remove_request_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_remove_request_mail(sel,app,db,location,es_records,mocker):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        mock = mocker.patch('weko_deposit.api.WekoIndexer.update_request_mail_list' , return_value=make_response())
        deposit.remove_request_mail()
        mock.assert_called()

    # def clean_unuse_file_contents(self, item_id, pre_object_versions,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_clean_unuse_file_contents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_clean_unuse_file_contents(sel,app,db,location,es_records):
        _, records = es_records
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


    # def merge_data_to_record_without_version(self, pid, keep_version=False,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_merge_data_to_record_without_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_merge_data_to_record_without_version(sel,app,db,location,es_records):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        recid = record['recid']

        with patch('weko_deposit.api.Indexes.get_path_list', return_value=['2']):
            assert deposit.merge_data_to_record_without_version(recid)

    # def prepare_draft_item(self, recid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_prepare_draft_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_prepare_draft_item(sel,app,db,location,es_records):
        _, records = es_records
        record = records[0]
        deposit = record['deposit']
        recid = record['recid']
        with app.test_request_context():
            with patch("weko_deposit.api.WekoDeposit.newversion",return_value="new_version"):
                assert deposit.prepare_draft_item(recid)=="new_version"

    # def delete_content_files(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_delete_content_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_delete_content_files(sel,app,db,location,es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']

        ret = indexer.get_metadata_by_item_id(deposit.id)
        # 正しくない手法だが、Elasticsearchの結果を前提としている
        deposit.jrc = copy.deepcopy(ret['_source'])
        deposit.delete_content_files()
        assert deposit.jrc==ret['_source']

    # def convert_type_shared_user_ids(cls, data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoDeposit::test_convert_type_shared_user_ids -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_convert_type_shared_user_ids(self, app, db, location, es_records):
        indexer, records = es_records
        record = records[0]
        deposit = record['deposit']
        
        data = {'shared_user_ids': [1,2]}
        ret = deposit.convert_type_shared_user_ids(data)
        assert [1,2] == ret['shared_user_ids']

        data1 = {'shared_user_ids': [{'user':1}, {'user':2}]}
        ret = deposit.convert_type_shared_user_ids(data1)
        assert [1,2] == ret['shared_user_ids']

        data2 = {}
        ret = deposit.convert_type_shared_user_ids(data2)
        assert [] == ret['shared_user_ids']

# class WekoRecord(Record):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
class TestWekoRecord:
    #     def pid(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid(self,es_records):
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

    #     def pid_recid(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_recid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_recid(self,es_records):
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



    #     def hide_file(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_hide_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_hide_file(self,es_records):
        indexer, results = es_records
        result = results[0]
        record = result['record']
        assert record.hide_file==False

    #     def navi(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_navi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_navi(self,app,users,es_records):
        record = WekoRecord({})
        with app.test_request_context():
            assert record.navi==[]
        indexer, results = es_records
        result = results[0]
        record = result['record']
        # assert record.navi==[]
        with app.test_request_context(query_string={"community":"test_com"}):
            assert record.navi==[]

    #     def item_type_info(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_item_type_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_item_type_info(self,app,es_records):
        record = WekoRecord({})
        with app.test_request_context():
            with pytest.raises(AttributeError):
                assert record.item_type_info==""
        indexer, results = es_records
        result = results[0]
        record = result['record']
        assert record.item_type_info=='テストアイテムタイプ(1)'

    #     def switching_language(data):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_switching_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_switching_language(self,app,es_records):
        record = WekoRecord({})
        # language = current_language
        with app.test_request_context(headers=[('Accept-Language', 'en')]):
            data = [{"language":"en","title":"test_title"}]
            result = record.switching_language(data)
            assert result == "test_title"
        # language != current_language, language=en
        with app.test_request_context(headers=[('Accept-Language', 'ja')]):
            data = [{"language":"en","title":"test_title"}]
            result = record.switching_language(data)
            assert result == "test_title"
        # language != en, exist language
        with app.test_request_context(headers=[('Accept-Language', 'da')]):
            data = [{"language":"ja","title":"test_title"}]
            result = record.switching_language(data)
            assert result == "test_title"
        # not exist language
        with app.test_request_context(headers=[('Accept-Language', 'da')]):
            data = [{"title":"test_title"}]
            result = record.switching_language(data)
            assert result == "test_title"
        # len(data) <= 0
        with app.test_request_context(headers=[('Accept-Language', 'da')]):
            data = {}
            result = record.switching_language(data)
            assert result == ""

        # no language
        with app.test_request_context(headers=[('Accept-Language', 'da')]):
            data = [{"title":"title"},{"title":"en_title","language":"en"}]
            result = record.switching_language(data)
            assert result == "title"

        # no language
        with app.test_request_context(headers=[('Accept-Language', 'en')]):
            data = [{"title":"title"},{"title":"en_title","language":"en"}]
            result = record.switching_language(data)
            assert result == "en_title"

        # no language
        with app.test_request_context(headers=[('Accept-Language', 'ja')]):
            data = [{"title":"en_title","language":"en"},{"title":"title"}]
            result = record.switching_language(data)
            assert result == "en_title"

    # def __get_titles_key(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_titles_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_titles_key(self,app,es_records,db_itemtype,db_oaischema):
        parent_key = ['item_1617186331708', 'item_1617186331709']
        title_key = {'item_1617186331708': 'subitem_1551255647225', 'item_1617186331709': 'subitem_1551255647226'}
        language_key = {'item_1617186331708': 'subitem_1551255648112', 'item_1617186331709': 'subitem_1551255648113'}

        item_type = db_itemtype["item_type"]
        item_type_mapping = db_itemtype["item_type_mapping"]

        mapping = item_type_mapping.mapping
        render = item_type.render
        meta_options = {**render["meta_fix"], **render["meta_list"], **render["meta_system"]}

        record = WekoRecord({})
        # Test Case 1: No hide list
        actual = record._WekoRecord__get_titles_key(mapping, meta_options, [])
        assert actual[0] == parent_key
        assert actual[1] == title_key
        assert actual[2] == language_key

        # Test Case 2: With hide list (title_key)
        hide_list = ["item_1617186331708.subitem_1551255647225"]
        actual = record._WekoRecord__get_titles_key(mapping, meta_options, hide_list)
        assert actual[0] == ['item_1617186331709']
        assert actual[1] == {'item_1617186331709': 'subitem_1551255647226'}
        assert actual[2] == {'item_1617186331709': 'subitem_1551255648113'}

        # Test Case 3: With hide list (language_key)
        hide_list = ["item_1617186331708.subitem_1551255648112"]
        actual = record._WekoRecord__get_titles_key(mapping, meta_options, hide_list)
        assert actual[0] == ['item_1617186331708', 'item_1617186331709']
        assert actual[1] == {'item_1617186331708': 'subitem_1551255647225', 'item_1617186331709': 'subitem_1551255647226'}
        assert actual[2] == {'item_1617186331708': None, 'item_1617186331709': 'subitem_1551255648113'}

        # Test Case 4: With hide list (both title_key and language_key)
        # hide_list = ["item_1617186331708.subitem_1551255647225", "item_1617186331709.subitem_1551255648113"]
        # actual = record._WekoRecord__get_titles_key(mapping, meta_options, hide_list)
        # assert actual[0] == ['item_1617186331709']
        # assert actual[1] == {'item_1617186331709': 'subitem_1551255647226'}
        # assert actual[2] == {'item_1617186331709': None}

    #     def __get_titles_key(item_type_mapping):
    #     def get_titles(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_titles -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_titles(self,app,es_records,db_itemtype,db_oaischema):
        _, results = es_records
        result = results[0]
        record = result['record']
        assert record['item_type_id']=="1"

        with app.test_request_context():
            assert record.get_titles=="title"

        with app.test_request_context(headers=[("Accept-Language", "en")]):
            assert record.get_titles=="title"

        app.config['BABEL_DEFAULT_LOCALE'] = 'ja'
        #from flask_babelex import refresh; refresh()
        with app.test_request_context():
            assert record.get_titles=="タイトル"

        app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
        #from flask_babelex import refresh; refresh()
        with app.test_request_context():
            assert record.get_titles=="title"

        record["item_1617186331708"]["attribute_value_mlt"][0].pop("subitem_1551255648112")
        record["item_1617186331708"]["attribute_value_mlt"][1].pop("subitem_1551255648112")
        with app.test_request_context():
            assert record.get_titles=="タイトル"

        record["item_1617186331709"] = {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647226": "タイトル-2", "subitem_1551255648113": "ja"},{"subitem_1551255647226": "title-2", "subitem_1551255648113": "en"}]}
        with app.test_request_context():
            assert record.get_titles=="タイトル"

        record.pop("item_1617186331708")
        app.config['BABEL_DEFAULT_LOCALE'] = 'ja'
        with app.test_request_context():
            assert record.get_titles=="タイトル-2"

        app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
        with app.test_request_context():
            assert record.get_titles=="title-2"

        record["item_1617186331709"]["attribute_value_mlt"][0].pop("subitem_1551255648113")
        record["item_1617186331709"]["attribute_value_mlt"][1].pop("subitem_1551255648113")
        with app.test_request_context():
            assert record.get_titles=="タイトル-2"

    #     def items_show_list(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_items_show_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_items_show_list(self,app,es_records,users,db_itemtype,db_admin_settings):
        record = WekoRecord({})
        with app.test_request_context():
            with pytest.raises(AttributeError):
                assert record.items_show_list==""
        _, results = es_records
        result = results[0]
        record = result['record']
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            assert record.items_show_list==[{'attribute_name': 'PubDate', 'attribute_value': '2022-08-20', 'attribute_name_i18n': 'PubDate'}, {'attribute_name': 'Title', 'attribute_name_i18n': 'Title', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Title': 'タイトル'}], [{'Language': 'ja'}]]], [[[{'Title': 'title'}], [{'Language': 'en'}]]]]}, {'attribute_name': 'Resource Type', 'attribute_name_i18n': 'Resource Type', 'attribute_type': None, 'attribute_value_mlt': [[[[{'Resource Type': 'conference paper'}], [{'Resource Type Identifier': 'http://purl.org/coar/resource_type/c_5794'}]]]]}, {'attribute_name': 'File', 'attribute_name_i18n': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [[[[{'dateType': 'Available', 'item_1617605131499[].date[0].dateValue': '2022-09-07'}]], [{'item_1617605131499[].url': 'https://weko3.example.org/record/1/files/hello.txt'}], [[{'item_1617605131499[].filesize[].value': '146 KB'}]], {'version_id': '{}'.format(record.files['hello.txt'].version_id), 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk', 'item_1617605131499[].filename': 'hello.txt', 'item_1617605131499[].format': 'plain/text', 'item_1617605131499[].accessrole': 'open_access'}]]}]


    #     def display_file_info(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_display_file_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_display_file_info(self,app,es_records,db_itemtype):
        record = WekoRecord({})
        with app.test_request_context():
            with pytest.raises(AttributeError):
                assert record.display_file_info==""
        _, results = es_records
        result = results[0]
        record = result['record']
        with app.test_request_context("/test?filename=hello.txt"):
            assert record.display_file_info==[{'attribute_name': 'File', 'attribute_name_i18n': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [[[[{'Opendate': '2022-09-07'}],[{'FileName': 'hello.txt'}],[{'Text URL': [[[{'Text URL': 'https://weko3.example.org/record/1/files/hello.txt'}]]]}],[{'Format': 'plain/text'}],[{'Size': [[[[{'Size': '146 KB'}]]]]}]]]]}]

    #     def __remove_special_character_of_weko2(self, metadata):
    #     def _get_creator(meta_data, hide_email_flag):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test__get_creator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator(self,es_records):
        record = WekoRecord({})
        assert record._get_creator({},False)==[]
        assert record._get_creator({},True)==[]


    #     def __remove_file_metadata_do_not_publish(self, file_metadata_list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test___remove_file_metadata_do_not_publish -vv -s --cov-branch
    #     def __check_user_permission(user_id_list):
    #     def is_input_open_access_date(file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_is_input_open_access_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_input_open_access_date(self):
        record = WekoRecord({})
        assert record.is_input_open_access_date({})==False

    #     def is_do_not_publish(file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_is_do_not_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_do_not_publish(self):
        record = WekoRecord({})
        assert record.is_do_not_publish({})==False

    #     def get_open_date_value(file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_open_date_value -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_open_date_value(self):
        record = WekoRecord({})
        assert record.get_open_date_value({})==None

    #     def is_future_open_date(self, file_metadata):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_is_future_open_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_is_future_open_date(self,es_records):
        record = WekoRecord({})
        assert record.is_future_open_date(record,{})==True
        assert record.is_future_open_date(record,{'url': {'url': 'https://weko3.example.org/record/1/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-07'}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_access', 'version_id': 'e131046c-291f-4065-b4b4-ca3bf1fac6e3', 'mimetype': 'application/pdf', 'file': 'SGVsbG8sIFdvcmxk'})==False




    #     def pid_doi(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_doi(self,es_records):
        record = WekoRecord({})
        with pytest.raises(AttributeError):
            assert record.pid_doi==""
        _, records = es_records
        record = records[0]['record']
        pid = record.pid_doi
        assert isinstance(pid,PersistentIdentifier)==True
        assert pid.pid_type=='doi'

    #     def pid_cnri(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_cnri -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_cnri(self,es_records):
        record = WekoRecord({})
        with pytest.raises(AttributeError):
            assert record.pid_cnri==""
        _, records = es_records
        record = records[0]['record']
        pid = record.pid_cnri
        assert isinstance(pid,PersistentIdentifier)==True
        assert pid.pid_type=='hdl'


    #     def pid_parent(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_pid_parent -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_pid_parent(self,es_records):
        record = WekoRecord({})
        with pytest.raises(AttributeError):
            assert record.pid_parent==""
        _, records = es_records
        record = records[0]['record']
        pid = record.pid_parent
        assert isinstance(pid,PersistentIdentifier)==True
        assert pid.pid_type=='parent'

    #     def get_record_by_pid(cls, pid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_record_by_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_record_by_pid(self,es_records):
        _, records = es_records
        record = records[0]['record']
        recid = records[0]['recid']
        rec = WekoRecord.get_record_by_pid(1)
        assert isinstance(rec,WekoRecord)
        assert rec.pid_recid==recid


    #     def get_record_by_uuid(cls, uuid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_record_by_uuid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_record_by_uuid(self,es_records):
        _, records = es_records
        record = records[0]['record']
        recid = records[0]['recid']
        rec =  WekoRecord.get_record_by_uuid(record.id)
        assert isinstance(rec,WekoRecord)==True
        assert rec.pid_recid == recid

    #     def get_record_cvs(cls, uuid):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_record_cvs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_record_cvs(self,es_records):
        _, records = es_records
        record = records[0]['record']
        assert WekoRecord.get_record_cvs(record.id)==False

    #     def _get_pid(self, pid_type):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test__get_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_pid(self,es_records):
        record = WekoRecord({})
        with pytest.raises(AttributeError):
            record._get_pid('')



    #     def update_item_link(self, pid_value):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_update_item_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_update_item_link(self,es_records):
        _, records = es_records
        record = records[0]['record']
        recid = records[0]['recid']
        record2 = records[2]['record']
        record.update_item_link(record2.pid.pid_value)
        item_link = ItemLink.get_item_link_info(recid.pid_value)
        assert item_link==[]


    #     def get_file_data(self):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::TestWekoRecord::test_get_file_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_file_data(self,app,es_records):
        _, records = es_records
        record = records[0]["record"]
        with app.test_request_context():
            result = record.get_file_data()
            assert result[0]["accessrole"] == "open_access"
            assert result[0]["filename"] == "hello.txt"


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
        with app.test_request_context():
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True
            obj._get_creator_languages_order()
            assert obj.languages==['ja', 'ja-Kana', 'en']

    # def _format_creator_to_show_detail(self, language: str, parent_key: str,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_to_show_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_to_show_detail(self,app,prepare_creator):
        with app.test_request_context():
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True
            language = 'en'
            parent_key = 'creatorNames'
            lst = []
            obj._format_creator_to_show_detail(language,parent_key,lst)
            assert lst==['Joho, Taro']

    #* This is for testing only for the changes regarding creatorType
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_to_show_detail_2 -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_to_show_detail_2(self, app, prepare_creator):
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

    #     def _get_creator_to_show_popup(self, creators: Union[list, dict],
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_to_show_popup -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_to_show_popup(self,app,prepare_creator):
        with app.test_request_context():
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True
            creators={'creatorType': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': '所属機関', 'affiliationNameLang': 'ja'}, {'affiliationName': 'Affilication Name', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}]}], 'creatorAlternatives': [{'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}
            language='ja'
            creator_list=[]
            creator_list_temp=None
            obj._get_creator_to_show_popup(creators,language,creator_list,creator_list_temp)
            assert creators=={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'affiliationName': 'Affilication Name', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}]}], 'creatorAlternatives': [{'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}
            assert language=="ja"
            assert creator_list==[{'ja': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}]
            assert creator_list_temp==None

    #* This is for testing only for the changes regarding creatorType
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_to_show_popup_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_to_show_popup_2(self, app, prepare_creator):
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

#         def _run_format_affiliation(affiliation_max, affiliation_min,
#         def format_affiliation(affiliation_data):
    # def _get_creator_based_on_language(creator_data: dict,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_based_on_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_based_on_language(self,app,prepare_creator):
        with app.test_request_context():
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True
            creator_data ={'givenName': '太郎', 'givenNameLang': 'ja'}
            creator_list_temp=[]
            language='ja'
            obj._get_creator_based_on_language(creator_data,creator_list_temp,language)
            assert creator_list_temp==[{'givenName': '太郎', 'givenNameLang': 'ja'}]

    # def format_creator(self) -> dict:
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test_format_creator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_format_creator(self,app,prepare_creator):
        with app.test_request_context():
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True
            assert obj.format_creator()=={'name': ['Joho, Taro'], 'order_lang': [{'ja': {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}}, {'ja-Kana': {'creatorName': ['ジョウホウ, タロウ'], 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'en': {'creatorName': ['Joho, Taro'], 'creatorAlternative': ['Alternative Name'], 'affiliationName': [' Affilication Name'], 'affiliationNameIdentifier': [{'identifier': '', 'uri': ''}]}}]}

    #* This is for testing only for the changes regarding creatorType
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test_format_creator_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_format_creator_2(self, app, prepare_creator):
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

    # def _format_creator_on_creator_popup(self, creators: Union[dict, list],
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_on_creator_popup -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_on_creator_popup(self,app,prepare_creator):
        with app.test_request_context():
            obj = _FormatSysCreator({})
            assert isinstance(obj,_FormatSysCreator)==True
            formatted_creator_list = []
            creator_list=[{'ja': {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}}, {'ja-Kana': {'givenName': ['タロウ'], 'givenNameLang': ['ja-Kana'], 'familyName': ['ジョウホウ'], 'familyNameLang': ['ja-Kana'], 'creatorName': ['ジョウホウ, タロウ'], 'creatorNameLang': ['ja-Kana']}}, {'en': {'givenName': ['Taro'], 'givenNameLang': ['en'], 'familyName': ['Joho'], 'familyNameLang': ['en'], 'creatorName': ['Joho, Taro'], 'creatorNameLang': ['en'], 'affiliationName': ['Affilication Name'], 'affiliationNameLang': ['en'], 'creatorAlternative': ['Alternative Name'], 'creatorAlternativeLang': ['en']}}]
            obj._format_creator_on_creator_popup(creator_list,formatted_creator_list)
            assert formatted_creator_list==[{'ja': {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}}, {'ja-Kana': {'creatorName': ['ジョウホウ, タロウ'], 'creatorAlternative': [], 'affiliationName': [], 'affiliationNameIdentifier': []}}, {'en': {'creatorName': ['Joho, Taro'], 'creatorAlternative': ['Alternative Name'], 'affiliationName': [' Affilication Name'], 'affiliationNameIdentifier': [{'identifier': '', 'uri': ''}]}}]

    # def _format_creator_name(creator_data: dict,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_name(self,app,prepare_creator):
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


    # def _format_creator_affiliation(creator_data: dict,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__format_creator_affiliation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__format_creator_affiliation(self,app,prepare_creator):
        with app.test_request_context():
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True
            creator_data = {'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
            des_creator = {'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名']}
            obj._format_creator_affiliation(creator_data,des_creator)
            assert des_creator=={'creatorName': ['情報, 太郎'], 'creatorAlternative': ['別名'], 'affiliationName': ['ISNI 所属機関'], 'affiliationNameIdentifier': [{'identifier': 'xxxxxx', 'uri': 'xxxxx'}]}

    #         def _get_max_list_length() -> int:
    # def _get_creator_to_display_on_popup(self, creator_list: list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_creator_to_display_on_popup -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_creator_to_display_on_popup(self,app,prepare_creator):
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True
            creator_list = []
            obj._get_creator_to_display_on_popup(creator_list)
            assert creator_list==[{'ja': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}, {'ja-Kana': [{'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}]}, {'en': [{'givenName': 'Taro', 'givenNameLang': 'en'}, {'familyName': 'Joho', 'familyNameLang': 'en'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}, {'affiliationName': 'Affilication Name', 'affiliationNameLang': 'en'}, {'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}]}]


    # def _merge_creator_data(self, creator_data: Union[list, dict],
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__merge_creator_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__merge_creator_data(self,app,prepare_creator):
        with app.test_request_context():
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True
            creator_data = [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]
            merged_data = {}
            obj._merge_creator_data(creator_data,merged_data)
            assert merged_data=={'givenName': ['太郎'], 'givenNameLang': ['ja'], 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
            creator_data = [ {'familyName': '情報', 'familyNameLang': 'ja'}, {'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'affiliationName': '所属機関', 'affiliationNameLang': 'ja', 'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]
            merged_data = {'givenName': '次郎', 'givenNameLang': 'ja'}
            obj._merge_creator_data(creator_data,merged_data)
            assert merged_data=={'givenName': '次郎', 'givenNameLang': 'ja', 'familyName': ['情報'], 'familyNameLang': ['ja'], 'creatorName': ['情報, 太郎'], 'creatorNameLang': ['ja'], 'affiliationName': ['所属機関'], 'affiliationNameLang': ['ja'], 'affiliationNameIdentifier': ['xxxxxx'], 'affiliationNameIdentifierURI': ['xxxxx'], 'affiliationNameIdentifierScheme': ['ISNI'], 'creatorAlternative': ['別名'], 'creatorAlternativeLang': ['ja']}
            creator_data="not_dict_or_list"
            merged_data={}
            obj._merge_creator_data(creator_data,merged_data)
            assert merged_data == {}

            creator_data={'givenName': ['太郎']}
            merged_data={}
            obj._merge_creator_data(creator_data,merged_data)
            assert merged_data == {}

            creator_data={'givenName': '太郎'}
            merged_data={'givenName': ['次郎']}
            obj._merge_creator_data(creator_data,merged_data)
            assert merged_data == {'givenName': ['次郎','太郎']}

    #         def merge_data(key, value):
    # def _get_default_creator_name(self, list_parent_key: list,
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test_FormatSysCreator::test__get_default_creator_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_default_creator_name(self,app,prepare_creator):
        with app.test_request_context():
            obj = _FormatSysCreator(prepare_creator)
            assert isinstance(obj,_FormatSysCreator)==True
            list_parent_key = ['creatorNames', 'familyNames', 'givenNames', 'creatorAlternatives']
            creator_name = []
            obj.languages=["ja","en"]
            obj._get_default_creator_name(list_parent_key,creator_name)
            assert creator_name==['Joho, Taro']

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
        mlt,solst = prepare_formatsysbib
        obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True
        assert obj.is_bibliographic()==True

        obj.bibliographic_meta_data_lst={"bibliographic_titles":"title"}
        assert obj.is_bibliographic() == True

        obj.bibliographic_meta_data_lst="str_value"
        assert obj.is_bibliographic() == False



    #         def check_key(_meta_data):
    # def get_bibliographic_list(self, is_get_list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test_get_bibliographic_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test_get_bibliographic_list(self,app,prepare_formatsysbib):
        mlt,solst = prepare_formatsysbib
        obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            assert obj.get_bibliographic_list(True)==[{'title_attribute_name': 'Journal Title', 'magazine_attribute_name': [{'Volume': '1'}, {'Issue': '12'}, {'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 'length': 5}]
            assert obj.get_bibliographic_list(False)==[{'title_attribute_name': ['ja : 雑誌タイトル', 'en : Journal Title'], 'magazine_attribute_name': [{'Volume Number': '1'}, {'Issue Number': '12'}, {'p.': '1-100'}, {'Number of Page': '99'}, {'Issue Date': '2022-08-29'}], 'length': 5}]

    # def _get_bibliographic(self, bibliographic, is_get_list):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_bibliographic -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_bibliographic(self,app,prepare_formatsysbib):
        mlt,solst = prepare_formatsysbib
        bibliographic = mlt[0]
        obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True
        with app.test_request_context(headers=[("Accept-Language", "en")]):
            assert obj._get_bibliographic(bibliographic,True)==('Journal Title', [{'Volume': '1'}, {'Issue': '12'}, {'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 5)
            assert obj._get_bibliographic(bibliographic,False)==(['ja : 雑誌タイトル', 'en : Journal Title'], [{'Volume Number': '1'}, {'Issue Number': '12'}, {'p.': '1-100'}, {'Number of Page': '99'}, {'Issue Date': '2022-08-29'}], 5)


    # def _get_property_name(self, key):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_property_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_property_name(self,app,prepare_formatsysbib):
        mlt,solst = prepare_formatsysbib
        obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True
        assert obj._get_property_name('subitem_1551255647225')=='Title'

        result = obj._get_property_name('not_exist_key')
        assert result == "not_exist_key"


    # def _get_translation_key(key, lang):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_translation_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_translation_key(self,app,prepare_formatsysbib):
        mlt,solst = prepare_formatsysbib
        obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True
        for key in WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS:
            assert obj._get_translation_key(key,"en")==WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS[key]["en"]

        result = obj._get_translation_key("not_exist_key","")
        assert result == None

    # def _get_bibliographic_information(self, bibliographic):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_bibliographic_information -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_bibliographic_information(self,app,prepare_formatsysbib):
        mlt,solst = prepare_formatsysbib
        bibliographic = mlt[0]
        obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True
        assert obj._get_bibliographic_information(bibliographic)==([{'Volume Number': '1'}, {'Issue Number': '12'}, {'p.': '1-100'}, {'Number of Page': '99'}, {'Issue Date': '2022-08-29'}], 5)

    # def _get_bibliographic_show_list(self, bibliographic, language):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_bibliographic_show_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_bibliographic_show_list(self,app,prepare_formatsysbib):
        mlt,solst = prepare_formatsysbib
        bibliographic = mlt[0]
        obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True
        with app.test_request_context():
            assert obj._get_bibliographic_show_list(bibliographic,"ja")==([{'巻': '1'}, {'号': '12'}, {'p.': '1-100'}, {'ページ数': '99'}, {'発行年': '2022-08-29'}], 5)
            assert obj._get_bibliographic_show_list(bibliographic,"en")==([{'Volume': '1'}, {'Issue': '12'}, {'p.': '1-100'}, {'Number of Pages': '99'}, {'Issued Date': '2022-08-29'}], 5)

    # def _get_source_title(source_titles):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test___get_source_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test___get_source_title(self,prepare_formatsysbib):
        mlt,solst = prepare_formatsysbib
        bibliographic = mlt[0]
        obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True

        assert obj._get_source_title(bibliographic.get('bibliographic_titles'))==['ja : 雑誌タイトル', 'en : Journal Title']

    # def _get_source_title_show_list(source_titles, current_lang):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_source_title_show_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_source_title_show_list(self,app,prepare_formatsysbib):
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

        data =[{"bibliographic_titleLang":"ja-Latn","bibliographic_title":"ja-Latn_title"}]
        value, lang = obj._get_source_title_show_list(data, "en")
        assert value == "ja-Latn_title"
        assert lang == "ja-Latn"


        data =[{"bibliographic_title":"not_key_title"},{"bibliographic_titleLang":"ja-Latn","bibliographic_title":"ja-Latn_title"}]
        value, lang = obj._get_source_title_show_list(data, "en")
        assert value == "not_key_title"
        assert lang == ""

        app.config.update(WEKO_RECORDS_UI_LANG_DISP_FLG=True)
        data = [{},{"bibliographic_title":"not_key_title"},{"bibliographic_titleLang":"ja","bibliographic_title":"ja_title"},{"bibliographic_titleLang":"zh","bibliographic_title":"zh_title"}]
        value, lang = obj._get_source_title_show_list(data, "en")
        assert value == "zh_title"
        assert lang == "zh"
        data = [{},{"bibliographic_title":"not_key_title"}]
        value, lang = obj._get_source_title_show_list(data, "en")
        assert value == "not_key_title"
        assert lang == "ja"

    # def _get_page_tart_and_page_end(page_start, page_end):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_page_tart_and_page_end -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_page_tart_and_page_end(self,prepare_formatsysbib):
        mlt,solst = prepare_formatsysbib
        bibliographic = mlt[0]
        obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True
        assert obj._get_page_tart_and_page_end(bibliographic.get('bibliographicPageStart'),
                    bibliographic.get('bibliographicPageEnd'))=="{0}-{1}".format(bibliographic.get('bibliographicPageStart'),
                    bibliographic.get('bibliographicPageEnd'))

    # def _get_issue_date(issue_date):
    # .tox/c1/bin/pytest --cov=weko_deposit tests/test_api.py::Test__FormatSysBibliographicInformation::test__get_issue_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
    def test__get_issue_date(self,prepare_formatsysbib):
        mlt,solst = prepare_formatsysbib
        bibliographic = mlt[0]
        obj=_FormatSysBibliographicInformation(copy.deepcopy(mlt),copy.deepcopy(solst))
        assert isinstance(obj,_FormatSysBibliographicInformation) == True
        assert obj._get_issue_date(bibliographic.get('bibliographicIssueDates'))==[bibliographic.get('bibliographicIssueDates').get('bibliographicIssueDate')]

        data = [{"bibliographicIssueDate":'2022-08-29', 'bibliographicIssueDateType': 'Issued'},{"key":"value"}]
        result = obj._get_issue_date(data)
        assert result == ["2022-08-29"]
        data = "str_data"
        result = obj._get_issue_date(data)
        assert result == []


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
    a = {'_oai': {'id': 'oai:weko3.example.org:00000002.1', 'sets': []}, 'path': ['1031'], 'owner': '1', 'recid': '2.1', 'title': ['ja_conference paperITEM00000002(public_open_access_open_access_simple)'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2021-02-13'}, '_buckets': {'deposit': '9766676f-0a12-439b-b5eb-6c39a61032c6'}, '_deposit': {'id': '2.1', 'pid': {'type': 'depid', 'value': '2.1', 'revision_id': 0}, 'owners': [1], 'status': 'draft'}, 'item_title': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'author_link': ['1', '2', '3'], 'item_type_id': '15', 'publish_date': '2021-02-13', 'publish_status': '0', 'weko_shared_ids': [], 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000002(public_open_access_simple)', 'subitem_1551255648112': 'en'}]}, 'item_1617186385884': {'attribute_name': 'Alternative Title', 'attribute_value_mlt': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}]}, 'item_1617186419668': {'attribute_name': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '1', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI'}]}]}, {'givenNames': [{'givenName': '次郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 次郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '2', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}, {'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 三郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '3', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}]}, 'item_1617186476635': {'attribute_name': 'Access Rights', 'attribute_value_mlt': [{'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}]}, 'item_1617186499011': {'attribute_name': 'Rights', 'attribute_value_mlt': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}]}, 'item_1617186609386': {'attribute_name': 'Subject', 'attribute_value_mlt': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}]}, 'item_1617186626617': {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'Description\\nDescription<br/>Description&EMPTY&\\nDescription', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'en'}, {'subitem_description': '概要\\n概要&EMPTY&\\n概要\\n概要', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'ja'}]}, 'item_1617186643794': {'attribute_name': 'Publisher', 'attribute_value_mlt': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}]}, 'item_1617186660861': {'attribute_name': 'Date', 'attribute_value_mlt': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}]}, 'item_1617186702042': {'attribute_name': 'Language', 'attribute_value_mlt': [{'subitem_1551255818386': 'jpn'}]}, 'item_1617186783814': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_identifier_uri': 'http://localhost', 'subitem_identifier_type': 'URI'}]}, 'item_1617186859717': {'attribute_name': 'Temporal', 'attribute_value_mlt': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}]}, 'item_1617186882738': {'attribute_name': 'Geo Location', 'attribute_value_mlt': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}]}, 'item_1617186901218': {'attribute_name': 'Funding Reference', 'attribute_value_mlt': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}]}, 'item_1617186920753': {'attribute_name': 'Source Identifier', 'attribute_value_mlt': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}]}, 'item_1617186941041': {'attribute_name': 'Source Title', 'attribute_value_mlt': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}]}, 'item_1617186959569': {'attribute_name': 'Volume Number', 'attribute_value_mlt': [{'subitem_1551256328147': '1'}]}, 'item_1617186981471': {'attribute_name': 'Issue Number', 'attribute_value_mlt': [{'subitem_1551256294723': '111'}]}, 'item_1617186994930': {'attribute_name': 'Number of Pages', 'attribute_value_mlt': [{'subitem_1551256248092': '12'}]}, 'item_1617187024783': {'attribute_name': 'Page Start', 'attribute_value_mlt': [{'subitem_1551256198917': '1'}]}, 'item_1617187045071': {'attribute_name': 'Page End', 'attribute_value_mlt': [{'subitem_1551256185532': '3'}]}, 'item_1617187112279': {'attribute_name': 'Degree Name', 'attribute_value_mlt': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}]}, 'item_1617187136212': {'attribute_name': 'Date Granted', 'attribute_value_mlt': [{'subitem_1551256096004': '2021-06-30'}]}, 'item_1617187187528': {'attribute_name': 'Conference', 'attribute_value_mlt': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'item_1617265215918': {'attribute_name': 'Version Type', 'attribute_value_mlt': [{'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}]}, 'item_1617349709064': {'attribute_name': 'Contributor', 'attribute_value_mlt': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'contributorType': 'ContactPerson', 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'lang': 'ja', 'contributorName': '情報, 太郎'}, {'lang': 'ja-Kana', 'contributorName': 'ジョウホウ, タロウ'}, {'lang': 'en', 'contributorName': 'Joho, Taro'}]}]}, 'item_1617349808926': {'attribute_name': 'Version', 'attribute_value_mlt': [{'subitem_1523263171732': 'Version'}]}, 'item_1617351524846': {'attribute_name': 'APC', 'attribute_value_mlt': [{'subitem_1523260933860': 'Unknown'}]}, 'item_1617353299429': {'attribute_name': 'Relation', 'attribute_value_mlt': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}]}, 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'url': {'url': 'https://weko3.example.org/record/2.1/files/1KB.pdf'}, 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'format': 'text/plain', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'mimetype': 'application/pdf', 'accessrole': 'open_access', 'version_id': '6f80e3cb-f681-45eb-bd54-b45be0f7d3ee', 'displaytype': 'simple'}]}, 'item_1617610673286': {'attribute_name': 'Rights Holder', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}], 'rightHolderNames': [{'rightHolderName': 'Right Holder Name', 'rightHolderLanguage': 'ja'}]}]}, 'item_1617620223087': {'attribute_name': 'Heading', 'attribute_value_mlt': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}]}, 'item_1617944105607': {'attribute_name': 'Degree Grantor', 'attribute_value_mlt': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}]}, 'relation_version_is_last': True}
    b = {'pid': {'type': 'depid', 'value': '2.0', 'revision_id': 0}, 'lang': 'ja', 'owner': '1', 'title': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'owners': [1], 'status': 'published', '$schema': '15', 'pubdate': '2021-02-13', 'edit_mode': 'keep', 'created_by': 1, 'deleted_items': ['item_1617187056579', 'approval1', 'approval2'], 'shared_user_ids': [], 'weko_shared_ids': [], 'item_1617186331708': [{'subitem_1551255647225': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000002(public_open_access_simple)', 'subitem_1551255648112': 'en'}], 'item_1617186385884': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}], 'item_1617186419668': [{'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}]}, {'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 三郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '3', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}]}], 'item_1617186476635': {'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}, 'item_1617186499011': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}], 'item_1617186609386': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}], 'item_1617186626617': [{'subitem_description': 'Description\\nDescription<br/>Description&EMPTY&\\nDescription', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'en'}, {'subitem_description': '概要\\n概要&EMPTY&\\n概要\\n概要', 'subitem_description_type': 'Abstract', 'subitem_description_language': 'ja'}], 'item_1617186643794': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}], 'item_1617186660861': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617186783814': [{'subitem_identifier_uri': 'http://localhost', 'subitem_identifier_type': 'URI'}], 'item_1617186859717': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}], 'item_1617186882738': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}], 'item_1617186901218': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}], 'item_1617186920753': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}], 'item_1617186941041': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}], 'item_1617186959569': {'subitem_1551256328147': '1'}, 'item_1617186981471': {'subitem_1551256294723': '111'}, 'item_1617186994930': {'subitem_1551256248092': '12'}, 'item_1617187024783': {'subitem_1551256198917': '1'}, 'item_1617187045071': {'subitem_1551256185532': '3'}, 'item_1617187112279': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}], 'item_1617187136212': {'subitem_1551256096004': '2021-06-30'}, 'item_1617187187528': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}], 'item_1617258105262': {'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}, 'item_1617265215918': {'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, 'item_1617349709064': [{'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'contributorType': 'ContactPerson', 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'lang': 'ja', 'contributorName': '情報, 太郎'}, {'lang': 'ja-Kana', 'contributorName': 'ジョウホウ, タロウ'}, {'lang': 'en', 'contributorName': 'Joho, Taro'}]}], 'item_1617349808926': {'subitem_1523263171732': 'Version'}, 'item_1617351524846': {'subitem_1523260933860': 'Unknown'}, 'item_1617353299429': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}], 'item_1617605131499': [{'url': {'url': 'https://weko3.example.org/record/2/files/1KB.pdf'}, 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'format': 'text/plain', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'mimetype': 'application/pdf', 'accessrole': 'open_access', 'version_id': 'c92410f6-ed23-4d2e-a8c5-0b3b06cc79c8', 'displaytype': 'simple'}], 'item_1617610673286': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}], 'rightHolderNames': [{'rightHolderName': 'Right Holder Name', 'rightHolderLanguage': 'ja'}]}], 'item_1617620223087': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}], 'item_1617944105607': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}]}
    # deposit = WekoDeposit.create(a)
    # print("deposit: {}".format(deposit))
