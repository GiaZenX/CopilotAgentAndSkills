"""The harness CLI -- the command surface the fail-closed remedies point at (II.4).

Thin argparse wrapper over the kernel API. Exit codes: 0 = ok, 1 = findings/
refusal (message explains), 2 = usage error.

IN A SCAFFOLDED PROJECT THIS MODULE IS NOT WHAT A ROLE RUNS. The scaffold installs
`scripts/harness.py` (ENTRY_POINT below), and the one sanctioned spelling is
`python scripts/harness.py <cmd>` -- identical in bash and PowerShell, which are
gated by the same eight PreToolUse hooks. That shim resolves `--root` itself and
refuses it on the command line, because `gate_write_scope` refuses any pipeline
that can write and whose COMMAND LINE names the state directory or `.claude`
(measured: `python -B .claude/kernel/cli.py doctor` -> "names the enforcement
layer"). `prog` below is that spelling, so every usage and error line argparse
prints is a line a role can retype.

BEFORE a kit is installed there is no shim, and the entry gate that writes the
first item reaches the module directly, with the kit staging on the import path:
`python -B -m kernel.cli <cmd>`. That form works only from there -- an installed
project has the kernel at `.claude/kernel`, where it raises `No module named
'kernel'` (measured) -- so it is documented for the installer position and
nowhere else. The two global entry-gate files spell the same line with an
explicit `PYTHONPATH` prefix, which is the only thing that puts the staging on
that path.

THE `-B` IS NOT DECORATION AND MUST TRAVEL WITH EVERY COPY OF THAT LINE. `-m`
imports the whole package, so the same command without that flag caches eleven
`.pyc` into `.claude/kernel` -- inside the tree `hook_bundle_hash` measures with
nothing excluded. Measured against an installed project: the flagless form ran
`doctor` and reported, in the same run that created them, that the bundle
"changed after trust was recorded", and the next SessionStart dropped the
project to `hooks_trust_required`. On Codex the inline verifier runs before
every tool call, so the same keystroke blocks the session until a re-scaffold.
A diagnosis command that destroys what it diagnoses -- and blames the user for
it -- is worse than no command, which is why every shipped remedy spells it this
way and `test_the_documented_cli_invocation_leaves_the_bundle_alone` runs what
this docstring says. The flagless form is deliberately not written out anywhere
in the shipped tree; a reader who copies a line copies a working one. The shim
carries the same rule as `sys.dont_write_bytecode = True` in its own first
statements, so the sanctioned spelling needs no flag to be safe.
"""
from __future__ import annotations

import argparse
import builtins
import inspect
import json
import os
import subprocess
import sys
import time

from . import (approvals, board, checkpoints, dispatch, filing, hashing, kitupdate, migrate,
               presets, report, staging)
from .backlog_types import (
    EVIDENCE_KINDS,
    EVIDENCE_RESULTS,
    REQUIRED_FIELDS,
    TASK_TYPES,
    TransitionError,
    field_elements,
)
from .schemas import load_schema
from .state import ProjectState, StateError


class UsageError(ValueError):
    """The command was not run because its INPUT was wrong -- exit 2, like argparse's own.

    Separate from `StateError` on purpose: 1 means the kernel looked and refused, 2 means it never
    got as far as looking. A malformed `capture` body is the second, and reporting it as the first
    would tell a role its item was rejected when it was never read.
    """


# WHERE the scaffold installs the entry point, and HOW a role invokes it -- one pair of
# constants because the two are the same fact and every other statement of it is derived:
# `prog` below (so argparse's own usage lines are runnable), the shim's self-location check,
# the scaffold's kit-owned list, and the test that requires every shipped text naming the
# entry point to spell it this way. A second, hand-written spelling anywhere is the drift
# this pair exists to prevent.
ENTRY_POINT = "scripts/harness.py"
INVOCATION = "python " + ENTRY_POINT


# THE PROMOTION SURFACE (spec II.6/II.6a). `kernel/staging.py` has had these three operations since
# 1.6 and its own docstring said "WHO calls freeze at mint time is phase-2 hook/orchestrator logic";
# nothing ever did. Measured 2026-07-31 in a scaffolded project, before this: no subcommand named
# freeze, `capture ARC` refused (`ARC` is not in `REQUIRED_FIELDS`), and `project_memory/**` is
# kernel-only for tool writes -- so an ARC item, a frozen wireframe and a `design_refs` entry were
# all unreachable. Three consequences, none of them theoretical: `gate_packaging_decision` blocked
# every push and merge on a field no role could write (a block with no exit, which is exactly what
# its own docstring said it was not); the UI-design tooth in `dispatch.validate_dispatch` only
# fires on a non-empty `root.design_refs` and that list could never become non-empty; and no
# wireframe could ever be frozen on scope approval.
#
# ONE MAPPING, and the surface is derived from it rather than restated: the subcommand names, their
# `--help`, the body's required and optional keys and the type each key must carry all come from
# `freeze_parameters` reading the operation's own signature. A fourth freeze operation is on the
# command line the day it is written, with the right contract, and a renamed parameter cannot leave
# a stale flag behind.
FREEZE_OPERATIONS = {
    "architecture": staging.freeze_architecture,
    "design": staging.freeze_design,
    "wireframe": staging.freeze_wireframe,
}
FREEZE_COMMANDS = {"freeze-" + kind: operation for kind, operation in FREEZE_OPERATIONS.items()}


def freeze_parameters(operation):
    """The body contract of a freeze operation, read off its signature: {name: (required, type)}.

    `state` is dropped -- the CLI holds it, and it is the one parameter a body must never carry.
    The TYPE is the parameter's own annotation resolved against `builtins`; `from __future__ import
    annotations` makes those annotations strings, and anything that does not name a builtin type
    simply carries no type check rather than an invented one. That matters because a body value of
    the wrong shape reaches the kernel as a `TypeError` from inside `list()` or `dict.get`, which is
    a traceback rather than a message a role can act on.
    """
    contract = {}
    for name, parameter in list(inspect.signature(operation).parameters.items())[1:]:
        declared = getattr(builtins, str(parameter.annotation), None)
        contract[name] = (parameter.default is inspect.Parameter.empty,
                          declared if isinstance(declared, type) else None)
    return contract


def _freeze_body(command, operation):
    """The stdin body for a freeze, checked against the operation's declared contract.

    Refusals are UsageErrors (exit 2) on purpose: a body with a missing or misspelled key is input
    the kernel never got to look at, and reporting it as a state refusal would tell a role its
    freeze was rejected when it was never attempted.
    """
    body = _json_body(command)
    contract = freeze_parameters(operation)
    missing = sorted(name for name, (required, _t) in contract.items()
                     if required and name not in body)
    unknown = sorted(key for key in body if key not in contract)
    if missing or unknown:
        raise UsageError(
            "the %s body %s. Its keys are exactly the operation's own parameters -- required: %s; "
            "optional: %s. Remedy: send that object on stdin, e.g. `%s %s <<'EOF'` … `EOF`."
            % (command,
               "; ".join(part for part in (
                   "is missing %s" % ", ".join(missing) if missing else "",
                   "carries %s, which the operation has no parameter for" % ", ".join(unknown)
                   if unknown else "") if part),
               ", ".join(sorted(n for n, (r, _t) in contract.items() if r)) or "none",
               ", ".join(sorted(n for n, (r, _t) in contract.items() if not r)) or "none",
               INVOCATION, command))
    for name, value in sorted(body.items()):
        _required, declared = contract[name]
        if declared is None or isinstance(value, declared):
            continue
        if value is None:
            # NULL IS THE SCHEMA'S QUESTION, NOT THIS ONE. The first cut allowed it only for a
            # parameter with a default and thereby refused a legitimate body: `freeze_wireframe`
            # takes `scope_apr_ref` as a REQUIRED parameter whose companion field is
            # `nullable: true` (same for `arc_companion.approval_ref`), so "no approval yet" had no
            # spelling. This check is about SHAPE -- a list stays a list -- and the strict companion
            # schemas decide which fields may be absent or null.
            continue
        raise UsageError(
            "the %s body gives %s as %s; the operation declares it %s. Remedy: send the field in "
            "the shape the kernel hashes it in -- a list stays a list, a mapping stays a mapping."
            % (command, name, type(value).__name__, declared.__name__))
    return body


def manifest_parameters(builder) -> list:
    """The subject keys a line-manifest builder takes, read off its own signature.

    Same derivation as `freeze_parameters`, and for the same reason: the flag surface of
    `request-approval push` IS `approvals.push_subject_manifest`'s parameter list, so a renamed
    or added subject key cannot leave a stale flag behind. Nothing is dropped here -- unlike a
    freeze operation, a manifest builder holds no `state`.
    """
    return list(inspect.signature(builder).parameters)


def optional_manifest_parameters(builder) -> frozenset:
    """The subject keys a command line may LEAVE OUT, read off the builder's own defaults.

    Same derivation as `freeze_parameters`' required/optional split, and here it carries meaning
    rather than convenience: for `filing_correction` the absent key IS the decision (no destination
    means the document is deleted, `approvals.filing_correction_subject_manifest`), so the builder's
    signature is where that fact belongs -- one statement, read by the parser, by `_line_manifest`
    and by the question the user signs.

    Empty for every builder that declares no default, which is all three of the older line kinds --
    so `push`, `preset` and `kit_update` keep refusing an unanswered subject key exactly as before
    (`tools/test_staging_cli.py::test_a_line_kind_without_a_defaulted_subject_key_still_demands_
    every_one`).
    """
    return frozenset(name for name, parameter in inspect.signature(builder).parameters.items()
                     if parameter.default is not inspect.Parameter.empty)


