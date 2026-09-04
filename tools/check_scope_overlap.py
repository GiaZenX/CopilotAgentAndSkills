#!/usr/bin/env python3
"""Do two open work orders own a common file? -- the workshop command line for `check-scopes`.

WHAT IT IS FOR. A generation is cut by FILE OWNERSHIP: every stream owns a disjoint set of files,
and two streams whose `allowed_scope`s reach the same file collide in the merge instead of in the
cut. This is the orchestrator's route to that reading in THIS repo, which carries no installed kit
and therefore no `scripts/harness.py`.

IT CARRIES NO PREDICATE. Generation 3 built the reading twice -- here, and as `kernel.scopes`
behind `harness.py check-scopes` -- and the TSK-0120 merge round kept the kernel's: a project
reaches it, a customer has it, and two bodies of one rule are two things to keep in step. What is
left in this file is a command line and the two rules a command line needs: what the caller SPELLED
OUT has to resolve, and what nobody spelled out is not an error. Everything else is imported and
asked. `tools/test_parallel_streams.py::test_the_workshop_tool_carries_no_predicate_of_its_own`
reads that off the parsed file rather than off this sentence.

WHERE TO READ THE RULE ITSELF: `team-kits/kernel/scopes.py`. Its module head carries the two
universes (the real tree and one witness per scope entry), why the matcher is the shipped gate's
own and not a second spelling, what a seam is and when a declaration stops being one, and the
residues `H135`, `H142` and `H143`.

USAGE
    python tools/check_scope_overlap.py [--root project_memory] [--only TSK-0001 TSK-0002]
                                        [--seam docs/** tools/**]
    exit 0 -- every pair of open orders is disjoint, OR there was no pair to compare (the two say
              so in different words; "disjoint" is never printed for an empty state directory)
    exit 2 -- at least one pair shares a file or a witness outside the seam -- including the pair
              whose declared seam would leave one order owning nothing, because that declaration is
              not a seam and the collision stands
    exit 1 -- the check could not do what the CALLER SPELLED OUT: no shipped kernel to ask, a
              `--root` that was named and does not exist, or an id `--only` named and no order
              carries. What nobody named is not an error: run with no arguments outside a project
              and the answer is "nothing was compared", 0.
"""
import argparse
import os
import sys

# NO BYTECODE IN THE KIT TREE. This imports the shipped gate and the kernel out of `team-kits/`,
# and `kernel.hashing` may leave `__pycache__` out of what a kit contains only because a kit ships
# none -- a tool that caches there makes that exclusion untrue at its source.
# `tools/test_hooks_v2.py::test_a_repo_tool_that_imports_the_kit_tree_leaves_no_bytecode_in_it`
# runs this file as a process and measures it.
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _kernel(tree):
    """The `kernel.scopes` module for this run, and where its kernel came from.

    A scaffolded project carries `.claude/kernel`; the workshop repo carries `team-kits/kernel` and
    no installed kit at all (the state `CLAUDE.md` explains). Both are asked for the SAME module,
    so the instrument runs in either place without a switch in the caller -- and the module finds
    the gate beside its own kernel, so nothing here passes it a hooks path.
    """
    for parent in (os.path.join(tree, ".claude"), os.path.join(ROOT, "team-kits")):
        if os.path.isfile(os.path.join(parent, "kernel", "scopes.py")):
            if parent not in sys.path:
                sys.path.insert(0, parent)
            from kernel import scopes
            return scopes, parent
    raise SystemExit("no kernel/scopes.py under %s or %s/team-kits"
                     % (os.path.join(tree, ".claude"), ROOT))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=None,
                        help="the state directory (default: project_memory)")
    parser.add_argument("--only", nargs="*", default=None,
                        help="check exactly these order ids, whatever their status")
    parser.add_argument("--seam", nargs="*", default=(),
                        help="scope entries declared as SEAMS for THIS run: shared on purpose, "
                             "applied in the merge round. A seam BOTH orders carry in their own "
                             "`seam_scope` needs no flag.")
    args = parser.parse_args(argv)

    named = set(args.only or ())
    state_dir = os.path.abspath(args.root if args.root is not None else "project_memory")
    tree = os.path.dirname(state_dir)
    scopes, _parent = _kernel(tree)
    # WHAT THE CALLER SPELLED OUT HAS TO RESOLVE, and what nobody spelled out does not. A `--root`
    # or an `--only` in the command line is a claim that something is there; answering it with the
    # same 0 that a clean cut gets is how a mistyped path reads as a pass. The DEFAULT root in a
    # directory that is not a project is nobody's claim -- that is the tool being run outside a
    # project, and it stays 0 (`tools/test_hooks_v2.py::
    # test_a_repo_tool_that_imports_the_kit_tree_leaves_no_bytecode_in_it` runs it exactly so).
    # THIS IS THE WHOLE OF WHAT THIS FILE STILL DECIDES ON ITS OWN: it is the reading of a command
    # line, and the kernel verb has no command line. Everything below the argument handling is
    # `kernel.scopes`, asked and printed.
    if args.root is not None and not os.path.isdir(state_dir):
        print("--root names %s and there is no such directory -- nothing could be compared."
              % state_dir)
        return 1
    if not os.path.isdir(state_dir):
        print("0 open work order(s) under %s -- NOTHING WAS COMPARED." % state_dir)
        return 0
    from kernel.state import ProjectState
    state = ProjectState(state_dir)
    if named:
        carried = {order["id"] for order in scopes.open_orders(state, named)}
        missing = sorted(named - carried)
        if missing:
            print("--only names %s and no work order under %s carries %s -- nothing could be "
                  "compared." % (", ".join(sorted(named)), state_dir, ", ".join(missing)))
            return 1
    try:
        code, lines = scopes.check(state, named or None, list(args.seam))
    except scopes.ScopeCheckError as exc:
        print(str(exc))
        return 1
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
