"""Sight what phase 2 BUILT (TSK-0115): the shipped kernel renderer over four states.

Four fixtures under this scratch directory -- empty, healthy, blocked, timeline -- rendered by
`kernel.board.render` itself (not by the prototype), then screenshotted per the BUG-0076 doctrine:
1280 / 1920 / 390, light and dark, every tab, plus the two focus states, an open record, the
records block and the tree default / expanded / collapsed / keyboard.

Writes: build/<state>.html, review/build/*.png and review/build/render.json (each page bound to the
sha256 of its bytes).
"""
import datetime
import hashlib
import json
import os
import shutil
import sys

import yaml

sys.dont_write_bytecode = True
HERE = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115"
WT = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
TEAM_KITS = os.path.join(WT, "team-kits")
MAIN_PM = "C:/Offline Repos/AgentAndSkills/project_memory"
sys.path.insert(0, TEAM_KITS)

from kernel import backlog_tree, backlog_types, board  # noqa: E402
from kernel.state import ProjectState  # noqa: E402

BUILD = os.path.join(HERE, "build")
OUT = os.path.join(HERE, "review", "build")
VIEWPORTS = ((1280, 800), (1920, 1000), (390, 844))
STAMP = "2026-09-03T12:00:00"

HEALTHY_IDS = ("PR-0002", "PR-0003", "SR-0008", "SR-0009", "FR-0075", "FR-0079", "FR-0080",
               "BUG-0086", "BUG-0087", "BUG-0088", "BUG-0089", "TSK-0115", "TSK-0116", "TSK-0117",
               "DEC-0061", "DEC-0062", "DEC-0063")
HEALTHY_EDITS = {
    "TSK-0116": {"status": "IN_PROGRESS", "product_requirement": "PR-0003",
                 "derives_from": "SR-0008"},
    "TSK-0115": {"product_requirement": "PR-0003", "derives_from": "SR-0009"},
    "TSK-0117": {"product_requirement": "PR-0003", "derives_from": "PR-0003"},
    "FR-0080": {"status": "TRIAGED", "related_pr": "PR-0003"},
    "FR-0075": {"related_pr": "PR-0003"},
    "FR-0079": {"related_pr": "PR-0002"},
    "BUG-0086": {"related_pr": "PR-0003"},
    "BUG-0087": {"related_pr": "PR-0003"},
    "BUG-0088": {"related_pr": "PR-0002"},
    "BUG-0089": {"related_pr": "PR-0003", "related_sr": "SR-0009"},
}
BLOCKED_OVERLAY = {"TSK-0117": "TSK-0115", "TSK-0118": "APR-0004", "BUG-0088": "TSK-0116"}
MILESTONES = [
    {"id": "MST-0001", "title": "generation 3 merged", "status": "PLANNED", "due": "2026-09-10",
     "derives_from": ["PR-0003"], "revision": 1, "approval_ref": None},
    {"id": "MST-0002", "title": "pilot repeat", "status": "PLANNED", "due": "2026-09-11",
     "derives_from": ["PR-0003"], "revision": 1, "approval_ref": None},
    {"id": "MST-0003", "title": "V2 cutover", "status": "PLANNED", "due": "2026-08-20",
     "derives_from": ["PR-0002"], "revision": 1, "approval_ref": None},
    {"id": "MST-0004", "title": "harness v2 feature freeze", "status": "REACHED",
     "due": "2026-08-01", "derives_from": ["PR-0002"], "revision": 1, "approval_ref": None},
]


