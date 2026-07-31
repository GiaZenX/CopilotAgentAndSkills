#!/usr/bin/env python3
"""
Notification(agent_completed|agent_needs_input) + SubagentStop() — deterministic audit log for
agent lifecycle events.

The delegation rule (spawn `run_in_background: false`, or deliberately parallelize and await ALL
completions) was prompt-level only; a real run spawned 37/37 specialists background-by-default with
zero accounting. This hook appends lifecycle events to project_memory/.audit/hook_events.jsonl so
spawn accounting is auditable (retro.py) instead of trusted. Two routes, because a real session
showed the Notification route alone delivering NOTHING (0 of 15 completions — the platform injected
task results as messages instead): (a) Notification with `notification_type: agent_completed |
agent_needs_input` (kept for environments that fire it), (b) SubagentStop, which fires whenever a
subagent finishes. Spawn-side accounting lives in guard_agent_spawn (event: spawn). Never blocks,
never prints — exit 0 always.
"""
import json
import os
import sys
import time


# NO BYTECODE FROM A HOOK RUN, for the reason `_gate.py` states at length: this file lives in
# the hashed enforcement bundle and imports its neighbours out of it, so caching them would
# change the bundle by being run — `hooks_trust_required` at the next session, blamed on
# anything but the hook that caused it. The kits register this hook as `python -B`, so in
# production the flag is redundant; it is here because a hook is also started directly — by the
# test suite, by a person diagnosing one — and the measurement must not depend on how it was
# started. `_gate.py` carries the same line for the gates it launches; this one is not launched.
sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _compat
try:
    from _root import find_repo_root
except Exception:
    def find_repo_root(start=None):
        return os.environ.get("CLAUDE_PROJECT_DIR") or start or os.getcwd()
try:
    import _compat  # noqa: F401 — UTF-8 stream pinning (import side effect)
except Exception:
    pass


def main():
    # BOUNDED read (spec II.4). A raw `json.load(sys.stdin)` will happily buffer a
    # payload of any size, and an oversized one is the shape that turns a hook into
    # a memory event rather than a decision. `_compat.load` caps it at STDIN_LIMIT
    # and returns the overflow sentinel here, because a comfort hook must not refuse a tool call.
    data = _compat.load(tolerate_overflow=True)
    hev = str(data.get("hook_event_name") or "")
    if hev in ("SubagentStart", "SubagentStop"):
        event = "subagent_start" if hev == "SubagentStart" else "subagent_stop"
        reason = str(data.get("agent_type") or data.get("agent_name")
                     or data.get("agent_id") or "")[:300]
    else:
        event = str(data.get("notification_type") or "")
        if event not in ("agent_completed", "agent_needs_input"):
            sys.exit(0)
        reason = str(data.get("message") or "")[:300]
    try:
        root = find_repo_root(data.get("cwd"))
        if not os.path.isdir(os.path.join(root, "project_memory")):
            sys.exit(0)  # no project yet -> nothing to log
        d = os.path.join(root, "project_memory", ".audit")
        os.makedirs(d, exist_ok=True)
        line = json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "hook": "notify_agent_events",
            "event": event,
            "reason": reason,
        }, ensure_ascii=False)
        with open(os.path.join(d, "hook_events.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass  # best-effort logging must never break a session
    sys.exit(0)


if __name__ == "__main__":
    main()
