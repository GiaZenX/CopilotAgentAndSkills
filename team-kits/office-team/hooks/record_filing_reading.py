#!/usr/bin/env python3
"""
PostToolUse(Edit|Write|MultiEdit|NotebookEdit|Bash|PowerShell) — record WHICH RUN wrote each staged
classification reading. It never blocks and never can: PostToolUse has no blocking contract, and
this hook has nothing to prevent. It is the half of the four-eyes filing rule that makes the other
half decidable, and it is separate from that half for one reason — the question "who wrote this
file" has an answer only in the payload of the call that wrote it, and `gate_second_reading` runs
on a LATER call, judging a move.

WHAT IT WRITES, and where the values come from. For every reading record THIS CALL NAMES whose
current bytes carry no attestation yet, one line into `project_memory/.filing/readings.jsonl`: the
record's path, the sha256 of its bytes, the run — `agent_id` from this call's payload, the field the
provider fills to identify a spawn instance — and the sha256 of every DOCUMENT the record names as a
source, read off the filesystem. Neither value is something the writing agent stated about itself.
`_readings` carries the rest of that argument (`source_digests` for why the document is bound here
rather than in a field of the record, and the direction the one unmeasured assumption fails in).

ONLY WHAT THIS CALL NAMES, and that is a hole closed rather than a nicety. The first cut stamped
every unattested record it could FIND, which attributes a record whose own PostToolUse never ran to
the next run that happens to make any tool call — so one agent's two records could come back as two
runs, which is exactly the thing the gate refuses. `named_by_this_call` reads the paths off the
payload through the SHARED readers, so what it cannot see is the residue those already carry.

WHY IT STILL HASHES THE FILE ON DISK instead of the payload's content. A record arrives through
`Write`, through an `Edit` of an existing one, or from a shell redirect, and only the first carries
the finished bytes in its own payload. The file's bytes are the one reading that is the same for all
three — and hashing them is also what makes an attestation stop applying the moment the record is
edited.

WHY BEST EFFORT IS THE RIGHT FAILURE MODE HERE. Everything this hook can fail at removes a reading
from the store, and a filing with fewer than two readings is refused by `gate_second_reading`. There
is no failure of this hook that opens a filing, so there is nothing here to fail closed ABOUT; an
exit 2 on a non-blocking event would only write a prevention into the audit log that never happened
(`_kernel.record_note` is the shape that does not).
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

import _compat  # noqa: E402
import _filing  # noqa: E402
import _readings  # noqa: E402

HOOK = "record_filing_reading"
EVENT = "PostToolUse"


def named_by_this_call(data, root, cwd):
    """{state-relative path} of every file THIS tool call creates, as the shared readers see it.

    The readers are the ones the filing wall already uses — `_compat.file_paths` for a tool write,
    `_filing.created` for a shell line — so this hook cannot disagree with `gate_filing` about what
    a command line writes, and what it does NOT see is the residue those readers already name: a
    write performed inside another program (`python -c "open(...).write(...)"`, a script). A record
    that arrives that way is never attested, is therefore not a reading, and refuses a filing rather
    than allowing one.
    """
    state = _kernel.state_dir(root)
    bases = _filing.reading_bases(root, cwd)
    if data.get("tool_name") in ("Bash", "PowerShell"):
        created = _filing.created(str((data.get("tool_input") or {}).get("command") or ""), bases)
    else:
        created = [(path, bases) for path in _compat.file_paths(data)]
    found = set()
    for token, token_bases in created:
        for base in token_bases:
            try:
                relative = os.path.relpath(
                    os.path.abspath(os.path.join(base, str(token).replace("\\", "/"))), state)
            except (OSError, ValueError):     # a different drive, an embedded NUL
                continue
            relative = relative.replace(os.sep, "/")
            if not relative.startswith("../") and relative != "..":
                found.add(relative)
    return found


def main():
    data = _kernel.payload(HOOK, event=EVENT)
    root = _kernel.find_repo_root(str(data.get("cwd") or ""))
    state = _kernel.state_dir(root)
    if not os.path.isdir(state):
        return
    # The paths FIRST, so the calls that wrote nothing into the state directory — which is nearly
    # all of them — pay nothing beyond this reading: the kernel import and the staging scan below
    # happen only for a call that really created a file there.
    named = named_by_this_call(data, root, str(data.get("cwd") or ""))
    if not named:
        return
    field = _readings.contract(lambda name: _kernel.kernel_module(name, root))
    if not field:
        # No contract, no recogniser. Said out loud rather than passed over in silence: from here on
        # every filing into a plan-covered path is refused for want of readings, and a role that
        # does not know why would look for the fault in its own record.
        _kernel.record_note(HOOK, "the %s contract could not be read, so no reading can be "
                                  "recognised and every gated filing will be refused"
                            % _readings.SCHEMA)
        return
    written = _readings.attest(state, [record for record in _readings.staged_records(state, field)
                                       if record[0] in named],
                               _readings.run_identity(data), root)
    if written:
        _kernel.record_note(HOOK, "attested %d filing reading record(s) to run %s: %s"
                            % (len(written), _readings.run_identity(data),
                               ", ".join(path for path, _sha in written)))


if __name__ == "__main__":
    # NOT `_kernel.run_gate`: that turns any escaping error into a `block`, which on this event is an
    # exit 2 that stops nothing and logs a prevention that did not occur. See the module docstring
    # for why there is nothing here to fail closed about.
    try:
        main()
    except BaseException as exc:  # noqa: BLE001
        try:
            _kernel.record_note(HOOK, "could not record filing readings (%r)" % (exc,))
        except BaseException:  # noqa: BLE001 — the note is diagnostics, not the job
            pass
    sys.exit(0)
