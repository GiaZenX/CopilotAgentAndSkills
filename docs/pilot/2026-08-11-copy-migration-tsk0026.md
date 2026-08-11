# Copy-migration pilot (TSK-0026) — migration engine against real projects, 2026-08-11

Engine from committed HEAD `c188d5f` (`git archive`), run against working copies of the three
staged real-repo copies; the real originals were never named (DEC-0026). Raw data:
`C:\Offline Repos\_verify-tsk0026\out\`. Verdict: **FAIL** (B1 blocks); the pilot itself ran fully.

## What holds (measured)
- **Originals byte-identical before/after** every run (sha256 over path+size+content):
  synaipse-KOPIE 5114 files, portfolio 9493, BuyPlugGo 7070 — all unchanged.
- **DEC-0024 injectivity holds on real field paths:** 64 printed COPY remedies, 64 distinct targets,
  0 named twice, 0 occupied, **0 overwrites**. Longest deposit name 77/255 chars (L32 overflow not
  reached by real data).
- **End-to-end clean:** synaipse 633 items written (receipt DEC-0070), portfolio 207, BuyPlugGo 16
  (DEC-0001); `validate` 0/0 on all three; idempotent (2nd dry-run → NOTHING TO DO, rc 0);
  V1 source docs are MOVED to legacy/, origin paths empty; counts reconcile (373 import + 260
  archived-unresolved = 633).
- **migrate-round2 residues re-checked on real data:** R-c (dotted path) closed for YAML (case-
  insensitive suffix; `.YAML`/`.yml` searched), open+named for non-YAML `.bak`/`.txt` (L19/L20);
  B5 (backlog type w/o table row) closed — refuses with a HARNESS-gap message instead of guessing;
  B6 (parent chain) closed on real data — 756 bindings, 0 mismatches, 353 items got a different V2
  id, 243 bindings rewritten correctly.
- Runtime measured: 633 items = 475.7 s (~0.75 s/item, capture takes the lock per item).

## B1 — BLOCKING: `record_deposit_of` omits the digest while the remedy tells the reader to change the source
`team-kits/kernel/migrate.py:358` (`record_deposit_of`), call site `:2012-2019`, claim `:274-309`
(`deposit_of`) and `docs/POST_V2_WISHLIST.md:1490-1496`. The printed remedy for an oversized RECORD
says: "COPY it ... to `staging/v1-deposit--…` Then shorten the record in the V1 file itself ... and
re-run". So the source DOES change — breaking the premise `deposit_of` derives safety from ("the
original stays where it is"). `overflow_deposit_of` (`:333`) puts sha256 in the name for exactly this
case; `record_deposit_of` does not.

Measured chain (real synaipse ADR-0013, real processes): dry-run → "21440 bytes / 292 lines" + the
remedy; reader copies (deposit 10556 B) then shortens the record too little; dry-run again → "18155
bytes / 244 lines", SAME instruction, SAME target; reader follows again (deposit 8952 B). **1604
bytes of the original record now exist in no file** — removed from the V1 file (step 3) and from the
deposit (step 5). In-session chain. Not in the wishlist. The message states the ITEM size, not the
record-text size, so the reader cannot compute the cut and shortens iteratively — the normal case.
Fix: sha256 in `record_deposit_of`'s name (like `overflow_deposit_of`), or an `_is_occupied`/
`_occupant_digest` check at the call site (both exist, `:616`/`:627`) that prints the conflict rather
than the remedy when the bytes differ.

## B2 — residue (medium): the READY line omits the flags the plan was built with
`migrate.py:2545` builds `READY: … --plan %s` from `plan_digest(plan)` only; `build_plan` took
`field_map` and `archive_year`. The one copy-paste line is always wrong once any flag was used
(2 of 3 copies) → rc 2 (digest catches it, no damage). `tools/test_migrate.py` has no assertion on
this line. Fix: print the flags in the READY line, or build it from the same source as the `--map`
remedy. Belongs in POST_V2_WISHLIST.

## B3 — residue (low): each applied NOT-SEARCHED remedy permanently adds another NOT-SEARCHED line
`migrate.py:664-671`. synaipse: 26 → 62 NOT SEARCHED after applying 26 deposits; no command removes
a deposit and the instruction names no way back. Fix: count deposits as their own coverage class in
validate/doctor rather than listing them line by line.

## B4 — note (low): doctor cannot name a V1 project's kit
`"kit": "unknown"` with `"kit_version": "2026.07.18-3"`. `generate-session-brief` requires `--kit`;
the obvious source (doctor) does not supply it.

## Synthetic bench vs real project — classes that appeared ONLY on real data
Oversized records (10 ADRs, the only trigger of B1); one missing field cascading to 391 blockers
(SR-0096 no status); mass undated records (196 SR blockers → `--archive-year`); foreign id schemes
(ACC-/AC- 194+75 "id-shaped but not items"); Codex surface (`.codex/hooks.json` flagged by doctor);
office business data (`filing_log.yaml` 590 KB → CARRIED, NOT TRANSLATED with hash); non-ASCII in
real YAML handled cleanly.

## Coverage gap named (important for "belegt fertig")
**No V2 kit was installed over a migrated project.** So nothing is measured about: real hook processes
against a 633-item state, the 60 s budget, `gate_memory_complete`/`gate_filing`/`gate_write_scope`
against migrated stores, and the **entire wall branch** of the engine (`walls_of`,
`absorbed_documents`) — `gated_documents` was empty in all three (the copies carry V1 hooks, so the
migration saw no wall). This is a distinct pilot still owed before dev-team is "clean finished".
