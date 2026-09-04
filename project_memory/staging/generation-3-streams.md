# DEC-0062 generation 3 -- five streams cut by FILE OWNERSHIP, spawned 2026-09-03 from e45c0ca (release 2026.09.02-12 dev/office, -11 research)

User decisions 2026-09-03 (AskUserQuestion, recorded in this session): all five streams as proposed;
FR-0084 (review as event) NOT in stream D -> generation 4; the four scope approvals BUG-0083..0086
minted (APR-0001..0004, EVD-0079 test run by the lead, all four VERIFIED); generation 2 PUSHED
(`c4f3cc0..e45c0ca feat/harness-v2`).

Cast per DEC-0059/DEC-0063: Opus is the implementer floor, Opus verifies; Fable ONLY for the design
pass of stream A (phase 1), the build is a second Opus spawn.

| Stream | Item | Primary FR + grouped | Worktree (branch) | Tier | Reserved H | Owns (files; the item is the authority) |
|---|---|---|---|---|---|---|
| A Board & Plan | TSK-0115 | FR-0075 + FR-0079 + FR-0080 | v2-testbed/_worktrees/g3-board (g3/board) | Fable design pass -> Opus build | H126-H128 | dev-team generate_dashboard.py + template, kernel/board.py, kernel/backlog_tree.py, (new) kernel/plan_diagram.py |
| B Buero-Finanzen | TSK-0116 | FR-0076 + gen-2 office seams + H125 | _worktrees/g3-office (g3/office) | Opus | H129-H131 | office templates/project_memory/**, templates/repo/**, hooks/guard_fs_tripwire.py, kernel/filing.py |
| C Freigaben & Beweismittel | TSK-0117 | FR-0074 + FR-0082 + FR-0083 + BUG-0089 | _worktrees/g3-approvals (g3/approvals) | Opus | H132-H134 | kernel/** minus A's and B's files, */hooks/gate_approval.py, */hooks/gate_git.py |
| D Parallele Spezialisten | TSK-0118 | FR-0021 (+ N2 auditor description) | _worktrees/g3-parallel (g3/parallel) | Opus | H135-H137 | */constitution/**, */skills/project-manager/**, office-manager skill, (new) dev-team skills/parallel-streams/**, */agents/project-manager.md + project-auditor.md |
| E Design-Gates | TSK-0119 | FR-0077 + FR-0078 | _worktrees/g3-design (g3/design) | Opus | H138-H140 | dev-team hooks/gate_design_*.py, ENFORCEMENT.md, settings/settings.json, templates/repo/scripts/kit_*.py, skills frontend-design / product-designer / webapp-testing |

All streams: `tools/**` and `docs/**` shared by ownership of NEW files and reserved hole numbers; the
hole list, `tools/test_hooks.py` (mirror-dir tests, A x B) and the three constitutions (D writes, B/C/E
report sentences) are SEAMS applied in the merge round. Handover per stream:
`_round-scratch/TSK-01nn/stream-<name>.patch` + protocol in `project_memory/staging/TSK-01nn/`.

Seams named at cut time (DEC-0062 (5)) -- an unnamed collision in the merge is a finding against this cut:

