# TSK-0099 — implementer protocol (BUG-0076: the design draft reached the user UNSEEN)

Role: harness-implementer. Nothing committed, nothing pushed.
Scratch: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0099\` (rig, clone, mutation drivers).
Rework round 2 after a verifier FAIL (F1–F9). What changed against round 1 is marked **[R2]**.

## 1. What was measured before anything was built

| question | measurement |
|---|---|
| which kits own a draft judged by its LOOK | **[R2]** the property is now read off each role's own `## Files you WRITE` section: dev-team (product-designer) and research-team (report-writer, `EXP-*.html`) both stage HTML; research is an explicitly named exemption (`DESIGN_LOOP_EXEMPT`) because that HTML is the optional quick view of the `.tex`/PDF and is judged on CONTENT. Round 1 asserted this property and measured a word search for `freeze-design`, which research fell straight through |
| can the sighting role render | `dev-team/agents/product-designer.md:4` granted `Read, Edit, Write, Grep, Glob` — no command tool; `kernel.dispatch.hand_back_path` answered `lead` |
| does a path-carrying render CLI work | NO: `--source project_memory/staging/...` is rc 2 at `gate_write_scope` for lead AND subagent. The id form is rc 0 across **all eight** gates the kit registers on a shell line, both callers — 32 runs, 0 refusals **[R2: eight gates, not the three round 1 ran]** |
| is Playwright a NEW dependency | no: `templates/repo/requirements-dev.txt:12` already ships it for `kit_browser_checks.py` |
| does an image reach the sighting role | yes, end to end: the renderer wrote `review/DSN-0001__1440x900.png` and `Read` displayed it |

## 2. F1 — the trigger now reads filesystem → text **[R2, blocking]**

Round 1 tokenised the message and resolved each token as a path; `:` and whitespace were excluded
from the token, so a Windows path lost its drive letter and a path with a space lost everything
before it. The live project sits under `C:/Offline Repos/gewerbe/...`.

The gate now enumerates the staged `.html`/`.htm` under `project_memory/staging/**` (a set the
kernel empties on promotion) and asks whether the message contains a draft's **file name** or its
**staging-relative path**, case-folded. New measurement series against ONE unrendered draft
(`spellings.py`, real hook process, project outside the repo, path with spaces):

