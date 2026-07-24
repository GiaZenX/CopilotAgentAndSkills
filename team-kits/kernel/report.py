"""Session brief, state validator and doctor (HARNESS_V2_SPEC.md II.4/II.5) -- 1.4c.

- generate_session_brief: a new session works from generated/session_brief.yaml
  plus active items ALONE -- never from transcripts (II.5). Content contract =
  kernel/schemas/session_brief.yaml, validated before writing.
- validate_state: the fail-closed layer-4 validator -- full field duties
  (incl. status-dependent ones), the reference graph, approval integrity with
  the D/4 content-hash check (out-of-band edits invalidate approvals visibly),
  staging orphans, id uniqueness, budgets, lease/request hygiene. Returns
  findings; gates block on any severity=error finding.
- doctor: read-only activation/diagnosis report (II.4) -- never writes state.

Language convention (II.10a parity rule "Deutsch zum User / Englisch in
Artefakten"): code, comments and identifiers are English; USER-FACING strings
(next_step texts, the approval question in approvals.py) are German.

Deferred validator duties (documented, not findings): INV check-test existence/
collectability -> pytest/CI integration (phase 2, B.2-10); cross-BRANCH id
uniqueness -> gate layer 5 / CI at merge; routine/analysis APR expiry ->
dispatch TODO (II.10a).
"""
from __future__ import annotations

import os
import time

from .approvals import item_subject_manifest
from .backlog_types import ACTIVE_DIRS, AUTOMATA, REQUIRED_FIELDS, parse_id
from .hashing import HASH_SCHEMA_VERSION, subject_manifest_hash
from .lock import LOCK_SCHEMA_VERSION, ext_path
from .schemas import validate
from .state import ProjectState, _now_iso

ITEM_MAX_BYTES = 12 * 1024   # spec II.5: active item <= 200 lines / 12 KB
ITEM_MAX_LINES = 200

_NEXT_STEP = {
    "DRAFT": "Scope-Freigabe einholen",
    "APPROVED": "Tasks anlegen / Delivery starten",
    "IN_DELIVERY": "Tasks abarbeiten",
    "DELIVERED": "Abnahme einholen",
}


def _finding(severity: str, item: str, message: str, remedy: str) -> dict:
    return {"severity": severity, "item": item, "message": message, "remedy": remedy}


def _iter_active(state: ProjectState):
    for item_type in sorted(ACTIVE_DIRS):
        base = state.active_dir(item_type)
        if not os.path.isdir(ext_path(base)):
            continue
        for name in sorted(os.listdir(ext_path(base))):
            if not name.endswith(".yaml"):
                continue
            path = os.path.join(base, name)
            try:
                item = state._read_yaml(path)
                yield item_type, name[:-5], item, path, None
            except Exception as exc:
                yield item_type, name[:-5], None, path, exc


# -- session brief -------------------------------------------------------------

