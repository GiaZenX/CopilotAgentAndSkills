"""The kanban board over the typed state -- `generated/board.html` (FR-0030).

WHY THE RENDERER IS IN THE KERNEL AND NOT A KIT SCRIPT THE KERNEL CALLS. Both were on the table
and the measurement decided it (TSK-0071 step 1, `docs/reviews/2026-08-16-tsk0071-measurements.md`):

  * every kernel call site that regenerates the index arrives in
    `state._regenerate_index_locked` -- capture, edit, transition, archive, the approval mint, the
    dispatch lifecycle, the freezes -- so a renderer called from there is refreshed by every state
    write that regenerates the index, with no second trigger to keep in sync. Two kernel writes did
    NOT regenerate and were fixed in the same round rather than excused (`approvals.revoke`, the
    lease-expiry release in `dispatch._validate_lease_locked`); what holds the pair together is
    `test_board.test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind`, which derives
    the writers from the package rather than trusting this sentence;
  * a kit script would have to be STARTED by the kernel, i.e. the kernel would execute a file
    living in the project's own `scripts/` -- a tree `gate_write_scope` does not protect the way it
    protects `.claude/` -- on every capture, transition and mint. That is code the state layer does
    not own, executed from inside it, and it would cost one interpreter start per state write;
  * a kit script would exist three times (one per kit) and would then owe the mirror rule, while
    this file ships once as part of the kernel every kit installs.

WHAT IT MAY NOT BECOME. The board is a REPORT: it is written under `generated/`, the directory
every kit's `.gitignore` excludes and the kernel rebuilds from the items, and it is a pure function
of the items it is handed, the type directories the project has, and the timestamp its caller hands
it. Nothing here reads a status it was not given and nothing here writes state.

DERIVED, NOT LISTED, in the two places a list would rot:
  * WHICH TYPES a kit has is read off the state directory it installed (`types_present`) -- the
    office kit ships no `research/active`, the research kit no `procedures/active`, and no per-kit
    type table exists to disagree with the tree;
  * WHICH COLUMNS a type has is its own automaton (`status_columns`), chain order first, so a
    changed chain moves the board with it.

A STATUS NO COLUMN CLAIMS IS NEVER DROPPED. It gets a column of its own and a warning ON THE PAGE
-- the only channel a report has, since stdout belongs to the command the state write was part of,
where `kernel.cli` prints that command's own paths and verdicts. The two directions are
`test_board.test_an_item_type_no_status_vocabulary_describes_still_appears_with_a_warning` and
`test_board.test_a_record_type_without_a_status_is_not_reported_as_a_defect`.
"""
from __future__ import annotations

import html
import os

from .backlog_types import ACTIVE_DIRS, AUTOMATA, status_values
from .lock import ext_path


# The report's name under `generated/`. One constant, because `kernel.state` composes the path with
# it and every reader of the board asks for the same file. `dashboard.html` is deliberately NOT this
# name: the dev kit's own `scripts/generate_dashboard.py` still writes that file, and two writers on
# one path would race on every state write.
FILENAME = "board.html"

# The column a corrupt item file lands in -- a file `state` could not parse has no status, but it is
# still an item somebody has to fix, and a board that omitted it would be reassuring about a state
# nobody could read.
UNREADABLE = "(unreadable)"

# ...and the column for an item that carries no status at all. For a record type (Evidence,
# Approvals, the frozen ARC/WFR/DSN) that is the contract; for a type with a status vocabulary it is
# a defect, and only the second case warns -- see the module docstring.
NO_STATUS = "(no status)"

# How much of ONE field value reaches the fold of a card -- a budget the flattener SPENDS as it
# walks, not a cut it makes afterwards (see `_Ink`). `report._clip` is the same idea for the session
# brief and is not imported here for a structural reason: `report` imports `state`, `state` imports
# this module, so a module-level import back into `report` would close the package's import graph
# into a cycle. This is a leaf on purpose.
VALUE_MAX_CHARS = 600

