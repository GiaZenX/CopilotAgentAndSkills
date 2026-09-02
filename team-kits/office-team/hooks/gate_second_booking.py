#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell) — a figure does not leave this project on ONE reading. FR-0065, the
booking twin of the four-eyes filing rule FR-0035 built, and the user's own finding: the numbers that
end at the Finanzamt had thinner assurance than the question which folder a PDF lands in.

WHAT THIS ADDS TO `gate_ledger_valid`, which it stands behind in the same chained command. That gate
runs the project's validator, and the validator's arithmetic layer (`net x (1 + vat) = gross`) judges
a triple against ITSELF: a triple that reconciles is accepted, whoever it belongs to. The measured
near-miss is BUG-0072 — the kit extractor returned 14.28 instead of 214.20 net, and only the
bookkeeper's own hand cross-check caught it. This gate asks the second question: has a SECOND run
read the source document into these same figures. The two layers have distinct catch classes and
neither replaces the other — non-reconciling triples are the validator's, wrong-but-reconciling ones
are this gate's (the wrong document's consistent total, a transposition that still adds up, the wrong
category).

THE ORDER IN THE CHAIN IS LOAD-BEARING, unlike the filing chain's, and `settings.json` says so too:
`_gate.py` stops at the first refusal, and a ledger that does not even parse into valid rows has to
be reported as broken data before anybody is told to go and read a document again. A row this gate
cannot judge is a row the gate ahead has already refused.

WHEN IT ASKS, and the one moment it deliberately does not. `gate_ledger_valid.requires_a_sound_ledger`
is the reader — one answer for both gates — and this one acts on its SHELL moments only: commit,
push, merge, tag, report. It does NOT act on a specialist DISPATCH, although that reader names it,
and the reason is not thrift: the second reading is written by a second SPAWN, so a dispatch refused
for want of readings would refuse the only route out of its own refusal. That is the deadlock
`gate_ledger_valid`'s header records under "a corrupt marker with no ledger present deadlocked the
repo", and it is why the two gates differ here.
`test_the_booking_gate_stands_at_the_shell_moments_and_not_at_a_dispatch` measures both halves.

WHICH ROWS IT JUDGES, what it can see and what it cannot, and the hole `git` leaves: all of that is
`_bookings`' own header, which is where the argument lives rather than in a shorter version of it
here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _kernel
except BaseException as exc:  # noqa: BLE001 — a hook that cannot load must not mean "allow"
    sys.stderr.write("[team-kit hook] refused: could not load hook helpers (%r). Remedy: run "
                     "`python scripts/harness.py doctor`; a partial checkout or half-finished kit update is the "
                     "usual cause.\n" % (exc,))
    sys.exit(2)

import _bookings  # noqa: E402
import _readings  # noqa: E402
import gate_ledger_valid  # noqa: E402

HOOK = "gate_second_booking"
SHELL_TOOLS = ("Bash", "PowerShell")
# How many findings and how many readings a single refusal prints. A quarter's worth of unread rows
# is a real state for a project meeting this layer for the first time, and a refusal that printed all
# of them would be a wall of text nobody reads; the count is always stated in full.
MAX_ROWS_SHOWN = 8
MAX_READINGS_SHOWN = 4
# The clause a BUDGET refusal adds, spelled apart from the message it joins: "we did not get to
# look" sends the reader somewhere else than "nobody read this row", and a remedy that mixed the two
# would offer re-reading a document to somebody whose problem is the size of one uncommitted batch.
BUDGET_REMEDY = (
    "\nFor the rows that were NOT looked at: this check stops at its own budget rather than "
    "being killed mid-decision by the host, because a killed hook is a silent pass. Commit in "
    "smaller batches -- every row already in `HEAD` is skipped on the next run, so the work "
    "shrinks each time -- and treat a ledger that needs longer than %d s in ONE uncommitted batch "
    "as a finding of its own.") % _bookings.TOTAL_BUDGET


