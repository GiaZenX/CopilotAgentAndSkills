# TSK-0079 close-out protocol (lead, 2026-08-21)

Round: FR-0053 — Board v2 (modal detail, real tabs, two hierarchical backlog views). Last
pre-pilot round. Two verifier rounds: FAIL(B1/B2 + N1..N5) → **PASS**.
Report: docs/reviews/2026-08-21-tsk0079-measurements.md.

## What shipped

- kernel/backlog_tree.py (new): tree derivation from REAL link fields only (PARENT_FIELDS),
  placement under the deepest resolvable parent, five distinct rejection reasons, orphans land
  in a visible Unassigned group WITH a warning — nothing vanishes from the trees.
- kernel/board.py: real tabs (button-driven, only the active view visible in the DOM), a full
  modal per item (all fields; id-shaped strings the board knows become clickable reference
  buttons — escape-then-link, no field list), archive counts, one interpolation-free inline
  script, a no-script fallback that shows everything openly instead of dead chrome.
- Click-through measured in a real headless browser by BOTH roles (card → modal → reference →
  other modal → Escape → tab → tree row → close); no-script probe via sandboxed iframes;
  hostile stores through the real write path found no injection (both roles' own payload sets).
- The loop's catches: B1 — the TSK-0071 alias-bomb property had RETURNED in the new module
  (str() on a binding-field container; 535 bytes → 97.8 s/480 MB) — closed as skip-containers +
  set-dedup (0.03 s), red via a memory-bound test; B2 — the hostile-id test fixture was an
  unreadable YAML stream so the attack never arrived — fixed with one safe_dump + ARRIVAL
  asserts (a fixture that fails to deliver its attack now goes red itself); the implementer
  additionally exposed two of his OWN round-1 red-proofs as invalid (placeholder-count
  TypeError) and struck them through — replaced by measured ones.
- This repo renders its own board too (208 cards, 465 KB, ~0.5 s per state write; scaling
  measured linear to 2000 items).

## Named deviation → USER QUESTION at release

The page (incl. the new lead paragraphs, type labels, warning templates, unassigned copy,
noscript hint) is ENGLISH; FR-0053 named the tabs in German. Deliberate one-language choice —
the whole-page language for the plain-language audience is the user's call; carried to the
release conversation with the verifier's mechanism statement.

## Bookkeeping

- radar/2026-08-21-claude.md appeared untracked mid-round: the weekly radar-watcher's scheduled
  report, not part of this package; committed alongside as its own dated artifact (precedent:
  2026-08-16 report rode with the A2 commit).
- One cosmetic residue named for the next touch of backlog_tree.py: the no-finite-verb comment
  overshoots its own templates (the built property is no verb AGREES WITH {plural}).
- FR-0053 → MERGED, archived. FR-0054 (BUG→SR link) stays the post-release refinement.
  TSK-0079 → CANCELLED, archived.

## Residues (named, non-blocking)

- Click behaviour has no in-suite regression guard (no browser in pytest); DOM state + the
  script↔markup coupling are guarded; the click itself is measured in both roles' reports.
- A root type never nests (PROC with derives_from stays root — pinned by test).
- unassigned-off-view merges wrong-branch and cycle (message true in both).
- Archive count walks the archive per state write (unmeasurable at 91 items; no invented cap);
  the except-OSError branch is unexercised.
