# TSK-0068 close-out protocol (lead, 2026-08-16)

Round: spec II.11/3 — the lead-package shortening after the replacing gates stand, plus the
shortening net's counted gap. Two verifier rounds: FAIL(F1 file-vs-symbol Codex count, F2
over-collect claim, F3 journal drift, F4 wrong row-54 reason, F5 report number) → **PASS**.

## What shipped

- NET FIX (the real deliverable): the counted gap (8 of 36 licences unjudgeable) was a READER
  defect — tool declarations via a bound name were invisible. Two derivations replace it:
  the binding reader follows the name per SCOPE (a rebind in a foreign function no longer
  leaks a tool in — measured against 89 shipped hook files: zero differences), and
  judgeability is asked only of matchers that SELECT tools. Result 8 → 0; the mutation the
  old net slept through (gate_write_scope registered on WebFetch) is red today.
- NEW measured boundary, derived per SYMBOL: five of 36 licences (rows 4, 15, 41, 54, 56)
  rest on mechanisms Codex cannot start — the hook's own HANDLERS map plus a call graph
  decide which events reach a symbol (row 54's _refuse_untrusted_bundle: PreToolUse only,
  while its file also serves Stop/SubagentStart). The permissive direction and the counting
  rule are NAMED in the document; a red test pins the file-vs-symbol confusion.
- CUTS, each with a licence and end-to-end measured in shipped kits (prose gone, refusal
  still happens): invented example filenames (dev+research §2.1 — guard_no_adhoc's DENY_NAME
  is the deciding list), the evidence flag-contract repetition (argparse required=True) and
  a third "--root" warning (dev+research §2.4), the filing refusal prose (office §2.5 —
  gate_filing speaks it verbatim). Sizes ratcheted DOWN: dev 32764→32585, office
  33773→33727, research 36875→36698; per-kit journal lines with THAT kit's rows.
- HONEST NON-CUTS: of eight redeemed licences one was cut; per-row reasons measured by the
  verifier (work-order scope vs role boundary; enforcement reference; the gate's reach limit
  measured live; guard_memory_budget's own header forbids two rows; row 54's real blockers
  are a content decision + the Codex boundary). Verdict: honest fulfilment, not shortfall.
  Reclassifying rows 17/73/106 would move two pinned counts — deferred deliberately
  (pinned numbers move on purpose, never in passing); TSK-0069 or Block A may take it up.

## Verifier PASS (round 2), self-measured

Independent per-symbol derivation (wider call graph) lands on the same five rows; three F1
mutations red in both named tests; F2 probe + counter-measurement (0 shipped differences,
four shapes correct incl. the conservative double-assignment); §9/§10 and row 54 read
against its own measurements; suite reconciled to 2680 passed/13 skipped (one more test:
the symbol floor); NO new stamps needed and none set (kit_hash == VERSION ×3, 2026.08.16-8);
.claude/ untouched; diff surface tools/ + docs/reviews only.

## Residues (named, cosmetic — no chains)

- _call_graph docstring says "self-less attributes" while the code reads only ast.Name —
  today without effect (the verifier's attribute-edge derivation lands on the same rows);
  two words to strike or one reader line to add, next time someone touches the file.
- The scope reader's rebind subtraction has no probe of its own (mutation survives);
  both untested shapes answer correctly today, one conservatively. A probe line when
  someone next works there.
- Suite-writes-audit remains BUG-0052 (unchanged, separate round).
