#!/usr/bin/env python3
"""
make_mockups.py -- PROTOTYPE of the redesigned backlog board (TSK-0115, phase 1, FR-0075).

Renders ONE self-contained HTML page from a copy of a project's `project_memory/` the way
`kernel/board.py` does -- same entries (`ACTIVE_DIRS` walk), same trees (`kernel.backlog_tree`),
same detail records (`board._detail`), same archive count (`board.archived_counts`) -- and adds
what the design brief asks for on top: a first strip answering "what is blocked, what waits on me,
what is in flight", a type order that puts living work before records, slots that collapse when
empty, and the T-card face. Nothing here is state: it reads, it never writes into the state it reads.

This is a DESIGN PROTOTYPE, not the build: phase 2 carries these decisions into `kernel/board.py`
(the one renderer, see 04-build-spec.md). Where this file re-implements a kernel function instead
of importing it, the reason is on the line.

Usage:
  python make_mockups.py --root <dir holding project_memory/> --out <file.html> [--name "Projekt"]

The command line names a directory ABOVE the state, never the state directory itself, for the
reason kit_design_render.py gives in its head: gate_write_scope refuses write-capable command lines
that name it.
"""
import argparse
import html
import os
import sys
import time

import yaml

sys.dont_write_bytecode = True
TEAM_KITS = os.environ.get("HARNESS_KERNEL_PATH") or "C:/Offline Repos/v2-testbed/_worktrees/g3-board/team-kits"
sys.path.insert(0, TEAM_KITS)

from kernel import backlog_tree, board  # noqa: E402
from kernel.backlog_types import ACTIVE_DIRS, AUTOMATA  # noqa: E402
from kernel.state import ProjectState  # noqa: E402

# ---------------------------------------------------------------- copy (one place, English)
# The page's own words. ENGLISH by user decision: DEC-0049 (2026-08-22) keeps the board page
# English; PM prose to the user stays German. `backlog_tree._LABELS` names the types the trees
# place; the record types get their names here for the same reader. Kernel vocabulary (status
# values, ids, type codes) is never translated: it is what commands take.
LABELS = dict(backlog_tree._LABELS)
LABELS.update({
    "DEC": ("decision", "decisions"),
    "EVD": ("evidence record", "evidence records"),
    "APR": ("approval", "approvals"),
    "INV": ("invariant", "invariants"),
    "ARC": ("architecture diagram", "architecture diagrams"),
    "WFR": ("wireframe", "wireframes"),
    "DSN": ("design revision", "design revisions"),
})
TREE_LABEL = {view.key: view.label for view in backlog_tree.VIEWS}
FOCUS = {
    "blocked": ("blocked", "nothing is stuck"),
    "you": ("waiting on you", "no open question for you"),
    "flight": ("in flight", "nothing started yet"),
}


def label(item_type, count=1):
    names = LABELS.get(item_type)
    if names is None:
        return item_type
    return names[0] if count == 1 else names[1]


# ---------------------------------------------------------------- reading the state (as the kernel does)
def read_entries(state):
    """(index row, body) pairs, the way `state._regenerate_index_locked` builds them."""
    entries = []
    for item_type in sorted(ACTIVE_DIRS):
        for stem, path in state.iter_active_items(item_type):
            try:
                item = state._read_yaml(path)
            except Exception:
                item = None
            if not isinstance(item, dict):
                entries.append(({"id": stem, "type": item_type, "corrupt": True}, None))
                continue
            row = {"id": item.get("id", stem), "type": item_type, "title": item.get("title"),
                   "status": item.get("status"), "revision": item.get("revision"),
                   "approval_ref": item.get("approval_ref")}
            if item.get("blocked_by"):
                row["blocked_by"] = item["blocked_by"]
            entries.append((row, item))
    return entries


def open_requests(pm, now):
    """The approval requests a user can still answer -- `report.generate_session_brief`'s rule:
    a request past `expires_at_epoch` can never mint and is not shown as open."""
    pending = os.path.join(pm, "approvals", "pending")
    found = []
    if not os.path.isdir(pending):
        return found
    for name in sorted(os.listdir(pending)):
        if not name.endswith(".yaml"):
            continue
        try:
            with open(os.path.join(pending, name), encoding="utf-8") as fh:
                request = yaml.safe_load(fh)
        except Exception:
            continue
        if not isinstance(request, dict) or now > float(request.get("expires_at_epoch", 0)):
            continue
        found.append({"request_id": str(request.get("request_id", name[:-5])),
                      "kind": str(request.get("kind", "?")),
                      "item": str(request.get("item") or ""),
                      "expires": time.strftime("%Y-%m-%d %H:%M",
                                               time.localtime(float(request["expires_at_epoch"])))})
    return found


