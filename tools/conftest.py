"""Shared pytest configuration for the harness's own test suite.

It carries the `known_hole` marker and the two V1 inventories below — what more than one test
module has to agree on. The inventories are a pair on purpose: one names the state stores this
lockstep MOVED, the other the ones it has not reached, and a check that reads only the first would
call the migration finished while shipped code still opens the second.

The `known_hole` marker: a place where a documented, still-open gap is
ASSERTED as current behaviour rather than promised in prose. `pytest -m known_hole` enumerates
them, and `harness doctor` (phase-2 step 8) must cross-check that enumeration against the
capability matrix's `unverified` entries — so "step 4 will close this" stops being a note someone
has to remember and becomes something the harness checks about itself.

A known_hole test PASSES while the hole exists and turns into a loud failure the day it is closed,
with its own docstring saying to invert it. That is deliberately not an xfail: a non-strict xfail
would be silent in both directions, and a strict one would file a working exploit under "expected
failure", which is the one label a reader must not walk away with.
"""


import os
import sys

import pytest

# NO BYTECODE IN THE SOURCE TREES. tools/validate.py states the principle for itself ("validation
# must never create __pycache__ that the installer could pick up") and the suite kept breaking it one
# import site at a time: three by-path loaders (only one of which was shielded), a plain
# `import kit_browser_checks` after a sys.path insert, and in principle every child process that runs
# a shipped script where it lies. Redirecting the cache is the only form of the rule that needs no
# list of import sites — `sys.pycache_prefix` covers this process, `PYTHONPYCACHEPREFIX` the ones it
# spawns. `.pytest_cache/` is already gitignored, so the caching benefit survives.
PYCACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           ".pytest_cache", "pycache")
os.makedirs(PYCACHE_DIR, exist_ok=True)
sys.pycache_prefix = PYCACHE_DIR
os.environ["PYTHONPYCACHEPREFIX"] = PYCACHE_DIR


# THE V1 STATE MONOLITHS. A monolith is a state store that lived directly at the ROOT of
# `project_memory/` and held MANY items at once. V2 gives every item its own file in a typed
# directory (`kernel.backlog_types.ACTIVE_DIRS`) and regenerates every rollup into `generated/`, so
# no ITEM lives at the V2 state root any more. What still does is reference MATERIAL — the config
# and the kits' own reference files (`master_data.yaml`, `literature.yaml`, `filing_plan.yaml`, …),
# which hold no items and have no status automaton, and are therefore not monoliths under this
# definition however many rows they carry.
#
# The names are historical fact — nothing in the V2 code can derive them — so they are written down
# exactly once, here, and every check that needs them reads this dict. The value says where the
# state went, because "gone" and "moved" need different treatment: `masterplan.md` still exists at
# `product/masterplan.md`, which is why the lockstep sweep judges the PATH and not the name.
#
# This dict holds the stores THIS lockstep moved, and nothing else. Four further V1 root stores fit
# the definition above and are deliberately not in it — see `V1_ROOT_STORES_NOT_YET_MIGRATED`
# below, which says why and pins them. Whatever reads this dict is therefore complete about the
# migration that happened, not about V1.
V1_MONOLITHS = {
    "product_requirements.yaml": "every PRD in one file -> product/active/PR-nnnn.yaml",
    "system_requirements.yaml": "every SR in one file -> system/active/SR-nnnn.yaml",
    "tasks.yaml": "every task in one file -> tasks/active/TSK-nnnn.yaml",
    "design.yaml": "design decisions -> frozen DSN revisions plus INV items",
    "architecture.yaml": "components/data flow -> ARC items plus SRs; packaging -> the ARC item",
    "progress.yaml": "the narrative status log -> the items' own status plus generated/index.yaml",
    "filing_log.yaml": "the office filing log -> the archive tree itself; a scan index over it "
                       "would be regenerated into generated/, never kept at the state root",
    "masterplan.md": "the discovery artifact -> product/masterplan.md, frozen and status-free",
    "research_questions.yaml": "every RQ in one file -> research/active/RQ-nnnn.yaml",
    "hypotheses.yaml": "every hypothesis in one file -> hypotheses/active/HYP-nnnn.yaml",
    "experiment_designs.yaml": "every experiment in one file -> experiments/active/EXP-nnnn.yaml",
}


