#!/usr/bin/env python3
"""The per-project kit-gap log and its harvest (FR-0062).

Two halves, measured apart because they run on two machines' worth of trust: `kernel.gaplog` is what
a PROJECT's session writes through, `tools/harvest_kit_gaps.py` is what THIS repo reads with. The
seam between them -- the `report-gap` verb on `kernel/cli.py` and the constitution sentence that
sends a role to it -- landed in TSK-0104 and is held from both sides by
`test_the_gap_command_and_the_duty_that_names_it_arrive_together`; the verb itself is driven end to
end by `test_the_gap_verb_books_through_the_entry_point`.
"""
import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "team-kits"))

from kernel.gaplog import COMMAND, LOG_DIR, LOG_NAME, MAX_FIELD, entries, entry_id, record  # noqa: E402
from kernel.state import ProjectState, StateError  # noqa: E402

HARVEST_TOOL = os.path.join(ROOT, "tools", "harvest_kit_gaps.py")


@pytest.fixture()
def project(tmp_path):
    state = ProjectState(str(tmp_path / "project_memory"))
    os.makedirs(state.root, exist_ok=True)
    return state


def test_a_recorded_gap_survives_in_the_projects_own_state(project):
    """The whole point of the item: a reported gap outlives the session that hit it.

    BUG-0068 and BUG-0070 were both recovered only by the lead reading entire sessions afterwards,
    because "report the gap" meant saying it in the chat. What is asserted is that the two fields a
    triage needs -- what the project WANTED and what the kit ANSWERED -- come back out of the store
    the way they went in.
    """
    written = record(project, tried="add a filing rule for Lieferscheine",
                     refused="gate_write_scope refused the write to filing_plan.yaml",
                     item="TSK-0007")
    assert written["recorded"] is True
    found = entries(project.root)
    assert len(found) == 1, found
    assert found[0]["tried"].startswith("add a filing rule")
    assert "gate_write_scope" in found[0]["refused"]
    assert found[0]["item"] == "TSK-0007"
    assert found[0]["ts"] and found[0]["kit_version"], found[0]
    assert os.path.isfile(os.path.join(project.root, LOG_DIR, LOG_NAME))


def test_a_gap_with_no_refusal_or_no_attempt_is_refused(project):
    """Both halves are required, and the refusal says WHY rather than naming a field.

    An entry that says only "something did not work" is one the lead cannot triage at the other end,
    which is the entire job this log has. The two are asked for separately so a caller that has one
    of them is told which is missing.
    """
    with pytest.raises(StateError, match="refused"):
        record(project, tried="add a filing rule", refused="")
    with pytest.raises(StateError, match="tried"):
        record(project, tried="", refused="gate_write_scope refused it")
    assert entries(project.root) == []


def test_the_same_gap_reported_twice_is_one_entry(project):
    """Idempotent on CONTENT, so one wall hit twice does not reach the lead's list twice.

    That is also what lets the harvest mark an entry from outside the project: the id is derived
    from the entry's own fields, so it is the same value on both machines and neither has to write
    into the other's store to agree on which entry is which.
    """
    first = record(project, tried="grow the plan", refused="no route", item="TSK-1")
    again = record(project, tried="grow the plan", refused="no route", item="TSK-1")
    assert first["id"] == again["id"]
    assert again["recorded"] is False
    assert len(entries(project.root)) == 1
    other = record(project, tried="grow the plan", refused="no route", item="TSK-2")
    assert other["recorded"] is True and other["id"] != first["id"]
    assert len(entries(project.root)) == 2


def test_a_pasted_transcript_is_cut_and_says_so(project):
    """A bound with a MARKER, not a silent truncation: an entry that lost its tail without saying so
    is one a reader trusts to be whole. The field cap is `MAX_FIELD` and the entry names it."""
    written = record(project, tried="x" * (MAX_FIELD * 3), refused="no")
    assert len(written["tried"]) < MAX_FIELD * 2
    assert "cut at %d characters" % MAX_FIELD in written["tried"]


def test_the_entry_id_ignores_the_clock_and_reads_the_content(project):
    """Two fields, one id -- pinned so a later `ts` in the material would turn this red.

    A clock in the id would make every re-report a new entry, which is the noise the lead pays for
    and the reason `record` can be idempotent at all.
    """
    assert entry_id({"tried": "a", "refused": "b", "title": "t", "item": "i"}) == \
        entry_id({"tried": "a", "refused": "b", "title": "t", "item": "i", "ts": "2026-01-01"})
    assert entry_id({"tried": "a", "refused": "b"}) != entry_id({"tried": "a", "refused": "c"})


