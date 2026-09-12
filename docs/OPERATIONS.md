# WEKO3 作業手順

> **素案 / DRAFT** — チームレビュー前。
> **ルール（なぜそうするか・何を守るか）は `docs/RULE.md`。本書は手順だけを書く。**

## 0. この文書の使い方

上から順に実行すれば終わる形で書いてある。**判断に迷ったら手を止めて `docs/RULE.md` を見る。**

| やりたいこと | どこ |
|---|---|
| いま自分がどの段階にいるか確かめる | §1 全体像 |
| 事前準備（ソフトのインストール・環境変数・実機の起動） | §2 |
| PR を出す | §3 |
| リリースする（棚卸しとタグ） | §4 |
| 始める前に前提がそろっているか見る | §2-6 `tools/release/preflight.sh` |
| ルール・用語・決定の記録 | `docs/RULE.md` |
| 台帳そのものの作り方、CI の設置 | `tools/api-inventory/scripts/README.md` / `ci/README.md` |

---

## 1. 全体像

**どこに何が書いてあるか。** 自分がいま何段階目にいるかを確かめてから読むこと。

| 段階 | やること | 書いてある場所 |
|---|---|---|
| 0. 環境をそろえる | ソフトのインストール・環境変数・実機の起動（最初の 1 回だけ） | §2 |
| 1. リリースラインを切る | `develop_v2.x.y` を作り、**private 側にも同名ブランチを作る** | `docs/RULE.md` 規則 2-2 |
| 2. 開発ブランチを作る | 作業ブランチを切る（台帳を触るなら private 側も同名で） | §3 手順 1 |
| 3. PR を出す前 | テストを通す・台帳を更新する・`preflight.sh` | §3 手順 2-3 |
| 4. PR を出す | public 側と、台帳を触ったなら private 側の 2 本 | §3 手順 4-7 |
| 5. レビュー〜マージ | 全指摘への反応、マージ条件 | `docs/RULE.md` §5-2 / §5-4 |
| 6. **リリース（棚卸しとタグ）** | 全経路の棚卸し・CHANGELOG・両リポジトリに同名タグ | **§4** |
| 7. リリース後 | 保留したものの引き継ぎ | §4 の最後 |

段階 0 は最初の 1 回だけ、段階 1・6 はリリースのたびに 1 回、段階 2〜5 は PR のたびに毎回回る。

---

## 2. 事前準備（最初に 1 回だけ）

**新しい端末で作業を始めるときは、まずこの節を通す。** ここでそろえたものは §3（PR）と §4（リリース）の両方で使う。
一度そろえたら、次からは 2-6 の確認コマンドだけでよい。

### 2-1. 必要なソフトウェア

| ソフト | 何に使うか | 確認コマンド |
|---|---|---|
| `git` | ソースとブランチの操作 | `git --version` |
| `gh`（GitHub CLI） | PR の作成・CI の確認・レビュー依頼 | `gh --version` |
| `docker` / `docker compose` | 実機（WEKO3 スタック）の起動と操作 | `docker ps` |
| `python3` | 台帳スクリプト（`tools/api-inventory/scripts/*.py`） | `python3 -V` |
| `curl` | 経路の到達確認 | `curl --version` |

**PR まわりは `gh` を標準とする。** ブラウザでもできるが、手順書にコマンドで残せるほうが間違いが少ない。

```bash
# gh — RHEL / Rocky / AlmaLinux
sudo dnf install -y gh
# gh — Ubuntu / Debian
sudo apt install -y gh
# 入らないときは公式手順: https://github.com/cli/cli#installation
```

`docker` はディストリの公式手順で入れる。**`sudo` なしで `docker ps` が通ること**を確認する
（通らなければ `sudo usermod -aG docker $USER` のあと、ログインし直す）。

### 2-2. `gh` を認証する

```bash
gh auth login      # GitHub.com / HTTPS / ブラウザ認証 でよい
gh auth status     # ✓ Logged in to github.com と出れば完了
```

**`RCOSDP/weko`（public）と `RCOSDP/weko-secret`（private）の両方にアクセスできること。**
private 側が見えないなら、push 権限を管理者に依頼する。台帳を触る作業はそこが無いと進まない。

### 2-3. リポジトリを 2 つ用意する

| リポジトリ | 中身 | 公開範囲 |
|---|---|---|
| `RCOSDP/weko` | コード・ツール・CI の定義 | **public** |
| `RCOSDP/weko-secret` | 台帳（`weko3_api_list*.tsv`）とベースライン（`api_snapshot.json`） | private |

