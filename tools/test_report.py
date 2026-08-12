"""Tests for session brief, state validator and doctor (spec II.4/II.5, step 1.4c)."""
import json
import os
import re
import subprocess
import sys
import time

import pytest
import yaml

TEAM_KITS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits")
sys.path.insert(0, TEAM_KITS)

from conftest import mint_via_hook, walk_to_status  # noqa: E402 -- ONE mint helper for the suite
from kernel import approvals, dispatch, report, staging  # noqa: E402
from kernel import state as kernel_state  # noqa: E402 -- the module, for its naming rule
from kernel.backlog_types import PARENT_FIELDS, REQUIRED_FIELDS  # noqa: E402
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


def test_a_parent_binding_pointing_nowhere_is_an_error_for_every_type_that_has_one(state):
    """The reference-graph layer judged three field names and `derives_from` was not one.

    So an `SR`, `HYP` or `EXP` bound to an id that exists nowhere was reported by NOBODY -- in
    the layer whose entire job is the reference graph. The kernel refuses such a binding at
    capture, which is why each item here is written the only way one can exist: by hand, past
    the kernel. That is exactly the case a validator is for.

    Asserted over `PARENT_FIELDS` rather than over the types that had a binding when this was
    written, because "a type nobody added to the list" is the defect itself.
    """
    root = state.capture("PR", dict(PR_FIELDS))
    expected = set()
    for item_type, fields in sorted(PARENT_FIELDS.items()):
        for number, field in enumerate(fields, start=1):
            item_id = "%s-%04d" % (item_type, number)
            item = {"id": item_id, field: "PR-0099"}
            item.update({other: root["id"] for other in fields if other != field})
            os.makedirs(os.path.dirname(state.active_path(item_id)), exist_ok=True)
            state._write_yaml_atomic(state.active_path(item_id), item)
            expected.add((item_id, field))
    reported = {(f["item"], field) for f in errors(report.validate_state(state))
                for field in [f["message"].split(" ->")[0]] if "PR-0099" in f["message"]}
    assert reported == expected, (
        "the validator judged %s of the parent bindings; %s went unreported"
        % (sorted(reported), sorted(expected - reported)))


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
    walk_to_status(state, exp, "ANALYZED")
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
    walk_to_status(state, item, "APPROVED")
    found = warnings_of(report.validate_state(state))
    assert any("premise re-check" in f["message"] for f in found), found


def test_recording_the_recheck_clears_it(state):
    """...and recording the outcome — even "nothing changed" — is what clears it. A warning with
    no way to satisfy it is noise, and noise gets filtered out."""
    dec = state.capture("DEC", {"title": "d", "context": "c", "decision": "use X",
                                "consequences": "y", "source": "adr",
                                "premise_invalidation_triggers": ["throughput above 1k/s"]})
    item = state.capture("PR", dict(PR_FIELDS))
    walk_to_status(state, item, "APPROVED")
    state.update_item(item["id"], {"premise_rechecks": [dec["id"]]})
    found = warnings_of(report.validate_state(state))
    assert not [f for f in found if "premise re-check" in f["message"]], found


def test_a_premise_recheck_naming_a_phantom_is_flagged(state):
    """BUG-0004: `premise_rechecks` is written through the generic `update` path, which takes the
    value blind. A re-check that clears the warning with an id no decision carries is a claim resting
    on nothing, so the validator makes it an error -- the field's writer contract."""
    item = state.capture("PR", dict(PR_FIELDS))
    walk_to_status(state, item, "APPROVED")
    state.update_item(item["id"], {"premise_rechecks": ["DEC-9999"]})
    found = errors(report.validate_state(state))
    assert any(f["item"] == item["id"] and "DEC-9999" in f["message"] for f in found), found


def _fr_to(state, target):
    fr = state.capture("FR", {"title": "wish", "request_text": "please add X"})
    state.transition(fr["id"], "TRIAGED")
    if target != "TRIAGED":
        state.transition(fr["id"], target)
    return fr


def test_a_converted_fr_must_name_its_result(state):
    """BUG-0009(a): a CONVERTED request became another item; the state has to say WHICH. Without
    `resulting_item` the trail ends where "what came of this wish" begins."""
    fr = _fr_to(state, "CONVERTED")
    found = errors(report.validate_state(state))
    assert any(f["item"] == fr["id"] and "resulting_item" in f["message"] for f in found), found


def test_a_converted_fr_naming_its_result_is_clean(state):
    """...and naming a real item clears it. A duty with no way to satisfy it is noise."""
    pr = state.capture("PR", dict(PR_FIELDS))
    fr = _fr_to(state, "CONVERTED")
    state.update_item(fr["id"], {"resulting_item": pr["id"]})
    found = errors(report.validate_state(state))
    assert not [f for f in found if f["item"] == fr["id"]], found


def test_a_converted_fr_naming_a_phantom_result_is_flagged(state):
    """The named result must EXIST -- a link to a phantom is the same lie as no link."""
    fr = _fr_to(state, "CONVERTED")
    state.update_item(fr["id"], {"resulting_item": "PR-9999"})
    found = errors(report.validate_state(state))
    assert any(f["item"] == fr["id"] and "PR-9999" in f["message"] for f in found), found


DEC_FIELDS = {"title": "d", "context": "c", "decision": "use X", "consequences": "y",
              "source": "adr"}


def test_a_superseding_decision_marks_the_older_one(state):
    """BUG-0009(b): DEC-A supersedes DEC-B, so "which decisions still hold" is answerable from the
    state -- B is superseded, A holds -- without anyone reading `context` prose."""
    old = state.capture("DEC", dict(DEC_FIELDS, title="old", decision="use X"))
    new = state.capture("DEC", dict(DEC_FIELDS, title="new", decision="use Y instead",
                                    supersedes=[old["id"]]))
    standing, superseded = report.standing_decisions(state)
    assert old["id"] not in standing
    assert new["id"] in standing
    assert superseded.get(old["id"]) == new["id"]


