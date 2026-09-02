# TSK-0104 merge round -- seam notes (lead, running list, 2026-09-02)

Everything below is what the four stream verifiers measured that NO stream could fix inside its
allowed_scope, plus the small prose items each final verifier left for the merge. The merge
round works this list, not a summary of it.

## Stream verdicts

| Stream | Item | Final stamp | Verdict | Patch |
|---|---|---|---|---|
| D research | TSK-0103 | research 2026.09.02-1 | PASS (2026-09-02 00:3x) | _round-scratch/TSK-0103/stream-research.patch (79 667 B, 9 files) |
| A design | TSK-0100 | dev 2026.09.01-6, office/research -3 | re-verify pending | _round-scratch/TSK-0100/stream-design.patch (153 112 B, 22 files) |
| B rollout | TSK-0101 | all three 2026.09.02-1 | re-verify pending | _round-scratch/TSK-0101/stream-rollout.patch (2076 lines, 11 files) |
| C office | TSK-0102 | office 2026.09.01-4 (first) | rework pending | _round-scratch/TSK-0102/stream-office.patch |

Apply order (DEC-0057 e): B, A, C, D. B first because its scaffold twins are the file A's H83 cut
lands in; A before C because both touch kernel; D last, it touches only research-team + docs.

## Seam work (outside every stream's scope)

1. `team-kits/kernel/cli.py` -- verbs `pin-kit` / `unpin-kit` / `rollback-kit` (B, S1; the
   protocol names the shape) and `report-gap` (C; the exact wiring stands in TSK-0102's protocol
   §2). C's tripwire `test_the_gap_command_and_the_duty_that_names_it_arrive_together` must go
   green -- so the constitution duty sentence lands in the SAME commit.
2. `team-kits/*/hooks/session_status.py` -- names the pin instead of offering the update (B, S2;
   H87). Mirrored across kits; byte-identical unless KIT_SPECIFIC_HOOKS names the reason.
