#!/usr/bin/env python3
"""
Global handover guard — BUG-0016, DEC-0032 (soft variant, user-approved 2026-08-10).

WHY THIS IS GLOBAL AND NOT A KIT HOOK. After the entry gate installs a kit and asks the user to
restart, the freshly installed PROJECT hooks are inactive in that same session: Claude Code's
settings watcher covers only directories that existed when the session started, and Auto-Init
creates `.claude/` fresh (measured, staging/BUG-0016/messung-2026-08-10.md). So the only hook that
can act inside that window is one that was already registered before the session began — a hook in
`~/.claude/settings.json`. This file is that hook.

MARKER-GATED, so it is INVISIBLE outside a handover. The scaffold writes `.claude/HANDOVER_PENDING`
into the project as its last act; a project-owned `SessionStart(startup)` hook deletes it on the
next REAL process start (measured: the startup matcher fires only on source=startup, not on
resume/reconnect, so the marker survives a reattach and clears on a genuine restart). With no marker
in the cwd this hook exits 0 immediately — no classification, no cost beyond one `os.path.exists`.

SOFT VARIANT, what it refuses and what it never touches (DEC-0032):
  * ALLOWED even with the marker: writes to the PLAN ARTEFACTS the entry gate hand-writes, because
    the user may keep refining the plan up to the restart (global CLAUDE.md Auto-Init step 3):
    `project_memory/product/masterplan.md`, `project_memory/project_config.yaml`, and the root item
    `project_memory/product/active/PR-0001*`.
  * REFUSED with the marker: product-code writes/edits (any file write that is not a plan artefact),
    specialist SPAWNS (Task/Agent), and DERIVATION through the work engine on the shell
    (`scripts/harness.py` / `kernel.cli` for anything other than a read like `doctor`/`--help`):
    creating items, dispatching, running the lifecycle. These are the post-handover PM's acts. A
    command line is split at the routine chaining operators `&&`, `||`, `;` and `|` and EACH segment
    is judged on its own, so a leading `cd x && python harness.py capture` or `ls | python -m
    kernel.cli create-task` is refused (measured bypasses, TSK-0031). A read in one segment never
    excuses derivation in another.
  * NEVER touched: reading, asking, answering, explaining. This hook refuses individual TOOL calls
    only; it never ends the session (AskUserQuestion, Read, Grep, ... are not in scope here).

FAIL-OPEN BY DESIGN, and deliberately so — this is a belt on a WELL-INTENTIONED entry agent that
merely keeps working, not an adversarial sandbox (the true boundary is the restart). So the routine
chaining forms above are the real vector and ARE built; the deliberately obfuscating ones are the
named residue, not a promise. Anything it cannot classify (no marker, a malformed payload, an
unresolved path) exits 0. NAMED, unclosed gaps this soft variant does NOT cover, both measured:
  * product code written through a raw shell redirect (`echo x > src/foo.py`) — the same class of
    shell write-verb hole the far larger `gate_write_scope` also leaves open. The measured
    product-code vector is the Write/Edit tool, which IS covered.
  * a work-engine call hidden inside a WRAPPED command whose verb is a shell (`sh -c '...'`,
    `bash -lc '...'`) or an ENCODED/obfuscated form — the segment splitter reads the outer verb
    (`sh`/`bash`), not the string it would execute. Carried as a measured route with its chain in
    docs/POST_V2_WISHLIST.md (L39); NOT closed here (that is the shell-parser rabbit hole DEC-0029
    warns against — no promised protection without code).
"""
import json
import os
import re
import sys

MARKER = os.path.join(".claude", "HANDOVER_PENDING")

FILE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
SHELL_TOOLS = ("Bash", "PowerShell")
SPAWN_TOOLS = ("Task", "Agent")

# The plan artefacts the entry gate writes by hand (global CLAUDE.md Auto-Init step 3; DEC-0032).
# Exact matches for the two singletons; a prefix for the root item so PR-0001.yaml (and any sidecar
# the entry gate writes beside it) is covered. This is the entry-gate contract's own closed set, not
# an open list of special cases.
_PLAN_FILES = ("project_memory/product/masterplan.md", "project_memory/project_config.yaml")
_PLAN_ROOT_PREFIX = "project_memory/product/active/pr-0001"

# Tokens that make a work-engine invocation a READ rather than derivation. Matched as whole tokens,
# never as substrings: `-h` inside `--header` must not turn a dispatch into an allowed "read".
_ENGINE_READS = frozenset(("doctor", "--help", "-h", "help"))
# Wrapper/assignment tokens to skip when finding the command verb (a small, well-known set; a
# VAR=value assignment is recognised structurally, not listed).
_WRAPPERS = frozenset(("sudo", "env", "command", "exec", "time", "nice"))

