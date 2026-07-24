"""Tests for the approval protocol + dispatch leases (HARNESS_V2_SPEC.md II.2/II.4)."""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits"))

from kernel import approvals, dispatch  # noqa: E402
from kernel.approvals import ApprovalError  # noqa: E402
from kernel.dispatch import DispatchError  # noqa: E402
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
}

TSK_FIELDS = {
    "derives_from": "PR-0001",
    "type": "implementation",
    "assigned_role": "backend-developer",
    "acceptance_refs": ["AC-1"],
    "required_inputs": [],
    "allowed_scope": ["src/"],
    "forbidden_scope": ["project_memory/"],
    "expected_outputs": ["src/x.py"],
    "dependencies": [],
}


@pytest.fixture
def state(tmp_path):
    root = tmp_path / "project_memory"
    root.mkdir()
    return ProjectState(str(root))


def approve_scope(state, item_id):
    request = approvals.create_pending_request(state, "scope", item_id)
    return approvals.mint(
        state, request["request_id"], approvals.approve_label(request["mint_code"])
    )


def make_ready_task(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    approve_scope(state, pr["id"])
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    state.transition(task["id"], "READY")
    return pr, state.read_item(task["id"])


# -- approval protocol ---------------------------------------------------------

def test_scope_approval_happy_path(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    apr = approve_scope(state, pr["id"])
    item = state.read_item(pr["id"])
    assert item["approval_ref"] == apr["id"]
    assert item["status"] == "APPROVED"  # (PR, scope) side-effect transition
    assert apr["revision"] == 1 and apr["revoked"] is False
    # request consumed, auditable
    assert os.path.exists(os.path.join(state.root, "approvals", "consumed", apr["request_id"] + ".yaml"))
    assert not os.path.exists(os.path.join(state.root, "approvals", "pending", apr["request_id"] + ".yaml"))


def test_question_is_deterministic_and_marked(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])
    q1 = approvals.build_question(request)
    q2 = approvals.build_question(request)
    assert q1 == q2
    assert "[APR-REQ:%s]" % request["request_id"] in q1["question"]
    assert q1["options"][0]["label"] == approvals.approve_label(request["mint_code"])
    assert [o["label"] for o in q1["options"][1:]] == ["Ändern", "Ablehnen"]
    assert len(request["mint_code"]) == 6  # per-request entropy (S2b)
    # SECRECY INVARIANT: the code must live ONLY in the approval option label --
    # leaking it into the question/header/descriptions would destroy the whole
    # mechanism (a user could then retype it without ever clicking)
    exposed = q1["question"] + q1["header"] + "".join(o["description"] for o in q1["options"])
    assert request["mint_code"] not in exposed


def test_free_text_freigeben_never_mints(state):
    """S2b amendment: the platform cannot distinguish a clicked option from
    'Other'-typed text (verified 2026-07-24) -- the per-request mint code does:
    a plain typed 'Freigeben' never mints."""
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])
    for typed in ("Freigeben", "freigeben", "ja", "ok, passt", "Freigeben [000000]"):
        with pytest.raises(ApprovalError, match="does not mint"):
            approvals.mint(state, request["request_id"], typed)
    # request survives until TTL (no auto-invalidation)
    assert os.path.exists(os.path.join(state.root, "approvals", "pending", request["request_id"] + ".yaml"))


def test_label_of_another_request_never_mints(state):
    """Cross-request: a VALID label only mints ITS own request."""
    pr_a = state.capture("PR", dict(PR_FIELDS))
    pr_b = state.capture("PR", dict(PR_FIELDS))
    req_a = approvals.create_pending_request(state, "scope", pr_a["id"])
    req_b = approvals.create_pending_request(state, "scope", pr_b["id"])
    assert req_a["mint_code"] != req_b["mint_code"]
    with pytest.raises(ApprovalError, match="does not mint"):
        approvals.mint(state, req_a["request_id"], approvals.approve_label(req_b["mint_code"]))


def test_apr_records_mint_code(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])
    apr = approvals.mint(state, request["request_id"], approvals.approve_label(request["mint_code"]))
    assert apr["mint_code"] == request["mint_code"]  # spec II.2 APR field list


def test_request_without_mint_code_fails_closed(state):
    """Pre-amendment or hand-written pending file -> refuse, never mint."""
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])
    path = os.path.join(state.root, "approvals", "pending", request["request_id"] + ".yaml")
    import yaml
    original = yaml.safe_load(open(path, encoding="utf-8"))
    for broken in ("__delete__", None, "", "TOOLONG", "ZZZZZZ"):
        raw = dict(original)
        if broken == "__delete__":
            del raw["mint_code"]
        else:
            raw["mint_code"] = broken
        yaml.safe_dump(raw, open(path, "w", encoding="utf-8"), sort_keys=False, allow_unicode=True)
        # the guessable label a malformed code would produce must not mint either
        for attempt in ("Freigeben [abc123]", "Freigeben [None]", "Freigeben []",
                        "Freigeben [%s]" % broken):
            with pytest.raises(ApprovalError, match="no valid mint_code"):
                approvals.mint(state, request["request_id"], attempt)


