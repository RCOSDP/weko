# 設置手順 — API インベントリ差分検知

## 前提: このリポジトリは public

`RCOSDP/weko` は public リポジトリで、**Actions のログ・artifact・PR コメントも誰でも読める**。
台帳(`weko3_api_list_full.tsv`)は「どの経路を・どう叩けば・何が取れるか」と実証結果
(`dynamic_verified` の ★)を持つため、**公開領域には一切置かない**。

| 置き場所 | 内容 |
|---|---|
| **本リポジトリ `tools/api-inventory/`** | **ツールのみ**(scripts / ci)。データは1件も置かない |
| **`RCOSDP/weko-secret`**(private) | 台帳TSV(62列/32列)、列定義README、`api_snapshot.json`、`reconcile_allow.json`、`detect_allow.json`、`reconcile_report.md`、調査記録、台帳の検査テスト |

本書では `RCOSDP/weko-secret`(private)を単に**プライベートリポジトリ**と呼ぶ。
スクリプトは環境変数 `WEKO_API_INVENTORY_DIR` でその場所を指す。未設定なら理由を添えて中断する。

```bash
git clone https://github.com/RCOSDP/weko-secret.git
export WEKO_API_INVENTORY_DIR=$PWD/weko-secret
python3 tools/api-inventory/scripts/reconcile.py --gate
```

CI の出力は **`--summary-only` で件数のみ**。URI や endpoint 名は出さない。

## ワークフローは2本

| ワークフロー | 見るもの | 要るもの | 所要 |
|---|---|---|---|
| `api-inventory-tests.yml` | **台帳を作る側**(スクリプト・手順書)が壊れていないか | なし | 数秒 |
| `api-inventory-drift.yml` | **台帳の中身**が実機・ソースとずれていないか | Secret + Docker | 60分枠 |

ツールが壊れたまま drift だけ回すと、検知器が黙って死んでいても緑で通る。
**先に tests を通すこと。**

台帳の中身そのものの検査(列数・語彙・派生列の再現・突き合わせゲート)は、
データのある**プライベートリポジトリ側の `tests/`** が持つ。

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
│   ├── schema.py              列定義の唯一の正(62列 / 32列)
│   ├── build_checklist.py     Phase 5: 62列 → 32列の再生成
│   ├── snapshot.py            Phase 6: 実機url_map → スナップショット
│   ├── diff_snapshot.py       Phase 6: スナップショット間の差分 + ゲート
│   ├── reconcile.py           Phase 6: スナップショット ↔ 台帳の突き合わせ
│   ├── detect_routes.py       ソース(AST)↔ 台帳の突き合わせ。実機不要
│   ├── changed_rows.py        Phase 6: git差分 → 再レビュー対象行
│   ├── fixtures.py            Phase 7: 到達可否測定用の最小コーパス投入
│   ├── probe_ci.py            Phase 7: フィクスチャ駆動の到達可否測定(CI が直接呼ぶ)
│   └── measure.sh             手作業で実測するときの唯一の入口(上記を固定順で回す)
├── tests/                     ツールの単体テスト(pytest。データ不要)
├── pytest.ini
├── ci/
│   ├── api-inventory-drift.yml    実機を起こして突き合わせる(60分枠)
│   ├── api-inventory-tests.yml    ツールの単体テスト(数秒。Secret 不要)
│   └── README.md              このファイル
└── .gitignore                 データ類を誤ってコミットしないための保険

$WEKO_API_INVENTORY_DIR/         ← プライベートリポジトリ。public リポジトリには置かない
├── weko3_api_list_full.tsv      台帳(62列・所見と実証結果つき)
├── weko3_api_list.tsv           台帳(32列)
├── weko3_api_list_README.md     32列の列定義・運用手順
├── weko3_api_list_full_README.md 62列の列定義
├── api_snapshot.json            経路のベースライン
├── reconcile_allow.json         実機に無いが台帳に残す行の許可リスト
├── detect_allow.json            ソースにあるが経路にならないものの許可リスト
├── reconcile_report.md          突き合わせ結果
├── tests/                       台帳そのものの検査(pytest。実機不要)
└── weko3_api_auth_findings.md   調査記録
```

`.gitignore` で `*.tsv` / `api_snapshot*.json` / `reconcile_*` 等を無視しているが、
これは保険であって設計ではない。**データを公開領域に置かないことが設計**。

---

## 2. 導入の順序（順序依存があるので守ること）

ベースライン `api_snapshot.json` が無いと `diff_snapshot.py` は動かない。
また台帳と実機が一致していないと `reconcile.py` が即 FAIL する。
**先にデータを入れ、最後にワークフローを有効化する。**

```bash
# --- プライベートリポジトリを用意する ---
git clone https://github.com/RCOSDP/weko-secret.git
export WEKO_API_INVENTORY_DIR=$PWD/weko-secret

