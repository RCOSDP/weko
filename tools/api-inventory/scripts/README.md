# WEKO3 API インベントリ/セキュリティチェックリスト 作成手順

> **【重要】このリポジトリは public。データを置かないこと。**
> 台帳(`weko3_api_list*.tsv`)は「どの経路を・どう叩けば・何が取れるか」と実証結果を
> 持つため、公開領域には置かない。ツールは環境変数で秘密の場所を参照する。
>
> ```bash
> export WEKO_API_INVENTORY_DIR=/path/to/api-inventory-private
> ```
>
> CI の出力は `--summary-only` で件数のみ(Actions のログ・artifact・PR コメントは
> 誰でも読めるため)。置き場所と設置手順は `../ci/README.md` を参照。



> **重要（このディレクトリの配置について）**
> 本ツール群は成果物とともに `weko-document/docs/spec/tools/api-inventory/` に配置されている。
> 解析対象は **WEKO3 本体リポジトリ**(`/home/mhaya/wekov2` 等)なので、実行時は解析対象を明示すること:
> ```bash
> WEKO_ROOT=/home/mhaya/wekov2 python3 scripts/extract_routes.py routes.json
> ```
> 成果物TSV/MDは一つ上の階層(`../weko3_api_list.tsv` 等)にある。


`weko3_api_list.tsv`(24列・チェックリスト版)と `weko3_api_list_full.tsv`(57列・詳細版)を
**バージョンアップのたびに再生成**するための手順とスクリプト一式。

# 台帳の更新手順(まずここを読む)

Phase 1-9 は「どう作るか」。日々の更新はこの節だけで足りる。

## 前提

```bash
git clone https://github.com/RCOSDP/weko-secret.git
export WEKO_API_INVENTORY_DIR=$PWD/weko-secret
cd /path/to/weko          # ツールは WEKO3 リポジトリ側にある
```

## 大原則

- **`weko3_api_list.tsv`(24列版)は直接編集しない。** `weko3_api_list_full.tsv` から
  `build_checklist.py` が丸ごと生成する派生物で、手を入れても次の生成で消える。
- **派生列も手編集しない。** `priority` / `priority_reason` / `test_normal`〜`test_gap` /
  `cleanup` はスクリプトが毎回上書きする。直したいときは判定の入力側
  (`security_finding` / `dynamic_verified` / `data_op` / `deprecated` 等)を直すか、
  `prioritize.py` のルールを変える。
- **実行順がある。** `prioritize.py` は `test_gap` を参照するので `test_coverage.py` が先。

## ケース1: 派生列を再計算するだけ(最も多い)

判定ルールを変えた、テストを追加した、といったとき。

```bash
python3 tools/api-inventory/scripts/test_coverage.py    # テスト4観点を判定
python3 tools/api-inventory/scripts/prioritize.py       # 優先度・整理対象を付与
python3 tools/api-inventory/scripts/build_checklist.py  # 24列版を再生成
```

## ケース2: 台帳に行を追加する

`reconcile.py` が「A. インベントリ未収載」を出したとき。57列を手で並べる必要はない。

```bash
# 1) 何が未収載かを確認する
python3 tools/api-inventory/scripts/reconcile.py
#    → A. インベントリ未収載 に endpoint 名が出る

# 2) 雛形を確認する(まだ書き込まない)
python3 tools/api-inventory/scripts/add_row.py --endpoint api:weko_admin.foo
#    URI の一部でも探せる: --uri /api/items/import-task

# 3) 追記する
python3 tools/api-inventory/scripts/add_row.py --endpoint api:weko_admin.foo --append

# 4) TODO の列を埋める(下記)
vi "$WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv"

# 5) 列数の検算
awk -F'\t' 'NR>1 && NF!=65{print "行"NR" 列数="NF}' \
  "$WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv"

# 6) 派生列を再計算 → 24列版を再生成 → 突き合わせ
python3 tools/api-inventory/scripts/test_coverage.py
python3 tools/api-inventory/scripts/prioritize.py
python3 tools/api-inventory/scripts/build_checklist.py
python3 tools/api-inventory/scripts/reconcile.py --gate   # 差分0になること
```

### 機械付与スクリプトで TODO を減らす

`add_row.py --append` の直後に、Phase 2 の機械付与スクリプトを流すと `TODO` が減る。

```bash
export WEKO_ROOT=/path/to/weko            # 解析対象のソース
python3 tools/api-inventory/scripts/add_cols.py          # csrf_protection / input_validation /
                                                          # audit_logged / triggers_task / resource_limit
python3 tools/api-inventory/scripts/add_ssrf_redirect.py # redirect_target / ssrf_surface
python3 tools/api-inventory/scripts/add_idempotency.py   # idempotency
python3 tools/api-inventory/scripts/add_dataop4.py       # data_op_detail
python3 tools/api-inventory/scripts/add_authmech.py      # auth_mechanism / bola_risk
```

**これらは空欄/`TODO` のセルだけを埋める。既存値は上書きしない。**
台帳の既存値は機械出力そのままではなく後から精査されており、一括再生成すると劣化する
(実測: `bola_risk` の判定が逆転、`data_op_detail` の論理削除/物理削除の区別が失われる、
`csrf_protection` の指摘が消える)。意図して作り直すときだけ
`WEKO_INVENTORY_OVERWRITE=1` を付ける。

### add_row.py が埋める列 / 埋めない列

`api_snapshot.json`(実機 url_map)と git から**機械的に決まる27列**を埋め、
調査が要る31列に `TODO` を入れる。

| 自動(27列) | no / module / api_type / app / method / uri / path_params / blueprint / endpoint / impl_func / impl_file / impl_line / auth_required / auth_method / auth_mechanism / api_version / last_commit系4列 ほか |
|---|---|
| **`TODO`(31列)** | **summary / response / status_codes / exceptions / roles / auth_response_variance / restricted_content / data_op / data_target / data_store / side_effects / config_deps / test_file / category_tags / notes / sec_* / dynamic_verified / csrf_protection / input_validation / audit_logged / triggers_task / resource_limit / redirect_target / ssrf_surface / idempotency / data_op_detail / bola_risk** |

`TODO` は **ソースを読まないと書けない列**。Phase 2(静的解析)と Phase 3(実機実測)で
やっていることを、その1行について行う。埋め方は列定義 README(秘密側の
`weko3_api_list_full_README.md`)の各列の説明に従う。

派生列(`priority` / `test_*` / `cleanup`)は空のままでよい。手順6で自動的に付く。

**`TODO` を残したままにしない。** 残っていると優先度判定の入力が欠けるため、
`prioritize.py` が誤った区分を付ける(例: `data_op` が `TODO` だと破壊系の判定に入らない)。
調査が終わるまでは、少なくとも `data_op` / `auth_required` / `dynamic_verified` を
埋めること。

## ケース2b: 既存行を修正する

```bash
vi "$WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv"   # 本体列(1-57)だけを直す
python3 tools/api-inventory/scripts/test_coverage.py
python3 tools/api-inventory/scripts/prioritize.py
python3 tools/api-inventory/scripts/build_checklist.py
```

派生列(58-65)は手で直しても次の実行で消える。優先度を変えたいときは、
判定の入力側(`security_finding` / `dynamic_verified` / `data_op` / `deprecated`)を
直すか、`prioritize.py` のルールを変える。

## ケース2c: 実測(dynamic_verified)を測り直す

`remeasure.sh` が「フィクスチャ投入 → 実測 → 台帳反映 → 再計算」を通しで行う。

