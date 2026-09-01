# Full Front-end Customization (the AMS pattern)

This document describes how to replace WEKO3's public user interface with a
front-end application of your own, keeping WEKO as the repository back end
(items, files, indexes, workflow, OAI-PMH, administration).

The reference implementation shipped in this repository is **AMS**:

| Path | Role |
| --- | --- |
| `nginx/ams/weko-frontend/` | The front-end application (Nuxt 3 / Vue 3, SPA mode) |
| `nginx/Dockerfile.ams` | nginx image that also builds and runs the front end |
| `nginx/weko-ams.conf` | nginx routing between the front end and WEKO |
| `nginx/ecosystem.config.js` | pm2 process definition for the Nuxt server |
| `nginx/startup.sh` | Container entrypoint: pm2 + supervisord |

For the no-code route (admin screens only), see
[DESIGN_CUSTOMIZATION_WIDGET.md](./DESIGN_CUSTOMIZATION_WIDGET.md).

---

## 1. When to use this approach

Choose full front-end customization when Widget Design is not enough:

- you need your own information architecture (search UI, facets, item detail
  layout, landing pages) rather than WEKO's;
- you must follow a corporate design system or an existing component library;
- you want a modern SPA/SSR stack (Nuxt, Next, SvelteKit …) and its tooling;
- the metadata you display is project-specific (AMS renders RO-Crate/JSON-LD
  metadata with a repository-specific mapping).

What you keep from WEKO: the admin screens, item registration and workflow,
file storage and access control, index tree, OAI-PMH, statistics, DOI
registration. What you take over: every public page.

What you give up: Widget Design, the theme templates, and any future WEKO UI
feature — your front end must implement it. Access-control logic in particular
must be re-implemented faithfully on top of the API responses.

### An intermediate option: template override

Before writing a whole SPA, consider overriding WEKO's Jinja templates. Put your
templates in an instance-level template folder and repoint the theme in
`invenio.cfg`:

```python
BASE_PAGE_TEMPLATE      = 'my_theme/page.html'
THEME_HEADER_TEMPLATE   = 'my_theme/header.html'
THEME_FOOTER_TEMPLATE   = 'my_theme/footer.html'
THEME_BODY_TEMPLATE     = 'my_theme/body.html'
THEME_FRONTPAGE_TEMPLATE= 'my_theme/frontpage.html'
```

(The defaults are listed in `modules/weko-theme/weko_theme/config.py`.) This
keeps WEKO's Angular/React search components and its permission handling, at the
cost of coupling you to WEKO's template structure across upgrades. The rest of
this document covers the decoupled SPA route.

---

## 2. Architecture

```
                    ┌──────────────────────── nginx container ────────────────────────┐
  browser ── 443 ──▶│                                                                  │
                    │  location /            → proxy_pass http://localhost:3000  ──────┼──▶ Nuxt (pm2, cluster)
                    │  location /api/v1      ┐                                         │
                    │  location /oauth       │                                         │
                    │  location /admin,/tree │  uwsgi_pass app_server ─────────────────┼──▶ WEKO (web:5000, uwsgi)
                    │  location /oai         │                                         │
                    │  location /api/records │                                         │
                    │  location /api/files   │                                         │
                    │  location /record/<id>/(files|file_preview|preview)/             │
                    │  location /api/iiif/v2/                                          │
                    │  location /static, /data → files from the instance folder        │
                    └──────────────────────────────────────────────────────────────────┘
```

Key properties of this design:

- **Single origin.** The SPA and the WEKO API are served from the same host, so
  the browser sends no cross-origin preflights and cookies/sessions still work
  for the paths that need them.
- **The Nuxt server runs inside the nginx container**, started by pm2 in cluster
  mode from `startup.sh`, listening on `127.0.0.1:3000`. Port 8080 of the same
  container is a plain HTTP passthrough to Nuxt, useful behind an external TLS
  terminator or for debugging.
- **WEKO is untouched.** No WEKO module is modified; the front end is a client
  of the public REST API.

