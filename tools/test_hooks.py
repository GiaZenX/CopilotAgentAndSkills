#!/usr/bin/env python3
"""
Behaviour tests for the shipped enforcement hooks + scripts/quality.py (dev-team kit).

The harness blocks other repos' merges on missing tests; it must test its OWN security machinery.
Each hook is run as a real subprocess with synthetic stdin JSON and CLAUDE_PROJECT_DIR, and asserted
on its exit code (0 = allow, 2 = block for guards/gates, 1 = red for quality.py). Run: pytest tools/
"""
import ast
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
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


# ---------------- gate_git (PRD binding) ----------------
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


def capture_root_item(repo, fields=None):
    """Give a repo its first typed root item — what `_root.has_root_item` now looks for.

    Written THROUGH the kernel, not by hand: the merge gates ask the state validator whether the
    state is complete, so a hand-rolled item would make every gate test measure a broken fixture
    rather than the gate.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    root = os.path.join(str(repo), "project_memory")
    os.makedirs(root, exist_ok=True)
    return ProjectState(root).capture("PR", dict(fields or PR_FIELDS))


@pytest.fixture
def prd_repo(tmp_path):
    capture_root_item(tmp_path)
    return tmp_path


def _merge(repo, report_txt):
    write(str(repo / "project_memory" / "test_reports.yaml"), report_txt)
    return {"tool_name": "Bash", "tool_input": {"command": "git merge feat/PRD-0001-x"}, "cwd": str(repo)}


def test_gate_git_force_push_blocked(prd_repo):
    payload = {"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}, "cwd": str(prd_repo)}
    assert run_hook("gate_git.py", payload, prd_repo) == 2


def test_gate_git_blocks_powershell_tool_too(prd_repo):
    # the gates must not be bypassable via the separate PowerShell tool (a real setup has both)
    payload = {"tool_name": "PowerShell", "tool_input": {"command": "git push --force origin main"},
               "cwd": str(prd_repo)}
    assert run_hook("gate_git.py", payload, prd_repo) == 2


def test_gate_git_stray_prd_pass_blocked(prd_repo):
    payload = _merge(prd_repo, "reports:\n  R1: { prd: PRD-0002, result: pass }\n")
    assert run_hook("gate_git.py", payload, prd_repo) == 2


def test_gate_git_matching_prd_pass_allowed(prd_repo):
    payload = _merge(prd_repo, "reports:\n  R1: { prd: PRD-0001, result: pass }\n")
    assert run_hook("gate_git.py", payload, prd_repo) == 0


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


def test_quality_python_targets_from_source_areas(tmp_path):
    os.makedirs(str(tmp_path / "scripts"))
    shutil.copy(QUALITY, str(tmp_path / "scripts" / "quality.py"))
    os.makedirs(str(tmp_path / "src"))
    os.makedirs(str(tmp_path / "compounder"))
    write(str(tmp_path / "project_memory" / "coding_guidelines.yaml"),
          "source_areas:\n  - compounder\n  - '..'\n")
    mod = _quality_mod(str(tmp_path / "scripts" / "quality.py"))
    targets = mod._python_targets()
    assert "compounder" in targets and "src" in targets
    assert ".." not in targets  # dot-only names never become lint targets (audit class)


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


# ---------------- guard_guidelines token matching (compound keys like html_vanilla_js) ----------------
def test_guidelines_compound_key_satisfies_js(prd_repo):
    # the synaipse case: the architect named the block `html_vanilla_js:` — token "js" must match
    write(str(prd_repo / "project_memory" / "coding_guidelines.yaml"),
          "global:\n  - x\nlanguages:\n  html_vanilla_js:\n    - no inline handlers\n")
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": str(prd_repo / "src" / "app.js")}, "cwd": str(prd_repo)}
    assert run_hook("guard_guidelines.py", payload, prd_repo) == 0


def test_guidelines_still_blocks_js_without_block(prd_repo):
    write(str(prd_repo / "project_memory" / "coding_guidelines.yaml"), "global:\n  - x\nlanguages: {}\n")
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": str(prd_repo / "src" / "app.js")}, "cwd": str(prd_repo)}
    assert run_hook("guard_guidelines.py", payload, prd_repo) == 2


def test_guidelines_stray_key_outside_languages_does_not_satisfy(prd_repo):
    # a `node_version:` under global must NOT satisfy .js — only keys under `languages:` count
    pytest.importorskip("yaml")
    write(str(prd_repo / "project_memory" / "coding_guidelines.yaml"),
          "global:\n  node_version: 20\nlanguages: {}\n")
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": str(prd_repo / "src" / "app.js")}, "cwd": str(prd_repo)}
    assert run_hook("guard_guidelines.py", payload, prd_repo) == 2


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


def test_guidelines_block_cpp_without_languages(prd_repo):
    write(str(prd_repo / "project_memory" / "coding_guidelines.yaml"), "global:\n  - x\nlanguages: {}\n")
    payload = {"tool_name": "Write",
               "tool_input": {"file_path": str(prd_repo / "src" / "main.cpp")}, "cwd": str(prd_repo)}
    assert run_hook("guard_guidelines.py", payload, prd_repo) == 2


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


def test_kit_check_remedies_never_name_a_file_the_project_does_not_have(tmp_path):
    """A remedy has to be walkable. V2 dissolved coding_guidelines.yaml, so a check that offers it
    as the only way out sends the user to a file the scaffold does not create and gate_write_scope
    would not let them write — the "remedy nobody can follow" class gate_filing documents on
    itself. When the project HAS a guidelines file the remedy must name that one."""
    pytest.importorskip("yaml")
    write(str(tmp_path / "src" / "static" / "app.js"), "let x = 1;\n" * 900)
    r = run_quality_proc(str(tmp_path))
    assert "file budget" in r.stdout and r.returncode == 1
    assert "coding_guidelines.yaml" not in r.stdout
    assert "has no home in this project" in r.stdout
    write(str(tmp_path / "project_memory" / "research_guidelines.yaml"), "source_areas: []\n")
    r = run_quality_proc(str(tmp_path))
    assert "`file_budget: exempt:` in project_memory/research_guidelines.yaml" in r.stdout


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
    "gate_git.py": "the dev/research merge gates run different pipelines",
}
# The SAME rule for the project scripts a kit ships. Empty on purpose: the office kit's scripts
# share no filename with dev/research, and every name dev and research both ship is meant to be one
# file. A kit that needs its own variant of one adds it here WITH the reason.
KIT_SPECIFIC_SCRIPTS = {}
KITS = ("dev-team", "office-team", "research-team")


def _kit_files_by_name(rel_dir, suffixes):
    """{filename: {kit: bytes}} for one directory across all kits — the input to the mirror rule."""
    by_name = {}
    for kit in KITS:
        directory = os.path.join(ROOT, "team-kits", kit, *rel_dir)
        for name in sorted(os.listdir(directory)):
            if name.endswith(suffixes):
                with open(os.path.join(directory, name), "rb") as handle:
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


def test_shared_kit_files_identical():
    """DERIVED, not listed. The old version enumerated six filenames, so every file mirrored after
    it was written stayed unpinned — `_gate.py`, `_kernel.py`, `_compat.py`, `kit_trust_state.py`
    and all six V2 gates lived in three unpinned copies. It found nothing when
    `gate_shell_hygiene.py` actually drifted: a fix limiting the docker rule to DESTRUCTIVE
    commands reached dev-team and neither mirror, so two kits blocked `docker compose ps`.

    Now the burden is the other way round: a name present in more than one kit is pinned unless
    KIT_SPECIFIC_HOOKS says why it differs. A new mirrored file is covered the day it ships.

    The SCRIPTS half used to be the old shape again — three typed filenames — so `kit_browser_checks.py`
    was unpinned here and `generate_dashboard.py` plus its HTML shell would have drifted silently the
    day research got a copy. Same derivation now, same burden of proof."""
    _assert_mirrored("hooks", _kit_files_by_name(("hooks",), (".py",)), KIT_SPECIFIC_HOOKS)
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
    write(str(tmp_path / "project_memory" / "coding_guidelines.yaml"),
          "global:\n  - x\nlanguages: {}\nfile_budget:\n  max_lines: 800\n  exempt:\n"
          "    - path: src/static/app.js\n      reason: \"legacy monolith - split tracked in TSK-1\"\n")
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


# ---------------- gate_git: entry-level QA binding (audit false-accept regression) ----------------
def test_gate_git_old_pass_other_task_fresh_fail_target_blocks(prd_repo):
    # the exact reported hole: an old PASS for ANOTHER PRD + a fresh FAIL for the target in ONE file
    write(str(prd_repo / "project_memory" / "test_reports.yaml"),
          "reports:\n  R1: { prd: PRD-0009, result: pass }\n  R2: { prd: PRD-0001, result: fail }\n")
    payload = {"tool_name": "Bash", "tool_input": {"command": "git merge feat/PRD-0001-x"}, "cwd": str(prd_repo)}
    assert run_hook("gate_git.py", payload, prd_repo) == 2


def test_gate_git_bound_pass_still_allows(prd_repo):
    write(str(prd_repo / "project_memory" / "test_reports.yaml"),
          "reports:\n  R1: { prd: PRD-0009, result: fail }\n  R2: { prd: PRD-0001, result: pass }\n")
    payload = {"tool_name": "Bash", "tool_input": {"command": "git merge feat/PRD-0001-x"}, "cwd": str(prd_repo)}
    assert run_hook("gate_git.py", payload, prd_repo) == 0


def test_gate_git_indirect_binding_falls_back_to_file_level(prd_repo):
    # entries bound via task ids only (no PRD in the entry) -> file-level check keeps working
    write(str(prd_repo / "project_memory" / "test_reports.yaml"),
          "# gate for PRD-0001\nreports:\n  R1: { task: TSK-0007, result: pass }\n")
    payload = {"tool_name": "Bash", "tool_input": {"command": "git merge feat/PRD-0001-x"}, "cwd": str(prd_repo)}
    assert run_hook("gate_git.py", payload, prd_repo) == 0


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
    write(str(repo / "project_memory" / "coding_guidelines.yaml"),
          "source_areas:\n  - '..'\n  - '.'\nfile_budget:\n  max_lines: 800\n  exempt: []\n")
    calls, ok, fail, warn = _collector()
    mod.check_file_budget(str(repo), ok, fail, warn)
    assert not any("neighbor" in m for _n, m in calls["fail"])  # never scans outside the repo
    assert any("NO scan area matched" in m for _n, m in calls["warn"])


def test_gate_test_coverage_rejects_dot_areas(tmp_path):
    repo = tmp_path / "repo"
    write(str(tmp_path / "stray.py"), "def f():\n    return 1\n")  # code OUTSIDE the repo
    capture_root_item(repo)
    write(str(repo / "project_memory" / "testing_guidelines.yaml"),
          "coverage_areas:\n  - '..'\n")
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
    write(str(tmp_path / "project_memory" / "coding_guidelines.yaml"),
          "source_areas:\n  - compounder\nfile_budget:\n  max_lines: 800\n  exempt: []\n")
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
    assert run_hook("gate_test_coverage.py", payload, tmp_path) == 0  # undeclared -> old behavior
    write(str(tmp_path / "project_memory" / "testing_guidelines.yaml"),
          "coverage_areas:\n  - compounder\n")
    r = run_hook_process("gate_test_coverage.py", payload, tmp_path)
    assert r.returncode == 2 and "compounder" in r.stderr
    write(str(tmp_path / "compounder" / "test_core.py"), "def test_f():\n    assert True\n")
    assert run_hook("gate_test_coverage.py", payload, tmp_path) == 0


PROC_HASH = os.path.join(ROOT, "team-kits", "office-team", "templates", "repo", "scripts",
                         "proc_hash.py")


def _proc_repo(tmp_path, newline="\n"):
    repo = tmp_path / "office"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(PROC_HASH, str(repo / "scripts" / "proc_hash.py"))
    text = (
        "processes:\n"
        "  PROC-0001:\n"
        "    status: APPROVED\n"
        "    steps:\n"
        "      - do a thing\n"
        '    approved_hash: "oldhash"\n'
        "  PROC-0002:\n"
        "    status: PROPOSED\n"
        "    steps:\n"
        "      - do another thing\n"
        "  PROC-0003:\n"
        "    status: APPROVED\n"
        "    steps:\n"
        "      - third thing\n"
        '    approved_hash: "thirdhash"\n'
    ).replace("\n", newline)
    path = repo / "project_memory" / "process_definitions.yaml"
    path.parent.mkdir(parents=True)
    path.write_bytes(text.encode("utf-8"))
    return repo, path


def test_proc_hash_update_stays_in_its_block(tmp_path):
    import tomllib  # noqa: F401  (env sanity: py3.11+)
    import yaml
    repo, path = _proc_repo(tmp_path)
    # PROC-0002 has NO approved_hash line: the old (?s) regex swallowed the FOLLOWING blocks and
    # wrote the hash into a NEIGHBOR (real incident: a PROPOSED PROC carried another's hash)
    r = subprocess.run([sys.executable, str(repo / "scripts" / "proc_hash.py"),
                        "PROC-0002", "--update"],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    procs = data["processes"]
    assert procs["PROC-0001"]["approved_hash"] == "oldhash"      # neighbors untouched
    assert procs["PROC-0003"]["approved_hash"] == "thirdhash"
    new_hash = procs["PROC-0002"]["approved_hash"]
    assert new_hash and new_hash not in ("oldhash", "thirdhash")


def test_proc_hash_update_survives_crlf(tmp_path):
    import yaml
    repo, path = _proc_repo(tmp_path, newline="\r\n")
    r = subprocess.run([sys.executable, str(repo / "scripts" / "proc_hash.py"),
                        "PROC-0001", "--update"],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["processes"]["PROC-0001"]["approved_hash"] != "oldhash"
    assert data["processes"]["PROC-0003"]["approved_hash"] == "thirdhash"


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
    write(str(tmp_path / "project_memory" / "coding_guidelines.yaml"),
          "languages:\n  python:\n    - use type hints\n")
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


def _dispatch_authorising_kinds():
    """APR kinds that really authorise a dispatch, read out of the kernel that decides.

    Two routes exist, and each keeps its answer in a different place: the ROOT route in the
    `ROOT_DISPATCH_KINDS` constant, the task-listing route as a literal comparison inside
    `_covering_analysis_apr`. Both are read here rather than restated, because the point of the test
    is that instruction text must not name a THIRD kind — `APR.kind: routine` was documented as the
    auditor's dispatch basis while the kernel refused it (measured 2026-07-26).
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.approvals import APR_KINDS, ROOT_DISPATCH_KINDS
    source = open(os.path.join(ROOT, "team-kits", "kernel", "dispatch.py"),
                  encoding="utf-8").read()
    kinds = set(ROOT_DISPATCH_KINDS)
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == "_covering_analysis_apr":
            kinds |= {n.value for n in ast.walk(node)
                      if isinstance(n, ast.Constant) and n.value in APR_KINDS}
    return kinds


