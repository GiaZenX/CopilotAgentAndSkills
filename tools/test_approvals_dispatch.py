"""Tests for the approval protocol + dispatch leases (HARNESS_V2_SPEC.md II.2/II.4)."""
import json
import os
import subprocess
import sys
import time

import pytest

TEAM_KITS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits")
sys.path.insert(0, TEAM_KITS)

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
    "forbidden_scope": ["secrets/"],
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
    mint_via_hook(state, request)
    return approvals.read_apr(state, state.read_item(item_id)["approval_ref"])

def mint_via_hook(state, request, answer=None, expect_success=True):
    """Mint through the REAL PostToolUse hook — the only caller the kernel accepts.

    `mint` refuses any other caller (user condition (i), 2026-07-25): it is a plain function, and
    anything that can read `approvals/pending/<id>.yaml` would otherwise be able to pass the label
    it found there and manufacture a user approval. So every test that expects a SUCCESSFUL mint
    drives the hook, which also means the mint path is exercised end to end rather than in a
    library call no production code makes. Refusal tests keep calling `mint` directly: the caller
    check is deliberately last, so content refusals still report on their own terms.
    """
    repo = os.path.dirname(state.root)
    question = approvals.build_question(request)
    if answer is None:
        answer = approvals.approve_label(request["mint_code"])
    payload = {
        "hook_event_name": "PostToolUse", "tool_name": "AskUserQuestion", "cwd": repo,
        "tool_input": {"questions": [question]},
        "tool_response": {"answers": {question["question"]: answer},
                          "questions": [question]},
    }
    env = dict(os.environ, CLAUDE_PROJECT_DIR=repo, HARNESS_KERNEL_PATH=TEAM_KITS)
    result = subprocess.run(
        [sys.executable, os.path.join(TEAM_KITS, "dev-team", "hooks", "gate_approval.py")],
        input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=120)
    assert result.returncode == 0, result.stderr
    if expect_success:
        assert "recorded for" in result.stderr, result.stderr
    return result



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
    mint_via_hook(state, request)
    apr = _latest_apr(state)
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
        approvals.create_pending_request(state, "analysis",
                                        approval_expires=time.time() + 3600)
    request = approvals.create_pending_request(
        state, "analysis",
        manifest={"question": "why is X slow", "read_only_scope": ["src/"],
                  "expected_result": "profile", "tasks": ["TSK-0001", "TSK-0002"]},
        approval_expires=time.time() + 3600,
    )
    mint_via_hook(state, request)
    apr = _latest_apr(state)
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


def test_lease_requires_an_approval_by_either_route(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    state.transition(task["id"], "READY")
    with pytest.raises(DispatchError, match="no subagent without a user approval"):
        dispatch.create_lease(state, task["id"])


def test_lease_blocked_for_invalidated_root_revision(state):
    pr, task = make_ready_task(state)
    # hashed edit on approved root -> revision bump + approval cleared
    state.update_item(pr["id"], {"goal": "moved goalposts"})
    with pytest.raises(DispatchError, match="no subagent without a user approval"):
        dispatch.create_lease(state, task["id"])
    # even with a fresh approval, the OLD task revision stays unleasable
    request = approvals.create_pending_request(state, "scope", pr["id"])
    mint_via_hook(state, request)
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
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=rq["id"],
                                            derives_from=rq["id"]))
    assert task["root_revision"] == 1


def test_mint_replay_blocked(state):
    """Fable-Check 8/#2: a half-consumed request must not mint twice."""
    pr = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", pr["id"])
    mint_via_hook(state, request)
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


# -- gate layer 2: validate_dispatch at SPAWN time (spec II.4 / II.12) ---------

def leased(state):
    """A task with a live lease and the header its dispatch would carry."""
    _pr, task = make_ready_task(state)
    lease = dispatch.create_lease(state, task["id"])
    return task, lease, dispatch.parse_header(dispatch.dispatch_header(lease))


