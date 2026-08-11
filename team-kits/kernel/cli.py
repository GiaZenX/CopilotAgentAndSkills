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

from . import approvals, dispatch, migrate, report, staging
from .backlog_types import (
    EVIDENCE_KINDS,
    EVIDENCE_RESULTS,
    REQUIRED_FIELDS,
    TASK_TYPES,
    TransitionError,
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


def _worktree_head(state: ProjectState) -> str:
    """The commit a push would publish, read from the worktree the state directory sits in.

    `gate_push_token` resolves the SAME value with the same git call and binds its check to it, so
    a head a role typed from memory would mint a token for a different commit -- which is exactly
    the single-use property `push_subject_manifest` rests on. Empty string when git cannot answer;
    the caller turns that into a usage error naming the flag.
    """
    repo = os.path.dirname(os.path.abspath(state.root))
    try:
        result = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return ""
    return (result.stdout or "").strip() if result.returncode == 0 else ""


# Manifest keys the CLI can determine itself; every other key of a builder must be typed. A key
# WITH a resolver is optional on the command line, one without is required -- that is the whole
# rule, and it is why `remote` and `branch` stay mandatory: they are what the user is asked to
# authorise, so they come from the role's intent, never from whatever the machine happens to be
# checked out at.
LINE_MANIFEST_RESOLVERS = {"head": _worktree_head}


def _line_manifest(state: ProjectState, kind: str, builder, args) -> dict:
    """The subject manifest for a line kind, from the flags plus the resolvers."""
    values = {}
    for name in manifest_parameters(builder):
        value = getattr(args, name, None)
        if not value:
            resolver = LINE_MANIFEST_RESOLVERS.get(name)
            value = resolver(state) if resolver else None
        if not value:
            raise UsageError(
                "a %s approval question must say what it releases, and %s is missing. Remedy: "
                "`%s request-approval %s %s` -- the keys are the manifest the approval hashes, "
                "so the gate can compare what was approved with what is being done."
                % (kind, name, INVOCATION, kind,
                   " ".join("--%s <%s>" % (key.replace("_", "-"), key)
                            for key in manifest_parameters(builder))))
        values[name] = value
    return builder(**values)


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
    sub.add_parser("generate-index", help="regenerate generated/index.yaml")
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
    submit.add_argument("--role", required=True)
    submit.add_argument("--status-proposal", required=True,
                        choices=list(envelope_fields["status_proposal"]["enum"]))
    submit.add_argument("--summary", required=True,
                        help="<= %d chars; raw logs are REFERENCED, never inlined"
                             % envelope_fields["summary"]["max_len"])
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
            resolver = LINE_MANIFEST_RESOLVERS.get(name)
            request.add_argument(
                flag, metavar=name.upper(),
                help="%s subject: %s%s" % (line_kind, name,
                                           " (default: read from the worktree)" if resolver
                                           else ""))
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
    archive = sub.add_parser("archive", help="move a terminal item to archive/")
    archive.add_argument("item_id")
    sub.add_parser("sweep-leases", help="return expired leases to READY")
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
            return 1 if errors else 0
        if args.command == "generate-index":
            print(state.generate_index())
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
                    root_item["id"], ", ".join(root_item.get("design_refs") or []) or "-"))
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
            task = dispatch.submit_result(state, {
                "task_id": args.task_id,
                "role": args.role,
                "status_proposal": args.status_proposal,
                "summary": args.summary,
                "outputs": list(args.outputs or []),
                "evidence": list(args.evidence or []),
                "scope_touched": list(args.scope_touched or []),
                "followups": list(args.followups or []),
            })
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
            print(dispatch.dispatch_header(dispatch.create_lease(state, args.task_id)))
            return 0
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
            released = sorted(set(dispatch.sweep_expired_leases(state))
                              | set(dispatch.reconcile_unstarted_dispatches(state)))
            print("released to READY: %s" % (", ".join(released) or "-"))
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
