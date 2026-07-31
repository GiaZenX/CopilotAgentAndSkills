#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell) gate — protects merge and push.

Two teeth, answering different questions.

FORCE-PUSH is refused unconditionally. The constitution forbids rewriting published history and
no project state can make it right, so this half decides before anything is read.

MERGE/PUSH NEEDS QA EVIDENCE — and in V2 that is a different sentence than it was. V1 looked for
`project_memory/*report*.yaml`, i.e. "whichever report file happens to be there", and matched
text inside it. Nothing in V2 writes such a file, so the gate had stopped being a QA rule and had
become an unconditional block on every merge and push in a scaffolded project (measured; phase-0
disposition rows 115/338/507). V2 has a typed store for exactly this question — Evidence
(spec II.2: a test/review/acceptance/audit record that carries no project status of its own),
living in `kernel.backlog_types.ACTIVE_DIRS["EVD"]` — and `kernel.report` is the ONE definition of
what that store SAYS. What this gate adds is only the DECISION taken on it (below); reading the
store for itself would give the harness two answers to the question the harness and CI must answer
the same way.

THE RULE, in one sentence: the merge opens when every item it is about could still be delivered,
has a current verdict from at least one delivery-judging Evidence kind, and has no current verdict
that is a fail. "Current verdict of a kind" is the newest Evidence of that kind covering the item
— see `report.qa_verdicts` for why newest-wins rather than any-pass-wins, and for what "covering"
means.

WHAT THE MERGE IS ABOUT is every root item the git invocation NAMES, and the gate requires all of
them rather than picking one. Picking would need a rule for which token is the ref being merged,
i.e. knowledge of which options carry a value, and that rule is one option away from wrong: the
first cut read the first id anywhere in the raw command, so `git merge -m "see PR-0002"
feat/PR-0001-x` judged PR-0002 and merged a failing PR-0001 (measured, audit finding of round 7).
Requiring every named item is the fail-closed reading of the same text: a merely mentioned id adds
a requirement, it can never substitute for one. Which text that reading is taken over is decided
by shell syntax rather than by a word list, and `_compat.git_argument_text` is that definition: a
`#` comment and everything past a `&&`/`|`/`;` was never handed to this git command, while a
QUOTED span WAS — quoting changes how the shell splits words, not what git receives, so the ref in
`git merge "feat/PR-0001-x"` counts exactly as the bare spelling does. (There was once a second
reader that deleted quoted spans as prose to answer "is this line a git invocation at all";
borrowing it for THIS question unbound every quoted merge, and answering the OTHER question with
it deleted the verb — `git "push" --force origin main` matched no gate whatsoever. Both are gone:
applicability is now read off the SUBCOMMAND, `_compat.git_invocations`.) A ref the shell only
builds at run time (`git merge "$B"`) is one no reading of the text can resolve, so it widens the
search to the whole line instead of being read as "this merge names nothing".

Every tooth the V1 gate had is kept, including the false accept an audit found — an old PASS for
another item together with a fresh FAIL for this one lifting the gate. That was possible because
binding was a text match inside one shared file. In V2 each Evidence is its own item with a
`related` field, so once an item could be determined, evidence for another item is not read as
evidence for this one. The qualifier is load-bearing: when NO item could be determined the gate
falls back to the whole store (below), and there the binding is only as specific as the branch
name.

Two situations are handled deliberately rather than by the main rule:
  * NO ROOT ITEM YET (`_root.has_root_item`) — the gate does not apply at all. A repo before
    its first PR/RQ is still being set up, and a quality gate firing there blocks the setup it
    exists to protect.
  * NO ITEM NAMED (no id in the command, none in the branch name) — the gate still applies, but
    it has nothing to bind evidence to, so it asks the weaker question the store can still answer:
    is anything currently failing, ANYWHERE. Refusing outright for the missing binding would block
    every push on a branch that is not named after an item, which is most of them; that would move
    the V1 blockage rather than remove it. Naming the item in the branch is what makes the gate
    specific — unnamed, a green run on one item does not silence another item's open FAIL, but
    neither does this gate know which of them the push carries.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _kernel
except BaseException as exc:  # noqa: BLE001 — a hook that cannot load must not mean "allow"
    sys.stderr.write("[team-kit hook] refused: could not load hook helpers (%r). Remedy: run "
                     "`python scripts/harness.py doctor`; a partial checkout or half-finished kit update is the "
                     "usual cause.\n" % (exc,))
    sys.exit(2)

