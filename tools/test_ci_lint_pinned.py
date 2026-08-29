#!/usr/bin/env python3
"""BUG-0007: the repo's own lint must be a CHOSEN rule set run at a PINNED ruff version.

WHY THIS IS THE RIGHT SUBJECT, and not "does ruff pass today". Two independent knobs decide what
`ruff check` reports, and both were left to chance:

  * ruff.toml set no `select`, so ruff linted with whatever DEFAULT rule set the installed version
    ships -- an inherited set, not a chosen one. A ruff upgrade then changes the findings by itself.
  * the CI workflow installed bare `ruff`, so the version drifted to whatever release was current.

Either alone makes two runs of the same CI on the same commit disagree. Measured on team-kits+tools
with the OLD select-less config: 37 findings under ruff 0.15.20, 3760 under 0.16.0 and 0.16.1 -- the
same config, three answers. With an explicit `select` the same three versions all report the same
set (37 E402, every one under a hooks/ dir the per-file-ignore covers -> green). The pin freezes the
version; the explicit select freezes the rule set; together two runs are identical.

Each check reads the part that RUNS -- the toml ruff parses and the run: line CI executes -- never a
string search over prose.

The workflow check below joined them for the same reason one level up (BUG-0069): what the runner
CHECKS OUT decides what the suite can measure there, and a depth the workflow leaves to the default
is as much an unpinned knob as an unpinned ruff version was.
"""
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib

import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUFF_TOML = os.path.join(ROOT, "ruff.toml")
CI_YML = os.path.join(ROOT, ".github", "workflows", "ci.yml")

# A pip requirement pinning ruff to one exact version, e.g. `ruff==0.15.20`. `==` is the only
# operator that yields ONE version; `>=`/`~=`/bare `ruff` all leave the resolved version to chance,
# which is the drift this test exists to forbid.
_RUFF_PIN = re.compile(r"""ruff==(\d+(?:\.\d+)*)""")


def _ci_run_lines():
    """Every shell line inside the CI workflow's `run:` steps, from the YAML CI actually executes."""
    with open(CI_YML, encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)
    lines = []
    for job in workflow.get("jobs", {}).values():
        for step in job.get("steps", []):
            run = step.get("run")
            if run:
                lines.extend(run.splitlines())
    return lines


def _ruff_pins():
    """Every exact ruff version the CI workflow pins, in order of appearance.

    `finditer`, not `search`: two pins on ONE `pip install` line (`ruff==A ruff==B`) is the natural
    shape of a disagreeing pin, and `search` would see only the first and call it singular.
    """
    return [match.group(1) for line in _ci_run_lines() for match in _RUFF_PIN.finditer(line)]


def test_root_ruff_select_is_explicit_not_inherited():
    """Red while ruff.toml carries no non-empty [lint] select (the inherited-set half of BUG-0007)."""
    with open(RUFF_TOML, "rb") as fh:
        config = tomllib.load(fh)
    select = config.get("lint", {}).get("select")
    assert isinstance(select, list) and select, (
        "ruff.toml sets no non-empty [lint] select, so ruff lints with whatever default rule set the "
        "installed version ships -- a ruff upgrade then silently changes the findings (BUG-0007). "
        "Choose the rule set explicitly, e.g. select = [\"E4\", \"E7\", \"E9\", \"F\"].")


def test_ci_pins_exactly_one_ruff_version():
    """Red while CI installs bare `ruff` (the drifting-version half of BUG-0007).

    Also red if ruff is pinned to two DIFFERENT versions: a version belongs at exactly one place,
    and a second, disagreeing pin is itself the defect (which run wins is then unpredictable).
    """
    pins = _ruff_pins()
    assert pins, (
        "the CI workflow installs ruff without an exact version (ruff==X.Y.Z), so each run inherits "
        "whatever ruff release is current and two runs of one commit can differ (BUG-0007).")
    assert len(set(pins)) == 1, (
        "ruff is pinned to more than one version in the CI workflow: %s -- one version, one place."
        % pins)


