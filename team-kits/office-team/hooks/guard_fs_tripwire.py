#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell) — deletes on inbox/ or archive/, and moves OUT of archive/, are blocked.

Business documents are irreplaceable: "originals are moved, never deleted" must not depend on
discipline. Filing INTO archive/ (mv from inbox) stays free; deleting anything under inbox/ or
archive/, or moving something OUT of archive/, blocks. Reorganisation inside the archive runs as
a user-approved migration PROC — if this guard fires on legitimate reorg, that is the signal to
get the user's OK first, not to work around it. Uncertainty -> exit 0.
"""
import os
import re
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _audit
import _compat  # noqa: F401 — UTF-8 stream pinning (import side effect)


DELETE_RX = re.compile(
    r"\b(rm|rmdir|del|erase|rd|Remove-Item|ri)\b[^\n;|&]*\b(inbox|archive)(\b|[/\\])", re.I)
MOVE_RX = re.compile(
    r"\b(mv|move|Move-Item|mi|ren|rename|Rename-Item)\b[^\n;|&]*\barchive[/\\]", re.I)
# shell redirects into the ledger bypass the Edit/Write guard (audit finding: `echo >> ledger/x.csv`)
LEDGER_REDIRECT_RX = re.compile(
    r"(?:[>|]\s*|\btee\b(?:\s+-\S+)*\s+)\"?[^\s\"|;&]*\bledger[/\\][^\s\"|;&]*\.csv", re.I)
# The exemption is for INVOKING the script, not for MENTIONING it. A substring test let
# `echo garbage >> ledger/2026.csv # via ledger_add.py` through -- a comment disabled the rule.
LEDGER_ADD_RX = re.compile(r"(?:^|[;&|(]|\bpython[0-9.]*\s+|\bpy\s+)\s*\S*ledger_add\.py\b", re.I)


def main():
    # BOUNDED read (spec II.4). A raw `json.load(sys.stdin)` will happily buffer a
    # payload of any size, and an oversized one is the shape that turns a hook into
    # a memory event rather than a decision. `_compat.load` caps it at STDIN_LIMIT
    # and exits 2, because a gate that cannot read its input has not judged it.
    data = _compat.load()
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        sys.exit(0)
    cmd = str((data.get("tool_input") or {}).get("command") or "")
    if LEDGER_REDIRECT_RX.search(cmd) and not LEDGER_ADD_RX.search(cmd):
        _audit.record("guard_fs_tripwire", "shell redirect into ledger: %s" % cmd[:120])
        _compat.stop(
            "[team-kit guard] A blind shell redirect into ledger/*.csv is BLOCKED — `>>` writes "
            "whatever it is handed, with no schema, no arithmetic check and no way to tell a row "
            "from a fragment. Editing the ledger IS allowed (user decision V2 I.3/1): use Edit, or "
            "`python scripts/ledger_add.py ...` for a new entry. Either way the whole file is "
            "re-validated afterwards and a failure marks the ledger invalid.\n", "PreToolUse")
    if DELETE_RX.search(cmd):
        _audit.record("guard_fs_tripwire", "delete on inbox/archive: %s" % cmd[:120])
        _compat.stop(
            "[team-kit guard] Deleting under inbox/ or archive/ is BLOCKED — business documents "
            "are moved (with a filing/migration manifest), never deleted. Duplicates get a _dupNN "
            "suffix and a flag.\n", "PreToolUse")
    m = MOVE_RX.search(cmd)
    if m:
        # moving INTO the archive is normal filing (from inbox/, outbox/, reports/ …); only an
        # archive/ SOURCE (moving out) blocks. The SOURCE is the first non-flag token after the
        # verb — checking "first token that mentions archive" wrongly blocked `mv report.pdf
        # archive/…` because the DESTINATION was the first archive mention.
        tail = cmd[m.start():]
        tokens = [t.strip("\"'") for t in tail.split()][1:]          # drop the verb itself
        source = next((t for t in tokens if not t.startswith("-")), "")
        if re.search(r"\barchive[/\\]", source, re.I):
            _audit.record("guard_fs_tripwire", "move out of archive: %s" % cmd[:120])
            _compat.stop(
                "[team-kit guard] Moving files OUT of archive/ is BLOCKED — the archive is the "
                "system of record. Reorganisation runs as a user-approved migration PROC (dry-run "
                "-> OK -> move + manifest); ask the manager/user instead of working around this.\n", "PreToolUse")
    sys.exit(0)


if __name__ == "__main__":
    main()