cd <weko>          # WEKO3 リポジトリ(public)
git switch -c chore/api-inventory-drift

# 1) ツールだけを配置(データは置かない)
mkdir -p tools/api-inventory
# … scripts/ と ci/ を配置 …

# 2) 実機を起動
./install.sh

# 3) ベースラインを現行リビジョンで生成し、**プライベートリポジトリに**保存する
python3 tools/api-inventory/scripts/snapshot.py \
  --out "$WEKO_API_INVENTORY_DIR/api_snapshot.json"

# 4) 台帳と一致することを確認(0 でなければ先に台帳を直す)
python3 tools/api-inventory/scripts/reconcile.py --gate

# 4b) 到達可否まで測るなら measure.sh を使う(フィクスチャ投入から台帳反映まで一括)
#     測定条件は $WEKO_API_INVENTORY_DIR/measure_profile.json に置く。
tools/api-inventory/scripts/measure.sh --nos 34,925,25

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

**公開リポジトリにはデータを一切 commit しないこと。** `git status` で `tools/api-inventory/` 配下に
`*.tsv` や `api_snapshot.json` が現れたら、置き場所を間違えている。

また、プライベートリポジトリ側にも **weko と同名のブランチ**を作っておくこと(§3a)。

3 のベースラインは**そのブランチのリビジョンで取り直す**こと。
weko-document に置いてあるものは `d2fdc0e3b`(v2.0.3) 時点なので、
導入先のブランチが進んでいれば差分が出る。

---

## 3. ベースラインの更新ルール（これを決めないと形骸化する）

**API を変更した PR では、プライベートリポジトリ側の `api_snapshot.json` を更新する。**
公開リポジトリのコード変更と、プライベートリポジトリ側のベースライン更新は**別の PR になる**。
案C(データを公開領域に置かない)の代償で、ここだけは手順が2つに分かれる。

```bash
# API を変更した PR の作業ブランチで
./install.sh
python3 tools/api-inventory/scripts/snapshot.py \
  --out "$WEKO_API_INVENTORY_DIR/api_snapshot.json"
# → プライベートリポジトリ側で commit / PR を作る
#    ブランチ名は weko 側の作業ブランチと**同名**にする(§3a)
```

差分は**プライベートリポジトリの `git diff`** に出る。「どの経路が増えたか・認証がどう変わったか」を
レビュアの目に入れる仕組みは維持されるが、見る場所がプライベートリポジトリ側になる。
公開リポジトリの CI は件数だけを報告し、詳細は出さない。

なお PR の CI は「PR ブランチの実機」と「**対応するブランチの**ベースライン」を比べるため
(対応の決め方は §3a)、ベースラインを更新すると差分は 0 になる。
**変更の妥当性を見るのは CI ではなくレビュア**で、
CI の役割は「ベースラインを更新せずに API を変えること」を防ぐことにある。

---

## 3a. ブランチの対応（weko ⇔ プライベートリポジトリ）

台帳とベースラインは **WEKO3 のブランチごとに内容が違う**。`develop_v2.0.4` のコードを
`main` の台帳と突き合わせれば、ブランチ間の経路差がそのまま A/B/C/D/E として出る。
件数が常に非ゼロになれば、そこから先は誰も読まなくなる。

**規則: プライベートリポジトリには、weko 側と同名のブランチを作る。**
`develop_v2.0.4` には `develop_v2.0.4`、`fix/issue62569` には `fix/issue62569`。

CI の `Resolve inventory ref` ステップが、次の順で使うブランチを決める。

| 順 | 見るブランチ | 使う場面 |
|---|---|---|
| 1 | PR の **head** ブランチ名 | 台帳更新 PR がまだマージされていない段階。作業ブランチ上の台帳を見る |
| 2 | PR の **base** ブランチ名 | 台帳を触らない PR。および両方がマージされた後の定常状態 |
| 3 | 既定ブランチ | 1・2 のどちらも無い場合。`::warning::` と PR コメント冒頭の警告を出して続行する |

採用したブランチ名は **PR コメントの冒頭に出る**。件数を読む前にそこを見ること。

### なぜ head を先に見るのか

公開リポジトリのコード変更と台帳更新は別 PR になる(§3)。base 同士だけで対応させると、
weko の PR の CI が回る時点で台帳更新はまだプライベートリポジトリの作業ブランチにあり、
`develop_v2.0.4` には入っていない。「プライベート側を先にマージしないと公開側の CI が
通らない」という直列の制約ができてしまう。head を先に見れば、2つの PR を並行して
レビューでき、マージ順にも依存しない。

