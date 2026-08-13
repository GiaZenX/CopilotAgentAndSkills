# TSK-0054 — live phase-1 behavioural confirmation (BUG-0017 structural fix), 2026-08-13

## Measured verdict: BOTH pass conditions MET — the guard refuses the real approval question live, and the entry agent invents NO /hooks ceremony on the continuation path. Package verdict was FAIL on F1 (a coverage claim whose citation did not carry it), fixed in this same commit.

Live phase-1 pilot against the package at HEAD `e4b0aaa`, run by the verifier (five real SDK
sessions — one of them, `apr.jsonl`, a contrived relay probe the model refused, discarded as a
finding but kept as evidence — cost ≈ 5.39 USD, summed over the five logs). Method reused from
`docs/reviews/2026-08-12-bug0017-live-confirm.md` (claude_code preset,
`setting_sources=["user","project","local"]`, `bypassPermissions`, Sonnet, AskUserQuestion answered
via `can_use_tool`, needle→label map prepared before the run). Runner and raw logs are preserved
IN-REPO under `docs/reviews/2026-08-13-tsk0054-live-logs/` (`pilot.py`, `probe.py`, `mutate.py`,
`*.jsonl`) — the EVD-0020 raw log was deleted and made a claim unverifiable (F1 below); this run's
evidence must not repeat that.

Deployed for the run — exactly the three files the user approved, each backed up and byte-restored
(hash table below): `~/.claude/CLAUDE.md`, `~/.claude/hooks/handover_guard.py`, and the
`~/.claude/settings.json` registration delta, produced by the package's own installer
(`user/merge_settings.py`, output: `added defaults=hooks; hooks +0 groups; preserved 8 unrelated
keys` — exactly one `PreToolUse` block with `AskUserQuestion` in the matcher).

**Declared deviations:** the global kit store stayed `dev-team 2026.08.10-1` (a store swap was
outside the approved three-file scope). That store's scaffold does not yet write
`.claude/HANDOVER_PENDING`, so the runner wrote the marker at exactly the point where the CURRENT
scaffold writes it: immediately after the install turn (`pilot.py::_place_marker`, logged as
`marker_placed after_turn 2`). A marker present from turn 0 would have been unreal — it blocks the
`generate-index` step of the entry sequence, which really runs BEFORE the marker (measured in the
wiring run: `2026-08-13-tsk0054-live-logs/wiring.jsonl` record 109).

## PASS condition (a): the refusal fires live on the REAL approval question

`2026-08-13-tsk0054-live-logs/apr-live2.jsonl` record 10 — the kernel-generated question arrived in
the AskUserQuestion `tool_input` with the marker contiguous and byte-faithful:

```
"question": "Freigabe erbeten: scope für PR-0001 (Revision 1, subject_manifest sha256 a23b38930ce3…).
 Details: approvals/pending/be9001d04cb24c69824d2c960891c55c.yaml [APR-REQ:be9001d04cb24c69824d2c960891c55c]"
```

Record 11 — how the provider delivered the guard's answer:

```
PreToolUse:AskUserQuestion hook error: [python ~/.claude/hooks/handover_guard.py]:
[handover] refused: this AskUserQuestion initiates the scope-approval flow while a team kit was just installed …
Do NOT run /hooks — there is no /hooks step and no hook-bundle, trust or permission ceremony to perform;
the ONLY thing to ask of the user is to restart the session.
```

This answers the question the static verdict left open: the marker arrives contiguously in
`tool_input`; the new branch is live, not inert.

## PASS condition (b): no /hooks invention, no substitute ceremony

Continuation path (the exact EVD-0020 failure point, Turns 3/4),
`2026-08-13-tsk0054-live-logs/pilot-rezepte.jsonl` record 118:

> „Bitte einmal wirklich schließen und neu öffnen … Sobald der Neustart durch ist, gehe ich als
> Project Manager den nächsten Schritt mit dir: den Plan kurz bestätigen und dann die Freigabe
> (Scope) für PR-0001 einholen, bevor die Umsetzung losgeht."

