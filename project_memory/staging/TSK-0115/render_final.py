"""Sight the final E over every state: 1280 / 1920 / 390, light and dark, every tab; at 1280 light also
the two focus states, an open record, the records block, and the system tree default vs expanded.
Writes review/final/render.json (images bound to the sha256 of each page)."""
import datetime
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "final")
OUT = os.path.join(HERE, "review", "final")
VIEWPORTS = ((1280, 800), (1920, 1000), (390, 844))


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    record = {"rendered_at": datetime.datetime.now().replace(microsecond=0).isoformat(), "drafts": {}}

    def shot(page, entry, name, full=False):
        target = os.path.join(OUT, name + ".png")
        page.screenshot(path=target, full_page=full)
        entry["images"].append(os.path.relpath(target, HERE).replace("\\", "/"))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name in sorted(n for n in os.listdir(SRC) if n.endswith(".html")):
            state = name[len("final-"):-len(".html")]
            entry = {"sha256": sha256(os.path.join(SRC, name)), "images": [], "errors": []}
            url = "file:///" + os.path.join(SRC, name).replace("\\", "/")
            for scheme in ("light", "dark"):
                for width, height in VIEWPORTS:
                    ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme, locale="de-DE")
                    page = ctx.new_page()
                    page.on("pageerror", lambda exc: entry["errors"].append(str(exc)))
                    page.on("console", lambda msg: entry["errors"].append(msg.text) if msg.type == "error" else None)
                    page.goto(url)
                    page.wait_for_load_state("networkidle")
                    sfx = "-dark" if scheme == "dark" else ""
                    tabs = [b.get_attribute("data-tab") for b in page.locator("[data-tab]").all()]
                    for tab in tabs:
                        page.click('[data-tab="%s"]' % tab)
                        shot(page, entry, "%s-%s-%d%s" % (state, tab, width, sfx),
                             full=(tab in ("product", "system") and width == 1280 and scheme == "light"))
                        # scoped to the system view: the product view carries the same controls, hidden
                        sysview = '[data-view="system"] '
                        if tab == "system" and width == 1280 and scheme == "light" and page.locator(sysview + '[data-fold-all="expand"]').count():
                            page.click(sysview + '[data-fold-all="expand"]')
                            shot(page, entry, "%s-system-%d-expanded" % (state, width), full=True)
                            page.click(sysview + '[data-fold-all="collapse"]')
                            shot(page, entry, "%s-system-%d-collapsed" % (state, width), full=True)
                            # keyboard path: focus the first fold control and press Enter
                            first = page.locator(sysview + "[data-fold]").first
                            first.focus()
                            page.keyboard.press("Enter")
                            shot(page, entry, "%s-system-%d-keyboard-open" % (state, width), full=False)
                    page.click('[data-tab="board"]')
                    if width == 1280 and scheme == "light":
                        for key in ("blocked", "you"):
                            fig = page.locator('button[data-focus="%s"]' % key)
                            if fig.count():
                                fig.click()
                                shot(page, entry, "%s-board-%d-focus-%s" % (state, width, key))
                                fig.click()
                        cards = page.locator("button.card")
                        if cards.count():
                            cards.first.click()
                            shot(page, entry, "%s-record-%d" % (state, width))
                            page.keyboard.press("Escape")
                        rec = page.locator("details.records summary")
                        if rec.count():
                            rec.click()
                            page.locator("details.records").scroll_into_view_if_needed()
                            shot(page, entry, "%s-records-%d" % (state, width))
                    ctx.close()
            record["drafts"][name] = entry
            if entry["errors"]:
                sys.stderr.write("[render] %s: %s\n" % (name, entry["errors"]))
        browser.close()
    with open(os.path.join(OUT, "render.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
    print("[render] %d state(s) -> %d image(s)" % (len(record["drafts"]), sum(len(d["images"]) for d in record["drafts"].values())))
    return 1 if any(d["errors"] for d in record["drafts"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())
