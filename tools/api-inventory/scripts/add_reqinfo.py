# -*- coding: utf-8 -*-
"""機械で決まる列を実装から付与する(人手で埋める必要のない列を減らす)。

    python3 add_reqinfo.py            # 空欄/TODO のみ埋める
    python3 add_reqinfo.py --fix-oauth-scope   # oauth_scope の誤値も是正する

対象:
  query_params          request.args / request.values の参照キー
  body_params           request.get_json / request.form / request.json の参照キー
  request_content_type  Content-Type の検査、または JSON を読むか
  oauth_scope           @require_oauth_scopes(...) の引数
  cache_ratelimit       @limiter.limit(...) / cache デコレータ
  api_version           uri から導出(/v1, <string:version> 等)
  test_file             impl_func 名でテストディレクトリを検索

いずれも **空欄/`-`/`TODO` のセルだけを埋める**。台帳の既存値は後から精査されており、
一括再生成すると劣化するため(add_cols.py 等と同じ方針)。

例外: `--fix-oauth-scope` は oauth_scope に入っている **スコープではない値**
(`admin-role-table` 等)を `-` に戻す。OAuth スコープは `<資源>:<操作>` 形で、
認証方式(auth_method / auth_mechanism)とは別物。手入力で 253 行に
`admin-role-table` が入っていた。
"""
import argparse
import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
from snapshot import default_weko_root  # noqa: E402

EMPTY = ('', '-', 'TODO')
# スコープらしさは「<資源>:<操作> の並びを1つでも含むか」で見る。
# 注記付きの正当な値(例: 'deposit:write(Authorizationヘッダ使用時)'、
# 'invalid_scope(存在しないスコープ)')を落とさないため、完全一致にはしない。
SCOPE_RE = re.compile(r'[a-z_]+:[a-z_]+|_scope\b')

_src = {}


def seg_of(root, fp, ln, span=60):
    """実装関数の周辺ソース。add_cols.py と同じ考え方。"""
    if not fp or fp.startswith('(') or not str(ln).isdigit() or ln == '0':
        return ''
    key = (fp, ln)
    if key in _src:
        return _src[key]
    path = os.path.join(root, fp)
    try:
        lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
    except OSError:
        _src[key] = ''
        return ''
    i = int(ln) - 1
    _src[key] = '\n'.join(lines[max(0, i - 8):i + span])
    return _src[key]


def keys_from(seg, patterns):
    out = []
    for pat in patterns:
        out += re.findall(pat, seg)
    seen, res = set(), []
    for k in out:
        if k and k not in seen:
            seen.add(k)
            res.append(k)
    return ';'.join(res[:8]) if res else '-'


def col_query(seg):
    return keys_from(seg, [r"request\.args\.get\(\s*['\"]([\w\-]+)['\"]",
                           r"request\.args\.getlist\(\s*['\"]([\w\-]+)['\"]",
                           r"request\.values\.get\(\s*['\"]([\w\-]+)['\"]"])


def col_body(seg):
    k = keys_from(seg, [r"request\.form\.get\(\s*['\"]([\w\-]+)['\"]",
                        r"request\.form\[\s*['\"]([\w\-]+)['\"]",
                        r"(?:data|json|body)\.get\(\s*['\"]([\w\-]+)['\"]"])
    if k == '-' and re.search(r"request\.(get_json|json)\b", seg):
        return 'JSON本文(キー不定)'
    return k


def col_ctype(seg):
    if re.search(r"request\.headers\[['\"]Content-Type", seg) or \
            re.search(r"content_type\s*[!=]=", seg):
        return 'application/json(検査あり)'
    if re.search(r"request\.(get_json|json)\b", seg):
        return 'application/json'
    if re.search(r"request\.form\b", seg):
        return 'application/x-www-form-urlencoded'
    if re.search(r"request\.files\b", seg):
        return 'multipart/form-data'
    return '-'


