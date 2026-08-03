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

import hashlib
import json
import os
import re
import subprocess
import sys
import time

from .approvals import (
    APPROVED_CONTENT_HASH_FIELD,
    ROOT_DISPATCH_KINDS,
    ApprovalError,
    approved_content_hash,
    approved_statuses,
    assert_apr_in_force,
    consumed_request,
    item_subject_manifest,
)
from .backlog_types import (
    ACTIVE_DIRS,
    AUTOMATA,
    DECLARED_REQUIRED_FIELDS,
    HASHED_FIELDS,
    PARENT_FIELDS,
    QA_EVIDENCE_KINDS,
    parse_id,
)
from .hashing import HASH_SCHEMA_VERSION, hook_bundle_hash, subject_manifest_hash
from .lock import LOCK_SCHEMA_VERSION, ext_path
from .schemas import validate
from .state import ProjectState, _now_iso

ITEM_MAX_BYTES = 12 * 1024   # spec II.5: active item <= 200 lines / 12 KB
ITEM_MAX_LINES = 200

# The next step per root status. Three of the four are "obtain an approval", and that is not
# editorial: those three edges are the ones `approvals.APPROVAL_TRANSITIONS` says an approval
# COMMITS, so `state.transition` refuses them without one and the mint walks them itself. A line
# here that said "transition it" would be telling the lead to run a command the kernel refuses.
_NEXT_STEP = {
    "DRAFT": "Scope-Freigabe einholen",
    "APPROVED": "Tasks anlegen; Delivery-Freigabe einholen (der Mint setzt IN_DELIVERY)",
    "IN_DELIVERY": "Tasks abarbeiten",
    "DELIVERED": "Abnahme einholen",
}


def _finding(severity: str, item: str, message: str, remedy: str) -> dict:
    return {"severity": severity, "item": item, "message": message, "remedy": remedy}


