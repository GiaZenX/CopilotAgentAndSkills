"""Dispatch leases + result submission (HARNESS_V2_SPEC.md II.4) -- step 1.4b.

READY -> short-lived lease (nonce + TTL) -> `HARNESS_DISPATCH` header ->
PreToolUse validates the lease (hook, phase 2) -> SubagentStart binds the
child's agent_id to the lease -> spawn outcome moves the task
(success: IN_PROGRESS, failure: straight back to READY) -> an orphaned lease
falls back to READY after TTL. The gate parses ONLY the header, never prose.

submit_result validates the <=4 KB result envelope against its schema and
moves IN_PROGRESS -> SUBMITTED; the envelope is stored beside the task.
"""
from __future__ import annotations

import json
import os
import time
import uuid

from .approvals import (
    ROOT_DISPATCH_KINDS,
    ApprovalError,
    consumed_request,
    item_subject_manifest,
    proven_expiry,
    read_apr,
)
from .backlog_types import UI_TASK_TYPES, parse_id
from .hashing import subject_manifest_hash
from .schemas import validate
from .state import ProjectState, StateError, _now_iso

HEADER_PREFIX = "HARNESS_DISPATCH "
DEFAULT_LEASE_TTL = 15 * 60.0
# how long a validated dispatch waits for its SubagentStart to claim it (see
# mark_awaiting_bind); generous enough for a slow spawn, short enough that a
# failed spawn does not leave a claimable slot lying around
BIND_WINDOW = 120.0
# where an `APR.kind: analysis` lists the tasks it covers (spec II.2 Buendelung:
# "EINE analysis- oder scope-APR darf MEHRERE im subject_manifest GELISTETE
# Analyse-Tasks decken"). Named here because the manifest is otherwise free-form
# for analysis, and a gate cannot check a key nobody agreed on.
ANALYSIS_TASKS_KEY = "tasks"


class DispatchError(StateError):
    """Dispatch-gate violation -- fail-closed, message carries the remedy."""


class NoPendingDispatch(DispatchError):
    """A subagent started without a dispatch awaiting it (spec II.4 gate 1/2)."""


class AmbiguousBinding(DispatchError):
    """Several same-role dispatches await binding; guessing is not allowed."""


def _lease_path(state: ProjectState, task_id: str) -> str:
    return os.path.join(state.root, "tasks", "leases", task_id + ".lease.yaml")


def _envelope_path(state: ProjectState, task_id: str) -> str:
    return os.path.join(state.root, "tasks", "results", task_id + ".envelope.yaml")


def create_task(state: ProjectState, fields: dict) -> dict:
    """Create a TSK: the kernel denormalizes root_revision from the CURRENT
    root item -- callers never guess it (spec II.2)."""
    if "root_revision" in fields:
        raise DispatchError(
            "root_revision is kernel-set from the root item. Remedy: drop it."
        )
    root_id = fields.get("product_requirement")
    if not root_id:
        raise DispatchError(
            "TSK needs product_requirement (the PR/RQ root id). Remedy: set it."
        )
    with state.lock:
        root = state.read_item(root_id)
        task_fields = dict(fields)
        task_fields["root_revision"] = root.get("revision")
    # TOCTOU note: capture below takes a SECOND lock hold -- a root-revision
    # change in between is caught fail-closed by create_lease's revision check
    return state.capture("TSK", task_fields)


