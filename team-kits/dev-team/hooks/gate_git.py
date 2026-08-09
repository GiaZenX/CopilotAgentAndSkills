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
has a current verdict from EVERY delivery-judging Evidence kind, and has no current verdict that is
a fail. "Current verdict of a kind" is the newest Evidence of that kind covering the item — see
`report.qa_verdicts` for why newest-wins rather than any-pass-wins, and for what "covering" means.
"Every kind" is `backlog_types.QA_EVIDENCE_KINDS`, read at run time and never listed here, so the
gate owes exactly what the kernel calls a delivery verdict.

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
    exists to protect. "No root item" means the directory answered; a canonical directory that
    exists and refuses to be listed is not an answer, and that predicate says so — otherwise a
    permission problem would switch off this gate and four others.
  * NO ITEM NAMED (no id in the command, none in the branch name) — the gate still applies, but
    it has nothing to bind evidence to, so it asks the weaker question the store can still answer:
    is anything currently failing, ANYWHERE. Refusing outright for the missing binding would block
    every push on a branch that is not named after an item, which is most of them; that would move
    the V1 blockage rather than remove it. Naming the item in the branch is what makes the gate
    specific — unnamed, a green run on one item does not silence another item's open FAIL, but
    neither does this gate know which of them the push carries.
    THE COMPLETENESS HALF IS NOT ASKED HERE, and the limit is stated rather than left to be
    discovered: with no item, "every kind has answered" has no subject, and demanding it per
    subject over the whole store would refuse every push while ANY item in the project is still
    mid-flight — the V1 blockage in a new spelling. So an unnamed merge is judged on open failures
    alone, which is strictly weaker than the named case. Naming the item is what buys the strict
    reading; nothing in this gate makes an unnamed push carry it.
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

# Force-push in every spelling. BOUND, not copied: this is `_compat.names_force_push` itself, and
# the name exists here because a gate should say under its own roof which rule it decides on. The
# definition moved out of this file because `gate_git` is not installed in the office kit, and a
# rule that kit also needs cannot live in a module it never runs — see `_compat.FORCE_PUSH_RX` for
# the two readings and for what the over-trigger costs.
names_force_push = _compat.names_force_push

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
            "changed in place leaves no item behind to notice. Archiving the failing Evidence is "
            "equally visible in git, but it retires a verdict without REPLACING it: the merge then "
            "opens only if an older passing Evidence of that same kind is left to become the "
            "current verdict, and with none left the kind is simply unanswered and this gate stays "
            "closed on that. So archiving belongs after a newer run, not instead of one. The proof "
            "itself goes under %s/staging/<task-id>/."
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
    """The main rule for ONE item: a current verdict of EVERY delivery-judging kind, none a fail.

    "Every kind" is `types.QA_EVIDENCE_KINDS`, asked of the kernel at run time. Not a tuple here,
    and that is the whole point of taking it from there: it is the same set
    `report._delivery_evidence` filters the store with, so a kind the kernel starts calling a
    delivery verdict is owed the day it exists, instead of becoming a verdict a role records in
    good faith and no merge ever waits for.

    WHY COMPLETENESS rather than "at least one". The kinds ask different questions — today,
    whether the work was read, whether the suite was run, whether the criteria were walked one by
    one — and under the weaker rule any one answer stood in for the others: a merge opened on a
    green test run that no reviewer had looked at, and on a reviewer's nod with no suite behind
    it. The QA/reviewer role skill of the kit this hook ships in is where the role is told which
    kinds it owes; this is the same demand at the moment it is collected.

    A `fail` is reported BEFORE an unanswered kind, so a role that has one of each is sent to fix
    the red verdict first and meets this refusal on the next attempt. Deliberate: the two are
    different work, and one message that mixed them would bury the failing verdict.

    WHAT IT DOES NOT REACH is decided one caller up in `main`: only a merge that NAMES a root item
    reaches this function at all (module docstring, NO ITEM NAMED).
    """
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
    unanswered = sorted(set(types.QA_EVIDENCE_KINDS) - set(verdicts))
    if unanswered:
        _kernel.block(
            HOOK,
            "QA has judged %s only in part — %s, and no %s Evidence covers it at all. Each kind "
            "answers a question the others do not, so a delivery merge rests on all of them (%s); "
            "an unanswered kind is work not finished, not a verdict to leave out."
            % (target, _describe(target, verdicts), "/".join(unanswered),
               ", ".join(sorted(types.QA_EVIDENCE_KINDS))),
            remedy="have the judging role record the missing verdict — one Evidence per kind, each "
                   "naming the run that produced it: `python scripts/harness.py evidence --kind "
                   "<test|review|acceptance> --result pass --related %s --summary ... "
                   "--artifact-ref <path to the raw proof>`. A kind that cannot be answered yet is "
                   "the merge arriving early; it is not this gate to route around." % target
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

    if (any(invocation.runs("push") for invocation in _compat.git_invocations(command))
            and names_force_push(command)):
        # NAMES NO SOURCE DOCUMENT, and that is structural rather than a wording taste. This file
        # is byte-identical in the dev and research kits (the mirror rule), so a refusal that cites
        # "the team constitution" cites a DIFFERENT text in each of them and can be wrong in one
        # while right in the other -- measured after II.11/3 redeemed parity licence 30 for dev:
        # the dev constitution stopped naming force-push and this message still sent its reader
        # there. The one document a refusal may point at is appended by `_compat.stop` from
        # `_compat.REFERENCE_NAME`, ships inside the hashed bundle beside this hook, and does name
        # force-push. So the message states the FACT and lets that pointer carry the authority.
        _kernel.block(HOOK, "force-push is refused: it rewrites history other clones already have.",
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
