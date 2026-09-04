"""The board's LAYOUT, measured in a browser (FR-0075 phase 1d, TSK-0115).

WHY THIS FILE IS SEPARATE FROM `test_board.py`. Everything there reads the DOM the renderer writes
and needs no browser; the four questions here cannot be answered from markup at all -- whether two
cards overlap, whether the page uses the width it is given, whether a keyboard reaches a fold
control and whether two ruler labels stand on top of each other are questions about BOXES, and only
a layout engine has those. The design pass measured the same numbers with the same technique
(`project_memory/staging/TSK-0115/measure_layout.py`, `layout-before.md` / `layout-after.md`); this
is that measurement turned into a check that runs.

IT MAY NOT BE SILENTLY GREEN WITHOUT A BROWSER. `importorskip` SKIPS the module rather than passing
it, so a run without Playwright says so per test instead of reporting four checks that measured
nothing -- which is the failure mode this repo has shipped twice. The round's protocol records the
run that really happened, with the numbers.
"""
import os
import sys

import pytest

playwright_api = pytest.importorskip(
    "playwright.sync_api",
    reason="the layout checks need a real layout engine; without Playwright they measure nothing, "
           "so they are skipped rather than passed (install: pip install playwright && "
           "playwright install chromium)")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")
sys.path.insert(0, TEAM_KITS)

from kernel import board  # noqa: E402
from test_board import (  # noqa: E402 -- one set of fixtures, one seam, no second copy
    BUG_FIELDS,
    PR_FIELDS,
    SR_FIELDS,
    TSK_FIELDS,
    _dev_store,
    _entries_of,
    _milestone,
    _state,
    # imported under its own name, because pytest resolves a fixture by the module ATTRIBUTE
    # it is bound to (an alias is not found); the parameter below therefore shadows it,
    # which is what the `noqa` on that line is about
    milestone_type,  # noqa: F401
)
from conftest import approve, walk_to_status  # noqa: E402

# The three widths the sighting doctrine names (BUG-0076): a laptop, a wide screen and a phone.
WIDTHS = ((1280, 800), (1920, 1000), (390, 844))

# The element groups a pair of boxes may not overlap in. Cards are the ones the defect was measured
# on; the others are every other group that lays out in a row or a column, so a fix that moved the
# overlap somewhere else is not a fix.
GROUPS = {
    "cards in a slot": ".slot > .card",
    "rows in a focus list": ".focus-list li",
    "the three figures": ".figures > .figure",
    "tree rows": ".tree .node-face",
    "slot headers": ".slot > h3",
}

_RECTS = """(selector) => Array.from(document.querySelectorAll(selector))
  .filter(el => el.offsetParent !== null)
  .map(el => { const r = el.getBoundingClientRect();
    return {x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height,
            id: (el.getAttribute('data-open') || el.textContent.trim().slice(0, 40))}; })"""

# The DOCUMENT against the window. `scrollWidth > clientWidth` on an ELEMENT is what the design
# pass measured overflow with, and it cannot see this class at all: an element that GROWS to fit its
# content has `scrollWidth == clientWidth` and reports nothing, while the page around it gets a
# horizontal scrollbar. So the subject here is the document, which cannot grow.
_DOCUMENT = """() => ({doc: document.documentElement.scrollWidth,
                       client: document.documentElement.clientWidth})"""

_EXTENT = """() => { const vw = document.documentElement.clientWidth; let right = 0;
  document.querySelectorAll('.type .slot').forEach(el => { if (el.offsetParent === null) return;
    right = Math.max(right, el.getBoundingClientRect().right + window.scrollX); });
  return {viewport: vw, right: Math.round(right),
          pad: parseFloat(getComputedStyle(document.body).paddingRight)}; }"""


def _overlaps(rects):
    """Every PAIR of boxes that intersects by more than a pixel in BOTH axes.

    One pixel, because sub-pixel rounding in a layout engine is not an overlap a reader can see,
    while the defect this was written against overlapped by a visible margin over a whole card
    height (`project_memory/staging/TSK-0115/layout-before.md`).
    """
    found = []
    for first in range(len(rects)):
        one = rects[first]
        for second in range(first + 1, len(rects)):
            two = rects[second]
            dx = min(one["x"] + one["w"], two["x"] + two["w"]) - max(one["x"], two["x"])
            dy = min(one["y"] + one["h"], two["y"] + two["h"]) - max(one["y"], two["y"])
            if dx > 1 and dy > 1:
                found.append((one["id"], two["id"], round(dx), round(dy)))
    return found


