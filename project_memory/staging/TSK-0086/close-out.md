# TSK-0086 close-out protocol (lead, 2026-08-28)

Round: BUG-0068 — the follow-up step after a kit update. **This one came from live use**, not from
an audit: the user updated his real office project himself, was handed `cp` lines for the terminal
by the PM, and asked whether that was right. It was not. Three verifier rounds:
FAIL(B1 false re-check claim) → FAIL(unreadable list deleted) → **PASS**.

## What the user's one question turned into

Five defects, and **two of them were created by the fixes for the first three** — which is the
whole argument for a second pair of eyes on every round:

1. **EOL drift** — the differ compared raw bytes, so a Windows/OneDrive checkout drifting LF→CRLF
   read EVERY script as "differs" and put it on the pending list. Both twins now strip CR first.
2. **The dead end (BUG-0041 family)** — the guarded ledger judge was copy-if-absent, so on
   divergence it was KEPT, LISTED, and the PM could not merge it (every in-session write path to
   the judge is refused, deliberately). It is now refreshed BY THE INSTALLER, and WHICH files that
   covers is DATA (`team-kits/repo_kit_owned.txt`, read by both twins) with a tripwire that asks
   the RUNNING guard as a process over EVERY shipped repo template — all four decision sources,
   not one; its floor fails on a silently-permissive AND on a crashing guard.
3. **The list never re-validated** (lead-measured on the live project: all four listed scripts raw
   byte-identical to the installed template, still listed) — the kernel now re-checks each entry at
   session start; a resolved list is deleted, a diverging entry still nags.
4. **NEW, from the fix for 3** — the assurance "Each entry was re-checked" was printed wherever the
   kernel merely ANSWERED, including when no template could be read at all (staged kit missing —
   the normal state on a second machine). Root cause: "differs" and "could not be read" were the
   SAME answer. Now three answers, and the sentence hangs on a real comparison.
5. **NEW, from the same fix** — an UNREADABLE pending list read as empty, counted as resolved, and
   was DELETED. Worse than before the round, where it at least survived. Reachable via an ACL
   denial or a non-hydrated OneDrive placeholder — and the user's project lives in OneDrive.

## Verifier PASS (round 3), self-measured

His own deny case both directions (file survives, nothing claims it resolved, escalation counter
untouched; readable+resolved still deleted and its counter reset); the three-answer split attacked
with a directory, a dangling symlink, a mid-read vanish and undecodable bytes; an unread list
reaches `resolved` on no path (read AND measured); the helper's icacls return-code check really
reds the test when the ACL command fails; no regressions in the earlier findings; the changed block
byte-identical across all three kits; stamps, mirrors, ruff, validate, .claude/ untouched.

## Hole list (this commit)

**H71** — four measured boundaries of the pending-list reader, with its table row and provenance:
(a) an entry `open()` rejects with something other than `OSError` aborts update-kit after a
SUCCESSFUL installer run (hook guarded, command not — the one-liner is named); (b) a read list
decoding to no recognisable entry counts as empty and is deleted (UTF-16 measured; not a shipped
form); (c) the comparison strips EVERY CR, so a lone CR mid-line or a 0x0D in a binary template
compares equal — over-discarding, and narrowing it would put reader and installers at odds about
the same file, exactly the break that produced the user's list; (d) two states that deliberately
keep nagging rather than going quiet.

## Delivery run (DEC-0050)

`pytest tools/` → **3856 passed, 14 skipped, 1 failed** in 30:04. The one failure was a real
tripwire doing its job, and it was MINE to fix: `test_the_session_start_hook_emits_what_the
_disposition_counts` — the round added an emission site to the session-start hook (the UNREADABLE
briefing), and the disposition journal still stated the old count. Journal updated with the reason
in the running list of increments (20 → 21, and the dependent "a deleted site lowers it to" 19 →
20); `tools/test_shortening_net.py` re-run: **35 passed**. The rest of the tree was untouched by
that edit, so the scope of the re-run follows what the change touched, per DEC-0050 — said here
rather than implied.

## Deviations

- `radar/2026-08-28-claude.md` — the weekly intelligence report landed in the tree during the
  round (scheduled watcher, not this item's work). Committed with the package, named here rather
  than smuggled; previous radar reports rode along the same way.
- R5 (this file landing CRLF in the worktree) left as the verifier advised — hygiene, git
  normalises on commit, ~50 files share it.

## What the user gets

His pending file clears itself at the next session start once this ships; and every future update
of his real projects avoids all five defects. The one thing still asked of a PM is a genuine merge
where a project really customised a kit template — with prose that now promises only what the
gates allow.
