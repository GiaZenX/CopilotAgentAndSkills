# project_memory/ — the project's canonical state

One file is one item. There is no status monolith any more — no file that collects the status of
many items in one place, and no narrative status log. Where a status used to be written twice —
once in the item and once in a summary — it is now written once, in the item, and every summary is
regenerated.

## Layout

```
procedures/active/PROC-0001.yaml   a reusable office procedure — this kit's leading level
product/masterplan.md              frozen discovery artifact; NOT a status source
inbox/active/FR-0001.yaml          an incoming wish not yet assigned
changes/active/CR-0001.yaml        a change to an already approved revision
bugs/active/BUG-0001.yaml          a deviation from confirmed behaviour
tasks/active/TSK-0001.yaml         a work order for exactly one role
invariants/active/INV-0001.yaml    a standing rule — only when genuinely reused
decisions/active/                  decision items
project_config.yaml                the project's configuration
approvals/APR-0001.yaml            a user approval of one revision or analysis
approvals/pending/                 open approval requests — written by the KERNEL only
evidence/                          test, review and acceptance evidence
archive/<type>/<year>/<ID>.yaml    closed items leave the active context
staging/<task_id>/                 non-canonical proposals
generated/                         index.yaml, session_brief.yaml — NOT committed
```

## Rules

- **Closed leaves.** Done, rejected or superseded moves to `archive/`, so the active directories
  ARE the current context and nothing has to be filtered out while reading.
- **`generated/**` is never hand-edited and never committed.** It is rebuilt from the items; a
  hand-maintained summary is a second source of truth, which is what this structure ends.
- **History lives in git**, not as a changelog inside an active file.
- **`approvals/pending/` belongs to the kernel.** An approval an agent could write is not one.

## The field contract

Required fields per type are defined ONCE, in code: `kernel/backlog_types.REQUIRED_FIELDS`, with
the status automata beside them in `AUTOMATA`. `harness validate` checks every item against them
and names what is missing. There are deliberately no skeleton files repeating those lists here — a
second copy of a contract is a copy that goes stale.

Create items through the kernel (`harness capture`), not by hand: it allocates the id, sets the
timestamps, and refuses a shape the validator would reject anyway.

## Kit-specific files that are NOT items

`business_profile.yaml`, `master_data.yaml`, `filing_plan.yaml`, `product_catalog.yaml`,
`marketing_plan.yaml`, `content_guidelines.yaml` and `compliance_register.yaml` are configuration
and reference data, not state with a lifecycle. `filing_plan.yaml` is the SINGLE machine-readable
truth for filing. The old `filing_log.yaml` would be a REGENERATED scan index over the archive tree,
never a hand-maintained log — it is not built yet, so a V2 project has no such file (the `.gitignore`
entry is defensive).
