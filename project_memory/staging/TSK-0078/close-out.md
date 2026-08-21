# TSK-0078 close-out protocol (lead, 2026-08-21)

Round: FR-0049 (filing review pipeline, the user's own design) + FR-0051 (manager model pins) +
two TSK-0077 residues. Pre-pilot-4 per user decision. Two verifier rounds: FAIL(B1..B4, N1..N7)
→ **PASS**. Report: docs/reviews/2026-08-21-tsk0078-measurements.md.

## What shipped

FR-0049 — the reviewed filing chain, the user's five steps in his order:
- New filing-reviewer role (office kit, worker/low per DEC-0047) — shell-less, returns via the
  TSK-0073 hand_back mechanics; clerk reads EVERY file individually and writes one proposal
  entry per document; reviewer answers accept/object/partial per file with content plausibility
  (recipient vs business_profile, required fields, GTIN ambiguity, image naming — rubric derived
  from business_profile, no hard-coded values); manager executes accepted moves (through
  gate_filing as ever) and carries objections to the user. Artifact contracts in ONE schema file
  per half; vocabulary lives once.
- Step 5 BUILT, not reported as a gap: kernel filing.py + APR kind filing_rule +
  `add-filing-rule` — the plan grows by exactly the approved rule (hash binds every field incl.
  reason; read-back compares the on-disk rule against the raw manifest values; wildcard first
  segments refused BEFORE the question after the verifier showed one would have opened a whole
  archive level); gate_write_scope names the route by derivation; session briefing and doctor
  now DERIVE document routes from partial_writers instead of asserting the old dead end (the
  BUG-0041 form, caught in round 1 — it also healed the project_config messaging).

FR-0051 — model pins, measured not assumed: frontmatter of the bound session agent SETS the
model, explicit user choice overrides, settings.json is the fallback for roles without model: —
all three claims probed against the real CLI by implementer AND verifier independently. dev- and
research-PM pinned to fable/high (T3 per DEC-0034/0047), office-manager stays opus/high;
settings values aligned (one answer, not two); model_tiers.yaml carries the DEC pointers;
validate.py derives portable model values from the tier file instead of an enumeration.

Residues N1/N2 fixed (dead drifted RX deleted; number derived); N4 decided by measurement;
TSK-0077 N1/N2 one-liners fixed (bracket truth; N>&M spans — door over-refusal on 2>&1 gone,
full TSK-0077 battery non-regressed).

## Named deviation ACCEPTED by the lead

README.md:332 (one line: add-filing-rule joins the command-surface list) lay outside the item's
allowed_scope, forced by the command-surface tripwire, content verified correct by the verifier.
Accepted; the item is archived, no rescope needed. Process note: command-surface additions
should list README.md in allowed_scope from the start.

## Verifier PASS (round 2), self-measured

Briefing/doctor routes both directions (incl. an invented-route ablation of his own); the B2
refusal chain over 11 hostile template spellings with the legit rules still minting; B4 typo
ablation now red with an honest StateError; item_enums both directions; pipeline smoke through
all registered hooks; TSK-0077 door battery 32/35 OK (3 = his own corrected round-1
expectations); mirrors byte-identical x3; suites reproduced (2927+13 via his copy's arithmetic;
gates 243). Stamps dev 2026.08.21-6 / office -7 / research -6.

## Hole list (this commit, lead)

Three new L9 bullets: kernel-appended rules never gain the optional fields; the verdict→move
seam is procedure prose (bounded by gate_filing + auditor); two answers on portable model
values (generator enumeration vs validate derivation).

## Items

FR-0049 → MERGED (delivered; the ONE half-built spot is named in role text and template:
optional billing_address means the reviewer checks the name and SAYS the address went
unchecked). FR-0051 → MERGED. TSK-0078 → CANCELLED, archived.

## Residues (named, non-blocking)

- No runtime hook validates the pipeline artifacts against their schema (guard_yaml_valid checks
  well-formedness only) — the wall stays gate_filing.
- filing-reviewer deliberately not in VERDICT_ROLES (that contract is task PASS/FAIL).
- add-filing-rule open to subagents — bounded by the approval, said in ENFORCEMENT.
- archive/<Jahr> stays legal (literal tray, reader-visible) — the docstring says what is not
  checked. Unmeasured: real bound-lease reviewer write path; interactive /model; codex runtime.
