import pytest
from unittest import mock
from unittest.mock import patch
import uuid
from sqlalchemy.exc import SQLAlchemyError

from invenio_pidstore.models import PIDStatus

from weko_records.errors import WekoRecordsError
from weko_records.models import FeedbackMailList
from weko_deposit.receivers import append_file_content


# def append_file_content(sender, json=None, record=None, index=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_receivers.py::test_append_file_content -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_append_file_content(app, db, es_records):
    #Call append_file_content for the first time, result is None
    json = {
        "key":"value",
        "_created":"2022-10-01"
    }
    sender={}
    with patch("weko_deposit.receivers.weko_logger") as mock_logger:
        res = append_file_content(sender, json, es_records[1][0]['record'])
        assert res==None
        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
        mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
        mock_logger.assert_any_call(key='WEKO_DEPOSIT_APPEND_FILE_CONTENT', recid=mock.ANY)
        mock_logger.reset_mock()


    #add FeedbackMailList to mail
    obj = es_records[1][0]["recid"]
    mail = FeedbackMailList(
        item_id=obj.object_uuid,
        mail_list=[{"email":"test@test.org"}]
    )
    db.session.add(mail)
    obj.status = "N"
    db.session.merge(obj)
    db.session.commit()

    #Call append_file_content for the second time, result is none
    with patch("weko_deposit.receivers.weko_logger") as mock_logger:
        res = append_file_content(sender, json, es_records[1][0]['record'])
        assert res==None
        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
        mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
        mock_logger.assert_any_call(key='WEKO_DEPOSIT_APPEND_FILE_CONTENT', recid=mock.ANY)
        mock_logger.reset_mock()

    #when record_metadata.status is D
    obj.status = "D"
    db.session.merge(obj)
    db.session.commit()
    with patch("weko_deposit.receivers.weko_logger") as mock_logger:
        res = append_file_content(sender, json, es_records[1][0]['record'])
        assert res==None
        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_START')
        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_LOOP_ITERATION', count=mock.ANY, element=mock.ANY)
        mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER', branch=mock.ANY)
        mock_logger.assert_any_call(key='WEKO_COMMON_FOR_END')
        mock_logger.assert_any_call(key='WEKO_DEPOSIT_APPEND_FILE_CONTENT', recid=mock.ANY)
        mock_logger.reset_mock()


    obj.status = "N"
    db.session.merge(obj)
    db.session.commit()
    #Throws an exception. Result of append_file_content is None.
    ex = Exception("test_error")
    with patch("weko_deposit.receivers.FeedbackMailList.get_mail_list_by_item_id", side_effect=ex):
        with patch("weko_deposit.receivers.weko_logger") as mock_logger:
            res = append_file_content(sender, json, es_records[1][0]['record'])
            assert res==None
            mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            mock_logger.reset_mock()

    # SQLAlchemyError
    ex = SQLAlchemyError("sql_error")
    with patch("weko_deposit.receivers.WekoDeposit.get_record", side_effect=ex):
        with patch("weko_deposit.receivers.weko_logger") as mock_logger:
            append_file_content(sender, json, es_records[1][0]['record'])
            mock_logger.assert_any_call(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
            mock_logger.reset_mock()

    # WekoRecordsError
    ex = WekoRecordsError("record_error")
    with patch("weko_deposit.receivers.WekoDeposit.get_record", side_effect=ex):
            with pytest.raises(WekoRecordsError):
                append_file_content(sender, json, es_records[1][0]['record'])

    # Exception
    ex = Exception("unexpected_error")
    with patch("weko_deposit.receivers.WekoDeposit.get_record", side_effect=ex):
        with patch("weko_deposit.receivers.weko_logger") as mock_logger:
            append_file_content(sender, json, es_records[1][0]['record'])
            mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            mock_logger.reset_mock()
