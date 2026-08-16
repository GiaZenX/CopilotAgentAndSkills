# TSK-0070 close-out protocol (lead, 2026-08-16)

Round: FR-0013 (PM shell gap) + the L40 closing direction. Two verifier rounds:
FAIL(B1 `>&` redirect unseen, B2 same-line variable target, B3 boundary prose) → **PASS**.
Block A, round A1.

## What shipped

HALF 1 — FR-0013, decision (b) built (clean split), the decision itself MEASURED:
- The claimed backstop for the honest-hole answer (c) is false as a premise: git commit behind a
  shell write passes all 8 gates, and gate_git blocks a merge only until the SAME lead self-mints
  the evidence (three evidence lines, each rc 0, then merge rc 0). gate_pipeline judges quality,
  not authorship. So (c) fell; (a) fell because the kit already owns the shell apparatus (a
  second _harness copy would be drift). Built the clean split: file property at guard_pm_scope,
  command-line parsing at gate_write_scope, rule 5 gates the one write position shell syntax
  itself defines — the target of a byte-keeping redirect. No verb list (L4).
- B1: `>&datei` is bash's csh-form of `&>datei` (both streams to the file) unless the word is a
  descriptor. _REDIRECT_RX extended with `[0-9]*>&`, one reader `_output_redirect_targets` for
  all three call sites; descriptor dropped only for `^[0-9]+$`/`-`. B2: `_line_assignments` +
  `_resolve` close `F=…; > $F` and its forms. B3: the boundary prose names all three residue
  classes, both-ends tripwired, no unconditional "does not reach".

HALF 2 — L40 second derived class:
- `_INSTALLING_COMMANDS` derived from `presets.installer_command` (the one place the kernel builds
  the installer invocation); the derivation crosses modules and resolves a constant comparator.
  A subagent is now refused set-preset AND update-kit (seven spellings + detours), create-task
  still refused, request-approval/evidence/etc. allowed, lead allowed. Two disjoint derived
  classes (orders-work; installs-enforcement).

## Verifier PASS (round 2), self-measured

The `>&` chain replayed (five write targets rc 0→2 both callers, descriptor forms stay []),
own extra spellings (`>& 2x.py`, `1>& datei`, subshell, pipeline, `3>&` over-refused) all
correct in real bash 5.2; B2 four assignment forms refused, residues honest; both ablations
red; L40 + no-lockout battery no regression; mirrors byte-identical; stamps 2026.08.16-12; suite
2758 passed, 13 skipped in the authoritative repo run.

## Hole list (this commit)

- **H46 → CLOSED**: the `>&` fix healed the repo's OWN gate 1 via the borrow mechanic
  (`_from_kit`) — measured independently (lead + verifier): `echo x >& state/.claude/kit` rc 0→2
  at gate_lead_write_scope.py, `>&2` stays rc 0. No out-of-session step needed.
- **H47 → NEW, OPEN**: the SAME B2 variable-target class is still open at the repo's gate 1 —
  it borrows the kit's target reader but not the line-assignment map, so
  `F=team-kits/kernel/state.py; echo x > $F` is rc 0 there (rc 2 at the kit gate since B2).
  Pre-existing (the kit had no resolution at HEAD). Two closing directions: (a) move resolution
  into the shared reader → a kit fix heals it via borrow (implementer scope); (b) gate 1 builds
  its own map (.claude/, out-of-session). Which one is needed is to be measured; the user decides
  after (a) is tried.
- **L43 → NEW**: the PM-shell rule-5 residue class (tool-language cp/mv/tee/sed -i/python -c,
  PowerShell cmdlets, unresolvable expansions, wrapper sh -c/bash -c/eval that disables all
  command-line rules) — the data-loss core (byte-keeping redirects + same-line variable target)
  is closed and red-tested; the residue is L4/H11 territory, a benefit-vs-maintenance decision.

## Deviations

- Section pins re-stamped (ENFORCEMENT section, 3 kits) with the intended tool.
- BUG-0056's observed text (from TSK-0069) had spelled a V1-monolith path a shipped tripwire
  refuses; the lead reworded it via the kernel — the tripwire is green in the current tree.
