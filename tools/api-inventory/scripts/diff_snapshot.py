# -*- coding: utf-8 -*-
"""API スナップショット差分 — 追加/削除/仕様変更を機械的に検知する。

    python3 diff_snapshot.py OLD.json NEW.json [--gate] [--out drift.md]

分類:
  ADDED / REMOVED        経路の増減
  RULE_CHANGED           endpoint 同一で URL が変化
  METHODS_CHANGED        HTTPメソッドの増減
  AUTH_CHANGED           認証・認可デコレータの変化(最優先)
  IMPL_CHANGED           デコルータ据置きで実装本体が変化(認可ロジック内包の変化)
  ATTRS_UNKNOWN_NEW      経路はあるが静的解析で属性が取れない新規

ゲート(--gate 指定時、該当があれば exit 1):
  G1 新規エンドポイントに認証系デコレータが無い
  G2 認証系デコレータが削除された
  G3 認証/認可デコレータのコメントアウトが増えた
  G4 認可を左右する config が危険側に変わった
  G5 ModelView の can_delete / can_export が False -> True
  G6 属性不明のまま追加された経路がある(レビュー必須)
"""
import argparse
import json
import sys

FAIL = 'FAIL'
WARN = 'WARN'

# G4: 危険側とみなす値
DANGEROUS_VALUES = {
    '*_PERMISSION_FACTORY': ('None',),
    'CSRF保護': ('False',),
    '認証の全無効化': ('True',),
}


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def auth_of(e):
    return set(e.get('auth_decorators') or [])


def classify(old, new):
    """エンドポイント単位の変化を分類する。"""
    o, n = old['endpoints'], new['endpoints']
    res = {k: [] for k in (
        'ADDED', 'REMOVED', 'RULE_CHANGED', 'METHODS_CHANGED',
        'AUTH_CHANGED', 'IMPL_CHANGED', 'ATTRS_UNKNOWN_NEW')}

    for key in sorted(set(n) - set(o)):
        e = n[key]
        res['ADDED'].append({'key': key, 'new': e})
        if e.get('attrs') == 'unknown':
            res['ATTRS_UNKNOWN_NEW'].append({'key': key, 'new': e})
    for key in sorted(set(o) - set(n)):
        res['REMOVED'].append({'key': key, 'old': o[key]})

    for key in sorted(set(o) & set(n)):
        a, b = o[key], n[key]
        if a.get('rules') != b.get('rules'):
            res['RULE_CHANGED'].append({'key': key, 'old': a, 'new': b})
        # メソッドはルール単位で比較する(endpoint 単位の union では取りこぼす)
        am = {x['rule']: x['methods'] for x in a.get('routes', [])}
        bm = {x['rule']: x['methods'] for x in b.get('routes', [])}
        if any(am.get(k2) != bm.get(k2) for k2 in set(am) & set(bm)):
            res['METHODS_CHANGED'].append({'key': key, 'old': a, 'new': b})
        if a.get('auth_hash') != b.get('auth_hash'):
            res['AUTH_CHANGED'].append({'key': key, 'old': a, 'new': b})
        elif a.get('body_hash') != b.get('body_hash'):
            res['IMPL_CHANGED'].append({'key': key, 'old': a, 'new': b})
        # 属性が取れていたのに取れなくなった = 実装の持ち方が変わった
        if a.get('attrs') == 'ast' and b.get('attrs') == 'unknown':
            res['ATTRS_UNKNOWN_NEW'].append({'key': key, 'new': b})
    return res


def diff_modelviews(old, new):
    o, n = old.get('modelviews', {}), new.get('modelviews', {})
    added = [{'endpoint': k, 'new': n[k]} for k in sorted(set(n) - set(o))]
    removed = [{'endpoint': k} for k in sorted(set(o) - set(n))]
    flipped = []
    for k in sorted(set(o) & set(n)):
        for flag in ('can_create', 'can_edit', 'can_delete', 'can_export', 'can_view_details'):
            if o[k].get(flag) is False and n[k].get(flag) is True:
                flipped.append({'endpoint': k, 'flag': flag})
        if o[k].get('column_export_list') != n[k].get('column_export_list'):
            flipped.append({'endpoint': k, 'flag': 'column_export_list',
                            'old': o[k].get('column_export_list'),
                            'new': n[k].get('column_export_list')})
    return added, removed, flipped


