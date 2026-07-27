# Project security-review policy (read by the security-guidance plugin's LLM reviewer)

Scope guidance for this repository:

- `project_memory/**` is **project state, not executable code** — the typed item files, their
  approvals under `approvals/`, the evidence records under `evidence/`, the frozen `design/**` and
  `architecture/**` revisions, the `archive/**` of closed items, and everything regenerated under
  `project_memory/generated/**` (index, session brief, dashboard) or `project_memory/reports/*.html`.
  Do NOT deep-review any of it; the only finding worth raising there is an actual committed
  secret/credential.
- Focus the review effort on real code: `src/**`, `frontend/**`, `backend/**`, `scripts/**`, CI config.
- The repository additionally enforces SAST/SCA/secret scanning at the merge gate (scripts/quality.py:
  bandit, pip-audit/npm audit, gitleaks) — treat those classes as covered there; prioritise logic-level
  issues (injection sinks, unsafe deserialization, authz gaps) in application code.
