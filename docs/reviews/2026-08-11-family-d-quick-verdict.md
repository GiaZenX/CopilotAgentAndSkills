# Family D quick batch — Verifier verdict (TSK-0036 BUG-0025, TSK-0037 BUG-0008), 2026-08-11

## Verdict: PASS

Independently reproduced in a git sandbox outside the repo (`git archive HEAD` + overlays).

### TSK-0036 / BUG-0025 — CRLF inflation of the lead package
`.gitattributes` changed from an enumeration (`*.py`/`*.sh`/VERSION `eol=lf`, no `.md`) to the
definition `* text=auto eol=lf` (+ `*.woff2 binary`). The enumeration-without-`.md` WAS the bug; the
definition closes the class (`.yaml`/`.json`/`.txt` too).
- Defect→fix reproduced: defect archive carries `.md` as CRLF (AGENTS.md 24204 B, 243 CR) →
  `lead_package.size` dev 31006 > 30674 → `tools/validate.py` rc 1. Fix → `.md` LF (23961 B) →
  30674 = record → rc 0.
- Definition edges safe: no `.bat`/`.cmd`/other CRLF-needing tracked file; `.woff2` is the only
  binary type and its `binary` pin wins (`text: unset`); a synthetic `.png` with NUL is auto-detected
  as binary under `text=auto` and not mangled on an autocrlf checkout.
- Kit content hash unaffected (stronger check than `--check`): `kit_hash(dev-team)` LF == CRLF ==
  `9acc74ace052b199…` (`hashing.py:249` normalises `\r\n`→`\n`).
- Red test `tools/test_context_budget.py::test_every_file_the_package_weighs_checks_out_lf` derives
  files from `lead_package.files` and queries `git check-attr eol` (the running attribute
  resolution, not a string search). Old attrs → 6 `.md` `unspecified` (RED); new → `lf` (GREEN).

### TSK-0037 / BUG-0008 — tracked tool trace
Item was wrong: the file was tracked and in HEAD, not untracked; the b32ec98 `.gitignore` rule was
dead and its comment overclaimed. Fix: `git rm --cached -r Microsoft/` (file stays on disk + in HEAD,
reversible; a staged index deletion, correctly part of the changeset, non-destructive). Comment
corrected, new test `tools/test_repo_hygiene.py`.
- `git ls-files --cached --ignored --exclude-standard` → only `project_memory/.audit/hook_events.jsonl`
  remains; the rm is complete.
- Red test `test_git_tracks_no_ignored_file_outside_canonical_state` both ends; tripwire
  `test_the_known_out_of_scope_trace_is_still_the_only_exception` stable.
- Named residue (not a hidden defect): `project_memory/.audit/hook_events.jsonl` is the same class but
  in forbidden scope — `git rm --cached` on it is refused by Gate 1 (measured). Carried as H37 Rest 2
  in POST_V2_WISHLIST; the fix belongs in the kit (the kit hook writes it).

### Interaction / acceptance
`git add --renormalize` is a content no-op (all text blobs already `i/lf`) — no byte-size/mirror/hash
record shifts. `.gitattributes`/`.gitignore` are not in `kit_hash_inputs`. Targeted
`pytest tools/test_context_budget.py tools/test_repo_hygiene.py` → 39 passed. Full suite 2447 passed
/ 13 skipped, ruff clean, validate rc 0, stamp unchanged (taken as implementer-measured; kit-hash
equality independently confirmed).

### Non-blocking cosmetic (folded into the ruff round)
`tools/test_repo_hygiene.py` lacks a `shutil.which("git")` skip guard (bare `subprocess.run(["git"…])`)
— cosmetic (git always present here); the sibling context-budget test guards it.
