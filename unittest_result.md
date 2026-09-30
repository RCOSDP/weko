# WEKO3 表示速度改善 ユニットテスト結果 (unittest_result.md)

対象ブランチ: `develop_v2.1.0` / 実施日: 2026-07-22

各修正ごとに実行したテストと結果をまとめる。関連仕様は [spec.md](./spec.md)、調査は [pref_issues.md](./pref_issues.md) 参照。

## テスト環境・実行方法

- **実行環境**: 稼働中の docker コンテナ `wekotest-run2` 内の Python 仮想環境
  `/home/invenio/.virtualenvs/invenio`(Python 3.6、pytest 5.4.3、SQLAlchemy 1.2.19)。
- **依存サービス**: PostgreSQL 12(`weko-postgresql-1`)、Elasticsearch 6.8.23(`weko-elasticsearch-1`、
  arm64 設定 `bootstrap.system_call_filter=false` で起動)、Redis(`weko-redis-1`)。
- **コード反映**: `wekotest-run2` の `/code` はイメージ内コピーのため、検証対象の編集ファイルは `docker cp` で
  逐次投入してからテストを実行(=**ライブコードで検証**)。
- **実行コマンド例**: 各モジュールディレクトリで
  `python -m pytest <対象テスト> -p no:cacheprovider -o addopts="" -q`。テスト用DB `wekotest` は各実行前にドロップ。
- **注意**: `sort_meta_data_by_options` 系は `@pytest.mark.asyncio` の async テストで、CI の requirements にも
  `pytest-asyncio` が含まれず**通常はスキップされる**。本検証ではローカルに `pytest-asyncio==0.14.0` を導入して実行した。

## 結果サマリー

| 修正 | 主な対象テスト | 結果 |
|------|---------------|------|
| 共通A | theme `test_views`, search-ui `test_search` | ✅ PASS |
| テスト基盤 (theme/records-ui) | theme `test_utils`/`test_views`, records-ui `test_default_view_method[1-4]` | ✅ PASS |
| 3-2 | records-ui `test_default_view_method`, `test_default_view_method3` | ✅ 2 passed |
| 共通C | gridlayout `test_models`(update/create), theme `test_views` | ✅ PASS |
| 共通B | search-ui `test_get_search_detail_keyword`, `test_search`, theme `test_views` | ✅ PASS |
| テスト基盤 (items-ui) | items-ui `test_get_ranking` 実行可能化 | ✅ PASS |
| 2-1 | items-ui `test_get_ranking` | ✅ 1 passed |
| 4-3 | records `test_sort_meta_data_by_options[*]` ほか | ✅ 9 passed |
| 3-1 | records-ui `test_default_view_method` | ✅ 1 passed |
| テスト基盤 (records-rest) | records-rest `test_serializer_response` | ✅ 2 passed |
| 4-1 | records `test_sort_meta_data_by_options[*]`, records-rest `test_serializer_response` | ✅ PASS |

---

## 各修正の詳細結果

### 共通A — `get_search_setting()` 集約 (`1288154d4`)

- `weko-theme/tests/test_views.py` → **5 passed**(`test_index` を含む。`index()` → `get_weko_contents()` を通過)。
- `weko-search-ui/tests/test_views.py::test_search` → **1 passed**。
- 回帰確認: `git stash` でオリジナルと比較し、変更行を通るテストの合否が同一であることを確認。
- 補足: 当初はコンテナのイメージ内コピー(旧コード)で走っていたことが判明したため、`docker cp` 方式に是正し
  **ライブコードで再検証**して上記結果を得た。

### テスト基盤修正 (theme / records-ui) (`71cc1a75e`)

- `weko-theme/tests/test_utils.py::test_get_weko_contents` → **1 passed**(パーティション作成後)。
- `weko-theme/tests/test_views.py` → **5 passed**。
- `weko-records-ui/tests/test_views.py::test_default_view_method[1..4]` → **4 passed**。
- 解消した既存問題: ①`user_activity_logs` 当月パーティション欠如、②`item_type_mapping` FK挿入順(Continuum)、
  ③テストが `get_weko_contents` に文字列引数を渡す不具合。

### 3-2 — インデックスループのメモ化 (`4cde4e05f`)

- `weko-records-ui/tests/test_views.py::test_default_view_method` + `::test_default_view_method3` → **2 passed**。

