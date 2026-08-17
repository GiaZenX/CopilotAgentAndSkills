# TSK-0071 close-out protocol (lead, 2026-08-17)

Round: FR-0030 — the dashboard HTML becomes the interim kanban backlog view. Block A, round A2.
Three verifier rounds: FAIL(B1..B7) → FAIL(C1/C2, narrow) → **PASS**.
Report: docs/reviews/2026-08-16-tsk0071-measurements.md (sections 1-8).

## What shipped

- `team-kits/kernel/board.py` (new, 395 lines): kanban board renderer — status columns derived
  from the automata (chain → side states → terminals), types = directories present (no per-kit
  table), cards title-only with a `<details>` fold, NO JavaScript, no external resource.
- `kernel/state.py`: `_regenerate_index_locked` renders `generated/board.html` WITH the index,
  one timestamp, same read loop; `_write_board` is fail-soft — a board failure can never fail a
  state write (warning with item id on stderr; `errors="replace"` for exactly this write).
- B2 (verifier round 1): two kernel write paths regenerated nothing — `approvals.revoke` and the
  lease-expiry branch of `dispatch._validate_lease_locked`. Both fixed IN CODE (regeneration
  added), plus a CLASS tripwire test that derives writers-vs-regenerators from the AST and
  measures both ends (`test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind`).
- Hardening measured in by the loop: surrogate characters, alias bombs (depth marker `[…]` +
  `_Ink` character budget; red evidence 128 MB / 494.8 MB vs shipped 0.04-0.25 MB), per-card
  exception catch, open-file-handle fail-soft. The round found its own worst defect (recursive
  YAML anchor would have crashed EVERY later capture) before the verifier did.
- All three kits ship the board (READMEs name it; kernel is shared); freshness prose is
  CONDITIONAL on all five spots (three READMEs, page footer, state.py docstring) — it claims
  exactly what the code builds.
- tools/test_board.py (new, 639 lines, 21 tests): every test red-capable, measured by ablation
  in both verifier rounds; tests parse the rendered page (HTMLParser over data-* attributes).

## Verifier PASS (round 3), self-measured

All C1 mutations red (str()-at-bound 128 MB, budget-off 494.8 MB, marker assertion catches the
unfold when the memory bound is loosened), the round-2 blind spot is the shipped state and goes
red; both bomb shapes proven necessary; 28 test names in kernel comments resolve, 0 unresolved;
stamp 2026.08.17-2 all three kits; full suite 2779 passed / 13 skipped (implementer run, verifier
reproduced 2778+1 with the +1 isolated as a host-load artifact and green alone); test_gates 243
passed (both roles independently).

## Hole list (this commit)

- **H48 → NEW, OPEN as a deliberate trade**: an open read handle freezes the board page for the
  session (Windows os.replace); the fail-soft keeps the STATE writing — the page keeps its stamp
  and the only active signal is a stderr line the hook path practically never reads. Chain
  measured by the verifier; browser-against-file:// unmeasured. Closing direction if it shows up
  in practice: a session-brief line "board older than index".

## Deviations / residues (named, non-blocking)

- Item wording: expected_outputs STEP 3(c) was reworded by the lead after verifier B6 judged the
  implementer's substitution COVERED (the board has no view→type assignment; the vanishing risk
  lives at status level and is measured in both directions).
- dev-team now has TWO overviews (board.html automatic, dashboard.html on demand). Merging them
  would cost the vitals panel (kit code the kernel must not import) — a product question for the
  user, post-release.
- The fold shows every field, incl. the CONSUMED mint_code of a minted APR (approvals/pending is
  not read; live codes are not on the page — verifier-measured both rounds).
- Title-less types (TSK/EVD/HYP/EXP) show only their id on the card face; sentinel columns
  `(no status)`/`(unreadable)` are strings a hand-written status could collide with (cosmetic).
- No card cap (linear ~1.6 KB/item) — a cap would make cards vanish, the exact FR-0030 failure.
- This repo's own board: `project_memory/generated/board.html` is rendered here too (kernel
  called directly) and is now .gitignored — never tracked, rule live from day one; index.yaml
  stays tracked (rollups refuse a store without it).
- Verifier precision note: the report's §8.1 numbers for the green case are host numbers, not
  constants (0.04 MB/0.017 s there vs 0.25 MB/0.044 s on the verifier host) — both far on the
  safe side of the asserted bounds.
- Kit hook registrations for gate_approval/gate_dispatch carry no `timeout` (pre-existing,
  already the TSK-0069 side observation); the renderer they now run is bounded in memory and
  output, a time limit only the registration can give it.