def diff_config(old, new):
    o, n = old.get('config', {}), new.get('config', {})
    changed = []
    for k in sorted(set(o) & set(n)):
        if o[k]['value_hash'] != n[k]['value_hash']:
            changed.append({'key': k, 'label': n[k]['label'],
                            'old': o[k]['value'], 'new': n[k]['value']})
    for k in sorted(set(n) - set(o)):
        changed.append({'key': k, 'label': n[k]['label'], 'old': '(なし)', 'new': n[k]['value']})
    for k in sorted(set(o) - set(n)):
        changed.append({'key': k, 'label': o[k]['label'], 'old': o[k]['value'], 'new': '(削除)'})
    return changed


def diff_packages(old, new):
    """依存パッケージの版変化。経路の増減を依存更新に帰着させるために取る。"""
    o, n = old.get('packages', {}), new.get('packages', {})
    out = []
    for k in sorted(set(o) & set(n)):
        if o[k] != n[k]:
            out.append({'package': k, 'old': o[k], 'new': n[k]})
    for k in sorted(set(n) - set(o)):
        out.append({'package': k, 'old': '(なし)', 'new': n[k]})
    for k in sorted(set(o) - set(n)):
        out.append({'package': k, 'old': o[k], 'new': '(削除)'})
    return out


def provider_name(e):
    p = (e or {}).get('provider') or ''
    return p.split('==')[0]


def diff_commented(old, new):
    o, n = old.get('commented_auth', {}), new.get('commented_auth', {})
    out = []
    for mod in sorted(n):
        before = {(c['line'], c['text']) for c in o.get(mod, [])}
        before_text = {c['text'] for c in o.get(mod, [])}
        for c in n[mod]:
            if (c['line'], c['text']) not in before and c['text'] not in before_text:
                out.append({'module': mod, **c})
    return out


def gates(res, mv_added, mv_flipped, conf_changed, commented_new, pkg_changed):
    """(レベル, ゲートID, 説明, 該当リスト) を返す。"""
    g = []

    g1 = [x for x in res['ADDED']
          if x['new'].get('attrs') == 'ast' and not auth_of(x['new'])]
    if g1:
        g.append((FAIL, 'G1', '新規エンドポイントに認証系デコレータが無い', g1))

    g2 = [x for x in res['AUTH_CHANGED'] if auth_of(x['old']) - auth_of(x['new'])]
    if g2:
        g.append((FAIL, 'G2', '認証系デコレータが削除された', g2))

    if commented_new:
        g.append((FAIL, 'G3', '認証/認可デコレータのコメントアウトが増えた', commented_new))

    g4 = [c for c in conf_changed
          if c['new'] in DANGEROUS_VALUES.get(c['label'], ())]
    if g4:
        g.append((FAIL, 'G4', '認可を左右する config が危険側に変わった', g4))

    g5 = [f for f in mv_flipped if f['flag'] in ('can_delete', 'can_export')]
    if g5:
        g.append((FAIL, 'G5', 'ModelView の can_delete / can_export が False -> True', g5))

    g6 = res['ATTRS_UNKNOWN_NEW']
    if g6:
        g.append((FAIL, 'G6', '属性不明のまま追加された経路がある(手動レビュー必須)', g6))

    # G7: 依存更新に伴う経路の増減。外部ライブラリ由来の経路は
    # ソース走査では原理的に見えないため、実機ダンプでしか捕捉できない。
    bumped = {c['package'] for c in pkg_changed}
    g7 = [x for x in res['ADDED'] + res['REMOVED']
          if provider_name(x.get('new') or x.get('old')) in bumped]
    if g7:
        g.append((FAIL, 'G7', '依存パッケージの更新で外部ライブラリ由来の経路が増減した', g7))

    if mv_added:
        g.append((WARN, 'W1', 'ModelView が追加された(1つにつき自動生成8ルート・削除系を含む)', mv_added))
    if res['IMPL_CHANGED']:
        g.append((WARN, 'W2', '実装本体が変化(data_op / 情報露出を再確認)', res['IMPL_CHANGED']))
    if res['METHODS_CHANGED']:
        g.append((WARN, 'W3', 'HTTPメソッドが増減した', res['METHODS_CHANGED']))
    if res['RULE_CHANGED']:
        g.append((WARN, 'W4', 'URL が変化した', res['RULE_CHANGED']))
    if pkg_changed:
        # 経路が変わらなくても、既存経路の挙動が変わっている可能性がある
        g.append((WARN, 'W6', '依存パッケージの版が変化した', pkg_changed))
    other_conf = [c for c in conf_changed if c not in g4]
    if other_conf:
        g.append((WARN, 'W5', '監視対象 config が変化した', other_conf))
    return g


