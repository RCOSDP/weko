# 既知の不具合: 利用申請承認済みアカウントでもダウンロードボタンではなく申請ボタンが表示される

> この `feature/jgss` ブランチ上での作業・レビューにあたり、既知の別事象として最初に共有しておくノート。本PRのコード変更（ビルド修正・環境設定）そのものが原因の事象ではない。原因調査・改修方針は別途まとめ済みで、コードへの適用は本PRの範囲外（未実施）。

## 1. 事象

利用申請（usage application）が承認済み（承認済みステータス）のアカウントでログインし、当該アイテムの詳細画面にアクセスすると、期待される「ダウンロード」ボタンではなく「申請」ボタンが表示される。

## 2. 現在の対応状況

- 原因調査済み: `FilePermission.status` を承認時に `1`（承認済み）へ更新する処理が `feature/jgss` のコードに存在しないこと、および画面側の権限判定が実際の承認経路（`file_onetime_download` テーブル）を一切参照していないことが根本原因。
- `jgss-pre` ブランチの実装を参考にした改修案・結合テスト計画を作成済み。
- Redmineに起票済み（担当者に確認のこと。本ファイルにはチケット番号は含めていない）。
- 上記いずれもコードへの適用はまだ行っていない。本ブランチのビルド・レビューを進める上で、この事象が別途あることを認識しておくこと。

## 3. 詳しい調査資料

同一環境（`/home/vagrant`）内に以下の内部ドキュメントがある（このgitリポジトリには含まれない）。

- `doc/download_button_not_shown_for_approved_user_report_20260916.md` — 原因調査レポート
- `doc/download_button_fix_proposal_20260916.md` — 改修案（`jgss-pre`参考）
- `doc/download_button_fix_integration_test_plan_20260916.md` — 結合テスト計画

## 4. 再現用データ

本リポジトリに、この事象をレビュアの手元で再現するための**完全に合成した**デモデータ一式を同梱している。本番データ・個人情報は一切含まない（メールアドレスは `populate-instance.sh` が作るデモアカウント `contributor@example.org` のみ）。

- 置き場所: `scripts/demo/download_button_bug_repro/`
- 詳細手順: `scripts/demo/download_button_bug_repro/README.md`

### 投入（`install.sh` による通常の新規構築が済んだ後に実行）

```bash
./scripts/demo/download_button_bug_repro/load.sh
```

`fixture.sql`（PostgreSQL の差分行）と `es_bulk.ndjson`（Elasticsearch の当該アイテム文書）を投入する。自分が作る行だけを先に `DELETE` してから入れるため冪等で、既存行の変更・削除は行わない。

### 再現手順

1. `contributor@example.org` / `uspass123` でログインする。
2. `https://<host>/records/2003976`（「サンプル制限公開アイテム / Sample Restricted Item」）を開く。
3. ファイル `sample_restricted_data.txt` の行に、**「ダウンロード」ではなく「申請」ボタン**が表示される。押すと同じ利用申請ワークフローが最初から始まってしまう。

利用申請アクティビティ `A-20260917-00001` は `activity_status='F'`（承認・完了済み）であるにもかかわらず上記になる点が本事象である。

### DB 上のシグネチャ

| テーブル | 期待 | 実際 |
| --- | --- | --- |
| `workflow_activity` (`A-20260917-00001`) | `activity_status='F'` | `activity_status='F'` |
| `file_permission` (`record_id='2003976'`) | `status=1` の行がある | **行が 1 件もない** |
| `file_onetime_download` (`record_id='2003976'`) | — | `contributor@example.org` の行がある |

シェルからの検証は `docker compose exec -T web invenio shell /code/scripts/demo/download_button_bug_repro/verify.py` で行える。
