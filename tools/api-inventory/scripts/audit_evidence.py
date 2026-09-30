# -*- coding: utf-8 -*-
"""台帳に書いたことが、ソースと合っているかを突き合わせる。

    python3 audit_evidence.py                 # 2つの検知のサマリ
    python3 audit_evidence.py --refs          # A: 位置参照のずれ(明細)
    python3 audit_evidence.py --dataop        # B: data_op と実装の矛盾(明細)
    python3 audit_evidence.py --json out.json # 明細を JSON で
    python3 audit_evidence.py --gate          # 検知があれば exit 1
    python3 audit_evidence.py --summary-only  # 件数だけ(public CI 用)

## なぜ要るか

台帳の検査は**形と語彙しか見ていない**。列数・ヘッダ・採番・語彙表に入っているか、
派生列が再現するか。**中身が本当かは一本も見ていない。**

実験で確かめた穴が2つある。どちらも検査を全部通る。

| 書き換え | 通るか |
|---|---|
| `sec_evidence` の行番号を実在しない値にする | **通る** |
| `data_op` の削除方式を誤った値に戻す | **通る** |
| `sec_exposed` を嘘の文面にする | **通る**(こちらは open_findings 側で受ける) |

`impl_line` には `refresh_impl.py` とテストがあるのに、**`sec_evidence` は同じ
`ファイル:行番号` の形をしているのに検査が無い**。バージョンが変われば必ず腐る。

## A. 位置参照のずれ

`sec_evidence` と `sec_detail` に書かれた `modules/.../foo.py:123` や
`:123-145` を拾い、そのファイルが実在し、行番号がファイルの行数に収まるかを見る。

**ファイル名だけの参照(`rest.py:309-313`)は解決できないので、別枠で数える。**
どのモジュールの rest.py か分からず、機械では追えない。書くときは
`modules/` から始まるパスにすること。

## B. data_op と実装の矛盾

`data_op` に削除があるのに、実装から削除らしき呼び出しに届かない行を出す。
ある設定画面が `更新,削除` と書かれていたが、呼んでいるのは設定の get と
update だけで、削除は一度も起きていなかった、という実例がある。

逆向き(実装は消しているのに data_op に無い)は見ない。**副作用として消える**
実装が多く、主たる操作を何と呼ぶかは人の判断だから。

## 限界

**「何が漏れるか」「その所見が正しいか」は原理的に見られない。** ここが見るのは
「書いてある位置が実在するか」と「書いてある操作が実装にあるか」だけ。
所見そのものの妥当性はレビューでしか担保できない。
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_masking import Index, called_names  # noqa: E402
from paths import data_path  # noqa: E402
from snapshot import default_weko_root  # noqa: E402

# 台帳が書く位置参照。`modules/` から始まる実パスだけを解決対象にする。
REF = re.compile(r'(modules/[\w./-]+\.py):(\d+)(?:-(\d+))?')
# ファイル名だけの参照。解決できないので別枠。
BARE = re.compile(r'(?<![\w/])([\w-]+\.py):(\d+)(?:-(\d+))?')

# 位置参照を書く列。
REF_COLUMNS = ('sec_evidence', 'sec_detail')

# 削除らしき呼び出し。**名前で見るので、別名に切り出したらここを足す。**
DELETE_CALLS = re.compile(
    r'^(delete|delete_model|delete_by_id|delete_record|delete_records|remove|'
    r'soft_delete|delete_schema|delete_session|delete_by_repo|remove_member)$')
# 実装の本文に現れる、削除を示す書き方。呼び出し名では拾えないもの。
DELETE_SOURCE = re.compile(
    r'session\.delete|\.delete\(\)|query\.delete|is_deleted|os\.remove|'
    r'requests\.delete|shutil\.rmtree|\.remove\(')

# 実ファイルを持たない実装の総称表記。突き合わせの対象外。
NON_SOURCE = re.compile(r'^\((provider|site-packages|framework)|^Flask-Admin ModelView')

# 確認済みで検知から外す行。`reconcile_allow.json` / `detect_allow.json` と同じ
# 規約で、**理由の文字列が必須**。理由を読めない許可は運用で形骸化する。
ALLOW = 'evidence_allow.json'


def load_allow(path=None):
    """{"refs": {no: 理由}, "dataop": {no: 理由}} を読む。無ければ空。"""
    p = path or data_path(ALLOW, required=False)
    if not p or not os.path.isfile(p):
        return {'refs': {}, 'dataop': {}}
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception:
        return {'refs': {}, 'dataop': {}}
    return {k: {str(n): r for n, r in (d.get(k) or {}).items() if str(r).strip()}
            for k in ('refs', 'dataop')}


def load(path):
    lines = open(path, encoding='utf-8').read().rstrip('\n').split('\n')
    hdr = lines[0].split('\t')
    return [dict(zip(hdr, l.split('\t'))) for l in lines[1:]], hdr


def line_count(path):
    with open(path, 'rb') as f:
        return sum(1 for _ in f)


def audit_refs(rows, root):
    """A. 位置参照が実在するか。戻り値は (ずれ, 解決できない参照の件数)。"""
    bad, unresolved, cache = [], 0, {}
    for r in rows:
        for col in REF_COLUMNS:
            text = r.get(col) or ''
            for rel, a, b in REF.findall(text):
                p = os.path.join(root, rel)
                if p not in cache:
                    cache[p] = line_count(p) if os.path.isfile(p) else None
                n = cache[p]
                if n is None:
                    bad.append({'no': r['no'], 'column': col, 'ref': f'{rel}:{a}',
                                'why': 'ファイルが無い'})
                    continue
                last = int(b or a)
                if int(a) < 1 or last > n:
                    bad.append({'no': r['no'], 'column': col,
                                'ref': f'{rel}:{a}' + (f'-{b}' if b else ''),
                                'why': f'行番号がファイルの範囲外(全 {n} 行)'})
            # `modules/` を伴わない参照は解決できない
            for m in BARE.finditer(REF.sub('', text)):
                unresolved += 1
    return bad, unresolved


def audit_dataop(rows, root, idx, depth):
    """B. data_op に削除があるのに、実装に削除が見当たらない行。"""
    out = []
    for r in rows:
        if '削除' not in (r.get('data_op') or ''):
            continue
        rel = (r.get('impl_file') or '').strip()
        fn = (r.get('impl_func') or '').strip().split('/')[0]
        if not rel or rel == '-' or NON_SOURCE.match(rel) or not fn or fn == '-':
            continue
        if not os.path.isfile(os.path.join(root, rel)):
            continue
        seed = idx.find(rel, fn)
        if not seed:
            continue
        reached, _gated = idx.reach([seed], depth)
        found = False
        for r_, qual, node in reached:
            if DELETE_CALLS.match(qual.split('.')[-1]):
                found = True
                break
            if any(DELETE_CALLS.match(c) for c in called_names(node)):
                found = True
                break
            src = os.path.join(root, r_)
            try:
                import ast
                if DELETE_SOURCE.search(ast.unparse(node)):
                    found = True
                    break
            except Exception:
                pass
        if not found:
            out.append({'no': r['no'], 'uri': r['uri'], 'data_op': r['data_op'],
                        'impl': f'{rel}:{fn}'})
    return out


def main():
    p = argparse.ArgumentParser(
        description='台帳の記述とソースを突き合わせる')
    p.add_argument('--full', default=None)
    p.add_argument('--weko-root', default=None)
    p.add_argument('--depth', type=int, default=3)
    p.add_argument('--allow', default=None, help=f'既定: $WEKO_API_INVENTORY_DIR/{ALLOW}')
    p.add_argument('--refs', action='store_true')
    p.add_argument('--dataop', action='store_true')
    p.add_argument('--json', dest='json_out', default=None)
    p.add_argument('--gate', action='store_true')
    p.add_argument('--summary-only', action='store_true')
    a = p.parse_args()

    root = a.weko_root or default_weko_root()
    rows, _hdr = load(a.full or data_path('weko3_api_list_full.tsv'))

    allow = load_allow(a.allow)
    refs, unresolved = audit_refs(rows, root)
    idx = Index(root)
    dataop = audit_dataop(rows, root, idx, a.depth)

    n_refs_all = len(refs); n_dataop_all = len(dataop)
    refs = [d for d in refs if d['no'] not in allow['refs']]
    dataop = [d for d in dataop if d['no'] not in allow['dataop']]
    skipped = (n_refs_all - len(refs)) + (n_dataop_all - len(dataop))

    print(f'位置参照のずれ: {len(refs)} 件 / '
          f'解決できない参照(ファイル名だけ): {unresolved} 件')
    print(f'data_op に削除があるのに実装に見当たらない行: {len(dataop)} 件')
    if skipped:
        print(f'  (理由つきで許可済み: {skipped} 件)')

    if not a.summary_only:
        if refs and (a.refs or not a.dataop):
            print('\n== A. 位置参照のずれ ==')
            for d in refs[:40]:
                print(f'  no={d["no"]:<6} {d["column"]:<13} {d["ref"]}  {d["why"]}')
            if len(refs) > 40:
                print(f'  ... 他 {len(refs) - 40} 件')
        if dataop and (a.dataop or not a.refs):
            print('\n== B. data_op と実装の矛盾 ==')
            for d in dataop[:40]:
                print(f'  no={d["no"]:<6} {d["uri"][:52]:<52} data_op={d["data_op"][:20]}')
                print(f'         {d["impl"]}')
            if len(dataop) > 40:
                print(f'  ... 他 {len(dataop) - 40} 件')

    if a.json_out:
        json.dump({'refs': refs, 'unresolved_refs': unresolved, 'dataop': dataop},
                  open(a.json_out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'明細を書き出した: {a.json_out}')

    if a.gate and (refs or dataop):
        sys.exit(1)


if __name__ == '__main__':
    main()
