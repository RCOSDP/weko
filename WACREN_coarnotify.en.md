# COAR Notify Feature: Specification and Usage Notes

Target branch: `feature/nii_WACREN_pre`
Survey date: 2026-08-04

Notes from a study of WEKO3's COAR Notify support (the `weko-notifications`
module): what it does, how it is built, how to configure it, and how to use it.

---

## 1. Overview

`weko-notifications` takes workflow events such as item registration, approval,
and deletion, turns them into **COAR Notify messages (Linked Data Notification /
ActivityStreams 2.0)**, sends them to an LDN Inbox, and delivers them to users by
Web Push or email.

WEKO itself is only the **sender**. The **Inbox is a separate external service**
running in its own container (`RCOSDP/coar-notify-inbox`).

```
[WEKO app]  --(LDN POST: ldnlib.Sender)-->  [inbox:8080]  --(Web Push)-->  [browser]
     |                                           |
     |  <--(GET /inbox?target=...)---------------+
     |      fetch the notification list (ldnlib.Consumer)
     |
     +--(POST /subscribe, /userprofile, /push-template)--> [inbox:8080]
```

### Main parts

| File | Role |
|---|---|
| `notifications.py` | The `Notification` class and the `ActivityType` enum. Builds the notification payload |
| `schema.py` | Validates the COAR Notify payload with marshmallow |
| `client.py` | `NotificationClient`. Sends and fetches using `py-ldnlib` |
| `utils.py` | Builds the Inbox URL and user URI; helper functions for SWORD notifications |
| `views.py` | The notification settings screen (UI) and the notification API |
| `models.py` | The `notifications_user_settings` table (email subscription flag) |
| `forms.py` | The notification settings form (Web Push / Email) |
| `ext.py` | Extension setup. Adds the `Link: rel="ldp#inbox"` header |
| `static/js/.../sw.js` | Service Worker for Web Push |
| `templates/.../push.json` | Text templates for push messages (en/ja) |

---

## 2. Notification types (ActivityType)

The `ActivityType` enum in `notifications.py` defines the COAR Notify patterns.
The `deletion_value` property makes a "deletion version" by adding `Delete` at
the end.

| ActivityType | Value of `type` |
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

### Events actually used, and their factory methods

| Case (`case`) | Factory method | `type` |
|---|---|---|
| `registered` | `create_item_registered` | `Announce` + `IngestAction` |
| `request_approval` | `create_request_approval` | `Offer` + `EndorsementAction` |
| `approved` | `create_item_approved` | `Announce` + `EndorsementAction` |
| `rejected` | `create_item_rejected` | `Reject` |
| `deleted` | `create_item_deleted` | `Announce` + `IngestAction` + `Delete` |
| `deletion_request` | `create_request_delete_approval` | `Offer` + `EndorsementAction` + `Delete` |
| `deletion_approved` | `create_item_delete_approved` | `Announce` + `EndorsementAction` + `Delete` |
| `deletion_rejected` | `create_item_delete_rejected` | `Reject` + `Delete` |

`ACCEPT_REVIEW`, `ANNOUNCE_RELATIONSHIP`, `ANNOUNCE_REVIEW`, `OFFER_INGEST`,
`OFFER_REVIEW`, `UNDO`, `TentativeAccept`, and `TentativeReject` are **defined
but never sent** at the moment. They exist so that payloads received from
outside can be validated.

---

## 3. Notification payload format

### Example (approval request = Offer + EndorsementAction)

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

### What each field means and how it is built (`Notification.set_all`)

| Field | Required | How it is built |
|---|---|---|
| `id` | Yes | `urn:uuid:<uuid4>`. Generated automatically if not given |
| `updated` | Yes | RFC3339 format. Current time if not given (default `Asia/Tokyo`) |
| `@context` | Yes | Fixed value `COAR_NOTIFY_CONTEXT` |
| `type` | Yes | An `ActivityType` value. Checked by `validate_activity_type` |
| `origin` | Yes | Site top URL / Inbox URL / `"Service"` |
| `target` | Yes | User URI of the recipient (`<site>/users/{user_id}`) / Inbox URL / `"Person"` |
| `object` | Yes | URL of the item (`<site>/records/{recid}`) / `["Page","sorg:WebPage"]` / item title |
| `actor` | Optional | User URI of the person who acted / `"Person"` / user name (`"Unknown"` if not known) |
| `context` | Optional | URL of the workflow activity detail page. Only when `context_id` is given |
| `inReplyTo` | Optional | ID of the notification being replied to |