def test_a_superseded_decision_is_flagged_for_archive(state):
    """A DEC has no automaton, so nothing else moves a replaced decision out of the active context;
    the validator warns, the DEC analogue of "terminal item awaiting archive"."""
    old = state.capture("DEC", dict(DEC_FIELDS, title="old"))
    state.capture("DEC", dict(DEC_FIELDS, title="new", supersedes=[old["id"]]))
    found = warnings_of(report.validate_state(state))
    assert any(f["item"] == old["id"] and "superseded by" in f["message"] for f in found), found


def test_a_decision_superseding_a_phantom_is_flagged(state):
    """The superseded id must resolve to a real decision -- otherwise "which still hold" rests on a
    phantom. Backward-compatible: the field is optional, so a DEC that supersedes nothing is clean."""
    state.capture("DEC", dict(DEC_FIELDS, supersedes=["DEC-9999"]))
    found = errors(report.validate_state(state))
    assert any("DEC-9999" in f["message"] for f in found), found


def test_a_decision_superseding_nothing_stays_valid(state):
    """Every DEC captured before this field existed carries no `supersedes` and must stay clean."""
    state.capture("DEC", dict(DEC_FIELDS))
    assert errors(report.validate_state(state)) == []


# -- BUG-0005: the last decision rides into the next session via the brief ------

def test_session_brief_carries_the_newest_standing_decision(state):
    """BUG-0005: the last call the previous session made rides into the next one WITH ITS CONTENT
    (title + decision, not just the id), so a PM does not begin blind -- and does not reach for the
    raw transcript to recover it (BUG-0019). Measured on a real generate-session-brief run."""
    state.capture("PR", dict(PR_FIELDS))
    dec = state.capture("DEC", dict(DEC_FIELDS, title="Local-only storage",
                                    decision="Ship with SQLite, no cloud sync"))
    path = report.generate_session_brief(state, "dev-team", "v", "audited")
    brief = yaml.safe_load(open(path, encoding="utf-8"))
    rows = {d["id"]: d for d in brief["standing_decisions"]}
    assert dec["id"] in rows, brief["standing_decisions"]
    assert rows[dec["id"]]["title"] == "Local-only storage"
    assert rows[dec["id"]]["decision"] == "Ship with SQLite, no cloud sync"


def test_a_superseded_decision_is_absent_from_the_brief(state):
    """The Gegenprobe for the link mechanism: a decision another one replaced does not ride along --
    the brief carries what HOLDS, not the whole history."""
    old = state.capture("DEC", dict(DEC_FIELDS, title="old", decision="use X"))
    new = state.capture("DEC", dict(DEC_FIELDS, title="new", decision="use Y instead",
                                    supersedes=[old["id"]]))
    path = report.generate_session_brief(state, "dev-team", "v", "audited")
    brief = yaml.safe_load(open(path, encoding="utf-8"))
    ids = {d["id"] for d in brief["standing_decisions"]}
    assert old["id"] not in ids, ids
    assert new["id"] in ids, ids


def test_a_status_superseded_decision_neither_holds_nor_rides_the_brief(state):
    """The Gegenprobe for the OTHER retirement mechanism: a DEC whose own status is SUPERSEDED (a
    migrated ADR) does not hold and must not appear -- the supersedes link is not the only way a
    decision is retired. Written by hand past the kernel, the only way a SUPERSEDED DEC exists
    (transition refuses a type with no automaton)."""
    dec = state.capture("DEC", dict(DEC_FIELDS, title="retired", decision="old call"))
    p = state.active_path(dec["id"])
    item = state._read_yaml(p)
    item["status"] = "SUPERSEDED"
    state._write_yaml_atomic(p, item)
    standing, _superseded = report.standing_decisions(state)
    assert dec["id"] not in standing
    path = report.generate_session_brief(state, "dev-team", "v", "audited")
    brief = yaml.safe_load(open(path, encoding="utf-8"))
    assert dec["id"] not in {d["id"] for d in brief["standing_decisions"]}


def test_the_brief_decision_section_is_bounded_in_count_and_bytes(state):
    """The section may not grow without bound: a decision log longer than the limit yields only the
    newest few, clipped, so the brief never breaks its own byte budget -- which would make
    generate_session_brief raise. The newest are the ones kept (created, then id number)."""
    ids = []
    for n in range(report._BRIEF_MAX_DECISIONS + 4):
        d = state.capture("DEC", dict(DEC_FIELDS, title="t%d" % n, decision="x" * 5000))
        ids.append(d["id"])
    path = report.generate_session_brief(state, "dev-team", "v", "audited")  # must not raise
    brief = yaml.safe_load(open(path, encoding="utf-8"))
    rows = brief["standing_decisions"]
    assert len(rows) == report._BRIEF_MAX_DECISIONS
    assert {r["id"] for r in rows} == set(ids[-report._BRIEF_MAX_DECISIONS:])
    assert all(len(r["decision"]) <= report._BRIEF_DECISION_MAX_CHARS for r in rows)


def test_a_second_user_visible_slice_may_not_enter_delivery(state):
    """R12 / parity row 107, the 4-slices incident. The point of the sequence rule is that the
    user SEES a slice before the next is built on its assumptions."""
    first = state.capture("PR", dict(PR_FIELDS))
    second = state.capture("PR", dict(PR_FIELDS, title="Second slice"))
    walk_to_status(state, first, "DELIVERED")
    walk_to_status(state, second, "IN_DELIVERY")
    found = errors(report.validate_state(state))
    assert any(f["item"] == second["id"] and "not yet ACCEPTED" in f["message"]
               for f in found), found


def test_a_technical_enabler_may_run_alongside(state):
    """The rule is about USER-VISIBLE slices: a technical enabler shows the user nothing, so
    holding it back buys nothing and would stall the work that unblocks the review."""
    first = state.capture("PR", dict(PR_FIELDS))
    enabler = state.capture("PR", dict(PR_FIELDS, title="Build pipeline",
                                       **{"class": "technical_enabler"}))
    walk_to_status(state, first, "DELIVERED")
    walk_to_status(state, enabler, "IN_DELIVERY")
    found = errors(report.validate_state(state))
    assert not [f for f in found if "not yet ACCEPTED" in f["message"]], found


