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
import json
import sys

from . import approvals, dispatch, report
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
    task.add_argument("--allowed-scope", required=True, action="append", dest="allowed_scope",
                      metavar="PATH", help="what the specialist may write (repeatable); this IS "
                                           "gate layer 3's input")
    task.add_argument("--forbidden-scope", action="append", dest="forbidden_scope", metavar="PATH")
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
    request = sub.add_parser(
        "request-approval",
        help="open the approval question for an item (phase 1); the USER mints by answering it")
    request.add_argument("kind", choices=sorted(approvals.item_derived_kinds()))
    request.add_argument("item_id", metavar="ITEM_ID")
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
    archive = sub.add_parser("archive", help="move a terminal item to archive/")
    archive.add_argument("item_id")
    sub.add_parser("sweep-leases", help="return expired leases to READY")
    return parser


def _json_body() -> dict:
    """The JSON object a `capture` was given on stdin, or a UsageError naming what went wrong.

    THE TTY CHECK IS NOT COSMETIC: `read()` on a terminal waits for EOF, so a role that forgets
    the heredoc would hang its own tool call until the harness times it out -- a command that
    hangs teaches "do not use this command". Refused with the remedy instead.
    """
    if sys.stdin is None or sys.stdin.isatty():
        raise UsageError(
            "capture reads the item's fields as a JSON object on STDIN and nothing is piped in -- "
            "it does not prompt for them. Remedy: `%s capture <TYPE> <<'EOF'` … `EOF`."
            % INVOCATION)
    raw = sys.stdin.read()
    if not raw.strip():
        raise UsageError(
            "capture reads the item's fields as a JSON object on STDIN and got nothing. Remedy: "
            "pipe or heredoc the body, e.g. `%s capture PR <<'EOF'` … `EOF`; the fields a type "
            "needs are `kernel/backlog_types.REQUIRED_FIELDS`, and the kernel names any that are "
            "missing." % INVOCATION)
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
            "the capture body is %d bytes; an active item is capped at %d (spec II.5, the same "
            "limit `python scripts/harness.py validate` reports and `guard_memory_budget` enforces "
            "on tool writes). Remedy: an item REFERENCES its detail -- put the bulk in "
            "staging/<key>/ or an Evidence artefact and name it from the item."
            % (len(raw.encode("utf-8")), report.ITEM_MAX_BYTES))
    try:
        body = json.loads(raw)
    except ValueError as exc:
        raise UsageError(
            "the capture body on stdin is not JSON (%s). Remedy: send a JSON object -- JSON and "
            "not YAML because these fields are hashed into approvals, and YAML would retype `no` "
            "as false and `1.10` as a float on the way in." % exc) from None
    except RecursionError:
        raise UsageError(
            "the capture body on stdin nests too deeply for the parser. Remedy: an item is a flat "
            "record that REFERENCES its detail; nothing in a field contract needs that depth."
        ) from None
    if not isinstance(body, dict):
        raise UsageError(
            "the capture body is a %s; an item is a JSON OBJECT of field -> value. Remedy: wrap "
            "it in braces." % type(body).__name__)
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
        if args.command == "capture":
            body = _json_body()
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
            # ONLY the question object on stdout, and as JSON, because it has to be relayed
            # VERBATIM: `gate_approval` compares the asked question against `build_question`
            # field by field, so anything printed beside it is something a role might paste in.
            # The request id travels inside the text as `[APR-REQ:<id>]`; that marker is what the
            # gate resolves back to this request.
            print(json.dumps(
                approvals.build_question(
                    approvals.create_pending_request(state, args.kind, args.item_id)),
                indent=2, ensure_ascii=False))
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
        if args.command == "archive":
            print(state.archive(args.item_id))
            return 0
        if args.command == "sweep-leases":
            released = dispatch.sweep_expired_leases(state)
            print("released to READY: %s" % (", ".join(released) or "-"))
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
