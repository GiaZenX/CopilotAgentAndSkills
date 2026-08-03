#!/usr/bin/env python3
"""Re-record `tools/lead_package_sizes.json` — the size each lead package may not exceed.

WHY A RECORD AND NOT A CONSTANT. `tools/lead_package.py` carries the reasoning in full; the short
form is that the constant it replaced (25 600 B) derived from nothing but the reading of "25 KB" at
1024 bytes, was missed by all three kits by 6 to 10 KB, and only warned. What is derivable is the
measurement, so the ceiling per kit IS the measurement, and the rule is "no growth without a
reason" instead of "stay under a number somebody chose".

WHY `--write` DEMANDS A `--note`, exactly as `pin_constitution_sections.py` does. A ratchet whose
record can be raised with one keystroke ratchets nothing. Every accepted change appends ONE LINE
PER KIT to the journal in `docs/reviews/phase0-disposition.md`, naming the direction and the two
figures, so raising a ceiling leaves a trace that can be read back.

    python tools/record_lead_package_sizes.py                      # what moved, exit 1 if any
    python tools/record_lead_package_sizes.py --write --note "..."  # record it, with the trace

The measurement is `lead_package.size` over `lead_package.files` — the same two functions
`validate.py` compares against, so this script and the validator cannot drift into two answers
about what a package IS.
"""
import argparse
import glob
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lead_package                                             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")
DOC = os.path.join(ROOT, "docs", "reviews", "phase0-disposition.md")
JOURNAL_HEADING = "## 10. Lead-Paket-Grössenjournal (append-only)"
JOURNAL_INTRO = (
    "Jede übernommene Änderung der Lead-Paket-Grösse, eine Zeile pro Kit, geschrieben von\n"
    "`tools/record_lead_package_sizes.py --write`. Der Rekord selbst steht in\n"
    "`tools/lead_package_sizes.json` und ist die Grenze, die `tools/validate.py` hart erzwingt.\n"
    "Es gibt keinen Aufschlag darauf: ein Spielraum wäre eine zweite gegriffene Zahl neben der\n"
    "gerade entfernten. Wer eine Grenze anhebt, schreibt hier hin, wofür.\n")


def kit_dirs():
    """Every shipped kit — the directories that carry a constitution, taken from the tree."""
    return sorted(os.path.dirname(os.path.dirname(path)) for path in
                  glob.glob(os.path.join(TEAM_KITS, "*", "constitution", "AGENTS.md")))


def measure():
    return {os.path.basename(kit): lead_package.size(kit) for kit in kit_dirs()}


def differences(recorded, measured):
    """[(direction, kit, was, now)] — every kit whose package no longer weighs what is recorded."""
    changes = []
    for kit in sorted(set(recorded) | set(measured)):
        was, now = recorded.get(kit), measured.get(kit)
        if was == now:
            continue
        if was is None:
            changes.append(("NEW", kit, 0, now))
        elif now is None:
            changes.append(("GONE", kit, was, 0))
        else:
            changes.append(("GREW" if now > was else "SHRANK", kit, was, now))
    return changes


def _append_journal(changes, note):
    with io.open(DOC, encoding="utf-8", newline="") as handle:
        raw = handle.read()
    newline = "\r\n" if "\r\n" in raw else "\n"
    body = raw.split(newline)
    if JOURNAL_HEADING not in body:
        body += ["", "---", "", JOURNAL_HEADING, ""] + JOURNAL_INTRO.split("\n")
    stamp = time.strftime("%Y-%m-%d")
    entries = [""]
    for direction, kit, was, now in changes:
        entries.append("- %s · %s · **%s** %d B → %d B (%+d) · Grund: %s"
                       % (stamp, kit, direction, was, now, now - was, note))
    # INTO the journal section, not onto the end of the file — the same correction
    # `pin_constitution_sections.py` carries, and here it is load-bearing from day one because
    # this heading is not the last one in the document as soon as anybody adds a §11.
    head = body.index(JOURNAL_HEADING)
    stop = next((index for index in range(head + 1, len(body))
                 if body[index].startswith("## ")), len(body))
    with io.open(DOC, "w", encoding="utf-8", newline="") as handle:
        handle.write(newline.join(body[:stop] + entries + body[stop:]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true",
                        help="record the measurement (default: only report the difference)")
    parser.add_argument("--note", default="",
                        help="why the change is accepted — required with --write, and written "
                             "into the journal beside every kit it covers")
    args = parser.parse_args(argv)

    measured = measure()
    changes = differences(lead_package.records(), measured)
    for kit in sorted(measured):
        print("%-14s %7d B" % (kit, measured[kit]))
    if not changes:
        print("lead packages: %d kits, every size is the one on record" % len(measured))
        return 0
    print("")
    for direction, kit, was, now in changes:
        print("%-7s %-14s %7d B -> %7d B  (%+d)" % (direction, kit, was, now, now - was))
    if not args.write:
        print("\n%d kit(s) differ from the record. A GREW line is the one that needs an argument: "
              "the package is what every session loads before it does anything. Then re-run with "
              "--write --note \"<reason>\"." % len(changes))
        return 1
    if not args.note.strip():
        print("\n--write needs --note: the journal line is the point of accepting a change.")
        return 2
    with io.open(lead_package.RECORD, "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"_comment": JOURNAL_INTRO.replace("\n", " ").strip(), "sizes": measured},
                  handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    _append_journal(changes, args.note.strip())
    print("\nrecorded %d change(s) in %s and in the journal of %s"
          % (len(changes), os.path.relpath(lead_package.RECORD, ROOT), os.path.relpath(DOC, ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
