# -*- coding: utf-8 -*-
"""probe_ci.py の実測結果を台帳の dynamic_verified に反映する。

    python3 apply_probe_results.py probe.json
    python3 apply_probe_results.py probe.json --overwrite   # 既存の実測値も差し替える

既定では **`dynamic_verified` が空/`-` の行だけ**を埋める。台帳の既存値には
★実証など人手で精査した記述が含まれており、機械生成の要約で上書きすると
情報が落ちるため(add_cols.py 等と同じ方針)。

書式は既存の台帳に合わせる:
    [実測·2026-08-25] 未認証で到達 | anon=200(到達); general=200(到達); ...
対象を変えて複数回測った行(公開/非公開、activity の自分/他人)は、
それぞれを ` || ` で連結する。
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402

IDENT = ['anon', 'general', 'contributor', 'comadmin', 'repoadmin', 'sysadmin']


def summarize(obs):
    """identity 別の判定から、台帳の見出し語を決める。"""
    def v(k):
        return (obs.get(k) or {}).get('verdict')
    if v('anon') == '到達':
        return '未認証で到達'
    if v('general') == '到達' or v('contributor') == '到達':
        return 'ログインのみで到達'
    if v('comadmin') == '到達' or v('repoadmin') == '到達':
        return '管理者で到達'
    if v('sysadmin') == '到達':
        return 'sysadminのみ到達'
    if any(v(k) == '到達' for k in IDENT):
        return '一部で到達'
    if all(v(k) in ('遮断', None) for k in IDENT):
        return '測定範囲では遮断'
    return '判定不能'


def render(results, date):
    """no ごとに dynamic_verified 用の文字列を作る。"""
    by = {}
    for r in results:
        if r.get('status') != 'measured':
            continue
        by.setdefault(r['no'], []).append(r)
    out = {}
    for no, rs in by.items():
        parts = []
        for r in rs:
            obs = r['observed']
            detail = '; '.join(f"{k}={obs[k]['code']}({obs[k]['verdict']})"
                               for k in IDENT if k in obs)
            tgt = r.get('target', '-')
            label = summarize(obs)
            head = f"{label}" if tgt in ('-', None) else f"{label}[{tgt}]"
            parts.append(f"{head} | {detail}")
        out[no] = f"[実測·{date}] " + ' || '.join(parts)
    return out


def main():
    p = argparse.ArgumentParser(description='実測結果を台帳に反映する')
    p.add_argument('probe_json')
    p.add_argument('--full', default=None)
    p.add_argument('--date', default=None, help='既定: probe.json の更新日')
    p.add_argument('--overwrite', action='store_true',
                   help='既存の dynamic_verified も差し替える(既定は空欄のみ)')
    p.add_argument('--keep-history', action='store_true',
                   help='--overwrite 時、旧値を " ‖ 旧: ..." として末尾に残す')
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    full = a.full or data_path('weko3_api_list_full.tsv')
    date = a.date or datetime.date.fromtimestamp(
        os.path.getmtime(a.probe_json)).isoformat()

    d = json.load(open(a.probe_json, encoding='utf-8'))
    rendered = render(d.get('results', []), date)

    lines = open(full, encoding='utf-8').read().rstrip('\n').split('\n')
    hdr = lines[0].split('\t')
    H = {n: i for i, n in enumerate(hdr)}
    i_no, i_dyn = H['no'], H['dynamic_verified']
    out = [lines[0]]
    filled = kept = 0
    for raw in lines[1:]:
        c = raw.split('\t')
        v = rendered.get(c[i_no])
        if v:
            if c[i_dyn] in ('', '-') or a.overwrite:
                prev = c[i_dyn]
                new = v.replace('\t', ' ')
                if a.keep_history and prev not in ('', '-'):
                    # 旧値には ★実証など人手の所見が含まれる。測り直しで判定が
                    # 変わっても、以前どう見えていたかを追えるように残す。
                    prev = prev.split(' \u2016 \u65e7: ')[0]
                    new = f'{new} \u2016 \u65e7: {prev}'
                c[i_dyn] = new
                filled += 1
            else:
                kept += 1
        out.append('\t'.join(c))
    if not a.dry_run:
        open(full, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(f'{"(dry-run) " if a.dry_run else ""}{full}')
    print(f'  実測がある行: {len(rendered)}')
    print(f'  dynamic_verified を埋めた: {filled}')
    print(f'  既存値を残した(--overwrite で差し替え可): {kept}')


if __name__ == '__main__':
    main()