def test_aendern_and_ablehnen_never_mint(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])
    for label in ("Ändern", "Ablehnen"):
        with pytest.raises(ApprovalError):
            approvals.mint(state, request["request_id"], label)


def test_expired_request_never_mints(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"], ttl_seconds=0.01)
    time.sleep(0.05)
    with pytest.raises(ApprovalError, match="expired"):
        approvals.mint(state, request["request_id"], approvals.approve_label(request["mint_code"]))


def test_unknown_request_never_mints(state):
    with pytest.raises(ApprovalError, match="never mint"):
        approvals.mint(state, "deadbeef", "Freigeben [x]")


def test_out_of_band_edit_kills_mint(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])
    state.update_item(pr["id"], {"goal": "changed after the question"})
    with pytest.raises(ApprovalError, match="changed since the request|out-of-band"):
        approvals.mint(state, request["request_id"], approvals.approve_label(request["mint_code"]))


def test_analysis_requires_explicit_manifest_and_bundles_tasks(state):
    with pytest.raises(ApprovalError, match="manifest"):
        approvals.create_pending_request(state, "analysis")
    request = approvals.create_pending_request(
        state, "analysis",
        manifest={"question": "why is X slow", "read_only_scope": ["src/"],
                  "expected_result": "profile", "tasks": ["TSK-0001", "TSK-0002"]},
    )
    apr = approvals.mint(state, request["request_id"], approvals.approve_label(request["mint_code"]))
    assert apr["item"] is None and apr["kind"] == "analysis"