def test_the_auditor_names_an_approval_kind_that_can_actually_dispatch_it():
    """The auditor's own SKILL must name a kind the dispatch gate accepts.

    It documented `APR.kind: routine` — the kind spec II.10a designs for this role — as the approval
    it "is dispatched on", and added that an expired one blocks the spawn. Measured: a valid,
    unexpired, unrevoked routine APR on the root authorises nothing, so the promised expiry check is
    unreachable code and an auditor following its instruction cannot be spawned at all. Until the
    kernel grows the route, the text has to name the kind that works.
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
INSTRUCTION_PATTERNS = ("constitution/AGENTS.md", "agents/*.md", "skills/*/SKILL.md",
                        "templates/project_memory/**/*")


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


def test_constitution_names_the_file_that_switches_a_gate_off():
    """A gate that fails OPEN on a missing input must say WHICH input, where its rule is documented.

    Two shipped rows claimed an unconditional hard block over a hook that exits 0 while its registry
    is absent — `gate_proc_approved` (the V2 bootstrap hole stayed permanently open) and
    `guard_guidelines` (no template ships its file, so the default project has no guard). Both rows
    read as protection nobody had. Naming the file is the smallest claim that cannot be true while
    the precondition is hidden: derived from the hook's AST, so a hook that GAINS such a path is
    covered the day it ships, and no list of hook names exists here to go stale.
    """
    for kit in ("dev-team", "research-team", "office-team"):
        cpath = os.path.join(ROOT, "team-kits", kit, "constitution", "AGENTS.md")
        lines = open(cpath, encoding="utf-8", errors="ignore").read().splitlines()
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
            assert documented, "%s: %s has no constitution row at all" % (kit, name)
            assert any(c in documented for c in sorted(candidates)), (
                "%s: %s stops without deciding when %s is missing, but its constitution row never "
                "names that file — the row reads as unconditional protection. Say which file the "
                "rule depends on." % (kit, name, "/".join(sorted(candidates))))


# Where an exemption below is allowed to be used. ANY = the file genuinely has no template in V2, so
# naming it is a true statement wherever it is written. KIT_ONLY = a DELETED V1 monolith that only
# one kit's own broken tooling still reads: inside that kit, naming it documents the defect; in the
# global entry gates there is no such tooling, so a monolith name there is exactly the V1 regression
# this sweep exists to catch (measured: the entry gates could name `process_definitions.yaml` and
# seed a PROC into it, green).
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
    # optional tuning files the instruction text names in order to say V2 ships neither
    "coding_guidelines.yaml": (ANY, "V2 ships no template; named to explain that guard_guidelines is conditional"),
    "testing_guidelines.yaml": (ANY, "V2 ships no template; named as the optional home of the two coverage knobs"),
    # deleted V1 stores the instruction text names in order to call the tooling that reads them broken
    "process_definitions.yaml": (KIT_ONLY, "deleted V1 PROC registry; named because proc_hash/gate_proc_approved still read it"),
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
MIGRATION_DOC_FILES = ("README.md", "HARNESS_LOG.md")
MIGRATION_DOC_TREES = ("docs/", "radar/")

# Trees that are not the repo's content: git's own store, caches, and the sandbox an e2e run builds.
_SWEEP_SKIP_DIRS = frozenset((".git", ".pytest_cache", "__pycache__", "node_modules",
                              ".e2e-sandbox"))


def _state_root_store(token, stores):
    """The V1 root store from `stores` that a path token puts at the state ROOT, or None.

    `stores` is the inventory to judge against, because there are two: `conftest.V1_MONOLITHS`, the
    stores this lockstep moved and nothing may point at any more, and
    `conftest.V1_ROOT_STORES_NOT_YET_MIGRATED`, the ones another group still owns and which are
    asserted PRESENT. Same machinery, opposite verdict — passing the inventory in is what keeps
    those two from needing two copies of the folding below.

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
    """
    segments = [s for s in re.split(r"[/\\]", token.strip()) if s and s != "."]
    if not segments or segments[-1] not in stores:
        return None
    if len(segments) == 1 or segments[-2] == "project_memory":
        return segments[-1]
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
    # The sibling inventory makes the same kind of claim ("this state went there") and gets the
    # same judgement. Only its REASON is read: the file lists beside it are source paths, not state
    # paths, and a source tree is not what ACTIVE_DIRS is the authority on.
    _assert_state_claims(
        "conftest.V1_ROOT_STORES_NOT_YET_MIGRATED",
        " ".join(why for why, _files in conftest.V1_ROOT_STORES_NOT_YET_MIGRATED.values()),
        *union, exempt_names=_exempt_names((ANY,)))


def test_nothing_shipped_still_spells_a_v1_monolith_path():
    """No file outside the migration documentation names a MOVED monolith AT THE STATE ROOT.

    This is the proof for the eleven stores `conftest.V1_MONOLITHS` names, and for nothing wider.
    Four further V1 root stores fit the same definition and are deliberately outside that
    inventory, because shipped code still reads them and repairing it belongs to another group:
    they are named in `conftest.V1_ROOT_STORES_NOT_YET_MIGRATED` and asserted PRESENT by
    `test_the_open_v1_root_store_couplings_are_still_exactly_these`. Green here therefore means
    "the eleven are gone", not "no V1 coupling is left" — a scaffolded V2 project today cannot get
    a single merge or push through, for one of those four reasons.

    Within that inventory it is a claim about PATHS, not about names. The
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
    assert not offences, (
        "these still point at one of the eleven MOVED V1 monoliths in the state root:\n  %s"
        % "\n  ".join(sorted(set(offences))))


