#!/usr/bin/env python3
"""
render_mockups.py -- the SIGHT half of BUG-0076 for TSK-0109's design draft.

Renders every mockup-<state>.html beside this file at 1280 and 390 px wide, one PNG per tab, plus
the dark scheme and two filtered states, and writes review/render.json tying each PNG to the sha256
of the HTML it came from (the shape kit_design_render.py records). The viewer's clock is FROZEN at
2026-09-02 so the ages of open items are the same on every run.

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
FROZEN_NOW = datetime.datetime(2026, 9, 2, 10, 0, 0)
TABS = ("ueberblick", "rechnungen", "offene-posten", "euer", "kleinunternehmer")


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(REVIEW, exist_ok=True)
    mockups = sorted(n for n in os.listdir(HERE) if n.startswith("mockup-") and n.endswith(".html"))
    record = {"rendered_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
              "frozen_clock": FROZEN_NOW.isoformat(), "drafts": {}}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name in mockups:
            state = name[len("mockup-"):-len(".html")]
            url = "file:///" + os.path.join(HERE, name).replace("\\", "/")
            shots = []
            for scheme in ("light", "dark"):
                for width, height in VIEWPORTS:
                    if scheme == "dark" and (width != 1280 or state != "regular"):
                        continue
                    ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme,
                                              locale="de-DE")
                    page = ctx.new_page()
                    page.clock.install(time=FROZEN_NOW)
                    errors = []
                    page.on("pageerror", lambda exc: errors.append(str(exc)))
                    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
                    page.goto(url)
                    page.wait_for_load_state("networkidle")
                    for tab in TABS:
                        button = page.locator('[role="tab"][data-view="%s"]' % tab)
                        if button.count() == 0:
                            continue
                        button.click()
                        target = os.path.join(REVIEW, "%s-%s-%d%s.png" % (state, tab, width, "-dark" if scheme == "dark" else ""))
                        # the invoice list is the one view whose full page is the whole ledger; the
                        # viewport shows what a reader sees first, which is what is judged here
                        page.screenshot(path=target, full_page=(tab != "rechnungen"))
                        shots.append(os.path.relpath(target, HERE).replace("\\", "/"))
                        if scheme == "light" and width == 1280 and state == "regular":
                            if tab == "rechnungen":
                                page.select_option('select[data-filter="dir"]', "income")
                                page.select_option('select[data-filter="status"]', "offen")
                                target = os.path.join(REVIEW, "%s-rechnungen-1280-filter-einnahmen-offen.png" % state)
                                page.screenshot(path=target, full_page=True)
                                shots.append(os.path.relpath(target, HERE).replace("\\", "/"))
                                page.click('table.ledger.full tbody tr:not([hidden]):not(.detail) >> nth=0')
                                target = os.path.join(REVIEW, "%s-rechnungen-1280-detail-open.png" % state)
                                page.screenshot(path=target, full_page=False)
                                shots.append(os.path.relpath(target, HERE).replace("\\", "/"))
                                page.click('button[type="reset"]')
                            if tab == "offene-posten":
                                page.check('input[data-filter="overdue"]')
                                target = os.path.join(REVIEW, "%s-offene-posten-1280-nur-mahnkandidaten.png" % state)
                                page.screenshot(path=target, full_page=True)
                                shots.append(os.path.relpath(target, HERE).replace("\\", "/"))
                                page.uncheck('input[data-filter="overdue"]')
                    if errors:
                        sys.stderr.write("[render] %s %s %dpx: console/page errors: %s\n" % (name, scheme, width, errors))
                    record["drafts"].setdefault(name, {"sha256": sha256(os.path.join(HERE, name)), "images": [], "errors": []})
                    record["drafts"][name]["errors"].extend(errors)
                    ctx.close()
            record["drafts"][name]["images"] = shots
        browser.close()
    with open(os.path.join(REVIEW, "render.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
    total = sum(len(d["images"]) for d in record["drafts"].values())
    print("[render] %d draft(s) -> %d image(s) in %s" % (len(record["drafts"]), total, REVIEW))
    return 1 if any(d["errors"] for d in record["drafts"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())
