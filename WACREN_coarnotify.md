# COAR Notify 機能 仕様・使い方メモ

対象ブランチ: `feature/nii_WACREN_pre`
調査日: 2026-08-04

WEKO3 の COAR Notify 対応（`weko-notifications` モジュール）について、
仕様・構成・設定方法・使い方を調査した記録。

---

## 1. 概要

`weko-notifications` は、アイテム登録・承認・削除といったワークフロー上のイベントを
**COAR Notify 準拠の通知（Linked Data Notification / ActivityStreams 2.0）** として
LDN Inbox に送信し、利用者に Web Push / メールで届けるモジュール。

WEKO本体は「通知の送信元（Sender）」であり、**Inbox 自体は別コンテナの外部サービス**
（`RCOSDP/coar-notify-inbox`）として動作する。

```
[WEKO app]  --(LDN POST: ldnlib.Sender)-->  [inbox:8080]  --(Web Push)-->  [ブラウザ]
     |                                           |
     |  <--(GET /inbox?target=...)---------------+
     |      通知一覧の取得 (ldnlib.Consumer)
     |
     +--(POST /subscribe, /userprofile, /push-template)--> [inbox:8080]
```

### 主な構成要素

| ファイル | 役割 |
|---|---|
| `notifications.py` | `Notification` クラスと `ActivityType` 列挙。通知ペイロードの組み立て |
| `schema.py` | marshmallow による COAR Notify ペイロードのバリデーション |
| `client.py` | `NotificationClient`。`py-ldnlib` を使った送信・取得 |
| `utils.py` | Inbox URL / ユーザURI の生成、SWORD経由の通知ヘルパ |
| `views.py` | 通知設定画面（UI）と通知取得API |
| `models.py` | `notifications_user_settings` テーブル（メール購読フラグ） |
| `forms.py` | 通知設定フォーム（Web Push / Email） |
| `ext.py` | 拡張初期化。`Link: rel="ldp#inbox"` ヘッダの付与 |
| `static/js/.../sw.js` | Web Push 用 Service Worker |
| `templates/.../push.json` | Push通知の文面テンプレート（en/ja） |

---

## 2. 通知の種類（ActivityType）

`notifications.py` の `ActivityType` 列挙で COAR Notify のパターンを定義。
`deletion_value` プロパティで末尾に `Delete` を付けた「削除版」を生成する。

| ActivityType | `type` の値 |
|---|---|
| `ACCEPT_REVIEW` | `["Accept", "coar-notify:ReviewAction"]` |
| `ACKNOWLEDGE_AND_REJECT` | `["Reject"]` |
| `ACKNOWLEDGE_AND_TENTATIVE_ACCEPT` | `["TentativeAccept"]` |
| `ACKNOWLEDGE_AND_TENTATIVE_REJECT` | `["TentativeReject"]` |
| `ANNOUNCE` | `["Announce"]` |
| `ANNOUNCE_ENDORSE` | `["Announce", "coar-notify:EndorsementAction"]` |
| `ANNOUNCE_INGEST` | `["Announce", "coar-notify:IngestAction"]` |
| `ANNOUNCE_RELATIONSHIP` | `["Announce", "coar-notify:RelationshipAction"]` |
| `ANNOUNCE_REVIEW` | `["Announce", "coar-notify:ReviewAction"]` |
| `OFFER_ENDORSE` | `["Offer", "coar-notify:EndorsementAction"]` |
| `OFFER_INGEST` | `["Offer", "coar-notify:IngestAction"]` |
| `OFFER_REVIEW` | `["Offer", "coar-notify:ReviewAction"]` |
| `UNDO` | `["Undo"]` |

### 実際に使われているイベントとファクトリメソッド

| ケース (`case`) | ファクトリメソッド | `type` |
|---|---|---|
| `registered` | `create_item_registered` | `Announce` + `IngestAction` |
| `request_approval` | `create_request_approval` | `Offer` + `EndorsementAction` |
| `approved` | `create_item_approved` | `Announce` + `EndorsementAction` |
| `rejected` | `create_item_rejected` | `Reject` |
| `deleted` | `create_item_deleted` | `Announce` + `IngestAction` + `Delete` |
| `deletion_request` | `create_request_delete_approval` | `Offer` + `EndorsementAction` + `Delete` |
| `deletion_approved` | `create_item_delete_approved` | `Announce` + `EndorsementAction` + `Delete` |
| `deletion_rejected` | `create_item_delete_rejected` | `Reject` + `Delete` |