3. `team-kits/gen_provider_artifacts.py` -- mirrors REFERENCE skills for Codex (A, F2). A's new
   AST test `test_the_codex_mirror_is_generated_per_role` pins today's per-role behaviour; when
   the generator changes, that test and the three role/skill sentences A rewrote ("no native copy
   on Codex, read .claude/skills/<name>/SKILL.md") must change WITH it.
4. `scaffold_team.sh` + `scaffold_team.ps1` -- copy a skill directory when it is in the preset
   OR when the kit ships no `agents/<name>.md` for it (A, H83). B reworked both twins; apply B
   first, then cut this in. A measured the failure as SILENT absence (no dangling pointer in the
   header) -- the worse direction; the merge verifier should check H83 says so.
5. `README.md` lines 333/748 (B, S3) -- command surface.
6. `docs/POST_V2_WISHLIST.md` summary table -- rows for H82 (pre-existing omission from
   TSK-0099) through H101; the streams appended entries only. Also the D clause: in
   `report_lint.py` the sentence "so no cut separates them, and any number picked here would
   blank one of them" is measurably wrong on today's tree (any cut between 71 and 87 separates
   the three measured spans); replace with the general argument (a real tag is unbounded in
   length; a cap tuned to today's tree frees a real tag tomorrow).
7. Ratchets: `tools/lead_package_sizes.json`, `tools/constitution_section_pins.json` -- every
   stream re-recorded provisionally; the merge re-records ONCE with one journal line each in
   `docs/reviews/phase0-disposition.md`.
8. Stamps: every stream stamped provisionally; the merge runs `tools/bump_kit_version.py` ONCE
   after everything else -- that stamp is the release (the user's "7.x -> 7").
9. `project_memory/.audit/hook_events.jsonl` grew in every worktree from test runs; the streams
   excluded it from their patches. Nothing to merge; the lead decides at commit time.
10. Item hygiene the kernel refused to let me fix mid-stream (READY freezes work-order fields):
    TSK-0101 and TSK-0102 forbid the three `team-kits/*/VERSION` files their own expected_outputs
    require (B7 / C-F6). Recorded here; the next stream generation gets `team-kits/*/VERSION` in
    allowed_scope explicitly. TSK-0103's docs/pilot + ratchet files were outside its allowed_scope
    (DEC-0057 c covers the ratchets, the wishlist by substance) -- same note.
11. Known merge risk (A verifier): main carries CRLF for
    `team-kits/dev-team/skills/project-manager/SKILL.md` (300 lines), stream A is LF. Expect a
    whole-file conflict there; resolve on content, then normalise to the repo's line-ending rule
    (`test_every_file_the_package_weighs_checks_out_lf`).

## DEC-0057 (g) numbers so far (wall-clock, spawn -> first implementer report)

- A: 1 h 30 (+ 54 min rework) · B: 1 h 19 (+ rework) · C: ~2 h (first) · D: 1 h 27 (+ two reworks,
  3 h 00 total to PASS)
- Every stream FAILed its first verification. Seam findings so far: 6 files no stream could touch.
- Suite time saved in streams: ~zero for A and C (kernel changes need every tools/ file).

## Added 2026-09-02 after stream A PASS

12. A verifier residue (safe direction): the AST reader in `tools/test_reference_skills.py:380-384` exempts enumerators by the NAME `listdir` -- a third mirror site written literally as `for x in os.listdir(<skills>)` passes green. One sentence at H83/H85. When TSK-0104 changes `gen_provider_artifacts.py` the tripwire fires by design (mutations A/B measured red) -- update the test and the three role/skill sentences with it.
13. Stream A final: PASS at dev 2026.09.01-6, office/research -3; patch 153 112 B, 22 files; `gen_provider_artifacts.py` byte-identical to main (only read).

## Added 2026-09-02 after stream B PASS

14. Stream B final: PASS at all three 2026.09.02-1; patch 2076 lines, 11 files; all six verifier findings closed with red-first (H96-H98 unused).
15. B verifier residues (not blocking): (a) `scaffold_team.sh:82-83` "the twins now refuse the same word for the same reason" -- true for a parent step (`..`), NOT for an ABSOLUTE path in RESTORE_SET: bash rc 0 (the path lands under the repo as a stray `C:` directory INSIDE the project, nothing outside touched), PowerShell rc 1. "no `..`" is an enumeration where the property is "the word is repo-relative". Qualify the sentence or add a line to H88. (b) `kitupdate.py:334-336` describes only the v2/mixed branch since the fix and no longer names the deciding `unknown` branch -- understatement, editorial.

## Added 2026-09-02 after stream C second verification (FAIL on one red test, final rework running)

16. C verifier N2 (being fixed in-stream): four pinned office instruction files changed, `tools/constitution_section_pins.json` not re-recorded, `test_shortening_net.py` red. ROOT CAUSE for the pilot report: the stream's DEC-0050 suite selection omitted `test_shortening_net.py` although the round changed pinned files -- selection by "what I touched" missed a suite that is affected BY CONSTRUCTION. Merge round: run the pin test explicitly after every stream's patch lands, not only at the end.
17. C residues (not blocking): (a) `usable_segment` admits Windows device names CON/PRN/AUX/NUL/COM1/LPT1 (a rule whose folder cannot be created on Windows) -- fixed or named in-stream; (b) the cmd.exe reasoning ("no substitution inside quotes; hooks registered on Bash|PowerShell only") lives in the protocol, one half-sentence owed at the `as_shell_value` docstring; (c) PRE-EXISTING, no stream's: `tools/test_hooks_v2.py:9428` is an `assert ... or True` -- a test that cannot fail, right next to the budget topic. Captured as its own BUG by the lead.
18. C verifier's own instrument note worth keeping for DEC-0057 (g): his first 39.74 s budget measurement was 3990 readings on the OLD code, not the size the implementer's 1.527 -> 0.560 s refers to -- numbers from two rigs must name their inputs before they stand side by side.

## Added 2026-09-02 after stream C final rework (confirmation pending)

19. Stream C final candidate: office 2026.09.02-3; patch 30 files +3001/-96; N1 (budget-sum test, red at 50), N2 (pins re-recorded, test_shortening_net in the final run: 3306/13/0), N3 (Windows device names) all closed; TWO ratchets provisional (lead_package office 47793 -> 49353; constitution pins four sections). Open by design: `report-gap` wiring (cli.py, seam 1) => FR-0062 half; H99 named exception awaiting the user's acceptance (the script-form class, H11).

## DEC-0057 (g) -- wall-clock per stream, spawn -> final PASS candidate (2026-09-01 21:20 base)

| Stream | first report | reworks | total to PASS/candidate | verifier rounds |
|---|---|---|---|---|
| A design | 1 h 30 | 1 (54 min) | ~3 h 00 | 2 (FAIL, PASS) |
| B rollout | 1 h 19 | 1 (~1 h) | ~3 h 15 | 2 (FAIL, PASS) |
| C office | ~2 h 05 | 2 | ~4 h 40 (candidate) | 3 (FAIL, FAIL, pending) |
| D research | 1 h 27 | 2 | 3 h 00 | 3 (FAIL, FAIL, PASS) |

## Added 2026-09-02 after the merge verifier's first pass (FAIL: 2 blockers, rework running)

20. Merge verifier Befund 1: the merge PROTOCOL spelled two V1 monolith paths -> `test_nothing_shipped_still_spells_a_v1_monolith_path` red on the merged tree (full suite: 4148 passed / 1 failed). Fix = describe, do not quote. The sweep and its code-file exception are measured sound (a planted monolith path in a template goes red).
21. Merge verifier Befund 2 (the tenth seam finding, not parallelism-caused): the seam tripwire `test_the_gap_command_and_the_duty_that_names_it_arrive_together` reads any MENTION of `report-gap`; the seam itself put the verb into the office section-0 command list, which the surface-completeness test keeps complete -> the duty half of the tripwire is dead (duty paragraph removed alone: still green). Fix = read an INVOCATION (`harness.py report-gap`), red-first both directions. Three texts overclaimed it (test docstring, four journal lines, protocol M6).
22. Residues: `gen_provider_artifacts.py:1009-1012` says twelve/nine where the merged tree measures eleven/eleven (twelve was TSK-0100's count with the user's design bundle dropped in -- qualified there, not here); H88 (a3) must say the POSIX twin reports SUCCESS over a rollback that replayed nothing (silent direction); `restore_from_snapshot` deletes before checking the saved copy exists -- unmeasured by the verifier, handed to the implementer to measure (DEC-0056 b: a corrupt snapshot causing data loss is an error class worth one check).
23. Correction to note 17 (c): on the merged tree the `assert ... or True` sits at `tools/test_hooks_v2.py:9455` (was 9428 at c155a5f). BUG-0087 updated.
24. Verifier could NOT replay `git apply --3way` for B in a clean clone ("does not match index" against the 47 CRLF-on-disk files) -- the 14/16 conflict count is derived from overlap structure, not replayed. Recorded as the limit of the (g) numbers.

Serial equivalent of the same four rounds at today's per-round average (~3 h 15 incl. verifier): ~13 h. Parallel wall-clock so far: ~4 h 45 from first spawn to last candidate. Token spend: implementers 0.35-0.56 M each, verifiers 0.19-0.30 M per round -- roughly the same per stream as a serial round, i.e. parallelism bought time, not tokens (as DEC-0057 predicted). Seam findings no stream could fix: 6 files (cli.py, session_status.py, gen_provider_artifacts.py, scaffold twins, README, hole-list table) -- all known BEFORE the merge starts, none discovered at merge time so far.
