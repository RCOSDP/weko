# -*- coding: utf-8 -*-
"""git 差分から「再レビューが必要なインベントリ行」を機械的に絞り込む。

    python3 changed_rows.py v2.0.3 HEAD --tsv ../weko3_api_list_full.tsv

`git diff -U0 <base>..<head>` の変更行を、その行を含む def/class の範囲に広げ、
インベントリの impl_file(14列) / impl_line(15列) と突き合わせる。
918行すべてを再測定せず、変更が実際に触れた行だけを Phase2-3 に回すためのもの。

`enrich_git.py` の `enclosing()` と同じ考え方(関数単位)。
"""
import argparse
import ast
import collections
import functools
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
import warnings

warnings.filterwarnings('ignore', category=SyntaxWarning)

HUNK = re.compile(r'^@@ -\S+ \+(\d+)(?:,(\d+))? @@')


def default_weko_root():
    """解析対象リポジトリのルートを決める。

    1. 環境変数 WEKO_ROOT
    2. このスクリプトを含む git リポジトリのトップ(`modules/` があれば採用)
       → WEKO3 リポジトリ内(例: tools/api-inventory/scripts/)に配置した場合に効く
    3. 従来の既定(weko-document から wekov2 を解析する場合)
    """
    env = os.environ.get('WEKO_ROOT')
    if env:
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        top = subprocess.run(['git', '-C', here, 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True).stdout.strip()
    except Exception:
        top = ''
    if top and os.path.isdir(os.path.join(top, 'modules')):
        return top
    return '/home/mhaya/wekov2'


def sh(args):
    return subprocess.run(args, capture_output=True, text=True).stdout


@functools.lru_cache(maxsize=None)
def def_ranges(root, rel):
    fp = os.path.join(root, rel)
    if not os.path.isfile(fp):
        return ()
    try:
        tree = ast.parse(open(fp, encoding='utf-8', errors='replace').read())
    except Exception:
        return ()
    out = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = min([n.lineno] + [d.lineno for d in n.decorator_list])
            out.append((start, getattr(n, 'end_lineno', n.lineno)))
    return tuple(out)


@functools.lru_cache(maxsize=None)
def named_defs(root, rel):
    """(start, end, 表示名) の一覧。ClassDef 配下のメソッドは Class.method で返す。"""
    fp = os.path.join(root, rel)
    if not os.path.isfile(fp):
        return ()
    try:
        tree = ast.parse(open(fp, encoding='utf-8', errors='replace').read())
    except Exception:
        return ()
    out = []

    def walk(node, prefix=''):
        for n in ast.iter_child_nodes(node):
            if isinstance(n, ast.ClassDef):
                walk(n, n.name + '.')
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = min([n.lineno] + [d.lineno for d in n.decorator_list])
                out.append((start, getattr(n, 'end_lineno', n.lineno), prefix + n.name))
    walk(tree)
    return tuple(out)


def changed_func_names(root, rel, ranges):
    """変更行を含む関数の表示名(重複なし)。"""
    names = []
    for s_, e_, name in named_defs(root, rel):
        if any(not (e_ < rs or re_ < s_) for rs, re_ in ranges):
            names.append(name)
    return names


def enclosing(root, rel, line):
    """line を含む最小の def/class 範囲。無ければ (line, line)。"""
    best = None
    for s, e in def_ranges(root, rel):
        if s <= line <= e and (best is None or (e - s) < (best[1] - best[0])):
            best = (s, e)
    return best or (line, line)


def changed_line_ranges(root, base, head):
    """{rel_path: [(start, end), ...]} — 変更後(+側)の行範囲。"""
    diff = sh(['git', '-C', root, 'diff', '-U0', f'{base}..{head}', '--', 'modules/'])
    out = collections.defaultdict(list)
    rel = None
    for line in diff.splitlines():
        if line.startswith('+++ b/'):
            rel = line[6:].strip()
        elif line.startswith('+++ /dev/null'):
            rel = None
        elif line.startswith('@@') and rel:
            m = HUNK.match(line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2) or 1)
                if count:
                    out[rel].append((start, start + count - 1))
    return out


