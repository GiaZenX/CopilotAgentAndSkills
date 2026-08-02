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
from conftest import walk_to_status  # noqa: E402
from kernel.backlog_types import ACTIVE_DIRS, TransitionError  # noqa: E402
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


def test_cli_request_approval_offers_exactly_the_kinds_a_manifest_builder_exists_for(state, capsys):
    """The surface is the kinds SOMETHING can build a subject manifest for -- and only those.

    The predecessor said `APR_KINDS - EXPIRING_KINDS` and called that "the item-derived kinds".
    Two properties in one sentence, agreeing by accident: `push` is time-boxed AND has a manifest
    builder, so the moment the CLI grew `request-approval push` -- the gap that made every project
    unable to publish -- the sentence was wrong about both halves. The property that actually
    decides the surface is whether a manifest for that kind can be BUILT without a caller who
    types an analysis question, a read-only scope and a cadence; the two families that can are
    `item_derived_kinds` (from an item id) and `line_manifest_kinds` (from flags).

    Not a set comparison alone, which would only prove somebody wrote the same expression twice.
    Every offered kind is put through the builder its family names and has to return a manifest,
    and every kind of the vocabulary that NO family claims has to be refused by the real parser.
    So a kind added to the surface without a builder fails on the equality, a kind whose builder
    stopped producing a manifest fails on the call, and a builder family that grew a name outside
    `APR_KINDS` fails on the vocabulary assertion.

    WHAT THIS CANNOT SAY, measured rather than guessed: adding a kind to `APR_KINDS` with no
    builder anywhere leaves this green, because the parser then refuses it and the loop below
    asserts exactly that. Whether such a kind SHOULD have become requestable is a reading -- it is
    the state `routine` and `analysis` are deliberately in. The `push` shape, a kind that HAS a
    builder while the surface ignores it, is the one this test is red for.
    """
    parser = cli.build_parser()
    offered = parser._subparsers._group_actions[0].choices["request-approval"]._actions
    kinds = [action.choices for action in offered if action.dest == "kind"][0]
    item_built = set(approvals.item_derived_kinds())
    line_built = set(approvals.line_manifest_kinds())
    buildable = item_built | line_built

    assert set(kinds) == buildable
    assert buildable <= set(approvals.APR_KINDS), (
        "a manifest builder names a kind the approval vocabulary does not have: %s"
        % sorted(buildable - set(approvals.APR_KINDS)))

    for kind in sorted(kinds):
        if kind in item_built:
            manifest = approvals.item_subject_manifest({"id": "PR-0001", "revision": 1}, kind)
        else:
            builder = approvals.LINE_MANIFEST_BUILDERS[kind]
            # the flags the parser really carries for this kind, read off the same signature the
            # parser read -- a builder whose keys moved takes its command line with it
            manifest = builder(**{name: "x" for name in cli.manifest_parameters(builder)})
        assert isinstance(manifest, dict) and manifest, (
            "`request-approval %s` is offered, but its manifest builder returns nothing to hash"
            % kind)

    # ...and every kind no family can build stays OFF the command line, judged by the parser
    # rather than named here (`routine`/`analysis` today, whatever the split says tomorrow).
    state.capture("PR", dict(PR_FIELDS))
    unbuildable = sorted(set(approvals.APR_KINDS) - buildable)
    assert unbuildable, "every kind is buildable, so this half of the split measures nothing"
    for kind in unbuildable:
        with pytest.raises(SystemExit) as exited:
            run_cli(state, "request-approval", kind, "PR-0001")
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


# -- the freeze commands: the promotion path a role can reach ------------------------------

BUG_FIELDS = {
    "title": "checkout 500s", "related_pr": "PR-0001", "observed": "500 on POST /pay",
    "expected": "200 and an order", "repro": "post /pay with a valid cart", "severity": "high",
    "acceptance_criteria": [{"id": "AC-1", "text": "no 500 on /pay"}],
}