### Validation (`schema.py`)

`NotificationSchema` (marshmallow, `strict=True`) runs on
`Notification.create()`, `load()`, and `validate()`.

- `validate_urn_uuid` — checks that `id` starts with `urn:uuid:` and is a valid UUID
- `validate_rfc3339` — checks that `updated` is in RFC3339 format
- `validate_activity_type` — checks that `type` is an `ActivityType` value (or one with `Delete`)
- `validate_string_or_list` — checks that `type` and `name` are a string or a list of strings

`ietf:cite-as`, `inReplyTo`, and `mediaType` have different names in Python and
in JSON, so they are mapped with `attribute` / `load_from`.

---

## 4. How notifications are sent, and from where

### 4-1. Through the workflow (main path)

The entry point is `WorkActivity.notify_about_activity(activity_id, case)`
(`modules/weko-workflow/weko_workflow/api.py:3226`).

```python
if not current_app.config["WEKO_NOTIFICATIONS"]:
    return
activity = self.get_activity_by_id(activity_id)
if activity is None or activity.workflow.open_restricted:
    return
```

→ **Nothing is sent when `WEKO_NOTIFICATIONS` is False, or when the workflow is
a restricted-access one.**

For each `case`, the code picks a "getter" (how to decide who receives the
notification) and a "creater" (how to build the notification).
`_notify_about_activity_wiht_case()` then loops over every target user and
sends. At the same time, the matching `send_mail_*` function sends an email.

| Caller | `case` |
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

#### How recipients are chosen

- **`_get_params_for_registrant`** (for the registrant: registered / approved /
  rejected / deleted cases)
  The activity's login user plus the shared users (`shared_user_ids`).
  The person who performed the action (`actor_id`) is excluded.
- **`_get_params_for_approver`** (for approvers: request_approval /
  deletion_request)
  All users with the repository administrator role
  (`WEKO_ADMIN_PERMISSION_ROLE_REPO`), plus the roles/users set on the flow's
  approval action, plus community administrators when a community is specified.
  The role's `action_role_exclude` / `action_user_exclude` settings are applied
  to remove users.

### 4-2. Through the SWORD API

`modules/weko-swordserver/weko_swordserver/utils.py:563,569`

| Operation | Function | Notification type |
|---|---|---|
| `import` / `update` | `notify_item_imported()` | `Announce` + `IngestAction` |
| `delete` | `notify_item_deleted()` | `Announce` + `IngestAction` + `Delete` |

These also send to the registrant and shared users, and exclude the person who
acted. When `object_name` is not given, the title is fetched with
`get_item_title(recid)`.

**Note: these two SWORD functions do not check `WEKO_NOTIFICATIONS`.**
`notify_about_activity` in `weko-workflow` checks the flag, but
`notify_item_imported` / `notify_item_deleted` try to POST to the Inbox no
matter what the flag says.

### 4-3. The actual send

```python
Notification.create_item_registered(target_id, recid, actor_id, ...) \
    .send(NotificationClient(inbox_url()))
```

If the payload has not been validated yet, `NotificationClient.send()` runs
`validate()` first, then POSTs with `ldnlib.Sender().send(inbox, payload)`.

Errors are caught (`ValidationError`, `HTTPError`, and other exceptions) and
only written to the log, so **a failed notification never stops the main work
(item registration, approval, and so on)**. However, an exception inside the
loop causes a `return`, so **users after that point receive nothing**.

---

## 5. Receiving and displaying notifications

### 5-1. Notification list API

```
GET /api/notifications
```
(registered as `blueprint_api` under `invenio_base.api_blueprints`)

- Returns 401 if the user is not logged in
- Calls `NotificationClient.notifications(target=<user_uri>)`, which does
  `GET <inbox>?target=<user_uri>`, and gets back a list of notification IDs
- Replaces the internal URL (`http://inbox:8080`) with the external URL
  (`THEME_SITEURL`) before returning

Response:
```json
{ "code": 200, "message": "...", "count": 3, "notifications": ["...", "..."] }
```

### 5-2. Announcing the Inbox (LDN Discovery)

