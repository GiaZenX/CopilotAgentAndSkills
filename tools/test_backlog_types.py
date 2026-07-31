"""Tests for the status automata + V1 mapping (HARNESS_V2_SPEC.md II.2 / II.10 / II.12)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "team-kits"))

from kernel.backlog_types import (  # noqa: E402
    AUTOMATA,
    INVALIDATION_TARGET,
    TransitionError,
    UnknownV1Status,
    assert_transition,
    format_id,
    initial_status,
    invalidation_target,
    is_terminal,
    map_v1_status,
    parse_id,
)


# -- chains and terminals ------------------------------------------------------

def test_every_chain_edge_is_allowed():
    for item_type, auto in AUTOMATA.items():
        for src, dst in zip(auto.chain, auto.chain[1:]):
            assert_transition(item_type, src, dst)  # must not raise


def test_all_edge_endpoints_are_registered_states():
    """Fable-Check 5: a typo'd edge must be impossible, not a dead edge."""
    for item_type, auto in AUTOMATA.items():
        for src, dst in auto.allowed:
            assert src in auto.states and dst in auto.states, (item_type, src, dst)


def test_terminals_have_no_outgoing_edges():
    for item_type, auto in AUTOMATA.items():
        for terminal in auto.terminals:
            assert is_terminal(item_type, terminal)
            outgoing = [e for e in auto.allowed if e[0] == terminal]
            assert outgoing == [], (item_type, terminal, outgoing)


def test_initial_states():
    assert initial_status("PR") == "DRAFT"
    assert initial_status("RQ") == "DRAFT"
    assert initial_status("FR") == "OPEN"
    assert initial_status("BUG") == "OPEN"
    assert initial_status("SR") == "PROPOSED"
    assert initial_status("TSK") == "DRAFT"
    assert initial_status("PROC") == "DRAFT"
    assert initial_status("HYP") == "PROPOSED"
    assert initial_status("EXP") == "DESIGNED"


# -- II.12 named cases ---------------------------------------------------------

def test_tsk_draft_to_in_progress_direct_is_blocked():
    """II.12: 'ungueltiger Statusuebergang (z. B. TSK DRAFT->IN_PROGRESS direkt) -> Block'."""
    with pytest.raises(TransitionError):
        assert_transition("TSK", "DRAFT", "IN_PROGRESS")


def test_tsk_back_edges():
    assert_transition("TSK", "LEASED", "READY")        # lease timeout / spawn failure
    assert_transition("TSK", "IN_PROGRESS", "FAILED")
    assert_transition("TSK", "SUBMITTED", "FAILED")
    assert_transition("TSK", "DONE", "FAILED")
    assert_transition("TSK", "FAILED", "READY")        # approved retry
    assert_transition("TSK", "FAILED", "CANCELLED")


def test_tsk_validated_only_from_done():
    assert_transition("TSK", "DONE", "VALIDATED")
    for src in ("DRAFT", "READY", "LEASED", "IN_PROGRESS", "SUBMITTED", "FAILED"):
        with pytest.raises(TransitionError):
            assert_transition("TSK", src, "VALIDATED")


def test_tsk_terminals_are_terminal():
    for terminal in ("VALIDATED", "CANCELLED"):
        with pytest.raises(TransitionError):
            assert_transition("TSK", terminal, "READY")


def test_bug_verified_only_from_fixed():
    assert_transition("BUG", "FIXED", "VERIFIED")
    with pytest.raises(TransitionError):
        assert_transition("BUG", "TRIAGED", "VERIFIED")


def test_pr_accepted_only_from_delivered():
    assert_transition("PR", "DELIVERED", "ACCEPTED")
    with pytest.raises(TransitionError):
        assert_transition("PR", "APPROVED", "ACCEPTED")


def test_fr_terminal_requires_triage():
    with pytest.raises(TransitionError):
        assert_transition("FR", "OPEN", "MERGED")
    assert_transition("FR", "TRIAGED", "CONVERTED")


def test_blocked_is_not_a_status_anywhere():
    for item_type, auto in AUTOMATA.items():
        assert "BLOCKED" not in auto.states, item_type
        with pytest.raises(TransitionError):
            assert_transition(item_type, auto.initial, "BLOCKED")


def test_unknown_type_and_status_fail_closed():
    with pytest.raises(TransitionError):
        assert_transition("XXX", "DRAFT", "APPROVED")
    with pytest.raises(TransitionError):
        assert_transition("PR", "DRAFT", "SHIPPED")


# -- invalidation table (spec II.2) --------------------------------------------