# -- qa_verdicts: the definition the merge gate reads (spec II.2 Evidence) -----

def evd(state, kind="test", result="pass", related=("PR-0001",), created=None):
    """An Evidence item, optionally back-dated so ORDER can be asserted independently of clock."""
    item = state.capture("EVD", {"kind": kind, "result": result, "related": list(related),
                                 "summary": "s",
                                 "artifact_refs": ["staging/TSK-0001/run.log"]})
    if created is not None:
        path = state.active_path(item["id"])
        stored = state._read_yaml(path)
        stored["created"] = created
        state._write_yaml_atomic(path, stored)
    return item["id"]


def test_qa_verdicts_reports_the_newest_evidence_of_each_kind(state):
    """"Current verdict" is per kind and newest-wins — the property "any pass anywhere" lacks.

    `created` is set explicitly here because the kernel stamps it to the SECOND: without it the
    two items below would carry the same timestamp and the test would be measuring the id
    tiebreaker rather than the ordering rule it claims to check.
    """
    state.capture("PR", dict(PR_FIELDS))
    old = evd(state, kind="test", result="pass", created="2026-01-01T00:00:00")
    new = evd(state, kind="test", result="fail", created="2026-02-01T00:00:00")
    review = evd(state, kind="review", result="pass", created="2026-01-15T00:00:00")
    verdicts = report.qa_verdicts(state, "PR-0001")
    assert verdicts["test"]["id"] == new and verdicts["test"]["result"] == "fail"
    assert verdicts["review"]["id"] == review
    assert old not in [v["id"] for v in verdicts.values()]


def test_qa_verdicts_breaks_a_same_second_tie_by_id(state):
    """The NORMAL case, not an edge one: `created` is second-resolution, so two verdicts recorded
    in one QA run share a timestamp. Ordering by time alone would make the winner arbitrary."""
    state.capture("PR", dict(PR_FIELDS))
    stamp = "2026-03-01T12:00:00"
    evd(state, result="fail", created=stamp)
    newer = evd(state, result="pass", created=stamp)
    assert report.qa_verdicts(state, "PR-0001")["test"]["id"] == newer


def test_qa_verdicts_ignores_audit_evidence_and_other_items(state):
    """`audit` judges the project (II.10a) and evidence for another item judges another item."""
    state.capture("PR", dict(PR_FIELDS))
    state.capture("PR", dict(PR_FIELDS, title="Second"))
    evd(state, kind="audit", result="pass")
    evd(state, kind="test", result="pass", related=("PR-0002",))
    assert report.qa_verdicts(state, "PR-0001") == {}
    # ...and the unbound view keeps the same two exclusions, per item instead of per project
    by_subject = report.qa_verdicts_by_subject(state)
    assert by_subject["PR-0002"]["test"]["result"] == "pass"
    assert "audit" not in by_subject.get("PR-0001", {})


def test_qa_verdicts_by_subject_keeps_every_items_verdict_apart(state):
    """The unbound view must not collapse the store into one newest-per-kind.

    That collapse is the V1 file-level false accept rebuilt out of typed items: PR-0002's fresh
    PASS is the newest `test` in the store, and a flat reading would let it answer for PR-0001,
    whose own FAIL is still open. Grouped, both verdicts survive — which is what lets a merge that
    named no item ask "is anything failing" instead of "was the last thing green".
    """
    state.capture("PR", dict(PR_FIELDS))
    state.capture("PR", dict(PR_FIELDS, title="Second"))
    stale = evd(state, kind="test", result="fail", related=("PR-0001",),
                created="2026-01-01T00:00:00")
    fresh = evd(state, kind="test", result="pass", related=("PR-0002",),
                created="2026-02-01T00:00:00")
    by_subject = report.qa_verdicts_by_subject(state)
    assert by_subject["PR-0001"]["test"] == {"id": stale, "result": "fail",
                                             "created": "2026-01-01T00:00:00"}
    assert by_subject["PR-0002"]["test"] == {"id": fresh, "result": "pass",
                                             "created": "2026-02-01T00:00:00"}


def test_qa_verdicts_by_subject_files_evidence_under_every_item_it_names(state):
    """One QA run may judge two items at once; each of them gets that verdict.

    And newest-wins applies INSIDE a subject, not across the store: PR-0002's later pass does not
    supersede the earlier joint fail for PR-0001, although it is the newer `test` item.
    """
    state.capture("PR", dict(PR_FIELDS))
    state.capture("PR", dict(PR_FIELDS, title="Second"))
    joint = evd(state, kind="test", result="fail", related=("PR-0001", "PR-0002"),
                created="2026-01-01T00:00:00")
    later = evd(state, kind="test", result="pass", related=("PR-0002",),
                created="2026-02-01T00:00:00")
    by_subject = report.qa_verdicts_by_subject(state)
    assert by_subject["PR-0001"]["test"]["id"] == joint
    assert by_subject["PR-0002"]["test"]["id"] == later


