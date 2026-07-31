"""Tests for the state-kernel core operations (HARNESS_V2_SPEC.md II.4, step 1.4a)."""
import os
import sys
import threading

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits"))

from conftest import walk_to_status  # noqa: E402 -- the ONE sanctioned way to walk a chain
from kernel.backlog_types import PARENT_FIELDS, REQUIRED_FIELDS, TransitionError  # noqa: E402
from kernel.state import _CLOSED_VOCABULARY, ProjectState, StateError  # noqa: E402


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


@pytest.fixture
def state(tmp_path):
    # the kernel is fail-closed on a missing state dir (spec II.4: empty state
    # blocks; only the installer bootstrap creates it) -- simulate an
    # initialized project here
    root = tmp_path / "project_memory"
    root.mkdir()
    return ProjectState(str(root))


def make_pr(state, **overrides):
    fields = dict(PR_FIELDS)
    fields.update(overrides)
    return state.capture("PR", fields)


# -- capture -------------------------------------------------------------------

def test_capture_assigns_kernel_fields(state):
    item = make_pr(state)
    assert item["id"] == "PR-0001"
    assert item["status"] == "DRAFT"
    assert item["revision"] == 1
    assert item["approval_ref"] is None
    assert item["created"]
    on_disk = yaml.safe_load(open(state.active_path("PR-0001"), encoding="utf-8"))
    assert on_disk == item


def test_capture_sequential_ids(state):
    assert make_pr(state)["id"] == "PR-0001"
    assert make_pr(state)["id"] == "PR-0002"


def test_capture_rejects_missing_required_field(state):
    fields = dict(PR_FIELDS)
    del fields["out_of_scope"]
    with pytest.raises(StateError, match="out_of_scope"):
        state.capture("PR", fields)


def test_capture_rejects_kernel_set_fields(state):
    with pytest.raises(StateError, match="kernel-set"):
        make_pr(state, status="ACCEPTED")


def test_capture_rejects_unknown_type(state):
    with pytest.raises(StateError, match="unknown|does not handle"):
        state.capture("ARC", {"title": "x"})


def test_id_allocation_includes_archive(state):
    """Max-scan spans active AND archive -- archived ids are never reused."""
    item = make_pr(state)
    walk_to_status(state, item, "ACCEPTED")
    state.archive(item["id"])
    assert make_pr(state)["id"] == "PR-0002"


# -- transition ----------------------------------------------------------------

def test_transition_chain_and_illegal_jump(state):
    item = make_pr(state)
    walk_to_status(state, item, "APPROVED")
    with pytest.raises(TransitionError):
        state.transition(item["id"], "ACCEPTED")  # only from DELIVERED


def test_tsk_failed_ready_requires_approved_retry(state):
    # the origin has to EXIST: `derives_from` is a gate input (the dispatch gate
    # resolves acceptance_refs against it), so the kernel refuses a phantom id
    pr = state.capture("PR", {
        "title": "Root", "class": "normal", "problem": "p", "goal": "g",
        "acceptance_criteria": [{"id": "AC-1", "text": "works"}], "invariants": [],
        "out_of_scope": [], "priority": "high",
    })
    task = state.capture("TSK", {
        "product_requirement": pr["id"],
        "root_revision": 1,
        "derives_from": pr["id"],
        "type": "implementation",
        "assigned_role": "backend-developer",
        "acceptance_refs": ["AC-1"],
        "required_inputs": [],
        "allowed_scope": ["src/"],
        "forbidden_scope": ["secrets/"],
        "expected_outputs": ["src/x.py"],
        "dependencies": [],
    })
    for step in ("READY", "LEASED", "IN_PROGRESS", "FAILED"):
        state.transition(task["id"], step)
    with pytest.raises(TransitionError, match="approved retry"):
        state.transition(task["id"], "READY")
    state.transition(task["id"], "READY", approved_retry=True)


# -- update + approval invalidation --------------------------------------------

