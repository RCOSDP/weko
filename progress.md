# Progress Log

## Session: 2026-04-06

### Phase 1: Requirements & Discovery
- **Status:** complete
- **Started:** 2026-04-06 UTC
- Actions taken:
- Read the user request and identified the goal as persistent context preparation for future coding tasks.
- Reviewed the planning workflow and decided to store reusable context in project-root markdown files.
- Files created/modified:
- `task_plan.md` (created)
- `findings.md` (created)
- `progress.md` (created)

### Phase 2: Repository Orientation
- **Status:** complete
- Actions taken:
- Inspected repository layout and confirmed this is a large monorepo with many `modules/*` packages.
- Read `AGENTS.md`, `README.rst`, `README-TEST.md`, `docker-compose2.yml`, `install.sh`, and `run-tests.sh`.
- Confirmed there is no top-level `manage.py`.
- Files created/modified:
- `task_plan.md` (updated)
- `findings.md` (updated)

### Phase 3: Persistent Context Setup
- **Status:** complete
- Actions taken:
- Seeded reusable findings and decisions for future work.
- Structured the persistent notes so future turns can resume quickly after context resets.
- Files created/modified:
- `task_plan.md` (updated)
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 4: Agent Instruction Update
- **Status:** complete
- Actions taken:
- Updated `AGENTS.md` to direct future work toward persistent notes first.
- Replaced the stale root test instruction with guidance aligned to `run-tests.sh`, targeted `pytest`, and `setup.py test`.
- Re-read the new persistent note files and confirmed they are concise enough to reuse in future turns.
- Files created/modified:
- `AGENTS.md` (updated)

### Phase 5: Delivery
- **Status:** complete
- Actions taken:
- Finalized the persistent project memory files for future tasks.
- Prepared a concise operating model for future requests to minimize repeated repository exploration.
- Files created/modified:
- `task_plan.md` (updated)
- `progress.md` (updated)

### Phase 6: Workflow Enforcement
- **Status:** complete
- Actions taken:
- Added a human-facing AI workflow section to `CONTRIBUTING.rst`.
- Added `.github/pull_request_template.md` so PRs explicitly confirm persistent-context usage.
- Added `CLAUDE.md` and `GEMINI.md` as thin adapter files that redirect those tools to `AGENTS.md` and the project memory files.
- Files created/modified:
- `CONTRIBUTING.rst` (updated)
- `.github/pull_request_template.md` (created)
- `CLAUDE.md` (created)
- `GEMINI.md` (created)

