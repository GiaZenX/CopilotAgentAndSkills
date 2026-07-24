"""Two-phase approval provenance (HARNESS_V2_SPEC.md II.2) -- step 1.4b.

A manual `approved_by: user` proves nothing. The kernel:
1. writes an immutable PENDING request (request_id, item, revision,
   content hash, kind, expiry, per-request MINT CODE) and generates the
   COMPLETE approval question deterministically -- text, header AND the three
   options, marker `[APR-REQ:<id>]` in the text
2. the PreToolUse hook (phase 2) enforces exact string equality of marked
   questions against `build_question`
3. `mint` creates the APR ONLY when the answer equals the kernel-generated
   approval label VERBATIM, including its per-request mint code
   (`Freigeben [7f3a2c]`); never for expired/mismatched requests; the item
   must still be at the requested revision AND content hash (out-of-band
   edits kill the mint)

MINT CODE, and why (empirical finding 2026-07-24, spike S2b): Claude Code
2.1.219 reports answers as `toolUseResult.answers = {question: answer_STRING}`
-- a clicked option and text typed into the always-present "Other" row are
INDISTINGUISHABLE (verified against real session transcripts). The spec's
original demand ("bind the token to the option identity, never the string")
is therefore not implementable on this platform. The mint code restores the
practical guarantee: the label carries per-request entropy that lives ONLY in
the option, so casual free text ("ok", "ja", "freigeben") can never mint.
Residual, documented honestly: a user who deliberately transcribes the code
mints -- but that user IS the approving authority, and the MODEL cannot
produce `answers` at all (the platform writes them, and the PreToolUse hook
pins the question the user saw).
The guarantee is CONDITIONAL on two things the phase-2 wiring must establish
(neither holds by library code alone): (i) `mint` is called ONLY by the
PostToolUse(AskUserQuestion) hook with the platform-provided answer -- it is
a plain function, so any other caller could pass the label itself; and
(ii) `approvals/pending/` is kernel-only territory (the codes sit there in
cleartext, and the question text even names the path) -- the write-scope gate
must cover the whole state dir, not just specialist scopes.

Bundling (user decision 2026-07-24): one analysis/scope APR may cover several
analysis tasks LISTED in its subject manifest.
"""
from __future__ import annotations

import os
import re
import time
import uuid

from .backlog_types import parse_id
from .hashing import subject_manifest_hash
from .state import ProjectState, StateError, _now_iso

APR_KINDS = ("analysis", "scope", "delivery", "acceptance", "routine")
_CHANGE_LABEL = "Ändern"
_REJECT_LABEL = "Ablehnen"


def approve_label(mint_code: str) -> str:
    """The ONE answer string that mints -- entropy-carrying by design."""
    return "Freigeben [%s]" % mint_code

# status side-effect of a successful mint, per (item_type, kind) -- everything
# else only sets approval_ref (spec II.2/II.3)
APPROVAL_TRANSITIONS = {
    ("PR", "scope"): ("DRAFT", "APPROVED"),
    ("RQ", "scope"): ("DRAFT", "APPROVED"),
    ("PR", "delivery"): ("APPROVED", "IN_DELIVERY"),
    ("RQ", "delivery"): ("APPROVED", "IN_DELIVERY"),
    ("PR", "acceptance"): ("DELIVERED", "ACCEPTED"),
    ("RQ", "acceptance"): ("DELIVERED", "ACCEPTED"),
    ("CR", "scope"): ("DRAFT", "APPROVED"),
    ("BUG", "scope"): ("TRIAGED", "APPROVED"),
    ("PROC", "scope"): ("DRAFT", "APPROVED"),
    ("EXP", "delivery"): ("DESIGNED", "APPROVED"),
}

# fields hashed into the subject manifest per kind for ITEM-bound approvals
# (spec II.2 subject_manifest lists)
_SCOPE_FIELDS = ("problem", "goal", "question", "motivation",
                 "acceptance_criteria", "invariants", "out_of_scope",
                 "design_refs")


class ApprovalError(StateError):
    """Approval-protocol violation -- message carries the remedy."""


def _pending_dir(state: ProjectState) -> str:
    return os.path.join(state.root, "approvals", "pending")


def _consumed_dir(state: ProjectState) -> str:
    return os.path.join(state.root, "approvals", "consumed")


def _request_path(state: ProjectState, request_id: str, consumed: bool = False) -> str:
    base = _consumed_dir(state) if consumed else _pending_dir(state)
    return os.path.join(base, request_id + ".yaml")