def _crowded_store(tmp_path):
    """A store with two NEIGHBOURING slots filled in one row -- the shape the defect needed.

    A board whose every type has one occupied slot cannot show an overlap between slots at all, so
    a fixture like that would have been green through the whole defect.
    """
    state = _state(tmp_path)
    first = state.capture("PR", PR_FIELDS)
    approve(state, first["id"], "scope")                     # DRAFT and APPROVED, side by side
    state.capture("PR", dict(PR_FIELDS, title="a second root with a rather long title on it"))
    state.capture("SR", dict(SR_FIELDS, derives_from=first["id"]))
    state.capture("BUG", dict(BUG_FIELDS, related_pr=first["id"]))
    stuck = state.capture("TSK", dict(TSK_FIELDS, product_requirement=first["id"],
                                      derives_from=first["id"], blocked_by=first["id"]))
    moving = state.capture("TSK", dict(TSK_FIELDS, product_requirement=first["id"],
                                       derives_from=first["id"]))
    walk_to_status(state, moving, "READY")
    state.generate_index()
    assert stuck["id"] and moving["id"]
    return os.path.join(state.root, "generated", board.FILENAME)


def _url(path):
    return "file:///" + os.path.abspath(path).replace("\\", "/")


def _pages(path, widths=WIDTHS):
    """One browser, one page per width, every tab visited -- the sighting loop as a generator."""
    with playwright_api.sync_playwright() as driver:
        browser = driver.chromium.launch(headless=True)
        for width, height in widths:
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(_url(path))
            page.wait_for_load_state("load")
            yield page, width
            page.close()
        browser.close()


def test_no_two_cards_of_the_board_overlap_at_any_width(tmp_path):
    """The defect phase 1d measured and the rule that fixed it, as a check.

    `.card` starts with `all: unset`, which puts `box-sizing` back to `content-box` underneath the
    global `border-box` rule; with horizontal padding and a border every 100 %-wide card was wider
    than its slot and reached into the neighbouring one. At 390 px the stacked layout had a second
    cause: a flex BASIS that becomes a HEIGHT, so the slot shrank under its own cards. The pair
    counts per width, before and after, are in
    `project_memory/staging/TSK-0115/layout-before.md` and `layout-after.md`. Both causes are
    measured here, over every group that lays out in a row or a column, so a fix that moves the
    overlap somewhere else does not pass.
    """
    path = _crowded_store(tmp_path)
    for page, width in _pages(path):
        for key, _selected, _tag in [(tab.get_attribute("data-tab"), None, None)
                                     for tab in page.locator("[data-tab]").all()]:
            page.click('[data-tab="%s"]' % key)
            if key == "board":
                for focus in ("blocked", "you", "flight"):
                    page.click('button[data-focus="%s"]' % focus)     # unroll the list
                    for name, selector in GROUPS.items():
                        hits = _overlaps(page.evaluate(_RECTS, selector))
                        assert not hits, (width, key, focus, name, hits[:3])
                    page.click('button[data-focus="%s"]' % focus)     # ...and roll it back up
            for name, selector in GROUPS.items():
                hits = _overlaps(page.evaluate(_RECTS, selector))
                assert not hits, (width, key, name, hits[:3])


def test_the_board_uses_the_width_it_is_given(tmp_path):
    """A row of slots at a FIXED width left the right of the board empty at every window size -- a
    board that ignores the window it is in (the empty margin per width is in
    `project_memory/staging/TSK-0115/layout-before.md`). The rule that fixed it is `flex: 1 1 15rem`
    on a slot with cards, so what is measured here is the right edge of the widest slot against the
    window."""
    path = _crowded_store(tmp_path)
    for page, width in _pages(path, widths=((1280, 800), (1920, 1000))):
        extent = page.evaluate(_EXTENT)
        assert extent["right"] >= extent["viewport"] - extent["pad"] - 1, (width, extent)


def test_a_fold_control_works_by_keyboard_and_shows_its_focus(tmp_path):
    """A control only a mouse can reach is not a control. Tab reaches the fold button because it IS
    a `<button>`, Enter folds it, and `:focus-visible` draws a ring so a keyboard user can see
    where they are. Measured in the engine, because "the CSS says outline" is not the same claim.
    """
    state, _pr, _sr, _bug, _under_sr, _under_root = _dev_store(tmp_path)
    path = os.path.join(state.root, "generated", board.FILENAME)
    for page, width in _pages(path, widths=((1280, 800),)):
        page.click('[data-tab="system"]')
        control = page.locator('[data-view="system"] [data-fold]').first
        node = control.get_attribute("data-fold")
        groups = page.locator('[data-view="system"] [data-group-parent="%s"]' % node)
        assert groups.count(), node
        before = control.get_attribute("aria-expanded")
        control.focus()
        page.keyboard.press("Enter")
        assert control.get_attribute("aria-expanded") != before, (width, node, before)
        hidden = [groups.nth(index).get_attribute("hidden") for index in range(groups.count())]
        assert set(hidden) == {None if before == "false" else ""}, (before, hidden)
        ring = control.evaluate("el => getComputedStyle(el).outlineStyle")
        assert ring and ring != "none", ("the focused fold control draws no ring", ring)


