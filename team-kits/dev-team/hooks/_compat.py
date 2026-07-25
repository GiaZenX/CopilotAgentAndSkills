#!/usr/bin/env python3
"""
Shared helper: provider payload adapter — ONE place that normalizes hook payloads.

Claude Code and Codex CLI send similar hook JSON (`tool_name`/`tool_input`/`cwd`/
`hook_event_name`), but their enforcement contracts differ. Claude documents exit 2 + stderr as
blocking. Codex documents exit 2 + stderr for PreToolUse/PostToolUse/UserPromptSubmit/SubagentStop
AND a structured `decision: block` JSON for the post/stop events; stop() below uses the JSON form
there because it carries the reason back to the model (verified 2026-07-14, official docs+source).
The differences this shim absorbs:

  * Codex file edits arrive as tool_name "apply_patch" with the patch envelope in
    tool_input.command (no file_path). load() normalizes that to tool_name "Edit" and extracts
    EVERY touched file from the `*** Add|Update|Delete File:` and `*** Move to:` headers; path guards iterate
    file_paths() so a multi-file patch cannot smuggle a blocked path past a single-path check.
  * Lowercase/alternate tool names from non-Claude payloads are normalized to the Claude names
    every guard filters on (see _TOOL_ALIASES).

Uncertainty -> return the payload unchanged; a guard that cannot parse stays fail-open (exit 0),
same philosophy as every other hook.
"""
import json
import os
import re
import subprocess
import sys

try:
    from _root import find_repo_root
except Exception:  # standalone import (tests) — same fallback _audit uses
    def find_repo_root(start=None):
        return os.environ.get("CLAUDE_PROJECT_DIR") or start or os.getcwd()

# OUTBOUND half of the encoding family (audit): hooks write block messages to stderr, which
# Windows opens cp1252 — "Käufer" reached a UTF-8-reading provider as mojibake while the
# INBOUND side was already pinned. Import-time side effect on purpose: every hook that imports
# _compat (all of them) gets UTF-8 streams without a per-hook call to forget.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass  # non-reconfigurable stream (test harness capture) — best effort


# BOUNDED stdin (spec II.4: "Hooks lesen stdin BEGRENZT"). An unbounded read makes every hook a
# memory amplifier for whatever the provider puts in tool_input (a Write of a huge file, a pasted
# dump). The cap is generous — real payloads carry whole file contents — but finite.
#
# Overflow BLOCKS by default, and that default is the whole design. The first cut of this returned
# a sentinel dict for the caller to notice, which silently disarmed ten shipped guards at once:
# they all dispatch on `tool_name`, the sentinel has none, so every one of them exited 0 = ALLOW —
# a 17 MB Write of `.claude/settings.json` walked straight past guard_harness_selfmod. An
# oversized payload means "this call could not be inspected", and for an integrity gate that must
# never read as "allowed" (spec II.4 fail-closed). So the SAFE behaviour is what you get by
# forgetting; comfort hooks (formatting, dashboards, notifications) opt out explicitly and
# greppably via tolerate_overflow=True.
STDIN_LIMIT = 16 * 1024 * 1024
_OVERFLOW_MESSAGE = (
    "[team-kit guard] Hook payload exceeded the %d-byte stdin bound, so this call could not be "
    "inspected — refused rather than waved through (spec II.4 bounded read + fail-closed).\n"
    "Remedy: split the call; a tool payload this large is never a normal delegation.\n"
)

_PATCH_FILE_RX = re.compile(r"(?m)^\*{3} (Add|Update|Delete) File: (.+?)\s*$")
_PATCH_MOVE_RX = re.compile(r"(?m)^\*{3} Move to: (.+?)\s*$")
# providers use different tool vocabularies — normalize the KNOWN aliases to the Claude names
# every guard filters on; unknown names pass through untouched (guards then fail open, by design).
_TOOL_ALIASES = {"edit": "Edit", "write": "Write", "bash": "Bash", "powershell": "PowerShell",
                 "str_replace": "Edit", "create_file": "Write", "shell": "Bash"}


