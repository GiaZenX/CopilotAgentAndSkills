"""The kanban board over the typed state -- `generated/board.html` (FR-0030, FR-0053).

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
of the items it is handed, the type directories the project has, the archive it counts, and the
timestamp its caller hands it. Nothing here reads a status it was not given and nothing here writes
state.

THREE VIEWS, ONE FILE, AND THE ONLY SCRIPT IS THE ONE THAT SWITCHES BETWEEN THEM (FR-0053). The
page carries a Board tab (columns per type, as FR-0030 shipped it) and the two hierarchical backlog
views `backlog_tree` derives. Which view is showing is DOM state -- the `hidden` attribute on the
other two -- so a reader of the page, and a test, can see it without a browser; the inline script
moves that attribute and does nothing else. It fetches nothing, loads nothing, stores nothing and
writes no state; the whole of it is `_SCRIPT` below, a constant with no item content interpolated
into it, which is what makes a `</script>` inside a hostile title impossible rather than escaped
(`test_board.test_the_page_script_carries_no_item_content_at_all`).

WITH SCRIPTING OFF the page falls back to what FR-0030 shipped: `_NOSCRIPT_STYLE` un-hides every
view and every item detail, so the file becomes one long page that shows everything. What it
prevents is not an EMPTY page -- the board view carries no `hidden` and would still stand there
with every card on it -- but a board with a dead tab strip, two views out of reach and cards whose
records never open. That is a CSS fallback in the page, not a claim about a browser this suite
runs: the round's report (`docs/reviews/2026-08-21-tsk0079-measurements.md`) carries the browser
measurement, this file carries the rule.

DERIVED, NOT LISTED, in the places a list would rot:
  * WHICH TYPES a kit has is read off the state directory it installed (`types_present`) -- the
    office kit ships no `research/active`, the research kit no `procedures/active`, and no per-kit
    type table exists to disagree with the tree;
  * WHICH COLUMNS a type has is its own automaton (`status_columns`), chain order first, so a
    changed chain moves the board with it;
  * WHICH ITEM a card links to is every id the item's own fields name (`_linked`), and which of
    those becomes a button is whether this board HAS that item -- not a list of reference fields.

A STATUS NO COLUMN CLAIMS IS NEVER DROPPED. It gets a column of its own and a warning ON THE PAGE
-- the only channel a report has, since stdout belongs to the command the state write was part of,
where `kernel.cli` prints that command's own paths and verdicts. The two directions are
`test_board.test_an_item_type_no_status_vocabulary_describes_still_appears_with_a_warning` and
`test_board.test_a_record_type_without_a_status_is_not_reported_as_a_defect`. The tree views carry
the same property through `backlog_tree`: an item no link can place is shown under Unassigned with
the reason, never dropped.
"""
from __future__ import annotations

import html
import os
import re

from . import backlog_tree
from .backlog_types import ACTIVE_DIRS, AUTOMATA, parse_id, status_values
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

# How much of ONE field value reaches the detail of an item -- a budget the flattener SPENDS as it
# walks, not a cut it makes afterwards (see `_Ink`). `report._clip` is the same idea for the session
# brief and is not imported here for a structural reason: `report` imports `state`, `state` imports
# this module, so a module-level import back into `report` would close the package's import graph
# into a cycle. This is a leaf on purpose.
VALUE_MAX_CHARS = 600

# How far a container inside a field value is unfolded before the detail just says "there is more
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

# What an item shows OUTSIDE its field list: on the card, on a tree node and in the header of its
# detail. Everything else about an item goes into the detail's field list, so a new field appears
# there the day it ships instead of needing an edit here. The claim is measured from the RENDERED
# PAGE by `test_board.test_every_field_of_an_item_is_in_its_detail_exactly_once` -- a check against
# this constant would only be this constant read twice.
HEADER_FIELDS = ("id", "title", "status")

# An id, as `backlog_types.parse_id` spells one, found inside a rendered field value. The pattern is
# the one place a reference is RECOGNISED; whether it becomes a button is a second question
# (`_linked`), and the answer is whether this board holds that item -- never a list of fields that
# are allowed to point somewhere.
_REFERENCE = re.compile(r"\b([A-Z]{2,4}-\d{4,})\b")

