"""The kanban board the kernel writes beside its index (FR-0030, TSK-0071).

EVERY CHECK HERE READS THE PAGE THAT SHIPS, parsed as HTML by `_Board` below, and the page is
produced by a real kernel state write or by the shipped renderer itself. That is deliberate and it
is the reason there is no JSON data block in the artefact: a test that read an embedded payload
would measure something no browser renders, and the failure this whole feature exists against --
a view that quietly stops showing an item -- lives in the DOM, not in a payload beside it.
"""
import ast
import os
import shutil
import subprocess
import sys
import time
import tracemalloc
from html.parser import HTMLParser

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")
sys.path.insert(0, TEAM_KITS)

from conftest import approve, walk_to_status  # noqa: E402 -- the sanctioned walkers
from kernel import board  # noqa: E402
from kernel.backlog_types import ACTIVE_DIRS, AUTOMATA  # noqa: E402
from kernel.state import ProjectState  # noqa: E402


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
RQ_FIELDS = {
    "title": "Does it hold?",
    "class": "normal",
    "question": "does it?",
    "motivation": "because",
    "acceptance_criteria": [{"id": "AC-1", "text": "answered"}],
    "out_of_scope": ["ethics"],
    "priority": "high",
}
PROC_FIELDS = {"title": "File an invoice", "steps": ["scan", "file"], "roles": ["office-manager"]}
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


class _Board(HTMLParser):
    """The rendered page, read the way a browser reads it.

    Sections, columns and cards are recovered from the DOM's own attributes, so a card that never
    made it into the markup is a card this parser does not have -- which is exactly the failure the
    tests below are about. `columns` keeps the ORDER the page puts them in, because a kanban board
    whose columns are in a random order is not one.
    """

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.generated_at = None
        self.columns = {}          # {type: [status, ...]} in page order
        self.cards = {}            # {(type, status): [item id, ...]}
        self.counts = {}           # {(type, status): the count the column CLAIMS}
        self.warnings = []         # [(kind, type, text), ...]
        self.titles = {}           # {item id: the title on the card's face}
        self.folds = {}            # {item id: {field: text}}
        self._type = self._status = self._item = None
        self._sink = None          # where character data goes right now
        self._field = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "time" and "data-generated-at" in attrs:
            self.generated_at = attrs["data-generated-at"]
        elif tag == "section" and "data-type" in attrs:
            self._type = attrs["data-type"]
            self.columns.setdefault(self._type, [])
        elif tag == "div" and "data-status" in attrs:
            self._status = attrs["data-status"]
            self.columns[self._type].append(self._status)
            self.cards.setdefault((self._type, self._status), [])
            self.counts[(self._type, self._status)] = int(attrs["data-count"])
        elif tag == "details" and "data-item" in attrs:
            self._item = attrs["data-item"]
            self.cards[(self._type, self._status)].append(self._item)
            self.folds[self._item] = {}
        elif tag == "li" and "data-warning" in attrs:
            self.warnings.append([attrs["data-warning"], attrs["data-type"], ""])
            self._sink = "warning"
        elif tag == "span" and dict(attrs).get("class") == "title":
            self._sink = "title"
        elif tag in ("dt", "dd") and self._item:
            self._sink = tag

    def handle_endtag(self, tag):
        if tag == "section":
            self._type = None
        elif tag == "details":
            self._item = None
        elif tag in ("li", "span", "dt", "dd"):
            self._sink = None

    def handle_data(self, data):
        if self._sink == "warning":
            self.warnings[-1][2] += data
        elif self._sink == "title" and self._item:
            self.titles[self._item] = self.titles.get(self._item, "") + data
        elif self._sink == "dt":
            self._field = data
        elif self._sink == "dd" and self._field is not None:
            self.folds[self._item][self._field] = self.folds[self._item].get(self._field, "") + data

    def where(self, item_id):
        """(type, status) of the one card carrying this id -- KeyError if the page dropped it."""
        found = [key for key, ids in self.cards.items() if item_id in ids]
        assert len(found) == 1, "%s appears %d time(s) on the board" % (item_id, len(found))
        return found[0]


