"""The named limit of the three-band ruler: three and four marks inside one gap."""
import os
import shutil
import sys

sys.dont_write_bytecode = True
WT = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
sys.path.insert(0, os.path.join(WT, "team-kits"))
sys.path.insert(0, os.path.join(WT, "tools"))
from kernel import backlog_tree, backlog_types, board      # noqa: E402
from kernel.state import ProjectState                      # noqa: E402

HERE = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1"
PR = {"title": "root", "class": "normal", "problem": "p", "goal": "g",
      "acceptance_criteria": [{"id": "AC-1", "text": "t"}], "invariants": [],
      "out_of_scope": ["z"], "priority": "high"}
JS = """(sel) => Array.from(document.querySelectorAll(sel)).filter(e => e.offsetParent !== null)
  .map(e => { const r = e.getBoundingClientRect();
    return {x: r.left, y: r.top, w: r.width, h: r.height, t: e.textContent.trim()}; })"""


def seam():
    backlog_types.AUTOMATA["MST"] = backlog_types._Automaton(
        chain=("PLANNED", "REACHED"), terminals=("REACHED", "MISSED", "DROPPED"),
        terminal_from={"MISSED": ("PLANNED",), "DROPPED": ("PLANNED",)})
    backlog_types.ACTIVE_DIRS["MST"] = "milestones/active"
    backlog_types.REQUIRED_FIELDS["MST"] = ("title", "due", "derives_from")
    backlog_tree._LABELS["MST"] = ("milestone", "milestones")
    backlog_tree.PARENT_FIELDS["MST"] = backlog_types._parent_fields()["MST"]


def overlaps(rects):
    out = []
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            dx = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
            dy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
            if dx > 1 and dy > 1:
                out.append((a["t"], b["t"], round(dx), round(dy)))
    return out


def page_for(count):
    root = os.path.join(HERE, "store-bands-%d" % count)
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(os.path.join(root, "project_memory"))
    state = ProjectState(os.path.join(root, "project_memory"))
    pr = state.capture("PR", PR)
    entries = [({"id": pr["id"], "type": "PR", "title": "root", "status": "DRAFT"}, pr)]
    for n in range(1, count + 1):
        item_id = "MST-%04d" % n
        body = {"id": item_id, "title": "m%d" % n, "status": "PLANNED",
                "due": "2026-09-%02d" % (9 + n), "derives_from": [pr["id"]], "revision": 1}
        entries.append(({"id": item_id, "type": "MST", "title": body["title"],
                         "status": "PLANNED", "revision": 1}, body))
    path = os.path.join(root, "timeline.html")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(board.render(state, entries, "2026-08-16T12:00:00"))
    return path


def main():
    from playwright.sync_api import sync_playwright
    seam()
    with sync_playwright() as driver:
        browser = driver.chromium.launch(headless=True)
        for count in (2, 3, 4):
            path = page_for(count)
            for width in (1280, 390):
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.goto("file:///" + path.replace(os.sep, "/"))
                page.wait_for_load_state("load")
                page.click('[data-tab="timeline"]')
                hits = overlaps(page.evaluate(JS, ".ruler .tick .id, .ruler .today span"))
                print("%d marks, %4d px: %d overlapping label pair(s) %s"
                      % (count, width, len(hits), hits[:2]))
                page.close()
        browser.close()


main()
