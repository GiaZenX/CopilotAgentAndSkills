# TSK-0077 close-out protocol (lead, 2026-08-21)

Round: FR-0050 — the archive wall gets exactly one approval-shaped door. Pre-pilot-4 per user
decision. FOUR verifier rounds: FAIL(F1..F10) → FAIL(R1..R5) → FAIL(V1..V6) → **PASS**.
Report: docs/reviews/2026-08-18-tsk0077-measurements.md (§1-5, §5a/5b/5c).

## What shipped

- New APR kind `filing_correction` on the existing approval machinery: the clerk requests
  (document + destination-or-delete + reason), the user mints via AskUserQuestion, and
  guard_fs_tripwire honours exactly that operation exactly once. The hashed subject binds the
  EXACT operation incl. the SHA-256 of the file bytes — single-use is DERIVED (after the executed
  correction nothing lies at the source; push-token construction, no writable "used" flag).
  Delete = absence of a destination; cli reads the builder's signature (push/preset/kit_update
  measured byte-unchanged — DEC-0048 surface intact through all four rounds).
- The door opens only for a line the guard has FULLY placed: every invocation classified
  (cd / copy-move / delete / redirect / other), riders of any kind close the door (python -c,
  tar, variable rm, a bare echo, output redirects into trays in every measured spelling incl.
  &>, leading redirects, fd forms, PowerShell cmdlets). Reason folded to one line as a Unicode
  property BEFORE hashing (the user signs what they see); dead-end approvals refused (absolute/
  climbing/case-flipped spellings refused WITH the real on-disk name). CORRECTION_CAP=25 with a
  derived budget ceiling (budget_cap() from _compat.HOOK_DEADLINE_SECONDS) and a red test that
  fires if someone raises the cap past the budget.
- The loop's hardest catch sat at the ROOT: _filing._tokens truncated the argument list at the
  first `<`/`>` — a LEADING redirect hid the whole command from every reader, which could even
  disable the WALL without any approval (V1) and had been an open pre-existing wall hole at HEAD
  (`> f mv archive/… /tmp/…`). Fixed by cutting the redirect span out instead of truncating;
  the fix closed the pre-existing hole along the way. Latency sanitised: the 114-second
  timeout-kill line now refuses in 0.82 s; the 204-approval case in 0.80 s.
- Prose measured, not asserted: the final round ran every claim of the four shipped texts as a
  real hook process (verifier independently: 9/9 own claims table). The honest boundary stands
  everywhere: the four conditions decide the DOOR, never the WALL.

## Verifier PASS (round 4), self-measured

_tokens probe table reproduced; all V1/V2 chains rc 2 with the wall battery NEW==HEAD everywhere
intended; the withdrawn over-refusal rule (b) verified as not reopening anything (18 tokenless
probes); red ablations incl. the implementer's own-choice mutation; the redundant second lock
carries a comment that claims no coverage — judged the right construction. Suite 2897 passed/
13 skipped + gates 243, both reproduced. Stamps office 2026.08.21-3, dev/research 2026.08.21-2.

## Hole list / records (this commit, lead)

- L9 bullet: the two pre-existing office-wall residues (variable-rewritten operand `$A`;
  case-sensitive `under` on the move half) — measured identical at HEAD, named with closing
  directions; as RIDERS they are refused since this round, alone they stay the named wall residue.
- CLAUDE.md: the scratch-discipline rule (v2-testbed/_round-scratch/<TSK-ID>) with its case.
- Scratch relocated: the round-1 dirs (tsk0077, vfy0077) moved into the testbed at close-out.
- FR-0050 → MERGED, archived. TSK-0077 → CANCELLED, archived.

## Residues (named, non-blocking — candidates for the FR-0049 round, same kit)

- N1: _compat.py:65-66 bracket claims CORRECTION_CAP/TOTAL_BUDGET "derived from it" — CAP is
  checked against the derivation, TOTAL_BUDGET derives from nothing; the truthful paragraph
  stands two lines below. One-line fix next time the file is touched.
- N2: `2>&1` — the docstring says "no rule reads it" while the door DOES read the split `1` token
  and over-refuses with a token nobody typed; fix = N>&M as one span in REDIRECT_SPAN_RX.
- Store-scan residual is store-bound (~1-4 ms per stored approval, host-dependent; both host
  numbers in §5b) — a cap there would hit push/preset/kit_update too: kernel decision, parked.
- Unmeasured: AskUserQuestion rendering of long option descriptions; provider kill-on-timeout
  semantics (taken from _compat's recorded property); cmd.exe redirect forms beyond PowerShell.