def test_evidence_against_a_system_requirement_covers_the_root_it_derives_from(state):
    """The hop `_parents_of` did not have, and an `SR` is the natural subject of a review.

    The graph enumerated its derived types (TSK/BUG/CR/HYP/EXP) instead of reading the field
    contracts, and `SR` -- given a REQUIRED `derives_from` in this lockstep -- was not in the
    list. So a reviewer who recorded the review against the CONTRACT they reviewed produced an
    Evidence that resolved to no root, and `gate_git` refused the merge of that root with
    "nothing judges this work" at the role that had just judged it. Fail-closed, and false
    about the fact.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    sr = state.capture("SR", {"title": "Pay API", "derives_from": pr["id"],
                              "contract": "POST /pay returns 200",
                              "affected_components": ["api"]})
    evd(state, kind="review", related=(sr["id"],))
    assert report.qa_verdicts(state, pr["id"])["review"]["result"] == "pass"


def test_the_reference_graph_walks_every_binding_field_a_contract_declares():
    """Asserted over the DEFINITION, not over the types that happened to have one today.

    A test naming the five types the old `_parents_of` knew would have stayed green through the
    very defect above -- `SR` was added to the field contracts and to nothing else. So this
    reads `PARENT_FIELDS`, which is derived from those contracts: a type joins the graph the day
    its contract gives it a binding field, and this walks whatever is in there.

    Both spellings of a binding are asserted, because the contracts use both: `SR.derives_from`
    is a single id, `TSK.derives_from` a list, and a hop that only understood one of them would
    lose exactly the types the other belongs to.
    """
    for item_type, fields in sorted(PARENT_FIELDS.items()):
        assert fields, item_type
        ids = {field: "PR-%04d" % (n + 1) for n, field in enumerate(fields)}
        assert report._parents_of(item_type, ids) == list(ids.values()), item_type
        listed = {field: [value] for field, value in ids.items()}
        assert report._parents_of(item_type, listed) == list(ids.values()), item_type
        assert report._parents_of(item_type, {}) == [], item_type


# The item-id shape as a SCHEMA declares one, written out here rather than imported: this
# section judges `PARENT_FIELDS`, and the three assertions it used to make all built their
# expectation out of `PARENT_FIELDS` itself. Measured 2026-07-28: with `derives_from` deleted
# from `backlog_types._BINDING_FIELD_NAMES` -- the defect on the definition level -- they stayed
# GREEN and simply measured less. So the reader below re-derives one of the two contract sources
# with its own eyes.
_SCHEMA_ID_RX = re.compile(r"\^?\(?([A-Z]{2,4}(?:\|[A-Z]{2,4})*)\)?-\\d\{4,\}\$?")


def _bindings_the_shipped_schemas_declare():
    """(item type, field) for every schema field held to the id of ANOTHER item.

    The kernel freezes ARC/WFR/DSN instead of capturing them, so `REQUIRED_FIELDS` says nothing
    about their fields -- their contract is the schema `staging.freeze_*` validates against, and
    that is the second source `PARENT_FIELDS` has to be derived from.

    An `APR` reference is deliberately NOT a binding: an approval is a stamp ON this item, not
    the item this one hangs from, and walking it would make every approved item a child of its
    own approval. The item's own `id` field is excluded for the same reason it is in
    `generate_dashboard.relations` -- it would make every item its own parent.
    """
    directory = os.path.join(TEAM_KITS, "kernel", "schemas")
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".yaml"):
            continue
        with open(os.path.join(directory, name), encoding="utf-8") as handle:
            fields = (yaml.safe_load(handle) or {}).get("fields") or {}

        def types_named(spec):
            found = set()
            for key in ("pattern", "item_pattern"):
                match = _SCHEMA_ID_RX.fullmatch((spec or {}).get(key) or "")
                if match:
                    found.update(match.group(1).split("|"))
            return found

        owner = types_named(fields.get("id"))
        if len(owner) != 1:
            continue                       # not an item schema (session_brief, result_envelope)
        for field, spec in fields.items():
            if field == "id":
                continue
            if types_named(spec) - {"APR"}:
                yield next(iter(owner)), field


def _required_fields_the_shipped_schemas_declare():
    """{item type -> required field names}, read out of the schema files by this test."""
    contracts = {}
    directory = os.path.join(TEAM_KITS, "kernel", "schemas")
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".yaml"):
            continue
        with open(os.path.join(directory, name), encoding="utf-8") as handle:
            fields = (yaml.safe_load(handle) or {}).get("fields") or {}
        owner = _SCHEMA_ID_RX.fullmatch(((fields.get("id") or {}).get("pattern")) or "")
        if not owner or "|" in owner.group(1):
            continue
        contracts[owner.group(1)] = {field for field, spec in fields.items()
                                     if (spec or {}).get("required")}
    return contracts


def test_the_validator_holds_a_frozen_item_to_the_duties_its_schema_declares(state):
    """The field-duty loop read the CAPTURE contract, and ran zero times for the frozen types.

    `ARC`, `WFR` and `DSN` never pass `capture`, so `REQUIRED_FIELDS` says nothing about them --
    and the validator, which judges FILES rather than capture calls, therefore judged the one
    kind of item a person can only produce by hand against no duties at all. Spec II.8 names the
    consequence outright ("ARC ohne derives_from -> Validator-Flag"), and the graph fix above
    would have been half a fix without it: an architecture companion with a DANGLING
    `derives_from` was reported, one with none at all was not.

    The duties are read out of the schema files here, not off the kernel's derived map.
    """
    declared = _required_fields_the_shipped_schemas_declare()
    assert len(declared) >= 3, declared
    for item_type, fields in sorted(declared.items()):
        item_id = "%s-0001" % item_type
        os.makedirs(os.path.dirname(state.active_path(item_id)), exist_ok=True)
        state._write_yaml_atomic(state.active_path(item_id), {"id": item_id})
        reported = {f["message"].split("'")[1] for f in errors(report.validate_state(state))
                    if f["item"] == item_id and "missing required field" in f["message"]}
        assert reported == fields - {"id"}, (
            "%s: the validator asked for %s, its schema requires %s"
            % (item_type, sorted(reported), sorted(fields - {"id"})))
        os.remove(state.active_path(item_id))


def test_parent_fields_holds_every_binding_a_shipped_schema_declares():
    """`PARENT_FIELDS` answered to ONE of its two contract sources, and the other half went missing.

    Derived from `REQUIRED_FIELDS` alone, the map knew the captured types and none of the frozen
    ones -- so an `ARC` carrying `derives_from: PR-0001`, required and item-id-patterned in its
    own companion schema, hung from nothing: a review Evidence recorded against the architecture
    resolved to no root and `gate_git` refused the merge with "nothing judges this work", at the
    architect who had just judged it. The identical damage the `SR` fix was written for, one type
    over, because the fix replaced a list of types with a smaller list of types.

    Read straight out of the shipped schema files, so this assertion shares nothing with the
    derivation it judges.
    """
    declared = sorted(set(_bindings_the_shipped_schemas_declare()))
    assert len(declared) >= 3, (
        "the shipped schemas declare almost no item bindings (%s) -- the reader above stopped "
        "matching the patterns rather than the schemas losing their `derives_from`" % declared)
    missing = [(item_type, field) for item_type, field in declared
               if field not in PARENT_FIELDS.get(item_type, ())]
    assert not missing, (
        "%s declare(s) a field naming another item, and the reference graph does not walk it. "
        "Every consumer of `PARENT_FIELDS` -- the merge gate's root resolution, the validator's "
        "reference check, the kernel's write-path check -- is blind to that binding, and each "
        "answers a role that recorded a correct judgement with 'nothing judges this work'."
        % sorted(missing))


_SPEC_PATH = os.path.join(os.path.dirname(TEAM_KITS), "docs", "HARNESS_V2_SPEC.md")
# A spec bullet or header that declares one type's field list. Both spellings II.2 uses:
# `**PR-Pflichtfelder:** id, title, ...` and `- PROC: id, title, status, derives_from (optional), ...`,
# the latter sometimes with a parenthetical about the storage form (`- DSN (Manifest-YAML ...): ...`).
_SPEC_TYPE_RX = re.compile(r"^(?:\*\*([A-Z]{2,4})-Pflichtfelder:\*\*|- ([A-Z]{2,4})(?: \([^)]*\))?:)")


def _fields_the_spec_declares():
    """{item type -> the field names spec II.2 declares for it}, required and optional alike.

    THE SOURCE OUTSIDE THE KERNEL. The two readers above re-derive the FROZEN types' contract
    from the schema files; the CAPTURED types' contract has no file of its own -- it is
    `backlog_types`, the thing under test -- so an independent assertion about it has to come
    from the document the kernel implements.

    Every declared field is collected, not only the mandatory ones, because that distinction is
    exactly what went wrong: `PARENT_FIELDS` was derived from `REQUIRED_FIELDS`, which by
    construction cannot mention a field an item may omit, and spec II.2 declares two bindings as
    optional (`PROC.derives_from`, `FR.related_pr`). A field's MEANING does not depend on whether
    the item carrying it is allowed to leave it out.

    Read leniently on purpose: the leading identifier of each comma-separated part. The spec is
    prose and its parentheticals contain commas, so this over-collects tokens like `ref` -- which
    costs nothing, since the question asked of the result is only whether a field name the graph
    binds by appears in some type's list.

    COVERS THE TYPES II.2 NAMES BY CODE (twelve today, all nine bindings among them). The two it
    spells out -- `Evidence`, `Decision` -- are not matched, and are not silently uncovered
    either: `EVD.related` is required, so `REQUIRED_FIELDS` carries it and the corpus test
    exercises it end to end. The floor below is what notices if this reader stops matching.
    """
    declared, current = {}, None
    with open(_SPEC_PATH, encoding="utf-8") as handle:
        for raw in handle:
            match = _SPEC_TYPE_RX.match(raw)
            if match:
                current = match.group(1) or match.group(2)
                rest = raw[match.end():]
            elif current and raw.startswith("  ") and raw.strip():
                rest = raw                      # a wrapped continuation of the bullet above
            else:
                current = None
                continue
            for part in rest.split(","):
                head = re.match(r"\s*`?([a-z_]+)\b", part)
                if head:
                    declared.setdefault(current, set()).add(head.group(1))
    return declared


_IMPORT_WITHOUT_YAML = """
import sys

