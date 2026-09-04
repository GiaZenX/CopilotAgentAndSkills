"""Do two open work orders own a common file? -- the pre-dispatch check of DEC-0062 (1)/(2).

WHAT IT IS FOR. A generation is cut by FILE OWNERSHIP: every stream owns a disjoint set of files,
and two streams whose `allowed_scope`s reach the same file collide in the merge instead of in the
cut. That rule was carried by the orchestrator's reading alone. This is the reading made
mechanical, and it lives in the KERNEL rather than in a repo script because the three kits share
one kernel and a project reaches it through `scripts/harness.py check-scopes` -- measured by
stream D (`H136`): a script under a skill directory is rc 2 at `gate_write_scope`, so there is no
executable route out of a skill, and a copy per kit would be a fourth spelling of the predicate.

THE PREDICATE IS THE ONE THAT RUNS, and that is the whole point. `allowed_scope` is enforced by
`gate_write_scope`, whose `_matches` decides prefix-vs-glob, what `**` widens and what a single `*`
does NOT cross -- fed with both sides FOLDED through that module's own `_norm`, which is how the
gate really asks it. A second spelling here -- `fnmatch`, a hand-rolled regex, or the raw predicate
without the folding -- would answer a different question than the gate the specialists actually
meet, and the disagreement would show up as a collision nobody predicted. The measured case is the
folding: with `_matches` asked raw, `Tools/**` and `tools/**` came back DISJOINT while the gate
grants both orders the same files. So both halves are IMPORTED and asked.
`tools/test_parallel_scopes.py::test_the_matcher_is_the_shipped_gates_own_and_not_a_second_spelling`
reads the answer off the imported module rather than off this sentence.

TWO UNIVERSES, ONE PREDICATE. "In scope" is asked of paths, so the answer depends on which paths
exist. The check therefore asks it twice over the same predicate:

  * the REAL TREE (`git ls-files -c -o --exclude-standard`) -- every file that is there today; and
  * the WITNESSES of the two orders -- one concrete path per `allowed_scope` entry, its wildcards
    filled with a placeholder segment. A stream that will CREATE `src/api.py` owns nothing under
    `src/**` today, so the tree half is blind to two orders that both claim an empty directory;
    the witness half is not.

Neither half is complete on its own, and the incompleteness is measured rather than assumed: the
witness of `a/*x` does not match `a/y*` although `a/yx` lies in both, so a pair whose entries
overlap only in a region no witness lands in and no file exists in yet passes here (`H135` in
`docs/POST_V2_WISHLIST.md`, with the chain).

WHAT THIS REFUSES: nothing. It is a check a caller runs before it hands out work, and its answer is
an exit code. The refusal at dispatch time is a separate requirement that is NOT built here (C-2 in
stream D's protocol) -- named rather than implied, because a reader of a check command may
otherwise take it for a gate.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

from .backlog_types import field_elements, is_terminal
from .state import ProjectState

# WHAT A WILDCARD RUN BECOMES IN A WITNESS. One segment, because `**` matches any depth including a
# single segment and `*` matches inside one -- so a single placeholder satisfies both readings of
# an entry with no file behind it yet.
PLACEHOLDER = "_"
GATE = "gate_write_scope.py"
# The field a work order declares its SEAMS in (DEC-0062 (5), stream D requirement C-4). Spelled
# once, here, because three readers need it: the field contract, this check, and the printout.
SEAM_FIELD = "seam_scope"
# How many shared paths a pair prints before the list is cut. A cut list still decides the exit
# code; it is only the reading that is bounded.
PATHS_SHOWN = 10


class ScopeCheckError(RuntimeError):
    """The check could not run at all -- distinct from "the check ran and refused"."""


def _hooks_dir() -> str:
    """Where the shipped gate lives, relative to THIS kernel package.

    Anchored on the kernel rather than on the project tree, because the kernel is what is running:
    in a scaffolded project the two sit side by side under `.claude/`, and in the workshop
    checkout the kernel is `team-kits/kernel` while every kit carries its own `hooks/`. Both are
    found by asking where this file is, so no caller passes a path and no second layout rule
    exists.

    WHICH KIT'S COPY, in the workshop case, is not a choice: the file is mirrored byte-identical
    across the kits (`tools/test_hooks.py::test_shared_kit_files_identical`, and
    `KIT_SPECIFIC_HOOKS` does not name it), so the first one found answers for all three.
    """
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    installed = os.path.join(parent, "hooks")
    if os.path.isfile(os.path.join(installed, GATE)):
        return installed
    if os.path.isdir(parent):
        for entry in sorted(os.listdir(parent)):
            candidate = os.path.join(parent, entry, "hooks")
            if os.path.isfile(os.path.join(candidate, GATE)):
                return candidate
    raise ScopeCheckError(
        "no %s next to this kernel (%s), so the path predicate the specialists really meet cannot "
        "be asked. Remedy: run this from a scaffolded project or from the kit checkout; a second "
        "spelling of the predicate would answer a different question than the gate does."
        % (GATE, parent))


def _shipped_halves():
    """(`_matches`, `_norm`, the file both came from) -- imported, never restated.

    TWO HALVES, because the gate's answer is made of two: `_matches` decides prefix-vs-glob, and
    `_norm` is what both sides have been folded with before it ever sees them (`_scope_entries`
    folds every entry, `_repo_relative(fold=True)` folds the path). Taking only the first was a
    measured hole in this file: `Tools/**` and `tools/**` came back DISJOINT while the gate grants
    both orders the same files on a case-insensitive filesystem.
    """
    hooks = _hooks_dir()
    if hooks not in sys.path:
        sys.path.insert(0, hooks)
    import gate_write_scope
    return gate_write_scope._matches, gate_write_scope._norm, os.path.join(hooks, GATE)


def matcher():
    """(the predicate as the GATE asks it, the file it came from).

    A wrapper and not the bare `_matches`, for the reason `_shipped_halves` gives: the gate never
    calls its predicate on unfolded text, so a caller that does is asking a question the gate does
    not answer. Both sides go through the shipped `_norm` first, in the shipped order.
    `tools/test_parallel_scopes.py::test_the_matcher_is_the_shipped_gates_own_and_not_a_second_spelling`
    reads the two halves off the module and then measures the folded pair.
    """
    matches, norm, gate = _shipped_halves()

    def folded(path, entry):
        return matches(norm(path), norm(entry))

    return folded, gate


def scope_entries(item: dict, field: str) -> list:
    """The entries of one scope field, folded the way the gate folds them.

    `field_elements` and not a list comprehension over the raw value: a scope written as a bare
    string is ONE entry to the kernel (BUG-0015), and this has to count it the same way.

    Blank, `.` and `*` are DROPPED rather than read as "everything": the gate refuses an order
    carrying one, so such an order is broken before this check has an opinion -- and reading it as
    the whole repository here would report an overlap the gate would never let happen.

    THE FOLD BELONGS HERE AND NOT ONLY IN `matcher`, because entries are compared to each other and
    not only to paths: `pair_seam` intersects two orders' `seam_scope` as plain strings, so an
    order declaring `Docs/**` and one declaring `docs/**` had NO seam in common. That failed
    closed -- the pair was reported as an overlap -- but the reader was told "you collide" instead
    of "your seam is spelled two ways", which is a different repair. Folding all three fields at
    the door makes one spelling of a path one entry everywhere in this module.
    `tools/test_parallel_scopes.py::test_a_seam_the_two_orders_spell_differently_is_still_one_seam`.
    """
    _matches, norm, _gate = _shipped_halves()
    entries = []
    for raw in field_elements(item.get(field)):
        entry = norm(str(raw))
        while entry.startswith("./"):
            entry = entry[2:]
        entry = entry.strip().rstrip("/")
        if entry in ("", ".", "*"):
            continue
        entries.append(entry)
    return entries


def in_scope(matches, order: dict, path: str) -> bool:
    """The one predicate: inside `allowed_scope`, outside `forbidden_scope`.

    The order of the two follows the gate: `forbidden_scope` is asked first there, so a path a work
    order forbids itself is not owned by it however wide its allowance is.
    """
    if any(matches(path, entry) for entry in order["forbidden"]):
        return False
    return any(matches(path, entry) for entry in order["allowed"])


def witnesses(entries) -> list:
    """One concrete path per scope entry -- what the entry would own if the tree were empty.

    THE LIMIT, because a witness is a sample and not the language: `a/*x` yields `a/_x`, which no
    longer matches `a/y*` although `a/yx` satisfies both. Two orders overlapping only in such a
    region, over files that do not exist yet, pass this half (`H135`).
    """
    return [re.sub(r"\*+", PLACEHOLDER, entry) for entry in entries]


def tracked_files(tree: str) -> list:
    """Every file git carries or would carry -- the real universe the scopes resolve against.

    `-c -o --exclude-standard`: cached AND untracked-but-not-ignored, because a file a stream has
    already created is as much a collision as a committed one, while an ignored build product is
    nobody's ownership. A tree git cannot answer for yields NO files rather than an exception --
    the witness half still decides, and a project without git is not a project without a cut.
    """
    try:
        result = subprocess.run(["git", "ls-files", "-c", "-o", "--exclude-standard"],
                                cwd=tree, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def open_orders(state: ProjectState, only=None) -> list:
    """Every work order that is not in a terminal status, read through the kernel's own contract.

    "Open" is `backlog_types.is_terminal` and not a list of status words: a cut is judged BEFORE
    the dispatch, so a DRAFT order counts exactly as much as a LEASED one -- both are work somebody
    is about to hand out. `--only` overrides the status filter, because a caller naming two ids is
    asking about those two whatever they are.
    """
    orders = []
    for stem, path in state.iter_active_items("TSK"):
        try:
            item = state._read_yaml(path)
        except Exception:  # noqa: BLE001 -- an unreadable order is the validator's finding
            continue
        if not isinstance(item, dict) or not item.get("id"):
            continue
        if only:
            if item["id"] not in only:
                continue
        elif is_terminal("TSK", str(item.get("status") or "")):
            continue
        orders.append({
            "id": str(item["id"]),
            "allowed": scope_entries(item, "allowed_scope"),
            "forbidden": scope_entries(item, "forbidden_scope"),
            "seam": scope_entries(item, SEAM_FIELD),
        })
    return sorted(orders, key=lambda order: order["id"])


def pair_seam(first: dict, second: dict, declared=()) -> list:
    """The entries that count as SHARED ON PURPOSE for this pair.

    BOTH ORDERS HAVE TO SAY SO, and that is the fail-closed reading rather than a strictness for
    its own sake: a seam is a file no stream can own alone (DEC-0062 (5)). If only one order
    declares `docs/**` and the other simply owns it, the second one was cut believing the file was
    its own -- which is exactly the surprise the seam table exists to prevent. So a one-sided
    declaration leaves the pair overlapping, and the printout shows why.
    `tools/test_parallel_scopes.py::test_a_seam_only_one_of_the_two_declares_is_not_a_seam`.

    A CALLER MAY ALSO DECLARE ONE, and that is a different statement rather than a second route to
    the same one: the items carry the cut a project has already written down, while the argument is
    the orchestrator asking "what if these three were the seam" before any item says so. It applies
    to every pair, which is what makes it an answer about the CUT and not about one order.
    """
    return sorted(set(first["seam"]) & set(second["seam"]) | set(declared))


def owns_anything_outside(matches, order: dict, files, seam) -> bool:
    """Does this order still own a path once the seam is taken away?

    THE LIMIT OF A DECLARATION, and it is a property rather than a shape. A seam is what two
    streams share ON PURPOSE and apply in the merge; it is not a way of declaring the collision
    away. `seam_scope: ["**"]` -- or `--seam **` -- matches every path either order owns, so every
    collision becomes "seam only" and the check reports rc 0 on a cut that is entirely shared.
    What separates the two cases is not how the entry is spelled (`**`, `team-kits/**`, a list of
    every entry the order has) but whether the order is left owning ANYTHING of its own. That also
    keeps the legitimate seam legitimate: an order owning `team-kits/kernel/**` and declaring
    `team-kits/*/VERSION` still owns the kernel afterwards.
    `tools/test_parallel_scopes.py::test_a_seam_that_leaves_an_order_owning_nothing_is_refused`
    holds both ends.

    WHAT THIS QUESTION DOES NOT REACH: a seam NARROWER than the overlap. It leaves both orders
    owning something, so it passes here while still covering part of a real collision -- `H143` in
    `docs/POST_V2_WISHLIST.md`, with the measurement. The routes that end without comparing
    anything at all -- one open order, or a `--only` that names exactly one -- are `H142`.
    """
    for path in list(files) + witnesses(order["allowed"]):
        if in_scope(matches, order, path) and not any(matches(path, entry) for entry in seam):
            return True
    return False


def overlaps(matches, orders, files, declared=()) -> list:
    """[{a, b, files, witnesses, seam, swallowed}] for every pair that shares a path.

    A SEAM IS SUBTRACTED, NOT IGNORED: both halves are reported, and only the undeclared half
    decides the verdict. A pair that shares nothing at all does not appear here.

    A SEAM THAT SWALLOWS AN ORDER IS NOT SUBTRACTED AT ALL (`owns_anything_outside`): the pair is
    then reported with everything it shares, because a declaration that leaves one side owning
    nothing is not a seam -- it is the whole scope handed over, and the check would otherwise say
    `disjoint` about a cut that is entirely shared. The seam this cannot reach -- one NARROWER than
    the overlap -- is `H143` in `docs/POST_V2_WISHLIST.md`.
    """
    real = set(files)
    found = []
    for index, first in enumerate(orders):
        for second in orders[index + 1:]:
            seam = pair_seam(first, second, declared)
            swallowed = [order["id"] for order in (first, second)
                         if seam and not owns_anything_outside(matches, order, files, seam)]
            effective = () if swallowed else seam
            universe = list(files) + witnesses(first["allowed"] + second["allowed"])
            shared_files, shared_witnesses, shared_seam = set(), set(), set()
            for path in universe:
                if not (in_scope(matches, first, path) and in_scope(matches, second, path)):
                    continue
                if any(matches(path, entry) for entry in effective):
                    shared_seam.add(path)
                elif path in real:
                    shared_files.add(path)
                else:
                    shared_witnesses.add(path)
            if shared_files or shared_witnesses or shared_seam:
                found.append({"a": first["id"], "b": second["id"],
                              "files": sorted(shared_files), "witnesses": sorted(shared_witnesses),
                              "seam": sorted(shared_seam), "swallowed": swallowed})
    return found


def check(state: ProjectState, only=None, declared=()) -> tuple:
    """Run the check: `(exit code, [lines])`.

    THREE OUTCOMES AND THEY NEVER SHARE A WORD. Nothing to compare is not "disjoint" -- a missing
    state directory, a task tray with one open order and a mistyped `--root` all land there, so the
    line says that nothing was measured rather than that everything was fine
    (`tools/test_parallel_scopes.py::test_a_state_with_nothing_to_compare_never_says_disjoint`).
    """
    matches, gate = matcher()
    orders = open_orders(state, set(only or ()) or None)
    if len(orders) < 2:
        return 0, ["%d open work order(s) under %s -- NOTHING WAS COMPARED."
                   % (len(orders), state.root)]
    tree = os.path.dirname(os.path.abspath(state.root))
    files = tracked_files(tree)
    lines = ["matcher: %s | %d open orders | %d files in the tree"
             % (gate, len(orders), len(files))]
    undeclared = 0
    for pair in overlaps(matches, orders, files, declared):
        collides = bool(pair["files"] or pair["witnesses"])
        undeclared += 1 if collides else 0
        lines.append("%s %s x %s" % ("OVERLAP" if collides else "seam only", pair["a"], pair["b"]))
        for path in pair["files"][:PATHS_SHOWN]:
            lines.append("    file      %s" % path)
        for path in pair["witnesses"][:PATHS_SHOWN]:
            lines.append("    witness   %s  (no such file today -- both scopes would own it)"
                         % path)
        for path in pair["seam"][:PATHS_SHOWN]:
            lines.append("    seam      %s  (declared by BOTH orders -- applied in the merge round)"
                         % path)
        for order_id in pair["swallowed"]:
            lines.append("    NOT A SEAM: the declaration leaves %s owning nothing of its own, so "
                         "it hands the whole scope over rather than sharing a file" % order_id)
    if not undeclared:
        lines.append("disjoint: no pair of open orders owns a common path outside the declared "
                     "seam.")
        return 0, lines
    lines.append(
        "refused: %d overlapping pair(s). Group them into ONE order with one owner, move the "
        "shared files out of one of the two scopes, or declare them in `%s` on BOTH orders "
        "(DEC-0062 (1)/(2)/(5))." % (undeclared, SEAM_FIELD))
    return 2, lines