def create_lease(state: ProjectState, task_id: str, ttl: float = DEFAULT_LEASE_TTL) -> dict:
    """READY -> LEASED with a nonce lease. Validates root approval + revision."""
    with state.lock:
        task = state.read_item(task_id)
        if task.get("status") != "READY":
            raise DispatchError(
                "%s is %s, not READY -- no lease (spec II.4). Remedy: bring the "
                "task to READY via its lifecycle first."
                % (task_id, task.get("status"))
            )
        root = state.read_item(task["product_requirement"])
        _assert_dispatch_authorised_locked(state, task, root)
        if root.get("revision") != task.get("root_revision"):
            raise DispatchError(
                "task %s was planned against root revision %s but %s is now at "
                "revision %s -- tasks of an invalidated root revision are not "
                "leasable (spec II.2). Remedy: re-approve and re-plan the task."
                % (task_id, task.get("root_revision"), root["id"], root.get("revision"))
            )
        blocked = task.get("blocked_by")
        if blocked:
            raise DispatchError(
                "%s is blocked by %s. Remedy: resolve the blocker first."
                % (task_id, blocked)
            )
        _assert_dependencies_met_locked(state, task)
        lease_path = _lease_path(state, task_id)
        if os.path.exists(lease_path):
            raise DispatchError(
                "a lease for %s already exists -- parallel second claim "
                "blocked (spec II.4). Remedy: wait for the lease to resolve "
                "or time out." % task_id
            )
        lease = {
            "task_id": task_id,
            "nonce": uuid.uuid4().hex,
            "root_revision": task["root_revision"],
            "created": _now_iso(),
            "created_epoch": time.time(),
            "ttl": float(ttl),
            "agent_id": None,
        }
        state._write_yaml_atomic(lease_path, lease)
        task["status"] = "LEASED"
        task["leased_at"] = _now_iso()
        state._write_yaml_atomic(state.active_path(task_id), task)
        state._regenerate_index_locked()
        return lease


def dispatch_header(lease: dict) -> str:
    """The ONLY thing the gate parses -- never free prompt prose (spec II.4)."""
    return HEADER_PREFIX + json.dumps(
        {
            "task_id": lease["task_id"],
            "root_revision": lease["root_revision"],
            "lease": lease["nonce"],
        },
        sort_keys=True,
    )


def parse_header(prompt: str) -> dict:
    """Extract the HARNESS_DISPATCH header from a spawn prompt, fail-closed."""
    for line in (prompt or "").splitlines():
        line = line.strip()
        if line.startswith(HEADER_PREFIX):
            try:
                data = json.loads(line[len(HEADER_PREFIX):])
                return {
                    "task_id": data["task_id"],
                    "root_revision": data["root_revision"],
                    "lease": data["lease"],
                }
            except (ValueError, KeyError, TypeError):
                raise DispatchError(
                    "malformed HARNESS_DISPATCH header. Remedy: emit the header "
                    "exactly as returned by dispatch_header()."
                ) from None
    raise DispatchError(
        "no HARNESS_DISPATCH header in the spawn prompt -- dispatch blocked "
        "(the gate parses ONLY the header, spec II.4). Remedy: create a lease "
        "and prepend dispatch_header()."
    )


def validate_lease(state: ProjectState, header: dict) -> dict:
    """PreToolUse-side check: lease exists, nonce matches, not expired."""
    with state.lock:
        return _validate_lease_locked(state, header)


def _validate_lease_locked(state: ProjectState, header: dict) -> dict:
    """validate_lease body for callers already holding the lock (not reentrant)."""
    lease = _read_lease(state, header["task_id"])
    if lease["nonce"] != header["lease"]:
        raise DispatchError(
            "lease nonce mismatch for %s -- stale or foreign header. "
            "Remedy: create a fresh lease." % header["task_id"]
        )
    if _expired(lease):
        _release_lease_locked(state, header["task_id"], to_ready=True)
        raise DispatchError(
            "lease for %s expired (ttl %ss) -- task returned to READY. "
            "Remedy: create a fresh lease." % (header["task_id"], lease["ttl"])
        )
    if header["root_revision"] != lease["root_revision"]:
        raise DispatchError(
            "header root_revision %s != lease root_revision %s. Remedy: "
            "emit the header exactly as returned by dispatch_header()."
            % (header["root_revision"], lease["root_revision"])
        )
    return lease


