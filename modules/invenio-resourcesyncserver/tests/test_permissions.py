import pytest
from mock import patch
from werkzeug.exceptions import NotFound

from invenio_resourcesyncserver.permissions import (
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
