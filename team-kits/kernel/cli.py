"""`harness` CLI -- the command surface the fail-closed remedies point at (II.4).

Thin argparse wrapper over the kernel API. Exit codes: 0 = ok, 1 = findings/
refusal (message explains), 2 = usage error. Phase-2 scaffold installs a
`harness` launcher per project; until then: `python -m kernel.cli <cmd>` with
team-kits/ on sys.path, or via the repo checkout.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import dispatch, report
from .backlog_types import TransitionError
from .state import ProjectState, StateError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harness", description="V2 state-kernel commands (HARNESS_V2_SPEC.md II.4)"
    )
    parser.add_argument("--root", default="project_memory", help="state directory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="read-only activation/diagnosis report")
    sub.add_parser("validate", help="fail-closed state validation (exit 1 on errors)")
    sub.add_parser("generate-index", help="regenerate generated/index.yaml")
    brief = sub.add_parser("generate-session-brief", help="regenerate generated/session_brief.yaml")
    brief.add_argument("--kit", required=True)
    brief.add_argument("--kit-version", required=True)
    brief.add_argument("--enforcement", choices=["hard", "audited"], required=True)
    transition = sub.add_parser("transition", help="status transition via the automaton")
    transition.add_argument("item_id")
    transition.add_argument("to_status")
    transition.add_argument("--approved-retry", action="store_true")
    archive = sub.add_parser("archive", help="move a terminal item to archive/")
    archive.add_argument("item_id")
    sub.add_parser("sweep-leases", help="return expired leases to READY")
    return parser


def main(argv=None) -> int:
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
    except (StateError, TransitionError, ValueError, TimeoutError, RuntimeError) as exc:
        # TimeoutError covers LockTimeout (another kernel op holds the lock),
        # RuntimeError the missing-state-dir case -- both carry their remedy
        print(str(exc), file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
