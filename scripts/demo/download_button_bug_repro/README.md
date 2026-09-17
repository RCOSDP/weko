# 再現用データ: 利用申請承認済みでもダウンロードボタンが出ない不具合

利用申請（usage application）が **承認済み・ワークフロー完了** のアカウントで
アイテム詳細画面を開いても、「ダウンロード」ボタンではなく「申請」ボタンが
表示されてしまう不具合を、PR レビュアが自分の環境で再現するためのデータ一式です。

不具合の概要は `KNOWN_ISSUE_download_button_not_shown.md` を参照してください。

---

## 0. このデータについて（重要）

**本番データ・個人情報は一切含まれていません。** すべて合成データです。

- メールアドレスは `populate-instance.sh` が作成するデモアカウント
  `contributor@example.org` のみ。
- アイテムのタイトル・本文・申請者氏名・所属はすべて架空
  （「サンプル制限公開アイテム」「デモ 太郎」「デモ 花子」「デモ大学」など）。
- 添付ファイルは中身のないプレースホルダ（`sample_restricted_data.txt`）。
- 実在の研究データ・研究者名・機関ドメインは含みません。

---

## 1. 前提

`install.sh`（= `populate-instance.sh` + `item_type3.sql` +
`resticted_access.sql`）による **通常の新規構築が完了している** こと。
本フィクスチャはその上に載る差分データのみを持ちます。依存しているのは
新規構築時点で必ず存在する以下だけです。

| 依存先 | 内容 |
| --- | --- |
| `item_type` 15 | デフォルトアイテムタイプ（フル）— 制限公開アイテム側 |
| `item_type` 31001 | 利用申請（`resticted_access.sql` が作成） |
| `accounts_role` 1–4 | System / Repository / **Contributor(3)** / Community |
| `accounts_user` | `repoadmin@` `contributor@` `user@` `comadmin@example.org` |
| `files_location` id=1 | 既定のファイル保存先 |
| `workflow_action` 1–4 | begin_action / end_action / item_login / approval |

デモアカウントのパスワードは `populate-instance.sh` が使う
`INVENIO_USER_PASS`（`docker-compose*.yml` の既定値は **`uspass123`**）です。

---

## 2. ロード方法

```bash
./scripts/demo/download_button_bug_repro/load.sh
```

`load.sh` は

1. `fixture.sql` を `docker exec -i weko-postgresql-1 psql -U invenio -d invenio` で流し込み
2. `es_bulk.ndjson` を `curl -X POST <ES>/_bulk` で投入

します。コンテナ名やポートが違う場合は環境変数で上書きできます。

```bash
PG_CONTAINER=weko-postgresql-1 ES_URL=http://localhost:29201 \
ES_INDEX=tenant1-weko-item-v1.0.0 ./scripts/demo/download_button_bug_repro/load.sh
```

`fixture.sql` は冒頭で自分が作る行だけを `DELETE` してから `COPY` するので、
**何度実行しても安全**（冪等）です。既存行の変更・削除は一切しません。

---

## 3. 投入されるデータ

| 対象 | ID |
| --- | --- |
| インデックス | `1758900000001`（デモ: 制限公開アイテム） |
| ワークフロー定義 | `workflow_flow_define` 39001 / `workflow_flow_action` 39001–39004 / `workflow_workflow` 39001（「デモ用データ利用申請 / Demo Data Usage Application」, `itemtype_id=31001`, `open_restricted=t`） |
| 制限公開アイテム | recid `2003976`（+バージョン `2003976.1`）／ファイル `sample_restricted_data.txt`（`accessrole = open_restricted`） |
| 利用申請アイテム | recid `2003977`（+バージョン `2003977.1`, item_type 31001） |
| 利用申請アクティビティ | `A-20260917-00001`（`activity_status = 'F'` = 完了、申請者 user_id=3 = contributor、承認者 user_id=2 = repoadmin） |
| ワンタイムDL許可 | `file_onetime_download`（`user_mail = contributor@example.org`） |
| **`file_permission`** | **行なし（これが不具合のシグネチャ）** |

`pidstore_pid` は 32056–32069 を明示 ID で使用します（新規構築直後の採番と
衝突しない領域。ロード後にシーケンスを `setval` で進めます）。

