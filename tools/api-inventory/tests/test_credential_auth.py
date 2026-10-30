# -*- coding: utf-8 -*-
"""credential_auth のテスト。

    python3 -m pytest tools/api-inventory/tests
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'scripts'))
import credential_auth  # noqa: E402

VIEWS = '''
from .api import ShibUser


@blueprint.route('/confim/user', methods=['POST'])
def confirm_user():
    if request.form.get('csrf_random', '') != session['csrf_random']:
        abort(400)
    shib_user = ShibUser()
    if not shib_user.check_weko_user(account, password):
        abort(400)
    return redirect('/')


@blueprint.route('/download', methods=['POST'])
def download_onetime():
    url_obj = convert_token_into_obj(token)
    return send()


@blueprint.route('/lang', methods=['POST'])
def set_lang():
    session['lang'] = request.form['lang']
    return redirect('/')


@blueprint.route('/csrf', methods=['POST'])
def only_csrf():
    validate_csrf_token(request.form['csrf_token'])
    check_captcha_token(request.form['captcha'])
    return 'ok'


@blueprint.route('/issue', methods=['POST'])
def issue():
    return generate_onetime_token()


@blueprint.route('/ambiguous', methods=['POST'])
def ambiguous():
    return get()


class WekoLogin(ContentNegotiatedMethodView):
    def post(self, **kwargs):
        func_name = f"post_{kwargs.get('version')}"
        return getattr(self, func_name)(**kwargs)

    def post_v1(self, **kwargs):
        if not verify_password(password, user.password):
            raise InvalidPasswordError()
        login_user(user)
'''

API = '''
class ShibUser(object):
    def check_weko_user(self, account, pwd):
        return verify_password(pwd, self.user.password)


def get():
    return verify_password('a', 'b')


class Other(object):
    def get(self):
        return None
'''


@pytest.fixture(autouse=True)
def pkg(tmp_path, monkeypatch):
    d = tmp_path / 'mod' / 'pkg'
    d.mkdir(parents=True)
    (d / 'views.py').write_text(VIEWS, encoding='utf-8')
    (d / 'api.py').write_text(API, encoding='utf-8')
    monkeypatch.setenv('WEKO_ROOT', str(tmp_path))
    credential_auth._parse.cache_clear()
    credential_auth._package_index.cache_clear()
    return d


def line_of(name):
    for i, line in enumerate(VIEWS.splitlines(), 1):
        if line.strip().startswith(f'def {name}('):
            return i
    raise AssertionError(name)


def check(name):
    return credential_auth.credential_auth('mod/pkg/views.py', line_of(name))


def test_password_in_callee_of_same_package():
    # confirm_user → ShibUser.check_weko_user → verify_password
    assert check('confirm_user') == 'app-credential(password: verify_password)'


def test_token_verification():
    assert check('download_onetime') == 'app-credential(token: convert_token_into_obj)'


def test_class_view_dispatches_to_versioned_method():
    # post は getattr で post_v1 に振り分けるだけ
    assert check('post') == 'app-credential(password: verify_password)'


@pytest.mark.parametrize('name', ['set_lang', 'only_csrf', 'issue'])
def test_not_identity_check(name):
    # セッション更新・CSRF/CAPTCHA・トークンの発行は本人認証ではない
    assert check(name) == ''


def test_ambiguous_callee_is_not_followed():
    # get は api.py に関数とメソッドの2つがあり、どちらが呼ばれるか決まらない
    assert check('ambiguous') == ''


def test_framework_endpoint():
    assert credential_auth.credential_auth(
        '(framework/自動生成)', '0', 'security.login') \
        == 'app-credential(password(Flask-Security login))'
    assert credential_auth.credential_auth(
        '(framework/自動生成)', '0', 'security.send_confirmation') == ''


@pytest.mark.parametrize('impl_file, impl_line', [
    ('(framework/自動生成)', '0'),
    ('mod/pkg/views.py', '-'),
    ('mod/pkg/missing.py', '1'),
    ('', ''),
])
def test_unknown_source(impl_file, impl_line):
    assert credential_auth.credential_auth(impl_file, impl_line) == ''
