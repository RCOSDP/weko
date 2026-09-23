# -*- coding: utf-8 -*-
"""open_findings.py — 未解消の指摘をチケット番号だけで報告する。

この検知が緩むと「台帳に書いたまま直さない」が無言で通る。所見は private 側に
しか書けないぶん、未修正が台帳の中だけで滞留して忘れられるのを、ここが止めて
いる。**落ちなくなっても件数が減るだけでゲートは緑**なので、
「落ちると言えること」を固定しておく。

もう一つ守るのは秘匿。このスクリプトは public な CI から回るので、
出してよいのは件数とチケット番号だけで、経路名・endpoint 名・所見は出さない
(docs/RULE.md §1)。
"""
import json

import open_findings as of
from conftest import make_row, run, write_full


def ledger(tmp_path, rows, name='full.tsv'):
    return write_full(tmp_path / name, rows)


def baseline(tmp_path, untriaged, name='fix_baseline.json'):
    p = tmp_path / name
    json.dump({'untriaged': untriaged}, open(p, 'w', encoding='utf-8'),
              ensure_ascii=False)
    return str(p)


def row(no, priority='P1', ticket='未起票', **over):
    return make_row(no=no, priority=priority, fix_ticket=ticket, **over)


# --- ゲート A: 記入漏れ ----------------------------------------------------

def test_対応が要る行のチケット欄が空なら落ちる(tmp_path):
    """所見を書いたのに起票し忘れる、を止める。"""
    tsv = ledger(tmp_path, [row('1', ticket='-')])
    p = run('open_findings.py', '--full', tsv, '--baseline',
            baseline(tmp_path, {'P1': 9}), '--gate', expect=1)
    assert '記入漏れ' in p.stdout


def test_語彙外の値も記入漏れとして扱う(tmp_path):
    """「そのうち直す」のような自由記述を通すと、集計が意味を失う。"""
    tsv = ledger(tmp_path, [row('1', ticket='そのうち直す')])
    run('open_findings.py', '--full', tsv, '--baseline',
        baseline(tmp_path, {'P1': 9}), '--gate', expect=1)


def test_対応が要らない行は空でも落ちない(tmp_path):
    tsv = ledger(tmp_path, [row('1', priority='P3', ticket='-')])
    run('open_findings.py', '--full', tsv, '--baseline',
        baseline(tmp_path, {}), '--gate', expect=0)


# --- ゲート B: 未起票のラチェット ------------------------------------------

def test_未起票がベースラインを超えたら落ちる(tmp_path):
    """対応を先送りするたびに積み上がるのを止めるラチェット。"""
    tsv = ledger(tmp_path, [row('1'), row('2')])
    p = run('open_findings.py', '--full', tsv, '--baseline',
            baseline(tmp_path, {'P1': 1}), '--gate', expect=1)
    assert 'ベースライン' in p.stdout


def test_ベースライン内なら通る(tmp_path):
    tsv = ledger(tmp_path, [row('1'), row('2')])
    run('open_findings.py', '--full', tsv, '--baseline',
        baseline(tmp_path, {'P1': 2}), '--gate', expect=0)


def test_起票すれば未起票が減って通る(tmp_path):
    """起票は前に進む操作。ベースラインを触らずに緑になる。"""
    tsv = ledger(tmp_path, [row('1', ticket='issue62810'), row('2')])
    p = run('open_findings.py', '--full', tsv, '--baseline',
            baseline(tmp_path, {'P1': 1}), '--gate', expect=0)
    assert 'issue62810' in p.stdout


def test_ベースラインが無ければ増加は見ない(tmp_path):
    """private 側の台帳を持たない環境でも、記入漏れの検査までは動くこと。"""
    tsv = ledger(tmp_path, [row('1')])
    p = run('open_findings.py', '--full', tsv, '--baseline',
            str(tmp_path / 'ない.json'), '--gate', expect=0)
    assert 'ベースライン' in p.stdout


# --- 集計 ------------------------------------------------------------------

def test_解消済みは未解消に数えない(tmp_path):
    """修正済みの行は値を消さずに残す規約なので、残ったまま数えると減らない。"""
    tsv = ledger(tmp_path, [row('1', ticket='解消済み(issue62569)')])
    p = run('open_findings.py', '--full', tsv, '--baseline',
            baseline(tmp_path, {}), '--gate', expect=0)
    assert '解消済み: 1 件' in p.stdout


def test_優先度ごとに内訳を出す(tmp_path):
    tsv = ledger(tmp_path, [row('1'), row('2', priority='P2'), row('3', priority='P2')])
    p = run('open_findings.py', '--full', tsv, '--baseline',
            baseline(tmp_path, {'P1': 1, 'P2': 2}), expect=0)
    assert 'P1 1' in p.stdout and 'P2 2' in p.stdout


def test_列が無い台帳は理由を出して止まる(tmp_path):
    """列を足す前のブランチで回したときに、空の集計を返して緑にしない。"""
    from conftest import FULL_HEADER
    p = tmp_path / 'old.tsv'
    cols = [c for c in FULL_HEADER if c != 'fix_ticket']
    p.write_text('\t'.join(cols) + '\n' + '\t'.join(['-'] * len(cols)) + '\n',
                 encoding='utf-8')
    r = run('open_findings.py', '--full', str(p), expect=1)
    assert 'fix_ticket' in r.stdout + r.stderr


# --- 秘匿の担保 ------------------------------------------------------------

def test_summary_onlyはURIもendpoint名も出さない(tmp_path):
    """public な CI のログ・artifact・PR コメントは誰でも読める。
    出してよいのは件数とチケット番号だけ(docs/RULE.md §1)。"""
    tsv = ledger(tmp_path, [
        row('1', ticket='-', uri='/secret/path/<id>',
            endpoint='weko_demo.secret_endpoint',
            sec_exposed='非公開アイテムのメタデータ',
            impl_file='modules/weko-demo/weko_demo/views.py'),
    ])
    p = run('open_findings.py', '--full', tsv, '--baseline',
            baseline(tmp_path, {'P1': 9}), '--summary-only', '--gate', expect=1)
    for leaked in ('/secret/path', 'secret_endpoint', '非公開アイテム',
                   'views.py', 'no='):
        assert leaked not in p.stdout, f'{leaked} が出ている'
    assert '記入漏れ/語彙外: 1 件' in p.stdout


def test_チケット番号は出す(tmp_path):
    """番号には分析が含まれないので出してよい。出さないと忘れ防止にならない。"""
    tsv = ledger(tmp_path, [row('1', ticket='issue62810'),
                            row('2', ticket='issue62811')])
    p = run('open_findings.py', '--full', tsv, '--baseline',
            baseline(tmp_path, {}), '--summary-only', expect=0)
    assert 'issue62810' in p.stdout and 'issue62811' in p.stdout


def test_語彙の区分(tmp_path):
    assert of.schema.fix_ticket_kind('issue62810') == '起票済み'
    assert of.schema.fix_ticket_kind('解消済み(issue62569)') == '解消済み'
    assert of.schema.fix_ticket_kind('未起票') == '未起票'
    assert of.schema.fix_ticket_kind('-') == 'なし'
    assert of.schema.fix_ticket_kind('issue62810 ファイル配信の認可漏れ') is None, \
        '説明を添えた値を通すと、番号だけという約束が崩れる'
