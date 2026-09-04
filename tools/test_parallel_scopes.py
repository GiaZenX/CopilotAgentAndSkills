#!/usr/bin/env python3
"""The pre-dispatch scope check (`kernel.scopes`, `check-scopes`) -- DEC-0062 (1)/(2)/(5).

Every verdict here is measured on ORDERS THE KERNEL WROTE and on the command run as a PROCESS: the
question is whether a cut holds, and a cut is made of stored work orders, not of dictionaries a
test happens to build.
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEAM_KITS = os.path.join(ROOT, "team-kits")
sys.path.insert(0, TEAM_KITS)

from conftest import approve  # noqa: E402 -- the sanctioned approval walker
from kernel import dispatch, scopes  # noqa: E402
from kernel.state import ProjectState  # noqa: E402

PR_FIELDS = {
    "title": "Checkout flow", "class": "normal", "problem": "no checkout",
    "goal": "working checkout",
    "acceptance_criteria": [{"id": "AC-1", "text": "order completes"}],
    "invariants": [], "out_of_scope": [], "priority": "high",
}


def _project(tmp_path):
    """A state directory inside a real git repository -- the tree half needs one to answer."""
    repo = str(tmp_path)
    os.makedirs(repo, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    os.makedirs(os.path.join(repo, "project_memory"), exist_ok=True)
    return repo, ProjectState(os.path.join(repo, "project_memory"))


def _order(state, root_id, allowed, forbidden=(), seam=None):
    """One work order, written THROUGH the kernel -- a hand-rolled file would measure a fixture."""
    fields = {
        "product_requirement": root_id, "derives_from": root_id, "type": "implementation",
        "assigned_role": "backend-developer", "acceptance_refs": ["AC-1"], "required_inputs": [],
        "allowed_scope": list(allowed), "forbidden_scope": list(forbidden),
        "expected_outputs": ["x"], "dependencies": [],
    }
    if seam is not None:
        fields[scopes.SEAM_FIELD] = list(seam)
    return dispatch.create_task(state, fields)


def _run(repo, *args):
    """`check-scopes` as a PROCESS on the kernel's own surface -- (rc, stdout)."""
    env = dict(os.environ, PYTHONPATH=TEAM_KITS)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "check-scopes",
         *args],
        cwd=repo, capture_output=True, text=True, env=env, timeout=120)
    return result.returncode, result.stdout + result.stderr


def _two_orders(tmp_path, first, second, **kwargs):
    repo, state = _project(tmp_path)
    root = state.capture("PR", dict(PR_FIELDS))
    approve(state, root["id"], "scope")
    _order(state, root["id"], first, seam=kwargs.get("seam_a"))
    _order(state, root["id"], second, seam=kwargs.get("seam_b"))
    return repo, state


def test_two_orders_with_the_same_scope_are_refused_and_disjoint_ones_are_not(tmp_path):
    """C-1, both directions in one test -- separately either half passes on a stuck check.

    RED WITHOUT THE FIX: without the command there is no `check-scopes` on the parser at all, so
    the process exits 2 with an argparse usage error and the disjoint half fails.
    """
    repo, _state = _two_orders(tmp_path, ["team-kits/kernel/**"], ["team-kits/kernel/**"])
    code, output = _run(repo)
    assert code == 2, output
    assert "OVERLAP" in output and "TSK-0001" in output and "TSK-0002" in output

    other, _state = _two_orders(tmp_path / "b", ["team-kits/kernel/**"], ["docs/**"])
    code, output = _run(other)
    assert code == 0, output
    assert "disjoint" in output


def test_an_overlap_that_exists_only_in_an_empty_directory_is_still_an_overlap(tmp_path):
    """C-1, the witness half: a stream that will CREATE the file owns nothing there today.

    The tree half alone is blind to exactly the collision that hurts most -- two orders that both
    claim a directory neither has written into yet -- so this plants a scope no file matches and
    asserts the refusal anyway.

    RED WITHOUT THE FIX: with `witnesses` reduced to the empty list, the tree holds no file under
    `src/` at all and the pair reads as disjoint.
    """
    repo, _state = _two_orders(tmp_path, ["src/api/**"], ["src/**"])
    assert not os.path.isdir(os.path.join(repo, "src"))
    code, output = _run(repo)
    assert code == 2, output
    assert "witness" in output and "src/" in output


