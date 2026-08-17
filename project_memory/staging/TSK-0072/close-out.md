# TSK-0072 + TSK-0073 close-out protocol (lead, 2026-08-17)

Round: BUG-0047 (role memory prescribed-and-impossible) + BUG-0048 (shell-less specialists
cannot submit) — one family, one writer, worked 0073-first. Block A, round A3a.
Three verifier rounds: FAIL(B1..B4 + N1..N7) → FAIL(B5 + N8..N11) → **PASS**.
Report: docs/reviews/2026-08-17-tsk0072-tsk0073-measurements.md (§1-6, §4a/4b/4c, lead
corrections appended after the PASS).

## What shipped

TSK-0073 — the submit contract derives per role which of TWO return paths applies:
- kernel dispatch derives `hand_back: lead|self` from the role's own tools frontmatter
  (COMMAND_TOOLS, no role list) into lease + dispatch header; `submit-result --from` lets the
  lead book in a shell-less specialist's envelope file from staging/<TSK>/ — the kernel stores
  the specialist's OWN bytes. Constitutions x3 (§6/§0), lead role texts x3, harness.py x3.
- The one place demanding a command line from EVERY dispatched role was the constitutions'
  checkpoint sentence — now qualified. 8 shell-less dispatchable specialists across the kits,
  derived, and AC-1 is a derivation: a synthetic role added in a clone is judged with no other
  edit (verifier-measured).
- Coverage the verifier forced in: a parametrised escape battery over `submit-result --from`
  (shared ESCAPE_SHAPES, runtime placeholder both batteries resolve) plus an AST floor that
  demands a battery for every kernel caller of staging.contained_child; the os.path.join
  mutation goes red twice. A derived lead-relay test (every kit with a shell-less role must
  carry the relay paragraph in its lead text) — red with three findings on ablation.

TSK-0072 — role memory gets a real, narrow door (window built, duty kept):
- Rule 6 in gate_write_scope (_own_craft_memory): a bound OR unbound subagent writes
  agent-memory/<its own role>/** and nothing else outside its task scope; all three conditions
  derived (payload agent_type, kernel.presets.AGENTS_DIR, guard_memory_budget.MEMORY_DIR).
  Task scope stays closed after submit (measured).
- The loop's main story: the window's first two shapes were HOLES the verifier found and the
  round closed — (1) payload forms guard_memory_budget cannot model (empty/absent old_string,
  MultiEdit, missing content key, NotebookEdit, notes.txt) opened without a content verdict →
  closed by asking the guard (`judges_this_write`), fail-closed; (2) gate and guard judged
  DIFFERENTLY SPELLED names (realpath vs abspath — ADS `::$DATA` and 8.3 short names measured
  in-session) → closed as ONE derivation `guard_relative`, two readers, no rel parameter.
  Both representatives of the spelling class MEASURED closed (verifier reproduced 8.3 in his
  scaffold; the report's own caution on this is corrected in its tail note).
- `memory:` added to the two duty-carrying roles that lacked it; MEMORY_DUTY_RX as the single
  definition of the duty; the shell refusal names the real door and its narrowness.

## Verifier PASS (round 3), self-measured

Full round-2 battery replayed as non-regression (six B1 forms refused, six legit forms allowed,
AC-2 refusals intact, six narrowness directions unchanged); B5 closed in both spellings plus
nine evasion spellings, both readers agree everywhere; N8 verdict movement judged acceptable
(a refusal of a no-op call was a warning, not a protection; ids still cannot LAND either way);
ablations red for every new direction; mirrors sha256 x3, stamp 2026.08.17-7, pins current,
sizes on record (+1731/+1724/+1701 B over three journaled steps); suite 2794 passed/13 skipped
reproduced; test_gates 243 passed.

## Hole list (this commit)

- **L6 → CLOSED and corrected** (it misnamed the trigger: the memory was locked at EVERY point,
  not after submit-result). Rewritten with the built rule 6, the deliberate shell-way refusal,
  and the named over-refusals: unmodelled payload forms (notebook/Codex apply_patch) and
  non-flattened spellings fall OUT of the window by design; closing direction = modelling those
  forms in the guard ("phase 3"); the main()-realpath question is an OWN future decision, not a
  side effect.

## Bugs stay TRIAGED (established pattern)

BUG-0047 and BUG-0048 remain TRIAGED in bugs/active — the BUG chain's APPROVED step needs a
user-minted approval this kit-less repo does not run (same as every fixed bug here; H39
terminal honesty). The fix record is this protocol + EVD + the report.

## Deviations / residues (named, non-blocking)

- submit-result still carries no caller identity; --from only changes whose bytes are stored
  (pre-existing; §6.5 of the report).
- The two-path split is an offer, not an enforcement — deliberate: the lead must be able to
  book in a crashed child's result (§ N6, constitutions phrased honestly).
- The LEAD may write any role memory (pre-existing; product question, named not decided).
- `memory:` provider effect is unmeasurable from this repo — the tests hold the contract
  contradiction, not the provider behaviour.
- office/research end-to-end ran derived-only (dev scaffold built; hand_back derived over all
  three kits); junction/symlink spelling closed by the same derivation, not separately built.
- N8's disclosed verdict movement: an Edit with absent old_string on a file already carrying
  ids flipped rc 2 → rc 0 — judged acceptable (no bytes can land; Write there still refused).
- Round-2 report's "foreign hand" on docs/POST_V2_WISHLIST.md was the lead's announced H48 fix
  (TSK-0071 close-out); corrected in the report tail.