```bash
git clone https://github.com/RCOSDP/weko.git         ~/weko
git clone https://github.com/RCOSDP/weko-secret.git  ~/weko-secret
```

**private 側を public リポジトリの中に置かない。** 誤って commit する事故を防ぐため、
必ず別の場所に clone する（`docs/RULE.md` §1）。

### 2-4. 環境変数を設定する

| 変数 | 既定 | 何のためか |
|---|---|---|
| `WEKO_API_INVENTORY_DIR` | **なし（必須）** | 台帳とベースラインの置き場所。台帳スクリプトは全部これを見る |
| `WEKO_WEB_CONTAINER` | `weko-web-1` | 実測で 500 が出たとき `docker logs` を引く先 |
| `WEKO_BASE_URL` | `https://localhost:8443` | 実機を叩くときの URL。到達確認と実測の宛先 |
| `WEKO_HOST_HEADER` | `weko3.example.org` | 実機に送る `Host` ヘッダ。`docker-compose.yml` の `INVENIO_WEB_HOST_NAME` に合わせる |
| `INV` | — | `tools/api-inventory/scripts` の打鍵を短くするだけ。本書のコマンドはこれを使う |
| `WEKO_PUBLIC_REPO` / `WEKO_PRIVATE_REPO` | `RCOSDP/weko` / `RCOSDP/weko-secret` | 変える必要はほぼ無い（`open-pr.sh` が読む） |

```bash
export WEKO_API_INVENTORY_DIR=~/weko-secret
export WEKO_WEB_CONTAINER=weko-web-1
export WEKO_BASE_URL=https://localhost:8443
export WEKO_HOST_HEADER=weko3.example.org
export INV=tools/api-inventory/scripts
```

**実機の場所（コンテナ名・URL・Host）を既定から変えているなら、この 3 つを必ず設定する。**
台帳ツールは初回に `$WEKO_API_INVENTORY_DIR/measure_profile.json` を作るとき、この 3 つを既定値として書き込む。
**作られたあとは JSON が正**で、環境変数を変えても既存のファイルは書き換わらない
（測定条件を変えたいときは JSON を直す。`tools/api-inventory/scripts/README.md`）。

毎回打つのが面倒なら前の 2 つを `~/.bashrc` に書いてよい。
**`INV` は相対パスなので、`~/weko` の中で作業しているときしか使えない。**

### 2-5. 実機を起動する

```bash
cd ~/weko
./install.sh          # 数十分かかる。CI と同じ手順で作られる
```

起動したことを 2 つで確かめる。

```bash
docker ps --format '{{.Names}}' | grep -x "$WEKO_WEB_CONTAINER"    # 名前が出れば起動している
curl -sk -o /dev/null -w '%{http_code}\n' -H "Host: $WEKO_HOST_HEADER" "$WEKO_BASE_URL/"   # 200
```

**ベースラインは必ずこの `install.sh` 環境から作る**（`docs/RULE.md` §3-1）。
手元で適当に組んだ docker 環境で作ると、依存パッケージの版差で警告が出続け、本当の依存更新に気づけなくなる。

### 2-6. そろったことを機械に確認させる

```bash
tools/release/preflight.sh --base develop_v2.1.0
```

gh の認証・台帳の置き場所・public と private のブランチ対応・実機の応答までまとめて見る。
**❌ が 1 つも無くなってから §3 / §4 へ進む。** ❌ の行には直し方が出る。

```text
[ OK ] gh が認証済み（mhaya）
[ NG ] WEKO_API_INVENTORY_DIR が未設定
    → git clone https://github.com/RCOSDP/weko-secret.git ~/weko-secret && export WEKO_API_INVENTORY_DIR=~/weko-secret
```

---

## 3. PR を出す手順

初めて出す人はここだけ順に追えばよい。**レビューとマージのルールは `docs/RULE.md` §5。**

**前提は §2 で済ませてあること**（`gh` の認証・環境変数・実機）。まだなら §2 へ戻る。

```bash
tools/release/preflight.sh --base develop_v2.1.0   # ❌ が無くなるまで直してから始める
```

1. **作業ブランチを切る。** 名前は既存に合わせる（`fix/issue62764` / `hotfix/issue62807` /
   `feature/<名前>`）。base は原則 `develop_v2.x.y`。
   **台帳を触るなら、private 側にも同名のブランチを切る**（`docs/RULE.md` 規則 2-1）。
