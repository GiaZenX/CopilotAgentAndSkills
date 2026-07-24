"""Tests for staging/freeze operations + the harness CLI (spec II.4/II.6a, step 1.6)."""
import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits"))

from kernel import cli, staging  # noqa: E402
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
