"""The backlog board over the typed state -- `generated/board.html` (FR-0030, FR-0053, FR-0075).

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

ONE RENDERER OF THE ITEMS, AND THIS IS IT (DEC-0065 (1)). The dev kit's own
`scripts/generate_dashboard.py` used to render the same items into a second page from a second
reading of the same index. The design pass measured the two against one copy of this repo
(`project_memory/staging/TSK-0115/parity.md`, which carries the figures): every sum agreed that
day, and the two disagreed as soon as the store held something unusual -- one counted yaml FILES
under `archive/`, the other item IDS of a type. Two programs that agree by inspection are two
numbers a reader has to reconcile, so the dashboard renders vital signs and a pointer here. What is
gone is the second COUNTING of the items; the one number it still states about them is the length
of the index it read, beside that index's own timestamp, so the two can be compared rather than
guessed at.

WHAT IT MAY NOT BECOME. The board is a REPORT: it is written under `generated/`, the directory
every kit's `.gitignore` excludes and the kernel rebuilds from the items, and it is a pure function
of the items it is handed, the type directories the project has, the archive it counts, the open
approval requests it reads, and the timestamp its caller hands it. Nothing here reads a status it
was not given and nothing here writes state. It reads no clock either -- `_clock` says why.

FOUR VIEWS, ONE FILE, AND THE ONLY SCRIPT IS THE ONE THAT MOVES ATTRIBUTES (FR-0053, FR-0075). The
page carries a Board tab (a row of status slots per type), the two hierarchical backlog views
`backlog_tree` derives, and -- only when the state holds milestones -- a Timeline. Which view is
showing, which record is open, which branch is folded and which focus list is unrolled are all DOM
state the renderer writes; the inline script moves those attributes and does nothing else. It
fetches nothing, loads nothing, stores nothing and writes no state; the whole of it is `_SCRIPT`
below, a constant with no item content interpolated into it, which is what makes a `</script>`
inside a hostile title impossible rather than escaped
(`test_board.test_the_page_script_carries_no_item_content_at_all`).

WITH SCRIPTING OFF the page falls back to what FR-0030 shipped: `_NOSCRIPT_STYLE` un-hides every
view, every folded branch and every item detail, and hides the controls that would then do nothing
-- the tabs, the fold buttons, the focus figures. That is a CSS fallback in the page, not a claim
about a browser this suite runs, and both halves are read out of the rendered page by
`test_board.test_the_noscript_page_shows_every_group_and_no_fold_control`.

DERIVED, NOT LISTED, in the places a list would rot:
  * WHICH TYPES a kit has is read off the state directory it installed (`types_present`) -- the
    office kit ships no `research/active`, the research kit no `procedures/active`, and no per-kit
    type table exists to disagree with the tree;
  * WHICH SLOTS a type has is its own automaton (`status_columns`), chain order first, so a
    changed chain moves the board with it;
  * WHICH TYPES lead and which are paperwork is `type_order`: a type with an automaton is living
    work, a type without one is a record, and the kit's own root type leads;
  * WHERE an item stands in its own life is `lane`, read off that same automaton -- first status,
    last status, anything else in between. That is also the answer to "what is in flight", and it
    is why `READY` counts there (DEC-0065 (4));
  * WHICH ITEM a card links to is every id the item's own fields name (`_linked`), and which of
    those becomes a button is whether this board HAS that item -- not a list of reference fields.

A STATUS NO SLOT CLAIMS IS NEVER DROPPED. It gets a slot of its own and a warning ON THE PAGE
-- the only channel a report has, since stdout belongs to the command the state write was part of,
where `kernel.cli` prints that command's own paths and verdicts. The two directions are
`test_board.test_an_item_type_no_status_vocabulary_describes_still_appears_with_a_warning` and
`test_board.test_a_record_type_without_a_status_is_not_reported_as_a_defect`. A type with no items
at all keeps its name on the page too, in the silent line
(`test_board.test_each_kit_renders_the_types_its_own_template_ships`). The tree views carry the
same property through `backlog_tree`: an item no link can place is shown with the reason, never
dropped.
"""
from __future__ import annotations

import datetime
import html
import os
import re
import time

from . import backlog_tree
from .backlog_types import ACTIVE_DIRS, AUTOMATA, parse_id, status_values
from .lock import ext_path


# The report's name under `generated/`. One constant, because `kernel.state` composes the path with
# it and every reader of the board asks for the same file. `dashboard.html` is deliberately NOT this
# name: the dev kit's own `scripts/generate_dashboard.py` still writes that file -- vital signs and
# a pointer here, since DEC-0065 (1) -- and two writers on one path would race on every state write.
FILENAME = "board.html"

# The slot a corrupt item file lands in -- a file `state` could not parse has no status, but it is
# still an item somebody has to fix, and a board that omitted it would be reassuring about a state
# nobody could read.
UNREADABLE = "(unreadable)"

# ...and the slot for an item that carries no status at all. For a record type (Evidence,
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

# WHERE AN ITEM STANDS IN ITS OWN LIFE, and the whole vocabulary of it. Read off the type's own
# automaton by `lane` below, so nothing here is a list of statuses: `NEW` is its first status,
# `DONE` a last one, `FLIGHT` everything registered in between, `OFF` a status the automaton does
# not know at all, and `RECORD` a type that has no automaton to ask.
NEW, FLIGHT, DONE, RECORD, OFF = "new", "flight", "done", "record", "off"

# The three lanes a plan is read in, in the words the page uses for them. `plan_diagram` names the
# same three on its own cells, from this map, so the board and the diagrams beside it cannot call
# one lane two things.
LANE_WORDS = {NEW: "planned", FLIGHT: "in flight", DONE: "done"}

# The three questions the first strip answers (FR-0075's brief), each with the sentence that stands
# where the number is zero. The keys are the focus keys in the markup and in `_SCRIPT`'s CSS hook.
FOCUS = {
    "blocked": ("blocked", "nothing is stuck"),
    "you": ("waiting on you", "no open question for you"),
    "flight": ("in flight", "nothing started yet"),
}

# Which milestone type the Timeline is over (DEC-0064: a milestone is an item TYPE, not a date field
# on other items). ONE name, because the decision is one; everything else about a milestone --
# its slots, its lane, its place in a tree, its plain-language name -- is derived from the type's own
# automaton and label like every other type's. The type lines themselves belong to
# `backlog_types`, which this module does not own; until stream C applies them a store cannot hold
# a milestone at all and the Timeline tab simply does not appear.
# `test_board.test_the_milestone_type_is_wired_completely_or_not_at_all` is the tripwire on a
# half-applied seam.
MILESTONE_TYPE = "MST"

# Below a node at this depth, the groups of children start folded. Roots stay open: a page whose
# first view is a list of closed roots answers nothing, while a fully open system view of this repo
# is far longer than a screen -- the design pass counted it and sighted both defaults
# (`project_memory/staging/TSK-0115/08-final.md`). So a reader meets every root with what hangs
# directly under it and one click opens the level below.
FOLD_DEPTH = 1

# Two milestone labels closer together than this share of the ruler would overlap, so the second
# takes the middle band (the today marker owns the top one). The number is the one phase 1d measured
# the three bands against; the ruler's height is in `_STYLE` beside the bands themselves.
LABEL_BAND_GAP = 9.0