The `after_request` hook in `ext.py` adds the `Link` header **only for HEAD
requests to the site top page**.

```
Link: <https://<site>/inbox>; rel="http://www.w3.org/ns/ldp#inbox"
```

```bash
curl -I https://<site>/
# → Link: <https://<site>/inbox>; rel="http://www.w3.org/ns/ldp#inbox"
```

Note that GET requests do not get the header (the code returns early when
`endpoint != "weko_theme.index" or method != "HEAD"`).

### 5-3. Web Push

- Service Worker: `/static/gen/sw.js` (scope `/static/gen/`)
- The VAPID public key comes from `GET /inbox/subscription/vapid-public-key`
- Subscribing is `POST <inbox>/subscribe`; unsubscribing is `POST <inbox>/unsubscribe`
- Clicking a notification focuses the tab with that URL, or opens a new one if
  there is none

### 5-4. Push message templates

`templates/weko_notifications/push.json` defines 8 kinds × en/ja.
At application start (`before_app_first_request`) they are registered with the
Inbox by `POST <inbox>/push-template`.

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

Defined keys: `registered`, `request_approval`, `approved`, `rejected`,
`deleted`, `request_deletion`, `approved_deletion`, `rejected_deletion`

---

## 6. Configuration

### 6-1. Flask settings (`weko_notifications/config.py`)

| Setting key | Default | Meaning |
|---|---|---|
| `WEKO_NOTIFICATIONS` | `True` | Turns the whole feature on/off. When False, the settings-screen blueprint is not registered either |
| `WEKO_NOTIFICATIONS_INBOX_ADDRESS` | `http://inbox:8080` | Internal address of the Inbox (server-to-server) |
| `WEKO_NOTIFICATIONS_INBOX_ENDPOINT` | `/inbox` | Endpoint path of the Inbox |
| `WEKO_NOTIFICATIONS_USERS_URI` | `/users/{user_id}` | Template for the user URI |
| `WEKO_NOTIFICATIONS_PUSH_TEMPLATE_PATH` | `""` | Absolute path to push.json. If empty, push template registration is skipped |
| `COAR_NOTIFY_CONTEXT` | AS2.0 + coar-notify.net | Value of `@context` |
| `COAR_NOTIFY_LINK_REL` | `http://www.w3.org/ns/ldp#inbox` | The `rel` of the Link header |
| `WEKO_NOTIFICATIONS_TEMPLATE` | Settings screen template | |
| `WEKO_NOTIFICATIONS_BASE_TEMPLATE` | `BASE_TEMPLATE` | |
| `WEKO_NOTIFICATIONS_SETTINGS_TEMPLATE` | `SETTINGS_TEMPLATE` | |

The external URLs (`origin.id`, `target.id`, `object.id`) are built from
**`THEME_SITEURL`**, so if that setting is wrong, every URL in the notifications
will be wrong too.

`init_config` in `ext.py` applies `setdefault` to all keys with the
`WEKO_NOTIFICATIONS_` prefix. But `COAR_NOTIFY_CONTEXT` and
`COAR_NOTIFY_LINK_REL` have a different prefix, so they are **not put into
`app.config` and are read directly inside the module** (they cannot be
overridden in `instance.cfg`).

### 6-2. Actual settings in `scripts/instance.cfg`

```python
WEKO_NOTIFICATIONS = True
WEKO_NOTIFICATIONS_INBOX_ADDRESS = 'http://inbox:8080'
WEKO_NOTIFICATIONS_INBOX_ENDPOINT = '/inbox'
WEKO_NOTIFICATIONS_PUSH_TEMPLATE_PATH = '/code/modules/weko-notifications/weko_notifications/templates/weko_notifications/push.json'
```

### 6-3. Inbox container (`docker-compose.yml`)

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

- `inbox/Dockerfile` clones
  `https://github.com/RCOSDP/coar-notify-inbox.git` (branch `nii_main`) and
  starts it with `uvicorn app:app --host 0.0.0.0 --port 8080`
- Storage is MongoDB 7.0.14
- **`VAPID_PUBLIC_KEY` and `VAPID_PRIVATE_KEY` are still empty**, so you must
  generate and set keys before Web Push will work