def test_invalidation_targets_match_spec_table():
    assert INVALIDATION_TARGET == {
        "PR": "DRAFT",
        "RQ": "DRAFT",
        "CR": "DRAFT",
        "PROC": "DRAFT",
        "BUG": "TRIAGED",
        "SR": "PROPOSED",
        "EXP": "DESIGNED",
    }


def test_hyp_has_no_invalidation_target():
    """Spec II.2: HYP deliberately absent -- no approval_ref, rides on RQ scope."""
    with pytest.raises(KeyError):
        invalidation_target("HYP")


def test_invalidation_targets_are_valid_states():
    for item_type, target in INVALIDATION_TARGET.items():
        assert target in AUTOMATA[item_type].states


# -- id convention -------------------------------------------------------------

def test_id_roundtrip():
    assert format_id("TSK", 42) == "TSK-0042"
    assert parse_id("TSK-0042") == ("TSK", 42)
    assert parse_id("PR-12345") == ("PR", 12345)  # >4 digits allowed


def test_id_rejects_garbage():
    for bad in ("TSK42", "tsk-0042", "TSK-42", "XXX-0042", "", "PRD-0001"):
        with pytest.raises(ValueError):
            parse_id(bad)


# -- V1 -> V2 mapping (spec II.10) ---------------------------------------------

def test_v1_mapping_table():
    assert map_v1_status("TSK", "TODO") == ("TSK", "READY", False)
    assert map_v1_status("PRD", "TESTED") == ("PR", "DELIVERED", False)
    assert map_v1_status("PRD", "DONE") == ("PR", "ACCEPTED", True)
    assert map_v1_status("PRD", "PROPOSED") == ("PR", "DRAFT", False)
    assert map_v1_status("SR", "DRAFT") == ("SR", "PROPOSED", False)
    assert map_v1_status("SR", "ACTIVE") == ("SR", "ACCEPTED", False)
    assert map_v1_status("SR", "DONE") == ("SR", "ACCEPTED", True)
    assert map_v1_status("PROC", "PROPOSED") == ("PROC", "DRAFT", False)


def test_v1_mapping_targets_are_valid_v2_states():
    from kernel.backlog_types import V1_STATUS_MAPPING
    for (_v1t, _v1s), (v2t, v2s, _arch) in V1_STATUS_MAPPING.items():
        assert v2s in AUTOMATA[v2t].states, (v2t, v2s)


def test_unknown_v1_status_blocks():
    """Spec II.10: unknown values -> block + Decision item, never guess."""
    with pytest.raises(UnknownV1Status):
        map_v1_status("SR", "WEIRD_LEGACY_STATE")


# -- the Evidence vocabulary: one list, one derivation -------------------------

def test_the_delivery_judging_kinds_are_derived_from_the_kinds_not_listed_again():
    """`QA_EVIDENCE_KINDS` must be a SUBTRACTION, not a second spelling of the same words.

    The two constants held the same three words twice, and that shape has produced one defect per
    review round in this repo: a kind added to `EVIDENCE_KINDS` alone becomes a verdict a role can
    legally record and the merge gate never reads — `gate_git` would answer "no QA Evidence" for
    work that has some. Nothing was red about it, because both lists were internally consistent.

    So the assertion is on the SOURCE of the assignment, read from the parsed module rather than
    matched as text: whatever `QA_EVIDENCE_KINDS` is built from, it may not be the kind words
    themselves. The partition below is what the derivation then guarantees and what a reader can
    check against the one declared exception.
    """
    import ast
    from kernel.backlog_types import (EVIDENCE_KINDS, PROJECT_EVIDENCE_KINDS, QA_EVIDENCE_KINDS)
    assert QA_EVIDENCE_KINDS | PROJECT_EVIDENCE_KINDS == EVIDENCE_KINDS
    assert not (QA_EVIDENCE_KINDS & PROJECT_EVIDENCE_KINDS)
    source = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "team-kits", "kernel", "backlog_types.py")
    with open(source, encoding="utf-8") as handle:
        module = ast.parse(handle.read())
    assignments = [node for node in module.body if isinstance(node, ast.Assign)
                   and any(getattr(target, "id", None) == "QA_EVIDENCE_KINDS"
                           for target in node.targets)]
    assert len(assignments) == 1, "QA_EVIDENCE_KINDS is assigned %d times" % len(assignments)
    spelled = {node.value for node in ast.walk(assignments[0].value)
               if isinstance(node, ast.Constant) and node.value in EVIDENCE_KINDS}
    assert not spelled, (
        "QA_EVIDENCE_KINDS spells %s literally instead of deriving the set. A kind added to "
        "EVIDENCE_KINDS would then have to be remembered here too, and forgetting it is silent: "
        "the kind stays legal at capture and stops counting for the merge gate."
        % ", ".join(sorted(spelled)))