def test_a_declared_seam_on_both_orders_is_shared_on_purpose(tmp_path):
    """C-4: the seam lives on the ITEM, so the cut a project wrote down is the cut it is judged on.

    RED WITHOUT THE FIX (measured): with the seam not subtracted in `scopes.overlaps` the pair is
    an OVERLAP and this is rc 2. NOT what makes it red, measured rather than assumed: removing the
    field from `OPTIONAL_FIELDS["TSK"]` changes nothing here -- the kernel stores an undeclared
    field without complaint (`state.py` says so about `update_item`, and `capture` is no stricter),
    so what the contract entry buys is the DECLARATION and not a refusal. That half is held by
    `test_the_seam_field_is_declared_once_and_read_from_there`.
    """
    repo, _state = _two_orders(tmp_path, ["docs/**", "team-kits/kernel/**"],
                               ["docs/**", "tools/**"],
                               seam_a=["docs/**"], seam_b=["docs/**"])
    code, output = _run(repo)
    assert code == 0, output
    assert "seam" in output and "disjoint" in output

    # ...and the same pair without the declaration is the refusal it was
    bare, _state = _two_orders(tmp_path / "bare", ["docs/**", "team-kits/kernel/**"],
                               ["docs/**", "tools/**"])
    code, output = _run(bare)
    assert code == 2, output


def test_a_seam_only_one_of_the_two_declares_is_not_a_seam(tmp_path):
    """The fail-closed half of `scopes.pair_seam`, and the reason it is fail-closed.

    A seam is a file NO stream can own alone (DEC-0062 (5)). If one order declares `docs/**` and
    the other simply owns it, the second was cut believing the file was its own -- which is the
    surprise the seam table exists to prevent. So one-sided is not declared.

    RED WITHOUT THE FIX: with `pair_seam` taking the UNION of the two declarations, this pair reads
    as a seam and the check reports disjoint on a cut that is not.
    """
    repo, _state = _two_orders(tmp_path, ["docs/**"], ["docs/**"], seam_a=["docs/**"])
    code, output = _run(repo)
    assert code == 2, output
    assert "OVERLAP" in output


def test_a_seam_the_two_orders_spell_differently_is_still_one_seam(tmp_path):
    """N1 of rework 2: `Docs/**` and `docs/**` are one entry, so the pair has a seam.

    RED WITHOUT THE FIX: `pair_seam` intersected the two `seam_scope` lists as raw strings, so the
    declaration matched nothing and the pair came back rc 2 as an ordinary OVERLAP -- fail-closed,
    but the reader was sent to fix a collision instead of a spelling.

    THE COUNTER-ASSERTION keeps it from passing by everything becoming a seam: the same pair with
    a seam neither order declares is still refused.
    """
    seamed, _state = _two_orders(tmp_path,
                                 ["docs/**", "team-kits/kernel/**"],
                                 ["docs/**", "tools/**"],
                                 seam_a=["Docs/**"], seam_b=["docs/**"])
    code, output = _run(seamed)
    assert code == 0, output
    assert "seam only" in output and "disjoint" in output

    bare, _state = _two_orders(tmp_path / "bare",
                               ["docs/**", "team-kits/kernel/**"],
                               ["docs/**", "tools/**"])
    assert _run(bare)[0] == 2


def test_the_matcher_is_the_shipped_gates_own_and_not_a_second_spelling():
    """`kernel.scopes` asks the gate the specialists really meet -- read off the module, not the text.

    BOTH HALVES, and the second one is the measured defect: the gate never calls its predicate on
    unfolded text (`_scope_entries` folds every entry, `_repo_relative(fold=True)` folds the path),
    so asking `_matches` raw answers a different question. This asserts identity of the two FUNCTION
    OBJECTS, then a behaviour only that predicate has (a single `*` does not cross a separator while
    `**` does), then the folding itself.
    """
    matches, gate = scopes.matcher()
    assert gate.endswith(os.path.join("hooks", "gate_write_scope.py"))
    sys.path.insert(0, os.path.dirname(gate))
    import gate_write_scope
    shipped_matches, shipped_norm, _where = scopes._shipped_halves()
    assert shipped_matches is gate_write_scope._matches
    assert shipped_norm is gate_write_scope._norm
    assert matches("src/a/b.py", "src/**") and not matches("src/a/b.py", "src/*")
    assert matches("Tools/x.py", "tools/**"), "the gate folds both sides; so must this"