def test_two_disagreeing_pins_on_one_line_are_both_seen(monkeypatch):
    """The tripwire on `test_ci_pins_exactly_one_ruff_version`'s "second, disagreeing pin" promise.

    The natural shape of a double pin is `pip install "ruff==A" "ruff==B"` on ONE line. `_ruff_pins`
    once used `re.search`, which returns only the first match per line, so that line looked singular
    and the check above waved it through -- a docstring claiming protection the code did not build.
    `finditer` sees every pin. Red without the fix (search -> ['0.15.20']); green with it.
    """
    monkeypatch.setattr(sys.modules[__name__], "_ci_run_lines",
                        lambda: ['python -m pip install --upgrade pip "ruff==0.15.20" '
                                 '"ruff==0.16.2" pyyaml pytest'])
    pins = _ruff_pins()
    assert pins == ["0.15.20", "0.16.2"], (
        "a second, disagreeing ruff pin on the same pip line was not seen: %s" % pins)
    assert len(set(pins)) != 1, "two different same-line pins must not resolve to one version"


def _checkout_steps():
    """Every `actions/checkout` step in the workflow, from the YAML the runner executes."""
    with open(CI_YML, encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)
    return [step for job in workflow.get("jobs", {}).values() for step in job.get("steps", [])
            if str(step.get("uses") or "").split("@")[0] == "actions/checkout"]


def _commits_back_to_the_v1_fixture():
    """How many commits separate HEAD from the newest commit the migration fixture needs, or None.

    None when this cannot be measured here at all -- no git, no work tree, or a clone whose history
    has already been cut. Asking git rather than remembering a depth: the answer moves with every
    commit, and a remembered one is the claim that rots.
    """
    if not shutil.which("git"):
        return None
    import test_migrate
    probe = subprocess.run(["git", "-C", ROOT, "log", "--all", "--format=%H", "--",
                            test_migrate._V1_MARKER],
                           capture_output=True, text=True, timeout=120)
    commits = probe.stdout.split() if probe.returncode == 0 else []
    if not commits:
        return None
    distance = subprocess.run(["git", "-C", ROOT, "rev-list", "--count", "%s..HEAD" % commits[0]],
                              capture_output=True, text=True, timeout=120)
    return int(distance.stdout.strip()) if distance.returncode == 0 else None


def test_ci_checkout_fetches_the_history_the_suite_reads_as_a_fixture():
    """The hosted runners cloned at depth 1 and `tools/test_migrate.py` needs a much older commit.

    That module restores its "real V1 state" from the newest commit still carrying the V1 office
    template (`test_migrate._last_v1_commit`); a depth-1 checkout has no such commit, and the whole
    module then failed with "no real V1 state to migrate" -- three failures and 96 errors per
    platform in the run BUG-0069 was raised on, the single largest class in it.

    BOTH ENDS, so neither half can go stale quietly: the workflow must fetch the whole history, AND
    that commit must really be out of a shallow checkout's reach. The day the fixture no longer
    needs history, the second assertion says so instead of leaving an unexplained `fetch-depth` in
    the workflow for ever.
    """
    steps = _checkout_steps()
    assert steps, "the CI workflow checks out nothing -- this test's subject is gone"
    for step in steps:
        depth = (step.get("with") or {}).get("fetch-depth")
        assert str(depth) == "0", (
            "an actions/checkout step fetches depth %r, so the runner gets a shallow clone and "
            "tools/test_migrate.py cannot build the V1 state it measures against (BUG-0069). "
            "Remedy: `with: fetch-depth: 0`." % (depth,))
    distance = _commits_back_to_the_v1_fixture()
    if distance is None:
        pytest.skip("this checkout cannot say how deep the V1 fixture commit lies (no git, no "
                    "work tree, or a history already cut) -- the workflow half above still ran")
    assert distance > 1, (
        "the commit tools/test_migrate.py restores its V1 fixture from is only %d commit(s) back, "
        "so a default checkout would reach it and the `fetch-depth: 0` above no longer earns its "
        "place -- drop it, or say here what else needs the history" % distance)