def validate_dispatch(state: ProjectState, header: dict, subagent_type: str,
                      claim: bool = False) -> dict:
    """The full gate-layer-2 check (spec II.4), re-run at SPAWN time.

    `create_lease` checked the same ground when the lease was made, but that was
    a separate moment: an out-of-band edit, a revoked approval or a newly
    failed dependency between lease and spawn must not get through. Everything
    happens under ONE lock hold so the answer cannot change while it is
    computed.

    Checks, in the order spec II.4 lists them: task exists and holds a valid
    READY-lease, role match, root revision, valid APR hash, dependencies met,
    required design_ref/AC references present.

    `claim=True` additionally CONSUMES the lease for one dispatch (spec II.4
    "Ein paralleler zweiter Claim wird blockiert", II.12 "zweiter Claim derselben
    Lease -> Block"). Without it a validated header is a reusable bearer token:
    the nonce travels inside the specialist's own prompt, so the same header
    could spawn N children -- and only the first would ever get bound. Callers
    that merely VERIFY an already-dispatched spawn (the PostToolUse path) pass
    claim=False.
    """
    with state.lock:
        task_id = header["task_id"]
        lease = _validate_lease_locked(state, header)
        if claim and lease.get("dispatched_at"):
            raise DispatchError(
                "the lease for %s was already dispatched at %s -- a second claim "
                "on one lease is blocked (spec II.4). Remedy: create a fresh "
                "lease for a second attempt; the specialist carries the nonce in "
                "its prompt, so re-using it would spawn under a spent claim."
                % (task_id, lease["dispatched_at"])
            )
        task = state.read_item(task_id)
        if task.get("status") != "LEASED":
            raise DispatchError(
                "%s is %s but holds a lease -- inconsistent state, dispatch "
                "blocked (fail-closed). Remedy: `harness doctor` shows the "
                "lease; `harness sweep-leases` returns the task to READY."
                % (task_id, task.get("status"))
            )
        expected_role = task.get("assigned_role")
        if not subagent_type or str(subagent_type) != str(expected_role):
            raise DispatchError(
                "role mismatch: %s is assigned to %r but the spawn asks for "
                "%r -- dispatch blocked (spec II.4). Remedy: spawn the "
                "assigned role, or re-plan the task."
                % (task_id, expected_role, subagent_type or "<none>")
            )
        root = state.read_item(task["product_requirement"])
        if root.get("revision") != task.get("root_revision"):
            raise DispatchError(
                "task %s was planned against root revision %s but %s is now at "
                "revision %s -- tasks of an invalidated root revision are not "
                "dispatchable (spec II.2). Remedy: re-approve and re-plan."
                % (task_id, task.get("root_revision"), root["id"], root.get("revision"))
            )
        _assert_dispatch_authorised_locked(state, task, root)
        _assert_dependencies_met_locked(state, task)
        if task.get("blocked_by"):
            raise DispatchError(
                "%s is blocked by %s. Remedy: resolve the blocker first."
                % (task_id, task["blocked_by"])
            )
        # A gate input is only as good as its VALIDATION. Both checks below ask
        # whether the reference RESOLVES, not merely whether it is non-empty:
        # three defects in a row on the design rule (synonym type -> legal
        # re-type -> dangling reference) were all the same mistake one level
        # further out, and "design_ref: TBD" satisfies a truthiness test while
        # pointing at nothing.
        #
        # The two are strict in DIFFERENT scopes, on purpose -- do not "make them
        # consistent". `design_refs` lives on the ROOT and is what the scope
        # approval hashes, so membership there is exactly right. Acceptance
        # criteria legitimately live ONE HOP AWAY: spec II.2 gives BUG its
        # Fix-Kriterien, CR its own acceptance_criteria and EXP its
        # success_criteria, and `derives_from` names which of them a task serves.
        # Resolving AC against the root alone made every bugfix, CR and EXP task
        # undispatchable while passing only the WRONG reference.
        refs = [str(ref) for ref in (task.get("acceptance_refs") or [])]
        known_ac = _known_acceptance_ids_locked(state, root, task)
        unknown = [ref for ref in refs if ref not in known_ac]
        if not refs or unknown:
            raise DispatchError(
                "%s %s -- a task nobody can check against the approved criteria "
                "is not dispatchable (spec II.4). Remedy: reference criteria that "
                "exist on %s or on its derives_from item (known: %s)."
                % (task_id,
                   "carries no acceptance_refs" if not refs
                   else "references criteria that exist nowhere: %s" % ", ".join(unknown),
                   root["id"], ", ".join(sorted(known_ac)) or "none defined")
            )
        if str(task.get("type", "")).lower() in UI_TASK_TYPES:
            confirmed = [str(ref) for ref in (root.get("design_refs") or [])]
            if confirmed and str(task.get("design_ref") or "") not in confirmed:
                raise DispatchError(
                    "%s is a UI task under %s, which has a confirmed design, but "
                    "its design_ref is %r -- dispatch blocked (spec II.6: the "
                    "active reference must be unambiguous, and II.6a makes "
                    "design_ref the binding implementation reference). Remedy: "
                    "set design_ref to one of the frozen revisions: %s."
                    % (task_id, root["id"], task.get("design_ref"), ", ".join(confirmed))
                )
        if claim:
            lease["dispatched_at"] = _now_iso()
            state._write_yaml_atomic(_lease_path(state, task_id), lease)
        return {"lease": lease, "task": task, "root": root}