class _NoYaml:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] == "yaml":
            raise ImportError("yaml unavailable")
        return None

sys.meta_path.insert(0, _NoYaml())
import kernel.backlog_types as bt
assert "yaml" not in sys.modules, "importing backlog_types pulled PyYAML in"
assert bt.AUTOMATA and bt.REQUIRED_FIELDS and bt.ACTIVE_DIRS
print("ok")
"""


def test_backlog_types_imports_without_pyyaml():
    """The type map has to stay loadable where the parser is not, and that is a hot-path rule.

    Spec II.7 keeps the integrity gates stdlib-first, with no PyYAML import load on the hot path,
    and `guard_no_adhoc` held its item-type list as a LITERAL partly for that reason -- "importing
    the kernel to learn the type names would pull PyYAML into that path, and a guard that cannot
    load must not stop guarding". `backlog_types` is the module that could serve such a guard --
    and for one round it could not, because `PARENT_FIELDS` and `DECLARED_REQUIRED_FIELDS` were
    derived at module scope from `kernel/schemas/*.yaml`, which closed the door and made every
    import of the type names read six files. They are computed on first access instead, and the
    guard's comment now names resilience rather than PyYAML as its reason.

    Measured in a FRESH interpreter with `yaml` blocked at the finder, because the suite has
    PyYAML loaded long before any test runs and would report the opposite in-process.
    """
    proc = subprocess.run([sys.executable, "-c", _IMPORT_WITHOUT_YAML], cwd=TEAM_KITS,
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, (
        "`import kernel.backlog_types` needs PyYAML. A gate that cannot afford the parser can no "
        "longer learn the type names from the kernel, so it goes back to a literal list that "
        "drifts.\n%s%s" % (proc.stdout, proc.stderr))


def test_parent_fields_holds_every_binding_the_spec_declares_for_a_captured_type():
    """The capture contract's OPTIONAL half is part of the contract, and the graph must read it.

    `REQUIRED_FIELDS` was the whole capture-time source for one round, and it is structurally
    incapable of reporting an optional field. Spec II.2 declares `derives_from (optional)` on
    `PROC` and `related_pr (optional)` on `FR`; both are item ids when present, so both are hops
    the reference graph has to walk. It did not: a `PROC` captured against a phantom parent was
    reported by no one (`state._assert_origins_resolve` reads this same map), and an Evidence
    recorded against a `PROC` or an `FR` resolved to no root, so `gate_git` answered the role that
    had judged the work with "nothing judges this work" -- the `SR` defect, two types further on.

    Judged against the SPEC, so it shares no source with the derivation it judges.
    """
    declared = _fields_the_spec_declares()
    assert len(declared) >= 8, (
        "the spec reader stopped matching II.2's field declarations (%s)" % sorted(declared))
    from kernel.backlog_types import _BINDING_FIELD_NAMES
    missing = sorted((item_type, field)
                     for item_type, fields in declared.items()
                     for field in sorted(fields & set(_BINDING_FIELD_NAMES))
                     if field not in PARENT_FIELDS.get(item_type, ()))
    assert not missing, (
        "spec II.2 declares %s as a field naming another item, and the reference graph does not "
        "walk it. Every consumer of `PARENT_FIELDS` is blind to that binding: the merge gate "
        "finds no root for an Evidence recorded against such an item, and the kernel's write-path "
        "check lets it be captured against an id that does not exist." % missing)


def test_the_reference_graph_claims_no_binding_a_frozen_types_schema_does_not_declare():
    """The other direction of the schema check: an INVENTED hop is as wrong as a missing one.

    For the types whose whole contract is a schema file, the shipped schema is the complete
    answer -- so `PARENT_FIELDS` must hold exactly the bindings it declares. A field the graph
    walks and the contract does not have makes the validator demand a parent no writer can supply
    and lets `_hangs_from` follow a value that means something else.
    """
    from kernel.schemas import item_field_contracts
    frozen = set(item_field_contracts()) - set(REQUIRED_FIELDS)
    assert frozen >= {"ARC", "WFR", "DSN"}, sorted(frozen)
    declared = {}
    for item_type, field in _bindings_the_shipped_schemas_declare():
        declared.setdefault(item_type, set()).add(field)
    for item_type in sorted(frozen):
        assert set(PARENT_FIELDS.get(item_type, ())) == declared.get(item_type, set()), (
            "%s: the graph walks %s, its schema declares %s"
            % (item_type, sorted(PARENT_FIELDS.get(item_type, ())),
               sorted(declared.get(item_type, set()))))


def test_every_captured_type_that_hangs_from_a_root_reaches_it(state):
    """The graph, asked the question a merge asks, over REAL items of every captured type.

    A corpus and deliberately concrete: each item is captured through the kernel and bound to
    the root the way its own contract binds it, then the walk has to find the root. Nothing here
    reads `PARENT_FIELDS` for its EXPECTATION -- that is the map under test, and an assertion
    built from it stays green through a defect in it (measured: deleting `derives_from` from
    `_BINDING_FIELD_NAMES` left three such assertions passing).

    Coverage is asserted the other way round, against the map: a captured type that gains a
    binding and no corpus entry fails here, so the concreteness cannot go stale.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    bug = make_bug(state, pr["id"])
    task = make_task(state, pr["id"], bug["id"])
    sr = state.capture("SR", {"title": "Pay API", "derives_from": pr["id"],
                              "contract": "POST /pay returns 200", "affected_components": ["api"]})
    change = state.capture("CR", {"title": "c", "target_pr": pr["id"], "target_revision": 1,
                                  "change_description": "d", "acceptance_criteria": ["ac"]})
    hypothesis = state.capture("HYP", {"statement": "s", "derives_from": pr["id"],
                                       "testable_prediction": "p"})
    experiment = state.capture("EXP", {"derives_from": hypothesis["id"], "design": "d",
                                       "variables": "v", "success_criteria": "c",
                                       "evidence_refs": []})
    # FR and PROC bind through a field spec II.2 marks OPTIONAL, which is why they were missing
    # from the graph for a round: `REQUIRED_FIELDS` cannot report a field an item may omit.
    request = state.capture("FR", {"title": "make it faster", "request_text": "t",
                                   "related_pr": pr["id"]})
    procedure = state.capture("PROC", {"title": "onboarding", "steps": ["s"], "roles": ["r"],
                                       "derives_from": pr["id"]})
    corpus = {"BUG": bug["id"], "TSK": task["id"], "SR": sr["id"], "CR": change["id"],
              "HYP": hypothesis["id"], "EXP": experiment["id"], "FR": request["id"],
              "PROC": procedure["id"],
              "EVD": evd(state, kind="review", related=(task["id"],))}
    for item_type, item_id in sorted(corpus.items()):
        assert report._hangs_from(state, item_id, pr["id"], set()), (
            "%s %s is bound to the root through its contract and the graph does not get there"
            % (item_type, item_id))
    captured = {item_type for item_type in PARENT_FIELDS if item_type in REQUIRED_FIELDS}
    assert set(corpus) == captured, (
        "the corpus and the map disagree about which captured types hang from a root: "
        "%s carry a binding and are not exercised here" % sorted(captured - set(corpus)))


