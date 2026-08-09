#!/usr/bin/env python3
"""
proc_hash.py — show whether a PROC's stamped `approved_hash` still matches its own content.

    python scripts/proc_hash.py            # every active PROC
    python scripts/proc_hash.py PROC-0001  # one of them

Exit 0 = every PROC examined is APPROVED/ACTIVE with a stamp that matches, or is still DRAFT and
owes none. Exit 1 = at least one stamp is missing or stale. Exit 2 = the command could not look.

THIS SCRIPT NO LONGER WRITES ANYTHING, and the deleted half is the point. V1 shipped
`--update`, which recomputed the hash and wrote it back into `process_definitions.yaml` -- i.e. a
command any role could run to make the tamper check pass again, with a docstring asking it not to
be used that way. That is the permission the check exists to withhold. In V2 the stamp is produced
where a user has just said yes to this exact content: `approvals.mint` writes it (see
`approved_content_hash`), so an approved PROC is stamped by the approval and by nothing else. If
the content moved, the remedy is the user's approval of the new content, not a fresh hash.

THE HASH IS THE KERNEL'S, not a second definition. V1 hashed `yaml.safe_dump(steps)`, which spec
II.2 rejects outright (PyYAML's output is version-dependent, un-normalized and carries no schema
version); `gate_proc_approved` carried a copy of that function with a comment demanding the two
stay identical. Both are gone: this reads `kernel.approvals.approved_content_hash`, the same call
the gate and the state validator make.
"""
import os
import sys

# BEFORE any kernel import: `.claude/hooks` and `.claude/kernel` are the tree `hook_bundle_hash`
# measures with nothing excluded, so a cached import would drop `.pyc` into the enforcement bundle
# and the next session would report `hooks_trust_required` because somebody checked a hash.
sys.dont_write_bytecode = True

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(REPO_ROOT, ".claude", "hooks")


def _fail(message, remedy):
    sys.stderr.write("[proc_hash] %s\nRemedy: %s\n" % (message, remedy))
    return 2


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not os.path.isfile(os.path.join(BRIDGE, "_kernel.py")):
        return _fail("this project has no enforcement layer at %s, so there is no kernel to ask "
                     "for the approval hash." % BRIDGE,
                     "re-run the team scaffold for this repo.")
    sys.path.insert(0, BRIDGE)
    try:
        import _kernel  # type: ignore[import-not-found]
    except BaseException as exc:  # noqa: BLE001 — a broken bridge names itself, never tracebacks
        return _fail("the hook helpers next to the kernel could not be loaded (%r)." % (exc,),
                     "a partial checkout or a half-finished kit update is the usual cause; "
                     "re-run the team scaffold for this repo.")
    # importing the bridge ARMS the gate excepthook; this is a command a person typed, so an
    # ordinary error must stay an ordinary error with a flushed stdout (harness.py does the same)
    _kernel.disarm()
    try:
        state = _kernel.open_state(REPO_ROOT)
        approvals = _kernel.kernel_module("approvals", REPO_ROOT)
    except Exception as exc:
        return _fail("the state kernel could not be reached (%s: %s)." % (type(exc).__name__, exc),
                     "run `python scripts/harness.py doctor`; it names what is missing.")

    directory = state.active_dir("PROC")
    names = sorted(n for n in os.listdir(directory) if n.endswith(".yaml")) \
        if os.path.isdir(directory) else []
    wanted = set(argv)
    stale = 0
    seen = 0
    for name in names:
        proc_id = name[:-5]
        if wanted and proc_id not in wanted:
            continue
        seen += 1
        try:
            item = state.read_item(proc_id)
        except Exception as exc:
            print("%s: unreadable (%s)" % (proc_id, exc))
            stale += 1
            continue
        status = item.get("status")
        computed = approvals.approved_content_hash("PROC", item)
        recorded = item.get(approvals.APPROVED_CONTENT_HASH_FIELD)
        if status not in approvals.approved_statuses("PROC"):
            print("%s: %s — owes no approval stamp yet" % (proc_id, status))
            continue
        print("%s: %s\n  computed: %s\n  recorded: %s"
              % (proc_id, status, computed, recorded or "(none)"))
        if computed != recorded:
            stale += 1
    missing = sorted(wanted - {n[:-5] for n in names})
    if missing:
        return _fail("no active PROC named %s." % ", ".join(missing),
                     "check the id in the generated index; archived procedures live in the "
                     "archive.")
    if not seen:
        print("no active PROC items")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
