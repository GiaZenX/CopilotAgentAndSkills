"""The two hierarchical backlog views the board renders beside its columns (FR-0053, TSK-0079).

WHY A SIBLING OF `board` AND NOT A PART OF IT. `board` turns state into HTML. This file answers a
question about the STATE MODEL -- which item hangs under which other item -- and answers it against
`backlog_types` alone. There is no markup here, so the placement rule can be read, and attacked,
without reading a page template; and `board` stays the one place that escapes.

THE BOARD NEVER INVENTS A LINK. This is the property FR-0053 is written around and the whole
placement is built from it: a parent is only ever an id the child's OWN binding field names, and
which fields bind is `backlog_types.PARENT_FIELDS` -- derived there from both field contracts, never
listed here. An item whose binding resolves to nothing is neither dropped nor guessed at: it lands
in the view's `unassigned` list together with the REASON its binding did not resolve, which the page
renders as a visible group plus a warning. That is the FR-0030 nothing-vanishes property carried
into the trees, and it is measured on the rendered page by
`test_board.test_an_item_the_tree_cannot_place_is_visible_with_the_reason`.

WHICH TYPES A VIEW SHOWS IS A CURATION AND IS THEREFORE WRITTEN DOWN. No property in the kernel
tells "customer language" from "system language" -- FR-0053 decides it, and a decision is written
once, in `_VIEWS` below, with the tripwire that measures BOTH of its ends:
`test_board.test_every_type_that_moves_through_a_lifecycle_is_placed_by_a_backlog_view` fails on a
type listed here that the kernel does not have (a dead entry) AND on a type with an automaton that
no view shows (an entry somebody owed). What is NOT curated is the ROOT of a tree: that follows the
kit, see `ROOT_TYPES`.
"""
from __future__ import annotations

from collections import namedtuple

from .backlog_types import (
    ACTIVE_DIRS,
    AREA_FIELD,
    AREA_SEPARATOR,
    DECLARED_REQUIRED_FIELDS,
    PARENT_FIELDS,
    ROOT_TYPE_BY_KIT,
    area_segments,
    field_elements,
)

# The types a backlog TREE hangs from -- the item a project belongs to, per kit, plus the office
# kit's procedures. `ROOT_TYPE_BY_KIT` is the derivation for dev and research (PR / RQ); the office
# kit is deliberately absent from that map because it seeds no root item at onboarding and is led by
# its procedures instead, so PROC is the one addition and it carries its reason here rather than
# being a fourth spelling of "the office kit is different". Every kit ships at least one of these
# directories, which is what keeps a kit from rendering two rootless trees
# (`test_board.test_every_kit_ships_a_type_its_backlog_trees_can_hang_from`).
ROOT_TYPES = frozenset(ROOT_TYPE_BY_KIT.values()) | {"PROC"}

# What a type is CALLED, in plain language -- (singular, plural). The product view exists to be read
# by somebody who did not write the item, so its nodes say "request" rather than "FR"; the id stands
# beside the name for everyone who wants the file.
#
# EVERY type the kernel has is in here, not only the ones a tree places: since FR-0075 the board
# heads each of its rows and each block of paperwork with this name, so a type missing here would
# appear as its own code and a name here for a type the kernel does not have would be a promise
# nobody keeps. Both ends are measured by
# `test_board.test_every_type_the_kernel_has_carries_a_plain_language_name`.
_LABELS = {
    "PR": ("product requirement", "product requirements"),
    "RQ": ("research question", "research questions"),
    "PROC": ("procedure", "procedures"),
    "FR": ("request", "requests"),
    "CR": ("change request", "change requests"),
    "SR": ("system requirement", "system requirements"),
    "HYP": ("hypothesis", "hypotheses"),
    "EXP": ("experiment", "experiments"),
    "BUG": ("bug", "bugs"),
    "TSK": ("task", "tasks"),
    "DEC": ("decision", "decisions"),
    "EVD": ("evidence record", "evidence records"),
    "APR": ("approval", "approvals"),
    "INV": ("invariant", "invariants"),
    "ARC": ("architecture diagram", "architecture diagrams"),
    "WFR": ("wireframe", "wireframes"),
    "DSN": ("design revision", "design revisions"),
    "MST": ("milestone", "milestones"),
}

View = namedtuple("View", "key label lead children")

