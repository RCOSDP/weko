# -*- coding: utf-8 -*-
"""スナップショット(実機url_map) ↔ インベントリTSV の突き合わせ。

    python3 reconcile.py --gate

検出するもの:
  A. インベントリ未収載の経路   … 実機にあるが台帳に無い(=抽出漏れ)
  B. 実機に無いインベントリ行   … 台帳にあるが実機url_mapに無い(未登録/条件付き)
  C. メソッド不一致             … 同一URIでHTTPメソッドが食い違う
  D. app列の不一致              … UI/API どちらに登録されているかの記載誤り
  E. endpoint 未収載            … 同じ URI に複数の Blueprint/設定が登録されている
                                   ケースの取りこぼし(URI 単位の A では拾えない)

B は「プラグイン未登録」「config で無効」等の正当な理由があるものを
`reconcile_allow.json` に登録して既知として扱う(理由を必ず書く)。

URI の正規化規則:
  - スナップショット: APIアプリのルールには `/api` を前置する
    (APIアプリは DispatcherMiddleware で /api にマウントされるため url_map 側には出ない)
  - インベントリ: uri セルの `;` 区切りを展開。`app=両方` の行は `/api` 側も展開
  - 末尾スラッシュは除去して比較
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)


def norm(u):
    u = u.strip()
    return u[:-1] if len(u) > 1 and u.endswith('/') else u


def load_snapshot(path):
    """uri -> {'methods': set, 'keys': [snapshot key], 'apps': set}"""
    snap = json.load(open(path, encoding='utf-8'))
    out = {}
    for key, v in snap['endpoints'].items():
        prefix = '/api' if v['app'] == 'api' else ''
        for rt in v['routes']:
            u = norm(prefix + rt['rule'])
            e = out.setdefault(u, {'methods': set(), 'keys': [], 'apps': set(),
                                   'provider': v.get('provider'), 'attrs': v.get('attrs')})
            # HEAD/OPTIONS は werkzeug が GET に自動付与するため比較対象外(ダンプ側で除外済み)
            e['methods'].update(rt['methods'])
            e['keys'].append(key)
            e['apps'].add(v['app'])
    return snap, out


def load_inventory(path):
    """uri -> {'methods': set, 'nos': [no], 'app_col': set}"""
    out = {}
    rows = {}
    with open(path, encoding='utf-8') as f:
        hdr = f.readline().rstrip('\n').split('\t')
        i_no, i_app = hdr.index('no'), hdr.index('app')
        i_m, i_u = hdr.index('method'), hdr.index('uri')
        for line in f:
            c = line.rstrip('\n').split('\t')
            if len(c) <= i_u:
                continue
            rows[c[i_no]] = c
            # HEAD/OPTIONS は比較対象外(werkzeug が GET に自動付与するため)
            methods = {m for m in c[i_m].replace(' ', '').split(',') if m
                       and m not in ('HEAD', 'OPTIONS')}
            uris = [norm(u) for u in c[i_u].split(';') if norm(u)]
            expanded = list(uris)
            if c[i_app] == '両方':
                # 旧表現(1行にUI/APIを集約)。v2.1.0 以降は別行に分けるが、
                # 過去の台帳もそのまま突き合わせられるように残す。
                expanded += [norm('/api' + u) for u in uris]
            for u in expanded:
                e = out.setdefault(u, {'methods': set(), 'nos': [], 'app_col': set()})
                e['methods'].update(methods)
                e['nos'].append(c[i_no])
                e['app_col'].add(c[i_app])
    return out, rows, hdr


def app_expected(apps):
    """スナップショット側の app 集合 -> インベントリの app 列の期待値"""
    if apps == {'ui'}:
        return 'UIアプリ'
    if apps == {'api'}:
        return 'APIアプリ(/api)'
    return '両方'


def main():
    p = argparse.ArgumentParser(description='スナップショットとインベントリを突き合わせる')
    p.add_argument('--snapshot', default=None, help='既定: $WEKO_API_INVENTORY_DIR/api_snapshot.json')
    p.add_argument('--tsv', default=None, help='既定: $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv')
    p.add_argument('--allow', default=None, help='既定: $WEKO_API_INVENTORY_DIR/reconcile_allow.json')
    p.add_argument('--out', help='Markdown 出力先')
    p.add_argument('--gate', action='store_true', help='未説明の差分があれば exit 1')
    p.add_argument('--summary-only', action='store_true',
                   help='件数のみ出力する。public リポジトリの CI ログ/artifact/PRコメントは'
                        '誰でも読めるため、URI や endpoint 名を出さない')
    a = p.parse_args()
    a.snapshot = a.snapshot or data_path('api_snapshot.json')
    a.tsv = a.tsv or data_path('weko3_api_list_full.tsv')
    a.allow = a.allow or data_path('reconcile_allow.json')

    snap, S = load_snapshot(a.snapshot)
    I, rows, _hdr = load_inventory(a.tsv)
    allow = {}
    if os.path.isfile(a.allow):
        allow = json.load(open(a.allow, encoding='utf-8'))
    allow_uris = allow.get('not_registered', {})
    allow_notreal = set(allow.get('not_a_route', []))

    # A. インベントリ未収載
    missing = []
    for u in sorted(set(S) - set(I)):
        e = S[u]
        missing.append({'uri': u, 'methods': sorted(e['methods']),
                        'key': e['keys'][0], 'provider': e.get('provider')})

    # B. 実機に無いインベントリ行
    phantom, phantom_known = [], []
    for u in sorted(set(I) - set(S)):
        item = {'uri': u, 'nos': I[u]['nos'], 'methods': sorted(I[u]['methods'])}
        nos = set(I[u]['nos'])
        if u in allow_uris or nos & allow_notreal:
            item['reason'] = allow_uris.get(u) or '(URIではない行)'
            phantom_known.append(item)
        else:
            phantom.append(item)

    # C. メソッド不一致
    method_diff = []
    for u in sorted(set(S) & set(I)):
        sm, im = S[u]['methods'], I[u]['methods']
        if sm != im:
            method_diff.append({'uri': u, 'nos': I[u]['nos'],
                                'snapshot': sorted(sm), 'inventory': sorted(im),
                                'only_live': sorted(sm - im), 'only_inv': sorted(im - sm)})

    # D. app 列の不一致(URIごとに、実機の登録先と台帳の app 列を比べる)
    app_diff = []
    seen_no = set()
    for u in sorted(set(S) & set(I)):
        exp = app_expected(S[u]['apps'])
        for no in I[u]['nos']:
            if no in seen_no:
                continue
            got = rows[no][3]
            uris_of_row = [norm(x) for x in rows[no][5].split(';') if norm(x)]
            if got == '両方':
                # 旧表現。UI 側 URI と /api 側 URI の両方が実機にあれば正。
                live_apps = set()
                for uu in uris_of_row:
                    for cand in (uu, norm('/api' + uu)):
                        if cand in S:
                            live_apps |= S[cand]['apps']
            else:
                # v2.1.0 以降の表現。行の URI が実機のどちらに登録されているかだけを見る。
                # 同じ view が UI と /api の双方にマウントされていても、行が担当するのは
                # 自分の URI 側だけなので、対の行の分まで期待値に含めてはならない。
                live_apps = set()
                for uu in uris_of_row:
                    if uu in S:
                        live_apps |= S[uu]['apps']
            if not live_apps:
                continue
            exp = app_expected(live_apps)
            if got != exp:
                app_diff.append({'no': no, 'uri': rows[no][5], 'inventory': got, 'live': exp})
            seen_no.add(no)

    # E. endpoint 単位の突き合わせ
    #    URI 単位の A/B/C だけでは、同じ URI に複数の Blueprint/設定が登録している
    #    ケース(static の /static/<path:filename> に 23件、RECORDS_REST_ENDPOINTS の
    #    item_route 重複など)の取りこぼしを検出できない。台帳は endpoint 単位で
    #    行を持つ方針なので、endpoint 集合でも突き合わせる。
    APP_TO_KEY = {'UIアプリ': 'ui', 'APIアプリ(/api)': 'api'}
    live_eps = {(e['app'], e['endpoint']) for e in snap['endpoints'].values()}
    inv_eps = {}
    i_ep = _hdr.index("endpoint") if "endpoint" in _hdr else None
    if i_ep is not None:
        for no, c in rows.items():
            if len(c) <= i_ep:
                continue
            ep = c[i_ep].strip()
            if not ep or ep in ('-', 'TODO', '(未登録)'):
                continue
            akey = APP_TO_KEY.get(c[3])
            for a_ in ([akey] if akey else ['ui', 'api']):
                inv_eps.setdefault((a_, ep), []).append(no)
    ep_missing = sorted(live_eps - set(inv_eps))
    ep_phantom = sorted(set(inv_eps) - live_eps)
    # 実機に無い endpoint は、その行の URI が既知許容(B')なら黙認する
    def row_allowed(no):
        c = rows.get(no)
        if not c:
            return False
        for u in c[5].split(';'):
            if norm(u) in allow_uris or norm(u) in allow_notreal:
                return True
        return False
    ep_phantom = [x for x in ep_phantom
                  if not all(row_allowed(no) for no in inv_eps[x])]

    summary_only = a.summary_only
    L = ['# スナップショット ↔ インベントリ 突き合わせ', '']
    L.append(f"- リビジョン: `{snap['meta'].get('revision')}` {snap['meta'].get('tag')} "
             f"経路URI={len(S)}")
    L.append(f"- 台帳: 行={len(rows)} URI={len(I)}")
    if summary_only:
        L.append('')
        L.append('> 件数のみ。詳細はプライベートリポジトリ側の完全版レポートを参照。')
    L.append('')
    unexplained = (len(missing) + len(phantom) + len(method_diff)
                   + len(app_diff) + len(ep_missing))
    L.append(f"## 判定: {'❌ 未説明の差分あり' if unexplained else '✅ 一致'} ({unexplained}件)")
    L.append('')
    L.append('| 検出 | 件数 |')
    L.append('|---|---:|')
    L.append(f'| A. インベントリ未収載(抽出漏れ) | {len(missing)} |')
    L.append(f'| B. 実機に無い(未説明) | {len(phantom)} |')
    L.append(f'| B\'. 実機に無い(既知・許容) | {len(phantom_known)} |')
    L.append(f'| C. メソッド不一致 | {len(method_diff)} |')
    L.append(f'| D. app列の不一致 | {len(app_diff)} |')
    L.append(f'| E. endpoint 未収載 | {len(ep_missing)} |')
    L.append(f"| E'. endpoint が実機に無い(参考) | {len(ep_phantom)} |")
    L.append('')

    if missing and not summary_only:
        L += ['## A. インベントリ未収載 — 台帳に追加が必要', '']
        for m in missing:
            prov = f"  [provider: {m['provider']}]" if m['provider'] else ''
            L.append(f"- `{','.join(m['methods'])}` `{m['uri']}` — {m['key']}{prov}")
        L.append('')
    if phantom and not summary_only:
        L += ['## B. 実機に無いインベントリ行 — 未説明', '']
        for x in phantom:
            L.append(f"- no={','.join(x['nos'])} `{x['uri']}`")
        L.append('')
    if method_diff and not summary_only:
        L += ['## C. メソッド不一致', '']
        for x in method_diff:
            L.append(f"- no={','.join(x['nos'])} `{x['uri']}` — 実機={x['snapshot']} / "
                     f"台帳={x['inventory']}（実機のみ {x['only_live']} / 台帳のみ {x['only_inv']}）")
        L.append('')
    if ep_missing and not summary_only:
        L += ['## E. endpoint 未収載 — 台帳に行の追加が必要', '']
        L += [f'- `{a_}` `{ep}`' for a_, ep in ep_missing]
        L += ['',
              '> 同じ URI に複数の Blueprint / 設定が登録されている場合、URI 単位の A では',
              '> 検出できない。台帳は endpoint 単位で行を持つ方針なので、こちらで拾う。', '']
    if ep_phantom and not summary_only:
        L += ["## E'. endpoint が実機に無い(参考)", '']
        L += [f'- `{a_}` `{ep}` — no.{",".join(inv_eps[(a_, ep)])}'
              for a_, ep in ep_phantom]
        L += ['']
    if app_diff and not summary_only:
        L += ['## D. app列の不一致', '']
        for x in app_diff:
            L.append(f"- no={x['no']} `{x['uri'][:70]}` — 台帳=`{x['inventory']}` / 実機=`{x['live']}`")
        L.append('')
    if phantom_known and not summary_only:
        L += ["## B'. 実機に無い(既知・許容)", '']
        for x in phantom_known:
            L.append(f"- no={','.join(x['nos'])} `{x['uri'][:70]}` — {x['reason']}")
        L.append('')

    md = '\n'.join(L)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(md + '\n')
        print(f'{a.out} を書き出しました')
    else:
        print(md)
    print(f'A={len(missing)} B={len(phantom)} C={len(method_diff)} D={len(app_diff)} '
          f"B'(既知)={len(phantom_known)}", file=sys.stderr)
    if a.gate and unexplained:
        sys.exit(1)


if __name__ == '__main__':
    main()
