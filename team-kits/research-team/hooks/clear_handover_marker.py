#!/usr/bin/env python3
"""
SessionStart() — clear `.claude/HANDOVER_PENDING`, the marker the global handover guard reads.

BUG-0016, DEC-0032. The scaffold writes the marker so the GLOBAL `~/.claude/hooks/handover_guard.py`
refuses product-code writes and further derivation in the entry session — the window in which the
freshly installed project hooks are not yet active (settings-watcher gap). This hook is the marker's
one legitimate remover, and it removes it only on a FORGERY-PROOF signal that the restart actually
happened: `source == "startup"`. A genuine new process start reports source=startup; an IDE
reconnect or terminal reattach reports source=resume — measured in a real SDK session,
staging/BUG-0016/messung-2026-08-10.md. So the marker survives a reattach of the entry session and
clears only when the user has truly restarted into the PM session.

The check is done in the hook body rather than through a `startup` SessionStart MATCHER on purpose:
that matcher has no representation in the Codex provider translation
(`gen_provider_artifacts`), and the in-body check is equivalent, unit-testable without trusting the
provider, and works on both providers. The hook therefore runs on every SessionStart and is a no-op
on resume.

COMFORT HOOK, fail-open (spec II.4): it maintains a project file, it must never refuse a session.
Any error — a marker that cannot be deleted, a payload that will not parse — is swallowed and the
session proceeds.
"""
import os
import sys

# NO BYTECODE FROM A HOOK RUN: this file lives in the hashed enforcement bundle, so caching it would
# change the bundle by being run. The kits register it as `python -B`; the flag here keeps that true
# when it is started directly (by the test suite, by a person diagnosing it).
sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _compat
from _root import find_repo_root

# The path, from the one place the hooks spell it: `gate_dispatch` refuses a spawn on the same
# file, and two hooks acting on one marker under two spellings is how one of them would stop
# meaning anything. Kept as a module constant because this hook's own tests address it by name.
MARKER = _compat.HANDOVER_MARKER


def clear_marker(repo_root, source):
    """Delete the handover marker, but only on a genuine restart. Returns True when it removed one."""
    if source != "startup":
        return False
    path = os.path.join(repo_root, MARKER)
    try:
        os.remove(path)
        return True
    except OSError:
        return False  # absent, or unremovable: nothing to do, and never a reason to block


def main():
    # `tolerate_overflow=True`: this hook only maintains a file, so an oversized payload must not
    # refuse the session (the opposite of the integrity gates, spec II.4).
    data = _compat.load(tolerate_overflow=True)
    try:
        clear_marker(find_repo_root(data.get("cwd")), data.get("source"))
    except BaseException:  # noqa: BLE001 — comfort hook, see the module docstring
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
