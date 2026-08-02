#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell) — block merge/push while the project state is incomplete.

WHAT MOVED IN V2. The V1 version answered "is anything still an empty template?" by scanning
`project_memory/*.yaml` itself: comments dropped, empty containers detected, `applicable: false`
honoured, plus a hand-written special case per monolith. Those monoliths are gone (spec II.2), and
the question they were a proxy for -- "does every item say what its type requires it to say?" --
now has one machine-readable answer in `kernel/report.validate_state`, checked against the per-type
field contracts in `kernel/backlog_types` (REQUIRED_FIELDS + the status automata; the files under
`kernel/schemas/` are the envelope/companion contracts and hold no item schema). This gate calls
that answer instead of re-deriving it: a second implementation of "what counts as complete" is
exactly how the two drift, and the validator is the one CI and `python scripts/harness.py doctor` also read.

NEITHER OF ITS OWN TEETH HAS A KEY INSIDE THE SESSION, and since 2026-08-02 the message says so.
The two files below are kit DOCUMENTS (`kernel.layout.is_project_document`): §0 locks the state
directory against every tool write and makes no exception for them, and the kernel has no path
builder that can name them either. Measured: Write rc 2, shell heredoc rc 2, no writer in
`.claude/kernel`. So this gate can block merge and push on a condition nothing inside the session
can satisfy — that is a REPORTED gap, not a hidden one, and `remedy_for` names who can close it
instead of sending a role to `python scripts/harness.py validate`, which answers
`0 error(s), 0 warning(s)` in exactly this state.

The gate keeps its own teeth for the two things the validator structurally cannot see:
  * `product/masterplan.md` -- prose, not a typed item, and therefore outside every schema. An
    unfilled north star means the plan lives only in the chat that produced it (the observed gap).
  * `project_config.yaml` -- project configuration, not canonical state; the validator never opens
    it. A config with no project name, or with `stacks:` still `[TODO]`, would otherwise reach a
    merge undeclared, which is what makes half the pipeline checks silently skip.

Only fires on `git push`/`git merge`, and only once a root item exists (`_root.has_root_item`) --
before that a repo is still being set up, and a merge gate firing there blocks the setup it exists
to protect.
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

import json  # noqa: E402
import re  # noqa: E402

import _compat  # noqa: E402
import _root  # noqa: E402

HOOK = "gate_memory_complete"
MASTERPLAN = os.path.join("product", "masterplan.md")
# the placeholder the shipped masterplan template carries in its title line; a masterplan that
# still names "<project name>" was never written
TEMPLATE_MARKER = "<project name>"
MAX_LISTED = 8

CONFIG_NAME_RE = re.compile(r"(?m)^\s*name:\s*(.*)$")
CONFIG_STACKS_INLINE_RE = re.compile(r"(?m)^\s*stacks:\s*\[([^\]]*)\]")
CONFIG_STACKS_BLOCK_RE = re.compile(r"(?m)^[ \t]*stacks:[ \t]*$")
CONFIG_STACK_ITEM_RE = re.compile(r"[ \t]*-[ \t]*([A-Za-z0-9_+-]+)[ \t]*$")


def read(path):
    try:
        # utf-8-sig: a PS 5.1 rewrite prepends a BOM and the ^-anchored key regexes
        # then never match — a correctly filled config caused a PERMANENT push block (audit)
        with open(path, encoding="utf-8-sig", errors="ignore") as fh:
            return fh.read()
    except Exception:  # noqa: BLE001 — an unreadable optional file is simply not a finding
        return ""


def config_unfilled(text):
    """project_config.yaml needs a real project name and, if it lists stacks, >=1 non-TODO stack."""
    m = CONFIG_NAME_RE.search(text)
    name = (m.group(1).split("#", 1)[0].strip().strip("'\"") if m else "")
    if not name:
        return True
    if re.search(r"(?m)^\s*stacks:", text):  # only enforce stacks when the key is present
        stacks = []
        mi = CONFIG_STACKS_INLINE_RE.search(text)
        if mi:
            stacks = [s.strip().strip("'\"").lower() for s in mi.group(1).split(",") if s.strip()]
        else:
            mb = CONFIG_STACKS_BLOCK_RE.search(text)
            if mb:
                for line in text[mb.end():].splitlines():
                    mm = CONFIG_STACK_ITEM_RE.match(line)
                    if mm:
                        stacks.append(mm.group(1).lower())
                    elif line.strip():
                        break
        if not [s for s in stacks if s != "todo"]:
            return True
    return False