def test_the_freeze_body_contract_is_read_off_the_operations_own_signature(state, capsys):
    """The three freeze commands validate their stdin body against `inspect.signature`, not a list.

    That is what makes the surface follow the kernel: `FREEZE_OPERATIONS` is one mapping, and the
    subcommand names, the `--help` text, the required keys, the optional keys and the type each
    key must carry are all derived from it. Renaming a parameter of `staging.freeze_architecture`
    moves every one of them together.

    All four refusals are rc 2 and not 1: the kernel never looked, so calling it a state refusal
    would tell the role its freeze was rejected when it was never attempted.
    """
    contract = cli.freeze_parameters(staging.freeze_architecture)
    assert contract["derives_from"] == (True, list)
    assert contract["packaging"] == (False, dict)
    assert "state" not in contract, "the CLI holds the state; a body may never carry it"

    stage_file(state, "PR-0001", "ARC-0001.drawio.svg")
    body = {"staging_key": "PR-0001", "arc_id": "ARC-0001", "title": "t", "scope": "s",
            "derives_from": ["PR-0001"]}

    missing = dict(body)
    missing.pop("scope")
    assert run_cli_with_body(state, json.dumps(missing), "freeze-architecture") == 2
    assert "is missing scope" in capsys.readouterr().err

    unknown = dict(body, packagng={"method": "docker"})
    assert run_cli_with_body(state, json.dumps(unknown), "freeze-architecture") == 2
    assert "no parameter for" in capsys.readouterr().err

    mistyped = dict(body, derives_from="PR-0001")
    assert run_cli_with_body(state, json.dumps(mistyped), "freeze-architecture") == 2
    err = capsys.readouterr().err
    assert "derives_from" in err and "list" in err

    smuggled = dict(body, state="somewhere else")
    assert run_cli_with_body(state, json.dumps(smuggled), "freeze-architecture") == 2
    assert "no parameter for" in capsys.readouterr().err


