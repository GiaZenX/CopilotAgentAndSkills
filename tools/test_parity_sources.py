#!/usr/bin/env python3
"""The source column of the parity matrix, checked against the files it points at.

THE HOLE THIS CLOSES. §3 classifies 116 rules and licenses deleting the prose of 36 of them. The
executor of that deletion finds the prose through the SOURCE column, and until 2026-08-02 nothing
read that column at all: `test_shortening_net._source_kits` resolved the shorthand to a KIT and
never looked at the locator behind it. Measured over the whole column against the revision it was
written in (`491fda7`, where every pointer was still true): of 248 pointer/kit resolutions, 128
named a different declared location than the rule they describe, 2 named a kit whose text does not
carry the rule at all, and one kit that does carry it was named by nobody. The document knew of
exactly one such case.

THE PREDICATE, and why this one. `tools/parity_sources.py` carries the full argument; in short: a
line number is a coordinate produced by counting from outside the file, so the only checkable
things about it are "the file is long enough" (worthless) and a digest over the span (red on every
rewording, which during a shortening is a full-scale false alarm). What IS checkable is whether the
pointer names a location the file DECLARES — its own section number, its own list enumerator, its
own table key. Those identifiers stand inside the file, survive a rewording of the sentence they
head, and vanish when the rule is deleted, moved or renumbered. So the check is red for the edits
the matrix governs and quiet for the edit that must not raise an alarm.

WHAT IT DOES NOT DECIDE — measured here rather than promised away, by
`test_the_anchor_survives_a_rewording_and_dies_on_a_deletion_or_a_rename`: if two items under one
heading SWAP their numbers, `§2.7` still resolves and now names another rule. That is the same
class as "resolves but means something else", and it is not decidable by parsing. Half of it is
caught elsewhere and only for half the files: every section of a LEAD PACKAGE carries a digest pin
(`test_shortening_net.py:test_no_section_of_a_pinned_instruction_file_disappears_unnoticed`), so a
content swap
there forces a second look. A specialist SKILL has no pin, and the pointers that land in one are
COUNTED by `test_the_pointers_no_section_pin_watches_are_counted` — a caveat nobody counts is how a
hole grows quietly, which is the lesson this file inherited from the matcher hole two rounds back.

WHAT IT ALSO DOES NOT SEE, and no test in this module can: a kit whose text carries the rule and
whose pointer is simply absent. A source column is checked for what it CLAIMS, never for what it
omits — the research half of row 54 was found by reading, not by a check, and the next one will be
too.
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parity_sources                                                   # noqa: E402
from parity_sources import ANCHOR_MARK, declared_blocks, resolve        # noqa: E402
from test_shortening_net import _matrix_rows, _pinned_files, _reading_view   # noqa: E402

KIT_DIRS = parity_sources.kit_dirs()


def _row_pointers():
    """(row number, rule, Pointer) for every pointer in the matrix."""
    for number, rule, sources, _classification in _matrix_rows():
        for pointer in parity_sources.pointers(sources):
            yield number, rule, pointer


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def test_the_legend_maps_every_shorthand_to_a_file_a_kit_actually_ships():
    """The map is only worth reading if every entry lands somewhere.

    A shorthand whose path exists in no kit resolves to the empty set of kits, and an empty set
    satisfies every per-kit obligation in the module next door in perfect silence — the exact shape
    `_source_kits` grew an assert for after row 97's sources were mutated to nonsense.
    """
    orphans = []
    for shorthand, relative in sorted(parity_sources.source_files().items()):
        if not any(os.path.isfile(os.path.join(kit, relative.replace("/", os.sep)))
                   for kit in KIT_DIRS):
            orphans.append("%s -> %s" % (shorthand, relative))
    assert not orphans, (
        "the §3 legend maps these shorthands to a file no kit ships: %s" % ", ".join(orphans))
    assert len(parity_sources.source_files()) > 20, "the legend parsed to almost nothing"


def test_every_pointer_names_a_shorthand_the_legend_declares_and_a_kit_that_ships_it():
    """Two failures, one test, because they are the same defect at two depths: a pointer into a
    file nobody has. `dev/audit` is the live example — the office kit ships that same auditor SKILL
    and does NOT carry the file-budget rule, so the kit-prefixed form is what keeps the licence off
    a text that never had the rule.
    """
    broken = []
    for number, _rule, pointer in _row_pointers():
        targets = pointer.targets()
        if targets is None:
            broken.append("#%s %s — no shorthand the legend maps" % (number, pointer.raw))
            continue
        if not targets:
            broken.append("#%s %s — resolves to no kit at all" % (number, pointer.raw))
        for kit, path, shipped in targets:
            if not shipped:
                broken.append("#%s %s — %s does not ship %s"
                              % (number, pointer.raw, os.path.basename(kit),
                                 os.path.relpath(path, kit).replace(os.sep, "/")))
    assert not broken, "the source column points at files that are not there:\n  " + "\n  ".join(
        broken)


def test_no_pointer_is_a_line_number():
    """THE PROPERTY THAT MAKES THE COLUMN CHECKABLE AT ALL.

    A line number is not a weak anchor, it is a different kind of thing: nothing in the target file
    states it, so no reading of the file can confirm or refute it. Before 2026-08-02 all 245
    pointers were line numbers and this test fails on every one of them.
    """
    numeric = []
    for number, _rule, pointer in _row_pointers():
        if pointer.anchors is None:
            numeric.append("#%s %s — carries no locator at all" % (number, pointer.raw))
            continue
        for token in pointer.unanchored_tokens():
            numeric.append("#%s %s — %r is not an anchor (a location a file DECLARES starts with "
                           "%r); a line number cannot be checked against anything"
                           % (number, pointer.raw, token, ANCHOR_MARK))
    assert not numeric, "\n  " + "\n  ".join(numeric)


def test_every_pointer_resolves_to_a_location_its_file_declares():
    """The core check: every anchor, in every kit the pointer covers, names exactly one block.

    Zero hits means the location is gone — the rule was deleted, moved or renumbered, and the
    column has to be brought along. More than one hit means the anchor is ambiguous, which is a
    pointer that sends the reader to two places and is fixed by spelling one more component.
    """
    unresolved, checked = [], 0
    for number, rule, pointer in _row_pointers():
        for kit, path, shipped in pointer.targets() or []:
            if not shipped:
                continue        # reported by the test above; do not report it twice
            text = _read(path)
            for anchor in pointer.anchor_paths():
                checked += 1
                hits = resolve(text, anchor)
                if len(hits) == 1:
                    continue
                where = "%s/%s" % (os.path.basename(kit),
                                   os.path.relpath(path, kit).replace(os.sep, "/"))
                unresolved.append(
                    "#%s (%s) %s%s%s -> %s: %s"
                    % (number, rule[:40], pointer.shorthand, ANCHOR_MARK, anchor, where,
                       "no such location" if not hits
                       else "ambiguous, %d locations: %s"
                            % (len(hits), ", ".join(hit[0] for hit in hits))))
    # A FLOOR AGAINST AN EMPTY SUBJECT. With the pre-2026-08-02 column restored, every locator is
    # a line number, `anchor_paths()` is empty for all of them and this test passed over nothing at
    # all while the column was entirely unchecked (measured on a copy of the repo outside it).
    #
    # THE EXACT FLOOR IS ELSEWHERE, and it is stronger than this one: the sentence "123 of 289" in
    # §3 pins the resolution count to the digit, so removing a SINGLE pointer turns
    # `test_the_pointers_no_section_pin_watches_are_counted` red (measured with `off/AGENTS:§9`
    # taken out of row 29). What remains for this line is the one case that pin cannot see — a
    # subject that collapses while somebody edits the sentence to match it.
    assert checked > 200, "only %d anchors were resolved — the subject has collapsed" % checked
    assert not unresolved, (
        "the parity matrix points at locations these files do not declare:\n  "
        + "\n  ".join(unresolved))


def test_the_anchor_survives_a_rewording_and_dies_on_a_deletion_or_a_rename():
    """The floor under the predicate — four mutations on an IN-MEMORY copy of a shipped file.

    The shipped constitution is read and never written; every mutation happens on the line list.

    Three of them are the claim: a REWORDED rule keeps its anchor (this is what a digest over the
    span could not do, and why the shortening can reformulate without a wall of false alarms), a
    DELETED one loses it, a RENAMED key loses it. The fourth is the LIMIT, asserted so that no
    docstring here can quietly overstate the guarantee: two items that SWAP their numbers keep both
    anchors resolving, each now on the other's rule, and nothing in this module notices.
    """
    source = os.path.join(KIT_DIRS[0], "constitution", "AGENTS.md")
    original = _read(source).splitlines()
    # A real anchor of a real row, and the enumerator is READ OFF it rather than typed twice — a
    # second spelling of "7" here is how a fixture starts mutating a line it no longer names.
    anchor = "2.7"
    item = anchor.rsplit(".", 1)[1]
    neighbour_anchor = "%s.%d" % (anchor.rsplit(".", 1)[0], int(item) + 1)
    hits = resolve("\n".join(original), anchor)
    assert len(hits) == 1, hits
    _path, start, end = hits[0]
    intact = "\n".join(original[start - 1:end])

    def blocks_of(lines):
        return resolve("\n".join(lines), anchor)

    reworded = list(original)
    reworded[start - 1:end] = ["%s. **Different words entirely** — the same duty, said otherwise."
                               % item]
    kept = blocks_of(reworded)
    assert len(kept) == 1 and kept[0][0] == hits[0][0], (
        "a rewording moved the anchor — then it is a digest with extra steps")
    assert "\n".join(reworded[kept[0][1] - 1:kept[0][2]]) != intact, "the mutation did nothing"

    deleted = list(original)
    del deleted[start - 1:end]
    assert not blocks_of(deleted), "a deleted rule kept its anchor"

    renamed = list(original)
    renamed[start - 1] = re.sub(r"^%s\." % item, "%sa." % item, renamed[start - 1])
    assert renamed != original, "the rename mutation did not apply"
    assert not blocks_of(renamed), "a renumbered rule kept its anchor"

    # THE LIMIT, executable: the two neighbours swap their numbers.
    neighbour = resolve("\n".join(original), neighbour_anchor)
    assert len(neighbour) == 1, neighbour
    swapped = list(original)
    swapped[neighbour[0][1] - 1] = re.sub(
        r"^%s\." % neighbour_anchor.rsplit(".", 1)[1], "%s." % item, swapped[neighbour[0][1] - 1])
    swapped[start - 1] = re.sub(
        r"^%s\." % item, "%s." % neighbour_anchor.rsplit(".", 1)[1], swapped[start - 1])
    after = blocks_of(swapped)
    assert len(after) == 1, "the swap broke the fixture, not the point"
    assert "\n".join(swapped[after[0][1] - 1:after[0][2]]) != intact, (
        "the swap did not move the content — the limit is not being measured")


def test_no_anchor_is_cut_shorter_than_two_words_of_the_key_it_names():
    """The narrower half of the migration hole, closed as far as an abbreviation can close it.

    An anchor component is a PREFIX, so a heading that is REWRITTEN while keeping its opening word
    keeps the anchor, which then resolves — uniquely and silently — onto another rule. Measured on
    `dev-team/skills/project-manager/SKILL.md`: `§the` named "The masterplan — the user's IDEA…";
    with the heading replaced by "The output envelope (unrelated rule)", `§the` still resolved.
    Requiring two of the key's word components makes that a rewrite that has to preserve two words.

    Exempt by definition, not by list: a component that IS the whole key (nothing was cut) and a
    key the file allocates as an identifier rather than as words (`2`, `14a`, `7`). What this does
    NOT do: stop a rewrite that keeps the first two words. §3 of the disposition says so beside the
    figure for the files no section pin watches.
    """
    thin, whole, rows, total = [], 0, set(), 0
    for number, _rule, pointer in _row_pointers():
        for _kit, path, shipped in pointer.targets() or []:
            if not shipped:
                continue
            text = _read(path)
            for anchor in pointer.anchor_paths():
                hits = resolve(text, anchor)
                if len(hits) != 1:
                    continue        # the resolution test owns that failure
                total += 1
                keys = hits[0][0].split(".")
                pairs = list(zip(anchor.split("."), keys))
                for component, key in pairs:
                    if not parity_sources._long_enough(component, key):
                        thin.append("#%s %s%s%s — %r stands for %r on one word"
                                    % (number, pointer.shorthand, ANCHOR_MARK, anchor,
                                       component, key))
                # the exempt shape, counted because the document states how often it occurs: a
                # component that IS its key and that key is one WORD (a section number is not one)
                if any(component == key and not key[:1].isdigit() and "-" not in key
                       for component, key in pairs):
                    whole += 1
                    rows.add(number)
    assert not thin, ("these anchors are cut so short that a rewritten heading would keep them:\n  "
                      + "\n  ".join(sorted(set(thin))))
    assert re.search(r"\*\*%d der %d Ankerauflösungen tragen eine einwortige Komponente, die keine "
                     r"Nummer ist\*\*.{0,120}?über %d der %d Zeilen"
                     % (whole, total, len(rows), len(set(row[0] for row in _matrix_rows()))),
                     _reading_view(), re.S), (
        "the document does not state that %d of %d resolutions carry a one-word non-numeric "
        "component, over %d rows" % (whole, total, len(rows)))


def test_the_length_rule_exempts_a_whole_key_and_gives_a_digit_no_dispensation(tmp_path):
    """The floor under `_long_enough`'s ONE exemption, over the case the old one let through.

    Until 2026-08-02 the rule also exempted `key[:1].isdigit()`, meant for `2`, `14a`, `7`. Those
    are single-word keys and are exempt anyway because the component IS the key; what the clause
    actually added was a dispensation for a digit-opening key WITH word parts. The phase tables
    ship two (`0-5`, `6-8`), so `§5.0` would have been permitted to stand for the row `0.5`. No
    anchor in the column used it — an exception that does nothing today and something wrong
    tomorrow, which is the shape being removed.

    Both halves are here: the predicate, and a probe file where the reader really produces the
    anchor, so the rule is measured where it runs and not only where it is written. In the probe
    the digit-opening key is the ONLY one of its shape, so uniqueness does not accidentally do the
    job the length rule is being tested for.
    """
    assert parity_sources._long_enough("do", "do"), "a whole key is a whole key"
    assert parity_sources._long_enough("2", "2")
    assert parity_sources._long_enough("14a", "14a")
    assert parity_sources._long_enough("the-masterplan", "the-masterplan-the-user-s-idea")
    assert not parity_sources._long_enough("the", "the-masterplan-the-user-s-idea")
    assert not parity_sources._long_enough("0", "0-5"), (
        "a key that opens with a digit still gets cut here — the removed exemption is back")
    assert not parity_sources._long_enough("6", "6-8")

    probe = tmp_path / "phases.md"
    probe.write_text(
        "## 5. Phase model\n\n"
        "| # | Phase |\n|---|---|\n"
        "| 0.5 | ASSESSMENT |\n"
        "| 3 | USER_APPROVAL |\n", encoding="utf-8")
    text = probe.read_text(encoding="utf-8")
    paths = [path for path, _s, _e in declared_blocks(text)]
    assert "5.0-5" in paths, paths
    assert len(resolve(text, "5.0")) == 1, "the probe must make `5.0` unique, or it tests nothing"
    assert parity_sources.shortest_anchor(text, "5.0-5") == "5.0-5", (
        "the reader still offers the cut form for a digit-opening key")


def test_the_block_reader_finds_every_kind_of_location_it_claims(tmp_path):
    """A probe carrying one of each declared location, so the reader's coverage rests on cases.

    Written because a reader that silently stops recognising, say, table rows would make dozens of
    pointers "ambiguous" or "missing" with no way to tell that from a real defect — and because the
    coverage claim in `declared_blocks`'s docstring has to be measured somewhere.
    """
    probe = tmp_path / "probe.md"
    probe.write_text(
        "---\nname: probe\n---\n"
        "Lead text before any heading.\n\n"
        "# Probe title\n\n"
        "## 2. Hard rules\n\n"
        "1. First rule.\n"
        "2. Second rule, wrapped\n   over two lines.\n\n"
        "   | Hook | Does |\n   |---|---|\n   | `gate_git` | blocks |\n"
        "   | `gate_pipeline` | blocks too |\n\n"
        "**2a. A bold anchor.**\n\n"
        "## Do (read-only, ~15 min)\n\n"
        "1. Sample.\n"
        "2. Judge.\n", encoding="utf-8")
    text = probe.read_text(encoding="utf-8")
    paths = [path for path, _start, _end in declared_blocks(text)]
    for expected in ("lead", "2", "2.1", "2.2", "2.2.gate-git", "2.2.gate-pipeline", "2.2a",
                     "do-read-only-15-min", "do-read-only-15-min.1"):
        assert expected in paths, (expected, paths)
    # the title is the file's name, not a location inside it
    assert not any(path.startswith("probe-title") for path in paths), paths
    # An abbreviation ends at a WORD BOUNDARY of the real key. That is the rule that keeps `§1`
    # from swallowing `§15` and `§14a`, and it is why `gate-g` is not a way to write `gate-git`.
    assert len(resolve(text, "do")) == 1, resolve(text, "do")
    assert len(resolve(text, "do-read")) == 1
    assert not resolve(text, "do-read-only-1"), "an abbreviation cut mid-word must not resolve"
    assert len(resolve(text, "2.2.gate")) == 2, "two rows share that prefix — must be ambiguous"
    assert len(resolve(text, "2.2.gate-git")) == 1
    assert not resolve(text, "2.2.gate-g"), "an abbreviation cut mid-word must not resolve"
    assert not resolve(text, "2.3"), "an anchor with no block must resolve to nothing"


def test_the_pointers_no_section_pin_watches_are_counted():
    """The named remainder, as a number the document carries.

    An anchor proves a location exists and is unique; it cannot prove the paragraph under it is
    still the rule. For a PINNED file — the lead package plus `hooks/ENFORCEMENT.md` — the section
    digest pin turns any content change into a mandatory second look, so the two together are close
    to a guarantee. For every other source file — the specialist SKILLs — there is no pin, and a
    content swap under a stable anchor is invisible. Read from `_pinned_files` rather than from the
    byte budget's subject, so that the two answers to "what does the pin watch" stay one. That set is counted here rather than described, because the honest instrument for a
    hole this module cannot close is a figure that goes red when it grows.
    """
    watched, unwatched = 0, 0
    for _number, _rule, pointer in _row_pointers():
        for kit, path, shipped in pointer.targets() or []:
            if not shipped:
                continue
            for _anchor in pointer.anchor_paths():
                if path in _pinned_files(kit):
                    watched += 1
                else:
                    unwatched += 1
    total = watched + unwatched
    assert re.search(r"\*\*%d der %d Ankerauflösungen liegen in einer Datei, die kein "
                     r"Sektionspin bewacht\*\*" % (unwatched, total), _reading_view()), (
        "the document does not state that %d of %d anchor resolutions rest on an unpinned file"
        % (unwatched, total))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
