"""Tests for session brief, state validator and doctor (spec II.4/II.5, step 1.4c)."""
import json
import os
import subprocess
import sys

import pytest
import yaml

TEAM_KITS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits")
sys.path.insert(0, TEAM_KITS)

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


def mint_via_hook(state, request):
    """Mint through the REAL PostToolUse approval hook — the only caller the kernel accepts.

    `mint` refuses every other caller (user condition (i)): it is a plain function, so anything
    that can read `approvals/pending/<id>.yaml` could otherwise pass the label it found there and
    manufacture a user approval.
    """
    repo = os.path.dirname(state.root)
    question = approvals.build_question(request)
    payload = {
        "hook_event_name": "PostToolUse", "tool_name": "AskUserQuestion", "cwd": repo,
        "tool_input": {"questions": [question]},
        "tool_response": {"answers": {
            question["question"]: approvals.approve_label(request["mint_code"])},
            "questions": [question]},
    }
    env = dict(os.environ, CLAUDE_PROJECT_DIR=repo, HARNESS_KERNEL_PATH=TEAM_KITS)
    result = subprocess.run(
        [sys.executable, os.path.join(TEAM_KITS, "dev-team", "hooks", "gate_approval.py")],
        input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=120)
    assert result.returncode == 0 and "recorded for" in result.stderr, result.stderr


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
    mint_via_hook(state, request)
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
    mint_via_hook(state, request)
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


# -- step 7: the graph duties the validator owns (spec II.4 gate 4) -----------

RQ_FIELDS = {
    "title": "Retry semantics", "class": "research", "question": "How long should retries wait?",
    "motivation": "Throughput drops under load", "acceptance_criteria": ["measured"],
    "out_of_scope": ["ui"], "priority": "high",
}


def make_bug(state, root_id):
    return state.capture("BUG", {
        "title": "b", "related_pr": root_id, "observed": "o", "expected": "e", "repro": "r",
        "severity": "low", "acceptance_criteria": ["fixed"]})


def make_task(state, root_id, origin_id):
    root = state.read_item(root_id)
    return state.capture("TSK", {
        "product_requirement": root_id, "root_revision": root.get("revision"),
        "derives_from": [origin_id], "type": "bugfix", "assigned_role": "backend-developer",
        "acceptance_refs": ["AC-1"], "required_inputs": [], "allowed_scope": ["src/**"],
        "forbidden_scope": [], "expected_outputs": ["patch"], "dependencies": []})


def warnings_of(findings):
    return [f for f in findings if f["severity"] == "warning"]


def test_a_modified_consumed_request_is_detected(state, tmp_path):
    """The ONE forgery `consumed_request` cannot detect arithmetically: the hash function is
    public, so a consistently re-hashed request verifies. It cannot hide from git — a minted
    request is immutable once written, and `approvals/**` is committed, so any diff on it IS the
    tampering. That turns the documented residual from "undetectable" into "detected at the next
    validate or merge"."""
    repo = os.path.dirname(state.root)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=60)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    item = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", item_id=item["id"])
    mint_via_hook(state, request)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, timeout=60)
    subprocess.run(["git", "commit", "-qm", "state"], cwd=repo, check=True, timeout=60)
    assert errors(report.validate_state(state)) == []

    consumed = os.path.join(state.root, "approvals", "consumed")
    name = sorted(os.listdir(consumed))[0]
    path = os.path.join(consumed, name)
    body = open(path, encoding="utf-8").read()
    open(path, "w", encoding="utf-8", newline="\n").write(body + "\ntampered: true\n")
    found = errors(report.validate_state(state))
    assert any("MODIFIED after it was minted" in f["message"] for f in found), found


def test_a_repo_without_git_says_nothing_about_consumed_requests(state):
    """The rule can only speak about files git is tracking — it must not turn "no git here" into
    a finding, or every scratch project would fail validation."""
    item = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", item_id=item["id"])
    mint_via_hook(state, request)
    assert errors(report.validate_state(state)) == []