---

## 3. Step 1 — Decide the boundary

Enumerate every public path and assign it to the SPA or to WEKO. In the AMS
configuration WEKO keeps:

- `/admin` — all administration screens
- `/oauth` — the OAuth2 authorization and token endpoints
- `/tree` — index tree endpoints used by the admin UI
- `/oai` — OAI-PMH (also used by the SPA's "export metadata" links)
- `/api/v1/**` — the versioned public REST API
- `/api/records`, `/api/files`, `/api/iiif/v2/` — deposit/file/IIIF APIs
- `/record/<id>/files/…`, `/record/<id>/file_preview/…`, `/record/<id>/preview/…`
  — file delivery and preview
- `/static`, `/data` — assets from the instance folder
- `/weko/shib`, `/Shibboleth.sso`, `/secure` — Shibboleth SSO

Everything else falls through to `location /` and is rendered by the SPA.

> **Caveat:** anything you link to on the WEKO side must have an explicit nginx
> `location`, otherwise it is swallowed by `location /` and answered by the SPA.
> For example the AMS `Export` component links to
> `/records/<id>/export/json` and `/records/<id>/export/bibtex`, which are *not*
> in the default `weko-ams.conf` location list — add a `location` for them (or
> for `/records`) if you use that component. Audit your links against the
> location list before going live.

---

## 4. Step 2 — Register an OAuth2 client in WEKO

The SPA authenticates users through WEKO's OAuth2 server
(`invenio-oauth2server`).

1. Log in to WEKO as the account that will own the client and go to
   **Settings › Applications** (`/account/settings/applications/`).
2. Create a new application with the redirect URI of your front end
   (`https://<host>/` — the AMS dev default is `http://localhost:3000`).
3. Note the **client id** and **client secret**.
4. Grant the scopes your UI needs. AMS requests:

   ```
   item:read index:read ranking:read file:read user:email
   ```

   These are defined in `weko_items_ui/scopes.py` (`item:read`,
   `ranking:read`), `weko_index_tree/scopes.py` (`index:read`),
   `weko_records_ui/scopes.py` (`file:read`) and
   `invenio_oauth2server/scopes.py` (`user:email`).

---

## 5. Step 3 — Authentication flow

AMS implements the authorization-code flow with the secret kept on the Nuxt
server side:

1. `pages/login.vue` posts the credentials to `POST /api/v1/login`.
2. On success it redirects the browser to
   `GET /oauth/authorize?response_type=code&client_id=…&scope=…&state=…`,
   storing `state` in `sessionStorage`.
3. WEKO redirects back to the SPA with `?code=…`. `pages/index.vue` calls the
   Nuxt server route `GET /api/token/create?code=…`.
4. `server/api/token/create.get.ts` exchanges the code at
   `POST /oauth/token` (`grant_type=authorization_code`) using
   `client_id` + `client_secret`, and returns the token to the browser.
5. The browser keeps `token:type`, `token:access`, `token:refresh`,
   `token:expires` and `token:issue` in `localStorage`.
6. `composables/refreshToken.ts` runs before API calls and, once the token is
   within `tokenRefreshLimit` seconds of expiry, calls
   `GET /api/token/refresh`, which performs a `grant_type=refresh_token`
   exchange server-side.
7. Every API request carries
   `Authorization: <token:type> <token:access>` plus
   `Accept-Language: ja|en` (the API accepts `en` and `ja`,
   `WEKO_RECORDS_UI_API_ACCEPT_LANGUAGES`).

**Security notes for a production port of this pattern:**

- The client secret must never reach the browser. Keep it in the private half of
  `runtimeConfig` (Nuxt exposes only `runtimeConfig.public`), and supply it from
  an environment variable (`NUXT_CLIENT_SECRET`), not from a literal in
  `nuxt.config.ts` as the AMS sample does.
- Access tokens in `localStorage` are readable by any script on the origin;
  consider an httpOnly-cookie session held by the Nuxt server if your threat
  model requires it.
- Validate the `state` parameter on return from `/oauth/authorize`.
- `server/api/token/*.ts` contain a commented-out
  `NODE_TLS_REJECT_UNAUTHORIZED = '0'`; it exists for self-signed development
  certificates only. Never enable it in production.

---

## 6. Step 4 — The API surface

WEKO's versioned public API lives under `/api/v1/...` (the `<string:version>`
segment; handlers are named `get_v1` / `post_v1` per module). The endpoints AMS
consumes, and where they are declared:

