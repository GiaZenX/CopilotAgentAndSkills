#!/usr/bin/env python3
"""The plan document is answerable to the repo — `docs/reviews/phase0-disposition.md`.

That file is the user-approved disposition PER FILE, and every round writes into it. It cites the
code by name and itself by number, and until this module existed nothing evaluated a single one of
those citations. Measured on 2026-07-31, before any of it was fixed: eight code citations pointed
at lines that had moved, the four summary figures were each short by the rows a later round had
appended, and the lockstep split said 41/39 where the table held 40/40. A steering document that
is wrong about the code is the same defect as a comment claiming protection the code does not
build — one level up, where it is harder to notice.

WHAT IS CHECKED AND WHAT IS NOT, so the green light is not read as wider than it is:

  * THE FIGURES ARE DERIVED. Every number this module asserts is COUNTED from the inventory tables
    and compared against what the prose says. Nobody has to maintain them; they are maintained by
    being counted, and a row appended without touching the summary is a failure rather than a
    silent drift.
  * A CODE CITATION NAMES A SYMBOL, NOT A LINE. `report.py:522` is a fact with a shelf life of one
    edit — the field it pointed at had moved to 731 and the function to 715, and nothing noticed
    for a release. `report.py:_check_premise_recheck` is the same statement in a form the AST can
    resolve, so it survives every edit that does not delete the thing being cited. The check
    RESOLVES it; a citation whose symbol does not exist fails.
  * A SELF-REFERENCE MAY NAME THE ROW'S PATH instead of a line number, and one that does is
    resolved against the inventory. NUMERIC self-references are NOT checked and this is the honest
    limit of this module: a bare "Zeile 321" cannot be told apart from a line number in some other
    file ("`progress.yaml` Zeile 13/60/135") without reading the sentence, and six of them were
    measured pointing at the wrong row while still landing on A row. Those six were converted to
    the path form; the rest stay unchecked until they are converted too.
"""
import ast
import io
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(ROOT, "docs", "reviews", "phase0-disposition.md")

# The four values the inventory's `disposition` column may carry (the document's own vocabulary,
# stated in its summary table). A row whose second cell is none of them is not an inventory row —
# which is what keeps the parity matrix and the spike tables out of the count.
DISPOSITIONS = ("übernehmen", "anpassen", "durch V2-Mechanik ersetzt", "bewusst entfernen")
ANCHOR = "⚓"


def _lines():
    with open(DOC, encoding="utf-8") as handle:
        return handle.read().splitlines()


def _cells(row):
    """The cells of one markdown table row — split at the pipes that ARE cell separators.

    `str.split("|")` is the obvious reader and it is wrong for this document, which is ABOUT hook
    matchers and shell metacharacters: three inventory rows carry a pipe inside a code span
    (`Bash|PowerShell`, `| sh`, `| & ; ( ) < >`, `agent_completed|agent_needs_input`) and a fourth
    spells them escaped (`Bash\\|PowerShell\\|Edit`). Split naively they yield 4, 6 and 9 cells, a
    reader that demands three DROPS them, and it drops them SILENTLY — which is how the first cut
    of this module reported 280/141/80 and got the summary "corrected" from right to wrong: the
    true set is 283/144/82, and the measured difference was entirely this function.

    Two rules, both from GFM: a pipe inside a backtick span is content, and a backslash-escaped
    pipe is content. Everything else separates. `test_a_row_whose_description_contains_a_pipe_is_
    counted` is the floor that keeps this honest — the version above passed the whole module with
    the pipe rows invisible.
    """
    out, buf, in_span, index = [], [], False, 0
    while index < len(row):
        char = row[index]
        if char == "\\" and index + 1 < len(row):
            buf.append(row[index:index + 2])
            index += 2
            continue
        if char == "`":
            in_span = not in_span
        if char == "|" and not in_span:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(char)
        index += 1
    out.append("".join(buf))
    return [cell.strip() for cell in out]