2. **commit する。** `git status` に `*.tsv` / `api_snapshot.json` が出ていないことを確認する（`docs/RULE.md` §1）。
3. **API を変えたなら、先に private 側の台帳を更新する**（`docs/RULE.md` §3-1）。
   公開側のコードと台帳は**別の PR**になる。

   ```bash
   ./install.sh                                    # ベースラインは install.sh 環境で作る
   python3 $INV/snapshot.py --out "$WEKO_API_INVENTORY_DIR/api_snapshot.json"
   # → private 側の同名ブランチで commit する（PR は手順 4 の --inventory で出る）
   ```
4. **PR を出す。**

   ```bash
   tools/release/open-pr.sh --base develop_v2.1.0                      # まず表示だけ（何も起きない）
   tools/release/open-pr.sh --base develop_v2.1.0 --run                # public 側の PR を作る
   tools/release/open-pr.sh --base develop_v2.1.0 --run --inventory    # private 側の台帳 PR も一緒に
   ```

   手で出すなら次と同じこと。

   ```bash
   git push -u origin <ブランチ>
   gh pr create --base develop_v2.1.0 --title "<タイトル>" --body-file .github/pull_request_template.md
   ```

5. **PR テンプレートのチェックボックスを埋める。**
   特に「🤖 0. CI 自動チェック (API Inventory Drift)」。埋めずに出さない。
6. **CI を待つ。**

   ```bash
   gh pr checks --watch      # Unit Tests / UI Tests / API Inventory Drift
   gh pr view --web          # コメントを読む
   ```

   **`API Inventory Drift` のコメントは、件数より先に冒頭のブランチ名を見る**（`docs/RULE.md` 規則 2-2）。
   警告が出ている PR の件数は当てにならない。
7. **レビューを依頼する。**

   ```bash
   gh pr edit --add-reviewer <github-id>
   ```

8. **指摘に反応を残す**（`docs/RULE.md` §5-2）。**マージの条件は `docs/RULE.md` §5-4。**

| やりたいこと | コマンド |
|---|---|
| 自分の PR を一覧する | `gh pr list --author "@me"` |
| CI の失敗ログを見る | `gh run view --log-failed` |
| 指摘を直して push した後の再確認 | `gh pr checks --watch` |
| Claude のレビューを回し直す | PR に `@claude` とコメントする |


## 4. リリース手順

> **この手順は 3 つの README から集めてある。** 年に数回しか回らない作業で、
> 初めての人が README を渡り歩くと確実に事故るため、ここに 1 本化した。
>
> **この節を直したら `tools/api-inventory/scripts/README.md`（ケース3）と
> `tools/api-inventory/ci/README.md`（§3b・§3c）も直すこと。** 内容が二重にあるので、
> 片方だけ直すとずれる。判断の背景と失敗の実例はそちらにある。

**所要は約 1.5 時間**（手順 7 の既存行の再レビューを除く。v2.0.3 → v2.1.0・478 コミットでの実績）。
**初めて回すなら、レビュアを 1 人つけて手順 3・4・10 の結果を見てもらうこと。**

### 始める前に

**環境は §2 でそろえてあること。** 加えてこの作業には次の 2 つが要る。

| | 内容 |
|---|---|
| 権限 | private リポジトリ `RCOSDP/weko-secret` への **push 権限**（読むだけでは回らない） |
| 知識 | 用語（台帳・ベースライン・ゲート）は `docs/RULE.md` §8 を先に読む |

```bash
cd ~/weko                                          # 以降のコマンドは全部ここで打つ
tools/release/preflight.sh --base develop_v2.1.0   # ❌ が 1 つも無くなってから手順 0 へ
```

以下、例として **前タグ `v2.0.4` → 新タグ `v2.1.0`** を使う。自分のバージョンに読み替えること。

---

### 手順 0. private 側に同名ブランチを作る

`docs/RULE.md` 規則 2-1 / 2-2。**これを飛ばすと CI が既定ブランチの台帳と比べ、出る件数が当てにならなくなる。**

```bash
git -C "$WEKO_API_INVENTORY_DIR" switch -c develop_v2.1.0 origin/main
```

ブランチ名は **public 側の対象ブランチと完全に同じ**にする。以降の private 側の作業は全部このブランチ上で行う。

### 手順 1. 対象ブランチにツールがあることを確認する