import re  # noqa: E402

import _compat  # noqa: E402
import _root  # noqa: E402

HOOK = "gate_git"

# The item a merge/push can be ABOUT: a root item id, spelled in the command or in the branch
# name. Assembled from `_root.ROOT_ITEM_TYPES`, so a kit that introduces a root type reaches this
# gate with it instead of leaving a third place for someone to remember. `\d{4,}` is the id
# convention (`kernel.backlog_types.parse_id`) — which is also what stops a leftover V1 `PRD-0001`
# branch from half-matching and being treated as a `PR`.
TARGET_RX = re.compile(r"\b(?:%s)-\d{4,}\b" % "|".join(_root.ROOT_ITEM_TYPES), re.IGNORECASE)

# Force-push in every spelling: the flags AND the `+refspec` form (`git push origin +main`).
# Matched on the NORMALISED view (`_compat.git_argument_text`) and on the raw command, and each
# check catches what the other cannot. The NORMALISED one carries the spellings that only become
# `--force` once the shell is done with them: a flag broken over a line continuation
# (`--f\<newline>orce`), the PowerShell escape (`--for`ce` — measured ALLOW as a real hook process
# with tool_name PowerShell), a flag assembled out of adjacent quoted pieces (`--fo''rce`). The
# RAW one is the belt for the opposite risk — a normaliser may drop characters, it may never
# invent them — and it is what already covered the quoted flags (`git push "--force"`, `"+main"`),
# because the pattern's own `["']` alternatives match those in the raw text. Over-triggering is
# acceptable for an action that is forbidden either way.
FORCE_RX = re.compile(r"--force(-with-lease)?|(^|[\s\"'])-f([\s\"']|$)|[\s\"']\+[\w./-]+(:|[\s\"']|$)")

# A ref the shell EXPANDS at run time — `$B`, `${B}`, `$(git …)`, `$env:B`, `%B%` — is a ref this
# gate cannot read, and "cannot read" must not become "names nothing". Seeing one means the item is
# spelled somewhere the segment does not show, so the search widens to the whole line, where
# `B=feat/PR-0001-x; git merge "$B"` does spell it. Widening only ADDS requirements, which is the
# same fail-closed direction as collecting every named id in the first place.
EXPANSION_RX = re.compile(r"\$\w|\$\{|\$\(|%\w+%")


def target_items(command, repo_root):
    """Every root item this merge/push is about, as a sorted list; empty when it names none.

    Read from the git invocation — see the module docstring for why this collects rather than
    picks, and why the reading keeps quoted argument text. The command wins over the branch:
    `git merge feat/PR-0002-x` run while standing on `feat/PR-0001-x` is about PR-0002, and reading
    the branch first would judge the wrong item. The branch is consulted only when the command
    names nothing at all.
    """
    text = _compat.git_argument_text(command)
    named, unresolved = set(), False
    for invocation in _compat.git_invocations(command):
        if invocation.runs("push", "merge"):
            named.update(match.group(0).upper()
                         for match in TARGET_RX.finditer(invocation.segment))
            unresolved = unresolved or EXPANSION_RX.search(invocation.segment) is not None
    if unresolved:
        named.update(match.group(0).upper() for match in TARGET_RX.finditer(text))
    if not named:
        try:
            branch = _compat.run_captured(
                ["git", "-C", repo_root, "rev-parse", "--abbrev-ref", "HEAD"], timeout=5).stdout
        except Exception:  # noqa: BLE001 — no git, detached head, timeout: simply no branch name
            branch = ""
        named.update(match.group(0).upper() for match in TARGET_RX.finditer(branch or ""))
    return sorted(named)


def _describe(subject, verdicts):
    return "%s: %s" % (subject, ", ".join(
        "%s %s (%s)" % (kind, verdicts[kind]["result"], verdicts[kind]["id"])
        for kind in sorted(verdicts)))


