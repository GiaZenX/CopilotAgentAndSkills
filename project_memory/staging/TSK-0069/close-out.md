# TSK-0069 close-out protocol (lead, 2026-08-16)

Round: FR-0004 part 1 — spec II.12 read clause by clause against the built system, the
release-readiness side check. Three verifier rounds: FAIL(9 conditions) → FAIL(2 single-spot
edits) → **PASS**. The document: docs/reviews/2026-08-16-tsk0069-ii12-side-check.md (540 lines).

## The verdict picture

82 clauses = **54 built + 2 deliberately deviated + 20 gaps + 6 not measured** — parsed from
the table by implementer AND verifier independently, not asserted. Every BUILT verdict carries
its measuring test/gate (146 file:line citations, all AST-verified to land in the function they
name); every gap became an item; every not-measured says so.

## What the loop caught (the round's own story)

- Round 1: five findings that changed WHAT gets filed — a measured gap buried under a wrong
  dedup (A20 vs L19/L20), a half-built clause marked G (E23 spawn_veto), a finding a class too
  narrow (D7 — the verifier found two MORE passing spellings), a clause mismarked N instead of
  L (H1), and a closure recommendation resting on a foreign measurement (BUG-0022).
- Round 2: the verifier caught and RETRACTED its own round-1 error — its B11 valuation would
  have reopened a user-REJECTED bug (BUG-0019) against the standing decision DEC-0040, which
  itself records that verifier and lead made the same misjudgement once before. The struck
  candidate stands in the document as a warning sign, not as silence.

## Filed from the document (this commit)

- BUG-0053 (compose foreign-project rule enumerates flags — four spellings pass),
  BUG-0054 (architecture_refs hashed without a producer), BUG-0055 (scope manifest has no
  wireframe field — DEC before fix), BUG-0056 (a recorded V1 file outside the state tree is
  writable), BUG-0057 (doctor claims spawn_veto verified on the codex path).
- FR-0037 (path-length warning), FR-0038 (auditor due-record + reporter, DEC-0028 shape),
  FR-0039 (INV.verified producer + merge blocker), FR-0040 (EVD run-scope field, possible DEC),
  FR-0041 (kit pin + rollback — precondition of FR-0004 part 2, the lateral RC),
  FR-0042 (research chain test), FR-0043 (latency bench), FR-0044 (stock classification).
- DEC-0046 (R5's mechanism→text swap recorded as decided, within the DEC-0045 envelope).

## State hygiene per the document's honest wording

- BUG-0005: already TRIAGED, fix measured red-capable (verifier mutation) — stays, like every
  fixed bug in this repo (H39 terminal honesty).
- BUG-0022: stays OPEN — the cited measurement covers BUG-0040's mechanism (fixture-captured
  CR); AC-1 (a CR reached in a real run) is open. No closure.
- BUG-0019: stays REJECTED per DEC-0040 — the round nearly reopened it and the loop caught it.
- FR-0006: MERGED and archived — update-kit (TSK-0067) delivered the whole want.

## Deviations / residues

- FR-0004 part 2 (the lateral RC) was never in TSK-0069's order — named in the document §6 and
  mechanically bound to FR-0041 (no pin, no "beside").
- Eleven clauses without own measurement stand individually in §5 (foreign measurements named
  as foreign; office/research measured only via registration and tests, no own run).
- The staging-vs-tree deviation (user's ~/.claude at 2026.08.10-1 vs tree 2026.08.16-8) is
  recorded as pilot-4 precondition — the pilot uses a redirected config, no home write needed.
- A side observation for a later round: 26 of 29 kit settings.json registrations carry no
  timeout (the verifier's round-1 margin note; no clause claims otherwise).
