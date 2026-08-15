# TSK-0062 close-out protocol (lead, 2026-08-15)

Round: BUG-0040 — an approved amendment's criteria are dispatchable. Implementer:
harness-implementer (session task a5b541e011c4c1b4e); verifier: harness-verifier, read-only
clone outside the repo. Verdict: **PASS**, after one FAIL round whose three blockers were
each re-verified with the verifier's own mutations.

## What the package is

- `kernel/dispatch.py`: the criteria universe a task's `acceptance_refs` resolve in is now
  DERIVED in one place — root criteria plus the criteria of amendments that (a) are an
  amendment type (`backlog_types.AMENDMENT_TYPES`), (b) bind to THIS root (`_binds_to`),
  (c) stand in a status a user's approval put them in (`approvals.approved_statuses`),
  (d) whose approval is in force AND signs the criteria (`assert_apr_in_force` +
  `_approval_covers_criteria`). Refusals carry the excluded amendments with reasons
  (BUG-0039's failure mode).
- Amendment entry through `derives_from` (hop 1) is closed: `dispatch.py:1147-1148` —
  an amendment's criteria are approval-gated, hop 2 or nothing.
- `kernel/backlog_types.py`: `AMENDMENT_TYPES` derived from `AMENDMENT_REVISION_FIELD`
  (`target_revision`) over the declared field contracts; both ends held by
  `tools/test_backlog_types.py` (the amendment-property test).
- Tests: `tools/test_approvals_dispatch.py:2803-3044` — incl. the smuggle test for the
  one unsigned-channel guard line (`_approval_covers_criteria`'s return line), the
  derives_from exclusion tests, and the APPLIED-stop test.

## Verifier PASS (final round)

- B1 (guard line untested) — red test exists and is the line's only cover; verified by
  mutating the guard line in the clone: test red, suite otherwise green.
- B2 (derives_from hole) — closed for amendment types; live replay: DRAFT-CR via
  `derives_from` rc 2, APPROVED CR rc 0, TRIAGED-BUG via `derives_from` rc 0.
- B3 (docstring claims) — honest: each limit named where it lives.
- Verifier retracted its own boundary suspicion (root-binding refused at creation, measured).

Pre-commit condition from the verdict, done: the justification comment
`backlog_types.py:532-540` was measured FALSE against the pilot store it cites and
corrected — under a root at revision 2 the five carrying CRs all sit at `target_revision` 2
(an equality term would have PASSED the BUG-0040 chain); the one it would drop is CR-0006
at revision 3, a later planned revision approved by the user in that form. Re-measured by
the implementer against the pilot copy before writing; kits restamped **2026.08.15-7**;
ruff clean; validate clean; amendment-property test green.

## Residues → hole list

`docs/POST_V2_WISHLIST.md` **H44** (this commit): (a) APPLIED criteria stop counting
(over-refusal, pinned by test), (b) `target_pr` membership unsigned (kernel path closed via
revision bump; open only past the kernel, which gate 1 holds shut in-session), (c)
`target_revision` read as name never compared as value (lends only user-signed content),
(d) hop-1 looseness for non-amendments (design, H39). Table row + provenance carried;
H41(d) pointer stock updated to ten, hand-resolved.

## Suite state at close-out

- `tools/` suite: green per implementer's final run; ruff + validate clean.
- Repo gate suite (`.claude/hooks/test_gates.py`, run explicitly): **241 passed, 1 failed**
  — the failure is `test_the_measurement_sandbox_leaves_a_child_shell_no_directory_word_
  that_names_another_tree`, reproduced in isolation, and is a HOST change unrelated to this
  package (a WSL distro now answers, the test's shell arbitration picks it although it
  cannot see this filesystem). Booked as **BUG-0051** in this same commit; every hole-list
  and contract tripwire covering this round's edits passed.
