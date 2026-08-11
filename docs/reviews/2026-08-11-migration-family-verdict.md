# Migration-engine family — Verifier verdict (TSK-0039..0042 / BUG-0026..0029), 2026-08-11

Shared kernel (`team-kits/kernel/`, one migrate.py/report.py, not mirrored). Measured against the
working-tree state in a local hardlink clone outside the repo (`git clone --local` + worktree overlay
— the verifier first mis-measured via PYTHONPATH because `test_migrate.py:41` inserts ROOT/team-kits,
overriding it; corrected). Verdict: **PASS**, no residue-list entry.

## BUG-0026 (blocking, data-loss) — closed and held under direct measurement
`record_deposit_of` now carries `_body_digest(body)` (sha256 via `yaml.safe_dump sort_keys=True` —
`canonical_json` throws TypeError on the `datetime.date` fields of a V1 record; docstring reason
confirmed). Measured: `_body_digest` deterministic (twice byte-equal), order-independent (different
dict insertion → same digest), content-sensitive (140 vs 90 steps → different). No time component in
the body (`_with_legacy` builds it from record/plan; the `created` placeholder lives only in
`item_size`). So: same body → same name (idempotent, no double-deposit); edited body → new name (no
overwrite). The iterative-shorten data-loss chain is closed; the first deposit stays byte-unchanged.
Red-without-fix reproduced (digest removed → identical name, overwrite).

## Name-scheme injectivity (the other data-loss risk) — no collision
`record`/`doc` deposits under `staging/`, `overflow` under `../v1-legacy-overflow/` (different dir);
encoder injective, case-fold-safe (`PROC-0811A` vs `-0811a` differ). A real document rel (a file) can
never equal `rel/PROC-XXXX/<64hex>`.

## BUG-0027 — READY line carries the build flags (deterministic sort); the pasted line runs rc 0 (red without fix: `--map` missing). BUG-0028 — deposits are their own DEPOSIT coverage class, counted not listed (red without fix: not_searched grows 1→7). BUG-0029 — honest reasoned gap: the `version:` line is identical across dev/office/research (`2026.08.11-4`), only `content:` differs, so doctor's version line genuinely does not point at a kit; with `kit_state.json` present the kit IS named and `kit_reason` empties (second test half real).

## Acceptance
`test_migrate.py` 141 passed (self-run); full suite 2455 passed / 13 skipped (implementer-measured);
ruff clean over the changed files; stamp 2026.08.11-4 consistent across the three kits. Docstrings /
WISHLIST (L32/L35) checked against the code (Hausregel 3), including the over-long deposit name
carried as a fail-safe residue (unexecutable instruction, loses nothing).

## Not measured (named)
Full tools/ suite taken as implementer-measured; the synaipse pilot copy not separately re-migrated
(the office V1 template chain from real git history covers the same path); a `--map` value with shell
metacharacters in the unquoted READY line not executed — analysed fail-safe (plan_digest covers the
whole plan → a shell-split paste rebuilds a different plan → rc 2 usage error, no state touched).