```
RCOSDP/weko          fix/issue62569 ──PR──> develop_v2.0.4
                          │ 同名で対応する
RCOSDP/weko-secret   fix/issue62569 ──PR──> develop_v2.0.4
```

作業ブランチは**両方のリポジトリで同じ名前**にする。台帳を触らない変更なら
プライベート側にブランチを作らなくてよい(2 の base 解決に落ちる)。

### 対応ブランチが無いとき

ジョブは止まらないが、出る件数は当てにならない。新しいリリースラインを切ったら、
プライベートリポジトリ側にも同名ブランチを作り、そのリビジョンでベースラインを
取り直すこと(§2 の 3、§3b)。

FAIL にせず警告に留めているのは、対応ブランチの無いリリースラインで一律にすべての PR が
止まるのを避けるため。**警告が出ている PR の件数を「PASS だった」と読まないこと。**

---

## 3b. ベースラインは CI と同じ環境で作る

`api_snapshot.json` は `meta.packages` にインストール済みパッケージの版を持ち、
`diff_snapshot.py` の W6 がその差を検知する。**ベースラインを CI と違う環境で作ると、
毎回 W6 が出続けて警告が形骸化する。**

実測: 手元の docker 環境で作ったベースライン(302パッケージ)を、CI の
`install.sh --no-cache` で作った環境(301パッケージ)と比べると W6 が2件出た。
経路(endpoints=860 / AST結合=495 / 属性不明=365)は完全に一致していたので、
差は依存の版だけ。

対処: **ベースラインは `install.sh` で作った環境から生成する**。

```bash
./install.sh          # CI と同じ手順で作り直す
python3 tools/api-inventory/scripts/snapshot.py \
  --out "$WEKO_API_INVENTORY_DIR/api_snapshot.json"
```

W6 は WARN なのでゲートは通るが、放置すると本当の依存更新に気づけなくなる。

---

## 3c. WEKO3 のバージョンごとにタグを打つ

台帳は「どのリビジョンの WEKO3 に対する調査結果か」が分からないと意味を失う。
`api_snapshot.json` の `meta.revision` / `meta.tag` に生成元は記録されるが、
**プライベートリポジトリ側にも同名のタグを打って対応を固定する**。

```bash
cd "$WEKO_API_INVENTORY_DIR"
git tag -a v2.0.3 -m "WEKO3 v2.0.3 (RCOSDP/weko d2fdc0e3b) 時点の API インベントリ

対象: RCOSDP/weko d2fdc0e3b62479a362d9ace6216316630ad654a6 (tag v2.0.3)
台帳: 926行 / 経路 URI 870 / 実機との突き合わせ差分 0"
git push origin v2.0.3
```

タグ名は **WEKO3 側のタグと同じ**にする(`v2.0.3` なら `v2.0.3`)。
ブランチを同名で対応させる(§3a)のと同じ理由で、タグも同名で対応させる。
メッセージには対象コミットの完全な SHA と、その時点の台帳規模・突き合わせ結果を残す。

### バージョンアップ時の流れ

0. プライベートリポジトリに **WEKO3 と同名のブランチ**を作る(§3a)
1. WEKO3 の新バージョンで `install.sh` → `snapshot.py` でベースラインを作り直す
2. `reconcile.py` の差分を 0 にする(新規経路を台帳に追加、消えた経路を整理)
3. `changed_rows.py` が出す行を Phase 2-3 で再確認する
4. プライベートリポジトリを commit し、**WEKO3 と同名のタグを打つ**

タグを打たずに台帳だけ更新すると、過去のバージョンに対する調査結果を後から
参照できなくなる(インシデント調査や監査で「その時点でどうだったか」を問われる)。

---

## 4. ゲートが FAIL したときの対処

ジョブが落ちる条件は3つ。どのステップで落ちたかで切り分ける。

| 落ちた場所 | 落ちる条件 |
|---|---|
| `diff_snapshot.py --gate` (`drift.md`) | G1〜G7 のいずれかに該当 |
| `reconcile.py --gate` (`reconcile.md`) | A + B + C + D + E の合計が 1 件以上 |
| `probe_ci.py --gate` | G8 / G9 に該当（明細を含むため artifact には上げていない。件数は Actions のログ） |