# ...and the same shape at the END of a value the budget cut short. A cut falls wherever
# `VALUE_MAX_CHARS` runs out, which can be INSIDE an id: an item naming `PR-000199999` was rendered
# as `PR-0001…`, and `_linked` then offered a button to PR-0001 -- a reference to a DIFFERENT item,
# invented by a display bound. Every trailing id-shaped run is therefore dropped at a cut, because
# nothing can tell a complete id at the boundary from a truncated one. The trees never read this
# text (`backlog_tree.parents_of` reads the item body), so only the record's own prose is affected.
# `test_board.test_a_value_cut_short_never_offers_a_reference_the_item_does_not_name`.
_CUT_REFERENCE = re.compile(r"[A-Z]{2,4}-\d+$")


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


def archived_counts(state) -> dict:
    """{type: how many items of it are archived} -- the number the tab strip carries (FR-0053).

    WHAT COUNTS AS AN ARCHIVED ITEM is what `state.archive_path` writes:
    `archive/<TYPE>/<year>/<ID>.yaml`. Only those subtrees are read, one per type, so what this
    costs at the end of every state write grows with the archived ITEMS and not with everything
    else that retires into `archive/` -- `staging.clear_staging` moves whole staging directories
    into `archive/staging/`, which this walk never enters. Inside a type's own subtree the stem
    still has to parse as an id OF THAT TYPE, because "every .yaml under here" is a claim about a
    directory nobody guards.

    A DIRECTORY THAT CANNOT BE READ COSTS ITS OWN NUMBER AND NOT THE PAGE: the board is written at
    the end of every state write, so a permission error here would cost the whole report. The type
    is then simply absent from the count, which is what the tab strip's own wording accounts for.
    """
    found: dict = {}
    for item_type in sorted(ACTIVE_DIRS):
        directory = ext_path(os.path.join(state.archive_root(), item_type))
        count = 0
        try:
            for _dirpath, _dirs, files in os.walk(directory):
                for name in files:
                    if not name.endswith(".yaml"):
                        continue
                    try:
                        found_type, _number = parse_id(name[: -len(".yaml")])
                    except ValueError:
                        continue
                    if found_type == item_type:
                        count += 1
        except OSError:
            continue
        if count:
            found[item_type] = count
    return found


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
    """A field value as ordinary text, containers included, bounded by `_Ink`.

    What a CUT may leave behind is a display decision with a reference consequence -- see
    `_CUT_REFERENCE`.
    """
    out, ink = [], _Ink(VALUE_MAX_CHARS)
    _emit(value, 0, out, ink)
    text = "".join(out)
    if not ink.cut:
        return text
    return _CUT_REFERENCE.sub("", text.rstrip()) + "…"


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


def _title_of(row: dict, body) -> str:
    title = row.get("title")
    if not title and isinstance(body, dict):
        title = body.get("title")
    return _flat(title)


def _face_title(row: dict, body) -> str:
    """The title as it appears on a card or a tree node, or nothing when it cannot be built.

    THE GUARD IS HERE AND NOT IN `_title_of`, and the difference is what the page says afterwards.
    A card and a tree node are drawn OUTSIDE any per-item guard -- one unrenderable title would
    otherwise cost the whole page, for every state write until the file is fixed. The item's DETAIL
    calls `_title_of` unguarded on purpose: that call sits inside `_detail`'s own try, so the same
    failure still becomes a warning that NAMES the id. Silence on the face, said in the banner
    (`test_board.test_an_item_no_renderer_can_read_costs_its_own_card_and_nothing_else`).
    """
    try:
        return _title_of(row, body)
    except Exception:                             # noqa: BLE001 -- see the docstring
        return ""