def _read_board(state):
    return _Board(open(os.path.join(state.root, "generated", board.FILENAME),
                       encoding="utf-8").read())


def _state(tmp_path, name="project_memory"):
    root = tmp_path / name
    root.mkdir()
    return ProjectState(str(root))


# ---------------- (a) the view cannot go stale: it is written where the index is ----------------

def test_every_state_write_leaves_a_board_as_fresh_as_the_index(tmp_path):
    """The finding FR-0030 records, flipped: the pilot project never generated its dashboard because
    nothing triggered it. The board has no trigger of its own -- it is written inside
    `state._regenerate_index_locked`, so every writer that touches the index refreshes it.

    Capture, the approval mint, transition and archive are driven here rather than one of them,
    because "every writer" is the claim; the ones not driven reach the same method.
    `walk_to_status` is the sanctioned walker -- a gated edge is walked by MINTING its approval, so
    this measures the board on the route a real session takes.
    """
    state = _state(tmp_path)
    pr = state.capture("PR", PR_FIELDS)
    page = _read_board(state)
    assert page.where(pr["id"]) == ("PR", "DRAFT")

    approve(state, pr["id"], "scope")                       # the mint writes state too
    assert _read_board(state).where(pr["id"]) == ("PR", "APPROVED")

    walk_to_status(state, pr, "IN_DELIVERY")
    assert _read_board(state).where(pr["id"]) == ("PR", "IN_DELIVERY")

    state.transition(pr["id"], "REJECTED")                  # a plain, ungated edge
    state.archive(pr["id"])
    page = _read_board(state)
    assert not any(pr["id"] in ids for ids in page.cards.values()), (
        "an archived item is still on the board")

    # ...and the page is never OLDER than the index: one clock reading feeds both files
    index = yaml.safe_load(open(os.path.join(state.root, "generated", "index.yaml"),
                                encoding="utf-8"))
    assert page.generated_at == index["generated_at"]


def test_the_documented_command_writes_and_names_both_artefacts(tmp_path):
    """`generate-index` is what a role is told to run, so it is what must produce the board -- and
    it must SAY it did, or the one artefact a person opens is the one the command never mentions."""
    state = _state(tmp_path)
    state.capture("PR", PR_FIELDS)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "kernel.cli", "--root", state.root, "generate-index"],
        cwd=TEAM_KITS, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    printed = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert len(printed) == 2, printed
    assert all(os.path.isfile(path) for path in printed), printed
    assert os.path.basename(printed[1]) == board.FILENAME


# ---------------- the columns are the type's own chain ----------------

def test_the_columns_of_a_type_are_its_own_automaton_in_chain_order(tmp_path):
    """Kanban columns are DERIVED: the chain in chain order, then the side states, then the
    terminals. Read off the automaton here, not off `board.status_columns`, so the two ends are
    independent -- a chain change has to move the page, not just the helper."""
    state = _state(tmp_path)
    state.capture("PR", PR_FIELDS)
    state.capture("TSK", TSK_FIELDS)
    page = _read_board(state)
    for item_type in ("PR", "TSK"):
        automaton = AUTOMATA[item_type]
        shown = page.columns[item_type]
        assert set(shown) == set(automaton.states), (item_type, shown)
        assert shown[:len(automaton.chain)] == list(automaton.chain), (item_type, shown)
        assert set(shown[len(automaton.chain):]) == (
            automaton.states - set(automaton.chain)), (item_type, shown)


