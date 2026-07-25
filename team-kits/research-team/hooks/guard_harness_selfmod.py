#!/usr/bin/env python3
"""
PreToolUse(Edit|Write) — the enforcement layer must not be editable by the agents it enforces.

A real PM silently rewrote the kit settings via Bash to unblock its own spawns; the answer was a
prose rule (§2.10) — this guard is its mechanical backstop, and it applies to EVERY agent (main
AND subagents). Blocked via Edit/Write: `.claude/hooks/**`, `.claude/skills/**`,
`.claude/settings.json`, `.claude/settings.local.json` (hook-affecting overrides land there too —
security-review finding), `.claude/kit_version`, the provider ownership manifests, and the
constitution itself (root `AGENTS.md` + the `CLAUDE.md` import shim — self-rewritten instructions
are the documented compromise pattern).
    Provider control planes (`.codex/**`, `.agents/skills/**`, `.github/hooks/**`,
    `.github/agents/**`) and scaffold backups are protected too.
Paths compare case-INsensitively (Windows FS is;
`.CLAUDE/hooks/x` must not slip through). Still allowed: `.claude/agents/*.md` (the
documented model:/effort: resync), `.claude/agent-memory/**` (the memory feature writes there).
Bash writes bypass Edit/Write hooks — tripwire level, like guard_pm_scope; harness changes belong
in the KIT (via a kit update), never patched live in a project. Uncertainty -> exit 0.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _root import find_repo_root
import _audit
import _compat


# `kernel/` is the V2 state kernel the scaffold installs beside the hooks. Every integrity
# gate imports it, so an agent that could Write it would not need to touch a single gate:
# rewriting `report.validate_state` to return `[]` clears every block at once.
BLOCKED = ("hooks/", "kernel/", "skills/", "backups/")
BLOCKED_FILES = ("settings.json", "settings.local.json", "kit_version",
                 "provider_artifacts.json", "team_kit_roles.txt",
                 # gate_pipeline's green-tree cache: hand-writing it would skip the merge gate
                 ".gate_pipeline_green",
                 # V2 runtime state (spec II.8) — it also carries the BOOTSTRAP marker, and
                 # spec II.4 insists bootstrap is "kein Config-Flag (der Lead könnte sein
                 # eigenes Gate umgehen)". Writable by an agent, it would be exactly that flag.
                 "kit_state.json",
                 # the office ledger gate's early-warning cache (spec II.9). It is NOT what
                 # decides the block -- that is re-validated live, precisely because a decision
                 # taken from a writable note is a decision the guarded party can make. It is
                 # still off limits: a forged "everything is fine" is a lie the next reader
                 # believes, and the warning is the only thing that reaches the agent promptly.
                 "ledger_state.json")
BLOCKED_PROVIDER_PREFIXES = (".codex/", ".agents/skills/", ".github/hooks/", ".github/agents/")
# Enforcement code that does NOT live under .claude/. `scripts/ledger_add.py` is the office
# ledger's validator: `gate_ledger_valid` refuses commit/push/merge/reports/dispatch on its
# verdict, so an agent that could Write it could replace it with `sys.exit(0)` and clear its own
# block. The gate's docstring claimed this guard covered it while the path was nowhere in this
# file — a stated protection that did not exist, which is worse than an open hole. Harmless in
# kits without the file.
BLOCKED_REPO_PATHS = ("scripts/ledger_add.py",)


def block(rel):
    _audit.record("guard_harness_selfmod", rel)
    sys.stderr.write(
        "[team-kit guard] '%s' is part of the ENFORCEMENT LAYER — no agent edits it in a "
        "project, ever (a real PM silently rewrote kit settings to unblock itself). A guard "
        "that seems wrong is an infrastructure defect: report it to the user; the generic fix "
        "belongs in the KIT and arrives via a kit update. Generated .codex/** and "
        ".agents/skills/** are updated only by the scaffold. Allowed here: "
        ".claude/agents/*.md (model:/effort: resync) and .claude/agent-memory/**.\n" % rel
    )
    sys.exit(2)


def check(path, root):
    try:
        rel = os.path.relpath(path, root).replace("\\", "/")
    except ValueError:
        return
    rel_l = rel.lower()  # case-insensitive: the FS on Windows is, so the comparison must be too
    # the constitution itself (root AGENTS.md + the CLAUDE.md import shim) is enforcement
    # knowledge: an agent rewriting its own instructions is the documented compromise pattern
    # (instructions/memory rewritten outside any diff) — constitution changes arrive via kit
    # updates (scaffold), never via agent edits.
    if rel_l in ("agents.md", "claude.md"):
        block(rel)
    if rel_l in BLOCKED_REPO_PATHS:
        block(rel)
    if any(rel_l.startswith(prefix) for prefix in BLOCKED_PROVIDER_PREFIXES):
        block(rel)
    if not rel_l.startswith(".claude/"):
        return
    sub = rel_l[len(".claude/"):]
    if any(sub.startswith(b) for b in BLOCKED) or sub in BLOCKED_FILES:
        block(rel)


def main():
    data = _compat.load()
    # Kept in step with the REGISTRATION (matcher `Edit|Write|MultiEdit|NotebookEdit`). The two
    # disagreed: this list handled MultiEdit while the matcher did not, and Claude Code compares
    # matchers per group — so the tool that edits several files at once never reached the guard
    # over `.claude/hooks` and `.claude/kernel`. Handling a tool you are not registered for is
    # protection that exists only in the source.
    if data.get("tool_name") not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        sys.exit(0)
    root = find_repo_root(data.get("cwd"))
    for path in _compat.file_paths(data):
        check(path, root)
    sys.exit(0)


if __name__ == "__main__":
    main()