```bash
export WEKO_API_INVENTORY_DIR=/path/to/weko-secret
./install.sh                                   # スタックを起動しておく

tools/api-inventory/scripts/remeasure.sh                    # 未測定の P1/P2 を測る
tools/api-inventory/scripts/remeasure.sh --all-unmeasured   # 未測定を全件
tools/api-inventory/scripts/remeasure.sh --nos 607,618      # no を直接指定
tools/api-inventory/scripts/remeasure.sh --allow-writes     # 書き込み系も測る(データが変わる)
```

**既定は読み取り専用(GET/HEAD のみ)で副作用がない。** 書き込み系まで測るには
`--allow-writes` を明示する。実機のデータ(著者DB・サイト情報・ワークフローの状態)が
書き換わるため、使い捨て環境で回すか、終了後に `./install.sh` で作り直すこと。

反映は `apply_probe_results.py` が行い、**`dynamic_verified` が空の行だけ**を埋める。
既存の実測値(★実証など人手で精査した記述を含む)は残す。差し替えるときは
`--overwrite` を明示する。

### 測定できる範囲

`fixtures.py` が作る対象で決まる。

| プレースホルダ | 解決先 | 出所 |
|---|---|---|
| `<pid_value>` `<recid>` | 公開アイテム / 非公開アイテムの**両方**で測る | 作成 |
| `<bucket_id>` `<key>` `<uuid>` | 非公開アイテムに添付したファイル(IIIF の三つ組も) | 作成 |
| `<activity_id>` `<action_id>` | ワークフロー activity を**自分所有/他人所有の両方**で測る | 作成 |
| `<index_id>` `<community_id>` `<group_id>` | フィクスチャで作成したもの | 作成 |
| `<identifier>` | 著者(authors は初期状態で0件のため作成) | 作成 |
| `<item_type_id>` `<property_id>` `<mail_id>` `<client_id>` `<token_id>` | `install.sh` が投入する初期データの先頭ID | **参照** |
| `<lang_code>` `<current_language>` `<req>` | 定数(`ja` / `1`) | 定数 |

**既存の初期データは作らずに参照する。** アイテムタイプ・プロパティ・メール
テンプレート・著者プレフィクス/所属・ファセット検索・OAuthクライアントは
`install.sh` が入れるので、フィクスチャで作ると二重になる。

解決できないプレースホルダ(`<mail_id>` など)を含む行は `未解決プレースホルダ` として
skip し、台帳には反映しない。**「測っていない」ことが分かる状態を保つ**ため。

## ケース3: WEKO3 のバージョンアップに伴う全面更新

v2.0.3 → v2.1.0 (478コミット) で実際に通した手順。所要は**実測で約1.5時間**
(既存行の再レビューを除く)。工程ごとに、そのとき何が起きたかを併記する。

### 0. 先にツールを対象ブランチへ持ち込む(★最初にここで詰まる)

`tools/api-inventory/` は **ツールを入れたブランチにしか存在しない**。
対象ブランチへ切り替えるとスクリプトごと消えるので、切替の前に決着させる。

```bash
# 方法A(推奨): 対象ブランチへツールを取り込む
git checkout develop_v2.1.0
git checkout develop_v2.0.4 -- tools/api-inventory .github/workflows/api-inventory-drift.yml

# 方法B: 別ディレクトリへ取り出して WEKO_ROOT を指定して回す(今回はこちら)
mkdir -p /tmp/inv && git archive develop_v2.0.4 tools/api-inventory | tar -x -C /tmp/inv
```

### 1. url_map を取る — `snapshot.py` だけなら `install.sh` は要らない

Docker がホストのリポジトリを `/code` にマウントしている構成なら、
**ブランチを切り替えるだけでコンテナ側のコードも入れ替わる**。
`snapshot.py` は `invenio shell`(毎回新しいプロセス)で動くので、再構築せずに通る。

```bash
git checkout develop_v2.1.0          # 2秒
python3 .../snapshot.py --out /tmp/snap_new.json   # 12秒
```

> 実績: 再起動なしで `endpoints=865` を取得できた(v2.0.3 は 860)。
> `install.sh` を回すと数十分かかるが、**url_map の取得だけなら不要**。

**egg-info の再生成は必須**。ルートは entry_points 経由で登録されるので、
モジュール構成や entry_points が変わったバージョンでは、
古い egg-info が存在しない属性を指してアプリが起動しなくなる。

```bash
docker exec weko-web-1 bash -lc 'cd /code && for d in modules/*/; do (cd "$d" && python setup.py -q egg_info); done'
docker restart weko-web-1
```

> 実績(v2.0.3 へ戻したとき): 再生成せずに再起動したら
> `AttributeError: module 'weko_theme.bundles' has no attribute 'js_preview_widget'` で
> `invenio_assets` の entry point が解決できず、**アプリが一切起動しなくなった**
> (`no python application found`)。再生成して再起動したら復旧した。所要は約4分。
> v2.0.3 → v2.1.0 の向きでは entry_points に変更が無く数も変わらなかったが、
> **再生成前後で数が変わらないことを確認するまで確定させない**。

### 1-b. 実測するなら uwsgi のリロードを確認する(★見落としやすい)

`snapshot.py` は毎回新しいプロセスなので即座に新しいコードを見るが、
**`probe_ci.py` は稼働中の uwsgi ワーカーを叩く**。こちらは自動リロードが
効かないと古いコードのままで、**測っているつもりのバージョンと違うものを測る**。

切り替えたら、そのバージョンにしか無い/無くなったエンドポイントを1つ叩いて確かめる。

```bash
# v2.0.3 に戻したなら、v2.1.0 で追加された経路が 404 になるはず
curl -sk -o /dev/null -w '%{http_code}\n' -H 'Host: weko3.example.org' \
  https://localhost:8443/api/admin/get_widget_item_list
```

> 実績: v2.0.3 に切り替えた直後は `500`(=v2.1.0 の経路がまだ生きている)だった。
> egg-info を再生成して `docker restart weko-web-1` した後に `404` になり、
> ここで初めて v2.0.3 を測れる状態になった。

### 2. Alembic マイグレーションを確認する(★実測の前に必須)

```bash
docker compose exec web invenio alembic current | tail -5
git log --oneline <前回タグ>..HEAD -- '*/alembic/*'   # 追加リビジョンを洗う
```

> url_map の取得は DB スキーマに依存しないが、**`fixtures.py` / `probe_ci.py` は依存する**。
> スキーマが古いと probe が 500 を返し、分類器がそれを「到達」と誤判定して
> 認可の穴と区別がつかなくなる。
> 実績: 追加リビジョンは 2件(`33c2a0cb8f5f`, `e0dd9fb514cf`)で、いずれも適用済み。
> 制約(`fk/uq_item_type_mapping_item_type_id`)が実DBにあることまで確認した。

### 3. 差分を確定し、台帳を 0 差分にする

```bash
python3 .../diff_snapshot.py "$WEKO_API_INVENTORY_DIR/api_snapshot.json" /tmp/snap_new.json
cp /tmp/snap_new.json "$WEKO_API_INVENTORY_DIR/api_snapshot.json"
python3 .../reconcile.py            # A(未収載) を洗い出す
python3 .../add_row.py --append --no <新規のendpoint>   # 自動27列だけ埋まる
python3 .../reconcile.py --gate     # 0件になるまで繰り返す
```

> 実績: ADDED=5 / REMOVED=0。`reconcile.py` は A=5 B=0 C=0 D=0 を報告し、
> 5行追加後に **✅ 一致(0件)** となった。