def test_validate_dispatch_happy_path(state):
    task, _lease, header = leased(state)
    result = dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])
    assert result["task"]["id"] == task["id"]


def test_role_mismatch_blocks(state):
    _task, _lease, header = leased(state)
    with pytest.raises(DispatchError, match="role mismatch"):
        dispatch.validate_dispatch(state, header, "frontend-developer")


def test_missing_subagent_type_blocks(state):
    _task, _lease, header = leased(state)
    with pytest.raises(DispatchError, match="role mismatch"):
        dispatch.validate_dispatch(state, header, None)


def test_foreign_lease_nonce_blocks(state):
    _task, _lease, header = leased(state)
    header["lease"] = "0" * 32
    with pytest.raises(DispatchError, match="nonce mismatch"):
        dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def _edit_around_the_kernel(state, item_id, changes):
    """Write an item file directly -- what an IDE edit does (spec II.4 gate 4)."""
    import yaml
    path = state.active_path(item_id)
    with open(path, encoding="utf-8") as fh:
        item = yaml.safe_load(fh)
    item.update(changes)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(item, fh, sort_keys=False, allow_unicode=True)


def test_out_of_band_edit_between_lease_and_spawn_blocks(state):
    """create_lease checked the approval; this checks it AGAIN at spawn time, because an edit
    around the kernel leaves approval_ref pointing at an approval that no longer describes the
    item."""
    _task, _lease, header = leased(state)
    _edit_around_the_kernel(state, "PR-0001", {"goal": "something the user never approved"})
    with pytest.raises(DispatchError, match="out-of-band edit"):
        dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def test_re_approval_after_an_out_of_band_edit_restores_dispatch(state):
    """II.12: "ungueltiger APR-Hash -> Block (nach Re-Approve + Hash-Update -> pass)". Without
    this the block above could be a permanent dead end."""
    task, _lease, header = leased(state)
    _edit_around_the_kernel(state, "PR-0001", {"goal": "an edit the user then approves"})
    approve_scope(state, "PR-0001")
    state.transition(task["id"], "CANCELLED")
    fresh = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement="PR-0001"))
    state.transition(fresh["id"], "READY")
    new_lease = dispatch.create_lease(state, fresh["id"])
    new_header = dispatch.parse_header(dispatch.dispatch_header(new_lease))
    assert dispatch.validate_dispatch(state, new_header, TSK_FIELDS["assigned_role"])


def test_revoked_approval_blocks_dispatch_even_with_a_live_lease(state):
    _task, _lease, header = leased(state)
    approvals.revoke(state, state.read_item("PR-0001")["approval_ref"])
    with pytest.raises(DispatchError, match="revoked"):
        dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def test_dependency_that_opens_after_the_lease_blocks_dispatch(state):
    _pr, first = make_ready_task(state)
    second = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement="PR-0001",
                                              dependencies=[first["id"]]))
    state.transition(second["id"], "READY")
    for status in ("LEASED", "IN_PROGRESS", "SUBMITTED", "DONE"):
        state.transition(first["id"], status)
    lease = dispatch.create_lease(state, second["id"])
    header = dispatch.parse_header(dispatch.dispatch_header(lease))
    state.transition(first["id"], "FAILED")
    with pytest.raises(DispatchError, match="open dependencies"):
        dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def test_task_without_acceptance_refs_is_not_dispatchable(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    approve_scope(state, pr["id"])
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"],
                                            acceptance_refs=[]))
    state.transition(task["id"], "READY")
    lease = dispatch.create_lease(state, task["id"])
    header = dispatch.parse_header(dispatch.dispatch_header(lease))
    with pytest.raises(DispatchError, match="acceptance_refs"):
        dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def _ui_task(state, **overrides):
    pr = state.capture("PR", dict(PR_FIELDS))
    state.update_item(pr["id"], {"design_refs": ["DSN-0001"]})
    approve_scope(state, pr["id"])
    fields = dict(TSK_FIELDS, product_requirement=pr["id"], type="ui",
                  assigned_role="frontend-developer")
    fields.update(overrides)
    task = dispatch.create_task(state, fields)
    state.transition(task["id"], "READY")
    lease = dispatch.create_lease(state, task["id"])
    return dispatch.parse_header(dispatch.dispatch_header(lease))