def item_subject_manifest(item: dict, kind: str) -> dict:
    """Deterministic manifest for an item-bound approval kind."""
    if kind == "scope":
        manifest = {k: item.get(k) for k in _SCOPE_FIELDS if k in item}
        manifest["item"] = item["id"]
        manifest["revision"] = item.get("revision")
        return manifest
    if kind == "acceptance":
        return {
            "item": item["id"],
            "revision": item.get("revision"),
            "delivered_commit": item.get("delivered_commit"),
            "evidence_refs": item.get("evidence_refs", []),
        }
    if kind == "delivery":
        return {
            "item": item["id"],
            "root_revision": item.get("revision"),
            "system_requirements": item.get("system_requirements", []),
            "architecture": item.get("architecture_refs", []),
            "tasks": item.get("planned_tasks", []),
            "risks": item.get("risks", []),
        }
    raise ApprovalError(
        "kind %r is not item-derived (analysis/routine take an explicit "
        "manifest). Remedy: pass `manifest=` to create_pending_request." % kind
    )


def create_pending_request(
    state: ProjectState,
    kind: str,
    item_id: str = None,
    manifest: dict = None,
    ttl_seconds: float = 24 * 3600.0,
) -> dict:
    """Phase 1 of the protocol: persist the immutable pending request."""
    if kind not in APR_KINDS:
        raise ApprovalError(
            "unknown APR kind %r. Remedy: use one of %s." % (kind, "/".join(APR_KINDS))
        )
    with state.lock:
        revision = None
        if item_id is not None:
            item = state.read_item(item_id)
            revision = item.get("revision")
            if manifest is None:
                manifest = item_subject_manifest(item, kind)
        if manifest is None:
            raise ApprovalError(
                "kind %r needs an explicit manifest (analysis: question/scope/"
                "expected result/listed tasks; routine: role/scope/trigger/"
                "cadence/expires). Remedy: pass `manifest=`." % kind
            )
        request = {
            "request_id": uuid.uuid4().hex,
            "kind": kind,
            "item": item_id,
            "revision": revision,
            "subject_manifest": manifest,
            "subject_manifest_hash": subject_manifest_hash(manifest),
            "created": _now_iso(),
            "expires_at_epoch": time.time() + ttl_seconds,
            # entropy that lives ONLY in the approval option label (S2b)
            "mint_code": uuid.uuid4().hex[:6],
        }
        state._write_yaml_atomic(_request_path(state, request["request_id"]), request)
        return request


def build_question(request: dict) -> dict:
    """The COMPLETE approval question, deterministic from the request alone.

    The model must relay this verbatim; the PreToolUse hook enforces string
    equality of question text, header AND all options for marked questions.
    """
    target = request["item"] if request["item"] else request["kind"]
    question = (
        "Freigabe erbeten: %s für %s (Revision %s, subject_manifest sha256 %s…). "
        "Details: approvals/pending/%s.yaml [APR-REQ:%s]"
        % (
            request["kind"],
            target,
            request["revision"] if request["revision"] is not None else "-",
            request["subject_manifest_hash"][:12],
            request["request_id"],
            request["request_id"],
        )
    )
    return {
        "question": question,
        "header": "Freigabe",
        "multiSelect": False,
        "options": [
            {
                "label": approve_label(request["mint_code"]),
                "description": "Erteilt die %s-Freigabe für %s in exakt dieser Revision "
                "(nur diese Option prägt die Freigabe)." % (request["kind"], target),
            },
            {
                "label": _CHANGE_LABEL,
                "description": "Keine Freigabe -- Änderungswünsche folgen im Chat.",
            },
            {
                "label": _REJECT_LABEL,
                "description": "Keine Freigabe -- der Vorgang wird verworfen.",
            },
        ],
    }


