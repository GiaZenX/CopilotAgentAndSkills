#!/usr/bin/env python3
"""Read the KIT-GAP LOGS of N installed projects and say which entries this repo has not triaged.

THE OTHER END OF FR-0062. A kit project's session records what the kit could not do with the
kernel's `report-gap` command, into that project's own `project_memory/.audit/kit_gaps.jsonl`
(`team-kits/kernel/gaplog.py` is the writer and carries why it lives there). This is the harvest:
the lead points it at the projects it maintains and gets the entries it has not seen, instead of
reading whole sessions after the fact -- which is what BUG-0068 and BUG-0070 actually cost.

THE HARVEST STATE LIVES HERE AND NEVER IN THE PROJECT, and that is the point rather than a detail.
Marking an entry inside the foreign store would mean this repo writing into a project's state
directory -- the wrong trust direction, and the exact thing `gate_write_scope` exists to refuse from
the other side. So `tools/kit_gap_harvest.json` records, keyed by project path plus the entry's
CONTENT id, what has been triaged and what it became. A project that is moved on disk therefore
reports its entries as new again; that is a re-read, not a loss, and it is the price of never
touching the foreign store.

Usage:
  python tools/harvest_kit_gaps.py <project-root> [<project-root> ...]
  python tools/harvest_kit_gaps.py --all                 # every project under a HARNESS_PROJECTS dir
  python tools/harvest_kit_gaps.py --mark <project-root> <entry-id> [--as FR-0099]
"""
import argparse
import json
import os
import sys

# The kit tree is hashed into every kit's VERSION, so a repo tool that imports out of it must not
# leave a `__pycache__` behind -- the same reason `tools/bump_kit_version.py` carries this line, and
# `test_a_repo_tool_that_imports_the_kit_tree_leaves_no_bytecode_in_it` is what holds it.
sys.dont_write_bytecode = True

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "team-kits"))

from kernel import gaplog  # noqa: E402

# Where this repo remembers what it has triaged. Beside the other ratchets in `tools/`, and read and
# written by this file alone.
HARVEST = os.path.join(ROOT, "tools", "kit_gap_harvest.json")
# ...and the ONE way to point it somewhere else. A TEST that exercised the real path was a test that
# DELETED the lead's own triage record: measured 2026-09-01, a `tools/kit_gap_harvest.json` with
# content in it was gone after a green suite run, and two parallel runs would have raced over it.
# The redirect is an environment variable rather than a flag because the thing that must not reach
# the real file is a subprocess somebody else started.
# `tools/test_gaplog.py::test_the_real_harvest_record_is_not_a_test_fixture` measures both ends.
HARVEST_ENV = "HARNESS_KIT_GAP_HARVEST"
# The environment variable naming a directory whose immediate children are projects. Not a path
# constant: which projects a machine maintains is that machine's business, and a list of them in
# this repo would be one more thing that goes stale where nobody looks.
PROJECTS_ENV = "HARNESS_PROJECTS"


def project_key(path):
    """How a project is identified in the harvest record: its absolute path, spelled one way."""
    return os.path.abspath(path).replace("\\", "/").rstrip("/")


def harvest_path():
    """The record this run reads and writes -- the environment's answer, or the repo's own file.

    Resolved per CALL and not captured at import: a caller that sets the variable for a child
    process must be able to move the file, and a constant frozen at import is exactly what would
    look redirected and not be.
    """
    return os.environ.get(HARVEST_ENV) or HARVEST


def read_harvest():
    try:
        with open(harvest_path(), encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_harvest(data):
    path = harvest_path()
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def state_root(project):
    """The state directory a gap log lives under -- `project_memory/` of an installed project.

    A project path that already IS the state directory is accepted too, because that is what a
    person pointing this at a log will type half the time, and guessing wrong here costs a silent
    "no entries" for a project that has some.
    """
    if os.path.isdir(os.path.join(project, "project_memory")):
        return os.path.join(project, "project_memory")
    return project


def unharvested(project, harvest):
    """[(entry, already harvested?)] for one project, oldest first."""
    seen = harvest.get(project_key(project)) or {}
    return [(entry, seen.get(str(entry.get("id")))) for entry in entries_of(project)]


def entries_of(project):
    return gaplog.entries(state_root(project))


def report(projects):
    harvest = read_harvest()
    total, fresh = 0, 0
    for project in projects:
        rows = unharvested(project, harvest)
        total += len(rows)
        new = [entry for entry, mark in rows if not mark]
        fresh += len(new)
        print("\n%s -- %d entr%s, %d not yet triaged"
              % (project_key(project), len(rows), "y" if len(rows) == 1 else "ies", len(new)))
        for entry in new:
            print("  %s  %s  kit %s  item %s"
                  % (entry.get("id"), entry.get("ts") or "?", entry.get("kit_version") or "?",
                     entry.get("item") or "-"))
            print("      tried:   %s" % entry.get("tried"))
            print("      refused: %s" % entry.get("refused"))
    print("\n%d entr%s across %d project(s), %d not yet triaged."
          % (total, "y" if total == 1 else "ies", len(projects), fresh))
    # A non-zero exit for "there is something to do" is what makes this usable from a session start
    # or a cron line without parsing its output.
    return 1 if fresh else 0


def mark(project, entry_id, became):
    harvest = read_harvest()
    known = {str(entry.get("id")) for entry in entries_of(project)}
    if entry_id not in known:
        print("%s holds no entry %s (it has: %s)"
              % (project_key(project), entry_id, ", ".join(sorted(known)) or "none"),
              file=sys.stderr)
        return 1
    harvest.setdefault(project_key(project), {})[entry_id] = {"as": became or ""}
    write_harvest(harvest)
    print("marked %s in %s%s" % (entry_id, project_key(project),
                                 (" as " + became) if became else ""))
    return 0


def discovered():
    """Every immediate child of `$HARNESS_PROJECTS` that carries a state directory."""
    base = os.environ.get(PROJECTS_ENV) or ""
    if not base or not os.path.isdir(base):
        print("%s names no directory, so --all has nothing to walk. Give the project roots as "
              "arguments instead." % PROJECTS_ENV, file=sys.stderr)
        return []
    return [os.path.join(base, name) for name in sorted(os.listdir(base))
            if os.path.isdir(os.path.join(base, name, "project_memory"))]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("projects", nargs="*", help="project roots to read")
    parser.add_argument("--all", action="store_true",
                        help="read every project under $%s" % PROJECTS_ENV)
    parser.add_argument("--mark", nargs=2, metavar=("PROJECT", "ENTRY_ID"),
                        help="record that this repo has triaged that entry")
    parser.add_argument("--as", dest="became", default="",
                        help="the FR/BUG id the marked entry became")
    args = parser.parse_args(argv)
    if args.mark:
        return mark(args.mark[0], args.mark[1], args.became)
    # NO ARGUMENTS IS `--all`, and it exits 0 with nothing to report rather than erroring. Two
    # reasons, and the second is the one that decided it: a lead running this as a radar wants the
    # bare word to mean "everything I maintain", and this repo runs every tool in `tools/` with no
    # arguments as a check that it does not cache bytecode into the kit tree -- a tool that exits 2
    # there leaves the tree clean for the wrong reason and the check reads as green.
    projects = list(args.projects) or discovered()
    if args.all:
        projects = list(args.projects) + discovered()
    return report(projects)


if __name__ == "__main__":
    sys.exit(main())
