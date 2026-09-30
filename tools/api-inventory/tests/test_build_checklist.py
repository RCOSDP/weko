# -*- coding: utf-8 -*-
"""build_checklist.py — 62列の詳細版から32列のチェックリスト版を丸ごと生成する。

24列版は派生物で、手編集は次の生成で消える。ここで守るのは2点。

  1. **参照している列名が実在すること。** `g(c, "存在しない列")` は例外にならず
     空文字を返す。列をリネームすると、その列だけが黙って空になったチェックリストが
     できあがる。
  2. **統合の規則が変わっていないこと。** impl の組み立て、auth の連結、
     security_flags の拾い方は、列を読む側の awk 例と README の凡例に直結する。
"""
import ast
import os
import re

import pytest

import schema
from conftest import SCRIPTS, FULL_HEADER, make_row, write_full, run

SRC = open(os.path.join(SCRIPTS, 'build_checklist.py'), encoding='utf-8').read()


def test_出力列を自前で並べ直していない():
    """列定義は schema.py が唯一の正。ここで並べ直すと必ず台帳とずれる。"""
    assert 'NEW = CHECKLIST_COLUMNS' in SRC


def _referenced_columns():
    """`g(c, "xxx")` で参照している列名を全部拾う。"""
    return set(re.findall(r'g\(\s*c\s*,\s*"([^"]+)"\s*\)', SRC))


def test_参照している列が全て台帳のヘッダに実在する():
    missing = sorted(_referenced_columns() - set(FULL_HEADER))
    assert not missing, (
        f'build_checklist.py が存在しない列を読んでいる: {missing}\n'
        'g() は存在しない列名でも例外にならず空文字を返すため、'
        '該当列だけが黙って空のチェックリストが出来上がる。')


def test_出力列は32列で列名が重複しない():
    new = schema.CHECKLIST_COLUMNS
    assert len(new) == 32
    assert len(set(new)) == len(new)


def test_派生列は末尾に置く():
    """既存列の位置を動かすと README の awk 例(`$20` など)が全て壊れる。"""
    assert schema.CHECKLIST_COLUMNS[24:] == schema.DERIVED_COLUMNS


# --- 生成そのもの ---------------------------------------------------------

def _build(tmp_path, rows):
    src = write_full(tmp_path / 'full.tsv', rows)
    dst = str(tmp_path / 'chk.tsv')
    run('build_checklist.py', src, dst, expect=0)
    out = [l.rstrip('\n').split('\t') for l in open(dst, encoding='utf-8')]
    return out[0], out[1:]


def test_行数と列数が揃う(tmp_path):
    hdr, rows = _build(tmp_path, [make_row(no='1'), make_row(no='2')])
    assert len(hdr) == 32
    assert len(rows) == 2
    assert all(len(r) == 32 for r in rows)


def test_implは関数とファイルと行を組み立てる(tmp_path):
    hdr, [r] = _build(tmp_path, [make_row(
        impl_func='show', impl_file='modules/weko-demo/views.py', impl_line='42')])
    assert r[hdr.index('impl')] == 'show @modules/weko-demo/views.py:42'


def test_impl_lineが0なら行番号を付けない(tmp_path):
    """0 は「行が取れなかった」印。`views.py:0` と書くと実在の位置に見えてしまう。"""
    hdr, [r] = _build(tmp_path, [make_row(
        impl_func='show', impl_file='modules/weko-demo/views.py', impl_line='0')])
    assert r[hdr.index('impl')] == 'show @modules/weko-demo/views.py'


def test_authは要否と方式と仕組みを連結する(tmp_path):
    hdr, [r] = _build(tmp_path, [make_row(
        auth_required='要(管理)', auth_method='roles_required',
        auth_mechanism='admin-role-table(WEKO_ADMIN_ACCESS_TABLE)')])
    assert r[hdr.index('auth')] == '要(管理) | roles_required | [admin-role-table]'


def test_security_flagsは該当する観点だけを集める(tmp_path):
    hdr, [r] = _build(tmp_path, [make_row(
        csrf_protection='なし(状態変更なのに未保護)',
        input_validation='あり(スキーマ検証)',
        bola_risk='★所有者チェックなし')])
    flags = r[hdr.index('security_flags')]
    assert 'CSRF:' in flags and 'BOLA:' in flags
    assert 'INPUT:' not in flags        # 「あり」は指摘ではない


def test_空欄と不明はハイフンに寄せる(tmp_path):
    """読む側が「空欄」「-」「不明」を区別しなくて済むようにする。"""
    hdr, [r] = _build(tmp_path, [make_row(summary='', roles='不明')])
    assert r[hdr.index('summary')] == '-'
    assert r[hdr.index('roles_scope')] == '-'


def test_タブと改行はセルに残さない(tmp_path):
    """1行1レコードの TSV が壊れると、以降の全行の列がずれる。"""
    hdr, rows = _build(tmp_path, [make_row(summary='一行目\t二行目')])
    assert len(rows) == 1 and len(rows[0]) == 32
    assert '\t' not in rows[0][hdr.index('summary')]
