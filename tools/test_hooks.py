#!/usr/bin/env python3
"""
Behaviour tests for the shipped enforcement hooks + scripts/quality.py (dev-team kit).

The harness blocks other repos' merges on missing tests; it must test its OWN security machinery.
Each hook is run as a real subprocess with synthetic stdin JSON and CLAUDE_PROJECT_DIR, and asserted
on its exit code (0 = allow, 2 = block for guards/gates, 1 = red for quality.py). Run: pytest tools/
"""
import ast
import fnmatch
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tokenize

import pytest

import conftest
from conftest import load_kit_module

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "team-kits", "dev-team", "hooks")
RESEARCH_HOOKS = os.path.join(ROOT, "team-kits", "research-team", "hooks")
OFFICE_HOOKS = os.path.join(ROOT, "team-kits", "office-team", "hooks")
OFFICE_SCRIPTS = os.path.join(ROOT, "team-kits", "office-team", "templates", "repo", "scripts")
OFFICE_PROFILE = os.path.join(ROOT, "team-kits", "office-team", "templates",
                              "project_memory", "business_profile.yaml")
QUALITY = os.path.join(ROOT, "team-kits", "dev-team", "templates", "repo", "scripts", "quality.py")
KIT_CHECKS = os.path.join(ROOT, "team-kits", "dev-team", "templates", "repo", "scripts", "kit_checks.py")
MERGE_SETTINGS = os.path.join(ROOT, "user", "merge_settings.py")


def run_hook_process(name, payload, project_dir, hooks_dir=None, extra_env=None):
    # HARNESS_KERNEL_PATH: the kernel-backed gates resolve `kernel` relative to the PROJECT, and a
    # tmp_path repo has no `.claude/kernel` — without this they would fail closed on every call and
    # the tests would read as "the gate works" while measuring a missing install.
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project_dir),
               HARNESS_KERNEL_PATH=os.path.join(ROOT, "team-kits"))
    env.update(extra_env or {})
    return subprocess.run([sys.executable, os.path.join(hooks_dir or HOOKS, name)],
                          input=json.dumps(payload), capture_output=True, text=True,
                          env=env, timeout=60)


def run_hook(name, payload, project_dir, hooks_dir=None):
    return run_hook_process(name, payload, project_dir, hooks_dir).returncode


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ---------------- global settings merge ----------------
def test_settings_merge_preserves_personal_values_and_unions_permissions(tmp_path):
    ours = {
        "_comment": "not installed",
        "theme": "dark",
        "statusLine": {"type": "command", "command": "bundled"},
        "telemetryEnabled": False,
        "permissions": {
            "allow": ["Bash(git *)", "Bash(pytest *)", "Bash(git *)"],
            "deny": ["Read(.env)", "Read(**/*.pem)"],
            "ask": ["Bash(release *)"],
        },
    }
    personal = {
        "theme": "light",
        "statusLine": {"type": "command", "command": "my-status"},
        "customSetting": "keep-me",
        "permissions": {
            "allow": ["Bash(custom *)", "Bash(git *)", "Bash(custom *)"],
            "deny": ["Read(private.txt)"],
            "ask": ["Bash(prod *)"],
            "defaultMode": "plan",
        },
    }
    ours_path = tmp_path / "defaults.json"
    target_path = tmp_path / "settings.json"
    ours_path.write_text(json.dumps(ours), encoding="utf-8")
    original = json.dumps(personal, indent=2) + "\n"
    target_path.write_text(original, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, MERGE_SETTINGS, str(ours_path), str(target_path)],
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, result.stderr
    merged = json.loads(target_path.read_text(encoding="utf-8"))
    assert merged["theme"] == "light"
    assert merged["statusLine"]["command"] == "my-status"
    assert merged["telemetryEnabled"] is False
    assert merged["customSetting"] == "keep-me"
    assert merged["permissions"] == {
        "allow": ["Bash(custom *)", "Bash(git *)", "Bash(pytest *)"],
        "deny": ["Read(private.txt)", "Read(.env)", "Read(**/*.pem)"],
        "ask": ["Bash(prod *)"],
        "defaultMode": "plan",
    }
    assert "_comment" not in merged
    assert (tmp_path / "settings.json.bak").read_text(encoding="utf-8") == original


def test_settings_merge_adds_missing_permission_lists_but_preserves_malformed_values(tmp_path):
    ours_path = tmp_path / "defaults.json"
    target_path = tmp_path / "settings.json"
    ours_path.write_text(json.dumps({
        "permissions": {"allow": ["Bash(git *)"], "deny": ["Read(.env)"]},
    }), encoding="utf-8")
    target_path.write_text(json.dumps({
        "permissions": {"allow": "managed-externally"},
    }), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, MERGE_SETTINGS, str(ours_path), str(target_path)],
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0
    merged = json.loads(target_path.read_text(encoding="utf-8"))
    assert merged["permissions"]["allow"] == "managed-externally"
    assert merged["permissions"]["deny"] == ["Read(.env)"]
    assert "preserving non-list permissions.allow" in result.stderr


def test_settings_merge_rejects_invalid_existing_json_without_touching_it(tmp_path):
    ours_path = tmp_path / "defaults.json"
    target_path = tmp_path / "settings.json"
    ours_path.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
    invalid = '{"theme": '
    target_path.write_text(invalid, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, MERGE_SETTINGS, str(ours_path), str(target_path)],
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 2
    assert "left unchanged" in result.stderr
    assert target_path.read_text(encoding="utf-8") == invalid
    assert not (tmp_path / "settings.json.bak").exists()


# ---------------- guard_pm_scope ----------------
def test_pm_blocked_from_src(tmp_path):
    (tmp_path / "project_memory").mkdir()
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "src" / "x.py")}, "cwd": str(tmp_path)}
    assert run_hook("guard_pm_scope.py", payload, tmp_path) == 2


def test_subagent_allowed_in_src(tmp_path):
    (tmp_path / "project_memory").mkdir()
    payload = {"tool_name": "Write", "agent_id": "sub-1",
               "tool_input": {"file_path": str(tmp_path / "src" / "x.py")}, "cwd": str(tmp_path)}
    assert run_hook("guard_pm_scope.py", payload, tmp_path) == 0


def test_pm_allowed_in_project_memory(tmp_path):
    (tmp_path / "project_memory").mkdir()
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": str(tmp_path / "project_memory" / "product" /
                                                "active" / "PR-0001.yaml")},
               "cwd": str(tmp_path)}
    assert run_hook("guard_pm_scope.py", payload, tmp_path) == 0


# ---------------- guard_agent_spawn ----------------
@pytest.fixture
def kit_repo(tmp_path):
    write(str(tmp_path / ".claude" / "agents" / "project-manager.md"), "x")
    write(str(tmp_path / ".claude" / "agents" / "backend-developer.md"), "x")
    write(str(tmp_path / ".claude" / "settings.json"), '{"agent": "project-manager"}')
    return tmp_path


def test_spawn_lead_blocked(kit_repo):
    payload = {"tool_name": "Agent", "tool_input": {"subagent_type": "project-manager"}, "cwd": str(kit_repo)}
    assert run_hook("guard_agent_spawn.py", payload, kit_repo) == 2


WORK_ORDER = ("objective: implement SR-0001\n"
              "read_first: [tasks/active/TSK-0001.yaml, system/active/SR-0001.yaml]\n"
              "output: summary, status\nboundaries: no schema changes\n")


def test_spawn_specialist_allowed(kit_repo):
    payload = {"tool_name": "Agent",
               "tool_input": {"subagent_type": "backend-developer", "run_in_background": False,
                              "prompt": WORK_ORDER},
               "cwd": str(kit_repo)}
    assert run_hook("guard_agent_spawn.py", payload, kit_repo) == 0


def test_spawn_without_background_flag_blocked(kit_repo):
    # V14 backstop: the platform defaults to background — 37/37 real spawns went that way by omission.
    payload = {"tool_name": "Agent",
               "tool_input": {"subagent_type": "backend-developer", "prompt": WORK_ORDER},
               "cwd": str(kit_repo)}
    assert run_hook("guard_agent_spawn.py", payload, kit_repo) == 2


def test_spawn_explicit_background_allowed(kit_repo):
    # explicit true = a deliberate parallel batch — allowed (the PM must await all notifications)
    payload = {"tool_name": "Agent",
               "tool_input": {"subagent_type": "backend-developer", "run_in_background": True,
                              "prompt": WORK_ORDER},
               "cwd": str(kit_repo)}
    assert run_hook("guard_agent_spawn.py", payload, kit_repo) == 0


def test_spawn_without_work_order_schema_blocked(kit_repo):
    # Anthropic: vague delegations duplicate work/leave gaps — objective/output are the floor
    payload = {"tool_name": "Agent",
               "tool_input": {"subagent_type": "backend-developer", "run_in_background": False,
                              "prompt": "please implement the feature from the tasks file"},
               "cwd": str(kit_repo)}
    assert run_hook("guard_agent_spawn.py", payload, kit_repo) == 2


def test_spawn_generic_blocked(kit_repo):
    payload = {"tool_name": "Agent", "tool_input": {"subagent_type": ""}, "cwd": str(kit_repo)}
    assert run_hook("guard_agent_spawn.py", payload, kit_repo) == 2


# ---------------- gate_git (QA Evidence binding) ----------------
PR_FIELDS = {
    "title": "Checkout flow",
    "class": "normal",
    "problem": "no checkout",
    "goal": "working checkout",
    "acceptance_criteria": [{"id": "AC-1", "text": "order completes"}],
    "invariants": [],
    "out_of_scope": [],
    "priority": "high",
    "user_story": "As a buyer I can pay",
}


def capture_root_item(repo, fields=None, status="DELIVERED"):
    """Give a repo its first typed root item — what `_root.has_root_item` now looks for.

    Written THROUGH the kernel, not by hand: the merge gates ask the state validator whether the
    state is complete, so a hand-rolled item would make every gate test measure a broken fixture
    rather than the gate.

    `status` walks the type's own chain to that status, because a merge is judged against it:
    `gate_git` refuses a merge for an item still in its DRAFT (nothing approved this work) or in a
    terminal status off the chain (the project dropped it). DELIVERED is the default because it is
    where the PM's checklist merges from — a fixture stuck in DRAFT would make every evidence test
    below measure the status tooth instead. `status=None` leaves the item where capture put it.

    THE WALK GOES THROUGH `conftest.walk_to_status`, which mints the approvals the gated edges
    need instead of transitioning past them. It used to call `state.transition` in a loop, and
    the day `transition` started demanding an approval that loop was the tempting place to put a
    bypass — see the fixture's own docstring for why there is none.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    from conftest import walk_to_status
    root = os.path.join(str(repo), "project_memory")
    os.makedirs(root, exist_ok=True)
    state = ProjectState(root)
    item = state.capture("PR", dict(fields or PR_FIELDS))
    if status is not None:
        item = walk_to_status(state, item, status)
    return item


def capture_invariant(repo, scope, value=None, text=None, source="PR-0001"):
    """Give a repo an `INV` item — the V2 home of every rule and every config knob.

    Through the kernel, for the same reason `capture_root_item` is: `report.py` enforces that an
    `INV` carries EXACTLY ONE of `text` or `value`, so a hand-written fixture could set both and
    the readers under test would be measured against a file no project can have.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    root = os.path.join(str(repo), "project_memory")
    os.makedirs(root, exist_ok=True)
    fields = {"scope": scope, "source": source,
              "check": {"kind": "test", "ref": "tests/test_invariants.py::test_it"}}
    if value is not None:
        fields["value"] = value
    else:
        fields["text"] = text or "the rule this invariant states"
    return ProjectState(root).capture("INV", fields)


@pytest.fixture
def prd_repo(tmp_path):
    capture_root_item(tmp_path)
    return tmp_path


def evidence_dir(repo):
    """Where Evidence lives, asked of the constant and never spelled out a second time."""
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ACTIVE_DIRS
    return os.path.join(str(repo), "project_memory", *ACTIVE_DIRS["EVD"].split("/"))


def capture_evidence(repo, kind="test", result="pass", related=("PR-0001",), summary="qa run"):
    """Record an Evidence item the way a QA/reviewer role is told to — through the shipped CLI.

    `kernel.cli` and not `ProjectState.capture`, because the producer is half of what these tests
    have to prove: the V1 gate looked for a file NOTHING could write, and a fixture that wrote the
    evidence by hand would prove the gate reads a store without proving anyone can fill it.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.cli import main as harness
    argv = ["--root", os.path.join(str(repo), "project_memory"), "evidence",
            "--kind", kind, "--result", result, "--summary", summary,
            "--artifact-ref", "staging/TSK-0001/run.log"]
    for ref in related:
        argv += ["--related", ref]
    assert harness(argv) == 0, argv
    # the kernel allocates ids by max-scan, so the newest EVD is the one just written
    return sorted(os.listdir(evidence_dir(repo)))[-1][:-5]


def _merge(repo, item="PR-0001"):
    return {"tool_name": "Bash", "tool_input": {"command": "git merge feat/%s-x" % item},
            "cwd": str(repo)}


def _bash(repo, command):
    return {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(repo)}


def test_gate_git_force_push_blocked(prd_repo):
    """The stderr is asserted, not only the exit code: in a repo with a root item the QA tooth
    returns the same rc 2, so `== 2` alone stayed green with the force-push ban removed
    (mutation-measured)."""
    result = run_hook_process("gate_git.py", _bash(prd_repo, "git push --force origin main"),
                              prd_repo)
    assert result.returncode == 2
    assert "force-push" in result.stderr


@pytest.mark.parametrize("command", [
    # an expansion glued to the word `git` — the `git` still ends a word after expansion
    "git${IFS}push --force origin main",
    "git$IFS push --force origin main",
    # a verb the text does not fix: brace sequence, glob, ANSI-C escape
    "git pus{h..h} --force origin main",
    "git pus[h] --force origin main",
    "git $'\\x70ush' --force origin main",
    # an escaped space keeps the word open, so the `#` after it is data and the `;` still splits
    "echo a\\ # ; git push --force origin main",
    # a wrapper payload in ANSI-C quotes is code one level down — and its backslashes stay the
    # payload's, so the POSIX reading resolves the harmless `x70ush` while the PowerShell reading
    # answers "this verb is not fixed by the text", which is the one the gates decide on
    "bash -c $'git push --force origin main'",
    "bash -c $'git \\x70ush --force origin main'",
    # a payload that is ITSELF a wrapper — the membership test holds twice and the substitution
    # ran once, so every one of these was a real push reaching all eight hooks as ALLOW
    "bash -c \"eval 'git push --force origin main'\"",
    "bash -c \"bash -c 'git push --force origin main'\"",
    "eval \"eval 'git push --force origin main'\"",
    "bash -c \"sh -c 'git push --force origin main'\"",
    # ...and the third way of handing a shell its commands: standard input
    "bash <<< 'git push --force origin main'",
    # cmd's own escape and its delayed expansion. Both really push (measured through the
    # PowerShell tool, whose `cmd /c` reaches cmd; Git Bash rewrites the `/c` into a path)
    'cmd /c "git p^ush --force origin main"',
    'cmd /c "git^ push --force origin main"',
    'cmd /v:on /c "set V=push& git !V! --force origin main"',
])
def test_gate_git_force_push_blocked_however_the_verb_is_spelled(prd_repo, command):
    """The force-push ban is unconditional, so the reader under it has to be fail-closed.

    Every line here force-pushes in a real bash 5.2 and every one of them measured a full ALLOW
    across all eight PreToolUse hooks — the first two against HEAD as well, which makes them
    regressions rather than old holes. Run as a REAL hook process against the shipped gate,
    because the unit tests on `_compat` cannot see a gate that reads the command a second way of
    its own; and the stderr is asserted, because in a repo with a root item the QA tooth returns
    the same rc 2 and `== 2` alone stays green with the ban removed.
    """
    result = run_hook_process("gate_git.py", _bash(prd_repo, command), prd_repo)
    assert result.returncode == 2, command
    assert "force-push" in result.stderr, command


@pytest.mark.parametrize("command", [
    'git commit -m "merge later"',
    'git commit -m "$MSG"',
    "git status",
    "ls $HOME",
    "echo a # ; git push --force origin main",       # a real comment really does end the line
    # a `#` at the start of a word, where the word was opened by a command SEPARATOR — one
    # `git status` and a comment in a real bash, and three gates refused it
    "git status;# git push --force origin main",
    # a backslash is not a word end, so none of these Windows lines names the program `git` —
    # cross-checked in a real bash AND a real PowerShell: not one starts a git process
    "cd C:\\src\\git\\repo",
    "cd C:\\git\\repo",
    'cd "C:\\Program Files\\Git\\bin"',
    "robocopy C:\\git\\a C:\\git\\b /E",
    "Copy-Item C:\\a\\git\\x.txt D:\\b",
    '$env:PATH = "C:\\git\\bin;" + $env:PATH',
    "git\\ push --force origin main",
])
def test_gate_git_stays_out_of_the_way_of_ordinary_commands(prd_repo, command):
    """The other half of the batch above: a gate that blocks when unsure must still be silent when
    it is not. Without this, "fail-closed" is satisfiable by refusing everything — which is how an
    enforcement layer gets switched off by the people it is meant to protect."""
    assert run_hook("gate_git.py", _bash(prd_repo, command), prd_repo) == 0, command


def _shell_gate_names():
    """Every PreToolUse gate the shipped matcher table points at Bash/PowerShell.

    Read out of settings.json rather than typed here: "all eight" is a claim about the SHIPPED
    wiring, and a list in a test would keep asserting eight after the ninth is registered.
    """
    with open(os.path.join(ROOT, "team-kits", "dev-team", "settings", "settings.json"),
              encoding="utf-8") as fh:
        data = json.load(fh)
    names = []
    for group in data.get("hooks", {}).get("PreToolUse", []):
        if not {"Bash", "PowerShell"} & set(str(group.get("matcher") or "").split("|")):
            continue
        for hook in group.get("hooks", []):
            found = re.search(r"_gate\.py[\"']?\s+(\S+\.py)", hook.get("command", ""))
            if found:
                names.append(found.group(1))
    return names


def test_a_refusal_names_an_unreadable_verb_as_its_own_reason(prd_repo):
    """A gate that applies because it could not READ the verb has to say that, in the message.

    `_ends_word` justified reading an undetermined boundary as a possible one with "the gate
    refuses with 'spell the subcommand literally' rather than silently standing down". Measured,
    no gate said anything of the sort: `cd C:\\src\\git\\repo` got "no quality pipeline found
    (scripts/quality.py)" from gate_pipeline, "no QA Evidence in this project" from gate_git and
    "the packaging/deployment decision is unmade" from gate_packaging_decision. Three refusals, and
    nothing in any of them a role could act on — the reader's uncertainty was invisible.

    Asserted as REAL hook processes over every shell gate the settings table registers, and in
    both directions: the note is on every refusal of a line whose verb the text does not fix, and
    on NONE of a line whose verb it does. The negative half is what keeps the note from becoming a
    footer nobody reads.
    """
    unreadable = run_hook_process("gate_git.py", _bash(prd_repo, "git $V --force origin main"),
                                  prd_repo)
    assert unreadable.returncode == 2
    assert "spell the subcommand literally" in unreadable.stderr

    seen_block = False
    for name in _shell_gate_names():
        blocked = run_hook_process(name, _bash(prd_repo, "git $V --force origin main"), prd_repo)
        if blocked.returncode == 2:
            seen_block = True
            assert "spell the subcommand literally" in blocked.stderr, (name, blocked.stderr)
        plain = run_hook_process(name, _bash(prd_repo, "git push origin main"), prd_repo)
        assert "spell the subcommand literally" not in plain.stderr, (name, plain.stderr)
    assert seen_block, "no shell gate refused the unreadable verb — the fixture is not gating"


def test_gate_git_blocks_powershell_tool_too(prd_repo):
    # the gates must not be bypassable via the separate PowerShell tool (a real setup has both)
    payload = {"tool_name": "PowerShell", "tool_input": {"command": "git push --force origin main"},
               "cwd": str(prd_repo)}
    result = run_hook_process("gate_git.py", payload, prd_repo)
    assert result.returncode == 2
    assert "force-push" in result.stderr   # same reason as above: rc 2 alone proves nothing here


def test_gate_git_blocks_a_merge_with_no_qa_evidence_at_all(prd_repo):
    """The base case, and the reason the gate exists: work exists, nothing judges it.

    The message is asserted to name the store the gate actually read, taken from the constant
    rather than typed out — the V1 gate's failure was that it named a store nobody could fill,
    and a refusal that does not say WHERE to put the proof repeats it in a smaller way."""
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ACTIVE_DIRS
    result = run_hook_process("gate_git.py", _merge(prd_repo), prd_repo)
    assert result.returncode == 2
    assert "no QA Evidence" in result.stderr
    assert "project_memory/%s" % ACTIVE_DIRS["EVD"] in result.stderr


def test_gate_git_opens_once_the_evidence_a_role_can_produce_exists(prd_repo):
    """...and the other half: the SAME repo merges once QA has recorded a passing Evidence.

    Blocked-then-allowed in one test on purpose — separately, either half could pass while the
    gate was stuck open or stuck shut."""
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 2
    capture_evidence(prd_repo, kind="test", result="pass")
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 0


def test_gate_git_evidence_for_another_item_does_not_open_this_merge(prd_repo):
    """A passing verdict about PR-0002 says nothing about PR-0001 — binding is per item."""
    capture_root_item(prd_repo, dict(PR_FIELDS, title="Second"))   # PR-0002
    capture_evidence(prd_repo, related=("PR-0002",))
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 2


def test_gate_git_an_audit_evidence_does_not_open_a_delivery_merge(prd_repo):
    """`kind: audit` judges the PROJECT (II.10a), so the auditor's weekly run is not a QA pass."""
    capture_evidence(prd_repo, kind="audit", result="pass")
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 2


def test_gate_git_does_not_apply_before_the_project_has_a_root_item(tmp_path):
    """A repo that has a state directory but no PR/RQ yet merges and pushes freely.

    This is the tooth that keeps the gate from being what it was before this round: with it gone,
    a QA rule fires in a project that has no work to judge and blocks the very setup it exists to
    protect (the V1 shape of this hook blocked EVERY merge and push for exactly that reason).
    The counter-assertion is the point of the last two lines — the same repo, one captured item
    later, is blocked, so "allowed" here cannot be the hook silently exiting on something else.
    """
    os.makedirs(os.path.join(str(tmp_path), "project_memory"), exist_ok=True)
    assert run_hook("gate_git.py", _merge(tmp_path), tmp_path) == 0
    assert run_hook("gate_git.py", _bash(tmp_path, "git push origin main"), tmp_path) == 0
    capture_root_item(tmp_path)
    assert run_hook("gate_git.py", _merge(tmp_path), tmp_path) == 2


@pytest.mark.parametrize("verdict", ["PASS", "inconclusive", None])
def test_gate_git_treats_a_verdict_it_cannot_read_as_no_pass(prd_repo, verdict):
    """`result` is the one field a gate DECIDES on, so anything but `pass` must close the merge.

    Written by hand, because the kernel refuses these three at capture — which is the point: the
    only way such a file exists is that someone bypassed the kernel, and that is precisely when a
    gate must not read an unrecognised value as consent. `PASS` is the plausible one (a human
    spelling), `inconclusive` the vocabulary the kernel deliberately does not have, and a missing
    field the shape a truncated write leaves behind.

    A LEGAL, OLDER pass of the same kind sits next to it, and that neighbour is what makes the
    test measure its own sentence. With the unreadable record alone, "read as no pass" and
    "silently skipped" both end in rc 2 — once for "not a pass", once for "no QA Evidence" — so
    the assertion held for the implementation the docstring warns about (measured: adding a skip
    of unknown `result` values to `report._delivery_evidence` left this test and 123 kernel tests
    green). With the older pass present, skipping makes it the current verdict and the merge
    opens, which is why the refusal REASON is asserted and not just the exit code.
    """
    import yaml
    capture_evidence(prd_repo, kind="test", result="pass", related=("PR-0001",))
    evidence = {"id": "EVD-0002", "kind": "test", "related": ["PR-0001"],
                "summary": "hand-written", "artifact_refs": ["staging/TSK-0001/run.log"],
                # dated after the captured pass on purpose: the newest record of a kind is that
                # kind's verdict, so this is the one the gate must be deciding on
                "created": "2999-01-01T00:00:00"}
    if verdict is not None:
        evidence["result"] = verdict
    write(os.path.join(evidence_dir(prd_repo), "EVD-0002.yaml"), yaml.safe_dump(evidence))
    result = run_hook_process("gate_git.py", _merge(prd_repo), prd_repo)
    assert result.returncode == 2
    assert "not a pass" in result.stderr, result.stderr


# ---------------- gate_memory_complete ----------------
MERGE = {"tool_name": "Bash", "tool_input": {"command": "git merge feat/PR-0001-x"}}


def _merge_payload(repo):
    return dict(MERGE, cwd=str(repo))


def test_memory_complete_is_silent_before_the_first_root_item(tmp_path):
    """The II.11/2 lockstep regression: the trigger is now `product/active/PR-*.yaml`. A repo that
    has not captured its first requirement is still being SET UP, and a merge gate firing there
    blocks the setup it exists to protect.

    The fixture is the SCAFFOLD, not an empty directory: a fresh repo carries the two shipped
    templates the gate has its own teeth for, and only that state can tell a working trigger from
    a dead one. Against an empty `project_memory/` the gate has nothing to find either way, so the
    test held even with `has_root_item` forced to True — it could not see the regression it
    claims. With the templates present, killing the trigger makes it rc=2 on the masterplan."""
    plan = tmp_path / "project_memory" / "product" / "masterplan.md"
    write(str(plan), "# Masterplan — <project name>\n")
    write(str(tmp_path / "project_memory" / "project_config.yaml"),
          'project:\n  name: ""\n  stacks: [TODO]\n')
    assert run_hook("gate_memory_complete.py", _merge_payload(tmp_path), tmp_path) == 0


def test_memory_complete_fires_once_a_typed_root_item_exists(tmp_path):
    """...and the other half of the same regression: the gate must actually WAKE UP for the typed
    item. An incomplete PR (no acceptance criteria, no goal) is what the validator calls an error."""
    capture_root_item(tmp_path, {"title": "x", "class": "normal", "problem": "p", "goal": "g",
                                 "acceptance_criteria": [], "invariants": [], "out_of_scope": [],
                                 "priority": "high"})
    os.remove(os.path.join(str(tmp_path), "project_memory", "product", "active", "PR-0001.yaml"))
    write(str(tmp_path / "project_memory" / "product" / "active" / "PR-0001.yaml"),
          "id: PR-0001\nstatus: DRAFT\ntitle: x\n")  # missing most required fields
    result = run_hook_process("gate_memory_complete.py", _merge_payload(tmp_path), tmp_path)
    assert result.returncode == 2
    assert "PR-0001" in result.stderr


def test_memory_complete_allows_a_state_the_validator_accepts(prd_repo):
    assert run_hook("gate_memory_complete.py", _merge_payload(prd_repo), prd_repo) == 0


def test_memory_complete_reports_the_validator_verdict_not_its_own(prd_repo):
    """The completeness question has ONE answer (`kernel/report.validate_state`); this gate relays
    it. Asserted by making the validator's own rule fire — a duplicate id, which no template scan
    could ever have seen."""
    for item_id in ("PR-0002",):
        write(str(prd_repo / "project_memory" / "product" / "active" / (item_id + ".yaml")),
              open(str(prd_repo / "project_memory" / "product" / "active" / "PR-0001.yaml"),
                   encoding="utf-8").read())
    result = run_hook_process("gate_memory_complete.py", _merge_payload(prd_repo), prd_repo)
    assert result.returncode == 2
    assert "duplicate id" in result.stderr


def test_freezing_a_second_wireframe_revision_does_not_block_every_merge(tmp_path):
    """Disposition row 6.5, measured where it actually hurt: at the merge.

    A second `freeze_wireframe` is the normal course of design work. It wrote
    `WFR-0001.r02.yaml` beside `WFR-0001.r01.yaml`, the validator called that `WFR-0001 duplicate
    id`, and THIS gate blocks on validator ERRORS -- so the project's every merge and every push
    was refused, with the only remedy being to delete a frozen, immutable artefact by hand. Both
    ends are asserted: the freeze really happened (two companions on disk), and the merge line
    really passes the shipped hook process.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import approvals as kernel_approvals
    from kernel import staging as kernel_staging
    from kernel.state import ProjectState

    item = capture_root_item(tmp_path, status=None)
    state = ProjectState(os.path.join(str(tmp_path), "project_memory"))
    conftest.mint_via_hook(
        state, kernel_approvals.create_pending_request(state, "scope", item["id"]))
    apr_ref = state.read_item(item["id"])["approval_ref"]
    for body in ("first cut", "second cut"):
        key = "%s-%s" % (item["id"], body.split()[0])
        write(os.path.join(kernel_staging.staging_dir(state, key), "WFR-0001.drawio.svg"),
              '<svg xmlns="http://www.w3.org/2000/svg"><g>%s</g></svg>' % body)
        kernel_staging.freeze_wireframe(state, key, "WFR-0001", apr_ref, [item["id"]], "Checkout")
    frozen = sorted(n for n in os.listdir(state.active_dir("WFR")) if n.endswith(".yaml"))
    assert frozen == ["WFR-0001.r01.yaml", "WFR-0001.r02.yaml"], frozen

    result = run_hook_process("gate_memory_complete.py", _merge_payload(tmp_path), tmp_path)
    assert result.returncode == 0, result.stderr
    assert "duplicate id" not in result.stderr


# ---------------- quality.py ----------------
BROWSER_CHECKS = os.path.join(ROOT, "team-kits", "dev-team", "templates", "repo", "scripts",
                              "kit_browser_checks.py")


def run_quality_proc(repo, *args, extra_env=None):
    os.makedirs(os.path.join(repo, "scripts"), exist_ok=True)
    import shutil
    shutil.copy(QUALITY, os.path.join(repo, "scripts", "quality.py"))
    shutil.copy(KIT_CHECKS, os.path.join(repo, "scripts", "kit_checks.py"))  # kit-owned check lib
    shutil.copy(BROWSER_CHECKS, os.path.join(repo, "scripts", "kit_browser_checks.py"))
    return subprocess.run([sys.executable, os.path.join(repo, "scripts", "quality.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          cwd=repo, timeout=120, env=dict(os.environ, **(extra_env or {})))


def run_quality(repo):
    return run_quality_proc(repo).returncode


def test_quality_empty_green(tmp_path):
    assert run_quality(str(tmp_path)) == 0


def test_quality_unknown_stack_red(tmp_path):
    write(str(tmp_path / "project_memory" / "project_config.yaml"), "project:\n  stacks: [cobol]\n")
    assert run_quality(str(tmp_path)) == 1


def test_quality_declared_node_no_frontend_red_not_crash(tmp_path):
    write(str(tmp_path / "project_memory" / "project_config.yaml"), "project:\n  stacks: [node]\n")
    assert run_quality(str(tmp_path)) == 1  # clean FAIL, not a crash


def test_quality_undeclared_stacks_with_code_red(tmp_path):
    # code present but stacks still [TODO] -> must FAIL (force the architect to declare; no silent auto-detect)
    write(str(tmp_path / "src" / "m.py"), "def f():\n    return 1\n")
    write(str(tmp_path / "project_memory" / "project_config.yaml"), "project:\n  stacks: [TODO]\n")
    assert run_quality(str(tmp_path)) == 1


def test_quality_declared_embedded_no_platformio_red(tmp_path):
    write(str(tmp_path / "project_memory" / "project_config.yaml"), "project:\n  stacks: [embedded]\n")
    assert run_quality(str(tmp_path)) == 1


def test_quality_only_flag_partial_run(tmp_path):
    # fast-iteration flag (upstreamed): loud partial notice, never merge evidence
    r = run_quality_proc(str(tmp_path), "--only", "cobol")
    assert r.returncode == 2 and "unknown stack" in r.stdout
    r = run_quality_proc(str(tmp_path), "--only")
    assert r.returncode == 2
    r = run_quality_proc(str(tmp_path), "--only", "node")  # no frontend -> clean FAIL, loudly partial
    assert r.returncode == 1 and "PARTIAL RUN" in r.stdout


def _quality_mod(path=None):
    import importlib.util
    p = path or QUALITY
    spec = importlib.util.spec_from_file_location("quality_under_test_%d" % abs(hash(p)), p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_quality_tool_cmd_module_fallback(monkeypatch):
    # pip on Windows drops console-script shims outside PATH while the module imports fine —
    # "not installed" would be a lie (upstreamed from a live project)
    mod = _quality_mod()
    monkeypatch.setattr(mod, "have", lambda t: False)
    assert mod.tool_cmd("ruff") == [sys.executable, "-m", "ruff"]
    assert mod.tool_cmd("gitleaks") is None  # not a Python console-script — honest absence


def test_quality_python_targets_from_governed_source_areas(tmp_path):
    os.makedirs(str(tmp_path / "scripts"))
    shutil.copy(QUALITY, str(tmp_path / "scripts" / "quality.py"))
    shutil.copy(KIT_CHECKS, str(tmp_path / "scripts" / "kit_checks.py"))
    os.makedirs(str(tmp_path / "src"))
    os.makedirs(str(tmp_path / "compounder"))
    capture_invariant(tmp_path, "compounder/", text="the whole codebase lives here")
    capture_invariant(tmp_path, "..", text="a scope that would walk out of the repo")
    capture_invariant(tmp_path, "python", text="not an area at all — no such directory")
    mod = _quality_mod(str(tmp_path / "scripts" / "quality.py"))
    targets = mod._python_targets()
    assert "compounder" in targets and "src" in targets
    assert ".." not in targets  # dot-only names never become lint targets (audit class)
    assert "python" not in targets  # a scope that names no directory names no area


def test_quality_electron_env_stripped():
    mod = _quality_mod()
    os.environ["ELECTRON_RUN_AS_NODE"] = "1"
    try:
        assert "ELECTRON_RUN_AS_NODE" not in mod._clean_node_env()
    finally:
        os.environ.pop("ELECTRON_RUN_AS_NODE", None)


# ---------------- guard_yaml_valid (write-time YAML validity, the synaipse invalid-decisions saga) ----------------
def _yaml_payload(repo, fname):
    return {"tool_name": "Write",
            "tool_input": {"file_path": str(repo / "project_memory" / fname)}, "cwd": str(repo)}


DECISION_ITEM = os.path.join("decisions", "active", "DEC-0001.yaml").replace(os.sep, "/")


def test_yaml_valid_blocks_parse_error(tmp_path):
    pytest.importorskip("yaml")
    write(str(tmp_path / "project_memory" / DECISION_ITEM),
          "title: STRIDE: threat: model\n")  # unquoted colons -> invalid
    assert run_hook("guard_yaml_valid.py", _yaml_payload(tmp_path, DECISION_ITEM), tmp_path) == 2


def test_yaml_valid_uses_codex_posttool_block_decision(tmp_path):
    pytest.importorskip("yaml")
    write(str(tmp_path / "project_memory" / DECISION_ITEM),
          "title: STRIDE: threat: model\n")
    result = run_hook_process(
        "guard_yaml_valid.py", _yaml_payload(tmp_path, DECISION_ITEM), tmp_path,
        extra_env={"TEAM_KIT_PROVIDER": "codex"})
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["decision"] == "block" and "INVALID YAML" in output["reason"]
    assert "continue" not in output


def test_yaml_valid_blocks_duplicate_key(tmp_path):
    pytest.importorskip("yaml")
    architecture_item = os.path.join("architecture", "active", "ARC-0001.yaml").replace(os.sep, "/")
    write(str(tmp_path / "project_memory" / architecture_item),
          "components:\n  api:\n    responsibility: a\n  api:\n    responsibility: b\n")
    assert run_hook("guard_yaml_valid.py", _yaml_payload(tmp_path, architecture_item), tmp_path) == 2


def test_yaml_valid_allows_good_yaml(tmp_path):
    pytest.importorskip("yaml")
    write(str(tmp_path / "project_memory" / DECISION_ITEM),
          'title: "STRIDE: threat model"\ncontext: |\n  prose: with colons is fine\n')
    assert run_hook("guard_yaml_valid.py", _yaml_payload(tmp_path, DECISION_ITEM), tmp_path) == 0


def test_yaml_valid_ignores_non_project_memory(tmp_path):
    write(str(tmp_path / "src" / "broken.yaml"), "a: b: c: [\n")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "src" / "broken.yaml")},
               "cwd": str(tmp_path)}
    assert run_hook("guard_yaml_valid.py", payload, tmp_path) == 0


# ---------------- guard_guidelines: which INV governs a write ----------------
def _write_code(repo, rel):
    return {"tool_name": "Write", "tool_input": {"file_path": str(repo / rel)}, "cwd": str(repo)}


def test_guidelines_compound_scope_satisfies_js(prd_repo):
    # the synaipse case: the architect named the language `html_vanilla_js` — token "js" must match
    capture_invariant(prd_repo, "html_vanilla_js", text="no inline handlers")
    assert run_hook("guard_guidelines.py", _write_code(prd_repo, "src/app.js"), prd_repo) == 0


def test_guidelines_still_blocks_js_when_no_invariant_governs_it(prd_repo):
    capture_invariant(prd_repo, "python", text="type hints on every public function")
    assert run_hook("guard_guidelines.py", _write_code(prd_repo, "src/app.js"), prd_repo) == 2


def test_guidelines_are_satisfied_by_an_invariant_over_the_area(prd_repo):
    """An invariant that governs `frontend/` governs the code IN it — a scope reads as a path too.

    V1 could only answer the language question, because its source was a `languages:` map. An
    invariant states what it governs, and "everything under frontend/" is as legitimate an answer
    as "TypeScript" — so the guard asks whether the scope covers the file, by either reading.
    """
    capture_invariant(prd_repo, "frontend/", text="no direct DOM access outside components")
    assert run_hook("guard_guidelines.py", _write_code(prd_repo, "frontend/app.ts"), prd_repo) == 0
    # ...and it does NOT govern the neighbouring backend area
    assert run_hook("guard_guidelines.py", _write_code(prd_repo, "backend/app.ts"), prd_repo) == 2


@pytest.mark.parametrize("scope,rel,expected", [
    # a PATH scope is an AREA and nothing else — every one of these carries a segment that is
    # also a language alias, and every one of them used to disarm that language repo-wide
    ("services/node-api", "src/x.js", 2),
    ("go/pkg", "src/main.go", 2),
    ("lib/c-bindings", "src/main.c", 2),
    ("docs/rust-notes", "src/m.rs", 2),
    # ...while the area reading itself keeps working, in both directions
    ("src/backend", "src/backend/a.py", 0),
    ("src/backend", "src/other.py", 2),
    # ...and a BARE name is still read as the language it names
    ("go", "src/main.go", 0),
    ("python", "src/a.py", 0),
    ("ui/components", "src/a.ts", 2),
])
def test_a_path_scope_is_an_area_and_not_a_list_of_languages(tmp_path, scope, rel, expected):
    """The collision the first cut of the INV migration opened, measured per shape.

    `_governs` tokenised every scope on non-letters BEFORE asking whether it was a path, so any
    segment equal to a `LANG` alias voted for that language across the whole repo — `go/pkg` for
    `.go`, `lib/c-bindings` for `.c`, `services/node-api` for `.js`. The guard had just been
    brought back from being inert; this made it inert again for those languages.

    Run as real hook processes, because the exit code is the only thing a session sees.
    """
    capture_root_item(tmp_path)
    capture_invariant(tmp_path, scope, text="the rule this invariant states")
    assert run_hook("guard_guidelines.py", _write_code(tmp_path, rel), tmp_path) == expected


def test_guidelines_pass_while_the_project_keeps_no_invariants_at_all(prd_repo):
    """The V1 "no guidelines file" case, kept: a project with no invariants has no regime yet.

    Turning this into a block would stop the first line of code in every new project, which spec
    II.4 does not ask for (`guard_guidelines` is not in its fail-closed list) — so the honest form
    is the constitution saying the rule binds as policy there, which it now does.
    """
    assert run_hook("guard_guidelines.py", _write_code(prd_repo, "src/app.js"), prd_repo) == 0


def test_yaml_valid_survives_recursive_alias(tmp_path):
    # anchors/aliases make the node graph cyclic — the dup-key walker must terminate (visited set)
    pytest.importorskip("yaml")
    write(str(tmp_path / "project_memory" / DECISION_ITEM), "a: &x\n  b: ok\nc: *x\n")
    assert run_hook("guard_yaml_valid.py", _yaml_payload(tmp_path, DECISION_ITEM), tmp_path) == 0


def test_memory_complete_blocks_template_masterplan(prd_repo):
    # the masterplan moved to product/ (spec II.2) — prose, so no schema sees it; this gate does
    write(str(prd_repo / "project_memory" / "product" / "masterplan.md"),
          "# Masterplan — <project name>\n\n> One-line essence of the idea.\n")
    write(str(prd_repo / "project_memory" / "project_config.yaml"),
          'project:\n  name: "X"\n  stacks: [python]\n')
    assert run_hook("gate_memory_complete.py", _merge_payload(prd_repo), prd_repo) == 2


def test_memory_complete_allows_filled_masterplan(prd_repo):
    write(str(prd_repo / "project_memory" / "product" / "masterplan.md"),
          "# Masterplan — Chatly\n\n> A local chat platform.\n\n## 1. Leitidee\nReal prose here.\n")
    write(str(prd_repo / "project_memory" / "project_config.yaml"),
          'project:\n  name: "X"\n  stacks: [python]\n')
    assert run_hook("gate_memory_complete.py", _merge_payload(prd_repo), prd_repo) == 0


# ---------------- quality.py: project_memory yaml-lint backstop ----------------
def test_quality_red_on_invalid_project_memory_yaml(tmp_path):
    pytest.importorskip("yaml")
    write(str(tmp_path / "project_memory" / DECISION_ITEM), "title: a: b: c\n")
    assert run_quality(str(tmp_path)) == 1


# ---------------- kit versioning: session_status flags updates; validate enforces bumps ----------------
def _mk_kit_repo(tmp_path, local_version, staged_version):
    home = tmp_path / "home"
    write(str(home / ".claude" / "team-kits" / "dev-team" / "VERSION"), staged_version)
    repo = tmp_path / "repo"
    write(str(repo / "CLAUDE.md"), "<!-- agents-and-skills:team-kit dev-team -->\n# x\n")
    if local_version is not None:
        write(str(repo / ".claude" / "kit_version"), local_version)
    return home, repo


def _run_session_status(home, repo):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo), HOME=str(home), USERPROFILE=str(home))
    p = subprocess.run([sys.executable, os.path.join(HOOKS, "session_status.py")],
                       input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True,
                       env=env, timeout=60)
    return p.stdout


def test_session_status_flags_kit_update(tmp_path):
    home, repo = _mk_kit_repo(tmp_path, "version: 2026.07.01-1\ncontent: aaa\n",
                              "version: 2026.07.03-1\ncontent: bbb\n")
    out = _run_session_status(home, repo)
    assert "KIT UPDATE AVAILABLE" in out and "2026.07.03-1" in out


def test_session_status_quiet_when_current(tmp_path):
    v = "version: 2026.07.03-1\ncontent: same\n"
    home, repo = _mk_kit_repo(tmp_path, v, v)
    out = _run_session_status(home, repo)
    assert "KIT UPDATE AVAILABLE" not in out


def test_validate_catches_unbumped_kit_change():
    # append a comment to a kit file -> hash drifts -> validate must FAIL mentioning the bump tool
    p = os.path.join(ROOT, "team-kits", "dev-team", "hooks", "_audit.py")
    orig = open(p, encoding="utf-8").read()
    try:
        with open(p, "a", encoding="utf-8", newline="") as fh:
            fh.write("\n# temp-test-drift\n")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "validate.py")],
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 1 and "VERSION not bumped" in r.stdout
    finally:
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(orig)


def test_preset_parser_changes_every_shared_kit_hash(tmp_path):
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from bump_kit_version import kit_hash

    team_kits = tmp_path / "team-kits"
    kit = team_kits / "demo-team"
    write(str(kit / "agents" / "project-manager.md"), "# lead\n")
    parser = team_kits / "preset_config.py"
    write(str(parser), "# parser version one\n")
    before = kit_hash(str(kit))
    parser.write_text("# parser version two\n", encoding="utf-8")
    assert kit_hash(str(kit)) != before


# ---------------- gate_test_coverage + guard_guidelines for C/C++ (embedded) ----------------
def test_coverage_blocks_cpp_without_tests(prd_repo):
    write(str(prd_repo / "src" / "main.cpp"), "int main(){return 0;}\n")
    payload = {"tool_name": "Bash", "tool_input": {"command": "git merge feat/PRD-0001"}, "cwd": str(prd_repo)}
    assert run_hook("gate_test_coverage.py", payload, prd_repo) == 2


def test_guidelines_block_cpp_when_no_invariant_governs_it(prd_repo):
    capture_invariant(prd_repo, "python", text="type hints on every public function")
    assert run_hook("guard_guidelines.py", _write_code(prd_repo, "src/main.cpp"), prd_repo) == 2


# ---------------- gate_memory_complete: project_config name/stacks loophole ----------------
def test_memory_complete_blocks_unnamed_config(prd_repo):
    # real scalars (preset/repo_mode) but name:"" + stacks:[TODO] -> must be caught
    write(str(prd_repo / "project_memory" / "project_config.yaml"),
          'project:\n  name: ""\n  preset: solo\n  repo_mode: greenfield\n  stacks: [TODO]\n')
    payload = {"tool_name": "Bash", "tool_input": {"command": "git merge feat/PRD-0001-x"}, "cwd": str(prd_repo)}
    assert run_hook("gate_memory_complete.py", payload, prd_repo) == 2


def test_memory_complete_allows_named_declared_config(prd_repo):
    write(str(prd_repo / "project_memory" / "project_config.yaml"),
          'project:\n  name: "TCG Tracker"\n  preset: team\n  repo_mode: greenfield\n  stacks: [python, typescript]\n')
    payload = {"tool_name": "Bash", "tool_input": {"command": "git merge feat/PRD-0001-x"}, "cwd": str(prd_repo)}
    assert run_hook("gate_memory_complete.py", payload, prd_repo) == 0


# ---------------- init_project_memory: deterministic, copy-if-absent ----------------
def test_init_project_memory_copies_and_never_clobbers(tmp_path):
    home = tmp_path / "home"
    tpl = home / ".claude" / "team-kits" / "demo-team" / "templates" / "project_memory"
    write(str(tpl / "a.yaml"), "x: 1\n")
    write(str(tpl / "sub" / "b.yaml"), "y: 2\n")
    repo = tmp_path / "repo"
    repo.mkdir()

    if os.name == "nt":
        script = os.path.join(ROOT, "team-kits", "init_project_memory.ps1")
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, "-Team", "demo-team"]
        env = dict(os.environ, USERPROFILE=str(home))
    else:
        if not shutil.which("bash"):
            pytest.skip("bash not available")
        script = os.path.join(ROOT, "team-kits", "init_project_memory.sh")
        cmd = ["bash", script, "demo-team"]
        env = dict(os.environ, HOME=str(home))

    r = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    a = repo / "project_memory" / "a.yaml"
    b = repo / "project_memory" / "sub" / "b.yaml"
    assert a.is_file() and b.is_file()

    # copy-if-absent: a local edit must survive a re-run (idempotent, never clobbers)
    a.write_text("EDITED\n", encoding="utf-8")
    r2 = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True, env=env, timeout=60)
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert a.read_text(encoding="utf-8") == "EDITED\n"


def _init_project_memory_symlink_state(tmp_path):
    home = tmp_path / "home"
    template = home / ".claude" / "team-kits" / "demo-team" / "templates" / "project_memory"
    write(str(template / "new.yaml"), "new: template\n")
    repo = tmp_path / "repo"
    repo.mkdir()
    external = tmp_path / "external-memory"
    sentinel = external / "sentinel.txt"
    write(str(sentinel), "external memory sentinel\n")
    return home, repo, external, sentinel


def test_init_project_memory_ps1_rejects_external_symlink_before_mutation(tmp_path):
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("PowerShell init integration runs on Windows")
    home, repo, external, sentinel = _init_project_memory_symlink_state(tmp_path)
    try:
        os.symlink(external, repo / "project_memory", target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip("directory symlinks are not permitted in this test environment: %s" % exc)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(ROOT, "team-kits", "init_project_memory.ps1"),
         "-Team", "demo-team"],
        cwd=str(repo), capture_output=True, text=True, timeout=60,
        env=dict(os.environ, USERPROFILE=str(home)))
    output = (result.stdout + result.stderr).lower()
    assert result.returncode != 0 and ("symlink" in output or "reparse" in output)
    assert sentinel.read_text(encoding="utf-8") == "external memory sentinel\n"
    assert not (external / "new.yaml").exists()
    assert (repo / "project_memory").is_symlink()
    assert not (repo / ".claude" / "kit_update_pending.memory").exists()


def test_init_project_memory_sh_rejects_external_symlink_before_mutation(tmp_path):
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX init integration runs on Unix CI")
    home, repo, external, sentinel = _init_project_memory_symlink_state(tmp_path)
    os.symlink(external, repo / "project_memory", target_is_directory=True)
    result = subprocess.run(
        ["bash", os.path.join(ROOT, "team-kits", "init_project_memory.sh"), "demo-team"],
        cwd=str(repo), capture_output=True, text=True, timeout=60,
        env=dict(os.environ, HOME=str(home)))
    output = (result.stdout + result.stderr).lower()
    assert result.returncode != 0 and "symlink" in output
    assert sentinel.read_text(encoding="utf-8") == "external memory sentinel\n"
    assert not (external / "new.yaml").exists()
    assert (repo / "project_memory").is_symlink()
    assert not (repo / ".claude" / "kit_update_pending.memory").exists()


# ---------------- gate_packaging_decision (the generalised "Docker was forgotten" guard) ----------------
def _architecture_item(repo, body):
    write(str(repo / "project_memory" / "architecture" / "active" / "ARC-0001.yaml"), body)


def test_packaging_gate_blocks_todo(prd_repo):
    _architecture_item(prd_repo, "id: ARC-0001\ntitle: system\npackaging:\n  method: TODO\n")
    assert run_hook("gate_packaging_decision.py", _merge_payload(prd_repo), prd_repo) == 2


def test_packaging_gate_blocks_when_no_architecture_item_exists(prd_repo):
    """V1 shipped an `architecture.yaml` template with `method: TODO` in every project, so 'no
    architecture' could not occur and the gate always asked the question. No template ships any
    more — reading an absent architecture item as an exemption would silently retire the gate."""
    result = run_hook_process("gate_packaging_decision.py", _merge_payload(prd_repo), prd_repo)
    assert result.returncode == 2
    assert "no architecture item yet" in result.stderr


def test_packaging_gate_allows_decided(prd_repo):
    _architecture_item(prd_repo,
                       "id: ARC-0001\ntitle: system\npackaging:\n  method: static-binary\n"
                       "  targets: [linux, windows]\n")
    assert run_hook("gate_packaging_decision.py", _merge_payload(prd_repo), prd_repo) == 0


def test_packaging_gate_allows_explicit_none(prd_repo):
    # "none (library only)" is a conscious decision and must pass — only TODO/absent blocks
    _architecture_item(prd_repo, "id: ARC-0001\ntitle: system\npackaging:\n  method: none(library)\n")
    assert run_hook("gate_packaging_decision.py", _merge_payload(prd_repo), prd_repo) == 0


def test_packaging_gate_reads_any_active_architecture_item(prd_repo):
    """The decision lives on ONE lean item; the directory also holds diagram companions. A gate
    that only looked at the first file would block a project that decided in the second."""
    write(str(prd_repo / "project_memory" / "architecture" / "active" / "ARC-0001.yaml"),
          "id: ARC-0001\ntitle: context diagram\ndiagram_hash: deadbeef\n")
    write(str(prd_repo / "project_memory" / "architecture" / "active" / "ARC-0002.yaml"),
          "id: ARC-0002\ntitle: system\npackaging:\n  method: docker\n")
    assert run_hook("gate_packaging_decision.py", _merge_payload(prd_repo), prd_repo) == 0


def test_packaging_gate_clears_on_a_kernel_written_architecture_item(prd_repo):
    """The field has to be REACHABLE, not merely readable.

    Every test above writes ARC-0001 by hand, so all of them passed while nothing could produce
    the field at all: `capture` refuses the type and the companion schema is strict, so the only
    writer — `freeze_architecture` — dropped `packaging` as an unknown field. A dev project was
    therefore blocked at its first merge for good. This test walks the one path a project has
    (stage the diagram, let the kernel freeze it) and goes red the moment that path stops
    carrying the decision.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import staging
    from kernel.state import ProjectState
    state = ProjectState(os.path.join(str(prd_repo), "project_memory"))
    write(os.path.join(state.root, "staging", "PR-0001", "ARC-0001.drawio.svg"),
          '<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>\n')
    staging.freeze_architecture(state, "PR-0001", "ARC-0001", title="system",
                                scope="whole system", derives_from=["PR-0001"],
                                packaging={"method": "docker"})
    assert run_hook("gate_packaging_decision.py", _merge_payload(prd_repo), prd_repo) == 0


# ---------------- dashboard generator: typed items + kernel index -> generated/dashboard.html ----------------
DASHBOARD = os.path.join(ROOT, "team-kits", "dev-team", "templates", "repo", "scripts",
                         "generate_dashboard.py")


def _dashboard_repo(tmp_path):
    """A repo the generator can run in: hook bridge, scripts/, project_memory, and typed items.

    The generator resolves the kernel through `.claude/hooks/_kernel.py` (the one place that
    knows where the kernel lives), so the bridge and its helpers have to be there; the kernel
    package itself comes from HARNESS_KERNEL_PATH, as for every other kernel-backed test.
    kit_checks.py comes along because the vitals panel takes its scan areas from there.
    """
    src = os.path.dirname(DASHBOARD)
    hooks = tmp_path / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    for helper in ("_kernel.py", "_root.py", "_audit.py", "_compat.py"):
        shutil.copy(os.path.join(HOOKS, helper), str(hooks / helper))
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("generate_dashboard.py", "progress.dashboard.template.html", "kit_checks.py"):
        shutil.copy(os.path.join(src, name), str(scripts / name))
    pm = tmp_path / "project_memory"
    pm.mkdir()
    return pm


def _generate_index(pm):
    """The real index, written by the kernel itself -- a hand-written fixture would let the
    generator agree with a shape nothing produces."""
    index = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, sys.argv[1]);"
         "from kernel.state import ProjectState; ProjectState(sys.argv[2]).generate_index()",
         os.path.join(ROOT, "team-kits"), str(pm)],
        capture_output=True, text=True, timeout=60)
    assert index.returncode == 0, index.stdout + index.stderr


def _run_dashboard(tmp_path, pm):
    env = dict(os.environ, HARNESS_KERNEL_PATH=os.path.join(ROOT, "team-kits"))
    _generate_index(pm)
    return subprocess.run([sys.executable, str(tmp_path / "scripts" / "generate_dashboard.py")],
                          capture_output=True, text=True, cwd=str(tmp_path), env=env, timeout=60)


def _dashboard_data(pm):
    html = (pm / "generated" / "dashboard.html").read_text(encoding="utf-8")
    return html, json.loads(re.search(
        r'<script type="application/json" id="dashboard-data">(.*?)</script>',
        html, re.DOTALL).group(1))


def test_dashboard_renders_typed_items(tmp_path):
    pytest.importorskip("yaml")
    pm = _dashboard_repo(tmp_path)
    write(str(pm / "product" / "active" / "PR-0001.yaml"),
          "id: PR-0001\ntitle: login\nstatus: APPROVED\nrevision: 2\n")
    write(str(pm / "tasks" / "active" / "TSK-0001.yaml"),
          "id: TSK-0001\ntitle: build it\nstatus: READY\nproduct_requirement: PR-0001\n")
    write(str(pm / "bugs" / "active" / "BUG-0001.yaml"),
          "id: BUG-0001\ntitle: crash\nstatus: OPEN\nblocked_by: TSK-0001\n")
    write(str(pm / "archive" / "PR" / "2025" / "PR-0009.yaml"), "id: PR-0009\nstatus: ACCEPTED\n")
    r = _run_dashboard(tmp_path, pm)
    assert r.returncode == 0, r.stdout + r.stderr
    html, data = _dashboard_data(pm)
    rendered = {it["id"]: it for view in data["views"] for it in view["items"]}
    assert set(rendered) == {"PR-0001", "TSK-0001", "BUG-0001"}
    # the next step is DERIVED from the automaton chain, not from a table of advice
    assert rendered["PR-0001"]["next"] == "IN_DELIVERY"
    assert rendered["TSK-0001"]["next"] == "LEASED"
    # the blocker flag survives, and a relation is "a field whose value parses as an item id"
    assert rendered["BUG-0001"]["blocked_by"] == "TSK-0001"
    assert rendered["TSK-0001"]["relations"] == ["PR-0001"]
    # archive is COUNTED, never embedded (spec II.7)
    assert "PR-0009" not in html
    assert data["archive"] == {"total": 1, "by_type": {"PR": {"2025": 1}}}


def _dashboard_without_index(tmp_path):
    env = dict(os.environ, HARNESS_KERNEL_PATH=os.path.join(ROOT, "team-kits"))
    return subprocess.run([sys.executable, str(tmp_path / "scripts" / "generate_dashboard.py")],
                          capture_output=True, text=True, cwd=str(tmp_path), env=env, timeout=60)


def test_dashboard_refuses_without_an_index(tmp_path):
    """Items on disk but no index: an un-generated index must not render as an empty, reassuring
    dashboard. The item is what separates this from the greenfield case below — the two used to be
    the same branch, which made the "non-skippable" command exit 1 in every brand-new project."""
    pytest.importorskip("yaml")
    pm = _dashboard_repo(tmp_path)
    write(str(pm / "product" / "active" / "PR-0001.yaml"), "id: PR-0001\nstatus: DRAFT\n")
    r = _dashboard_without_index(tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "generate-index" in r.stderr
    assert not (pm / "generated" / "dashboard.html").exists()


def test_dashboard_on_a_greenfield_project_renders_and_says_nothing_is_captured(tmp_path):
    """A project that has captured nothing has no index BY CONSTRUCTION (the kernel writes it on a
    state write, and the scaffold writes no items), while the constitution calls the generator
    non-skippable from day 1. So here — and only here — "no index" and "nothing captured" are the
    same truth, and the honest answer is a rendered page that SAYS so. The predicate is the bridge's
    `state_is_empty`, not a guess: one item flips it (the test above)."""
    pytest.importorskip("yaml")
    pm = _dashboard_repo(tmp_path)
    r = _dashboard_without_index(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "No items captured yet" in r.stdout
    html, data = _dashboard_data(pm)
    assert "No items captured yet" in data["notice"]
    assert "No items captured yet" in html          # the page itself says it, not just stdout
    assert all(view["total"] == 0 for view in data["views"])


_DASHBOARD_CMD_RX = re.compile(r"python[^`\n<]*generate_dashboard\.py")
# Only POSITIVE examples may reach the gate. A didactic counter-example ("never run `python
# project_memory/generate_dashboard.py`") documents what NOT to do; run through gate_write_scope it
# would turn this test red, and the obvious "repair" would be to delete the lesson. None exists
# today, hence the filter rather than a rule nobody can see. `assert found` below is what keeps the
# filter from silently emptying a whole source file.
_COUNTEREXAMPLE_RX = re.compile(r"\b(never|no longer|must not|do not|don't)\b", re.I)


def test_the_documented_dashboard_command_survives_the_write_scope_gate(tmp_path):
    """The generator is only reachable if the command a user or agent is TOLD to run passes
    gate_write_scope. It once did not: the gate refuses every write-capable pipeline that names the
    state directory, so the invocation of a generator living inside project_memory/ exited 2 while
    the constitution called it non-skippable. The commands are read OUT of the shipped files, so
    this goes red again the day one of them names the state directory."""
    sources = (
        os.path.join(ROOT, "team-kits", "dev-team", "constitution", "AGENTS.md"),
        os.path.join(os.path.dirname(DASHBOARD), "progress.dashboard.template.html"),
        DASHBOARD,
    )
    commands = []
    for path in sources:
        found = []
        for line in open(path, encoding="utf-8").read().splitlines():
            if _COUNTEREXAMPLE_RX.search(line):
                continue
            found += _DASHBOARD_CMD_RX.findall(line)
        assert found, "no runnable generator command documented in %s" % path
        commands += found
    for command in commands:
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                   "tool_input": {"command": command}, "cwd": str(tmp_path)}
        r = run_hook_process("gate_write_scope.py", payload, tmp_path)
        assert r.returncode == 0, "the documented command %r is refused: %s" % (command, r.stderr)


def test_dashboard_delivery_board_hides_finished_work(tmp_path):
    """Spec II.7: "Delivery (Task-Board, Erledigtes verborgen)". Nothing auto-archives a terminal
    item, so without the filter a VALIDATED task sits on the board for good. Which statuses count
    as finished is the automaton's `terminals`, never a list in the generator."""
    pytest.importorskip("yaml")
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import AUTOMATA
    done = sorted(AUTOMATA["TSK"].terminals)[0]
    pm = _dashboard_repo(tmp_path)
    write(str(pm / "tasks" / "active" / "TSK-0001.yaml"), "id: TSK-0001\nstatus: READY\n")
    write(str(pm / "tasks" / "active" / "TSK-0002.yaml"), "id: TSK-0002\nstatus: %s\n" % done)
    r = _run_dashboard(tmp_path, pm)
    assert r.returncode == 0, r.stdout + r.stderr
    html, data = _dashboard_data(pm)
    delivery = [v for v in data["views"] if v["id"] == "delivery"][0]
    assert [it["id"] for it in delivery["items"]] == ["TSK-0001"]
    assert delivery["total"] == 1, "the hidden item must not be counted as work in progress"
    assert "TSK-0002" not in html
    # the stdout tally is the only place the filter's WORK is visible; an unchecked counter is
    # where a number quietly stops being true
    assert "1 finished hidden" in r.stdout, r.stdout
    # a view WITHOUT the filter still shows its terminal items -- the rule is Delivery's alone
    write(str(pm / "product" / "active" / "PR-0001.yaml"),
          "id: PR-0001\nstatus: %s\n" % sorted(AUTOMATA["PR"].terminals)[0])
    r = _run_dashboard(tmp_path, pm)
    assert r.returncode == 0, r.stdout + r.stderr
    _html, data = _dashboard_data(pm)
    product = [v for v in data["views"] if v["id"] == "product"][0]
    assert [it["id"] for it in product["items"]] == ["PR-0001"]


def test_dashboard_survives_a_hand_written_item(tmp_path):
    """Two shapes no shipped schema produces but a hand-edited item does, and `capture` is not the
    only thing that ever writes these files: a title containing `</script>` ends the embedded JSON
    block as far as any HTML parser is concerned, and mixed top-level key types (`1:` next to `a:`)
    made the relation scan's `sorted()` raise TypeError and kill the run with a traceback.

    The title assertion carries the escaping proof: the extraction here is non-greedy up to the
    first `</script>`, exactly like the parser, so an unescaped title would truncate the block."""
    pytest.importorskip("yaml")
    pm = _dashboard_repo(tmp_path)
    write(str(pm / "bugs" / "active" / "BUG-0001.yaml"),
          'id: BUG-0001\ntitle: "fix </script> leak"\nstatus: OPEN\n1: numeric key\n')
    r = _run_dashboard(tmp_path, pm)
    assert r.returncode == 0, r.stdout + r.stderr
    html, data = _dashboard_data(pm)
    rendered = {it["id"]: it for view in data["views"] for it in view["items"]}
    assert rendered["BUG-0001"]["title"] == "fix </script> leak"
    assert "<\\/script>" in html, "the JSON block is embedded unescaped"


def test_dashboard_vitals_and_the_file_budget_see_the_same_files(tmp_path):
    """One knob, ONE definition. The panel used to carry its own copy of the extension set, its own
    `.min.*` filter and a third line counter, so the promise "panel and gate cannot scan different
    trees" held for the trees and quietly failed for the file TYPES. The expected set here is read
    from `kit_checks.source_files` — the same generator the budget check iterates — so this goes red
    on divergence, whichever side moves."""
    pytest.importorskip("yaml")
    pm = _dashboard_repo(tmp_path)
    write(str(tmp_path / "src" / "app.py"), "x = 1\n" * 2500)
    write(str(tmp_path / "src" / "vendor.min.js"), "let x=1;\n" * 2500)   # vendored, not ours
    write(str(tmp_path / "src" / "notes.md"), "text\n" * 2500)            # not source at all
    r = _run_dashboard(tmp_path, pm)
    assert r.returncode == 0, r.stdout + r.stderr
    _html, data = _dashboard_data(pm)
    expected = {rel for rel, n in _kit_checks_mod().source_files(str(tmp_path)) if n is not None}
    assert "src/app.py" in expected and "src/vendor.min.js" not in expected
    assert data["repo_vitals"]["source_files"] == len(expected)
    assert {entry["path"] for entry in data["repo_vitals"]["largest"]} <= expected
    assert data["repo_vitals"]["over_2000"] == 1


def test_dashboard_page_size_is_the_hard_ceiling(tmp_path):
    """Spec II.7 promises at most 50 items per page and no full text in the initial DOM — the
    reason the template and the generator were rewritten at all. Every other dashboard test works
    with a handful of items and can never touch the boundary."""
    pytest.importorskip("yaml")
    pm = _dashboard_repo(tmp_path)
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    mod = _load_dashboard_module()
    over = mod.PAGE_SIZE + 5
    for n in range(1, over + 1):
        write(str(pm / "bugs" / "active" / ("BUG-%04d.yaml" % n)),
              "id: BUG-%04d\ntitle: crash %d\nstatus: OPEN\n" % (n, n))
    r = _run_dashboard(tmp_path, pm)
    assert r.returncode == 0, r.stdout + r.stderr
    html, data = _dashboard_data(pm)
    product = [v for v in data["views"] if v["id"] == "product"][0]
    assert product["total"] == over
    assert len(product["items"]) == mod.PAGE_SIZE
    assert "BUG-%04d" % over not in html, "an item past the page size reached the initial DOM"


def _load_dashboard_module():
    return load_kit_module("generate_dashboard_under_test", DASHBOARD)


def test_dashboard_views_cover_every_item_type():
    """Every type the kernel knows reaches a view. A type nobody assigned lands in "Other" and is
    named on stdout — the failure worth designing against is a whole item type quietly missing
    from the only overview a user looks at."""
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ACTIVE_DIRS
    mod = _load_dashboard_module()
    views, unassigned = mod.assign_views(ACTIVE_DIRS)
    assert not unassigned, "unassigned item type(s): %s" % unassigned
    covered = [t for view in views for t in view.types]
    assert sorted(covered) == sorted(ACTIVE_DIRS)
    assert len(covered) == len(set(covered)), "a type is rendered in two views"
    # ...and the catch-all really catches: in a green tree `unassigned` is always empty, so the
    # branch that saves a NEW item type from disappearing is otherwise never executed.
    views, unassigned = mod.assign_views({**ACTIVE_DIRS, "ZZZ": "zzz/active"})
    assert unassigned == ["ZZZ"]
    assert "ZZZ" in [t for view in views for t in view.types]


# ---------------- guard_yaml_valid: typed items live in SUBdirectories now ----------------
def test_yaml_valid_reaches_a_typed_item_in_a_subdirectory(tmp_path):
    """The V2 state is one file per item under `project_memory/<type>/active/`, so the guard's
    reach must not stop at the top level — the monolith era only ever wrote there."""
    pytest.importorskip("yaml")
    rel = os.path.join("product", "active", "PR-0001.yaml")
    write(str(tmp_path / "project_memory" / rel), "id: PR-0001\ntitle: a: b\n")  # unquoted colon
    assert run_hook("guard_yaml_valid.py", _yaml_payload(tmp_path, rel), tmp_path) == 2


# ---------------- notify_agent_events: background-agent lifecycle -> audit log ----------------
def _notify(tmp_path, ntype):
    payload = {"hook_event_name": "Notification", "notification_type": ntype,
               "message": "agent done", "cwd": str(tmp_path)}
    return run_hook("notify_agent_events.py", payload, tmp_path)


def test_notify_logs_agent_completed(tmp_path):
    (tmp_path / "project_memory").mkdir()
    assert _notify(tmp_path, "agent_completed") == 0
    audit = tmp_path / "project_memory" / ".audit" / "hook_events.jsonl"
    assert audit.is_file() and "agent_completed" in audit.read_text(encoding="utf-8")


def test_notify_logs_codex_subagent_start(tmp_path):
    (tmp_path / "project_memory").mkdir()
    payload = {"hook_event_name": "SubagentStart", "agent_type": "backend-developer",
               "agent_id": "agent-1", "cwd": str(tmp_path)}
    result = run_hook_process("notify_agent_events.py", payload, tmp_path,
                              extra_env={"TEAM_KIT_PROVIDER": "codex"})
    assert result.returncode == 0
    audit = tmp_path / "project_memory" / ".audit" / "hook_events.jsonl"
    event = json.loads(audit.read_text(encoding="utf-8").splitlines()[-1])
    assert event["event"] == "subagent_start"
    assert event["reason"] == "backend-developer"


def test_notify_ignores_other_types(tmp_path):
    (tmp_path / "project_memory").mkdir()
    assert _notify(tmp_path, "permission_prompt") == 0
    assert not (tmp_path / "project_memory" / ".audit" / "hook_events.jsonl").exists()


def test_notify_never_blocks_without_project(tmp_path):
    assert _notify(tmp_path, "agent_completed") == 0  # no project_memory -> silent no-op


# ---------------- quality.py: secure-context + local-first asset greps ----------------
def test_quality_red_on_raw_secure_context_api(tmp_path):
    write(str(tmp_path / "src" / "static" / "index.html"),
          "<html><script>const id = crypto.randomUUID();</script></html>\n")
    assert run_quality(str(tmp_path)) == 1


def test_quality_green_with_marked_fallback(tmp_path):
    write(str(tmp_path / "src" / "static" / "index.html"),
          "<html><script>// secure-context: has fallback\n"
          "const id = crypto.randomUUID ? crypto.randomUUID() : fallbackUuid();</script></html>\n")
    assert run_quality(str(tmp_path)) == 0


def test_quality_red_on_cdn_asset_when_local_first(tmp_path):
    write(str(tmp_path / "project_memory" / "project_config.yaml"),
          "project:\n  local_first: true\n  stacks: []\n")
    write(str(tmp_path / "src" / "static" / "index.html"),
          '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Caveat">\n')
    assert run_quality(str(tmp_path)) == 1


def test_quality_external_link_anchor_stays_legal(tmp_path):
    # local_first bans loaded RESOURCES, not plain hyperlinks the user may click
    write(str(tmp_path / "project_memory" / "project_config.yaml"),
          "project:\n  local_first: true\n  stacks: []\n")
    write(str(tmp_path / "src" / "static" / "index.html"),
          '<a href="https://github.com/x/y">source</a>\n')
    assert run_quality(str(tmp_path)) == 0


# ---------------- session_status: unfinished kit-update reminder (pending files) ----------------
def test_session_status_reminds_on_pending_kit_update(tmp_path):
    repo = tmp_path / "repo"
    write(str(repo / ".claude" / "kit_update_pending.repo"),
          "# diverged\n- scripts/quality.py\n- requirements-dev.txt\n")
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    p = subprocess.run([sys.executable, os.path.join(HOOKS, "session_status.py")],
                       input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True,
                       env=env, timeout=60)
    assert "KIT MERGE BACKLOG" in p.stdout and "scripts/quality.py" in p.stdout
    assert "do NOT run the scaffold again" in p.stdout  # audit: a PM re-ran the update instead


def test_session_status_quiet_without_pending(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    p = subprocess.run([sys.executable, os.path.join(HOOKS, "session_status.py")],
                       input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True,
                       env=env, timeout=60)
    assert "KIT MERGE BACKLOG" not in p.stdout


# ---------------- session_status: model/effort frontmatter must match the user-confirmed maps ----------------
def _sync_repo(tmp_path, agent_model):
    repo = tmp_path / "repo"
    config_path = repo / "project_memory" / "project_config.yaml"
    write(str(config_path),
          "project:\n  name: x\nmodel_map:\n  backend-developer: opus   # user-approved upscale\n"
          "effort_map:\n  backend-developer: high\n")
    write(str(repo / ".claude" / "agents" / "backend-developer.md"),
          "---\nname: backend-developer\nmodel: %s\neffort: high\n---\nbody\n" % agent_model)
    return repo


def _run_status(repo, provider="claude", hooks_dir=HOOKS):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo), TEAM_KIT_PROVIDER=provider)
    return subprocess.run([sys.executable, os.path.join(hooks_dir, "session_status.py")],
                          input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True,
                          env=env, timeout=60).stdout


@pytest.mark.parametrize("hooks_dir", (HOOKS, RESEARCH_HOOKS, OFFICE_HOOKS))
def test_session_status_flags_model_drift_with_claude_guidance(tmp_path, hooks_dir):
    # the scaffold reset the frontmatter to sonnet although the map says opus -> must nag
    out = _run_status(_sync_repo(tmp_path, "sonnet"), "claude", hooks_dir)
    assert "MODEL/EFFORT OUT OF SYNC" in out and "backend-developer model=sonnet (map says opus)" in out
    assert "frontmatter line in .claude/agents/" in out
    assert "Do NOT edit .codex/agents/*.toml" not in out


@pytest.mark.parametrize("hooks_dir", (HOOKS, RESEARCH_HOOKS, OFFICE_HOOKS))
def test_session_status_flags_model_drift_with_codex_regeneration_guidance(tmp_path, hooks_dir):
    out = _run_status(_sync_repo(tmp_path, "sonnet"), "codex", hooks_dir)
    assert "MODEL/EFFORT OUT OF SYNC" in out
    assert "Do NOT edit .codex/agents/*.toml or one isolated provider source" in out
    assert "confirm a full scaffold re-sync" in out
    assert "Never run the provider generator alone" in out
    assert "verify the generated .codex/agents/*.toml model/effort mappings" in out
    assert "Re-sync each named agent's model:/effort: frontmatter line" not in out


def test_session_status_quiet_when_synced(tmp_path):
    out = _run_status(_sync_repo(tmp_path, "opus"))
    assert "MODEL/EFFORT OUT OF SYNC" not in out


# ---------------- quality.py: the project_memory yaml-lint reaches the typed items ----------------
def test_quality_red_on_unparsable_typed_item(tmp_path):
    """V2 state is one file per item under `project_memory/<type>/active/` (spec II.2). The
    monolith-era pass listed the top level only, which after the lockstep would scan an almost
    empty directory and report green over every real item — and `_repo_wide_yaml_parse` skips
    project_memory/ on the promise that this pass covers it."""
    pytest.importorskip("yaml")
    write(str(tmp_path / "project_memory" / "product" / "active" / "PR-0001.yaml"),
          "id: PR-0001\ntitle: a: b\n")          # unquoted colon
    assert run_quality(str(tmp_path)) == 1


def test_quality_green_on_valid_typed_items(tmp_path):
    pytest.importorskip("yaml")
    write(str(tmp_path / "project_memory" / "product" / "active" / "PR-0001.yaml"),
          "id: PR-0001\ntitle: ok\nstatus: DRAFT\n")
    write(str(tmp_path / "project_memory" / "tasks" / "active" / "TSK-0001.yaml"),
          "id: TSK-0001\nstatus: READY\n")
    assert run_quality(str(tmp_path)) == 0


def test_quality_red_on_duplicate_key_in_typed_item(tmp_path):
    """Duplicate keys parse fine and silently keep the last value — the reason this pass exists
    at all. It has to reach a nested item, not just the (now empty) top level."""
    pytest.importorskip("yaml")
    write(str(tmp_path / "project_memory" / "bugs" / "active" / "BUG-0001.yaml"),
          "id: BUG-0001\nseverity: high\nseverity: low\n")
    assert run_quality(str(tmp_path)) == 1


# ---------------- kit_checks: the kernel's state validator runs in the pipeline ----------------
def _repo_with_kernel_bridge(tmp_path):
    """A repo where kit_checks can reach the kernel the way a scaffolded project does."""
    hooks = tmp_path / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    for helper in ("_kernel.py", "_root.py", "_audit.py", "_compat.py"):
        shutil.copy(os.path.join(HOOKS, helper), str(hooks / helper))
    return {"HARNESS_KERNEL_PATH": os.path.join(ROOT, "team-kits")}


def test_quality_runs_the_kernel_state_validator(tmp_path):
    """Spec II.4 gate 4 in the PIPELINE, not only in the merge gate. A valid state has to be able
    to say so, or the red case below would prove nothing about the check running."""
    pytest.importorskip("yaml")
    env = _repo_with_kernel_bridge(tmp_path)
    (tmp_path / "project_memory").mkdir()
    r = run_quality_proc(str(tmp_path), extra_env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "state validity (kernel validator, 0 findings)" in r.stdout


def test_quality_red_on_a_state_the_kernel_validator_rejects(tmp_path):
    """Two items carrying the SAME id parse cleanly and lint cleanly — only the kernel's graph
    scan sees it, and the merge gate is the latest possible place to learn that."""
    pytest.importorskip("yaml")
    env = _repo_with_kernel_bridge(tmp_path)
    # FR is the type with the smallest field contract, so the duplicate id is the ONLY finding and
    # the assertion cannot pass on some unrelated schema complaint
    inbox = tmp_path / "project_memory" / "inbox" / "active"
    write(str(inbox / "FR-0001.yaml"), "id: FR-0001\ntitle: a\nrequest_text: a\nstatus: OPEN\n")
    write(str(inbox / "FR-0002.yaml"), "id: FR-0001\ntitle: b\nrequest_text: b\nstatus: OPEN\n")
    r = run_quality_proc(str(tmp_path), extra_env=env)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "duplicate id" in r.stdout


def test_kit_check_remedies_name_a_home_that_exists(tmp_path):
    """A remedy has to be walkable, and for a whole round this one was not.

    V2 dissolved the guidelines monolith, so the check first offered a file the scaffold does not
    create and `gate_write_scope` would not let anyone write; the round after that it said the knob
    "has no home in this project", which was honest and still left the user nowhere. The home is an
    `INV` item, so the remedy names that — and it must not fall back to the deleted file's name,
    which is the regression this asserts against.
    """
    pytest.importorskip("yaml")
    write(str(tmp_path / "src" / "static" / "app.js"), "let x = 1;\n" * 900)
    r = run_quality_proc(str(tmp_path))
    assert "file budget" in r.stdout and r.returncode == 1
    assert "guidelines.yaml" not in r.stdout
    assert "no home in this project" not in r.stdout
    assert "INV item" in r.stdout and "scope: file_budget" in r.stdout


def test_quality_says_so_when_the_state_validator_cannot_be_reached(tmp_path):
    """An unreachable validator must never read as a passed one (the false-green class)."""
    pytest.importorskip("yaml")
    (tmp_path / "project_memory").mkdir()
    r = run_quality_proc(str(tmp_path))
    assert "state validator was NOT run" in r.stdout


# ---------------- retro.py: agent lifecycle events must not count as gate blocks ----------------
def test_retro_separates_blocks_from_agent_events(tmp_path):
    retro_src = os.path.join(ROOT, "team-kits", "dev-team", "templates", "repo", "scripts", "retro.py")
    os.makedirs(str(tmp_path / "scripts"), exist_ok=True)
    shutil.copy(retro_src, str(tmp_path / "scripts" / "retro.py"))
    lines = (
        ['{"ts": "t", "hook": "gate_git", "event": "block", "reason": "x"}'] * 2
        + ['{"ts": "t", "hook": "notify_agent_events", "event": "agent_completed", "reason": "done"}'] * 3
    )
    write(str(tmp_path / "project_memory" / ".audit" / "hook_events.jsonl"), "\n".join(lines) + "\n")
    p = subprocess.run([sys.executable, str(tmp_path / "scripts" / "retro.py")],
                       capture_output=True, text=True, cwd=str(tmp_path), timeout=60)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "gates blocked work: gate_git x2" in p.stdout
    assert "background-agent events: agent_completed x3" in p.stdout
    assert "notify_agent_events x" not in p.stdout  # lifecycle events must never read as blocks
    # ...and a missing index must be SAID, not silently rendered as "nothing happened"
    assert "generate-index" in p.stdout


def _run_retro(tmp_path):
    retro_src = os.path.join(ROOT, "team-kits", "dev-team", "templates", "repo", "scripts", "retro.py")
    os.makedirs(str(tmp_path / "scripts"), exist_ok=True)
    shutil.copy(retro_src, str(tmp_path / "scripts" / "retro.py"))
    return subprocess.run([sys.executable, str(tmp_path / "scripts" / "retro.py")],
                          capture_output=True, text=True, cwd=str(tmp_path), timeout=60)


def test_retro_reports_the_item_status_mix_from_the_index(tmp_path):
    """The V2 facts come from the kernel's regenerated index, so retro carries neither a copy of
    the type->directory map nor a copy of the status vocabulary."""
    pytest.importorskip("yaml")
    pm = tmp_path / "project_memory"
    write(str(pm / "tasks" / "active" / "TSK-0001.yaml"), "id: TSK-0001\nstatus: READY\n")
    write(str(pm / "tasks" / "active" / "TSK-0002.yaml"),
          "id: TSK-0002\nstatus: FAILED\nblocked_by: BUG-0001\n")
    write(str(pm / "bugs" / "active" / "BUG-0001.yaml"), "id: BUG-0001\nstatus: OPEN\n")
    index = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, sys.argv[1]);"
         "from kernel.state import ProjectState; ProjectState(sys.argv[2]).generate_index()",
         os.path.join(ROOT, "team-kits"), str(pm)],
        capture_output=True, text=True, timeout=60)
    assert index.returncode == 0, index.stdout + index.stderr
    p = _run_retro(tmp_path)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "TSK: READY x1, FAILED x1" in p.stdout or "TSK: FAILED x1, READY x1" in p.stdout
    assert "BUG: OPEN x1" in p.stdout
    assert "1 blocked item(s): TSK-0002 (by BUG-0001)" in p.stdout
    assert "generate-index" not in p.stdout
    # retro writes ONLY its own diagnostic layer, and that file has to be valid YAML
    import yaml
    entries = yaml.safe_load((pm / "retro.yaml").read_text(encoding="utf-8"))["retros"]
    assert len(entries) == 1 and entries[0]["active_items"] == 3
    assert all(isinstance(f, str) for f in entries[0]["findings"])


# ---------------- init_project_memory: diverged tooling -> pending file; resolution deletes it ----------------
def test_init_pending_file_written_and_removed(tmp_path):
    home = tmp_path / "home"
    tpl = home / ".claude" / "team-kits" / "demo-team" / "templates" / "project_memory"
    write(str(tpl / "gen.py"), "print('v2')\n")
    repo = tmp_path / "repo"
    repo.mkdir()

    if os.name == "nt":
        script = os.path.join(ROOT, "team-kits", "init_project_memory.ps1")
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script, "-Team", "demo-team"]
        env = dict(os.environ, USERPROFILE=str(home))
    else:
        if not shutil.which("bash"):
            pytest.skip("bash not available")
        script = os.path.join(ROOT, "team-kits", "init_project_memory.sh")
        cmd = ["bash", script, "demo-team"]
        env = dict(os.environ, HOME=str(home))

    def run_init():
        r = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True, env=env, timeout=60)
        assert r.returncode == 0, r.stdout + r.stderr

    run_init()  # fresh copy — no divergence, no pending file
    pend = repo / ".claude" / "kit_update_pending.memory"
    assert not pend.exists()

    (repo / "project_memory" / "gen.py").write_text("print('v1')\n", encoding="utf-8")
    run_init()  # tooling diverged -> pending file records it
    assert pend.is_file() and "gen.py" in pend.read_text(encoding="utf-8-sig")

    (repo / "project_memory" / "gen.py").write_text("print('v2')\n", encoding="utf-8")
    run_init()  # divergence resolved -> pending file removed
    assert not pend.exists()


# ---------------- kit mirroring: shared files must stay byte-identical across kits ----------------
# Hooks that legitimately differ per kit — each one a decision, not an omission. Anything NOT
# listed here and present in more than one kit must be byte-identical.
KIT_SPECIFIC_HOOKS = {
    "session_status.py": "the session briefing names each kit's own artifacts and nags",
    "format_on_write.py": "formats the languages a kit actually produces",
    # Kit-specific BY CONSTRUCTION: it is the list of document trays THIS kit ships in its repo
    # template, derived by `kernel.trays` and regenerated by `bump_kit_version.py`. Office ships
    # three, dev and research none, and a mirrored copy would put the office exemption back into
    # the kits F1 removed it from.
    "document_trays.txt": "each kit's own trays, derived from its templates/repo",
    # Kit-specific BY CONSTRUCTION as well: it describes THIS kit's registered mechanisms, and the
    # three kits register 24 / 21 / 22 different ones. A mirrored copy would promise the office kit
    # a `gate_test_coverage` it does not ship.
    "ENFORCEMENT.md": "each kit's own registered mechanisms, described",
}
# The SAME rule for the project scripts a kit ships. Empty on purpose: the office kit's scripts
# share no filename with dev/research, and every name dev and research both ship is meant to be one
# file. A kit that needs its own variant of one adds it here WITH the reason.
KIT_SPECIFIC_SCRIPTS = {}
KITS = ("dev-team", "office-team", "research-team")


def _kit_files_by_name(rel_dir, suffixes=None):
    """{filename: {kit: bytes}} for one directory across all kits — the input to the mirror rule.

    `suffixes=None` means EVERY file, and that is what the hooks directory is read with. A suffix
    filter there was a hole with a docstring over it: the rule below claims "a new mirrored file
    is covered the day it ships" while `(".py",)` covered only the Python half. Measured
    2026-08-01 with three DIFFERENT `hooks/allowlist.txt`, one per kit — green. That stopped being
    hypothetical the day `hooks/document_trays.txt` shipped, which is a behaviour source a hook
    reads.
    """
    by_name = {}
    for kit in KITS:
        directory = os.path.join(ROOT, "team-kits", kit, *rel_dir)
        for name in sorted(os.listdir(directory)):
            path = os.path.join(directory, name)
            if not os.path.isfile(path):
                continue          # `__pycache__` and friends are not shipped files
            if suffixes is not None and not name.endswith(suffixes):
                continue
            with open(path, "rb") as handle:
                by_name.setdefault(name, {})[kit] = handle.read()
    return by_name


def _assert_mirrored(label, by_name, exceptions):
    for name, copies in sorted(by_name.items()):
        if len(copies) < 2 or name in exceptions:
            continue
        assert len(set(copies.values())) == 1, (
            "%s/%s exists in %s and they are NOT identical — either re-mirror it, or add it to the "
            "kit-specific map with the reason" % (label, name, ", ".join(sorted(copies))))
    # ...and a name on the exception list that has stopped differing is an exception nobody needs
    for name in sorted(exceptions):
        copies = by_name.get(name, {})
        if len(copies) >= 2:
            assert len(set(copies.values())) > 1, (
                "%s/%s is listed as kit-specific but all copies are identical — drop the exception "
                "so it stays pinned" % (label, name))


def test_the_hooks_that_name_a_typed_directory_spell_it_as_the_kernel_does():
    """A hook that hard-codes a state path must agree with `ACTIVE_DIRS`, or it reads an empty tree.

    Spec II.7 keeps the integrity gates stdlib-first, so a gate that needs one typed directory
    spells it as a literal rather than importing the kernel for it — a guard that cannot load must
    not stop guarding. That literal is a second statement of a kernel constant, which is exactly the
    shape this repo keeps finding a defect in, so it is PINNED here instead of trusted.

    WHAT MAKES A CONSTANT ONE OF THESE is what the hook DOES with it, not what it is called: a
    tuple of literals that the module SPLATS into a `join(...)` is a path composition, and there is
    nothing else it could be. The first cut asked for a name ending in `_DIR` instead and was an
    enumeration wearing a definition's clothes — it read `gate_filing`'s `GNU_TARGET_DIR`
    (`mv`/`cp`/`install`, a set of shell verbs it tests membership against) as a state path and
    reported it as a defect.

    Derived, so a hook that gains such a constant is covered the day it ships, and one whose value
    drifts from the kernel fails the same day. Measured reach: changing `INVARIANTS_DIR` to
    `("invariants", "activ")` in either hook that has one turns this red.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ACTIVE_DIRS
    known = set(ACTIVE_DIRS.values())
    seen = []
    for kit in KITS:
        hooks_dir = os.path.join(ROOT, "team-kits", kit, "hooks")
        for name in sorted(os.listdir(hooks_dir)):
            if not name.endswith(".py"):
                continue
            tree = ast.parse(open(os.path.join(hooks_dir, name), encoding="utf-8").read())
            literals = {}
            for node in tree.body:
                if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Tuple)):
                    continue
                parts = [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
                if len(parts) != len(node.value.elts):
                    continue              # not a plain tuple of literals
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        literals[target.id] = "/".join(str(p) for p in parts)
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and _callee_name(node) == "join"):
                    continue
                for argument in node.args:
                    if not (isinstance(argument, ast.Starred)
                            and isinstance(argument.value, ast.Name)
                            and argument.value.id in literals):
                        continue
                    spelled = literals[argument.value.id]
                    seen.append("%s/%s:%s" % (kit, name, argument.value.id))
                    assert spelled in known, (
                        "%s/%s joins %s as a path, and it spells %r — no entry of kernel "
                        "ACTIVE_DIRS (%s), so the hook would read an empty directory and decide "
                        "on it" % (kit, name, argument.value.id, spelled, ", ".join(sorted(known))))
    # a floor, so the reader silently finding nothing cannot pass for agreement
    assert seen, "no hook composes a typed-directory constant any more — did the reader narrow?"


_SHIPPED_SCRIPT_RX = re.compile(r"(?:scripts/)?(kit_checks|quality|kit_browser_checks|"
                                r"generate_dashboard|retro|harness)(?:\.py)?")


def test_the_invariant_scan_of_a_blocking_gate_is_bounded(tmp_path):
    """A gate that cannot answer inside the host's budget is a gate that ALLOWS (spec II.4).

    Both readers of the invariant store sit on BLOCKING PreToolUse hooks — `guard_guidelines` on
    every code write, `gate_test_coverage` on every merge/push — and both walked the whole
    directory with no bound at all. Measured before the caps: ~0.23 s per MB (10 MB 4.80 s,
    99 MB 22.84 s, 199 MB 46.82 s), so a store past ~250 MB crosses the 60 s at which the host
    kills the hook, and a killed hook is an ALLOW. The inversion was the giveaway: the NON-blocking
    repo script carried a per-file cap with its reason while the blocking gates carried none.

    ASSERTED AS A PROPERTY, NOT AS A DURATION, deliberately: a wall-clock bound on a scan this
    cheap measures the machine (that mistake is documented one file over, in the memory-budget
    latency test). The bound is visible in the RESULT instead — items beyond
    `INVARIANT_SCAN_MAX_BYTES` are not read, so their scopes do not appear, and both readers stop
    at the same place because both walk the directory in sorted order.
    """
    pytest.importorskip("yaml")
    mod = _kit_checks_mod()
    gate = load_kit_module("gate_test_coverage_bounded",
                           os.path.join(HOOKS, "gate_test_coverage.py"))
    invariants = tmp_path / "project_memory" / "invariants" / "active"
    # one item just under the per-item cap per area, enough of them to pass the scan budget
    per_item = mod.INVARIANT_MAX_BYTES - 4096
    count = mod.INVARIANT_SCAN_MAX_BYTES // per_item + 2
    for index in range(count):
        area = "area%02d" % index
        os.makedirs(str(tmp_path / area), exist_ok=True)
        path = str(invariants / ("INV-%04d.yaml" % (index + 1)))
        # the filler is ONE long scalar, not many lines: `write` opens in text mode, so on Windows
        # every newline costs a second byte on disk and a line-counted payload lands ABOVE the
        # per-item cap instead of just under it — measured, and it made every item invisible
        write(path, "id: INV-%04d\nscope: %s\nsource: PR-0001\n"
                    "check: {kind: test, ref: \"t.py::t\"}\nstatus: unverified\ntext: %s\n"
                    % (index + 1, area, "x" * (per_item - 200)))
        assert os.path.getsize(path) < mod.INVARIANT_MAX_BYTES, "the fixture item is oversized"
    seen = mod.governed_source_areas(str(tmp_path))
    from_gate = gate._governed_source_areas(str(tmp_path),
                                            os.path.join(str(tmp_path), "project_memory"))
    assert seen == from_gate, (seen, from_gate)
    assert 0 < len(seen) < count, (
        "the scan read %d of %d items — the whole-store budget bounds nothing" % (len(seen), count))


def test_no_shipped_template_declares_a_knob_the_scripts_read_somewhere_else():
    """A shipped state template may not offer a key that is really an `INV` knob, or claim a
    script reads a key it does not.

    THE CLASS, measured in the research kit on 2026-07-31 and closed with this check:
    `research_guidelines.yaml` shipped `source_areas:`, `module_invariants:` and
    `yaml_lint_exclude:` with comments saying "the deterministic checks SCAN", "enforced by
    `scripts/kit_checks.py`" and "Repo-wide YAML parse (kit_checks)". After the knobs moved into
    `INV` items no script read any of them, so a project filling them got nothing — measured in a
    research scaffold: `compounder/big.py` at 1 200 lines PASSED the file budget with
    `source_areas: [compounder]`, and FAILED it with the same package as an invariant's `scope`.
    The V1-monolith sweep cannot see this: `research_guidelines.yaml` is reference material, not a
    monolith, so it is correctly outside `conftest.V1_MONOLITHS` — and a dead key inside a LIVING
    file is a shape that inventory was never going to catch.

    TWO PROPERTIES, both derived from the RUNNING scripts, because one of them alone was measured
    insufficient:

      * A KNOB NAME IS TAKEN. The scopes the kit scripts read as knobs are the literal arguments
        to their `invariant_knob(...)` calls, read out of the AST — today `file_budget`,
        `module_invariants`, `yaml_lint_exclude`, `coverage_gate`, `browser_smoke`, and whatever a
        later round adds without telling this test. A top-level key of that name in a state
        template is a decoy: the script reads that name out of an `INV` item, so filling the key
        does nothing. Reintroducing the `module_invariants:` block passes the annotation rule
        below on its own (the name IS a literal in `kit_checks.py`, just not read from there) —
        measured, and that is why this half exists.
      * A NAMED SCRIPT MUST READ IT. A comment directly above a top-level key that NAMES one of
        the kit's own scripts is a claim about that script, so the key must appear as a string
        literal in it. This is the half that catches a name no script mentions at all —
        `source_areas:` and `coverage_areas:` are literals nowhere any more.

    Prose rules a ROLE reads (`global:`, `methods:`, `method_tooling:`) name no script and are no
    knob — none of this check's business, which is the line between a rule and a knob.
    """
    scripts = {}
    knobs = set()
    for kit in KITS:
        directory = os.path.join(ROOT, "team-kits", kit, "templates", "repo", "scripts")
        for name in sorted(os.listdir(directory)) if os.path.isdir(directory) else []:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(directory, name), encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            scripts.setdefault(name[:-3], set()).update(
                node.value for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and isinstance(node.value, str))
            for node in ast.walk(tree):
                # `invariant_knob(root, "<scope>")` and the local wrapper `_invariant_knob(...)`:
                # matched on the callable's NAME, so a third spelling of the same call is covered
                if not isinstance(node, ast.Call):
                    continue
                called = getattr(node.func, "attr", getattr(node.func, "id", "")) or ""
                if not called.endswith("invariant_knob"):
                    continue
                for argument in node.args:
                    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                        knobs.add(argument.value)
    assert scripts and knobs, "no kit script / no knob found — did the reader narrow?"
    offences = []
    for kit in KITS:
        directory = os.path.join(ROOT, "team-kits", kit, "templates", "project_memory")
        for name in sorted(os.listdir(directory)) if os.path.isdir(directory) else []:
            if not name.endswith((".yaml", ".yml")):
                continue
            path = os.path.join(directory, name)
            comment = []
            for line in open(path, encoding="utf-8", errors="ignore").read().splitlines():
                if line.startswith("#"):
                    comment.append(line)
                    continue
                key = re.match(r"([A-Za-z_][A-Za-z0-9_]*):", line)
                if key and key.group(1) in knobs:
                    offences.append("%s/%s: `%s:` is an INV knob — the scripts read that name out "
                                    "of an invariant, so the key here is a decoy"
                                    % (kit, name, key.group(1)))
                if key and comment:
                    named = {m.group(1) for block in comment
                             for m in _SHIPPED_SCRIPT_RX.finditer(block)}
                    for script in sorted(named & set(scripts)):
                        if key.group(1) not in scripts[script]:
                            offences.append("%s/%s: `%s:` is annotated with %s.py, which never "
                                            "reads that key" % (kit, name, key.group(1), script))
                comment = []
    assert not offences, (
        "a shipped template offers a key nothing behind it honours:\n  " + "\n  ".join(offences))


def test_the_two_readers_of_a_governed_source_area_agree(tmp_path):
    """One definition, two processes: the merge gate and the file budget must see the same areas.

    "A source area is a directory some `INV` item's `scope` names" replaced two V1 config keys in
    two files (`coverage_areas:` and `source_areas:`) that meant the same thing and drifted — an
    audit caught one of them scanning an area the other skipped. A hook cannot import a repo script,
    so the derivation exists twice; a copy that may not be deleted has to be PINNED, and this is the
    pin: one INV fixture, both readers, the same answer.

    Both are read where they RUN — the gate as a real hook process (its verdict is the only thing a
    session ever sees of it), the script through its own module — so neither can be satisfied by a
    docstring.

    THE FIXTURE CARRIES AN OVERSIZED ITEM, because without one this pin was green while the two
    readers already disagreed: the script skipped an item past its per-file cap and the hook, which
    had no cap at all, read it. Measured then — `script=[]` against `gate=['compounder']` — and the
    pin could not see it, since every item it built was small. The caps themselves are compared
    too, so a reader that keeps a limit of its own invents a divergence rather than inheriting one.
    """
    pytest.importorskip("yaml")
    capture_root_item(tmp_path)
    for name in ("compounder", "engine", "docs_site", "bloated"):
        os.makedirs(str(tmp_path / name), exist_ok=True)
    capture_invariant(tmp_path, "compounder/scoring", text="pure, no I/O")
    capture_invariant(tmp_path, "engine", text="deterministic")
    capture_invariant(tmp_path, "python", text="not a directory, so not an area")
    capture_invariant(tmp_path, "..", text="a scope that would walk out of the repo")
    mod = _kit_checks_mod()
    gate = load_kit_module("gate_test_coverage_under_test",
                           os.path.join(HOOKS, "gate_test_coverage.py"))
    guard = load_kit_module("guard_guidelines_under_test",
                            os.path.join(HOOKS, "guard_guidelines.py"))
    for name in ("INVARIANT_MAX_BYTES", "INVARIANT_SCAN_MAX_BYTES"):
        values = {getattr(reader, name) for reader in (mod, gate, guard)}
        assert len(values) == 1, "%s differs across the readers: %s" % (name, values)
    # an item past the per-item cap governs nothing — in BOTH readers or in neither
    oversized = capture_invariant(tmp_path, "bloated", text="x")
    path = os.path.join(str(tmp_path), "project_memory", "invariants", "active",
                        oversized["id"] + ".yaml")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("padding: |\n" + "  filler\n" * (mod.INVARIANT_MAX_BYTES // 9))

    from_script = mod.governed_source_areas(str(tmp_path))
    from_gate = gate._governed_source_areas(str(tmp_path),
                                            os.path.join(str(tmp_path), "project_memory"))
    assert sorted(from_script) == sorted(from_gate) == ["compounder", "engine"]
    # ...and the gate's answer is what a real hook process acts on: `compounder/` has code, no tests
    write(str(tmp_path / "compounder" / "core.py"), "def f():\n    return 1\n")
    result = run_hook_process("gate_test_coverage.py",
                              {"tool_name": "Bash", "cwd": str(tmp_path),
                               "tool_input": {"command": "git push origin main"}}, tmp_path)
    assert result.returncode == 2 and "compounder" in result.stderr


def test_shared_kit_files_identical():
    """DERIVED, not listed. The old version enumerated six filenames, so every file mirrored after
    it was written stayed unpinned — `_gate.py`, `_kernel.py`, `_compat.py`, `kit_trust_state.py`
    and all six V2 gates lived in three unpinned copies. It found nothing when
    `gate_shell_hygiene.py` actually drifted: a fix limiting the docker rule to DESTRUCTIVE
    commands reached dev-team and neither mirror, so two kits blocked `docker compose ps`.

    Now the burden is the other way round: a name present in more than one kit is pinned unless
    KIT_SPECIFIC_HOOKS says why it differs. A new mirrored file is covered the day it ships — and
    that sentence was only true of `.py` files for a round, because the reader carried a suffix
    filter the sentence did not mention. Three different `hooks/allowlist.txt` passed it, measured;
    the hooks half now reads EVERY shipped file, which is what makes the claim above one the code
    builds.

    The SCRIPTS half used to be the old shape again — three typed filenames — so `kit_browser_checks.py`
    was unpinned here and `generate_dashboard.py` plus its HTML shell would have drifted silently the
    day research got a copy. Same derivation now, same burden of proof."""
    _assert_mirrored("hooks", _kit_files_by_name(("hooks",)), KIT_SPECIFIC_HOOKS)
    _assert_mirrored("templates/repo/scripts",
                     _kit_files_by_name(("templates", "repo", "scripts"), (".py", ".html")),
                     KIT_SPECIFIC_SCRIPTS)


# ---------------- kit_checks: file budget (the anti-monolith gate) ----------------
def test_file_budget_blocks_monolith(tmp_path):
    pytest.importorskip("yaml")
    write(str(tmp_path / "src" / "static" / "app.js"), "let x = 1;\n" * 900)
    assert run_quality(str(tmp_path)) == 1


def test_file_budget_exemption_with_reason_passes(tmp_path):
    pytest.importorskip("yaml")
    write(str(tmp_path / "src" / "static" / "app.js"), "let x = 1;\n" * 900)
    capture_invariant(tmp_path, "file_budget", value={
        "max_lines": 800,
        "exempt": [{"path": "src/static/app.js",
                    "reason": "legacy monolith - split tracked in TSK-1"}]})
    assert run_quality(str(tmp_path)) == 0


def test_file_budget_under_limit_green(tmp_path):
    pytest.importorskip("yaml")
    write(str(tmp_path / "src" / "static" / "app.js"), "let x = 1;\n" * 100)
    assert run_quality(str(tmp_path)) == 0


# ---------------- session_status: pending nag escalates across sessions ----------------
def test_pending_nag_escalates(tmp_path):
    repo = tmp_path / "repo"
    write(str(repo / ".claude" / "kit_update_pending.repo"), "# d\n- scripts/quality.py\n")
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))

    def run_status():
        return subprocess.run([sys.executable, os.path.join(HOOKS, "session_status.py")],
                              input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True,
                              env=env, timeout=60).stdout

    first = run_status()
    assert "KIT MERGE BACKLOG" in first and "OPEN SINCE" not in first
    second = run_status()
    # SAME-DAY sessions never scold (audit: a user actively working the backlog hit
    # "5th session" within one evening) — escalation needs an OLDER first_seen
    assert "OPEN SINCE" not in second
    write(str(repo / ".claude" / "kit_update_pending.state"),
          json.dumps({"sessions": 2, "first_seen": "2020-01-01"}))
    third = run_status()
    assert "OPEN SINCE 2020-01-01" in third and "3. session" in third
    (repo / ".claude" / "kit_update_pending.repo").unlink()
    cleared = run_status()
    assert "KIT MERGE BACKLOG" not in cleared
    assert not (repo / ".claude" / "kit_update_pending.state").exists()  # counter reset


# ---------------- guard_agent_spawn: allowed spawns are audited ----------------
def test_allowed_spawn_is_audited(kit_repo):
    (kit_repo / "project_memory").mkdir()
    payload = {"tool_name": "Agent",
               "tool_input": {"subagent_type": "backend-developer", "run_in_background": False,
                              "prompt": WORK_ORDER},
               "cwd": str(kit_repo)}
    assert run_hook("guard_agent_spawn.py", payload, kit_repo) == 0
    audit = kit_repo / "project_memory" / ".audit" / "hook_events.jsonl"
    text = audit.read_text(encoding="utf-8")
    assert '"event": "spawn"' in text and "backend-developer" in text


# ---------------- gate_subagent_output: specialists honor their output contract ----------------
def _stop_payload(repo, atype, message):
    return {"hook_event_name": "SubagentStop", "agent_type": atype,
            "last_assistant_message": message, "cwd": str(repo)}


def test_subagent_output_blocks_prose_only(kit_repo):
    payload = _stop_payload(kit_repo, "backend-developer", "All done, everything works great!")
    assert run_hook("gate_subagent_output.py", payload, kit_repo) == 2


def test_subagent_output_uses_codex_block_decision(kit_repo):
    payload = _stop_payload(kit_repo, "backend-developer", "prose only")
    result = run_hook_process(
        "gate_subagent_output.py", payload, kit_repo,
        extra_env={"TEAM_KIT_PROVIDER": "codex"})
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["decision"] == "block" and "output-contract" in output["reason"]
    assert "continue" not in output


def test_subagent_output_passes_contract(kit_repo):
    payload = _stop_payload(kit_repo, "backend-developer", "summary: implemented SR-1\nstatus: DONE")
    assert run_hook("gate_subagent_output.py", payload, kit_repo) == 0


def test_subagent_output_verdict_role_needs_verdict(kit_repo):
    write(str(kit_repo / ".claude" / "agents" / "quality-engineer.md"), "x")
    payload = _stop_payload(kit_repo, "quality-engineer", "summary: reviewed everything, looks fine")
    assert run_hook("gate_subagent_output.py", payload, kit_repo) == 2
    payload = _stop_payload(kit_repo, "quality-engineer", "summary: gate run\nverdict: PASS")
    assert run_hook("gate_subagent_output.py", payload, kit_repo) == 0


def test_subagent_output_ignores_foreign_agents(kit_repo):
    payload = _stop_payload(kit_repo, "Explore", "just some search results")
    assert run_hook("gate_subagent_output.py", payload, kit_repo) == 0


# ---------------- session_status: version-change announcement after an external restamp ----------------
def test_version_change_announced_once(tmp_path):
    repo = tmp_path / "repo"
    write(str(repo / ".claude" / "kit_version"), "version: 2026.07.12-4\ncontent: aaa\n")
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))

    def run_status():
        return subprocess.run([sys.executable, os.path.join(HOOKS, "session_status.py")],
                              input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True,
                              env=env, timeout=60).stdout

    first = run_status()
    assert "KIT UPDATED" not in first  # first sighting just records the version
    write(str(repo / ".claude" / "kit_version"), "version: 2026.07.14-1\ncontent: bbb\n")
    second = run_status()
    assert "KIT UPDATED" in second and "2026.07.12-4 -> 2026.07.14-1" in second
    third = run_status()
    assert "KIT UPDATED" not in third  # announced once, then recorded


# ---------------- guard_harness_selfmod: the enforcement layer is not self-editable ----------------
def test_selfmod_blocks_hook_edit(tmp_path):
    p = tmp_path / ".claude" / "hooks" / "gate_git.py"
    payload = {"tool_name": "Edit", "tool_input": {"file_path": str(p)}, "cwd": str(tmp_path)}
    assert run_hook("guard_harness_selfmod.py", payload, tmp_path) == 2


def test_selfmod_blocks_settings_edit(tmp_path):
    p = tmp_path / ".claude" / "settings.json"
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(p)}, "cwd": str(tmp_path)}
    assert run_hook("guard_harness_selfmod.py", payload, tmp_path) == 2


@pytest.mark.parametrize("rel", [
    ".codex/config.toml",
    ".codex/hooks.json",
    ".codex/agents/backend-developer.toml",
    ".agents/skills/backend-developer/SKILL.md",
    ".CoDeX/agents/reviewer.toml",
    ".AGENTS/SKILLS/reviewer/SKILL.md",
    ".claude/provider_artifacts.json",
    ".claude/team_kit_roles.txt",
])
def test_selfmod_blocks_provider_generated_control_files(tmp_path, rel):
    p = tmp_path / rel
    payload = {"tool_name": "Edit", "tool_input": {"file_path": str(p)},
               "cwd": str(tmp_path)}
    assert run_hook("guard_harness_selfmod.py", payload, tmp_path) == 2, rel


def test_selfmod_blocks_editing_the_installed_entry_point(tmp_path):
    """The file every fail-closed remedy tells a role to RUN is not a file that role may edit.

    `scripts/harness.py` is installed kit-owned and imports the kernel, so an edited copy could
    mint an approval and clear `gate_push_token` while every refusal in the tree kept pointing at
    it — the same argument that put `scripts/ledger_add.py` in `BLOCKED_REPO_PATHS`. The path
    comes from `kernel.cli.ENTRY_POINT`, so moving the entry point moves this test with it rather
    than leaving a guard on a path nothing uses.

    What this does NOT pin is unreachability: this is an Edit/Write guard, and a shell write goes
    around it — the guard's own docstring has said so since V1.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    for kit in ("dev-team", "office-team", "research-team"):
        hooks = os.path.join(ROOT, "team-kits", kit, "hooks")
        payload = {"tool_name": "Edit", "cwd": str(tmp_path),
                   "tool_input": {"file_path": str(tmp_path / cli.ENTRY_POINT)}}
        assert run_hook("guard_harness_selfmod.py", payload, tmp_path, hooks) == 2, kit


def test_selfmod_allows_scaffold_command(tmp_path):
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "bash ~/.claude/team-kits/scaffold_team.sh dev-team"},
        "cwd": str(tmp_path),
    }
    assert run_hook("guard_harness_selfmod.py", payload, tmp_path) == 0


def test_selfmod_allows_agent_resync_and_memory(tmp_path):
    for rel in (".claude/agents/backend-developer.md", ".claude/agent-memory/project-manager/MEMORY.md"):
        p = tmp_path / rel
        payload = {"tool_name": "Edit", "tool_input": {"file_path": str(p)}, "cwd": str(tmp_path)}
        assert run_hook("guard_harness_selfmod.py", payload, tmp_path) == 0, rel


# ---------------- gate_git: QA binding (audit false-accept regression, in its V2 shape) ---------
def capture_task(repo, root="PR-0001", **overrides):
    """A TSK hanging from `root` — what QA actually judges, and the indirect binding's middle hop."""
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    fields = {"product_requirement": root, "root_revision": 1, "derives_from": [root],
              "type": "implementation", "assigned_role": "backend-developer",
              "acceptance_refs": ["AC-1"], "required_inputs": [], "allowed_scope": ["src/**"],
              "forbidden_scope": [], "expected_outputs": ["src/checkout.py"], "dependencies": []}
    fields.update(overrides)
    return ProjectState(os.path.join(str(repo), "project_memory")).capture("TSK", fields)


def test_gate_git_a_pass_for_another_item_plus_a_fail_for_this_one_blocks(prd_repo):
    """The reported false accept, carried over to the store that replaced the report files.

    V1 kept every verdict in ONE file and matched TEXT, so an old PASS for another item sitting
    next to a fresh FAIL for the target lifted the gate. Here the two verdicts are two items with
    two `related` fields, and only the one about this item is read."""
    capture_root_item(prd_repo, dict(PR_FIELDS, title="Second"))   # PR-0002
    capture_evidence(prd_repo, result="pass", related=("PR-0002",))
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    result = run_hook_process("gate_git.py", _merge(prd_repo), prd_repo)
    assert result.returncode == 2
    assert "not a pass" in result.stderr


def test_gate_git_a_fail_for_another_item_does_not_close_this_merge(prd_repo):
    """The counter-direction, so the test above cannot be satisfied by blocking everything."""
    capture_root_item(prd_repo, dict(PR_FIELDS, title="Second"))   # PR-0002
    capture_evidence(prd_repo, result="fail", related=("PR-0002",))
    capture_evidence(prd_repo, result="pass", related=("PR-0001",))
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 0


def test_gate_git_evidence_bound_to_a_task_resolves_to_its_root(prd_repo):
    """QA judges a TASK; the merge is of the PR it hangs from. V1 could only fall back to matching
    the PR's name anywhere in the file — including in a comment. V2 walks the reference graph."""
    task = capture_task(prd_repo)
    capture_evidence(prd_repo, related=(task["id"],))
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 0


def test_gate_git_evidence_bound_to_an_archived_task_still_resolves(prd_repo):
    """A task is archived when it reaches VALIDATED — which is BEFORE the merge it was validated
    for. Resolving only active items would lose the binding exactly at the finish line."""
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    state = ProjectState(os.path.join(str(prd_repo), "project_memory"))
    task = capture_task(prd_repo)
    capture_evidence(prd_repo, related=(task["id"],))
    for status in ("READY", "LEASED", "IN_PROGRESS", "SUBMITTED", "DONE", "VALIDATED"):
        state.transition(task["id"], status)
    state.archive(task["id"])
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 0


def test_gate_git_a_fail_recorded_after_a_pass_closes_the_gate_again(prd_repo):
    """Newest-wins, not any-pass-wins: a regression found after a green run is what re-blocks the
    merge, and "there is a passing Evidence somewhere" cannot express that."""
    capture_evidence(prd_repo, kind="test", result="pass")
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 0
    capture_evidence(prd_repo, kind="test", result="fail")
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 2
    capture_evidence(prd_repo, kind="test", result="pass")   # the fix, re-verified
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 0


def test_gate_git_a_failing_kind_blocks_although_another_kind_passes(prd_repo):
    """Per KIND, because the kinds ask different questions: a green test run does not answer the
    reviewer's finding, and reading only "some kind passed" would let it."""
    capture_evidence(prd_repo, kind="test", result="pass")
    capture_evidence(prd_repo, kind="review", result="fail")
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 2


def test_gate_git_archiving_a_superseded_verdict_retires_it(prd_repo):
    """Archiving is a kernel operation and visible in git, so it does lift the gate — and the
    remedy text says so rather than pretending otherwise. What it must NOT be is the cheap way
    out, which is why the kernel refuses to edit an Evidence at all (test_state.py)."""
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    failed = capture_evidence(prd_repo, kind="review", result="fail")
    capture_evidence(prd_repo, kind="test", result="pass")
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 2
    ProjectState(os.path.join(str(prd_repo), "project_memory")).archive(failed)
    assert run_hook("gate_git.py", _merge(prd_repo), prd_repo) == 0


def test_gate_git_names_recording_the_re_run_as_the_way_out_of_a_fail(prd_repo):
    """The refusal must point at the mechanism that exists, and describe archiving honestly.

    Two failures this pins, both of them a house-rule-3 shape: a remedy that recommends editing
    the Evidence (which the kernel refuses), and one that recommends archiving as THE fix while
    the whole paragraph demands the work be repaired — archiving retires a verdict without
    replacing it, so it is aftercare, not a remedy.
    """
    capture_evidence(prd_repo, kind="test", result="fail")
    stderr = run_hook_process("gate_git.py", _merge(prd_repo), prd_repo).stderr
    assert "scripts/harness.py evidence" in stderr and "--result pass" in stderr
    assert "refuses to EDIT" in stderr
    assert "after a newer run, not instead of one" in stderr


# ---------------- gate_git: WHICH item the merge is about ----------------------------------------
def test_gate_git_requires_every_item_the_command_names(prd_repo):
    """An id in a message is a requirement, never a substitute for the ref's own verdict.

    The measured regression: reading "the first root id anywhere in the raw command" made
    `git merge -m "see PR-0002" feat/PR-0001-x` a merge of PR-0002 in the gate's eyes, so an old
    PASS for another item lifted the gate over a fresh FAIL for the branch's item — literally the
    audit false accept, restored by one flag. Both spellings are checked because they fail
    differently: quoted, the message is not part of the invocation at all; unquoted, it names a
    second item and the gate then wants BOTH green.
    """
    capture_root_item(prd_repo, dict(PR_FIELDS, title="Second"))   # PR-0002
    capture_evidence(prd_repo, result="pass", related=("PR-0002",))
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    for command in ('git merge -m "see PR-0002" feat/PR-0001-x',
                    "git merge -m see-PR-0002 feat/PR-0001-x"):
        result = run_hook_process("gate_git.py", _bash(prd_repo, command), prd_repo)
        assert result.returncode == 2, command
        assert "PR-0001" in result.stderr, command


def test_gate_git_ignores_an_item_named_only_in_a_shell_comment(prd_repo):
    """The counter-direction of the rule above: what the shell drops, the gate drops.

    Without it "require every named item" would be satisfiable by blocking on anything that looks
    like an id anywhere on the line, and a trailing note would start failing merges.
    """
    capture_evidence(prd_repo, result="pass", related=("PR-0001",))
    assert run_hook("gate_git.py",
                    _bash(prd_repo, "git merge feat/PR-0001-x  # follow-up to PR-0002"),
                    prd_repo) == 0


@pytest.mark.parametrize("quote", ["", '"', "'"])
def test_gate_git_binds_a_quoted_ref_exactly_like_a_bare_one(prd_repo, quote):
    """Quoting the ref is the ordinary spelling and must change nothing the gate decides.

    Measured before the fix, in a scaffolded project with the shipped hook as a real process:
    `git merge feat/PR-0002-x` blocked and `git merge "feat/PR-0002-x"` merged — an item with no
    Evidence at all, and a DRAFT one likewise. The cause was reading the PROSE-stripped view for a
    question about ARGUMENTS: a quoted span is prose only when the question is whether the line
    invokes git; here it is the ref itself. Both teeth of disposition row 115 are checked, because
    they fail through the same hole and each alone can be satisfied by the wrong implementation —
    the evidence tooth by any block, the status tooth by any lookup that finds the item.
    """
    capture_root_item(prd_repo, dict(PR_FIELDS, title="Second"))                    # PR-0002
    capture_root_item(prd_repo, dict(PR_FIELDS, title="Third"), status=None)        # PR-0003 DRAFT
    capture_evidence(prd_repo, result="pass", related=("PR-0001",))
    for item, why in (("PR-0002", "no QA Evidence"),
                      ("PR-0003", "nothing has approved this work")):
        command = "git merge %sfeat/%s-x%s" % (quote, item, quote)
        result = run_hook_process("gate_git.py", _bash(prd_repo, command), prd_repo)
        assert result.returncode == 2, command
        assert item in result.stderr and why in result.stderr, (command, result.stderr)


def test_gate_git_still_drops_a_hash_that_only_looks_like_a_comment(prd_repo):
    """The cost of keeping quoted text: a `#` inside a message must not cut the line.

    The comment rule and the quoting rule meet here. Once the quote MARKS are gone, `-m "fix #3"`
    ends in something that reads like the start of a shell comment, and cutting there would drop
    the ref that follows — turning the fix for the quoted ref into a new way to unbind the gate.
    So the two are decided in one pass over the text (`_compat.git_argument_text`), and only a `#`
    seen outside quotes opens a comment.
    """
    capture_root_item(prd_repo, dict(PR_FIELDS, title="Second"))   # PR-0002, no evidence
    capture_evidence(prd_repo, result="pass", related=("PR-0001",))
    result = run_hook_process(
        "gate_git.py", _bash(prd_repo, 'git merge -m "fix #3 in the flow" feat/PR-0002-x'),
        prd_repo)
    assert result.returncode == 2
    assert "PR-0002" in result.stderr


def test_gate_git_widens_to_the_whole_line_when_the_ref_is_a_shell_variable(prd_repo):
    """A ref the shell builds at run time is unreadable, and unreadable is not "names nothing".

    `B=feat/PR-0002-x; git merge "$B"` passed the gate before: the merge segment holds only `$B`,
    so the command "named no item" and fell through to the store-wide question, which only asks
    whether something is currently FAILING — and an item with no evidence at all is not failing.
    The counter-assertion is the second half: widening must not turn every scripted ref into a
    block, so the same expansion with nothing else on the line still merges.
    """
    capture_root_item(prd_repo, dict(PR_FIELDS, title="Second"))   # PR-0002, no evidence
    capture_evidence(prd_repo, result="pass", related=("PR-0001",))
    result = run_hook_process("gate_git.py",
                              _bash(prd_repo, 'B=feat/PR-0002-x; git merge "$B"'), prd_repo)
    assert result.returncode == 2
    assert "PR-0002" in result.stderr
    assert run_hook("gate_git.py", _bash(prd_repo, 'git merge "$B"'), prd_repo) == 0


def test_gate_git_sees_a_command_split_over_a_line_continuation(prd_repo):
    """`\\`+newline is the shell joining two lines, and the gate has to join them too.

    Measured before the fix: `git \\<newline>  merge feat/PR-0001-x` matched no git gate at all —
    the applicability pattern of every one of them stops at a newline, correctly, because an
    unescaped newline really does end a command. So this was not a weaker judgement, it was the
    whole merge gate switched off by two characters, force-push ban included. Both are asserted
    because they refuse at different points and the second is the one no project state can lift.
    """
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    merged = run_hook_process("gate_git.py",
                              _bash(prd_repo, "git \\\n  merge feat/PR-0001-x"), prd_repo)
    assert merged.returncode == 2
    assert "PR-0001" in merged.stderr
    forced = run_hook_process("gate_git.py",
                              _bash(prd_repo, "git \\\n  push --force origin main"), prd_repo)
    assert forced.returncode == 2
    assert "force-push" in forced.stderr


@pytest.mark.parametrize("command,expected", [
    ('git "push" --force origin main', "force-push"),
    ("git pu''sh --force origin main", "force-push"),
    ('git "push" origin main', "PR-0001"),
    ('git "merge" feat/PR-0001-x', "PR-0001"),
    ('"git" push --force origin main', "force-push"),
])
def test_gate_git_reads_a_quoted_verb_as_the_verb_it_is(prd_repo, command, expected):
    """Two quote characters used to switch this whole layer off.

    Measured in a scaffolded project against all eight PreToolUse(Bash) hooks: `git push --force
    origin main` was refused by four of them and `git "push" --force origin main` by NONE — the
    applicability reader deleted quoted spans as prose, and the span it deleted held the VERB. So
    "force-push is always forbidden" cost two keystrokes to lift, and the evidence, pipeline,
    coverage and push-token gates went with it. `git pu''sh` is the same hole from the other end:
    the shell closes the word back up, and a reader that replaces a quote mark with a SPACE does
    not. `"git" push` is the third: there the quoted word is the command itself.

    The fix is a definition — applicability is read off the git SUBCOMMAND — so this asserts the
    two teeth that no project state can lift or fake: the unconditional force-push ban, and the
    QA-evidence tooth naming the failing item.
    """
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    result = run_hook_process("gate_git.py", _bash(prd_repo, command), prd_repo)
    assert result.returncode == 2, command
    assert expected in result.stderr, (command, result.stderr)


@pytest.mark.parametrize("command,expected", [
    ("git push --f\\\norce origin main", "force-push"),
    ("git mer\\\nge feat/PR-0001-x", "PR-0001"),
    ("git pu\\\nsh origin main", "PR-0001"),
    ("git pu`\nsh --force origin main", "force-push"),
])
def test_gate_git_sees_a_continuation_inside_a_token(prd_repo, command, expected):
    """The shell removes `\\`+newline with NOTHING in its place; the reader inserted a SPACE.

    Between two tokens the difference does not show (`git \\<newline> merge x` reads correctly
    either way, which is why the continuation test written one round earlier stayed green). INSIDE
    a token it is the whole gate: `--f\\<newline>orce` became `--f orce` and the force-push ban
    matched nothing, `mer\\<newline>ge` became `mer ge` and the merge gate did not apply at all.
    The PowerShell spelling (backtick+newline) is the same rule and was equally blind.
    """
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    result = run_hook_process("gate_git.py", _bash(prd_repo, command), prd_repo)
    assert result.returncode == 2, command
    assert expected in result.stderr, (command, result.stderr)


@pytest.mark.parametrize("command,expected", [
    ("git push>/dev/null --force origin main", "force-push"),
    ("git push</dev/null --force origin main", "force-push"),
    ("git >/dev/null push --force origin main", "force-push"),
    ("git>/dev/null push --force origin main", "force-push"),
    ('git "push">/dev/null --force origin main', "force-push"),
    ("git push>/dev/null origin main", "PR-0001"),
    ("git merge>/dev/null feat/PR-0001-x", "PR-0001"),
    ("git merge feat/PR-0001-x>/dev/null", "PR-0001"),
])
def test_gate_git_reads_a_redirection_as_shell_syntax(prd_repo, command, expected):
    """One `>` used to switch this whole layer off — half a keystroke less than the two quotes.

    The word reader answered for `& | ; ( )` and not for `< >`, although a shell ends a word at all
    ten of its metacharacters. So `push>/dev/null` came back as the SUBCOMMAND, which is no git
    command at all, and applicability — which is now correctly a question about the subcommand —
    answered no for every git gate at once. Measured as real hook processes in a scaffolded
    project: force-push ban, evidence, pipeline, coverage, packaging, push-token and hygiene gate
    all silent. `git>/dev/null push` is the same gap on the other word: with the operator inside
    it, `git` no longer ENDS a word, so the line invoked nothing.

    This is the direction a rebuild must never take — a class the old spelling-based reader still
    caught, lost by the definition that replaced it — which is why it is asserted on the two teeth
    no project state can lift: the unconditional force-push ban and the QA-evidence tooth.
    """
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    result = run_hook_process("gate_git.py", _bash(prd_repo, command), prd_repo)
    assert result.returncode == 2, command
    assert expected in result.stderr, (command, result.stderr)


@pytest.mark.parametrize("command", [
    'git commit -m "merge later"',
    'git commit -m "docs: git push blocked by gate defect"',
])
def test_gate_git_still_reads_a_commit_message_as_a_message(prd_repo, command):
    """THE COUNTER-ASSERTION, and the reason the broken design was chosen in the first place.

    Keeping quoted spans is what closes the bypass above; reading them as commands would rebuild
    the incident that produced the prose-stripping — a diagnosis commit ABOUT a blocked push
    re-triggering every push gate. Both halves hold now because the reader answers a different
    question: `merge` is not the first non-option token after `git`, so this is a commit; and the
    `git` inside the message is quoted text at an argument position, so it opens no invocation.
    The repo is left with a FAILING verdict on purpose — if either half slipped, this would block.
    """
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    result = run_hook_process("gate_git.py", _bash(prd_repo, command), prd_repo)
    assert result.returncode == 0, (command, result.stderr)


@pytest.mark.parametrize("command,expected", [
    ('sudo "git" push --force origin main', "force-push"),
    ('env "git" push --force origin main', "force-push"),
    ('nohup "git" push --force origin main', "force-push"),
    ('command "git" push --force origin main', "force-push"),
    ('timeout 30 "git" push --force origin main', "force-push"),
    ('sudo "g"it push --force origin main', "force-push"),
    ('sudo "git" merge feat/PR-0001-x', "PR-0001"),
])
def test_gate_git_does_not_care_what_word_stands_in_front_of_git(prd_repo, command, expected):
    """The quoted-verb fix, one word further along — and it was measured, not imagined.

    The first repair asked whether a quoted `git` was the segment's own COMMAND word, which is a
    question about POSITION: put any word that itself runs a command in front, and the quoted
    `git` sits past that offset and is discarded as prose again. Measured as real hook processes
    against all eight PreToolUse hooks, `sudo "git" push --force origin main` was ALLOWED by every
    one of them, as were `env`, `nohup`, `command` and `timeout` — the same five characters buying
    back the same total bypass. `sudo "g"it` is the second half: only the FIRST character of the
    word was tested for quoting.

    The definition that replaces it is about WORDS, not positions: `git` names the program when it
    ENDS a shell word, whatever precedes the word and whatever quoting is sprinkled through it.
    """
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    result = run_hook_process("gate_git.py", _bash(prd_repo, command), prd_repo)
    assert result.returncode == 2, command
    assert expected in result.stderr, (command, result.stderr)


@pytest.mark.parametrize("command,expected", [
    ("git push --for`ce origin main", "force-push"),
    ("git pu`sh --force origin main", "force-push"),
    ("git `push --force origin main", "force-push"),
    ("git mer`ge feat/PR-0001-x", "PR-0001"),
])
def test_gate_git_reads_the_powershell_escape_on_the_powershell_tool(prd_repo, command, expected):
    """PowerShell escapes with a backtick, and this gate is registered on the PowerShell tool.

    `SHELL_TOOLS`/`test_gate_git_blocks_powershell_tool_too` establish that the second tool rail is
    gated on purpose; the reader knew the backtick for line CONTINUATIONS only. Verified against a
    real `powershell -File` run that prints its arguments: `git pu``sh` arrives as `push`,
    `git push --for``ce` as `--force`. Measured against the shipped hooks before the fix, with
    `tool_name: "PowerShell"`: the first line here left the unconditional force-push ban blind and
    the other three matched no git gate at all.

    Payloads are sent as the PowerShell TOOL, which is how they would really arrive.
    """
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    payload = {"tool_name": "PowerShell", "tool_input": {"command": command},
               "cwd": str(prd_repo)}
    result = run_hook_process("gate_git.py", payload, prd_repo)
    assert result.returncode == 2, command
    assert expected in result.stderr, (command, result.stderr)


@pytest.mark.parametrize("command,expected", [
    ("git --config-env a.b=C push --force origin main", "force-push"),
    ("git --attr-source HEAD push --force origin main", "force-push"),
    ("git --brand-new HEAD push --force origin main", "force-push"),
    ("git $'push' --force origin main", "force-push"),
    ("git $(echo push) --force origin main", "force-push"),
    ("V=push; git $V --force origin main", "force-push"),
])
def test_gate_git_is_not_switched_off_by_what_stands_between_git_and_its_verb(
        prd_repo, command, expected):
    """Applicability may not hang on an ENUMERATION of git's global options (house rule 1).

    `--config-env` and `--attr-source` take their value as a separate token exactly like `-c` and
    `-C` do (verified against git 2.47.1), and both were missing: the reader skipped the option and
    then read its VALUE as the verb, so `git --attr-source HEAD push --force origin main` had the
    subcommand `head` and was ALLOWED by all eight hooks. Adding two names would only move the
    hole to the next option git ships, so an option the reader does not know (`--brand-new`) now
    makes the following token AMBIGUOUS and both readings count.

    The last three are the same failure from the other side: a verb the shell builds at run time is
    UNKNOWN, and an unconditional ban has to treat unknown as "could be this one".
    """
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    result = run_hook_process("gate_git.py", _bash(prd_repo, command), prd_repo)
    assert result.returncode == 2, command
    assert expected in result.stderr, (command, result.stderr)


def test_gate_git_answers_a_command_built_to_outlast_its_budget(prd_repo):
    """A hook the host KILLS has allowed the call — the repo's own words, and the reason
    `gate_ledger_valid` carries a TOTAL_BUDGET.

    The reader sliced the remainder of the segment out once per `git` word, so a line of `git `
    words cost quadratic time with the real command hidden at the end of it. Measured as real hook
    processes: 120 KB — 0.7 % of the 16 MiB `STDIN_LIMIT` accepts — took `gate_git` 125.7 s and
    `gate_push_token` 59.6 s, past the 60 s the host allows either of them. `run_hook_process`
    caps the subprocess at 60 s too, so the old code cannot make this test pass at all: it raises
    TimeoutExpired instead.
    """
    payload = ": " + "git " * 30000 + "&& git push --force origin main"
    assert len(payload) > 100 * 1024
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    result = run_hook_process("gate_git.py", _bash(prd_repo, payload), prd_repo)
    assert result.returncode == 2
    assert "force-push" in result.stderr


def test_gate_pipeline_applies_to_a_quoted_verb_too(tmp_path):
    """The bypass was in the SHARED reader, so it disarmed every gate that asks the same question.

    gate_git is checked above; this is the second consumer, and it is the one that proves the fix
    landed in `_compat.wants_push_or_merge` rather than in one hook. Its own prose counter-case
    lives in `test_gate_pipeline_ignores_prose_push_mentions`.
    """
    capture_root_item(tmp_path)
    for command in ('git "push" origin main', "git pu\\\nsh origin main"):
        result = run_hook_process("gate_pipeline.py", _bash(tmp_path, command), tmp_path)
        assert result.returncode == 2, command
        assert "no quality pipeline" in result.stderr, (command, result.stderr)


def _git_repo_on_branch(repo, branch):
    """A real git repo with one commit, standing on `branch` — the branch fallback needs one."""
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@e")
    subprocess.run(["git", "init", "-q", "-b", branch], cwd=str(repo), capture_output=True,
                   timeout=30, env=env)
    write(os.path.join(str(repo), "README.md"), "x\n")
    subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True, timeout=30, env=env)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=str(repo), capture_output=True,
                   timeout=30, env=env)


def test_gate_git_reads_the_branch_only_when_the_command_names_nothing(prd_repo):
    """The command wins over the branch, and the branch is read at all.

    Both halves in one test because each alone is passable by the wrong implementation: reading
    the branch first would judge PR-0002 for `git merge feat/PR-0001-x` (measured green with the
    order reversed), and never reading it would leave `git push` on a named branch unbound.
    """
    capture_root_item(prd_repo, dict(PR_FIELDS, title="Second"))   # PR-0002
    _git_repo_on_branch(prd_repo, "feat/PR-0002-x")
    capture_evidence(prd_repo, result="pass", related=("PR-0002",))
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    named = run_hook_process("gate_git.py", _bash(prd_repo, "git merge feat/PR-0001-x"), prd_repo)
    assert named.returncode == 2 and "PR-0001" in named.stderr
    assert run_hook("gate_git.py", _bash(prd_repo, "git push origin HEAD"), prd_repo) == 0


def test_gate_git_an_unnamed_branch_does_not_inherit_another_items_pass(prd_repo):
    """A merge that binds to nothing is judged against every OPEN failure, not the newest verdict.

    Measured before the fix: with PR-0001 failing and PR-0002 passing, `git merge feat/rechnungen`
    and `git push origin main` were both allowed, because the store collapsed to one newest-per-
    kind and the newest happened to be green. That is the V1 file-level false accept rebuilt out
    of typed items, and the push to `main` is the case where a red QA matters most.
    """
    capture_root_item(prd_repo, dict(PR_FIELDS, title="Second"))   # PR-0002
    capture_evidence(prd_repo, result="fail", related=("PR-0001",))
    capture_evidence(prd_repo, result="pass", related=("PR-0002",))
    for command in ("git merge feat/rechnungen", "git push origin main"):
        result = run_hook_process("gate_git.py", _bash(prd_repo, command), prd_repo)
        assert result.returncode == 2, command
        assert "PR-0001" in result.stderr, command
    # ...and the counter-direction: with nothing failing, an unnamed branch still merges
    capture_evidence(prd_repo, result="pass", related=("PR-0001",))
    assert run_hook("gate_git.py", _bash(prd_repo, "git merge feat/rechnungen"), prd_repo) == 0


# ---------------- gate_git: the item's own status (disposition rows 115/343) ---------------------
@pytest.mark.parametrize("status,expected", [
    ("DRAFT", 2),        # the automaton's initial status: nothing approved this work
    ("REJECTED", 2),     # terminal OFF the chain: the project dropped it
    ("SUPERSEDED", 2),
    ("IN_DELIVERY", 0),  # mid-chain: exactly what a merge delivers
    ("DELIVERED", 0),
    ("ACCEPTED", 0),     # the chain's own end: a later fix merged against it is legitimate
])
def test_gate_git_judges_the_merged_items_status_against_its_own_automaton(tmp_path, status,
                                                                           expected):
    """"Branch↔item + a status appropriate to the TYPE" — the second half of the disposition row.

    Which statuses those are is read off `AUTOMATA[type]` rather than listed in the hook, so the
    rule travels with a kit that adds a root type. Passing evidence is recorded in every case, so
    a block here can only come from the status and an allow only from both teeth agreeing.
    """
    capture_root_item(tmp_path, status=status)
    capture_evidence(tmp_path, result="pass")
    assert run_hook("gate_git.py", _merge(tmp_path), tmp_path) == expected


# ---------------- gate_subagent_output: honors stop_hook_active (no infinite block loop) ----------------
def test_subagent_output_gives_up_on_stop_hook_active(kit_repo):
    (kit_repo / "project_memory").mkdir(exist_ok=True)
    payload = {"hook_event_name": "SubagentStop", "agent_type": "backend-developer",
               "last_assistant_message": "still just prose", "stop_hook_active": True,
               "cwd": str(kit_repo)}
    assert run_hook("gate_subagent_output.py", payload, kit_repo) == 0
    audit = kit_repo / "project_memory" / ".audit" / "hook_events.jsonl"
    assert "gave_up" in audit.read_text(encoding="utf-8")


# ---------------- office fs tripwire: shell redirects into the ledger are blocked ----------------
def test_office_business_profile_records_provider_and_preserves_legacy_key():
    yaml = pytest.importorskip("yaml")
    text = open(OFFICE_PROFILE, encoding="utf-8").read()
    privacy = yaml.safe_load(text)["privacy"]
    assert {"provider", "account_type", "claude_account_type"} <= set(privacy)
    assert "LEGACY" in text and "provider=claude" in text


def test_fs_tripwire_blocks_ledger_redirect(tmp_path):
    payload = {"tool_name": "Bash",
               "tool_input": {"command": 'echo "L1,2026-01-01,..." >> ledger/2026.csv'},
               "cwd": str(tmp_path)}
    assert run_hook("guard_fs_tripwire.py", payload, tmp_path, hooks_dir=OFFICE_HOOKS) == 2


def test_fs_tripwire_allows_ledger_add_script(tmp_path):
    payload = {"tool_name": "Bash",
               "tool_input": {"command": "python scripts/ledger_add.py --year 2026 --net 1 > /tmp/log"},
               "cwd": str(tmp_path)}
    assert run_hook("guard_fs_tripwire.py", payload, tmp_path, hooks_dir=OFFICE_HOOKS) == 0


# ---------------- _root: Windows drive-letter case normalization ----------------
def test_root_normalizes_windows_drive_case(tmp_path, monkeypatch):
    if os.name != "nt":
        pytest.skip("drive-letter casing is a Windows concept")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "root_under_test", os.path.join(HOOKS, "_root.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    (tmp_path / ".claude").mkdir()
    lower = str(tmp_path)[0].lower() + str(tmp_path)[1:]
    # env path (CLAUDE_PROJECT_DIR) and walk-up path both normalize the drive letter:
    # a lowercase c:\ cwd broke vite/rollup ONLY inside the hook subprocess chain (real
    # overnight incident); direct comparison runs were silently msys-normalized.
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", lower)
    assert mod.find_repo_root()[0] == str(tmp_path)[0].upper()
    monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    result = mod.find_repo_root(os.path.join(lower, "sub"))
    assert result[0] == str(tmp_path)[0].upper()


# ---------------- gate detection: prose mentions of push/merge must not trigger ----------------
def test_gate_pipeline_ignores_prose_push_mentions(tmp_path):
    capture_root_item(tmp_path)
    # a commit message DESCRIBING a push must not run the pipeline (real incident:
    # the diagnosis commit about a blocked push triggered the full RED pipeline again)
    prose = {"tool_name": "Bash", "cwd": str(tmp_path),
             "tool_input": {"command": 'git commit -m "docs: git push blocked by gate defect"'}}
    assert run_hook("gate_pipeline.py", prose, tmp_path) == 0
    # a REAL push still gates (no scripts/quality.py here -> hard block)
    push = {"tool_name": "Bash", "cwd": str(tmp_path),
            "tool_input": {"command": "git push origin main"}}
    r = run_hook_process("gate_pipeline.py", push, tmp_path)
    assert r.returncode == 2 and "no quality pipeline" in r.stderr


def test_gate_git_force_check_survives_quote_stripping(tmp_path):
    blocked = {"tool_name": "Bash", "cwd": str(tmp_path),
               "tool_input": {"command": "git push origin main --force"}}
    r = run_hook_process("gate_git.py", blocked, tmp_path)
    assert r.returncode == 2 and "force-push" in r.stderr
    prose = {"tool_name": "Bash", "cwd": str(tmp_path),
             "tool_input": {"command": 'git commit -m "never use git push --force"'}}
    assert run_hook("gate_git.py", prose, tmp_path) == 0
    # audit findings: QUOTED force flags reach git after the shell strips the quotes —
    # hiding them in quotes must not disarm the always-forbidden ban
    for command in ('git push "--force" origin main', 'git push origin "+main"'):
        payload = {"tool_name": "Bash", "cwd": str(tmp_path),
                   "tool_input": {"command": command}}
        r = run_hook_process("gate_git.py", payload, tmp_path)
        assert r.returncode == 2 and "force-push" in r.stderr, command


def test_gates_catch_shell_wrapped_push(tmp_path):
    # audit finding (regression vs the old substring check): a push inside a shell WRAPPER
    # payload is CODE and must gate — plain quote-stripping had let it pass both gates
    capture_root_item(tmp_path)
    for command in ('bash -c "git push origin main"',
                    "powershell -Command 'git push origin main'",
                    'powershell -NoProfile -Command "git push origin main"',
                    'cmd /c "git merge feature"'):
        payload = {"tool_name": "Bash", "cwd": str(tmp_path),
                   "tool_input": {"command": command}}
        r = run_hook_process("gate_pipeline.py", payload, tmp_path)
        assert r.returncode == 2 and "no quality pipeline" in r.stderr, command
    # the fixed prose incident stays fixed
    prose = {"tool_name": "Bash", "cwd": str(tmp_path),
             "tool_input": {"command": 'git commit -m "docs: git push blocked by gate defect"'}}
    assert run_hook("gate_pipeline.py", prose, tmp_path) == 0


def test_gates_catch_combined_flag_wrappers(tmp_path):
    # audit finding (MAJOR): `bash -lc "git push --force"` bypassed EVERY git gate — the
    # wrapper regex required -c as its OWN token, so a combined short cluster unwrapped
    # nothing and the payload was then stripped as prose. Escaped quotes inside the payload
    # must not cut the unwrap short either.
    capture_root_item(tmp_path)
    for command in ('bash -lc "git push origin main"',
                    'bash -xec "git push origin main"',
                    "sh -euc 'git merge feature'",
                    'bash -c "echo \\"done\\" && git push origin main"'):
        payload = {"tool_name": "Bash", "cwd": str(tmp_path),
                   "tool_input": {"command": command}}
        r = run_hook_process("gate_pipeline.py", payload, tmp_path)
        assert r.returncode == 2 and "no quality pipeline" in r.stderr, command
    forced = {"tool_name": "Bash", "cwd": str(tmp_path),
              "tool_input": {"command": 'bash -lc "git push --force origin main"'}}
    r = run_hook_process("gate_git.py", forced, tmp_path)
    assert r.returncode == 2 and "force-push" in r.stderr


def test_source_areas_reject_dot_names(tmp_path):
    # audit finding (both auditors, MAJOR): '..' passed the area filter and os.walk escaped
    # the repo into NEIGHBOR projects (a sibling's file failed OUR budget). Dot-only names
    # must never become scan areas — in the budget, the coverage gate and the dashboard.
    mod = _kit_checks_mod()
    repo = tmp_path / "repo"
    write(str(tmp_path / "neighbor" / "big.py"), "x = 1\n" * 900)
    capture_invariant(repo, "..", text="a scope that would walk out of the repo")
    capture_invariant(repo, ".", text="and one that names the repo root itself")
    calls, ok, fail, warn = _collector()
    mod.check_file_budget(str(repo), ok, fail, warn)
    assert not any("neighbor" in m for _n, m in calls["fail"])  # never scans outside the repo
    assert any("NO scan area matched" in m for _n, m in calls["warn"])


def test_gate_test_coverage_rejects_dot_areas(tmp_path):
    repo = tmp_path / "repo"
    write(str(tmp_path / "stray.py"), "def f():\n    return 1\n")  # code OUTSIDE the repo
    capture_root_item(repo)
    capture_invariant(repo, "..", text="a scope that would walk out of the repo")
    payload = {"tool_name": "Bash", "cwd": str(repo),
               "tool_input": {"command": "git push origin main"}}
    assert run_hook("gate_test_coverage.py", payload, repo) == 0  # '..' is ignored, no block


# ---------------- provider compat: Codex apply_patch payloads ----------------
def _codex_patch(*files):
    body = "".join("*** Update File: %s\n@@\n-x\n+y\n" % f for f in files)
    return "*** Begin Patch\n" + body + "*** End Patch"


def test_selfmod_blocks_codex_apply_patch(tmp_path):
    payload = {"tool_name": "apply_patch",
               "tool_input": {"command": _codex_patch(".claude/hooks/gate_git.py")},
               "cwd": str(tmp_path)}
    assert run_hook("guard_harness_selfmod.py", payload, tmp_path) == 2


@pytest.mark.parametrize("rel", [
    ".codex/config.toml",
    ".agents/skills/project-manager/SKILL.md",
    ".claude/provider_artifacts.json",
    ".claude/team_kit_roles.txt",
])
def test_selfmod_blocks_codex_provider_artifact_patch(tmp_path, rel):
    payload = {"tool_name": "apply_patch",
               "tool_input": {"command": _codex_patch(rel)},
               "cwd": str(tmp_path)}
    assert run_hook("guard_harness_selfmod.py", payload, tmp_path) == 2, rel


def test_pm_scope_blocks_codex_multifile_patch(tmp_path):
    # first file allowed, SECOND file in the same patch is production code -> must still block
    payload = {"tool_name": "apply_patch",
               "tool_input": {"command": _codex_patch("docs/notes.md", "src/main.py")},
               "cwd": str(tmp_path)}
    assert run_hook("guard_pm_scope.py", payload, tmp_path) == 2


def test_no_adhoc_blocks_codex_added_dump_file(tmp_path):
    patch = "*** Begin Patch\n*** Add File: final_report.md\n+x\n*** End Patch"
    payload = {"tool_name": "apply_patch", "tool_input": {"command": patch}, "cwd": str(tmp_path)}
    assert run_hook("guard_no_adhoc.py", payload, tmp_path) == 2


def test_no_adhoc_allows_codex_update_of_existing_dump_name(tmp_path):
    patch = "*** Begin Patch\n*** Update File: final_report.md\n@@\n-x\n+y\n*** End Patch"
    payload = {"tool_name": "apply_patch", "tool_input": {"command": patch}, "cwd": str(tmp_path)}
    assert run_hook("guard_no_adhoc.py", payload, tmp_path) == 0


def test_no_adhoc_blocks_codex_move_to_dump_name(tmp_path):
    patch = ("*** Begin Patch\n*** Update File: docs/notes.md\n*** Move to: final_report.md\n"
             "@@\n-x\n+y\n*** End Patch")
    payload = {"tool_name": "apply_patch", "tool_input": {"command": patch}, "cwd": str(tmp_path)}
    assert run_hook("guard_no_adhoc.py", payload, tmp_path) == 2


def hook_constant(hook_file, name, hooks_dir=None):
    """The value of a module-level literal constant in a hook, read WITHOUT importing the hook.

    Reading the assignment that actually runs is the point (a docstring-satisfied test proves
    nothing), but executing the module for it is too expensive a side effect for a test process:
    it puts a kit's `hooks/` on `sys.path` for good and runs `_compat`'s stream pinning as an
    import effect, making later tests depend on collection order. `ast.literal_eval` on the
    parsed assignment reads the same line with none of that.
    """
    path = os.path.join(hooks_dir or HOOKS, hook_file)
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else []
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            return ast.literal_eval(node.value)
    raise AssertionError("%s does not define %s at module level" % (hook_file, name))


def test_no_adhoc_covers_every_item_type(tmp_path):
    """The guard names the item prefixes literally (it must decide without loading the kernel), so
    the list is only safe while something proves it complete. Adding a type to ACTIVE_DIRS without
    it would let `<NEWTYPE>-0001_notes.md` past the rule that exists for exactly that file."""
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ACTIVE_DIRS, V1_STATUS_MAPPING
    item_types = hook_constant("guard_no_adhoc.py", "ITEM_TYPES")
    legacy_types = hook_constant("guard_no_adhoc.py", "LEGACY_ITEM_TYPES")
    assert set(item_types) == {t.lower() for t in ACTIVE_DIRS}
    # LEGACY_ITEM_TYPES was the one prefix list with nothing behind it. The V1 vocabulary the
    # migration table still translates is a real source for part of it: every type a migrated
    # project can carry must be a prefix this guard knows, current or legacy.
    assert {v1_type.lower() for v1_type, _ in V1_STATUS_MAPPING} <= set(item_types) | set(
        legacy_types)
    # ...and the pattern really rejects a file named after the newest of them. Run the guard, do
    # not re-derive its regex here: a second construction of the pattern would pass while the
    # shipped one is broken.
    newest = sorted(ACTIVE_DIRS)[-1].lower()
    payload = {"tool_name": "Write", "cwd": str(tmp_path),
               "tool_input": {"file_path": str(tmp_path / "docs" / ("%s-0001_notes.md" % newest))}}
    assert run_hook("guard_no_adhoc.py", payload, tmp_path) == 2


def test_no_adhoc_leaves_a_note_that_only_looks_like_an_item_id_alone(tmp_path):
    """The rule is "named after a KERNEL ITEM ID", and the kernel mints `<TYPE>-<4+ digits>`
    (`backlog_types._ID_RE`). Matching on `<type>-<any digit>` widened the guard over ordinary
    notes — `bug-42.md`, `fr-1.md` — which the docstring's "never block legitimate work" forbids.
    A name that IS a valid item id stays blocked: that collision is what the rule is for."""
    for name, expected in (("bug-42.md", 0), ("fr-1.md", 0), ("bug-0042.md", 2)):
        payload = {"tool_name": "Write", "cwd": str(tmp_path),
                   "tool_input": {"file_path": str(tmp_path / "docs" / name)}}
        assert run_hook("guard_no_adhoc.py", payload, tmp_path) == expected, name


def test_root_item_globs_are_the_kernels_root_types():
    """`_root.ROOT_ITEM_GLOBS` spells out directories the kernel already owns. The literal is
    deliberate — `has_root_item` runs on every guarded shell command and must not import the
    kernel to answer "does an item exist" — but a cache without a proof is just a second list, and
    this repo has produced one defect per unproven list. Same pattern as guard_no_adhoc.ITEM_TYPES,
    which is why the exception was inconsistent rather than justified."""
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ACTIVE_DIRS, ROOT_TYPE_BY_KIT
    assert set(hook_constant("_root.py", "ROOT_ITEM_GLOBS")) == {
        "%s/%s-*.yaml" % (ACTIVE_DIRS[t], t) for t in set(ROOT_TYPE_BY_KIT.values())}


def test_root_item_types_are_the_same_root_types_seen_from_the_id_side():
    """`gate_git` matches a root id in a branch name; `has_root_item` matches a file on disk.

    One fact, two views — so `ROOT_ITEM_TYPES` is derived from the globs rather than typed out
    again. Proven against the kernel and not merely against the globs, because deriving from a
    wrong list would still agree with itself: a kit that gains a root type must reach BOTH the
    filesystem question and the merge gate, and this is what fails if only one of them moves.

    Read by IMPORTING the helper, not by `ast.literal_eval` like its sibling above: the value is
    computed from the globs, so the only honest way to ask what it is is to let it be computed."""
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ROOT_TYPE_BY_KIT
    module = conftest.load_kit_module(
        "_root_under_test", os.path.join(ROOT, "team-kits", "dev-team", "hooks", "_root.py"))
    assert set(module.ROOT_ITEM_TYPES) == set(ROOT_TYPE_BY_KIT.values())


def test_pm_scope_blocks_lowercase_tool_alias(tmp_path):
    # non-Claude payloads may use lowercase tool names; _TOOL_ALIASES must normalize them
    payload = {"tool_name": "edit", "tool_input": {"file_path": str(tmp_path / "src" / "x.py")},
               "cwd": str(tmp_path)}
    assert run_hook("guard_pm_scope.py", payload, tmp_path) == 2


def test_selfmod_blocks_constitution_and_shim(tmp_path):
    for name in ("AGENTS.md", "CLAUDE.md"):
        payload = {"tool_name": "Edit", "tool_input": {"file_path": str(tmp_path / name)},
                   "cwd": str(tmp_path)}
        assert run_hook("guard_harness_selfmod.py", payload, tmp_path) == 2, name


def test_selfmod_blocks_settings_local_and_case_bypass(tmp_path):
    for rel in (".claude/settings.local.json", ".CLAUDE/hooks/gate_git.py"):
        payload = {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / rel)},
                   "cwd": str(tmp_path)}
        assert run_hook("guard_harness_selfmod.py", payload, tmp_path) == 2, rel


# ---------------- kit_checks: secure-context false positives + honest truncation ----------------
def _kit_checks_mod():
    return load_kit_module("kit_checks_under_test", KIT_CHECKS)


def _collector():
    calls = {"ok": [], "fail": [], "warn": []}
    return (calls, lambda n, *a: calls["ok"].append(n),
            lambda n, m: calls["fail"].append((n, m)),
            lambda n, m: calls["warn"].append((n, m)))


def test_file_budget_source_areas_extend_and_warn(tmp_path):
    # false-green killer: a project keeping its whole codebase under an UNLISTED top-level
    # package was never scanned ("PASS file budget" with an 1,111-line file undetected)
    mod = _kit_checks_mod()
    write(str(tmp_path / "compounder" / "big.py"), "x = 1\n" * 900)
    calls, ok, fail, warn = _collector()
    mod.check_file_budget(str(tmp_path), ok, fail, warn)
    assert not calls["fail"] and not calls["ok"]
    assert any("NO scan area matched" in m for _n, m in calls["warn"])  # never silent
    capture_invariant(tmp_path, "compounder/", text="every module here stays import-free")
    calls, ok, fail, warn = _collector()
    mod.check_file_budget(str(tmp_path), ok, fail, warn)
    assert any("compounder/big.py" in m for _n, m in calls["fail"])


def test_yaml_lint_skips_the_frozen_archive(tmp_path):
    """`project_memory/archive/` is excluded from the recursive lint on purpose: an archived item is
    frozen (it was linted while active, nothing may write it again, and the kernel's own validator
    does not scan it either), while the tree grows monotonically and this check runs on every merge
    with a cold CI read. Asserted as behaviour so the exclusion cannot silently become "everything"
    or "nothing" — the second half proves the walk still reaches an active item."""
    pytest.importorskip("yaml")
    mod = _kit_checks_mod()
    write(str(tmp_path / "project_memory" / "archive" / "PR" / "2025" / "PR-0009.yaml"),
          "a: [unclosed\n")
    calls, ok, fail, warn = _collector()
    mod.check_project_memory_yaml(str(tmp_path), ok, fail, warn)
    assert not calls["fail"], calls["fail"]
    write(str(tmp_path / "project_memory" / "product" / "active" / "PR-0001.yaml"), "a: [unclosed\n")
    calls, ok, fail, warn = _collector()
    mod.check_project_memory_yaml(str(tmp_path), ok, fail, warn)
    assert any("PR-0001" in m for _n, m in calls["fail"]), calls


def test_the_suite_leaves_no_bytecode_in_the_kit_tree():
    """tools/validate.py's principle: the suite must never create bytecode the installer could pick
    up. It had been implemented at ONE of three by-path loaders, and a `kit_checks.cpython-*.pyc`
    was measured appearing under the kit's scripts/ mid-run — from the other two AND from a plain
    `import kit_browser_checks` nobody had counted. So the guarantee is a redirected cache
    (`conftest.PYCACHE_DIR`), not a shielded call site, and this asserts the OUTCOME over the whole
    shipped tree rather than at the loaders it happens to know about."""
    assert sys.pycache_prefix == conftest.PYCACHE_DIR, "the cache redirection is gone"
    kit_tree = os.path.join(ROOT, "team-kits")
    for cache in _kit_bytecode_dirs(kit_tree):
        shutil.rmtree(cache, ignore_errors=True)
    _load_dashboard_module()
    _kit_checks_mod()
    leaked = _kit_bytecode_dirs(kit_tree)
    assert not leaked, "the suite wrote bytecode into the kit tree: %s" % leaked


def _kit_bytecode_dirs(tree):
    return sorted(os.path.join(dirpath, name)
                  for dirpath, dirnames, _files in os.walk(tree)
                  for name in dirnames if name == "__pycache__")


def test_ops_pitfalls_compose_name_pin(tmp_path):
    mod = _kit_checks_mod()
    write(str(tmp_path / "docker-compose.yml"), "services:\n  db:\n    image: postgres\n")
    calls, ok, fail, warn = _collector()
    mod.check_ops_pitfalls(str(tmp_path), ok, fail, warn)
    assert any("no top-level `name:`" in m for _n, m in calls["warn"])
    write(str(tmp_path / "docker-compose.yml"),
          "name: myproject\nservices:\n  db:\n    image: postgres\n")
    calls, ok, fail, warn = _collector()
    mod.check_ops_pitfalls(str(tmp_path), ok, fail, warn)
    assert not calls["warn"] and any("compose project name pinned" in n for n in calls["ok"])


def test_gate_test_coverage_declared_areas(tmp_path):
    capture_root_item(tmp_path)
    write(str(tmp_path / "compounder" / "core.py"), "def f():\n    return 1\n")
    payload = {"tool_name": "Bash", "cwd": str(tmp_path),
               "tool_input": {"command": "git push origin main"}}
    assert run_hook("gate_test_coverage.py", payload, tmp_path) == 0  # ungoverned -> old behavior
    capture_invariant(tmp_path, "compounder/", text="every module here is covered by tests")
    r = run_hook_process("gate_test_coverage.py", payload, tmp_path)
    assert r.returncode == 2 and "compounder" in r.stderr
    write(str(tmp_path / "compounder" / "test_core.py"), "def test_f():\n    assert True\n")
    assert run_hook("gate_test_coverage.py", payload, tmp_path) == 0


def _office_project(tmp_path):
    """An office repo with the shipped enforcement layer installed, as a scaffold leaves it.

    The kit scripts reach the kernel through `.claude/hooks/_kernel.py` (the one module that knows
    where the kernel lives), so a script test that ran without that bridge would measure the
    "no enforcement layer" branch instead of the script.
    """
    repo = tmp_path / "office"
    (repo / "scripts").mkdir(parents=True)
    for name in ("proc_hash.py", "process_doc.py"):
        shutil.copy(os.path.join(OFFICE_SCRIPTS, name), str(repo / "scripts" / name))
    ignore = shutil.ignore_patterns("__pycache__")
    shutil.copytree(OFFICE_HOOKS, str(repo / ".claude" / "hooks"), ignore=ignore)
    shutil.copytree(os.path.join(ROOT, "team-kits", "kernel"), str(repo / ".claude" / "kernel"),
                    ignore=ignore)
    return repo


def _run_office_script(repo, name, *args):
    return subprocess.run([sys.executable, str(repo / "scripts" / name), *args],
                          capture_output=True, text=True, timeout=120)


def test_proc_hash_reports_a_matching_stamp_and_can_no_longer_write_one(tmp_path):
    """The V1 script's `--update` was the hole, not a feature — so it is gone, measured as gone.

    "Run this to make the tamper check pass again" is the permission the check exists to withhold,
    and V1 shipped it with a docstring asking not to use it that way. The stamp now comes from
    `approvals.mint` and from nowhere else. Both halves are asserted: a freshly approved PROC
    verifies clean, and the old writing invocation neither writes nor succeeds.
    """
    pytest.importorskip("yaml")
    repo = _office_project(tmp_path)
    proc = capture_proc(repo)
    before = open(_office_state(repo).active_path(proc["id"]), encoding="utf-8").read()
    result = _run_office_script(repo, "proc_hash.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert proc["id"] in result.stdout and "APPROVED" in result.stdout
    update = _run_office_script(repo, "proc_hash.py", proc["id"], "--update")
    assert update.returncode == 2
    assert open(_office_state(repo).active_path(proc["id"]), encoding="utf-8").read() == before


def test_proc_hash_reports_a_stamp_that_no_longer_matches_its_procedure(tmp_path):
    yaml = pytest.importorskip("yaml")
    repo = _office_project(tmp_path)
    proc = capture_proc(repo)
    path = _office_state(repo).active_path(proc["id"])
    item = yaml.safe_load(open(path, encoding="utf-8").read())
    item["steps"].append("a step nobody approved")
    write(path, yaml.safe_dump(item, sort_keys=False, allow_unicode=True))
    result = _run_office_script(repo, "proc_hash.py")
    assert result.returncode == 1, result.stdout + result.stderr


def test_process_doc_renders_the_verfahrensdokumentation_from_the_proc_items(tmp_path):
    """The renderer used to raise FileNotFoundError in every project that installed it.

    A Verfahrensdokumentation nobody can generate is a GoBD obligation the kit claims to cover and
    does not, so the measurement is the file appearing with the procedure in it — not the exit code
    alone, which a script that wrote an empty document would also produce.
    """
    pytest.importorskip("yaml")
    repo = _office_project(tmp_path)
    proc = capture_proc(repo, steps=("open the post", "scan and file it"))
    write(str(repo / "project_memory" / "filing_plan.yaml"),
          "naming_rule: '{date}_{type}'\ntree:\n  - path: archive/belege\n    doc_types: [beleg]\n"
          "    retention: 10y\n")
    result = _run_office_script(repo, "process_doc.py")
    assert result.returncode == 0, result.stdout + result.stderr
    rendered = open(str(repo / "docs" / "verfahrensdokumentation.md"), encoding="utf-8").read()
    assert proc["id"] in rendered
    assert "scan and file it" in rendered
    assert "archive/belege" in rendered


def test_gate_pipeline_green_tree_cache(tmp_path):
    repo = tmp_path / "repo"
    runs = tmp_path / "runs.txt"           # OUTSIDE the repo: the counter must not dirty the tree
    capture_root_item(repo)
    write(str(repo / "scripts" / "quality.py"),
          "import pathlib\n"
          "p = pathlib.Path(r'%s')\n"
          "p.write_text(p.read_text() + 'x' if p.exists() else 'x')\n" % str(runs))
    # real projects gitignore the kit bookkeeping (template .gitignore) — without this the cache
    # file itself would count as an untracked change (the hook is deliberately conservative)
    write(str(repo / ".gitignore"), ".claude/.gate_pipeline_green\nproject_memory/.audit/\n")
    subprocess.run(["git", "init", "-q"], cwd=str(repo), capture_output=True, timeout=30)
    subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True, timeout=30)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "x"],
                   cwd=str(repo), capture_output=True, timeout=30)
    payload = {"tool_name": "Bash", "cwd": str(repo),
               "tool_input": {"command": "git push origin main"}}
    assert run_hook("gate_pipeline.py", payload, repo) == 0
    assert runs.read_text() == "x"          # pipeline ran once, green, cache written
    assert run_hook("gate_pipeline.py", payload, repo) == 0
    assert runs.read_text() == "x"          # identical clean tree -> cache hit, NOT rerun
    audit = (repo / "project_memory" / ".audit" / "hook_events.jsonl").read_text(encoding="utf-8")
    assert "cache_hit" in audit
    # a tree change invalidates the cache
    write(str(repo / "scripts" / "extra.py"), "y = 2\n")
    subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True, timeout=30)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "y"],
                   cwd=str(repo), capture_output=True, timeout=30)
    assert run_hook("gate_pipeline.py", payload, repo) == 0
    assert runs.read_text() == "xx"         # reran on the new tree
    # a DIRTY tree always runs (no cache read or write)
    write(str(repo / "scripts" / "extra.py"), "y = 3\n")
    assert run_hook("gate_pipeline.py", payload, repo) == 0
    assert runs.read_text() == "xxx"


def test_gate_memory_complete_escalates_on_repeat(tmp_path):
    capture_root_item(tmp_path)
    write(str(tmp_path / "project_memory" / "product" / "masterplan.md"),
          "# Masterplan — <project name>\nTODO\n")
    payload = {"tool_name": "Bash", "cwd": str(tmp_path),
               "tool_input": {"command": "git push origin main"}}
    outputs = []
    for _ in range(3):
        r = run_hook_process("gate_memory_complete.py", payload, tmp_path)
        assert r.returncode == 2
        outputs.append(r.stderr)
    assert "REPEAT BLOCK" not in outputs[0]
    assert "REPEAT BLOCK" in outputs[2]     # third identical block escalates


def test_gate_memory_complete_escalates_past_the_audit_reason_cap(tmp_path):
    """`REASON_KEY_CHARS` exists because `_audit` stores at most 2000 characters of a reason: a
    key longer than what was stored can never `startswith`-match it, and the escalation dies
    silently on exactly the noisy state it is for. Nothing bounds the message length — the item id
    is the part of a finding the STATE decides — so this drives it past the cap with long (still
    kernel-legal, `<TYPE>-<4+ digits>`) ids and requires the third block to escalate anyway."""
    capture_root_item(tmp_path)
    active = tmp_path / "project_memory" / "product" / "active"
    for i in range(2, 12):
        item_id = "PR-" + str(i).zfill(240)
        write(str(active / (item_id + ".yaml")), "id: %s\nstatus: DRAFT\ntitle: t\n" % item_id)
    payload = {"tool_name": "Bash", "cwd": str(tmp_path),
               "tool_input": {"command": "git push origin main"}}
    outputs = [run_hook_process("gate_memory_complete.py", payload, tmp_path).stderr
               for _ in range(3)]
    assert len(outputs[0]) > 2000            # the message really is past the cap
    assert "REPEAT BLOCK" in outputs[2]


def test_session_status_path_change_tripwire(tmp_path):
    # audit finding: the old absence-of-memory heuristic false-fired on every mature project
    # without auto-memory (opt-in). The replacement is deterministic: a recorded path that
    # differs from the current one. First run records SILENTLY, a changed record warns.
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    payload = {"hook_event_name": "SessionStart", "cwd": str(repo)}
    r = run_hook_process("session_status.py", payload, repo)
    assert "PROJECT PATH CHANGED" not in r.stdout      # first run: record only, no nag
    state = repo / ".claude" / "project_path.state"
    assert state.read_text().strip() == os.path.abspath(str(repo))
    r2 = run_hook_process("session_status.py", payload, repo)
    assert "PROJECT PATH CHANGED" not in r2.stdout     # unchanged path: stays silent
    old = os.path.abspath(str(tmp_path / "old-name"))
    state.write_text(old + "\n")                       # simulate a folder rename
    r3 = run_hook_process("session_status.py", payload, repo)
    assert "PROJECT PATH CHANGED" in r3.stdout and "old-name" in r3.stdout
    assert state.read_text().strip() == os.path.abspath(str(repo))  # re-recorded after warning


def test_secure_context_skips_test_files_and_comment_lines(tmp_path):
    write(str(tmp_path / "frontend" / "src" / "App.test.tsx"),
          "navigator.clipboard.writeText = vi.fn()\n")
    write(str(tmp_path / "frontend" / "src" / "notes.ts"),
          "// navigator.clipboard is wrapped by copyText()\nconst a = 1\n")
    write(str(tmp_path / "frontend" / "src" / "bad.ts"),
          "navigator.clipboard.writeText(text)\n")
    calls, ok, fail, warn = _collector()
    _kit_checks_mod().check_frontend_pitfalls(str(tmp_path), ok, fail, warn)
    assert len(calls["fail"]) == 1
    msg = calls["fail"][0][1]
    assert "bad.ts" in msg and "App.test.tsx" not in msg and "notes.ts" not in msg


def test_kit_checks_truncation_reports_hidden_count(tmp_path):
    for i in range(8):
        write(str(tmp_path / "frontend" / "src" / ("f%d.ts" % i)),
              "navigator.clipboard.writeText(x)\n")
    calls, ok, fail, warn = _collector()
    _kit_checks_mod().check_frontend_pitfalls(str(tmp_path), ok, fail, warn)
    assert "(+3 more)" in calls["fail"][0][1]  # 8 hits, 5 shown


# ---------------- kit_checks: enforcement-diff second line of defense ----------------
def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=30)


def _mk_diff_repo(tmp_path):
    repo = tmp_path / "repo"
    write(str(repo / ".claude" / "hooks" / "gate_git.py"), "# v1\n")
    write(str(repo / ".claude" / "kit_version"), "version: 1\n")
    write(str(repo / "src" / "app.py"), "x = 1\n")
    _git(repo, "init", "-b", "main")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "base")
    _git(repo, "checkout", "-b", "feat")
    return repo


def test_enforcement_diff_blocks_hook_change_without_kit_bump(tmp_path):
    repo = _mk_diff_repo(tmp_path)
    write(str(repo / ".claude" / "hooks" / "gate_git.py"), "# tampered\n")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "tamper")
    calls, ok, fail, warn = _collector()
    _kit_checks_mod().check_enforcement_diff(str(repo), ok, fail, warn)
    assert calls["fail"] and "kit update" in calls["fail"][0][1]


@pytest.mark.parametrize("rel", [
    ".codex/config.toml",
    ".agents/skills/project-manager/SKILL.md",
    ".claude/provider_artifacts.json",
    ".claude/team_kit_roles.txt",
])
def test_enforcement_diff_blocks_codex_controls_without_kit_bump(tmp_path, rel):
    repo = _mk_diff_repo(tmp_path)
    write(str(repo / rel), "tampered\n")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "tamper")
    calls, ok, fail, warn = _collector()
    _kit_checks_mod().check_enforcement_diff(str(repo), ok, fail, warn)
    assert calls["fail"] and rel in calls["fail"][0][1]


def test_enforcement_diff_allows_kit_update(tmp_path):
    repo = _mk_diff_repo(tmp_path)
    write(str(repo / ".claude" / "hooks" / "gate_git.py"), "# v2 via kit\n")
    write(str(repo / ".claude" / "kit_version"), "version: 2\n")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "kit update")
    calls, ok, fail, warn = _collector()
    _kit_checks_mod().check_enforcement_diff(str(repo), ok, fail, warn)
    assert not calls["fail"]


def test_enforcement_diff_catches_tamper_on_main(tmp_path):
    # audit M1: solo/trunk workflow — a tampered hook committed STRAIGHT to main (no remote,
    # HEAD == base) must not pass as "no changes"
    repo = tmp_path / "repo"
    write(str(repo / ".claude" / "hooks" / "gate_git.py"), "# v1\n")
    write(str(repo / ".claude" / "kit_version"), "version: 1\n")
    _git(repo, "init", "-b", "main")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "base")
    write(str(repo / ".claude" / "hooks" / "gate_git.py"), "# TAMPERED\n")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "tamper on main")
    calls, ok, fail, warn = _collector()
    _kit_checks_mod().check_enforcement_diff(str(repo), ok, fail, warn)
    assert calls["fail"] and "kit update" in calls["fail"][0][1]


def test_selfmod_blocks_codex_patch_from_subdir_cwd(tmp_path):
    # audit M2: cwd drifted into a subdir — a repo-root-looking patch path must still block
    # (dual-candidate resolution: cwd-join AND repo-root-join)
    (tmp_path / "frontend").mkdir(parents=True)
    payload = {"tool_name": "apply_patch",
               "tool_input": {"command": _codex_patch(".claude/hooks/gate_git.py")},
               "cwd": str(tmp_path / "frontend")}
    assert run_hook("guard_harness_selfmod.py", payload, tmp_path) == 2


def test_enforcement_diff_warns_on_deleted_tests(tmp_path):
    repo = tmp_path / "repo"
    write(str(repo / ".claude" / "kit_version"), "version: 1\n")
    write(str(repo / "tests" / "test_a.py"), "def test_a(): pass\n")  # exists on main
    _git(repo, "init", "-b", "main")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "base")
    _git(repo, "checkout", "-b", "feat")
    (repo / "tests" / "test_a.py").unlink()
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "delete test")
    calls, ok, fail, warn = _collector()
    _kit_checks_mod().check_enforcement_diff(str(repo), ok, fail, warn)
    assert calls["warn"] and "DELETED" in calls["warn"][0][1]


# ---------------- session_status: version-banner bootstrap + resume-proof pending counter ----------------
def test_session_status_announces_bootstrap_update_with_pending(tmp_path):
    repo = tmp_path / "repo"
    write(str(repo / ".claude" / "kit_version"), "version: 2026.07.14-3\ncontent: x\n")
    write(str(repo / ".claude" / "kit_update_pending.repo"), "# diverged\n- scripts/quality.py\n")
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    p = subprocess.run([sys.executable, os.path.join(HOOKS, "session_status.py")],
                       input=json.dumps({"cwd": str(repo)}), capture_output=True, text=True,
                       env=env, timeout=60)
    assert "KIT UPDATED to 2026.07.14-3" in p.stdout  # neutral wording: PM-run updates are
    # not "external" (audit: the label confused a PM into re-updating)


def test_session_status_pending_counter_ignores_resume(tmp_path):
    repo = tmp_path / "repo"
    write(str(repo / ".claude" / "kit_update_pending.repo"), "# diverged\n- scripts/quality.py\n")
    write(str(repo / ".claude" / "kit_update_pending.state"),
          '{"sessions": 2, "first_seen": "2026-07-14"}')
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(repo))
    subprocess.run([sys.executable, os.path.join(HOOKS, "session_status.py")],
                   input=json.dumps({"cwd": str(repo), "source": "resume"}),
                   capture_output=True, text=True, env=env, timeout=60)
    st = json.loads(open(str(repo / ".claude" / "kit_update_pending.state"), encoding="utf-8").read())
    assert st["sessions"] == 2  # resume did NOT inflate the counter
    subprocess.run([sys.executable, os.path.join(HOOKS, "session_status.py")],
                   input=json.dumps({"cwd": str(repo), "source": "startup"}),
                   capture_output=True, text=True, env=env, timeout=60)
    st = json.loads(open(str(repo / ".claude" / "kit_update_pending.state"), encoding="utf-8").read())
    assert st["sessions"] == 3  # a real session start still increments


# ---------------- provider generator: single-source .codex/.github artifacts ----------------
GEN = os.path.join(ROOT, "team-kits", "gen_provider_artifacts.py")


def test_gen_provider_artifacts(tmp_path):
    import shutil
    repo = tmp_path / "repo"
    os.makedirs(str(repo / ".claude"), exist_ok=True)
    shutil.copytree(os.path.join(ROOT, "team-kits", "dev-team", "hooks"),
                    str(repo / ".claude" / "hooks"))
    shutil.copy(os.path.join(ROOT, "team-kits", "dev-team", "settings", "settings.json"),
                str(repo / ".claude" / "settings.json"))
    write(str(repo / ".claude" / "agents" / "backend-developer.md"),
          "---\nname: backend-developer\ndescription: >\n  Backend specialist: builds\n"
          "  the server side.\nmodel: sonnet\neffort: high\n---\nBody of the backend role.\n")
    write(str(repo / ".claude" / "agents" / "project-manager.md"),
          "---\nname: project-manager\ndescription: Lead\nmodel: opus\neffort: high\n---\nLead body.\n")
    write(str(repo / ".claude" / "skills" / "backend-developer" / "SKILL.md"),
          "---\nname: backend-developer\n---\nFollow ./CLAUDE.md.\n")
    write(str(repo / ".claude" / "skills" / "project-manager" / "SKILL.md"),
          "---\nname: project-manager\n---\nLead skill.\n")
    write(str(repo / ".claude" / "team_kit_roles.txt"),
          "# agents-and-skills:team-kit-roles v1 team=dev-team count=2\n"
          "project-manager\nbackend-developer\n")
    # Pre-manifest upgrades remove only artifacts carrying the old generator's stable marker.
    write(str(repo / ".codex" / "agents" / "stale.toml"),
          'developer_instructions = "team-kit governed repository"\n')
    write(str(repo / ".codex" / "agents" / "custom.toml"),
          'developer_instructions = "user-owned agent"\n')
    write(str(repo / ".github" / "agents" / "stale.agent.md"),
          "You are inside a team-kit governed repository.\n")
    write(str(repo / ".github" / "agents" / "custom.agent.md"), "User-owned agent.\n")
    p = subprocess.run([sys.executable, GEN, "--repo", str(repo), "--providers", "codex"],
                       capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    assert not (repo / ".codex" / "agents" / "stale.toml").exists()
    # legacy Copilot outputs (generation removed) are still recognized and cleaned up
    assert not (repo / ".github" / "agents" / "stale.agent.md").exists()
    assert (repo / ".codex" / "agents" / "custom.toml").is_file()
    assert (repo / ".github" / "agents" / "custom.agent.md").is_file()
    hooks = json.loads(open(str(repo / ".codex" / "hooks.json"), encoding="utf-8").read())
    txt = json.dumps(hooks)
    assert "apply_patch" in txt                      # Edit|Write matchers translated
    assert "Agent|Task" not in txt                   # spawn guard deliberately not registered
    # ...and the TRIPLE, not two independent substrings. `"apply_patch" in txt` plus
    # `"guard_pm_scope.py" in txt` both stayed green while guard_pm_scope lost its apply_patch
    # matcher entirely — widening its Claude matcher to `Edit|Write|MultiEdit|NotebookEdit` fell
    # through a string lookup and was emitted verbatim, so the lead's write-scope veto never fired
    # on Codex again. Two strings in one file prove nothing about each other.
    # The GATE behind the launcher has to count, not just `_gate.py`: a plain
    # `.claude/hooks/<name>.py` search sees only the launcher, which is exactly how the equivalent
    # check in the V2 suite came to assert nothing at all. `report._invoked_scripts` cannot be
    # reused here — these are Codex shell one-liners that invoke `"$py"`, not `python`, so it
    # finds no interpreter and returns nothing (worth knowing: doctor's wiring reader is
    # Claude-settings-shaped by construction).
    def scripts_in(command):
        found = re.findall(r"[A-Za-z0-9_]+\.py", command.replace("\\", "/"))
        return [name for name in found if name != "_gate.py"] or found
    triples = {(event, group.get("matcher", ""), script)
               for event, groups in hooks["hooks"].items()
               for group in groups
               for hook in group.get("hooks", [])
               for script in scripts_in(hook.get("command", ""))}
    for script in ("guard_pm_scope.py", "guard_harness_selfmod.py"):
        assert ("PreToolUse", "apply_patch", script) in triples, (
            "%s has no PreToolUse/apply_patch registration on Codex: %s"
            % (script, sorted(triples)))
    # every generated matcher must be one Codex actually knows, or it is a dead entry that reads
    # as enforcement in any audit of this file
    for _event, matcher, _script in triples:
        assert matcher in ("", "*", "Bash", "apply_patch") or matcher.startswith("mcp__"), matcher
    # Codex may inherit a stale Claude variable from the parent shell. Every generated
    # command must overwrite it with the root it just resolved before running a shared hook.
    assert 'CLAUDE_PROJECT_DIR=\\"$root\\"' in txt
    assert "$env:CLAUDE_PROJECT_DIR = $root" in txt
    assert "git rev-parse --show-toplevel" in txt     # stable even when Codex starts in a subdir
    assert "dirname" in txt and "Get-Location" in txt  # greenfield fallback before git init
    assert "TEAM_KIT_PROVIDER=codex" in txt
    assert "guard_pm_scope.py" in txt                 # current Codex PreToolUse carries agent_id
    assert "SubagentStart" in hooks["hooks"] and "notify_agent_events.py" in json.dumps(
        hooks["hooks"]["SubagentStart"])
    import tomllib
    config = tomllib.loads((repo / ".codex" / "config.toml").read_text(encoding="utf-8"))
    assert config["model"] == "gpt-5.6-sol"
    assert config["model_reasoning_effort"] == "high"
    assert config["default_permissions"] == "team-kit"
    assert config["features"]["multi_agent"] is True
    assert "Lead body." in config["developer_instructions"]
    fs = config["permissions"]["team-kit"]["filesystem"][":workspace_roots"]
    assert fs["."] == "write" and fs[".env"] == "deny" and fs["**/*.pem"] == "deny"
    assert fs[".codex"] == "read" and fs[".agents/skills"] == "read"
    assert fs["AGENTS.md"] == "read" and fs[".claude/hooks"] == "read"
    toml = open(str(repo / ".codex" / "agents" / "backend-developer.toml"), encoding="utf-8").read()
    assert 'model = "gpt-5.6-terra"' in toml and "AGENTS.md" in toml
    assert ".agents/skills/backend-developer/SKILL.md" in toml
    # audit M3: folded (>) frontmatter descriptions must be joined, not collapsed to '>'
    assert "Backend specialist: builds the server side." in toml
    assert not os.path.isfile(str(repo / ".codex" / "agents" / "project-manager.toml"))
    native_skill = repo / ".agents" / "skills" / "backend-developer" / "SKILL.md"
    assert native_skill.is_file() and "./AGENTS.md" in native_skill.read_text(encoding="utf-8")
    native_marker = repo / ".agents" / "skills" / "backend-developer" / ".team-kit-generated"
    assert "agents-and-skills:generated-codex-config" in native_marker.read_text(encoding="utf-8")
    assert (repo / ".agents" / "skills" / "project-manager" / "SKILL.md").is_file()
    manifest_path = repo / ".claude" / "provider_artifacts.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert ".codex/config.toml" in manifest["files"]

    # Invalid ownership fails closed before any generated or user-owned output is touched.
    write(str(repo / "src" / "keep.py"), "KEEP = True\n")
    write(str(repo / ".agents" / "skills" / "keep" / "SKILL.md"), "user-owned\n")
    tampered = json.loads(json.dumps(manifest))
    tampered["files"].append("src/keep.py")
    tampered["dirs"].append(".agents/skills/keep/nested")
    write(str(manifest_path), json.dumps(tampered))
    bad = subprocess.run([sys.executable, GEN, "--repo", str(repo), "--providers", "codex"],
                         capture_output=True, text=True, timeout=60)
    assert bad.returncode != 0 and "left untouched" in bad.stderr
    assert (repo / ".codex" / "config.toml").is_file() and native_skill.is_file()
    write(str(manifest_path), "{")
    truncated = subprocess.run(
        [sys.executable, GEN, "--repo", str(repo), "--providers", "codex"],
        capture_output=True, text=True, timeout=60)
    assert truncated.returncode != 0 and manifest_path.read_text(encoding="utf-8") == "{"
    assert (repo / ".codex" / "config.toml").is_file() and native_skill.is_file()
    write(str(manifest_path), json.dumps(manifest))

    # The removed provider is rejected fail-closed with a migration hint, artifacts untouched.
    rejected = subprocess.run([sys.executable, GEN, "--repo", str(repo), "--providers", "copilot"],
                              capture_output=True, text=True, timeout=60)
    assert rejected.returncode != 0 and "no longer supported" in rejected.stderr
    assert (repo / ".codex" / "config.toml").is_file() and native_skill.is_file()

    # Removing every extra provider cleans exactly the manifest-owned outputs, nothing else.
    p2 = subprocess.run([sys.executable, GEN, "--repo", str(repo), "--providers", ""],
                        capture_output=True, text=True, timeout=60)
    assert p2.returncode == 0, p2.stderr
    assert not (repo / ".codex" / "config.toml").exists()
    assert not (repo / ".codex" / "hooks.json").exists()
    assert not native_skill.exists()
    assert (repo / "src" / "keep.py").is_file()
    assert (repo / ".agents" / "skills" / "keep" / "SKILL.md").is_file()
    empty_manifest = json.loads(
        (repo / ".claude" / "provider_artifacts.json").read_text(encoding="utf-8")
    )
    assert empty_manifest == {"version": 1, "files": [], "dirs": []}
    assert (repo / ".codex" / "agents" / "custom.toml").is_file()
    assert (repo / ".github" / "agents" / "custom.agent.md").is_file()


def test_gen_provider_artifacts_cleans_pre_manifest_codex_outputs(tmp_path):
    repo = tmp_path / "repo"
    write(str(repo / ".codex" / "config.toml"),
          "# agents-and-skills:generated-codex-config\nmodel = \"old\"\n")
    write(str(repo / ".codex" / "hooks.json"),
          '{"hooks":{"PreToolUse":[{"command":".claude/hooks/old.py"}]}}')
    write(str(repo / ".agents" / "skills" / "backend-developer" / "SKILL.md"),
          "old generated kit skill\n")
    write(str(repo / ".agents" / "skills" / "backend-developer" / ".team-kit-generated"),
          "agents-and-skills:generated-codex-config\n")
    write(str(repo / ".agents" / "skills" / "custom" / "SKILL.md"), "user-owned\n")
    result = subprocess.run([sys.executable, GEN, "--repo", str(repo), "--providers", ""],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert not (repo / ".codex" / "config.toml").exists()
    assert not (repo / ".codex" / "hooks.json").exists()
    assert not (repo / ".agents" / "skills" / "backend-developer").exists()
    assert (repo / ".agents" / "skills" / "custom" / "SKILL.md").is_file()


def test_gen_provider_artifacts_preserves_unmarked_native_skill(tmp_path):
    repo = tmp_path / "repo"
    skill = repo / ".agents" / "skills" / "backend-developer" / "SKILL.md"
    write(str(skill), "user-owned skill without generator marker\n")
    result = subprocess.run([sys.executable, GEN, "--repo", str(repo), "--providers", ""],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert skill.read_text(encoding="utf-8") == "user-owned skill without generator marker\n"


def _provider_test_repo(tmp_path):
    """Minimal, complete installed-kit state for generator fail-closed tests."""
    repo = tmp_path / "repo"
    shutil.copytree(os.path.join(ROOT, "team-kits", "dev-team", "hooks"),
                    str(repo / ".claude" / "hooks"))
    shutil.copy(os.path.join(ROOT, "team-kits", "dev-team", "settings", "settings.json"),
                str(repo / ".claude" / "settings.json"))
    for role, model in (("project-manager", "opus"), ("backend-developer", "sonnet")):
        write(str(repo / ".claude" / "agents" / (role + ".md")),
              "---\nname: %s\ndescription: %s\nmodel: %s\neffort: high\n---\n%s body.\n"
              % (role, role, model, role))
        write(str(repo / ".claude" / "skills" / role / "SKILL.md"),
              "---\nname: %s\n---\nFollow ./CLAUDE.md.\n" % role)
    write(str(repo / ".claude" / "team_kit_roles.txt"),
          "# agents-and-skills:team-kit-roles v1 team=dev-team count=2\n"
          "project-manager\nbackend-developer\n")
    return repo


def test_gen_provider_artifacts_requires_installed_hook_bundle(tmp_path):
    repo = _provider_test_repo(tmp_path)
    shutil.rmtree(repo / ".claude" / "hooks")
    result = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                             "--providers", "codex"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode != 0 and "Missing .claude/hooks" in result.stderr
    assert not (repo / ".codex" / "config.toml").exists()
    assert not (repo / ".codex" / "hooks.json").exists()


def test_gen_provider_config_defaults_absent_providers_to_both(tmp_path):
    # Legacy project_config predating the providers key: default [claude, codex] with a notice,
    # so existing projects keep taking kit updates without a config edit first.
    repo = _provider_test_repo(tmp_path)
    config = repo / "project_memory" / "project_config.yaml"
    write(str(config), "project:\n  preset: mini\n")
    checked = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                              "--project-config", str(config), "--check-config-only"],
                             capture_output=True, text=True, timeout=60)
    assert checked.returncode == 0, checked.stderr
    assert "defaulting to" in checked.stdout
    generated = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                                "--project-config", str(config)],
                               capture_output=True, text=True, timeout=60)
    assert generated.returncode == 0, generated.stderr
    assert (repo / ".codex" / "config.toml").is_file()

    # an explicitly PRESENT but empty providers value stays fail-closed
    config.write_text("project:\n  preset: mini\nproviders:\n", encoding="utf-8")
    empty = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                            "--project-config", str(config), "--check-config-only"],
                           capture_output=True, text=True, timeout=60)
    assert empty.returncode != 0 and "must not be empty" in empty.stderr


def test_gen_accepts_fable_as_lead_tier_pin(tmp_path):
    # `fable` is a legitimate Claude-side §11 pin (a real synaipse map carried it): Claude keeps
    # the literal value, the Codex artifact maps it to the provider's LEAD tier.
    repo = _provider_test_repo(tmp_path)
    write(str(repo / ".claude" / "agents" / "backend-developer.md"),
          "---\nname: backend-developer\ndescription: backend\nmodel: fable\neffort: high\n"
          "---\nbackend body.\n")
    result = subprocess.run([sys.executable, GEN, "--repo", str(repo), "--providers", "codex"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    toml = (repo / ".codex" / "agents" / "backend-developer.toml").read_text(encoding="utf-8")
    assert 'model = "gpt-5.6-sol"' in toml

    config = repo / "project_memory" / "project_config.yaml"
    write(str(config), "project:\n  preset: mini\nproviders: [claude, codex]\n"
                       "model_map:\n  backend-developer: fable\n")
    checked = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                              "--project-config", str(config), "--check-config-only"],
                             capture_output=True, text=True, timeout=60)
    assert checked.returncode == 0, checked.stderr


def test_gen_codex_frontmatter_overlay(tmp_path):
    # The divergence valve: a namespaced `codex:` frontmatter block (ignored by Claude) merges
    # Codex-only keys into the generated TOML; identity keys stay generator-owned.
    repo = _provider_test_repo(tmp_path)
    write(str(repo / ".claude" / "agents" / "backend-developer.md"),
          "---\nname: backend-developer\ndescription: backend\nmodel: sonnet\neffort: high\n"
          "codex:\n  sandbox_mode: workspace-write\n  model_reasoning_effort: xhigh\n"
          "---\nbackend body.\n")
    result = subprocess.run([sys.executable, GEN, "--repo", str(repo), "--providers", "codex"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    toml = (repo / ".codex" / "agents" / "backend-developer.toml").read_text(encoding="utf-8")
    assert 'sandbox_mode = "workspace-write"' in toml
    assert 'model_reasoning_effort = "xhigh"' in toml       # overlay wins over effort:
    assert 'model = "gpt-5.6-terra"' in toml                # tier mapping still applies

    # reserved keys are rejected fail-closed
    write(str(repo / ".claude" / "agents" / "backend-developer.md"),
          "---\nname: backend-developer\ndescription: backend\nmodel: sonnet\neffort: high\n"
          "codex:\n  developer_instructions: hijack\n---\nbackend body.\n")
    rejected = subprocess.run([sys.executable, GEN, "--repo", str(repo), "--providers", "codex"],
                              capture_output=True, text=True, timeout=60)
    assert rejected.returncode != 0 and "must not override" in rejected.stderr
    assert 'sandbox_mode = "workspace-write"' in (
        repo / ".codex" / "agents" / "backend-developer.toml").read_text(encoding="utf-8")


def test_gen_provider_removal_rejects_symlinked_managed_parent(tmp_path):
    repo = _provider_test_repo(tmp_path)
    config = repo / "project_memory" / "project_config.yaml"
    write(str(config), "project:\n  preset: mini\nproviders: [claude, codex]\n")
    generated = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                                "--project-config", str(config)],
                               capture_output=True, text=True, timeout=60)
    assert generated.returncode == 0, generated.stderr
    manifest = repo / ".claude" / "provider_artifacts.json"
    manifest_before = manifest.read_text(encoding="utf-8")

    shutil.rmtree(repo / ".codex")
    external = tmp_path / "outside-codex"
    sentinel = external / "config.toml"
    write(str(sentinel), "# external sentinel must survive\n")
    try:
        os.symlink(external, repo / ".codex", target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip("directory symlinks are not permitted in this test environment: %s" % exc)

    config.write_text("project:\n  preset: mini\nproviders: [claude]\n", encoding="utf-8")
    removed = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                              "--project-config", str(config)],
                             capture_output=True, text=True, timeout=60)
    assert removed.returncode != 0
    assert "symlink" in (removed.stdout + removed.stderr).lower()
    assert sentinel.read_text(encoding="utf-8") == "# external sentinel must survive\n"
    assert manifest.read_text(encoding="utf-8") == manifest_before


@pytest.mark.parametrize("relative,is_directory", [
    (".codex/config.toml", False),
    (".agents/skills/backend-developer", True),
])
def test_gen_provider_artifacts_rejects_unowned_output_collision(tmp_path, relative,
                                                                 is_directory):
    repo = _provider_test_repo(tmp_path)
    target = repo / relative
    if is_directory:
        write(str(target / "SKILL.md"), "user-owned collision\n")
    else:
        write(str(target), "# user-owned collision\n")
    result = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                             "--providers", "codex"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode != 0 and "Provider output collision" in result.stderr
    assert "user-owned collision" in (
        (target / "SKILL.md").read_text(encoding="utf-8") if is_directory
        else target.read_text(encoding="utf-8"))
    assert not (repo / ".claude" / "provider_artifacts.json").exists()


@pytest.mark.parametrize("source", [
    "project:\n  name: missing-providers\n",
    "providers: null\n",
    "providers: [claude]\nproviders: [codex]\n",
])
def test_gen_provider_config_rejects_missing_null_or_duplicate_provider_key(tmp_path, source):
    config = tmp_path / "project_config.yaml"
    config.write_text(source, encoding="utf-8")
    sentinel = tmp_path / "sentinel.txt"
    sentinel.write_text("untouched\n", encoding="utf-8")
    result = subprocess.run([sys.executable, GEN, "--repo", str(tmp_path),
                             "--project-config", str(config), "--check-config-only"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode != 0 and "provider artifacts were left untouched" in result.stderr
    assert sentinel.read_text(encoding="utf-8") == "untouched\n"


@pytest.mark.parametrize("missing_kind", ["agent", "skill"])
def test_gen_provider_artifacts_rejects_role_or_skill_mismatch(tmp_path, missing_kind):
    repo = _provider_test_repo(tmp_path)
    if missing_kind == "agent":
        (repo / ".claude" / "agents" / "backend-developer.md").unlink()
    else:
        shutil.rmtree(repo / ".claude" / "skills" / "backend-developer")
    result = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                             "--providers", "codex"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode != 0
    expected = "Role manifest/source mismatch" if missing_kind == "agent" else "native skill source"
    assert expected in result.stderr
    assert not (repo / ".codex" / "config.toml").exists()


def test_gen_provider_artifacts_translates_role_scoped_hooks(tmp_path):
    repo = _provider_test_repo(tmp_path)
    agent_source = os.path.join(ROOT, "team-kits", "dev-team", "agents")
    skill_source = os.path.join(ROOT, "team-kits", "dev-team", "skills")
    for role in ("backend-developer", "frontend-developer"):
        shutil.copy(os.path.join(agent_source, role + ".md"),
                    str(repo / ".claude" / "agents" / (role + ".md")))
        if role == "frontend-developer":
            shutil.copytree(os.path.join(skill_source, role),
                            str(repo / ".claude" / "skills" / role))
    write(str(repo / ".claude" / "team_kit_roles.txt"),
          "# agents-and-skills:team-kit-roles v1 team=dev-team count=3\n"
          "project-manager\nbackend-developer\nfrontend-developer\n")
    result = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                             "--providers", "codex"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    text = (repo / ".codex" / "hooks.json").read_text(encoding="utf-8")
    assert "guard_guidelines.py" in text
    assert "TEAM_KIT_AGENT_TYPES=backend-developer,frontend-developer" in text
    assert "$env:TEAM_KIT_AGENT_TYPES='backend-developer,frontend-developer'" in text


def test_guard_guidelines_codex_multifile_patch_honors_role_scope(tmp_path):
    pytest.importorskip("yaml")
    capture_invariant(tmp_path, "python", text="use type hints")
    payload = {
        "hook_event_name": "PreToolUse",
        "agent_type": "backend-developer",
        "tool_name": "apply_patch",
        "tool_input": {"command": _codex_patch("src/ok.py", "frontend/blocked.ts")},
        "cwd": str(tmp_path),
    }
    env = {"TEAM_KIT_PROVIDER": "codex",
           "TEAM_KIT_AGENT_TYPES": "backend-developer,frontend-developer"}
    assert run_hook_process("guard_guidelines.py", payload, tmp_path,
                            extra_env=env).returncode == 2
    payload["agent_type"] = "quality-engineer"
    assert run_hook_process("guard_guidelines.py", payload, tmp_path,
                            extra_env=env).returncode == 0


def test_gen_provider_artifacts_hook_bundle_hash_changes_with_hook_content(tmp_path):
    repo = _provider_test_repo(tmp_path)

    def generate_and_hash():
        result = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                                 "--providers", "codex"],
                                capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stderr
        text = (repo / ".codex" / "hooks.json").read_text(encoding="utf-8")
        hashes = set(re.findall(
            r"TEAM_KIT_HOOK_BUNDLE_SHA256(?:=|=')([0-9a-f]{64})", text))
        assert len(hashes) == 1
        return hashes.pop()

    before = generate_and_hash()
    compat = repo / ".claude" / "hooks" / "_compat.py"
    compat.write_text(compat.read_text(encoding="utf-8") + "\n# bundle hash regression\n",
                      encoding="utf-8")
    after = generate_and_hash()
    assert before != after


def _generated_subagent_start_command(repo, key):
    result = subprocess.run([sys.executable, GEN, "--repo", str(repo),
                             "--providers", "codex"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    document = json.loads((repo / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    for group in document["hooks"].get("SubagentStart", []):
        for hook in group.get("hooks", []):
            if "notify_agent_events.py" in hook.get("command", ""):
                return hook[key]
    raise AssertionError("generated SubagentStart notify hook not found")


def _exercise_generated_hook_bundle_command(tmp_path, command_key, shell_executable=None):
    repo = _provider_test_repo(tmp_path)
    (repo / "project_memory").mkdir()
    git_init = subprocess.run(["git", "init", "-b", "main"], cwd=str(repo),
                              capture_output=True, text=True, timeout=30)
    assert git_init.returncode == 0, git_init.stderr
    command = _generated_subagent_start_command(repo, command_key)
    payload = {"hook_event_name": "SubagentStart", "agent_type": "backend-developer",
               "agent_id": "generated-command-test", "cwd": str(repo)}

    def run_command():
        kwargs = {"cwd": str(repo), "input": json.dumps(payload), "capture_output": True,
                  "text": True, "timeout": 60, "shell": bool(shell_executable),
                  # A Codex process launched from a Claude-configured shell may inherit this.
                  # The generated wrapper must replace it with the root resolved above.
                  "env": dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp_path / "stale-root"))}
        if shell_executable:
            kwargs["executable"] = shell_executable
        return subprocess.run(command, **kwargs)

    clean = run_command()
    assert clean.returncode == 0, clean.stdout + clean.stderr
    audit = repo / "project_memory" / ".audit" / "hook_events.jsonl"
    assert audit.is_file() and "subagent_start" in audit.read_text(encoding="utf-8")
    audit_before = audit.read_bytes()

    helper = repo / ".claude" / "hooks" / "_compat.py"
    helper.write_text(helper.read_text(encoding="utf-8") + "\n# changed after hook trust\n",
                      encoding="utf-8")
    changed = run_command()
    assert changed.returncode == 2
    message = (changed.stdout + changed.stderr).lower()
    assert "hook bundle changed" in message
    assert "full scaffold" in message and "/hooks" in message
    assert audit.read_bytes() == audit_before  # verifier stopped before the actual hook


def test_generated_windows_hook_command_verifies_bundle_before_execution(tmp_path):
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("generated Windows hook command runs on Windows")
    _exercise_generated_hook_bundle_command(tmp_path, "commandWindows")


def test_generated_posix_hook_command_verifies_bundle_before_execution(tmp_path):
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("generated POSIX hook command runs on Unix CI")
    _exercise_generated_hook_bundle_command(tmp_path, "command", shutil.which("bash"))


def _kit_hooks(kit):
    hooks_dir = os.path.join(ROOT, "team-kits", kit, "hooks")
    return {fn[:-3] for fn in os.listdir(hooks_dir)
            if fn.endswith(".py") and not fn.startswith("_")}


# ---------------- constitutions: every hook has a documented rule-home (diet safety) ----------------
def test_every_hook_documented_in_its_constitution():
    for kit in KITS:
        cpath = os.path.join(ROOT, "team-kits", kit, "constitution", "AGENTS.md")
        text = open(cpath, encoding="utf-8", errors="ignore").read()
        for name in sorted(_kit_hooks(kit)):
            assert name in text, "%s: hook %s has no documented rule-home in the constitution" % (kit, name)


def test_no_instruction_file_names_a_hook_its_own_kit_does_not_ship():
    """The other direction, which nothing checked: a hook name the kit does not install.

    A role that reads "`guard_no_adhoc`-style discipline" in a kit shipping no such hook looks for a
    guard that is not there and reads the rule as enforced. Which names count is derived, not listed:
    a name is a HOOK if some kit ships a module by that name, so `gate_health` — a judge-rubric
    dimension that merely looks like one — is not one, and a new hook is covered the day it ships.
    """
    known = set()
    for kit in KITS:
        known |= _kit_hooks(kit)
    hook_mention = re.compile(r"`([a-z][a-z0-9_]+)`")
    for kit in KITS:
        shipped = _kit_hooks(kit)
        for path, text in _instruction_files(kit):
            for match in hook_mention.finditer(text):
                name = match.group(1)
                if name not in known or name in shipped:
                    continue
                raise AssertionError(
                    "%s names the hook `%s`, which %s does not install — the rule it stands for is "
                    "policy here. Say so, or name a hook this kit actually ships."
                    % (os.path.relpath(path, ROOT), name, kit))


DISPATCH_AUTHORISER = "_assert_dispatch_authorised_locked"


def _dispatch_authorising_kinds():
    """APR kinds that really authorise a dispatch, read out of the kernel that decides.

    DERIVED OVER THE CALL GRAPH of `_assert_dispatch_authorised_locked`, which is the one function
    every dispatch passes through: the root route keeps its answer in the `ROOT_DISPATCH_KINDS`
    constant, and each task route compares `apr["kind"]` against a literal inside the helper it
    delegates to. So the answer is that constant plus every `APR_KINDS` string appearing in the
    authoriser or in any module-level function of `dispatch.py` it reaches.

    The predecessor named `_covering_analysis_apr` outright and its docstring said "two routes
    exist". Both statements aged the day the `routine` route shipped: the helper's answer would
    have stayed {scope, delivery, analysis}, and this test would have gone on asserting that a
    role naming `routine` names a kind the kernel refuses — the over-alarming half of exactly the
    defect it was written to catch (`APR.kind: routine` documented as the auditor's dispatch basis
    while the kernel refused it, measured 2026-07-26; the route measured working 2026-07-31).
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.approvals import APR_KINDS, ROOT_DISPATCH_KINDS
    source = open(os.path.join(ROOT, "team-kits", "kernel", "dispatch.py"),
                  encoding="utf-8").read()
    functions = {node.name: node for node in ast.parse(source).body
                 if isinstance(node, ast.FunctionDef)}
    assert DISPATCH_AUTHORISER in functions, (
        "%s is gone from kernel/dispatch.py — this derivation has lost its entry point and would "
        "silently answer with the root route alone" % DISPATCH_AUTHORISER)
    reached, queue = set(), [DISPATCH_AUTHORISER]
    while queue:
        name = queue.pop()
        if name in reached or name not in functions:
            continue
        reached.add(name)
        queue += [node.func.id for node in ast.walk(functions[name])
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    kinds = set(ROOT_DISPATCH_KINDS)
    for name in reached:
        kinds |= {node.value for node in ast.walk(functions[name])
                  if isinstance(node, ast.Constant) and node.value in APR_KINDS}
    return kinds


def test_the_auditor_names_an_approval_kind_that_can_actually_dispatch_it():
    """The auditor's own SKILL must name a kind the dispatch gate accepts.

    It documented `APR.kind: routine` — the kind spec II.10a designs for this role — as the approval
    it "is dispatched on", and added that an expired one blocks the spawn. Measured 2026-07-26: a
    valid, unexpired, unrevoked routine APR on the root authorised nothing, so the promised expiry
    check was unreachable code and an auditor following its instruction could not be spawned at
    all. The kernel has the route since 2026-07-31; what this keeps pinned is the property, not
    that round's answer — the text may name only kinds the running authoriser accepts.
    """
    authorising = _dispatch_authorising_kinds()
    assert authorising, "could not read the dispatch routes out of the kernel"
    for kit in KITS:
        path = os.path.join(ROOT, "team-kits", kit, "skills", "project-auditor", "SKILL.md")
        text = open(path, encoding="utf-8", errors="ignore").read()
        named = set(re.findall(r"APR\.kind:\s*([a-z]+)", text))
        assert named, "%s: the auditor SKILL names no APR kind as its dispatch basis" % kit
        assert named & authorising, (
            "%s: the auditor SKILL names only %s as its dispatch basis, but the kernel authorises a "
            "dispatch through %s. A role told to ride on a kind the gate refuses cannot be spawned."
            % (kit, "/".join(sorted(named)), "/".join(sorted(authorising))))


# Everything an agent is instructed BY. The constitution, the agent definitions and the role SKILLs,
# because a rule the constitution states honestly and a role SKILL then restates as unconditional is
# still a lie told to the role that acts on it — plus the state templates, because the entry gate
# tells the initializer to fill EVERY section of them, so a dead monolith name in a template comment
# is copied into every new project. That is how `feature_requests.yaml` survived in the masterplan
# template while this sweep, reading three patterns, saw nothing (found by hand, 2026-07-26).
# `hooks/ENFORCEMENT.md` is here because the §2 hook table moved into it: the text a role reads
# after a refusal is instruction text wherever it is stored, and leaving it outside this corpus
# would have made "relocating" a way to escape every honesty sweep below — a dead monolith name, a
# mis-spelled entry point or an unconditional claim would simply have moved out of range.
INSTRUCTION_PATTERNS = ("constitution/AGENTS.md", "hooks/ENFORCEMENT.md", "agents/*.md",
                        "skills/*/SKILL.md", "templates/project_memory/**/*")


def _instruction_files(kit):
    import glob as _glob
    for pattern in INSTRUCTION_PATTERNS:
        for path in sorted(_glob.glob(os.path.join(ROOT, "team-kits", kit, pattern),
                                      recursive=True)):
            if os.path.isdir(path):
                continue
            yield path, open(path, encoding="utf-8", errors="ignore").read()


def _self_disabling_state_files(source):
    """The `*.yaml` inputs whose ABSENCE makes this hook stop without deciding.

    Derived from the code that runs, via the AST: an `if not <exists-check>(...)` whose body ENDS the
    decision (`return`, or `sys.exit(0)`) is a hook that switches itself off when its input is
    missing. The path is normally assembled by an `os.path.join` some lines above the guard, so every
    `*.yaml` literal in the module counts as a candidate input rather than only the guard's own
    expression. `.json` literals are deliberately out: project STATE in these kits is YAML (the
    kernel writes YAML items), while the `.json` files a hook touches are enforcement-layer or cache
    files whose absence means "not a scaffolded project", not "this rule is off".
    """
    exists_predicates = ("isfile", "exists", "isdir", "is_file", "is_dir")

    def ends_decision(node):
        for sub in ast.walk(node):
            if isinstance(sub, ast.Return):
                return True
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                    and sub.func.attr == "exit" and isinstance(sub.func.value, ast.Name) \
                    and sub.func.value.id == "sys" and sub.args \
                    and isinstance(sub.args[0], ast.Constant) and sub.args[0].value == 0:
                return True
        return False

    def negated_existence(test):
        if not (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)):
            return False
        return any(isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                   and sub.func.attr in exists_predicates for sub in ast.walk(test.operand))

    tree = ast.parse(source)
    if not any(isinstance(n, ast.If) and negated_existence(n.test) and ends_decision(n)
               for n in ast.walk(tree)):
        return set()
    if not ("sys.exit(2)" in source or "_kernel.block(" in source):
        return set()  # a hook that cannot block claims no block to be honest about
    return {n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and re.fullmatch(r"[A-Za-z0-9_.-]+\.yaml", n.value.strip())}


def test_the_enforcement_reference_names_the_file_that_switches_a_gate_off():
    """A gate that fails OPEN on a missing input must say WHICH input, where its rule is documented.

    Two shipped rows claimed an unconditional hard block over a hook that exits 0 while its registry
    is absent — `gate_proc_approved` (the V2 bootstrap hole stayed permanently open) and
    `guard_guidelines` (no template ships its file, so the default project has no guard). Both rows
    read as protection nobody had. Naming the file is the smallest claim that cannot be true while
    the precondition is hidden: derived from the hook's AST, so a hook that GAINS such a path is
    covered the day it ships, and no list of hook names exists here to go stale.

    THE SUBJECT FOLLOWED THE ROW. This read the constitution while the hook table lived there; the
    table now lives in `hooks/ENFORCEMENT.md` and the refusal messages point at it, so that is "the
    cell a role reads at the gate" — the phrase this check was written around. Both files are read,
    because a rule may still be stated in the constitution's prose, and the ROW is looked for first
    exactly as before.
    """
    for kit in ("dev-team", "research-team", "office-team"):
        lines = []
        for relative in (os.path.join("constitution", "AGENTS.md"),
                         os.path.join("hooks", "ENFORCEMENT.md")):
            path = os.path.join(ROOT, "team-kits", kit, relative)
            lines += open(path, encoding="utf-8", errors="ignore").read().splitlines()
        hooks_dir = os.path.join(ROOT, "team-kits", kit, "hooks")
        for fn in sorted(os.listdir(hooks_dir)):
            if not fn.endswith(".py") or fn.startswith("_"):
                continue
            name = fn[:-3]
            candidates = _self_disabling_state_files(
                open(os.path.join(hooks_dir, fn), encoding="utf-8", errors="ignore").read())
            if not candidates:
                continue
            # The hook's OWN table row — the cell a role reads at the gate. Deliberately not "any
            # line mentioning the hook": the shipped defect was a row that contradicted the truth
            # a paragraph elsewhere told, and joining both made the honest paragraph cover for it.
            documented = " ".join(
                ln for ln in lines
                if ln.lstrip().startswith("|") and name in ln.split("|")[1])
            documented = documented or " ".join(ln for ln in lines if name in ln)
            assert documented, ("%s: %s has no row in the constitution or the enforcement "
                                "reference at all" % (kit, name))
            assert any(c in documented for c in sorted(candidates)), (
                "%s: %s stops without deciding when %s is missing, but its row never names that "
                "file — the row reads as unconditional protection. Say which file the rule "
                "depends on." % (kit, name, "/".join(sorted(candidates))))


# Where an exemption below is allowed to be used. ANY = the file genuinely has no template in V2, so
# naming it is a true statement wherever it is written. KIT_ONLY = a DELETED V1 monolith that only
# ONE kit's own text still has reason to name: inside that kit the name says what a store used to be
# and what replaced it; in the global entry gates there is nothing to explain, so a monolith name
# there is exactly the V1 regression this sweep exists to catch (measured with the office PROC
# registry: the entry gates could name it and seed a PROC into it, green).
ANY, KIT_ONLY = "any", "kit-only"

# Names an instruction file may say although the kit template ships no such file. Each one is a
# deliberate statement about a file that does NOT exist in a V2 project, and each needs its scope and
# reason here — this dict is the only place a name may be exempted, so re-introducing a monolith by
# writing about it is a test failure rather than a review finding.
STATE_FILES_NOT_SHIPPED = {
    # kernel rollups: written into `generated/` on every state write, never templated
    "index.yaml": (ANY, "generated by the kernel, not a template"),
    "session_brief.yaml": (ANY, "generated by the kernel, not a template"),
    "retro.yaml": (ANY, "written by scripts/retro.py as its own diagnostic layer, not project state"),
    "hook_events.jsonl": (ANY, "hook event log, created by notify_agent_events on its first write"),
    # deleted V1 stores the instruction text names in order to say what replaced them
    "filing_log.yaml": (KIT_ONLY, "deleted V1 log; named to say nothing writes one and no gate reads one"),
    # a placeholder in a note ABOUT glob semantics, not a file anyone is sent to
    "x.yaml": (ANY, "the `deploy/sub/x.yaml` example in research_guidelines.yaml, showing that `*` "
                    "crosses directory separators"),
}


def _exempt_names(scopes):
    """The exempted names usable in the given scope(s) — see ANY / KIT_ONLY above."""
    return {name for name, (scope, _why) in STATE_FILES_NOT_SHIPPED.items() if scope in scopes}


# The same contract for DIRECTORIES under the state dir: a path an instruction file spells out
# although the kit template ships no such directory. Only entries here are allowed to be absent.
# A `/**` suffix exempts the whole subtree — for a layout no template CAN ship because it is data:
# the archive tree is derived from the item type and year in dev/research and from the office kit's
# own `filing_plan.yaml` rules, so the alternative is a list of example paths going stale.
STATE_DIRS_NOT_SHIPPED = {
    "generated": "kernel output, recreated on every state write, never templated",
    ".audit": "hook event log, created by notify_agent_events on its first write",
    "architecture": "the research kit ships none, and the one line naming it says exactly that",
    "archive/**": "created on demand when an item or document is filed; the layout is data, "
                  "not a template (item type + year, or the filing plan's rule paths)",
}

# A path token in prose — a run of path characters with at least one `/`. `<...>` placeholders and
# `*` globs are part of the token and are cut off before the path is judged.
_PATH_TOKEN_RX = re.compile(r"[A-Za-z0-9_.<>*-]+(?:/[A-Za-z0-9_.<>*-]*)+")


def _state_file_suffixes(shipped_paths):
    """The file extensions the STATE tree actually uses — the alphabet a bare name is judged in.

    Derived, not listed. Pinning `.yaml` here was a hole with teeth in exactly the place this sweep
    exists for: `product/masterplan.md` is state too, so `fill the masterplan into masterplan.md at
    the state root` — the shortest way to undo one of the three §6.2 moves of this lockstep — was
    invisible (measured 2026-07-26). A dotfile such as `.gitkeep` is a NAME, not an extension, and
    contributes none; a suffix no state file uses is therefore also unjudged, which is the honest
    price of deriving instead of enumerating.
    """
    suffixes = set()
    for path in shipped_paths:
        name = path.rsplit("/", 1)[-1]
        if "." in name[1:]:
            suffixes.add(name.rsplit(".", 1)[-1])
    return suffixes


def _bare_name_rx(suffixes):
    """A BARE file name — no directory at all — in one of the state tree's own extensions."""
    return re.compile(r"(?<![A-Za-z0-9_.<>*/-])[A-Za-z0-9_.<>*-]*[A-Za-z0-9_.-]\.(?:%s)"
                      r"(?![A-Za-z0-9_-])" % "|".join(sorted(map(re.escape, suffixes))))


def _dir_not_shipped(claimed):
    """Whether `claimed` is a directory STATE_DIRS_NOT_SHIPPED excuses, subtrees included."""
    for entry in STATE_DIRS_NOT_SHIPPED:
        if entry.endswith("/**"):
            top = entry[:-3]
            if claimed == top or claimed.startswith(top + "/"):
                return True
        elif claimed == entry:
            return True
    return False


def _state_path_claim(token, state_tops):
    """What `token` claims about the state dir, as (directory, file path) — either may be None.

    A token is treated as a PATH only when it says so: rooted at `project_memory/`, ending in a
    slash, or ending in a file name. Prose writes `product/taste/cost` to mean "or", and reading
    that as a directory tree is how a check of this shape earns a false finding per review round.

    The file half is the state-RELATIVE path, not the basename, because that is what the text
    actually asserts: "this file lives HERE". Judging the name alone was a hole — reverting the
    masterplan to `project_memory/masterplan.md` in the template left the entry-gate sweep green,
    although the move is one of the three §6.2 lines this lockstep is about (measured 2026-07-26).
    It also makes the claim extension-blind, so an `.md` or `.json` state file is covered without
    anyone maintaining a list of state suffixes.
    """
    # Prose punctuation is not part of the path. `>` is in the token alphabet for `<placeholder>`,
    # so a path ending an HTML comment (`… generated/session_brief.yaml.>`) drags the terminator and
    # the sentence's full stop into the file name.
    while token and token[-1] in ".>" and not (token[-1] == ">" and "<" in token):
        token = token[:-1]
    if not (token.startswith("project_memory/") or token.endswith("/")
            or "." in token.rsplit("/", 1)[-1]):
        return None, None
    segments = [s for s in token.split("/") if s]
    rooted = bool(segments) and segments[0] == "project_memory"
    if rooted:
        segments = segments[1:]
    if not segments or (not rooted and segments[0] not in state_tops):
        return None, None  # not a path into the state dir at all
    kept, truncated = [], False
    for segment in segments:
        if "<" in segment or "*" in segment:
            truncated = True
            break  # a placeholder or glob: everything below it is unknowable
        kept.append(segment)
    file_claim = None
    if kept and "." in kept[-1]:
        if not truncated:
            file_claim = "/".join(kept)
        kept.pop()  # the last segment is a file name, not part of the directory
    return "/".join(kept) or None, file_claim


def _assert_name_claim(where, name, at_path, shipped, shipped_paths, exempt_names):
    """Judge ONE file name an instruction text writes, against where the state tree ships that name.

    `at_path` is the state-relative path the text asserts, or None when the text says nothing about
    the location because it wrote a path OUTSIDE the state tree. A bare name is not location-free,
    though: a file written with no directory sits at the state root, so callers pass the name itself
    as `at_path` and the claim is judged as "this file is at the state root".

    Two rules, with deliberately different reach:
      * LOCATION, extension-blind: if the state tree ships this name, the text must put it where the
        template actually has it. This is what covers `.md`/`.tex`/`.html` state without a suffix
        list, and what catches reverting `product/masterplan.md` to a bare `masterplan.md`.
      * PHANTOM, `.yaml` only: a name nothing ships at all is a deleted monolith. Restricted to YAML
        because every V1 status store was one, while a `.md` name in prose is as often a file outside
        this repo (a role's `MEMORY.md`) or an example artifact (`outbox/…/2026-08-01_instagram.md`)
        as it is state — measured: broadening this half produced five such false findings and no true
        one. The price, stated rather than papered over: an invented `progress.md` is not caught.
    """
    in_state = {p for p in shipped_paths if p.rsplit("/", 1)[-1] == name}
    if in_state:
        assert at_path is None or at_path in in_state, (
            "%s puts `%s` at `%s`, but the state tree ships that name at %s. A moved state file "
            "whose old path stays in the prose sends the reader to a file that is not there — and a "
            "name written without a directory claims the state ROOT, because that is where such a "
            "file sits." % (where, name, at_path, " / ".join(sorted(in_state))))
    elif name.endswith(".yaml"):
        assert name in shipped or name in exempt_names, (
            "%s names `%s`, which this kit ships nowhere. Either it is a V1 monolith that "
            "must not be in instruction text any more, or it is deliberate — then add it to "
            "STATE_FILES_NOT_SHIPPED with its scope and the reason." % (where, name))


def _assert_state_claims(where, text, shipped, shipped_paths, state_dirs, state_tops,
                         exempt_names):
    """Judge every state claim ONE instruction text makes (the three claims below).

    Extracted so the kit sweep and the entry-gate sweep share one implementation: a second copy of
    this logic would be a second thing to keep in step with `ACTIVE_DIRS`, which is the failure mode
    both tests exist to prevent. The regexes are built from the constant on every call rather than
    passed in, so no caller can supply a stale set of type names.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ACTIVE_DIRS
    types = "|".join(sorted(ACTIVE_DIRS))
    # The number half of an item id: a run of the placeholder character, a glob, or a real number.
    # Written as a shape rather than the two spellings `nnnn`/`xxxx`, because prose also writes
    # `EXP-xxx` and a check that hinges on the exact placeholder width is a check on a typo.
    number = r"(?:[nN]+|[xX]+|\*|\d+)"
    # A path holding an item id names no single file: the kernel writes it at runtime, so no template
    # can ship it. Extension-blind on purpose — a DSN revision is `.html`, an experiment report
    # `.tex`, and pinning `.yaml` here made the path claim below demand a template for both.
    id_placeholder = re.compile(r"(?:%s)-%s" % (types, number))
    # an ITEM FILE: the type's own id shape as the last segment. That fixes the directory it must
    # sit in, which is ACTIVE_DIRS[type] and nothing else. Extension-blind for the same reason
    # `id_placeholder` is: what makes a token an item file is the ID, not the format it is stored
    # in. Pinned to `.yaml` this could never judge the only two non-YAML types ACTIVE_DIRS has —
    # `DSN` (`.html` revisions) and `WFR` — and this round put the first DSN path into a swept file
    # (`design/wireframes/DSN-0001.html` measured green before the fix, 2026-07-27).
    item_file = re.compile(r"(?:^|/)(%s)-%s(?:\.[A-Za-z0-9.]+)?$" % (types, number))
    # the `TYPE (dir/sub)` shape of the §6 ownership tables
    type_dir_pair = re.compile(r"`(%s)`[^(\n]{0,40}\(`?([A-Za-z0-9_./<>*-]*/[A-Za-z0-9_./<>*-]*)"
                               % types)
    suffixes = _state_file_suffixes(shipped_paths)
    for match in _bare_name_rx(suffixes).finditer(text):
        name = match.group(0)
        if "*" in name or "<" in name or id_placeholder.search(name):
            continue  # a glob or an id placeholder names no single file
        _assert_name_claim(where, name, name, shipped, shipped_paths, exempt_names)
    for match in _PATH_TOKEN_RX.finditer(text):
        token = match.group(0)
        claimed, claimed_file = _state_path_claim(token, state_tops)
        if claimed is None and claimed_file is None:
            # Not a path into the state dir — so it claims nothing about the LAYOUT, but it still
            # names a file, and `docs/product_requirements.yaml` or `.claude/progress.yaml` names a
            # deleted monolith just as loudly as the bare name does. Judging the basename here is
            # what the earlier basename-only cut did for free and the path rewrite dropped.
            tail = token.rstrip(".>").rsplit("/", 1)[-1]
            if (tail and tail.rsplit(".", 1)[-1] in suffixes and "*" not in token
                    and "<" not in token and not id_placeholder.search(tail)):
                _assert_name_claim(where, tail, None, shipped, shipped_paths, exempt_names)
            continue
        if claimed is not None:
            assert claimed in state_dirs or _dir_not_shipped(claimed), (
                "%s sends a role to `%s`, but `%s` is neither a directory this kit's template "
                "ships nor a value in kernel.backlog_types.ACTIVE_DIRS. A role told to read a "
                "directory that does not exist invents one — fix the path, or add it to "
                "STATE_DIRS_NOT_SHIPPED with the reason it is absent."
                % (where, token, claimed))
        if (claimed_file is not None and not id_placeholder.search(claimed_file)
                and not _dir_not_shipped(claimed_file.rsplit("/", 1)[0] if "/" in claimed_file
                                        else "")):
            # Two kinds of file are not a template's business and are judged elsewhere or not at
            # all: one carrying an item id (written at runtime — its DIRECTORY is the whole claim,
            # asserted just below), and one inside a subtree STATE_DIRS_NOT_SHIPPED excuses.
            assert (claimed_file in shipped_paths
                    or claimed_file.rsplit("/", 1)[-1] in exempt_names), (
                "%s puts `%s` at `%s`, but no kit template ships a file at that path. A moved "
                "state file whose old path stays in the prose sends the reader to a file that is "
                "not there — fix the path, or add the name to STATE_FILES_NOT_SHIPPED with its "
                "scope and the reason it is absent."
                % (where, claimed_file.rsplit("/", 1)[-1], claimed_file))
        item = item_file.search(token)
        if item and claimed in set(ACTIVE_DIRS.values()):
            # Judged where an item HOME is claimed, and only there. A file named after an item is
            # not always the item: `reports/EXP-nnnn.tex` is a document ABOUT the experiment and
            # `reports/` is a directory of the research template, so demanding
            # `experiments/active` for it would be wrong. What the constant is the authority on is
            # its own homes — put a file carrying an id into one of them and the type has to match.
            expected = ACTIVE_DIRS[item.group(1)]
            assert claimed == expected, (
                "%s puts a %s item in `%s`, but ACTIVE_DIRS says `%s`. The constant is the "
                "authority; prose that disagrees with it sends the role to the wrong place."
                % (where, item.group(1), claimed, expected))
    for match in type_dir_pair.finditer(text):
        item_type, claimed = match.group(1), match.group(2).lstrip("`")
        expected = ACTIVE_DIRS[item_type]
        assert claimed.rstrip("/") == expected or claimed.startswith(expected + "/"), (
            "%s tells the reader that `%s` lives in `%s`, but ACTIVE_DIRS says `%s` — this "
            "table is a prose copy of the constant and has drifted from it."
            % (where, item_type, claimed, expected))


def _kit_state_vocabulary(kit):
    """(shipped names, shipped state-relative paths, state directories, their tops) for one kit.

    The names and the paths answer different questions: a bare `progress.yaml` in prose can only be
    judged by name, while `project_memory/product/masterplan.md` states WHERE the file is and has to
    be judged against the template's own layout.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ACTIVE_DIRS
    shipped = set()
    for _dirpath, _dirs, files in os.walk(os.path.join(ROOT, "team-kits", kit)):
        shipped.update(files)
    shipped.update(os.listdir(os.path.join(ROOT, "team-kits")))
    template_root = os.path.join(ROOT, "team-kits", kit, "templates", "project_memory")
    state_dirs = set(ACTIVE_DIRS.values()) | set(STATE_DIRS_NOT_SHIPPED)
    shipped_paths = set()
    for dirpath, _dirs, files in os.walk(template_root):
        rel = os.path.relpath(dirpath, template_root).replace("\\", "/")
        if rel != ".":
            state_dirs.add(rel)
        for name in files:
            shipped_paths.add(name if rel == "." else "%s/%s" % (rel, name))
    return shipped, shipped_paths, state_dirs, {d.split("/")[0] for d in state_dirs}


def test_instruction_files_name_only_state_files_a_v2_project_has():
    """Every state path an instruction file names must exist in the kit it ships with.

    Derived from the template tree and from `kernel.backlog_types.ACTIVE_DIRS` — the two authorities
    on what a scaffolded project contains — so a monolith nobody thought to enumerate is caught by
    construction. This is the check that was missing: the mirror/§-reference tests and
    `assert name in text` all passed while three constitutions and nineteen SKILLs were rewritten.

    Three claims are judged, because instruction text makes three:
    1. a FILE, anywhere in the prose — not only inside backticks, and not only at the end of a
       backtick span. Both narrowings were real holes: `project_memory/progress.yaml` written without
       backticks, and `` `progress.yaml status:` `` with the name followed by other words, each passed
       an earlier cut of this test while naming a deleted monolith. Every file name is judged the same
       way, by `_assert_name_claim`: against where the state tree ships that name. A name written
       without a directory claims the state ROOT, which is what catches reverting
       `product/masterplan.md` back to `masterplan.md`; the extensions this applies to are derived
       from the state tree's own files, so `.md` state is covered without a suffix list.
    2. a DIRECTORY, which the earlier cut never looked at at all — so `invariant/active/` for
       `invariants/active/` was invisible although the §6 tables now carry a prose copy of
       ACTIVE_DIRS.
    3. the AGREEMENT between an item type and the directory the text puts it in, in both shapes the
       text uses: `` `SR` (system/active) `` and `procedures/active/PROC-nnnn.yaml`. This is what pins
       the prose copy against the constant instead of trusting it.

    What it cannot catch, stated so nobody reads more protection into it: a token whose FIRST segment
    is not a known state directory (`docs/progress.yaml`, `system/OSS`) makes no claim about the state
    LAYOUT, so only its file name is judged there and a directory typo is invisible unless the path is
    rooted at `project_memory/`; a path holding an item id is only judged on its directory, since no
    template can ship the file; everything under a `/**` entry of STATE_DIRS_NOT_SHIPPED is unjudged,
    because that layout is data rather than a template; and a file extension no state file uses is
    outside the name alphabet altogether (`_state_file_suffixes`).
    """
    for kit in ("dev-team", "research-team", "office-team"):
        vocabulary = _kit_state_vocabulary(kit)
        for path, text in _instruction_files(kit):
            _assert_state_claims(os.path.relpath(path, ROOT), text, *vocabulary,
                                 exempt_names=_exempt_names((ANY, KIT_ONLY)))


# -- the Evidence vocabulary in prose -------------------------------------------------------------
# `kind` and `result` are the two Evidence fields a GATE decides on, so the kernel closes both
# (`backlog_types.EVIDENCE_KINDS` / `EVIDENCE_RESULTS`). Every role that produces Evidence is told
# in prose which values to use, and that prose is hand-typed in six files — so a rename in the
# kernel leaves six texts instructing roles to type a value the kernel refuses, with nothing red.
# This is the same failure the state-path sweep above exists for, one field deeper.
#
# Three shapes, each a different KIND of claim:
_CLI_ARG_RX = re.compile(r"--(kind|result)\s+<?([a-z]+(?:\|[a-z]+)*)>?")
# ...a BARE `kind:` field claim. Anchored at the backtick, because a qualified one is about a
# different type's vocabulary: `APR.kind: analysis` is an approval's kind and `{kind: test|script}`
# is an INV check's, and neither is judged by the Evidence constants.
_FIELD_KIND_RX = re.compile(r"`kind:\s*([a-z]+)`")
# ...and an alternation written as prose (`test`/`review`/`acceptance`), which is how both
# constitutions state what the merge gate rests on.
_BACKTICK_RUN_RX = re.compile(r"`[a-z]+`(?:/`[a-z]+`)+")


def _evidence_vocabulary_claims(text):
    """Every Evidence-vocabulary claim in `text`, as (field, values, raw).

    `field` is "kind" or "result"; `values` is the SET the text offers, which is one element for an
    instruction ("--kind audit") and several for a choice ("--kind <test|review|acceptance>"). The
    distinction matters: a single value is only judged on membership, while a choice also claims to
    be the complete set of options for that field, and that claim is checkable against the constant.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import EVIDENCE_KINDS, EVIDENCE_RESULTS
    for match in _CLI_ARG_RX.finditer(text):
        yield match.group(1), set(match.group(2).split("|")), match.group(0)
    for match in _FIELD_KIND_RX.finditer(text):
        yield "kind", {match.group(1)}, match.group(0)
    for match in _BACKTICK_RUN_RX.finditer(text):
        words = set(re.findall(r"[a-z]+", match.group(0)))
        # A slash run is only a vocabulary claim when every one of its words IS one -- otherwise it
        # is some other list (`Edit`/`Write`), and reading it as an incomplete kind list would make
        # this test fire on prose that never mentioned Evidence.
        for field, vocabulary in (("kind", EVIDENCE_KINDS), ("result", EVIDENCE_RESULTS)):
            if words <= vocabulary:
                yield field, words, match.group(0)


def _texts_that_name_the_evidence_vocabulary():
    """(where, text) for everything that TELLS someone which kind/result to use.

    The instruction files of all three kits and the README, plus the refusal messages of every
    module the harness SHIPS — those are read by the same person, at the moment they have to act
    on them, and they name the command and its arguments just as the SKILLs do. Every shipped
    module rather than the merge gate alone, for the reason `_refusal_texts` reads raises as well
    as `block()` calls: which module stops a role is not something this check may know in advance.
    Read as RUNNING strings rather than as file text, so the module docstring's account of what V1
    did cannot satisfy the check (house rule: a check reads the part that runs).
    """
    for kit in KITS:
        for path, text in _instruction_files(kit):
            yield os.path.relpath(path, ROOT), text
    for path in _shipped_python_modules():
        yield os.path.relpath(path, ROOT), "\n".join(_refusal_texts(path))
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as fh:
        yield "README.md", fh.read()


def test_no_instruction_text_names_an_evidence_kind_or_verdict_the_kernel_refuses():
    """The prose vocabulary is pinned to the kernel's, in both directions.

    Membership is the first direction: a value outside `EVIDENCE_KINDS` / `EVIDENCE_RESULTS` is one
    the kernel refuses at capture, so the text would be teaching a role a command that cannot run.

    The second direction is the one that matters for the merge gate: wherever a text offers a
    CHOICE of kinds it is telling a delivery-judging role what its options are, and those are
    exactly `QA_EVIDENCE_KINDS`. `audit` appearing in such a list would promise that an audit run
    can open a merge — which `qa_verdicts` refuses — and a list missing one of the three would send
    a role to a kind the gate then never sees. `audit` remains legitimate as a SINGLE instruction
    (the auditor's own command line), which is why single values are judged on membership alone.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import EVIDENCE_KINDS, EVIDENCE_RESULTS, QA_EVIDENCE_KINDS
    complete = {"kind": QA_EVIDENCE_KINDS, "result": EVIDENCE_RESULTS}
    known = {"kind": EVIDENCE_KINDS, "result": EVIDENCE_RESULTS}
    seen = 0
    for where, text in _texts_that_name_the_evidence_vocabulary():
        for field, values, raw in _evidence_vocabulary_claims(text):
            seen += 1
            unknown = values - known[field]
            assert not unknown, (
                "%s writes `%s`, but %s is not in kernel.backlog_types.%s. The kernel refuses "
                "that value at capture, so the role is being told a command that cannot run."
                % (where, raw, ", ".join(sorted(unknown)),
                   "EVIDENCE_KINDS" if field == "kind" else "EVIDENCE_RESULTS"))
            if len(values) > 1:
                assert values == set(complete[field]), (
                    "%s offers `%s` as the choice of Evidence %s, but the set a merge rests on is "
                    "%s. A kind list with `audit` in it promises that an audit run opens a merge "
                    "(it never does); one missing a kind sends the role to a verdict the gate then "
                    "never reads."
                    % (where, raw, field, ", ".join(sorted(complete[field]))))
    # A floor, because the assertions above are vacuously true over text nobody reads: the shapes
    # are regexes over prose, and prose gets reformatted. 79 claims are measured today; well under
    # half of that means a shape stopped matching, not that the texts got shorter.
    assert seen >= 50, (
        "only %d Evidence vocabulary claims found — the role texts spell out the kinds and "
        "verdicts many times over, so this few means the shapes above stopped matching and the "
        "test is passing over prose it no longer reads." % seen)


# An `evidence` command line as a TEXT spells it: an inline-code span, so it ends at the closing
# backtick and not at the line break markdown wraps it on. Everything between is argument prose
# (`<TSK-nnnn>`, `"…"`, `%s`), which is why only the FLAG NAMES are read out of it. The command's
# own spelling is not written here — it is assembled from `kernel.cli.INVOCATION`, so this reader
# follows the entry point instead of having to be remembered when it moves.
def _evidence_call_rx():
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    return re.compile(re.escape(cli.INVOCATION) + r" evidence([^`]*)`")
_EVIDENCE_FLAG_RX = re.compile(r"--[a-z][a-z-]*")


def test_every_evidence_command_a_text_spells_names_every_argument_the_cli_requires():
    """A command line in an instruction is a promise that typing it works.

    The required arguments are read off the SHIPPED PARSER — `kernel.cli.build_parser`, the object
    argparse will actually evaluate — so making one of them mandatory cannot quietly leave six
    texts teaching a usage error. That is not hypothetical: `--artifact-ref` became required in
    this round precisely because every one of these texts already presented it as THE proof while
    the parser treated it as optional, and one gate remedy had left it out entirely.

    Only flag NAMES are compared. Whether `<TSK-nnnn>` is a real id is not a question a text can
    answer, but whether the flag is there at all is.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    evidence = [action for action in cli.build_parser()._subparsers._group_actions[0]
                .choices["evidence"]._actions if action.option_strings and action.required]
    required = {action.option_strings[0] for action in evidence}
    assert len(required) >= 4, required   # the parser itself must still be the strict thing
    seen = 0
    for where, text in _texts_that_name_the_evidence_vocabulary():
        for match in _evidence_call_rx().finditer(text):
            flags = set(_EVIDENCE_FLAG_RX.findall(match.group(1)))
            if not flags:
                continue    # the command named, not spelled out as a call
            seen += 1
            assert required <= flags, (
                "%s spells an `evidence` call `%s` that omits %s. `kernel.cli` requires that "
                "argument, so the role is being told a command line argparse rejects."
                % (where, match.group(1).rstrip(), ", ".join(sorted(required - flags))))
    # 13 call sites were measured when this was written (both gate_git copies, the three auditor
    # SKILLs, the QA and reviewer SKILLs). A floor rather than the number, because texts get
    # rewritten — but zero would mean the span shape stopped matching, not that the calls went.
    assert seen >= 8, "only %d spelled-out `evidence` calls found" % seen


# The two files that install to ~/.claude/CLAUDE.md and $CODEX_HOME/AGENTS.md. They are instruction
# text like a constitution, but they belong to NO kit: they run before one is installed and route to
# whichever kit the registry picks. That is why the per-kit sweep above never saw them — and why both
# kept telling the initializer to write `product_requirements.yaml` and a `progress.yaml` summary
# after those monoliths were deleted from all three kits (found by hand, 2026-07-26).
ENTRY_GATE_FILES = (os.path.join("user", "claude", "CLAUDE.md"),
                    os.path.join("user", "codex", "AGENTS.md"))


def test_entry_gates_name_only_state_files_some_kit_ships():
    """The same state-claim contract for the global entry gates, against the UNION of the kits.

    A kit-agnostic file may legitimately name an artifact only one kit ships (`business_profile.yaml`
    is office-only), so a per-kit judgement would be wrong here; the union is what "some kit ships
    this" means. Everything else is judged by the same code — except the exemption scope: an entry
    gate gets only the ANY exemptions, never the KIT_ONLY ones, because those excuse a deleted V1
    monolith on the grounds that a KIT's own hook still reads it, and an entry gate has no hooks.
    """
    union = (set(), set(), set(), set())
    for kit in ("dev-team", "research-team", "office-team"):
        for target, addition in zip(union, _kit_state_vocabulary(kit)):
            target |= addition
    for rel in ENTRY_GATE_FILES:
        path = os.path.join(ROOT, rel)
        assert os.path.isfile(path), "%s is the installed entry gate and must exist" % rel
        with open(path, encoding="utf-8", errors="ignore") as fh:
            _assert_state_claims(rel, fh.read(), *union, exempt_names=_exempt_names((ANY,)))


def test_the_eval_scenarios_name_only_state_files_a_v2_project_has():
    """`tools/eval/scenarios.yaml` is instruction text too — and the only one nothing else reads.

    Every scenario's `work_order` is a work order for a real role, `read_first` is a list of files
    that role is sent to open, and no runner, test or CI step parses the file: it is executed by a
    human running the eval by hand. So the sweeps are all it has, and the completion proof does not
    reach it either — that one judges the state-root PATH, while a scenario reverted to
    `read_first: [product_requirements.yaml PRD-0001]` names the monolith without a path and stayed
    green (measured 2026-07-26).

    Judged exactly like the entry gates: same union over the three kits, because a scenario names
    the artifacts of the kit it runs in, and the ANY exemptions only — a scenario has no hooks, so
    the KIT_ONLY licence for "a kit's own hook still reads this deleted V1 store" cannot apply.

    One documented limit of `_assert_state_claims` bites HARDER here than anywhere else, so it is
    repeated rather than referred to: a path whose FIRST segment is not a known state top makes no
    claim about the layout and only its file name is judged. Every `read_first` path in this file
    is written relative to the state root, so that first segment is always a state top and a typo
    in it (`procedure/active/PROC-0001.yaml`) takes the whole path out of judgement — measured
    green, 2026-07-27. In the kits' instruction text most paths are `project_memory/`-rooted and
    the same typo is caught; here nothing catches it.
    """
    union = (set(), set(), set(), set())
    for kit in KITS:
        for target, addition in zip(union, _kit_state_vocabulary(kit)):
            target |= addition
    rel = "tools/eval/scenarios.yaml"
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        _assert_state_claims(rel, fh.read(), *union, exempt_names=_exempt_names((ANY,)))


def test_kit_names_a_root_item_exactly_when_the_kernel_gives_it_one():
    """`ROOT_TYPE_BY_KIT` decides which kits HAVE a leading item — and nothing held that decision.

    Its `office-team: PR` entry was dropped in this lockstep (the office constitution knows no `PR`
    anywhere, and the entry gates were seeding a `PR-0001` no office role would ever read). The only
    other code reader is `test_root_item_globs_are_the_kernels_root_types`, which compares
    `set(values())` — so putting the line back leaves the whole suite green while the entry gates start
    seeding a PR for office again. The rule has two visible consequences and this pins both, per kit
    and per root type, so it holds for a kit or a root type nobody thought of here:

      * the SKELETON. A kit ships the storage directory of a root type exactly when that type is ITS
        root type; a `product/active/` in a kit that is not PR-led is a shipped, documented home for
        an item nobody seeds. Both office and research shipped one, and the state-claim sweep cannot
        see it: `product/active/PR-0001.yaml` is a VALID `ACTIVE_DIRS` path, so what is checked there
        is type-vs-directory, never "does this kit have that root type".
      * the INSTRUCTION TEXT. Same iff for an id of that type — office named `PR-0001` in the very
        README a fresh office project reads first.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ACTIVE_DIRS, ROOT_TYPE_BY_KIT
    for kit in ("dev-team", "research-team", "office-team"):
        own = ROOT_TYPE_BY_KIT.get(kit)
        template_root = os.path.join(ROOT, "team-kits", kit, "templates", "project_memory")
        shipped_dirs = {os.path.relpath(d, template_root).replace("\\", "/")
                        for d, _sub, _files in os.walk(template_root)} - {"."}
        for root_type in sorted(set(ROOT_TYPE_BY_KIT.values())):
            expected = root_type == own
            # the id shape, written as in `_assert_state_claims`: placeholder run, glob or number
            id_rx = re.compile(r"(?<![A-Za-z0-9_])%s-(?:[nNxX]+|\*|\d+)" % root_type)
            named = sorted(os.path.relpath(p, ROOT) for p, text in _instruction_files(kit)
                           if id_rx.search(text))
            assert (ACTIVE_DIRS[root_type] in shipped_dirs) is expected, (
                "%s %s `%s`, the home of `%s` items, but ROOT_TYPE_BY_KIT gives this kit %s. A root "
                "type's directory in a kit not led by it is a home for an item no entry gate seeds "
                "and no role owns; a missing one leaves the kit's own root item homeless."
                % (kit, "ships" if not expected else "does not ship", ACTIVE_DIRS[root_type],
                   root_type, own or "no root item at all"))
            assert bool(named) is expected, (
                "%s: instruction text %s a `%s` item (%s), but ROOT_TYPE_BY_KIT gives this kit %s."
                % (kit, "names" if named else "never names", root_type,
                   ", ".join(named) or "nowhere", own or "no root item at all"))


# ------------- the lockstep proof: which V1 root stores are gone, and which are not -------------

# The harness's own written record of what V1 was and where it went. A V1 path is the SUBJECT
# there — the spec's findings section quotes monolith sizes, the append-only log records the
# migration — so this is the one place the old paths are allowed to stand. Everywhere else in the
# repo a V1 path is a leftover: it either still reaches for the file or tells someone else to.
#
# `radar/` is in the second list for a related but distinct reason, worth saying rather than
# blurring: it is an APPEND-ONLY record — dated weekly reports and a triage log — that nobody edits
# after writing. A V1 path there is a quotation of the week it was written, not a pointer, and
# sweeping it would leave the suite one honest weekly report away from red. The residual, stated:
# `radar/README.md` describes the radar workflow rather than recording a week, so a V1 path
# creeping into THAT one would go unnoticed. It ships to no project and addresses no role, so the
# cost is a stale in-repo note.
#
# The root `README.md` USED to sit in the first list and does not any more, because it never met
# the definition: it is not a record of the migration but a description of what the harness IS,
# rewritten whenever that changes — the `radar/README.md` argument one directory up. The blanket
# exemption cost exactly what that argument predicts: for a whole round after the merge gate had
# been moved onto the Evidence store, the front page still told the reader the gate blocks EVERY
# merge and push because it reaches for the V1 report monolith — and nothing could go red
# (round-7 finding 10). Sweeping it is free: measured with this sweep's own reader, the file names
# no V1 path today. That is what makes the front page's account of a gate answerable to the gate.
# (Naming the offending path here would trip this very sweep, which reads `#` comments — the check
# demonstrating itself, and the reason the sentence above describes the claim instead of quoting it.)
MIGRATION_DOC_FILES = ("HARNESS_LOG.md",)
MIGRATION_DOC_TREES = ("docs/", "radar/")

# Trees that are not the repo's content: git's own store, caches, and the sandbox an e2e run builds.
_SWEEP_SKIP_DIRS = frozenset((".git", ".pytest_cache", "__pycache__", "node_modules",
                              ".e2e-sandbox"))


def _state_root_store(token, stores):
    """The V1 root store from `stores` that a path token puts at the state ROOT, or None.

    `stores` is passed IN rather than read from `conftest.V1_MONOLITHS` here, because there used to
    be two inventories with opposite verdicts (moved stores nothing may point at, versus stores
    another group still owned and which were asserted PRESENT). There is one again — the second
    half's readers were rewritten — and the parameter stays: it is what let the two share this
    folding instead of copying it, and it is what lets a caller ask about a subset.

    A token claims the state root when its LAST segment is a store name and the segment
    directly ABOVE it is `project_memory` — or there is no segment above it at all, which is how a
    composed path arrives once its runtime prefix has been dropped. What decides is the PARENT, not
    where `project_memory` sits in the token: `"%s/project_memory/progress.yaml" % root` is the
    second most common way this repo writes a path in a hook, and `"$repo/project_memory/…"` is the
    only way the shell half of the init script writes one. Anchoring the definition at the FIRST
    segment made both invisible, so the docstring below promised a protection this function did not
    give (measured 2026-07-26: three such reintroductions passed the sweep).

    Judging the parent is also what makes the sweep right about the two different fates of a
    monolith: `masterplan.md` MOVED, so `product/masterplan.md` claims nothing, while
    `project_memory/masterplan.md` claims the file is back where V1 kept it. `docs/progress.yaml`
    and `generated/filing_log.yaml` claim nothing either — neither parent is the state root.

    An inventory key that IS a glob is matched as one. One store was never a file name — the V1
    merge gate globbed for "whichever report file happens to be there" — and matching such a key
    literally means the entry only ever catches a re-introduced `glob("*report*.yaml")` call while
    `project_memory/test_reports.yaml`, the same store spelled out, walks past the inventory that
    claims to own it. Measured before widening: over both inventories and the whole tree this adds
    zero findings today, so it closes a blind spot rather than opening a front.
    """
    segments = [s for s in re.split(r"[/\\]", token.strip()) if s and s != "."]
    if not segments:
        return None
    name = segments[-1]
    if name not in stores:
        name = next((key for key in stores
                     if glob.has_magic(key) and fnmatch.fnmatch(segments[-1], key)), None)
    if name is None:
        return None
    if len(segments) == 1 or segments[-2] == "project_memory":
        return name
    return None


# The sweep's own path token. It differs from `_PATH_TOKEN_RX` in one character class, and the
# difference is the native path separator: the claim sweep reads PROSE about the state tree, where
# a backslash is a LaTeX command as often as a separator, but this sweep also reads the `.ps1` half
# of the init/scaffold pair, where a backslash-separated `project_memory\<store>` is the normal
# spelling and was therefore unjudged (measured 2026-07-26). Widening the shared regex would change
# what `_assert_state_claims` sees, so the two stay separate. A backslash run cannot become a false
# finding here: a token is only reported once it reduces to a store name directly under
# `project_memory`.
_SWEEP_PATH_TOKEN_RX = re.compile(r"[A-Za-z0-9_.<>*-]+(?:[/\\][A-Za-z0-9_.<>*-]*)+")


def _monolith_paths_in_text(text, stores):
    """Every state-root store path spelled out in `text`, as (store, token).

    The trailing full stop of a sentence is not part of the path — `.` is in the token alphabet
    because file names need it, so a path that ends a sentence arrives one character too long.
    """
    for match in _SWEEP_PATH_TOKEN_RX.finditer(text):
        token = match.group(0).rstrip(".")
        found = _state_root_store(token, stores)
        if found:
            yield found, token


def _callee_name(node):
    """The bare name of what a `Call` calls, ignoring how it was imported or qualified."""
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return node.func.id if isinstance(node.func, ast.Name) else None


def _path_call_parts(node):
    """The path segments a CALL composes, or None when the call composes no path.

    What makes a call a path composition is what it DOES with its arguments, not which module it
    came from: `join` appends its arguments to a base, `joinpath` appends them to the object it is
    called on, and a `Path` constructor builds one out of them. Matching the callable's own NAME is
    what makes that a definition rather than a list of spellings — `os.path.join`, `posixpath.join`
    and `from os.path import join` are one operation written three ways, and the previous cut knew
    only the first: `pathlib.Path(root, "project_memory", "progress.yaml")` and
    `root.joinpath("project_memory").joinpath("progress.yaml")` both walked past the sweep
    (measured 2026-07-27).

    The RECEIVER of a `join` is never a segment. For `os.path.join` it is the module; for
    `"/".join(parts)` it is the separator of a string operation that is not a path at all — and
    since neither contributes, the same rule covers both and `"/".join(...)` needs no exception.
    """
    name = _callee_name(node)
    if name is None:
        return None
    if name == "join":
        return list(node.args)
    if name == "joinpath" and isinstance(node.func, ast.Attribute):
        return [node.func.value] + list(node.args)
    if name.endswith("Path"):     # pathlib's constructors: Path, PurePath, WindowsPath, …
        return list(node.args)
    return None


def _path_parts(node):
    """The parts a path composition is built from, `None` for a part decided at runtime."""
    parts = _path_call_parts(node)
    if parts is not None:
        composed = []
        for arg in parts:
            composed.extend(_path_parts(arg))
        return composed
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.Add)):
        return _path_parts(node.left) + _path_parts(node.right)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    return [None]


def _is_composition(node):
    """Whether `node` glues several expressions into one path-shaped value.

    Two forms, and they are Python's, not this repo's: a CALL that composes (`_path_call_parts`)
    and a binary operator that concatenates — `/` for paths and `+` for the strings paths are made
    of. Naming the operators rather than the habits is the point: `state + "/progress.yaml"` is the
    same claim as `state / "progress.yaml"` and used to be invisible because only the second was
    listed (measured 2026-07-27).
    """
    return (_path_call_parts(node) is not None
            or (isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.Add))))


def _composed_paths(tree):
    """The tail of every path the module BUILDS, from the last runtime part onwards.

    A composed path holds no path SEPARATOR in any one literal, which is exactly why a plain text
    scan over Python source reads `os.path.join(state_dir, "progress.yaml")` as innocent. The tail
    is what the code asserts about the location, so `os.path.join("product", "masterplan.md")`
    yields `product/masterplan.md` and is silent, while a bare name joined onto a runtime directory
    yields that name alone and claims the root.
    """
    for node in ast.walk(tree):
        if not _is_composition(node):
            continue
        tail = []
        for part in _path_parts(node):
            tail = [] if part is None else tail + [part]
        if tail:
            yield "/".join(tail)


def _running_strings(tree):
    """Every string literal the module RUNS on — docstrings and bare string statements removed.

    A string that is a statement by itself executes nothing and opens nothing; it is a comment with
    quotes around it, and half this repo's honest explanations of what V1 did live in one. What is
    left is the set of strings a path can actually be built from.
    """
    prose = {id(node.value) for node in ast.walk(tree)
             if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
             and isinstance(node.value.value, str)}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in prose):
            yield node.value


def _python_comments(source):
    """Every `#` comment in `source`, asked of the tokenizer rather than matched out of the text.

    A `#` inside a string literal is not a comment, and the difference is what a regex over the raw
    text cannot see. `tokenize` is the same reader Python itself uses, so it needs no rule about
    quoting, line continuations or f-strings.
    """
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                yield token.string
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return  # unreadable source; `_monolith_paths_in_file` falls back to the raw-text sweep


def _monolith_paths_in_python(source, stores):
    """The same sweep for Python: the part that RUNS, plus the comments.

    The AST gives the executable half — string literals that are not prose statements, and the path
    compositions above. It does NOT give comments, and that is the half where the risk actually
    lives: a comment still spelling the V1 path is how the path gets copied back into the code
    beneath it. This test's own docstring promised comments were read while `.py` — the largest file
    type it sweeps — was the one type where they were not (measured 2026-07-27: a commented V1 path
    in a shipped hook passed). So the comments are read separately, through the tokenizer.

    Backslashes are normalised in the literals, because in a Python string a backslash IS a path
    separator on this platform — unlike in the prose files, where it is a LaTeX command as often as
    anything else and rewriting it would invent path tokens that were never there.
    """
    tree = ast.parse(source)
    for value in _running_strings(tree):
        for found, token in _monolith_paths_in_text(value.replace("\\", "/"), stores):
            yield found, token
    for comment in _python_comments(source):
        for found, token in _monolith_paths_in_text(comment, stores):
            yield found, token
    for path in _composed_paths(tree):
        found = _state_root_store(path, stores)
        if found:
            yield found, path


# A `Join-Path` whose second argument is a quoted literal — the PowerShell twin of
# `os.path.join`. The head may be a quoted literal or a plain word (`$dst`, `$env:X`); a
# parenthesised head is deliberately not matched, because a nested composition is beyond what a
# regex can fold and guessing at it would put a finding on `Join-Path (… "product") "masterplan.md"`,
# which claims the V2 home and not the root.
_PS_JOIN_PATH_RX = re.compile(r"Join-Path\s+(['\"][^'\"]*['\"]|[^\s()'\"]+)\s+(['\"])([^'\"]+)\2")


def _monolith_paths_in_powershell(text, stores):
    """`Join-Path` compositions that land a store at the state root, as (store, token).

    The same rule `_composed_paths` applies to Python: what the composition asserts about the
    LOCATION is the tail from the last runtime part onwards. A quoted head is part of the path; a
    head decided at runtime is not, so `Join-Path $dst "progress.yaml"` claims the bare name — the
    state root, wherever `$dst` points. The `.ps1` half of the init/scaffold pair is the half that
    runs on Windows, and it was the only path-building shape in the repo that nothing folded
    (measured 2026-07-26).
    """
    for match in _PS_JOIN_PATH_RX.finditer(text):
        head, tail = match.group(1), match.group(3)
        if head.startswith("-"):
            # A PARAMETER NAME, not a head. `… | Join-Path -ChildPath "masterplan.md"` takes its
            # parent from the pipeline, and `Join-Path -Path $a -ChildPath "b"` from an argument
            # this regex has already passed — either way the head is not in hand, and folding it as
            # if it were absent claims the state ROOT for a path whose root is unknown (measured
            # 2026-07-27: a false finding on the piped form). Nothing in the repo writes it, so the
            # choice is between a latent false alarm and a latent blind spot; a blind spot at least
            # cannot make a correct file fail.
            continue
        quoted_head = head[1:-1] if head[0] in "'\"" else None
        path = tail if quoted_head is None else quoted_head + "/" + tail
        found = _state_root_store(path, stores)
        if found:
            yield found, match.group(0)


def _monolith_paths_in_gitignore(text, stores):
    """The store paths a `.gitignore` REFERS to — which is only what it re-includes.

    An ignore pattern is a PROHIBITION, not a reference: it neither opens the file nor sends anyone
    to it, it forbids git from ever tracking it, which is what V2 wants for a V1 leftover too. The
    office kit ignores `project_memory/filing_log.yaml` on exactly that defensive ground (phase-0
    disposition, `.gitignore` row), and reading that line as a leftover pointer is what made the
    previous lockstep round delete it against its own disposition. A `!pattern` is the opposite —
    it re-includes the path — and stays judged.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("!"):
            for found, token in _monolith_paths_in_text(stripped[1:], stores):
                yield found, token


def _monolith_paths_in_file(path, text, stores):
    """Every state-root store path a file points at, judged in that file's own language."""
    if path.endswith(".py"):
        try:
            return list(_monolith_paths_in_python(text, stores))
        except SyntaxError:
            return list(_monolith_paths_in_text(text, stores))
    if os.path.basename(path) == ".gitignore":
        return list(_monolith_paths_in_gitignore(text, stores))
    found = list(_monolith_paths_in_text(text, stores))
    if path.endswith(".ps1"):
        found += list(_monolith_paths_in_powershell(text, stores))
    return found


def _sweep_state_root(stores):
    """(repo-relative file, store, token) for every place in the repo that spells one of `stores`.

    One traversal shared by the two verdicts the inventories carry — "must be gone" and "is still
    here" — so neither can be measured with a reader the other does not have.
    """
    for rel, path, text in _sweepable_files():
        for store, token in _monolith_paths_in_file(path, text, stores):
            yield rel, store, token


def _sweepable_files():
    """Every file of the repo that is not the harness's own record of the migration."""
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in _SWEEP_SKIP_DIRS)
        for name in sorted(files):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            if rel in MIGRATION_DOC_FILES or rel.startswith(MIGRATION_DOC_TREES):
                continue
            with open(path, "rb") as fh:
                data = fh.read()
            if b"\x00" in data:
                continue  # binary; a path token in a PNG is a coincidence, not a reference
            yield rel, path, data.decode("utf-8", errors="replace")


def test_the_state_root_ships_no_v1_monolith():
    """No kit template puts a V1 monolith back into `project_memory/`.

    The first half of the lockstep, and the half that needs no text at all: a monolith is a file at
    the state ROOT, so shipping one is visible in the template tree itself, whatever the instruction
    text says about it.

    Only the ROOT is judged, and the reason is `product/masterplan.md`: a monolith NAME can have a
    legitimate V2 home, so "no file with that basename anywhere" would be false. A monolith name
    reappearing deep in the tree (`product/progress.yaml`) is therefore not caught here — what would
    catch it is prose sending a role to it, which
    `test_instruction_files_name_only_state_files_a_v2_project_has` judges against this same tree.
    """
    for kit in KITS:
        template_root = os.path.join(ROOT, "team-kits", kit, "templates", "project_memory")
        for dirpath, _dirs, files in os.walk(template_root):
            rel = os.path.relpath(dirpath, template_root).replace("\\", "/")
            for name in files:
                at = name if rel == "." else "%s/%s" % (rel, name)
                assert not _state_root_store(at, conftest.V1_MONOLITHS), (
                    "%s ships `%s` — a V1 monolith at the state root (%s). V2 keeps no state "
                    "there; the state is one file per item."
                    % (kit, at, conftest.V1_MONOLITHS[name]))


def test_the_monolith_inventory_names_real_v2_successors():
    """Where each monolith WENT is prose in `conftest.V1_MONOLITHS` — pin it to the constant.

    The inventory is the one place the V1 names are written down, and every value says which V2
    directory took the state over. That is a prose copy of `ACTIVE_DIRS`, and a prose copy of a
    constant in this repo has drifted from it once per review round — so it is judged by the same
    code as a constitution's ownership table, against the union of the three kits (the inventory is
    kit-agnostic: `hypotheses/active` exists only in research, `procedures/active` only in office).

    Measured reach, so nobody reads the pin as tighter than it is: putting a type in another type's
    home (`system/active/TSK-nnnn.yaml`), a typo below a real state top (`tasks/activ/`) and the
    masterplan back at the root all fail. Two do NOT, and both are the documented limits of
    `_assert_state_claims`: a typo in the TOP segment itself (`task/active/`) reads as a path
    outside the state tree and is judged only on its file name, and anything under a
    `STATE_DIRS_NOT_SHIPPED` entry (`generated/…`) has no template to be checked against.
    """
    union = (set(), set(), set(), set())
    for kit in KITS:
        for target, addition in zip(union, _kit_state_vocabulary(kit)):
            target |= addition
    _assert_state_claims("conftest.V1_MONOLITHS", " ".join(conftest.V1_MONOLITHS.values()),
                         *union, exempt_names=_exempt_names((ANY,)))


def test_nothing_shipped_still_spells_a_v1_monolith_path():
    """No file outside the migration documentation names a MOVED monolith AT THE STATE ROOT.

    This is the proof for the stores `conftest.V1_MONOLITHS` names, and it now names all of them.
    For a round it named fewer, while three more — the two guidelines files and the office PROC
    registry — sat in a second inventory asserted PRESENT, because shipped code still read them and
    repairing it belonged to another group. Those readers were rewritten, so the three moved in
    here and the second inventory is gone; green now means "no shipped file points at a V1
    state-root store" rather than "…at one of the subset this once covered".
    HOW MANY there are is not written here or in the failure message: both read `len()` off the
    inventory. The number in this docstring said eleven over a dict of fifteen for a round, which
    is this sweep's own subject matter one level up.

    It is a claim about PATHS, not about names. The
    names survive on purpose: `filing_log.yaml` is what spec II.9 will call a regenerated scan
    index, `masterplan.md` is a file that moved rather than died, and every honest "V1 read this,
    V2 does not" comment in the hooks has to be able to say which file it means. What must not
    survive is the LOCATION — `project_memory/<monolith>` is a place V2 has nothing at, so
    whatever still points there either opens a file that is not there or sends a role to it.

    Python is read through its AST plus its tokenizer: docstrings and bare string statements are
    dropped (a comment with quotes around it cannot open anything), path COMPOSITIONS are folded
    first because none of them puts a separator inside any single literal (`_is_composition`), and
    the `#` comments are read back in through `tokenize`. PowerShell gets the same fold for its
    `Join-Path`. Every other file is read whole, comments included — everything except a
    `.gitignore`, whose one exception is below. Reading comments is stricter than necessary and
    deliberately so, since a comment that still spells the V1 path is how the path gets copied back
    into the code beneath it; that reason had been written here for a round while `.py`, the
    largest type swept, was the one type whose comments were NOT read.

    One file type is read looser rather than stricter, and it is the one whose lines are not
    references at all: in a `.gitignore` only a re-inclusion (`!path`) points AT a file, while a
    plain pattern forbids it — see `_monolith_paths_in_gitignore`.

    What this does NOT judge, so nobody reads more into it: a BARE monolith name that is not part
    of a path. In a kit's instruction text and in the entry gates such a name IS judged — against
    the shipped template tree, by `test_instruction_files_name_only_state_files_a_v2_project_has`,
    which owns the registry of names V2 still deliberately talks about. Everywhere else it is
    judged by nobody: a hook or a fixture that hands `"progress.yaml"` to a helper which joins it
    onto the state directory somewhere else passes here, because the join this reads is the one at
    the call site. The same goes for a path assembled at runtime from pieces the AST cannot see.
    """
    offences = []
    for rel, _store, token in _sweep_state_root(conftest.V1_MONOLITHS):
        offences.append("%s: `%s` (%s)"
                        % (rel, token, conftest.V1_MONOLITHS[_state_root_store(
                            token, conftest.V1_MONOLITHS)]))
    # the COUNT comes from the inventory, not from prose: it said "eleven" while the dict held
    # fifteen, which is the same class of rot this whole sweep exists to catch, in the sweep's own
    # failure message
    assert not offences, (
        "these still point at one of the %d MOVED V1 monoliths in the state root:\n  %s"
        % (len(conftest.V1_MONOLITHS), "\n  ".join(sorted(set(offences)))))


def test_a_store_the_inventory_records_as_a_glob_is_matched_as_a_glob():
    """One inventory key is a PATTERN, and reading it literally left the store half-guarded.

    The V1 merge gate did not open a named file, it globbed the state root for "whichever report
    file happens to be there", so `conftest.V1_MONOLITHS` records the store as `*report*.yaml`.
    Matched by string equality that entry catches only a re-introduced `glob("*report*.yaml")`
    call — while `project_memory/test_reports.yaml`, the very same store written out, is a path
    the inventory claims to own and nothing checks. Both spellings are the regression; both are
    findings now.

    The last two assertions are the counter-direction, so the widening cannot be satisfied by
    matching more or less everything: the parent still decides, and a name outside every pattern
    is still no store.

    The tokens are ASSEMBLED rather than written out, for two reasons that point the same way:
    the pattern comes from the inventory instead of being retyped here, and the file this test
    lives in is itself swept — a literal `project_memory/<store>` in it would be the very
    regression the sweep reports, found by the sweep, in the test that proves the sweep works.
    """
    monoliths = conftest.V1_MONOLITHS
    root, elsewhere = "project_memory/", "docs/"
    pattern = next(key for key in monoliths if glob.has_magic(key))
    spelled_out = "test_reports.yaml"
    assert fnmatch.fnmatch(spelled_out, pattern), "the fixture must be an instance of the pattern"
    assert _state_root_store(root + pattern, monoliths) == pattern
    assert _state_root_store(root + spelled_out, monoliths) == pattern
    assert _state_root_store(elsewhere + spelled_out, monoliths) is None
    assert _state_root_store(root + "project_config.yaml", monoliths) is None


# `test_the_open_v1_root_store_couplings_are_still_exactly_these` STOOD HERE and is gone with the
# inventory it read. It asserted, in both directions, that exactly three V1 root stores still had
# shipped readers — so that "the sweep is green" could not be read as "no V1 coupling is left"
# while `guard_guidelines` was inert and two office scripts could not start. Its own docstring said
# it would go red the day a coupling was repaired, and the error message said what to do then: move
# the store's name into `V1_MONOLITHS`. All three were repaired in one release and all three names
# moved, which leaves nothing for that test to assert about and the completion proof above owning
# every V1 root store. Deleting it is the bargain being kept, not a check being dropped: an
# equality against an empty inventory could never have gone red again.


# ---- ...and the blockage that MOVED rather than migrated with the store it used to live in ----

# Every suffix that makes a file RUNNABLE BY NAME on either platform: nothing on POSIX, the
# default Windows `PATHEXT` set, the two spellings the Python launcher adds, and the two script
# suffixes an installer drops when it wants one word to work on both. Taken as the constant it is
# rather than from the runner's own `PATHEXT`, because the question is what a ROLE's shell would
# execute in a scaffolded project, not what this machine happens to be configured for.
_EXECUTABLE_SUFFIXES = ("", ".com", ".exe", ".bat", ".cmd", ".vbs", ".vbe", ".js", ".jse",
                        ".wsf", ".wsh", ".msc", ".py", ".pyw", ".ps1", ".sh")


def _invocable_as(word, path):
    """Would a shell run `path` when a role types `word`?

    What makes a file a COMMAND is its NAME: the stem is the word typed, and the suffix is one the
    shell or `PATHEXT` executes. That is the definition, so a shim shipped as `harness`,
    `harness.cmd` or `harness.ps1` is caught by the same rule, and a `HARNESS_LOG.md` is not a
    command however much of the word it starts with.
    """
    stem, suffix = os.path.splitext(os.path.basename(path))
    return stem.lower() == word.lower() and suffix.lower() in _EXECUTABLE_SUFFIXES


def _installer_scripts():
    """Every installer script this repo ships — an install POSITION, not a list of paths.

    The `install.*` pair at the root (harness → user home) and every `*.sh`/`*.ps1` under
    `team-kits/` (home → project: `scaffold_team`, `init_project_memory`). Written out as four
    paths, this reader did not contain `init_project_memory.*` — the step the global entry gate
    calls the deterministic one — so a shim generated there was measured to pass it.
    """
    for rel in ("install.sh", "install.ps1"):
        if os.path.isfile(os.path.join(ROOT, rel)):
            yield rel
    for path in sorted(glob.glob(os.path.join(ROOT, "team-kits", "*.sh"))
                       + glob.glob(os.path.join(ROOT, "team-kits", "*.ps1"))):
        yield os.path.relpath(path, ROOT).replace(os.sep, "/")


# THE INSTALLER-TEXT READER THAT USED TO STAND HERE IS GONE, and the reason is worth one comment.
# It answered "does an installer WRITE a file a shell would run as <word>" by finding a
# file-creating line and reading every identifier-shaped token on it — the fallback for the
# platform whose installer chain this host cannot execute. Measured against the entry point that
# shipped: it finds nothing, and nothing is the correct answer for it. Both scaffolds copy the
# repo templates in a generic loop (`cp "$KIT/templates/repo/$rel" "$dst"`), so the file's name
# never appears on the writing line at all — it is a directory walk, not a spelling. What decides
# instead is the KIT-OWNED branch inside that loop, and
# `test_both_installers_own_the_entry_point_like_the_other_kit_scripts` reads exactly that, in
# both installers, for both platforms.


def _project_the_installers_produce(tmp_path):
    """Scaffold a real project with the shipped installers; return (repo, every path created).

    THE MEASUREMENT, as opposed to the text reader above: what the installers PUT ON DISK answers
    "does a role get a `harness` command" without needing any rule about how a shell script spells
    a file name. A name held in a variable, composed by `Join-Path`, or written by a `printf` in a
    file no list mentions all show up here as the same thing — a file in the project. The repo
    itself comes back too, because the same question has a second half — does that file WORK — and
    a second scaffold would only measure the installers twice.

    The platform's own pair is run (`*.ps1` on Windows, `*.sh` elsewhere), so the check measures
    where it stands and never skips. The trust recorder is removed from the staging first: it
    writes `.claude/kit_state.json` and no executable, so it can hide nothing — and running it
    would tie this pin to whether somebody has run `bump_kit_version.py`, which is the coupling
    that drops a dozen unrelated tests with an off-topic message.
    """
    home, repo = tmp_path / "home", tmp_path / "repo"
    kits = home / ".claude" / "team-kits"
    shutil.copytree(os.path.join(ROOT, "team-kits"), str(kits),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".*_cache"))
    if (kits / "write_kit_state.py").is_file():
        os.remove(str(kits / "write_kit_state.py"))
    os.makedirs(str(repo), exist_ok=True)
    subprocess.run(["git", "init", "-q", str(repo)], capture_output=True, timeout=60)
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
               PYTHONPATH=os.pathsep.join(path for path in sys.path if path))
    if os.name == "nt":
        def run(script, *args):
            return subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                 str(kits / (script + ".ps1")), "-Team"] + list(args),
                cwd=str(repo), capture_output=True, text=True, env=env, timeout=600)
    else:
        def run(script, *args):
            return subprocess.run(
                ["bash", str(kits / (script + ".sh"))] + list(args),
                cwd=str(repo), capture_output=True, text=True, env=env, timeout=600)
    for script in ("init_project_memory", "scaffold_team"):
        proc = run(script, "dev-team")
        assert proc.returncode == 0, "%s failed:\n%s%s" % (script, proc.stdout, proc.stderr)
    created = []
    for base, dirs, files in os.walk(str(repo)):
        dirs[:] = [d for d in dirs if d != ".git"]
        created += [os.path.join(base, name) for name in files]
    return repo, created


def _run_project_hook(repo, hook, command, agent_id=None):
    """One of the PROJECT's own hooks, as a real process, on a real shell payload.

    The project's copy under `.claude/hooks`, not this repo's kit source, and with no
    `$HARNESS_KERNEL_PATH`: the question these tests ask is what a scaffolded project does, and an
    override would hand the gate a kernel the project did not install. `PYTHONPATH` is dropped for
    the same reason — the suite's own path is the one place `kernel` is importable by name.
    """
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["CLAUDE_PROJECT_DIR"] = str(repo)
    payload = {"tool_name": "Bash", "tool_input": {"command": command},
               "cwd": str(repo), "hook_event_name": "PreToolUse"}
    if agent_id:
        payload["agent_id"] = agent_id     # what a SUBAGENT's payload carries (spike S3)
    return subprocess.run(
        [sys.executable, "-B", os.path.join(str(repo), ".claude", "hooks", hook)],
        input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=120)


def _shell_gates_of(repo):
    """Every PreToolUse hook THIS PROJECT registered that FIRES ON A BASH CALL.

    Read from the wiring rather than named here: a gate added to the matcher is covered on the day
    it ships, and "every shell gate allows it" stays a claim about the set the provider will run.

    THE MATCHER IS A TOOL LIST, NOT A STRING, and reading it as a string made this reader narrower
    than the provider. It compared `== "Bash|PowerShell"`, so `gate_filing.py` -- registered by the
    office kit on `Bash|PowerShell|Edit|Write|MultiEdit` -- was invisible although it runs on every
    Bash call. Measured 2026-07-31: string-equality sees dev 8 / office 5 / research 6; splitting
    the matcher sees dev 8 / office 6 / research 6, and the office claim of "5" in the shipped
    entry point was an artefact of this line. Same defect class as the "eight gates" text it was
    used to correct, one layer down.
    """
    with open(os.path.join(str(repo), ".claude", "settings.json"), encoding="utf-8") as handle:
        return _shell_gates_of_settings(json.load(handle))


def _shell_gates_of_settings(settings):
    """The same question asked of a settings MAPPING, so a kit source can be measured too."""
    return [os.path.basename(entry["command"].split()[-1].strip('"'))
            for group in settings["hooks"]["PreToolUse"]
            if "Bash" in (group.get("matcher") or "").split("|")
            for entry in group["hooks"]]


def test_the_evidence_the_merge_gate_demands_has_an_installed_producer(tmp_path):
    """The merge blockage is GONE, and this run is what says so — not a path this test names.

    It replaces the pin that recorded the opposite (`conftest.NO_INSTALLED_EVIDENCE_PRODUCER_CLAIM`
    and its three doc siblings, deleted together with the caveat in every shipped text). The SHAPE
    is kept, because the shape is what made that pin honest: the producer is read off the parser
    argparse evaluates, the INSTALLATION is measured by running the shipped installers, and the
    consequence is measured in the gate that has it.

    Four steps, in the order a role meets them:

      * the PRODUCER, off `kernel.cli.build_parser()`: an `evidence` subcommand, and a `prog` that
        is the one sanctioned spelling. Renaming either moves this assertion with it. `prog` is
        asserted because argparse prints it in every usage and error line, so a role who retypes
        what the parser printed must get a command that exists.
      * the INSTALLATION: the shipped installers really put a file at `cli.ENTRY_POINT` into a
        project they built. Measured by RUNNING them, because a shell script has more ways to write
        a file than a reader has rules about text.
      * the RUN, through the gates a role's shell command actually meets: the merge refused for
        want of Evidence, then the entry point's own command line put through every
        `Bash|PowerShell` PreToolUse hook this project registered AND then executed, then the same
        merge again. Both halves are here because either alone proves nothing — an Evidence
        recorded by a command line the gates refuse is no remedy, and a command line the gates
        allow but that records nothing is no producer.
      * and NO BYTECODE in the hashed bundle afterwards. The shim carries
        `sys.dont_write_bytecode` instead of asking a role to remember `-B`, so the sanctioned
        spelling has to be safe without the flag; the flagless `-m` form was measured reporting
        the bundle as tampered with in the same run that changed it.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    parser = cli.build_parser()
    subcommands = parser._subparsers._group_actions[0].choices
    assert "evidence" in subcommands, "the Evidence producer is not on the kernel's command surface"
    assert parser.prog == cli.INVOCATION, (
        "argparse prints `%s` in every usage and error line, which is not the sanctioned spelling "
        "`%s` — a role who retypes what the parser printed types a command that does not exist"
        % (parser.prog, cli.INVOCATION))

    repo, created = _project_the_installers_produce(tmp_path / "scaffold")
    assert len(created) > 20, (
        "the installers produced almost nothing (%d files) — this reader stopped measuring rather "
        "than the scaffold stopping work" % len(created))
    entry = os.path.join(str(repo), *cli.ENTRY_POINT.split("/"))
    assert entry in created, (
        "the installers built a project without %s. Every shipped remedy names that path, so a "
        "project that lacks it is handed command lines it cannot run." % cli.ENTRY_POINT)
    assert _invocable_as("harness", entry), entry

    capture_root_item(repo)
    merge = "git merge feat/PR-0001-x"
    blocked = _run_project_hook(repo, "gate_git.py", merge)
    assert blocked.returncode == 2, blocked.stdout + blocked.stderr
    assert "no QA Evidence for PR-0001" in blocked.stderr, blocked.stderr

    arguments = ["evidence", "--kind", "test", "--result", "pass", "--related", "PR-0001",
                 "--summary", "qa run green", "--artifact-ref", "staging/TSK-0001/run.log"]
    record = "%s %s" % (cli.INVOCATION, " ".join(arguments))
    for gate in _shell_gates_of(repo):
        seen = _run_project_hook(repo, gate, record)
        assert seen.returncode == 0, (
            "%s refuses the one command line that records an Evidence:\n%s" % (gate, seen.stderr))
    # THE SUITE'S OWN BYTECODE SETTINGS ARE REMOVED, not inherited. `conftest` exports
    # `PYTHONPYCACHEPREFIX` so the tests never litter the tree, and a subprocess that inherits it
    # writes no `.pyc` wherever the shim stands on the question — measured: with
    # `sys.dont_write_bytecode` flipped to False in a copy of the kit outside this repo, the last
    # assertion of this test stayed GREEN until these two names were dropped. A role's shell has
    # neither variable, so neither may decide anything here.
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTHONPATH", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE")}
    ran = subprocess.run([sys.executable, os.path.join(*cli.ENTRY_POINT.split("/"))] + arguments,
                         cwd=str(repo), capture_output=True, text=True, env=env, timeout=120)
    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert "test: pass" in ran.stdout, ran.stdout

    opened = _run_project_hook(repo, "gate_git.py", merge)
    assert opened.returncode == 0, (
        "the merge is still refused after the Evidence was recorded:\n%s" % opened.stderr)

    cached = [os.path.join(base, name)
              for base, _dirs, files in os.walk(os.path.join(str(repo), ".claude"))
              for name in files if name.endswith((".pyc", ".pyo"))]
    assert not cached, (
        "running the entry point cached bytecode into the tree `hook_bundle_hash` measures, so the "
        "next SessionStart would drop the project to `hooks_trust_required`: %s" % cached)


def test_the_entry_point_refuses_the_one_argument_the_write_gate_would_refuse(tmp_path):
    """`--root` is unrunnable AND wrong, so the entry point says so instead of forwarding it.

    Unrunnable: `gate_write_scope` refuses a write-capable pipeline whose command line NAMES the
    state directory, which is the whole reason the entry point resolves it itself. Wrong: the
    kernel reads the flag RELATIVE to the current directory, so the same argument addresses a
    different — usually nonexistent — directory from any subdirectory. Without a refusal that says
    this, a role who copies `--root project_memory` out of an older document meets the write gate's
    rc 2 and no explanation.

    Four spellings are run, and the last three are why the shim asks the parser instead of
    matching text: argparse accepts any unambiguous prefix AND the `=` form, so `--r`, `--ro`,
    `--roo` and `--root=x` all bind to `--root` on a parser whose only long option that is. A list
    would have covered the first line and none of the rest.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    repo, _created = _project_the_installers_produce(tmp_path / "scaffold")
    capture_root_item(repo)
    refused = _run_project_hook(
        repo, "gate_write_scope.py",
        "%s --root project_memory evidence --kind test" % cli.INVOCATION)
    assert refused.returncode == 2 and "canonical state directory" in refused.stderr, refused.stderr

    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    for flag in (["--root", "project_memory"], ["--r", "project_memory"],
                 ["--roo", "project_memory"], ["--root=project_memory"]):
        proc = subprocess.run(
            [sys.executable, os.path.join(*cli.ENTRY_POINT.split("/"))] + flag +
            ["evidence", "--kind", "test", "--result", "pass", "--related", "PR-0001",
             "--summary", "x", "--artifact-ref", "staging/a.log"],
            cwd=str(repo), capture_output=True, text=True, env=env, timeout=120)
        assert proc.returncode == 2, "%s was accepted: %s%s" % (flag, proc.stdout, proc.stderr)
        assert "`--root` does not belong" in proc.stderr, (flag, proc.stderr)
    # ...and the refusal is a refusal: no Evidence was recorded on the way to it. Asked as "is
    # there an item", not "is the directory empty" — the scaffold seeds a `.gitkeep` there.
    recorded = [name for name in os.listdir(evidence_dir(repo))] if os.path.isdir(
        evidence_dir(repo)) else []
    assert not [name for name in recorded if name.lower().endswith((".yaml", ".yml"))], (
        "the entry point wrote an Evidence and then refused the command line that wrote it: %s"
        % recorded)


def test_both_installers_own_the_entry_point_like_the_other_kit_scripts():
    """The entry point is KIT-OWNED, in the installer pair for BOTH platforms.

    The run above proves it for the platform this suite is on; the other platform's chain cannot be
    executed here, so its half is read — but neither the installers nor the branch is a list. EVERY
    installer this repo ships is asked (`_installer_scripts`, which is an install POSITION rather
    than four paths), and the ones that HAVE an always-overwrite branch are the ones that owe an
    answer: the branch is located by the file that has been in it longest (`scripts/kit_checks.py`),
    and the question is whether `cli.ENTRY_POINT` sits in the same expression. Copy-if-absent is
    the wrong class for it: a project keeping an old entry point keeps an old bridge into the
    enforcement layer, and every shipped remedy names that path.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    checked = []
    for rel in _installer_scripts():
        with open(os.path.join(ROOT, *rel.split("/")), encoding="utf-8") as handle:
            text = handle.read()
        # LOGICAL lines: a shell condition wraps with a trailing `\` and PowerShell with a
        # backtick, and a reader that stops at the newline would report a name on the second half
        # as absent — which is how a list of one condition becomes a list of one LINE.
        text = re.sub(r"[\\`]\r?\n\s*", " ", text)
        owning = [line for line in text.splitlines()
                  if "scripts/kit_checks.py" in line and not line.lstrip().startswith("#")]
        if not owning:
            continue        # this installer has no always-overwrite branch, so it owes nothing
        checked.append(rel)
        assert any(cli.ENTRY_POINT in line for line in owning), (
            "%s decides which repo templates are always overwritten without naming %s, so a "
            "project that already has an old one keeps it forever:\n%s"
            % (rel, cli.ENTRY_POINT, "\n".join(owning)))
    # One per platform. A floor rather than an equality, so a third installer gaining the branch is
    # covered too — but zero would mean the reader stopped matching, not that nothing owes it.
    assert len(checked) >= 2, (
        "only %s carry an always-overwrite branch; the reader found nothing to judge" % checked)


def _markdown_blocks(text):
    """The units a reader takes in at once: a paragraph, a list item, a table row.

    Block granularity is the point of the check that uses this. The previous version asked only
    whether the CAVEAT appeared anywhere in the FILE, and the regression it was written for
    survived it: deleting the honest sentence out of the README's merge-gate bullet left the
    phrase standing in an unrelated paragraph about the write-lock, four hundred lines away, and
    nothing went red (measured 2026-07-28).
    """
    current = []
    for line in text.splitlines():
        if not line.strip():
            if current:
                yield "\n".join(current)
            current = []
            continue
        if current and re.match(r"^\s*(?:[-*+]|\d+\.)\s|^\|", line):
            yield "\n".join(current)
            current = [line]
            continue
        current.append(line)
    if current:
        yield "\n".join(current)


def _folded_string(node, names, functions, depth=0):
    """The value a string expression PRODUCES, or None when it is not decidable statically.

    A refusal text is assembled, not written: `"…" % target`, a shared tail added with `+`, a
    helper that returns the whole thing. Reading the literals instead answers about fragments —
    the caveat added as `… + _NOT_INSTALLED` is a second literal, and a check over literals would
    report the first one as missing it while the role reads the two together (measured while
    writing this). So the pieces are put back together the way the interpreter would:

    * `%` yields its TEMPLATE — the arguments are runtime values and no static reader can have
      them, while the template is the sentence a role reads.
    * a call to a module-level helper yields what that helper returns, so a remedy factored out
      into a function is still read.
    """
    if depth > 8:
        return None
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.Name):
        return names.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        return _folded_string(node.left, names, functions, depth + 1)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _folded_string(node.left, names, functions, depth + 1)
        right = _folded_string(node.right, names, functions, depth + 1)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        body = functions.get(node.func.id)
        if body is None:
            return None
        parts = [_folded_string(stmt.value, names, functions, depth + 1)
                 for stmt in ast.walk(body)
                 if isinstance(stmt, ast.Return) and stmt.value is not None]
        parts = [part for part in parts if part]
        return "\n".join(parts) or None
    return None


def _refusal_texts(path):
    """Every text this shipped module hands a ROLE at the moment it stops them.

    A refusal is defined by WHAT IT DOES to the role, not by which function spells it: a hook
    stops with `block(...)`, and the kernel stops by RAISING one of its own error types, which
    `_kernel.run_gate` and the CLI turn into the same stderr the role reads. Reading only
    `block()` was a reader that knew three source KINDS, and it missed `state.py` handing a
    blocked role an `evidence` command line without the caveat every other text then carried —
    the enumeration failure, in the check written to replace an enumeration.

    Assembled as the interpreter would (`_folded_string`), so a message built from a template
    plus a shared tail is read the way the role reads it.
    """
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    names, functions = {}, {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = node
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            value = _folded_string(node.value, names, functions)
            if value is not None:
                names[node.targets[0].id] = value
    for node in ast.walk(tree):
        call = None
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else \
                getattr(node.func, "id", None)
            if name == "block":
                call = node
        elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            name = node.exc.func.attr if isinstance(node.exc.func, ast.Attribute) else \
                getattr(node.exc.func, "id", None)
            if name and name.endswith("Error"):
                call = node.exc
        if call is None:
            continue
        for argument in list(call.args) + [kw.value for kw in call.keywords]:
            text = _folded_string(argument, names, functions)
            if text:
                yield text


def _shipped_python_modules():
    """Every Python module this harness INSTALLS into a project.

    The kits' hooks and the kernel — which is what "a shipped text" means for the checks below:
    a role in a scaffolded project can be stopped by any of them, and reads whatever the one that
    stopped them says. Listing the modules that happened to carry a sentence is how the previous
    reader missed `kernel/state.py`.
    """
    for kit in KITS:
        for path in sorted(glob.glob(os.path.join(ROOT, "team-kits", kit, "hooks", "*.py"))):
            yield path
    for path in sorted(glob.glob(os.path.join(ROOT, "team-kits", "kernel", "*.py"))):
        yield path


def test_no_refusal_text_names_a_kernel_invocation_a_project_cannot_run():
    """A remedy is read at the moment a role is stopped, so a command inside it has to work.

    `gate_write_scope` once offered `python -B -m kernel.cli <command>` as the fallback for the
    entry point. Measured in a scaffolded project: the kernel installs as `.claude/kernel`, so
    that import fails with `No module named 'kernel'` — and `python .claude/kernel/cli.py` is no
    entry either, since `cli.py` opens with a relative import and raises before the gate even sees
    it (and the write gate refuses that command line for naming the enforcement layer). The gate
    that had just refused a role handed them a second command that cannot run, which is the "no
    comment may promise what the code does not implement" failure in the text a blocked role acts
    on.

    The INSTALLED entry point is deliberately not judged here — `python scripts/harness.py` is the
    sanctioned surface and its two neighbours check that every text spells it that way and names
    only commands the parser has. What may not appear is a MODULE invocation presented as the
    alternative that works, because that is the one no project can run at all.

    Over every module the harness ships, for the same reason as its neighbours: the kernel refuses
    a role as often as a gate does, and it is the module that knows its own import name.
    """
    offenders = []
    for path in _shipped_python_modules():
        offenders += ["%s: %s" % (os.path.relpath(path, ROOT), text[:120])
                      for text in _refusal_texts(path) if "kernel.cli" in text]
    assert not offenders, (
        "these refusal texts name the kernel CLI as a module invocation, which no scaffolded "
        "project can run:\n" + "\n".join(offenders))


def _shipped_texts():
    """(where, text) for every file the harness SHIPS that a person or an agent reads a line off.

    The kits (constitutions, agents, SKILLs, project_memory templates, hooks, repo scripts), the
    kernel, the two global instruction files that install into the user's home, and the front page.
    Whole files, deliberately: the two checks below ask what is WRITTEN DOWN, and a comment, a
    docstring and a refusal string are all lines somebody copies. `_refusal_texts` answers the
    narrower question ("what is a role handed at the moment they are stopped") and is used by the
    check that needs that narrower subject.
    """
    for base in (os.path.join(ROOT, "team-kits"), os.path.join(ROOT, "user")):
        for current, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".ruff_cache")]
            for name in sorted(files):
                if not name.endswith((".py", ".md", ".json", ".sh", ".ps1", ".yaml", ".yml")):
                    continue
                path = os.path.join(current, name)
                with open(path, encoding="utf-8", errors="ignore") as handle:
                    yield os.path.relpath(path, ROOT).replace(os.sep, "/"), handle.read()
    with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as handle:
        yield "README.md", handle.read()


# TWO SHAPES, because a command line reaches a reader in two ways and the first shape alone missed
# four shipped sites.
#   1. a CODE SPAN that opens with the bare word. A code span is what a reader retypes, so that is
#      a command line by construction — whether it continues (`harness doctor`) or stops there.
#   2. the bare word followed by a word the SHIPPED PARSER knows as a subcommand, in ANY text,
#      backticks or not. `kernel/report.py` handed a role the remedy
#      "git restore <path> && harness generate-index" as a plain string, and both scaffolds warned
#      that "harness doctor will report hook_trust: unverified" — no backtick anywhere, so shape 1
#      saw none of them, and each was a command line a role would type. Reading the SUBCOMMAND off
#      the parser is what keeps this from refusing ordinary prose: "the harness generates …" does
#      not match, because `generates` is not on the surface, and it never needs a list of English
#      words to exclude.
# Both are rules rather than lists, because the previous round HAD a list: three spellings of a
# root wrapper, chosen by shell, is exactly the drift the single spelling replaced.
#
# WHERE SHAPE 1 CANNOT REACH, named as the mechanism it is rather than as a judgement call: the
# FIRST content line of a fenced block. Shape 1 needs a backtick immediately before the word, and
# `_reading_view`'s seam pops a fence's ``` because backticks are not command-word characters — so
# ```` ```\nharness\n``` ```` reads as ` harness ` and no shape fires, while the same content
# inline (`` see `harness` here ``) is found. Both are "what a reader retypes", which is the ground
# shape 1 stands on, so this is not an ambiguity between prose and code: it is one construct the
# rule cannot see. Measured at 0 occurrences in the shipped tree. Closing it means teaching the
# reader what a fence is — medium knowledge, which is the thing `_reading_view` was written to
# avoid needing — so it is named here and left, not tightened by reflex.
_BARE_ENTRY_SPAN_RX = re.compile(r"`harness(?=[\s`])")

# What a command TOKEN is made of. Everything else at a line break is the medium's punctuation,
# which is the whole idea behind `_reading_view` below.
_COMMAND_WORD_RX = re.compile(r"[\w/.-]")


def _reading_view(text):
    """(text as a reader takes it in, source line of every character in it).

    THE LINE IS NOT THE UNIT A COMMAND LIVES IN, and reading line by line was this check
    repeating the very defect it replaced. Measured: `("run harness "` / `"doctor first")` — a
    Python implicit concatenation, the EXACT shape whose split hid
    `"its entry " "point is not installed yet"` from a `rg` over `gate_write_scope.py` in this
    same round — passed the line reader untouched, and so did a markdown code span wrapped over
    two lines and a fenced block.

    THE SEAM IS DEFINED, NOT ENUMERATED, because a list of break forms is the failure one level
    down: a shell backslash, a PowerShell backtick, Python's abutting quotes (with or without a
    comma or a `+` between them), a markdown wrap that carries no marker at all, and a fence's
    backticks look nothing alike. The definition is exactly one predicate: a character belongs to
    the seam when it is NOT a member of `_COMMAND_WORD_RX`. So the seam is "the break, plus the
    characters on either side of it that could not be part of a command word", collapsed to one
    space — and the reader never has to know which medium it is reading. Measured across
    thirteen carriers it was never written against: a block-comment star, a `#` comment, a YAML
    fold, a batch caret, a PowerShell backtick, a blockquote marker and CRLF are all closed by
    that one predicate.

    WHAT THE PREDICATE IS NOT is "punctuation", and an earlier wording of this docstring said so
    and was wrong. Four punctuation marks — `-`, `.`, `/`, `_` — ARE command-word characters here,
    by necessity: without them `generate-index`, `harness.py`, `scripts/` and an underscored name
    stop being single tokens and the whole reader falls apart. So a break carried by one of THOSE
    is not closed, and the misses are real and measured: a markdown list dash
    (`run harness` / `- doctor first`), line numbers in a listing (`12  run harness` /
    `13  doctor first`), a bare `.`, `_` or `/` continuation marker, and a hyphenated word wrap.
    That is the price of the four characters, paid knowingly, and it is the mirror image of the
    price named below — not an oversight to be tightened later without deciding which tokens to
    give up.

    THE PRICE IN THE OTHER DIRECTION, fail-closed: a line that ENDS with the bare word followed by
    a line STARTING with a subcommand reads as a command, even in prose, and a blank line is no
    boundary (see below). Five of the eight subcommands are ordinary English words — `archive`,
    `doctor`, `evidence`, `transition`, `validate` — so this is not theoretical. Measured over the
    shipped tree: 0 offences today, but SIX lines already end in the bare word — the nearest is in
    `kernel.report.qa_verdicts`' docstring, whose sentence breaks after the bare word and resumes
    with a conjunction; it turns red the day somebody rewrites that continuation to start with a
    subcommand. Named by location rather than quoted, for the reason `scripts/harness.py` gives at
    length: a quotation of another file that nothing checks is the defect this round is about. The
    number is the honest form of this note; "costs nothing today" was not.

    A blank line is NOT a boundary here. Treating it as one would need the reader to know that a
    paragraph ends a reading unit in markdown but a blank line inside a Python string does not —
    medium knowledge again, and the direction it fails in is the open one.

    COST: over the 222-file shipped corpus the reading view takes the reader from 0.25 s to 0.54 s
    (median of the same run), i.e. ~0.3 s for the whole check. Written down because a time budget
    has twice become a defect in this suite, and because a reader who cannot see the number cannot
    judge whether the next reader may be added.
    """
    out, at, line = [], [], 1
    index, end = 0, len(text)
    while index < end:
        char = text[index]
        if char not in "\r\n":
            out.append(char)
            at.append(line)
            index += 1
            continue
        while out and not _COMMAND_WORD_RX.match(out[-1]):
            out.pop()
            at.pop()
        while index < end and not _COMMAND_WORD_RX.match(text[index]):
            if text[index] == "\n":
                line += 1
            index += 1
        out.append(" ")
        at.append(line)
    return "".join(out), at


def _bare_entry_word_rx():
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    surface = sorted(cli.build_parser()._subparsers._group_actions[0].choices)
    # A word boundary at BOTH ends: without the trailing one "the harness archived the item"
    # would read as `harness archive`, and without the leading one the required spelling
    # `scripts/harness.py doctor` would match itself.
    return re.compile(r"(?<![\w/.-])harness\s+(?:%s)\b"
                      % "|".join(re.escape(name) for name in surface))


def _bare_entry_offences(text):
    """(source line, matched text) for every bare-word command in `text`, seams included.

    Both readings run: the LINE view, because it is what names the line a reader edits, and the
    READING view, because a command does not stop at a line break. The reading view's line map
    reports the FIRST fragment — where the command starts is where somebody has to fix it.
    """
    bare_word = _bare_entry_word_rx()
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        for rx in (_BARE_ENTRY_SPAN_RX, bare_word):
            match = rx.search(line)
            if match:
                found.append((number, line.strip()[:120]))
                break
    joined, at = _reading_view(text)
    for rx in (_BARE_ENTRY_SPAN_RX, bare_word):
        for match in rx.finditer(joined):
            number = at[match.start()] if match.start() < len(at) else 0
            if not any(number == seen for seen, _ in found):
                found.append((number, joined[match.start():match.start() + 120]))
    return sorted(found)


def test_the_spelling_reader_sees_a_command_split_across_a_line_break():
    """The reader above is asked the question it was measured getting WRONG.

    A line-based reader passed all four shapes below, and the first is the exact one this round
    had already found by hand one layer down: `gate_write_scope.py` carried
    `"its entry " "point is not installed yet"` across a source line, so a `rg` for the sentence
    reported twenty files and not the twenty-three that held it. A check written to replace an
    enumeration that then cannot see a split string is that enumeration wearing a different hat,
    which is why this test exists at all rather than a note saying "mind line breaks".

    The shapes are the four MEDIA the shipped tree actually uses, not four spellings: Python's
    implicit concatenation, a markdown code span the paragraph wrapped, a shell continuation, and
    a fenced block. They agree on nothing except that a medium's break punctuation is not part of
    a command word — which is the whole of `_reading_view`'s definition.

    THE CONTROLS MATTER AS MUCH AS THE CASES. Three of them, each pinning one boundary the reader
    must NOT cross: prose that merely names the harness (the subcommand rule is what excludes it),
    the sanctioned spelling itself (the leading word-boundary), and the sanctioned spelling split
    across a break (the seam must not manufacture an offence out of the required form).
    """
    split_python = (
        '    remedy=("run harness "\n'
        '            "doctor first")\n'
    )
    wrapped_span = "Run `harness\ndoctor` to check the install.\n"
    shell_continuation = 'echo "run harness \\\n  doctor"\n'
    fenced_block = "```\nharness generate-index\n```\n"
    for label, text in (("python implicit concatenation", split_python),
                        ("wrapped markdown code span", wrapped_span),
                        ("shell line continuation", shell_continuation),
                        ("fenced block", fenced_block)):
        assert _bare_entry_offences(text), (
            "the reader does not see the bare word in a %s — a command does not stop at a line "
            "break, and neither may this check:\n%s" % (label, text))
        # ...and the line it reports is where the command STARTS, which is the line to edit.
        assert _bare_entry_offences(text)[0][0] == (1 if "```" not in text else 2), (
            "%s: reported line %d, which is not where the first fragment sits"
            % (label, _bare_entry_offences(text)[0][0]))

    for label, text in (
            ("prose naming the harness", "the harness\ngenerates the index for you\n"),
            ("the sanctioned spelling", "run `python scripts/harness.py doctor` first\n"),
            ("the sanctioned spelling, split", "run `python scripts/harness.py\ndoctor` first\n")):
        assert not _bare_entry_offences(text), (
            "the reader invents an offence in %s — the seam may close a break, never create a "
            "command:\n%s" % (label, text))


def test_every_shipped_text_spells_the_entry_point_the_one_way():
    """One entry point, one spelling, and no shipped text may print another.

    `kernel.cli.INVOCATION` is that spelling and this test takes it from there — the same constant
    argparse uses for `prog`, so a rename moves the requirement with it rather than leaving a
    hundred texts behind. What is forbidden is the bare word wherever it reads as a command — in a
    code span, or in front of a word the parser knows as a subcommand — because that is a line a
    role can retype and no installation provides it: nothing is named `harness` on any PATH, and a
    root wrapper was rejected precisely because `harness`, `./harness` and the `.cmd` spelling are
    three commands for one thing.

    This is the check that replaces `conftest.NO_INSTALLED_EVIDENCE_PRODUCER_CLAIM`. That constant
    held one measured fact together across twenty documents by DERIVING which of them owed it; the
    fact is now the opposite one, and it needs holding together in exactly the same way — otherwise
    the ~150 places that used to say `harness doctor` quietly become promises again, one file at a
    time. The subject is every shipped text rather than only the refusal strings, because a comment
    or a docstring naming a command that does not exist is the same defect one reader further out.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    offenders = []
    for where, text in _shipped_texts():
        offenders += ["%s:%d %s" % (where, number, found)
                      for number, found in _bare_entry_offences(text)]
    assert not offenders, (
        "these shipped lines spell a command as the bare word `harness` — in a code span, or in "
        "front of a subcommand the parser has — and so hand a reader a command no installation "
        "provides. The one spelling is `%s` (kernel.cli.INVOCATION); if the word is meant as a "
        "NOUN, it belongs neither in a code span nor in front of a subcommand:\n%s"
        % (cli.INVOCATION, "\n".join(offenders)))


def _entry_point_calls(text):
    """Every `<INVOCATION> <word>` spelled in a text, as the subcommand word it names.

    Reads the invocation off `kernel.cli`, so this cannot drift from what the shim installs. A
    span that continues with a `<placeholder>` or a flag names no subcommand and yields nothing —
    `python scripts/harness.py <command>` is a pointer to the surface, not a promise about one
    member of it.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    for match in re.finditer(re.escape(cli.INVOCATION) + r"\s+([a-z][a-z0-9-]*)", text):
        yield match.group(1)


# The sentence a text owes a command spec II.4 names and the shipped parser does not have. ONE
# fragment for all of them, for the same reason the retired claim was one fragment: the same
# measured gap must not drift into a dozen accounts of itself. Long enough to be a statement rather
# than a coincidence -- "not on" alone would have exempted any block that happens to contain those
# five characters for an unrelated reason, which is an exemption nobody wrote.
MISSING_SUBCOMMAND_CLAIM = "not on the entry point's command surface"


def test_every_command_a_role_is_handed_is_on_the_entry_points_surface():
    """A command line in an instruction is a promise that typing it works.

    Before the shim that promise was covered by one honest caveat — the entry point is not
    installed, so nothing here runs. Shipping the shim REMOVED that cover: `python
    scripts/harness.py evidence` now works, which is exactly what makes `python
    scripts/harness.py capture` a promise for the first time. Spec II.4 asks for twelve commands
    and `build_parser()` has eight, so this is not hypothetical.

    So every block that hands a role a `<INVOCATION> <word>` line must either name a subcommand the
    SHIPPED PARSER has, or say in the same block that it is not on the surface.

    THE SUBJECT IS THE SAME AS ITS SISTER'S, and it was NOT: this check read the instruction files,
    the AST-folded refusal texts and the README, while `test_every_shipped_text_...` read every
    shipped text. Measured in the round that shipped the entry point: an uncovered
    `python scripts/harness.py capture` planted in `hooks/session_status.py` — the text the lead
    reads FIRST at every session start — in `templates/repo/scripts/kit_checks.py` and in
    `scaffold_team.sh`'s console output all passed. An asymmetry nobody wrote down is an
    enumeration wearing a different hat, so the corpora are one corpus now: every shipped text,
    split into blocks, PLUS the folded refusal texts, which stay because folding is the only way to
    read a message the interpreter assembles from a template and a shared tail.

    BLOCK, still, and the block is read the way `_reading_view` reads it. Both halves are measured
    needs: the caveat has to be near the command a role is looking at, not four hundred lines away
    — and the caveat in `gate_push_token` is itself SPLIT across two source lines, so a raw-text
    reader would have reported it missing while the role reads it whole.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    surface = set(cli.build_parser()._subparsers._group_actions[0].choices)
    assert len(surface) >= 8, surface

    blocks = []
    for where, text in _shipped_texts():
        blocks += [(where, _reading_view(block)[0]) for block in _markdown_blocks(text)]
    for path in _shipped_python_modules():
        where = os.path.relpath(path, ROOT).replace(os.sep, "/")
        blocks += [(where, text) for text in _refusal_texts(path)]

    seen, offenders = 0, []
    for where, block in blocks:
        for word in _entry_point_calls(block):
            seen += 1
            if word in surface or MISSING_SUBCOMMAND_CLAIM in block:
                continue
            offenders.append("%s: `%s %s`" % (where, cli.INVOCATION, word))
    assert not offenders, (
        "these blocks hand a role a command the shipped parser does not have (%s). Either the "
        "command ships, or the block says, in so many words, that it is \"%s\" — the caveat "
        "fragment is deliberately the words a role reads and not a `conftest` constant:\n%s"
        % (", ".join(sorted(surface)), MISSING_SUBCOMMAND_CLAIM, "\n".join(offenders)))
    # A floor, because every assertion above is vacuously true over a set that stopped matching.
    # 177 call sites across 267 shipped files were measured the day the two corpora were merged.
    # The floor sits well under that, so a rewritten document cannot trip it, and well over the 49
    # the narrower corpus saw, so losing the merge cannot pass unnoticed.
    assert seen >= 100, "only %d entry-point calls found — the reader stopped matching" % seen


# ---------------- notify_agent_events: SubagentStop route ----------------
def test_notify_logs_subagent_stop(tmp_path):
    (tmp_path / "project_memory").mkdir()
    payload = {"hook_event_name": "SubagentStop", "agent_type": "frontend-developer",
               "cwd": str(tmp_path)}
    assert run_hook("notify_agent_events.py", payload, tmp_path) == 0
    text = (tmp_path / "project_memory" / ".audit" / "hook_events.jsonl").read_text(encoding="utf-8")
    assert "subagent_stop" in text and "frontend-developer" in text


# ---------------- guard_scratchpad_ref ----------------
def test_scratchpad_ref_blocked_in_source(tmp_path):
    p = tmp_path / "src" / "styles.css"
    write(str(p), "/* Regenerate via scratchpad/vendor_fonts.py */\nbody{}\n")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(p)}, "cwd": str(tmp_path)}
    assert run_hook("guard_scratchpad_ref.py", payload, tmp_path) == 2


def test_scratchpad_ref_allowed_outside_source_areas(tmp_path):
    p = tmp_path / "project_memory" / "notes.yaml"
    write(str(p), "note: the scratchpad/ dir is ephemeral\n")
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(p)}, "cwd": str(tmp_path)}
    assert run_hook("guard_scratchpad_ref.py", payload, tmp_path) == 0


# ---------------- office kit: gate_proc_approved ----------------
def _office_state(repo):
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    root = os.path.join(str(repo), "project_memory")
    os.makedirs(root, exist_ok=True)
    return ProjectState(root)


def capture_proc(repo, steps=("file it",), roles=("bookkeeper",), approve=True):
    """Give an office project a PROC — captured through the kernel, approved through the MINT.

    Nothing here is hand-written, and the approval half is why: `approved_hash` is stamped by
    `approvals.mint` (see `approved_content_hash`), so a fixture that wrote the field itself would
    prove the gate reads a stamp without proving anything can produce one — the exact shape of the
    V1 defect this replaces, where the only writer of that field was a script that opened a deleted
    monolith and died.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from conftest import walk_to_status
    state = _office_state(repo)
    item = state.capture("PROC", {"title": "inbox sweep", "steps": list(steps),
                                  "roles": list(roles)})
    if approve:
        item = walk_to_status(state, item, "APPROVED")
    return item


def _spawn(repo, prompt):
    return {"hook_event_name": "PreToolUse", "tool_name": "Agent",
            "tool_input": {"subagent_type": "bookkeeper", "run_in_background": False,
                           "prompt": prompt}, "cwd": str(repo)}


def _proc_gate(repo, prompt):
    return run_hook_process("gate_proc_approved.py", _spawn(repo, prompt), repo,
                            hooks_dir=OFFICE_HOOKS)


def test_the_proc_gate_refuses_every_spawn_while_no_procedure_is_approved(tmp_path):
    """Spec II.4 in the one sentence this file exists for: "leerer Zustand blockiert".

    The V1 gate had two doors out and both said "no PROC yet, so let the onboarding work happen":
    the registry file being absent, and nothing in it being approved. In a V2 project the first is
    permanently true — the registry was dissolved into `procedures/active/` — so the measured
    behaviour was rc 0 on every spawn, forever, while the office constitution promised the opposite.
    Fail-closed is affordable here because the way out needs no spawn: the lead captures the
    procedure and asks the user, and the refusal says so.
    """
    repo = tmp_path / "repo"
    _office_state(repo)                       # state exists, holds no procedure
    result = _proc_gate(repo, "onboarding interview")
    assert result.returncode == 2
    assert "no approved procedure" in result.stderr
    assert "request-approval scope" in result.stderr, "a fail-closed refusal carries its remedy"


def test_the_proc_gate_still_allows_the_installers_own_bootstrap_window(tmp_path):
    """The one exception spec II.4 grants — and it is not a flag the lead can set for itself.

    `_kernel.bootstrap_active` demands an EMPTY target state, a marker recording an installer run
    plus an explicit user confirmation, and a TTL; `guard_harness_selfmod` keeps `kit_state.json`
    off every Edit/Write path. Asserted here so the "empty state blocks" rule above cannot be read
    as "an installer cannot install".
    """
    repo = tmp_path / "repo"
    (repo / "project_memory").mkdir(parents=True)
    write(str(repo / ".claude" / "kit_state.json"), json.dumps({"bootstrap": {
        "user_confirmed": True, "installer_run": "scaffold_team",
        "expires_at_epoch": time.time() + 600}}))
    assert _proc_gate(repo, "onboarding interview").returncode == 0


def test_the_proc_gate_refuses_a_work_order_that_names_no_procedure(tmp_path):
    repo = tmp_path / "repo"
    capture_proc(repo)
    result = _proc_gate(repo, "please file the inbox")
    assert result.returncode == 2
    assert "names no PROC" in result.stderr


def test_the_proc_gate_allows_a_work_order_naming_an_approved_procedure(tmp_path):
    repo = tmp_path / "repo"
    proc = capture_proc(repo)
    assert _proc_gate(repo, "execute %s sweep" % proc["id"]).returncode == 0


def test_the_proc_gate_refuses_a_procedure_the_user_never_approved(tmp_path):
    """A DRAFT procedure is not a permission — and one approved PROC does not authorise another."""
    repo = tmp_path / "repo"
    capture_proc(repo)
    draft = capture_proc(repo, steps=("do something else",), approve=False)
    result = _proc_gate(repo, "execute %s" % draft["id"])
    assert result.returncode == 2
    assert "not an approved" in result.stderr


def test_the_proc_gate_refuses_a_procedure_edited_after_its_approval(tmp_path):
    """The stamp is what makes an out-of-band edit visible.

    The edit here goes PAST the kernel (straight to the item file), which is the only way an
    approved PROC's steps can move without the revision bump and approval invalidation
    `state.update_item` performs — and it is exactly the case `approved_hash` exists for.
    """
    yaml = pytest.importorskip("yaml")
    repo = tmp_path / "repo"
    proc = capture_proc(repo)
    path = _office_state(repo).active_path(proc["id"])
    item = yaml.safe_load(open(path, encoding="utf-8").read())
    item["steps"].append("NEW sneaky step")
    write(path, yaml.safe_dump(item, sort_keys=False, allow_unicode=True))
    result = _proc_gate(repo, "execute %s" % proc["id"])
    assert result.returncode == 2
    assert "edited past the kernel" in result.stderr


def test_the_proc_gate_reads_the_stamp_the_mint_wrote_and_no_other_producer(tmp_path):
    """The rule and its route to compliance, measured as one fact.

    `report.validate_state` reports an approved PROC without an `approved_hash` as an ERROR, and
    until the mint stamped it the only writer of that field was `scripts/proc_hash.py --update` —
    a script that opened a deleted monolith, crashed, and whose whole purpose was to make a tamper
    check pass on demand. So the rule had no walkable route at all. This asserts the route: capture
    plus the user's approval leaves a stamp that matches the content, and the validator is clean.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import approvals, report
    repo = tmp_path / "repo"
    proc = capture_proc(repo)
    state = _office_state(repo)
    stored = state.read_item(proc["id"])
    assert stored["status"] == "APPROVED"
    assert stored[approvals.APPROVED_CONTENT_HASH_FIELD] == approvals.approved_content_hash(
        "PROC", stored)
    assert [f for f in report.validate_state(state)
            if f["severity"] == "error" and f["item"] == proc["id"]] == []


# ---------------- office kit: ledger scripts ----------------
def test_the_append_only_guard_is_gone(tmp_path):
    """User decision I.3/1: append-only is abolished, so `guard_ledger_direct` was DELETED rather
    than loosened. II.12 asks for exactly this proof ("Append-only-Guard nachweislich entfernt") —
    a direct ledger edit is now judged by `gate_ledger_valid`, not forbidden."""
    assert not os.path.exists(os.path.join(OFFICE_HOOKS, "guard_ledger_direct.py"))
    settings = json.load(open(os.path.join(ROOT, "team-kits", "office-team", "settings",
                                           "settings.json"), encoding="utf-8"))
    assert "guard_ledger_direct" not in json.dumps(settings)


def _ledger_add(repo, *extra):
    os.makedirs(os.path.join(repo, "scripts"), exist_ok=True)
    shutil.copy(os.path.join(OFFICE_SCRIPTS, "ledger_add.py"),
                os.path.join(repo, "scripts", "ledger_add.py"))
    base = [sys.executable, os.path.join(repo, "scripts", "ledger_add.py"),
            "--year", "2026", "--direction", "expense", "--doc-type", "invoice",
            "--doc-date", "2026-07-01", "--payment-date", "2026-07-03",
            "--counterparty", "Muster GmbH", "--invoice-no", "RE-1",
            "--vat-treatment", "standard", "--category", "goods",
            "--source", "archive/finance/x.pdf"]
    return subprocess.run(base + list(extra), capture_output=True, text=True, cwd=repo, timeout=60)


def test_ledger_add_appends_valid_row(tmp_path):
    r = _ledger_add(str(tmp_path), "--net", "100.00", "--vat-rate", "19", "--gross", "119.00")
    assert r.returncode == 0, r.stderr
    text = (tmp_path / "ledger" / "2026.csv").read_text(encoding="utf-8")
    assert "L2026-0001" in text and "Muster GmbH" in text


def test_ledger_add_refuses_bad_arithmetic(tmp_path):
    r = _ledger_add(str(tmp_path), "--net", "100.00", "--vat-rate", "19", "--gross", "125.00")
    assert r.returncode == 1 and "re-read the document" in r.stderr


def test_ledger_add_refuses_duplicate(tmp_path):
    assert _ledger_add(str(tmp_path), "--net", "100.00", "--vat-rate", "19", "--gross", "119.00").returncode == 0
    r = _ledger_add(str(tmp_path), "--net", "100.00", "--vat-rate", "19", "--gross", "119.00")
    assert r.returncode == 1 and "duplicate" in r.stderr


def test_euer_report_totals(tmp_path):
    assert _ledger_add(str(tmp_path), "--net", "100.00", "--vat-rate", "19", "--gross", "119.00").returncode == 0
    shutil.copy(os.path.join(OFFICE_SCRIPTS, "euer_report.py"),
                os.path.join(str(tmp_path), "scripts", "euer_report.py"))
    r = subprocess.run([sys.executable, os.path.join(str(tmp_path), "scripts", "euer_report.py"),
                        "--year", "2026", "--quarter", "3"],
                       capture_output=True, text=True, cwd=str(tmp_path), timeout=60)
    assert r.returncode == 0, r.stderr
    report = (tmp_path / "reports" / "euer_2026_Q3.md").read_text(encoding="utf-8")
    assert "| Ausgaben | 119.00 EUR |" in report and "Steuerberatung" in report


# ---------------- office kit: filing gate + fs tripwire ----------------
FILING_PLAN = (
    "rules:\n"
    "  - id: FP-001\n"
    '    path_template: "archive/finance/incoming_invoices/<year>/"\n'
    "    document_types: [invoice]\n"
)


def _filing_move(repo, command):
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash",
            "tool_input": {"command": command}, "cwd": str(repo)}


def _run_filing(payload, repo, extra_env=None):
    return run_hook_process("gate_filing.py", payload, repo, hooks_dir=OFFICE_HOOKS,
                            extra_env=extra_env)


def test_gate_filing_blocks_while_the_plan_has_no_rules(tmp_path):
    """Fail-closed on an empty plan: with no rule there is nothing to file AGAINST, and a business
    archive is where an unverifiable filing is dearest to undo. Note that the shipped template IS
    the empty plan and `project_memory/**` is kernel-only for tool writes, so this currently
    blocks the first filing of every office project — see the gate's LOCKSTEP DEPENDENCY note."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), "rules: []\n")
    payload = _filing_move(tmp_path, "mv inbox/a.pdf archive/finance/incoming_invoices/2026/a.pdf")
    result = _run_filing(payload, tmp_path)
    assert result.returncode == 2 and "filing_plan.yaml" in result.stderr


def test_gate_filing_blocks_a_target_no_rule_covers(tmp_path):
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    payload = _filing_move(tmp_path, "mv inbox/a.pdf archive/invented/a.pdf")
    result = _run_filing(payload, tmp_path)
    assert result.returncode == 2 and "archive/invented" in result.stderr


def test_gate_filing_allows_a_target_a_rule_covers(tmp_path):
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    payload = _filing_move(tmp_path,
                           "mv inbox/a.pdf archive/finance/incoming_invoices/2026/2026-01-01_x.pdf")
    assert _run_filing(payload, tmp_path).returncode == 0


def test_gate_filing_placeholder_matches_one_segment_only(tmp_path):
    """`<year>` stands for ONE path segment. Letting it swallow `2026/subfolder` would turn every
    rule into a prefix rule, and the Aktenplan would stop describing the archive."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    payload = _filing_move(tmp_path, "mv inbox/a.pdf archive/finance/incoming_invoices/2026/q1/a.pdf")
    assert _run_filing(payload, tmp_path).returncode == 2


def test_gate_filing_sees_a_quoted_destination_with_spaces(tmp_path):
    """A business archive is full of `Müller GmbH.pdf`. Splitting the command on whitespace ended
    in the token `GmbH.pdf"`, which is not under archive/ — the gate passed the exact filenames it
    exists for."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    payload = _filing_move(tmp_path, 'mv inbox/a.pdf "archive/invented/Müller GmbH.pdf"')
    assert _run_filing(payload, tmp_path).returncode == 2


def test_gate_filing_ignores_a_move_that_is_not_a_filing(tmp_path):
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    payload = _filing_move(tmp_path, "mv draft.md outbox/draft.md")
    assert _run_filing(payload, tmp_path).returncode == 0


def test_gate_filing_reads_a_named_powershell_destination_before_the_source(tmp_path):
    """`Move-Item -Destination <dst> -Path <src>` is ordinary PowerShell, the gate IS registered on
    PowerShell, and under the old "destination = last positional token" rule it passed clean
    (measured rc=0 while the same move in POSIX order blocked). A named parameter names its own
    token, so it has to win over position."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    for command in (r"Move-Item -Destination archive\invented\a.pdf -Path inbox\a.pdf",
                    r"Copy-Item -Des:archive\invented\a.pdf -Path inbox\a.pdf"):
        result = _run_filing(_filing_move(tmp_path, command), tmp_path)
        assert result.returncode == 2, command
        assert "archive/invented" in result.stderr, command


def test_gate_filing_reads_the_destination_of_a_directory_copier(tmp_path):
    """`robocopy`/`xcopy` put the destination SECOND and it is a directory — reading it as "the
    last token" landed on the filename filter and let a whole folder into the archive."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    result = _run_filing(_filing_move(tmp_path, "robocopy inbox archive\\invented a.pdf"), tmp_path)
    assert result.returncode == 2 and "archive/invented" in result.stderr


def test_gate_filing_sees_a_move_inside_a_shell_wrapper(tmp_path):
    """`bash -lc "mv … archive/…"` is the same `mv`, one level down.

    `_compat` exists for exactly this ("audit: `-lc` bypassed every gate") and every git gate
    unwraps through it; this one tokenised the outer line instead, so both wrapper spellings
    measured rc=0 while the bare command blocked."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    for command in ('bash -lc "mv inbox/a.pdf archive/invented/a.pdf"',
                    'powershell -Command "Move-Item inbox/a.pdf archive/invented/a.pdf"'):
        result = _run_filing(_filing_move(tmp_path, command), tmp_path)
        assert result.returncode == 2, command
        assert "archive/invented" in result.stderr, command


def test_gate_filing_reads_a_gnu_target_directory_flag(tmp_path):
    """`mv -t DIR src` moves the destination OFF its position — the flag names it, exactly as
    `-Destination` does for PowerShell. Under the last-token rule the destination was the SOURCE
    and the gate passed (measured rc=0 for all four spellings). The `-t` reading is scoped to the
    coreutils family on purpose: `rsync -t` preserves timestamps."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    for command in ("mv -t archive/invented inbox/a.pdf",
                    "mv --target-directory=archive/invented inbox/a.pdf",
                    "cp -fvt archive/invented inbox/a.pdf",
                    "install -tarchive/invented inbox/a.pdf"):
        result = _run_filing(_filing_move(tmp_path, command), tmp_path)
        assert result.returncode == 2, command
        assert "archive/invented" in result.stderr, command


def test_gate_filing_reads_the_target_directory_flag_as_a_directory(tmp_path):
    """...and it names a DIRECTORY, so the rule check must run against that directory itself.
    Read as a file path, `-t archive/finance/incoming_invoices/2026` would be checked against its
    PARENT — a directory nobody is filing into, and one a coarser rule may well cover."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    ok = "mv -t archive/finance/incoming_invoices/2026 inbox/a.pdf"
    assert _run_filing(_filing_move(tmp_path, ok), tmp_path).returncode == 0
    bad = "mv -t archive/finance/incoming_invoices inbox/a.pdf"
    assert _run_filing(_filing_move(tmp_path, bad), tmp_path).returncode == 2


def test_gate_filing_reads_the_trailing_destination_of_rsync(tmp_path):
    """`rsync -a inbox/ archive/2026/` obeys the same N-sources-then-destination convention as
    `mv`, and fills an archive just as well — it was simply not in the family."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    result = _run_filing(_filing_move(tmp_path, "rsync -a inbox/ archive/invented/"), tmp_path)
    assert result.returncode == 2 and "archive/invented" in result.stderr


def test_gate_filing_sees_a_redirect_into_the_archive(tmp_path):
    """A redirection target is a file the SHELL creates — no move verb involved. `cat inbox/a.pdf >
    archive/invented/a.pdf` files a document exactly as well as `mv` does, and a verb list can
    never see it. Same rule guard_fs_tripwire uses for the ledger."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    for command in ("cat inbox/a.pdf > archive/invented/a.pdf",
                    "cat inbox/a.pdf | tee archive/invented/a.pdf"):
        result = _run_filing(_filing_move(tmp_path, command), tmp_path)
        assert result.returncode == 2, command


def test_gate_filing_still_sees_the_destination_past_a_redirect(tmp_path):
    """...and adding the redirect rule must not cost the positional one: with `mv a b > log` the
    last token of the line is the log file, so the argument list has to end at the redirect."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    payload = _filing_move(tmp_path, "mv inbox/a.pdf archive/invented/a.pdf > /tmp/mv.log")
    result = _run_filing(payload, tmp_path)
    assert result.returncode == 2 and "archive/invented" in result.stderr


def test_gate_filing_resolves_a_relative_target_against_the_agents_cwd(tmp_path):
    """An agent working in `inbox/` writes `../archive/…`, which resolved against the repo ROOT
    looks like an escape from the repo and was dropped — the document really landed in the
    archive while the gate stayed silent. The same failure class `_compat` already fixed for Codex
    patch paths: resolve against cwd AND root, block on either reading."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    os.makedirs(str(tmp_path / "inbox"), exist_ok=True)
    payload = dict(_filing_move(tmp_path, "mv a.pdf ../archive/invented/a.pdf"),
                   cwd=str(tmp_path / "inbox"))
    result = _run_filing(payload, tmp_path)
    assert result.returncode == 2 and "archive/invented" in result.stderr


def test_gate_filing_covers_a_direct_write_into_the_archive(tmp_path):
    """The other door. A gate that only watched shell moves would document its own bypass: `Write`
    to a path under archive/ files a document just as effectively."""
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Write",
               "tool_input": {"file_path": str(tmp_path / "archive" / "invented" / "a.pdf")},
               "cwd": str(tmp_path)}
    assert _run_filing(payload, tmp_path).returncode == 2


def test_gate_filing_blocks_codex_patch_that_files_into_the_archive(tmp_path):
    write(str(tmp_path / "project_memory" / "filing_plan.yaml"), FILING_PLAN)
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "apply_patch",
        "tool_input": {"command": _codex_patch("docs/notes.md", "archive/invented/a.md")},
        "cwd": str(tmp_path),
    }
    result = _run_filing(payload, tmp_path, extra_env={"TEAM_KIT_PROVIDER": "codex"})
    assert result.returncode == 2 and "archive/invented" in result.stderr


def test_fs_tripwire_blocks_archive_delete(tmp_path):
    payload = {"tool_name": "Bash", "tool_input": {"command": "rm -rf archive/finance/2026"},
               "cwd": str(tmp_path)}
    assert run_hook("guard_fs_tripwire.py", payload, tmp_path, hooks_dir=OFFICE_HOOKS) == 2


def test_fs_tripwire_allows_filing_move(tmp_path):
    payload = {"tool_name": "Bash",
               "tool_input": {"command": 'mv "inbox/scan.pdf" "archive/fin/2026-07-01_x_invoice.pdf"'},
               "cwd": str(tmp_path)}
    assert run_hook("guard_fs_tripwire.py", payload, tmp_path, hooks_dir=OFFICE_HOOKS) == 0


def test_fs_tripwire_blocks_move_out_of_archive(tmp_path):
    payload = {"tool_name": "Bash",
               "tool_input": {"command": "mv archive/fin/a.pdf /tmp/gone.pdf"}, "cwd": str(tmp_path)}
    assert run_hook("guard_fs_tripwire.py", payload, tmp_path, hooks_dir=OFFICE_HOOKS) == 2


# ---------------- audit regressions: reversal maths, re-book flow, year guard, CII id, budget edge ----------------
def _reversal_ledger(tmp_path):
    assert _ledger_add(str(tmp_path), "--net", "100.00", "--vat-rate", "19", "--gross", "119.00").returncode == 0
    r = _ledger_add(str(tmp_path), "--net", "100.00", "--vat-rate", "19", "--gross", "119.00",
                    "--doc-type", "reversal", "--reverses", "L2026-0001")
    assert r.returncode == 0, r.stderr


def test_euer_report_reversal_nets_to_zero(tmp_path):
    # BLOCKER regression: booked +119 and reversed 119 in the same quarter must total 0.00, not -119
    _reversal_ledger(tmp_path)
    shutil.copy(os.path.join(OFFICE_SCRIPTS, "euer_report.py"),
                os.path.join(str(tmp_path), "scripts", "euer_report.py"))
    r = subprocess.run([sys.executable, os.path.join(str(tmp_path), "scripts", "euer_report.py"),
                        "--year", "2026", "--quarter", "3"],
                       capture_output=True, text=True, cwd=str(tmp_path), timeout=60)
    assert r.returncode == 0, r.stderr
    report = (tmp_path / "reports" / "euer_2026_Q3.md").read_text(encoding="utf-8")
    assert "| Ausgaben | 0.00 EUR |" in report


def test_ledger_rebook_after_reversal_allowed(tmp_path):
    # MAJOR regression: the sanctioned correction flow (book -> reversal -> re-book) must not dead-end
    _reversal_ledger(tmp_path)
    r = _ledger_add(str(tmp_path), "--net", "100.00", "--vat-rate", "19", "--gross", "119.00")
    assert r.returncode == 0, r.stderr


def test_ledger_refuses_year_mismatch(tmp_path):
    r = _ledger_add(str(tmp_path), "--net", "100.00", "--vat-rate", "19", "--gross", "119.00",
                    "--payment-date", "2025-12-31")
    assert r.returncode == 1 and "ledger/2025.csv" in r.stderr


def test_einvoice_cii_invoice_no_not_guideline_urn(tmp_path):
    pytest.importorskip("defusedxml")
    cii = (
        '<?xml version="1.0"?>'
        '<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"'
        ' xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">'
        '<rsm:ExchangedDocumentContext><ram:GuidelineSpecifiedDocumentContextParameter>'
        '<ram:ID>urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0</ram:ID>'
        '</ram:GuidelineSpecifiedDocumentContextParameter></rsm:ExchangedDocumentContext>'
        '<rsm:ExchangedDocument><ram:ID>RE-2026-0815</ram:ID>'
        '<ram:IssueDateTime><udt:DateTimeString xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100"'
        ' format="102">20260701</udt:DateTimeString></ram:IssueDateTime></rsm:ExchangedDocument>'
        '</rsm:CrossIndustryInvoice>')
    xml_path = tmp_path / "invoice.xml"
    xml_path.write_text(cii, encoding="utf-8")
    r = subprocess.run([sys.executable, os.path.join(OFFICE_SCRIPTS, "einvoice_extract.py"),
                        str(xml_path)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    assert "invoice_no: RE-2026-0815" in r.stdout and "urn:cen.eu" not in r.stdout.split("invoice_no:")[1].splitlines()[0]
    assert "issue_date: 2026-07-01" in r.stdout


def test_file_budget_exactly_at_limit_passes(tmp_path):
    # MINOR regression: an exactly-800-line file (with trailing newline) is AT the budget, not over
    pytest.importorskip("yaml")
    write(str(tmp_path / "src" / "static" / "app.js"), "let x = 1;\n" * 800)
    assert run_quality(str(tmp_path)) == 0


def test_fs_tripwire_allows_archiving_generated_report(tmp_path):
    # MINOR regression: destination-is-archive must not block (only an archive/ SOURCE blocks)
    payload = {"tool_name": "Bash",
               "tool_input": {"command": "mv reports/euer_2026_Q3.md archive/finance/reports/"},
               "cwd": str(tmp_path)}
    assert run_hook("guard_fs_tripwire.py", payload, tmp_path, hooks_dir=OFFICE_HOOKS) == 0


# ---------------- scaffold: mechanical presets + map re-stamp ----------------
def _preset_parser_kit(tmp_path, presets):
    kit = tmp_path / "preset-kit"
    for role in ("project-manager", "alpha", "beta"):
        write(str(kit / "agents" / (role + ".md")), "# %s\n" % role)
    write(str(kit / "settings" / "settings.json"), '{"agent": "project-manager"}\n')
    write(str(kit / "presets.yaml"), presets)
    return kit


def test_preset_parser_resolves_only_valid_specialists(tmp_path):
    kit = _preset_parser_kit(tmp_path, "mini: alpha beta\nfull: all\n")
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "team-kits", "preset_config.py"),
         "--kit", str(kit), "--preset", "mini", "--format", "json"],
        capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    parsed = json.loads(result.stdout)
    assert parsed == {
        "preset": "mini", "lead": "project-manager", "all": False,
        "roles": ["alpha", "beta"], "available": ["mini", "full"],
    }


@pytest.mark.parametrize("presets, diagnostic", [
    ("mini: alpha\nmini: beta\n", "duplicate yaml key"),
    ("mini: missing\n", "unknown role"),
    ("mini: project-manager alpha\n", "foreground lead"),
    ("mini: alpha alpha\n", "duplicate specialist"),
    ("mini: [alpha]\n", "space-separated role string"),
    ("- alpha\n", "non-empty mapping"),
])
def test_preset_parser_rejects_ambiguous_or_nonmechanical_policy(
        tmp_path, presets, diagnostic):
    kit = _preset_parser_kit(tmp_path, presets)
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "team-kits", "preset_config.py"),
         "--kit", str(kit)], capture_output=True, text=True, timeout=60)
    output = (result.stdout + result.stderr).lower()
    assert result.returncode != 0 and diagnostic in output


def _unknown_recorded_preset_state(tmp_path):
    home = tmp_path / "home"
    kit = home / ".claude" / "team-kits" / "demo-team"
    for role in ("project-manager", "alpha"):
        write(str(kit / "agents" / (role + ".md")),
              "---\nname: %s\nmodel: sonnet\neffort: high\n---\nbody\n" % role)
        write(str(kit / "skills" / role / "SKILL.md"),
              "---\nname: %s\n---\nbody\n" % role)
    write(str(kit / "settings" / "settings.json"), '{"agent": "project-manager"}\n')
    write(str(kit / "presets.yaml"), "mini: alpha\n")
    write(str(kit / "constitution" / "AGENTS.md"),
          "<!-- agents-and-skills:team-kit demo-team -->\n# Replacement constitution\n")

    repo = tmp_path / "repo"
    write(str(repo / "project_memory" / "project_config.yaml"),
          'project:\n  name: demo\n  preset: "retired"\nproviders: [claude]\n')
    write(str(repo / "AGENTS.md"), "# external sentinel constitution\n")
    write(str(repo / ".claude" / "agents" / "custom.md"), "user-owned role\n")
    return home, repo


def _duplicate_recorded_preset_state(tmp_path):
    home, repo = _unknown_recorded_preset_state(tmp_path)
    config = repo / "project_memory" / "project_config.yaml"
    config.write_text(
        "project:\n  name: demo\n  preset: mini\nproviders: [claude]\n",
        encoding="utf-8")
    presets = home / ".claude" / "team-kits" / "demo-team" / "presets.yaml"
    presets.write_text("mini: alpha\nmini: all\n", encoding="utf-8")
    return home, repo


def _scaffold_external_file_symlink_state(tmp_path, relative):
    home = tmp_path / "home"
    kit = home / ".claude" / "team-kits" / "demo-team"
    for role in ("project-manager", "alpha"):
        write(str(kit / "agents" / (role + ".md")),
              "---\nname: %s\nmodel: sonnet\neffort: high\n---\nbody\n" % role)
        write(str(kit / "skills" / role / "SKILL.md"),
              "---\nname: %s\n---\nbody\n" % role)
    write(str(kit / "settings" / "settings.json"), '{"agent": "project-manager"}\n')
    write(str(kit / "presets.yaml"), "mini: alpha\n")
    write(str(kit / "constitution" / "AGENTS.md"),
          "<!-- agents-and-skills:team-kit demo-team -->\n# Replacement constitution\n")
    write(str(kit / "templates" / "repo" / "scripts" / "kit_checks.py"),
          "# kit-owned replacement\n")

    repo = tmp_path / "repo"
    write(str(repo / "project_memory" / "project_config.yaml"),
          "project:\n  name: symlink\n  preset: mini\nproviders: [claude]\n")
    write(str(repo / "AGENTS.md"), "# local constitution sentinel\n")
    external = tmp_path / "external-scaffold" / relative.replace("/", "-")
    write(str(external), "external scaffold sentinel\n")
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    return home, repo, external, target


def _assert_scaffold_symlink_preflight_untouched(repo, external, target):
    assert external.read_text(encoding="utf-8") == "external scaffold sentinel\n"
    assert target.is_symlink()
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == (
        "# local constitution sentinel\n")
    assert not (repo / ".claude" / "settings.json").exists()
    assert not (repo / ".claude" / "team_kit_roles.txt").exists()
    assert not (repo / ".claude" / "backups").exists()


@pytest.mark.parametrize("relative", [
    "scripts/kit_checks.py",
    ".claude/kit_update_pending.repo",
])
def test_scaffold_ps1_rejects_external_control_file_symlink_before_mutation(tmp_path, relative):
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("PowerShell scaffold integration runs on Windows")
    home, repo, external, target = _scaffold_external_file_symlink_state(tmp_path, relative)
    try:
        os.symlink(external, target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip("file symlinks are not permitted in this test environment: %s" % exc)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(ROOT, "team-kits", "scaffold_team.ps1"), "-Team", "demo-team"],
        cwd=str(repo), capture_output=True, text=True, timeout=120,
        env=dict(os.environ, USERPROFILE=str(home)))
    output = (result.stdout + result.stderr).lower()
    assert result.returncode != 0 and ("symlink" in output or "reparse" in output)
    _assert_scaffold_symlink_preflight_untouched(repo, external, target)


@pytest.mark.parametrize("relative", [
    "scripts/kit_checks.py",
    ".claude/kit_update_pending.repo",
])
def test_scaffold_sh_rejects_external_control_file_symlink_before_mutation(tmp_path, relative):
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX scaffold integration runs on Unix CI")
    home, repo, external, target = _scaffold_external_file_symlink_state(tmp_path, relative)
    os.symlink(external, target)
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    result = subprocess.run(
        ["bash", os.path.join(ROOT, "team-kits", "scaffold_team.sh"), "demo-team"],
        cwd=str(repo), capture_output=True, text=True, timeout=120,
        env=dict(os.environ, HOME=str(home), PYTHONPATH=pythonpath))
    output = (result.stdout + result.stderr).lower()
    assert result.returncode != 0 and "symlink" in output
    _assert_scaffold_symlink_preflight_untouched(repo, external, target)


def _assert_unknown_preset_left_repo_untouched(repo):
    assert (repo / "AGENTS.md").read_text(encoding="utf-8") == (
        "# external sentinel constitution\n")
    assert (repo / ".claude" / "agents" / "custom.md").read_text(
        encoding="utf-8") == "user-owned role\n"
    assert not (repo / ".claude" / "agents" / "alpha.md").exists()
    assert not (repo / ".claude" / "settings.json").exists()
    assert not (repo / ".claude" / "team_kit_roles.txt").exists()
    assert not (repo / ".claude" / "backups").exists()


def _scaffold_provider_collision_state(tmp_path):
    home = tmp_path / "home"
    kit = home / ".claude" / "team-kits" / "demo-team"
    for role in ("project-manager", "alpha"):
        model = "opus" if role == "project-manager" else "sonnet"
        write(str(kit / "agents" / (role + ".md")),
              "---\nname: %s\ndescription: new %s\nmodel: %s\neffort: high\n---\nnew body\n"
              % (role, role, model))
        write(str(kit / "skills" / role / "SKILL.md"),
              "---\nname: %s\n---\nnew skill\n" % role)
    write(str(kit / "settings" / "settings.json"), '{"agent": "project-manager"}\n')
    write(str(kit / "hooks" / "new_hook.py"), "#!/usr/bin/env python3\n# new hook\n")
    write(str(kit / "presets.yaml"), "mini: alpha\n")
    write(str(kit / "VERSION"), "version: rollback-test\ncontent: new\n")
    write(str(kit / "constitution" / "AGENTS.md"),
          "<!-- agents-and-skills:team-kit demo-team -->\n# New constitution\n")

    repo = tmp_path / "repo"
    write(str(repo / "project_memory" / "project_config.yaml"),
          "project:\n  name: rollback\n  preset: mini\nproviders: [claude, codex]\n")
    write(str(repo / "AGENTS.md"),
          "<!-- agents-and-skills:team-kit old-team -->\n# Old constitution\n")
    write(str(repo / "CLAUDE.md"), "# Old Claude entry\n")
    for role in ("project-manager", "alpha"):
        write(str(repo / ".claude" / "agents" / (role + ".md")), "old %s agent\n" % role)
        write(str(repo / ".claude" / "skills" / role / "SKILL.md"),
              "old %s skill\n" % role)
    write(str(repo / ".claude" / "agents" / "custom.md"), "user-owned custom agent\n")
    write(str(repo / ".claude" / "hooks" / "old_hook.py"), "# old hook\n")
    write(str(repo / ".claude" / "settings.json"),
          '{"agent": "project-manager", "old": true}\n')
    write(str(repo / ".claude" / "team_kit_roles.txt"),
          "# agents-and-skills:team-kit-roles v1 team=old-team count=2\n"
          "project-manager\nalpha\n")
    write(str(repo / ".claude" / "provider_artifacts.json"),
          '{"version": 1, "files": [], "dirs": []}\n')
    write(str(repo / ".claude" / "kit_version"),
          "version: old\ncontent: old\n")
    write(str(repo / ".agents" / "skills" / "old-native" / "SKILL.md"),
          "old native skill\n")
    collision = repo / ".codex" / "config.toml"
    write(str(collision), "# unowned collision sentinel\n")
    return home, repo, collision


def _controlled_scaffold_snapshot(repo):
    roots = (
        "AGENTS.md", "CLAUDE.md", ".claude/agents", ".claude/hooks",
        ".claude/skills", ".claude/settings.json", ".claude/team_kit_roles.txt",
        ".claude/provider_artifacts.json", ".claude/kit_version", ".codex",
        ".agents/skills", ".github/hooks", ".github/agents",
    )
    snapshot = {}
    for relative in roots:
        path = repo / relative
        if path.is_file():
            data = path.read_bytes()
            snapshot[relative] = (hashlib.sha256(data).hexdigest(), data)
        elif path.is_dir():
            snapshot[relative + "/"] = ("directory", b"")
            for child in sorted(item for item in path.rglob("*") if item.is_file()):
                child_relative = child.relative_to(repo).as_posix()
                data = child.read_bytes()
                snapshot[child_relative] = (hashlib.sha256(data).hexdigest(), data)
    return snapshot


def test_scaffold_ps1_rolls_back_base_after_provider_collision(tmp_path):
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("PowerShell scaffold integration runs on Windows")
    home, repo, collision = _scaffold_provider_collision_state(tmp_path)
    before = _controlled_scaffold_snapshot(repo)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(ROOT, "team-kits", "scaffold_team.ps1"), "-Team", "demo-team"],
        cwd=str(repo), capture_output=True, text=True, timeout=120,
        env=dict(os.environ, USERPROFILE=str(home)))
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "Provider output collision" in output and "rollback" in output.lower()
    assert _controlled_scaffold_snapshot(repo) == before
    assert collision.read_text(encoding="utf-8") == "# unowned collision sentinel\n"


def test_scaffold_sh_rolls_back_base_after_provider_collision(tmp_path):
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX scaffold integration runs on Unix CI")
    home, repo, collision = _scaffold_provider_collision_state(tmp_path)
    before = _controlled_scaffold_snapshot(repo)
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    result = subprocess.run(
        ["bash", os.path.join(ROOT, "team-kits", "scaffold_team.sh"), "demo-team"],
        cwd=str(repo), capture_output=True, text=True, timeout=120,
        env=dict(os.environ, HOME=str(home), PYTHONPATH=pythonpath))
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "Provider output collision" in output and "rollback" in output.lower()
    assert _controlled_scaffold_snapshot(repo) == before
    assert collision.read_text(encoding="utf-8") == "# unowned collision sentinel\n"


def test_scaffold_ps1_rejects_unknown_quoted_recorded_preset_before_mutation(tmp_path):
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("PowerShell scaffold integration runs on Windows")
    home, repo = _unknown_recorded_preset_state(tmp_path)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(ROOT, "team-kits", "scaffold_team.ps1"), "-Team", "demo-team"],
        cwd=str(repo), capture_output=True, text=True, timeout=120,
        env=dict(os.environ, USERPROFILE=str(home)))
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "retired" in output and "preset" in output.lower()
    _assert_unknown_preset_left_repo_untouched(repo)


def test_scaffold_sh_rejects_unknown_quoted_recorded_preset_before_mutation(tmp_path):
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX scaffold integration runs on Unix CI")
    home, repo = _unknown_recorded_preset_state(tmp_path)
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    result = subprocess.run(
        ["bash", os.path.join(ROOT, "team-kits", "scaffold_team.sh"), "demo-team"],
        cwd=str(repo), capture_output=True, text=True, timeout=120,
        env=dict(os.environ, HOME=str(home), PYTHONPATH=pythonpath))
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "retired" in output and "preset" in output.lower()
    _assert_unknown_preset_left_repo_untouched(repo)


def test_scaffold_ps1_rejects_duplicate_preset_keys_before_mutation(tmp_path):
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("PowerShell scaffold integration runs on Windows")
    home, repo = _duplicate_recorded_preset_state(tmp_path)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(ROOT, "team-kits", "scaffold_team.ps1"), "-Team", "demo-team"],
        cwd=str(repo), capture_output=True, text=True, timeout=120,
        env=dict(os.environ, USERPROFILE=str(home)))
    output = (result.stdout + result.stderr).lower()
    assert result.returncode != 0 and "duplicate yaml key" in output
    _assert_unknown_preset_left_repo_untouched(repo)


def test_scaffold_sh_rejects_duplicate_preset_keys_before_mutation(tmp_path):
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX scaffold integration runs on Unix CI")
    home, repo = _duplicate_recorded_preset_state(tmp_path)
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    result = subprocess.run(
        ["bash", os.path.join(ROOT, "team-kits", "scaffold_team.sh"), "demo-team"],
        cwd=str(repo), capture_output=True, text=True, timeout=120,
        env=dict(os.environ, HOME=str(home), PYTHONPATH=pythonpath))
    output = (result.stdout + result.stderr).lower()
    assert result.returncode != 0 and "duplicate yaml key" in output
    _assert_unknown_preset_left_repo_untouched(repo)


# Windows: real ps1 run
def test_scaffold_preset_and_map_sync(tmp_path):
    if os.name != "nt":
        pytest.skip("ps1 test runs on Windows; the sh mirror is covered by the kit audit")
    home = tmp_path / "home"
    kit = home / ".claude" / "team-kits" / "demo-team"
    for role in ("project-manager", "alpha", "beta", "gamma"):
        # lead + gamma use tier aliases: the lead is never in model_map and gamma has no map
        # entry, so both exercise the copy-time alias resolution (not the map stamping)
        model = {"project-manager": "lead", "gamma": "worker"}.get(role, "sonnet")
        write(str(kit / "agents" / ("%s.md" % role)),
              "---\nname: %s\ndescription: Demo %s\nmodel: %s\neffort: high\n---\nbody\n"
              % (role, role, model))
        write(str(kit / "skills" / role / "SKILL.md"), "---\nname: %s\n---\nx\n" % role)
    write(str(kit / "settings" / "settings.json"), '{"agent": "project-manager"}')
    write(str(kit / "hooks" / "noop.py"), "#!/usr/bin/env python3\n")
    write(str(kit / "presets.yaml"), "mini: alpha\nfull: all\n")
    write(str(kit / "VERSION"), "version: 2026.07.13-1\ncontent: x\n")
    write(str(kit / "constitution" / "AGENTS.md"),
          "<!-- agents-and-skills:team-kit demo-team -->\n# Demo constitution\nRule body.\n")
    legacy_kit = home / ".claude" / "team-kits" / "legacy-team"
    write(str(legacy_kit / "agents" / "legacy-specialist.md"), "old kit role\n")
    write(str(legacy_kit / "skills" / "legacy-specialist" / "SKILL.md"), "old kit skill\n")
    repo = tmp_path / "repo"
    config_path = repo / "project_memory" / "project_config.yaml"
    write(str(config_path),
          "project:\n  name: x\n  preset: mini\n"
          "providers:\n  - \"claude\"\n  - 'codex'  # generated provider\n"
          "model_map:\n  alpha: lead   # tier alias — must stamp as opus\n"
          "effort_map:\n  alpha: high\n")
    # Simulate a pre-manifest install from another kit plus unrelated user-owned files.
    write(str(repo / ".claude" / "agents" / "legacy-specialist.md"), "installed old role\n")
    write(str(repo / ".claude" / "skills" / "legacy-specialist" / "SKILL.md"),
          "installed old skill\n")
    # Legacy Copilot artifacts from an older kit (generation removed): the marker proves
    # ownership, so the full scaffold path must clean them up.
    write(str(repo / ".github" / "agents" / "alpha.agent.md"),
          "You are inside a team-kit governed repository.\n")
    write(str(repo / ".github" / "hooks" / "team-kit-hooks.json"),
          '{"version": 1, "hooks": {"PreToolUse": [{"bash": "python .claude/hooks/x.py"}]}}\n')
    write(str(repo / "AGENTS.md"),
          "<!-- agents-and-skills:team-kit legacy-team -->\n# Legacy constitution\n")
    write(str(repo / ".claude" / "agents" / "custom.md"), "custom\n")
    write(str(repo / ".claude" / "skills" / "custom" / "SKILL.md"), "custom\n")
    script = os.path.join(ROOT, "team-kits", "scaffold_team.ps1")

    def scaffold(*extra):
        return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                               script, "-Team", "demo-team", *extra],
                              cwd=str(repo), capture_output=True, text=True,
                              env=dict(os.environ, USERPROFILE=str(home)), timeout=120)

    roles_manifest = repo / ".claude" / "team_kit_roles.txt"
    write(str(roles_manifest),
          "# agents-and-skills:team-kit-roles v1 team=legacy-team count=2\n"
          "legacy-specialist\n")
    invalid = scaffold("-Preset", "mini")
    assert invalid.returncode != 0 and "Invalid/truncated" in invalid.stdout + invalid.stderr
    assert (repo / ".claude" / "agents" / "legacy-specialist.md").is_file()
    roles_manifest.unlink()

    valid_config = config_path.read_text(encoding="utf-8")
    # a PRESENT but invalid providers value stays fail-closed (the ABSENT key now defaults to
    # [claude, codex] for legacy configs — covered by its own generator test)
    config_path.write_text("project:\n  name: x\n  preset: mini\nproviders: 42\n",
                           encoding="utf-8")
    invalid_config = scaffold("-Preset", "mini")
    assert invalid_config.returncode != 0
    assert "Invalid provider configuration; no scaffold files were changed" in (
        invalid_config.stdout + invalid_config.stderr)
    assert "Legacy constitution" in (repo / "AGENTS.md").read_text(encoding="utf-8")
    config_path.write_text(valid_config, encoding="utf-8")

    r = scaffold("-Preset", "mini")
    assert r.returncode == 0, r.stdout + r.stderr
    agents = repo / ".claude" / "agents"
    assert (agents / "alpha.md").is_file() and (agents / "project-manager.md").is_file()
    assert not (agents / "beta.md").exists() and not (agents / "gamma.md").exists()
    skills = repo / ".claude" / "skills"
    assert (skills / "alpha" / "SKILL.md").is_file() and not (skills / "beta").exists()
    assert not (agents / "legacy-specialist.md").exists()
    assert not (skills / "legacy-specialist").exists()
    assert (agents / "custom.md").is_file() and (skills / "custom" / "SKILL.md").is_file()
    # V4 + tier alias: the user-approved map value `lead` stamps the concrete claude name
    assert "model: opus" in (agents / "alpha.md").read_text(encoding="utf-8-sig")
    # copy-time alias resolution: the lead is NOT in model_map — its kit-source alias must
    # still become the concrete reference-platform name on install
    pm_installed = (agents / "project-manager.md").read_text(encoding="utf-8-sig")
    assert "model: opus" in pm_installed and "model: lead" not in pm_installed
    # constitution ships as AGENTS.md + a 2-line CLAUDE.md import shim (marker on line 1)
    assert "Demo constitution" in (repo / "AGENTS.md").read_text(encoding="utf-8-sig")
    shim = (repo / "CLAUDE.md").read_text(encoding="utf-8-sig").splitlines()
    assert shim[0].startswith("<!-- agents-and-skills:team-kit demo-team")
    assert shim[1].strip() == "@AGENTS.md" and len([ln for ln in shim if ln.strip()]) == 2
    # providers: [claude, codex] -> the generator produced .codex artifacts (alpha on lead -> sol)
    assert (repo / ".codex" / "hooks.json").is_file()
    import tomllib
    codex_config = tomllib.loads((repo / ".codex" / "config.toml").read_text(encoding="utf-8-sig"))
    assert codex_config["model"] == "gpt-5.6-sol"
    alpha_toml = (repo / ".codex" / "agents" / "alpha.toml").read_text(encoding="utf-8-sig")
    assert 'model = "gpt-5.6-sol"' in alpha_toml
    assert not (repo / ".codex" / "agents" / "project-manager.toml").exists()
    assert (repo / ".agents" / "skills" / "alpha" / "SKILL.md").is_file()
    assert (repo / ".agents" / "skills" / "project-manager" / "SKILL.md").is_file()
    assert "agents-and-skills:generated-codex-config" in (
        repo / ".agents" / "skills" / "alpha" / ".team-kit-generated").read_text(
            encoding="utf-8")
    assert (repo / ".codex" / "config.toml").read_text(encoding="utf-8-sig").startswith(
        "# agents-and-skills:generated-codex-config")
    assert (repo / ".claude" / "hooks" / "noop.py").is_file()
    # legacy Copilot artifacts were marker-proven and removed by the provider transaction
    assert not (repo / ".github" / "agents" / "alpha.agent.md").exists()
    assert not (repo / ".github" / "hooks" / "team-kit-hooks.json").exists()
    assert (repo / ".claude" / "team_kit_roles.txt").read_text(
        encoding="utf-8-sig").splitlines() == [
            "# agents-and-skills:team-kit-roles v1 team=demo-team count=2",
            "project-manager", "alpha"]

    # Upgrade, then downgrade back to the recorded mini preset. Only kit-managed stale roles go;
    # unrelated user roles/skills survive.
    r_full = scaffold("-Preset", "full")
    assert r_full.returncode == 0, r_full.stdout + r_full.stderr
    assert (agents / "beta.md").is_file() and (repo / ".codex" / "agents" / "beta.toml").is_file()
    # gamma has NO model_map entry: its kit-source alias resolves at copy time
    gamma_installed = (agents / "gamma.md").read_text(encoding="utf-8-sig")
    assert "model: sonnet" in gamma_installed and "model: worker" not in gamma_installed

    config_text = config_path.read_text(encoding="utf-8")
    provider_block = "providers:\n  - \"claude\"\n  - 'codex'  # generated provider\n"
    config_path.write_text(config_text.replace(provider_block, "providers: [codex"),
                           encoding="utf-8")
    malformed = scaffold()
    assert malformed.returncode != 0 and "Invalid provider configuration; no scaffold files were changed" in (
        malformed.stdout + malformed.stderr)
    assert (repo / ".codex" / "agents" / "beta.toml").is_file()
    # the removed provider is rejected with a migration hint before any mutation
    config_path.write_text(config_text.replace(provider_block,
                                               "providers: [claude, codex, copilot]\n"),
                           encoding="utf-8")
    rejected = scaffold()
    assert rejected.returncode != 0 and "no longer supported" in (
        rejected.stdout + rejected.stderr)
    assert (repo / ".codex" / "agents" / "beta.toml").is_file()
    config_path.write_text(config_text.replace(provider_block,
                                               'providers: ["claude", "codex"]\n'),
                           encoding="utf-8")

    # a kit UPDATE without a preset argument must keep the RECORDED preset (project_config.yaml) —
    # not silently install the full roster (the inert-preset failure mode)
    r2 = scaffold()
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "from project_config.yaml" in r2.stdout
    assert not (agents / "beta.md").exists() and not (agents / "gamma.md").exists()
    assert not (repo / ".codex" / "agents" / "beta.toml").exists()
    assert not (repo / ".agents" / "skills" / "beta").exists()
    assert not (repo / ".github" / "agents" / "alpha.agent.md").exists()
    assert not (repo / ".github" / "hooks" / "team-kit-hooks.json").exists()
    assert (agents / "custom.md").is_file() and (skills / "custom" / "SKILL.md").is_file()
    assert "model: opus" in (agents / "alpha.md").read_text(encoding="utf-8-sig")
    backups = list((repo / ".claude" / "backups").glob("*/AGENTS.md"))
    assert backups
    assert list((repo / ".claude" / "backups").glob("*/.claude/provider_artifacts.json"))


def test_scaffold_sh_preset_and_provider_e2e(tmp_path):
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX scaffold integration runs on Unix CI")
    home = tmp_path / "home"
    kit = home / ".claude" / "team-kits" / "demo-team"
    for role in ("project-manager", "alpha", "beta"):
        model = "lead" if role == "project-manager" else "sonnet"
        write(str(kit / "agents" / (role + ".md")),
              "---\nname: %s\ndescription: Demo %s\nmodel: %s\neffort: high\n---\n%s body\n"
              % (role, role, model, role))
        write(str(kit / "skills" / role / "SKILL.md"),
              "---\nname: %s\n---\nFollow ./CLAUDE.md.\n" % role)
    # the lead never appears in model_map, so copy-time alias resolution is its ONLY path —
    # and CRLF content exercises the CR-tolerant awk (audit finding: non-MSYS awk keeps \r in $0)
    write(str(kit / "agents" / "project-manager.md"),
          "---\r\nname: project-manager\r\ndescription: Demo lead\r\nmodel: lead\r\n"
          "effort: high\r\n---\r\nlead body\r\n")
    write(str(kit / "settings" / "settings.json"), '{"agent": "project-manager"}\n')
    write(str(kit / "hooks" / "noop.py"), "#!/usr/bin/env python3\n")
    write(str(kit / "presets.yaml"), "mini: alpha\nfull: all\n")
    write(str(kit / "VERSION"), "version: 2026.07.14-test\ncontent: test\n")
    write(str(kit / "constitution" / "AGENTS.md"),
          "<!-- agents-and-skills:team-kit demo-team -->\n# Demo constitution\n")

    repo = tmp_path / "repo"
    write(str(repo / "project_memory" / "project_config.yaml"),
          "project:\n  name: demo\n  preset: mini\n"
          "providers: [claude, codex]\n"
          "model_map:\n  alpha: lead\n"
          "effort_map:\n  alpha: high\n")
    write(str(repo / ".claude" / "agents" / "custom.md"), "user-owned role\n")
    write(str(repo / ".claude" / "skills" / "custom" / "SKILL.md"), "user-owned skill\n")
    script = os.path.join(ROOT, "team-kits", "scaffold_team.sh")
    pythonpath = os.pathsep.join(path for path in sys.path if path)

    def scaffold(preset=None):
        command = ["bash", script, "demo-team"]
        if preset:
            command.append(preset)
        return subprocess.run(command, cwd=str(repo), capture_output=True, text=True, timeout=120,
                              env=dict(os.environ, HOME=str(home), PYTHONPATH=pythonpath))

    first = scaffold("mini")
    assert first.returncode == 0, first.stdout + first.stderr
    assert (repo / ".claude" / "agents" / "alpha.md").is_file()
    assert not (repo / ".claude" / "agents" / "beta.md").exists()
    assert (repo / ".claude" / "agents" / "custom.md").is_file()
    # copy-time alias resolution: lead is NOT in model_map, CRLF source, line ending preserved
    lead_installed = (repo / ".claude" / "agents" / "project-manager.md").read_bytes()
    assert b"model: opus\r\n" in lead_installed and b"model: lead" not in lead_installed
    assert (repo / ".codex" / "config.toml").is_file()
    assert (repo / ".agents" / "skills" / "alpha" / ".team-kit-generated").is_file()
    assert (repo / ".claude" / "team_kit_roles.txt").read_text(
        encoding="utf-8").splitlines() == [
            "# agents-and-skills:team-kit-roles v1 team=demo-team count=2",
            "project-manager", "alpha"]

    upgraded = scaffold("full")
    assert upgraded.returncode == 0, upgraded.stdout + upgraded.stderr
    assert (repo / ".claude" / "agents" / "beta.md").is_file()
    assert (repo / ".codex" / "agents" / "beta.toml").is_file()

    downgraded = scaffold()
    assert downgraded.returncode == 0, downgraded.stdout + downgraded.stderr
    assert "from project_config.yaml" in downgraded.stdout
    assert not (repo / ".claude" / "agents" / "beta.md").exists()
    assert not (repo / ".codex" / "agents" / "beta.toml").exists()
    assert not (repo / ".agents" / "skills" / "beta").exists()
    assert (repo / ".claude" / "agents" / "custom.md").is_file()
    assert (repo / ".claude" / "skills" / "custom" / "SKILL.md").is_file()
    assert list((repo / ".claude" / "backups").glob("*/.codex/config.toml"))


# ---------------- installers: fresh Codex-only homes + CODEX_HOME/override handling ----------------
def test_install_sh_codex_only_uses_codex_home(tmp_path):
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX installer integration runs on Unix CI")
    home = tmp_path / "home"
    codex_home = tmp_path / "custom-codex"
    write(str(codex_home / "AGENTS.md"), "# old entry gate\n")
    write(str(codex_home / "AGENTS.override.md"), "# keep me\n")
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    command = ["bash", os.path.join(ROOT, "install.sh"), "--target", "codex", "--force"]
    env = dict(os.environ, HOME=str(home), CODEX_HOME=str(codex_home), PYTHONPATH=pythonpath)
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=180,
                            env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (codex_home / "AGENTS.md").is_file()
    assert (codex_home / "AGENTS.override.md").read_text(encoding="utf-8") == "# keep me\n"
    assert (home / ".claude" / "team-kits" / "gen_provider_artifacts.py").is_file()
    assert (home / ".claude" / "team-kits" / "preset_config.py").is_file()
    first_backups = list((home / ".claude" / "backups").glob("*/codex-AGENTS.md"))
    assert len(first_backups) == 1
    assert first_backups[0].read_text(encoding="utf-8") == "# old entry gate\n"
    assert list((home / ".claude" / "backups").glob("*/codex-AGENTS.override.md"))
    assert "entry gate stays inactive" in result.stdout

    second = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=180,
                            env=env)
    assert second.returncode == 0, second.stdout + second.stderr
    backup_dirs = {path.parent for path in
                   (home / ".claude" / "backups").glob("*/codex-AGENTS.md")}
    assert len(backup_dirs) == 2
    assert not list((home / ".claude").glob(".team-kits.stage.*"))
    assert not list((home / ".claude").glob(".team-kits.previous.*"))


def test_install_sh_rejects_symlinked_codex_agents_before_backup(tmp_path):
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX installer integration runs on Unix CI")
    home = tmp_path / "home"
    codex_home = tmp_path / "custom-codex"
    external = tmp_path / "external" / "AGENTS.md"
    write(str(external), "# external sentinel\n")
    codex_home.mkdir(parents=True)
    os.symlink(external, codex_home / "AGENTS.md")
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    result = subprocess.run(
        ["bash", os.path.join(ROOT, "install.sh"), "--target", "codex", "--force"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=180,
        env=dict(os.environ, HOME=str(home), CODEX_HOME=str(codex_home),
                 PYTHONPATH=pythonpath))
    assert result.returncode != 0
    assert "symlink" in (result.stdout + result.stderr).lower()
    assert external.read_text(encoding="utf-8") == "# external sentinel\n"
    assert (codex_home / "AGENTS.md").is_symlink()
    assert not (home / ".claude" / "backups").exists()
    assert not (home / ".claude" / "team-kits").exists()


def test_install_sh_codex_only_creates_fresh_codex_home(tmp_path):
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX installer integration runs on Unix CI")
    home = tmp_path / "home"
    codex_home = tmp_path / "fresh-codex"
    assert not codex_home.exists()
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    result = subprocess.run(
        ["bash", os.path.join(ROOT, "install.sh"), "--target", "codex", "--force"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=180,
        env=dict(os.environ, HOME=str(home), CODEX_HOME=str(codex_home),
                 PYTHONPATH=pythonpath))
    assert result.returncode == 0, result.stdout + result.stderr
    assert codex_home.is_dir() and (codex_home / "AGENTS.md").is_file()
    assert "created Codex home" in result.stdout
    assert (home / ".claude" / "team-kits" / "gen_provider_artifacts.py").is_file()
    assert (home / ".claude" / "team-kits" / "preset_config.py").is_file()


def test_install_sh_rejects_invalid_target():
    if os.name == "nt" or not shutil.which("bash"):
        pytest.skip("POSIX installer integration runs on Unix CI")
    result = subprocess.run(
        ["bash", os.path.join(ROOT, "install.sh"), "--target", "invalid", "--force"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=30)
    assert result.returncode != 0 and "Invalid target" in result.stderr


# ---------------- codex_global_config.py: opt-in user-wide secret shield ----------------
CODEX_SHIELD = os.path.join(ROOT, "user", "codex_global_config.py")


def _run_shield(codex_home):
    return subprocess.run([sys.executable, CODEX_SHIELD, str(codex_home)],
                          capture_output=True, text=True, timeout=60)


def test_codex_shield_appends_and_activates(tmp_path):
    import tomllib
    home = tmp_path / "codex"
    write(str(home / "config.toml"),
          'personality = "pragmatic"\nmodel = "gpt-5.6-sol"\n\n[windows]\nsandbox = "elevated"\n'
          "[projects.'c:\\x']\ntrust_level = \"trusted\"\n")
    r = _run_shield(home)
    assert r.returncode == 0, r.stdout + r.stderr
    text = (home / "config.toml").read_text(encoding="utf-8")
    data = tomllib.loads(text)
    assert data["default_permissions"] == "agents-and-skills-secrets"
    profile = data["permissions"]["agents-and-skills-secrets"]
    assert profile["extends"] == ":workspace"
    assert profile["filesystem"][":workspace_roots"]["**/*.pem"] == "deny"
    assert profile["filesystem"]["~/.ssh"] == "deny"
    # personal content untouched, activation line BEFORE the first table (TOML top-level rule)
    assert data["personality"] == "pragmatic" and data["windows"]["sandbox"] == "elevated"
    assert text.index("default_permissions") < text.index("[windows]")
    assert (home / "config.toml.agents-and-skills.bak").is_file()
    before = text
    r2 = _run_shield(home)  # idempotent: marker present -> byte-identical
    assert r2.returncode == 0
    assert (home / "config.toml").read_text(encoding="utf-8") == before

    # a fresh Codex home without a config.toml gets a valid minimal one
    empty_home = tmp_path / "codex-fresh"
    empty_home.mkdir()
    r3 = _run_shield(empty_home)
    assert r3.returncode == 0, r3.stdout + r3.stderr
    fresh = tomllib.loads((empty_home / "config.toml").read_text(encoding="utf-8"))
    assert fresh["default_permissions"] == "agents-and-skills-secrets"


def test_codex_shield_fail_closed(tmp_path):
    home = tmp_path / "codex"
    write(str(home / "config.toml"), 'sandbox_mode = "workspace-write"\n')
    r = _run_shield(home)
    assert r.returncode == 3 and "IGNORES permission profiles" in r.stderr
    assert (home / "config.toml").read_text(
        encoding="utf-8") == 'sandbox_mode = "workspace-write"\n'
    write(str(home / "config.toml"), "not [ valid toml\n")
    r2 = _run_shield(home)
    assert r2.returncode == 2 and "nothing was written" in r2.stderr
    assert (home / "config.toml").read_text(encoding="utf-8") == "not [ valid toml\n"


def test_codex_shield_respects_existing_default(tmp_path):
    import tomllib
    home = tmp_path / "codex"
    write(str(home / "config.toml"),
          'default_permissions = "mine"\n\n[permissions.mine]\nextends = ":workspace"\n')
    r = _run_shield(home)
    assert r.returncode == 0 and "NOT activated" in r.stdout
    data = tomllib.loads((home / "config.toml").read_text(encoding="utf-8"))
    assert data["default_permissions"] == "mine"  # the user's choice is never fought
    assert "agents-and-skills-secrets" in data["permissions"]


def test_install_ps1_codex_global_secrets_flag(tmp_path):
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("PowerShell installer integration runs on Windows")
    home = tmp_path / "home"
    codex_home = tmp_path / "codex-home"
    appdata = tmp_path / "appdata"
    write(str(codex_home / "config.toml"), 'personality = "pragmatic"\n')
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
               os.path.join(ROOT, "install.ps1"), "-Target", "codex", "-Force",
               "-CodexGlobalSecrets"]
    env = dict(os.environ, USERPROFILE=str(home), APPDATA=str(appdata),
               CODEX_HOME=str(codex_home), PYTHONPATH=pythonpath)
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=180,
                            env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    text = (codex_home / "config.toml").read_text(encoding="utf-8")
    assert "agents-and-skills:codex-global-secrets" in text
    assert 'default_permissions = "agents-and-skills-secrets"' in text
    assert 'personality = "pragmatic"' in text
    assert list((home / ".claude" / "backups").glob("*/codex-config.toml"))


def test_install_ps1_codex_only_uses_codex_home(tmp_path):
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("PowerShell installer integration runs on Windows")
    home = tmp_path / "home"
    codex_home = tmp_path / "custom-codex"
    appdata = tmp_path / "appdata"
    write(str(codex_home / "AGENTS.md"), "# old entry gate\n")
    write(str(codex_home / "AGENTS.override.md"), "# keep me\n")
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
               os.path.join(ROOT, "install.ps1"), "-Target", "codex", "-Force"]
    env = dict(os.environ, USERPROFILE=str(home), APPDATA=str(appdata),
               CODEX_HOME=str(codex_home), PYTHONPATH=pythonpath)
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=180,
                            env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (codex_home / "AGENTS.md").is_file()
    assert (codex_home / "AGENTS.override.md").read_text(encoding="utf-8") == "# keep me\n"
    assert (home / ".claude" / "team-kits" / "gen_provider_artifacts.py").is_file()
    assert (home / ".claude" / "team-kits" / "preset_config.py").is_file()
    first_backups = list((home / ".claude" / "backups").glob("*/codex-AGENTS.md"))
    assert len(first_backups) == 1
    assert first_backups[0].read_text(encoding="utf-8") == "# old entry gate\n"
    assert list((home / ".claude" / "backups").glob("*/codex-AGENTS.override.md"))
    assert "entry gate stays inactive" in result.stdout

    second = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=180,
                            env=env)
    assert second.returncode == 0, second.stdout + second.stderr
    backup_dirs = {path.parent for path in
                   (home / ".claude" / "backups").glob("*/codex-AGENTS.md")}
    assert len(backup_dirs) == 2
    assert not list((home / ".claude").glob(".team-kits.stage.*"))
    assert not list((home / ".claude").glob(".team-kits.previous.*"))


def test_install_ps1_rejects_symlinked_codex_agents_before_backup(tmp_path):
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("PowerShell installer integration runs on Windows")
    home = tmp_path / "home"
    codex_home = tmp_path / "custom-codex"
    appdata = tmp_path / "appdata"
    external = tmp_path / "external" / "AGENTS.md"
    write(str(external), "# external sentinel\n")
    codex_home.mkdir(parents=True)
    try:
        os.symlink(external, codex_home / "AGENTS.md")
    except (OSError, NotImplementedError) as exc:
        pytest.skip("file symlinks are not permitted in this test environment: %s" % exc)
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(ROOT, "install.ps1"), "-Target", "codex", "-Force"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=180,
        env=dict(os.environ, USERPROFILE=str(home), APPDATA=str(appdata),
                 CODEX_HOME=str(codex_home), PYTHONPATH=pythonpath))
    assert result.returncode != 0
    output = (result.stdout + result.stderr).lower()
    assert "symlink" in output or "reparse" in output
    assert external.read_text(encoding="utf-8") == "# external sentinel\n"
    assert (codex_home / "AGENTS.md").is_symlink()
    assert not (home / ".claude" / "backups").exists()
    assert not (home / ".claude" / "team-kits").exists()


def test_install_ps1_codex_only_creates_fresh_codex_home(tmp_path):
    if os.name != "nt" or not shutil.which("powershell"):
        pytest.skip("PowerShell installer integration runs on Windows")
    home = tmp_path / "home"
    codex_home = tmp_path / "fresh-codex"
    appdata = tmp_path / "appdata"
    assert not codex_home.exists()
    pythonpath = os.pathsep.join(path for path in sys.path if path)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         os.path.join(ROOT, "install.ps1"), "-Target", "codex", "-Force"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=180,
        env=dict(os.environ, USERPROFILE=str(home), APPDATA=str(appdata),
                 CODEX_HOME=str(codex_home), PYTHONPATH=pythonpath))
    assert result.returncode == 0, result.stdout + result.stderr
    assert codex_home.is_dir() and (codex_home / "AGENTS.md").is_file()
    assert "created Codex home" in result.stdout
    assert (home / ".claude" / "team-kits" / "gen_provider_artifacts.py").is_file()
    assert (home / ".claude" / "team-kits" / "preset_config.py").is_file()


# ---------------- upstream round: kit_checks additions (chunk guard, invariants, repo-wide yaml) ----------------
def test_kit_checks_chunk_warnlimit_guard(tmp_path):
    mod = _kit_checks_mod()
    # a protective COMMENT mentioning the key must never trip the guard
    write(str(tmp_path / "frontend" / "vite.config.ts"),
          "// chunkSizeWarningLimit stays at Vite's DEFAULT and MUST NEVER be raised\n"
          "export default {}\n")
    calls, ok, fail, warn = _collector()
    mod.check_frontend_build_config(str(tmp_path), ok, fail, warn)
    assert not calls["fail"] and any("chunkSizeWarningLimit" in n for n in calls["ok"])
    write(str(tmp_path / "frontend" / "vite.config.ts"),
          "export default { build: { chunkSizeWarningLimit: 1000 } }\n")
    calls, ok, fail, warn = _collector()
    mod.check_frontend_build_config(str(tmp_path), ok, fail, warn)
    assert any("ASSIGNED" in m for _n, m in calls["fail"])


def test_kit_checks_module_invariants(tmp_path):
    mod = _kit_checks_mod()
    capture_invariant(tmp_path, "module_invariants", value=[
        {"path": "src/pure.py", "forbidden_tokens": ["open("],
         "reason": "pure module - no I/O"}])
    write(str(tmp_path / "src" / "pure.py"),
          "# never call open( in this module\ndef f():\n    return 1\n")
    calls, ok, fail, warn = _collector()
    mod.check_module_invariants(str(tmp_path), ok, fail, warn)
    assert not calls["fail"]  # comment-only mention never trips
    write(str(tmp_path / "src" / "pure.py"), "def f():\n    return open('x').read()\n")
    calls, ok, fail, warn = _collector()
    mod.check_module_invariants(str(tmp_path), ok, fail, warn)
    assert any("pure module - no I/O" in m for _n, m in calls["fail"])
    os.remove(str(tmp_path / "src" / "pure.py"))
    calls, ok, fail, warn = _collector()
    mod.check_module_invariants(str(tmp_path), ok, fail, warn)
    assert any("missing" in m for _n, m in calls["warn"])  # stale rule guards nothing


def test_kit_checks_repo_wide_yaml_parse(tmp_path):
    pytest.importorskip("yaml")
    mod = _kit_checks_mod()
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), capture_output=True)
    write(str(tmp_path / "project_memory" / "product" / "active" / "PR-0001.yaml"), "id: PR-0001\n")
    write(str(tmp_path / "config" / "bad.yaml"), "a: [unclosed\n")
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), capture_output=True)
    calls, ok, fail, warn = _collector()
    mod.check_project_memory_yaml(str(tmp_path), ok, fail, warn)
    assert any(n == "yaml-lint (repo-wide)" for n, _m in calls["fail"])
    capture_invariant(tmp_path, "yaml_lint_exclude", value=["config/*"])
    calls, ok, fail, warn = _collector()
    mod.check_project_memory_yaml(str(tmp_path), ok, fail, warn)
    assert not any(n == "yaml-lint (repo-wide)" for n, _m in calls["fail"])


def _browser_checks_mod():
    import importlib.util
    spec = importlib.util.spec_from_file_location("browser_checks_under_test", BROWSER_CHECKS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_browser_smoke_config_and_missing_dist(tmp_path):
    mod = _browser_checks_mod()
    capture_invariant(tmp_path, "coverage_gate", value={"threshold": 80})
    capture_invariant(tmp_path, "browser_smoke",
                      value={"entry": "/app/", "mount_selector": "#app"})
    assert mod._config(str(tmp_path)) == ("/app/", "#app")
    calls, ok, fail, warn = _collector()
    mod.browser_smoke(str(tmp_path), ok, fail, warn)  # no frontend/dist
    assert not calls["fail"] and any("dist missing" in m for _n, m in calls["warn"])


def test_browser_smoke_falls_back_when_no_invariant_configures_it(tmp_path):
    """The default route must stay the default, and only that.

    The audit finding this replaces was a config that SILENTLY fell back — an unquoted value with a
    trailing comment voided the whole line and the smoke green-tested the wrong page. The V2 reader
    parses YAML rather than lines, so that particular hazard is gone; what still has to hold is
    that an unconfigured project gets `/` and `#root` instead of an exception.
    """
    mod = _browser_checks_mod()
    os.makedirs(str(tmp_path / "project_memory"), exist_ok=True)
    assert mod._config(str(tmp_path)) == ("/", "#root")


def test_quality_declared_stacks_quoted_block(tmp_path):
    os.makedirs(str(tmp_path / "scripts"))
    shutil.copy(QUALITY, str(tmp_path / "scripts" / "quality.py"))
    write(str(tmp_path / "project_memory" / "project_config.yaml"),
          "stacks:  # declared by the architect\n  - 'python'\n  # more later\n  - go\n")
    mod = _quality_mod(str(tmp_path / "scripts" / "quality.py"))
    assert mod.declared_stacks() == ["python", "go"]


def test_kit_checks_module_invariants_string_tokens(tmp_path):
    # audit finding: a bare-string forbidden_tokens iterated CHARACTERS ('e' matched everywhere)
    mod = _kit_checks_mod()
    capture_invariant(tmp_path, "module_invariants", value=[
        {"path": "src/pure.py", "forbidden_tokens": "open(", "reason": "pure"}])
    write(str(tmp_path / "src" / "pure.py"), "def f():\n    return open('x').read()\n")
    calls, ok, fail, warn = _collector()
    mod.check_module_invariants(str(tmp_path), ok, fail, warn)
    assert len(calls["fail"]) == 1 and "'open('" in calls["fail"][0][1]


# ---------------- guard_question_context: a question must never point at invisible context ----------------
def _question_payload(tmp_path, question, desc="pick one"):
    return {"tool_name": "AskUserQuestion", "cwd": str(tmp_path),
            "tool_input": {"questions": [{"question": question, "header": "Decision",
                                          "options": [{"label": "Ja", "description": desc},
                                                      {"label": "Nein", "description": "skip"}],
                                          "multiSelect": False}]}}


def test_question_context_blocks_invisible_references(tmp_path):
    # the real incident: sign-off requested for a summary that existed only in THINKING
    bad = _question_payload(tmp_path, "Kategorien-Set freigeben (wie oben zusammengefasst)?")
    r = run_hook_process("guard_question_context.py", bad, tmp_path)
    assert r.returncode == 2 and "CANNOT see" in r.stderr
    # an option DESCRIPTION referencing invisible context blocks too
    desc_bad = _question_payload(tmp_path, "Freigeben?", desc="applies the plan as summarized above")
    assert run_hook("guard_question_context.py", desc_bad, tmp_path) == 2
    for hooks_dir in (RESEARCH_HOOKS, OFFICE_HOOKS):  # mirrored guard behaves identically
        assert run_hook("guard_question_context.py", bad, tmp_path, hooks_dir=hooks_dir) == 2


def test_question_context_allows_self_contained_and_dialogue_refs(tmp_path):
    good = _question_payload(
        tmp_path, "Kategorien-Set freigeben? Vorschlag: 12 Kategorien (Wareneinkauf, Versand, "
                  "Gebühren, ...) — Details in den Optionen.")
    assert run_hook("guard_question_context.py", good, tmp_path) == 0
    # "wie besprochen" refers to the VISIBLE dialogue with the user — must stay legal
    dialogue = _question_payload(tmp_path, "Wie besprochen mit Etappe 1 starten?")
    assert run_hook("guard_question_context.py", dialogue, tmp_path) == 0
    # prose containing 'above' in a non-reference sense stays legal
    prose = _question_payload(tmp_path, "Ist die above-average Latenz akzeptabel?")
    assert run_hook("guard_question_context.py", prose, tmp_path) == 0


def run_hook_raw_utf8(name, payload, project_dir, hooks_dir=None):
    """Send the payload as RAW UTF-8 bytes (ensure_ascii=False) — how providers really send it.
    json.dumps' default ASCII-escaping made the test suite structurally blind to the audit-proven
    Windows failure: text-mode stdin decoded cp1252 and umlaut patterns never matched."""
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project_dir))
    return subprocess.run([sys.executable, os.path.join(hooks_dir or HOOKS, name)],
                          input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                          capture_output=True, env=env, timeout=60)


def test_question_context_matches_umlauts_in_raw_utf8_stdin(tmp_path):
    bad = _question_payload(tmp_path, "Freigeben (oben erwähnt)?")
    r = run_hook_raw_utf8("guard_question_context.py", bad, tmp_path)
    assert r.returncode == 2  # cp1252 stdin used to mojibake 'erwähnt' -> silent miss
    flexed = _question_payload(tmp_path, "Das oben beschriebene Set freigeben?")
    assert run_hook_raw_utf8("guard_question_context.py", flexed, tmp_path).returncode == 2
    placement = _question_payload(tmp_path, "Soll die Navigation oben dargestellt werden?")
    assert run_hook_raw_utf8("guard_question_context.py", placement, tmp_path).returncode == 0
    garbage = {"tool_name": "AskUserQuestion", "cwd": str(tmp_path), "tool_input": "not a dict"}
    assert run_hook_raw_utf8("guard_question_context.py", garbage, tmp_path).returncode == 0


def test_question_context_catches_audit_reported_misses(tmp_path):
    for text in ("Approve the plan as mentioned above?",
                 "Approve the plan above?",
                 "Die o.g. Punkte freigeben?",
                 "Die obigen Kategorien freigeben?"):
        payload = _question_payload(tmp_path, text)
        assert run_hook("guard_question_context.py", payload, tmp_path) == 2, text
    header_ref = _question_payload(tmp_path, "Freigeben?")
    header_ref["tool_input"]["questions"][0]["header"] = "s.o."
    assert run_hook("guard_question_context.py", header_ref, tmp_path) == 2


def test_quality_without_pyyaml_keeps_its_state_root_fallback_and_defaults_the_rest(tmp_path,
                                                                                    monkeypatch):
    """CI always installs pyyaml, so the demoted regex fallbacks were DEAD paths in CI (audit) —
    the yaml import is poisoned here to measure what a pyyaml-less machine really does.

    The answer CHANGED with the knobs' move into `INV` items, and this test says so rather than
    asserting the old one: `project_config.yaml` is a single state-root file and keeps its regex
    fallback, while a knob now lives in an item store that cannot be listed and parsed without a
    parser. Writing a second, regex-shaped reader for that store would have been two parsers for one
    question — the exact divergence an audit already caught between this file and `kit_checks` — so
    the knobs degrade to their DEFAULTS instead, visibly and without an exception.
    """
    os.makedirs(str(tmp_path / "scripts"))
    shutil.copy(QUALITY, str(tmp_path / "scripts" / "quality.py"))
    shutil.copy(KIT_CHECKS, str(tmp_path / "scripts" / "kit_checks.py"))
    write(str(tmp_path / "project_memory" / "project_config.yaml"),
          "project:\n  stacks:\n    - python\n")
    capture_invariant(tmp_path, "compounder/", text="the whole codebase lives here")
    capture_invariant(tmp_path, "coverage_gate", value={"threshold": 85})
    os.makedirs(str(tmp_path / "compounder"))
    mod = _quality_mod(str(tmp_path / "scripts" / "quality.py"))
    assert mod.coverage_threshold() == 85            # with a parser: the declared value
    assert "compounder" in mod._python_targets()
    monkeypatch.setitem(sys.modules, "yaml", None)   # import yaml -> ImportError
    assert mod.declared_stacks() == ["python"]       # state-root file: regex fallback survives
    assert mod.coverage_threshold() == 80            # item store: unreadable -> the default
    assert "compounder" not in mod._python_targets()


# ---------------- update-flow round: marker announce, alias guard, transcript handover ----------------
def test_session_status_announces_from_scaffold_marker(tmp_path):
    # the one-shot kit_updated_from marker survives broken/parallel restarts — the pure
    # last_seen delta lost the announcement when no clean SessionStart followed (audit:
    # a live repo sat two days without the banner, mislabeled as "applied externally")
    repo = tmp_path / "repo"
    write(str(repo / ".claude" / "kit_version"), "version: 2026.07.17-8\n")
    write(str(repo / ".claude" / "kit_updated_from"), "version: 2026.07.16-1\n")
    payload = {"hook_event_name": "SessionStart", "cwd": str(repo)}
    r = run_hook_process("session_status.py", payload, repo)
    assert "KIT UPDATED: 2026.07.16-1 -> 2026.07.17-8" in r.stdout
    assert "do NOT run the scaffold again" in r.stdout
    assert not (repo / ".claude" / "kit_updated_from").exists()  # consumed exactly once
    assert (repo / ".claude" / "kit_last_seen_version").read_text().strip() == "2026.07.17-8"
    r2 = run_hook_process("session_status.py", payload, repo)
    assert "KIT UPDATED" not in r2.stdout  # announced once, then silent


def test_session_status_flags_unresolved_tier_alias(tmp_path):
    # a raw `model: worker` in INSTALLED frontmatter crashes subagents at spawn; the
    # canonicalized compare used to call it "in sync" (audit: a real bookkeeper died)
    repo = tmp_path / "repo"
    write(str(repo / "project_memory" / "project_config.yaml"),
          "name: x\nmodel_map:\n  bookkeeper: worker\n")
    write(str(repo / ".claude" / "agents" / "bookkeeper.md"),
          "---\nname: bookkeeper\nmodel: worker\n---\nbody\n")
    payload = {"hook_event_name": "SessionStart", "cwd": str(repo)}
    r = run_hook_process("session_status.py", payload, repo)
    assert "UNRESOLVED tier alias" in r.stdout
    write(str(repo / ".claude" / "agents" / "bookkeeper.md"),
          "---\nname: bookkeeper\nmodel: sonnet\n---\nbody\n")
    r2 = run_hook_process("session_status.py", payload, repo)
    assert "UNRESOLVED tier alias" not in r2.stdout  # resolved name + worker map = in sync


def test_session_status_points_at_previous_transcript(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".claude").mkdir(parents=True)
    home = tmp_path / "home"
    key = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(str(repo)))
    tdir = home / ".claude" / "projects" / key
    write(str(tdir / "aaaa-old-session.jsonl"), '{"type":"user"}\n')
    payload = {"hook_event_name": "SessionStart", "cwd": str(repo),
               "session_id": "bbbb-current"}
    r = run_hook_process("session_status.py", payload, repo,
                         extra_env={"USERPROFILE": str(home), "HOME": str(home)})
    assert "PREVIOUS SESSION transcript" in r.stdout and "aaaa-old-session" in r.stdout
    assert "never re-open settled decisions" in r.stdout
    # the CURRENT session's own transcript must never be suggested as "previous"
    write(str(tdir / "bbbb-current.jsonl"), '{"type":"user"}\n')
    r2 = run_hook_process("session_status.py", payload, repo,
                          extra_env={"USERPROFILE": str(home), "HOME": str(home)})
    assert "aaaa-old-session" in r2.stdout and "bbbb-current.jsonl" not in r2.stdout


# ---------------- the command surface, measured in a project the installers built ----------

PR_BODY = {
    "title": "Checkout flow", "class": "normal", "problem": "no checkout",
    "goal": "working checkout",
    "acceptance_criteria": [{"id": "AC-1", "text": "order completes"}],
    "invariants": [], "out_of_scope": [], "priority": "high",
    "user_story": "As a buyer I can pay",
}


def _entry_point(repo, *arguments, body=None):
    """Run the INSTALLED entry point the way a role does, from the project root.

    The suite's own bytecode variables are stripped for the reason
    `test_the_evidence_the_merge_gate_demands_has_an_installed_producer` states: a role's shell
    has neither, so neither may decide anything here.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTHONPATH", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE")}
    # ENCODING PINNED ON THE READING SIDE TOO. The approval question carries `für` and `…`,
    # and the gate compares it character for character -- so a reader that decodes the entry
    # point's stdout with the machine's ANSI codepage turns a correct question into a mismatch,
    # which is exactly the class `test_e2e.py` exists for. The producer pins UTF-8
    # (`cli._pin_utf8`); this is the consumer half.
    return subprocess.run(
        [sys.executable, os.path.join(*cli.ENTRY_POINT.split("/"))] + list(arguments),
        cwd=str(repo), input=body, capture_output=True, text=True, encoding="utf-8",
        env=env, timeout=120)


def _every_shell_gate_allows(repo, command, agent_id=None):
    """Every `Bash|PowerShell` PreToolUse hook THIS project registered, run on one command line.

    `agent_id` is what a SUBAGENT's payload carries. Passing it is not decoration: nothing binds a
    harness command line to a role, so the same line runs from a specialist as from the lead, and
    a check that only ever measured the lead's payload would describe half the surface.
    """
    for gate in _shell_gates_of(repo):
        seen = _run_project_hook(repo, gate, command, agent_id=agent_id)
        assert seen.returncode == 0, (
            "%s refuses `%s` (agent_id=%r):\n%s" % (gate, command, agent_id, seen.stderr))


def _approval_question(repo, kind, item_id):
    """Phase 1 THROUGH THE SHIPPED COMMAND LINE, not through a library call.

    This is the half that decides whether the transition gate has a walkable counterpart at all.
    `create_pending_request` had no caller in the shipped tree, so measuring the happy path with a
    library call would have measured a project nobody can run: no pending request, no marked
    question, no mint, and a root item that never leaves DRAFT. So the request is opened by
    running `python scripts/harness.py request-approval <kind> <ITEM-ID>` in the project, and the
    question the kernel composed is read off its stdout.
    """
    opened = _entry_point(repo, "request-approval", kind, item_id)
    assert opened.returncode == 0, opened.stdout + opened.stderr
    question = json.loads(opened.stdout)
    assert "[APR-REQ:" in question["question"], question
    return question


def _mint_in_project(repo, kind, item_id):
    """Open the request through the CLI, pin the question, then mint through the project's hook.

    All three phases of spec II.2 run as the platform runs them: the kernel composes the question
    (the command above), `gate_approval` PreToolUse compares the question the model would ask
    against the one the kernel wrote, and PostToolUse mints from the recorded answer. The mint is
    still the only thing `approvals.mint` accepts a caller for.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import approvals
    from kernel.state import ProjectState
    state = ProjectState(os.path.join(str(repo), "project_memory"))
    question = _approval_question(repo, kind, item_id)
    request_id = re.search(r"\[APR-REQ:([0-9a-f]{32})\]", question["question"]).group(1)
    mint_code = approvals.pending_request(state, request_id)["mint_code"]

    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["CLAUDE_PROJECT_DIR"] = str(repo)
    hook = os.path.join(str(repo), ".claude", "hooks", "gate_approval.py")

    asked = subprocess.run(
        [sys.executable, "-B", hook],
        input=json.dumps({"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion",
                          "cwd": str(repo), "tool_input": {"questions": [question]}}),
        capture_output=True, text=True, env=env, timeout=120)
    assert asked.returncode == 0, (
        "the gate refused the question its own kernel composed:\n%s" % asked.stderr)

    payload = {"hook_event_name": "PostToolUse", "tool_name": "AskUserQuestion", "cwd": str(repo),
               "tool_input": {"questions": [question]},
               "tool_response": {"answers": {
                   question["question"]: approvals.approve_label(mint_code)},
                   "questions": [question]}}
    minted = subprocess.run([sys.executable, "-B", hook], input=json.dumps(payload),
                            capture_output=True, text=True, env=env, timeout=120)
    assert minted.returncode == 0 and "recorded for" in minted.stderr, minted.stderr
    return state


def test_the_four_commands_spec_ii4_named_are_runnable_by_the_role_that_needs_them(tmp_path):
    """`capture`, `create-task`, `dispatch`, `submit-result` -- through the gates, then executed.

    Both halves, for the reason the Evidence measurement gives: a command the gates refuse is no
    remedy, and a command the gates allow but that writes nothing is no producer. The command
    lines here are the ones a role would type, including the heredoc `capture` needs -- its body
    is a JSON object on stdin, because `gate_write_scope` refuses a write-capable pipeline that
    names the state directory, which is what any `--from project_memory/...` would have to do.

    WHAT THIS ALSO MEASURES, because it is the direct consequence of shipping them: the role is
    now the author of its own work orders. `--allowed-scope` is gate layer 3's only input, so the
    party a specialist's writes are scoped by is the party that wrote the scope. That is what spec
    II.4 asks for; it is bounded by the plan fields freezing outside DRAFT and by the dispatch
    still needing a user approval on the root, both of which are asserted below.
    """
    repo, _created = _project_the_installers_produce(tmp_path / "surface")
    body = json.dumps(PR_BODY)

    capture_line = "python scripts/harness.py capture PR <<'EOF'\n%s\nEOF" % body
    _every_shell_gate_allows(repo, capture_line)
    # ...and from a SUBAGENT's payload too, which is the honest half: nothing binds a harness
    # command line to a role, so a bound specialist can capture items and plan work orders it
    # would never be dispatched for. Measured rather than reasoned, and named in the shim's
    # docstring -- closing it needs a role rule the shell layer does not have today.
    _every_shell_gate_allows(repo, capture_line, agent_id="agent_specialist_1")
    captured = _entry_point(repo, "capture", "PR", body=body)
    assert captured.returncode == 0, captured.stdout + captured.stderr
    assert "PR-0001 DRAFT" in captured.stdout, captured.stdout

    task_arguments = ["create-task", "--product-requirement", "PR-0001",
                      "--derives-from", "PR-0001", "--type", "implementation",
                      "--assigned-role", "backend-developer", "--acceptance-ref", "AC-1",
                      "--allowed-scope", "src/"]
    _every_shell_gate_allows(repo, "python scripts/harness.py " + " ".join(task_arguments))
    planned = _entry_point(repo, *task_arguments)
    assert planned.returncode == 0, planned.stdout + planned.stderr
    assert "TSK-0001 DRAFT (backend-developer)" in planned.stdout, planned.stdout

    # a dispatch without the user's approval on the root is refused BY THE KERNEL, not by a gate
    _every_shell_gate_allows(repo, "python scripts/harness.py dispatch TSK-0001")
    _entry_point(repo, "transition", "TSK-0001", "READY")
    unapproved = _entry_point(repo, "dispatch", "TSK-0001")
    assert unapproved.returncode == 1, unapproved.stdout + unapproved.stderr
    assert "no subagent without a user approval" in unapproved.stderr, unapproved.stderr

    _mint_in_project(repo, "scope", "PR-0001")
    leased = _entry_point(repo, "dispatch", "TSK-0001")
    assert leased.returncode == 0, leased.stdout + leased.stderr
    assert leased.stdout.strip().startswith("HARNESS_DISPATCH "), leased.stdout

    # the work order's gate inputs FREEZE outside DRAFT -- a leased task cannot be re-scoped
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    state = ProjectState(os.path.join(str(repo), "project_memory"))
    with pytest.raises(Exception, match="frozen outside"):
        state.update_item("TSK-0001", {"allowed_scope": ["**"]})

    from kernel import dispatch as dispatch_module
    header = dispatch_module.parse_header(leased.stdout)
    dispatch_module.validate_dispatch(state, header, "backend-developer", claim=True)
    dispatch_module.spawn_outcome(state, "TSK-0001", True)
    submit_arguments = ["submit-result", "--task-id", "TSK-0001", "--role", "backend-developer",
                        "--status-proposal", "SUBMITTED", "--summary", "checkout implemented",
                        "--output", "src/checkout.py", "--scope-touched", "src/checkout.py"]
    _every_shell_gate_allows(repo, "python scripts/harness.py " + " ".join(submit_arguments))
    submitted = _entry_point(repo, *submit_arguments)
    assert submitted.returncode == 0, submitted.stdout + submitted.stderr
    assert "TSK-0001 -> SUBMITTED" in submitted.stdout, submitted.stdout

    cached = [os.path.join(base, name)
              for base, _dirs, files in os.walk(os.path.join(str(repo), ".claude"))
              for name in files if name.endswith((".pyc", ".pyo"))]
    assert not cached, cached


def test_a_root_item_no_longer_leaves_its_initial_status_from_a_roles_command_line(tmp_path):
    """The acceptance run for the transition gate, as real hook processes in a real project.

    Four measurements, in the order a session meets them:

      1. `transition PR-0001 APPROVED` with no approval: every shell gate ALLOWS the command line
         (so the refusal is the kernel's, which is the point -- a gate cannot see what a command
         line does not reveal), and the kernel refuses it naming the kind, the item and the
         revision.
      2. with a valid approval: allowed. WHICH edge that is measured on is not free. A mint WALKS
         the edge it commits, so `scope` + a PR still in DRAFT is a state that cannot exist -- one
         second after the scope APR is minted the item is APPROVED and the AUTOMATON answers that
         command, not the approval check. A `delivery` approval minted while the item is still
         DRAFT has no status effect (its source is APPROVED), so it is the one shape that holds a
         valid approval for an unwalked edge, and `transition PR-0001 IN_DELIVERY` is then rc 0.
      3. revoked: the same command, refused. (EXPIRED is unreachable for these kinds by
         construction -- spec II.2 time-boxes only routine/analysis/push, and
         `create_pending_request` refuses an expiry on the rest;
         `test_an_expiring_approval_kind_cannot_even_be_created_for_a_gated_edge` pins that.)
      4. an out-of-band edit of a field the approval hashes: refused, because the manifest hash is
         recomputed from the item's CURRENT content.
    """
    repo, _created = _project_the_installers_produce(tmp_path / "gate")
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    state = ProjectState(os.path.join(str(repo), "project_memory"))

    assert _entry_point(repo, "capture", "PR", body=json.dumps(PR_BODY)).returncode == 0
    _every_shell_gate_allows(repo, "python scripts/harness.py request-approval scope PR-0001")
    _every_shell_gate_allows(repo, "python scripts/harness.py transition PR-0001 APPROVED")
    refused = _entry_point(repo, "transition", "PR-0001", "APPROVED")
    assert refused.returncode == 1, refused.stdout + refused.stderr
    assert "scope approval" in refused.stderr and "PR-0001" in refused.stderr, refused.stderr
    assert state.read_item("PR-0001")["status"] == "DRAFT"

    _mint_in_project(repo, "delivery", "PR-0001")
    assert state.read_item("PR-0001")["status"] == "DRAFT"      # its source is APPROVED, not DRAFT
    _mint_in_project(repo, "scope", "PR-0001")
    assert state.read_item("PR-0001")["status"] == "APPROVED"   # the mint walked that edge itself
    allowed = _entry_point(repo, "transition", "PR-0001", "IN_DELIVERY")
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr
    assert "PR-0001 -> IN_DELIVERY" in allowed.stdout, allowed.stdout

    # ... and the same edge on a second item, once its approval is revoked
    assert _entry_point(repo, "capture", "PR", body=json.dumps(
        dict(PR_BODY, title="Second slice"))).returncode == 0
    _mint_in_project(repo, "delivery", "PR-0002")
    _mint_in_project(repo, "scope", "PR-0002")
    from kernel import approvals
    revoked_apr = next(
        state._read_yaml(os.path.join(state.root, "approvals", name))
        for name in sorted(os.listdir(os.path.join(state.root, "approvals")))
        if name.startswith("APR-") and name.endswith(".yaml")
        and state._read_yaml(os.path.join(state.root, "approvals", name)).get("item") == "PR-0002"
        and state._read_yaml(os.path.join(state.root, "approvals", name)).get("kind") == "delivery")
    approvals.revoke(state, revoked_apr["id"])
    withdrawn = _entry_point(repo, "transition", "PR-0002", "IN_DELIVERY")
    assert withdrawn.returncode == 1, withdrawn.stdout + withdrawn.stderr
    assert "REVOKED" in withdrawn.stderr or "revoked" in withdrawn.stderr, withdrawn.stderr

    # ... and on a third, once a field the delivery manifest hashes is edited past the kernel
    assert _entry_point(repo, "capture", "PR", body=json.dumps(
        dict(PR_BODY, title="Third slice"))).returncode == 0
    _mint_in_project(repo, "delivery", "PR-0003")
    _mint_in_project(repo, "scope", "PR-0003")
    path = state.active_path("PR-0003")
    item = state._read_yaml(path)
    item["risks"] = ["a risk nobody approved"]
    state._write_yaml_atomic(path, item)
    edited = _entry_point(repo, "transition", "PR-0003", "IN_DELIVERY")
    assert edited.returncode == 1, edited.stdout + edited.stderr
    assert "out-of-band" in edited.stderr, edited.stderr
    assert state.read_item("PR-0003")["status"] == "APPROVED"


def test_the_shell_gate_reader_sees_a_gate_registered_on_a_wider_matcher():
    """`_shell_gates_of` decides which gates "every shell gate allows it" is a claim about.

    It compared the matcher as a STRING (`== "Bash|PowerShell"`), so a hook registered on
    `Bash|PowerShell|Edit|Write|MultiEdit` was invisible although the provider fires it on every
    Bash call -- the office kit's `gate_filing.py` is exactly that, and the reader saw 5 of 6.
    Measured against every SHIPPED settings.json rather than a fixture, because the divergence is
    a fact about what the kits register: for each kit, the reader must return every hook whose
    matcher CONTAINS `Bash`, and the string comparison is what this test refuses.
    """
    for kit in KITS:
        with open(os.path.join(ROOT, "team-kits", kit, "settings", "settings.json"),
                  encoding="utf-8") as handle:
            settings = json.load(handle)
        expected = sorted({
            os.path.basename(entry["command"].split()[-1].strip('"'))
            for group in settings["hooks"]["PreToolUse"]
            if "Bash" in (group.get("matcher") or "").split("|")
            for entry in group["hooks"]})
        wider = sorted({
            os.path.basename(entry["command"].split()[-1].strip('"'))
            for group in settings["hooks"]["PreToolUse"]
            if "Bash" in (group.get("matcher") or "").split("|")
            and (group.get("matcher") or "") != "Bash|PowerShell"
            for entry in group["hooks"]})
        seen = sorted(set(_shell_gates_of_settings(settings)))
        assert seen == expected, "%s: reader saw %s, the provider fires %s" % (kit, seen, expected)
        if wider:
            assert set(wider) <= set(seen), (
                "%s registers %s on a matcher WIDER than `Bash|PowerShell` and the reader loses "
                "it -- which is how the office kit was measured at 5 shell gates instead of 6"
                % (kit, wider))


# ---------------- guard_pm_scope: production code is a LANGUAGE, not a directory ----------------
PM_CODE_PATHS = [
    # the two the directory list already caught
    "pay.py", "src/index.html",
    # ...and the ones it did not, measured rc 0 before this: an ordinary project layout that is
    # not called `src`, a nested one, a script directory, and a case the list could not fold
    "services/pay.py", "modules/pay.py", "core/pay.go", "scripts/deploy.py",
    "deep/nested/dir/util.ts", "pkg/handler/main.rs", "Ui/Widget.vue",
]
PM_UPKEEP_PATHS = [
    "docs/architecture.md", "docs/adr/0001-choice.md", "docs/examples/snippet.py",
    "plans/roadmap.md", "project_memory/staging/TSK-0001/proposal.md",
    "README.md", "CHANGELOG.md", ".gitignore", "pyproject.toml", "package.json",
    "docker-compose.yml", ".claude/agents/backend-developer.md", "Makefile", ".env.example",
]


def _pm_write(repo, rel):
    return {"tool_name": "Write", "cwd": str(repo),
            "tool_input": {"file_path": os.path.join(str(repo), *rel.split("/")),
                           "content": "x"}}


@pytest.mark.parametrize("rel", PM_CODE_PATHS)
def test_guard_pm_scope_blocks_code_by_language_not_by_directory(tmp_path, rel):
    """The PM writes no production code, and what makes a file production code is the LANGUAGE
    it is written in -- at any depth, outside the PM's own areas.

    Measured as real hook processes before this: `pay.py` and `src/index.html` were refused while
    `services/pay.py`, `modules/pay.py`, `core/pay.go`, `scripts/deploy.py`,
    `deep/nested/dir/util.ts` and `Ui/Widget.vue` all passed -- the guard decided on a list of
    top-level directory names plus root files, so every layout not called `src` was unguarded and
    `Ui` was a second spelling of a name that was in the list.
    """
    result = run_hook_process("guard_pm_scope.py", _pm_write(tmp_path, rel), tmp_path)
    assert result.returncode == 2, (rel, result.stderr)
    assert "production code" in result.stderr


@pytest.mark.parametrize("rel", PM_UPKEEP_PATHS)
def test_guard_pm_scope_leaves_ordinary_pm_upkeep_alone(tmp_path, rel):
    """THE COUNTER-BATTERY, and the reason the widening above is affordable. A guard that lamed
    the role it leads would be a worse defect than the one it closes, so the ordinary writes a PM
    really makes are measured too: documentation at any depth (including a code SNIPPET under
    docs/), plans, its own staging area, root configuration and the specialist frontmatter it
    maintains."""
    result = run_hook_process("guard_pm_scope.py", _pm_write(tmp_path, rel), tmp_path)
    assert result.returncode == 0, (rel, result.stderr)


def test_a_leading_dot_directory_keeps_its_name(tmp_path):
    """`lstrip("./")` strips a character SET, not a prefix: `.claude/hooks/x.py` arrived inside
    this guard as `claude/hooks/x.py`.

    Two consequences, both measured as real hook processes and both closed here. `ALLOW_TOP`'s
    `.claude` entry was UNREACHABLE, so once the rule above started deciding on the extension the
    guard refused the one directory its own message promises the lead may write ("You may write
    ./.claude/**"); `guard_harness_selfmod` is the guard that owns `.claude/hooks/**` and is
    registered on the same matcher — measured here, so the allow is a handover and not a hole. And
    the path in the refusal was not the path the role wrote, which is the first thing a reader
    checks.
    """
    allowed = run_hook_process("guard_pm_scope.py", _pm_write(tmp_path, ".claude/hooks/x.py"),
                               tmp_path)
    assert allowed.returncode == 0, allowed.stderr
    owner = run_hook_process("guard_harness_selfmod.py",
                             _pm_write(tmp_path, ".claude/hooks/x.py"), tmp_path)
    assert owner.returncode == 2 and "ENFORCEMENT LAYER" in owner.stderr, owner.stderr

    refused = run_hook_process("guard_pm_scope.py", _pm_write(tmp_path, ".config/deploy.py"),
                               tmp_path)
    assert refused.returncode == 2
    assert "'.config/deploy.py'" in refused.stderr, refused.stderr


@pytest.mark.parametrize("rel", ["services/pay.py", "src/index.html"])
def test_guard_pm_scope_still_ignores_subagents(tmp_path, rel):
    """`agent_id` present means a SUBAGENT, which `gate_write_scope` scopes against its task. This
    guard is the lead's alone, and the widening must not change that."""
    payload = dict(_pm_write(tmp_path, rel), agent_id="agent-1")
    assert run_hook_process("guard_pm_scope.py", payload, tmp_path).returncode == 0


# --------- every kit's LEAD meets the same two write guards (parity matrix rows 3 and 6) ---------
def _lead_registered_write_hooks(kit_dir):
    """{hook filename} — the hooks a shipped `settings.json` starts on a WRITE tool call.

    `settings.json` ONLY, and that is the definition rather than a shortcut: those registrations
    fire for the main agent as well as for every subagent, while an agent's own frontmatter
    `hooks:` block fires for that subagent alone. The party under test here is the LEAD, so a
    frontmatter registration is not its protection and counting one would report a guard the lead
    never meets (`guard_guidelines` is exactly that case).

    Read with the kernel's own `report._wired_hooks`, so "this command starts that file" has one
    definition in the repo: it drops a non-`command` type, a missing file, a mere mention and a
    swallowed exit code, and it KEEPS the matcher, which is judged here against the tool.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import report
    settings = os.path.join(kit_dir, "settings", "settings.json")
    hooks_dir = os.path.join(kit_dir, "hooks")
    if not os.path.isfile(settings):
        return set()
    staged = tempfile.mkdtemp(prefix="lead-wiring-")
    try:
        claude = os.path.join(staged, ".claude")
        shutil.copytree(hooks_dir, os.path.join(claude, "hooks"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(settings, os.path.join(claude, "settings.json"))
        started = set()
        for name, events in report._wired_hooks(staged).items():
            # `_gate.py` is the DISPATCHER: it appears in every command because it is the
            # executable, and the hook is its argument. Running it here with no argv would measure
            # the dispatcher's own error path instead of a rule.
            if name.startswith("_"):
                continue
            for event, matchers in events.items():
                if not event.startswith("PreToolUse"):
                    continue
                for matcher in matchers:
                    tokens = {t.strip() for t in str(matcher or "*").split("|")}
                    if matcher in (None, "", "*") or tokens & {"Write"}:
                        started.add(name)
        return started
    finally:
        shutil.rmtree(staged, ignore_errors=True)


# Each pair differs in exactly ONE property — the property the rule is about. The refused member
# alone would be satisfied by any hook refusing for any reason (a fixture measuring itself); the
# allowed member is what makes the pair a measurement of the deciding term.
LEAD_WRITE_PAIRS = [
    # a file in a programming language, in an area no kit hands its lead — vs the same name in a
    # language that is not one. The deciding term: the LANGUAGE.
    ("tools/extract.py", "tools/extract.md"),
    # `implementation_summary.*` — vs a root document every kit allows. Term: the NAME.
    ("IMPLEMENTATION_SUMMARY.md", "README.md"),
    # the `*_report.md` dump — vs the same stem without the suffix. Term: the SUFFIX.
    ("docs/audit_2026_report.md", "docs/audit_2026_notes.md"),
    # an item's status as a markdown file — vs prose that merely mentions the type. Term: the ID.
    ("docs/PROC-0001_status.md", "docs/proc-conventions.md"),
    # `backend_result_*` handed over as a file — vs the same note without the pattern. Under
    # `docs/`, deliberately: as of 2026-08-01 the name rule stands down inside a DOCUMENT TRAY
    # (`guard_no_adhoc.DOCUMENT_TRAYS`), so the `outbox/` spelling this probe used to carry would
    # now be measuring the exemption instead of the rule. The tray side is measured where it
    # belongs, in the office false-alarm corpus below.
    ("docs/backend_result_x.md", "docs/backend_notes_x.md"),
]


@pytest.mark.parametrize("kit", KITS)
@pytest.mark.parametrize("refused,allowed", LEAD_WRITE_PAIRS)
def test_every_kit_lead_is_refused_the_same_two_classes_of_write(tmp_path, kit, refused, allowed):
    """Parity rows 3 and 6, as behaviour rather than as an inventory of hook files.

    Measured 2026-08-01 before this, as real hook processes against a scaffolded project outside
    the repo: an office-lead `Write` of `tools/extract.py` came back rc 0 from ALL FOUR hooks the
    office `settings.json` starts on a write, and so did every one of the four ad-hoc names —
    while the identical payload in dev was refused with rc 2 by `guard_pm_scope` resp.
    `guard_no_adhoc`. The office kit shipped neither file, and the assumption behind that ("office
    writes no product code") is contradicted by its own constitution, which gives the
    office-developer `tools/**` and `dashboards/**` as sole ownership.

    THE SUBJECT IS DERIVED — every shipped kit — so a fourth kit is covered the day it ships, and
    the verdict is taken from the hooks the kit's OWN `settings.json` starts, never from a list
    here. No hook name is asserted: what the parity row claims is that the write is refused, and
    naming the refuser would make the test fail for a kit that closes the same hole differently.
    """
    kit_dir = os.path.join(ROOT, "team-kits", kit)
    hooks_dir = os.path.join(kit_dir, "hooks")
    started = sorted(_lead_registered_write_hooks(kit_dir))
    assert started, "%s: settings.json starts no hook at all on a Write" % kit

    def verdicts(rel):
        return {name: run_hook_process(name, _pm_write(tmp_path, rel), tmp_path,
                                       hooks_dir=hooks_dir).returncode
                for name in started}

    blocked = {name: rc for name, rc in verdicts(refused).items() if rc == 2}
    assert blocked, (
        "%s: the lead writing %r passes every hook settings.json starts (%s) — parity rows 3/6 "
        "are open in this kit" % (kit, refused, ", ".join(started)))
    passed = {name: rc for name, rc in verdicts(allowed).items() if rc != 0}
    assert not passed, (
        "%s: %r is refused too (%s), so the refusal of %r does not track the property the rule is "
        "about — the probe is measuring the fixture" % (kit, allowed, passed, refused))


# THE FALSE-ALARM CORPUS — a probe input, deliberately NOT a rule and claiming no completeness.
# One entry per row of the office constitution's ownership table (§6) plus the artifacts §2 names,
# spelled the way the kit's own scripts spell them (`euer_report.py` writes
# `reports/euer_<year>_Q<q>.md` and points at `_notes.md` beside it). The measurement it supports
# is the one the two new registrations have to survive: a guard that lamed the office roles would
# be a worse defect than the hole it closes.
OFFICE_OWN_WRITE_PATHS = [
    "project_memory/procedures/active/PROC-0001.yaml",
    "project_memory/inbox/active/FR-0001.yaml",
    "project_memory/changes/active/CR-0001.yaml",
    "project_memory/bugs/active/BUG-0001.yaml",
    "project_memory/decisions/active/DEC-0001.yaml",
    "project_memory/business_profile.yaml",
    "project_memory/product/masterplan.md",
    "project_memory/project_config.yaml",
    "project_memory/filing_plan.yaml",
    "project_memory/master_data.yaml",
    "project_memory/product_catalog.yaml",
    "project_memory/content_guidelines.yaml",
    "project_memory/compliance_register.yaml",
    "project_memory/marketing_plan.yaml",
    "ledger/2026.csv",
    "reports/euer_2026_Q2.md",
    "reports/euer_2026_Q2_notes.md",
    "docs/verfahrensdokumentation.md",
    "dashboards/sales.html",
    "outbox/marketing-planner/post-draft.md",
    # ...the document-tray writes the name rule refused until 2026-08-01, measured rc 2 each: a
    # bookkeeper's quarterly draft, a summary addressed to the Steuerberater, and an INCOMING
    # scanned invoice whose supplier happened to name it `..._report.md`. None of them is a
    # substitute for a typed item, which is the only thing that rule is about.
    "outbox/bookkeeper/2026-Q2_report.md",
    "outbox/office-manager/steuerberater_summary.md",
    "archive/2026/Rechnungen/2026-01-15_ACME_report.md",
    "inbox/2026-02-01_ACME_summary.md",
    # ...and the two the kit is SUPPOSED to refuse, kept in the corpus so the reason is asserted
    # rather than assumed. `tools/**` is the office-DEVELOPER's, and `guard_pm_scope` exits on any
    # payload carrying an `agent_id`, so what it refuses here is the LEAD reaching into it. The
    # root constitution is `guard_harness_selfmod`'s in every kit; `guard_no_adhoc` arrives at the
    # same verdict through its "no loose markdown at the repo root" rule.
    "tools/sales_extract.py",
    "AGENTS.md",
]
OFFICE_INTENDED_REFUSALS = {
    ("tools/sales_extract.py", "guard_pm_scope.py"),
    ("AGENTS.md", "guard_no_adhoc.py"),
    ("AGENTS.md", "guard_harness_selfmod.py"),
    # `gate_filing`'s own rule, not a false alarm and not this package's business: a document
    # landing under `archive/` while `filing_plan.yaml` lists no rules is refused BY DESIGN
    # (office constitution §2.5, "blocks filing at all while the plan has no rules"), and the
    # corpus repo deliberately has no plan. The path is in the corpus for `guard_no_adhoc`, which
    # used to refuse it on its NAME — that refusal is gone and this one is not.
    ("archive/2026/Rechnungen/2026-01-15_ACME_report.md", "gate_filing.py"),
}


def test_the_two_new_office_guards_do_not_refuse_the_office_roles_own_work(tmp_path):
    """The false-alarm direction of parity rows 3 and 6, measured before the copies were trusted.

    Every hook the office `settings.json` starts on a write is run against the corpus above. The
    only refusals allowed are the two named there WITH their reason; anything else means a guard
    written for a code repo is refusing a document workspace's ordinary work, and that is the
    defect this measurement exists to catch — not a footnote in a report.

    Measured 2026-08-01 over 22 own paths: `guard_pm_scope` refused exactly `tools/sales_extract.py`
    and `guard_no_adhoc` exactly `AGENTS.md`, which the kit already refused through
    `guard_harness_selfmod` before either copy existed.

    THE FIXTURE CARRIES THE KIT'S TRAY RECORD, written by the same module a scaffold runs. The
    document-tray half of this corpus is meaningless without it — an exemption that is a fact
    about the installed kit has to be installed before it can be measured.
    """
    kit_dir = os.path.join(ROOT, "team-kits", "office-team")
    started = sorted(_lead_registered_write_hooks(kit_dir))
    assert {"guard_pm_scope.py", "guard_no_adhoc.py"} <= set(started), started
    trays = load_kit_module("kernel_trays_for_office_corpus",
                            os.path.join(ROOT, "team-kits", "kernel", "trays.py"))
    os.makedirs(str(tmp_path / ".claude" / "hooks"), exist_ok=True)
    shutil.copyfile(trays.record_path(kit_dir),
                    str(tmp_path / ".claude" / "hooks" / trays.TRAYS_FILE))
    assert trays.document_trays(kit_dir) == ["archive", "inbox", "outbox"]

    surprises = []
    for rel in OFFICE_OWN_WRITE_PATHS:
        # A path under the STATE DIRECTORY is refused in every kit by §0's write-lock — the kernel
        # is its only writer — so a refusal there is the constitution, not a false alarm. Stated as
        # the LOCATION rather than as a hook name: which gate enforces §0 is not what makes the
        # refusal correct, and the state half is measured separately below.
        if rel.startswith("project_memory/"):
            continue
        for name in started:
            rc = run_hook_process(name, _pm_write(tmp_path, rel), tmp_path,
                                  hooks_dir=os.path.join(kit_dir, "hooks")).returncode
            if rc == 2 and (rel, name) not in OFFICE_INTENDED_REFUSALS:
                surprises.append("%s refuses %s" % (name, rel))
    assert not surprises, (
        "these hooks refuse work the office constitution hands a role: %s" % "; ".join(surprises))
    for rel in [p for p in OFFICE_OWN_WRITE_PATHS if p.startswith("project_memory/")]:
        assert any(run_hook_process(name, _pm_write(tmp_path, rel), tmp_path,
                                    hooks_dir=os.path.join(kit_dir, "hooks")).returncode == 2
                   for name in started), rel
    # ...and the two intended refusals really happen — an exception list nothing exercises would
    # keep this test green over a guard that stopped guarding.
    for rel, name in sorted(OFFICE_INTENDED_REFUSALS):
        assert run_hook_process(name, _pm_write(tmp_path, rel), tmp_path,
                                hooks_dir=os.path.join(kit_dir, "hooks")).returncode == 2, (rel, name)


def _trays_shipped_by(kit):
    """The tray directories a kit ships, re-derived HERE and not asked of the code under test.

    A tray is a top-level directory of `templates/repo` that the kit ships EMPTY except for a
    folder-guide seed: a place to be filled at RUNTIME by documents arriving from outside or
    drafts handed to a human, as opposed to `scripts/` (shipped full of code) or `.claude/`
    (shipped full of configuration). `kernel/trays.py` states the same property in the code the
    scaffold runs; this is the second reader that makes it a measurement rather than a tautology.
    """
    template = os.path.join(ROOT, "team-kits", kit, "templates", "repo")
    trays = set()
    for name in sorted(os.listdir(template)):
        directory = os.path.join(template, name)
        if not os.path.isdir(directory) or name.startswith("."):
            continue
        files = [f for _d, _s, fs in os.walk(directory) for f in fs]
        if files and all(os.path.splitext(f)[0].lower() == "readme" for f in files):
            trays.add(name.lower())
    return trays


@pytest.mark.parametrize("kit", KITS)
def test_the_document_trays_are_the_directories_the_kits_ship_as_trays(tmp_path, kit):
    """The SHIPPED record, pinned against the template tree it is derived from.

    THE SUBJECT MOVED HERE FOR A MEASURED REASON. The exemption used to be a tuple in
    `guard_no_adhoc`, and that hook is byte-identical across all three kits — so the tray names
    exempted `archive/`, `outbox/` and `inbox/` in kits that ship no tray, where such a directory
    is created by the very `Write` that drops a file into it. Measured 2026-08-01 in a dev
    project, LEAD write, against every hook the dev settings.json starts on `Write`:
    `archive/implementation_summary.md`, `outbox/backend_result_x.md`,
    `inbox/delegation_plan.md` and `archive/notes/frontend_result_2.md` came back ALLOWED by all
    of them; all four were rc 2 before the exemption existed. Identical in research.

    Three assertions, because the record has three jobs: it must MATCH the template tree, it must
    be SHIPPED (a file the scaffold copies, prunes and rolls back like any other hook file, and
    which `hook_bundle_hash` therefore measures), and it must READ BACK as what a kernel-less hook
    will act on.
    """
    trays = load_kit_module("kernel_trays_under_test",
                            os.path.join(ROOT, "team-kits", "kernel", "trays.py"))
    kit_dir = os.path.join(ROOT, "team-kits", kit)
    shipped = trays.document_trays(kit_dir)
    assert set(shipped) == _trays_shipped_by(kit), (
        "%s: the module answers %s and the template tree ships %s as trays"
        % (kit, shipped, sorted(_trays_shipped_by(kit))))

    record = trays.record_path(kit_dir)
    assert os.path.isfile(record), (
        "%s ships no hooks/document_trays.txt — run `python tools/bump_kit_version.py`, which "
        "regenerates it" % kit)
    with open(record, encoding="utf-8") as handle:
        assert handle.read().split() == shipped, (
            "%s's shipped record is stale against its own template tree — run "
            "`python tools/bump_kit_version.py`" % kit)

    guard = load_kit_module("guard_no_adhoc_trays_%s" % kit,
                            os.path.join(ROOT, "team-kits", kit, "hooks", "guard_no_adhoc.py"))
    installed = tmp_path / "installed"
    os.makedirs(str(installed / ".claude" / "hooks"))
    shutil.copyfile(record, str(installed / ".claude" / "hooks" / trays.TRAYS_FILE))
    assert guard.document_trays(str(installed)) == frozenset(shipped)


TRAY_NAME_BATTERY = [
    "inbox", "outbox", "archive", "Archive", "  inbox  ",       # ordinary names
    ".claude", ".git", ".", "..",                               # hidden / relative
    "project_memory", "PROJECT_MEMORY",                         # the state directory
    "docs/inner", "docs\\inner", "/tmp", "C:\\Windows", "",      # not one segment
]


def _function_source(path, name):
    """The AST of one function, with its docstring dropped and its position stripped.

    Position and docstring are exactly what the two copies may differ in — they sit in different
    files and say so — while everything else is the definition.
    """
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    node = next(n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == name)
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    stripped = ast.Module(body=body, type_ignores=[])
    return ast.dump(ast.fix_missing_locations(stripped))


def test_the_two_readers_of_a_tray_name_agree():
    """THE SAME CODE, not the same answers on the cases somebody thought of.

    `is_tray_name` exists twice — in `kernel.trays` and in every kit's `guard_no_adhoc`, which
    must keep guarding with no kernel to import. The two halves drifted the day they were written,
    in the direction that matters: the stamper skipped hidden directories while the reader dropped
    only names carrying a separator, so a record saying `.claude` exempted the enforcement layer
    (`.claude/x_report.md` rc 0) and one saying `project_memory` exempted the state directory
    (`project_memory/staging/T-1/x_summary.md` rc 0) — both measured 2026-08-01.

    A battery of counter-examples stood here first and was the weaker instrument: it can only ever
    say "these cases agree", and an independent fuzz over 300k inputs found no case it added. The
    bodies are compared as AST instead, docstrings and positions removed — that is the property,
    and it covers the input nobody listed.

    THE BATTERY STAYS FOR THE OTHER QUESTION, which the AST cannot answer: whether the shared
    definition still MEANS what the rule needs. Identical code that returns True for `.claude`
    would pass an equality check and open the enforcement layer.
    """
    trays_path = os.path.join(ROOT, "team-kits", "kernel", "trays.py")
    canonical = _function_source(trays_path, "is_tray_name")
    for kit in KITS:
        hook = os.path.join(ROOT, "team-kits", kit, "hooks", "guard_no_adhoc.py")
        assert _function_source(hook, "is_tray_name") == canonical, (
            "%s's guard_no_adhoc.is_tray_name is no longer the same code as kernel.trays's — one "
            "of the two copies was edited alone" % kit)

    trays = load_kit_module("kernel_trays_names", trays_path)
    assert [name for name in TRAY_NAME_BATTERY if trays.is_tray_name(name)] == [
        "inbox", "outbox", "archive", "Archive", "  inbox  "], (
        "the shared definition changed meaning: a tray name is ONE ordinary top-level directory "
        "— not the enforcement layer, not the state directory, not a path")


def _cygpath(path):
    try:
        result = subprocess.run(["cygpath", "-u", str(path)], capture_output=True, text=True,
                                timeout=60)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except OSError:
        pass
    return None


# How a path might have to be spelled for the `bash` that will actually RUN. Tried in order and
# the first one that WORKS is kept; nothing here assumes which of them it will be.
_BASH_SPELLINGS = (str, lambda path: str(path).replace("\\", "/"), _cygpath)


def _bash_spelling(tmp_path):
    """The path transform this machine's `bash` accepts — or None, and then the branch is skipped.

    ASKED, NEVER ASSUMED, and asking the wrong thing is what made this helper useless for a round.
    `shutil.which("bash")` answered `C:\\Program Files\\Git\\usr\\bin\\bash.EXE` while the process
    that actually started was WSL's (`ls /tmp` → `snap-private-tmp`), which cannot see a Windows
    path at all — and `cygpath` on the same PATH is Git Bash's, so it produced `/tmp/…` for a
    bash whose `/tmp` is somewhere else entirely. Probe and run then used different spellings: the
    probe said "bash works", the scaffold answered `Refusing non-absolute source path`, and the
    branch was skipped here and would have been red anywhere else.

    So the probe is the SAME operation the test performs — execute a script in this directory with
    `$HOME` pointing into it — and whichever spelling survives that is the one the run uses.
    """
    if not shutil.which("bash"):
        return None
    probe = os.path.join(str(tmp_path), "bash-probe.sh")
    write(probe, "#!/usr/bin/env bash\ncd \"$HOME\" || exit 3\necho ok\n")
    for spelling in _BASH_SPELLINGS:
        script, home = spelling(probe), spelling(tmp_path)
        if not script or not home:
            continue
        try:
            result = subprocess.run(["bash", script], capture_output=True, text=True, timeout=60,
                                    env=dict(os.environ, HOME=home))
        except OSError:
            continue
        if result.returncode == 0 and "ok" in result.stdout:
            return spelling
    return None


@pytest.mark.parametrize("kit,expected", [("office-team", ["archive", "inbox", "outbox"]),
                                          ("dev-team", [])])
@pytest.mark.parametrize("launcher", ["sh", "ps1"])
def test_the_shipped_scaffold_records_the_trays_of_the_kit_it_installs(tmp_path, kit, expected,
                                                                      launcher):
    """The INSTALLATION, not the module: a record no scaffold delivers exempts nothing.

    The record is an ordinary shipped hook-directory file, so no scaffold step was added for it —
    which is the point of putting it there. What this measures is that the generic
    copy/prune/rollback machinery really carries it, on BOTH launchers whenever the interpreter is
    reachable. That last part is the one thing `prune_transient`'s own comment says went wrong the
    last time a scaffold gained a step: "the shell twins did, and only the Windows one was ever
    executed by a test".

    Two kits, because the interesting record is the EMPTY one: a kit that ships no tray installs
    an empty file, not "no file" and not the previous kit's list. The kit-switch case is the
    second run below — office trays must not survive a dev install, or the exemption outlives the
    kit that justified it.
    """
    if launcher == "ps1" and os.name != "nt":
        pytest.skip("no PowerShell here")
    spelling = _bash_spelling(tmp_path) if launcher == "sh" else None
    if launcher == "sh" and spelling is None:
        pytest.skip("no bash that can run a file under this tmp_path")
    pytest.importorskip("yaml")

    home = tmp_path / "home"
    staging = home / ".claude" / "team-kits"
    shutil.copytree(os.path.join(ROOT, "team-kits"), str(staging),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    repo = tmp_path / "repo"

    def run(team):
        source = os.path.join(str(staging), team, "templates", "project_memory",
                              "project_config.yaml")
        os.makedirs(str(repo / "project_memory"), exist_ok=True)
        preset = "core" if team == "office-team" else "solo"
        with open(source, encoding="utf-8") as handle:
            config = re.sub(r"(?m)^(\s*preset:\s*).*$", r"\g<1>" + preset, handle.read())
        write(str(repo / "project_memory" / "project_config.yaml"), config)
        environment = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
        if launcher == "sh":
            # `_posix` for BOTH, and the probe uses it too: the scaffold resolves its staging out
            # of `$HOME`, and a `C:/…` spelling made it refuse with "Refusing non-absolute source
            # path" — a red that has nothing to do with what this test asks.
            environment["HOME"] = spelling(home)
            command = ["bash", spelling(os.path.join(str(staging), "scaffold_team.sh")), team]
        else:
            command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                       os.path.join(str(staging), "scaffold_team.ps1"), "-Team", team]
        result = subprocess.run(command, cwd=str(repo), capture_output=True, text=True,
                                timeout=600, env=environment)
        assert result.returncode == 0, result.stdout + result.stderr
        record = repo / ".claude" / "hooks" / "document_trays.txt"
        assert record.is_file(), "%s/%s installed no tray record" % (launcher, team)
        return record.read_text(encoding="utf-8").split()

    assert run(kit) == expected
    # ...and a SECOND kit over the first rewrites it rather than inheriting it
    other = "dev-team" if kit == "office-team" else "office-team"
    assert run(other) == ([] if other == "dev-team" else ["archive", "inbox", "outbox"])


@pytest.mark.parametrize("kit", KITS)
def test_a_kit_that_ships_no_tray_gets_no_exemption(tmp_path, kit):
    """F1 in one sentence: the exemption is a fact about the INSTALLED KIT, not about the hook.

    Every kit's own hook is run as a real process against a project carrying that kit's recorded
    tray list, over the four names the tuple-in-the-hook version waved through. A kit that ships
    trays must allow them; a kit that ships none must refuse all four — the state before this
    package, restored for the kits it never applied to.

    The parent-directory case rides along, because `lstrip("./")` strips a character SET: a write
    to `../archive/x_report.md` — a file OUTSIDE this repo — arrived inside the guard as
    `archive/x_report.md` and fell into the exemption. It is a `Write` no kit's tray covers.
    """
    trays = load_kit_module("kernel_trays_for_%s" % kit,
                            os.path.join(ROOT, "team-kits", "kernel", "trays.py"))
    kit_dir = os.path.join(ROOT, "team-kits", kit)
    repo = tmp_path / kit
    os.makedirs(str(repo / "project_memory"))
    os.makedirs(str(repo / ".claude" / "hooks"))
    shutil.copyfile(trays.record_path(kit_dir),
                    str(repo / ".claude" / "hooks" / trays.TRAYS_FILE))
    shipped = trays.document_trays(kit_dir)
    hooks_dir = os.path.join(kit_dir, "hooks")

    probes = ["archive/implementation_summary.md", "outbox/backend_result_x.md",
              "inbox/delegation_plan.md", "archive/notes/frontend_result_2.md"]
    for rel in probes:
        expected = 0 if rel.split("/")[0] in shipped else 2
        result = run_hook_process("guard_no_adhoc.py", _pm_write(repo, rel), repo,
                                  hooks_dir=hooks_dir)
        assert result.returncode == expected, (kit, rel, result.returncode, result.stderr)

    # a tray of the PARENT directory is not this repo's tray, in any kit
    outside = {"tool_name": "Write", "cwd": str(repo),
               "tool_input": {"file_path": os.path.join(str(tmp_path), "archive", "x_report.md"),
                              "content": "x"}}
    assert run_hook_process("guard_no_adhoc.py", outside, repo,
                            hooks_dir=hooks_dir).returncode == 2

    # ...and with NO record at all, no kit exempts anything (an installation from before this)
    os.remove(str(repo / ".claude" / "hooks" / trays.TRAYS_FILE))
    for rel in probes:
        assert run_hook_process("guard_no_adhoc.py", _pm_write(repo, rel), repo,
                                hooks_dir=hooks_dir).returncode == 2, (kit, rel)


# ---------------- guard_question_context R2: the comment's own example must fire ----------------
def _question(text, options):
    return {"tool_name": "AskUserQuestion",
            "tool_input": {"questions": [{"question": text, "header": "",
                                          "options": [{"label": o, "description": ""}
                                                      for o in options]}]}}


@pytest.mark.parametrize("text,options", [
    ("Postgres oder MySQL?", ["Postgres", "MySQL"]),
    ("Welche Datenbank?", ["PostgreSQL nutzen", "MongoDB nutzen"]),
    ("React oder Vue?", ["React", "Vue"]),
])
def test_the_two_word_technical_choice_the_comment_names_actually_warns(tmp_path, text, options):
    """R2's own comment says "`Postgres oder MySQL` cannot be anything but a technical choice",
    and the threshold under it was three distinct hits -- so the sentence the paragraph is built
    on measured SILENT. A comment claiming a protection the code does not build, in the guard
    whose subject is questions that point at something that is not there.

    Two is the smallest number that can be a CHOICE. It stays a WARNING (rc 0): the cost of a
    false alarm is a line of stderr the message itself tells the reader to ignore.
    """
    result = run_hook_process("guard_question_context.py", _question(text, options), tmp_path)
    assert result.returncode == 0, result.stderr
    assert "[team-kit note]" in result.stderr and "technical choices" in result.stderr


@pytest.mark.parametrize("text,options", [
    ("Sollen Kundinnen ihre Bestellhistorie sehen?", ["Ja", "Nein"]),
    ("Wo sollen die Daten liegen?", ["In Deutschland", "Beim guenstigsten Anbieter"]),
    ("Soll die App als Docker-Container ausgeliefert werden?", ["Ja", "Nein, nativ"]),
    ("Welches Preis-Schema?", ["Pro Nutzer", "Pauschal"]),
    ("Brauchen wir eine Migration der Altdaten?", ["Ja", "Nein"]),
])
def test_r2_stays_silent_on_product_questions(tmp_path, text, options):
    """THE COUNTER-BATTERY for the threshold change. Every one of these is a product question a PM
    is supposed to ask the user -- including three that mention exactly ONE technical word, which
    is the case the lower bound must not turn into noise."""
    result = run_hook_process("guard_question_context.py", _question(text, options), tmp_path)
    assert result.returncode == 0
    assert "technical choices" not in result.stderr, (text, result.stderr)


# ---------------- the packaging block, and the exit it did not have ----------------
_ARC_SVG = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>\n')


def test_the_packaging_block_has_an_exit_a_role_can_type(tmp_path):
    """`gate_packaging_decision` refuses every push and merge until some active ARC item states a
    resolved `packaging.method`. Its own docstring said the field "has to be writable through the
    kernel or the gate is a block with no exit" and then said it was — measured 2026-07-31 in a
    scaffolded project, it was not: no subcommand named freeze, `capture` refuses `ARC`
    (`REQUIRED_FIELDS`), and `gate_write_scope` refuses every tool write under the state directory.

    The same four steps as the Evidence producer's acceptance test, because either half alone
    proves nothing: a command line the gates refuse is no remedy, and a command line the gates
    allow but that writes nothing is no producer.

      * the merge, REFUSED, with the gate's own reason;
      * the freeze command line through EVERY `Bash|PowerShell` PreToolUse hook this project
        registered — read off its settings.json, so a gate added later is covered the day it ships;
      * the same line EXECUTED, with the body on stdin;
      * the same merge, ALLOWED.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    assert "freeze-architecture" in cli.build_parser()._subparsers._group_actions[0].choices

    repo, _created = _project_the_installers_produce(tmp_path / "scaffold")
    capture_root_item(repo)
    merge = "git merge feat/PR-0001-x"
    blocked = _run_project_hook(repo, "gate_packaging_decision.py", merge)
    assert blocked.returncode == 2, blocked.stdout + blocked.stderr
    assert "packaging/deployment decision is unmade" in blocked.stderr

    staged = os.path.join(str(repo), "project_memory", "staging", "PR-0001")
    os.makedirs(staged, exist_ok=True)
    write(os.path.join(staged, "ARC-0001.drawio.svg"), _ARC_SVG)
    body = json.dumps({"staging_key": "PR-0001", "arc_id": "ARC-0001", "title": "Deployment",
                       "scope": "whole system", "derives_from": ["PR-0001"],
                       "packaging": {"method": "docker"}})
    line = "%s freeze-architecture <<'EOF'\n%s\nEOF" % (cli.INVOCATION, body)
    for gate in _shell_gates_of(repo):
        seen = _run_project_hook(repo, gate, line)
        assert seen.returncode == 0, (
            "%s refuses the one command line that unblocks the packaging gate:\n%s"
            % (gate, seen.stderr))

    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTHONPATH", "PYTHONPYCACHEPREFIX", "PYTHONDONTWRITEBYTECODE")}
    ran = subprocess.run([sys.executable, os.path.join(*cli.ENTRY_POINT.split("/")),
                          "freeze-architecture"],
                         input=body, cwd=str(repo), capture_output=True, text=True,
                         env=env, timeout=120)
    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert "architecture/revisions/ARC-0001.r01.drawio.svg" in ran.stdout

    opened = _run_project_hook(repo, "gate_packaging_decision.py", merge)
    assert opened.returncode == 0, (
        "the merge is still refused after the architecture was frozen:\n%s" % opened.stderr)


# ---------------- a text that PRESENTS the surface must present all of it ----------------
_SURFACE_SPAN_MIN = 3
_SUBCOMMAND_SPAN_RX = re.compile(r"`([a-z][a-z0-9-]*)`")


def test_every_span_that_presents_the_command_surface_names_all_of_it():
    """A block that lists the entry point's subcommands is telling a role what EXISTS, and a role
    who reads such a list and does not find a command concludes it has none.

    That is not hypothetical: on 2026-07-31 three constitutions, two PM agent definitions, the
    README and three copies of `gate_write_scope`'s refusal all carried such a list, and six of
    them also said in so many words that "an `ARC` is FROZEN through the promotion path (II.6a),
    which has no command" — while `staging.freeze_architecture` was one subcommand away from
    existing. The reader would report an infrastructure gap instead of freezing.

    WHAT COUNTS AS SUCH A SPAN is measured, not guessed. Over the whole shipped corpus the
    distribution of "distinct subcommands named in code spans per block" is bimodal WITH A WIDE
    EMPTY BAND: the overwhelming majority name 0, 1 or 2, a handful name every member of the
    surface, and nothing lands in between. A threshold inside that band separates prose that
    MENTIONS a command from a text that LISTS them; 3 is its low edge, so a shrinking list cannot
    slip under it.

    THE ABSOLUTE COUNTS ARE DELIBERATELY NOT WRITTEN HERE, and that is a correction: an earlier
    version of this docstring quoted a span total and a histogram, and they were stale INSIDE the
    round that wrote them -- the comments this very round added moved the zero bucket by fifteen.
    A number nothing asserts drifts with every comment anyone writes. What the check needs is the
    BAND, and the assertions below are what measure it: every presenting span complete, and enough
    of them found to prove the reader still matches.

    The corpus is the same one its two sisters use (`_shipped_texts` split into blocks, plus the
    AST-folded refusal texts), because an asymmetry nobody wrote down is an enumeration wearing a
    different hat.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel import cli
    surface = set(cli.build_parser()._subparsers._group_actions[0].choices)

    spans = []
    for where, text in _shipped_texts():
        spans += [(where, block) for block in _markdown_blocks(text)]
    for path in _shipped_python_modules():
        where = os.path.relpath(path, ROOT).replace(os.sep, "/")
        spans += [(where, text) for text in _refusal_texts(path)]

    seen, offenders = 0, []
    for where, span in spans:
        named = {word for word in _SUBCOMMAND_SPAN_RX.findall(span) if word in surface}
        if len(named) < _SURFACE_SPAN_MIN:
            continue
        seen += 1
        missing = sorted(surface - named)
        if missing:
            offenders.append("%s: names %d, misses %s" % (where, len(named), ", ".join(missing)))
    assert not offenders, (
        "these blocks present the entry point's surface and leave commands out of it — either "
        "name them, or stop presenting a list and point at `--help`:\n%s" % "\n".join(offenders))
    # A FLOOR, because every assertion above is vacuously true over an empty set. Six spans were
    # measured; the floor is three, which is the number of kit constitutions -- each of those
    # really does present the surface in its §0, and a reader that finds fewer than one per kit has
    # stopped matching. It is deliberately not six: a document that stops presenting a list and
    # points at `--help` instead is the RIGHT change (that is what the refusal texts just did), and
    # a floor that forbade it would pin the enumeration this check exists to keep honest.
    assert seen >= 3, (
        "only %d surface-presenting span(s) found — the reader stopped matching rather than the "
        "documents stopping listing" % seen)


# ---------------- the kit checkers that had no caller ----------------
def test_a_kit_checker_that_declares_a_quality_stage_is_run_by_the_pipeline(tmp_path):
    """`report_lint.py` and `pii_scan.py` were written, documented and tested and then named by
    NOTHING — no hook, no settings.json, no CI file, no pre-commit config, no SKILL. A check with
    no caller is prose with a shebang.

    `quality.py` now DISCOVERS every sibling in `scripts/` that declares the pair
    (`QUALITY_STAGE`, `quality_stage()`), which is what a list here could not do: quality.py is
    byte-identical across the dev and research kits (the mirror rule), and only research ships
    `report_lint.py`.

    Measured both ways in one run — with the checker present its findings reach the report as a
    `warn`, and the same project without it is green and silent, which is what says the wiring is
    the checker's declaration rather than something quality.py knows.
    """
    research_scripts = os.path.join(ROOT, "team-kits", "research-team", "templates", "repo",
                                    "scripts")
    verdicts = {}
    for present in (False, True):
        work = tmp_path / ("with" if present else "without")
        os.makedirs(str(work / "reports"))
        write(str(work / "reports" / "final.md"),
              "The intervention proves the effect and improved outcomes dramatically.\n")
        subprocess.run(["git", "init", "-q"], cwd=str(work), capture_output=True, timeout=60)
        subprocess.run(["git", "add", "-A"], cwd=str(work), capture_output=True, timeout=60)
        if present:
            os.makedirs(str(work / "scripts"), exist_ok=True)
            shutil.copy(os.path.join(research_scripts, "report_lint.py"),
                        str(work / "scripts" / "report_lint.py"))
        verdicts[present] = run_quality_proc(str(work))

    assert verdicts[True].returncode == 0, verdicts[True].stdout
    assert "warn  research report lint" in verdicts[True].stdout, verdicts[True].stdout
    assert "causal claim without a hedge" in verdicts[True].stdout
    assert verdicts[False].returncode == 0
    assert "report lint" not in verdicts[False].stdout


def test_the_declared_stage_of_every_shipped_checker_is_callable():
    """The contract is two names, so a checker that declares one and not the other would be
    discovered and then silently skipped — which is the inert state this whole item is about.

    Derived over every script the kits ship, so a fourth checker is covered the day it declares
    itself.
    """
    for path in sorted(glob.glob(os.path.join(
            ROOT, "team-kits", "*", "templates", "repo", "scripts", "*.py"))):
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        if "QUALITY_STAGE" not in source or os.path.basename(path) == "quality.py":
            continue
        module = load_kit_module("checker_" + os.path.basename(path)[:-3], path)
        label, severity = module.QUALITY_STAGE
        assert isinstance(label, str) and label
        assert severity in ("warn", "fail"), (path, severity)
        assert callable(getattr(module, "quality_stage", None)), path
        rc, text = module.quality_stage()
        assert rc in (0, 1) and isinstance(text, str), path


# ---------------- which roles the guidelines guard is registered for ----------------
def _composes_kernel_dir(path, wanted):
    """Does this module BUILD the kernel's `wanted` state path out of a literal tuple?

    The same shape `test_the_hooks_that_name_a_typed_directory_spell_it_as_the_kernel_does` keys
    on, and for the same reason: a tuple of literals a module SPLATS into a `join(...)` is a path
    composition and there is nothing else it could be. Parsed from the AST — this is CODE being
    read, never a string search over a document.
    """
    with open(path, encoding="utf-8", errors="ignore") as handle:
        tree = ast.parse(handle.read(), filename=path)
    literals = {}
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Tuple)):
            continue
        parts = [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
        if len(parts) != len(node.value.elts):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                literals[target.id] = "/".join(str(p) for p in parts)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and _callee_name(node) == "join"):
            continue
        for argument in node.args:
            if (isinstance(argument, ast.Starred) and isinstance(argument.value, ast.Name)
                    and literals.get(argument.value.id) == wanted):
                return True
    return False


def _kits_with_an_invariant_regime():
    """Every kit that ships a project script READING the kernel's `INV` store.

    TWO SUBJECTS HAVE ALREADY EMPTIED THEMSELVES HERE, and both times the test stayed green
    through the defect it was written for. Measured on 2026-08-01:

      * derived from `hooks/guard_guidelines.py` existing — deleting that file made research drop
        out of the subject, 2 passed;
      * derived from the string ``INV`` appearing in the constitution — rewriting the six
        occurrences in the research constitution to `**INV**` and THEN deleting the hook, again
        2 passed. A prose anchor is defeated by the same edit that hides the change, and the only
        backstop (`test_no_section_of_a_pinned_instruction_file_disappears_unnoticed`) is a re-pinnable
        tripwire on the text, not a guard on this subject.

    So the anchor is CODE, read as code: a kit whose shipped `templates/repo/scripts/**` composes
    `kernel.backlog_types.ACTIVE_DIRS["INV"]` has an invariant regime, because something it ships
    reads that store. Measured: dev and research (`kit_checks.py`, whose `INVARIANTS_DIR` feeds
    `load_invariants`/`governed_source_areas`), office not — its scripts are ledger and filing
    tools and touch no invariant. Undoing THAT to escape this test is not a quiet edit: those
    scripts are byte-mirrored between dev and research (`test_shared_kit_files_identical`) and
    their invariant reader is pinned against the gate's
    (`test_the_two_readers_of_a_governed_source_area_agree`).

    The floor is asserted for the case no argument covers — a reader that simply stops matching.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.backlog_types import ACTIVE_DIRS
    wanted = ACTIVE_DIRS["INV"]
    kits = []
    for kit in sorted(glob.glob(os.path.join(ROOT, "team-kits", "*", "constitution",
                                             "AGENTS.md"))):
        kit_dir = os.path.dirname(os.path.dirname(kit))
        scripts = glob.glob(os.path.join(kit_dir, "templates", "repo", "scripts", "*.py"))
        if any(_composes_kernel_dir(path, wanted) for path in sorted(scripts)):
            kits.append(kit_dir)
    assert len(kits) >= 2, (
        "only %d kit(s) ship a script that reads the invariant store (%s) — either a kit lost its "
        "regime, or this reader stopped matching; both are findings, neither is a pass"
        % (len(kits), ", ".join(os.path.basename(k) for k in kits) or "none"))
    return kits


@pytest.mark.parametrize("kit", _kits_with_an_invariant_regime(), ids=os.path.basename)
def test_every_specialist_that_can_write_carries_the_guidelines_guard(kit):
    """`guard_guidelines` refuses a code write no `INV` item governs. It is registered in the
    AGENTS' OWN FRONTMATTER rather than in settings.json — deliberately, because settings hooks
    fire for the lead too and this rule is the specialists'.

    Measured 2026-07-31: it was registered for `backend-developer` and `frontend-developer` only,
    while six further dev specialists ship `Edit`/`Write` in their tool list — among them
    `devops-engineer`, which writes deployment code, and `software-architect`, which is the role
    the guard's own refusal tells you to ask. Measured 2026-08-01: the research kit shipped no
    `guard_guidelines.py` at all, so parity row 14 was prose there while its own §2.7 promised a
    rule — its seven writing roles are covered here now.

    BOTH SUBJECTS ARE DERIVED, not lists of names, and neither is derived from the thing under
    test: the kits are `_kits_with_an_invariant_regime()` — those whose shipped repo scripts read
    the `INV` store — and inside each, every agent that is not the SESSION agent (settings.json
    `agent`) and whose tools include a write tool registers the guard on the write matcher.
    Registering it where no code is ever written costs nothing — the guard decides per FILE whether
    the language is one it governs — so there is no role for which the answer is legitimately "no",
    and a new specialist or a new kit is covered the day it ships.

    The frontmatter is PARSED as YAML, never scanned: a reviewer who moves a hook to single quotes
    or a folded scalar writes the same registration, and a line reader would call it missing.
    """
    yaml = pytest.importorskip("yaml")
    assert os.path.isfile(os.path.join(kit, "hooks", "guard_guidelines.py")), (
        "%s ships a script that reads the invariant store and no guard_guidelines.py — the rule "
        "its §2 states has no mechanism in this kit" % os.path.basename(kit))
    with open(os.path.join(kit, "settings", "settings.json"), encoding="utf-8") as handle:
        session_agent = json.load(handle).get("agent")
    assert session_agent, "settings.json names no session agent"

    checked, missing = 0, []
    for path in sorted(glob.glob(os.path.join(kit, "agents", "*.md"))):
        with open(path, encoding="utf-8") as handle:
            raw = handle.read()
        front = yaml.safe_load(raw.split("---", 2)[1]) or {}
        if front.get("name") == session_agent:
            continue
        tools = {t.strip() for t in str(front.get("tools") or "").split(",")}
        if not tools & {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
            continue
        checked += 1
        registered = any(
            "guard_guidelines.py" in ((hook or {}).get("command") or "")
            for groups in [(front.get("hooks") or {}).get("PreToolUse") or []]
            for group in groups
            for hook in (group or {}).get("hooks") or [])
        if not registered:
            missing.append(os.path.basename(path))
    assert checked >= 6, "only %d writing specialists found — the reader stopped matching" % checked
    assert not missing, (
        "these %s specialists may write files and do not register guard_guidelines, so a code "
        "write no INV governs passes for them: %s"
        % (os.path.basename(kit), ", ".join(missing)))


@pytest.mark.parametrize("kit", _kits_with_an_invariant_regime(), ids=os.path.basename)
def test_the_guidelines_guard_reaches_exactly_the_areas_its_kit_calls_code(tmp_path, kit):
    """The behaviour half, and the half that keeps the constitutions honest about parity row 14.

    Run against a project holding ONE `INV` whose scope governs a language that is not the one
    being written, so "an invariant exists but none governs this file" — the case the rule is for,
    and not the "no regime at all" case that passes by design.

    THE WHOLE REACH IS MEASURED, not one example of it, and that is the fix for a defect this test
    had in its first cut: it asserted `src/**` refused and three directories allowed, and the
    research constitution then described the reach as "`src/**` — or a code file at the repo ROOT".
    Measured 2026-08-01, the guard also refuses fourteen further areas the text did not name
    (`api`, `lib`, `app`, `web`, `internal`, `ui`, `cmd`, `packages`, `server`, `include`,
    `firmware`, `hardware`, `backend`, `frontend`), while `analysis/`, `scripts/` and `data/` —
    the three most obvious research homes — pass and were in no "not reached" list either.

    So the subject is the hook's OWN `CODE_TOP`, read out of the module: every area in it must
    refuse, and a directory outside it must pass. A widening of `CODE_TOP` that a constitution has
    not caught up with turns this red on the ALLOW side, which is the direction a text can lie in
    without anybody noticing.
    """
    pytest.importorskip("yaml")
    repo = tmp_path / os.path.basename(kit)
    os.makedirs(str(repo / "project_memory"))
    capture_invariant(repo, "typescript", text="strict mode everywhere",
                      source=_root_item_for(repo, kit))

    hooks_dir = os.path.join(kit, "hooks")
    guard = load_kit_module("guard_guidelines_reach_%s" % os.path.basename(kit),
                            os.path.join(hooks_dir, "guard_guidelines.py"))

    def payload(rel):
        # a SUBAGENT write: this guard lives in the specialists' frontmatter, never in settings
        return dict(_pm_write(repo, rel), agent_id="sub-1", agent_type="writer")

    refused = run_hook_process("guard_guidelines.py", payload("src/analyse.py"), repo,
                               hooks_dir=hooks_dir)
    assert refused.returncode == 2, refused.stderr
    assert "no INV item of this project governs it" in refused.stderr

    # every area the module itself calls code, plus the repo root — the reach, in full
    for top in sorted(guard.CODE_TOP) + [""]:
        rel = (top + "/" if top else "") + "probe.py"
        result = run_hook_process("guard_guidelines.py", payload(rel), repo, hooks_dir=hooks_dir)
        assert result.returncode == 2, (rel, result.stderr)

    # ...and what it does NOT reach. Named here because each of these is claimed as unreached by a
    # kit text, so the claim is measured rather than believed; `reports/x.md` is the second axis
    # (a language the guard tracks for nobody).
    for rel in ("notebooks/x.py", "tests/test_a.py", "analysis/x.py", "scripts/x.py",
                "data/x.py", "reports/x.md"):
        assert rel.split("/")[0] not in guard.CODE_TOP, rel
        result = run_hook_process("guard_guidelines.py", payload(rel), repo, hooks_dir=hooks_dir)
        assert result.returncode == 0, (rel, result.stderr)

    # NO CONSTITUTION ENUMERATES THESE AREAS, which is the only form of that sentence a text can
    # hold. A conditional pin stood here for one round — "whichever row names areas has to name
    # all of them" — and it was a string search over a document: rewriting the research row's
    # fifteen names to `` `src/**` ``-with-slash spellings emptied its match set and switched the
    # pin off, measured, 2 passed. The answer is not a fourth pin but the deletion the pin was
    # protecting: both rows now state the definition and point at `CODE_TOP`, so the only place
    # the area set is written down is the code above, and a sixteenth area ages nothing.
    row = _enforcement_row(kit, "guard_guidelines")
    # READ THE BACKTICK SPANS, do not split on whitespace. `row.split()` compared tokens, so
    # `` `src` `` was caught and `` `src`, `` — the same name with a comma — was not; measured,
    # the whole fifteen-name list came back green in two of three spellings, including the
    # `` `src/**` `` form. The `/**` and `/` suffixes are stripped for the same reason.
    named = {span.rstrip("/*") for span in re.findall(r"`([^`]+)`", row)} & set(guard.CODE_TOP)
    assert not named, (
        "%s's guard_guidelines row names %s again — an enumeration in a text is what goes stale; "
        "state the rule and point at the constant"
        % (os.path.basename(kit), ", ".join(sorted(named))))


def _enforcement_row(kit, hook):
    """The kit's own table row for one hook — the cell a role reads at the gate.

    THE ROW MOVED, so this reader did. It lived in the constitution's §2 until that table went to
    `hooks/ENFORCEMENT.md`, which is where every refusal message now sends a blocked role; both
    files are read so that a row stated in either is found, and exactly one row must match, which
    is what makes "the cell" a singular thing.
    """
    rows = []
    for relative in (os.path.join("constitution", "AGENTS.md"),
                     os.path.join("hooks", "ENFORCEMENT.md")):
        with open(os.path.join(kit, relative), encoding="utf-8") as handle:
            rows += [line for line in handle.read().splitlines()
                     if line.lstrip().startswith("|") and hook in line.split("|")[1]]
    assert len(rows) == 1, "%s: %d enforcement rows for %s" % (kit, len(rows), hook)
    return rows[0]


def _root_item_for(repo, kit):
    """The kit's own root item type, captured through the kernel so `INV.source` resolves."""
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    state = ProjectState(os.path.join(str(repo), "project_memory"))
    if os.path.basename(kit).startswith("research"):
        return state.capture("RQ", {
            "title": "Retry semantics", "class": "research",
            "question": "How long should retries wait?", "motivation": "Throughput drops",
            "acceptance_criteria": ["measured"], "out_of_scope": ["ui"], "priority": "high"})["id"]
    return state.capture("PR", dict(PR_FIELDS))["id"]


def test_a_script_beside_quality_py_cannot_forge_the_pipeline_verdict(tmp_path):
    """The pipeline verdict is what `gate_pipeline` and `gate_git` consume as merge evidence, so
    anything that can reach it can forge a merge.

    The first cut of `auxiliary_stages` IMPORTED every `.py` beside `quality.py` and checked the
    contract afterwards, which ran each module body inside the pipeline process. Measured with a
    `scripts/aaa_helper.py` that declares NO contract and calls
    `sys.modules["__main__"].FAILS.clear()`: a RED pipeline became `[quality] pipeline GREEN`, rc 0.
    Reachable for any role whose task scope legitimately includes `scripts/` — devops, backend.

    Discovery is an AST parse now and execution is a SUBPROCESS, so neither step runs a sibling's
    code in this process. The project is made red by something the forger does not control (a file
    over the anti-monolith budget), and the assertion is that it STAYS red.
    """
    forger = ('import sys\n'
              'main = sys.modules.get("__main__")\n'
              'if main is not None and hasattr(main, "FAILS"):\n'
              '    main.FAILS.clear()\n')
    verdicts = {}
    for planted in (False, True):
        work = tmp_path / ("planted" if planted else "clean")
        write(str(work / "src" / "static" / "app.js"), "let x = 1;\n" * 900)
        if planted:
            write(str(work / "scripts" / "aaa_helper.py"), forger)
        verdicts[planted] = run_quality_proc(str(work))
    assert verdicts[False].returncode == 1, verdicts[False].stdout
    assert verdicts[True].returncode == 1, (
        "a script in scripts/ that declares no quality stage cleared the pipeline's "
        "verdict:\n%s" % verdicts[True].stdout)
    assert "pipeline is RED" in verdicts[True].stdout


def test_a_declared_stage_can_add_to_the_verdict_but_never_clear_it(tmp_path):
    """THE OTHER HALF of the same question — what does DECLARING a stage make reachable?

    It makes exactly one thing reachable, and that is worth naming rather than assuming: a file in
    `scripts/` that declares the pair is EXECUTED on every pipeline run. It is contained by
    construction rather than by trust — it runs as its own process, so the only channel back is an
    exit code, and an exit code can only ADD an `ok`/`warn`/`fail`. There is no value it can return
    that removes a FAIL another stage recorded. Measured with a stage that exits 0 (the most
    permissive answer it has) in a project the file budget has already turned red, and with a
    marker file proving it really ran.
    """
    stage = ('import os, sys\n'
             'QUALITY_STAGE = ("planted stage", "warn")\n'
             'if "--quality-stage" in sys.argv[1:]:\n'
             '    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),\n'
             '                           "ran.marker"), "w") as handle:\n'
             '        handle.write("ran")\n'
             '    print("all clear")\n'
             '    sys.exit(0)\n')
    work = tmp_path / "planted-stage"
    write(str(work / "src" / "static" / "app.js"), "let x = 1;\n" * 900)
    write(str(work / "scripts" / "zz_planted.py"), stage)
    result = run_quality_proc(str(work))
    assert (work / "scripts" / "ran.marker").is_file(), (
        "the declared stage was not executed at all:\n%s" % result.stdout)
    assert "PASS  planted stage" in result.stdout, result.stdout
    assert result.returncode == 1 and "pipeline is RED" in result.stdout, result.stdout


def test_the_stage_flag_the_pipeline_runs_is_the_one_the_checkers_answer():
    """`quality.STAGE_FLAG` and each checker's own spelling are two statements of one fact, and the
    pipeline runs the checker as a subprocess, so a divergence would be a stage that is discovered,
    launched, and silently does something else. Asked of both running modules, not of a constant
    here."""
    quality = load_kit_module("quality_flag", QUALITY)
    for path in sorted(glob.glob(os.path.join(
            ROOT, "team-kits", "*", "templates", "repo", "scripts", "*.py"))):
        if quality.declared_stage(path) is None:
            continue
        proc = subprocess.run([sys.executable, path, quality.STAGE_FLAG],
                              cwd=os.path.dirname(os.path.dirname(path)),
                              capture_output=True, text=True, timeout=300)
        assert proc.returncode in (0, 1), (path, proc.returncode, proc.stderr)
        assert proc.stdout.strip(), "%s answered the stage flag with nothing" % path
