# TSK-0076 close-out protocol (lead, 2026-08-18)

Round: FR-0026 (codex entry twin) + BUG-0043/0044/0045 (entry-flow findings) + FR-0009 (report
renames) + FR-0048 half 1 (German-rule boundary). Block A, round A4b. Two verifier rounds:
FAIL(F1..F7, prose/report only — "nothing to rebuild") → **PASS**.
Report: docs/reviews/2026-08-18-tsk0076-measurements.md.

## What shipped (user/** + docs/** + tools/**, NO kit change — stamp stays 2026.08.18-3)

- FR-0026: codex twin at parity — team-size question as its own question, not-a-one-way-door,
  set-preset named as the change route, post-install field owner named; DEC-0048 compliance in
  BOTH entry files (no sentence promises added-roles naming; checked against the shipped
  renderer).
- BUG-0043: plan dialog framed as PRESENTATION; the sign-off is an explicit recorded answer;
  plan-mode EXIT instruction mirrored into the Claude file (verifier F5). Pilot measurement
  confirmed independently: ExitPlanMode 18:00:45Z, then no user turn and no question until close.
- BUG-0045: hand-stamped fields demand the READ clock in _now_iso's format AND zone (local, no
  offset, no Z — verifier-checked against state.py:1361); applies to all hand-stamped fields.
- BUG-0044: already fixed by TSK-0064 — measured, not rebuilt (question shipped, answer is what
  gets written); the ROUTE half now has tests; the QUESTION itself remains untested (named
  residue — a word-based block selector was tried and rejected as the enumeration this repo
  already paid for twice).
- FR-0009: the five mis-named research reports renamed per content-derived ring mapping
  (verifier re-derived all six mappings himself); content byte-identical, zero stale references;
  the naming floor test's escape claim corrected to the measured truth (way out NOT open today;
  opens silently with the seventh report — both directions measured).
- FR-0048 half 1: cause analysis (11/12 turns German; the one English turn right after diving
  into the kernel contract → unbounded exception scope), boundary rebuilt around identifiers/code
  only (an English masterplan is no longer covered), step numbers replaced by content naming —
  the rule block is now byte-identical across both entry files. BINDING EFFECT UNMEASURED (needs
  a pilot). HALF 2 — home-directory rollout — WAITS ON THE USER (DEC-0045 external approval);
  until then real entry sessions run the OLD ~/.claude/CLAUDE.md: the biggest open effect gap.

## Process lesson (lead, recorded against myself)

F1: I edited docs/POST_V2_WISHLIST.md while the round was between implementer finish and verifier
verdict — the package no longer matched the report's file list. Corrected by declaration (report
§5 splits mine/not-mine with timestamps; the verifier's full-suite run covered the final tree).
Rule going forward: no lead edits to tracked files inside an open round; queue them for close-out.

## Hole list / records (this commit, lead)

- L9 bullets: cp -r of project_memory refused read-only (H19 family, workaround named);
  git hash-object classed as history-writing (precision: without -w it writes nothing);
  grep pattern .* read as ancestor path (H19 family).
- FR-0026 + FR-0009 → MERGED, archived. FR-0048 stays OPEN (half 2 = user rollout).
  BUG-0043/0044/0045 stay TRIAGED (fixed-bug pattern; 0044 fixed by TSK-0064, measured here).

## Residues (named, non-blocking)

- Preset QUESTION untested (route half measured); sign-off pinned only via its anchor (item-id
  resolution gives it teeth); German-rule and sign-off binding effect need a pilot (pilot 4 will
  run the NEW entry files via redirected config — precondition already recorded in TSK-0069
  close-out); F4 clock-zone risk closed in prose, unmeasured in behaviour.