def status_columns(item_type: str) -> tuple:
    """The board slots of one type, in the order work moves through them.

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


def lane(item_type: str, status) -> str:
    """Where an item stands in its own life -- read off its automaton and nothing else.

    This is the one derivation behind three surfaces: the "in flight" number of the first strip,
    the dimming a focus click applies, and the lanes of the generated plan. DEC-0065 (4) settles
    what a reader asks about it -- `READY` is in flight, because it is neither the first status of
    a task nor a last one -- and settles it as this rule rather than as a list of statuses, so a
    changed chain moves all three surfaces together.
    """
    automaton = AUTOMATA.get(item_type)
    if automaton is None:
        return RECORD
    if status == automaton.initial:
        return NEW
    if status in automaton.terminals:
        return DONE
    if status in automaton.states:
        return FLIGHT
    return OFF


def type_order(types) -> tuple:
    """(living types, record types) -- what the board leads with and what it files at the end.

    A type with an automaton is living work: it moves, so it belongs in slots a reader scans. A type
    without one is paperwork -- Evidence, decisions, approvals, the frozen design artefacts -- which
    is complete the moment it is written and is filed rather than tracked (DEC-0065 (3)). Inside the
    living half the kit's own root type leads, which `backlog_tree.ROOT_TYPES` already knows.
    """
    living = [item_type for item_type in types if item_type in AUTOMATA]
    roots = [item_type for item_type in living if item_type in backlog_tree.ROOT_TYPES]
    rest = [item_type for item_type in living if item_type not in backlog_tree.ROOT_TYPES]
    return tuple(roots + rest), tuple(item_type for item_type in types if item_type not in AUTOMATA)


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


def _clock(generated_at) -> tuple:
    """(epoch seconds, calendar date) of the stamp the caller handed in -- or (None, None).

    THE PAGE READS NO CLOCK OF ITS OWN, and that is a property rather than an omission. Two things
    on it depend on "now": whether an approval request has already expired, and where today stands
    on the milestone ruler. Both are answered from `generated_at` -- the ONE reading
    `state._regenerate_index_locked` takes for the index and the board together -- so the page stays
    a pure function of what it is handed and cannot report a different instant than the index beside
    it. Measured as determinism under a fixed stamp:
    `test_board.test_the_board_is_a_pure_function_of_the_state_and_the_stamp_it_is_handed`.

    A STAMP THIS CANNOT READ COSTS THE TWO ANSWERS AND NOT THE PAGE: the ruler then carries no today
    marker, and no request is called expired, because "expired" is a claim this page would have
    nothing to make it with. The test that measures it is
    `test_board.test_a_stamp_the_board_cannot_read_costs_the_today_marker_and_not_the_page`.
    """
    try:
        parsed = time.strptime(str(generated_at)[:19], "%Y-%m-%dT%H:%M:%S")
    except (TypeError, ValueError):
        return None, None
    try:
        epoch = time.mktime(parsed)
    except (OverflowError, ValueError):
        epoch = None
    return epoch, datetime.date(parsed.tm_year, parsed.tm_mon, parsed.tm_mday)


def open_requests(state, now) -> list:
    """The approval requests a person can still answer -- `approvals/pending/`, expiry applied.

    THE EXPIRY RULE IS ASKED, NOT SPELLED: a request past `expires_at_epoch` can never mint, so it
    is not an open question for anybody, and `approvals.has_expired` is the one place that says so
    -- for the hooks, for the session brief and, since TSK-0120, for this strip. The import is
    deferred into the call because `approvals` imports `state` and `state` imports THIS module at
    module scope, so only a module-level import back would close the package's graph into a cycle;
    the package already reaches the other way the same way (`state.py`, `approvals.py`, each with
    the same one-line reason). What is NOT shared is the WALK: this module reads the files itself,
    through `_flat`, because a request file is a hand-written file and the two halves of that
    defence are `_emit`'s depth bound and character budget
    (`test_board.test_a_request_file_nothing_could_write_costs_neither_the_page_nor_the_write`).
    What is left of H126 in `docs/POST_V2_WISHLIST.md` after this is the two clocks, not the rule.

    `now` is the page's own stamp (`_clock`) -- the second clock, and it stays a second clock so
    the page remains a pure function of the state it was rendered from. When it could not be read,
    nothing here is called expired: over-reporting an open question is a nuisance, dropping one is
    the failure this strip exists against.

    A REQUEST FILE IS A FILE, so this reads it the way this module reads every other file: through
    `_flat`, whose depth bound and character budget are the two halves of the alias-bomb defence
    (`_emit`), and with the clock call wrapped. `approvals.create_pending_request` cannot produce
    either shape -- the TTL is its own argument and no command exposes it -- so both only ever
    arrive as a hand-written or corrupted file, which is exactly the class this renderer is built
    against twice over. Measured on the shipped code before this line existed, in a store outside
    the repo: `expires_at_epoch: 99999999999` raised OSError and `1e30` OverflowError out of
    `time.localtime`, so `_write_board` caught it and the WHOLE PAGE stopped being rebuilt at every
    later state write -- "nothing vanishes" turned into "everything vanishes"; and a 504-byte
    request whose `item` is an alias graph rendered a 107 MB page.
    `test_board.test_a_request_file_nothing_could_write_costs_neither_the_page_nor_the_write`.
    """
    from . import approvals                       # deferred: `approvals` imports `state`
    pending = os.path.join(state.root, "approvals", "pending")
    found = []
    if not os.path.isdir(ext_path(pending)):
        return found
    for name in sorted(os.listdir(ext_path(pending))):
        if not name.endswith(".yaml"):
            continue
        try:
            request = state._read_yaml(os.path.join(pending, name))
        except Exception:                         # noqa: BLE001 -- a report never fails a write
            continue
        if not isinstance(request, dict):
            continue
        if now is not None and approvals.has_expired(request, now):
            continue
        try:
            expires = float(request.get("expires_at_epoch", 0))
        except (TypeError, ValueError):
            expires = 0.0
        try:
            shown = (time.strftime("%Y-%m-%d %H:%M", time.localtime(expires))
                     if expires else "no expiry")
        except (OSError, OverflowError, ValueError):
            # a date this platform cannot express is still a request somebody has to answer
            shown = "unreadable expiry"
        # THE REQUEST ID IS NOT CARRIED, and that is a decision rather than an omission: nothing on
        # this page shows it, so reading it would mean spending the flattener on a value that is
        # thrown away -- and every field read here is a `str()` call an alias graph can make
        # expensive (see the docstring). When the seam below lands, the id arrives with the record
        # `approvals.pending_request` builds and is not composed a second time here.
        found.append({
            "kind": _flat(request.get("kind")) or "?",
            "item": _flat(request.get("item")),
            "expires": shown,
        })
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
    """Which slot an index row belongs in -- its status, or one of the two named sentinels."""
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


def face_title(row: dict, body) -> str:
    """What a card shows besides its id -- the item's title, or the work it describes.

    A `TSK` OWES NO TITLE. Its field contract (`backlog_types.REQUIRED_FIELDS`) asks for the kind of
    work, the item it serves and the role that holds it, and not for a sentence -- so a task board
    built on `title` alone showed a column of bare ids, which is what the design pass measured on
    the shipped page. What stands instead is what the ITEM'S OWN BODY says about the work, read off
    the body rather than off a per-type table: nothing is invented, and a body that says none of it
    yields nothing at all rather than a restatement of the type the card already stands under.
    `test_board.test_a_task_without_a_title_shows_its_work_on_the_face` measures the first half,
    `test_board.test_an_item_no_renderer_can_read_costs_its_own_card_and_nothing_else` the second.
    """
    title = _face_title(row, body)
    if title or not isinstance(body, dict):
        return title
    parts = []
    if body.get("type"):
        parts.append(_flat(body["type"]))
    target = body.get("derives_from") or body.get("product_requirement") or body.get("related_pr")
    if target:
        parts.append("for %s" % _flat(target))
    if body.get("assigned_role"):
        parts.append("· %s" % _flat(body["assigned_role"]))
    return " ".join(part for part in parts if part)


def blockers(row: dict) -> str:
    """The ids an item's `blocked_by` names, as one line -- scalar or list (the BUG-0015 shape)."""
    value = row.get("blocked_by")
    if not value:
        return ""
    return ", ".join(_flat(one) for one in (value if isinstance(value, list) else [value]))


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


def _face(row: dict, body) -> str:
    """The id and the title (or its absence) every clickable face of an item carries.

    ONE PLACE, because a card, a focus row and a milestone face all answer the same question and a
    reader who meets the same item twice may not meet two different faces. An item with nothing to
    show carries no `.title` element at all rather than a placeholder inside one: the placeholder
    IS a title as far as any reader of the page is concerned, including
    `test_board.test_an_item_no_renderer_can_read_costs_its_own_card_and_nothing_else`, which is
    where the difference is measured.
    """
    shown = face_title(row, body)
    return ('<span class="id">%s</span> %s'
            % (html.escape(str(row.get("id") or "")),
               ('<span class="title">%s</span>' % html.escape(shown)) if shown
               else '<span class="untitled">no title</span>'))


def _card(row: dict, body, flags: dict) -> str:
    """One item's face in its slot -- the control that opens its detail.

    The two signals a reader looks for FIRST are on the face and not in the record behind it
    (FR-0075): a blocked card names what it waits for, a card somebody owes an answer for names
    the kind of approval. `test_board.test_a_blocked_card_carries_its_blocker_on_its_face`.
    """
    item_id = str(row.get("id") or "")
    classes = ["card"] + [flag for flag in ("blocked", "you") if flag in flags]
    note = ""
    if "blocked" in flags:
        note = '<span class="flag">blocked by %s</span>' % html.escape(blockers(row))
    elif "you" in flags:
        note = ('<span class="flag">waiting on you: %s approval</span>'
                % html.escape(flags["you"]))
    return ('<button type="button" class="%s" data-open="%s" data-lane="%s">'
            '<span class="head"><span class="id">%s</span>%s</span>%s</button>'
            % (" ".join(classes), html.escape(item_id, quote=True),
               html.escape(lane(str(row.get("type") or ""), row.get("status")), quote=True),
               html.escape(item_id), note,
               ('<span class="title">%s</span>' % html.escape(face_title(row, body)))
               if face_title(row, body) else '<span class="untitled">no title</span>'))


def _by_column(item_type: str, entries: list) -> tuple:
    """(declared slots, {slot: [(row, body), ...]}, slots nothing declared) for one type."""
    declared = status_columns(item_type)
    by_column: dict = {column: [] for column in declared}
    for row, body in entries:
        by_column.setdefault(_column_of(row), []).append((row, body))
    extra = sorted(column for column in by_column if column not in declared)
    return declared, by_column, extra


def _column_warnings(item_type: str, entries: list) -> list:
    """(type, kind, text) for every slot this type's own vocabulary does not describe.

    SEPARATED FROM THE MARKUP, because the two answer different questions and the page needs the
    warnings for types it does NOT draw a slot row for: a record type files its items in the
    records block, and a status nothing declares is just as much a defect there. While the warnings
    were computed inside the section renderer, a type that stopped getting a section stopped being
    checked.
    """
    declared, by_column, extra = _by_column(item_type, entries)
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
    return warnings


