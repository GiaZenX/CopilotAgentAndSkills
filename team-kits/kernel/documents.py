"""Applying a role's STAGED PROPOSAL to a kit document -- the writer the constitutions promised.

THE DEAD END THIS EXISTS TO END (BUG-0071, and P4-12 before it). Every kit ships documents into
`templates/project_memory/` that are prose and configuration rather than typed items -- and every
constitution's §6 assigns their CONTENT to a role. After the install nobody can write them: no
kernel path builder names such a file (`layout.is_project_document`), and `gate_write_scope`
refuses every tool write under the state directory. Measured live on 2026-08-29 in the user's real
office project: FOUR TIMES IN ONE DAY a specialist worked out the content, could only put it in
`staging/`, and the USER hand-copied it into the target file with a text editor.

WHY ONE GENERIC ROUTE AND NOT A COMMAND PER DOCUMENT, decided in the round with the numbers that
decided it (BUG-0071 AC-3). The office PM proposed both shapes. Measured 2026-08-29 against the
SHIPPED kits by running `layout.is_project_document` + `layout.partial_writers` over all three
template trees: of 22 kit documents (the research kit's KaTeX assets left out) EIGHTEEN had no
writer at all -- not the four the report named. Office adds `marketing_plan.yaml` and
`product_catalog.yaml`, research ships `literature.yaml`, `methodology.yaml`,
`research_guidelines.yaml` and `fzulg_documentation.yaml`, and every kit has `README.md` and
`product/masterplan.md`. Two more facts settled it:

  * A per-document command has to know the document's SHAPE, and the shapes do not rhyme:
    `master_data.yaml` carries two nested lists under `categories:` plus `counterparties:`,
    `content_guidelines.yaml` is mostly SCALARS (`tone`, `seo.title_pattern`) that an "add-x"
    command cannot fill at all, `compliance_register.yaml` is one list, `business_profile.yaml` is
    nested mappings. That is four commands with four hardcoded field lists -- and the field lists
    would already be wrong: the user's REAL `master_data.yaml` carries `example_doc` and
    `vat_treatment_note` on every category, fields the shipped template's commented example does
    not have. A schema written here would have refused his own file.
  * P4-12's lesson is that the ENUMERATION is the defect. "Exactly two kernel commands write into
    kit documents" was a true sentence twice and produced this class twice. A third special case
    buys one document and leaves eleven.

So the mechanism is the one operation the user was performing BY HAND, with the kernel doing the
writing and the user approving it: a role stages the document AS IT SHOULD STAND, the kernel says
what that WOULD change, the user approves exactly those bytes, and the kernel copies them in.

WHAT KEEPS IT FROM BEING A BLANK CHEQUE -- all of it is refusal, none of it is trust:
  * ADDITIONS ONLY. Every value the document has now must still be there, unchanged, in the
    proposal (`compare`). A removed key, a dropped list entry, a rewritten scalar: refused. What is
    allowed is a new key, a new list entry, and filling a value that is empty today. Amending what
    is already there stays the user's own edit, exactly as `filing.apply` refuses to edit a rule.
  * NO COMMENT MAY DISAPPEAR. These documents carry their field list, their defaults and their
    reasons in comments, and nothing else in the project rewrites them. The structural comparison
    cannot see prose, so the comment lines are compared as a multiset (`_comment_lines`).
  * NO DUPLICATES. A list entry equal to one already in the list is refused -- an append the user
    approved twice would otherwise sit twice in the file.
  * THE USER'S APPROVAL BINDS THE BYTES. The manifest carries the hash of the document as it stands
    and of the proposal, so an approval covers exactly one before-and-after. When either file moves
    the approval stops matching -- which is also what stops the same approval applying twice: after
    the write the document hashes to `proposed`, not to `base`.
  * THE WRITE IS READ BACK, parsed, and compared to what was approved; a deviation restores the
    original bytes. Same doctrine as `presets.record_preset` and `filing.apply`.

WHAT IT DELIBERATELY DOES NOT DO:
  * it writes no document it cannot COMPARE. Both sides must parse as a YAML mapping, so the eight
    prose documents of the same measurement -- three `README.md`, three `product/masterplan.md`,
    the research kit's two report templates -- keep having no writer, and the entry gate's rule
    that the masterplan is written once, before the install, stands unchanged. `accepts` is that
    line, and it is drawn by what the comparison NEEDS rather than by a suffix.
  * it never creates a document. A file the project does not have is an installation question, not
    a proposal.
  * it does not touch canonical state: `layout.is_project_document` is the gate on the target, so
    an item, an approval record or the index is refused here exactly as it is everywhere else.
"""
from __future__ import annotations

import collections
import os

import yaml

from . import approvals, layout
from .hashing import document_content_hash
from .staging import contained_child, staging_dir
from .state import STAGING_DIRNAME, ProjectState, StateError

