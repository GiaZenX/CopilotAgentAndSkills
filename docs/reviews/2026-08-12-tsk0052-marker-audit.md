# TSK-0052 / BUG-0011 / DEC-0039 — marker occurrence-vs-structure audit (2026-08-12)

DEC-0039 makes the kit-shim marker count only in its **shim form on line 1**
(`<!-- agents-and-skills:team-kit <team> -->`), never as a bare occurrence of the string. This is
the AC-3 measurement: every place in the harness that reads `agents-and-skills:team-kit`, judged as a
real analogue of BUG-0011 (an occurrence check that a mention could trip) or harmless (already
structural / a different string / a fixture).

Method: `rg "agents-and-skills:team-kit"` across the tree; each hit read at its running site.

## Fixed in this task

| Site | What it did | Change |
|---|---|---|
| `user/claude/CLAUDE.md` (Detect-state pt.1 + HANDOVER) | prose rule "`./CLAUDE.md` **contains** the marker" | now structural: the **first line** is the shim marker line; a mention elsewhere/negation does not count |
| `team-kits/{dev,office,research}-team/hooks/session_status.py` (kit detection) | `re.search(r"agents-and-skills:team-kit\s+([\w-]+)", fh.readline())` — matched the marker **anywhere on line 1** (a quote / prose / negation / `#` comment tripped it) | `re.match(r"\s*<!--\s*agents-and-skills:team-kit\s+([\w-]+)\s*-->", first_line)` after `lstrip("\ufeff")`; anchored to the shim FORM. BOM/CRLF/leading-space tolerant so real installs still match. (kit-hash input, mirror-exempt via `KIT_SPECIFIC_HOOKS`, bumped) |
| `tools/validate.py:~216` (constitution line-1 marker) | `"agents-and-skills:team-kit" not in lines[0]` — substring on line 0 | tightened to the same shim-form `re.match`; the constitution IS the shim source `scaffold_team` copies line 1 from, so a non-shim line-1 (that would blind the anchored detector) now fails CI |
| `team-kits/scaffold_team.sh:~332` / `scaffold_team.ps1:~311` (legacy ownership recovery) | read the marker anywhere on the first line of AGENTS.md/CLAUDE.md (`…team-kit\s+([A-Za-z0-9_-]+)`) | pulled onto the SAME anchored shim form `^…<!--…team-kit <team>…-->…$` so every marker reader shares one definition (`[[:space:]]*$` / `\s*$` swallows a trailing CR on a CRLF entry file) |

### End-anchor remainder — CLOSED (2026-08-12, follow-up review)

The first-round anchor `…-->` had no END anchor `$`: a line
`<!-- agents-and-skills:team-kit dev-team --> this is NOT an install` still matched (banner True),
contradicting the entry prose (`user/claude/CLAUDE.md`, "`@AGENTS.md` on line 2 **and nothing
else**") and the hook comment — House rule 3. Closed by adding `\s*$` to every marker reader in one
definition: `session_status.py` (×3), `validate.py`, and both `scaffold_team` twins (above).
Measured (real `session_status` process): trailing text after `-->` → banner **True → False**;
real shim incl. **CRLF** and **trailing whitespace with no text** (`--> \n`) → **True → True**.
Red proof: `test_handover_marker.py` case `[trailing_text]` fails with the `$` removed in an
external clone; the shim forms stay green.

Measured before/after (real `session_status` process, dev-team staged newer): line-1 `quote` /
`prose` / `negation` / `# comment` → **banner fired = True** before, **False** after; real shim,
plus **leading space / CRLF / UTF-8 BOM** → **True** before and after (real installs unbroken).
Test + red proof: `tools/test_handover_marker.py` — with the loose predicate restored in an external
clone, exactly the four line-1 mention cases fail; the four shim forms and the scans stay green.

## Harmless (already structural / not a handover occurrence check)

| Site | Why harmless |
|---|---|
| `team-kits/*/hooks/session_status.py` (now `re.match` shim-form, line 1) | the running structural detector this task anchored; exercised by `test_handover_marker.py` |
| `tools/validate.py` (now shim-form `re.match` on constitution line 0) | position-asserting build check, consistent with the detector after this task |
| `team-kits/scaffold_team.sh` (legacy migration, ~l.332) / `scaffold_team.ps1` (~l.311) | was first-line-structural but unanchored; **pulled onto the anchored shim form** in the follow-up review (see Fixed table) so all marker readers share one definition |
| `team-kits/gen_provider_artifacts.py:~1094` | `re.fullmatch` on the `# agents-and-skills:team-kit-roles v1 …` manifest **header** — a different string, fully anchored |
| `tools/test_hooks.py` (many), `tools/test_shortening_net.py`, `tools/test_context_budget.py` | build shim fixtures `"<!-- …team-kit … -->\n@AGENTS.md"`; `test_hooks.py:~8751-8755` asserts the real `scaffold_team` shim generation (line 1 = marker, line 2 = `@AGENTS.md`) — fixtures/structural, not detectors |

## Real analogues left open (NAMED, not closed here)

1. **`user/codex/AGENTS.md:22-25`** — the Codex provider's global entry gate carries the SAME
   pre-fix rule for handover: "If its `./AGENTS.md` … **contains** the marker" and "either
   `./CLAUDE.md` **contains** the team marker". This is a genuine analogue of BUG-0011, still live.
   It sits in `user/**` (the implementer's area), but DEC-0039 scopes the fix to
   `user/claude/CLAUDE.md`; AC-3 directs analogues to be **named as a follow-up**, not co-fixed.
   Disposition: the coordinator files a separate BUG for the Codex entry gate (same structural
   rewrite: the marker counts only as `./AGENTS.md` line-1 constitution marker / `./CLAUDE.md`
   line-1 shim). Not fixed in TSK-0052.

2. **`.claude/hooks/test_gates.py:469-484` (HANDBACK — protected path, not touched)** — the belt
   asserting this repo's `CLAUDE.md` carries no marker (`:482`) stays valid and green (this repo
   still ships no marker). But its rationale comment (`:469-473`, "the global handover rule routes
   on the bare substring … even a sentence denying it triggers the handover") describes the
   **pre-fix** rule and is stale after DEC-0039 (over-alarming — House rule 3). `.claude/` is a
   protected path a tool write cannot reach; the fix must run from a shell outside Claude Code.
   Recommended edit: soften the comment to "belt: keep the marker off line 1 / out of this doc even
   though the handover rule is now structural (DEC-0039)". The assertion itself needs no change.
