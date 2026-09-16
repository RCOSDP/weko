# -*- coding: utf-8 -*-
"""ビュー関数が in-process からも呼ばれている経路を検出する (AST)。

## なぜ要るのか

台帳は `extract_routes.py` が拾う **Flask のルート** を単位にしている。
だが WEKO3 には、ビュー関数を HTTP 経由ではなく別モジュールから
``from weko_records_ui.views import soft_delete`` して直接呼ぶ経路がある。
この「第二の入口」は台帳のどの列にも現れないため、ルート単位で認可を
足していく作業では見落とされる。

issue62807 がその実例:
``record_edit_permission_required`` は recid を kwargs / request.form /
JSON body / query string からしか探しておらず、``soft_delete(del_value)`` と
*位置引数* で呼ぶ in-process 経路で id を見つけられず abort(400) していた。
台帳上この行は auth_required=要 / test_gap=- で、穴が無いように見えていた。

## 何を出すか

ルート/expose/add_url_rule で登録されたビュー関数のうち、
**テスト以外の本体コードから名前で import されている** ものを列挙する。
デコレータが付いているものは、呼び出し元のリクエストコンテキストで
そのデコレータが動くことになるため risk=HIGH として区別する。

## 使い方

    WEKO_ROOT=/home/mhaya/wekov2 python3 audit_inprocess_views.py
    WEKO_ROOT=/home/mhaya/wekov2 python3 audit_inprocess_views.py --json out.json
    WEKO_ROOT=/home/mhaya/wekov2 python3 audit_inprocess_views.py --summary-only

``--summary-only`` は件数だけを出す。CI のログ・artifact・PR コメントは
誰でも読めるため、CI から回すときは必ずこちらを使うこと
(``tools/api-inventory/ci/README.md`` と同じ方針)。
"""
import argparse
import ast
import json
import os
import sys

