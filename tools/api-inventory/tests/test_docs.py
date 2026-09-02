# -*- coding: utf-8 -*-
"""手順書(scripts/README.md)が実装とずれていないかを検査する。

手順書は**壊れても誰も落ちない**ので、いちばん静かに腐る。実際 v2.0.4 時点で
README は「57列 / 24列 / 926行 / `NF!=65`」と書いたまま、実体は
「62列 / 32列 / 1048行」になっていた。列数の検算例が間違っていると、
検算をすり抜けた壊れた行がそのまま台帳に入る。

ここで見るのは3点。

  1. 手順に出てくるスクリプトが実在すること
  2. 列数・列名の記述が `schema.py` と一致すること
  3. 手順に書かれた実行順が、スクリプトの依存関係と矛盾しないこと
"""
import os
import re

import pytest

import schema
from conftest import SCRIPTS

DOC = os.path.join(SCRIPTS, 'README.md')
TEXT = open(DOC, encoding='utf-8').read()

# 台帳の列名として出てくるが、実際には24列版・中間生成物の名前であるもの。
# schema.FULL_COLUMNS に無くても誤りではない。
NOT_FULL_COLUMNS = set(schema.CHECKLIST_COLUMNS) | {
    'impl', 'auth', 'roles_scope', 'last_change', 'tags', 'security_finding',
    'security_flags',
}

# 列名に見えるが列ではない語。entry point 群の名前など。
NOT_A_COLUMN = {'api_apps', 'api_blueprints', 'data_dir', 'api_route',
                'api_route_item', 'access_token', 'refresh_token', 'api_key'}


def test_手順に出てくるスクリプトが実在する():
    """`python3 .../xxx.py` の形で案内しているものだけを見る
    (解析対象側の views.py / admin.py などの言及と混ぜない)。"""
    named = set(re.findall(r'python3\s+(?:[^\s$]*/)?([a-z_0-9]+\.py)', TEXT))
    named |= set(re.findall(r'`([a-z_0-9]+\.py)`', TEXT)) & set(os.listdir(SCRIPTS))
    missing = sorted(n for n in named if not os.path.isfile(os.path.join(SCRIPTS, n)))
    assert not missing, f'README が存在しないスクリプトを案内している: {missing}'


def test_全スクリプトが手順書のどこかで説明されている():
    """入口が README しかない。載っていないスクリプトは、いずれ誰も回さなくなる。"""
    files = {f for f in os.listdir(SCRIPTS)
             if f.endswith('.py') and not f.startswith('_')}
    files -= {'schema.py', 'paths.py'}        # 他から読まれるだけの土台
    undocumented = sorted(f for f in files if f not in TEXT)
    assert not undocumented, f'README に説明が無いスクリプト: {undocumented}'


# 台帳そのものの列数を名指ししている書き方。ここが古びると検算が意味を失う。
FULL_CLAIM = re.compile(r'(?:weko3_api_list_full\.tsv`?\(|詳細版\()(\d+)列')
CHECKLIST_CLAIM = re.compile(
    r'(?:weko3_api_list\.tsv`?\(|チェックリスト版\()(\d+)列|(\d+)列版')


def test_台帳の列数の記述がschemaと一致する():
    """README は台帳の列数を何度も書く。1か所でも古いと検算がすり抜ける
    (実測: 「57列 / 24列」と書いたまま実体は 62列 / 32列 になっていた)。"""
    full = {int(x) for x in FULL_CLAIM.findall(TEXT)}
    chk = {int(x or y) for x, y in CHECKLIST_CLAIM.findall(TEXT)}
    assert full, 'README から詳細版の列数の記述が消えている'
    assert chk, 'README からチェックリスト版の列数の記述が消えている'
    assert full == {len(schema.FULL_COLUMNS)}, \
        f'詳細版の列数 {sorted(full)} が実際の {len(schema.FULL_COLUMNS)} と合わない'
    assert chk <= {len(schema.CHECKLIST_COLUMNS), len(schema.FULL_COLUMNS)}, \
        f'チェックリスト版の列数 {sorted(chk)} が実際の {len(schema.CHECKLIST_COLUMNS)} と合わない'