def index_stamp(pm):
    path = os.path.join(pm, "generated", "index.yaml")
    try:
        with open(path, encoding="utf-8") as fh:
            return str(yaml.safe_load(fh).get("generated_at") or "")
    except Exception:
        return ""


# ---------------------------------------------------------------- the lanes (derived from the automaton)
NEW, FLIGHT, DONE, RECORD, OFF = "new", "flight", "done", "record", "off"


def lane(item_type, status):
    """Where an item stands in its own life, read off its automaton and nothing else:
    initial status -> new; terminal -> done (but still in active/); any other registered state
    (chain or side state) -> in flight; a type without an automaton -> a record."""
    auto = AUTOMATA.get(item_type)
    if auto is None:
        return RECORD
    if status == auto.initial:
        return NEW
    if status in auto.terminals:
        return DONE
    if status in auto.states:
        return FLIGHT
    return OFF


def chain_position(item_type, status):
    """'k/n' for a chain status, the side state's own name otherwise, '' for records."""
    auto = AUTOMATA.get(item_type)
    if auto is None or status not in auto.states:
        return ""
    if status in auto.chain:
        return "%d/%d" % (auto.chain.index(status) + 1, len(auto.chain))
    return str(status)


# ---------------------------------------------------------------- pieces of the page
def face_title(row, body, item_type):
    """What a card shows besides its id. A TSK has no `title` in its contract (REQUIRED_FIELDS),
    so its face is built from the fields it does owe: type of work, what it serves, who holds it."""
    title = board._face_title(row, body)
    if title or not isinstance(body, dict):
        return title
    if item_type == "TSK":
        parts = [str(body.get("type") or "task")]
        target = body.get("derives_from") or body.get("product_requirement")
        if target:
            parts.append("for %s" % target)
        if body.get("assigned_role"):
            parts.append("· %s" % body["assigned_role"])
        return " ".join(parts)
    return ""


def blockers(row):
    value = row.get("blocked_by")
    return ", ".join(str(one) for one in (value if isinstance(value, list) else [value]))


def card(row, body, item_type, flags):
    item_id = str(row.get("id") or "")
    classes = ["card"] + [flag for flag in ("blocked", "you") if flag in flags]
    head_note = ""
    if "blocked" in flags:
        head_note = '<span class="flag">blocked by %s</span>' % html.escape(blockers(row))
    elif "you" in flags:
        head_note = '<span class="flag">waiting on you: %s approval</span>' % html.escape(flags["you"])
    return ('<button type="button" class="%s" data-open="%s" data-lane="%s"><span class="head">'
            '<span class="id">%s</span>%s</span><span class="title">%s</span></button>'
            % (" ".join(classes), html.escape(item_id, quote=True), lane(item_type, row.get("status")),
               html.escape(item_id), head_note,
               html.escape(face_title(row, body, item_type)) or "<em>no title</em>"))


def section(item_type, entries, flags_of):
    declared = board.status_columns(item_type)
    by_column = {column: [] for column in declared}
    for row, body in entries:
        by_column.setdefault(board._column_of(row), []).append((row, body))
    extra = sorted(column for column in by_column if column not in declared)
    terminals = getattr(AUTOMATA.get(item_type), "terminals", frozenset())
    slots, empty_ends, empty_chain = [], [], []
    for column in list(declared) + extra:
        cards = sorted(by_column.get(column, []), key=lambda pair: str(pair[0].get("id") or ""))
        drawn = [card(row, body, item_type, flags_of(row)) for row, body in cards]
        cls = "slot" + (" terminal" if column in terminals else "") + ("" if drawn else " empty")
        if not drawn:
            (empty_ends if column in terminals else empty_chain).append(html.escape(str(column)))
            if column in terminals:
                # an empty end state says nothing a reader needs; the chain slots stay so the flow
                # reads left to right, the end states are named in the line below
                continue
        slots.append('<div class="%s" data-status="%s" data-count="%d"><h3>%s <span class="count">%d'
                     '</span></h3>%s</div>' % (cls, html.escape(str(column), quote=True), len(drawn),
                                               html.escape(str(column)), len(drawn), "".join(drawn)))
    empties_line = ""
    if empty_ends or empty_chain:
        empties_line = '<p class="empties">%s%s</p>' % (
            ('<span class="ends">no cards in %s</span>' % " · ".join(empty_ends)) if empty_ends else "",
            ('<span class="chain">%sno cards in %s</span>' % (" — " if empty_ends else "", " · ".join(empty_chain)))
            if empty_chain else "")
    return ('<section class="type" id="type-%s" data-type="%s" data-items="%d"><h2><span class="name">%s</span> '
            '<span class="code">%s</span> <span class="count">%d</span></h2>%s<div class="board">%s'
            '</div></section>' % (item_type, item_type, len(entries), html.escape(label(item_type, 2)),
                                  item_type, len(entries), empties_line, "".join(slots)))