def _section(item_type: str, entries: list, flags_of) -> str:
    """One living type's row of slots -- every entry of that type, in the slot its status names.

    THE EMPTY RULE, and both of its halves. An empty slot in the CHAIN is drawn, narrow: the flow
    reads left to right and a gap in it is information. An empty TERMINAL is not drawn at all --
    "0 REJECTED" is the normal state of every healthy project, and a page mostly made of such slots
    is what the design pass measured on the shipped board
    (`project_memory/staging/TSK-0115/01-information-architecture.md`). Both are named in the line
    under the row instead, so nothing vanishes silently.
    `test_board.test_an_empty_end_state_is_named_not_drawn` measures both ends.
    """
    declared, by_column, extra = _by_column(item_type, entries)
    terminals = getattr(AUTOMATA.get(item_type), "terminals", frozenset())
    slots, empty_ends, empty_chain = [], [], []
    for column in list(declared) + extra:
        cards = sorted(by_column.get(column, []), key=lambda pair: str(pair[0].get("id") or ""))
        drawn = [_card(row, body, flags_of(row)) for row, body in cards]
        if not drawn:
            (empty_ends if column in terminals else empty_chain).append(html.escape(str(column)))
            if column in terminals:
                continue
        slots.append('<div class="slot%s%s" data-status="%s" data-count="%d">'
                     '<h3>%s <span class="count">%d</span></h3>%s</div>'
                     % (" terminal" if column in terminals else "", "" if drawn else " empty",
                        html.escape(str(column), quote=True), len(drawn),
                        html.escape(str(column)), len(drawn), "".join(drawn)))
    empties = ""
    if empty_ends or empty_chain:
        empties = '<p class="empties">%s%s</p>' % (
            ('<span class="ends">no cards in %s</span>' % " · ".join(empty_ends))
            if empty_ends else "",
            ('<span class="chain">%sno cards in %s</span>'
             % (" — " if empty_ends else "", " · ".join(empty_chain))) if empty_chain else "")
    return ('<section class="type" id="type-%s" data-type="%s" data-items="%d">'
            '<h2><span class="name">%s</span> <span class="code">%s</span> '
            '<span class="count">%d</span></h2>%s<div class="board">%s</div></section>'
            % (html.escape(item_type, quote=True), html.escape(item_type, quote=True), len(entries),
               html.escape(backlog_tree.label(item_type, 2)), html.escape(item_type), len(entries),
               empties, "".join(slots)))


def _records_section(record_types, grouped) -> str:
    """The project's paperwork: listed, grouped by status, and CLOSED by default (DEC-0065 (3)).

    Evidence, decisions, approvals and the frozen design artefacts are complete when they are
    written; they are looked up, not scanned. On this repo they OUTNUMBER the living work, so the
    board was mostly a list of finished paperwork. Nothing is dropped: the summary counts every one
    of them, opening the block shows every id, and every record still has its own record on the
    page.
    A type whose vocabulary is empty gets no status heading, because `(no status)` is that type's
    contract rather than a group a reader chooses between.
    """
    total = sum(len(grouped.get(item_type, [])) for item_type in record_types)
    if not total:
        return ""
    summary = " · ".join("%s %d" % (backlog_tree.label(item_type, 2), len(grouped[item_type]))
                         for item_type in record_types if grouped.get(item_type))
    parts = []
    for item_type in record_types:
        entries = grouped.get(item_type, [])
        if not entries:
            continue
        _declared, by_column, _extra = _by_column(item_type, entries)
        groups = []
        for status, pairs in sorted((key, value) for key, value in by_column.items() if value):
            rows = "".join(
                '<li><button type="button" class="rec" data-open="%s">%s</button></li>'
                % (html.escape(str(row.get("id") or ""), quote=True), _face(row, body))
                for row, body in sorted(pairs, key=lambda pair: str(pair[0].get("id") or ""),
                                        reverse=True))
            heading = ('<h4>%s <span class="count">%d</span></h4>'
                       % (html.escape(str(status)), len(pairs))) if status_columns(item_type) else ""
            groups.append('<div class="recgroup" data-status="%s" data-count="%d">%s<ul>%s</ul>'
                          "</div>" % (html.escape(str(status), quote=True), len(pairs), heading,
                                      rows))
        parts.append('<section class="records-type" data-type="%s">'
                     '<h3><span class="name">%s</span> <span class="code">%s</span> '
                     '<span class="count">%d</span></h3>%s</section>'
                     % (html.escape(item_type, quote=True),
                        html.escape(backlog_tree.label(item_type, 2)), html.escape(item_type),
                        len(entries), "".join(groups)))
    return ('<details class="records" id="records" data-records="%d"><summary>Records '
            '<span class="count">%d</span> <span class="sum">%s</span></summary>%s</details>'
            % (total, total, html.escape(summary), "".join(parts)))


def _focus_row(row, body, note: str) -> str:
    return ('<li><button type="button" class="rec" data-open="%s">%s '
            '<span class="badge">%s</span>%s</button></li>'
            % (html.escape(str(row.get("id") or ""), quote=True), _face(row, body),
               html.escape(_column_of(row)),
               (' <span class="note">%s</span>' % html.escape(note)) if note else ""))


def _first_strip(entries, requests) -> tuple:
    """(the three numbers with the three lists behind them, {item id: request kind}).

    THE THREE QUESTIONS FR-0075 NAMES, in the order it names them: what is blocked, what waits on
    you, what is in flight. Each number is a control that unrolls the list it counts, and the number
    and the list are ONE computation -- `data-count` on the list and the figure's own number come
    from the same sequence, which is what
    `test_board.test_the_first_strip_counts_blocked_waiting_and_in_flight_from_the_state` reads off
    the page. A count computed once and a list built again is how the two start disagreeing.

    AN OPEN REQUEST WHOSE ITEM IS NOT ON THIS BOARD still gets a row and is still counted. A
    request outlives the item it was asked about -- the item can be archived under it -- and it is
    still a question somebody has to answer; a strip that counted only the requests it could put a
    card behind would say "nothing waits on you" while the session brief said otherwise. Measured
    on exactly that store by
    `test_board.test_the_board_and_the_session_brief_agree_on_the_open_requests`.
    """
    by_id = {str(row.get("id") or ""): (row, body) for row, body in entries}
    blocked = [(row, body) for row, body in entries if row.get("blocked_by")]
    flight = [(row, body) for row, body in entries
              if lane(str(row.get("type") or ""), row.get("status")) == FLIGHT]
    done = [(row, body) for row, body in entries
            if lane(str(row.get("type") or ""), row.get("status")) == DONE]
    named = {request["item"]: request for request in requests if request["item"] in by_id}

    rows = {"blocked": [_focus_row(row, body, "blocked by " + blockers(row))
                        for row, body in blocked],
            "you": [], "flight": [_focus_row(row, body, "") for row, body in
                                  sorted(flight, key=lambda pair: (str(pair[0].get("type")),
                                                                   str(pair[0].get("id"))))]}
    for request in requests:
        note = "%s approval, open until %s" % (request["kind"], request["expires"])
        if request["item"] in by_id:
            row, body = by_id[request["item"]]
            rows["you"].append(_focus_row(row, body, note))
        else:
            # NO CARD TO OPEN, so no control -- but the row still names its SUBJECT the way the
            # session brief names it: the item when the request has one, the kind when it does not.
            # That is what lets the two readers be compared at all
            # (`test_board.test_the_board_and_the_session_brief_agree_on_the_open_requests`), and
            # it is a rule rather than a case: a request without an item is about its kind.
            subject = request["item"] or request["kind"]
            rows["you"].append(
                '<li><span class="rec" data-request="%s"><span class="id">%s</span> '
                '<span class="title">%s</span></span></li>'
                % (html.escape(subject, quote=True), html.escape(subject), html.escape(note)))

    examples = {
        "blocked": ("%s waits for %s" % (blocked[0][0].get("id"), blockers(blocked[0][0])))
        if blocked else FOCUS["blocked"][1],
        "you": ("%s: %s approval, open until %s"
                % (requests[0]["item"] or "no item named", requests[0]["kind"],
                   requests[0]["expires"])) if requests else FOCUS["you"][1],
        "flight": ("e.g. %s (%s)" % (flight[0][0].get("id"), flight[0][0].get("status")))
        if flight else FOCUS["flight"][1],
    }
    figures = "".join(
        '<button type="button" class="figure%s" data-focus="%s" aria-pressed="false">'
        '<span class="num">%d</span><span class="word">%s</span><span class="ex">%s</span></button>'
        % ("" if rows[key] else " zero", key, len(rows[key]), html.escape(FOCUS[key][0]),
           html.escape(examples[key]))
        for key in ("blocked", "you", "flight"))
    tail = ('<p class="done">%d finished and not yet archived — e.g. %s</p>'
            % (len(done), html.escape(str(done[0][0].get("id") or "")))) if done else ""
    lists = "".join(
        '<div class="focus-list" data-focus-list="%s" data-count="%d"><h3>%s '
        '<span class="count">%d</span></h3>%s</div>'
        % (key, len(rows[key]), html.escape(FOCUS[key][0]), len(rows[key]),
           ("<ul>%s</ul>" % "".join(rows[key])) if rows[key]
           else '<p class="empty">%s</p>' % html.escape(FOCUS[key][1]))
        for key in ("blocked", "you", "flight"))
    return ('<section class="first" aria-label="First"><p class="eyebrow">First</p>'
            '<div class="figures">%s%s</div><p class="rule">In flight is every item past its first '
            "status and not yet in a last one — a task in READY is in flight, because nobody has to "
            "do anything to it before it can be worked on.</p>%s</section>"
            % (figures, tail, lists), {item: request["kind"]
                                       for item, request in named.items()})


def _node_face(node) -> str:
    """A tree node's own line: what kind of thing it is, its id, its title, its status."""
    return ('<button type="button" class="node-face" data-open="%s">'
            '<span class="kind">%s</span> %s <span class="badge">%s</span></button>'
            % (html.escape(node.item_id, quote=True),
               html.escape(backlog_tree.label(node.item_type)),
               _face(node.row, node.body), html.escape(_column_of(node.row))))