# The APR kind that authorises this operation, and the command that spends it. One name, several
# readers: the vocabulary, the manifest builder, the refusals and the CLI.
KIND = "document_proposal"
COMMAND = "apply-proposal"

# WHAT THIS COMMAND WRITES, in the words the write-scope refusal and the session briefing print. It
# is not a field name because this writer owns no single field -- what it owns is the DIFFERENCE
# between the document and a proposal, and that difference is bounded by `compare` below.
WRITES = "what a staged proposal ADDS (never a change, never a removal)"


class DocumentError(StateError):
    """A proposal this kernel will not apply -- the message carries the remedy."""


def read_text(path: str) -> str:
    """The file exactly as it stands: no newline translation, no BOM stripped.

    Deliberately NOT `filing.read_text`, and the difference is the whole job here. That reader opens
    with `utf-8-sig` because it EDITS one line of a file and puts the rest back; this command copies
    a proposal's bytes into the document, so a reader that silently dropped a byte-order mark would
    write a file that differs from the one the user approved -- and the read-back check compares
    against exactly that text. `yaml.safe_load` handles a leading BOM itself, so parsing loses
    nothing by keeping it.
    """
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def parsed(text: str, what: str):
    """`text` as the mapping this command compares, or a refusal naming `what`."""
    try:
        document = yaml.safe_load(text)
    except Exception as exc:                            # noqa: BLE001 -- any parse failure is one
        raise DocumentError(
            "%s could not be parsed as YAML (%s) -- refused, nothing was changed. Remedy: fix the "
            "file and ask again; this command compares the two documents structurally and cannot "
            "compare one it cannot read." % (what, exc)) from None
    if document is None:
        document = {}
    if not isinstance(document, dict):
        raise DocumentError(
            "%s is not a YAML mapping, and this command only writes documents it can compare "
            "key by key -- refused, nothing was changed. Remedy: prose documents (the masterplan, "
            "a README) have no writer after the install; report that as the gap it is." % what)
    return document


def accepts(state_root: str, relative: str) -> bool:
    """Would this command write that path? The predicate `DOCUMENT_WRITES` declares as `applies`.

    WHAT IT IS FOR: the route a gate NAMES must be one this command would walk. A gate that offered
    `apply-proposal` for the masterplan would send a role at a refusal, which is BUG-0041's failure
    form pointed the other way, so the predicate reads the FILE -- "can this be compared" is a fact
    about the file, not about its name.

    IT IS THE CONJUNCTION OF THE COMMAND'S OWN REFUSALS AND NOT A SECOND POLICY, but it is not one
    call either: `document_path` refuses the position, the document class and the absence with a
    message each, and `parsed` (through `change_plan`) refuses the shape with the parse error in
    it. This asks all of them and answers yes or no. Where the two can differ is a document that is
    a kit document and does not parse: this says no, the command starts and then refuses at the
    parse -- an unusable document reported by name, never a write.
    """
    position = approvals.filed_position(relative)
    if not approvals.is_project_position(position):
        return False
    if not layout.is_project_document(state_root, position):
        return False
    path = os.path.join(state_root, *position.split("/"))
    if not os.path.isfile(path):
        return False
    try:
        parsed(read_text(path), position)
    except (DocumentError, OSError, UnicodeDecodeError):
        return False
    return True


# THE PART OF A KIT DOCUMENT THIS COMMAND WRITES, declared where the writing happens -- the same
# contract `presets.DOCUMENT_WRITES` and `filing.DOCUMENT_WRITES` declare, read by
# `kernel.layout.partial_writers` so the write-scope gate's refusal can name the route.
#
# `document` IS `layout.ANY_DOCUMENT` AND NOT A LIST OF FILES, which is the module docstring's
# decision put into the one place that would otherwise carry the enumeration. `applies` is what
# keeps that from becoming a promise the command does not keep: it is `accepts` -- the same
# predicate `document_path` refuses on -- so the route a gate names and the route this command
# walks are one answer. It stands here, below that predicate, because it names it.
DOCUMENT_WRITES = ({"document": layout.ANY_DOCUMENT, "applies": accepts,
                    "field": WRITES, "command": COMMAND},)


