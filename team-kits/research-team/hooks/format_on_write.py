#!/usr/bin/env python3
"""
PostToolUse(Edit|Write) — auto-format the file a specialist just wrote (shift-left).

Best-effort: runs the matching formatter ONLY if it is installed, so unformatted code
never reaches the validation gate. Never blocks; any problem -> exit 0. The gate
(validity_criteria.yaml) stays the hard enforcement; this just keeps code clean in transit.

Skips project_memory/, .claude/, plans/ and other non-source paths so the PM's
hand-curated YAML state is never reformatted.

Lives in subagent frontmatter (the code-writers) to scope it to the roles that write CODE.
NOTE (verified): settings.json tool-hooks fire for the main agent AND all subagents —
frontmatter placement is for per-role scoping, NOT because settings hooks would skip subagents.
"""
import sys
import os
import shutil
import subprocess

# extension -> ordered candidate formatter argv (first available wins); {f} = file path.
FORMATTERS = {
    ".py": [["ruff", "format", "{f}"], ["black", "{f}"]],
    ".js": [["prettier", "--write", "{f}"]],
    ".jsx": [["prettier", "--write", "{f}"]],
    ".ts": [["prettier", "--write", "{f}"]],
    ".tsx": [["prettier", "--write", "{f}"]],
    ".mjs": [["prettier", "--write", "{f}"]],
    ".css": [["prettier", "--write", "{f}"]],
    ".scss": [["prettier", "--write", "{f}"]],
    ".html": [["prettier", "--write", "{f}"]],
    ".json": [["prettier", "--write", "{f}"]],
    ".go": [["gofmt", "-w", "{f}"]],
    ".rs": [["rustfmt", "{f}"]],
}
SKIP_DIRS = ("project_memory", ".claude", "plans", "node_modules", ".git", "dist", "build")


# NO BYTECODE FROM A HOOK RUN, for the reason `_gate.py` states at length: this file lives in
# the hashed enforcement bundle and imports its neighbours out of it, so caching them would
# change the bundle by being run — `hooks_trust_required` at the next session, blamed on
# anything but the hook that caused it. The kits register this hook as `python -B`, so in
# production the flag is redundant; it is here because a hook is also started directly — by the
# test suite, by a person diagnosing one — and the measurement must not depend on how it was
# started. `_gate.py` carries the same line for the gates it launches; this one is not launched.
sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _root import find_repo_root
import _compat


def fmt(path, cwd):
    if not path or not os.path.isfile(path):
        return
    try:
        rel = os.path.relpath(path, cwd).replace("\\", "/")
    except Exception:
        rel = path
    if any(part in SKIP_DIRS for part in rel.split("/")):
        return

    cands = FORMATTERS.get(os.path.splitext(path)[1].lower())
    if not cands:
        return

    for cmd in cands:
        exe = cmd[0]
        runner = None
        if shutil.which(exe):
            runner = [c.replace("{f}", path) for c in cmd]
        elif exe == "prettier" and shutil.which("npx"):
            runner = ["npx", "--no-install", "prettier", "--write", path]
        if runner:
            try:
                subprocess.run(runner, cwd=cwd, capture_output=True, timeout=60)
            except Exception:
                pass
            break  # a formatter for this extension was found; stop


def main():
    # comfort hook (spec II.4: formatting may fail open), so an oversized payload is skipped
    # rather than blocked — the integrity gates are the ones that must refuse what they cannot
    # inspect, and they do so by default
    data = _compat.load(tolerate_overflow=True)
    allowed_roles = {role for role in os.environ.get("TEAM_KIT_AGENT_TYPES", "").split(",")
                     if role}
    if allowed_roles and str(data.get("agent_type") or "") not in allowed_roles:
        sys.exit(0)
    if data.get("tool_name") not in ("Edit", "Write"):
        sys.exit(0)
    cwd = find_repo_root(data.get("cwd"))
    for path in _compat.file_paths(data):
        fmt(path, cwd)
    sys.exit(0)


if __name__ == "__main__":
    main()
