# リリース／PR 用のツール

手順そのものは `docs/OPERATIONS.md`（§2 事前準備、§3 PR を出す手順、§4 リリース手順）、ルールは `docs/RULE.md` にある。
ここに置くのは、その手順の中で「人が間違えやすいところ」を機械に確認させるための 2 本だけ。

| スクリプト | 何をするか | 書き換えるか |
|---|---|---|
| `preflight.sh` | 始める前の前提チェック（gh・docker・台帳の置き場所・ブランチの対応・実機の応答） | しない（読み取りだけ） |
| `open-pr.sh` | public 側と private 側の PR を同名ブランチで出す | `--run` を付けたときだけ |

```bash
export WEKO_API_INVENTORY_DIR=~/weko-secret
tools/release/preflight.sh --base develop_v2.1.0      # ❌ が無くなるまで直す
tools/release/open-pr.sh   --base develop_v2.1.0      # まず表示だけ
tools/release/open-pr.sh   --base develop_v2.1.0 --run --inventory
```

環境変数: `WEKO_API_INVENTORY_DIR`（private リポジトリのパス。必須）、
`WEKO_WEB_CONTAINER`（既定 `weko-web-1`）、`WEKO_PUBLIC_REPO` / `WEKO_PRIVATE_REPO`（既定 `RCOSDP/weko` / `RCOSDP/weko-secret`）。

**判断はしない。** ゲートが落ちたときにどうするか、台帳をどう直すかは人が決める（`docs/RULE.md` §3-3）。