| Seam | Streams | Arbiter / apply order |
|---|---|---|
| MST type lines in `kernel/backlog_types.py` | A recommends, USER decides (DEC), C applies | A phase-1 report -> lead asks user -> DEC captured -> C receives lines via the lead; if FIELD or no DEC before C's handover: not built, protocol says so |
| Board/diagram trigger call site (`kernel/cli.py` generate-index) | A needs, C owns | one line, verbatim in A's protocol, applied in the merge (or by C if delivered via the lead) |
| `kernel/filing.py` retention validation entry point (F6) | B builds, `report.py` is C's | one call line, verbatim in B's protocol, applied in the merge |
| Constitution / role / skill sentences | B, C, E report; D owns | written in the MERGE, not by D during the round (D's protocol carries "received: none; expected at merge: B, C, E") |
| Leases/dispatch requirements for parallel specialists | D lists, C owns kernel/hooks | built by C only if D delivers a concrete requirement + test through the lead; else "not built" in both protocols |
| `tools/test_hooks.py` mirror-dir tests | A, B (new shipped scripts) | merge round; no dir is new in either stream, so expected empty |
| `docs/POST_V2_WISHLIST.md` | all five | reserved numbers only; appended entries re-ordered in the merge by number |
| `team-kits/*/VERSION` | all five | provisional per stream; dropped from every patch; ONE stamp in the merge |

Rules from DEC-0063 carried in every order: measure every new property claim before handover; hole
citations with module prefix; scratch only under `_round-scratch/<TSK>/`; verifier copies WITHOUT
the worktree's `.git` file; streams run only their DEC-0050 affected suites (full suite = merge);
provisional stamp; every plan names the alternative it rejected in one line (FR-0084 shape).

(g) table to fill per stream (DEC-0060/DEC-0062 (3): does the cap hold?): first-report wall-clock,
verifier first-pass findings (B/M/N), rework rounds, tier, tokens.

## Log

- 2026-09-03 07:0x Session start on e45c0ca. User answers: five streams yes; FR-0084 -> gen 4; four
  approvals yes; push yes. Push done. APR-0001..0004 minted one question at a time (the mint gate
  takes exactly one approval question per AskUserQuestion; a second pending request for BUG-0083 was
  created by re-issuing the question -- the older one, 68b1aa0e, expires unanswered and is swept
  later). BUG-0083..0086 -> APPROVED -> FIXED -> VERIFIED (EVD-0079: the 12 tests whose docstrings
  name them, selected by ast, 12 passed in 36.85 s, artifact under staging/TSK-0114/).
- 2026-09-03 07:1x Gate-1 note for the record (measured, four refusals and three passing probes):
  a shell loop whose body STARTS with the kernel line -- `for b in ...; do PYTHONPATH=team-kits
  python -B -m kernel.cli ...; done` -- is refused as a write on `team-kits`: `do` is a verb the
  reader cannot classify, so the stage is scanned as writing and `PYTHONPATH=team-kits` is its first
  operand. The same loop with `do echo ...;` in front passed (the `echo` stage is read-only), and so
  did every kernel line on its own. My first reading blamed the `..` in `BUG-0083..0086`; the
  probes on `validate` refuted that. Over-refusal, not a hole; one kernel line per command from
  here on.
- 2026-09-03 07:2x TSK-0115..0119 created through the kernel by
  `staging/generation-3/create_tasks.py` (argument lists -- a shell line of that length broke on
  quoting twice), set READY; five worktrees at e45c0ca; this logbook opened.
- 2026-09-03 07:3x **Spawned all five**: A phase 1 (Fable, design pass only -- stops with the MST
  proposal and the board-vs-generator measurement), B, C, D, E (Opus). Orders generated from the
  items: each prompt carries the item id, role, worktree, scratch path and the item's
  allowed/forbidden/required/expected fields verbatim. C told to hand the FR-0074 DEC proposal to
  the lead FIRST and build the independent parts (FR-0082, BUG-0089, FR-0083) meanwhile; D told to
  report its kernel/hook requirements EARLY so C can still take them.
- 2026-09-03 07:4x BUG-0083..0086 stay FIXED, not VERIFIED, and honestly so: EVD-0079 is a passing
  `test` run recorded with `run_scope: selection`, and `report._delivery_evidence` drops every
  passing selection (DEC-0061), which `_assert_confirmed` also reads for the BUG confirming edge --
  while the kernel's own refusal text asks for exactly such a targeted regression run. Contradiction
  captured as a BUG (kernel territory; candidate for the gen-3 merge round or gen 4), not gamed by
  re-recording the same run without its scope. -> BUG-0090 OPEN.
- 2026-09-03 08:1x **Stream A phase 1 (Fable) reported after 48 min, ~430 k tokens, 144 tool uses.**
  Package under staging/TSK-0115/ (README, 01-05, mst-decision-proposal.md, parity.md,
  user-feedback.md, four mockups, 69 + 3 sighted PNGs, render.json errors: []). Parity MEASURED
  (parity.py, both generators on a copy of this repo, 284 items): every sum equal; divergences only in
  the missing-status label, the timestamp of two triggers, and the archive count under a planted
  foreign yaml (dashboard counts files, kernel counts ids). Recommendation: ONE renderer
  (kernel/board.py) with two outputs, generate_dashboard.py renders no items any more -- lead adopts
  unless the user objects. MST proposal: TYPE (PLANNED -> REACHED; MISSED/DROPPED; title, due,
  derives_from = roots), cost list per kernel line with the tripwire that goes red for each (C seam
  lines verbatim in the proposal; hook ITEM_TYPES x3 + templates x3 + constitution x3 named as merge/D
  seams). FR-0080: plan grid + mindmap from the same entries as the board, SVG + mxfile in one pass,
  hand edit detected via data-source-digest; trigger = one seam line in state._write_board (C-owned).
  Found while sighting: first draft German-labelled -> DEC-0049 says board English -> turned. Seven
  questions to the user in user-feedback.md; (g) row A-1: Fable, 48 min, 0 rework (design pass).
  No kit file, no stamp, worktree clean. Next: user answers -> DEC for FR-0079 -> phase 2 (Opus).
- 2026-09-03 08:2x USER answers on stream A: MST = TYPE -> **DEC-0064 VALID** (kernel lines = seam to C,
  hook/template/constitution lines = merge seams); diagrams in generated/ beside the board; records
  collapsed with a count; direction "T-card plan board" accepted in structure, but the LOOK reads as a
  copy of the finance dashboard (TSK-0109) -> the user wants it re-thought and re-tokenised through the
  frontend-design skill. -> **DEC-0065 VALID** (one renderer with two outputs; generated/ diagrams;
  records collapsed; three numbers; READY = in flight; English per DEC-0049; a second SHORT Fable
  design pass on tokens/visual identity with IA, data contract and rig kept, user picks a direction,
  phase 2 after the pick). The stale duplicate approval request for BUG-0083 (68b1aa0e) expires
  2026-09-04 04:06 -- until then every AskUserQuestion answer prints the "no approval minted" note;
  it is not re-asked (BUG-0083 is APPROVED already).
- 2026-09-03 08:3x User picks "three directions to choose from" for the restyle. Stream A phase 1b
  sent to the SAME Fable agent (context kept, DEC-0063 (6)): three visibly different visual
  directions, tokens only, IA/rig/measurements kept, sighted under review/directions/, distance to
  the TSK-0109 tokens measured and named, AI-default look avoided; user picks, then phase 2 (Opus).
  MST seam handed to stream C (message: DEC-0064 + the proposal table; kernel lines to build in
  backlog_types/state, VIEWS stays A's, hooks/templates/constitution = merge seams).
- 2026-09-03 08:3x **Stream A phase 1b reported** (Fable, 11 min, ~80 k; both phases 07:22-08:35,
  ~510 k): three directions A Werkstatt / B Blueprint / C Leitsystem as three token sheets over the
  SAME markup (`make_mockups.py --style a|b|c`), 27 sighted PNGs under review/directions/, contrast
  measured (all pairs >= 4.5 after three sighting rounds fixed four legibility defects), distance to
  TSK-0109 measured at seven tokens and every one changed per direction, no radius/shadow/gradient/
  pill anywhere. Recommendation A; user asked to pick. (g) row A-1b: Fable, 11 min, 0 rework.
- 2026-09-03 08:4x USER on the three directions: likes C's strong colour signalling, none hits his
  taste, "wirkt alles bisschen retro, ich will's modern haben". Phase 1c sent to the same Fable agent:
  two MODERN variants D/E (contemporary product UI, geometric sans, whitespace, flat strong colour as
  signal, real dark mode), no material metaphors, still not the AI-default look and not the TSK-0109
  tokens; the design task named explicitly = the line between "modern" and "AI default", stated in
  07-modern.md in three sentences. Taste round 2 -- recorded for the (g) table (design passes that
  end at the user's taste are a cost class of their own; FR-0074 keeps taste with the user).
- 2026-09-03 09:0x **Stream A phase 1c reported** (Fable, 14 min, ~60 k; all phases 07:22-09:04,
  ~570 k): D (4 px edge bar, neutral surfaces) and E (coloured surfaces, tinted cards) over shared
  modern tokens (Segoe UI Variable/Inter stack, no monospace, no click accent, signal colours red/
  amber/teal, radius 4, no shadow/gradient/pill, real dark mode); the modern-vs-AI-default line stated
  in three sentences in 07-modern.md; contrast measured (E white-on-red 4.8 is the tightest); 18 PNGs;
  three sighting rounds fixed two inherited-style defects. Three of seven tokens stay class-equal to
  TSK-0109 by the brief (text family, light neutral ground, dark ink) -- named. Recommendation E.
- 2026-09-03 09:1x USER: **E chosen** ("gefällt mir eigentlich ganz gut"), four flaws to fix before
  the build: full window width instead of a left-aligned block with empty right margin; cards must
  not overlap; collapsible hierarchies in the backlog; the milestone/Gantt tab is missing from D/E
  (phase 1 had it as mockup-timeline.html; 1b/1c rendered only the blocked state -- a gap of the
  brief, not the idea). Plus a fundamental question outside the dashboard: why are some FRs
  "unassigned" -- answered measured below. Phase 1d sent to the same Fable agent: E over all states
  incl. timeline at 1280/1920/390, overlap measured by bounding boxes, collapse as a pure state
  function with keyboard path, 08-final.md + 03-tokens-final.md + 04-build-spec.md updated so phase 2
  builds without questions.
- 2026-09-03 09:1x "Why are some FRs unassigned?" MEASURED: 14 of 35 active FRs carry no related_pr
  (FR-0019/0020/0021/0022/0023/0024/0025/0033/0043/0047/0048/0057/0058/0064), so backlog_tree cannot
  hang them under a root -> Unassigned. The FR contract does not require the field; this repo's three
  PRs are coarse; nobody filed the wishes under one. A bookkeeping gap of this repo, made visible by
  the board (its job). Proposed to the user: `update` each to related_pr PR-0003 through the kernel;
  awaiting his word.
- 2026-09-03 09:5x **Stream D first report** (Opus, spawn 07:3x -> 09:5x = ~2 h 17, ~380 k tokens,
  203 tool uses). Cut-deciding measurement first: `python .claude/skills/parallel-streams/<script>`
  is rc 2 under the shipped gate_write_scope (names the enforcement layer) -> a check script in the
  skill dir is not startable in a customer project -> H136; the check became a workshop tool
  (`tools/check_scope_overlap.py`, imports `gate_write_scope._matches`, two universes: real files +
  one witness per scope entry, `--seam` subtracts declared seams) and the executable route a
  requirement to C. Built: dev skill parallel-streams (+ a byte-identical research copy, DEMANDED by
  the shipped reference-skill contract -- deviation from the item, reported), one constitution
  paragraph byte-identical x3 (cap stated as a property, not the 4-5 of DEC-0063), lead-skill lines
  x3, N2 closed red-first (cadence words out of three auditor descriptions + office role line),
  tools/test_parallel_streams.py 22 tests, 16 mutations red in a copy outside. Measured on THIS
  generation's five items: 10/10 pairs overlap on docs/**, tools/**, team-kits/*/VERSION; with
  --seam of exactly those three: 0/10 -- the seam lives in a markdown file no program reads = the
  measurement behind requirement C-4. Requirements to C: C-1 kernel verb check-scopes, C-2 refusal on
  overlapping scope in create_lease, C-3 worktree field on the lease, C-4 seam_scope item field.
  Residues H135 (witness half is a sample), H136, H137 (_routine.py docstring claims a weekly cadence
  no constitution states any more; forbidden, mirrored x3). Own finding before the verifier: one
  cited test name did not resolve -> fixed; test_hooks_v2 full run found the checker writing
  bytecode into the kit tree + rc 1 on an empty root -> fixed red-first, reading suite re-run FULL.
  Suites: 22 / 129 / 18 / 86 / 115 / 902 / 2137 / gate suite 489 full; provisional stamps dev -1,
  office -2, research -1 (2026.09.03). Patch 18 files +1160/-17. Verifier (Opus) spawned; C-1..C-4
  forwarded to C with the cap caveat.
- 2026-09-03 10:0x USER: "wir muessen die Ursache bekaempfen -- ausser es ist so vorgesehen; ist das
  bei den Kits auch so?" MEASURED against the kits: FR = inbox (constitution section 4, PM skill step
  3, backlog_tree NO_LINK "breaks no rule"); unassigned is normal there but TRANSIENT. This repo
  deviates: 21/119 TSKs hang from an FR, 49 archived FRs of which 10 CONVERTED, 14 active without a
  root. Root cause = the lead skipped wish-to-goal; the kernel let it pass -> **BUG-0091 OPEN**
  (create-task accepts an FR as product_requirement/derives_from). User chose "apply the kit rule
  here too" -> **DEC-0066**: 14 FRs get related_pr PR-0003 through the kernel now; FR-0021/0023/0024/
  0025 CONVERTED to PRs from gen 4; BUG-0091 to the merge round or gen 4; board wording for a root-less
  FR = inbox language (PHASE-2 LINE FOR STREAM A, board.py). Not a cosmetic fix: it is the state the
  kits prescribe for a wish about an existing goal.
- 2026-09-03 10:1x USER asks whether one TSK may work several PRs under the bundling workflow. Lead
  answer from DEC-0062/0066 + kernel contract: no -- a TSK has ONE product_requirement; DEC-0062 (2)
  bundled at TSK level with the secondary FRs in prose fields (a stop-gap the board cannot see); the
  kit-native place for the bundle is the PR (triage MERGES wishes into one goal) -> from gen 4:
  streams cut by file ownership as PRs, one TSK per PR. Proposed as a DEC-0062 amendment; user's
  word pending. Verifier of D asked to check that D's kit text bundles at the right level.
- 2026-09-03 10:0x **Stream A phase 1d reported** (Fable, 16 min, ~105 k; all phases 07:22-09:56,
  ~690 k, 0 reworks by a verifier -- four user taste rounds instead): E final over four states at
  1280/1920/390 x light/dark, 101 PNGs, layout MEASURED by bounding boxes (before: 110 overlapping
  pairs at 1280 and 1920, 333 at 390, right margin 115/752 px empty; cause `all: unset` resetting
  box-sizing + flex basis in column layout; after: 0/0/0 px on all pages); collapse = native button
  with aria-expanded, roots open, depth >= 1 closed, keyboard path sighted, noscript shows all;
  timeline in E with a three-band ruler (today alone on top), 0 overlaps; 03-tokens-final.md +
  04-build-spec.md section 0/5 = the build contract. Phase 2 (Opus) spawned.
- 2026-09-03 10:2x USER: "Ja halte fest und definitiv einbauen" (bundle at PR level; parallel +
  bundled work saves time) + "wieso wird nicht zwangsweise ein SR daraus?" -> **DEC-0067 VALID**
  (amendment to DEC-0062: a stream = one PR cut by file ownership, wishes merged at triage, one TSK
  per PR; DEC-0062 (2) retired for new work; kits get it through D/FR-0021; D's first report bundled
  after the stop-gap -> rework line, not a new stream). SR question MEASURED: procedure only (PM skill
  step 5 hands the PR to the architect), no gate reads it, TSK derives from PR not SR, 8 SRs vs 95
  PR-tasks here -> **FR-0085 OPEN** (SR duty keyed on PR class, enforced at dispatch; gen 4). D's
  verifier told to measure the bundling level of D's kit text (M-class finding if it copies the
  stop-gap; not against the implementer).
- 2026-09-03 10:2x **Stream B first report** (Opus, spawn 07:3x -> 10:2x = ~2 h 20 wall, ~460 k
  tokens, 244 tool uses; ~50 min of it three full hook/gate runs where DEC-0050 wanted one -- named
  by the implementer). FR-0076: shipped vocabulary 15 categories with euer_line as NUMBER +
  euer_line_label + euer_form {year, source, gwg_limit_net} (no line number, no year in code);
  euer_report.by_form_line shared by report and dashboard (parity measured on a generated report);
  AfA hint from the vocabulary limit, red twice (hint removed; limit as constant 800), user lever
  afa_hint false found by measuring six false positives in the regular fixture. Gen-2 seams:
  kleinunternehmer null + interview question as template comment; founding_year ADDED because a
  reader now exists (finance_dashboard.threshold previous_unknown -> current_exceeded measured on a
  fixture); F6 kernel/filing.py retention_span/retention_refusal, two readers agree over a corpus;
  filing_plan --draft placeholder made recognisable. H125 CLOSED: WHERE as a definition (reach of a
  destruction hits a tray of record), WHAT still a stem list read over every word; measured as
  processes against all eight office hooks HEAD vs now: unlink / git clean -fdx (with and without
  path) / Clear-Content / find -delete / tar --remove-files ALLOW -> rc 2; controls unchanged; git
  clean in a project WITHOUT archive stays ALLOW (the over-refusal weighing); slowest hook 0.446 s;
  NOTE: none of the eight office registrations carries a timeout (FR-0057, gen 4 -- confirmed
  measured). H123 narrowed to the target-deleting flag class (robocopy /MIR, rsync --delete).
  Residues H129 (WHAT half stays a list: python -c os.remove rc 0 through all eight), H130
  (retention null unreachable via add-filing-rule -> approvals.py seam to C), H131 (line numbers from
  public guides, not the official form -- year + source printed beside every sum). No sighting of the
  two new EUeR tables (DOM only) -- merge/design round to look at 390. Seams S1-S3 -> D, S4-S6 -> C,
  S7 tools/test_hooks.py with A, S8 user/CLAUDE.md -> lead. One red gate test = BUG-0033 (gate 3
  wall-time under load, measured red on the clean main repo too). Stamps office -4, dev/research -1.
  Patch 19 files / 2419 lines. Verifier (Opus) spawned.
- 2026-09-03 10:1x **Stream D verifier: FAIL, B 1 / M 5 / N 3** (Opus, 27 min, ~210 k; own dev-team
  pilot scaffolded against a redirected store). B1 `tools/check_scope_overlap.py` imports
  `gate_write_scope._matches` but not `_norm` (case fold) -> `Tools/**` vs `tools/**` rc 0 while the
  hook lets both write `tools/foo.py` (false negative; fix measured: wrap both sides in `_norm`, 3
  lines + one red case). M1 the kit text bundles at ORDER level ("requirements whose file lists
  overlap go into ONE order") in eight places -- DEC-0067 (3) rework, explicitly NOT against the
  implementer. M2 the cap axis "how many streams at once" (DEC-0063 (2), "cap by one round's
  attention") is absent; the text caps order SIZE; protocol :171 claims otherwise. M3 `_CADENCE_IN_PROSE`
  is an adverb list -- `runs once a week` / `on Mondays` pass (docstring names a narrower limit). M4
  every path with fewer than two orders ends rc 0 incl. a typo in --root/--only. M5 a `--seam` as
  wide as the scope turns a real collision into "seam only", rc 0. N1 protocol misnames the name
  checker; N2 patch drops VERSION (expected by DEC-0057 (d), but the item says worktree diff -- merge
  round must stamp); N3 skill text omits the case fold. Measured negatives: H136 holds over the CLASS
  (six spellings rc 2 on the pilot, controls rc 0); no shipped refusal of overlapping scopes
  (create_lease AND gate_dispatch as process); constitution paragraph x3 falls on V1/V2/V3; skill
  copies enforced; N2 test red on one file; hole list H135-H137 tripwires red; 285 backtick names
  resolve; patch applies to e45c0ca; counts match collect-only. **Findings against the CUT (lead):**
  (i) TSK-0118's allowed_scope was unfulfillable under the shipped reference-skill contract (research
  copy demanded) -- accepted as the named deviation; (ii) the cut now has SIX open orders: TSK-0088
  (DRAFT since August, scope team-kits/**) overlaps every stream -> lead cancels it, BUG-0069 stays
  open. Rework sent to the same D implementer: B1, M1 (eight places, PR level), M2, N3, N1; M3/M4/M5
  as hole entries -- D's H135-H137 are used, so **H141-H143 reserved for D** (E keeps H138-H140).
- 2026-09-03 10:5x **Stream B verifier: FAIL, B 2 / M 2 / N 6** (Opus, 1 h 05, ~220 k; two own
  pilots, eight office hooks as processes, nothing destructive executed except `git clean -n`). B1
  `guard_fs_tripwire.py:574/:362` reads reach only as "operand UNDER a tray", never "tray under the
  operand": `git clean -fdx` rc 2 but `git clean -fdx .` / `./` / `-e docs`, `rm -rf .`, `find .
  -delete`, `Remove-Item -Recurse -Force .`, `shred .` all rc 0 through all eight hooks (git clean -ndx
  proves the dot form removes archive/ identically) -- and the rc-2 refusal text tells the caller to
  "run the destruction with the paths it should really touch" = the bypass as instruction. B2 H125
  stands CLOSED while B1 is open. M1 `sweeps_a_tray` answers "does the project have a tray" not "is
  one under the cwd" (`cd docs && git clean -fdx` rc 2 = over-refusal; the named test does not test
  its own name). M2 the two-reader retention equality test compares 16 samples, not the definitions
  (`_SPAN_RX + "|jahren"` in one reader stays green = the F6 drift it exists for). N1 protocol claims
  guard_fs_tripwire is in KIT_SPECIFIC_HOOKS (it is not; not needed). N2 `clc` (alias of Clear-Content)
  rc 0 while `ri` is a stem; `sc`/`Out-File`/`dd` rc 0 (H129 mechanism, but the limit sentence
  overclaims). N3 dashboard vocabulary reader dies on a non-mapping entry (AttributeError, no page)
  now that the template invites RENAME AND ADD FREELY. N4 unit list of retention (`10 Jahren`, `10`,
  `6 Monate` refused with remedy). N5 "nothing for a GmbH" is prose, not a branch (implementer's
  stated decision; merge-round call). N6 slowest hook 0.899 s not 0.446; BUG-0033 gate test red solo
  on the clean repo (4.54 vs 4.5). Per FR: (1)(2)(3) fulfilled and measured (parity is DOM vs process
  report, three mutations red); kleinunternehmer/founding_year fulfilled; F6 built with M2 as the
  hole in its guard; H125 NOT closed. Rework sent to the same B implementer; **H144 reserved for B**
  (the ancestor class if B1 cannot be fully closed).
- 2026-09-03 11:0x **Stream C first report** (Opus, spawn 07:3x -> 10:5x = ~3 h 20 wall incl. two
  mid-round seams, ~540 k tokens, 344 tool uses). Both seams received and built: MST kernel lines
  (automaton, dir, fields, date check; FOUND on the way: `state._AUTOMATON_TYPES` was a hand-written
  tuple beside AUTOMATA -- an eleventh type landed WITHOUT a status field and nothing fired; now
  `frozenset(AUTOMATA)`), C-1 `kernel/scopes.py` + verb `check-scopes` (imports gate_write_scope._matches;
  measured through the shipped scripts/harness.py: TSK-0115..0119 -> 10 overlapping pairs rc 2, with
  --seam docs/** tools/** team-kits/*/VERSION rc 0) and C-4 `seam_scope` item field (subtracted only
  when BOTH orders declare it); C-2/C-3 NOT built (would redden two D tests + D-owned texts; named).
  FR-0074: dec-plan-approval.json ready since 07:34 (four ways with cost; recommendation B = own
  approval kind `plan`; measured context: one product goal costs THREE user approvals today, ten
  goals = 30 questions from the automaton alone); no user decision before handover -> the
  recommendation is BUILT (plan manifest = goal list with scope hash per goal; one question walks
  every goal APPROVED with the same approval_ref, IN_DELIVERY still asks, a moved goal is asked again).
  FR-0082 blocked + sentence duty + gate_git as process; FR-0083 minted_via derived from the route,
  second route kernel/sdk_approval.py, IRREVERSIBLE_KINDS refused to a program, gate_git refuses a
  merge over a programmatic mint; BUG-0089 remedy from AUTOMATA (replanning_route), no READY->DRAFT
  edge. 20 red-first measurements R1-R22; two own claims measured and withdrawn (a test asking the
  function instead of the stored field; "kernel refuses capture without the seam_scope contract" --
  it does not). H132-H134 written. Seam sentences for D in protocol section 6 (four constitution/PM
  paragraphs + one QA-skill paragraph on --result blocked). **Red left in forbidden scope (all
  measured = merge seams):** test_board VIEWS (A), test_hooks no_adhoc ITEM_TYPES + dashboard_views +
  test_hooks_v2 id_prefixes (MST hooks x3), test_hooks evidence-kind wording in 5 SKILL.md (D),
  command-surface span in 3 constitutions + README (`check-scopes` line, D/merge), repo_hygiene
  decision pointer red only because DEC-0064.yaml is absent in the worktree checkout. Suites 3203/13/5
  (33:48), 548/1, gate suite 489 full (21:01); stamp -4. Verifier (Opus) spawned; FR-0074 DEC put to
  the user.
- 2026-09-03 11:1x USER chooses **B (plan approval kind)** for FR-0074 -> DEC captured from C's
  proposal (user pick recorded in title/context). C's build IS the decided shape; no rebuild.
- 2026-09-03 11:1x **Stream E first report** (Opus, spawn 07:3x -> 11:0x = ~3 h 30 wall, ~1 h 20 of
  it suite runtime -- 14 suites in one 50-min run, DEC-0050 says affected suites only; ~352 k tokens).
  ONE place, NO new gate: the checkable halves (contrast, keyboard path, reduced motion, focus
  visibility by PIXEL comparison -- computed styles measured to miss `outline:none` + offset shift --,
  colour literals, and FR-0078 exactly-one-primary-action per declared view) run in the shipped
  `templates/repo/scripts/kit_design_render.py` on the RENDERED DSN draft, exit 3 = findings; rejected
  way named (browser_smoke in kit_browser_checks.py: byte-mirrored to research-team = forbidden, and
  its subject needs npm + vite). Reasons for script-not-hook: DEC-0056 (b) no gate without a measured
  error class; a browser-starting hook has no child deadline; the draft is the contract. Zero new
  registrations (the auftrag sentence "every new registration carries a timeout" contradicts
  `test_a_registration_names_a_window_exactly_when_its_gate_can_outlive_the_default` -- resolved by
  adding none; settings.json 0 lines diff). Cost without UI 0.078 vs 0.074 s (returns before the
  Playwright import); +0.27 s per draft. tools/test_design_conformance.py 20 tests, 10 mutations red.
  Seam sentences for D: product-designer.md (exit codes 0/2/3) and PM skill step (b); constitution:
  none. Residues H138 (findings refuse nothing), H139 (BUILD half C1-C3 in browser_smoke + B3 not
  built -- **finding against the CUT:** allowed kit_browser_checks.py vs forbidden research-team/**
  mirror, not named as a seam), H140 (only declared views; contrast over image/gradient NOT
  DECIDABLE). No axe run (kit ships no npm file); frontend-design/webapp-testing untouched (Apache-2.0
  foreign texts, [MOD-4]). Suites 3366/14 (49:57), gate suite 488/1 = BUG-0033 (red on clean main
  too, 4.5023 s). Stamp -3. .audit/hook_events.jsonl in the worktree carries two lines from hook
  processes (not in patch; merge discards). Verifier (Opus) spawned.
- 2026-09-03 12:0x **Stream D rework 1 reported** (Opus, 1 h 55 wall, ~50 min suite runtime -- ran
  test_hooks_v2 AND test_hooks in full again although only text/contract suites read the change:
  DEC-0050 process note for the (g) table; ~85 k tokens, round total ~465 k). B1 matcher wraps both
  sides in `_norm` (Tools/** vs tools/** rc 0 -> rc 2), red test added; N3 in the skill. M1 all eight
  places on PR level per DEC-0067 (11 pointers), the shared paragraph kit-neutral "goal" because the
  three kits have different root types (PR/RQ/none -- office names PROC), lead skills name their own
  type; §2 says the pre-dispatch check runs over the orders of those goals. M2 both caps as
  properties without a number. M3 -> H141 (+ five blind forms as test lines, docstring on the real
  class). M4 BUILT: what the caller NAMED must resolve (rc 1), what nobody named stays rc 0 (the
  argument-less run of the bytecode test needs it) -> rest H142. M5 BUILT in a different form than
  proposed: a seam that leaves one order NO ownership is refused (the proposed "covers a whole
  allowed_scope entry" would have refused the legitimate team-kits/*/VERSION seam) -> rest H143;
  generation-3 cut with three seams still rc 0. N1 fixed (two checkers), N2 unchanged (named). 10 new
  mutations red + the 16 of round 1 re-run red; one dead pointer found by own check_refs and fixed.
  Suites 27 / 202 / 2 / 2137 / 902; stamps dev -2, office -3, research -2. Patch 18 files
  +1482/-17. Re-verify sent to the same D verifier.
- 2026-09-03 12:1x USER proposes a hook that blocks a 100 % test run during a round unless intended
  (delivery run), for this repo and the kits -> **FR-0086 OPEN** (grouped with FR-0057 for gen 4):
  property "the line names no selection" instead of a percentage; "intended" said on the line like
  gate 3 and recorded as the run_scope-full EVD the merge needs (DEC-0061); runners = the project's
  declared test command, not a name list; threshold a config value. Measured cost class named: TSK-0083
  4 h, today B/D/E ~50 min each.
- 2026-09-03 12:2x **Stream E verifier: FAIL, B 1 / M 5 / N 4** (Opus, ~75 min, ~200 k; own pilot,
  Chromium 149, everything as process). B1 `tools/test_design_conformance.py:351-353`: the
  "procedure instead of adjective" test is a substring window (4000 chars, words "sentence"/"first")
  -- the adjective mutation survives; negative slice when the section is early. M2 a stylesheet the
  document may not read is silently empty (literals missed, false "declares no :focus-visible rule");
  M3 focus visible = "PNG bytes differ" (white-on-white passes; the DEFINITION is the gap); M4
  pseudo-element text never judged, 0<opacity<1 computed opaque (false green); M5 SVG `fill=`
  literals pass, in the protocol without number/chain; M6 one mechanism: the probe reads the
  declarative light DOM. N7 stale sha256 in H139; N8 a draft without any [data-view] says nothing
  though the undecided channel exists; N9 suite list misses one; N10 item contradiction (forbidden
  project_memory/** vs staging exception) = against the CUT. Both deviations ACCEPTED (script not
  gate = fulfilled; BUILD half = cut finding, KIT_SPECIFIC_SCRIPTS argued away by H139 itself).
  Measured: patch/scope/stamp/mirror fine; no-UI cost with poisoned Playwright rc 2 in 0.10-0.13 s,
  import absent; H138 as process (renderer rc 3 -> gate rc 0; no kit reader pulls
  conformance.findings -- the PM sees the envelope rc only = the D seam); BUG-0033 solo on clean
  main: 1 passed in 27 s; the 14 suites were NOT a DEC-0050 violation (12 read a changed file) --
  lead suspicion withdrawn. Handback: DEC-0056 needs the USER's acceptance of H138 -> asked (user
  asked for an example first). Rework sent to E: B1, H145 (M2) + H146 (M4) reserved, M3/M5/M6 into
  H140 as mechanisms, N8 built, N7/N9 cleaned.
- 2026-09-03 12:3x **Stream C verifier: FAIL, B 2 / M 2 / N 7** (Opus, 2 h 20, ~300 k; 20/20 red
  mutations reproduced, four tripwires both ends). B1 `state.py:1281-1282` stamps the used approval
  onto the item after a gated edge; a plan APR has item None / revision None -> `report.validate_state`
  compares apr revision != item revision -> error -> `gate_memory_complete` blocks merge AND push
  after ONE plan approval (rc 0 -> rc 2 as process; the two lines removed -> rc 0); no test caught
  it; the printed remedy sends the role to cancel + archive the goals. Fix: validate_state asks
  `approvals.assert_apr_in_force` (the one definition of in force) instead of computing its own
  revision compare; test = the measured chain. B2 DEC-0068 claimed as MEASURED that a changed goal
  drops coverage for ALL goals -- measured false (per goal, `_assert_the_plan_covers`); the user
  chose on that cost sentence -> **lead corrected DEC-0068 through the kernel** (context B,
  consequences, plus N4: seven IRREVERSIBLE_KINDS not six, and analysis/routine/plan stay questions
  outside both sets). M1 `kernel/scopes.py` imports `_matches` without `_norm` (same class as D's B1;
  the head claims the property) -> `Tools/**` x `tools/**` reported disjoint through the shipped
  verb. M2 `state.py:830-836` date check skips None although the required-field loop refuses only
  ABSENT fields -> `due: None` stored on an MST. N1 `20260903` accepted (3.13 fromisoformat),
  unnormalised, version-dependent. N2 `H135`/`H136` cited from shipped kernel files exist only in
  D's worktree (merge seam not in the seam table; no H-pointer test exists). N3 `seam_scope ["**"]`
  turns any collision into "seam only" rc 0. N5 tests 31 not 26; N6 H132 closes pointing at the
  proposal, now DEC-0068; N7 worktree diff carries .audit (patch does not). Per FR: FR-0082 PASS
  (blocked selection still closes; BUG-0090 untouched), FR-0083 PASS (route not a parameter,
  smuggled field ignored, gate_git reads the record, 13/13 kinds agree; hook route forgeable from
  stdin = pre-existing H133), BUG-0089 PASS, MST pass but M2/N1, C-1/C-4 pass but M1/N3, FR-0074
  code right but B1. Question relay measured: 10 goals = 1000 chars verbatim rc 0, tampered rc 2,
  truncated loses the marker = mints nothing (fail-closed); a plan answer walks ZERO items, goals go
  through transition. Rework sent to C: B1, M1, M2, N1, N3 (**H147, H148 reserved for C**), N2 seam
  row, N5/N6/N7.
- 2026-09-03 12:4x USER accepts **H138** after an example (draft with contrast 2.1:1 and two primary
  buttons -> rc 3 in the envelope -> PM sends it back; nothing prevents freezing): "melden reicht
  vorerst" -- the DEC-0056 user acceptance of a named exception; falls the first time a draft with
  findings is built anyway. Written into the H138 entry by the E implementer (message sent).
  DEC-0068 corrected through the kernel (context B cost sentence = per-goal invalidation, measured;
  consequences; decision (3): seven IRREVERSIBLE_KINDS, analysis/routine/plan stay questions) --
  first attempt failed because the generator printed into the JSON body; second clean.
- 2026-09-03 12:5x **Stream B rework 1 reported** (Opus, 1 h 50 wall, ~65 min of it two closing runs
  incl. the gate suite in full -- DEC-0050 note; ~110 k tokens, round total ~570 k). B1 `swallows_a_tray`
  reads the second direction (a tray of record INSIDE what the operand names); root / cwd operand =
  the sweeping form, ONE reader (`WORKING_DIRECTORY`); `EXCLUDING_FLAGS` (-e/--exclude) do not narrow
  a sweep; refusal text no longer names a way around. Measured on a pilot, eight hooks as processes,
  HEAD / first cut / now: `git clean -fdx .` `./` `-e docs`, `rm -rf .`, `find . -delete`,
  `Remove-Item -Recurse -Force .` (Bash and PowerShell), `shred .`, `clc archive/...` all ALLOW ->
  ALLOW -> rc 2; controls unchanged; all ancestor forms rc 0 in a project without a tray. M1
  `where_it_runs` picks the DEEPEST reading (the order's "last of current" was measured wrong:
  reading_bases appends, _bases_after prepends) -> cwd=docs rc 0, `cd docs &&` rc 0, `cd archive &&`
  rc 2; NEW measured price named in the guard head and H125: `echo cd outbox ; rm -rf .` is ALLOW
  because `_bases_after` reads a cd inside an argument (no new number). B2 H125 stays CLOSED with
  the ancestor table; H144 unused. M2 the two-reader test compares compiled patterns and derives its
  corpus from BOTH readers' unit alternatives -- red in both directions. N1 fixed; N2 `clc` a stem,
  H129 says alias only when itself a stem, and the "empties by WRITING" class (Set-Content, sc,
  Out-File, dd of=) is not read at all (rc 0, named); N3 non-mapping vocabulary entry skipped like the
  report; N4 H130 lists the unit vocabulary; N6 own measurement 0.19-0.28 s, verifier's 0.899 s kept
  beside. 15/15 red-first; suites 1157/13 (17:38); gate suite 488/1 = BUG-0033. Stamps office -5,
  dev/research -2. Re-verify sent to the same B verifier.
- 2026-09-03 13:0x **Stream D re-verify: PASS** (Opus, 1 h 31, ~145 k; both verifications ~355 k;
  0 B / 0 M / 4 N). B1 measured over ELEVEN `_norm` classes hook-as-process vs checker: 11/11 agree,
  incl. the door's own dead spellings (`tools//sub/**`, `tools/./sub/**`) -- the checker mirrors the
  door, not a better door; half-folding mutation red too. M1 no residue of order-level bundling
  (grep null); office "ONE PROC at triage" MEASURED to hold (kernel captures a TSK on a PROC root and
  an FR with related_pr PROC; ROOT_TYPE_BY_KIT governs the entry seed only). M2 both caps, no number.
  M3 the five blind forms are MEASURING lines (teaching the reader one form reddens exactly its line).
  M4/M5 both ends measured; the verifier withdraws its own M5 proposal (it would have refused the
  `team-kits/*/VERSION` seam, literally one allowed_scope entry of TSK-0118). N4 dead pointer in
  protocol :251 (renamed test; check_refs does not read older protocol sections); N5 H142/H143 not
  cited in the module docstrings where the seam logic sits; N6 "All six" number in two places (five
  rows); N7 the one derivable kernel claim of the constitution paragraph ("a work order has exactly
  one goal") has no test though REQUIRED_FIELDS/field_elements make it measurable. (g) process
  finding: rework ran test_hooks_v2 + test_hooks in full (~31 min) for two reading tests. (g) row D:
  Opus, first report ~2 h 17, verifier first pass B1/M5/N3 -> PASS after one rework (1 h 55), tokens
  implementer ~465 k, verifier ~355 k, spawn -> PASS ~5 h 30 wall. Closing lines N4-N7 ordered to the
  D implementer (no re-verify; the merge verifier reads them). VERSION not in patch: merge stamps.
- 2026-09-03 13:1x **Stream D closed** (rework 2, 35 min, ~30 k; round total ~495 k): N4 historical
  name without backticks + check_refs reads the whole protocol (209 spans, one standing hit
  `test_strategy` = a YAML field, pre-existing); N5 H142/H143 cited in overlaps/ownership_left; N6
  no count; N7 `test_a_work_order_carries_exactly_one_product_requirement` (REQUIRED_FIELDS +
  PARENT_FIELDS + create_task refuses a list -- red-first R11), cited by the paragraph in three
  constitutions and the skill. Only reading suites run (28 / 2). Stamps dev -3, office -4, research
  -3 (provisional; not in patch). Patch 18 files +1537/-17 = **D's merge input**.
- 2026-09-03 13:2x **Stream C rework 1 reported** (Opus, ~1 h 10; round ~4 h 10, ~600 k). B1
  validate_state asks `approvals.assert_apr_in_force` (the one definition), gate_memory_complete rc 0
  before and after a plan approval as process, no tightening on real state (same 0 errors / 54
  warnings on a copy of this repo's store), red W1 on two tests incl. the counter-direction (a real
  out-of-band edit stays an error). M1 matcher folds both sides via `_norm`, `_shipped_halves()` for
  identity in the test, red W2. M2 presence instead of truthiness, `None` refused, red W3. N1
  `backlog_types.normalised_date` = one reader, capture STORES the normalised form; interpreter
  differences = **H147** with table; red W4. N3 `scopes.owns_anything_outside`: a seam is subtracted
  only if both orders still own something afterwards (`**` rc 2, docs-only pair rc 2, VERSION seam
  rc 0); the narrower rule not built because it would forbid the legitimate glob seam = **H148**;
  red W5 both ends. N2 seam row, N5 35 tests, N6 H132 -> DEC-0068, N7 named. **Own incident,
  reported by the implementer:** a mutation rig run from the wrong cwd wrote a mutation into the MAIN
  repo's team-kits/kernel/state.py; reverted by hand (no git restore), rig now refuses to run outside
  its own directory -- lead re-measured the main tree (see next entry). Suites 568/2 -> 185, hooks
  nodes 119/4 (the four known seam reds). Stamp -5. Patch 24 files +2756/-131. Re-verify sent to the
  same C verifier.
- 2026-09-03 13:3x Lead re-measured the main tree after C's stray write: content of
  team-kits/kernel/state.py = HEAD (git diff empty; validate.py passes) but the file now carries CRLF
  (1473 x, 89 147 B, sha e3dddbc2…) where HEAD and every sibling are LF (87 674 B, sha 525f31e4…) --
  invisible to git status, fatal to `git apply` in the merge round. Gate 1 keeps the lead out of
  team-kits; the C implementer ordered to restore the exact bytes (binary write of the HEAD blob, no
  git restore) and to report size / CRLF count / sha. Lesson for the (g) table and DEC-0057 (f): a
  red-first rig must refuse to run outside its own copy -- C built that refusal after the incident.
- 2026-09-03 13:3x C verifier addendum (first pass): its background run of test_hooks + test_hooks_v2
  finished after 47:43 -- 5 failed / 3037 passed / 13 skipped = 3055 collected; exactly the five
  seam reds named in C's protocol §5, no sixth. Verdict unchanged. (g) process note: the VERIFIER
  ran two full hook suites DEC-0050 does not ask of it -- fourth measurement of the class today
  (D rework, B rework, B verifier partially, C verifier); all four feed FR-0086.
- 2026-09-03 13:4x **Stream B re-verify: FAIL (bookkeeping only), B 2 / N 2** (Opus, 55 min, ~125 k;
  session ~345 k; own pilots rebuilt incl. a junction belege/ -> archive/). Repair CONFIRMED beyond
  the order: all eight lines rc 2, plus `cd docs && rm -rf ..`, `../..` from sub/deep, three absolute
  root spellings, `docs/..`; M1 both directions (cwd/cd docs rc 0, cd archive rc 2, `cd $D` rc 2
  fail-closed); over-refusal controls rc 0; eight red-first mutations incl. flags-only drift for M2.
  B3 H125 says CLOSED while three measured classes are unnamed: operands from a pipe/stdin (`ls
  archive | xargs rm -rf`, `find -print0 | xargs -0 rm -rf`, `gci -Recurse | Remove-Item` all rc 0 --
  the naming word has no operand on the line), a directory link onto a tray (`rm belege/.../invoice.pdf`
  rc 0 while the real path is rc 2; `_filing.position` normalises but does not resolve), and the
  glob ancestor form (`rm -rf *`, `./*`, `git clean -fdx *` rc 0; in the guard head, not in H125).
  Verifier owns the miss: reachable with the same pilot in round 1. B4 the cd-narrowing (`echo cd
  outbox ; rm -rf .` rc 0; class = any argument word `cd` in any stage, `grep -r cd outbox`, `ls cd
  outbox` too; quoted/printf/`$X`/archive stay rc 2) is an ACTIVE under-refusal created by this round
  and sits as a paragraph inside a CLOSED entry = the third state CLAUDE.md forbids -> H144 as its
  own open entry, or close it (smallest way: advance the sweep base only from cd invocations whose
  COMMAND WORD is cd). N7 `git clean -fdx -e archive` rc 2 = the one careful spelling is refused
  (cost: a correction, never a receipt) -- sentence in the EXCLUDING_FLAGS comment. N8 "slowest hook
  0.280 s" is the guard alone; over all eight 0.565 s. Gate suite 23 min for three 2-s nodes
  confirmed as the DEC-0050 class. Rework 2 (text, optional B4 close) sent to B.
- 2026-09-03 13:5x Main tree re-measured by the lead: team-kits/kernel/state.py = 87 674 B, 0 CRLF,
  sha 525f31e4… = the HEAD blob; `git status` over team-kits/tools/docs/.claude empty. C's stray
  write is fully undone.
- 2026-09-03 13:5x C implementer confirms the byte restore (binary write of the HEAD blob; cause =
  text-mode `open(path, "w")` in its rig translating \n to \r\n on Windows). Its byte sweep over the
  592 tracked files outside project_memory/: 0 content differences; **35 pre-existing files carry
  CRLF** (content identical to HEAD, mtimes 2026-06-27 .. 2026-09-02, before this session) -- incl.
  .gitignore, team-kits/registry.yaml, kernel/checkpoints.py, guard_yaml_valid.py x3, docs/reviews/*,
  templates. Not this round's; relevant to the MERGE ORDER (git apply against a CRLF working copy)
  and to BUG-0025 (.gitattributes eol). Merge implementer to check the 35 before applying.
- 2026-09-03 14:0x **Stream B rework 2 reported** (Opus, ~50 min, ~60 k; round total ~630 k). B4
  CLOSED, not filed: `moves_the_working_directory(tokens, base)` advances the sweep base only from an
  invocation whose COMMAND WORD is a directory change and whose target `_filing.directory_change`
  can compute; `read_the_line` keeps that base itself. Measured eight hooks HEAD / rework 1 / now:
  `echo cd outbox ; rm -rf .`, `grep -r cd outbox ; ...`, `ls cd outbox && ...`, `echo cd docs ; git
  clean -fdx` ALLOW/ALLOW/rc 2; controls rc 2; M1 both ways kept; `cd $DIR && rm -rf .` rc 2
  (unknowable move keeps the base). Red-first `test_a_word_that_only_LOOKS_like_a_cd_does_not_move_the_sweep`;
  H144 unused. B3 three classes measured (pipe/xargs x3, junction x2, glob x3), no small fix seen
  (each is its own build: pipeline reader, link resolver, glob expander); in H125 as a table, in
  the guard head's rest list, verdict "CLOSED for the named and the ancestor form; not covered:
  pipe, link, glob, and the vocabulary (H129)". N7 comment; N8 both numbers with what they measure
  (single hook 0.280 s / whole line over eight 1.276 s vs 60 s = 2.1 %). Runs: gate nodes 5 (1.6 s),
  hooks nodes 100 (56 s), red 2/2; stamp office -6. Re-verify 3 (text + B4 code) sent.
- 2026-09-03 14:1x **Stream A phase 2 reported** (Opus, ~4 h 30 wall, ~550 k, 187 tool uses). ONE
  renderer: kernel/board.py 776 -> 1667 lines (style E from 03-tokens-final.md: three-number strip,
  slots, edge cards with flag, records collapsed, collapsible trees with keyboard path, Timeline tab);
  generate_dashboard.py 423 -> 244 + template 351 -> 91 render no items (4946 B on the real state, no
  item id); new kernel/plan_diagram.py 402 lines. Measured: layout 4 pages x 3 widths x every tab =
  39 rows all 0 overlaps / 0 overflow / 0 px margin; 105 sighted PNGs, errors: [], 0 network requests
  (page.on("request")); diagram labels 97/95 with 0 overflows; CELL_BUDGET 240 (5000 items 0.084 s /
  162+246 KB vs 3.3+5.1 MB); CHAR_WIDTH 0.62 measured. 33 mutations red (FR-0075 20, FR-0079 6,
  FR-0080 7); own find: `test_every_cell_names_an_item_the_entries_hold` built its expectation with
  the function under test -> now derived from backlog_tree.arrange; two uncovered claims measured,
  one real defect (an open request on an archived item carried no machine-readable subject ->
  `data-request`). Seams verbatim in protocol §7: C backlog_types MST lines; C state.py one line
  `plan_diagram.render_all(entries)` (signature without state -- deviation named); C cli.py print two
  diagram paths; C approvals `open_requests(state, now)`; backlog_tree MST lines deliberately NOT
  written (suite red until C's lines land); the `now` seam falls away (`_clock` from generated_at).
  Residues H126 (expiry rule twice, two clocks: board 1 -> brief 0 -> board 1 -> after next write 0),
  H127 (a hand edit between two state writes is seen by nobody; diagrams have NO trigger today --
  said in the module head), H128 unused (archive-count candidate closed by DEC-0065 (1)).
  test_repo_hygiene decision-pointer red in the worktree only because DEC-0064/65/66 are uncommitted
  (measured). Suites 83 green + nine-suite batch 3321/3 -> two repaired (test_kernel pin 8->7,
  test_migrate onto backlog_tree.parents_of, test_disposition quote), one named. Stamp -3. Patch 16
  files +3003/-891. Verifier (Opus) spawned.
- 2026-09-03 14:3x **Stream B verify 3: FAIL, B 1** (Opus, 35 min, ~95 k; session ~440 k). B4 closed
  for the reported class and the command-word reader is fail-closed over pushd/Set-Location/sl/
  chdir/env/sudo/builtin/`cd -`/`cd ~`/`cd outbox/..`/subshell; the new test is two-sided; B3 text
  matches eight re-measured rows; H144 unused; N7/N8 fine. **B5** `moves_the_working_directory`
  :392-419 follows a cd that the shell never performs: `cd nichtda ; rm -rf .`, `cd docs2 ; rm -rf .`
  (typo = the DEC-0056 error form), `false && cd outbox ; rm -rf .`, `ls | cd outbox ; rm -rf .`,
  `cd outbox | rm -rf .`, `cd outbox & rm -rf .`, `cd .. ; rm -rf .` -> all rc 0 while `rm -rf .` is
  rc 2. One-line fix measured by the verifier: follow only if the computed target `isdir` -> the
  typo forms rc 2 with no cost to the counter-direction; the pipe/background/short-circuit forms
  need the invocation SEPARATOR that `_filing._walk` (forbidden _*.py) does not hand out -> seam to
  C/D + own entry **H144** + fourth row in the H125 "not covered" table (which claims completeness)
  + fourth point in the guard head. Pattern for the (g) table: each narrowing of the guard opened
  the next class (B1 -> M1 -> B4 -> B5); the verifier's "nothing left to measure after this" is
  the third such sentence. Rework 3 sent to B.
- 2026-09-03 14:4x **Stream B rework 3 reported** (Opus, ~40 min, ~45 k; round ~720 k). B5: the
  computed target must be a directory AND inside the project (`_filing.position(root, moved,
  WORKING_DIRECTORY)` -- the `cd ..` case: a base above the root would answer "no tray under it",
  false); `cd nichtda`, `cd docs2`, `cd ..` ALLOW -> rc 2; controls unchanged; red-first three times
  (whole revert + each half) on `test_a_directory_change_that_never_lands_does_not_move_the_sweep`.
  **H144 filed** (four forms where the target exists but the change does not act: `false && cd`,
  pipe into cd, cd into pipe, `cd outbox &`; need the invocation SEPARATOR `_filing._walk` does not
  hand out) + seam **S9** to C/D (fourth field `separator` from the INVOCATION_RX split, with the
  test the stream owes) + fourth guard-head point + fourth H125 row; the H125 table lead-in no longer
  claims completeness. Runs: 11 hooks nodes (7.7 s), 5 gate nodes, red 3/3; stamp office -7. Verify 4
  sent.
- 2026-09-03 15:0x **Stream B verify 4: PASS** (Opus, 30 min, ~85 k; session ~525 k; 0 B / 1 M /
  1 N). B5 closed in every direction reached: target as file, `../..`, neighbour project (position
  None -> rc 2), and the legit spellings (`outbox/`, `./outbox/`, quoted, OUTBOX case) keep rc 0;
  both halves of the fix red singly; H144 matches row by row; S9 concrete. M3 the link class is
  described only as a naming delete -- measured the same junction as cwd: `cd belege ; rm -rf .`
  rc 0 (whole tray, not one receipt); same class, H125 (b) + guard head + one table row. N9 the
  verdict sentence counts three classes over a four-row table. Verifier owns the miss again (said
  "nothing left" after round 3). (g) row B: Opus, first report ~2 h 20, verifier B2/M2/N6 -> rework
  1 (1 h 50) -> FAIL B2/N2 -> rework 2 (50 min) -> FAIL B1 -> rework 3 (40 min) -> PASS; four
  verifications (1 h 05 + 55 + 35 + 30); implementer ~720 k, verifier ~525 k; spawn -> PASS ~7 h 30
  wall. Closing lines M3/N9 ordered (no re-verify).
- 2026-09-03 15:2x **Stream B closed** (rework 4, 20 min, ~25 k; round total ~745 k): M3 measured on
  its own junction pilot (three cwd-link lines rc 0 HEAD and now; controls unchanged) -> sentence in
  H125 (b) + guard head + three table rows; N9 "four classes". Deviation from the lead's line "no
  stamp": the guard docstring IS kit code -- validate.py said "kit files changed but VERSION not
  bumped" -> office stamped **-8** (dev/research -2 unchanged); ten tripwire/sweep nodes green after
  the stamp. Patch 19 files / 2968 lines = **B's merge input**.
- 2026-09-03 15:3x **Stream A verifier: FAIL, B 2 / M 2 / N 7** (Opus, 52 min, ~295 k; 15 own
  mutations full-file red; independent counter over index.yaml + AUTOMATA matches the three numbers
  on the real state 0/1/72; page purity measured with page.on("request") + hostile fixtures; MST seam
  arbiter measured both ways; CELL_BUDGET 241 sentence; determinism under shuffled order; poisoned
  Playwright -> skip with reason, not green). B-1 `board.py:360-361` `open_requests` is the FIRST
  board reader of approvals/pending/ and lacks the module's own container rule and a try around
  strftime: `expires_at_epoch=99999999999` -> OSError, board NOT rebuilt on every state write (all
  disappears); alias bomb in `item:` of a 622-byte file -> 14.9 s, 470 MB. Unreachable through the
  kernel (TTL fixed), = the hand-file/corruption class the module is built against; neither closed
  nor named. Fix 3 lines + red test. B-2 `backlog_tree.py:247-248` comment names
  `test_every_reason_a_tree_can_refuse_an_item_is_one_a_store_can_produce` as holding
  `_REASON_LABELS` both ways -- it never reads it (dead entry survives the whole suite). M-1
  `overflow-wrap` only on `.card .title`; `.node-face` and `.focus-list .rec` grids with `auto`
  minimum GROW with a 74-char path title at 390 -> page-wide scrollbar; the round's overflow probe
  (`scrollWidth > clientWidth`) structurally cannot see a growing element (0/0 measured, scrollbar
  anyway). M-2 XML-1.0-forbidden chars (`\x00`) in a title make both diagrams not well-formed while
  `is_pristine` says pristine; harmless today (no trigger), live once seam §7.3 lands. N-1 stale
  stamp (-2 vs -3) and line count in the protocol; N-2 seam table names a PARENT_FIELDS schema line
  §7.1 says is derived; N-3 ruler docstring in the browser test claims no two labels share a band
  (code docstring correctly bounds it; four milestones within 0.66 % overlap 44x16); N-4
  generate_dashboard.py is copy-if-absent (not in repo_kit_owned.txt) -> DEC-0065 (1) holds for
  NEW installs until the PM updates; N-5 without JS the three figures are absent (noscript says so);
  N-6 disposition quote rewritten to prose to pass the citation test (honest, mechanism named);
  N-7 .audit written in the worktree by a hook test. FR-0079 accepted, FR-0080 accepted with M-2,
  FR-0075 not accepted (B-1, M-1). Rework sent to the A implementer; H128 free for M-1/M-2 if not
  closed, **H149 reserved for A** as a second number.
- 2026-09-03 15:5x **Stream E rework 1 reported** (Opus, 2 h 25 wall, ~1 h 10 of it the same 14
  suites (46:30) + gate suite (22:45) again -- DEC-0050 process note, fifth of the day; round ~5 h 55,
  ~430 k). B1 closed structurally: `_skill_section` cuts heading to heading (own two-way floor test),
  ONE source `RANKING_SENTENCE_TEMPLATE` in the module -- the refusal quotes it, the skill carries it
  as step 1 -- two couplings (template read from the module vs the skill section; template read from
  a real run's printed refusal vs the skill); the verifier's adjective mutation now red, section at
  file start green. H145 built (undecided with sheet.href; no false "declares no rule" once a sheet
  is unreadable), H146 built (cumulative ancestor opacity folded into alpha; ::before/::after via
  getComputedStyle(el, part)), M5 as a PROPERTY (an attribute counts when the browser accepts its
  NAME as a CSS property with that value: fill="#ff0000" rc 3, fill="var(--brand)" rc 0), N8
  undecided line, M3/M6 as mechanisms in H140 (+ el.onclick read); each with a red test. H138 entry
  = named exception accepted by the user 2026-09-03 with the example and the falling condition. N7
  sha line removed (no mirror), N9 listed. Own red in the gate suite = the summary row still said
  OPEN while the entry said accepted -- exactly the drift the judges-test guards; fixed. Gate-3 timing
  test green this run (BUG-0033 confirmed as load class). Cost re-measured: no UI no measurable
  difference; one draft +0.32 s; 603 elements / 242 focusable +9.88 s, capped by FOCUS_PIXEL_BUDGET
  = 120 with a spoken cap. Stamp -4. Patch 8 files +1431/-22. Re-verify sent to the same E verifier.
- 2026-09-03 16:1x **Stream A rework 1 reported** (Opus, ~1 h 30, ~120 k; reading suites only --
  first stream today to keep DEC-0050 in a rework). B-1 request fields go through `_flat` (depth +
  char budget of `_emit`), clock call caught -> the three hand-written request files (epoch out of
  range x2, 504-byte alias graph that produced a 107 MB page) all rebuild in 0.02 s / 35.5 KB; test
  compares against the same store without the file. B-2 both ends of `_REASON_LABELS` in the named
  test; comment says it did not for one round. M-1 measured which half carries: `overflow-wrap`
  alone (171 px -> 0), `min-width: 0` alone 0 px -> only the wrap rule shipped, the other named as
  measured and rejected; new test reads `documentElement.scrollWidth` (the old probe's blind spot);
  12 sighted long-title PNGs. M-2 `_clip` replaces XML-1.0-forbidden chars with U+FFFD -- and a
  SECOND own find: `digest_of` raised UnicodeEncodeError on a lone surrogate before any label ->
  same tolerance as `state._write_text_atomic`, consequence named. N-1..N-7 done (ruler limit
  re-measured: 3 ticks one day apart = 0 at 1280, 1 pair at 390; 4 ticks 2 pairs; both docstrings
  say so). 90 tests green (83 -> 90), 40/40 mutations red, stamp -4, patch 16 files +3259/-892.
  Re-verify sent to the same A verifier.
- 2026-09-03 16:3x **Stream E re-verify: FAIL without a round-blocking finding** (Opus, 50 min,
  ~95 k; ~295 k both). B1 CLOSED and cross-measured with five own mutations (adjective, decoy
  heading, wrapped template, constant changed, paraphrased refusal all red); remaining edge R2 (a
  section that quotes the template and then teaches the adjective as the operative step stays
  green) = the limit of any assurance over prose -> docstring sentence (N-3). M5 as a property
  clean over ten cases (fill/stroke/stop-color/flood-color/font color/svg style rc 3; var/
  currentColor/url/noise rc 0). New: B-1 (M) `kit_design_render.py:553` the H145 suppression is
  GLOBAL -- a draft with truly no :focus-visible rule loses the finding as soon as any sheet
  (print.css) is unreadable; fix = qualify the sentence, not suppress. B-2 (M) `:339-345`
  pseudo-element text nobody can see (display:none, visibility:hidden, opacity:0, empty content) gets
  contrast findings incl. "at opacity 0" -- the inverse of the suite's own no-invisible-text rule;
  fix = four conditions on the pseudo object + counter-direction test. N-1 keyboard refusal names
  cursor:pointer when onclick fired; N-2 H140 (1) still says "the check is silent" (N8 made it
  speak); N-3 docstring limit; N-5 summary row order. **Against the cut (lead):** N-4 the frozen
  item says "H138 to H140 ONLY" while H145/H146 were assigned by message -- reservations live in
  this logbook (READY items are frozen, BUG-0089); N-6 the H138 user acceptance existed only as
  prose -> **DEC-0069 captured**. Budget: first 120 focusable in DOCUMENT order, the rest spoken as
  NOT MEASURED (200 links + broken #late -> "82 not compared"); 120 in one place. DEC-0050: the 14
  suites are defensible (12 read a changed file), the SECOND full gate-suite run is not (22:45 for two
  reading tests = 6.7 s). BUG-0033 solo 1 passed in 14 s. Rework 2 (text + two small fixes) sent.
- 2026-09-03 16:5x USER on generation 4: "Ja die vier" (G4-1 test discipline & hook hygiene =
  FR-0086 + FR-0057 + S9/H144 + H139; G4-2 kernel contracts = BUG-0090 + BUG-0091 + FR-0085 +
  C-2/C-3; G4-3 procedure & retrospective = FR-0084 + FR-0005 + FR-0010; G4-4 repo hygiene =
  BUG-0069 + BUG-0025 + BUG-0088); the deliberately deferred items are THEIR OWN BLOCK, not part of
  this order -- above all the own system with the interactive backlog (FR-0024); humanizer follow-up
  waits for the taste verdict. Cut as PRs after the gen-3 merge round and the retrospective
  (DEC-0067; first use of the plan approval DEC-0068). User asks what H and S are ("I thought
  everything is FR/SR/CR/PR/TSK") -> answered in chat; candidate FR: hole-list entries as typed items.
- 2026-09-03 16:5x **Stream E rework 2 reported** (Opus, ~40 min; round ~6 h 35, ~455 k; reading
  suites only). B-1 qualified instead of suppressed ("no :focus-visible rule in the sheets this run
  could read (N unreadable, named)", rc 3 stays; red-first + third assertion in the H145 test).
  B-2 the pseudo-element's OWN display/visibility/opacity/empty content are asked (four
  parametrised cases red; counter-direction test green). N-1 signal named; N-2 H140 (1) names the
  NOT DECIDABLE line; N-3 docstring limit; N-5 order; H138 entry + row point to DEC-0069. 34 tests
  (27 -> 34), gate nodes 2 in 2.2 s, stamp -5, patch 8 files +1568/-22. Re-verify 3 sent.
- 2026-09-03 17:0x USER "ja" -> **FR-0087 OPEN**: hole-list entries become typed items (BUG-shaped
  with a 'limits' duty and a user-minted acceptance edge, or an own type -- DEC first), ids by the
  kernel, test_gates judges read items, merge seam table reads the index, one-round migration with
  a generated pointer index in the document; kits get the same shape. -> G4-2 kernel contracts.
- 2026-09-03 17:1x **Stream A re-verify: FAIL (one finding, two lines), M 1 / N 1** (Opus, 20 min,
  ~75 k; ~370 k both). B-1 closed and loaded with 25 hand-file forms (epoch nan/inf/string/None/
  container, bombs in item/request_id/kind/subject_manifest, non-mapping, scalar, BOM, empty,
  broken yaml, binary, surrogate, self-referential, directory, 5000 files) -- every one rebuilds
  the board, page 37.4-37.8 KB; warm 5000 pending = 1.5 s per write. B-2 closed both ways (four
  mutations, named test alone red). M-1 closed: 0 px overhang at six widths incl. focus list;
  four-variant measurement confirms only overflow-wrap carries (min-width alone leaves 96-747 px);
  the document probe catches position:absolute. M-2 closed over eleven char forms incl. surrogate
  in the id field; determinism after replacement. N-3 numbers match word for word. NEW M-3
  `board.py:369-370`: `_flat` on request_id and kind carries 42.8 s and a 3.4 GB page, and no test
  reddens when either reverts (72 passed) -- the test covers one of three fields; fix = two rows in
  `_UNWRITABLE_REQUESTS` + two mutations. N-8 `overflow-wrap` for `.card .title` stated twice
  (:1213 and :1441). Verifier owns two misses of round 1 (recommended a line that carries nothing;
  split one rule into two cases). Rework 2 sent (two lines); verify 3 after.
- 2026-09-03 17:2x **Stream E verify 3: PASS with one merge condition** (Opus, 35 min, ~65 k; three
  rounds ~360 k). B-1 closed in all four sheet configurations (readable rule -> no accusation;
  rule only in the unreadable sheet / truly none -> qualified sentence rc 3; two unreadable sheets
  named); return to suppression AND to the "at all" wording both red. B-2 closed with four separate
  pins (display/visibility/opacity/empty content each red alone), collapse/space/attr()/url()
  rc 0, element visibility still first, opacity 0.001 judged = the checkVisibility boundary
  (consistent). N-1 three signal combinations; N-2/N-3/N-5 done; DEC-0069 exists in the main repo,
  not in the patch (project_memory respected). Two new NAMED RESTS, non-blocking: R-A `@import` of
  an unreadable sheet is never entered by walkRules (CSSImportRule keeps rules under
  rule.styleSheet) -> unqualified accusation + silent literal; fix = one try/catch branch or a
  sentence in H145. R-B `["::before", "::after"]` is a list without a tripwire; `::placeholder`
  (the classic faint-placeholder mockup defect) and `::marker` rc 0; fix = two names + the reason
  the list is a list (CSS closes the set, the DOM does not enumerate it) or a sentence in H146.
  Against the cut (unchanged): H145/H146 not in the frozen item; forbidden project_memory/** vs
  the staging exception. (g) row E: Opus, first report ~3 h 30, verifier B1/M5/N4 -> rework 1
  (2 h 25) -> FAIL (bookkeeping) -> rework 2 (40 min) -> PASS; three verifications (75 + 50 + 35
  min); implementer ~455 k, verifier ~360 k; spawn -> PASS ~9 h 45 wall (incl. ~2 h 20 of full
  suite runs the order did not ask for). Closing lines R-A/R-B ordered (build, no re-verify).
- 2026-09-03 17:4x **TSK-0120 DRAFT = the generation-3 merge round** (root PR-0003 per DEC-0066/
  0067; created by staging/generation-3/create_merge_task.py). Apply order C, B, A, E, D; seam
  table + arbiters from this logbook and the five protocols; CRLF measured before the first apply;
  the two scope readers decided; ONE stamp, ONE full run + gate suite; (g) table completed; cut
  findings collected for the retrospective DEC. Stays DRAFT (editable) until A and C PASS; then
  residue lines updated, READY, merge implementer (Opus) spawned in the main tree, merge verifier
  after.
- 2026-09-03 17:5x **Stream A rework 2 reported** (Opus, ~35 min, ~45 k; round ~715 k). M-3: the
  bomb built per field (`_alias_bomb_request(field)`), five request forms, and the test gains a
  memory assertion (tracemalloc, 8 MB cap: 42x above need with fix, 3.5x below the cheapest
  defect) because `request_id` never reaches the page -- measured without the guard: request_id
  5.9 s / 28 MB / page unchanged, kind 6.6 s / 558 MB / 107 MB page, item 6.8 s / 510 MB; with
  guard 0.02 s / 0.19 MB. Four mutations red on the same node. N-8 one place; "collective rule
  removed" stays red. test_board 74, test_board_browser 5 (run because N-8 touches the CSS it
  measures -- right call), stamp -5, patch 16 files +3292/-892. Verify 3 sent.
- 2026-09-03 18:0x **Stream E closed** (rework 3, ~20 min; round ~6 h 55, ~475 k): R-A BUILT --
  `walkRules` enters `CSSImportRule.styleSheet.cssRules` in the same try/catch, unreadable import
  named with its href (both directions measured: unreadable neighbour -> qualified + named;
  readable data: import -> no accusation, literal found); R-B BUILT -- four pseudo-elements, each
  stating how text reaches it (::before/::after via content, ::placeholder via the attribute,
  ::marker via list-style; content computes to normal for the last two, measured), the reason the
  list is a list written in code (the DOM cannot enumerate pseudo-elements), cost in H146; tests
  measure the counter-direction too. 38 tests (34 -> 38), gate nodes 2, stamp -6, patch 8 files
  +1750/-22 = **E's merge input**. H145 rest widened (any sheet the document may not read, linked
  or imported; readability decided by the browser).
- 2026-09-03 18:1x **Stream A verify 3: FAIL, M 1 (text) / N 3** (Opus, 23 min, ~60 k; ~430 k all).
  M-3 CLOSED: four mutations each caught by its own assertion (request_id by the MEMORY assertion
  alone, page unchanged 37 408 B); 8 MB cap bit-identical over five runs and under 16 CPU burners,
  depth-independent in the green case. N-8 closed both ways. NEW M-4 (blocking, text): seam §7.5
  and H126 hand C a NEW `def open_requests(state, now)` -- the function EXISTS (`approvals.py:2136`,
  one argument) and gate_approval x3 calls it with one; applied literally: TypeError, 2 failed in
  test_hooks_v2, and the seam's named arbiter (test_board parity) cannot see it; `now=None` -> 88
  passed. Fix = two sentences: the seam is an optional `now=None`, second arbiter
  `test_hooks_v2.test_an_expired_request_is_not_open_and_a_reworded_relay_goes_silent`. N-9 8 MB
  in three places without the reason (two pre-existing), same for `took < 30`. N-10 the cap's
  margin hangs on `range(1, 21)` 80 lines away: at depth 18 the cheapest defect is 7.01 MB, under
  the cap; deeper fixture costs nothing. N-11 `board.py:376` computes `request_id` and nobody reads
  it -- the cheaper answer to M-3 (drop the field) that the verifier did not see in round 2 (own
  miss named). Rework 3 sent; verify 4 after (text + one field).
- 2026-09-03 18:4x **Stream A rework 3 reported** (Opus, ~50 min, ~60 k; round ~775 k). M-4 text:
  §7.5 + H126 = optional `now=None` on the existing function, measured table (new signature red on
  two test_hooks_v2 nodes, parity test blind), two arbiters named, cycle reason `approvals -> state
  -> board` verified at the import lines; H126 says the rule stands THREE times. N-11 `request_id`
  removed (nothing reads it; with the seam the id comes from approvals.pending_request); the fixture
  now measures the counter-direction (an unread field costs nothing). N-9 `_MEMORY_BUDGET` +
  `_STATE_WRITE_SECONDS` with reasons, three call sites each. N-10 `_BOMB_LEVELS` once, end alias
  derived -- and while re-measuring the implementer hit the described error itself (lowered range,
  literal `*a20` left -> file no longer parsed -> reader skipped it -> "defect" measured 0.19 MB and
  looked harmless) -> the test now asserts the bomb ARRIVES (parses, field is a container) before
  judging cost; probe: 3 of 5 forms red without that. 79 green, 41/41 mutations, stamp -6, patch 16
  files +3364/-896. Verify 4 sent.
- 2026-09-03 18:5x **Lead process finding (own):** the C re-verify sent at 13:3x was "queued for
  delivery at its next tool round" while the C verifier was finishing its addendum -- it never ran;
  ListAgents at 18:4x listed no C verifier. ~5 h of C's critical path lost. Re-sent -> "Resuming
  agent". Rule for the (g) table and the lead role: a SendMessage result that says "queued" (not
  "Resuming") to an agent that is completing is not a delivery -- confirm with ListAgents.
- 2026-09-03 19:1x **Stream C re-verify: FAIL (one M), N 3** (Opus, 2 h 05 by its clock, ~220 k;
  report reached the lead only after the re-send -- correction to the 18:5x note: the message was
  delivered and the run happened; the COMPLETION NOTIFICATION was lost; same lesson). B1 CLOSED:
  merge AND push rc 0 before/after a plan approval, counter-direction rc 2 with a true remedy;
  seven counter-directions planted and caught incl. three the old code never checked (provenance,
  clock, item binding) -- strictly stricter; real store 0/54 with old and new report.py; the
  widened test is a broader reading, not weaker (two mutations red). B2 closed (DEC-0068 per goal,
  seven kinds). M1 closed over eleven fold classes, hook-as-process vs kernel verb: disagreements
  none. N3 seam rule = a property (four extra attacks rc 2). NEW M: `DATE_FIELDS` refusal +
  normalisation live only in capture_preflight/capture; `update MST-0001 {"due": "Weihnachten"}`
  rc 0 stored, `"20261225"` stored raw, `null` stored -- M2's own symptom via another verb, and
  H147's three limit sentences ("exactly one spelling", "only the question whether an input gets
  through", "the stored record stays readable") are false. Fix = the DATE_FIELDS loop in
  `_update_item_locked` + two test lines, or H147 names the capture path only. N1 `pair_seam`
  intersects raw strings (Docs/** vs docs/** = no seam, rc 2 fail-closed but no NOT-A-SEAM line);
  fold in scope_entries. N2 the rig guard asserts cwd instead of joining HERE. N3 the two scope
  readers agree in predicate and rule but differ in INPUT (D: command line only; kernel: also the
  seam_scope item field) -> merge decision (TSK-0120 already carries it). Rework 2 sent.
- 2026-09-03 19:3x **Stream A verify 4: PASS, 0 B / 0 M / 4 N** (Opus, 40 min, ~65 k; four rounds
  ~495 k). M-4 closed and word-for-word consistent with TSK-0120's seam line; N-11 closed (25
  hand-file forms rebuild, 5000 files counted); N-9 closed with a counter-measurement that the time
  budget carries something (binding-field defect without the memory assert reddens over time,
  388.8 s); N-10 half. N-12 the arrival check reads the TYPE not the STRENGTH (`_BOMB_LEVELS` 3 or 8
  with both guards removed -> 5 passed; a 52-char "bomb" counts as arrived) -> bind the fixture to
  its effect (`len(str(v)) > plain`) instead of a remembered number; N-13 §13 credits the new
  assertion with a catch `test_board.py:1724` already made; N-14 "the memory budget is the
  load-bearing one" no longer true at the new call site since request_id fell; N-15 H126: three
  readers, two clocks. Verifier owns half of N-12. (g) row A: Fable design 07:22-09:56 (4 phases,
  4 user taste rounds, ~690 k) + Opus build ~4 h 30 first report, verifier B2/M2/N7 -> rework 1
  (1 h 30) -> FAIL M1/N1 -> rework 2 (35 min) -> FAIL M-4 text -> rework 3 (50 min) -> PASS; four
  verifications (52 + 20 + 23 + 40 min); build implementer ~775 k, verifier ~495 k; build spawn ->
  PASS ~9 h 15 wall. Closing lines N-12..N-15 ordered (no re-verify).
- 2026-09-03 19:5x **Stream C rework 2 reported** (Opus, ~40 min; round ~4 h 50, ~650 k). M:
  `state._dates_in(item_type, fields, operation)` -- one function, three callers (capture_preflight
  refuses, capture writes its result, _update_item_locked calls it BEFORE the hashed-field compare
  so rewriting the same day is no change); `update {"due": "Weihnachten"}` rc 1 untouched,
  `null` rc 1, `20261225` -> `2026-12-25` rev unchanged; red W6 `test_the_update_path_reads_a_date
  _field_exactly_as_capture_does`. H147 rewritten: condition (both verbs share one reader), the
  refuting measurement cited, a writer OUTSIDE these verbs (hand edit, import) named as unbounded.
  N1 fold at the door (`scope_entries` calls `_norm`, all three fields); `Docs/**` x `docs/**` one
  seam rc 0, red W7. N2 rig joins HERE and uses newline="" (the text mode was the CRLF cause). N3
  named for TSK-0120 (input difference, not verdict difference). 116 + 246 + 4 green, stamp -6,
  patch 24 files +2859/-131, 37 new tests. NOTE for the merge: the C worktree files it touched are
  uniformly CRLF ("the convention of this checkout") -- git apply --check on e45c0ca passed in
  every verification, but the merge implementer measures eol before applying. Verify 3 sent.
- 2026-09-03 20:0x **Stream A closed** (rework 4, ~30 min, ~35 k; build round ~810 k): N-12 the
  arrival assertion measures STRENGTH (what str() of the bombed field would produce must exceed the
  page; price computed over the graph, memoised, not built) -- levels 3/8 with both guards removed
  now 3 failed; N-13 §13 corrected (the block relocates the failure to the fixture, catches nothing
  new); N-14 the budget comment names its two load-bearing sites and the third's own reason; N-15
  H126 three readers on two clocks, why the seam is an OPTIONAL now. test_board 74; no kit code ->
  stamp unchanged -6. Patch 16 files +3400/-896 = **A's merge input**.
- 2026-09-03 20:1x C verify 3 terminated by API 529 Overloaded (server side, no finding). Resumed
  with context per DEC-0063 (6) ("Vorgefunden" first, measured scratch counts, no re-measure).
- 2026-09-03 20:3x **Stream C verify 3: PASS with one merge condition** (Opus, ~1 h 15 measuring
  across the 529 interruption, ~170 k; three rounds ~690 k). M closed: `update` refuses every bad
  form (string/null/""/0/false/[]/list/mapping) untouched, normalises `20261225` and int with
  revision 1 -> 1, atomic over several fields, the ordering line before the hashed compare is REAL
  (with it: same-day rewrite keeps APR-0001 in force; without: rev 2, DRAFT, approval dead); foreign
  type with `due` stored (undeclared field, documented, no regress). H147 text now matches. N1 fold
  at the door holds for all three fields incl. forbidden; rest: `docs/` vs `docs/**` are one file set
  to the gate but two strings to `pair_seam` -> rc 2 fail-closed = N, append to H148. W6/W7
  reproduced red. B1 no regress (merge AND push rc 0 after a plan approval). **M (delivery form):**
  20 of the 24 patch files are CRLF in the C worktree (the rig's text mode; NOT "the checkout's
  convention" -- `.gitattributes:10` says `* text=auto eol=lf` since BUG-0025); the PATCH is pure LF,
  24/24 index parents = e45c0ca, applies on an LF checkout; kit_hash normalises CRLF, stamp -6
  trustworthy. Merge line: take the patch, never file copies from g3-approvals; normalise the
  worktree first. Verifier's own miss: first CRLF sweep converted 160 binaries and nearly called the
  stamp worthless. (g) row C: Opus, first report ~3 h 20 (two mid-round seams), verifier B2/M2/N7
  -> rework 1 (1 h 10) -> FAIL M/N3 -> rework 2 (40 min) -> PASS; three verifications (2 h 20 + 2 h
  05 + 1 h 15) + one lost completion notice (~5 h idle) + one 529; implementer ~650 k, verifier
  ~690 k; spawn -> PASS ~13 h wall (critical path of the generation). **ALL FIVE STREAMS PASSED.**
- 2026-09-03 20:4x **TSK-0120 READY; merge implementer (Opus) spawned in the main tree** (order
  from the item; eol measurement + plan + seam table + pin baseline first; C's patch only after the
  lead's "C final" once C's worktree is LF-normalised and the patch re-emitted byte-identical).
  Retrospective DEC (successor of DEC-0063) after the merge verdict, from the (g) rows here.
- 2026-09-03 21:0x **Stream C closed** (closing pass ~25 min; round ~4 h 50 + closing, ~670 k):
  worktree normalised to LF (21 files, 50 564 bytes; binaries decided by bytes -- 2 071 binaries in
  the tree contain \r\n by chance, an extension list would have destroyed a font one day); git diff
  --stat identical before/after; kit_hash unchanged (kernel.hashing normalises CRLF itself --
  measured); patch byte-identical before/after normalisation, then re-emitted with the second H148
  rest class: 231 318 B, sha e3ab4ceac6b0…, +2879/-131 = **C's merge input**. "C final" sent to
  the merge implementer with the sha.
- 2026-09-03 23:0x Merge implementer terminated by the weekly rate limit (HTTP 429) mid-round;
  user: "reset war drin. weiter." Resumed with context per DEC-0063 (6) ("Vorgefunden" from the
  disk first). ListAgents to confirm.
- 2026-09-03 23:2x **Merge round (TSK-0120) reported** (Opus, 19:01 -> 23:1x ≈ 4 h 15 incl. the 429
  resume, ~1 h 40 suite runtime, ~530 k). Five patches applied C, B, A, E, D on e45c0ca (sha per
  patch measured, C = e3ab4cea…), pin set 67 + 3 green after every patch, VERSION hunks dropped;
  eol: 35 CRLF files outside project_memory measured (own first count 27 was a filter error, fixed
  before applying), exactly TWO files met a hunk and were normalised (progress.dashboard.template.html,
  research PM SKILL.md), cause = core.autocrlf=true local AND system vs .gitattributes (BUG-0025 gen
  4). Seams: MST hook lines x3 + `milestones/active` x3 (+ a NEW tripwire, the named one stayed
  green with all three dirs deleted = M-2), backlog_tree MST lines, plan_diagram trigger in
  state._write_board in its OWN try (A's "same try" would have let the board message lie = M-4),
  cli.py paths derived from plan_diagram.FILENAMES (counting arbiter replaced = M-5), `now=None` +
  `has_expired` as the one definition with three readers (approvals.mint was a FOURTH reader raising
  bare ValueError = M-1), **S9 separator BUILT** (`_filing._walk` fourth field
  `changes_the_calling_shell`) -> **H144 CLOSED** with a named over-refusal, sentences B/C/E +
  DEC-0064 constitution line written, scope readers decided: kernel/scopes.py survives, the workshop
  tool keeps only the command line (they answered a swallowing seam rc 1 vs rc 2 = M-6). 16
  red-first measurements incl. two self-corrections. Full-run findings M-10..M-13 (plan question
  never measured -> new test; EUeR vocabulary vs kit neutrality FR-0028 -> exception WITH tripwire;
  list floor; shared paragraph exception). Against the ORDER: M-7 "F6 call line in report.py" exists
  in no protocol (S4 proposal, S5 optional, S6 hook change); M-8 the item says H126 "two clocks ->
  one", A's measured entry says the rule becomes one, the clocks stay two -- followed the
  measurement. Three NEW cut findings: tools/test_hooks.py is written by A, B AND C (table said
  A x B) + three unnamed shared files (test_kernel.py, constitution_section_pins.json,
  phase0-disposition.md); "every patch drops the VERSION hunks" false (four of five carry them);
  DEC-0064's cost list names two tripwires that do not see the defect or do not exist. Hole list
  merged section-wise (line-wise attempt put a table into a foreign entry -> rig refuses two streams
  on one entry), 0 lines missing, H128/H149 stated unused; H126 narrowed, H127 half closed, H136
  closed, H144 closed. Suites: tools/ full ONCE 4554 / 14 / 4 failed = 4572 collected (57:45) ->
  four findings fixed (tests only) -> DEC-0063 (4) full runs of the reading suites (201 + 117) +
  gate suite 489 (26:10); BUG-0033 did not appear; ruff/validate clean. Stamp ONCE: 2026.09.03-1
  x3. Deliberately open: H130, S5, S6 (measured against: binding the duty register to an importable
  kernel would silence it at session start), S8, H127's reporting half, BUG-0025, eight cut
  findings. 14 new files `git add`ed (validate needs them tracked). (g) table in protocol §9;
  bottleneck = two orchestrator delivery failures (~5 h idle) + ~5 h suite runtime DEC-0050 did not
  ask for, not the cap. **Merge verifier (Opus) spawned.**
- 2026-09-04 00:2x **Merge verifier: FAIL, B 1 / M 4 / N 4** (Opus, ~50 min, ~300 k; own office
  scaffold, six Bash PreToolUse entries = 8 hooks as processes). Merge itself clean: five patches
  apply --3way rc 0 in seam order on e45c0ca, rest vs merge = 24 hand-worked files all explained;
  90 changed files = 68 patch union + 22 named; real overlap = wishlist (x5), phase0-disposition
  (A,D,E), VERSION, test_hooks.py (A,B,C), test_kernel.py (A,B), constitution_section_pins.json
  (D,E) -- no unnamed collision; 13 red-first reproduced incl. M-2 both statements; S9 attack surface
  (subshell, ||, braces, bash -lc, nohup, timeout, env, newline, pushd, PowerShell) correct; hole
  list 117 entries strictly ascending, gate nodes can fail (four mutations); eol 33 CRLF outside
  project_memory untouched by any hunk, two normalised = HEAD blob + patch byte-equal; digest clean
  (14 A / 75 M / 1 MM, no unknown file; .audit = HEAD prefix + 22 lines from today's hooks). **B1
  (blocking):** `guard_fs_tripwire.py:715` + `_filing.py:502-529` -- S9 keeps the sweep base only
  on a CERTAIN cd; an uncertain cd that leads BACK to the root leaves a stale harmless base: `cd
  outbox && cd .. && rm -rf .`, `... ; rm -rf .`, `cd outbox ; true && cd .. ; rm -rf .` rc 0 on
  all hooks (controls `rm -rf .` and `cd outbox ; cd .. ; rm -rf .` rc 2); measured caused by this
  round (with `changes_the_calling_shell` = True the line is rc 2; e45c0ca rc 0 too = no
  regression vs HEAD but a claimed close that is not one); three prose claims false (`_filing.py:510`
  fail-closed, guard head :123, H144 "GESCHLOSSEN für die vier Formen" while the item says H144
  stays open either way). Fix prototyped by the verifier: `standing` becomes a SET -- an uncertain
  change ADDS a base instead of replacing it, the sweep is refused when ANY base holds a tray;
  three ALLOWs -> rc 2, twelve controls unchanged, one more over-refusal (`cd outbox ; cd .. | true
  ; rm -rf .`). M1 H125 row/paragraph (d)/verdict still say rc 0 for `cd outbox & rm -rf .` (now rc
  2) and count H144 as uncovered. M2 `tools/check_scope_overlap.py:20` claims kernel/scopes.py
  carries H135/H142/H143 -- H142/H143 nowhere under team-kits (D's N5 pointers lost with the retired
  second reader) -> D's package incomplete at that line. M3 protocol "0 missing" false: 24 wishlist
  lines of B/A/D missing, all in the five entries this round re-judged (H126/127/135/136/144) --
  number wrong, substance right. M4 against the ORDER: four of five patches carry VERSION hunks; "F6
  call line in report.py" exists in no protocol; H126 "two clocks -> one" vs measured "one rule,
  two clocks"; "(H144 stays open either way)" vs the protocol's CLOSED. N1 `pushd outbox ; popd ;
  rm -rf .` ALLOW (pre-existing; uncomputable move back to a tray leaves the base) -> hole entry,
  **H150 reserved**. N2 a seam arbiter was a grep (collect-only proves it). N3 E's (a) sentence
  additive. N4 collect 4573 vs 4572 (the M-10 test born after the full run). DEC-0050: letter
  deviated (stamp before full run), substance fine -- validate.py proven red-capable on a kit edit,
  reading suites full, stamp covers the shipped tree -> retrospective note. Rework sent to the merge
  implementer; re-verify after.
- 2026-09-04 01:3x **Merge rework 1 reported** (Opus, 00:03 -> 01:25 ≈ 1 h 20, ~65 min suites,
  ~120 k; round ~650 k). B1 CLOSED: the sweep base is a SET of possible positions (a certain change
  replaces it, any other adds a candidate, the destruction is refused when ANY candidate holds a
  tray) -- three lines; the three ALLOWs -> rc 2 and `pushd ; popd ; rm -rf .` (N1) too? NO --
  measured: popd hands out no target, nothing to add -> N1 BUILT separately (three lines, two more
  named over-refusals) = **H150 filed and closed**, beyond the order and said so. Price named: three
  over-refusals (`true && cd outbox ; rm -rf .`, `cd outbox ; cd .. | true ; rm -rf .`, `cd outbox ;
  cd $X ; rm -rf .`). Red-first R19-R21 each half; own correction: R21 is held by the H144 arbiter,
  not by the test that claimed it -- both docstrings say which half they hold. Three prose claims
  made true (`_filing.changes_the_calling_shell`, guard head :123 with H144 AND H150,
  moves_the_working_directory:415 costs named). M1 H125 row rc 0 -> rc 2, (d) + verdict = three
  uncovered classes; M2 H142/H143 in `scopes.overlaps`/`owns_anything_outside`; M3 "28 missing of
  1182, all in the eight re-judged entries (A 6, B 8, D 9, 5 summary rows), C and E 0"; M4 four
  order findings in §6 lines 9-12; N2 arbiter = collect-only; N4 collect 4574 (two tests born after
  the full run). Own find: an `(H150)` inside a measurement table was read as a verdict row ->
  moved to prose. SECOND stamp with reason: dev/office/research 2026.09.04-1. Reading suites FULL
  after the stamp: test_hooks 943/13 (17:20), ten suites 2465 (18:48), gate suite 489 (28:33),
  ruff/validate clean. Tree 90 files +12776/-1602. Re-verify sent to the merge verifier.
- 2026-09-04 02:2x **Merge re-verify: FAIL, B 1 / M 4 / N 1** (Opus, ~40 min, ~90 k). B1 fix works
  as reported (three ALLOWs + H150 rc 2, twelve controls, R19-R21 each half, R21's split correctly
  stated, candidate set bounded: 500 uncertain cds 3.29 s). **B2 (blocking):**
  `guard_fs_tripwire.py:723-729` computes `moved` from the NEWEST candidate only and a CERTAIN change
  REPLACES the whole set -> after an uncertain cd the root candidate is dropped: `cd docs | true ;
  cd ../outbox ; rm -rf .`, `false && cd docs ; cd ../outbox ; rm -rf .` rc 0 while real bash
  (shell_truth.py) stands on the ROOT (the second cd fails, resolved against the root); rc 0 on
  e45c0ca, 09.03-1 and 09.04-1 = open neighbour, no regression -- but the guard head :121-123 now
  claims "judged against every position the shell could be standing in" and H144/H150 say CLOSED.
  Fix measured (four lines): map the change over EVERY candidate; certain -> replace by the mapped
  set, uncertain -> union; three ALLOWs rc 2, all 18 controls/prices unchanged. M5 two over-refusals
  unnamed (`pushd outbox ; pushd sub ; popd ; rm -rf .` and `cd <ABS>/outbox ; rm -rf .` rc 2 since
  09.03-1); M6 4573 vs 4574 in two places (SR-0008); M7 "28 missing" measured 30 (A 9, B 10, D 11);
  M8 the reading-suite list misses test_e2e (raw_hook guard_fs_tripwire) and one test_migrate node
  (reads the wishlist) -- verifier ran both, green; N5 prose inside the run table. DEC-0050
  judgement: not repeating the full run is right; coverage given with the M8 gap now closed. Rework
  2 sent.
- 2026-09-04 02:3x **Merge rework 2 reported** (Opus, 01:25 -> 02:25 ≈ 1 h, ~23 min suites, ~95 k;
  round ~745 k). B2 CLOSED: the change is computed from EVERY candidate; certain -> the mapped set,
  uncertain -> union (four lines, `guard_fs_tripwire.py:735-741`, the H150 add-on in the same
  expression); real bash as arbiter: the three ALLOWs (bash on the root) rc 2, 18 controls/prices
  unchanged, 0 deviations over 21 lines; red-first R22/R23 only in the NEW test
  `test_a_relative_change_is_computed_from_every_position_it_could_start_in` (the three existing
  arbiters move away from the root); guard head :119-134 names both failed intermediate readings
  with measurement and FOUR prices. M5 decided by measurement: `pushd outbox ; pushd sub ; popd`
  = real over-refusal (fourth price, named in H144/H150/head); `cd <abs>/outbox` unquoted is NOT a
  price -- real bash answers "cd: too many arguments" (the path carries a space) and stays; quoted
  both follow (rc 0); the space-free variant is unmeasurable on this host (every allowed scratch dir
  lives under C:\Offline Repos\...) -- said. M6 one place (§8: full run 4572, today 4575 = three
  tests born after); M7 counting rule beside the number (whole-line rule A 9, B 10, D 11 = the
  verifier's; substring rule two fewer; both stated); M8 test_e2e + test_migrate in the reader table
  and re-run; N5 prose out of the table. THIRD stamp, itself a probe: bump stamps ONLY office
  -> 2026.09.04-2, dev/research stay 2026.09.04-1 (the hash decides, not the announcement). Runs
  after the last kit change: test_hooks + test_e2e + test_migrate FULL 1105/13 (21:24),
  test_parallel_scopes/streams 43, wishlist nodes 3 + 5, ruff/validate clean. Tree 90 files
  +12860/-1602. Re-verify 3 sent.
- 2026-09-04 03:1x **Merge verify 3: PASS, 0 B / 0 M / 2 N** (Opus, ~45 min, ~60 k; three rounds
  ~450 k). B2 fix holds against 14 chain forms measured against REAL bash (`bash -lc ... ; pwd`):
  uncertain+certain+uncertain, a target that exists from one candidate only, a target outside the
  project (the set cannot go empty: `... or one` keeps every candidate the change cannot be computed
  from), dedupe order (`standing[-1]` left only in the H150 add-on, harmless), 500 alternating
  changes 1.28 s; R22 red only in the new test, R23 (`standing[0]` only) stays green but is
  STRICTER never looser (first candidate = the start position that holds the trays) -> N7 docstring
  sentence. M5-M8, N5 confirmed; stamps dev/research 2026.09.04-1, office 2026.09.04-2, validate
  green; digest clean (90 files = 68 patch union + 22 hand-worked, nothing unknown); hole list 118
  consistent, new test name resolves, gate nodes 5. N6 PowerShell pipeline is not a subshell ->
  `Set-Location docs | Out-Null ; Set-Location ../outbox ; rm -rf .` rc 2 while the shell is in
  outbox = FIFTH price, unnamed (verifier owns: visible in its round 1). Verifier's own corrections:
  its M5 absolute-path price was wrong (bash says "too many arguments" on the unquoted space); it
  MEASURED the "unmeasurable" space-free variant in a pilot under C:\tmp_nospace_probe (outside
  _round-scratch -- rule breach named and the pilot deleted): the guard follows an absolute cd fully,
  no price in that class -> replace the H144 sentence. Closing lines N6/N7 + the H144 sentence
  ordered (no re-verify); then EVD + commit. (g) row merge: Opus, 4 h 15 first report + 1 h 20 +
  1 h reworks, three verifications (50 + 40 + 45 min), ~745 k impl / ~450 k verif.
- 2026-09-04 03:3x **Merge round CLOSED** (closing lines 22 min, ~45 k; round 19:01 -> 02:47 ≈ 8 h 15,
  ~790 k). N6 fifth price named (PowerShell pipeline is not a subshell) in H144/H150/guard head; N7
  MEASURED instead of ticked: no one-candidate reading survives the file (newest-only red in two
  tests, first-only red in the both-positions test), the offered five-minute case built, measured
  and rejected (the delete rule refuses it before the sweep rule -- same fallacy as rework 1, twice
  measured); H144 "unmeasurable" replaced by the verifier's measurement (no price in the absolute
  class). Final: 90 files +12887/-1602, stamps dev 2026.09.04-1 / office 2026.09.04-3 / research
  2026.09.04-1, collect 4575, wishlist H123-H148 + H150 (H128/H149 reserved-unused), 33 CRLF files
  untouched (BUG-0025 gen 4). Next: EVD + commit by the lead.