| Endpoint | Used for | Declared in |
| --- | --- | --- |
| `POST /api/v1/login`, `POST /api/v1/logout` | Credential login | `weko-accounts` |
| `GET /api/v1/records` | Search (returns `search_results`, `total_results`, `aggregations`) | `weko-search-ui` |
| `GET /api/v1/records/list` | Search result list variant | `weko-search-ui` |
| `GET /api/v1/records/<id>` | Item metadata | `weko-records-ui` |
| `GET /api/v1/records/<id>/stats` | View counts | `weko-records-ui` |
| `GET /api/v1/records/<id>/files/<filename>` | File metadata / download | `weko-records-ui` |
| `GET /api/v1/records/<id>/files/<filename>/stats` | Per-file download counts | `weko-records-ui` |
| `GET /api/v1/records/<id>/files/all`, `/files/selected` | Bulk file lists | `weko-records-ui` |
| `GET /api/v1/records/<id>/need-restricted-access`, `/files/<name>/terms`, `/files/<name>/application` | Restricted-access flow | `weko-records-ui` |
| `POST /api/v1/records/<id>/request-mail` | "Request this item" mail | `weko-records-ui` |
| `GET /api/v1/captcha/image`, `POST /api/v1/captcha/validate` | CAPTCHA for the mail forms | `weko-records-ui` |
| `GET /api/v1/tree/index`, `/tree/index/<id>`, `/tree/index/<id>/parent` | Index tree navigation | `weko-index-tree` |
| `GET /api/v1/ranking/<type>`, `/ranking/<id>/files` | Ranking blocks | `weko-items-ui` |
| `GET /api/v1/authors/count`, `/authors`, `/authors/<identifier>` | Author lookups | `weko-authors` |
| `GET /api/v1/workflow/activities` and the approve/throw-out/application routes | Workflow (if your UI exposes it) | `weko-workflow` |

Metadata export is done by linking to WEKO/OAI-PMH rather than by an API call:
`/oai?verb=GetRecord&metadataPrefix=jpcoar_1.0|oai_dc|ddi&identifier=oai:<host>:<id>`
and `/records/<id>/export/json|bibtex`.

Grep for `string:version` in `modules/weko-*/weko_*/config.py` to get the full,
current list for your WEKO version.

---

## 7. Step 5 — Application configuration

AMS separates two config layers, and it is worth keeping the distinction.

**`app.config.ts`** — what the repository *is*, evaluated at build time:

```ts
const weko = 'ams-dev.ir.rcos.nii.ac.jp';

export default defineAppConfig({
  wekoOrigin: 'https://' + weko,
  wekoApi:    'https://' + weko + '/api/v1',
  export: { jpcoar: …, dublincore: …, ddi: … },
  roCrate: { root: { … }, layer: { … }, selector: { … } },
  cc: { … }          // licence id → CC licence and link
});
```

The `roCrate` block is the interesting part: it maps the keys defined in WEKO's
**RO-Crate Mapping** admin screen onto the slots of the AMS item detail page
(thumbnail, title, creators, access rights, files, …), plus the tab/section/
subsection layering and the vocabulary WEKO uses for access levels. This is the
contract between the repository's metadata model and your UI — define one
explicitly instead of scattering field names through components.

**`nuxt.config.ts`** — how the app runs:

```ts
ssr: false,                       // AMS is a pure SPA
modules: ['@nuxtjs/tailwindcss', 'nuxt-lodash'],
runtimeConfig: {
  public: {
    clientId, redirectURI,
    apiTimeout: 10000,            // ms
    tokenRefreshLimit: 600,       // refresh this many seconds before expiry
    contact: { use: 'smtp' },
    dlRanking: { display: 5 }
  },
  clientSecret,                   // server-side only
  contact: { to, subject, smtp: {…}, gmail: {…} }
}
```

Every value in `runtimeConfig` can be overridden at run time by `NUXT_*` /
`NUXT_PUBLIC_*` environment variables — use that for per-environment deployment
instead of editing the file.

---

## 8. Step 6 — Project layout

```
nginx/ams/weko-frontend/
├── app.config.ts          # repository-specific contract (see §7)
├── nuxt.config.ts         # runtime/build configuration
├── tailwind.config.js     # design tokens
├── assets/
│   ├── sass/              # variables.scss / mixin.scss / common.scss / styles.scss
│   └── data/              # static UI definitions (search fields, filters, result columns)
├── components/
│   ├── common/            # Header, Footer, SearchForm, IndexTree, Pagination, Alert, modals
│   ├── index/             # top page blocks: LatestItem, KeywardRank, News
│   ├── search/            # Conditions, SearchResult, SummaryStyle
│   ├── detail/            # ItemInfo, ItemContent, Section/SubSection, Export, DownloadRank, ViewsNumber
│   ├── files/             # TableStyle, filter modal
│   └── contact/           # contact confirmation modal
├── composables/           # getContentById (JSON-LD @graph lookup), refreshToken
├── layouts/default.vue
├── locales/{ja,en}.json   # vue-i18n messages
├── pages/                 # index, search/, search/[id], detail, files, preview, contact, login, logout
├── plugins/i18n.ts
├── public/img/
└── server/api/            # token/create, token/refresh, mail/send, captcha/*
```

Two conventions worth copying:

- **`assets/data/*.json`** holds the declarative parts of the UI (detail search
  fields, filter definitions, result columns) so that adding a search facet is a
  data change, not a component change.
- **`server/api/`** holds everything that needs a secret or an SMTP connection —
  token exchange and contact mail. Browser code never sees those credentials.

---

## 9. Step 7 — nginx configuration

Start from `nginx/weko-ams.conf`. The essentials:

```nginx
upstream app_server { server web:5000 fail_timeout=0; }
upstream nuxt       { server localhost:3000; }

server {                       # plain HTTP passthrough (optional)
    listen 8080;
    location / { proxy_pass http://nuxt; proxy_redirect off; }
}

server {
    listen 443;
    ssl_certificate     /etc/nginx/server.crt;
    ssl_certificate_key /etc/nginx/server.key;

    location /static { root /home/invenio/.virtualenvs/invenio/var/instance; }
    location /data   { root /home/invenio/.virtualenvs/invenio/var/instance; }

    location ~ /(admin|oauth|tree) { uwsgi_pass app_server; include uwsgi_params; … }
    location /api/v1               { uwsgi_pass app_server; include uwsgi_params; … }
    location /oai                  { uwsgi_pass app_server; include uwsgi_params; … }
    location /api/records          { uwsgi_pass app_server; include uwsgi_params; … }
    location /api/files            { uwsgi_pass app_server; include uwsgi_params; … }
    location ~ /record/[0-9]*/(files|file_preview|preview)/ { uwsgi_pass app_server; … }
    location /api/iiif/v2/         { uwsgi_pass app_server; … }

    # Everything else is the SPA
    location / { proxy_pass http://nuxt; proxy_redirect off; }
}
```

Points to get right:

- **Location precedence.** nginx matches regex locations before the `/` prefix,
  and longer prefixes before shorter ones. Add a location for every WEKO path
  your SPA links to (see the caveat in §3).
