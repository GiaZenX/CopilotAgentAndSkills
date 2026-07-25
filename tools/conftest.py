"""Shared pytest configuration for the harness's own test suite.

Its one job today is the `known_hole` marker: a place where a documented, still-open gap is
ASSERTED as current behaviour rather than promised in prose. `pytest -m known_hole` enumerates
them, and `harness doctor` (phase-2 step 8) must cross-check that enumeration against the
capability matrix's `unverified` entries — so "step 4 will close this" stops being a note someone
has to remember and becomes something the harness checks about itself.

A known_hole test PASSES while the hole exists and turns into a loud failure the day it is closed,
with its own docstring saying to invert it. That is deliberately not an xfail: a non-strict xfail
would be silent in both directions, and a strict one would file a working exploit under "expected
failure", which is the one label a reader must not walk away with.
"""


import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "known_hole(capability): asserts a documented-open gap as current behaviour; the named "
        "capability must be reported `unverified` while this test passes",
    )


@pytest.fixture(autouse=True)
def _isolated_user_settings(monkeypatch, tmp_path_factory):
    """Point `CLAUDE_CONFIG_DIR` at an empty directory for every test.

    `report._settings_layers` reads the USER layer (`~/.claude/settings.json`) because Claude Code
    merges it and `disableAllHooks` most often lives there. That is correct in production and
    poison in a test suite: without this the results depend on whose machine runs them, and a
    developer with hooks disabled globally would watch the enforcement tests fail for a reason
    that has nothing to do with the code. Tests that care about the user layer create the file
    inside this directory.
    """
    monkeypatch.setenv(
        "CLAUDE_CONFIG_DIR", str(tmp_path_factory.mktemp("claude-config", numbered=True)))
    yield