def one_line(x):
    # 依存パッケージの版変化
    if 'package' in x:
        return f"`{x['package']}` — {x['old']} -> {x['new']}"
    # config 変化(label を持つ)
    if 'label' in x:
        return f"`{x.get('key')}` ({x['label']}) — `{x.get('old')}` -> `{x.get('new')}`"
    # コメントアウト認証
    if 'module' in x and 'line' in x:
        return f"`{x['module']}:{x['line']}` — {x['text']}"
    # ModelView フラグ変化
    if 'flag' in x:
        return (f"`{x['endpoint']}` — {x['flag']}: "
                f"{x.get('old', False)} -> {x.get('new', True)}")
    # ModelView 追加/削除
    if 'endpoint' in x and 'key' not in x:
        n = x.get('new') or {}
        return (f"`{x['endpoint']}` — model={n.get('model')} "
                f"del={n.get('can_delete')} exp={n.get('can_export')}")
    # エンドポイント変化
    e = x.get('new') or x.get('old') or {}
    rules = ','.join(e.get('rules', []))[:70]
    meth = ','.join(e.get('methods', []))
    auth = ','.join(e.get('auth_decorators') or []) or '(なし)'
    line = f"`{x['key']}` — {meth} {rules} — auth: {auth}"
    old_e = x.get('old')
    if old_e and x.get('new') and old_e.get('auth_decorators') != e.get('auth_decorators'):
        before = ','.join(old_e.get('auth_decorators') or []) or '(なし)'
        line += f"  ← 旧: {before}"
    if old_e and x.get('new') and old_e.get('rules') != e.get('rules'):
        line += f"  ← 旧URL: {','.join(old_e.get('rules', []))[:70]}"
    if e.get('provider'):
        line += f"  [provider: {e['provider']}]"
    if e.get('reason'):
        line += f"  [{e['reason']}]"
    if e.get('impl'):
        line += f"  ({e['impl']})"
    return line


