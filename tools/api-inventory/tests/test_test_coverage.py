# -*- coding: utf-8 -*-
"""test_coverage.py — 各行のテストが4観点を押さえているかを静的に判定する。

これは**キーワード判定であり、テストの十分性は見ていない**。「観点が全く見当たらない」
ことの検出にだけ使える。だからこそ、判定が緩む方向に壊れると
「テストがある」と誤って言い切る台帳が出来上がる。
"""
import os

import pytest

import test_coverage as tc
from conftest import make_row, write_full, run


def analyse(src):
    return tc.analyse({'t.py::test_x': src})


# --- 4観点の判定 -----------------------------------------------------------

@pytest.mark.parametrize('code', [
    'assert res.status_code == 200',
    'assert res.status_code == 201',
    'assert res.status_code in (200, 302)',
])
def test_正常値は2xxの検証で立つ(code):
    assert analyse(code)['normal']


@pytest.mark.parametrize('code', [
    'assert res.status_code == 403',
    'assert res.status_code == 500',
    'assert res.status_code in (400, 422)',
])
def test_異常値は4xx5xxの検証で立つ(code):
    assert analyse(code)['abnormal']


def test_2xxだけなら異常値は立たない():
    r = analyse('assert res.status_code == 200')
    assert r['normal'] and not r['abnormal']


@pytest.mark.parametrize('code', [
    'with pytest.raises(ValueError):\n    f()',
    'self.assertRaises(KeyError, f)',
])
def test_例外処理は例外検証で立つ(code):
    assert analyse(code)['exception']


def test_境界値はparametrizeで立つ():
    assert analyse('@pytest.mark.parametrize("v", [0, 1])\ndef test_x(v): pass')['boundary']


def test_境界値は関数名からも立つ():
    """本体に現れなくても、名前が境界を狙っていると分かるものは拾う。"""
    assert tc.analyse({'t.py::test_empty_title': 'assert True'})['boundary']


def test_観点が何も無ければ全て偽():
    r = analyse('assert res is not None')
    assert not any(r.values())


# --- 対応するテスト関数の特定 ----------------------------------------------

def test_URIから検索に使う静的部分を取り出す():
    assert tc.norm_static('/api/records/<pid_value>/files') == 'files'
    assert tc.norm_static('/admin/community/new/') == 'new'
    assert tc.norm_static('/<int:pk>') == ''


def _run_on(tmp_path, rows, test_src=None, test_rel='modules/demo/tests/test_x.py'):
    root = tmp_path / 'repo'
    if test_src is not None:
        p = root / test_rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(test_src, encoding='utf-8')
    full = write_full(tmp_path / 'full.tsv', rows)
    run('test_coverage.py', '--full', full, '--weko-root', str(root), expect=0)
    out = [l.rstrip('\n').split('\t') for l in open(full, encoding='utf-8')]
    return out[0], out[1:]


def test_同じファイル内の別APIのテストを自分のものにしない(tmp_path):
    """ファイル単位で見ると、隣の API のアサーションを自分の観点として数えてしまう。"""
    src = '''
def test_other_api(client):
    res = client.get('/other')
    assert res.status_code == 200

def test_mine(client):
    res = client.get('/mine')
    assert something(res)
'''
    hdr, [r] = _run_on(tmp_path, [make_row(
        uri='/mine', impl_func='mine_view', test_file='modules/demo/tests/test_x.py')],
        test_src=src)
    assert r[hdr.index('test_normal')] == '-'


def test_関係するテストが見つかれば観点を判定する(tmp_path):
    src = '''
def test_show_view_ok(client):
    res = client.get('/show')
    assert res.status_code == 200
'''
    hdr, [r] = _run_on(tmp_path, [make_row(
        uri='/show', impl_func='show_view', test_file='modules/demo/tests/test_x.py')],
        test_src=src)
    assert r[hdr.index('test_normal')] == '○'
    assert r[hdr.index('test_gap')] == '異常値,境界値,例外処理'


def test_名前の判定は部分一致なので過検出しうる(tmp_path):
    """`min` は `mine` にも当たる。境界値の `○` は「それらしい名前がある」以上の
    意味を持たない。緩む方向の癖として明示的に固定しておく。"""
    assert tc.analyse({'t.py::test_mine_ok': 'assert True'})['boundary']


def test_特定不能とテスト無しを同じ記号にしない(tmp_path):
    """どちらも '-' にすると、テストが本当に無い行と区別できなくなる。"""
    hdr, [r] = _run_on(tmp_path, [make_row(test_file='-')])
    assert r[hdr.index('test_normal')] == '?'
    assert r[hdr.index('test_gap')] == '特定不能'


def test_列を増やさず上書きする(tmp_path):
    """毎回付け足すと実行のたびに列が増える。"""
    rows = [make_row()]
    hdr, _ = _run_on(tmp_path, rows)
    from conftest import FULL_HEADER
    assert sorted(hdr) == sorted(FULL_HEADER)


def test_dry_runは台帳を書き換えない(tmp_path):
    full = write_full(tmp_path / 'full.tsv', [make_row()])
    before = open(full, encoding='utf-8').read()
    run('test_coverage.py', '--full', full, '--weko-root', str(tmp_path),
        '--dry-run', expect=0)
    assert open(full, encoding='utf-8').read() == before
