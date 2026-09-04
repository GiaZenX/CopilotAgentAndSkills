"""Sight the generated .drawio.svg files in Chromium (the SVG half) -- one PNG each, 1280 wide."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main(folder):
    from playwright.sync_api import sync_playwright
    out = os.path.join(HERE, "review")
    os.makedirs(out, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".drawio.svg"):
                continue
            # an SVG document as the top-level page hung Chromium's full-page screenshot
            # (30 s timeout, measured); the SVG in an <img> is what a browser shows for the file
            # anyway, so the size is read off the root and the page is sized to it
            import xml.etree.ElementTree as ET
            root = ET.parse(os.path.join(folder, name)).getroot()
            width, height = int(float(root.get("width"))), int(float(root.get("height")))
            page = browser.new_page(viewport={"width": min(width, 1600), "height": min(height, 1600)})
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            # a wrapper FILE beside the svg: an about:blank page (set_content) may not load file:// images
            wrapper = os.path.join(folder, name + ".view.html")
            with open(wrapper, "w", encoding="utf-8") as fh:
                fh.write('<html><body style="margin:0"><img src="%s" width="%d" height="%d"></body></html>'
                         % (name, width, height))
            page.goto("file:///" + wrapper.replace("\\", "/"))
            page.wait_for_load_state("networkidle")
            target = os.path.join(out, "diagram-%s.png" % name.replace(".drawio.svg", ""))
            page.screenshot(path=target, full_page=True)
            print("[render]", target, "errors:", errors)
            page.close()
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1])
