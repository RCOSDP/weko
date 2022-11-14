import json
import pytest
from flask import current_app, make_response, request, url_for
from flask_login import current_user
from mock import patch

from weko_admin.utils import (
    get_title_facets
)

# def get_title_facets():
def test_get_title_facets(i18n_app, users, facet_search_setting):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        titles, order, uiTypes, isOpens, displayNumbers = get_title_facets()
        assert uiTypes
        assert isOpens
        assert displayNumbers