def col_scope(seg):
    m = re.findall(r"require_oauth_scopes\(([^)]*)\)", seg)
    scopes = []
    for arg in m:
        scopes += re.findall(r"['\"]([\w:]+)['\"]", arg)
        scopes += re.findall(r"(\w+_scope)\b", arg)
    return ';'.join(dict.fromkeys(scopes)) if scopes else '-'


def col_cache(seg):
    hits = re.findall(r"@limiter\.limit\(([^)]*)\)", seg)
    if hits:
        return 'rate-limit:' + re.sub(r"['\"]", '', hits[0])[:40]
    if re.search(r"@cache|cached\(", seg):
        return 'cache あり'
    return '-'


def col_apiver(uri):
    if '/v2/' in uri or uri.endswith('/v2'):
        return 'v2'
    if '/v1/' in uri or uri.endswith('/v1') or '<string:version>' in uri:
        return 'v1'
    return '-'


def find_tests(root, impl_func, cache={}):
    """impl_func 名を含むテストファイルを探す。"""
    if not impl_func or impl_func in ('-', 'TODO'):
        return '-'
    if impl_func in cache:
        return cache[impl_func]
    hits = []
    for dp, dn, fn in os.walk(os.path.join(root, 'modules')):
        if '/tests' not in dp:
            continue
        for f in fn:
            if not f.startswith('test') or not f.endswith('.py'):
                continue
            p = os.path.join(dp, f)
            try:
                if impl_func in open(p, encoding='utf-8', errors='replace').read():
                    hits.append(os.path.relpath(p, root))
            except OSError:
                pass
        if len(hits) >= 3:
            break
    cache[impl_func] = ';'.join(hits[:3]) if hits else '-'
    return cache[impl_func]


def main():
    p = argparse.ArgumentParser(description='機械で決まる列を付与する')
    p.add_argument('--full', default=None)
    p.add_argument('--weko-root', default=None)
    p.add_argument('--fix-oauth-scope', action='store_true',
                   help='oauth_scope に入っているスコープでない値を - に戻す')
    p.add_argument('--with-test-file', action='store_true',
                   help='test_file も探す(全モジュール走査で時間がかかる)')
    a = p.parse_args()
    full = a.full or data_path('weko3_api_list_full.tsv')
    root = a.weko_root or default_weko_root()

    lines = open(full, encoding='utf-8').read().rstrip('\n').split('\n')
    hdr = lines[0].split('\t')
    H = {n: i for i, n in enumerate(hdr)}
    out = [lines[0]]
    filled = {k: 0 for k in ('query_params', 'body_params', 'request_content_type',
                             'oauth_scope', 'cache_ratelimit', 'api_version', 'test_file')}
    fixed = 0
    for raw in lines[1:]:
        c = raw.split('\t') + [''] * len(hdr)
        c = c[:len(hdr)]
        seg = seg_of(root, c[H['impl_file']], c[H['impl_line']])
        calc = {
            'query_params': col_query(seg),
            'body_params': col_body(seg),
            'request_content_type': col_ctype(seg),
            'oauth_scope': col_scope(seg),
            'cache_ratelimit': col_cache(seg),
            'api_version': col_apiver(c[H['uri']]),
        }
        if a.with_test_file:
            calc['test_file'] = find_tests(root, c[H['impl_func']])
        # oauth_scope の誤値是正: スコープ形(<資源>:<操作>)でない値は落とす
        if a.fix_oauth_scope:
            cur = c[H['oauth_scope']]
            if cur not in EMPTY and not SCOPE_RE.search(cur):
                c[H['oauth_scope']] = '-'
                fixed += 1
        for n, v in calc.items():
            if n not in H:
                continue
            if c[H[n]] in EMPTY and v != '-':
                c[H[n]] = v
                filled[n] += 1
        out.append('\t'.join(x.replace('\t', ' ') for x in c))

    open(full, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(f'{full}: {len(lines) - 1} 行')
    for k, v in filled.items():
        if v or k in ('query_params', 'oauth_scope'):
            print(f'  {k:<22} 空欄を埋めた: {v}')
    if a.fix_oauth_scope:
        print(f'  oauth_scope の誤値を - に戻した: {fixed}')


if __name__ == '__main__':
    main()
