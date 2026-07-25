#!/usr/bin/env python3
"""
PreToolUse(Agent|Task) — specialist spawns require an APPROVED, un-tampered PROC reference.

The PROC is the office kit's unit of user approval (like a PRD). Opt-in checks are fake security
(leave the reference out and nothing fires), so this gate is INVERTED: once ANY approved PROC
exists, every specialist work order MUST name one, the named PROC must be APPROVED/ACTIVE, and its
steps must still hash to the recorded `approved_hash` (editing an approved PROC voids approval —
re-approve, then `python scripts/proc_hash.py PROC-xxxx --update`). Bootstrap exception: while no
PROC is APPROVED yet (onboarding/filing-plan phase), spawns pass. Uncertainty -> exit 0.
"""
import hashlib
import os
import re
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _root import find_repo_root
import _compat  # noqa: F401 — UTF-8 stream pinning (import side effect)
import _audit


def block(why):
    _audit.record("gate_proc_approved", why)
    sys.stderr.write(
        "[team-kit gate] Spawn blocked: %s\n"
        "Every specialist work order names the PROC it executes (PROC-xxxx, APPROVED/ACTIVE in "
        "project_memory/process_definitions.yaml). Editing an approved PROC's steps voids the "
        "approval — get the user's re-approval, then run `python scripts/proc_hash.py PROC-xxxx "
        "--update`.\n" % why
    )
    sys.exit(2)


def steps_hash(steps, yaml_mod):
    """Canonical hash over a PROC's steps — MUST match scripts/proc_hash.py exactly."""
    dumped = yaml_mod.safe_dump(steps, sort_keys=True, allow_unicode=True)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def main():
    # BOUNDED read (spec II.4). A raw `json.load(sys.stdin)` will happily buffer a
    # payload of any size, and an oversized one is the shape that turns a hook into
    # a memory event rather than a decision. `_compat.load` caps it at STDIN_LIMIT
    # and exits 2, because a gate that cannot read its input has not judged it.
    data = _compat.load()
    if data.get("tool_name") not in ("Agent", "Task"):
        sys.exit(0)
    inp = data.get("tool_input") or {}
    prompt = str(inp.get("prompt") or "")

    root = find_repo_root(data.get("cwd"))
    path = os.path.join(root, "project_memory", "process_definitions.yaml")
    if not os.path.isfile(path):
        sys.exit(0)  # bootstrap: no PROC registry yet
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        sys.exit(0)
    try:
        doc = yaml.safe_load(open(path, encoding="utf-8", errors="ignore").read()) or {}
    except Exception:
        # NOT exit 0. The delegation this used to make -- "guard_yaml_valid owns broken YAML" --
        # does not hold at this event: that guard fires when the file is WRITTEN, not when a spawn
        # is judged, so a registry corrupted by any other route simply disabled this gate. And the
        # question here is "is this PROC approved", which an unreadable registry cannot answer:
        # "we cannot tell" and "yes" are the same outcome only if you are willing to ship the
        # difference. Same reasoning the ledger gate arrived at, one kit over.
        _audit.record("gate_proc_approved", "unreadable PROC registry")
        sys.stderr.write(
            "[team-kit gate] the PROC registry (%s) cannot be parsed, so no spawn can be checked "
            "against an approved PROC — refused rather than passed (spec II.4 fail-closed). "
            "Remedy: `git restore %s`, or fix the YAML; `python scripts/proc_hash.py --list` "
            "shows what the file should contain.\n" % (path, path))
        sys.exit(2)
    procs = doc.get("processes") or {}
    if not isinstance(procs, dict):
        sys.exit(0)
    approved = {pid: body for pid, body in procs.items()
                if isinstance(body, dict)
                and str(body.get("status", "")).upper() in ("APPROVED", "ACTIVE")}
    if not approved:
        sys.exit(0)  # bootstrap: nothing approved yet -> onboarding spawns pass

    refs = re.findall(r"\bPROC-\d{4}\b", prompt)
    if not refs:
        block("the work order names no PROC-xxxx although approved PROCs exist")
    for pid in refs:
        body = procs.get(pid)
        if not isinstance(body, dict):
            block("%s does not exist in process_definitions.yaml" % pid)
        status = str(body.get("status", "")).upper()
        if status not in ("APPROVED", "ACTIVE"):
            block("%s has status %s — only APPROVED/ACTIVE PROCs may be executed" % (pid, status or "?"))
        recorded = str(body.get("approved_hash") or "")
        if not recorded:
            block("%s carries no approved_hash — set it at approval time via scripts/proc_hash.py" % pid)
        if steps_hash(body.get("steps"), yaml) != recorded:
            block("%s steps changed AFTER approval (hash mismatch) — the approval is void" % pid)
    sys.exit(0)


if __name__ == "__main__":
    main()