def test_the_freeze_commands_write_the_state_no_other_producer_can(state, capsys):
    """The measured hole this closes: `capture` refuses `ARC`, `project_memory/**` is kernel-only
    for tool writes, and `staging.freeze_*` had no caller a role could reach -- so an ARC item, a
    frozen wireframe and a `design_refs` entry were all unreachable in a shipped project.

    The printed path is STATE-RELATIVE on purpose: the absolute one names `project_memory`, and
    `gate_write_scope` refuses a write-capable pipeline whose command line does.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    stage_file(state, pr["id"], "ARC-0001.drawio.svg")
    assert run_cli_with_body(state, json.dumps({
        "staging_key": pr["id"], "arc_id": "ARC-0001", "title": "Deployment",
        "scope": "whole system", "derives_from": [pr["id"]],
        "packaging": {"method": "docker"}}), "freeze-architecture") == 0
    printed = capsys.readouterr().out.strip()
    assert printed == "architecture/revisions/ARC-0001.r01.drawio.svg", printed
    assert "project_memory" not in printed
    companion = os.path.join(state.root, "architecture", "active", "ARC-0001.yaml")
    with open(companion, encoding="utf-8") as handle:
        assert yaml.safe_load(handle)["packaging"] == {"method": "docker"}

    stage_file(state, pr["id"], "WFR-0001.drawio.svg")
    apr = approve(state, pr["id"])
    assert run_cli_with_body(state, json.dumps({
        "staging_key": pr["id"], "wfr_id": "WFR-0001", "scope_apr_ref": apr["id"],
        "derives_from": [pr["id"]], "title": "Checkout screen"}), "freeze-wireframe") == 0
    assert capsys.readouterr().out.strip() == "design/wireframes/WFR-0001.r01.drawio.svg"


def test_freeze_design_is_the_only_thing_that_can_fill_design_refs(state, capsys):
    """Minimum-keep 9 end to end: freeze -> `design_refs` -> the spawn tooth that reads it.

    `dispatch.validate_dispatch` -- the one function `gate_dispatch` calls at a spawn -- refuses
    a UI task whose `design_ref` is not one of the root's
    CONFIRMED refs -- but only once that list is non-empty, and `staging.freeze_design` is the only
    function in the harness that appends to it. Without a command for it the rule could not fire in
    any shipped project, so it existed as prose. Both directions are measured here: the wrong ref
    is refused, the frozen one dispatches.
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    assert not state.read_item(pr["id"]).get("design_refs")
    stage_file(state, pr["id"], "preview.html", content="<html><body>x</body></html>")
    assert run_cli_with_body(state, json.dumps({
        "staging_key": pr["id"], "dsn_id": "DSN-0001", "root_id": pr["id"],
        "source_name": "preview.html"}), "freeze-design") == 0
    out = capsys.readouterr().out
    assert "design/revisions/DSN-0001.r01.html" in out
    assert "PR-0001 design_refs: design/revisions/DSN-0001.r01.html" in out
    frozen = state.read_item(pr["id"])["design_refs"]
    assert frozen == ["design/revisions/DSN-0001.r01.html"]

    walk_to_status(state, state.read_item(pr["id"]), "IN_DELIVERY")
    order = {"product_requirement": pr["id"], "derives_from": pr["id"], "type": "ui",
             "assigned_role": "frontend-developer", "acceptance_refs": ["AC-1"],
             "allowed_scope": ["frontend/"], "forbidden_scope": [], "required_inputs": [],
             "expected_outputs": [], "dependencies": []}
    wrong = dispatch.create_task(state, dict(order, design_ref="DSN-9999"))
    state.transition(wrong["id"], "READY")
    header = json.loads(dispatch.dispatch_header(
        dispatch.create_lease(state, wrong["id"])).split(" ", 1)[1])
    with pytest.raises(dispatch.DispatchError) as refused:
        dispatch.validate_dispatch(state, header, order["assigned_role"])
    assert "design_ref" in str(refused.value)

    good = dispatch.create_task(state, dict(order, design_ref=frozen[0]))
    state.transition(good["id"], "READY")
    header = json.loads(dispatch.dispatch_header(
        dispatch.create_lease(state, good["id"])).split(" ", 1)[1])
    assert dispatch.validate_dispatch(state, header, order["assigned_role"])


def test_a_bug_cannot_be_verified_without_the_regression_evidence(state, capsys):
    """Minimum-keep 8. The constitution says the regression test's Evidence is what moves a bug
    from FIXED to VERIFIED; measured before this, `transition BUG-0001 VERIFIED` ran with no
    Evidence in the project at all and `validate` then reported 0 errors.

    Four steps, because the rule is about a CURRENT PASSING TEST verdict and each of the three
    near-misses is a way of not being one: nothing at all, a failing test, and a passing review
    (which judges the code, not the repro).
    """
    pr = state.capture("PR", dict(PR_FIELDS))
    bug = state.capture("BUG", dict(BUG_FIELDS, related_pr=pr["id"]))
    walk_to_status(state, bug, "FIXED")

    with pytest.raises(TransitionError) as refused:
        state.transition(bug["id"], "VERIFIED")
    message = str(refused.value)
    assert "'test' Evidence that PASSES" in message and "there is none" in message
    assert "--related %s" % bug["id"] in message, "the remedy must be a line the role can type"

    assert run_cli(state, "evidence", "--kind", "test", "--result", "fail",
                   "--related", bug["id"], "--summary", "red",
                   "--artifact-ref", "staging/x/run.log") == 0
    capsys.readouterr()
    with pytest.raises(TransitionError) as still:
        state.transition(bug["id"], "VERIFIED")
    assert "verdict is 'fail'" in str(still.value)

    assert run_cli(state, "evidence", "--kind", "review", "--result", "pass",
                   "--related", bug["id"], "--summary", "looks fine",
                   "--artifact-ref", "staging/x/review.md") == 0
    capsys.readouterr()
    with pytest.raises(TransitionError):
        state.transition(bug["id"], "VERIFIED")

    assert run_cli(state, "evidence", "--kind", "test", "--result", "pass",
                   "--related", bug["id"], "--summary", "regression green",
                   "--artifact-ref", "staging/x/run2.log") == 0
    capsys.readouterr()
    assert state.transition(bug["id"], "VERIFIED")["status"] == "VERIFIED"


