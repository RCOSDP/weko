import pytest
from mock import MagicMock, patch
from werkzeug.exceptions import NotFound

from invenio_resourcesyncserver.permissions import (
    can_download_file,
    is_public_record,
    public_record_required
)


PUBLIC = {
    "publish_status": "0",
    "pubdate": {"attribute_value": "2022-08-20"},
    "path": ["1"],
}
PRIVATE = {
    "publish_status": "1",
    "pubdate": {"attribute_value": "2022-08-20"},
    "path": ["1"],
}
DELETED = {
    "publish_status": "-1",
    "pubdate": {"attribute_value": "2022-08-20"},
    "path": ["1"],
}
FUTURE = {
    "publish_status": "0",
    "pubdate": {"attribute_value": "2999-01-01"},
    "path": ["1"],
}


def _records(mapping):
    def get_record_by_pid(pid):
        if pid not in mapping:
            raise Exception("pid does not exist")
        return mapping[pid]
    return get_record_by_pid


# def is_public_record(record_id):
@pytest.mark.parametrize("records, record_id, private_index, expected", [
    ({"1": PUBLIC}, "1", False, True),
    ({"1": PUBLIC}, 1, False, True),
    ({"1": PRIVATE}, "1", False, False),
    ({"1": DELETED}, "1", False, False),
    ({"1": FUTURE}, "1", False, False),
    ({"1": PUBLIC}, "1", True, False),
    ({}, "1", False, False),
    # versioned identifier: the parent record is checked as well
    ({"1": PUBLIC, "1.1": PUBLIC}, "1.1", False, True),
    ({"1": PRIVATE, "1.1": PUBLIC}, "1.1", False, False),
    ({"1": PUBLIC, "1.1": PRIVATE}, "1.1", False, False),
    ({"1.1": PUBLIC}, "1.1", False, False),
])
def test_is_public_record(i18n_app, records, record_id, private_index, expected):
    with patch("weko_deposit.api.WekoRecord.get_record_by_pid", side_effect=_records(records)):
        with patch("invenio_oaiserver.response.is_private_index", return_value=private_index):
            assert is_public_record(record_id) == expected


# def public_record_required(param='record_id'):
def test_public_record_required(i18n_app):
    @public_record_required()
    def view(index_id, record_id):
        return "ok"

    with patch("invenio_resourcesyncserver.permissions.is_public_record", return_value=True) as m:
        assert view(index_id=1, record_id="2") == "ok"
        m.assert_called_once_with("2")

    with patch("invenio_resourcesyncserver.permissions.is_public_record", return_value=False):
        with pytest.raises(NotFound):
            view(index_id=1, record_id="2")

    @public_record_required(param="recid")
    def view2(recid=None):
        return "ok"

    with patch("invenio_resourcesyncserver.permissions.is_public_record", return_value=True):
        assert view2(recid="3") == "ok"
        with pytest.raises(NotFound):
            view2()


# def can_download_file(record, file):
def test_can_download_file(i18n_app):
    record = {"recid": "1"}
    file = MagicMock()
    file.info.return_value = {"filename": "a.txt", "accessrole": "open_access"}
    target = "weko_records_ui.permissions.check_file_download_permission"

    with patch(target, return_value=True) as m:
        assert can_download_file(record, file) is True
        m.assert_called_once_with(record, file.info.return_value)
    with patch(target, return_value=False):
        assert can_download_file(record, file) is False
    with patch(target, return_value=None):
        assert can_download_file(record, file) is False
    with patch(target, side_effect=Exception("error")):
        assert can_download_file(record, file) is False


# check_file_download_permission is not mocked: a file whose access role
# does not allow anonymous download is excluded.
@pytest.mark.parametrize("fjson, expected", [
    ({"filename": "a.txt", "accessrole": "open_access",
      "date": [{"dateType": "Available", "dateValue": "2000-01-01"}]}, True),
    ({"filename": "a.txt", "accessrole": "open_access",
      "date": [{"dateType": "Available", "dateValue": "2999-01-01"}]}, False),
    ({"filename": "a.txt", "accessrole": "open_no"}, False),
])
def test_can_download_file_guest(i18n_app, users, fjson, expected):
    record = {"recid": "1", "item_type_id": "1", "owner": "1",
              "_deposit": {"created_by": 1}}
    file = MagicMock()
    file.info.return_value = fjson
    assert can_download_file(record, file) == expected