def install_milestone_type():
    """The DEC-0064 type lines stream C applies -- installed here so the fixture can be rendered."""
    backlog_types.AUTOMATA["MST"] = backlog_types._Automaton(
        chain=("PLANNED", "REACHED"), terminals=("REACHED", "MISSED", "DROPPED"),
        terminal_from={"MISSED": ("PLANNED",), "DROPPED": ("PLANNED",)})
    backlog_types.ACTIVE_DIRS["MST"] = "milestones/active"
    backlog_types.REQUIRED_FIELDS["MST"] = ("title", "due", "derives_from")
    backlog_tree._LABELS["MST"] = ("milestone", "milestones")
    backlog_tree.PARENT_FIELDS["MST"] = backlog_types._parent_fields()["MST"]
    product = backlog_tree.VIEWS[0]
    backlog_tree.VIEWS = ((product._replace(children=product.children + ("MST",)),)
                          + backlog_tree.VIEWS[1:])


def _edit(path, fields):
    with open(path, encoding="utf-8") as fh:
        body = yaml.safe_load(fh)
    body.update(fields)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(body, fh, allow_unicode=True, sort_keys=False)


def _find(pm, item_id):
    for dirpath, _dirs, files in os.walk(pm):
        if "archive" in dirpath.replace("\\", "/").split("/"):
            continue
        if item_id + ".yaml" in files:
            return os.path.join(dirpath, item_id + ".yaml")
    raise SystemExit("no %s under %s" % (item_id, pm))


def _fresh(name):
    pm = os.path.join(HERE, "fixtures", name, "project_memory")
    if os.path.isdir(os.path.dirname(pm)):
        shutil.rmtree(os.path.dirname(pm))
    os.makedirs(os.path.dirname(pm))
    return pm


def build_empty():
    pm = _fresh("empty")
    shutil.copytree(os.path.join(TEAM_KITS, "dev-team", "templates", "project_memory"), pm)
    return pm


def build_healthy():
    pm = build_empty()
    shutil.rmtree(os.path.dirname(pm))
    os.makedirs(os.path.dirname(pm))
    shutil.copytree(os.path.join(TEAM_KITS, "dev-team", "templates", "project_memory"), pm)
    for item_id in HEALTHY_IDS:
        src = _find(MAIN_PM, item_id)
        dst = os.path.join(pm, os.path.relpath(src, MAIN_PM))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)
        if item_id in HEALTHY_EDITS:
            _edit(dst, HEALTHY_EDITS[item_id])
    arch_src = os.path.join(MAIN_PM, "archive", "TSK", "2026")
    arch_dst = os.path.join(pm, "archive", "TSK", "2026")
    os.makedirs(arch_dst, exist_ok=True)
    for name in sorted(os.listdir(arch_src))[-5:]:
        shutil.copy(os.path.join(arch_src, name), os.path.join(arch_dst, name))
    return pm


def build_blocked():
    pm = _fresh("blocked")
    shutil.copytree(MAIN_PM, pm, ignore=shutil.ignore_patterns(
        "staging", "generated", ".kernel.lock*", ".audit", "__pycache__"))
    for item_id, blocker in BLOCKED_OVERLAY.items():
        _edit(_find(pm, item_id), {"blocked_by": blocker})
    return pm


def entries_of(pm):
    state = ProjectState(pm)
    state.generate_index()
    rows = yaml.safe_load(open(os.path.join(pm, "generated", "index.yaml"),
                               encoding="utf-8"))["items"]
    out = []
    for row in rows:
        try:
            body = state.read_item(row["id"])
        except Exception:
            body = None
        out.append((row, body))
    return state, out


