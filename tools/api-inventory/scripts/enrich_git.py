# -*- coding: utf-8 -*-
"""台帳の git 由来4列を引き直す。

    last_commit / last_commit_date / last_commit_subject / release_tag

    python3 enrich_git.py                      # 差分を表示するだけ
    python3 enrich_git.py --write              # 台帳に書き戻す
    python3 enrich_git.py --tsv in.tsv --out out.tsv   # 別ファイルへ出す(初回生成向け)

`impl_file`(リポジトリ相対) と `impl_line` が指す def/class の行範囲を AST で特定し、
`git log -1 -L <開始>,<終了>:<file>` でその範囲を最後に変更したコミットを取る
(ファイル単位で見るより正確)。`release_tag` は
`git tag --sort=creatordate --contains <sha>` の先頭 = 最初に入ったリリース。
コミットがどのタグにも入っていなければ `(未リリース)`。

`impl_file` が実ファイルでない行(Flask-Admin ModelView の総称表記 / framework 自動生成 /
site-packages)は git で追えないので4列とも `-` にする。

★ `impl_line` がずれていると手前の関数のコミットを拾う。**必ず `refresh_impl.py --write`
  を先に回すこと。** バージョンアップでデコレータが増えると行番号は簡単にずれる。

解析対象リポジトリは `WEKO_ROOT`、台帳は `WEKO_API_INVENTORY_DIR` で指す。
"""
import argparse
import ast
import functools
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
from changed_rows import default_weko_root  # noqa: E402

COLS = ('last_commit', 'last_commit_date', 'last_commit_subject', 'release_tag')
EMPTY = ('-', '-', '-', '-')


@functools.lru_cache(maxsize=None)
def def_ranges(root, path):
    """ファイル内の全 def/class の (開始, 終了) を返す。開始はデコレータ行を含む。"""
    fp = os.path.join(root, path)
    if not os.path.isfile(fp):
        return ()
    try:
        tree = ast.parse(open(fp, encoding='utf-8', errors='replace').read())
    except Exception:
        return ()
    out = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            s = min([n.lineno] + [d.lineno for d in n.decorator_list])
            out.append((s, getattr(n, 'end_lineno', n.lineno)))
    return tuple(out)


def enclosing(root, path, line):
    """line を含む最小の def/class 範囲。無ければ (line, line)。"""
    best = None
    for s, e in def_ranges(root, path):
        if s <= line <= e and (best is None or (e - s) < (best[1] - best[0])):
            best = (s, e)
    return best or (line, line)


@functools.lru_cache(maxsize=None)
def git_last(root, path, start, end):
    try:
        r = subprocess.run(
            ['git', '-C', root, 'log', '-1', '--format=%h\x1f%ad\x1f%s', '--date=short',
             '-L', f'{start},{end}:{path}'],
            capture_output=True, text=True, timeout=120)
    except Exception:
        return ('', '', '')
    line = r.stdout.split('\n', 1)[0] if r.stdout else ''
    parts = line.split('\x1f')
    if len(parts) != 3:
        return ('', '', '')
    return (parts[0], parts[1], parts[2].replace('\t', ' ').strip()[:120])


@functools.lru_cache(maxsize=None)
def git_tag(root, sha):
    if not sha:
        return ''
    try:
        r = subprocess.run(['git', '-C', root, 'tag', '--sort=creatordate', '--contains', sha],
                           capture_output=True, text=True, timeout=120)
    except Exception:
        return ''
    tags = [t.strip() for t in r.stdout.split('\n') if t.strip()]
    return tags[0] if tags else '(未リリース)'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tsv', default=None, help='入力の台帳(既定: $WEKO_API_INVENTORY_DIR の57列版)')
    p.add_argument('--out', default=None, help='出力先(既定: --tsv と同じ = 上書き)')
    p.add_argument('--write', action='store_true', help='書き戻す(付けないと差分表示のみ)')
    a = p.parse_args()

    tsv = a.tsv or data_path('weko3_api_list_full.tsv')
    dst = a.out or tsv
    root = default_weko_root()

    rows = [l.rstrip('\n').split('\t') for l in open(tsv, encoding='utf-8') if l.rstrip('\n')]
    head = {n: i for i, n in enumerate(rows[0])}
    for c in ('impl_file', 'impl_line') + COLS:
        if c not in head:
            sys.exit(f'列が無い: {c}')
    i_file, i_line = head['impl_file'], head['impl_line']
    idx = [head[c] for c in COLS]

    changed, same, nofile = [], 0, 0
    for r in rows[1:]:
        if len(r) < len(rows[0]):
            r += [''] * (len(rows[0]) - len(r))
        path, ln = r[i_file].strip(), r[i_line].strip()
        try:
            line = int(ln)
        except ValueError:
            line = None
        if path and line and os.path.isfile(os.path.join(root, path)):
            s, e = enclosing(root, path, line)
            sha, date, subj = git_last(root, path, s, e)
            new = (sha or '-', date or '-', subj or '-', git_tag(root, sha) or '-')
        else:
            nofile += 1
            new = EMPTY
        old = tuple(r[i] for i in idx)
        if old != new:
            changed.append((r[0], path, ln, old, new))
            for i, v in zip(idx, new):
                r[i] = v
        else:
            same += 1

    print(f'{tsv} (root={root})')
    print(f'  更新 {len(changed)} / 変化なし {same} / 追えない行 {nofile}')
    for no, path, ln, old, new in changed[:40]:
        print(f'  no={no:<5} {path}:{ln}')
        print(f'         {old[0]} / {old[3]}  ->  {new[0]} ({new[1]}) / {new[3]}')
    if len(changed) > 40:
        print(f'  ... 他 {len(changed) - 40} 件')

    if a.write:
        with open(dst, 'w', encoding='utf-8') as f:
            f.write('\n'.join('\t'.join(x.replace('\t', ' ') for x in r) for r in rows) + '\n')
        print(f'  → {dst} に書き戻した')
    else:
        print('  (--write を付けると書き戻す)')


if __name__ == '__main__':
    main()
