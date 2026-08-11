# INCIDENT: DEC-0001 canonical item deleted (a measured occurrence of BUG-0020)

2026-08-11, during the autonomous night. This is a real occurrence of exactly what BUG-0020
describes: a canonical item was deleted and Gate 1 did NOT catch it (an `rm`/delete verb slips
through, while `git checkout` and Write are caught).

## What happened
- `project_memory/decisions/active/DEC-0001.yaml` (the PM update-kit decision, user decision
  2026-08-04, valuable) was deleted from the working tree sometime between commit `c188d5f`
  (Family-D-quick, where it still existed) and `86b144f` (TSK-0038), and the lead's `git add -A`
  swept the deletion into `86b144f`.
- Bounded: ONLY DEC-0001 was deleted (`git show --diff-filter=D 86b144f` lists just that one file).
- No permanent loss: the content is in git history (`b32ec98`, `c188d5f`).
- `validate` stays 0/0 (no hard dangling-ref error), but BUG-0018.yaml and FR-0006.yaml reference
  DEC-0001 in text, and the regenerated index already lacks it.
- Culprit not identified from the audit log (it records hook events, not `rm`). The ruff-round
  implementer ran a working-tree write in that window; not confirmed as the deleter.

## RESTORE (external shell — Gate 1 refuses `git checkout` on canonical state from inside)
Run from a shell OUTSIDE Claude Code, in the repo root:

    git checkout c188d5f -- project_memory/decisions/active/DEC-0001.yaml
    PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory generate-index

Then commit the restore (external shell, gate 3 does not gate a shell outside Claude Code), or leave
it for the next in-session commit — `project_memory/` is excluded from the gate-3 digest, so the
restored file rides along without affecting any evidence.

## Why this matters
This is the second time a canonical item has been removed and slipped the enforcement (N5 earlier
this session removed a stray DEC-0032). BUG-0020's fix (cover rm/move of canonical items, or check
kernel identity) is validated by this incident. Two process fixes the lead adopts immediately:
1. Never `git add -A` blindly — review `git status` / staged deletions before every commit.
2. Instruct every implementer explicitly to never rm/move anything under `project_memory/`.
