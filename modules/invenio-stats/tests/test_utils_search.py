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
def test_billing_file_search_factory(i18n_app, role_users):
    from os.path import join, dirname
    search = RecordsSearch()
    with patch("flask_login.utils._get_user", return_value=role_users[3]['obj']):
        with patch('flask_principal.Permission.can', MagicMock(return_value=True)):
            search, urlkwargs = billing_file_search_factory(search)
            current_app.logger.info(search)
            current_app.logger.info(urlkwargs)
            with open(join(dirname(__file__), 'data', 'billing_file_query.json')) as json_file:
                expected = json.load(json_file)
            assert search.to_dict() == expected
            with patch('invenio_search.api.RecordsSearch.filter', side_effect=SyntaxError()):
                with pytest.raises(InvalidQueryRESTError) as e:
                    billing_file_search_factory(RecordsSearch())


# def get_permission_filter(index_id: str = None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils_search.py::test_get_permission_filter -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
class MockSearchPerm:
    def can(self):
        return True

def test_get_permission_filter(i18n_app, role_users):
    with patch("flask_login.utils._get_user", return_value=role_users[3]['obj']):
        with patch('flask_principal.Permission.can', MagicMock(return_value=True)):
            res = get_permission_filter('33')
            assert res==([Bool(must=[Terms(path=[])], should=[Match(weko_creator_id='3'), Match(weko_shared_id='3'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['1','2','3','4'])
            with patch('invenio_stats.utils_search.check_admin_user', return_value=('1', False)):
                res = get_permission_filter('33')
                assert res==([], ['1', '2', '3', '4'])
                res = get_permission_filter('1')
                assert res==([], ['1', '2', '3', '4'])
            with i18n_app.test_request_context(data={'search_type': '0'}):
                res = get_permission_filter('33')
                assert res==([Bool(must=[Bool()], should=[Match(weko_creator_id='3'), Match(weko_shared_id='3'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['1', '2', '3', '4'])
                res = get_permission_filter('1')
                assert res==([Bool(must=[Bool(should=[Terms(path='1')])], should=[Match(weko_creator_id='3'), Match(weko_shared_id='3'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['1', '2', '3', '4'])
            mock_searchperm = MagicMock(side_effect=MockSearchPerm)
            with patch('weko_search_ui.query.search_permission', mock_searchperm):
                    res = get_permission_filter()
                    assert res==([Bool(must=[Terms(path=['1', '2', '3', '4'])], should=[Match(weko_creator_id='3'), Match(weko_shared_id='3'), Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'})])]), Bool(must=[Match(relation_version_is_last='true')])], ['1','2','3','4'])
        with patch('flask_principal.Permission.can', return_value=False):
            res = get_permission_filter('33')
            assert res==([Match(publish_status='0'), Range(publish_date={'lte': 'now/d'}), Terms(path=[]), Bool(must=[Match(publish_status='0'), Match(relation_version_is_last='true')])], ['1','2','3','4'])


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
