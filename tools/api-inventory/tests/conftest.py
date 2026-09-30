# -*- coding: utf-8 -*-
"""台帳ツールの単体テスト用の足場。

テストは**データを一切必要としない**。合成した最小のリポジトリと最小の台帳を
その場で組み立て、スクリプトの判定だけを確かめる。台帳そのものの検査は
プライベートリポジトリ側の `tests/` が受け持つ(公開リポジトリに台帳は置けない)。
"""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.normpath(os.path.join(HERE, '..', 'scripts'))
sys.path.insert(0, SCRIPTS)


def run(script, *args, env=None, expect=None):
    """スクリプトを別プロセスで回す。(returncode, stdout, stderr) を返す。

    `build_checklist.py` のようにモジュール直下で処理を走らせるものがあるので、
    import ではなく実行で確かめる。
    """
    e = dict(os.environ)
    e.pop('WEKO_API_INVENTORY_DIR', None)   # 実データを踏まないようにする
    e.update(env or {})
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *map(str, args)],
                       capture_output=True, text=True, env=e)
    if expect is not None:
        assert p.returncode == expect, \
            f'{script} の終了コードが {p.returncode}(期待 {expect})\n' \
            f'--- stdout ---\n{p.stdout}\n--- stderr ---\n{p.stderr}'
    return p


# --- 台帳(full)の合成 -----------------------------------------------------

from schema import FULL_COLUMNS

# 台帳(詳細版)のヘッダ。定義は scripts/schema.py が持つ。
FULL_HEADER = FULL_COLUMNS


def make_row(**over):
    """既定値で埋めた1行を作る。変えたい列だけキーワードで渡す。"""
    r = {n: '-' for n in FULL_HEADER}
    r.update({
        'no': '1', 'module': 'weko-demo', 'api_type': 'REST API',
        'app': 'UIアプリ', 'method': 'GET', 'uri': '/demo',
        'blueprint': 'demo', 'endpoint': 'demo.index',
        'impl_func': 'index', 'impl_file': 'modules/weko-demo/weko_demo/views.py',
        'impl_line': '10', 'auth_required': '要', 'auth_method': 'login_required',
        'data_op': '取得', 'dynamic_verified': '-',
    })
    r.update(over)
    return r


def write_full(path, rows):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\t'.join(FULL_HEADER) + '\n')
        for r in rows:
            f.write('\t'.join(r.get(n, '-') for n in FULL_HEADER) + '\n')
    return str(path)


@pytest.fixture
def full_tsv(tmp_path):
    """行を渡すと台帳(62列)を書き出して、そのパスを返す関数。"""
    def _make(rows, name='weko3_api_list_full.tsv'):
        return write_full(tmp_path / name, rows)
    return _make


# --- スナップショット(実機 url_map)の合成 --------------------------------

def snap_entry(app, endpoint, rule, methods=('GET',), **extra):
    d = {'app': app, 'endpoint': endpoint,
         'routes': [{'rule': rule, 'methods': list(methods)}],
         'provider': None, 'attrs': 'ast'}
    d.update(extra)
    return d


@pytest.fixture
def snapshot(tmp_path):
    """endpoints を渡すとスナップショット JSON を書き出して、そのパスを返す関数。"""
    def _make(endpoints, revision='deadbee', tag='v0.0.0', name='api_snapshot.json'):
        p = tmp_path / name
        json.dump({'meta': {'revision': revision, 'tag': tag}, 'endpoints': endpoints},
                  open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        return str(p)
    return _make


@pytest.fixture
def allow_json(tmp_path):
    def _make(not_registered=None, not_a_route=None, name='reconcile_allow.json'):
        p = tmp_path / name
        json.dump({'not_registered': not_registered or {},
                   'not_a_route': not_a_route or []},
                  open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        return str(p)
    return _make


# --- 合成リポジトリ --------------------------------------------------------

@pytest.fixture
def fake_repo(tmp_path):
    """`modules/<pkg>/<pkg>/<file>` にソースを置く最小リポジトリを作る。"""
    root = tmp_path / 'repo'

    def _write(relpath, text):
        p = root / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        return str(p)

    _write('modules/.keep', '')
    _write.root = str(root)
    return _write
