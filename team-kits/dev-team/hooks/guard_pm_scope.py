#!/usr/bin/env python3
"""
PreToolUse(Edit|Write) — keep the PM out of production code.

settings.json tool-hooks fire for the PM AND for every subagent (verified in a real run + the
Claude Code docs), so to block ONLY the PM we skip when `agent_id` is present (set only inside a
subagent call). A real run had the PM make ~60 self-edits instead of delegating; code goes to the
specialist subagents and QA gates it. (Bash writes bypass Edit/Write hooks — this is a 95% guard;
the QA gate is the hard backstop.)

Allowed for the PM: project_memory/**, .claude/** (it rewrites specialist model frontmatter),
plans/**, docs/** and root config/markdown. Blocked: src/**, tests/**, frontend/** and other
code areas, plus root-level code files. Uncertainty -> exit 0 (never block legitimate upkeep).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _root import find_repo_root
import _audit
import _compat

ALLOW_TOP = {"project_memory", ".claude", "plans", "docs"}
BLOCK_TOP = {"src", "tests", "test", "frontend", "backend", "lib", "server",
             "app", "packages", "cmd", "internal", "api", "ui", "web"}
CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".c",
            ".cpp", ".h", ".hpp", ".rb", ".php", ".cs", ".kt", ".swift", ".vue", ".svelte"}


def block(rel):
    _audit.record("guard_pm_scope", rel)
    sys.stderr.write(
        "[team-kit guard] PM blocked from writing '%s'.\n"
        "You are the Project Manager — you do NOT write production code (src/**, tests/**, "
        "frontend/**). Delegate this to the matching specialist subagent; QA gates it. "
        "You may write ./.claude/**, docs/ and plans/. CANONICAL STATE — items, tasks, "
        "approvals — goes through the KERNEL (`harness capture/transition/approve`), never "
        "through a direct write: `gate_write_scope` refuses those. This message used to "
        "advertise `project_memory/*.yaml` as an open door, which sent the lead straight into "
        "another gate's refusal.\n" % rel
    )
    sys.exit(2)


def check(path, root):
    try:
        rel = os.path.relpath(path, root)
    except Exception:
        return
    rel = rel.replace("\\", "/").lstrip("./")
    if rel.startswith("../"):
        return  # outside the repo -> not our business
    segs = [s for s in rel.split("/") if s]
    if not segs:
        return
    top = segs[0]

    if top in ALLOW_TOP:
        return
    if top in BLOCK_TOP:
        block(rel)
    # root-level code file (e.g. app.py, server.py, main.ts)
    if len(segs) == 1 and os.path.splitext(top)[1].lower() in CODE_EXT:
        block(rel)


def main():
    data = _compat.load()
    if data.get("agent_id"):
        sys.exit(0)  # settings.json hooks also fire for subagents; only gate the PM (main agent)
    if data.get("tool_name") not in ("Edit", "Write"):
        sys.exit(0)
    root = find_repo_root(data.get("cwd"))
    # iterate EVERY touched file (a Codex apply_patch is one call with many files) — the first
    # blocked path exits 2
    for path in _compat.file_paths(data):
        check(path, root)
    sys.exit(0)


if __name__ == "__main__":
    main()
