#!/usr/bin/env python3
"""
PreToolUse(Agent|Task) — specialist spawns require an APPROVED, un-tampered PROC item.

The PROC is the office kit's unit of user approval (like a PRD in the dev kit). Opt-in checks are
fake security -- leave the reference out and nothing fires -- so this gate is INVERTED: every
specialist work order MUST name a `PROC-nnnn`, the named PROC must stand in a status a user
approval put it in, and its approval-relevant content must still hash to the `approved_hash` the
mint stamped on it. Editing an approved PROC past the kernel voids the approval.

THE V1 BOOTSTRAP HOLE IS GONE, and that is the whole reason this file was rewritten. The V1 gate
opened a single `process_definitions.yaml` registry at the state root, exited 0 when it was absent -- which in
every V2 project it is, the store having been dissolved into `procedures/active/PROC-nnnn.yaml` --
and exited 0 again when nothing in it was approved. Both halves read as "no PROC yet, so let the
onboarding work happen"; measured as a real hook process against a scaffolded office project, they
read as rc 0 on every spawn, forever. Spec II.4 is explicit about which way that goes:
"Das V1-Bootstrap-Loch von gate_proc_approved (leerer PROC-Bestand liess Spawns passieren)
entfaellt: leerer Zustand blockiert -- ausser im expliziten Installer-Bootstrap".

SO AN EMPTY PROC STORE BLOCKS, and the way out is walkable rather than a shrug: the office manager
captures the procedure itself (`python scripts/harness.py capture PROC ...`), asks for the user's
approval (`request-approval scope PROC-nnnn`), and the mint walks it to APPROVED and stamps the
hash. None of that needs a spawn, which is what makes fail-closed affordable here -- the lead can
reach the first approved PROC alone. The one exception is the installer's own bootstrap window
(`_kernel.bootstrap_active`), which spec II.4 puts under a lock, an empty target state, a user
confirmation and a TTL, and which is therefore not something the lead can grant itself.

WHICH STATUSES COUNT is asked of the kernel (`approvals.approved_statuses("PROC")`), not written
out here: the chain says DRAFT -> APPROVED -> ACTIVE and `APPROVAL_TRANSITIONS` says a scope
approval walks the first of those edges, so "approved and still in use" follows from the automaton.
A RETIRED PROC falls out on its own, being terminal.

The GATE_PREAMBLE below must stay the first executable statement — see _kernel.py for why. Only
the docstring may precede it, because a docstring cannot fail.
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

import re  # noqa: E402 — after the preamble, by the rule the preamble exists for

HOOK = "gate_proc_approved"
SPAWN_TOOLS = ("Agent", "Task")
PROC_RX = re.compile(r"\bPROC-\d{4,}\b")


def _executable_procs(state, approvals):
    """{id: item} for every PROC a work order may legitimately execute right now.

    Reads the typed item directory, so a file that does not parse or does not look like an item is
    simply not an executable PROC -- the fail-closed direction, since the alternative would be to
    let an unreadable file stand in for an approval. `report.validate_state` is what NAMES such a
    file; a spawn gate only has to refuse to count it.
    """
    allowed = approvals.approved_statuses("PROC")
    found = {}
    directory = state.active_dir("PROC")
    if not os.path.isdir(directory):
        return found
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".yaml"):
            continue
        try:
            item = state._read_yaml(os.path.join(directory, name))
        except Exception:
            continue
        if isinstance(item, dict) and item.get("status") in allowed:
            found[str(item.get("id") or name[:-5])] = item
    return found


def _refuse(why, remedy):
    _kernel.block(HOOK, "specialist spawn refused: %s" % why, event="PreToolUse", remedy=remedy)


def main():
    data = _kernel.payload(HOOK)
    if data.get("tool_name") not in SPAWN_TOOLS:
        sys.exit(0)
    root = _kernel.find_repo_root(data.get("cwd"))
    if _kernel.bootstrap_active(root):
        sys.exit(0)   # the explicit installer/migration window (spec II.4), never a config flag
    if not os.path.isdir(_kernel.state_dir(root)):
        _refuse("this repo has no canonical project state, so no work order can be checked "
                "against an approved procedure (spec II.4 fail-closed).",
                "initialise the project via the installer/scaffold, the only path that may run "
                "with an empty state.")
    state = _kernel.open_state(root)
    approvals = _kernel.kernel_module("approvals", root)
    executable = _executable_procs(state, approvals)
    if not executable:
        _refuse("this project has no approved procedure at all, and the office kit dispatches "
                "specialists only to execute one (spec II.4: an empty state blocks -- the V1 gate "
                "waved these spawns through).",
                "capture the procedure and obtain the user's approval first -- "
                "`python scripts/harness.py capture PROC ...` then "
                "`python scripts/harness.py request-approval scope PROC-nnnn`; neither needs a "
                "spawn, so the first procedure is reachable without one.")

    prompt = str((data.get("tool_input") or {}).get("prompt") or "")
    named = PROC_RX.findall(prompt)
    if not named:
        _refuse("the work order names no PROC-nnnn, and %d approved procedure(s) exist "
                "(%s)." % (len(executable), ", ".join(sorted(executable))),
                "name in the work order the PROC this specialist executes.")
    for proc_id in named:
        item = executable.get(proc_id)
        if item is None:
            _refuse("%s is not an approved, active procedure of this project (approved: %s)."
                    % (proc_id, ", ".join(sorted(executable)) or "none"),
                    "name a PROC the user approved, or obtain the approval for this one via "
                    "`python scripts/harness.py request-approval scope %s`." % proc_id)
        recorded = item.get(approvals.APPROVED_CONTENT_HASH_FIELD)
        if not recorded:
            _refuse("%s carries no %s, so nothing proves its steps are the ones the user "
                    "approved." % (proc_id, approvals.APPROVED_CONTENT_HASH_FIELD),
                    "re-run the approval flow for %s -- the mint stamps the hash." % proc_id)
        if approvals.approved_content_hash("PROC", item) != recorded:
            _refuse("%s was edited past the kernel after its approval (its content no longer "
                    "hashes to the stamped %s), so the approval is void."
                    % (proc_id, approvals.APPROVED_CONTENT_HASH_FIELD),
                    "restore the approved content, or obtain the user's approval for the new one "
                    "via `python scripts/harness.py request-approval scope %s`." % proc_id)
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