# The curation, and the whole of it. `children` is also the ORDER the groups appear in under a
# parent, so a reader meets the contract (SR) before the work (TSK).
VIEWS = (
    View(
        key="product",
        label="Product backlog",
        lead="What the project owes the people it is for: every product requirement with the "
             "requests and change requests that hang from it. No tasks — this view is the "
             "conversation with the user, not the work plan.",
        children=("FR", "CR", "MST"),
    ),
    View(
        key="system",
        label="System backlog",
        lead="The same roots seen from the build side: the system requirements under a root, the "
             "bugs recorded against it, and every task under the item it was cut from.",
        children=("SR", "HYP", "EXP", "BUG", "TSK"),
    ),
)


def view_types(view: View) -> tuple:
    """Every item type this view places -- its roots, then its own children in their order."""
    return tuple(sorted(ROOT_TYPES)) + tuple(view.children)


def label(item_type: str, count: int = 1) -> str:
    """The plain-language name of a type, or the type itself when nothing named it."""
    names = _LABELS.get(item_type)
    if names is None:
        return item_type
    return names[0] if count == 1 else names[1]


class Node:
    """One item in a tree, and the items placed under it.

    The item BODY travels with the node: the page renders the item's own fields from it, and
    `parents_of` reads its binding fields there -- an index row carries a status and a title, never
    a reference.
    """

    __slots__ = ("row", "body", "item_id", "item_type", "depth", "parent", "children")

    def __init__(self, row, body):
        self.row, self.body = row, body
        self.item_id = str(row.get("id") or "")
        self.item_type = str(row.get("type") or "")
        self.depth, self.parent, self.children = 0, None, []

    def grouped_children(self, view: View) -> list:
        """[(type, area, [node, ...]), ...] -- the children of this node, per type and per area.

        GROUPED BY TYPE RATHER THAN "the bugs get a group of their own": FR-0053 asks for the bugs
        of a root to stand apart from its system requirements, and the property behind that ask is
        that a reader wants one kind of thing at a time. Applied to every type it needs no case for
        the one that prompted it, and a type added to a view is grouped the day it ships.

        AND THEN BY `area`, which is the outline FR-0017 asks for, on the surface a person reads.
        The field is optional and orthogonal to the type, so the second key changes nothing for a
        project that sets none: every child falls into the one group with the empty area and the
        page is what it was. An area is a path (`backlog_types.area_segments`), so its segments
        read as the heading they are.

        ORDER: the view's type order first, then areas alphabetically with the UNFILED group LAST
        -- a reader looking for what is not sorted yet finds it in one place, at the end, instead
        of under whichever name happens to sort before "A".
        `test_board.test_children_of_one_parent_stand_under_their_outline_area` holds both.
        """
        grouped: dict = {}
        for child in self.children:
            body = child.body if isinstance(child.body, dict) else {}
            area = AREA_SEPARATOR.join(area_segments(body.get(AREA_FIELD)))
            grouped.setdefault((child.item_type, area), []).append(child)
        types = [item_type for item_type in view.children
                 if any(key[0] == item_type for key in grouped)]
        types += sorted({key[0] for key in grouped} - set(types))
        out = []
        for item_type in types:
            areas = {key[1] for key in grouped if key[0] == item_type}
            for area in sorted(areas, key=lambda one: (one == "", one)):
                out.append((item_type, area,
                            sorted(grouped[(item_type, area)], key=lambda node: node.item_id)))
        return out


def parents_of(node: Node) -> list:
    """Every id this item's own binding fields name, in contract order -- and nothing else.

    `PARENT_FIELDS` is the reference graph the rest of the kernel walks (the merge gate resolves an
    Evidence to its root through it), so a tree built from those fields cannot disagree with the
    state model about what belongs to what. `field_elements` is why a scalar `derives_from: SR-0003`
    is ONE reference and not eight letters (BUG-0015).

    A CONTAINER IN A BINDING FIELD IS NOT A REFERENCE, and it is skipped rather than rendered --
    which is the alias bomb again, one module further along. `str()` on a value `yaml.safe_load`
    built from an alias graph unfolds the WHOLE graph in one call, and no budget can interrupt a
    single call; that is the defect `board._emit` was written against (see its docstring), and this
    function reintroduced it by spelling `str(one)` with nothing around it. Measured on a 535-byte
    item file whose `derives_from` carried the bomb: 97.77 s and 480 MB per state write, against
    0.02 s with the container skipped. An id is a scalar by construction, so nothing a binding can
    legitimately hold is lost here -- the item reads as "names no <field>" and lands, visibly, under
    Unassigned. `test_board.test_an_alias_bomb_in_a_binding_field_cannot_stretch_a_state_write`.

    The `seen` SET is the second half of the same measurement: `str(one) not in found` was a linear
    scan per element, so a binding holding n references cost n²/2 comparisons.
    """
    if not isinstance(node.body, dict):
        return []
    found, seen = [], set()
    for field in PARENT_FIELDS.get(node.item_type, ()):
        for one in field_elements(node.body.get(field)):
            if not one or isinstance(one, (dict, list, tuple, set)):
                continue
            reference = str(one)
            if reference not in seen:
                seen.add(reference)
                found.append(reference)
    return found