def _worktree_head(state: ProjectState, _args) -> str:
    """The commit a push would publish, read from the worktree the state directory sits in.

    `gate_push_token` resolves the SAME value with the same git call and binds its check to it, so
    a head a role typed from memory would mint a token for a different commit -- which is exactly
    the single-use property `push_subject_manifest` rests on. None when git cannot answer; the
    caller turns that into a usage error naming the flag.
    """
    repo = os.path.dirname(os.path.abspath(state.root))
    try:
        result = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    return ((result.stdout or "").strip() or None) if result.returncode == 0 else None


def _preset_roles(state: ProjectState, args):
    """The specialist set the requested preset installs here -- the kit's own answer."""
    return presets.change_manifest(state, args.preset)["roles"]


def _preset_removes(state: ProjectState, args):
    """The installed specialists that the requested preset drops -- possibly none, legitimately."""
    return presets.change_manifest(state, args.preset)["removes"]


# Manifest keys the CLI determines ITSELF, from the project rather than from the role -- each with
# the SOURCE it determines them from, in the words the `--help` prints. A key here is not the
# role's to fill in; a key without an entry is required on the line. That split is why `remote` and
# `branch` stay typed: they are what the user is asked to authorise, so they come from the role's
# intent, never from whatever the machine happens to be checked out at. `preset`'s two lists are
# the mirror image -- they are what the KIT decides, and a role typing them would be typing over
# the file that owns them.
#
# A TYPED VALUE FOR ONE OF THESE IS REFUSED, not quietly overridden and not quietly used. The
# verifier measured what "used" costs: `--roles product-designer --removes nothing-at-all` produced
# a real, kernel-signed approval question whose role lists were those strings split into single
# CHARACTERS -- and `build_question` rests on the property that what the hash covers is what the
# user is shown. A silent override would be no better: the question would then be right while the
# line the role typed said something else. `test_a_resolver_owned_key_is_not_the_roles_to_type`
# measures the refusal on both keys.
#
# A resolver takes (state, args): the second half arrived with `preset`, whose answer depends on
# the preset already named on the line. `_worktree_head` ignores it, which is the honest shape --
# one signature, and no branch here about which resolver wants what.
def _kit_update_key(key):
    """One resolver per key of the kit-update manifest, all reading ONE derivation.

    Every key of that manifest is the kit's own statement about a release
    (`approvals.kit_update_subject_manifest`), so none of them is a role's to type -- and the
    entries are generated from the builder's signature rather than written out, for the reason
    `manifest_parameters` exists: a renamed or added key arrives here correctly refused instead of
    silently becoming a flag the command ignores.
    """
    def resolve(state: ProjectState, _args):
        return kitupdate.change_manifest(state).get(key)
    return resolve


