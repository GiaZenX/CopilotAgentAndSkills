#!/usr/bin/env python3
"""
generate_dashboard.py - owned by: PM (generated artifact source)

Renders `project_memory/generated/dashboard.html` from the kernel's regenerated index
(`generated/index.yaml`) plus the active item files (spec II.7). It writes only into
`generated/`, which is regenerable and never committed (spec II.2), so the dashboard can never
become a second source of truth: it reports status, it never sets one.

WHY IT LIVES IN scripts/ AND NOT IN project_memory/. Measured, not assumed: `gate_write_scope`
refuses every write-capable command line that NAMES the state directory, and `python` is not a
read-only verb. A script inside the state directory cannot be started without naming it, so while
it lived there the documented command exited 2 for every agent — the one the constitution calls
non-skippable. The script therefore moved out; the OUTPUT still goes to
`project_memory/generated/dashboard.html`, exactly the way `scripts/retro.py` writes its own
diagnostic layer.

WHAT CHANGED FROM V1 AND WHY. V1 read the status monoliths, archived the previous HTML into a
committed `dashboard_history/`, and diffed against a snapshot file. All three are gone: the
monoliths are dissolved into typed items, the history is git's job (spec II.7 "keine committete
Dashboard-History"), and a "changes since last run" panel made the output depend on when it last
ran — a generated artifact that is not a pure function of the state is one nobody can reproduce.

DERIVED, NOT LISTED. The item types, their directories, their status chains and which statuses
count as finished all come from `kernel.backlog_types`; the views below assign types to the four
TYPE sections of spec II.7 (its fifth section, Archive, is a counts-only tab rather than a view
over types) and anything unassigned lands in "Other" WITH a warning on stdout, so a new item type
shows up on the dashboard the day it ships instead of silently disappearing from it.

Dependency: the installed state kernel (`.claude/kernel`, placed by the scaffold), the kit's
`scripts/kit_checks.py` (which DEFINES what counts as a source file, so the vitals panel and the
file-budget gate can never disagree) and PyYAML. The GENERATED html stays dependency-free and
opens by double-click.

Usage:
  python scripts/generate_dashboard.py
"""

import collections
import datetime
import json
import os
import re
import sys

# This script imports the kernel THROUGH the installed bundle (`.claude/hooks/_kernel.py`), and
# `.claude/hooks` + `.claude/kernel` are what `hook_bundle_hash` measures. Left to itself, running
# a report would drop `__pycache__` into the enforcement bundle, the hash would no longer match the
# one the project recorded, and the next session would report `hooks_trust_required` because
# somebody generated a dashboard. No harness process writes bytecode into a tree the harness
# hashes — see `kernel/hashing.py`, BYTECODE_SUFFIXES.
sys.dont_write_bytecode = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
TEMPLATE = os.path.join(BASE_DIR, "progress.dashboard.template.html")

# A view is one spec II.7 section: which item types it shows, and whether it hides finished work.
View = collections.namedtuple("View", "id label types hide_done")

# Spec II.7 names the sections; this maps item TYPES onto them. It is a presentation decision,
# not a second copy of the type registry — `assign_views()` below routes every type
# `backlog_types.ACTIVE_DIRS` knows and reports the ones no section claims. `hide_done` carries
# the one filter the spec asks for, on the one view it asks for it: "Delivery (Task-Board,
# Erledigtes verborgen)". WHICH statuses count as finished is deliberately not written here —
# that is `AUTOMATA[type].terminals`, so a chain change moves the board with it.
VIEWS = (
    View("product", "Product", ("PR", "RQ", "FR", "CR", "BUG"), False),
    View("delivery", "Delivery", ("TSK", "PROC", "HYP", "EXP"), True),
    View("system", "System", ("SR", "INV", "ARC", "WFR", "DSN"), False),
    View("decisions", "Decisions", ("DEC", "APR", "EVD"), False),
)
# A type nobody assigned is shown unfiltered: hiding items of a type this file does not
# understand is precisely the disappearance the fallback exists to prevent.
OTHER_VIEW = View("other", "Other", (), False)

# Spec II.7: at most 50 items per page, details lazy, no archive or full text in the initial DOM.
PAGE_SIZE = 50