**外部調査との突き合わせで数が合わないときは、まず相手の環境を疑う。**
今回ベンダ資料は新規23件としていたが、`develop_v2.1.0` のソースに存在するのは 5件だけで、
残り18件(`invenio_accounts_rest_auth.*` 7 / `invenio_oauthclient.rest_*` 6 /
`reindex_search.*` 3 ほか)は grep しても 1件もヒットしなかった。
`modules/` 配下でなく site-packages 側の pip パッケージのバージョン差が原因。

### 4. 新規行を埋める

機械付与 → 実装読解、の順。機械付与は**空欄/TODOセルのみ**を触るので既存値を壊さない。

```bash
for s in add_cols add_ssrf_redirect add_idempotency add_dataop4 add_authmech add_reqinfo; do
  python3 .../$s.py
done
```

> 実績: 5行に対し機械付与で 112セル(約3分)。残る 18列は実装を読んで手で埋めた(約20分)。
> 人手が要るのは `summary` / `response*` / `status_codes` / `exceptions` / `roles` /
> `access_variance` / `data_store` / `side_effects` / `config_deps` / `category_tags` /
> `notes` / `sec_*` 5列 / `dynamic_verified`。

### 5. 実測する

```bash
python3 .../fixtures.py --out "$WEKO_API_INVENTORY_DIR/fixtures.json"
python3 .../probe_ci.py --nos 927,928,929,930,931 --allow-writes --out /tmp/probe.json
python3 .../apply_probe_results.py --probe /tmp/probe.json
```

> 実績: `fixtures.py` は `errors=3` を返したが中身は ES への reindex 失敗で、
> 到達可否の測定には影響しない。5件中4件を測定、`<task_id>` を持つ 1件は
> フィクスチャが無く未解決でスキップされたため手で叩いた。

**分類器の穴に注意する。measured の結果をそのまま信じない。**

| 症状 | 実態 | 対処 |
|---|---|---|
| `/api/*` の `anon=500` → `到達` | `BuildError('security.login')` で**実態は遮断** | **修正済み**: `--web-container weko-web-1` を渡すと `docker logs --since` を見て切り分ける |
| `502` → `判定不能` | nginx の一過性エラー。叩き直すと `403` だった | 手で2回叩いて確定させる |
| `308` → `到達` | werkzeug の末尾スラッシュ正規化。その先にログイン転送が隠れる | **修正済み**: 転送を最大6段たどり最終ステータスで判定する |
| 途中から全部 `遮断` になる | `--allow-writes` で `/logout` や `POST /accounts/settings/session` を叩き、**自分のセッションを消していた** | **修正済み**: ログイン転送を検出したら張り直して測り直す |
| 転送を追った先が `200` → `到達` | 「拒否して一覧へ戻す」転送だった | **修正済み**: `到達(転送)` として区別し転送先URLを併記。人が判断する |

1行目はレスポンス本文が汎用メッセージなので本文からは判別できない。
`--web-container`(既定は `$WEKO_WEB_CONTAINER`)を渡すと、500 のときだけ
`docker logs --since` を引いて `BuildError` / `security.login` を探す。
渡さないと従来どおり「到達」と誤判定するので、`/api/*` を測るときは必ず指定すること。
なお 500 を返すこと自体は
`weko3_api_unauthorized_handler_proposal.md` の恒久対策が入るまで残る問題で、
v2.1.0 では API 側 35 行に `応答不整合:401の代わりに500` として記録した。

下2つは v2.1.0 の一括再測で顕在化した。特に最後のものは**静かに壊れる**のが厄介で、
「88%の行が全識別子で遮断・sysadmin の到達がわずか9%」という
明らかにおかしい分布で気付いた。一括測定のあとは必ずこの2つを確認すること:

- 全識別子が遮断の行の割合(管理系が多い母集団で 8割を超えたらセッション切れを疑う)
- `sysadmin` の到達率(管理系エンドポイントなら高いはず)

**転送先がログイン画面でも「遮断」とは限らない。**
ハンドラが副作用を起こしてからログインへ転送する可能性は転送先からは判別できない。
書き込み系で判定が重要な行は、DB を直接見て副作用の有無を確かめること。

> 実績: `no.480 POST /record/<pid>/publish` は長らく「302 は publish 成功リダイレクトの可能性」と
> 保留されていた(コード中のコメントは「実証済み」と書いていた)。
> 非公開レコードに未認証 POST して `publish_status` を前後で比較したところ **変化しなかった**。
> 真に遮断であると確定し、コメントの記述を訂正した。

**`--allow-writes` の一括測定は、自分が壊した環境を測ることになる。**
書き込み系を叩くとフィクスチャや設定そのものが変わり、以降の行が
`404` や別の結果に化ける。実際に起きたもの:

- `POST /admin/searchsettings/` に空ボディが入り `sort_setting` が `{}` になって
  **トップページが 500** になった(気付かずに次のバージョンの測定を始めていた)
- records の `publish_status` が `None` になり `/records/<pid>` が軒並み 404
- フィクスチャのグループが sysadmin の行で削除され、後続の行が 404

対策として `probe_ci.py` に2つ入れた。`--allow-writes` のときは必ず使う。

```bash
--refresh-fixtures 40      # 40行ごとに fixtures.py を流し直す
                           # 加えて、フィクスチャ由来の値を使う行で 404 と非404 が
                           # 混ざったら、その場で張り直して1度だけ測り直す
```

それでも **単発の観測は鵜呑みにしない**。v2.0.3 の全行測定で
`DELETE /api/deposits/items/<depid>` が `anon=204` と出たが、
単独で3回叩くと `401` で安定し PID も残った(`delete_permission_factory_imp=deny_all`)。
重い結論を出す前に、その行だけ単独で測り直すこと。

**`到達(転送)` は「到達したかもしれない」であって「処理が成功した」ではない。**
転送先URLが併記されるので、そこを見て判断する。一覧画面や元のページへ戻されていれば
たいてい拒否、対象リソースのページへ進んでいれば処理が通っている。
迷ったら実データを見る。

> 実績: `no.318 POST /accounts/settings/groups/<id>/delete` は
> `general=302→200(到達(転送)) 転送先=/accounts/settings/groups/` と出た。
> 所有者以外がグループを消せるなら重大なので、repoadmin 所有のグループを新規に作って
> ロール無しのユーザで削除要求したところ、**一覧へ差し戻されグループは残っていた**。
> 一方で同じグループの `no.314-317`(`/` と `/manage`)は転送を経ずに `200` で
> グループ名と説明が表示され、こちらは**非メンバーによる閲覧が本当に通る**。
> 同じリソースでも操作ごとに結論が違うので、まとめて判断しないこと。

### 6. 既存行への影響を洗う

**先に `refresh_impl.py` を流すこと。**
台帳の `impl_line` はバージョンアップで関数がずれても更新されない。
`changed_rows.py` は「git diff のハンク行番号」と「台帳の `impl_line`」を突き合わせるので、
**ずれたまま流すと対象行を取り違える**。

```bash
python3 .../refresh_impl.py                 # まず差分だけ見る
python3 .../refresh_impl.py --write         # 納得したら書き戻す
python3 .../changed_rows.py <前回タグ> HEAD --out /tmp/rerun.txt
```

> 実績(v2.1.0): 一致 390 / **ずれ 254** / 解決不能 2 / 委譲 12 / impl_file が実ファイルでない 273。
> 直さずに流したときの対象は 41行、直してから流すと **31行**。
> 差の内訳は、実際には変わっていないのに拾われていた 12行と、
> 変わったのに漏れていた 2行(`no.53 /oauth/errors`、`no.919 /api/deposits/items`)。
> 例: `invenio-oauth2server/views/server.py` は台帳が `errors=L121` のところ実際は `L127` で、
> 変わっていない `no.52/54/55` を拾い、変わった `no.53` を落としていた。

