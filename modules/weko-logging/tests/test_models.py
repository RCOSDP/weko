# -*- coding: utf-8 -*-
""" Pytest for weko_logging models."""

from datetime import datetime
from unittest.mock import patch
from weko_logging.models import UserActivityLog


# UserActivityLog.get_sequence(session):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_models.py::test_get_sequence -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_get_sequence(db):
    """Test get sequence."""
    class MockSession:
        def __init__(self):
            self.id = {"user_activity_logs_id_seq":1}
        def execute(self, sequence):
            name = sequence.name
            self.id[name] += 1
            return self.id[name]
    session = MockSession()

    # Test session is None
    with patch("weko_logging.models.db.session.execute", side_effect=session.execute):
        sequence = UserActivityLog.get_sequence(None)
        assert sequence == 2

    # Test session is not None
    sequence = UserActivityLog.get_sequence(session)
    assert sequence == 3

# UserActivityLog.to_dict(self):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_models.py::test_to_dict -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
def test_to_dict(db, users):
    """Test to dict."""
    user_activity_log = UserActivityLog(
        date=datetime.now(),
        user_id=users[0]["id"],
        community_id=None,
        log_group_id=None,
        log={"operation": "test"},
        remarks="test"
    )
    db.session.add(user_activity_log)
    db.session.commit()
    assert user_activity_log.to_dict() == {
        "id": user_activity_log.id,
        "date": user_activity_log.date,
        "user_id": user_activity_log.user_id,
        "community_id": "",
        "log_group_id": "",
        "log": user_activity_log.log,
        "remarks": user_activity_log.remarks
    }