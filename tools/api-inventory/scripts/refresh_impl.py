# -*- coding: utf-8 -*-
"""impl_line を現在のソースから引き直す。

バージョンアップ後は関数の位置がずれるため、台帳の impl_line が実際とずれる。
changed_rows.py は「git diff のハンク行番号」と「台帳の impl_line」を突き合わせて
再レビュー対象を決めるので、**ずれたまま流すと対象行を取り違える**
(v2.1.0 では no.52/54/55 を誤って拾い、実際に変わった no.53 を取りこぼした)。

    python3 refresh_impl.py            # 差分を表示するだけ
    python3 refresh_impl.py --write    # 台帳に書き戻す

impl_func は `func` / `Class.method` の形式を想定する。
"""
import argparse
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
from changed_rows import default_weko_root  # noqa: E402


def index_defs(path):
    """ファイル内の関数定義を {name: lineno, Class.method: lineno} で返す。"""
    try:
        tree = ast.parse(open(path, encoding='utf-8').read())
    except Exception:
        return {}
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.setdefault(node.name, node.lineno)
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[f'{node.name}.{sub.name}'] = sub.lineno
    return out


def resolve(defs, fn):
    """impl_func の表記ゆれを吸収して定義行を引く。

    台帳の impl_func には注釈が付く:
        BucketResource.get(listobjects/multipart_listuploads)   括弧で経路の内訳
        WekoLogin.post/post_v1                                  / で複数版
    括弧を落とし、/ で割った候補を順に当てる。
    """
    base = fn.split('(')[0].strip()
    cands = []
    for part in base.split('/'):
        part = part.strip()
        if not part:
            continue
        cands.append(part)
        if '.' in base and '.' not in part:
            cands.append(base.rsplit('.', 1)[0] + '.' + part)   # Class.method 復元
        cands.append(part.rsplit('.', 1)[-1])
    for c in cands:
        if c in defs:
            return defs[c]
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tsv', default=None)
    p.add_argument('--write', action='store_true')
    a = p.parse_args()

    tsv = a.tsv or data_path('weko3_api_list_full.tsv')
    root = default_weko_root()
    rows = [l.rstrip('\n').split('\t') for l in open(tsv, encoding='utf-8')]
    head = {n: i for i, n in enumerate(rows[0])}
    for c in ('impl_file', 'impl_line', 'impl_func'):
        if c not in head:
            sys.exit(f'列が無い: {c}')

    cache, moved, missing, skipped, nofile, ok = {}, [], [], [], [], 0
    for r in rows[1:]:
        f, ln, fn = r[head['impl_file']], r[head['impl_line']], r[head['impl_func']]
        if not f or not fn or f in ('-', 'TODO'):
            continue
        full = os.path.join(root, f)
        if not os.path.isfile(full):
            # impl_file が実ファイルでない行(Flask-Admin ModelView の総称表記など)
            nofile.append((r[0], f, fn))
            continue
        if full not in cache:
            cache[full] = index_defs(full)
        defs = cache[full]
        if '\u2192' in fn:
            # `A→B` は実体が別ファイルにある委譲。impl_file と対応しないので触らない。
            skipped.append((r[0], f, fn))
            continue
        new = resolve(defs, fn)
        if new is None:
            missing.append((r[0], f, fn))
            continue
        if str(new) != ln:
            moved.append((r[0], f, fn, ln, new))
            r[head['impl_line']] = str(new)
        else:
            ok += 1

    print(f'{tsv}: 一致 {ok} / ずれ {len(moved)} / 解決不能 {len(missing)} / 委譲 {len(skipped)} / 実ファイル無し {len(nofile)}')
    for m in moved[:40]:
        print(f'  no={m[0]:<5} {m[1]}:{m[3]} -> {m[4]}  {m[2]}')
    if len(moved) > 40:
        print(f'  ... 他 {len(moved) - 40} 件')
    for m in missing[:20]:
        print(f'  ★解決不能 no={m[0]:<5} {m[1]}  {m[2]}  (関数が消えた/改名の可能性)')
    if len(missing) > 20:
        print(f'  ... 他 {len(missing) - 20} 件')

    if a.write and moved:
        open(tsv, 'w', encoding='utf-8').write(
            '\n'.join('\t'.join(x) for x in rows) + '\n')
        print(f'  → {len(moved)} 行の impl_line を書き戻した')
    elif not a.write:
        print('  (--write を付けると書き戻す)')


if __name__ == '__main__':
    main()
