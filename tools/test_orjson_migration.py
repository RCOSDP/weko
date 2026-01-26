#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
orjson移行のためのテストスイート

このスクリプトは、jsonからorjsonへの移行が正しく行われたことを検証します。
"""

import sys
import subprocess


def run_benchmark():
    """ベンチマークを実行してパフォーマンス改善を確認"""
    print("\n" + "="*60)
    print("ベンチマーク実行中...")
    print("="*60)
    
    try:
        result = subprocess.run(
            ["python", "tools/benchmark_json.py", "medium", "100"],
            capture_output=True,
            text=True,
            timeout=300
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"エラー: {result.stderr}", file=sys.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print("エラー: ベンチマークがタイムアウトしました", file=sys.stderr)
        return False
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        return False


def check_imports():
    """orjsonがインストールされているか確認"""
    print("\n" + "="*60)
    print("orjsonインストール確認中...")
    print("="*60)
    
    try:
        import orjson
        print(f"✓ orjson バージョン: {orjson.__version__}")
        return True
    except ImportError:
        print("✗ orjsonがインストールされていません", file=sys.stderr)
        print("インストール方法: pip install orjson==3.9.15", file=sys.stderr)
        return False


def test_compatibility_layer():
    """互換性レイヤーのテスト"""
    print("\n" + "="*60)
    print("互換性レイヤーのテスト中...")
    print("="*60)
    
    try:
        # パスを追加
        sys.path.insert(0, 'modules/weko-records')
        from weko_records.json_utils import dumps, loads, dump, load
        
        # テストデータ
        test_data = {
            "name": "テスト",
            "value": 123,
            "items": [1, 2, 3],
            "nested": {"key": "値"}
        }
        
        # dumps/loadsのテスト
        serialized = dumps(test_data)
        deserialized = loads(serialized)
        assert deserialized == test_data, "dumps/loadsのテスト失敗"
        print("✓ dumps/loads テスト成功")
        
        # dump/loadのテスト
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            dump(test_data, f)
            temp_path = f.name
        
        with open(temp_path, 'r') as f:
            loaded_data = load(f)
        assert loaded_data == test_data, "dump/loadのテスト失敗"
        print("✓ dump/load テスト成功")
        
        # クリーンアップ
        import os
        os.unlink(temp_path)
        
        return True
    except Exception as e:
        print(f"✗ 互換性レイヤーのテスト失敗: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def test_migration():
    """移行されたファイルのインポートテスト"""
    print("\n" + "="*60)
    print("移行ファイルのインポートテスト中...")
    print("="*60)
    
    migrated_files = [
        ('invenio-records-rest', 'invenio_records_rest.views'),
        ('weko-workflow', 'weko_workflow.rest'),
        ('weko-search-ui', 'weko_search_ui.rest'),
        ('weko-records', 'weko_records.api'),
    ]
    
    success_count = 0
    for module_name, import_path in migrated_files:
        try:
            # モジュールのパスを追加
            sys.path.insert(0, f'modules/{module_name}')
            __import__(import_path)
            print(f"✓ {import_path} インポート成功")
            success_count += 1
        except Exception as e:
            print(f"✗ {import_path} インポート失敗: {e}", file=sys.stderr)
    
    print(f"\n結果: {success_count}/{len(migrated_files)} ファイルのインポート成功")
    return success_count == len(migrated_files)


def main():
    """メイン関数"""
    print("="*60)
    print("orjson移行テストスイート")
    print("="*60)
    
    results = []
    
    # テスト実行
    results.append(("orjsonインストール確認", check_imports()))
    results.append(("互換性レイヤー", test_compatibility_layer()))
    results.append(("移行ファイルインポート", test_migration()))
    results.append(("ベンチマーク", run_benchmark()))
    
    # 結果サマリー
    print("\n" + "="*60)
    print("テスト結果サマリー")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n合計: {passed}/{total} テスト成功")
    
    if passed == total:
        print("\n🎉 全てのテストが成功しました！")
        return 0
    else:
        print("\n⚠️ 一部のテストが失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