def document_path(state: ProjectState, relative: str) -> str:
    """The kit document a proposal targets, refused unless this command may write it.

    Every refusal names WHICH of the reasons applies, because they need different remedies: a path
    that is not a place in this project is a typo, canonical state is the kernel's own and always
    will be, and a document this kernel cannot compare is an infrastructure gap to report.
    """
    position = approvals.filed_position(relative)
    if not approvals.is_project_position(position):
        raise DocumentError(
            "%r does not name a document inside this project's state directory (an absolute path, "
            "a climb out of it, or a name carrying control characters) -- refused. Remedy: name it "
            "relative to the state directory, e.g. `--kit-document master_data.yaml`."
            % str(relative or ""))
    if not layout.is_project_document(state.root, position):
        raise DocumentError(
            "%s is not a kit DOCUMENT: it is canonical state, machinery, or the proposal area, and "
            "the kernel is the only writer of those -- refused. Remedy: a typed item is written "
            "with `capture`/`update`; this command writes the prose-and-configuration documents a "
            "kit ships, which have no other writer after the install." % position)
    path = os.path.join(state.root, *position.split("/"))
    if not os.path.isfile(path):
        raise DocumentError(
            "%s does not exist in this project, and this command never CREATES a document -- "
            "refused. Remedy: a missing kit document is an installation gap; report it and name "
            "the file." % position)
    return path


def proposal_path(state: ProjectState, relative: str) -> str:
    """The staged file a proposal names: `staging/<key>/<name>`, and nothing else.

    THE PROPOSAL AREA IS THE ONE PLACE A ROLE MAY WRITE (spec II.4), so it is the one place a
    proposal may come from: a command that read any path would let a role hand the kernel a file
    it wrote somewhere the gates never saw. The two segments go through `staging.contained_child`,
    the same chokepoint every freeze parameter passes and for the same measured reason -- a `..`
    there composes a path outside the state directory.
    """
    position = approvals.filed_position(relative)
    parts = [part for part in position.split("/") if part]
    if (not approvals.is_project_position(position) or len(parts) != 3
            or parts[0].lower() != STAGING_DIRNAME):
        raise DocumentError(
            "%r is not a staged proposal. A proposal is a file in the task's own proposal area, "
            "named as `%s/<TSK-ID>/<name>` relative to the state directory -- refused. Remedy: "
            "stage the document as it should stand, then name it, e.g. `--proposal "
            "%s/TSK-0007/master_data.yaml`." % (str(relative or ""), STAGING_DIRNAME,
                                                STAGING_DIRNAME))
    path = contained_child(staging_dir(state, parts[1]), parts[2], "staged proposal")
    if not os.path.isfile(path):
        raise DocumentError(
            "the staged proposal %s does not exist -- refused, nothing was changed. Remedy: stage "
            "the document as it should stand under that name first." % position)
    return path


# -- what a proposal WOULD do ---------------------------------------------------------------

def _empty(value) -> bool:
    """Is this the "not answered yet" the shipped templates write -- `""`, `null`, `[]`, `{}`?

    The kit documents ship every field pre-declared and empty (`tone: ""`, `register: []`,
    `kleinunternehmer: null`), so FILLING one is the ordinary case this command exists for, and it
    is an addition rather than a change: nothing that was said is being unsaid.
    """
    return value is None or value == "" or value == [] or value == {}


def _where(path: str, key) -> str:
    return "%s.%s" % (path, key) if path else str(key)


def _shown(value) -> str:
    """A filled value as the user reads it in the approval question.

    A string as itself -- quoting it would put two layers of punctuation into a sentence a
    non-technical person has to judge -- and anything else through the dumper, inline, because a
    mapping or a list has no reading a human agrees on otherwise. The LENGTH is not bounded here:
    `approvals.document_proposal_subject_manifest` folds every descriptor to one line of the same
    bound, so a second limit here would be a second answer to how long the card may be.
    """
    if isinstance(value, str):
        return value
    return yaml.safe_dump(value, default_flow_style=True, allow_unicode=True,
                          sort_keys=False).strip().rstrip("\n")


def _duplicates(entries: list) -> list:
    """The entries of one list that appear in it more than once, as their rendered positions."""
    seen, found = [], []
    for index, entry in enumerate(entries):
        if any(entry == earlier for earlier in seen):
            found.append(index)
        seen.append(entry)
    return found


def _subsequence_extras(current: list, proposed: list):
    """The entries `proposed` adds to `current`, or None when `current` is not kept whole.

    A SUBSEQUENCE and not a prefix: a category inserted into an alphabetically sorted list is an
    addition, and demanding that new entries go last would refuse the ordinary editing move. Because
    duplicates inside the proposed list are refused before this runs, every entry is distinct and
    the greedy match below is the only match there is.
    """
    position, extras = 0, []
    for entry in proposed:
        if position < len(current) and entry == current[position]:
            position += 1
        else:
            extras.append(entry)
    return extras if position == len(current) else None


# ONE CHANGE, in the three readings it needs: WHERE it is (`path`, which `_skeleton` blanks a
# filled value by), WHAT it is (`kind`, and `fill` is the only one that reshapes a line), and what
# the USER reads (`text`, German, because it lands inside an approval card -- BUG-0073).
Change = collections.namedtuple("Change", "path kind text")