def test_a_case_only_difference_is_the_same_ownership_the_gate_grants(tmp_path):
    """M1 of rework 1, end to end: `Tools/**` and `tools/**` are one scope to the gate.

    RED WITHOUT THE FIX: with `matcher` handing back the raw `_matches`, this pair comes back
    `disjoint` at rc 0 -- while `gate_write_scope` lets both orders write the same file, which is
    the collision the check exists to predict.
    """
    repo, _state = _two_orders(tmp_path, ["Tools/**"], ["tools/**"])
    os.makedirs(os.path.join(repo, "tools"), exist_ok=True)
    with open(os.path.join(repo, "tools", "x.py"), "w", encoding="utf-8") as handle:
        handle.write("# a real file both orders own" + chr(10))
    code, output = _run(repo)
    assert code == 2, output
    assert "tools/x.py" in output


def test_a_seam_that_leaves_an_order_owning_nothing_is_refused(tmp_path):
    """N3 of rework 1, both ends: a declaration is a shared FILE, not a handed-over scope.

    END ONE -- `**` on both orders (or on the command line) used to turn every collision into
    "seam only" and the check reported rc 0 on a cut that is entirely shared. It is refused now,
    and the line says why rather than only that.

    END TWO -- the legitimate seam stays legitimate: an order owning the kernel and declaring
    `team-kits/*/VERSION` still owns the kernel afterwards, so that pair passes. Without this half
    the rule would be "a wide seam is forbidden", which would have refused the real generation-3
    seam.
    """
    swallowed, _state = _two_orders(tmp_path, ["team-kits/kernel/**"], ["team-kits/kernel/**"],
                                    seam_a=["**"], seam_b=["**"])
    code, output = _run(swallowed)
    assert code == 2, output
    assert "NOT A SEAM" in output and "owning nothing" in output

    flagged, _state = _two_orders(tmp_path / "flag", ["team-kits/kernel/**"],
                                  ["team-kits/kernel/**"])
    code, output = _run(flagged, "--seam", "**")
    assert code == 2, output

    real, _state = _two_orders(tmp_path / "real",
                               ["team-kits/kernel/**", "team-kits/*/VERSION"],
                               ["team-kits/dev-team/hooks/**", "team-kits/*/VERSION"],
                               seam_a=["team-kits/*/VERSION"], seam_b=["team-kits/*/VERSION"])
    code, output = _run(real)
    assert code == 0, output
    assert "seam" in output and "NOT A SEAM" not in output


def test_a_state_with_nothing_to_compare_never_says_disjoint(tmp_path):
    """Nothing measured and everything fine are different answers, and they share no word.

    A missing task tray, one open order and a mistyped `--root` all land here; reporting "disjoint"
    for any of them would be the check telling a caller its cut holds when nothing was read.
    """
    repo, state = _project(tmp_path)
    code, output = _run(repo)
    assert code == 0 and "NOTHING WAS COMPARED" in output and "disjoint" not in output

    root = state.capture("PR", dict(PR_FIELDS))
    approve(state, root["id"], "scope")
    _order(state, root["id"], ["docs/**"])
    code, output = _run(repo)
    assert code == 0 and "NOTHING WAS COMPARED" in output and "disjoint" not in output


def test_a_terminal_order_is_not_part_of_the_cut(tmp_path):
    """"Open" is `is_terminal` and not a status word: a cancelled order owns nothing any more."""
    repo, state = _project(tmp_path)
    root = state.capture("PR", dict(PR_FIELDS))
    approve(state, root["id"], "scope")
    first = _order(state, root["id"], ["team-kits/kernel/**"])
    _order(state, root["id"], ["team-kits/kernel/**"])
    assert _run(repo)[0] == 2
    state.transition(first["id"], "CANCELLED")
    code, output = _run(repo)
    assert code == 0 and "NOTHING WAS COMPARED" in output, output


def test_the_seam_field_is_frozen_with_the_rest_of_the_work_order(tmp_path):
    """C-4's consequence, asserted rather than left to be discovered.

    A seam added to a LEASED order re-decides a cut that has already been handed out, so the field
    rides in `TSK_PLAN_FIELDS` with `allowed_scope`. Declaring one later stays legitimate -- it
    just has to be visible, which is what the freeze forces.
    """
    from kernel.backlog_types import TSK_PLAN_FIELDS
    from kernel.state import StateError

    assert scopes.SEAM_FIELD in TSK_PLAN_FIELDS
    repo, state = _project(tmp_path)
    root = state.capture("PR", dict(PR_FIELDS))
    approve(state, root["id"], "scope")
    task = _order(state, root["id"], ["docs/**"])
    state.transition(task["id"], "READY")
    with pytest.raises(StateError, match="frozen outside"):
        state.update_item(task["id"], {scopes.SEAM_FIELD: ["docs/**"]})