| ゲート | 意味 | 対処 |
|---|---|---|
| G1 新規経路に認証デコレータが無い | 認証の付け忘れの可能性 | 意図的な公開なら台帳に根拠を書いたうえでベースライン更新。そうでなければ実装を直す |
| G2 認証デコレータが削除された | | 同上 |
| G3 認証のコメントアウトが増えた | no.34(IIIF)と同型 | 原則やり直し。残すなら理由をコード中のコメントに明記 |
| G4 config が危険側に変わった | no.10/519/520/920 と同型。`*_PERMISSION_FACTORY=None` / CSRF保護=False / 認証の全無効化=True | 原則やり直し |
| G5 ModelView の can_delete/can_export 有効化 | 削除・全件CSV出力面が開く | 意図的なら台帳の data_op を更新 |
| G6 属性不明の経路が増えた | 外部ライブラリ由来など | 台帳に行を追加してから `reconcile.py` を通す |
| G7 依存更新で経路が増減 | Flask-IIIF 等 | 増えた経路を台帳に追加。減った場合は該当行を削除するか allow に登録 |
| G8 未認証で到達する書き込み系 | 台帳の `data_op` が作成/更新/削除の行に、匿名で到達した | 原則やり直し。意図的な公開なら台帳の根拠を更新。`data_op` の記載誤りなら台帳を直す |
| G9 台帳では遮断だが実測で到達 | 認可の回帰 | 原則やり直し |
| reconcile A(未収載) | 実機にあるが台帳に無い(URI 単位) | `weko3_api_list_full.tsv` に行を追加 → `build_checklist.py` で24列版を再生成 |
| reconcile B(実機に無い) | 台帳にあるが url_map に登録されていない | 理由を確認し `reconcile_allow.json` に**理由付きで**登録。理由なしの登録は禁止 |
| reconcile C/D | メソッド・app列の記載誤り | 台帳を実機に合わせる |
| reconcile E(endpoint 未収載) | 同じ URI に複数の Blueprint/設定が登録されていて、URI 単位の A では拾えない取りこぼし | 台帳は endpoint 単位で行を持つ方針なので、行を追加する |

`reconcile_allow.json` に登録済みの行は **B'(既知・許容)** として別枠で数え、ゲートには効かない。
**E'(endpoint が実機に無い)** も参考表示のみでゲート対象外。

「とりあえず allow に入れて通す」を防ぐため、`reconcile_allow.json` は
**理由の文字列が必須**（キーの値が説明文になっている）。レビューで理由を読むこと。

### WARN(W1〜W6)はゲートを通すが、レビューでは見る

| WARN | 意味 |
|---|---|
| W1 | ModelView が追加された(1つにつき自動生成8ルート・削除系を含む) |
| W2 | デコレータ据置きで実装本体が変化(認可ロジックを内包している可能性) |
| W3 | HTTPメソッドが増減した |
| W4 | URL が変化した |
| W5 | 監視対象 config が変化した(危険側の値でなければ WARN) |
| W6 | 依存パッケージの版が変化した |

W6 は §3b のとおり、ベースラインを CI と違う環境で作ると出続けて形骸化する。

---

## 5. プロファイル（条件付き blueprint 登録への対応）

`weko-notifications/ext.py:41` や `invenio-accounts/ext.py:168` のように
config で blueprint 登録を分岐している箇所があるため、**1プロファイルのダンプでは
他の設定で有効になる経路を見落とす**。

CI は既定プロファイル(`--profile default`)のみを回す。全機能を有効にした
プロファイルを追加する場合は、ベースラインをプロファイルごとに持つ。

```bash
python3 tools/api-inventory/scripts/snapshot.py \
  --out "$WEKO_API_INVENTORY_DIR/api_snapshot.full.json" --profile full-features
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
export WEKO_API_INVENTORY_DIR=/path/to/weko-secret
./install.sh
# --container は省略してよい(compose のラベルから web を自動検出する。§6 参照)
python3 tools/api-inventory/scripts/snapshot.py --out /tmp/new.json
python3 tools/api-inventory/scripts/diff_snapshot.py \
  "$WEKO_API_INVENTORY_DIR/api_snapshot.json" /tmp/new.json --out /tmp/drift.md
python3 tools/api-inventory/scripts/reconcile.py --snapshot /tmp/new.json --out /tmp/reconcile.md
python3 tools/api-inventory/scripts/changed_rows.py <前回タグ> HEAD --out /tmp/rerun_nos.txt

# 到達可否まで測る場合(データが変わるので使い捨て環境で)
tools/api-inventory/scripts/measure.sh --nos "$(paste -sd, /tmp/rerun_nos.txt)"
```

ただし「ベースラインを更新せずに API を変えること」は防げないため、
検知が漏れるのはリリース直前になる。