def compare(current, proposed, path: str = "") -> list:
    """What `proposed` ADDS to `current`, or a refusal naming the place it would take something away.

    THE DEFINITION OF "ADDS", and it is the whole safety of this command: for every value the
    document holds today there must be a value in the proposal that keeps it -- the same scalar, a
    mapping that keeps every key, a list that keeps every entry in order. Everything else is a
    change or a removal, and neither is this command's business.

    WHAT IT CANNOT SEE IS EVERYTHING THAT IS NOT DATA -- a comment, the order of two keys, the way
    a line is set. That is not a caveat here but a division of labour: `_skeleton` compares exactly
    the complement of this, and `change_plan` runs both. Neither alone keeps the promise the
    approval question makes.

    The descriptors it returns are what the USER reads in the approval question, so they name the
    PLACE and the amount and never the value: a value belongs to the file the question names, and a
    question that quoted them would be a summary of a document rather than a binding on it
    (`tools/test_kernel.py::test_a_proposal_that_changes_or_drops_anything_is_refused`).
    """
    if isinstance(current, dict) and isinstance(proposed, dict):
        changes = []
        for key in current:
            if key not in proposed:
                raise DocumentError(
                    "the proposal drops `%s`, and this command only ADDS -- refused, nothing was "
                    "changed. Remedy: stage the document as it should stand INCLUDING everything "
                    "it holds today; removing something is an edit the user makes themselves."
                    % _where(path, key))
            changes += compare(current[key], proposed[key], _where(path, key))
        # A NEW KEY SHOWS ITS VALUE, for the reason a FILL does (see below): both are wholly new
        # prose entering a document that roles read, and `claims_policy: neu` names a place while
        # the sentence that arrives with it decides what the next reader does.
        changes += [Change(_where(path, key), "new",
                           "%s: neu, Wert %s" % (_where(path, key), _shown(proposed[key])))
                    for key in proposed if key not in current]
        return changes
    if isinstance(current, list) and isinstance(proposed, list):
        duplicated = _duplicates(proposed)
        if duplicated:
            raise DocumentError(
                "the proposal puts the same entry into `%s` twice (position %s) -- refused, "
                "nothing was changed. Remedy: one entry per thing; a list carrying one thing twice "
                "is one nobody can amend by naming it."
                % (path or "the document", ", ".join(str(one + 1) for one in duplicated)))
        extras = _subsequence_extras(current, proposed)
        if extras is None:
            raise DocumentError(
                "the proposal does not keep every entry `%s` already holds -- an entry was "
                "removed, reordered around one, or rewritten. Refused, nothing was changed. "
                "Remedy: stage the list as it stands and ADD to it; changing an entry that is "
                "already filed is an edit the user makes themselves." % (path or "the document"))
        if not extras:
            return []
        # `fill` WHEN THE LIST WAS EMPTY, and that is not cosmetics: the kind is what tells
        # `_skeleton` a line may legitimately change shape, and answering `structure: []` means
        # writing `structure:` with the entries below it. A list that already HELD something grows
        # by added lines and its own line must stay exactly as it is.
        return [Change(path, "fill" if not current else "grow",
                       "%s: %d %s hinzu" % (path or "die Liste", len(extras),
                                            "Eintrag" if len(extras) == 1 else "Einträge"))]
    if current == proposed:
        return []
    if _empty(current):
        # THE VALUE IS SHOWN, and it is the twin of the comment channel (verifier finding B2, found
        # again one step over while measuring his probe): a field that was EMPTY turns into prose
        # entering a document roles read as instructions -- `tone:` governs how the product editor
        # writes -- and "tone: gefüllt" told the user a place and not a word. A FILL is the one
        # value that is wholly new, and it is bounded (the builder folds every descriptor), so it
        # can be shown. An entry ADDED to a list is not shown: it is one more record of a kind the
        # document already holds, and showing them all would put the file into the card.
        return [Change(path, "fill",
                       "%s: gefüllt mit %s" % (path or "das Dokument", _shown(proposed)))]
    raise DocumentError(
        "the proposal changes `%s`, which already carries a value, and this command only ADDS -- "
        "refused, nothing was changed. Remedy: leave what is filled as it is; correcting a value "
        "the project already recorded is an edit the user makes themselves."
        % (path or "the document"))


# WHAT A BLANKED VALUE READS AS in the skeleton below. One character no YAML document contains, so
# a document cannot spell its own way past the comparison.
_BLANK = "\x00"


def _composed(text: str, what: str):
    """The document as a NODE tree, which is what carries the position of every value.

    `yaml.compose` rather than `safe_load`, because the skeleton below needs to know WHERE in the
    text each value stands, and a loaded dict has thrown that away. Same refusal as `parsed` for a
    text this kernel cannot read at all.
    """
    try:
        return yaml.compose(_marked(text))
    except Exception as exc:                            # noqa: BLE001 -- any parse failure is one
        raise DocumentError(
            "%s could not be parsed as YAML (%s) -- refused, nothing was changed. Remedy: fix the "
            "file and ask again; this command compares the two documents structurally and cannot "
            "compare one it cannot read." % (what, exc)) from None