- `ALLOWED_ORIGINS` and `ALLOWED_ADMIN_ORIGINS` are `["*"]` — these should be
  narrowed in production

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
  limit_except POST { deny all; }   # only POST is allowed on the root
  proxy_pass http://inbox_server;
  proxy_set_header Host $http_host;
}
```

`/inbox` itself allows **POST only** (it is the LDN receiving point).
Sub-paths such as `/inbox/subscribe` allow all methods.

### 6-5. Database

| Table | Contents |
|---|---|
| `notifications_user_settings` | `user_id` (PK/FK), `user_profile_id`, `subscribe_email` |

alembic: `1aceb8bc87f2` (branch creation) → `9ef65066e0d3` (table creation)
Branch label: `weko_notifications`.

**The Web Push subscription state is not stored in the WEKO database. It is kept
by the Inbox and the Service Worker.**
(`NotificationsUserSettings` only holds the email subscription flag.)

### 6-6. Dependencies

`requirements.txt` has `py-ldnlib==0.1.3`.
However, `install_requires` in `weko-notifications/setup.py` lists only
`Flask-BabelEx`, so **`py-ldnlib` is not declared there** (it is resolved by the
monorepo-wide requirements).

---

## 7. How to use

### 7-1. End users

1. After logging in, open **Account settings → Notifications**
   (`/account/settings/notifications/`)
   - It appears in the side menu with a bell icon
2. Turn **Web push** on and click Update
   - Accept the browser's notification permission dialog
   - The Service Worker is registered and the subscription is sent to the Inbox
3. Turn **Email** on and click Update
   - This fails if the email address is not confirmed (`confirmed_at`)
4. The notification list can be fetched with `GET /api/notifications`

### 7-2. Administrators (during setup)

1. **Set the VAPID keys** on the `inbox` service in `docker-compose.yml`
   (Web Push does not work while they are empty)
2. In `instance.cfg`, set `WEKO_NOTIFICATIONS = True` and
   `WEKO_NOTIFICATIONS_INBOX_ADDRESS` / `_INBOX_ENDPOINT` / `_PUSH_TEMPLATE_PATH`
3. **Check that `THEME_SITEURL` is the correct externally visible URL**
   (every URL in a notification is built from it)
4. Check that nginx proxies `/inbox` to the Inbox container
5. Apply the alembic migration (creates the `notifications_user_settings` table)
6. To change the push message text, edit `push.json` and restart the
   application (it is re-registered with the Inbox on the first request)

### 7-3. Developers (sending a notification from code)

```python
from weko_notifications import Notification, NotificationClient
from weko_notifications.utils import inbox_url

# Use a factory method
Notification.create_item_registered(
    target_id=1,          # user ID of the recipient
    object_id="2000001",  # recid
    actor_id=3,           # user ID of the person who acted
    actor_name="Alex",
    object_name="A new record",
).send(NotificationClient(inbox_url()))
```

To build your own notification, chain the setters (each setter returns self).

```python
from weko_notifications.notifications import Notification, ActivityType

n = (Notification()
     .set_type(ActivityType.ANNOUNCE_REVIEW)
     .set_origin(id=..., inbox=..., entity_type="Service")
     .set_target(id=..., inbox=..., entity_type="Person")
     .set_object(id=..., object_type=["Page", "sorg:WebPage"], name="...")
     .create())          # create() runs the validation