# THE V1 ROOT STORES THE LOCKSTEP HAS NOT REACHED. Same definition as above — a store at the state
# root that held many items — and every one of them is gone from all three template trees. What
# separates them from the dict above is the READERS: shipped, running code still composes their
# path, and rewriting it is another group's work under its own phase-0 disposition row. Sweeping
# them with the inventory above would therefore paint that group's open work as this group's
# regression, and the suite would be red for something nobody in it may fix.
#
# They are written down as facts that hold TODAY, not as an exemption list. The value names the
# repo-relative files that still reach for the store, and
# `test_the_open_v1_root_store_couplings_are_still_exactly_these` asserts the set is EXACTLY that —
# so a new coupling fails it, and so does the day one is repaired, which is when the entry must be
# deleted. That is the `known_hole` idiom (see above) applied where the marker itself does not fit:
# `known_hole` names a capability from `report.CAPABILITIES`, doctor forces that capability to
# `unverified`, and every name there is also in `_REQUIRED_FOR_HARD` — a test-suite coupling is
# none of those things, and inventing a capability for it would put a permanent hold on
# `enforcement: hard` for a reason spec II.8 does not know. Measured rather than assumed
# (2026-07-27): marking the test `known_hole("v1_root_store_couplings")` and regenerating the
# sidecar turns `test_an_asserted_hole_outranks_a_green_wiring_check` red with "names no
# capability", which is doctor correctly reporting a marker the matrix cannot cross-check.
#
# `*report*.yaml` is a glob rather than a name because that is literally what `gate_git` looks for:
# the store was "whichever report file happens to be there", which is why nothing in V2 can write
# one and every merge and push in a scaffolded V2 project is blocked (disposition rows 115/338/507).
V1_ROOT_STORES_NOT_YET_MIGRATED = {
    "coding_guidelines.yaml": (
        "the language rule book -> INV items plus config knobs (disposition row 159). "
        "`guard_guidelines` reads it and exits 0 when it is absent, so the 'no code before "
        "guidelines' rule is inert in every V2 project.",
        ("team-kits/dev-team/hooks/guard_guidelines.py",
         "team-kits/dev-team/skills/software-architect/SKILL.md",
         "tools/test_hooks.py"),
    ),
    "testing_guidelines.yaml": (
        "test rules -> INV items plus config knobs (disposition row 176). It is the source of the "
        "EXTRA coverage areas and of the browser-smoke configuration, so those knobs are "
        "unreachable in a V2 project rather than gone.",
        ("team-kits/dev-team/hooks/gate_test_coverage.py",
         "team-kits/dev-team/skills/devops-engineer/SKILL.md",
         "team-kits/dev-team/skills/quality-engineer/SKILL.md",
         "team-kits/dev-team/templates/repo/scripts/kit_browser_checks.py",
         "team-kits/dev-team/templates/repo/scripts/quality.py",
         "team-kits/research-team/templates/repo/scripts/kit_browser_checks.py",
         "team-kits/research-team/templates/repo/scripts/quality.py",
         "tools/test_e2e.py",
         "tools/test_hooks.py"),
    ),
    "process_definitions.yaml": (
        "the office PROC registry -> procedures/active/PROC-nnnn.yaml (disposition rows 249/556). "
        "`gate_proc_approved` exits 0 when the file is absent, so the work-order-names-an-APPROVED-"
        "PROC rule is inert; the two repo scripts fail outright.",
        ("team-kits/office-team/hooks/gate_proc_approved.py",
         "team-kits/office-team/templates/repo/scripts/proc_hash.py",
         "team-kits/office-team/templates/repo/scripts/process_doc.py",
         "tools/test_hooks.py",
         "tools/test_hooks_v2.py"),
    ),
    "*report*.yaml": (
        "the QA/validation reports -> evidence/EVD-nnnn.yaml (disposition rows 115/338/507). "
        "Nothing in V2 writes a file matching this glob, so `gate_git` blocks EVERY merge and "
        "push in a scaffolded V2 project — measured, not inferred.",
        ("team-kits/dev-team/constitution/AGENTS.md",
         "team-kits/dev-team/hooks/gate_git.py",
         "team-kits/dev-team/skills/project-manager/SKILL.md",
         "team-kits/research-team/constitution/AGENTS.md",
         "team-kits/research-team/hooks/gate_git.py"),
    ),
}


def load_kit_module(name, path):
    """Import a shipped kit script by path, without polluting the kit tree or `sys.path`.

    ONE loader for the whole suite: there were three (`generate_dashboard.py`, `kit_checks.py`
    twice) plus a plain import, and the `__pycache__` shielding had been applied to exactly one of
    them. The cache redirection above is what actually guarantees the tree stays clean — this
    function's own `dont_write_bytecode` is the belt to that braces, and it also keeps the module
    out of `sys.modules` under a name a later real import could pick up.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = previous
    return mod


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
