# Family B round 1 — Verifier verdict (TSK-0044 BUG-0021 BOM, TSK-0045 BUG-0001 update), 2026-08-11

## Verdict: PASS

Measured against the real CLI process in a sandbox outside the repo.

## BUG-0021 — BOM at capture (`cli.py:527`, `decode("utf-8-sig")`)
Leading BOM stripped → stored item has no BOM, `ü` stays `c3 bc` (BUG-0018 not undone, raw bytes
measured). A BOM in the MIDDLE of a value stays as data (roundtrip preserves U+FEFF). Empty body →
rc 2; BOM-only body → rc 2; invalid UTF-8 (`0xFC`), with or without a leading BOM → rc 2 "not valid
UTF-8", no traceback. Red-without-fix seen (revert to `decode("utf-8")` → the BOM test fails with
the very "decode using utf-8-sig" message the code now applies).

## BUG-0001 — update command (`state.py:944` `_update_item_locked`, CLI `cli.py:752`)
- All five kernel-set fields (id/status/revision/approval_ref/created) → rc 1, item byte-identical
  on disk, approval intact (a refused change is not a covert invalidation). Two fields at once (one
  allowed + one forbidden) → rc 1, all-or-nothing (refuse precedes `item.update`).
- Invalidation correct: a hashed field changed → approval gone, status→DRAFT, revision+1; a
  non-hashed field → approval/status/revision unchanged; a hashed field set to the SAME value → no
  invalidation. No over-invalidation.
- The automaton is not bypassed by field-writes: a frozen TSK plan field outside DRAFT → rc 1; an
  immutable EVD → rc 1. Red-without-fix seen (empty the forbidden list → all 5 refuse-tests red;
  disable the invalidation block → the change-test red).
- The forbidden-field limit is single-source in state.py (not duplicated in the CLI); the new e2e
  test measures it through the running CLI, so if the state guard ever falls the refuse-test goes red.

## Follow-on changes (forced by the surface-completeness test, all consistent)
`update` named in all three AGENTS.md §0 (command-list substring byte-identical across kits) and in
README.md:331; VERSION 2026.08.11-7; `lead_package_sizes.json` and `constitution_section_pins.json`
re-recorded (derived, not guessed — the ceiling==measurement and section-digest tests are green);
`validate` rc 0.

## Non-blocking note (not a hole, not a regression)
`state.py:944`'s forbidden check is a case-sensitive enumeration and `item.update` takes any
non-forbidden key literally, so `{"Status": "APPROVED"}` (capital S) creates an inert phantom field
without touching the real lowercase `status` (readers are lowercase; the approval hash runs only over
HASHED_FIELDS). Measured: `capture` behaves identically — so this is a pre-existing kernel property,
not a TSK-0045 regression. Noted here, not in the hole list. If ever addressed, it is a project-wide
"the field whitelist is an open enumeration" observation about capture+update together.

## Scope note (lead-accepted per DEC-0037)
The implementer edited README.md (repo root, outside its allowed_scope) because the surface test
requires the new command listed there. README is system documentation → system-side → the team
accepts it; the edit is correct (names `update` accurately). Future tasks that add a CLI command
should include README in scope.

## Acceptance
Targeted suites green: test_e2e.py (20), test_context_budget+test_shortening_net (67/1 skip),
test_kernel.py (49); three red-without-fix mutations seen red. Full `pytest tools/` (2472 passed/13
skipped) taken as implementer-measured (the verifier's own full run exceeded budget; relevant
subsuites measured green individually). ruff/stamp taken as implementer-measured.
