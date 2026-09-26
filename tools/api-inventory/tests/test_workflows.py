# -*- coding: utf-8 -*-
"""ワークフローの原本(ci/)と実体(.github/workflows/)がずれていないかを検査する。

GitHub Actions が動かすのは `.github/workflows/` 側だけで、`ci/` 側は原本に過ぎない。
片方だけ直すと、手順書と原本を読んだ人は「その検査は回っている」と思い込む。
実際に `detect_routes.py` の段が原本にだけ入り、実体の drift ワークフローからは
抜けたまま、ソース由来の経路検知が CI で一度も走っていなかった。
"""
import os

import pytest

from conftest import SCRIPTS

TOOL = os.path.dirname(SCRIPTS)
CI = os.path.join(TOOL, 'ci')
# リポジトリのルート直下にある(ツールだけ取り出した環境には無い)。
WORKFLOWS = os.path.join(os.path.dirname(os.path.dirname(TOOL)), '.github', 'workflows')

ORIGINALS = sorted(f for f in os.listdir(CI) if f.endswith('.yml'))


def test_原本のワークフローがある():
    assert ORIGINALS, f'{CI} に .yml が無い'


@pytest.mark.skipif(not os.path.isdir(WORKFLOWS),
                    reason='.github/workflows が無い(ツールだけ取り出した環境)')
@pytest.mark.parametrize('name', ORIGINALS)
def test_原本と実体が一致する(name):
    actual = os.path.join(WORKFLOWS, name)
    assert os.path.isfile(actual), \
        f'.github/workflows/{name} が無い。原本を置いただけでは動かない'
    with open(os.path.join(CI, name), encoding='utf-8') as f:
        original = f.read()
    with open(actual, encoding='utf-8') as f:
        assert f.read() == original, \
            f'ci/{name} と .github/workflows/{name} がずれている。' \
            '変更したら両方に反映すること(ci/README.md §2 の 5)'
