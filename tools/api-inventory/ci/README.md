# 設置手順 — API インベントリ差分検知

## 前提: このリポジトリは public

`RCOSDP/weko` は public リポジトリで、**Actions のログ・artifact・PR コメントも誰でも読める**。
台帳(`weko3_api_list_full.tsv`)は「どの経路を・どう叩けば・何が取れるか」と実証結果
(`dynamic_verified` の ★)を持つため、**公開領域には一切置かない**。

| 置き場所 | 内容 |
|---|---|
| **本リポジトリ `tools/api-inventory/`** | **ツールのみ**(scripts / ci)。データは1件も置かない |
| **`RCOSDP/weko-secret`**(private) | 台帳TSV(57列/24列)、列定義README、`api_snapshot.json`、`reconcile_allow.json`、`reconcile_report.md`、調査記録 |

スクリプトは環境変数 `WEKO_API_INVENTORY_DIR` で秘密の場所を指す。未設定なら理由を添えて中断する。

```bash
git clone https://github.com/RCOSDP/weko-secret.git
export WEKO_API_INVENTORY_DIR=$PWD/weko-secret
python3 tools/api-inventory/scripts/reconcile.py --gate
```

CI の出力は **`--summary-only` で件数のみ**。URI や endpoint 名は出さない。

## 1. 移設するファイル

WEKO3 リポジトリに `tools/api-inventory/` を作り、weko-document の
`docs/spec/tools/api-inventory/` から以下を**移動**する。

```
weko/tools/api-inventory/          ← public。ツールのみ
├── scripts/
│   ├── README.md              全手順(Phase 1-7)
│   ├── paths.py               $WEKO_API_INVENTORY_DIR の解決
│   ├── extract_routes.py …    Phase 1-2: 静的抽出・観点付与
│   ├── probe.py / asuser.sh   Phase 3: 実機Docker実測(参考実装)
│   ├── build_checklist.py     Phase 5: 57列 → 24列の再生成
│   ├── snapshot.py            Phase 6: 実機url_map → スナップショット
│   ├── diff_snapshot.py       Phase 6: スナップショット間の差分 + ゲート
│   ├── reconcile.py           Phase 6: スナップショット ↔ 台帳の突き合わせ
│   ├── changed_rows.py        Phase 6: git差分 → 再レビュー対象行
│   ├── fixtures.py            Phase 7: 到達可否測定用の最小コーパス投入
│   └── probe_ci.py            Phase 7: フィクスチャ駆動の到達可否測定
├── ci/
│   ├── api-inventory-drift.yml
│   └── README.md              このファイル
└── .gitignore                 データ類を誤ってコミットしないための保険

$WEKO_API_INVENTORY_DIR/         ← 秘密の場所。public リポジトリには置かない
├── weko3_api_list_full.tsv      台帳(57列・所見と実証結果つき)
├── weko3_api_list.tsv           台帳(24列)
├── weko3_api_list_README.md     24列の列定義・運用手順
├── weko3_api_list_full_README.md 57列の列定義
├── api_snapshot.json            経路のベースライン
├── reconcile_allow.json         実機に無い行の許可リスト
├── reconcile_report.md          突き合わせ結果
└── weko3_api_auth_findings.md   調査記録
```

`.gitignore` で `*.tsv` / `api_snapshot*.json` / `reconcile_*` 等を無視しているが、
これは保険であって設計ではない。**データを公開領域に置かないことが設計**。

---

---

## 2. 導入の順序（順序依存があるので守ること）

ベースライン `api_snapshot.json` が無いと `diff_snapshot.py` は動かない。
また台帳と実機が一致していないと `reconcile.py` が即 FAIL する。
**先にデータを入れ、最後にワークフローを有効化する。**

```bash
# --- 秘密の場所を用意する ---
git clone https://github.com/RCOSDP/weko-secret.git
export WEKO_API_INVENTORY_DIR=$PWD/weko-secret

cd <weko>          # WEKO3 リポジトリ(public)
git switch -c chore/api-inventory-drift

# 1) ツールだけを配置(データは置かない)
mkdir -p tools/api-inventory
# … scripts/ と ci/ を配置 …

# 2) 実機を起動
./install.sh

# 3) ベースラインを現行リビジョンで生成し、**秘密の場所に**保存する
python3 tools/api-inventory/scripts/snapshot.py \
  --out "$WEKO_API_INVENTORY_DIR/api_snapshot.json"

# 4) 台帳と一致することを確認(0 でなければ先に台帳を直す)
python3 tools/api-inventory/scripts/reconcile.py --gate

# 4b) 到達可否まで測るならフィクスチャを投入する
python3 tools/api-inventory/scripts/fixtures.py --out /tmp/fixtures.json
python3 tools/api-inventory/scripts/probe_ci.py --fixtures /tmp/fixtures.json --nos 34,925,25

# 5) ワークフローを配置
cp tools/api-inventory/ci/api-inventory-drift.yml .github/workflows/

# 6) GitHub に Secret を登録する
#    API_INVENTORY_REPO    = RCOSDP/weko-secret
#    API_INVENTORY_SSH_KEY = weko-secret の read-only deploy key の秘密鍵
#      作り方:
#        ssh-keygen -t ed25519 -N '' -C 'api-inventory-ci' -f /tmp/k
#        gh api repos/RCOSDP/weko-secret/keys -X POST -f title='api-inventory-ci' \
#          -f key="$(cat /tmp/k.pub)" -F read_only=true
#        gh secret set API_INVENTORY_SSH_KEY --repo RCOSDP/weko < /tmp/k
#        shred -u /tmp/k /tmp/k.pub
#    未設定ならワークフローは何もせずスキップする

git add -A && git commit -m "chore(ci): API インベントリ差分検知を追加"
```

