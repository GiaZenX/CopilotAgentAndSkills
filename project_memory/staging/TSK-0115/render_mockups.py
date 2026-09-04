#!/usr/bin/env python3
"""
render_mockups.py -- the SIGHT half of BUG-0076 for TSK-0115's design draft.

Renders every mockup-<state>.html beside this file at 1280 and 390 px, one PNG per tab, the dark
scheme at 1280 for every state, the two focus states (blocked / wartet auf dich) and one open
record, and writes review/render.json tying each PNG to the sha256 of the HTML it came from (the
shape kit_design_render.py records). Console and page errors are collected per draft; a non-empty
list is exit 1.

Usage: python render_mockups.py
"""
import datetime
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEW = os.path.join(HERE, "review")
VIEWPORTS = ((1280, 800), (390, 844))


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def shoot(page, target, full=True):
    page.screenshot(path=target, full_page=full)
    return os.path.relpath(target, HERE).replace("\\", "/")


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(REVIEW, exist_ok=True)
    mockups = sorted(n for n in os.listdir(HERE) if n.startswith("mockup-") and n.endswith(".html"))
    record = {"rendered_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
              "viewports": ["%dx%d" % v for v in VIEWPORTS], "drafts": {}}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name in mockups:
            state = name[len("mockup-"):-len(".html")]
            url = "file:///" + os.path.join(HERE, name).replace("\\", "/")
            entry = {"sha256": sha256(os.path.join(HERE, name)), "images": [], "errors": []}
            for scheme in ("light", "dark"):
                for width, height in VIEWPORTS:
                    if scheme == "dark" and width != 1280:
                        continue
                    ctx = browser.new_context(viewport={"width": width, "height": height},
                                              color_scheme=scheme, locale="de-DE")
                    page = ctx.new_page()
                    page.on("pageerror", lambda exc: entry["errors"].append(str(exc)))
                    page.on("console", lambda msg: entry["errors"].append(msg.text) if msg.type == "error" else None)
                    page.goto(url)
                    page.wait_for_load_state("networkidle")
                    suffix = "-dark" if scheme == "dark" else ""
                    tabs = [b.get_attribute("data-tab") for b in page.locator("[data-tab]").all()]
                    for tab in tabs:
                        page.click('[data-tab="%s"]' % tab)
                        # the board of the full real state is long; the viewport is what a reader
                        # meets first and is what is judged, the trees are shot whole
                        entry["images"].append(shoot(page, os.path.join(REVIEW, "%s-%s-%d%s.png" % (state, tab, width, suffix)),
                                                     full=(tab != "board" or state != "blocked")))
                    page.click('[data-tab="board"]')
                    if scheme == "light":
                        for key in ("blocked", "you", "flight"):
                            fig = page.locator('button[data-focus="%s"]' % key)
                            if fig.count():
                                fig.click()
                                entry["images"].append(shoot(page, os.path.join(REVIEW, "%s-board-%d-focus-%s.png" % (state, width, key)),
                                                             full=(state != "blocked")))
                                fig.click()
                        if width == 1280:
                            cards = page.locator("button.card")
                            if cards.count():
                                cards.first.click()
                                entry["images"].append(shoot(page, os.path.join(REVIEW, "%s-record-open-%d.png" % (state, width)), full=False))
                                page.keyboard.press("Escape")
                            rec = page.locator("details.records summary")
                            if rec.count():
                                rec.click()
                                page.locator("details.records").scroll_into_view_if_needed()
                                entry["images"].append(shoot(page, os.path.join(REVIEW, "%s-records-open-%d.png" % (state, width)), full=False))
                    ctx.close()
            record["drafts"][name] = entry
            if entry["errors"]:
                sys.stderr.write("[render] %s: %s\n" % (name, entry["errors"]))
        browser.close()
    with open(os.path.join(REVIEW, "render.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
    total = sum(len(d["images"]) for d in record["drafts"].values())
    print("[render] %d draft(s) -> %d image(s) in %s" % (len(record["drafts"]), total, REVIEW))
    return 1 if any(d["errors"] for d in record["drafts"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())