def _marked(text: str) -> str:
    """The text the parser's own marks are offsets into -- i.e. without a leading BOM.

    PyYAML strips a byte-order mark before it starts counting, so a skeleton built with the mark
    offsets against the UNstripped text would be shifted by one character for the whole file.
    The write path keeps the mark (`read_text`); this is only what the COMPARISON reads.
    """
    return text[1:] if text.startswith("﻿") else text


def _blanked_spans(node, fills, path="", key_position=False):
    """The character spans of every VALUE this comparison deliberately does not look at.

    THE LINE THIS DRAWS IS THE WHOLE POINT OF THE MODULE (verifier finding B1). `compare` above is
    STRUCTURAL -- it reads what a YAML parser sees -- and `apply` is BYTE-WISE. Everything in
    between (an inline comment, the order of two keys, the way a line is set) was seen by NEITHER,
    while the question the user signs promises that nothing existing changes and no comment is
    lost. Measured on the shipped `content_guidelines.yaml`: filling its five empty scalars deleted
    five inline comments (`tone: "" # e.g. "sachlich, praezise"`) and every check passed.

    So the comparison is turned around: the VALUES are blanked out -- `compare` is what judges
    those -- and everything that is left, keys included, comments included, blank lines included,
    has to survive line for line. What is blanked:

      * a value that stands on ONE line. It carries no comment (a `#` after it starts one, and that
        `#` is outside the value), so blanking it hides nothing a reader owns -- and it is what
        lets `markets: [DE]` become `markets: [DE, AT]` without the line reading as rewritten.
      * a value at a path the data comparison recorded as FILLED, however many lines it takes.
        That is the one place a line legitimately changes shape: `register: []` becoming a block
        list is the ordinary way to answer an unanswered field.

    A SPAN ENDS WHERE THE VALUE ENDS, and that sentence is `_value_end`'s and not this function's:
    the marks a parser hands back run to the NEXT TOKEN, so the raw end of a block collection lies
    below the comments that follow the field. Trimming it there is what makes the paragraph above
    true -- a filled list keeps its commented examples, because they are outside the blanked span
    once it has been cut back. It was NOT true while this docstring already said so: measured over
    the shipped documents, the natural fill of 9 of 9 empty lists was refused.

    KEYS ARE NEVER BLANKED, in any position: a renamed key is a removal plus an addition to
    `compare`, and it has to read as a changed line here too.
    """
    spans = []
    if node is None:
        return spans
    blankable = not key_position and (
        path in fills or node.start_mark.line == node.end_mark.line)
    if blankable:
        return [(node.start_mark.index, node.end_mark.index)]
    if isinstance(node, yaml.MappingNode):
        for key_node, value_node in node.value:
            spans += _blanked_spans(key_node, fills, path, key_position=True)
            spans += _blanked_spans(
                value_node, fills,
                _where(path, key_node.value) if isinstance(key_node, yaml.ScalarNode) else path)
    elif isinstance(node, yaml.SequenceNode):
        for item in node.value:
            spans += _blanked_spans(item, fills, path)
    return spans


def _value_end(text: str, start: int, end: int) -> int:
    """Where a value's span REALLY ends: after the last line the value occupies.

    THE DEFECT THIS EXISTS FOR, measured by the verifier over every shipped kit document: PyYAML's
    `end_mark` of a block collection runs to the NEXT TOKEN, so it reaches across the comment lines
    standing below the field. Blanking that whole span swallowed those comments out of the AFTER
    skeleton, `_first_line_lost` reported them as lost, and the natural fill of an empty list --
    entries directly under the key, which is where every template's own commented example shows
    them -- was REFUSED in 9 of 9 lists across five documents, `master_data.yaml`'s three included.
    That is the case this whole round exists for, so the fix is fail-closed and impassable at once:
    the BUG-0041 dead-end form, one layer in.

    So the span is cut back to the last line inside it that carries something other than a comment
    or nothing at all. Those lines then stand in BOTH skeletons and are compared instead of
    swallowed -- which is what `_skeleton`'s own contract says about a filled list keeping its
    commented examples.

    ONE OVER-REPORT, stated rather than hidden: a line INSIDE a filled block scalar that begins
    with `#` is content, not a comment, and this trims it out of the span like one -- so it stays
    visible and is reported as an added comment. That errs toward showing the user more of what
    lands, which is the direction this module errs in everywhere.
    """
    lines = text[start:end].splitlines(keepends=True)
    while lines and (not lines[-1].strip() or lines[-1].lstrip().startswith("#")):
        lines.pop()
    if not lines:
        return end
    return start + len("".join(lines).rstrip("\r\n"))