def generate_session_brief(
    state: ProjectState, kit: str, kit_version: str, enforcement_mode: str
) -> str:
    with state.lock:
        roots, tasks = [], []
        for item_type, stem, item, _path, exc in _iter_active(state):
            if exc or not isinstance(item, dict):
                continue
            if item_type in ("PR", "RQ"):
                roots.append({
                    "id": item.get("id", stem),
                    "title": item.get("title", ""),
                    "status": item.get("status", ""),
                    "next_step": _NEXT_STEP.get(item.get("status"), "-"),
                })
            elif item_type == "TSK":
                row = {
                    "id": item.get("id", stem),
                    "status": item.get("status", ""),
                    "assigned_role": item.get("assigned_role", ""),
                }
                if item.get("blocked_by"):
                    row["blocked_by"] = item["blocked_by"]
                tasks.append(row)
        pending, expired_requests = [], 0
        pending_dir = os.path.join(state.root, "approvals", "pending")
        if os.path.isdir(ext_path(pending_dir)):
            for name in sorted(os.listdir(ext_path(pending_dir))):
                if not name.endswith(".yaml"):
                    continue
                try:
                    request = state._read_yaml(os.path.join(pending_dir, name))
                except Exception:
                    continue
                if time.time() > float(request.get("expires_at_epoch", 0)):
                    # an expired request can never mint -- never show it as
                    # open (Fable-Check 9/NIT-8), only count it
                    expired_requests += 1
                    continue
                pending.append({
                    "request_id": request["request_id"],
                    "kind": request["kind"],
                    "item": request.get("item") or request["kind"],
                })
        staging = []
        staging_dir = os.path.join(state.root, "staging")
        if os.path.isdir(ext_path(staging_dir)):
            staging = ["staging/%s/" % d for d in sorted(os.listdir(ext_path(staging_dir)))]
        findings = validate_state(state, _locked=True)
        brief = {
            "kit": kit,
            "kit_version": kit_version,
            "enforcement_mode": enforcement_mode,
            "generated_at": _now_iso(),
            "active_roots": roots,
            "active_tasks": tasks,
            "open_approvals": pending,
            "staging_pointers": staging,
            "budget_status": {
                "validator_errors": sum(1 for f in findings if f["severity"] == "error"),
                "validator_warnings": sum(1 for f in findings if f["severity"] == "warning"),
                "expired_requests": expired_requests,
            },
        }
        validate(brief, "session_brief")
        path = os.path.join(state.root, "generated", "session_brief.yaml")
        state._write_yaml_atomic(path, brief)
        return path


# -- state validator (gate layer 4) --------------------------------------------