def test_the_open_v1_root_store_couplings_are_still_exactly_these():
    """The other side of the proof: the V1 root stores this lockstep did NOT reach, as measured.

    The completion proof above is only as complete as its inventory, and four V1 root stores are
    outside it on purpose — `conftest.V1_ROOT_STORES_NOT_YET_MIGRATED` says which and why. Left at
    that, the artefact would claim more than it holds: a reader seeing the sweep green would take
    the lockstep for finished while `gate_git` blocks every push in a scaffolded V2 project and
    two office scripts cannot start.

    So the open couplings are asserted as facts that hold TODAY, with the same reader the proof
    uses. Equality in BOTH directions is the whole point:

      * a NEW file reaching for one of these four fails here, which is the guarantee the
        completion proof cannot give for a name outside its inventory;
      * and the day a coupling is repaired, this fails too, saying so in the one place the next
        round will look. That is the `known_hole` bargain — a hole asserted rather than promised —
        and a note in a report would not have survived the round.
    """
    measured = {}
    for rel, store, _token in _sweep_state_root(conftest.V1_ROOT_STORES_NOT_YET_MIGRATED):
        measured.setdefault(store, set()).add(rel)
    recorded = {store: set(files)
                for store, (_why, files) in conftest.V1_ROOT_STORES_NOT_YET_MIGRATED.items()}
    assert measured == recorded, (
        "the open V1 root-store couplings have moved.\n"
        "  gone (delete the entry from conftest.V1_ROOT_STORES_NOT_YET_MIGRATED, and if a store "
        "has no files left, move its name into V1_MONOLITHS so the completion proof owns it): "
        "%s\n"
        "  new (a file started reaching for a deleted V1 root store): %s"
        % (sorted((s, f) for s in recorded for f in recorded[s] - measured.get(s, set())) or "none",
           sorted((s, f) for s in measured for f in measured[s] - recorded.get(s, set())) or "none"))


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
def _office_repo(tmp_path, procs_yaml=None):
    repo = tmp_path / "repo"
    (repo / "project_memory").mkdir(parents=True)
    if procs_yaml is not None:
        write(str(repo / "project_memory" / "process_definitions.yaml"), procs_yaml)
    return repo


