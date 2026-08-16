# TSK-0067 close-out protocol (lead, 2026-08-16)

Round: FR-0006 — the PM installs kit updates itself (the 2026-08-04 decision V2's gate
hardening had accidentally undone). Two verifier rounds: FAIL(F1 unchanged-branch marker,
F2 unscoped stop claim ×6+, F3 dead pointer, F4 unfalsifiable success claim) → **PASS**.

## What shipped

- `team-kits/kernel/kitupdate.py` (new): `relation` as the ONE version-comparison authority
  (moved from _compat — no second ordering rule in the tree); `assert_updatable` refuses
  downgrade/same-version/content-mismatch/unreadable, all 8 verdicts reachable with honest
  messages; `assert_the_staging_is_its_own_stamp` checks the staging against its OWN content
  stamp BEFORE the first byte (verifier: covers EVERYTHING the command runs or installs —
  a smuggled Set-Content in scaffold_team.ps1 is refused, PWNED.txt never exists);
  approval kind `kit_update` signs FIVE values (kit, from/to version+content) — staging swap,
  from-drift and expiry all refused; digests shortened to 12 chars in the user question.
- Failure honesty with the week's lessons: interpreter search BEFORE any write (B6 lesson);
  TWO readers (stamp + bundle) in every failure branch (B4 lesson); the marker is written by
  the kernel itself when the installer died after moving bytes — and, since the rework, NOT
  written when nothing moved: a preset typo no longer kills the session (marker absent,
  retry reaches the installer, fix-then-success measured end-to-end).
- Session stop: gate_dispatch refuses spawns while the marker stands, bundle-trust reason
  deliberately BEFORE the marker reason (the abort window produces both, the revoked-bundle
  finding must not be masked — measured order holds). The scoped stop sentence names the
  MECHANISM at all 11 shipped places incl. the marker text itself, held by the new tripwire
  test_the_scoped_stop_sentence_is_the_one_every_kit_text_carries.
- Pilot 4 half 1 command lines (in C:/pilot3-rechnung):
  `python scripts/harness.py request-approval kit_update` (question passed on VERBATIM,
  the USER answers) then `python scripts/harness.py update-kit`.

## Verifier PASS (round 2), self-measured

F1 chain replayed 1:1 (typo → alive → retry → fix → success → spawn stopped only after the
real update); abort-window recheck (1.0s no marker / 1.6s marker forced + bundle reason first
/ 2.6s marker reason); 7 mutations red at their named tests incl. M16/M16b/M12 and the F2
specimen both ways; full-tree grep: no work-engine claim without the mechanism; suite 2676
passed, 13 skipped exclusive; mirrors/stamps/sizes/pins verified; .claude/ untouched.

## Deviations (named)

- README.md:332 — update-kit in the command-surface list; forced minimum, lead-accepted
  (third round in a row, same tripwire).
- Lead package +98/+144/+98 B this rework (+750/+463/+750 in round 1) with journal notes;
  TSK-0068 (the shortening round) is next and exists for exactly this growth.
- docs/reviews/2026-08-16-tsk0067-measurements.md: the lead struck a place-count the
  tripwire owns (verifier R-B).

## Residues (named, none blocking)

- L40 extended (lead, this commit): update-kit/request-approval kit_update pass all 8 gates
  as a subagent (repetition excluded — second run rc 1; timing control only, one-shot);
  the same-version repair scaffold deliberately has no in-session route (re-blessing a
  bundle would be the self-approval write_kit_state prevents).
- L41 extended (lead, this commit): the abort window hits update-kit too — 1.4s of ~3.4s
  left five skill dirs gone while both readers said unchanged; no marker (the F1 direction),
  enforcement layer untouched, message carries the limit, rerun heals (rc 0, skills 0→5) —
  measured. The honest remainder of the right direction.
- Codex unmeasured (installer as session child vs write-protected .codex/); second writer of
  HANDOVER_PENDING (kernel beside the two scaffolds, readers check existence); the completing
  run can also die (refusal then reports both readings and hands to the user); "19 ablations"
  total is the implementer's count — the verifier ran 7, all red.