**秘密の場所には何も commit しないこと。** `git status` で `tools/api-inventory/` 配下に
`*.tsv` や `api_snapshot.json` が現れたら、置き場所を間違えている。

3 のベースラインは**そのブランチのリビジョンで取り直す**こと。
weko-document に置いてあるものは `d2fdc0e3b`(v2.0.3) 時点なので、
導入先のブランチが進んでいれば差分が出る。

---

## 3. ベースラインの更新ルール（これを決めないと形骸化する）

**API を変更した PR では、秘密側の `api_snapshot.json` を更新する。**
公開リポジトリのコード変更と、秘密側のベースライン更新は**別の PR になる**。
案C(データを公開領域に置かない)の代償で、ここだけは手順が2つに分かれる。

```bash
# API を変更した PR の作業ブランチで
./install.sh
python3 tools/api-inventory/scripts/snapshot.py \
  --out "$WEKO_API_INVENTORY_DIR/api_snapshot.json"
# → 秘密リポジトリ側で commit / PR を作る
```

差分は**秘密リポジトリの `git diff`** に出る。「どの経路が増えたか・認証がどう変わったか」を
レビュアの目に入れる仕組みは維持されるが、見る場所が秘密側になる。
公開リポジトリの CI は件数だけを報告し、詳細は出さない。

なお PR の CI は「PR ブランチの実機」と「PR ブランチのベースライン」を比べるため、
ベースラインを更新すると差分は 0 になる。**変更の妥当性を見るのは CI ではなくレビュア**で、
CI の役割は「ベースラインを更新せずに API を変えること」を防ぐことにある。

---

## 4. ゲートが FAIL したときの対処

| ゲート | 意味 | 対処 |
|---|---|---|
| G1 新規に認証デコレータが無い | 認証の付け忘れの可能性 | 意図的な公開なら台帳に根拠を書いたうえでベースライン更新。そうでなければ実装を直す |
| G2 認証デコレータが削除された | | 同上 |
| G3 認証のコメントアウトが増えた | no.34(IIIF)と同型 | 原則やり直し。残すなら理由をコード中のコメントに明記 |
| G4 config が危険側に変わった | no.10/519/520/920 と同型 | 原則やり直し |
| G5 ModelView の can_delete/can_export 有効化 | 削除・全件CSV出力面が開く | 意図的なら台帳の data_op を更新 |
| G6 属性不明の経路が増えた | 外部ライブラリ由来など | 台帳に行を追加してから `reconcile.py` を通す |
| G7 依存更新で経路が増減 | Flask-IIIF 等 | 増えた経路を台帳に追加。減った場合は該当行を削除するか allow に登録 |
| G8 未認証で到達する書き込み系 | 認可が効いていない | 原則やり直し。意図的な公開なら台帳の根拠を更新 |
| G9 台帳では遮断だが実測で到達 | 認可の回帰 | 原則やり直し |
| reconcile A(未収載) | 台帳に無い経路がある | `weko3_api_list_full.tsv` に行を追加 → `build_checklist.py` で24列版を再生成 |
| reconcile B(実機に無い) | 台帳にあるが登録されていない | 理由を確認し `reconcile_allow.json` に**理由付きで**登録。理由なしの登録は禁止 |
| reconcile C/D | メソッド・app列の記載誤り | 台帳を実機に合わせる |

「とりあえず allow に入れて通す」を防ぐため、`reconcile_allow.json` は
**理由の文字列が必須**（キーの値が説明文になっている）。レビューで理由を読むこと。

---

## 5. プロファイル（条件付き blueprint 登録への対応）

`weko-notifications/ext.py:41` や `invenio-accounts/ext.py:168` のように
config で blueprint 登録を分岐している箇所があるため、**1プロファイルのダンプでは
他の設定で有効になる経路を見落とす**。