def test_ui_task_without_design_ref_blocks_when_a_design_is_confirmed(state):
    header = _ui_task(state)
    with pytest.raises(DispatchError, match="design_ref"):
        dispatch.validate_dispatch(state, header, "frontend-developer")


def test_ui_task_with_design_ref_dispatches(state):
    header = _ui_task(state, design_ref="DSN-0001")
    assert dispatch.validate_dispatch(state, header, "frontend-developer")


def test_a_dangling_design_ref_does_not_satisfy_the_design_gate(state):
    """Truthiness is not resolution: `design_ref: "TBD"` passed a non-empty test while pointing at
    nothing, so the specialist would implement against no frozen revision — the exact failure II.6
    exists to prevent. Third defect in a row on this rule, each one the gate's INPUT going
    unvalidated a level further out."""
    header = _ui_task(state, design_ref="a revision that exists nowhere")
    with pytest.raises(DispatchError, match="design_ref"):
        dispatch.validate_dispatch(state, header, "frontend-developer")


def _dispatchable(state, root_id, **task_overrides):
    fields = dict(TSK_FIELDS, product_requirement=root_id)
    fields.update(task_overrides)
    task = dispatch.create_task(state, fields)
    state.transition(task["id"], "READY")
    lease = dispatch.create_lease(state, task["id"])
    return dispatch.parse_header(dispatch.dispatch_header(lease))


@pytest.mark.parametrize("origin", ["not an item at all", "PR-9999", 42, ["PR-0001", "nonsense"]])
def test_a_task_cannot_derive_from_something_that_does_not_exist(state, origin):
    """`derives_from` became a gate input the moment acceptance_refs started resolving against it,
    so a phantom id, an integer or a free-text note would let a task look derived while
    contributing no criteria at all. The cheap half is enforced here; whether the origin belongs to
    this root's TREE is a reference-graph question and sits on the validator's duty list."""
    pr = state.capture("PR", dict(PR_FIELDS))
    with pytest.raises(Exception):
        dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"],
                                         derives_from=origin))


