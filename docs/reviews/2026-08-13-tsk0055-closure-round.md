# TSK-0055 — closure round (archiving), 2026-08-13

## What ran

The active item store overstated open work by an order of magnitude: statuses had never been
walked because this repo drives the kernel directly, without a kit — and the kernel's own guards
make the "finished" terminals unreachable here (no leases, no approval mint). Policy **DEC-0041**
decides what closing honestly means under that constraint; hole-list entry **H39**
(docs/POST_V2_WISHLIST.md section 12) carries the measured unreachability.

Assessment (STEP 1) ran as a read-only subagent producing one proposal file, now preserved as
`docs/reviews/2026-08-13-tsk0055-assessment.yaml`: one verdict row per active TSK/FR/DEC item,
each with its proof (EVD ids, commit hashes, file:line). Completeness was checked against the
directory file counts (53 task files = 52 rows + TSK-0055 itself; 17 FR; 39 DEC — match).
Execution (STEP 2) ran entirely through the kernel: `transition` + `archive` per item, no
hand-edited state.

## Before / after

| Type | active before | active after | archived by this round |
|---|---|---|---|
| TSK | 53 | 4 | 49 (30 delivered, 19 superseded — all CANCELLED per DEC-0041a) |
| FR | 17 | 16 (all TRIAGED with `triage_result`) | 1 (FR-0001 CONVERTED: the todo gate exists) |
| DEC | 39 | 39 | 0 (no active decision is superseded — measured, see assessment `dec_note`) |
| BUG | 30 | 29 | 1 (BUG-0019, already REJECTED — validator remedy, not a new verdict) |
| SR / PR / EVD | 8 / 3 / 23 | 8 / 3 / 23 | untouched (standing requirements, live roots, evidence) |

`validate`: **0 errors, 1 warning** after the round. Before the round it was 1 warning (BUG-0019
awaiting archive); the "6 warnings" a mid-round run showed were the 5 staging dirs freshly
orphaned by the archiving itself, not a pre-existing state. The staging prose of archived TSKs
(verdicts, wishlist drafts for TSK-0018/0020/0021/0029) moved to
`docs/archive/staging-of-archived-items/` — preserved, not deleted. The TSK-0022 staging dir went
with them at first and CAME BACK: the round verifier caught that the active evidence records
EVD-0001/0002/0003 point their `artifact_refs` into it, and an EVD is immutable (the kernel
refuses the edit — a record of something that already happened). So the file's place is fixed by
its referees, and the one remaining warning ("orphaned staging dir TSK-0022") is the named price —
its own wording is imprecise, since the orphan heuristic reads tasks and roots but not EVD
`artifact_refs`; that reader gap is captured as **BUG-0032** (kernel-side, `report.py:496`), so it
has a status instead of living only in this prose.

## What stays active, and why

- **TSK-0009** — the SR-0008 comment-discipline rule was never mirrored into the role definitions
  and BUG-0012 is unfixed (measured: no `.claude/agents/*.md` references SR-0008).
- **TSK-0027** — pilot 3 (invoice tool) and the three-pilot comparison never ran; only the game
  pilot delivered.
- **TSK-0033** — the BUG-0015 scalar-roles fix in `process_doc.py` never ran (file untouched since
  before the item existed).
- **TSK-0055** — this round; closes CANCELLED + archived once its verifier verdict is in
  (the same DEC-0041a path it applied to the others — `DONE` is as unreachable for it as for them).
- **16 FR items** — real, still-wanted wishes, each now carrying a measured `triage_result`.
- **29 BUG items** — deliberately NOT assessed (DEC-0041d): a fixed bug cannot honestly reach
  `VERIFIED` here (H39), and REJECTED/DUPLICATE would be lies. This round asserts NO per-bug
  fixed/open split; that overhang is named, visible, and grows until a mint path exists.
- **39 DEC / 8 SR / 3 PR** — standing decisions, standing requirements, live roots. Not backlog.

## Corrections after round verification (the verifier's F1–F10)

The round verifier FAILed the first cut of this package and every finding was resolved before the
commit: **F1** H39 was missing from the section-12 overview table (the repo's own
`test_the_hole_list_judges_every_entry_it_carries` was red — row added, provenance line extended,
test green again). **F2** H39 claimed `.claude/settings.json` is "unwritable from inside" — wrong:
gate 1 refuses it to the SESSION agent only, an implementer subagent may write it; the sentence now
says what the gate builds. **F3** the moved TSK-0022 staging dir broke three active EVD
`artifact_refs` — moved back, see above. **F4** FR-0011's triage_result claimed "still one serial
suite" while the file runs cells through a ThreadPoolExecutor — re-measured and rewritten (the
FR's actual cut stays unbuilt; a full run still exceeded 580 s). **F5/F6** two numbers in this
report did not survive re-measurement (warning count, file count) — corrected above. **F7** one
diff prefix typo in the assessment (e37642a3→e37642a7) — corrected. **F8** two disclosed
deviations stand: BUG-0019's archive rode the validator's remedy line (not DEC-0041), and the
assessment lives under docs/reviews instead of staging. **F9** the EVD column (23 active) was
missing from the table — added. **F10** DEC-0007 announces a supersession of SR-0006 whose
condition (TSK-0007's verification chain delivered) has since occurred; DEC-0041e keeps SR items
untouched, so it is NAMED here as due follow-up work, not executed.

## Gate suite

A clean full run of `.claude/hooks/test_gates.py` AFTER the rework: **143 passed in 4512.42 s** —
including `test_the_hole_list_judges_every_entry_it_carries`, which was red before the F1 fix. The
verifier's earlier full run (started pre-rework, contaminated by its own parallel measurements)
showed 2 reds that did not reproduce idle; that load-dependent flakiness is owned as **BUG-0033**
(a red from the timing test cannot be told apart from a genuinely slow gate). `python -m pytest
tools/` was not run: the round touches no product code, and `tools/bump_kit_version.py` names no
docs/ path — no version stamp is due.

## Honest limits

- `CANCELLED` on the 49 closed TSKs does not mean "not delivered" — it is the only reachable
  terminal (H39); the delivery verdicts live in the related EVD items, commits and
  `docs/reviews/` verdict documents, which the assessment rows cite one by one.
- The assessment's verdicts are single-sourced (one agent); the round verifier spot-checks them
  against the cited proofs before the commit — its verdict is recorded as the round's EVD.
- BUG rows: see above — no claim made.