def _linked(escaped: str, known) -> str:
    """Every id in ALREADY ESCAPED text that this board holds an item for, as a button.

    THE ORDER IS THE WHOLE SAFETY ARGUMENT and it is why this function takes escaped text rather
    than doing both jobs itself: `_REFERENCE` matches capitals, digits and one hyphen -- characters
    `html.escape` neither produces nor consumes -- so a match can never be a piece of an escape
    sequence, and the id it inserts into an attribute can hold no quote, no angle bracket and no
    space by construction. Hostile field content therefore cannot reach the markup through this
    substitution however it is spelled, which is measured on the real write path by
    `test_board.test_a_hostile_field_cannot_add_an_element_or_an_attribute_to_the_page`.

    Only ids this board HAS an item for become buttons; an archived or mistyped id stays text,
    because a control that opens nothing is worse than a plain reference.
    """
    def swap(match):
        item_id = match.group(1)
        if item_id not in known:
            return item_id
        return '<button type="button" class="ref" data-open="%s">%s</button>' % (item_id, item_id)
    return _REFERENCE.sub(swap, escaped)


def _fields(body, known) -> str:
    """The item's own fields as a definition list -- everything not in `HEADER_FIELDS`."""
    rows = []
    for key, value in (body or {}).items():
        if key in HEADER_FIELDS:
            continue
        rendered = "<br>".join(_linked(html.escape(line), known) for line in _lines(value))
        rows.append("<dt>%s</dt><dd>%s</dd>"
                    % (html.escape(str(key)), rendered or "<em>empty</em>"))
    return "<dl>%s</dl>" % "".join(rows) if rows else "<p class='empty'>no further fields</p>"


def _detail(row: dict, body, known) -> tuple:
    """(the item's full record as a hidden `<article>`, what went wrong or None).

    THIS IS THE SURFACE THE CARD OPENS, and it is ordinary markup rendered here -- not a payload the
    page's script turns into markup later. The script only moves the `hidden` attribute, so there is
    no second escaping layer to get right and nothing item-derived ever passes through JavaScript
    (`test_board.test_the_page_script_carries_no_item_content_at_all`).

    ONE ITEM MAY NOT COST THE WHOLE PAGE. The body comes out of a YAML file, so its shape is the
    file's decision, not this module's -- and this module runs at the end of every state write. An
    item whose value nothing here can render therefore becomes a detail that SAYS so, named by its
    id, instead of an exception that reaches `capture`. That it costs its own record and nothing
    else is `test_board.test_an_item_no_renderer_can_read_costs_its_own_card_and_nothing_else`;
    that a state write survives what no renderer catches at all is `state._write_board`.
    """
    item_id = str(row.get("id") or "")
    try:
        head = '<span class="id">%s</span><h2 class="title">%s</h2>' % (
            html.escape(item_id), html.escape(_title_of(row, body)))
        fields = _fields(body, known)
        problem = None
    except Exception as exc:                      # noqa: BLE001 -- see the docstring
        problem = "%s: %s" % (type(exc).__name__, exc)
        head = '<span class="id">%s</span><h2 class="title"></h2>' % html.escape(item_id)
        fields = ('<p class="empty">this item could not be rendered (%s) — read the file '
                  "itself</p>" % html.escape(problem[:200]))
    return ('<article class="detail%s" data-detail="%s" hidden><header>%s'
            '<span class="kind">%s</span><span class="badge">%s</span></header>%s</article>'
            % (" broken" if problem else "", html.escape(item_id, quote=True), head,
               html.escape(str(row.get("type") or "")), html.escape(_column_of(row)), fields),
            problem)


def _card(row: dict, body) -> str:
    """One item's face in its column -- the control that opens its detail."""
    item_id = str(row.get("id") or "")
    return ('<button type="button" class="card" data-open="%s">'
            '<span class="id">%s</span> <span class="title">%s</span></button>'
            % (html.escape(item_id, quote=True), html.escape(item_id),
               html.escape(_face_title(row, body))))


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
        drawn = [_card(row, body) for row, body in cards]
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


def _node_face(node) -> str:
    """A tree node's own line: what kind of thing it is, its id, its title, its status."""
    return ('<button type="button" class="node-face" data-open="%s">'
            '<span class="kind">%s</span> <span class="id">%s</span> '
            '<span class="title">%s</span> <span class="badge">%s</span></button>'
            % (html.escape(node.item_id, quote=True),
               html.escape(backlog_tree.label(node.item_type)),
               html.escape(node.item_id), html.escape(_face_title(node.row, node.body)),
               html.escape(_column_of(node.row))))


