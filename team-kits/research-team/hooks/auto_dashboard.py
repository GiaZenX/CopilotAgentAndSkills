#!/usr/bin/env python3
"""
Stop hook — keeps the dashboard in sync with zero agent effort.

When the agent finishes a turn, if any project_memory/*.yaml is newer than
progress.dashboard.html (or the html is missing), regenerate it by running
generate_dashboard.py. Never blocks; failures are swallowed (exit 0 always).
"""
import sys
import os
import glob
import json


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _compat
from _root import find_repo_root
from _compat import run_captured


def main():
    cwd = os.getcwd()
    data = {}
    # BOUNDED read (spec II.4): a raw `json.load(sys.stdin)` buffers a payload of any
    # size. `tolerate_overflow=True` because this hook only INFORMS -- refusing a tool
    # call because a dashboard could not be rendered would be absurd.
    data = _compat.load(tolerate_overflow=True)
    try:
        cwd = find_repo_root(data.get("cwd"))
    except Exception:
        pass

    # kit-update follow-through (V1, once per session): SessionStart-only nags proved to fade in a
    # 7-hour session — remind again at the FIRST stop, so the backlog cannot be silently outlived.
    exit_code = 0
    try:
        pend = [s for s in ("repo", "memory")
                if os.path.isfile(os.path.join(cwd, ".claude", "kit_update_pending." + s))]
        if pend:
            state_p = os.path.join(cwd, ".claude", "kit_update_pending.state")
            sid = str(data.get("session_id") or "")
            st = {}
            try:
                with open(state_p, encoding="utf-8") as fh:
                    st = json.load(fh)
            except Exception:
                pass
            if sid and st.get("stop_nag_sid") != sid:
                st["stop_nag_sid"] = sid
                try:
                    with open(state_p, "w", encoding="utf-8") as fh:
                        json.dump(st, fh)
                except Exception:
                    pass
                sys.stderr.write(
                    "[kit-update] .claude/kit_update_pending.%s still unresolved — merge each entry via "
                    "the owning role or log a conscious skip in progress.yaml log:, then DELETE the "
                    "file(s). Do not end the session with this untouched.\n" % "/".join(pend))
                exit_code = 1  # non-blocking error -> the reminder becomes visible
    except Exception:
        pass

    pm = os.path.join(cwd, "project_memory")
    gen = os.path.join(pm, "generate_dashboard.py")
    if not os.path.isfile(gen):
        sys.exit(exit_code)

    yamls = glob.glob(os.path.join(pm, "*.yaml"))
    if not yamls:
        sys.exit(exit_code)
    newest = max(os.path.getmtime(y) for y in yamls)

    html = os.path.join(pm, "progress.dashboard.html")
    if os.path.isfile(html) and os.path.getmtime(html) >= newest:
        sys.exit(exit_code)  # already up to date

    try:
        p = run_captured([sys.executable, gen], cwd=pm, timeout=60)
        if p.returncode != 0:
            # surface a generator FATAL (e.g. invalid project_memory YAML) instead of swallowing it —
            # exit 1 is a NON-blocking hook error (stop proceeds; the message becomes visible).
            tail = ((p.stderr or "") + (p.stdout or "")).strip()[-400:]
            sys.stderr.write("[auto_dashboard] dashboard NOT regenerated:\n%s\n" % tail)
            sys.exit(1)
    except Exception:
        pass
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
