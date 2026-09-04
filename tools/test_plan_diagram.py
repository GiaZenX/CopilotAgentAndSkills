"""The generated implementation plan and mindmap (FR-0080, DEC-0065 (2), TSK-0115).

EVERY CHECK HERE READS THE FILE THAT WOULD SHIP, parsed as XML -- both halves of it: the SVG a
browser draws and the draw.io model inside the root's `content` attribute. That is the whole point
of the format and it is where the pilot's own `.drawio.svg` fell short: it parsed as XML and
carried no model at all, so a tool opened it as a flat image. A check that only asked "is it
well-formed" would have passed that file.

The module is a PURE FUNCTION of the entries, so most of this suite hands it entries directly --
the same (index row, body) pairs `state._regenerate_index_locked` builds -- and only the shape
tests walk a real store through `capture`.
"""
import ast
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")
sys.path.insert(0, TEAM_KITS)

from kernel import backlog_tree, board, plan_diagram, staging  # noqa: E402
from kernel.state import ProjectState  # noqa: E402

MODULE = os.path.join(TEAM_KITS, "kernel", "plan_diagram.py")

PR_FIELDS = {
    "title": "Checkout flow",
    "class": "normal",
    "problem": "no checkout",
    "goal": "working checkout",
    "acceptance_criteria": [{"id": "AC-1", "text": "order completes"}],
    "invariants": [],
    "out_of_scope": ["payments"],
    "priority": "high",
}
SR_FIELDS = {
    "title": "checkout contract",
    "derives_from": "PR-0001",
    "contract": "POST /checkout returns 201",
    "affected_components": ["api"],
}
BUG_FIELDS = {
    "title": "crash on save",
    "related_pr": "PR-0001",
    "observed": "it crashes",
    "expected": "it saves",
    "repro": "press save",
    "severity": "high",
    "acceptance_criteria": [{"id": "AC-1", "text": "saves"}],
}
TSK_FIELDS = {
    "product_requirement": "PR-0001",
    "root_revision": 1,
    "derives_from": "PR-0001",
    "type": "implementation",
    "assigned_role": "backend-developer",
    "acceptance_refs": ["AC-1"],
    "required_inputs": [],
    "allowed_scope": ["src/**"],
    "forbidden_scope": [],
    "expected_outputs": ["code"],
    "dependencies": [],
}


def _store(tmp_path, name="project_memory"):
    """A real store: a root, a system requirement, a bug, and one task under each of them."""
    from conftest import approve, walk_to_status
    root = tmp_path / name
    root.mkdir()
    state = ProjectState(str(root))
    pr = state.capture("PR", PR_FIELDS)
    approve(state, pr["id"], "scope")
    sr = state.capture("SR", dict(SR_FIELDS, derives_from=pr["id"]))
    state.capture("BUG", dict(BUG_FIELDS, related_pr=pr["id"]))
    under_sr = state.capture("TSK", dict(TSK_FIELDS, product_requirement=pr["id"],
                                         derives_from=sr["id"]))
    walk_to_status(state, under_sr, "READY")
    state.capture("TSK", dict(TSK_FIELDS, product_requirement=pr["id"], derives_from=pr["id"]))
    return state


def _entries(state):
    """(row, body) pairs, the way `state._regenerate_index_locked` hands them to a renderer."""
    import yaml
    rows = yaml.safe_load(open(os.path.join(state.root, "generated", "index.yaml"),
                               encoding="utf-8"))["items"]
    return [(row, state.read_item(row["id"])) for row in rows]


def _synthetic(count):
    """`count` tasks under one root, without a store -- for the size bound only."""
    pr_row = {"id": "PR-0001", "type": "PR", "title": "root", "status": "APPROVED"}
    pr_body = dict(PR_FIELDS, id="PR-0001", status="APPROVED")
    entries = [(pr_row, pr_body)]
    for number in range(1, count + 1):
        item_id = "TSK-%04d" % number
        row = {"id": item_id, "type": "TSK", "title": None, "status": "DRAFT"}
        body = dict(TSK_FIELDS, id=item_id, status="DRAFT", product_requirement="PR-0001",
                    derives_from="PR-0001")
        entries.append((row, body))
    return entries


