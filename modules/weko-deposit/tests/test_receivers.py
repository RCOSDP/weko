import pytest
from unittest import mock
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError

from invenio_pidstore.models import PIDStatus

from weko_records.errors import WekoRecordsError
from weko_records.models import FeedbackMailList
from weko_deposit.logger import weko_logger
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
        mock_logger.reset_mock


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
        mock_logger.reset_mock


    #Throws an exception. Result of append_file_content is None.
    with patch("weko_deposit.receivers.FeedbackMailList.get_mail_list_by_item_id",side_effect=Exception("test_error")):
        with patch("weko_deposit.receivers.weko_logger") as mock_logger:
            res = append_file_content(sender, json, es_records[1][0]['record'])
            assert res==None
            mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
            mock_logger.reset_mock

    # SQLAlchemyError
    with patch("weko_deposit.receivers.WekoDeposit.get_record", side_effect=SQLAlchemyError("db_error")):
        with patch("weko_deposit.receivers.weko_logger") as mock_logger:
            append_file_content(sender, json, es_records[1][0]['record'])
            mock_logger.assert_any_call(key='WEKO_COMMON_DB_SOME_ERROR', ex=mock.ANY)
            mock_logger.reset_mock

    # WekoRecordsError
    with patch("weko_deposit.receivers.WekoDeposit.get_record", side_effect=WekoRecordsError("record_error")):
            with pytest.raises(WekoRecordsError):
                append_file_content(sender, json, es_records[1][0]['record'])

    # Exception
    with patch("weko_deposit.receivers.WekoDeposit.get_record", side_effect=Exception("unexpected_error")):
        with patch("weko_deposit.receivers.weko_logger") as mock_logger:
            append_file_content(sender, json, es_records[1][0]['record'])
            mock_logger.assert_any_call(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
            mock_logger.reset_mock

    # # record_metadata.status == PIDStatus.DELETED
    # with patch("weko_deposit.receivers.RecordMetadata.query.filter_by") as mock_query:
    #     mock_record_metadata = mock.Mock()
    #     mock_record_metadata.status = PIDStatus.DELETED
    #     mock_query.return_value.first.return_value = mock_record_metadata
    #     # mock_query.filter_by.return_value.one_or_none.return_value = mock_record_metadata
    #     with patch("weko_deposit.receivers.weko_logger") as mock_logger:
    #         append_file_content(sender, json, es_records[1][0]['record'])
    #         assert not any(call[1].get('key') == 'WEKO_DEPOSIT_APPEND_FILE_CONTENT' for call in mock_logger.call_args_list)
    #         mock_logger.assert_any_call(key='WEKO_COMMON_DB_SOME_ERROR', ex=mock.ANY)