| must refuse | rc | | must pass | rc |
|---|---|---|---|---|
| repo-relative | 2 | | name without `.html` | 0 |
| absolute (`\`) | 2 | | the folder only | 0 |
| absolute (`/`) | 2 | | `src/index.html` | 0 |
| `file://` URL | 2 | | `design/revisions/DSN-0001.r01.html` | 0 |
| quoted absolute | 2 | | the wireframe `.drawio.svg` | 0 |
| bare file name | 2 | | a plain product question | 0 |
| UPPER CASE | 2 | | | |
| markdown link | 2 | | | |
| space in the file name | 2 | | | |
| space in a sub directory | 2 | | | |

0.15–0.28 s per run. The visible prose BEFORE the question: **checked, deliberately not read** —
the `PreToolUse(AskUserQuestion)` payload is the question and its options; `transcript_path` is in
the payload (`tools/provider_observations.json`) but is unbounded, provider-shaped, and a mention
three turns old is not this question's mention. Named as the residue in H82 (a).

The three places that named the mechanism wrongly are corrected: `gate_design_sighted.py` head,
`skills/project-manager/SKILL.md`, `docs/POST_V2_WISHLIST.md` H82 (a). The residue is now "a
mention that never writes the file name out", plus the prose-before-the-question route.

## 3. F2 — the inventory and the pins **[R2, blocking]**

`gate_design_sighted` entered dev-team's `WHAT RUNS HERE` list (constitution §2), whose own
sentence claims completeness in both directions. Then
`pin_constitution_sections.py --write --note` (4 sections), then
`record_lead_package_sizes.py --write --note` (dev-team 41237 → 41260 B, +23), then
`bump_kit_version.py`. `tools/test_shortening_net.py`: 36 passed.

## 4. F3 — the containment note now matches the gates **[R2, blocking]**

Round 1's role text said `gate_write_scope` "keeps your writes inside your task's `allowed_scope`".
Measured by the verifier as a bound subagent through all eight registered shell gates: the Write
TOOL onto `src/app.py` is rc 2, but `echo x > src/app.py`, `sed -i`, `cp`, `python -c open(...)`,
`curl`, `cat .env` are rc 0; only `docker system prune -f` and `git push` refuse. The note now says
the scope binds the WRITE TOOLS and not a shell line, names what does refuse, and points at
`ENFORCEMENT.md` instead of summarising it a second time. H82 (e) carries the same correction.
`test_the_product_designer_can_look_at_its_own_draft_and_says_what_that_costs` asserts the
retracted claim cannot return.

## 5. F4/F6/F8 — built rather than named **[R2]**

* **F4** the stop door is scoped to the property "this role could have rendered", read off the
  installed role file. Measured per caller: `product-designer` 2, `frontend-developer` 2,
  `quality-engineer` 2, `devops-engineer` 2, `software-architect` 0, `Explore` 0, no `agent_type` 0.
  The remaining over-reach (a shell-carrying specialist that merely quotes a draft) is H82 (d) with
  its cost: the exact cut is `kernel.dispatch.task_for_agent`, which needs the kernel bridge and
  the `GATE_PREAMBLE` restructure of the whole hook (DEC-0056).
* **F6** image paths are contained to the staging item (`_contained_child`);
  `"images": ["../../../elsewhere.png"]` is rc 2. The overstated "the record proves provenance" is
  gone from the hook, the renderer, the skill and the ENFORCEMENT row: the record is self-report of
  the judged agent, so it establishes neither a render nor a sighting.
* **F8** `seen` is counted per SOURCE PATH; a sibling draft nobody rendered now reads "nobody has
  rendered this draft" instead of "this file changed after it was rendered".

## 6. F5 — the registration is measured **[R2]**

`test_both_doors_run_through_the_command_the_kit_registers` installs hooks + kernel + settings +
role files as a scaffold does, reads the command line for each event out of the installed
`settings.json` (`${CLAUDE_PROJECT_DIR}` and all, launcher chain included) and drives both doors
through it — refused unrendered, opened once the record exists. Two further branches that had zero
red cases now have one each: `test_a_draft_named_only_in_an_option_description_is_refused` and the
third parameter of `test_a_record_whose_images_are_not_there_is_not_evidence` (`images: []`).

## 7. F7 — the kit property **[R2]**, F9 — the two wrong numbers **[R2]**

F7: see §1. F9: the selection collects **52** cases (`--collect-only`), not 23; and the shell-gate
measurement is **32 runs over eight gates**, not sixteen over four — the test now derives the gate
list from the kit's own registration instead of naming three.

## 8. The decisions, unchanged in substance

**Gate vs prose.** Gate: provenance (a named staged draft without a record over its current bytes).
Prose: whether anyone looked — measured, a record whose images are 20 bytes of ASCII is accepted.
DEC-0056: the error is the live Canyon case; the cost to the legitimate path is that the duty
attaches to the ARTIFACT (six silent cases measured) plus the browser dependency.

**Render route.** (i) the designer gets `Bash` and renders itself, because the images must reach the
SIGHTING role and a hand-back to another role is an orchestration step that can be skipped — the
failure class BUG-0076 measured. Costs: the shell surface (§4) and `hand_back: self`, which makes
`freeze-design` reachable from the designer's session with nothing but prose behind the rule.

## 9. Red-first

19 mutations in `…\TSK-0099\clone` plus one faithful restoration of the first-cut reader
(`redfirst.py`, `redfirst_head.py`, `redfirst_f1.py`). Baseline 52 selected cases green, restored
green. Every new test has a measured red direction:

| mutation | RED |
|---|---|
| the gate decides nothing (**the shipped kit before this round**) | 23 cases, incl. all eight spellings, both space cases, both doors |
| **the first cut's tokenising reader, restored verbatim** | `bare file name`, both `…space_in_the_path…` cases (see below) |
| record matched by filename, not sha256 | `…edited_after_its_render…` |
| images not checked / may point anywhere | `…images_are_not_there…` (2), `…cannot_point_its_images_outside…` |
| the stop door removed / judges every subagent / one-retry removed | `…stop_door_judges_only_a_role_that_could_render` (5 params), `…retry_is_let_through` |
| the question's options are not read | `…named_only_in_an_option_description…` |
| a record with no images is accepted | `…images_are_not_there…[images2]` |
| `seen` per item instead of per source path | `…sibling_draft_that_was_never_rendered…` |
| the renderer writes a record on a failed run | `…fails_loud_and_never_writes_a_half_record` |
| the gate refuses even a covered draft / every question / judges `.svg` | `…presentation_opens…`, `…measures_provenance…`, `…both_doors…`, `…is_silent_where_there_is_nothing_to_look_at` (6 params) |
| the role text claims the shell is bound by `allowed_scope` | `…product_designer_can_look_at_its_own_draft…` |
| the designer has no command tool | 4 cases |
| a second kit ships the loop | `…design_loop_ships_where_a_draft_is_judged_by_its_LOOK` |
| the render script's name puts the state dir on the command line | `…render_command_this_gate_prescribes…` (2) |

**Honest note on the second row:** restoring the first-cut reader verbatim turns three cases red on
this machine, not eight — the drive letter its token pattern dropped happened to be the hook
process's own current drive, so `/Users/...` resolved back to the same file. That is luck of the
layout; the whole matrix has its red direction through the first mutation. The test docstring says
this in the same words.

## 10. Suites (DEC-0050 — the full `tools/` suite stays the lead's delivery step)

`tools/test_hooks.py`, `tools/test_role_contracts.py`, `tools/test_shortening_net.py`,
`tools/test_hooks_v2.py`, `tools/test_kitupdate.py`, `tools/test_presets.py`,
`tools/test_repo_hygiene.py` — results in the report. `ruff` clean, `validate.py` clean,
`bump_kit_version.py` run last.

## 11. Not closed, named

`docs/POST_V2_WISHLIST.md` → **H82**, nine measured limits (a)–(i): the mention that never writes
the name out and the prose before the question; the name-collision over-refusal; the record as
self-report; the stop door's remaining over-reach; the shell surface; `freeze-design` reachability;
no browser ⇒ no presentation; the shared one-retry pass-through; and research-team as a reasoned,
two-way-pinned exemption.

## 12. Two honesty additions after the verifier's PASS on `2026.08.31-5` (N1, N2)

Nothing about the gate's behaviour changed; both are additions the verifier asked for so his
measurement keeps carrying.

* **N1** — H82 (b) and the ENFORCEMENT row already named the name-collision over-refusal, but
  nothing measured it, so the direction could flip unnoticed.
  `test_a_staged_draft_sharing_a_file_name_over_refuses_and_that_is_the_price` now measures it in
  both directions: with `staging/TSK-0009/index.html` staged, all three of the verifier's sentences
  ("src/index.html ist fertig — abnehmen?", "frontend/public/index.html ist gebaut", "Die
  index.html ist noch offen") are rc 2; with the colliding draft removed and an ordinary
  `DSN-0001.html` staged instead, the same sentences are rc 0. Red-first, both directions, in the
  clone: restoring whole-path matching (the F1 regression) turns all three red, and refusing every
  question turns all three red. The product-designer skill now names the convention
  (`DSN-nnnn.html`, `WFR-nnnn.drawio.svg`) as what keeps the collision unlikely, and says outright
  that nothing enforces it.
* **N2** — one sentence in H82 (d): on a refusal the `SubagentStop` chain breaks BEFORE
  `gate_dispatch`, so the child's end is not booked. Inherited from `gate_subagent_output`, where
  it is intended (the child keeps working); here it now also touches roles that have nothing to do
  with the draft.

Suites after these two: `tools/test_hooks.py` 876 passed / 13 skipped,
`tools/test_shortening_net.py` + `tools/test_role_contracts.py` 63 passed, `ruff` clean,
`validate.py` clean. New stamp: **dev-team `2026.08.31-6`** (`content: 234c7e12d636edf0…`),
office-team and research-team unchanged at `2026.08.31-3`.

## 13. The counted residual L24 gained one place (found after the -5 PASS)

`tools/test_kernel.py::test_the_path_rule_stops_at_the_kernel_package_and_the_rest_is_counted` was
red from the first version of this round onward — measured red across `-4`, `-5` and `-6` — and it
sat outside the verifier's selection. `kit_design_render.staging_dir` composes
`project_memory/staging/<id>` by hand, which is the eighth such place in shipped code outside the
kernel package.

**No code change, and that is the decision rather than an omission:** the three repo template
scripts run IN the project and stdlib-only (their own headers say so); there is no `ProjectState`
to ask there, and importing the kernel would give up exactly the kernel-free path L24 describes.
So the residual grows by a number and an entry:

* `tools/test_kernel.py` `_COMPOSITIONS_OUTSIDE_THE_PACKAGE` 7 → 8. The pin is two-way by
  construction, so the count keeps failing in both directions.
* `docs/POST_V2_WISHLIST.md` L24: `kit_design_render.py` (`staging`) added to the named places,
  with what a rename of `staging/` would cost here (the renderer writes into nothing and
  `gate_design_sighted` refuses every presentation, because it looks for the record at the old
  place), plus the sentence that the three template scripts share one reason.
* The test's own docstring stopped enumerating the places ("the hooks' bridge ... and two template
  scripts") — that sentence had gone false while the count beside it did its job. One statement of
  one fact, in L24, which the docstring's first line already points at.

**Nothing under `team-kits/` was touched in this step**, so the seven files the verifier checked
byte-identical stay byte-identical and the stamp does not move: `git status team-kits/` shows the
same set as before, and `bump_kit_version.py` reports all three kits unchanged.

Verification: `pytest tools/test_kernel.py -k path_rule` 1 passed. Hole-list tripwires:
`tools/test_disposition.py` 8 passed, `gen_known_holes.py --check` up to date,
`tools/test_kernel.py` + `test_repo_hygiene.py` + `test_migrate.py` 265 passed, and the hole-list
readers inside `test_hooks.py` / `test_role_contracts.py` / `test_shortening_net.py` 5 passed.
`ruff` clean, `validate.py` clean. Stamp unchanged: dev-team `2026.08.31-6`.