def _document_content(state: ProjectState, args) -> str:
    """The FASSUNG of the document a filing correction names -- hashed here, never typed.

    A role typing this would be typing the one value that decides whether the approval still covers
    the document when the gate looks: `guard_fs_tripwire` recomputes it from the file on disk with
    the same function, so a typed value could only differ from what the user was shown -- which is
    the property `LINE_MANIFEST_RESOLVERS` exists for.

    A document that cannot be hashed is refused HERE, with the path in the message, rather than
    reported as a missing manifest key: the two causes a clerk actually hits are a mistyped path and
    a file past `hashing.DOCUMENT_HASH_LIMIT`, and neither is helped by a remedy listing four flags.

    THE SPELLING HAS TO ROUND-TRIP, and this is the half that was silent (verifier finding F5). It
    is not enough that the named file lies inside the project: the typed spelling must BE the
    project-relative position, because that is the only spelling `guard_fs_tripwire` can ever
    produce. An absolute path to a file inside the project passed the earlier check, minted a real
    approval -- and the same document named the way the gate names it was then refused, which is a
    dead end handed over without a word. So the position is resolved and normalised back, and it has
    to come out as what was typed (`tools/test_staging_cli.py::test_a_document_named_in_a_spelling_
    the_gate_cannot_produce_is_refused_at_the_command_line`). `approvals.is_project_position` refuses
    the same class one layer further in, over the subject the user signs; this one is the message
    the clerk gets, with the path in it.

    AND THE ROUND TRIP IS AGAINST THE FILESYSTEM, NOT AGAINST THE STRING (verifier round 2, R2).
    Lexically, `ARCHIVE/…/x.pdf` round-trips perfectly -- and on a case-insensitive filesystem it is
    the same file under a name the archive does not use, so the approval was minted and then matched
    nothing. `hashing.on_disk_position` reads back the spelling the filesystem really carries, and a
    deviating one is refused BY NAME rather than by the generic message: a user who answered a
    question for nothing is worse off than one who was told to type the path again.
    """
    repo = os.path.dirname(os.path.abspath(state.root))
    document = approvals.filed_position(getattr(args, "document", None))
    absolute = os.path.abspath(os.path.join(repo, document)) if document else ""
    inside = bool(document) and (os.path.normcase(absolute)
                                 .startswith(os.path.normcase(repo) + os.sep))
    round_trips = inside and approvals.filed_position(
        os.path.relpath(absolute, repo)) == document
    spelled = hashing.on_disk_position(repo, document) if round_trips else None
    if spelled is not None and spelled != document:
        raise UsageError(
            "the document is called %s; %s names the same file but not by that name, and the gate "
            "reads the position out of the command that touches it. An approval for a spelling the "
            "archive does not use would be minted and would then match nothing -- a question the "
            "user answers for nothing. Remedy: name it exactly as it lies there: `--document %s`."
            % (spelled, document, spelled))
    content = hashing.document_content_hash(absolute) if spelled is not None else None
    if not content:
        raise UsageError(
            "a filing correction is bound to the document's own bytes, and %s could not be read as "
            "a file inside %s under the name the gate uses (it lies outside the project, it is "
            "spelled in a way the gate never produces -- absolute, or climbing -- or it is missing, "
            "is a directory, is unreadable, or is larger than the %d MiB a gate may hash while "
            "judging a call). Remedy: name the document with its path relative to the project root, "
            "exactly as it lies there."
            % (document or "an empty path", repo, hashing.DOCUMENT_HASH_LIMIT // (1024 * 1024)))
    return content


LINE_MANIFEST_RESOLVERS = {
    "content": (_document_content, "hashed from the document named on this line"),
    "head": (_worktree_head, "read from the worktree this state directory sits in"),
    "roles": (_preset_roles, "read from the kit's own presets.yaml for the preset on this line"),
    "removes": (_preset_removes, "derived from what this installation owns and that preset"),
}
LINE_MANIFEST_RESOLVERS.update(
    (name, (_kit_update_key(name),
            "read from this project's own kit stamp and the kit staged on this machine"))
    for name in manifest_parameters(approvals.kit_update_subject_manifest))


def _line_manifest(state: ProjectState, kind: str, builder, args) -> dict:
    """The subject manifest for a line kind, from the flags plus the resolvers.

    EMPTY IS AN ANSWER WHEN A RESOLVER GAVE IT, and that distinction is load-bearing: a preset
    upgrade REMOVES nothing, so `removes: []` is the truth about it, while the same emptiness in a
    key the role must type means the question would not say what it releases. So a resolved key
    fails only when the resolver cannot answer at all (None), and a typed key fails on emptiness.
    `test_a_manifest_key_a_resolver_answers_with_nothing_is_still_an_answer` measures the pair.

    ...AND EMPTY IS AN ANSWER WHEN THE BUILDER DECLARED A DEFAULT FOR IT
    (`optional_manifest_parameters`). That is not a third leniency but the same rule read off the
    one place that owns it: for `filing_correction` an absent `--destination` is what says the
    document ends up nowhere, and the question the user signs spells that out as a deletion. A
    builder that declares no default keeps demanding every key, which is all three older line kinds.

    THE REMEDY IS DERIVED FROM THE SAME TWO STATEMENTS the loop decides on, and that is the fix to
    verifier finding F8: it used to print EVERY manifest key as a flag to type, which named
    `--content` (a resolver-owned key this very function refuses when typed) and `--destination` (a
    key whose OMISSION is the documented way to request a deletion). A remedy that contradicts the
    command it is the remedy for is worse than none, and `optional_manifest_parameters` having a
    reader that disagrees with it is exactly the second statement this kernel keeps unlearning.
    """
    values = {}
    optional = optional_manifest_parameters(builder)
    typed = [key for key in manifest_parameters(builder) if key not in LINE_MANIFEST_RESOLVERS]
    flags = " ".join(
        ("[--%s <%s>]" if key in optional else "--%s <%s>")
        % (key.replace("_", "-"), key) for key in typed)
    for name in manifest_parameters(builder):
        value = getattr(args, name, None)
        entry = LINE_MANIFEST_RESOLVERS.get(name)
        if entry is not None:
            if value:
                raise UsageError(
                    "%s is not a value to type on this line: it is %s, and the command re-derives "
                    "it when it acts on the approval -- a typed one could only differ from what "
                    "the user was shown. Remedy: drop `--%s %s` and run the command again."
                    % (name, entry[1], name.replace("_", "-"), value))
            value = entry[0](state, args)
        if name in optional and not value:
            continue          # the builder's own default answers it -- see the paragraph above
        if value is None or (not value and entry is None):
            raise UsageError(
                "a %s approval question must say what it releases, and %s is missing. Remedy: "
                "`%s request-approval %s %s` -- these are the subject keys a line carries (a "
                "bracketed one may be left out, and what its absence MEANS is in the question the "
                "command prints); every other key of the manifest is derived by the command itself "
                "and is refused when typed."
                % (kind, name, INVOCATION, kind, flags))
        values[name] = value
    try:
        return builder(**values)
    except approvals.ApprovalError as exc:
        # A BUILDER THAT REFUSES ITS SUBJECT IS REFUSING THE LINE, and the role has to read one exit
        # code for that. `filing_correction` is the first line kind whose builder can refuse (a
        # position the gate could never produce, a destination that names no place); as an
        # ApprovalError it came back as exit 1 -- "the kernel refused" -- beside exit 2 for the
        # resolver's refusal about the very same flag. Same input, same fault, two codes.
        raise UsageError(str(exc)) from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=INVOCATION, description="V2 state-kernel commands (HARNESS_V2_SPEC.md II.4)"
    )
    # NOT a flag a role types: the shim fills it in from the repo root and refuses it in argv
    # (`scripts/harness.py`). It stays on the parser -- and stays VISIBLE in `--help` -- because
    # the installer position above really does need it, and a flag that works while the help
    # denies it is the same defect as a help that promises one that does not.
    parser.add_argument("--root", default="project_memory",
                        help="state directory; for the pre-install installer position only -- the "
                             "installed entry point resolves it and refuses this flag")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="read-only activation/diagnosis report")
    sub.add_parser("validate", help="fail-closed state validation (exit 1 on errors)")
    # NAMES BOTH ARTEFACTS because the command writes both (`state._regenerate_index_locked`): a
    # help line that mentions only the index is a description one release out of date the moment
    # somebody looks for the human-readable view under `generated/`.
    sub.add_parser("generate-index",
                   help="regenerate generated/index.yaml and the board rebuilt with it")
    brief = sub.add_parser("generate-session-brief", help="regenerate generated/session_brief.yaml")
    brief.add_argument("--kit", required=True)
    brief.add_argument("--kit-version", required=True)
    brief.add_argument("--enforcement", choices=["hard", "audited"], required=True)
    # The ONE producer of QA evidence. It is a `capture` specialised to a single type, and
    # deliberately so: Evidence is the only item a specialist role is told to hand back on
    # its own (spec II.2 -- no project status, no approval, no automaton to walk), so it is
    # the only capture that needs no orchestrator judgement between the finding and the
    # file. Everything else still goes through the generic capture command the CLI shim
    # brings with it.
    evidence = sub.add_parser("evidence", help="record a test/review/acceptance/audit Evidence item")
    evidence.add_argument("--kind", required=True, choices=sorted(EVIDENCE_KINDS))
    evidence.add_argument("--result", required=True, choices=sorted(EVIDENCE_RESULTS),
                          help="the verdict the merge gate reads")
    evidence.add_argument("--related", required=True, action="append", metavar="ITEM_ID",
                          help="the item this evidence examined (repeatable)")
    evidence.add_argument("--summary", required=True)
    # Required, like `--related`: those two are what make the record evidence rather
    # than an assertion (backlog_types.NONEMPTY_FIELDS). The kernel refuses an empty
    # one anyway; asking argparse first is what turns that into a usage error naming
    # the flag, at the moment the role is typing the command.
    evidence.add_argument("--artifact-ref", required=True, action="append", metavar="PATH",
                          dest="artifact_refs",
                          # STATE-RELATIVE, and that is not cosmetic: `gate_write_scope`
                          # refuses any write-capable command line that names the state
                          # directory, so an argument spelling `project_memory/...` would
                          # make this very command unrunnable for the role that needs it.
                          help="where the raw proof lives, relative to the state directory "
                               "(e.g. staging/TSK-0007/coverage.html; repeatable) -- evidence "
                               "references its artefacts, never inlines them")
    # THE GENERIC ITEM PRODUCER (spec II.4 `capture`). Its body arrives on STDIN as JSON, and both
    # halves of that are forced rather than chosen:
    #   * STDIN, because an item's fields include lists of mappings (`acceptance_criteria:
    #     [{id, text}]`) that no flag surface expresses, and the obvious alternative -- a `--from
    #     project_memory/staging/<key>/item.yaml` -- cannot be typed: `gate_write_scope` refuses a
    #     write-capable pipeline whose COMMAND LINE names the state directory (measured: rc 2,
    #     "names the canonical state directory"). A body on stdin names nothing.
    #   * JSON and not YAML, although the store is YAML. The body decides the item's HASHED fields,
    #     and YAML 1.1's implicit typing silently changes values on the way in -- `no` becomes
    #     False, `1.10` becomes a float, `12:30` becomes 750. A value that means one thing to the
    #     role who typed it and another to `subject_manifest_hash` is the approval-invalidation
    #     class this kernel exists to end, and `kernel/hashing.canonical_json` already fixes JSON
    #     as the form a hash is defined over.
    # The type list is the kernel's own (`REQUIRED_FIELDS`), so a new capturable type needs no
    # edit here.
    capture = sub.add_parser(
        "capture", help="create a typed item from a JSON object on stdin")
    capture.add_argument("item_type", choices=sorted(REQUIRED_FIELDS))
    # The TSK work order as FLAGS. Same producer as `capture TSK` (both end in
    # `dispatch.create_task`), different surface: a work order is flat, it is the thing a role
    # types most often, and every one of its fields is a gate input worth naming on the line.
    task = sub.add_parser("create-task", help="create a TSK work order (kernel sets root_revision)")
    task.add_argument("--product-requirement", required=True, metavar="ITEM_ID",
                      help="the PR/RQ root this task serves")
    task.add_argument("--derives-from", required=True, metavar="ITEM_ID",
                      help="the item whose criteria this task serves (root, BUG, CR, EXP)")
    task.add_argument("--type", required=True, choices=sorted(TASK_TYPES), dest="task_type")
    task.add_argument("--assigned-role", required=True,
                      help="the installed role the dispatch gate matches the spawn against")
    task.add_argument("--acceptance-ref", required=True, action="append", dest="acceptance_refs",
                      metavar="AC_ID", help="criterion this task is measured against (repeatable)")
    # QUOTE THE GLOB, and the help says so because the failure is silent in the one case that
    # matters. `**` and `*` are what `gate_write_scope._matches` reads, but the SHELL sees them
    # first: once `src/` exists, `--allowed-scope src/**` is expanded before this parser is
    # reached. With several matches argparse rejects the extra words; with exactly ONE the scope
    # is quietly narrowed to that single file and the task runs under a grant nobody wrote.
    task.add_argument("--allowed-scope", required=True, action="append", dest="allowed_scope",
                      metavar="PATH", help="what the specialist may write (repeatable); this IS "
                                           "gate layer 3's input. QUOTE any glob -- "
                                           "`--allowed-scope 'src/**'` -- or the shell expands it "
                                           "against the working tree before the kernel sees it")
    task.add_argument("--forbidden-scope", action="append", dest="forbidden_scope", metavar="PATH",
                      help="what the specialist may NOT write (repeatable); quote globs, for the "
                           "reason --allowed-scope gives")
    task.add_argument("--required-input", action="append", dest="required_inputs",
                      metavar="PATH_OR_ID")
    task.add_argument("--expected-output", action="append", dest="expected_outputs", metavar="PATH")
    task.add_argument("--dependency", action="append", dest="dependencies", metavar="ITEM_ID")
    task.add_argument("--design-ref", metavar="DSN_ID",
                      help="required for a UI task once its root has a confirmed design (II.6)")
    # The specialist's hand-back. Field names and the status vocabulary come from the SCHEMA the
    # kernel validates against, not from a copy here -- `submit_result` would reject a divergence
    # anyway, but it would reject it after the role had typed the command.
    envelope_fields = load_schema("result_envelope")["fields"]
    submit = sub.add_parser("submit-result", help="hand a specialist's result envelope back")
    submit.add_argument("--task-id", required=True, metavar="TSK_ID")
    # NOT `required=True` any more, and `--from` is why (BUG-0048). A specialist whose toolset
    # grants no command-running tool cannot type this line at all, so the lead books its result
    # in; retyping the envelope out of the child's final message makes the LEAD the author of
    # what the kernel records. `--from` lets the specialist's OWN bytes travel instead: it stages
    # the envelope under its task's staging key -- the one place `gate_write_scope` lets a bound
    # specialist write -- and the lead names the file. `_submitted_envelope` refuses the flag
    # route without the fields the schema requires, which is what these three lines used to do.
    submit.add_argument("--role")
    submit.add_argument("--status-proposal",
                        choices=list(envelope_fields["status_proposal"]["enum"]))
    submit.add_argument("--summary",
                        help="<= %d chars; raw logs are REFERENCED, never inlined"
                             % envelope_fields["summary"]["max_len"])
    submit.add_argument("--from", dest="envelope_file", metavar="NAME",
                        help="a staged envelope to hand back verbatim: the BARE FILE NAME of a "
                             "JSON object inside this task's own staging directory, e.g. "
                             "`--from result.json`. The path is composed by the kernel, so a name "
                             "that walks out of that directory is refused. Use this to book in a "
                             "specialist that cannot run a command itself; the other flags are "
                             "then unnecessary and a conflicting one is refused.")
    # Paths are repo-relative; anything inside the state directory is named RELATIVE TO IT
    # (`staging/<task-id>/...`), exactly as `evidence --artifact-ref` is and for the same measured
    # reason -- the shell gate refuses a write-capable command line that names `project_memory`.
    submit.add_argument("--output", action="append", dest="outputs", metavar="PATH",
                        help="what the task produced (repeatable); state-relative inside the "
                             "state dir, e.g. staging/TSK-0007/proposal.md")
    submit.add_argument("--evidence", action="append", dest="evidence", metavar="EVD_ID")
    submit.add_argument("--scope-touched", action="append", dest="scope_touched", metavar="PATH")
    submit.add_argument("--followup", action="append", dest="followups")
    # PHASE 1 OF THE APPROVAL PROTOCOL, and the reason it has to be on this surface: without it
    # `create_pending_request` had NO caller in the shipped tree, so no `[APR-REQ:<id>]` question
    # could exist, so `gate_approval` blocked every AskUserQuestion that looked like one, so no
    # APR could ever be minted -- and since `transition` now demands an APR on the edges an
    # approval commits, a root item could never leave DRAFT in a real project. The sperre had no
    # walkable counterpart. Measured before this command: `approvals/pending/` stays empty and
    # `transition PR-0001 APPROVED` refuses forever.
    #
    # IT REQUESTS, IT DOES NOT MINT, and that line is where the provenance lives. This writes the
    # immutable pending request and prints the question the KERNEL composed; the user mints by
    # ANSWERING it, and `approvals.mint` still refuses every caller but `gate_approval.py`.
    # Nothing about spec II.2's chain changes -- what changes is that the chain now has a first
    # link a role can reach.
    #
    # THE KINDS ARE ASKED OF THE FUNCTION THAT DECIDES THEM (`approvals.item_derived_kinds`,
    # which probes `item_subject_manifest`). A command line can carry an item id; it cannot carry
    # an analysis question, a read-only scope and a cadence, so a kind whose manifest is not
    # item-derived keeps needing a caller that builds one. This used to read
    # `APR_KINDS - EXPIRING_KINDS`, which is a different property (time-boxed vs
    # content-invalidated) that agrees today -- a third statement of one split is how they drift.
    #
    # THE SECOND HALF OF THE SPLIT, added 2026-08-02 because its absence was a wall: this parser
    # offered `item_derived_kinds()` only, so `push` -- a kind in `APR_KINDS`, with its own
    # manifest builder and a gate refusing every push without one -- had no way to be requested at
    # all. Measured before this: no project could publish anything, ever, and `gate_push_token`'s
    # remedy named a command the parser did not have. The flags come from the BUILDER'S SIGNATURE,
    # exactly as a freeze body's keys do, so a second line kind arrives correctly flagged.
    request = sub.add_parser(
        "request-approval",
        help="open the approval question (phase 1); the USER mints by answering it")
    request.add_argument("kind", choices=sorted(set(approvals.item_derived_kinds())
                                                | set(approvals.line_manifest_kinds())))
    request.add_argument("item_id", metavar="ITEM_ID", nargs="?",
                         help="the item to approve -- required for %s, and refused for %s, whose "
                              "subject is the flags below rather than an item"
                              % ("/".join(sorted(approvals.item_derived_kinds())),
                                 "/".join(approvals.line_manifest_kinds())))
    for line_kind, builder in sorted(approvals.LINE_MANIFEST_BUILDERS.items()):
        for name in manifest_parameters(builder):
            flag = "--" + name.replace("_", "-")
            if flag in {action.option_strings[0] for action in request._actions
                        if action.option_strings}:
                continue          # two line kinds sharing a manifest key share the flag
            # THE HELP SAYS WHERE THE VALUE COMES FROM, in the resolver's own words, and says it
            # is refused where that source is not the role. It used to say "default: read from the
            # worktree" for every resolved key, which was true of `head` and false of the two the
            # kit's preset file answers -- and it read as an override the line may set, which is
            # exactly what `_line_manifest` refuses. The flag stays VISIBLE for the reason `--root`
            # does: a flag the parser accepts and the command refuses must be findable in `--help`.
            entry = LINE_MANIFEST_RESOLVERS.get(name)
            request.add_argument(
                flag, metavar=name.upper(),
                help="%s subject: %s%s" % (line_kind, name,
                                           " -- NOT typed here: %s, and a value is refused"
                                           % entry[1] if entry else ""))
    # The lease + header, in one command, because they are one moment: spec II.4 orders
    # "READY -> kurzlebige Dispatch-Lease mit Nonce und TTL -> Header", and the gate that reads the
    # header runs at PreToolUse of the spawn -- AFTER the model has composed the prompt. A lease
    # created there would be a lease minted for a nonce the model chose, which is the bearer-token
    # shape the nonce exists to prevent. So the lease is created BEFORE, and this prints the one
    # header line `dispatch_header` produces, for the role to copy verbatim.
    # NO `--ttl`: "kurzlebig" is the property spec II.4 names, and a flag would let the supervised
    # party decide how short short is. The kernel default stands.
    lease = sub.add_parser(
        "dispatch", help="lease a READY task and print its HARNESS_DISPATCH header")
    lease.add_argument("task_id")
    # THE CHECKPOINT PAIR (DEC-0044). Written and read through the kernel for the same reason the
    # result envelope is: the two digests that decide adoption later are MEASUREMENTS, and a record
    # whose integrity data the checked party supplied would verify itself (`kernel/checkpoints.py`).
    # The body is on STDIN like `capture`'s, and for the second of that command's two reasons as
    # well -- an artefact list is a list of mappings once the kernel has measured it, and a
    # `--from project_memory/staging/...` cannot be typed past `gate_write_scope` at all.
    checkpoint = sub.add_parser(
        "checkpoint",
        help="record resumable progress for a dispatched task (JSON body on stdin: next_step, "
             "outputs[{output_index, progress, artifacts[, note]}]) -- a successor MAY adopt it "
             "only after the verification command below confirms it",
        description="Record resumable progress for a task that is dispatched RIGHT NOW, so a "
                    "session break does not take the work with it (DEC-0044). JSON body on stdin: "
                    "{\"next_step\": \"...\", \"outputs\": [{\"output_index\": 0, \"progress\": "
                    "\"partial\", \"artifacts\": [\"src/x.py\"], \"note\": \"...\"}]}. "
                    "`output_index` addresses the task's expected_outputs in order; artefact paths "
                    "are relative to the project root, have to stay inside it (an absolute one, a "
                    "`..` and a link that leads out are refused) and are hashed by the kernel as "
                    "they are recorded. Nothing else is written, and the record is a PROPOSAL in "
                    "staging/<TSK-ID>/, never state.")
    checkpoint.add_argument("task_id")
    status = sub.add_parser(
        "checkpoint-status",
        help="verify a task's checkpoint (read-only) and print what was measured; exit 1 when it "
             "is absent, stale or broken -- which are one answer: treat it as absent")
    status.add_argument("task_id")
    transition = sub.add_parser(
        "transition",
        help="status transition via the automaton; an edge an approval COMMITS needs that "
             "approval in force, and the mint walks such an edge itself")
    transition.add_argument("item_id")
    transition.add_argument("to_status")
    transition.add_argument("--approved-retry", action="store_true")
    # THE SANCTIONED EDIT PATH (BUG-0001). `state.update_item` existed with its approval
    # invalidation (spec II.2) but had no CLI surface, so a typo in a captured field could only be
    # fixed by cancelling the item and recapturing it (measured 2026-08-04). The body is on STDIN
    # for the same two reasons `capture`'s is -- a change can carry lists and mappings no flag
    # expresses, and a `--from project_memory/...` cannot be typed past `gate_write_scope`. The
    # KERNEL-SET fields (`id`, `status`, `revision`, `approval_ref`, `created`) are NOT accepted:
    # they change only through their own operations (capture/transition/approve), and this surface
    # names no flag for them precisely because it does not decide them -- `update_item` refuses any
    # such key in the body, so the automaton cannot be side-stepped by writing `status` here.
    update = sub.add_parser(
        "update", help="edit an item's fields through the kernel (JSON object of changes on "
                       "stdin); invalidates a current approval when a hashed field changes")
    update.add_argument("item_id")
    # THE PROMOTION COMMANDS (see FREEZE_OPERATIONS for what they unblock). Generated from that
    # mapping, so the surface cannot fall behind the kernel; the body is on STDIN for the same two
    # reasons `capture`'s is -- `derives_from`, `assets` and `packaging` are a list and two mappings
    # no flag surface expresses, and a `--from project_memory/staging/...` cannot be typed at all
    # (`gate_write_scope` refuses a write-capable pipeline whose COMMAND LINE names the state
    # directory). Nothing on this line names it: a staging KEY, an item id and a file NAME are
    # state-relative by construction, exactly as `evidence --artifact-ref` is.
    for command, operation in sorted(FREEZE_COMMANDS.items()):
        contract = freeze_parameters(operation)
        summary = (
            "promote the staged %s to canonical state (spec II.6/II.6a); JSON body on stdin, "
            "required: %s%s" % (
                command.split("-", 1)[1],
                ", ".join(sorted(name for name, (required, _t) in contract.items() if required)),
                "; optional: %s" % ", ".join(
                    sorted(name for name, (required, _t) in contract.items() if not required))
                if any(not required for required, _t in contract.values()) else ""))
        # THE CONTRACT GOES INTO `description` AS WELL AS `help`, because the two are printed in
        # different places and a role reads the wrong one: `help` appears only in the PARENT's
        # `--help`, so `freeze-architecture --help` -- the command a role actually types when it
        # wants to know what to send -- printed `usage: ... freeze-architecture [-h]` and nothing
        # else (measured 2026-08-02). A body-taking command whose own help does not name its body
        # is a command with no discoverable contract.
        sub.add_parser(command, help=summary, description="%s. The keys are exactly the "
                       "operation's own parameters; send them as ONE JSON object on stdin, e.g. "
                       "`%s %s <<'EOF'` … `EOF`." % (summary, INVOCATION, command))
    # THE ROUTE OUT OF THE PRESET DEAD END (BUG-0041). Before this, changing which specialist
    # roles a project has meant editing `project_config.yaml` and running the scaffold -- and both
    # are refused from inside a session, on purpose, so the lead's only move was to send the USER
    # to a text editor and a terminal. Pilot 3 measured what that is worth to a non-technical user:
    # she got no further than finding the folder. `kernel/presets.py` carries the design; what
    # belongs here is that this is a NORMAL command line -- it names neither the state directory
    # nor the enforcement layer, which is what lets a role type it at all.
    preset = sub.add_parser(
        "set-preset",
        help="record a user-approved team preset and install exactly its roles (needs a minted "
             "`preset` approval; asks for a session restart afterwards)")
    preset.add_argument("preset", help="the preset to move to; the kit's presets.yaml names them "
                                       "and an unknown one is refused with the list")
    # THE SECOND HALF OF THE SAME DEAD END (FR-0006). A preset change and a kit update were both
    # "ask the USER to run the scaffold", and the second one is the wider of the two: it replaces
    # the hooks, the kernel, the settings and the constitution. `kernel/kitupdate.py` carries the
    # design; what belongs here is that this command takes NO argument -- which kit, which release
    # and which direction are the project's and the staging's own statements, and a role typing
    # any of them would be typing over the files that own them.
    sub.add_parser(
        kitupdate.COMMAND,
        help="install the kit release staged on this machine over this project (needs a minted "
             "`%s` approval; refuses a downgrade and stops the session afterwards)" % kitupdate.KIND)
    # THE THIRD DEAD END OF THE SAME FAMILY (FR-0049 step 5). An office project meeting a document
    # class its Aktenplan does not know could not file it -- correctly -- and could not grow the
    # plan either: `filing_plan.yaml` is a kit document, so no tool write reaches it and, until
    # `kernel/filing.py`, no command wrote it. The flags are the manifest builder's own parameters,
    # exactly as the approval request above renders them, so the line that ASKS and the line that ACTS
    # cannot come to describe two different rules; `_line_manifest` builds the same manifest from
    # them and `filing.apply` refuses unless a live approval carries it.
    rule = sub.add_parser(
        filing.COMMAND,
        help="append a user-approved rule to %s (needs a minted `%s` approval; same flags as the "
             "request that opened the question)" % (filing.PLAN, filing.KIND))
    for name in manifest_parameters(approvals.LINE_MANIFEST_BUILDERS[filing.KIND]):
        rule.add_argument("--" + name.replace("_", "-"), metavar=name.upper(),
                          help="the approved rule's %s -- the approval is looked up by the "
                               "manifest these flags build, so they are the ones the user was "
                               "shown" % name)
    archive = sub.add_parser("archive", help="move a terminal item to archive/")
    archive.add_argument("item_id")
    sub.add_parser("sweep-leases", help="return expired leases to READY")
    # ...and the same job for the OTHER store that only ever grew. An approval request that ran out
    # of time is already inert everywhere it is read; what it was not, until this command, is
    # removable -- see `approvals.sweep_expired_requests` for the measured occasion.
    sub.add_parser("sweep-requests",
                   help="delete approval requests whose clock ran out (they can never mint)")
    # THE V1 IMPORT (spec II.10). Two halves of one command rather than two commands, because the
    # second half is only sound as the continuation of the first: `--dry-run` reads and prints a
    # DIGEST over everything it read, and `--plan <digest>` refuses unless it re-derives the same
    # value. Splitting them into `migrate-plan`/`migrate-apply` would have made "run the apply
    # without ever running the plan" a spelling that exists.
    #
    # NO APPROVAL KIND IS ASKED FOR HERE, and `kernel/migrate.py`'s docstring is where the reason
    # is argued rather than restated -- including why the kinds are named by ASKING
    # (`approvals.item_derived_kinds`, `approvals.line_manifest_kinds`) rather than counted: this
    # line said "all five" over a vocabulary of six and thereby put the two kinds that hash NEITHER
    # an item nor a commit on the wrong side of its own sentence. What the digest proves is that
    # the STATE has not moved since the run was presented -- not that a user consented -- and no
    # text in this harness may say otherwise.
    migration = sub.add_parser(
        "migrate", help="import V1 records into the V2 item store (spec II.10); --dry-run first")
    exclusive = migration.add_mutually_exclusive_group(required=True)
    exclusive.add_argument("--dry-run", action="store_true",
                           help="read the state and print what a run would do; writes nothing")
    exclusive.add_argument("--plan", metavar="DIGEST",
                           help="the digest the dry run printed; the run refuses any other state")
    # A FLAG AND NOT A BODY ON STDIN, unlike `capture`: these are scalar pairs the DRY RUN ITSELF
    # prints, so what a human does with them is paste a line back. Nothing here names a path, so
    # `gate_write_scope` has nothing to refuse.
    migration.add_argument("--map", action="append", dest="field_map", metavar="TYPE.FIELD=V1_FIELD",
                         help="which V1 field feeds a V2 required field the record does not spell "
                              "the same way (repeatable); the dry run prints the exact flags")
    # THE ONE THING THE IMPORT REFUSES TO GUESS ABOUT A FINISHED RECORD (SR-0004). A record spec
    # II.10's table calls finished is written under `archive/<TYPE>/<year>/`, and the year comes from
    # the record's own newest date. Where a V1 store carries no date at all -- `system_requirements
    # .yaml` carries none in either field project -- this is the answer, given once for the run,
    # rather than a year this command picked.
    migration.add_argument("--archive-year", type=int, metavar="YYYY",
                           help="the archive year for finished records that carry no date of "
                                "their own; the dry run blocks and asks for it when it needs it")
    return parser


