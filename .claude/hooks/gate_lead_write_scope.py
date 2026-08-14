#!/usr/bin/env python3
"""
Gate 1 (SR-0009 clause 1, over the protected area the contract leaves to the running derivation):
the session agent writes no versioned kit code, does not rewrite the rules it is running under, and
nobody writes canonical state through a tool -- the last of those is not clause 1 but the area
itself, which SR-0009 refuses to EVERY caller for the canonical part of `project_memory/`.

WHO IT APPLIES TO -- THREE AUDIENCES, because there are three questions. Kit content, the provider
tree and the producer of the protected area are refused to the SESSION INSTANCE only: a subagent
writing kit code is what the change circle exists for. Canonical `project_memory/` is refused to
EVERYONE; `_harness.ProtectedArea` carries why (a hand-written Evidence item opens `git commit`
outright, and it does so whoever wrote it). And a subject this gate cannot PLACE at all is refused
to everyone as well, because what it might name includes what everyone is refused;
`_harness.Unplaceable` says what makes a word one, and each of those reasons rides with the word.

"Session instance" is `_compat.calling_subagent` answering "": the payload names no agent other than
the role `.claude/settings.json` binds as `agent:`. Read that function's docstring before changing
anything here; the definition was "names someone" for a month, measured in a fixture that bound no
session agent, and it refused every lead call in every scaffolded project. This repo binds one
(`harness-lead`) so that shape is exercised where the kits are built. Measured 2026-08-05 in THIS
repo from a real hook process: a SUBAGENT's payload carries `agent_id` and `agent_type` = its own
role; the session instance's own payload could not be produced from inside a subagent and is
recorded as unmeasured in `docs/reviews/2026-08-05-tsk0007-measurements.md` (section 6).

WHICH EVENTS. The write tools AND the shell, and the second half is not a widening for its own
sake: registered on the write tools alone, every protected path was reachable in one Bash call
(`python -c`, `sed -i`, PowerShell `Set-Content`, a plain `>` redirect) -- eight such lines measured
rc 0 on 2026-08-05. `_harness.written_paths` decides what a command line WRITES, through the kits'
own shell reader.

WHAT IT PROTECTS -- see `_harness.ProtectedArea`; every area there is derived or defined, none is
listed. WHAT STAYS FREE falls out of that rather than out of an allowlist, so nothing here names it:
a path that goes into no kit hash, is outside `.claude/`, is not a file this gate's own answer was
computed from and is not canonical state is free. That half is a claim like any other and is held to
a measurement rather than to this sentence (SR-0008): `test_gate1_leaves_prose_and_bookkeeping_free`
for a subject that reaches this gate as a path, and
`test_gate1_leaves_the_sessions_own_commands_runnable` for one that reaches it as a command line --
the two halves of the registration above, and a gate that refuses either is a broken one, not a
stricter one.
"""
import os
import sys

# THE IMPORT IS INSIDE THE PROTECTION, not in front of it. A missing or truncated `_harness.py`
# raised at module level and the process exited 1, which the provider reads as "hook error, carry
# on" -- an ALLOW on every call this gate is registered on (measured 2026-08-05: all four gates
# rc 1 with the file deleted). Only `os`/`sys` may stand above this block, and only stdlib may be
# reached before it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _harness
except BaseException as error:  # noqa: BLE001 -- a gate that cannot load must not mean "allow"
    sys.stderr.write(
        "[harness gate] refused: the shared body of this repo's gates (.claude/hooks/_harness.py) "
        "could not be loaded (%r), so this call could not be judged. A gate that cannot decide "
        "refuses.\nRemedy: repair the file from a shell OUTSIDE Claude Code and start a new "
        "session -- it cannot be repaired from inside this one.\n" % (error,))
    sys.exit(2)


def _subjects(data):
    """Every path this call would write, and the direction it came from.

    A CALL THIS GATE CANNOT READ IS NOT A CALL IT MAY ALLOW. The payload of a write tool carries a
    path and the payload of a shell tool carries a command line; one that carries neither could not
    be inspected, and for an integrity gate "not inspected" is not "allowed" -- the same verdict
    `_harness.payload` already reaches for a payload over the stdin bound.
    """
    command = str((data.get("tool_input") or {}).get("command") or "").strip()
    if command:
        return _harness.written_paths(data)
    paths = _harness.compat(data).file_paths(data)
    if paths:
        return paths
    _harness.refuse(
        "this tool call could not be inspected: its payload names neither a file path nor a "
        "command line, so there is nothing to check it against.\n"
        "Remedy: if this is a legitimate call in a shape the gate does not read, report it -- the "
        "gate refuses rather than guessing, and a guess in this direction is a silent allow.")
    return []


def decide():
    data = _harness.payload()
    root = _harness.repo_root(data)
    # THE SUBJECTS FIRST, AND THAT ORDER IS THE MEASUREMENT `decision_inputs` PROMISES: it protects
    # the files this answer was computed FROM, read off what the interpreter has loaded, so a
    # producer that has not run yet is a producer nothing protects. Reading the command line is
    # where the kits' shell modules load, and they decide as much of this verdict as the stamper
    # does. `test_gate1_protects_every_reader_its_own_answer_came_from` measures it.
    subjects = _subjects(data)
    area = _harness.ProtectedArea(root)
    session = _harness.is_session_instance(data)
    for path in subjects:
        audience, reason = area.verdict(path)
        if audience is None:
            continue
        everyone = audience != _harness.SESSION_ONLY
        if not everyone and not session:
            continue
        if audience == _harness.NOWHERE_KNOWN:
            subject = "a word this line writes could not be placed:"
            remedy = ("spell the path absolutely and without a tilde prefix. WHICH of the two "
                      "reasons applies is in the reason above, and they need different remedies: "
                      "a move this gate could not compute is split apart -- the move on its own "
                      "line and the write on the next, where the position is the one the payload "
                      "states -- while a tilde prefix only the shell can resolve has to be written "
                      "out.")
        elif everyone:
            subject = "no tool call in this repo may write"
            remedy = ("write it through the kernel (`PYTHONPATH=team-kits python -B -m kernel.cli "
                      "--root %s <command>`), the route CLAUDE.md already prescribes; a proposal "
                      "that is not state yet goes to %s/%s/<item-id>/."
                      % (_harness.STATE_ROOT, _harness.STATE_ROOT, _harness.STAGING))
        else:
            subject = "the session agent may not write"
            remedy = ("delegate the change to the `harness-implementer` subagent with the item "
                      "that orders it (see CLAUDE.md, \"Die drei Rollen\"). Prose and bookkeeping "
                      "outside the areas above stay free.")
        _harness.refuse("%s %s.\n%s\nRemedy: %s" % (subject, path, reason, remedy))


if __name__ == "__main__":
    _harness.guarded(decide)