def test_every_field_of_an_item_is_on_its_card_exactly_once(tmp_path):
    """Nothing an item records may be missing from its card, and nothing may be on it twice.

    THE EXPECTATION COMES FROM THE PAGE, NOT FROM `FACE_FIELDS`. The first cut of this test read
    `set(item) - set(board.FACE_FIELDS)`, i.e. it compared the constant with itself: the verifier
    changed `FACE_FIELDS` to `("id", "title", "status", "priority")` and watched `priority` vanish
    from the card entirely — the face renders only id and title — with the suite still green. That
    is exactly the disappearance FR-0030 exists against.

    So the three RENDERED PLACES are looked up in the parsed page and each one only counts when it
    actually shows the item's value: the card's own id, the title on the face, the column the card
    sits in. Whatever they carry may not be in the fold, and everything else must be. Both
    mutations then go red — a widened `FACE_FIELDS` drops a field from the card, a narrowed one
    prints it twice.
    """
    state = _state(tmp_path)
    item = state.capture("PR", PR_FIELDS)
    page = _read_board(state)
    _type, column = page.where(item["id"])
    shown_elsewhere = {name for name, rendered in (("id", item["id"]),
                                                   ("title", page.titles.get(item["id"], "")),
                                                   ("status", column))
                       if name in item and rendered == str(item[name])}
    assert shown_elsewhere == {"id", "title", "status"}, (
        "a field the card is supposed to show on its face is not there: %s" % (shown_elsewhere,))
    assert set(page.folds[item["id"]]) == set(item) - shown_elsewhere
    # a nested value reads as text, not as a Python repr somebody has to decode
    assert page.folds[item["id"]]["acceptance_criteria"] == "id: AC-1; text: order completes"


def test_a_title_that_closes_the_card_element_does_not_break_the_page(tmp_path):
    """A hand-written item is not the only source of a hostile title, and `</details>` in one would
    end the card as far as any parser is concerned. The proof is that the PARSER still finds the
    card and reads the title back whole."""
    state = _state(tmp_path)
    fields = dict(PR_FIELDS, title="fix </details><script>alert(1)</script> leak")
    item = state.capture("PR", fields)
    page = _read_board(state)
    assert page.where(item["id"]) == ("PR", "DRAFT")
    assert page.titles[item["id"]] == fields["title"]


# ---------------- (b) every kit renders its own types ----------------

def _kit_state(tmp_path, kit):
    """A state directory as that kit's scaffold installs it -- its own template tree, verbatim."""
    root = tmp_path / kit / "project_memory"
    shutil.copytree(os.path.join(TEAM_KITS, kit, "templates", "project_memory"), str(root))
    return ProjectState(str(root))


@pytest.mark.parametrize("kit,captures,expected_absent", [
    ("dev-team", [("PR", PR_FIELDS)], ("RQ", "HYP", "EXP", "PROC")),
    ("research-team", [("RQ", RQ_FIELDS)], ("PR", "PROC", "ARC")),
    ("office-team", [("PROC", PROC_FIELDS)], ("PR", "RQ", "HYP", "EXP", "ARC")),
])
def test_each_kit_renders_the_types_its_own_template_ships(tmp_path, kit, captures,
                                                           expected_absent):
    """FR-0030/3: all three kits, with KIT-APPROPRIATE types. Which types those are is read off the
    state tree the kit ships -- there is no per-kit type table to disagree with it -- so the
    expectation here is derived from that same tree, and the hard-named absences are the
    counter-direction: a board that simply showed every type the kernel knows would fail them."""
    state = _kit_state(tmp_path, kit)
    for item_type, fields in captures:
        state.capture(item_type, fields)
    page = _read_board(state)
    shipped = {item_type for item_type, directory in ACTIVE_DIRS.items()
               if os.path.isdir(os.path.join(state.root, *directory.split("/")))}
    assert set(page.columns) == shipped, (kit, sorted(page.columns), sorted(shipped))
    for absent in expected_absent:
        assert absent not in page.columns, "%s renders %s, which it does not ship" % (kit, absent)
    for item_type, _fields in captures:
        assert page.cards[(item_type, AUTOMATA[item_type].initial)]


# ---------------- (c) nothing a type does not describe is ever dropped ----------------