def verify_dispatch_identity(state: ProjectState, header: dict, subagent_type: str,
                             require_role: bool = True) -> dict:
    """Is this header really THIS lease's? -- identity only, no authorisation.

    For the post-spawn events. They cannot block, so the only thing they protect
    is their own bookkeeping, and the question they need answered is "does this
    header belong to the lease it names" -- nonce, root revision, assigned role.

    Deliberately NOT `validate_dispatch`: asking "is dispatch still authorised?"
    on an event that cannot prevent anything only breaks the bookkeeping. An
    approval revoked while the child ran would freeze the task LEASED -- no
    rollback on failure, a ghost bind window poisoning the next same-role
    dispatch, and on success a task that never reaches IN_PROGRESS, so
    `submit_result` later refuses the specialist's finished work. Recording an
    outcome takes permission away or leaves it unchanged; it never grants any.

    `require_role` is the asymmetry, and it is deliberate rather than an
    oversight (an earlier cut treated a MISSING role as "no opinion" everywhere,
    which failed open on the one path that GRANTS something):
      * True for the success path, which BINDS an agent_id to a task and thereby
        hands gate layer 3 a write permission. A payload variant without
        `subagent_type` must not collect that binding unchecked.
      * False for the failure paths, which only return the task to READY. That
        takes permission away, so refusing it over a missing field would strand
        the task until the TTL sweep for no safety gain.
    """
    with state.lock:
        lease = _validate_lease_locked(state, header)
        task = state.read_item(header["task_id"])
        expected_role = task.get("assigned_role")
        role_missing = not subagent_type
        if (role_missing and require_role) or (
                not role_missing and str(subagent_type) != str(expected_role)):
            raise DispatchError(
                "role %s: %s is assigned to %r but the spawn declared %r -- "
                "refusing to record an outcome for it."
                % ("missing" if role_missing else "mismatch",
                   header["task_id"], expected_role, subagent_type or "<none>")
            )
        return {"lease": lease, "task": task}


def mark_awaiting_bind(state: ProjectState, task_id: str, prompt_id: str = None) -> dict:
    """Record that a validated dispatch is waiting for its SubagentStart.

    Why this exists: the SubagentStart payload carries `agent_id` and
    `agent_type` but NO key back to the tool call (no tool_use_id, no prompt --
    verified against the S3 spike payloads and the hooks reference). So the lease
    has to be claimable by role for a short window. See `bind_agent_by_role` for
    what happens when the window holds more than one candidate.

    `prompt_id` narrows it as far as the platform allows: both PreToolUse and
    SubagentStart carry the id of the user prompt being processed, so a stale
    window left by an earlier turn can neither collide with, nor be stolen by, a
    child from a later one. It cannot separate two same-role dispatches inside
    ONE turn -- that is the residual ambiguity, and it is refused, not guessed.
    """
    with state.lock:
        lease = _read_lease(state, task_id)
        lease["awaiting_bind_until"] = time.time() + BIND_WINDOW
        lease["awaiting_bind_prompt"] = prompt_id
        state._write_yaml_atomic(_lease_path(state, task_id), lease)
        return lease


def clear_awaiting_bind(state: ProjectState, task_id: str) -> None:
    """Close the bind window (the spawn failed or was denied, so no child comes).

    Without this a denied spawn leaves a claimable slot for BIND_WINDOW seconds,
    and the next strictly SEQUENTIAL same-role dispatch collides with the ghost
    -- reported as "dispatch same-role tasks sequentially" to a user who already
    was.
    """
    with state.lock:
        try:
            lease = _read_lease(state, task_id)
        except DispatchError:
            return
        lease.pop("awaiting_bind_until", None)
        lease.pop("awaiting_bind_prompt", None)
        state._write_yaml_atomic(_lease_path(state, task_id), lease)


