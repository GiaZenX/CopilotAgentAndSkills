#!/usr/bin/env python3
"""
bump_kit_version.py — stamp each team kit with a version + content hash.

Writes team-kits/<kit>/VERSION:
    version: YYYY.MM.DD-N        (human-readable, monotonic per day)
    content: <sha256>            (hash over every kit file, CRLF-normalized)

validate.py recomputes the hash and FAILS when kit files changed without a bump — so forgetting
is impossible (CI goes red). The scaffold stamps the version into a project's ./.claude/kit_version;
session_status compares it against the staged kit and flags available updates at session start.

Run after any kit change:  python tools/bump_kit_version.py
"""
import datetime
import os
import sys

# The stamper imports `kernel.hashing` out of `team-kits/` — the tree the installer copies into the
# global staging and the scaffold copies into projects. `tools/validate.py` made that a rule for
# itself ("validation must never create __pycache__ that the installer could accidentally carry
# into the shared team-kit staging tree"); the same applies to every tool that imports from there.
# Bytecode is excluded from `kit_hash` on the grounds that a kit does not ship any, and that
# exclusion is only honest while the source trees genuinely hold none — see
# `kernel.hashing.BYTECODE_SUFFIXES`.
sys.dont_write_bytecode = True

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Everything about WHAT a kit hash covers -- which root entries are kits, which are shared input,
# which are tool leftovers -- lives with the hash itself, in `kernel.hashing`, because that module
# ships and `tools/` does not. Made importable once, here, rather than per call.
sys.path.insert(0, os.path.join(ROOT, "team-kits"))


def discover_kits(root=ROOT):
    """Every directory under team-kits/ that is a kit — no hard-coded list, so a future third kit
    can never ship unversioned/unchecked by omission.

    THE PREDICATE LIVES IN THE KERNEL (`kernel.hashing.is_kit_dir`) because the hash reads it too:
    `kit_hash` treats every root entry that is NOT a kit as shared input hashed into every kit, so
    a directory this stamper and the hash classified differently would be hashed into itself.
    """
    base = os.path.join(root, "team-kits")
    if not os.path.isdir(base):
        return []
    from kernel.hashing import is_kit_dir
    return sorted(d for d in os.listdir(base) if is_kit_dir(os.path.join(base, d)))


def kit_hash(kit_dir):
    """Hash kit-local files plus shared scaffold/generator inputs (except VERSION + caches).

    THE DEFINITION LIVES IN THE KERNEL (`kernel.hashing.kit_hash`) because two things need it and
    only one of them can reach `tools/`: this stamper, and `write_kit_state.py`, which checks that
    the kit it compares an installation against really is that kit. A copy here would have been
    the third duplicated hash in this repo's history, and the previous two each produced a round
    of findings.
    """
    from kernel.hashing import kit_hash as canonical
    return canonical(kit_dir)


def read_version_line(path):
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("version:"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return ""


def next_version(previous):
    today = datetime.date.today().strftime("%Y.%m.%d")
    if previous.startswith(today + "-"):
        try:
            return "%s-%d" % (today, int(previous.rsplit("-", 1)[1]) + 1)
        except ValueError:
            pass
    return today + "-1"


def main(argv=None):
    """Stamp every kit, or with `--check` only REPORT whether a stamp is due.

    `--check` exists because a reviewer reached for it and got a stamper: argv was ignored
    entirely, so `bump_kit_version.py --check` would have WRITTEN the VERSION files it was being
    asked about — and then reported "unchanged" for a tree it had just changed. A flag that a
    reader assumes is read-only has to be read-only or absent; this is the first half.

    Exit codes follow the CI convention `tools/validate.py` already uses: `--check` returns 1 when
    a bump is due, so it can gate a pipeline; the stamping mode always returns 0.
    """
    argv = sys.argv[1:] if argv is None else list(argv)
    check_only = "--check" in argv
    unknown = [argument for argument in argv if argument != "--check"]
    if unknown:
        sys.stderr.write("usage: bump_kit_version.py [--check]\n")
        return 2
    changed = False
    for kit in discover_kits():
        kit_dir = os.path.join(ROOT, "team-kits", kit)
        if not os.path.isdir(kit_dir):
            continue
        vfile = os.path.join(kit_dir, "VERSION")
        # DERIVED KIT FILES ARE REGENERATED BEFORE THE HASH, never remembered by a human. The
        # tray record (`kernel.trays`) is computed from the kit's own `templates/repo`, so a kit
        # that gains or loses a tray would otherwise ship a stale list until somebody noticed —
        # the drift shape this repo keeps paying for. Regenerating first means the stamped hash
        # covers the regenerated file, and `--check` sees the resulting content change as the
        # pending bump it is.
        #
        # `--check` STAYS READ-ONLY, which is the whole reason this is not one call: writing in a
        # mode a reader assumes is read-only is the defect `--check` itself was added for.
        from kernel.trays import document_trays, record_path, stamp_document_trays
        if check_only:
            wanted = "".join(name + "\n" for name in document_trays(kit_dir))
            try:
                with open(record_path(kit_dir), encoding="utf-8", newline="") as fh:
                    stale = fh.read() != wanted
            except OSError:
                stale = True
            if stale:
                print("  %s: BUMP DUE (document_trays.txt is stale)" % kit)
                changed = True
                continue
        else:
            stamp_document_trays(kit_dir)
        digest = kit_hash(kit_dir)
        old = ""
        if os.path.isfile(vfile):
            old = open(vfile, encoding="utf-8").read()
        if ("content: %s" % digest) in old:
            print("  %s: unchanged (%s)" % (kit, read_version_line(vfile)))
            continue
        changed = True
        if check_only:
            print("  %s: BUMP DUE (stamped %s, content moved)" % (kit, read_version_line(vfile)))
            continue
        version = next_version(read_version_line(vfile))
        with open(vfile, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("version: %s\ncontent: %s\n" % (version, digest))
        print("  %s: bumped -> %s" % (kit, version))
    if changed and check_only:
        print("a bump is DUE — run python tools/bump_kit_version.py")
        return 1
    if changed:
        print("VERSION files updated — commit them with the kit change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