def _branches(nodes, view) -> str:
    """The nodes and everything under them, as nested lists.

    ITERATIVE, WITH AN EXPLICIT STACK, and that is not a style choice. The tree's depth is the
    items' own doing -- a chain of tasks each deriving from the last is a legal store -- and a
    recursive walk over it raises RecursionError into `state._write_board`, which catches
    everything by design: the state write survives, and the PAGE quietly keeps its previous
    content. Measured on the recursive version at two depths, both in the round's report. With the
    stack the depth costs memory instead of frames and nothing here has to guess a maximum
    (`test_board.test_a_long_chain_of_links_still_reaches_the_page`).
    """
    out = []
    stack = [("node", node) for node in reversed(nodes)]
    while stack:
        kind, payload = stack.pop()
        if kind == "html":
            out.append(payload)
            continue
        node = payload
        out.append('<li class="node" data-node="%s" data-node-type="%s" data-parent="%s" '
                   'data-depth="%d">%s'
                   % (html.escape(node.item_id, quote=True),
                      html.escape(node.item_type, quote=True),
                      html.escape(node.parent.item_id if node.parent else "", quote=True),
                      node.depth, _node_face(node)))
        follow = []
        for item_type, area, children in node.grouped_children(view):
            # THE AREA IS PART OF THE HEADING and part of the group's identity in the markup, so a
            # person and a test see the same grouping (FR-0017). An item that names no area keeps
            # the heading it always had: the outline is optional, and a project that keeps none
            # gets the page it had before.
            follow.append(('html',
                           '<div class="group" data-group="%s" data-group-area="%s" '
                           'data-group-parent="%s" data-count="%d">'
                           '<h4>%s%s <span class="count">%d</span></h4><ol>'
                           % (html.escape(item_type, quote=True),
                              html.escape(area, quote=True),
                              html.escape(node.item_id, quote=True), len(children),
                              html.escape(backlog_tree.label(item_type, len(children))),
                              html.escape(" — " + area) if area else "",
                              len(children))))
            follow.extend(("node", child) for child in children)
            follow.append(("html", "</ol></div>"))
        follow.append(("html", "</li>"))
        stack.extend(reversed(follow))
    return "".join(out)


def _tree_view(arrangement) -> str:
    """One hierarchical view: its roots, then everything no link could place."""
    view = arrangement.view
    parts = ['<p class="lead">%s</p>' % html.escape(view.lead)]
    if arrangement.roots:
        parts.append('<ol class="tree" data-tree="%s">%s</ol>'
                     % (html.escape(view.key, quote=True),
                        _branches(arrangement.roots, view)))
    else:
        parts.append('<p class="empty">no %s yet — nothing to hang this view from</p>'
                     % html.escape(" or ".join(sorted(
                         backlog_tree.label(item_type)
                         for item_type in backlog_tree.ROOT_TYPES))))
    if arrangement.unassigned:
        parts.append('<section class="unassigned" data-unassigned="%s" data-count="%d">'
                     '<h3>Unassigned <span class="count">%d</span></h3>'
                     '<p class="lead">This view could not place these items under any item they '
                     'name — some name nothing, some name an item this view does not show, some '
                     'name an id that is not on this board at all. They stand here rather than '
                     'nowhere; the warning above says which group is which.</p>'
                     '<ol class="tree">%s</ol></section>'
                     % (html.escape(view.key, quote=True), len(arrangement.unassigned),
                        len(arrangement.unassigned),
                        _branches(arrangement.unassigned, view)))
    return "".join(parts)


def _warnings(found) -> str:
    """The banner of one view -- (type, kind, text) triples, or nothing at all."""
    if not found:
        return ""
    return '<ul class="warnings">%s</ul>' % "".join(
        '<li data-warning="%s" data-type="%s">%s: %s</li>'
        % (html.escape(kind, quote=True), html.escape(item_type, quote=True),
           html.escape(item_type), html.escape(detail))
        for item_type, kind, detail in found)