def binding_fields(item_type: str) -> tuple:
    return PARENT_FIELDS.get(item_type, ())


def required_binding_fields(item_type: str) -> tuple:
    """The binding fields this type's own contract does not let it omit."""
    required = set(DECLARED_REQUIRED_FIELDS.get(item_type, ()))
    return tuple(field for field in binding_fields(item_type) if field in required)


# WHY an item could not be placed. Five cases and not five spellings of "no parent": they carry
# DIFFERENT remedies, and which one applies is read off the item's own contract rather than guessed
# -- a `TSK` without `derives_from` breaks a rule, an `FR` without `related_pr` does not (spec II.2
# declares it optional), an id that resolves to an item elsewhere on the board is a third thing, and
# an id that resolves to nothing at all a fourth. Both ends of this list are measured: every kind
# has to be producible from a real store and every producible kind has to have a message
# (`test_board.test_every_reason_a_tree_can_refuse_an_item_is_one_a_store_can_produce`).
UNREADABLE = "unassigned-unreadable"
MISSING_LINK = "unassigned-missing-link"
NO_LINK = "unassigned-no-link"
OFF_VIEW = "unassigned-off-view"
UNKNOWN_LINK = "unassigned-unknown-link"

# The templates carry NO finite verb and no possessive pronoun -- "1 request name no related_pr" is
# what a `{plural} name …` template reads like at a count of one, and the count is the item's, not
# the writer's. Nothing checks grammar here (no test can), so the shape is chosen to have nothing to
# inflect.
MESSAGES = {
    UNREADABLE: "{count} {plural} with a file nothing could parse (for example {example})",
    MISSING_LINK: "{count} {plural} without the {fields} the contract requires "
                  "(for example {example})",
    NO_LINK: "{count} {plural} without a {fields} — the contract allows that, and the tree has "
             "nothing to hang it from (for example {example})",
    OFF_VIEW: "{count} {plural} pointing at an item this view does not place "
              "(for example {example})",
    UNKNOWN_LINK: "{count} {plural} pointing at an id no item on this board carries "
                  "(for example {example})",
}


# The SHORT word the board puts on the item's own row, one per reason above. The banner counts a
# reason for a whole type; a reader looking at one item wants to know what THAT item is, and
# DEC-0066 (5) settles what it is called: a wish whose contract asks for no link is not "unassigned"
# -- it is still in the inbox, waiting to be triaged, which is the state the kits' own workflow
# gives it. Which word "inbox" is, is not written here twice: it is the type's own home, read off
# `home_word`, so `FR` reads "inbox" and any other type reads its own directory.
# BOTH ENDS of this map are read by
# `test_board.test_every_reason_a_tree_can_refuse_an_item_is_one_a_store_can_produce`, together
# with the two ends of MESSAGES: a reason with no word raises on the page, and a word for a reason
# nothing can produce is a dead entry. It did NOT read this map for one round, while this comment
# said it did.
_REASON_LABELS = {
    UNREADABLE: "file cannot be read",
    MISSING_LINK: "required link missing",
    NO_LINK: "{home} — not yet triaged",
    OFF_VIEW: "linked outside this view",
    UNKNOWN_LINK: "link goes nowhere",
}


def home_word(item_type: str) -> str:
    """The kit's own word for where an item of this type lives -- `inbox` for FR, `bugs` for BUG.

    The first segment of the type's OWN active directory, so the page speaks the vocabulary the
    project's tree already uses and no second naming of it exists to drift.
    """
    return ACTIVE_DIRS.get(item_type, item_type).split("/")[0]


def reason_label(kind: str, item_type: str) -> str:
    """The word the board puts on one refused item's row -- see `_REASON_LABELS`."""
    return _REASON_LABELS[kind].format(home=home_word(item_type))


