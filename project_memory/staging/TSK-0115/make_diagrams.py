#!/usr/bin/env python3
"""
make_diagrams.py -- PROTOTYPE of FR-0080: the implementation plan and the mindmap as .drawio.svg,
GENERATED from the same entries the board renders, never maintained by hand.

What a generated .drawio.svg is here (docs/research/2026-07-27-plan-als-diagramm.md, section 1):
a valid SVG whose root carries the whole draw.io document, uncompressed, in its `content`
attribute, so draw.io / the VS Code extension open it as an editable diagram while every browser
renders the SVG half. BOTH halves come from ONE layout pass in this file: the geometry is a grid,
computed by multiplication, no layout library, no Chromium, no JVM.

HOW A HAND EDIT IS DETECTED (the FR-0080 acceptance line): the file is a pure function of the
entries -- no clock, no random ids -- so `is_pristine(path, entries)` re-renders and compares
bytes. The root also carries `data-source-digest`, a sha256 over the canonical entry list the
file was rendered from; with it the two failure modes are told apart: same digest + different
bytes = somebody edited the file; different digest = the state moved on and the file is stale.
Phase 2 turns this into `kernel/plan_diagram.py` and the tests 04-build-spec.md names.

Usage: python make_diagrams.py --root <dir holding project_memory/> --out <dir> [--name "Project"]
"""
import argparse
import hashlib
import html
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
TEAM_KITS = os.environ.get("HARNESS_KERNEL_PATH") or "C:/Offline Repos/v2-testbed/_worktrees/g3-board/team-kits"
sys.path.insert(0, TEAM_KITS)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kernel import backlog_tree  # noqa: E402
from kernel.state import ProjectState  # noqa: E402
from make_mockups import DONE, FLIGHT, NEW, face_title, label, lane, read_entries  # noqa: E402

GENERATOR = "plan_diagram prototype 2026-09-03"
LANES = ((NEW, "planned"), (FLIGHT, "in flight"), (DONE, "done"))
# one palette, named, no other hex anywhere below (the research note's gate "no hard-coded colour")
INK = "#16181c"
PAPER = "#ffffff"
RULE = "#c9ced6"
LANE_FILL = {NEW: "#eceef1", FLIGHT: "#dfe6f5", DONE: "#d9ead3"}
LATE = "#b4121b"
FONT = "Segoe UI, system-ui, sans-serif"
TEXT_MAX = 58


def canonical(entries):
    """What the diagrams are a function of: id, type, status, title and parents, sorted."""
    rows = []
    for row, body in entries:
        node = backlog_tree.Node(row, body)
        rows.append([str(row.get("id") or ""), str(row.get("type") or ""), str(row.get("status") or ""),
                     str(row.get("title") or ""), backlog_tree.parents_of(node)])
    return json.dumps(sorted(rows), ensure_ascii=False, separators=(",", ":"))


def digest_of(entries):
    return hashlib.sha256(canonical(entries).encode("utf-8")).hexdigest()


def clip(text, limit=TEXT_MAX):
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


class Sheet:
    """Collects SVG elements and the matching mxCells, from one pass."""

    def __init__(self):
        self.svg, self.cells, self.n = [], [], 1

    def box(self, x, y, w, h, text, fill=PAPER, stroke=INK, bold=False, small=False):
        self.n += 1
        cell_id = "c%d" % self.n
        size = 10 if small else 12
        self.svg.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s" stroke="%s"/>' % (x, y, w, h, fill, stroke))
        self.svg.append('<text x="%d" y="%d" font-family="%s" font-size="%d"%s fill="%s">%s</text>'
                        % (x + 6, y + h // 2 + size // 3, FONT, size, ' font-weight="600"' if bold else "", INK, html.escape(text)))
        style = "rounded=1;whiteSpace=wrap;html=1;fillColor=%s;strokeColor=%s;fontSize=%d;%s" % (
            fill, stroke, size, "fontStyle=1;" if bold else "")
        self.cells.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1"><mxGeometry x="%d" y="%d" width="%d" height="%d" as="geometry"/></mxCell>'
                          % (cell_id, html.escape(text, quote=True), style, x, y, w, h))
        return cell_id

    def line(self, x1, y1, x2, y2, source=None, target=None):
        self.n += 1
        self.svg.append('<path d="M%d %d L%d %d L%d %d" fill="none" stroke="%s"/>' % (x1, y1, x1, y2, x2, y2, RULE))
        if source and target:
            self.cells.append('<mxCell id="c%d" style="edgeStyle=orthogonalEdgeStyle;endArrow=none;strokeColor=%s;" edge="1" parent="1" source="%s" target="%s"><mxGeometry relative="1" as="geometry"/></mxCell>'
                              % (self.n, RULE, source, target))

    def text(self, x, y, text, size=13, bold=True):
        self.svg.append('<text x="%d" y="%d" font-family="%s" font-size="%d"%s fill="%s">%s</text>'
                        % (x, y, FONT, size, ' font-weight="600"' if bold else "", INK, html.escape(text)))
        self.n += 1
        self.cells.append('<mxCell id="c%d" value="%s" style="text;html=1;fontSize=%d;%s" vertex="1" parent="1"><mxGeometry x="%d" y="%d" width="300" height="20" as="geometry"/></mxCell>'
                          % (self.n, html.escape(text, quote=True), size, "fontStyle=1;" if bold else "", x, y - 14))


def wrap(sheet, width, height, name, digest):
    """The .drawio.svg: SVG geometry + the whole mxfile in `content`, both from `sheet`."""
    model = ('<mxfile host="%s" agent="%s"><diagram id="d1" name="%s"><mxGraphModel dx="0" dy="0" grid="1" '
             'gridSize="10" guides="1" page="1" pageWidth="%d" pageHeight="%d"><root><mxCell id="0"/>'
             '<mxCell id="1" parent="0"/>%s</root></mxGraphModel></diagram></mxfile>'
             % (GENERATOR, GENERATOR, html.escape(name, quote=True), width, height, "".join(sheet.cells)))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
            'data-generator="%s" data-source-digest="%s" content="%s">\n'
            '<rect width="%d" height="%d" fill="%s"/>\n%s\n</svg>\n'
            % (width, height, width, height, GENERATOR, digest, html.escape(model, quote=True),
               width, height, PAPER, "\n".join(sheet.svg)))


