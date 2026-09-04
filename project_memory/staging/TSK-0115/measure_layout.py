"""Layout measurement (phase 1d): overlaps and unused width, per page, tab and viewport.

For every element group below it reads the bounding boxes in Chromium and reports every PAIR that
intersects by more than 1 px in both axes, every element whose text overflows its box, the widest
right edge of the board content against the viewport (the empty margin the user saw), and which
`.board` rows scroll horizontally. Output: a markdown table on stdout and a JSON file beside it.

Usage: python measure_layout.py <label> <html> [<html> ...]   (writes review/layout-<label>.json)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WIDTHS = ((1280, 800), (1920, 1000), (390, 844))
GROUPS = {
    "cards in a slot": ".slot > .card",
    "rows in a focus list": ".focus-list li",
    "the three figures": ".figures > .figure",
    "milestone cards": ".milestones > .milestone",
    "tree rows": ".tree .node-face",
    "ruler labels": ".ruler .tick .id, .ruler .today span",
    "slot headers": ".slot > h3",
}
OVERFLOW = ".card .title, .figure .ex, .figure .word, .node-face .title, .rec .title, .slot > h3, .ms-face .title"

JS_RECTS = """(sel) => Array.from(document.querySelectorAll(sel)).filter(e => e.offsetParent !== null || e.tagName === 'BODY')
  .map(e => { const r = e.getBoundingClientRect(); return {x: r.left + window.scrollX, y: r.top + window.scrollY, w: r.width, h: r.height,
  id: (e.getAttribute('data-open') || e.getAttribute('data-milestone') || e.textContent.trim().slice(0, 40))}; })"""
JS_OVERFLOW = """(sel) => Array.from(document.querySelectorAll(sel)).filter(e => e.offsetParent !== null && e.scrollWidth > e.clientWidth + 1)
  .map(e => ({text: e.textContent.trim().slice(0, 50), scroll: e.scrollWidth, client: e.clientWidth}))"""
JS_EXTENT = """() => { const vw = document.documentElement.clientWidth; let right = 0;
  document.querySelectorAll('.type .slot').forEach(e => { if (e.offsetParent === null) return;
    const r = e.getBoundingClientRect(); right = Math.max(right, r.right + window.scrollX); });
  const boards = Array.from(document.querySelectorAll('.type .board')).filter(e => e.offsetParent !== null);
  const scrolling = boards.filter(b => b.scrollWidth > b.clientWidth + 1).map(b => b.parentElement.getAttribute('data-type'));
  const pad = parseFloat(getComputedStyle(document.body).paddingRight);
  return {viewport: vw, right_edge: Math.round(right), empty_right: Math.round(vw - pad - right), scrolling_boards: scrolling, body_pad: pad}; }"""


def overlaps(rects):
    found = []
    for i in range(len(rects)):
        a = rects[i]
        for j in range(i + 1, len(rects)):
            b = rects[j]
            dx = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
            dy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
            if dx > 1 and dy > 1:
                found.append((a["id"], b["id"], round(dx), round(dy)))
    return found


def main(label, pages):
    from playwright.sync_api import sync_playwright
    report, lines = {}, ["| Seite | Reiter | Breite | Überlappungen | Textüberlauf | rechter Rand leer (px) | scrollende Zeilen |",
                         "|---|---|---|---|---|---|---|"]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for html in pages:
            name = os.path.basename(html)
            url = "file:///" + os.path.abspath(html).replace("\\", "/")
            for width, height in WIDTHS:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.goto(url)
                page.wait_for_load_state("networkidle")
                tabs = [b.get_attribute("data-tab") for b in page.locator("[data-tab]").all()] or ["board"]
                for tab in tabs:
                    if page.locator('[data-tab="%s"]' % tab).count():
                        page.click('[data-tab="%s"]' % tab)
                    if tab == "board":
                        for key in ("blocked", "you"):
                            if page.locator('button[data-focus="%s"]' % key).count():
                                page.click('button[data-focus="%s"]' % key)   # lists open, stay open for the measure
                    ov, of = {}, page.evaluate(JS_OVERFLOW, OVERFLOW)
                    for group, sel in GROUPS.items():
                        rects = page.evaluate(JS_RECTS, sel)
                        hits = overlaps(rects)
                        if hits:
                            ov[group] = hits
                    extent = page.evaluate(JS_EXTENT)
                    key = "%s|%s|%d" % (name, tab, width)
                    report[key] = {"overlaps": ov, "overflow": of, "extent": extent}
                    lines.append("| %s | %s | %d | %s | %s | %s | %s |" % (
                        name, tab, width,
                        "; ".join("%s: %d (z. B. %s/%s %dx%d)" % (g, len(h), h[0][0], h[0][1], h[0][2], h[0][3]) for g, h in ov.items()) or "0",
                        "%d (z. B. %s)" % (len(of), of[0]["text"][:30]) if of else "0",
                        extent["empty_right"], ", ".join(extent["scrolling_boards"]) or "—"))
                    if tab == "board":
                        for key2 in ("you", "blocked"):
                            if page.locator('button[data-focus="%s"]' % key2).count():
                                page.click('button[data-focus="%s"]' % key2)
                page.close()
        browser.close()
    text = "\n".join(lines)
    print(text)
    os.makedirs(os.path.join(HERE, "review"), exist_ok=True)
    with open(os.path.join(HERE, "review", "layout-%s.json" % label), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)
    with open(os.path.join(HERE, "review", "layout-%s.md" % label), "w", encoding="utf-8") as fh:
        fh.write(text + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