def mint(state: ProjectState, request_id: str, answer: str) -> dict:
    """Phase 3: create the APR -- only for the verbatim approval label.

    `answer` is the raw string from `toolUseResult.answers[<question>]`. It
    mints ONLY if it equals `approve_label(request["mint_code"])` exactly.
    The platform gives no structural option identity (spike S2b), so the
    per-request mint code carries the proof instead: any other text --
    "Ändern", "Ablehnen", "ok", a plain "Freigeben" typed into "Other" --
    never mints.
    """
    with state.lock:
        path = _request_path(state, request_id)
        try:
            request = state._read_yaml(path)
        except FileNotFoundError:
            raise ApprovalError(
                "no pending approval request %s (consumed, expired-and-cleaned, "
                "or never created). Remedy: run the kernel approval flow again "
                "-- an invented request ID never mints. (A hand-WRITTEN pending "
                "file with a self-chosen mint_code would mint; keeping "
                "approvals/pending/ kernel-only is the write-scope gate's job, "
                "and the state validator flags hand edits.)" % request_id
            ) from None
        if time.time() > float(request["expires_at_epoch"]):
            raise ApprovalError(
                "approval request %s expired. Remedy: create a fresh request "
                "and ask again -- expired requests never mint." % request_id
            )
        # format check, not mere presence: `mint_code: null` / "" would yield a
        # guessable label like "Freigeben [None]" (Opus check 2026-07-24)
        if not re.fullmatch(r"[0-9a-f]{6}", str(request.get("mint_code") or ""), flags=re.ASCII):
            raise ApprovalError(
                "pending request %s carries no valid mint_code (pre-amendment "
                "or hand-written file) -- refusing to mint (fail-closed). "
                "Remedy: create a fresh approval request." % request_id
            )
        expected = approve_label(request["mint_code"])
        if answer != expected:
            raise ApprovalError(
                "answer %r does not mint: only the exact approval label of "
                "THIS request mints (it carries a per-request code shown in "
                "the option). Casual free text never approves. The pending "
                "request stays until TTL." % (answer,)
            )
        item = None
        if request["item"] is not None:
            item = state.read_item(request["item"])
            if item.get("revision") != request["revision"]:
                raise ApprovalError(
                    "item %s moved to revision %s since the request (requested "
                    "%s) -- out-of-band change, no mint. Remedy: re-run the "
                    "approval flow on the current revision."
                    % (request["item"], item.get("revision"), request["revision"])
                )
            if request["kind"] in ("scope", "acceptance", "delivery"):
                current_hash = subject_manifest_hash(
                    item_subject_manifest(item, request["kind"])
                )
                if current_hash != request["subject_manifest_hash"]:
                    raise ApprovalError(
                        "subject manifest of %s changed since the request -- "
                        "no mint. Remedy: re-run the approval flow."
                        % request["item"]
                    )
        # idempotency guard (Fable-Check 8/#2): a crash between APR write and
        # request consume would leave the request pending -- a replayed mint
        # must not create a SECOND approval for the same request
        approvals_dir = os.path.join(state.root, "approvals")
        if os.path.isdir(approvals_dir):
            for name in sorted(os.listdir(approvals_dir)):
                if not (name.startswith("APR-") and name.endswith(".yaml")):
                    continue
                try:
                    existing = state._read_yaml(os.path.join(approvals_dir, name))
                except Exception:
                    continue
                if isinstance(existing, dict) and existing.get("request_id") == request_id:
                    raise ApprovalError(
                        "request %s already minted %s -- replay blocked. "
                        "Remedy: run `harness validate` to reconcile the "
                        "half-consumed request." % (request_id, existing.get("id"))
                    )
        apr_id = state.allocate_id("APR")
        apr = {
            "id": apr_id,
            "kind": request["kind"],
            "item": request["item"],
            "revision": request["revision"],
            "subject_manifest_hash": request["subject_manifest_hash"],
            "request_id": request_id,
            "mint_code": request["mint_code"],
            "approved_at": _now_iso(),
            # TODO(1.4c/phase 2): routine/analysis requests must populate this
            # (spec II.10a: expired routine approvals block the audit dispatch)
            "expires": request.get("routine_expires"),
            "revoked": False,
        }
        state._write_yaml_atomic(
            os.path.join(state.root, "approvals", apr_id + ".yaml"), apr
        )
        if item is not None:
            item["approval_ref"] = apr_id
            item_type, _ = parse_id(apr["item"])
            transition = APPROVAL_TRANSITIONS.get((item_type, request["kind"]))
            if transition and item.get("status") == transition[0]:
                item["status"] = transition[1]
            state._write_yaml_atomic(state.active_path(item["id"]), item)
        # consume the request (move, never delete -- audit trail)
        state._write_yaml_atomic(_request_path(state, request_id, consumed=True), request)
        os.remove(path)
        state._regenerate_index_locked()
        return apr


def revoke(state: ProjectState, apr_id: str) -> dict:
    with state.lock:
        path = os.path.join(state.root, "approvals", apr_id + ".yaml")
        try:
            apr = state._read_yaml(path)
        except FileNotFoundError:
            raise ApprovalError(
                "no approval %s. Remedy: check generated/index.yaml." % apr_id
            ) from None
        apr["revoked"] = True
        state._write_yaml_atomic(path, apr)
        return apr


def read_apr(state: ProjectState, apr_id: str) -> dict:
    path = os.path.join(state.root, "approvals", apr_id + ".yaml")
    try:
        return state._read_yaml(path)
    except FileNotFoundError:
        raise ApprovalError(
            "no approval %s. Remedy: the item's approval_ref is stale -- run "
            "`harness validate`." % apr_id
        ) from None
