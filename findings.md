# Findings & Decisions

## Requirements
- Reduce repeated token spend on future WEKO maintenance tasks by preserving reusable repository context on disk.
- Prepare the repository so future requests like test fixes, bug investigation, null checks, and DB session lifecycle work can start with minimal re-discovery.
- Update agent-facing instructions only where that improves future efficiency.

## Research Findings
- This repository is a large monorepo centered on WEKO3, with many Python packages under `modules/`.
- Top-level operational entry points include `install.sh`, `docker-compose2.yml`, `run-tests.sh`, `README.rst`, and `README-TEST.md`.
- `docker-compose2.yml` defines the main development stack with `web`, `worker`, PostgreSQL/Pgpool, Redis, Elasticsearch, RabbitMQ, nginx-related assets, and supporting services.
- `run-tests.sh` creates a local virtualenv, installs pinned dependencies, and iterates through `modules/(invenio-|weko-)*/tests` by running `python setup.py test` inside each module.
- `README-TEST.md` documents both container-based and local `pytest` flows, including module-level and single-test execution.
- A top-level `manage.py` was not found, so generic instructions like `python manage.py test` are currently misleading for this repository.
- `git status --short` was clean at the start of this preparation work.
- The actual environment setup flow in this repository is `./install.sh`; the old `pip install -e .[all]` guidance in `CONTRIBUTING.rst` was stale and has been corrected.
- The repository did not have a root PR template, so PR-level workflow enforcement can be added cheaply through `.github/pull_request_template.md`.
- `CONTRIBUTING.rst` is the right place for the human-facing version of the agent workflow.
- Thin adapter files can point Claude Code and Gemini CLI users back to `AGENTS.md` so the rule set stays centralized.
- GitHub Copilot can use a repository-level `.github/copilot-instructions.md`, so it can be aligned to the same canonical workflow without duplicating the full ruleset elsewhere.
- Existing GitHub Actions can accept a lightweight additional workflow without coupling it to the expensive test jobs.
- A cheap enforcement rule is to fail when non-documentation files change but none of `task_plan.md`, `findings.md`, or `progress.md` were updated.
- The persistent-context check should tolerate first-push comparisons where GitHub provides an all-zero base SHA.
- A smarter rule is to require `progress.md` for executable/config changes, and require `findings.md` or `task_plan.md` as well when changes are cross-cutting or code-heavy.
- DB structure is split across SQLAlchemy models, module Alembic migrations, raw SQL files under `postgresql/`, and the large schema dump at `docs/source/developer/database.rst`.
- The existing schema dump is comprehensive but too large to serve as the first lookup entry point during routine investigation.
- A generated inventory page works well as a first entry point because it compresses models, Alembic migrations, and raw SQL DDL into one searchable page.
- Markdown is a better fit than Sphinx pages for quick repository lookup because it does not require building docs to be useful.
- For developer ergonomics, helper scripts should print a short success message when they only update files.
- `postgresql/ddl/` and `postgresql/update/` should be treated as legacy schema-change directories; new version-upgrade DB changes should go through Alembic.
- A low-friction enforcement point is CI that blocks newly added `.sql` files under `postgresql/ddl/` and `postgresql/update/`.
- The current CI already has expensive Docker-based unit and UI workflows, so test rollout planning should focus on stability, scope control, and runtime reduction before expanding coverage.
- A practical CI testing roadmap is: classify tests, stabilize module-level execution, define a smoke subset, make failures reproducible locally, then tighten required checks.
- `.github/workflows/unit-tests.yml` currently runs a 44-module matrix, but the repository has 47 tox-enabled modules; `weko-notifications`, `weko-signposting`, and `weko-workspace` are currently outside the matrix.
- The unit-test matrix includes `weko-redis`, which has a `tox.ini` but no `tests/` directory, so its CI role should be decided explicitly rather than assumed.
- The current unit-test workflow rebuilds the full Docker environment in every matrix job by calling `./install.sh`, and `install.sh` performs `docker compose build --no-cache --force-rm`, data initialization SQL imports, asset builds, and service startup. This is a major runtime and flakiness risk.
- The documented local "run all tests" path (`./run-tests.sh`) is not aligned with the GitHub Actions unit-test path: local flow uses a venv plus per-module `python setup.py test`, while CI uses `docker compose exec ... tox`.
- Representative module tox configs default to env `c1`, depend on legacy pinned requirements from `requirements2.txt`, and still declare Python 3.6 assumptions in typing/config sections. CI planning should assume legacy runtime constraints until proven otherwise.
- `.github/workflows/ui-tests.yml` is already separated from the unit workflow, but it also bootstraps the full WEKO stack from scratch and therefore shares the same startup-cost and readiness-risk profile.
- `scripts/generate_ci_test_inventory.py` now generates `docs/ci_test_inventory.md`, which compares the unit-test workflow matrix against actual `tox.ini`, `tests/`, and `run-tests.sh` coverage.
- The generated CI inventory confirms the actionable mismatch set precisely: 47 in-scope modules, 44 matrix entries, 3 tox-and-tests modules missing from the matrix (`weko-notifications`, `weko-signposting`, `weko-workspace`), and 1 matrix entry without a `tests/` directory (`weko-redis`).
- `.github/workflows/unit-tests.yml` has now been updated to include `weko-notifications`, `weko-signposting`, and `weko-workspace`, so the unit-test matrix covers all 47 tox-enabled modules.
- After the matrix update, `docs/ci_test_inventory.md` reports zero tox-and-tests modules missing from unit CI; the remaining structural mismatch is `weko-redis`, which stays in the matrix pending later test addition.
- `scripts/survey_module_tests.py` now generates `docs/ci_test_status.json` and `docs/ci_test_status.md` from actual `tox` executions in the Docker `web` container.
- A fresh all-module survey from this workspace generated 47 module results, and all 47 failed before module code executed because the sandbox cannot access `/var/run/docker.sock`; this is a workspace execution constraint, not a module-specific failure signature.
- After escalation, `docker compose -f docker-compose2.yml ps` showed no running services, and a fresh all-module survey failed uniformly with `service "web" is not running`; the next prerequisite for real module-level results is a booted WEKO Compose stack, not just image build success.
- A later `bash install.sh` run completed successfully and brought up the full WEKO Compose stack, including `web`, `worker`, `nginx`, `elasticsearch`, `postgresql`, `pgpool`, `redis`, `rabbitmq`, `mongo`, `inbox`, and `flower`.
- With the stack running, a fresh 47-module survey still failed uniformly, but the blocker moved to the test toolchain inside the `web` container: every module exits `127` with `bash: tox: command not found`.
- After host-side ownership was aligned to UID `1000`, `docker compose -f docker-compose2.yml exec -T web bash -lc './run-tests.sh'` could create `/code/venv` and proceed past the previous `/code/venv`, `/code/src`, and `./.eggs` permission failures.
- Under the corrected permissions, `run-tests.sh` reached real module execution instead of failing during setup.
- A direct module run for `weko-workspace` using the prepared `/code/venv` completed test collection and execution: 239 tests collected, 165 passed, 74 errored, 5191 warnings.
- The dominant observed `weko-workspace` failure class is missing `mocker` fixture support, which points to missing `pytest-mock` in the test environment rather than a workspace filesystem problem.
- Under `modules/` there are 51 directories total, but the WEKO/Invenio unit-test scope remains 47 tox-enabled modules; non-scope directories currently include `cookiecutter-weko-module`, `invenio-admin`, `invenio-app`, and `resources`.
- Of the 47 tox-enabled modules, 46 have a `tests/` directory and 1 (`weko-redis`) does not.
- `inbox/Dockerfile` needed `build-essential` added because the cloned `coar-notify-inbox` dependencies build `JPype1`, which failed without `g++`.
- The current machine is `aarch64`, and `docker run --platform linux/amd64 alpine uname -m` fails with `exec format error`, so amd64 container emulation is not available in this environment.
- Despite the earlier architecture concern around Elasticsearch image build behavior, a later `bash install.sh` run completed successfully and the full WEKO Compose stack came up; the active blockers have now moved from environment bootstrap to test-tooling and test-dependency gaps inside the running stack.
- The current practical blockers for collecting real module-by-module results are split by execution path: the CI-style `tox` survey fails uniformly because `tox` is absent from the `web` container, while the local `run-tests.sh` path now executes modules and exposes real test-environment issues such as missing `pytest-mock`.
- `run-tests.sh` has now been adjusted to stop depending on a writable `/code/venv` and module-local pytest cache paths: it creates its test virtualenv under `/tmp`, installs `pytest-mock` plus the CI-side tox tooling, and runs `pytest tests` with `--basetemp` and `cache_dir` redirected into `/tmp`.
- `run-tests.sh` did not previously fail the overall process when one or more modules failed; for CI use, that made the root entrypoint non-authoritative. It now tracks per-module failures, prints a summary, and exits nonzero when any selected module fails.
- `run-tests.sh` now supports `WEKO_TEST_MODULES` so CI can shard the module set without reintroducing a per-module full-stack bootstrap.
- `.github/workflows/unit-tests.yml` has been redirected away from `docker compose ... cd modules/<module> && tox` and now computes 4 deterministic shards, then executes `./run-tests.sh` inside the `web` container with `WEKO_TEST_MODULES` set for the shard.
- `scripts/ci_test_shards.py` is the new deterministic sharding helper; it discovers all `modules/(invenio-|weko-)*/tests` directories and prints one shard as a space-separated module list.
- `scripts/survey_module_tests.py` has been reworked so the survey no longer assumes a writable source checkout inside the container. It now stages a writable copy of the full `modules/` tree under a repository-local temp directory, makes that staged tree writable to the container user, and bootstraps `tox` in user site-packages if needed before running module tox commands there.
- During survey hardening, the real next failure layers after `tox: command not found` were confirmed in order: `.tox` directory creation under `/code` was denied, then copied-module relative editable dependencies (`../invenio-*`) broke, then sibling-module `.eggs` writes failed. The new staged-workspace approach is designed specifically to remove that entire class of write-path failures.
- A focused run against `invenio-communities` showed that the current suite now reaches real test execution under `run-tests.sh`, but at least one representative admin-view test hangs or blocks long enough to stall `pytest` after collection. The remaining work is no longer entrypoint wiring; it is module-level failure and hang triage.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Treat this project as a monorepo with per-module test entry points | Future tasks will often be cheaper if scoped to a single module first |
| Keep a lightweight root-level project memory instead of expanding `AGENTS.md` into a long handbook | Persistent notes can grow organically without forcing every turn to re-read large instructions |
| Use `AGENTS.md` to enforce the read order: instructions first, then persistent notes | This creates a stable startup routine for future turns |
| Plan CI test stabilization in stages starting with inventory and workflow structure, not immediate broad test fixing | Current workflow cost and scope mismatches would make module-by-module bug fixing inefficient and noisy |
| Maintain a generated CI inventory document before changing the workflow matrix | A checked-in snapshot makes scope decisions and future drift visible without re-running ad hoc analysis |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Initial shell reads were blocked by sandbox restrictions | Re-ran commands with escalated permissions for read-only inspection |
| Existing AGENTS testing guidance references `manage.py test`, but repository does not expose that entry point at root | Updated guidance to prefer `run-tests.sh` and targeted `pytest` / `setup.py test` flows |
| Root `CONTRIBUTING.rst` still described a generic virtualenv editable-install flow | Updated it to match the repository's `install.sh`-based Docker setup |

