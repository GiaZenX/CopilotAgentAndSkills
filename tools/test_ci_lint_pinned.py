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
"""
import os
import re
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
