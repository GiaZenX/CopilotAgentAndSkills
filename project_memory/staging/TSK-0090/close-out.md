# TSK-0090 close-out protocol (lead, 2026-08-29)

Round: FR-0011 — the gate suite's wall time per round, without falsifying a measurement.
Verifier: FAIL(BF-1 doc number, BF-2 shared-copy invariant) → PASS with every residue taken.

## The surprise first

The factor-11 rise (358 s → 4102 s) WAS NEVER IN THE CODE: the hot tests are AST-byte-equal
across three monthly states; the same benchmark measured 3.6× fewer shell lines/s between two
windows of one day. The driver is host load (the user's parallel sessions). The 4512 s IDLE run
of 08-13 stays honestly unexplained. BUG-0033's own record already attributed the 4101.94 s to
the verifier's parallel load.

## What the cut delivers (verifier-confirmed in his own copies)

- Process KINDS run together (AT_ONCE per kind; batches share a kind's pool; worker exceptions
  resurface — now incl. BaseException, red-first): −20…−27% on the heavy phases per window,
  −9.2% full suite under load.
- COLUMN SELECTION: -k one cell test = 23 s instead of 789–1018 s — factor 32–44 in time AND
  processes. This is the number that makes every future repair round cheap.
- THE DEADLINE PHASE CANNOT GET NEIGHBOURS within one pytest process (every thread joined,
  every pool closed) — stronger than the doc first argued; measured that neighbours eat the
  PROOF margin (4/12 under noise with a neighbour vs 0/12 without) while the verdict never
  flipped. Load is BUG-0033's territory and stays there.
- The shared check copy carries a finalizer that reds on ANY movement (changed, new, deleted —
  all three measured): 11 cases stay green, the finalizer alone says it. Without it, a gate
  that ever writes into the tree it judges would poison ten cases silently.
- Two repo tools (gate_suite_rates.py, gate_suite_margins.py) replace scratch scripts so the
  quiet-window run (accepted DEC-0053 residue) is reproducible, with measured costs named.

## Verifier rigor worth recording

He replayed both blockers and every residue mutation in his own copies (incl. a DELETE
direction of his own design on the finalizer), recomputed both corrected doc numbers from the
raw files — and retracted his own first counter-computation as his aggregation artifact. His
window was slower than the implementer's; all his numbers are labelled to their window. No
quiet-number dishonesty found anywhere.

## Hole list (this commit)

H74: no protection against a SECOND runner (and the suite now presses harder as a neighbour,
peak 10→26); host-load truth + the unexplained idle run; three priced trade-offs (authored
without column selection, deadline phase stays neighbour-free, check sets unshrunk); line-number
pointers as an open class (the H45 shift was case 2, corrected by the lead in this same tree).
Entry and measurement doc name each other (tripwire-enforced, seen red once during writing).

## Also in this commit (parallel lead work, all named)

- H45 pointer corrected (131-135 → 132-136 with the round named).
- radar/2026-08-29-claude.md + decided.md triage lines (radar + newsletter, FR-0060/61 captured,
  FR-0047 broadened); docs/reviews/2026-08-29-cd-rebinding-research.md shipped previous round.
- Live-find items from the user's real-project day: BUG-0070/0071/0072/0073, FR-0062...FR-0066.
- Decisions DEC-0053/0054/0055 (bugs-first ordering; stage-2 pull-forward; no ladder
  intermediate — static pins accepted).

## Delivery

Kit stamps unchanged ×3 (test file, tools probes and docs only). ruff, validate clean. Fresh
full runs by the lead before commit (results in the commit message). Quiet-window run: OPEN,
accepted per DEC-0053, two commands in the measurement doc §7.
