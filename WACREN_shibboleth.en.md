# WACREN Shibboleth Login — `mail` Attribute Not Propagated

Target branch: `feature/nii_WACREN_crossref_doi`
Written: 2026-09-01

## Premise

The following is **already confirmed working** in the WACREN environment and is
therefore out of scope for this document:

- The SP is federated with the WACREN IdP; the SAML handshake completes.
- Users can log in to WEKO3 through the IdP and reach the site authenticated.
- Consequently, the nginx → CGI → WEKO attribute chain works for **at least one**
  attribute (see §2), and the `wekoSocietyAffiliation` gate in
  `nginx/login.py:12-17` is not blocking these logins.

**The problem:** for users who log in through the Shibboleth IdP, the **e-mail
address on the WEKO3 profile screen (`/account/settings/profile/`) is blank**.
`mail` is not reaching `accounts_user.email`.

This document is the procedure to locate which hop drops `mail`, fix it, repair
the accounts already created without an e-mail, and pin the configuration so it
does not regress.

Line references were checked against this branch and will drift — confirm the
surrounding code before editing.

> **Urgent:** a blank e-mail is not only a cosmetic defect. `accounts_user.email`
> is the key WEKO uses to bind a Shibboleth identity to an account, and an empty
> value makes distinct IdP users collapse onto one WEKO account. See §3 before
> letting more users log in.

---

## 1. Where `mail` has to travel

An attribute crosses four name mappings between the IdP and the profile screen.
The profile field is not wired to the IdP directly.

```
[WACREN IdP]
  |  (A) attribute release policy (attribute-filter.xml, operated by the IdP)
  v
[Shibboleth SP]            nginx/attribute-map.xml
  |  (B) SAML name (OID) -> SP attribute id     urn:oid:0.9.2342.19200300.100.1.3 -> "mail"
  v
[nginx shibauthorizer]     nginx/weko.conf  +  nginx/shib_fastcgi_params
  |  (C) SP id -> CGI parameter name            "mail" -> fastcgi_param mail
  v
[/secure/login.py]         nginx/login.py:27-41
  |      CGI env var -> POST form field         os.environ["mail"] -> data["mail"]
  v
[POST /weko/shib/login]    weko_accounts/utils.py:114-152  parse_attributes()
  |  (D) POST field -> internal key             "mail" -> shib_attr["shib_mail"]
  v
[WEKO DB]  accounts_user.email  <- api.py:222 (new account) / api.py:197 (binding)
  v
[Profile screen]  weko_user_profiles/views.py:176
```

Hop (D) is the one that is easy to get wrong, because the POST field name is not
taken from `WEKO_ACCOUNTS_ATTRIBUTE_MAP` at runtime — it is read from the
`admin_settings.attribute_mapping` DB row:

```python
# weko_accounts/utils.py:114-152
admin_settings = AdminSettings.get("attribute_mapping", dict_to_object=False)
for header, attr in current_app.config["WEKO_ACCOUNTS_SSO_ATTRIBUTE_MAP"].items():
    required, name = attr                      # ("SHIB_ATTR_MAIL", (False, "shib_mail"))
    target = admin_settings.get(name, header) if admin_settings else header
    value = request.form.get(target, "")       # target == "" yields ""
    attrs[name] = value
```

`scripts/populate-instance.sh:465-466` and `postgresql/ddl/W2025-29.sql:1713-1715`
seed that row with **empty strings**. Because the key exists, the `header`
fallback never applies and `target` becomes `""`, which silently resolves to an
empty value. `WEKO_ACCOUNTS_ATTRIBUTE_MAP` in `invenio.cfg` only *seeds* the row
— but it does so on every start, which is what makes it the place of record:

`_adjust_shib_admin_DB()` (`weko_accounts/views.py:79`, a
`before_app_first_request` hook) **unconditionally overwrites**
`attribute_mapping` — and also `shib_login_enable` and `default_role_settings` —
from `current_app.config` (`views.py:136-148`).

Two operational rules follow:

- **`invenio.cfg` is the source of truth.** After a restart its values win.
- **Edits in Setting > Shibboleth do not survive a restart.** Use the admin
  screen for a temporary test only, never as the record.