**ここで最初に詰まる。** `tools/api-inventory/` は**ツールを入れたブランチにしか存在しない**ので、
対象ブランチへ切り替えるとスクリプトごと消えることがある。

```bash
git switch develop_v2.1.0
ls $INV/snapshot.py || git checkout <ツールのあるブランチ> -- tools/api-inventory .github/workflows/api-inventory-drift.yml
```

### 手順 2. 実機を新バージョンに合わせる

ブランチを切り替えただけでは**稼働中の uwsgi は古いコードのまま**で、
「測っているつもりのバージョンと違うものを測る」ことになる。egg-info を作り直して再起動する。

```bash
docker exec "$WEKO_WEB_CONTAINER" bash -lc 'cd /code && for d in modules/*/; do (cd "$d" && python setup.py -q egg_info); done'
docker restart "$WEKO_WEB_CONTAINER"
```

**確認（必須）**: そのバージョンにしか無い／無くなった経路を 1 つ叩き、期待どおりのコードが返ること。

```bash
curl -sk -o /dev/null -w '%{http_code}\n' -H "Host: $WEKO_HOST_HEADER" \
  "$WEKO_BASE_URL/api/admin/get_widget_item_list"
# 旧バージョンへ戻したなら 404 になるはず。500 が返るなら古いコードがまだ生きている
```

続けて **Alembic の適用状況**を見る。スキーマが古いと手順 6 の probe が 500 を返し、
**認可の穴と区別がつかなくなる。**

```bash
docker compose exec web invenio alembic current | tail -5
git log --oneline v2.0.4..HEAD -- '*/alembic/*'     # 追加リビジョンを洗い、適用済みか確かめる
```

### 手順 3. ベースラインを作り直す

**ベースラインは必ず `install.sh` で作った環境から生成する。** 手元の docker 環境で作ると
依存パッケージの版差で W6 が出続け、本当の依存更新に気づけなくなる。

```bash
./install.sh                                          # 数十分かかる
python3 $INV/snapshot.py --out /tmp/snap_new.json
python3 $INV/diff_snapshot.py "$WEKO_API_INVENTORY_DIR/api_snapshot.json" /tmp/snap_new.json
```

差分（ADDED / REMOVED）を読んで納得してから置き換える。**読まずに上書きしない。**

```bash
cp /tmp/snap_new.json "$WEKO_API_INVENTORY_DIR/api_snapshot.json"
```

> 途中で何度も試したいだけなら `install.sh` は要らない（`snapshot.py` は毎回新しいプロセスで動くため
> ブランチ切り替えだけで通る）。ただし**最後に確定させる 1 本は `install.sh` 環境で取り直す。**

### 手順 4. 台帳の差分を 0 にする

```bash
python3 $INV/reconcile.py                    # A（実機にあるが台帳に無い）に endpoint 名が出る

# 出た endpoint を 1 件ずつ追加する。まず表示して中身を見る（--append が無ければ書き込まない）
python3 $INV/add_row.py --endpoint api:weko_admin.get_widget_item_list
python3 $INV/add_row.py --endpoint api:weko_admin.get_widget_item_list --append
# endpoint 名が分からなければ URI の一部でも引ける
python3 $INV/add_row.py --uri /api/items/import-task --append

python3 $INV/reconcile.py --gate             # 「✅ 一致(0件)」になるまで繰り返す
```

消えた経路（B）は `reconcile_allow.json` に**理由付きで**登録する。理由なしの登録は禁止（`docs/RULE.md` §3-3）。

**外部調査と件数が合わないときは、まず相手の環境を疑う。**
v2.1.0 ではベンダ資料が新規 23 件としていたが、ソースに存在したのは 5 件だけだった。
残り 18 件は `modules/` ではなく site-packages 側の pip パッケージの版差が原因で、grep しても 1 件も出なかった。

### 手順 5. 新規行を埋める

`add_row.py` が埋めるのは機械的に決まる 26 列だけで、残りは `TODO` が入っている。
機械付与 → 実装読解の順で潰す。機械付与は**空欄／TODO セルしか触らない**ので既存値は壊れない。

```bash
for s in add_cols add_ssrf_redirect add_idempotency add_dataop4 add_authmech add_reqinfo; do
  python3 $INV/$s.py
done
```

残る列は実装を読んで手で埋める（`summary` / `response*` / `status_codes` / `exceptions` / `roles` /
`access_variance` / `data_store` / `side_effects` / `config_deps` / `category_tags` / `notes` / `sec_*` 5 列）。
v2.1.0 実績で 5 行あたり機械付与 3 分＋手作業 20 分。