def _pytest_invocations():
    """The CI run lines that RUN pytest -- pytest as the PROGRAM, not as a word on a line.

    `pip install ... pyyaml pytest` names it and runs nothing; a substring reader called that the
    test step and asked it for reporting flags. The program is the first word of the line or the
    one right after `-m`, which is how an interpreter reads it too.
    """
    found = []
    for line in _ci_run_lines():
        try:
            words = shlex.split(line, posix=True)
        except ValueError:
            continue
        for index, word in enumerate(words):
            program = word.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            if program == "pytest" and (index == 0 or words[index - 1] == "-m"):
                found.append(line)
                break
    return found


def test_ci_names_the_reason_for_every_skip_it_counts():
    """A skip is this suite saying it cannot measure something HERE; the log must say what.

    Several measurements are impossible on a hosted runner and now say so as an explicit skip
    rather than as a red (BUG-0069): the null-device spellings, the case-flip on a case-sensitive
    filesystem, the `.ps1` installer without a PowerShell, the parser that does not recurse inside
    the item budget. Under `-q` alone the run prints only "N skipped", so a test that quietly
    stopped measuring is indistinguishable from one that honestly could not -- which is the defect
    this repo documents against itself. `-rs` puts every reason in the log the failure mail points
    at.

    The pytest step is found by what it RUNS, not by its name, and the flag is read as pytest reads
    it: `-r` takes a set of characters, so `-rs`, `-rsx` and `-ra` all name skips.
    """
    invocations = _pytest_invocations()
    assert invocations, "the CI workflow runs no pytest -- this test's subject is gone"
    for line in invocations:
        chosen = set("".join(re.findall(r"(?:^|\s)-r([a-zA-Z]+)", line)))
        assert chosen & set("sa"), (
            "the CI pytest step reports no skip reasons (%r), so the hosted log says only how many "
            "measurements were skipped and never which, or why. Remedy: add `-rs`." % line)


def _installed_ruff_version():
    """The version of the ruff this interpreter can run, or None if ruff is not importable/runnable."""
    proc = subprocess.run([sys.executable, "-m", "ruff", "--version"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    match = re.search(r"(\d+(?:\.\d+)+)", proc.stdout)
    return match.group(1) if match else None


def test_ruff_is_green_and_reproducible_at_the_pinned_version():
    """Executable proof that the pinned version + explicit select give a stable, green result.

    This RUNS ruff exactly as CI does (`ruff check team-kits tools`), twice, and asserts both runs
    are byte-identical AND green. It is the 'select basis == pinned version' clause: the pin is
    chosen for a version the select is green under, so bumping the pin to a version where the select
    is no longer green turns this red.

    It skips honestly when it cannot measure -- ruff absent, or the installed ruff is not the pinned
    one (it cannot prove a version it does not have). The two parse-level checks above carry the
    version-independent red-without-fix duty; this one is the reproducibility measurement.
    """
    pins = set(_ruff_pins())
    if len(pins) != 1:
        pytest.skip("ruff version pin is not singular (covered by test_ci_pins_exactly_one_ruff_version)")
    pinned = next(iter(pins))
    installed = _installed_ruff_version()
    if installed is None:
        pytest.skip("ruff is not runnable in this environment")
    if installed != pinned:
        pytest.skip("installed ruff %s is not the pinned %s -- cannot prove a version we lack"
                    % (installed, pinned))
    cmd = [sys.executable, "-m", "ruff", "check", "team-kits", "tools"]
    first = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    second = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    assert first.returncode == 0, (
        "ruff %s is not green under the repo's explicit select -- the pin and the select basis have "
        "drifted apart:\n%s" % (pinned, first.stdout))
    assert first.stdout == second.stdout and first.returncode == second.returncode, (
        "two runs of the same ruff on the same tree disagreed -- output is not reproducible")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