`ACCEPT_REVIEW` / `ANNOUNCE_RELATIONSHIP` / `ANNOUNCE_REVIEW` /
`OFFER_INGEST` / `OFFER_REVIEW` / `UNDO` / `TentativeAccept` / `TentativeReject` は
**定義のみで、現時点では送信箇所が無い**（外部からの受信ペイロードのバリデーション用）。

---

## 3. 通知ペイロードの仕様

### 実例（承認依頼 = Offer + EndorsementAction）

```json
{
  "id": "urn:uuid:4123522e-8211-4bd2-9cef-24892a19b92f",
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://coar-notify.net"
  ],
  "type": ["Offer", "coar-notify:EndorsementAction"],
  "origin": {
    "id": "http://test_server.localdomain/",
    "inbox": "http://test_server.localdomain/inbox",
    "type": "Service"
  },
  "target": {
    "id": "http://test_server.localdomain/users/1",
    "inbox": "http://test_server.localdomain/inbox",
    "type": "Person"
  },
  "object": {
    "id": "http://test_server.localdomain/records/2000001",
    "ietf:cite-as": null,
    "object": null,
    "url": null,
    "type": ["Page", "sorg:WebPage"],
    "name": "A new record"
  },
  "actor": {
    "id": "http://test_server.localdomain/users/3",
    "type": "Person",
    "name": "Alex"
  },
  "context": {
    "id": "http://test_server.localdomain/workflow/activity/detail/A-20250306-00001",
    "ietf:cite-as": null,
    "type": ["Page", "sorg:WebPage"]
  }
}
```

### 各フィールドの意味と生成規則（`Notification.set_all`）

| フィールド | 必須 | 生成規則 |
|---|---|---|
| `id` | ○ | `urn:uuid:<uuid4>`。未指定なら自動採番 |
| `updated` | ○ | RFC3339形式。未指定なら現在時刻（既定 `Asia/Tokyo`） |
| `@context` | ○ | `COAR_NOTIFY_CONTEXT` 固定 |
| `type` | ○ | `ActivityType` の値。`validate_activity_type` で検証 |
| `origin` | ○ | サイトトップURL / Inbox URL / `"Service"` |
| `target` | ○ | 通知先ユーザURI (`<site>/users/{user_id}`) / Inbox URL / `"Person"` |
| `object` | ○ | 対象アイテムURL (`<site>/records/{recid}`) / `["Page","sorg:WebPage"]` / アイテムタイトル |
| `actor` | 任意 | 操作者のユーザURI / `"Person"` / ユーザ名（不明時は `"Unknown"`） |
| `context` | 任意 | ワークフローのアクティビティ詳細URL。`context_id` 指定時のみ |
| `inReplyTo` | 任意 | 返信元通知のID |

### バリデーション（`schema.py`）

`NotificationSchema`（marshmallow, `strict=True`）で `Notification.create()` /
`load()` / `validate()` 時に検証される。

- `validate_urn_uuid` — `id` が `urn:uuid:` で始まる正しいUUIDか
- `validate_rfc3339` — `updated` がRFC3339形式か
- `validate_activity_type` — `type` が `ActivityType` の値（または `Delete` 付き）か
- `validate_string_or_list` — `type` / `name` が文字列または文字列リストか

`ietf:cite-as` / `inReplyTo` / `mediaType` は Python 属性名と JSON キーが異なるため
`attribute` / `load_from` でマッピングしている。

---

## 4. 送信の流れと呼び出し箇所

### 4-1. ワークフロー経由（主経路）

`WorkActivity.notify_about_activity(activity_id, case)`
（`modules/weko-workflow/weko_workflow/api.py:3226`）が入口。

```python
if not current_app.config["WEKO_NOTIFICATIONS"]:
    return
activity = self.get_activity_by_id(activity_id)
if activity is None or activity.workflow.open_restricted:
    return
```

→ **`WEKO_NOTIFICATIONS` が False の場合と、制限公開ワークフローの場合は送信しない。**

