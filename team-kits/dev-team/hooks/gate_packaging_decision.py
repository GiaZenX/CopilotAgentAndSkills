#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell) — block merge/push while the packaging/deployment decision is unmade.

Generalises the "Docker was forgotten" failure mode: HOW the software is built and shipped must be
a CONSCIOUS choice (even "none / library" is valid), never implicit.

WHERE THE ANSWER LIVES NOW. V1 read `packaging.method` out of the `architecture.yaml` monolith,
which every project carried as a shipped template with `method: TODO` — so the gate effectively
fired from the first PRD onwards, and only a real value cleared it. That monolith is dissolved
(spec II.6a): `packaging.method` is a field on a lean architecture item, one of the typed items
under the kernel's ARC directory. Keeping the SAME teeth therefore means keeping the same trigger,
not the same file: once a root item exists, some active architecture item must state a resolved
packaging method. "No architecture item at all" is an unmade decision, not an exemption — reading
it as one would be the exact failure this lockstep exists to prevent, since the template that used
to guarantee the question got asked no longer ships.

The directory is never spelled out here; it comes from `kernel.backlog_types.ACTIVE_DIRS` via
`ProjectState.active_dir("ARC")`, so a relocation of the typed state moves this gate with it.

HOW THE ANSWER GETS THERE. `project_memory/**` is kernel-only for tool writes (`gate_write_scope`,
on Edit/Write AND Bash), so the field this gate reads has to be writable through the kernel or the
gate is a block with no exit. `kernel.staging.freeze_architecture(..., packaging={"method": ...})`
is the one path that creates an ARC item — `capture` refuses the type — and until 2026-07-31 that
function had no caller a role could reach, which made this gate exactly the block with no exit the
paragraph above claimed it was not: measured in a scaffolded project, `git merge` was rc 2 for
"no architecture item yet" and no command line existed that could produce one. The exit is the
`freeze-architecture` subcommand (`kernel.cli.FREEZE_COMMANDS`), whose body is on stdin; the remedy
below is that line, and `test_the_packaging_block_has_an_exit_a_role_can_type` runs it through
every registered shell gate and then executes it.

`packaging` is an optional field of the `arc_companion` schema, whose own `method` is required.
That schema is `strict`, which is also why this reads only `packaging.method` and no second
spelling: nothing can write a `packaging_method:` variant, so tolerating one would be a branch no
producer can reach.

Only fires on `git push`/`git merge`.
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
import _root  # noqa: E402

HOOK = "gate_packaging_decision"
ARCHITECTURE = "ARC"
# Unresolved means absent or still the template's placeholder — the V1 definition, kept verbatim.
# Widening it to a list of synonyms ("tbd", "?", ...) would be guessing at what a human meant;
# an odd-looking but deliberate value is a decision, and this gate is about decisions being made.
PLACEHOLDER = "todo"


def packaging_method(item):
    """The `packaging.method` an architecture item states, '' when it states none.

    Exactly the shape `kernel/schemas/arc_companion.yaml` permits — see the module docstring for
    why there is no second spelling. The isinstance guards are for a file that reached the
    directory some other way, not for a second contract.
    """
    if not isinstance(item, dict):
        return ""
    packaging = item.get("packaging")
    if not isinstance(packaging, dict):
        return ""
    return str(packaging.get("method") or "").strip()


def resolved_packaging(state):
    """(method, seen) — the first resolved packaging method found, and how many architecture items
    were looked at.

    `seen` is not decoration: it is what separates "this project has no architecture item at all"
    from "it has several and none of them decides" in the block message, and those are two
    different conversations with the architect.

    An item is `<ID>.yaml` written by the kernel — the same definition `ProjectState.read_item`
    uses, which is why the read goes through that PUBLIC entry point rather than the private YAML
    helper next to it. Everything else in the directory (the `.drawio.svg` diagrams) is the
    picture, not the decision. Deliberately WITHOUT the kernel lock: items are written temp-file +
    `os.replace`, so every read sees a whole file, and a second lock acquisition on the same
    PreToolUse — `gate_memory_complete` already takes one — buys nothing but latency and a
    lock-timeout failure mode on a merge.
    """
    lock = _kernel.kernel_module("lock")
    directory = lock.ext_path(state.active_dir(ARCHITECTURE))
    seen = 0
    if not os.path.isdir(directory):
        return None, 0
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".yaml"):
            continue
        seen += 1
        try:
            item = state.read_item(os.path.splitext(name)[0])
        except Exception:  # noqa: BLE001 — guard_yaml_valid owns broken YAML; it is not a method
            continue
        method = packaging_method(item)
        if method and method.lower() != PLACEHOLDER:
            return method, seen
    return None, seen


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
    if not _root.has_root_item(root):
        sys.exit(0)  # still being set up; see gate_memory_complete for why that is not gated

    method, seen = resolved_packaging(_kernel.open_state(root))
    if method:
        sys.exit(0)
    _kernel.block(
        HOOK,
        "the packaging/deployment decision is unmade (%s). HOW the software is built and shipped "
        "must be a CONSCIOUS choice — even 'none / library' is valid, but it has to be stated. "
        "This is the deterministic guard against a critical packaging tool (e.g. Docker) being "
        "silently forgotten."
        % ("no active architecture item states one" if seen else
           "this project has no architecture item yet"),
        remedy="have the architect stage the architecture diagram under "
               "project_memory/staging/<ROOT-ID>/<ARC-ID>.drawio.svg, then freeze it through the "
               "entry point with the decision attached — `python scripts/harness.py "
               "freeze-architecture`, run from the project root, with the body on stdin: "
               "{\"staging_key\": \"<ROOT-ID>\", \"arc_id\": \"ARC-0001\", \"title\": \"…\", "
               "\"scope\": \"…\", \"derives_from\": [\"<ROOT-ID>\"], \"packaging\": {\"method\": "
               "\"<docker|static-binary|none (library)|…>\"}}. Add a Decision item recording why, "
               "then merge again.")


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
