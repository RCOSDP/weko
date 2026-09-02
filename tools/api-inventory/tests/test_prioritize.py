# -*- coding: utf-8 -*-
"""prioritize.py — 台帳に対応優先度を付ける。

優先度は「どの行から手を付けるか」を決める唯一の指標なので、判定が静かに変わると
**見るべき行が埋もれる**。ルールの分岐そのものを固定する。

判定の入力は台帳の本体列(security_finding / dynamic_verified / data_op / deprecated 等)。
派生列は毎回上書きされるので、ここを直しても意味がない。
"""
import pytest

import prioritize
from conftest import FULL_HEADER, make_row, write_full

H = {n: i for i, n in enumerate(FULL_HEADER)}


def cls(**over):
    """1行を作って classify に掛け、(優先度, 理由) を返す。"""
    r = make_row(**over)
    return prioritize.classify([r[n] for n in FULL_HEADER], H)


def dec(allow=(frozenset(), frozenset()), **over):
    r = make_row(**over)
    return prioritize.decide([r[n] for n in FULL_HEADER], H, allow)


# --- P1: データ破壊と、認可の無い状態変更 --------------------------------

def test_無認証で既存ファイル実体を壊せる行はP1():
    p, why = cls(method='POST', auth_required='不要', data_op='更新',
                 data_store='ファイル実体(FileInstance)')
    assert p == 'P1' and 'ファイル実体' in why


def test_認証の無い状態変更系はP1():
    p, why = cls(method='POST', auth_required='不要', data_op='更新')
    assert p == 'P1' and '認証チェックが無い' in why


def test_権限チェックが機能していない状態変更系はP1():
    p, why = cls(method='DELETE', sec_pattern='ロールチェックが実効せず',
                 data_op='物理削除')
    assert p == 'P1' and '機能していない' in why


def test_未認証で到達したという実測はP1に上げる():
    """静的には login_required が付いていても、実測で通っていれば実態が正。"""
    p, _ = cls(method='POST', auth_required='要', data_op='更新',
               dynamic_verified='[実測] 未認証で到達')
    assert p == 'P1'


# --- P2: 壊さない、または限定が足りない -----------------------------------

def test_新規作成しかしない無認証の書き込みはP2():
    """既存データを壊さない。P1(データ破壊)と同列には置かない。"""
    p, why = cls(method='POST', auth_required='不要', data_op='作成')
    assert p == 'P2' and '新規作成のみ' in why


def test_ログインのみで所有者限定が無い状態変更系はP2():
    p, why = cls(method='PUT', auth_required='要', data_op='更新',
                 dynamic_verified='[実測] ログインのみで到達')
    assert p == 'P2' and 'IDOR' in why


def test_到達可否が未測定の状態変更系はP2():
    """「分からない」を安全側に倒さない。測っていない書き込みは確認対象。"""
    p, why = cls(method='POST', auth_required='要', data_op='更新',
                 dynamic_verified='-')
    assert p == 'P2' and '未測定' in why


def test_参照系でも露出が認証情報で認可が緩ければP2():
    p, why = cls(method='GET', auth_required='不要', data_op='取得',
                 sec_pattern='認証不要で参照可', sec_exposed='client_secret')
    assert p == 'P2' and '認証情報' in why


def test_露出の記述だけでは引き上げない():
    """指摘も実証も無い行を露出語だけで上げると、適切に絞られている行まで赤くなる。"""
    p, _ = cls(method='GET', auth_required='要', data_op='取得',
               access_variance='非公開アイテムは除外される')
    assert p != 'P2'


# --- P3 / P4 / P5 / 対象外 ------------------------------------------------

def test_認証の無い読み取り系はP3():
    p, why = cls(method='GET', auth_required='不要', data_op='取得')
    assert p == 'P3' and '読み取り系' in why


@pytest.mark.parametrize('uri,label', [
    ('/ping', 'ヘルスチェック'), ('/robots.txt', 'robots.txt'),
    ('/api/oai', 'OAI-PMH'), ('/static/x.js', '静的ファイル配信')])
def test_意図的な公開設計はP4(uri, label):
    p, why = cls(method='GET', uri=uri, auth_required='不要', data_op='取得')
    assert p == 'P4' and label in why