def validate_state(state: ProjectState, _locked: bool = False) -> list:
    """Full fail-closed scan; returns findings (empty = valid).

    `_locked=True` skips taking the kernel lock -- ONLY for callers that
    either already hold it (generate_session_brief) or are explicitly
    read-only-racy by design (doctor). Everyone else uses the default.
    """
    if not _locked:
        with state.lock:
            return validate_state(state, _locked=True)
    findings = []
    seen_ids = {}
    active_items = {}
    for item_type, stem, item, path, exc in _iter_active(state):
        rel = os.path.relpath(path, state.root)
        if exc or not isinstance(item, dict):
            findings.append(_finding(
                "error", stem, "corrupt item file (%s)" % (exc or "non-mapping"),
                "git restore %s && harness generate-index" % rel,
            ))
            continue
        item_id = item.get("id", stem)
        active_items[item_id] = (item_type, item)
        if item_id in seen_ids:
            findings.append(_finding(
                "error", item_id, "duplicate id (also at %s)" % seen_ids[item_id],
                "merge/rename one of the two items -- ids are unique (spec II.4 gate 5)",
            ))
        seen_ids[item_id] = rel
        # field duties: capture-time requireds
        for field in REQUIRED_FIELDS.get(item_type, ()):
            if field not in item:
                findings.append(_finding(
                    "error", item_id, "missing required field %r" % field,
                    "add the field (spec II.2 Pflichtfelder)",
                ))
        # status validity
        auto = AUTOMATA.get(item_type)
        if auto and item.get("status") not in auto.states:
            findings.append(_finding(
                "error", item_id, "unknown status %r" % item.get("status"),
                "use `harness transition` with a defined status",
            ))
        elif auto and item.get("status") in auto.terminals:
            # II.2: Geschlossenes verlaesst den aktiven Kontext
            findings.append(_finding(
                "warning", item_id,
                "terminal item (%s) awaiting archive" % item.get("status"),
                "run `harness archive %s`" % item_id,
            ))
        # status-dependent duties (Fable-Check 7/NIT-1)
        status = item.get("status")
        if item_type == "FR" and status == "TRIAGED" and not item.get("triage_result"):
            findings.append(_finding(
                "error", item_id, "TRIAGED without triage_result",
                "record the triage result",
            ))
        if item_type == "PROC" and status in ("APPROVED", "ACTIVE") and not item.get("approved_hash"):
            findings.append(_finding(
                "error", item_id, "%s PROC without approved_hash" % status,
                "re-run the approval flow to stamp the hash",
            ))
        if item_type == "PR" and item.get("class") != "technical_enabler" and not item.get("user_story"):
            findings.append(_finding(
                "warning", item_id, "user_story missing (class %r)" % item.get("class"),
                "add a user_story or set class technical_enabler",
            ))
        if item_type == "INV" and not (("text" in item) ^ ("value" in item)):
            findings.append(_finding(
                "error", item_id, "INV needs exactly one of text|value",
                "set exactly one of the two",
            ))
        # budgets (spec II.5)
        try:
            size = os.path.getsize(ext_path(path))
            with open(ext_path(path), encoding="utf-8") as fh:
                lines = sum(1 for _ in fh)
            if size > ITEM_MAX_BYTES or lines > ITEM_MAX_LINES:
                findings.append(_finding(
                    "error", item_id,
                    "item exceeds budget (%d bytes / %d lines; max %d/%d)"
                    % (size, lines, ITEM_MAX_BYTES, ITEM_MAX_LINES),
                    "move detail to staging/evidence and reference it (spec II.5)",
                ))
        except OSError:
            pass
    # reference graph + approval integrity (D/4)
    for item_id, (item_type, item) in active_items.items():
        # a TSK's root must be ACTIVE (dispatch depends on it) ...
        ref = item.get("product_requirement")
        if ref and ref not in active_items:
            findings.append(_finding(
                "error", item_id, "product_requirement -> %s does not exist (active)" % ref,
                "fix the reference or restore the item",
            ))
        # ... while related_pr/target_pr may legitimately point at ARCHIVED
        # items (a BUG against an accepted PR; Fable-Check 9/#1)
        for ref_field in ("related_pr", "target_pr"):
            ref = item.get(ref_field)
            if ref and ref not in active_items and not _in_archive(state, ref):
                findings.append(_finding(
                    "error", item_id, "%s -> %s exists neither active nor archived" % (ref_field, ref),
                    "fix the reference or restore the item",
                ))
        for dep in item.get("dependencies") or []:
            if dep not in active_items and not _in_archive(state, dep):
                findings.append(_finding(
                    "error", item_id, "dependency %s does not exist" % dep,
                    "fix the dependency list",
                ))
        apr_ref = item.get("approval_ref")
        if apr_ref:
            apr_path = os.path.join(state.root, "approvals", apr_ref + ".yaml")
            try:
                apr = state._read_yaml(apr_path)
            except Exception:
                findings.append(_finding(
                    "error", item_id, "approval_ref %s has no APR file" % apr_ref,
                    "manually written approvals never count -- re-run the approval flow",
                ))
                continue
            if apr.get("revoked"):
                findings.append(_finding(
                    "error", item_id, "approval %s is revoked" % apr_ref,
                    "obtain a fresh approval",
                ))
            if apr.get("revision") != item.get("revision"):
                findings.append(_finding(
                    "error", item_id,
                    "revision %s no longer matches approval revision %s"
                    % (item.get("revision"), apr.get("revision")),
                    "out-of-band edit invalidated approval; re-approve or revert (D/4)",
                ))
            elif apr.get("kind") in ("scope", "acceptance", "delivery"):
                try:
                    current = subject_manifest_hash(item_subject_manifest(item, apr["kind"]))
                except Exception:
                    current = None
                if current != apr.get("subject_manifest_hash"):
                    findings.append(_finding(
                        "error", item_id,
                        "content hash no longer matches approval %s" % apr_ref,
                        "out-of-band edit invalidated approval; re-approve or revert (D/4)",
                    ))
    # staging orphans: neither an active task nor an active root item
    staging_dir = os.path.join(state.root, "staging")
    if os.path.isdir(ext_path(staging_dir)):
        for entry in sorted(os.listdir(ext_path(staging_dir))):
            if entry not in active_items:
                findings.append(_finding(
                    "warning", "staging/%s" % entry,
                    "orphaned staging dir (no active task or root item)",
                    "promote, archive or remove via the kernel staging lifecycle",
                ))
    # lease hygiene
    lease_dir = os.path.join(state.root, "tasks", "leases")
    if os.path.isdir(ext_path(lease_dir)):
        for name in sorted(os.listdir(ext_path(lease_dir))):
            if not name.endswith(".lease.yaml"):
                continue
            task_id = name[: -len(".lease.yaml")]
            if task_id not in active_items:
                findings.append(_finding(
                    "warning", task_id, "lease without active task",
                    "remove the lease (doctor) -- sweep cannot resolve it",
                ))
    # stale-break remnants (lock module leftovers)
    for name in os.listdir(ext_path(state.root)):
        if name.startswith(".kernel.lock.stale-"):
            findings.append(_finding(
                "warning", name, "stale-break remnant lockfile",
                "safe to delete after inspection (doctor)",
            ))
    return findings


