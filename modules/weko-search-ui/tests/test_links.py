import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch, MagicMock

from weko_search_ui.links import default_links_factory


# def test_default_links_factory(app):
#     pid = MagicMock()
#     pid.pid_value = "1.0"
#     with app.test_request_context():
#         assert default_links_factory(pid, method="HTTPS") == ""


def test_default_links_factory_2(i18n_app):
    pid = MagicMock()
    pid.pid_value = "1.0"
    with i18n_app.test_request_context():
        assert default_links_factory(pid, method="HTTPS") == ""