def refuse(operation, verdicts, unjudged):
    """The one refusal, with the rows and the readings the reader has to act on spelled out.

    THE TWO KINDS ARE TOLD APART, for `gate_ledger_valid._refuse_if_invalid`'s measured reason:
    "this row is not read twice" and "this file could not be judged at all" send the reader to two
    different places, and reporting them as one told an operator to re-read rows nobody had looked
    at.
    """
    detail, rows = [], 0
    for rel in sorted(verdicts):
        detail.append("  %s:" % rel)
        for label, why, about, keys in verdicts[rel][:MAX_ROWS_SHOWN]:
            detail.append("    - %s: %s" % (label, why))
            for one in about[:MAX_READINGS_SHOWN]:
                detail.append("        read: " + one.named(keys))
        rows += len(verdicts[rel])
        if len(verdicts[rel]) > MAX_ROWS_SHOWN:
            detail.append("    ... and %d more row(s) in this file"
                          % (len(verdicts[rel]) - MAX_ROWS_SHOWN))
    for rel in sorted(unjudged):
        detail.append("  %s: NOT CHECKED — %s" % (rel or "the ledger", unjudged[rel]))
    # A BUDGET refusal and a MISSING-READING refusal send the reader to two different places, so the
    # remedy grows a clause rather than the message growing a second headline. `_bookings._spent` is
    # the one sentence that marks it, asked for here rather than re-spelled.
    ran_out = any(_bookings._spent() in why for why in unjudged.values())
    _kernel.block(
        HOOK,
        "%d ledger row(s) that are not yet in `HEAD` are booked on fewer independent readings than "
        "their category asks for, so %s is blocked (FR-0065). The arithmetic check these rows "
        "passed says the amounts add up, not that they came off the right document — that is the "
        "reading this gate is missing.\n%s" % (rows, operation, "\n".join(detail[:40])),
        remedy="have a SECOND run read the SOURCE DOCUMENT — one that was not given the first "
               "answer and not the row — and let it write its own `%s` record into "
               "`project_memory/staging/<TSK-ID>/`, naming the document's own path as `source` and "
               "the figures it read for the row's other fields. Where a reading and the row differ, "
               "nothing is committed: put BOTH answers to the USER and book what they decide. A "
               "record counts only once `record_booking_reading` has attested WHICH RUN wrote those "
               "exact bytes and what the document looked like then, so a record produced inside "
               "another program, one edited after it was attested, and one whose document has been "
               "replaced since are not readings. A category the USER has released with "
               "`%s: false` in `master_data.yaml` asks for one reading — never for none. What the "
               "attestation shows is the run and not the reader's attention: it cannot see whether "
               "the second run read the first record, and this gate does not claim it can.%s"
               % (_bookings.SCHEMA, _readings.SECOND_READING, BUDGET_REMEDY if ran_out else ""))


def main():
    # No `hook_event_name` guard, for `gate_filing`'s reason: this gate is registered on PreToolUse
    # and nowhere else, so the event is settled by settings.json.
    data = _kernel.payload(HOOK)
    if data.get("tool_name") not in SHELL_TOOLS:
        sys.exit(0)
    operation = gate_ledger_valid.requires_a_sound_ledger(data)
    if not operation:
        sys.exit(0)
    root = _kernel.find_repo_root(str(data.get("cwd") or ""))
    if not os.path.isdir(os.path.join(root, _bookings.LEDGER_DIR)):
        sys.exit(0)   # no books in this project: nothing to have read twice
    verdicts, unjudged, stood_down = _bookings.unread_rows(
        root, lambda name: _kernel.kernel_module(name, root))
    for rel, why in sorted(stood_down.items()):
        # A stand-down is written into the audit log and NOT into a refusal: see the module header
        # and `_bookings.unread_rows` for why refusing here would wall off the way out of itself.
        _kernel.record_note(HOOK, "stood down for %s: %s" % (rel, why))
    if verdicts or unjudged:
        refuse(operation, verdicts, unjudged)
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