def records_section(record_types, grouped, flags_of):
    """Types without an automaton (Evidence, approvals, decisions, frozen artefacts) are the
    project's paperwork: listed, not slotted, and closed by default. Nothing is dropped -- the
    summary line counts every one of them and opening it shows every id."""
    total = sum(len(grouped.get(t, [])) for t in record_types)
    if not total:
        return ""
    summary = " · ".join("%s %d" % (label(t, 2), len(grouped.get(t, []))) for t in record_types
                         if grouped.get(t))
    parts = []
    for item_type in record_types:
        entries = grouped.get(item_type, [])
        if not entries:
            continue
        by_status = {}
        for row, body in entries:
            by_status.setdefault(board._column_of(row), []).append((row, body))
        groups = []
        for status, pairs in sorted(by_status.items()):
            items = "".join(
                '<li><button type="button" class="rec" data-open="%s"><span class="id">%s</span> '
                '<span class="title">%s</span></button></li>'
                % (html.escape(str(r.get("id") or ""), quote=True), html.escape(str(r.get("id") or "")),
                   html.escape(board._face_title(r, b)))
                for r, b in sorted(pairs, key=lambda p: str(p[0].get("id") or ""), reverse=True))
            heading = "" if not board.status_columns(item_type) else (
                '<h4>%s <span class="count">%d</span></h4>' % (html.escape(str(status)), len(pairs)))
            groups.append('<div class="recgroup" data-status="%s">%s<ul>%s</ul></div>'
                          % (html.escape(str(status), quote=True), heading, items))
        parts.append('<section class="records-type" data-type="%s"><h3><span class="name">%s</span> <span class="code">%s</span>'
                     ' <span class="count">%d</span></h3>%s</section>'
                     % (item_type, html.escape(label(item_type, 2)), item_type, len(entries), "".join(groups)))
    return ('<details class="records" data-records="%d"><summary>Records '
            '<span class="count">%d</span> <span class="sum">%s</span></summary>%s</details>'
            % (total, total, html.escape(summary), "".join(parts)))


def type_order(types, grouped):
    """Living work first, records last; inside the living half the kit's root type leads.
    DERIVED: root = `backlog_tree.ROOT_TYPES`, living = has an automaton, record = has none."""
    living = [t for t in types if t in AUTOMATA]
    roots = [t for t in living if t in backlog_tree.ROOT_TYPES]
    rest = [t for t in living if t not in backlog_tree.ROOT_TYPES]
    records = [t for t in types if t not in AUTOMATA]
    return roots + rest, records


def focus_row(row, body, note):
    return ('<li><button type="button" class="rec" data-open="%s"><span class="id">%s</span> '
            '<span class="title">%s</span> <span class="badge">%s</span>%s</button></li>'
            % (html.escape(str(row.get("id") or ""), quote=True), html.escape(str(row.get("id") or "")),
               html.escape(face_title(row, body, row["type"])), html.escape(board._column_of(row)),
               (' <span class="note">%s</span>' % html.escape(note)) if note else ""))


