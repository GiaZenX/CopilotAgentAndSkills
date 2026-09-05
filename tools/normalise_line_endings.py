#!/usr/bin/env python3
"""
normalise_line_endings.py — put every tracked text file back on LF, once, and never guess (BUG-0025).

WHY A SCRIPT AND NOT A `git add --renormalize`. Renormalising rewrites the INDEX; what is wrong in
the ordinary case here is the WORKING TREE, and the two are not the same file. `.gitattributes` pins
`* text=auto eol=lf`, so git stores LF and checks out LF -- the CRLF this repairs was written into
the file AFTER the checkout, by an editor, a generator or a shell redirection on a host whose git
config says `core.autocrlf=true` (this repo's local config and this host's system config both do).
There the committed blob is already what the file should be, and the repair is to make the file on
disk equal it again. Where that premise does NOT hold -- a blob that carries CRLF itself -- this
tool says so and sends the caller to `git add --renormalize`; and where BOTH are wrong at once, it
says that too and offers neither command alone. See `_verdict`.

THE PRECONDITION IS THE WHOLE SAFETY OF THIS SCRIPT: a file is rewritten only when its
CRLF-normalised bytes are BYTE-FOR-BYTE the blob `HEAD` holds. Where they are not, the file carries
a real, uncommitted change and normalising it would smuggle an edit in under the name of a
line-ending repair -- so it is refused and NAMED, never silently skipped. (The shape is the one
`_round-scratch/TSK-0120/normalise_one.py` used for the two files the generation-3 merge repaired;
this is that measurement made repeatable.)

WHICH FILES ARE TEXT IS GIT'S ANSWER, NOT AN EXTENSION LIST. `git ls-files --eol` reports `w/-text`
for every path git resolves as binary, which under `text=auto` is decided by BYTES -- a NUL in the
first 8000. That git's heuristic and a plain NUL scan agree over this whole tree, and that the
pin really reaches every text file, is measured by
`tools/test_repo_hygiene.py::test_git_decides_binary_by_bytes_and_pins_every_text_file_to_lf`.
WHY THE DISTINCTION EARNS ITS KEEP is a separate fact and NOT that test's subject: binaries in
this tree do carry CRLF byte pairs, so a normaliser going by extension -- or one replacing every
CRLF it finds -- would rewrite them. The figure behind that sentence is in the round protocol.

WHAT IT WILL NOT TOUCH is the canonical part of `project_memory/`, and check and remedy share ONE
predicate for it -- `repairable` below, which `tools/test_repo_hygiene.py` imports rather than
restating. Gate 1 refuses every tool write there; a remedy that offered to rewrite it would promise
something the enforcement layer would refuse anyway, and the round-1 verification found the check
excusing that tree while this tool did not.

    python tools/normalise_line_endings.py            # say what would change, change nothing
    python tools/normalise_line_endings.py --apply    # rewrite the files that pass the precondition

`tools/test_repo_hygiene.py::test_no_tracked_text_file_checks_out_with_crlf` is the check this
script is the remedy for; `docs/line-endings.md` carries the cause and what this repo does not do
about it.
"""
import os
import subprocess
import sys

# NO `sys.dont_write_bytecode` HERE, deliberately, and the reason is the whole reason. `validate.py`
# sets it because it imports out of `team-kits/` -- the source side of the kit hash -- and may not
# cache into that tree. This tool imports nothing but the standard library, so the flag buys it
# nothing; and since `tools/test_repo_hygiene.py` imports this module for the one predicate they
# share, the flag would be set process-wide for a suite it does nothing for. No test is named here
# as a tripwire for that: an earlier version of this comment named one, and the flag was measured to
# make that test's assertion EASIER, never red -- a named check that cannot fall is worse than none.

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The `w/` readings that mean "this text file is not on LF". `none` (a file with no line at all) and
# `lf` are already right, and `-text` is git saying binary -- see the module docstring.
DRIFTED = ("crlf", "mixed")
CRLF, LF = b"\r\n", b"\n"
# The canonical state directory and the one subtree of it that is NOT canonical.
STATE = "project_memory/"
STATE_PROPOSALS = "project_memory/staging/"


def repairable(path):
    """False for the canonical state no tool write reaches, True for everything else.

    `gate_lead_write_scope.py` refuses every tool write under `project_memory/` except `staging/`,
    so a CRLF file in the canonical part can be neither reported as actionable nor repaired from a
    harness session. ONE predicate, used by the check and by this remedy: the first cut had the
    exclusion only in the check, which made the protocol's sentence about the audit log a promise
    this tool did not keep -- it was held by nothing but that file's size happening to fail the
    byte precondition. `staging/` is deliberately NOT excluded: proposals there are ordinary files.
    """
    return not (path.startswith(STATE) and not path.startswith(STATE_PROPOSALS))


