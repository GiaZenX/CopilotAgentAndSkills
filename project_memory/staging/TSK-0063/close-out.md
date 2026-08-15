# TSK-0063 close-out protocol (lead, 2026-08-15)

Round: BUG-0051 — the repo gate suite's shell arbitration picked the WSL launcher once the
host grew a distro ("runs `true`" was the whole question), and the sandbox test's control
could no longer show the accident it exists for. One file changed:
`.claude/hooks/test_gates.py`. No kit content, no bump owed (measured by the verifier:
`tools/bump_kit_version.py:43` hashes only `team-kits/<kit>`).

## The fix

Arbitration is a PROPERTY now, decided where the selection happens: the arbiter must read a
nonce this process wrote back through ITS OWN redirect, judged by CONTENT, not exit code
(the launcher answers rc 0 with empty stdout — the exit code was the defect). All NINE
selection sites go through `_sees_this_filesystem` / `_can_arbitrate` (:131, :1263, :2565,
:2754, :2866, :2932, :2985, :3082, :3150). Bonus hardening: `_can_arbitrate` probes the
property BEFORE any payload runs in a candidate shell (HEAD ran a real `sed -i` in the
launcher first).

## Verifier verdict: FAIL → rework → PASS (no conditions)

First pass confirmed the code on every attack (content-beats-exit-code via its own mutant,
no arbiter/executor mismatch, red-capable reproduced twice, 243 solo in its clone in 18:19)
and failed the round on THREE PROSE FINDINGS (rule 3): a reassuring sentence measured false
(the discarded launcher DOES rewrite relatively named files on this side — H37 class), an
over-alarming "every move in the table" (only absolutely-named moves flip), and a pointer
promising env handling `_reads_back` does not build. All three corrected; final verdict PASS:
- AST comparison with docstrings blanked: identical, 28258 = 28258 lines — prose-only, so
  the earlier full run (243 passed) carries.
- B1/B2/R3 sentences re-measured true against the running host; :2405/:2473 contradiction gone.
- All three prose sweeps + ruff green, measured by the verifier itself
  (5 passed in 91.42s; the implementer's 7-test subset had missed the third sweep :3903 —
  named as a rule for prose changes, not a defect).
- Both agents owned their own errors openly (implementer: call-site count 8→9; verifier: it
  had prescribed a nonexistent sweep name — the exact pointer rot the sweep prevents).

## Red seen, not claimed

- Old selection restored in a clone: the sandbox test fails again at the control (1 failed).
- `_reads_back` degraded to `returncode == 0`: the new arbiter test goes red and the
  selection falls back to the WSL launcher — the defect mechanism, caught where it arises.

## Residues → hole list (lead's H45, this commit)

(a) the autouse session fixture demands the seeing-shell property even from shell-free
registration checks — on a WSL-only PATH, 4 ERROR vs 4 passed on HEAD, mechanism hits all
243; kept STRICT by lead decision (fail-closed in the honest direction), closing direction
named. (b) `_can_arbitrate` is covered by no red-capable test: the HEAD form restored left
8 relevant tests green in 19:51 — the removed cd probe is unobserved (H10 class).