def test_具体的な権限チェック機構があればP5():
    p, why = cls(method='GET', auth_required='要',
                 auth_method='need_record_permission', data_op='取得')
    assert p == 'P5' and 'need_record_permission' in why


def test_admin保護され指摘も実証も無ければ対象外():
    p, _ = cls(method='GET', auth_required='要(管理)',
               auth_method='roles_required', data_op='取得')
    assert p == '対象外'


def test_指摘がある行は対象外にしない():
    """保護されているように見えて破綻している行を除外してしまうため。"""
    p, _ = cls(method='GET', auth_required='要(管理)',
               auth_method='roles_required', data_op='取得',
               sec_pattern='管理画面だが権限表に載っていない')
    assert p != '対象外'


# --- テスト観点による引き上げ ---------------------------------------------

def test_テスト観点が全く確認できない行はP3まで上げる():
    p, why = cls(method='GET', auth_required='要(管理)',
                 auth_method='roles_required', data_op='取得',
                 test_gap='正常値,異常値,境界値,例外処理')
    assert p == 'P3' and '4観点' in why


def test_テスト関数を特定できない行もP3まで上げる():
    p, why = cls(method='GET', auth_required='要(管理)',
                 auth_method='roles_required', data_op='取得',
                 test_gap='特定不能')
    assert p == 'P3' and '特定できず' in why


def test_観点が一部欠けるだけなら優先度は変えず理由に残す():
    p, why = cls(method='GET', auth_required='要(管理)',
                 auth_method='roles_required', data_op='取得',
                 test_gap='例外処理')
    assert p == '対象外' and '例外処理' in why


# --- 非利用・環境依存の重ね合わせ ------------------------------------------

def test_非利用で認可も軽ければ整理対象():
    p, why, cleanup = dec(method='GET', auth_required='不要', data_op='取得',
                          deprecated='未使用(呼出元なし)')
    assert p == '整理対象' and cleanup == '未使用(呼出元なし)'


def test_非利用でもP1は優先度を落とさない():
    """消せば済むが、消すまでは穴が空いたまま。優先度を下げると見落とす。"""
    p, why, _ = dec(method='POST', auth_required='不要', data_op='更新',
                    deprecated='未使用(呼出元なし)')
    assert p == 'P1' and '削除が最短' in why


def test_実機に無い行は環境依存にするが削除候補にしない():
    """別の設定・別サイトでは有効になる。台帳からは消さない。"""
    p, why, cleanup = dec(allow=(frozenset({'/demo'}), frozenset()),
                          method='GET', uri='/demo',
                          auth_required='不要', data_op='取得')
    assert p == '環境依存' and cleanup == '-'
    assert '認可上の判定は P3' in why


def test_実測の履歴を現在値として読まない():
    """apply_probe_results.py --keep-history が旧測定を同じセルに残す。
    旧測定の『未認証で到達』を今の値として読むと、直した行が赤いままになる。"""
    now = '[実測·2026-09-02] 管理者で到達'
    old = '[実測·2026-08-26] 未認証で到達'
    p, _ = cls(method='POST', auth_required='要', data_op='更新',
               dynamic_verified=f'{now}{prioritize.HISTORY_SEP}{old}')
    assert p != 'P1'


# --- 列順の正規化 ----------------------------------------------------------

def test_派生列は実行順に依存しない位置に揃える(tmp_path):
    """test_coverage.py は test_* を末尾に付け直す。prioritize.py が並びを
    正規化しないと、同じ内容でも実行順で列順が変わって差分が出続ける。"""
    p = write_full(tmp_path / 'full.tsv', [make_row()])
    prioritize.apply_to(p)
    hdr = open(p, encoding='utf-8').readline().rstrip('\n').split('\t')
    assert hdr[-8:] == prioritize.TAIL
    assert hdr == FULL_HEADER


def test_二度流しても結果が変わらない(tmp_path):
    p = write_full(tmp_path / 'full.tsv', [make_row(no='1'), make_row(no='2')])
    prioritize.apply_to(p)
    once = open(p, encoding='utf-8').read()
    prioritize.apply_to(p)
    assert open(p, encoding='utf-8').read() == once
