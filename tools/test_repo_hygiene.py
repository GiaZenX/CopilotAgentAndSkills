#!/usr/bin/env python3
"""Repo hygiene: git must not TRACK a file it also IGNORES, and a file name must not lie about
whose report it holds.

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
import re
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH = os.path.join(ROOT, "docs", "research")


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


def _shipped_roles():
    """The role names this repo ships, off the kit's own skill directories — never typed here.

    Longest first, so a role whose name is a prefix of another cannot swallow the longer one when
    the two are searched as alternatives.
    """
    skills = os.path.join(ROOT, "team-kits", "dev-team", "skills")
    roles = [name for name in os.listdir(skills) if os.path.isdir(os.path.join(skills, name))]
    assert len(roles) > 3, roles
    return sorted(roles, key=len, reverse=True)


def _role_reports():
    """(file name, role the NAME claims) for every research report named after a shipped role."""
    roles = _shipped_roles()
    for name in sorted(os.listdir(RESEARCH)):
        if not name.endswith(".md") or not os.path.isfile(os.path.join(RESEARCH, name)):
            continue
        claimed = [role for role in roles if name[:-len(".md")].endswith(role)]
        if claimed:
            yield name, claimed[0]


def test_every_research_role_report_is_named_after_the_role_its_own_text_is_about():
    """FR-0009: five of these six carried the name of the NEXT role in the ring.

    THE CONTENT DECIDES, and the rule is one rule for all of them: the FIRST role name a report
    mentions is the role it is about. Every one of these reports opens by naming its subject — in a
    title (`# Rolle \\`product-designer\\``) or in the `Datei:`/`Gelesen:` line that says which
    SKILL.md was read — and the six shipped files agree with that reading unanimously today, which
    is what makes it a rule rather than a guess. The role vocabulary comes from the kit's skill
    directories, so a renamed or a new role moves this check with it.

    WHY A FILE NAME IS WORTH A TEST HERE. These reports are cited by role, opened by role, and
    nothing inside them repeats the file name — so a shifted name is silent: whoever looks up one
    role's findings reads the neighbour's and has no way to notice. The shift survived from
    2026-07-27 until this check, in a repo that measures nearly everything else.

    THE WAY OUT IS NOT OPEN TODAY, and claiming it was would be the over-alarming half of the same
    house rule. A report renamed to something that is not a role name does leave the subject — but
    as long as the shipped set is exactly the floor's size, the floor is an equality in effect and
    that rename trips it. The gap opens with the FIRST report ABOVE the floor, and then silently:
    the count still holds while the renamed one sits unjudged. Both directions are measured in
    `docs/reviews/2026-08-18-tsk0076-measurements.md`. So the floor counts, it does not identify —
    whoever adds a report above it inherits this sentence.
    """
    roles = _shipped_roles()
    pattern = re.compile("|".join(re.escape(role) for role in roles), re.IGNORECASE)
    reports, offences = list(_role_reports()), []
    for name, claimed in reports:
        with open(os.path.join(RESEARCH, name), encoding="utf-8") as handle:
            match = pattern.search(handle.read())
        found = match.group(0).lower() if match else None
        if found != claimed:
            offences.append(
                "%s is filed under `%s` and its own text is about `%s`" % (name, claimed, found))
    assert len(reports) >= 6, (
        "only %d research reports are named after a shipped role — the set was six when this was "
        "written, and a subject that shrinks to nothing is how this check passes over the next "
        "shift: %s" % (len(reports), [name for name, _ in reports]))
    assert not offences, (
        "a research report is filed under the wrong role, so looking up one role's findings hands "
        "over another's and nothing in the file says so:\n  " + "\n  ".join(offences))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
