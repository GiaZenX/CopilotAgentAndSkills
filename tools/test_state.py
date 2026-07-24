"""Tests for the state-kernel core operations (HARNESS_V2_SPEC.md II.4, step 1.4a)."""
import os
import sys
import threading

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits"))

from kernel.backlog_types import TransitionError  # noqa: E402
from kernel.state import ProjectState, StateError  # noqa: E402


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
    for step in ("APPROVED", "IN_DELIVERY", "DELIVERED", "ACCEPTED"):
        state.transition(item["id"], step)
    state.archive(item["id"])
    assert make_pr(state)["id"] == "PR-0002"


# -- transition ----------------------------------------------------------------

def test_transition_chain_and_illegal_jump(state):
    item = make_pr(state)
    state.transition(item["id"], "APPROVED")
    with pytest.raises(TransitionError):
        state.transition(item["id"], "ACCEPTED")  # only from DELIVERED


def test_tsk_failed_ready_requires_approved_retry(state):
    task = state.capture("TSK", {
        "product_requirement": "PR-0001",
        "root_revision": 1,
        "derives_from": "PR-0001",
        "type": "implementation",
        "assigned_role": "backend-developer",
        "acceptance_refs": ["AC-1"],
        "required_inputs": [],
        "allowed_scope": ["src/"],
        "forbidden_scope": ["project_memory/"],
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
    state.transition(item["id"], "APPROVED")
    index = yaml.safe_load(open(index_path, encoding="utf-8"))
    assert index["items"][0]["status"] == "APPROVED"
    state.transition(item["id"], "SUPERSEDED")
    state.archive(item["id"])
    index = yaml.safe_load(open(index_path, encoding="utf-8"))
    assert index["items"] == []  # archived items leave the active context


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
