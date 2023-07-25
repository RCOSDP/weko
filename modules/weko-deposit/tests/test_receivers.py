import pytest
import json
import uuid
from mock import patch
from tests.helpers import create_record, json_data
from collections import OrderedDict
from invenio_accounts.models import User
from invenio_records.models import RecordMetadata
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidrelations.models import PIDRelation
from weko_records.models import FeedbackMailList
from weko_deposit.receivers import append_file_content
from weko_records.api import WekoRecord, ItemsMetadata
from weko_deposit.api import WekoDeposit 
from flask_security import current_user

# def append_file_content(sender, json=None, record=None, index=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_receivers.py::test_append_file_content -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_append_file_content(app, db, db_itemtype, users, db_userprofile, es_records, mocker):
    recid = es_records[1][0]['recid']
    depid = es_records[1][0]['depid']
    deposit = es_records[1][0]['deposit']

    user = User.query.filter_by(email="sysadmin@test.org").first()
    mocker.patch("flask_login.utils._get_user", return_value=user)
    with patch("flask_security.current_user", return_value=user):
        # なんでPIDがDBに入っていないのか不明だが、再作成する
        recid = PersistentIdentifier.create('recid', '1', object_type='rec', object_uuid=recid.object_uuid,status=PIDStatus.REGISTERED)
        depid = PersistentIdentifier.create('depid', '1', object_type='rec', object_uuid=depid.object_uuid,status=PIDStatus.REGISTERED)
        with db.session.begin_nested():
            db.session.add(recid)
            db.session.add(depid)

        # WekoRecordデータベース登録
        record = WekoRecord.create(es_records[1][0]['record_data'], id_=recid.object_uuid, recid=recid)

        # from six import BytesIO
        from invenio_files_rest.models import Bucket, ObjectVersion
        from invenio_records_files.models import RecordsBuckets
        import base64
        from six import BytesIO
        bucket = Bucket.create()
        record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)
        stream = BytesIO(b'Hello, World')
        obj=ObjectVersion.create(bucket=bucket.id, key='hello.txt', stream=stream)
        record['item_1617605131499']['attribute_value_mlt'][0]['file'] = (base64.b64encode(stream.getvalue())).decode('utf-8')

        es_records[1][0]['record_data']['content']= [{"date":[{"dateValue":"2021-07-12","dateType":"Available"}],"accessrole":"open_access","displaytype" : "simple","filename" : "hello.txt","attachment" : {},"format" : "text/plain","mimetype" : "text/plain","filesize" : [{"value" : "1 KB"}],"version_id" : "{}".format(obj.version_id),"url" : {"url":"http://localhost/record/{1}/files/hello.txt"},"file":(base64.b64encode(stream.getvalue())).decode('utf-8')}]
        es_records[0].upload_metadata(es_records[1][0]['record_data'], recid.object_uuid, 1, False)
        record.commit()
        # WekoDepositデータベース登録
        #rec_deposit = WekoDeposit.create(deposit, id_=recid.object_uuid)
        #rec_deposit.commit()
        # ItemsMetadataデータベース登録
        es_records[1][0]['item_data']['content'] = 'hoge'
        rec_item = ItemsMetadata.create(es_records[1][0]['item_data'], id_=recid.object_uuid)
        rec_item.commit()

        json = {
            "key":"value",
            "_created":"2022-10-01"
        }
        sender={}
        jrc = {'type': ['conference paper'], 'title': ['タイトル', 'title'], 
                'control_number': '1', '_oai': {'id': '1'}, 
                '_item_metadata': OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2023-07-23'}), 
                                            ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}]}), 
                                            ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}), 
                                            ('item_title', 'title'), ('item_type_id', '1'), ('control_number', '1'), ('author_link', []), 
                                            ('weko_shared_ids', []), ('_oai', {'id': '1'}), ('owner', '5'), ('owners', ['5'])]), 
                                            'itemtype': 'テストアイテムタイプ', 'publish_date': '2022-08-20', 'author_link': [], 
                                            'weko_creator_id': '5', 'weko_shared_ids': [], 
                                            'content': 'test'}
        def json_loader_dummy(metadata, pid):
            return _, jrc, _
        with mocker.patch("weko_records.utils.json_loader", return_value=json_loader_dummy):
            res = append_file_content(sender, json, es_records[1][0]['record'])
            assert res==None

        obj = es_records[1][0]["recid"]
        mail = FeedbackMailList(
            item_id=obj.object_uuid,
            mail_list=[{"email":"test@test.org"}]
        )
        db.session.add(mail)
        obj.status = "N"
        db.session.merge(obj)
        db.session.commit()
        
        res = append_file_content(sender, json, es_records[1][0]['record'])
        assert res==None
        
        with patch("weko_deposit.receivers.FeedbackMailList.get_mail_list_by_item_id",side_effect=Exception("test_error")):
            res = append_file_content(sender, json, es_records[1][0]['record'])
            assert res==None

        json = {'_created':"2023-08-01",
                '_updated':"2023-08-01",
                'id':'1'}
        sender={}
        
        rec_uuid = uuid.uuid4()

        recid = PersistentIdentifier.create('recid', "100", object_type='rec', object_uuid=rec_uuid, status=PIDStatus.REGISTERED)
        depid = PersistentIdentifier.create('depid', "100", object_type='rec', object_uuid=rec_uuid, status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(recid,depid, 2, 0)
        es_records[1][0]['record_data']['recid'] = 100
        es_records[1][0]['record_data']['_deposit']['id'] = 100
        es_records[1][0]['record_data']['_deposit']['pid']['value'] = 100
        es_records[1][0]['record_data']['content'] = "content"
        es_records[1][0]['item_data']['id'] = 100
        es_records[1][0]['item_data']['pid']['value'] = 100
        es_records[1][0]['item_data']['id'] = 100
        rec = WekoRecord.create(es_records[1][0]['record_data'], id_=rec_uuid)
        dep = WekoDeposit(rec, rec.model)
        ItemsMetadata.create(es_records[1][0]['item_data'], id_=rec_uuid)
        rec_meta = RecordMetadata(id=rec_uuid, json=es_records[1][0]['record_data'], version_id=1)
        record_metadata = RecordMetadata.query.filter_by(id=rec_uuid).first()

        ret = append_file_content(sender, json, rec)
        assert ret == None
        assert json['weko_shared_ids'] == []

        rec_uuid = uuid.uuid4()
        recid = PersistentIdentifier.create('recid', "101", object_type='rec', object_uuid=rec_uuid, status=PIDStatus.RESERVED)
        depid = PersistentIdentifier.create('depid', "101", object_type='rec', object_uuid=rec_uuid, status=PIDStatus.RESERVED)
        rel = PIDRelation.create(recid,depid, 2, 0)
        es_records[1][0]['record_data']['recid'] = 101
        es_records[1][0]['record_data']['_deposit']['id'] = 101
        es_records[1][0]['record_data']['_deposit']['pid']['value'] = 101
        es_records[1][0]['item_data']['id'] = 101
        es_records[1][0]['item_data']['pid']['value'] = 101
        es_records[1][0]['item_data']['id'] = 101
        rec = WekoRecord.create(es_records[1][0]['record_data'], id_=rec_uuid)
        dep = WekoDeposit(rec, rec.model)
        ItemsMetadata.create(es_records[1][0]['item_data'], id_=rec_uuid)
        rec_meta = RecordMetadata(id=rec_uuid, json=es_records[1][0]['record_data'], version_id=1)
        record_metadata = RecordMetadata.query.filter_by(id=rec_uuid).first()

        ret = append_file_content(sender, json, rec)
        assert ret == None
        assert json['weko_shared_ids'] == []
        
        rec_uuid = uuid.uuid4()
        recid = PersistentIdentifier.create('recid', "102", object_type='rec', object_uuid=rec_uuid, status=PIDStatus.REGISTERED)
        depid = PersistentIdentifier.create('depid', "102", object_type='rec', object_uuid=rec_uuid, status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(recid,depid, 2, 0)
        es_records[1][0]['record_data']['weko_shared_ids'] = [1,2,3]
        es_records[1][0]['record_data']['recid'] = 102
        es_records[1][0]['record_data']['_deposit']['id'] = 102
        es_records[1][0]['record_data']['_deposit']['pid']['value'] = 102
        es_records[1][0]['item_data']['id'] = 102
        es_records[1][0]['item_data']['pid']['value'] = 102
        es_records[1][0]['item_data']['id'] = 102
        es_records[1][0]['item_data']['shared_user_ids'] = [1,2,3]
        es_records[1][0]['record']['weko_shared_ids'] = [1,2,3]
        rec = WekoRecord.create(es_records[1][0]['record_data'], id_=rec_uuid)
        dep = WekoDeposit(rec, rec.model)
        ItemsMetadata.create(es_records[1][0]['item_data'], id_=rec_uuid)
        rec_meta = RecordMetadata(id=rec_uuid, json=es_records[1][0]['record_data'], version_id=1)
        record_metadata = RecordMetadata.query.filter_by(id=rec_uuid).first()

        with patch("weko_records.api.FeedbackMailList.get_mail_list_by_item_id", return_value=["xxxxxx@ivis.co.jp"]):
            ret = append_file_content(sender, json, rec)
            assert ret == None
            assert json['weko_shared_ids'] == [1,2,3]