# Every remedy below hands a blocked role a command line, and since the entry point shipped that
# command line RUNS: the scaffold installs `scripts/harness.py` kit-owned in every project
# (`kernel.cli.ENTRY_POINT`), and `python scripts/harness.py evidence ...` was measured recording
# an Evidence through all eight PreToolUse gates and opening the merge this gate had closed. What
# this constant used to carry — that no installation provided the command — came out with the
# shim. What replaces it is the only thing the command still needs from the role: WHERE to run it
# and which argument not to add. Both halves are measured refusals, not caution.
_FROM_THE_ROOT = (
    " Run it from the project root: the entry point resolves the state directory itself, and a "
    "`--root` argument is refused twice over — by `gate_write_scope`, because a write-capable "
    "pipeline that NAMES the state directory is refused, and by the entry point, which reads the "
    "flag off its own parser and says so.")


def _evidence_home(types):
    return "%s/%s" % (_kernel.STATE_DIRNAME, types.ACTIVE_DIRS["EVD"])


def _remedy(target):
    return ("fix what the Evidence names, then have QA record the re-run (`python scripts/harness.py evidence "
            "--kind <test|review|acceptance> --result pass --related %s --summary ... "
            "--artifact-ref <path to the raw proof>`). Recording the newer verdict is what "
            "supersedes the old one — the kernel refuses to EDIT an Evidence, because a verdict "
            "changed in place leaves no item behind to notice. Archiving the failing Evidence "
            "lifts this gate too and is equally visible in git, but it retires a verdict without "
            "replacing it, so it belongs after a newer run, not instead of one. The proof itself "
            "goes under %s/staging/<task-id>/."
            % (target or "<ITEM-ID>", _kernel.STATE_DIRNAME)) + _FROM_THE_ROOT


def _refuse_a_status_no_delivery_can_follow(state, types, target):
    """Refuse a merge ABOUT an item whose own automaton says there is no delivery to merge.

    The type-appropriate half of the binding (disposition rows 115/343: "branch↔item + a status
    appropriate to the TYPE"). Which statuses those are is read off the item's automaton instead
    of being named here, so a kit that adds a root type brings the rule with it:

    * the INITIAL status is the draft in which the item is still being written. Nothing has
      authorised work on it — the dispatch gate will not even lease a task for it — so a merge
      claiming to deliver it is delivering something the project has not agreed to.
    * a TERMINAL status that is NOT the end of the chain is a life that ended without delivery
      (REJECTED, SUPERSEDED). The project decided against this work; merging it ships what was
      dropped. The chain's own last status is the opposite case — the delivery having been
      accepted — so a later fix merged against it is legitimate and is left alone.

    An id that names no item is not judged here: it binds to nothing, which is precisely what the
    evidence half below refuses it for, with the more useful message.
    """
    item, _archived = state.read_anywhere(target)
    if not isinstance(item, dict):
        return
    try:
        item_type, _number = types.parse_id(target)
    except ValueError:
        return
    automaton = types.AUTOMATA.get(item_type)
    if automaton is None:
        return
    status = item.get("status")
    if status == automaton.initial:
        _kernel.block(
            HOOK,
            "%s is still %s — nothing has approved this work, so there is no delivery to merge."
            % (target, status),
            remedy="obtain the user's approval for %s first (`python scripts/harness.py "
                   "request-approval scope %s`, relay the question verbatim) — the MINT walks "
                   "this transition itself, so there is no `transition` to run afterwards and the "
                   "kernel refuses one. If this merge is not about %s, name the item it IS about "
                   "in the branch." % (target, target, target))
    if status in automaton.terminals and status != automaton.chain[-1]:
        _kernel.block(
            HOOK,
            "%s is %s — the project closed this item without delivering it, so merging it ships "
            "work that was dropped." % (target, status),
            remedy="if the decision changed, that is a new item (a `CR` against the root, or a "
                   "fresh root item) — a reopened terminal status is not a transition the "
                   "automaton has. If this merge is about something else, name that item in the "
                   "branch.")


def _refuse_unless_the_item_is_green(types, target, verdicts):
    """The main rule for ONE item: at least one current verdict, and none of them a fail."""
    failing = {kind: entry for kind, entry in verdicts.items() if entry["result"] != "pass"}
    if failing:
        _kernel.block(
            HOOK,
            "the current QA verdict is not a pass — %s. A newer Evidence of the same kind "
            "supersedes an older one, so this is what QA says about the work RIGHT NOW."
            % _describe(target, failing),
            remedy=_remedy(target))
    if not verdicts:
        _kernel.block(
            HOOK,
            "no QA Evidence for %s — nothing in %s judges this work, so there is no proof to "
            "merge on (spec II.10a: a partial run is not merge evidence either)."
            % (target, _evidence_home(types)),
            remedy="run the QA gate and have the reviewing role record the outcome as an Evidence "
                   "item: `python scripts/harness.py evidence --kind <test|review|acceptance> --result pass "
                   "--related %s --summary ... --artifact-ref <path to the raw proof>`." % target
                   + _FROM_THE_ROOT)


