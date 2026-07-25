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
The guarantee is CONDITIONAL on two things NEITHER library code NOR any
in-process check can establish (measured 2026-07-25, see
_assert_minting_caller): (i) only the PostToolUse hook reaches `mint` -- but the
hook is meant to be run with a payload on stdin, so anyone able to execute
`python <hooks>/gate_approval.py < forged.json` mints, and the forged payload is
assembled from the readable pending request; and (ii) `approvals/pending/` is
kernel-only territory (the codes sit there in cleartext, and the question text
even names the path). BOTH need a Bash/PowerShell-level guard, because
`guard_harness_selfmod` gates only Edit|Write|MultiEdit. Until that guard
exists, `approval_provenance` is `unverified` and the enforcement mode is
`audited` -- and `harness doctor` must compute that rather than assert it.

Bundling (user decision 2026-07-24): one analysis/scope APR may cover several
analysis tasks LISTED in its subject manifest.
"""
from __future__ import annotations

import inspect
import os
import re
import sys
import time
import uuid

from .backlog_types import parse_id
from .hashing import subject_manifest_hash
from .state import ProjectState, StateError, _now_iso

APR_KINDS = ("analysis", "scope", "delivery", "acceptance", "routine", "push")
# kinds that are time-boxed rather than content-invalidated (spec II.2 APR field
# list: "expires (routine/analysis)")
# `push` expires like the others, and for the sharpest reason of the three: a
# push token that outlives its session is a standing permission to publish.
EXPIRING_KINDS = frozenset(("routine", "analysis", "push"))
# kinds that may authorise a specialist dispatch through the ROOT item's
# approval_ref. analysis/routine deliberately excluded: they are read-only,
# task-listed permissions (II.2/II.3) and their manifests are not item-derived,
# so no content hash could catch an out-of-band edit of the root.
ROOT_DISPATCH_KINDS = frozenset(("scope", "delivery"))
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


def _revoked_dir(state: ProjectState) -> str:
    return os.path.join(state.root, "approvals", "revoked")


def _request_path(state: ProjectState, request_id: str, consumed: bool = False,
                  revoked: bool = False) -> str:
    if revoked:
        base = _revoked_dir(state)
    else:
        base = _consumed_dir(state) if consumed else _pending_dir(state)
    return os.path.join(base, request_id + ".yaml")


def push_subject_manifest(remote: str, branch: str, head: str) -> dict:
    """R1 (parity row 29, a MINIMUM-KEEP rule): what a push approval is bound to.

    "Push nur nach expliziter Userfreigabe" was prose only, so it died with every
    context window. It is now the same two-phase protocol as an APR, with the
    same mint code -- Amendment 2026-07-24 records why the option IDENTITY cannot
    carry it (spike S2b: a clicked option and typed text are indistinguishable in
    the payload), so the entropy lives in the option LABEL.

    Bound to remote + branch + HEAD, which makes the token single-use without any
    "used" flag to keep honest: approve HEAD abc123, push it, and the next commit
    moves HEAD so the same approval no longer matches. Re-running the identical
    push is a git no-op, so nothing is lost by allowing it. The alternative --
    a consumed marker -- would be one more piece of writable state deciding an
    enforcement question, which is the mistake the ledger gate spent four rounds
    unlearning.
    """
    return {
        "remote": str(remote or ""),
        "branch": str(branch or ""),
        "head": str(head or ""),
    }


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
        "kind %r is not item-derived (analysis/routine/push take an explicit "
        "manifest -- for push, build it with `push_subject_manifest`). Remedy: "
        "pass `manifest=` to create_pending_request." % kind
    )


def create_pending_request(
    state: ProjectState,
    kind: str,
    item_id: str = None,
    manifest: dict = None,
    ttl_seconds: float = 24 * 3600.0,
    approval_expires: float = None,
) -> dict:
    """Phase 1 of the protocol: persist the immutable pending request.

    `ttl_seconds` bounds how long the QUESTION stays answerable; `approval_expires`
    (epoch seconds, routine/analysis only per spec II.10a) bounds how long the
    resulting APPROVAL stays valid. Two different clocks -- conflating them would
    either expire live approvals or leave routine approvals standing forever.
    """
    if kind not in APR_KINDS:
        raise ApprovalError(
            "unknown APR kind %r. Remedy: use one of %s." % (kind, "/".join(APR_KINDS))
        )
    if kind in EXPIRING_KINDS and approval_expires is None:
        # spec II.2: a routine approval "ist gebunden an Rolle, Read-only-Scope,
        # Trigger, Ablaufdatum und jederzeit widerrufbar", and II.10a: an expired
        # routine approval blocks the audit dispatch. With an OPTIONAL expiry the
        # natural call mints an approval that never expires -- a standing spawn
        # permission, i.e. the one thing the revocable time-boxed design exists
        # to prevent. So it is required.
        raise ApprovalError(
            "kind %r must carry an expiry (spec II.2 Ablaufdatum / II.10a: an "
            "expired routine approval blocks the dispatch). Remedy: pass "
            "approval_expires=<epoch seconds>." % kind
        )
    if approval_expires is not None and kind not in EXPIRING_KINDS:
        raise ApprovalError(
            "only %s approvals carry an expiry (spec II.2); kind %r does not. "
            "Remedy: drop approval_expires -- a scope or delivery approval is "
            "invalidated by content change, not by the clock."
            % ("/".join(sorted(EXPIRING_KINDS)), kind)
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
                "cadence/expires; push: remote/branch/head via "
                "`push_subject_manifest`). Remedy: pass `manifest=`." % kind
            )
        if approval_expires is not None:
            # spec II.10a: the routine approval HASHES role, read-only scope,
            # trigger, cadence AND the expiry date -- so the expiry has to sit
            # inside the hashed manifest, not merely beside it. Otherwise the
            # date could be moved without invalidating the approval.
            manifest = dict(manifest, expires=float(approval_expires))
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
    if request["kind"] == "push" and not request["item"]:
        # A push approval has no ITEM, so the generic target would read "push" and the human would
        # be asked to authorise publishing without being told WHAT gets published. The manifest is
        # already in the request and is hash-covered, so naming it here is deterministic (the
        # PreToolUse gate compares this text character for character) and it is the whole point of
        # the rule: "explizite Userfreigabe" means the user knew what they released.
        manifest = request.get("subject_manifest") or {}
        target = "%s -> %s/%s @ %s" % ("push", manifest.get("remote", "?"),
                                       manifest.get("branch", "?"),
                                       str(manifest.get("head", "?"))[:8])
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


APPROVAL_HOOK = "gate_approval.py"


def _is_same_file(left, right) -> bool:
    if not left or not right:
        return False
    try:
        return (os.path.normcase(os.path.realpath(left))
                == os.path.normcase(os.path.realpath(right)))
    except OSError:
        return False


def _assert_minting_caller() -> None:
    """The mint must come from the approval hook, RUN AS the approval hook.

    Three conditions, each closing a measured accidental path (phase-2 review
    2026-07-25):
    1. a `_kernel` bridge module is loaded, and the hook path we accept is
       derived from ITS `__file__`;
    2. the immediate caller's file IS that hook -- realpath+normcase, so a
       crafted `compile(src, "<real hook path>")` filename does not suffice;
    3. `__main__` is that same file, so importing the hook as a module and
       calling its handler, or `runpy.run_path`, does not either.

    WHAT THIS IS WORTH, measured rather than hoped: no ACCIDENTAL path mints. A
    deliberate one does, and cheaply -- every input above is in-process state the
    caller may rewrite. Assigning `sys.modules["__main__"].__file__`, or
    registering a synthetic `_kernel` module whose `__file__` points at a path
    that need not even exist, satisfies all three; so does a two-file directory
    containing any `gate_approval.py` next to an EMPTY `_kernel.py`; and the hook
    is meant to be run with a payload on stdin, so
    `python <hooks>/gate_approval.py < forged.json` mints outright, with the
    forged `answers` + `questions` echo assembled from the readable pending
    request. The cheapest of these never runs the hook, so it does not even leave
    the hook's audit note.

    So user condition (i) ("only the PostToolUse hook may call mint") is NOT
    established by library code, and cannot be: this is in-process state
    checking in-process state. It needs a guard that stops an agent from invoking
    the hooks, or python against the kernel, at all -- a Bash/PowerShell-level
    check, since `guard_harness_selfmod` gates only Edit|Write|MultiEdit. Until
    that exists, `harness doctor` must report `approval_provenance: unverified`
    and the mode stays `audited`.

    Deliberately the LAST check in `mint`: every content refusal (wrong label,
    expired request, out-of-band edit, replay) is reported on its own terms
    first, so a caller-provenance failure never masks the real reason. No APR is
    written before it either way.
    """
    bridge = getattr(sys.modules.get("_kernel"), "__file__", None)
    if not bridge:
        raise ApprovalError(
            "an approval can only be minted from the %s hook, and this process "
            "has no hook bridge loaded at all -- refused. Remedy: approvals "
            "happen through the AskUserQuestion flow; nothing else creates an "
            "APR." % APPROVAL_HOOK
        )
    expected = os.path.join(os.path.dirname(bridge), APPROVAL_HOOK)
    frames = inspect.stack()
    # [0] this function, [1] mint, [2] whoever called mint
    caller = frames[2].filename if len(frames) > 2 else ""
    entry = getattr(sys.modules.get("__main__"), "__file__", None)
    if not _is_same_file(caller, expected) or not _is_same_file(entry, expected):
        raise ApprovalError(
            "only %s may mint an approval, run as itself -- this call came from "
            "%s (entry point %s) and was refused. A mint is a USER decision; any "
            "other caller would be manufacturing one. Remedy: approvals happen "
            "through the AskUserQuestion flow."
            % (expected, caller or "<unknown>", entry or "<none>")
        )


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
        # LAST gate before the approval exists: provenance of the CALLER (see
        # _assert_minting_caller). Everything above refuses on content grounds and
        # says so; this refuses on "who is asking".
        _assert_minting_caller()
        apr_id = state.allocate_id("APR")
        apr = {
            "id": apr_id,
            "kind": request["kind"],
            "item": request["item"],
            "revision": request["revision"],
            # only the HASH, exactly as spec II.2 lists the APR fields. An
            # earlier cut stored the manifest here too, so a bundled analysis
            # approval could answer "do you cover TSK-0007?" -- but the consumed
            # request already carries the manifest and is kept forever ("move,
            # never delete"), so the copy created a second canonical home AND
            # let a HAND-WRITTEN APR answer that question with no minted request
            # behind it. Coverage is read from the consumed request instead
            # (kernel/dispatch.py), which carries the provenance with it.
            "subject_manifest_hash": request["subject_manifest_hash"],
            "request_id": request_id,
            "mint_code": request["mint_code"],
            "approved_at": _now_iso(),
            # DERIVED DISPLAY VALUE, not the authority: spec II.2 lists `expires`
            # among the APR fields and humans/dashboards read it here, but every
            # gate reads `proven_expiry(request)` instead -- the hash-covered copy
            # inside the minted manifest. Duty for the 1.4c validator: assert the
            # two agree, so a human can never read "valid until 2030" from a
            # record the gate correctly refuses.
            "expires": (request.get("subject_manifest") or {}).get("expires"),
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
    """Withdraw an approval — recorded where the APR file is NOT the evidence.

    The flag on the approval stays, because it is what a human reads. But the
    fact that actually blocks is the MOVE of the minted request out of
    `approvals/consumed/`: `consumed_request` then finds no provenance and
    refuses, so flipping `revoked` back to false achieves nothing.
    """
    with state.lock:
        path = os.path.join(state.root, "approvals", apr_id + ".yaml")
        try:
            apr = state._read_yaml(path)
        except FileNotFoundError:
            raise ApprovalError(
                "no approval %s. Remedy: check generated/index.yaml." % apr_id
            ) from None
        # ORDER MATTERS, do not "clean this up": the flag is written FIRST and is
        # checked first in both authorisation routes, so a crash between the two
        # writes can leave the flag without the move -- never the move without the
        # flag, which would be an approval that still authorises.
        apr["revoked"] = True
        state._write_yaml_atomic(path, apr)
        request_id = str(apr.get("request_id") or "")
        if request_id:
            consumed = _request_path(state, request_id, consumed=True)
            if os.path.exists(consumed):
                request = state._read_yaml(consumed)
                request["revoked_at"] = _now_iso()
                state._write_yaml_atomic(
                    _request_path(state, request_id, revoked=True), request)
                os.remove(consumed)
        return apr


def pending_request(state: ProjectState, request_id: str) -> dict:
    """A PENDING approval request, or ApprovalError — the reader the hooks use.

    The PreToolUse(AskUserQuestion) gate resolves `[APR-REQ:<id>]` back to its
    request and rebuilds `build_question(request)` for the string comparison, so
    that lookup needs one public, fail-closed home rather than a hook reaching
    into a private path helper. The TTL check lives here too, for the same reason.
    """
    try:
        request = state._read_yaml(_request_path(state, request_id))
    except FileNotFoundError:
        raise ApprovalError(
            "no pending approval request %s (consumed, expired-and-cleaned, or "
            "never created). Remedy: run the kernel approval flow again -- an "
            "invented request id never mints." % request_id
        ) from None
    except Exception as exc:
        raise ApprovalError(
            "pending request %s is unreadable (%s) -- fail-closed. Remedy: "
            "re-run the approval flow." % (request_id, type(exc).__name__)
        ) from None
    if not isinstance(request, dict):
        raise ApprovalError(
            "pending request %s is not a mapping -- fail-closed." % request_id
        )
    if time.time() > float(request.get("expires_at_epoch") or 0):
        raise ApprovalError(
            "approval request %s expired -- expired requests never mint. "
            "Remedy: create a fresh request and ask again." % request_id
        )
    return request


def consumed_request(state: ProjectState, apr: dict) -> dict:
    """The minted request behind an approval — its PROVENANCE (spec II.12).

    "manuell geschriebene APR ohne Provider-gepraegten Token -> Block": an
    approval file on its own proves nothing, because anything that can write
    YAML can write one. What cannot be forged is a CONSUMED REQUEST: the kernel
    is the only writer of `approvals/consumed/`, it lands there only through
    `mint`, and mint only runs on the verbatim approval label carrying that
    request's mint code. So every authorisation check resolves the approval back
    to its request and compares the two.

    Raises ApprovalError when the request is missing or disagrees with the
    approval — fail-closed, because "cannot prove provenance" must never read as
    "approved".

    REVOCATION lives here too, not in the APR file: `revoke` MOVES the request to
    `approvals/revoked/`, so a revoked approval simply has no consumed request
    and this refuses. Keeping `revoked: true` only inside the APR made revocation
    the least protected fact in the record — flipping one boolean back
    resurrected a withdrawn permission, and II.2 makes revocability load-bearing
    for exactly the kind that carries standing permissions.
    """
    request_id = str(apr.get("request_id") or "")
    if not request_id:
        raise ApprovalError(
            "approval %s names no request_id -- refusing to treat it as a user "
            "approval (spec II.12: a hand-written APR without a provider-minted "
            "token blocks). Remedy: obtain the approval through the kernel "
            "approval flow." % apr.get("id")
        )
    try:
        request = state._read_yaml(_request_path(state, request_id, consumed=True))
    except FileNotFoundError:
        revoked = os.path.exists(_request_path(state, request_id, revoked=True))
        raise ApprovalError(
            "approval %s %s -- it grants nothing (spec II.12/II.10a). Remedy: %s"
            % (apr.get("id"),
               "was REVOKED" if revoked else "has no consumed request %s, so its "
               "provenance cannot be proven" % request_id,
               "obtain a fresh approval." if revoked else
               "obtain the approval through the kernel approval flow; `harness "
               "validate` reports approvals without a request.")
        ) from None
    except Exception as exc:
        raise ApprovalError(
            "consumed request %s for approval %s is unreadable (%s) -- "
            "fail-closed. Remedy: `git restore` the approvals directory."
            % (request_id, apr.get("id"), type(exc).__name__)
        ) from None
    if not isinstance(request, dict):
        raise ApprovalError(
            "consumed request %s is not a mapping -- fail-closed." % request_id
        )
    for field in ("mint_code", "subject_manifest_hash", "kind", "item", "revision"):
        if request.get(field) != apr.get(field):
            raise ApprovalError(
                "approval %s disagrees with its minted request on %s -- the "
                "approval was altered after minting, so it grants nothing "
                "(fail-closed). Remedy: re-run the approval flow."
                % (apr.get("id"), field)
            )
    # the hash is RECOMPUTED from the request's own manifest, not merely compared
    # between two stored copies: both stored hashes survive an edit of the
    # manifest, and the expiry lives inside that manifest (II.10a hashes the
    # Ablaufdatum), so without this an expired approval could be resurrected by
    # editing one field
    if subject_manifest_hash(request.get("subject_manifest")) != request.get(
            "subject_manifest_hash"):
        raise ApprovalError(
            "consumed request %s does not hash to its own recorded hash -- the "
            "minted record was tampered with, so the approval grants nothing "
            "(fail-closed). Remedy: re-run the approval flow." % request_id
        )
    return request


def proven_expiry(request: dict):
    """The approval's expiry, taken from the HASH-COVERED side.

    Read from the request's `subject_manifest`, not from `request.approval_expires`
    and never from the APR file. All three carry the same value, but only the
    manifest is inside the hash that `consumed_request` RECOMPUTES, so only there
    is the value tamper-evident. Reading it anywhere else made expiry a one-line
    edit away from resurrecting a lapsed permission, while II.10a demands the
    opposite ("Abgelaufene ... Routinefreigabe blockiert den Audit-Dispatch
    (fail-closed)").

    Honest limit: an editor that changes the manifest AND recomputes the hash in
    the request AND matches it in the approval file still passes -- the hash
    function is public. What is gone is every SINGLE-field edit. The remaining
    surface is closed by making the state directory kernel-only for tool writes
    (gate layer 3), not by arithmetic.
    """
    expires = (request.get("subject_manifest") or {}).get("expires")
    if expires is None:
        return None
    try:
        return float(expires)
    except (TypeError, ValueError):
        raise ApprovalError(
            "minted request %s carries an unreadable expiry %r -- fail-closed; "
            "an approval whose validity cannot be read grants nothing. Remedy: "
            "re-run the approval flow." % (request.get("request_id"), expires)
        ) from None


def read_apr(state: ProjectState, apr_id: str) -> dict:
    path = os.path.join(state.root, "approvals", apr_id + ".yaml")
    try:
        return state._read_yaml(path)
    except FileNotFoundError:
        raise ApprovalError(
            "no approval %s. Remedy: the item's approval_ref is stale -- run "
            "`harness validate`." % apr_id
        ) from None