def first_strip(entries, requests):
    """The three numbers a reader looks for first -- each a focus button, each with its first
    example -- and, under them, the three lists the buttons reveal, so the answer to "what is
    blocked" is one click and no scrolling away even on a board of 284 cards."""
    blocked = [(r, b) for r, b in entries if r.get("blocked_by")]
    named = {req["item"]: req for req in requests if req["item"]}
    you = [(r, b) for r, b in entries if str(r.get("id")) in named]
    unnamed = [req for req in requests if not req["item"]]
    flight = [(r, b) for r, b in entries if lane(r["type"], r.get("status")) == FLIGHT]
    done = [(r, b) for r, b in entries if lane(r["type"], r.get("status")) == DONE]

    def figure(key, count, example):
        return ('<button type="button" class="figure%s" data-focus="%s" aria-pressed="false">'
                '<span class="num">%d</span><span class="word">%s</span><span class="ex">%s</span></button>'
                % (" zero" if not count else "", key, count, FOCUS[key][0], html.escape(example)))

    ex_blocked = ("%s waits for %s" % (blocked[0][0]["id"], blockers(blocked[0][0]))) if blocked else FOCUS["blocked"][1]
    if you:
        req = named[str(you[0][0]["id"])]
        ex_you = "%s: %s approval, open until %s" % (you[0][0]["id"], req["kind"], req["expires"])
    elif unnamed:
        ex_you = "%s approval, open until %s" % (unnamed[0]["kind"], unnamed[0]["expires"])
    else:
        ex_you = FOCUS["you"][1]
    ex_flight = ("e.g. %s (%s)" % (flight[0][0]["id"], flight[0][0]["status"])) if flight else FOCUS["flight"][1]
    out = ['<section class="first" aria-label="First"><p class="eyebrow">First</p><div class="figures">',
           figure("blocked", len(blocked), ex_blocked),
           figure("you", len(you) + len(unnamed), ex_you),
           figure("flight", len(flight), ex_flight)]
    if done:
        out.append('<p class="done">%d finished, not yet archived — e.g. %s</p>' % (len(done), html.escape(done[0][0]["id"])))
    out.append("</div>")
    lists = (
        ("blocked", [focus_row(r, b, "blocked by " + blockers(r)) for r, b in blocked]),
        ("you", [focus_row(r, b, "%s approval, open until %s" % (named[str(r["id"])]["kind"], named[str(r["id"])]["expires"]))
                 for r, b in you]
         + ['<li><span class="rec"><span class="title">%s approval, open until %s</span></span></li>'
            % (html.escape(req["kind"]), html.escape(req["expires"])) for req in unnamed]),
        ("flight", [focus_row(r, b, "") for r, b in sorted(flight, key=lambda p: (p[0]["type"], p[0]["id"]))]),
    )
    for key, rows in lists:
        out.append('<div class="focus-list" data-focus-list="%s" data-count="%d"><h3>%s <span class="count">%d</span></h3>%s</div>'
                   % (key, len(rows), FOCUS[key][0], len(rows),
                      ('<ul>%s</ul>' % "".join(rows)) if rows else '<p class="empty">%s</p>' % FOCUS[key][1]))
    out.append("</section>")
    return "".join(out), named


# Groups under a node at this depth or deeper start hidden: a reader meets every root with what hangs
# directly under it, and one click opens the tasks. Roots stay open because a page whose first view is
# a list of closed roots answers nothing (user-feedback: "die Hierarchien einklappen koennen").
FOLD_DEPTH = 1


def _branches(nodes, view):
    """`board._branches` with a fold control per node that has children. Same iterative stack (the
    depth is the items' own), same group markup; the ONLY additions are the `.row` wrapper, the
    button and `hidden` on the groups of a deep node."""
    out = []
    stack = [("node", node) for node in reversed(nodes)]
    while stack:
        kind, payload = stack.pop()
        if kind == "html":
            out.append(payload)
            continue
        node = payload
        groups = node.grouped_children(view)
        collapsed = bool(groups) and node.depth >= FOLD_DEPTH
        if groups:
            fold = ('<button type="button" class="fold" data-fold="%s" aria-expanded="%s" '
                    'aria-label="children of %s"></button>'
                    % (html.escape(node.item_id, quote=True), "false" if collapsed else "true",
                       html.escape(node.item_id, quote=True)))
        else:
            fold = '<span class="fold-space"></span>'
        out.append('<li class="node" data-node="%s" data-node-type="%s" data-parent="%s" data-depth="%d">'
                   '<div class="row">%s%s</div>'
                   % (html.escape(node.item_id, quote=True), html.escape(node.item_type, quote=True),
                      html.escape(node.parent.item_id if node.parent else "", quote=True),
                      node.depth, fold, board._node_face(node)))
        follow = []
        for item_type, area, children in groups:
            follow.append(("html",
                           '<div class="group" data-group="%s" data-group-area="%s" data-group-parent="%s" '
                           'data-count="%d"%s><h4>%s%s <span class="count">%d</span></h4><ol>'
                           % (html.escape(item_type, quote=True), html.escape(area, quote=True),
                              html.escape(node.item_id, quote=True), len(children), " hidden" if collapsed else "",
                              html.escape(backlog_tree.label(item_type, len(children))),
                              html.escape(" — " + area) if area else "", len(children))))
            follow.extend(("node", child) for child in children)
            follow.append(("html", "</ol></div>"))
        follow.append(("html", "</li>"))
        stack.extend(reversed(follow))
    return "".join(out)