### Phase 7: Lightweight CI Enforcement
- **Status:** complete
- Actions taken:
- Reviewed existing GitHub Actions and kept the new enforcement separate from the heavy Docker-based test workflows.
- Added `scripts/check_persistent_context.sh` to detect code/config changes without corresponding updates to `task_plan.md`, `findings.md`, or `progress.md`.
- Added `.github/workflows/persistent-context.yml` to run that check on push and pull request events.
- Files created/modified:
- `scripts/check_persistent_context.sh` (created)
- `.github/workflows/persistent-context.yml` (created)
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 8: Copilot Alignment
- **Status:** complete
- Actions taken:
- Added `.github/copilot-instructions.md` so GitHub Copilot users are directed to the same canonical workflow as other agents.
- Updated `CONTRIBUTING.rst` to explicitly include GitHub Copilot in the shared AI-assisted workflow.
- Recorded the new Copilot-specific entry point in `findings.md`.
- Files created/modified:
- `.github/copilot-instructions.md` (created)
- `CONTRIBUTING.rst` (updated)
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 9: Smarter Persistent Context CI
- **Status:** complete
- Actions taken:
- Refined `scripts/check_persistent_context.sh` so first-push all-zero base SHAs fall back to the Git empty tree.
- Split the check into two levels: `progress.md` is required for executable/config changes, and `findings.md` or `task_plan.md` is additionally required for cross-cutting or code-heavy changes.
- Kept documentation-only and workflow-guidance-only changes exempt from persistent-context updates.
- Files created/modified:
- `scripts/check_persistent_context.sh` (updated)
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 10: Setup Guidance Correction
- **Status:** complete
- Actions taken:
- Verified that repository setup is performed via `./install.sh`, not via a root editable install.
- Updated `CONTRIBUTING.rst` to replace the stale `mkvirtualenv` / `pip install -e .[all]` flow with the Docker-based `install.sh` workflow.
- Recorded the correction in the persistent findings.
- Files created/modified:
- `CONTRIBUTING.rst` (updated)
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 11: Database Structure Navigation
- **Status:** complete
- Actions taken:
- Identified that DB structure is split across module models, Alembic migrations, raw SQL DDL/update files, and a large schema dump.
- Added a compact developer guide and a generated inventory page to make DB lookup faster.
- Added `scripts/generate_db_reference.py` and generated a Markdown inventory at `docs/database_inventory.md`.
- Fixed the inventory grouping so modules are shown by package name instead of an absolute-path artifact.
- Switched the DB navigation guide from Sphinx `.rst` pages to plain Markdown so it can be used directly without a docs build.
- Files created/modified:
- `docs/database_guide.md` (created)
- `docs/database_inventory.md` (created)
- `docs/source/developer/index.rst` (updated)
- `scripts/generate_db_reference.py` (created)
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 12: DB Script UX
- **Status:** complete
- Actions taken:
- Updated `scripts/generate_db_reference.py` to print the generated Markdown file path on success.
- Recorded the helper-script UX preference in `findings.md`.
- Files created/modified:
- `scripts/generate_db_reference.py` (updated)
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 13: Legacy SQL Migration Policy
- **Status:** complete
- Actions taken:
- Added `docs/database_migration_policy.md` to state that new schema changes must use Alembic.
- Added `docs/legacy_sql_inventory.md` as the starting review list for existing files under `postgresql/ddl/` and `postgresql/update/`.
- Added `scripts/check_no_new_legacy_sql.sh` and `.github/workflows/legacy-sql-policy.yml` to block newly added legacy SQL files in CI.
- Updated the DB guide to point developers at the new policy and inventory documents.
- Files created/modified:
- `docs/database_migration_policy.md` (created)
- `docs/legacy_sql_inventory.md` (created)
- `docs/database_guide.md` (updated)
- `scripts/check_no_new_legacy_sql.sh` (created)
- `.github/workflows/legacy-sql-policy.yml` (created)
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 14: CI Test Roadmap Planning
- **Status:** complete
- Actions taken:
- Consolidated the current understanding that CI test execution is already present but heavy, so the next work should prioritize test classification, stability, and required-check design.
- Recorded the high-level rollout sequence for moving toward a reliable CI-centered testing workflow.
- Files created/modified:
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 15: CI Test Current-State Assessment
- **Status:** complete
- Actions taken:
- Read `run-tests.sh`, `README-TEST.md`, `.github/workflows/unit-tests.yml`, `.github/workflows/ui-tests.yml`, `install.sh`, `docker-compose2.yml`, and representative `tox.ini` files.
- Compared the unit-test matrix to actual tox-enabled modules and identified missing CI coverage for `weko-notifications`, `weko-signposting`, and `weko-workspace`.
- Confirmed that `weko-redis` is included in the matrix despite lacking a `tests/` directory.
- Confirmed that every matrix job currently rebuilds and reinitializes the full WEKO Docker stack through `./install.sh`, which is likely the primary CI cost/stability bottleneck.
- Confirmed that local documented all-module execution (`./run-tests.sh` / `setup.py test`) does not match the CI execution contract (`tox` inside the web container).
- Files created/modified:
- `task_plan.md` (updated)
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 16: CI Test Stabilization Plan
- **Status:** complete
- Actions taken:
- Added a staged roadmap covering baseline inventory, workflow restructuring, failure triage, coverage-gap closure, actionable reporting, and long-term enforcement.
- Chose to sequence workflow-cost reduction before broad module-level bug fixing so later debugging can happen against a stable CI shape.
- Files created/modified:
- `task_plan.md` (updated)
- `progress.md` (updated)

### Phase 17: CI Test Inventory Automation
- **Status:** complete
- Actions taken:
- Added `scripts/generate_ci_test_inventory.py` to compare `.github/workflows/unit-tests.yml`, `run-tests.sh`, `modules/*/tox.ini`, and `modules/*/tests`.
- Generated `docs/ci_test_inventory.md` as a checked-in summary of current CI test coverage and mismatch points.
- Verified the script with `python3 -m py_compile scripts/generate_ci_test_inventory.py`.
- Confirmed the generated report matches the intended WEKO/Invenio module scope and highlights the current gap set.
- Files created/modified:
- `scripts/generate_ci_test_inventory.py` (created)
- `docs/ci_test_inventory.md` (created)
- `task_plan.md` (updated)
- `findings.md` (updated)
- `progress.md` (updated)

## Session: 2026-04-07

### Phase 18: Unit Test Matrix Gap Closure
- **Status:** complete
- Actions taken:
- Updated `.github/workflows/unit-tests.yml` to add `weko-notifications`, `weko-signposting`, and `weko-workspace` to the unit-test matrix.
- Re-generated `docs/ci_test_inventory.md` and confirmed that the unit-test workflow now covers all 47 tox-enabled modules.
- Kept `weko-redis` in the matrix without further changes, per the decision to handle its missing tests in a later step after the broader CI structure is cleaned up.
- Files created/modified:
- `.github/workflows/unit-tests.yml` (updated)
- `docs/ci_test_inventory.md` (updated)
- `task_plan.md` (updated)
- `findings.md` (updated)
- `progress.md` (updated)

