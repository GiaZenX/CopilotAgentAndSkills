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

from .approvals import read_apr
from .backlog_types import parse_id
from .schemas import validate
from .state import ProjectState, StateError, _now_iso

HEADER_PREFIX = "HARNESS_DISPATCH "
DEFAULT_LEASE_TTL = 15 * 60.0


class DispatchError(StateError):
    """Dispatch-gate violation -- fail-closed, message carries the remedy."""


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
        apr_ref = root.get("approval_ref")
        if not apr_ref:
            raise DispatchError(
                "root %s has no current approval -- dispatch blocked "
                "(fail-closed). Remedy: obtain the scope/delivery approval."
                % root["id"]
            )
        apr = read_apr(state, apr_ref)
        if apr.get("revoked"):
            raise DispatchError(
                "approval %s is revoked -- dispatch blocked. Remedy: obtain a "
                "fresh approval." % apr_ref
            )
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
        # spec II.4 gate 2 / II.12: "offene Abhaengigkeit -> Block" -- a
        # dependency is satisfied once its work was accepted (DONE) or QA'd
        # (VALIDATED); archived deps count only if they ended VALIDATED
        open_deps = []
        for dep_id in task.get("dependencies") or []:
            dep, archived = _read_item_any(state, dep_id)
            if dep is None:
                open_deps.append("%s (missing)" % dep_id)
            elif dep.get("status") not in ("DONE", "VALIDATED"):
                open_deps.append("%s (%s)" % (dep_id, dep.get("status")))
        if open_deps:
            raise DispatchError(
                "%s has open dependencies: %s -- dispatch blocked (spec II.4). "
                "Remedy: finish the dependencies first."
                % (task_id, ", ".join(open_deps))
            )
        # TODO(1.4c/phase 2): once routine/analysis APRs carry `expires`,
        # create_lease must also block on expired approvals (spec II.10a)
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


def bind_agent(state: ProjectState, task_id: str, agent_id: str) -> dict:
    """SubagentStart: bind the child's agent_id to the lease (spike S3 --
    the documented binding point; child tool calls carry the same agent_id)."""
    with state.lock:
        lease = _read_lease(state, task_id)
        lease["agent_id"] = agent_id
        state._write_yaml_atomic(_lease_path(state, task_id), lease)
        return lease


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