def _branches(nodes, view, reasons) -> str:
    """The nodes and everything under them, as nested lists, each with its fold control.

    ITERATIVE, WITH AN EXPLICIT STACK, and that is not a style choice. The tree's depth is the
    items' own doing -- a chain of tasks each deriving from the last is a legal store -- and a
    recursive walk over it raises RecursionError into `state._write_board`, which catches
    everything by design: the state write survives, and the PAGE quietly keeps its previous
    content. Measured on the recursive version at two depths, both in the round's report. With the
    stack the depth costs memory instead of frames and nothing here has to guess a maximum
    (`test_board.test_a_long_chain_of_links_still_reaches_the_page`).

    THE FOLD CONTROL IS A NATIVE `<button>` and not a `<details>/<summary>`: the node's own row IS
    already a button (it opens the record), and a `summary` containing a button is invalid HTML and
    two competing click targets in one row. `hidden` on the child groups is the same mechanism the
    tabs and the records already use, so the noscript fallback un-hides all three with one rule.
    A node with no children carries a spacer of the same width instead, so the rows line up.
    `test_board.test_every_deep_group_starts_hidden_and_every_root_open`,
    `test_board.test_a_fold_control_states_what_it_hides`.
    """
    out = []
    stack = [("node", node) for node in reversed(nodes)]
    while stack:
        kind, payload = stack.pop()
        if kind == "html":
            out.append(payload)
            continue
        node = payload
        groups = node.grouped_children(view)
        folded = bool(groups) and node.depth >= FOLD_DEPTH
        if groups:
            control = ('<button type="button" class="fold" data-fold="%s" aria-expanded="%s" '
                       'aria-label="children of %s"></button>'
                       % (html.escape(node.item_id, quote=True), "false" if folded else "true",
                          html.escape(node.item_id, quote=True)))
        else:
            control = '<span class="fold-space"></span>'
        why = reasons.get(node.item_id)
        out.append('<li class="node" data-node="%s" data-node-type="%s" data-parent="%s" '
                   'data-depth="%d"><div class="row">%s%s%s</div>'
                   % (html.escape(node.item_id, quote=True),
                      html.escape(node.item_type, quote=True),
                      html.escape(node.parent.item_id if node.parent else "", quote=True),
                      node.depth, control, _node_face(node),
                      ('<span class="why" data-reason="%s">%s</span>'
                       % (html.escape(why, quote=True),
                          html.escape(backlog_tree.reason_label(why, node.item_type))))
                      if why else ""))
        follow = []
        for item_type, area, children in groups:
            # THE AREA IS PART OF THE HEADING and part of the group's identity in the markup, so a
            # person and a test see the same grouping (FR-0017). An item that names no area keeps
            # the heading it always had: the outline is optional, and a project that keeps none
            # gets the page it had before.
            follow.append(('html',
                           '<div class="group" data-group="%s" data-group-area="%s" '
                           'data-group-parent="%s" data-count="%d"%s>'
                           '<h4>%s%s <span class="count">%d</span></h4><ol>'
                           % (html.escape(item_type, quote=True),
                              html.escape(area, quote=True),
                              html.escape(node.item_id, quote=True), len(children),
                              " hidden" if folded else "",
                              html.escape(backlog_tree.label(item_type, len(children))),
                              html.escape(" — " + area) if area else "",
                              len(children))))
            follow.extend(("node", child) for child in children)
            follow.append(("html", "</ol></div>"))
        follow.append(("html", "</li>"))
        stack.extend(reversed(follow))
    return "".join(out)


def _tree_view(arrangement) -> str:
    """One hierarchical view: its roots, then everything no link could place.

    THE SECOND GROUP IS NOT CALLED "UNASSIGNED" ANY MORE, and that is DEC-0066 (5) rather than a
    word choice. An `FR` without a `related_pr` breaks no rule -- the kits treat the inbox as where
    a wish waits for triage -- so the page says what the item IS instead of what the tree could not
    do with it. The word comes from `backlog_tree.reason_label`, one per reason, so the five reasons
    stay as distinguishable on the page as they are in the warning
    (`test_board.test_the_reason_a_link_did_not_resolve_is_the_one_the_contract_gives`).
    """
    view = arrangement.view
    parts = ['<p class="lead">%s</p>' % html.escape(view.lead)]
    if arrangement.roots:
        parts.append('<div class="tree-tools">'
                     '<button type="button" data-fold-all="expand">Expand all</button>'
                     '<button type="button" data-fold-all="collapse">Collapse all</button></div>')
        parts.append('<ol class="tree" data-tree="%s">%s</ol>'
                     % (html.escape(view.key, quote=True),
                        _branches(arrangement.roots, view, arrangement.reasons)))
    else:
        parts.append('<p class="empty">no %s yet — nothing to hang this view from</p>'
                     % html.escape(" or ".join(sorted(
                         backlog_tree.label(item_type)
                         for item_type in backlog_tree.ROOT_TYPES))))
    if arrangement.unassigned:
        parts.append('<section class="unassigned" data-unassigned="%s" data-count="%d">'
                     '<h3>Not under a goal <span class="count">%d</span></h3>'
                     '<p class="lead">This view could not place these items under any item they '
                     'name — some are wishes nobody has triaged yet, some name an item this view '
                     'does not show, some name an id that is not on this board at all. Each one '
                     'says which it is; the warning above counts them per reason.</p>'
                     '<ol class="tree">%s</ol></section>'
                     % (html.escape(view.key, quote=True), len(arrangement.unassigned),
                        len(arrangement.unassigned),
                        _branches(arrangement.unassigned, view, arrangement.reasons)))
    return "".join(parts)


def _descendants(arrangement, goals) -> dict:
    """{lane: [node, ...]} for everything the system tree hangs under one of `goals`."""
    found = {NEW: [], FLIGHT: [], DONE: []}
    stack = [node for node in arrangement.roots if node.item_id in goals]
    while stack:
        node = stack.pop()
        for child in node.children:
            key = lane(child.item_type, child.row.get("status"))
            if key in found:
                found[key].append(child)
            stack.append(child)
    return found


def _milestone_date(body):
    """The calendar date a milestone names, or None when nothing readable stands there.

    A DATE THAT CANNOT BE READ IS SHOWN AS "no date" AND NEVER RAISES. `state.capture_preflight`
    refuses one at the door (DEC-0064 (3)), so this shape only ever arrives as a hand-written file
    -- which is exactly when a board may not fail the state write it is written by.
    `test_board.test_a_milestone_with_an_unreadable_date_is_shown_with_no_date`.
    """
    if not isinstance(body, dict):
        return None
    try:
        return datetime.date.fromisoformat(str(body.get("due")))
    except (TypeError, ValueError):
        return None


def _timeline_view(milestones, system, today) -> str:
    """The milestones on a date ruler, then one card each with the goals they are a date for.

    NO PERCENTAGE, and that is a consequence of a kernel rule rather than a design preference:
    archived items are not on this board, so a share would count the visible half only and read as
    progress. What stands instead is the count per lane, in words.

    THE RULER HAS THREE BANDS. The today marker owns the top one alone; a tick label that would
    stand within `LABEL_BAND_GAP` per cent of its neighbour takes the middle band instead of the
    bottom one. The design pass measured the overlap a single band produced and its absence
    afterwards, at all three widths
    (`test_board_browser.test_ruler_labels_share_no_band`,
    `test_board.test_two_milestones_a_day_apart_keep_both_labels`). ITS LIMIT IS TWO BANDS FOR
    THE TICKS: three marks inside one gap alternate bottom-middle-bottom, so the third stands where
    the first does. Re-measured in this round rather than repeated from the sheet: three marks one
    day apart overlap at 390 px and not at 1280, four give two such pairs, two give none. Widening
    the rule would need a third tick band or a per-label width and neither is built; nothing is
    lost by it, because every milestone also has a card below the ruler. The protocol of TSK-0115
    carries the figures.
    """
    dated = [(_milestone_date(body), row, body) for row, body in milestones]
    known = [date for date, _row, _body in dated if date is not None]
    anchor = today or (known[0] if known else None)
    if anchor is None:
        span_from = span_to = None
    else:
        span_from = min(known + [anchor]) - datetime.timedelta(days=7)
        span_to = max(known + [anchor]) + datetime.timedelta(days=7)
    span = max((span_to - span_from).days, 1) if span_from else 1

    def position(date):
        return 100.0 * (date - span_from).days / span

    ticks, marks, cards = [], [], []
    if today is not None and span_from is not None:
        ticks.append('<div class="today" style="--x:%.2f%%"><span>today %s</span></div>'
                     % (position(today), html.escape(today.isoformat())))
    for date, row, body in sorted(dated, key=lambda triple: (triple[0] is None, triple[0])):
        status = str(row.get("status") or "")
        reached = lane(MILESTONE_TYPE, status) == DONE
        late = date is not None and today is not None and date < today and not reached
        if date is not None and span_from is not None:
            marks.append((position(date), " late" if late else (" done" if reached else ""),
                          str(row.get("id") or "")))
        goals = [_flat(one) for one in backlog_tree.parents_of(backlog_tree.Node(row, body))]
        under = _descendants(system, set(goals))
        goal_text = ", ".join(
            '<button type="button" class="ref" data-open="%s">%s</button>'
            % (html.escape(goal, quote=True), html.escape(goal)) for goal in goals)
        counts = " · ".join("%d %s" % (len(nodes), LANE_WORDS[key])
                            for key, nodes in under.items() if nodes)
        bar = "".join('<span class="seg %s" style="--g:%d"></span>' % (key, len(nodes))
                      for key, nodes in under.items() if nodes)
        cards.append(
            '<li class="milestone%s" data-milestone="%s" data-late="%s">'
            '<button type="button" class="ms-face" data-open="%s"><span class="date">%s</span>%s'
            '<span class="badge">%s</span></button><p class="goals">for %s — %s</p>'
            '<div class="bar">%s</div></li>'
            % (" late" if late else "", html.escape(str(row.get("id") or ""), quote=True),
               "true" if late else "false", html.escape(str(row.get("id") or ""), quote=True),
               html.escape(date.isoformat() if date else "no date"), _face(row, body),
               html.escape(status), goal_text or "<em>names no goal</em>",
               html.escape(counts or "nothing under these goals yet"), bar))
    level, previous = 0, None
    for place, extra, item_id in sorted(marks):
        level = 1 - level if previous is not None and place - previous < LABEL_BAND_GAP else 0
        previous = place
        ticks.append('<div class="tick%s%s" style="--x:%.2f%%" data-milestone="%s">'
                     '<span class="id">%s</span></div>'
                     % (extra, " up" if level else "", place, html.escape(item_id, quote=True),
                        html.escape(item_id)))
    return ('<p class="lead">Every milestone is an item of its own: a date, a title and the goals '
            'it is a date for. What hangs under those goals is counted by lane — archived work is '
            'not on this board and is not counted here either.</p>'
            '<div class="ruler" data-from="%s" data-to="%s">%s</div>'
            '<ol class="milestones">%s</ol>'
            % (html.escape(span_from.isoformat() if span_from else ""),
               html.escape(span_to.isoformat() if span_to else ""),
               "".join(ticks), "".join(cards)))


