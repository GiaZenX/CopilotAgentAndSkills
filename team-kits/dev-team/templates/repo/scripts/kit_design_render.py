#!/usr/bin/env python3
"""
kit_design_render.py — KIT-OWNED design render (draft phase). DO NOT EDIT IN THE PROJECT.

Renders every staged design draft of ONE task to PNG at the configured viewports, optionally
beside the reference sites the design ambition names, and writes the RECORD `gate_design_sighted`
reads. Its subject is the DRAFT — the self-contained HTML the designer stages before anyone has
seen it — where `kit_browser_checks.py` renders the BUILT app after implementation.

WHY IT EXISTS: in a real project (Canyon, 2026-08-30) a design revision reached the user twice
without anyone ever rendering it; both rounds were rejected on things only pixels show ("teilweise
linksbuendig statt mittig"). Every screenshot duty in this kit was conditioned on "after
implementation", so the draft phase had the user as its first pair of eyes by construction.

THE COMMAND LINE NAMES A TASK ID, NEVER A PATH INSIDE `project_memory/`, and that is not a
convenience: `gate_write_scope` refuses any write-capable shell pipeline that names the state
directory, so `--source project_memory/staging/<id>/x.html` would be refused before this script
ever started. The id resolves to `project_memory/staging/<id>/` here instead.

  python scripts/kit_design_render.py TSK-0007
  python scripts/kit_design_render.py TSK-0007 --reference https://example.com --reference ...

FAILS LOUD, never silently skips: no Playwright, no browser binary, no staged HTML and no page
that loads are each exit 2 with the command that fixes them. A render that did not happen must not
look like one that did — the record is the evidence a gate consumes, so a half-written record would
buy a presentation nobody sighted. An unreachable REFERENCE is the one degradation: it is recorded
with its error and the run continues, because a site being down is not a reason to stop looking at
your own draft.

WHAT THE RECORD SAYS AND WHAT IT DOES NOT: it TIES a set of images to the exact bytes they were
made from (sha256). It is not evidence that a browser ran — anything with a shell can write the
same file — and it says nothing about anyone having LOOKED. `gate_design_sighted` reads it as
provenance of the bytes and states that boundary in its own row of `hooks/ENFORCEMENT.md`; the
sighting duty is prose in the product-designer skill and stays there (`FR-0035`).

Every kit update OVERWRITES this file (like kit_checks.py), so fixes reach existing projects.
"""
import argparse
import datetime
import hashlib
import json
import os
import sys

# The two widths a design draft is judged at. ONE statement of them: the record repeats what it
# rendered, and every other reader (the gate, the skills) asks the record. Desktop first, because a
# reference site is loaded at the widest configured viewport only -- an external page is the slow
# part of a run, and it is looked at for its craft, not for its breakpoints.
DEFAULT_VIEWPORTS = ("1440x900", "390x844")
RECORD_NAME = "render.json"
REVIEW_DIR = "review"
INSTALL_HINT = ("pip install -r requirements-dev.txt && playwright install chromium")


def repo_root(start):
    """The project root — the nearest ancestor holding `project_memory/`."""
    here = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(here, "project_memory")):
            return here
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def staging_dir(root, task_id):
    return os.path.join(root, "project_memory", "staging", task_id)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def drafts_in(directory):
    """Every HTML draft staged for this task, EXCEPT what a previous run wrote.

    The review directory is excluded by name: a rendered artefact of this script must never become
    a subject of the next run.
    """
    found = []
    for base, dirs, names in os.walk(directory):
        dirs[:] = [d for d in dirs if d != REVIEW_DIR]
        for name in sorted(names):
            if name.lower().endswith((".html", ".htm")):
                found.append(os.path.join(base, name))
    return sorted(found)


def parse_viewport(text):
    width, _sep, height = str(text).lower().partition("x")
    return int(width), int(height)


def _slug(text):
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in text)[:60]