def test_hashed_edit_invalidates_approval(state):
    item = make_pr(state)
    # simulate an approval (approve() lands in step 1.4b -- set via kernel file io)
    with state.lock:
        raw = state.read_item(item["id"])
        raw["approval_ref"] = "APR-0001"
        raw["status"] = "APPROVED"
        state._write_yaml_atomic(state.active_path(item["id"]), raw)
    updated = state.update_item(item["id"], {"goal": "DIFFERENT goal"})
    assert updated["revision"] == 2
    assert updated["approval_ref"] is None
    assert updated["status"] == "DRAFT"  # invalidation target for PR


def test_unhashed_edit_keeps_approval(state):
    item = make_pr(state)
    with state.lock:
        raw = state.read_item(item["id"])
        raw["approval_ref"] = "APR-0001"
        raw["status"] = "APPROVED"
        state._write_yaml_atomic(state.active_path(item["id"]), raw)
    updated = state.update_item(item["id"], {"priority": "low"})
    assert updated["revision"] == 1
    assert updated["approval_ref"] == "APR-0001"
    assert updated["status"] == "APPROVED"


def test_hashed_edit_without_approval_keeps_revision(state):
    item = make_pr(state)
    updated = state.update_item(item["id"], {"goal": "new goal"})
    assert updated["revision"] == 1
    assert updated["status"] == "DRAFT"


def test_update_rejects_status_and_id_changes(state):
    item = make_pr(state)
    with pytest.raises(StateError, match="dedicated command"):
        state.update_item(item["id"], {"status": "ACCEPTED"})


def test_dec_capture_starts_valid(state):
    dec = state.capture("DEC", {
        "title": "use SubagentStart binding",
        "context": "S3 spike",
        "decision": "bind lease at SubagentStart",
        "consequences": "no PostToolUse dependency",
        "source": "phase0-disposition",
    })
    assert dec["status"] == "VALID"


def test_inv_capture_starts_unverified(state):
    inv = state.capture("INV", {
        "scope": "frontend",
        "source": "PR-0001",
        "check": {"kind": "test", "ref": "frontend/tests/order.spec"},
        "value": ["CPU", "GPU", "RAM", "STORAGE"],
    })
    assert inv["status"] == "unverified"


def test_update_rejects_created(state):
    item = make_pr(state)
    with pytest.raises(StateError, match="dedicated command"):
        state.update_item(item["id"], {"created": "1999-01-01T00:00:00"})


def test_hashed_key_with_unchanged_value_keeps_approval(state):
    item = make_pr(state)
    with state.lock:
        raw = state.read_item(item["id"])
        raw["approval_ref"] = "APR-0001"
        raw["status"] = "APPROVED"
        state._write_yaml_atomic(state.active_path(item["id"]), raw)
    updated = state.update_item(item["id"], {"goal": PR_FIELDS["goal"]})  # same value
    assert updated["approval_ref"] == "APR-0001"
    assert updated["revision"] == 1


# -- archive -------------------------------------------------------------------

def test_archive_refuses_non_terminal(state):
    item = make_pr(state)
    with pytest.raises(StateError, match="terminal"):
        state.archive(item["id"])


def test_archive_moves_terminal_item_deterministically(state):
    item = make_pr(state)
    state.transition(item["id"], "REJECTED")
    target = state.archive(item["id"])
    assert not os.path.exists(state.active_path(item["id"]))
    assert os.path.exists(target)
    year = yaml.safe_load(open(target, encoding="utf-8"))["closed_at"][:4]
    assert os.sep + os.path.join("archive", "PR", year, "PR-0001.yaml") in target


def test_archive_non_automaton_item_without_terminal_check(state):
    dec = state.capture("DEC", {
        "title": "t", "context": "c", "decision": "d",
        "consequences": "q", "source": "s",
    })
    target = state.archive(dec["id"])
    assert os.path.exists(target)
    assert not os.path.exists(state.active_path(dec["id"]))


