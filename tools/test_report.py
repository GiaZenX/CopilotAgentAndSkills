"""Tests for session brief, state validator and doctor (spec II.4/II.5, step 1.4c)."""
import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits"))

from kernel import approvals, dispatch, report  # noqa: E402
from kernel.state import ProjectState  # noqa: E402


PR_FIELDS = {
    "title": "Checkout flow",
    "class": "normal",
    "problem": "no checkout",
    "goal": "working checkout",
    "acceptance_criteria": [{"id": "AC-1", "text": "order completes"}],
    "invariants": [],
    "out_of_scope": [],
    "priority": "high",
    "user_story": "As a buyer I can pay",
}


@pytest.fixture
def state(tmp_path):
    root = tmp_path / "project_memory"
    root.mkdir()
    return ProjectState(str(root))


def errors(findings):
    return [f for f in findings if f["severity"] == "error"]


# -- validator -----------------------------------------------------------------

def test_clean_state_has_no_errors(state):
    state.capture("PR", dict(PR_FIELDS))
    assert errors(report.validate_state(state)) == []


def test_out_of_band_hand_edit_detected_via_hash(state):
    """D/4: an IDE edit past the kernel invalidates the approval VISIBLY."""
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])
    approvals.mint(state, request["request_id"], approvals.approve_label(request["mint_code"]))
    assert errors(report.validate_state(state)) == []
    # hand-edit: bypass the kernel entirely (same revision, changed content)
    path = state.active_path(pr["id"])
    item = yaml.safe_load(open(path, encoding="utf-8"))
    item["goal"] = "sneakily changed in the IDE"
    yaml.safe_dump(item, open(path, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
    found = errors(report.validate_state(state))
    assert any("content hash" in f["message"] for f in found)
    assert any("re-approve or revert" in f["remedy"] for f in found)


def test_manually_written_apr_ref_detected(state):
    """II.12: manually written APR without kernel token -> flagged."""
    pr = state.capture("PR", dict(PR_FIELDS))
    path = state.active_path(pr["id"])
    item = yaml.safe_load(open(path, encoding="utf-8"))
    item["approval_ref"] = "APR-0042"  # no such APR file
    yaml.safe_dump(item, open(path, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
    found = errors(report.validate_state(state))
    assert any("no APR file" in f["message"] for f in found)


def test_status_dependent_duties(state):
    fr = state.capture("FR", {"title": "wish", "request_text": "please add X"})
    state.transition(fr["id"], "TRIAGED")
    found = errors(report.validate_state(state))
    assert any("triage_result" in f["message"] for f in found)


def test_inv_text_value_one_of(state):
    inv = state.capture("INV", {
        "scope": "frontend", "source": "PR-0001",
        "check": {"kind": "test", "ref": "t.py::test_x"},
    })
    found = errors(report.validate_state(state))
    assert any(inv["id"] == f["item"] and "text|value" in f["message"] for f in found)


def test_item_budget_enforced(state):
    pr = state.capture("PR", dict(PR_FIELDS, problem="x" * 13000))
    found = errors(report.validate_state(state))
    assert any(pr["id"] == f["item"] and "budget" in f["message"] for f in found)


def test_orphaned_staging_flagged(state):
    os.makedirs(os.path.join(state.root, "staging", "TSK-0099"))
    findings = report.validate_state(state)
    assert any("orphaned staging" in f["message"] for f in findings)


def test_dangling_reference_flagged(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    dispatch.create_task(state, {
        "product_requirement": pr["id"], "derives_from": pr["id"],
        "type": "implementation", "assigned_role": "backend-developer",
        "acceptance_refs": ["AC-1"], "required_inputs": [],
        "allowed_scope": ["src/"], "forbidden_scope": [],
        "expected_outputs": [], "dependencies": ["TSK-1234"],
    })
    found = errors(report.validate_state(state))
    assert any("TSK-1234" in f["message"] for f in found)


def test_staging_dir_keyed_by_active_root_not_flagged(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    os.makedirs(os.path.join(state.root, "staging", pr["id"]))
    assert not any("orphaned staging" in f["message"] for f in report.validate_state(state))


def test_terminal_unarchived_item_warned(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    state.transition(pr["id"], "REJECTED")
    findings = report.validate_state(state)
    assert any("awaiting archive" in f["message"] and pr["id"] == f["item"] for f in findings)


def test_related_pr_to_archived_item_is_no_error(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    state.transition(pr["id"], "REJECTED")
    state.archive(pr["id"])
    state.capture("BUG", {
        "title": "regression", "related_pr": pr["id"], "observed": "x",
        "expected": "y", "repro": "steps", "severity": "high",
        "acceptance_criteria": [{"id": "AC-1", "text": "fixed"}],
    })
    assert not any("related_pr" in f["message"] for f in errors(report.validate_state(state)))


# -- session brief -------------------------------------------------------------

def test_session_brief_generated_and_schema_valid(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])  # left open
    path = report.generate_session_brief(state, "dev-team", "2026.07.24-rc1", "audited")
    brief = yaml.safe_load(open(path, encoding="utf-8"))
    assert brief["active_roots"][0]["id"] == pr["id"]
    assert brief["active_roots"][0]["next_step"] == "Scope-Freigabe einholen"
    assert brief["open_approvals"][0]["request_id"] == request["request_id"]
    assert brief["enforcement_mode"] == "audited"


def test_session_brief_reports_validator_budget(state):
    state.capture("PR", dict(PR_FIELDS, problem="x" * 13000))
    path = report.generate_session_brief(state, "dev-team", "v", "audited")
    brief = yaml.safe_load(open(path, encoding="utf-8"))
    assert brief["budget_status"]["validator_errors"] >= 1


def test_expired_request_not_listed_as_open(state):
    import time as _time
    pr = state.capture("PR", dict(PR_FIELDS))
    approvals.create_pending_request(state, "scope", pr["id"], ttl_seconds=0.01)
    _time.sleep(0.05)
    path = report.generate_session_brief(state, "dev-team", "v", "audited")
    brief = yaml.safe_load(open(path, encoding="utf-8"))
    assert brief["open_approvals"] == []
    assert brief["budget_status"]["expired_requests"] == 1


# -- doctor --------------------------------------------------------------------

def test_doctor_reports_lock_leases_and_findings(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])
    approvals.mint(state, request["request_id"], approvals.approve_label(request["mint_code"]))
    task = dispatch.create_task(state, {
        "product_requirement": pr["id"], "derives_from": pr["id"],
        "type": "implementation", "assigned_role": "backend-developer",
        "acceptance_refs": ["AC-1"], "required_inputs": [],
        "allowed_scope": ["src/"], "forbidden_scope": [],
        "expected_outputs": [], "dependencies": [],
    })
    state.transition(task["id"], "READY")
    dispatch.create_lease(state, task["id"], ttl=0.01)
    result = report.doctor(state, kit="dev-team", kit_version="rc1")
    assert result["lock"] == {"state": "free"}
    assert result["leases"][0]["task_id"] == task["id"]
    assert result["leases"][0]["expired"] is True
    assert result["index_present"] is True
    assert result["kit"] == "dev-team"


def test_doctor_reports_held_lock(state):
    state.lock.acquire(timeout=1)
    try:
        result = report.doctor(state)
        assert result["lock"]["held_by_pid"] == os.getpid()
    finally:
        state.lock.release()


def test_doctor_never_writes_state(state):
    state.capture("PR", dict(PR_FIELDS))
    before = {}
    for base, _dirs, files in os.walk(state.root):
        for name in files:
            p = os.path.join(base, name)
            before[p] = os.path.getmtime(p)
    report.doctor(state)
    after = {}
    for base, _dirs, files in os.walk(state.root):
        for name in files:
            p = os.path.join(base, name)
            after[p] = os.path.getmtime(p)
    assert before == after  # read-only: no file added, removed or touched