# How far a container inside a field value is unfolded before the fold just says "there is more
# here". The value is the depth the shipped item shapes actually use (a field holding a list of
# mappings, e.g. `acceptance_criteria`) plus one; the reason a bound exists AT ALL is termination,
# and that is spelled out at `_emit`.
VALUE_MAX_DEPTH = 3

# What stands where a container was not unfolded. Deliberately not the container's `repr`: a YAML
# alias graph re-expands under `str()` (see `_emit`).
#
# AND DELIBERATELY NOT THE BARE ELLIPSIS `_flat` APPENDS AT THE BUDGET CUT. While the two were the
# same string, a test could not tell "the depth bound marked a container" from "this value ran out
# of budget", and the one check that was supposed to carry the depth half was satisfied by the cut
# alone -- green with `str(value)` put back at the bound. Distinguishable is what makes
# `test_board.test_an_alias_bomb_cannot_stretch_a_state_write` able to fail.
NESTED_MARKER = "[…]"

# The card's face. Everything else about an item goes into the fold, so a new field appears there
# the day it ships instead of needing an edit here. The claim is measured from the RENDERED PAGE by
# `test_board.test_every_field_of_an_item_is_on_its_card_exactly_once` -- a check against this
# constant would only be this constant read twice.
FACE_FIELDS = ("id", "title", "status")


def status_columns(item_type: str) -> tuple:
    """The board columns of one type, in the order work moves through them.

    The type's OWN automaton: the chain first (that is the order a kanban board is about), then the
    side states it can fall into, then the terminals it ends in. A type without an automaton
    contributes the vocabulary `backlog_types.status_values` gives it, whose first value is its
    initial one; a type with no status at all contributes nothing, which is what makes it a record
    rather than a piece of living state.
    """
    automaton = AUTOMATA.get(item_type)
    if automaton is None:
        return tuple(status_values(item_type))
    ordered = list(automaton.chain)
    ordered += sorted(automaton.states - set(ordered) - automaton.terminals)
    ordered += sorted(automaton.terminals - set(ordered))
    return tuple(ordered)


def types_present(state) -> tuple:
    """Every item type THIS state has a home for -- the installed kit's types, read off its tree.

    The kits ship different `templates/project_memory/` trees, and that tree IS the answer: a kit
    that has no research questions ships no `research/active`. Asking the directory rather than a
    per-kit table is what keeps the board kit-appropriate without a second list of types to
    maintain (`test_board.test_each_kit_renders_the_types_its_own_template_ships`).
    """
    return tuple(item_type for item_type in sorted(ACTIVE_DIRS)
                 if os.path.isdir(ext_path(state.active_dir(item_type))))


class _Ink:
    """The character budget ONE field value may spend, and whether it ran out.

    A budget rather than a `text[:limit]` afterwards, because the expensive thing is BUILDING the
    text. Measured on an alias bomb (a 481-byte item file whose YAML aliases each double one level
    into the next): flattening it and cutting the result took 14.87 s per state write, while the
    index beside it stayed 142 bytes. With the budget the walk stops at `VALUE_MAX_CHARS`
    characters, so the work an item can cause is bounded by its own card
    (`test_board.test_an_alias_bomb_cannot_stretch_a_state_write`).
    """

    __slots__ = ("left", "cut")

    def __init__(self, limit: int):
        self.left, self.cut = limit, False

    def spend(self, text: str) -> str:
        """As much of `text` as the budget still affords, marking the budget when it is short."""
        if len(text) > self.left:
            text, self.cut = text[: max(self.left, 0)], True
        self.left -= len(text)
        return text

    @property
    def dry(self) -> bool:
        return self.left <= 0