def bind_agent_by_role(state: ProjectState, agent_id: str, agent_type: str,
                       prompt_id: str = None) -> dict:
    """SubagentStart: claim the one lease awaiting a child of this role.

    Returns the bound lease, or raises AmbiguousBinding when the window holds
    several candidates for the same role. That case is refused rather than
    guessed: binding the wrong agent_id would attribute one specialist's writes
    to another specialist's allowed_scope, which is worse than a visible
    refusal -- it would be a silent hole in gate layer 3 (spec II.4).
    """
    if not agent_id:
        # consuming the window for a payload with no agent_id would leave the
        # REAL child permanently unbound, i.e. unable to write anything
        raise NoPendingDispatch(
            "SubagentStart carried no agent_id -- nothing to bind, leaving the "
            "window open for the real child."
        )
    with state.lock:
        now = time.time()
        candidates = []
        for lease in _iter_leases(state):
            if lease.get("agent_id") or _window_open_until(lease) < now:
                continue
            if _expired(lease):
                continue  # the bind window can outlive the lease itself
            if prompt_id and lease.get("awaiting_bind_prompt") not in (None, prompt_id):
                continue
            try:
                task = state.read_item(lease["task_id"])
            except StateError:
                continue
            if str(task.get("assigned_role")) == str(agent_type):
                candidates.append(lease)
        if not candidates:
            raise NoPendingDispatch(
                "no dispatch awaiting a %r child -- this subagent was not "
                "started through the dispatch gate." % agent_type
            )
        if len(candidates) > 1:
            raise AmbiguousBinding(
                "%d concurrent dispatches await a %r child (%s) and the platform "
                "gives SubagentStart no key to tell them apart -- refusing to "
                "guess, because a wrong binding would silently run one "
                "specialist under another's allowed_scope. Remedy: dispatch "
                "tasks of the SAME role sequentially; different roles in "
                "parallel are unaffected."
                % (len(candidates), agent_type,
                   ", ".join(sorted(c["task_id"] for c in candidates)))
            )
        lease = candidates[0]
        lease["agent_id"] = agent_id
        lease.pop("awaiting_bind_until", None)
        lease.pop("awaiting_bind_prompt", None)
        state._write_yaml_atomic(_lease_path(state, lease["task_id"]), lease)
        return lease


def bind_agent(state: ProjectState, task_id: str, agent_id: str) -> dict:
    """Bind a known task to a known agent_id -- the UNAMBIGUOUS binding point.

    Used from PostToolUse(Agent), where `tool_input.prompt` (and therefore the
    dispatch header) and `tool_response.agentId` arrive together, so no
    role-matching guess is involved. It fires at child COMPLETION, which is too
    late to gate the child's own writes -- hence the role-claim above for the
    live window, and this as the authoritative record afterwards (spike S3
    names both binding points).
    """
    with state.lock:
        lease = _read_lease(state, task_id)
        lease["agent_id"] = agent_id
        lease.pop("awaiting_bind_until", None)
        state._write_yaml_atomic(_lease_path(state, task_id), lease)
        return lease


def task_for_agent(state: ProjectState, agent_id: str):
    """The task an agent_id is bound to, or None -- gate layer 3 asks this."""
    if not agent_id:
        return None
    for lease in _iter_leases(state):
        if lease.get("agent_id") == agent_id:
            try:
                return state.read_item(lease["task_id"])
            except StateError:
                return None
    return None


def spawn_outcome(state: ProjectState, task_id: str, ok: bool) -> dict:
    """PostToolUse on the spawn: success -> IN_PROGRESS, failure -> READY."""
    with state.lock:
        task = state.read_item(task_id)
        if ok:
            if task.get("status") == "LEASED":
                task["status"] = "IN_PROGRESS"
                task["started"] = _now_iso()
                state._write_yaml_atomic(state.active_path(task_id), task)
        else:
            _release_lease_locked(state, task_id, to_ready=True)
            task = state.read_item(task_id)
        state._regenerate_index_locked()
        return task


