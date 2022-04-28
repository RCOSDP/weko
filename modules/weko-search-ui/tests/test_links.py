import pytest

from unittest.mock import MagicMock

from weko_search_ui.links import default_links_factory


def test_default_links_factory(app):
    pid = MagicMock()
    pid.pid_value = "1.0"
    with app.test_request_context():
        assert default_links_factory(pid, method="HTTPS") == ""