def _git(*argv):
    """One git call in this repo, its output decoded."""
    result = subprocess.run(["git"] + list(argv), cwd=ROOT, capture_output=True, timeout=300)
    if result.returncode != 0:
        raise SystemExit("git %s failed: %s" % (" ".join(argv),
                                                result.stderr.decode("utf-8", "replace").strip()))
    return result.stdout.decode("utf-8", "replace")


def drifted_files():
    """`(repairable, out of reach)` -- tracked paths whose WORKING TREE is not LF, in git's reading.

    Split rather than filtered, because the second list is not nothing: it is what this tool
    deliberately will not touch, and a caller that never hears about it cannot tell an empty tree
    from a silent one.
    """
    found = []
    for line in _git("ls-files", "--eol").splitlines():
        if "\t" not in line:
            continue
        fields, path = line.split("\t", 1)
        for field in fields.split():
            if field.startswith("w/") and field[2:] in DRIFTED:
                found.append(path)
    return sorted(p for p in found if repairable(p)), sorted(p for p in found if not repairable(p))


def _committed(path):
    """The bytes `HEAD` holds for `path`, or None where HEAD has no such blob."""
    result = subprocess.run(["git", "show", "HEAD:%s" % path], cwd=ROOT, capture_output=True,
                            timeout=300)
    return result.stdout if result.returncode == 0 else None


def _verdict(path):
    """`(verdict, normalised bytes)` for one file -- what would happen, without doing it.

    TWO THINGS CAN BE WRONG, AND THEY ARE NOT EXCLUSIVE -- which is what the second cut got wrong.

      * the blob in `HEAD` carries CRLF ITSELF. Then the working tree is not (or not only) what is
        wrong: `git status` reports nothing on that ground, the file is unchanged, and what needs
        rewriting is the INDEX -- `git add --renormalize`. Saying "it carries an uncommitted change"
        there sends the caller after an edit that does not exist (the first cut said exactly that);
      * the file differs from the blob BEYOND its line endings. Then it carries a real, uncommitted
        change, and a line-ending repair may not swallow one.

    BOTH AT ONCE IS A REAL STATE, and it is the one the second cut answered with the first sentence
    alone: a CRLF blob plus a hand edit. `git status` DOES report that file, and `git add
    --renormalize` would take the foreign edit into the index -- so neither command may be offered
    on its own. The two questions are therefore asked separately, and the comparison for the second
    one is against the blob AS NORMALISED, or a CRLF blob would make every file look edited.

    Both classes are empty in this repo today (measured: no tracked text path has a CRLF blob),
    which is exactly why a wrong sentence could stand here twice.
    """
    with open(os.path.join(ROOT, path.replace("/", os.sep)), "rb") as handle:
        body = handle.read()
    normalised = body.replace(CRLF, LF)
    committed = _committed(path)
    if committed is None:
        return "no blob in HEAD -- this file is not committed, so nothing says what it should be", None
    blob_carries_crlf = CRLF in committed
    diverges = normalised != committed.replace(CRLF, LF)
    if blob_carries_crlf and diverges:
        return ("TWO things are wrong at once: the blob HEAD holds carries CRLF itself, AND this "
                "file differs from it beyond its line endings (%d bytes normalised against %d in "
                "the blob). So `git status` DOES report it, and `git add --renormalize` would take "
                "that other change into the index with it -- neither command is the answer on its "
                "own. Decide the content change first, then renormalise"
                % (len(normalised), len(committed.replace(CRLF, LF)))), None
    if blob_carries_crlf:
        return ("the blob HEAD holds carries CRLF itself, so the working tree is not what is wrong "
                "here and `git status` says nothing about this file. The index is what needs "
                "rewriting: `git add --renormalize -- %s`" % path), None
    if diverges:
        return ("normalised it is %d bytes and HEAD holds %d -- it carries a real uncommitted "
                "change, and a line-ending repair may not swallow one"
                % (len(normalised), len(committed))), None
    return "ok", normalised


def main(argv):
    apply_it = "--apply" in argv
    files, out_of_reach = drifted_files()
    if out_of_reach:
        print("%d file(s) are NOT this tool's to repair -- canonical state, which no tool write "
              "reaches (gate 1); they are repaired where they are written:" % len(out_of_reach))
        for path in out_of_reach:
            print("  %s" % path)
    if not files:
        print("every tracked text file this tool may touch is already on LF -- nothing to do")
        return 0
    repaired, refused = [], []
    for path in files:
        verdict, normalised = _verdict(path)
        if normalised is None:
            refused.append((path, verdict))
            continue
        if apply_it:
            with open(os.path.join(ROOT, path.replace("/", os.sep)), "wb") as handle:
                handle.write(normalised)
        repaired.append(path)
    word = "normalised" if apply_it else "would be normalised (run with --apply)"
    print("%d file(s) %s:" % (len(repaired), word))
    for path in repaired:
        print("  %s" % path)
    if refused:
        print("%d file(s) REFUSED -- each one is named with what stopped it:" % len(refused))
        for path, why in refused:
            print("  %s: %s" % (path, why))
    return 1 if refused else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
