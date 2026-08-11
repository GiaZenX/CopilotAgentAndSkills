# Family B round 2a — Verifier verdict (TSK-0046 BUG-0004, TSK-0047 BUG-0009), 2026-08-11

## Verdict: PASS

Measured in a copy outside the repo; backward-compat measured over the read-only CLI route against
the real project_memory.

## BUG-0004 — premise_rechecks (measured USED, not removed)
The field is read (`report.py:1087` R8 warning), referenced (constitutions/architect+methodologist
skills), and written via the `update` command that landed with BUG-0001 — so the literal "no writer"
premise is outdated. The real gap (a blindly-accepted value naming no item) is closed: an entry must
name an existing item (`report.py:_check_premise_recheck`), else error. Measured: phantom → error,
real item → clean, empty list → clean; no double-report with the R8 warning (error and warning hit
different DECs; the warning skips DRAFT). Red-without-fix seen.

## BUG-0009 — links as validated fields
- (a) FR result: `resulting_item` required in CONVERTED/MERGED (status-dependent, not in the capture
  contract → backward-compatible), existence-checked; REJECTED unforced. The FR-terminal partition
  has a both-ends tripwire (`==` catches a missing terminal AND a dead entry). Measured: CONVERTED
  w/o → error, phantom → error, real → clean, REJECTED w/o → clean; mutation to drop MERGED → RED.
- (b) DEC `supersedes` (forward link on the newer decision, optional): existence + TYPE checked
  (`report.py:1201` — a non-DEC target errors), superseded-but-active → archive warning.
  `standing_decisions` derives which DECs hold. Measured: phantom → error, non-DEC → error, A
  supersedes B → B not standing / A standing / superseded[B]==A. **Cycles/self/multi all terminate**
  (pure dict-comprehensions, no recursion) — no infinite loop. Red-without-fix seen.
- Backward-compat: `validate` against real project_memory → 0 errors, 0 warnings. Kits 2026.08.11-9.

## Named residues (non-blocking, measured)
- `report.standing_decisions` has no production caller yet (only tests) — a weaker BUG-0004 smell,
  but NOT a violation: the load-bearing field `supersedes` IS consumed by the validator (archive
  warning via `_superseded_decisions` from `validate_state`), and no comment claims a production
  caller for the convenience query. Carried as "public query without a caller".
- Multi-supersession yields one archive warning for the shared target; self-supersession a
  self-referential warning — both harmless (warning level, no crash, no false-negative on real data).
- Existence check requires ANY item, not specifically the right type, for `resulting_item` and
  `premise_rechecks` (the "the RIGHT item" judgement stays the writer's); `supersedes` DOES type-check.
- DEC status is not flipped to SUPERSEDED (no live writer for DEC status; expressed via links +
  archive warning instead) — a separate gap.

## Acceptance
`pytest tools/test_report.py tools/test_backlog_types.py -q` → 87 passed (verifier self-run); full
`pytest tools/` 2481 passed / 13 skipped taken as implementer-measured; ruff/validate/stamp likewise.
The implementer caught its own comment-citation module mismatch via the full suite and fixed it
(the "a citation that verifies nothing rots" class); citations now match (`backlog_types.py:71`,
`:761-762`).
