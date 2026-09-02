# -*- coding: utf-8 -*-
"""reconcile.py — 実機 url_map と台帳の突き合わせ。

**検出器そのものの回帰テスト**。ここが黙って壊れると、台帳から経路が漏れていても
ゲートは緑のまま通る。A〜E の各検出が「本当に鳴る」ことを毎回確かめる。
"""
import json

import pytest

import reconcile
from conftest import make_row, snap_entry, run


def _run(snapshot, tsv, allow, *extra, expect=None):
    return run('reconcile.py', '--snapshot', snapshot, '--tsv', tsv,
               '--allow', allow, *extra, expect=expect)


# --- 一致する状態が本当に緑になるか --------------------------------------

def test_一致していればゲートを通る(full_tsv, snapshot, allow_json):
    tsv = full_tsv([make_row(uri='/demo', method='GET', endpoint='demo.index')])
    snap = snapshot({'ui:demo.index': snap_entry('ui', 'demo.index', '/demo')})
    p = _run(snap, tsv, allow_json(), '--gate', expect=0)
    assert '✅ 一致' in p.stdout


# --- A: 台帳の抽出漏れ ----------------------------------------------------

def test_A_実機にあって台帳に無い経路を検出する(full_tsv, snapshot, allow_json):
    tsv = full_tsv([make_row(uri='/demo', endpoint='demo.index')])
    snap = snapshot({
        'ui:demo.index': snap_entry('ui', 'demo.index', '/demo'),
        'ui:demo.hidden': snap_entry('ui', 'demo.hidden', '/demo/hidden'),
    })
    p = _run(snap, tsv, allow_json(), '--gate', expect=1)
    assert '/demo/hidden' in p.stdout
    assert 'A. インベントリ未収載(抽出漏れ) | 1' in p.stdout


# --- B: 台帳にあって実機に無い ------------------------------------------

def test_B_実機に無い行を検出し許可リストで既知にできる(full_tsv, snapshot, allow_json):
    rows = [make_row(uri='/demo', endpoint='demo.index'),
            make_row(no='2', uri='/gone', endpoint='demo.gone')]
    tsv = full_tsv(rows)
    snap = snapshot({'ui:demo.index': snap_entry('ui', 'demo.index', '/demo')})

    p = _run(snap, tsv, allow_json(), '--gate', expect=1)
    assert "B. 実機に無い(未説明) | 1" in p.stdout

    # 理由を書いて許可リストに載せれば既知(B')に移り、ゲートは通る。
    # URI を許可すると、その行の endpoint も E' 側で黙認される。
    ok = allow_json(not_registered={'/gone': 'config で無効'})
    p = _run(snap, tsv, ok, '--gate', expect=0)
    assert "B'. 実機に無い(既知・許容) | 1" in p.stdout
    assert 'B. 実機に無い(未説明) | 0' in p.stdout
    assert 'config で無効' in p.stdout      # 理由が必ず出力に残る


# --- C: メソッド不一致 ----------------------------------------------------

def test_C_メソッドの食い違いを検出する(full_tsv, snapshot, allow_json):
    tsv = full_tsv([make_row(uri='/demo', method='GET', endpoint='demo.index')])
    snap = snapshot({'ui:demo.index':
                     snap_entry('ui', 'demo.index', '/demo', ('GET', 'POST'))})
    p = _run(snap, tsv, allow_json(), '--gate', expect=1)
    assert 'C. メソッド不一致 | 1' in p.stdout


def test_C_HEADとOPTIONSは差分に数えない(full_tsv, snapshot, allow_json):
    """werkzeug が GET に自動付与するだけなので、比較対象から外れていること。"""
    tsv = full_tsv([make_row(uri='/demo', method='GET,HEAD,OPTIONS',
                             endpoint='demo.index')])
    snap = snapshot({'ui:demo.index': snap_entry('ui', 'demo.index', '/demo')})
    _run(snap, tsv, allow_json(), '--gate', expect=0)


# --- D: app 列の不一致 ----------------------------------------------------

def test_D_登録先アプリの記載誤りを検出する(full_tsv, snapshot, allow_json):
    tsv = full_tsv([make_row(uri='/api/demo', app='UIアプリ', endpoint='demo.index')])
    snap = snapshot({'api:demo.index': snap_entry('api', 'demo.index', '/demo')})
    p = _run(snap, tsv, allow_json(), '--gate', expect=1)
    assert 'D. app列の不一致 | 1' in p.stdout


# --- E: endpoint 単位の取りこぼし ----------------------------------------

def test_E_同一URIに複数endpointがある取りこぼしを検出する(full_tsv, snapshot,
                                                            allow_json):
    """URI 単位の A では拾えない。台帳は endpoint 単位で行を持つ方針。"""
    tsv = full_tsv([make_row(uri='/demo', endpoint='demo.index')])
    snap = snapshot({
        'ui:demo.index': snap_entry('ui', 'demo.index', '/demo'),
        'ui:other.index': snap_entry('ui', 'other.index', '/demo'),
    })
    p = _run(snap, tsv, allow_json(), '--gate', expect=1)
    assert 'A. インベントリ未収載(抽出漏れ) | 0' in p.stdout   # URI は一致している
    assert 'E. endpoint 未収載 | 1' in p.stdout


# --- 出力の秘匿 -----------------------------------------------------------

def test_summary_onlyは経路名を出さない(full_tsv, snapshot, allow_json):
    """public な CI ログ・artifact・PR コメントは誰でも読める。"""
    tsv = full_tsv([make_row(uri='/demo', endpoint='demo.index')])
    snap = snapshot({
        'ui:demo.index': snap_entry('ui', 'demo.index', '/demo'),
        'ui:demo.secret': snap_entry('ui', 'demo.secret', '/secret/leak/me'),
    })
    p = _run(snap, tsv, allow_json(), '--summary-only')
    assert '/secret/leak/me' not in p.stdout
    assert 'demo.secret' not in p.stdout
    assert 'A. インベントリ未収載(抽出漏れ) | 1' in p.stdout


# --- 正規化規則 -----------------------------------------------------------

@pytest.mark.parametrize('a,b', [('/demo/', '/demo'), ('/demo', '/demo'), ('/', '/')])
def test_末尾スラッシュは同一視する(a, b):
    assert reconcile.norm(a) == reconcile.norm(b)


def test_APIアプリの経路にはapiが前置される(snapshot):
    """API アプリは DispatcherMiddleware で /api にマウントされ、url_map 側には出ない。"""
    snap = snapshot({'api:x': snap_entry('api', 'x', '/records')})
    _, S = reconcile.load_snapshot(snap)
    assert '/api/records' in S


@pytest.mark.parametrize('apps,expected', [
    ({'ui'}, 'UIアプリ'), ({'api'}, 'APIアプリ(/api)'), ({'ui', 'api'}, '両方')])
def test_app列の期待値(apps, expected):
    assert reconcile.app_expected(apps) == expected