def tree_view(arrangement, key):
    """`board._tree_view`'s lead, empty and unassigned parts, with the collapsible branches."""
    view = arrangement.view
    parts = ['<p class="lead">%s</p>' % html.escape(view.lead)]
    if arrangement.roots:
        parts.append('<div class="tree-tools"><button type="button" data-fold-all="expand">Expand all</button>'
                     '<button type="button" data-fold-all="collapse">Collapse all</button></div>')
        parts.append('<ol class="tree" data-tree="%s">%s</ol>' % (html.escape(view.key, quote=True),
                                                                   _branches(arrangement.roots, view)))
    else:
        parts.append('<p class="empty">no %s yet — nothing to hang this view from</p>'
                     % html.escape(" or ".join(sorted(backlog_tree.label(t) for t in backlog_tree.ROOT_TYPES))))
    if arrangement.unassigned:
        parts.append('<section class="unassigned" data-unassigned="%s" data-count="%d">'
                     '<h3>Unassigned <span class="count">%d</span></h3>'
                     '<p class="lead">This view could not place these items under any item they name — some name '
                     'nothing, some name an item this view does not show, some name an id that is not on this board '
                     'at all. They stand here rather than nowhere; the warning above says which group is which.</p>'
                     '<ol class="tree">%s</ol></section>'
                     % (html.escape(view.key, quote=True), len(arrangement.unassigned), len(arrangement.unassigned),
                        _branches(arrangement.unassigned, view)))
    return "".join(parts)


# ---------------------------------------------------------------- FR-0079: milestones (TYPE option)
def simulate_mst_type():
    """The stream-C seam, applied at RUNTIME to the imported kernel maps so this mockup renders
    what the seam would render: an automaton, a directory, the required fields, a tree placement
    and a label. These are the lines mst-decision-proposal.md hands to stream C, verbatim in spirit."""
    from kernel import backlog_types
    backlog_types.AUTOMATA["MST"] = backlog_types._Automaton(
        chain=("PLANNED", "REACHED"),
        terminals=("REACHED", "MISSED", "DROPPED"),
        terminal_from={"MISSED": ("PLANNED",), "DROPPED": ("PLANNED",)},
    )
    backlog_types.ACTIVE_DIRS["MST"] = "milestones/active"
    backlog_types.REQUIRED_FIELDS["MST"] = ("title", "due", "derives_from")
    LABELS["MST"] = ("milestone", "milestones")
    backlog_tree._LABELS["MST"] = LABELS["MST"]
    product = backlog_tree.VIEWS[0]
    backlog_tree.VIEWS = (product._replace(children=product.children + ("MST",)),) + backlog_tree.VIEWS[1:]


def load_milestones(path):
    with open(path, encoding="utf-8") as fh:
        items = yaml.safe_load(fh) or []
    entries = []
    for item in items:
        row = {"id": item["id"], "type": "MST", "title": item.get("title"), "status": item.get("status"),
               "revision": item.get("revision", 1), "approval_ref": None}
        entries.append((row, item))
    return entries


def _descendants(arrangement, root_ids):
    """Every node the system tree hangs under one of `root_ids`, by lane."""
    found = {NEW: [], FLIGHT: [], DONE: []}
    stack = [node for node in arrangement.roots if node.item_id in root_ids]
    while stack:
        node = stack.pop()
        for child in node.children:
            key = lane(child.item_type, child.row.get("status"))
            if key in found:
                found[key].append(child)
            stack.append(child)
    return found