def test_an_item_type_no_status_vocabulary_describes_still_appears_with_a_warning(tmp_path):
    """The "Other" path of the shipped dashboard, one layer down. This board assigns no type to a
    hand-kept view, so what is left to be unknown about a type is its STATUS VOCABULARY: a type the
    kernel gains without an automaton has no column of its own. Its items get one anyway, and the
    page says so -- a whole item type quietly missing from the only overview a user opens is the
    failure worth designing against."""
    state = _state(tmp_path)
    row = {"id": "ZZZ-0001", "type": "ZZZ", "title": "from a type nobody wired", "status": "WEIRD"}
    page = _Board(board.render(state, [(row, dict(row))], "2026-08-16T12:00:00"))
    assert page.where("ZZZ-0001") == ("ZZZ", "WEIRD")
    assert [(kind, item_type) for kind, item_type, _text in page.warnings] == [
        ("unknown-status", "ZZZ")]


def test_a_status_off_its_types_vocabulary_still_appears_and_warns(tmp_path):
    """The same property through the shipped write path, in the shape that really produces it: a
    hand-edited item file. The kernel refuses such a status on its own transitions, so the item
    only ever reaches the store by hand -- and that is precisely when a board must not hide it."""
    state = _state(tmp_path)
    os.makedirs(os.path.join(state.root, *ACTIVE_DIRS["BUG"].split("/")))
    open(os.path.join(state.root, *ACTIVE_DIRS["BUG"].split("/"), "BUG-0001.yaml"),
         "w", encoding="utf-8").write("id: BUG-0001\ntitle: crash\nstatus: WAT\n")
    state.generate_index()
    page = _read_board(state)
    assert page.where("BUG-0001") == ("BUG", "WAT")
    assert ("unknown-status", "BUG") in [(kind, item_type) for kind, item_type, _t in page.warnings]


def test_a_record_type_without_a_status_is_not_reported_as_a_defect(tmp_path):
    """The counter-direction, and the reason the warning above is not simply "no column matched":
    Evidence, approvals and the frozen design types carry NO status by contract. Their cards belong
    in a column of their own, and calling that a defect would make the banner meaningless noise on
    every project that has ever recorded a test run."""
    state = _state(tmp_path)
    pr = state.capture("PR", PR_FIELDS)
    evidence = state.capture("EVD", {"kind": "test", "related": [pr["id"]], "result": "pass",
                                     "summary": "suite green",
                                     "artifact_refs": ["staging/TSK-0001/log.txt"]})
    page = _read_board(state)
    assert page.where(evidence["id"]) == ("EVD", board.NO_STATUS)
    assert not page.warnings, page.warnings


def test_an_item_file_that_cannot_be_read_is_shown_rather_than_dropped(tmp_path):
    """A corrupt item is the one an overview must show most loudly: the index already reports it as
    `corrupt`, and a board that skipped those rows would be reassuring about a state nobody can
    read."""
    state = _state(tmp_path)
    os.makedirs(os.path.join(state.root, *ACTIVE_DIRS["SR"].split("/")))
    open(os.path.join(state.root, *ACTIVE_DIRS["SR"].split("/"), "SR-0001.yaml"),
         "w", encoding="utf-8").write("- this is a list, not an item\n")
    state.generate_index()
    page = _read_board(state)
    assert page.where("SR-0001") == ("SR", board.UNREADABLE)
    assert ("unreadable", "SR") in [(kind, item_type) for kind, item_type, _t in page.warnings]