def _submitted_envelope(state, args) -> dict:
    """The result envelope `submit-result` hands the kernel -- from a staged FILE or from flags.

    THE TWO PATHS ARE THE TWO KINDS OF SPECIALIST (BUG-0048), not a convenience pair. A role
    whose installed definition grants a command-running tool types the flags itself
    (`dispatch.HAND_BACK_SELF`); a role whose definition grants none cannot type any command
    line, so it stages the envelope under its own task's key -- the one path
    `gate_write_scope` leaves a bound specialist inside the state directory -- and the lead
    names that file here (`dispatch.HAND_BACK_LEAD`). What the lead hands over is then the
    specialist's own bytes: retyping them out of a child's final message makes the LEAD the
    author of the record, and a summary the lead paraphrased is a summary nobody can attribute.

    THE FILE NAME IS A NAME, NOT A PATH, and `staging.contained_child` is what makes that true --
    the same chokepoint every freeze parameter goes through, and for the same measured reason (a
    `..` there was an `rmtree` on the repository). It is composed onto the staging directory of
    the task NAMED ON THE COMMAND LINE, so the lead cannot be talked into reading another task's
    proposal by the envelope it is about to submit.

    JSON AND NOT YAML, for the reason `_json_body` gives one screen down: YAML retypes `no` as
    false and `1.10` as a float, and a `summary` is a string whatever it spells.
    """
    if not args.envelope_file:
        missing = [name for name, value in (("--role", args.role),
                                            ("--status-proposal", args.status_proposal),
                                            ("--summary", args.summary)) if not value]
        if missing:
            raise UsageError(
                "submit-result needs %s, or a staged envelope to hand back instead. Remedy: add "
                "the flag(s), or -- for a specialist that cannot run a command itself -- let it "
                "write the envelope into the staging directory its OWN task owns and name that "
                "file here with `--from <NAME>`. No place is spelled out for you to fill in: the "
                "kernel composes it from the task id you already named (DEC-0024)."
                % ", ".join(missing))
        return {
            "task_id": args.task_id,
            "role": args.role,
            "status_proposal": args.status_proposal,
            "summary": args.summary,
            "outputs": list(args.outputs or []),
            "evidence": list(args.evidence or []),
            "scope_touched": list(args.scope_touched or []),
            "followups": list(args.followups or []),
        }
    conflicting = sorted(name for name, value in (
        ("--role", args.role), ("--status-proposal", args.status_proposal),
        ("--summary", args.summary), ("--output", args.outputs),
        ("--evidence", args.evidence), ("--scope-touched", args.scope_touched),
        ("--followup", args.followups)) if value)
    if conflicting:
        raise UsageError(
            "--from hands back a staged envelope VERBATIM, so %s would be a second author of the "
            "same record and the kernel refuses to pick one. Remedy: drop those flags, or drop "
            "--from and type the whole envelope." % ", ".join(conflicting))
    path = staging.contained_child(
        staging.staging_dir(state, args.task_id), args.envelope_file, "staged envelope")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(report.ITEM_MAX_BYTES + 1)
    except OSError as exc:
        raise UsageError(
            "the staged envelope %r is not readable in the staging directory %s owns (%s). "
            "Remedy: the specialist writes it there before it stops -- that directory is the one "
            "place inside the state directory its own writes reach."
            % (args.envelope_file, args.task_id, exc)) from None
    if len(raw) > report.ITEM_MAX_BYTES:
        raise UsageError(
            "the staged envelope %r is over %d bytes. Remedy: an envelope REFERENCES its detail; "
            "the schema caps it far below this and would refuse it anyway."
            % (args.envelope_file, report.ITEM_MAX_BYTES))
    try:
        envelope = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise UsageError(
            "the staged envelope %r is not UTF-8 JSON (%s). Remedy: the specialist writes the "
            "eight envelope fields as ONE JSON object; `kernel/schemas/result_envelope.yaml` is "
            "the contract and `submit-result` validates against it."
            % (args.envelope_file, exc)) from None
    if not isinstance(envelope, dict):
        raise UsageError(
            "the staged envelope %r is a %s; an envelope is a JSON OBJECT of field -> value."
            % (args.envelope_file, type(envelope).__name__))
    named = envelope.get("task_id")
    if named != args.task_id:
        raise UsageError(
            "the staged envelope names task_id %r and this command names %s -- refused rather "
            "than reconciled. Remedy: submit the envelope under the task it was written for."
            % (named, args.task_id))
    return envelope