def _spawn(repo, prompt):
    return {"tool_name": "Agent",
            "tool_input": {"subagent_type": "bookkeeper", "run_in_background": False,
                           "prompt": prompt}, "cwd": str(repo)}


def _steps_hash(steps):
    import hashlib
    yaml = pytest.importorskip("yaml")
    return hashlib.sha256(yaml.safe_dump(steps, sort_keys=True, allow_unicode=True)
                          .encode("utf-8")).hexdigest()


def test_proc_gate_bootstrap_allows(tmp_path):
    repo = _office_repo(tmp_path, "processes: {}\n")
    assert run_hook("gate_proc_approved.py", _spawn(repo, "onboarding interview"), repo,
                    hooks_dir=OFFICE_HOOKS) == 0


def test_proc_gate_blocks_missing_ref(tmp_path):
    pytest.importorskip("yaml")
    h = _steps_hash(["file it"])
    repo = _office_repo(tmp_path,
                        "processes:\n  PROC-0001:\n    title: x\n    status: APPROVED\n"
                        "    approved_hash: \"%s\"\n    steps:\n      - file it\n" % h)
    assert run_hook("gate_proc_approved.py", _spawn(repo, "please file the inbox"), repo,
                    hooks_dir=OFFICE_HOOKS) == 2


def test_proc_gate_passes_approved_with_hash(tmp_path):
    pytest.importorskip("yaml")
    h = _steps_hash(["file it"])
    repo = _office_repo(tmp_path,
                        "processes:\n  PROC-0001:\n    title: x\n    status: APPROVED\n"
                        "    approved_hash: \"%s\"\n    steps:\n      - file it\n" % h)
    assert run_hook("gate_proc_approved.py", _spawn(repo, "execute PROC-0001 sweep"), repo,
                    hooks_dir=OFFICE_HOOKS) == 0