def test_qa_verdicts_resolves_evidence_through_the_reference_graph(state):
    """A BUG under the PR, a task under the BUG: QA judges the task, the merge is of the PR."""
    pr = state.capture("PR", dict(PR_FIELDS))
    bug = state.capture("BUG", {"title": "500 on checkout", "related_pr": pr["id"],
                                "observed": "500", "expected": "200", "repro": "post /pay",
                                "severity": "high", "acceptance_criteria": [{"id": "AC-1",
                                                                             "text": "no 500"}]})
    task = state.capture("TSK", {
        "product_requirement": pr["id"], "root_revision": 1, "derives_from": [bug["id"]],
        "type": "bugfix", "assigned_role": "backend-developer", "acceptance_refs": ["AC-1"],
        "required_inputs": [], "allowed_scope": ["src/**"], "forbidden_scope": [],
        "expected_outputs": ["src/pay.py"], "dependencies": []})
    evd(state, related=(task["id"],))
    assert report.qa_verdicts(state, pr["id"])["test"]["result"] == "pass"


def test_doctor_reads_its_identity_off_the_installation(state, tmp_path):
    """Spec II.4 lists kit / kit_version / lead_role / provider_config, and all four were `unknown`.

    THE PREDECESSOR COULD NOT FAIL FOR THE SHIPPED PATH: it called
    `report.doctor(state, kit="dev-team", kit_version="rc1")` and then asserted the report said
    "dev-team" -- it handed in its own expected value. Meanwhile `cli` passes neither argument, so
    a correctly installed project reported `unknown` for its own kit while `.claude/kit_state.json`
    named it two directories away. This calls doctor the way the CLI does -- NO arguments -- and
    builds the `.claude` an installation really has.
    """
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / "kit_state.json").write_text(
        json.dumps({"kit": "office-team", "state": "active"}), encoding="utf-8")
    (claude / "kit_version").write_text("version: 2026.07.31-4\ncontent: abc\n", encoding="utf-8")
    (claude / "settings.json").write_text(
        json.dumps({"agent": "office-manager", "hooks": {}}), encoding="utf-8")

    result = report.doctor(state)
    assert result["kit"] == "office-team", result["kit"]
    assert result["kit_version"] == "2026.07.31-4", result["kit_version"]
    assert result["lead_role"] == "office-manager", result["lead_role"]
    assert "claude" in result["provider_config"], result["provider_config"]
    # ...and an explicit argument still wins, which is what the SessionStart path needs
    assert report.doctor(state, kit="dev-team")["kit"] == "dev-team"