def timeline_view(entries, today):
    """Milestones on a date ruler, then each milestone with the goals it names and what hangs
    under them by lane. No percentage: archived items are not on this board (kernel rule), so a
    share would count the visible half only."""
    import datetime
    milestones = [(r, b) for r, b in entries if r["type"] == "MST"]
    if not milestones:
        return '<p class="empty">no milestones yet — a milestone is captured like any item and names the goals it dates</p>'
    dates = []
    for row, body in milestones:
        try:
            dates.append((datetime.date.fromisoformat(str(body.get("due"))), row, body))
        except ValueError:
            dates.append((None, row, body))
    known = [d for d, _r, _b in dates if d]
    lo = min(known + [today]) - datetime.timedelta(days=7)
    hi = max(known + [today]) + datetime.timedelta(days=7)
    span = max((hi - lo).days, 1)

    def x(day):
        return 100.0 * (day - lo).days / span
    system = backlog_tree.arrange(backlog_tree.VIEWS[1], entries)
    ticks = ['<div class="today" style="left:%.2f%%"><span>today %s</span></div>' % (x(today), today.isoformat())]
    rows, marks = [], []
    for due, row, body in sorted(dates, key=lambda t: (t[0] is None, t[0] or today)):
        status = str(row.get("status") or "")
        late = due is not None and due < today and lane("MST", status) != DONE
        if due is not None:
            marks.append((x(due), " late" if late else (" done" if lane("MST", status) == DONE else ""), row["id"]))
        goals = [str(g) for g in (body.get("derives_from") if isinstance(body.get("derives_from"), list)
                                  else [body.get("derives_from")]) if g]
        under = _descendants(system, set(goals))
        goal_text = ", ".join('<button type="button" class="ref" data-open="%s">%s</button>' % (html.escape(g, quote=True), html.escape(g))
                              for g in goals) or "<em>names no goal</em>"
        bar = "".join('<span class="seg %s" style="flex-grow:%d" title="%s %d"></span>' % (key, len(nodes), key, len(nodes))
                      for key, nodes in under.items() if nodes)
        counts = " · ".join("%d %s" % (len(nodes), {NEW: "planned", FLIGHT: "in flight", DONE: "done"}[key])
                            for key, nodes in under.items() if nodes) or "nothing under these goals yet"
        rows.append('<li class="milestone%s" data-milestone="%s"><button type="button" class="ms-face" data-open="%s">'
                    '<span class="date">%s</span><span class="id">%s</span> <span class="title">%s</span> '
                    '<span class="badge">%s</span></button><p class="goals">for %s — %s</p><div class="bar">%s</div></li>'
                    % (" late" if late else "", html.escape(row["id"], quote=True), html.escape(row["id"], quote=True),
                       html.escape(due.isoformat() if due else "no date"), html.escape(row["id"]),
                       html.escape(str(row.get("title") or "")), html.escape(status), goal_text, counts, bar))
    # a label that would stand on top of its neighbour's takes the upper level; sorted by position,
    # so the rule reads left to right the way the ruler does
    # three bands, so no two labels can share one: the today marker owns the top band, tick labels
    # alternate between the bottom and the middle band when they would stand within 9 % of each other
    level, last_x = 0, None
    for px, cls, item_id in sorted(marks):
        level = 1 - level if last_x is not None and px - last_x < 9 else 0
        last_x = px
        ticks.append('<div class="tick%s%s" style="left:%.2f%%" data-milestone="%s"><span class="id">%s</span></div>'
                     % (cls, " up" if level else "", px, html.escape(item_id, quote=True), html.escape(item_id)))
    return ('<p class="lead">Every milestone is an item of its own: a date, a title and the goals it is a date for. '
            'What hangs under those goals is counted by lane — archived work is not on this board and is not counted.</p>'
            '<div class="ruler" data-from="%s" data-to="%s">%s</div><ol class="milestones">%s</ol>'
            % (lo.isoformat(), hi.isoformat(), "".join(ticks), "".join(rows)))