def load_bridge():
    """The hooks' own kernel bridge, `.claude/hooks/_kernel.py`.

    That module is the ONE place that knows where the kernel lives (installed bundle, harness
    checkout, `$HARNESS_KERNEL_PATH`) and what the state directory is called; resolving either of
    those a second time here is how the dashboard would end up reporting on a different kernel's
    idea of the state than the gates enforce. `disarm()` exists for exactly this caller: without
    it an ordinary error in this script would exit 2 through the gate excepthook and skip the
    stdout flush.
    """
    sys.path.insert(0, os.path.join(REPO_ROOT, ".claude", "hooks"))
    try:
        import _kernel  # type: ignore[import-not-found]
    except ImportError:
        sys.stderr.write(
            "[dashboard] no .claude/hooks/_kernel.py — the dashboard reads the typed state "
            "through the installed kernel. Remedy: re-run the team scaffold for this repo.\n")
        sys.exit(1)
    _kernel.disarm()
    return _kernel


def load_backlog_types(bridge):
    try:
        return bridge.kernel_module("backlog_types", REPO_ROOT)
    except Exception as exc:  # noqa: BLE001 — the remedy matters more than the type here
        sys.stderr.write("[dashboard] the state kernel is unavailable (%s).\n" % exc)
        sys.exit(1)


def assign_views(active_dirs):
    """([View, ...], unassigned) covering EVERY type.

    A type no section claims is not dropped — it goes to "Other" and is named on stdout, because
    the failure mode worth designing against is a whole item type quietly missing from the only
    overview a user looks at.
    """
    claimed, views = set(), []
    for view in VIEWS:
        present = tuple(t for t in view.types if t in active_dirs)
        claimed.update(present)
        views.append(view._replace(types=present))
    unassigned = tuple(sorted(set(active_dirs) - claimed))
    if unassigned:
        views.append(OTHER_VIEW._replace(types=unassigned))
    return views, list(unassigned)