def test_doctor_says_unknown_only_where_it_really_cannot_tell(state):
    """`unknown` is the spec's answer for what cannot be determined -- not a default."""
    result = report.doctor(state)
    assert result["kit"] == "unknown" and result["kit_version"] == "unknown"
    assert result["lead_role"] == "unknown"


# -- per-revision items: ONE reading of one directory (disposition row 6.5) ----

def _freeze_wireframe(state, wfr_id, root_id, apr_ref, body):
    """Freeze one wireframe revision through the kernel -- the only producer of these files."""
    key = "%s-%s" % (root_id, body)
    directory = staging.staging_dir(state, key)
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, wfr_id + ".drawio.svg"), "w", encoding="utf-8") as handle:
        handle.write('<svg xmlns="http://www.w3.org/2000/svg"><g>%s</g></svg>' % body)
    return staging.freeze_wireframe(state, key, wfr_id, apr_ref, [root_id], "Checkout wireframe")


def _approved_root(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    mint_via_hook(state, approvals.create_pending_request(state, "scope", pr["id"]))
    return state.read_item(pr["id"])


def test_a_second_frozen_revision_is_one_item_and_not_a_duplicate_id(state):
    """THE merge-blocking defect of disposition row 6.5, measured at the validator.

    A second `freeze_wireframe` is the normal course of design work, and it wrote
    `WFR-0001.r02.yaml` beside `WFR-0001.r01.yaml`. `_iter_active` read every `*.yaml` as its own
    item, so the validator reported `WFR-0001 duplicate id` -- an ERROR, which
    `gate_memory_complete` turns into a blocked merge for the whole project, with no remedy a role
    is allowed to take: a frozen revision is immutable and deleting one is exactly what II.6a
    forbids.

    Both files stay on disk. The older revision is HISTORY, not garbage -- the fix is a reading
    rule, not a cleanup.
    """
    pr = _approved_root(state)
    apr_ref = pr["approval_ref"]
    _freeze_wireframe(state, "WFR-0001", pr["id"], apr_ref, "first")
    _freeze_wireframe(state, "WFR-0001", pr["id"], apr_ref, "second")
    directory = state.active_dir("WFR")
    assert sorted(n for n in os.listdir(directory) if n.endswith(".yaml")) == [
        "WFR-0001.r01.yaml", "WFR-0001.r02.yaml"]
    assert errors(report.validate_state(state)) == []
    # ...and the ONE item it is, is the newest revision -- the reading `read_anywhere` already had
    item, archived = state.read_anywhere("WFR-0001")
    assert (item["revision"], archived) == (2, False)


def test_the_generated_index_lists_a_per_revision_item_once(state):
    """The index is the second reader that had its own copy of the rule.

    `_regenerate_index_locked` listed a twice-frozen wireframe as TWO rows carrying one id, which
    is what the dashboard and every "what is open" reader work from. It now reads the same
    `iter_active_items` the validator does, so the row count follows from the definition rather
    than from a second implementation of it.
    """
    pr = _approved_root(state)
    for body in ("first", "second", "third"):
        _freeze_wireframe(state, "WFR-0001", pr["id"], pr["approval_ref"], body)
    index = state._read_yaml(os.path.join(state.root, "generated", "index.yaml"))
    rows = [row for row in index["items"] if row["id"] == "WFR-0001"]
    assert len(rows) == 1 and rows[0]["revision"] == 3, rows


def test_every_active_item_is_the_one_its_own_id_resolves_to(state):
    """The property behind both fixes, asserted over the running readers rather than per type.

    `read_anywhere` and `_iter_active` are the kernel's two answers to "which file is this item",
    and disposition row 6.5 is what happens when they differ: the validator judged a file that
    `read_anywhere` says is not the item, and reported the disagreement as a duplicate id. Stated
    as a property it needs no list of per-revision types -- a type frozen that way tomorrow is
    covered by the same assertion.
    """
    pr = _approved_root(state)
    for body in ("first", "second"):
        _freeze_wireframe(state, "WFR-0001", pr["id"], pr["approval_ref"], body)
    dispatch.create_task(state, dict(
        product_requirement=pr["id"], derives_from=pr["id"], type="implementation",
        assigned_role="backend-developer", acceptance_refs=["AC-1"], required_inputs=[],
        allowed_scope=["src/"], forbidden_scope=[], expected_outputs=["src/x.py"],
        dependencies=[]))
    seen = 0
    for _item_type, _stem, item, path, exc in report._iter_active(state):
        assert exc is None, (path, exc)
        resolved, _archived = state.read_anywhere(item["id"])
        assert resolved == item, (
            "%s is judged as %s, but its id resolves to a different file" % (item["id"], path))
        seen += 1
    assert seen >= 3, seen   # the PR, the wireframe and the task -- not the superseded revision


def test_two_different_items_claiming_one_id_are_still_a_duplicate(state):
    """The counter-direction: the revision rule must PRECISE the duplicate rule, not abolish it.

    Two frozen files that differ in more than their `.rNN` are two items, and one id between them
    is the thing gate 5 exists to catch. Written by hand because the kernel cannot produce it --
    which is exactly why the validator has to.
    """
    pr = _approved_root(state)
    _freeze_wireframe(state, "WFR-0001", pr["id"], pr["approval_ref"], "first")
    _freeze_wireframe(state, "WFR-0002", pr["id"], pr["approval_ref"], "other")
    path = os.path.join(state.active_dir("WFR"), "WFR-0002.r01.yaml")
    forged = state._read_yaml(path)
    forged["id"] = "WFR-0001"
    state._write_yaml_atomic(path, forged)
    assert [f["message"] for f in errors(report.validate_state(state))
            if "duplicate id" in f["message"]], report.validate_state(state)


def test_a_plain_file_beside_a_revision_file_is_still_a_duplicate(state):
    """One directory claiming two homes for one id is a contradiction, not a revision.

    `read_anywhere` silently prefers the plain `<ID>.yaml`, so collapsing this into "the newest
    revision" would hide the disagreement instead of reporting it. Only files that differ in
    nothing but their `.rNN` are revisions of one another.
    """
    pr = _approved_root(state)
    _freeze_wireframe(state, "WFR-0001", pr["id"], pr["approval_ref"], "first")
    companion = state._read_yaml(os.path.join(state.active_dir("WFR"), "WFR-0001.r01.yaml"))
    state._write_yaml_atomic(os.path.join(state.active_dir("WFR"), "WFR-0001.yaml"), companion)
    assert [f["message"] for f in errors(report.validate_state(state))
            if "duplicate id" in f["message"]], report.validate_state(state)


def test_the_name_the_kernel_composes_is_the_name_it_reads_back():
    """Compose and parse are one rule, so a change to either cannot pass this by halves.

    `staging` writes `<ID>.rNN` with three different suffixes and three readers take it apart
    again; the round trip is what makes "an item stored per revision IS its newest revision" a
    definition instead of four agreeing implementations.
    """
    for suffix in (".yaml", ".drawio.svg", ".html"):
        for revision in (1, 9, 10, 137):
            name = kernel_state.revision_name("WFR-0001", revision, suffix)
            assert kernel_state.split_revision(name) == ("WFR-0001", revision, suffix), name
    # a name that is NOT one of these carries no revision -- the answer the readers fall back on
    for plain in ("WFR-0001.yaml", "notes.yaml", "WFR-0001.rXX.yaml", "WFR-0001.r.yaml"):
        assert kernel_state.split_revision(plain) == (None, None, None), plain
    # ...and the two conditions `item_revision` adds on top, each one a sentence the docstrings
    # promise and neither of which had a test: a base that is no item id is not an item stored per
    # revision (`notes.r01.yaml` and `notes.r02.yaml` stay two files), and a NON-ASCII digit is not
    # a number -- `re.ASCII` is why `WFR-0001.r١٢.yaml` is not revision 12.
    assert kernel_state.split_revision("notes.r01.yaml") == ("notes", 1, ".yaml")
    assert kernel_state.item_revision("notes.r01.yaml") == (None, None)
    assert kernel_state.item_revision("WFR-0001.r١٢.yaml") == (None, None)
    assert kernel_state.item_revision("WFR-0001.r02.drawio.yaml") == (None, None)
    assert kernel_state.item_revision("WFR-0001.r02.yaml") == ("WFR-0001", 2)


def test_a_revision_file_carrying_a_second_suffix_is_not_the_active_revision(state):
    """The defect the FIRST cut of THIS fix introduced, measured before it shipped.

    `_frozen_revision_path` demanded that the `.rNN` be followed by exactly the item suffix;
    `iter_active_items` accepted any suffix. So `WFR-0001.r03.backup.yaml` -- a name a hand or a
    half-finished copy produces, never the kernel -- was the ACTIVE item for the validator and the
    index while `read_anywhere` still resolved the id to `r02`: the identical two-readings defect
    disposition row 6.5 is about, one file shape further along. Both readers ask
    `state.item_revision` now, so the stray file is not a revision at all -- it is a second file
    claiming an id, which is what the duplicate rule is for.
    """
    pr = _approved_root(state)
    for body in ("first", "second"):
        _freeze_wireframe(state, "WFR-0001", pr["id"], pr["approval_ref"], body)
    stray = os.path.join(state.active_dir("WFR"), "WFR-0001.r03.backup.yaml")
    state._write_yaml_atomic(stray, state._read_yaml(
        os.path.join(state.active_dir("WFR"), "WFR-0001.r02.yaml")))
    assert os.path.basename(state._frozen_revision_path("WFR-0001")) == "WFR-0001.r02.yaml"
    assert "WFR-0001.r02" in [stem for stem, _path in state.iter_active_items("WFR")]
    assert [f for f in errors(report.validate_state(state)) if "duplicate id" in f["message"]]


def test_a_root_presenting_a_non_dispatching_approval_is_reported(state):
    """The blind spot behind the `approval_ref` move -- nothing reported it at all.

    `mint` writes `approval_ref` for every item-bound approval and the dispatch gate's root route
    reads that one field, so minting a routine (or analysis) approval for a root that already
    carries a valid scope approval silently stops every implementation task under it. The project
    used to learn that at the next spawn, as a refusal -- and since a routine is time-boxed and
    recurring by construction, it recurs at EVERY renewal, on a root long since APPROVED.

    A WARNING: the state is legal and the remedy is a user action. The counter-direction is
    asserted in the same test, so "warn always" cannot satisfy it.
    """
    pr = _approved_root(state)
    assert not [f for f in report.validate_state(state) if "presents" in f["message"]]
    mint_via_hook(state, approvals.create_pending_request(
        state, "routine", pr["id"],
        manifest={"role": "project-auditor", "scope": ["project_memory/**"],
                  "trigger": "weekly", "cadence": "weekly"},
        approval_expires=time.time() + 3600))
    reported = [f for f in report.validate_state(state) if "presents" in f["message"]]
    assert len(reported) == 1, report.validate_state(state)
    assert reported[0]["severity"] == "warning"
    assert "routine" in reported[0]["message"] and "scope" in reported[0]["message"]
    assert "re-run the scope approval flow" in reported[0]["remedy"]
