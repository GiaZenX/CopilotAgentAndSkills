# TSK-0081 close-out protocol (lead, 2026-08-23)

Round B after pilot 4: BUG-0059 (old-stock update bridge) + FR-0056 (small-fixes bundle). Two
verifier loops: FAIL(B1..B3, M1/M2, L1/L2) → PASS after the verifier-prescribed H57 clause fix,
applied verbatim by the lead. Kits dev/office 2026.08.22-9, research 2026.08.22-8.

## What shipped

- BUG-0059: user/bridge/update_kit.py (installs to ~/agents-and-skills, outside ~/.claude) +
  user/claude/hooks/kit_bridge_notice.py (user-global SessionStart notice) + installer wiring.
  Measured on a REAL 2026.08.14-9 install rebuilt from revision 3598444: the bridge lifts
  without any user shell line, leaves project_memory byte-identical, refuses arguments,
  downgrade, same version, tampered staging, lifted projects (remedy: request-approval
  kit_update); reachable where the old gate refuses the scaffold line. Both roles attacked it
  independently — all eight hostile forms fail-closed; half-abort recoverable (second run lifts).
- FR-0056: reversibility clause verbatim in both entry files' team question; three SKILL texts
  aligned with the built command surface (property test over cli.build_parser); "a place you
  name is a place you wrote to" constitution line x3; master_data truth + entry gates seed
  office documents as a derivation (the "Today those files are" list removed in both twins);
  gate_ledger_valid no longer reads heredoc bodies to command parsers or the entry-point
  invocation as shell writes — per-STAGE exception after the verifier's pipe finding (B1),
  interpreter-option property instead of a flag list (L2, incl. the self-found -b/-B decoy
  defect); approvals sweep-requests (deletes only what can never mint); P4-11 documented
  boundary + parked case becomes an envelope question.
- Hole list: H55 (subagent reaches the bridge in old stock, no minted approval), H56 (half
  abort, recoverable), H57 (interpreter heredoc invisible to gate_ledger_valid — the verifier
  measured the full in-session chain to a committed invalid ledger; the entry now names the
  MEASURED limits: tool path doubly refused, nothing catches after a replaced validator, the
  replacement is visible in the commit diff; H11 class, at a kit gate) + L9 bullet (six office
  content documents without any write path, derived) + L10 bullet (SessionStart delivery of the
  global notice unmeasured — live-run measurement point).

## The loop's catches

B1: the entry-point exception dropped whole SEGMENTS, freeing pipe stages (doctor | tee
scripts/ledger_add.py — HEAD 2, briefly 0, now 2). B2: a _compat claim made false by its new
reader. B3/H57 clause: the lead's own limitation claim ("commit hangs on invalid ledger")
measured false — the commit check runs whatever validator stands. Implementer's own catches:
first HEAD comparison ran outside the hook dir (every rc 2 a loader error, re-measured), the
case-insensitive message-flag regex, the unmirrored helper rename in round A.

## Open, deliberately

Live-run measurement points now pooled: BUG-0058 AC-2 (Stop exit 2 reaches the model),
kit_bridge_notice delivery (L10), H53 stop_hook_active lifetime. BUG-0059 stays OPEN until the
live update run confirms; FR-0056 → MERGED, archived. TSK-0081 CANCELLED+archived.