def _reading(line: str) -> str:
    """One skeleton line as it is COMPARED: the value gone, runs of whitespace collapsed.

    WHY WHITESPACE IS NOT COMPARED, and it is the one thing this reader deliberately gives up: a
    value that grows moves the comment column of its own line, and answering `structure: []` with a
    block list moves the value to the NEXT line entirely. Both are the ordinary shape of filling in
    a template field, and a byte-exact line comparison refuses them while nothing has been lost.
    What survives the collapse is every WORD and its ORDER -- which is what a comment is, and what
    a key is. Indentation carries meaning in YAML, and a changed one changes the DATA, so `compare`
    is what refuses that, not this.
    """
    return " ".join(line.replace(_BLANK, " ").split())


def _skeleton(text: str, fills, what: str):
    """The document's lines with every value blanked -- everything a YAML parser does NOT see.

    Two documents whose skeletons agree line for line differ ONLY in values, and values are
    `compare`'s business. What holds this to the promise the approval question makes is
    `test_nothing_the_yaml_parser_cannot_see_may_change_either` in `tools/test_kernel.py`, and the
    floor under it is `test_the_ordinary_ways_a_document_grows_are_not_refused` -- each on ONE
    line, because a name broken across two is one nobody can copy or resolve.

    Blank lines fall out: a line that reads as nothing carries nothing to lose, and keeping them
    would make re-spacing a paragraph a refusal.
    """
    marked = _marked(text)
    spans = sorted(_blanked_spans(_composed(text, what), set(fills)))
    out, position = [], 0
    for start, end in spans:
        if start < position:
            continue                    # a nested span already covered by its parent
        out.append(marked[position:start])
        out.append(_BLANK)
        position = _value_end(marked, start, end)
    out.append(marked[position:])
    return [line for line in ("".join(out)).splitlines() if _reading(line)]


def _comment_texts(lines):
    """Every comment a document carries, as a multiset -- inline and whole-line alike.

    READ OFF THE SKELETON, which is what makes one reader enough for both shapes: the values are
    already blanked there, so the first `#` of a line is a comment and never a character inside a
    value. `tone: … # e.g.` and a line that is nothing but a comment come back the same way.
    """
    found = collections.Counter()
    for line in lines:
        reading = _reading(line)
        if "#" in reading:
            found[reading[reading.index("#"):]] += 1
    return found


def _first_line_lost(before, after):
    """The first line of `before` that `after` does not carry, in order -- or None.

    A SUBSEQUENCE, not a set: a comment that MOVED is a comment that now documents something else,
    and a document whose keys were reordered is not the document the user read. Both come back
    here as a line that could not be matched in order.
    """
    readable = [_reading(line) for line in after]
    position = 0
    for line in before:
        wanted = _reading(line)
        found = next((index for index in range(position, len(readable))
                      if readable[index] == wanted), None)
        if found is None:
            return line
        position = found + 1
    return None


def _duplicate_key(node, path=""):
    """The first mapping key a document spells TWICE, or None.

    YAML resolves a duplicate key by keeping the LAST one, silently. So a proposal could carry the
    document's real `categories:` block and a second, emptier one below it: the parse `compare`
    judges would see only the second, the skeleton would read the first as still present, and the
    file the user opens afterwards would show both. Refused rather than resolved -- the one thing
    this command may not do is write a document that means something other than what it shows.
    """
    if isinstance(node, yaml.MappingNode):
        seen = set()
        for key_node, value_node in node.value:
            key = getattr(key_node, "value", None)
            if key in seen:
                return _where(path, key)
            seen.add(key)
            found = _duplicate_key(value_node, _where(path, key))
            if found:
                return found
    elif isinstance(node, yaml.SequenceNode):
        for item in node.value:
            found = _duplicate_key(item, path)
            if found:
                return found
    return None


def _owned_elsewhere(state: ProjectState, kit_document: str, changes):
    """(path, command) for the first change a NAMED partial writer owns -- or None.

    THE HOLE THIS CLOSES (verifier finding B4). `filing_plan.yaml` has two routes, and they do not
    ask the same question: `add-filing-rule` binds every field of the rule -- which documents, where
    they land, how they are named, how long they are kept -- and renders each of them in the card,
    because that rule decides where every FUTURE document of a class goes. Through this command the
    same rule arrives as "rules: 1 Eintrag hinzu". The verifier planted a catch-all
    (`archive/<a>/<b>/<c>`, `document_types: [alles]`) that takes `gate_filing`'s wall down for the
    whole level, and the user would have signed a count.

    So a change at a path a NAMED writer owns belongs to that writer. DERIVED from
    `layout.partial_writers`, which asks the writing modules themselves: the generic entry (this
    command) names no document, every other entry names one and the field it owns. A third such
    command is covered on the day it declares itself, and this function does not know one by name.

    NESTED PATHS COUNT: `rules` and `rules.0.path_template` are the same field to its owner, and a
    proposal that reached into it would be the same substitution one level down.
    """
    document = approvals.filed_position(kit_document)
    for entry in layout.partial_writers(document, state.root):
        field = str(entry.get("field") or "")
        if entry.get("command") == COMMAND or not field:
            continue
        for one in changes:
            if one.path == field or one.path.startswith(field + "."):
                return one.path, entry["command"]
    return None


