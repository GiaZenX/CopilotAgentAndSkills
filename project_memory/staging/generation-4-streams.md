# Generation 4 -- four PRODUCT GOALS (DEC-0067: the bundle lives at the goal), approved as ONE plan (DEC-0068, APR-0005, 2026-09-04)

Base: feat/harness-v2 at 46eaaf2 (generation 3 merged in 6704221; release dev/research 2026.09.04-1,
office 2026.09.04-3). Cut rules: DEC-0062 (file ownership), DEC-0067 (one PR per stream, wishes merged
at triage), DEC-0070 (retrospective of generation 3: the cut is MEASURED before spawn with
check-scopes; a command-line guard is a DEC-first design round, not a stream; a "queued" message is
no delivery; DEC-0050 becomes a gate first).

User decisions: the four goals (2026-09-03 "Ja die vier"); the deferred block is its own generation
(FR-0024 interactive backlog system, FR-0023, FR-0025, FR-0019, FR-0022, FR-0081, FR-0033); plan
approval GRANTED 2026-09-04 over PR-0001..0007 (the three old roots included by the kernel's own
rule: every goal in the source status of its scope edge); BUG-0089 scope approval GRANTED.

| Goal | Item | Absorbed | Owns (files -- to be measured with check-scopes before spawn) |
|---|---|---|---|
| G4-1 Test discipline & hook hygiene | PR-0004 | FR-0086, FR-0057, H139 | .claude/hooks/** (gate 5, implementer only), */hooks/** (new gate + timeouts reader), */settings/**, skills quality-engineer + implementer texts, dev-team templates/repo/scripts/kit_browser_checks.py (+ research mirror), tools/test_hooks*.py nodes |
| G4-2 Kernel contracts | PR-0005 | BUG-0090, BUG-0091, FR-0085, FR-0087, C-2/C-3 | kernel/** (backlog_types, state, approvals, dispatch, report, scopes), */hooks/gate_dispatch.py, .claude/hooks/test_gates.py (holes judges), docs/POST_V2_WISHLIST.md migration |
| G4-3 Procedure & retrospective | PR-0006 | FR-0084, FR-0005, FR-0010, DEC-0070 rules 1/2/5 | */constitution/**, */skills/project-manager/**, */skills/project-auditor/**, */agents/project-auditor.md, .claude/agents/harness-lead.md (implementer only) |
| G4-4 Repo hygiene | PR-0007 | BUG-0069, BUG-0025, BUG-0088, BUG-0033 | .github/**, .gitattributes, kernel/kitupdate.py, tools/validate.py (eol check), .claude/hooks/test_gates.py (gate-3 timing test) |

Seams to name before the cut (measured, not written -- DEC-0070 (1)): `.claude/hooks/test_gates.py`
(G4-2 holes judges x G4-4 timing test), `*/hooks/**` (G4-1 new gate + timeouts x G4-2 gate_dispatch
refusal), `tools/test_hooks.py` (every stream), the constitutions (G4-3 owns; G4-1/G4-2 report
sentences), `docs/POST_V2_WISHLIST.md` (G4-2 migrates it -- every other stream files holes THROUGH
G4-2's new item shape or reserves numbers IN its item before READY), `team-kits/*/VERSION` (all;
dropped from every patch, ONE stamp in the merge -- a patch that carries VERSION hunks is a cut
finding, DEC-0070). Hole numbers: next free H151; reserve IN the item text.

Rules carried in every order (DEC-0063 (5), DEC-0070): measure every new property claim before
handover; hole citations with module prefix; scratch only under
`C:/Offline Repos/v2-testbed/_round-scratch/<TSK>/`; verifier copies WITHOUT `.git`; streams run
only the reading suites, the full run belongs to the merge; provisional stamp; the plan names the
rejected alternative; real shell as arbiter wherever the truth about the shell can be executed;
resume-not-respawn under 429/529; the lead confirms every delivery with ListAgents when "queued".

## Log

- 2026-09-04 04:3x PR-0004..0007 captured (staging/generation-4/create_goals.py); wishes MERGED into
  their goal (resulting_item), bugs filed under theirs; plan approval requested and GRANTED
  (APR-0005); PR-0001..0007 -> APPROVED through `transition` (a plan answer walks zero items by
  design, C's measured rule); BUG-0089 APPROVED -> FIXED -> VERIFIED (EVD-0081). Next: one TSK per
  PR (DEC-0067), check-scopes over the four items BEFORE spawn, worktrees g4-*, spawn -- or hand
  over to the next session (the user decides how far this session goes).