_STYLE = """
:root { color-scheme: light dark; }
body { font: 14px/1.45 system-ui, sans-serif; margin: 0 0 3rem; padding: 1rem 1.25rem; }
h1 { font-size: 1.35rem; margin: 0 0 .25rem; }
h2 { font-size: 1.05rem; margin: 1.75rem 0 .5rem; }
h3 { font-size: .78rem; letter-spacing: .04em; text-transform: uppercase; margin: 0 0 .5rem;
     opacity: .75; }
h4 { font-size: .74rem; letter-spacing: .04em; text-transform: uppercase; margin: .5rem 0 .2rem;
     opacity: .7; font-weight: 600; }
.meta { margin: 0 0 1rem; opacity: .75; }
.lead { margin: .2rem 0 1rem; opacity: .8; max-width: 62rem; }
.tabs { display: flex; flex-wrap: wrap; gap: .4rem; align-items: center; margin: 0 0 1rem;
        border-bottom: 1px solid rgba(128,128,128,.35); padding-bottom: .5rem; }
.tab { font: inherit; cursor: pointer; background: rgba(128,128,128,.1); color: inherit;
       border: 1px solid rgba(128,128,128,.35); border-radius: .4rem; padding: .35rem .7rem; }
.tab[aria-selected="true"] { background: rgba(128,128,128,.32); font-weight: 600; }
.archived { margin-left: auto; opacity: .7; font-size: .85rem; }
nav.types a { margin-right: .6rem; white-space: nowrap; }
.board { display: flex; gap: .6rem; overflow-x: auto; align-items: flex-start; padding-bottom: .4rem; }
.column { flex: 0 0 15rem; border: 1px solid rgba(128,128,128,.35); border-radius: .4rem;
          padding: .5rem; }
.column.terminal { opacity: .6; }
.count { opacity: .6; font-weight: normal; }
.card { display: block; width: 100%; text-align: left; font: inherit; color: inherit; cursor: pointer;
        border: 1px solid rgba(128,128,128,.3); border-radius: .3rem; padding: .35rem .45rem;
        margin-bottom: .4rem; background: rgba(128,128,128,.07); }
.card:hover, .node-face:hover { background: rgba(128,128,128,.2); }
.id { font-family: ui-monospace, monospace; font-size: .8rem; opacity: .7; }
.kind { font-size: .72rem; text-transform: uppercase; letter-spacing: .04em; opacity: .6; }
.badge { font-size: .72rem; border: 1px solid rgba(128,128,128,.4); border-radius: .8rem;
         padding: 0 .45rem; opacity: .8; }
.tree, .tree ol { list-style: none; margin: 0; padding: 0; }
.tree .group { margin: 0 0 .3rem 1.4rem; border-left: 1px solid rgba(128,128,128,.3);
               padding-left: .7rem; }
.node { margin: .15rem 0; }
.node-face { display: block; width: 100%; text-align: left; font: inherit; color: inherit;
             cursor: pointer; background: rgba(128,128,128,.07); border-radius: .3rem;
             border: 1px solid rgba(128,128,128,.3); padding: .3rem .5rem; }
.unassigned { border: 1px solid #c93; border-radius: .4rem; padding: .6rem; margin: 1.5rem 0 0; }
.ref { font: inherit; font-family: ui-monospace, monospace; font-size: .85em; cursor: pointer;
       background: rgba(128,128,128,.15); border: 1px solid rgba(128,128,128,.35);
       border-radius: .25rem; padding: 0 .25rem; color: inherit; }
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,.55); padding: 2.5vh 2vw;
           overflow: auto; }
.dialog { max-width: 60rem; margin: 0 auto; background: Canvas; color: CanvasText;
          border: 1px solid rgba(128,128,128,.5); border-radius: .5rem; padding: 1rem 1.2rem; }
.dialog .close { float: right; font: inherit; cursor: pointer; color: inherit;
                 background: rgba(128,128,128,.15); border: 1px solid rgba(128,128,128,.4);
                 border-radius: .3rem; padding: .2rem .6rem; }
.detail header { display: flex; flex-wrap: wrap; gap: .5rem; align-items: baseline;
                 border-bottom: 1px solid rgba(128,128,128,.3); padding-bottom: .4rem; }
.detail h2 { margin: 0; font-size: 1.15rem; }
.detail dl { display: grid; grid-template-columns: max-content 1fr; gap: .2rem .8rem;
             margin: .7rem 0 .1rem; font-size: .9rem; }
.detail dt { font-weight: 600; opacity: .7; }
.detail dd { margin: 0; overflow-wrap: anywhere; }
.warnings { border: 1px solid #c93; border-radius: .4rem; padding: .6rem .6rem .6rem 1.6rem;
            margin: 0 0 1rem; }
.empty { opacity: .6; font-style: italic; margin: .4rem 0 .1rem; }
"""

