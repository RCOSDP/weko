# -*- coding: utf-8 -*-
"""merge.py — Phase 1 の out/*.tsv を1本にまとめて採番する。

台帳の初回生成でしか使わないが、ここが崩れると以降の全 Phase の入力が崩れる。
"""
import os

import merge
from conftest import run


def _merge(tmp_path, files):
    outdir = tmp_path / 'out'
    outdir.mkdir()
    for name, lines in files.items():
        (outdir / name).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    dst = tmp_path / 'merged.tsv'
    run('merge.py', str(outdir), str(dst), expect=0)
    rows = [l.rstrip('\n').split('\t') for l in open(dst, encoding='utf-8')]
    return rows[0], rows[1:]


def row(uri, method='GET', file='a.py', line='1', module='m'):
    c = [''] * merge.NCOL
    c[1], c[4], c[5], c[13], c[14] = module, method, uri, file, line
    return '\t'.join(c)


def test_ヘッダは定義どおりの列数(tmp_path):
    hdr, _ = _merge(tmp_path, {'a.tsv': [row('/a')]})
    assert hdr == merge.HEADER
    assert len(hdr) == merge.NCOL


def test_連番を振り直す(tmp_path):
    _, rows = _merge(tmp_path, {'a.tsv': [row('/b'), row('/a')]})
    assert [r[0] for r in rows] == ['1', '2']


def test_同じ経路の重複を落とす(tmp_path):
    """uri+method+file+line が同じなら同一行。Phase 1 は複数の抽出を合流させる。"""
    _, rows = _merge(tmp_path, {'a.tsv': [row('/a')], 'b.tsv': [row('/a')]})
    assert len(rows) == 1


def test_列が足りない行は埋める(tmp_path):
    _, [r] = _merge(tmp_path, {'a.tsv': ['x\ty\tz']})
    assert len(r) == merge.NCOL


def test_列が多い行は末尾にまとめる(tmp_path):
    """切り捨てると備考が黙って消える。最終列に連結して残す。"""
    _, [r] = _merge(tmp_path, {'a.tsv': ['\t'.join(['v'] * (merge.NCOL + 2))]})
    assert len(r) == merge.NCOL
    assert ' | ' in r[-1]


def test_誤って混ざったヘッダ行を落とす(tmp_path):
    _, rows = _merge(tmp_path, {'a.tsv': ['\t'.join(merge.HEADER), row('/a')]})
    assert len(rows) == 1


def test_セルの前後の空白を落とす(tmp_path):
    """抽出元によって空白の付き方が違う。突き合わせは文字列一致なので揃える。"""
    _, [r] = _merge(tmp_path, {'a.tsv': [row('  /a  ')]})
    assert r[5] == '/a'