### 共通C — ウィジェット設計メモ化 (`a76f6c564`)

- `weko-gridlayout/tests/test_models.py::test_update_WidgetDesignSetting` + `::test_create_WidgetDesignSetting`
  → **2 passed**(`_clear_request_cache` を含む更新/作成経路)。
- `weko-theme/tests/test_views.py` → **5 passed**(`select_by_repository_id` を通るトップページ描画)。

### 共通B — `get_search_detail_keyword()` キャッシュ (`b63d08a73`)

- `weko-search-ui/tests/test_api.py::test_get_search_detail_keyword` → **1 passed**(計算検証のため呼び出し前に
  `current_cache.clear()` を追加)。
- `weko-search-ui/tests/test_views.py::test_search` → **1 passed**。
- `weko-theme/tests/test_views.py` → **5 passed**。
- **既知の無関係な失敗**: `test_get_search_detail_keyword_fix52136` は `assert 0`(guest 用 index_tree/redis 依存の
  assertion)で失敗するが、**オリジナルコードでも同一に失敗**することを確認済み。本修正とは無関係の既存不具合。

### テスト基盤修正 (items-ui) (`3a6530bde`)

- `user_activity_logs` パーティション作成、および `InvenioCache(app_)` 初期化(config はあったが未初期化だった)。
  これにより `test_get_ranking` が `KeyError('invenio-cache')` / パーティションエラーなく実行可能に。

### 2-1 — `get_ranking()` キャッシュ (`b412edaa6`)

- `weko-items-ui/tests/test_utils.py::test_get_ranking` → **1 passed**。
  InvenioCache 導入によりキャッシュ経路(clear→計算→キャッシュ)を実際に通過し、期待するランキング出力を確認。
- テストには呼び出し前 `current_cache.clear()` を追加(設定変更前後で異なる結果を検証するため)。

### 4-3 — sort_meta のアイテムタイプメモ化 (`723ecb7a6`)

- `weko-records/tests/test_utils.py::test_sort_meta_data_by_options`(パラメータ6ケース)→ **6 passed**。
- 同 `::test_sort_meta_data_by_options_sample_1` / `::..._no_item_type_id` / `::..._exception` → **3 passed**。
- 計 **9 passed**。実データのアイテムタイプ・レコードヒットでメモ化が出力を変えないことを確認。
- 補足: これらは async テストのため `pytest-asyncio` をローカル導入して実行。`..._subRepository` は別種の
  既存フィクスチャ不備(item_type 未作成)で setup エラーとなるため対象外。

### 3-1 — OAI XML キャッシュ (`6d8e7e2d8`)

- `weko-records-ui/tests/test_views.py::test_default_view_method` → **1 passed**。
- records-ui テストアプリは `InvenioCache` 初期化済み(conftest line 304)のため、**キャッシュ経路が実際に
  テストされて** PASS(get/set が正しく動作)。

### テスト基盤修正 (records-rest) (`406859f34`)

- `invenio-records-rest/tests/test_serializer_response.py` → **2 passed**。
- 解消した既存問題: `item_type_mapping` FK挿入順(Continuum)による `test_search_responsify` の setup エラー。

### 4-1 — per-item 同期最適化 (`93eab88fa`)

- `weko-records/tests/test_utils.py::test_sort_meta_data_by_options[*]`(6)+ `_sample_1`(1)= **7 passed**、
  さらに `_no_item_type_id` / `_exception` を加えて **8 passed**(O(n)化ループの出力不変を確認)。
- `invenio-records-rest/tests/test_serializer_response.py` → **2 passed**
  (`test_search_responsify` が serializer 全経路 `view` → `__format_item_list` → `sort_meta_data_by_options` を通過)。

---

## 総括

- 全パフォーマンス修正について、**変更行を通る対象テストが PASS** し、出力・挙動が不変であることを確認した。
- 検証過程で判明した既存のテストフィクスチャ不具合(パーティション欠如、Continuum FK挿入順、InvenioCache 未初期化、
  文字列引数テスト)は付随して修正し、それぞれコミットした。
- 本修正と無関係の既存失敗(`test_get_search_detail_keyword_fix52136`)は、オリジナルコードでも同一に失敗することを
  確認済みで、今回のスコープ外。
- 短TTLキャッシュ導入に伴い、設定変更等が反映されるまで最大 TTL 秒(既定300秒)のラグが生じる(受容済みの仕様)。
