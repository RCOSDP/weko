# Claude Code Workflow

Use `/home/mhaya/weko/AGENTS.md` as the canonical instruction file for this
repository.

Before starting work, read these files in order:

1. `/home/mhaya/weko/AGENTS.md`
2. `/home/mhaya/weko/task_plan.md`
3. `/home/mhaya/weko/findings.md`
4. `/home/mhaya/weko/progress.md`

Rules:

- Do not repeat broad repository discovery unless the task enters a new area.
- Add reusable discoveries to `/home/mhaya/weko/findings.md`.
- Add actions taken, test results, and failure history to
  `/home/mhaya/weko/progress.md`.
- For multi-step work, update `/home/mhaya/weko/task_plan.md`.
- Keep durable instructions in `AGENTS.md`; keep task-specific knowledge in the
  persistent context files.
