#!/usr/bin/env python3
"""
The measurement for this repo's four PreToolUse gates (SR-0006, TSK-0003).

HOW IT MEASURES. Every gate is started as a REAL PROCESS with a JSON payload on stdin, against a
project built OUTSIDE this repo, and the verdict read off the exit code -- 2 is a refusal, 0 is an
allow. Nothing here imports a gate to call a function inside it, and nothing searches a file for a
sentence: two tests in this repo's history were satisfied by their own docstring, and one measured
its own environment instead of the thing under test.

BOTH DIRECTIONS, EVERY GATE. A gate that only refuses is indistinguishable from a gate that refuses
everything, and that failure is the expensive one here -- these four sit on the delegation path of
the session that builds the kits.

WHERE IT DOES NOT RUN. `python -m pytest tools/ -q` does not collect this file; it lives beside the
gates, not in the suite, because the gates are not part of any kit and `tools/` is the kits' suite.
Run it explicitly:  python -B -m pytest .claude/hooks/test_gates.py -q
"""
import ast
import concurrent.futures
import hashlib
import inspect
import io
import json
import math
import os
import queue
import random
import re
import shlex
import shutil
import stat
import string
import subprocess
import sys
import tempfile
import textwrap
import time
import tokenize

import pytest

HOOKS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HOOKS))
TEAM_KITS = os.path.join(ROOT, "team-kits")


def _copy(source, target, ignore=None):
    if os.path.isdir(source):
        shutil.copytree(source, target, dirs_exist_ok=True, ignore=ignore)
    else:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(source, target)


def build_project(base):
    """A stand-in for this repo at `base`, with a real git history and a real diff.

    A function and not only a fixture, because one test needs the SAME project under a directory
    whose name contains a space (see `test_gate1_refuses_a_protected_path_however_the_line_spells
    _it`) -- and a project whose path has no space cannot measure that.
    """
    sys.path.insert(0, TEAM_KITS)
    from kernel.hashing import transient_ignore_globs
    ignore = shutil.ignore_patterns(*transient_ignore_globs())
    _copy(TEAM_KITS, os.path.join(base, "team-kits"), ignore)
    _copy(os.path.join(ROOT, "tools", "bump_kit_version.py"),
          os.path.join(base, "tools", "bump_kit_version.py"))
    _copy(os.path.join(ROOT, "project_memory"), os.path.join(base, "project_memory"), ignore)
    _copy(HOOKS, os.path.join(base, ".claude", "hooks"), ignore)
    _copy(os.path.join(ROOT, ".claude", "settings.json"),
          os.path.join(base, ".claude", "settings.json"))
    _copy(os.path.join(ROOT, ".claude", "agents"), os.path.join(base, ".claude", "agents"))
    _copy(os.path.join(ROOT, "CLAUDE.md"), os.path.join(base, "CLAUDE.md"))
    os.makedirs(os.path.join(base, "docs"), exist_ok=True)
    os.makedirs(os.path.join(base, "radar"), exist_ok=True)
    with open(os.path.join(base, "docs", "note.md"), "w", encoding="utf-8") as handle:
        handle.write("prose\n")
    with open(os.path.join(base, "radar", "note.md"), "w", encoding="utf-8") as handle:
        handle.write("radar\n")
    for arguments in (["init", "-q", "."], ["config", "user.email", "t@t.t"],
                      ["config", "user.name", "t"], ["add", "-A"],
                      ["-c", "commit.gpgsign=false", "commit", "-qm", "base"]):
        subprocess.run(["git"] + arguments, cwd=base, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # an uncommitted change, so the working tree gate has a non-empty subject to hash
    with open(os.path.join(base, "docs", "note.md"), "a", encoding="utf-8") as handle:
        handle.write("an uncommitted change\n")
    return base


def _digest(path):
    """What this file holds, or None when there is none."""
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


def _sandbox_module():
    """The sandbox discipline this suite and the scripts beside it share, imported once."""
    sys.path.insert(0, HOOKS)
    import _sandbox
    return _sandbox


@pytest.fixture(scope="session", autouse=True)
def the_repo_is_not_a_sandbox(tmp_path_factory):
    """This suite runs REAL shell lines, and every one of them names its target RELATIVELY.

    THAT IS THE ONE THING THAT CANNOT BE LEFT TO CARE. `_changes_the_protected_file` hands
    `sed -i "s/a/b/" team-kits/kernel/state.py` to a real shell with `cwd` set to a sandbox AND the
    directory state that shell reads out of its environment kept inside that sandbox
    (`_sandbox.sandbox_environment`); the line is safe only because of both, and a line meant to
    PROVE a refusal is dangerous exactly when the proof fails -- if the gate does not refuse it,
    something runs it.
    Measured 2026-08-07 in this repo's working tree: `team-kits/kernel/state.py` came out with the
    first `a` of each of its 928 lines replaced by `b`, which is that payload run once, and the
    kernel stopped importing. Nothing in this suite would have noticed.

    SO THE SUBJECT IS THE REPO ITSELF, and the watch list is DERIVED rather than typed: a sandbox is
    built and walked, and every path it contains is looked up in `ROOT`. Whatever a line shape can
    write inside a sandbox is exactly what it would write here if its `cwd` were wrong.

    WHAT IT CANNOT TELL APART is this suite writing the tree and somebody else writing it while the
    suite runs -- this repo is worked on by more than one agent. The message says both; either way
    the run measured a tree that moved under it.
    """
    probe = _sandbox(str(tmp_path_factory.mktemp("canary")), 0)
    shell = next(iter(_posix_shells()), None)
    if shell is not None:
        # `_sandbox` makes the FREE file; the protected one is made by the helper that runs a line
        # in it, so the list is taken after both have had their say. Without this the walk found
        # only `docs/note.md`, which this repo does not have -- measured 2026-08-07, the guard was
        # green while the escaping run really rewrote the tree.
        _changes_the_protected_file(shell, probe, ":")
    watched = sorted(
        os.path.relpath(os.path.join(root, name), probe).replace("\\", "/")
        for root, _dirs, names in os.walk(probe) for name in names)
    before = {relative: _digest(os.path.join(ROOT, *relative.split("/")))
              for relative in watched}
    assert [relative for relative in watched if before[relative] is not None], (
        "none of the files a sandbox holds (%s) exists in %s, so this guard is watching nothing "
        "that a run of this suite could damage" % (watched, ROOT))
    yield
    moved = [relative for relative in watched
             if _digest(os.path.join(ROOT, *relative.split("/"))) != before[relative]]
    assert not moved, (
        "these files of THIS repo changed while the suite ran: %s.\n"
        "Every line shape here names its target relatively, so the first thing to rule out is a "
        "run of this suite that escaped its sandbox. "
        "The other possibility is another agent writing the same tree at the same time; both mean "
        "the run measured a tree that moved under it." % moved)


def _base_outside_the_home_directory():
    """A writable directory the path a bare `~` names does not contain.

    THE HOME DIRECTORY IS AN ANCESTOR, AND AN ANCESTOR ANSWERS FOR THE PROPERTY. A word whose
    path-like substring is a bare `~` gives this gate ONE candidate -- the home directory -- and a
    stand-in project built under it is then something that directory CONTAINS, so the gate refuses
    for the containment (H19) and not for the word. Measured 2026-08-08 with two projects that
    differ in nothing else: `sed -i "s/a/b/" x=~+/team-kits/kernel/state.py` is rc 0 against a
    project outside the home directory and rc 2 against one under it, while bash writes nothing
    either way. Three lines of the hole list stood on the second answer and said "over-refusal".

    THE CANDIDATES ARE DERIVED AND ORDERED BY WHAT THEY COST, not by host: the system temporary
    directory first, because on a host where it is not under the home directory nothing else is
    needed; then the anchor of this repo's own path; then the directory this repo stands in. A host
    where none of them is writable has no place to measure this property and says so.
    """
    home = os.path.realpath(os.path.expanduser("~"))
    for candidate in (tempfile.gettempdir(), os.path.splitdrive(ROOT)[0] + os.sep,
                      os.path.dirname(ROOT)):
        if not candidate or not os.path.isdir(candidate):
            continue
        resolved = os.path.realpath(candidate)
        if _under(resolved, home) or _under(resolved, os.path.realpath(ROOT)):
            continue
        try:
            probe = tempfile.mkdtemp(prefix="harness-probe-", dir=candidate)
        except OSError:
            continue
        os.rmdir(probe)
        return candidate
    raise AssertionError(
        "no writable directory on this host stands outside %s, so every stand-in project would be "
        "measured through an ancestor rather than through the property under test" % home)


def _under(path, base):
    """Is `path` `base` itself or inside it -- asked on resolved paths, across drives."""
    try:
        return os.path.commonpath([path, base]) == base
    except ValueError:
        return False


@pytest.fixture(scope="session")
def outside_the_home_directory():
    """The base every stand-in project is built under, and why it is not `tmp_path`.

    `tmp_path` is under the home directory on this host, and a project there turns a whole class of
    cells into refusals that measure the containment rather than the word (`_base_outside_the_home
    _directory`). Nothing else about the placement matters, so this is the only thing it changes.
    """
    base = tempfile.mkdtemp(prefix="harness-gates-", dir=_base_outside_the_home_directory())
    yield base
    _removed(base)
    assert not os.path.exists(base), (
        "%s survived the run. This base is not `tmp_path`, so nothing else cleans it up, and a "
        "suite that leaves a stand-in project behind on every run is a suite that fills the "
        "directory it measures from" % base)


def _removed(tree):
    """Delete `tree`, including the read-only files a `.git` directory is made of.

    `ignore_errors=True` is what this replaced, and it hid the whole problem: git object files are
    read-only, Windows refuses to unlink a read-only file, and every run left its stand-in projects
    behind -- measured 2026-08-08, seven of them at the base after one suite run.
    """
    def writable(function, path, _excinfo):
        os.chmod(path, stat.S_IWRITE)
        function(path)

    if sys.version_info >= (3, 12):
        shutil.rmtree(tree, onexc=writable)
    else:  # `onexc` is 3.12; this repo's floor is 3.11 (`kernel/report.py` states it)
        shutil.rmtree(tree, onerror=writable)


@pytest.fixture(scope="session")
def project(outside_the_home_directory):
    """The shared stand-in, built OUTSIDE this repo.

    Outside, because a gate that refuses writes and commits must not be measured by pointing it at
    the working tree it is protecting -- and because gate 3 hashes that working tree, so measuring
    in place would make every run depend on whatever else is uncommitted. And outside the HOME
    directory, because a bare `~` is a candidate this gate resolves and a project under it is one
    the home directory contains (`_base_outside_the_home_directory`).
    """
    return build_project(os.path.join(outside_the_home_directory, "project"))


@pytest.fixture(scope="session")
def open_item(project):
    """An id that RESOLVES, can carry work and is not terminal -- looked up, never typed.

    `TSK-0003` stood spelled out in eight tests, which quietly made them a precondition of that
    one item's status: the day it is validated, gate 2's allow-case, gate 4's allow-case and all
    three of gate 3's remedy tests go red for a reason that has nothing to do with any gate. The
    PROPERTY is what those tests need, so the property is what is looked up; if the store holds no
    such item, one is captured through the kernel, so the branch is measured either way.
    """
    import yaml
    sys.path.insert(0, TEAM_KITS)
    from kernel.backlog_types import ACTIVE_DIRS, AUTOMATA, REQUIRED_FIELDS
    from kernel.state import ProjectState
    state = ProjectState(os.path.join(project, "project_memory"))
    for item_type in sorted(set(AUTOMATA) & set(ACTIVE_DIRS)):
        for stem, path in state.iter_active_items(item_type):
            with open(path, encoding="utf-8") as handle:
                item = yaml.safe_load(handle) or {}
            if str(item.get("status") or "") not in AUTOMATA[item_type].terminals:
                return str(item.get("id") or stem)
    fields = {"title": "probe", "request_text": "probe"}
    candidates = [name for name in sorted(REQUIRED_FIELDS)
                  if name in ACTIVE_DIRS and name in AUTOMATA
                  and set(REQUIRED_FIELDS[name]) <= set(fields)]
    assert candidates, "no open item exists and none can be captured -- widen `fields`"
    done = subprocess.run(
        [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "capture",
         candidates[0]],
        input=json.dumps({key: fields[key] for key in REQUIRED_FIELDS[candidates[0]]}),
        cwd=project, env=dict(os.environ, PYTHONPATH=os.path.join(project, "team-kits")),
        capture_output=True, text=True)
    assert done.returncode == 0, done.stderr[-600:]
    return done.stdout.split()[0]


def run(project, gate, payload, hooks=None):
    """Start `gate` as the provider starts it and return (rc, stderr)."""
    directory = hooks or os.path.join(project, ".claude", "hooks")
    environment = dict(os.environ, CLAUDE_PROJECT_DIR=project)
    environment.pop("PYTHONPATH", None)
    done = subprocess.run([sys.executable, "-B", os.path.join(directory, gate)],
                          input=json.dumps(payload).encode("utf-8"), cwd=project,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=environment, timeout=300)
    return done.returncode, done.stderr.decode("utf-8", "replace")


def write_payload(project, relative, **extra):
    data = {"hook_event_name": "PreToolUse", "tool_name": "Write", "cwd": project,
            "tool_input": {"file_path": os.path.join(project, *relative.split("/")),
                           "content": "x"}}
    data.update(extra)
    return data


def spawn_payload(project, agent, prompt):
    return {"hook_event_name": "PreToolUse", "tool_name": "Task", "cwd": project,
            "tool_input": {"subagent_type": agent, "description": "d", "prompt": prompt}}


def bash_payload(project, command, tool="Bash"):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": project,
            "tool_input": {"command": command}}


def todo_payload(project, *entries):
    return {"hook_event_name": "PreToolUse", "tool_name": "TodoWrite", "cwd": project,
            "tool_input": {"todos": [{"content": text, "status": "pending", "activeForm": text}
                                     for text in entries]}}


# -- what is registered, read off the registration ----------------------------


def _registered(settings_path):
    """{event: {matcher: [command, ...]}} as the provider reads it."""
    with open(settings_path, encoding="utf-8") as handle:
        settings = json.load(handle)
    out = {}
    for event, groups in (settings.get("hooks") or {}).items():
        for group in groups:
            entry = out.setdefault(event, {}).setdefault(group.get("matcher", ""), [])
            entry.extend(hook.get("command", "") for hook in group.get("hooks") or [])
    return out


def _registered_tools(settings_path):
    """{script: {tool_name, ...}} -- which EVENTS each gate is actually wired to.

    The matcher is an alternation of tool names, which is how the provider reads it, so the tool
    names are what comes back. A matcher naming a tool that does not exist (`NeverFires`) shows up
    here as that name and fails the comparison below rather than quietly firing on nothing.
    """
    out = {}
    for matchers in _registered(settings_path).values():
        for matcher, commands in matchers.items():
            tools = {part.strip() for part in matcher.split("|") if part.strip()}
            for command in commands:
                for relative in re.findall(r"\$\{CLAUDE_PROJECT_DIR\}(/[^\"\s]+\.py)", command):
                    out.setdefault(os.path.basename(relative), set()).update(tools)
    return out


# The contract's own table, transcribed from SR-0006 -- {gate script: the tool names it must see}.
# AN ENUMERATION, and the only one in this file, because nothing in the repo derives it: SR-0006
# states the trigger as a set of tool names and not as a property, which is the contract deviation
# this round reports rather than papers over. So it carries a tripwire at BOTH ends
# (`test_the_registration_is_the_one_the_contract_asks_for`): every gate that is registered must
# appear here, and every gate here must be registered on exactly these tools -- and a second test
# drives each of those names through the real process, so a name that is registered and does
# nothing is not the same as one that decides.
#
# WHERE EACH LINE COMES FROM:
#   gate 1  -- "der Hauptagent darf nichts schreiben, was in eine Kit-Version eingeht". A write is
#              a write whichever tool makes it, so both the write tools and the two shells; the
#              shell half is the deviation SR-0006's four-name trigger did not cover.
#   gate 2  -- "ein Spawn im Aenderungskreis braucht ein Item": the spawn tools.
#   gate 3  -- "kein Commit ohne ein Beweismittel-Item": a commit is a shell act.
#   gate 4  -- "die Aufgabenliste traegt hoechstens EINEN Eintrag ohne Item-Id": the list tool.
EXPECTED_TOOLS = {
    "gate_lead_write_scope.py": {"Write", "Edit", "MultiEdit", "NotebookEdit",
                                 "Bash", "PowerShell"},
    "gate_spawn_needs_item.py": {"Agent", "Task"},
    "gate_commit_evidence.py": {"Bash", "PowerShell"},
    "gate_todo_items.py": {"TodoWrite"},
}

# The call each gate must REFUSE, per class of tool it is registered on. Used to drive every
# registered tool name through the real process -- see
# `test_each_gate_refuses_on_every_tool_name_it_is_registered_for`.
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}


def _refusable(project, script, tool):
    """A payload `script` must refuse, shaped as tool `tool` would deliver it."""
    if script == "gate_lead_write_scope.py":
        if tool in SHELL_TOOLS:
            return bash_payload(project, "sed -i 's/a/b/' team-kits/kernel/state.py", tool=tool)
        return write_payload(project, "team-kits/kernel/state.py", tool_name=tool)
    if script == "gate_spawn_needs_item.py":
        payload = spawn_payload(project, "harness-implementer", "Bau mal was.")
        payload["tool_name"] = tool
        return payload
    if script == "gate_commit_evidence.py":
        return bash_payload(project, "git commit -m wip", tool=tool)
    payload = todo_payload(project, "eins", "zwei")
    payload["tool_name"] = tool
    return payload


REGISTERED_PAIRS = sorted(
    (script, tool)
    for script, tools in _registered_tools(os.path.join(ROOT, ".claude", "settings.json")).items()
    for tool in tools)


def test_the_registration_is_the_one_the_contract_asks_for():
    """WHICH gate sits on WHICH event, read off the file the provider reads.

    Nothing measured this before, and four mutations of `settings.json` left all 38 tests green:
    gate 1's matcher narrowed to `Write`, gate 3's stripped of `PowerShell`, gate 1's registration
    pointed at `gate_todo_items.py` (so gate 1 was not registered at all) and gate 2's matcher set
    to a tool name that does not exist. Both ends, because either alone rots: a gate that is
    registered but not in the table is a gate nobody decided about, and a table entry that is not
    registered is a gate that does not run.
    """
    actual = _registered_tools(os.path.join(ROOT, ".claude", "settings.json"))
    assert set(actual) == set(EXPECTED_TOOLS), (
        "registered gates %s, contract table %s -- one of the two is stale"
        % (sorted(actual), sorted(EXPECTED_TOOLS)))
    for script, tools in sorted(EXPECTED_TOOLS.items()):
        assert actual[script] == tools, (
            "%s is registered on %s but SR-0006 asks for %s"
            % (script, sorted(actual[script]), sorted(tools)))


@pytest.mark.parametrize("script,tool", REGISTERED_PAIRS)
def test_each_gate_refuses_on_every_tool_name_it_is_registered_for(project, script, tool):
    """The registered name is not the claim -- the process is.

    A tool name in a matcher only means something if the gate DECIDES when a payload arrives under
    it. So every registered pair is driven through the real process with a call that gate must
    refuse; a gate that reads `tool_name` and stands down for one of its own names goes red here,
    and so does a matcher naming an event the gate never handles.
    """
    rc, err = run(project, script, _refusable(project, script, tool))
    assert rc == 2, "%s allowed a refusable call arriving as %s (stderr: %s)" % (
        script, tool, err[:400])


def test_every_registered_gate_names_a_file_that_exists_and_refuses_to_cache():
    """The registration is the subject -- not a list of filenames kept in this test.

    Two properties at once, because both are invisible until they break: a command naming a hook
    that is not there is a silent ALLOW on every call of that event, and an interpreter started
    without `-B` over `.claude/hooks` (which imports out of `team-kits/`, the source side of the
    kit hash) drops bytecode into a hashed tree -- the obligation `kernel/hashing.py`
    (BYTECODE_SUFFIXES) states for every route.
    """
    import re
    registered = _registered(os.path.join(ROOT, ".claude", "settings.json"))
    commands = [command for matchers in registered.values()
                for group in matchers.values() for command in group]
    assert commands, "this repo registers no hooks at all"
    for command in commands:
        assert " -B " in command, "%r starts an interpreter without -B" % command
        named = re.findall(r"\$\{CLAUDE_PROJECT_DIR\}(/[^\"\s]+\.py)", command)
        assert named, "no project-relative script in %r" % command
        for relative in named:
            path = os.path.join(ROOT, relative.lstrip("/").replace("/", os.sep))
            assert os.path.isfile(path), "registered but missing: %s" % path


def test_the_session_agent_is_bound_and_the_repo_carries_no_kit_marker():
    """Both halves of DEC-0003, read off the files that decide them.

    The binding is what makes `_compat.calling_subagent` able to tell the lead from a subagent at
    all -- the fixture blindness that let the July regression live for a month was exactly a
    project that bound none.

    THE MARKER HALF IS A SUBSTRING TEST BECAUSE THE RULE IT MIRRORS IS ONE. The global entry file
    routes on "does ./CLAUDE.md CONTAIN the marker", with no notion of quoting or of a sentence
    saying the opposite -- so a line explaining that this repo carries no marker, with the marker
    spelled out in it, IS a marker. That is not hypothetical: this file said exactly that until
    2026-08-04, which would have handed the repo to a Project Manager of a project that is not one.
    """
    with open(os.path.join(ROOT, ".claude", "settings.json"), encoding="utf-8") as handle:
        bound = json.load(handle).get("agent")
    assert bound, "no session agent bound"
    assert os.path.isfile(os.path.join(ROOT, ".claude", "agents", bound + ".md")), (
        "settings.json binds `%s` but there is no definition for it" % bound)
    with open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8") as handle:
        text = handle.read()
    assert "agents-and-skills:team-kit" not in text, (
        "CLAUDE.md contains the team-kit marker -- the global handover rule routes on the bare "
        "substring, so even a sentence denying it triggers the handover")


def test_todowrite_is_gated_here_and_by_no_kit():
    """Gate 4 has no counterpart in the kits, and this pins BOTH ends of that claim.

    Asked of the registrations the providers read, not of a grep: a kit that starts gating
    `TodoWrite` turns this red so the claim in `gate_todo_items.py` is corrected rather than left
    to rot, and a repo that stops gating it turns it red too.
    """
    sys.path.insert(0, TEAM_KITS)
    from kernel.hashing import is_kit_dir
    kits = [name for name in sorted(os.listdir(TEAM_KITS))
            if is_kit_dir(os.path.join(TEAM_KITS, name))]
    assert kits, "no kits found"
    for kit in kits:
        matchers = _registered(os.path.join(TEAM_KITS, kit, "settings", "settings.json"))
        for event, groups in matchers.items():
            for matcher in groups:
                assert "TodoWrite" not in matcher, (
                    "%s now gates TodoWrite on %s (%s) -- gate_todo_items.py claims no kit does"
                    % (kit, event, matcher))
    here = _registered(os.path.join(ROOT, ".claude", "settings.json"))
    assert any("TodoWrite" in matcher for matcher in here.get("PreToolUse", {})), (
        "this repo no longer gates TodoWrite")


# -- gate 1 -------------------------------------------------------------------


@pytest.mark.parametrize("relative", [
    "team-kits/dev-team/hooks/gate_git.py",     # an existing kit file
    "team-kits/dev-team/hooks/gate_new.py",     # a NEW file in an existing kit directory
    "team-kits/newkit/agents/x.md",             # a NEW kit, no directory on disk yet
    "team-kits/kernel/state.py",                # the shared half of every kit hash
    ".claude/hooks/gate_todo_items.py",         # the enforcement layer itself
    ".claude/settings.json",                    # ...and the file that registers it
    ".claude/agents/harness-lead.md",           # ...and the roles it binds (gate 2 reads these)
    ".claude/settings.local.json",              # ...and the permission overlay it merges
    "tools/bump_kit_version.py",                # ...and the producer of the protected area
])
def test_gate1_refuses_the_session_agent(project, relative):
    """The areas `_harness.ProtectedArea` names, including the paths no enumeration could hold.

    The NEW-file cases are the ones that decide whether the protected area is a position rule or a
    file list: `kit_hash_inputs` enumerates files that EXIST, so a list-based gate waves through
    exactly the write a session agent would use to add kit code.

    The last three are the ones the contract's own enumeration missed, each measured as an open
    route on 2026-08-05: an agent definition carries gate 2's exemption and is re-read on every
    call, `settings.local.json` is a permission overlay, and `bump_kit_version.py` is what gate 1
    derives its protected area FROM -- two `Write` calls to it left every kit file writable.
    """
    rc, err = run(project, "gate_lead_write_scope.py", write_payload(project, relative))
    assert rc == 2, "allowed %s (stderr: %s)" % (relative, err[:400])


@pytest.mark.parametrize("relative", ["docs/note.md", "CLAUDE.md", "radar/note.md",
                                      "project_memory/staging/TSK-0007/proposal.md"])
def test_gate1_leaves_prose_and_bookkeeping_free(project, relative):
    """The counter-direction: a gate that only refuses is a gate that has stopped working.

    `project_memory/staging/**` is here rather than the state root: spec II.4 defines staging as
    explicitly non-canonical, and it is the only route a proposal has out of an agent's hands.
    """
    rc, err = run(project, "gate_lead_write_scope.py", write_payload(project, relative))
    assert rc == 0, "refused %s (stderr: %s)" % (relative, err[:400])


@pytest.mark.parametrize("caller", [{}, {"agent_id": "sub-1", "agent_type": "harness-implementer"}])
def test_gate1_refuses_canonical_state_from_every_caller(project, caller):
    """Canonical state has one writer, and WHO asks does not change that.

    Measured before this existed: a `Write` of
    `project_memory/evidence/active/EVD-9999.yaml` carrying `result: pass` and the current digest
    was allowed (rc 0) and opened `git commit` on the spot -- gate 3's subject certified by a file
    the same session had just typed. Both callers, because a subagent's forgery is the lead's
    forgery one spawn later.
    """
    payload = write_payload(project, "project_memory/evidence/active/EVD-9999.yaml", **caller)
    rc, err = run(project, "gate_lead_write_scope.py", payload)
    assert rc == 2, "a hand-written Evidence item was allowed (%s): %s" % (caller, err[:300])


def test_gate1_reads_a_junction_as_the_tree_it_points_at(project, tmp_path):
    """R4: a second spelling of the same directory is the same directory.

    `mklink /J` needs no administrator rights on Windows, so this is a route a session agent
    really has. Measured with `abspath` in place: the write through the junction was allowed while
    the same file spelled directly was refused.
    """
    work = str(tmp_path / "junction")
    shutil.copytree(project, work)
    link = os.path.join(work, "kits")
    target = os.path.join(work, "team-kits")
    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        subprocess.run(["cmd", "/c", "mklink", "/J", link, target], capture_output=True)
    if not os.path.isdir(link):
        pytest.skip("this host allows neither a symlink nor a junction")
    rc, err = run(work, "gate_lead_write_scope.py",
                  write_payload(work, "kits/dev-team/hooks/gate_git.py"))
    assert rc == 2, "a write through a junction into the kit tree was allowed: %s" % err[:300]


# -- gate 1, the shell half ---------------------------------------------------


