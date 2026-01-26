#!/usr/bin/env python
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

"""JSON処理のパフォーマンスベンチマークツール.

jsonライブラリとorjsonライブラリのパフォーマンスを比較します。
様々なデータサイズとデータ構造でベンチマークを実行し、
移行による性能改善を定量的に評価します。
"""

import json
import orjson
import time
import sys
from typing import Dict, Any, List


def generate_test_data(size: str = "medium") -> Dict[str, Any]:
    """テストデータを生成します.

    Args:
        size: データサイズ ('small', 'medium', 'large')

    Returns:
        テストデータの辞書
    """
    sizes = {
        "small": 100,
        "medium": 1000,
        "large": 10000,
    }

    count = sizes.get(size, 1000)

    return {
        "metadata": {
            "title": "研究成果リポジトリシステム WEKO3",
            "description": "これはWEKO3のベンチマークテストデータです",
            "language": "ja",
            "version": "1.0.0",
        },
        "items": [
            {
                "id": i,
                "title": f"アイテム {i}",
                "author": f"著者 {i}",
                "keywords": ["キーワード1", "キーワード2", "キーワード3"],
                "metadata": {
                    "created": "2026-01-25T00:00:00Z",
                    "updated": "2026-01-25T00:00:00Z",
                    "status": "published",
                },
            }
            for i in range(count)
        ],
        "statistics": {
            "total_items": count,
            "total_authors": count,
            "total_downloads": count * 10,
        },
    }


def benchmark_dumps(data: Dict[str, Any], iterations: int = 100) -> Dict[str, float]:
    """dumps処理のベンチマークを実行します.

    Args:
        data: テストデータ
        iterations: 反復回数

    Returns:
        各ライブラリの処理時間
    """
    print(f"\n=== dumps ベンチマーク (反復: {iterations}回) ===")

    # json.dumps
    start = time.time()
    for _ in range(iterations):
        json.dumps(data)
    json_time = time.time() - start
    print(f"json.dumps:   {json_time:.4f}秒")

    # orjson.dumps
    start = time.time()
    for _ in range(iterations):
        orjson.dumps(data)
    orjson_time = time.time() - start
    print(f"orjson.dumps: {orjson_time:.4f}秒")

    speedup = json_time / orjson_time if orjson_time > 0 else 0
    print(f"高速化率:     {speedup:.2f}x")

    return {"json": json_time, "orjson": orjson_time, "speedup": speedup}


def benchmark_loads(json_str: str, iterations: int = 100) -> Dict[str, float]:
    """loads処理のベンチマークを実行します.

    Args:
        json_str: JSON文字列
        iterations: 反復回数

    Returns:
        各ライブラリの処理時間
    """
    print(f"\n=== loads ベンチマーク (反復: {iterations}回) ===")

    # json.loads
    start = time.time()
    for _ in range(iterations):
        json.loads(json_str)
    json_time = time.time() - start
    print(f"json.loads:   {json_time:.4f}秒")

    # orjson.loads
    json_bytes = json_str.encode("utf-8")
    start = time.time()
    for _ in range(iterations):
        orjson.loads(json_bytes)
    orjson_time = time.time() - start
    print(f"orjson.loads: {orjson_time:.4f}秒")

    speedup = json_time / orjson_time if orjson_time > 0 else 0
    print(f"高速化率:     {speedup:.2f}x")

    return {"json": json_time, "orjson": orjson_time, "speedup": speedup}


def benchmark_roundtrip(data: Dict[str, Any], iterations: int = 100) -> Dict[str, float]:
    """dumps→loads の往復処理のベンチマークを実行します.

    Args:
        data: テストデータ
        iterations: 反復回数

    Returns:
        各ライブラリの処理時間
    """
    print(f"\n=== 往復処理ベンチマーク (反復: {iterations}回) ===")

    # json
    start = time.time()
    for _ in range(iterations):
        json.loads(json.dumps(data))
    json_time = time.time() - start
    print(f"json往復:     {json_time:.4f}秒")

    # orjson
    start = time.time()
    for _ in range(iterations):
        orjson.loads(orjson.dumps(data))
    orjson_time = time.time() - start
    print(f"orjson往復:   {orjson_time:.4f}秒")

    speedup = json_time / orjson_time if orjson_time > 0 else 0
    print(f"高速化率:     {speedup:.2f}x")

    return {"json": json_time, "orjson": orjson_time, "speedup": speedup}


def run_all_benchmarks(size: str = "medium", iterations: int = 100):
    """全てのベンチマークを実行します.

    Args:
        size: データサイズ ('small', 'medium', 'large')
        iterations: 反復回数
    """
    print(f"\n{'='*60}")
    print(f"JSON処理ベンチマーク - データサイズ: {size}")
    print(f"{'='*60}")

    # テストデータ生成
    print("\nテストデータを生成中...")
    data = generate_test_data(size)
    json_str = json.dumps(data)
    data_size_kb = len(json_str) / 1024
    print(f"データサイズ: {data_size_kb:.2f} KB")

    # ベンチマーク実行
    dumps_results = benchmark_dumps(data, iterations)
    loads_results = benchmark_loads(json_str, iterations)
    roundtrip_results = benchmark_roundtrip(data, iterations)

    # サマリー表示
    print(f"\n{'='*60}")
    print("ベンチマーク結果サマリー")
    print(f"{'='*60}")
    print(f"dumps高速化率:     {dumps_results['speedup']:.2f}x")
    print(f"loads高速化率:     {loads_results['speedup']:.2f}x")
    print(f"往復処理高速化率:  {roundtrip_results['speedup']:.2f}x")
    print(f"\n平均高速化率:      {(dumps_results['speedup'] + loads_results['speedup'] + roundtrip_results['speedup']) / 3:.2f}x")


def main():
    """メイン関数."""
    if len(sys.argv) > 1:
        size = sys.argv[1]
        if size not in ["small", "medium", "large"]:
            print("使用方法: python benchmark_json.py [small|medium|large]")
            sys.exit(1)
    else:
        size = "medium"

    iterations = 100
    if len(sys.argv) > 2:
        try:
            iterations = int(sys.argv[2])
        except ValueError:
            print("反復回数は整数で指定してください")
            sys.exit(1)

    run_all_benchmarks(size, iterations)


if __name__ == "__main__":
    main()
