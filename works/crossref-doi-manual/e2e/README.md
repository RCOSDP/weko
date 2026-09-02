# Capturing the Crossref DOI manual

The screenshots in [`../images`](../images) and the terminal output in
[`../cli`](../cli) are produced by this directory, so the manual can be
refreshed against the application instead of drifting from it.

Crossref's own test system needs credentials that are not in this repository
and answers differently on every run, so the capture deposits to
[`crossref_stub.py`](./crossref_stub.py) — a local stand-in serving the two
endpoints `CrossrefAgency` talks to. The success path therefore looks the same
every time, and the run needs no Crossref account.

## What is here

| File | What it is |
| --- | --- |
| `compose.e2e.yml` | Overlay on the repository's `docker-compose.yml`: moves published ports off 80/443/8080, adds the `crossref-stub` service, and appends `crossref_e2e.cfg` to the rendered `invenio.cfg` |
| `crossref_e2e.cfg` | The Crossref settings for the capture, pointed at the stub and with the deposit and poll delays cut down |
| `crossref_stub.py` | The stand-in for `test.crossref.org`; standard library only |
| `conftest.py` | One browser, one page, one screenshot directory |
| `test_crossref_doi_manual.py` | The flow, one screenshot per step |
| `capture_cli.sh` | The `invenio workflow doi list` output and the deposit document |

## Running it

From the repository root:

```bash
# 1. Bring the stack up with the capture overlay.
docker compose -f docker-compose.yml \
               -f works/crossref-doi-manual/e2e/compose.e2e.yml up -d

# 2. Install Playwright (once).
python3 -m venv .venv-e2e
.venv-e2e/bin/pip install -r works/crossref-doi-manual/e2e/requirements.txt
.venv-e2e/bin/playwright install chromium

# 3. Capture the screens.
cd works/crossref-doi-manual/e2e && ../../../.venv-e2e/bin/python -m pytest

# 4. Capture the deposit, once the worker has had a moment to send it.
./capture_cli.sh
```

WEKO is published on <https://weko3.example.org:8443>; the capture maps that
host name to `127.0.0.1` inside chromium, so nothing has to be added to
`/etc/hosts`.

| Variable | Default | |
| --- | --- | --- |
| `WEKO_BASE_URL` | `https://weko3.example.org:8443` | Where WEKO is published |
| `WEKO_HOST_MAP` | `MAP weko3.example.org 127.0.0.1` | Chromium host resolver rule; set empty when DNS resolves the name |
| `WEKO_TEST_EMAIL` | `wekosoftware@nii.ac.jp` | A system administrator |
| `WEKO_TEST_PASSWORD` | `uspass123` | |
| `WEKO_TEST_INDEX` | `Sample Index` | Index the item is registered in |
| `WEKO_CROSSREF_TEST_PREFIX` | `10.5555` | Prefix written into the identifier settings |
| `WEKO_HEADED` | unset | Set to anything to watch the browser |

The steps share one browser on purpose: WEKO locks an activity to the session
that opened it, so a flow split across contexts locks itself out. A run that
does not reach the end leaves its activity open; the next run finds it, quits
it and starts again, so an interrupted capture does not need cleaning up by
hand.

## What the environment needs

A stack brought up from a stale image will fail in ways that have nothing to
do with Crossref. What we hit, and the fix:

- **`ModuleNotFoundError: No module named 'orjson'`, web serves 500** — the
  image predates a dependency the working tree needs. Install it into the
  container's virtualenv and restart:
  `pip install orjson` as root in `web` and `worker`.
- **`ImportError: module 'weko_theme.bundles' has no attribute
  'js_preview_widget'`, the worker restarts forever** — the `*.egg-info`
  directories baked into the image list entry points the current source no
  longer defines, and they are mounted over the working tree. Regenerate them
  inside the container:
  `for d in /code/modules/*/; do (cd "$d" && python setup.py -q egg_info); done`
  Without a running worker the deposit never leaves `pending`.
- **File upload answers 500, and the DOI grant is then refused for a missing
  `jpcoar:URI`** — `user_activity_logs` is partitioned by month and the
  partition for the current month does not exist, so every request that logs
  activity fails. Create it:
  ```sql
  CREATE TABLE user_activity_logs_YYYYMM PARTITION OF user_activity_logs
      FOR VALUES FROM ('YYYY-MM-01') TO ('YYYY-MM+1-01');
  ```
- **`invenio alembic upgrade` cannot find a revision, and `doi_deposit_log`
  does not exist** — the database is ahead of, or beside, the migrations in
  the working tree. Create the one table directly:
  ```python
  from weko_workflow.models import DoiDepositLog
  DoiDepositLog.__table__.create(bind=db.engine, checkfirst=True)
  ```

## Known gap

The public item landing page (`/records/<id>`) is **not** captured. Record
pages do not render in this environment — an existing record answers 500 and a
new one returns a page whose body is never filled in — which is a stale asset
build, unrelated to DOI registration. The granted DOI is shown instead on the
item view reached from the activity (`13-granted-identifier.png`). Once record
pages render again, a step for the landing page belongs at the end of
`test_crossref_doi_manual.py`.

## Deposits the stub received

`crossref_stub.py` writes every deposit it is sent to `deposits/`, which is
git-ignored. That is the document WEKO actually built, and it is what
`capture_cli.sh` pretty-prints into `../cli/deposit.xml`.

Set `CROSSREF_STUB_PENDING_POLLS=n` on the stub service to have it answer the
first n polls with Crossref's `status="unknown_submission"` — its "not judged
yet" answer — before reporting success, which exercises the polling path.