**`changed_rows.py` はエンドポイント関数の行範囲しか見ない。**
エンドポイントが呼ぶ**ヘルパの変更は自動では台帳行に結び付かない**ので、
出力末尾の「台帳のエンドポイントではないが変更されたヘルパ関数」を必ず読み、
`grep` で呼び出し元を辿ること。

> 実績(v2.1.0): ヘルパ18件が報告され、うち3件が実質的な指摘だった。
> `_get_status_document` / `_get_file_info` の変更で
> `no.573 GET /sword/deposit/<recid>` の応答にファイルURLが増えていたが、
> `no.573` 自体は(行番号を直した後も)対象一覧に出ていなかった。

**台帳に1行も無いファイルの認可ヘルパも見る。**
`permissions.py` / `utils.py` / `api.py` / `ext.py` / `decorators.py` のうち、
関数名に `permission` `role` `group` `auth` `can_` `check_` などを含むものの変更は
別枠で報告する。`permission_factory` 経由で間接的に呼ばれ、エンドポイントの
可否をそのまま動かすため。

> 実績(v2.1.0): 28件。うち `weko_index_tree/utils.py` の
> `check_index_permission_by_role_and_group` は、索引の閲覧判定を
> `check_roles OR check_groups` から **AND** に変えていた。
> `/item/edit/<pid>` の可否まで動く変更だが、このファイルには台帳行が無いため
> 上の(台帳行があるファイル限定の)ヘルパ報告には出ていなかった。

再レビュー自体は機械化できず実装読解が要る。時間が取れないときは
「構造(0差分)と新規行の実測だけ先に確定し、既存行は次サイクルへ回す」と割り切ってよい。
その場合は**保留した旨を必ず記録する**。

### 7. 再計算してゲートを通す

```bash
python3 .../test_coverage.py
python3 .../prioritize.py
python3 .../build_checklist.py
python3 .../reconcile.py --gate     # exit 0 を確認
```

> 実績(v2.1.0 / 931行): 特定617 特定不能314 /
> P1=82 P2=150 P3=450 P4=4 P5=64 整理対象=20 環境依存=11 対象外=150 / reconcile ✅ 0件。

### 8. タグを打つ

最後に **WEKO3 と同名のタグ**を打つ(理由は `../ci/README.md` 3c)。

```bash
cd "$WEKO_API_INVENTORY_DIR"
git add -A && git commit -m "..."
git tag -a v2.1.0 -m "WEKO3 v2.1.0 (RCOSDP/weko <sha>) 時点の API インベントリ"
git push origin main --follow-tags
```

### 所要時間の実績(v2.0.3 → v2.1.0)

| 工程 | 実績 |
|---|---|
| 0. ツール持ち込み | 5分 |
| 1. snapshot(再起動なし) | 12秒 / egg-info 再生成込みで 5分 |
| 2. Alembic 確認 | 5分 |
| 3. 差分確定・0差分化 | 15分(外部資料との突き合わせ含む) |
| 4. 新規5行を埋める | 25分 |
| 5. 実測 | 15分 |
| 7. 再計算・ゲート | 5分 |
| **小計** | **約1.5時間** |
| 6. 既存41行の再レビュー | 別途(今回は保留) |

## 各スクリプトが何を読み書きするか

| スクリプト | 読む | 書く |
|---|---|---|
| `snapshot.py` | 実機 url_map + ソース | `api_snapshot.json` |
| `reconcile.py` | snapshot + full.tsv | 何も書かない(差分を報告するだけ) |
| `refresh_impl.py` | full.tsv + 実装ソース(AST) | full.tsv の `impl_line`(`--write` 時のみ) |
| `changed_rows.py` | git diff + full.tsv | 再確認対象の `no` 一覧 + 変更ヘルパ関数の報告 |
| `test_coverage.py` | full.tsv + テストコード | full.tsv の 60-64列 |
| `prioritize.py` | full.tsv | full.tsv の 58-59, 65列 + 末尾列順の正規化 |
| `build_checklist.py` | full.tsv | **`weko3_api_list.tsv` を全体再生成** |
| `add_row.py` | `api_snapshot.json` + git | full.tsv に新規行の雛形を追記(`--append`) |
| `apply_probe_results.py` | probe.json | full.tsv の `dynamic_verified`(空欄のみ / `--overwrite` で差し替え、`--keep-history` で旧値を ` ‖ 旧: ` として残す) |
| `remeasure.sh` | — | 上記を通しで実行するドライバ |
| `add_cols.py` / `add_ssrf_redirect.py` / `add_idempotency.py` / `add_dataop4.py` / `add_authmech.py` | full.tsv + 実装ソース | full.tsv の**空欄/TODO セルのみ**を機械付与 |

`test_coverage.py` → `prioritize.py` → `build_checklist.py` は**何度流しても結果が変わらない**
(冪等)。24列版は full.tsv から完全に再現できることを確認済み。

---

## 収録範囲(v2.1.0 で変更)

**static 配信ルートも収録する。**
以前は `*.static` / `send_static_file` を除外していたが、外部調査と突き合わせるたびに
「経路として存在するのに台帳に無い」ものを毎回説明する羽目になったため方針を変えた。
snapshot は `is_static: true` を立てて収録する(v2.1.0 で endpoints 865 → 933、+68)。

同じ URI に複数の Blueprint が static を登録することがある
(`/static/<path:filename>` に 23、`/api/static/<path:filename>` に 7)。
**台帳は endpoint 単位で1行**を持つ(68 行)。

url_map 上は先に登録されたものだけが応答する。どれが応答するかは
`url_map.bind(host).match(path)` で確定できるので、それで確かめて
実際に応答する行と、隠れて到達不能な行を書き分ける。
到達不能な側は `category_tags` に `shadowed` を付け、実測は行わない。

| URI | 登録数 | 実際に応答する endpoint |
|---|---:|---|
| `/static/<path:filename>` (ui) | 23 | `static`(アプリ本体) |
| `/api/static/<path:filename>` | 7 | `invenio_files_rest_admin.static` |
| `/api/admin/static/<path:filename>` | 2 | `weko_admin.static` |
| `/oauth/static/<path:filename>` (ui) | 2 | `invenio_oauthclient.static` |

同じことが static 以外でも起きる。`RECORDS_REST_ENDPOINTS` は
`/records/<pid(recid):pid_value>` を **recid / opensearch / worksapce の3組**で
重複登録しており、応答するのは `recid_item` だけ。残り2組に設定した
`permission_factory` は一切効かない。**「設定したつもりの認可が適用されていない」**
状態なので、`設定不整合:到達不能な重複登録` として台帳に記録している。

**UI アプリと API アプリ(/api)は別行にする。**
以前は同じ view が両方にマウントされている場合 `app=両方` の1行に集約していたが、
**同じ view でも未認証時の挙動が違う**。

| | UI 側 | API 側 |
|---|---|---|
| `/workflow/activity/list` | `302` → `/login/` | `500`(`BuildError('security.login')`) |
| `/workflow/iframe/success` | `200`(到達) | `500`(遮断) |

1行に集約していると、実測値も所見も片側でしか成り立たないものを書き分けられない。
v2.1.0 で 46 行を分割した(931 → 1015 行)。`reconcile.py` は旧表現(`app=両方`)も
引き続き受け付けるので、過去の台帳もそのまま突き合わせられる。

---

## 全体の考え方

3層で構築する:
1. **静的抽出** — ソースコードから全HTTPエンドポイントと属性を機械抽出(AST)
2. **静的解析** — 認証/認可/データ操作/セキュリティ観点を実装読解＋AST解析で付与
3. **動的検証** — 実際にDocker起動しHTTPリクエストを送って机上の結論を実測で裏取り

