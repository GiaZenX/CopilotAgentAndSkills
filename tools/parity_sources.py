#!/usr/bin/env python3
"""The source column of the parity matrix, read as pointers instead of as prose.

WHY THIS EXISTS. §3 of `docs/reviews/phase0-disposition.md` classifies 116 rules, and 32-odd of
those rows license deleting the rule's prose. Whoever performs the shortening finds that prose
through the SOURCE column. Until 2026-08-02 that column held line numbers (`dev/AGENTS:57`), and a
line number is a coordinate produced by counting from OUTSIDE the file: nothing in the file states
it, so nothing can check it. Measured over the whole column: of 248 pointer/kit resolutions, 128
named a different declared location than the rule they describe.

WHAT A POINTER IS NOW, and why this predicate rather than another:

  * A DIGEST over the cited span would pin the text. It says nothing about content and goes red on
    every reformulation — during a shortening that reformulates ~50 sections, that is a full-scale
    false alarm, and an alarm that always fires is read as noise.
  * A KEYWORD COMPARISON between the matrix cell and the target text is a string search over a
    file. It cannot tell a rule from a sentence that happens to share words, and this repo has paid
    three times for checks that were really searches.
  * What IS decidable: whether the pointer names a location the target file DECLARES ITSELF. A
    heading prints its own number, an ordered list item prints its own enumerator, a table row
    prints its own key cell. Those identifiers are written INSIDE the file, they survive every
    rewording of the sentence they head, and they change exactly when the rule is deleted, moved
    to another section or renumbered — which is the operation the matrix governs. So the anchor is
    red for the edit that must be noticed and green for the edit that must not raise an alarm.

WHAT THIS DOES NOT DECIDE, stated here rather than left for a reader to discover: that the located
paragraph IS the rule the row describes. That is a reading, and no parser performs it. Two things
narrow the gap and neither closes it: the anchor cannot silently follow a text change the way a
line number does, and for the LEAD PACKAGE every anchored section carries a digest pin
(`test_shortening_net.py:test_no_section_of_a_pinned_instruction_file_disappears_unnoticed`), so a
content swap
under a stable anchor forces a second look. For a specialist SKILL there is no such pin — that
remainder is counted, not claimed away, by
`test_parity_sources.py:test_the_pointers_no_section_pin_watches_are_counted`.

The shorthand->file map and the anchor grammar are DECLARED IN THE DOCUMENT and parsed from there.
A table of spellings in this file would be a second answer to a question the document already
answers, and the two would diverge — which is how the shorthand `audit` came to mean the auditor of
all three kits in one reader and of two in another.
"""
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")
DOC = os.path.join(ROOT, "docs", "reviews", "phase0-disposition.md")

ANCHOR_MARK = "§"

_HEADING_RX = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_BOLD_ANCHOR_RX = re.compile(r"^\*\*(\d+[a-z]?)\.\s")
_ORDERED_RX = re.compile(r"^(\s*)(\d+[a-z]?)[.)]\s+\S")
_TABLE_ROW_RX = re.compile(r"^\s*\|(.*)\|\s*$")
_NUMBERED_HEADING_RX = re.compile(r"^(\d+[a-z]?)\.\s*(.*)$")

_BOLD_LEVEL = 50
_LIST_LEVEL = 100
_ROW_LEVEL = 200

# The region before the first declared block. Not an invention: every markdown reader separates it,
# and `test_shortening_net._sections` already treats it as a section of its own. Rule #1 (language)
# lives there in six of the files this column points at.
LEAD_KEY = "lead"


def slug(text):
    """A declared key, reduced to what a reader can type.

    Backticks and `*` are markup, not identity, so `` `gate_git` `` and **gate_git** are the same
    key; everything else that is not a letter or a digit becomes a separator. The underscore is
    NOT treated as markup here even though markdown emphasises with it: in this document's keys it
    is nearly always part of an identifier (`gate_git`, `filing_plan.yaml`), and folding it away
    produced `gategit` — a key a reader cannot map back to the hook it names.
    """
    text = re.sub(r"[`*]", "", text)
    text = unicodedata.normalize("NFKD", text)
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()


def _title_depth(lines):
    """The depth of a heading that TITLES the file rather than dividing it.

    A heading titles the file when it is the first one, unique at its depth, and every other
    heading is deeper — that is what an H1 over a document means. It is dropped from the paths so
    that `§2` is section 2 of the constitution and not a suffix of the document's name.
    """
    depths = [len(match.group(1)) for match in
              (_HEADING_RX.match(line) for line in lines) if match]
    if not depths:
        return None
    top = min(depths)
    return top if depths[0] == top and depths.count(top) == 1 and len(depths) > 1 else None