def test_列数の検算例が正しい列数を使っている():
    """`awk NF!=N` は行追加のたびに回す検算。N がずれると常に無言で通る。"""
    got = re.findall(r'NF\s*!=\s*(\d+)', TEXT)
    assert got, 'README から列数の検算例が消えている'
    assert set(got) == {str(len(schema.FULL_COLUMNS))}, \
        f'検算例の列数 {set(got)} が実際の {len(schema.FULL_COLUMNS)} と合わない'


def test_README_が触れる列名が実在する():
    """列を統合・改名したのに README が旧名で残ると、その手順は実行できない
    (実測: `auth_response_variance` / `data_target` / `data_op_detail` が該当した)。"""
    named = _column_like() - NOT_FULL_COLUMNS - NOT_A_COLUMN
    missing = sorted(n for n in named if n not in schema.FULL_COLUMNS)
    assert not missing, f'README が実在しない列名を使っている: {missing}'


def _column_like():
    """列名らしい語だけに絞る。関数名や設定キーを巻き込まないための当たり表。"""
    prefixes = ('sec_', 'test_', 'auth_', 'data_', 'impl_', 'last_commit',
                'input_', 'audit_', 'csrf_', 'ssrf_', 'redirect_', 'resource_',
                'triggers_', 'bola_', 'api_', 'path_', 'query_', 'body_',
                'request_', 'response_', 'oauth_', 'cache_', 'config_',
                'category_', 'release_', 'priority', 'dynamic_', 'access_',
                'restricted_', 'idempotency', 'deprecated', 'side_effects')
    return {w for w in re.findall(r'`([a-z][a-z_0-9]{3,})`', TEXT)
            if w.startswith(prefixes)}


def test_派生列が手編集禁止として説明されている():
    """「手編集しても消える列」の説明。抜けがあると、消える列を人が直し続ける。
    連番の列は `test_normal`〜`test_gap` のような範囲表記でもよい。"""
    for col in schema.DERIVED_COLUMNS:
        assert col in TEXT or f'`{schema.DERIVED_COLUMNS[2]}`〜`{schema.DERIVED_COLUMNS[-2]}`' in TEXT, \
            f'派生列 {col} が README で説明されていない'
    assert '手編集しない' in TEXT or '直接編集しない' in TEXT


def _order_in_procedure(*names):
    """『ケース1』のコードブロックに現れる順を返す。"""
    start = TEXT.index('## ケース1:')
    block = TEXT[start:TEXT.index('## ケース1b')]
    return [block.index(n) for n in names]


def test_ケース1の実行順が依存関係どおり():
    """`prioritize.py` は `test_gap` を読むので `test_coverage.py` が先。
    逆順に書かれていると、1回目の実行で優先度が1世代古い値になる。"""
    tc, pr, bc = _order_in_procedure(
        'test_coverage.py', 'prioritize.py', 'build_checklist.py')
    assert tc < pr < bc, \
        'ケース1 の実行順が test_coverage → prioritize → build_checklist になっていない'


def test_静的検知の手順が案内されている():
    """実機 url_map だけでは、config で無効な経路の漏れを検出できない。"""
    assert 'detect_routes.py' in TEXT
    assert 'detect_allow.json' in TEXT


def test_実装を触ったときの順序が明記されている():
    """`enrich_git.py` は `impl_line` の指す関数のコミットを引く。
    `refresh_impl.py` を先に回さないと手前の関数のコミットを拾う。"""
    ri = TEXT.index('refresh_impl.py')
    eg = TEXT.index('enrich_git.py')
    assert ri < eg
    assert '★順序が重要' in TEXT or '必ず `refresh_impl.py` が先' in TEXT


def test_公開してはいけないものの注意が残っている():
    """このリポジトリは public。台帳を置かない前提が消えたら手順ごと危険になる。"""
    assert 'public' in TEXT
    assert 'WEKO_API_INVENTORY_DIR' in TEXT
    assert '--summary-only' in TEXT