`case` ごとに「通知先の決め方（getter）」と「通知の作り方（creater）」を選び、
`_notify_about_activity_wiht_case()` が対象ユーザ全員にループ送信する。
COAR Notify 送信と同時に、対応する `send_mail_*` でメール通知も行う。

| 呼び出し元 | `case` |
|---|---|
| `weko_workflow/views.py:2368` | `deletion_rejected` |
| `weko_workflow/views.py:2372` | `deletion_request` |
| `weko_workflow/views.py:2374` | `request_approval` |
| `weko_workflow/views.py:2405` | `approved` |
| `weko_workflow/views.py:2407` | `registered` |
| `weko_workflow/views.py:2436` | `deletion_approved` |
| `weko_workflow/views.py:2707` | `rejected` |
| `weko_workflow/utils.py:2246` | `deleted` |
| `weko_workflow/utils.py:2264` | `deletion_request` |

#### 通知先の決定ロジック

- **`_get_params_for_registrant`**（登録者向け: registered / approved / rejected / deleted 系）
  アクティビティのログインユーザ + 共有ユーザ（`shared_user_ids`）。
  操作者自身（`actor_id`）は除外される。
- **`_get_params_for_approver`**（承認者向け: request_approval / deletion_request）
  リポジトリ管理者ロール（`WEKO_ADMIN_PERMISSION_ROLE_REPO`）に属するユーザ全員 +
  フローの承認アクションに設定されたロール/ユーザ +
  コミュニティ指定時はコミュニティ管理者。
  ロールの `action_role_exclude` / `action_user_exclude` を考慮して除外も行う。

### 4-2. SWORD API 経由

`modules/weko-swordserver/weko_swordserver/utils.py:563,569`

| 操作 | 関数 | 通知種別 |
|---|---|---|
| `import` / `update` | `notify_item_imported()` | `Announce` + `IngestAction` |
| `delete` | `notify_item_deleted()` | `Announce` + `IngestAction` + `Delete` |

こちらも登録者＋共有ユーザに送り、操作者自身は除外。
`object_name` 未指定時は `get_item_title(recid)` でアイテムタイトルを取得する。

**注意: SWORD経由のこの2関数には `WEKO_NOTIFICATIONS` のチェックが無い。**
`weko-workflow` 側の `notify_about_activity` はフラグを見るが、
`notify_item_imported` / `notify_item_deleted` はフラグに関係なく Inbox へ送信を試みる。

### 4-3. 送信の実体

```python
Notification.create_item_registered(target_id, recid, actor_id, ...) \
    .send(NotificationClient(inbox_url()))
```

`NotificationClient.send()` は未検証なら `validate()` を実行してから
`ldnlib.Sender().send(inbox, payload)` で POST する。

エラーは `ValidationError` / `HTTPError` とその他の例外を捕捉してログ出力するのみで、
**通知の失敗が本体処理（アイテム登録・承認）を止めることはない。**
ただしループ内で例外が起きると `return` するため、**その時点以降のユーザには通知が飛ばない。**

---

## 5. 受信・表示

### 5-1. 通知一覧API

```
GET /api/notifications
```
（`blueprint_api`、`invenio_base.api_blueprints` で登録）

- 未認証は 401
- `NotificationClient.notifications(target=<user_uri>)` で
  `GET <inbox>?target=<user_uri>` を呼び、通知IDのリストを取得
- 内部URL（`http://inbox:8080`）を外部URL（`THEME_SITEURL`）に置換して返す

レスポンス:
```json
{ "code": 200, "message": "...", "count": 3, "notifications": ["...", "..."] }
```

### 5-2. Inbox の公開（LDN Discovery）

`ext.py` の `after_request` フックが、**サイトトップページへの HEAD リクエスト**に対してのみ
`Link` ヘッダを追加する。

```
Link: <https://<site>/inbox>; rel="http://www.w3.org/ns/ldp#inbox"
```

```bash
curl -I https://<site>/
# → Link: <https://<site>/inbox>; rel="http://www.w3.org/ns/ldp#inbox"
```

GETリクエストには付かない点に注意（`endpoint != "weko_theme.index" or method != "HEAD"` で早期return）。