def test_a_displayed_expiry_that_disagrees_with_the_request_is_an_error(state):
    """The APR copy is a DISPLAY value; the gate reads expiry only from the hash-covered manifest.
    When the two disagree a human reads a validity the gate correctly refuses — or believes an
    approval is still live when it is not."""
    item = state.capture("PR", dict(PR_FIELDS))
    request = approvals.create_pending_request(state, "scope", item_id=item["id"])
    mint_via_hook(state, request)
    assert errors(report.validate_state(state)) == []
    apr_ref = state.read_item(item["id"])["approval_ref"]
    apr_path = os.path.join(state.root, "approvals", apr_ref + ".yaml")
    apr = yaml.safe_load(open(apr_path, encoding="utf-8"))
    apr["expires"] = 99999999999.0
    with open(apr_path, "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump(apr, fh, sort_keys=False, allow_unicode=True)
    found = errors(report.validate_state(state))
    assert any("hash-covered request says" in f["message"] for f in found), found


def test_a_task_deriving_from_another_roots_tree_is_an_error(state):
    """The dispatch gate resolves `acceptance_refs` against the ORIGIN, so an origin belonging to
    an unrelated root lets a task be judged against borrowed criteria. Authorisation is unaffected
    — that comes only from the root's approval — which is exactly why the mislabel survives the
    hot path and has to be caught by the graph walk."""
    root_a = state.capture("PR", dict(PR_FIELDS))
    root_b = state.capture("PR", dict(PR_FIELDS, title="Other root"))
    bug = make_bug(state, root_b["id"])
    task = make_task(state, root_a["id"], bug["id"])
    found = errors(report.validate_state(state))
    assert any(f["item"] == task["id"] and "belongs to" in f["message"] for f in found), found


def test_a_task_deriving_from_its_own_roots_tree_is_fine(state):
    """The counterpart, so the rule cannot decay into "no task may derive from anything"."""
    root = state.capture("PR", dict(PR_FIELDS))
    bug = make_bug(state, root["id"])
    make_task(state, root["id"], bug["id"])
    assert errors(report.validate_state(state)) == []


def test_a_task_deriving_from_a_terminal_origin_is_flagged(state):
    """A task deriving from a REJECTED bug is stale: its criteria left the active context."""
    root = state.capture("PR", dict(PR_FIELDS))
    bug = make_bug(state, root["id"])
    task = make_task(state, root["id"], bug["id"])
    state.transition(bug["id"], "REJECTED")
    found = warnings_of(report.validate_state(state))
    assert any(f["item"] == task["id"] and "terminal" in f["message"] for f in found), found


def test_an_analyzed_experiment_without_evidence_is_incomplete(state):
    """R7 / parity row 84: "Report pro EXP sofort nach PASS; sonst incomplete." Without it the
    research loop can close an experiment whose result exists only in a chat message."""
    root = state.capture("RQ", dict(RQ_FIELDS))
    hyp = state.capture("HYP", {"statement": "s", "derives_from": root["id"],
                                "testable_prediction": "p"})
    exp = state.capture("EXP", {"derives_from": hyp["id"], "design": "d",
                                "variables": "v", "success_criteria": "c", "evidence_refs": []})
    for target in ("APPROVED", "RUNNING", "COMPLETED", "ANALYZED"):
        state.transition(exp["id"], target)
    found = errors(report.validate_state(state))
    assert any(f["item"] == exp["id"] and "ANALYZED without evidence_refs" in f["message"]
               for f in found), found


def test_a_decision_with_invalidation_triggers_asks_for_a_recheck(state):
    """R8 / parity row 87. A WARNING deliberately: whether a trigger actually FIRED is a judgement
    no pattern can make, and the user's "maximal härten" decision says heuristics warn and never
    fail closed."""
    state.capture("DEC", {"title": "d", "context": "c", "decision": "use X",
                          "consequences": "y", "source": "adr",
                          "premise_invalidation_triggers": ["throughput above 1k/s"]})
    item = state.capture("PR", dict(PR_FIELDS))
    state.transition(item["id"], "APPROVED")
    found = warnings_of(report.validate_state(state))
    assert any("premise re-check" in f["message"] for f in found), found


def test_recording_the_recheck_clears_it(state):
    """...and recording the outcome — even "nothing changed" — is what clears it. A warning with
    no way to satisfy it is noise, and noise gets filtered out."""
    dec = state.capture("DEC", {"title": "d", "context": "c", "decision": "use X",
                                "consequences": "y", "source": "adr",
                                "premise_invalidation_triggers": ["throughput above 1k/s"]})
    item = state.capture("PR", dict(PR_FIELDS))
    state.transition(item["id"], "APPROVED")
    state.update_item(item["id"], {"premise_rechecks": [dec["id"]]})
    found = warnings_of(report.validate_state(state))
    assert not [f for f in found if "premise re-check" in f["message"]], found


def test_a_second_user_visible_slice_may_not_enter_delivery(state):
    """R12 / parity row 107, the 4-slices incident. The point of the sequence rule is that the
    user SEES a slice before the next is built on its assumptions."""
    first = state.capture("PR", dict(PR_FIELDS))
    second = state.capture("PR", dict(PR_FIELDS, title="Second slice"))
    for target in ("APPROVED", "IN_DELIVERY", "DELIVERED"):
        state.transition(first["id"], target)
    for target in ("APPROVED", "IN_DELIVERY"):
        state.transition(second["id"], target)
    found = errors(report.validate_state(state))
    assert any(f["item"] == second["id"] and "not yet ACCEPTED" in f["message"]
               for f in found), found


def test_a_technical_enabler_may_run_alongside(state):
    """The rule is about USER-VISIBLE slices: a technical enabler shows the user nothing, so
    holding it back buys nothing and would stall the work that unblocks the review."""
    first = state.capture("PR", dict(PR_FIELDS))
    enabler = state.capture("PR", dict(PR_FIELDS, title="Build pipeline",
                                       **{"class": "technical_enabler"}))
    for target in ("APPROVED", "IN_DELIVERY", "DELIVERED"):
        state.transition(first["id"], target)
    for target in ("APPROVED", "IN_DELIVERY"):
        state.transition(enabler["id"], target)
    found = errors(report.validate_state(state))
    assert not [f for f in found if "not yet ACCEPTED" in f["message"]], found
