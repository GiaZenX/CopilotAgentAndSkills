"""Tests for staging/freeze operations + the harness CLI (spec II.4/II.6a, step 1.6)."""
import io
import json
import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits"))

from conftest import approve  # noqa: E402 -- the ONE minting helper for the suite
from kernel import approvals, cli, dispatch, report, staging  # noqa: E402
from kernel.backlog_types import ACTIVE_DIRS  # noqa: E402
from kernel.schemas import SchemaError  # noqa: E402
from kernel.staging import StagingError  # noqa: E402
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

DRAWIO_SVG = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" content="&lt;mxfile&gt;&lt;/mxfile&gt;">'
    "<rect width='10' height='10'/></svg>\n"
)


@pytest.fixture
def state(tmp_path):
    root = tmp_path / "project_memory"
    root.mkdir()
    return ProjectState(str(root))


def stage_file(state, key, name, content=DRAWIO_SVG):
    directory = staging.staging_dir(state, key)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


# -- wireframe freeze ----------------------------------------------------------

def test_freeze_wireframe_happy_path(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    stage_file(state, pr["id"], "WFR-0001.drawio.svg")
    result = staging.freeze_wireframe(
        state, pr["id"], "WFR-0001", scope_apr_ref="APR-0001",
        derives_from=[pr["id"]], title="Checkout layout",
    )
    assert result["frozen"].endswith(os.path.join("design", "wireframes", "WFR-0001.r01.drawio.svg"))
    assert os.path.exists(result["frozen"])
    companion = yaml.safe_load(open(result["frozen"][:-len(".drawio.svg")] + ".yaml", encoding="utf-8"))
    assert companion["scope_apr_ref"] == "APR-0001"
    assert len(companion["diagram_hash"]) == 64
    # staging emptied on promotion (II.4 lifecycle)
    assert not os.path.isdir(staging.staging_dir(state, pr["id"]))


def test_freeze_second_revision_gets_r02(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    for expected in ("r01", "r02"):
        stage_file(state, pr["id"], "WFR-0001.drawio.svg")
        result = staging.freeze_wireframe(
            state, pr["id"], "WFR-0001", "APR-0001", [pr["id"]], "layout"
        )
        assert expected in result["frozen"]


def test_malformed_xml_blocks_promotion(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    stage_file(state, pr["id"], "WFR-0001.drawio.svg", content="<svg><unclosed>")
    with pytest.raises(StagingError, match="well-formed XML"):
        staging.freeze_wireframe(state, pr["id"], "WFR-0001", "APR-0001", [pr["id"]], "t")
    # staging untouched on failure
    assert os.path.isdir(staging.staging_dir(state, pr["id"]))


# -- architecture freeze -------------------------------------------------------

def test_freeze_architecture_writes_active_and_revision(state):
    stage_file(state, "TSK-0001", "ARC-0001.drawio.svg")
    result = staging.freeze_architecture(
        state, "TSK-0001", "ARC-0001", title="System overview", scope="whole-system",
        derives_from=["PR-0001"],
    )
    assert os.path.exists(result["frozen"])
    active = os.path.join(state.root, "architecture", "active")
    assert os.path.exists(os.path.join(active, "ARC-0001.drawio.svg"))
    companion = yaml.safe_load(open(os.path.join(active, "ARC-0001.yaml"), encoding="utf-8"))
    assert companion["assets"] == {"mode": "self_contained"}
    assert companion["approval_ref"] is None  # empty until frozen via delivery


# -- design freeze -------------------------------------------------------------

def test_freeze_design_updates_design_refs_and_invalidation_semantics(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    stage_file(state, pr["id"], "preview.html", content="<html><body>design</body></html>")
    result = staging.freeze_design(state, pr["id"], "DSN-0001", pr["id"], "preview.html")
    assert os.path.exists(result["frozen"])
    assert result["root"]["design_refs"] == ["design/revisions/DSN-0001.r01.html"]
    # design_refs is a HASHED field: on an approved root this goes through
    # update_item and would invalidate -- here the root was DRAFT, revision stays
    assert result["root"]["revision"] == 1


def test_freeze_design_empty_file_blocks(state):
    pr = state.capture("PR", dict(PR_FIELDS))
    stage_file(state, pr["id"], "preview.html", content="")
    with pytest.raises(StagingError, match="missing or empty"):
        staging.freeze_design(state, pr["id"], "DSN-0001", pr["id"], "preview.html")


def test_freeze_design_refuses_a_manifest_that_contradicts_the_declared_contract(state):
    """The manifest is VALIDATED before it is written, and this is the guard, not its consequence.

    `dsn_manifest.yaml` says `root` is a `PR|RQ` id, and that declaration is a source
    `backlog_types.PARENT_FIELDS` derives the reference graph from -- so the graph walks
    `DSN.root` believing it names a root. A manifest written past the schema would make the
    stored record say something else while every reader still follows the declaration.

    Measured with the validate call deleted: the whole kernel suite stayed green, and only a
    SECOND mutation (writing a wrong key as well) turned a test red. A guard whose removal costs
    nothing is not tested, so this drives the guard directly: `root_id` is a caller-supplied
    parameter that nothing else in `freeze_design` type-checks.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    task = state.capture("TSK", {
        "product_requirement": pr["id"], "root_revision": 1, "derives_from": [pr["id"]],
        "type": "implementation", "assigned_role": "backend-developer",
        "acceptance_refs": ["AC-1"],
        "required_inputs": [], "allowed_scope": ["src/"], "forbidden_scope": [],
        "expected_outputs": ["code"], "dependencies": []})
    stage_file(state, "design", "preview.html", content="<html><body>x</body></html>")
    with pytest.raises(SchemaError, match="root"):
        staging.freeze_design(state, "design", "DSN-0001", task["id"], "preview.html")
    assert not os.path.exists(
        os.path.join(state.root, "design", "revisions", "DSN-0001.r01.yaml")), (
        "the manifest was written despite failing its own schema")


def test_frozen_design_manifest_validates_against_its_schema(state):
    """The written record, read back off disk and held to the contract the graph derives from."""
    from kernel.schemas import validate
    pr = state.capture("PR", dict(PR_FIELDS))
    stage_file(state, "design", "preview.html", content="<html><body>x</body></html>")
    staging.freeze_design(state, "design", "DSN-0001", pr["id"], "preview.html")
    path = os.path.join(state.root, "design", "revisions", "DSN-0001.r01.yaml")
    validate(yaml.safe_load(open(path, encoding="utf-8")), "dsn_manifest")


def test_freeze_design_preserves_existing_refs(state):
    """Fable-Check 11/BUG-1: refs computed from the FRESH root -- no lost update."""
    pr = state.capture("PR", dict(PR_FIELDS))
    state.update_item(pr["id"], {"design_refs": ["design/revisions/DSN-0000.r01.html"]})
    stage_file(state, pr["id"], "preview.html", content="<html>x</html>")
    result = staging.freeze_design(state, pr["id"], "DSN-0001", pr["id"], "preview.html")
    assert result["root"]["design_refs"] == [
        "design/revisions/DSN-0000.r01.html",
        "design/revisions/DSN-0001.r01.html",
    ]


def test_frozen_revision_numbers_never_reused(state):
    """Fable-Check 11/NIT-1: max-parse -- deleting r01 must not recycle its number."""
    pr = state.capture("PR", dict(PR_FIELDS))
    stage_file(state, pr["id"], "WFR-0001.drawio.svg")
    first = staging.freeze_wireframe(state, pr["id"], "WFR-0001", "APR-0001", [pr["id"]], "t")
    os.remove(first["frozen"])  # simulate manual out-of-band deletion
    stage_file(state, pr["id"], "WFR-0001.drawio.svg")
    second = staging.freeze_wireframe(state, pr["id"], "WFR-0001", "APR-0001", [pr["id"]], "t")
    assert ".r02." in second["frozen"]


# -- rejection path ------------------------------------------------------------

def test_rejected_staging_is_archived_never_deleted(state):
    stage_file(state, "TSK-0007", "ARC-0002.drawio.svg")
    target = staging.clear_staging(state, "TSK-0007", mode="rejected")
    assert os.path.isdir(target)
    assert "archive" in target and "staging" in target
    assert os.path.exists(os.path.join(target, "ARC-0002.drawio.svg"))
    assert not os.path.isdir(staging.staging_dir(state, "TSK-0007"))


# -- CLI -----------------------------------------------------------------------

def run_cli(state, *argv):
    return cli.main(["--root", state.root, *argv])


def test_cli_validate_exit_codes(state, capsys):
    state.capture("PR", dict(PR_FIELDS))
    assert run_cli(state, "validate") == 0
    state.capture("INV", {"scope": "s", "source": "PR-0001",
                          "check": {"kind": "test", "ref": "t"}})  # text/value missing
    assert run_cli(state, "validate") == 1
    assert "text|value" in capsys.readouterr().out


def test_cli_transition_and_archive(state, capsys):
    pr = state.capture("PR", dict(PR_FIELDS))
    assert run_cli(state, "transition", pr["id"], "REJECTED") == 0
    assert run_cli(state, "archive", pr["id"]) == 0
    out = capsys.readouterr().out
    assert "REJECTED" in out and "archive" in out


def test_cli_illegal_transition_exits_1(state, capsys):
    pr = state.capture("PR", dict(PR_FIELDS))
    assert run_cli(state, "transition", pr["id"], "ACCEPTED") == 1
    assert "illegal transition" in capsys.readouterr().err


def test_cli_doctor_and_index(state, capsys):
    state.capture("PR", dict(PR_FIELDS))
    assert run_cli(state, "doctor") == 0
    assert '"state_version"' in capsys.readouterr().out
    assert run_cli(state, "generate-index") == 0


def test_cli_session_brief(state, capsys):
    state.capture("PR", dict(PR_FIELDS))
    assert run_cli(state, "generate-session-brief", "--kit", "dev-team",
                   "--kit-version", "rc1", "--enforcement", "audited") == 0
    assert "session_brief.yaml" in capsys.readouterr().out


# -- evidence: the producer the merge gate reads (spec II.2 Evidence) -----------

def test_cli_evidence_captures_a_typed_item_the_merge_gate_can_read(state, capsys):
    """The one command that turns a QA verdict into canonical state.

    Everything the gate needs is asserted on the ITEM, not on the printed line: the store it
    lands in comes from `ACTIVE_DIRS["EVD"]`, the verdict from `--result`, and the binding from
    `--related`. Evidence carries no project status (II.2), so its absence is asserted too --
    a status would put it on an automaton it has no place on.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    assert run_cli(state, "evidence", "--kind", "test", "--result", "pass",
                   "--related", pr["id"], "--summary", "full suite green",
                   "--artifact-ref", "staging/TSK-0001/coverage.html") == 0
    out = capsys.readouterr().out
    assert "EVD-0001" in out and "pass" in out
    path = os.path.join(state.root, *ACTIVE_DIRS["EVD"].split("/"), "EVD-0001.yaml")
    with open(path, encoding="utf-8") as handle:
        item = yaml.safe_load(handle)
    assert item["kind"] == "test" and item["result"] == "pass"
    assert item["related"] == [pr["id"]]
    assert item["artifact_refs"] == ["staging/TSK-0001/coverage.html"]
    assert "status" not in item


def test_cli_evidence_refuses_a_verdict_outside_the_vocabulary(state, capsys):
    """`--result passed` must not become a value the gate reads as "not a fail".

    The refusal is checked by its REASON, and the legal spelling is run right after it: a bare
    `pytest.raises(SystemExit)` would be satisfied just as well by argparse rejecting the whole
    subcommand, so deleting the command entirely would leave this green (measured).
    """
    state.capture("PR", dict(PR_FIELDS))
    with pytest.raises(SystemExit):     # argparse rejects it before the kernel is touched
        run_cli(state, "evidence", "--kind", "test", "--result", "passed",
                "--related", "PR-0001", "--summary", "s", "--artifact-ref", "staging/x.log")
    assert "--result" in capsys.readouterr().err
    assert run_cli(state, "evidence", "--kind", "test", "--result", "pass",
                   "--related", "PR-0001", "--summary", "s",
                   "--artifact-ref", "staging/x.log") == 0


def test_cli_evidence_will_not_record_a_verdict_with_nothing_to_point_at(state, capsys):
    """`--artifact-ref` is required, because the whole group's claim is proof over assertion.

    Every role text and every refusal `gate_git` prints presents that flag as THE proof, and it
    was optional: `python scripts/harness.py evidence --kind test --result pass --related PR-0001 --summary "sieht
    gut aus"` recorded a verdict pointing nowhere and opened the merge (measured). Argparse is
    only the front door — the kernel refuses the empty list as well (test_state.py), which is what
    makes the rule hold for a caller that does not come through this parser.
    """
    state.capture("PR", dict(PR_FIELDS))
    with pytest.raises(SystemExit):
        run_cli(state, "evidence", "--kind", "test", "--result", "pass",
                "--related", "PR-0001", "--summary", "sieht gut aus")
    assert "--artifact-ref" in capsys.readouterr().err
    assert run_cli(state, "evidence", "--kind", "test", "--result", "pass",
                   "--related", "PR-0001", "--summary", "sieht gut aus",
                   "--artifact-ref", "staging/TSK-0001/suite.log") == 0


def test_cli_evidence_refuses_a_binding_that_names_nothing(state, capsys):
    """Evidence bound to a phantom id is bound to nothing, and would look like proof anyway."""
    state.capture("PR", dict(PR_FIELDS))
    assert run_cli(state, "evidence", "--kind", "test", "--result", "pass",
                   "--related", "PR-0099", "--summary", "s",
                   "--artifact-ref", "staging/x.log") == 1
    assert "does not exist" in capsys.readouterr().err


def test_evidence_can_judge_a_frozen_item_and_reaches_its_root(state):
    """A frozen item is stored per REVISION, and by its plain id it did not exist at all.

    `freeze_wireframe` and `freeze_design` write `WFR-0001.r01.yaml` / `DSN-0001.r01.yaml`, while
    `active_path` composes `<id>.yaml`. So the two readers that answer "does this id name an
    item" answered no: the kernel REFUSED an Evidence recorded against a wireframe ("does not
    exist"), and the merge gate's walk stopped at the id. The designer's review could not be
    recorded, and the reviewing role would then have been told by `gate_git` that nothing judges
    the work — the same refusal the reference-graph fix was written for, at the one item type
    whose file name carries a revision.

    Asserted as the merge gate asks it: the verdict has to arrive at the ROOT.
    """
    from kernel import report
    pr = state.capture("PR", dict(PR_FIELDS))
    stage_file(state, "wire", "WFR-0001.drawio.svg")
    staging.freeze_wireframe(state, "wire", "WFR-0001", scope_apr_ref="APR-0001",
                             derives_from=[pr["id"]], title="Checkout layout")
    stage_file(state, "design", "preview.html", content="<html><body>x</body></html>")
    staging.freeze_design(state, "design", "DSN-0001", pr["id"], "preview.html")
    for target, kind in (("WFR-0001", "review"), ("DSN-0001", "acceptance")):
        assert state.exists_anywhere(target), "%s does not resolve by its own id" % target
        evidence = state.capture("EVD", {
            "kind": kind, "result": "pass", "related": [target], "summary": "judged",
            "artifact_refs": ["staging/TSK-0001/notes.md"]})
        assert report.evidence_covers(state, state.read_item(evidence["id"]), pr["id"]), target
    verdicts = report.qa_verdicts(state, pr["id"])
    assert {kind: entry["result"] for kind, entry in verdicts.items()} == {
        "review": "pass", "acceptance": "pass"}


# -- the four commands spec II.4 named and the surface lacked (capture/create-task/
#    dispatch/submit-result) --------------------------------------------------------------

def run_cli_with_body(state, body, *argv):
    """Run the CLI with a JSON body on stdin, the way a heredoc or a pipe delivers one."""
    previous = sys.stdin
    sys.stdin = io.StringIO(body)
    try:
        return run_cli(state, *argv)
    finally:
        sys.stdin = previous


def test_cli_capture_creates_a_typed_item_from_a_json_body(state, capsys):
    body = json.dumps(PR_FIELDS)
    assert run_cli_with_body(state, body, "capture", "PR") == 0
    assert "PR-0001 DRAFT" in capsys.readouterr().out
    item = state.read_item("PR-0001")
    assert item["title"] == PR_FIELDS["title"] and item["revision"] == 1
    # the kernel stamps its own fields -- a body may not carry them (`_KERNEL_SET`)
    assert item["approval_ref"] is None and item["created"]


def test_cli_capture_carries_a_list_of_mappings_no_flag_surface_could(state):
    """The reason the body is stdin at all: `acceptance_criteria` is [{id, text}].

    A flag surface would have to invent an encoding for it, and the encoding would then be a
    second grammar between the role and the hash. The mapping arrives unchanged here.
    """
    assert run_cli_with_body(state, json.dumps(PR_FIELDS), "capture", "PR") == 0
    assert state.read_item("PR-0001")["acceptance_criteria"] == PR_FIELDS["acceptance_criteria"]


def test_cli_capture_refuses_a_body_it_did_not_read(state, capsys):
    """rc 2, not 1: the kernel never looked, so reporting a refusal would be a lie about what
    happened. Both shapes a role produces by accident are covered -- nothing on stdin, and YAML
    typed where JSON was asked for."""
    assert run_cli_with_body(state, "", "capture", "PR") == 2
    assert "JSON object on STDIN" in capsys.readouterr().err
    assert run_cli_with_body(state, "title: x\nclass: normal\n", "capture", "PR") == 2
    assert "not JSON" in capsys.readouterr().err
    assert run_cli_with_body(state, "[1, 2]", "capture", "PR") == 2
    assert "JSON OBJECT" in capsys.readouterr().err


def test_cli_capture_of_a_task_goes_through_the_task_constructor(state, capsys):
    """`root_revision` has ONE producer, and `capture TSK` is not a second one.

    The field decides whether a lease is allowed at all (`create_lease` compares it against the
    root's current revision), so a body that carried it by hand would be a role choosing its own
    answer to that question. `dispatch.create_task` refuses the field and denormalizes it instead
    -- and `capture TSK` routes there, so both spellings get the same one.
    """
    state.capture("PR", dict(PR_FIELDS))
    fields = {"product_requirement": "PR-0001", "derives_from": "PR-0001",
              "type": "implementation", "assigned_role": "backend-developer",
              "acceptance_refs": ["AC-1"], "required_inputs": [], "allowed_scope": ["src/"],
              "forbidden_scope": [], "expected_outputs": [], "dependencies": []}
    assert run_cli_with_body(state, json.dumps(fields), "capture", "TSK") == 0
    capsys.readouterr()
    assert state.read_item("TSK-0001")["root_revision"] == 1
    assert run_cli_with_body(state, json.dumps(dict(fields, root_revision=99)),
                             "capture", "TSK") == 1
    assert "kernel-set" in capsys.readouterr().err


def test_cli_create_task_writes_the_work_order_the_gates_read(state, capsys):
    state.capture("PR", dict(PR_FIELDS))
    assert run_cli(state, "create-task",
                   "--product-requirement", "PR-0001", "--derives-from", "PR-0001",
                   "--type", "implementation", "--assigned-role", "backend-developer",
                   "--acceptance-ref", "AC-1", "--allowed-scope", "src/",
                   "--allowed-scope", "tests/", "--forbidden-scope", "secrets/",
                   "--expected-output", "src/checkout.py") == 0
    assert "TSK-0001 DRAFT (backend-developer)" in capsys.readouterr().out
    task = state.read_item("TSK-0001")
    assert task["allowed_scope"] == ["src/", "tests/"]         # gate layer 3's only input
    assert task["forbidden_scope"] == ["secrets/"]
    assert task["root_revision"] == 1 and task["dependencies"] == []


def test_cli_create_task_refuses_a_type_outside_the_closed_vocabulary(state, capsys):
    state.capture("PR", dict(PR_FIELDS))
    with pytest.raises(SystemExit) as exited:
        run_cli(state, "create-task", "--product-requirement", "PR-0001",
                "--derives-from", "PR-0001", "--type", "frontend-work",
                "--assigned-role", "frontend-developer", "--acceptance-ref", "AC-1",
                "--allowed-scope", "src/")
    assert exited.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def _approved_ready_task(state):
    """A PR with a real scope approval and a READY task under it -- the dispatch precondition."""
    pr = state.capture("PR", dict(PR_FIELDS))
    approve(state, pr["id"], "scope")
    assert run_cli(state, "create-task", "--product-requirement", pr["id"],
                   "--derives-from", pr["id"], "--type", "implementation",
                   "--assigned-role", "backend-developer", "--acceptance-ref", "AC-1",
                   "--allowed-scope", "src/") == 0
    state.transition("TSK-0001", "READY")
    return pr, state.read_item("TSK-0001")


def test_cli_dispatch_leases_the_task_and_prints_only_the_header(state, capsys):
    """The header is copied into the spawn prompt character for character, so stdout carries it
    and nothing else -- anything printed beside it is something a role might copy along."""
    _pr, task = _approved_ready_task(state)
    capsys.readouterr()
    assert run_cli(state, "dispatch", task["id"]) == 0
    printed = capsys.readouterr().out.strip()
    assert printed.startswith(dispatch.HEADER_PREFIX), printed
    header = dispatch.parse_header(printed)
    assert header["task_id"] == task["id"] and header["root_revision"] == 1
    assert state.read_item(task["id"])["status"] == "LEASED"
    # the nonce is the lease's, not the model's: the gate validates the printed header as-is
    assert dispatch.validate_lease(state, header)["nonce"] == header["lease"]


def test_cli_dispatch_refuses_a_second_claim_and_an_unapproved_root(state, capsys):
    _pr, task = _approved_ready_task(state)
    assert run_cli(state, "dispatch", task["id"]) == 0
    capsys.readouterr()
    assert run_cli(state, "dispatch", task["id"]) == 1      # not READY any more
    assert "not READY" in capsys.readouterr().err

    other = state.capture("PR", dict(PR_FIELDS, title="Unapproved"))
    assert run_cli(state, "create-task", "--product-requirement", other["id"],
                   "--derives-from", other["id"], "--type", "implementation",
                   "--assigned-role", "backend-developer", "--acceptance-ref", "AC-1",
                   "--allowed-scope", "src/") == 0
    state.transition("TSK-0002", "READY")
    capsys.readouterr()
    assert run_cli(state, "dispatch", "TSK-0002") == 1
    assert "no subagent without a user approval" in capsys.readouterr().err


def test_cli_dispatch_has_no_ttl_flag(state):
    """"Kurzlebige Lease" is the property spec II.4 names, so the supervised party does not get to
    choose how short short is. Asserted off the parser, which is what argparse evaluates."""
    parser = cli.build_parser()
    lease = parser._subparsers._group_actions[0].choices["dispatch"]
    options = [option for action in lease._actions for option in action.option_strings]
    assert not [option for option in options if "ttl" in option.lower()], options


def test_cli_submit_result_moves_the_task_and_stores_the_envelope(state, capsys):
    _pr, task = _approved_ready_task(state)
    header = dispatch.parse_header(_dispatch_line(state, task["id"], capsys))
    dispatch.validate_dispatch(state, header, "backend-developer", claim=True)
    dispatch.spawn_outcome(state, task["id"], True)
    assert state.read_item(task["id"])["status"] == "IN_PROGRESS"

    assert run_cli(state, "submit-result", "--task-id", task["id"],
                   "--role", "backend-developer", "--status-proposal", "SUBMITTED",
                   "--summary", "checkout implemented", "--output", "src/checkout.py",
                   "--scope-touched", "src/checkout.py") == 0
    assert "%s -> SUBMITTED" % task["id"] in capsys.readouterr().out
    envelope = state._read_yaml(os.path.join(state.root, "tasks", "results",
                                             task["id"] + ".envelope.yaml"))
    assert envelope["outputs"] == ["src/checkout.py"] and envelope["followups"] == []


def test_cli_submit_result_holds_the_envelope_to_its_schema(state, capsys):
    """The 4 KB cap and the field contract are the schema's, and the CLI does not soften them:
    raw logs are REFERENCED (spec II.5), so an inlined one is refused at the kernel boundary."""
    _pr, task = _approved_ready_task(state)
    header = dispatch.parse_header(_dispatch_line(state, task["id"], capsys))
    dispatch.validate_dispatch(state, header, "backend-developer", claim=True)
    dispatch.spawn_outcome(state, task["id"], True)
    assert run_cli(state, "submit-result", "--task-id", task["id"],
                   "--role", "backend-developer", "--status-proposal", "SUBMITTED",
                   "--summary", "x" * 3000) == 1
    assert "max_len" in capsys.readouterr().err
    assert state.read_item(task["id"])["status"] == "IN_PROGRESS"


def _dispatch_line(state, task_id, capsys):
    capsys.readouterr()
    assert run_cli(state, "dispatch", task_id) == 0
    return capsys.readouterr().out.strip()


# -- request-approval: the walkable counterpart to the transition gate -------------------------

def test_cli_request_approval_opens_the_question_the_gate_will_pin(state, capsys):
    """Without this command the transition gate had no counterpart at all.

    `create_pending_request` had no caller in the shipped tree, so no `[APR-REQ:<id>]` question
    could exist, so nothing could ever mint -- and a gated edge would refuse forever. What is
    asserted is the whole chain the gate needs: a pending request on disk, a question carrying
    that request's marker, and a question BYTE-IDENTICAL to what `build_question` rebuilds from
    the stored request (which is what `gate_approval` compares against).
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    assert run_cli(state, "request-approval", "scope", pr["id"]) == 0
    printed = json.loads(capsys.readouterr().out)

    pending = os.path.join(state.root, "approvals", "pending")
    files = sorted(os.listdir(pending))
    assert len(files) == 1, files
    request_id = files[0][:-5]
    assert "[APR-REQ:%s]" % request_id in printed["question"]
    stored = approvals.pending_request(state, request_id)
    assert printed == approvals.build_question(stored)
    # the mint code lives ONLY in the approval option's label (spec II.2 / spike S2b)
    assert stored["mint_code"] in printed["options"][0]["label"]
    assert stored["mint_code"] not in printed["question"] + printed["header"]


def test_cli_request_approval_only_offers_the_item_derived_kinds(state, capsys):
    """The time-boxed kinds (routine/analysis/push) take a manifest a command line cannot carry.

    Derived from `APR_KINDS - EXPIRING_KINDS` rather than listed: spec II.2 splits approvals into
    the time-boxed ones and the content-invalidated ones, and only the second group has an
    item-derived manifest. A kind that moved between those groups changes this surface with it.
    """
    parser = cli.build_parser()
    offered = parser._subparsers._group_actions[0].choices["request-approval"]._actions
    kinds = [action.choices for action in offered if action.dest == "kind"][0]
    assert set(kinds) == set(approvals.APR_KINDS) - approvals.EXPIRING_KINDS
    for kind in kinds:
        assert approvals.item_subject_manifest(
            {"id": "PR-0001", "revision": 1}, kind) is not None
    state.capture("PR", dict(PR_FIELDS))
    with pytest.raises(SystemExit) as exited:
        run_cli(state, "request-approval", "routine", "PR-0001")
    assert exited.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_the_installer_position_prints_utf8_whatever_the_console_codepage_is(state, tmp_path):
    """The PRE-INSTALL position is the one `_pin_utf8` saves, and this measures that position.

    Measured with the function removed: the INSTALLED entry point still prints UTF-8, because the
    shim imports `_kernel` -> `_compat`, which pins both streams at import. The installer position
    (`python -B -m kernel.cli …`, what the entry gate uses) loads no hook helper and was cp1252.
    So the subject here is that command, run with `PYTHONIOENCODING=cp1252` to stand in for a
    console that is not UTF-8 -- and the bytes it writes have to decode as UTF-8, because
    `gate_approval` compares the question character for character.

    The predecessor of this test asserted only that `_pin_utf8()` calls `reconfigure` twice; it
    could not go red for any other reason and never touched the path its docstring described.
    """
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pr = state.capture("PR", dict(PR_FIELDS))
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONUTF8")}
    env["PYTHONPATH"] = os.path.join(root, "team-kits")
    env["PYTHONIOENCODING"] = "cp1252"
    opened = subprocess.run(
        [sys.executable, "-B", "-m", "kernel.cli", "--root", state.root,
         "request-approval", "scope", pr["id"]],
        capture_output=True, env=env, timeout=120)
    assert opened.returncode == 0, opened.stderr.decode("utf-8", "replace")
    question = json.loads(opened.stdout.decode("utf-8"))     # strict: mojibake fails here
    assert "für" in question["question"], question["question"]
    assert question == approvals.build_question(
        approvals.pending_request(state, question["question"].split("[APR-REQ:")[1][:32]))


def test_cli_capture_refuses_a_body_over_the_item_budget(state, capsys):
    """`capture` went around the budget every other writer into this tree obeys.

    Measured before this: a 2 MB body was accepted, the item written, and only `validate` said so
    afterwards -- about a file nothing can edit any more (`update_item` refuses hashed-field
    surgery, and there is no edit command at all). The cap is `report.ITEM_MAX_BYTES`, read from
    the validator's own constant so the two cannot drift.
    """
    body = dict(PR_FIELDS, problem="x" * (report.ITEM_MAX_BYTES + 1))
    assert run_cli_with_body(state, json.dumps(body), "capture", "PR") == 2
    err = capsys.readouterr().err
    assert str(report.ITEM_MAX_BYTES) in err and "staging" in err
    assert not os.path.exists(state.active_path("PR-0001"))


def test_cli_capture_survives_a_body_no_parser_can_bound(state, capsys):
    """A RecursionError is not a usage message; a role hitting one learns nothing.

    THE DEPTH COMES FROM THE INTERPRETER, not from a number that looked deep enough. The first
    version sent 400 brackets, which `json.loads` parses without complaint -- so it never reached
    the branch it was written for and passed on the LIST refusal instead (mutation-measured:
    `except RecursionError` -> `except ZeroDivisionError` stayed green). `sys.getrecursionlimit()`
    is what decides, so the fixture is derived from it, and the assertion names the message only
    this branch produces.
    """
    depth = sys.getrecursionlimit()
    while depth <= 100000:
        try:
            json.loads("[" * depth + "]" * depth)
        except RecursionError:
            break
        depth *= 2
    else:
        pytest.fail("no nesting depth made this parser recurse -- the branch is unreachable")
    body = "[" * depth + "]" * depth
    # ...and the branch is only reachable if such a body still fits the item budget, which is
    # checked first. If it ever does not, the RecursionError arm is dead code and this says so
    # rather than passing on the budget refusal, which is how the first version of this test lied.
    assert len(body.encode("utf-8")) <= report.ITEM_MAX_BYTES, (
        "a body deep enough to recurse (%d) is already over the %d-byte item budget, so the "
        "RecursionError branch cannot be reached through this command"
        % (len(body.encode("utf-8")), report.ITEM_MAX_BYTES))
    assert run_cli_with_body(state, body, "capture", "PR") == 2
    assert "nests too deeply" in capsys.readouterr().err


def test_a_design_ref_that_names_nothing_does_not_open_a_spawn(state):
    """`design_refs` is the II.6 gate's input and nothing resolved it.

    Measured: `capture PR … "design_refs":["DSN-9999"]` then a UI task naming that ref -> SPAWN
    ALLOWED. The field is not a binding (`PARENT_FIELDS`), so no write path ever looked; the gate
    that CLAIMS to ask whether the reference resolves is where it is asked now.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    state.update_item(pr["id"], {"design_refs": ["DSN-9999"]})
    approve(state, pr["id"], "scope")
    task = dispatch.create_task(state, {
        "product_requirement": pr["id"], "derives_from": pr["id"], "type": "ui",
        "assigned_role": "frontend-developer", "acceptance_refs": ["AC-1"],
        "required_inputs": [], "allowed_scope": ["src/"], "forbidden_scope": [],
        "expected_outputs": [], "dependencies": [], "design_ref": "DSN-9999"})
    state.transition(task["id"], "READY")
    header = dispatch.parse_header(
        dispatch.dispatch_header(dispatch.create_lease(state, task["id"])))
    with pytest.raises(dispatch.DispatchError, match="exist nowhere"):
        dispatch.validate_dispatch(state, header, "frontend-developer")


def test_a_design_ref_may_not_escape_the_state_root_or_name_any_file(state, tmp_path):
    """The first fix closed the phantom-ID shape and left every PATH open.

    Measured against the running resolver before this: `README.md`, `generated/index.yaml`,
    `staging`, `.`, `..`, `../scripts/harness.py` and `../.claude/settings.json` all resolved
    True, and the last of them opened a real spawn end to end. Three conditions decide now --
    containment after `normpath`, it must be a FILE, and it must lie in a directory a freezer
    writes into (`staging.frozen_design_dirs`) -- and each row below is one of the measured cases.
    """
    frozen = os.path.join(state.root, *ACTIVE_DIRS["DSN"].split("/"))
    os.makedirs(frozen, exist_ok=True)
    with open(os.path.join(frozen, "DSN-0001.r01.html"), "w", encoding="utf-8") as handle:
        handle.write("<html/>")
    os.makedirs(os.path.join(state.root, "generated"), exist_ok=True)
    with open(os.path.join(state.root, "generated", "index.yaml"), "w", encoding="utf-8") as h:
        h.write("x")
    outside = os.path.join(os.path.dirname(state.root), ".claude")
    os.makedirs(outside, exist_ok=True)
    with open(os.path.join(outside, "settings.json"), "w", encoding="utf-8") as handle:
        handle.write("{}")

    resolves = dispatch._design_ref_resolves
    assert resolves(state, ACTIVE_DIRS["DSN"] + "/DSN-0001.r01.html")
    # THE ID FORM, on an id that really was frozen. The first cut of the resolver could not reach
    # its own id branch at all -- a bare identifier is a relative path under the root, so it left
    # through the path branch as "not a file" -- and replacing that whole branch with `return
    # False` changed no test. A phantom in the refused list cannot catch that; a real one can.
    pr = state.capture("PR", dict(PR_FIELDS))
    stage_file(state, pr["id"], "preview.html", content="<html><body>d</body></html>")
    staging.freeze_design(state, pr["id"], "DSN-0003", pr["id"], "preview.html")
    assert state.exists_anywhere("DSN-0003")
    assert resolves(state, "DSN-0003"), "the id of a really frozen design does not resolve"
    for refused in ("DSN-9999",                                   # the original phantom id
                    ACTIVE_DIRS["DSN"] + "/DSN-0002.r01.html",    # right place, no such file
                    "generated/index.yaml",                       # exists, wrong place
                    "staging", ".", "..", "../../..",             # directories / walk-ups
                    "../.claude/settings.json",                   # the measured escape
                    "../scripts/harness.py", ""):
        assert not resolves(state, refused), refused


def test_bump_kit_version_check_mode_writes_nothing(tmp_path):
    """`--check` was argv-blind: it would have STAMPED the tree it was being asked about.

    A reviewer relied on it as a read-only probe, which is exactly the way a flag like this gets
    trusted. Measured on a copy of `team-kits/` so the repo's own VERSION files are not the
    subject: with a kit file changed, `--check` reports a due bump, returns 1, and leaves every
    byte of VERSION alone; the stamping mode then writes.
    """
    import hashlib
    import shutil
    import subprocess

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    copy = tmp_path / "repo"
    shutil.copytree(root, str(copy), ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "*.pyc", ".pytest_cache", ".ruff_cache", "radar"))
    version = copy / "team-kits" / "dev-team" / "VERSION"
    marker = copy / "team-kits" / "dev-team" / "hooks" / "gate_git.py"
    marker.write_text(marker.read_text(encoding="utf-8") + "\n# probe\n", encoding="utf-8")
    before = hashlib.sha256(version.read_bytes()).hexdigest()

    checked = subprocess.run(
        [sys.executable, "-B", str(copy / "tools" / "bump_kit_version.py"), "--check"],
        capture_output=True, text=True, timeout=300)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    assert "BUMP DUE" in checked.stdout, checked.stdout
    assert hashlib.sha256(version.read_bytes()).hexdigest() == before, "--check WROTE the stamp"

    stamped = subprocess.run(
        [sys.executable, "-B", str(copy / "tools" / "bump_kit_version.py")],
        capture_output=True, text=True, timeout=300)
    assert stamped.returncode == 0, stamped.stdout + stamped.stderr
    assert hashlib.sha256(version.read_bytes()).hexdigest() != before
    again = subprocess.run(
        [sys.executable, "-B", str(copy / "tools" / "bump_kit_version.py"), "--check"],
        capture_output=True, text=True, timeout=300)
    assert again.returncode == 0 and "unchanged" in again.stdout, again.stdout


def test_a_design_ref_cannot_leave_the_state_root_through_a_link(state, tmp_path):
    """`normpath` is textual and `isfile` follows links -- so containment needs `realpath`.

    Measured on Windows with `mklink /J project_memory/design/revisions/out .claude`: the entry
    `design/revisions/out/settings.json` resolved True while its real path lay outside the state
    root. This repo has paid for a symlink-blind path comparison once already
    (`hashing._bundle_files`); the fix is the same word in both places.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "settings.json").write_text("{}", encoding="utf-8")
    frozen = os.path.join(state.root, *ACTIVE_DIRS["DSN"].split("/"))
    os.makedirs(frozen, exist_ok=True)
    link = os.path.join(frozen, "out")
    try:
        os.symlink(str(outside), link, target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("this platform/user cannot create a directory link")
    assert os.path.isfile(os.path.join(link, "settings.json")), "the fixture built no live link"
    assert not dispatch._design_ref_resolves(state, ACTIVE_DIRS["DSN"] + "/out/settings.json")


def test_a_wireframe_directory_is_not_a_design_reference(state):
    """`frozen_design_dirs` was wider than any producer.

    `freeze_wireframe` never touches `design_refs` -- only `freeze_design` appends, and it appends
    under `ACTIVE_DIRS[DESIGN_REF_TYPE]`. A real file under `design/wireframes/` used to resolve,
    which is a rule about a shape nothing produces. Spec II.2 does expect approved wireframes among
    the design references (II.6a); that the producer is missing is the open gap, named in
    `staging.DESIGN_REF_TYPE`, and this test is what turns red the day it is closed there.
    """
    wireframes = os.path.join(state.root, *ACTIVE_DIRS["WFR"].split("/"))
    os.makedirs(wireframes, exist_ok=True)
    with open(os.path.join(wireframes, "WFR-0001.r01.drawio.svg"), "w", encoding="utf-8") as h:
        h.write("<svg/>")
    assert staging.frozen_design_dirs() == (ACTIVE_DIRS[staging.DESIGN_REF_TYPE],)
    assert not dispatch._design_ref_resolves(
        state, ACTIVE_DIRS["WFR"] + "/WFR-0001.r01.drawio.svg")


def test_a_probe_failure_cannot_take_the_whole_command_surface_down(state, monkeypatch, capsys):
    """`item_derived_kinds()` runs inside `build_parser()`, so anything it lets escape kills EVERY
    command -- `doctor` included.

    The probe is `{"id": ..., "revision": ...}`, and a future item-derived kind whose manifest
    reads a real field raises `KeyError`, not `ApprovalError`. Measured before the widening:
    `KeyError: 'contract'` out of `build_parser()` and out of `main([..., "doctor"])` -- exactly
    the shape `cli.py`'s own docstring is written against ("a diagnosis command that destroys what
    it diagnoses"). A kind that cannot be built from an id alone is simply not item-derived.
    """
    original = approvals.item_subject_manifest

    def hostile(item, kind):
        if kind == "acceptance":
            raise KeyError("contract")
        return original(item, kind)

    monkeypatch.setattr(approvals, "item_subject_manifest", hostile)
    kinds = approvals.item_derived_kinds()
    assert "acceptance" not in kinds and "scope" in kinds, kinds
    assert cli.build_parser() is not None
    assert run_cli(state, "doctor") == 0
    assert '"state_version"' in capsys.readouterr().out