---

## 2. What "login works" already tells us

`shib_sp_login()` rejects the request when both identifiers are empty
(`weko_accounts/views.py:448-453`):

```python
if error or not (
        shib_attr.get('shib_eppn', None)
        or _shib_username_config and shib_attr.get('shib_user_name')):
    flash(_("Missing SHIB_ATTRs!"), category='error')
    return _redirect_method()
```

Since logins succeed, `shib_eppn` **or** `shib_user_name` is arriving non-empty.
That eliminates the whole-chain failures and narrows the investigation:

| Eliminated | Why |
|---|---|
| nginx `/secure/` block not reached, fcgiwrap broken | `login.py` ran and POSTed to WEKO |
| `nginx/login.py` `wekoSocietyAffiliation` gate blocking | the login was not stopped there |
| `admin_settings.attribute_mapping` entirely empty | at least one key resolves to a real POST field |
| Redis / session / SP session handling | the login completed |

So the fault is **specific to `mail`** and lives in hop (A), (B), (C) or (D)
for that one attribute. §4 walks the hops in the order that costs least to check.

`parse_attributes()` synthesises `shib_user_name` from the eppn when the display
name is absent (`utils.py:140-149`: `WEKO_ACCOUNTS_GAKUNIN_USER_NAME_PREFIX` +
SHA-256 of the eppn, or the raw eppn when it is
`WEKO_ACCOUNTS_SHIB_USER_NAME_NO_HASH_LENGTH` = 253 characters or shorter), so
the two identifiers are not independent. Read the current state straight from
the database:

```sql
SELECT u.id, u.email, p.displayname, s.shib_eppn, s.shib_mail, s.shib_user_name
FROM shibboleth_user s
JOIN accounts_user u ON u.id = s.weko_uid
LEFT JOIN userprofiles_userprofile p ON p.user_id = u.id
ORDER BY u.id DESC LIMIT 20;
```

| `shib_eppn` | `shib_user_name` | Reading |
|---|---|---|
| a real eppn | a real display name | `eppn` and `displayName` both arrive — **only `mail` is missing** |
| a real eppn | `G_<64 hex>` | `eppn` arrives, `displayName` does not |
| equals `shib_user_name` | a display name | `eppn` did not arrive; `api.py:199-201` copied the user name into it |
| `''` on one row, others missing | — | `eppn` empty: `shibboleth_user.shib_eppn` is `UNIQUE`, so only the first such user was created |

Record which row shape you see — §4 branches on it.

---

## 3. Damage a blank `mail` is doing right now

`accounts_user.email` is `UNIQUE` and nullable, and WEKO uses it as the lookup
key when binding a Shibboleth identity to an account. With `shib_mail` empty:

| Scenario | Code | Result |
|---|---|---|
| First SSO user, no matching account | `api.py:214-239` `new_relation_info()` | Account created with `email=''` |
| **Second** SSO user, `WEKO_ACCOUNTS_SKIP_CONFIRMATION_PAGE = True` | `views.py:498-506` → `views.py:421` `find_user_by_email('')` → `confirm_user_without_page` → `api.py:184-212` | `find_user(email='')` matches the **first** user, so a *different* IdP identity is bound to that same WEKO account |
| User confirms with an existing WEKO account | `api.py:197` `bind_relation_info()` | `self.user.email = self.shib_attr['shib_mail']` runs unconditionally — an account that **already had a correct e-mail loses it** |
| Second account creation with `email=''` | `accounts_user.email` `UNIQUE` | IntegrityError, rollback, login failure |

The second row is the serious one: two people can end up sharing one WEKO
account, with whatever roles and submissions that account holds.

**Mitigation until §4 and §5 are done:** either set
`WEKO_ACCOUNTS_SKIP_CONFIRMATION_PAGE = False` (the default,
`weko_accounts/config.py:209`) so no account is auto-provisioned or auto-bound,
or set `'SHIB_ATTR_MAIL': (True, 'shib_mail')` in `WEKO_ACCOUNTS_SSO_ATTRIBUTE_MAP`
so a login without `mail` is refused outright instead of silently creating a
blank-e-mail account. Then audit for collisions:

```sql
-- Distinct Shibboleth identities sharing one WEKO account
SELECT weko_uid, count(*), array_agg(shib_eppn)
FROM shibboleth_user GROUP BY weko_uid HAVING count(*) > 1;

-- Accounts with no e-mail
SELECT u.id, u.email, s.shib_eppn
FROM accounts_user u JOIN shibboleth_user s ON s.weko_uid = u.id
WHERE u.email IS NULL OR u.email = '';
```

- [ ] Collision query run; results recorded
- [ ] Auto-provisioning/auto-binding paused, or `mail` made mandatory

---

## 4. Diagnosis — find the hop that drops `mail`

Run in order. Each step eliminates one hop, so the first failure names the fix.

### 4.1 Hop (D) — is WEKO's POST-field name for `mail` correct?

Cheapest check, and the one the seeded-empty-string defect lands on.

```bash
psql -U invenio -d invenio -c \
  "select settings from admin_settings where name='attribute_mapping';"
```

Expected:

```json
{"shib_eppn": "eppn", "shib_user_name": "DisplayName",
 "shib_mail": "mail", "shib_role_authority_name": "eduPersonAffiliation"}
```

**If `shib_mail` is `""` or anything other than `mail` → the cause is here.**
Note that `shib_eppn` can be correct while `shib_mail` is empty, which is exactly
the "login works but no e-mail" symptom. Fix in §5.1.

Also confirm what the running process holds, since `views.py:136-148` rewrites
the row from config on start:

```bash
docker compose exec web invenio shell -c \
  "from flask import current_app as a; print(a.config['WEKO_ACCOUNTS_ATTRIBUTE_MAP'])"
```

### 4.2 Hop (D) — what did WEKO actually parse?

`parse_attributes()` caches its output in Redis under `Shib-Session-<id>` for
180 s (`views.py:477-484`, `WEKO_ACCOUNTS_SHIB_LOGIN_CACHE_TTL`). Trigger a
login, then within three minutes:

```bash
docker compose exec redis redis-cli -n 0 --scan --pattern 'Shib-Session-*'
docker compose exec redis redis-cli -n 0 get 'Shib-Session-<id>'
```

Use the deployment's `CACHE_REDIS_DB` (`0` in `docker-compose.yml:82`).

Expected:

```json
{"shib_eppn": "user@example.org",
 "shib_mail": "user@example.org",
 "shib_user_name": "Test User",
 "shib_role_authority_name": "", "shib_ip_range_flag": ""}
```

`shib_mail` empty here while 4.1 was correct → the value never reached WEKO;
continue to 4.3. `shib_mail` populated here but the profile still blank → the
parsing is fine and the problem is in the account layer; go to §6.

### 4.3 Hop (C) — does nginx forward `mail`?

An attribute reaches WEKO only if it is declared in **both** files:
`nginx/weko.conf` sets the value, and `nginx/shib_fastcgi_params` is the list
`login.py:27-41` scans to decide what to forward. `weko.conf:146` has
`include shib_fastcgi_params;` commented out and re-declares the parameters
inline, so the two files can drift apart.

Check the **deployed** files, not just the repo:

```bash
docker compose exec nginx grep -n 'fastcgi_param mail\|fastcgi_param eppn\|fastcgi_param DisplayName' \
  /etc/nginx/conf.d/weko.conf /etc/nginx/shib_fastcgi_params
```

On this branch both files are complete:

| Attribute | `weko.conf` | `shib_fastcgi_params` | CGI / POST field name |
|---|---|---|---|
| eppn | `:174` | `:49` | `eppn` |
| mail | `:162` | `:84` | `mail` |
| displayName | `:168` | `:77` | `DisplayName` |

Names are **case-sensitive** — they become POSIX environment variables and then
POST field keys. The SP attribute id is `displayName` (lower-case `d`) but nginx
re-labels it `DisplayName`, which is why §5.1 configures `DisplayName` in WEKO.

If `mail` is missing from either deployed file, fix per §5.2.

### 4.4 Hop (C) — inspect the CGI environment directly