def change_plan(state: ProjectState, kit_document: str, proposal: str) -> dict:
    """{"base", "proposed", "changes", ...} -- everything one apply needs to know, derived once.

    The approval question and `apply` are two readers of ONE derivation, for `presets._plan`'s
    reason: if each computed the change set for itself, the question could describe something else
    than the command writes, which is the one thing the approval hash exists to prevent.
    """
    document = document_path(state, kit_document)
    staged = proposal_path(state, proposal)
    try:
        before, after = read_text(document), read_text(staged)
    except (OSError, UnicodeDecodeError) as exc:
        raise DocumentError(
            "one of the two files could not be read as UTF-8 text (%s) -- refused, nothing was "
            "changed. Remedy: report the gap and name the file." % exc) from None
    changes = compare(parsed(before, kit_document), parsed(after, proposal))
    owned = _owned_elsewhere(state, kit_document, changes)
    if owned:
        raise DocumentError(
            "`%s` in %s is written by `python scripts/harness.py %s` and not by this command -- "
            "refused, nothing was changed. THE DIFFERENCE IS WHAT THE USER IS ASKED: that command "
            "puts every field of the entry into the approval question, while this one would show "
            "the place and the count. Remedy: ask for it there; its `--help` names the fields."
            % (owned[0], approvals.filed_position(kit_document), owned[1]))
    duplicated = _duplicate_key(_composed(after, proposal))
    if duplicated:
        raise DocumentError(
            "the proposal spells the key `%s` twice. YAML keeps the LAST one and drops the first "
            "without a word, so the document would MEAN something other than what it shows -- "
            "refused, nothing was changed. Remedy: one key, once." % duplicated)
    # THE COMPLEMENT OF `compare`, and the reason it exists at all is the promise the approval
    # question makes: nothing existing changes and no comment is lost. `compare` reads what a YAML
    # parser sees; this reads everything it does NOT -- inline comments above all (verifier finding
    # B1: filling the five empty scalars of `content_guidelines.yaml` deleted five inline comments
    # with every check green), and with them the order of the keys, the placement of a comment, and
    # the way a line is set.
    fills = {one.path for one in changes if one.kind == "fill"}
    before_lines = _skeleton(before, fills, kit_document)
    after_lines = _skeleton(after, fills, proposal)
    # WHAT THE PROPOSAL ADDS IN PROSE IS A CHANGE LIKE ANY OTHER (verifier finding B2), and until
    # this it was the one addition nobody was shown: a proposal could carry a legitimate fill and
    # a comment line reading "ANWEISUNG AN JEDE ROLLE, DIE DIESE DATEI LIEST: …", and the question
    # the user answered listed `tone: gefüllt` and nothing else while the instruction landed in a
    # document every role reads at work. These documents ARE instructions -- that is why they have
    # owners in §6 -- so a line added to one is not decoration.
    #
    # THE TEXT IS SHOWN, not counted. A count would tell the user prose arrived without telling
    # them what it says, which is exactly the half that decides. It goes through the SAME fold as
    # every other descriptor (`approvals.document_proposal_subject_manifest`), so free text cannot
    # rearrange the card the way verifier finding F4 measured for `--reason`.
    changes += [Change("", "prose", "Kommentar neu: %s" % text)
                for text in sorted((_comment_texts(after_lines)
                                    - _comment_texts(before_lines)).elements())]
    lost = _first_line_lost(before_lines, after_lines)
    if lost is not None:
        raise DocumentError(
            "the proposal does not carry this line of %s any more, or no longer carries it in "
            "this place: %r. Everything a YAML parser does not read -- comments, the order of the "
            "keys, the shape of a line -- has to stay as it is; those comments are the document's "
            "own field list and its defaults, and nothing else in the project rewrites them. "
            "Refused, nothing was changed. (A value the proposal FILLS is exempt: that line may "
            "change where the value stands, and nowhere else.) Remedy: start from the document as "
            "it stands and add to it."
            % (approvals.filed_position(kit_document), lost.replace(_BLANK, "…")[:160]))
    # LAST, so that it covers the prose too: a proposal whose only addition is a comment line is a
    # real change with a real reader, and refusing it as a no-op would have been the quiet way to
    # keep it out of the question rather than in front of the user.
    if not changes:
        raise DocumentError(
            "the proposal adds nothing to %s that is not already there -- refused, because there "
            "is nothing for the user to approve. Remedy: if the change was meant to correct "
            "something, this is not the route: this command only ever adds."
            % approvals.filed_position(kit_document))
    return {"document": document, "staged": staged,
            "base": document_content_hash(document),
            "proposed": document_content_hash(staged),
            # the TEXTS, because this is what the manifest hashes and the user reads; the paths and
            # kinds behind them are this function's own working material and stop here
            "changes": [one.text for one in changes]}