def sweep_expired_leases(state: ProjectState) -> list:
    """Orphaned leases fall back to READY after TTL (no task hangs, spec II.4)."""
    released = []
    with state.lock:
        lease_dir = os.path.join(state.root, "tasks", "leases")
        if not os.path.isdir(lease_dir):
            return released
        for name in sorted(os.listdir(lease_dir)):
            if not name.endswith(".lease.yaml"):
                continue
            task_id = name[: -len(".lease.yaml")]
            try:
                lease = _read_lease(state, task_id)
            except DispatchError:
                continue
            if _expired(lease):
                _release_lease_locked(state, task_id, to_ready=True)
                released.append(task_id)
        if released:
            state._regenerate_index_locked()
    return released


def submit_result(state: ProjectState, envelope: dict) -> dict:
    """Validate the <=4 KB envelope, store it, move IN_PROGRESS -> SUBMITTED."""
    validate(envelope, "result_envelope")
    task_id = envelope["task_id"]
    with state.lock:
        task = state.read_item(task_id)
        if task.get("status") != "IN_PROGRESS":
            raise DispatchError(
                "%s is %s -- submit-result needs IN_PROGRESS. Remedy: check "
                "the task lifecycle." % (task_id, task.get("status"))
            )
        state._write_yaml_atomic(_envelope_path(state, task_id), envelope)
        task["status"] = "SUBMITTED" if envelope["status_proposal"] == "SUBMITTED" else "FAILED"
        task["completed"] = _now_iso()
        state._write_yaml_atomic(state.active_path(task_id), task)
        _remove_lease(state, task_id)
        state._regenerate_index_locked()
        return task


# -- internals -----------------------------------------------------------------

def _iter_leases(state: ProjectState):
    """Every readable lease; the caller holds the lock. Corrupt files are skipped
    here on purpose -- callers that must FAIL on one read it by task id."""
    lease_dir = os.path.join(state.root, "tasks", "leases")
    if not os.path.isdir(lease_dir):
        return
    for name in sorted(os.listdir(lease_dir)):
        if not name.endswith(".lease.yaml"):
            continue
        try:
            lease = state._read_yaml(os.path.join(lease_dir, name))
        except Exception:
            continue
        if isinstance(lease, dict) and lease.get("task_id"):
            yield lease


def _criteria_ids(item: dict) -> set:
    """The criterion ids an item offers: `acceptance_criteria` (PR/RQ/CR/BUG) or
    `success_criteria` (EXP, spec II.2). Entries may be `{id, text}` mappings or
    plain strings -- both shapes appear in real items, and a strict resolution
    check that only understood one of them would block the other."""
    ids = set()
    for field in ("acceptance_criteria", "success_criteria"):
        for entry in item.get(field) or []:
            if isinstance(entry, dict) and entry.get("id"):
                ids.add(str(entry["id"]))
            elif isinstance(entry, str) and entry.strip():
                ids.add(entry)
    return ids


def _known_acceptance_ids_locked(state: ProjectState, root: dict, task: dict) -> set:
    """Criterion ids a task may reference: the root's, plus its derives_from item's.

    `derives_from` is a required TSK field and is what names the contract the task
    actually serves -- a bugfix task referencing the PR's AC instead of the BUG's
    Fix-Kriterien would be referencing the wrong contract entirely.
    """
    known = _criteria_ids(root)
    origins = task.get("derives_from")
    origins = origins if isinstance(origins, (list, tuple)) else [origins]
    for origin in origins:
        if not origin or str(origin) == root["id"]:
            continue
        try:
            parse_id(str(origin))
        except ValueError:
            continue  # free-text provenance note, not an item reference
        item, _archived = _read_item_any(state, str(origin))
        if item:
            known |= _criteria_ids(item)
    return known


def _assert_dependencies_met_locked(state: ProjectState, task: dict) -> None:
    """spec II.4 gate 2 / II.12 "offene Abhaengigkeit -> Block". A dependency is
    satisfied once its work was accepted (DONE) or QA'd (VALIDATED)."""
    open_deps = []
    for dep_id in task.get("dependencies") or []:
        dep, _archived = _read_item_any(state, dep_id)
        if dep is None:
            open_deps.append("%s (missing)" % dep_id)
        elif dep.get("status") not in ("DONE", "VALIDATED"):
            open_deps.append("%s (%s)" % (dep_id, dep.get("status")))
    if open_deps:
        raise DispatchError(
            "%s has open dependencies: %s -- dispatch blocked (spec II.4). "
            "Remedy: finish the dependencies first."
            % (task["id"], ", ".join(open_deps))
        )