def _json_body(command: str = "capture") -> dict:
    """The JSON object a body-taking command was given on stdin, or a UsageError naming what
    went wrong.

    `command` is the subcommand the role typed, so the remedy names the line they were running --
    `capture` and the three `freeze-*` commands share this reader because they share the reason
    for it (see the `capture` parser entry: a body carries lists and mappings no flag surface
    expresses, and a `--from project_memory/...` cannot be typed past `gate_write_scope`).

    THE TTY CHECK IS NOT COSMETIC: `read()` on a terminal waits for EOF, so a role that forgets
    the heredoc would hang its own tool call until the harness times it out -- a command that
    hangs teaches "do not use this command". Refused with the remedy instead.
    """
    if sys.stdin is None or sys.stdin.isatty():
        raise UsageError(
            "%s reads its fields as a JSON object on STDIN and nothing is piped in -- "
            "it does not prompt for them. Remedy: `%s %s <<'EOF'` … `EOF`."
            % (command, INVOCATION, command))
    # THE BODY IS A UTF-8 BYTE STREAM, DECODED HERE AND NOT BY THE CONSOLE (BUG-0018/TSK-0028).
    # `sys.stdin.read()` decodes with `sys.stdin.encoding`, which on Windows is the console
    # codepage (cp1252), so a heredoc `ü` (c3bc) arrived as the two cp1252 chars `Ã¼` and
    # `yaml.safe_dump` re-encoded them -- the item stored the double-encoded c383c2bc in a field
    # L2 makes immutable, so a user could only fix it by replacing the whole item. The bytes are
    # the same whatever the codepage; the decode is the kernel's, exactly like every file it opens
    # (state/report/schemas/layout all pass encoding="utf-8"). `buffer` is absent only when a
    # caller replaced stdin with an in-memory text stream (the in-process CLI tests), which already
    # holds decoded text -- there is nothing to decode.
    #
    # `utf-8-sig` AND NOT `utf-8` (BUG-0021): a producer that prepends a byte-order mark -- a
    # PowerShell here-string over a native pipe is the measured one -- sent `EF BB BF` ahead of the
    # JSON, and a strict `utf-8` decode kept those bytes as U+FEFF at the front, so `json.loads`
    # refused with "Unexpected UTF-8 BOM" (exit 2) while its own remedy already named `utf-8-sig`.
    # `utf-8-sig` STRIPS a single leading BOM and otherwise decodes exactly like `utf-8` -- it does
    # not undo BUG-0018: the byte stream is still the kernel's to decode, the codepage still has no
    # say, and a BOM in the MIDDLE of the body (not a real producer, but a well-formed U+FEFF) is
    # left untouched. So the stored item carries no BOM, and its hash is the hash of the JSON.
    stdin_buffer = getattr(sys.stdin, "buffer", None)
    if stdin_buffer is None:
        raw = sys.stdin.read()
    else:
        try:
            raw = stdin_buffer.read().decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise UsageError(
                "the %s body on stdin is not valid UTF-8 (%s). Remedy: send the body as UTF-8 -- "
                "the kernel stores and hashes it as UTF-8 and does not guess a console codepage."
                % (command, exc)) from None
    if not raw.strip():
        raise UsageError(
            "%s reads its fields as a JSON object on STDIN and got nothing. Remedy: "
            "pipe or heredoc the body, e.g. `%s %s <<'EOF'` … `EOF`; the fields a capture type "
            "needs are `kernel/backlog_types.REQUIRED_FIELDS` and a freeze body's keys are its "
            "operation's own parameters, and the kernel names any that are missing."
            % (command, INVOCATION, command))
    # THE BUDGET IS CHECKED ON THE BYTES, BEFORE THE PARSE, and both halves are deliberate.
    # Spec II.5 caps an active item at `report.ITEM_MAX_BYTES`, `guard_memory_budget` enforces it
    # on every TOOL write into the same tree, and `capture` went around both -- measured: a 2 MB
    # body was accepted, the item written, and only `validate` complained afterwards, about a file
    # nothing can now edit. The limit is read from the validator's own constant so there is one
    # number. Before the parse, because a body too large to keep is a body not worth parsing, and
    # because `json.loads` on a deeply nested one raises RecursionError rather than anything a
    # role could act on -- caught below for the same reason.
    if len(raw.encode("utf-8")) > report.ITEM_MAX_BYTES:
        raise UsageError(
            "the %s body is %d bytes; an active item is capped at %d (spec II.5, the same "
            "limit `python scripts/harness.py validate` reports and `guard_memory_budget` enforces "
            "on tool writes). Remedy: an item REFERENCES its detail -- send a body that fits and "
            "keep the bulk in the artefact it belongs to, named from the item. No place for it is "
            "offered here: a place named in a message is one the reader completes, and what they "
            "put there can already be taken (DEC-0024)."
            % (command, len(raw.encode("utf-8")), report.ITEM_MAX_BYTES))
    try:
        body = json.loads(raw)
    except ValueError as exc:
        raise UsageError(
            "the %s body on stdin is not JSON (%s). Remedy: send a JSON object -- JSON and "
            "not YAML because these fields are hashed into approvals, and YAML would retype `no` "
            "as false and `1.10` as a float on the way in." % (command, exc)) from None
    except RecursionError:
        raise UsageError(
            "the %s body on stdin nests too deeply for the parser. Remedy: an item is a flat "
            "record that REFERENCES its detail; nothing in a field contract needs that depth."
            % command) from None
    if not isinstance(body, dict):
        raise UsageError(
            "the %s body is a %s; an item is a JSON OBJECT of field -> value. Remedy: wrap "
            "it in braces." % (command, type(body).__name__))
    return body