def _why(node: Node, known: set) -> str:
    """The kind of reason this view has for not placing `node`."""
    if not isinstance(node.body, dict):
        return UNREADABLE
    named = parents_of(node)
    if not named:
        return MISSING_LINK if required_binding_fields(node.item_type) else NO_LINK
    return OFF_VIEW if any(one in known for one in named) else UNKNOWN_LINK


Arrangement = namedtuple("Arrangement", "view roots unassigned warnings placed reasons")


def arrange(view: View, entries) -> Arrangement:
    """Place every item this view shows under the item its own fields name.

    THE PLACEMENT RULE, in one sentence: a child goes under the DEEPEST of the items its binding
    fields name that this view has already placed. Deepest, because that is what "most specific"
    means in a tree, and because a `TSK` names two of them -- `product_requirement` (the root it
    serves) and `derives_from` (the SR, BUG or CR it was cut from), both real fields of its
    contract. Taking the first resolvable one instead would hang every task off the root and the
    system tree would be two levels deep for ever.

    AN ITEM OF A ROOT TYPE IS ALWAYS A ROOT, even when it names a parent of its own -- a PROC may
    carry `derives_from` (optional by spec II.2) and this tree does not nest it. That is a decision
    and the one place a real link goes unused: a root type is the top of its own tree, and a
    procedure filed under another procedure would bury the office kit's whole backlog one level
    down. `test_board.test_a_procedure_that_names_another_one_is_still_a_root` is where it stands,
    so it rots visibly if it stops being what we want.

    WHY THE LOOP HAS TWO PASSES. Depth is only known once a parent is placed, so a child whose
    deeper candidate is still unplaced must WAIT -- the strict pass places only children none of
    whose in-view candidates are still pending. When a round finds no such child, the state is a
    cycle or a chain into something unplaceable, and the relaxed pass then places whatever has any
    settled candidate at all; when even that finds nothing, the rest is unassigned. Every round
    settles at least one item or ends the loop, which is what makes a self-referential
    `derives_from` cost a warning instead of a hang
    (`test_board.test_a_link_that_points_at_itself_cannot_hang_the_state_write`).
    """
    known = {str(row.get("id") or "") for row, _body in entries}
    shown = set(view_types(view))
    nodes = [Node(row, body) for row, body in entries if str(row.get("type") or "") in shown]

    in_view: dict = {}
    settled: dict = {}
    pending = []
    for node in nodes:
        in_view.setdefault(node.item_id, node)
        if node.item_type in ROOT_TYPES:
            settled.setdefault(node.item_id, node)
        else:
            pending.append(node)

    candidates = {id(node): parents_of(node) for node in pending}
    while pending:
        ready = [node for node in pending
                 if any(one in settled for one in candidates[id(node)])
                 and not any(one in in_view and one not in settled
                             for one in candidates[id(node)])]
        if not ready:
            ready = [node for node in pending
                     if any(one in settled for one in candidates[id(node)])]
        if not ready:
            break
        for node in ready:
            reachable = [(position, settled[one])
                         for position, one in enumerate(candidates[id(node)]) if one in settled]
            _position, parent = max(reachable, key=lambda pair: (pair[1].depth, -pair[0]))
            node.parent, node.depth = parent, parent.depth + 1
            parent.children.append(node)
        # settled AFTER the whole round, so which parent a child gets never depends on where its
        # sibling sat in the round's list
        for node in ready:
            settled.setdefault(node.item_id, node)
        chosen = {id(node) for node in ready}
        pending = [node for node in pending if id(node) not in chosen]

    grouped: dict = {}
    for node in pending:
        grouped.setdefault((node.item_type, _why(node, known)), []).append(node)
    warnings = []
    for (item_type, kind), refused in sorted(grouped.items()):
        fields = ", ".join(required_binding_fields(item_type) or binding_fields(item_type))
        warnings.append((kind, item_type, MESSAGES[kind].format(
            count=len(refused), plural=label(item_type, len(refused)),
            fields=fields or "field that binds it to anything",
            example=refused[0].item_id or "?")))
    return Arrangement(
        view=view,
        roots=sorted((node for node in nodes if node.item_type in ROOT_TYPES),
                     key=lambda node: node.item_id),
        unassigned=sorted(pending, key=lambda node: (node.item_type, node.item_id)),
        warnings=warnings,
        placed=len(nodes) - len(pending),
        # the SAME kind the warning above was grouped by, per item: the banner counts the reasons
        # and the page says on each row which of them applies to that item (`board._branches`),
        # so the two can never name different reasons for one item
        reasons={node.item_id: kind for (_item_type, kind), refused in grouped.items()
                 for node in refused},
    )
