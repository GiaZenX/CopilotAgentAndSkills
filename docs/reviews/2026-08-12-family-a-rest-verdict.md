# Family A rest — Verifier verdict (TSK-0049 BUG-0002, TSK-0050 BUG-0003), 2026-08-12

Office-only shell classification (`_filing.py`, `guard_fs_tripwire.py` — no dev/research mirror;
`_compat.py` byte-identical and untouched). Runtime accepted against the frozen office `2026.08.12-3`
(content hash `34266b16…`).

## A concurrency note (process, corrected)
The first verification overlapped a still-writing implementer (the CLAUDE.md scar — "separate trees
are not separate verification"): its first battery measured stale source (-2) and flagged holes, then
re-measured the fresh source (-3) and found them closed. Resolved by serialising: the implementer was
stopped, the tree frozen, and one clean verifier run made against the frozen -3 state.

## Runtime — PASS (verified against the frozen tree, clean full suite)
- **BUG-0002** (`guard_fs_tripwire.moved_out_of_the_archive`, `_filing.SOURCE_DELETING_FLAGS`): a
  robocopy/rsync with a source-deleting flag out of the archive is a move, refused: `/MOVE`, `/MOV`,
  `/move`, spliced `/MO'VE'`, `rsync --remove-source-files`, `rsync --remove-sent-files` (deprecated
  alias), `mv`, `Move-Item`, `git mv` → rc 2; a real copy (no flag), `/MIR` (purges the DESTINATION,
  no move-out) → rc 0. Residue named: `tar --remove-files` (not a copier verb) in POST_V2_WISHLIST.
- **BUG-0003** (ledger redirect + filing): one shared resolved-target reader `_redirect_targets_in`
  now serves both the ledger rule and `created()`. `>|` / `1>|` / `>>|` (noclobber-override) and a
  line-continuation in the target — both closed by `gate_write_scope` and previously OPEN here — are
  now rc 2, with real file effect measured; `cat`, `< ledger`, `2>&1`, non-ledger redirect,
  `ledger_add.py` stay rc 0. The same fix closes a blind archive write (`cat a >| archive/…` → rc 2,
  filing without the filing-plan check). Residues named: `dd of=` (write inside another program),
  the backslash-reading of `created()`.
- Clean full suite against the frozen copy: **2489 passed, 13 skipped, 0 failed** (the earlier
  `id_scan_is_linear` failure was host-load jitter — green in the load-free run and isolated).
  Red-without-fix reproduced for `>|` (lookbehind) and the continuation join.

## The one blocking finding — a self-referential tripwire — now fixed
`test_fs_tripwire_reads_a_source_deleting_copier...` iterated its cases FROM the very map it guards
(`SOURCE_DELETING_FLAGS`), so dropping a flag dropped its case and nothing went red — the round's
deliverable `--remove-sent-files` had no test that fails without it (Hausregel 4), and the docstring
claimed a catch the loop did not build (Hausregel 3). Measured: dropping it → test green, behaviour
rc 2→rc 0.

Fixed (test-only, `tools/test_hooks.py:7987-8023`) exactly as the verifier specified: an INDEPENDENT
literal `KNOWN_SOURCE_DELETERS` (a hardcoded second source, not derived from the map) asserts each
measured deleter IS in the map AND turns the copy into rc 2; the KeyError sample-honesty and the
`/MIR`/no-flag over-inclusion ends stay. Docstring corrected to describe what is built. Red-without-
fix proven by the implementer (dropping `--remove-sent-files` → AssertionError; dropping `/move` →
AssertionError). Suite 2489 passed, no stamp (a test file is not a kit-hash input).

## Lead confirmation of the delta (measure, not assume)
Since the runtime PASS: office content hash is still `34266b16` — the runtime files are byte-identical
to the verified state; only `tools/test_hooks.py` changed (+95 lines). The lead read the new test and
confirmed `KNOWN_SOURCE_DELETERS` is a genuine independent literal. Runtime verified by the verifier;
the tripwire fix is verifier-specified, red-without-fix proven, and delta-confirmed test-only.