def test_revoke(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    apr = approve_scope(state, pr["id"])
    assert approvals.revoke(state, apr["id"])["revoked"] is True


# -- dispatch ------------------------------------------------------------------

def test_create_task_denormalizes_root_revision(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    assert task["root_revision"] == 1
    with pytest.raises(DispatchError, match="kernel-set"):
        dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"], root_revision=7))


def test_lease_happy_path_and_header_roundtrip(state):
    _pr, task = make_ready_task(state)
    lease = dispatch.create_lease(state, task["id"])
    assert state.read_item(task["id"])["status"] == "LEASED"
    header = dispatch.parse_header("objective: x\n" + dispatch.dispatch_header(lease))
    assert dispatch.validate_lease(state, header)["nonce"] == lease["nonce"]


def test_lease_requires_ready(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    approve_scope(state, pr["id"])
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    with pytest.raises(DispatchError, match="not READY"):
        dispatch.create_lease(state, task["id"])


def test_lease_requires_root_approval(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    state.transition(task["id"], "READY")
    with pytest.raises(DispatchError, match="no current approval"):
        dispatch.create_lease(state, task["id"])


def test_lease_blocked_for_invalidated_root_revision(state):
    pr, task = make_ready_task(state)
    # hashed edit on approved root -> revision bump + approval cleared
    state.update_item(pr["id"], {"goal": "moved goalposts"})
    with pytest.raises(DispatchError, match="no current approval"):
        dispatch.create_lease(state, task["id"])
    # even with a fresh approval, the OLD task revision stays unleasable
    request = approvals.create_pending_request(state, "scope", pr["id"])
    approvals.mint(state, request["request_id"], approvals.approve_label(request["mint_code"]))
    with pytest.raises(DispatchError, match="not leasable|invalidated root revision"):
        dispatch.create_lease(state, task["id"])


def test_second_claim_blocked(state):
    _pr, task = make_ready_task(state)
    dispatch.create_lease(state, task["id"])
    # normal path: the LEASED status blocks the second claim first
    with pytest.raises(DispatchError, match="not READY"):
        dispatch.create_lease(state, task["id"])
    # inconsistent state (lease file present but task forced back to READY,
    # e.g. after a crash between writes): the dedicated guard still blocks
    with state.lock:
        raw = state.read_item(task["id"])
        raw["status"] = "READY"
        state._write_yaml_atomic(state.active_path(task["id"]), raw)
    with pytest.raises(DispatchError, match="second claim"):
        dispatch.create_lease(state, task["id"])


def test_revoked_approval_blocks_lease(state):
    pr, task = make_ready_task(state)
    approvals.revoke(state, state.read_item(pr["id"])["approval_ref"])
    with pytest.raises(DispatchError, match="revoked"):
        dispatch.create_lease(state, task["id"])


def test_missing_header_blocks(state):
    with pytest.raises(DispatchError, match="no HARNESS_DISPATCH header"):
        dispatch.parse_header("objective: build\noutput: yaml")


def test_random_task_id_prose_blocks(state):
    """II.12: free prose with a random TSK id -> block (header required)."""
    with pytest.raises(DispatchError):
        dispatch.parse_header("please work on TSK-0099 thanks")


def test_spawn_failure_returns_to_ready(state):
    _pr, task = make_ready_task(state)
    dispatch.create_lease(state, task["id"])
    dispatch.spawn_outcome(state, task["id"], ok=False)
    assert state.read_item(task["id"])["status"] == "READY"
    assert not os.path.exists(os.path.join(state.root, "tasks", "leases", task["id"] + ".lease.yaml"))


def test_lease_timeout_sweep_returns_to_ready(state):
    _pr, task = make_ready_task(state)
    dispatch.create_lease(state, task["id"], ttl=0.01)
    time.sleep(0.05)
    assert dispatch.sweep_expired_leases(state) == [task["id"]]
    assert state.read_item(task["id"])["status"] == "READY"


def test_bind_agent_records_subagent_id(state):
    _pr, task = make_ready_task(state)
    dispatch.create_lease(state, task["id"])
    lease = dispatch.bind_agent(state, task["id"], "agent-abc123")
    assert lease["agent_id"] == "agent-abc123"


def test_submit_result_full_cycle(state):
    _pr, task = make_ready_task(state)
    lease = dispatch.create_lease(state, task["id"])
    dispatch.spawn_outcome(state, task["id"], ok=True)
    envelope = {
        "task_id": task["id"],
        "role": "backend-developer",
        "status_proposal": "SUBMITTED",
        "summary": "done per AC-1",
        "outputs": ["src/x.py"],
        "evidence": [],
        "scope_touched": ["src/x.py"],
        "followups": [],
    }
    updated = dispatch.submit_result(state, envelope)
    assert updated["status"] == "SUBMITTED"
    assert os.path.exists(os.path.join(state.root, "tasks", "results", task["id"] + ".envelope.yaml"))
    assert lease["nonce"]  # lease consumed
    assert not os.path.exists(os.path.join(state.root, "tasks", "leases", task["id"] + ".lease.yaml"))


def test_open_dependency_blocks_lease(state):
    """II.12: 'offene Abhaengigkeit -> Block' (Fable-Check 8/#1)."""
    pr, task_a = make_ready_task(state)
    task_b = dispatch.create_task(state, dict(
        TSK_FIELDS, product_requirement=pr["id"], dependencies=[task_a["id"]]
    ))
    state.transition(task_b["id"], "READY")
    with pytest.raises(DispatchError, match="open dependencies"):
        dispatch.create_lease(state, task_b["id"])
    # dependency reaches DONE -> lease possible
    for step in ("LEASED", "IN_PROGRESS", "SUBMITTED", "DONE"):
        state.transition(task_a["id"], step)
    assert dispatch.create_lease(state, task_b["id"])["task_id"] == task_b["id"]


def test_submit_failed_proposal_moves_task_to_failed(state):
    _pr, task = make_ready_task(state)
    dispatch.create_lease(state, task["id"])
    dispatch.spawn_outcome(state, task["id"], ok=True)
    updated = dispatch.submit_result(state, {
        "task_id": task["id"], "role": "backend-developer",
        "status_proposal": "FAILED", "summary": "blocked by missing schema",
        "outputs": [], "evidence": [], "scope_touched": [], "followups": [],
    })
    assert updated["status"] == "FAILED"


def test_double_header_first_line_wins(state):
    _pr, task = make_ready_task(state)
    lease = dispatch.create_lease(state, task["id"])
    prompt = dispatch.dispatch_header(lease) + "\n" + dispatch.HEADER_PREFIX + '{"task_id":"TSK-9999","root_revision":9,"lease":"bogus"}'
    assert dispatch.parse_header(prompt)["lease"] == lease["nonce"]


def test_create_task_accepts_rq_root(state):
    rq = state.capture("RQ", {
        "title": "Latency study", "class": "normal", "question": "why slow",
        "motivation": "perf", "acceptance_criteria": [{"id": "AC-1", "text": "answered"}],
        "out_of_scope": [], "priority": "high",
    })
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=rq["id"]))
    assert task["root_revision"] == 1


def test_mint_replay_blocked(state):
    """Fable-Check 8/#2: a half-consumed request must not mint twice."""
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])
    approvals.mint(state, request["request_id"], approvals.approve_label(request["mint_code"]))
    # simulate the crash-replay: restore the consumed request as pending
    import shutil
    consumed = os.path.join(state.root, "approvals", "consumed", request["request_id"] + ".yaml")
    pending = os.path.join(state.root, "approvals", "pending", request["request_id"] + ".yaml")
    shutil.copy(consumed, pending)
    with pytest.raises(ApprovalError, match="replay blocked"):
        approvals.mint(state, request["request_id"], approvals.approve_label(request["mint_code"]))


def test_submit_result_rejects_invalid_envelope(state):
    _pr, task = make_ready_task(state)
    dispatch.create_lease(state, task["id"])
    dispatch.spawn_outcome(state, task["id"], ok=True)
    from kernel.schemas import SchemaError
    with pytest.raises(SchemaError):
        dispatch.submit_result(state, {"task_id": task["id"]})
