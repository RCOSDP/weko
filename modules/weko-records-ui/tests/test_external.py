# import pytest
import json
from mock import patch, MagicMock
from pytest_mock import mocker
from flask import current_app
import copy
import requests
from datetime import datetime, timedelta

from weko_schema_ui.models import PublishStatus
from weko_deposit.api import WekoRecord
from weko_records.models import ItemReference
from weko_records_ui.external import(
call_external_system,
select_call_external_system_list,
get_action,
get_article_id,
get_file_counts,
get_record_diff,
get_pid_value_without_ver,
validate_records,
OAPublishStatus
)


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_external.py::test_call_external_system -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_call_external_system(app, records, mocker):
    EXTERNAL_SYSTEM = current_app.config.get("EXTERNAL_SYSTEM")
    ITEM_ACTION = current_app.config.get("ITEM_ACTION")
    FILE_OPEN_STATUS = current_app.config.get("FILE_OPEN_STATUS")

    token_api_response = MagicMock()
    token_api_response.text = ""
    article_id = 1234
    mocker.patch("weko_records_ui.external.get_article_id",
                 return_value=article_id)
    api_cert = {
        "cert_data": {
            "client_id": "aaa",
            "secret": "bbb"
        }
    }

    # cases until token api
    with patch('requests.Session.post',
               return_value=token_api_response) as token_api_mock:
        record1 = WekoRecord.get_record_by_pid(1)

        # case not valid
        call_external_system()
        token_api_mock.assert_not_called()

        # case old_record == new_record
        call_external_system(record1, record1, [], [])
        token_api_mock.assert_not_called()

        with patch("weko_records_ui.external.ApiCertificate.select_by_api_code",
                    return_value=None):
            # case none
            call_external_system(new_record=record1)
            token_api_mock.assert_not_called()

        with patch("weko_records_ui.external.ApiCertificate.select_by_api_code",
                    return_value=api_cert):
            # case no client_id, secret
            api_cert["cert_data"]["client_id"] = ""
            api_cert["cert_data"]["secret"] = ""
            call_external_system(new_record=record1)
            token_api_mock.assert_not_called()

            # case no secret
            api_cert["cert_data"]["client_id"] = "aaa"
            api_cert["cert_data"]["secret"] = ""
            call_external_system(new_record=record1)
            token_api_mock.assert_not_called()

            # case no client_id
            api_cert["cert_data"]["client_id"] = ""
            api_cert["cert_data"]["secret"] = "bbb"
            call_external_system(new_record=record1)
            token_api_mock.assert_not_called()

    api_cert = {
        "cert_data": {
            "client_id": "aaa",
            "client_secret": "bbb"
        }
    }
    mocker.patch("weko_records_ui.external.ApiCertificate.select_by_api_code",
                 return_value=api_cert)

    # cases between token api and update api
    with patch('requests.Session.put') as update_api_mock:
        # case RequestException
        with patch('requests.Session.post',
                   side_effect=requests.exceptions.RequestException):
            call_external_system(new_record=record1)
            update_api_mock.assert_not_called()

        # no token in response
        token_api_response = MagicMock()
        token_api_response.text = ""
        with patch('requests.Session.post', return_value=token_api_response):
            call_external_system(new_record=record1)
            update_api_mock.assert_not_called()

    # cases update api
    token_api_response.text = '{"access_token": "mocked_token"}'
    mocker.patch('requests.Session.post', return_value=token_api_response)

    update_api_response = MagicMock()
    update_api_response.text = ""
    update_api_response.status_code = 200

    with patch("weko_logging.activity_logger.UserActivityLogger.info") as mock_logger:
        result = {}
        result[EXTERNAL_SYSTEM.OA.value] = {"status": "ok"}
        update_api_response.json = lambda: {"status":"ok"}

        url = current_app.config.get(
            "WEKO_RECORDS_UI_OA_UPDATE_STATUS_URL").format(article_id)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mocked_token'
        }

        file_counts = {}
        file_counts[FILE_OPEN_STATUS.PUBLIC.value] = 1
        file_counts[FILE_OPEN_STATUS.EMBARGO.value] = 0
        file_counts[FILE_OPEN_STATUS.PRIVATE.value] = 0
        file_counts[FILE_OPEN_STATUS.RESTRICTED.value] = 0
        data = {}
        data["status_action"] = ITEM_ACTION.CREATED.value
        data["item_info"] = {}
        data["item_info"]["pub_date"] = record1["pubdate"]["attribute_value"]
        data["file_counts"] = file_counts

        # case create item
        with patch('requests.Session.put',
                    return_value=update_api_response) as update_api_mock:
            data["item_info"]["publish_status"] = OAPublishStatus.PUBLISHED.value
            call_external_system(new_record=record1)
            update_api_mock.assert_called_once_with(
                url, headers=headers, json=data
            )

        # case delete item
        with patch('requests.Session.put',
                    return_value=update_api_response) as update_api_mock:
            call_external_system(old_record=record1)
            data["status_action"] = ITEM_ACTION.DELETED.value
            data["item_info"]["publish_status"] = OAPublishStatus.DELETED.value
            update_api_mock.assert_called_once_with(
                url, headers=headers, json=data
            )

        # case update item
        with patch('requests.Session.put',
                    return_value=update_api_response) as update_api_mock:
            record1["publish_status"] = PublishStatus.PUBLIC.value
            record2 = copy.deepcopy(record1)
            record2["publish_status"] = PublishStatus.PRIVATE.value
            call_external_system(old_record=record1, new_record=record2)
            data["status_action"] = ITEM_ACTION.UPDATED.value
            data["item_info"]["publish_status"] = OAPublishStatus.DRAFT.value
            update_api_mock.assert_called_once_with(
                url, headers=headers, json=data
            )

        # case 500 error
        update_api_response.status_code = 500
        update_api_response.json = lambda: {"status":"ng", "message": "error"}
        expected_remarks = {
            "action": ITEM_ACTION.CREATED.value,
            EXTERNAL_SYSTEM.OA.value: {"status":"ng", "message": "error"}
        }
        with patch('requests.Session.put', return_value=update_api_response
                    ) as update_api_mock:
            call_external_system(new_record=record1)
            update_api_mock.assert_called_once()
            mock_logger.assert_called_with(
                operation="ITEM_EXTERNAL_LINK",
                target_key="1",
                request_info=None,
                remarks=json.dumps(expected_remarks),
                required_commit=False
            )

        # case RequestException
        expected_remarks = {
            "action": ITEM_ACTION.CREATED.value,
            EXTERNAL_SYSTEM.OA.value: {"status":"error"}
        }
        with patch('requests.Session.put',
                    side_effect=requests.exceptions.RequestException
                    ) as update_api_mock:
            call_external_system(new_record=record1)
            update_api_mock.assert_called_once()
            mock_logger.assert_called_with(
                operation="ITEM_EXTERNAL_LINK",
                target_key="1",
                request_info=None,
                remarks=json.dumps(expected_remarks),
                required_commit=False
            )


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_external.py::test_call_external_system_error_config -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_call_external_system_error_config(app, records, mocker):
    # case config error
    EXTERNAL_SYSTEM = current_app.config.get("EXTERNAL_SYSTEM")
    WEKO_RECORDS_UI_OA_GET_TOKEN_URL = current_app.config.get(
        "WEKO_RECORDS_UI_OA_GET_TOKEN_URL")
    record1 = WekoRecord.get_record_by_pid(1)
    token_api_response = MagicMock()
    token_api_response.text = "mocked_token"
    article_id = 1234
    api_cert = {
        "cert_data": {
            "client_id": "aaa",
            "secret": "bbb"
        }
    }
    mocker.patch("weko_records_ui.external.get_article_id",
                 return_value=article_id)
    mocker.patch("weko_records_ui.external.ApiCertificate.select_by_api_code",
                 return_value=api_cert)
    with patch('requests.Session.put',
                   return_value=None) as update_api_mock:
        # case EXTERNAL_SYSTEM is None
        current_app.config.update(EXTERNAL_SYSTEM=None)
        with patch("weko_records_ui.external.validate_records") as mock_validate:
            call_external_system(record1)
            mock_validate.assert_not_called()

        current_app.config.update(EXTERNAL_SYSTEM=EXTERNAL_SYSTEM)

        # case WEKO_RECORDS_UI_OA_GET_TOKEN_URL is None
        current_app.config.update(WEKO_RECORDS_UI_OA_GET_TOKEN_URL=None)
        with patch('requests.Session.post',
                   return_value=token_api_response) as token_api_mock:
            call_external_system(new_record=record1)
            token_api_mock.assert_not_called()
            update_api_mock.assert_not_called()

        # case WEKO_RECORDS_UI_OA_GET_TOKEN_URL == ""
        current_app.config.update(WEKO_RECORDS_UI_OA_GET_TOKEN_URL="")
        with patch('requests.Session.post',
                   return_value=token_api_response) as token_api_mock:
            call_external_system(new_record=record1)
            token_api_mock.assert_not_called()
            update_api_mock.assert_not_called()

        current_app.config.update(
            WEKO_RECORDS_UI_OA_GET_TOKEN_URL=WEKO_RECORDS_UI_OA_GET_TOKEN_URL)

        # case WEKO_RECORDS_UI_OA_UPDATE_STATUS_URL is None
        current_app.config.update(WEKO_RECORDS_UI_OA_UPDATE_STATUS_URL=None)
        with patch('requests.Session.post',
                   return_value=token_api_response) as token_api:
            call_external_system(new_record=record1)
            token_api.assert_called()
            update_api_mock.assert_not_called()

        # case WEKO_RECORDS_UI_OA_UPDATE_STATUS_URL == ""
        current_app.config.update(WEKO_RECORDS_UI_OA_UPDATE_STATUS_URL="")
        with patch('requests.Session.post',
                   return_value=token_api_response) as token_api:
            call_external_system(new_record=record1)
            token_api.assert_called()
            update_api_mock.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_external.py::test_select_call_external_system_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_select_call_external_system_list(app, records, mocker):
    EXTERNAL_SYSTEM = current_app.config.get("EXTERNAL_SYSTEM")
    today = datetime.today()
    today_date = today.strftime('%Y-%m-%d')
    tommorow = today + timedelta(days=1)
    tommorow_date = tommorow.strftime('%Y-%m-%d')
    record1 = WekoRecord.get_record_by_pid(1)
    article_id = 1234

    # case no article id
    with patch("weko_records_ui.external.get_article_id",
            return_value=None):
        system_list = select_call_external_system_list(old_record=record1)
        assert system_list == []

    # case Exception
    with patch("weko_records_ui.external.get_article_id",
            side_effect=Exception):
        system_list = select_call_external_system_list(record1, record1)
        assert system_list == []

    mocker.patch("weko_records_ui.external.get_article_id",
                 return_value=article_id)
    # case no args
    system_list = select_call_external_system_list()
    assert system_list == []

    # case old_record only
    system_list = select_call_external_system_list(old_record=record1)
    assert system_list == [EXTERNAL_SYSTEM.OA]

    # case new_record only
    system_list = select_call_external_system_list(new_record=record1)
    assert system_list == [EXTERNAL_SYSTEM.OA]

    record_publish_status = copy.deepcopy(record1)
    record_pubdate = copy.deepcopy(record1)
    record_file = copy.deepcopy(record1)
    record1["publish_status"] = PublishStatus.PUBLIC.value
    record_publish_status["publish_status"] = PublishStatus.PRIVATE.value
    record1["pubdate"]["attribute_value"] = today_date
    record_pubdate["pubdate"]["attribute_value"] = tommorow_date
    file = {"accessrole": "open_date",
            "date": [{"dateValue": today_date}]}
    for property in record1.values():
        if isinstance(property, dict):
            if property.get("attribute_type") == "file":
                property["attribute_value_mlt"] = [file]
    file = {"accessrole": "open_date",
            "date": [{"dateValue": tommorow_date}]}
    for property in record_file.values():
        if isinstance(property, dict):
            if property.get("attribute_type") == "file":
                property["attribute_value_mlt"] = [file]

    # case old_record == new_record
    system_list = select_call_external_system_list(record1, record1)
    assert system_list == []

    # case publish_status is different
    system_list = select_call_external_system_list(record1, record_publish_status)
    assert system_list == [EXTERNAL_SYSTEM.OA]

    # case pubdate is different
    system_list = select_call_external_system_list(record1, record_pubdate)
    assert system_list == [EXTERNAL_SYSTEM.OA]

    # case file_count is different
    system_list = select_call_external_system_list(record1, record_file)
    assert system_list == [EXTERNAL_SYSTEM.OA]


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_external.py::test_get_pid_value_without_ver -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_pid_value_without_ver(app, records):
    record1 = WekoRecord.get_record_by_pid(1)
    record2 = WekoRecord.get_record_by_pid(2)
    record1_1 = copy.deepcopy(record1)
    record1_1["recid"] = "1.1"

    assert get_pid_value_without_ver(record1, record2) is None
    assert get_pid_value_without_ver(record1, None) == "1"
    assert get_pid_value_without_ver(None, record1) == "1"
    assert get_pid_value_without_ver(record1, record1) == "1"
    assert get_pid_value_without_ver(record1, record1_1) == "1"


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_external.py::test_get_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_action(app, records):
    record = WekoRecord.get_record_by_pid(1)
    ITEM_ACTION = current_app.config.get("ITEM_ACTION")
    assert get_action(None, record) == ITEM_ACTION.CREATED
    assert get_action(record, record) == ITEM_ACTION.UPDATED
    assert get_action(record, None) == ITEM_ACTION.DELETED
    assert get_action(None, None) is None


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_external.py::test_get_article_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_article_id():
    mock_oa_status = MagicMock()
    article_id = 1234

    with patch(
            "weko_records_ui.external.OaStatus.get_oa_status_by_weko_item_pid",
            return_value=mock_oa_status
        ):
        mock_oa_status.oa_article_id = article_id
        assert get_article_id(1) == article_id
    with patch(
            "weko_records_ui.external.OaStatus.get_oa_status_by_weko_item_pid",
            return_value=None
        ):
        assert get_article_id(1) is None


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_external.py::test_file_counts -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_counts(app):
    today = datetime.today()
    today_date = today.strftime('%Y-%m-%d')
    tommorow = today + timedelta(days=1)
    tommorow_date = tommorow.strftime('%Y-%m-%d')

    FILE_OPEN_STATUS = current_app.config.get("FILE_OPEN_STATUS")
    file_counts_0 = {}
    file_counts_0[FILE_OPEN_STATUS.PUBLIC.value] = 0
    file_counts_0[FILE_OPEN_STATUS.EMBARGO.value] = 0
    file_counts_0[FILE_OPEN_STATUS.PRIVATE.value] = 0
    file_counts_0[FILE_OPEN_STATUS.RESTRICTED.value] = 0

    file_counts_public = copy.deepcopy(file_counts_0)
    file_counts_public[FILE_OPEN_STATUS.PUBLIC.value] = 1

    file_counts_embargo = copy.deepcopy(file_counts_0)
    file_counts_embargo[FILE_OPEN_STATUS.EMBARGO.value] = 1

    file_counts_private = copy.deepcopy(file_counts_0)
    file_counts_private[FILE_OPEN_STATUS.PRIVATE.value] = 1

    file_counts_restricted = copy.deepcopy(file_counts_0)
    file_counts_restricted[FILE_OPEN_STATUS.RESTRICTED.value] = 1

    # cases public
    file = {"accessrole": "open_access"}
    assert get_file_counts([file]) == file_counts_public
    file = {"accessrole": "open_date",
            "date": [{"dateValue": today_date}],
            "accessdate": today_date}
    assert get_file_counts([file]) == file_counts_public
    file = {"accessrole": "open_date",
            "date": [{"dateValue": tommorow_date}],
            "accessdate": today_date}
    assert get_file_counts([file]) == file_counts_public
    file = {"accessrole": "open_date",
            "date": [{"dateValue": today_date}]}
    assert get_file_counts([file]) == file_counts_public
    file = {"accessrole": "open_date",
            "accessdate": today_date}
    assert get_file_counts([file]) == file_counts_public

    # cases embargo
    file = {"accessrole": "open_date",
            "date": [{"dateValue": today_date}],
            "accessdate": tommorow_date}
    assert get_file_counts([file]) == file_counts_embargo
    file = {"accessrole": "open_date",
            "date": [{"dateValue": tommorow_date}],
            "accessdate": tommorow_date}
    assert get_file_counts([file]) == file_counts_embargo
    file = {"accessrole": "open_date",
            "date": [{"dateValue": tommorow_date}]}
    assert get_file_counts([file]) == file_counts_embargo
    file = {"accessrole": "open_date",
            "accessdate": tommorow_date}
    assert get_file_counts([file]) == file_counts_embargo

    # cases private
    file = {"accessrole": "open_no"}
    assert get_file_counts([file]) == file_counts_private
    file = {"accessrole": "open_login"}
    assert get_file_counts([file]) == file_counts_private

    # cases restricted
    file = {"accessrole": "open_restricted"}
    assert get_file_counts([file]) == file_counts_restricted

    # case None
    file = {"accessrole": ""}
    assert get_file_counts([file]) == file_counts_0


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_external.py::test_validate_records -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_validate_records(app, records):
    record1 = WekoRecord.get_record_by_pid("1")
    record2 = copy.deepcopy(record1)
    ref1 = ItemReference(
        src_item_pid="1",
        dst_item_pid="1",
        reference_type="a"
    )
    ref2 = copy.deepcopy(ref1)

    assert validate_records(record1, record2, [ref1], [ref2])
    assert not validate_records(1, None, None, None)
    assert not validate_records(None, 1, None, None)
    assert not validate_records(None, None, None, None)
    assert not validate_records(record1, record2, [1], [])
    assert not validate_records(record1, record2, [], [1])
    assert not validate_records(record1, record2, 1, [])
    assert not validate_records(record1, record2, [], 1)

    record1["recid"] = "1"
    record2["recid"] = "2"
    assert not validate_records(record1, record2, None, None)

    record1["recid"] = "1"
    record2["recid"] = "1"
    ref1.src_item_pid = "2"
    assert not validate_records(record1, record2, [ref1], [])

    record1["recid"] = "1"
    record2["recid"] = "1"
    ref2.src_item_pid = "2"
    assert not validate_records(record1, record2, [], [ref2])

    record1["recid"] = "1"
    record2["recid"] = "1.0"
    ref1.src_item_pid = "1.1"
    ref2.src_item_pid = "1.2"
    assert validate_records(record1, record2, [ref1], [ref2])


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_external.py::test_get_record_diff -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_record_diff(app, records):
    today = datetime.today()
    today_date = today.strftime('%Y-%m-%d')
    tommorow = today + timedelta(days=1)
    tommorow_date = tommorow.strftime('%Y-%m-%d')

    FILE_OPEN_STATUS = current_app.config.get("FILE_OPEN_STATUS")
    file_counts_0 = {}
    file_counts_0[FILE_OPEN_STATUS.PUBLIC.value] = 0
    file_counts_0[FILE_OPEN_STATUS.EMBARGO.value] = 0
    file_counts_0[FILE_OPEN_STATUS.PRIVATE.value] = 0
    file_counts_0[FILE_OPEN_STATUS.RESTRICTED.value] = 0

    file_counts_public = copy.deepcopy(file_counts_0)
    file_counts_public[FILE_OPEN_STATUS.PUBLIC.value] = 1

    file_counts_embargo = copy.deepcopy(file_counts_0)
    file_counts_embargo[FILE_OPEN_STATUS.EMBARGO.value] = 1

    file = {"accessrole": "open_date",
            "date": [{"dateValue": today_date}]}
    record1 = WekoRecord.get_record_by_pid(1)
    record1["publish_status"] = PublishStatus.PUBLIC.value
    record1["pubdate"]["attribute_value"] = today_date
    for property in record1.values():
        if isinstance(property, dict):
            if property.get("attribute_type") == "file":
                property["attribute_value_mlt"] = [file]

    record2 = copy.deepcopy(record1)
    record2["publish_status"] = PublishStatus.PRIVATE.value
    record2["pubdate"]["attribute_value"] = tommorow_date
    file = {"accessrole": "open_date",
            "date": [{"dateValue": tommorow_date}]}
    for property in record2.values():
        if isinstance(property, dict):
            if property.get("attribute_type") == "file":
                property["attribute_value_mlt"] = [file]

    # case old_record == new_record
    diff = get_record_diff(record1, record1)
    diff_before = diff["before"]
    diff_after = diff["after"]
    assert diff_before == {}
    assert diff_after == {}

    # case old_record only
    diff = get_record_diff(record1, None)
    diff_before = diff["before"]
    diff_after = diff["after"]
    assert diff_before["publish_status"] == record1["publish_status"]
    assert diff_before["pubdate"] == record1["pubdate"]["attribute_value"]
    assert diff_before["file_counts"] == file_counts_public
    assert diff_after["publish_status"] is None
    assert diff_after["pubdate"] is None
    assert diff_after["file_counts"] == file_counts_0

    # case new_record only
    diff = get_record_diff(None, record1)
    diff_before = diff["before"]
    diff_after = diff["after"]
    assert diff_before["publish_status"] is None
    assert diff_before["pubdate"] is None
    assert diff_before["file_counts"] == file_counts_0
    assert diff_after["publish_status"] == record1["publish_status"]
    assert diff_after["pubdate"] == record1["pubdate"]["attribute_value"]
    assert diff_after["file_counts"] == file_counts_public

    # case old_record != new_record
    diff = get_record_diff(record1, record2)
    diff_before = diff["before"]
    diff_after = diff["after"]
    assert diff_before["publish_status"] == PublishStatus.PUBLIC.value
    assert diff_before["pubdate"] == today_date
    assert diff_before["file_counts"] == file_counts_public
    assert diff_after["publish_status"] == PublishStatus.PRIVATE.value
    assert diff_after["pubdate"] == tommorow_date
    assert diff_after["file_counts"] == file_counts_embargo