# ---------------------------------------------------------------- the page
def render(state, pm, project_name, now, extra_entries=()):
    entries = read_entries(state) + list(extra_entries)
    requests = open_requests(pm, now)
    stamp = index_stamp(pm)
    grouped = {}
    for row, body in entries:
        grouped.setdefault(str(row.get("type") or "?"), []).append((row, body))
    types = sorted(set(board.types_present(state)) | set(grouped))
    living, records = type_order(types, grouped)
    strip, named = first_strip(entries, requests)

    def flags_of(row):
        flags = {}
        if row.get("blocked_by"):
            flags["blocked"] = True
        if str(row.get("id")) in named:
            flags["you"] = named[str(row.get("id"))]["kind"]
        return flags

    sections, warnings = [], []
    for item_type in living:
        if not grouped.get(item_type):
            continue
        sections.append(section(item_type, grouped[item_type], flags_of))
        _html, found = board._section(item_type, grouped[item_type])   # the kernel's own warnings
        warnings += found
    silent = [t for t in living if not grouped.get(t)]
    silent_line = ('<p class="silent">No entries: %s</p>' % ", ".join(
        "%s (%s)" % (html.escape(label(t, 2)), t) for t in silent)) if silent else ""
    known = {str(row.get("id") or "") for row, _b in entries}
    details = []
    for row, body in entries:
        drawn, problem = board._detail(row, body, known)
        details.append(drawn)
        if problem:
            warnings.append((str(row.get("type") or "?"), "unrenderable",
                             "%s could not be rendered (%s)" % (row.get("id") or "?", problem[:120])))
    if not entries:
        empty = ('<p class="nothing">Nothing captured yet. The first item comes from '
                 '<code>python scripts/harness.py capture</code>; the board is rebuilt with every '
                 'state write the kernel makes.</p>')
    else:
        empty = ""
    views = ['<div class="view" data-view="board">%s%s%s%s%s</div>'
             % (board._warnings(warnings), empty, "\n".join(sections),
                records_section(records, grouped, flags_of), silent_line)]
    tabs = [("board", "Board", len(entries))]
    for view in backlog_tree.VIEWS:
        arrangement = backlog_tree.arrange(view, entries)
        views.append('<div class="view" data-view="%s" hidden>%s%s</div>'
                     % (view.key, board._warnings([(t, k, d) for k, t, d in arrangement.warnings]),
                        tree_view(arrangement, view.key)))
        tabs.append((view.key, TREE_LABEL[view.key], arrangement.placed + len(arrangement.unassigned)))
    if any(row["type"] == "MST" for row, _b in entries):
        import datetime
        today = datetime.date.fromtimestamp(now)
        views.append('<div class="view" data-view="timeline" hidden>%s</div>' % timeline_view(entries, today))
        tabs.append(("timeline", "Timeline", sum(1 for row, _b in entries if row["type"] == "MST")))
    archived = board.archived_counts(state)
    strip_tabs = "".join('<button type="button" class="tab" data-tab="%s" aria-selected="%s">%s '
                         '<span class="count">%d</span></button>'
                         % (key, "true" if key == "board" else "false", html.escape(name), count)
                         for key, name, count in tabs)
    strip_tabs += ('<span class="archived" data-archived="%d">archived, not on this board: %d%s</span>'
                   % (sum(archived.values()), sum(archived.values()),
                      (" (%s)" % ", ".join("%s %d" % (t, c) for t, c in sorted(archived.items()))) if archived else ""))
    name = html.escape(project_name or "Project without a name")
    return PAGE % {
        "style": STYLE, "noscript": NOSCRIPT_STYLE, "script": SCRIPT, "name": name,
        "stamp": html.escape(stamp), "first": strip, "tabs": strip_tabs,
        "views": "\n".join(views), "details": "".join(details),
    }


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Backlog — %(name)s</title>
<style>%(style)s</style>
<noscript><style>%(noscript)s</style></noscript>
</head>
<body>
<header class="top">
<p class="eyebrow">Backlog</p>
<h1>%(name)s</h1>
<p class="meta">As of <time data-generated-at="%(stamp)s">%(stamp)s</time> — written by the state kernel
together with <code>index.yaml</code>, rebuilt on every state write. This page reports and sets
nothing; <span class="interactive">a click on a card opens its record, and every id in it that is on
this board opens in turn.</span> Archived items are not here.</p>
<noscript><p class="meta">This browser runs no scripts, so this page shows everything at once: the tabs
are hidden, the three views stand one after another, and every record is open under the board.</p></noscript>
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