「デコレータの有無」だけでなく **実測での到達可否** まで取ることで、
「認可が実際に効いているか」を確定できる(静的解析だけでは分からない)。

---

## Phase 0: 対象リビジョンの確定
```bash
cd /home/mhaya/wekov2
git rev-parse --short HEAD              # 生成元リビジョンを記録
git describe --tags                     # タグ
```

## Phase 1: 静的抽出(エンドポイント発見)

### 1-1. blueprint route を AST 抽出
```bash
python3 tools/api-inventory/extract_routes.py routes.json
```
`@blueprint.route` / `add_url_rule` を全 modules から収集。357件程度。

### 1-2. config駆動 REST エンドポイントを抽出
```bash
python3 tools/api-inventory/extract_endpoints.py endpoints.json
```
`*_REST_ENDPOINTS` config の route 文字列(`/<string:version>/...`)を展開。

### 1-3. 実機の url_map と突合(取りこぼし検出) ★重要
静的抽出は Flask-Admin ModelView(自動生成CRUD 253件)や framework 由来ルートを取りこぼす。
**実際にアプリを起動して url_map をダンプし、差分を追記する**(Phase 3 で起動後):
```bash
# コンテナ内で
docker exec weko-web-1 bash -lc 'source ~/.virtualenvs/invenio/bin/activate; cd /code; \
  invenio shell -c "from flask import current_app; \
  [print(r.endpoint, sorted(r.methods), str(r)) for r in current_app.url_map.iter_rules()]"'
```
これと Phase1-1/1-2 の抽出結果を endpoint 名で照合し、未収載を追記する。
※ @route/@expose だけを見ると ModelView と framework(security.login等)が漏れる。

### URI 算出ルール(重要)
- `invenio_base.blueprints`/`apps` 経由 → `bp.url_prefix` + route
- `invenio_base.api_blueprints`/`api_apps` 経由 → **`/api`** + `bp.url_prefix` + route
- Flask-Admin → `/admin/<endpoint>/<@expose path>`
- 根拠: `invenio_app.factory` が API アプリを DispatcherMiddleware で `/api` にマウント

## Phase 2: 静的解析(観点の付与)

各エンドポイントの実装関数(+呼び出しヘルパ1段)を AST で解析し、列を付与。