def test_a_task_may_derive_from_an_archived_item(state):
    """Archived origins still resolve: a fix task for a closed bug is legitimate, and staleness is
    the validator's judgement rather than a hard capture-time refusal."""
    pr = state.capture("PR", dict(PR_FIELDS))
    approve_scope(state, pr["id"])
    bug = state.capture("BUG", {"title": "old", "related_pr": pr["id"], "observed": "x",
                                "expected": "y", "repro": "z", "severity": "low",
                                "acceptance_criteria": [{"id": "AC-OLD", "text": "fixed"}]})
    state.transition(bug["id"], "TRIAGED")
    state.transition(bug["id"], "REJECTED")
    state.archive(bug["id"])
    header = _dispatchable(state, pr["id"], type="bugfix", derives_from=bug["id"],
                           acceptance_refs=["AC-OLD"])
    assert dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def test_a_bugfix_task_may_reference_the_bugs_own_fix_criteria(state):
    """spec II.2 gives BUG its own acceptance_criteria (Fix-Kriterien). Resolving a task's refs
    against the PR/RQ root ALONE blocked the correct shape and would have passed only the wrong
    one — a bugfix referencing the PR's AC instead of the BUG's."""
    pr = state.capture("PR", dict(PR_FIELDS))
    approve_scope(state, pr["id"])
    bug = state.capture("BUG", {"title": "checkout 500s", "related_pr": pr["id"],
                                "observed": "500", "expected": "200", "repro": "click",
                                "severity": "high",
                                "acceptance_criteria": [{"id": "AC-FIX-1", "text": "no 500"}]})
    header = _dispatchable(state, pr["id"], type="bugfix", derives_from=bug["id"],
                           acceptance_refs=["AC-FIX-1"])
    assert dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def test_a_cr_derived_task_may_reference_the_crs_own_criteria(state):
    """A CR exists precisely because its AC differ from the PR revision it changes."""
    pr = state.capture("PR", dict(PR_FIELDS))
    approve_scope(state, pr["id"])
    cr = state.capture("CR", {"title": "add express checkout", "target_pr": pr["id"],
                              "target_revision": 1, "change_description": "express lane",
                              "acceptance_criteria": [{"id": "AC-CR-1", "text": "one click"}]})
    header = _dispatchable(state, pr["id"], derives_from=cr["id"], acceptance_refs=["AC-CR-1"])
    assert dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def test_an_exp_derived_task_may_reference_success_criteria(state):
    """Research: an execution task delivers against the EXP's success_criteria (spec II.2)."""
    rq = state.capture("RQ", {"title": "why slow", "class": "normal", "question": "why?",
                              "motivation": "users wait",
                              "acceptance_criteria": [{"id": "AC-RQ-1", "text": "answered"}],
                              "out_of_scope": [], "priority": "high"})
    approve_scope(state, rq["id"])
    exp = state.capture("EXP", {"derives_from": rq["id"], "design": "A/B", "variables": ["n"],
                                "success_criteria": [{"id": "SC-1", "text": "p<0.05"}],
                                "evidence_refs": []})
    header = _dispatchable(state, rq["id"], type="research", derives_from=exp["id"],
                           acceptance_refs=["SC-1"])
    assert dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def test_plain_string_criteria_resolve_too(state):
    """Real items carry both shapes; a strict check understanding only mappings would block the
    other one."""
    pr = state.capture("PR", dict(PR_FIELDS, acceptance_criteria=["AC-PLAIN"]))
    approve_scope(state, pr["id"])
    header = _dispatchable(state, pr["id"], acceptance_refs=["AC-PLAIN"])
    assert dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def test_acceptance_refs_must_point_at_criteria_that_exist(state):
    """The same shape as the design_ref defect, on the field right next to it: non-emptiness was
    checked, resolution was not."""
    pr = state.capture("PR", dict(PR_FIELDS))
    approve_scope(state, pr["id"])
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"],
                                            acceptance_refs=["AC-1", "AC-does-not-exist"]))
    state.transition(task["id"], "READY")
    lease = dispatch.create_lease(state, task["id"])
    header = dispatch.parse_header(dispatch.dispatch_header(lease))
    with pytest.raises(DispatchError, match="exist nowhere"):
        dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


