import pytest
from mock import patch
from collections import OrderedDict

from weko_records.models import FeedbackMailList
from weko_deposit.receivers import append_file_content

# def append_file_content(sender, json=None, record=None, index=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_receivers.py::test_append_file_content -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_append_file_content(app, db, es_records):
    json = {
        "key":"value",
        "_created":"2022-10-01"
    }
    sender={}
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

    with patch("weko_records.api.RequestMailList.get_mail_list_by_item_id", return_value=["xxxxxx@example.com"]):
        jrc ={'content': True,'type': ['conference paper'], 'title': ['タイトル', 'title'], 'control_number': '1', '_oai': {'id': '1'}, '_item_metadata': OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}), ('item_title', 'title'), ('item_type_id', '1'), ('control_number', '1'), ('author_link', []), ('weko_shared_ids', []), ('owner', 5), ('owners', [5])]), 'itemtype': 'テストアイテムタイプ', 'publish_date': '2022-08-20', 'author_link': [], 'weko_creator_id': '5', 'weko_shared_ids': []}
        jrc['content']=True
        with patch("weko_deposit.receivers.json_loader", return_value=["a", jrc, "b"]):
            ret = append_file_content(sender, json, es_records[1][0]['record'],None,arguments={"pipeline":""})
            assert ret == None
            assert json['weko_shared_ids'] == []
            assert json['request_mail_list'] == ["xxxxxx@example.com"]

    with patch("weko_records.api.RequestMailList.get_mail_list_by_item_id", return_value=[]):
        jrc ={'content': True,'type': ['conference paper'], 'title': ['タイトル', 'title'], 'control_number': '1', '_oai': {'id': '1'}, '_item_metadata': OrderedDict([('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'}), ('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'タイトル', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'title', 'subitem_1551255648112': 'en'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}), ('item_title', 'title'), ('item_type_id', '1'), ('control_number', '1'), ('author_link', []), ('weko_shared_ids', []), ('owner', 5), ('owners', [5])]), 'itemtype': 'テストアイテムタイプ', 'publish_date': '2022-08-20', 'author_link': [], 'weko_creator_id': '5', 'weko_shared_ids': []}
        jrc['content']=True
        with patch("weko_deposit.receivers.json_loader", return_value=["a", jrc, "b"]):
            ret = append_file_content(sender, json, es_records[1][0]['record'],None,arguments={"pipeline":""})
            assert ret == None
            assert json['weko_shared_ids'] == []
            assert json.get('request_mail_list') is None