def _write(tmp_path, entries):
    """Both files on disk, the way the kernel's writer would leave them."""
    written = {}
    for name, text in plan_diagram.render_all(entries):
        path = str(tmp_path / name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        written[name] = path
    return written


def _model(path):
    """The draw.io document inside the SVG root -- the half a picture-only file does not have."""
    root = ET.parse(path).getroot()
    content = root.get("content")
    assert content, "no `content` attribute: draw.io would open this as a flat image"
    return root, ET.fromstring(content)


def _cells(model):
    return model.findall("./diagram/mxGraphModel/root/mxCell")


# ---------------- the property the whole format rests on ----------------

def test_the_diagram_is_a_pure_function_of_the_entries(tmp_path):
    """Two renders of the same entries are the same bytes -- and nothing in the module can read a
    clock or a random source, which is the reason they are.

    BOTH ENDS, because either alone is weak: two equal runs a second apart would also pass with a
    clock that ticks in minutes, and an import check alone says nothing about `id()` or dictionary
    order reaching the output. The syntax tree is read rather than the text of the file, so a
    `datetime` reached through an alias is found too.
    """
    entries = _entries(_store(tmp_path))
    first = plan_diagram.render_all(entries)
    second = plan_diagram.render_all(entries)
    assert first == second, "two renders of one state differ"
    assert [name for name, _text in first] == [plan_diagram.PLAN_FILENAME,
                                               plan_diagram.MINDMAP_FILENAME]
    tree = ast.parse(open(MODULE, encoding="utf-8").read(), filename=MODULE)
    forbidden = {"time", "datetime", "random", "secrets", "uuid"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            assert node.value.id not in forbidden, "%s.%s is a clock" % (node.value.id, node.attr)
    assert not (imported & forbidden), sorted(imported & forbidden)


def test_a_hand_edit_is_told_from_a_stale_file(tmp_path):
    """Three verdicts, each produced the way it really happens.

    A HAND EDIT is made the way draw.io itself rewrites the document when it saves -- through
    ElementTree, not by patching bytes -- because that is the shape the check has to survive: the
    whole file comes back reserialised, so "the bytes differ" is all a comparison can see, and the
    digest on the root is what turns that into "somebody edited it". A STALE file is the same
    bytes against entries whose status has moved. A FOREIGN name is neither.
    """
    entries = _entries(_store(tmp_path))
    written = _write(tmp_path, entries)
    path = written[plan_diagram.PLAN_FILENAME]
    assert plan_diagram.is_pristine(path, entries)[0] == "pristine"

    tree = ET.parse(path)
    for node in tree.getroot().iter("{http://www.w3.org/2000/svg}text"):
        node.text = (node.text or "") + " (edited by hand)"
        break
    tree.write(path, encoding="utf-8", xml_declaration=True)
    verdict, reason = plan_diagram.is_pristine(path, entries)
    assert verdict == "hand-edited", (verdict, reason)

    _write(tmp_path, entries)                       # back to a fresh render
    moved = [(dict(row, status="ACCEPTED") if row["type"] == "PR" else row, body)
             for row, body in entries]
    verdict, reason = plan_diagram.is_pristine(path, moved)
    assert verdict == "stale", (verdict, reason)
    assert plan_diagram.is_pristine(str(tmp_path / "nothing.drawio.svg"), entries)[0] == "foreign"


def test_the_file_is_well_formed_and_carries_a_drawio_model(tmp_path):
    """What the kernel already checks about a `.drawio.svg` (`staging._assert_xml_wellformed`) PLUS
    what makes one a diagram rather than a picture: a `content` attribute holding an `<mxfile>` with
    a model whose every vertex has a geometry. The pilot's own file passes the first and fails the
    second, which is why both are here."""
    entries = _entries(_store(tmp_path))
    for path in _write(tmp_path, entries).values():
        staging._assert_xml_wellformed(path)        # raises StagingError if it is not
        root, model = _model(path)
        assert model.tag == "mxfile", model.tag
        cells = _cells(model)
        assert cells, path
        for cell in cells:
            if cell.get("vertex") == "1":
                assert cell.find("mxGeometry") is not None, cell.get("id")
            else:
                assert cell.get("edge") == "1" or cell.get("id") in ("0", "1"), cell.get("id")
        assert root.get("data-source-digest") == plan_diagram.digest_of(entries)
        assert root.get("data-generator") == plan_diagram.GENERATOR


def test_every_cell_names_an_item_the_entries_hold(tmp_path):
    """Nothing invented and nothing lost: every id a cell shows is an item of the entries, and every
    item the system tree hangs under a root has a cell of its own. The second half is the one that
    rots -- a layout that silently skips what does not fit is exactly the failure the board's own
    nothing-vanishes rule exists against, and here it is bounded instead by `CELL_BUDGET`, which
    SAYS what it left out (`test_a_project_over_the_budget_says_what_it_left_out`)."""
    state = _store(tmp_path)
    entries = _entries(state)
    known = {str(row.get("id") or "") for row, _body in entries}
    view = backlog_tree.VIEWS[-1]
    system = backlog_tree.arrange(view, entries)
    # DERIVED FROM THE ARRANGEMENT AND NOT FROM THE MODULE'S OWN WALKER. The first cut of this test
    # built `expected` with `plan_diagram._outline` -- the very function that decides which items
    # reach a cell -- so a walker that dropped every node below depth 1 shrank the expectation with
    # it and the check stayed green through the defect (measured with the mutation harness of this
    # round). What the view PLACES is `arrange`'s own contract: every item of a type the view shows
    # that did not land in `unassigned`.
    shown_types = set(backlog_tree.view_types(view))
    unplaced = {node.item_id for node in system.unassigned}
    expected = {str(row.get("id") or "") for row, _body in entries
                if str(row.get("type") or "") in shown_types} - unplaced
    assert len(expected) == system.placed, (len(expected), system.placed)
    assert len(expected) > 3, "the fixture hangs nothing under its root"
    for path in _write(tmp_path, entries).values():
        _root, model = _model(path)
        values = " ".join(cell.get("value") or "" for cell in _cells(model))
        found = {item_id for item_id in known if item_id in values}
        assert expected <= found, ("items with no cell: %s" % sorted(expected - found), path)
        import re
        named = set(re.findall(r"\b[A-Z]{2,4}-\d{4,}\b", values))
        assert named <= known, ("cells name ids no item carries: %s" % sorted(named - known),)


def test_status_is_never_carried_by_colour_alone(tmp_path):
    """WCAG 1.4.1, and the research note names it as a gate on this format: every cell whose FILL is
    a lane colour also carries that lane as a WORD. A reader who cannot tell the three fills apart
    still reads the plan."""
    entries = _entries(_store(tmp_path))
    fills = {colour: board.LANE_WORDS[key] for key, colour in plan_diagram.LANE_FILL.items()}
    for path in _write(tmp_path, entries).values():
        _root, model = _model(path)
        coloured = 0
        for cell in _cells(model):
            for colour, word in fills.items():
                if "fillColor=%s;" % colour in (cell.get("style") or ""):
                    coloured += 1
                    assert word in (cell.get("value") or ""), (
                        "a cell says its lane in colour only: %r" % cell.get("value"))
        assert coloured, ("no lane-coloured cell at all in %s" % path)


def test_no_colour_outside_the_named_palette():
    """One palette, named at the top of the module, and nothing else. Read off the syntax tree, so a
    hex literal written at a call site is found wherever it hides -- that is how a diagram grows a
    colour nobody chose and no sheet documents."""
    tree = ast.parse(open(MODULE, encoding="utf-8").read(), filename=MODULE)
    import re
    hexes = {node.value for node in ast.walk(tree)
             if isinstance(node, ast.Constant) and isinstance(node.value, str)
             and re.fullmatch(r"#[0-9a-fA-F]{3,8}", node.value)}
    palette = {plan_diagram.INK, plan_diagram.PAPER, plan_diagram.RULE}
    palette |= set(plan_diagram.LANE_FILL.values())
    assert hexes == palette, ("outside the palette: %s / declared but unused: %s"
                              % (sorted(hexes - palette), sorted(palette - hexes)))


def test_a_project_over_the_budget_says_what_it_left_out(tmp_path):
    """A bound has to exist -- this runs at the end of every state write over the whole active store
    -- and a bound that drops work in silence is the failure the board's own rules are written
    against. So over `CELL_BUDGET` the picture carries the sentence that names what is missing and
    where all of it is, and under the budget that sentence is absent."""
    over = _synthetic(plan_diagram.CELL_BUDGET + 5)
    under = _synthetic(plan_diagram.CELL_BUDGET - 5)
    for entries, expect in ((over, True), (under, False)):
        for _name, text in plan_diagram.render_all(entries):
            said = "of %d items shown" % (len(entries) - 1) in text
            assert said is expect, (expect, len(entries))
    plan = dict(plan_diagram.render_all(over))[plan_diagram.PLAN_FILENAME]
    path = str(tmp_path / plan_diagram.PLAN_FILENAME)
    open(path, "w", encoding="utf-8", newline="\n").write(plan)
    staging._assert_xml_wellformed(path)
    _root, model = _model(path)
    cells = [cell for cell in _cells(model) if (cell.get("value") or "").startswith("TSK-")]
    assert len(cells) == plan_diagram.CELL_BUDGET, len(cells)


def test_the_kernel_cli_still_runs_with_the_new_module_beside_it(tmp_path):
    """A module the package imports has to import cleanly in the process the kernel really runs in
    -- an import cycle or a syntax error here would only show up at the end of the next state
    write, inside a `try` that swallows it."""
    root = tmp_path / "project_memory"
    root.mkdir()
    result = subprocess.run(
        [sys.executable, "-B", "-c",
         "from kernel import plan_diagram; print(len(plan_diagram.render_all([])))"],
        cwd=TEAM_KITS, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "2", result.stdout


@pytest.mark.parametrize("entries", [[], _synthetic(0)])
def test_an_empty_or_rootless_state_still_produces_both_files(entries):
    """The greenfield case: a project that has captured nothing, and one whose only item is a root
    with nothing under it. Both have to render -- this runs inside the state write, so a shape that
    raises here would cost every capture in that project."""
    produced = plan_diagram.render_all(entries)
    assert len(produced) == 2
    for _name, text in produced:
        assert text.startswith("<?xml")
        assert ET.fromstring(text.split("\n", 1)[1]) is not None


# Characters a YAML file can carry and an XML document cannot (XML 1.0 §2.2). None of them is an
# attack: a NUL arrives from a truncated write, a lone surrogate from text that was decoded once too
# often, and both reach an item file the same way every other hostile shape in this suite does --
# by hand or by corruption.
_ILLEGAL_IN_XML = {
    "a NUL byte first": chr(0) + chr(1) + " NUL first",
    "a control character inside a word": "before" + chr(0x0B) + "after",
    "a lone surrogate half": "half " + chr(0xD800) + " here",
}


@pytest.mark.parametrize("shape", sorted(_ILLEGAL_IN_XML))
def test_a_control_character_in_a_title_cannot_break_the_model(tmp_path, shape):
    """`html.escape` answers `&<>"` -- a different question from "may this character be in an XML
    document at all".

    Measured before the fix, on a title beginning with NUL: BOTH files came out unparseable, and
    `is_pristine` still called them pristine -- because pristine means "equal to a fresh render",
    and a fresh render was equally broken. So the file's own verdict cannot catch this class and
    the characters have to be gone before they are written. The escape happens in `_clip`, which
    every label goes through, so this measures the property on both pictures at once.

    THE ITEM'S TEXT IS NOT DROPPED, it is marked: a label that silently closed the gap would tell a
    reader the title is shorter than it is.
    """
    title = _ILLEGAL_IN_XML[shape]
    entries = [
        ({"id": "PR-0001", "type": "PR", "title": title, "status": "APPROVED"},
         dict(PR_FIELDS, id="PR-0001", title=title, status="APPROVED")),
        ({"id": "TSK-0001", "type": "TSK", "title": title, "status": "DRAFT"},
         dict(TSK_FIELDS, id="TSK-0001", title=title, status="DRAFT")),
    ]
    written = _write(tmp_path, entries)
    assert len(written) == 2
    for path in written.values():
        staging._assert_xml_wellformed(path)
        root, model = _model(path)
        assert _cells(model), path
        values = " ".join(cell.get("value") or "" for cell in _cells(model))
        assert "PR-0001" in values and "TSK-0001" in values
        assert plan_diagram._REPLACEMENT in values, (
            "the unreadable character was dropped instead of marked")
        assert plan_diagram.is_pristine(path, entries)[0] == "pristine"


def test_a_state_write_leaves_both_diagrams_beside_the_board(tmp_path, capsys, monkeypatch):
    """The trigger: a project that captures an item gets the pictures, and never pays for them.

    UNTIL TSK-0120 THIS MODULE HAD NO CALLER OUTSIDE THIS FILE -- `render_all` was reachable from
    the tests and from nowhere a running project walks, which is why `is_pristine` could tell a
    hand edit from a stale file and no project ever heard either verdict (`H127`). The seam is one
    loop in `state._write_board`, and this test is its arbiter from BOTH ends:

    * the pictures exist after an ordinary `capture`, are `pristine` against the same entries, and
      move with the state -- a second capture leaves neither `stale`;
    * a renderer that raises does not fail the state write, and does not claim the BOARD was lost.
      That second half is why the loop sits in a `try` of its own: the board's own message names
      the board, and it had already been written when the picture failed.
    """
    state = _store(tmp_path)
    entries = _entries(state)
    written = {name: os.path.join(state.root, "generated", name)
               for name, _ in plan_diagram.render_all(entries)}
    assert len(written) == 2
    for name, path in written.items():
        assert os.path.isfile(path), "%s was not written by the state write" % name
        assert plan_diagram.is_pristine(path, entries)[0] == "pristine", name

    state.capture("BUG", dict(BUG_FIELDS, title="a second bug moves the state"))
    fresh = _entries(state)
    for name, path in written.items():
        assert plan_diagram.is_pristine(path, fresh)[0] == "pristine", (
            "%s did not move with the state" % name)

    def refuse(_entries):
        raise RuntimeError("no picture today")

    monkeypatch.setattr(plan_diagram, "render_all", refuse)
    capsys.readouterr()
    item = state.capture("BUG", dict(BUG_FIELDS, title="the write must still go through"))
    said = capsys.readouterr().err
    assert state.read_item(item["id"])["id"] == item["id"], "the state write did not go through"
    assert "no picture today" in said, said
    assert "[plan]" in said, said
    assert board.FILENAME + " was NOT rebuilt" not in said, (
        "a board that WAS rebuilt is reported as lost by a picture that was not: %s" % said)