### 手順 6. 実測する

**入口は `measure.sh` だけ。** 個別スクリプトを直接叩くと条件がずれてバージョン間で比較できなくなる。

```bash
$INV/measure.sh --nos 927,928,929,930,931     # 手順 5 で足した no を指定。全行なら引数なし
```

**既定で書き込み系も測る**（`measure_profile.json` の `allow_writes` が `true`）。実機のデータが
書き換わるので、**使い捨て環境で回すか、終わったら `./install.sh` で作り直すこと。**

測り終えたら、結果をそのまま信じずに次を確認する。**静かに壊れるのはこの 2 つ。**

- 全識別子で「遮断」になっている行の割合 — 管理系が多い母集団で **8 割を超えたらセッション切れを疑う**
- `sysadmin` の到達率 — 管理系エンドポイントなら高いはず。低すぎるなら測定が壊れている

個々の判定でも次は疑ってかかる。

| 出力 | 実態 | どうするか |
|---|---|---|
| `到達(転送)` | 「拒否して一覧へ戻した」かもしれない | 併記された転送先 URL を見る。迷ったら DB で副作用の有無を確かめる |
| `502` → 判定不能 | nginx の一過性エラー | 手で 2 回叩いて確定させる |
| 単発の意外な結果 | 直前の行が環境を壊した可能性 | **その行だけ単独で測り直す** |

### 手順 7. 既存行への影響を洗う

**必ず `refresh_impl.py` を先に流す。** 台帳の `impl_line` はバージョンアップで関数がずれても
更新されず、`changed_rows.py` は行番号で突き合わせるため、**ずれたまま流すと対象行を取り違える。**

```bash
python3 $INV/refresh_impl.py                  # まず差分だけ見る
python3 $INV/refresh_impl.py --write          # 納得したら書き戻す
python3 $INV/changed_rows.py v2.0.4 HEAD --out /tmp/rerun.txt
```

> v2.1.0 実績: 直さずに流すと対象 41 行、直してから流すと 31 行。
> 差は「変わっていないのに拾われた 12 行」と「変わったのに漏れた 2 行」。

**出力末尾の 2 つの報告を必ず読む。** ここが自動化できない部分で、実際に穴が見つかっている。

- 「台帳のエンドポイントではないが変更されたヘルパ関数」— `grep` で呼び出し元を辿る
- 認可ヘルパの変更（`permission` / `role` / `group` / `auth` / `can_` / `check_` を含む関数）

> v2.1.0 実績: `weko_index_tree/utils.py` の `check_index_permission_by_role_and_group` が
> 索引の閲覧判定を `check_roles OR check_groups` から **AND** に変えていた。
> このファイルには台帳行が無いため、行単位の報告には一切出てこなかった。

**時間が取れないときは、既存行の再レビューを次サイクルに回してよい。**
その場合は**保留した旨を台帳と PR に必ず記録する**（記録しなければ、やったのか忘れたのか区別がつかなくなる）。

### 手順 8. 再計算してゲートを通す

```bash
python3 $INV/refresh_impl.py --write     # impl_line を新バージョンのソースへ追随させる
python3 $INV/enrich_git.py   --write     # last_commit / date / subject / release_tag
python3 $INV/test_coverage.py
python3 $INV/prioritize.py
python3 $INV/build_checklist.py
python3 $INV/reconcile.py --gate         # exit 0 を確認する
```

順序に意味がある（`prioritize.py` は `test_coverage.py` の結果を読む）。上から順に流すこと。

**確認**: `release_tag` 列に今回のタグが 1 行も出てこなかったら、先頭 2 本を回し忘れている。

```bash
grep -c 'v2.1.0' "$WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv"
```

### 手順 9. CHANGELOG を確定する（public 側）

