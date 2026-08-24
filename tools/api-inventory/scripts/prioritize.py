# -*- coding: utf-8 -*-
"""台帳に対応優先度(priority / priority_reason)を付与する。

    python3 prioritize.py            # $WEKO_API_INVENTORY_DIR の台帳を更新

判定基準(上から順に評価し、最初に合致したものを採用する):

  P0(至急)      無認証で **既存のファイル実体** を上書き/削除できる
                (「データ破壊」を「既存の実データを不可逆に壊すこと」と定義する。
                 メタデータの更新や新規作成は破壊に含めない)
  P0(最優先)    状態変更系(POST/PUT/DELETE/PATCH)なのに認証・権限チェックが一切ない、
                または権限チェック機構はあるように見えるが実装上機能していない
  P1(高)        ログイン必須のみで所有者/ロール/スコープの限定がない状態変更系(IDOR疑い)、
                ゲストトークン等のバイパス、ロールチェックが実質不問、または「不明」。
                加えて、認証が無い状態変更系でも **新規作成のみで既存データを
                壊さない** ものはここに下げる
  対象外        認証必須かつ admin-access 相当の権限チェックがあり、指摘が無いもの
  P3(低)        意図的な公開設計(static配信・ヘルスチェック・robots.txt・OAI-PMH等)、
                または deny_all 常時拒否
  P2(中)        読み取り系(GET/HEAD)で認証・権限チェックが無い、または
                ログイン必須のみでロール/所有者スコープなし
  P4(低・実装済) 具体的な権限/所有者チェック機構が明記されており破綻が見えない

テスト観点による引き上げ(上限 P2):
  正常値/異常値/境界値/例外処理 のチェックが確認できない行は、認可上の問題が
  無くても確認対象に上げる。ただし **引き上げは P2 まで** とする(認可の欠陥と
  同列には扱わない)。既に P0/P1/P2 の行は変更しない。

評価順について: 「対象外」と P3 は P2 より先に評価する。admin-access で保護された
管理画面や、意図的に公開している OAI-PMH を「認証なしの読み取り系」として
P2 に落とすと、実際に見るべき行が埋もれるため。ただし **指摘(security_finding)や
★実証がある行は「対象外」にしない**(保護されているように見えて破綻している行を
除外してしまうため)。
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path  # noqa: E402

WRITE_METHODS = {'POST', 'PUT', 'DELETE', 'PATCH'}

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

# 具体的な権限/所有者チェック機構(P4 の根拠)
CONCRETE_AUTHZ = [
    'page_permission_factory', 'check_created_id', 'roles_required',
    'permission.require', 'action-need', 'need_record_permission',
    'require_api_auth', 'require_oauth_scopes', 'admin-role-table',
    'file_permission_factory', 'check_index_access',
]


def field(cols, H, name):
    i = H.get(name)
    return cols[i] if i is not None and len(cols) > i else ''


def classify(c, H):
    """(priority, reason) を返す。"""
    method = field(c, H, 'method').upper()
    uri = field(c, H, 'uri')
    auth = field(c, H, 'auth') or (field(c, H, 'auth_required') + ' | ' +
                                   field(c, H, 'auth_method'))
    data_op = field(c, H, 'data_op') or field(c, H, 'data_op_detail')
    finding = field(c, H, 'security_finding') or field(c, H, 'sec_pattern')
    dyn = field(c, H, 'dynamic_verified')
    cfg = field(c, H, 'config_deps')
    # full.tsv は data_target(操作対象) と data_store(保存先) が別列、
    # 24列版は両者を結合した data_store 1列。どちらでも拾えるよう連結する。
    store = ' '.join(x for x in (field(c, H, 'data_target'),
                                 field(c, H, 'data_store')) if x)

    gap = field(c, H, 'test_gap')

    def bump(pri, why):
        """テスト観点が確認できない行を P2 まで引き上げる。

        認可上の問題が無くても「4観点のチェックが確認できない」なら確認対象に
        上げる。ただし認可の欠陥と同列にはしないため **上限は P2**。
        """
        if not gap or gap == '-':
            return pri, why
        if gap == '特定不能':
            return 'P2(中)', f'{why} / 対応するテスト関数を特定できずテスト観点を確認できない'
        if gap.count(',') == 3:
            return 'P2(中)', f'{why} / テストの4観点(正常値・異常値・境界値・例外処理)が全て確認できない'
        return pri, f'{why} / テスト観点の欠落: {gap}'

    methods = {m.strip() for m in method.split(',') if m.strip()}
    auth_req = auth.split('|')[0].strip()

    is_write_method = bool(methods & WRITE_METHODS)
    is_destructive = ('削除' in data_op)
    is_mutating = any(k in data_op for k in ('作成', '更新', '削除'))
    no_auth = auth_req in ('不要', '任意(匿名可)')
    unauth_reach = ('未認証で到達' in dyn) or ('未認証で' in dyn and '★' in dyn)
    proven = '★' in dyn
    broken_authz = '実効せず' in finding
    login_only = ('ログインのみで到達' in dyn) or ('低権限ログインで到達' in dyn)
    scope_missing = any(k in finding for k in (
        '所有者チェック欠落', '権限過小', '兄弟と不揃い', '読み書き非対称'))
    guest_bypass = 'session+guest' in auth or 'guest_token' in finding
    unknown = (dyn.strip() in ('', '-'))
    has_finding = finding.strip() not in ('', '-')

    # --- P0(至急) 無認証で既存のファイル実体を壊せる ---
    # 「データ破壊」= 既存の実データを不可逆に壊すこと。メタデータの更新や
    # 新規作成は含めない。この定義で 926 行中 no.503(POST /records/replace_file)
    # だけが該当する。
    destroys_real_data = ('ファイル実体' in store) and ('更新' in data_op or '削除' in data_op)
    if (no_auth or unauth_reach) and destroys_real_data:
        return 'P0(至急)', f'無認証で既存のファイル実体を上書き/削除できる (data_op={data_op})'

    # --- P0(最優先) 状態変更系で認証・権限が無い/機能していない ---
    # ただし新規作成しかせず既存データを壊さないものは P1 に下げる(下の P1 で拾う)。
    creates_only = ('作成' in data_op) and not ('更新' in data_op or '削除' in data_op)
    if is_write_method and (no_auth or unauth_reach) and not creates_only:
        why = '認証チェックが無い' if no_auth else '認証はあるが未認証で到達(実測)'
        return 'P0(最優先)', f'状態変更系({method})で{why}'
    if is_write_method and broken_authz and not creates_only:
        return 'P0(最優先)', f'状態変更系({method})だが権限チェックが実装上機能していない'

    # --- P1(高) ---
    # 認証が無い状態変更系でも、新規作成のみで既存データを壊さないものはここ。
    if is_write_method and (no_auth or unauth_reach or broken_authz) and creates_only:
        return 'P1(高)', f'状態変更系({method})で認証チェックが無いが、新規作成のみで既存データは壊さない'
    if is_write_method and guest_bypass:
        return 'P1(高)', f'状態変更系({method})にゲストトークンのバイパス経路がある'
    if is_write_method and (login_only or scope_missing):
        why = 'ログイン必須のみで所有者/ロール限定なし(IDOR疑い)' if login_only \
            else finding.split(';')[0].strip()[:60]
        return 'P1(高)', f'状態変更系({method}): {why}'
    if is_write_method and unknown:
        return 'P1(高)', f'状態変更系({method})だが到達可否が未測定(不明)'

    # --- 対象外: admin-access 相当で保護され、指摘も実証も無い ---
    if (not has_finding) and (not proven) and (
            'admin-role-table' in auth or 'admin-access' in auth
            or auth_req == '要(管理)'):
        return bump('対象外', '認証必須+admin-access 相当の権限チェックあり、指摘なし')

    # --- P3(低) 意図的な公開設計 / deny_all ---
    for pat, label in PUBLIC_BY_DESIGN:
        if re.search(pat, uri):
            return bump('P3(低)', f'意図的な公開設計({label})')
    if 'deny_all' in auth or 'deny_all' in cfg:
        return bump('P3(低)', 'deny_all で常時拒否(逆方向の問題)')

    # --- P2(中) 読み取り系 ---
    if not is_write_method:
        if no_auth or unauth_reach:
            return 'P2(中)', f'読み取り系({method})で認証・権限チェックが無い'
        if login_only or scope_missing:
            why = 'ログイン必須のみでロール/所有者スコープなし' if login_only \
                else finding.split(';')[0].strip()[:60]
            return 'P2(中)', f'読み取り系({method}): {why}'
        if unknown and has_finding:
            return 'P2(中)', f'読み取り系({method})に指摘があるが到達可否は未測定'

    # --- P4(低・実装済) ---
    hit = [k for k in CONCRETE_AUTHZ if k in auth]
    if hit:
        return bump('P4(低・実装済)', f'具体的な権限チェック機構あり({", ".join(hit[:3])})')
    if auth_req.startswith('要'):
        return bump('P4(低・実装済)', f'認証必須({auth_req})で破綻は見えない')
    return 'P2(中)', '分類条件に合致せず。手動確認が必要'


def apply_to(path, out=None):
    with open(path, encoding='utf-8') as f:
        lines = f.read().rstrip('\n').split('\n')
    hdr = lines[0].split('\t')
    H = {n: i for i, n in enumerate(hdr)}
    if 'priority' in H:                      # 再実行時は既存列を作り直す
        keep = [i for i, n in enumerate(hdr) if n not in ('priority', 'priority_reason')]
        hdr = [hdr[i] for i in keep]
        lines = [ '\t'.join(hdr) ] + [
            '\t'.join([(r.split('\t') + [''] * len(H))[i] for i in keep])
            for r in lines[1:]]
        H = {n: i for i, n in enumerate(hdr)}

    out_lines = ['\t'.join(hdr + ['priority', 'priority_reason'])]
    counts = {}
    for raw in lines[1:]:
        c = raw.split('\t')
        p, why = classify(c, H)
        counts[p] = counts.get(p, 0) + 1
        out_lines.append('\t'.join(c + [p, why.replace('\t', ' ')]))
    with open(out or path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines) + '\n')
    return counts


ORDER = ['P0(至急)', 'P0(最優先)', 'P1(高)', 'P2(中)', 'P3(低)',
         'P4(低・実装済)', '対象外']


def main():
    p = argparse.ArgumentParser(description='台帳に対応優先度を付与する')
    p.add_argument('--full', default=None, help='既定: $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv')
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    full = a.full or data_path('weko3_api_list_full.tsv')

    import tempfile
    tmp = tempfile.mktemp(suffix='.tsv') if a.dry_run else None
    counts = apply_to(full, out=tmp)
    total = sum(counts.values())
    print(f'{"(dry-run) " if a.dry_run else ""}{full}: {total} 行に priority を付与')
    for k in ORDER:
        if counts.get(k):
            print(f'  {k:<14} {counts[k]:>4}')
    for k in sorted(set(counts) - set(ORDER)):
        print(f'  {k:<14} {counts[k]:>4}  ← 未定義の区分')
    if tmp:
        os.unlink(tmp)


if __name__ == '__main__':
    main()
