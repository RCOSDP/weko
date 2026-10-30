# -*- coding: utf-8 -*-
"""prioritize.classify の P1 判定のテスト。

    python3 -m pytest tools/api-inventory/tests
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'scripts'))
import credential_auth  # noqa: E402
import infra_auth  # noqa: E402
import prioritize  # noqa: E402

COLS = ['method', 'uri', 'auth_required', 'auth_method', 'data_op', 'data_store',
        'dynamic_verified', 'impl_file', 'impl_line', 'endpoint', 'test_gap']
H = {n: i for i, n in enumerate(COLS)}

VIEWS = '''
def login():
    if not verify_password(password, user.password):
        abort(401)
    login_user(user)


def update_item():
    item.update(request.json)
'''


@pytest.fixture(autouse=True)
def repo(tmp_path, monkeypatch):
    (tmp_path / 'pkg').mkdir()
    (tmp_path / 'pkg' / 'views.py').write_text(VIEWS, encoding='utf-8')
    monkeypatch.setenv('WEKO_ROOT', str(tmp_path))
    # nginx の設定は置かない(アプリの外側の認証は無し)
    monkeypatch.setenv('WEKO_NGINX_CONF', str(tmp_path / 'none.conf'))
    for f in (infra_auth._nginx, infra_auth._functions,
              credential_auth._parse, credential_auth._package_index):
        f.cache_clear()


def row(**kw):
    base = {'method': 'POST', 'uri': '/x', 'auth_required': '不要',
            'auth_method': 'none', 'data_op': '更新',
            # 未測定('-')だと「到達可否が未測定」で P2 になるので測定済みにする
            'data_store': '対象 / PostgreSQL:t',
            'dynamic_verified': '[実測] anon=400(到達)',
            'impl_file': 'pkg/views.py', 'impl_line': '9', 'endpoint': '',
            'test_gap': '-'}
    base.update(kw)
    return [base[n] for n in COLS]


def test_unauthenticated_db_update_is_p1():
    assert prioritize.classify(row(), H)[0] == 'P1'


@pytest.mark.parametrize('kw', [
    {'data_op': '取得'},                                  # POST で受ける取得
    {'data_op': '更新(セッション言語のみ・永続DB無し)', 'data_store': '-'},
    {'data_store': '統計 / ES:stats'},                    # ES だけ
])
def test_not_persistent_change_is_not_p1(kw):
    assert prioritize.classify(row(**kw), H)[0] != 'P1'


def test_view_with_password_check_is_not_p1():
    pri, why = prioritize.classify(row(impl_line='2'), H)
    assert pri == 'P5'
    assert 'app-credential(password: verify_password)' in why


def test_reach_without_proof_does_not_count_for_credential_view():
    # ログイン等は未認証のリクエストがビューまで届くのが正常
    dyn = '[実測] 未認証で到達 | anon=400(到達)'
    assert prioritize.classify(row(impl_line='2', dynamic_verified=dyn), H)[0] == 'P5'


def test_proven_bypass_still_counts_for_credential_view():
    dyn = '[実測] ★未認証で到達 | anon=200(到達)'
    assert prioritize.classify(row(impl_line='2', dynamic_verified=dyn), H)[0] == 'P1'


def test_framework_login_endpoint():
    r = row(impl_file='(framework/自動生成)', impl_line='0', endpoint='security.login')
    assert prioritize.classify(r, H)[0] == 'P5'