### 5-3. Web Push

- Service Worker: `/static/gen/sw.js`（scope `/static/gen/`）
- VAPID公開鍵は `GET /inbox/subscription/vapid-public-key` から取得
- 購読情報は `POST <inbox>/subscribe`、解除は `POST <inbox>/unsubscribe`
- 通知クリックで該当URLのタブにフォーカス、無ければ新規に開く

### 5-4. Push文面テンプレート

`templates/weko_notifications/push.json` に8種類 × en/ja で定義。
アプリ起動時（`before_app_first_request`）に `POST <inbox>/push-template` で Inbox へ登録される。

```json
"registered": {
  "name": "Registered",
  "type": ["Announce", "coar-notify:IngestAction"],
  "templates": {
    "ja": {
      "title": "アイテムが登録されました",
      "body": "\"{{ object_name }}\" が {{ actor_name }} によって登録されました。"
    }
  }
}
```

定義済みキー: `registered`, `request_approval`, `approved`, `rejected`,
`deleted`, `request_deletion`, `approved_deletion`, `rejected_deletion`

---

## 6. 設定

### 6-1. Flask設定 (`weko_notifications/config.py`)

| 設定キー | 既定値 | 意味 |
|---|---|---|
| `WEKO_NOTIFICATIONS` | `True` | 機能全体のON/OFF。Falseで設定画面ブループリントも登録されない |
| `WEKO_NOTIFICATIONS_INBOX_ADDRESS` | `http://inbox:8080` | Inbox の内部アドレス（サーバ間通信用） |
| `WEKO_NOTIFICATIONS_INBOX_ENDPOINT` | `/inbox` | Inbox のエンドポイントパス |
| `WEKO_NOTIFICATIONS_USERS_URI` | `/users/{user_id}` | ユーザURIのテンプレート |
| `WEKO_NOTIFICATIONS_PUSH_TEMPLATE_PATH` | `""` | push.json の絶対パス。未設定だとPushテンプレート登録がスキップされる |
| `COAR_NOTIFY_CONTEXT` | AS2.0 + coar-notify.net | `@context` の値 |
| `COAR_NOTIFY_LINK_REL` | `http://www.w3.org/ns/ldp#inbox` | Linkヘッダの rel |
| `WEKO_NOTIFICATIONS_TEMPLATE` | 設定画面テンプレート | |
| `WEKO_NOTIFICATIONS_BASE_TEMPLATE` | `BASE_TEMPLATE` | |
| `WEKO_NOTIFICATIONS_SETTINGS_TEMPLATE` | `SETTINGS_TEMPLATE` | |

外部URL（`origin.id` / `target.id` / `object.id`）の組み立てには
**`THEME_SITEURL`** を使うため、この設定が正しくないと通知内のURLが壊れる。

`ext.py` の `init_config` が `WEKO_NOTIFICATIONS_` 接頭辞のキーを一括で `setdefault`。
ただし `COAR_NOTIFY_CONTEXT` / `COAR_NOTIFY_LINK_REL` は接頭辞が異なるため
**`app.config` に登録されず、モジュール内から直接参照される**（`instance.cfg` で上書きできない）。

### 6-2. `scripts/instance.cfg` の実設定

```python
WEKO_NOTIFICATIONS = True
WEKO_NOTIFICATIONS_INBOX_ADDRESS = 'http://inbox:8080'
WEKO_NOTIFICATIONS_INBOX_ENDPOINT = '/inbox'
WEKO_NOTIFICATIONS_PUSH_TEMPLATE_PATH = '/code/modules/weko-notifications/weko_notifications/templates/weko_notifications/push.json'
```

### 6-3. Inbox コンテナ (`docker-compose.yml`)

```yaml
inbox:
  build:
    context: ./inbox
    dockerfile: Dockerfile
  ports:
    - "8080:8080"
  environment:
    - ENABLE_PUSH_NOTIFICATIONS=True
    - ICON=/static/images/weko-logo-256.png
    - MONGO_DB_URI=mongodb://inbox:ibpass123@mongo:27017
    - MONGO_DB_NAME=inbox
    - ON_RECEIVE_NOTIFICATION_WEBHOOK_URL=
    - ALLOWED_ADMIN_ORIGINS=["*"]
    - ALLOWED_ORIGINS=["*"]
    - SUBSCRIBER=mailto:wekosoftware@nii.ac.jp
    - VAPID_PUBLIC_KEY=
    - VAPID_PRIVATE_KEY=
  links:
    - mongo
```

