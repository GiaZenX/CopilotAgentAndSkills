#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell) — deletes under inbox/ or archive/, and moves that take a document OUT
of archive/, are blocked.

Business documents are irreplaceable: "originals are moved, never deleted" must not depend on
discipline. Filing INTO archive/ stays free (`gate_filing` is what makes that opening safe);
deleting anything under inbox/ or archive/, or moving something out of archive/, blocks.
Reorganisation inside the archive runs as a user-approved migration PROC — if this guard fires on
legitimate reorg, that is the signal to get the user's OK first, not to work around it.

WHAT "OUT OF ARCHIVE" MEANS, and this is the correction of 2026-08-03. The question is about the
RESOLVED POSITION of the source and of the destination, not about the string `archive/` appearing
in a token. Reading the token was wrong in both directions at once, measured against these hooks: a
move from one archive folder to another was refused (the source token carried the word), and a move
that really emptied the archive was allowed as soon as the source token did not. The audited
project had written the second spelling into an APPROVED procedure, because it was the shape that
got its work done, and two of the refusals in its audit log are moves that never left the archive
at all.

So the fix is not a pattern for that spelling. Source and destination are resolved against the
working directory the command line actually left behind (`_filing`, shared with `gate_filing`, so
the two sides of the wall cannot disagree about where it stands), which reads every spelling whose
TEXT IS THE PATH the same way — a relative path after a `cd` or a `pushd`, a `../` climb, a
wrapper payload. The spellings whose text is NOT the path are the residual, and they are listed at
the end of this docstring rather than implied to be covered.

The DELETE rule keeps its token reading and gains the resolved one on top: the two are a union, so
a `cd archive/x && rm y.pdf` is caught while nothing that was refused before becomes allowed. It is
deliberately NOT the same replacement as the move rule — there is no legitimate delete under these
trays to protect, so there is no false positive to remove.

WHAT THIS DOES NOT SEE, so each stays a decision rather than a discovery:

  * a removal performed inside another program (`python -c "os.remove(...)"`);
  * a token, or a `cd` argument, the shell rewrites before use — a variable, a glob, `~`. `_filing`
    resolves none of them and this guard blocks on none; uncertainty -> exit 0 is this guard's
    contract, and a guess about an unresolvable name would break it;
  * a COPIER told to relocate IS now read as one: a source-deleting flag (`robocopy /MOVE`, `rsync
    --remove-source-files` and its alias `--remove-sent-files`) makes `_filing.relocating` true, so
    emptying the archive with it is refused (BUG-0002, `SOURCE_DELETING_FLAGS`). What stays open is
    the neighbouring case that deletes in the DESTINATION rather than the source — `robocopy inbox
    archive/… /MIR` (which /PURGEs the archive) is not a move OUT of it and this rule does not see it;
    that is a delete INSIDE the archive, and the delete rule keys on verbs (`DELETE_VERBS`), not on a
    robocopy flag;
  * `tar --remove-files` archives the source and then DELETES it, emptying the archive as surely as a
    move — but `tar` is not a copy verb (`_filing` reads copy/move by calling convention and tar has
    none), so `moved_out_of_the_archive` never sees it. Named as a residual in
    docs/POST_V2_WISHLIST.md rather than bolted on here, because catching it means a second,
    non-copier deletion path this guard does not have.