def test_non_ui_task_needs_no_design_ref(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    state.update_item(pr["id"], {"design_refs": ["DSN-0001"]})
    approve_scope(state, pr["id"])
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    state.transition(task["id"], "READY")
    lease = dispatch.create_lease(state, task["id"])
    header = dispatch.parse_header(dispatch.dispatch_header(lease))
    assert dispatch.validate_dispatch(state, header, TSK_FIELDS["assigned_role"])


# -- analysis route (spec II.2 Buendelung; II.12 "Draft-Analyse ohne APR") -----

def _analysis_task(state, **overrides):
    """A task under an UNAPPROVED root -- the draft-analysis situation."""
    pr = state.capture("PR", dict(PR_FIELDS))
    fields = dict(TSK_FIELDS, product_requirement=pr["id"], type="analysis",
                  assigned_role="software-architect")
    fields.update(overrides)
    task = dispatch.create_task(state, fields)
    state.transition(task["id"], "READY")
    return pr, task


def _analysis_apr(state, task_ids, expires_in=3600):
    request = approvals.create_pending_request(
        state, "analysis",
        manifest={"question": "how does checkout fail?", "scope": "read-only",
                  "expected_result": "a written finding",
                  dispatch.ANALYSIS_TASKS_KEY: list(task_ids)},
        approval_expires=time.time() + expires_in)
    mint_via_hook(state, request)
    return _latest_apr(state)


def _latest_apr(state):
    names = sorted(n for n in os.listdir(os.path.join(state.root, "approvals"))
                   if n.startswith("APR-") and n.endswith(".yaml"))
    return approvals.read_apr(state, names[-1][:-5])


def test_draft_analysis_without_an_analysis_approval_blocks(state):
    _pr, task = _analysis_task(state)
    with pytest.raises(DispatchError, match="analysis"):
        dispatch.create_lease(state, task["id"])


def test_bundled_analysis_approval_covers_its_listed_tasks(state):
    _pr, task = _analysis_task(state)
    _analysis_apr(state, [task["id"]])
    lease = dispatch.create_lease(state, task["id"])
    header = dispatch.parse_header(dispatch.dispatch_header(lease))
    assert dispatch.validate_dispatch(state, header, "software-architect")


def test_an_analysis_approval_does_not_cover_an_unlisted_task(state):
    _pr, listed = _analysis_task(state)
    unlisted = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement="PR-0001",
                                                type="analysis",
                                                assigned_role="software-architect"))
    state.transition(unlisted["id"], "READY")
    _analysis_apr(state, [listed["id"]])
    with pytest.raises(DispatchError, match="analysis"):
        dispatch.create_lease(state, unlisted["id"])


def test_revoked_analysis_approval_stops_covering(state):
    _pr, task = _analysis_task(state)
    apr = _analysis_apr(state, [task["id"]])
    lease = dispatch.create_lease(state, task["id"])
    header = dispatch.parse_header(dispatch.dispatch_header(lease))
    approvals.revoke(state, apr["id"])
    with pytest.raises(DispatchError, match="analysis"):
        dispatch.validate_dispatch(state, header, "software-architect")


def test_expired_approval_blocks_dispatch(state):
    """spec II.10a: an expired routine/analysis approval blocks the dispatch."""
    _pr, task = _analysis_task(state)
    _analysis_apr(state, [task["id"]], expires_in=-1)
    with pytest.raises(DispatchError, match="analysis"):
        dispatch.create_lease(state, task["id"])


def test_editing_the_approval_file_cannot_resurrect_an_expired_approval(state):
    """The expiry is read from the HASH-COVERED manifest of the minted request, so the copy in
    the approval file is decoration. Reading it there made a lapsed standing permission one
    YAML line away from being valid again."""
    _pr, task = _analysis_task(state)
    apr = _analysis_apr(state, [task["id"]], expires_in=-1)
    path = os.path.join(state.root, "approvals", apr["id"] + ".yaml")
    forged = state._read_yaml(path)
    forged["expires"] = time.time() + 3600
    state._write_yaml_atomic(path, forged)
    with pytest.raises(DispatchError, match="analysis"):
        dispatch.create_lease(state, task["id"])


def test_editing_the_minted_manifest_breaks_provenance(state):
    """Moving the expiry where it IS hash-covered does not help either: consumed_request
    recomputes the hash from the manifest rather than comparing two stored copies."""
    _pr, task = _analysis_task(state)
    apr = _analysis_apr(state, [task["id"]], expires_in=-1)
    path = os.path.join(state.root, "approvals", "consumed", apr["request_id"] + ".yaml")
    request = state._read_yaml(path)
    request["subject_manifest"]["expires"] = time.time() + 3600
    state._write_yaml_atomic(path, request)
    with pytest.raises(DispatchError, match="analysis"):
        dispatch.create_lease(state, task["id"])


def test_unreadable_expiry_grants_nothing(state):
    _pr, task = _analysis_task(state)
    apr = _analysis_apr(state, [task["id"]])
    path = os.path.join(state.root, "approvals", "consumed", apr["request_id"] + ".yaml")
    request = state._read_yaml(path)
    request["subject_manifest"]["expires"] = "whenever"
    state._write_yaml_atomic(path, request)
    with pytest.raises(DispatchError, match="analysis"):
        dispatch.create_lease(state, task["id"])