def test_a_self_referential_item_body_does_not_stop_the_state_write(tmp_path):
    """The regression this renderer can cause and the index never could. A YAML anchor pointing at
    its own container is a legal file `yaml.safe_load` resolves into a self-referential object; the
    board is rendered at the END of every state write, so an unbounded walk over it would not merely
    spoil one page -- it would raise out of `_regenerate_index_locked` and make every later capture
    in that project fail. The item still has to reach the board, so the bound may not simply drop it.
    """
    state = _state(tmp_path)
    os.makedirs(os.path.join(state.root, *ACTIVE_DIRS["BUG"].split("/")))
    open(os.path.join(state.root, *ACTIVE_DIRS["BUG"].split("/"), "BUG-0001.yaml"),
         "w", encoding="utf-8").write("id: BUG-0001\ntitle: loops\nstatus: OPEN\n"
                                      "repro: &loop\n  - step\n  - *loop\n")
    state.generate_index()                       # the write itself must survive it
    state.capture("PR", PR_FIELDS)               # ...and so must the next one
    page = _read_board(state)
    assert page.where("BUG-0001") == ("BUG", "OPEN")
    assert page.folds["BUG-0001"]["repro"].startswith("step")


# ---------------- the freshness claim, on the writers that did NOT regenerate ----------------

def _kernel_calls():
    """{(module, function): {called attribute names}} for every function in the kernel package.

    Parsed, not imported: the question is which calls a function CONTAINS, and that is a property
    of the source. Nested functions are attributed to the enclosing one, which is what the rule
    below needs -- a writer that regenerates from inside a closure still regenerates.
    """
    found = {}
    kernel_dir = os.path.join(TEAM_KITS, "kernel")
    for name in sorted(os.listdir(kernel_dir)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(kernel_dir, name), encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=name)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            calls = found.setdefault((name, node.name), set())
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call):
                    target = inner.func
                    calls.add(target.attr if isinstance(target, ast.Attribute)
                              else getattr(target, "id", ""))
    return found


# Kernel functions that write a file WITHOUT regenerating the index, each with the reason the board
# does not have to care. Every entry is a claim about WHAT that function writes, and both ends are
# measured by the test below: an entry whose function no longer writes at all is dead, and a writer
# that is neither here nor regenerating is the B2 defect coming back.
_WRITERS_THE_BOARD_DOES_NOT_RENDER = {
    ("state.py", "_write_yaml_atomic"): "IS the writer (delegates to _write_text_atomic)",
    ("state.py", "_regenerate_index_locked"): "IS the regeneration",
    ("state.py", "_write_board"): "writes the board itself",
    ("approvals.py", "create_pending_request"): "approvals/pending/ -- not listed by "
                                                "iter_active_items and not in the index",
    ("checkpoints.py", "record"): "tasks/checkpoints/ -- no ACTIVE_DIRS home, so no card",
    ("dispatch.py", "mark_awaiting_bind"): "the lease file, which is not an item",
    ("dispatch.py", "clear_awaiting_bind"): "the lease file",
    ("dispatch.py", "bind_agent_by_role"): "the lease file",
    ("dispatch.py", "bind_agent"): "the lease file",
    ("dispatch.py", "validate_dispatch"): "the lease file (the claim)",
    ("dispatch.py", "_release_lease_locked"): "resets the TASK, but every caller regenerates -- "
                                              "checked below, because one of them did not",
    ("staging.py", "freeze_design"): "its DSN manifest, then `_update_item_locked` on the root, "
                                     "which regenerates",
    ("report.py", "generate_session_brief"): "generated/session_brief.yaml",
    ("presets.py", "record_preset"): "project_config.yaml -- a kit document, no card",
    ("filing.py", "apply"): "filing_plan.yaml -- a kit document, no card (and nothing it writes "
                            "is an item: the plan says where documents belong, the board shows "
                            "what the project is working on)",
    ("presets.py", "_after_a_failed_install"): "a .claude marker file",
    ("kitupdate.py", "_ensure_restart_is_forced"): "a .claude marker file",
}


