
import pkg_resources
import pytest
from mock import MagicMock, patch
from flask_login import login_user
from werkzeug.exceptions import Forbidden, NotFound, Unauthorized

from weko_admin.permissions import admin_permission_factory, \
    repository_scope_required
# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp


# def admin_permission_factory(action):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_admin_permission_factory -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_admin_permission_factory(app, users):
    action = "update-style-action"
    result = admin_permission_factory(action)
    permission_values = [permission.value for permission in list(result.needs)]
    assert action in permission_values

    with patch("weko_admin.permissions.pkg_resources.get_distribution", side_effect=pkg_resources.DistributionNotFound):
        result = admin_permission_factory(action)
        permission_values = [permission.value for permission in list(result.needs)]
        assert action in permission_values


# def repository_scope_required(...):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_anonymous -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_anonymous(app):
    """未ログインの場合は401になること。"""
    @repository_scope_required(repository_id_param='repo_id')
    def view(*args, **kwargs):
        return 'ok'

    with app.test_request_context('/?repo_id=repoA'):
        with pytest.raises(Unauthorized):
            view()


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_super_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("index", [0, 1])  # sysadmin, repoadmin
def test_repository_scope_required_super_user(app, users, index):
    """System/Repository Administratorは無条件で許可されること。"""
    @repository_scope_required(repository_id_param='repo_id')
    def view(*args, **kwargs):
        return 'ok'

    with app.test_request_context('/?repo_id=repoA'):
        login_user(users[index]["obj"])
        assert view() == 'ok'


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_no_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_no_role(app, users):
    """ロールなしログインユーザーは拒否されること。"""
    @repository_scope_required(repository_id_param='repo_id')
    def view(*args, **kwargs):
        return 'ok'

    with app.test_request_context('/?repo_id=repoA'):
        login_user(users[4]["obj"])  # generaluser
        with pytest.raises(Forbidden):
            view()


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_community_admin_allowed -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_community_admin_allowed(app, users):
    """担当コミュニティのCommunity Administratorは許可されること。"""
    @repository_scope_required(repository_id_param='repo_id')
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoA')
    with app.test_request_context('/?repo_id=repoA'):
        login_user(users[2]["obj"])  # comadmin
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            assert view() == 'ok'


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_community_admin_denied -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_community_admin_denied(app, users):
    """担当外コミュニティのCommunity Administratorは拒否されること。"""
    @repository_scope_required(repository_id_param='repo_id')
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoB')
    with app.test_request_context('/?repo_id=repoA'):
        login_user(users[2]["obj"])  # comadmin(repoBのみ担当)
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            with pytest.raises(Forbidden):
                view()


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_id_param_prefers_db_value -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_id_param_prefers_db_value(app, users):
    """id_param指定時はDB側の値を優先してスコープ判定すること。"""
    record = MagicMock(repository_id='repoA')
    id_model = MagicMock()
    id_model.query.filter_by.return_value.one_or_none.return_value = record

    @repository_scope_required(repository_id_param='repository_id',
                                id_param='page_id', id_model=id_model)
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoA')
    # bodyには担当外のrepoBが送られているが、DB側(repoA)が優先されて許可される
    with app.test_request_context('/?repository_id=repoB&page_id=1'):
        login_user(users[2]["obj"])  # comadmin(repoAを担当)
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            assert view() == 'ok'
    id_model.query.filter_by.assert_called_with(id='1')


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_id_param_not_found -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_id_param_not_found(app, users):
    """id_paramで指定したレコードが存在しない場合は404になること。"""
    id_model = MagicMock()
    id_model.query.filter_by.return_value.one_or_none.return_value = None

    @repository_scope_required(id_param='page_id', id_model=id_model)
    def view(*args, **kwargs):
        return 'ok'

    with app.test_request_context('/?page_id=999'):
        login_user(users[2]["obj"])  # comadmin
        with pytest.raises(NotFound):
            view()


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_no_repository_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_no_repository_id(app, users):
    """repository_idが取得できない場合は拒否されること。"""
    @repository_scope_required(repository_id_param='repo_id')
    def view(*args, **kwargs):
        return 'ok'

    with app.test_request_context('/'):
        login_user(users[2]["obj"])  # comadmin
        with pytest.raises(Forbidden):
            view()
