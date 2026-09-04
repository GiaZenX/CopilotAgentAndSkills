"""M-1 before/after: a title that is one long word, measured as DOCUMENT width."""
import os
import shutil
import sys

sys.dont_write_bytecode = True
WT = os.environ.get("PROBE_TREE", "C:/Offline Repos/v2-testbed/_worktrees/g3-board")
sys.path.insert(0, os.path.join(WT, "team-kits"))
sys.path.insert(0, os.path.join(WT, "tools"))
from kernel.state import ProjectState                      # noqa: E402
from kernel import board                                   # noqa: E402

HERE = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115/rework1"
PATH_TITLE = "team-kits/dev-team/templates/repo/scripts/progress.dashboard.template.html"
PR = {"title": PATH_TITLE, "class": "normal", "problem": "p", "goal": "g",
      "acceptance_criteria": [{"id": "AC-1", "text": "t"}], "invariants": [],
      "out_of_scope": ["z"], "priority": "high"}
SR = {"title": PATH_TITLE, "derives_from": "PR-0001", "contract": "c",
      "affected_components": ["api"]}
JS = """() => ({doc: document.documentElement.scrollWidth,
                 client: document.documentElement.clientWidth})"""


def build():
    root = os.path.join(HERE, "store-m1")
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(os.path.join(root, "project_memory"))
    state = ProjectState(os.path.join(root, "project_memory"))
    pr = state.capture("PR", PR)
    state.capture("SR", dict(SR, derives_from=pr["id"]))
    from kernel import approvals
    approvals.create_pending_request(state, "scope", pr["id"], ttl_seconds=3600.0)
    state.generate_index()
    return os.path.join(state.root, "generated", board.FILENAME)


def main():
    from playwright.sync_api import sync_playwright
    page_path = build()
    url = "file:///" + page_path.replace(os.sep, "/")
    worst = 0
    with sync_playwright() as driver:
        browser = driver.chromium.launch(headless=True)
        for width, height in ((1280, 800), (1920, 1000), (390, 844)):
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(url)
            page.wait_for_load_state("load")
            for tab in [b.get_attribute("data-tab") for b in page.locator("[data-tab]").all()]:
                page.click('[data-tab="%s"]' % tab)
                if tab == "board":
                    page.click('button[data-focus="you"]')
                got = page.evaluate(JS)
                over = got["doc"] - got["client"]
                worst = max(worst, over)
                print("  %4d px %-8s document %5d vs window %5d  -> %+d"
                      % (width, tab, got["doc"], got["client"], over))
                if tab == "board":
                    page.click('button[data-focus="you"]')
            page.close()
        browser.close()
    print("worst overhang: %d px" % worst)
    return 0 if worst <= 1 else 1


if __name__ == "__main__":
    sys.exit(main())
