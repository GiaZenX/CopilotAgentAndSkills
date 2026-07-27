#!/usr/bin/env python3
"""
pii_scan.py — data minimization in git (parity risk R3, constitution §2 "Datenminimierung").

THE INCIDENT: a real day-1 deployment committed 140 customer names. Not through a leak and not
through carelessness with a password — through ordinary work. An agent filing documents writes
what it sees, and what it sees is names; every note, every progress line, every "processed the
invoice from <person>" puts one more into a history that is forever.

THE RULE the constitution states: personal names appear ONLY where the business record requires
them — the ledger, under statutory retention. Everything under `project_memory/generated/` (spec
II.9 plans a regenerated scan index over what is actually filed there, with `filing_plan.yaml` as
the filing truth; nothing regenerates it yet, so it may simply not exist) and the migration
manifests are gitignored wherever they do exist, out of history. Every OTHER tracked file
references a document by Beleg-ID, date and doctype, never by customer name.

WHAT THIS CHECKS, and what it cannot: the names it knows are the ones the project has already
written down — `counterparties` in `master_data.yaml`, canonical plus aliases. That is a real
limit and it is the right one to have: a general-purpose name detector on German business text
would flag every street, product and company suffix it met, and a check that cries wolf is a check
someone silences. The counterparty list is exactly the set of names the ledger legitimately holds,
which makes "this name appears OUTSIDE the ledger" a precise question with a precise answer.

  exit 0  no tracked file outside the allowed set names a known counterparty
  exit 1  at least one does — the message names file, line and which name

Usage:  python scripts/pii_scan.py          # all tracked files
        python scripts/pii_scan.py --staged # only what is about to be committed
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Where a name may legitimately appear in a TRACKED file: because the record requires it (the
# ledger, under statutory retention), because the file IS the name list, or because the file is a
# derived view whose names came from the tracked state anyway. Everything else is a finding.
ALLOWED = (
    "ledger/",
    "project_memory/master_data.yaml",      # the name list itself
    # ...and THIS FILE. It is tracked (it ships in the repo template) and its comments carry
    # example names, so on its first run it reported itself: "Muster GmbH" is a placeholder here
    # and a plausible real customer elsewhere. Only this one script is exempt, not all of
    # `scripts/` -- a name hardcoded in `process_doc.py` would be a genuine finding.
    "scripts/pii_scan.py",
    # Every regenerated rollup: the index, the session brief and the filing scan index spec II.9
    # plans all name documents by their target path, and every one of them is rebuilt from the
    # tracked state rather than written by hand -- so a hit there points at the item that carries
    # the name, and fixing the copy would fix nothing. The DIRECTORY, not the three file names:
    # `generated/` is defined as what the kernel rebuilds, so an enumeration would go stale with
    # the next rollup. This is load-bearing, not decorative: the shipped .gitignore keeps the tree
    # untracked, but a project upgraded from an older template still tracks it, and then these are
    # the files the scan meets first.
    "project_memory/generated/",
    "project_memory/business_profile.yaml",  # the user's own details, not a customer's
)
ALLOWED_PREFIXES = tuple(part.replace("\\", "/") for part in ALLOWED)
# Binary and generated things: a PDF in archive/ IS the source document and legitimately contains
# the name; scanning it would flag every file the business is required to keep.
SKIP_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg", ".zip", ".xlsx", ".docx", ".ods", ".odt",
                 ".p7s", ".p7m", ".xml")
SKIP_DIRS = ("archive/", "inbox/", "outbox/", ".git/", "reports/")


def git(*args):
    try:
        result = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def known_names():
    """Canonical counterparties and their aliases, longest first.

    Longest first so a two-word counterparty is reported rather than the single word inside
    it — the finding should name the string a human recognises.
    """
    path = os.path.join(ROOT, "project_memory", "master_data.yaml")
    try:
        import yaml
    except ImportError:
        sys.stderr.write("[pii_scan] PyYAML is not installed, so master_data.yaml cannot be "
                         "read — install it or run this in the project's environment.\n")
        sys.exit(1)
    try:
        with open(path, encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError) as exc:
        sys.stderr.write("[pii_scan] cannot read %s (%s)\n" % (path, exc))
        sys.exit(1)
    names = set()
    for entry in (data.get("counterparties") or []):
        if not isinstance(entry, dict):
            continue
        for value in [entry.get("canonical")] + list(entry.get("aliases") or []):
            text = str(value or "").strip()
            if len(text) >= 4:          # "AWS" and shorter collide with ordinary words
                names.add(text)
    return sorted(names, key=len, reverse=True)


def scannable(rel):
    rel = rel.replace("\\", "/")
    if rel.startswith(ALLOWED_PREFIXES) or rel.startswith(SKIP_DIRS):
        return False
    return not rel.lower().endswith(SKIP_SUFFIXES)


def main():
    staged = "--staged" in sys.argv
    listing = git("diff", "--cached", "--name-only") if staged else git("ls-files")
    if listing is None:
        sys.stderr.write("[pii_scan] not a git repository — nothing to check.\n")
        return 0
    names = known_names()
    if not names:
        print("[pii_scan] master_data.yaml lists no counterparties yet — nothing to match "
              "against. This check grows with the project.")
        return 0
    patterns = [(name, re.compile(re.escape(name), re.IGNORECASE)) for name in names]

    findings = []
    for rel in sorted(set(line.strip() for line in listing.splitlines() if line.strip())):
        if not scannable(rel):
            continue
        try:
            with open(os.path.join(ROOT, rel), encoding="utf-8", errors="ignore") as handle:
                lines = handle.read().splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, start=1):
            for name, pattern in patterns:
                if pattern.search(line):
                    findings.append((rel, number, name, line.strip()[:100]))
                    break          # one finding per line; the first (longest) name is the label

    if not findings:
        print("[pii_scan] %d tracked file(s) checked against %d counterparty name(s): clean."
              % (len(listing.splitlines()), len(names)))
        return 0
    sys.stderr.write(
        "[pii_scan] PERSONAL NAMES OUTSIDE THE LEDGER (%d):\n" % len(findings))
    for rel, number, name, text in findings[:40]:
        sys.stderr.write("  %s:%d  %r\n      %s\n" % (rel, number, name, text))
    if len(findings) > 40:
        sys.stderr.write("  … and %d more\n" % (len(findings) - 40))
    sys.stderr.write(
        "\nConstitution §2: personal names appear ONLY where the business record requires them "
        "(the ledger, statutory retention). A real day-1 deployment committed 140 names this way "
        "— through ordinary filing notes, not through carelessness.\n"
        "Remedy: reference the document by Beleg-ID, date and doctype instead. If a name really "
        "belongs in that file, that is the user's call and the file belongs in the allowed set.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