def render(old, new, res, mv, conf_changed, commented_new, pkg_changed, gate_list,
           summary_only=False):
    om, nm = old['meta'], new['meta']
    L = []
    L.append('# API インベントリ差分レポート')
    L.append('')
    L.append(f"- 旧: `{om.get('revision')}` {om.get('tag')} (profile={om.get('profile')}) "
             f"endpoints={om['counts']['endpoints']} "
             f"(外部ライブラリ由来 {om['counts'].get('external_endpoints', '?')})")
    L.append(f"- 新: `{nm.get('revision')}` {nm.get('tag')} (profile={nm.get('profile')}) "
             f"endpoints={nm['counts']['endpoints']} "
             f"(外部ライブラリ由来 {nm['counts'].get('external_endpoints', '?')})")
    if om.get('profile') != nm.get('profile'):
        L.append('')
        L.append('> **注意**: プロファイルが異なります。条件付き blueprint 登録の差が '
                 '追加/削除として現れるため、同一プロファイル同士で比較してください。')
    L.append('')

    fails = [g for g in gate_list if g[0] == FAIL]
    warns = [g for g in gate_list if g[0] == WARN]
    L.append(f"## 判定: {'❌ FAIL' if fails else '✅ PASS'} "
             f"(FAIL {len(fails)} / WARN {len(warns)})")
    L.append('')

    L.append('## サマリ')
    L.append('')
    L.append('| 分類 | 件数 |')
    L.append('|---|---:|')
    for k, v in res.items():
        L.append(f'| {k} | {len(v)} |')
    L.append(f"| ModelView 追加 | {len(mv[0])} |")
    L.append(f"| ModelView 削除 | {len(mv[1])} |")
    L.append(f"| ModelView フラグ変化 | {len(mv[2])} |")
    L.append(f'| config 変化 | {len(conf_changed)} |')
    L.append(f'| コメントアウト認証の増加 | {len(commented_new)} |')
    L.append(f'| 依存パッケージの版変化 | {len(pkg_changed)} |')
    L.append('')

    for level, gid, desc, items in gate_list:
        L.append(f"## [{level}] {gid} {desc} — {len(items)}件")
        L.append('')
        if summary_only:
            # 依存パッケージの版は公開情報なので名前を出してよい。
            # 原因追跡に必要で、経路や所見は一切含まない。
            if gid == 'W6':
                for x in items[:40]:
                    L.append(f'- {one_line(x)}')
                if len(items) > 40:
                    L.append(f'- … ほか {len(items) - 40} 件')
            else:
                L.append('> 件数のみ。該当の経路名は秘密側の完全版レポートを参照。')
            L.append('')
            continue
        for x in items[:40]:
            L.append(f'- {one_line(x)}')
        if len(items) > 40:
            L.append(f'- … ほか {len(items) - 40} 件')
        L.append('')

    if not gate_list:
        L.append('変化はありません。')
        L.append('')

    L.append('---')
    L.append('')
    if summary_only:
        return '\n'.join(L)
    L.append('## 全分類の明細')
    L.append('')
    for k, v in res.items():
        if not v:
            continue
        L.append(f'### {k} — {len(v)}件')
        L.append('')
        for x in v[:60]:
            L.append(f'- {one_line(x)}')
        if len(v) > 60:
            L.append(f'- … ほか {len(v) - 60} 件')
        L.append('')
    return '\n'.join(L)


def main():
    p = argparse.ArgumentParser(description='API スナップショットの差分を取る')
    p.add_argument('old')
    p.add_argument('new')
    p.add_argument('--out', help='Markdown 出力先(既定: 標準出力)')
    p.add_argument('--json-out', help='機械可読な差分の出力先')
    p.add_argument('--gate', action='store_true', help='FAIL があれば exit 1')
    p.add_argument('--summary-only', action='store_true',
                   help='件数のみ出力する。public リポジトリの CI ログ/artifact/PRコメントは'
                        '誰でも読めるため、URI や endpoint 名を出さない')
    a = p.parse_args()

    old, new = load(a.old), load(a.new)
    res = classify(old, new)
    mv = diff_modelviews(old, new)
    conf_changed = diff_config(old, new)
    commented_new = diff_commented(old, new)
    pkg_changed = diff_packages(old, new)
    gate_list = gates(res, mv[0], mv[2], conf_changed, commented_new, pkg_changed)

    md = render(old, new, res, mv, conf_changed, commented_new, pkg_changed, gate_list,
                summary_only=a.summary_only)
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write(md + '\n')
        print(f'{a.out} を書き出しました')
    else:
        print(md)

    if a.json_out:
        with open(a.json_out, 'w', encoding='utf-8') as f:
            json.dump({'endpoints': res, 'modelviews_added': mv[0],
                       'modelviews_removed': mv[1], 'modelviews_flipped': mv[2],
                       'config': conf_changed, 'commented_auth': commented_new,
                       'packages': pkg_changed,
                       'gates': [{'level': l, 'id': i, 'desc': d, 'count': len(x)}
                                 for l, i, d, x in gate_list]},
                      f, ensure_ascii=False, indent=1)

    fails = [g for g in gate_list if g[0] == FAIL]
    for level, gid, desc, items in gate_list:
        print(f'[{level}] {gid} {desc}: {len(items)}件', file=sys.stderr)
    if a.gate and fails:
        sys.exit(1)


if __name__ == '__main__':
    main()
