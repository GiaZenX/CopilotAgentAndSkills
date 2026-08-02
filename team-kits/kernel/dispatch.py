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
    ROUTINE_ROLE_FIELD,
    ApprovalError,
    assert_apr_in_force,
    consumed_request,
    proven_expiry,
    read_apr,
)
from .backlog_types import UI_TASK_TYPES, parse_id
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
        _assert_origins_belong_to_root_locked(state, root, fields)
        task_fields = dict(fields)
        task_fields["root_revision"] = root.get("revision")
    # TOCTOU note: capture below takes a SECOND lock hold -- a root-revision
    # change in between is caught fail-closed by create_lease's revision check
    return state.capture("TSK", task_fields)


def _assert_origins_belong_to_root_locked(state: ProjectState, root: dict, fields: dict) -> None:
    """A TSK's `derives_from` must hang from the SAME root -- refused at CREATION.

    THE DEAD END THIS ENDS, measured 2026-08-02 in a scaffolded project: `create-task
    --product-requirement PR-0001 --derives-from BUG-0001` where BUG-0001 hangs from PR-0002 was
    accepted with rc 0; `validate` then reported it as an ERROR, `gate_memory_complete` blocked
    the merge on that error, and neither remedy named a way out. `transition TSK-0001 CANCELLED`
    does NOT clear the finding (a cancelled item is still an active item -- measured: the error
    survives and gains an "awaiting archive" warning); only `archive` removes it. And the
    alternative both remedies offer -- "fix product_requirement or derives_from" -- is not
    executable at all: an item's fields are frozen outside DRAFT and no command rewrites them.
    An item that cannot be created wrong needs no remedy for having been.

    ONE definition of "which item does this one hang from", and it is the VALIDATOR'S:
    `report._root_of` over `backlog_types.PARENT_FIELDS`. Imported here rather than re-walked --
    a second implementation of that walk is precisely the drift `_parents_of` was rebuilt to end,
    and the two answers have to agree or this refuses what `validate` accepts.

    SEVERITY IS KEPT IN STEP with the validator on purpose: `_check_task_origins` calls the
    cross-root case an ERROR and the archived/terminal origin a WARNING, so only the first is
    refused. Refusing a warning here would make a task the validator tolerates uncreatable.
    """
    # deferred: `report` imports `state` and `approvals`, never `dispatch`, so this is a leaf
    # import rather than a cycle -- and by the time a task is created, both halves are loaded
    from .report import _root_of

    origins = fields.get("derives_from")
    origins = origins if isinstance(origins, (list, tuple)) else [origins]
    for origin in origins:
        origin = str(origin or "")
        if not origin or origin == root["id"]:
            continue
        try:
            origin_type, _number = parse_id(origin)
        except ValueError:
            continue          # free-text provenance note, not an item reference
        origin_item, _archived = _read_item_any(state, origin)
        if not isinstance(origin_item, dict):
            continue          # a phantom origin is refused by `state._assert_origins_resolve`
        origin_root = _root_of(origin_type, origin_item)
        if origin_root and origin_root != root["id"]:
            raise DispatchError(
                "derives_from %s belongs to %s, not to this task's root %s -- refused at "
                "creation (spec II.8). The dispatch gate resolves acceptance_refs against the "
                "ORIGIN, so this task would be judged against another root's criteria, and "
                "`python scripts/harness.py validate` reports it as an error that blocks every "
                "merge. Remedy: create the task under %s, or name an origin that hangs from %s "
                "-- the fields of an existing task are frozen outside DRAFT, which is why this "
                "is refused now rather than reported later."
                % (origin, origin_root, root["id"], origin_root, root["id"])
            )


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
            # THE WAIT IS NAMED, and so is the command that ends it. This said "wait for the lease
            # to resolve or time out" and nothing else -- no duration, no command -- so a role that
            # hit it after a denied spawn had a fifteen-minute stall it could not measure and no
            # instruction it could act on. The remaining seconds are read off the lease that is
            # actually there.
            held = _read_lease(state, task_id)
            left = float(held["created_epoch"]) + float(held["ttl"]) - time.time()
            raise DispatchError(
                "a lease for %s already exists -- parallel second claim blocked (spec II.4). It "
                "expires in %d s%s. Remedy: wait, then `python scripts/harness.py sweep-leases`, "
                "which returns every EXPIRED lease's task to READY and reports what is still "
                "running; a lease this task no longer needs is also dropped by any transition off "
                "%s."
                % (task_id, max(0, int(left)),
                   " (already expired -- the sweep releases it now)" if left <= 0 else "",
                   "/".join(LEASE_BEARING_STATUSES))
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
                "blocked (fail-closed). Remedy: `python scripts/harness.py doctor` shows the "
                "lease; `python scripts/harness.py sweep-leases` returns the task to READY."
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
            # ...and MEMBERSHIP IS NOT RESOLUTION. The paragraph above says both checks "ask
            # whether the reference RESOLVES", and this one did not: `design_refs` lives on the
            # ROOT, is not a binding field (`PARENT_FIELDS`), and is therefore never resolved on
            # any write path -- so `capture PR … "design_refs":["DSN-9999"]` followed by
            # `create-task --design-ref DSN-9999` was a SPAWN ALLOWED against a design that does
            # not exist (measured 2026-07-31, before this).
            #
            # WHAT A `design_ref` IS, read off the producer rather than assumed: `staging.
            # freeze_design` writes a STATE-RELATIVE PATH (`design/revisions/DSN-0001.r01.html`)
            # and `freeze_wireframe` the same shape, because a frozen revision is a FILE, not an
            # item with its own automaton (II.6a: "Zustand = Ort + approval_ref"). A role writing
            # the field by hand reaches for the id instead, which is what the measured hole used.
            # Both are accepted and both must resolve -- a path to a file under the state root, an
            # id through `exists_anywhere` (which already knows a frozen revision lives at
            # `<id>.rNN.yaml`). Anything else resolves to nothing and is refused.
            missing = [ref for ref in confirmed if not _design_ref_resolves(state, ref)]
            if missing:
                raise DispatchError(
                    "%s names design references that exist nowhere: %s -- dispatch blocked "
                    "(spec II.6a: design_ref is the BINDING implementation reference, and a "
                    "reference to nothing binds nothing). Remedy: freeze the design through the "
                    "promotion path, or correct %s's design_refs."
                    % (root["id"], ", ".join(missing), root["id"])
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


def live_leases(state: ProjectState) -> list:
    """[(task_id, seconds_left)] for every lease a sweep did NOT release, sorted.

    WHY THE SWEEP HAS TO SAY THIS. `sweep-leases` printed the released ids and nothing else, so a
    role holding a task blocked by "a lease for TSK-0007 already exists -- parallel second claim
    blocked" ran it, read `released to READY: -`, and had no way to learn whether the wait was
    five seconds or fifteen minutes. Silence there is what turns a bounded wait into a stall.
    """
    remaining = []
    with state.lock:
        for lease in _iter_leases(state):
            left = float(lease["created_epoch"]) + float(lease["ttl"]) - time.time()
            if left > 0:
                remaining.append((str(lease["task_id"]), left))
    return sorted(remaining)


# The statuses a lease SERVES, and therefore the only ones it may outlive its creation into.
# `create_lease` puts a task in the first and `spawn_outcome` moves it to the second while keeping
# the lease, because `task_for_agent` resolves a running child's writes through it; `submit_result`
# removes it. Any OTHER status means no child is coming and none is running, so a lease left behind
# there blocks the next claim for its whole TTL with nothing on the other end.
# `test_the_lease_bearing_statuses_are_the_ones_the_lifecycle_produces` drives create_lease,
# spawn_outcome and submit_result and reads the statuses off the running code, so this tuple cannot
# quietly stop describing the lifecycle.
LEASE_BEARING_STATUSES = ("LEASED", "IN_PROGRESS")


def release_lease_for_status_locked(state: ProjectState, task_id: str, status: str) -> bool:
    """Drop a lease the task's new status no longer serves; True when one was dropped.

    THE DEAD END THIS ENDS, measured 2026-08-02: `transition TSK-0001 READY` off LEASED (an
    explicit back-edge in the TSK automaton, spec II.2 Querregeln) moved the status and left the
    lease file in place. The task then read READY while `create_lease` refused it with "a lease for
    TSK-0001 already exists", `validate` reported nothing at all, and the only exit was to wait out
    the TTL. `transition ... CANCELLED` from LEASED or IN_PROGRESS left the same wreckage on a task
    nobody would ever sweep.

    Called from `state._transition_locked`, i.e. from EVERY transition, so the rule is a property
    of the status rather than of the four callers that happen to move a task today.
    """
    # No item-type test: a lease is keyed by task id, so a non-task simply has no lease file and
    # the existence check below answers for it. One condition instead of two spellings of one.
    if status in LEASE_BEARING_STATUSES:
        return False
    if not os.path.exists(_lease_path(state, task_id)):
        return False
    _remove_lease(state, task_id)
    return True


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
    of the THREE legitimate routes, never neither.

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
    3. ROUTINE route: an `APR.kind: routine` on this root covers this task's
       ROLE and the task claims no writable scope (see `_covering_routine_apr`).
       Spec II.1 makes the auditor "eine VERPFLICHTENDE Routine ... legitimiert
       durch eine widerrufbare `APR.kind: routine`-Freigabe" and II.10a demands
       that an expired or revoked one block that dispatch fail-closed. Until
       this route existed the kernel had no reader for the kind at all, so the
       expiry branch it demands was dead code on this path and the auditor rode
       an `analysis` approval whose manifest has to list every single run
       (measured 2026-07-26, re-measured 2026-07-31, disposition line 100).

    THE TWO TASK ROUTES ARE NOT BOUND ALIKE, and the difference decides what happens
    when the ROOT's own approval has stopped granting anything: the routine route
    refuses a task that claims a writable scope, the analysis route binds a listed
    task and nothing else. So the read-only fall-through below is conditional on the
    TASK, never on which route might catch it -- see the `except` branch.
    """
    refusals = []
    apr_ref = root.get("approval_ref")
    if apr_ref:
        try:
            apr = _read_root_apr(state, apr_ref)
            if apr.get("kind") in ROOT_DISPATCH_KINDS:
                _assert_root_approval_locked(state, root)
                return
        except DispatchError as exc:
            # A ROOT WHOSE APPROVAL NO LONGER GRANTS ANYTHING MAY STILL BE READ, NEVER WRITTEN.
            # That is the whole condition, and getting it wrong once is why it is stated as a
            # rule rather than as a route: refusing outright made the audit unreachable in
            # exactly the situation an audit exists for (scope approval REVOKED, or the root
            # edited past the kernel), while falling through UNCONDITIONALLY -- what the first
            # cut of this did -- handed the same amnesty to implementation work. `analysis` is
            # what made that measurable: `_covering_analysis_apr` binds a LISTED TASK and nothing
            # else, so any task some analysis approval lists walked past both tripwires
            # `assert_apr_in_force` exists for. Measured 2026-07-31: root edited out of band
            # (revision unchanged, content hash broken) -> IMPLEMENTATION dispatch ALLOWED; root
            # approval revoked -> ALLOWED. The revocation is the worse of the two, because a user
            # deliberately withdrew it.
            # So the fall-through is conditional on the TASK claiming no writable scope -- the
            # same `_claims_writable_scope` the routine route binds to. A writable task gets the
            # root's own refusal, verbatim and unaggregated, exactly as before.
            if _claims_writable_scope(task):
                raise
            refusals.append("the approval %s presents (%s): %s" % (root["id"], apr_ref, exc))
        # an approval of a non-dispatching kind raises nothing and is NOT an error on the item --
        # it simply does not authorise a spawn, so fall through to the task routes
    if _covering_analysis_apr(state, task["id"]) is not None:
        return
    covering, routine_refusals = _covering_routine_apr(state, task, root)
    if covering is not None:
        return
    refusals += routine_refusals
    raise DispatchError(
        "no user approval authorises dispatching %s under %s -- blocked (spec II.2: no "
        "subagent without a user approval). Remedy: obtain the scope approval for %s, or "
        "an analysis approval that LISTS %s in its subject manifest, or -- for a recurring "
        "read-only run -- a routine approval on %s naming role %r (spec II.10a).%s"
        % (task["id"], root["id"], root["id"], task["id"], root["id"],
           task.get("assigned_role"),
           (" The approvals that name %s and why none of them covers it: %s"
            % (root["id"], "; ".join(refusals))) if refusals else "")
    )


def _read_root_apr(state: ProjectState, apr_ref: str) -> dict:
    """The APR a root presents, refused in the DISPATCH vocabulary when it cannot be read.

    `read_apr` raises `ApprovalError`, which is not a `DispatchError` -- and the hook classifies
    anything else as an internal error, so a MISSING approval file reached the user as "the
    harness is broken, run the doctor" instead of "this root's approval is gone". The same
    argument `_assert_root_approval_locked` makes for its own re-raise; it lived one call too far
    in, so the one failure that skipped that function skipped the translation too, and with it the
    read-only fall-through that every other reason for "grants nothing" gets.
    """
    try:
        return read_apr(state, apr_ref)
    except ApprovalError as exc:
        raise DispatchError("dispatch blocked (spec II.4): %s" % exc) from None


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


def _claims_writable_scope(task: dict) -> bool:
    """Does this task's work order CLAIM the right to write outside the state directory?

    `allowed_scope` is the claim, and this asks only about the claim. Truthy rather than a length
    test on purpose: a single unusable entry (`[""]`, `["."]`) is a claim to something, and
    `gate_write_scope._scope_entries` refuses those loudly rather than reading them as
    "everything", so a task carrying one is not read-only here either.

    WHAT REFUSING SUCH A TASK BUYS, AND WHERE IT STOPS -- measured 2026-07-31, because the first
    version of this docstring claimed the whole of it and the harness builds half:
      * a work order with an empty `allowed_scope` is refused every write outside the state
        directory BY THE WRITE TOOLS: `gate_write_scope.handle_file_write` reads the bound task
        and blocks Edit/Write/MultiEdit/NotebookEdit (measured rc 2). Inside the state directory
        it never consults the field -- the specialist keeps its own `staging/<task-id>/`, which is
        the one exception the auditor role is written around.
      * THE SHELL PATH CHECKS NO TASK SCOPE AT ALL. `gate_write_scope.handle_shell` never resolves
        the bound task; it decides on whether the command line names the state directory or the
        enforcement layer. Measured with a bound auditor whose `allowed_scope` is empty, against
        all eight registered `Bash|PowerShell` PreToolUse hooks: `echo pwned > src/x.py`,
        `rm -rf src` and `git commit -am wip` all rc 0. The auditor carries `Bash`.
    So what this route enforces is the WORK ORDER, not a sandbox: a routine approval cannot
    authorise a task that is planned to write, and it does not stop a spawned agent from writing
    through a shell. Gate layer 3 for the shell is an open hole of `gate_write_scope`, older than
    this route and shared by every bound specialist; it is pinned as such in
    `tools/test_hooks_v2.py` under the `state_write_protection.shell` capability, so
    `python scripts/harness.py doctor` reports that capability `unverified` rather than green.
    """
    return bool(task.get("allowed_scope"))


def _covering_routine_apr(state: ProjectState, task: dict, root: dict):
    """(approval, refusals): a `routine` approval that authorises THIS dispatch, plus why the
    others did not.

    WHAT A ROUTINE BINDS, and therefore what this checks -- spec II.2 makes it "gebunden an
    Rolle, Read-only-Scope, Trigger, Ablaufdatum und jederzeit widerrufbar", II.10a hashes all
    of those plus the Takt:
      * the ROOT it was minted for, and everything `assert_apr_in_force` means by "in force":
        revoked, unprovable (`consumed_request`), foreign, or past its expiry. The expiry is
        re-read on EVERY dispatch, from the hash-covered manifest of the minted request, so a
        lease taken before the clock ran out does not carry the spawn past it -- `create_lease`
        and `validate_dispatch` both come through here.
      * the ROLE. A route that did not bind it would let one signature spawn any specialist.
      * READ-ONLY, via `_claims_writable_scope`. This is what keeps the route from being the
        blanket permission `ROOT_DISPATCH_KINDS` deliberately withholds: a routine can authorise
        a recurring audit, and it can never authorise implementation work under the same root.
    Read out of the CONSUMED REQUEST, never the approval file, for the reason the analysis route
    is: the request is the part only `mint` can produce, so a hand-written `APR-0001.yaml`
    claiming any role it likes authorises nothing (spec II.12).

    WHAT IT DOES NOT CHECK, named because the manifest carries it and a reader would otherwise
    assume the kernel acts on it: `trigger` and `cadence` say WHEN the routine may run, and
    nothing in this kernel records when it last did -- II.10a's `last_completed`/`next_due` have
    no producer. `scope` says where the run may READ, and there is no read gate at any layer. All
    three are inside the hashed manifest, so they cannot be moved without breaking the approval;
    they are simply not enforced, and the auditor's role text says so in the same words.

    AND WHAT MINTING ONE COSTS, which is the interaction this route invites rather than creates:
    `mint` writes `approval_ref` for every item-bound approval, and the DELIVERY route above reads
    that ONE field. So a routine minted for a root that already carries a scope or delivery
    approval takes the reference with it, and implementation tasks under that root stop
    dispatching until the scope approval is obtained again -- the older approval is still valid,
    it is simply no longer the one the root presents. The refusal names both the cause and that
    action. Not repaired by making the delivery route search the store: which APR it rides on is a
    decision written next to it, and this route may not quietly rewrite the one beside it.
    """
    refusals = []
    approvals_dir = os.path.join(state.root, "approvals")
    if not os.path.isdir(approvals_dir):
        return None, refusals
    for name in sorted(os.listdir(approvals_dir)):
        if not (name.startswith("APR-") and name.endswith(".yaml")):
            continue
        try:
            apr = state._read_yaml(os.path.join(approvals_dir, name))
        except Exception:  # noqa: BLE001 -- an unreadable approval authorises nothing
            continue
        if not isinstance(apr, dict) or apr.get("kind") != "routine":
            continue
        if str(apr.get("item") or "") != root["id"]:
            continue
        apr_id = apr.get("id") or name[:-5]
        try:
            request = assert_apr_in_force(state, apr, root)
        except ApprovalError as exc:
            refusals.append("%s: %s" % (apr_id, exc))
            continue
        manifest = request.get("subject_manifest") or {}
        role = str(manifest.get(ROUTINE_ROLE_FIELD) or "")
        if role != str(task.get("assigned_role") or ""):
            refusals.append(
                "%s covers role %r, not %r" % (apr_id, role or "<none>", task.get("assigned_role")))
            continue
        if _claims_writable_scope(task):
            refusals.append(
                "%s is a READ-ONLY routine (spec II.2), but %s claims allowed_scope %s"
                % (apr_id, task["id"], task.get("allowed_scope")))
            continue
        return apr, refusals
    return None, refusals


def _assert_root_approval_locked(state: ProjectState, root: dict) -> None:
    """Root carries a CURRENT approval that is still in force.

    Which APR that is, is this function's own question: `approval_ref` names the approval the root
    presents, and the dispatch route rides on THAT one (its kind decided the route two frames up).
    Whether it still grants anything is `approvals.assert_apr_in_force`, shared with the status
    automaton -- revoked, unprovable, foreign, expired, or invalidated by an out-of-band edit are
    the same five answers whoever asks, and the copy that used to live here is how a shared fact
    becomes two facts.

    ApprovalError is NOT a DispatchError, and the hook classifies anything else as an internal
    error -- so a provable-policy refusal would reach the user as "the harness is broken, run the
    doctor" instead of "this approval is not proven". Re-raised in the dispatch vocabulary here,
    with the consequence this caller adds and the shared check deliberately does not carry.
    """
    apr_ref = root.get("approval_ref")
    if not apr_ref:
        raise DispatchError(
            "root %s has no current approval -- dispatch blocked (fail-closed). "
            "Remedy: obtain the scope/delivery approval." % root["id"]
        )
    apr = read_apr(state, apr_ref)
    try:
        assert_apr_in_force(state, apr, root)
    except ApprovalError as exc:
        raise DispatchError("dispatch blocked (spec II.4): %s" % exc) from None


def _design_ref_resolves(state: ProjectState, reference: str) -> bool:
    """Does this `design_refs` entry name a FROZEN DESIGN that exists? (see validate_dispatch)

    "EXISTS" IS NOT ENOUGH, and the first cut of this function proved it. It asked
    `os.path.exists(state.root/<entry>)`, which is true of `README.md`, of `generated/index.yaml`,
    of `.`, of `..` and of `../.claude/settings.json` -- measured 2026-07-31 end to end over the
    shipped surface: `capture PR … "design_refs":["../.claude/settings.json"]`, a UI task naming
    that ref, scope approval, lease, and the spawn was ALLOWED. The II.6 rule was still satisfiable
    by a self-written reference; only the shape had changed from a phantom id to any path at all.
    Its own docstring claimed the opposite ("an entry that escapes the state root simply does not
    resolve"), which is the comment shape this kit refuses.

    TWO FORMS, AND THE ID FORM IS ASKED FIRST -- which is the correction to the first version of
    this function, where it was DEAD CODE. A bare `DSN-0001` is also a relative path under the
    state root, so it entered the path branch, was not a file, and came back False: the branch
    below could only ever be reached by a reference that lands on or outside the root, and none of
    those parses as an id. Measured after a real `freeze_design`: `exists_anywhere('DSN-0001')`
    True, `_design_ref_resolves('DSN-0001')` False -- so the docstring's promise was wrong AND a
    `design_refs` entry in id form locked every legitimate UI dispatch. Replacing the whole branch
    with `return False` changed no test, which is why the test below now carries a REAL frozen id
    in the accepted list rather than only a phantom in the refused one.

    THE PATH FORM, three conditions, each closing one measured case:
      * CONTAINMENT -- `realpath`, not `normpath`. `normpath` is textual, and `os.path.isfile`
        follows links: measured with `mklink /J project_memory/design/revisions/out .claude`, the
        entry `design/revisions/out/settings.json` resolved True while its real path lay outside
        the state root entirely. This repo has paid for a symlink-blind path comparison once
        already (`hashing._bundle_files`); resolving both sides is the same fix in one word.
      * IT MUST BE A FILE. A frozen revision is a file (II.6a: "Zustand = Ort"), so `staging`,
        `.` and every other directory stop here.
      * IT MUST LIE WHERE THE PRODUCER PUTS ONE (`staging.frozen_design_dirs`).
    """
    from .staging import frozen_design_dirs

    reference = str(reference or "").strip()
    if not reference:
        return False
    try:
        parse_id(reference)
    except ValueError:
        pass
    else:
        return state.exists_anywhere(reference)
    root = os.path.realpath(state.root)
    target = os.path.realpath(os.path.join(state.root, reference.replace("/", os.sep)))
    if target == root or not target.startswith(root + os.sep):
        return False
    relative = os.path.relpath(target, root).replace(os.sep, "/")
    return os.path.isfile(target) and any(
        relative.startswith(directory + "/") for directory in frozen_design_dirs())


def _read_item_any(state: ProjectState, item_id: str):
    """Return (item, archived); the caller holds the lock.

    Delegates to `ProjectState.read_anywhere` -- this was the original home of
    that walk, and the merge gate needed the same one. Two readers of one storage
    layout is the defect this repo keeps finding, so the walk moved to the state
    object and this name stays as the local spelling.
    """
    return state.read_anywhere(item_id)


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
            "Remedy: `python scripts/harness.py doctor` inspects leases; removing the corrupt "
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