# -- generated index -----------------------------------------------------------

def test_index_marks_corrupt_items_visibly(state):
    make_pr(state)
    broken = os.path.join(state.active_dir("PR"), "PR-0999.yaml")
    with open(broken, "w", encoding="utf-8") as fh:
        fh.write(":: definitely not yaml ::\n\t[")
    state.generate_index()
    index = yaml.safe_load(open(os.path.join(state.root, "generated", "index.yaml"), encoding="utf-8"))
    corrupt_rows = [row for row in index["items"] if row.get("corrupt")]
    assert corrupt_rows and corrupt_rows[0]["id"] == "PR-0999"


def test_index_regenerated_by_every_operation(state):
    item = make_pr(state)
    index_path = os.path.join(state.root, "generated", "index.yaml")
    index = yaml.safe_load(open(index_path, encoding="utf-8"))
    assert [row["id"] for row in index["items"]] == [item["id"]]
    walk_to_status(state, item, "APPROVED")
    index = yaml.safe_load(open(index_path, encoding="utf-8"))
    # ROWS ARE SELECTED BY ID, not by position: walking to APPROVED mints an approval, and an APR
    # is an item type of its own (`ACTIVE_DIRS`), so it takes row 0 in the sorted index.
    rows = {row["id"]: row for row in index["items"]}
    assert rows[item["id"]]["status"] == "APPROVED"
    state.transition(item["id"], "SUPERSEDED")
    state.archive(item["id"])
    index = yaml.safe_load(open(index_path, encoding="utf-8"))
    assert item["id"] not in {row["id"] for row in index["items"]}  # archived items leave active


def test_read_item_names_remedy_for_missing(state):
    with pytest.raises(StateError, match="index.yaml"):
        state.read_item("PR-0099")


# -- concurrency ---------------------------------------------------------------

