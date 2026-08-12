# TSK-0052 (BUG-0011 / DEC-0039) — Verifier verdict: structural marker detection, 2026-08-12

## Verdict: PASS (two verifier rounds, one implementer rework between them)

Measured against a frozen tree in a copy outside the repo (robocopy without `.git`/`project_memory`);
the real repo read-only; real `session_status` processes throughout.

## Round 1 — the three ACs (verifier ae21f71)
- **AC-1 (occurrence vs. mention): PASS.** The running detector `session_status.py` anchors to the
  shim form `<!-- agents-and-skills:team-kit <team> -->`; the entry prose `user/claude/CLAUDE.md:12-19`
  is rewritten structurally ("first line … a mention elsewhere … does not count").
- **AC-2 (a test measures a mention NOT triggering): PASS.** `tools/test_handover_marker.py`, 12/12
  green against the real process; red-without-fix reproduced (the loose pre-predicate fails exactly
  the four line-1 mentions).
- **AC-3 (every "bare occurrence" check measured): PASS.** Audit `docs/reviews/2026-08-12-tsk0052-marker-audit.md`
  complete and honest; own grep found no hidden site.

Round 1 named ONE non-blocking residue (Befund 1): the shim predicate had no END anchor, so a line
`<!-- …dev-team --> this is NOT an install` still matched (informing banner only, not the handover
decision) — Hausregel 3 (comment/prose said "and nothing else", code allowed trailing text).

## Implementer rework — end anchor `\s*$` at all five read sites
`session_status.py` (three kits, byte-identical detection block), `tools/validate.py`, and
`scaffold_team.sh`/`.ps1` (legacy ownership-recovery, previously an unanchored line-1 search) all
pulled to the same anchored shim form. "One definition", not an enumeration.

## Round 2 — the end-anchor delta (verifier ae4f28f)
- **No new false negative (the real attack): PASS.** Real process, 11 real shim forms all banner=True:
  plain, **CRLF (`-->\r\n`)**, leading-space, **leading-tab**, **BOM**, trailing-whitespace (` \n`,
  `\t\n`), trailing-ws+CRLF, tight inner, wide inner, BOM+CRLF+lead. The `\r` is swallowed by `\s*$`
  (Python `\s` includes `\r`, plus universal-newline on `open(encoding="utf-8")`).
- **Trailing text rejected (the anchor's purpose): PASS.** `--> this is NOT an install`, `-->x`,
  quote, prose, negation (the 08-04 form), `#` comment → all banner=False.
- **`validate.py`: PASS.** Green against the frozen tree (the three real shim constitutions NOT
  over-refused); red on a non-shim line 1 AND red on line 1 with trailing text after `-->`. Both ends.
- **`scaffold_team` (bash + ps1): PASS.** Legacy regex isolated: plain/CRLF/leading+trailing-space/tab
  → MATCH `dev-team`; trailing-text/quote/prose/`#` → no match. The anchor does not break real
  ownership recovery.
- **Test measures the running part + red-without-fix: PASS.** Removing `\s*$` from the running hook
  in the copy → exactly `test_line1_mention_of_marker_does_not_trigger_kit_detection[trailing_text]`
  goes red, the other 13 (all real shim forms + the four mentions) stay green. The red test drives the
  real subprocess, not just the helper predicate.
- **Mirror + stamps: PASS.** Detection block byte-identical across the three kits (md5
  `e24a90e8…`, len 5923); stamps dev/research `2026.08.12-3`, office `2026.08.12-6`; hash consistency
  green via `validate.py`.
- **Full suite: PASS (classified artefacts).** Split run, every failure a sandbox artefact
  (`test_ci_lint_pinned` FileNotFound `.github/` → 4 passed after re-copy; `test_migrate` needs `.git`;
  four sh full-install scaffold tests hang on Git-Bash process-exit on this host, anker-independent —
  the legacy regex is not entered on fresh install and is measured directly in point 4). No real failure.

## The two named residues that remain (both disclosed, not overlooked)
- `user/codex/AGENTS.md:22-25` still carries the "contains the marker" rule — a real BUG-0011 analogue
  for the Codex entry file. DEC-0039 scopes the fix to `user/claude`; the Codex twin is a follow-up BUG.
- `.claude/hooks/test_gates.py:469-484` — assertion green, but its rationale comment ("routes on the
  bare substring") is stale after DEC-0039. Protected path, cannot be edited from the session → handback.

## Why this matters
The marker is what the global entry file routes on to decide whether a repo hands over to a Project
Manager. A quote, a negation, or a sentence that merely names the marker used to trigger that handover;
now only the exact shim line scaffold_team writes does. This repo deliberately keeps the marker string
out of its own `CLAUDE.md` for exactly that reason — the fix makes the detector match that intent.
