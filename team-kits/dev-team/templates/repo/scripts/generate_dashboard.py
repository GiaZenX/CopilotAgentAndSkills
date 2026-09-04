#!/usr/bin/env python3
"""
generate_dashboard.py - owned by: PM (generated artifact source)

Renders `project_memory/generated/dashboard.html`: the repository's VITAL SIGNS and a pointer to the
backlog board. It writes only into `generated/`, which is regenerable and never committed (spec
II.2), so it can never become a second source of truth: it reports status, it never sets one.

WHY IT NO LONGER RENDERS ITEMS (DEC-0065 (1), FR-0075). Until 2026-09-03 this script read the
kernel's index and the item files and drew the whole backlog a second time, beside the board
`kernel/board.py` writes from the same index. The design pass measured the two against one copy of
the harness repo (`project_memory/staging/TSK-0115/parity.md`, which carries the figures): every
sum agreed that day, and the two disagreed the moment the store held something unusual -- this file
counted yaml FILES under `archive/`, the board counted item IDS of a type, so one planted foreign
yaml gave three different archive totals. Two programs that agree by inspection are two numbers a
reader has to reconcile. So the board is the one renderer of items, and what is left here is the
one thing it does NOT know: the shape of the repository's own source tree.

WHAT STAYS FROM FR-0030, because the wish that rebuilt this page kept all three: the documented
refresh trigger (`python scripts/generate_dashboard.py`, the end-of-phase checklist calls it
non-skippable), kit ownership (this file ships with the dev kit and is installed by its scaffold),
and the one-file property (the generated page opens by double-click and loads nothing).

WHY IT LIVES IN scripts/ AND NOT IN project_memory/. Measured, not assumed: `gate_write_scope`
refuses every write-capable command line that NAMES the state directory, and `python` is not a
read-only verb. A script inside the state directory cannot be started without naming it, so while
it lived there the documented command exited 2 for every agent. The script therefore moved out; the
OUTPUT still goes to `project_memory/generated/dashboard.html`, exactly the way `scripts/retro.py`
writes its own diagnostic layer.

WHAT IT STILL READS THE INDEX FOR: how many items the project has and when the index was written.
Not to draw them -- to say, honestly, whether there is anything on the board at all and how fresh it
is. A missing index is FATAL unless the project has captured nothing; the two are different truths
and V1's dashboard confused them for days.

Dependency: the installed state kernel (`.claude/kernel`, placed by the scaffold), the kit's
`scripts/kit_checks.py` (which DEFINES what counts as a source file, so the vitals panel and the
file-budget gate can never disagree) and PyYAML. The GENERATED html stays dependency-free.

Usage:
  python scripts/generate_dashboard.py
"""

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

# The file the kernel writes beside the index, and the one this page points at. A RELATIVE name,
# because both files live in `generated/` and an absolute path would break the moment the project
# is opened from anywhere else. The name is the kernel's (`kernel.board.FILENAME`) and is not
# imported from there: this script runs against the INSTALLED bundle, and a pointer that could not
# be resolved would cost the page rather than the link.
BOARD_FILENAME = "board.html"


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


def load_index(index_path, bridge):
    """(rows, generated_at, notice). A missing index is FATAL — unless there is no state at all.

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
            return [], "", ("No items captured yet — nothing has been written to "
                            "project_memory/, so there is no state to report on.")
        sys.stderr.write(
            "[dashboard] no %s, but %s holds items — the dashboard reports the kernel's index, it "
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
                         "truncated or hand-edited. Delete it; `python scripts/harness.py "
                         "generate-index` or the next kernel state write rebuilds it.\n")
        sys.exit(1)
    return ([row for row in rows if isinstance(row, dict)],
            str((data or {}).get("generated_at") or ""), "")


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
    # at the first `</script>` regardless of JSON quoting. Nothing item-derived reaches this block
    # any more (the items are on the board), but a source-file PATH is still project content, so
    # the escape stays where the parser is. `\/` is a legal JSON escape for `/`, so the parsed
    # value is unchanged. (V1 shipped without this.)
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
    state_dir = bridge.state_dir(REPO_ROOT)
    generated_dir = os.path.join(state_dir, "generated")
    output = os.path.join(generated_dir, "dashboard.html")

    rows, index_generated_at, notice = load_index(
        os.path.join(generated_dir, "index.yaml"), bridge)
    vitals = compute_repo_vitals()
    board_path = os.path.join(generated_dir, BOARD_FILENAME)
    data = {
        "generated_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
        "notice": notice,
        "active_items": len(rows),
        "index_generated_at": index_generated_at,
        "board": BOARD_FILENAME,
        "board_present": os.path.isfile(board_path),
        "repo_vitals": vitals,
    }

    html = render(data)
    if not os.path.isdir(generated_dir):
        os.makedirs(generated_dir)
    with open(output, "w", encoding="utf-8") as fh:
        fh.write(html)

    sys.stdout.write(
        "Dashboard generated: %s (vital signs only; %d active item(s) are on %s)\n"
        % (output, len(rows), board_path))
    if notice:
        sys.stdout.write("[dashboard] %s\n" % notice)
    if not data["board_present"] and rows:
        # SAID, not guessed at: the link would open nothing, and the remedy is a kernel command
        sys.stdout.write(
            "[dashboard] %s does not exist yet, so the link on this page opens nothing. The board "
            "is written by every kernel state write; run `python scripts/harness.py "
            "generate-index` to produce it.\n" % board_path)
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
