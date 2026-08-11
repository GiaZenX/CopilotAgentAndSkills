#!/usr/bin/env python3
"""Repo hygiene: git must not TRACK a file it also IGNORES.

WHY THIS IS THE RIGHT SUBJECT, and not "is ModuleAnalysisCache absent". A `.gitignore` rule has no
effect on a path git already tracks, so a tool trace that was committed once (a PowerShell module
cache under `Microsoft/`, a kit audit log under `project_memory/.audit/` -- both in b32ec98) stays
in every future commit no matter how many rules name it. That is precisely the state BUG-0008 was
in: the rule existed and the file was tracked anyway, so the rule was a promise the tree did not
keep. The invariant that catches it is git's own: the set of TRACKED files and the set of
IGNORED files must be disjoint. Measured with `git ls-files --cached --ignored --exclude-standard`,
which is git resolving `.gitignore` against its own index -- the running behaviour, not a string
search over the file.

THE ONE EXCLUSION IS SCOPED AND REASONED, not an allowlist of paths. `project_memory/` is canonical
state under gate 1 (`gate_lead_write_scope.py`), which refuses every tool write there for every
caller, so a `project_memory/.audit/hook_events.jsonl` that a kit hook subprocess committed cannot
be untracked from a harness session -- `git rm --cached` on it is refused before it runs. It is the
open remainder H37 Rest 2 in `docs/POST_V2_WISHLIST.md`, and the repair belongs in the kit. Anything
tracked-and-ignored OUTSIDE that tree is a new tool trace that must be untracked.
"""
import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _tracked_and_ignored():
    """Paths git both TRACKS and IGNORES, straight from git's own index/attribute resolution."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--ignored", "--exclude-standard"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert result.returncode == 0, result.stderr
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_git_tracks_no_ignored_file_outside_canonical_state():
    """A tracked-and-ignored file is a dead ignore rule (BUG-0008): the file ships regardless.

    Goes red while `Microsoft/Windows/PowerShell/ModuleAnalysisCache` is tracked, which is the
    exact state the `Microsoft/` rule was added into and could not fix on its own -- the file had
    to be untracked (`git rm --cached`) for the rule to mean anything. `project_memory/` is excluded
    because it is gate-protected canonical state a harness session cannot untrack (H37).
    """
    if not shutil.which("git"):
        pytest.skip("git not on PATH")
    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT,
                      capture_output=True, text=True).returncode != 0:
        pytest.skip("not a git work tree")
    offenders = [path for path in _tracked_and_ignored()
                 if not path.startswith("project_memory/")]
    assert not offenders, (
        "git tracks these files while a .gitignore rule ignores them, so the rule is a no-op and "
        "the tool trace ships in every commit -- untrack each with `git rm --cached <path>`: %s"
        % offenders)


def test_the_known_out_of_scope_trace_is_still_the_only_exception():
    """The tripwire on the exclusion above, so it cannot quietly widen or go stale.

    The exclusion earns its place only as long as the audit log is the one thing it covers. If that
    file gets untracked in the kit (H37 closed), this asserts the exception is no longer needed and
    should be removed; if a SECOND ignored file appears under project_memory/, it surfaces here
    rather than hiding behind the prefix.
    """
    if not shutil.which("git"):
        pytest.skip("git not on PATH")
    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT,
                      capture_output=True, text=True).returncode != 0:
        pytest.skip("not a git work tree")
    excused = [path for path in _tracked_and_ignored()
               if path.startswith("project_memory/")]
    assert excused == ["project_memory/.audit/hook_events.jsonl"], (
        "the project_memory/ exclusion in test_git_tracks_no_ignored_file_outside_canonical_state "
        "no longer covers exactly the audit log H37 names -- update the exclusion and H37: %s"
        % excused)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