# How much of a block message identifies it. The cap is the reason for the prefix: `_audit`
# truncates a recorded reason at 2000 characters, and eight findings with a remedy each reach that
# — a full-message comparison would then match a stored reason that was cut mid-sentence and stop
# counting exactly when the repetition matters most. A prefix short enough to always be stored
# whole compares like with like. (It does NOT exist to survive the escalation suffix: the key is
# built before the suffix is appended, and `repeat_count` compares with `startswith`.)
REASON_KEY_CHARS = 500


def repeat_count(root, key):
    """How often this gate already blocked with the SAME leading reason (audit log).

    A real night produced ~14 identical blocks without anyone being told to stop retrying and fix
    the cause; the escalation below is what turns the 3rd identical block into an instruction.
    """
    try:
        count = 0
        log = os.path.join(root, "project_memory", ".audit", "hook_events.jsonl")
        with open(log, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except Exception:  # noqa: BLE001 — a truncated line is not a data point
                    continue
                if (entry.get("hook") == HOOK and entry.get("event") == "block"
                        and str(entry.get("reason") or "").startswith(key)):
                    count += 1
        return count
    except Exception:  # noqa: BLE001 — no audit log yet, or unreadable: no escalation, no crash
        return 0


def state_errors(root):
    """The state validator's ERROR findings (spec II.4 gate 4), formatted one per line.

    Warnings are deliberately not fatal: "terminal item awaiting archive" is housekeeping, and a
    gate that blocks a merge on housekeeping gets worked around instead of fixed.

    This is the EXPENSIVE reader among the merge gates, and knowingly so: `validate_state` takes
    the kernel lock (30 s) and forks a `git diff` for the consumed-approvals rule, on a push. It
    is affordable because a push happens once per work cycle, not once per tool call, and it is
    the price of the gate asking the validator rather than re-deriving completeness. The cost that
    is NOT free: while another kernel operation holds the lock, the timeout arrives here, and
    `run_gate`/`fail_closed` turn it into a blocked push. That is the correct direction for an
    integrity gate — "the state could not be read" must never read as "the state is fine" — but it
    is a real interaction, which is why `gate_packaging_decision`, running on the same event,
    deliberately reads its one field WITHOUT taking a second lock.
    """
    report = _kernel.kernel_module("report", root)
    findings = report.validate_state(_kernel.open_state(root))
    return ["%s: %s -> %s" % (f["item"], f["message"], f["remedy"])
            for f in findings if f.get("severity") == "error"]


def remedy_for(documents, validator_errors):
    """The way out, built from the findings that actually FIRED.

    WHY IT IS BUILT AND NOT WRITTEN. The single fixed remedy this replaces said "run
    `python scripts/harness.py validate` for the full list" — and in the state a fresh project is
    in, the two document findings below fire while `validate` answers `0 error(s), 0 warning(s)`
    (measured 2026-08-02). A remedy that sends a role to a command reporting nothing is a remedy
    that teaches the gate is broken.

    THE DOCUMENT HALF STATES THE DEAD END INSTEAD OF PAPERING OVER IT. `product/masterplan.md` and
    `project_config.yaml` are kit DOCUMENTS (`kernel.layout.is_project_document`): no
    `harness.py` command writes them, and §0 of every constitution locks the state directory
    against every tool write with no exception for exactly these files. Measured 2026-08-02, all
    three routes: Write rc 2, shell heredoc rc 2, no kernel writer. So this block genuinely has no
    key inside the session, and the only useful thing a message can do is say so and name who can
    close it — a remedy that pretends otherwise sends a role into a retry loop, which is what the
    repeat-block escalation above exists to count.

    THE VALIDATOR HALF names `archive`, and that is the correction the previous wording needed:
    "closed through its status automaton" is what a role does with `transition <ID> CANCELLED`,
    and measured against a cross-root `derives_from` the error SURVIVES that transition (a
    cancelled item is still an active item) and gains an "awaiting archive" warning on top. Only
    `archive` clears it.
    """
    parts = []
    if documents:
        many = len(documents) > 1
        parts.append(
            "%s %s kit DOCUMENT%s, not %s -- and %s has NO writer inside this session: no "
            "`python scripts/harness.py` command writes %s, and §0 locks the state directory "
            "against every tool and shell write with no exception for %s. Do not retry: tell the "
            "user this file is unfilled and that only they can fill it (an editor outside the "
            "session; `init_project_memory` is copy-if-absent and will not overwrite it)."
            % (", ".join(documents), "are" if many else "is", "s" if many else "",
               "typed items" if many else "a typed item", "that" if many else "it",
               "them" if many else "it", "them" if many else "it"))
    if validator_errors:
        parts.append(
            "The remaining findings come from the state validator: `python scripts/harness.py "
            "validate` lists them all with their own remedies. An item that genuinely does not "
            "apply leaves the ACTIVE store to stop counting — `python scripts/harness.py "
            "transition <ID> CANCELLED` and then `python scripts/harness.py archive <ID>`; the "
            "cancellation alone does not clear the finding, because a cancelled item is still an "
            "active one. An item whose FIELDS are wrong cannot be corrected in place (a work "
            "order is frozen outside DRAFT): re-plan it in DRAFT, or archive it and create the "
            "right one.")
    return " ".join(parts)


def main():
    # No `hook_event_name` guard: this gate is registered on PreToolUse and nowhere else, so
    # the event is settled by settings.json. Re-checking a field a provider may simply omit
    # would turn the gate into a silent exit 0 -- the failure this whole phase is about.
    data = _kernel.payload(HOOK)
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        sys.exit(0)
    # Detection lives in _compat.wants_push_or_merge (single home): applicability is decided on
    # the git SUBCOMMAND of a `git` word the shell would execute -- so no quoting, escaping, line
    # break or wrapper word spells the verb past this gate, and a verb the shell only builds at
    # run time counts as every verb. A commit MESSAGE about a push stays a message (it once
    # re-triggered a full gate), because it is an argument, not a word git was handed.
    if not _compat.wants_push_or_merge(((data.get("tool_input") or {}).get("command") or "")):
        sys.exit(0)

    root = _kernel.find_repo_root(data.get("cwd"))
    if not os.path.isdir(_kernel.state_dir(root)):
        sys.exit(0)
    # only gate once there is real work — see `_root.has_root_item`, the ONE definition five gates
    # used to compute for themselves by grepping the product_requirements monolith
    if not _root.has_root_item(root):
        sys.exit(0)

    documents, unfilled = [], []
    masterplan = os.path.join(_kernel.state_dir(root), MASTERPLAN)
    if os.path.isfile(masterplan) and TEMPLATE_MARKER in read(masterplan):
        unfilled.append("%s: still the unfilled template — write the real masterplan"
                        % MASTERPLAN.replace(os.sep, "/"))
        documents.append(MASTERPLAN.replace(os.sep, "/"))
    config = os.path.join(_kernel.state_dir(root), "project_config.yaml")
    if os.path.isfile(config) and config_unfilled(read(config)):
        unfilled.append("project_config.yaml: no project name, or `stacks:` still TODO — the "
                        "pipeline checks are selected by that list, so an undeclared stack is an "
                        "unchecked stack")
        documents.append("project_config.yaml")
    validator = state_errors(root)
    problems = unfilled + validator
    if not problems:
        sys.exit(0)

    shown = problems[:MAX_LISTED]
    message = ("the project state is not complete enough to merge (%d finding(s)):\n  %s"
               % (len(problems), "\n  ".join(shown)))
    repeats = repeat_count(root, message[:REASON_KEY_CHARS])
    if repeats >= 2:
        message += (
            "\nREPEAT BLOCK #%d for the SAME findings — STOP retrying the push and fix the cause "
            "in THIS cycle: task the owning role to complete the item(s) before anything else."
            % (repeats + 1))
    _kernel.block(HOOK, message, remedy=remedy_for(documents, validator))


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