Only if 4.3 looks correct but 4.2 still shows an empty `shib_mail`. Deploy the
bundled probe **temporarily**:

```dockerfile
# nginx/Dockerfile, next to line 80 (where login.py is added)
ADD ./info.py /usr/share/nginx/html/secure/info.py
RUN chmod 755 /usr/share/nginx/html/secure/info.py
```

Open `https://<host>/secure/info.py` while authenticated and look for `mail`
under "Environment Variables (CGI)".

> **Remove this file before returning to normal operation.** It dumps the entire
> CGI environment of an authenticated session to anyone who can reach the URL.

`mail` present here but empty in 4.2 → hop (D); revisit 4.1.
`mail` absent here → hop (A) or (B); continue to 4.5.

### 4.5 Hops (A)/(B) — does the SP hold `mail` at all?

Log in through the IdP, then on the same browser session open:

```
https://<host>/Shibboleth.sso/Session
```

Expected: the session summary lists the attribute names `eppn`, `mail`,
`displayName`. Values are hidden because
`shibboleth2.xml:63` sets `showAttributeValues="false"` — names are enough.

```bash
docker compose exec nginx tail -200 /var/log/shibboleth/shibd.log
```

- **`mail` absent from the session** → the IdP is not releasing it, or
  `attribute-map.xml` is not decoding it. Confirm the decoder first (cheap):
  `nginx/attribute-map.xml:110` maps `urn:oid:0.9.2342.19200300.100.1.3` to id
  `mail` and `:145` maps `urn:mace:dir:attribute-def:mail`; both are active on
  this branch, and `attribute-policy.xml:93` (`attributeID="*" permitAny="true"`)
  passes `mail` through. If those are intact in the deployed container, the
  attribute is not being released — go to §5.3.
- **`mail` present in the session** → the SP has it and nginx is not forwarding
  it; go back to 4.3 against the deployed files.

**This is the most likely outcome for WACREN.** `mail` is not a mandatory
attribute in most federations, and `eppn` is typically released by default —
which produces exactly the observed "login works, e-mail is blank" behaviour.

- [ ] Failing hop identified and recorded

---

## 5. Fixes

### 5.1 Hop (D) — pin the attribute map in `invenio.cfg`

Add to the deployed `invenio.cfg` (`scripts/instance.cfg` is the template) and
restart. There is no need to touch the DB row by hand — `_adjust_shib_admin_DB()`
rewrites it from config on the first request after restart.

```python
# POST field name for each internal key.
# Must match the fastcgi_param names in nginx/weko.conf exactly (case-sensitive).
# All four keys are mandatory: weko_accounts/admin.py:64-68 reads each one
# directly, and the Shibboleth admin screen returns HTTP 400 if any is missing.
WEKO_ACCOUNTS_ATTRIBUTE_MAP = {
    'shib_eppn': 'eppn',
    'shib_user_name': 'DisplayName',
    'shib_mail': 'mail',
    'shib_role_authority_name': 'eduPersonAffiliation',   # unused in WACREN, see §7
}
```

`shib_role_authority_name` is dead weight in WACREN but the key must be present.
Give it a value that exists in `WEKO_ACCOUNTS_ATTRIBUTE_LIST`
(`weko_accounts/config.py:97-120`): with `''` the admin screen's `<select>` has
no matching option, the browser pre-selects the first entry (`eppn`), and saving
the form writes `eppn` into the DB row.

```bash
docker compose restart web
curl -sk https://<host>/ -o /dev/null      # trigger before_app_first_request
psql -U invenio -d invenio -c \
  "select settings from admin_settings where name='attribute_mapping';"
```

For a temporary test without a restart (reverts on the next start):

```bash
docker compose exec web invenio admin_settings mapping_update --shib_mail mail
```

### 5.2 Hop (C) — nginx

Add the pair to **both** files if either is missing, keeping the names identical:

```nginx
# nginx/shib_fastcgi_params  (the list login.py scans)  and
# nginx/weko.conf, inside `location ~ /secure/`         (what actually sets it)
shib_request_set $shib_mail $upstream_http_variable_mail;
fastcgi_param mail $shib_mail;
```

