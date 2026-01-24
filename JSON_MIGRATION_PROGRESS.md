# JSON to orjson Migration Progress

## 移行状況サマリー (2026-01-25 - 最終更新)

### ✅ 完了したフェーズ

#### Phase 1: 準備段階
- ✅ orjsonを requirements-devel.txt に追加
- ✅ 互換性レイヤー作成: `modules/weko-records/weko_records/json_utils.py`
- ✅ ベンチマークツール作成: `tools/benchmark_json.py`

#### Phase 2: パフォーマンスクリティカルなAPIエンドポイント
- ✅ `modules/invenio-records-rest/invenio_records_rest/views.py` - 11箇所のjson使用をorjsonに移行
- ✅ `modules/weko-workflow/weko_workflow/rest.py` - importとjson.loadsを移行
- ✅ `modules/weko-search-ui/weko_search_ui/rest.py` - importとjson.dumpsを移行

#### Phase 3: ビジネスロジック層
- ✅ `modules/weko-records/weko_records/api.py` - コアAPIのjson使用をorjsonに移行
- ✅ `modules/weko-workflow/weko_workflow/views.py` - importと8箇所の使用箇所を移行

#### Phase 4-5: その他の重要ファイル（NEW！）
- ✅ `modules/weko-workflow/weko_workflow/utils.py` - 7箇所を移行
- ✅ `modules/weko-search-ui/weko_search_ui/utils.py` - 17箇所を移行
- ✅ `modules/weko-search-ui/weko_search_ui/tasks.py` - 3箇所を移行
- ✅ `modules/weko-search-ui/weko_search_ui/admin.py` - 3箇所を移行
- ✅ `modules/weko-records-ui/weko_records_ui/api.py` - 1箇所を移行
- ✅ `modules/weko-schema-ui/weko_schema_ui/schema.py` - 4箇所を移行
- ✅ `modules/weko-schema-ui/weko_schema_ui/rest.py` - 2箇所を移行

### 📊 移行完了ファイル一覧

**コアファイル (12ファイル):**
1. invenio-records-rest/views.py
2. weko-workflow/rest.py
3. weko-workflow/views.py
4. weko-workflow/utils.py
5. weko-search-ui/rest.py
6. weko-search-ui/utils.py
7. weko-search-ui/tasks.py
8. weko-search-ui/admin.py
9. weko-records/api.py
10. weko-records-ui/api.py
11. weko-schema-ui/schema.py
12. weko-schema-ui/rest.py

**合計移行箇所数: 約70箇所以上**

### 🎯 残っている作業（低優先度）

以下のファイルにはまだjson使用箇所が残っていますが、**パフォーマンスへの影響は限定的**です：

**テストファイル:**
- 各モジュールの `tests/` ディレクトリ配下
- テストヘルパーファイル (helpers.py, conftest.py等)

**ツール・スクリプト:**
- `tools/` 配下のスクリプト（benchmark_json.py以外）
- `scripts/demo/` 配下のスクリプト

**その他:**
- 一部のマイナーなモジュール
- ドキュメント生成関連

### 📊 期待される効果

主要なパフォーマンスクリティカルな箇所がすべて完了したため、以下の改善が見込まれます：

- **API応答速度**: 2-3倍の高速化
- **メモリ使用量**: 20-30%削減
- **スループット**: 大量データ処理時の大幅な改善
- **CPU使用率**: JSON処理時の負荷軽減

### ⚠️ 重要な変更点

1. **orjsonの戻り値**
   - `orjson.dumps()` は `bytes` を返すため、文字列が必要な場合は `.decode('utf-8')` が必要
   - Redisへの保存時は、既に `bytes` なのでそのまま使用可能

2. **オプション指定**
   - インデント: `option=orjson.OPT_INDENT_2`
   - ソート: `option=orjson.OPT_SORT_KEYS`
   - 複数指定: `option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS`

3. **後方互換性**
   - 標準ライブラリのjsonが必要な場合は、`import json as stdlib_json` で残すことも可能
   - 互換性レイヤー `weko_records.json_utils` を使えば、既存コードの変更を最小限にできる

### 📝 コミットメッセージ例

```
feat: Migrate from json to orjson for performance improvement

Phase 1-3 complete:
- Add orjson dependency and compatibility layer
- Migrate performance-critical API endpoints (invenio-records-rest, weko-workflow, weko-search-ui)
- Migrate core business logic (weko-records API)
- Create benchmark tool for performance measurement

Expected improvements:
- 2-3x faster JSON serialization/deserialization
- Reduced memory usage
- Better API response times

Related: #ISSUE_NUMBER
```

### 🔗 関連ファイル

- 互換性レイヤー: [weko_records/json_utils.py](modules/weko-records/weko_records/json_utils.py)
- ベンチマークツール: [tools/benchmark_json.py](tools/benchmark_json.py)
- 依存関係: [requirements-devel.txt](requirements-devel.txt)