def _inventory_rows():
    """(part, path, disposition) for every row of the FULL INVENTORY, i.e. of §1.1 and §1.2.

    Section 1 is what the document calls the Vollinventar and is where its summary table sits, so
    that is the subject. §2 re-enumerates the lockstep subset in prose and §3/§6 carry tables of a
    different shape; counting those in would answer a different question than the summary asks.
    """
    part = None
    rows = []
    for line in _lines():
        if line.startswith("### 1.1"):
            part = "Teil 1"
            continue
        if line.startswith("### 1.2"):
            part = "Teil 2"
            continue
        if line.startswith("## "):
            part = None
            continue
        if part is None or not line.startswith("|"):
            continue
        cells = _cells(line.strip().strip("|"))
        if len(cells) != 3 or cells[1].strip("*") not in DISPOSITIONS:
            continue
        rows.append((part, cells[0], cells[1].strip("*")))
    return rows


def _path_of(cell):
    """The repo-relative path an inventory row's first cell names, without the lockstep marker."""
    return cell.lstrip(ANCHOR).strip().strip("`")


def test_the_inventory_has_rows_to_count():
    """A floor, so every derivation below cannot pass by measuring an empty document."""
    rows = _inventory_rows()
    assert len(rows) > 200, len(rows)
    assert {part for part, _path, _disposition in rows} == {"Teil 1", "Teil 2"}


def test_a_row_whose_description_contains_a_pipe_is_counted():
    """The floor `_cells` needed and did not have — a row this reader cannot see is a row nobody
    counts, and a summary derived from an incomplete count is worse than a hand-written one:
    it looks maintained.

    THREE SHAPES, all of them measured IN this document rather than invented for the test: a raw
    pipe inside a code span (`Bash|PowerShell`, row `⚓ constitution/AGENTS.md`), a code span that
    IS a pipe (`| sh` and the metacharacter set, row `⚓ hooks/gate_git.py`), and escaped pipes
    (`Bash\\|PowerShell\\|Edit`, row `gen_provider_artifacts.py`). Split at every pipe, they parse
    as 4, 6 and 9 cells and drop out of the inventory — which is exactly what happened: the module
    reported 280 rows and 141 `anpassen`, the summary table was "corrected" to those figures, and
    all six tests were green over a document that had been made wrong.

    The counter-direction is asserted too, so the fix cannot be "accept any cell count": a row
    with a genuine fourth column is still not an inventory row.
    """
    shapes = {
        "raw pipe in a span": "| ⚓ a/b.py | anpassen | matcher `Bash|PowerShell` bleibt |",
        "span that is a pipe": "| c/d.py | übernehmen | Segmente an `&&`/`|`/`;` trennen |",
        "escaped pipes": "| e/f.py | anpassen | `Bash\\|PowerShell\\|Edit` gilt weiter |",
    }
    for label, row in shapes.items():
        cells = _cells(row.strip().strip("|"))
        assert len(cells) == 3, "%s: parsed as %d cells %r" % (label, len(cells), cells)
        assert cells[1] in DISPOSITIONS, label
    four_columns = _cells("| übernehmen | 28 | 67 | **95** |".strip().strip("|"))
    assert len(four_columns) == 4, four_columns


def test_the_summary_table_is_the_rows_that_are_there():
    """§1's summary table, cell by cell, against the rows it summarises.

    Measured wrong on 2026-07-31: it claimed 92/140/43/1 over 101+175=276 rows while the tables
    held 95/141/43/1 over 104+176=280. Seven rows appended by later rounds had never been counted,
    and nothing could say so.
    """
    rows = _inventory_rows()
    counted = {}
    for part, _path, disposition in rows:
        counted[(part, disposition)] = counted.get((part, disposition), 0) + 1
    claimed = {}
    for line in _lines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("*") for cell in _cells(line.strip().strip("|"))]
        if len(cells) == 4 and cells[0] in DISPOSITIONS:
            claimed[cells[0]] = tuple(cells[1:])
    assert set(claimed) == set(DISPOSITIONS), sorted(claimed)
    for disposition in DISPOSITIONS:
        expected = (counted.get(("Teil 1", disposition), 0),
                    counted.get(("Teil 2", disposition), 0))
        expected = tuple(str(n) for n in expected + (sum(expected),))
        assert claimed[disposition] == expected, (
            "the summary row for %r says %s; the tables hold %s"
            % (disposition, claimed[disposition], expected))