def render(task_id, references, viewports, root=None, out=sys.stderr):
    root = root or repo_root(os.getcwd())
    if not root:
        out.write("[design-render] no project_memory/ above %s — run this from the project.\n"
                  % os.getcwd())
        return 2
    item_dir = staging_dir(root, task_id)
    if not os.path.isdir(item_dir):
        out.write("[design-render] no staging directory for %s (%s). The designer stages its "
                  "draft there; render the task that owns the draft.\n" % (task_id, item_dir))
        return 2
    drafts = drafts_in(item_dir)
    if not drafts:
        out.write("[design-render] %s stages no .html draft — nothing to render. A wireframe "
                  "(.drawio.svg) is not this script's subject.\n" % task_id)
        return 2
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]
    except ImportError:
        out.write("[design-render] Playwright (Python) is not installed, so no draft can be "
                  "looked at. This is a hard stop, not a warning: a design draft that reaches the "
                  "user unrendered is the defect this step exists for.\nInstall: %s\n"
                  % INSTALL_HINT)
        return 2

    review = os.path.join(item_dir, REVIEW_DIR)
    os.makedirs(review, exist_ok=True)
    sizes = [parse_viewport(v) for v in viewports]
    record = {
        "tool": os.path.basename(__file__),
        "generated": datetime.datetime.now().replace(microsecond=0).isoformat(),
        "task": task_id,
        "viewports": list(viewports),
        "sources": [],
        "references": [],
    }
    try:
        with sync_playwright() as play:
            browser = play.chromium.launch()
            for draft in drafts:
                relative = os.path.relpath(draft, item_dir).replace(os.sep, "/")
                images = []
                for width, height in sizes:
                    page = browser.new_page(viewport={"width": width, "height": height})
                    page.goto("file:///" + os.path.abspath(draft).replace(os.sep, "/"),
                              wait_until="load", timeout=15000)
                    name = "%s__%dx%d.png" % (_slug(os.path.splitext(relative)[0]), width, height)
                    page.screenshot(path=os.path.join(review, name), full_page=True)
                    page.close()
                    images.append(REVIEW_DIR + "/" + name)
                record["sources"].append({"path": relative, "sha256": file_sha256(draft),
                                          "images": images})
            width, height = sizes[0]
            for index, url in enumerate(references, start=1):
                entry = {"url": url, "image": None, "error": None}
                name = "reference-%02d-%s__%dx%d.png" % (index, _slug(url), width, height)
                try:
                    page = browser.new_page(viewport={"width": width, "height": height})
                    page.goto(url, wait_until="load", timeout=20000)
                    page.screenshot(path=os.path.join(review, name), full_page=False)
                    page.close()
                    entry["image"] = REVIEW_DIR + "/" + name
                except Exception as exc:                     # noqa: BLE001 — see the module head
                    entry["error"] = str(exc)[:300]
                    out.write("[design-render] reference %s could not be loaded: %s\n"
                              % (url, entry["error"]))
                record["references"].append(entry)
            browser.close()
    except Exception as exc:                                 # noqa: BLE001
        message = str(exc)
        if "Executable doesn't exist" in message or "playwright install" in message:
            out.write("[design-render] the Chromium binary is missing, so nothing was rendered.\n"
                      "Install: playwright install chromium\n")
        else:
            out.write("[design-render] rendering failed: %s\n" % message[:500])
        return 2

    with open(os.path.join(review, RECORD_NAME), "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write("\n")
    out.write("[design-render] %d draft(s) x %d viewport(s) -> %s\n"
              % (len(drafts), len(sizes), os.path.join(review, "")))
    out.write("[design-render] NOW LOOK AT THEM. Read every PNG, compare against the frozen "
              "wireframe and the references, fix what you see, and render again — the record only "
              "says the pixels exist.\n")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("task_id", help="the task whose staging directory holds the draft")
    parser.add_argument("--reference", action="append", default=[], metavar="URL",
                        help="a style reference (or the current site) to shoot beside the draft; "
                             "take the URLs from the design-ambition Decision item, never from a "
                             "list in this script")
    parser.add_argument("--viewport", action="append", default=[], metavar="WxH",
                        help="override the viewports (default: %s)" % ", ".join(DEFAULT_VIEWPORTS))
    args = parser.parse_args(argv)
    try:
        viewports = [v for v in (args.viewport or list(DEFAULT_VIEWPORTS))]
        for one in viewports:
            parse_viewport(one)
    except ValueError:
        sys.stderr.write("[design-render] a viewport is WIDTHxHEIGHT, e.g. 1440x900\n")
        return 2
    return render(args.task_id, args.reference, viewports)


if __name__ == "__main__":
    sys.exit(main())
