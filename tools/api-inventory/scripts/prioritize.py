# -*- coding: utf-8 -*-
"""台帳に対応優先度(priority / priority_reason)を付与する。

    python3 prioritize.py            # $WEKO_API_INVENTORY_DIR の台帳を更新

判定基準(classify が上から順に評価し、最初に合致したものを採用する):

  「無認証」は auth_required が 不要/任意(匿名可)、または実測で未認証のまま到達
  したこと。ただし infra_auth がアプリの外側の認証(OAuth2 クライアント認証・
  nginx・Shibboleth SP)を、credential_auth がビュー内の本人認証(パスワード・
  トークンの検証)を見つけた行は、auth_required が 不要 でも無認証としない。
  ビュー内の本人認証がある行は、実測の「未認証で到達」も★実証が無ければ数えない
  (ログイン等は未認証のリクエストがビューまで届くのが正常なため)。
  「書き込み系」は method に POST/PUT/DELETE/PATCH を含むこと。
  「新規作成のみ」は data_op に 作成 を含み 更新/削除 を含まないこと。
  「永続データを変更」は data_store にデータベース(PostgreSQL)かファイルストレージ
  があり、data_op に 作成/更新/削除 を含むこと。セッション・Redis・ES・
  外部サービスだけを書き換えるものは含めない。

  P1            (1) 無認証で、data_store がファイル実体かつ data_op が更新/削除
                (2) 書き込み系・無認証で、永続データを変更し、新規作成のみではない
                (3) 書き込み系で指摘に「実効せず」があり、永続データを変更し、
                    新規作成のみではない
                ※ POST で受けるだけの取得(ログイン・検索・エクスポート等)や
                  セッションだけを変えるもの(言語切替等)は P1 にならない
  P2            書き込み系で、無認証/「実効せず」だが新規作成のみ、
                ゲストトークンのバイパス経路がある、ログインのみで到達するか
                所有者/ロールの限定が欠けている、または到達可否が未測定。
                読み取り系でも、認可が緩く(無認証・ログインのみ・スコープ欠落)
                指摘か★実証があり、露出内容が認証情報または非公開データの実体のもの
  対象外        auth が admin-role-table/admin-access 相当または auth_required が
                要(管理)で、指摘も★実証も無い
  P4            意図的な公開設計(static配信・ヘルスチェック・robots.txt・OAI-PMH等)、
                または deny_all 常時拒否
  P3            読み取り系で、無認証、またはログインのみ/スコープ欠落の指摘がある、
                または指摘があるが到達可否が未測定
  P5            デコレータ以外の仕組みで認証している(infra_auth/credential_auth)、
                具体的な権限/所有者チェック機構がある、または auth_required が 要 で
                破綻が見えない
  P3            上のいずれにも合致しない(手動確認が必要)

  P1/P2 は対象外・P4 より先に評価する。管理画面や公開設計のエンドポイントでも、
  P1/P2 の条件に合えばそちらが優先される。

テスト観点による引き上げ(bump、対象外/P4/P5 にのみ適用):
  test_gap が「特定不能」、または 正常値/異常値/境界値/例外処理 の4観点が
  全て欠けている行は P3 に上げる。一部の欠落なら優先度は変えず理由に追記する。

classify の後に decide が次を重ねる(いずれも P1/P2 の行は優先度を変えない):
  環境依存      実機の url_map に存在しない(プラグイン未導入・config で無効・動的登録)
  整理対象      非利用(未使用/非推奨/実質未使用/呼出元なし/経路なし)
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402
import credential_auth  # noqa: E402
import infra_auth  # noqa: E402

WRITE_METHODS = {'POST', 'PUT', 'DELETE', 'PATCH'}

# data_store の保存先の種別がデータベース/ファイルストレージであるもの。
# data_store は「対象 / 種別:詳細; 種別:詳細」の形なので、区切りの直後に
# 種別として現れたものだけを拾う(「ファイルダウンロード統計」や
# 「認証情報ファイル:」のような対象名・修飾語には反応させない)。
PERSISTENT_STORE_RE = re.compile(
    r'(?:^|[/;；→])\s*(?:PostgreSQL|ファイル)(?=[:：(]|\s*(?:[/;；→]|$))')

# 露出内容が「認証情報」とみなせる語
CREDENTIAL_WORDS = (
    '露出:秘密情報', '秘密:', 'client_secret', 'access_token', 'refresh_token',
    'password', 'cert_data', '資格情報', '外部トークン', 'APIキー', 'api_key',
)
# 露出内容が「非公開データの実体」とみなせる語
NONPUBLIC_BODY_WORDS = (
    '非公開業務データ', '非公開アイテム', 'ファイル実体', '非公開含む',
    '全レコードJSON', '本文取得',
)

# 意図的な公開設計とみなす URI パターン
PUBLIC_BY_DESIGN = [
    (r'^/(api/)?ping$', 'ヘルスチェック'),
    (r'robots\.txt', 'robots.txt'),
    (r'/sitemap', 'サイトマップ配信'),
    (r'^/(api/)?oai', 'OAI-PMH'),
    (r'/resync/', 'ResourceSync'),
    (r'^/(api/)?schema/', 'JSONスキーマ配信'),
    (r'^/(api/)?lang', '言語切替'),
    (r'/static/', '静的ファイル配信'),
    (r'^/api/csl/styles$', 'CSLスタイル一覧'),
    (r'^/$', 'トップページ'),
]

def load_allow():
    """reconcile_allow.json を「実機に無い」ことの一次情報として読む。

    実測欄(dynamic_verified)の粒度はばらついており、同じ機能群でも
    「経路なし」と書かれた行と空欄の行が混在する。それを判定に使うと
    同一グループが 整理対象 と 対象外 に割れる。突き合わせで確認済みの
    allow リストを正とする。
    """
    p = data_path('reconcile_allow.json', required=False)
    if not p or not os.path.isfile(p):
        return set(), set()
    try:
        a = json.load(open(p, encoding='utf-8'))
    except Exception:
        return set(), set()
    return set(a.get('not_registered', {})), set(a.get('not_a_route', []))


def norm_uri(u):
    u = u.strip()
    return u[:-1] if len(u) > 1 and u.endswith('/') else u


# 「非利用」とみなす根拠。deprecated 列の記述と、実機 url_map に無いこと。
UNUSED_WORDS = ('未使用', '非推奨', '実質未使用', '呼出元なし', '経路なし')

# 具体的な権限/所有者チェック機構(P4 の根拠)
CONCRETE_AUTHZ = [
    'page_permission_factory', 'check_created_id', 'roles_required',
    'permission.require', 'action-need', 'need_record_permission',
    'require_api_auth', 'require_oauth_scopes', 'admin-role-table',
    'file_permission_factory', 'check_index_access',
]


HISTORY_SEP = ' \u2016 \u65e7: '   # apply_probe_results.py --keep-history が付ける区切り


def field(cols, H, name):
    i = H.get(name)
    v = cols[i] if i is not None and len(cols) > i else ''
    if name == 'dynamic_verified' and HISTORY_SEP in v:
        # 旧測定の記述(★実証 など)を現在値として読まないよう切り落とす
        v = v.split(HISTORY_SEP)[0]
    return v


def classify(c, H):
    """(priority, reason, cleanup) を返す。

    cleanup は「非利用につき整理対象」の根拠。非利用の行は、認可上の問題が
    P3 以下なら **削除すれば済む** ので `整理対象` に置き換える。P1/P2 の行は
    優先度を落とさず、理由に「削除が最短の対応」であることを添える。
    """
    method = field(c, H, 'method').upper()
    uri = field(c, H, 'uri')
    auth = field(c, H, 'auth') or (field(c, H, 'auth_required') + ' | ' +
                                   field(c, H, 'auth_method'))
    data_op = field(c, H, 'data_op')
    finding = field(c, H, 'security_finding') or field(c, H, 'sec_pattern')
    dyn = field(c, H, 'dynamic_verified')
    cfg = field(c, H, 'config_deps')
    # full.tsv は data_target(操作対象) と data_store(保存先) が別列、
    # 24列版は両者を結合した data_store 1列。どちらでも拾えるよう連結する。
    # data_target と data_store は access_variance と同様に1列へ統合済み
    store = field(c, H, 'data_store')

    gap = field(c, H, 'test_gap')
    dep = field(c, H, 'deprecated')
    unused_src = ''
    if dep and dep != '-' and any(w in dep for w in UNUSED_WORDS):
        unused_src = dep
    elif '経路なし' in dyn:
        unused_src = '経路なし(実機 url_map に未登録)'

    def bump(pri, why):
        """テスト観点が確認できない行を P3 まで引き上げる。

        認可上の問題が無くても「4観点のチェックが確認できない」なら確認対象に
        上げる。ただし認可の欠陥と同列にはしないため **上限は P3**。
        """
        if not gap or gap == '-':
            return pri, why
        if gap == '特定不能':
            return 'P3', f'{why} / 対応するテスト関数を特定できずテスト観点を確認できない'
        if gap.count(',') == 3:
            return 'P3', f'{why} / テストの4観点(正常値・異常値・境界値・例外処理)が全て確認できない'
        return pri, f'{why} / テスト観点の欠落: {gap}'

    methods = {m.strip() for m in method.split(',') if m.strip()}
    auth_req = auth.split('|')[0].strip()

    is_write_method = bool(methods & WRITE_METHODS)
    is_destructive = ('削除' in data_op)
    # 永続データ(データベース/ファイルストレージ)を作成・更新・削除するか。
    # セッション・Redis・ES・外部サービスだけを書き換えるもの(言語切替・CAPTCHA・
    # 統計・Handle 等)は含めない。保存先が書かれていない行(data_store が '-')も同様。
    persists = bool(PERSISTENT_STORE_RE.search(store))
    is_mutating = persists and any(k in data_op for k in ('作成', '更新', '削除'))
    no_auth = auth_req in ('不要', '任意(匿名可)')
    # アプリの外側(OAuth2 プロバイダ・nginx・Shibboleth SP)で行う認証と、
    # ビューの中で行う本人認証(パスワード・トークンの検証)。
    # デコレータに現れないので auth_required は「不要」になっているが、無認証ではない。
    impl_file, impl_line = field(c, H, 'impl_file'), field(c, H, 'impl_line')
    infra = infra_auth.detect(
        [u.strip() for u in uri.split(';')], sorted(methods), impl_file, impl_line)
    cred = '' if infra else credential_auth.credential_auth(
        impl_file, impl_line, field(c, H, 'endpoint'))
    if infra or cred:
        no_auth = False
    unauth_reach = ('未認証で到達' in dyn) or ('未認証で' in dyn and '★' in dyn)
    proven = '★' in dyn
    # ビューで本人認証をするもの(ログイン等)は、未認証のリクエストがビューまで
    # 届くのが正常な動き。届いただけでは認証の欠落とみなさず、★実証(突破)が
    # あるときだけ残す。
    if cred and not proven:
        unauth_reach = False
    broken_authz = '実効せず' in finding
    login_only = ('ログインのみで到達' in dyn) or ('低権限ログインで到達' in dyn)
    scope_missing = any(k in finding for k in (
        '所有者チェック欠落', '権限過小', '兄弟と不揃い', '読み書き非対称'))
    guest_bypass = 'session+guest' in auth or 'guest_token' in finding
    unknown = (dyn.strip() in ('', '-'))
    has_finding = finding.strip() not in ('', '-')

    # --- P1: 無認証で既存のファイル実体を壊せる(データ破壊) ---
    # 「データ破壊」= 既存の実データを不可逆に壊すこと。メタデータの更新や
    # 新規作成は含めない。この定義で 926 行中 no.503(POST /records/replace_file)
    # だけが該当する。
    destroys_real_data = ('ファイル実体' in store) and ('更新' in data_op or '削除' in data_op)
    if (no_auth or unauth_reach) and destroys_real_data:
        return 'P1', f'無認証で既存のファイル実体を上書き/削除できる (data_op={data_op})'

    # --- P1: 状態変更系で認証・権限が無い/機能していない ---
    # 永続データを作成・更新・削除するものに限る。POST で受けるだけの取得や、
    # セッションだけを変えるものは P1 にしない。
    # ただし新規作成しかせず既存データを壊さないものは P2 に下げる(下の P2 で拾う)。
    creates_only = ('作成' in data_op) and not ('更新' in data_op or '削除' in data_op)
    if is_write_method and is_mutating and (no_auth or unauth_reach) \
            and not creates_only:
        why = '認証チェックが無い' if no_auth else '認証はあるが未認証で到達(実測)'
        return 'P1', f'状態変更系({method})で{why}'
    if is_write_method and is_mutating and broken_authz and not creates_only:
        return 'P1', f'状態変更系({method})だが権限チェックが実装上機能していない'

    # --- P2 ---
    # 認証が無い状態変更系でも、新規作成のみで既存データを壊さないものはここ。
    if is_write_method and (no_auth or unauth_reach or broken_authz) and creates_only:
        return 'P2', f'状態変更系({method})で認証チェックが無いが、新規作成のみで既存データは壊さない'
    if is_write_method and guest_bypass:
        return 'P2', f'状態変更系({method})にゲストトークンのバイパス経路がある'
    if is_write_method and (login_only or scope_missing):
        why = 'ログイン必須のみで所有者/ロール限定なし(IDOR疑い)' if login_only \
            else finding.split(';')[0].strip()[:60]
        return 'P2', f'状態変更系({method}): {why}'
    if is_write_method and unknown:
        return 'P2', f'状態変更系({method})だが到達可否が未測定(不明)'

    # --- 露出内容による引き上げ(参照系でも P2) ---
    # 「読み取り系だから情報漏洩リスクは限定的」は、露出するものが認証情報や
    # 非公開データの実体である場合には成り立たない。認可が緩い行に限って P2 に上げる。
    # 「管理者に集約」のように適切に保護されている行は対象にしない。
    # restricted_content / access_variance は「何が制限されているか」の説明であり、
    # 適切に絞られている旨の記述にも「非公開」が出てくる。露出の根拠には使わない
    # (例: no.575 GET / は「ブラウジング権限のあるインデックスのみ」と書かれており
    #  指摘も無いのに、これを拾うと P1 に誤って上がる)。
    exposure = ' '.join((finding, field(c, H, 'sec_exposed'),
                         field(c, H, 'sec_detail')))
    # 指摘または★実証がある行に限る。露出の記述があるだけでは上げない。
    weak_access = (no_auth or unauth_reach or login_only or scope_missing) \
        and (has_finding or proven)
    if (not is_write_method) and weak_access:
        cred = [w for w in CREDENTIAL_WORDS if w in exposure]
        body = [w for w in NONPUBLIC_BODY_WORDS if w in exposure or w in store]
        if cred:
            return 'P2', f'参照系だが露出内容が認証情報({cred[0]})で、認可が緩い'
        if body:
            return 'P2', f'参照系だが露出内容が非公開データの実体({body[0]})で、認可が緩い'

    # --- 対象外: admin-access 相当で保護され、指摘も実証も無い ---
    if (not has_finding) and (not proven) and (
            'admin-role-table' in auth or 'admin-access' in auth
            or auth_req == '要(管理)'):
        return bump('対象外', '認証必須+admin-access 相当の権限チェックあり、指摘なし')

    # --- P4: 意図的な公開設計 / deny_all ---
    for pat, label in PUBLIC_BY_DESIGN:
        if re.search(pat, uri):
            return bump('P4', f'意図的な公開設計({label})')
    if 'deny_all' in auth or 'deny_all' in cfg:
        return bump('P4', 'deny_all で常時拒否(逆方向の問題)')

    # --- P3: 読み取り系 ---
    if not is_write_method:
        if no_auth or unauth_reach:
            return 'P3', f'読み取り系({method})で認証・権限チェックが無い'
        if login_only or scope_missing:
            why = 'ログイン必須のみでロール/所有者スコープなし' if login_only \
                else finding.split(';')[0].strip()[:60]
            return 'P3', f'読み取り系({method}): {why}'
        if unknown and has_finding:
            return 'P3', f'読み取り系({method})に指摘があるが到達可否は未測定'

    # --- P5 ---
    if infra or cred:
        return bump('P5', f'デコレータ以外の仕組みで認証している({infra or cred})')
    hit = [k for k in CONCRETE_AUTHZ if k in auth]
    if hit:
        return bump('P5', f'具体的な権限チェック機構あり({", ".join(hit[:3])})')
    if auth_req.startswith('要'):
        return bump('P5', f'認証必須({auth_req})で破綻は見えない')
    return 'P3', '分類条件に合致せず。手動確認が必要'


def decide(c, H, allow=(frozenset(), frozenset())):
    """classify の結果に「実機に無い」「非利用」の判定を重ねる。"""
    pri, why = classify(c, H)
    not_registered, not_a_route = allow

    # --- 実機に無い(環境依存で無効) ---
    # 削除候補ではない。別の設定・別サイトでは有効になるため台帳に残す。
    uris = [norm_uri(x) for x in field(c, H, 'uri').split(';') if norm_uri(x)]
    hit = [u for u in uris if u in not_registered]
    if hit or field(c, H, 'no') in not_a_route:
        src = ('起動後に動的登録されるためURIが静的に定まらない'
               if not hit else 'この環境では未登録(プラグイン未導入・config で無効等)')
        if pri in ('P1', 'P1', 'P2'):
            return pri, f'{why} / 実機に無い({src})が、有効な環境では成立しうる', '-'
        return '環境依存', f'実機に無い: {src} / 認可上の判定は {pri}', '-'

    dep = field(c, H, 'deprecated')
    dyn = field(c, H, 'dynamic_verified')
    src = ''
    if dep and dep != '-' and any(w in dep for w in UNUSED_WORDS):
        src = dep
    elif '経路なし' in dyn:
        src = '経路なし(実機 url_map に未登録)'
    if not src:
        return pri, why, '-'
    if pri in ('P1', 'P1', 'P2'):
        return pri, f'{why} / 非利用({src[:40]})のため削除が最短の対応', src
    return '整理対象', f'非利用({src[:60]}) / 認可上の判定は {pri}', src


TAIL = ['priority', 'priority_reason', 'test_normal', 'test_abnormal',
        'test_boundary', 'test_exception', 'test_gap', 'cleanup']


def apply_to(path, out=None):
    with open(path, encoding='utf-8') as f:
        lines = f.read().rstrip('\n').split('\n')
    hdr = lines[0].split('\t')
    H0 = {n: i for i, n in enumerate(hdr)}
    rows = [r.split('\t') for r in lines[1:]]

    # 既存の派生列を一旦外し、本体列だけにする
    base_idx = [i for i, n in enumerate(hdr) if n not in ('priority', 'priority_reason', 'cleanup')]
    base_hdr = [hdr[i] for i in base_idx]

    allow = load_allow()
    out_rows = []
    counts = {}
    cleanup_n = 0
    for c in rows:
        c = c + [''] * (len(hdr) - len(c))
        pri, why, cl = decide(c, H0, allow)
        counts[pri] = counts.get(pri, 0) + 1
        if cl != '-':
            cleanup_n += 1
        base = [c[i] for i in base_idx]
        out_rows.append((base, pri, why.replace('\t', ' '), cl.replace('\t', ' ')))

    # 末尾の並びを実行順に依存させない(canonical order に揃える)
    tail_present = [n for n in TAIL if n in base_hdr or n in ('priority', 'priority_reason', 'cleanup')]
    body_hdr = [n for n in base_hdr if n not in TAIL]
    tail_hdr = ['priority', 'priority_reason'] + \
               [n for n in ('test_normal', 'test_abnormal', 'test_boundary',
                            'test_exception', 'test_gap') if n in base_hdr] + ['cleanup']
    bi = {n: i for i, n in enumerate(base_hdr)}
    final = ['\t'.join(body_hdr + tail_hdr)]
    for base, pri, why, cl in out_rows:
        vals = {**{n: base[bi[n]] for n in body_hdr},
                'priority': pri, 'priority_reason': why, 'cleanup': cl}
        for n in ('test_normal', 'test_abnormal', 'test_boundary',
                  'test_exception', 'test_gap'):
            if n in bi:
                vals[n] = base[bi[n]]
        final.append('\t'.join(vals[n] for n in body_hdr + tail_hdr))
    with open(out or path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final) + '\n')
    counts['__cleanup__'] = cleanup_n
    return counts


ORDER = ['P1', 'P2', 'P3', 'P4', 'P5', '整理対象', '環境依存', '対象外']


def main():
    p = argparse.ArgumentParser(description='台帳に対応優先度を付与する')
    p.add_argument('--full', default=None, help='既定: $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv')
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    full = a.full or data_path('weko3_api_list_full.tsv')

    import tempfile
    tmp = tempfile.mktemp(suffix='.tsv') if a.dry_run else None
    counts = apply_to(full, out=tmp)
    cleanup_n = counts.pop('__cleanup__', 0)
    total = sum(counts.values())
    print(f'{"(dry-run) " if a.dry_run else ""}{full}: {total} 行に priority を付与')
    for k in ORDER:
        if counts.get(k):
            print(f'  {k:<14} {counts[k]:>4}')
    for k in sorted(set(counts) - set(ORDER)):
        print(f'  {k:<14} {counts[k]:>4}  ← 未定義の区分')
    print(f'  (うち非利用と判定: {cleanup_n} 行)')
    if tmp:
        os.unlink(tmp)


if __name__ == '__main__':
    main()