- **Abuse-prone endpoints.** AMS restricts
  `/api/v1/(captcha|records/[0-9]*/request-mail)` to private networks with
  `satisfy any; allow …; deny all;`. Adjust to your deployment — if your
  contact form is reachable from the internet, that block must allow it, and the
  CAPTCHA becomes your only protection.
- **CORS headers.** `weko-ams.conf` sets `Access-Control-Allow-Origin "*"` with
  credentials, which is permissive and unnecessary in the single-origin layout.
  Narrow or remove it unless you genuinely serve the API to another origin.
- Keep the long `uwsgi_read_timeout`/`uwsgi_send_timeout` values for `/api/v1`,
  `/api/records` and `/api/files`; large file operations need them.

---

## 10. Step 8 — Build and deploy

`nginx/Dockerfile.ams` extends the standard nginx+Shibboleth image with:

```dockerfile
COPY weko-ams.conf /etc/nginx/conf.d/weko.conf     # instead of weko.conf

RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
 && apt-get update && apt-get install -y nodejs
ADD ./ams/weko-frontend /usr/local/weko-frontend
WORKDIR /usr/local/weko-frontend
RUN npm install
RUN export NODE_OPTIONS=--max_old_space_size=4096
RUN npm run build
RUN npm install -g pm2
EXPOSE 3000

ADD ./startup.sh /usr/local
ADD ./ecosystem.config.js /usr/local
CMD ["/usr/local/startup.sh"]
```

`ecosystem.config.js` runs the built server under pm2 in cluster mode:

```js
module.exports = { apps: [{
  name: 'AMS', port: '3000', exec_mode: 'cluster', instances: 'max',
  script: '/usr/local/weko-frontend/.output/server/index.mjs'
}] };
```

`startup.sh` starts pm2 first, then supervisord (which runs nginx, php-fpm and
the Shibboleth daemons).

To use it, point the `nginx` service in your compose file at this Dockerfile
(the default `docker-compose.yml` uses `build: ./nginx`, i.e. the plain
`Dockerfile`):

```yaml
  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile.ams
    ports: ["80:80", "443:443", "8080:8080"]
    volumes:
      - static_data:/home/invenio/.virtualenvs/invenio/var/instance/static
      - data_data:/home/invenio/.virtualenvs/invenio/var/instance/data
    links: [web]
```

Note that the front end is baked into the image: any change to the SPA requires
rebuilding the nginx image. If you iterate often, prefer a separate service that
mounts the source and runs `nuxt build` (or run Nuxt outside the container and
change the `nuxt` upstream accordingly).

---

## 11. Step 9 — Local development

```bash
cd nginx/ams/weko-frontend
npm install
npm run dev            # http://localhost:3000
npm run dev:ssl        # https, needs localhost.pem / localhost-key.pem
npm run lint           # eslint + prettier
npm run lintfix
```

Point `app.config.ts` at a running WEKO instance and register the dev redirect
URI (`http://localhost:3000`) on the OAuth2 application. Because the dev server
is on a different origin from WEKO, you will need CORS on the WEKO side or a
dev proxy — reproducing the single-origin nginx layout locally is the least
surprising option.

---

## 12. Checklist

- [ ] Boundary defined: every public path assigned to the SPA or to WEKO
- [ ] An nginx `location` exists for every WEKO path the SPA links to
- [ ] OAuth2 application registered, redirect URI and scopes correct
- [ ] Client secret injected from the environment, never shipped to the browser
- [ ] `state` validated on the authorization-code callback
- [ ] Token refresh working; expired-token path tested
- [ ] `Accept-Language` sent on every API call; both languages verified
- [ ] Restricted-access, embargoed and login-required items render correctly for
      anonymous, logged-in and privileged users
- [ ] File download, preview and IIIF paths reach WEKO, not the SPA
- [ ] Metadata export links (OAI-PMH, JSON, BibTeX) resolve
- [ ] CORS headers narrowed to what the deployment actually needs
- [ ] Abuse-prone endpoints (contact mail, CAPTCHA) protected
- [ ] Image rebuild included in the release procedure for front-end changes