def test_the_headline_figures_are_the_rows_that_are_there():
    """The Kurzfazit and the §1 heading repeat the same four numbers in prose — same source."""
    rows = _inventory_rows()
    # the prose wraps, so a figure and its label are routinely split across a line break — the
    # search is over the reading view, not over the source lines
    text = re.sub(r"\s+", " ", "\n".join(_lines()))
    total = len(rows)
    assert re.search(r"## 1\. Vollinventar \(%d Dateien\)" % total, text), (
        "the §1 heading does not say %d" % total)
    assert re.search(r"\*\*Kurzfazit:\*\* %d Dateien disponiert" % total, text), (
        "the Kurzfazit does not say %d" % total)
    for disposition in DISPOSITIONS:
        counted = sum(1 for _part, _path, value in rows if value == disposition)
        pattern = r"%d %s" % (counted, re.escape(disposition))
        assert re.search(pattern, text), (
            "no headline figure says %r for %r — the tables hold that many"
            % (counted, disposition))


def test_the_lockstep_figures_are_the_anchored_rows_that_are_there():
    """§2's heading and its two part enumerations, against the ⚓ rows of the inventory.

    Measured wrong on 2026-07-31: the enumerations said 41 and 39 while the tables carried 40 and
    40. The TOTAL was right, which is exactly why nobody saw it — a split that adds up is the
    shape an eye passes over.

    WHAT THIS DOES NOT CHECK, named rather than implied: the prose lists in §2 spell their members
    with brace expansion (`dev/hooks/{gate_git, ...}.py`), and this module does not parse them. So
    a member missing from a list while its count is right stays invisible here — two were measured
    that way (`tools/test_hooks_v2.py`, `team-kits/write_kit_state.py` are ⚓ rows of §1 that §2
    does not name). The inventory is the authority; §2 is a reading aid that lags it.
    """
    rows = _inventory_rows()
    anchored = {}
    for part, path, _disposition in rows:
        if path.startswith(ANCHOR):
            anchored[part] = anchored.get(part, 0) + 1
    total = sum(anchored.values())
    text = "\n".join(_lines())
    assert re.search(r"## 2\. Lockstep-Disposition \(%d %s-Dateien\)" % (total, ANCHOR), text), (
        "the §2 heading does not say %d" % total)
    for part in ("Teil 1", "Teil 2"):
        assert re.search(r"\*\*%s \(%d\):\*\*" % (part, anchored[part]), text), (
            "the §2 enumeration for %s does not say %d" % (part, anchored[part]))


# A code citation: a backticked `<file>:<symbol>`, where the file is a repo-relative path or a
# bare basename this repo holds exactly once. The SYMBOL form is the point — see the module
# docstring for why a line number is not a citation this check can keep honest.
_CODE_CITATION = re.compile(r"`([A-Za-z0-9_./-]+\.py):([A-Za-z_][A-Za-z0-9_]*)`")


def _resolve_file(name):
    """The one file in the repo this citation names, or None when it is ambiguous/absent."""
    direct = os.path.join(ROOT, name.replace("/", os.sep))
    if os.path.isfile(direct):
        return direct
    found = []
    for current, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "__pycache__", ".pytest_cache", ".e2e-sandbox")]
        if os.path.basename(name) in filenames and name.count("/") == 0:
            found.append(os.path.join(current, os.path.basename(name)))
    unique = {os.path.basename(p): p for p in found}
    if len(found) == 1:
        return found[0]
    # a file the kits mirror is one name with identical copies — any of them answers the question
    if found and len({open(p, "rb").read() for p in found}) == 1:
        return found[0]
    return None if not found else (found[0] if len(unique) == 1 else None)