def _warnings(found) -> str:
    """The banner of one view -- (type, kind, text) triples, or nothing at all."""
    if not found:
        return ""
    return '<ul class="warnings">%s</ul>' % "".join(
        '<li data-warning="%s" data-type="%s">%s: %s</li>'
        % (html.escape(kind, quote=True), html.escape(item_type, quote=True),
           html.escape(item_type), html.escape(detail))
        for item_type, kind, detail in found)


_STYLE = """:root {
  color-scheme: light dark;

  --board: #f5f5f7;        /* quiet neutral ground */
  --slot: #ebecef;         /* the empty figure, the record list ground */
  --card: #ffffff;
  --ink: #0f1115;
  --ink-2: #5b616e;
  --rule: #e2e4e8;         /* hairline */
  --stop: #d92d20;         /* blocked: field colour */
  --stop-text: #b42318;    /* blocked: as text on white */
  --stop-tint: #fee4e2;
  --stop-ink: #ffffff;
  --you: #b54708;          /* waiting on you: field colour (amber, dark enough for white type) */
  --you-text: #b54708;
  --you-tint: #fef0c7;
  --you-ink: #ffffff;
  --go: #107569;           /* in flight: field colour (teal) */
  --go-text: #107569;
  --go-tint: #d5f5ef;
  --go-ink: #ffffff;

  --font-display: "Segoe UI Variable Display", "Segoe UI Variable", Inter, "SF Pro Display", -apple-system, "Helvetica Neue", Arial, sans-serif;
  --font-head: "Segoe UI Variable Display", "Segoe UI Variable", Inter, "SF Pro Display", -apple-system, "Helvetica Neue", Arial, sans-serif;
  --font-body: "Segoe UI Variable Text", "Segoe UI Variable", Inter, "SF Pro Text", -apple-system, "Helvetica Neue", Arial, sans-serif;
  --font-mono: "Segoe UI Variable Text", "Segoe UI Variable", Inter, "SF Pro Text", -apple-system, "Helvetica Neue", Arial, sans-serif;
  --s1: .5rem; --s2: 1rem; --s3: 1.5rem; --s4: 2.5rem;
}
@media (prefers-color-scheme: dark) {

  :root { --board: #0f1115; --slot: #1b1e24; --card: #171a1f; --ink: #f3f4f6; --ink-2: #9aa1ad; --rule: #2a2f37;
          --stop: #d92d20; --stop-text: #f97066; --stop-tint: #3a1715; --stop-ink: #ffffff;
          --you: #b54708; --you-text: #fdb022; --you-tint: #3a2810; --you-ink: #ffffff;
          --go: #107569; --go-text: #2ed3b7; --go-tint: #0f2e2a; --go-ink: #ffffff; }
}

* { box-sizing: border-box; }
body { margin: 0; padding: var(--s3) clamp(12px, 3vw, 40px) var(--s4); background: var(--board); color: var(--ink);
       font: 15px/1.45 var(--font-body); }
code { font-family: var(--font-mono); font-size: .92em; }
.eyebrow { margin: 0; font: 600 .74rem/1 var(--font-head); letter-spacing: .12em; text-transform: uppercase; color: var(--ink-2); }
h1 { margin: .15rem 0 .4rem; font: 500 2rem/1.1 var(--font-head); letter-spacing: .01em; }
h2 { margin: 0; font: 500 1.25rem/1.2 var(--font-head); }
h3 { margin: 0; font: 600 .78rem/1.2 var(--font-head); letter-spacing: .08em; text-transform: uppercase; color: var(--ink-2); }
h4 { margin: .4rem 0 .2rem; font: 600 .74rem/1.2 var(--font-head); letter-spacing: .08em; text-transform: uppercase; color: var(--ink-2); }
.meta { margin: 0; max-width: 62rem; color: var(--ink-2); font-size: .9rem; }
.code { font-family: var(--font-mono); font-size: .75rem; color: var(--ink-2); margin-left: .2rem; }
.count { font: 500 .85em/1 var(--font-head); color: var(--ink-2); }

/* First: three numbers, one line, no tiles */
.first { margin: var(--s3) 0 var(--s2); border-top: 2px solid var(--ink); padding-top: var(--s1); }
.figures { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--s2); align-items: start; }
.figure { all: unset; cursor: pointer; display: grid; grid-template-columns: auto 1fr; grid-template-rows: auto auto;
          column-gap: .6rem; align-items: baseline; padding: .3rem .4rem .4rem; border-radius: 3px; }
.figure:hover, .figure:focus-visible { background: var(--slot); outline: 2px solid var(--you); outline-offset: 1px; }
.figure[aria-pressed="true"] { background: var(--ink); color: var(--board); }
.figure[aria-pressed="true"] .ex, .figure[aria-pressed="true"] .word { color: inherit; }
.figure .num { grid-row: 1 / span 2; font: 500 2.6rem/1 var(--font-head); font-variant-numeric: tabular-nums; }
.figure[data-focus="blocked"] .num { color: var(--stop); }
.figure[data-focus="you"] .num { color: var(--you); }
.figure.zero .num { color: var(--ink-2); }
.figure[aria-pressed="true"] .num { color: inherit; }
.figure .word { font: 500 1rem/1.1 var(--font-head); }
.figure .ex { font-size: .82rem; color: var(--ink-2); }
.done { grid-column: 1 / -1; margin: 0; font-size: .85rem; color: var(--ink-2); }

/* tabs */
.tabs { display: flex; flex-wrap: wrap; gap: .3rem; align-items: center; margin: var(--s2) 0 var(--s2);
        border-bottom: 1px solid var(--rule); padding-bottom: var(--s1); }
.tab { font: 500 .95rem var(--font-head); cursor: pointer; background: none; color: var(--ink-2);
       border: 0; border-bottom: 3px solid transparent; padding: .3rem .6rem; }
.tab[aria-selected="true"] { color: var(--ink); border-bottom-color: var(--ink); }
.tab:hover, .tab:focus-visible { color: var(--ink); outline: none; border-bottom-color: var(--you); }
.archived { margin-left: auto; color: var(--ink-2); font-size: .82rem; }

/* one type = one row of slots */
.type { margin: var(--s3) 0 0; }
.type h2 { display: flex; align-items: baseline; gap: .5rem; margin-bottom: .5rem; }
.name { display: inline-block; }
.name::first-letter { text-transform: uppercase; }
.empties .chain { display: none; }
.board { display: flex; gap: .5rem; overflow-x: auto; align-items: flex-start; padding: 0 0 .5rem; }
.slot { flex: 0 0 14rem; background: var(--slot); border-radius: 3px; padding: .45rem .45rem .2rem; min-height: 3rem; }
.slot.empty { flex-basis: 6.5rem; min-height: 2rem; padding-bottom: .45rem; }
.slot.empty h3 { color: var(--ink-2); opacity: .75; font-weight: 500; }
.slot.terminal { opacity: .65; }
.slot h3 { display: flex; justify-content: space-between; gap: .4rem; padding: 0 .15rem .4rem; }
.empties { margin: 0 0 .4rem; font-size: .82rem; color: var(--ink-2); }

/* the T-card: a head that overhangs the body */
.card { all: unset; cursor: pointer; display: block; width: 100%; margin: 0 0 .5rem; padding: 0 0 .5rem;
        background: var(--card); border-radius: 2px; box-shadow: 0 0 0 1px var(--rule); }
.card .head { display: block; margin: 0 -.25rem .35rem; padding: .25rem .5rem; background: var(--ink); color: var(--board);
              border-radius: 2px 2px 0 0; font: 500 .78rem/1.2 var(--font-mono); }
.card .head .flag { display: block; font: 600 .74rem/1.2 var(--font-head); letter-spacing: .04em; margin-top: .15rem; }
.card.blocked .head { background: var(--stop); color: var(--stop-ink); }
.card.you .head { background: var(--you); color: var(--you-ink); }
.card .title { display: block; padding: 0 .5rem; font-size: .92rem; line-height: 1.35; overflow-wrap: anywhere; }
.card .title em { color: var(--ink-2); }
.card:hover, .card:focus-visible, .rec:hover, .node-face:hover { box-shadow: 0 0 0 2px var(--you); }
body[data-focus="blocked"] .card:not(.blocked), body[data-focus="you"] .card:not(.you) { opacity: .22; }
body[data-focus="flight"] .card:not([data-lane="flight"]) { opacity: .22; }
.focus-list { display: none; margin: var(--s2) 0 0; padding: var(--s1) var(--s2) var(--s2); background: var(--slot); border-radius: 3px; }
body[data-focus="blocked"] [data-focus-list="blocked"], body[data-focus="you"] [data-focus-list="you"],
body[data-focus="flight"] [data-focus-list="flight"] { display: block; }
.focus-list ul { list-style: none; margin: .3rem 0 0; padding: 0; columns: 30rem; column-gap: var(--s2); }
.focus-list .rec { display: grid; grid-template-columns: auto 1fr auto; gap: .5rem; align-items: baseline; padding: .2rem .3rem; }
.focus-list .rec .note { grid-column: 2 / -1; font-size: .8rem; color: var(--ink-2); }
[data-focus-list="blocked"] .rec .id { color: var(--stop); font-weight: 600; }
[data-focus-list="you"] .rec .id { color: var(--you); font-weight: 600; }

/* records: paperwork, listed and closed by default */
.records { margin: var(--s4) 0 0; border-top: 1px solid var(--rule); padding-top: var(--s2); }
.records summary { cursor: pointer; font: 500 1.1rem var(--font-head); }
.records summary .sum { font: .85rem var(--font-body); color: var(--ink-2); margin-left: .5rem; }
.records-type { margin: var(--s2) 0 0; }
.records-type ul { list-style: none; margin: 0; padding: 0; columns: 22rem; column-gap: var(--s2); }
.rec { all: unset; cursor: pointer; display: block; padding: .15rem .3rem; border-radius: 2px; font-size: .88rem; break-inside: avoid; }
.rec .id, .node-face .id, .detail .id { font: .78rem var(--font-mono); color: var(--ink-2); }
.silent { margin: var(--s3) 0 0; color: var(--ink-2); font-size: .85rem; }
.nothing { margin: var(--s2) 0; font: 500 1.15rem/1.4 var(--font-head); max-width: 40rem; }

/* trees: the kernel's markup, restyled */
.lead { margin: .2rem 0 var(--s2); max-width: 62rem; color: var(--ink-2); }
.tree, .tree ol { list-style: none; margin: 0; padding: 0; }
.tree .group { margin: 0 0 .3rem 1.2rem; border-left: 2px solid var(--rule); padding-left: .7rem; }
.node { margin: .2rem 0; }
.node-face { all: unset; cursor: pointer; display: grid; grid-template-columns: auto auto 1fr auto; gap: .5rem; align-items: baseline;
             width: 100%; background: var(--card); border-radius: 2px; box-shadow: 0 0 0 1px var(--rule); padding: .3rem .55rem; }
.node-face .kind { font: 600 .68rem var(--font-head); letter-spacing: .06em; text-transform: uppercase; color: var(--ink-2); }
.node-face .badge, .detail .badge, .rec .badge { font: .72rem var(--font-mono); border: 1px solid var(--rule); border-radius: 2px; padding: 0 .35rem; }
.unassigned { margin: var(--s3) 0 0; border-top: 2px solid var(--stop); padding-top: var(--s1); }
.warnings { margin: 0 0 var(--s2); padding: .5rem .8rem .5rem 1.6rem; border-left: 3px solid var(--stop); background: var(--slot); font-size: .88rem; }
.empty { color: var(--ink-2); font-style: italic; }
/* `all: unset` resets box-sizing to content-box; with horizontal padding a 100 %-wide control then
   overhangs its slot -- measured in phase 1d: 18 px into the neighbouring slot at 1280, 110 pairs */
.card, .figure, .rec, .node-face, .ms-face, .fold, .tree-tools button { box-sizing: border-box; }
/* collapsible trees (phase 1d) */
.row { display: flex; gap: .4rem; align-items: flex-start; }
.node-face { flex: 1 1 auto; }
.fold { all: unset; box-sizing: border-box; cursor: pointer; flex: 0 0 auto; width: 1.7rem; height: 1.9rem; display: flex;
        align-items: center; justify-content: center; border-radius: 4px; color: var(--ink-2); font-size: .8rem; }
.fold::before { content: "▾"; }
.fold[aria-expanded="false"]::before { content: "▸"; }
.fold:hover, .fold:focus-visible { background: var(--slot); outline: 2px solid var(--ink); outline-offset: 1px; }
.fold-space { flex: 0 0 auto; width: 1.7rem; }
.tree-tools { display: flex; gap: .5rem; margin: 0 0 .8rem; }
.tree-tools button { all: unset; box-sizing: border-box; cursor: pointer; font: 500 .8rem var(--font-body); padding: .3rem .6rem;
                     border: 1px solid var(--rule); border-radius: 4px; color: var(--ink); }
.tree-tools button:hover, .tree-tools button:focus-visible { outline: 2px solid var(--ink); outline-offset: 1px; }

/* timeline (FR-0079, TYPE option) */
.ruler { position: relative; height: 4.2rem; margin: var(--s2) 0 var(--s2); border-bottom: 2px solid var(--ink); }
.ruler .tick { position: absolute; bottom: -2px; height: 1.6rem; border-left: 2px solid var(--ink); }
.ruler .tick .id { position: absolute; left: .3rem; bottom: .2rem; white-space: nowrap; font: .74rem var(--font-mono); }
.ruler .tick.up { height: 3rem; }
.ruler .tick.up .id { bottom: auto; top: .05rem; }
.ruler .tick.late { border-color: var(--stop); } .ruler .tick.late .id { color: var(--stop); }
.ruler .tick.done { opacity: .5; }
.ruler .today { position: absolute; top: 0; bottom: -2px; border-left: 2px dashed var(--you); }
.ruler .today span { position: absolute; left: .3rem; top: 0; white-space: nowrap; font: 600 .74rem var(--font-head); color: var(--you); letter-spacing: .06em; text-transform: uppercase; }
.milestones { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--s2); grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr)); }
.milestone { background: var(--card); box-shadow: 0 0 0 1px var(--rule); border-radius: 2px; padding: 0 0 .6rem; }
.milestone.late { box-shadow: 0 0 0 2px var(--stop); }
.ms-face { all: unset; cursor: pointer; display: grid; grid-template-columns: auto 1fr auto; gap: .4rem .6rem; align-items: baseline; width: 100%; padding: .4rem .6rem; }
.ms-face .date { grid-column: 1 / -1; font: 500 1.4rem/1 var(--font-head); font-variant-numeric: tabular-nums; }
.milestone.late .ms-face .date { color: var(--stop); }
.ms-face .title { font-size: .95rem; }
.goals { margin: 0; padding: 0 .6rem; font-size: .82rem; color: var(--ink-2); }
.bar { display: flex; height: .45rem; margin: .5rem .6rem 0; background: var(--slot); border-radius: 2px; overflow: hidden; }
.bar .seg.new { background: var(--rule); } .bar .seg.flight { background: var(--ink-2); } .bar .seg.done { background: var(--ink); }

/* the record (detail) */
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); padding: 3vh 2vw; overflow: auto; }
.dialog { max-width: 58rem; margin: 0 auto; background: var(--card); color: var(--ink); border-radius: 3px;
          box-shadow: 0 0 0 1px var(--rule); padding: var(--s2) var(--s3) var(--s3); }
.dialog .close { float: right; font: 500 .9rem var(--font-head); cursor: pointer; color: var(--ink); background: var(--slot);
                 border: 0; border-radius: 2px; padding: .3rem .7rem; }
.detail header { display: grid; grid-template-columns: auto 1fr auto auto; gap: .6rem; align-items: baseline;
                 border-bottom: 2px solid var(--ink); padding: 0 0 .5rem; }
.detail h2 { margin: 0; font-size: 1.25rem; }
.detail .kind { font: 600 .7rem var(--font-head); letter-spacing: .06em; text-transform: uppercase; color: var(--ink-2); }
.detail dl { display: grid; grid-template-columns: max-content 1fr; gap: .25rem 1rem; margin: var(--s2) 0 0; font-size: .92rem; }
.detail dt { font: 600 .74rem/1.6 var(--font-head); letter-spacing: .06em; text-transform: uppercase; color: var(--ink-2); }
.detail dd { margin: 0; overflow-wrap: anywhere; }
.ref { all: unset; cursor: pointer; font: .85em var(--font-mono); color: var(--you); text-decoration: underline; text-underline-offset: 2px; }

@media (max-width: 720px) {
  body { padding: var(--s2) 12px var(--s3); }
  h1 { font-size: 1.6rem; }
  .figures { gap: .5rem; }
  .figure { grid-template-columns: 1fr; padding: .2rem; }
  .figure .num { grid-row: auto; font-size: 2rem; }
  .figure .ex { display: none; }
  .board { flex-direction: column; overflow: visible; }
  .slot { flex-basis: auto; width: 100%; }
  .slot.empty { display: none; }
  .empties .chain { display: inline; }
  .focus-list ul { columns: 1; }
  .archived { margin-left: 0; width: 100%; }
  .records-type ul { columns: 1; }
  .node-face { grid-template-columns: auto 1fr; }
  .node-face .kind { grid-column: 1 / -1; }
  .detail header { grid-template-columns: 1fr; }
}

body { font-size: 14px; line-height: 1.5; }
h1 { font: 600 1.75rem/1.2 var(--font-display); letter-spacing: -.02em; margin: .1rem 0 .5rem; }
h2 { font: 600 1.05rem/1.3 var(--font-display); letter-spacing: -.01em; }
h3, h4 { text-transform: none; letter-spacing: 0; font: 500 .8rem/1.3 var(--font-body); color: var(--ink-2); }
.eyebrow { text-transform: uppercase; letter-spacing: .08em; font: 600 .68rem/1 var(--font-body); }
.meta, .lead { font-size: .875rem; }
.code, .id, .rec .id, .node-face .id, .detail .id { font-family: var(--font-body); font-variant-numeric: tabular-nums; font-weight: 500; }
.count { font: 500 .8em/1 var(--font-body); }
.first { border-top: 0; padding-top: 0; margin: var(--s3) 0 var(--s2); }
.figures { gap: var(--s2); }
.figure { border-radius: 4px; padding: .7rem .9rem .8rem; column-gap: .7rem; }
.figure .num { font: 600 2.4rem/1 var(--font-display); letter-spacing: -.03em; font-variant-numeric: tabular-nums; }
.figure .word { font: 600 .95rem/1.2 var(--font-body); }
.figure .ex { font-size: .8rem; }
.tabs { border-bottom: 1px solid var(--rule); gap: .1rem; padding-bottom: 0; }
.tab { font: 500 .9rem var(--font-body); padding: .5rem .8rem; border-bottom: 2px solid transparent; border-radius: 0; margin-bottom: -1px; }
.tab[aria-selected="true"] { border-bottom-color: var(--ink); color: var(--ink); }
.tab:hover, .tab:focus-visible { border-bottom-color: var(--ink-2); }
.archived { font-size: .8rem; }
.type { margin-top: var(--s4); }
/* fluid: a slot with cards grows into the width the window has; an empty chain slot stays narrow.
   Rows with more slots than fit still scroll (min-width holds the column readable). */
.slot { background: transparent; padding: 0; border-radius: 0; flex: 1 1 15rem; min-width: 15rem; }
.slot.empty { flex: 0 0 7rem; min-width: 0; }
/* in the stacked (column) layout a 15rem flex-basis becomes a HEIGHT and the slot shrinks under its
   cards -- measured phase 1d: 327 vertical overlaps at 390 px; the basis goes back to auto there */
@media (max-width: 720px) { .slot { flex: 0 0 auto; min-width: 0; width: 100%; } }
.slot h3 { padding: 0 .1rem .5rem; justify-content: flex-start; gap: .4rem; }
.slot.empty { flex-basis: 7rem; }
.slot.empty h3 { opacity: .6; font-weight: 500; }
.slot.terminal { opacity: .7; }
.card { border-radius: 4px; box-shadow: none; border: 1px solid var(--rule); background: var(--card);
        margin-bottom: .5rem; padding: .6rem .75rem .7rem; }
.card .head { margin: 0 0 .25rem; padding: 0; background: transparent; color: var(--ink-2); font: 500 .75rem/1.3 var(--font-body);
              display: flex; flex-wrap: wrap; gap: .2rem .6rem; align-items: baseline; border-radius: 0; }
.card .head .flag { margin: 0; font: 600 .75rem/1.3 var(--font-body); letter-spacing: 0; }
/* the phase-1 sheet fills the head of a signalled card; modern signals by bar (D) or tint (E), never
   by a solid band across the card (sighted 1c-1: BUG-0083 carried an amber band in both) */
.card.blocked .head, .card.you .head { background: transparent; box-shadow: none; }
.card .title { padding: 0; font-size: .9rem; line-height: 1.4; }
.card:hover, .card:focus-visible, .node-face:hover, .rec:hover { box-shadow: 0 0 0 2px var(--ink); }
.node-face, .dialog, .focus-list, .rec { border-radius: 4px; }
.node-face { box-shadow: none; border: 1px solid var(--rule); }
.node-face .kind { text-transform: none; letter-spacing: 0; font: 500 .72rem var(--font-body); }
.badge, .node-face .badge, .detail .badge, .rec .badge { border-radius: 3px; border: 1px solid var(--rule); font: 500 .72rem var(--font-body); }
.focus-list { background: var(--card); border: 1px solid var(--rule); }
.dialog { box-shadow: none; border: 1px solid var(--rule); }
.dialog .close { border-radius: 4px; font: 500 .85rem var(--font-body); }
.detail header { border-bottom: 1px solid var(--rule); }
.detail .kind { text-transform: none; letter-spacing: 0; font: 500 .75rem var(--font-body); }
.detail dt { text-transform: none; letter-spacing: 0; font: 500 .8rem/1.6 var(--font-body); }
.records { border-top: 1px solid var(--rule); }
.records summary { font: 600 1rem var(--font-display); }
.records summary .sum { font: .8rem var(--font-body); }
.warnings { border-radius: 4px; background: var(--card); border: 1px solid var(--rule); border-left: 3px solid var(--stop); font-size: .85rem; }
.unassigned { border-top: 0; border-left: 3px solid var(--stop); border-radius: 0; padding: 0 0 0 var(--s2); }
.ref { color: var(--ink); font-family: var(--font-body); }
.empties, .silent { font-size: .8rem; }
.ruler .tick .id, .ruler .today span { font-family: var(--font-body); }
@media (max-width: 720px) {
  .figures { grid-template-columns: 1fr; gap: .5rem; }
  .figure { grid-template-columns: auto 1fr; padding: .5rem .8rem; }
  .figure .num { grid-row: 1 / span 2; font-size: 2rem; }
  .figure .ex { display: block; }
}

/* E: the signal is the surface itself -- the three figures are colour fields, a signalled card is tinted */
.figure { background: var(--slot); color: var(--ink); }
.figure[data-focus="blocked"]:not(.zero) { background: var(--stop); color: var(--stop-ink); }
.figure[data-focus="you"]:not(.zero) { background: var(--you); color: var(--you-ink); }
.figure[data-focus="flight"]:not(.zero) { background: var(--go); color: var(--go-ink); }
.figure[data-focus="blocked"] .num, .figure[data-focus="you"] .num, .figure[data-focus="flight"] .num,
.figure .word, .figure .ex { color: inherit; }
.figure.zero .num { color: var(--ink-2); }
.figure:hover, .figure:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; background: var(--slot); }
.figure[data-focus="blocked"]:not(.zero):hover, .figure[data-focus="blocked"]:not(.zero):focus-visible { background: var(--stop); }
.figure[data-focus="you"]:not(.zero):hover, .figure[data-focus="you"]:not(.zero):focus-visible { background: var(--you); }
.figure[data-focus="flight"]:not(.zero):hover, .figure[data-focus="flight"]:not(.zero):focus-visible { background: var(--go); }
.figure[aria-pressed="true"] { outline: 3px solid var(--ink); outline-offset: 2px; }
.card.blocked { background: var(--stop-tint); border-color: var(--stop); }
.card.blocked .head { color: var(--stop-text); }
.card.blocked .head .flag { background: var(--stop); color: var(--stop-ink); padding: .05rem .4rem; border-radius: 3px; }
.card.you { background: var(--you-tint); border-color: var(--you); }
.card.you .head { color: var(--you-text); }
.card.you .head .flag { background: var(--you); color: var(--you-ink); padding: .05rem .4rem; border-radius: 3px; }
[data-focus-list="blocked"] .rec { background: var(--stop-tint); }
[data-focus-list="you"] .rec { background: var(--you-tint); }
[data-focus-list="flight"] .rec { background: var(--go-tint); }
[data-focus-list="blocked"] .rec .id { color: var(--stop-text); }
[data-focus-list="you"] .rec .id { color: var(--you-text); }
[data-focus-list="flight"] .rec .id { color: var(--go-text); }
.records .rec { background: transparent; }

/* ---- phase 2: what the shipped renderer needs beyond the design sheet ---- */
/* Position on the ruler and share of a bar come from the DATA, and they are handed to CSS as
   CUSTOM PROPERTIES rather than as `style="left:…"`. An attribute VALUE beginning `word:` is what
   `test_board.test_the_page_carries_no_event_handler_and_no_link_out_of_itself` reads as a URL
   scheme -- that check is the page's javascript:-URL defence and it may not be weakened for a
   layout. A `--x` value cannot be read as a scheme. */
.ruler .tick, .ruler .today { left: var(--x); }
.bar .seg { flex-grow: var(--g); }
/* An item with nothing to show on its face says so, and says it OUTSIDE `.title`: a placeholder
   inside that element is a title as far as any reader of the page is concerned. */
.untitled { color: var(--ink-2); font-style: italic; font-size: .9rem; }
/* Why the tree could not place an item, on the item's own row (DEC-0066 (5)). */
.why { flex: 0 0 auto; align-self: center; font: 500 .72rem/1.3 var(--font-body);
       color: var(--ink-2); border: 1px solid var(--rule); border-radius: 3px;
       padding: .05rem .4rem; white-space: nowrap; }
/* The rule behind the third number, on the page rather than in a docstring (DEC-0065 (4)). */
.rule { margin: .5rem 0 0; font-size: .8rem; color: var(--ink-2); max-width: 62rem; }
/* A title in this repo is regularly a PATH -- one word of seventy-odd characters with no break
   opportunity in it -- and a grid track sized `auto` will not shrink below its content's
   MIN-CONTENT width. So without a place to break, one such row pushes the whole DOCUMENT wider
   than the window and the page gets a horizontal scrollbar. The CARD already had this rule from
   the design sheet above and is deliberately not repeated here -- one selector, one place, or the
   next reader has to find out which of the two wins; the tree faces, the focus rows and the
   milestone faces had no such rule at all. `min-width: 0` on the same tracks was tried beside this
   and measured to change nothing once the word may break, so it is not here either: a line that
   carries no fix is a line the next reader trusts. The measurement is
   `test_board_browser.test_a_title_that_is_one_long_word_does_not_widen_the_page`, over the
   DOCUMENT rather than over an element -- a track that GROWS reports no overflow of its own, which
   is why the design pass's probe saw nothing here. */
.node-face .title, .rec .title, .rec .note, .ms-face .title, .goals {
  overflow-wrap: anywhere; }
/* Jump marks to the type rows and to the records block. */
nav.types { display: flex; flex-wrap: wrap; gap: .1rem .9rem; margin: var(--s2) 0 0;
            font-size: .82rem; }
nav.types a { color: var(--ink-2); text-decoration: none; border-bottom: 1px solid var(--rule); }
nav.types a:hover, nav.types a:focus-visible { color: var(--ink); border-bottom-color: var(--ink); }
@media (max-width: 720px) { .why { white-space: normal; } }
"""

