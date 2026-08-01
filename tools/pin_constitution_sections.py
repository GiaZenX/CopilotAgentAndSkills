#!/usr/bin/env python3
"""Re-pin `tools/constitution_section_pins.json` — the record every lead-package section is
answerable to.

WHY THIS IS A SEPARATE, MANUAL COMMAND. An independent run deleted each of the 16 sections of the
dev constitution one at a time and ran all 34 instruction-text tests: only §2 and §7 were noticed,
the other 13 could be removed whole with the suite green. The pin closes that by recording a
digest per section, and a pin that re-generated itself inside the test run would record nothing.

WHY `--write` WRITES A JOURNAL. The pin is loud by design: every legitimate rewording reports its
section as CHANGED, and the II.11/3 shortening will move ~50 sections at once. That is exactly the
moment somebody waves it through in one gesture. So `--write` demands a `--note` and appends ONE
LINE PER SECTION to the journal in `docs/reviews/phase0-disposition.md`, naming the section and the
registered hooks it anchors. Accepting a change then leaves a trace that can be read back against
the parity matrix; it stops being a keystroke.

    python tools/pin_constitution_sections.py                      # what moved, exit 1 if any
    python tools/pin_constitution_sections.py --write --note "..."  # record it, with the trace

The measurement itself lives in `tools/test_shortening_net.py` (`measure_sections`,
`section_differences`), so this script and the test cannot drift into two answers about one file.
"""
import argparse
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_shortening_net import (      # noqa: E402
    DOC, PINS, measure_sections, section_differences)

JOURNAL_HEADING = "## 9. Sektionspin-Journal (append-only)"
JOURNAL_INTRO = (
    "Jede übernommene Änderung an einer Lead-Paket-Sektion, eine Zeile pro Sektion, geschrieben\n"
    "von `tools/pin_constitution_sections.py --write`. Der Pin selbst steht in\n"
    "`tools/constitution_section_pins.json`; dieses Journal ist der Grund, warum das Übernehmen\n"
    "einer Änderung ein Vorgang ist und keine Geste. Wer hier nichts schreiben will, hat den Pin\n"
    "nicht gelesen.\n")


def _load_pins():
    try:
        with io.open(PINS, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def _append_journal(changes, note):
    """One line per accepted section, appended to the journal block of the disposition."""
    with io.open(DOC, encoding="utf-8", newline="") as handle:
        raw = handle.read()
    newline = "\r\n" if "\r\n" in raw else "\n"
    body = raw.split(newline)
    if JOURNAL_HEADING not in body:
        body += ["", "---", "", JOURNAL_HEADING, ""] + JOURNAL_INTRO.split("\n")
    stamp = time.strftime("%Y-%m-%d")
    entries = [""]
    for what, kit, name, key, hooks in changes:
        entries.append(
            "- %s · %s · `%s` · §%s — **%s** · verankert %s · Grund: %s"
            % (stamp, kit, name, key, what, ", ".join(hooks) or "keinen registrierten Hook", note))
    # INTO THE JOURNAL SECTION, not onto the end of the file. Appending to `body` put the lines
    # wherever the document happens to end — measured with a later `## 10.` in place, the
    # confirmation landed inside that foreign section. Invisible today only because §9 is last,
    # and this document has grown from §1 to §9.
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
                             "into the journal beside every section it covers")
    args = parser.parse_args(argv)

    measured = measure_sections()
    changes = section_differences(_load_pins(), measured)
    sections = sum(len(file) for kit in measured.values() for file in kit.values())

    if not changes:
        print("lead packages: %d kits, %d files, %d sections, all pins current"
              % (len(measured), sum(len(kit) for kit in measured.values()), sections))
        return 0
    for what, kit, name, key, hooks in changes:
        print("%-7s  %-14s %-28s §%s" % (what, kit, name, key))
        print("%s  anchors: %s" % (" " * 7, ", ".join(hooks) or "no registered hook"))
    if not args.write:
        print("\n%d section(s) differ from the pin. Read each against the parity matrix in "
              "docs/reviews/phase0-disposition.md §3 — a section carrying a rule classified "
              "`behalten` may not lose it — then re-run with --write --note \"<reason>\"."
              % len(changes))
        return 1
    if not args.note.strip():
        print("\n--write needs --note: the journal line is the point of accepting a change.")
        return 2
    with io.open(PINS, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(measured, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    _append_journal(changes, args.note.strip())
    print("\nrecorded %d change(s) in %s and in the journal of %s"
          % (len(changes), os.path.relpath(PINS), os.path.relpath(DOC)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