制限公開ファイルの `provide` には `role_id`/`workflow_id` と `role`/`workflow`
の両方の綴りを入れてあります。画面側の `get_usage_workflow`
(`weko_records_ui/views.py`) は前者を読み、JGSS のアイテムタイプが実際に
保存するのは後者、という食い違いがあるためです（調査レポート 4章参照）。

---

## 4. 再現手順

1. `load.sh` を実行する。
2. `contributor@example.org` / `uspass123` でログインする。
3. `https://<host>/records/2003976`（「サンプル制限公開アイテム / Sample
   Restricted Item」）を開く。
4. ファイル `sample_restricted_data.txt` の行のボタンを見る。

### 期待される結果（修正後）

利用申請は承認済み（`A-20260917-00001` は `activity_status='F'`）なので、
**「ダウンロード」ボタン** が表示され、ファイルをダウンロードできる。

### 実際の結果（不具合）

**「申請」ボタン** が表示される。押すと `/workflow/activity/init` が呼ばれ、
同じ利用申請ワークフロー（39001）を **もう一度最初から** 開始してしまう。

管理画面 → ワークフロー一覧 で `A-20260917-00001` が「完了」になっていること、
つまり「承認済みなのに申請ボタンのまま」であることを併せて確認できます。

---

## 5. DB 上のシグネチャ / シェルからの確認

```bash
docker compose exec -T web invenio shell \
    /code/scripts/demo/download_button_bug_repro/verify.py
```

不具合が再現している場合の出力：

```
activity_status                : activity_completed
file_permission rows           : 0
file_permission status=1 rows  : 0
file_onetime_download          : sample_restricted_data.txt contributor@example.org ...
check_file_download_permission : False
get_permission                 : None
check_content_file_clickable   : True
rendered button classes        : ['... term-condtion-modal', 'btn-start-workflow ...']
rendered download href present : False
=> BUG REPRODUCED: the approved applicant gets the "Apply" button.
```

SQL で直接見る場合：

```sql
SELECT activity_id, activity_status FROM workflow_activity
 WHERE activity_id = 'A-20260917-00001';          -- => F（完了）
SELECT * FROM file_permission WHERE record_id = '2003976';
                                                  -- => 0 rows（★これが原因）
SELECT file_name, user_mail, extra_info FROM file_onetime_download
 WHERE record_id = '2003976';                      -- => contributor@example.org の行
```

### なぜこうなるか

- `weko_records_ui/permissions.py` の `check_open_restricted_permission` /
  `check_permission_period` は **`file_permission.status == 1` の行があること**
  を承認済みの判定条件にしている。
- ところが `FilePermission.update_status()` を呼ぶコードが `feature/jgss` の
  `modules/` 配下に **一箇所も存在しない** ため、`status` が `1` になることがない。
- さらに承認完了時（`weko_workflow/views.py` の `next_action`, 1153–1156 行付近）で
  `FilePermission.delete_object()` により、申請時に作られた `status=-1` の行まで
  削除される。
- 承認の実体は `create_onetime_download_url_to_guest()`
  （`weko_workflow/utils.py`）による `file_onetime_download` への書き込みだが、
  詳細画面のボタン判定はこのテーブルを一切参照しない。

結果として `access_permission` は常に `False`、`permission` は常に `None` となり、
`weko_records_ui/templates/weko_records_ui/_macros.html` の
`{% elif not permission %}`（89 行目付近）の分岐に落ちて「申請」ボタンが描画される。

---

## 6. 付属ファイル

| ファイル | 内容 |
| --- | --- |
| `fixture.sql` | PostgreSQL の差分データ（`COPY ... FROM stdin` 形式、約 32KB） |
| `es_bulk.ndjson` | Elasticsearch `_bulk` 形式のアイテムドキュメント 4 件（約 12KB） |
| `load.sh` | 上記 2 つを投入するスクリプト |
| `verify.py` | 不具合が再現しているかを `invenio shell` から検証するスクリプト |
| `attach_file.py` | （任意）プレースホルダのファイル実体を `ObjectVersion` に紐付ける |

`fixture.sql` は `files_object` の行は入れますが **ファイル実体（バイト列）は
入れません**。ファイル実体は各環境の `files_location` 配下に置かれるもので、
git に入れるべきものではないためです。本不具合はボタンの描画判定の問題であり、
詳細画面は `records_metadata` の JSON だけを見てボタンを出し分けるため、
ファイル実体がなくても再現には影響しません。修正後に実際のダウンロードまで
試したい場合のみ `attach_file.py` を実行してください。