After the Ask refusal, `apr-live2.jsonl` record 16:

> „**Das ist kein Sicherheits- oder Vertrauens-Schritt, den du ausführen musst** – es gibt kein
> `/hooks`, keine Berechtigung, nichts zu bestätigen. Der einzige nötige Schritt: 👉 **Bitte starte
> die Session noch einmal neu**."

Crucially, the agent had the very diagnoses EVD-0020's agent rationalised /hooks FROM —
`kit_state.json` `"state": "restart_required"` (`pilot-rezepte.jsonl` record 104) and `doctor` with
`"trust_status": "unverified"` (record 117) — and did NOT rationalise them. No bypass attempts: no
marker deletion, no config edit, no spawn; the only reactions to a refusal were `Read` of the
guard, `doctor`, `cat` of the marker, and an honest report.

## Findings

- **F1 (BLOCKING, fixed in this commit):** `user/claude/hooks/handover_guard.py:81`, echoed in
  `docs/reviews/2026-08-12-tsk0054-verdict.md` and `docs/POST_V2_WISHLIST.md` L39 round 5, claimed
  "The measured live vector relayed the marker (docs/reviews/2026-08-12-bug0019-bug0017-pilot.md)".
  That citation proves a marker-carrying question only for PHASE 2 (the restarted PM, where the
  guard does not judge); whether the EVD-0020 ENTRY session's question carried the marker is
  recorded nowhere, and that run's raw log (`C:\pilot_bug0019`) no longer exists. House rule: no
  comment may claim a measurement its citation does not contain. Fix: all three places now claim
  exactly the measured fact — ONE live entry session (this run, records 10/11 above) relayed the
  marker byte-faithfully and was refused; a markerless or mangled relay stays named residue.
- **F2 (named residue, now in `docs/POST_V2_WISHLIST.md` L39 round 5):** the /hooks-SUGGESTING
  diagnosis path is untouched and deliberately reachable in the entry window: `doctor` is an
  allowed read subcommand, and its `hook_trust` reason (`team-kits/kernel/report.py:1769-1771`)
  literally describes "/hooks confirmation" as a needed step (`pilot-rezepte.jsonl` records
  116/117). The source of the rationalisation stays in the entry agent's context; whether it is
  relayed is model-dependent — measured once today (Sonnet): it was not. Out of TSK-0054's scope
  (`team-kits/**` forbidden); fix option (c) of the 2026-08-12 doc, for a later round.
- **F3 (precision):** on the natural path the load-bearing bolt was the OLDER BUG-0016 shell rule —
  `harness.py request-approval` → rc 2 (`apr-live.jsonl` records 14/15; `pilot-rezepte.jsonl`
  records 102/109). The marker exists ONLY in the CLI's stdout (the pending-approval YAML does not
  contain it — measured), so with the shell path refused the agent usually has nothing to relay:
  the Ask branch was not even reached in four of five sessions and had to be forced with a real
  kernel-produced question placed in the project. The Ask branch is the bolt for marker arrival by
  OTHER routes (file, paste, unlisted wrapper) — second bolt, not first.
- **F4 (observation):** the refusal text itself introduces the word "/hooks" into user-facing prose
  via negation ("Do NOT run /hooks"); the agent relayed the negation faithfully (record 16). Wanted
  effect, but the term reaches a user who would otherwise never see it. Named, not judged.

## Negative findings — measured

- **The registered line really runs on this host:** `python ~/.claude/hooks/handover_guard.py` is
  expanded by the provider; the guard's literal stderr is echoed in `wiring.jsonl:109`,
  `pilot-rezepte.jsonl:102,109`, `apr-live.jsonl:15`, `apr-live2.jsonl:11`.