def plan(entries, name):
    """The implementation plan: one row per root, three lanes (planned / in flight / done), every
    item under the root in plain words in the lane its own status puts it in."""
    system = backlog_tree.arrange(backlog_tree.VIEWS[1], entries)
    sheet = Sheet()
    col_w, box_h, gap, left = 300, 22, 4, 260
    width = left + 3 * (col_w + 20) + 20
    y = 50
    sheet.text(20, 30, "%s — implementation plan" % name, size=16)
    for index, (key, word) in enumerate(LANES):
        sheet.box(left + index * (col_w + 20), y, col_w, box_h, word, fill=LANE_FILL[key], bold=True)
    y += box_h + 16
    for root in system.roots:
        by_lane = {NEW: [], FLIGHT: [], DONE: []}
        stack = list(root.children)
        while stack:
            node = stack.pop(0)
            key = lane(node.item_type, node.row.get("status"))
            if key in by_lane:
                by_lane[key].append(node)
            stack.extend(node.children)
        rows = max(1, max(len(v) for v in by_lane.values()))
        block_h = rows * (box_h + gap)
        root_id = sheet.box(20, y, left - 40, block_h, clip("%s %s" % (root.item_id, root.row.get("title") or ""), 34), bold=True)
        for index, (key, _word) in enumerate(LANES):
            x = left + index * (col_w + 20)
            for k, node in enumerate(sorted(by_lane[key], key=lambda n: n.item_id)):
                text = "%s: %s" % (label(node.item_type), clip(face_title(node.row, node.body, node.item_type), 44))
                cell = sheet.box(x, y + k * (box_h + gap), col_w, box_h, text, fill=LANE_FILL[key], stroke=RULE, small=True)
                if k == 0:
                    sheet.line(left - 20, y + box_h // 2, x, y + box_h // 2, root_id, cell)
        if not any(by_lane.values()):
            sheet.box(left, y, col_w, box_h, "nothing under this root yet", fill=PAPER, stroke=RULE, small=True)
        y += block_h + 14
    if not system.roots:
        sheet.text(20, y + 10, "no root item yet — the plan starts with the first product requirement", size=12, bold=False)
        y += 40
    return wrap(sheet, width, y + 20, name + " — plan", digest_of(entries))


def mindmap(entries, name):
    """The mindmap: project -> roots -> kinds of things -> the things, to the right, leaf-stacked."""
    system = backlog_tree.arrange(backlog_tree.VIEWS[1], entries)
    sheet = Sheet()
    box_h, gap = 22, 6
    x0, x1, x2, x3 = 20, 260, 500, 720
    leaf_w = 360
    y = 40
    branches = []
    for root in system.roots:
        groups = root.grouped_children(backlog_tree.VIEWS[1])
        leaves = []
        for item_type, area, children in groups:
            kind = label(item_type, len(children)) + (" — " + area if area else "")
            leaves.append((kind, [(c, clip(face_title(c.row, c.body, c.item_type), 48)) for c in children]))
        branches.append((root, leaves))
    total_leaves = sum(max(1, sum(len(items) for _k, items in leaves)) for _r, leaves in branches) or 1
    height = y + total_leaves * (box_h + gap) + 60
    project_id = sheet.box(x0, height // 2 - box_h, 200, box_h * 2, clip(name, 30), bold=True)
    for root, leaves in branches:
        start = y
        count = max(1, sum(len(items) for _k, items in leaves))
        root_id = sheet.box(x1, start + (count * (box_h + gap)) // 2 - box_h // 2, 220, box_h,
                            clip("%s %s" % (root.item_id, root.row.get("title") or ""), 30), bold=True)
        sheet.line(x0 + 200, height // 2, x1, start + (count * (box_h + gap)) // 2, project_id, root_id)
        for kind, items in leaves:
            kind_id = sheet.box(x2, y + (len(items) * (box_h + gap)) // 2 - box_h // 2, 200, box_h, kind, fill=LANE_FILL[NEW], small=True)
            sheet.line(x1 + 220, start + (count * (box_h + gap)) // 2, x2, y + (len(items) * (box_h + gap)) // 2, root_id, kind_id)
            for node, text in items:
                key = lane(node.item_type, node.row.get("status"))
                # the lane is SAID on the leaf and not only coloured (WCAG 1.4.1, the research note's gate)
                word = dict(LANES).get(key, "")
                leaf_id = sheet.box(x3, y, leaf_w, box_h, "%s %s%s" % (node.item_id, text, (" — " + word) if word else ""),
                                    fill=LANE_FILL.get(key, PAPER), stroke=RULE, small=True)
                sheet.line(x2 + 200, y + (len(items) * (box_h + gap)) // 2 - box_h // 2 + box_h // 2, x3, y + box_h // 2, kind_id, leaf_id)
                y += box_h + gap
        if not leaves:
            y += box_h + gap
    if not branches:
        sheet.text(x1, height // 2, "no root item yet", size=12, bold=False)
    return wrap(sheet, x3 + leaf_w + 20, height, name + " — mindmap", digest_of(entries))


def validate(path):
    """What the kernel checks today (well-formed XML, `staging._assert_xml_wellformed`) plus what a
    draw.io file must carry: a `content` attribute holding an <mxfile> with a model and cells."""
    tree = ET.parse(path)
    root = tree.getroot()
    content = root.get("content")
    assert content, "no content attribute -- draw.io would open this as a plain image"
    model = ET.fromstring(content)
    assert model.tag == "mxfile", model.tag
    cells = model.findall("./diagram/mxGraphModel/root/mxCell")
    return {"svg_elements": len(list(root.iter())) - 1, "mx_cells": len(cells),
            "digest": root.get("data-source-digest"), "generator": root.get("data-generator")}


def is_pristine(path, entries, renderer, name):
    """(verdict, reason): pristine | hand-edited | stale | foreign."""
    with open(path, "rb") as fh:
        found = fh.read()
    fresh = renderer(entries, name).encode("utf-8")
    if found == fresh:
        return "pristine", "bytes equal to a fresh render"
    try:
        recorded = ET.parse(path).getroot().get("data-source-digest")
    except ET.ParseError:
        return "foreign", "not even XML"
    if recorded == digest_of(entries):
        return "hand-edited", "same source digest, different bytes"
    return "stale", "rendered from a state that has moved on (digest %s… vs %s…)" % ((recorded or "")[:8], digest_of(entries)[:8])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="Project")
    args = ap.parse_args()
    pm = os.path.join(args.root, "project_memory")
    entries = read_entries(ProjectState(pm))
    os.makedirs(args.out, exist_ok=True)
    for fname, renderer in (("plan.drawio.svg", plan), ("mindmap.drawio.svg", mindmap)):
        target = os.path.join(args.out, fname)
        text = renderer(entries, args.name)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("[diagram] %s %s -> %s" % (fname, validate(target), is_pristine(target, entries, renderer, args.name)))
    # the detection, demonstrated: (a) a label edited the way draw.io would rewrite it
    target = os.path.join(args.out, "plan.drawio.svg")
    edited = os.path.join(args.out, "plan-hand-edited.drawio.svg")
    tree = ET.parse(target)
    for node in tree.getroot().iter("{http://www.w3.org/2000/svg}text"):
        node.text = (node.text or "") + " (edited by hand)"
        break
    tree.write(edited, encoding="utf-8", xml_declaration=True)
    print("[detect] hand edit ->", is_pristine(edited, entries, plan, args.name))
    # (b) the same file against a state that moved on: one status changed
    moved = [(dict(row, status="APPROVED") if row["type"] == "PR" else row, body) for row, body in entries]
    print("[detect] state moved ->", is_pristine(target, moved, plan, args.name))
    print("[detect] untouched ->", is_pristine(target, entries, plan, args.name))
    # (c) determinism: two renders, same bytes
    print("[detect] two renders equal:", plan(entries, args.name) == plan(entries, args.name))


if __name__ == "__main__":
    main()