def _tree_state(path):
    """Every file under `path`, as {relative path: sha256} — the canary a freeze must not touch."""
    import hashlib
    state = {}
    for current, _dirs, files in os.walk(path):
        for name in sorted(files):
            full = os.path.join(current, name)
            try:
                with open(full, "rb") as handle:
                    state[os.path.relpath(full, path)] = hashlib.sha256(handle.read()).hexdigest()
            except OSError:
                state[os.path.relpath(full, path)] = "<unreadable>"
    return state


CANARY = "OUTSIDE-CANARY-8f2a"
ARTEFACTS = ("WFR-0001.drawio.svg", "ARC-0001.drawio.svg")
VALID_FREEZE_BODY = {
    "staging_key": "PR-0001", "wfr_id": "WFR-0001", "arc_id": "ARC-0001", "dsn_id": "DSN-0001",
    "root_id": "PR-0001", "source_name": "preview.html", "title": "t", "scope": "s",
    "derives_from": ["PR-0001"], "scope_apr_ref": None, "approval_ref": None,
}


def _freeze_fixture(work, sibling):
    """A state root under `work`, with the artefacts a freeze looks for placed BOTH inside the
    staging key and at every place a traversal would land.

    That second placement is what makes this an exploit reproduction rather than a spelling test:
    without a source file at the traversal target the operation stops at `FileNotFoundError`, the
    canary survives, and the test would pass over the unfixed kernel. Only the copies OUTSIDE the
    state root carry `CANARY`, so "did something from outside get in" is decidable.
    """
    root = os.path.join(str(work), "project_memory")
    os.makedirs(os.path.join(root, "staging", "PR-0001"), exist_ok=True)
    state = ProjectState(root)
    state.capture("PR", dict(PR_FIELDS))
    for directory, preview in ((os.path.join(root, "staging", "PR-0001"), "<html>inside</html>"),
                               (root, "<html>inside</html>"),
                               (str(work), "<html>%s</html>" % CANARY),
                               (sibling, "<html>%s</html>" % CANARY)):
        os.makedirs(directory, exist_ok=True)
        for name in ARTEFACTS:
            with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
                handle.write(DRAWIO_SVG)
        with open(os.path.join(directory, "preview.html"), "w", encoding="utf-8") as handle:
            handle.write(preview)
    with open(os.path.join(str(work), "keepme.txt"), "w", encoding="utf-8") as handle:
        handle.write(CANARY)
    return state


def _outside_state(work):
    """Everything under the repo that is NOT canonical state — what a freeze may never touch."""
    return {key: value for key, value in _tree_state(str(work)).items()
            if not key.replace("\\", "/").startswith("project_memory/")}