# The routine chaining operators an overflowing entry agent actually types. `||` is tried before `|`
# so the two-char operator is not split as two single pipes. This is deliberately NOT a shell parser
# (wrapped/encoded forms are the named residue in the docstring / POST_V2_WISHLIST L39).
_SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\|")


def _norm(text):
    return str(text).replace("\\", "/").lower()


def _allow():
    sys.exit(0)


def _refuse(reason):
    sys.stderr.write(
        "[handover] refused: %s\n"
        "A team kit was just installed and you asked the user to restart the session "
        "(.claude/HANDOVER_PENDING is set). Until that restart, this session only refines the plan "
        "and talks — it does not produce the product or derive further work; the freshly installed "
        "project hooks are not active yet (settings-watcher gap, BUG-0016). Report what is still "
        "needed and let the restarted Project Manager do it. Reading, asking and answering are not "
        "affected; the marker clears itself on the next real restart.\n" % reason)
    sys.exit(2)


def _cwd(data):
    return data.get("cwd") or os.getcwd()


def _marker_present(cwd):
    return os.path.exists(os.path.join(cwd, MARKER))


def _targets(tool_input):
    for key in ("file_path", "notebook_path"):
        value = tool_input.get(key)
        if value:
            yield value


def _rel(path, cwd):
    """The write target relative to the project root, normalised — or None when it will not resolve.

    None fails OPEN (see the module docstring): an unresolvable path is not classified as product
    code, it is simply not judged.
    """
    try:
        absolute = path if os.path.isabs(path) else os.path.join(cwd, path)
        rel = os.path.relpath(os.path.abspath(absolute), os.path.abspath(cwd))
    except (OSError, ValueError):
        return None
    rel = _norm(rel)
    if rel.startswith("../"):
        return None
    return rel


def _is_plan_artifact(rel):
    return rel in _PLAN_FILES or rel.startswith(_PLAN_ROOT_PREFIX)


def _handle_file_write(tool_input, cwd):
    for path in _targets(tool_input):
        rel = _rel(path, cwd)
        if rel is None:
            continue  # unresolvable: not judged (fail-open)
        if not _is_plan_artifact(rel):
            _refuse("'%s' is product code / derived state, not a plan artefact" % rel)


def _verb(tokens):
    """The command verb, skipping VAR=value assignments and a small set of wrappers."""
    for token in tokens:
        bare = token.strip("\"'")
        if "=" in bare and not bare.startswith("-"):
            continue  # VAR=value prefix
        low = os.path.basename(bare).lower()
        if low in _WRAPPERS:
            continue
        return low
    return ""


def _segment_drives_engine(segment):
    """True when this single command segment RUNS the work engine (not just names or reads it)."""
    if "harness.py" not in segment and "kernel.cli" not in segment:
        return False  # does not name the work engine
    tokens = segment.split()
    verb = _verb(tokens)
    # names the engine but does not RUN it (e.g. `cat scripts/harness.py`, `grep x harness.py`):
    # reading is never derivation. Only a python interpreter or the script itself in verb position
    # drives it.
    if not (verb.startswith("python") or verb in ("py", "pythonw", "harness.py")):
        return False
    if any(token.strip("\"'") in _ENGINE_READS for token in tokens):
        return False  # doctor / --help: a read of the engine, not derivation
    return True


def _handle_shell(tool_input):
    command = _norm(tool_input.get("command") or "")
    if not command.strip():
        _allow()
    # Judge EACH chained segment on its own (TSK-0031): a routine `cd x && python harness.py capture`
    # or `cat foo | python harness.py capture` must not slip past because the first word is benign,
    # and a read in one segment must not excuse derivation in another.
    for segment in _SEGMENT_SPLIT.split(command):
        if _segment_drives_engine(segment):
            _refuse("this command drives the work engine (item capture / dispatch / lifecycle)")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — a guard that cannot read its payload must not block a session
        _allow()
    if not isinstance(data, dict):
        _allow()
    if str(data.get("hook_event_name") or "PreToolUse") != "PreToolUse":
        _allow()
    cwd = _cwd(data)
    if not _marker_present(cwd):
        _allow()  # no handover in progress: invisible no-op
    tool = data.get("tool_name")
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        _allow()
    if tool in FILE_TOOLS:
        _handle_file_write(tool_input, cwd)
    elif tool in SPAWN_TOOLS:
        _refuse("spawning a specialist derives work — that is the restarted PM's act")
    elif tool in SHELL_TOOLS:
        _handle_shell(tool_input)
    _allow()


if __name__ == "__main__":
    main()