def test_proc_gate_blocks_tampered_steps(tmp_path):
    pytest.importorskip("yaml")
    h = _steps_hash(["file it"])
    repo = _office_repo(tmp_path,
                        "processes:\n  PROC-0001:\n    title: x\n    status: APPROVED\n"
                        "    approved_hash: \"%s\"\n    steps:\n      - file it\n"
                        "      - NEW sneaky step\n" % h)
    assert run_hook("gate_proc_approved.py", _spawn(repo, "execute PROC-0001"), repo,
                    hooks_dir=OFFICE_HOOKS) == 2


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
    write(str(tmp_path / "project_memory" / "coding_guidelines.yaml"),
          "module_invariants:\n"
          "  - path: src/pure.py\n"
          "    forbidden_tokens: [\"open(\"]\n"
          "    reason: \"pure module - no I/O\"\n")
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
    write(str(tmp_path / "project_memory" / "coding_guidelines.yaml"),
          "yaml_lint_exclude:\n  - \"config/*\"\n")
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
    write(str(tmp_path / "project_memory" / "testing_guidelines.yaml"),
          "coverage_gate:\n  threshold: 80\nbrowser_smoke:\n  entry: /app/\n"
          "  mount_selector: \"#app\"\n")
    assert mod._config(str(tmp_path)) == ("/app/", "#app")
    calls, ok, fail, warn = _collector()
    mod.browser_smoke(str(tmp_path), ok, fail, warn)  # no frontend/dist
    assert not calls["fail"] and any("dist missing" in m for _n, m in calls["warn"])


