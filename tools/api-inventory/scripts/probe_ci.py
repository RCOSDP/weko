# -*- coding: utf-8 -*-
"""Phase 7-b: フィクスチャ駆動の到達可否測定(CI向け)。

    python3 probe_ci.py --only rerun_nos.txt --out probe.json --gate

`probe.py` は参考実装でセッション固有のUUID・パスがハードコードされている。
本スクリプトは `fixtures.py` が出力した fixtures.json からプレースホルダを解決するため、
まっさらな CI 環境でも動く。

測定対象は `--only` で渡した `no` に限定する(全926行を毎PR測るのは時間がかかりすぎる)。
CI では changed_rows.py の出力と diff_snapshot の ADDED/AUTH_CHANGED の和集合を渡す。

安全装置: GET/HEAD 以外は既定でスキップする。書き込み系まで測るには --allow-writes を
明示すること(CI のコンテナは install.sh が毎回作り直す使い捨てなので許可してよい)。
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
import tempfile

IDENTITIES = [
    ('anon', None),
    ('general', 'user@example.org'),
    ('contributor', 'contributor@example.org'),
    ('comadmin', 'comadmin@example.org'),
    ('repoadmin', 'repoadmin@example.org'),
    ('sysadmin', 'wekosoftware@nii.ac.jp'),
]

SAFE_METHODS = ('GET', 'HEAD')
REDIRECT_CODES = ('301', '302', '303', '307', '308')


def curl(args):
    return subprocess.run(['curl', '-sk', '--max-time', '15'] + args,
                          capture_output=True, text=True)


class Session:
    """identity ごとの Cookie を持つ。測定直前にログインし直して失効を避ける。"""

    def __init__(self, base, host, email, password, workdir):
        self.base, self.host, self.email = base, host, email
        self.jar = os.path.join(workdir, f'ck_{email or "anon"}')
        self.password = password
        self.relogins = 0
        self.ok = True
        if email:
            self.ok = self.login()

    def login(self):
        """ログインし直して Cookie を取り直す。"""
        if not self.email:
            return True
        r = curl(['-c', self.jar, '-o', '/dev/null', '-w', '%{http_code}',
                  '-H', f'Host: {self.host}', '-X', 'POST',
                  '-H', 'Content-Type: application/json',
                  '-d', json.dumps({'email': self.email,
                                    'password': self.password}),
                  f'{self.base}/api/v1/login'])
        return r.stdout.strip() == '200'

    def request(self, method, path, body_file, _retry=True):
        """1回測る。認証済みのはずがログイン画面へ飛ばされたら張り直して測り直す。

        --allow-writes を付けると /logout や /accounts/settings/session(POST) など
        「自分のセッションを消す」エンドポイントも叩くため、そこを通過した時点で
        以降の測定が全部「遮断」に見えてしまう(v2.1.0 の一括再測で実際に起きた)。
        """
        code, redirect = self._request_once(method, path, body_file)
        orig = code
        if code in REDIRECT_CODES:
            redirect, code = self.follow(method, redirect, code, body_file)
        if (_retry and self.email and self.ok
                and 'login' in (redirect or '').lower()):
            if self.login():
                self.relogins += 1
                return self.request(method, path, body_file, _retry=False)
        return code, redirect, orig

    def _request_once(self, method, path, body_file):
        args = ['-o', body_file, '-w', '%{http_code}\t%{redirect_url}',
                '-H', f'Host: {self.host}', '-X', method]
        if self.email:
            args += ['-b', self.jar]
        if method not in SAFE_METHODS:
            args += ['-H', 'Content-Type: application/json', '-d', '{}']
        args.append(f'{self.base}{path}')
        out = curl(args).stdout.strip().split('\t')
        return out[0], (out[1] if len(out) > 1 else '')

    def follow(self, method, redirect, code, body_file=None, limit=6):
        """転送を最大 limit 段たどり、(最終URL, 最終ステータス) を返す。

        1段目だけを見ると判定を2通り取りこぼす(v2.1.0 の実測で判明):
          - werkzeug の strict_slashes は末尾スラッシュを 308 で正規化するため、
            その先のログイン転送が見えない。
          - 転送先が 403 を返しても、308 のまま「到達」と誤判定してしまう。
        302/303 はブラウザ同様 GET に切り替える(書き込みの二重実行を避ける)。
        転送ループは末尾に ' [LOOP]' を付けて返す。
        """
        seen = set()
        for _ in range(limit):
            if not redirect:
                return redirect, code
            if 'login' in redirect.lower():
                return redirect, code       # ログイン画面に着いた時点で遮断確定
            if redirect in seen:
                return redirect + ' [LOOP]', code
            seen.add(redirect)
            nxt_method = method if code in ('307', '308') else 'GET'
            args = ['-o', body_file or os.devnull,
                    '-w', '%{http_code}\t%{redirect_url}',
                    '-H', f'Host: {self.host}', '-X', nxt_method]
            if self.email:
                args += ['-b', self.jar]
            args.append(redirect.replace(f'https://{self.host}', self.base, 1))
            out = curl(args).stdout.strip().split('\t')
            nxt_code = out[0]
            nxt = out[1] if len(out) > 1 else ''
            if nxt_code not in REDIRECT_CODES:
                return redirect, nxt_code    # ← 最終ステータスで判定させる
            redirect, code, method = nxt, nxt_code, nxt_method
        return redirect + ' [DEEP]', code


def classify(code, body_path, redirect=''):
    """到達(認可を通過してハンドラに入った) / 遮断 / 判定不能 を分ける。

    500 は原則「認可通過後のクラッシュ=到達」だが、APIアプリの login_required は
    url_for('security.login') の BuildError で 500 になる(= 遮断)。本文で切り分ける。
    """
    try:
        body = open(body_path, encoding='utf-8', errors='replace').read(4000)
    except Exception:
        body = ''
    if code in ('401', '403'):
        return '遮断'
    if code in REDIRECT_CODES:
        # ログイン画面への転送は遮断。それ以外は処理が完了した転送(到達)。
        # code / redirect は Session.follow() が転送を追いきった最終地点であること。
        # 308(末尾スラッシュ正規化)の先にログイン転送が隠れるため、1段目だけでは
        # 判定できない(v2.1.0 実測で判明)。
        # 注意: 転送先がログインでも「ハンドラが副作用を起こしてからログインへ
        # 転送した」可能性は排除できない。副作用の有無は DB を直接見て確かめること
        # (no.480 /record/<pid>/publish は実際に確かめ、publish_status は
        #  変化しない=真に遮断、と確定した)。
        low = (redirect or '').lower()
        if '[loop]' in low or '[deep]' in low:
            return '判定不能'      # 転送ループ / 追いきれず
        if 'login' in low or 'signin' in low or 'sso' in low:
            return '遮断'
        return '到達'
    if code == '500':
        return '遮断' if ('security.login' in body or 'BuildError' in body) else '到達'
    if code == '404':
        return '判定不能'          # hidden=True の権限NG か、対象が無いだけか区別できない
    if code == '000':
        return '判定不能'          # タイムアウト等
    if code.startswith('2') or code in ('400', '405', '415'):
        return '到達'
    return '判定不能'


def build_resolver(fx):
    """URI のプレースホルダをフィクスチャの実値に置き換える表を作る。"""
    ids = fx.get('ids') or {}
    priv = fx['records'].get('private', {})
    other = fx['records'].get('other_owner', {})
    f = fx.get('file') or {}
    table = [
        (r'<string:version>', '__VERSION__'),
        (r'<[^>]*\bversion\b[^>]*>', '__VERSION__'),
        (r'<[^>]*uuid[^>]*>', f.get('uuid_triplet', '')),
        (r'<[^>]*bucket_id[^>]*>', f.get('bucket', '')),
        (r'<path:[^>]+>', 'secret.png'),
        (r'<[^>]*(key|filename|file_name)[^>]*>', 'secret.png'),
        (r'<[^>]*(pid_value|recid|pid\()[^>]*>', str(priv.get('recid', ''))),
        (r'<[^>]*index_id[^>]*>', str(fx.get('index', ''))),
        (r'<[^>]*community_id[^>]*>', (fx.get('community') or {}).get('id', '')),
        (r'<[^>]*group_id[^>]*>', str((fx.get('group') or {}).get('id', ''))),
        (r'<[^>]*user_id[^>]*>', str(other.get('owner', ''))),
        (r'<[^>]*api_code[^>]*>', 'crf'),
        # ワークフロー(no.601-636)。fixtures.py が作った activity を使う
        (r'<[^>]*activity_id[^>]*>', (fx.get('activity') or {}).get('activity_id', '')),
        (r'<[^>]*action_id[^>]*>', str((fx.get('activity') or {}).get('action_id', ''))),
        (r'<[^>]*workflow_id[^>]*>', str((fx.get('activity') or {}).get('workflow_id', ''))),
        (r'<[^>]*flow_id[^>]*>', str((fx.get('activity') or {}).get('flow_id', ''))),
        # fixtures.py が拾った既存レコードのID
        # 台帳には <int:item_type_id> と <int:ItemTypeID> の両方が現れる。
        # 大小文字は無視して照合するがアンダースコアの有無は吸収できないので両方書く。
        (r'<[^>]*item_?type_?id[^>]*>', ids.get('item_type_id', '')),
        (r'<[^>]*property_id[^>]*>', ids.get('property_id', '')),
        (r'<[^>]*client_id[^>]*>', ids.get('oauth_client_id', '')),
        (r'<[^>]*token_id[^>]*>', ids.get('oauth_token_id', '')),
        (r'<[^>]*mail_id[^>]*>', ids.get('mail_template_id', '')),
        (r'<[^>]*identifier[^>]*>', str(ids.get('author_id', ''))),
        # 定数で決まるもの(値域が有限で、コード/設定から特定できるもの)
        (r'<[^>]*(lang_code|current_language|lang)[^>]*>', 'ja'),
        (r'<int:req>', '1'),
        (r'<[^>]*schema_?name[^>]*>', ids.get('schema_name', 'ddi_mapping')),
        (r'<[^>]*data_type[^>]*>', 'username'),          # views.py:819 username|email
        (r'<[^>]*format[^>]*>', 'bibtex'),               # weko-records-ui/config.py:292
        (r'<[^>]*target_report[^>]*>', '1'),             # invenio-stats TARGET_REPORTS
        (r'<[^>]*ranking_type[^>]*>', 'most_downloaded_items'),  # ranking_settings
        (r'<[^>]*selection[^>]*>', 'target'),
        (r'<int:year>', '2026'), (r'<int:month>', '8'),
        (r'<[^>]*start_date[^>]*>', '2026-01-01'),
        (r'<[^>]*end_date[^>]*>', '2026-12-31'),
        (r'<[^>]*unit[^>]*>', 'Day'),
        (r'<[^>]*event[^>]*>', 'file_download'),
        (r'<[^>]*task_name[^>]*>', 'aggregate'),
        (r'<[^>]*repository_id[^>]*>', str(fx.get('index', ''))),
        (r'<[^>]*record_id[^>]*>', str(priv.get('recid', ''))),
        (r'<string:method>', 'get'),
        (r'<string:value>', ids.get('journal_id', '900001')),
        (r'<[^>]*widget_id[^>]*>', ids.get('widget_id', '')),
        (r'<[^>]*page_id[^>]*>', ids.get('widget_page_id', '')),
        (r'<[^>]*journal_id[^>]*>', ids.get('journal_id', '')),
        # 上記で解決しない汎用ID(facet-search の <int:id> 等)は最後に当てる
        (r'<(int|string):id>', ids.get('facet_search_id', '1')),
        (r'<id>', ids.get('prefix_id', '1')),
        # IIIF Image API のパラメータ(no.34)
        (r'<[^>]*region[^>]*>', 'full'),
        (r'<[^>]*size[^>]*>', 'full'),
        (r'<[^>]*rotation[^>]*>', '0'),
        (r'<[^>]*quality[^>]*>', 'default'),
        (r'<[^>]*image_format[^>]*>', 'png'),
    ]
    return table


PID_PAT = r'<[^>]*(pid_value|recid|pid\()[^>]*>'
ACT_PAT = r'<[^>]*activity_id[^>]*>'


def resolve_variants(uri, table, fx):
    """(ラベル, 解決後パス) の一覧を返す。

    アイテムIDのプレースホルダは **公開/非公開の両方**で測る。どちらを入れるかで
    結論が変わるため。例: no.480 /record/<pid>/publish は非公開アイテムだと
    未認証でログインへ転送されるが、公開アイテムだと未認証で publish_status が
    書き換わることを実証済み。片方だけでは取りこぼす。
    """
    import re
    ver = 'v2' if '/iiif/' in uri else 'v1'   # <version> は文脈依存
    base = uri
    for pat, val in table:
        if val == '__VERSION__':
            val = ver
        if not val:
            continue
        # 台帳には <int:item_type_id> と <int:ItemTypeID> の両方が現れるため
        # 大小文字を無視して照合する
        base = re.sub(pat, val, base, flags=re.I)

    # activity は「自分所有」と「他人所有」の両方で測る(所有者チェックの検証)
    if re.search(ACT_PAT, uri):
        out = []
        for label, key in (('own', 'activity'), ('other', 'activity_other')):
            a = fx.get(key) or {}
            if not a.get('activity_id'):
                continue
            u = re.sub(ACT_PAT, a['activity_id'], uri)
            for pat, val in table:
                if val == '__VERSION__':
                    val = ver
                if not val or pat == ACT_PAT:
                    continue
                u = re.sub(pat, val, u, flags=re.I)
            out.append((f'activity:{label}', u))
        if out:
            return out

    if not re.search(PID_PAT, uri):
        return [('-', base)]
    out = []
    for label in ('public', 'private'):
        rec = fx['records'].get(label)
        if not rec:
            continue
        out.append((label, re.sub(PID_PAT, str(rec['recid']), uri if False else base)))
    # base は既に private で置換済みなので、公開版は uri から作り直す
    fixed = []
    for label, _ in out:
        rec = fx['records'][label]
        u = re.sub(PID_PAT, str(rec['recid']), uri)
        for pat, val in table:
            if val == '__VERSION__':
                val = ver
            if not val or pat == PID_PAT:
                continue
            u = re.sub(pat, val, u, flags=re.I)
        fixed.append((label, u))
    return fixed or [('-', base)]


def load_tsv(path):
    rows = {}
    with open(path, encoding='utf-8') as f:
        hdr = f.readline().rstrip('\n').split('\t')
        H = {n: i for i, n in enumerate(hdr)}
        for line in f:
            c = line.rstrip('\n').split('\t')
            if len(c) > H['uri']:
                rows[c[H['no']]] = c
    return rows, H


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(here)
    p = argparse.ArgumentParser(description='フィクスチャ駆動の到達可否測定')
    p.add_argument('--fixtures', default='fixtures.json')
    p.add_argument('--tsv', default=None, help='既定: $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv')
    p.add_argument('--only', help='測定対象の no を1行1件で並べたファイル')
    p.add_argument('--nos', help='測定対象の no をカンマ区切りで直接指定')
    p.add_argument('--base', default='https://localhost:8443')
    p.add_argument('--host', default='weko3.example.org')
    p.add_argument('--allow-writes', action='store_true',
                   help='GET/HEAD 以外も測る(使い捨て環境でのみ指定すること)')
    p.add_argument('--out', default='probe.json')
    p.add_argument('--gate', action='store_true', help='G8/G9 に該当があれば exit 1')
    p.add_argument('--summary-only', action='store_true',
                   help='件数のみ出力する。public リポジトリの CI ログ/artifact/PRコメントは'
                        '誰でも読めるため、URI や測定結果の明細を出さない')
    a = p.parse_args()
    a.tsv = a.tsv or data_path('weko3_api_list_full.tsv')

    fx = json.load(open(a.fixtures, encoding='utf-8'))
    rows, H = load_tsv(a.tsv)

    targets = []
    if a.only and os.path.isfile(a.only):
        targets += [l.strip() for l in open(a.only, encoding='utf-8') if l.strip()]
    if a.nos:
        targets += [x.strip() for x in a.nos.split(',') if x.strip()]
    targets = [t for t in dict.fromkeys(targets) if t in rows]
    if not targets:
        print('測定対象がありません(--only / --nos)。')
        json.dump({'results': [], 'skipped': 'no targets'},
                  open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        return

    work = tempfile.mkdtemp(prefix='api-probe-')
    sessions = {}
    for name, email in IDENTITIES:
        s = Session(a.base, a.host, email, fx['password'], work)
        if email and not s.ok:
            print(f'  警告: {name} ({email}) のログインに失敗。この identity は測れません。')
        sessions[name] = s

    table = build_resolver(fx)
    results = []
    for no in targets:
        c = rows[no]
        uri, methods = c[H['uri']], c[H['method']]
        for label, path in resolve_variants(uri.split(';')[0], table, fx):
            if '<' in path:
                results.append({'no': no, 'uri': uri, 'status': 'skip',
                                'reason': '未解決プレースホルダ: ' + path})
                continue
            for method in [m for m in methods.replace(' ', '').split(',') if m]:
                if method not in SAFE_METHODS and not a.allow_writes:
                    results.append({'no': no, 'uri': uri, 'method': method,
                                    'status': 'skip',
                                    'reason': '書き込み系(--allow-writes 未指定)'})
                    continue
                obs = {}
                for name, _ in IDENTITIES:
                    sess = sessions[name]
                    if sess.email and not sess.ok:
                        continue
                    bf = os.path.join(work, 'body')
                    code, redirect, orig = sess.request(method, path, bf)
                    v = classify(code, bf, redirect)
                    if orig in REDIRECT_CODES and v == '到達':
                        # 転送を追った先が 200 でも、「拒否して一覧へ戻す」転送の
                        # ことがある(実測: 非所有者のグループ削除)。到達とは
                        # 断定できないので、行き先を添えて人が判断できるようにする。
                        v = '到達(転送)'
                    obs[name] = {'code': code, 'via': orig if orig != code else None,
                                 'verdict': v,
                                 'redirect': redirect or None}
                results.append({'no': no, 'uri': uri, 'method': method,
                                'target': label, 'resolved': path,
                                'status': 'measured',
                                'data_op': c[H['data_op']], 'observed': obs,
                                'recorded': c[H['dynamic_verified']]})

    # --- ゲート ---
    g8, g9 = [], []
    for r in results:
        if r.get('status') != 'measured':
            continue
        anon = (r['observed'].get('anon') or {}).get('verdict')
        if anon == '到達':
            if any(k in r['data_op'] for k in ('作成', '更新', '削除')):
                g8.append(r)
            if '遮断' in (r['recorded'] or '') and '到達' not in (r['recorded'] or ''):
                g9.append(r)

    out = {'targets': len(targets), 'results': results,
           'gates': {'G8_unauth_write': g8, 'G9_regression': g9}}
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    measured = [r for r in results if r.get('status') == 'measured']
    skipped = [r for r in results if r.get('status') == 'skip']
    print(f"\n測定 {len(measured)} / スキップ {len(skipped)} (対象 no {len(targets)}件)")
    if a.summary_only:
        print('  (件数のみ。明細は秘密側の完全版レポートを参照)')
        print(f"\n[G8] 未認証で到達する書き込み系: {len(g8)}件")
        print(f"[G9] 台帳では遮断だが実測で到達(回帰): {len(g9)}件")
        if a.gate and (g8 or g9):
            sys.exit(1)
        return
    for r in measured:
        obs = ' '.join(f"{k}={v['code']}({v['verdict']})" for k, v in r['observed'].items())
        tgt = f"[{r.get('target', '-')}]"
        print(f"  no={r['no']:<5} {r['method']:<7} {tgt:<10} {r['uri'][:44]:<44} {obs}")
    for r in skipped:
        print(f"  no={r['no']:<5} skip: {r['reason']}")
    if g8:
        print(f"\n[FAIL] G8 未認証で到達する書き込み系: {len(g8)}件")
        for r in g8:
            print(f"  no={r['no']} {r['method']} [{r.get('target','-')}] "
                  f"{r['uri'][:60]} data_op={r['data_op']}")
    if g9:
        print(f"\n[FAIL] G9 台帳では遮断だが実測で到達(回帰): {len(g9)}件")
        for r in g9:
            print(f"  no={r['no']} {r['method']} [{r.get('target','-')}] {r['uri'][:60]}")
    if a.gate and (g8 or g9):
        sys.exit(1)


if __name__ == '__main__':
    main()