def _find_root():
    """WEKO3 リポジトリのルート(`modules/` を持つ階層)を探す。

    ツールは WEKO3 本体の tools/api-inventory/scripts/ に置かれることも、
    weko-document 側に置かれることもある(README 冒頭の注記)。
    決め打ちの相対パスだと片方で外れるので、`modules/` の有無で決める。
    """
    env = os.environ.get('WEKO_ROOT')
    if env:
        return env
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isdir(os.path.join(d, 'modules')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.getcwd()
        d = parent


ROOT = _find_root()
SKIP = ('/tests', '/examples', '/.tox', '/node_modules', '/docs/', '/build/',
        '/cookiecutter')

# audit_decorators.py と同じ集合。認可デコレータの名寄せ。
AUTH = {
    'login_required', 'login_required_customize', 'roles_required',
    'require_api_auth', 'require_oauth_scopes', 'need_record_permission',
    'need_permissions', 'check_authority', 'stats_api_access_required',
    'check_index_access_permissions', 'check_on_behalf_of', 'require_oauth',
    'pass_record', 'record_edit_permission_required',
    'require_item_edit_permission',
}


def iter_py():
    for dp, _dn, fn in os.walk(os.path.join(ROOT, 'modules')):
        if any(s in dp + '/' for s in SKIP):
            continue
        for f in sorted(fn):
            if f.endswith('.py'):
                yield os.path.join(dp, f)


def dec_name(d):
    c = d.func if isinstance(d, ast.Call) else d
    parts = []
    while isinstance(c, ast.Attribute):
        parts.append(c.attr)
        c = c.value
    if isinstance(c, ast.Name):
        parts.append(c.id)
    return '.'.join(reversed(parts))


def is_auth(name):
    last = name.split('.')[-1]
    return last in AUTH or name.endswith('permission.require')


def mod_of(rel):
    """modules/weko-records-ui/weko_records_ui/views.py -> weko_records_ui.views"""
    parts = rel.split(os.sep)
    if len(parts) < 3 or parts[0] != 'modules':
        return None
    return '.'.join(parts[2:])[:-3] if parts[-1].endswith('.py') else None


def collect_views():
    """{(module, func): {...}} ルート登録されたビュー関数。"""
    views = {}
    url_rule_funcs = set()   # add_url_rule(view_func=...) で登録される名前

    for fp in iter_py():
        rel = os.path.relpath(fp, ROOT)
        mod = mod_of(rel)
        if not mod:
            continue
        try:
            tree = ast.parse(open(fp, encoding='utf-8', errors='replace').read())
        except Exception:
            continue

        for node in ast.walk(tree):
            # add_url_rule(..., view_func=publish) 形式
            if isinstance(node, ast.Call) and \
                    dec_name(node).endswith('add_url_rule'):
                for kw in node.keywords:
                    if kw.arg == 'view_func' and isinstance(kw.value, ast.Name):
                        url_rule_funcs.add((mod, kw.value.id))

            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decs = [dec_name(d) for d in node.decorator_list]
            routed = any(d.endswith('.route') or d == 'expose'
                         or d.endswith('.expose') for d in decs)
            if not routed:
                continue
            views[(mod, node.name)] = {
                'module': mod,
                'func': node.name,
                'file': rel,
                'line': node.lineno,
                'decorators': decs,
                'auth_decorators': [d for d in decs if is_auth(d)],
            }

    # add_url_rule 経由も、関数定義が見つかればビューとして扱う
    for fp in iter_py():
        rel = os.path.relpath(fp, ROOT)
        mod = mod_of(rel)
        if not mod:
            continue
        try:
            tree = ast.parse(open(fp, encoding='utf-8', errors='replace').read())
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                    (mod, node.name) in url_rule_funcs and \
                    (mod, node.name) not in views:
                decs = [dec_name(d) for d in node.decorator_list]
                views[(mod, node.name)] = {
                    'module': mod,
                    'func': node.name,
                    'file': rel,
                    'line': node.lineno,
                    'decorators': decs,
                    'auth_decorators': [d for d in decs if is_auth(d)],
                    'registered_via': 'add_url_rule',
                }
    return views


def collect_imports():
    """[(module, name, importer_file, line)] 本体コードからの from-import。"""
    found = []
    for fp in iter_py():
        rel = os.path.relpath(fp, ROOT)
        try:
            tree = ast.parse(open(fp, encoding='utf-8', errors='replace').read())
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            # 相対 import (level>0) は同一モジュール内なので対象外。
            # 見たいのは「別モジュールがビューを直接呼ぶ」ケース。
            if node.level:
                continue
            for a in node.names:
                found.append((node.module, a.name, rel, node.lineno))
    return found


def positional_calls(rel_file, names):
    """importer の中で、その名前を位置引数付きで呼んでいる行を返す。"""
    hits = {}
    fp = os.path.join(ROOT, rel_file)
    try:
        tree = ast.parse(open(fp, encoding='utf-8', errors='replace').read())
    except Exception:
        return hits
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in names and node.args:
            hits.setdefault(node.func.id, []).append(node.lineno)
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--json', help='結果を JSON で書き出す')
    ap.add_argument('--summary-only', action='store_true',
                    help='件数だけ出す (CI 用。ログが公開されるため)')
    ap.add_argument('--fail-on-high', action='store_true',
                    help='risk=HIGH が1件でもあれば終了コード1')
    args = ap.parse_args()

    views = collect_views()
    imports = collect_imports()

    results = []
    for mod, name, importer, line in imports:
        key = (mod, name)
        if key not in views:
            continue
        v = views[key]
        if importer == v['file']:
            continue                       # 自分自身の再 import
        pos = positional_calls(importer, {name})
        entry = dict(v)
        entry['importer'] = importer
        entry['import_line'] = line
        entry['positional_call_lines'] = pos.get(name, [])
        # デコレータ付きのビューを in-process で呼ぶと、そのデコレータが
        # 呼び出し元のリクエストコンテキストで動く。位置引数だと
        # kwargs しか見ないデコレータが id を取れない (issue62807)。
        if entry['auth_decorators'] and entry['positional_call_lines']:
            entry['risk'] = 'HIGH'
        elif entry['auth_decorators']:
            entry['risk'] = 'MEDIUM'
        else:
            entry['risk'] = 'LOW'
        results.append(entry)

    results.sort(key=lambda e: ({'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[e['risk']],
                                e['module'], e['func']))

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as fh:
            json.dump(results, fh, ensure_ascii=False, indent=2)

    counts = {r: sum(1 for e in results if e['risk'] == r)
              for r in ('HIGH', 'MEDIUM', 'LOW')}
    if args.summary_only:
        print('in-process から呼ばれるビュー: {} 件 '
              '(HIGH={HIGH} MEDIUM={MEDIUM} LOW={LOW})'
              .format(len(results), **counts))
    else:
        for e in results:
            print('[{risk}] {module}.{func}  ({file}:{line})'.format(**e))
            print('    デコレータ: {}'.format(', '.join(e['decorators']) or '-'))
            print('    呼び出し元: {}:{}'.format(e['importer'], e['import_line']))
            if e['positional_call_lines']:
                print('    位置引数での呼び出し: 行 {}'.format(
                    ', '.join(str(n) for n in e['positional_call_lines'])))
        print('\n合計 {} 件 (HIGH={HIGH} MEDIUM={MEDIUM} LOW={LOW})'
              .format(len(results), **counts))

    if args.fail_on_high and counts['HIGH']:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