# The fallback when the browser runs no script: every view and every detail becomes visible, so the
# file degrades into the one long page FR-0030 shipped rather than into a board with a dead tab
# strip whose cards open nothing -- that, and not an empty page, is what is left without these
# rules. It
# is an author rule with `!important`, which is what lets it beat the `hidden` attribute the
# renderer writes (the browser's own `[hidden] { display: none }`).
#
# `.interactive` is the other half of the same fallback and it is about a SENTENCE rather than a
# layout: the header tells the reader that a click opens an item's record, and with no script that
# sentence is not true. It is hidden here, and the `<noscript>` note in the body says what holds
# instead -- with scripting off, nothing on this page may claim a behaviour it no longer has. Both
# directions were measured in a browser for the round's report.
_NOSCRIPT_STYLE = """
[hidden] { display: block !important; }
.tabs, .dialog .close, .interactive { display: none !important; }
.overlay { position: static !important; background: none !important; padding: 0 !important; }
.detail { border-top: 1px solid rgba(128,128,128,.4); margin-top: 1rem; }
"""

# The whole of the page's behaviour. A CONSTANT: no item content is interpolated into it, which is
# why a `</script>` in a hostile title is impossible here rather than escaped. It moves the `hidden`
# attribute and the `aria-selected` state and does nothing else -- no fetch, no navigation, no
# storage, no element it creates from a string.
_SCRIPT = """
(function () {
  var overlay = document.querySelector('.overlay');
  var details = document.querySelectorAll('[data-detail]');
  var views = document.querySelectorAll('[data-view]');
  var tabs = document.querySelectorAll('[data-tab]');
  function open(id) {
    var found = false;
    for (var i = 0; i < details.length; i++) {
      var mine = details[i].getAttribute('data-detail') === id;
      details[i].hidden = !mine;
      found = found || mine;
    }
    if (found && overlay) { overlay.hidden = false; }
    return found;
  }
  function close() {
    if (overlay) { overlay.hidden = true; }
    for (var i = 0; i < details.length; i++) { details[i].hidden = true; }
  }
  function show(key) {
    for (var i = 0; i < views.length; i++) {
      views[i].hidden = views[i].getAttribute('data-view') !== key;
    }
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].setAttribute('aria-selected',
        tabs[i].getAttribute('data-tab') === key ? 'true' : 'false');
    }
  }
  document.addEventListener('click', function (event) {
    var node = event.target;
    while (node && node.getAttribute) {
      if (node.hasAttribute('data-open')) { open(node.getAttribute('data-open')); return; }
      if (node.hasAttribute('data-close')) { close(); return; }
      if (node.hasAttribute('data-tab')) { close(); show(node.getAttribute('data-tab')); return; }
      node = node.parentNode;
    }
    if (event.target === overlay) { close(); }
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') { close(); }
  });
})();
"""