def _refuse_unless_nothing_is_failing(types, by_subject):
    """The fallback for a merge that named no item: no OPEN failure anywhere in the store.

    Per (item, kind), never collapsed to one newest-per-kind for the whole project. Collapsing
    would rebuild the V1 false accept out of typed items: the newest verdict in the store is some
    item's, and if it is green it would speak for an unrelated item whose own FAIL is still open.
    Since this branch cannot tell which item the push carries, the only honest reading is that
    every open failure counts against it.
    """
    failing = {}
    for subject, verdicts in by_subject.items():
        for kind, entry in verdicts.items():
            if entry["result"] != "pass":
                failing.setdefault(subject, {})[kind] = entry
    if failing:
        _kernel.block(
            HOOK,
            "this merge names no item — not in the command and not in the branch — so the gate "
            "cannot tell which work it carries, and QA currently reports a failure: %s."
            % "; ".join(_describe(subject, failing[subject]) for subject in sorted(failing)),
            remedy="name the item in the branch (`feat/PR-0001-…`) so the gate judges that item "
                   "alone, or clear the failing verdict by recording the re-run "
                   "(`python scripts/harness.py evidence --kind <test|review|acceptance> --result pass --related "
                   "<ITEM-ID> --summary ... --artifact-ref <path to the raw proof>`)."
                   + _FROM_THE_ROOT)
    if not by_subject:
        _kernel.block(
            HOOK,
            "no QA Evidence in this project — nothing in %s judges any work, so there is no "
            "proof to merge on (spec II.10a: a partial run is not merge evidence either)."
            % _evidence_home(types),
            remedy="run the QA gate and have the reviewing role record the outcome as an Evidence "
                   "item: `python scripts/harness.py evidence --kind <test|review|acceptance> --result pass "
                   "--related <ITEM-ID> --summary ... --artifact-ref <path to the raw proof>`; "
                   "name the item in the branch too, so the next merge is judged on it alone."
                   + _FROM_THE_ROOT)


def main():
    # No `hook_event_name` guard: this gate is registered on PreToolUse and nowhere else, so the
    # event is settled by settings.json. Re-checking a field a provider may omit would turn the
    # gate into a silent exit 0.
    data = _kernel.payload(HOOK)
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        sys.exit(0)
    command = str((data.get("tool_input") or {}).get("command") or "")
    # Detection lives in _compat.wants_push_or_merge (single home): applicability is decided on the
    # git SUBCOMMAND of a `git` word the shell would execute, so `git "push"`, `git pu''sh`,
    # `git pu\<newline>sh`, `git $'push'` and `sudo "git" push` are the push they are, a verb the
    # shell only builds at run time counts as every verb, and `git commit -m "merge later"` stays
    # a commit because its `merge` is inside an argument, not a word git was handed.
    if not _compat.wants_push_or_merge(command):
        sys.exit(0)

    text = _compat.git_argument_text(command)
    if (any(invocation.runs("push") for invocation in _compat.git_invocations(command))
            and (FORCE_RX.search(text) or FORCE_RX.search(command.lower()))):
        _kernel.block(HOOK, "force-push is forbidden by the team constitution.",
                      remedy="push without --force; if history really has to be rewritten, that "
                             "is a user decision, not a task decision.")

    repo_root = _kernel.find_repo_root(data.get("cwd"))
    if not os.path.isdir(_kernel.state_dir(repo_root)):
        sys.exit(0)  # nothing to gate yet
    if not _root.has_root_item(repo_root):
        sys.exit(0)

    state = _kernel.open_state(repo_root)
    report = _kernel.kernel_module("report", repo_root)
    types = _kernel.kernel_module("backlog_types", repo_root)
    targets = target_items(command, repo_root)

    for target in targets:
        _refuse_a_status_no_delivery_can_follow(state, types, target)
    if targets:
        for target in targets:
            _refuse_unless_the_item_is_green(types, target, report.qa_verdicts(state, target))
    else:
        _refuse_unless_nothing_is_failing(types, report.qa_verdicts_by_subject(state))
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