def _assert_dispatch_authorised_locked(state: ProjectState, task: dict, root: dict) -> None:
    """No subagent without a user approval (spec II.2 Risikoklassen) -- via one
    of the TWO legitimate routes, never neither.

    1. DELIVERY route: the root item carries a current scope or delivery
       approval, and the task rides on it. ONLY those two kinds (see
       ROOT_DISPATCH_KINDS): an analysis or routine approval minted against the
       root would otherwise authorise unlimited IMPLEMENTATION work under a
       still-DRAFT root -- and because their manifests are not item-derived, no
       content hash could catch an out-of-band edit either, silently switching
       off gate layer 4 for that root.
    2. ANALYSIS route: an `APR.kind: analysis` LISTS this task. Spec II.2
       (Buendelung, user decision 2026-07-24) lets one analysis approval cover
       several listed tasks, and such an approval is usually not item-bound at
       all -- so the root may legitimately have no approval_ref while the task
       is still fully approved.
    """
    apr_ref = root.get("approval_ref")
    if apr_ref:
        apr = read_apr(state, apr_ref)
        if apr.get("kind") in ROOT_DISPATCH_KINDS:
            _assert_root_approval_locked(state, root)
            return
        # an approval of a non-dispatching kind is NOT an error on the item -- it
        # simply does not authorise a spawn, so fall through to the task route
    covering = _covering_analysis_apr(state, task["id"])
    if covering is None:
        raise DispatchError(
            "neither %s nor an analysis approval authorises dispatching %s -- "
            "blocked (spec II.2: no subagent without a user approval, and a "
            "draft analysis needs its own APR.kind: analysis). Remedy: obtain "
            "the scope approval for %s, or an analysis approval that LISTS %s "
            "in its subject manifest."
            % (root["id"], task["id"], root["id"], task["id"])
        )


def _assert_not_expired(apr_ref: str, request: dict) -> None:
    """spec II.10a: an expired routine approval blocks the dispatch.

    The expiry comes from the minted REQUEST, never from the approval file --
    see approvals.proven_expiry for why that distinction is the whole point.
    """
    expires = proven_expiry(request)
    if expires is not None and expires < time.time():
        raise DispatchError(
            "approval %s expired -- dispatch blocked (spec II.10a: an expired "
            "routine approval blocks the dispatch). Remedy: renew the approval."
            % apr_ref
        )


def _covering_analysis_apr(state: ProjectState, task_id: str):
    """A valid, PROVEN analysis approval listing this task, or None.

    The task list is read from the approval's CONSUMED REQUEST, never from the
    approval file: the request is the part only `mint` can produce, so reading
    coverage there means a hand-written APR-0001.yaml listing whatever tasks it
    likes authorises nothing (spec II.12).
    """
    approvals_dir = os.path.join(state.root, "approvals")
    if not os.path.isdir(approvals_dir):
        return None
    for name in sorted(os.listdir(approvals_dir)):
        if not (name.startswith("APR-") and name.endswith(".yaml")):
            continue
        try:
            apr = state._read_yaml(os.path.join(approvals_dir, name))
        except Exception:
            continue
        if not isinstance(apr, dict) or apr.get("kind") != "analysis" or apr.get("revoked"):
            continue
        try:
            request = consumed_request(state, apr)
            expires = proven_expiry(request)
        except (DispatchError, ApprovalError):
            continue  # unprovable, revoked or unreadable covers nothing (fail-closed)
        if expires is not None and expires < time.time():
            continue
        listed = (request.get("subject_manifest") or {}).get(ANALYSIS_TASKS_KEY) or []
        if task_id in [str(entry) for entry in listed]:
            return apr
    return None


