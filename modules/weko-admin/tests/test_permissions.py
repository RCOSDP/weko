
import pkg_resources
import pytest
from mock import MagicMock, patch
from flask_login import login_user
from werkzeug.exceptions import Forbidden, NotFound, Unauthorized

from weko_admin.permissions import _lookup_param, \
    admin_permission_factory, repository_scope_required
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


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_both_params_required -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_both_params_required(app, users):
    """DB側とbody側の両方が取得できる場合は双方が担当範囲内であることを要求すること。"""
    record = MagicMock(repository_id='repoA')
    id_model = MagicMock()
    id_model.query.filter_by.return_value.one_or_none.return_value = record

    @repository_scope_required(repository_id_param='repository_id',
                                id_param='page_id', id_model=id_model)
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoA')
    # DB側(repoA)は担当内だが、bodyで担当外のrepoBへの移動が指定されているため拒否
    with app.test_request_context('/?repository_id=repoB&page_id=1'):
        login_user(users[2]["obj"])  # comadmin(repoAを担当)
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            with pytest.raises(Forbidden):
                view()
    id_model.query.filter_by.assert_called_with(id='1')


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_db_out_of_scope -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_db_out_of_scope(app, users):
    """DB側が担当外の場合はbody側が担当内でも拒否されること。"""
    record = MagicMock(repository_id='repoB')
    id_model = MagicMock()
    id_model.query.filter_by.return_value.one_or_none.return_value = record

    @repository_scope_required(repository_id_param='repository_id',
                                id_param='page_id', id_model=id_model)
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoA')
    with app.test_request_context('/?repository_id=repoA&page_id=1'):
        login_user(users[2]["obj"])  # comadmin(repoAを担当)
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            with pytest.raises(Forbidden):
                view()


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_both_in_scope -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_both_in_scope(app, users):
    """DB側・body側とも担当内(同一ID)の場合は許可されること。"""
    record = MagicMock(repository_id='repoA')
    id_model = MagicMock()
    id_model.query.filter_by.return_value.one_or_none.return_value = record

    @repository_scope_required(repository_id_param='repository_id',
                                id_param='page_id', id_model=id_model)
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoA')
    with app.test_request_context('/?repository_id=repoA&page_id=1'):
        login_user(users[2]["obj"])  # comadmin(repoAを担当)
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            assert view() == 'ok'


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_move_within_scope -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_move_within_scope(app, users):
    """複数コミュニティ担当者による担当内から担当内への移動は許可されること。"""
    record = MagicMock(repository_id='repoA')
    id_model = MagicMock()
    id_model.query.filter_by.return_value.one_or_none.return_value = record

    @repository_scope_required(repository_id_param='repository_id',
                                id_param='page_id', id_model=id_model)
    def view(*args, **kwargs):
        return 'ok'

    communities = [MagicMock(id='repoA'), MagicMock(id='repoB')]
    with app.test_request_context('/?repository_id=repoB&page_id=1'):
        login_user(users[2]["obj"])  # comadmin(repoA/repoBを担当)
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=communities):
            assert view() == 'ok'


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_id_param_only -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("db_repository_id, allowed", [('repoA', True), ('repoB', False)])
def test_repository_scope_required_id_param_only(app, users, db_repository_id, allowed):
    """id_paramのみ値がある場合(削除系)はDB側の値だけで判定すること。"""
    record = MagicMock(repository_id=db_repository_id)
    id_model = MagicMock()
    id_model.query.filter_by.return_value.one_or_none.return_value = record

    @repository_scope_required(repository_id_param='repository_id',
                                id_param='page_id', id_model=id_model)
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoA')
    with app.test_request_context('/?page_id=1'):
        login_user(users[2]["obj"])  # comadmin(repoAを担当)
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            if allowed:
                assert view() == 'ok'
            else:
                with pytest.raises(Forbidden):
                    view()


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_repository_id_param_only -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("body_repository_id, allowed", [('repoA', True), ('repoB', False)])
def test_repository_scope_required_repository_id_param_only(app, users,
                                                            body_repository_id, allowed):
    """repository_id_paramのみ値がある場合(新規作成)はbody側の値だけで判定すること。"""
    id_model = MagicMock()

    @repository_scope_required(repository_id_param='repository_id',
                                id_param='page_id', id_model=id_model)
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoA')
    with app.test_request_context('/?repository_id={}'.format(body_repository_id)):
        login_user(users[2]["obj"])  # comadmin(repoAを担当)
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            if allowed:
                assert view() == 'ok'
            else:
                with pytest.raises(Forbidden):
                    view()
    id_model.query.filter_by.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_no_params -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_no_params(app, users):
    """id_param/repository_id_paramとも値がない場合は拒否されること。"""
    id_model = MagicMock()

    @repository_scope_required(repository_id_param='repository_id',
                                id_param='page_id', id_model=id_model)
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoA')
    with app.test_request_context('/'):
        login_user(users[2]["obj"])  # comadmin
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            with pytest.raises(Forbidden):
                view()


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_db_repository_id_none -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
def test_repository_scope_required_db_repository_id_none(app, users):
    """DBレコードのrepository_idがNoneの場合はbody側が担当内でも拒否されること。"""
    record = MagicMock(repository_id=None)
    id_model = MagicMock()
    id_model.query.filter_by.return_value.one_or_none.return_value = record

    @repository_scope_required(repository_id_param='repository_id',
                                id_param='page_id', id_model=id_model)
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoA')
    with app.test_request_context('/?repository_id=repoA&page_id=1'):
        login_user(users[2]["obj"])  # comadmin(repoAを担当)
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            with pytest.raises(Forbidden):
                view()


# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_repository_scope_required_nested_param -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("body_repository_id, allowed", [('repoA', True), ('repoB', False)])
def test_repository_scope_required_nested_param(app, users, body_repository_id, allowed):
    """repository_id_paramにドット記法を指定した場合はネストした値で判定すること。"""
    @repository_scope_required(repository_id_param='data.repository')
    def view(*args, **kwargs):
        return 'ok'

    community = MagicMock(id='repoA')
    with app.test_request_context(
            '/', json={'data': {'repository': body_repository_id}}):
        login_user(users[2]["obj"])  # comadmin(repoAを担当)
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                    return_value=[community]):
            if allowed:
                assert view() == 'ok'
            else:
                with pytest.raises(Forbidden):
                    view()


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


# def _lookup_param(data, kwargs, path):
# .tox/c1/bin/pytest --cov=weko_admin tests/test_permissions.py::test_lookup_param -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-admin/.tox/c1/tmp
@pytest.mark.parametrize("data, kwargs, path, expected", [
    # ドット無し: dataを優先
    ({'repo_id': 'repoA'}, {'repo_id': 'repoB'}, 'repo_id', 'repoA'),
    # ドット無し: dataに無ければkwargsにフォールバック
    ({}, {'repo_id': 'repoB'}, 'repo_id', 'repoB'),
    # ドット無し: dataの値がfalsyならkwargsにフォールバック
    ({'repo_id': ''}, {'repo_id': 'repoB'}, 'repo_id', 'repoB'),
    # ドット無し: どちらにも無い
    ({}, {}, 'repo_id', None),
    # ドット記法: ネストした値を取得
    ({'data': {'repository': 'repoA'}}, {}, 'data.repository', 'repoA'),
    # ドット記法: 途中がdictでない
    ({'data': 'foo'}, {}, 'data.repository', None),
    ({'data': None}, {}, 'data.repository', None),
    ({'data': [1, 2]}, {}, 'data.repository', None),
    # ドット記法: キーが存在しない
    ({'data': {}}, {}, 'data.repository', None),
    ({}, {}, 'data.repository', None),
    # ドット記法: 3階層
    ({'a': {'b': {'c': 'repoA'}}}, {}, 'a.b.c', 'repoA'),
    ({'a': {'b': {}}}, {}, 'a.b.c', None),
    # pathが未指定
    ({'repo_id': 'repoA'}, {}, None, None),
    ({'repo_id': 'repoA'}, {}, '', None),
])
def test_lookup_param(data, kwargs, path, expected):
    """_lookup_paramがdata/kwargs/ドット記法から正しく値を取得すること。"""
    assert _lookup_param(data, kwargs, path) == expected