def declared_blocks(text):
    """[(path, first line, last line)] — every location this file declares about itself.

    Four kinds, and they are one definition rather than four special cases: a block is declared
    when it PRINTS an identifier of its own in first position. A heading prints its number (or,
    lacking one, its wording); an ordered list item prints its enumerator; a table row prints its
    key cell; a bold `**2a.` opener is the same thing as a heading one level down and is what the
    constitutions use for their sub-anchors (`tools/validate.py` already resolves those two forms).
    A plain paragraph and an unordered bullet print nothing and therefore cannot be anchored — the
    enclosing block is what a pointer names then.
    """
    lines = text.splitlines()
    title = _title_depth(lines)
    out, stack = [], []

    def close(level, index):
        while stack and stack[-1][0] >= level:
            _level, _key, start, path = stack.pop()
            out.append((path, start, index))

    def open_block(level, key, index):
        stack.append((level, key, index, ".".join([entry[1] for entry in stack] + [key])))

    for index, line in enumerate(lines, 1):
        heading = _HEADING_RX.match(line)
        if heading:
            depth = len(heading.group(1))
            close(depth, index - 1)
            if depth == title:
                continue
            numbered = _NUMBERED_HEADING_RX.match(heading.group(2))
            open_block(depth, numbered.group(1) if numbered else slug(heading.group(2)), index)
            continue
        bold = _BOLD_ANCHOR_RX.match(line)
        if bold:
            close(_BOLD_LEVEL, index - 1)
            open_block(_BOLD_LEVEL, bold.group(1), index)
            continue
        ordered = _ORDERED_RX.match(line)
        if ordered:
            level = _LIST_LEVEL + len(ordered.group(1))
            close(level, index - 1)
            open_block(level, ordered.group(2), index)
            continue
        row = _TABLE_ROW_RX.match(line)
        if row:
            first = row.group(1).split("|")[0].strip()
            # the `|---|---|` separator prints no key, it prints the table's shape
            key = slug(first) if first and not set(first) <= set("-: ") else ""
            if key:
                close(_ROW_LEVEL, index - 1)
                open_block(_ROW_LEVEL, key, index)
    close(0, len(lines))
    out.sort(key=lambda entry: (entry[1], -entry[2]))
    first_declared = out[0][1] if out else len(lines) + 1
    if first_declared > 1:
        out.insert(0, (LEAD_KEY, 1, first_declared - 1))
    return out


def _component_matches(component, key):
    """May this anchor component stand for that declared key?

    Equal, or an abbreviation that ends at one of the key's own word boundaries. The boundary is
    what keeps `§1` from swallowing `§10` and `§14a`, and it is what lets `§work` keep naming the
    work loop after its heading grew from "Work loop (every cycle, end to end)" to a line and a half
    of qualifiers — measured: that rewording moved eight pointers and none of the anchors.
    """
    return key == component or key.startswith(component + "-")


def resolve(text, anchor):
    """The blocks this anchor names: outermost kept, blocks nested inside them dropped.

    Rooted at the file, so `§5` is section 5 and not item 5 of section 2. Nesting is collapsed
    because naming a section is naming everything under it; two DISJOINT hits mean the anchor is
    ambiguous, and the caller treats that as an error rather than picking one.
    """
    want = anchor.split(".")
    hits = []
    for path, start, end in declared_blocks(text):
        keys = path.split(".")
        if len(keys) >= len(want) and all(
                _component_matches(component, key) for component, key in zip(want, keys)):
            hits.append((path, start, end))
    return [hit for hit in hits if not any(hit[0].startswith(other[0] + ".") for other in hits)]


# HOW SHORT AN ABBREVIATION MAY BE, and it is not a taste question. An anchor component is a
# PREFIX of the key, so a heading that is REWRITTEN while keeping its opening word keeps the
# anchor — which then resolves, uniquely, onto a different rule. Measured on the dev PM SKILL:
# `§the` named "The masterplan — the user's IDEA…", the heading was replaced by "The output
# envelope (unrelated rule)", and `§the` still resolved — silently, onto the new text. Two word
# components make that a rewrite that has to preserve two words, which is no longer an accident.
# It does NOT make migration impossible; §3 of the disposition says so, and for a specialist SKILL
# nothing else watches the spot.
MIN_ANCHOR_WORDS = 2


def _long_enough(component, key):
    """May this component stand for that key at all — length, not uniqueness.

    ONE exemption, and it is a property rather than a class: a component that IS the key. Nothing
    was cut there, so nothing can migrate — an extension of the heading still resolves (that is the
    point of prefix matching) and a rewrite breaks the anchor at the first changed word. A key of a
    single word is covered by the same arithmetic, since two words cannot be demanded of a key that
    has one.

    THE EXEMPTION THAT WAS HERE UNTIL 2026-08-02 AND IS GONE: `key[:1].isdigit()`, meant for `2`,
    `14a`, `7`. Those are single-word keys and were already exempt; what the clause ADDED was a
    dispensation for digit-opening keys that DO have word parts — `0-5` and `6-8` exist in the
    phase tables — so `§5.0` would have been allowed to stand for `0-5`. No anchor in the column
    used it, which is precisely the shape this repo keeps paying for: an exception that does
    nothing today and something wrong tomorrow.
    """
    if component == key:
        return True
    return len(component.split("-")) >= min(MIN_ANCHOR_WORDS, len(key.split("-")))