def render(state, entries, generated_at: str) -> str:
    """The whole board as one dependency-free HTML page.

    `entries` are (index row, item body or None) pairs -- the rows the caller has just written into
    `generated/index.yaml` and the bodies it read on the way, so the board reports exactly the state
    the index reports and costs no second parse of the store.

    A type is on the page when the state has a home for it OR an entry names it: the first is the
    kit's own set of types, the second is what makes an item impossible to lose, whatever type it
    turns out to carry.

    THE ITEM DETAILS ARE RENDERED ONCE, at the end, and every card and every tree node is a control
    that opens one of them. So an item shown in three views still has ONE record on the page, and
    the fields of an item live in exactly one place no matter how many views place it.
    """
    grouped: dict = {}
    for row, body in entries:
        grouped.setdefault(str(row.get("type") or "?"), []).append((row, body))
    types = sorted(set(types_present(state)) | set(grouped))

    sections, board_warnings = [], []
    for item_type in types:
        section, found = _section(item_type, grouped.get(item_type, []))
        sections.append(section)
        board_warnings += found

    known = {str(row.get("id") or "") for row, _body in entries}
    details = []
    for row, body in entries:
        drawn, problem = _detail(row, body, known)
        details.append(drawn)
        if problem:
            # NAMED, not counted: the id is what a reader needs to open the file that broke
            board_warnings.append((str(row.get("type") or "?"), "unrenderable",
                                   "%s could not be rendered (%s)"
                                   % (row.get("id") or "?", problem[:120])))

    type_nav = '<nav class="types">%s</nav>' % "".join(
        '<a href="#type-%s">%s (%d)</a>' % (html.escape(item_type, quote=True),
                                            html.escape(item_type), len(grouped.get(item_type, [])))
        for item_type in types)
    views = ['<div class="view" data-view="board">%s%s\n%s</div>'
             % (_warnings(board_warnings), type_nav, "\n".join(sections))]
    tabs = [("board", "Board", len(entries))]
    for view in backlog_tree.VIEWS:
        arrangement = backlog_tree.arrange(view, entries)
        views.append('<div class="view" data-view="%s" hidden>%s%s</div>'
                     % (html.escape(view.key, quote=True),
                        _warnings([(item_type, kind, detail)
                                   for kind, item_type, detail in arrangement.warnings]),
                        _tree_view(arrangement)))
        tabs.append((view.key, view.label,
                     arrangement.placed + len(arrangement.unassigned)))

    archived = archived_counts(state)
    strip = "".join(
        '<button type="button" class="tab" data-tab="%s" aria-selected="%s">%s '
        '<span class="count">%d</span></button>'
        % (html.escape(key, quote=True), "true" if key == "board" else "false",
           html.escape(label), count)
        for key, label, count in tabs)
    strip += ('<span class="archived" data-archived="%d">archived, not on this board: %d%s</span>'
              % (sum(archived.values()), sum(archived.values()),
                 (" (%s)" % ", ".join("%s %d" % (item_type, count)
                                      for item_type, count in sorted(archived.items())))
                 if archived else ""))

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Backlog board</title>\n<style>%s</style>\n"
        "<noscript><style>%s</style></noscript>\n</head>\n<body>\n"
        '<header><h1>Backlog board</h1>\n'
        '<p class="meta">Rebuilt by the state kernel together with <code>index.yaml</code>, on '
        'every state write the kernel makes — <time data-generated-at="%s">%s</time>. A rebuild '
        "that fails says so on the error output of the command that triggered it and leaves this "
        "page as it was, so compare that stamp with what you expect. It reports, it never sets: "
        "this page is regenerated output and holds no state of its own. "
        '<span class="interactive">The three tabs are three views of the same items; a click on '
        "any card or tree row opens that item's full record, and every id inside it that this "
        "board holds opens in turn.</span> Shown is every item in a type's <code>active</code> "
        "directory; an archived item is not on this board.</p></header>\n"
        '<noscript><p class="meta">This browser runs no scripts, so the tabs above would do '
        "nothing and no card would open. Instead this page shows everything at once: the tabs are "
        "hidden, all three views stand one after another, and every item's full record is open "
        "under the board.</p></noscript>\n"
        '<nav class="tabs" role="tablist">%s</nav>\n<main>\n%s\n</main>\n'
        '<div class="overlay" hidden><div class="dialog" role="dialog" aria-modal="true">'
        '<button type="button" class="close" data-close>Close</button>%s</div></div>\n'
        "<script>%s</script>\n</body>\n</html>\n"
        % (_STYLE, _NOSCRIPT_STYLE,
           html.escape(str(generated_at), quote=True), html.escape(str(generated_at)),
           strip, "\n".join(views), "".join(details), _SCRIPT))
