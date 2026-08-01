#!/usr/bin/env python3
"""
PreToolUse(Edit|Write|MultiEdit|NotebookEdit) — the enforcement layer must not be editable by the agents it enforces.

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
                 # the tray list the scaffold derives from the kit it installed
                 # (`kernel/trays.py`). `guard_no_adhoc` stands its name rule down inside a
                 # directory named here, so an agent that could write this file could exempt any
                 # directory it liked from that rule — the exemption has to be a fact about the
                 # INSTALLED KIT, and this is what keeps it one.
                 "document_trays.txt",
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
#
# `scripts/harness.py` is the same class: it is the ONE entry point every fail-closed remedy hands
# a blocked role, it is installed kit-owned (the scaffold overwrites it on every run), and it
# imports the kernel — so a rewritten copy holds the whole kernel API, including the operations
# the sanctioned command surface deliberately does not expose. Edit/Write/MultiEdit/NotebookEdit
# are closed here, case-insensitively.
#
# WHAT THIS DOES NOT CLAIM, measured rather than reasoned, and the honest version is NARROWER than
# "an agent could write some other script": a role can replace THIS EXACT FILE from a shell, and
# nothing in the harness notices. Measured 2026-07-29 in a scaffolded project:
#   * `cat > scripts/harness.py <<EOF … EOF` → every registered shell gate ALLOWS (the command line
#     names neither the state directory nor `.claude`, which is what those gates read);
#   * with a stub in place, `kernel.hashing.hook_bundle_hash` is UNCHANGED — the value recorded at
#     scaffold time still equals the live one, which is the whole of what the trust comparison
#     asks — and `report.doctor` gives `installation_errors: []` while `scripts/kit_checks.py`
#     exits 0. Stated as the hash rather than as a `kit_state` name on purpose: which name a
#     project carries depends on whether a SessionStart has run since the scaffold, so the name
#     would be a fact about the fixture and the hash is the fact about the tampering.
# WHY THE HASH DOES NOT MOVE — a derivation, not a count, because the count this comment used to
# carry was wrong. `hook_bundle_hash` measures `<repo>/.claude/<s>` for every `s` in
# `kernel/hashing.BUNDLE_SUBTREES`, today `("hooks", "kernel")`. So an entry of THIS file is INSIDE
# the measurement exactly when the path it blocks lies under `.claude/hooks/` or `.claude/kernel/`,
# and OUTSIDE otherwise — which can be read off each entry below without measuring anything:
# `BLOCKED`'s first two prefixes are inside; its `skills/` and `backups/`, every name in
# `BLOCKED_FILES`, every entry of `BLOCKED_PROVIDER_PREFIXES`, both `BLOCKED_REPO_PATHS` and the
# constitution pair (`AGENTS.md` / `CLAUDE.md`, matched in `check`) are outside.
# The sentence that stood here — "these two paths are the only entries in this whole file that
# [sit outside the bundle]" — was false under both readings: measured 2026-07-31 by tampering with
# one file per entry and recomputing the hash, 18 of the 20 paths this file blocks leave the bundle
# hash untouched, and EIGHT of them are not under `.claude` at all (`AGENTS.md`, `CLAUDE.md`, the
# four provider prefixes and the two `scripts/` paths), which is the narrower reading gone too.
# `test_the_bundle_measures_exactly_the_two_subtrees_this_guard_shares_with_it` re-measures it
# against the running guard rather than against this paragraph.
# MINTING IS PART OF THE EXPOSURE, and the sentence that stood here said the opposite. It read
# "minting is NOT part of the exposure (measured: `approvals.mint` refuses any caller whose
# `__main__` is not `gate_approval.py`)", which describes only the IN-PROCESS refusal. Measured
# 2026-07-31 in a scaffolded project: a replacement `scripts/harness.py` that writes its own
# pending request and then STARTS the real hook as a subprocess with a forged PostToolUse payload
# mints — every shell gate returns 0 on both the write and the run, and the hook answers
# "approval APR-0007 recorded for PR-0004". That is not a new hole; it is the one
# `test_running_the_shipped_hook_by_hand_still_mints` asserts as open under the `approval_provenance`
# known_hole, reached from here. So what a replaced file buys is the kernel's write surface, a
# role's trust in the output it prints, AND a forged user approval.
# So: the TOOL path to the file every remedy points at is closed, the SHELL path to it is open and
# undetected. Closing it needs either a shell rule that knows this path or `BUNDLE_SUBTREES`
# widened to cover it — both decisions for the harness owner, and neither is claimed here.
#
# AND THE FINDING THAT FOLLOWS FROM THE SAME MEASUREMENT, stated because a paragraph that ends at
# `scripts/harness.py` would read as if that were the widest hole here: `.claude/settings.json` is
# shell-writable (the shell rule refuses a write-capable pipeline that NAMES `.claude`, and a
# script that names nothing does not) AND unhashed. That file is the hook WIRING — what decides
# whether any of these guards runs at all — so it is a larger surface than the entry point, not a
# smaller one. Named for the harness owner; nothing in this file closes it.
BLOCKED_REPO_PATHS = ("scripts/ledger_add.py", "scripts/harness.py")


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