def _emit(value, depth: int, out: list, ink: _Ink) -> None:
    """Append the pieces of `value` to `out`, within `ink` and within `VALUE_MAX_DEPTH`.

    `str()` on a nested list or mapping prints Python's own repr -- quotes, braces and all -- into a
    page a non-developer reads, which is how `acceptance_criteria` would arrive as
    `{'id': 'AC-1', ...}`. So containers are walked, and the walk is bounded in BOTH directions
    because a YAML file decides its own shape:

      * DEPTH -- a YAML anchor may point at its own container (`repro: &loop [step, *loop]`), which
        `yaml.safe_load` builds as a self-referential object. An unbounded walk raises
        RecursionError, and it does so INSIDE `state._regenerate_index_locked`, i.e. at the end of
        every state write. `test_board.test_a_self_referential_item_body_does_not_stop_the_state
        _write` carries it.
      * WIDTH -- below the depth bound, aliases still multiply: `yaml.safe_load` resolves them into
        SHARED objects, so a few hundred bytes of file describe a walk of millions of values.
        `_Ink` is the bound there, and it is a bound on the WALK rather than a cut afterwards.

    THE TWO ARE NOT INDEPENDENT, and saying they were is what let the depth half ship untested. At
    the depth bound the container contributes `NESTED_MARKER` and is NOT handed to `str()` -- and
    that is not a display choice, it is the other half of the same defence: `str()` re-expands the
    whole graph below it inside ONE call, which no character budget can interrupt. The budget
    bounds what is spent per step; the marker is what keeps a single step from being the whole
    graph. Measured in both directions by
    `test_board.test_an_alias_bomb_cannot_stretch_a_state_write`, whose bomb puts its LARGEST
    container exactly at the bound -- the round's report carries the numbers.
    """
    if ink.dry:
        ink.cut = True
        return
    if isinstance(value, (dict, list, tuple)):
        if depth >= VALUE_MAX_DEPTH:
            out.append(ink.spend(NESTED_MARKER))
            return
        is_map = isinstance(value, dict)
        for index, entry in enumerate(value.items() if is_map else value):
            if ink.dry:
                ink.cut = True
                return
            if index:
                out.append(ink.spend("; " if is_map else ", "))
            if is_map:
                out.append(ink.spend("%s: " % (entry[0],)))
                entry = entry[1]
            _emit(entry, depth + 1, out, ink)
        return
    out.append(ink.spend("" if value is None else str(value)))


def _flat(value) -> str:
    """A field value as ordinary text, containers included, bounded by `_Ink`."""
    out, ink = [], _Ink(VALUE_MAX_CHARS)
    _emit(value, 0, out, ink)
    text = "".join(out)
    return text.rstrip() + "…" if ink.cut else text


def _lines(value) -> list:
    """One display line per thing a field value holds.

    A field is not typed by any contract (`backlog_types.field_elements` says why), so every value
    shape has to render: a list becomes one line per element, a mapping one `key: value` line per
    entry, and anything else is one line. What sits INSIDE one of those goes through `_flat` on one
    line with it -- the item file stays the place to read the full structure.

    EACH LINE CARRIES ITS OWN BUDGET, and that is the one place this module lets a value grow with
    the item: a field holding 500 references is 500 lines. They are the field's own elements, so
    the growth is the state's, not the renderer's -- unlike the alias graph `_Ink` exists for,
    which is one value pretending to be a million.
    """
    if isinstance(value, dict):
        return ["%s: %s" % (key, _flat(inner)) for key, inner in value.items()]
    if isinstance(value, (list, tuple)):
        return [_flat(entry) for entry in value]
    return [_flat(value)]


def _column_of(row: dict) -> str:
    """Which column an index row belongs in -- its status, or one of the two named sentinels."""
    if row.get("corrupt"):
        return UNREADABLE
    status = row.get("status")
    return NO_STATUS if status is None or status == "" else str(status)


