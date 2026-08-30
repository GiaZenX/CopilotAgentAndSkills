# TSK-0094 + TSK-0095 close-out protocol (lead, 2026-08-30)

Two rounds, one subject: FR-0063 — the newsletter line about `--restricted`. TSK-0094 measured;
TSK-0095 corrected the prose the measurement falsified. Verifier: TSK-0094 CONFIRMED-with-blockers
(the finding was written onto a flag, the proposed floor overclaimed) → corrected; TSK-0095
FAIL(office list incomplete) → FAIL(two fresh comment overclaims) → PASS.

## What was measured (TSK-0094, both roles independently, CLI 2.1.251)

A client start mode that does NOT load the project settings removes the kit's entire enforcement
apparatus — all four registration surfaces — while the file tools stay writable in the project.
THREE members measured (`--restricted`, `--safe-mode`, `--setting-sources user`); uniform on the
enforcement question, different elsewhere (`--safe-mode` brings Bash, bypassPermissions and
out-of-directory writes; `--restricted` drops permissions.deny so a .env secret reads in clear).
THE CHAIN driven against the running gates: a DRAFT PR refuses merge (rc 2); after four ordinary
file operations (status edit + three passing EVD files) merge AND push run rc 0 while
`kernel.cli validate` reports 0 errors — the kernel reads items with os.listdir, so a planted
file IS state. The verifier's restricted session performed those four operations ITSELF.
Four edges named: scripts/harness.py writable and OUTSIDE the trust hash; permissions.deny gone;
tool surface 7 → 152/159 incl. the user's MCP servers; the constitution does not load.

## What was corrected (TSK-0095)

The three shipping sentences that claimed absolute refusal now carry their measured condition —
as a PROPERTY ("a client start mode that does not load this project's settings"), never a flag,
so a fourth member is covered the day it exists. The long floor lives once per kit in
hooks/ENFORCEMENT.md §0, byte-identical, and the verifier MEASURED the delivery decision: he
scaffolded a project, drove gate_write_scope, and the refusal hands the reader exactly that file.
No over-correction: the lock is still claimed, and true, for a settings-loading session.

## What the rounds caught in themselves

- The implementer's first floor sentence claimed per-role hooks the OFFICE kit does not have
  (measured 0 of 10) — this round's own error class, self-found.
- The verifier found the office WHAT-RUNS list understating by two: gate_second_reading and
  record_filing_reading — OUR OWN TSK-0087 hooks, running but unlisted, with no test able to
  catch it. Now the list is DERIVED from the registrations in both directions (5 reds, three of
  the verifier's own design incl. file-exists-but-unregistered and a duplicate).
- Two freshly written justifications overclaimed and were corrected: a majority rule justified by
  a 25-span competitor that measures FOUR spans, and a sibling docstring still saying "really
  states" where the measurement says "addresses".
- The lead's own hole-list entry claimed "0 errors, 0 warnings" where the two rigs differ —
  corrected to what both measured.

## Hole list

H78 — OPEN, NOT CLOSEABLE, with its named bound (the third state CLAUDE.md allows): why not
closeable (the client removes the apparatus before a kit file is read; the only surface that
still binds is the invocation line, i.e. the attacker's) and what bounds it instead (such modes
must be started deliberately; the kit prose stops claiming otherwise; the user was told directly,
with the one practical consequence: do not start a kit project in such a mode). Plus the two
residues: the same absolute claim outside the six corrected texts (78 reach claims in 42 files,
54 unconditioned — the LEAD ROLE FILES load at every session start while ENFORCEMENT.md loads
never), and the reader's own two-noun-phrase limit (a single reworded return to the absolute form
is invisible).

## Delivery

Kits: dev/research 2026.08.30-13, office -14. ruff, validate clean; both ratchets re-recorded with
journal lines; mirrors untouched (ENFORCEMENT.md in KIT_SPECIFIC_HOOKS with its reason). Suites
through the rounds: 3184 → 3185 passed / 14 skipped, plus 77 passed on the final comment fix.
Full suite fresh by the lead before commit.