def test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind():
    """The board can only be as fresh as the index, so every kernel write has to regenerate it.

    Two did not, and the verifier found them by hand: `approvals.revoke` (the APR card kept saying
    `revoked = False` -- a field the index does not even carry, so only the board could show it)
    and the lease-expiry release in `dispatch._validate_lease_locked` (task READY on disk, LEASED
    on the index and the board). Both are fixed; this is what keeps the pair from coming back, and
    it derives the writers from the package instead of trusting a sentence in a docstring.
    """
    calls = _kernel_calls()
    writers = {key for key, made in calls.items()
               if {"_write_yaml_atomic", "_write_text_atomic"} & made}
    offenders = sorted(key for key in writers
                       if "_regenerate_index_locked" not in calls[key]
                       and key not in _WRITERS_THE_BOARD_DOES_NOT_RENDER)
    assert not offenders, (
        "these kernel functions write a file and regenerate neither index nor board; if what they "
        "write is not rendered, say so in _WRITERS_THE_BOARD_DOES_NOT_RENDER: %s" % offenders)
    # the other end: an exemption for a function that no longer writes anything is a dead claim
    dead = sorted(key for key in _WRITERS_THE_BOARD_DOES_NOT_RENDER if key not in writers)
    assert not dead, "exempted, but no longer a writer: %s" % dead
    # ...and the one exemption that is an argument about its CALLERS is checked on them
    for key, made in calls.items():
        if "_release_lease_locked" in made and key != ("dispatch.py", "_release_lease_locked"):
            assert "_regenerate_index_locked" in made, (
                "%s releases a lease (which resets the task) without regenerating -- the board "
                "and the index then keep the task LEASED" % (key,))


def test_a_revoked_approval_shows_as_revoked_on_the_board(tmp_path):
    """`revoked` lives on the APR item and in NO index row, so the board is the only place it can
    be read at all -- and before the fix it was the one place that still said `False` after the
    file said `True`."""
    state = _state(tmp_path)
    pr = state.capture("PR", PR_FIELDS)
    apr = approve(state, pr["id"], "scope")
    assert _read_board(state).folds[apr["id"]]["revoked"] == "False"
    sys.path.insert(0, TEAM_KITS)
    from kernel import approvals
    approvals.revoke(state, apr["id"])
    assert _read_board(state).folds[apr["id"]]["revoked"] == "True"


def test_an_expired_lease_puts_the_task_back_on_the_board_as_ready(tmp_path):
    """The other half: an expired lease returns the task to READY on disk. Of the four release
    sites this one -- the gate's own validation path -- regenerated nothing, so the board (and the
    index under it) went on showing a task as LEASED that nobody held."""
    sys.path.insert(0, TEAM_KITS)
    from kernel import dispatch
    state = _state(tmp_path)
    pr = state.capture("PR", PR_FIELDS)
    approve(state, pr["id"], "scope")
    task = state.capture("TSK", dict(TSK_FIELDS, product_requirement=pr["id"],
                                     derives_from=pr["id"]))
    state.transition(task["id"], "READY")
    lease = dispatch.create_lease(state, task["id"], ttl=-1)     # already expired
    assert _read_board(state).where(task["id"]) == ("TSK", "LEASED")
    with pytest.raises(dispatch.DispatchError):
        dispatch.validate_lease(state, {"task_id": task["id"], "lease": lease["nonce"],
                                        "root_revision": lease["root_revision"]})
    assert state.read_item(task["id"])["status"] == "READY"
    assert _read_board(state).where(task["id"]) == ("TSK", "READY")


# ---------------- the board may never fail the state write it is written by ----------------

def test_a_surrogate_in_an_item_does_not_stop_the_state_write(tmp_path):
    """A lone surrogate is legal YAML and UTF-8 cannot encode it. The state write has already
    happened by the time the page is written, so a raised UnicodeEncodeError there would report a
    successful capture as failed -- and, because the renderer reads ALL items, it would do so for
    every later capture in that project, with the hand edit the gates refuse as the only apparent
    remedy."""
    state = _state(tmp_path)
    os.makedirs(os.path.join(state.root, *ACTIVE_DIRS["BUG"].split("/")))
    open(os.path.join(state.root, *ACTIVE_DIRS["BUG"].split("/"), "BUG-0001.yaml"),
         "w", encoding="utf-8").write('id: BUG-0001\ntitle: lone half\nstatus: OPEN\n'
                                      'observed: "\\uD800"\n')
    state.generate_index()
    item = state.capture("PR", PR_FIELDS)          # the NEXT write must go through as well
    page = _read_board(state)
    assert page.where("BUG-0001") == ("BUG", "OPEN")
    assert page.where(item["id"]) == ("PR", "DRAFT")