def _card(row: dict, body) -> tuple:
    """(one item as a `<details>`, what went wrong or None).

    Native `<details>`, no script: the page opens by double-click from a file manager, and an
    expander that needs JavaScript is one that does not expand when the browser blocks it.

    ONE ITEM MAY NOT COST THE WHOLE PAGE. The body comes out of a YAML file, so its shape is the
    file's decision, not this module's -- and this module runs at the end of every state write. An
    item whose value nothing here can render therefore becomes a card that SAYS so, named by its
    id, instead of an exception that reaches `capture`. That the state write survives it is
    `test_board.test_an_item_no_renderer_can_read_costs_its_own_card_and_nothing_else`.
    """
    item_id = str(row.get("id") or "")
    try:
        title = row.get("title")
        if not title and isinstance(body, dict):
            title = body.get("title")
        face_text = _flat(title)
        rows = []
        for key, value in (body or {}).items():
            if key in FACE_FIELDS:
                continue
            rows.append("<dt>%s</dt><dd>%s</dd>" % (
                html.escape(str(key)),
                "<br>".join(html.escape(line) for line in _lines(value)) or "<em>empty</em>"))
        fold = "<dl>%s</dl>" % "".join(rows) if rows else "<p class='empty'>no further fields</p>"
        problem = None
    except Exception as exc:                      # noqa: BLE001 -- see the docstring
        face_text, problem = "", "%s: %s" % (type(exc).__name__, exc)
        fold = '<p class="empty">this item could not be rendered (%s) — read the file itself</p>' % (
            html.escape(problem[:200]))
    face = '<summary><span class="id">%s</span> <span class="title">%s</span></summary>' % (
        html.escape(item_id), html.escape(face_text))
    return ('<details class="card%s" data-item="%s">%s%s</details>'
            % (" broken" if problem else "", html.escape(item_id, quote=True), face, fold),
            problem)


def _section(item_type: str, entries: list) -> tuple:
    """(html for one type's board, [warning, ...]) -- every entry of that type, in a column."""
    declared = status_columns(item_type)
    by_column: dict = {column: [] for column in declared}
    for row, body in entries:
        by_column.setdefault(_column_of(row), []).append((row, body))
    extra = sorted(column for column in by_column if column not in declared)
    terminals = getattr(AUTOMATA.get(item_type), "terminals", frozenset())

    warnings = []
    for column in extra:
        if column == UNREADABLE:
            warnings.append((item_type, "unreadable", "%d item file(s) could not be parsed"
                             % len(by_column[column])))
        elif column == NO_STATUS and declared:
            warnings.append((item_type, "missing-status",
                             "%d item(s) carry no status although %s declares %s"
                             % (len(by_column[column]), item_type, ", ".join(declared))))
        elif column != NO_STATUS:
            warnings.append((item_type, "unknown-status",
                             "status %r belongs to no column %s declares -- shown at the end"
                             % (column, item_type)))

    columns = []
    for column in list(declared) + extra:
        cards = sorted(by_column.get(column, []), key=lambda pair: str(pair[0].get("id") or ""))
        drawn = []
        for row, body in cards:
            card, problem = _card(row, body)
            drawn.append(card)
            if problem:
                # NAMED, not counted: the id is what a reader needs to open the file that broke
                warnings.append((item_type, "unrenderable",
                                 "%s could not be rendered (%s)"
                                 % (row.get("id") or "?", problem[:120])))
        columns.append(
            '<div class="column%s" data-status="%s" data-count="%d"><h3>%s '
            '<span class="count">%d</span></h3>%s</div>'
            % (" terminal" if column in terminals else "",
               html.escape(str(column), quote=True), len(drawn),
               html.escape(str(column)), len(drawn), "".join(drawn)))
    return ('<section class="type" id="type-%s" data-type="%s" data-items="%d">'
            '<h2>%s <span class="count">%d</span></h2><div class="board">%s</div></section>'
            % (html.escape(item_type, quote=True), html.escape(item_type, quote=True), len(entries),
               html.escape(item_type), len(entries), "".join(columns)), warnings)


