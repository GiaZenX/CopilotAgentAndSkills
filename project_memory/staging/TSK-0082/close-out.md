# TSK-0082 close-out protocol (lead, 2026-08-23)

Round C after pilot 4: BUG-0060 (evidence drawer) + BUG-0061 (filing plan from onboarding) +
BUG-0062 (hook timeouts). Two verifier loops: FAIL(C1,C2) → PASS after the prescribed
docstring-example fix (implementer, measured red/green) and the lead's hole-list entries.
Kits 2026.08.23-3.

## What shipped

- BUG-0062 INVERTED by measurement (both roles independently, real provider sessions,
  claude.exe 2.1.239): a SET timeout kills exactly at its number and the kill is a SILENT
  passthrough; an entry without timeout survives 310/560 s and is killed at ~600 s (bracket
  560/900, dated from two session durations 611/612 s). Consequence: all timeout keys removed
  EXCEPT gate_pipeline, which keeps 1800 over its own 1500 s child bound — the property "the
  own refusal always arrives before the kill", held by a test that reads child bounds from the
  RUNNING code via AST and every number from tools/provider_observations.json (hook_deadlines,
  with provenance and named not-measured). 13+ stale "the host kills at 60s" prose sites
  rewritten both directions.
- BUG-0060 answered with a NAMED third way (the item's two outcomes both refused with reasons:
  writing evidence would invent a pass verdict and stamp gate_git's own merge door; removing
  the drawer breaks 54 records + three readers): the drawer is UNREACHED, not dead (three
  populations measured) — report.accepted_without_a_verdict warns per accepted task without a
  passing delivery verdict (edge derived via confirming_edge, office exempted via
  ROOT_TYPE_BY_KIT where the verdict is unfulfillable) + session-start briefing says the same
  sentence (dev/research), both directions measured as real hook processes.
- BUG-0061: business_profile gains document_sources (interview DIRECTIONS as a derivation, "I
  don't have that" is an answer), filing_plan head names the coverage duty, registry why states
  the derivation checkably, kernel/filing.uncovered_document_sources + filing_coverage_briefing
  at office session start; red test with the REAL half-3 answer set as fixture, both
  directions. The interview itself is a conversation — the live test run measures it.
- Hole list: H58 (DONE→VALIDATED requires no evidence — user semantics decision), H59 (nothing
  drives a project into phases 6-9 — emptiness now SAID), H60 (document_sources enforces
  nothing — doubly bounded), H61 (no kit hook notices its window expiring — closing
  construction exists in this repo's _harness.Deadline, not taken into the kits) + L9 bullet
  (the ~600 s default kill window, both roles' measurements, observed-runtime vs own-bound
  distinction after the verifier's nit).

## The loop's catches

C1: the implementer's generalisation from one point ("no realistic gate runtime reaches a
kill") measured false by the verifier's own provider session — gate_pipeline briefly sat in
the passthrough class its own round had named; C1 fix verified in five directions incl. two
verifier-built mutations proving the test reads running code. C2: hole list. Final: a
docstring named a red direction that was green (gate_push_token has an own 15 s bound).

## Named accident (not part of the package)

init_project_memory.sh ran once in the repo root: 8 untracked office template files sit in
project_memory/ (validate: 0 errors). Gate 1 rightly refuses their removal from inside;
deletion is the user's, from a shell outside Claude Code:
  Remove-Item "C:\Offline Repos\AgentAndSkills\project_memory\{business_profile,compliance_register,content_guidelines,filing_plan,marketing_plan,master_data,product_catalog}.yaml" ; Remove-Item -Recurse "C:\Offline Repos\AgentAndSkills\project_memory\procedures"
These files are NOT committed with this round.

## Open, deliberately

Live-run measurement points pooled for the next step: BUG-0058 AC-2, kit_bridge_notice
delivery, H53, H59 (does the said emptiness move a project into QA), BUG-0061 interview.
BUG-0060/0061/0062 stay OPEN until the live run confirms. TSK-0082 CANCELLED+archived.
