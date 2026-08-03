import json
from elasticsearch_dsl.query import Match, Range, Terms, Bool
from flask import current_app
from invenio_search.api import RecordsSearch
from invenio_records_rest.errors import InvalidQueryRESTError
from mock import MagicMock, Mock, patch
import pytest

from invenio_stats.utils_search import (
    billing_file_search_factory,
    check_admin_user, get_permission_filter
)


# .tox/c1/bin/pytest -vv -s --basetemp=/code/modules/invenio-stats/.tox/c1/tmp --full-trace tests/test_utils_search.py --cov=invenio_stats --cov-branch --cov-report=term

# def billing_file_search_factory(search):
#   def get_permission_filter(index_id: str = None):
#   def check_admin_user():
# .tox/c1/bin/pytest -vv -s --basetemp=/code/modules/invenio-stats/.tox/c1/tmp --full-trace tests/test_utils_search.py::test_billing_file_search_factory --cov=invenio_stats --cov-branch --cov-report=term
def test_billing_file_search_factory(i18n_app, role_users, indextree):
    from os.path import join, dirname
    search = RecordsSearch()
    with patch("flask_login.utils._get_user", return_value=role_users[3]['obj']):
        search, urlkwargs = billing_file_search_factory(search)
        current_app.logger.info(search)
        current_app.logger.info(urlkwargs)
        with open(join(dirname(__file__), 'data', 'billing_file_query.json')) as json_file:
            expected = json.load(json_file)
        assert search.to_dict() == expected
        with patch('invenio_search.api.RecordsSearch.filter', side_effect=SyntaxError()):
            with pytest.raises(InvalidQueryRESTError) as e:
                billing_file_search_factory(RecordsSearch())

    # auto send report
    search2 = RecordsSearch()
    search2, urlkwargs2 = billing_file_search_factory(search2)
    current_app.logger.info(search2)
    current_app.logger.info(urlkwargs2)
    with open(join(dirname(__file__), 'data', 'billing_file_query.json')) as json_file:
        expected2 = json.load(json_file)
    assert search2.to_dict() == expected2
    with patch('invenio_search.api.RecordsSearch.filter', side_effect=SyntaxError()):
        with pytest.raises(InvalidQueryRESTError) as e:
            billing_file_search_factory(RecordsSearch())


# def get_permission_filter(index_id: str = None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils_search.py::test_get_permission_filter -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_get_permission_filter(i18n_app, role_users, indextree):
    res = get_permission_filter()
    assert res == [
        Bool(should=[Bool(must=[
            Match(publish_status='0'),
            Range(publish_date={'lte': 'now/d'})
        ])]),
        Bool(must=Match(relation_version_is_last='true'))
    ]


# def check_admin_user():
# .tox/c1/bin/pytest -vv -s --basetemp=/code/modules/invenio-stats/.tox/c1/tmp --full-trace tests/test_utils_search.py::test_check_admin_user --cov=invenio_stats --cov-branch --cov-report=term
def test_check_admin_user(i18n_app, roles):
    mock_auth_user = Mock()
    mock_auth_user.get_id = lambda: '123'
    mock_auth_user.is_authenticated = True
    mock_auth_user.roles = [roles['System Administrator'], roles['Contributor']]
    with patch("flask_login.utils._get_user", return_value=mock_auth_user):
        res = check_admin_user()
        assert res==('123', True)

    mock_anon_user = Mock()
    mock_anon_user.is_authenticated = False
    with patch("flask_login.utils._get_user", return_value=mock_anon_user):
        res = check_admin_user()
        assert res==(None, True)