def test_flipping_revoked_back_does_not_restore_an_approval(state):
    """Revocation is recorded by MOVING the minted request out of approvals/consumed/, so the
    boolean in the approval file is what a human reads, not what a gate trusts."""
    _pr, task = _analysis_task(state)
    apr = _analysis_apr(state, [task["id"]])
    approvals.revoke(state, apr["id"])
    path = os.path.join(state.root, "approvals", apr["id"] + ".yaml")
    forged = state._read_yaml(path)
    forged["revoked"] = False
    state._write_yaml_atomic(path, forged)
    with pytest.raises(DispatchError, match="analysis"):
        dispatch.create_lease(state, task["id"])


def test_revoking_a_scope_approval_also_blocks_via_provenance(state):
    _pr, task = make_ready_task(state)
    approvals.revoke(state, state.read_item("PR-0001")["approval_ref"])
    path = state.active_path("PR-0001")
    with pytest.raises(DispatchError):
        dispatch.create_lease(state, task["id"])
    assert os.path.exists(path)


def test_a_forged_scope_approval_on_the_root_is_refused_as_a_dispatch_error(state):
    """The root route must speak the dispatch vocabulary: an ApprovalError leaking through would
    reach the user as "internal error -- the harness is broken" instead of "this approval is not
    proven" (spec II.13 wants the remedy named)."""
    pr = state.capture("PR", dict(PR_FIELDS))
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    state.transition(task["id"], "READY")
    state._write_yaml_atomic(
        os.path.join(state.root, "approvals", "APR-0001.yaml"),
        {"id": "APR-0001", "kind": "scope", "item": pr["id"], "revision": 1,
         "subject_manifest_hash": "0" * 64, "request_id": "made-up",
         "mint_code": "000000", "approved_at": "2026-07-25T00:00:00",
         "expires": None, "revoked": False})
    path = state.active_path(pr["id"])
    item = state._read_yaml(path)
    item["approval_ref"] = "APR-0001"
    state._write_yaml_atomic(path, item)
    with pytest.raises(DispatchError, match="provenance cannot be proven"):
        dispatch.create_lease(state, task["id"])


def test_a_dispatched_tasks_work_order_is_frozen(state):
    """gate layer 3 reads `allowed_scope` from the task record, so widening it on a LEASED, BOUND
    task hands a running specialist the whole repo -- with no approval and no revision bump. The
    work-order fields are frozen outside DRAFT; re-planning has to be a visible transition."""
    _task, _lease, header = leased(state)
    task_id = header["task_id"]
    for field, value in (("allowed_scope", ["/"]), ("forbidden_scope", []),
                         ("assigned_role", "frontend-developer"), ("acceptance_refs", ["AC-9"]),
                         ("dependencies", []), ("type", "implementation")):
        with pytest.raises(Exception, match="frozen outside"):
            state.update_item(task_id, {field: value})
    assert state.read_item(task_id)["allowed_scope"] == ["src/"]


def test_a_draft_task_can_still_be_re_planned(state):
    """The freeze must not make planning impossible -- DRAFT is where re-planning belongs."""
    pr = state.capture("PR", dict(PR_FIELDS))
    approve_scope(state, pr["id"])
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    assert state.update_item(task["id"], {"allowed_scope": ["src/", "tests/"]})[
        "allowed_scope"] == ["src/", "tests/"]


def test_flags_stay_writable_on_a_dispatched_task(state):
    """`blocked_by` is a flag, not a status (spec II.2 Querregeln), and design_ref is set by the
    design-promotion path -- neither may be caught by the freeze."""
    _task, _lease, header = leased(state)
    assert state.update_item(header["task_id"], {"blocked_by": "BUG-0001"})
    assert state.update_item(header["task_id"], {"design_ref": "DSN-0001"})