def _harvest(argv, home, record=None):
    """Run the shipped harvest tool with its triage record pointed INTO the test's own directory.

    Never at the repo's own `tools/kit_gap_harvest.json`: the first cut of these tests used the real
    path and deleted it in a `finally`, so a green suite run wiped the lead's actual triage state
    (measured 2026-09-01 -- a record with content in it was gone afterwards), and two parallel runs
    would have raced over one file. `test_the_real_harvest_record_is_not_a_test_fixture` is what
    holds the redirect.
    """
    env = dict(os.environ, HARNESS_PROJECTS=home,
               HARNESS_KIT_GAP_HARVEST=record or os.path.join(home, "harvest.json"))
    return subprocess.run([sys.executable, HARVEST_TOOL] + argv, capture_output=True, text=True,
                          timeout=120, env=env)


def test_the_harvest_reads_a_foreign_projects_log_and_never_writes_into_it(tmp_path):
    """The lead's end, and the trust direction that shaped it.

    The harvest READS the project and records what it has triaged HERE, so nothing in this repo ever
    writes into a project's state directory. Measured as bytes: the project's log is byte-identical
    before and after a marking run, and the mark is nevertheless remembered.
    """
    project = ProjectState(str(tmp_path / "acme" / "project_memory"))
    os.makedirs(project.root, exist_ok=True)
    written = record(project, tried="grow the Aktenplan", refused="no command writes it",
                     item="TSK-0009")
    log = os.path.join(project.root, LOG_DIR, LOG_NAME)
    with open(log, "rb") as handle:
        before = handle.read()

    listed = _harvest([str(tmp_path / "acme")], str(tmp_path))
    assert listed.returncode == 1, listed.stdout + listed.stderr   # 1 = there is something to do
    assert written["id"] in listed.stdout and "grow the Aktenplan" in listed.stdout

    marked = _harvest(["--mark", str(tmp_path / "acme"), written["id"], "--as", "FR-0099"],
                      str(tmp_path))
    assert marked.returncode == 0, marked.stdout + marked.stderr
    with open(log, "rb") as handle:
        assert handle.read() == before, "the harvest wrote into the foreign project's store"

    again = _harvest([str(tmp_path / "acme")], str(tmp_path))
    assert again.returncode == 0, again.stdout + again.stderr
    assert "0 not yet triaged" in again.stdout, again.stdout
    with open(os.path.join(str(tmp_path), "harvest.json"), encoding="utf-8") as handle:
        assert "FR-0099" in json.dumps(json.load(handle))


def test_the_real_harvest_record_is_not_a_test_fixture(tmp_path):
    """A SUITE MAY NOT TOUCH THE LEAD'S OWN TRIAGE STATE -- measured as bytes, both ends.

    The first cut of these tests wrote and then `os.remove`d the repo's real
    `tools/kit_gap_harvest.json`, so a green run deleted what the lead had already triaged and two
    parallel runs raced over one file. That is not a style question: the record is the only place
    this repo remembers which live findings it has already turned into an FR or a BUG.

    Both directions in one run: a marking run pointed at a redirect writes THERE and leaves the real
    path exactly as it found it (bytes, or absent), and the redirect is what the shipped tool
    resolves -- so removing it from `harvest_kit_gaps.harvest_path` turns this red rather than
    leaving it silently reading a constant frozen at import.
    """
    real = os.path.join(ROOT, "tools", "kit_gap_harvest.json")
    before = None
    if os.path.isfile(real):
        with open(real, "rb") as handle:
            before = handle.read()

    project = ProjectState(str(tmp_path / "acme" / "project_memory"))
    os.makedirs(project.root, exist_ok=True)
    written = record(project, tried="grow the Aktenplan", refused="no command writes it")
    redirect = os.path.join(str(tmp_path), "elsewhere", "harvest.json")
    marked = _harvest(["--mark", str(tmp_path / "acme"), written["id"], "--as", "FR-0099"],
                      str(tmp_path), record=redirect)
    assert marked.returncode == 0, marked.stdout + marked.stderr

    assert os.path.isfile(redirect), "the tool did not write where it was pointed"
    with open(redirect, encoding="utf-8") as handle:
        assert written["id"] in handle.read()
    if before is None:
        assert not os.path.isfile(real), (
            "the suite created the lead's real triage record at %s" % real)
    else:
        with open(real, "rb") as handle:
            assert handle.read() == before, (
                "the suite changed the lead's real triage record at %s" % real)


def test_the_harvest_walks_every_project_under_the_environment_directory(tmp_path):
    """`--all` is a property of the MACHINE and not a list in this repo: which projects a lead
    maintains is that machine's business, and a list here would be one more thing going stale where
    nobody looks. A directory that is not an installed project is skipped rather than reported."""
    for name in ("acme", "beta"):
        state = ProjectState(str(tmp_path / name / "project_memory"))
        os.makedirs(state.root, exist_ok=True)
        record(state, tried="do %s" % name, refused="the kit said no")
    os.makedirs(str(tmp_path / "not-a-project"), exist_ok=True)
    listed = _harvest(["--all"], str(tmp_path))
    assert listed.returncode == 1, listed.stdout + listed.stderr
    assert "do acme" in listed.stdout and "do beta" in listed.stdout
    assert "not-a-project" not in listed.stdout, listed.stdout
    assert "2 entries across 2 project(s)" in listed.stdout, listed.stdout