def _symbols(path):
    """Every name the module DEFINES: functions, classes, and module-level assignments."""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def test_every_code_citation_resolves_in_the_file_it_names():
    """`file.py:symbol` must be a symbol that file defines — resolved, not spell-checked."""
    text = "\n".join(_lines())
    citations = sorted(set(_CODE_CITATION.findall(text)))
    assert citations, "no code citation found — did the reader narrow?"
    unresolved = []
    for name, symbol in citations:
        path = _resolve_file(name)
        if path is None:
            unresolved.append("%s:%s (no such file in this repo, or several)" % (name, symbol))
            continue
        if symbol not in _symbols(path):
            unresolved.append("%s:%s (the file defines no such name)" % (name, symbol))
    assert not unresolved, (
        "the plan document cites code that is not there:\n  " + "\n  ".join(unresolved))


# A self-reference in the ROW form: "die Zeile `<path>`" / "siehe Zeile `<path>`".
#
# The value has to LOOK like an inventory path (it carries a `/` or an extension), which keeps the
# reader off ordinary German prose that happens to end in the word "Zeile" before a code span —
# measured on the `.gitignore` row, whose sentence "nur eine Wiedereinschluss-Zeile `!pfad` wird
# beurteilt" was read as a reference to a row called `!pfad`.
_ROW_REFERENCE = re.compile(r"Zeile `([A-Za-z0-9_@.-]+(?:/[A-Za-z0-9_@.{}, -]+)+)`")


def test_every_row_reference_resolves_to_exactly_one_inventory_row():
    """The rot-proof form of "siehe Zeile 321": name the row's PATH and let the table answer.

    Six numeric self-references were measured pointing at the wrong row (they had drifted by the
    six lines a later round inserted above them, and all six still landed on A row, so no check
    over line numbers could have seen it). Converted, they resolve here or they fail here.
    """
    paths = {}
    for part, cell, _disposition in _inventory_rows():
        paths.setdefault(_path_of(cell), []).append(part)
    references = sorted(set(_ROW_REFERENCE.findall("\n".join(_lines()))))
    assert references, "no row reference found — did the reader narrow?"
    broken = [ref for ref in references if len(paths.get(ref, [])) != 1]
    assert not broken, (
        "these row references resolve to no inventory row, or to more than one:\n  %s"
        % "\n  ".join("%s -> %d rows" % (ref, len(paths.get(ref, []))) for ref in broken))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))


# -- a citation is answerable to the line it cites ---------------------------------------------

SPEC = os.path.join(ROOT, "docs", "HARNESS_V2_SPEC.md")
# The addenda to spec II.10: the paragraphs whose whole job is to name where the BUILT import
# departs from what II.10 demands. They quote the demand they depart from, and a quotation that
# is not the wording of the line it quotes is the same defect as a comment claiming a protection
# -- one level up, in the paragraph whose subject is honesty.
_ADDENDUM_START = "**Nachtrag 2026-08-04"
# A CITATION IS „...\", A GLOSS IS *...*. The convention is what makes the check possible at all:
# nothing can tell a quoted CITATION from a quoted paraphrase by reading it, so the addenda spell
# the paraphrase in italics. Outside these paragraphs the repo's documents use „...\" for both,
# which is why the check stops here and says so rather than pretending to cover them.
_CITATION = re.compile("„([^„\"]{6,})\"")
_QUOTED_SPAN = re.compile("„[^„\"]{0,400}\"")
# The stores this repository writes are ASCII-only, and the documents are not: a line that reads
# `nur bei Endzustaenden` in an item is quoted `nur bei Endzuständen` in prose and is the same
# line. Folding is what lets the check compare wordings rather than encodings; it folds nothing
# that changes a WORD.
_FOLD = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe",
         "Ü": "Ue", "ß": "ss", "—": "--", "–": "-", "→": "->",
         "’": "'", " ": " "}
