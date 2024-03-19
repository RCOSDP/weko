import pytest
from mock import patch

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
