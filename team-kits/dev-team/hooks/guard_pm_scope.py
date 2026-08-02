#!/usr/bin/env python3
"""
PreToolUse(Edit|Write|MultiEdit|NotebookEdit) — keep the PM out of production code.

settings.json tool-hooks fire for the PM AND for every subagent (verified in a real run + the
Claude Code docs), so to block ONLY the PM we skip when `agent_id` is present (set only inside a
subagent call). A real run had the PM make ~60 self-edits instead of delegating; code goes to the
specialist subagents and QA gates it. (Bash writes bypass Edit/Write hooks — this is a 95% guard;
the QA gate is the hard backstop.)

WHAT COUNTS AS PRODUCTION CODE is a property of the FILE, not a directory somebody thought of.
This guard used to decide on two lists — a set of top-level directories (`BLOCK_TOP`) plus root
files carrying a code extension — and measured as real hook processes on 2026-07-31 that meant
`pay.py` and `src/index.html` were refused while `services/pay.py`, `modules/pay.py`,
`core/pay.go`, `scripts/deploy.py`, `deep/nested/dir/util.ts` and `Ui/Widget.vue` all passed. The
last of those is the list's second failure mode: the FS is case-insensitive on Windows and macOS,
so `Ui` and `ui` are one directory and only one of them was in the list. Every ordinary project
layout that does not happen to be named `src` was therefore unguarded, and `gate_write_scope` does
not cover the gap either — without an `agent_id` it never resolves a task, so it checks the PM
against nothing but the state directory.

The rule now: outside the PM's OWN areas, a file written in a programming language is production
code, wherever it sits. `ALLOW_TOP` says where the PM works; `CODE_EXT` says what a programming
language looks like; everything else follows. `BLOCK_TOP` survives with a narrower job — those
areas belong to the specialists whether or not the file is code (`src/fixtures.json`,
`tests/data.csv`) — so it can only over-block now, never let code through.

THE FALSE-ALARM DIRECTION IS DELIBERATE, and it is the opposite of the line this docstring used to
end with ("Uncertainty -> exit 0"). That principle is about UNCERTAINTY, and a `.go` file is not
uncertain. The cost of a false alarm is one delegation, or one sentence in a report; the cost of a
false pass is the incident this guard exists for — a real run had the PM make ~60 self-edits
instead of delegating. What the widening must not do is lame the role, so it is measured from both
sides: `test_guard_pm_scope_blocks_code_by_language_not_by_directory` runs the code battery, and
`test_guard_pm_scope_leaves_ordinary_pm_upkeep_alone` runs fifteen ordinary PM writes — docs,
plans, `project_memory/staging/`, root config and `.claude/agents/**` — and requires rc 0 for all
of them.

Allowed for the PM: project_memory/**, .claude/** (it rewrites specialist model frontmatter),
plans/**, docs/** and root config/markdown. Blocked: src/**, tests/**, frontend/** and other
code areas, plus every file in a programming language outside the allowed areas. A path this hook
cannot resolve at all -> exit 0.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _root import find_repo_root
import _audit
import _compat

# The PM's own areas. Compared WITHOUT case folding, unlike `BLOCK_TOP` below, and the asymmetry
# is the fail-closed direction on both sides: folding a BLOCK list catches `Src` on the
# case-insensitive filesystems Windows and macOS ship (one directory, two spellings), while folding
# an ALLOW list would WIDEN it on Linux, where `Docs` really is a different directory.
ALLOW_TOP = {"project_memory", ".claude", "plans", "docs"}
# Areas that are wholly the specialists', code or not (`src/fixtures.json`, `tests/data.csv`).
# Since `CODE_EXT` below now backstops every directory, this list can only over-block.
BLOCK_TOP = {"src", "tests", "test", "frontend", "backend", "lib", "server",
             "app", "packages", "cmd", "internal", "api", "ui", "web"}
CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".c",
            ".cpp", ".h", ".hpp", ".rb", ".php", ".cs", ".kt", ".swift", ".vue", ".svelte"}


def block(rel):
    _audit.record("guard_pm_scope", rel)
    _compat.stop(
        "[team-kit guard] PM blocked from writing '%s'.\n"
        "You are the Project Manager — you do NOT write production code, and that is any file in "
        "a programming language outside your own areas, at any depth (so `services/pay.py` and "
        "`core/pay.go` count, not only `src/**`). Delegate this to the matching specialist "
        "subagent; QA gates it. "
        "You may write ./.claude/**, docs/ and plans/. CANONICAL STATE — items, tasks, "
        "approvals — goes through the KERNEL, i.e. `python scripts/harness.py <command>` run "
        "from the project root, never through a direct write: `gate_write_scope` refuses those. "
        "`python scripts/harness.py --help` lists the surface that exists. The approval flow is "
        "two halves: `request-approval <kind> <ITEM-ID>` prints the kernel-generated question "
        "-- relay it verbatim -- and the USER mints it by answering. No command mints. This "
        "message used to "
        "advertise `project_memory/*.yaml` as an open door, which sent the lead straight into "
        "another gate's refusal.\n" % rel,
        "PreToolUse")


def check(path, root):
    try:
        rel = os.path.relpath(path, root)
    except Exception:
        return
    # A LEADING `./` IS A PREFIX, NOT A CHARACTER SET. `lstrip("./")` strips every leading `.` and
    # `/`, so `.claude/hooks/x.py` arrived here as `claude/hooks/x.py` -- `.claude` could never
    # match `ALLOW_TOP`, and once the rule above started deciding on the extension that turned into
    # a REFUSAL of the one directory the message two functions down promises the lead may write
    # ("it rewrites specialist model frontmatter"). The same slip cost `gate_write_scope` a round
    # (`.env` read as `env`), which is why the fix is the prefix and not another special case.
    rel = rel.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    if rel.startswith("../"):
        return  # outside the repo -> not our business
    segs = [s for s in rel.split("/") if s]
    if not segs:
        return
    top = segs[0]

    if top in ALLOW_TOP:
        return
    if top.lower() in BLOCK_TOP:
        block(rel)
    # ...and OUTSIDE those areas, what makes a file production code is its LANGUAGE, at any depth:
    # `services/pay.py`, `core/pay.go` and `deep/nested/dir/util.ts` are the same thing `app.py` at
    # the root is, and a directory list can never be finished.
    if os.path.splitext(segs[-1])[1].lower() in CODE_EXT:
        block(rel)


def main():
    data = _compat.load()
    if data.get("agent_id"):
        sys.exit(0)  # settings.json hooks also fire for subagents; only gate the PM (main agent)
    if data.get("tool_name") not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        sys.exit(0)
    root = find_repo_root(data.get("cwd"))
    # iterate EVERY touched file (a Codex apply_patch is one call with many files) — the first
    # blocked path exits 2
    for path in _compat.file_paths(data):
        check(path, root)
    sys.exit(0)


if __name__ == "__main__":
    main()