def test_update_item_cannot_retype_a_task_out_of_the_design_gate(state):
    """The sanctioned edit path has to enforce the same closed vocabulary as capture -- otherwise
    an orchestrator that hits the capture-time refusal simply re-types the task afterwards."""
    header = _ui_task(state, design_ref=None)
    # an ILLEGAL value is refused by the vocabulary...
    with pytest.raises(Exception, match="unknown TSK type"):
        state.update_item(header["task_id"], {"type": "ui-implementation"})
    # ...and a vocabulary-LEGAL one by the freeze, which is the half the closed
    # vocabulary alone did not cover
    with pytest.raises(Exception, match="frozen outside"):
        state.update_item(header["task_id"], {"type": "implementation"})
    with pytest.raises(DispatchError, match="design_ref"):
        dispatch.validate_dispatch(state, header, "frontend-developer")


# -- agent binding (spike S3; the platform gives SubagentStart no join key) ----

def test_role_claim_binds_the_single_pending_dispatch(state):
    _task, _lease, header = leased(state)
    dispatch.mark_awaiting_bind(state, header["task_id"])
    bound = dispatch.bind_agent_by_role(state, "agent-abc", TSK_FIELDS["assigned_role"])
    assert bound["agent_id"] == "agent-abc"
    assert dispatch.task_for_agent(state, "agent-abc")["id"] == header["task_id"]


def test_role_claim_ignores_a_different_role(state):
    _task, _lease, header = leased(state)
    dispatch.mark_awaiting_bind(state, header["task_id"])
    with pytest.raises(dispatch.NoPendingDispatch):
        dispatch.bind_agent_by_role(state, "agent-abc", "frontend-developer")


def test_two_same_role_dispatches_refuse_to_guess(state):
    """The platform limit, made visible: SubagentStart carries no key back to the tool call, so
    two concurrent same-role dispatches cannot be told apart. Binding the wrong one would run
    one specialist under another's allowed_scope -- a silent hole in gate layer 3."""
    _pr, first = make_ready_task(state)
    second = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement="PR-0001"))
    state.transition(second["id"], "READY")
    for task_id in (first["id"], second["id"]):
        dispatch.create_lease(state, task_id)
        dispatch.mark_awaiting_bind(state, task_id)
    with pytest.raises(dispatch.AmbiguousBinding, match="refusing to"):
        dispatch.bind_agent_by_role(state, "agent-abc", TSK_FIELDS["assigned_role"])


def test_different_roles_in_parallel_bind_cleanly(state):
    """The restriction is same-role only; parallel batches across roles must keep working."""
    _pr, backend = make_ready_task(state)
    frontend = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement="PR-0001",
                                                assigned_role="frontend-developer"))
    state.transition(frontend["id"], "READY")
    for task_id in (backend["id"], frontend["id"]):
        dispatch.create_lease(state, task_id)
        dispatch.mark_awaiting_bind(state, task_id)
    assert dispatch.bind_agent_by_role(state, "a1", "backend-developer")["task_id"] == backend["id"]
    assert dispatch.bind_agent_by_role(state, "a2", "frontend-developer")["task_id"] == frontend["id"]


def test_an_expired_bind_window_is_not_claimable(state):
    """A failed spawn must not leave a slot a later, undispatched subagent can walk into."""
    _task, _lease, header = leased(state)
    dispatch.mark_awaiting_bind(state, header["task_id"])
    path = os.path.join(state.root, "tasks", "leases", header["task_id"] + ".lease.yaml")
    stale = state._read_yaml(path)
    stale["awaiting_bind_until"] = time.time() - 1
    state._write_yaml_atomic(path, stale)
    with pytest.raises(dispatch.NoPendingDispatch):
        dispatch.bind_agent_by_role(state, "agent-abc", TSK_FIELDS["assigned_role"])


def test_task_for_agent_is_none_for_an_unbound_agent(state):
    leased(state)
    assert dispatch.task_for_agent(state, "never-bound") is None
    assert dispatch.task_for_agent(state, None) is None
