"""tools/claude-review のテスト共通フィクスチャ。"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def graphql_payload():
    return json.loads((FIXTURES / "pr1905_graphql.json").read_text(encoding="utf-8"))


@pytest.fixture
def diff_text():
    return (FIXTURES / "pr1905.diff").read_text(encoding="utf-8")