| スクリプト | 付与する列 |
|---|---|
| (extract_routes内) | summary/response/exceptions/data操作の一次抽出 |
| `audit_decorators.py` | コメントアウトされた認証/デコレータ不揃い/roles_required無効化 |
| `audit_injection.py` | eval/exec, ZIP-slip, SQLi連結, パストラバーサル |
| `add_cols.py` | csrf_protection, input_validation, audit_logged, triggers_task, resource_limit |
| `add_ssrf_redirect.py` | redirect_target(オープンリダイレクト), ssrf_surface |
| `add_idempotency.py` | idempotency(冪等性) |
| `add_dataop4.py` | data_op_detail(取得/作成/更新/**論理削除/物理削除**) |
| `add_authmech.py` | auth_mechanism(decorator/config-factory/modelview), bola_risk |

### 認証・認可の参照辞書(手動で維持)
- ロール: System/Repository/Community Administrator, Contributor, General
- スコープ: `*/scopes.py`(item:read, file:read, index:*, author:*, oa_status:update等)
- permission factory: `weko-records-ui/permissions.py`(page/file_permission_factory)
- `WEKO_ADMIN_ACCESS_TABLE`(weko-admin/config.py) = Flask-Admin のロール制御

### git情報の付与
```bash
python3 tools/api-inventory/enrich_git.py body.tsv body_enriched.tsv
```
`git log -L <開始>,<終了>:<file>` で**実装関数の行範囲**の最終コミットを取得(ファイル単位より正確)。
`git tag --sort=creatordate --contains <sha>` で導入リリースタグ。

## Phase 3: 動的検証(実測で裏取り) ★静的だけでは不正確

### 3-1. Docker 環境起動
```bash
# 既存の初期化済みボリュームを再利用(プロジェクト名 weko)
docker compose -p weko up -d postgresql pgpool redis elasticsearch rabbitmq
docker compose -p weko up -d web
# egg-info がソースと食い違うと起動失敗 → 全モジュール再生成
docker exec -u root weko-web-1 bash -lc 'source ~/.virtualenvs/invenio/bin/activate; cd /code; \
  for d in modules/weko-* modules/invenio-*; do (cd "$d" && python setup.py egg_info -q); done'
docker compose -p weko restart web
# nginx(80/443競合時は remap して起動、web は uwsgi プロトコルで直叩き不可)
docker compose -p weko -f docker-compose.yml -f nginx-override.yml up -d nginx
# → https://localhost:8443 (Host: weko3.example.org)
```

### 3-2. テストデータ・アカウント準備
- 全ユーザにパスワード設定 → `/api/v1/login` でロール別セッションCookie取得
- 公開/非公開アイテム、グループ・コミュニティ(所有者を変えて)、OAuthトークン(全スコープ)
- ファイル実体(ObjectVersion)を非公開アイテムに添付

### 3-3. 全フラグ付きエンドポイントを実測
```bash
python3 tools/api-inventory/probe.py probe_results.json    # 未認証+各ロールで叩く
```
- プレースホルダ(`<pid_value>`等)を実値に解決
- ★**Cookie失効に注意**: セッションは短時間で失効する。identityごとに直前ログイン＋
  sentinel(既知の200エンドポイント)で鮮度確認してから測定する(`reprobe_own.py`/`asuser.sh`方式)。
  失効Cookieは認証ユーザに大量の偽「遮断」を生む。
- ★**500の切り分け**: `security.login`のBuildErrorなら login_required による遮断、
  それ以外は認可通過後のクラッシュ=到達。ログで個別判定する。

### 3-4. 実測結果を dynamic_verified 列へ
`apply_probe.py`/`final_apply.py` で判定(未認証で到達/ログインのみ/管理者のみ/遮断/検証不能)を付与。
本文取得・DB改変・ファイル露出まで確認できたものは `★確定` とする。

## Phase 4: マージ・整形
```bash
python3 tools/api-inventory/merge.py out/ merged.tsv       # 分割TSVを結合・重複排除・採番
```

## Phase 5: チェックリスト版(24列)を生成
```bash
python3 tools/api-inventory/build_checklist.py             # 57列 full → 24列 に統合
```
派生列を統合: impl(func+file+line), auth(required+method+mechanism),
security_flags(CSRF/BOLA/SSRF等8観点を該当のみ), last_change(commit系4列) 等。

---

## 観点の網羅性(OWASP API Security Top 10 対応)
| OWASP API(2023) | 対応列 |
|---|---|
| API1 BOLA | bola_risk / security_finding:所有者チェック欠落 |
| API2 Broken Auth | auth / dynamic_verified |
| API3 Property-Level Auth | access_variance |
| API4 Resource Consumption | security_flags:RESLIMIT |
| API5 Function-Level Auth | roles_scope / security_finding:権限過小 |
| API6 Business Flow | security_flags:IDEMP |
| API7 SSRF | security_flags:SSRF |
| API8 Misconfiguration | security_flags:CSRF / config_deps |
| API9 Inventory Mgmt | deprecated / api_version / test_file |
| API10 Unsafe Consumption | side_effects |

## 差分レビューの勘所(バージョンアップ時)
1. Phase1で新url_mapを取り、前回の `no`/`uri` と**差分**を取る(新規/削除エンドポイント)
2. 新規・変更行だけ Phase2-3 を回す(全部再測定は不要)
3. `auth`が`不要`(公開)に変わった行、`security_flags`に★が付いた行を重点確認
4. `data_op`が`物理削除`(不可逆)の新規エンドポイントは特に注意

## 既知の限界
- SSRF検出は関数本体＋1段ヘルパまで。route→Celery→utils の間接SSRFは triggers_task で追跡。
- ModelView 253件は代表実測。全個別測定ではない。
- 動的検証はテストデータ依存。完全な end-to-end(ワークフロー経由の正規deposit)は一部のみ。
- `probe_ci.py` の判定には既知の穴が2つある(v2.1.0 実測で確認)。
  - `/api/*` への未認証アクセスが返す `500` は、実態は `BuildError('security.login')`
    による**遮断**だが、本文が汎用メッセージのため「到達」と誤判定される。
    `docker logs weko-web-1 | grep BuildError` で切り分けること。
  - nginx の一過性 `502` を `判定不能` として記録してしまう。手で叩き直して確定させる。
- `<task_id>` のようにフィクスチャで作れないパスパラメータは probe がスキップする。
  該当行は手で叩いて `dynamic_verified` に測定条件(ダミー値を使った旨)まで書く。

---

# Phase 6: 差分検知(バージョンアップ時の機械的チェック)

Phase 1-5 が「作る」手順なのに対し、Phase 6 は **「変わったことを検知する」** 手順。
CI に組み込んで、API の追加・仕様変更を人手のレビュー前に機械で拾う。

## なぜ実機 url_map が正なのか

**ブループリント(`@bp.route`)を見ても半分しか分からない。** 実測値:

```
AST抽出(@bp.route + add_url_rule) : 357ルート / 77ブループリント
実機url_map(static除く)           : 903ルート (UI 724 + API 248)
ASTで説明できない                 : 472件 (52%)
```

漏れの内訳:

| 種別 | 件数 | 理由 |
|---|---:|---|
| Flask-Admin ModelView 自動生成 | 223 | `index_view`/`create_view`/`edit_view`/`delete_view`/`details_view`/`action_view`/`ajax_lookup`/`ajax_update`。ModelView を1つ定義すると8ルート生える |
| `@expose`(Flask-Admin BaseView) | 約100 | `@bp.route` ではないので route 抽出の対象外。リポジトリ内に `@expose` 205箇所 |
| config駆動 REST(`*_REST_ENDPOINTS`) | 約30 | route 文字列が config の dict の中 |
| `modules/` に無い pip パッケージ | — | `extract_routes.py` は `ROOT/modules` しか walk しない |
| route が式の `add_url_rule` | — | 357件中75件が add_url_rule、`options.pop('rdc_route')` 等は literal_eval 不可 |
| framework 由来 | — | flask_security / flask-oauthlib(9) / invenio_i18n |

したがって **役割を分ける**:

- **経路の集合(何が存在するか)** → 実機 url_map ダンプが唯一の正
- **各経路の属性(誰が叩けるか)** → AST + ソース読解

## 6-1. スナップショット生成

```bash
python3 scripts/snapshot.py --out api_snapshot.json --container weko-web-1
# → endpoints=860 (AST結合=495 / 属性不明=365) modelviews=30 config=33
```

やっていること:

1. 実機 url_map を **UIアプリと APIアプリの両方**ダンプ
   (APIアプリは `current_app.wsgi_app.mounts['/api']` を辿らないと出てこない)
2. ModelView の権限属性(`can_delete`/`can_export`/`column_export_list`)を併せて取得
   — url_map には現れないが、`can_export` が有効化されると DB 全件 CSV 出力面が開く
3. AST で全 def を索引化し、`(module, funcname)` で url_map に左結合してデコレータを付与
4. **結合できなかったものは `attrs: "unknown"` として残す**(黙って落とさない)

出力の構造:

```jsonc
{
  "meta":       { "revision": "d2fdc0e3b", "tag": "v2.0.3", "profile": "default", "counts": {...} },
  "endpoints":  { "api:weko_admin.get_curr_api_cert": {
                    "rules": ["/admin/get_curr_api_cert/<string:api_code>"],
                    "methods": ["GET"],
                    "auth_decorators": [],          // ← 認証デコレータ無し
                    "auth_hash": "da39a3ee5e6b",
                    "body_hash": "…" } },
  "modelviews": { "actionroles": { "can_delete": true, "can_export": false, … } },
  "config":     { "…/config.py::RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY": {…} },
  "commented_auth": { "invenio_iiif.handlers": [{ "line": 39, "text": "#g.obj = ObjectResource.get_object(…)" }] }
}
```

キーは **`<app>:<endpoint>`**。URL ではなく Flask の endpoint 名にすることで、
URL だけ変わった場合を「新規＋削除」ではなく `RULE_CHANGED` と正しく分類できる。
1エンドポイントが複数ルールを持つ場合(末尾スラッシュ違い等・36件)は `rules` 配列で保持する。

### プロファイル

条件付きで blueprint を登録している箇所が実在する
(`weko-notifications/ext.py:41`, `invenio-accounts/ext.py:168` 等)ため、
**1プロファイルのダンプでは他の設定で有効になる経路を見落とす。**

```bash
python3 scripts/snapshot.py --out api_snapshot.json      --profile default
python3 scripts/snapshot.py --out api_snapshot.full.json --profile full-features
```

比較は同一プロファイル同士で行う(異なる場合は差分レポートが警告する)。

### 外部ライブラリが登録する経路(動的抽出でしか見えないもの)

実機ダンプの最大の効き目はここ。**860経路のうち 291件(34%)は `modules/` に存在しない
外部ライブラリが登録している。**

| provider | 経路数 | 例 |
|---|---:|---|
| Flask-Admin==1.5.4 | 254 | `/admin/actionroles/action/` |
| invenio-records-ui==1.0.0 | 20 | `/item/edit/<pid_value>` |
| invenio-oauthclient==1.0.0 | 5 | `/oauth/authorized/<remote_app>/` |
| Flask-Security==3.0.0 | 4 | `/confirm/<token>` |
| **Flask-IIIF==0.6.1** | **3** | `/iiif/<version>/<uuid>/<region>/<size>/<rotation>/<quality>.<format>` |
| invenio-i18n / invenio-jsonschemas / invenio-csl-rest | 5 | `/lang/`, `/schema/<path>`, `/csl/styles` |

**no.34(非公開ファイルの実体を未認証で取得できることを実証した経路)は Flask-IIIF が
登録している。** リポジトリのソースをいくら走査しても出てこない。動的抽出が必須である
最も強い実例。

各エンドポイントには `provider: "<配布物>==<版>"` を付与し、`meta.packages` に
インストール済み302パッケージの版を丸ごと保持する。これにより
**「依存を上げたら経路が増えた」を機械的に帰着できる**(ゲート G7)。

```jsonc
"api:iiifimageapi": {
  "rules": ["/iiif/<string:version>/<string:uuid>/<string:region>/…"],
  "view": "flask_iiif.restful.iiifimageapi",
  "provider": "Flask-IIIF==0.6.1",
  "attrs": "unknown", "reason": "framework 由来"
}
```

## 6-2. 差分とゲート

```bash
python3 scripts/diff_snapshot.py OLD.json NEW.json --out drift.md --gate
# FAIL があれば exit 1
```

分類:

| 分類 | 意味 |
|---|---|
| `ADDED` / `REMOVED` | 経路の増減 → **インベントリへの追加/削除が必要** |
| `RULE_CHANGED` | endpoint 同一で URL が変化 |
| `METHODS_CHANGED` | HTTPメソッドの増減 |
| `AUTH_CHANGED` | 認証・認可デコレータの変化(最優先) |
| `IMPL_CHANGED` | デコレータ据置きで実装本体のみ変化 |
| `ATTRS_UNKNOWN_NEW` | 経路はあるが静的解析で属性が取れない新規 |

`IMPL_CHANGED` は「デコレータは同じだが中身が変わった」を拾う。
no.480(`page_permission_factory` が `flg='Edit'` を無視)のような
**ロジック内認可**の変化はここでしか捕まらない。

### ゲート(いずれも過去の実際の穴から導出)

| ID | 条件 | 由来 |
|---|---|---|
| G1 | 新規エンドポイントに認証系デコレータが無い | no.200/201/389/390/393 |
| G2 | 認証系デコレータが削除された | — |
| G3 | 認証/認可デコレータのコメントアウトが増えた | **no.34(IIIF `protect_api`)** |
| G4 | 認可を左右する config が危険側に変わった | **no.10/269/271/519/520(`factory=None`)** |
| G5 | ModelView の `can_delete`/`can_export` が False→True | CSV export 22件 |
| G6 | 属性不明のまま追加された経路がある | 手動レビュー必須 |
| G7 | 依存パッケージの更新で外部ライブラリ由来の経路が増減した | **no.34(Flask-IIIF)** |
| W1 | ModelView が追加された | 1つにつき自動生成8ルート(削除系を含む) |
| W2 | 実装本体が変化 | data_op / 情報露出の再確認 |
| W6 | 依存パッケージの版が変化した | 経路据置きでも既存経路の挙動が変わりうる |

G3 は **エンドポイントに紐付かないコメントアウトも検知する**。
no.34 の `protect_api` はビュー関数ではなくハンドラフックなので、
エンドポイント単位の検査だけでは捕まらない。

## 6-3. 再レビュー対象行の絞り込み

```bash
python3 scripts/changed_rows.py v2.0.2 v2.0.3 --out rerun_nos.txt
# v2.0.2..v2.0.3
#   変更ファイル(modules/*.py): 9
#   再レビュー対象行: 1 / 全918行
#   no=21    GET  /admin/location/   modules/invenio-files-rest/invenio_files_rest/admin.py:178
```

`git diff -U0` の変更行を AST で def/class 範囲に広げ、
インベントリの `impl_file`/`impl_line` と突き合わせる(`enrich_git.py` と同じ関数単位の考え方)。
918行すべてを Phase2-3 に回す必要がなくなる。

`views.py`/`rest.py`/`admin.py`/`ext.py`/`config.py` が変更されたのに
インベントリに未登録のファイルは「新規エンドポイントの可能性」として別途警告する。

## 6-4. CI への組み込み

**設置手順は `ci/README.md`**(移設するファイル・導入順序・ベースライン更新ルール・
ゲートFAIL時の対処・プロファイル・トラブルシュート)。ワークフロー本体は
`ci/api-inventory-drift.yml`。

CI が触るファイルは WEKO3 リポジトリの `tools/api-inventory/` に移設して
**単一リポジトリで完結**させる。別リポジトリの checkout もトークンも不要。

WEKO3 側には `ui-tests.yml` が既にあり、**push/PR ごとに `install.sh` で
WEKO スタック全体を起動している**。実機 url_map を取る土台は既に存在するので、
ジョブを1つ足すだけでよい。

**`api_snapshot.json` を git 管理するのが肝。**
API を変えた PR は必ずスナップショット更新を伴い、**差分がコードレビューに乗る**。
人手の運用ルールではなく、diff が目に入る仕組みになる。

## 6-5. さらに強くしたい場合

**アクセスログからの実在経路収集。** nginx のアクセスログから `(method, パステンプレート)`
の distinct を取り、インベントリと突き合わせる。プラグインや動的登録で
**コードにも url_map スナップショットにも出ない経路**が本番で叩かれていないかの最終確認になる。
(インベントリに「経路なし(プラグイン未登録)」と記録した4件は、逆に本番では有効な可能性がある)

## 6-6. インベントリとの突き合わせ(reconcile)

スナップショットは「実機に何があるか」、インベントリTSVは「調査済みの台帳」。
**この2つがズレていないかを機械的に検証する**のが `reconcile.py`。

```bash
python3 scripts/reconcile.py --gate --out reconcile_report.md
# A=0 B=0 C=0 D=0 B'(既知)=11   → exit 0
```

| 検出 | 意味 |
|---|---|
| A. インベントリ未収載 | 実機にあるが台帳に無い = **抽出漏れ** |
| B. 実機に無いインベントリ行 | 台帳にあるが url_map に無い(未登録/条件付き) |
| C. メソッド不一致 | 同一URIでHTTPメソッドが食い違う |
| D. app列の不一致 | UI/API どちらに登録されているかの記載誤り |

B のうち正当な理由があるもの(プラグイン未登録・config で無効・動的登録のプレースホルダ)は
`reconcile_allow.json` に**理由付きで**登録して既知扱いにする。理由なしの登録は禁止。

### URI の正規化規則(ここを間違えると偽の差分が大量に出る)

- **スナップショット**: APIアプリのルールには `/api` を前置する。
  APIアプリは DispatcherMiddleware で `/api` にマウントされるため、その url_map 側には prefix が出ない。
- **インベントリ**: `uri` セルの `;` 区切りを展開する。`app=両方` の行は `/api` 側も展開する。
- **末尾スラッシュ**は除去して比較する。
- **HEAD / OPTIONS** は比較対象外。werkzeug が GET ルールに自動付与するため、
  実装が HEAD を意識しているかを区別できない。

### メソッドは必ずルール単位で比較する

同じ `view_func` を `add_url_rule` で複数回登録すると **endpoint 名が同一になる**。
このとき endpoint 単位でメソッドを union すると、実際には POST しか受けないルールが
`DELETE,GET,POST,PUT` を受けるように見えてしまう(初版で偽の不一致17件を出した)。

```python
# weko-index-tree/rest.py:217-232 — 同じ view_func `ima` を別ルール・別メソッドで登録
blueprint.add_url_rule(options.get('api_create_index'), view_func=ima, methods=['POST'])
blueprint.add_url_rule(options.get('api_update_index'), view_func=ima, methods=['PUT'])
blueprint.add_url_rule(options.get('api_delete_index'), view_func=ima, methods=['DELETE'])
```

このため `snapshot.py` は `routes: [{rule, methods}, …]` とルール単位で保持する
(`rules` / `methods` は概観用の派生値)。

### CI での位置づけ

`diff_snapshot.py`(前回スナップショットとの差分)と `reconcile.py`(台帳との差分)は目的が違う。
両方を回す:

- `diff_snapshot.py` … **バージョン間**で何が変わったか
- `reconcile.py` … **今の実機と台帳**が一致しているか(＝調査漏れが無いか)

---

# Phase 7: 到達可否の実測を CI に載せる

Phase 6 は**構造の変化**(経路・デコレータ・config)を検知するが、
`dynamic_verified`(誰が到達できるか)は更新しない。新規APIが増えても
「未認証で本当に到達するか」は測られず、認証を追加して直しても
「修正が効いているか」を確認できない。Phase 7 がそこを埋める。

## 7-0. なぜフィクスチャが要るか

`install.sh` は `scripts/populate-instance.sh:179` の

```bash
#${INVENIO_WEB_INSTANCE} demo init      ← コメントアウトされている
```

によって **レコードを1件も作らない**。CI 環境で入るのは次のとおり。

| 項目 | CI環境 |
|---|---|
| ロール4種 + action 付与 / ユーザ5人 | あり |
| アイテムタイプ / インデックスツリー / ワークフロー定義 / ファイルロケーション | あり |
| **recid / depid のレコード** | **0件** |
| **ファイル実体(ObjectVersion)** | **なし** |
| **公開/非公開の区別、他人所有のリソース** | **なし** |
| **OAuthトークン / Community / Group** | **なし** |

この状態では認可判定を通せず、到達可否を測れない。

## 7-1. `fixtures.py` — 最小テストコーパスの投入

```bash
python3 scripts/fixtures.py --out fixtures.json
# users=5 records=3 index=900001 file=あり token=あり community=あり group=あり
```

投入するもの:

- 既知パスワード(`Passw0rd!123`)に揃えたユーザ5人
- 公開インデックス(`900001`)
- レコード3件 — いずれもバケット付き
  - `public` (recid 900001, publish_status=0, owner=Contributor)
  - `private` (recid 900002, publish_status=1, owner=Contributor, **ファイル実体付き**)
  - `other_owner` (recid 900003, publish_status=1, owner=General, **ファイル実体付き**)
- 全19スコープの個人アクセストークン
- Community / Group

**冪等かつ自己修復。** 既存があれば再利用しつつ `path` / `owner` / `publish_status` を
毎回入れ直す。先行ステップ(インデックス作成など)が失敗した回に作られたレコードは
`path` が空のままになり `check_index_permissions` を通らないため、再実行で直るようにしてある。

生成物 `fixtures.json` は **`.gitignore` 済み**。OAuthアクセストークンと平文パスワードを
含むのでリポジトリには入れない。CI では毎回生成する。

### フィクスチャで再現できること(検証済み)

```
未認証 IIIF info.json                    → 200          (no.925)
未認証 IIIF 画像本体                      → 200 / 70バイト (no.34)
未認証 files-rest 直                      → 404          (露出がIIIF経路限定であることも再現)
Contributor → 他人所有のファイル           → 200 / 70バイト (no.25 の BOLA)
未認証 POST /api/deposits/items          → 200          (no.920)
```

### 限界(正直に)

合成レコードのためアイテムタイプ固有フィールドを持たない。詳細画面の
レンダリングは 404/500 になりうる。**ワークフロー経由の正規 deposit は作っていない。**
`probe_ci.py` はこれを「判定不能」として明示するので、誤った安心にはならないが、
レンダリングまで通す必要がある行は測れない。ワークフローの activity も未整備のため
no.601-636 は未解決プレースホルダとして skip される。

## 7-2. `probe_ci.py` — フィクスチャ駆動の実測

```bash
python3 scripts/probe_ci.py --only rerun_nos.txt --allow-writes --gate --out probe.json
```

`probe.py`(参考実装)はセッション固有のUUIDとパスがハードコードされている。
`probe_ci.py` は `fixtures.json` からプレースホルダを解決するため、まっさらな環境で動く。

- 測定 identity: anon / general / contributor / comadmin / repoadmin / sysadmin
- 測定対象は `--only` で渡した `no` に限定する(全926行を毎PR測ると時間がかかりすぎる)
- **安全装置**: GET/HEAD 以外は既定でスキップ。`--allow-writes` を明示したときだけ測る
  (CI のコンテナは使い捨てなので許可してよいが、実環境では既定のままにすること)

### 判定の切り分け

| 応答 | 判定 | 根拠 |
|---|---|---|
| 401 / 403 | 遮断 | |
| 3xx でログイン画面へ | 遮断 | |
| **3xx でログイン画面以外** | **到達** | no.480 は未認証 302 で `publish_status` が実際に書き換わる。302を一律「遮断」にすると取りこぼす |
| 500 (本文に `security.login` / `BuildError`) | 遮断 | APIアプリの `login_required` は BuildError で 500 になる |
| 500 (それ以外) | 到達 | 認可通過後のクラッシュ |
| 404 | 判定不能 | `hidden=True` の権限NGか、対象が無いだけか区別できない |
| 2xx / 400 / 405 / 415 | 到達 | |

### アイテムIDは公開/非公開の両方で測る

`<pid_value>` 等は `public` と `private` の**両方**に解決して2回測る。
どちらを入れるかで結論が変わるため(no.480 は非公開だとログインへ転送されるが、
公開アイテムでは未認証で書き換えが成立することを実証済み)。

`<string:version>` は文脈依存で、IIIF なら `v2`、WEKO の REST API なら `v1` に解決する。

## 7-3. ゲート

| ID | 条件 |
|---|---|
| **G8** | 未認証で到達し、かつ `data_op` が作成/更新/削除 |
| **G9** | 台帳が「遮断」なのに実測で「到達」(回帰) |

CI では `changed_rows.py` が出す `rerun_nos.txt`(変更が触れた行)だけを測る。
全件測定はリリース前の棚卸しで行う。

---

# Phase 8: テスト観点の解析と対応優先度の付与

```bash
python3 scripts/test_coverage.py       # 4観点(正常値/異常値/境界値/例外処理)を判定
python3 scripts/prioritize.py          # 優先度を付与(テスト観点を参照するので後に実行)
python3 scripts/build_checklist.py     # 24列版(=32列)へ引き継ぐ
```

**実行順が重要**: `prioritize.py` は `test_gap` を参照して「テスト観点が確認できない行」を
P2 まで引き上げるため、`test_coverage.py` を先に回すこと。

## test_coverage.py

`test_file`(対応テスト) と `impl_func` を突き合わせ、そのエンドポイントに関係する
テスト関数を特定してから観点を判定する。ファイル単位で見ると、同じファイル内の
別APIのテストを自分のものとして数えてしまうため。

対応するテスト関数を同定できなかった行は `特定不能` として区別する。
**「テストが無い」と断定はできない**ので、4観点すべて欠落と同じ表記にはしない。

## prioritize.py

`security_finding` / `security_flags` / `dynamic_verified` / `data_op` / `data_target` /
`method` / `auth` / `test_gap` から、対応優先度を機械判定して台帳に書き戻す。
判定基準・凡例・限界は秘密側の `weko3_api_list_README.md`「priority の凡例」に記載。

「データ破壊」は **既存の実データを不可逆に壊すこと** と定義している。メタデータの
更新や新規作成は含めない。新規作成しかせず既存データを壊さないものは、認証が
無くても P0 ではなく P1 に置く。

参照系でも、露出内容が **認証情報** または **非公開データの実体** であり認可が
緩い行は P1 に上げる。「読み取り系だから限定的」は露出物次第で成り立たないため。

`deprecated` の記述から **非利用** を判定し、認可上の判定が P2 以下なら
`整理対象` に置き換える(削除すれば認可の問題ごと消える)。

`reconcile_allow.json` に登録された URI(=実機の url_map に無いことを確認済み)は
`環境依存` とする。**`整理対象` とは別物で、削除してはいけない**。別の設定・別サイトでは
有効になるため。判定に `dynamic_verified` を使わないのは、実測欄の粒度がばらついていて
同じ機能群が別区分に割れるため(プラグイン群8件が対象外3件と整理対象5件に割れていた)。

いずれも P0/P1 の行は優先度を落とさず、理由に事情を添えるだけにする。

末尾の派生列(priority / test_* / cleanup)の並びは `prioritize.py` が正規化するため、
実行順に依存しない。

**この判定は着手順を決めるための粗い仕分けであって、リスク評価の代替ではない。**
`method` ベースで判定するため副作用のある GET を落とすこと、読み取り系は露出内容の
重大さ(認証情報か公開情報か)を見ていないこと、テスト観点は静的なキーワード判定で
あって内容の妥当性を見ていないこと──いずれも目視補正が要る。