# A text that SENDS a role to the command, as opposed to one that lists the command among
# the others the entry point has. The difference is the invocation: the shim is the one way
# a role runs anything (`cli.INVOCATION`), so a body that spells it in front of the verb is
# telling somebody to run it, and a body that carries the bare name is describing the
# surface. Without this distinction the duty half of the tripwire below is a theorem --
# see its docstring for the measurement.
_CALLS_THE_COMMAND = re.compile(r"harness\.py\s+" + re.escape(COMMAND) + r"\b")


def test_the_gap_command_and_the_duty_that_names_it_arrive_together():
    """THE SEAM, held from both sides so a HALF of it cannot ship.

    FR-0062 has two halves that are worthless apart: a `report-gap` verb on `kernel/cli.py`, and a
    sentence in the office texts telling the manager to run it. `kernel/cli.py` belongs to another
    stream this round, so neither half is in the tree yet -- and the failure that would cost a round
    is one of them arriving alone: a constitution naming a command `--help` does not list sends a
    role down a route that does not exist (BUG-0041's own shape), and a verb nobody is told to run
    is a command with no caller.

    So this is a TRIPWIRE and not an assertion about today: it goes red the moment either half lands
    without the other. It was deliberately quiet while both were absent, which is a state the round
    protocol recorded as the seam item rather than something this file could measure; TSK-0104 wired
    both halves in one change, so it now measures a present route rather than an absent one.

    WHAT "WIRED" MEANS IS THE PARSER'S OWN ANSWER, not a word in a file. The first version of this
    test searched `cli.py` for the string `gaplog.COMMAND`, which a comment mentioning the seam
    would have satisfied just as well as a subparser -- the defect this repo has paid for twice
    (a check that reads a file instead of the part that runs). `build_parser` is what `--help`
    prints and what argparse dispatches on, so it is what a role would actually meet.

    WHAT "TOLD" MEANS IS A CALL, and that correction is the whole reason this docstring can make
    the claim above at all. Reading a MENTION made the duty end of the wire dead the moment the
    same round put `report-gap` into the office constitution's section 0 command-surface list --
    because `tools/test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it`
    forces that list to carry every subcommand the parser has, so "wired" now IMPLIES "mentioned"
    and the assertion became a theorem. Measured 2026-09-02 in a clone: the entire duty passage
    deleted from the constitution, this test GREEN, one mention left. A surface list names a
    command; only a text that spells the INVOCATION sends a role to run it, and the duty is the
    second kind.
    """
    from kernel import cli as cli_module
    surface = set(cli_module.build_parser()._subparsers._group_actions[0].choices)
    kit = os.path.join(ROOT, "team-kits", "office-team")
    texts = {path: open(path, encoding="utf-8").read() for path in
             (os.path.join(kit, "constitution", "AGENTS.md"),
              os.path.join(kit, "agents", "office-manager.md"),
              os.path.join(kit, "skills", "office-manager", "SKILL.md"))}
    wired = COMMAND in surface
    told = [path for path, body in texts.items() if _CALLS_THE_COMMAND.search(body)]
    assert wired == bool(told), (
        "`%s` is wired in kernel/cli.py: %s; the office texts naming it: %s. One without the other "
        "is either a route nobody is told about or a role sent to a command that does not exist."
        % (COMMAND, wired, [os.path.basename(one) for one in told]))


def test_the_gap_verb_books_through_the_entry_point(project, capsys):
    """The seam TSK-0104 wired, driven end to end instead of read off the parser.

    Its neighbour above holds the two halves to each other; this one runs the half that is code.
    What a role types is `python scripts/harness.py report-gap --tried … --refused …`, so the
    assertion is that ONE such call reaches `gaplog.record` with both fields and comes back with the
    line that keeps the duty honest: booking it is not telling the user (§8 of every constitution).
    """
    from kernel import cli

    assert cli.main(["--root", project.root, COMMAND,
                     "--tried", "run the design render script",
                     "--refused", "gate_write_scope refused the pipeline",
                     "--item", "TSK-0104"]) == 0
    printed = capsys.readouterr().out
    assert "recorded" in printed and "the user has not been told" in printed, printed
    found = entries(project.root)
    assert len(found) == 1, found
    assert found[0]["item"] == "TSK-0104" and "gate_write_scope" in found[0]["refused"], found[0]
    # THE SECOND CALL IS THE SAME WALL, and the log does not grow -- `record` is content-addressed,
    # which is what lets a session book a gap it hit twice without the lead triaging it twice.
    assert cli.main(["--root", project.root, COMMAND,
                     "--tried", "run the design render script",
                     "--refused", "gate_write_scope refused the pipeline",
                     "--item", "TSK-0104"]) == 0
    assert "already recorded" in capsys.readouterr().out
    assert len(entries(project.root)) == 1
