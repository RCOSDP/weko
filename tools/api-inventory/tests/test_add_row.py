# -*- coding: utf-8 -*-
"""add_row.py — 新しい行に振る `no`。

`no` は台帳の主キーで、一度振った番号は変えず、使い回さない。消した行の番号は
`no_registry.tsv` に `廃止` として残るので、台帳だけを見て「最大値 + 1」にすると、
末尾の行を廃止した直後にその番号をもう一度振ってしまう。
"""
import json

import add_row
from conftest import FULL_HEADER, make_row, run

REG_HEADER = '\t'.join(add_row.REGISTRY_COLUMNS)


def _setup(tmp_path, full_nos, registry=None):
    full = tmp_path / 'weko3_api_list_full.tsv'
    lines = ['\t'.join(FULL_HEADER)]
    for n in full_nos:
        r = make_row(no=str(n), uri=f'/demo{n}', endpoint=f'demo.v{n}')
        lines.append('\t'.join(r[h] for h in FULL_HEADER))
    full.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    if registry is not None:
        (tmp_path / 'no_registry.tsv').write_text(
            '\n'.join([REG_HEADER] + registry) + '\n', encoding='utf-8')
    snap = tmp_path / 'api_snapshot.json'
    snap.write_text(json.dumps({'endpoints': {'ui:demo.new': {
        'app': 'ui', 'endpoint': 'demo.new', 'view': 'weko_demo.views.new',
        'routes': [{'rule': '/demo/new', 'methods': ['GET']}]}}}), encoding='utf-8')
    return full, snap


def _append(tmp_path, full, snap):
    return run('add_row.py', '--endpoint', 'ui:demo.new', '--append',
               '--full', full, '--snapshot', snap, '--weko-root', tmp_path, expect=0)


def _last(path):
    return open(path, encoding='utf-8').read().rstrip('\n').split('\n')[-1].split('\t')


def test_次の番号は払い出し記録と台帳の両方の最大値の次(tmp_path):
    # 3 を廃止して台帳から消した直後。台帳だけ見ると 3 を振ってしまう
    full, snap = _setup(tmp_path, [1, 2], registry=[
        '1\tUIアプリ\tGET\t/demo1\tdemo.v1\t現役\t',
        '2\tUIアプリ\tGET\t/demo2\tdemo.v2\t現役\t',
        '3\tUIアプリ\tGET\t/demo3\tdemo.v3\t廃止\t経路が消えた',
    ])
    _append(tmp_path, full, snap)
    assert _last(full)[0] == '4'


def test_追記した行を同じ番号で払い出し記録に書き足す(tmp_path):
    full, snap = _setup(tmp_path, [1], registry=['1\tUIアプリ\tGET\t/demo1\tdemo.v1\t現役\t'])
    _append(tmp_path, full, snap)
    assert _last(tmp_path / 'no_registry.tsv') == \
        ['2', 'UIアプリ', 'GET', '/demo/new', 'demo.new', '現役', '']


def test_表示だけなら払い出し記録を触らない(tmp_path):
    full, snap = _setup(tmp_path, [1], registry=['1\tUIアプリ\tGET\t/demo1\tdemo.v1\t現役\t'])
    before = (tmp_path / 'no_registry.tsv').read_text(encoding='utf-8')
    run('add_row.py', '--endpoint', 'ui:demo.new',
        '--full', full, '--snapshot', snap, '--weko-root', tmp_path, expect=0)
    assert (tmp_path / 'no_registry.tsv').read_text(encoding='utf-8') == before


def test_払い出し記録が無ければ台帳の最大値の次で注意を出す(tmp_path):
    full, snap = _setup(tmp_path, [1, 5])
    p = _append(tmp_path, full, snap)
    assert _last(full)[0] == '6'
    assert '払い出しを記録していません' in p.stdout
    assert not (tmp_path / 'no_registry.tsv').exists()


def test_払い出し記録のヘッダが違えば書き込まない(tmp_path):
    full, snap = _setup(tmp_path, [1], registry=[])
    (tmp_path / 'no_registry.tsv').write_text('no\turi\n1\t/demo1\n', encoding='utf-8')
    before = full.read_text(encoding='utf-8')
    p = run('add_row.py', '--endpoint', 'ui:demo.new', '--append',
            '--full', full, '--snapshot', snap, '--weko-root', tmp_path)
    assert p.returncode != 0
    assert full.read_text(encoding='utf-8') == before
