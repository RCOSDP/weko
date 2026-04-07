# Task Plan: Prepare Persistent Project Context And CI Test Stabilization Roadmap For Future WEKO Changes

## Goal
Create persistent project-level working notes so future requests can start from a small, reusable context instead of repeating broad repository discovery, and define a practical roadmap for making the full CI test suite reliably runnable.

## Current Phase
Phase 19

## Phases

### Phase 1: Requirements & Discovery
- [x] Understand user intent
- [x] Identify constraints and requirements
- [x] Document initial findings
- **Status:** complete

### Phase 2: Repository Orientation
- [x] Confirm high-level repository layout
- [x] Identify primary setup and test entry points
- [x] Record notable mismatches in existing instructions
- **Status:** complete

### Phase 3: Persistent Context Setup
- [x] Create `task_plan.md`
- [x] Create `findings.md`
- [x] Create `progress.md`
- [x] Seed files with reusable project context
- **Status:** complete

### Phase 4: Agent Instruction Update
- [x] Update `AGENTS.md` to point future work at persistent notes
- [x] Correct stale or risky assumptions where observed
- [x] Verify the updated guidance is concise and reusable
- **Status:** complete

### Phase 5: Delivery
- [x] Summarize the preparation work
- [x] Explain how future requests should be handled efficiently
- [x] Note remaining gaps that should be filled during future tasks
- **Status:** complete

## Key Questions
1. What minimum repository context prevents repeated broad discovery?
2. Which instructions belong in `AGENTS.md` versus persistent working notes?
3. Which current instructions appear stale and should be corrected now?

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Store reusable context in `task_plan.md`, `findings.md`, and `progress.md` at project root | These files persist across turns and are cheaper to reuse than rebuilding context in chat |
| Keep `AGENTS.md` short and directive instead of turning it into a large project manual | Short instructions are more likely to be read every turn without wasting tokens |
| Record only high-value entry points and structural facts now | Detailed module internals should be added incrementally when real tasks touch them |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| Sandbox blocked initial local reads (`bwrap: loopback: Failed RTM_NEWADDR`) | 1 | Re-ran read-only commands with escalated permissions |

## Notes
- Future tasks should start by reading `AGENTS.md`, then `task_plan.md`, `findings.md`, and `progress.md`.
- Module-specific discoveries should be appended to `findings.md` when a task explores them.

### Phase 15: CI Test Current-State Assessment
- [x] Inspect current unit-test and UI-test workflows
- [x] Compare CI matrix coverage to actual tox-enabled modules
- [x] Identify structural blockers to running the full test suite in CI
- **Status:** complete

### Phase 16: CI Test Stabilization Plan
- [x] Define target states for "all tests run in CI"
- [x] Break the work into incremental phases with measurable outputs
- [x] Record sequencing and risk-reduction strategy
- **Status:** complete

### Phase 17: CI Test Inventory Automation
- [x] Add a generator that compares the unit-test matrix to actual module test assets
- [x] Generate a repository-local inventory document for future triage
- [x] Verify the generated report matches the current repository state
- **Status:** complete

### Phase 18: Unit Test Matrix Gap Closure
- [x] Add missing tox-and-tests modules to the unit-test workflow matrix
- [x] Re-generate the CI inventory after the workflow update
- [x] Keep `weko-redis` in view as a later test-addition task rather than solving it in this step
- **Status:** complete

### Phase 19: Module Test Execution Baseline
- [x] Add a reusable script to record per-module tox execution status
- [x] Attempt to bootstrap the Docker environment needed for module execution
- [x] Identify environment-level blockers preventing the full module survey
- [ ] Collect full pass/fail/timeout results for all modules
- **Status:** in_progress

## CI Test Stabilization Roadmap

### Phase A: Establish A Reliable Baseline
- Inventory all testable modules and classify them as `tox-ready`, `tests-missing`, `known-broken`, or `UI-only`.
- Normalize the authoritative execution contract: decide whether CI standardizes on `tox` or a shared wrapper that delegates to `tox`.
- Add a machine-readable baseline report that records pass/fail/skip for each module.
- **Exit criteria:** every module in scope has an explicit owner state and execution command.

### Phase B: Fix Workflow Structure Before Fixing Test Failures
- Replace per-module full-stack rebuilds with a cheaper structure: build/start the WEKO stack once per job group, then run multiple module tests against it.
- Split fast module tests from expensive full-stack or browser-dependent tests.
- Ensure the unit-test matrix is derived from actual repository inventory rather than a hand-maintained list.
- **Exit criteria:** CI can execute the intended unit-test scope without rebuilding the whole Docker stack dozens of times.

### Phase C: Triage Module Failures Systematically
- Run the classified module set in CI-compatible containers and capture first-failure signatures.
- Group failures by shared root cause: dependency pinning, fixture/data setup, service readiness, order dependence, missing tests, and Python-version assumptions.
- Fix common infrastructure failures first, then module-specific breakages.
- **Exit criteria:** repeated failure classes are documented and at least one representative fix path exists for each class.

### Phase D: Close Coverage Gaps
- Add missing tox-matrix coverage for `weko-notifications`, `weko-signposting`, and `weko-workspace`.
- Decide whether `weko-redis` should gain tests, use a smoke assertion, or be removed from the unit-test matrix until it has real coverage.
- Verify whether any modules should move to a non-unit-test lane because they require a different runtime contract.
- **Exit criteria:** the CI inventory and actual executed module set match by policy.

### Phase E: Make Failures Actionable
- Persist per-module artifacts and concise summaries so failed jobs show which command failed and why.
- Add a lightweight smoke gate that runs on every PR, with broader/full coverage on push, nightly, or manually-triggered workflows until stability improves.
- Promote jobs to required status only after their flake rate is acceptable.
- **Exit criteria:** CI results are fast enough to use and clear enough to debug.

### Phase F: Enforce And Maintain
- Add a guard that detects new modules with `tox.ini` or `tests/` that are not represented in CI inventory.
- Document the standard local reproduction command for every CI lane.
- Review runtime and flake metrics after rollout and tighten the matrix incrementally.
- **Exit criteria:** new modules and regressions cannot silently bypass the agreed CI test policy.
