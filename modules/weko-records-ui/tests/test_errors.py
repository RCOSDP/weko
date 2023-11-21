from mock import patch
from unittest.mock import MagicMock
import pytest
import io
from flask import Flask, json, jsonify, session, url_for
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session

from weko_records_ui.errors import InvalidWorkflowError
from flask_babelex import get_locale

class MockLocale():
    def __init__(self, return_value):
        self.return_value= return_value

    def get_language_name(self, lang):
        return self.return_value

#.tox/c1/bin/pytest --cov=weko_records_ui tests/test_errors.py::test_get_this_message -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_this_message(app):
    locale = ""
    restricted_error_msg = {"key" : "","content" : {"ja" : {"content" : "このデータは利用できません（権限がないため）。"},"en":{"content" : "This data is not available for this user"}}}
    #test No.4(W2023-22 3-5)
    with app.app_context():
        mock_locale = MockLocale("English")
        with patch("weko_records_ui.errors.get_locale", return_value=mock_locale):
            with patch("weko_admin.utils.get_restricted_access", return_value = restricted_error_msg):
                error = InvalidWorkflowError()
                result = error.get_this_message()
                assert result == restricted_error_msg['content']['en']['content']

    #test No.5(W2023-22 3-5)
    with app.app_context():
        mock_locale = MockLocale("Japanese")
        with patch("weko_records_ui.errors.get_locale", return_value=mock_locale):
            with patch("weko_admin.utils.get_restricted_access", return_value = restricted_error_msg):
                error = InvalidWorkflowError()
                result = error.get_this_message()
                assert result == restricted_error_msg['content']['ja']['content']