# The fallback when the browser runs no script: every view, every folded branch and every item
# detail becomes visible, so the file degrades into the one long page FR-0030 shipped rather than
# into a board with a dead tab strip, closed branches out of reach and cards whose records never
# open. It is an author rule with `!important`, which is what lets it beat the `hidden` attribute
# the renderer writes (the browser's own `[hidden] { display: none }`).
#
# THE CONTROLS THAT WOULD THEN DO NOTHING ARE HIDDEN, and that is about a SENTENCE as much as a
# layout: the tabs, the fold buttons, the "Expand all" pair and the three focus figures are all
# controls whose whole effect is script; left standing they would claim a behaviour the page no
# longer has. `.interactive` is the same rule applied to the header's own sentence. Both directions
# are read out of the rendered page by
# `test_board.test_the_noscript_page_shows_every_group_and_no_fold_control`.
_NOSCRIPT_STYLE = """
[hidden] { display: block !important; }
.tabs, .dialog .close, .interactive, .fold, .tree-tools, .figures, .focus-list {
  display: none !important; }
.overlay { position: static !important; background: none !important; padding: 0 !important; }
.detail { border-top: 1px solid var(--rule); margin-top: 1rem; }
"""

# The whole of the page's behaviour. A CONSTANT: no item content is interpolated into it, which is
# why a `</script>` in a hostile title is impossible here rather than escaped. It moves the `hidden`
# attribute, the `aria-selected`/`aria-expanded` state and one `data-focus` on `<body>`, and does
# nothing else -- no fetch, no navigation, no storage, no element it creates from a string. The
# focus dimming is CSS reading that one attribute, so no item is touched by script even there.
_SCRIPT = """
(function () {
  var overlay = document.querySelector('.overlay');
  var details = document.querySelectorAll('[data-detail]');
  var views = document.querySelectorAll('[data-view]');
  var tabs = document.querySelectorAll('[data-tab]');
  var figures = document.querySelectorAll('[data-focus]');
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
  function focus(key) {
    var on = document.body.getAttribute('data-focus') === key;
    document.body.removeAttribute('data-focus');
    if (!on) { document.body.setAttribute('data-focus', key); }
    for (var i = 0; i < figures.length; i++) {
      figures[i].setAttribute('aria-pressed',
        (!on && figures[i].getAttribute('data-focus') === key) ? 'true' : 'false');
    }
  }
  function fold(button, open) {
    var node = button.parentNode;
    while (node && !(node.classList && node.classList.contains('node'))) {
      node = node.parentNode;
    }
    if (!node) { return; }
    for (var i = 0; i < node.children.length; i++) {
      if (node.children[i].classList.contains('group')) { node.children[i].hidden = !open; }
    }
    button.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  function foldAll(el) {
    var wanted = el.getAttribute('data-fold-all') === 'expand';
    var scope = el;
    while (scope && !(scope.hasAttribute && scope.hasAttribute('data-view'))) {
      scope = scope.parentNode;
    }
    var buttons = (scope || document).querySelectorAll('[data-fold]');
    for (var i = 0; i < buttons.length; i++) { fold(buttons[i], wanted); }
  }
  document.addEventListener('click', function (event) {
    var node = event.target;
    while (node && node.getAttribute) {
      if (node.hasAttribute('data-open')) { open(node.getAttribute('data-open')); return; }
      if (node.hasAttribute('data-close')) { close(); return; }
      if (node.hasAttribute('data-tab')) { close(); show(node.getAttribute('data-tab')); return; }
      if (node.hasAttribute('data-focus')) { focus(node.getAttribute('data-focus')); return; }
      if (node.hasAttribute('data-fold')) {
        fold(node, node.getAttribute('aria-expanded') !== 'true');
        return;
      }
      if (node.hasAttribute('data-fold-all')) { foldAll(node); return; }
      node = node.parentNode;
    }
    if (event.target === overlay) { close(); }
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') { close(); }
  });
})();
"""

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Backlog board</title>
<style>%(style)s</style>
<noscript><style>%(noscript)s</style></noscript>
</head>
<body>
<header class="top">
<p class="eyebrow">Backlog</p>
<h1>Backlog board</h1>
<p class="meta">Rebuilt by the state kernel together with <code>index.yaml</code>, on every state
write the kernel makes — <time data-generated-at="%(stamp_attr)s">%(stamp)s</time>. A rebuild that
fails says so on the error output of the command that triggered it and leaves this page as it was,
so compare that stamp with what you expect. It reports, it never sets: this page is regenerated
output and holds no state of its own. <span class="interactive">A click on any card, tree row or
milestone opens that item's full record, and every id inside it that this board holds opens in
turn.</span> Shown is every item in a type's <code>active</code> directory; an archived item is not
on this board.</p>
<noscript><p class="meta">This browser runs no scripts, so the tabs, the fold controls and the
three figures above would do nothing. Instead this page shows everything at once: those controls
are hidden, every view stands one after another with every branch open, and every item's full
record is open under the board.</p></noscript>
</header>
%(first)s
<nav class="tabs" role="tablist">%(tabs)s</nav>
<main>
%(views)s
</main>
<div class="overlay" hidden><div class="dialog" role="dialog" aria-modal="true">
<button type="button" class="close" data-close>Close</button>%(details)s</div></div>
<script>%(script)s</script>
</body>
</html>
"""


def render(state, entries, generated_at: str) -> str:
    """The whole board as one dependency-free HTML page.

    `entries` are (index row, item body or None) pairs -- the rows the caller has just written into
    `generated/index.yaml` and the bodies it read on the way, so the board reports exactly the state
    the index reports and costs no second parse of the store.

    A type is on the page when the state has a home for it OR an entry names it: the first is the
    kit's own set of types, the second is what makes an item impossible to lose, whatever type it
    turns out to carry. A type with no entries keeps its NAME on the page (the silent line) rather
    than an empty row of slots.

    THE ITEM DETAILS ARE RENDERED ONCE, at the end, and every card, tree node, focus row and
    milestone face is a control that opens one of them. So an item shown in four views still has
    ONE record on the page, and the fields of an item live in exactly one place no matter how many
    views place it.
    """
    now, today = _clock(generated_at)
    grouped: dict = {}
    for row, body in entries:
        grouped.setdefault(str(row.get("type") or "?"), []).append((row, body))
    types = sorted(set(types_present(state)) | set(grouped))
    living, records = type_order(types)

    strip, awaited = _first_strip(entries, open_requests(state, now))

    def flags_of(row):
        flags = {}
        if row.get("blocked_by"):
            flags["blocked"] = True
        if str(row.get("id") or "") in awaited:
            flags["you"] = awaited[str(row.get("id") or "")]
        return flags

    board_warnings = []
    for item_type in types:
        board_warnings += _column_warnings(item_type, grouped.get(item_type, []))
    sections = [_section(item_type, grouped[item_type], flags_of)
                for item_type in living if grouped.get(item_type)]

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

    silent = [item_type for item_type in types if not grouped.get(item_type)]
    silent_line = ('<p class="silent">No entries yet: %s</p>' % ", ".join(
        '<span data-silent="%s">%s (%s)</span>'
        % (html.escape(item_type, quote=True), html.escape(backlog_tree.label(item_type, 2)),
           html.escape(item_type)) for item_type in silent)) if silent else ""
    nothing = ('<p class="nothing">Nothing captured yet. The first item comes from '
               "<code>python scripts/harness.py capture</code>; this page is rebuilt with every "
               "state write the kernel makes.</p>") if not entries else ""
    anchors = [(item_type, "type-" + item_type, backlog_tree.label(item_type, 2),
                len(grouped.get(item_type, [])))
               for item_type in living if grouped.get(item_type)]
    if any(grouped.get(item_type) for item_type in records):
        anchors.append(("records", "records", "records",
                        sum(len(grouped.get(item_type, [])) for item_type in records)))
    type_nav = ('<nav class="types">%s</nav>' % "".join(
        '<a href="#%s">%s (%d)</a>' % (html.escape(anchor, quote=True), html.escape(name), count)
        for _key, anchor, name, count in anchors)) if anchors else ""

    views = ['<div class="view" data-view="board">%s%s%s%s%s%s</div>'
             % (_warnings(board_warnings), nothing, type_nav, "\n".join(sections),
                _records_section(records, grouped), silent_line)]
    tabs = [("board", "Board", len(entries))]
    arrangements = {}
    for view in backlog_tree.VIEWS:
        arrangement = backlog_tree.arrange(view, entries)
        arrangements[view.key] = arrangement
        views.append('<div class="view" data-view="%s" hidden>%s%s</div>'
                     % (html.escape(view.key, quote=True),
                        _warnings([(item_type, kind, detail)
                                   for kind, item_type, detail in arrangement.warnings]),
                        _tree_view(arrangement)))
        tabs.append((view.key, view.label, arrangement.placed + len(arrangement.unassigned)))

    # THE TIMELINE TAB EXISTS WHEN THERE ARE MILESTONES, and not before: a tab for zero milestones
    # is an empty promise, and the design pass sighted exactly that (08-final.md, §3).
    milestones = grouped.get(MILESTONE_TYPE, [])
    if milestones:
        views.append('<div class="view" data-view="timeline" hidden>%s</div>'
                     % _timeline_view(milestones,
                                      arrangements[backlog_tree.VIEWS[-1].key], today))
        tabs.append(("timeline", "Timeline", len(milestones)))

    archived = archived_counts(state)
    strip_tabs = "".join(
        '<button type="button" class="tab" data-tab="%s" aria-selected="%s">%s '
        '<span class="count">%d</span></button>'
        % (html.escape(key, quote=True), "true" if key == "board" else "false",
           html.escape(label), count)
        for key, label, count in tabs)
    strip_tabs += ('<span class="archived" data-archived="%d">archived, not on this board: %d%s'
                   "</span>"
                   % (sum(archived.values()), sum(archived.values()),
                      (" (%s)" % ", ".join("%s %d" % (item_type, count)
                                           for item_type, count in sorted(archived.items())))
                      if archived else ""))

    return _PAGE % {
        "style": _STYLE, "noscript": _NOSCRIPT_STYLE, "script": _SCRIPT,
        "stamp_attr": html.escape(str(generated_at), quote=True),
        "stamp": html.escape(str(generated_at)),
        "first": strip, "tabs": strip_tabs, "views": "\n".join(views),
        "details": "".join(details),
    }