def main():
    p = argparse.ArgumentParser(
        description='git 差分 → 再レビューが必要なインベントリ行')
    p.add_argument('base', help='比較元(前回チェック時のタグ/コミット)')
    p.add_argument('head', nargs='?', default='HEAD')
    p.add_argument('--weko-root', default=default_weko_root())
    p.add_argument('--tsv', default=None,
                   help='既定: $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv')
    p.add_argument('--out', help='該当 no の一覧(1行1件)の出力先')
    a = p.parse_args()
    a.tsv = a.tsv or data_path('weko3_api_list_full.tsv')

    root = os.path.abspath(a.weko_root)
    ranges = changed_line_ranges(root, a.base, a.head)
    if not ranges:
        print(f'{a.base}..{a.head}: modules/ 配下に変更なし')
        return

    # 変更行 → その行を含む def/class 範囲へ拡張
    touched = collections.defaultdict(set)
    for rel, rs in ranges.items():
        if not rel.endswith('.py'):
            continue
        for s, e in rs:
            for line in range(s, e + 1):
                touched[rel].add(enclosing(root, rel, line))

    # インベントリ突き合わせ
    hits, files_changed = [], set()
    with open(a.tsv, encoding='utf-8') as f:
        header = f.readline().rstrip('\n').split('\t')
        i_no, i_uri = header.index('no'), header.index('uri')
        i_file, i_line = header.index('impl_file'), header.index('impl_line')
        i_method = header.index('method')
        for raw in f:
            c = raw.rstrip('\n').split('\t')
            if len(c) <= i_line:
                continue
            rel, ln = c[i_file].strip(), c[i_line].strip()
            if rel not in touched:
                continue
            files_changed.add(rel)
            try:
                ln = int(ln)
            except ValueError:
                continue
            if any(s <= ln <= e for s, e in touched[rel]):
                hits.append((c[i_no], c[i_method], c[i_uri], f'{rel}:{ln}'))

    print(f'{a.base}..{a.head}')
    print(f'  変更ファイル(modules/*.py): {len([r for r in ranges if r.endswith(".py")])}')
    print(f'  うちインベントリに載る実装ファイル: {len(files_changed)}')
    print(f'  再レビュー対象行: {len(hits)} / 全{sum(1 for _ in open(a.tsv, encoding="utf-8")) - 1}行')
    print()
    for no, method, uri, impl in hits:
        print(f'  no={no:<5} {method:<10} {uri[:70]:<70} {impl}')

    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write('\n'.join(h[0] for h in hits) + '\n')
        print(f'\n{a.out} に no 一覧を出力しました'
              f'(probe.py の --only に渡せます)')

    # 台帳に載るファイル内で変わったが、どの台帳行の impl_func でもない関数
    # = エンドポイントから呼ばれるヘルパ。呼び出し元の行は自動では拾えない。
    # (v2.1.0 では _get_status_document/_get_file_info の変更がこれに当たり、
    #  no.573 GET /sword/deposit/<recid> の応答内容が変わっていた)
    ledger_funcs = collections.defaultdict(set)
    with open(a.tsv, encoding='utf-8') as f:
        h2 = f.readline().rstrip('\n').split('\t')
        j_file, j_func = h2.index('impl_file'), h2.index('impl_func')
        for raw in f:
            c = raw.rstrip('\n').split('\t')
            if len(c) > max(j_file, j_func):
                # impl_func は `Class.method`/`a/b`/`名前(注釈)` の表記ゆれがある
                for part in c[j_func].split('(')[0].strip().split('/'):
                    part = part.strip()
                    if part:
                        ledger_funcs[c[j_file].strip()].add(part.split('.')[-1])
    helpers = []
    for rel in sorted(files_changed):
        for name in changed_func_names(root, rel, ranges.get(rel, [])):
            if name.split('.')[-1] not in ledger_funcs.get(rel, ()):
                helpers.append((rel, name))
    if helpers:
        print()
        print('  ⚠ 台帳のエンドポイントではないが変更されたヘルパ関数'
              f'({len(helpers)}件):')
        for rel, name in helpers[:40]:
            print(f'      {rel}  {name}')
        if len(helpers) > 40:
            print(f'      ... 他 {len(helpers) - 40} 件')
        print('    → 呼び出し元のエンドポイントは自動では拾えない。'
              'grep で呼び出し元を辿り、該当する台帳行も再レビューすること。')

    # 変更はあるがインベントリに載っていない実装ファイル = 新規APIの可能性
    unmapped = sorted(set(r for r in ranges if r.endswith('.py')) - files_changed)
    view_like = [r for r in unmapped
                 if os.path.basename(r) in ('views.py', 'rest.py', 'admin.py', 'ext.py', 'config.py')]
    if view_like:
        print()
        print('  ⚠ インベントリに未登録だが views/rest/admin/ext/config が変更されたファイル:')
        for r in view_like:
            print(f'      {r}')
        print('    → 新規エンドポイントの可能性。snapshot.py の差分と併せて確認すること。')


if __name__ == '__main__':
    main()
