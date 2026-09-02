#!/usr/bin/env python3
"""
PostToolUse(Edit|Write|MultiEdit|NotebookEdit|Bash|PowerShell) — record WHICH RUN wrote each staged
BOOKING reading. The booking twin of `record_filing_reading`, and it never blocks and never can:
PostToolUse has no blocking contract, and this hook has nothing to prevent.

WHY IT IS A SECOND FILE AND NOT A SECOND BRANCH IN THE FIRST. The two recorders answer the same
question about two different contracts and write into two different stores, and the one thing that
must not happen is that a failure of one silences the other. Registered in the same chained command
behind `record_filing_reading`, both exit 0 unconditionally, so the chain never stops at the first —
and the shared machinery is `_readings`, which is where a change to what an attestation IS lands
once.

WHAT IT WRITES, and where the values come from: for every `booking_reading` record THIS CALL NAMES
whose current bytes carry no attestation yet, one line into `project_memory/.books/readings.jsonl`
— the record's path, the sha256 of its bytes, the run (`agent_id` from this call's payload, the
field the provider fills to identify a spawn instance) and the sha256 of every DOCUMENT the record
names as a source. Neither value is something the writing agent stated about itself, and the store
sits inside the state directory and outside `staging/`, which is the area `gate_write_scope` refuses
every tool write and every write-capable shell line naming.
`test_an_agent_cannot_write_the_booking_attestation_store_through_the_registered_chain` measures the
covered half; a shell line that names the path NOWHERE is refused by nothing here, exactly as for the
filing store.

WHY BEST EFFORT IS THE RIGHT FAILURE MODE. Everything this hook can fail at REMOVES a reading from
the store, and a row with fewer readings than its category asks for is refused by
`gate_second_booking`. There is no failure of this hook that lets a booking through, so there is
nothing here to fail closed about.
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
import record_filing_reading  # noqa: E402

HOOK = "record_booking_reading"
EVENT = "PostToolUse"


def main():
    data = _kernel.payload(HOOK, event=EVENT)
    root = _kernel.find_repo_root(str(data.get("cwd") or ""))
    state = _kernel.state_dir(root)
    if not os.path.isdir(state):
        return
    # The paths FIRST, and through the SAME reader the filing recorder uses — so the two cannot come
    # to disagree about what a call created, and what this one cannot see is the residue that reader
    # already names (a record written inside another program is named by nobody and is not a
    # reading). The scan below then happens only for a call that really created a file in the state
    # directory, which is nearly none of them.
    named = record_filing_reading.named_by_this_call(data, root, str(data.get("cwd") or ""))
    if not named:
        return
    field, keys = _readings.contract_of(lambda name: _kernel.kernel_module(name, root),
                                        _bookings.BOOKING)
    if not field:
        # Said out loud rather than passed over: from here on every ledger row that is not already
        # committed is refused for want of readings, and a role that does not know why would look
        # for the fault in its own record.
        _kernel.record_note(HOOK, "the %s contract could not be read, so no booking reading can be "
                                  "recognised and every uncommitted ledger row will be refused"
                            % _bookings.SCHEMA)
        return
    records = [record for record in _readings.staged_records(state, field, keys)
               if record[0] in named]
    written = _readings.attest(state, records, _readings.run_identity(data), root,
                               _bookings.BOOKING)
    if written:
        _kernel.record_note(HOOK, "attested %d booking reading record(s) to run %s: %s"
                            % (len(written), _readings.run_identity(data),
                               ", ".join(path for path, _sha in written)))


if __name__ == "__main__":
    # NOT `_kernel.run_gate`, for `record_filing_reading`'s reason: that turns any escaping error
    # into a `block`, which on this event is an exit 2 that stops nothing and logs a prevention that
    # did not occur.
    try:
        main()
    except BaseException as exc:  # noqa: BLE001
        try:
            _kernel.record_note(HOOK, "could not record booking readings (%r)" % (exc,))
        except BaseException:  # noqa: BLE001 — the note is diagnostics, not the job
            pass
    sys.exit(0)