def test_concurrent_captures_allocate_distinct_ids(tmp_path):
    root = str(tmp_path / "project_memory")
    os.makedirs(root)
    ids, errors = [], []

    def work():
        try:
            local = ProjectState(root)
            for _ in range(3):
                ids.append(local.capture("FR", {"title": "w", "request_text": "x"})["id"])
        except Exception as exc:  # pragma: no cover - diagnostic
            errors.append(exc)

    threads = [threading.Thread(target=work) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(ids) == 18
    assert len(set(ids)) == 18  # no duplicate ids under contention


# -- Evidence: the two fields a gate decides on (spec II.2) --------------------

def evidence_fields(**overrides):
    fields = {"kind": "test", "related": ["PR-0001"], "result": "pass",
              "summary": "full suite green",
              "artifact_refs": ["staging/TSK-0001/suite.log"]}
    fields.update(overrides)
    return fields


def test_evidence_capture_needs_a_verdict(state):
    """Without `result` the store cannot tell a passing run from a failing one, and the merge
    gate would open on the mere existence of a report."""
    make_pr(state)
    with pytest.raises(StateError, match="result"):
        state.capture("EVD", {k: v for k, v in evidence_fields().items() if k != "result"})


def test_evidence_carries_no_project_status(state):
    """Evidence never has a status of its own (II.2) — it is a record, not a workflow item."""
    make_pr(state)
    item = state.capture("EVD", evidence_fields())
    assert "status" not in item


@pytest.mark.parametrize("field", ["artifact_refs", "related"])
def test_evidence_capture_refuses_a_record_that_points_at_nothing(state, field):
    """The two list fields of an Evidence must NAME something; present-but-empty is not provided.

    `gate_git` opens a merge on this record and its refusal text presents `--artifact-ref` as the
    proof — so `python scripts/harness.py evidence --kind test --result pass --related PR-0001 --summary "looks
    fine"` used to be enough to open a merge on nothing but the word of whoever typed it
    (measured). `related` is the same shape one field over: an evidence bound to no item is filed
    under its own id and judges no delivery at all, while looking exactly like a verdict.

    Both directions are asserted: the counter-case at the end is what keeps this from being
    satisfiable by refusing every Evidence.
    """
    make_pr(state)
    with pytest.raises(StateError, match="must name something"):
        state.capture("EVD", evidence_fields(**{field: []}))
    assert state.capture("EVD", evidence_fields())["id"] == "EVD-0001"


@pytest.mark.parametrize("field,value", [("result", "passed"), ("kind", "smoke")])
def test_evidence_vocabulary_is_closed_at_capture(state, field, value):
    """A value outside the vocabulary would not FAIL the merge gate, it would skip it: an unknown
    result is not a fail, an unknown kind is not QA."""
    make_pr(state)
    with pytest.raises(StateError, match="unknown EVD"):
        state.capture("EVD", evidence_fields(**{field: value}))


@pytest.mark.parametrize("changes", [
    {"result": "pass"},            # the verdict itself: a FAIL turned into a PASS in place
    {"related": ["PR-0002"]},      # the binding: this verdict now covers a different item
    {"summary": "actually fine"},  # the prose the reader is left with
    {"result": "passed"},          # even a value the vocabulary would refuse anyway
])
def test_no_field_of_an_evidence_can_be_edited(state, changes):
    """A record is superseded, never corrected — the whole item, not just the two gate inputs.

    Measured before the refusal existed: `update_item(evd, {"result": "pass"})` reopened a merge
    `gate_git` had closed and `{"related": [...]}` moved a failing verdict onto another item, in
    both cases without a new item and without a trace in the store. That is what makes the gate's
    own sentence ("retired by recording the re-run, never by editing it") true rather than a
    wish, and it is why the rule is the TYPE's, not a list of protected fields: any field of a
    record that changes makes the record's claim false.
    """
    make_pr(state)
    state.capture("PR", dict(PR_FIELDS, title="Second"))
    item = state.capture("EVD", evidence_fields(result="fail"))
    with pytest.raises(StateError, match="record of something that already happened"):
        state.update_item(item["id"], changes)
    assert state.read_item(item["id"])["result"] == "fail"


def test_an_edit_cannot_rebind_a_task_to_an_origin_that_does_not_exist(state):
    """The reference check runs on the edit path for the reason the vocabulary check does.

    `derives_from` is frozen once a task leaves DRAFT (TSK_PLAN_FIELDS), so the window this closes
    is a DRAFT task: refusing a phantom origin at capture and then accepting it from an edit is
    not refusing it at all, and the dispatch gate resolves `acceptance_refs` against exactly that
    field.
    """
    pr = make_pr(state)
    task = state.capture("TSK", {
        "product_requirement": pr["id"], "root_revision": 1, "derives_from": [pr["id"]],
        "type": "implementation", "assigned_role": "backend-developer",
        "acceptance_refs": ["AC-1"], "required_inputs": [], "allowed_scope": ["src/**"],
        "forbidden_scope": [], "expected_outputs": ["src/x.py"], "dependencies": []})
    with pytest.raises(StateError, match="derives_from PR-0099 does not exist"):
        state.update_item(task["id"], {"derives_from": ["PR-0099"]})
    with pytest.raises(StateError, match="not an item id"):
        state.update_item(task["id"], {"derives_from": ["the login epic"]})
    assert state.read_item(task["id"])["derives_from"] == [pr["id"]]


def test_evidence_related_must_name_items_that_exist(state):
    """Evidence bound to a phantom id covers no work while looking exactly like proof."""
    make_pr(state)
    with pytest.raises(StateError, match="related PR-0099 does not exist"):
        state.capture("EVD", evidence_fields(related=["PR-0099"]))
    with pytest.raises(StateError, match="not an item id"):
        state.capture("EVD", evidence_fields(related=["the nightly run"]))


def _contract_payload(item_type, bindings):
    """A payload that satisfies `item_type`'s contract, with its bindings set as given.

    Built from `REQUIRED_FIELDS` so a new field cannot make this test silently stop reaching
    the check it is about, and from `_CLOSED_VOCABULARY` for the fields the kernel judges
    against a fixed vocabulary a few lines earlier -- both read from the kernel rather than
    retyped, so the fixture cannot drift from the contract it is a fixture for.

    THE REQUESTED BINDINGS ARE SET WHETHER OR NOT THE CONTRACT REQUIRES THEM. `REQUIRED_FIELDS`
    cannot mention an optional field, and two of the graph's bindings are optional by spec II.2
    (`PROC.derives_from`, `FR.related_pr`) -- built from the required half alone, this payload
    simply left them out, and the caller's `pytest.raises` then failed with DID NOT RAISE on a
    capture that was never asked to bind anything. The payload has to carry what the caller is
    testing, not only what the type may not omit.
    """
    payload = {}
    for field in REQUIRED_FIELDS[item_type]:
        allowed = _CLOSED_VOCABULARY.get((item_type, field))
        payload[field] = sorted(allowed[0])[0] if allowed else bindings.get(field, "x")
    for field, value in bindings.items():
        payload.setdefault(field, value)
    return payload


def test_a_binding_a_field_contract_declares_is_checked_for_every_type_that_has_one(state):
    """The write-path check reads `PARENT_FIELDS`, so it cannot fall behind the graph.

    It used to carry its own two-name list (`TSK.derives_from`, `EVD.related`) while the
    reference graph in `report` carried a second one, and the two drifted apart around `SR`:
    its REQUIRED `derives_from` was in neither, so an `SR` could be captured against a phantom
    parent AND the Evidence judging it then resolved to no root.

    Asserted over the whole map rather than over the types that carry a binding today, because
    "a type nobody added to the list" is precisely the defect. Both refusals are asserted --
    a free-text binding and one that parses but names nothing -- and the counter-assertion is
    the same payload with every binding pointed at a real item: it captures, so the refusals
    above cannot be this fixture failing some other part of the contract.

    The types this write path never sees are excluded BY CAPTURE'S OWN CONDITION -- `capture`
    refuses everything outside `REQUIRED_FIELDS` (ARC/WFR/DSN come from the freeze path, which
    validates against their schemas instead) -- and the exclusion is measured rather than
    assumed: each one is offered to `capture` and has to be refused for that reason. A skip
    list would otherwise be the place a type quietly stops being checked.
    """
    root = make_pr(state)
    for item_type in sorted(set(PARENT_FIELDS) - set(REQUIRED_FIELDS)):
        with pytest.raises(StateError, match="capture does not handle type"):
            state.capture(item_type, {})
    for item_type, fields in sorted(PARENT_FIELDS.items()):
        if item_type not in REQUIRED_FIELDS:
            continue
        for field in fields:
            others = {other: root["id"] for other in fields if other != field}
            with pytest.raises(StateError, match="%s PR-0099 does not exist" % field):
                state.capture(item_type,
                              _contract_payload(item_type, dict(others, **{field: "PR-0099"})))
            with pytest.raises(StateError, match="not an item id"):
                state.capture(item_type,
                              _contract_payload(item_type,
                                                dict(others, **{field: "the login epic"})))
        captured = state.capture(item_type,
                                 _contract_payload(item_type, {f: root["id"] for f in fields}))
        assert captured["id"].startswith(item_type + "-"), item_type


def test_read_anywhere_follows_an_item_into_the_archive(state):
    """The walk the merge gate needs: a task is archived at VALIDATED, before the merge it
    cleared, so a reader that stops at active/ loses the binding at the finish line."""
    pr = make_pr(state)
    state.transition(pr["id"], "REJECTED")
    state.archive(pr["id"])
    item, archived = state.read_anywhere(pr["id"])
    assert archived and item["id"] == pr["id"]
    assert state.read_anywhere("PR-0099") == (None, False)
    assert state.read_anywhere("not an id") == (None, False)