_STYLE = """
:root { color-scheme: light dark; }
body { font: 14px/1.45 system-ui, sans-serif; margin: 0 0 3rem; padding: 1rem 1.25rem; }
h1 { font-size: 1.35rem; margin: 0 0 .25rem; }
h2 { font-size: 1.05rem; margin: 1.75rem 0 .5rem; }
h3 { font-size: .78rem; letter-spacing: .04em; text-transform: uppercase; margin: 0 0 .5rem;
     opacity: .75; }
.meta { margin: 0 0 1rem; opacity: .75; }
nav a { margin-right: .6rem; white-space: nowrap; }
.board { display: flex; gap: .6rem; overflow-x: auto; align-items: flex-start; padding-bottom: .4rem; }
.column { flex: 0 0 15rem; border: 1px solid rgba(128,128,128,.35); border-radius: .4rem;
          padding: .5rem; }
.column.terminal { opacity: .6; }
.count { opacity: .6; font-weight: normal; }
.card { border: 1px solid rgba(128,128,128,.3); border-radius: .3rem; padding: .35rem .45rem;
        margin-bottom: .4rem; background: rgba(128,128,128,.07); }
.card summary { cursor: pointer; }
.card .id { font-family: ui-monospace, monospace; font-size: .8rem; opacity: .7; }
.card dl { display: grid; grid-template-columns: max-content 1fr; gap: .15rem .5rem;
           margin: .5rem 0 .1rem; font-size: .85rem; }
.card dt { font-weight: 600; opacity: .7; }
.card dd { margin: 0; overflow-wrap: anywhere; }
.warnings { border: 1px solid #c93; border-radius: .4rem; padding: .6rem .6rem .6rem 1.6rem;
            margin: 0 0 1rem; }
.empty { opacity: .6; font-style: italic; margin: .4rem 0 .1rem; }
"""


def render(state, entries, generated_at: str) -> str:
    """The whole board as one dependency-free HTML page.

    `entries` are (index row, item body or None) pairs -- the rows the caller has just written into
    `generated/index.yaml` and the bodies it read on the way, so the board reports exactly the state
    the index reports and costs no second parse of the store.

    A type is on the page when the state has a home for it OR an entry names it: the first is the
    kit's own set of types, the second is what makes an item impossible to lose, whatever type it
    turns out to carry.
    """
    grouped: dict = {}
    for row, body in entries:
        grouped.setdefault(str(row.get("type") or "?"), []).append((row, body))
    types = sorted(set(types_present(state)) | set(grouped))

    sections, warnings = [], []
    for item_type in types:
        section, found = _section(item_type, grouped.get(item_type, []))
        sections.append(section)
        warnings += found

    banner = ""
    if warnings:
        banner = '<ul class="warnings">%s</ul>' % "".join(
            '<li data-warning="%s" data-type="%s">%s: %s</li>'
            % (html.escape(kind, quote=True), html.escape(item_type, quote=True),
               html.escape(item_type), html.escape(detail))
            for item_type, kind, detail in warnings)
    nav = '<nav>%s</nav>' % "".join(
        '<a href="#type-%s">%s (%d)</a>' % (html.escape(item_type, quote=True),
                                            html.escape(item_type), len(grouped.get(item_type, [])))
        for item_type in types)
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Backlog board</title>\n<style>%s</style>\n</head>\n<body>\n"
        '<header><h1>Backlog board</h1>\n'
        '<p class="meta">Rebuilt by the state kernel together with <code>index.yaml</code>, on '
        'every state write the kernel makes — <time data-generated-at="%s">%s</time>. A rebuild '
        "that fails says so on the error output of the command that triggered it and leaves this "
        "page as it was, so compare that stamp with what you expect. It reports, it never sets: "
        "this page is regenerated output and holds no state of its own. Shown is every item in a "
        "type's <code>active</code> directory; an archived item is not on this board.</p></header>\n"
        "%s%s\n%s\n</body>\n</html>\n"
        % (_STYLE, html.escape(str(generated_at), quote=True), html.escape(str(generated_at)),
           banner, nav, "\n".join(sections)))