Keep every forwarded attribute listed in `more_clear_input_headers`
(`weko.conf:143`) — that is what stops a caller from spoofing the attribute in a
request header. Then `docker compose restart nginx`.

### 5.3 Hop (A) — ask the IdP to release `mail`

Provide the SP entityID (`nginx/shibboleth2.xml:26`, currently
`https://research.ren.ng/shibboleth-sp` — confirm against the deployed file) and
request the three attributes WEKO uses:

```xml
<AttributeFilterPolicy id="releaseToWEKO3">
  <PolicyRequirementRule xsi:type="Requester"
      value="https://research.ren.ng/shibboleth-sp"/>

  <AttributeRule attributeID="eduPersonPrincipalName">
    <PermitValueRule xsi:type="ANY"/>
  </AttributeRule>
  <AttributeRule attributeID="mail">
    <PermitValueRule xsi:type="ANY"/>
  </AttributeRule>
  <AttributeRule attributeID="displayName">
    <PermitValueRule xsi:type="ANY"/>
  </AttributeRule>
</AttributeFilterPolicy>
```

| Attribute | OID | WEKO uses it for |
|---|---|---|
| `eduPersonPrincipalName` | `urn:oid:1.3.6.1.4.1.5923.1.1.1.6` | `shibboleth_user.shib_eppn` — account identity key |
| `mail` | `urn:oid:0.9.2342.19200300.100.1.3` | `accounts_user.email` — the profile e-mail field |
| `displayName` | `urn:oid:2.16.840.1.113730.3.1.241` | `userprofiles_userprofile.displayname` — the profile user name |

`eduPersonAffiliation`, `isMemberOf` and `wekoSocietyAffiliation` are **not**
needed — see §7.

No SP-side change is required once the IdP releases `mail`: the decoder and the
filter policy already accept it (§4.5).

- [ ] Fix applied
- [ ] 4.2 re-run and `shib_mail` now populated

---

## 6. Verify end to end, then backfill

### 6.1 Confirm a new login

Log in as a fresh test user, then:

```sql
SELECT u.id, u.email, u.active, p.displayname, p.username,
       s.shib_eppn, s.shib_mail, s.shib_user_name
FROM shibboleth_user s
JOIN accounts_user u ON u.id = s.weko_uid
LEFT JOIN userprofiles_userprofile p ON p.user_id = u.id
ORDER BY u.id DESC LIMIT 5;
```

- [ ] `accounts_user.email` holds the IdP's `mail`
- [ ] `/account/settings/profile/` shows it
- [ ] `userprofiles_userprofile.displayname` holds the IdP's `displayName`

### 6.2 Repair the existing accounts

Fixing the mapping does **not** repair existing rows. `get_relation_info()`
refreshes `shibboleth_user.shib_mail` on every login (`api.py:153-159`) but never
touches `accounts_user.email`, and `new_shib_profile()` (`api.py:242-257`) only
runs at account creation.

1. Resolve any shared-account collisions found in §3 **first** — a backfill
   cannot separate two identities already bound to one account. Detach the
   wrongly bound `shibboleth_user` row and let that user log in again to be
   provisioned properly.
2. Have the affected users log in once, so `shibboleth_user.shib_mail` is
   refreshed through the corrected mapping.
3. Take a database backup.
4. Check for collisions, then backfill:

```sql
-- accounts_user.email is UNIQUE: this must return no rows before the UPDATE
SELECT shib_mail, count(*) FROM shibboleth_user
WHERE shib_mail IS NOT NULL AND shib_mail <> ''
GROUP BY shib_mail HAVING count(*) > 1;

UPDATE accounts_user u
SET email = s.shib_mail
FROM shibboleth_user s
WHERE s.weko_uid = u.id
  AND (u.email IS NULL OR u.email = '')
  AND s.shib_mail IS NOT NULL AND s.shib_mail <> '';

UPDATE userprofiles_userprofile p
SET displayname = s.shib_user_name
FROM shibboleth_user s
WHERE s.weko_uid = p.user_id
  AND (p.displayname IS NULL OR p.displayname = '')
  AND s.shib_user_name IS NOT NULL AND s.shib_user_name <> '';
```