def shortest_anchor(text, path):
    """The shortest anchor that names exactly this block AND carries enough of each key."""
    keys = path.split(".")
    for depth in range(1, len(keys) + 1):
        head = list(keys[:depth])
        if not _names_only(text, ".".join(head), path):
            continue
        for position, key in enumerate(head):
            for length in range(1, len(key) + 1):
                trial = list(head)
                trial[position] = key[:length]
                if trial[position].endswith("-") or not _long_enough(trial[position], key):
                    continue
                if _names_only(text, ".".join(trial), path):
                    head = trial
                    break
        return ".".join(head)
    return path


def _names_only(text, anchor, path):
    hits = resolve(text, anchor)
    return len(hits) == 1 and hits[0][0] == path


# ------------------------------------------------------------------ the legend, read as a map
def _doc_lines():
    with open(DOC, encoding="utf-8") as handle:
        return handle.read().splitlines()


def _legend_block(label):
    """The lines of the bold-labelled paragraph, up to the blank line that ends it."""
    collecting, block = False, []
    for line in _doc_lines():
        if line.startswith("**%s" % label):
            collecting = True
        elif collecting and not line.strip():
            break
        if collecting:
            block.append(line)
    assert block, "the document declares no %r paragraph" % label
    return block


_MAP_RX = re.compile(r"`([A-Za-z][A-Za-z-]*)`\s*→\s*`([^`]+)`")


def source_files():
    """{shorthand: kit-relative path} — DECLARED IN THE DOCUMENT, parsed here.

    A shorthand that resolves to nothing is a typo in the very column the shortening will read, so
    the callers treat an unknown one as an error and never as an empty set.
    """
    # ONE STRING, not one line at a time: the paragraph is wrapped at 100 columns and a `shorthand
    # -> path` pair sits astride the break as often as not. Read line-wise, ten of the twenty-five
    # entries were invisible and their pointers resolved to NO kit at all — the silent-empty-set
    # failure this module's asserts exist for, and it turned up in the first run.
    paragraph = re.sub(r"\s+", " ", " ".join(_legend_block("Quellen-Kürzel")))
    out = dict(_MAP_RX.findall(paragraph))
    assert out, "the §3 legend no longer maps a single shorthand to a file"
    return out


def kit_dirs():
    """Every shipped kit — the directories that carry a constitution, taken from the tree."""
    import glob
    return sorted(os.path.dirname(os.path.dirname(path)) for path in
                  glob.glob(os.path.join(TEAM_KITS, "*", "constitution", "AGENTS.md")))


def kit_of_prefix(prefix):
    for kit in kit_dirs():
        if os.path.basename(kit).startswith(prefix):
            return kit
    return None


_POINTER_RX = re.compile(r"^(?:([a-z]{3})/)?([A-Za-z][A-Za-z-]*)(?::(.*))?$")


class Pointer(object):
    """One `kit/shorthand:§anchor,§anchor` entry of a source cell."""

    def __init__(self, raw, prefix, shorthand, anchors):
        self.raw, self.prefix, self.shorthand, self.anchors = raw, prefix, shorthand, anchors

    def anchor_paths(self):
        """The anchors this pointer carries, without the marker."""
        return [token[len(ANCHOR_MARK):] for token in self.anchors or []
                if token.startswith(ANCHOR_MARK)]

    def unanchored_tokens(self):
        """Locator tokens that are not anchors — a line number is the case this exists for."""
        return [token for token in self.anchors or [] if not token.startswith(ANCHOR_MARK)]

    def targets(self):
        """[(kit dir, absolute path, shipped)] — the files this pointer claims the rule stands in.

        WHICH KITS is not a list anywhere: it is the set of kits that SHIP the declared file,
        narrowed by an explicit `dev/`/`off/`/`res/` prefix. The old legend answered it with three
        hand-written groups, and the one shorthand two readers disagreed about (`audit`, which every
        kit ships) is exactly where a hand-written group had gone stale.
        """
        relative = source_files().get(self.shorthand)
        if relative is None:
            return None
        kits = [kit_of_prefix(self.prefix)] if self.prefix else kit_dirs()
        out = []
        for kit in kits:
            if kit is None:
                continue
            path = os.path.join(kit, relative.replace("/", os.sep))
            shipped = os.path.isfile(path)
            if shipped or self.prefix:
                out.append((kit, path, shipped))
        return out


def pointers(sources):
    """[Pointer] for one source cell. A part that does not parse is returned with anchors None."""
    out = []
    for part in [part.strip() for part in sources.split(";") if part.strip()]:
        match = _POINTER_RX.match(part)
        if not match:
            out.append(Pointer(part, None, None, None))
            continue
        locator = match.group(3)
        anchors = None
        if locator is not None:
            anchors = [token.strip() for token in locator.split(",") if token.strip()]
        out.append(Pointer(part, match.group(1), match.group(2), anchors))
    return out
