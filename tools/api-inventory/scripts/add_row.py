# -*- coding: utf-8 -*-
"""台帳に新規行の雛形を追加する。

    # reconcile が「A. インベントリ未収載」に挙げた経路を追加する
    python3 add_row.py --endpoint api:weko_admin.get_widget_item_list
    python3 add_row.py --uri /api/items/import-task --append

`api_snapshot.json`(実機 url_map)と git から **機械的に決まる列だけを埋め**、
調査が要る列は `TODO` を入れて出力する。57列を手で並べる作業をなくすためのもの。

自動で埋まる: no / module / api_type / app / method / uri / path_params /
              blueprint / endpoint / impl_func / impl_file / impl_line /
              auth_required / auth_method / auth_mechanism / api_version /
              last_commit系4列
`TODO` のまま残る: summary / response / status_codes / roles / data_op /
              data_store / side_effects / config_deps /
              test_file / notes / sec_* / dynamic_verified など、
              **ソースを読まないと書けない列**。

派生列(priority / test_* / cleanup)は空のままでよい。後で
test_coverage.py → prioritize.py が付与する。
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
from snapshot import default_weko_root  # noqa: E402

AUTO_TODO = 'TODO'
DERIVED = ('priority', 'priority_reason', 'test_normal', 'test_abnormal',
           'test_boundary', 'test_exception', 'test_gap', 'cleanup')


def sh(args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def module_of(impl_file):
    m = re.match(r'modules/([^/]+)/', impl_file or '')
    if m:
        return m.group(1)
    if impl_file.startswith('(site-packages)'):
        return impl_file.split('/')[0].replace('(site-packages)', '').strip() or '-'
    return '-'


def api_type_of(app, uri, view):
    if 'flask_admin' in (view or ''):
        return '管理画面(ModelView自動生成)'
    if uri.startswith('/admin/'):
        return '管理画面'
    if app == 'api':
        return 'REST API'
    return '画面ビュー'


def git_last(root, impl_file, impl_line):
    """実装関数の行範囲の最終コミット。enrich_git.py と同じ考え方。"""
    if not impl_file or impl_file.startswith('(site-packages)') or not impl_line:
        return ['-', '-', '-', '-']
    try:
        ln = int(impl_line)
    except ValueError:
        return ['-', '-', '-', '-']
    out = sh(['git', '-C', root, 'log', '-1', '--format=%h\x1f%ad\x1f%s',
              '--date=short', '-L', f'{ln},{ln + 40}:{impl_file}'])
    line = out.split('\n', 1)[0] if out else ''
    p = line.split('\x1f')
    if len(p) != 3:
        return ['-', '-', '-', '-']
    tags = sh(['git', '-C', root, 'tag', '--sort=creatordate', '--contains', p[0]])
    tag = next((t for t in tags.split('\n') if t.strip()), '(未リリース)')
    return [p[0], p[1], p[2].replace('\t', ' ')[:120], tag]


def build(hdr, snap_key, e, root, next_no):
    app = 'APIアプリ(/api)' if e['app'] == 'api' else 'UIアプリ'
    prefix = '/api' if e['app'] == 'api' else ''
    rules = e.get('routes') or [{'rule': r, 'methods': e.get('methods', [])}
                               for r in e.get('rules', [])]
    uri = ';'.join(prefix + r['rule'] for r in rules)
    methods = sorted({m for r in rules for m in r['methods']})
    impl = e.get('impl', '')
    impl_file, impl_line = (impl.split(':') + [''])[:2] if impl else ('', '')
    params = ';'.join(sorted({m for r in rules
                              for m in re.findall(r'<([^>]+)>', r['rule'])})) or '-'
    decs = e.get('auth_decorators') or []
    if decs:
        auth_req, auth_method = '要', ';'.join(decs)
        mech = 'decorator'
    elif e.get('attrs') == 'unknown':
        auth_req, auth_method, mech = AUTO_TODO, AUTO_TODO + '(属性不明。実装を読むこと)', 'framework'
    else:
        auth_req, auth_method, mech = '不要', 'none', 'none'

    v = {n: AUTO_TODO for n in hdr}
    for n in DERIVED:
        if n in v:
            v[n] = ''
    v.update({
        'no': str(next_no),
        'module': module_of(impl_file),
        'api_type': api_type_of(e['app'], uri, e.get('view', '')),
        'app': app,
        'method': ','.join(methods),
        'uri': uri,
        'path_params': params,
        'blueprint': e['endpoint'].rsplit('.', 1)[0] if '.' in e['endpoint'] else e['endpoint'],
        'endpoint': e['endpoint'],
        'impl_func': (e.get('view') or '').split('.')[-1] or AUTO_TODO,
        'impl_file': impl_file or (f"(provider){e['provider']}" if e.get('provider') else AUTO_TODO),
        'impl_line': impl_line or '-',
        'auth_required': auth_req,
        'auth_method': auth_method,
        'auth_mechanism': mech,
        'api_version': 'v1' if '/v1' in uri or '<string:version>' in uri else '-',
        'deprecated': '-',
        'query_params': '-', 'body_params': '-', 'request_content_type': '-',
        'oauth_scope': '-', 'cache_ratelimit': '-',
    })
    g = git_last(root, impl_file, impl_line)
    for n, val in zip(('last_commit', 'last_commit_date', 'last_commit_subject',
                       'release_tag'), g):
        if n in v:
            v[n] = val
    return [v[n] for n in hdr]


def main():
    p = argparse.ArgumentParser(description='台帳に新規行の雛形を作る')
    p.add_argument('--endpoint', help='api_snapshot.json のキー(例 api:weko_admin.foo)')
    p.add_argument('--uri', help='URI の一部で検索して特定する')
    p.add_argument('--snapshot', default=None)
    p.add_argument('--full', default=None)
    p.add_argument('--weko-root', default=None)
    p.add_argument('--append', action='store_true', help='full.tsv に追記する(既定は表示のみ)')
    a = p.parse_args()
    snap_p = a.snapshot or data_path('api_snapshot.json')
    full = a.full or data_path('weko3_api_list_full.tsv')
    root = a.weko_root or default_weko_root()

    E = json.load(open(snap_p, encoding='utf-8'))['endpoints']
    keys = []
    if a.endpoint:
        keys = [a.endpoint] if a.endpoint in E else []
    elif a.uri:
        # APIアプリのルールは url_map 上 /api を含まない(DispatcherMiddleware で
        # マウントされるため)。利用者は /api/... で探すので前置してから比較する。
        def full_rules(v):
            pre = '/api' if v['app'] == 'api' else ''
            return [pre + r['rule'] for r in v.get('routes', [])]
        keys = [k for k, v in E.items()
                if any(a.uri in r for r in full_rules(v))]
    if not keys:
        sys.exit('該当する経路がスナップショットにありません。'
                 '--endpoint か --uri を見直してください。')
    if len(keys) > 1 and not a.append:
        print('複数該当:')
        for k in keys:
            print('  ' + k)

    lines = open(full, encoding='utf-8').read().rstrip('\n').split('\n')
    hdr = lines[0].split('\t')
    next_no = max(int(l.split('\t')[0]) for l in lines[1:]
                  if l.split('\t')[0].isdigit()) + 1

    rows = []
    for k in keys:
        rows.append(build(hdr, k, E[k], root, next_no))
        next_no += 1

    if a.append:
        with open(full, 'a', encoding='utf-8') as f:
            for r in rows:
                f.write('\t'.join(r) + '\n')
        print(f'{full} に {len(rows)} 行を追記しました。')
        print('  次に: TODO の列をソースを読んで埋め、')
        print('        test_coverage.py → prioritize.py → build_checklist.py を実行')
    else:
        for r in rows:
            print('--- 追記される行(--append で書き込み) ---')
            for n, val in zip(hdr, r):
                mark = '  ' if val != AUTO_TODO else '★'
                if val != '':
                    print(f'{mark}{n:<22} {val[:70]}')
            print('  ★ が付いた列はソースを読んで埋めること')


if __name__ == '__main__':
    main()