- 実体は `inbox/Dockerfile` で
  `https://github.com/RCOSDP/coar-notify-inbox.git`（ブランチ `nii_main`）を clone し、
  `uvicorn app:app --host 0.0.0.0 --port 8080` で起動
- ストレージは MongoDB 7.0.14
- **`VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` が空のまま**なので、
  Web Push を使うには鍵を生成して設定する必要がある
- `ALLOWED_ORIGINS` / `ALLOWED_ADMIN_ORIGINS` が `["*"]` — 本番では絞るべき

### 6-4. nginx (`nginx/weko.conf`)

```nginx
upstream inbox_server {
  server inbox:8080;
}

location ~ ^/inbox/(.+) {
  proxy_pass http://inbox_server;
  proxy_set_header Host $http_host;
}
location ~ ^/inbox/?$ {
  limit_except POST { deny all; }   # ルートはPOSTのみ許可
  proxy_pass http://inbox_server;
  proxy_set_header Host $http_host;
}
```

`/inbox` 直下は **POST のみ許可**（LDN の受信口）。
`/inbox/subscribe` などのサブパスは全メソッド通す。

### 6-5. DB

| テーブル | 内容 |
|---|---|
| `notifications_user_settings` | `user_id`（PK/FK）、`user_profile_id`、`subscribe_email` |

alembic: `1aceb8bc87f2`（ブランチ作成） → `9ef65066e0d3`（テーブル作成）
ブランチラベル `weko_notifications`。

**Web Push の購読状態はWEKO側のDBに保存されず、Inbox 側と Service Worker が保持する。**
（`NotificationsUserSettings` に持つのはメール購読フラグのみ）

### 6-6. 依存パッケージ

`requirements.txt` に `py-ldnlib==0.1.3`。
ただし `weko-notifications/setup.py` の `install_requires` は `Flask-BabelEx` のみで
**`py-ldnlib` が宣言されていない**（モノレポ全体の requirements で解決している）。

---

## 7. 使い方

### 7-1. 利用者（エンドユーザ）

1. ログイン後、**アカウント設定 → Notifications**（`/account/settings/notifications/`）を開く
   - サイドメニューにベルアイコンで表示される
2. **Web push** をONにして Update
   - ブラウザの通知許可ダイアログを承認する
   - Service Worker が登録され、購読情報が Inbox に送られる
3. **Email** をONにして Update
   - メールアドレスが確認済み（`confirmed_at`）でないとエラーになる
4. 通知一覧は `GET /api/notifications` で取得できる

### 7-2. 管理者（構築時）

1. `docker-compose.yml` の `inbox` サービスに **VAPID鍵を設定**
   （空のままだと Web Push が動作しない）
2. `instance.cfg` で `WEKO_NOTIFICATIONS = True`、
   `WEKO_NOTIFICATIONS_INBOX_ADDRESS` / `_INBOX_ENDPOINT` / `_PUSH_TEMPLATE_PATH` を設定
3. **`THEME_SITEURL` が外部から見える正しいURLになっていることを確認**
   （通知内の全URLがこれを基準に作られる）
4. nginx が `/inbox` を Inbox コンテナへプロキシしていることを確認
5. alembic マイグレーションを適用（`notifications_user_settings` テーブル作成）
6. Push文面を変えたい場合は `push.json` を編集してアプリを再起動
   （初回リクエスト時に Inbox へ再登録される）

### 7-3. 開発者（コードから通知を送る）

```python
from weko_notifications import Notification, NotificationClient
from weko_notifications.utils import inbox_url

# ファクトリメソッドを使う
Notification.create_item_registered(
    target_id=1,          # 通知先ユーザID
    object_id="2000001",  # recid
    actor_id=3,           # 操作者ユーザID
    actor_name="Alex",
    object_name="A new record",
).send(NotificationClient(inbox_url()))
```

独自の通知を組み立てる場合はセッターをチェーンする（各セッターは self を返す）。