_CITED_SUFFIXES = (".py", ".md", ".yaml", ".yml", ".json", ".sh", ".ps1")


def _fold(text):
    for bad, good in _FOLD.items():
        text = text.replace(bad, good)
    return re.sub(r"\s+", " ", text).strip()


def _sources_that_could_be_cited():
    """Every authored text of this repository, with its own QUOTATIONS removed.

    Removing them is what makes the check non-vacuous: a document is in its own corpus (the
    addenda cite II.10's later paragraphs, which is the normal case), so a quotation left in the
    pool would resolve against itself and every wording would pass.
    """
    texts = []
    for base in ("team-kits", "project_memory", "docs"):
        for current, dirs, files in os.walk(os.path.join(ROOT, base)):
            dirs[:] = [name for name in dirs if not name.startswith(".")]
            for name in sorted(files):
                if not name.endswith(_CITED_SUFFIXES):
                    continue
                try:
                    with io.open(os.path.join(current, name), encoding="utf-8") as handle:
                        texts.append(_QUOTED_SPAN.sub(" ", _fold(handle.read())))
                except (OSError, UnicodeDecodeError):
                    continue
    with io.open(os.path.join(ROOT, "README.md"), encoding="utf-8") as handle:
        texts.append(_QUOTED_SPAN.sub(" ", _fold(handle.read())))
    return texts


def test_every_citation_in_the_migration_addenda_carries_the_wording_it_cites():
    """A quotation names a line, so the line has to say that.

    Measured 2026-08-05: the addendum on the move to `legacy/` quoted the demand as `Restore nur
    über expliziten userbestätigten Restore-Befehl` where the demanded line says
    `Wiederherstellung nur über…` -- a different word, in quotation marks, in the paragraph whose
    subject is naming deviations honestly. Nothing read it, so nothing could say so.

    WHAT IS CHECKED: every citation in the II.10 addenda occurs, word for word, somewhere in this
    repository's authored text outside a quotation.

    WHAT IS NOT, and the reason is measured rather than assumed. Counted 2026-08-07 over the whole
    spec with this file's own reader: 35 citation-shaped spans, 7 of them in the addenda (all 7
    resolve) and 28 outside, of which 17 resolve against no line of this repository. The previous
    version of this paragraph explained those away as text that "quotes the world outside this
    repository" -- which holds for most of them (a vendor doc, a product's UI, a research source)
    and NOT for all: `Prefer Mermaid over draw.io` is quoted in II.6a as this repo's own former
    kit ruling, `je <=150 Zeilen` as its own former line budget, `Derived 1:1 from ... v1.11` as
    the header of its own V1 filing plan. Each is an artefact of this repository that no line here
    carries any more, and that is a THIRD class: a citation of something retired reads exactly
    like a mis-worded one, and no reader here can tell them apart.

    So the limit is not "everything out there is foreign". It is that outside the addenda the same
    marks carry citations, paraphrases and quotations of retired text, and a check over them would
    fail on wordings nothing here can read. That is the reason the addenda spell paraphrases in
    italics; the limit is the price of that convention holding in one place only. The numbers
    above are a reading of one day and nothing pins them -- what is pinned is that the addenda
    still carry citations at all (asserted below) and that every one of them resolves.
    """
    with io.open(SPEC, encoding="utf-8") as handle:
        spec = handle.read()
    start = spec.index(_ADDENDUM_START)
    end = spec.index("\n## ", start)
    citations = _CITATION.findall(re.sub(r"\s+", " ", spec[start:end]))
    assert len(citations) >= 5, (
        "the addenda carry almost no citations any more (%d), so this measures nothing"
        % len(citations))
    pool = _sources_that_could_be_cited()
    for citation in citations:
        needle = _fold(citation).rstrip(".;,")
        assert any(needle in text for text in pool), (
            "the addenda quote %r and no line of this repository says that" % citation)
