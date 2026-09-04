"""Build a project the dev-team dashboard generator can run in, from a copy of a real state.

Used by parity.py (kernel board vs dev-team dashboard) and by the mockup prototype. Nothing here
touches the main repo: the rig lives under this scratch directory, the code comes from the
g3-board worktree, and the state is a COPY of whatever `source_pm` names.
"""
import os
import shutil
import subprocess
import sys

MAIN = "C:/Offline Repos/AgentAndSkills"
WT = "C:/Offline Repos/v2-testbed/_worktrees/g3-board"
SCRATCH = "C:/Offline Repos/v2-testbed/_round-scratch/TSK-0115"
TEAM_KITS = os.path.join(WT, "team-kits")

sys.path.insert(0, os.path.join(WT, "tools"))
sys.path.insert(0, TEAM_KITS)
sys.dont_write_bytecode = True


def build(rig, source_pm):
    """A rig at `rig` holding the hook bridge, the dev-team scripts and a copy of `source_pm`."""
    import conftest  # the suite's own closure helper, so the bridge travels with its imports
    if os.path.isdir(rig):
        shutil.rmtree(rig)
    hooks = os.path.join(rig, ".claude", "hooks")
    os.makedirs(hooks)
    src_hooks = os.path.join(TEAM_KITS, "dev-team", "hooks")
    for name in conftest.sibling_import_closure("_kernel.py", src_hooks):
        shutil.copy(os.path.join(src_hooks, name), os.path.join(hooks, name))
    scripts = os.path.join(rig, "scripts")
    os.makedirs(scripts)
    tsrc = os.path.join(TEAM_KITS, "dev-team", "templates", "repo", "scripts")
    for name in ("generate_dashboard.py", "progress.dashboard.template.html", "kit_checks.py"):
        shutil.copy(os.path.join(tsrc, name), os.path.join(scripts, name))
    pm = os.path.join(rig, "project_memory")
    if source_pm is None:
        os.makedirs(pm)
    else:
        shutil.copytree(source_pm, pm, ignore=shutil.ignore_patterns(
            "staging", "generated", ".kernel.lock*", ".audit", "__pycache__"))
    return pm


def kernel_index(pm):
    """The kernel's own regeneration: index.yaml AND board.html, one call, one timestamp."""
    from kernel.state import ProjectState
    return ProjectState(pm).generate_index()


def dev_dashboard(rig):
    env = dict(os.environ, HARNESS_KERNEL_PATH=TEAM_KITS)
    return subprocess.run([sys.executable, "-B", os.path.join(rig, "scripts", "generate_dashboard.py")],
                          capture_output=True, text=True, cwd=rig, env=env, timeout=120)