def load_index(index_path, bridge):
    """(rows, yaml, notice). A missing index is FATAL — unless there is no state at all.

    An empty page must never stand in for "the index has not been generated": those are two
    different truths and V1's dashboard confused them for days. There is ONE case where they are
    the same truth, and the bridge decides it, not a guess here: `state_is_empty()` — a greenfield
    repo. The index is written by the kernel's state writes (capture/transition/archive), so a
    project that has captured nothing has no index BY CONSTRUCTION, and the end-of-phase checklist
    calls this command non-skippable from day 1. Refusing there would make the documented command
    fail in every new project. So: no state and no index -> render, and SAY that nothing has been
    captured. Items but no index -> still fatal.
    """
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        sys.stderr.write("[dashboard] PyYAML is required. Install it: pip install pyyaml\n")
        sys.exit(1)
    if not os.path.isfile(index_path):
        if bridge.state_is_empty(REPO_ROOT):
            return [], yaml, ("No items captured yet — nothing has been written to "
                              "project_memory/, so there is no state to report on.")
        sys.stderr.write(
            "[dashboard] no %s, but %s holds items — the dashboard renders the kernel's index, it "
            "does not rebuild it. Remedy: `python scripts/harness.py generate-index`, from the "
            "project root — and ANY kernel state write rebuilds the index as part of the same "
            "commit anyway, so a missing index means nothing has written state here yet.\n"
            % (os.path.relpath(index_path, REPO_ROOT), bridge.STATE_DIRNAME))
        sys.exit(1)
    try:
        with open(index_path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        # FATAL, not silent: a swallowed parse error once let an invalid decisions.yaml feed a
        # stale-but-green-looking dashboard for days. Keep the old dashboard, fail loudly.
        sys.stderr.write("[dashboard] FATAL: generated/index.yaml is invalid YAML — dashboard "
                         "NOT regenerated: %s\n" % exc)
        sys.exit(1)
    rows = (data or {}).get("items") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        sys.stderr.write("[dashboard] generated/index.yaml carries no `items:` list — it is "
                         "truncated or hand-edited. Delete it; `python scripts/harness.py generate-index` or the next "
                         "kernel state write rebuilds it.\n")
        sys.exit(1)
    return [row for row in rows if isinstance(row, dict)], yaml, ""


def read_item(yaml, state_dir, active_dirs, item_type, item_id):
    """The item file behind an index row, or {} when it cannot be read."""
    directory = active_dirs.get(item_type)
    if not directory or not item_id:
        return {}
    path = os.path.join(state_dir, directory, "%s.yaml" % item_id)
    try:
        with open(path, encoding="utf-8") as fh:
            body = yaml.safe_load(fh)
    except (OSError, yaml.YAMLError):
        return {}
    return body if isinstance(body, dict) else {}


def next_status(automata, item_type, status):
    """The next status on this type's chain — spec II.7's "nächster Schritt", derived.

    Taken from the automaton rather than from a table of advice: the chain IS the sequence of
    steps, so a chain change moves the dashboard with it, and a terminal or off-chain status
    honestly has no next step.
    """
    auto = automata.get(item_type)
    chain = list(getattr(auto, "chain", ()) or ())
    if status in chain and chain.index(status) + 1 < len(chain):
        return chain[chain.index(status) + 1]
    return ""


def is_finished(automata, item_type, status):
    """True when this status is TERMINAL for this type, i.e. the item is done with.

    Terminal items stay in `<type>/active/` until somebody archives them explicitly (the kernel
    has no auto-archive), so without this filter a Delivery board fills up with VALIDATED and
    CANCELLED tasks that push the open work off the first page.
    """
    return status in getattr(automata.get(item_type), "terminals", frozenset())


def relations(body, parse_id):
    """Every item id this item points at through a TOP-LEVEL field.

    A relation is DEFINED as "a field value that parses as an item id" instead of as a list of
    field names (`derives_from`, `dependencies`, `related_pr`, ...). The list version goes stale
    the first time a type gains a reference field; this version cannot. It reads top-level
    scalars and top-level lists of scalars; an id buried in a nested mapping is not found, and no
    shipped schema puts one there.

    `id` and `legacy_ids` are skipped for opposite reasons: the item's own id would make every
    item its own relation, and a legacy id is a former NAME of this item rather than a pointer to
    another one — and a V1 name can share a V2 prefix, so `parse_id` would accept it happily.
    """
    found = []
    # `key=str`: a hand-written item with mixed top-level key types (`1: x` next to `a: y`) makes a
    # bare sort raise TypeError, and this generator would die with a traceback instead of showing
    # the item — `corrupt` exists for exactly that item.
    for key, value in sorted(body.items(), key=lambda kv: str(kv[0])):
        if key in ("id", "legacy_ids"):
            continue
        for candidate in (value if isinstance(value, (list, tuple)) else [value]):
            if not isinstance(candidate, str):
                continue
            try:
                parse_id(candidate)
            except ValueError:
                continue
            if candidate not in found:
                found.append(candidate)
    return found


def archive_summary(state_dir):
    """Counts per type and year — never the archived items themselves.

    Spec II.7 asks for an Archive view and forbids archive content in the initial DOM. Counts
    answer "is there history here, and where" without embedding any of it; the items stay one
    `archive/<type>/<year>/` directory listing away.
    """
    base = os.path.join(state_dir, "archive")
    out, total = {}, 0
    if not os.path.isdir(base):
        return {"total": 0, "by_type": {}}
    for item_type in sorted(os.listdir(base)):
        type_dir = os.path.join(base, item_type)
        if not os.path.isdir(type_dir):
            continue
        years = {}
        for year in sorted(os.listdir(type_dir)):
            year_dir = os.path.join(type_dir, year)
            if not os.path.isdir(year_dir):
                continue
            count = sum(1 for name in os.listdir(year_dir) if name.endswith(".yaml"))
            if count:
                years[year] = count
                total += count
        if years:
            out[item_type] = years
    return {"total": total, "by_type": out}


def compute_repo_vitals():
    """Structure vitals (largest source files, count > 2000 lines): a real App.tsx grew to 8,966
    lines (+666 the very day its split-flag was logged) and nobody noticed — prompt findings
    without an artifact verpuffen. Enforcement lives in scripts/kit_checks.py (file budget); this
    is the always-visible signal on every regeneration (stdout + dashboard data).

    The FILE SET comes from `kit_checks.source_files()`, the same generator the budget check
    itself iterates — scan areas, skip list, extension set, the `.min.*` exclusion and the line
    count are one definition, not two. This panel used to re-declare all four, so "the panel and
    the gate cannot scan different trees" held for the trees and quietly failed for the file types.
    """
    sys.path.insert(0, BASE_DIR)
    try:
        import kit_checks  # type: ignore[import-not-found]
    except ImportError:
        sys.stderr.write("[dashboard] scripts/kit_checks.py is missing, so the repo vitals were "
                         "skipped. Remedy: re-run the team scaffold for this repo.\n")
        return {"largest": [], "over_2000": 0, "source_files": 0}
    # an unreadable file is yielded with lines=None (it still proves the area matched); a report
    # has nothing to say about it
    sizes = [(rel, n) for rel, n in kit_checks.source_files(REPO_ROOT) if n is not None]
    sizes.sort(key=lambda t: -t[1])
    return {
        "largest": [{"path": p, "lines": n} for p, n in sizes[:5]],
        "over_2000": sum(1 for _, n in sizes if n > 2000),
        "source_files": len(sizes),
    }


def render(data):
    with open(TEMPLATE, "r", encoding="utf-8") as fh:
        template = fh.read()
    # `</` -> `<\/`: the JSON goes inside a <script> element, where the HTML parser ends the block
    # at the first `</script>` regardless of JSON quoting — an item titled "fix </script> leak"
    # would break out of the data block and into the document. `\/` is a legal JSON escape for
    # `/`, so the parsed value is unchanged. (V1 shipped without this.)
    block = json.dumps(data, indent=2, ensure_ascii=False).replace("</", "<\\/")
    replacement = (
        '<script type="application/json" id="dashboard-data">\n'
        + block
        + "\n</script>"
    )
    pattern = re.compile(
        r'<script type="application/json" id="dashboard-data">.*?</script>',
        re.DOTALL,
    )
    if not pattern.search(template):
        sys.stderr.write("Template is missing the dashboard-data block.\n")
        sys.exit(1)
    return pattern.sub(lambda _m: replacement, template, count=1)


def main():
    if not os.path.exists(TEMPLATE):
        sys.stderr.write("Template not found: %s\n" % TEMPLATE)
        sys.exit(1)

    bridge = load_bridge()
    backlog_types = load_backlog_types(bridge)
    state_dir = bridge.state_dir(REPO_ROOT)
    generated_dir = os.path.join(state_dir, "generated")
    output = os.path.join(generated_dir, "dashboard.html")

    rows, yaml, notice = load_index(os.path.join(generated_dir, "index.yaml"), bridge)
    views, unassigned = assign_views(backlog_types.ACTIVE_DIRS)

    by_type = {}
    for row in rows:
        by_type.setdefault(str(row.get("type") or "?"), []).append(row)

    view_data, rendered, hidden = [], 0, 0
    for view in views:
        # SORT and SLICE on the index rows, THEN read the item files: the sort key (type, id) is
        # fully present in the index, so a 10,000-item project must not cost 10,000 YAML parses to
        # show 50 rows.
        kept = []
        for item_type in view.types:
            for row in by_type.get(item_type, []):
                status = str(row.get("status") or "")
                if view.hide_done and is_finished(backlog_types.AUTOMATA, item_type, status):
                    hidden += 1
                    continue
                kept.append((item_type, str(row.get("id") or ""), status, row))
        kept.sort(key=lambda t: (t[0], t[1]))
        items = []
        for item_type, item_id, status, row in kept[:PAGE_SIZE]:   # spec II.7: max 50 per page
            body = read_item(yaml, state_dir, backlog_types.ACTIVE_DIRS, item_type, item_id)
            items.append({
                "id": item_id,
                "type": item_type,
                "title": str(row.get("title") or body.get("title") or ""),
                "status": status,
                "next": next_status(backlog_types.AUTOMATA, item_type, status),
                "blocked_by": row.get("blocked_by") or "",
                "revision": row.get("revision"),
                "approved": bool(row.get("approval_ref")),
                "corrupt": bool(row.get("corrupt")),
                "relations": relations(body, backlog_types.parse_id),
            })
        rendered += len(items)
        view_data.append({
            "id": view.id,
            "label": view.label,
            "total": len(kept),
            "items": items,
        })

    vitals = compute_repo_vitals()
    data = {
        "generated_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
        "page_size": PAGE_SIZE,
        "notice": notice,
        "views": view_data,
        "archive": archive_summary(state_dir),
        "repo_vitals": vitals,
    }

    html = render(data)
    if not os.path.isdir(generated_dir):
        os.makedirs(generated_dir)
    with open(output, "w", encoding="utf-8") as fh:
        fh.write(html)

    sys.stdout.write(
        "Dashboard generated: %s (%d active item(s) in %d view(s), %d rendered, %d finished "
        "hidden, %d archived)\n"
        % (output, len(rows), len(view_data), rendered, hidden, data["archive"]["total"]))
    if notice:
        sys.stdout.write("[dashboard] %s\n" % notice)
    if unassigned:
        sys.stdout.write(
            "[dashboard] item type(s) %s belong to no view and were rendered under 'Other' — "
            "assign them in generate_dashboard.VIEWS\n" % ", ".join(unassigned))
    if vitals["largest"]:
        top = vitals["largest"][0]
        sys.stdout.write(
            "[vitals] largest source file: %s (%d lines); %d file(s) > 2000 lines of %d — structural "
            "flags MUST become a TSK or a recorded decision (constitution §13); the file budget in "
            "scripts/kit_checks.py enforces the hard limit\n"
            % (top["path"], top["lines"], vitals["over_2000"], vitals["source_files"])
        )


if __name__ == "__main__":
    main()
