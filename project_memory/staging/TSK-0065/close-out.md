# TSK-0065 close-out protocol (lead, 2026-08-16)

Round: BUG-0042 (pilot 3 finding B11) per DEC-0044 — a running background dispatch survived NO
session end; three in-flight specialists lost their work, honest bookkeeping, no continuation
path. The user chose checkpoint WITH verified adoption. Two verifier rounds:
FAIL(F1..F5) → **PASS, no conditions**.

## What shipped

HYGIENE — orphaned-dispatch sweep at session start, defined not enumerated: a dispatch is
orphaned when the session that requested the child is not the one now asking.
`DISPATCHING_SESSION` recorded on the lease at claim AND the task at spawn outcome (the TTL
sweep drops the lease first); while a lease EXISTS only it answers — even empty — so a
compaction can never sweep this session's own fresh retry (F1, measured both directions plus
the TTL window). Target states DERIVED from the TSK automaton's edge set (LEASED→READY,
IN_PROGRESS→FAILED; ambiguity → report, never guess). The expired-lease sweep prints two honest
lists ("released to READY" / "lease expired, status left standing" — the old line lied). A
dispatch with NO recorded session is reported and left standing, never moved — and the briefing
plus all three constitutions §6 SAY so, scoped (F4; the unconditional "nothing is left claiming
to run" is gone; §6 now 748 B/kit, size record ratcheted DOWN with journal note).

CONTINUATION — `staging/<TSK>/checkpoint.yaml`, derived location, schema shipped. The KERNEL
measures expected_outputs digest and per-artifact sha256+bytes (a caller sending them is
refused). `verify` re-measures THREE terms — identity, contract (expected_outputs digest +
task/root revision), artifact bytes — plus, since the rework: artifact paths CONTAINED against
the project realpath on write AND verify (traversal, absolute, drive-relative, UNC, junction
links all rc 1 — F2; measured incl. a pre-fix record with an outside path now refused
honestly), and a record measuring nothing is ABSENT (F3). The retry envelope carries the
checkpoint path ONLY after verification; stdout stays header-pure; a hostile checkpoint value
in a prompt grants nothing. Both recording halves red-covered (F5: K1 → 7 real red, K2 → 2).

## Verifier PASS (round 2), self-measured

Own F1 chain replayed (fresh retry survives compaction; foreign session still sweeps with the
RIGHT attribution; TTL window decides via task), 11 containment spellings, empty-outputs
absent, both briefing classes in ONE SessionStart, K0/K1/K2 mutations, unconditional-phrase
sweep over the new prose (no hit), full suite 2637 passed/13 skipped in its copy, stamps
2026.08.16-1 current, mirrors byte-identical except the four KIT_SPECIFIC files, .claude/
untouched.

## Deviations (named)

- README.md:332 touched though out of scope — forced by the command-surface tripwire (two
  command names; restored pre-fix wording measured red). Lead accepts, same class as TSK-0064.
- The audit log gained lines written by suite runs — NOT this package's writes; captured as
  BUG-0052 (the suite writes canonical state), separate round.

## Residues → hole list (L42, this commit)

(a) kernel-side fail-open: orphaned_dispatches with None/"" calls every recorded dispatch
orphaned — the only guard is the kit hook; plus the R5 side effect (dispatch in the
dispatch→claim window reported as undecidable at every session start — noise, right
direction). (b) what a checkpoint SAYS (note/next_step) is unverified prose — only measured
facts open adoption. (c) unmeasured: provider session-id stability across compaction/resume
(candidate for the next provider measurement round), second concurrent session, office/research
E2E, SessionStart hook runtime budget with large artifacts.
