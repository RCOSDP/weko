# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module tests."""
import pytest
from flask_babelex import gettext as _
from weko_workspace.utils import *
from weko_workspace.defaultfilters import merge_default_filters
from weko_workspace.config import WEKO_WORKSPACE_DEFAULT_FILTERS as DEFAULT_FILTERS


# ===========================def merge_default_filters():=====================================
@pytest.mark.parametrize('default_con, expected_response', [
    # シナリオ1: default_conが空の場合、デフォルトテンプレートを返す
    (
        {},
        {key: dict(value) for key, value in DEFAULT_FILTERS.items()}
    ),
    # シナリオ2: 単一選択フィールドを更新
    (
        {
            "favorite": True,
            "peer_review": False
        },
        {
            **{key: dict(value) for key, value in DEFAULT_FILTERS.items()},
            "favorite": {**DEFAULT_FILTERS["favorite"], "default": "あり"},
            "peer_review": {**DEFAULT_FILTERS["peer_review"], "default": "なし"}
        }
    ),
    # シナリオ3: 複数選択フィールドを更新
    (
        {
            "resource_type": ["article", "dataset", "invalid_type"]
        },
        {
            **{key: dict(value) for key, value in DEFAULT_FILTERS.items()},
            "resource_type": {
                **DEFAULT_FILTERS["resource_type"],
                "default": ["article", "dataset"]
            }
        }
    ),
    # シナリオ4: すべての単一選択フィールドを更新
    (
        {
            "peer_review": True,
            "related_to_paper": False,
            "related_to_data": None,
            "file_present": True,
            "favorite": False
        },
        {
            **{key: dict(value) for key, value in DEFAULT_FILTERS.items()},
            "peer_review": {**DEFAULT_FILTERS["peer_review"], "default": "あり"},
            "related_to_paper": {**DEFAULT_FILTERS["related_to_paper"], "default": "なし"},
            "related_to_data": {**DEFAULT_FILTERS["related_to_data"], "default": None},
            "file_present": {**DEFAULT_FILTERS["file_present"], "default": "あり"},
            "favorite": {**DEFAULT_FILTERS["favorite"], "default": "なし"}
        }
    ),
    # シナリオ5: default_conに存在しないキーを含む場合、無視する
    (
        {
            "favorite": True,
            "unknown_key": "value"
        },
        {
            **{key: dict(value) for key, value in DEFAULT_FILTERS.items()},
            "favorite": {**DEFAULT_FILTERS["favorite"], "default": "あり"}
        }
    ),
    # シナリオ6: None値を含む場合
    (
        {
            "favorite": None,
            "resource_type": None
        },
        {
            **{key: dict(value) for key, value in DEFAULT_FILTERS.items()},
            "favorite": {**DEFAULT_FILTERS["favorite"], "default": None},
            "resource_type": {**DEFAULT_FILTERS["resource_type"], "default": []}
        }
    ),
])
def test_merge_default_filters(default_con, expected_response):
    result = merge_default_filters(default_con)
    assert result == expected_response

    # # elif key == "resource_type": について、test_merge_default_filtersメソッドでどうしてもカバレッジ確認できないため、以下のテストを追加して確認した。
    default_con = {"favorite": True, "award_title": [], "funder_name": [], "peer_review": "", "file_present": True, "resource_type": ["conference paper"], "related_to_data": "", "related_to_paper": ""}
    result = merge_default_filters(default_con)
