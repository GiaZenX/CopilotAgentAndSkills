# TSK-0074 close-out protocol (lead, 2026-08-17)

Round: BUG-0046 (specialist narration / mixed-language jargon reaches the user). Block A, round
A3b. Three verifier rounds: FAIL(F1..F8) → FAIL(N1/N2 report-only + N3/N4) → **PASS** (sight
check; comment-only change proven by token stream + AST). Report:
docs/reviews/2026-08-17-tsk0074-measurements.md; repeatable analysis:
docs/reviews/2026-08-17-tsk0074-relay-origin.py.

## What the measurement showed (the round's real result)

- AC-2 separated by MEASUREMENT: origin decided by WHERE the provider stores a block (own session
  vs subagent transcript + agentType), never by wording. Whole pilot 3: 263 assistant blocks
  stored, 256 relayed; **132/256 (51.6%) were NOT the PM** but specialist transcripts the rig
  relayed unfiltered; every English block of the four complaint turns is specialist-origin.
- The mechanism is a switch: run_in_background False → 0 specialist blocks relayed; True →
  132/132. Reproduced live (SDK probes, Sonnet, 0.96 USD recorded cost).
- The kit-PM's own mixing: ONE one-word case in 112 blocks. BUG-0046's "within single PM turns"
  overclaimed (corrected in the item via kernel); the pilot doc's "im selben Zug" was right.
- The real kit fault: the constitutions PROMISED "jargon stays between agents" — an assurance
  about foreign voices the kit does not build; the PM relayed it and had to retract → one
  complaint became four.

## What shipped

- Constitutions x3: assurance out; mechanism named with its measured limit ("measured on the SDK
  stream; what a terminal client collapses of it is not"); PM address CONDITIONAL (answer if
  asked, never promise suppression); "on Claude" qualifier (Codex has no Agent/Task).
- PM/office-manager skills x3: the cost named where the mode is chosen, same conditional form.
- guard_agent_spawn: a mechanical note at the decision point (JSON boolean only, no free text —
  the DEC-0029-class language-judging gate stays rejected; correct precedent guard_question_context
  R2 + B14 porosity); stderr, exit 0, chain unbroken; red-capable test, 4/4 mutations red.
- No language-judging gate built (known-rejected direction; the item's DEC-0029 citation was a
  wrong attribution — named deviation, adjudicated honest, corrected everywhere).

## Verifier PASS (round 3)

All eight round-1 findings + four round-2 findings closed; package identity in exactly one report
place (§9): stamp 2026.08.17-10 x3, mirrors md5 633ab38e… x3, pins current, sizes on record
(+304/+330/+304 then +89/+87/+89 then unchanged); full suite 2795 passed/13 skipped (round-2 run,
carried by proven comment-only delta + 1309-test verifier subset); test_gates 243 (round-2 runs by
both roles; round-3 skip justified by the path-based derivation surface). N4 pointer dispute
settled AGAINST the verifier by his own recount (:804 correct).

## Lead homework done with this commit

- Hole list: two new L9 bullets (exit-0 stderr note reach unproven repo-wide; spawn note fires
  only on JSON bool true — "true"/1 silently no note).
- BUG-0046 observed corrected via kernel (measured two-speaker effect; stays TRIAGED per the
  fixed-bug pattern).
- FR-0048 captured: the ENTRY agent breaks the German rule itself (pilot session fd2685ae block
  #3 fully English); fix wording in user/claude/CLAUDE.md + home-directory rollout — the rollout
  is the DEC-0045 external approval that waits for the user.

## Residues (named, non-blocking)

- What the real CLI renders in the terminal is unmeasured — now correctly stated as unmeasured
  everywhere the sentence ships, instead of claimed.
- Whether a stderr note on exit 0 reaches the model is unmeasured repo-wide (L9 bullet).
- Suppression itself is not closable kit-side; bounded by the mode and parent_tool_use_id — the
  instrument half belongs to the post-release own-UI track (FR-0024/BUG-0039).
- Report :303-305 explains the verifier's miscount too generously (cosmetic; correct at next
  touch of the file).