def _iter_active(state: ProjectState):
    """(type, stem, item, path, read error) for every ACTIVE item, over every type.

    WHICH FILES ARE ITEMS is `ProjectState.iter_active_items` and no longer this function's own
    answer. It was, with the rule "every `*.yaml` in the directory is an item", and that rule
    contradicted `state._frozen_revision_path` for the types the kernel stores per revision: a
    second `freeze_wireframe` wrote `WFR-0001.r02.yaml` beside `WFR-0001.r01.yaml`, this loop
    yielded two items carrying one id, `validate_state` reported `WFR-0001 duplicate id` and
    `gate_memory_complete` refused every merge in the project until a frozen, immutable artefact
    was deleted by hand (measured 2026-07-28, disposition row 6.5).
    """
    for item_type in sorted(ACTIVE_DIRS):
        for stem, path in state.iter_active_items(item_type):
            try:
                item = state._read_yaml(path)
                yield item_type, stem, item, path, None
            except Exception as exc:
                yield item_type, stem, None, path, exc


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

    GRAPH-WALKING DUTIES this validator owns (spec II.4 gate 4). They were named
    as open in the phase-2 review of 2026-07-25 and are implemented below; the
    reasoning is kept because it is what makes each one a decision rather than a
    rule someone happened to write:
    * `approvals/consumed/**` must be DIFF-CLEAN against HEAD. A minted request
      is immutable once written, and `approvals/**` is committed (II.2 excludes
      only kit_state.json, generated/** and the lock), so a re-hashed request --
      the one forgery `consumed_request` cannot detect arithmetically, because
      the hash function is public -- shows up as a git diff on a file that must
      never change. That turns the documented residual from "undetectable" into
      "detected at the next validate/merge".
    * `apr["expires"]` must equal `request["subject_manifest"]["expires"]`. The
      APR copy is a derived display value; if the two disagree, a human reads a
      validity the gate correctly refuses.
    * A TSK's `derives_from` must belong to its ROOT's tree -- BUG.related_pr ==
      root, CR.target_pr == root, EXP -> HYP -> RQ == root. The kernel already
      refuses phantom origins at capture, but the dispatch gate resolves
      `acceptance_refs` against the origin, so an origin from an UNRELATED root
      lets a task be judged against borrowed criteria. Authorisation is
      unaffected (that comes only from the root's approval), and the mislabel is
      recorded in a committed file and frozen outside DRAFT -- which is why it
      belongs to this graph-walking layer rather than to the hot path. A task
      deriving from a TERMINAL/archived origin (e.g. a REJECTED bug) is stale and
      should be flagged the same way.
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
                "git restore %s && python scripts/harness.py generate-index" % rel,
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
        # field duties, over BOTH contract sources (`DECLARED_REQUIRED_FIELDS`): what a stored
        # item must CARRY, not what a caller must hand `capture`. Reading the capture map alone
        # made this loop run zero times for `ARC`, `WFR` and `DSN` -- the three types whose duties
        # live in `kernel/schemas/` -- so a hand-written architecture companion with no
        # `derives_from` was reported by nobody, the finding spec II.8 names outright.
        for field in DECLARED_REQUIRED_FIELDS.get(item_type, ()):
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
                "use `python scripts/harness.py transition` with a defined status",
            ))
        elif auto and item.get("status") in auto.terminals:
            # II.2: Geschlossenes verlaesst den aktiven Kontext
            findings.append(_finding(
                "warning", item_id,
                "terminal item (%s) awaiting archive" % item.get("status"),
                "run `python scripts/harness.py archive %s`" % item_id,
            ))
        # status-dependent duties (Fable-Check 7/NIT-1)
        status = item.get("status")
        if item_type == "FR" and status == "TRIAGED" and not item.get("triage_result"):
            findings.append(_finding(
                "error", item_id, "TRIAGED without triage_result",
                "record the triage result",
            ))
        # THE APPROVAL STAMP, judged for PRESENCE and for TRUTH. Which statuses carry the duty is
        # asked of `approved_statuses` (the automaton plus `APPROVAL_TRANSITIONS`) rather than
        # written out as ("APPROVED", "ACTIVE") -- the pair this line used to carry was a copy of
        # the PROC chain, and a copy of a chain is what goes stale when the chain moves.
        # Spec II.2 lists `approved_hash` for PROC, so the DUTY stays PROC's; the second half is
        # new and is the point of stamping at all: a stamp that no longer matches the content is a
        # worse lie than a missing one, because it reads as proof.
        if item_type == "PROC" and status in approved_statuses(item_type):
            recorded = item.get(APPROVED_CONTENT_HASH_FIELD)
            if not recorded:
                findings.append(_finding(
                    "error", item_id, "%s PROC without approved_hash" % status,
                    "re-run the approval flow -- the mint stamps the hash (spec II.2)",
                ))
            else:
                try:
                    current = approved_content_hash(item_type, item)
                except (TypeError, ValueError) as exc:
                    current, recorded = None, "unhashable content (%s)" % type(exc).__name__
                if current != recorded:
                    findings.append(_finding(
                        "error", item_id,
                        "approved_hash no longer matches the PROC's own %s -- it was edited past "
                        "the kernel after approval"
                        % "/".join(HASHED_FIELDS.get(item_type, ())),
                        "restore the approved content, or re-run the approval flow for the new one",
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
        # THE PARENT BINDINGS, taken from `_parents_of` -- the same hop the graph walks, so a
        # binding the merge gate resolves and a binding this validator judges cannot be two
        # different sets. Listed instead, this knew `product_requirement`, `related_pr` and
        # `target_pr`, and `derives_from` was in none of them: an `SR`, `HYP` or `EXP` pointed at
        # an id that exists nowhere was reported by nobody, in the layer whose whole job is the
        # reference graph.
        #
        # ONE binding is judged more strictly, and it is a rule about that field rather than about
        # a type: `product_requirement` must be ACTIVE, because the dispatch gate reads the root of
        # the task it is about to lease. Every other parent may legitimately have been ARCHIVED --
        # a BUG against an accepted PR (Fable-Check 9/#1), Evidence about a task archived the moment
        # it reached VALIDATED.
        for field, ref in _parent_bindings(item_type, item):
            if ref in active_items:
                continue
            if field == "product_requirement":
                findings.append(_finding(
                    "error", item_id, "product_requirement -> %s does not exist (active)" % ref,
                    "fix the reference or restore the item",
                ))
            elif not _in_archive(state, ref):
                findings.append(_finding(
                    "error", item_id,
                    "%s -> %s exists neither active nor archived" % (field, ref),
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
    findings.extend(_check_consumed_requests_diff_clean(state))
    findings.extend(_check_approval_expiry_agrees(state, active_items))
    findings.extend(_check_task_origins(state, active_items))
    findings.extend(_check_experiment_reports(active_items))
    findings.extend(_check_premise_recheck(active_items))
    findings.extend(_check_ui_delivery_sequence(active_items))
    findings.extend(_check_dispatch_approval_presented(state, active_items))
    # staging orphans: neither an active task nor an active root item
    staging_dir = os.path.join(state.root, "staging")
    if os.path.isdir(ext_path(staging_dir)):
        for entry in sorted(os.listdir(ext_path(staging_dir))):
            # A staging KEY is a directory named after an item. The template ships `staging/.gitkeep`
            # so git can carry the empty directory, and reading that file as a key put a warning into
            # every `python scripts/harness.py validate` and every session brief of every fresh project.
            if not os.path.isdir(ext_path(os.path.join(staging_dir, entry))):
                continue
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


def _check_dispatch_approval_presented(state: ProjectState, active_items: dict) -> list:
    """WARN when a root presents a non-dispatching approval while a dispatching one is in force.

    `mint` writes `approval_ref` for every item-bound approval, and the dispatch gate's ROOT route
    reads that one field -- "the approval the root presents". So minting a `routine` or `analysis`
    approval for a root that already carries a valid scope or delivery approval MOVES the
    reference, and every implementation task under that root stops dispatching. The older approval
    is still valid; it is simply no longer the one the root presents.

    Measured 2026-07-31, and the reason this exists: nothing reported the state at all. The
    project only learns of it at the next spawn, as a refusal -- and because a `routine` is
    time-boxed and recurring by construction, it recurs at EVERY renewal, on a root that has long
    been APPROVED, where "mint them in the right order" is no advice at all.

    A WARNING, not an error: the state is legal, the remedy is a user action (re-run the scope
    approval), and a gate that blocked the merge here would block it for a permission the project
    may not need this cycle. Terminal items are skipped -- they dispatch nothing, and they already
    carry their own "awaiting archive" warning.

    THE STORE IS READ ONCE, and that is not tidiness. The first cut re-listed and re-parsed the
    whole approvals directory INSIDE the item loop, with `assert_apr_in_force` -- which reads the
    consumed request and recomputes its hash -- in the inner branch. `validate_state` runs from
    `gate_memory_complete` on every Bash call, and the shape this very round creates is the bad
    one: a routine approval is per root and is re-minted WEEKLY, so the store grows linearly while
    those roots permanently present a non-dispatching approval. Measured over 400 approvals and
    300 items: 1 affected item 0.20 s, 5 -> 1.34 s, 20 -> 5.33 s, 50 -> 13.23 s, 300 -> 87.97 s --
    past the 60 s hook timeout, and a killed hook is an ALLOW. One pass over the directory into
    `{item id: [approval, ...]}` makes it O(approvals + items) with the same verdicts.
    """
    findings = []
    approvals_dir = os.path.join(state.root, "approvals")
    if not os.path.isdir(ext_path(approvals_dir)):
        return findings
    by_item, presented_by_ref = {}, {}
    for name in sorted(os.listdir(ext_path(approvals_dir))):
        if not (name.startswith("APR-") and name.endswith(".yaml")):
            continue
        try:
            apr = state._read_yaml(os.path.join(approvals_dir, name))
        except Exception:  # noqa: BLE001 -- an unreadable approval grants nothing
            continue
        if not isinstance(apr, dict):
            continue
        presented_by_ref[name[:-5]] = apr
        if apr.get("kind") in ROOT_DISPATCH_KINDS and apr.get("item"):
            by_item.setdefault(str(apr["item"]), []).append((name[:-5], apr))
    for item_id, (item_type, item) in sorted(active_items.items()):
        apr_ref = item.get("approval_ref")
        auto = AUTOMATA.get(item_type)
        if not apr_ref or (auto and item.get("status") in auto.terminals):
            continue
        # a missing APR file is the neighbouring finding's business, not this one's
        presented = presented_by_ref.get(str(apr_ref))
        if presented is None or presented.get("kind") in ROOT_DISPATCH_KINDS:
            continue
        for name, apr in by_item.get(item_id, ()):
            try:
                assert_apr_in_force(state, apr, item)
            except ApprovalError:
                continue
            findings.append(_finding(
                "warning", item_id,
                "presents %s approval %s, while %s approval %s is still in force -- the dispatch "
                "gate's root route reads approval_ref, so tasks under this item are refused"
                % (presented.get("kind"), apr_ref, apr.get("kind"), apr.get("id") or name),
                "re-run the %s approval flow for %s to make it the presented one again; the "
                "routine/analysis approval keeps working through its own route"
                % (apr.get("kind"), item_id),
            ))
            break
    return findings


def _check_consumed_requests_diff_clean(state: ProjectState) -> list:
    """`approvals/consumed/**` must be diff-clean against HEAD.

    A minted request is immutable once written, and `approvals/**` is committed
    (II.2 excludes only kit_state.json, generated/** and the lock). Re-hashing a
    request is the ONE forgery `consumed_request` cannot detect arithmetically --
    the hash function is public, so a consistent rewrite verifies. It cannot hide
    from git, though: the file must never change after it is written, so any diff
    on it is the forgery, and the documented residual turns from "undetectable"
    into "detected at the next validate or merge".

    A repo without git, or a file not yet committed, yields nothing: this rule can
    only speak about files git is tracking.
    """
    consumed = os.path.join(state.root, "approvals", "consumed")
    if not os.path.isdir(ext_path(consumed)):
        return []
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", "approvals/consumed"],
            cwd=state.root, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    findings = []
    for line in (result.stdout or "").splitlines():
        rel = line.strip()
        if rel:
            findings.append(_finding(
                "error", rel,
                "a consumed approval request was MODIFIED after it was minted",
                "a minted request is immutable -- `git restore %s`. A re-hashed "
                "request verifies arithmetically (the hash function is public), so "
                "this diff is the only place the tampering shows." % rel,
            ))
    return findings


def _check_approval_expiry_agrees(state: ProjectState, active_items: dict) -> list:
    """`apr["expires"]` must equal `request["subject_manifest"]["expires"]`.

    The APR copy is a derived DISPLAY value; the gate reads expiry only from the
    hash-covered manifest. If the two disagree, a human reads a validity the gate
    correctly refuses -- or, worse, believes an approval is still live.
    """
    findings = []
    for item_id, (_item_type, item) in sorted(active_items.items()):
        apr_ref = item.get("approval_ref")
        if not apr_ref:
            continue
        try:
            apr = state._read_yaml(os.path.join(state.root, "approvals", apr_ref + ".yaml"))
            request = consumed_request(state, apr)
        except Exception:
            # NOT "reported above", which is what this line used to claim: the loop above only
            # reports a MISSING APR file. An approval whose consumed request is gone (revoked, or
            # never written) makes `consumed_request` raise here and the item is skipped silently
            # -- measured 2026-07-31: `0 error(s), 1 warning(s)`. It is the mirror of the other
            # unreported pair (a valid APR whose item lost its `approval_ref`, see
            # `approvals.mint`): the store can disagree with itself in both directions and this
            # validator names neither. Fail-closed downstream -- every AUTHORISATION path
            # re-derives provenance and refuses -- so what is missing is the REPORT, not the
            # protection. Closing it is a validator change of its own.
            continue
        proven = (request.get("subject_manifest") or {}).get("expires")
        shown = apr.get("expires")
        if shown != proven:
            findings.append(_finding(
                "error", item_id,
                "approval %s shows expires=%r while its hash-covered request says %r"
                % (apr_ref, shown, proven),
                "the gate reads the REQUEST, so the displayed value is the wrong one -- "
                "re-run the approval flow rather than editing either file",
            ))
    return findings


def _parent_bindings(item_type: str, item: dict):
    """(field, id) for every item this one hangs from -- ONE hop up the reference graph.

    WHICH FIELDS bind is `backlog_types.PARENT_FIELDS`, derived there from the field
    contracts -- BOTH of them, the capture-time one and the frozen types' schemas. Nothing
    here may know a list of types: `_parents_of` was one (TSK/BUG/CR/HYP/EXP), and `SR` --
    required to carry `derives_from` since the lockstep, and the natural subject of a review
    -- was missing from it. Evidence recorded against an `SR` therefore resolved to no root,
    and the merge gate answered the role that had judged the work with "nothing judges this
    work". `ARC`, `WFR` and `DSN` then repeated it for the architect and the designer, whose
    contracts live in `kernel/schemas/` rather than in `REQUIRED_FIELDS`.

    A binding field holds one id or a list of them; both spellings are normalised here, so a
    type whose contract lets it hang from several items needs no second code path. A TSK is
    that type today: `product_requirement` is the root it serves and `derives_from` the item
    whose criteria it was cut from (a BUG or CR under that root), and both are legitimate
    ways for the work to belong to the root.

    The FIELD is yielded alongside the id because the validator's message names it and one
    binding is judged more strictly than the rest -- see `validate_state`.
    """
    for field in PARENT_FIELDS.get(item_type, ()):
        value = item.get(field)
        values = value if isinstance(value, (list, tuple)) else [value]
        for one in values:
            if one:
                yield field, str(one)


def _parents_of(item_type: str, item: dict) -> list:
    """The ids of `_parent_bindings`, for the walk that only needs to know where to go next."""
    return [ref for _field, ref in _parent_bindings(item_type, item)]


def _root_of(item_type: str, item: dict):
    """The ONE item a type hangs from, or None when it names none or several.

    Its caller compares an origin's root with the task's own, and that comparison only means
    something when the origin belongs to exactly one item: a TSK names both its root and the
    item its criteria came from, so "the root of a TSK origin" has no single answer and the
    comparison is skipped -- as it always was, when this function listed the types instead.
    """
    parents = _parents_of(item_type, item)
    return parents[0] if len(parents) == 1 else None


def _hangs_from(state: ProjectState, item_id: str, target_id: str, seen: set) -> bool:
    """Does `item_id` belong to `target_id`'s tree? (transitive, cycle-safe)

    The walk goes through `read_anywhere` rather than the active map on purpose: a task is
    archived the moment it reaches VALIDATED, which is BEFORE the merge it was validated
    for. Resolving only active items would therefore lose exactly the binding a merge gate
    needs, and lose it at the one moment the work is finished.
    """
    if item_id == target_id:
        return True
    if item_id in seen:
        return False
    seen.add(item_id)
    try:
        item_type, _ = parse_id(item_id)
    except ValueError:
        return False
    item, _archived = state.read_anywhere(item_id)
    if not isinstance(item, dict):
        return False
    return any(_hangs_from(state, parent, target_id, seen)
               for parent in _parents_of(item_type, item))


def evidence_covers(state: ProjectState, evidence: dict, target_id: str) -> bool:
    """Was this Evidence recorded about `target_id`?

    Bound DIRECTLY when `related` names the item, and INDIRECTLY when it names something
    that hangs from it -- QA judges a task, and the task belongs to a root. The indirect
    hop is what replaces the V1 merge gate's file-level fallback, and it is strictly
    narrower: V1 accepted any passing entry in a file whose TEXT mentioned the target
    anywhere, including in a comment.
    """
    related = evidence.get("related") or []
    related = list(related) if isinstance(related, (list, tuple)) else [related]
    return any(_hangs_from(state, str(ref), target_id, set()) for ref in related)


def _delivery_evidence(state: ProjectState):
    """Every ACTIVE Evidence of a delivery-judging kind, as (item, ordering key).

    The one scan both verdict functions below share, so "which files are verdicts and in
    what order do they supersede each other" is answered once.

    WHICH files count -- `QA_EVIDENCE_KINDS`, i.e. the kinds that judge a delivery. An
    `audit` Evidence judges the project (II.10a), so it can neither open nor close the
    merge of one item.

    ARCHIVED evidence is deliberately not read: spec II.2 says closed things leave the
    active context, so archiving a superseded verdict is how it is retired -- visibly,
    through a kernel operation recorded in git, rather than by editing a file.

    The ordering key is `created` and then the id NUMBER (monotonic under the kernel's
    max-scan allocation, so it settles same-second ties).

    Lock-free by design. Every read here is a single item file, and this runs on the same
    tool call as `gate_memory_complete`, which already takes the lock for `validate_state`
    -- a second acquisition on that event is the interaction that turns a slow validate
    into a blocked push (see the note in that gate).
    """
    # through `iter_active_items` like every other "what is active" reader. `EVD` is not stored
    # per revision today, so this changes nothing measurable -- it is here because a private
    # listing of an active directory is the shape that produced disposition row 6.5, and this was
    # the last one inside the kernel.
    for stem, path in state.iter_active_items("EVD"):
        try:
            evidence = state._read_yaml(path)
            _type, number = parse_id(str((evidence or {}).get("id") or stem))
        except Exception:  # noqa: BLE001 -- a corrupt/misnamed file is no verdict; the
            continue       # state validator is what reports it as a finding
        if not isinstance(evidence, dict):
            continue
        if evidence.get("kind") not in QA_EVIDENCE_KINDS:
            continue
        yield evidence, (str(evidence.get("created") or ""), number)


def _newest_per_kind(records) -> dict:
    """{kind: {id, result, created}} keeping the newest record of each kind.

    A kind's newest evidence is its CURRENT verdict: a re-run supersedes its predecessor,
    and a FAIL recorded after a PASS is a regression that must close the gate again --
    which "any pass wins" could not express.
    """
    verdicts = {}
    for evidence, order in records:
        kind = evidence.get("kind")
        if kind in verdicts and order <= verdicts[kind]["_order"]:
            continue
        verdicts[kind] = {"id": evidence.get("id"), "result": evidence.get("result"),
                          "created": evidence.get("created"), "_order": order}
    for entry in verdicts.values():
        del entry["_order"]
    return verdicts


def qa_verdicts(state: ProjectState, target_id: str) -> dict:
    """The CURRENT QA verdict per Evidence kind FOR ONE item, as {kind: {id, result, created}}.

    THE definition the merge gate reads, and the reason it lives here rather than in the
    hook: "has QA passed for this item" is a question about canonical state, and a hook
    that answered it for itself would be a second implementation of the answer the harness
    and CI must give too.

    `target_id` is required. An earlier cut let it be None and meant "the store's newest
    per kind, unbound" -- but that reading collapses the whole project into one verdict,
    so a green run on one item hid an open failure on another. The caller that has no item
    asks `qa_verdicts_by_subject` instead, which keeps the grouping.

    Which evidence counts for this item is `evidence_covers`; which of several counts is
    `_newest_per_kind`; which files are verdicts at all is `_delivery_evidence`.
    """
    return _newest_per_kind(
        (evidence, order) for evidence, order in _delivery_evidence(state)
        if evidence_covers(state, evidence, target_id))


def qa_verdicts_by_subject(state: ProjectState) -> dict:
    """The current verdict per kind for EVERY item Evidence names: {subject: {kind: entry}}.

    The answer for a caller that could not determine an item -- a merge on a branch named
    after none. Reading the store as one flat newest-per-kind would be the V1 file-level
    false accept rebuilt out of typed items: one item's fresh PASS would be the project's
    verdict while another item's open FAIL sat one file away, unread. Grouping by the item
    each Evidence NAMES keeps every open verdict its own, so "nothing is currently failing"
    can be asked instead of "the last thing that happened was green".

    Grouping is by the `related` ids AS WRITTEN, without the reference-graph walk
    `evidence_covers` does: this function has no target to walk towards, and the walk would
    only merge groups that are already each judged. Evidence naming no item at all is
    grouped under its own id rather than dropped -- it judges only itself, but a `fail`
    pinned to nothing is still a `fail`, and dropping it would make the emptiest record the
    most permissive one.
    """
    groups = {}
    for evidence, order in _delivery_evidence(state):
        related = evidence.get("related") or []
        related = list(related) if isinstance(related, (list, tuple)) else [related]
        for subject in [str(ref) for ref in related] or [str(evidence.get("id"))]:
            groups.setdefault(subject, []).append((evidence, order))
    return {subject: _newest_per_kind(records) for subject, records in groups.items()}


def _check_task_origins(state: ProjectState, active_items: dict) -> list:
    """A TSK's `derives_from` must belong to its ROOT's tree, and not be stale.

    The kernel refuses phantom origins at capture (cheap, on the hot path), but
    the dispatch gate resolves `acceptance_refs` against the ORIGIN -- so an
    origin from an unrelated root lets a task be judged against borrowed
    criteria. Authorisation is unaffected (that comes only from the root's
    approval) and the mislabel sits in a committed file frozen outside DRAFT,
    which is why it belongs to this graph-walking layer rather than to dispatch.
    """
    findings = []
    for item_id, (item_type, item) in sorted(active_items.items()):
        if item_type != "TSK":
            continue
        root = item.get("product_requirement")
        origins = item.get("derives_from") or []
        origins = origins if isinstance(origins, (list, tuple)) else [origins]
        for origin in origins:
            origin = str(origin)
            if origin == root:
                continue
            entry = active_items.get(origin)
            if entry is None:
                if _in_archive(state, origin):
                    findings.append(_finding(
                        "warning", item_id,
                        "derives_from %s is archived -- the task is judged against "
                        "criteria that left the active context" % origin,
                        "re-point the task at a live origin, or archive it too",
                    ))
                continue          # non-existent origins are refused at capture
            origin_type, origin_item = entry
            auto = AUTOMATA.get(origin_type)
            if auto and origin_item.get("status") in (auto.terminals or ()):
                findings.append(_finding(
                    "warning", item_id,
                    "derives_from %s is %s (terminal) -- a task deriving from a closed "
                    "origin is stale" % (origin, origin_item.get("status")),
                    "close the task, or re-point it at the item that supersedes %s" % origin,
                ))
            origin_root = _root_of(origin_type, origin_item)
            if root and origin_root and origin_root != root:
                findings.append(_finding(
                    "error", item_id,
                    "derives_from %s belongs to %s, not to this task's root %s"
                    % (origin, origin_root, root),
                    "the dispatch gate resolves acceptance_refs against the origin, so "
                    "this task would be judged against another root's criteria -- fix "
                    "product_requirement or derives_from",
                ))
    return findings


def _check_experiment_reports(active_items: dict) -> list:
    """R7 (parity row 84): an EXP that reached ANALYZED without report evidence.

    "Report pro EXP sofort nach PASS; sonst incomplete." Without it the research
    loop can close an experiment whose result exists only in a chat message.
    """
    findings = []
    for item_id, (item_type, item) in sorted(active_items.items()):
        if item_type != "EXP" or item.get("status") != "ANALYZED":
            continue
        if not (item.get("evidence_refs") or []):
            findings.append(_finding(
                "error", item_id,
                "ANALYZED without evidence_refs -- an experiment with no report is "
                "incomplete, whatever the conversation said (parity row 84)",
                "attach the report as evidence, or move the EXP back to COMPLETED",
            ))
    return findings


def _check_premise_recheck(active_items: dict) -> list:
    """R8 (parity row 87): a decision carrying premise_invalidation_triggers, and
    newer scope work that never records a re-check.

    A WARNING on purpose: whether a trigger actually fired is a judgement no
    pattern can make, and the user's "maximal haerten" decision says heuristics
    warn, never fail closed.
    """
    triggered = [(i, it) for i, (t, it) in sorted(active_items.items())
                 if t == "DEC" and (it.get("premise_invalidation_triggers") or [])]
    if not triggered:
        return []
    findings = []
    for item_id, (item_type, item) in sorted(active_items.items()):
        if item_type not in ("PR", "RQ", "CR") or item.get("status") == "DRAFT":
            continue
        checked = {str(ref) for ref in (item.get("premise_rechecks") or [])}
        missing = [dec for dec, _ in triggered if dec not in checked]
        if missing:
            findings.append(_finding(
                "warning", item_id,
                "no premise re-check recorded against %s, which carries invalidation "
                "triggers" % ", ".join(missing[:3]),
                "the architect re-checks direction-setting decisions on every PR/CR; "
                "record the outcome in `premise_rechecks` (naming the DEC) even when "
                "nothing changed -- \"not up for renegotiation\" is forbidden",
            ))
    return findings


def _check_ui_delivery_sequence(active_items: dict) -> list:
    """R12 (parity row 107, the 4-slices incident): no SECOND user-visible item
    enters delivery while one is DELIVERED and not yet ACCEPTED.

    The point of the sequence rule is that the user SEES a slice before the next
    is built on its assumptions; four unreviewed slices in flight is how the
    incident happened.
    """
    awaiting = [i for i, (t, it) in sorted(active_items.items())
                if t in ("PR", "RQ") and it.get("class") != "technical_enabler"
                and it.get("status") == "DELIVERED"]
    if not awaiting:
        return []
    findings = []
    for item_id, (item_type, item) in sorted(active_items.items()):
        if (item_type in ("PR", "RQ") and item.get("class") != "technical_enabler"
                and item.get("status") == "IN_DELIVERY"):
            findings.append(_finding(
                "error", item_id,
                "IN_DELIVERY while %s is DELIVERED and not yet ACCEPTED -- a second "
                "user-visible slice is being built on assumptions the user has not "
                "seen confirmed (parity row 107)" % ", ".join(awaiting[:3]),
                "get %s accepted (or explicitly rejected) first" % awaiting[0],
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

# The capabilities spec II.8 names, each `verified` or `unverified`, plus the SPLIT the phase-2
# review asked for. `state_write_protection` was one value covering two different mechanisms with
# two different strengths, so a project could read "verified" while every shell command in it
# walked past the file-tool gate.
CAPABILITIES = (
    "spawn_veto",
    "approval_provenance",
    "hook_trust",
    "state_write_protection.file",
    "state_write_protection.shell",
)
# Which ones must be verified for `enforcement: hard`. All of them: II.8 says "NUR wenn alle
# notwendigen Faehigkeiten verifiziert sind", and after the split both halves are necessary --
# they guard the same directory through different doors.
_REQUIRED_FOR_HARD = frozenset(CAPABILITIES)


def _settings_layers(repo_root: str):
    """Every settings layer Claude Code merges, LOWEST precedence first.

    The local file is REAL wiring — Claude Code merges it — and reading only the committed one
    reported a hook as unregistered when it was live. The USER layer (`~/.claude/settings.json`)
    is real too and was missing: it is where `disableAllHooks` is most likely to be set, because a
    user who wants hooks off wants them off everywhere, and a project reading only its own two
    files reported full enforcement while nothing ran.

    Order is precedence order, so a caller that needs "the winning value" can take the LAST layer
    that defines a key. `_hooks_disabled` deliberately does not: see there.
    """
    # `CLAUDE_CONFIG_DIR` is Claude Code's own override for that directory. Honoured because
    # ignoring it would read a file the provider does not, and because a doctor that consults the
    # developer's real home makes its own test suite depend on whose machine it runs on.
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(
        os.path.expanduser("~"), ".claude")
    home = os.path.join(config_dir, "settings.json")
    project = os.path.join(repo_root, ".claude")
    for path in (home, os.path.join(project, "settings.json"),
                 os.path.join(project, "settings.local.json")):
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            yield data


def _hooks_disabled(repo_root: str) -> bool:
    """Claude Code's documented global kill switch. Nothing enforces anything when it is set.

    ANY layer setting it counts, rather than the highest-precedence one that mentions it. That is
    deliberately not a merge: the question here is not "what is configured" but "could a hook have
    been suppressed", and answering it wrong in the permissive direction is how a report claims
    enforcement that is not running. A project that re-enables hooks over a user-level kill switch
    is welcome to be reported as `unverified` until someone looks; the reverse mistake is silent.
    """
    return any(layer.get("disableAllHooks") is True for layer in _settings_layers(repo_root))


def _wired_hooks(repo_root: str) -> dict:
    """{hook filename: {event: set of matchers}} — only registrations that could actually FIRE.

    Four things are checked that a first cut ignored, and each of them was a settings shape in
    which NOTHING is enforced while the matrix reported `hard`:

      * the MATCHER. It is a tool-name filter, so `gate_dispatch` registered for `Edit|Write`
        never sees a spawn. Every shipped kit uses per-tool matchers, so a one-token typo silently
        upgraded a project — which is precisely the failure the `.file`/`.shell` split exists to
        prevent, reached through a different door.
      * the hook TYPE. Claude Code supports `command|http|mcp_tool|prompt|agent`; only a
        `command` runs the file this matrix is reasoning about.
      * whether the file EXISTS. A registration pointing at a missing file cannot run.
      * whether the command actually INVOKES it. `echo "see gate_write_scope.py"` mentions it.

    The command must name the hook as an ARGUMENT, not merely contain the string, and the
    invocation must not swallow the exit code (`sh -c "python gate.py; exit 0"` can never block).
    """
    wired = {}
    if _hooks_disabled(repo_root):
        return wired
    hooks_dir = os.path.join(repo_root, ".claude", "hooks")
    for layer in _settings_layers(repo_root):
        # DEFENSIVELY, because this is the tool of last resort: three malformed shapes crashed it
        # outright -- a list-valued `hooks`, a non-string matcher going into a set, an int matcher
        # reaching `re.compile`. Doctor is run precisely when a kit update half-finished or
        # somebody hand-edited the file, so it is the one program that must not die on bad input.
        hooks = layer.get("hooks")
        if not isinstance(hooks, dict):
            continue
        for event, entries in hooks.items():
            for entry in entries if isinstance(entries, list) else []:
                if not isinstance(entry, dict):
                    continue
                matcher = entry.get("matcher")
                if not isinstance(matcher, (str, type(None))):
                    matcher = "<unusable-matcher>"     # hashable, and matches no tool
                for hook in entry.get("hooks") or []:
                    if not isinstance(hook, dict) or hook.get("type", "command") != "command":
                        continue
                    command = str(hook.get("command") or "")
                    if _swallows_exit_code(command):
                        continue
                    for name in _invoked_scripts(command):
                        if not os.path.isfile(os.path.join(hooks_dir, name)):
                            continue
                        wired.setdefault(name, {}).setdefault(event, set()).add(matcher)
    return wired


# A registration whose shell rewrites the gate's exit status enforces nothing: exit 2 is the only
# code Claude Code blocks on, so `python gate.py; exit 0` is a gate that always allows. Separators
# include newline and `&` — a wrapper written across two lines is the same command, and the first
# version of this pattern accepted both as enforcement. `:` is sh's no-op and exits 0 like `true`.
_SWALLOW_RX = re.compile(
    r"(?:[;&\n]|\|\||&&)\s*(?:exit\s+0|true|:)\s*(?:[;&\n\"']|$)")


def _swallows_exit_code(command: str) -> bool:
    """Does this command throw away the gate's exit status?

    Deliberately over-eager, and the direction is the point: a false positive reports a working
    gate as `unverified` and costs someone a look at their settings; a false negative reports a
    gate that can never block as enforcement. It is also quote-BLIND, so `echo "; exit 0"` counts
    — which is the same trade, and the alternative is a shell parser inside a report.
    """
    return bool(_SWALLOW_RX.search(command or ""))


def _invoked_scripts(command: str) -> list:
    """The `.py` files this command RUNS, as opposed to merely mentions.

    The script must follow an INTERPRETER (or be the command word itself). Extracting every `.py`
    token counted `echo "see gate_dispatch.py for details"` as a registration of that gate — which
    is the same "it appears, therefore it enforces" reasoning the whole matrix exists to reject.

    A `.py` passed AS AN ARGUMENT to an already-invoked `.py` also runs. That is `_gate.py`, the
    launcher every V2 gate is now registered behind, and without this the whole matrix would read
    zero the moment the launcher shipped: doctor would see `_gate.py` registered and no gate
    anywhere. Written as the general relationship rather than as a special case for one filename —
    the previous version of this function collected findings for exactly as long as it enumerated
    shapes instead of stating what "runs" means.
    """
    names = []
    for match in re.finditer(
            r"(?:^|[;&|(]|\bsh\s+-c\s+[\"']?)\s*[\"']?"
            r"(?:(?:[^\s\"';|&]*[/\\])?(?:python[0-9.]*|py|pypy[0-9.]*)(?:\.exe)?[\"']?"
            r"(?:\s+-[^\s\"']+)*\s+[\"']?([^\s\"';|&]+\.py)"
            r"|([^\s\"';|&]+\.py))",
            command or "", re.IGNORECASE):
        token = match.group(1) or match.group(2)
        base = os.path.basename(token.replace("\\", "/"))
        if base and base not in names:
            names.append(base)
    # ...then follow the launcher chain: `A.py B.py` runs B as well, and `A.py B.py C.py` both.
    #
    # THE SECOND SCRIPT IS MATCHED IN A LOOKAHEAD, so consecutive pairs OVERLAP. Without it
    # `re.finditer` consumed `A.py B.py` whole and resumed after it, so the pair `B.py C.py` was
    # never seen and a three-link chain reported only its first two. That stopped being
    # hypothetical the day the kits registered their spawn gates as ONE chained command — office
    # runs four gates behind the launcher — and it would have read as `gate_dispatch` being
    # unregistered on PreToolUse in doctor's own capability matrix.
    for _pass in range(8):
        grew = False
        for match in re.finditer(
                r"([^\s\"';|&]+\.py)[\"']?\s+(?=[\"']?([^\s\"';|&]+\.py))", command or ""):
            first = os.path.basename(match.group(1).replace("\\", "/"))
            second = os.path.basename(match.group(2).replace("\\", "/"))
            if first in names and second not in names:
                names.append(second)
                grew = True
        if not grew:
            break
    return names


def _matches_tool(matcher, tools) -> bool:
    """Would this matcher fire for any of `tools`?

    `*`/empty means every tool. Otherwise Claude Code treats it as an unanchored regex, which is
    why `Edit|Write` matches `Edit` and nothing else here.
    """
    if matcher in (None, "", "*"):
        return True
    if not isinstance(matcher, str):
        return False          # a non-string matcher cannot fire; see the malformed-settings note
    # Claude Code matches a matcher made only of letters/digits/_/-/space/,/| EXACTLY, with `|` as
    # alternation. Treating every matcher as an unanchored regex made `"dit"` "cover" Edit and
    # `"Ag"` "cover" Agent -- registrations that fire for NOTHING, read as enforcement.
    if re.fullmatch(r"[\w\-, |]+", matcher):
        alternatives = {part.strip() for part in matcher.split("|") if part.strip()}
        return any(tool in alternatives for tool in tools)
    try:
        pattern = re.compile(matcher)
    except (re.error, TypeError):
        return False
    return any(pattern.search(tool) for tool in tools)


def _fires_for(wired: dict, name: str, event: str, tools) -> bool:
    """Is EVERY tool in the class covered by some matcher?

    `any` was the wrong quantifier and it re-created the defect the matcher check was added to
    close: `gate_dispatch` registered for `Task` alone read as a spawn veto while `Agent` spawns
    went unguarded, and `gate_write_scope` registered for `NotebookEdit` alone "protected" Edit,
    Write and MultiEdit. A class is covered when all of it is.
    """
    matchers = wired.get(name, {}).get(event)
    if not matchers:
        return False
    return all(any(_matches_tool(m, (tool,)) for m in matchers) for tool in tools)


def capability_matrix(state: ProjectState, repo_root: str = None, enumeration=None):
    """(matrix, reasons) — every enforcement capability, and WHY each reads as it does.

    `enumeration` is the `(holes, source)` pair from `_known_hole_capabilities()`. It is
    passed in rather than fetched here so that ONE report describes ONE sidecar: read twice,
    a file that changed in between produced a `capabilities` block and a `known_holes` block
    about different data, with nothing to notice it.

    Two rules govern this function, and the first review of it found nine ways the first cut
    broke them:

    1. NEVER CLAIM MORE THAN IS MEASURED. `verified` means a check ran against this project and
       passed. Anything else -- a value that cannot be determined here, a condition that library
       code cannot establish, a file that is not where this code can see it -- is `unverified`.
       Spec II.8: "nicht Feststellbares bleibt `unverified`."
    2. AN OPEN HOLE OUTRANKS A GREEN CHECK. `tools/conftest.py` defines the `known_hole` marker's
       contract as "the named capability must be reported `unverified` while this test passes".
       A first cut reported such capabilities as `verified` with a `documented_residuals` note and
       called it "not an error" -- but the only residual any user decision covers is a USER who
       deliberately types the mint code, and the shipped `known_hole` tests assert AGENT-side
       forgeries (two authored files mint; rewriting `sys.modules` mints). Those are not residuals
       of a verified capability; they are the capability not being verified.
    """
    repo_root = repo_root or os.path.dirname(state.root)
    wired = _wired_hooks(repo_root)
    reasons = {}

    def verdict(name, ok, why):
        reasons[name] = why
        return "verified" if ok else "unverified"

    spawn = _fires_for(wired, "gate_dispatch.py", "PreToolUse", ("Agent", "Task"))
    matrix = {"spawn_veto": verdict(
        "spawn_veto", spawn,
        "gate_dispatch fires on PreToolUse for Agent/Task, the only event that can DENY a spawn"
        if spawn else
        "no gate_dispatch registration fires on PreToolUse for Agent/Task — either it is not "
        "registered, its matcher excludes those tools, the file is missing, or hooks are disabled")}

    approval_pre = _fires_for(wired, "gate_approval.py", "PreToolUse", ("AskUserQuestion",))
    approval_post = _fires_for(wired, "gate_approval.py", "PostToolUse", ("AskUserQuestion",))
    scope_file = _fires_for(wired, "gate_write_scope.py", "PreToolUse",
                            ("Edit", "Write", "MultiEdit", "NotebookEdit"))
    scope_shell = _fires_for(wired, "gate_write_scope.py", "PreToolUse", ("Bash", "PowerShell"))

    matrix["state_write_protection.file"] = verdict(
        "state_write_protection.file", scope_file,
        "gate_write_scope fires on PreToolUse for the file tools" if scope_file else
        "no gate_write_scope registration fires for Edit/Write/MultiEdit")
    matrix["state_write_protection.shell"] = verdict(
        "state_write_protection.shell", scope_shell,
        "gate_write_scope fires on PreToolUse for Bash/PowerShell" if scope_shell else
        "shell writes to the state directory are not analysed — `sed -i`, `cp` and `>` bypass the "
        "file-tool gate entirely")

    # ...and provenance. Condition (ii) -- "mint() is callable ONLY from the PostToolUse hook" --
    # is one library code cannot establish about itself, which `approvals.mint` says in its own
    # docstring. A first cut "checked" it by asking whether `_assert_minting_caller` was a
    # callable attribute; deleting the CALL left that True. So it is reported as unmeasured
    # rather than assumed, and provenance cannot be verified here at all.
    matrix["approval_provenance"] = verdict(
        "approval_provenance", False,
        "the wiring conditions %s, but condition (ii) of the 2026-07-24 decision — that `mint()` "
        "is reachable ONLY from the PostToolUse hook — depends on the project's PERMISSION "
        "posture (whether an agent can run an arbitrary interpreter), which this report cannot "
        "read. Spec II.8: what cannot be determined stays `unverified`, and the mode stays "
        "`audited`."
        % ("hold" if (approval_pre and approval_post and scope_shell) else "do not hold"))

    trusted, trust_why = _hook_bundle_trust(repo_root)
    matrix["hook_trust"] = verdict("hook_trust", trusted, trust_why)

    # THE ENUMERATION WINS. Any capability a shipped `known_hole` test names is not verified,
    # whatever the wiring says -- that is the marker's contract, written before this matrix.
    holes, holes_source = enumeration if enumeration else _known_hole_capabilities()
    if not holes_source:
        # ...and NOT BEING ABLE TO READ IT wins too. This rule is the one that pulls a capability
        # down; if it could not run, then no green verdict below it was fully checked, and rule 1
        # applies. Getting this backwards would have been the worst possible incentive: deleting
        # `known_holes.json` -- one ordinary file removal -- would have SILENCED every hole and
        # turned the report greener than a correct install.
        why = ("the `known_hole` enumeration (kernel/known_holes.json) could not be read, so the "
               "rule that pulls capabilities down for asserted open paths did not run. Nothing "
               "below it can be reported as checked. Remedy: reinstall the kit, or regenerate the "
               "kit. Inside the harness checkout: `python tools/gen_known_holes.py`.")
        for name in matrix:
            if matrix[name] == "verified":
                matrix[name] = "unverified"
                reasons[name] = why
        return matrix, reasons
    for name in holes:
        if name in matrix and matrix[name] == "verified":
            matrix[name] = "unverified"
            reasons[name] = ("%s — but a `known_hole` test asserts an OPEN path for this "
                             "capability, and an asserted hole outranks a green wiring check "
                             "(tools/conftest.py)." % reasons.get(name, ""))
    return matrix, reasons


_UNMEASURABLE_HERE = {
    "approval_provenance":
        "condition (ii) of the 2026-07-24 decision — `mint()` reachable ONLY from the PostToolUse "
        "hook — is a property of the project's PERMISSION posture (can an agent run an arbitrary "
        "interpreter?), which no library can read about itself. It is not a wiring defect and no "
        "wiring change raises it.",
}


def _structural_blockers(matrix, reasons, holes):
    """{capability: why} for the required capabilities NO configuration could raise here.

    The difference this draws is the one a reader of `enforcement: audited` actually needs: a
    project that is misconfigured, versus one where the mode is a property of the harness. Both
    print the same word today, and only the first is worth fixing.

    Two structural sources, kept apart on purpose because they were masking each other:
      * a shipped `known_hole` test ASSERTS an open path (the enumeration; it outranks wiring),
      * a condition library code cannot establish about itself (_UNMEASURABLE_HERE).
    A capability that is merely unwired appears in `enforcement_blockers` and NOT here — that is
    the whole distinction. `holes` is None when the enumeration could not be read, which is itself
    structural: the rule that would pull capabilities down did not run.
    """
    if holes is None:
        return {name: "the `known_hole` enumeration could not be read, so no capability can be "
                      "reported as checked (see installation_errors)."
                for name in sorted(_REQUIRED_FOR_HARD)}
    out = {}
    for name in sorted(_REQUIRED_FOR_HARD):
        why = []
        if name in holes:
            why.append("a shipped `known_hole` test asserts an OPEN path for it, which outranks "
                       "any wiring check (tools/conftest.py); removing that test is the only "
                       "thing that changes this")
        if name in _UNMEASURABLE_HERE:
            why.append(_UNMEASURABLE_HERE[name])
        if why:
            out[name] = " Also: ".join(why)
    return out


def _kit_state_record(repo_root: str):
    """`.claude/kit_state.json` as a mapping, or None when there is nothing readable to use.

    ONE READER. The trust verdict and the raw measurement below ask different questions of this
    file and must not answer from different readings of it. There WAS a second reader,
    `_hook_bundle_trusted`, unreferenced from anywhere and answering the old way — `active` plus any
    recorded hash meant trusted, with no recomputation — so it returned True precisely where
    `_hook_bundle_trust` returns "the bundle changed since it was trusted". A dead duplicate of a
    security decision is a loaded gun for whoever calls the shorter name next; it is gone.
    """
    try:
        with open(os.path.join(repo_root, ".claude", "kit_state.json"), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def bundle_measurement(repo_root: str):
    """(recorded, actual) hex hashes of the installed bundle — either may be None.

    THE OBSERVATION, SEPARATE FROM THE CAPABILITY, and the separation is the whole point. `hook_trust`
    is pulled to `unverified` by a shipped `known_hole` no matter what this pair says — correctly,
    because the recorder is forgeable by anyone who can run scripts. But collapsing the capability
    also collapsed the only machine-readable trace of the comparison: with `gate_dispatch` replaced
    by `sys.exit(0)`, every typed field of the report — capabilities, trust_status, known_holes,
    enforcement, blockers — came out byte-identical to a clean run (measured 2026-07-27; only the
    free-text `capability_reasons["hook_trust"]` still differed, and no consumer parses prose).
    A measurement with two outcomes had become a constant.

    So the honest answer is two answers: the CAPABILITY stays down because the mechanism that
    produces the record cannot be trusted, and the OBSERVATION is published on its own, whatever
    the capability says. Deliberately blind to `disableAllHooks` and to the state machine, which
    are reasons a matching bundle is not in EFFECT — not reasons it stopped matching.
    """
    data = _kit_state_record(repo_root)
    recorded = str((data or {}).get("hook_bundle_hash") or "") or None
    return recorded, _hook_bundle_hash(repo_root)


def _hook_bundle_trust(repo_root: str):
    """(bool, reason) — does the installed bundle match the hash the project recorded?

    A first cut returned True whenever `kit_state.json` said `active` and carried ANY hash, so a
    project with no hooks directory at all read "the installed hook bundle matches the trusted
    hash". Nothing was matched. Spec II.8 wants a CHANGED hash to force `/hooks` confirmation, so
    the hash has to be recomputed and compared.
    """
    # With the global kill switch on, the bundle's hash may well match — and saying "verified"
    # beside "no hook runs" invites exactly the wrong reading. A capability describes what is in
    # EFFECT, not what is on disk.
    if _hooks_disabled(repo_root):
        return False, ("`disableAllHooks` is set, so no hook runs at all — whatever the bundle "
                       "hashes to is not in effect")
    data = _kit_state_record(repo_root)
    if data is None:
        return False, "no readable .claude/kit_state.json, so there is no recorded hash to compare"
    if data.get("state") != "active":
        return False, ("the kit update is in state %r — a changed bundle needs /hooks "
                       "confirmation and exactly one new session (spec II.8)"
                       % data.get("state"))
    recorded, actual = bundle_measurement(repo_root)
    if not recorded or actual is None:
        return False, "no hook-bundle hash to compare (recorded=%r, computed=%r)" % (
            bool(recorded), actual is not None)
    if recorded != actual:
        return False, ("the installed hooks hash to %s but the project recorded %s — the bundle "
                       "changed since it was trusted" % (actual[:12], recorded[:12]))
    return True, "the installed hook bundle hashes to the value the project recorded (%s)" % (
        actual[:12])


def _hook_bundle_hash(repo_root: str):
    """sha256 over the installed hook bundle — see `hashing.hook_bundle_hash` for THE definition.

    This used to be a second implementation (top-level `*.py`, name+content, no separators) of a
    concept `gen_provider_artifacts` already implemented differently. It therefore never produced
    the value the Codex trust binding recorded, and `hook_trust` compared two measurements of
    different things.
    """
    return hook_bundle_hash(os.path.join(repo_root, ".claude"))


def _mint_is_hook_only() -> bool:
    """Does `approvals.mint` still refuse every caller but the PostToolUse hook?

    A property of the SHIPPED code, not of configuration: `_assert_minting_caller` is the last
    check inside `mint`, and it is the whole reason a hand-written approval proves nothing.
    """
    try:
        from . import approvals
        return callable(getattr(approvals, "_assert_minting_caller", None))
    except Exception:  # noqa: BLE001
        return False


def installed_identity(state: ProjectState) -> dict:
    """What the INSTALLATION says about itself: kit, version, lead role, provider config.

    THE WIRING SPEC II.4 ASKS FOR, and it did not exist. `doctor` took `kit`/`kit_version` as
    parameters, `cli` passed neither, and `lead_role`/`provider_config` were hard-coded to
    "unknown" behind a comment promising that "phase-2 wiring fills these from the installed kit".
    Measured on a correctly installed office project: all four came back `unknown` while
    `.claude/kit_state.json` held `"kit": "office-team"` and `settings.json` held
    `agent: office-manager` two directories away. Spec II.4 lists these fields and allows
    `unknown` only for what cannot be determined -- these can.

    EVERY VALUE IS READ FROM THE INSTALLATION, never guessed: the kit name from
    `.claude/kit_state.json` (what the scaffold recorded), the version from `.claude/kit_version`
    (what the scaffold stamped), the lead role from `settings.json`'s `agent`, and the provider
    config from which generated artefacts exist. Anything unreadable stays `unknown`, which is the
    honest answer and the one the spec reserves for it.
    """
    claude_dir = os.path.join(os.path.dirname(state.root), ".claude")
    identity = {"kit": "unknown", "kit_version": "unknown",
                "lead_role": "unknown", "provider_config": "unknown"}
    try:
        with open(os.path.join(claude_dir, "kit_state.json"), encoding="utf-8") as handle:
            recorded = json.load(handle)
        if isinstance(recorded, dict) and recorded.get("kit"):
            identity["kit"] = str(recorded["kit"])
    except Exception:
        pass
    try:
        with open(os.path.join(claude_dir, "kit_version"), encoding="utf-8-sig") as handle:
            for line in handle:
                if line.startswith("version:"):
                    identity["kit_version"] = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass
    try:
        with open(os.path.join(claude_dir, "settings.json"), encoding="utf-8") as handle:
            settings = json.load(handle)
        if isinstance(settings, dict) and settings.get("agent"):
            identity["lead_role"] = str(settings["agent"])
    except Exception:
        pass
    providers = [name for name, marker in (
        ("claude", os.path.join(claude_dir, "settings.json")),
        ("codex", os.path.join(os.path.dirname(state.root), ".codex")),
    ) if os.path.exists(marker)]
    if providers:
        identity["provider_config"] = "+".join(providers)
    return identity


def doctor(state: ProjectState, kit: str = None, kit_version: str = None) -> dict:
    # ARGUMENTS WIN, THE INSTALLATION FILLS THE REST. The two parameters stay because the
    # SessionStart path knows the kit it is about to record and should not have to read it back;
    # every other caller (`cli`) passes nothing and gets the installed answer instead of `unknown`.
    identity = installed_identity(state)
    report = {
        "generated_at": _now_iso(),
        "root": state.root,
        "kit": kit or identity["kit"],
        "kit_version": kit_version or identity["kit_version"],
        # defects in the INSTALLATION rather than in the project's state -- kept separate from
        # `validator.errors`, which callers gate on, because a damaged kit is no reason to refuse
        # the user's own well-formed items. Always present, so no consumer has to guess whether an
        # absent key means "clean" or "an older report".
        "installation_errors": [],
        # spec II.4: what the kernel cannot determine is reported as `unknown` -- and these two
        # CAN be determined, from `settings.json` and the generated provider artefacts
        # (`installed_identity`). They were pinned to "unknown" behind a comment promising a
        # wiring that was never built.
        "lead_role": identity["lead_role"],
        "provider_config": identity["provider_config"],
        # filled below from what was actually read -- reporting `unknown` here while
        # `hook_trust` said "the bundle matches the trusted hash" made one report contradict
        # itself in two lines.
        "hook_bundle_hash": None,
        # ...and, as a TYPED field rather than as prose inside a capability reason, the comparison
        # itself: what the project recorded, and whether the installed bundle still hashes to it.
        # `null` is "there was nothing to compare", which is a third answer and not a quiet `false`
        # -- see `bundle_measurement` for why this may not be folded back into `hook_trust`.
        "recorded_hook_bundle_hash": None,
        "bundle_matches_recorded": None,
        "trust_status": None,
        # spec II.4 names Spezialisten among doctor's fields; it was absent entirely, not even
        # as `unknown`.
        "specialists": "unknown",
        # filled below from what is actually WIRED
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
    repo_root = os.path.dirname(state.root)
    holes, holes_source = _known_hole_capabilities()
    matrix, reasons = capability_matrix(state, repo_root, (holes, holes_source))
    recorded_bundle, actual_bundle = bundle_measurement(repo_root)
    report["hook_bundle_hash"] = actual_bundle or "unknown"
    report["recorded_hook_bundle_hash"] = recorded_bundle
    report["bundle_matches_recorded"] = (
        None if recorded_bundle is None or actual_bundle is None
        else recorded_bundle == actual_bundle)
    if report["bundle_matches_recorded"] is False:
        # An INSTALLATION defect, not a state defect, so it goes where a damaged kit goes and not
        # into `validator.errors` that callers gate on. It has to be raised somewhere typed: the
        # capability it belongs to is held at `unverified` by a `known_hole` in every case, so
        # without this line the difference between a clean project and one whose enforcement code
        # was rewritten after it was trusted appears in no field a consumer can branch on.
        report["installation_errors"].append(_finding(
            "error", ".claude/kit_state.json",
            "the installed enforcement bundle hashes to %s but this project recorded %s — it "
            "changed after trust was recorded, and every gate now runs code the project never "
            "confirmed." % (actual_bundle[:12], recorded_bundle[:12]),
            "review the difference in /hooks, then ask the user to re-run the team scaffold, "
            "which reinstalls the kit's own files and records the bundle it installed. A session "
            "cannot run it itself: `gate_write_scope` refuses a write-capable command line that "
            "names the enforcement layer, and starting a script is one."))
    report["trust_status"] = matrix.get("hook_trust", "unknown")
    report["specialists"] = _installed_specialists(repo_root)
    report["hooks_disabled"] = _hooks_disabled(repo_root)
    report["capabilities"] = matrix
    report["capability_reasons"] = reasons
    # spec II.8: `hard` only when every necessary capability is verified, otherwise `audited`.
    # The SPLIT must never RAISE the mode -- before it, `state_write_protection` was one value,
    # and splitting a single "verified" into two would have been a way to keep the verdict while
    # only half the door was locked. Both halves are required, so the split can only ever lower.
    unmet = sorted(name for name in _REQUIRED_FOR_HARD if matrix.get(name) != "verified")
    report["enforcement"] = "hard" if not unmet else "audited"
    report["enforcement_blockers"] = unmet
    # ...and, separately, THE CEILING: the best mode this installation could reach if every
    # wiring problem were fixed. Without it the report answers "are you `hard`?" and never "could
    # you be?", and a reader chasing `enforcement: audited` cannot tell a misconfigured project
    # from one where no configuration would help. Both are `audited`; only one is worth an
    # afternoon.
    #
    # The distinction is also what keeps three overlapping reasons from masking each other. Every
    # required capability here is currently held down by TWO independent mechanisms, and a review
    # showed the consequence: reverting `approval_provenance` to the naive wiring check it started
    # as — the round-1 defect — passed the entire suite, because the enumeration pulled it down
    # anyway. Naming the structural reason on its own line makes the overlap visible instead of
    # convenient, and `test_each_mechanism_holds_the_ceiling_on_its_own` kills each mutant apart.
    ceiling_reasons = _structural_blockers(matrix, reasons, holes if holes_source else None)
    report["enforcement_ceiling"] = "audited" if ceiling_reasons else "hard"
    report["enforcement_ceiling_reasons"] = ceiling_reasons
    # ...and the KNOWN HOLES the shipped suite enumerates, cross-checked against the matrix.
    #
    #   known_holes == null -- the enumeration could not be READ. `[]` would say the opposite
    #     ("looked, found none"), and the difference decides whether the matrix above means
    #     anything. Kept as two fields rather than one sentinel value so a consumer that only
    #     iterates the list cannot mistake "could not look" for "nothing to see".
    #   unknown_hole_capabilities -- a marker naming a capability that does not exist. That is a
    #     real defect: the enumeration and the matrix have drifted, and the cross-check for that
    #     capability can never fire again. It happened immediately: splitting
    #     `state_write_protection` left two markers pointing at a name the matrix no longer has.
    #
    # There is deliberately no `documented_residuals`. It existed while a verified capability
    # could carry an asserted hole beside it; rule 2 ended that, so the field could only ever be
    # empty -- and an always-empty "no residuals" line reads as reassurance.
    report["environment_notes"] = _environment_notes(repo_root)
    report["known_holes"] = sorted(holes) if holes_source else None
    report["known_holes_source"] = holes_source
    # WHICH kernel answered. Two now legitimately exist on one machine — `<repo>/.claude/kernel`
    # installed by the scaffold and `~/.claude/team-kits/kernel` from the installer — and the
    # capability matrix measures the PROJECT'S bundle while this enumeration comes from whichever
    # package is executing. A doctor run from the global staging over a project with a stale
    # `.claude/kernel` describes two different kernels in one report and says so nowhere.
    report["kernel_path"] = os.path.dirname(os.path.abspath(__file__))
    project_kernel = os.path.join(repo_root, ".claude", "kernel")
    foreign = False
    if os.path.isdir(project_kernel):
        try:
            foreign = not os.path.samefile(project_kernel, report["kernel_path"])
        except OSError:
            foreign = True
    if foreign:
        report["environment_notes"].append(
            "this report was produced by the kernel at %s, but the project installed its own at "
            "%s — the capability matrix measures the project's bundle while the `known_hole` "
            "enumeration comes from the running package. Remedy: run `python scripts/harness.py doctor` from the "
            "project's kernel, or re-run the scaffold so the two agree."
            % (report["kernel_path"], project_kernel))
    report["unknown_hole_capabilities"] = sorted(
        name for name in holes if name not in matrix)
    if report["unknown_hole_capabilities"]:
        # Called a real defect two comments up, and it has to BE one: a marker naming a
        # capability the matrix does not have is a cross-check that can never fire again,
        # and it was QUIETER than a missing sidecar until this finding existed.
        report["installation_errors"].append(_finding(
            "error", "kernel/known_holes.json",
            "the enumeration names %s, which is not a capability this doctor knows — the cross-check for it can never fire, so whatever hole that test asserts is invisible here."
            % ", ".join(report["unknown_hole_capabilities"]),
            "rename the marker to a capability in `report.CAPABILITIES`, or add the capability."))
    if not holes_source:
        # Loud, and deliberately NOT in `validator.errors`. That list is findings about the
        # PROJECT'S STATE, which callers gate on; a damaged installation is not a reason to refuse
        # the user's own well-formed items. It is a reason to distrust the matrix above — which is
        # what this field says, in the one place a reader cannot page past.
        report["installation_errors"].append(_finding(
            "error", "kernel/known_holes.json",
            "the `known_hole` enumeration is missing or unreadable, so doctor cannot report any "
            "capability as verified — the whole matrix above is `unverified` for that reason "
            "alone, and the mode is `audited`.",
            "reinstall the kit (a project has no `tools/`; inside the harness checkout, "
            "`python tools/gen_known_holes.py` regenerates it)."))
    index_path = os.path.join(state.root, "generated", "index.yaml")
    report["index_present"] = os.path.exists(ext_path(index_path))
    return report


def _environment_notes(repo_root: str) -> list:
    """Environment facts that WEAKEN a capability without falsifying it.

    Both of these came out of phase-2 reviews and belong here rather than in a gate:

      * Python < 3.11 has no `-P`, so the office ledger validator runs with the script directory
        on `sys.path` and a `scripts/csv.py` could shadow a stdlib module it imports. The gate
        omits the flag rather than pretending; the honest place to say so is this report.
      * an interpreter INSIDE the repo (`.venv/`) is one an agent can write. A gate cannot check
        that meaningfully -- it would execute on the very interpreter it distrusts -- so it is
        reported instead of guarded, which is where a reviewer put it.
    """
    notes = []
    if sys.version_info < (3, 11):
        notes.append(
            "python %d.%d has no `-P`: the ledger validator runs with its script directory on "
            "sys.path, so a file placed in `scripts/` can shadow a stdlib module it imports. "
            "Remedy: run the project on 3.11+." % sys.version_info[:2])
    # The matrix describes ONE provider surface: `.claude/settings.json` and the layers Claude
    # Code merges. A project that also runs Codex enforces through `.codex/hooks.json`, generated
    # from the same source but a separate file with its own event set and its own trust binding.
    # Reporting a single matrix over a two-provider project is not wrong so much as narrower than
    # it looks, and spec II.8 asks for the mode of the INSTALLATION. Named here rather than
    # silently, until the matrix reads both surfaces.
    codex = os.path.join(repo_root, ".codex", "hooks.json")
    if os.path.isfile(codex):
        notes.append(
            "this project also has a Codex surface (.codex/hooks.json) and the capability matrix "
            "above describes the CLAUDE one only — a gate can be registered for one provider and "
            "not the other. Remedy: re-run the scaffold, which generates both from the same "
            "settings, and read the Codex bundle-trust line in /hooks separately.")
    try:
        executable = os.path.realpath(sys.executable)
        inside = os.path.realpath(repo_root)
        if executable.startswith(inside + os.sep):
            notes.append(
                "the interpreter running the hooks lives INSIDE the repo (%s), and an agent can "
                "write there. No gate can check this credibly -- it would run on the interpreter "
                "it distrusts. Remedy: run the harness on an interpreter outside the project."
                % os.path.relpath(executable, inside))
    except (OSError, ValueError):
        pass
    return notes


def _installed_specialists(repo_root: str) -> list:
    """The specialist agents actually installed — spec II.4 names them among doctor's fields."""
    agents = os.path.join(repo_root, ".claude", "agents")
    try:
        return sorted(n[:-3] for n in os.listdir(agents) if n.endswith(".md"))
    except OSError:
        return []


def _known_hole_capabilities():
    """(capabilities, source) — what a shipped `known_hole` test says is NOT closed.

    `source` is "sidecar" when the generated enumeration was read, and None when it could not be.
    THAT DISTINCTION IS THE POINT. A first cut regex-scanned the harness's own test files, which
    do not exist in a scaffolded project — so it returned `[]` there, and `[]` reads as an
    affirmative "no known holes" rather than "could not look". Since the enumeration is what
    forces a capability down (rule 2 in `capability_matrix`), being unable to read it silently
    switched the governing rule off in every environment except the one the tests run in, and one
    unchanged project got different verdicts depending on where the kernel package sat.

    The sidecar (`kernel/known_holes.json`, generated by `tools/gen_known_holes.py` from pytest's
    own marker collection) travels with the kernel.

    IT IS CHECKED AGAINST A DIGEST HELD IN CODE. Without it the two tampers had opposite prices:
    DELETING the file cost every capability (the branch above), while writing
    `{"capabilities": {}}` over it silenced every asserted hole for free and turned
    `state_write_protection.shell` green — the cheapest edit was the profitable one.

    WHAT THE DIGEST DOES AND DOES NOT BUY, stated precisely because the first version of this
    comment overclaimed it. It raises the price of a SILENT edit from one file to two, and it
    catches every accidental deviation: a stale sidecar after a new marker, a BOM from a Windows
    redirect, a truncated write, a hand-fix someone meant to regenerate. It does NOT stop someone
    who edits both files: they sit in one directory behind one guard. The cost that does not
    depend on the attacker's diligence comes from elsewhere — both files are inside
    `hashing.BUNDLE_SUBTREES`, so any edit changes the enforcement bundle's hash and drops
    `hook_trust` to `unverified` at the next session start. In the harness checkout, where
    `team-kits/kernel` sits under no `.claude`, even that does not apply; there the pin is CI.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "known_holes.json")
    try:
        with open(path, encoding="utf-8") as handle:
            payload = handle.read()
    except OSError:
        return [], None
    try:
        from .known_holes_digest import KNOWN_HOLES_SHA256
    except Exception:  # noqa: BLE001
        # NOT just ImportError. A module truncated mid-write raises SyntaxError, and that is the
        # very "half-finished kit update" this whole layer exists for -- uncaught it propagated
        # out of doctor() and produced a traceback and ZERO report, exactly when the report is
        # the thing someone needs.
        return [], None
    if hashlib.sha256(payload.encode("utf-8")).hexdigest() != KNOWN_HOLES_SHA256:
        return [], None
    try:
        data = json.loads(payload)
    except ValueError:
        return [], None
    capabilities = data.get("capabilities") if isinstance(data, dict) else None
    if not isinstance(capabilities, dict):
        return [], None
    return sorted(capabilities), "sidecar"
