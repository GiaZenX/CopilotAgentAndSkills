# TSK-0089 close-out protocol (lead, 2026-08-29)

Round: FR-0052 — kit PMs answer target-state questions from the DECISIONS first, then the code;
an answer drawn only from built artifacts says so. The kit half of the discipline the lead
adopted 2026-08-17 after missing DEC-0034 in a model answer. Verifier: FAIL(B1 dead guard) →
PASS.

## What was built

- The rule in EVERY kit, on the surface that actually LOADS at answer time: Block A (procedure,
  1542 B byte-identical ×3) in the lead SKILLs, Block B (649 B ×3) in the lead AGENT files —
  because lead_package.py measures the SKILL as registered-not-injected; a rule only there is
  not in front of the lead when the user asks "why?". Constitution deliberately untouched.
- The honest limit verbatim in both: NOTHING ENFORCES THIS — free text is invisible to every
  gate; the paragraph and the brief's decision section are the whole mechanism.
- Counter-direction: 7 dangling pointers found in shipped files, all naming DEC-0001 — which the
  store no longer holds (deleted during the BUG-0020/H34 measurement; TSK-0043:25 records it).
  Fixed to followable pointers; a new test holds every DEC pointer in shipped kit files
  resolvable (126 judged, 38 files), with floors that red when the reader returns everything or
  nothing.

## The verifier's blocker — the GUARD was blind, not the ware

The honesty tripwire's 90-char run-up window read nearly every overclaim as negated (Block A is
saturated with negation words): both overclaim forms in the SKILL measured affirmed=0 — a SKILL
claiming "A gate refuses an answer that skipped this step." would have shipped past every check.
The implementer re-measured, found it WORSE than reported, and fixed it with the verifier's
measured sketch: run-up cut at the last clause boundary. Verifier round 2 replayed six mutations
(replace/add × skill/agent, top-of-block, honesty-cut) — all red; shipped text clean on both
surfaces. Also in the pass: the apostrophe alternative dropped from the pointer reader (it
swallowed model_tiers.yaml:31's DEC-0034 — the round's own pattern file), pinned by a new floor;
the latent over-demand removed (an extra constitution section naming both anchors no longer reds
the test; drift still does).

## Hole list (this commit)

H72 (TSK-0087, prior commit) unchanged. NEW H73 — four measured boundaries: (a) any id inside a
delimiter longer than itself is unjudged — 16 of 22 quoted spans are text someone READS (13
kernel refusal messages + 3 handover literals; closing direction named, own round); (b) the rule
test reads only the two anchors, not the direction (the rule inverted passes, measured); (c) an
overclaim never naming the apparatus is not caught — visibility comes from the section-pin
digest, not byte-identity; (d) the clause cut reads "," never and "."/":" always as a boundary —
both failure directions measured by the verifier, neither hits today's text.

## For the user (tomorrow's list)

DEC-0001 is gone and stays gone — restoring it is HIS decision (the kit-update-flow rationale
survives only via FR-0006 and BUG-0020/TSK-0043; the content is reconstructable).

## Delivery

Kit stamps dev 2026.08.29-3, office -7, research -3 (round 1; rework touched only two test
files, bump confirmed unchanged). ruff, validate clean; lead-package size and section-pin
journals updated honestly ("anchors: no registered hook"). 13 reds seen across the task by the
implementer, 10+ replayed independently by the verifier. Full delivery suite: run by the lead
before commit (result in the commit message).
