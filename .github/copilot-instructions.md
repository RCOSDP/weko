# GitHub Copilot Instructions

Use `/home/mhaya/weko/AGENTS.md` as the canonical instruction file for this
repository.

Before starting work, read these files in order:

1. `/home/mhaya/weko/AGENTS.md`
2. `/home/mhaya/weko/task_plan.md`
3. `/home/mhaya/weko/findings.md`
4. `/home/mhaya/weko/progress.md`

Rules:

- Avoid repeating full-repository exploration for routine tasks.
- Append reusable discoveries to `/home/mhaya/weko/findings.md`.
- Record actions taken, tests run, and failures in
  `/home/mhaya/weko/progress.md`.
- For multi-step work, update `/home/mhaya/weko/task_plan.md`.
- Keep durable repository instructions in `AGENTS.md` and keep task-specific
  notes in the project-root persistent context files.