# The visual system: a T-card planning board. Values live HERE and nowhere else (03-tokens.md carries
# names, roles and reasons, not hex).
STYLE = """
:root {
  color-scheme: light dark;
  --board: #eceef1;      /* the magnetic board */
  --slot: #e1e4e9;       /* one column's rail */
  --card: #ffffff;
  --ink: #16181c;
  --ink-2: #5a6170;
  --rule: #c9ced6;
  --you: #1a56c4;        /* your turn: the one accent, also every control */
  --you-ink: #ffffff;
  --stop: #b4121b;       /* blocked */
  --stop-ink: #ffffff;
  --font-head: "Bahnschrift SemiCondensed", Bahnschrift, "Avenir Next Condensed", "Arial Narrow", "Segoe UI", sans-serif;
  --font-body: "Segoe UI", system-ui, -apple-system, sans-serif;
  --font-mono: "Cascadia Mono", Consolas, "SF Mono", ui-monospace, monospace;
  --s1: .5rem; --s2: 1rem; --s3: 1.5rem; --s4: 2.5rem;
}
@media (prefers-color-scheme: dark) {
  :root { --board: #17191d; --slot: #1f2227; --card: #262a30; --ink: #eceef1; --ink-2: #a0a7b3;
          --rule: #3b414a; --you: #79a6ff; --you-ink: #0b1a3a; --stop: #ff7b7b; --stop-ink: #2a0608; }
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
"""

NOSCRIPT_STYLE = """
[hidden] { display: block !important; }
.tabs, .dialog .close, .interactive, .figure, .focus-list, .fold, .tree-tools { display: none !important; }
.overlay { position: static !important; background: none !important; padding: 0 !important; }
.detail { border-top: 1px solid var(--rule); margin-top: 1rem; }
"""

# The kernel's own script (hidden/aria-selected only) plus ONE addition: the focus buttons set
# `data-focus` on <body>, and the CSS does the dimming. Still a constant, still no item content.
SCRIPT = board._SCRIPT + """
(function () {
  function setFold(button, open) {
    var node = button.parentNode;
    while (node && !(node.classList && node.classList.contains('node'))) { node = node.parentNode; }
    if (!node) { return; }
    for (var i = 0; i < node.children.length; i++) {
      if (node.children[i].classList.contains('group')) { node.children[i].hidden = !open; }
    }
    button.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  document.addEventListener('click', function (event) {
    var el = event.target;
    while (el && el.getAttribute) {
      if (el.hasAttribute('data-fold')) { setFold(el, el.getAttribute('aria-expanded') !== 'true'); return; }
      if (el.hasAttribute('data-fold-all')) {
        var open = el.getAttribute('data-fold-all') === 'expand';
        var view = el;
        while (view && !(view.hasAttribute && view.hasAttribute('data-view'))) { view = view.parentNode; }
        var folds = (view || document).querySelectorAll('[data-fold]');
        for (var j = 0; j < folds.length; j++) { setFold(folds[j], open); }
        return;
      }
      el = el.parentNode;
    }
  });
})();
(function () {
  var figures = document.querySelectorAll('button[data-focus]');
  document.addEventListener('click', function (event) {
    var node = event.target;
    while (node && node.getAttribute) {
      if (node.hasAttribute('data-focus')) {
        var key = node.getAttribute('data-focus');
        var on = document.body.getAttribute('data-focus') === key;
        document.body.removeAttribute('data-focus');
        if (!on) { document.body.setAttribute('data-focus', key); }
        for (var i = 0; i < figures.length; i++) {
          figures[i].setAttribute('aria-pressed', (!on && figures[i].getAttribute('data-focus') === key) ? 'true' : 'false');
        }
        return;
      }
      node = node.parentNode;
    }
  });
})();
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="directory that holds project_memory/")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="")
    ap.add_argument("--now", type=float, default=None, help="epoch seconds deciding which requests are open")
    ap.add_argument("--milestones", default=None, help="FR-0079 fixture: a YAML list of MST items (TYPE option)")
    ap.add_argument("--style", default=None, help="phase 1b: one of the directions in directions.py (a|b|c)")
    args = ap.parse_args()
    if args.style:
        import directions
        global STYLE
        _name, STYLE = directions.build(args.style)
    pm = os.path.join(args.root, "project_memory")
    extra = ()
    if args.milestones:
        simulate_mst_type()
        extra = load_milestones(args.milestones)
    state = ProjectState(pm)
    page = render(state, pm, args.name, args.now if args.now is not None else time.time(), extra)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    print("[mockup] %s (%d bytes)" % (args.out, len(page.encode("utf-8"))))


if __name__ == "__main__":
    main()