n.send(NotificationClient(inbox_url()))
```

To validate a payload you have received, use `Notification.load(payload)`.

---

## 8. Points to watch

1. **SWORD notifications ignore `WEKO_NOTIFICATIONS`**
   `notify_item_imported` and `notify_item_deleted`
   (`weko_notifications/utils.py`) have no flag check, so they still try to POST
   to the Inbox even when the feature is off. `notify_about_activity` in
   `weko-workflow` does check it, so the behaviour is inconsistent.

2. **`COAR_NOTIFY_CONTEXT` and `COAR_NOTIFY_LINK_REL` never reach `app.config`**
   `init_config` in `ext.py` only picks up keys with the `WEKO_NOTIFICATIONS_`
   prefix, so they cannot be overridden from `instance.cfg`.

3. **The VAPID keys are empty** (`docker-compose.yml`). They must be set if you
   want Web Push.

4. **`ALLOWED_ORIGINS` and `ALLOWED_ADMIN_ORIGINS` are `["*"]`.** They should be
   narrowed in production.

5. **No timeout on HTTP calls to the Inbox**
   Neither the `requests.post(...)` calls in `views.py` and
   `weko_user_profiles/views.py` nor the sends through `ldnlib` set a timeout.
   If the Inbox stops responding, requests may pile up.

6. **An exception in the loop stops the remaining notifications**
   `_notify_about_activity_wiht_case` and `notify_item_imported` `return` as
   soon as one send raises, so the remaining recipients get nothing.

7. **`Link: rel="ldp#inbox"` is only added to HEAD requests**
   It is not added to a GET of the top page, so a discovery client that only
   does GET may fail to find the Inbox.

8. **`object_name` is reused in `notify_item_imported` / `notify_item_deleted`**
   The title is only fetched when `object_name is None`, but the result stays in
   the variable, so the same value is used from the second recipient on. Since
   all notifications are about the same item, this causes no real problem.

9. **Many ActivityTypes are unused**
   The `Review`, `Relationship`, `Undo`, `TentativeAccept`, and
   `TentativeReject` types are defined but never sent. They are extension points
   for future interoperability with external systems.

10. **`templates/weko_notifications/index.html` is still the boilerplate
    template** (`TODO: Example template, please remove if you do not need it.`)

---

## 9. How to add a new notification

How much work is needed depends on whether an existing `ActivityType` can
express what you want. `ANNOUNCE_REVIEW`, `ANNOUNCE_RELATIONSHIP`,
`OFFER_REVIEW`, `OFFER_INGEST`, `ACCEPT_REVIEW`, `UNDO`, `TentativeAccept`, and
`TentativeReject` are **already defined but unused**, so if one of them is
enough, you can skip Step 1. Combinations of an existing type plus `Delete` can
be made with `deletion_value`.

### Summary of the minimum work

| Case | Files to touch |
|---|---|
| Use an existing ActivityType | `notifications.py` (factory), `push.json`, the caller |
| New ActivityType | The above + an addition to `ActivityType` |
| Send email too | The above + `send_mail_*` in `api.py` + 2 `.tpl` files |

`schema.py` reads `ActivityType` dynamically, so **it never needs to change**.

---

### Step 1: Add an ActivityType (only if you need a new type)

`modules/weko-notifications/weko_notifications/notifications.py`

```python
class ActivityType(Enum):
    ...
    ANNOUNCE_EMBARGO = ["Announce", "coar-notify:EmbargoAction"]   # example
```

`validate_activity_type` in `schema.py` walks through `ActivityType`, so the
schema needs no change. The `deletion_value` form (with `Delete` at the end) is
allowed automatically too.

> **Trap: duplicate Enum values become aliases**
>
> ```python
> ANNOUNCE     = ["Announce"]
> ANNOUNCE_NEW = ["Announce"]   # → becomes the same object as ActivityType.ANNOUNCE
> ```
>
> Referring to `ActivityType.ANNOUNCE_NEW` returns `ANNOUNCE`, and it does not
> appear in `list(ActivityType)`. Always use a unique value. (Confirmed by
> testing.)

### Step 2: Add a factory method

Add it to the `Notification` class in the same `notifications.py`, in the same
shape as the existing `create_item_registered` and friends.

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

`set_all()` always produces the same shape.

| Entity | Fixed value |
|---|---|
| `origin` | Site top URL / own Inbox / `Service` |
| `target` | `<site>/users/{id}` / own Inbox / `Person` |
| `object` | `<site>/records/{recid}` / `["Page","sorg:WebPage"]` |
| `actor` | `<site>/users/{id}` / `Person` |
| `context` | URL of the workflow activity detail page |

You **cannot** use `set_all()` for notifications that go to an external
repository's Inbox, whose target is not a Person, or whose object is not a
record. In those cases, chain `set_type()`, `set_origin()`, `set_target()`,
`set_object()`, `set_actor()`, and `set_context()` directly and then call
`create()`.

### Step 3: Add the sending code

#### 3-a. When it is tied to a workflow event

Add a branch to `notify_about_activity` in
`modules/weko-workflow/weko_workflow/api.py`.

```python
elif case == "embargoed":
    self._notify_about_activity_wiht_case(
        activity, case, self._get_params_for_registrant,
        Notification.create_item_embargoed
    )
    self.send_mail_item_embargoed(activity)   # only if you also send email
