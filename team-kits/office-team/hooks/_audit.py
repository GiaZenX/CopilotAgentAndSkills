#!/usr/bin/env python3
"""
Shared helper: append a one-line record whenever a gate BLOCKS, so the (read-only) PM retro
has a data basis for "did this cycle run cleanly / were gates hit". Append-only JSONL under
project_memory/.audit/ — never project state, never blocks, best-effort (failures are swallowed).
"""
import glob
import json
import os
import time
import uuid

try:
    from _root import find_repo_root
except Exception:
    def find_repo_root(start=None):
        return os.environ.get("CLAUDE_PROJECT_DIR") or start or os.getcwd()

# Rotation (spec II.5 "Audit-Logs rotieren bei ~1 MB"). The live file stays small enough to skim
# and to tail; older generations move aside under a timestamp. Only the newest ROTATIONS_KEPT are
# retained — deliberately bounded, because `.audit/` is gitignored LOCAL diagnostics, not the
# audit trail: git history plus Evidence items are (user decision I.3/1).
ROTATE_BYTES = 1024 * 1024
ROTATIONS_KEPT = 5
LOG_NAME = "hook_events.jsonl"


def _rotate(path):
    try:
        if os.path.getsize(path) < ROTATE_BYTES:
            return
    except OSError:
        return
    stem = path[: -len(".jsonl")]
    # UNIQUE target, because hooks run concurrently by construction (PreToolUse fires per tool
    # call) and rotation triggers exactly when the log is busiest. A second-resolution name let
    # two processes compute the SAME target, and os.replace overwrites: the loser renamed its
    # fresh empty log over the winner's full generation, destroying both.
    target = "%s.%d-%d-%s.jsonl" % (stem, int(time.time()), os.getpid(), uuid.uuid4().hex[:6])
    try:
        os.replace(path, target)
    except OSError:
        return  # another hook process rotated first — its file is just as good
    # glob.escape: `[` and `]` are legal in Windows directory names and silently make an
    # unescaped pattern match nothing, which would leave rotations unpruned forever
    rotations = glob.glob(glob.escape(stem) + ".*.jsonl")
    # by mtime, not by name — the name is no longer sortable now that it carries pid + nonce
    for old in sorted(rotations, key=lambda p: os.stat(p).st_mtime)[:-ROTATIONS_KEPT]:
        try:
            os.remove(old)
        except OSError:
            pass


def record_event(hook, event, reason):
    """Generic append (event != block for lifecycle records, e.g. spawns/completions — retro.py
    counts non-block events separately)."""
    try:
        root = find_repo_root()
        d = os.path.join(root, "project_memory", ".audit")
        if not os.path.isdir(os.path.join(root, "project_memory")):
            return  # no project yet -> nothing to log
        os.makedirs(d, exist_ok=True)
        line = json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "hook": hook,
            "event": event,
            # 2000, not 300: the 300-char cut hid exactly the FAIL line of every pipeline block
            # during a real overnight incident — forensics had to fall back to transcripts.
            "reason": (str(reason) or "")[:2000],
        }, ensure_ascii=False)
        log = os.path.join(d, LOG_NAME)
        _rotate(log)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def record(hook, reason):
    record_event(hook, "block", reason)
