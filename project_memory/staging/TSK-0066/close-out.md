# TSK-0066 close-out protocol (lead, 2026-08-22)

Round: Pilot 4 — the pre-release confirmation pilot, three halves + one bounded supplement
session, run by ONE pilot-mechanic implementer under the lead's per-half orders (assigned_role
harness-lead: the lead orchestrated and wrote the findings; the mechanic measured). Nobody in
the runs learned it was a test; defects noted, never fixed (item rule).

Findings document: docs/pilot/2026-08-22-pilot-4-befunde.md (with the pilot-3 comparison).
Raw data, screenplays (frozen before each run), verbatims and operator steps:
C:\Offline Repos\v2-testbed\_round-scratch\TSK-0066\ (half1/half2/half3 + rig). The half-3
answer key was written by the lead BEFORE the run (answer-key.md); evaluation references
document numbers only, PII stayed local, ID/Gewerbe scans excluded.

## Result in one paragraph

Four of five hard pilot-3 blockers measured closed on the live object (B1/B2/B3/B4/B12, B15 at
PM level); DEC-0044 resumption honest and PM-drivable (work itself still lost — 0 checkpoint
files); the office kit's core claim HELD (PROC taught once, recalled unprompted in a NEW
session, 14→3 inputs; gate_filing measured as a real hook process; all three art cases answered
with asking instead of guessing). Central open finding P4-2: a dispatched specialist delivered
nothing and the PM idled nine turns without checking — first runnable result NOT reached in 46
user actions. Full P4-1..P4-13 list in the findings doc. Cost 65.93 of ~70 USD.

## Named deviations (in the findings doc as Abweichungen 1-7)

- CLAUDE_CONFIG_DIR had to be redirected (and the probe exposed that pilot 3 could not have
  seen which entry file loaded — byte-equal then, not now).
- Sonnet override per item ("Sonnet fuer Vergleichbarkeit") vs the shipped fable/opus pins
  (FR-0051) — named measurement deviation; P4-2 severity explicitly bounded by it.
- BuyPlugGo location taken from the curated copy instead of being named by the user at pilot
  start (user away, DEC-0045 autonomy).
- C:\pilot3-rechnung was deleted by the USER mid-pilot (drive cleanup, confirmed); tree digest
  proves half 1 measured the intact original; half1\rechnung (commit c455e18) is now the only
  backup of that stock.
- Two kill runs unlogged; subagent text not relayed to the persona (B5 unmeasured); two
  instrument faults named and re-run clean rather than patched.

## Bookkeeping

- FR-0055 (remoteControlAtStartup=false as shipped user-scope default) captured mid-round from
  a user request — rides with FR-0048 half 2.
- Cleanup measured by the mechanic: credentials hardlink removed (Test-Path False, live file
  untouched), live ~/.claude untouched, BuyPlugGo sources unchanged 12/12, repo at b5aca46
  with only the lead's two kernel-written files. Kept as evidence: half3/stapel, half3/_gatecheck,
  half3/fresh, half1/rechnung (backup).
- TSK-0066 → CANCELLED, archived (established TSK close form; the work is delivered, the TSK
  automaton has no DONE reachable from DRAFT without dispatch machinery this repo does not run).

## Open threads carried forward (not this round's to fix)

- P4-2 (idle specialist unnoticed) — first post-release work, to be measured on the shipped
  fable PM; P4-1 (update bootstrap gap for old stock); P4-7 (evidence/ never filled);
  P4-9/P4-10 (filing-plan onboarding completeness, folder language); P4-13 (office hook
  timeouts). Release conversation items for the user: FR-0048 half 2 rollout (+FR-0055), board
  page language + archive folder language, ultrareview yes/no before push, push announcement,
  disk inventory of legacy scratch for the user's approval.
