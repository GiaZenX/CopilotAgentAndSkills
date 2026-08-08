#!/usr/bin/env python3
"""
Gate 4 (SR-0006): the task list is not a place to keep work.

THIS ONE EXISTS NOWHERE ELSE. No kit registers a hook on `TodoWrite`, and that claim is kept true
rather than merely written down: `test_todowrite_is_gated_here_and_by_no_kit` parses every kit's
`settings/settings.json` -- the file the provider itself reads -- and goes red at BOTH ends, when a
kit starts gating the event and when this repo stops. The occasion is measured too and it is in
DEC-0003: eight defects lived in ONE line of a task list and were only ever written down because
the user asked afterwards. What is only in a task list or in a chat is gone the moment the session
is summarised.

THE RULE, and it carries no content heuristic -- prose is not inspected for intent:

    The list holds AT MOST ONE entry without an item id: the one being worked on. Every other entry
    names a `<TYPE>-nnnn` that resolves under `project_memory/`, whose type can carry work, and
    which is not terminal.

THREE CLASSES OF ENTRY, so the refusal can say which rule was broken:
  * BOUND    -- names at least one id that resolves, carries work and is open.
  * BARE     -- names no id candidate at all. One of these is allowed.
  * DANGLING -- names id candidates but none that qualify. Always refused, and never counted as
                the free entry: a mistyped or finished reference must not buy the exemption that
                "no reference at all" gets.

WHAT "CAN CARRY WORK" MEANS is the kernel's `AUTOMATA` -- see `_harness.Reference.carries_work` for
why the property is "has a lifecycle" rather than the three type names SR-0006 illustrates it with,
and for the tripwire that keeps that reading honest at both ends.

WHAT IS DELIBERATELY NOT ENFORCED: that the one bare entry is the RUNNING one. SR-0006's apposition
("den laufenden") describes which entry it will be in practice, and a `status`-test would refuse the
ordinary case of a list written before anything is in progress -- every entry `pending`. The COUNT
is what the rule turns on, and the count is what is enforced.
"""
import os
import sys

# THE IMPORT IS INSIDE THE PROTECTION -- see the same block in `gate_lead_write_scope.py` and the
# measurement in `_harness.py`'s header: a module-level import failure exits 1, and the provider
# reads that as an allow.
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


def _entry_text(entry):
    """Everything one task-list entry says, as text to scan for item ids."""
    if isinstance(entry, dict):
        return "\n".join(str(value) for value in entry.values() if isinstance(value, str))
    return str(entry)


def _label(entry):
    """A short quotation of the entry, so the refusal points at a line the reader recognises."""
    text = _entry_text(entry).replace("\n", " ").strip()
    return text if len(text) <= 90 else text[:87] + "..."


def decide():
    data = _harness.payload()
    todos = (data.get("tool_input") or {}).get("todos")
    if not isinstance(todos, list):
        # A LIST THIS GATE CANNOT READ IS NOT A LIST IT MAY WAVE THROUGH. An EMPTY list is a real
        # call (the list is being cleared) and passes below on its own; a payload whose `todos` is
        # missing or is not a list is one this gate could not inspect, and for an integrity gate
        # "not inspected" is not "allowed" -- the verdict `_harness.payload` already reaches for a
        # payload over the stdin bound.
        _harness.refuse(
            "this task list could not be inspected: the payload carries no `todos` list, so there "
            "is nothing to check.\n"
            "Remedy: if this is a legitimate call in a shape the gate does not read, report it -- "
            "the gate refuses rather than guessing, and a guess here is a silent allow.")
    if not todos:
        return
    root = _harness.repo_root(data)
    known = _harness.automata(root)
    bare, dangling = [], []
    for entry in todos:
        references = _harness.resolve_references(root, _entry_text(entry))
        if not references:
            bare.append(entry)
            continue
        if any(ref.found and ref.carries_work(known) and not ref.terminal(known)
               for ref in references):
            continue
        dangling.append((entry, references))
    if dangling:
        lines = []
        for entry, references in dangling:
            why = "; ".join("%s: %s" % (ref.text, _why(ref, known)) for ref in references)
            lines.append("  - %s\n      %s" % (_label(entry), why))
        _harness.refuse(
            "this task list names item ids that lead no open work:\n%s\n"
            "An entry that points at nothing is worse than an entry that points at nothing "
            "KNOWINGLY -- it reads as bookkeeping while carrying none.\n"
            "Remedy: capture the work as an item and name it, or drop the id from the entry (an "
            "entry with no id at all is allowed -- once, for the step being worked on)."
            % "\n".join(lines))
    if len(bare) > 1:
        _harness.refuse(
            "this task list holds %d entries without an item id; at most one may be unbound "
            "(the step being worked on right now):\n%s\n"
            "Everything else in the list is work, and work that lives only here is lost the "
            "moment this session is summarised -- which is measured, not feared (DEC-0003).\n"
            "Remedy: capture each of them and name the id in the entry, e.g.\n"
            "    PYTHONPATH=team-kits python -B -m kernel.cli --root %s create-task ...\n"
            "then write the entry as `TSK-nnnn: <what it is>`. Where the entry belongs is in "
            "CLAUDE.md, \"Wo Dinge hingehoeren\"."
            % (len(bare), "\n".join("  - " + _label(entry) for entry in bare),
               _harness.STATE_ROOT))


def _why(reference, known):
    """Why this id does not qualify -- one sentence, in the order the rule asks the questions."""
    if not reference.found:
        return "does not resolve under %s/" % _harness.STATE_ROOT
    if not reference.carries_work(known):
        return ("type %s has no lifecycle in the kernel, so it can carry no work"
                % reference.item_type)
    return "is finished (%s%s)" % (reference.status, ", archived" if reference.archived else "")


if __name__ == "__main__":
    _harness.guarded(decide)