def write_page(name, state, entries):
    os.makedirs(BUILD, exist_ok=True)
    path = os.path.join(BUILD, name + ".html")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(board.render(state, entries, STAMP))
    return path


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def shoot(pages):
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    record = {"rendered_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
              "pages": {}}
    with sync_playwright() as driver:
        browser = driver.chromium.launch(headless=True)
        for name, path in pages:
            entry = {"sha256": sha256(path), "images": [], "errors": []}
            url = "file:///" + os.path.abspath(path).replace("\\", "/")
            for scheme in ("light", "dark"):
                for width, height in VIEWPORTS:
                    ctx = browser.new_context(viewport={"width": width, "height": height},
                                              color_scheme=scheme, locale="de-DE")
                    page = ctx.new_page()
                    page.on("pageerror", lambda exc: entry["errors"].append(str(exc)))
                    page.on("console",
                            lambda msg: entry["errors"].append(msg.text)
                            if msg.type == "error" else None)
                    page.on("request", lambda req: entry["errors"].append("request " + req.url)
                            if not req.url.startswith("file:") else None)
                    page.goto(url)
                    page.wait_for_load_state("load")
                    suffix = "-dark" if scheme == "dark" else ""
                    tabs = [tab.get_attribute("data-tab")
                            for tab in page.locator("[data-tab]").all()]
                    for tab in tabs:
                        page.click('[data-tab="%s"]' % tab)
                        full = (tab in ("product", "system") and width == 1280
                                and scheme == "light")
                        target = os.path.join(OUT, "%s-%s-%d%s.png" % (name, tab, width, suffix))
                        page.screenshot(path=target, full_page=full)
                        entry["images"].append(os.path.basename(target))
                        scope = '[data-view="system"] '
                        if (tab == "system" and width == 1280 and scheme == "light"
                                and page.locator(scope + '[data-fold-all="expand"]').count()):
                            for action in ("expand", "collapse"):
                                page.click(scope + '[data-fold-all="%s"]' % action)
                                target = os.path.join(OUT, "%s-system-%d-%s.png"
                                                      % (name, width, action))
                                page.screenshot(path=target, full_page=True)
                                entry["images"].append(os.path.basename(target))
                            first = page.locator(scope + "[data-fold]").first
                            first.focus()
                            page.keyboard.press("Enter")
                            target = os.path.join(OUT, "%s-system-%d-keyboard.png" % (name, width))
                            page.screenshot(path=target)
                            entry["images"].append(os.path.basename(target))
                    page.click('[data-tab="board"]')
                    if width == 1280 and scheme == "light":
                        for key in ("blocked", "you", "flight"):
                            figure = page.locator('button[data-focus="%s"]' % key)
                            if figure.count():
                                figure.click()
                                target = os.path.join(OUT, "%s-board-focus-%s.png" % (name, key))
                                page.screenshot(path=target)
                                entry["images"].append(os.path.basename(target))
                                figure.click()
                        cards = page.locator("button.card")
                        if cards.count():
                            cards.first.click()
                            target = os.path.join(OUT, "%s-record.png" % name)
                            page.screenshot(path=target)
                            entry["images"].append(os.path.basename(target))
                            page.keyboard.press("Escape")
                        records = page.locator("details.records summary")
                        if records.count():
                            records.click()
                            page.locator("details.records").scroll_into_view_if_needed()
                            target = os.path.join(OUT, "%s-records.png" % name)
                            page.screenshot(path=target)
                            entry["images"].append(os.path.basename(target))
                    ctx.close()
            record["pages"][name] = entry
            if entry["errors"]:
                sys.stderr.write("[sight] %s: %s\n" % (name, entry["errors"][:3]))
        browser.close()
    with open(os.path.join(OUT, "render.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
    print("[sight] %d page(s) -> %d image(s)"
          % (len(record["pages"]), sum(len(one["images"]) for one in record["pages"].values())))
    return 1 if any(one["errors"] for one in record["pages"].values()) else 0


def main():
    install_milestone_type()
    pages = []
    for name, builder in (("empty", build_empty), ("healthy", build_healthy),
                          ("blocked", build_blocked)):
        state, entries = entries_of(builder())
        pages.append((name, write_page(name, state, entries)))
        if name == "healthy":
            extra = [({"id": one["id"], "type": "MST", "title": one["title"],
                       "status": one["status"], "revision": 1, "approval_ref": None}, one)
                     for one in MILESTONES]
            pages.append(("timeline", write_page("timeline", state, entries + extra)))
    for name, path in pages:
        print("[page] %-9s %8d bytes  %s" % (name, os.path.getsize(path), sha256(path)[:16]))
    return shoot(pages)


if __name__ == "__main__":
    sys.exit(main())