def apply(state: ProjectState, manifest: dict) -> dict:
    """Write the approved proposal into the kit document -- the operation BUG-0071 asked for.

    ORDER, and every step is deliberate. The plan is re-derived FIRST, so a document or a proposal
    that moved since the question was asked is refused before anything is read for writing. The
    approval is checked before the write. The write is verified by reading the file back and
    comparing it to the proposal's own text, with the original bytes restored on any deviation --
    `presets.record_preset`'s doctrine, and for its reason: a copy is a byte operation, and the only
    proof it produced the approved document is reading what is now there.

    RUNNING IT AGAINST THE DOCUMENT IT JUST WROTE DOES NOTHING, and the condition is part of the
    sentence (verifier finding B5). After the write the document hashes to the manifest's
    `proposed`, so the re-derived plan carries a different `base`, no live approval matches it, and
    `change_plan` finds nothing left to add. What that does NOT say is "single use": the approval
    binds two FASSUNGEN, not an event, so if the document is put back to the bytes it had -- by
    hand, by a revert -- the same approval covers writing the proposal again until its clock runs
    out (`approvals.LINE_APPROVAL_VALIDITY`, one hour).

    THAT IS THE READING `filing_correction` HAS BY DESIGN and the reason no marker was added here:
    a "used" flag would be one more piece of writable state deciding an enforcement question, which
    is the mistake the office ledger gate spent four rounds unlearning. What bounds it is the
    clock, and the fact that re-applying writes exactly the bytes the user already approved.
    """
    with state.lock:
        plan = change_plan(state, manifest["kit_document"], manifest["proposal"])
        # RE-DERIVED THROUGH THE BUILDER, not compared against the raw plan. The manifest the user
        # signed went through `document_proposal_subject_manifest`, which folds and bounds every
        # value it hashes -- so comparing a raw `changes` list against a folded one would differ
        # for any descriptor the fold touches (a path over its length bound is one), and the
        # command would refuse an approval that covers it perfectly. One normalisation, both sides.
        derived = approvals.document_proposal_subject_manifest(
            manifest["kit_document"], manifest["proposal"], plan["base"], plan["proposed"],
            plan["changes"], manifest.get("reason"))
        moved = [key for key in ("base", "proposed", "changes")
                 if derived[key] != manifest.get(key)]
        if moved or approvals.live_line_approval(state, KIND, manifest) is None:
            raise DocumentError(
                "no live user approval covers applying %s to %s%s -- nothing was changed. What it "
                "would do: %s. Remedy: ask for it first -- `python scripts/harness.py "
                "request-approval %s --kit-document %s --proposal %s` prints the question the "
                "kernel composed, the USER approves by answering it, and then this command writes "
                "exactly what they approved."
                % (manifest["proposal"], manifest["kit_document"],
                   " (the document or the proposal has changed since the question was asked: %s)"
                   % ", ".join(moved) if moved else "",
                   ", ".join(plan["changes"]), KIND,
                   manifest["kit_document"], manifest["proposal"]))
        before = read_text(plan["document"])
        after = read_text(plan["staged"])
        state._write_text_atomic(plan["document"], after)
        # AGAINST THE SIGNED HASH, not against the text this function just read. Two reasons, and
        # the second is the one that made this a hole rather than a style question. A parse-level
        # check would accept a file that means the same and reads differently, and the comments are
        # the half a parse cannot see at all -- so it has to be the bytes. And the bytes it has to
        # be are the ones the USER signed: `after` was read a line ago from a file the kernel lock
        # does not protect against an editor, so comparing the write against it would confirm
        # whatever was there at that moment. `proposed` is in the manifest the approval hashes.
        if document_content_hash(plan["document"]) != manifest["proposed"]:
            state._write_text_atomic(plan["document"], before)
            raise DocumentError(
                "writing the proposal into %s did not produce the document the user approved; the "
                "file was restored unchanged and nothing was applied. Remedy: report the gap and "
                "name the file." % manifest["kit_document"])
        return {"document": manifest["kit_document"], "changes": plan["changes"],
                "bytes": len(after.encode("utf-8"))}