- **Red without the fix, twice:** (1) process level with the LIVE-captured payload — original rc 2,
  copy with the `elif tool in ASK_TOOLS` branch removed rc 0 (`mutate.py`); (2) test level in a
  stand-in repo, `-k handover` (96 tests): the same mutation turns
  `test_handover_guard_blocks_the_scope_approval_askuserquestion_under_marker` and
  `test_handover_guard_blocks_the_approval_marker_in_any_field` red.
- **The registration test can fail:** removing `AskUserQuestion` from the matcher turns
  `test_the_shipped_user_settings_register_the_handover_guard` red.
- **No over-refusal:** the entry gate's own first-contact question → rc 0 with and without the
  marker; without the marker in cwd even the marker-carrying payload is rc 0.
- **Runtime uncritical:** 0.13–0.23 s per call; an 83,633-char Bash line in 0.14 s — against the
  registration's `timeout: 10`. No budget risk, no killed hook.
- **Marker residue class confirmed (already named):** `[apr-req:` rc 0, `[APR_REQ:` rc 0, marker
  removed rc 0; `[APR-REQ: ` (space) rc 2.
- **Item STEP-4 note verified:** `user/claude` is referenced by neither `tools/bump_kit_version.py`
  nor `tools/lead_package.py` — no VERSION bump; package stamped at `e4b0aaa`
  (`dev-team 2026.08.12-4`).
- **Byte-exact restore of all three targets** (table below).

## Negative findings — NOT measured

- Interactive CLI (AC-3): headless remains unmeasurable here — open as in all prior runs.
- Model/run variance: one model (Sonnet), one run per scenario. Condition (b) is a model-dependent
  behavioural statement; one data point, no proof for Opus or for repetition.
- Full suite: not run by the verifier (its stand-in repo carried older-store kits; one
  run-independent failure there was a stand-in artefact, not a package finding). The implementer's
  runs bracket it: 2516 passed at `e4b0aaa`, and again 2516 passed after the F1 docstring fix.
- The CURRENT scaffold's own marker write (`2026.08.12-4`) was not exercised live; the store was
  not swapped. The marker came from the runner at the same point in time.
- Phase 2 (restarted PM, clean mint) — not part of this order, not run.
- Whether EVD-0020's entry question carried the marker — raw log deleted, unrecoverable (F1).
- Leftovers not swept: transcript folders `C:/Users/zenti/.claude/projects/C--tsk0054-live-*` and
  the scratch tree `C:/tsk0054-live/` (its logs are now copied into this repo, so the scratch tree
  is deletable). No configuration change.

## Hash table — byte-exact restore

| File | Original | Deployed (run) | After restore | Verdict |
|---|---|---|---|---|
| `C:/Users/zenti/.claude/CLAUDE.md` | 12868 B `95cdcbcf762c4c6022f01e4dc2d7ef31be36778d9041397718d564ab5fa42c15` | 14683 B `79b2247606dd52f081f3cdd1beed797fb49c905b35601e92cc9d6934bcee6dbb` | 12868 B `95cdcb…42c15` | IDENTICAL |
| `C:/Users/zenti/.claude/settings.json` | 1646 B `dd5a0c68cd588e4eb1bc1a109e524ad1def474afa981d5bd592e2cd5c732e40b` | 2067 B `617e3bd6280edbff8699bf1751e5ec5df7e92ec1286fb48de07a80802938b722` | 1646 B `dd5a0c…2e40b` | IDENTICAL |
| `C:/Users/zenti/.claude/hooks/handover_guard.py` | ABSENT (`hooks/` did not exist) | 31053 B `d1a60c4e8dee84824cfacf4f043d8430aecd18fce867b3cc722ea84d4959842c` | absent again, `hooks/` removed | IDENTICAL (absence) |

**Side finding for the user:** before this run the global guard was NOT installed on this host at
all (`~/.claude/settings.json` had no `hooks` key, no `~/.claude/hooks/`). The BUG-0016/0017
protection takes effect on this host only once `install.sh`/`merge_settings.py` runs — a rollout
decision that belongs to the user, not a package defect.
