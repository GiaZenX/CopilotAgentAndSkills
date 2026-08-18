# TSK-0075 close-out protocol (lead, 2026-08-18)

Round: BUG-0049 (gave_up line) + BUG-0050 (question-guard escapes) + FR-0027 (preset question
rendering). Block A, round A4a. Two verifier rounds: FAIL(F1..F8) → **PASS**. Mid-rework the
implementer agent died on repeated provider 500s; a FRESH implementer took over forensically
(handover table in report §4c) — no work lost, the session-break principle held in practice.
Report: docs/reviews/2026-08-17-tsk0075-measurements.md.

## What shipped

- BUG-0049: gate_subagent_output's pass-through line is state-accurate (retry_delivered vs
  gave_up) and jurisdiction runs before state — foreign agents and payloads without agent_type
  no longer get contract-violation records. The deliberate one-retry pass-through STAYS
  (re-blocking = endless loop; a counter would be writable state deciding enforcement) — now
  named in the docstring, in all three ENFORCEMENT lines (ast-derived tripwire both ends), and
  as hole H49 with its three bounds.
- BUG-0050: both measured escape classes (git identity, window furniture) caught as WARNINGS
  via R2b — a second word tier for environment vocabulary; ambiguous everyday words (push,
  branch, merge, terminal, …) need TWO hits after the verifier measured 8/8 legitimate product
  questions false-warning at one (9 counter-examples with their own two-direction tripwire).
  Warnings now recorded as event kind "warn" (they were logged as "block" — the F3 defect that
  had spoiled the pilot-3 count and BUG-0050's own observed line; both records corrected by the
  lead via kernel/docs). Warned roles now see the ENFORCEMENT pointer (reference_note on warn).
  The APR-marker exemption keeps kernel-built questions advice-free; measured no bypass
  (7 attack cases, both hooks).
- FR-0027: the question renders the RESULT in plain words; the delta half is REJECTED per
  DEC-0048 (measured: same target set from two installed states = same manifest hash = same
  minted approval valid in both, while "added" would be 2 vs 6 — a delta would be a signed
  sentence the hash does not bind). FR-0027 closed REJECTED, readability half delivered;
  constitutions' anchor pulled down in all three kits with a derived tripwire that renders the
  same target set from two installed states (red on both delta routes).

## Verifier PASS (round 2), self-measured

All F1-F8 re-measured on the running code; both takeover additions verified SHARPER than
claimed (B9: a freely invented ENFORCEMENT property line keeps 12 tests green — the word-list
deletion was right; the two-state tripwire is red-capable on both delta routes); round-1
batteries replayed with zero regression; mirrors over all 31 shared hook files (four deviations
all declared in KIT_SPECIFIC_HOOKS); stamp 2026.08.18-3 x3; suite 2824 passed/13 skipped and
gates 243 reproduced in the verifier's own copy.

## Hole list / records (this commit, lead)

- H49 entered with the implementer's proposal text + table row (open, not closable with this
  event's means; three named bounds).
- L9 bullet: the ENFORCEMENT property claims have no reader (verifier N2, measured with the
  invented line) — prose is signpost, not proof; the constitution tripwire shows the fix shape.
- BUG-0050 observed and the pilot-3 block count corrected earlier in the round (declared in the
  report's foreign-changes paragraph per verifier N1).
- FR-0027 → REJECTED (DEC-0048), archived. BUG-0049/BUG-0050 stay TRIAGED (fixed-bug pattern).

## Residues (named, non-blocking)

- H49 pass-through (see entry); R2b stays a word net — costs BOTH directions (unnamed-word
  question passes; one-word environment probe now silent) — named in docstring + ENFORCEMENT.
- The constitution tripwire demands three fixed phrasings (an honestly-differently-worded kit
  would go red — over-refusal, named); warning loudness on exit 0 unproven (pre-existing L9).
- Not measured: research-team scaffold, office "full" preset, codex artifact processes.
