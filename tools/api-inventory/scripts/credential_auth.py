# -*- coding: utf-8 -*-
"""ビューの中で行う本人認証(パスワード・トークンの検証)を判定する。

ログインやメール確認、ワンタイムダウンロードのように、ログインセッションの
代わりにリクエストで渡された認証情報を確かめるビューは、デコレータを持たない
ため台帳では auth_required が「不要」になる。実装を読んで次を探す。

  パスワード   verify_password / check_password / verify_and_update_password
  トークン     関数名が「検証の動詞 + token」のもの(validate_*_token、
               convert_token_into_obj、confirm_email_token_status 等)

対象は実装関数と、そこから呼ぶ **同じパッケージ内の関数を1段** まで。
同名の定義が複数ある関数(get / post 等)はどれが呼ばれるか決まらないのでたどらない。
クラスベースのビューで post → post_v1 のように getattr で振り分けている
場合に備え、同じクラスの `<メソッド名>_*` も含める。

CSRF トークンと CAPTCHA は本人確認ではないので含めない。

ソースの無いフレームワークの行(Flask-Security 等)は endpoint 名で判定する。
"""
import ast
import functools
import os
import re
import warnings

from infra_auth import repo_root

PASSWORD_CALLS = ('verify_password', 'check_password', 'verify_and_update_password')
TOKEN_CALL_RE = re.compile(
    r'(?:verify|validate|check|confirm|convert)\w*token|token\w*_(?:status|valid)',
    re.I)
NOT_IDENTITY_RE = re.compile(r'csrf|captcha', re.I)

# ソースが台帳に無いフレームワークのエンドポイント
FRAMEWORK = {
    'security.login': 'password(Flask-Security login)',
    'security.confirm_email': 'token(Flask-Security confirm_email)',
    'security.reset_password': 'token(Flask-Security reset_password)',
}

HTTP_METHODS = ('get', 'post', 'put', 'patch', 'delete')


def _calls(node):
    names = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                names.add(f.attr)
            elif isinstance(f, ast.Name):
                names.add(f.id)
    return names


@functools.lru_cache(maxsize=None)
def _parse(path):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', SyntaxWarning)
            return ast.parse(open(path, encoding='utf-8', errors='replace').read())
    except (OSError, SyntaxError, ValueError):
        return None


@functools.lru_cache(maxsize=None)
def _package_index(pkg_dir):
    """パッケージ内の関数名 → [呼び出している関数名の集合, ...](定義ごと)。"""
    index = {}
    for base, _, files in os.walk(pkg_dir):
        for f in files:
            if not f.endswith('.py'):
                continue
            tree = _parse(os.path.join(base, f))
            if tree is None:
                continue
            for n in ast.walk(tree):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    index.setdefault(n.name, []).append(_calls(n))
    return index


def _targets(tree, line):
    """impl_line を含む関数と、post → post_v1 のような振り分け先を返す。"""
    best = None
    parent = {}
    for n in ast.walk(tree):
        for ch in ast.iter_child_nodes(n):
            parent[ch] = n
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = min([n.lineno] + [d.lineno for d in n.decorator_list])
            end = getattr(n, 'end_lineno', n.lineno)
            if start <= line <= end and (best is None or end - start < best[1] - best[0]):
                best = (start, end, n)
    if not best:
        return []
    fn = best[2]
    out = [fn]
    cls = parent.get(fn)
    if isinstance(cls, ast.ClassDef) and fn.name in HTTP_METHODS:
        out += [m for m in cls.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                and m.name.startswith(fn.name + '_')]
    return out


def _kinds(names):
    pw = sorted(n for n in names if n in PASSWORD_CALLS)
    tk = sorted(n for n in names
                if TOKEN_CALL_RE.search(n) and not NOT_IDENTITY_RE.search(n))
    out = []
    if pw:
        out.append(f'password: {", ".join(pw)}')
    if tk:
        out.append(f'token: {", ".join(tk)}')
    return out


def credential_auth(impl_file, impl_line, endpoint=''):
    """実装がパスワード/トークンで本人を確かめていれば説明を返す。無ければ ''。"""
    if endpoint in FRAMEWORK:
        return f'app-credential({FRAMEWORK[endpoint]})'
    try:
        line = int(impl_line)
    except (TypeError, ValueError):
        return ''
    if not impl_file or impl_file.startswith('('):
        return ''
    path = os.path.join(repo_root(), impl_file)
    tree = _parse(path)
    if tree is None:
        return ''
    direct = set()
    for fn in _targets(tree, line):
        direct |= _calls(fn)
    index = _package_index(os.path.dirname(path))
    reached = set(direct)
    for name in direct:
        # 同名の定義が複数ある(get / post 等)ものはどれが呼ばれるか決まらないので
        # たどらない。無関係な関数の検証処理を拾ってしまうため。
        defs = index.get(name, [])
        if len(defs) == 1:
            reached |= defs[0]
    kinds = _kinds(reached)
    return f'app-credential({"; ".join(kinds)})' if kinds else ''