```python
from weko_notifications.notifications import Notification, ActivityType

n = (Notification()
     .set_type(ActivityType.ANNOUNCE_REVIEW)
     .set_origin(id=..., inbox=..., entity_type="Service")
     .set_target(id=..., inbox=..., entity_type="Person")
     .set_object(id=..., object_type=["Page", "sorg:WebPage"], name="...")
     .create())          # create() でバリデーション実行
n.send(NotificationClient(inbox_url()))
```

受信したペイロードの検証には `Notification.load(payload)` を使う。

---

## 8. 注意点・気になる点

1. **SWORD経由の通知が `WEKO_NOTIFICATIONS` を見ていない**
   `notify_item_imported` / `notify_item_deleted`（`weko_notifications/utils.py`）には
   フラグチェックが無く、機能OFFでも Inbox へのPOSTが試行される。
   `weko-workflow` 側の `notify_about_activity` はチェックしているので挙動が非対称。

2. **`COAR_NOTIFY_CONTEXT` / `COAR_NOTIFY_LINK_REL` が `app.config` に載らない**
   `ext.py` の `init_config` が `WEKO_NOTIFICATIONS_` 接頭辞しか拾わないため、
   `instance.cfg` から上書きできない。

3. **VAPID鍵が空のまま**（`docker-compose.yml`）。Web Push を使うなら要設定。

4. **`ALLOWED_ORIGINS` / `ALLOWED_ADMIN_ORIGINS` が `["*"]`**。本番では絞るべき。

5. **Inbox への HTTP 通信にタイムアウト指定が無い**
   `views.py` / `weko_user_profiles/views.py` の `requests.post(...)` および
   `ldnlib` 経由の送信のいずれもタイムアウト未指定。
   Inbox が無応答だとリクエスト処理が滞留する可能性がある。

6. **ループ内の例外で以降の通知が止まる**
   `_notify_about_activity_wiht_case` / `notify_item_imported` は
   1件目の送信で例外が出るとその場で `return` するため、残りの宛先に通知されない。

7. **`Link: rel="ldp#inbox"` が HEAD リクエストにしか付かない**
   トップページの GET には付かないため、GET しか見ないディスカバリ実装からは
   Inbox を発見できない可能性がある。

8. **`notify_item_imported` / `notify_item_deleted` の `object_name` 再利用**
   ループ内で `object_name is None` のときのみタイトルを取得するが、
   取得結果を変数に残すため2件目以降も同じ値が使われる。同一アイテムへの通知なので実害は無い。

9. **未使用の ActivityType が多い**
   `Review` / `Relationship` / `Undo` / `TentativeAccept` / `TentativeReject` 系は
   定義のみで送信箇所が無い。外部システムとの相互運用を進める際の拡張ポイント。

10. **`templates/weko_notifications/index.html` がテンプレートのひな形のまま**
    （`TODO: Example template, please remove if you do not need it.`）

---

## 9. 新しい通知の追加手順

追加したい通知が既存の `ActivityType` で表現できるかで手数が変わる。
`ANNOUNCE_REVIEW` / `ANNOUNCE_RELATIONSHIP` / `OFFER_REVIEW` / `OFFER_INGEST` /
`ACCEPT_REVIEW` / `UNDO` / `TentativeAccept` / `TentativeReject` は
**定義済みだが未使用**なので、これで足りるなら Step 1 は不要。
既存型 + `Delete` の組み合わせは `deletion_value` で作れる。

### 最小手数のまとめ

| ケース | 触るファイル |
|---|---|
| 既存 ActivityType を使う | `notifications.py`（ファクトリ）、`push.json`、呼び出し元 |
| 新しい ActivityType | 上記 + `ActivityType` への追加 |
| メールも出す | 上記 + `api.py` の `send_mail_*` + `.tpl` × 2 |

`schema.py` は `ActivityType` を動的に読むため、**どのケースでも修正不要**。

---

### Step 1: ActivityType を追加（新しい型が必要な場合のみ）

`modules/weko-notifications/weko_notifications/notifications.py`

```python
class ActivityType(Enum):
    ...
    ANNOUNCE_EMBARGO = ["Announce", "coar-notify:EmbargoAction"]   # 追加例
```