def _in_archive(state: ProjectState, item_id: str) -> bool:
    try:
        item_type, _ = parse_id(item_id)
    except ValueError:
        return False
    base = os.path.join(state.root, "archive", item_type)
    if not os.path.isdir(ext_path(base)):
        return False
    for year in os.listdir(ext_path(base)):
        if os.path.exists(ext_path(os.path.join(base, year, item_id + ".yaml"))):
            return True
    return False


# -- doctor (read-only, never writes state; spec II.4) -------------------------

def doctor(state: ProjectState, kit: str = None, kit_version: str = None) -> dict:
    report = {
        "generated_at": _now_iso(),
        "root": state.root,
        "kit": kit or "unknown",
        "kit_version": kit_version or "unknown",
        # spec II.4: what the kernel cannot determine is reported as `unknown`
        # (phase-2 wiring fills these from the installed kit)
        "lead_role": "unknown",
        "provider_config": "unknown",
        "hook_bundle_hash": "unknown",
        "trust_status": "unknown",
        "capabilities": "unknown",
        "state_version": {
            "lock_schema": LOCK_SCHEMA_VERSION,
            "hash_schema": HASH_SCHEMA_VERSION,
        },
    }
    lock_path = state.lock.lock_path
    if os.path.exists(ext_path(lock_path)):
        try:
            payload = state._read_yaml(lock_path)
            report["lock"] = {
                "held_by_pid": payload.get("pid"),
                "age_seconds": round(max(0.0, time.time() - float(payload.get("acquired_at", 0))), 1),
                "ttl": payload.get("ttl"),
            }
        except Exception:
            report["lock"] = {"state": "unreadable (corrupt lockfile)"}
    else:
        report["lock"] = {"state": "free"}
    leases = []
    lease_dir = os.path.join(state.root, "tasks", "leases")
    if os.path.isdir(ext_path(lease_dir)):
        for name in sorted(os.listdir(ext_path(lease_dir))):
            if name.endswith(".lease.yaml"):
                try:
                    lease = state._read_yaml(os.path.join(lease_dir, name))
                    leases.append({
                        "task_id": lease.get("task_id"),
                        "agent_id": lease.get("agent_id"),
                        "expired": time.time() > float(lease.get("created_epoch", 0)) + float(lease.get("ttl", 0)),
                    })
                except Exception:
                    leases.append({"task_id": name, "state": "corrupt"})
    report["leases"] = leases
    # read-only scan WITHOUT taking the lock: doctor must work while a kernel
    # operation (or a stale holder) holds it -- diagnosis may see mid-write
    # snapshots, which is acceptable for a report that never writes state
    findings = validate_state(state, _locked=True)
    report["validator"] = {
        "errors": [f for f in findings if f["severity"] == "error"],
        "warnings": [f for f in findings if f["severity"] == "warning"],
    }
    index_path = os.path.join(state.root, "generated", "index.yaml")
    report["index_present"] = os.path.exists(ext_path(index_path))
    return report
