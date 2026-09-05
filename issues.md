# ユニットテスト全面実行で見つかった製品側の問題

`unit-tests.yml` が 47 モジュールすべてのユニットテストを回すようになり、
これまで一度も実行されていなかったテストが大量に走った。その過程で
**テストコードでは直せない製品側の不具合**が見つかったので、ここに残す。

該当するテストは削除も無効化もせず `pytest.mark.xfail` にして、理由を
マーカーの `reason` に書いてある。CI は緑になるが、直せば xfail が xpass に
変わるので気付ける。

対象コミット: `fix/issue62764` (PR #1911)
記録日: 2026-09-03

---

## A. 製品コードの不具合 (xfail 中)

### A-1. invenio-files-rest: 例外を握り潰した後に未代入のローカルを参照する

- 場所: `modules/invenio-files-rest/invenio_files_rest/views.py`
  - multipart の POST: `except Exception` (857行) → `data=multipart` (861行)
  - object の PUT: `except Exception` (680行) → `data=obj` (694行)
- 症状:
  `MultipartObject.create()` / `ObjectVersion` の生成が入力を拒否すると、
  `except Exception` がログを出してロールバックするだけで先へ進み、
  代入されていない `multipart` / `obj` を `make_response()` に渡して
  `UnboundLocalError` になる。REST のエラーハンドラが 400 を返していたのが
  **500 に変わっている**。
  さらに、アップロードの読み取り中に失敗した場合も同じ経路で握り潰されるため、
  **失敗したアップロードが成功として応答される**（`test_put_error` /
  `test_already_exhausted_input_stream` が該当）。
- 影響: 不正な partSize・quota 超過・ロック済みバケットへの POST、
  読み取り中に切れたアップロード。
- xfail: `tests/test_views_multipart.py` の `SWALLOWED_ERROR_XFAIL` /
  `SWALLOWED_ERROR_SILENT_XFAIL`、`tests/test_views_objectversion.py` の同名マーカー。計 6 件。
- 直し方: `except` 節で 4xx を返して抜けるか、少なくとも `multipart`/`obj` を
  先に `None` で初期化して分岐する。

### A-2. invenio-indexer: BulkConnectionError を str() すると IndexError

- 場所: `modules/invenio-indexer/invenio_indexer/api.py`
  - `BulkBaseException.__init__` (749-770行) が
    `super().__init__(str(original_exception))` と引数 1 つで基底を初期化する
  - `BulkConnectionError` (773行) / `BulkConnectionTimeout` (791行) は
    elasticsearch の `TransportError` を継承しており、その `__str__` は
    `self.args[1]` を読む
  - 例外ハンドラ `except (BulkConnectionError, ConnectionError) as ce:` (372行)
    の**先頭行**が `logger.error(f"...{str(ce)}...")`
- 症状: 一括インデックス中に本物の接続エラーが起きると、それを報告するはずの
  ハンドラ自身が `IndexError: tuple index out of range` で落ちる。
  成功数・失敗数の集計も行われない。
- xfail: `tests/test_api.py` の `CONNECTION_ERROR_XFAIL`。
  `test_process_bulk_queue_connection_error` /
  `test_process_bulk_queue_connection_error_no_errors` の 2 件。
- 直し方: `BulkBaseException.__init__` で `TransportError` が期待する
  `(status_code, error, info)` の形を渡すか、ハンドラ側で `str(ce)` をやめる。

### A-3. invenio-resourcesyncclient: mapper.map() を引数なしで呼んでいる

- 場所: `modules/invenio-resourcesyncclient/invenio_resourcesyncclient/utils.py:338, 377`
- 症状: `JPCOARMapper.map(self, version)` は `version` が必須
  (`modules/invenio-oaiharvester/invenio_oaiharvester/harvester.py:1502`) なのに
  `mapper.map()` と呼んでおり、JPCOAR レコードの resync で `TypeError`。
  同じマッパーを呼ぶ invenio-oaiharvester (`tasks.py:226`) と
  weko-search-ui (`utils.py:1379`) は `version` を渡しているので、
  このモジュールだけ追随漏れ。
- xfail: `tests/test_utils.py::test_process_item`。
- 直し方: 対象スキーマのバージョン ("1.0" / "2.0") を渡す。

### A-4. invenio-resourcesyncserver: 2 か所の書き間違い

- `modules/invenio-resourcesyncserver/invenio_resourcesyncserver/utils.py:203`
  `if len(tz_parts > 1):` — `len(tz_parts) > 1` の書き間違い。
  タイムゾーンを `-` 付きで書いた日付を渡すと `TypeError`。
  xfail: `tests/test_utils.py::test_get_timezone_minus_offset`
- `modules/invenio-resourcesyncserver/invenio_resourcesyncserver/admin.py:83`
  `result` は `if resource:` の中でしか代入されないのに、その外の
  `jsonify(message=result.get('message'), ...)` で参照している。
  存在しない resource_id を渡すと `success=False` ではなく `UnboundLocalError`。
  同じ形が 151行・167行にもある。
  xfail: `tests/test_admin.py::test_update_AdminResourceListView_unknown_resource`

### A-5. weko-gridlayout: 存在しないモデルメソッドを呼んでいる

- 場所: `modules/weko-gridlayout/weko_gridlayout/api.py`
  - `WidgetItems.delete` (162行) → `WidgetItem.delete(...)`
  - `WidgetItems.is_existed` (211行) → `WidgetItem.get_by_repo_and_type(...)`
- 症状: どちらも `weko_gridlayout/models.py` の `WidgetItem` に存在しない。
  呼べば必ず `AttributeError`。
- xfail: `tests/test_api.py` の `MISSING_MODEL_METHOD_XFAIL` (2 件)。

### A-6. weko-gridlayout: VARCHAR の列を int と比較している

- 場所: `modules/weko-gridlayout/weko_gridlayout/models.py:615`
  `WidgetDesignPage.update_settings_by_repository_id` が
  `filter_by(repository_id=int(repository_id))` としているが、
  `repository_id` は `db.String(100)` (474行)。
- 症状: PostgreSQL が
  `operator does not exist: character varying = integer` を返し、
  `except` がそれを握り潰すので**このメソッドは常に False を返す**。
  SQLite なら通るので、テストが動いていなかった間は気付けなかった。
- xfail: `tests/test_models.py::test_update_settings_by_repository_id`

### A-7. WEKO の alembic に、作られないテーブルへの ALTER がある

- 場所: `modules/weko-records/weko_records/alembic/1619a115156f_add_repository_id_column.py:23`
  `op.add_column('feedback_mail_list', ...)`
- 症状: `feedback_mail_list` を **CREATE するマイグレーションがどこにも無い**。
  この表は `db.create_all()` でしか作られないため、まっさらな DB に対して
  `invenio alembic upgrade` 相当を流すと
  `relation "feedback_mail_list" does not exist` で止まる。
- xfail: `modules/invenio-communities/tests/test_invenio_communities.py::test_alembic`
- 直し方: weko-records の alembic 履歴に `feedback_mail_list` の作成を足す。

### A-8. invenio-oaiharvester: 平文の oai_dc 要素が取り込まれない

- 場所: `modules/invenio-oaiharvester/invenio_oaiharvester/harvester.py`
  `subitem_recs` (166行)、191行・220行の `if oai_key and metadata and oai_key in metadata:`
- 症状: 属性を持たない dc 要素 (`<dc:creator>テスト, 太郎</dc:creator>` など) は
  xmltodict が**文字列**にする。`subitem_recs` は末端の分岐 (249-258行) では
  文字列を扱えるが、`creatorNames.creatorName` のような**入れ子のパス**では
  1 段目で `oai_key in metadata` が偽になり、値が捨てられる。
  title のような 1 階層のマッピングは通るので、creator / contributor / relation
  だけが落ちる。
- xfail: `tests/test_harvester.py` の `DC_PLAIN_TEXT_XFAIL` (3 件)。

### A-9. invenio-oaiharvester: アイテムタイプが常に "Multiple" になった件の影響

- 場所: `harvester.py:1442` `BaseMapper.map_itemtype()` (weko#56939 で
  レコードの resource type を見なくなり、`itemtype_map.get('Multiple')` 固定に)
- 症状: そのため、収穫したレコードは形式にかかわらず "Multiple" のアイテムタイプに
  マッピングされる。テストのフィクスチャの "Multiple"
  (`tests/data/itemtype_multiple_mapping.json`) は `jpcoar_mapping` しか持たず、
  `jpcoar_v1_mapping` も oai_dc / ddi 用のマッピングも無いため、
  それらの語彙で書かれたレコードは何も取り込めない。
- 不明点: **実運用の "Multiple" アイテムタイプが必要なマッピングを
  すべて持っているのかは未確認**。持っていなければ、jpcoar 1.0 / oai_dc / DDI の
  収穫が実際に壊れている可能性がある。
- xfail: `tests/test_harvester.py` の `MULTIPLE_ITEMTYPE_XFAIL` (3 件)、
  `tests/test_tasks.py` の同名マーカー (2 件)。

### A-10. weko-workflow: wait タブの JSON パスリテラルが不正

- 場所: `modules/weko-workflow/weko_workflow/api.py`
  `query_activities_by_tab_is_wait` の 1917-1919行あたり
  (`query_activities_by_tab_is_all` / `_todo` にも同じ形がある)
- 症状:
  ```python
  _Activity.temp_data.op("#>>")("{'metainfo', 'shared_user_ids'}")
  ```
  PostgreSQL の `#>>` は右辺を `text[]` として読む。`{'metainfo', 'shared_user_ids'}`
  というリテラルの要素は **引用符込みの `'metainfo'`** になるため、
  そんなキーは JSON に存在せず**常に NULL** を返す。
  wait タブはこれを `not_(...)` に入れて AND で連ねているので、
  NULL を否定しても NULL のままとなり、その枝は決して真にならない。
  結果、`shared_user_ids` が NULL でないアクティビティは
  **wait タブに1件も出てこない**。
  all / todo タブでは OR の一枝なので実害は出ない。
- xfail: `tests/test_api.py::TestWorkActivity::test_get_activity_list` の
  `WAIT_TAB_XFAIL` (wait タブの 2 パラメータ)。
- 直し方: `"{metainfo,shared_user_ids}"` にする。

### A-11. weko-workflow: 存在しない activity_id で 404 ではなく 500

- 場所: `modules/weko-workflow/weko_workflow/rest.py:747` `get_activity()` →
  `weko_workflow/utils.py:3846` `get_activity_display_info()`
- 症状: `Activity` が見つからないと `activity_detail` が None のまま
  `activity_detail.workflow_id` を読み、`AttributeError` で 500 になる。
  存在確認はどちらの層にも無い。
  `views.display_activity` は戻り値の None を見て弾いているが、
  `get_activity_display_info` 自身がその前に落ちる。
- xfail: `tests/test_rest.py::test_FileApplicationActivity_post`
- 直し方: `get_activity_display_info` の冒頭で activity を確認し、
  無ければ 404 を返す。

### A-12. weko-deposit: 著者名が重複し、非表示指定した名前も出る

- 場所: `modules/weko-deposit/weko_deposit/tasks.py` `_change_to_meta()`
  - 400-416行: `for name in target.get('authorNameInfo', [])`
  - 446-463行: **同じループがもう一度**あり、同じ
    `family_names` / `given_names` / `full_names` に append する
- 症状: 著者情報の一括更新でアイテムのメタデータを書き換えると、
  **著者名が重複して入る**。さらに1周目の判定が
  ```python
  if not bool(name.get('nameShowFlg', "true")):
  ```
  で、`nameShowFlg` は文字列 (`weko_authors/schema.py:39` が
  `fields.String(validate=OneOf(["true","false"]))`) のため
  `"false"` でも真になり、**非表示指定した名前が落ちない**。
  2周目は `strtobool()` を使っており、そちらは正しい。
  `[{ja,"true"}, {en,"false"}]` を渡すと `[ja, en, ja]` になる。
- xfail: `tests/test_tasks.py::TestChangeToMeta::test_change_to_meta_exists_authorNameInfo`
- 直し方: 400-416行のループを消す (446行のものが正しい)。

### A-13. weko-deposit: リトライを使い切ると UnboundLocalError

- 場所: `modules/weko-deposit/weko_deposit/tasks.py:670-687`
  ```python
  for attempt in range(retry_count):
      try:
          update_file_content(record_uuid, file_datas)
          success = True
          break
      except ConflictError: ...
      except NotFoundError: ...
      except Exception: ...
  if not success:
      current_app.logger.error(...)
  ```
- 症状: 全リトライが失敗すると `success` は一度も代入されないため、
  **その失敗を報告するはずの行**が `UnboundLocalError` で落ちる。
  invenio-files-rest の A-1 とまったく同じ形。
- xfail: `tests/test_tasks.py` の `RETRY_EXHAUSTED_XFAIL` (3 パラメータ) と
  `test_extract_pdf_and_update_file_contents`。
- 直し方: ループの前で `success = False` と初期化する。

### A-14. weko-deposit: 実体の無いファイルが1つあると 500

- 場所: `modules/weko-deposit/weko_deposit/api.py:1247` `get_content_files()`
  ```python
  except FileNotFoundError as se:
      current_app.logger.error(...)
  ```
- 症状: ストレージ上に実体が無いファイルで `storage().open()` が投げるのは
  `fs.errors.ResourceNotFoundError` で、`FileNotFoundError` では捕まらない。
  外側の `except Exception` に落ちて `abort(500)` するため、
  **1件でも実体の欠けたファイルがあるとコンテンツ抽出全体が 500 になる**。
  内側に FileNotFoundError のハンドラを置いている以上、
  1件だけ飛ばして続ける意図だったはず。
- xfail: `tests/test_api.py::TestWekoDeposit::test_get_content_files`
- 直し方: `except (FileNotFoundError, ResourceNotFoundError)` にする。

### A-15. weko-deposit: ドラフトのあるアイテムを削除すると FK 違反

- 場所: `modules/weko-deposit/weko_deposit/api.py:944-957` `WekoDeposit.delete()`
  ```python
  RecordsBuckets.query.filter_by(record_id=self.id).delete()
  ...
  bucket.remove()
  ```
- 症状: `.0` のドラフトは親レコードと同じバケットを参照する。
  `delete()` は**自分の** `RecordsBuckets` 行だけ消してからバケット本体を
  削除するので、ドラフト側の参照が残ったままとなり
  `update or delete on table "files_bucket" violates foreign key constraint
  "fk_records_buckets_bucket_id_files_bucket"` になる。
- xfail: `tests/test_api.py::TestWekoDeposit::test_delete`
- 直し方: 他に参照が残っていないか確かめてから `bucket.remove()` する。

---

## B. テスト側で回避したが、実アプリにも同じ形が残っているもの

### B-1. kombu と invenio-queues でキュータイプが食い違う

- このプロジェクトが固定している kombu の
  `kombu/compat.py:118` は `Consumer` に
  `queue_arguments={'x-queue-type': 'quorum'}` を**直書き**している。
  一方 `modules/invenio-queues/invenio_queues/queue.py:39` は引数なしで
  `Queue` を宣言する (= vhost 既定、classic)。
- 症状: 同じキューを両方が宣言するため、後から来たほうが RabbitMQ に
  `PRECONDITION_FAILED - inequivalent arg 'x-queue-type' for queue
  'stats-file-download'` で弾かれる。
  統計イベントの publish/consume がこれで止まる。
- テスト側の扱い: `modules/invenio-stats/tests/conftest.py` の
  `quorum_stats_queues` フィクスチャで、宣言を consumer 側に合わせている。
  **実アプリではこの食い違いがそのまま残っている。**
- 直し方: invenio-queues 側の宣言にも `x-queue-type` を渡すか、
  kombu の直書きを外す。

### B-2. weko-gridlayout: Content-Type ヘッダが無いと KeyError

- 場所: `modules/weko-gridlayout/weko_gridlayout/views.py:189, 264, 320`
  `if request.headers['Content-Type'] != 'application/json':`
- 症状: ヘッダを送らないリクエストで `KeyError: 'CONTENT_TYPE'` → 500。
  `.get('Content-Type')` にすべきところ。
- テスト側の扱い: `test_delete_widget_item_issue50978` はヘッダを付けて呼ぶよう
  直した。ヘッダ無しの経路は今も 500 になる。

### B-3. invenio-records-rest: PUT はどんな失敗も 500 にする

- 場所: `modules/invenio-records-rest/invenio_records_rest/views.py:1147-1151`
  `except BaseException` → `make_response(None, None, 500)`
- 症状: スキーマ検証エラーも含め、あらゆる失敗が 500 になる。
  本来 400 で返すべきものが区別できない。
- テスト側の扱い: `test_validation_error` の期待値を実際の 500 に合わせ、
  「書き込まれていないこと」だけ確かめるようにした。

### B-5. weko-records-ui: fpdf のフォントキャッシュに相対パスが焼き込まれている

- 場所: `modules/weko-records-ui/weko_records_ui/fonts/*/ipaex*.pkl`
- 症状: これは fpdf が作るフォントメトリクスのキャッシュで、中に
  生成時の **ttffile が相対パスで記録されている**。
  ```
  ttffile: modules/weko-records-ui/weko_records_ui/fonts/ipaexg00201/ipaexg.ttf
  ```
  fpdf は `add_font()` でこのキャッシュを読み、PDF 出力時にその
  `ttffile` を開くため、作業ディレクトリが「リポジトリ直下」でないと
  `FileNotFoundError` になる。カバーページ付き PDF の生成が
  起動ディレクトリに依存する。
- テスト側の扱い: `tests/conftest.py` で `FPDF_CACHE_MODE = 1`
  (キャッシュを使わない) にした。
- 直し方: この `.pkl` をリポジトリから外す (fpdf が実行時に作り直す)。
  生成環境のパスが混ざった生成物を配布物に含めない。

### B-4. weko-gridlayout の API は login_required のみ

- `/admin/save_widget_layout_setting`、`/admin/delete_widget_item`、
  `/widget/unlock` などの `blueprint_api` 側のエンドポイントは
  `@login_required` だけで、ロールによる制限が無い。
  管理画面 (`admin.py` の `WidgetSettingView`) 側には権限があるので、
  API だけ素通しになっている。
- テスト側の扱い: 403 を期待していたパラメータがあったが、
  contributor と repoadmin を拒否して generaluser を通すという筋の通らない
  並びだったので、実挙動 (全員 200) に合わせた
  (`modules/weko-gridlayout/tests/test_views.py` の `user_results1`)。
- **意図した仕様なのか、権限の付け忘れなのかは要確認。**

---

## C. CI / インフラ

### C-1. テスト1件ごとに全テーブルを作り直している

`weko-workflow/tests/conftest.py` の `db` フィクスチャは関数スコープで、
1 テストごとに `drop_all()` / `create_all()` と `drop_database()` /
`create_database()` を行う。作られるのは WEKO 全モジュール分のテーブルで、
**1 テストあたり約 22 秒**かかる。同じ形が weko-deposit / weko-records-ui /
weko-search-ui にもある。

実測 (ローカル):

| モジュール | 件数 | 所要 |
|---|---|---|
| weko-workflow | 794 | 4時間54分 |

このため `timeout-minutes` を 60 → 120 に上げても 4 モジュールが
cancelled になり、pytest-split でジョブを分割して回避した
(`.github/workflows/unit-tests.yml` の `matrix.include`)。
GitHub のジョブ上限は 6 時間なので、上限を上げる方向では解決しない。

**根治はフィクスチャのスコープ見直し** (セッションで 1 回 `create_all()` し、
テストごとに `TRUNCATE ... RESTART IDENTITY CASCADE`)。
テスト間の独立性が変わるので、まとまった検証時間が要る。

### C-2. 依存の取得が不安定

`invenio-s3` のジョブが

```
ERROR: Could not find a version that satisfies the requirement flask-oauthlib (unavailable)
```

で落ちた。`requirements2.txt` の
`-e git+https://github.com/RCOSDP/flask-oauthlib.git@add-redissentinel` の
clone に失敗したもので、前後の run では通っている。再実行で直る類だが、
git 依存が 2 件 (flask-oauthlib, pyfpdf) ある以上たまに起きる。

### C-3. テスト実行が DB の状態に敏感

CI は 1 ジョブ 1 コンテナなので毎回まっさらだが、ローカルでサービスを
使い回すと、モジュールをまたいだ `wekotest` の残骸で CI では出ない失敗が出る。
`invenio-db` は各テストの teardown で `drop_database` するため、
接続が残っていると次のテストの `create_all()` が
`relation ... already exists` で落ちることがあった
(`modules/invenio-db/tests/conftest.py` で `engine.dispose()` を追加済み)。

---

## D. テスト側の作りで直したもの (参考)

製品の不具合ではないが、原因が分かりにくく再発しやすいもの。

- **weko-workflow の `users` フィクスチャ**
  `contributor` を探すクエリが `email='user@test.org'` になっており
  (他 20 モジュールはすべて `contributor@test.org`)、
  contributor@test.org が一度も作られず、`users[0]` が user@test.org を指し、
  以降のユーザ ID が 1 つずつずれていた。
  テストが決め打ちしている `workflow_userlock_activity_5` (= sysadmin) などが
  すべて外れる。
- **weko-workflow の `comm01`**
  `role_id=sysadmin_role.id` で作られていた (これも他モジュールからのコピー)。
  このモジュールには「コミュニティ管理者が自分のコミュニティだけ見える」ことを
  確かめるテストが複数あり、`Community.get_by_user()` が必ず空を返していた。
- **weko-workflow の `db_register_activity`**
  FlowAction を「新しく作った FlowDefine」にぶら下げていたため、
  どの Activity からも参照されず、`get_activity_list` の
  `_FlowAction.action_id == _Activity.action_id` /
  `action_order == _Activity.action_order` の突き合わせに一切当たらなかった。
  workflow_approval のフローに (1,5) (1,7) (2,5) を足して解消。
- **weko-workflow の `test_check_authority_action2`**
  `im.json['shared_user_ids'] = [1,2,3,4,5,6]` としていたが、
  `WEKO_ITEMS_UI_PROXY_POSTING` が False のときは**リストの最後の1人**しか
  見ない。generaluser が id 6 になったことで末尾と一致してしまった。
  6 を含みつつ末尾を別人にして、両方の分岐を確かめるようにした。
- **weko-workflow の `test_prepare_edit_workflow[4]`**
  ドラフト無しの経路を通すテストなのに、194.0 のドラフトを既に持つ
  `db_records[7]` (recid 194) を渡していて `uidx_type_pid` に当たっていた。
  ドラフトを持たない 195 (`db_records[8]`) に変更。
- **weko-search-ui の `test_handle_fill_system_item3`**
  設定名が `WEKO_HANDLE_ALLOW_REGISTER_CRNI` (正しくは CNRI) で、
  `is_register_cnri` パラメータが一度も効いていなかった。
- **invenio-files-rest の `dbsession_clean`**
  `invenio_files_rest.views` が blueprint に登録する `teardown_request` が
  テスト内でセッションを閉じ、`DetachedInstanceError` を撒いていた。
  `expire_on_commit=False` で塞ぐと今度は refresh 前提のテストが壊れるため、
  フィクスチャ側でこの teardown だけ外している。