def _pin_utf8() -> None:
    """Write UTF-8 whatever the console codepage is -- the approval question depends on it.

    WHICH POSITION THIS ACTUALLY SAVES, measured rather than assumed -- and the first version of
    this paragraph named the wrong one. The INSTALLED entry point was never affected: the shim
    imports `_kernel`, which imports `_compat`, which pins both streams at import time, so a
    scaffolded project prints UTF-8 with or without this function. What was cp1252 is the
    PRE-INSTALL INSTALLER POSITION (`python -B -m kernel.cli …`), which loads no hook helper at
    all -- and that is the position the entry gate uses. So this belongs in the kernel rather than
    in the shim, which is where it is.

    WHY IT MATTERS AT ALL: `request-approval` prints a question containing `für` and `…`, and
    `gate_approval` compares the asked question to the kernel's one CHARACTER FOR CHARACTER. A
    question that loses its encoding on the way out is a protocol that cannot be completed. (The
    mojibake that first surfaced this was a READER defect -- UTF-8 bytes decoded as cp1252 in a
    test subprocess -- and is fixed on that side too; the producer half is here because a role's
    console codepage is not something the harness gets to choose.)

    Failure is ignored on purpose: a stream that cannot be reconfigured (a test runner capturing
    it, a closed handle) is not a reason to refuse a command.
    `test_the_installer_position_prints_utf8_whatever_the_console_codepage_is` measures the
    position this saves, with `PYTHONIOENCODING=cp1252`, rather than counting calls to
    `reconfigure` -- which is all its predecessor did.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass


def main(argv=None) -> int:
    _pin_utf8()
    args = build_parser().parse_args(argv)
    state = ProjectState(args.root)
    try:
        if args.command == "doctor":
            data = report.doctor(state)
            # Installation defects go to stderr BEFORE the JSON and set the exit code. A comment
            # in report.py called this "the one place a reader cannot page past", and that was
            # only true of the dict: doctor printed one JSON blob and always exited 0, so the
            # loudest thing in the report was a key somewhere in the middle of it. State findings
            # keep their own channel (`validate` exits 1 on those); this is about the KIT.
            for finding in data.get("installation_errors") or []:
                sys.stderr.write("[INSTALLATION] %s: %s -- Remedy: %s\n" % (
                    finding["item"], finding["message"], finding["remedy"]))
            print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
            return 1 if data.get("installation_errors") else 0
        if args.command == "validate":
            findings = report.validate_state(state)
            for finding in findings:
                print("[%s] %s: %s -- Remedy: %s" % (
                    finding["severity"].upper(), finding["item"],
                    finding["message"], finding["remedy"],
                ))
            errors = [f for f in findings if f["severity"] == "error"]
            print("%d error(s), %d warning(s)" % (len(errors), len(findings) - len(errors)))
            # WHAT THE V1 RECORD SCAN DID NOT LOOK AT, printed with the findings and not among
            # them: it is coverage, so it carries no severity and no exit code (see
            # `report.record_scan_coverage`), and without it "no finding about that file" and "that
            # file was never read" are the same silence on this surface.
            coverage = report.record_scan_coverage(state)
            # DEPOSIT copies are COUNTED, not listed (BUG-0028): one appears per applied remedy, so a
            # line each grew this section every time the project followed the report.
            deposits = coverage.get("deposits") or []
            print("V1 record scan: searched %d document(s), did not search %d, %d deposit copy(ies)"
                  % (len(coverage["searched"]), len(coverage["not_searched"]), len(deposits)))
            for entry in coverage["not_searched"]:
                print("  NOT SEARCHED %s: %s" % (entry["path"], entry["why"]))
            # WHAT A DELIVERY HAS ALREADY CLOSED WHILE THE STATUS FIELD STILL READS OPEN
            # (DEC-0051), printed with the findings and not among them for the reason
            # `report.delivery_closure_rollup` gives: a row a project cannot clear -- and a BUG
            # whose route needs a mint the project has no way to run is exactly that -- would be a
            # finding nobody can act on. Without this line the difference between "open" and
            # "delivered, and nobody moved it" is a difference no surface shows.
            rollup = report.delivery_closure_rollup(state)
            # THE HEADLINE SAYS "ALL", not "a passing", and that is not editorial: the derivation
            # closes an item only when EVERY current verdict naming it passes, so a line reading
            # "a passing delivery Evidence names it" taught the reader the one rule
            # `closed_by_delivery` does not have -- the "any pass wins" reading its own regression
            # test exists to red. The docstring was precise and this line was not, which is the
            # half a reader actually meets.
            print("Delivered but still open: %d item(s) whose delivery verdicts ALL pass while "
                  "their status still reads otherwise" % len(rollup))
            for row in rollup:
                print("  %s %s (%s): %s" % (row["item"], row["status"],
                                            ", ".join(row["evidence"]),
                                            row["route"] or "no route on this type's chain"))
            return 1 if errors else 0
        if args.command == "generate-index":
            # Both paths, for the reason the subparser's help gives: the index is what the machines
            # read, the board is what a person opens, and the same call writes them together.
            print(state.generate_index())
            print(state.generated_path(board.FILENAME))
            return 0
        if args.command == "generate-session-brief":
            print(report.generate_session_brief(state, args.kit, args.kit_version, args.enforcement))
            return 0
        if args.command == "evidence":
            item = state.capture("EVD", {
                "kind": args.kind,
                "related": list(args.related),
                "result": args.result,
                "summary": args.summary,
                "artifact_refs": list(args.artifact_refs),
            })
            print("%s %s: %s" % (item["id"], item["kind"], item["result"]))
            return 0
        if args.command in FREEZE_COMMANDS:
            operation = FREEZE_COMMANDS[args.command]
            result = operation(state, **_freeze_body(args.command, operation))
            # STATE-RELATIVE, like every other path this surface prints or accepts: the absolute
            # one names `project_memory`, and a role who pastes it into the next command line meets
            # `gate_write_scope` instead of an answer.
            print(os.path.relpath(result["frozen"], state.root).replace(os.sep, "/"))
            # `freeze_design` is the ONE producer of a `design_refs` entry, and that list is the
            # input `dispatch` refuses a UI spawn against (II.6). Printed from the returned root
            # rather than re-read, so what is shown is what the same lock hold wrote.
            root_item = result.get("root")
            if root_item is not None:
                print("%s design_refs: %s" % (
                    root_item["id"],
                    ", ".join(str(ref) for ref in
                              field_elements(root_item.get("design_refs"))) or "-"))
            return 0
        if args.command == "capture":
            body = _json_body("capture %s" % args.item_type)
            # TSK goes through its own constructor even here: `root_revision` is denormalized from
            # the CURRENT root (spec II.2) and `dispatch.create_task` is the one thing that reads
            # it. Letting a hand-written body carry that field would be a second producer of one
            # value, and the value decides whether a lease is allowed at all.
            item = (dispatch.create_task(state, body) if args.item_type == "TSK"
                    else state.capture(args.item_type, body))
            print("%s %s" % (item["id"], item.get("status") or "-"))
            return 0
        if args.command == "create-task":
            task = dispatch.create_task(state, {
                "product_requirement": args.product_requirement,
                "derives_from": args.derives_from,
                "type": args.task_type,
                "assigned_role": args.assigned_role,
                "acceptance_refs": list(args.acceptance_refs),
                "allowed_scope": list(args.allowed_scope),
                "forbidden_scope": list(args.forbidden_scope or []),
                "required_inputs": list(args.required_inputs or []),
                "expected_outputs": list(args.expected_outputs or []),
                "dependencies": list(args.dependencies or []),
                **({"design_ref": args.design_ref} if args.design_ref else {}),
            })
            print("%s %s (%s)" % (task["id"], task["status"], task["assigned_role"]))
            return 0
        if args.command == "submit-result":
            task = dispatch.submit_result(state, _submitted_envelope(state, args))
            print("%s -> %s" % (task["id"], task["status"]))
            return 0
        if args.command == "request-approval":
            builder = approvals.LINE_MANIFEST_BUILDERS.get(args.kind)
            if builder is None:
                if not args.item_id:
                    raise UsageError(
                        "a %s approval is bound to an ITEM and none was named. Remedy: `%s "
                        "request-approval %s <ITEM_ID>`."
                        % (args.kind, INVOCATION, args.kind))
                pending = approvals.create_pending_request(state, args.kind, args.item_id)
            else:
                if args.item_id:
                    raise UsageError(
                        "a %s approval has no item -- its subject is %s. Remedy: drop %r from the "
                        "command line." % (args.kind,
                                           ", ".join(manifest_parameters(builder)), args.item_id))
                pending = approvals.create_pending_request(
                    state, args.kind,
                    manifest=_line_manifest(state, args.kind, builder, args),
                    approval_expires=time.time() + approvals.LINE_APPROVAL_VALIDITY)
            # ONLY the question object on stdout, and as JSON, because it has to be relayed
            # VERBATIM: `gate_approval` compares the asked question against `build_question`
            # field by field, so anything printed beside it is something a role might paste in.
            # The request id travels inside the text as `[APR-REQ:<id>]`; that marker is what the
            # gate resolves back to this request.
            print(json.dumps(approvals.build_question(pending), indent=2, ensure_ascii=False))
            return 0
        if args.command == "dispatch":
            # ONLY the header on stdout: it has to be copied into the spawn prompt character for
            # character (the gate compares the nonce), so anything else printed beside it is
            # something a role might copy along with it.
            lease = dispatch.create_lease(state, args.task_id)
            print(dispatch.dispatch_header(lease))
            # ...AND THE CHECKPOINT VERDICT ON STDERR, for that same rule rather than despite it:
            # the reasons are for the human composing the dispatch, and putting them on stdout
            # would make them one paste away from travelling inside the prompt. `create_lease`
            # has already decided whether the header carries the pointer; this only says why.
            sys.stderr.write(dispatch.checkpoint_verdict(state, args.task_id).summary + "\n")
            return 0
        if args.command == "checkpoint":
            stored = checkpoints.record(state, args.task_id, _json_body("checkpoint"))
            print("%s checkpoint recorded: %s (%d output(s), %d artefact(s))" % (
                stored["task_id"], checkpoints.state_relative(
                    state, checkpoints.checkpoint_path(state, args.task_id)),
                len(stored["outputs"]),
                sum(len(entry["artifacts"]) for entry in stored["outputs"])))
            return 0
        if args.command == "checkpoint-status":
            verdict = checkpoints.verify(state, args.task_id)
            print(verdict.summary)
            # 1 = "there is nothing here to adopt", exactly as `validate` uses it for findings: a
            # caller scripting the retry has to tell "adopt" from "start over" without reading
            # prose, and DEC-0044 makes absent, stale and broken ONE answer.
            return 0 if verdict.adoptable else 1
        if args.command == "transition":
            item = state.transition(args.item_id, args.to_status, approved_retry=args.approved_retry)
            print("%s -> %s" % (item["id"], item["status"]))
            return 0
        if args.command == "update":
            # The body carries only the fields that CHANGE. Every guard lives in `update_item`
            # (kernel-set fields refused, immutable types refused, frozen work-order fields refused,
            # closed vocabularies and origins asserted, approval invalidated atomically when a
            # hashed field moves) -- the CLI adds no second copy of any of those rules, so the one
            # that runs is the one the state layer states.
            body = _json_body("update %s" % args.item_id)
            item = state.update_item(args.item_id, body)
            # `revision` and `approval_ref` are printed because they are exactly what an
            # invalidating edit moves: a caller sees the approval gone (`approval_ref: -`) and the
            # revision bumped without re-reading the file.
            print("%s %s rev %s approval_ref: %s" % (
                item["id"], item.get("status") or "-", item.get("revision", 1),
                item.get("approval_ref") or "-"))
            return 0
        if args.command == "set-preset":
            result = presets.apply(state, args.preset)
            print("%s preset: %s" % (result["kit"], result["preset"]))
            # READ BACK OFF THE INSTALLATION, not off the plan: what this prints is the ownership
            # manifest the installer just wrote, so a role that did not arrive does not appear here
            # either. The lead is in that list because the installation manages it too.
            print("roles installed (lead first): %s" % (", ".join(result["installed"]) or "-"))
            print("removed: %s" % (", ".join(result["removed"]) or "-"))
            # THE RESTART IS PART OF THE ANSWER, not an afterthought: the provider reads its agent
            # set at session start, so a role installed here is not spawnable in this session and
            # the installer's handover marker stops this one deriving further. A command that
            # reported success and left the lead to discover that is the shape BUG-0016 named.
            print("RESTART REQUIRED: the new role set loads at the next session start. Tell the "
                  "user in their own words and stop deriving here.")
            return 0
        if args.command == filing.COMMAND:
            builder = approvals.LINE_MANIFEST_BUILDERS[filing.KIND]
            result = filing.apply(state, _line_manifest(state, filing.KIND, builder, args))
            rule = result["rule"]
            print("%s rule added: %s -> %s" % (filing.PLAN, rule["id"], rule["path_template"]))
            # READ BACK OFF THE FILE, not off the plan of what to write: the count is what the
            # plan now PARSES to, so a rule that did not arrive does not appear here either.
            print("rules in the plan now: %d" % result["rules"])
            # The plan grew; nothing moved. Said here because a role that reads "rule added" as
            # "document filed" would report a filing that has not happened -- `gate_filing` judges
            # the move when the move is made, against the plan as it then stands.
            print("NOT done here: no document was filed. File it now; the plan covers it.")
            return 0
        if args.command == kitupdate.COMMAND:
            result = kitupdate.apply(state)
            print("%s kit: %s -> %s" % (result["kit"], result["from"], result["to"]))
            # READ BACK OFF THE INSTALLATION, never off the plan, and BOTH readers: the stamp says
            # what the project claims to run and the bundle says what it actually runs, which is
            # the pair an aborted run makes disagree (`kitupdate._bundle_reading`).
            print("installed: %s" % result["installed"])
            print("NOT re-read: %s" % kitupdate.UNREAD)
            if result["pending_templates"]:
                print("follow-up: %s" % result["pending_templates"])
            # THE RESTART IS THE COMMAND'S LAST ACT, not a courtesy line: the registration in
            # `settings.json`, the agent set and the session agent are what this session started
            # with, while the hook FILES are already the new kit's. What actually stops the session
            # is the marker, so the line says which one and what state it was found in.
            print("RESTART REQUIRED: %s. Tell the user in their own words and stop here -- "
                  "specialist spawns are refused here; with the harness's user-global "
                  "handover guard installed, further work-engine commands and product writes "
                  "as well." % result["marker"])
            return 0
        if args.command == "archive":
            print(state.archive(args.item_id))
            return 0
        if args.command == "sweep-leases":
            # BOTH ways a lease comes back, because the remedy line that sends a role here does
            # not know which of the two it is looking at. `sweep_expired_leases` is the TTL
            # backstop; `reconcile_unstarted_dispatches` is the one for a lease spent on a spawn
            # that never started -- the case a permission refusal produces, which no hook event
            # reports. Running only the first left that case waiting the full DEFAULT_LEASE_TTL
            # after a sweep that had just told the role there was nothing to release.
            to_ready, lease_only = dispatch.sweep_expired_leases(state)
            released = sorted(set(to_ready) | set(dispatch.reconcile_unstarted_dispatches(state)))
            print("released to READY: %s" % (", ".join(released) or "-"))
            # THE OTHER HALF OF THE SAME SWEEP, and it used to be printed as part of the line above
            # while being none of it (see `sweep_expired_leases`): the lease is gone, the status is
            # not. Which of the two readings applies is not decidable from inside a session, so the
            # line says both and points at the moment that can decide -- a new session's start,
            # where `sweep_orphaned_dispatches` runs against the session that asked for the child.
            print("lease expired, status left standing: %s%s" % (
                ", ".join(sorted(lease_only)) or "-",
                " (either a child still working past its lease, or a dispatch nothing is behind "
                "any more -- this command cannot tell them apart; the next session start can)"
                if lease_only else ""))
            # THE SECOND LINE IS THE ANSWER A CALLER CAME FOR. A role runs this because a lease
            # blocked its dispatch; "released to READY: -" alone tells it the sweep found nothing
            # and leaves the length of the wait unknown, which is what turns a bounded wait into a
            # stall. `live_leases` says which leases are still running and for how long.
            print("still leased: %s" % (", ".join(
                "%s (%d s left)" % (task_id, int(left))
                for task_id, left in dispatch.live_leases(state)) or "-"))
            # A LEASED task with no lease is not a lease the sweep releases -- it is the untrue
            # bookkeeping DEC-0038 makes unreachable by a bare transition. Where old state or a
            # removed lease still shows it, the sweep REPORTS it (BUG-0010 AC-3) rather than
            # resetting it silently, so a human sees the anomaly instead of the sweep papering over it.
            print("LEASED without a lease (report only): %s" % (
                ", ".join(dispatch.leased_without_live_lease(state)) or "-"))
            return 0
        if args.command == "sweep-requests":
            swept = approvals.sweep_expired_requests(state)
            # WHAT WAS REMOVED, NAMED. A cleanup that prints a count is one nobody can check
            # afterwards; these ids are the last trace the files leave.
            print("deleted (expired, could never mint): %s" % (", ".join(
                "%s %s%s" % (entry["request_id"], entry["kind"],
                             " for %s" % entry["item"] if entry["item"] else "")
                for entry in swept["removed"]) or "-"))
            print("still open (answering one of these still mints): %s"
                  % (", ".join(swept["kept"]) or "-"))
            # ...and the third outcome, which is neither: a file this command could not judge is a
            # file it did not touch, and saying so is the difference between a store that is clean
            # and one that merely looks it.
            print("left standing because they could not be read: %s"
                  % (", ".join(swept["unreadable"]) or "-"))
            return 0
        if args.command == "migrate":
            field_map = migrate.parse_field_map(args.field_map)
            plan = migrate.build_plan(state, field_map, args.archive_year)
            digest = migrate.plan_digest(plan)
            if args.dry_run:
                print(migrate.render(plan, state))
                # 1 = "there are findings", exactly as `validate` uses it: a dry run that cannot
                # be executed as it stands is the same kind of answer as a state finding, and a
                # caller scripting this needs to tell the two apart without parsing prose.
                return 0 if migrate.plan_is_executable(plan) else 1
            if args.plan != digest:
                # A USAGE error and not a state refusal: the command was never attempted.
                #
                # WHAT THE MISMATCH DOES AND DOES NOT TELL THE CALLER, and why the answer is a
                # DECOMPOSITION rather than a list of causes. This message has now been short
                # THREE times, every time in the same direction and every time because it counted:
                # first "something under the state directory changed" while the `--map` flags are
                # in the plan too; then "the flags" while `--archive-year` is equally in it and
                # while the plan carries the WALLS, which come out of the project's `.claude/`
                # registration and not out of the state directory; and then those three while the
                # kernel's OWN contract tables decide half of what a record classifies to.
                # Measured 2026-08-07: adding one entry to `backlog_types.OPTIONAL_FIELDS` moves
                # the digest with `state_fingerprint` byte-identical, the flags unchanged and the
                # registration unchanged -- both places the message named answer nothing about it.
                #
                # A plan is a deterministic COMPUTATION, so it can move for exactly three kinds of
                # reason: what it read, what it was told, and what computed it. That is closed by
                # construction, which a list of three causes was not, and each kind is given the
                # place that answers it rather than an answer restated here.
                raise UsageError(
                    "this run is not the run the dry run presented. You passed %r; this command "
                    "line against this state digests to %s. The digest is a fingerprint of the "
                    "whole PLAN, and a plan is a computation: it moves only when one of its "
                    "inputs does, and it has three kinds of input. What the dry run READ -- the "
                    "content of the state directory, and this project's hook REGISTRATION, "
                    "because the plan records which documents are walls a gate reads (so "
                    "installing, removing or re-pointing a refusal-capable hook moves the plan "
                    "while every file under the state directory stays byte-identical). What it "
                    "was TOLD -- the flags on this command line. And the CODE AND TABLES that "
                    "computed it: a kit update between the two halves can change what the same "
                    "records classify to, with every file and every flag byte-identical. In each "
                    "case the plan you read is not the plan that would run. (WHICH files count is "
                    "`kernel/migrate.state_fingerprint`, which also names what it leaves out; "
                    "WHICH hooks count is `kernel/layout.gated_documents`; `%s doctor` reports "
                    "both -- the walls it derives from that registration, each with the gate that "
                    "reads it, and the `kit_version` this project is installed at, which is where "
                    "the third kind shows.) This command cannot tell you WHICH of them moved: it "
                    "holds the digest of the plan you read, not that plan. "
                    "Remedy: `%s migrate --dry-run` with the flags you mean, read it again, and "
                    "use the digest it prints."
                    % (args.plan, digest, INVOCATION, INVOCATION))
            result = migrate.execute(state, plan, digest)
            if not result["created"]:
                print("nothing to migrate: no record in this state is translatable and none was "
                      "written, so this run changed nothing.")
                return 0
            print("imported %d item(s): %s" % (len(result["created"]),
                                               ", ".join(result["created"])))
            print("run recorded as %s" % result["receipt"])
            # THE SAME WARNING THE DRY RUN PRINTS, on the half that actually produced the state.
            # It stood in `render` only, so the executing run said nothing about a project it had
            # just left without a root item -- and `render` is the half a scripted or scrolled-past
            # invocation never reads. `migrate.root_item_warnings` is the one text.
            for line in migrate.root_item_warnings(plan, written=True):
                print(line)
            return 0
    except UsageError as exc:
        # BEFORE the generic handler, because UsageError IS a ValueError -- the broad clause below
        # would otherwise swallow it and report "the kernel refused" for input the kernel never saw
        print(str(exc), file=sys.stderr)
        return 2
    except (StateError, TransitionError, ValueError, TimeoutError, RuntimeError) as exc:
        # TimeoutError covers LockTimeout (another kernel op holds the lock),
        # RuntimeError the missing-state-dir case -- both carry their remedy
        print(str(exc), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
