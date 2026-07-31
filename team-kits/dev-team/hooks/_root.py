#!/usr/bin/env python3
"""
Shared helper: resolve the repo/project root independent of the current working
directory. A real test run had an agent's cwd slip into a subfolder (frontend/),
which broke every hook that trusted cwd. This makes root resolution cwd-proof.

Resolution order:
  1) $CLAUDE_PROJECT_DIR — Claude Code sets this to the session's project root and
     keeps it stable even if the agent `cd`s elsewhere.
  2) Walk UP from the hook JSON's `cwd` (or os.getcwd()) until a repo marker is found
     (.claude/ | project_memory/ | .git).
  3) Fallback to the original cwd.
"""
import os


def _drive_upper(path):
    """Windows: uppercase a lowercase drive letter (c:\\... -> C:\\...). The session cwd often
    carries the lowercase form, and a node/vite child spawned with it as cwd breaks on rollup's
    case-sensitive module identity (verified A/B: ONLY the drive letter matters — a real gate
    blocked a push for a whole night on exactly this). Deliberately lexical, NOT realpath():
    resolving junctions would change path identity for every prefix-comparing guard."""
    if os.name == "nt" and len(path) >= 2 and path[1] == ":":
        return path[0].upper() + path[1:]
    return path


def find_repo_root(start=None):
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and os.path.isdir(env):
        return _drive_upper(os.path.abspath(env))
    base = _drive_upper(os.path.abspath(start or os.getcwd()))
    d = base
    while True:
        for marker in (".claude", "project_memory", ".git"):
            if os.path.exists(os.path.join(d, marker)):
                return d
        parent = os.path.dirname(d)
        if parent == d:
            return base
        d = parent


# The typed state's root types, per kit (kernel/backlog_types.ROOT_TYPE_BY_KIT). A dev project is
# led by PRs, a research project by RQs; both may exist in a mixed repo, so both count.
# Spelled out because `has_root_item` answers on every guarded shell command and importing the
# kernel there would pull PyYAML into that path. It is a cache with a proof, not a second list:
# `test_root_item_globs_are_the_kernels_root_types` derives the same tuple from ACTIVE_DIRS +
# ROOT_TYPE_BY_KIT, so a moved directory or a new root type cannot leave the gates asleep.
ROOT_ITEM_GLOBS = ("product/active/PR-*.yaml", "research/active/RQ-*.yaml")

# The id PREFIXES those globs look for -- what a merge or push names when it names the item it is
# about. Derived from the globs rather than written out a second time: the two are the same fact
# seen from opposite sides (a file on disk, an id in a branch name), and a root type added to one
# but not the other is how a gate goes blind on the kit that introduced it.
ROOT_ITEM_TYPES = tuple(os.path.basename(pattern).split("-", 1)[0] for pattern in ROOT_ITEM_GLOBS)


def has_root_item(repo_root):
    """Has this project captured its first product requirement / research question yet?

    THE ONE PREDICATE five gates used to compute for themselves, each by grepping
    `project_memory/product_requirements.yaml` for a `PRD-<number>` line. That file no longer exists —
    the state is one file per item — and five private copies of a question is how the answers
    drift. Gates ask this to decide whether they APPLY at all: before the first root item a repo
    is still being set up, and a quality gate that fires there blocks the setup it exists to
    protect.

    Glob, not YAML: this runs on every guarded shell command, and the question is "does an item
    exist", which a filename answers.
    """
    import glob as _glob
    state = os.path.join(repo_root, "project_memory")
    for pattern in ROOT_ITEM_GLOBS:
        if _glob.glob(os.path.join(state, pattern.replace("/", os.sep))):
            return True
    return False
