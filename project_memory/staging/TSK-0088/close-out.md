# TSK-0088 close-out protocol (lead, 2026-08-29)

Round: BUG-0069 — the hosted GitHub CI red on every push while the local delivery suite is green;
the one external signal the user gets was inverted. Verifier: FAIL on form (nothing technical
blocked) → rework delivered per his pre-specified shape.

## The classification (AC-2) — one root for the ~100 errors

Ten buckets, summing EXACTLY to the reported numbers on both platforms, recomputed independently
by the verifier, durable home in docs/reviews/2026-08-29-ci-red-classification.md:
A shallow clone (96 errors each platform — test_migrate builds its V1 fixture from a commit 72
steps back); D sys.path leaking across tests until PYTHONPATH exceeds Linux MAX_ARG_STRLEN
(17F+52E ubuntu); F hardwired powershell calls; E1/E2 host-dependent shell/path expectations
(E2 became a PRODUCT fix); C recursion fixture vs item budget on CPython 3.14; I pip-audit
availability probing the runner; B relpath across two drives; G case-sensitive fs; H a 10 ms
lease race.

## Fixes worth naming

- ci.yml fetch-depth: 0 — history IS fixture material (cost measured: 6.2 vs 4.3 MB).
- conftest: no test leaves the next a sys.path entry (cause, not 15 deduplicating readers).
- PRODUCT (kernel state.py + 3 callers): a drive prefix is not a project-relative position on
  ANY host — state trees travel; behavior-identical on Windows, strictly stricter on POSIX; old
  approvals still resolve (verifier-measured).
- ci.yml -rs: every counted skip NAMES its reason — an honest skip is distinguishable from a
  silenced test; reader tests red on both -rs removal and a substring reader.
- Rework: the over-alarming one-place docstring cut to the true statement AND the property
  measured — a new sweep in test_repo_hygiene: every powershell command line handed to
  subprocess must sit in a function that asks the host (or a helper whose every caller does);
  19 sites found, 0 unguarded; 4 bypass mutations all red; the reader's boundary in its own
  docstring (a runtime-assembled launcher is not a subject).
- The floating python-version is now a SAID decision (comment names what it costs: the deep-body
  half of the recursion test skips on 3.14+).

## Verifier measurements (his own copies)

Bucket table digit-identical; run 33225215675 (d66525d) carries the IDENTICAL failure set — so
TSK-0087 added no class and that run is the pre-fix evidence. Six red-without-fix measurements
reproduced; E2 compatibility attacked (old approvals resolve; only new refusal: POSIX root names
with a colon at position 2 — said in the docstring); full suites green in his copies: windows
3885/14 named skips, POSIX 3860/39 named skips, 0 errors; D-fix probe: 405 sys.path entries →
24.

## Residues (named, in the classification doc)

1. AC-1 is not provable locally: the ONLY proof is the next push's hosted run — 69 ubuntu tests
   run there for the FIRST time ever, on CPython 3.14 which no local rig has. BUG-0069 STAYS
   OPEN until that run is measured green.
2. The deep-body half of bucket C skips on both runners (the arm stays measured via the
   companion test).
3. .audit/hook_events.jsonl grows through the gates themselves (H37) — rides along.
4. names_a_drive deliberately over-refuses on POSIX; test_report.py:224 is a guessed margin but
   NOT the same race (verifier's correction, taken).

## Delivery

Kit stamps unchanged (test files, workflow and docs are outside the kit hash; bump run to prove
it: dev 2026.08.29-2, office -6, research -2). ruff, validate green. Affected suites after
rework: 54 + 2131 + 5 (POSIX spot-check). Full delivery run by the lead before commit (result in
the commit message).

## What the user gets

The "All jobs have failed" mail on every push should end with the next push — and if it does
not, the classification document means the next investigation starts from the table, not from
zero. One real product defect fell out of it: state files now read drive letters the same way on
every system, so a project moved between Windows and Linux cannot mint an approval that hits
nothing.