`userprofiles_userprofile.username` is `UNIQUE`; leave it alone unless you have
verified there are no collisions.

- [ ] Collisions resolved
- [ ] Backup taken
- [ ] Backfill applied and confirmed on the profile screen

---

## 7. Reference — the WACREN configuration

The settings below are what a WACREN deployment should hold. Values marked
*verify* are already satisfied in the working environment; the repo defaults on
this branch differ, so treat them as drift to reconcile, not as steps.

```python
# --- Shibboleth / SAML login (WACREN) ------------------------------------
WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED = True          # verify (repo default: False)
WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED = True      # verify - single IdP, no discovery service
WEKO_ACCOUNTS_SHIB_INST_LOGIN_DIRECTLY_ENABLED = False   # True = Shibboleth only, no local login
WEKO_ACCOUNTS_SHIB_DP_LOGIN_DIRECTLY_ENABLED = False

WEKO_ACCOUNTS_ATTRIBUTE_MAP = {                  # §5.1 - the fix for this issue
    'shib_eppn': 'eppn',
    'shib_user_name': 'DisplayName',
    'shib_mail': 'mail',
    'shib_role_authority_name': 'eduPersonAffiliation',   # unused
}

# Roles are assigned by hand from Administration > User Management > Users.
WEKO_ACCOUNTS_SHIB_ROLE_MANUAL_ASSIGN = True     # repo default: False
WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = False
WEKO_ACCOUNTS_IDP_ENTITY_ID = ''                 # only read by the mAP group code

# Provision an account on first login instead of prompting for an existing
# WEKO account and password. Enable only after §4 confirms `mail` arrives - see §3.
WEKO_ACCOUNTS_SKIP_CONFIRMATION_PAGE = True
```

### Why roles are not mapped in WACREN

Commit `9a9a51afe` added `WEKO_ACCOUNTS_SHIB_ROLE_MANUAL_ASSIGN`
(`weko_accounts/api.py:318-320`):

```python
def check_in(self):
    # Skip Shibboleth-driven role recalculation when roles are managed by hand
    if current_app.config['WEKO_ACCOUNTS_SHIB_ROLE_MANUAL_ASSIGN']:
        return None
    self.user.roles.clear()                       # not reached
    check_role, error = self.assign_user_role()   # not reached
    ...
```

With the flag on, none of the following runs:

- `self.user.roles.clear()` — previously every login wiped all roles before
  recomputing them, so roles assigned in the admin screen vanished on the user's
  next login. This is the behaviour the flag exists to stop.
- `assign_user_role()` (`api.py:271-295`) — splits `shib_role_authority_name` on
  `;` and matches it against `WEKO_ACCOUNTS_SHIB_ROLE_RELATION`, whose defaults
  are the Japanese JAIRO Cloud values (`管理者` / `図書館員` / `教員` / `教官`).
- `_get_roles_to_add()` / `_assign_roles_to_user()` — GakuNin mAP group binding.

`shib_role_authority_name` is still parsed and stored in
`shibboleth_user.shib_role_authority_name` (`api.py:157-159`); it has no effect
on authorisation.

The matching nginx-side switch is `NO_CHECK_WEKOSOCIETYAFFILIATION`
(`weko.conf:182`, repo default `FALSE`), which arms the
`HTTP_WEKOSOCIETYAFFILIATION` gate in `login.py:12-17`. Since WACREN logins
succeed, the deployed file must already have it as `TRUE`; the repo default is
drift to reconcile, not an action.

### `WEKO_ACCOUNTS_SSO_ATTRIBUTE_MAP`

No change needed (`scripts/instance.cfg:589-597`), except the hardening in §3:
`'SHIB_ATTR_MAIL': (True, 'shib_mail')` makes a login without `mail` fail loudly
instead of creating a blank-e-mail account.

---

## 8. Known issues in the code

Not fixed by configuration; track separately.

