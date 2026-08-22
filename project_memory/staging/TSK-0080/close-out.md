# TSK-0080 close-out protocol (lead, 2026-08-22)

Round A after pilot 4: BUG-0058 / P4-2 — an idle dispatched specialist becomes visible instead
of staying silently IN_PROGRESS. Three verifier loops: FAIL(F1..F6) → FAIL(G1,G2) → PASS after
the verifier's own one-sentence H50 clause fix, applied verbatim by the lead. Kits 2026.08.22-4.

## What shipped

- kernel/dispatch.py: child_ended recorded on SubagentStop (recorder BEHIND gate_subagent_output
  in the chain — the gate ahead can turn a stop into a continuation); the turn end (Stop event)
  is refused exit 2 AT MOST once per finding when a lease-bearing dispatch has a stopped child
  with no booked result OR a lease that never bound a child and whose window ran out. Only
  positive records decide — the round-1 lease term produced a measured false alarm on a RUNNING
  child whose remedy destroyed its dispatch (verifier F1) and was removed. Attribution of
  id-less stops refuses whenever more than one dispatch of the role could own the stop,
  unbound ones included; a dispatch with a recorded end stops competing. A new lease clears
  both fields. Index+board regenerate on both writers.
- gate_dispatch.py (mirrored x3, byte-identical): SubagentStop recorder + Stop refusal with the
  finding, staging state and the automaton's no-progress edge; reconciliation beside it never
  swallows the finding (_report and_stop=False).
- The chain-order property test now measures EVERY registered multi-gate chain (F6 closed as a
  property, not a filename claim).
- Texts say what the term distinguishes ("a dispatch whose own records say no child is on it";
  "A bound child that outlived its lease is ... not named"); settings _comment for Stop
  corrected; "at most once per finding" everywhere (stop_hook_active lifetime unmeasured).
- Hole list: H50–H54 (lead-written, verifier-checked against his own measurements) — the H50
  in-session gap named as the deliberate trade for the measured false alarm.

## The loop's catches

F1 false positive + loss chain (verifier), F2/F3 prose overclaims incl. a stale settings
_comment, F4 misattribution (implementer's deviation from the verifier's minimal fix measured
BETTER than the proposal — expiry filter would have opened the mirror misattribution), G1
one-word constitution overclaim, G2/H50 one clause claiming an unbuilt limitation (lead's own
text, verifier-caught).

## Open, deliberately

BUG-0058 AC-2 (does Stop exit 2 reach a real session's model?) = the live test run, next step
of the release loop; H53 stop_hook_active lifetime measured there too. BUG-0058 stays OPEN
until the live run confirms; TSK-0080 CANCELLED+archived (established close form).