`schema.py` の `validate_activity_type` が `ActivityType` を走査するので、
スキーマ側の修正は不要。`deletion_value`（末尾に `Delete`）も自動で許可される。

> **落とし穴: Enum の値が重複するとエイリアスになる**
>
> ```python
> ANNOUNCE     = ["Announce"]
> ANNOUNCE_NEW = ["Announce"]   # → ActivityType.ANNOUNCE と同一物になる
> ```
>
> `ActivityType.ANNOUNCE_NEW` を参照しても `ANNOUNCE` が返り、
> `list(ActivityType)` にも現れない。必ず一意な値にすること。（動作確認済み）

### Step 2: ファクトリメソッドを追加

同じく `notifications.py` の `Notification` クラスに、
既存の `create_item_registered` などと同じ形で追加する。

```python
@classmethod
def create_item_embargoed(cls, target_id, object_id, actor_id, context_id=None, **kwargs):
    """Create embargo notification."""
    obj = cls()
    obj.set_all(
        activity_type=ActivityType.ANNOUNCE_EMBARGO,
        target_id=target_id,
        object_id=object_id,
        actor_id=actor_id,
        context_id=context_id,
        **kwargs
    )
    return obj.create()
```

`set_all()` は生成する形が固定されている。

| エンティティ | 固定値 |
|---|---|
| `origin` | サイトトップURL / 自Inbox / `Service` |
| `target` | `<site>/users/{id}` / 自Inbox / `Person` |
| `object` | `<site>/records/{recid}` / `["Page","sorg:WebPage"]` |
| `actor` | `<site>/users/{id}` / `Person` |
| `context` | ワークフローのアクティビティ詳細URL |

**外部リポジトリの Inbox に送る / target が Person 以外 / object がレコード以外**
といった通知は `set_all()` では作れない。
その場合は `set_type()` / `set_origin()` / `set_target()` / `set_object()` /
`set_actor()` / `set_context()` を直接チェーンして `create()` を呼ぶ。

### Step 3: 送信箇所を組み込む

#### 3-a. ワークフローのイベントに紐づく場合

`modules/weko-workflow/weko_workflow/api.py` の `notify_about_activity` に分岐を追加。

```python
elif case == "embargoed":
    self._notify_about_activity_wiht_case(
        activity, case, self._get_params_for_registrant,
        Notification.create_item_embargoed
    )
    self.send_mail_item_embargoed(activity)   # メールも出すなら
```

getter は通知先の決め方で選ぶ。

- `_get_params_for_registrant` — 登録者＋共有ユーザ（操作者は除外）
- `_get_params_for_approver` — リポジトリ管理者ロール＋フローの承認ロール＋コミュニティ管理者

どちらでもない宛先が必要なら、`(set_target_id, recid, actor_id, actor_name)` の
4タプルを返す getter を新設する。

そのうえで `views.py` / `utils.py` の該当処理から呼ぶ。

```python
work_activity.notify_about_activity(activity_id, "embargoed")
```

#### 3-b. ワークフロー外（SWORD、バッチ、REST API など）の場合