@pytest.mark.parametrize("tool,command", [
    ("Bash", "python -c \"open('team-kits/dev-team/hooks/gate_git.py','w').write('')\""),
    ("Bash", "python -c \"open('team-kits/kernel/state.py','w').write('')\""),
    ("Bash", "python -c \"open('.claude/hooks/gate_todo_items.py','w').write('')\""),
    ("Bash", "python -c \"open('.claude/settings.json','w').write('')\""),
    ("Bash", "python -c \"open('tools/bump_kit_version.py','w').write('')\""),
    ("Bash", "sed -i 's/a/b/' team-kits/dev-team/hooks/gate_git.py"),
    ("PowerShell", "Set-Content -Path .claude/hooks/gate_todo_items.py -Value ''"),
    ("Bash", "echo x > .claude/settings.json"),                 # the shell's own redirect
    ("Bash", "rm -rf team-kits"),                               # names the tree, not a file in it
    ("Bash", "cd .claude/hooks && rm gate_todo_items.py"),      # the path is never spelled out
    ("Bash", "bash -lc \"rm -f .claude/settings.json\""),       # code one level down
    ("Bash", "python -c \"open('project_memory/evidence/active/EVD-9999.yaml','w')\""),
])
def test_gate1_refuses_a_shell_write_into_a_protected_area(project, tool, command):
    """The eight measured lines of 2026-08-05, plus the four shapes they generalise to.

    Registered on the write tools alone, every one of these answered rc 0 while the same target
    was refused through `Write` -- so the protected area was a property of the TOOL, not of the
    path. `_harness.written_paths` is what answers now, through the kits' own shell reader.
    """
    rc, err = run(project, "gate_lead_write_scope.py", bash_payload(project, command, tool=tool))
    assert rc == 2, "allowed %r (stderr: %s)" % (command, err[:400])


def test_gate1_refuses_a_protected_path_spelled_absolutely_through_a_space(
        outside_the_home_directory):
    """The spelling the first cut of the shell half missed, and it is the ordinary one HERE.

    This repo's own checkout is `C:/Offline Repos/AgentAndSkills`, and the lead's command lines
    start with `cd "<that>"`. A scan for path-like SUBSTRINGS splits such a path at the space and
    neither half names anything -- so the quoted absolute spelling came out allowed while the same
    file spelled relatively was refused. The project is therefore rebuilt under a directory that
    HAS a space: measured in a path without one, this test measures nothing.
    """
    holder = os.path.join(outside_the_home_directory, "a path with spaces")
    os.makedirs(holder, exist_ok=True)
    work = build_project(os.path.join(holder, "repo"))
    target = os.path.join(work, "team-kits", "dev-team", "hooks", "gate_git.py")
    command = 'sed -i "s/a/b/" "%s"' % target.replace("\\", "/")
    rc, err = run(work, "gate_lead_write_scope.py", bash_payload(work, command))
    assert rc == 2, "allowed %r (stderr: %s)" % (command, err[:400])


@pytest.mark.parametrize("tool,command", [
    # every command CLAUDE.md prescribes for this repo, plus the reads a refusal must not cost
    ("Bash", "PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory generate-index"),
    ("PowerShell", '$env:PYTHONPATH="team-kits"; python -B -m kernel.cli --root project_memory '
                   'generate-index'),
    ("Bash", "python -B -m pytest .claude/hooks/test_gates.py -q"),
    ("Bash", "python -B -m pytest tools/ -q"),
    ("Bash", "python tools/bump_kit_version.py"),
    ("Bash", "python -m ruff check ."),
    ("Bash", "git status --short"),
    ("Bash", "git add -A"),
    ("Bash", "cat .claude/hooks/gate_todo_items.py"),
    ("Bash", "grep -rn STATE_ROOT team-kits/"),
])
def test_gate1_leaves_the_sessions_own_commands_runnable(project, tool, command):
    """The counter-error, and it is the expensive one.

    The kits' rule is "a write-capable pipeline that NAMES the protected tree", which works in a
    scaffolded project and would be a lockout here: every one of these lines names `team-kits`,
    `.claude` or `project_memory` and every one of them is prescribed by CLAUDE.md. A gate that
    refuses the session's own documented commands is not stricter, it is broken.
    """
    rc, err = run(project, "gate_lead_write_scope.py", bash_payload(project, command, tool=tool))
    assert rc == 0, "refused %r (stderr: %s)" % (command, err[:400])


def test_gate1_leaves_paths_outside_the_repo_free(project, tmp_path):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Write", "cwd": project,
               "tool_input": {"file_path": str(tmp_path / "scratch.md"), "content": "x"}}
    rc, err = run(project, "gate_lead_write_scope.py", payload)
    assert rc == 0, err[:400]


def test_gate1_lets_a_subagent_write_what_it_refuses_the_lead(project):
    """The gate is about WHO writes; a subagent writing kit code is the point of the loop."""
    payload = write_payload(project, "team-kits/dev-team/hooks/gate_git.py",
                            agent_id="sub-1", agent_type="harness-implementer")
    rc, err = run(project, "gate_lead_write_scope.py", payload)
    assert rc == 0, err[:400]


def test_gate1_reads_the_lead_naming_its_own_role_as_the_lead(project):
    """The regression `_compat.calling_subagent` documents, measured from this side.

    A session instance's payload carries `agent_type` equal to the bound role and no `agent_id`.
    A gate that reads "names an agent" as "is a subagent" waves this write through; a gate that
    reads it as "is the lead" -- which is what the two-field definition does -- refuses it.
    """
    with open(os.path.join(project, ".claude", "settings.json"), encoding="utf-8") as handle:
        lead = json.load(handle)["agent"]
    payload = write_payload(project, "team-kits/kernel/state.py", agent_type=lead)
    rc, err = run(project, "gate_lead_write_scope.py", payload)
    assert rc == 2, "the lead naming its own role was read as a subagent: %s" % err[:400]


# -- gate 2 -------------------------------------------------------------------


def test_gate2_refuses_a_spawn_with_no_item(project):
    rc, err = run(project, "gate_spawn_needs_item.py",
                  spawn_payload(project, "harness-implementer", "Bau mal was."))
    assert rc == 2, err[:400]


def test_gate2_refuses_an_id_that_does_not_resolve(project):
    rc, err = run(project, "gate_spawn_needs_item.py",
                  spawn_payload(project, "harness-implementer", "Auftrag: TSK-9999."))
    assert rc == 2, err[:400]
    assert "TSK-9999" in err


def test_gate2_allows_a_spawn_that_names_an_open_item(project, open_item):
    rc, err = run(project, "gate_spawn_needs_item.py",
                  spawn_payload(project, "harness-implementer",
                                "Dein Auftrag ist %s in tasks/active." % open_item))
    assert rc == 0, err[:400]


def test_gate2_exempts_only_what_its_own_definition_exempts(project, tmp_path):
    """BOTH ENDS of the exemption, which is the whole reason it is not a list of role names.

    End one: an agent whose definition declares `harness_item: none` is spawned without an item.
    End two: the SAME definition with that line removed is refused -- so the exemption is really
    read off the file and is not something the gate hands out for other reasons.
    """
    import _harness
    exempt = [name[:-3] for name in sorted(os.listdir(os.path.join(project, ".claude", "agents")))
              if name.endswith(".md")
              and not _harness.spawn_needs_an_item(project, name[:-3])]
    assert exempt, "no agent declares %s: %s" % (_harness.ITEM_KEY, _harness.ITEM_NONE)
    for agent in exempt:
        rc, err = run(project, "gate_spawn_needs_item.py",
                      spawn_payload(project, agent, "Weekly run."))
        assert rc == 0, "%s is declared exempt but was refused: %s" % (agent, err[:400])
    stripped = str(tmp_path / "agents-without-the-key")
    shutil.copytree(os.path.join(project, ".claude", "agents"), stripped)
    definition = os.path.join(stripped, exempt[0] + ".md")
    with open(definition, encoding="utf-8") as handle:
        text = handle.read()
    lines = [line for line in text.splitlines(True)
             if not line.strip().startswith(_harness.ITEM_KEY + ":")]
    assert len(lines) < len(text.splitlines(True)), "the key was not found to remove"
    with open(definition, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(lines))
    live = os.path.join(project, ".claude", "agents")
    backup = str(tmp_path / "agents-backup")
    shutil.copytree(live, backup)
    try:
        shutil.rmtree(live)
        shutil.copytree(stripped, live)
        rc, err = run(project, "gate_spawn_needs_item.py",
                      spawn_payload(project, exempt[0], "Weekly run."))
        assert rc == 2, ("%s stayed exempt after its own declaration was removed -- the exemption "
                         "does not come from the definition" % exempt[0])
    finally:
        shutil.rmtree(live, ignore_errors=True)
        shutil.copytree(backup, live)


# -- gate 3 -------------------------------------------------------------------


def test_gate3_ignores_a_command_that_does_not_commit(project):
    rc, err = run(project, "gate_commit_evidence.py", bash_payload(project, "git status"))
    assert rc == 0, err[:400]


@pytest.mark.parametrize("command", [
    'git commit -m "wip"',
    'bash -lc "git commit -m wip"',      # the payload is code one level down
    'git $V -m wip',                     # a verb the text does not fix: could be any subcommand
])
def test_gate3_refuses_a_commit_without_evidence(project, command):
    rc, err = run(project, "gate_commit_evidence.py", bash_payload(project, command))
    assert rc == 2, "allowed %r" % command
    assert "diff:" in err, "the refusal names no subject digest"


def test_gate3_remedy_is_executable_and_opens_the_commit(project, tmp_path, open_item):
    """The refusal's own command, run as printed, must make the next call pass.

    THIS IS THE TEST THAT KEEPS THE GATE HONEST. A gate whose remedy cannot be executed locks the
    repo out of its own history, and this one is on `git commit`. So the digest is read out of the
    refusal, handed to `kernel.cli evidence` exactly as the text spells it, and the same call is
    repeated. Against a COPY of the project, because recording evidence changes it.
    """
    import re
    work = str(tmp_path / "remedy")
    shutil.copytree(project, work)
    payload = bash_payload(work, 'git commit -m "wip"')
    rc, err = run(work, "gate_commit_evidence.py", payload)
    assert rc == 2
    digest = re.search(r"diff:[0-9a-f]{64}", err).group(0)
    environment = dict(os.environ, PYTHONPATH=os.path.join(work, "team-kits"))
    done = subprocess.run(
        [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "evidence",
         "--kind", "review", "--result", "pass", "--related", open_item,
         "--summary", "verifier PASS for " + digest,
         "--artifact-ref", "staging/verdict.md"],
        cwd=work, env=environment, capture_output=True, text=True)
    assert done.returncode == 0, "the remedy command failed: %s" % done.stderr[-800:]
    rc, err = run(work, "gate_commit_evidence.py", payload)
    assert rc == 0, "the recorded verdict did not open the commit: %s" % err[:600]


def test_gate3_verdict_stops_covering_a_tree_that_moved(project, tmp_path, open_item):
    """The digest is an identity, so a package that moves after the review is refused again.

    And the counter-direction, which is what makes the construction reachable at all: a change
    confined to `project_memory/` does NOT invalidate the verdict -- it cannot, because the
    verdict is written there.
    """
    import re
    work = str(tmp_path / "moved")
    shutil.copytree(project, work)
    payload = bash_payload(work, "git commit -m wip")
    rc, err = run(work, "gate_commit_evidence.py", payload)
    digest = re.search(r"diff:[0-9a-f]{64}", err).group(0)
    subprocess.run([sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory",
                    "evidence", "--kind", "review", "--result", "pass", "--related", open_item,
                    "--summary", "verifier PASS for " + digest,
                    "--artifact-ref", "staging/verdict.md"],
                   cwd=work, env=dict(os.environ, PYTHONPATH=os.path.join(work, "team-kits")),
                   check=True, capture_output=True, text=True)
    assert run(work, "gate_commit_evidence.py", payload)[0] == 0
    with open(os.path.join(work, "project_memory", "README.md"), "a", encoding="utf-8") as handle:
        handle.write("\nbookkeeping\n")
    assert run(work, "gate_commit_evidence.py", payload)[0] == 0, (
        "a change under the state store invalidated the verdict -- then no verdict could ever "
        "cover the tree it is recorded for")
    with open(os.path.join(work, "docs", "note.md"), "a", encoding="utf-8") as handle:
        handle.write("\none more line\n")
    assert run(work, "gate_commit_evidence.py", payload)[0] == 2, (
        "the verdict still covers a working tree that has moved since")


def test_gate3_sees_a_file_git_does_not_track_yet(project, tmp_path, open_item):
    """R10: the UNTRACKED half of the digest, which no test reached.

    `working_tree_digest` hashes HEAD, the diff to the working tree AND every untracked,
    non-ignored file -- and only the first two were ever measured, so deleting the third loop left
    the suite green while a whole new file could be added to a certified tree. A new file is the
    ordinary shape of "work happened since the review", which makes this the half most worth
    having.
    """
    work = str(tmp_path / "untracked")
    shutil.copytree(project, work)
    payload = bash_payload(work, "git commit -m wip")
    digest = re.search(r"diff:[0-9a-f]{64}",
                       run(work, "gate_commit_evidence.py", payload)[1]).group(0)
    subprocess.run([sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory",
                    "evidence", "--kind", "review", "--result", "pass", "--related", open_item,
                    "--summary", "verifier PASS for " + digest,
                    "--artifact-ref", "staging/verdict.md"],
                   cwd=work, env=dict(os.environ, PYTHONPATH=os.path.join(work, "team-kits")),
                   check=True, capture_output=True, text=True)
    assert run(work, "gate_commit_evidence.py", payload)[0] == 0, "wrong precondition"
    with open(os.path.join(work, "docs", "brand-new.md"), "w", encoding="utf-8") as handle:
        handle.write("a file git has never seen\n")
    rc, err = run(work, "gate_commit_evidence.py", payload)
    assert rc == 2, "an untracked file was added and the verdict still covered the tree: %s" % (
        err[:300])


def test_gate3_reads_the_digest_in_any_field_of_the_record(project, tmp_path, open_item):
    """R10: `evidence_naming` searches EVERY string of the item, and only `--summary` was measured.

    The reviewer decides which field carries the reference; pinning one silently makes the other
    not count. Here the digest is put in `--artifact-ref` and nowhere else.
    """
    work = str(tmp_path / "any-field")
    shutil.copytree(project, work)
    payload = bash_payload(work, "git commit -m wip")
    digest = re.search(r"diff:[0-9a-f]{64}",
                       run(work, "gate_commit_evidence.py", payload)[1]).group(0)
    subprocess.run([sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory",
                    "evidence", "--kind", "review", "--result", "pass", "--related", open_item,
                    "--summary", "verifier PASS",
                    "--artifact-ref", "staging/%s.md" % digest],
                   cwd=work, env=dict(os.environ, PYTHONPATH=os.path.join(work, "team-kits")),
                   check=True, capture_output=True, text=True)
    rc, err = run(work, "gate_commit_evidence.py", payload)
    assert rc == 0, "a verdict naming the digest outside --summary did not count: %s" % err[:300]


def test_gate3_reads_the_verdict_and_not_merely_the_record(project, tmp_path, open_item):
    """`result: fail` naming the same digest is a review that said NO."""
    import re
    work = str(tmp_path / "failing")
    shutil.copytree(project, work)
    payload = bash_payload(work, "git commit -m wip")
    digest = re.search(r"diff:[0-9a-f]{64}",
                       run(work, "gate_commit_evidence.py", payload)[1]).group(0)
    subprocess.run([sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory",
                    "evidence", "--kind", "review", "--result", "fail", "--related", open_item,
                    "--summary", "verifier FAIL for " + digest,
                    "--artifact-ref", "staging/verdict.md"],
                   cwd=work, env=dict(os.environ, PYTHONPATH=os.path.join(work, "team-kits")),
                   check=True, capture_output=True, text=True)
    assert run(work, "gate_commit_evidence.py", payload)[0] == 2, (
        "a FAILING report opened the commit")


# -- gate 4 -------------------------------------------------------------------


def test_gate4_refuses_a_second_entry_without_an_item(project):
    rc, err = run(project, "gate_todo_items.py",
                  todo_payload(project, "Gates bauen", "Bericht schreiben"))
    assert rc == 2, err[:400]


def test_gate4_allows_exactly_one_unbound_entry(project, open_item):
    rc, err = run(project, "gate_todo_items.py",
                  todo_payload(project, "laufender Schritt", "%s: Gates bauen" % open_item,
                               "%s: Vertrag pruefen" % open_item))
    assert rc == 0, err[:400]


def test_gate4_refuses_an_id_that_does_not_resolve(project, open_item):
    rc, err = run(project, "gate_todo_items.py",
                  todo_payload(project, "%s: a" % open_item, "TSK-9999: b"))
    assert rc == 2, err[:400]


def test_gate4_refuses_a_type_that_carries_no_work(project, open_item):
    """A decision has no lifecycle, so a task list entry pointing at one leads nothing."""
    rc, err = run(project, "gate_todo_items.py",
                  todo_payload(project, "%s: a" % open_item, "DEC-0003: b"))
    assert rc == 2, err[:400]
    assert "DEC-0003" in err


def test_gate4_refuses_an_item_in_a_terminal_status(project, tmp_path, open_item):
    """A finished item is no open work -- the AUTOMATON half of `Reference.terminal`.

    THE SUBJECT IS BUILT, NOT LOOKED UP, and that is what makes this measure the branch it names.
    Every item this project has already archived is BOTH archived and terminal, so either branch
    answers for it and removing one changes nothing -- the first cut of this test was green with
    the automaton test deleted. So an item is captured and driven to a terminal status while
    staying in `active/`: then the archive branch cannot answer, and only the automaton can.

    Its type, and the route to a terminal, come from the kernel (`REQUIRED_FIELDS`, `AUTOMATA`),
    so a renamed type or a changed chain re-derives instead of going stale. The precondition is
    measured too: while the same item is still OPEN, the same list is allowed.
    """
    sys.path.insert(0, TEAM_KITS)
    from kernel.backlog_types import ACTIVE_DIRS, AUTOMATA, REQUIRED_FIELDS
    fields = {"title": "probe", "request_text": "probe"}
    candidates = [name for name in sorted(REQUIRED_FIELDS)
                  if name in ACTIVE_DIRS and name in AUTOMATA
                  and set(REQUIRED_FIELDS[name]) <= set(fields)]
    assert candidates, "no automaton type can be captured from this body -- widen `fields`"
    item_type = candidates[0]
    automaton = AUTOMATA[item_type]
    work = str(tmp_path / "terminal")
    shutil.copytree(project, work)
    environment = dict(os.environ, PYTHONPATH=os.path.join(work, "team-kits"))

    def kernel(*arguments, **kw):
        return subprocess.run([sys.executable, "-B", "-m", "kernel.cli", "--root",
                               "project_memory"] + list(arguments), cwd=work, env=environment,
                              capture_output=True, text=True, **kw)

    done = kernel("capture", item_type,
                  input=json.dumps({key: fields[key] for key in REQUIRED_FIELDS[item_type]}))
    assert done.returncode == 0, done.stderr[-600:]
    item_id = done.stdout.split()[0]
    entries = todo_payload(work, "%s: a" % open_item, item_id + ": b")
    assert run(work, "gate_todo_items.py", entries)[0] == 0, (
        "%s was refused while still open -- wrong precondition" % item_id)
    for status in list(automaton.chain)[1:]:
        assert kernel("transition", item_id, status).returncode == 0
    reached = [status for status in sorted(automaton.terminals)
               if kernel("transition", item_id, status).returncode == 0]
    assert reached, "no terminal status of %s could be reached" % item_type
    state = os.path.join(work, "project_memory", *ACTIVE_DIRS[item_type].split("/"))
    assert os.path.isfile(os.path.join(state, item_id + ".yaml")), (
        "%s left active/ -- then this measures the archive branch, not the automaton" % item_id)
    rc, err = run(work, "gate_todo_items.py", entries)
    assert rc == 2, "%s in %s counted as open work: %s" % (item_id, reached[0], err[:400])