def test_an_alias_bomb_cannot_stretch_a_state_write(tmp_path):
    """A small item file whose YAML aliases multiply into tens of millions of values.

    `yaml.safe_load` resolves aliases into SHARED objects, so a kilobyte can describe a structure
    whose flattening is enormous -- while the index beside it stays a few hundred bytes, because it
    never looks inside a field. The first cut of this round met that twice over: it handed the
    container at the depth bound to `str()` (which unfolds the entire graph below it, the shape the
    verifier measured at 14.87 s per state write) and it cut the text only AFTER building it.

    TWO BOMBS, BECAUSE THE TWO BOUNDS FAIL DIFFERENTLY, and one of them shipped untested for a
    round because a single shape cannot show both:
      * `deep` grows OUTWARD -- every level doubles the one below it, so its LARGEST container is
        the one the walk meets exactly AT the depth bound. `str()` there unfolds that whole graph
        in ONE call, which no character budget can interrupt. (The earlier shape had the mass the
        other way round: the SMALLEST container sat at the bound, worth 14 characters under
        `str()`, so restoring that defect left every assertion green.)
      * `wide` keeps its mass BELOW the bound, where the marker never applies and only the walk's
        own budget can stop the multiplication.
    Each mutation is caught by exactly one of them, and both are measured by the same assertions.

    WHAT IS ASSERTED AND WHY IT IS NOT A STOPWATCH. Wall-clock separates the versions only at sizes
    whose intermediate string costs hundreds of megabytes, so the load-bearing measure is what the
    work actually consumes: the memory the render allocates (`tracemalloc`, which sees the
    intermediate the file never gets), plus the bytes the item may add to the page and the fact
    that the deep container was MARKED. That last one is only evidence because `NESTED_MARKER` is
    not the ellipsis a budget cut appends -- while it was, this assertion held for the wrong reason.
    """
    levels, width = 24, 150
    state = _state(tmp_path)
    state.generate_index()
    board_path = os.path.join(state.root, "generated", board.FILENAME)
    empty = os.path.getsize(board_path)             # the page around the cards, measured not guessed

    # `l1` is two leaves; every level after it is two references to the level below, so `l24`
    # stands for 2**23 leaves in ~500 bytes of file.
    deep = ["  - &l1 [xxxxxxxxxx, xxxxxxxxxx]"]
    deep += ["  - &l%d [*l%d, *l%d]" % (n, n - 1, n - 1) for n in range(2, levels + 1)]
    deep.append("  - [*l%d]" % levels)
    # ...and three levels of `width` copies, whose mass sits above the depth bound
    wide = ["  - &w1 [%s]" % ", ".join(["xxxxxxxxxx"] * width)]
    wide += ["  - &w%d [%s]" % (n, ", ".join(["*w%d" % (n - 1)] * width)) for n in (2, 3)]
    wide.append("  - [%s]" % ", ".join(["*w3"] * width))
    lines = len(deep) + len(wide)                   # one card line per top-level element
    os.makedirs(os.path.join(state.root, *ACTIVE_DIRS["BUG"].split("/")))
    path = os.path.join(state.root, *ACTIVE_DIRS["BUG"].split("/"), "BUG-0001.yaml")
    open(path, "w", encoding="utf-8").write(
        "id: BUG-0001\ntitle: bomb\nstatus: OPEN\nrepro:\n%s\nobserved:\n%s\n"
        % ("\n".join(deep), "\n".join(wide)))

    tracemalloc.start()
    started = time.time()
    state.generate_index()
    took = time.time() - started
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    grew = os.path.getsize(board_path) - empty
    item_bytes = os.path.getsize(path)
    assert peak < 8 * 1024 * 1024, (
        "rendering a %d-byte item allocated %.1f MB" % (item_bytes, peak / 1024.0 / 1024))
    # the page bound is the BUDGET, read off `board`: one line per top-level element, each within
    # VALUE_MAX_CHARS, plus room for the markup around a card
    assert grew < lines * (board.VALUE_MAX_CHARS + 128) + 2048, (
        "the item added %d bytes to the board (item file: %d bytes)" % (grew, item_bytes))
    assert took < 30, "one item stretched a state write to %.1f s" % took
    page = _read_board(state)
    assert page.where("BUG-0001") == ("BUG", "OPEN")
    assert board.NESTED_MARKER in page.folds["BUG-0001"]["repro"], (
        "the container at the depth bound was unfolded instead of marked")