def test_browser_smoke_config_trailing_comment(tmp_path):
    # audit finding: an unquoted value with a trailing comment silently fell back to the
    # default route — the smoke then green-tested the WRONG page
    mod = _browser_checks_mod()
    write(str(tmp_path / "project_memory" / "testing_guidelines.yaml"),
          "browser_smoke:\n  entry: /app/   # main view\n  mount_selector: '#app'  # spa mount\n")
    assert mod._config(str(tmp_path)) == ("/app/", "#app")


def test_quality_source_areas_inline_and_quoted(tmp_path):
    # audit finding: the block-only parser silently skipped an INLINE-declared area that the
    # file-budget check DID scan — same knob, two behaviors
    os.makedirs(str(tmp_path / "scripts"))
    shutil.copy(QUALITY, str(tmp_path / "scripts" / "quality.py"))
    os.makedirs(str(tmp_path / "compounder"))
    write(str(tmp_path / "project_memory" / "coding_guidelines.yaml"),
          "source_areas: [compounder, '..']\n")
    mod = _quality_mod(str(tmp_path / "scripts" / "quality.py"))
    targets = mod._python_targets()
    assert "compounder" in targets and ".." not in targets
    write(str(tmp_path / "project_memory" / "coding_guidelines.yaml"),
          "source_areas:\n  # extra areas below\n  - 'compounder'\n")
    mod2 = _quality_mod(str(tmp_path / "scripts" / "quality.py"))
    assert "compounder" in mod2._python_targets()  # quoted item + comment line survive


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
    write(str(tmp_path / "project_memory" / "coding_guidelines.yaml"),
          "module_invariants:\n  - path: src/pure.py\n    forbidden_tokens: \"open(\"\n"
          "    reason: \"pure\"\n")
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