def _mini_install(repo):
    """The two directories a scaffold puts under `.claude/` -- hooks and kernel, nothing else.

    Enough for the shipped entry point to resolve a kernel (`scripts/harness.py` refuses a project
    without an enforcement layer, which is the check this borrows rather than defeats). Built here
    rather than by running the scaffold, because the scaffold installs agents, settings and a
    constitution this test has no use for.
    """
    installed = os.path.join(repo, ".cl" "aude")
    shutil.copytree(os.path.join(TEAM_KITS, "dev-team", "hooks"),
                    os.path.join(installed, "hooks"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(os.path.join(TEAM_KITS, "kernel"), os.path.join(installed, "kernel"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    os.makedirs(os.path.join(repo, "scripts"), exist_ok=True)
    shutil.copyfile(
        os.path.join(TEAM_KITS, "dev-team", "templates", "repo", "scripts", "harness.py"),
        os.path.join(repo, "scripts", "harness.py"))


def test_the_verb_runs_through_the_shipped_entry_point(tmp_path):
    """C-1's own wording: the verb as a PROCESS through `scripts/harness.py`, not only through the
    kernel module.

    That entry point is the only route a project has -- a script under a skill directory is rc 2 at
    `gate_write_scope` (`H136`) -- so a verb that worked in the module and not through the shim
    would be a verb no project could run. The shim forwards argv to the kernel parser, which is
    exactly what this measures: the same two orders, the same two exit codes.
    """
    repo, state = _project(tmp_path)
    root = state.capture("PR", dict(PR_FIELDS))
    approve(state, root["id"], "scope")
    # Each order keeps something of its own outside the seam -- a declaration that left one of
    # them owning nothing is not a seam (`scopes.owns_anything_outside`).
    _order(state, root["id"], ["docs/**", "team-kits/kernel/**"], seam=["docs/**"])
    _order(state, root["id"], ["docs/**", "tools/**"])
    _mini_install(repo)

    def shim(*args):
        result = subprocess.run([sys.executable, os.path.join("scripts", "harness.py"),
                                 "check-scopes", *args],
                                cwd=repo, capture_output=True, text=True, timeout=120)
        return result.returncode, result.stdout + result.stderr

    code, output = shim()
    assert code == 2, output
    assert "OVERLAP" in output
    code, output = shim("--seam", "docs/**")
    assert code == 0, output
    assert "disjoint" in output


def test_the_check_command_is_on_the_shipped_parser():
    """The surface itself, so "the module works" cannot pass for "a project can run it"."""
    from kernel.cli import build_parser

    choices = build_parser()._subparsers._group_actions[0].choices
    assert "check-scopes" in choices
    assert json.dumps(sorted(choices)).count("check-scopes") == 1


def test_the_seam_field_is_declared_once_and_read_from_there():
    """The field name has one home, and the check reads it from there rather than spelling it.

    BOTH ENDS, because a field name in two places is the drift this repo keeps removing: the
    contract of `TSK` declares it, and `kernel.scopes.SEAM_FIELD` is that same string -- so a
    renamed field takes its reader with it instead of leaving a check that silently reads nothing.

    WHAT THIS DOES NOT CLAIM, measured: nothing refuses a work order carrying an UNDECLARED field.
    A `TSK` captured with `seam_scope` while the contract does not name it is stored and passes
    `validate_state` without a finding. So the declaration is what a reader and the flag surface
    point at, not a wall -- and the wall the seam really has is the freeze
    (`test_the_seam_field_is_frozen_with_the_rest_of_the_work_order`).
    """
    from kernel.backlog_types import OPTIONAL_FIELDS, REQUIRED_FIELDS

    assert scopes.SEAM_FIELD in OPTIONAL_FIELDS["TSK"]
    assert scopes.SEAM_FIELD not in REQUIRED_FIELDS["TSK"], (
        "most orders share nothing, so a required seam would be a field every planner types to "
        "say 'none'")
