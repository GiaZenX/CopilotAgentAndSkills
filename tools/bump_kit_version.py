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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The kit-hash inputs (skipped dirs, shared harness files) live with the hash itself, in
# `kernel.hashing` — see kit_hash() below.


def discover_kits(root=ROOT):
    """Every directory under team-kits/ that ships agents/ is a kit — no hard-coded list, so a
    future third kit can never ship unversioned/unchecked by omission."""
    base = os.path.join(root, "team-kits")
    if not os.path.isdir(base):
        return []
    return sorted(d for d in os.listdir(base)
                  if os.path.isdir(os.path.join(base, d, "agents")))


def kit_hash(kit_dir):
    """Hash kit-local files plus shared scaffold/generator inputs (except VERSION + caches).

    THE DEFINITION LIVES IN THE KERNEL (`kernel.hashing.kit_hash`) because two things need it and
    only one of them can reach `tools/`: this stamper, and `write_kit_state.py`, which checks that
    the kit it compares an installation against really is that kit. A copy here would have been
    the third duplicated hash in this repo's history, and the previous two each produced a round
    of findings.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
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


def main():
    changed = False
    for kit in discover_kits():
        kit_dir = os.path.join(ROOT, "team-kits", kit)
        if not os.path.isdir(kit_dir):
            continue
        vfile = os.path.join(kit_dir, "VERSION")
        digest = kit_hash(kit_dir)
        old = ""
        if os.path.isfile(vfile):
            old = open(vfile, encoding="utf-8").read()
        if ("content: %s" % digest) in old:
            print("  %s: unchanged (%s)" % (kit, read_version_line(vfile)))
            continue
        version = next_version(read_version_line(vfile))
        with open(vfile, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("version: %s\ncontent: %s\n" % (version, digest))
        print("  %s: bumped -> %s" % (kit, version))
        changed = True
    if changed:
        print("VERSION files updated — commit them with the kit change.")
    sys.exit(0)


if __name__ == "__main__":
    main()