def test_a_board_that_cannot_be_written_does_not_fail_the_state_write(tmp_path, capsys):
    """The write itself can fail for reasons no renderer controls: on Windows an ordinary read
    handle on `board.html` makes `os.replace` refuse (measured on this host), and a directory in
    the file's place does it on every platform. The state write must still go through, and the
    failure must be SAID -- a silent one would be a stale page nobody doubts."""
    state = _state(tmp_path)
    state.capture("PR", PR_FIELDS)
    board_path = os.path.join(state.root, "generated", board.FILENAME)
    before = open(board_path, encoding="utf-8").read()
    os.remove(board_path)
    os.mkdir(board_path)                            # nothing can replace this with a file
    item = state.capture("BUG", BUG_FIELDS)         # must NOT raise
    assert state.read_item(item["id"])["id"] == item["id"]
    index = yaml.safe_load(open(os.path.join(state.root, "generated", "index.yaml"),
                                encoding="utf-8"))
    assert item["id"] in [row["id"] for row in index["items"]], "the index write was skipped too"
    said = capsys.readouterr().err
    assert board.FILENAME in said and "NOT rebuilt" in said, said
    os.rmdir(board_path)
    open(board_path, "w", encoding="utf-8").write(before)


def test_an_item_no_renderer_can_read_costs_its_own_card_and_nothing_else(tmp_path):
    """The per-card guard, driven with a body no YAML file produces -- deliberately, because the
    guard exists for the CLASS (the body's shape is the file's decision, not this module's) and
    not for one shape somebody thought of. The neighbouring card must survive it, and the page has
    to NAME the id rather than quietly drop a row."""
    state = _state(tmp_path)
    good = ({"id": "PR-0002", "type": "PR", "title": "fine", "status": "DRAFT"},
            {"id": "PR-0002", "title": "fine", "status": "DRAFT"})
    broken = ({"id": "PR-0001", "type": "PR", "title": "bad body", "status": "DRAFT"},
              ["not a mapping at all"])
    page = _Board(board.render(state, [broken, good], "2026-08-16T12:00:00"))
    assert page.where("PR-0002") == ("PR", "DRAFT")
    assert page.where("PR-0001") == ("PR", "DRAFT")
    assert page.titles["PR-0002"] == "fine"
    assert [(kind, item_type) for kind, item_type, _t in page.warnings] == [("unrenderable", "PR")]
    assert "PR-0001" in page.warnings[0][2]


def test_every_column_counts_the_cards_it_actually_carries(tmp_path):
    """The number beside a column head is a claim about the cards under it. An unchecked counter is
    where a number quietly stops being true -- and this one is what a reader trusts when a column is
    long enough to scroll."""
    state = _state(tmp_path)
    for _ in range(3):
        state.capture("PR", PR_FIELDS)
    page = _read_board(state)
    for key, count in page.counts.items():
        assert count == len(page.cards[key]), key
    assert page.counts[("PR", "DRAFT")] == 3