```

Choose the getter based on who should receive the notification.

- `_get_params_for_registrant` — registrant + shared users (the person who acted
  is excluded)
- `_get_params_for_approver` — repository admin role + the flow's approval roles
  + community administrators

If you need recipients that neither covers, write a new getter that returns the
4-tuple `(set_target_id, recid, actor_id, actor_name)`.

Then call it from the right place in `views.py` or `utils.py`.

```python
work_activity.notify_about_activity(activity_id, "embargoed")
```

#### 3-b. When it is outside the workflow (SWORD, batch jobs, REST API, etc.)

The existing style is to add a helper to `weko_notifications/utils.py` shaped
like `notify_item_imported`. But **the two existing functions do not check the
`WEKO_NOTIFICATIONS` flag**, so put the check in your new one from the start
(see item 1 in [8. Points to watch](#8-points-to-watch)).

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
            continue        # the existing code uses return; continue is safer here
```

The existing `notify_item_*` and `_notify_about_activity_wiht_case` `return`
when an exception happens in the loop, so the remaining recipients get nothing
(see item 6 in [8. Points to watch](#8-points-to-watch)). Using `continue` in
new code keeps one failure from affecting the others.

### Step 4: Add the push message text

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

- The `type` must **match exactly** the value used in Steps 1 and 2.
  The Inbox appears to look up the template by this `type`
  (the Inbox is in a separate repository, `RCOSDP/coar-notify-inbox`, so this
  could not be checked from this repository)
- Using the same `type` in more than one template causes a conflict
- `push.json` is POSTed to the Inbox in `before_app_first_request`, so
  **you must restart the application after editing it**
- The variables available in the body are the ones already in use,
  `{{ object_name }}` and `{{ actor_name }}`, which map to `object.name` and
  `actor.name` in the notification payload

### Step 5: If you also want email

1. Add `send_mail_item_embargoed()` to `api.py`
   (copying the existing `send_mail_item_registered` (`api.py:3550`) is the
   quickest way)
2. Decide the template file name — `email_notification_item_embargoed_{language}.tpl`
3. Add both `_en.tpl` and `_ja.tpl` under
   `modules/weko-workflow/weko_workflow/templates/weko_workflow/email_templates/`

Email is only sent to users whose `NotificationsUserSettings.subscribe_email` is
True and who have a `confirmed_at` value (checked inside
`send_notification_email`).

### Step 6: Tests and translations

- Add the expected payload JSON under
  `modules/weko-notifications/tests/data/notifications/` and add a case to
  `test_notifications.py`
- If you added UI text, update
  `translations/{en,ja}/LC_MESSAGES/messages.po`

---

## 10. List of related files

```
modules/weko-notifications/
├── weko_notifications/
│   ├── notifications.py     # Notification, ActivityType
│   ├── schema.py            # NotificationSchema and validators
│   ├── client.py            # NotificationClient (py-ldnlib)
│   ├── utils.py             # inbox_url, user_uri, notify_item_*
│   ├── views.py             # settings screen + GET /api/notifications
│   ├── models.py            # NotificationsUserSettings
│   ├── forms.py             # NotificationsForm
│   ├── ext.py               # extension setup + Link header
│   ├── config.py            # default settings
│   ├── bundles.py           # assets (css/js/sw)
│   ├── alembic/             # 1aceb8bc87f2 → 9ef65066e0d3
│   ├── static/js/weko_notifications/{sw.js, notifications.settings.js}
│   └── templates/weko_notifications/{push.json, settings/notifications.html}
└── tests/data/notifications/*.json   # example notification payloads

modules/weko-workflow/weko_workflow/api.py       # notify_about_activity (:3226)
modules/weko-workflow/weko_workflow/views.py     # callers (:2368-2707)
modules/weko-workflow/weko_workflow/utils.py     # callers (:2246, :2264)
modules/weko-swordserver/weko_swordserver/utils.py  # via SWORD (:563, :569)
modules/weko-items-ui/weko_items_ui/utils.py     # gets the email recipients
modules/weko-user-profiles/weko_user_profiles/views.py  # syncs the profile to the Inbox (:145)

inbox/Dockerfile          # RCOSDP/coar-notify-inbox (nii_main)
docker-compose.yml        # inbox / mongo services (:401-)
nginx/weko.conf           # proxy for /inbox (:5, :274-)
scripts/instance.cfg      # actual settings (:632-)
```