def test_ruler_labels_share_no_band(tmp_path, milestone_type):  # noqa: F811
    """TWO neighbouring labels do not share a band: the today marker owns the top one and a tick
    label within `board.LABEL_BAND_GAP` per cent of its neighbour takes the middle one instead of
    the bottom one. The design pass measured the overlap the single band produced and its absence
    afterwards, at all three widths (`project_memory/staging/TSK-0115/layout-before.md`,
    `layout-after.md`).

    THE FIXTURE IS TWO MARKS AND TODAY, and that is the claim -- not "no two labels can ever share
    a band". The rule alternates between two bands, so THREE marks inside one gap put the third
    back where the first is; `board._timeline_view` names that limit and this test does not measure
    past it, because a test whose name is wider than its fixture is the second-worst kind of green.
    """
    state, pr, _sr, _bug, _under_sr, _under_root = _dev_store(tmp_path)
    entries = _entries_of(state) + [_milestone(1, "2026-08-17", [pr["id"]]),
                                    _milestone(2, "2026-08-18", [pr["id"]])]
    path = str(tmp_path / "timeline.html")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(board.render(state, entries, "2026-08-16T12:00:00"))
    for page, width in _pages(path):
        page.click('[data-tab="timeline"]')
        labels = page.evaluate(_RECTS, ".ruler .tick .id, .ruler .today span")
        assert len(labels) == 3, (width, labels)      # two marks a day apart, plus today
        assert not _overlaps(labels), (width, _overlaps(labels))


# The two shapes a title takes when it has no break opportunity in it. The first is not invented:
# it is what an item of THIS repo is called (`test_hooks.test_the_documented_dashboard_command
# _survives_the_write_scope_gate` names files the same way), which is why the class was reachable
# with ordinary content and not only with an attack.
_PATH_TITLE = "team-kits/dev-team/templates/repo/scripts/progress.dashboard.template.html"
_ONE_LONG_WORD = "x" * 140


def _unbreakable_store(tmp_path):
    """A store whose titles cannot be broken between words, on every face the page has."""
    state = _state(tmp_path, "unbreakable")
    pr = state.capture("PR", dict(PR_FIELDS, title=_PATH_TITLE))
    state.capture("SR", dict(SR_FIELDS, derives_from=pr["id"], title=_ONE_LONG_WORD))
    state.capture("BUG", dict(BUG_FIELDS, related_pr=pr["id"], title=_PATH_TITLE,
                              blocked_by=pr["id"]))
    state.capture("TSK", dict(TSK_FIELDS, product_requirement=pr["id"], derives_from=pr["id"]))
    sys.path.insert(0, TEAM_KITS)
    from kernel import approvals
    approvals.create_pending_request(state, "scope", pr["id"], ttl_seconds=3600.0)
    state.generate_index()
    return os.path.join(state.root, "generated", board.FILENAME)


def test_a_title_that_is_one_long_word_does_not_widen_the_page(tmp_path):
    """A page wider than its window is a page with a horizontal scrollbar, and on a phone that is
    the difference between reading the board and dragging it.

    THE SUBJECT IS THE DOCUMENT AND NOT AN ELEMENT, and that is the half without which this class
    stays invisible. The overflow probe of the design pass asks each element whether its content
    overflows IT (`scrollWidth > clientWidth`) -- and a grid track sized `auto` does not overflow,
    it GROWS, so the probe reported nothing while the page around it had a scrollbar. Measured at
    390 px with a real title of this repo (a path of seventy-odd characters): the probe said 0
    overflows and the document stood 171 px wider than the window.

    Every tab, both focus lists open and a record open, because each of those is a different set of
    grid tracks that a long word can push apart.
    """
    path = _unbreakable_store(tmp_path)
    for page, width in _pages(path):
        for tab in [one.get_attribute("data-tab") for one in page.locator("[data-tab]").all()]:
            page.click('[data-tab="%s"]' % tab)
            probes = [None]
            if tab == "board":
                probes = ["blocked", "you", None]
            for focus in probes:
                if focus:
                    page.click('button[data-focus="%s"]' % focus)
                got = page.evaluate(_DOCUMENT)
                assert got["doc"] <= got["client"] + 1, (width, tab, focus, got)
                if focus:
                    page.click('button[data-focus="%s"]' % focus)
        page.click('[data-tab="board"]')
        page.locator("button.card").first.click()
        got = page.evaluate(_DOCUMENT)
        assert got["doc"] <= got["client"] + 1, ("with a record open", width, got)