@pytest.mark.parametrize("command", sorted(cli.FREEZE_COMMANDS))
def test_no_freeze_parameter_can_reach_outside_the_state_root(tmp_path, command):
    """THE MECHANISM, not two parameter names: a freeze body arrives on STDIN, so no hook sees it —
    `gate_write_scope` reads command LINES — and every freeze ends in
    `clear_staging(..., mode="promoted")`, which is `shutil.rmtree(<root>/staging/<key>)`.

    Measured before `staging.contained_child`: `{"staging_key": "../.."}` on stdin DELETED THE
    WHOLE REPOSITORY (`.git`, `.claude`, `scripts`, everything), `".."` deleted the whole state
    directory, and `freeze-design` with an absolute `source_name` copied any file on the disk into
    `design/revisions/` and pointed the root's `design_refs` at it — all three command lines
    passing all eight registered shell gates.

    THE PARAMETER SET IS DERIVED from `cli.freeze_parameters`, so the next freeze parameter that
    happens to reach a path join is covered on the day it is written. Every `str` parameter of the
    command is substituted in turn with every escape shape, and FOUR universal invariants are
    asserted, none of which needs to know which parameter is path-bearing:
      * the repo outside the state directory is unchanged — same files, same hashes;
      * a sibling directory outside the repo is unchanged;
      * the root ITEM still exists (this is what `staging_key: ".."` destroyed: the whole state
        directory, which the first two checks cannot see because they look past it);
      * nothing from outside got IN — the canary content appears in no file under the state root,
        which is the `source_name` case a deletion check cannot see.
    """
    sibling = os.path.join(str(tmp_path), "sibling")
    contract = cli.freeze_parameters(cli.FREEZE_COMMANDS[command])
    for name, (_required, declared) in sorted(contract.items()):
        if declared is not str:
            continue
        for escape in ("..", "../..", r"..\..", "sub/deep", "../../../preview.html",
                       os.path.join(sibling, "preview.html")):
            work = tmp_path / ("%s-%s-%s" % (command, name, abs(hash(escape))))
            os.makedirs(str(work), exist_ok=True)
            state = _freeze_fixture(work, sibling)
            before, before_sibling = _outside_state(work), _tree_state(sibling)

            body = {key: value for key, value in VALID_FREEZE_BODY.items() if key in contract}
            body[name] = escape
            run_cli_with_body(state, json.dumps(body), command)

            where = "%s %s=%r" % (command, name, escape)
            assert _outside_state(work) == before, "%s changed the repo outside the state dir" % where
            assert _tree_state(sibling) == before_sibling, "%s changed a sibling directory" % where
            assert os.path.isfile(state.active_path("PR-0001")), (
                "%s destroyed canonical state" % where)
            for current, _dirs, files in os.walk(state.root):
                for entry in files:
                    with open(os.path.join(current, entry), encoding="utf-8",
                              errors="ignore") as handle:
                        assert CANARY not in handle.read(), (
                            "%s pulled a file from outside the state root into %s" % (where, entry))


def test_the_freeze_refusal_names_the_parameter_a_role_typed(state, capsys):
    """The refusal has to be actionable: a role that typed `staging_key: "../.."` needs to read
    which field it was, not `[Errno 2]`."""
    stage_file(state, "PR-0001", "WFR-0001.drawio.svg")
    body = {"staging_key": "../..", "wfr_id": "WFR-0001", "scope_apr_ref": None,
            "derives_from": ["PR-0001"], "title": "t"}
    assert run_cli_with_body(state, json.dumps(body), "freeze-wireframe") == 1
    err = capsys.readouterr().err
    assert "staging key" in err and "single name" in err


def test_a_nullable_companion_field_may_be_sent_as_null(state, capsys):
    """`freeze_wireframe` takes `scope_apr_ref` as a REQUIRED parameter whose companion field is
    `nullable: true` — so "no scope approval yet" must have a spelling. The body check is about
    SHAPE (a list stays a list); nullability is the strict companion schema's question, and the
    first cut of `_freeze_body` refused this legitimate body."""
    pr = state.capture("PR", dict(PR_FIELDS))
    stage_file(state, pr["id"], "WFR-0001.drawio.svg")
    assert run_cli_with_body(state, json.dumps({
        "staging_key": pr["id"], "wfr_id": "WFR-0001", "scope_apr_ref": None,
        "derives_from": [pr["id"]], "title": "Checkout"}), "freeze-wireframe") == 0
    assert "design/wireframes/WFR-0001.r01.drawio.svg" in capsys.readouterr().out