CI は既定プロファイル(`--profile default`)のみを回す。全機能を有効にした
プロファイルを追加する場合は、ベースラインをプロファイルごとに持つ。

```bash
python3 tools/api-inventory/scripts/snapshot.py \
  --out tools/api-inventory/api_snapshot.full.json --profile full-features
```

比較は**同一プロファイル同士**で行うこと。異なる場合は `diff_snapshot.py` が
レポート冒頭で警告する（条件付き登録の差が追加/削除として現れるため）。

---

## 6. トラブルシュート

**`docker cp 失敗: must specify at least one container source`**
`--container` に空文字が渡っている。原因はほぼ **compose のプロジェクト名の食い違い**。

`docker compose -f X.yml ps -q web` は **X.yml のプロジェクト名**でしか探さない。
`install.sh` は `docker-compose2.yml`(project=`wekov2`)を使うが、
手動で `docker compose -p weko up -d web` のように起動したスタックは project=`weko` なので
0 件になる。実行中のコンテナがどのプロジェクトに属するかは次で分かる。

```bash
docker inspect weko-web-1 \
  --format '{{index .Config.Labels "com.docker.compose.project"}} / {{index .Config.Labels "com.docker.compose.project.config_files"}}'
```

**対処: `--container` を省略する。** `snapshot.py` は
`com.docker.compose.service=web` ラベルから起動中のコンテナを自動検出する
(0件・複数件なら候補を挙げて中断する)。明示したい場合は `--container weko-web-1`。

**`install.sh` が失敗している場合**
`docker compose -f docker-compose2.yml logs web` を見る。

**`url_map ダンプ失敗` で `invenio shell` のトレースバックが出る**
`invenio shell -c` の中で例外が起きている。よくあるのは ModelView の `can_*` が
権限を実行時評価する property になっているケース(`invenio_communities/admin.py:571` の
`can_create` が `min()` で `ValueError`)。`snapshot.py` の `safe()` で握っているが、
新しい ModelView で同種の例外が出たら同様に握る。

**`create_api()` を2回呼んで `KeyError: 'schemas_route'`**
`weko-schema-ui/rest.py:127` が `options.pop()` するため API アプリは2回作れない。
`snapshot.py` は `current_app.wsgi_app.mounts['/api']` を辿ることでこれを回避している。
自前でダンプを書くときは `create_api()` を再度呼ばないこと。

**`reconcile.py` が大量の C(メソッド不一致)を出す**
メソッドを endpoint 単位で union していないか確認する。同じ `view_func` を
`add_url_rule` で複数回登録すると endpoint 名が同一になるため、
ルール単位(`routes: [{rule, methods}]`)で比較しなければならない。

**probe の結果が「判定不能」ばかりになる**
フィクスチャが入っていない可能性が高い。`fixtures.py` を先に流すこと。
投入済みでも、合成レコードはアイテムタイプ固有フィールドを持たないため
詳細画面のレンダリングは 404/500 になりうる。ワークフローの activity も
未整備なので no.601-636 は「未解決プレースホルダ」で skip される。これは既知の限界。

**fixtures.json をコミットしそうになる**
OAuthアクセストークンと平文パスワードを含むため `.gitignore` に入れてある。
CI では毎回生成する。

**中間ファイルがリポジトリに残る**
`snapshot.py` の中間ファイル(`_dump.py` / `_snapshot_dump.json`)は既定で一時ディレクトリに
作られ、終了時に削除される。`--workdir` を明示したときだけそこに残る(デバッグ用)。

**外部ライブラリ由来の経路が大量に unknown になる**
仕様。860経路のうち291件(34%)は `modules/` に無いライブラリの登録で、
AST では属性を取れない。G6 で人のレビューに回すのが設計意図。

---

## 7. CI を入れない場合の手動運用

CI を入れずに、リリース前の棚卸しだけ機械化することもできる。

```bash
./install.sh
WEB=$(docker compose -f docker-compose2.yml ps -q web)
python3 tools/api-inventory/scripts/snapshot.py --out /tmp/new.json --container "$WEB"
python3 tools/api-inventory/scripts/diff_snapshot.py \
  tools/api-inventory/api_snapshot.json /tmp/new.json --out drift.md
python3 tools/api-inventory/scripts/reconcile.py --snapshot /tmp/new.json --out reconcile.md
python3 tools/api-inventory/scripts/changed_rows.py <前回タグ> HEAD --out rerun_nos.txt

# 到達可否まで測る場合(使い捨て環境でのみ --allow-writes)
python3 tools/api-inventory/scripts/fixtures.py --out /tmp/fixtures.json
python3 tools/api-inventory/scripts/probe_ci.py --fixtures /tmp/fixtures.json \
  --only rerun_nos.txt --allow-writes --out probe.json
```

ただし「ベースラインを更新せずに API を変えること」は防げないため、
検知が漏れるのはリリース直前になる。
