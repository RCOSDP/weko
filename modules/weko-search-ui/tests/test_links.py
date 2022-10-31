import pytest
import copy
from unittest.mock import MagicMock

from weko_search_ui.links import default_links_factory


def test_default_links_factory(app, client_rest_weko_search_ui):
    pid = MagicMock()
    pid.pid_value = "1.0"
    with app.test_request_context():
        assert not default_links_factory(pid, method="HTTPS") == ""