"""
import os
import re
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _audit
import _compat  # noqa: F401 — UTF-8 stream pinning (import side effect)
import _filing
import _root


# The two trays whose contents are DOCUMENTS OF RECORD: what arrived (inbox) and what is filed
# (archive). `outbox/` is the kit's third tray and is deliberately not here — it holds drafts the
# project produces and may discard, so a delete there is ordinary work.
INBOX = "inbox"
PROTECTED_TRAYS = (_filing.ARCHIVE, INBOX)
# The verbs that DESTROY. Read twice on purpose (see the module docstring): once against the raw
# command text, once against what each operand resolves to. The regex is BUILT from the same two
# tuples rather than re-typed — a verb or a tray added to one reading and not the other is exactly
# the half-blind guard this round is correcting.
DELETE_VERBS = ("rm", "rmdir", "del", "erase", "rd", "remove-item", "ri")
DELETE_RX = re.compile(r"\b(%s)\b[^\n;|&]*\b(%s)(\b|[/\\])"
                       % ("|".join(DELETE_VERBS), "|".join(PROTECTED_TRAYS)), re.I)
# shell redirects into the ledger bypass the Edit/Write guard (audit finding: `echo >> ledger/x.csv`).
# The TARGET is read through `_filing.redirect_targets`, which resolves quoting and lifts wrapper
# payloads the same way the write-scope gate reads a state path — a raw scan of the command text saw
# neither `led'g'er/x.csv` nor `"ledger"/x.csv`, both of which name this file (BUG-0003). This
# pattern therefore runs against an already-resolved single word, not the raw line.
LEDGER_CSV_RX = re.compile(r"\bledger[/\\][^\s]*\.csv", re.I)
# The exemption is for INVOKING the script, not for MENTIONING it. A substring test let
# `echo garbage >> ledger/2026.csv # via ledger_add.py` through -- a comment disabled the rule.
LEDGER_ADD_RX = re.compile(r"(?:^|[;&|(]|\bpython[0-9.]*\s+|\bpy\s+)\s*\S*ledger_add\.py\b", re.I)


def writes_the_ledger(command):
    """Does any output redirect in `command` write to a `ledger/*.csv`? — reading every value a
    shell could hand the target (`_compat.shell_readings`), so the POSIX backslash spelling resolves
    too, exactly as the write-scope gate answers the same question for a state path."""
    return any(LEDGER_CSV_RX.search(reading)
               for target in _filing.redirect_targets(command)
               for reading in _compat.shell_readings(target))


def in_a_protected_tray(root, base, token):
    """The repo-relative path this token names, if it lies in a tray of record — else None."""
    relative = _filing.position(root, base, token)
    return relative if any(_filing.under(relative, tray) for tray in PROTECTED_TRAYS) else None


def deleted_document(root, command, bases):
    """The first path this command would delete out of a tray of record, or None."""
    for token, invocation_bases in _filing.named_by(command, bases, DELETE_VERBS):
        for base in invocation_bases:
            found = in_a_protected_tray(root, base, token)
            if found:
                return found
    return None


def moved_out_of_the_archive(root, command, bases):
    """(source, destination) for the first move that takes a document out of archive/, or None.

    Source AND destination are read against the SAME base, because the question is a RELATION
    between two positions and reading each against a different one would compare two different
    repositories. Every base a token may be meant against is tried (`_filing.reading_bases`, plus
    whatever a `cd` in the same command line moved them to); a move that lands anywhere inside
    archive/ is filing or reorganisation and is left alone.
    """
    for move in _filing.moves(command, bases):
        if not _filing.relocating(move) or not move.destination:
            continue          # a copy leaves the original in place: nothing left the archive
        for base in move.bases:
            destination = _filing.position(root, base, move.destination)
            if _filing.under(destination, _filing.ARCHIVE):
                continue
            for source in move.sources:
                relative = _filing.position(root, base, source)
                if _filing.under(relative, _filing.ARCHIVE):
                    return relative, (destination or move.destination)
    return None


def main():
    # BOUNDED read (spec II.4). A raw `json.load(sys.stdin)` will happily buffer a
    # payload of any size, and an oversized one is the shape that turns a hook into
    # a memory event rather than a decision. `_compat.load` caps it at STDIN_LIMIT
    # and exits 2, because a gate that cannot read its input has not judged it.
    data = _compat.load()
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        sys.exit(0)
    cmd = str((data.get("tool_input") or {}).get("command") or "")
    cwd = str(data.get("cwd") or "")
    root = _root.find_repo_root(cwd)
    bases = _filing.reading_bases(root, cwd)
    if writes_the_ledger(cmd) and not LEDGER_ADD_RX.search(cmd):
        _audit.record("guard_fs_tripwire", "shell redirect into ledger: %s" % cmd[:120])
        _compat.stop(
            "[team-kit guard] A blind shell redirect into ledger/*.csv is BLOCKED — `>>` writes "
            "whatever it is handed, with no schema, no arithmetic check and no way to tell a row "
            "from a fragment. Editing the ledger IS allowed (user decision V2 I.3/1): use Edit, or "
            "`python scripts/ledger_add.py ...` for a new entry. Either way the whole file is "
            "re-validated afterwards and a failure marks the ledger invalid.\n", "PreToolUse")
    deleted = deleted_document(root, cmd, bases)
    if DELETE_RX.search(cmd) or deleted:
        _audit.record("guard_fs_tripwire",
                      "delete on inbox/archive (%s): %s" % (deleted or "named in the command",
                                                            cmd[:120]))
        _compat.stop(
            "[team-kit guard] Deleting under inbox/ or archive/ is BLOCKED — business documents "
            "are moved (with a filing/migration manifest), never deleted. Duplicates get a _dupNN "
            "suffix and a flag.\n", "PreToolUse")
    leaving = moved_out_of_the_archive(root, cmd, bases)
    if leaving:
        _audit.record("guard_fs_tripwire",
                      "move out of archive (%s -> %s): %s" % (leaving[0], leaving[1], cmd[:120]))
        _compat.stop(
            "[team-kit guard] Moving files OUT of archive/ is BLOCKED — the archive is the "
            "system of record. This command moves %s to %s, which is outside it. Reorganisation "
            "runs as a user-approved migration PROC (dry-run -> OK -> move + manifest); ask the "
            "manager/user instead of working around this. A move that STAYS inside archive/ is "
            "not this rule and is not blocked, whichever way it is spelled.\n"
            % (leaving[0], leaving[1]), "PreToolUse")
    sys.exit(0)


if __name__ == "__main__":
    main()