`weko_notifications/utils.py` に `notify_item_imported` と同じ形のヘルパを足すのが既存の流儀。
ただし**既存の2関数は `WEKO_NOTIFICATIONS` フラグを見ていない**ので、
新規追加分には最初から入れておく（[8. 注意点](#8-注意点気になる点) の1番）。

```python
def notify_item_embargoed(target_id, recid, actor_id, object_name=None, shared_ids=[]):
    if not current_app.config.get("WEKO_NOTIFICATIONS"):
        return
    set_target_id, actor_name = _get_params_for_registrant(target_id, actor_id, shared_ids)

    from .notifications import Notification
    for tid in set_target_id:
        try:
            Notification.create_item_embargoed(
                tid, recid, actor_id,
                actor_name=actor_name,
                object_name=object_name or get_item_title(recid),
            ).send(NotificationClient(inbox_url()))
        except Exception:
            current_app.logger.error("Failed to send embargo notification.")
            traceback.print_exc()
            continue        # 既存実装は return なので、ここは continue のほうが安全
```

既存の `notify_item_*` / `_notify_about_activity_wiht_case` はループ内で例外が起きると
`return` してしまい、残りの宛先に届かない（[8. 注意点](#8-注意点気になる点) の6番）。
新規分は `continue` にしておくと1件の失敗が他を巻き込まない。

### Step 4: Push 通知の文面を追加

`modules/weko-notifications/weko_notifications/templates/weko_notifications/push.json`

```json
"embargoed": {
  "name": "Embargoed",
  "description": "Notification for item embargo.",
  "type": ["Announce", "coar-notify:EmbargoAction"],
  "templates": {
    "en": { "title": "Your item is under embargo",
            "body": "\"{{ object_name }}\" has been embargoed by {{ actor_name }}." },
    "ja": { "title": "アイテムが公開停止されました",
            "body": "\"{{ object_name }}\" が {{ actor_name }} によって公開停止されました。" }
  }
}
```

- `type` は Step 1/2 で使った値と**完全に一致**させる。
  Inbox 側はこの `type` でテンプレートを引き当てていると見られる
  （Inbox の実装は別リポジトリ `RCOSDP/coar-notify-inbox` にあり、本リポジトリからは未確認）
- 同じ `type` を複数のテンプレートに使うと衝突する
- `push.json` は `before_app_first_request` で Inbox に POST されるため、
  **編集後はアプリの再起動が必要**
- body で使える変数は、通知ペイロードの `object.name` / `actor.name` に対応する
  `{{ object_name }}` / `{{ actor_name }}` が既存で使われているもの

### Step 5: メール通知も出す場合

1. `api.py` に `send_mail_item_embargoed()` を追加
   （既存の `send_mail_item_registered`（`api.py:3550`）をコピーするのが早い）
2. テンプレートファイル名を決める — `email_notification_item_embargoed_{language}.tpl`
3. `modules/weko-workflow/weko_workflow/templates/weko_workflow/email_templates/` に
   `_en.tpl` と `_ja.tpl` の2本を追加

メールは `NotificationsUserSettings.subscribe_email` が True かつ
`confirmed_at` があるユーザにのみ送られる（`send_notification_email` 内で判定）。

### Step 6: テストと翻訳

- `modules/weko-notifications/tests/data/notifications/` に期待ペイロードのJSONを追加し、
  `test_notifications.py` にケースを追加
- UI文言を足した場合は `translations/{en,ja}/LC_MESSAGES/messages.po` を更新

---

## 10. 参照ファイル一覧

```
modules/weko-notifications/
├── weko_notifications/
│   ├── notifications.py     # Notification, ActivityType
│   ├── schema.py            # NotificationSchema とバリデータ
│   ├── client.py            # NotificationClient (py-ldnlib)
│   ├── utils.py             # inbox_url, user_uri, notify_item_*
│   ├── views.py             # 設定画面 + GET /api/notifications
│   ├── models.py            # NotificationsUserSettings
│   ├── forms.py             # NotificationsForm
│   ├── ext.py               # 拡張初期化 + Linkヘッダ
│   ├── config.py            # 設定既定値
│   ├── bundles.py           # assets (css/js/sw)
│   ├── alembic/             # 1aceb8bc87f2 → 9ef65066e0d3
│   ├── static/js/weko_notifications/{sw.js, notifications.settings.js}
│   └── templates/weko_notifications/{push.json, settings/notifications.html}
└── tests/data/notifications/*.json   # 通知ペイロードの実例

modules/weko-workflow/weko_workflow/api.py       # notify_about_activity (:3226)
modules/weko-workflow/weko_workflow/views.py     # 呼び出し (:2368-2707)
modules/weko-workflow/weko_workflow/utils.py     # 呼び出し (:2246, :2264)
modules/weko-swordserver/weko_swordserver/utils.py  # SWORD経由 (:563, :569)
modules/weko-items-ui/weko_items_ui/utils.py     # メール通知先の取得
modules/weko-user-profiles/weko_user_profiles/views.py  # プロフィールをInboxへ同期 (:145)

inbox/Dockerfile          # RCOSDP/coar-notify-inbox (nii_main)
docker-compose.yml        # inbox / mongo サービス (:401-)
nginx/weko.conf           # /inbox のプロキシ (:5, :274-)
scripts/instance.cfg      # 実設定 (:632-)
```