`CHANGELOG.md` / `CHANGELOG_ja.md` の `## [Unreleased]` に積んだ項目を、
**今回のバージョンの見出しへ移す**（[Keep a Changelog](http://keepachangelog.com/) 形式）。

```markdown
## [Unreleased]
### 新機能
### 既存機能の変更
...

# [v2.1.0] 2026-09-11
### 新機能
- （Unreleased から移した項目）
```

`## [Unreleased]` の空の見出しは**残す**（次のリリースで使う）。日本語版と英語版の両方を直す。

### 手順 10. PR を出し、マージし、両リポジトリに同名タグを打つ

**先に public 側にデータが紛れ込んでいないことを確認する。**

```bash
git status --short           # tools/api-inventory/ 配下に *.tsv / api_snapshot.json が出たら置き場所の間違い
```

private 側を commit して PR を出す（`docs/RULE.md` 規則 2-2 の実例と同じ形：同名ブランチ → `main` へ PR）。

```bash
cd "$WEKO_API_INVENTORY_DIR"
git add -A && git commit -m "chore: WEKO3 v2.1.0 時点の棚卸し"
cd -
tools/release/open-pr.sh --base develop_v2.1.0 --run --inventory
gh pr checks --watch
```

**マージしてから**、両リポジトリに**同名のタグ**を打つ（`docs/RULE.md` 規則 2-3）。

```bash
# public 側
git tag -a v2.1.0 -m "WEKO3 v2.1.0"
git push origin v2.1.0

# private 側（メッセージに対象コミットの完全な SHA と台帳規模を残す）
cd "$WEKO_API_INVENTORY_DIR"
git switch main && git pull
git tag -a v2.1.0 -m "WEKO3 v2.1.0 (RCOSDP/weko <完全な40桁SHA>) 時点の API インベントリ

対象: RCOSDP/weko <完全な40桁SHA> (tag v2.1.0)
台帳: <行数>行 / 経路 URI <数> / 実機との突き合わせ差分 0"
git push origin v2.1.0
```

**タグを打たずに台帳だけ更新すると、「そのバージョンの時点でどうだったか」を後から参照できなくなる。**
インシデント調査や監査で必ず問われる。

---

### 終わったことの確認

全部 ✅ になって完了。1 つでも欠けていたら、その手順に戻る。

- [ ] private 側に public と同名のブランチがある（手順 0）
- [ ] ベースラインを `install.sh` 環境で取り直した（手順 3）
- [ ] `reconcile.py --gate` が exit 0（手順 4・8）
- [ ] 新規行の実測が済んでいる。または保留を記録した（手順 6）
- [ ] `changed_rows.py` のヘルパ報告と認可ヘルパ報告を読んだ。または保留を記録した（手順 7）
- [ ] `release_tag` に今回のタグが入っている（手順 8）
- [ ] CHANGELOG の `[Unreleased]` を今回のバージョンへ移した（手順 9）
- [ ] public 側に `*.tsv` / `api_snapshot.json` を commit していない（手順 10）
- [ ] 両リポジトリに同名のタグを打って push した（手順 10）

### リリース後にやること

- **保留したものを次サイクルへ引き継ぐ。** 手順 6・7 で後回しにした行、`xfail` で受け止めたテスト
  （例: `docs/v2.1.0-test-reconciliation.textile`）を、次のリリースラインの課題として残す。
- **次のリリースラインを切ったら、private 側にも同名ブランチを作る**（`docs/RULE.md` 規則 2-2）。ここを忘れると、
  そのライン上の全 PR で台帳ブランチ名の警告が出続ける。

### 困ったとき

| 症状 | 原因 | 対処 |
|---|---|---|
| `no python application found` / `AttributeError: module ... has no attribute` | egg-info の再生成漏れ | 手順 2 をやり直す。再生成前後で件数が変わらないことを確認するまで確定させない |
| 切り替えたのに旧バージョンの経路が生きている | uwsgi が古いコードのまま | 手順 2 の再起動と確認コマンド |
| `reconcile.py` の件数が減らない | 台帳の行の追加漏れ、または `impl_file` の記載誤り | `reconcile.py`（`--gate` なし）で A/B/C/D/E の内訳を読む。詳細は `tools/api-inventory/ci/README.md` §4 |
| 測定結果が「ほぼ全部遮断」 | 書き込み系を叩いて自分のセッションを消した | 手順 6 の 2 つの確認。`--refresh-fixtures` で張り直して測り直す |
| ゲートが落ちて先へ進めない | G1〜G9 / reconcile A〜E | `docs/RULE.md` §3-3 の原則に従う。**G3/G4/G8/G9 の例外は RCOS 公開基盤チームリーダの承認が要る** |
| 台帳の数字が外部資料と合わない | 相手の環境差（pip パッケージの版など） | 手順 4。まずソースを grep して実在を確かめる |

判断に迷ったら止めて聞くこと。**「とりあえず allow に入れて通す」「期待値を実挙動に書き換える」は禁止。**
背景と失敗の実例は `tools/api-inventory/scripts/README.md`（ケース3）に全部残してある。

---
