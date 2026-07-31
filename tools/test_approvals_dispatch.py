"""Tests for the approval protocol + dispatch leases (HARNESS_V2_SPEC.md II.2/II.4)."""
import ast
import inspect
import os
import sys
import time

import pytest

TEAM_KITS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits")
sys.path.insert(0, TEAM_KITS)

from conftest import approve, mint_via_hook  # noqa: E402 -- ONE mint helper for the suite
from kernel import approvals, backlog_types, dispatch, staging  # noqa: E402
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
    return approve(state, item_id, "scope")



def make_ready_task(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    approve_scope(state, pr["id"])
    task = dispatch.create_task(state, dict(TSK_FIELDS, product_requirement=pr["id"]))
    state.transition(task["id"], "READY")
    return pr, state.read_item(task["id"])


# -- approval protocol ---------------------------------------------------------

def test_a_status_an_approval_commits_is_an_approved_status():
    """`approved_statuses` must not contradict its own first sentence — for ANY type.

    The property, over every (type, kind) pair in `APPROVAL_TRANSITIONS` rather than over PROC
    alone: the status an approval WALKS AN ITEM INTO is by definition a status the item stands in
    because a user approved it, so it has to be in the answer. The first cut subtracted every
    terminal and therefore dropped `ACCEPTED` from PR and RQ — the exact status an `acceptance`
    approval commits — while `PROC`, whose terminals all lie off its chain, agreed with both
    readings and hid it. Its only consumer today is the office spawn gate, so this was latent, not
    live; a check over the pairs is what keeps it that way.

    The counter-direction is asserted too, so "return every state" cannot satisfy it: a terminal
    NO approval targets stays out (`PROC` RETIRED, `BUG` VERIFIED, `CR` APPLIED, `EXP` ANALYZED),
    and a type nothing approves answers with nothing.
    """
    for (item_type, kind), (_source, target) in approvals.APPROVAL_TRANSITIONS.items():
        answer = approvals.approved_statuses(item_type)
        assert target in answer, (
            "%s %s commits %s -> %s, but %s is not an approved status of %s"
            % (item_type, kind, _source, target, target, item_type))
    for item_type, automaton in backlog_types.AUTOMATA.items():
        answer = approvals.approved_statuses(item_type)
        targets = {edge[1] for (typ, _kind), edge in approvals.APPROVAL_TRANSITIONS.items()
                   if typ == item_type}
        assert not (answer & (automaton.terminals - targets)), (
            "%s: a terminal no approval targets is not an approved status" % item_type)
        if not targets:
            assert answer == frozenset(), item_type
    assert approvals.approved_statuses("INV") == frozenset()
    assert approvals.approved_statuses("EVD") == frozenset()


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
    """A UI task under a root whose confirmed design REALLY EXISTS.

    It used to hand-write `design_refs: ["DSN-0001"]` with no such design anywhere, which is how
    `test_ui_task_with_design_ref_dispatches` proved a spawn against a dangling reference. The
    design is frozen through `staging.freeze_design` now -- the one producer of the field -- so
    what the gate is measured against is the shape the freezer writes (a state-relative path to
    the frozen revision), not a shape only this fixture ever produced.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    staging_dir = os.path.join(state.root, "staging", pr["id"])
    os.makedirs(staging_dir, exist_ok=True)
    with open(os.path.join(staging_dir, "preview.html"), "w", encoding="utf-8") as handle:
        handle.write("<html><body>design</body></html>")
    frozen = staging.freeze_design(state, pr["id"], "DSN-0001", pr["id"], "preview.html")
    approve_scope(state, pr["id"])
    fields = dict(TSK_FIELDS, product_requirement=pr["id"], type="ui",
                  assigned_role="frontend-developer")
    fields.update(overrides)
    if fields.get("design_ref") == "DSN-0001":
        # the task references what the freezer actually wrote, not the bare id
        fields["design_ref"] = frozen["root"]["design_refs"][0]
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
    """spec II.10a: an expired ANALYSIS approval blocks the dispatch.

    "routine/analysis" is what this said, and only the analysis half is built: `routine` is not a
    dispatch route at all (`ROOT_DISPATCH_KINDS` is scope/delivery, `_covering_analysis_apr` reads
    `kind == "analysis"`), so no test here could have covered it. The routine route is an open
    disposition row, not something this assertion measures.
    """
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


# -- the transition gate: an edge an approval COMMITS is that approval's to walk ----------------

def _gated_edges():
    """{(item type, from, to) -> kinds} for every edge some approval kind commits.

    Read out of `APPROVAL_TRANSITIONS` here as well, because the tests below need the SUBJECTS,
    not a second opinion about them. What is not tautological is what each test then does with an
    edge -- build a real item, walk it, and see the kernel refuse or allow.
    """
    edges = {}
    for (item_type, kind), edge in approvals.APPROVAL_TRANSITIONS.items():
        edges.setdefault((item_type,) + edge, set()).add(kind)
    return edges


def test_a_root_item_cannot_leave_its_initial_status_without_the_users_approval(state):
    """The measured hole: `transition PR-0002 APPROVED` walked a root item out of DRAFT.

    HOW WIDE THE NET UNDER THIS GATE IS, measured so the next reader does not overestimate it:
    stubbing `assert_transition_approved` to `return None` turns FOUR tests red, all in this
    module. `test_state`, `test_report`, `test_e2e` and `test_staging_cli` stay green, because
    `conftest.walk_to_status` mints on every gated edge and therefore never depends on the refusal.
    That is the correct behaviour for a fixture -- it walks the sanctioned route -- and it does
    mean the gate's proof lives here and in the two scaffolded acceptance tests, nowhere else.

    `gate_git` refuses a merge for an item still in its initial status BECAUSE nothing has
    approved the work, so a status the supervised party can set itself was a value that gate had
    no business reading. The refusal names the kind, the item and the revision, because a role
    that hits it has to know which approval to ask for.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    with pytest.raises(ApprovalError) as refused:
        state.transition(pr["id"], "APPROVED")
    message = str(refused.value)
    assert "scope" in message and pr["id"] in message and "revision 1" in message, message
    assert state.read_item(pr["id"])["status"] == "DRAFT"


def test_the_gated_edges_are_exactly_the_ones_the_mint_walks(state):
    """WHICH edges are gated, pinned as an answer rather than derived twice.

    The derivation itself (`required_approval_kinds` inverts `APPROVAL_TRANSITIONS`) cannot fail a
    test written from the same map, so what is asserted is the four CONSEQUENCES the review asked
    about by name. Each is a live decision, and the day one changes this test is where the change
    has to be made deliberately:

      * the TSK middle rides on leases and `submit-result`, never on an approval -- so no edge of
        the TSK automaton is gated, and the retry rule stays a caller argument;
      * `SR` (PROPOSED -> ACCEPTED) is NOT gated, and that is the finding rather than the design:
        accepting a technical contract under a root looks like something a user should sign, but
        no APR kind has a manifest that describes an SR. Gating it needs a KIND first, which is a
        spec decision;
      * a terminal edge (REJECTED / SUPERSEDED / CANCELLED / DUPLICATE / ABORTED / MERGED /
        CONVERTED / RETIRED) is never gated -- abandoning work is not approving it. The cost is
        named where a role reads it: the supervised party can still drop a requirement;
      * `DEC`/`INV` have no automaton at all, so the question never reaches the approval check.
    """
    gated = set(_gated_edges())
    for item_type, automaton in backlog_types.AUTOMATA.items():
        for source, target in sorted(automaton.allowed):
            kinds = approvals.required_approval_kinds(item_type, source, target)
            assert bool(kinds) == ((item_type, source, target) in gated)
            if item_type == "TSK":
                assert not kinds, "a TSK edge became approval-bound: %s -> %s" % (source, target)
            if target in automaton.terminals and target != "ACCEPTED":
                assert not kinds, (
                    "%s %s -> %s is a terminal edge and is now gated -- abandoning work is not "
                    "approving it, and an item that cannot be abandoned is the other failure"
                    % (item_type, source, target))
    assert not approvals.required_approval_kinds("SR", "PROPOSED", "ACCEPTED"), (
        "SR acceptance became approval-bound -- if an APR kind now describes an SR, delete this "
        "assertion and say so in the docstring above")
    for item_type in ("DEC", "INV"):
        assert item_type not in backlog_types.AUTOMATA


def _apr_of_kind(state, item_id, kind):
    directory = os.path.join(state.root, "approvals")
    for name in sorted(os.listdir(directory)):
        if name.startswith("APR-") and name.endswith(".yaml"):
            apr = state._read_yaml(os.path.join(directory, name))
            if apr.get("item") == item_id and apr.get("kind") == kind:
                return apr
    raise AssertionError("no %s approval for %s" % (kind, item_id))


def _delivery_then_scope(state):
    """A PR that is APPROVED and carries a valid, unused DELIVERY approval at revision 1.

    WHY THE ORDER IS THIS WAY ROUND, because it looks odd and is the honest answer to "show the
    gate letting a legitimate transition through". A mint WALKS the edge it commits, so a scope
    approval and a PR still in DRAFT cannot coexist -- the moment the scope APR exists the item is
    already APPROVED, and the automaton, not the approval check, is what answers
    `transition PR-0001 APPROVED`. A delivery approval minted while the item is still DRAFT has no
    status effect (its source is APPROVED), so it is the one way to hold a valid approval for an
    edge nobody has walked yet. Everything downstream of that -- valid, revoked, edited -- is then
    measurable on a real transition.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    mint_via_hook(state, approvals.create_pending_request(state, "delivery", pr["id"]))
    assert state.read_item(pr["id"])["status"] == "DRAFT"
    approve_scope(state, pr["id"])
    assert state.read_item(pr["id"])["status"] == "APPROVED"
    return pr, _apr_of_kind(state, pr["id"], "delivery")


def test_a_valid_approval_lets_the_gated_edge_through(state):
    pr, _apr = _delivery_then_scope(state)
    assert state.transition(pr["id"], "IN_DELIVERY")["status"] == "IN_DELIVERY"


def test_a_revoked_approval_does_not_authorise_the_transition(state):
    """BOTH halves of a revocation, because `revoke` writes two things and only one is the proof.

    A full `revoke` MOVES the minted request out of `approvals/consumed/`, so the provenance check
    refuses before the flag is ever read -- which is exactly why `revoke` writes the flag first:
    its own docstring records that a crash between the two writes can leave the flag WITHOUT the
    move, never the move without the flag. So the second half here is that crash state, written by
    hand: flag set, request still consumed. Without it, deleting the flag check entirely left this
    test green (mutation-measured), i.e. the flag branch was asserted by nothing.
    """
    pr, apr = _delivery_then_scope(state)
    approvals.revoke(state, apr["id"])
    with pytest.raises(ApprovalError, match="revoked|REVOKED"):
        state.transition(pr["id"], "IN_DELIVERY")
    assert state.read_item(pr["id"])["status"] == "APPROVED"

    second, other = _delivery_then_scope(state)
    path = os.path.join(state.root, "approvals", other["id"] + ".yaml")
    record = state._read_yaml(path)
    record["revoked"] = True                       # the crash window: flag written, move pending
    state._write_yaml_atomic(path, record)
    with pytest.raises(ApprovalError, match="is revoked"):
        state.transition(second["id"], "IN_DELIVERY")
    assert state.read_item(second["id"])["status"] == "APPROVED"


def test_an_out_of_band_edit_closes_the_gated_edge(state):
    """The hash is recomputed from the item's CURRENT content, so an IDE edit shuts the door.

    `risks` rather than `goal`, because the delivery manifest is what this approval hashes and
    `goal` is not in it -- editing a field the approval does not cover would prove the check runs
    on the wrong manifest and still pass.
    """
    pr, _apr = _delivery_then_scope(state)
    path = state.active_path(pr["id"])
    item = state._read_yaml(path)
    item["risks"] = ["a risk nobody approved"]
    state._write_yaml_atomic(path, item)
    with pytest.raises(ApprovalError, match="out-of-band"):
        state.transition(pr["id"], "IN_DELIVERY")


def test_an_expiring_approval_kind_cannot_even_be_created_for_a_gated_edge(state):
    """"Expired" is unreachable for the gated kinds, BY CONSTRUCTION -- so it is pinned, not faked.

    Spec II.2 time-boxes `routine`/`analysis`/`push` and content-invalidates `scope`/`delivery`/
    `acceptance`; `create_pending_request` refuses an expiry on the second group, and no
    (item type, expiring kind) pair exists in `APPROVAL_TRANSITIONS`. So the expiry branch in
    `assert_apr_in_force` is dead for transitions and live for dispatch, which is where
    `routine`/`analysis` approvals actually authorise something. Asserted rather than explained:
    the day a gated edge gets an expiring kind, this goes red and that branch needs a test of its
    own on the transition path too.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    for kinds in _gated_edges().values():
        assert not (kinds & approvals.EXPIRING_KINDS), kinds
    with pytest.raises(ApprovalError, match="carry an expiry"):
        approvals.create_pending_request(state, "scope", pr["id"],
                                         approval_expires=time.time() + 60)


def test_no_optional_argument_of_transition_can_skip_the_approval_check(state):
    """Spec II.4: bootstrap "ist kein Config-Flag (der Lead koennte sein eigenes Gate umgehen)".

    Derived from the SIGNATURE, not from a list of forbidden names: every optional parameter of
    both transition entry points is tried with truthy and falsy values, and the gated edge has to
    stay refused for all of them. A `force=`/`bootstrap=`/`skip_approval=` added later is caught
    the day it is added, whatever it is called -- a test that matched names would only catch the
    names somebody had already thought of.

    A VARIADIC PARAMETER IS ITSELF THE DEFECT, and that half was missing: with
    `(self, item_id, to_status, approved_retry=False, **kwargs)` the loop above enumerates nothing
    new, so `bootstrap=True` reached the body and moved the item -- measured. A `*args`/`**kwargs`
    on a gate entry point means the surface cannot be enumerated at all, so it is refused outright
    rather than probed.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    for entry in (ProjectState.transition, ProjectState._transition_locked):
        parameters = inspect.signature(entry).parameters
        variadic = [name for name, parameter in parameters.items()
                    if parameter.kind in (inspect.Parameter.VAR_KEYWORD,
                                          inspect.Parameter.VAR_POSITIONAL)]
        assert not variadic, (
            "%s takes %s -- a gate entry point whose arguments cannot be enumerated cannot be "
            "proven free of a bypass, and this test would silently stop covering the new ones"
            % (entry.__qualname__, variadic))
        optional = [name for name, parameter in parameters.items()
                    if parameter.default is not inspect.Parameter.empty]
        assert optional, "%s has no optional parameter -- the loop below asserts nothing" % entry
        for name in optional:
            for value in (True, 1, "yes", False, None):
                with pytest.raises(ApprovalError):
                    state.transition(pr["id"], "APPROVED", **{name: value})


def _possible_statuses(node):
    """Every status an assignment expression can produce, or None when that cannot be bounded.

    FOUR SHAPES, and each one's values come from the kernel map that produces them rather than
    from a list here: a string literal; a conditional between two of them (`submit_result`); a
    call to `initial_status` / `invalidation_target`; a lookup in `_NON_AUTOMATON_INITIAL_STATUS`.
    Anything else is None, which the caller reports -- fail-closed, because the shape this whole
    check exists for (`item["status"] = transition[1]` in the old `mint`) is exactly an expression
    a reader cannot bound.
    """
    from kernel.backlog_types import AUTOMATA, INVALIDATION_TARGET
    from kernel.state import _NON_AUTOMATON_INITIAL_STATUS

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {node.value}
    if isinstance(node, ast.IfExp):
        left, right = _possible_statuses(node.body), _possible_statuses(node.orelse)
        return None if left is None or right is None else left | right
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "initial_status":
            return {automaton.chain[0] for automaton in AUTOMATA.values()}
        if node.func.id == "invalidation_target":
            return set(INVALIDATION_TARGET.values())
    if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
            and node.value.id == "_NON_AUTOMATON_INITIAL_STATUS"):
        return set(_NON_AUTOMATON_INITIAL_STATUS.values())
    return None


def _persisted_names(tree, function_name):
    """The local names a function PERSISTS as an item file, i.e. hands to `_write_yaml_atomic`.

    THE SUBJECT FILTER, and without it the reader below is unusable rather than merely narrow.
    "Can this expression write a `status` key" has no sound AST answer for a computed key or an
    opaque merge -- but the question that matters is narrower: can it write the status of a
    MAPPING THAT BECOMES AN ITEM FILE. That is decidable: the payload of `_write_yaml_atomic` is
    exactly the mapping that lands on disk, so a merge into anything else (a hashlib digest, a
    field-contract dict, a capability matrix) is not this check's business. Flagging those made
    the first cut report 31 sites, all noise -- a check nobody can keep green protects nothing.
    """
    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef) and node.name == function_name):
            continue
        names = set()
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Call):
                continue
            called = getattr(inner.func, "attr", getattr(inner.func, "id", ""))
            # EVERY ROUTE INTO THE STORE, not just the one spelled `_write_yaml_atomic(p, item)`.
            # Two blind spots were measured: a payload that is not a bare name
            # (`_write_yaml_atomic(p, dict(item))`, `(p, {**item})`) and a mapping handed to
            # `capture`/`update_item`, which is what `dispatch.create_task` does after
            # `task_fields.update(...)`. Any Name INSIDE the argument counts, because that is the
            # mapping whose contents end up on disk.
            if called not in ("_write_yaml_atomic", "capture", "update_item",
                              "_update_item_locked"):
                continue
            for argument in inner.args[1:] if called == "_write_yaml_atomic" else inner.args:
                for part in ast.walk(argument):
                    if isinstance(part, ast.Name):
                        names.add(part.id)
        return names
    return set()


_UNREADABLE_KEY = object()


def _module_string_constants(tree):
    """{name: value} for module-level `NAME = "literal"` bindings that hold ONE string, always.

    A subscript key spelled as such a constant is as readable as a quoted one -- `item[FIELD] = x`
    where `FIELD = "approved_hash"` writes `approved_hash` and nothing else -- and reading it is
    what keeps the kernel free to name its own field constants instead of retyping the string at
    every write site. A name that is ever bound to something else, or to two different strings, is
    left out: "I can see one of its values" is not the same as "I know what it is", and the whole
    point of the reader below is that the second answer is the only safe one.
    """
    values, rejected = {}, set()
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
                rejected.add(target.id)
            elif values.setdefault(target.id, node.value.value) != node.value.value:
                rejected.add(target.id)
    return {name: value for name, value in values.items() if name not in rejected}


def _status_writes(tree):
    """(function name, value node or None) for every expression that can SET an ITEM's `status`.

    THE READER IS FAIL-CLOSED IN BOTH DIRECTIONS, and it was not. It first read only
    `x["status"] = ...`, so `x.update({"status": "APPROVED"})` walked past it (mutation-measured
    green). Widening it to three syntaxes fixed that case and left the SHAPE of the defect: an
    unbounded VALUE was an offender while an unreadable FORM was silence -- so `i |= {...}`, a
    computed key, and `i.update(changes)` (which is in the running kernel) reported nothing.

    Now a form this reader cannot bound yields `(where, None)`, exactly like a value it cannot
    bound. What it reads:
      * a subscript assignment whose key can be READ -- a string literal, or a module constant
        bound to exactly one string (`_module_string_constants`) -> the value node. Any receiver:
        the key is visible, so the value is the only open question.
      * `.update({...})` / `dict(..., status=...)` naming the key -> the value node.
      * on a PERSISTED receiver only (`_persisted_names`): a subscript assignment with a computed
        key, an `.update(<not a dict literal>)`, and an augmented `|=` -> None.
    A sixth spelling would still be missed, which is why the test below parses a sample of each
    and fails when one stops being recognised: a reader that quietly narrows is the failure mode.
    """
    holder = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for inner in ast.walk(node):
                holder[inner] = node.name
    persisted = {name: _persisted_names(tree, name) for name in set(holder.values())}
    constants = _module_string_constants(tree)
    found = []

    def persisted_receiver(node, where):
        return isinstance(node, ast.Name) and node.id in persisted.get(where, set())

    def written_key(slice_node):
        if isinstance(slice_node, ast.Constant):
            return slice_node.value
        if isinstance(slice_node, ast.Name) and slice_node.id in constants:
            return constants[slice_node.id]
        return _UNREADABLE_KEY

    for node in ast.walk(tree):
        where = holder.get(node, "<module>")
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if not isinstance(target, ast.Subscript):
                    continue
                key = written_key(target.slice)
                if key is not _UNREADABLE_KEY:
                    if key == "status":
                        found.append((where, node.value))
                elif persisted_receiver(target.value, where):
                    found.append((where, None))      # a computed key may be "status"
        elif isinstance(node, ast.AugAssign) and isinstance(node.op, ast.BitOr):
            if persisted_receiver(node.target, where):
                found.append((where, None))          # `item |= {...}` merges an unread mapping
        elif isinstance(node, ast.Call):
            named = (node.func.attr if isinstance(node.func, ast.Attribute)
                     else getattr(node.func, "id", ""))
            if named not in ("update", "dict"):
                continue
            for keyword in node.keywords:
                if keyword.arg == "status":
                    found.append((where, keyword.value))
            for argument in node.args:
                if isinstance(argument, ast.Dict):
                    for key, value in zip(argument.keys, argument.values):
                        if isinstance(key, ast.Constant) and key.value == "status":
                            found.append((where, value))
                elif (named == "update" and isinstance(node.func, ast.Attribute)
                        and persisted_receiver(node.func.value, where)):
                    found.append((where, None))      # merges a mapping this reader cannot read
    return found


def _collections_with_the_key(tree):
    """Module-level names bound to a literal collection that contains "status"."""
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, (ast.Tuple, ast.List, ast.Set)):
            continue
        if any(isinstance(element, ast.Constant) and element.value == "status"
               for element in node.value.elts):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
    return names


def _refuses_the_key(tree, function_name):
    """Does this function REFUSE a `status` in its input before it writes anything?

    The one sanctioned answer to an unreadable form, and it is a property rather than a name: a
    function that raises after testing its input against a collection containing "status" cannot
    write one however opaquely it merges. Two shapes of that test are read, because the kernel
    uses both -- a literal tuple in the comparison (`_update_item_locked`) and a module constant
    iterated over (`capture`, over `_KERNEL_SET`) -- and the constant is RESOLVED rather than
    named, so a renamed constant keeps working and an emptied one stops.

    Without this, the check could only be satisfied by editing the kernel into a shape an AST
    likes, which is the tail wagging the dog; with it, a function that drops its guard becomes an
    offender the same day.
    """
    holders = _collections_with_the_key(tree)

    def tests_the_key(node):
        """Does this expression test something against a collection containing "status"?"""
        for inner in ast.walk(node):
            sources = []
            if isinstance(inner, ast.Compare):
                sources = list(inner.comparators)
            elif isinstance(inner, ast.comprehension):
                sources = [inner.iter]
            for source in sources:
                if isinstance(source, ast.Name) and source.id in holders:
                    return True
                if isinstance(source, (ast.Tuple, ast.List, ast.Set)) and any(
                        isinstance(element, ast.Constant) and element.value == "status"
                        for element in source.elts):
                    return True
        return False

    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef) and node.name == function_name):
            continue
        # THE RAISE HAS TO HANG ON THE TEST, which the first version did not require: it asked for
        # a `raise` SOMEWHERE and a membership test SOMEWHERE, so an unrelated
        # `raise ValueError("empty")` beside an unrelated comprehension over the constant made an
        # opaque writer look guarded -- measured, and it suppressed a real offender. Now the `if`
        # itself has to be the guard: either its condition tests the key, or its condition names a
        # local that was computed from such a test, and its body has to raise.
        assigned = {target.id: statement.value
                    for statement in ast.walk(node) if isinstance(statement, ast.Assign)
                    for target in statement.targets if isinstance(target, ast.Name)}
        for branch in ast.walk(node):
            if not isinstance(branch, ast.If):
                continue
            if not any(isinstance(inner, ast.Raise) for inner in ast.walk(branch)):
                continue
            if tests_the_key(branch.test):
                return True
            for inner in ast.walk(branch.test):
                if (isinstance(inner, ast.Name) and inner.id in assigned
                        and tests_the_key(assigned[inner.id])):
                    return True
        return False
    return False


def test_the_reader_that_finds_direct_status_writes_sees_every_shape_it_claims_to():
    """The reader below is only worth its floor if it does not silently narrow.

    Each sample is one syntax Python offers for setting the key, and each has to be FOUND with its
    value bounded. The subscript-only version of this reader passed the whole suite while
    `task.update({"status": "APPROVED"})` was invisible to it -- so the reader gets its own test,
    ahead of the check that depends on it.
    """
    bounded = {
        "subscript": 'def f(i):\n    i["status"] = "APPROVED"\n',
        # a module constant as the key is as readable as the quoted string, and the kernel writes
        # its own fields that way (`approvals.APPROVED_CONTENT_HASH_FIELD`) — so it must be READ,
        # not counted as an unbounded computed key. Both directions matter and both are here: this
        # one resolves to `status`, and the `constant_key_elsewhere` sample below resolves to a
        # different field and is therefore not a status write at all.
        "constant_key": 'K = "status"\ndef f(i):\n    i[K] = "APPROVED"\n',
        "update_dict": 'def f(i):\n    i.update({"status": "APPROVED"})\n',
        "update_keyword": 'def f(i):\n    i.update(status="APPROVED")\n',
        "dict_keyword": 'def f(i):\n    j = dict(i, status="APPROVED")\n',
    }
    for name, source in bounded.items():
        writes = _status_writes(ast.parse(source))
        assert len(writes) == 1, "%s: the reader found %d writes" % (name, len(writes))
        assert _possible_statuses(writes[0][1]) == {"APPROVED"}, name
    # ...and the forms it CANNOT bound have to surface as unbounded rather than as nothing: the
    # asymmetry between "value I cannot read" (offender) and "form I cannot read" (silence) is
    # what let `i.update(changes)`, `i |= {...}` and a computed key past this reader entirely.
    # ...on a PERSISTED receiver, which is the subject filter: the same shapes on a hashlib
    # digest or a field-contract dict are not this check's business (see `_persisted_names`).
    persist = '    s._write_yaml_atomic(p, i)\n'
    unbounded = {
        "update_variable": 'def f(i, c, s, p):\n    i.update(c)\n' + persist,
        "aug_or": 'def f(i, c, s, p):\n    i |= c\n' + persist,
        "computed_key": 'def f(i, k, s, p):\n    i[k] = "APPROVED"\n' + persist,
    }
    for name, source in unbounded.items():
        writes = _status_writes(ast.parse(source))
        assert len(writes) == 1, "%s: the reader found %d writes" % (name, len(writes))
        assert _possible_statuses(writes[0][1]) is None, name
    assert not _status_writes(ast.parse('def f(i):\n    i["title"] = "APPROVED"\n'))
    # a constant key that names ANOTHER field is not a status write...
    assert not _status_writes(ast.parse(
        'K = "approved_hash"\ndef f(i):\n    i[K] = "x"\n')), "constant_key_elsewhere"
    # ...and a name the module rebinds is not readable at all, so it stays an unbounded write on a
    # persisted receiver rather than resolving to whichever binding this reader happened to see
    rebound = ('K = "approved_hash"\nK = "status"\n'
               'def f(i, s, p):\n    i[K] = "x"\n' + persist)
    assert _status_writes(ast.parse(rebound)) == [("f", None)], "rebound module constant"
    # the guard that makes an unreadable merge provably safe, and its absence
    guarded = ('def g(c, i):\n'
               '    bad = [k for k in c if k in ("id", "status")]\n'
               '    if bad:\n        raise ValueError(bad)\n'
               '    i.update(c)\n')
    assert _refuses_the_key(ast.parse(guarded), "g")
    # ...and through a module constant, which is how `capture` spells the same guard
    via_constant = ('KEYS = ("id", "status")\n'
                    'def g(c, i):\n'
                    '    bad = [k for k in KEYS if k in c]\n'
                    '    if bad:\n        raise ValueError(bad)\n'
                    '    i.update(c)\n')
    assert _refuses_the_key(ast.parse(via_constant), "g")
    # ...and an unrelated raise beside an unrelated membership test is NOT a guard: that shape
    # made an opaque writer look protected while nothing connected the two.
    unrelated = ('KEYS = ("id", "status")\n'
                 'def g(c, i):\n'
                 '    if not c:\n        raise ValueError("empty")\n'
                 '    noise = [k for k in KEYS]\n'
                 '    i.update(c)\n')
    assert not _refuses_the_key(ast.parse(unrelated), "g")
    assert not _refuses_the_key(ast.parse('def g(c, i):\n    i.update(c)\n'), "g")


def test_no_direct_status_write_can_produce_a_status_an_approval_commits():
    """Every `x["status"] = ...` in the kernel, and what it is allowed to be.

    The kernel used to claim `transition` was its only status writer while `approvals.mint` and
    several dispatch and state functions wrote one directly. Rather than repeat a claim, this
    reads the running source: `_status_writes` finds every expression outside `_transition_locked`
    that can set the key (three syntaxes, self-tested above), `_possible_statuses` BOUNDS what each
    can produce from the kernel's own maps, and an expression nobody can bound is itself a failure
    -- that was exactly the old mint's shape.

    So a new direct writer is not forbidden; a direct writer that could produce APPROVED,
    IN_DELIVERY or ACCEPTED is, and so is one nobody can bound.
    """
    destinations = {}
    for (item_type, _kind), (_source, target) in approvals.APPROVAL_TRANSITIONS.items():
        destinations.setdefault(target, set()).add(item_type)
    kernel_dir = os.path.join(TEAM_KITS, "kernel")
    offenders, writers = [], []
    for name in sorted(os.listdir(kernel_dir)):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(kernel_dir, name), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        for function, value_node in _status_writes(tree):
            where = "%s:%s" % (name, function)
            if where == "state.py:_transition_locked":
                continue
            writers.append(where)
            produced = _possible_statuses(value_node)
            if produced is None:
                if _refuses_the_key(tree, function):
                    continue      # it raises on a `status` in its input before it merges anything
                offenders.append(
                    "%s writes a status this reader cannot bound -- bound it (add the shape to "
                    "`_possible_statuses`, with the kernel map it reads its values from), refuse "
                    "the key first, or route the write through the automaton" % where)
                continue
            for value in sorted(produced):
                owners = {item_type for item_type, automaton in backlog_types.AUTOMATA.items()
                          if value in automaton.states}
                clash = owners & destinations.get(value, set())
                if clash:
                    offenders.append("%s can write %r directly, which an approval commits "
                                     "for %s" % (where, value, sorted(clash)))
    # A FLOOR THAT IS NOT A MAGIC NUMBER: the reader must have seen the two modules that really do
    # write statuses. The COUNT is deliberately not asserted -- a docstring said four while the
    # source had seven, and pinning the number here would only re-create that lie one layer down.
    assert {where.split(":")[0] for where in writers} >= {"state.py", "dispatch.py"}, writers
    assert not offenders, offenders