| # | Location | Issue | Suggested fix |
|---|---|---|---|
| 1 | `api.py:197` | `bind_relation_info()` assigns `self.user.email = self.shib_attr['shib_mail']` unconditionally, so an empty `shib_mail` wipes a correct existing e-mail | Skip the assignment when `shib_mail` is falsy |
| 2 | `views.py:421` + `api.py:184-212` | `find_user_by_email('')` matches an earlier blank-e-mail account, binding a different IdP identity to it | Refuse to look up or bind on an empty e-mail |
| 3 | `api.py:222` | `new_relation_info()` creates the account with `email=''`; `accounts_user.email` is `UNIQUE`, so the second such user hits an IntegrityError | Reject the login when `shib_mail` is empty |
| 4 | `config.py:68-82` | `SHIB_ATTR_MAIL` is `required=False`, so a missing `mail` fails silently | `(True, 'shib_mail')` where `mail` is required |
| 5 | `api.py:153-159` | `get_relation_info()` refreshes `shib_mail` but never syncs `accounts_user.email` | Sync `user.email` on login when it differs and is non-empty |
| 6 | `views.py:79-148` | `_adjust_shib_admin_DB()` overwrites `attribute_mapping`, `shib_login_enable` and `default_role_settings` from config on every start, discarding admin-screen edits | Write defaults only when the row is absent |
| 7 | `admin.py:64-68` | The Shibboleth admin screen raises `KeyError` → HTTP 400 if any of the four `WEKO_ACCOUNTS_ATTRIBUTE_MAP` keys is missing | Use `.get()` with a default |

Items 1–3 are why a blank `mail` escalates from a display defect to an account
integrity problem. Item 6 is why `invenio.cfg` — not the admin screen — is the
place of record.

---

## 9. Rollback

1. Restore the previous `invenio.cfg` and, if touched, `nginx/weko.conf` /
   `nginx/shib_fastcgi_params`.
2. `docker compose restart web nginx`. `_adjust_shib_admin_DB()` rewrites
   `admin_settings.attribute_mapping` from the restored config on the first
   request, so no manual DB edit is needed.
3. Remove `/secure/info.py` if it was deployed for §4.4.
4. The `UPDATE` statements in §6.2 are not reversible — restore from the backup.

---

## 10. Appendix

### Attribute chain

| Profile field | WEKO internal key | POST field / `fastcgi_param` | SP attribute id | OID |
|---|---|---|---|---|
| E-mail address | `shib_mail` | `mail` | `mail` | `urn:oid:0.9.2342.19200300.100.1.3` |
| User name | `shib_user_name` | `DisplayName` | `displayName` | `urn:oid:2.16.840.1.113730.3.1.241` |
| (identity key, not shown) | `shib_eppn` | `eppn` | `eppn` | `urn:oid:1.3.6.1.4.1.5923.1.1.1.6` |
| (unused in WACREN) | `shib_role_authority_name` | — | — | — |

University / department / position / phone number and the other
`userprofiles_userprofile` columns have **no** SSO mapping at all. They are
entered by hand; populating them from SAML would mean extending
`new_shib_profile()` (`api.py:242-257`).

### Source map

| Concern | Location |
|---|---|
| POST field → internal key | `modules/weko-accounts/weko_accounts/utils.py:114-152` |
| SSO endpoints, first-login branch | `modules/weko-accounts/weko_accounts/views.py:173-509` |
| Config row bootstrap/overwrite | `modules/weko-accounts/weko_accounts/views.py:79-148` |
| Account/profile creation and binding | `modules/weko-accounts/weko_accounts/api.py:125-257` |
| Role assignment and the manual-assign switch | `modules/weko-accounts/weko_accounts/api.py:271-336` |
| Shibboleth admin screen | `modules/weko-accounts/weko_accounts/admin.py:36-140` |
| Defaults | `modules/weko-accounts/weko_accounts/config.py:29-260` |
| Profile screen | `modules/weko-user-profiles/weko_user_profiles/views.py:176` |
| CGI bridge | `nginx/login.py`, `nginx/shib_fastcgi_params`, `nginx/weko.conf:141-186` |
| SP | `nginx/shibboleth2.xml`, `nginx/attribute-map.xml`, `nginx/attribute-policy.xml` |
