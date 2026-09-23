# -*- coding: utf-8 -*-
"""未解消の指摘を、チケット番号だけで公開側から見えるようにする。

    python3 open_findings.py                  # 優先度別の内訳と番号一覧
    python3 open_findings.py --summary-only   # 件数と番号だけ(public CI 用)
    python3 open_findings.py --gate           # 記入漏れ・未起票の増加で exit 1
    python3 open_findings.py --json out.json  # 明細(番号まで)を JSON で

## なぜ要るか

所見は private 側の台帳にしか書けない(docs/RULE.md §1)。そのぶん、**未修正の
指摘が台帳の中だけで滞留し、台帳を開く人が減った時点で忘れられる**。
`api-inventory-drift` のゲートは「台帳を更新せずに API を変えること」を止めるが、
「台帳に書いたまま直さないこと」は止めない。ここが抜けていた。

このスクリプトは台帳の `fix_ticket` 列を読み、**チケット番号と件数だけ**を出す。
番号には所見が含まれないので public な CI に出せる。経路名・関数名・所見の本文は
一切出さない。「何件あるか」と「番号は何か」は毎 PR で目に入り、「どこが該当するか」
は private 側でしか読めない、という切り分けにする。

## ゲート

| 条件 | 意味 |
|---|---|
| A. 記入漏れ | `schema.FIX_REQUIRED_PRIORITIES` の行で `fix_ticket` が空・語彙外 |
| B. 未起票の増加 | `未起票` の件数がベースライン(`fix_baseline.json`)を超えた |

A は「所見を書いたのにチケットを立て忘れた」を止める。B はラチェットで、
**既存の未起票は減らせても増やせない**。B が無いと、対応を先送りするたびに
未起票が積み上がっても誰も気付かない。ベースラインは private 側に置く
(件数そのものは公開してよいが、更新は台帳と同じ PR で行うため)。

## この列に書いてよいもの

`schema.py` の `fix_ticket` の語彙を参照。**説明を添えないこと。**
「issueNNNNN ○○の認可漏れ」と書いた時点で、それは所見であって
番号ではない。
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schema  # noqa: E402
from paths import data_path  # noqa: E402

BASELINE = 'fix_baseline.json'


def load_ledger(path):
    lines = open(path, encoding='utf-8').read().rstrip('\n').split('\n')
    hdr = lines[0].split('\t')
    return [dict(zip(hdr, l.split('\t'))) for l in lines[1:]], hdr


def load_baseline(path=None):
    """未起票のベースライン。無ければ None(ゲート B をスキップする)。"""
    p = path or data_path(BASELINE, required=False)
    if not p or not os.path.isfile(p):
        return None
    try:
        return json.load(open(p, encoding='utf-8')).get('untriaged') or {}
    except Exception:
        return None


def classify(rows):
    """行を区分ごとに畳む。戻り値は (区分 -> 優先度 -> [行]) と記入漏れ。"""
    by_kind = collections.defaultdict(lambda: collections.defaultdict(list))
    invalid = []
    for r in rows:
        kind = schema.fix_ticket_kind(r.get('fix_ticket'))
        pri = (r.get('priority') or '-').strip()
        if kind is None:
            invalid.append((r.get('no'), pri, '語彙外'))
            continue
        if kind == 'なし' and pri in schema.FIX_REQUIRED_PRIORITIES:
            invalid.append((r.get('no'), pri, '記入漏れ'))
            continue
        by_kind[kind][pri].append(r)
    return by_kind, invalid


def tickets_of(rows):
    """未解消(起票済み)のチケット番号を重複なく並べる。"""
    out = []
    for r in rows:
        for t in schema.fix_tickets_in(r.get('fix_ticket')):
            if t not in out:
                out.append(t)
    return sorted(out)


def report(by_kind, invalid, baseline, summary_only):
    open_rows = {p: rs for p, rs in by_kind['起票済み'].items()}
    untriaged = {p: rs for p, rs in by_kind['未起票'].items()}

    def total(d):
        return sum(len(v) for v in d.values())

    def breakdown(d):
        return ' / '.join(f'{p} {len(rs)}' for p, rs in sorted(d.items())) or 'なし'

    print(f'未解消の指摘: 起票済み {total(open_rows)} 件 ({breakdown(open_rows)}) / '
          f'未起票 {total(untriaged)} 件 ({breakdown(untriaged)})')
    tickets = tickets_of([r for rs in open_rows.values() for r in rs])
    print(f'  起票済みの番号: {", ".join(tickets) if tickets else "(なし)"}')
    print(f'  解消済み: {total(by_kind["解消済み"])} 件')

    if baseline is not None:
        over = {p: len(rs) - baseline.get(p, 0)
                for p, rs in untriaged.items() if len(rs) > baseline.get(p, 0)}
        if over:
            print('  ★未起票がベースラインを超えた: '
                  + ', '.join(f'{p} +{n}' for p, n in sorted(over.items())))
    else:
        print(f'  (ベースライン {BASELINE} が無いため増加は見ていない)')

    if invalid:
        print(f'  ★fix_ticket の記入漏れ/語彙外: {len(invalid)} 件')
        if not summary_only:
            for no, pri, why in invalid[:20]:
                print(f'      no={no:<6} {pri:<4} {why}')
            if len(invalid) > 20:
                print(f'      ... 他 {len(invalid) - 20} 件')
    return untriaged


def main():
    p = argparse.ArgumentParser(
        description='未解消の指摘をチケット番号だけで報告する')
    p.add_argument('--full', default=None,
                   help='既定: $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv')
    p.add_argument('--baseline', default=None)
    p.add_argument('--summary-only', action='store_true',
                   help='件数と番号だけ(public な CI 用)')
    p.add_argument('--gate', action='store_true',
                   help='記入漏れ、または未起票の増加があれば終了コード1')
    p.add_argument('--json', dest='json_out', default=None)
    a = p.parse_args()

    tsv = a.full or data_path('weko3_api_list_full.tsv')
    rows, hdr = load_ledger(tsv)
    if 'fix_ticket' not in hdr:
        sys.exit('台帳に fix_ticket 列がありません。'
                 'schema.py と列定義 README を直してから追加してください。')

    baseline = load_baseline(a.baseline)
    by_kind, invalid = classify(rows)
    untriaged = report(by_kind, invalid, baseline, a.summary_only)

    if a.json_out:
        with open(a.json_out, 'w', encoding='utf-8') as f:
            json.dump({
                'open_tickets': tickets_of(
                    [r for rs in by_kind['起票済み'].values() for r in rs]),
                'counts': {k: {p: len(rs) for p, rs in v.items()}
                           for k, v in by_kind.items()},
                'invalid': [{'no': n, 'priority': p, 'why': w}
                            for n, p, w in invalid],
            }, f, ensure_ascii=False, indent=2)
        print(f'明細を書き出した: {a.json_out}')

    if a.gate:
        over = baseline is not None and any(
            len(rs) > baseline.get(p, 0) for p, rs in untriaged.items())
        if invalid or over:
            sys.exit(1)


if __name__ == '__main__':
    main()