def load(stream=None, limit=None, tolerate_overflow=False):
    """Read + normalize the hook payload from stdin. Returns {} on garbage.

    stdin is read as BYTES and decoded UTF-8: providers send raw UTF-8, but Windows text-mode
    stdin decodes cp1252 — an audit proved non-ASCII payload content (umlauts in question text,
    German file paths) arrived as mojibake and pattern matches silently missed.

    The read is BOUNDED at `limit` bytes, defaulting to STDIN_LIMIT (spec II.4). Beyond it this
    EXITS 2 with a block message — see STDIN_LIMIT for why that is the default rather than a
    return value. Comfort hooks pass tolerate_overflow=True and get the `_stdin_overflow`
    sentinel instead. The limit default is resolved HERE, not in the signature, so the
    module-level cap stays adjustable at runtime (tests, tuning)."""
    limit = STDIN_LIMIT if limit is None else limit
    raw = None
    try:
        source = stream if stream is not None else sys.stdin
        buffer = getattr(source, "buffer", None)
        if stream is None and buffer is not None:
            raw = buffer.read(limit + 1)
        else:
            # text stream (tests): read(n) counts CHARACTERS, so the encoded result may exceed
            # the cap slightly — the overflow check below is on bytes and errs toward blocking
            raw = source.read(limit + 1)
            if isinstance(raw, str):
                raw = raw.encode("utf-8", "replace")
    except Exception:
        return {}
    if raw is None:
        return {}
    if len(raw) > limit:
        if not tolerate_overflow:
            sys.stderr.write(_OVERFLOW_MESSAGE % limit)
            sys.exit(2)
        return {"_stdin_overflow": True, "tool_input": {}}
    try:
        data = json.loads(raw.decode("utf-8", "replace"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    ti = data.get("tool_input")
    if not isinstance(ti, dict):
        ti = {}
        data["tool_input"] = ti
    tn = str(data.get("tool_name") or "")
    if tn in _TOOL_ALIASES:
        data["tool_name"] = _TOOL_ALIASES[tn]
    if data.get("tool_name") == "apply_patch":
        patch = str(ti.get("command") or ti.get("input") or "")
        raw_operations = _PATCH_FILE_RX.findall(patch)
        raw_operations += [("Move", path) for path in _PATCH_MOVE_RX.findall(patch)]
        # patch paths are CWD-relative (Codex applies the patch against the session cwd). Join
        # against cwd for the file the edit REALLY touches, and ADDITIONALLY against the repo
        # root when the two differ: block-guards then catch either interpretation (fail-closed
        # against cwd drift — the failure class _root.py exists for), while isfile-based checks
        # simply skip the nonexistent candidate. (Audit finding: cwd in a subdir made a
        # repo-root-looking patch path miss every prefix check.)
        base = str(data.get("cwd") or "")
        root = find_repo_root(base or None)
        operations = []
        for operation, q in raw_operations:
            p = q.replace("\\", "/")
            if os.path.isabs(p):
                operations.append({"operation": operation, "path": p})
                continue
            operations.append({"operation": operation,
                               "path": os.path.join(base, p) if base else p})
            if root and os.path.abspath(root) != os.path.abspath(base or root):
                cand = os.path.join(root, p)
                if not any(item["path"] == cand and item["operation"] == operation
                           for item in operations):
                    operations.append({"operation": operation, "path": cand})
        paths = [item["path"] for item in operations]
        data["tool_name"] = ("Write" if operations and
                             all(item["operation"] == "Add" for item in operations) else "Edit")
        data["_file_operations"] = operations
        data["_file_paths"] = paths
        if paths and not ti.get("file_path"):
            ti["file_path"] = paths[0]
    return data


def file_paths(data):
    """Every file this tool call touches (list of str; may be empty). Path guards MUST iterate
    this instead of reading tool_input.file_path once — a Codex multi-file patch is one call."""
    if isinstance(data.get("_file_paths"), list) and data["_file_paths"]:
        return [str(p) for p in data["_file_paths"]]
    ti = data.get("tool_input") or {}
    # notebook_path: NotebookEdit is a file write like any other, and a guard that does not see it
    # scopes everything except notebooks
    p = ti.get("file_path") or ti.get("path") or ti.get("notebook_path") or ""
    return [str(p)] if p else []


def created_file_paths(data):
    """Paths newly created by apply_patch (`Add File` or a `Move to` destination)."""
    operations = data.get("_file_operations")
    if isinstance(operations, list):
        return [str(item.get("path")) for item in operations
                if isinstance(item, dict) and item.get("operation") in ("Add", "Move")
                and item.get("path")]
    return file_paths(data) if data.get("tool_name") == "Write" else []


# Shared push/merge detection for every git gate (single home — six hook-local copies drifted:
# an audit had to fix the same regression twice). Shell-WRAPPER payloads are CODE
# (`bash -c "git push"` must gate), remaining quoted spans are PROSE (a commit MESSAGE describing
# a push must not). Unquoted prose may still over-trigger — the safe direction for a gate.
# The c-flag may sit in a COMBINED short cluster (`bash -lc`, `-xec` — audit: `-lc` bypassed
# every gate) and quoted payloads may contain ESCAPED quotes — both are handled below.
_WRAPPER_RX = re.compile(
    r'((?:bash|sh|zsh|dash|pwsh|powershell|cmd)(?:\.exe)?\s+(?:[-/]{1,2}[\w-]+\s+)*'
    r'[-/]{1,2}(?:[A-Za-z]*c|command)\s+)("((?:\\.|[^"\\])*)"|\'((?:\\.|[^\'\\])*)\')',
    re.IGNORECASE | re.DOTALL)
_QUOTED_RX = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')


def git_invocation_text(command):
    """Lowercased command text with wrapper payloads unwrapped and prose quotes stripped."""
    unwrapped = _WRAPPER_RX.sub(
        lambda m: m.group(1) + " " + (m.group(3) if m.group(3) is not None else m.group(4) or "")
        + " ", command or "")
    return _QUOTED_RX.sub(" ", unwrapped.lower())


def wants_push_or_merge(command):
    """True when the command really invokes `git push`/`git merge` (not merely mentions it)."""
    return re.search(r"\bgit\b[^&|;\n]*\b(push|merge)\b", git_invocation_text(command)) is not None


def run_captured(cmd, cwd=None, timeout=60, **kw):
    """subprocess.run with captured TEXT output decoded UTF-8 (lossy, never a crash).

    THE one place hooks run tools and read their output: git and every provider tool emit
    UTF-8, while Windows' locale codec (cp1252) mojibakes umlauts in filenames, branch names,
    commit messages and tool output — three separate audit findings in one week came from
    per-call-site encoding choices. Raises nothing beyond subprocess's own errors
    (TimeoutExpired etc.) — callers keep their existing try/except semantics."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout, **kw)


def stop(message, event):
    """Block a post/stop event using the current provider's event-specific contract.

    Codex PostToolUse/SubagentStop consume `decision: block` + `reason`. Claude uses exit 2 with
    stderr for these events. PreToolUse guards should keep using exit 2 directly; current Codex
    builds support that contract and include `agent_id` for subagent tool calls.
    """
    if (os.environ.get("TEAM_KIT_PROVIDER", "").lower() == "codex"
            and event in ("PostToolUse", "SubagentStop")):
        sys.stdout.write(json.dumps({"decision": "block", "reason": message}) + "\n")
        sys.exit(0)
    sys.stderr.write(message)
    sys.exit(2)
