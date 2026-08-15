# TSK-0064 close-out protocol (lead, 2026-08-15)

Round: BUG-0041 + BUG-0044 (pilot 3 findings B4 + B2) — a preset change after install was a
dead end for non-developers, and the entry interview never asked the preset question it claimed
to confirm. Five verifier rounds: FAIL(3 blockers) → FAIL(B4) → FAIL(B5) → FAIL(B6) → **PASS**.
Convergence: four findings → one branch → one sentence → one line → nothing.

## What shipped

- **`team-kits/kernel/presets.py` (new) + CLI surface**: `request-approval preset --preset <n>`
  and `set-preset <n>` — the PM-drivable path. Approval kind `preset` signs the RESULT
  (preset, roles, removes); set-preset re-derives the manifest and refuses on hash mismatch.
  Version pin refuses a preset change against a newer staged kit (no smuggled kit update).
  Config edit is a structural line-edit inside the `project:` block (comments preserved,
  CRLF preserved, ambiguity refused). One role installer: the kit's own scaffold.
- **Failure honesty, hardened over three rounds**: both failure branches re-read the
  installation through TWO readers (ownership record + the role files it names); a half-written
  state can never report "unchanged"; a failed install triggers a REPAIR RUN of the restored
  preset, judged by re-reading, not by exit code; all three outcome messages are scoped to what
  was measured and carry `presets.UNREAD` (skills/provider artifacts/foreign files not re-read
  — missing AND leftover directions). The no-shell refusal is true by construction (interpreter
  search moved BEFORE the config write; measured byte-identical config after refusal).
- **`--roles/--removes` are not typable**: a resolver-owned key refuses a typed value as
  UsageError before any state is written; help text names the true source (kit's presets.yaml).
- **Entry interview (user/claude/CLAUDE.md, repo SOURCE)**: own team-size AskUserQuestion with
  presets derived from registry.yaml/presets.yaml; step 3 writes the ANSWER. Closes BUG-0044
  in the source.
- **Dead-end prose gone**: HEAD 7 hits in 6 files → worktree 0 (both-ends sweep now also
  guards README.md and BOTH global entry files, incl. the codex one nobody may write here).
- `layout.partial_writers` names the one exception in the kit-document refusal, derived;
  `gate_push_token` delegates to `approvals.live_line_approval` (one definition).

## Verifier PASS (round 5), all self-measured in real outside projects

Byte-identical config after no-shell refusal (sha256 equal); all three outcomes scoped, UNREAD
one constant three readers; class sweep over EVERY StateError: no unconditional state claim
fires after a write; ablation battery red across all five rounds (B6 1, B6b 1, B5 2, B4a 3,
M12 3, M1 14; baseline 28+1); mirrors 2 hashes over 6 files; stamps dev 2026.08.15-17 /
office -18 / research -17, proven current by a real scaffold run; suite 2612 passed, 13
skipped; .claude/ untouched (acceptance surface tools/).

## Deviations (named in-package)

- The RESTART stays: the provider reads its agent set at session start, so a changed role set
  needs one restart — the PM ASKS for it (the measured kit-update pattern). expected_outputs'
  "no restart step" is deviated from with this reason.
- README.md touched though in neither scope list — forced twice by shipped tripwires
  (command-surface completeness; dead-end sweep). Judged the forced minimum by the verifier.

## Residues (all named, none blocking)

- **L40** (hole list): a subagent reaches set-preset — controls timing/repetition of a signed
  change, never its content; repair site is the kits' subagent rule.
- **L41** (hole list): skills/provider artifacts in the abort window are not re-read — messages
  carry the limit (UNREAD); repaired by the next full installer run; pilot 4 observes.
- **FR-0026**: codex entry twin does not know set-preset. **FR-0027**: approval question shows
  the full target role set, not the delta.
- Rollout gap: the installed ~/.claude/CLAUDE.md still lacks the team-size question — closing
  it is a separate, user-approved step (scheduled before/with the release cut; pilot 4's fresh
  half uses the repo source via redirected config).
- Comment-column drift on preset rename (cosmetic); BOM latent (no shipped config carries one);
  POSIX branch of _installer_command unmeasured on this host (E2E skips off-Windows);
  office/research E2E preset change not driven; gate_push_token not exercised in a real push.