def _assert_root_approval_locked(state: ProjectState, root: dict) -> None:
    """Root carries a current, unrevoked approval whose hash still matches.

    The hash re-computation is what catches an OUT-OF-BAND edit: someone who
    edits an approved item in an IDE, around the kernel, keeps `approval_ref`
    pointing at an approval that no longer describes the item (spec II.4 gate 4
    "out-of-band edit invalidated approval").
    """
    apr_ref = root.get("approval_ref")
    if not apr_ref:
        raise DispatchError(
            "root %s has no current approval -- dispatch blocked (fail-closed). "
            "Remedy: obtain the scope/delivery approval." % root["id"]
        )
    apr = read_apr(state, apr_ref)
    if apr.get("revoked"):
        raise DispatchError(
            "approval %s is revoked -- dispatch blocked. Remedy: obtain a fresh "
            "approval." % apr_ref
        )
    # provenance first: an approval that cannot show its minted request is not a
    # user approval at all, whatever else it says (spec II.12). ApprovalError is
    # NOT a DispatchError, and the hook classifies anything else as an internal
    # error -- so a provable-policy refusal would have reached the user as "the
    # harness is broken, run harness doctor" instead of "this approval is not
    # proven". Re-raised in the dispatch vocabulary here.
    try:
        request = consumed_request(state, apr)
    except ApprovalError as exc:
        raise DispatchError(str(exc)) from None
    if str(apr.get("item") or "") != root["id"]:
        raise DispatchError(
            "approval %s belongs to %r, not to %s -- dispatch blocked. Remedy: "
            "obtain an approval for this root item."
            % (apr_ref, apr.get("item"), root["id"])
        )
    _assert_not_expired(apr_ref, request)
    kind = apr.get("kind")
    if kind in ("scope", "acceptance", "delivery"):
        current = subject_manifest_hash(item_subject_manifest(root, kind))
        if current != apr.get("subject_manifest_hash"):
            raise DispatchError(
                "content hash of %s no longer matches approval %s -- an "
                "out-of-band edit invalidated the approval; dispatch blocked "
                "(spec II.4). Remedy: re-approve the current revision, or "
                "`git restore %s` to return to the approved content."
                % (root["id"], apr_ref,
                   os.path.relpath(state.active_path(root["id"]), state.root))
            )


def _read_item_any(state: ProjectState, item_id: str):
    """Return (item, archived) looking in active first, then the archive; the
    caller holds the lock. (None, False) when the id exists nowhere."""
    try:
        return state.read_item(item_id), False
    except StateError:
        pass
    item_type, _ = parse_id(item_id)
    base = os.path.join(state.root, "archive", item_type)
    if os.path.isdir(base):
        for year in sorted(os.listdir(base)):
            candidate = os.path.join(base, year, item_id + ".yaml")
            if os.path.exists(candidate):
                return state._read_yaml(candidate), True
    return None, False


def _read_lease(state: ProjectState, task_id: str) -> dict:
    try:
        return state._read_yaml(_lease_path(state, task_id))
    except FileNotFoundError:
        raise DispatchError(
            "no lease for %s -- dispatch blocked (spec II.4). Remedy: create "
            "a lease from READY first." % task_id
        ) from None
    except Exception as exc:
        raise DispatchError(
            "corrupt lease file for %s (%s) -- dispatch blocked (fail-closed). "
            "Remedy: `harness doctor` inspects leases; removing the corrupt "
            "lease returns the task to READY on the next sweep."
            % (task_id, exc.__class__.__name__)
        ) from None


def _expired(lease: dict) -> bool:
    return time.time() > float(lease["created_epoch"]) + float(lease["ttl"])


def _window_open_until(lease: dict) -> float:
    """The bind window's end, or 0 when there is none / it is unreadable.

    Defensive on purpose: `_iter_leases` skips leases that do not PARSE, so a
    parseable lease with a junk value here is the remaining gap -- and a claim
    path that raises ValueError on it turns a diagnosable state into an
    internal-error block with a traceback instead of a remedy.
    """
    try:
        return float(lease.get("awaiting_bind_until") or 0)
    except (TypeError, ValueError):
        return 0.0


def _remove_lease(state: ProjectState, task_id: str) -> None:
    try:
        os.remove(_lease_path(state, task_id))
    except FileNotFoundError:
        pass


def _release_lease_locked(state: ProjectState, task_id: str, to_ready: bool) -> None:
    _remove_lease(state, task_id)
    task = state.read_item(task_id)
    if to_ready and task.get("status") == "LEASED":
        task["status"] = "READY"
        state._write_yaml_atomic(state.active_path(task_id), task)
