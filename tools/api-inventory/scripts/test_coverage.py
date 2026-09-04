# -*- coding: utf-8 -*-
"""Phase 9: 各エンドポイントのテストが4観点をカバーしているかを解析する。

    python3 test_coverage.py

観点:
  正常値    2xx を期待するアサーションがある
  異常値    4xx/5xx を期待するアサーションがある
  境界値    parametrize による値の振り分け、または空文字/長大値/上限下限を狙ったテスト
  例外処理  pytest.raises / assertRaises による例外の検証

台帳の `test_file`(対応テスト) と `impl_func` を突き合わせ、そのエンドポイントに
関係するテスト関数を特定してから観点を判定する。ファイル単位で見ると、同じ
ファイル内の別APIのテストを自分のものとして数えてしまうため。

**これは静的なキーワード判定であり、テストの十分性を保証するものではない。**
「観点が全く見当たらない」ことの検出には使えるが、「観点がある」は
アサーションの存在を示すだけで、内容の妥当性は見ていない。
"""
import argparse
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
from snapshot import default_weko_root  # noqa: E402

RE_OK = re.compile(r'status_code\s*(==|in)\s*\(?\s*(200|201|202|204)')
RE_NG = re.compile(r'status_code\s*(==|in)\s*\(?\s*(400|401|403|404|405|409|410|412|415|422|500)')
RE_EXC = re.compile(r'pytest\.raises|assertRaises|with\s+raises\(')
RE_BOUND_NAME = re.compile(
    r'boundary|limit|max|min|empty|too_?long|overflow|invalid_length|zero|negative|'
    r'境界|上限|下限|空', re.I)
RE_BOUND_BODY = re.compile(
    r'@pytest\.mark\.parametrize|["\']\s*["\']\s*[,)]|\*\s*\d{3,}|'
    r'sys\.maxsize|float\(["\']inf|-1\s*[,)]')


def norm_static(uri):
    """URI から検索に使える静的部分を取り出す(最長のパラメータなし区間)。"""
    parts = [p for p in uri.split('/') if p and '<' not in p]
    return parts[-1] if parts else ''


def collect_tests(path):
    """テストファイルから {関数名: ソース} を返す。"""
    try:
        text = open(path, encoding='utf-8', errors='replace').read()
        tree = ast.parse(text)
    except Exception:
        return {}
    lines = text.splitlines()
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and node.name.startswith('test'):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            end = getattr(node, 'end_lineno', node.lineno)
            out[node.name] = '\n'.join(lines[start - 1:end])
    return out


def analyse(row_tests):
    """関係するテスト群から4観点の有無を判定する。"""
    joined = '\n'.join(row_tests.values())
    names = ' '.join(row_tests)
    return {
        'normal': bool(RE_OK.search(joined)),
        'abnormal': bool(RE_NG.search(joined)),
        'boundary': bool(RE_BOUND_BODY.search(joined)) or bool(RE_BOUND_NAME.search(names)),
        'exception': bool(RE_EXC.search(joined)),
    }


def main():
    p = argparse.ArgumentParser(description='テスト4観点のカバレッジを台帳に付与')
    p.add_argument('--full', default=None)
    p.add_argument('--weko-root', default=None)
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    full = a.full or data_path('weko3_api_list_full.tsv')
    root = a.weko_root or default_weko_root()

    lines = open(full, encoding='utf-8').read().rstrip('\n').split('\n')
    hdr = lines[0].split('\t')
    H = {n: i for i, n in enumerate(hdr)}
    NEW = ['test_normal', 'test_abnormal', 'test_boundary', 'test_exception', 'test_gap']
    keep = [i for i, n in enumerate(hdr) if n not in NEW]
    hdr = [hdr[i] for i in keep]

    cache = {}
    out = ['\t'.join(hdr + NEW)]
    stats = {k: 0 for k in ('normal', 'abnormal', 'boundary', 'exception')}
    nomatch = 0
    for raw in lines[1:]:
        c0 = raw.split('\t')
        c = [(c0 + [''] * len(H))[i] for i in keep]
        Hn = {n: i for i, n in enumerate(hdr)}
        tf = c[Hn['test_file']]
        impl = c[Hn['impl_func']].split('.')[-1]
        static = norm_static(c[Hn['uri']])

        related = {}
        for f in [x.strip() for x in tf.split(';') if x.strip() and x.strip() != '-']:
            fp = os.path.join(root, f)
            if fp not in cache:
                cache[fp] = collect_tests(fp)
            for name, src in cache[fp].items():
                if (impl and impl in src) or (static and static in src) \
                        or (impl and impl in name):
                    related[f'{f}::{name}'] = src
        if not related:
            # 「テストが無い」のではなく「どのテスト関数が対応するか特定できなかった」。
            # 両者を同じ '-' にすると、実際にテストが無い行と区別できなくなる。
            nomatch += 1
            out.append('\t'.join(c + ['?', '?', '?', '?', '特定不能']))
            continue
        res = analyse(related)
        for k, v in res.items():
            stats[k] += 1 if v else 0
        gap = [ja for k, ja in (('normal', '正常値'), ('abnormal', '異常値'),
                                ('boundary', '境界値'), ('exception', '例外処理'))
               if not res[k]]
        out.append('\t'.join(c + ['○' if res['normal'] else '-',
                                  '○' if res['abnormal'] else '-',
                                  '○' if res['boundary'] else '-',
                                  '○' if res['exception'] else '-',
                                  ','.join(gap) if gap else '-']))

    if not a.dry_run:
        open(full, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    n = len(lines) - 1
    judged = n - nomatch
    print(f'{"(dry-run) " if a.dry_run else ""}{full}: {n} 行を解析')
    print(f'  テスト関数を特定できた行: {judged} / 特定不能: {nomatch}')
    for k, ja in (('normal', '正常値'), ('abnormal', '異常値'),
                  ('boundary', '境界値'), ('exception', '例外処理')):
        print(f'  {ja:<6} あり {stats[k]:>4} / なし {judged - stats[k]:>4}  (特定できた {judged} 行中)')


if __name__ == '__main__':
    main()