### Phase 19: Module Test Execution Baseline
- **Status:** in_progress
- Actions taken:
- Added `scripts/survey_module_tests.py` to execute per-module `tox` commands inside the Docker `web` container and write both JSON and Markdown status reports.
- Verified the survey script with `python3 -m py_compile scripts/survey_module_tests.py`.
- Smoke-ran the survey script for `weko-redis` and confirmed it records environment failures cleanly when the `web` service is not running.
- Attempted full environment bootstrap with `bash install.sh`; initial failure was in `inbox` because `JPype1` needed `g++`.
- Fixed `inbox/Dockerfile` by adding `build-essential`, then confirmed `docker compose -f docker-compose2.yml build inbox` succeeds.
- Attempted to continue bootstrap by building the remaining services and identified an architecture blocker in Elasticsearch: the host is `aarch64`, amd64 emulation is unavailable, and the Elasticsearch 6.8 container fails with `exec format error`.
- Files created/modified:
- `scripts/survey_module_tests.py` (created)
- `docs/ci_test_status.json` (created)
- `docs/ci_test_status.md` (created)
- `inbox/Dockerfile` (updated)
- `task_plan.md` (updated)
- `findings.md` (updated)
- `progress.md` (updated)

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Repository cleanliness | `git status --short` | No unexpected local edits before preparation | Clean worktree | ✓ |
| Root test entry point discovery | `rg --files -g 'manage.py' .` | Confirm whether `manage.py` exists | No result at repository root | ✓ |
| Unit-test matrix inventory check | compare `.github/workflows/unit-tests.yml` against `modules/*/tox.ini` | CI matrix should cover intended tox-enabled modules | Matrix has 44 modules vs. 47 tox-enabled modules; 3 modules missing | ✓ |
| `weko-redis` test presence check | compare `modules/weko-redis/tox.ini` with filesystem | Module in CI matrix should have explicit test strategy | `tox.ini` exists but `tests/` directory is absent | ✓ |
| CI inventory generator syntax check | `python3 -m py_compile scripts/generate_ci_test_inventory.py` | New generator script should be syntactically valid | Passed with no output | ✓ |
| CI inventory generation | `python3 scripts/generate_ci_test_inventory.py` | Report should reflect actual WEKO/Invenio module scope | Generated `docs/ci_test_inventory.md` with 47 modules, 3 missing matrix entries, 1 matrix entry without tests | ✓ |
| Unit-test matrix gap closure | compare `.github/workflows/unit-tests.yml` against generated CI inventory after update | No tox-and-tests modules should remain outside unit CI | Inventory now reports 47 matrix entries and 0 missing tox-and-tests modules | ✓ |
| Survey script syntax check | `python3 -m py_compile scripts/survey_module_tests.py` | New survey script should be syntactically valid | Passed with no output | ✓ |
| Survey script smoke run | `python3 scripts/survey_module_tests.py --module weko-redis --timeout-seconds 1` | Script should record execution status even when environment is missing | Generated reports with `service "web" is not running` | ✓ |
| Cross-architecture container check | `docker run --rm --platform linux/amd64 alpine uname -m` | If emulation exists, amd64 containers should execute | Failed with `exec /bin/uname: exec format error` | ✓ |
| Inbox image rebuild | `docker compose -f docker-compose2.yml build inbox` | Inbox should build after adding compiler toolchain | Build succeeded | ✓ |
| Elasticsearch image build step | `docker compose -f docker-compose2.yml build web worker nginx elasticsearch` | Remaining services should build for test bootstrap | Fails at Elasticsearch with `exec /bin/sh: exec format error` | ✓ |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| 2026-04-06 UTC | Sandbox blocked initial shell reads with `bwrap: loopback: Failed RTM_NEWADDR` | 1 | Re-ran read-only inspection commands with escalated permissions |
| 2026-04-07 UTC | `bash install.sh` failed while building `inbox` because `JPype1` needed `g++` | 1 | Added `build-essential` to `inbox/Dockerfile` and verified `inbox` builds |
| 2026-04-07 UTC | Full Docker bootstrap blocked by Elasticsearch `exec format error` on `aarch64` host | 1 | Confirmed lack of amd64 emulation; full module survey remains blocked pending image/platform strategy change |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 5: Delivery |
| Where am I going? | Future task-specific work can now start from the persistent notes |
| What's the goal? | Create persistent project context so future WEKO tasks can start with minimal rediscovery |
| What have I learned? | The repo is a large module-based monorepo with Docker and per-module test flows; see `findings.md` |
| What have I done? | Created persistent notes and gathered the first reusable repository summary |

---
*Update after completing each phase or encountering errors*