def test_quality_regex_fallbacks_without_pyyaml(tmp_path, monkeypatch):
    # CI always installs pyyaml, so the demoted regex fallbacks were DEAD paths in CI (audit) —
    # poison the yaml import to prove the pyyaml-less machine still reads every knob
    os.makedirs(str(tmp_path / "scripts"))
    shutil.copy(QUALITY, str(tmp_path / "scripts" / "quality.py"))
    shutil.copy(KIT_CHECKS, str(tmp_path / "scripts" / "kit_checks.py"))
    write(str(tmp_path / "project_memory" / "project_config.yaml"),
          "project:\n  stacks:\n    - python\n")
    write(str(tmp_path / "project_memory" / "coding_guidelines.yaml"),
          "source_areas:\n  - compounder\n  - '..'\n")
    write(str(tmp_path / "project_memory" / "testing_guidelines.yaml"),
          "coverage_gate:\n  threshold: 85\n")
    os.makedirs(str(tmp_path / "compounder"))
    mod = _quality_mod(str(tmp_path / "scripts" / "quality.py"))
    monkeypatch.setitem(sys.modules, "yaml", None)  # import yaml -> ImportError
    assert mod.declared_stacks() == ["python"]
    targets = mod._python_targets()
    assert "compounder" in targets and ".." not in targets
    assert mod.coverage_threshold() == 85


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
