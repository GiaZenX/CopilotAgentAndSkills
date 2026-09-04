"""Sight the three directions: the blocked state, board tab, 1280 and 390, light and dark, plus
the two focus states and one open record at 1280. review/directions/render.json ties images to
the HTML sha256."""
import datetime
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "directions")
OUT = os.path.join(HERE, "review", "directions")
VIEWPORTS = ((1280, 800), (390, 844))


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    record = {"rendered_at": datetime.datetime.now().replace(microsecond=0).isoformat(), "drafts": {}}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        only = set(sys.argv[1:])          # optional: render only these keys (e.g. d e)
        for name in sorted(n for n in os.listdir(SRC) if n.endswith(".html")
                           and (not only or n[len("direction-"):-len(".html")] in only)):
            key = name[len("direction-"):-len(".html")]
            entry = {"sha256": sha256(os.path.join(SRC, name)), "images": [], "errors": []}
            url = "file:///" + os.path.join(SRC, name).replace("\\", "/")
            for scheme in ("light", "dark"):
                for width, height in VIEWPORTS:
                    ctx = browser.new_context(viewport={"width": width, "height": height},
                                              color_scheme=scheme, locale="de-DE")
                    page = ctx.new_page()
                    page.on("pageerror", lambda exc: entry["errors"].append(str(exc)))
                    page.on("console", lambda msg: entry["errors"].append(msg.text) if msg.type == "error" else None)
                    page.goto(url)
                    page.wait_for_load_state("networkidle")
                    suffix = "-dark" if scheme == "dark" else ""
                    target = os.path.join(OUT, "%s-%d%s.png" % (key, width, suffix))
                    page.screenshot(path=target, full_page=False)
                    entry["images"].append(os.path.relpath(target, HERE).replace("\\", "/"))
                    if width == 1280:
                        for focus in ("blocked", "you"):
                            page.click('button[data-focus="%s"]' % focus)
                            target = os.path.join(OUT, "%s-%d%s-focus-%s.png" % (key, width, suffix, focus))
                            page.screenshot(path=target, full_page=False)
                            entry["images"].append(os.path.relpath(target, HERE).replace("\\", "/"))
                            page.click('button[data-focus="%s"]' % focus)
                        if scheme == "light":
                            page.locator("button.card").first.click()
                            target = os.path.join(OUT, "%s-%d-record.png" % (key, width))
                            page.screenshot(path=target, full_page=False)
                            entry["images"].append(os.path.relpath(target, HERE).replace("\\", "/"))
                            page.keyboard.press("Escape")
                    ctx.close()
            record["drafts"][name] = entry
            if entry["errors"]:
                sys.stderr.write("[render] %s: %s\n" % (name, entry["errors"]))
        browser.close()
    with open(os.path.join(OUT, "render.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
    print("[render] %d direction(s) -> %d image(s)" % (
        len(record["drafts"]), sum(len(d["images"]) for d in record["drafts"].values())))
    return 1 if any(d["errors"] for d in record["drafts"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())