def test_gate2_refuses_an_archived_item_whose_type_declares_no_terminals(project, tmp_path):
    """The ARCHIVE half of `Reference.terminal`, measured where it is the only answer.

    A type without an automaton declares no terminal status at all, so for it the archive IS the
    end of the line -- `state.archive()` accepts such a type unconditionally. Gate 2 is where that
    matters: unlike gate 4 it does not additionally demand that the type can carry work, so an
    automaton-less item reaches the terminal question instead of being rejected before it.

    Built rather than looked up: the item is captured and archived through the kernel in a COPY,
    because a project that happens to have no archived decision today would otherwise silently
    skip the only case this branch decides.
    """
    sys.path.insert(0, TEAM_KITS)
    from kernel.backlog_types import ACTIVE_DIRS, AUTOMATA, REQUIRED_FIELDS
    fields = {"title": "probe", "context": "c", "decision": "d", "consequences": "x",
              "source": "probe", "scope": "probe", "check": "probe"}
    # the type is CHOSEN by what this body can fill, so a type list that changes shape makes the
    # test pick another subject instead of failing on a body written for the old one
    candidates = [name for name in sorted(REQUIRED_FIELDS)
                  if name in ACTIVE_DIRS and name not in AUTOMATA
                  and set(REQUIRED_FIELDS[name]) <= set(fields)]
    assert candidates, "no automaton-less type can be captured -- the branch is unreachable"
    item_type = candidates[0]
    work = str(tmp_path / "archived")
    shutil.copytree(project, work)
    environment = dict(os.environ, PYTHONPATH=os.path.join(work, "team-kits"))
    body = json.dumps({key: value for key, value in fields.items()
                       if key in REQUIRED_FIELDS[item_type]})
    done = subprocess.run([sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory",
                           "capture", item_type], input=body, cwd=work, env=environment,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stderr[-600:]
    item_id = done.stdout.split()[0]
    rc, _err = run(work, "gate_spawn_needs_item.py",
                   spawn_payload(work, "harness-implementer", "Auftrag: " + item_id))
    assert rc == 0, "%s was refused while still active -- wrong precondition" % item_id
    subprocess.run([sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory",
                    "archive", item_id], cwd=work, env=environment, check=True,
                   capture_output=True, text=True)
    rc, err = run(work, "gate_spawn_needs_item.py",
                  spawn_payload(work, "harness-implementer", "Auftrag: " + item_id))
    assert rc == 2, "an ARCHIVED %s still counted as open work: %s" % (item_type, err[:400])


def test_the_types_the_contract_names_are_the_ones_the_derivation_accepts():
    """The tripwire on the widened predicate, at BOTH ends.

    `_harness.Reference.carries_work` asks the kernel whether a type has a LIFECYCLE, which is the
    reason SR-0006 gives, rather than repeating the three type names its parenthesis illustrates it
    with. That reading is only defensible while the two ends hold: every type the contract names
    must pass, and the type its justification names (`DEC`, "keinen Lebenszyklus") must fail. A
    rename kills the first, a `DEC` that grew an automaton kills the second, and either turns this
    red instead of quietly changing what gate 4 means.
    """
    sys.path.insert(0, TEAM_KITS)
    from kernel.backlog_types import ACTIVE_DIRS, AUTOMATA
    for named in ("TSK", "BUG", "FR"):
        assert named in ACTIVE_DIRS, "%s is no longer a kernel type" % named
        assert named in AUTOMATA, (
            "%s has no automaton, so gate 4 would refuse an item SR-0006 names as work" % named)
    assert "DEC" in ACTIVE_DIRS and "DEC" not in AUTOMATA, (
        "DEC now has a lifecycle -- SR-0006's justification for the rule no longer holds and "
        "gate 4's derivation has to be revisited")


# -- fail-closed --------------------------------------------------------------


@pytest.mark.parametrize("script,tool", REGISTERED_PAIRS)
def test_a_gate_whose_shared_body_is_gone_still_refuses(project, tmp_path, script, tool):
    """The import is INSIDE the protection, and this is the measurement that says so.

    `guarded()` cannot cover the import of `_harness`, because that happens before any gate
    function runs. Measured on 2026-08-05 with the file deleted: all four gates exited 1, and the
    provider reads a non-zero exit other than 2 as "hook error, carry on" -- an ALLOW on every
    call. Together with gate 1 not being registered on the shell, that was two tool calls to
    switch the whole layer off.

    Driven over the REGISTERED pairs rather than over a list of filenames, so a gate that is added
    to `settings.json` without the preamble is measured on the day it is registered.
    """
    work = str(tmp_path / ("no-body-" + script + "-" + tool))
    shutil.copytree(project, work)
    os.remove(os.path.join(work, ".claude", "hooks", "_harness.py"))
    rc, err = run(work, script, _refusable(work, script, tool))
    assert rc == 2, "%s answered rc=%d without its shared body (stderr: %s)" % (
        script, rc, err[:400])


@pytest.mark.parametrize("script,payload_key", [
    ("gate_lead_write_scope.py", "Write"),
    ("gate_commit_evidence.py", "Bash"),
    ("gate_todo_items.py", "TodoWrite"),
])
def test_a_payload_a_gate_cannot_read_is_refused(project, script, payload_key):
    """"Nothing to check" is not "nothing to worry about".

    Each of these three stood down on a payload it could not map to the shape it asks for -- no
    file path, no command line, no `todos` list -- and standing down is an ALLOW. The direction is
    the one `_harness.payload` already takes for a payload over the stdin bound: a call that could
    not be inspected is refused, and the refusal says how to report it if the shape is legitimate.

    An EMPTY todo list is deliberately not in here: clearing the list is a real call and passes.
    """
    payload = {"hook_event_name": "PreToolUse", "tool_name": payload_key, "cwd": project,
               "tool_input": {}}
    rc, err = run(project, script, payload)
    assert rc == 2, "%s allowed a payload it could not read: %s" % (script, err[:300])


def test_gate4_allows_an_empty_list(project):
    """The counter-direction of the test above -- clearing the task list is not an unreadable call."""
    payload = {"hook_event_name": "PreToolUse", "tool_name": "TodoWrite", "cwd": project,
               "tool_input": {"todos": []}}
    assert run(project, "gate_todo_items.py", payload)[0] == 0


def test_gate3_refuses_a_line_that_moves_the_tree_before_it_commits(project, tmp_path, open_item):
    """R1: the digest is taken BEFORE the line runs, so the line must not move the tree.

    Measured with a valid verdict recorded: `echo more >> docs/note.md && git commit -m wip` was
    allowed (rc 0) -- the commit recorded a tree no verdict had ever seen. Both counter-directions
    are measured in the same run, because a rule that also refuses the ordinary flow is not a
    fix: a plain commit and `git add -A && git commit` must stay open, and staging really does
    move nothing the digest reads (`diff HEAD` covers staged and unstaged alike).

    "BEFORE" IS WHAT THE LINE CAN SHOW, and three spellings put a change where nothing orders it
    against the commit -- measured 2026-08-05 with the same valid verdict, all three rc 0: the
    change handed to the background (`... & git commit`), the change glued to its separator
    (`(...);git commit`), and a commit the shell does not wait for, with the change behind it
    (`git commit & ...`). The last one is why the rule is not simply "everything in front of it":
    a background command has no front.

    A PIPE IS THE FOURTH SUCH SPELLING and it was open until TSK-0015: the stages of a pipeline run
    beside each other, so `sed -i ... docs/note.md | git commit -m wip` (rc 0, measured) puts a
    write next to the commit with nothing ordering them. The counter-ends are two: the same shape
    ordered properly (`git commit ; <a write>` stays open, because a write after a commit the shell
    waited for cannot reach it) and a READING stage feeding the commit (`echo wip | git commit -F -`
    stays open, or this rule would refuse a documented flow).

    AND A SUBSTITUTION IS A COMMAND, WHICH IS THE FIFTH: the committing stage is dropped as a whole
    here, and a substitution inside it is neither its verb nor its redirection -- so a write in one
    was invisible. Measured 2026-08-07 with the same valid verdict and end to end:
    `git commit -am wip $(sed -i s/prose/POISON/ docs/note.md)` was rc 0, `docs/note.md` read
    `POISON` afterwards, HEAD moved, and the commit carried it. The counter-end is a READ in the
    same position (`git commit -m "wip $(git rev-parse HEAD)"`), which has to stay open.
    """
    work = str(tmp_path / "before-commit")
    shutil.copytree(project, work)
    payload = bash_payload(work, "git commit -m wip")
    digest = re.search(r"diff:[0-9a-f]{64}",
                       run(work, "gate_commit_evidence.py", payload)[1]).group(0)
    subprocess.run([sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory",
                    "evidence", "--kind", "review", "--result", "pass", "--related", open_item,
                    "--summary", "verifier PASS for " + digest,
                    "--artifact-ref", "staging/verdict.md"],
                   cwd=work, env=dict(os.environ, PYTHONPATH=os.path.join(work, "team-kits")),
                   check=True, capture_output=True, text=True)
    assert run(work, "gate_commit_evidence.py", payload)[0] == 0, "wrong precondition"
    assert run(work, "gate_commit_evidence.py",
               bash_payload(work, "git add -A && git commit -m wip"))[0] == 0, (
        "staging a file was read as moving the tree -- that refuses the ordinary flow")
    assert run(work, "gate_commit_evidence.py",
               bash_payload(work, 'git commit -m wip ; sed -i "s/a/b/" docs/note.md'))[0] == 0, (
        "a write AFTER a commit the shell waits for was read as a write before it")
    assert run(work, "gate_commit_evidence.py",
               bash_payload(work, "echo wip | git commit -F -"))[0] == 0, (
        "a READING stage feeding the commit was read as a write beside it -- that refuses a "
        "documented flow")
    assert run(work, "gate_commit_evidence.py",
               bash_payload(work, "git commit -m wip > /dev/null"))[0] == 0, (
        "a redirect into the discard device was read as a write -- output suppression is not a "
        "change to the tree, and refusing it would refuse the ordinary flow")
    assert run(work, "gate_commit_evidence.py",
               bash_payload(work, 'git commit -m "wip $(git rev-parse HEAD)"'))[0] == 0, (
        "a READ in a substitution of the committing stage was read as a write -- the command a "
        "substitution introduces is judged by the same classification as any other, or this rule "
        "refuses every commit message that quotes the tree it commits")
    unordered = {
        "and then": "echo more >> docs/note.md && git commit -m wip",
        "in the background": "echo more >> docs/note.md & git commit -m wip",
        "glued to its separator": "(echo more >> docs/note.md);git commit -m wip",
        "behind a commit the shell does not wait for":
            'git commit -m wip & sed -i "s/a/b/" docs/note.md',
        # A PIPE IS NO ORDERING: the stages run beside each other, so a write in the committing
        # pipeline reaches the tree while the commit reads it. Two of these were rc 0 before
        # TSK-0015 and are the same mechanism as the four above.
        "in the same pipeline": 'sed -i "s/a/b/" docs/note.md | git commit -m wip',
        "in the same pipeline, glued to a bracket":
            "(echo more >> docs/note.md)|git commit -m wip",
        "in a pipeline that carries stderr too": "echo more >> docs/note.md |& git commit -m wip",
        "behind a commit in the same pipeline":
            'git commit -m wip |& sed -i "s/a/b/" docs/note.md',
        # ONLY THE VERB OF A STAGE IS THE COMMIT -- its REDIRECTION is the shell, and the shell
        # sets it up before git ever starts. Measured 2026-08-07, rc 0 with a valid verdict in the
        # tree, and end to end: `docs/note.md` was EMPTY afterwards and the commit recorded
        # `docs/note.md | 1 -`, a tree no verdict had ever seen.
        "into a file it redirects the commit's own output to": "git commit -am wip > docs/note.md",
        "into a file it appends the commit's own output to": "git commit -m wip >> docs/note.md",
        "into a file it redirects the commit's errors to": "git commit -m wip 2> docs/note.md",
        # A COMMAND A SUBSTITUTION INTRODUCES runs before the word it stands in reaches git, and the
        # stage that carries the commit is dropped as a whole -- so this was the one command in the
        # line that no stage of it ever showed.
        "in a substitution of the committing stage":
            "git commit -am wip $(sed -i s/prose/POISON/ docs/note.md)",
        "in a backtick substitution of the committing stage":
            "git commit -am wip `sed -i s/prose/POISON/ docs/note.md`",
        "in a substitution of a stage beside the commit":
            'echo "$(sed -i s/prose/POISON/ docs/note.md)" | git commit -F -',
    }
    for label, command in sorted(unordered.items()):
        rc, err = run(work, "gate_commit_evidence.py", bash_payload(work, command))
        assert rc == 2, "a line that writes %s was allowed: %s" % (label, err[:300])


def test_gate3_sees_what_the_kits_classification_calls_a_write_and_no_more(project, tmp_path,
                                                                          open_item):
    """WHERE the ordering rule ends, measured -- because a claim of totality would be false.

    Gate 3 asks whether everything the line does not put AFTER the commit is READ-ONLY, and what
    read-only means is the kits' classification (`gate_write_scope._stage_is_read_only`). That is a
    boundary and not a set of exceptions, and it is a boundary in the direction that passes: a verb
    the kits list as reading can still write. Measured here rather than described, in both
    directions in the same run, with a valid verdict recorded:

      * a write the classification SEES (a redirect out of the committing stage itself) is refused;
      * a write it does NOT see -- `sed -n "w <file>"` writes with no redirect operator anywhere,
        which that module's own docstring names as its open edge -- is allowed, and the shell really
        truncates the file.

    So the constitution may not say "every line that changes the tree before the commit"; it names
    this gate and this boundary instead, and `test_the_constitution_names_only_code_that_exists`
    keeps that pointer from rotting. H22 in `docs/POST_V2_WISHLIST.md` carries the boundary itself.
    """
    work = str(tmp_path / "classification-edge")
    shutil.copytree(project, work)
    payload = bash_payload(work, "git commit -m wip")
    digest = re.search(r"diff:[0-9a-f]{64}",
                       run(work, "gate_commit_evidence.py", payload)[1]).group(0)
    subprocess.run([sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory",
                    "evidence", "--kind", "review", "--result", "pass", "--related", open_item,
                    "--summary", "verifier PASS for " + digest,
                    "--artifact-ref", "staging/verdict.md"],
                   cwd=work, env=dict(os.environ, PYTHONPATH=os.path.join(work, "team-kits")),
                   check=True, capture_output=True, text=True)
    assert run(work, "gate_commit_evidence.py", payload)[0] == 0, "wrong precondition"
    seen = 'git commit -am wip > docs/note.md'
    assert run(work, "gate_commit_evidence.py", bash_payload(work, seen))[0] == 2, (
        "the write this gate CAN see was allowed, so the boundary below says nothing")
    unseen = 'sed -n "w docs/note.md" radar/note.md ; git commit -m wip'
    assert run(work, "gate_commit_evidence.py", bash_payload(work, unseen))[0] == 0, (
        "this line is refused now, so the boundary moved: the constitution and H22 describe an "
        "edge that is no longer there, and both have to be corrected rather than left standing")
    shell = next((candidate for candidate in _posix_shells()
                  if subprocess.run([candidate, "-c", "true"], cwd=work,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL).returncode == 0), None)
    assert shell is not None, (
        "no shell on this host could run the line, so what it does to the file was not measured")
    subprocess.run([shell, "-c", 'sed -n "w docs/note.md" radar/note.md'], cwd=work,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    with open(os.path.join(work, "docs", "note.md"), encoding="utf-8") as handle:
        after = handle.read()
    assert after == "radar\n", (
        "the line this gate allows did not move the tree here, so this test measured no boundary "
        "at all: %r" % after)


# -- the constitution points at code, and the pointers are read (TSK-0017 F6) -------------------

CONSTITUTION = os.path.join(ROOT, "CLAUDE.md")
# A backtick-quoted `<module>.<name>` or `<name>.py`, as the constitution spells its pointers.
POINTER_RX = re.compile(r"`([A-Za-z_][\w.]*(?:\.py)?)`")


def _module_names():
    """Every module of the enforcement layer, by the name a pointer would use."""
    return {os.path.splitext(name)[0]: os.path.join(HOOKS, name)
            for name in os.listdir(HOOKS) if name.endswith(".py")}


def test_the_constitution_names_only_code_that_exists():
    """A pointer into the enforcement layer is checkable; a sentence about it is not.

    THE RULE THIS ENFORCES IS THE HOUSE RULE ITSELF -- no comment or document may claim protection
    the code does not build -- turned into something a run can answer. A prose claim ("and every
    line that changes the tree before the commit") cannot be measured and was false: measured
    2026-08-07, `sed -n "w docs/note.md" <file> ; git commit -m wip` is rc 0 and really truncates
    the file (`test_gate3_sees_what_the_kits_classification_calls_a_write_and_no_more`). What CAN be
    measured is a POINTER, so the constitution names the function that decides and this reads that
    name out of the module's syntax tree.

    BOTH ENDS: a pointer that names nothing is a claim that has rotted, and a constitution that
    names no code at all would satisfy the first half by saying nothing -- so the count is asserted
    too.
    """
    with open(CONSTITUTION, encoding="utf-8") as handle:
        text = handle.read()
    modules = _module_names()
    defined, missing = 0, []
    for pointer in sorted(set(POINTER_RX.findall(text))):
        head = pointer.split(".")[0]
        if head not in modules:
            continue
        if pointer.endswith(".py") and pointer.count(".") == 1:
            defined += 1
            continue
        with open(modules[head], encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        names = {node.name for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        names |= {target.id for node in tree.body if isinstance(node, ast.Assign)
                  for target in node.targets if isinstance(target, ast.Name)}
        wanted = pointer.split(".", 1)[1]
        if wanted in names:
            defined += 1
        else:
            missing.append("%s -- %s defines no %s" % (pointer, modules[head], wanted))
    assert not missing, (
        "the constitution points at code that is not there any more:\n%s" % "\n".join(missing))
    assert defined >= 3, (
        "the constitution names %d thing(s) in %s -- a document that points at no code cannot be "
        "held to it, and the prose claims it makes instead are what this test exists to replace"
        % (defined, HOOKS))


@pytest.mark.parametrize("gate", ["gate_lead_write_scope.py", "gate_spawn_needs_item.py",
                                  "gate_commit_evidence.py", "gate_todo_items.py"])
def test_a_gate_that_cannot_decide_refuses(project, tmp_path, gate):
    """A crash must not read as an allow.

    The provider treats a non-zero exit other than 2 as "hook error, carry on". So a gate that
    cannot reach the kernel it decides with has to say so as a REFUSAL, and this measures it by
    taking the kit tree away from a copy rather than by trusting the `try/except` to be there.
    """
    work = str(tmp_path / ("broken-" + gate))
    shutil.copytree(project, work)
    shutil.rmtree(os.path.join(work, "team-kits"))
    payloads = {
        "gate_lead_write_scope.py": write_payload(work, "team-kits/kernel/state.py"),
        "gate_spawn_needs_item.py": spawn_payload(work, "harness-implementer", "x"),
        "gate_commit_evidence.py": bash_payload(work, "git commit -m wip"),
        "gate_todo_items.py": todo_payload(work, "a", "b"),
    }
    rc, err = run(work, gate, payloads[gate])
    assert rc == 2, "%s answered rc=%d instead of refusing (stderr: %s)" % (gate, rc, err[:400])


# -- one file, however it is spelled (TSK-0008 B1) -----------------------------


def spellings(path):
    """Every way THIS host can spell one path, as `{label: spelling}`.

    Asked of the host rather than listed: the 8.3 alias only exists where the volume generates
    one, and a spelling that does not resolve here would measure nothing. The prefixed forms are
    built from the path itself, and each is checked below through the running gate rather than
    trusted.
    """
    full = os.path.abspath(path)
    out = {"plain": full}
    if os.name != "nt" or full[1:3] != ":" + os.sep:
        return out
    drive, rest = full[0], full[2:]
    out["extended-length"] = "\\\\?\\" + full
    out["administrative share"] = "\\\\localhost\\%s$%s" % (drive, rest)
    out["extended UNC"] = "\\\\?\\UNC\\localhost\\%s$%s" % (drive, rest)
    if os.path.exists(full):
        done = subprocess.run(["cmd", "/c", "@for %I in (" + full + ") do @echo %~sI"],
                              capture_output=True, text=True)
        short = done.stdout.strip()
        if short and short != full and os.path.exists(short):
            out["8.3 alias"] = short
    return out


PROTECTED_SUBJECTS = [
    "team-kits/dev-team/hooks/gate_git.py",             # versioned kit content, exists
    ".claude/hooks/gate_todo_items.py",                 # the enforcement layer, exists
    "project_memory/evidence/active/EVD-9999.yaml",     # canonical state, does NOT exist yet
]


@pytest.mark.parametrize("relative", PROTECTED_SUBJECTS)
def test_gate1_refuses_a_protected_path_however_the_filesystem_spells_it(project, relative):
    """R/B1: "the same file" is what the FILESYSTEM says, not what the text says.

    `realpath` leaves an extended-length prefix, an administrative share and its UNC host
    standing, so each of them was a second name for a protected file that no comparison of text
    recognised: measured 2026-08-05, nine of eleven spellings of a protected path were allowed
    while the plain one was refused -- through `Write`, through `sed -i` and through PowerShell
    `Set-Content` alike.

    Both tool classes per spelling, because the two halves of gate 1 reach the path by different
    routes (a payload field and a command line), and one of them alone leaves the other unmeasured.
    """
    full = os.path.join(project, *relative.split("/"))
    forms = spellings(full)
    if len(forms) < 2:
        pytest.skip("this host spells %s exactly one way" % relative)
    for label, path in sorted(forms.items()):
        rc, err = run(project, "gate_lead_write_scope.py",
                      {"hook_event_name": "PreToolUse", "tool_name": "Write", "cwd": project,
                       "tool_input": {"file_path": path, "content": "x"}})
        assert rc == 2, "Write allowed the %s spelling of %s: %s" % (label, relative, err[:300])
        command = 'sed -i "s/a/b/" "%s"' % path
        rc, err = run(project, "gate_lead_write_scope.py", bash_payload(project, command))
        assert rc == 2, "sed -i allowed the %s spelling of %s: %s" % (label, relative, err[:300])
        command = 'Set-Content -Path "%s" -Value ""' % path
        rc, err = run(project, "gate_lead_write_scope.py",
                      bash_payload(project, command, tool="PowerShell"))
        assert rc == 2, "Set-Content allowed the %s spelling of %s: %s" % (
            label, relative, err[:300])


def test_gate1_reads_a_free_path_as_free_in_every_spelling(project):
    """The counter-direction of the test above, and the expensive one.

    An identity comparison that answers "same file" too generously would refuse ordinary prose in
    a second spelling, and a gate that refuses the session's own notes is broken in the direction
    nobody notices until work stops.
    """
    for label, path in sorted(spellings(os.path.join(project, "docs", "note.md")).items()):
        rc, err = run(project, "gate_lead_write_scope.py",
                      {"hook_event_name": "PreToolUse", "tool_name": "Write", "cwd": project,
                       "tool_input": {"file_path": path, "content": "x"}})
        assert rc == 0, "the %s spelling of a free file was refused: %s" % (label, err[:300])


# -- the standard library cannot be answered from a gate's own tree (TSK-0008 B2) --------------

# A module that answers every attribute and raises nothing. THE SILENT SHAPE IS THE POINT: a stub
# that fails loudly makes the gate refuse anyway, so it would measure nothing. This one makes the
# tokeniser return nothing, which reads as "this line writes no path".
SILENT_MODULE = '''
class _Anything(object):
    def __init__(self, *a, **k):
        pass

    def __call__(self, *a, **k):
        return _Anything()

    def __getattr__(self, name):
        return _Anything()

    def __iter__(self):
        return iter(())

    def __bool__(self):
        return False

    def __str__(self):
        return ""


class _Module(object):
    def __getattr__(self, name):
        return _Anything()


import sys as _sys
_sys.modules[__name__] = _Module()
'''


def _stdlib_names_the_reader_loads(project):
    """Standard-library modules gate 1's own reading of a command line pulls in.

    ASKED OF A RUNNING INTERPRETER, not read out of an import line: the subject of the test below
    has to be the set the code actually depends on, and that set changes when the kits' reader
    does. `sys.stdlib_module_names` is the interpreter's own answer to "is this the standard
    library".
    """
    code = (
        "import os, sys\n"
        "sys.path.insert(0, os.path.join(sys.argv[1], '.claude', 'hooks'))\n"
        "import _harness\n"
        "before = set(sys.modules)\n"
        "_harness.shell_reader({'cwd': sys.argv[1]})\n"
        "fresh = (set(sys.modules) - before) & set(sys.stdlib_module_names)\n"
        "print('\\n'.join(sorted(fresh)))\n")
    done = subprocess.run([sys.executable, "-B", "-c", code, project], cwd=project,
                          capture_output=True, text=True,
                          env=dict(os.environ, CLAUDE_PROJECT_DIR=project))
    assert done.returncode == 0, done.stderr[-600:]
    return [name for name in done.stdout.split() if name]


def _apparatus_directories(project):
    """The directories a gate of this repo runs its own decision out of."""
    sys.path.insert(0, os.path.join(project, ".claude", "hooks"))
    import _harness
    return {"the gate's own directory": os.path.join(project, ".claude", "hooks"),
            "the kit hooks directory": _harness._kit_hooks_dir(project),
            "the kit root": os.path.join(project, "team-kits")}


@pytest.mark.parametrize("where", sorted(["the gate's own directory", "the kit hooks directory",
                                          "the kit root"]))
def test_a_planted_module_cannot_answer_for_a_standard_library_name(project, tmp_path, where):
    """B2: a file in a gate's own tree that is NAMED like a standard-library module.

    Measured 2026-08-05, all three directories, with a stub that raises nothing: the kits'
    tokeniser returned no tokens, `written_paths` came back empty, and gate 1 answered rc 0 with
    an empty stderr for `sed -i` into `team-kits/kernel/state.py`. Appending the kit directories
    to `sys.path` does not prevent it -- `gate_write_scope.py` and `tools/bump_kit_version.py`
    insert their own directory at position 0 while they load, so the shadow exists during an
    import the gate is in the middle of.

    BOTH ENDS IN ONE RUN: the attack must be refused AND the repo's own documented kernel command
    must still be allowed, because a finder that answered too widely would break every kit import
    instead.

    THE REASON IS ASSERTED, NOT ONLY THE EXIT CODE, and that is what makes two of these three
    parameters measure anything. Ablated 2026-08-05 (finder removed, same stub, real gate process):
    the KIT HOOKS directory flips to rc 0 -- it is the one `gate_write_scope.py` puts at
    `sys.path[0]` while it loads. The gate's OWN directory stays rc 2 without the finder, but for
    another reason entirely (the payload reader is stubbed too, so the call comes out
    uninspectable), which the reason assertion below now separates. The KIT ROOT stays rc 2 with
    the same reason either way, because by the time `tools/bump_kit_version.py` puts it at
    position 0 every module the reader needs is already in `sys.modules` -- that parameter is a
    tripwire for the day that order changes, not a measurement of the finder today.
    """
    work = str(tmp_path / ("shadow-" + where.replace(" ", "-").replace("'", "")))
    shutil.copytree(project, work)
    directory = _apparatus_directories(work)[where]
    names = _stdlib_names_the_reader_loads(work)
    assert names, "gate 1 loads no standard-library module while reading a command line"
    for name in names:
        with open(os.path.join(directory, name + ".py"), "w", encoding="utf-8") as handle:
            handle.write(SILENT_MODULE)
    rc, err = run(work, "gate_lead_write_scope.py",
                  bash_payload(work, "sed -i 's/a/b/' team-kits/kernel/state.py"))
    assert rc == 2, "a module planted in %s answered for the standard library: rc=%d %r" % (
        where, rc, err[:300])
    assert "may not write" in err, (
        "refused, but not because the path is protected -- a module planted in %s took the "
        "decision somewhere else: %r" % (where, err[:300]))
    rc, err = run(work, "gate_lead_write_scope.py", bash_payload(
        work, "PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory generate-index"))
    assert rc == 0, "the repo's own kernel command was refused: %s" % err[:300]


def test_no_module_of_this_apparatus_is_named_after_a_standard_library_module():
    """The other end of the finder, and the one that would break work rather than let it through.

    The finder answers for every name the interpreter calls standard library, so a kit -- or this
    hooks directory -- that ever ships `types.py` or `queue.py` would find its own module replaced
    by the standard one. Nothing today does; this turns red on the day something does, which is
    the day the finder needs a narrower question.
    """
    sys.path.insert(0, TEAM_KITS)
    from kernel.hashing import is_kit_dir
    directories = [HOOKS, TEAM_KITS] + [os.path.join(TEAM_KITS, name, "hooks")
                                        for name in sorted(os.listdir(TEAM_KITS))
                                        if is_kit_dir(os.path.join(TEAM_KITS, name))]
    for directory in directories:
        if not os.path.isdir(directory):
            continue
        for entry in sorted(os.listdir(directory)):
            name = entry[:-3] if entry.endswith(".py") else entry
            if not (entry.endswith(".py")
                    or os.path.isfile(os.path.join(directory, entry, "__init__.py"))):
                continue
            assert name not in sys.stdlib_module_names, (
                "%s ships %s, which the interpreter calls standard library -- the finder in "
                "_harness would answer that import from the standard library instead"
                % (directory, entry))


def test_an_exit_this_gate_did_not_make_is_not_a_verdict(project, tmp_path):
    """B2, the second half: `guarded()` lets exactly ONE exit code out of a decision.

    A gate's success exit stands AFTER `decide()` and the only other exit it raises is `refuse()`,
    so every remaining `SystemExit` came from something the decision loaded. Measured 2026-08-05:
    a module ending the process with code 0 during gate 1's decision made the gate answer rc 0 and
    write nothing at all -- the provider reads that as an allow.

    The subject is injected into a module of the KIT the gate loads, and deliberately not into a
    standard-library name: those are covered by the finder above, and a test that measured both at
    once would stay green if either alone were removed.
    """
    work = str(tmp_path / "foreign-exit")
    shutil.copytree(project, work)
    sys.path.insert(0, os.path.join(work, ".claude", "hooks"))
    import _harness
    with open(os.path.join(_harness._kit_hooks_dir(work), "_root.py"), "a",
              encoding="utf-8") as handle:
        handle.write("\nimport sys as _sys\n_sys.exit(0)\n")
    for payload in (write_payload(work, "team-kits/kernel/state.py"),
                    bash_payload(work, "sed -i 's/a/b/' team-kits/kernel/state.py")):
        rc, err = run(work, "gate_lead_write_scope.py", payload)
        assert rc == 2, "a foreign exit(0) during the decision answered rc=%d %r" % (rc, err[:300])


# -- the producer set is measured, and it depends on the payload (TSK-0008 B4) ------------------


def _reason(text):
    """The refusal WITHOUT its subject line -- the branch that answered, as the process states it."""
    return " ".join(line.strip() for line in text.splitlines()[1:] if line.strip())[:400]


def test_gate1_protects_every_reader_its_own_answer_came_from(project):
    """`decision_inputs` promises "every file this answer was computed from", and the shell reader
    is one of them -- it decides WHICH paths a command line writes.

    Measured through the refusals rather than through introspection, and RELATIONALLY so that no
    sentence from another file is quoted here: for a shell payload the kits' `gate_write_scope`
    has to be refused for the same reason `tools/bump_kit_version.py` is (both are where the
    protected area comes from) and for a different one than an ordinary kit file (which is merely
    versioned content). Before the subjects were read first, the shell reader had not been loaded
    when the producer set was taken, and it came out as ordinary kit content.

    THE SET IS PAYLOAD-DEPENDENT, and that is the honest half: a `Write` payload never loads the
    shell reader, so for that call it decided nothing and must NOT be in the set.
    """
    import _harness
    reader = os.path.relpath(os.path.join(_harness._kit_hooks_dir(project),
                                          "gate_write_scope.py"), project).replace("\\", "/")
    stamper = "tools/bump_kit_version.py"
    ordinary = "team-kits/kernel/state.py"

    def shell(relative):
        rc, err = run(project, "gate_lead_write_scope.py",
                      bash_payload(project, "sed -i 's/a/b/' " + relative))
        assert rc == 2, "%s was allowed" % relative
        return _reason(err)

    assert shell(reader) == shell(stamper), (
        "the shell reader is not refused as a producer of the protected area, although gate 1 "
        "computed this very answer with it")
    assert shell(reader) != shell(ordinary), (
        "producer and ordinary kit content answer with the same reason -- then the producer "
        "branch is not what answered")
    rc, err = run(project, "gate_lead_write_scope.py", write_payload(project, reader))
    assert rc == 2, "the shell reader was allowed through a Write"
    assert _reason(err) == shell(ordinary), (
        "a Write payload never loads the shell reader, so it cannot have produced that answer -- "
        "the producer set has to be what the call actually used")


# -- what a shell RUNS, not what it declares (TSK-0008 BUG-0012, R-a, R-b) ----------------------


def test_gate1_reads_a_function_definition_as_the_command_inside_it(project):
    """BUG-0012: this repo's documented kernel prefix, wrapped in a shell function.

    `_stage_verb` reads the declared NAME as the verb, and a verb nothing recognises is not
    read-only -- so every word of the body became a write candidate and `PYTHONPATH=team-kits` put
    the kit tree into the refusal. Measured 2026-08-05: the line below rc 2, the identical line
    without the wrapper rc 0, which stopped items being captured in one go.

    THREE COUNTER-ENDS, because the cut must not swallow a real write: the same wrapper around a
    real write stays refused, so does a bare brace group, and so does a line that writes BEFORE a
    brace token (where the brace is an operand and not a header).
    """
    kernel_line = ("PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory "
                   "generate-index")
    write_line = "sed -i 's/a/b/' team-kits/kernel/state.py"
    assert run(project, "gate_lead_write_scope.py",
               bash_payload(project, "dec () { %s ; }" % kernel_line))[0] == 0, (
        "the repo's own kernel command is refused as soon as it is wrapped in a function")
    for command in ("dec () { %s ; }" % write_line,
                    "{ %s ; }" % write_line,
                    "%s {" % write_line):
        rc, err = run(project, "gate_lead_write_scope.py", bash_payload(project, command))
        assert rc == 2, "a write survived as %r: %s" % (command, err[:300])


def test_gate1_resolves_a_relative_word_where_the_line_really_runs(project, tmp_path):
    """R-b: "we cannot say where we are" and "we are at the repo root" were one answer.

    `_walk` reports None for every absolute target, which is right for a scaffolded project and
    wrong here -- this repo's own lines start with `cd "C:/.../AgentAndSkills"`. Reading None as
    the repo root refused `cd <outside> && sed -i team-kits/...` (measured rc 2) although that
    line writes in another tree entirely, and in the other direction it left a cwd BESIDE the repo
    unread: `sed -i <repo>/team-kits/kernel/state.py` spelled relative to the parent directory was
    allowed (measured rc 0).

    All four ends in one test, because each alone is satisfied by the wrong fix: leaving the
    tracked directory unknown after `popd` would let the last case through again.
    """
    outside = str(tmp_path).replace("\\", "/")
    state = "team-kits/kernel/state.py"
    parent, name = os.path.dirname(project), os.path.basename(project)

    def shell(command, cwd=None):
        payload = bash_payload(project, command)
        payload["cwd"] = cwd or project
        return run(project, "gate_lead_write_scope.py", payload)

    assert shell('cd "%s" && sed -i "s/a/b/" %s' % (outside, state))[0] == 0, (
        "a line that writes outside the repo was refused because the gate assumed the root")
    assert shell('sed -i "s/a/b/" %s' % state, cwd=outside)[0] == 0, (
        "a call whose cwd is outside the repo was judged as if it ran in the repo")
    assert shell('sed -i "s/a/b/" %s/%s' % (name, state), cwd=parent)[0] == 2, (
        "a relative word reaching INTO the repo from beside it was not read")
    assert shell('cd .claude/hooks && rm gate_todo_items.py')[0] == 2, (
        "a relative walk INSIDE the repo stopped being followed")
    assert shell('pushd "%s" ; popd ; sed -i "s/a/b/" %s' % (outside, state))[0] == 2, (
        "the gate lost the directory over pushd/popd and stopped looking")


def test_gate3_leaves_an_environment_prefix_in_front_of_a_commit(project, tmp_path, open_item):
    """R-a: a stage with no verb runs nothing, so it cannot move the tree.

    `_stage_verb` skips a `VAR=value` prefix and reports "", which `written_paths` reads as "this
    stage writes nothing" and the shape check did not -- so the PowerShell spelling of this repo's
    own environment prefix counted as a change to the working tree and every commit behind it was
    refused (measured 2026-08-05, rc 2).

    The counter-end is in the same run: a line that really writes before committing stays refused.
    """
    work = str(tmp_path / "env-prefix")
    shutil.copytree(project, work)
    payload = bash_payload(work, "git commit -m wip")
    digest = re.search(r"diff:[0-9a-f]{64}",
                       run(work, "gate_commit_evidence.py", payload)[1]).group(0)
    subprocess.run([sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory",
                    "evidence", "--kind", "review", "--result", "pass", "--related", open_item,
                    "--summary", "verifier PASS for " + digest,
                    "--artifact-ref", "staging/verdict.md"],
                   cwd=work, env=dict(os.environ, PYTHONPATH=os.path.join(work, "team-kits")),
                   check=True, capture_output=True, text=True)
    assert run(work, "gate_commit_evidence.py", payload)[0] == 0, "wrong precondition"
    prefixed = bash_payload(work, '$env:PYTHONPATH="team-kits"; git commit -m wip',
                            tool="PowerShell")
    rc, err = run(work, "gate_commit_evidence.py", prefixed)
    assert rc == 0, "an environment prefix was read as a change to the working tree: %s" % err[:400]
    assert run(work, "gate_commit_evidence.py",
               bash_payload(work, "echo more >> docs/note.md && git commit -m wip"))[0] == 2, (
        "a line that writes before it commits was allowed")


# A module that leaves a trace when it is EXECUTED, and nothing else. The trace is the measurement:
# a planted file that is never imported cannot decide anything, and no exit code says so.
MARKING_MODULE = 'import os\nopen(%r, "w").close()\n'


def test_a_kit_directory_does_not_outlive_its_own_import_on_sys_path(project, tmp_path):
    """The kits' modules put their own directory at `sys.path[0]` while they load, and it stayed.

    `gate_write_scope.py` inserts its directory at position 0 as it is executed, and a gate loads
    it while reading a command line. Everything a gate imports AFTERWARDS -- `yaml`, which parses
    the Evidence record gate 3 judges by -- was then answered out of a kit directory instead of out
    of site-packages. `StandardLibraryWins` does not cover that: `yaml` is not a name the
    interpreter calls standard library. The same restore stands around the stamper's execution in
    `_bump_tool`, which inserts its own directory the same way.

    THE SUBJECT IS THE EXECUTION of the planted file, not an exit code: a module that is imported
    runs, and running is what it would take to decide anything, while both outcomes happen to end
    in a refusal. Measured 2026-08-05 through the real gate process.
    """
    work = str(tmp_path / "path-outlives")
    shutil.copytree(project, work)
    sys.path.insert(0, os.path.join(work, ".claude", "hooks"))
    import _harness
    marker = os.path.join(str(tmp_path), "the-planted-module-ran")
    with open(os.path.join(_harness._kit_hooks_dir(work), "yaml.py"), "w",
              encoding="utf-8") as handle:
        handle.write(MARKING_MODULE % marker)
    rc, err = run(work, "gate_commit_evidence.py", bash_payload(work, "git commit -m wip"))
    assert not os.path.exists(marker), (
        "a file planted in the kit hooks directory answered `import yaml` for gate 3 -- and that "
        "is what decides whether an Evidence record says pass")
    assert rc == 2 and "diff:" in err, (
        "wrong precondition: gate 3 did not reach the Evidence store at all (%s)" % err[:200])


# -- where the shell really is (TSK-0011 F1, F2) -------------------------------


def test_gate1_does_not_follow_a_move_the_shell_would_not_make(project, tmp_path):
    """A directory verb moves the gate's base only where a shell would really land.

    The reading that stood here counted every `cd`, `pushd` and `popd` as done. A shell does not:
    measured 2026-08-05 in a real bash, each of the seven lines below leaves the shell exactly
    where it was and REWRITES the protected file it names relatively -- while the gate had already
    followed the move out of the tree and answered rc 0 for all of them.

    THE COUNTER-DIRECTION IS IN THE SAME RUN, and it is the expensive one: a gate that simply
    stopped following directory verbs would pass the first half and refuse every line that really
    did leave the tree. `cd -` and a bare `cd` are both in it because they are different branches
    that used to be one -- the operand filter dropped every word starting with a dash, `-` among
    them, so `cd -` silently went HOME and no test could see the difference.
    """
    outside = str(tmp_path).replace("\\", "/")
    write = 'sed -i "s/a/b/" team-kits/kernel/state.py'

    def shell(command):
        return run(project, "gate_lead_write_scope.py", bash_payload(project, command))

    stays = {
        "cd into an absolute directory that is not there": "cd /nope-not-there ; " + write,
        "cd into a relative directory that is not there": "cd nope-does-not-exist ; " + write,
        "popd with nothing pushed": "popd ; " + write,
        "pushd with an empty stack": "pushd ; " + write,
        "cd - after a cd that went out": 'cd "%s" ; cd - ; %s' % (outside, write),
        "a cd inside a subshell": '( cd "%s" ) ; %s' % (outside, write),
        "pushd out, then a bare pushd that swaps back": 'pushd "%s" ; pushd ; %s' % (outside,
                                                                                     write),
    }
    for label, command in sorted(stays.items()):
        rc, err = shell(command)
        assert rc == 2, "the gate followed %s and let the write through: %s" % (label, err[:200])
    moves = {
        "cd into a directory that IS there": 'cd "%s" ; %s' % (outside, write),
        "pushd into a directory that IS there": 'pushd "%s" ; %s' % (outside, write),
        "a bare cd, which goes home": "cd ; " + write,
        "cd ~, which is the same place spelled out": "cd ~ ; " + write,
    }
    for label, command in sorted(moves.items()):
        rc, err = shell(command)
        assert rc == 0, "the gate did not follow %s and refused a write outside the repo: %s" % (
            label, err[:200])


def test_gate1_cuts_a_declaration_head_because_it_is_one(project):
    """The head of a function declaration, not "there is a bracket somewhere in front of the brace".

    The cut exists so this repo's own kernel prefix survives being wrapped in a function
    (BUG-0012). Asking for a bracket ANYWHERE in the head answers yes for heads that declare
    nothing, and then the cut throws away the write standing in front of the brace: measured
    2026-08-05, both lines below wrote into a kit file with rc 0.

    THE OTHER END IS THE REASON THE CUT IS NARROW AT ALL: the same wrapper around a real write
    stays refused, and so does a write in front of a brace that is only an operand -- those are
    measured in `test_gate1_reads_a_function_definition_as_the_command_inside_it`. What is new here
    is the keyword form, which the grammar has and the old head test could not see.
    """
    kernel_line = ("PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory "
                   "generate-index")
    write = 'sed -i "s/a/b/" team-kits/kernel/state.py'
    for command in ("%s $(true) {" % write, "arr=(a b) %s {" % write):
        rc, err = run(project, "gate_lead_write_scope.py", bash_payload(project, command))
        assert rc == 2, "a head that declares nothing was cut, losing the write: %r" % command
    for command in ("dec () { %s ; }" % kernel_line, "function dec { %s ; }" % kernel_line):
        rc, err = run(project, "gate_lead_write_scope.py", bash_payload(project, command))
        assert rc == 0, "a real declaration was not recognised: %r (%s)" % (command, err[:200])


# -- what a line writes, measured against the shell itself (TSK-0013 F1, F2) --------------------

# A path inside a protected tree, spelled RELATIVELY, and a write into it. Which tree it lands in is
# decided by where the shell stands when it runs, so it is the subject every shape below is measured
# with.
RELATIVE_TARGET = "team-kits/kernel/state.py"
RELATIVE_WRITE = 'sed -i "s/a/b/" %s' % RELATIVE_TARGET

# WHERE A DIRECTORY VERB STANDS, and whether the SHELL ITSELF is what runs it there. The first
# axis of the table below, and the one `_harness._runs_in_the_shell_itself` answers.
IN_THE_SHELL, IN_A_CHILD = "the shell itself", "a child"
POSITIONS = {
    "run by the shell itself": ("%(move)s ; %(write)s", IN_THE_SHELL),
    "glued to its terminator": ("%(move)s;%(write)s", IN_THE_SHELL),
    "in a brace group, which groups and is no child": ("{ %(move)s ; } ; %(write)s", IN_THE_SHELL),
    "with its own output redirected": ("%(move)s > /dev/null ; %(write)s", IN_THE_SHELL),
    "after a group that closed": ("( true ) ; %(move)s ; %(write)s", IN_THE_SHELL),
    "after a group whose list went to the background":
        ("( true & ) ; %(move)s ; %(write)s", IN_THE_SHELL),
    "behind a backgrounded command": ("true & %(move)s ; %(write)s", IN_THE_SHELL),
    "behind a glued and": ("true&&%(move)s ; %(write)s", IN_THE_SHELL),
    "in a group": ("( %(move)s ) ; %(write)s", IN_A_CHILD),
    "in a group opened before a terminator": ("( true ; %(move)s ) ; %(write)s", IN_A_CHILD),
    "in a group opened before an and": ("( true && %(move)s ) ; %(write)s", IN_A_CHILD),
    "in a group opened before an or": ("( false || %(move)s ) ; %(write)s", IN_A_CHILD),
    "in a group inside a group": ("( ( %(move)s ) ) ; %(write)s", IN_A_CHILD),
    "in a group glued to the terminator behind it": ("(%(move)s);%(write)s", IN_A_CHILD),
    "in a background list": ("%(move)s & %(write)s", IN_A_CHILD),
    "in a background list with a command behind it": ("%(move)s & true ; %(write)s", IN_A_CHILD),
    "in an and-or list backgrounded at its end": ("%(move)s && true & %(write)s", IN_A_CHILD),
    "as the first stage of a pipeline": ("%(move)s | true ; %(write)s", IN_A_CHILD),
    "as the last stage of a pipeline": ("true | %(move)s ; %(write)s", IN_A_CHILD),
}

# WHERE THE MOVE LEAVES EACH OF THE TWO READERS OF THIS LINE -- the SHELL and the gate. Two columns
# and not one, because the reader is knowingly stricter than the shell in places and a single column
# could only be kept by leaving those places out of the table, which is the beschneiden DEC-0016 is
# about.
#
# FOUR LANDINGS, AND THE FOURTH IS THIS ROUND'S AXIS (DEC-0018). Three of them are places a shell
# can be -- at the target the move names, where it already stood, or in the home directory, which is
# neither tree. `LOST` is only ever the READER's: a move it cannot compute leaves it nowhere it can
# name, and every relative word from there is refused. That answer used to be written as a BRANCH
# over the verb (`popd` alone had it), so it had no value here and no cell -- measured 2026-08-07,
# seven line shapes with the base outside the tree were rc 0 while bash rewrote the protected file.
# `UNCLAIMED` is the third answer for the SHELL: this reader makes no claim about what a word in
# FRONT of a command name does with it, so the table does not either.
AT_TARGET, STAYS_PUT, HOME, LOST, UNCLAIMED = (
    "at the target", "nowhere", "the home directory", "nowhere it can name", None)
MOVES = {
    "cd to a directory that is there": ("cd %(to)s", AT_TARGET, AT_TARGET),
    "cd with a second operand the shell rejects": ("cd %(to)s x", STAYS_PUT, LOST),
    "cd with an option the shell rejects": ("cd -q %(to)s", STAYS_PUT, LOST),
    # POSIX Utility Syntax Guideline 10 -- the shell's grammar, so this reader can account for it
    "cd behind the end of the options": ("cd -- %(to)s", AT_TARGET, AT_TARGET),
    # ...and an option the shell ACCEPTS is the friction that costs (H29): the shell moves and this
    # reader gives the position up, and only a table with two columns can carry that cell at all
    "cd with an option the shell accepts": ("cd -L %(to)s", AT_TARGET, LOST),
    "cd into a directory that is not there": ("cd %(to)s/nope-not-there", STAYS_PUT, LOST),
    "cd into a relative directory that is not there": ("cd nope-does-not-exist", STAYS_PUT, LOST),
    "a bare cd, which goes home": ("cd", HOME, HOME),
    # THE QUOTING IS THE WHOLE CELL: a shell expands a tilde and then removes quoting, so a QUOTED
    # tilde is a directory named `~` and nothing else -- while a reader that expands the reading it
    # is handed expands what the quoting was there to suppress (H31).
    "cd to a tilde the quoting keeps": ('cd "~"', STAYS_PUT, LOST),
    "cd to a tilde the shell expands": ("cd ~", HOME, HOME),
    # A TARGET ONLY THE SHELL CAN COMPUTE. The variable is set in the ENVIRONMENT of the arbitrating
    # shell and nowhere else, which is the real shape of it: what the gate is handed is the text,
    # and the text is not what the shell uses. (`_changes_the_protected_file` sets it; the gate
    # process is started without it.)
    "cd to a target this reader cannot name": ('cd "$%(var)s"', AT_TARGET, LOST),
    "pushd to a directory that is there": ("pushd %(to)s", AT_TARGET, AT_TARGET),
    "pushd with a second operand the shell rejects": ("pushd %(to)s x", STAYS_PUT, LOST),
    "popd with nothing pushed": ("popd", STAYS_PUT, STAYS_PUT),
    "pushd with an empty stack": ("pushd", STAYS_PUT, STAYS_PUT),
}

# WHERE THE LINE STANDS WHEN THE MOVE HAPPENS -- the axis DEC-0018 asks for, and the one the table
# had only one value of. It is not a spelling but the only property that decides what a relative
# word names: the base is in the tree the write points into, or it is not. With the base INSIDE,
# staying is the refusing direction; with the base OUTSIDE, every move this reader cannot compute
# may be the one that goes back IN, and staying is the passing one.
BASES = {
    "with the base inside the tree": ("", "%(out)s", "R_OUT"),
    "with the base outside it": ("cd %(out)s ; ", '"%(here)s"', "R_HERE"),
}
# What the arbitrating shell is told about the two trees, and the gate is not. A directory verb
# whose target is only in the environment is the shape H16 carries: the gate is handed the text.
TREE_VARIABLES = {"R_OUT": "outside", "R_HERE": "the sandbox"}


def _reader():
    """The module under test, imported once -- the table's axes are GENERATED out of it."""
    sys.path.insert(0, HOOKS)
    import _harness
    return _harness


def _other_spellings(word):
    """Spellings that differ from `word` and that a case-folding reader cannot tell from it.

    NOT A LIST OF CASES BUT THE FOLD ITSELF: the kits' `_stage_verb` hands the verb out through
    `str(token).lower()`, so every spelling here is one that reader answers `word` for, and a POSIX
    shell answers `command not found` for. What makes them different words is generated from the
    word, so a verb this repo gains is crossed in its miscased spellings on the day it appears.
    """
    return sorted({word.upper(), word.capitalize(), word.title()} - {word})


def _verb_shapes(harness):
    """One move per verb of every shell this reader knows, per spelling it cannot tell apart.

    DEC-0016: the enumeration the reader decides from (`_harness.SHELLS`) GENERATES the values of
    this axis, so the checked set cannot be narrower than the deciding one. Both columns are derived
    from the same claim -- this line is sent to the Bash tool, so the shell moves exactly where a
    word is spelled exactly like a verb of the POSIX table, and so does the reader.

    A SPELLING THE POSIX TABLE DOES NOT CARRY IS A COMPUTED NON-MOVE ON BOTH SIDES, not a doubt:
    the shell answers `command not found` and stays, and `_harness._directory_role` answers None,
    which is the one branch of `follow` that is an ANSWER rather than a failure to compute.

    A POP HAS NOTHING TO RETURN TO HERE, so its cell stays put in every spelling and carries
    little; the pop shapes that carry the weight are in `LOOSE_SHAPES`, where a stack can be built
    first. Generated all the same, because a value left out is the cut DEC-0016 is about.
    """
    posix = harness.SHELLS["Bash"]["verbs"]
    known = {}
    for shell in sorted(harness.SHELLS):
        known.update(harness.SHELLS[shell]["verbs"])
    out = {}
    for verb, role in sorted(known.items()):
        for spelling in [verb] + _other_spellings(verb):
            runs = posix.get(spelling) == role and role != harness._POP
            where = AT_TARGET if runs else STAYS_PUT
            out["%s spelled %r" % (role, spelling)] = (
                spelling if role == harness._POP else "%s %%(to)s" % spelling, where, where)
    return out


def _substitution_shapes(harness):
    """One line per pair the reader reads as a command substitution, for the shell that arbitrates.

    THE ENUMERATION GENERATES ITS OWN CELLS (DEC-0016), and here it has to: no reader this
    apparatus borrows from knows what a substitution is, so `_harness.SHELLS[...]["substitutions"]`
    is an enumeration with nothing to derive it from. The cell therefore measures BOTH ends of the
    entry -- the shell REALLY runs the command inside the pair (a dead entry writes nothing and the
    first column says so), and the gate refuses the write it hides (a missing entry passes it, and
    the second column says so).

    The verb in front is a READ-ONLY one on purpose: a substitution behind a writing verb is
    refused for the verb's sake, which would make the cell green for a reason that is not this one.
    """
    out = {}
    for opener, closer in harness.SHELLS["Bash"]["substitutions"]:
        out["a write in a %s%s substitution behind a read-only verb" % (opener, closer)] = (
            "echo %s%%(write)s%s" % (opener, closer), True, True)
    return out


def _quoted_write_shapes(harness):
    """The quoting axis over the PLAIN relative write -- the half of it where no tilde is involved.

    WHY IT IS HERE AND NOT ONLY IN THE TILDE CHECK SET: `_quotings` exists because where the quoting
    stands decides whether an expansion happens, and a reader that answered that question by
    refusing quoted words outright would satisfy the tilde half and break every ordinary path. So
    every run of an ordinary relative path is quoted in turn, and every one of these cells has the
    same two columns -- a shell writes the protected file exactly as it does without the quoting
    (`_compat.shell_words` resolves it for the reader, measured there), and the gate refuses.
    """
    out = {}
    for label, word in sorted(_quotings(harness, RELATIVE_TARGET).items()):
        if label != UNQUOTED:
            out["a write into a relative path %s" % label] = (
                'sed -i "s/a/b/" %s' % word, True, True)
    return out


def _steps_over(reader, word):
    """Does the kits' `_stage_verb` really walk past this word to find the verb behind it?"""
    return reader._stage_verb([word, "cd", "x"]) == "cd"


def _witnesses(test):
    """Words a branch's own condition offers as something it steps over.

    THE CONSTANTS THE CONDITION COMPARES AGAINST, in the two shapes a condition can carry them:
    the member of a list (`low in ("sudo", ...)`) and the substring of a test (`"=" in low`). The
    second needs the constant put INTO a word to be one, so both are offered and the caller proves
    each against the function that runs -- a candidate the reader does not step over drops out
    there, and a branch left with none is reported rather than skipped.
    """
    out = []
    for node in ast.walk(test):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value:
            out.extend([node.value, "a%sb" % node.value])
    return out


def _skipped_words(harness):
    """The words the kits' `_stage_verb` steps over while looking for the verb -- from EVERY branch.

    READ OUT OF THE FUNCTION THAT RUNS, never typed here: its source is parsed, every branch whose
    body is a `continue` is one that steps over something, and the words come out of that branch's
    own condition (`_witnesses`) and are then PROVEN by asking the running function.

    DEC-0018, AND THIS IS THE HALF THAT COST A ROUND: a skip written as a PREDICATE generates no
    value the way a skip written as a LIST does. The reader has both -- `low in ("sudo", ...)` and
    `"=" in low and not low.startswith("-")` -- and the second had no cell in 638, so an assignment
    in front of a directory verb was crossed nowhere while `_is_the_command_name` decided about it.
    Reading branches instead of tuples is what makes the difference; proving each witness against
    the function is what keeps the values honest.

    THE PUNCTUATION BRANCH DROPS OUT BY A PROPERTY and not by its position: what it holds is the
    shell's grouping punctuation, and punctuation is what `_harness._SYNTAX_CHARACTERS` defines --
    a word made only of it is syntax and is allowed to stand in front of a command name.
    """
    words, empty = [], []
    for branch, proven in _skip_branches(_kits_reader(harness)):
        if not proven:
            empty.append(branch)
        elif not all(set(word) <= harness._SYNTAX_CHARACTERS for word in proven):
            words.extend(proven)
    assert not empty, (
        "these branches of the kits' `_stage_verb` step over a word this test could not name, so "
        "they are crossed nowhere: %s" % empty)
    return sorted(set(words))


def _kits_reader(harness):
    harness._add_kit_paths(ROOT)
    return harness._from_kit("gate_write_scope")


def _skip_branches(reader):
    """`[(the branch as text, the words it is PROVEN to step over)]` of the kits' `_stage_verb`.

    THE BRANCHES AND NOT THE TUPLES IN THEM, which is what makes a skip written as a predicate
    visible at all (DEC-0018). Kept apart from `_skipped_words` on purpose: the test that asks
    whether every branch has a cell must not ask the function that BUILDS the cells, or the two
    agree by construction and a generator that reads only tuples stays green.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(reader._stage_verb)))
    branches = [node for node in ast.walk(tree) if isinstance(node, ast.If)
                and node.body and all(isinstance(step, ast.Continue) for step in node.body)]
    assert branches, (
        "the kits' `_stage_verb` steps over nothing any more, so the axis that crosses what it "
        "steps over could not be generated")
    return [(ast.unparse(branch.test),
             sorted({word for word in _witnesses(branch.test) if _steps_over(reader, word)}))
            for branch in branches]


# The value of the quoting axis that leaves the word as it was. Named once, because both the
# generator and the check that the axis measured ANYTHING have to mean the same value by it.
UNQUOTED = "with no quoting in it"


def _quotable_runs(harness, word):
    """[(what this run is, start, stop)] -- the runs of `word` a shell can be told to keep literal.

    TWO DEFINITIONS OF THE READER STRUCTURE A WORD HERE, and neither is a list: the separators cut
    it into spans (`_harness._PATH_SEPARATORS`), and a leading tilde opens a prefix that ENDS at the
    first of them (`_harness._tilde_prefix`) -- so the tilde and the rest of that prefix are two
    runs and not one. That split is the whole point of the axis: quoting either of them keeps the
    word literal in a shell, and quoting anything BEHIND them changes nothing about the expansion.
    """
    runs, start = [], 0
    if harness._tilde_prefix(word) is not None:
        runs.append(("the tilde itself", 0, len(harness._TILDE)))
        start = len(harness._TILDE)
    separators, opened = 0, start
    for index in range(start, len(word) + 1):
        if index < len(word) and word[index] not in harness._PATH_SEPARATORS:
            continue
        if index > opened:
            runs.append(("the rest of the tilde prefix" if runs and not separators
                         else "the span %d separators in" % separators, opened, index))
        opened, separators = index + 1, separators + 1
    return runs


def _quotings(harness, word):
    """{label: `word` with one run of it quoted} -- generated out of what quoting IS, not listed.

    THE AXIS IS WHERE THE QUOTING STANDS. A shell removes quoting character by character and
    expands the tilde prefix BEFORE it does, so a word that carries quoting somewhere is not a word
    whose expansion was suppressed -- only quoting inside the prefix suppresses anything. The
    spellings come from the reader's own alphabet (`shlex.quotes` and its escape) instead of from
    `"` alone, and the places come from `_quotable_runs`.

    THIS IS THE AXIS THAT WAS MISSING, and its absence was a hole rather than a gap in coverage.
    Measured 2026-08-07 through the real gate with a real bash as arbiter over the file: 0 of 1440
    cells and 0 of the 615 tilde subjects carried quoting in the target word, and
    `sed -i "s/a/b/" ~+/"team-kits"/kernel/state.py` was rc 0 while bash rewrote the protected file
    -- the same shape reaching `.claude/settings.json`, `.claude/hooks/_harness.py` and
    `project_memory/` (`docs/POST_V2_WISHLIST.md` H33).
    """
    reader = shlex.shlex("", punctuation_chars=True)
    out = {UNQUOTED: word}
    for what, start, stop in _quotable_runs(harness, word):
        for mark in sorted(set(reader.quotes)):
            out["with %s quoted by %s" % (what, mark)] = (
                word[:start] + mark + word[start:stop] + mark + word[stop:])
        out["with %s escaped" % what] = word[:start] + reader.escape + word[start:]
    return out


def _prefix_shapes(words):
    """One move per word the kits' reader steps over to find the verb.

    THE SECOND HALF OF DEC-0016: the reader decides the verb out of these branches, so the branches
    generate the values. The reader's column is `LOST`, which is what `_harness._is_the_command_name`
    now costs -- a word in front of the command name is a command of its own, and whether it hands
    the verb to a CHILD (`env cd` never reaches the builtin) or leaves it in the shell (`command cd`
    does) is not readable from here, so the position is given up. The shell's column is UNCLAIMED
    for the same reason, from the other side.
    """
    return {"cd behind %r, which the kits' reader steps over" % word:
            ("%s cd %%(to)s" % word, UNCLAIMED, LOST) for word in words}

# What has no directory verb in it at all, or more than one. WHERE A COMMAND ENDS is its own
# question (`_harness._cuts`), and so is a second move that undoes the first -- neither is a cell of
# the cross above, so both stand here with both columns written down and measured like every other.
# `%(here)s` is the tree the line runs in, spelled absolutely: a POP is only dangerous when the top
# of the stack lies OUTSIDE while the position is INSIDE, and that takes two directories.
LOOSE_SHAPES = {
    # a command that has ENDED takes nothing with it: what follows is a command of its own, and the
    # verb in front of it says nothing about the words behind it
    "a write behind a backgrounded read": ("echo hi & %(write)s", True, True),
    "a write behind a backgrounded write": ('sed -i "s/x/y/" docs/note.md & %(write)s', True, True),
    "a write behind a glued terminator": ("(echo hi);%(write)s", True, True),
    "a write behind a glued and": ("(echo hi)&&%(write)s", True, True),
    "a redirect glued to the terminator in front of it": ("echo hi;>%(target)s", True, True),
    "a redirect glued to a terminator behind a group": ("(echo hi);>%(target)s", True, True),
    "a redirect behind a spaced terminator": ("echo hi ; > %(target)s", True, True),
    "a write behind a spaced terminator": ("echo hi ; %(write)s", True, True),
    "a write behind a group that read": ("( echo hi ) ; %(write)s", True, True),
    "a write fed through a pipe": ("echo hi | %(write)s", True, True),
    "a write behind a pipe glued to a bracket": ("(echo hi)|%(write)s", True, True),
    "a write behind a pipe that carries stderr too": ("echo hi |& %(write)s", True, True),
    "a write behind a pipe that carries stderr, glued": ("echo hi|&%(write)s", True, True),
    "a move behind a pipe that carries stderr": ("echo hi |& cd %(out)s ; %(write)s", True, True),
    "a move in front of a pipe that carries stderr": ("cd %(out)s |& true ; %(write)s", True, True),
    "a move behind a pipe glued to a bracket": ("(echo hi)|cd %(out)s ; %(write)s", True, True),
    # two moves, where the second is what decides
    "a move and a move back": ("cd %(out)s ; cd - ; %(write)s", True, True),
    "a move and a second move that stays": ("cd %(out)s ; cd . ; %(write)s", False, False),
    "a move continued conditionally": ("cd %(out)s && cd . ; %(write)s", False, False),
    "a push and a pop": ("pushd %(out)s ; popd ; %(write)s", True, True),
    "a push and a pop of the top by index": ("pushd %(out)s ; popd +0 ; %(write)s", True, True),
    "a push and a bare push that swaps back": ("pushd %(out)s ; pushd ; %(write)s", True, True),
    "a push and one pop too many": ("pushd %(out)s ; popd ; popd ; %(write)s", True, True),
    # A POP WITH THE STACK OUTSIDE AND THE POSITION INSIDE. The one direction in which STAYING is
    # not the careful answer, and it was a hole in one tool call: the shell rejects the operand
    # list, stays inside and rewrites the protected file, while the base had been popped out.
    "a pop whose operand the shell rejects":
        ('cd %(out)s ; pushd "%(here)s" ; popd x ; %(write)s', True, True),
    "a pop with an option the shell rejects":
        ('cd %(out)s ; pushd "%(here)s" ; popd -q ; %(write)s', True, True),
    "a pop of an index the stack does not have":
        ('cd %(out)s ; pushd "%(here)s" ; popd +9 ; %(write)s', True, True),
    "a pop that only drops the entry": ('cd %(out)s ; pushd "%(here)s" ; popd -n ; %(write)s',
                                        True, True),
    "a push that only adds an entry, then a pop":
        ('cd %(out)s ; pushd -n "%(here)s" ; popd ; %(write)s', True, True),
    # A PUSH THIS READER COULD NOT MAKE IS A PUSH THE SHELL MAY WELL HAVE MADE, and then its stack
    # holds an entry this one does not -- so the bare pop behind it goes back INTO the tree while
    # this reader would have stayed outside. Measured 2026-08-07: rc 0 before, and the shell really
    # rewrites the protected file.
    "a push this reader cannot make, and a pop the shell can":
        ('R="%(here)s" ; pushd "$R" ; cd %(out)s ; popd ; %(write)s', True, True),
    # ...and the counter-end, which is what stops "never follow a pop": here the shell really does
    # go back out, and the write must stay allowed
    "a pop the shell really makes, back out of the tree":
        ('cd %(out)s ; pushd "%(here)s" ; popd ; %(write)s', False, False),
    # THE BASE NEVER LEAVES THE REPO HERE, and the write still lands in the protected tree: what
    # decides is the SUBTREE the base stands in, not the repo boundary. Measured 2026-08-07: rc 0
    # before, and bash really rewrites the protected file.
    "a move inside the tree the reader cannot compute":
        ('cd docs ; command cd .. ; %(write)s', True, True),
    # a closer that stands INSIDE the substitution's own quoting -- see `_harness._closings`
    "a write in a substitution whose closer is quoted":
        ('echo $(sed -i "s/a/)/" %(target)s)', True, True),
}


def _reaches_the_tree(landing, base_inside):
    """Does an actor that ended up HERE resolve the relative write into the protected tree?

    The one question both columns are made of, and it needs the base to answer -- which is why the
    base is an axis: `AT_TARGET` is the tree when the line started outside it and is not when it
    started inside, and `STAYS_PUT` is exactly the other way round.
    """
    if landing == HOME:
        return False  # neither tree, whichever direction the line ran in
    return base_inside if landing == STAYS_PUT else not base_inside


def _crossed():
    """`{label: (template, does the shell write the protected file, does the gate refuse)}`.

    THE COLUMNS ARE DERIVED, NOT COLLECTED, and that is DEC-0014 applied to this table: a relative
    write lands in the protected tree UNLESS the shell ran the WORD as the verb this reader takes it
    for, ran it ITSELF, could account for its operands and could make the move -- which are exactly
    the conditions `_harness.WorkingDirectory` claims for itself. Every one of them is an axis here,
    so a cell nobody thought about is still in the table. THE VALUES of those axes are generated by
    the enumerations the reader decides from (`_verb_shapes`, `_prefix_shapes`,
    `_substitution_shapes`), which is DEC-0016.

    AND THE CONDITION THAT WAS WRITTEN AS A BRANCH IS AN AXIS TOO, which is DEC-0018 and this
    round's correction: where the base STANDS decides what "staying" means, so `BASES` crosses every
    shape twice. Of the 32 moves generated before, 25 pointed out of the tree, 7 nowhere and NONE
    back in -- so the direction in which staying is the passing answer had no cell at all, and seven
    line shapes were rc 0 with the shell writing the protected file.

    TWO COLUMNS, because one could only be kept by leaving out every shape the reader is knowingly
    too strict about -- and leaving them out is what made the miscased verb and the word in front of
    it invisible for two rounds. `test_the_shell_writes_where_the_table_of_line_shapes_says` takes
    the first column from a real shell, cell by cell, and says so instead of passing when it
    disagrees; `test_gate1_refuses_a_line_exactly_where_the_shell_would_write` takes the second from
    a real gate process and asserts the invariant that binds them: where the shell writes, the gate
    refuses.

    WHAT IS STILL NOT IN HERE: a directory verb inside `while ... do` or inside `if` (H24 in
    `docs/POST_V2_WISHLIST.md`). Both come out rc 2 while the shell really moves, and they are
    measured as friction in `docs/reviews/2026-08-05-tsk0015-measurements.md` (section 6) instead.
    """
    harness = _reader()
    out = {}
    moves = dict(MOVES)
    moves.update(_verb_shapes(harness))
    moves.update(_prefix_shapes(_skipped_words(harness)))
    for base, (prefix, target, variable) in BASES.items():
        for position, (frame, whose) in POSITIONS.items():
            for move, (line, shell_where, reader_where) in moves.items():
                in_the_shell = whose == IN_THE_SHELL
                # A MOVE THE SHELL RUNS IN A CHILD IS A COMPUTED NON-MOVE FOR BOTH, and that is why
                # the reader does not lose its position there either: `follow` proves the childhood
                # before it asks anything it could fail to compute. UNCLAIMED stays UNCLAIMED in
                # every position, and that is not a convenience: a word this reader says nothing
                # about can make the frame around it something else entirely -- measured,
                # `true | ! cd <target> ; <write>` is a syntax error in bash and NOTHING in the
                # line runs, the write included.
                reader_lands = reader_where if in_the_shell else STAYS_PUT
                base_inside = not prefix
                writes = (UNCLAIMED if shell_where is UNCLAIMED
                          else _reaches_the_tree(shell_where if in_the_shell else STAYS_PUT,
                                                 base_inside))
                refuses = (reader_lands == LOST
                           or _reaches_the_tree(reader_lands, base_inside))
                out["%s -- %s -- %s" % (move, position, base)] = (
                    prefix + frame.replace("%(move)s", line.replace("%(to)s", target)
                                           .replace("%(var)s", variable)),
                    writes, refuses)
    out.update(LOOSE_SHAPES)
    out.update(_substitution_shapes(harness))
    out.update(_quoted_write_shapes(harness))
    return out


LINE_SHAPES = _crossed()


def _line(template, outside, here):
    return template % {"out": '"%s"' % outside, "write": RELATIVE_WRITE,
                       "target": RELATIVE_TARGET, "here": str(here).replace("\\", "/")}


def _posix_shells():
    """Every shell on this host that COULD arbitrate -- candidates, never a decision.

    Which of them sees this filesystem is measured by the caller, not assumed here: on Windows the
    first `bash` on PATH is the WSL launcher, and its `C:/...` is a different tree. The last
    candidate is derived rather than typed -- the shell that ships beside the version control
    system this repo already requires.
    """
    out = []
    for directory in (os.environ.get("PATH") or "").split(os.pathsep):
        for name in ("bash.exe", "bash"):
            out.append(os.path.join(directory, name))
    vcs = shutil.which("git")
    if vcs:
        out.append(os.path.join(os.path.dirname(os.path.dirname(vcs)), "bin", "bash.exe"))
    return [path for path in out if os.path.isfile(path)]


def _changes_the_protected_file(shell, sandbox, line, outside=""):
    """Run `line` in `sandbox` and report whether the protected file it names really changed.

    CHANGED, not "holds what the write puts there": a redirect TRUNCATES, and a criterion that
    looked for the new content read an emptied file as untouched -- measured 2026-08-05, which is
    how `echo hi;>team-kits/<file>` looked harmless while it was destroying the file.

    THE TWO TREES ARE ALSO IN THE ENVIRONMENT (`TREE_VARIABLES`), and only here: a line whose target
    stands in a variable is a line whose text says nothing about where it goes, and the gate is
    started without them (`run`).

    AND THE SHELL'S DIRECTORY STATE IS SET, NOT INHERITED, BECAUSE `cwd` IS NOT ALL OF IT -- through
    `_sandbox.sandbox_environment`, which is the same answer the scripts a round writes beside this
    file stand on, so there is one of it rather than two that drift. WHICH names those are is that
    module's answer and not this docstring's: a word that does not name a directory is resolved out
    of the shell's own state, and pieces of that state come in through the ENVIRONMENT -- `~-` reads
    `OLDPWD`, a bare `~` reads `HOME`, a relative `cd` word is looked up along `CDPATH`. A suite
    started in the tree it measures hands the shell that tree in `OLDPWD` -- and `~-` is a subject
    of this check set, so one line
    with a perfectly correct `cwd` rewrote `team-kits/kernel/state.py` of THIS repo. Measured
    2026-08-07 in isolation: with `cwd` a sandbox and `OLDPWD` another tree, `printf "%s\\n" ~-`
    prints the other tree and `sed -i "s/a/b/" ~-/team-kits/kernel/state.py` rewrites the file in
    it. That file has been destroyed that way repeatedly and the damage put down to a script
    standing in the wrong directory; the directory was never the whole answer
    (`docs/POST_V2_WISHLIST.md` H37 carries the damages).
    `test_the_arbiter_cannot_be_pointed_out_of_its_sandbox_by_the_state_a_tilde_reads` measures it.
    """
    subject = os.path.join(sandbox, *RELATIVE_TARGET.split("/"))
    with open(subject, "w", encoding="utf-8") as handle:
        handle.write("a")
    here = str(sandbox).replace("\\", "/")
    subprocess.run([shell, "-c", line], cwd=sandbox, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=120,
                   env=dict(_sandbox_module().sandbox_environment(sandbox),
                            R_OUT=outside, R_HERE=here))
    with open(subject, encoding="utf-8") as handle:
        return handle.read().strip() != "a"


def _claimed(label):
    """What `LINE_SHAPES` says the shell does with this shape, or None where it claims nothing."""
    return LINE_SHAPES[label][1]


def _can_arbitrate(shell, sandbox, outside):
    """Does this shell see the two trees the table is about, as THIS host spells them?

    TWO MEASUREMENTS, and the second is the one that matters on Windows: the WSL launcher passes
    the first (it reaches the sandbox through the cwd it inherits and has `sed`) and fails the
    second, because `C:/...` names nothing in it -- so every move in the table would look like a
    move that failed, and the table would be measured against a different filesystem.
    """
    if not _changes_the_protected_file(shell, sandbox, RELATIVE_WRITE):
        return False
    return subprocess.run([shell, "-c", 'cd "%s"' % outside], cwd=sandbox,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          timeout=120).returncode == 0


def _sandbox(base, index):
    """One tree the table can be measured in -- `index` of them, so the shapes can run in parallel.

    Every shape needs the protected path to hold a known content while its own line runs, so two
    lines sharing a tree would read each other's answer.
    """
    sandbox = os.path.join(base, "sandbox-%d" % index)
    os.makedirs(os.path.join(sandbox, "team-kits", "kernel"), exist_ok=True)
    # one shape writes a second, unprotected file first -- it has to exist for the line to run
    os.makedirs(os.path.join(sandbox, "docs"), exist_ok=True)
    with open(os.path.join(sandbox, "docs", "note.md"), "w", encoding="utf-8") as handle:
        handle.write("x")
    return sandbox


# How many of the table's shapes are measured at once. Every one of them is a real process, and
# each has its own tree (`_sandbox`) or, for the gate, no tree at all -- so the parallelism changes
# what it costs and not what it measures.
AT_ONCE = 10


def _in_parallel(work, subjects):
    """`{subject: work(slot, subject)}`, with `AT_ONCE` of them running.

    A SLOT IS HELD, NOT COMPUTED FROM THE POSITION IN THE LIST: with `index % AT_ONCE` the seventh
    subject took the tree the first one was still measuring in, and six shapes of the table came
    back with each other's answers -- caught by the shell arbitration itself, which is what it is
    for. A slot is taken from the queue and given back, so two running subjects never share one.
    """
    slots = queue.Queue()
    for index in range(AT_ONCE):
        slots.put(index)

    def held(subject):
        slot = slots.get()
        try:
            return work(slot, subject)
        finally:
            slots.put(slot)

    out = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=AT_ONCE) as pool:
        futures = {pool.submit(held, subject): subject for subject in subjects}
        for future in concurrent.futures.as_completed(futures):
            out[futures[future]] = future.result()
    return out


def test_the_shell_writes_where_the_table_of_line_shapes_says(tmp_path):
    """The first column of `LINE_SHAPES`, taken from a real shell instead of from anybody's memory.

    THE RETURN CODE OF A GATE IS NO EVIDENCE OF WHERE A SHELL STANDS, so the subject here is the
    FILE: each line runs in a sandbox where the protected path holds `a`, and what counts is
    whether it holds `b` afterwards. Without this the other test would be a reader measured against
    a table written by the same hand that wrote the reader -- and since the column is DERIVED from
    the conditions the reader claims (`_crossed`), this is also what keeps the derivation honest.

    WHERE THE TABLE CLAIMS NOTHING, THE MEASUREMENT IS MADE WHERE IT CAN DECIDE SOMETHING, and that
    is this round's correction. What a word standing in FRONT of a command name does with the rest
    of the line is nothing this reader says anything about (`env cd` never reaches the builtin,
    `command cd` does, `! cd` inside a pipeline is a syntax error and runs nothing at all), so the
    table asserts no value there and the INVARIANT is asserted instead: wherever the shell writes
    the protected file, the gate has to refuse. That invariant can only fire where the table lets
    the gate ALLOW -- and for the unclaimed cells whose gate column is a refusal it was a branch
    that was constantly false, and one real shell process per such cell per run for a question
    already answered. Those are left unmeasured here and bound by the other test, which drives every
    one of them through a real gate process against exactly that constant; the moment such a cell
    turns into an allow it lands in `binding` below and is measured again, without anything being
    edited. How many that is stands nowhere: it is `len(LINE_SHAPES) - len(claiming) - len(binding)`
    and a number written beside it is the one that goes stale, which it did.

    THE SHELL IS CHOSEN BY MEASUREMENT (`_can_arbitrate`), not by its name or its place on PATH. A
    host where no candidate qualifies cannot answer this question at all, and a test that cannot
    measure its property reports that as a FAILURE: a silent skip is how a table stopped being
    checked for three rounds while it looked green.
    """
    outside = str(tmp_path / "elsewhere").replace("\\", "/")
    os.makedirs(outside)
    trees = [_sandbox(str(tmp_path), index) for index in range(AT_ONCE)]
    shell = next((candidate for candidate in _posix_shells()
                  if _can_arbitrate(candidate, trees[0], outside)), None)
    assert shell is not None, (
        "no shell on this host sees both trees this table is about, so the column of `LINE_SHAPES` "
        "was not measured against anything: %s" % (_posix_shells(),))
    claiming = sorted(label for label in LINE_SHAPES if _claimed(label) is not None)
    assert len(claiming) > len(LINE_SHAPES) // 2, (
        "the table stopped claiming what the shell does in most of its shapes (%d of %d), so this "
        "test measures almost nothing" % (len(claiming), len(LINE_SHAPES)))
    binding = sorted(label for label in LINE_SHAPES
                     if _claimed(label) is None and not LINE_SHAPES[label][2])

    def measure(index, label):
        return _changes_the_protected_file(shell, trees[index],
                                           _line(LINE_SHAPES[label][0], outside, trees[index]),
                                           outside)

    answers = _in_parallel(measure, claiming + binding)
    wrong = ["the table says %r %s the protected file, and %s disagrees: %s"
             % (label, "changes" if _claimed(label) else "does not change", shell,
                _line(LINE_SHAPES[label][0], outside, trees[0]))
             for label in claiming if answers[label] != _claimed(label)]
    wrong += ["%s writes the protected file in %r, and the table lets the gate allow it: %s"
              % (shell, label, _line(LINE_SHAPES[label][0], outside, trees[0]))
              for label in binding if answers[label]]
    assert not wrong, "\n".join(wrong)


def test_gate1_refuses_a_line_exactly_where_the_shell_would_write(project, tmp_path):
    """The gate answers every shape of `LINE_SHAPES` the way the second column derives.

    ONE PROPERTY, BOTH DIRECTIONS: where this reader keeps its position, the relative write behind
    it is refused; where it really follows the shell out, the same write is allowed. The second
    half is the expensive one -- a reader that stopped following directory verbs altogether would
    satisfy the first and refuse this repo's own commands.

    THE INVARIANT THAT BINDS THE TWO COLUMNS IS ASSERTED HERE, and it is the one that says "no
    hole": wherever the first column says the shell writes the protected file, the second has to
    say the gate refuses. A cell where the gate refuses and the shell writes OUTSIDE is friction,
    named as such in `docs/POST_V2_WISHLIST.md` (H29, H30) -- a cell the other way round would be a
    hole, and this makes it impossible to write one into the table by hand.

    The first column is measured against a real shell in
    `test_the_shell_writes_where_the_table_of_line_shapes_says`, so neither test can be satisfied
    by the reader it is about.
    """
    outside = str(tmp_path).replace("\\", "/")
    holes = [label for label in LINE_SHAPES if _claimed(label) and not LINE_SHAPES[label][2]]
    assert not holes, (
        "the table itself says the shell writes the protected file here while the gate allows it, "
        "which is a hole written down rather than measured: %s" % sorted(holes))

    def measure(_index, label):
        return run(project, "gate_lead_write_scope.py",
                   bash_payload(project, _line(LINE_SHAPES[label][0], outside, project)))

    answers = _in_parallel(measure, sorted(LINE_SHAPES))
    wrong = []
    for label in sorted(LINE_SHAPES):
        line, refuses = _line(LINE_SHAPES[label][0], outside, project), LINE_SHAPES[label][2]
        rc, err = answers[label]
        if refuses and rc != 2:
            wrong.append("%s: this reader keeps its position here, the gate answered rc %d: %s"
                         % (label, rc, line))
        if not refuses and rc != 0:
            wrong.append("%s: this reader follows the move here, the gate refused: %s\n%s"
                         % (label, line, err[:200]))
    assert not wrong, "\n".join(wrong)


# WHAT A SHELL CAN HAVE BEHIND IT when it reads a tilde word, and the axis the six prefixes it
# resolves out of its own state differ in: nothing, a directory it came from, a stack. The last two
# leave the line OUTSIDE the tree, so every relative word there is one the gate allows and only the
# prefix can bring the write back in -- which is what makes those cells measure the prefix and not
# the position.
TILDE_STATES = {
    "with nothing behind it": "",
    "after a move out of the tree": 'cd %(out)s ; ',
    "after a push out of the tree": 'pushd %(out)s > /dev/null ; ',
}


def _tilde_prefixes(harness):
    """Every prefix a tilde word could carry -- generated out of the ALPHABET, not out of a manual.

    A LIST OF THE FORMS A SHELL DOCUMENTS WOULD BE A CLAIM THAT IT HAS NO MORE. What a prefix is,
    is a span (`_harness._tilde_prefix`), so its values come from the characters that may stand in
    one: everything printable except what would stop the word being one word -- whitespace, the
    separators that END the prefix, the shell's own syntax, its quotes, its comment character and
    the openers of the substitutions this reader knows. Each character is also crossed with a digit
    behind it, because the numeric forms carry a sign AND a number and one character cannot show
    that.

    WHAT EACH OF THEM REALLY NAMES IS ASKED OF THE ARBITRATING SHELL and never of the library
    expansion under test, which is the whole point of DEC-0020: the delegate answers for all of
    them, and the two answers agree for one.
    """
    alphabet = _word_alphabet(harness)
    return [""] + alphabet + [letter + "0" for letter in alphabet]


def _word_alphabet(harness):
    """Every character that can stand inside ONE word without ending it or the prefix in it.

    Everything printable except what would stop the word being one word -- whitespace, the
    separators that END a tilde prefix, the shell's own syntax, its quotes, its comment character
    and the openers of the substitutions this reader knows.
    """
    reader = shlex.shlex("", punctuation_chars=True)
    apart = (set(string.whitespace) | set(reader.quotes) | set(reader.commenters)
             | set(harness._PATH_SEPARATORS) | harness._SYNTAX_CHARACTERS
             | {character for pair in harness._SUBSTITUTIONS for part in pair
                for character in part})
    alphabet = sorted(set(string.printable) - apart)
    assert len(alphabet) > 1, "no character is left for a tilde prefix to be made of"
    return alphabet


def _tilde_subjects():
    """`{(state, prefix, quoting): the word the line writes into}` -- three axes, fully crossed.

    THE THIRD AXIS IS THIS ROUND'S CORRECTION AND IT WAS A HOLE, not a gap: the check set had no
    value in which the target word carried quoting at all, and the fix of the round before had been
    built on "does this word carry a spliced span" -- a property of the WHOLE word. Where the
    quoting stands is what a shell reads, so where it stands is an axis (`_quotings`).

    A CHECK SET THAT CAN BE CUT SILENTLY IS THE OTHER HALF. Its size and the values of the axis are
    stated by the hole entry that stands on them and compared with the set itself
    (`test_every_tilde_subject_a_closed_hole_names_is_one_the_check_set_carries`), so a shrunk
    alphabet, a dropped state or a dropped quoting is red rather than green-and-smaller.
    """
    harness = _reader()
    out = {}
    for state in sorted(TILDE_STATES):
        for prefix in _tilde_prefixes(harness):
            word = "%s%s/%s" % (harness._TILDE, prefix, RELATIVE_TARGET)
            for label, quoted in sorted(_quotings(harness, word).items()):
                out[(state, prefix, label)] = quoted
    return out


TILDE_SUBJECTS = _tilde_subjects()
# The values of the quoting axis, over every prefix that generates them -- the set the entry that
# leans on this check set has to name, in both directions.
TILDE_QUOTINGS = sorted({label for _state, _prefix, label in TILDE_SUBJECTS})


def test_gate1_places_a_tilde_word_where_the_shell_puts_it(project, tmp_path):
    """Where this reader DELEGATES the expansion of a tilde, the delegate is measured against bash.

    THE BRANCH WAS RIGHT AND THE VALUE IT WAS FED WAS NOT (DEC-0020). Whether a reading may be
    expanded at all is decided and crossed elsewhere (`MOVES`, H31); WHAT the expansion is came out
    of `os.path.expanduser`, which answers "the home directory of a user". A shell answers "the
    directory this prefix names", and for a prefix that is not empty that is its own working
    directory, the one it came from or an entry of its stack. The delegate does not decline there --
    it hands back a path under the home directory, which nothing protects. Measured 2026-08-07
    through the real gate, one tool call and no preparation: `sed -i "s/a/b/" ~0/<kit file>` was
    rc 0 while bash rewrote the file, and the same shape reached `.claude/settings.json`,
    `.claude/hooks/_harness.py` and canonical state (`docs/POST_V2_WISHLIST.md` H33).

    THE SUBJECT IS `TILDE_SUBJECTS`: every prefix the alphabet can make, from every state a shell
    can carry, and with the quoting standing in every run of the word it can stand in. Both columns
    are measured rather than claimed: a real shell says which of them reach the protected file from
    where the line stands, and a real gate process says what it answers. The invariant is the one
    the cross table asserts as well -- wherever the shell writes, the gate refuses.

    THE QUOTING AXIS IS THIS ROUND'S CORRECTION AND IT WAS A HOLE. `~+/"team-kits"/kernel/state.py`
    was rc 0 through the real gate on 2026-08-07 while bash rewrote the protected file: the fix of
    the round before asked whether the word carried a spliced span ANYWHERE, and a shell suppresses
    an expansion only where the quoting stands.

    THE GATE IS ASKED WHERE SOMETHING IS ASSERTED, AND NOWHERE ELSE, which is what makes an axis of
    9840 values affordable: the shell column decides where the invariant binds (a subject the shell
    does not write is a subject this test asserted nothing about even when the gate was asked), and
    the both-ends set is generated. Before this the gate ran once per subject and the answer was
    dropped for all but a handful.

    BOTH ENDS, AND THE THIRD ONE IS NEW. Some prefix other than the empty one has to reach the tree,
    or the arbiter measured nothing at all; some word that CARRIES QUOTING has to reach it, or the
    new axis measured nothing; and the empty prefix -- the one reading the delegate and the shell
    agree on -- has to stay ALLOWED wherever the shell does not take it into the tree, in every
    quoting and every state, or this is a gate that refuses every tilde and the friction it costs is
    unbounded.
    """
    harness = _reader()
    outside = str(tmp_path / "elsewhere")
    os.makedirs(outside)
    outside = outside.replace("\\", "/")
    trees = [_sandbox(str(tmp_path), index) for index in range(AT_ONCE)]
    shell = next((candidate for candidate in _posix_shells()
                  if _can_arbitrate(candidate, trees[0], outside)), None)
    assert shell is not None, (
        "no shell on this host sees the trees this test is about, so what a tilde prefix names was "
        "measured against nothing: %s" % (_posix_shells(),))

    def line(subject):
        return ((TILDE_STATES[subject[0]] % {"out": '"%s"' % outside})
                + 'sed -i "s/a/b/" %s' % TILDE_SUBJECTS[subject])

    subjects = sorted(TILDE_SUBJECTS)

    def writes(index, subject):
        return _changes_the_protected_file(shell, trees[index], line(subject), outside)

    def judged(_index, subject):
        return run(project, "gate_lead_write_scope.py", bash_payload(project, line(subject)))

    reached = _in_parallel(writes, subjects)
    reaching = sorted(subject for subject in subjects if reached[subject])
    assert [subject for subject in reaching if subject[1]], (
        "no tilde prefix on this host reaches the protected tree from any of %d states, so the "
        "column this test asserts against was empty: %s"
        % (len(TILDE_STATES), sorted(TILDE_STATES)))
    assert [subject for subject in reaching if subject[2] != UNQUOTED], (
        "no word carrying quoting reaches the protected tree from any state, so the axis that "
        "crosses WHERE the quoting stands measured nothing: %s" % TILDE_QUOTINGS)
    free = [subject for subject in subjects if not subject[1] and not reached[subject]]
    answers = _in_parallel(judged, sorted(set(reaching) | set(free)))
    holes = []
    for subject in reaching:
        rc, err = answers[subject]
        if rc != 2:
            holes.append("`%s%s` %s, %s: the shell writes the protected file, the gate answered "
                         "rc %d: %s"
                         % (harness._TILDE, subject[1], subject[0], subject[2], rc, line(subject)))
        elif ("%s%s" % (harness._TILDE, subject[1])) not in err:
            holes.append("`%s%s` %s, %s: refused, but the reason never names the word: %s"
                         % (harness._TILDE, subject[1], subject[0], subject[2], err[:200]))
    assert not holes, "\n".join(holes)
    friction = ["%s, %s: %s\n%s" % (subject[0], subject[2], line(subject),
                                    answers[subject][1][:200])
                for subject in free if answers[subject][0] != 0]
    assert not friction, (
        "the one prefix whose expansion this reader and the shell agree on was refused where the "
        "shell leaves it outside the tree, so the delegate is not measured against the shell here "
        "but switched off:\n%s" % "\n".join(friction))


def _tilde_leads(harness):
    """`{lead: does the shell's quote removal take it away}` -- what can stand BEFORE the tilde.

    TWO CLASSES AND THEY ARE GENERATED, because the difference between them is the whole answer: a
    shell decides whether to expand on the word BEFORE quoting is removed, so a lead it removes
    leaves a word that STARTS with the tilde and is still not expanded, while a lead it keeps
    leaves a word in which the tilde is not the first character at all. The removable ones are the
    empty span each quote character of the reader can make; the kept ones are the same alphabet a
    prefix is made of (`_word_alphabet`), so a character this repo's reader stops treating as
    syntax is crossed here on the day it changes.

    THE ESCAPE IS NOT ONE OF THEM, and that is not an omission: `_PATH_SEPARATORS` carries the
    backslash, which is why it cannot open a lead this reader would read as quoting -- the same
    reason `_harness._quoting_in` gives for not asking about it.
    """
    out = {quote + quote: True for quote in sorted(shlex.shlex("", punctuation_chars=True).quotes)}
    out.update({character: False for character in _word_alphabet(harness)})
    assert any(out.values()) and not all(out.values()), (
        "one of the two classes of lead is empty, so this check set measures no difference")
    return out


def _lead_subjects(harness):
    """`{(lead, prefix): the word}` for a tilde that does not start its word.

    THE PREFIX AXIS IS ITS TWO ENDS AND NOT ALL 157: what a lead changes is whether the word is a
    tilde word at all, and the prefix only decides what the answer then IS -- empty, and this
    reader expands into the home directory, which nothing protects; not empty, and it cannot place
    the word at all. Crossing every prefix would multiply a real shell and a real gate process by
    157 for an axis whose two values are already both here.
    """
    ends = ["", next(prefix for prefix in _tilde_prefixes(harness) if prefix)]
    return {(lead, prefix): "%s%s%s/%s" % (lead, harness._TILDE, prefix, RELATIVE_TARGET)
            for lead in sorted(_tilde_leads(harness)) for prefix in ends}


def test_gate1_answers_for_a_tilde_that_does_not_start_its_word(project, tmp_path):
    """The cell three places of the hole list described from a measurement taken under the home
    directory, where an ancestor answered instead of the property.

    `x=~+/team-kits/kernel/state.py` was written down as measured over-refusal. It is not:
    measured 2026-08-08 against a stand-in project OUTSIDE the home directory it is rc 0, and the
    rc 2 of the round before came from the project living under the directory a bare `~` names --
    the word's only path-like substring that this reader can place is that bare `~`, and a
    directory that CONTAINS protected state is refused for the containment (H19). The other half of
    the sentence was wrong too: bash expands `x=~+/y` (`x=/c/.../y`), it does not keep it literal.

    SO THE CLAIM IS A SUBJECT NOW INSTEAD OF A SENTENCE, and the rule it is measured against is one
    expression rather than a list of spellings: after the shell has removed quoting, the word either
    starts with a tilde carrying a non-empty prefix -- and then this reader cannot place it and
    refuses everyone -- or it does not, and then there is nothing here to refuse. Both classes of
    lead are generated (`_tilde_leads`).

    BOTH ENDS. The control is the same line with NO lead: the shell has to write the protected file
    through it and the gate has to refuse it, or the leads below are compared against nothing. And
    the shell column is measured for every lead rather than assumed -- a lead through which bash
    reaches the protected file while the gate allows is a hole and says so.
    """
    harness = _reader()
    outside = str(tmp_path / "elsewhere")
    os.makedirs(outside)
    outside = outside.replace("\\", "/")
    trees = [_sandbox(str(tmp_path), index) for index in range(AT_ONCE)]
    shell = next((candidate for candidate in _posix_shells()
                  if _can_arbitrate(candidate, trees[0], outside)), None)
    assert shell is not None, (
        "no shell on this host sees the trees this test is about: %s" % (_posix_shells(),))
    control = 'sed -i "s/a/b/" %s%s/%s' % (harness._TILDE, "+", RELATIVE_TARGET)
    assert _changes_the_protected_file(shell, trees[0], control), (
        "the same line without a lead does not reach the protected file on this host, so what a "
        "lead in front of it changes was measured against nothing: %s" % control)
    assert run(project, "gate_lead_write_scope.py", bash_payload(project, control))[0] == 2, (
        "the same line without a lead is not refused, so this test measures the lead against an "
        "answer that is already an allow")

    removable = _tilde_leads(harness)
    subjects = _lead_subjects(harness)
    order = sorted(subjects)

    def writes(index, subject):
        return _changes_the_protected_file(
            shell, trees[index], 'sed -i "s/a/b/" %s' % subjects[subject], outside)

    def judged(_index, subject):
        return run(project, "gate_lead_write_scope.py",
                   bash_payload(project, 'sed -i "s/a/b/" %s' % subjects[subject]))

    reached = _in_parallel(writes, order)
    answers = _in_parallel(judged, order)
    wrong = []
    for subject in order:
        lead, prefix = subject
        # what a shell hands the program: a removable lead is gone, a kept one is still in front
        word = subjects[subject][len(lead):] if removable[lead] else subjects[subject]
        head = word[len(harness._TILDE):].split("/")[0] if word.startswith(harness._TILDE) else ""
        rc = answers[subject][0]
        if reached[subject] and rc != 2:
            wrong.append("lead %r, prefix %r: bash writes the protected file through it and the "
                         "gate answered rc %d" % (lead, prefix, rc))
        elif (rc == 2) != bool(head):
            wrong.append("lead %r, prefix %r: the shell reads the word as %r, so this gate can "
                         "place it %s -- and it answered rc %d"
                         % (lead, prefix, word, "not at all" if head else "as any other word", rc))
    assert not wrong, "\n".join(wrong)


def test_the_arbiter_cannot_be_pointed_out_of_its_sandbox_by_the_state_a_tilde_reads(tmp_path):
    """What keeps this suite off the tree it measures is not `cwd` alone, and that cost real files.

    THE SUBJECT IS THE LAUNCHER, not a gate: `_changes_the_protected_file` runs every line of every
    check set here, and the safety of all of them is one keyword argument -- except that a tilde
    prefix does not read `cwd`. It reads the shell's own state, and `PWD` and `OLDPWD` come in
    through the ENVIRONMENT. A suite started in this repo hands the repo to `OLDPWD`, `~-` is a
    subject of `TILDE_SUBJECTS`, and the line writes the repo with a perfectly correct `cwd`.
    Measured 2026-08-07, three times: `team-kits/kernel/state.py` came out with the first `a` of
    each of its 928 lines replaced by `b`. Twice it was put down to a measuring script standing in
    the wrong directory; the third time the session guard above caught it mid-run and the mechanism
    was isolated -- with `cwd` a sandbox and `OLDPWD` another tree, `printf "%s\\n" ~-` prints the
    other tree.

    SO THE MEASUREMENT IS MADE WITH THAT STATE POINTED SOMEWHERE ELSE ON PURPOSE: every prefix the
    alphabet can make is run at a tree the sandbox has nothing to do with, and that tree has to be
    untouched afterwards. BOTH ENDS: some prefix has to reach the sandbox's OWN protected file, or
    the launcher ran nothing and the first half is empty.
    """
    harness = _reader()
    outside = str(tmp_path / "elsewhere")
    os.makedirs(outside)
    trees = [_sandbox(str(tmp_path), index) for index in range(AT_ONCE)]
    shell = next((candidate for candidate in _posix_shells()
                  if _can_arbitrate(candidate, trees[0], outside.replace("\\", "/"))), None)
    assert shell is not None, (
        "no shell on this host can arbitrate, so the launcher was measured against nothing: %s"
        % (_posix_shells(),))
    other = str(tmp_path / "a-tree-this-suite-must-not-reach")
    subject = os.path.join(other, *RELATIVE_TARGET.split("/"))
    os.makedirs(os.path.dirname(subject))
    with open(subject, "w", encoding="utf-8") as handle:
        handle.write("a")
    saved = {name: os.environ.get(name) for name in ("PWD", "OLDPWD")}
    os.environ["PWD"] = os.environ["OLDPWD"] = other.replace("\\", "/")
    try:
        def measure(index, prefix):
            return _changes_the_protected_file(
                shell, trees[index],
                'sed -i "s/a/b/" %s%s/%s' % (harness._TILDE, prefix, RELATIVE_TARGET))

        reached = _in_parallel(measure, _tilde_prefixes(harness))
    finally:
        for name, value in saved.items():
            os.environ.pop(name, None) if value is None else os.environ.__setitem__(name, value)
    with open(subject, encoding="utf-8") as handle:
        held = handle.read()
    assert held == "a", (
        "a line of this check set reached %s, which is not the sandbox it was given: the shell "
        "resolves a tilde prefix out of state the launcher hands it, and `cwd` does not cover that"
        % other)
    assert any(reached.values()), (
        "no tilde prefix reached the sandbox's own protected file, so the launcher was not running "
        "these lines at all and the assertion above holds for the wrong reason")


def test_gate1_does_not_see_a_program_a_here_document_hands_a_shell(project, tmp_path):
    """WHERE the reading of a command line ends, measured -- the same kind of boundary as H22.

    Both gates read the line only after the KITS' prose removal has run over it
    (`_harness._prose_removed`), and that removal deletes every here-document BODY: a body is where
    a commit message is written, and reading inside one would be a second answer to "what is prose"
    (H15). The consequence is not about messages at all -- a here-document is also how a shell is
    handed a PROGRAM, and that program is then invisible to both gates.

    MEASURED IN BOTH DIRECTIONS IN ONE RUN, one tool call, no preparation and no commit: the same
    payload written as an argument is refused, and written into a here-document it is allowed while
    a real bash really rewrites the protected file. `docs/POST_V2_WISHLIST.md` H38 carries the
    chain and the judgement.

    THIS TEST GOES RED WHEN THE HOLE CLOSES, which is what it is for: the repair site is in the kit
    (`gate_write_scope._HEREDOC_RX`), outside the scope of the item that measured it, so the entry
    stands open -- and the day the kit reads inside a body, H38 and this test have to be corrected
    together rather than one of them left claiming an edge that is no longer there.
    """
    sandbox = _sandbox(str(tmp_path), 0)
    shell = next((candidate for candidate in _posix_shells()
                  if _changes_the_protected_file(candidate, sandbox, RELATIVE_WRITE)), None)
    assert shell is not None, (
        "no shell on this host reaches the protected file with %r, so what the here-document does "
        "was measured against nothing" % RELATIVE_WRITE)
    seen = "bash -c '%s'" % RELATIVE_WRITE
    assert run(project, "gate_lead_write_scope.py", bash_payload(project, seen))[0] == 2, (
        "the same program passed as an ARGUMENT is allowed too, so this test is not measuring what "
        "the here-document costs but a gate that sees nothing at all")
    unseen = "bash <<EOF\n%s\nEOF" % RELATIVE_WRITE
    assert run(project, "gate_lead_write_scope.py", bash_payload(project, unseen))[0] == 0, (
        "this line is refused now, so the boundary moved: H38 describes an edge that is no longer "
        "there and has to be corrected rather than left standing")
    assert _changes_the_protected_file(shell, sandbox, unseen), (
        "the line this gate allows does not move the tree here, so what it allows was not measured")


def test_every_span_the_kits_prose_removal_takes_out_is_named_where_it_is_documented():
    """The blind spot of `command_line` is stated where it is read, and the statement is generated.

    A DOCSTRING THAT NAMES ONE OF TWO IS THE CLAIM THIS EXISTS FOR. `command_line` named
    `_MESSAGE_ARG_RX` as what its reading does not reach and said nothing about the here-document
    body, and that second span carries a chain that runs in one tool call (H38) -- so the paragraph
    that was supposed to be the warning was itself the reassurance.

    SO THE NAMES COME OUT OF THE SYNTAX TREE OF THE FUNCTION THAT RUNS. Both directions: a span the
    removal applies and the docstring does not name is a blind spot nobody was told about, and a
    span the docstring names and the removal no longer applies is a warning about something that is
    not there any more.
    """
    harness = _reader()
    applied = {node.attr
               for node in ast.walk(ast.parse(textwrap.dedent(
                   inspect.getsource(harness._prose_removed))))
               if isinstance(node, ast.Attribute) and node.attr.endswith("_RX")}
    assert applied, (
        "`_prose_removed` applies no named expression at all any more, so this test would pass "
        "whatever the docstring says")
    named = {span.rsplit(".", 1)[-1]
             for span in re.findall(r"`([^`]+)`", harness.command_line.__doc__ or "")
             if span.rsplit(".", 1)[-1].endswith("_RX")}
    assert named == applied, (
        "`command_line` names %s as what its reading does not reach; the prose removal it goes "
        "through takes out %s" % (sorted(named), sorted(applied)))


# -- the apparatus a round measures WITH, which is a subject and not a promise ------------------


def _decoy(base, name):
    """A tree the measurement must not reach, holding the file every payload here names."""
    subject = os.path.join(base, name, *RELATIVE_TARGET.split("/"))
    os.makedirs(os.path.dirname(subject), exist_ok=True)
    with open(subject, "w", encoding="utf-8") as handle:
        handle.write("a")
    return os.path.join(base, name), subject


def _directory_words(harness, asked_for):
    """Every line that writes `RELATIVE_TARGET` under a directory the LINE ITSELF never names.

    THE SHAPES ARE THE WAYS A SHELL CAN GET A DIRECTORY WITHOUT BEING TOLD ONE, and there are two:
    a tilde prefix, which it resolves out of its own state -- every prefix the alphabet can make,
    GENERATED (`_tilde_prefixes`) rather than listed -- and a bare relative word, which it looks up
    along a search list once it cannot find it below `cwd`. `asked_for` is what a line of the second
    shape asks for. The `cd` stands in a subshell so no line depends on the order of the ones before
    it, which is what lets the whole set run as one script instead of one process per line.
    """
    for prefix in _tilde_prefixes(harness):
        yield 'sed -i "s/a/b/" %s%s/%s' % (harness._TILDE, prefix, RELATIVE_TARGET)
    yield "( cd %s && %s )" % (asked_for, RELATIVE_WRITE)


def _pointed_at(name, tree):
    """The value that makes the environment name `name` reach `tree` for a child shell.

    A NAME THAT ENDS IN `PATH` HOLDS A SEARCH LIST AND NOT A DIRECTORY: what a shell joins its word
    onto is an ENTRY, so the value that reaches `tree` is its parent -- and it is spelled the way a
    list is read on this host, which is the spelling a colon does not split (`C:/x` is read as `C`
    and then `/x`, measured 2026-08-08, and a `cd` through it finds nothing).
    """
    return os.path.dirname(tree) if name.endswith("PATH") else _sandbox_module().posix(tree)


# WHAT A SHELL ON THIS HOST WAS MEASURED TO READ A DIRECTORY BACK OUT OF -- a fact about shells,
# and it is stated HERE rather than taken from `_sandbox` on purpose. A measurement whose hostile
# environment comes out of the module under test cannot fail when that module DROPS a name: it then
# stops pointing that name at the decoy as well, and the attack disappears together with the
# defence. Measured 2026-08-08 in a clone: with the hostile set derived from
# `POINTED_AT_THE_SANDBOX`, deleting `HOME`, `OLDPWD` or `CDPATH` from that tuple left this test
# GREEN. The test below ties this tuple to the running shell in both directions, so it cannot rot
# into a second opinion.
CARRY_A_TREE = ("OLDPWD", "HOME", "CDPATH")


def test_the_measurement_sandbox_leaves_a_child_shell_no_directory_word_that_names_another_tree(
        tmp_path):
    """`_sandbox.pin` is what stands between a payload and this repo, so it is measured, not trusted.

    THE SCRIPTS BESIDE THIS FILE ARE NOT UNDER THE SESSION GUARD. `the_repo_is_not_a_sandbox`
    watches runs of this file; the ad-hoc apparatus a round writes -- a probe, a single try out of
    a shell -- is a Python process of its own, and the hole list says so (H37). What takes the
    place of that guard is that module, and every version of it so far was wrong about WHICH names
    carry a directory: the first pinned `cwd` alone and left `OLDPWD` on the real repo, the second
    added `PWD` and `DIRSTACK` and left `HOME` and `CDPATH` (measured 2026-08-08 against a decoy
    tree: `~/...` wrote the decoy, and so did `cd <decoy> && sed -i ...` through `CDPATH`).

    SO WHAT IS ASKED HERE IS A PROPERTY AND NOT THREE NAMES: does ANY line that names a directory
    without spelling one reach a tree the sandbox has nothing to do with? Every tilde prefix the
    alphabet can make, and the relative word a search list answers.

    THE CONTROL COMES FIRST AND IT REALLY DAMAGES THE DECOY -- with the state INHERITED, which is
    what a process started in the measured tree hands on. Then `pin()`, and the decoy has to be
    untouched while the sandbox's OWN file is not.

    AND THE ENUMERATION IN THAT MODULE IS TRIPPED AT BOTH ENDS, because a list of names is a claim
    that the world has no more of them: each name is put back on its own and measured, so a name
    that carries a tree while the module calls it blind fails here, and so does a name the module
    handles that carries nothing -- which is how `DIRSTACK` and `PWD` came to be marked as carried
    without a chain instead of described as protection. The hostile state itself comes from
    `CARRY_A_TREE` and not from the module, for the reason written there.
    """
    harness = _reader()
    module = _sandbox_module()
    shell = next((candidate for candidate in _posix_shells()
                  if subprocess.run([candidate, "-c", "true"], cwd=str(tmp_path),
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL).returncode == 0), None)
    assert shell is not None, "no shell on this host could run these lines: %s" % (_posix_shells(),)
    controlled = set(module.POINTED_AT_THE_SANDBOX) | set(module.DROPPED)
    hostile = controlled | set(CARRY_A_TREE)
    # short subject names on purpose: each of them becomes a directory below `tmp_path`, and this
    # host stops a path at 260 characters
    INHERITED, PINNED = "inherited", "pinned"
    subjects = [INHERITED, PINNED] + sorted(hostile)
    trees = {}
    for subject in subjects:
        work = str(tmp_path / ("box-%s" % subject) / "run")
        os.makedirs(work)
        trees[subject] = (work, ) + _decoy(str(tmp_path), "not-mine-%s" % subject)

    def measure(_slot, subject):
        work, decoy, victim = trees[subject]
        _decoy(work, "")
        script = "\n".join(_directory_words(harness, os.path.basename(decoy)))
        subprocess.run([shell, "-c", script], cwd=work, stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600,
                       env=environments[subject])
        with open(victim, encoding="utf-8") as handle:
            reached = handle.read() != "a"
        with open(os.path.join(work, *RELATIVE_TARGET.split("/")), encoding="utf-8") as handle:
            return reached, handle.read() != "a"

    def inherits(subject):
        _work, decoy, _victim = trees[subject]
        return dict(os.environ, **{name: _pointed_at(name, decoy) for name in hostile})

    here, saved = os.getcwd(), dict(os.environ)
    try:
        os.environ.update(inherits(PINNED))
        work = module.pin(os.path.dirname(trees[PINNED][0]), "run")
        environments = {PINNED: dict(os.environ)}
    finally:
        os.chdir(here)
        os.environ.clear()
        os.environ.update(saved)
    assert os.path.realpath(work) == os.path.realpath(trees[PINNED][0]), (
        "`pin()` stood in %s and not in the tree measured here" % work)
    environments[INHERITED] = inherits(INHERITED)
    for name in hostile:
        environments[name] = dict(module.sandbox_environment(trees[name][0]),
                                  **{name: _pointed_at(name, trees[name][1])})
    answers = _in_parallel(measure, subjects)

    assert answers[INHERITED][0], (
        "with the directory state inherited no line reached %s, so this host cannot show the "
        "accident this module exists for and everything below says nothing" % trees[INHERITED][1])
    assert not answers[PINNED][0], (
        "a line run after `pin()` reached %s, which is not the sandbox it was pinned to"
        % trees[PINNED][1])
    assert answers[PINNED][1], (
        "no line reached the sandbox's OWN file either, so nothing ran and the decoy is untouched "
        "for the wrong reason")
    carries = {name for name in hostile if answers[name][0]}
    assert carries == set(CARRY_A_TREE), (
        "the names this host was measured to resolve a directory out of are %s; put back one at a "
        "time, the ones that really reached their decoy are %s. Either a shell here changed or the "
        "hostile state above stopped being hostile -- and the halves before this one are only worth "
        "what it is" % (sorted(CARRY_A_TREE), sorted(carries)))
    assert carries <= controlled, (
        "%s carry a tree on this host and `_sandbox` does not touch them, so `pin()` hands a child "
        "shell a word that names another tree" % sorted(carries - controlled))
    assert controlled - carries == set(module.NOT_MEASURED_TO_CARRY_A_TREE), (
        "`_sandbox` says %s carry no tree; measured on this host the ones that carry none are %s. "
        "A name on the left that is missing on the right is a chain nobody was told about; one on "
        "the right that is missing on the left is handled for nothing and says so"
        % (sorted(module.NOT_MEASURED_TO_CARRY_A_TREE), sorted(controlled - carries)))


def test_the_measurement_watch_list_is_the_area_the_gate_protects(project):
    """What a measurement watches is derived from the gate's authority, not from its own lines.

    THE VERSION THIS REPLACED SCANNED THE PAYLOAD LINES for path-like spans, and a scan answers
    only for the spellings it can read: measured 2026-08-08 on the previous round's own lines, it
    found one of the four protected files those lines named -- the quoting inside a word broke the
    span and a join threw the repo root away -- so `.claude/settings.json`, `_harness.py` and a
    canonical state file were never hashed at all while the run reported everything unchanged.

    SO THE LIST IS THE PROTECTED SET, and the comparison here is a set EQUALITY against an
    independent derivation: every file of the project, walked without asking where the areas are,
    judged by `ProtectedArea.verdict`. Both directions fall out of it -- a file the areas do not
    reach is missing from the list, and a file the verdict allows (`staging/**`) is one the list may
    not carry.
    """
    module = _sandbox_module()
    harness = _reader()
    area = harness.ProtectedArea(project)
    walked = set()
    for here, dirs, names in os.walk(project):
        dirs[:] = [name for name in dirs if name != ".git"]
        walked.update(os.path.abspath(os.path.join(here, name)) for name in names)
    expected = {path for path in walked if area.verdict(path)[0] is not None}
    listed = set(module.protected_files(project))
    assert listed == expected, (
        "watched but not protected: %s -- protected but not watched: %s"
        % (sorted(listed - expected)[:5], sorted(expected - listed)[:5]))
    assert expected, "this project protects no file at all, so the comparison above is empty"
    allowed = walked - expected
    assert allowed, (
        "every file of the stand-in project is protected, so a list that simply returned all of "
        "them would pass this test")


def test_an_index_restore_refuses_a_target_outside_the_pinned_sandbox(tmp_path):
    """The one write-back path an apparatus for measuring writes had, and it checked the process.

    `restore_from_index` takes its destination as an ARGUMENT, so standing in the sandbox says
    nothing about where it writes -- the version it replaced checked only that the process was
    pinned, which makes a mistyped first argument a write into whatever it names, this repo's
    working tree included. That is the same class as the accident the whole module exists for.

    BOTH ENDS: a target under the pinned sandbox really receives the index bytes, and one outside it
    is refused without the file being touched.
    """
    module = _sandbox_module()
    sandbox = str(tmp_path / "sandbox")
    os.makedirs(sandbox)
    elsewhere, subject = _decoy(str(tmp_path), "not-the-sandbox")
    # a repository of its own rather than this one: what is measured is where the bytes GO
    source, _ = _decoy(str(tmp_path), "source")
    for arguments in (["init", "-q", "."], ["config", "user.email", "t@t.t"],
                      ["config", "user.name", "t"], ["add", "-A"]):
        subprocess.run(["git"] + arguments, cwd=source, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    here, saved = os.getcwd(), dict(os.environ)
    try:
        module.pin(sandbox)
        inside = module.restore_from_index(os.path.join(sandbox, "clone"), RELATIVE_TARGET,
                                           root=source)
        with open(inside, "rb") as handle:
            restored = handle.read()
        with pytest.raises(SystemExit) as refusal:
            module.restore_from_index(elsewhere, RELATIVE_TARGET, root=source)
    finally:
        # `pin()` writes the directory state into `os.environ`, which every later test inherits
        os.chdir(here)
        os.environ.clear()
        os.environ.update(saved)
    assert restored, "the index version of %s came back empty, so the half above wrote nothing" % (
        RELATIVE_TARGET,)
    assert "sandbox" in str(refusal.value), (
        "the refusal does not say what was wrong with the target: %s" % refusal.value)
    with open(subject, encoding="utf-8") as handle:
        assert handle.read() == "a", (
            "the refused restore wrote %s anyway, so the check is on the message and not on the "
            "write" % subject)


def test_the_words_this_reader_reads_are_the_kits_own_tokens():
    """`_harness.tokenise` adds a fact to the kits' tokens; it does not become a second tokeniser.

    A SECOND READER OF THE SAME TEXT IS THE DRIFT THIS REPO KEEPS PAYING FOR, and `tokenise` is one
    line away from being one: the kits' `_tokenise` is `_compat.shell_words` with that gate's lexer,
    and this spells the same composition in order to see the tokens BEFORE the quoting was taken out
    of them (`TYPED_READING`). So both are handed every line of both check sets and have to answer
    with the same words, the same splice flags and the same readings.

    THE OTHER END: a typed reading that never differs from the resolved text would make the whole
    round's distinction unmeasurable, so some word of these lines has to carry one that does. And
    the kits' tokeniser must no longer be reached directly from `_harness` -- read off that module's
    SYNTAX TREE, because a word arriving without a typed reading falls back to the pre-H31 answer
    for it, which is a hole rather than a defect anybody would see.
    """
    harness = _reader()
    harness._add_kit_paths(ROOT)
    module, compat = harness._from_kit("gate_write_scope"), harness._from_kit("_compat")
    lines = [_line(LINE_SHAPES[label][0], "/out", "/here") for label in sorted(LINE_SHAPES)]
    lines += ['sed -i "s/a/b/" %s' % word for word in sorted(set(TILDE_SUBJECTS.values()))]
    wrong, differing = [], 0
    for line in lines:
        mine, theirs = harness.tokenise(module, compat, line), module._tokenise(line)
        if [str(word) for word in mine] != [str(word) for word in theirs]:
            wrong.append("different words for %r" % line)
        elif ([(word.spliced, word.readings) for word in mine]
              != [(word.spliced, word.readings) for word in theirs]):
            wrong.append("same words, different facts for %r" % line)
        for word in mine:
            typed = getattr(word, harness.TYPED_READING, None)
            if typed is None:
                wrong.append("a word without a typed reading in %r: %r" % (line, str(word)))
            elif typed != str(word):
                differing += 1
    assert not wrong, "\n".join(sorted(set(wrong))[:20])
    assert differing, (
        "no word of either check set has a typed reading that differs from the text a program "
        "receives, so the distinction this round is built on was measured against nothing")
    with open(os.path.join(HOOKS, "_harness.py"), encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    direct = [node for node in ast.walk(tree)
              if isinstance(node, ast.Attribute) and node.attr == "_tokenise"]
    assert not direct, (
        "`_harness` still reaches the kits' tokeniser directly, so words can arrive at `readings` "
        "without a typed reading -- and those fall back to the answer H31 closed")


def _a_process_can_enter(path):
    """Can a process make this its working directory? Asked by having one TRY."""
    return subprocess.run(
        [sys.executable, "-B", "-c", "import os, sys; os.chdir(sys.argv[1])", path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def _a_process_can_list(path):
    """Can a process read this directory's entries? Asked by having one TRY."""
    return subprocess.run(
        [sys.executable, "-B", "-c", "import os, sys; os.listdir(sys.argv[1])", path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


# The two rights that come apart here. ENTERING and LISTING a directory are separate rights on
# both operating systems, and this test exists because a reader that asked for the wrong one
# answered wrong in BOTH directions -- so the pair is the subject, not a case. Each carries how the
# two systems spell it: the Windows right to deny, and the mode a POSIX directory keeps when that
# right is gone.
ENTRY, LISTING = "entry", "listing"
RIGHTS = {ENTRY: ("(X)", 0o400), LISTING: ("(RD)", 0o100)}


def _right(path, which, revoke):
    """Take `which` right on `path` away, or give it back. Reports nothing -- see the caller.

    Two spellings because the two operating systems have two, and NEITHER is believed: what the
    test acts on is `_a_process_can_enter` / `_a_process_can_list`, which try the thing rather than
    read a permission.

    EXACTLY THE ONE RIGHT IT IS ASKED FOR, and no more. Denying full control also denies the right
    to hand the rights back: measured 2026-08-05, a directory denied `(F)` could no longer be read,
    reset, or owned by the account that had just created it -- `icacls`, `takeown` and `Set-Acl`
    all answered "access denied". `/deny` takes the rights with the principal, `/remove:d` takes
    the principal alone; a restore spelled like the revocation removes nothing.
    """
    windows, mode = RIGHTS[which]
    user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    if os.name == "nt" and user:
        subprocess.run(["icacls", path] + (["/deny", "%s:%s" % (user, windows)] if revoke
                                           else ["/remove:d", user]),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        os.chmod(path, mode if revoke else 0o700)
    except OSError:
        pass


def test_gate1_follows_a_move_a_process_can_make_and_no_other(project, tmp_path):
    """ENTERING a directory is what a shell does to land in it, and it is a right of its own.

    BOTH DIRECTIONS OF ONE SPLIT, because every question that is not the entry itself gets one of
    them wrong. Measured 2026-08-05 on this host, one right revoked at a time:

      * traverse revoked (`icacls /deny <user>:(X)`) -- `os.scandir` succeeds, `os.path.isdir`,
        `os.stat`, `os.stat` of its `.` and `os.access(X_OK)` all say yes, while `os.chdir` and a
        real bash both answer `Permission denied`. The shell stays in the tree and the relative
        write behind it rewrites the protected file: the gate, asking whether the directory OPENS,
        followed the move and answered rc 0. A hole in one tool call;
      * list revoked (`(RD)`) -- `os.scandir` raises while `os.chdir` and bash go in. The gate
        stayed where it was and refused a write that lands outside the tree. Friction.

    So the pair is the subject here and neither half alone would do: a reader that refuses every
    move passes the first assertion, and one that follows every move passes the second.
    """
    cannot_enter = str(tmp_path / "no-entry")
    cannot_list = str(tmp_path / "no-listing")
    reachable = str(tmp_path / "reachable")
    for path in (cannot_enter, cannot_list, reachable):
        os.makedirs(path)
    _right(cannot_enter, ENTRY, revoke=True)
    _right(cannot_list, LISTING, revoke=True)
    try:
        assert not _a_process_can_enter(cannot_enter), (
            "this host would not take the entry right away from %s, so the half of this test that "
            "measures a hole measured nothing" % cannot_enter)
        assert _a_process_can_enter(cannot_list) and not _a_process_can_list(cannot_list), (
            "this host would not separate listing from entering on %s, so the half of this test "
            "that measures the friction measured nothing" % cannot_list)

        def line(directory):
            return 'cd "%s" ; %s' % (directory.replace("\\", "/"), RELATIVE_WRITE)

        rc, err = run(project, "gate_lead_write_scope.py",
                      bash_payload(project, line(cannot_enter)))
        assert rc == 2, "the gate followed a move into a directory no process can enter"
        rc, err = run(project, "gate_lead_write_scope.py",
                      bash_payload(project, line(cannot_list)))
        assert rc == 0, (
            "the gate did not follow a move a process makes, because the directory cannot be "
            "listed: %s" % err[:300])
        rc, err = run(project, "gate_lead_write_scope.py", bash_payload(project, line(reachable)))
        assert rc == 0, "the gate stopped following moves into ordinary directories: %s" % err[:300]
    finally:
        _right(cannot_enter, ENTRY, revoke=False)
        _right(cannot_list, LISTING, revoke=False)
    for path in (cannot_enter, cannot_list):
        assert _a_process_can_enter(path) and _a_process_can_list(path), (
            "this test took a right away that it could not give back, and %s stays behind: every "
            "later run of this suite trips over it" % path)


def test_the_words_the_kits_reader_steps_over_are_all_crossed():
    """DEC-0016: the enumeration the reader decides from GENERATES the values of its axis.

    The kits' `_stage_verb` walks past a list of words to find the verb, and what it hands back is
    what `_harness` then asks for a directory role. The last round crossed THREE lowercase verbs
    against nineteen positions and never touched that list at all -- two of the two holes it left
    were words out of it (`env cd`, `nice cd`, `sudo cd`: measured rc 0 while a real bash stayed in
    the tree and the relative write behind them rewrote the protected file).

    THE BRANCHES ARE ASKED, NOT THE GENERATOR, and that is DEC-0018 turned into a tripwire: a
    generator that reads the reader's word LIST covers the branch that steps over a word list and
    nothing else, and the branch that steps over an ASSIGNMENT (`"=" in low ...`) then has no cell
    while `_is_the_command_name` decides about it every day. So this walks the branches itself,
    proves a word against the running function and asks whether THAT word has a shape -- which
    stays red if the generator narrows back to tuples.
    """
    harness = _reader()
    words = _skipped_words(harness)
    assert words, "the kits' reader steps over no word at all -- then this axis measures nothing"
    generated = set(_prefix_shapes(words)) | set(_verb_shapes(harness))
    crossed = {label.split(" -- ")[0] for label in LINE_SHAPES}
    assert generated <= crossed, (
        "these values of the two generated axes have no shape in the table: %s"
        % sorted(generated - crossed))
    for branch, proven in _skip_branches(_kits_reader(harness)):
        if not proven or all(set(word) <= harness._SYNTAX_CHARACTERS for word in proven):
            continue  # syntax is what may stand in front of a command name (`_is_the_command_name`)
        assert set(_prefix_shapes(proven)) & crossed, (
            "the kits' `_stage_verb` steps over a word this branch accepts (%s: %s) and no shape "
            "in the table stands behind one" % (branch, proven))
    # The other direction needs no assertion and could not fail: `_crossed` builds its cells out of
    # THESE functions, so a value the enumerations stop producing stops being a cell in the same
    # step. What can go wrong is only the direction above -- a table built once and left behind.
    both = [label for label in LINE_SHAPES if " -- " in label]
    directions = {label.rsplit(" -- ", 1)[1] for label in both}
    assert len(directions) > 1, (
        "the table crosses the moves in one direction only (%s), so the base an uncomputable move "
        "is judged from is a claim again instead of an axis -- which is what DEC-0018 is about"
        % sorted(directions))
    deciding = {label.rsplit(" -- ", 1)[0] for label in both
                if LINE_SHAPES[label][2] != LINE_SHAPES[
                    "%s -- %s" % (label.rsplit(" -- ", 1)[0],
                                  sorted(directions - {label.rsplit(" -- ", 1)[1]})[0])][2]}
    assert deciding, (
        "no shape of the table answers differently in the two directions, so crossing them "
        "decides nothing and one of the two columns is not derived from the base at all")


def test_the_shells_this_reader_knows_are_the_ones_the_registration_names():
    """DEC-0016, the other enumeration: which shell a line is for decides which words are verbs.

    `_harness.SHELLS` says what `cd`, `pushd`, `popd` and `set-location` do and whether command
    names are compared case-insensitively; a tool it has no entry for moves the base at all. That is
    the fail-closed direction and it is silent, so the tripwire is here: the shell tools the
    REGISTRATION names are the ones that reach these gates, and every one of them needs an entry.

    Read off the registration rather than typed, which is the same rule the rest of this file keeps:
    what binds at session start is the file, not anybody's memory of it.
    """
    harness = _reader()
    registered = {tool for _script, tool in REGISTERED_PAIRS} & SHELL_TOOLS
    assert registered, "no shell tool is registered for any gate -- this axis measures nothing"
    assert registered == set(harness.SHELLS), (
        "the registration sends %s to these gates and `_harness.SHELLS` answers for %s; a shell "
        "without an entry moves no base at all, so every directory verb in it is invisible"
        % (sorted(registered), sorted(harness.SHELLS)))
    for tool, shell in sorted(harness.SHELLS.items()):
        assert shell["verbs"], "%s knows no directory verb at all" % tool
        for verb in shell["verbs"]:
            assert verb == verb.lower(), (
                "%s is spelled with capitals in %s's table, and a folding reader would compare it "
                "against a lowercased word forever" % (verb, tool))


def _kit_gains_a_separator(project, tmp_path, name, separator):
    """A copy of `project` whose KIT reader carries one more pipeline separator.

    APPENDED, NOT PATCHED INTO THE SOURCE TEXT: a test that asserts how a line of `team-kits/**` is
    spelled is a test another task's edit turns red for nothing, and `team-kits/**` is forbidden
    ground for the task this file belongs to. The extension is written as code that reads the
    tuple the module really ends up with, so a rename does not silently make it a no-op -- it makes
    the gate refuse with a NameError, which the assertions below see as "not the reason expected".
    """
    work = str(tmp_path / name)
    shutil.copytree(project, work)
    sys.path.insert(0, os.path.join(work, ".claude", "hooks"))
    import _harness
    path = os.path.join(_harness._kit_hooks_dir(work), "gate_write_scope.py")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n_PIPELINE_SEPARATORS = _PIPELINE_SEPARATORS + (%r,)\n" % (separator,))
    return work


def test_a_separator_this_reader_cannot_place_refuses_the_line(project, tmp_path):
    """Where a command ends is the kits' answer; this reader only adds what their tuple lacks.

    The two readings can drift -- that is the price H15 names for borrowing the kits' shell module
    -- and the direction that drift must NOT take is silence: a separator whose words are left with
    the verb in FRONT of them hides a write, which is how `echo hi & sed -i <kit file>` came out
    rc 0. So the check runs on every line, and the subject here is a line the gate otherwise
    ALLOWS, so nothing except the separator can be what refused it.

    THE OTHER END IS WHAT THE TRIPWIRE COSTS WHEN IT IS WRONG, and it is the whole line: a refusal
    here stops every call, this repo's own kernel invocation included. So a separator this reader
    DOES place must not fire it -- measured 2026-08-05 with `|` in the tuple, which `_harness`
    cuts stages at: the words behind it get a verb of their own, nothing is hidden, and the gate
    has to go on deciding. Before that end existed, the predicate refused it.
    """
    kernel_line = ("PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory "
                   "generate-index")
    work = _kit_gains_a_separator(project, tmp_path, "unknown-separator", "NEWLINE-ISH")
    rc, err = run(work, "gate_lead_write_scope.py", bash_payload(work, "echo hi"))
    assert rc == 2, "a separator this reader cannot place was read as an ordinary word"
    assert "cannot place" in err, "refused, but not for the separator: %s" % err[:300]
    placed = _kit_gains_a_separator(project, tmp_path, "known-separator", "|")
    rc, err = run(placed, "gate_lead_write_scope.py", bash_payload(placed, kernel_line))
    assert rc == 0, (
        "a separator this reader places itself stopped a line it has to judge: %s" % err[:300])
    assert run(placed, "gate_lead_write_scope.py",
               bash_payload(placed, "echo hi | " + RELATIVE_WRITE))[0] == 2, (
        "with that separator in the tuple, a write behind it stopped being judged")


# -- the hole list keeps its own rule (TSK-0013 F5, F6, F7) --------------------

HOLE_LIST = os.path.join(ROOT, "docs", "POST_V2_WISHLIST.md")
# The section of it that judges these four gates, opened by this heading and closed by the next
# heading of the same level.
HOLE_SECTION = "## 12."
# What the third column of the summary table must NOT be for an entry that is not closed: the rule
# stated in the section itself says an open entry names what takes the place of the protection.
NOTHING_SAID = ("", "-", "—", "–", "?")


def _hole_section():
    """The lines of the hole list that judge these gates, and only those."""
    with open(HOLE_LIST, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith(HOLE_SECTION))
    end = next((index for index, line in enumerate(lines[start + 1:], start + 1)
                if line.startswith("## ")), len(lines))
    return lines[start:end]


def _hole_entries(lines):
    """{H<n>: the lines of its entry} -- the entries this section actually carries."""
    out, current = {}, None
    for line in lines:
        found = re.match(r"### (H\d+)\b", line)
        if found:
            current = found.group(1)
            out[current] = []
        elif current:
            out[current].append(line)
    return out


def _hole_rows(lines):
    """[(entries named in the first cell, state, what takes the place)] of the summary table."""
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or not re.search(r"H\d+", cells[0]) or set(cells[1]) <= set("- "):
            continue
        rows.append((re.findall(r"H\d+", cells[0]), cells[1], cells[2]))
    return rows


# What a bold span looks like, and what the ENTRY's own verdict line opens with. The judgement of
# an entry is the last one it states -- an entry may record what a round decided and then what the
# full rule makes of it -- and it is the BOLD part of that line: what follows the bold span is
# reasoning, and reasoning names the other verdicts too.
BOLD_RX = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
VERDICT_RX = re.compile(r"\*\*(Urteil\b.+?)\*\*", re.DOTALL)
# The one word that turns a verdict into its opposite. A row may not claim a state its entry denies.
NEGATION = "nicht"


def _stated_verdict(body):
    """The verdict an entry states about itself, as the words of its last `**Urteil ...**` span.

    THE SPAN, NOT THE LINE: where the text wraps is a property of the editor, and a verdict that
    happened to break across two lines was read here as no verdict at all. What follows the bold
    span is reasoning, and reasoning names the other verdicts too -- so it stays outside.
    """
    stated = VERDICT_RX.findall("\n".join(body))
    return re.findall(r"\w+", stated[-1].lower()) if stated else None


def test_the_hole_list_judges_every_entry_it_carries():
    """The section's own rule, applied to the section: every entry is in the table, the table says
    what the entry says, and every open one names what takes the place of the protection.

    THE SUBJECT HERE IS THE TEXT, so reading the text is reading the thing under test -- and what is
    read is its STRUCTURE (headings, table rows, the bold span of a verdict line), not a sentence
    somebody could satisfy by quoting it. Measured 2026-08-05: two entries appeared under no row at
    all, so the column that has to name the replacement was empty for them without anything saying
    so; and the state column itself was checked by nothing -- three entries whose row and whose body
    said different things stayed green, and one of them escaped the replacement column entirely by
    being called closed.
    """
    lines = _hole_section()
    entries = _hole_entries(lines)
    rows = _hole_rows(lines)
    assert entries and rows, "the hole list section was not found where this test looks for it"
    judged = [name for names, _state, _replacement in rows for name in names]
    assert sorted(judged) == sorted(set(judged)), (
        "an entry is judged twice in the table: %s" % sorted(judged))
    assert set(judged) == set(entries), (
        "entries with no row: %s -- rows with no entry: %s"
        % (sorted(set(entries) - set(judged)), sorted(set(judged) - set(entries))))
    for names, state, replacement in rows:
        claimed = BOLD_RX.search(state)
        assert claimed, "the row over %s states no verdict: %r" % (", ".join(names), state)
        word = re.findall(r"\w+", claimed.group(1).lower())[0]
        for name in names:
            spoken = _stated_verdict(entries[name])
            assert spoken, "%s states no verdict of its own (`**Urteil ...**`)" % name
            assert word in spoken, (
                "the table calls %s %r and the entry itself says %r" % (name, word, " ".join(spoken)))
            assert NEGATION not in spoken[:spoken.index(word)], (
                "the table calls %s %r while its own verdict denies it: %r"
                % (name, word, " ".join(spoken)))
        if "GESCHLOSSEN" in state:
            continue
        assert replacement not in NOTHING_SAID, (
            "%s is not closed and its row does not say what takes the place of the protection"
            % ", ".join(names))


def test_every_test_the_hole_list_names_is_one_that_exists():
    """A closed entry names the test that goes red without its fix. That name is checkable.

    THE CLAIM AN ENTRY MAKES ABOUT ITSELF is "this is closed, and here is what would notice if it
    were reopened". A name that no longer resolves turns that into a claim nothing checks -- the
    same rot the constitution's prose had, one document further on. So the names are read out of
    the hole list and looked up in the SYNTAX TREE of this file, not searched for as text: a name
    that only appears in a docstring would otherwise answer for itself.

    Names are matched loosely on purpose (`…refuses_a_line…`): the entries abbreviate long test
    names, and demanding the full spelling would make the entries harder to read without checking
    anything more. What is asserted is that exactly one test answers to each.
    """
    defined = {node.name for node in ast.walk(ast.parse(open(
        os.path.join(HOOKS, "test_gates.py"), encoding="utf-8").read()))
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
    assert defined, "this file defines no tests at all"
    named, wrong = 0, []
    for entry, body in sorted(_hole_entries(_hole_section()).items()):
        text = "\n".join(body)
        # WHAT IS INSIDE THE BACKTICKS, WITH THE LINE BREAKS TAKEN OUT: the entries wrap long names
        # across lines, and a name read as two halves resolves to nothing. A span carrying a dot is
        # a file name and not a test.
        spans = [re.sub(r"\s+", "", span) for span in re.findall(r"`([^`]+)`", text, re.DOTALL)]
        for cited in sorted({span for span in spans
                             if span.lstrip("…._").startswith("test_") and "." not in span}):
            stem = cited.strip("_.…")
            matching = [name for name in defined if stem in name]
            named += 1
            if len(matching) != 1:
                wrong.append("%s names `%s`, and %d tests in %s answer to it"
                             % (entry, cited, len(matching), "test_gates.py"))
    assert not wrong, "\n".join(wrong)
    assert named >= 5, (
        "the hole list names %d test(s) of this file -- an entry that claims to be closed and "
        "names nothing that would notice is the claim this test exists for" % named)


# The entry that says what the cross table's OVER-REFUSAL is made of, and the paragraph it says it
# in. The claim is generated out of the table here rather than read as prose: it stood wrong in both
# directions at once -- two things named that had no such cell, four moves unnamed that were half of
# them -- and it had been corrected by hand the round before that.
OVER_REFUSAL_ENTRY = "H30"
COMPOSITION_RX = re.compile(r"\*\*Zusammensetzung[^*]*\*\*(.*?)(?=\n\n|\Z)", re.DOTALL)

# What a closed entry has to name when the cross table is what would notice its defect: the VALUES
# of that table it stands on. Nothing tied the two together before -- measured 2026-08-07, the
# hand-written axes can be cut until 100 of 1440 cells are left and every other test in this file
# stays green, because the tripwires cover the GENERATED axes and not the written-out values.
CELLS_RX = re.compile(r"\*\*Zellen[^*]*\*\*(.*?)(?=\n\n|\Z)", re.DOTALL)
TABLE_TEST = "test_gate1_refuses_a_line_exactly_where_the_shell_would_write"


def _over_refusal():
    """The cells where the gate refuses and the shell does not write the protected file."""
    return {label for label in LINE_SHAPES
            if LINE_SHAPES[label][1] is False and LINE_SHAPES[label][2]}


def test_the_hole_list_states_the_over_refusal_the_table_carries():
    """What an entry claims about the check set is GENERATED out of the check set.

    Measured 2026-08-07, and the claim had been corrected by hand one round earlier: the entry named
    the descriptor duplication and the words the kits' reader steps over, and neither has an
    over-refusal cell at all -- the second has cells whose shell column is UNCLAIMED, which is a
    different thing. It left four moves unnamed that are exactly half of the count it stated. Only
    the two numbers were right.

    BOTH DIRECTIONS FALL OUT OF ONE COMPARISON, which is why it is a set equality and not a
    containment: a move named without cells and a move with cells left unnamed are the two ways the
    sentence went wrong, and neither can be written into the document again.
    """
    body = "\n".join(_hole_entries(_hole_section())[OVER_REFUSAL_ENTRY])
    found = COMPOSITION_RX.search(body)
    assert found, (
        "%s no longer states what the over-refusal in the cross table is made of, so the claim this "
        "test generates has nowhere to be compared with" % OVER_REFUSAL_ENTRY)
    said = found.group(1)
    numbers = [int(number) for number in re.findall(r"\d+", said)]
    friction = _over_refusal()
    assert numbers[:2] == [len(friction), len(LINE_SHAPES)], (
        "%s says %s of the table's cells are over-refusal; the table has %d of %d"
        % (OVER_REFUSAL_ENTRY, " of ".join(str(number) for number in numbers[:2]),
           len(friction), len(LINE_SHAPES)))
    named = {re.sub(r"\s+", " ", span).strip()
             for span in re.findall(r"`([^`]+)`", said, re.DOTALL)}
    moves = {label.split(" -- ")[0] for label in friction}
    assert named == moves, (
        "%s names moves that have no over-refusal cell: %s -- and leaves these unnamed: %s"
        % (OVER_REFUSAL_ENTRY, sorted(named - moves), sorted(moves - named)))


def test_every_cell_a_closed_hole_names_is_one_the_table_carries():
    """An entry that leans on the cross table names the VALUES of it that carry its chain.

    THE HAND-WRITTEN AXES HAD NO TRIPWIRE. `test_the_words_the_kits_reader_steps_over_are_all
    _crossed` and `test_the_shells_this_reader_knows_are_the_ones_the_registration_names` bind the
    axes that are GENERATED out of the reader; the positions, the moves, the bases and the loose
    shapes are typed here, and deleting them costs nothing -- measured 2026-08-07, cut down to 100
    of 1440 cells with every other test in this file still green, and what was silently removable
    was exactly the values that carry closed holes.

    BOTH ENDS. A value an entry names and the table no longer carries is the cut; an entry that
    leans on the table and names no value at all is the tripwire being dropped instead of the cell.
    Which entries owe one is read off the entries themselves -- those that cite the table's test.
    """
    values = set(POSITIONS) | set(MOVES) | set(BASES) | set(LOOSE_SHAPES)
    owed, wrong, named = [], [], 0
    for entry, body in sorted(_hole_entries(_hole_section()).items()):
        text = "\n".join(body)
        if TABLE_TEST not in re.sub(r"\s+", "", text):
            continue
        found = CELLS_RX.search(text)
        spans = [re.sub(r"\s+", " ", span).strip()
                 for span in re.findall(r"`([^`]+)`", found.group(1), re.DOTALL)] if found else []
        if not spans:
            owed.append(entry)
            continue
        for span in spans:
            named += 1
            if span not in values and span not in LINE_SHAPES:
                wrong.append("%s names `%s`, and no value of the cross table is spelled that way"
                             % (entry, span))
    assert not owed, (
        "these entries say the cross table is what would notice their defect and name no value of "
        "it, so the values they stand on can be deleted without anything going red: %s" % owed)
    assert not wrong, "\n".join(wrong)
    assert named, (
        "no entry of the hole list leans on %s any more, so this test measured nothing" % TABLE_TEST)


# What an entry has to state when the TILDE check set is what would notice its defect: how big that
# set is and what the axis it gained is made of. Same reason as `CELLS_RX` above and a worse case --
# the set was not merely shrinkable, it was already too narrow: measured 2026-08-07, none of its
# 471 subjects carried quoting in the target word, and the shape that did was rc 0 through the real
# gate while bash rewrote the protected file.
SUBJECTS_RX = re.compile(r"\*\*Subjekte[^*]*\*\*(.*?)(?=\n\n|\Z)", re.DOTALL)
TILDE_TEST = "test_gate1_places_a_tilde_word_where_the_shell_puts_it"


def test_every_tilde_subject_a_closed_hole_names_is_one_the_check_set_carries():
    """An entry leaning on the tilde check set states its SIZE and the values of its quoting axis.

    GENERATED OUT OF THE SET AND COMPARED WITH IT, in both directions, which is what the same
    treatment of the cross table (`test_the_hole_list_states_the_over_refusal_the_table_carries`)
    exists for: a number that goes stale says nothing, and an axis named in prose that the set no
    longer carries says less. The set equality is the half that matters here -- the defect this
    round closed was an axis the check set did not have at all, so an entry that names its values
    cannot be satisfied by a set they were dropped from.
    """
    owed, named = [], 0
    prefixes = len(_tilde_prefixes(_reader()))
    for entry, body in sorted(_hole_entries(_hole_section()).items()):
        text = "\n".join(body)
        if TILDE_TEST not in re.sub(r"\s+", "", text):
            continue
        found = SUBJECTS_RX.search(text)
        if not found:
            owed.append(entry)
            continue
        said = found.group(1)
        # the numbers OUTSIDE the backticks: the values of the axis carry digits of their own
        numbers = [int(number) for number in re.findall(r"\d+", re.sub(r"`[^`]*`", " ", said))]
        assert numbers[:3] == [len(TILDE_SUBJECTS), len(TILDE_STATES), prefixes], (
            "%s says the tilde check set is %s; it is %d subjects out of %d states and %d prefixes"
            % (entry, " / ".join(str(number) for number in numbers[:3]),
               len(TILDE_SUBJECTS), len(TILDE_STATES), prefixes))
        spans = {re.sub(r"\s+", " ", span).strip()
                 for span in re.findall(r"`([^`]+)`", said, re.DOTALL)}
        assert spans == set(TILDE_QUOTINGS), (
            "%s names quotings the check set does not carry: %s -- and leaves these unnamed: %s"
            % (entry, sorted(spans - set(TILDE_QUOTINGS)), sorted(set(TILDE_QUOTINGS) - spans)))
        named += 1
    assert not owed, (
        "these entries say the tilde check set is what would notice their defect and state nothing "
        "about it, so it can be cut back to what they were measured against: %s" % owed)
    assert named, (
        "no entry of the hole list leans on %s any more, so this test measured nothing" % TILDE_TEST)


def _anchors(path):
    """What a document can be cited BY: the hole entries it carries and its numbered sections.

    Read off the document's own headings, so a document gains an anchor by carrying it and not by
    being listed anywhere.
    """
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    return (set(re.findall(r"^### (H\d+)\b", text, re.M)),
            set(re.findall(r"^## (\d+)\.", text, re.M)))


def _said_in(source):
    """Every unit of text a source file states something in: its strings and its comment blocks.

    PARSED, NOT SEARCHED. A docstring, a refusal message and a block of comment lines are the three
    places this apparatus makes claims in, and each of them is one statement -- so a reference and
    the anchor it is made with have to stand in the SAME one. Reading them off `ast` and `tokenize`
    also means a claim inside a string that no longer belongs to any code is not read as if it did.
    """
    out = [node.value for node in ast.walk(ast.parse(source))
           if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    block, previous = [], None
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        if previous is not None and token.start[0] != previous + 1 and block:
            out.append("\n".join(block))
            block = []
        block.append(token.string)
        previous = token.start[0]
    if block:
        out.append("\n".join(block))
    return out


def test_every_reference_to_a_measurement_leads_to_one(project):
    """A reference that names a document has to lead to one that carries what it is cited for.

    Measured 2026-08-05: the hole list assigned entries to the two measurement protocols by NUMBER
    RANGE, and three of the entries in the range were in neither document. A range is a claim about
    a file nobody checks; a reference beside the entry is one that can be. Measured again in the
    round after that: a docstring cited a protocol for six line shapes, three of which were in a
    DIFFERENT protocol -- because this half of the test asked only whether the file existed.

    BOTH DIRECTIONS ARE READ THE SAME WAY, and that is what this round adds: the entries of the
    hole list, and the apparatus itself, whose docstrings, refusal texts and comments point at
    protocols and at the hole list. A reference has to name what it is citing -- an entry (`H<n>`)
    for the hole list, a section for a measurement protocol -- and the document has to carry it.
    Which anchors a document has is read off the document (`_anchors`); a document that carries
    neither kind is cited by its name alone, because there is nothing finer to check it against.
    """
    entries = _hole_entries(_hole_section())
    for name, body in sorted(entries.items()):
        for relative in re.findall(r"docs/reviews/[A-Za-z0-9._-]+\.md", "\n".join(body)):
            path = os.path.join(ROOT, *relative.split("/"))
            assert os.path.isfile(path), "%s points at %s, which does not exist" % (name, relative)
            with open(path, encoding="utf-8") as handle:
                assert re.search(r"\b%s\b" % name, handle.read()), (
                    "%s cites %s, and that document does not carry it" % (name, relative))
    for entry in sorted(os.listdir(HOOKS)):
        if not entry.endswith(".py"):
            continue
        with open(os.path.join(HOOKS, entry), encoding="utf-8") as handle:
            source = handle.read()
        for said in _said_in(source):
            for relative in set(re.findall(r"docs/[A-Za-z0-9._/-]+\.md", said)):
                # A PATH THIS SUITE BUILDS IS A SUBJECT, NOT A REFERENCE: the gates' docstrings
                # quote measured command lines, and those name files in the stand-in project. So
                # both trees answer, and neither is a list -- the stand-in is whatever
                # `build_project` writes.
                here = os.path.join(ROOT, *relative.split("/"))
                assert os.path.isfile(here) or os.path.isfile(
                    os.path.join(project, *relative.split("/"))), (
                    "%s names %s, and nothing of that name exists in this repo or in the project "
                    "the suite builds" % (entry, relative))
                if not os.path.isfile(here):
                    continue
                holes, sections = _anchors(here)
                if holes:
                    assert holes & set(re.findall(r"\bH\d+\b", said)), (
                        "%s cites %s without naming an entry of it, so nothing says what the "
                        "reference is for: %r" % (entry, relative, said[:200]))
                elif sections:
                    assert sections & set(re.findall(r"section (\d+)", said)), (
                        "%s cites %s without naming a section of it, so nothing says what the "
                        "reference is for: %r" % (entry, relative, said[:200]))


# -- the deadline the registration sets (TSK-0011 F4) --------------------------

# RFC 5737 reserves these three ranges for documentation: no host is assigned in any of them, so
# nothing answers. What makes a question about one SLOW rather than instantly wrong is the SMB
# client's own retry, which is a property of the host running the test -- so the test measures that
# before it relies on it.
UNREACHABLE_NETS = ("192.0.2.%d", "198.51.100.%d", "203.0.113.%d")
# How many addresses those ranges give this test. The last octet stays inside a single subnet on
# purpose: what makes an address slow is that nothing routes to it, and that is a property of the
# range rather than of the number.
UNREACHABLE_ADDRESSES = 250


def _unreachable():
    """A UNC path in a range nothing is assigned in -- a DIFFERENT one every time it is asked.

    THE ADDRESS HAS TO BE ONE NOTHING ASKED ABOUT A MOMENT AGO: Windows remembers for a while that
    a host did not answer -- measured 2026-08-05 on this host, one address costs 42.18 s cold,
    0.00 s when asked again immediately, and 42.15 s again a minute and a half later, while a
    neighbour in the same range is cold throughout. A test that hands its subject an address some
    earlier run has already asked about measures that memory instead of the gate; the cut that
    stood here derived the address from the process id modulo 120, and a suite that starts a
    hundred processes puts the next run within reach of the same number. Drawn at random out of
    750, a repeat inside the window the measurement above shows is not a shape this host produces.
    """
    net = random.choice(UNREACHABLE_NETS)
    return "\\\\%s\\share\\f" % (net % random.randrange(2, UNREACHABLE_ADDRESSES))


def _cost_of_asking_about(path):
    """What this host charges for ONE filesystem question about `path`."""
    started = time.monotonic()
    try:
        os.stat(path)
    except OSError:
        pass
    return time.monotonic() - started


@pytest.fixture(scope="session")
def unreachable_cost():
    """What one question about an unroutable host costs here -- measured ONCE for the session.

    Once, because the address is spent by asking: the operating system remembers for a while that
    it did not answer, so this one is sacrificed to the measurement and every subject takes a fresh
    one (`_unreachable`).
    """
    return _cost_of_asking_about(_unreachable())


# How often a cost is sampled, and what is taken. THE WORST OF SEVERAL, because these numbers are
# what a later assertion is measured against: a run that happened to be fast produces a deadline
# the next run cannot keep, which is a test that fails for the machine's mood rather than for the
# gate. Measured 2026-08-05 on this host, single samples of the two runs below: 0.48 s to 0.87 s
# for a gate that answers at once, 0.67 s to 1.26 s for a whole verdict.
SAMPLES = 3


def _samples_of(sample):
    return [sample() for _ in range(SAMPLES)]


def _worst_of(sample):
    return max(_samples_of(sample))


# How long a gate process needs here before it can answer ANYTHING -- the interpreter start, the
# imports, the payload. Measured through a run that asks the filesystem nothing at all, because
# that is the floor no implementation can go below on this host; a call the gate ALLOWS is not that
# floor, it is the full price of a verdict, and comparing IT against a short registration is what
# made this test skip itself on a busy machine (measured 2026-08-05: 1.12 s against a 1 s
# registration, "no implementation could answer inside", while the gate answers such a call in
# 0.52 s).
def _cost_of_a_gate_that_answers_at_once(project, tmp_path):
    """`(the worst of the samples, the spread between them)`. The spread is this host's own timing
    noise, and it is what decides whether a margin below it can be measured at all."""
    work = str(tmp_path / "bare-cost")
    shutil.copytree(project, work)
    _set_registered_timeout(work, None)

    def once():
        started = time.monotonic()
        rc, _err = run(work, "gate_lead_write_scope.py", write_payload(work, "docs/note.md"))
        assert rc == 2, "the run that measures this host's floor was not the refusal it should be"
        return time.monotonic() - started

    taken = _samples_of(once)
    return max(taken), max(taken) - min(taken)


def _cost_of_one_gate_run(project):
    """What a WHOLE verdict costs here: a call this gate allows, walked to the end. It is the
    quantity a budget has to cover, and it is not the floor above."""
    def once():
        started = time.monotonic()
        run(project, "gate_lead_write_scope.py", write_payload(project, "docs/note.md"))
        return time.monotonic() - started

    return _worst_of(once)


def _register_another_group(work, script, matcher, seconds):
    """Add a SECOND registration of `script` to a copy, under `matcher`, with its own deadline."""
    path = os.path.join(work, ".claude", "settings.json")
    with open(path, encoding="utf-8") as handle:
        settings = json.load(handle)
    event = next(iter(settings["hooks"]))
    settings["hooks"][event].append({
        "matcher": matcher,
        "hooks": [{"type": "command", "timeout": seconds,
                   "command": 'python -B "${CLAUDE_PROJECT_DIR}/.claude/hooks/%s"' % script}]})
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)


def _set_registered_timeout(work, seconds):
    """Rewrite the deadline every hook entry of a COPY states -- or take it away (`None`)."""
    path = os.path.join(work, ".claude", "settings.json")
    with open(path, encoding="utf-8") as handle:
        settings = json.load(handle)
    for groups in settings["hooks"].values():
        for group in groups:
            for hook in group["hooks"]:
                if seconds is None:
                    hook.pop("timeout", None)
                else:
                    hook["timeout"] = seconds
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)


def _reserve_numbers():
    """The two numbers `_harness` reserves time by -- read from it, never copied into this file."""
    sys.path.insert(0, HOOKS)
    import _harness
    return _harness._SPENDABLE_SHARE, _harness._RESERVE_FLOOR


def _registrations(project, tmp_path):
    """The deadline this test writes into a copy -- DERIVED from what a run costs here.

    `(long, why)`: the registration under which an ordinary verdict still fits in the budget, which
    is what the counter-ends below need. A typed number measures nothing on a machine that is
    faster or slower than the one it was typed on.
    """
    verdict = _cost_of_one_gate_run(project)
    share, floor = _reserve_numbers()
    longer = next((seconds for seconds in range(1, 600)
                   if seconds - max(seconds * (1 - share), floor) >= 2 * verdict), None)
    return longer, ("a whole verdict costs %.2fs here, against a share of %.2f and a floor of "
                    "%.2fs" % (verdict, share, floor))


def _floor_case(bare, share, floor):
    """`(registration, the process start that shows the FLOOR is what keeps it)`, or None.

    THE BAND, AND WHY THERE IS ONE. A gate that kept only the SHARE sets its deadline
    `seconds * share` after its own first line and answers `bare + seconds * share` after the
    provider started it, which is past `seconds` exactly when `bare > seconds * (1 - share)`. A gate
    that keeps the floor answers `min(seconds, reserve)` after its start, which is inside the
    registration when `bare < min(seconds, reserve)`. Both together are a band of process starts,
    and its upper end is the floor itself -- so a host whose own start is past the floor cannot show
    the property at all, and neither can one that is far below the band.

    THAT IS WHY `bare` IS CONTROLLED HERE INSTEAD OF HOPED FOR (`_slowed`): measured under load
    2026-08-05 a bare start of 4.76s against a floor of 1.50s, and idle on this host 0.13s -- the
    test went red for the machine's speed in BOTH directions while the gate was untouched. The
    margin on both sides is maximised rather than hoped for.
    """
    best, margin = None, 0.0
    for seconds in range(1, 60):
        reserve = max(seconds * (1.0 - share), floor)
        low, high = seconds * (1.0 - share), min(float(seconds), reserve)
        want = (low + high) / 2.0
        if high <= low or want < bare or min(high - want, want - low) <= margin:
            continue
        best, margin = (seconds, want), min(high - want, want - low)
    return best and (best[0], best[1], margin)


def _slowed(project, tmp_path, name, seconds):
    """A copy whose gate processes need `seconds` longer BEFORE `_harness` starts its own clock.

    THE ONE QUANTITY IN THIS PROBLEM A PROCESS CANNOT SEE is what happened before its first line,
    and it is the quantity the reserve exists for. Making it a CONTROLLED variable is what stops
    this test from measuring the machine: the sleep goes immediately in front of `_LOADED_AT`, which
    is by definition the part of the start the gate cannot measure, and the line it goes in front of
    is found in the module's syntax tree rather than by matching text -- so a `_harness` that starts
    its clock somewhere else fails this instead of silently sleeping in the wrong place.
    """
    work = str(tmp_path / name)
    shutil.copytree(project, work)
    path = os.path.join(work, ".claude", "hooks", "_harness.py")
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().splitlines(True)
    starts = [node.lineno for node in ast.parse("".join(lines)).body
              if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == "_LOADED_AT"
                      for target in node.targets)]
    assert len(starts) == 1, (
        "`_harness` no longer starts its clock in exactly one place (%s), so the part of the "
        "process start this test controls could not be placed" % (starts,))
    lines.insert(starts[0] - 1, "import time as _before; _before.sleep(%r)\n" % (seconds,))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(lines))
    return work


def _without_the_floor(work):
    """The same copy with the reserve reduced to its SHARE -- the counter-end of the floor.

    Appended rather than patched into the text: what is asserted is the NUMBER the module ends up
    with, so a rename raises inside the gate and `guarded()` turns that into a refusal the
    assertions below see as "not the reason expected", never into a quiet pass.
    """
    path = os.path.join(work, ".claude", "hooks", "_harness.py")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n_RESERVE_FLOOR = 0.0\n")
    return work


def _refused_for_the_deadline(work, seconds):
    """Run the gate on a candidate this host cannot answer about, and time it.

    THE ADDRESS IS FRESH AND IT IS TRIED AGAIN IF IT WAS NOT SLOW: an address the operating system
    still remembers costs nothing, and a run against one would report that memory as a verdict. A
    host that hands out three cold addresses in a row and is fast about all of them is a host this
    property cannot be measured on, and the caller says so instead of passing.
    """
    for _ in range(3):
        started = time.monotonic()
        rc, err = run(work, "gate_lead_write_scope.py",
                      bash_payload(work, 'sed -i "s/a/b/" "%s"' % _unreachable()))
        elapsed = time.monotonic() - started
        if rc == 2 and "registration allows" in err:
            return rc, err, elapsed
        if elapsed > seconds:
            return rc, err, elapsed
    return rc, err, elapsed


def test_gate1_answers_before_its_registration_gives_up(project, tmp_path, unreachable_cost):
    """A candidate must not be able to decide the call by taking longer than the provider waits.

    A hook still deciding when its timeout expires is killed, and the provider reads a kill the
    way it reads a crash -- "hook error, carry on", i.e. an ALLOW. Measured 2026-08-05 against
    gate 1's registered 120 s: one candidate on an unroutable host cost 21.6 s, three 85.0 s and
    five 211.3 s -- the last rc 0 with no stderr at all, so the write was never judged.

    THE DEADLINE IS READ FROM THE REGISTRATION, so this moves the registration and expects the gate
    to follow: the copy states a short one, and the verdict has to be out before it. Both
    counter-ends in the same run, because a gate that just refused everything after the change
    would satisfy the first assertion -- under the SAME deadline a protected path is still refused
    for being protected, and a free one is still allowed.

    THE RESERVE IS THE LARGER OF A SHARE AND A FLOOR, and the floor is measured by CONTROLLING the
    quantity it exists for instead of waiting for the host to have it: a fifth of a short
    registration is smaller than a process start, so a gate keeping only the share plans past the
    moment it is killed. `_slowed` puts a known start in front of `_harness`'s own clock,
    `_floor_case` picks the registration that shows the difference with the widest margin on both
    sides, and `_without_the_floor` is the counter-end -- the SAME copy with the floor taken away
    has to MISS the deadline, or the floor is decorating.

    NOTHING HERE SKIPS, AND NOTHING HERE FAILS FOR THE MACHINE'S SPEED. A host that cannot show the
    property -- because it answers about an unroutable address at once, or because a gate process
    costs more before its first line than the floor itself -- has not measured the gate, and this
    says so as a failure that names what stopped it. The number that would have to change in the
    second case is `_harness._RESERVE_FLOOR`, not anything in this file.
    """
    longer, measured = _registrations(project, tmp_path)
    assert longer, ("no registration on this host leaves room for an ordinary verdict: %s"
                    % measured)
    assert unreachable_cost > longer, (
        "this host answers about an unroutable host in %.2fs, so a %ds registration is never at "
        "stake and nothing about the deadline was measured here"
        % (unreachable_cost, longer))
    work = str(tmp_path / "deadline-long")
    shutil.copytree(project, work)
    _set_registered_timeout(work, longer)
    rc, err, elapsed = _refused_for_the_deadline(work, longer)
    assert rc == 2, "a candidate this host cannot answer about was waved through: rc=%d" % rc
    assert "registration allows" in err, "refused, but not for the deadline: %s" % err[:300]
    assert elapsed < longer, (
        "the gate answered after %.2fs while its registration gives it %ds -- the provider would "
        "have killed it, and a killed hook is an allow (%s)" % (elapsed, longer, measured))
    assert run(work, "gate_lead_write_scope.py",
               write_payload(work, "team-kits/kernel/state.py"))[0] == 2, (
        "under a deadline it can keep, the gate stopped protecting anything")
    assert run(work, "gate_lead_write_scope.py", write_payload(work, "docs/note.md"))[0] == 0, (
        "under a deadline it can keep, the gate turned into one that refuses everything")

    bare, noise = _cost_of_a_gate_that_answers_at_once(project, tmp_path)
    share, floor = _reserve_numbers()
    case = _floor_case(bare, share, floor)
    assert case, (
        "a gate process here needs %.2fs before its own first line, and the reserve's floor is "
        "%.2fs -- past the floor there is no registration under which the floor can keep the "
        "deadline either, so nothing about it was measured. What has to change is "
        "`_harness._RESERVE_FLOOR`, not this test." % (bare, floor))
    seconds, wanted, margin = case
    assert margin > noise, (
        "the widest band this host offers is %.2fs wide on either side, and this host's own timing "
        "noise over %d runs of the same gate is %.2fs -- a difference under the noise is not a "
        "measurement, so nothing about the floor was shown here" % (margin, SAMPLES, noise))
    keeps = _slowed(project, tmp_path, "deadline-floor", wanted - bare)
    _set_registered_timeout(keeps, seconds)
    rc, err, elapsed = _refused_for_the_deadline(keeps, seconds)
    assert rc == 2 and "registration allows" in err, (
        "with a start of %.2fs in front of it the gate did not refuse for its deadline: rc=%d %s"
        % (wanted, rc, err[:300]))
    assert elapsed < seconds, (
        "the gate answered after %.2fs while its registration gives it %ds, with %.2fs of that "
        "spent before its own first line" % (elapsed, seconds, wanted))
    misses = _without_the_floor(_slowed(project, tmp_path, "deadline-share-only", wanted - bare))
    _set_registered_timeout(misses, seconds)
    _rc, _err, without = _refused_for_the_deadline(misses, seconds)
    assert without > seconds, (
        "with the reserve cut down to its share the same gate still answered inside %ds (%.2fs), "
        "so this run did not measure the floor at all (%s, start %.2fs)"
        % (seconds, without, measured, wanted))


def _a_line_too_long_to_read_in(harness, seconds):
    """A command line whose READING alone costs more than `seconds`, sized by measuring the growth.

    NOT A TYPED SIZE. What reading a substitution costs grows faster than the text is long, and by
    how much is a property of this host -- so two small samples are taken through the function that
    runs, the exponent between them is read off, and the size is computed from it. A host on which
    the cost does not grow at all is one this property cannot be shown on, and the caller is told
    rather than passed.

    The line is a substitution opener repeated, with one closer: that is the shape whose readings
    `_harness._closings` multiplies (both endings, then recursion), and it is the shape the chain
    behind H35 was measured with.
    """
    def line(count):
        return "echo " + "$(" * count + ")"

    def cost(count):
        started = time.monotonic()
        harness.substituted_lines(line(count), "Bash")
        return max(time.monotonic() - started, 1e-6)

    base = 64
    small, large = cost(base), cost(2 * base)
    growth = math.log(large / small, 2) if large > small else 0.0
    assert growth > 1.0, (
        "reading %d openers costs %.4fs here and reading %d costs %.4fs, so the cost does not grow "
        "with the line at all and no length reaches a deadline" % (base, small, 2 * base, large))
    return line(int(2 * base * (2.0 * seconds / large) ** (1.0 / growth)) + 1)


def test_gate1_answers_before_its_registration_however_long_the_line_takes_to_read(project,
                                                                                   tmp_path):
    """A line must not be able to decide the call by costing more to READ than the provider waits.

    THE BOUND HAS TO SIT OUTSIDE THE READING, and that is what this measures. `substituted_lines`
    checked the budget once per CALL and said in its own docstring that it was bounded by it; the
    cost is inside a call, so the check could not fire. Measured 2026-08-07, one tool call and no
    preparation: 2444 characters of command line -- a `sed -i` on a kit file with the openers behind
    a `#` -- were rc 2 only after 150.6 s against gate 1's registered 120, and bash really rewrote
    the file. Past the registration the hook is killed, and a killed hook is an ALLOW
    (`docs/POST_V2_WISHLIST.md` H35).

    THE SIZE IS DERIVED FROM THE HOST (`_a_line_too_long_to_read_in`) and the registration from what
    a verdict costs here (`_registrations`), so nothing in this test is a number typed on the
    machine it was written on.

    BOTH ENDS, under the SAME registration: a gate that answered "too slow" to everything would pass
    the first half, so a protected path still has to be refused for being protected and a free one
    still allowed.
    """
    harness = _reader()
    seconds, measured = _registrations(project, tmp_path)
    assert seconds, ("no registration on this host leaves room for an ordinary verdict: %s"
                     % measured)
    work = str(tmp_path / "deadline-reading")
    shutil.copytree(project, work)
    _set_registered_timeout(work, seconds)
    started = time.monotonic()
    rc, err = run(work, "gate_lead_write_scope.py",
                  bash_payload(work, _a_line_too_long_to_read_in(harness, seconds)))
    elapsed = time.monotonic() - started
    assert rc == 2, (
        "a line this gate could not read inside its budget was waved through: rc=%d after %.2fs"
        % (rc, elapsed))
    assert "registration allows" in err, (
        "refused after %.2fs, but not for the deadline -- so the line was cheap enough to read and "
        "nothing about the budget was measured: %s" % (elapsed, err[:300]))
    assert elapsed < seconds, (
        "the gate answered after %.2fs while its registration gives it %ds -- the provider would "
        "have killed it, and a killed hook is an allow (%s)" % (elapsed, seconds, measured))
    assert run(work, "gate_lead_write_scope.py",
               write_payload(work, "team-kits/kernel/state.py"))[0] == 2, (
        "under the same registration the gate stopped protecting anything")
    assert run(work, "gate_lead_write_scope.py", write_payload(work, "docs/note.md"))[0] == 0, (
        "under the same registration the gate turned into one that refuses everything")


def test_gate1_answers_before_the_shortest_registration_that_applies(project, tmp_path,
                                                                     unreachable_cost):
    """Which registrations apply to a call is the PROVIDER's reading of the matcher, not a split.

    A matcher was read here as an alternation of tool names. The provider reads it as an
    expression, so a group whose matcher is one (`Ba.h`) applied to a call that this gate did not
    count -- and when that group states the SHORTER deadline, the gate plans with the longer one
    and is killed, which the provider reads as an allow. Measured 2026-08-05: registered 60 s
    literally and 5 s under an expression, the gate answered rc 0 after 43.1 s, eight times past
    the entry that applied; reading the matcher as the provider does, rc 2 after 4.1 s.

    THE COUNTER-END IS A REGISTRATION THAT DOES NOT APPLY, and it is what stops "just take the
    smallest number in the file": a group naming a tool that never fires states 1 s here, and an
    ordinary call still has to be judged rather than refused for a deadline that was never its own.
    """
    longer, measured = _registrations(project, tmp_path)
    seconds = longer
    assert unreachable_cost > seconds, (
        "this host answers about an unroutable host in %.2fs, so a %ds registration is never at "
        "stake and nothing about the matcher was measured here (%s)"
        % (unreachable_cost, seconds, measured))
    work = str(tmp_path / "matcher-expression")
    shutil.copytree(project, work)
    _set_registered_timeout(work, int(unreachable_cost) + 60)
    _register_another_group(work, "gate_lead_write_scope.py", "Ba.h", seconds)
    rc, err, elapsed = _refused_for_the_deadline(work, seconds)
    assert rc == 2 and "registration allows" in err, (
        "the call was not refused for the deadline: rc=%d %s" % (rc, err[:300]))
    assert elapsed < seconds, (
        "the gate answered after %.2fs while a registration that matches this call gives it %ds"
        % (elapsed, seconds))
    other = str(tmp_path / "matcher-that-never-fires")
    shutil.copytree(project, other)
    _set_registered_timeout(other, 60)
    _register_another_group(other, "gate_lead_write_scope.py", "NeverFires", 1)
    assert run(other, "gate_lead_write_scope.py", write_payload(other, "docs/note.md"))[0] == 0, (
        "a registration for a tool this call is not made with decided the deadline anyway")


def test_a_gate_whose_registration_states_no_deadline_refuses(project, tmp_path):
    """The fail-closed half, and the reason every entry has to state one.

    A gate that cannot read its own deadline cannot promise to answer before it, and the direction
    that costs nothing to be wrong in is the refusal. The subject is a call this gate normally
    ALLOWS, so nothing except the missing deadline can be what refused it.
    """
    work = str(tmp_path / "no-deadline")
    shutil.copytree(project, work)
    _set_registered_timeout(work, None)
    rc, err = run(work, "gate_lead_write_scope.py", write_payload(work, "docs/note.md"))
    assert rc == 2, "a gate that cannot know its deadline judged the call anyway"
    assert "timeout" in err, "refused, but not for the missing deadline: %s" % err[:300]


def test_every_registered_hook_states_the_time_it_gets():
    """Read off the registration, which is the file both the provider and the gate read.

    `_harness.Deadline` refuses when it finds no `timeout` for the call it is judging, so an entry
    added without one does not degrade quietly -- it stops every call of that event. This is the
    tripwire that says so before a session finds out.
    """
    with open(os.path.join(ROOT, ".claude", "settings.json"), encoding="utf-8") as handle:
        settings = json.load(handle)
    entries = [hook for groups in settings["hooks"].values() for group in groups
               for hook in group["hooks"]]
    assert entries, "this repo registers no hooks at all"
    for hook in entries:
        assert isinstance(hook.get("timeout"), (int, float)), (
            "%r states no `timeout`, so the gate it starts cannot know when it will be killed"
            % hook.get("command"))


# -- which direction a candidate meets an area from (TSK-0011 F6) --------------


def test_gate1_says_whether_a_path_is_an_area_or_merely_holds_one(project):
    """A refusal that cannot tell the two apart says something false about one of them.

    The containment test answers yes in both directions -- and it must, or `rm -rf team-kits` would
    read as an unrelated path. The reason behind it, though, described the AREA while claiming it
    of the CANDIDATE: measured 2026-08-05, `cp -r docs C:/` was refused with the words "this is
    canonical project state", about a drive letter.

    Both ends, because a note glued onto every refusal would pass the first assertion alone.
    """
    holds = run(project, "gate_lead_write_scope.py", bash_payload(project, "cp -r docs .."))
    assert holds[0] == 2, "a copy whose target holds the whole repo was allowed"
    assert "stands UNDER it" in holds[1], (
        "a candidate that only CONTAINS the protected area was refused as though it were it: %s"
        % holds[1][:300])
    inside = run(project, "gate_lead_write_scope.py",
                 bash_payload(project, 'sed -i "s/a/b/" project_memory/README.md'))
    assert inside[0] == 2, "a write into canonical state was allowed"
    assert "canonical project state" in inside[1]
    assert "stands UNDER it" not in inside[1], (
        "a write INTO canonical state was described as if it merely contained it: %s"
        % inside[1][:300])


# -- what a kit is, asked of the kernel (TSK-0011 F8) --------------------------


def test_the_kit_these_gates_read_is_the_one_the_kernel_calls_a_kit(project, tmp_path):
    """`_kit_hooks_dir` asks `kernel.hashing.is_kit_dir`; it used to spell the predicate out again.

    A COPIED PREDICATE IS MEASURED BY MAKING THE TWO DISAGREE: this clone teaches the kernel a
    different marker for "this directory is a kit" and plants a directory that satisfies only the
    new one. The gates have to follow the kernel; a second opinion kept here answers with the old
    kit and turns this red.

    THE KERNEL IS TAUGHT BY APPENDING TO IT, not by asserting how its predicate is spelled: a test
    that pins a line of `team-kits/**` goes red for an edit that has nothing to do with it, and
    that tree is forbidden ground for the task this file belongs to. The redefinition below is the
    last one the module makes, so it is the one the gates see -- and if the name it replaces ever
    disappears, nothing calls it any more and the assertion below fails rather than passing on a
    prediction nobody checked.
    """
    work = str(tmp_path / "kit-predicate")
    shutil.copytree(project, work)
    hashing = os.path.join(work, "team-kits", "kernel", "hashing.py")
    with open(hashing, "a", encoding="utf-8") as handle:
        handle.write("\n\ndef is_kit_dir(path):\n"
                     "    return os.path.isdir(os.path.join(path, 'roles'))\n")
    planted = os.path.join(work, "team-kits", "aaa-kit")
    os.makedirs(os.path.join(planted, "roles"))
    os.makedirs(os.path.join(planted, "hooks"))
    with open(os.path.join(planted, "hooks", "_compat.py"), "w", encoding="utf-8") as handle:
        handle.write("")
    code = ("import os, sys\n"
            "sys.path.insert(0, os.path.join(sys.argv[1], '.claude', 'hooks'))\n"
            "import _harness\n"
            "print(_harness._kit_hooks_dir(sys.argv[1]))\n")
    done = subprocess.run([sys.executable, "-B", "-c", code, work], cwd=work,
                          capture_output=True, text=True,
                          env=dict(os.environ, CLAUDE_PROJECT_DIR=work))
    assert done.returncode == 0, done.stderr[-600:]
    assert done.stdout.strip() == os.path.join(planted, "hooks"), (
        "the gates read %r as the kit while the kernel calls only %r one"
        % (done.stdout.strip(), os.path.join(planted, "hooks")))