## Resources
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.github/copilot-instructions.md`
- `task_plan.md`
- `findings.md`
- `progress.md`
- `README.rst`
- `README-TEST.md`
- `install.sh`
- `run-tests.sh`
- `docker-compose2.yml`
- `modules/`
- `.github/pull_request_template.md`
- `.github/workflows/persistent-context.yml`
- `CONTRIBUTING.rst`
- `scripts/check_persistent_context.sh`
- `docs/source/developer/database.rst`
- `docs/database_guide.md`
- `docs/database_inventory.md`
- `docs/database_migration_policy.md`
- `docs/legacy_sql_inventory.md`
- `docs/ci_test_inventory.md`
- `scripts/generate_db_reference.py`
- `scripts/generate_ci_test_inventory.py`
- `scripts/check_no_new_legacy_sql.sh`
- `.github/workflows/legacy-sql-policy.yml`

## Visual/Browser Findings
- None.

## Module-Specific Findings
- `weko-authors` needs a module-unique PostgreSQL test DB; the shared `wekotest` database caused scope/setup instability similar to other modules.
- `weko-authors/tests/conftest.py` must define `WEKO_DEPOSIT_ITEM_UPDATE_TASK_TTL` in test app config or `tests/test_views.py::test_gatherById*` fails with `KeyError`.
- `weko-authors` CLI error strings for missing option values now come from Click as `Error: Option '--name' requires an argument.`; older assertions without `Option` and the trailing period are stale.
- `weko_authors.tasks.import_author()` now requires `request_info`; tests calling it directly must pass a third argument such as `None`.
- `weko_authors.tasks.import_author()` retry-path failures surface through traceback stdout rather than `caplog`, so stable assertions should check returned `status`/`error_id` instead of logger tuples.
- `weko-authors` import temp-file cleanup tests cannot write under `/code/tmp` in this workspace; they should use a temp directory under `tempfile.mkdtemp()` and patch `tempfile.gettempdir()`.
- `weko_authors.config.WEKO_AUTHORS_LIST_SCHEME` now includes `e-Rad_Researcher`, so `test_get_list_schema` should derive expected values from app config rather than a hard-coded legacy list.

---
*Update this file after every 2 view/browser/search operations*
*This prevents visual information from being lost*
