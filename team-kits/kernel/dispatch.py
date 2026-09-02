"""Dispatch leases + result submission (HARNESS_V2_SPEC.md II.4) -- step 1.4b.

READY -> short-lived lease (nonce + TTL) -> `HARNESS_DISPATCH` header ->
PreToolUse validates the lease and CLAIMS it for one dispatch (hook, phase 2) ->
SubagentStart binds the child's agent_id to the lease -> spawn outcome moves the
task (success: IN_PROGRESS, failure: straight back to READY) -> an orphaned lease
falls back to READY after TTL. The gate parses ONLY the header, never prose.

A claim that produces NO child is undone by the clock, not by an event:
`spent_claim_reason` says what makes a claim still stand and
`reconcile_unstarted_dispatches` returns the task to READY once it does not.
Measured 2026-08-02: the provider delivers no hook event for a permission
refusal at all, so a rollback that needs one is a rollback that may never run.

submit_result validates the <=4 KB result envelope against its schema and
moves IN_PROGRESS -> SUBMITTED; the envelope is stored beside the task.
"""
from __future__ import annotations

import json
import operator
import os
import time
import uuid

from .approvals import (
    ROOT_DISPATCH_KINDS,
    ROUTINE_ROLE_FIELD,
    ApprovalError,
    approved_statuses,
    assert_apr_in_force,
    consumed_request,
    item_subject_manifest,
    proven_expiry,
    read_apr,
)
from .backlog_types import (
    AMENDMENT_TYPES,
    AUTOMATA,
    PARENT_FIELDS,
    UI_TASK_TYPES,
    field_elements,
    parse_id,
)
from . import references
from .lock import ext_path
from .schemas import validate
from .state import ProjectState, StateError, _now_iso

HEADER_PREFIX = "HARNESS_DISPATCH "
DEFAULT_LEASE_TTL = 15 * 60.0
# How long a validated dispatch waits for its SubagentStart to claim it (see
# mark_awaiting_bind); generous enough for a slow spawn, short enough that a
# failed spawn does not leave a claimable slot lying around.
#
# It bounds the CLAIM as well, and that is one window rather than two on purpose:
# "the child may still arrive" and "the claim still stands" are the same
# question. See `spent_claim_reason` and `reconcile_unstarted_dispatches` -- past
# this window a dispatch that produced no child is not evidence of anything, and
# the task goes back to READY without any hook event having to say so.
BIND_WINDOW = 120.0
# where an `APR.kind: analysis` lists the tasks it covers (spec II.2 Buendelung:
# "EINE analysis- oder scope-APR darf MEHRERE im subject_manifest GELISTETE
# Analyse-Tasks decken"). Named here because the manifest is otherwise free-form
# for analysis, and a gate cannot check a key nobody agreed on.
ANALYSIS_TASKS_KEY = "tasks"
# The item fields that OFFER criterion ids (spec II.2: PR/RQ/CR/BUG carry
# `acceptance_criteria`, EXP carries `success_criteria`). One tuple, because two
# readers ask about it in opposite directions -- `_criteria_ids` collects the ids
# out of them, `_approval_covers_criteria` asks whether an approval's manifest
# signed them -- and a second spelling would let the second reader vouch for a
# field the first one reads.
CRITERIA_FIELDS = ("acceptance_criteria", "success_criteria")

# WHICH PROVIDER TOOLS RUN A COMMAND LINE. Provider knowledge, so nothing here can
# derive it; it lives in the kernel because the party that has to ACT on it is the
# kernel (`hand_back_path` below) and a kit hook cannot be imported from here. The
# gate that routes on the same fact keeps its own tuple
# (`gate_write_scope.SHELL_TOOLS`) rather than importing this one, because that
# routing must survive a project whose kernel is unreachable; the two ends and the
# kit's own `settings.json` matcher are measured against each other by
# `tools/test_role_contracts.py::test_the_command_running_tools_are_one_fact_in_three_places`.
COMMAND_TOOLS = ("Bash", "PowerShell")

# WHO BOOKS A SPECIALIST'S RESULT IN. Two values, and which one applies to a role is
# a fact about that role's installed definition, never a list: a role whose `tools:`
# frontmatter names none of `COMMAND_TOOLS` cannot run the entry point at all, so
# `submit-result` is not a step it can take. Measured in pilot 3 (BUG-0048) three
# times: the roles reported the demand as a gap instead of working around it, which
# is the honest outcome of a contract that asks for something the toolset withholds.
# The value rides in the lease and then in the dispatch header, so the role is told
# its path at the one moment the dispatch is composed.
HAND_BACK_KEY = "hand_back"
HAND_BACK_SELF = "self"
HAND_BACK_LEAD = "lead"
# The reference skills a dispatch names (FR-0071). Like `checkpoint` and `hand_back` this is a
# POINTER carried in the header and NOT one of the three keys `parse_header` decides on, so it
# grants nothing; `kernel.references` computes it from the task.
REFERENCES_KEY = "references"


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

    for origin in field_elements(fields.get("derives_from")):
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
        # THE ADOPTION OFFER IS MADE HERE, at the one moment a dispatch is composed, so that what
        # the specialist receives says whether there is anything to resume -- and says it ONLY when
        # the verification passed (DEC-0044: an unverified checkpoint is treated as absent). The
        # key is absent otherwise, so "no offer" and "a failing offer" are the same envelope.
        # `checkpoint_verdict` is the caller's route to the REASONS, which belong in front of a
        # human rather than in the header.
        verdict = checkpoint_verdict(state, task_id, _locked=True)
        if verdict.adoptable:
            lease["checkpoint"] = verdict.pointer
        # ...AND THE HAND-BACK PATH, decided here for the same reason: this is the one moment a
        # dispatch is composed, and the role's own definition is what decides it (BUG-0048).
        # Absent when the definition cannot be read -- see `hand_back_path`.
        path = hand_back_path(agents_dir(os.path.dirname(state.root)),
                              task.get("assigned_role"))
        if path:
            lease[HAND_BACK_KEY] = path
        # ...AND THE REFERENCE SKILLS THIS TASK NAMES (FR-0071), derived here for the third time
        # for the same reason: this is the one moment a dispatch is composed, and the TASK is what
        # decides -- its `assigned_role` and its `type`, both frozen plan fields. The alternative
        # was leaving the pick to the role, which is the habitual-pick failure the item names.
        # Absent when nothing matches, so "this kit ships no reference skills" and "none applies to
        # this task" are the same envelope, and the key grants nothing either way.
        reference_skills = references.for_task(
            references.skills_dir(os.path.dirname(state.root)),
            task.get("assigned_role"), task.get("type"))
        if reference_skills:
            lease[REFERENCES_KEY] = reference_skills
        state._write_yaml_atomic(lease_path, lease)
        task["status"] = LEASE_MINTED_STATUS
        task["leased_at"] = _now_iso()
        # A NEW LEASE IS A NEW DISPATCH, so what the PREVIOUS run's child did stops being evidence
        # about this task here. Left standing, the records would report a retry as idle before its
        # child has even been asked for -- see `idle_dispatches` and `CHILD_ENDED`.
        task.pop(CHILD_ENDED, None)
        task.pop(IDLE_REPORTED, None)
        state._write_yaml_atomic(state.active_path(task_id), task)
        state._regenerate_index_locked()
        return lease


def checkpoint_verdict(state: ProjectState, task_id: str, _locked: bool = False):
    """What `kernel.checkpoints` says about this task's checkpoint -- deferred so the two stay leaves.

    `checkpoints` imports `LEASE_BEARING_STATUSES` from here, so a module-level import in this
    direction would be a cycle. The same shape as `_assert_origins_belong_to_root_locked`'s import
    of `report`, and for the same reason.
    """
    from .checkpoints import verify

    return verify(state, task_id, _locked=_locked)


def agents_dir(repo_root: str) -> str:
    """Where the INSTALLED role definitions live, asked of the installer that puts them there.

    `presets.AGENTS_DIR` is the path the kit installer writes into, so a kit that moved its
    role definitions would move this reader with it. Deferred import for the reason
    `checkpoint_verdict` gives: `presets` pulls in `subprocess`/`shutil` for the installer it
    drives, and a lease does not need them.
    """
    from .presets import AGENTS_DIR

    return os.path.join(repo_root, AGENTS_DIR)


def role_tools(definitions: str, role: str):
    """The tools `role`'s definition grants, or None when it cannot be read.

    `definitions` is the DIRECTORY the role definitions live in -- `agents_dir(repo_root)` in an
    installed project, `<kit>/agents` for the shipped source, which is how the suite judges a kit
    before anybody installs it.

    None is NOT "no tools": it means the question could not be asked -- an uninstalled kit, a
    role name nobody ships, a definition without frontmatter. Every caller has to distinguish
    the two, because "this role has no shell" is a statement about a contract and "I could not
    look" is a statement about this process.
    """
    import yaml

    path = os.path.join(definitions, str(role or "") + ".md")
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        # THE NEIGHBOUR OF THE SAME DEFECT, fixed in the same shape. Here the file is one the
        # installer writes, so no measured chain reaches it -- `kernel.references._frontmatter`
        # carries the one that was measured, and this is the identical line rather than a second
        # answer to "what does this reader do with a file it cannot decode".
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    try:
        front = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return None
    if not isinstance(front, dict):
        return None
    granted = front.get("tools")
    if granted is None:
        return None
    if isinstance(granted, str):
        granted = [part.strip() for part in granted.split(",")]
    if not isinstance(granted, list):
        return None
    return [str(one).strip() for one in granted if str(one).strip()]


def hand_back_path(definitions: str, role: str):
    """`HAND_BACK_SELF`, `HAND_BACK_LEAD`, or None when the role definition cannot be read.

    THE PROPERTY, not a list of role names: a role can book its own result in exactly when its
    installed definition grants a tool that runs a command line (`COMMAND_TOOLS`), because
    `submit-result` IS a command line. A role added tomorrow is judged by its own frontmatter on
    the day it ships, and one that gains or loses a shell changes path without anybody editing a
    contract.

    None keeps the dispatch silent rather than guessing. The constitution states the path for
    every role anyway (the hand-back is the final message; the lead books it in), so an absent
    key withholds an ADDITIONAL permission and never grants one.
    """
    granted = role_tools(definitions, role)
    if granted is None:
        return None
    runnable = {tool.lower() for tool in COMMAND_TOOLS}
    return (HAND_BACK_SELF if any(tool.lower() in runnable for tool in granted)
            else HAND_BACK_LEAD)


def dispatch_header(lease: dict) -> str:
    """The ONLY thing the gate parses -- never free prompt prose (spec II.4).

    `checkpoint` rides ALONG when `create_lease` verified one, because the header is the part of the
    envelope that reaches the specialist verbatim; `parse_header` names the three keys the gate
    decides on and this is not one of them, so it grants nothing. It is a POINTER the specialist
    re-verifies for itself (`python scripts/harness.py checkpoint-status <TSK-ID>`) -- the tree can
    move between the lease and the spawn, and a pointer inside a model-composed prompt is not
    evidence of anything on its own.
    """
    body = {
        "task_id": lease["task_id"],
        "root_revision": lease["root_revision"],
        "lease": lease["nonce"],
    }
    if lease.get("checkpoint"):
        body["checkpoint"] = lease["checkpoint"]
    # WHO BOOKS THIS RESULT IN, in the one part of the prompt that reaches the specialist
    # verbatim. Like `checkpoint` it grants nothing -- `parse_header` names the three keys the
    # gate decides on and this is not one of them -- it TELLS the role which of the two paths
    # the constitution describes is the one its own toolset can walk (BUG-0048).
    if lease.get(HAND_BACK_KEY):
        body[HAND_BACK_KEY] = lease[HAND_BACK_KEY]
    # ...AND WHICH REFERENCE SKILLS THIS ORDER NAMES (FR-0071). Same standing as the two above: a
    # pointer, in the one part of the prompt that reaches the specialist verbatim, so that the
    # choice is in the ORDER rather than in the role's habits. The role still has to open them --
    # a name in a header is not a loaded file.
    # NOT a local called `named`: `test_backlog_types._key_read_aliases` follows one binding by NAME
    # and is scope-blind, so a second `named` in this module inherits this one's key and the
    # unrelated `"; ".join(named)` at the bottom of the file is reported as an unguarded read of a
    # reference-list field (measured, red).
    reference_skills = lease.get(REFERENCES_KEY)
    if reference_skills:
        body[REFERENCES_KEY] = reference_skills
    return HEADER_PREFIX + json.dumps(body, sort_keys=True)


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
        # THE ONE RELEASE SITE THAT DID NOT REGENERATE, of the four this function has siblings in
        # (`reconcile_unstarted_dispatches`, `spawn_outcome`, `sweep_expired_leases` all do). The
        # release resets the task to READY on disk, so without this the index -- and the board over
        # it -- kept saying LEASED for a task nobody holds any more (TSK-0071 verifier finding B2).
        # Only on the EXPIRY branch, which already writes the item; a validation that passes stays
        # a pure read.
        _release_lease_locked(state, header["task_id"], to_ready=True)
        state._regenerate_index_locked()
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


def spent_claim_reason(lease: dict):
    """Why this lease may not be claimed (again), or None -- ONE definition of a spent claim.

    WHEN A CLAIM MAY COME INTO EXISTENCE, stated as a property rather than as a
    flag: a claim is the record that a child was ASKED FOR. It may stand only
    while that ask can still produce a child, or while one exists. Nothing else
    about it is evidence of anything.

    Two terms, and both are things that were OBSERVED rather than assumed:
      * `agent_id` -- a child is bound to this lease. It exists; a second claim
        would be a second child under one grant.
      * an ask that is still in flight -- the bind window opened when the claim
        was made has not closed yet, so the child may still arrive.

    TWO HERE, FOUR IN `reconcile_unstarted_dispatches`, and they are not one list
    counted twice -- the two functions answer opposite questions. This one asks
    "may this lease be claimed (again) NOW", and needs only the reasons a claim
    still stands. The other asks "may this lease be GIVEN BACK", which is a
    stronger question: it adds that a claim was ever made (an undispatched lease
    is nobody's failure) and that the task is still LEASED (an outcome already
    recorded must not be undone). Anyone quoting a number should say which of the
    two functions it belongs to.

    WHAT WAS HERE BEFORE AND WHY IT WAS A DEAD END, measured 2026-08-02 in a real
    headless session: the term was `dispatched_at`, an eternal flag written at
    PreToolUse. Every PreToolUse hook of one event runs to completion even when a
    sibling exits 2, so the flag was written for a spawn another gate was
    refusing at the same moment; the retry was then refused for the remaining
    ~900 s of DEFAULT_LEASE_TTL. The rollback that was supposed to undo it hung
    on a `PermissionDenied` hook event, which fired in NONE of twelve measured
    sessions. A consumption whose undo depends on an event nobody has seen is a
    consumption without a way out, so the undo is now the clock plus
    `reconcile_unstarted_dispatches`, which needs no event at all.

    THE RESIDUAL, named rather than implied: two spawns of the SAME header issued
    inside one parallel batch both land inside the open window, so the second is
    refused -- that half holds. Two spawns MORE than BIND_WINDOW apart where the
    first really did start but neither `SubagentStart` nor `PostToolUse` was ever
    delivered would both be allowed. Such a first child is UNBOUND (nothing set
    `agent_id`), and gate layer 3 refuses every write from an unbound agent, so
    what is lost there is tokens, not scope.
    """
    if lease.get("agent_id"):
        return ("a child (%s) is already bound to the lease for %s"
                % (lease["agent_id"], lease["task_id"]))
    left = _window_open_until(lease) - time.time()
    if lease.get("dispatched_at") and left > 0:
        return ("the lease for %s was dispatched at %s and is still awaiting its child "
                "(%d s left)" % (lease["task_id"], lease["dispatched_at"], int(left)))
    return None


def reconcile_unstarted_dispatches(state: ProjectState) -> list:
    """Every claim that never produced a child -> the task back to READY. Returns the ids.

    THE WAY BACK FOR A SPENT LEASE, and it depends on no hook event whatsoever --
    which is the whole point. Spec II.4 wants "Fehlschlag -> sofort zurueck auf
    READY"; the events that could say "this spawn failed" are the provider's to
    deliver, and a real run showed the harness cannot rely on getting them:
    `PostToolUseFailure` does fire, a permission refusal fires NOTHING, and
    `PermissionDenied` -- which the rollback was registered on -- was never seen.
    So the condition here is the ABSENCE of evidence after the window in which
    evidence could still arrive, which is decidable locally:

        dispatched, no bound child, bind window closed, task still LEASED.

    Every one of the four is load-bearing. Without `dispatched` this would sweep
    a lease its owner has not spawned against yet. Without the `agent_id` check
    it would free a task whose child is running. Without the closed window it
    would race the child that is just starting. Without `LEASED` it would undo an
    outcome one of the post-spawn events already recorded.

    FOUR HERE, TWO IN `spent_claim_reason`: giving a lease back is a stronger
    claim than refusing to re-issue it, so it takes two conditions more. See that
    docstring for the pairing.

    Cost is BIND_WINDOW rather than DEFAULT_LEASE_TTL: 120 s instead of 900 s,
    and `sweep_expired_leases` remains the backstop for everything else (a bound
    child that never finished, a lease nobody dispatched).
    """
    released = []
    with state.lock:
        now = time.time()
        for lease in _iter_leases(state):
            if lease.get("agent_id") or not lease.get("dispatched_at"):
                continue
            if _window_open_until(lease) >= now:
                continue
            task_id = str(lease["task_id"])
            try:
                task = state.read_item(task_id)
            except StateError:
                continue
            if task.get("status") != "LEASED":
                continue
            _release_lease_locked(state, task_id, to_ready=True)
            released.append(task_id)
        if released:
            state._regenerate_index_locked()
    return released


def validate_dispatch(state: ProjectState, header: dict, subagent_type: str,
                      claim: bool = False, prompt_id: str = None,
                      session_id: str = None) -> dict:
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

    A claim OPENS THE BIND WINDOW in the SAME write, under the same lock hold,
    and that is not tidiness: `spent_claim_reason` reads that window to decide
    whether a claim still stands, so a claim recorded in one write and its window
    in the next would leave a moment in which the claim counted for nothing.
    `prompt_id` narrows the window exactly as `mark_awaiting_bind` documents.
    """
    with state.lock:
        task_id = header["task_id"]
        lease = _validate_lease_locked(state, header)
        if claim:
            spent = spent_claim_reason(lease)
            if spent:
                raise DispatchError(
                    "%s -- a second claim on one lease is blocked (spec II.4). "
                    "Remedy: create a fresh lease for a second attempt; the "
                    "specialist carries the nonce in its prompt, so re-using it "
                    "would spawn under a spent claim." % spent
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
        #
        # AND ONE HOP AWAY IS NOT THE WHOLE UNIVERSE EITHER -- BUG-0040. An
        # APPROVED AMENDMENT changes the ROOT's contract, so its criteria reach a
        # task that derives from the root and names no CR at all. The universe is
        # therefore derived rather than walked; `_known_acceptance_ids_locked` is
        # the one place it is built, and `excluded` is what it could not admit.
        refs = [str(ref) for ref in field_elements(task.get("acceptance_refs"))]
        known_ac, excluded = _known_acceptance_ids_locked(state, root, task)
        unknown = [ref for ref in refs if ref not in known_ac]
        if not refs or unknown:
            raise DispatchError(
                "%s %s -- a task nobody can check against the approved criteria "
                "is not dispatchable (spec II.4). Remedy: reference criteria that "
                "exist on %s, on its derives_from item, or on an approved amendment "
                "of %s (known: %s).%s"
                % (task_id,
                   "carries no acceptance_refs" if not refs
                   else "references criteria that exist nowhere: %s" % ", ".join(unknown),
                   root["id"], root["id"], ", ".join(sorted(known_ac)) or "none defined",
                   _amendment_hint(unknown, excluded))
            )
        if str(task.get("type", "")).lower() in UI_TASK_TYPES:
            confirmed = [str(ref) for ref in field_elements(root.get("design_refs"))]
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
            _open_bind_window(lease, prompt_id, session_id)
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


def mark_awaiting_bind(state: ProjectState, task_id: str, prompt_id: str = None,
                       session_id: str = None) -> dict:
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

    `validate_dispatch(claim=True)` opens the same window in its own write; both
    go through `_open_bind_window` so there is one description of what an open
    window is, and `spent_claim_reason` reads that same description back.
    """
    with state.lock:
        lease = _read_lease(state, task_id)
        _open_bind_window(lease, prompt_id, session_id)
        state._write_yaml_atomic(_lease_path(state, task_id), lease)
        return lease


def _open_bind_window(lease: dict, prompt_id: str = None, session_id: str = None) -> dict:
    """Mark a lease as awaiting its child for BIND_WINDOW seconds (caller writes).

    THE ASKING SESSION IS RECORDED HERE because this is the moment a child is ASKED FOR, and
    `DISPATCHING_SESSION` explains what the record is for. A caller that has no session id (an
    in-process test, a CLI) leaves the existing record standing rather than blanking it: a claim
    re-opened without the id must not turn a decidable dispatch into an undecidable one.
    """
    lease["awaiting_bind_until"] = time.time() + BIND_WINDOW
    lease["awaiting_bind_prompt"] = prompt_id
    if session_id:
        lease[DISPATCHING_SESSION] = str(session_id)
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


def spawn_outcome(state: ProjectState, task_id: str, ok: bool, session_id: str = None) -> dict:
    """PostToolUse on the spawn: success -> IN_PROGRESS, failure -> READY.

    THE SESSION IS RECORDED ON THE TASK AS WELL, and not only on the lease, because the lease is
    the record that goes away first: `sweep_expired_leases` drops it after the TTL while leaving an
    IN_PROGRESS task standing (see `LEASE_MINTED_STATUS`), and that is precisely the state BUG-0042
    measured -- "IN_PROGRESS with no live agent behind them". With the asker recorded only on the
    lease, that task would be undecidable for `orphaned_dispatches` forever.
    """
    with state.lock:
        task = state.read_item(task_id)
        if ok:
            if task.get("status") == "LEASED":
                task["status"] = "IN_PROGRESS"
                task["started"] = _now_iso()
                if session_id:
                    task[DISPATCHING_SESSION] = str(session_id)
                state._write_yaml_atomic(state.active_path(task_id), task)
        else:
            _release_lease_locked(state, task_id, to_ready=True)
            task = state.read_item(task_id)
        state._regenerate_index_locked()
        return task


def sweep_expired_leases(state: ProjectState):
    """(returned to READY, lease dropped only) for every expired lease (spec II.4: no task hangs).

    TWO LISTS AND NOT ONE, because for one of the two the sweep did LESS than it says. Measured
    2026-08-15 in a scaffolded project against the previous single list: an IN_PROGRESS task whose
    lease expired was printed as "released to READY: TSK-0001" while it stayed IN_PROGRESS --
    `_release_lease_locked` resets only `LEASE_MINTED_STATUS`, deliberately (a child can outlive its
    lease, see that constant). The task was then unleasable, unreported by `validate` and unnamed by
    the next sweep: the "IN_PROGRESS with no live agent behind them" dead end of BUG-0042, wearing a
    sentence that said the opposite. Every caller has to carry both halves; what to DO about the
    second one is a question only a new session can answer (`sweep_orphaned_dispatches`).
    """
    to_ready, lease_only = [], []
    with state.lock:
        lease_dir = os.path.join(state.root, "tasks", "leases")
        if not os.path.isdir(lease_dir):
            return to_ready, lease_only
        for name in sorted(os.listdir(lease_dir)):
            if not name.endswith(".lease.yaml"):
                continue
            task_id = name[: -len(".lease.yaml")]
            try:
                lease = _read_lease(state, task_id)
            except DispatchError:
                continue
            if _expired(lease):
                reset = _release_lease_locked(state, task_id, to_ready=True)
                (to_ready if reset else lease_only).append(task_id)
        if to_ready or lease_only:
            state._regenerate_index_locked()
    return to_ready, lease_only


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


# The single status a lease MINTS, and the one whose loss RESETS the task: `create_lease` produces
# it and `_release_lease_locked` returns a task in it to READY once the lease is gone. That
# one-to-one -- LEASED at rest <=> a live lease -- is what DEC-0038/BUG-0010 rests on: it is why a
# bare transition may not reach it (`assert_lease_backed_transition_locked`) and why a task FOUND in
# it without a live lease is an anomaly to REPORT rather than a running child to leave be
# (`leased_without_live_lease`). IN_PROGRESS is deliberately NOT this status: a running child can
# hold IN_PROGRESS past its lease's expiry -- `sweep_expired_leases` drops the lease but leaves the
# status (`_release_lease_locked` resets only LEASED) -- so IN_PROGRESS without a lease is expected,
# not corrupt. One spelling, referenced by `create_lease` and `_release_lease_locked`.
LEASE_MINTED_STATUS = "LEASED"

# The statuses a lease SERVES, and therefore the only ones it may outlive its creation into.
# `create_lease` puts a task in the first and `spawn_outcome` moves it to the second while keeping
# the lease, because `task_for_agent` resolves a running child's writes through it; `submit_result`
# removes it. Any OTHER status means no child is coming and none is running, so a lease left behind
# there blocks the next claim for its whole TTL with nothing on the other end.
# `test_the_lease_bearing_statuses_are_the_ones_the_lifecycle_produces` drives create_lease,
# spawn_outcome and submit_result and reads the statuses off the running code, so this tuple cannot
# quietly stop describing the lifecycle. It is ALSO the set a bare transition may not enter without
# a live lease (DEC-0038): a lease-served status can only be reached honestly through the lease.
LEASE_BEARING_STATUSES = (LEASE_MINTED_STATUS, "IN_PROGRESS")


def lease_in_force(state: ProjectState, task_id: str) -> bool:
    """True when a live (unexpired) lease file exists for this task -- the record a lease-bearing
    status rests on (DEC-0038). Caller holds the lock; a missing, corrupt or expired lease is not
    in force. Reuses `_read_lease`/`_expired` so "in force" has one definition."""
    if not os.path.exists(_lease_path(state, task_id)):
        return False
    try:
        lease = _read_lease(state, task_id)
    except DispatchError:
        return False
    return not _expired(lease)


def assert_lease_backed_transition_locked(state: ProjectState, item_id: str, to_status: str) -> None:
    """Refuse a DIRECT transition INTO a lease-bearing status when no live lease backs it.

    DEC-0038/BUG-0010: a lease-bearing status is ESTABLISHED by a real dispatch lease, never by a
    bare `transition`. `create_lease` (READY -> LEASED) and `spawn_outcome` (LEASED -> IN_PROGRESS)
    write those statuses DIRECTLY and never come through `state.transition`, so this refuses ONLY
    the parallel non-dispatch path -- the dispatch lifecycle is untouched (`create_lease` still
    reaches LEASED). The property is `LEASE_BEARING_STATUSES`, so a lifecycle that started keeping a
    lease into a further status would carry this guard with it rather than leaving a new hole.

    Caller holds the lock. No item-type test is needed: a lease-bearing status name lives only in
    the TSK automaton, so `assert_transition` has already refused it for any other type, and the
    membership test below simply returns for every status but LEASED/IN_PROGRESS.
    """
    if to_status not in LEASE_BEARING_STATUSES:
        return
    if lease_in_force(state, item_id):
        return
    raise DispatchError(
        "%s cannot be moved to %s by a direct transition: a lease-bearing status is established by "
        "a real dispatch lease, not by a status write (DEC-0038/BUG-0010). LEASED with no lease is "
        "untrue bookkeeping -- a later `sweep-leases` finds no lease to reconcile. Remedy: lease the "
        "task through the dispatch path (`python scripts/harness.py dispatch %s`), which mints the "
        "lease and moves it to LEASED." % (item_id, to_status, item_id))


def leased_without_live_lease(state: ProjectState) -> list:
    """Active tasks that read LEASED but hold no live lease -- REPORTED, never silently reset.

    After DEC-0038 a bare transition can no longer mint LEASED, so a LEASED task with no live lease
    is old state or a removed/corrupt lease. `sweep-leases` NAMES it (with the id) instead of
    throwing it back to READY: a silent reset would erase the only sign the bookkeeping was ever
    wrong, and a status the automaton calls LEASED whose lease is gone is a fact a human should see
    (BUG-0010 AC-3). Only `LEASE_MINTED_STATUS`, not the whole lease-bearing set -- an IN_PROGRESS
    task legitimately outlives its lease (see that constant), so flagging it would be noise.
    """
    flagged = []
    with state.lock:
        for stem, _path in state.iter_active_items("TSK"):
            try:
                task = state.read_item(stem)
            except StateError:
                continue
            if task.get("status") == LEASE_MINTED_STATUS and not lease_in_force(state, stem):
                flagged.append(stem)
    return sorted(flagged)


# -- session ownership: the one locally decidable form of "no agent is behind this" -------------

# WHERE THE ASK IS RECORDED. A subagent is a child of the session that asked for it and cannot
# outlive that session, so "the session that asked for this child is not the session asking now" is
# the only form of DEC-0044's "a lease whose agent the session cannot see" this kernel can decide
# without looking at a process it has no handle on. The provider hands every hook payload a
# `session_id` (measured key list in `tools/provider_observations.json`, agent_identity), which is
# what makes the term readable at all.
#
# ONE field name on TWO records, because one of them is dropped first: the LEASE carries it from the
# claim (`_open_bind_window`), the TASK from the successful spawn (`spawn_outcome`) -- and
# `sweep_expired_leases` deletes the lease after the TTL while leaving an IN_PROGRESS task standing,
# which is exactly the state BUG-0042 measured. `dispatching_session_locked` is the single reader.
DISPATCHING_SESSION = "dispatch_session"


def dispatching_session_locked(state: ProjectState, task_id: str, task: dict = None):
    """Which session asked for THIS task's current dispatch, or None when nothing recorded it.

    THE LEASE IS THE LIVE RECORD, and while one EXISTS it is the only one asked -- even when it is
    still empty. The task's copy answers only where there is no lease at all, which is precisely the
    state it was written for (`sweep_expired_leases` drops the lease and leaves IN_PROGRESS
    standing).

    THE DEFECT THAT MADE THAT ORDER A RULE INSTEAD OF A PREFERENCE, measured 2026-08-15: a fallback
    that ran whenever the lease carried no session read the LAST run's value out of the task, and
    `create_lease` mints a lease with no session (it is recorded at the CLAIM, one tool call later).
    In that window a retry dispatched by THIS session was judged foreign: a mid-session SessionStart
    -- a compaction, same id -- swept the fresh dispatch back to READY and killed the nonce sitting
    in the prompt that was being composed. `test_approvals_dispatch
    .test_a_fresh_lease_of_this_session_is_not_judged_by_the_previous_runs_record` is that chain.

    None is NOT "nobody" -- it is "undecidable here", and every caller has to treat it that way (see
    `orphaned_dispatches`). A corrupt lease answers None for the same reason.
    """
    if os.path.exists(_lease_path(state, task_id)):
        try:
            recorded = _read_lease(state, task_id).get(DISPATCHING_SESSION)
        except DispatchError:
            return None
        return str(recorded) if recorded else None
    try:
        recorded = (task if task is not None else state.read_item(task_id)).get(
            DISPATCHING_SESSION)
    except StateError:
        return None
    return str(recorded) if recorded else None


def no_progress_status(from_status: str):
    """The status the TSK automaton offers for a run that produced NOTHING, or None when it is not
    the single obvious one.

    DERIVED FROM THE EDGE SET, not a table of two rows, because a table is a claim that the
    lifecycle has exactly these two lease-bearing statuses forever. Three subtractions, each of
    which says what such a status may NOT be:
      * a TERMINAL -- a run that produced nothing did not end the task's life,
      * the CHAIN SUCCESSOR -- that edge means the run DID produce something,
      * a LEASE-BEARING status -- landing in one would re-assert the very thing being swept away.
    What the shipped automaton leaves is LEASED -> READY (the lease-timeout back-edge) and
    IN_PROGRESS -> FAILED (the run that did not deliver, which is also the edge the pilot's PM
    walked by hand -- BUG-0042). Ambiguity is refused rather than guessed: with no single answer
    left, the caller REPORTS the dispatch instead of moving it.
    `test_approvals_dispatch.test_the_no_progress_status_is_derived_from_the_automatons_edge_set`
    holds both halves.
    """
    auto = AUTOMATA["TSK"]
    if from_status not in auto.states:
        return None
    candidates = {dst for src, dst in auto.allowed if src == from_status}
    candidates -= set(auto.terminals)
    candidates -= set(LEASE_BEARING_STATUSES)
    if from_status in auto.chain and auto.chain.index(from_status) + 1 < len(auto.chain):
        candidates.discard(auto.chain[auto.chain.index(from_status) + 1])
    return candidates.pop() if len(candidates) == 1 else None


def orphaned_dispatches(state: ProjectState, session_id: str):
    """(orphaned, undecidable) for every task sitting in a lease-bearing status.

    ORPHANED means the ask is recorded and it names a session other than `session_id` -- no child of
    it can be running here, so the status is a claim nothing backs. UNDECIDABLE means the record this
    task's CURRENT dispatch answers with (`dispatching_session_locked`) names no session at all:
    state written before this record existed, a lease just minted and not yet claimed, a lease
    removed out of band. The honest answer there is "this cannot be judged", and the caller says so
    rather than sweeping on a guess. A dispatch this very session asked for is neither, which is what
    keeps a mid-session SessionStart (a compaction) from reporting a live child of its own as gone --
    and that holds for the retry it minted seconds ago only because of the reading order the reader's
    own docstring measures.

    WHAT THIS DOES NOT MEASURE, named because the answer would otherwise read stronger than it is:
    a session id that is not ours proves the ask came from ELSEWHERE, not that the asker is over.
    Two Claude Code sessions in one repo at the same time are therefore the case where "orphaned" is
    true by this definition and wrong in fact; `sweep_orphaned_dispatches` is what decides what may
    be done about that, and it is deliberately narrower than this function. The second boundary is
    the id itself: it is the provider's, and what this term needs of it -- that a session KEEPS it
    while its children live -- is not among the things `tools/provider_observations.json` records as
    measured. A provider that issued a fresh id to a continuing session would look, from here,
    exactly like a session that ended.
    """
    orphaned, undecidable = [], []
    with state.lock:
        for stem, _path in state.iter_active_items("TSK"):
            try:
                task = state.read_item(stem)
            except StateError:
                continue
            status = task.get("status")
            if status not in LEASE_BEARING_STATUSES:
                continue
            asked_by = dispatching_session_locked(state, stem, task)
            record = {"task_id": stem, "status": status, "asked_by": asked_by,
                      "lease_in_force": lease_in_force(state, stem)}
            if asked_by is None:
                undecidable.append(record)
            elif asked_by != str(session_id or ""):
                orphaned.append(record)
    by_id = operator.itemgetter("task_id")          # one sort key, two lists
    return sorted(orphaned, key=by_id), sorted(undecidable, key=by_id)


def sweep_orphaned_dispatches(state: ProjectState, session_id: str):
    """(swept, left) -- return every orphaned dispatch to an honest status at session start.

    DEC-0044 half (1): nothing pretends to run. The status moves through `state.transition`, i.e.
    along an edge the TSK automaton names (`no_progress_status`), so the sweep cannot write a status
    the lifecycle does not offer, and the transition drops the lease on its way out
    (`release_lease_for_status_locked`). An IN_PROGRESS dispatch therefore lands in FAILED and its
    retry is the user's approved one (`state.RETRY_APPROVAL_EDGE`) -- which is the moment DEC-0044
    puts the checkpoint verdict in front of a human.

    `left` carries every dispatch this did NOT move, with the reason, and it is not a leftover: the
    undecidable ones and any whose transition the automaton refuses have to reach the session as
    facts, or the sweep's silence would read as "there was nothing".

    THE RESIDUE THIS DOES NOT CLOSE, measured against the shipped surface rather than assumed: a
    SECOND live session in the same repo owns dispatches this session cannot see either, and they
    are indistinguishable here from those of a session that ended. What bounds the damage is that
    the sweep only ever moves a task to a status a human then has to act on -- READY (re-leasable)
    or FAILED (whose way back needs the user's approved retry) -- and never touches an agent binding
    that is still resolvable: `task_for_agent` reads the LEASE, and by the time this has run the
    lease is gone, so a still-running foreign child is refused by gate layer 3 exactly as it already
    is today once its lease expires (`test_approvals_dispatch
    .test_a_swept_orphan_keeps_no_lease_and_no_agent_binding`).
    """
    orphaned, undecidable = orphaned_dispatches(state, session_id)
    swept, left = [], list(undecidable)
    for record in orphaned:
        target = no_progress_status(record["status"])
        if target is None:
            left.append(dict(record, why="the TSK automaton offers no single no-progress edge out "
                                         "of %s -- refusing to guess one" % record["status"]))
            continue
        try:
            state.transition(record["task_id"], target)
        except StateError as exc:
            left.append(dict(record, why="the transition to %s was refused (%s)" % (target, exc)))
            continue
        swept.append(dict(record, moved_to=target))
    for record in left:
        record.setdefault("why", "no dispatching session is recorded for it, so whether a child was "
                                 "ever asked for by another session cannot be decided here")
    return swept, left


# -- the dispatch nobody is working on any more (BUG-0058) --------------------------------------

# WHERE THE END OF A CHILD IS RECORDED, and it is the TASK for the reason DISPATCHING_SESSION also
# rides on it: the lease is the record that goes away FIRST (`sweep_expired_leases` drops it while
# leaving an IN_PROGRESS task standing), while this fact is read at the end of a LATER turn --
# arbitrarily long after the child stopped. `create_lease` clears it, because a new lease is a new
# dispatch and the previous run's child says nothing about this one.
CHILD_ENDED = "child_ended"

# WHAT THE LEAD WAS LAST TOLD about this dispatch: the sentence itself, not a counter and not a
# digest. `idle_dispatches` composes it and `mark_idle_reported` compares against it, so the
# surfacing speaks at most once per FINDING rather than once per turn -- and again the moment the
# finding changes. Kept readable in the item on purpose: a task file that says what was surfaced
# needs no second store to explain a refusal somebody met an hour ago. ONE STRING and not the list
# of reasons, because a list on an item is a shape other readers have a rule about
# (`backlog_types.REFERENCE_LIST_FIELDS`, and BUG-0038 is what a scalar read as a sequence costs);
# what is stored here holds prose and no references, so it stays a scalar.
IDLE_REPORTED = "idle_reported"


def _lease_bearing_dispatches_locked(state: ProjectState):
    """(task_id, task, lease) for every lease whose task still stands in a lease-bearing status.

    The caller holds the lock. Everything that asks "which dispatch does this belong to" starts
    here and narrows from it, so the narrowing terms stay visible at their own call site instead of
    being baked into the walk.
    """
    for lease in _iter_leases(state):
        task_id = str(lease["task_id"])
        try:
            task = state.read_item(task_id)
        except StateError:
            continue
        if task.get("status") in LEASE_BEARING_STATUSES:
            yield task_id, task, lease


def _dispatches_a_stop_could_belong_to(state: ProjectState):
    """The dispatches whose child could be the one that just stopped. The caller holds the lock.

    ONE narrowing, and it is the only thing that can be said with certainty about a stop: a
    dispatch whose child's end is ALREADY RECORDED cannot be the owner of a NEW one. Everything
    else stays in -- an UNBOUND dispatch belongs here because its child is precisely the one no
    record can identify, and an EXPIRED lease belongs here because a child may outlive its lease
    (`LEASE_MINTED_STATUS`), so its window running out says nothing about whether its child is the
    one that stopped.

    Both were measured rather than reasoned into place. Without the recorded-end term the corpse of
    pilot 4 stays a possible owner for every later stop of the same role forever, and the ambiguity
    refusal in `record_child_end` then turns the whole mechanism off for that role
    (`test_a_dispatch_whose_end_is_recorded_stops_competing_for_the_next_stop`). With an EXPIRY
    term added on top -- the shape a review proposed against exactly that poison -- a stop of a
    long-running child lands on the fresh same-role dispatch beside it, which is the misattribution
    this whole function exists to avoid
    (`test_a_long_running_dispatch_still_counts_as_a_possible_owner_of_a_role_matched_stop`).
    """
    for task_id, task, lease in _lease_bearing_dispatches_locked(state):
        if not task.get(CHILD_ENDED):
            yield task_id, task, lease


def record_child_end(state: ProjectState, agent_id: str = None, agent_type: str = None):
    """Record that a dispatch's child has STOPPED; returns the task id, or None when this stop
    belongs to no dispatch this kernel can name.

    WHY IT IS WRITTEN DOWN AT ALL: the end of a child is an EVENT, and the party that has to know
    about it -- the lead, at the end of one of its own later turns -- is not the party the event is
    delivered to. Without a record, "is anything still working on this task?" is a question no
    reader can answer, which is the state pilot 4 measured (BUG-0058; see `idle_dispatches`).

    TWO ATTRIBUTIONS, AND THEY ARE NOT THE SAME KIND OF ANSWER:
      * `agent_id` is an IDENTITY. The lease that names it IS this child's dispatch; nothing is
        matched and nothing is guessed.
      * the ROLE is a GUESS, taken only when the payload carries no id, and it is made ONLY when
        exactly one dispatch of that role could be the owner at all -- counting every one this
        kernel cannot rule out (`_dispatches_a_stop_could_belong_to`), the UNBOUND ones included.
        An unbound dispatch's child is exactly the one no record can identify, so leaving it out of
        the count is what wrote the stop of an unbound child onto a RUNNING same-role dispatch
        beside it -- measured, and the counter-direction is
        `test_a_stop_with_no_id_is_refused_while_an_unbound_dispatch_of_the_role_could_own_it`.
        Where the single possible owner is itself unbound, there is nothing to record: no record
        ties that child to that dispatch, and writing one would be the same guess in one step.

    Zero candidates is None and not an error: every subagent stop reaches this, including those of
    helpers the harness never dispatched, and including a second stop of a child whose end is
    already recorded.

    WHAT IT CANNOT SEE: a child whose lease is already GONE (the TTL sweep drops it while the task
    stays IN_PROGRESS) has no `agent_id` mapping left, so its end is unattributable here -- and
    `idle_dispatches` does not carry that case either, since a running child is indistinguishable
    from a dead one once every record of it is gone. It is a hole with a name, not a covered case.
    """
    with state.lock:
        possible = list(_dispatches_a_stop_could_belong_to(state))
        if agent_id:
            candidates = [row for row in possible
                          if str(row[2].get("agent_id")) == str(agent_id)]
        elif agent_type:
            owners = [row for row in possible
                      if str(row[1].get("assigned_role")) == str(agent_type)]
            if len(owners) > 1:
                raise AmbiguousBinding(
                    "%d dispatches of the role %r could own this stop (%s) and it carries no "
                    "agent_id -- refusing to guess which of them ended, because recording the end "
                    "against the wrong task reports a specialist that is still working as idle. "
                    "Remedy: dispatch tasks of the SAME role sequentially; different roles in "
                    "parallel are unaffected."
                    % (len(owners), agent_type, ", ".join(sorted(row[0] for row in owners))))
            candidates = [row for row in owners if row[2].get("agent_id")]
        else:
            candidates = []
        if not candidates:
            return None
        task_id, task, _lease = candidates[0]
        task[CHILD_ENDED] = _now_iso()
        state._write_yaml_atomic(state.active_path(task_id), task)
        state._regenerate_index_locked()      # see `mark_idle_reported` -- a task is a board card
        return task_id


def _window_ran_out_with_no_child(state: ProjectState, task_id: str) -> bool:
    """Is there a lease for this task that names no child and whose window has passed?

    The caller holds the lock. All three terms are read off the ONE record that can carry them, and
    a MISSING lease answers False on purpose: once the TTL sweep has taken the lease away, whether
    a child was ever bound is not a question this kernel can still answer, and False is what "we
    cannot say" has to mean for a term that produces a refusal.
    """
    if not os.path.exists(_lease_path(state, task_id)):
        return False
    try:
        lease = _read_lease(state, task_id)
    except DispatchError:
        return False
    return not lease.get("agent_id") and _expired(lease)


def staged_progress(state: ProjectState, task_id: str) -> str:
    """One sentence about what this dispatch has PUT ON DISK, measured rather than assumed.

    The top level of the task's staging directory, which is the one place a dispatched specialist
    may write with its own tools (spec II.4) -- so "nothing there" is the same observation the
    pilot made by hand about the run that produced no file. A COUNT and no judgement: whether what
    is there carries the work forward is what `checkpoint-status` answers, and every message built
    on this points at that command instead of pretending to have asked it.
    """
    directory = os.path.join(state.staging_root(), task_id)
    where = os.path.relpath(directory, state.root).replace(os.sep, "/")
    try:
        entries = os.listdir(ext_path(directory))
    except OSError:
        return "nothing was staged for it (%s does not exist)" % where
    if not entries:
        return "nothing was staged for it (%s is empty)" % where
    return "%d entr%s under %s" % (len(entries), "y" if len(entries) == 1 else "ies", where)


def idle_dispatches(state: ProjectState) -> list:
    """Every dispatch this kernel has a RECORD saying no child is on it, with what it staged.

    THE FAILURE THIS MAKES VISIBLE, measured in pilot 4 half 2 (BUG-0058, P4-2 in
    docs/pilot/2026-08-22-pilot-4-befunde.md): a dispatched specialist made two tool calls,
    produced no file and stopped; the lead then answered NINE consecutive user turns with waiting
    phrases and made not one follow-up call, while the task sat in IN_PROGRESS with a live lease
    and an empty staging directory. Nothing asked whether anything was still behind that status.

    WHAT A FINDING IS -- a POSITIVE record, never the absence of one, and the difference is the
    whole correction this function has behind it:
      * its child's end is recorded (`CHILD_ENDED`, written at that child's SubagentStop), or
      * NOTHING WAS EVER BOUND to it and its dispatch window has run out: the lease is still there,
        it names no `agent_id`, and its TTL has passed. Nobody was ever tracking a run on it.
    A task in a lease-bearing status that matches neither is silent here.

    THE TERM THAT IS DELIBERATELY ABSENT, because it was WRONG and its chain ran to work loss: "no
    lease in force" on its own. A running child may legitimately outlive its lease -- that is a
    documented property of this lifecycle, stated at `LEASE_MINTED_STATUS` -- so that term reported
    specialists that were still working; measured, and the remedy it carried (take the task to the
    no-progress status) would have unbound a live child and made its `submit-result` refusable.
    `test_a_bound_child_that_outlived_its_lease_is_not_reported_as_idle` is the counter-direction,
    and it goes red the moment the term comes back.

    A finding is REPORTED, never moved: what to do about it is the lead's judgement (book a
    handed-back envelope, adopt a checkpoint, or take the task onto the automaton's no-progress
    edge), and a kernel that decided it would be guessing at work it cannot see. `no_progress_status`
    rides along so the reader that prints this does not have to name a status the automaton might
    not offer.

    WHAT THIS DOES NOT SEE, and both are holes with names rather than covered cases: a BOUND child
    whose SubagentStop never arrives is indistinguishable here from one that is still working, for
    as long as the task stands; and once the TTL sweep has removed the lease of such a task, no
    record of it is left at all. What this DOES report about a run nobody stopped is the unbound
    case above -- and an unbound child, if one is running, is one gate layer 3 refuses every write
    from, so what is reported there is a dispatch that can produce nothing either way.
    """
    findings = []
    with state.lock:
        for stem, _path in state.iter_active_items("TSK"):
            try:
                task = state.read_item(stem)
            except StateError:
                continue
            status = task.get("status")
            if status not in LEASE_BEARING_STATUSES:
                continue
            reasons = []
            ended = task.get(CHILD_ENDED)
            if ended:
                reasons.append("its child stopped at %s and no result was booked" % ended)
            if _window_ran_out_with_no_child(state, stem):
                reasons.append("no child was ever bound to it and its dispatch window of %d s has "
                               "run out, so nothing here was ever tracking a run on it"
                               % DEFAULT_LEASE_TTL)
            if not reasons:
                continue
            findings.append({"task_id": stem,
                             "status": status,
                             "assigned_role": task.get("assigned_role"),
                             "reasons": reasons,
                             # THE FINDING AS ONE SENTENCE, composed once: `mark_idle_reported`
                             # compares this against what was last said and the reader that prints
                             # it prints this, so "the same finding" cannot come to mean two
                             # things -- which is what deciding it twice would eventually buy.
                             "why": "; ".join(reasons),
                             "no_progress_status": no_progress_status(status),
                             "staged": staged_progress(state, stem)})
    return sorted(findings, key=operator.itemgetter("task_id"))


def mark_idle_reported(state: ProjectState, finding: dict) -> bool:
    """Record that the lead was told THIS finding; True when it had not been told this one before.

    THE BOUND ON A REFUSAL THAT WOULD OTHERWISE REPEAT ITSELF. The caller refuses the end of a turn
    (`gate_dispatch.handle_stop`), and the assistant answers a refused stop by CONTINUING -- so a
    condition that survives being reported would refuse the next stop of the same continuation, and
    the one after that. What is compared is the REASONS: unchanged means the lead has already been
    handed this exact fact and a second refusal adds nothing; changed means something happened
    since -- a child bound late to a dispatch that had already been reported as never having had
    one, and then stopping, is the reachable case
    (`test_an_idle_finding_is_reported_once_and_again_only_when_it_changes`).

    This is the kernel-side bound and it is deliberately not the only one -- the caller also stands
    down for a stop the provider marks as one a stop hook already blocked. Two bounds because the
    second is the provider's word and this one is the harness's own; only this one is measured
    here, which is why no text in the kits promises that the refusal arrives, only that it does not
    repeat.
    """
    task_id = finding["task_id"]
    said = finding["why"]
    with state.lock:
        try:
            task = state.read_item(task_id)
        except StateError:
            return False
        if str(task.get(IDLE_REPORTED) or "") == said:
            return False
        task[IDLE_REPORTED] = said
        state._write_yaml_atomic(state.active_path(task_id), task)
        # THE RECORD LANDS ON THE TASK, and a task is a card on the board, so an unregenerated
        # write leaves the board showing the item as it was before it. The rule and its two
        # measured defects are in
        # `test_board.test_no_kernel_writer_of_a_rendered_file_leaves_the_board_behind`.
        state._regenerate_index_locked()
        return True


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
    check that only understood one of them would block the other.

    The FIELD itself is normalised through `backlog_types.field_elements` for the same reason
    (BUG-0015): a scalar `acceptance_criteria: AC-1` split into four one-letter criterion ids,
    and against a scalar `acceptance_refs` that split the same way the dispatch check passed on
    criteria nobody wrote."""
    ids = set()
    for field in CRITERIA_FIELDS:
        for entry in field_elements(item.get(field)):
            if isinstance(entry, dict) and entry.get("id"):
                ids.add(str(entry["id"]))
            elif isinstance(entry, str) and entry.strip():
                ids.add(entry)
    return ids


def _binds_to(item_type: str, item: dict, target_id: str) -> bool:
    """Does this item hang DIRECTLY from `target_id`, through a field its own contract binds with?

    A predicate over `backlog_types.PARENT_FIELDS`, which is where the fact "these field names
    carry a binding" is decided; `report._parent_bindings` is the other reader of that same map,
    for the walk that needs the pairs rather than a yes/no. Direct rather than transitive on
    purpose -- an amendment names its target itself, and the narrower question is the safe one for
    a check that WIDENS what dispatches.
    """
    return any(str(one) == target_id
               for field in PARENT_FIELDS.get(item_type, ())
               for one in field_elements(item.get(field)))


def _approval_covers_criteria(item: dict, kind: str) -> bool:
    """Does an approval of this KIND hash the very criteria we are about to trust?

    THE QUESTION THIS ANSWERS, and why it is not "is the kind `scope`": `assert_apr_in_force`
    verifies a content hash only for the item-derived kinds, and even among those only the SCOPE
    manifest carries `acceptance_criteria` (`approvals._SCOPE_FIELDS`; the acceptance and delivery
    manifests name delivered commits and task lists instead). An `analysis` or `routine` approval
    is not item-derived at all and `item_subject_manifest` refuses to build one.

    So the reachable hole this closes is a real interaction and not a hypothetical: `mint` writes
    `approval_ref` for EVERY item-bound approval (see `_covering_routine_apr`, which documents the
    same overwrite for roots), so a routine approval minted on an already-APPROVED amendment leaves
    `status: APPROVED` standing beside an `approval_ref` whose kind hashes nothing -- and an
    out-of-band edit of the criteria would then widen the universe unchallenged. Asking the
    MANIFEST instead of naming a kind means a kind added to `APPROVAL_TRANSITIONS` later is judged
    by what it actually covers.

    THE RETURN LINE IS THE WHOLE PROTECTION FOR ONE FIELD, so it is named rather than left to be
    inferred: `success_criteria` is read by `_criteria_ids` and is NOT in `approvals._SCOPE_FIELDS`.
    Measured 2026-08-15 -- an out-of-band `success_criteria: [{id: AC-77}]` added to an APPROVED CR
    leaves the scope hash MATCHING (so `assert_apr_in_force` says nothing), and this comparison is
    the only thing between that and a dispatchable criterion nobody signed. It is per FIELD and not
    per item for exactly that reason. `test_approvals_dispatch
    .test_a_criterion_smuggled_into_a_field_the_approval_does_not_sign_does_not_widen` is its red
    test; the line has no other one.
    """
    try:
        manifest = item_subject_manifest(item, kind)
    except ApprovalError:
        return False  # not item-derived -- it signs no content of this item at all
    return all(field in manifest for field in CRITERIA_FIELDS if field in item)


def _amendment_criteria_locked(state: ProjectState, root: dict):
    """(criterion ids, {amendment id: why it does not count}) for the amendments of one root.

    THE DERIVATION: an amendment's criteria are part of the root's contract when the USER approved
    that amendment's content -- the same authority the root's own criteria rest on, which
    `_assert_dispatch_authorised_locked` has already demanded one frame up. Four terms, each read
    from the store that owns it:
      * it IS an amendment -- `backlog_types.AMENDMENT_TYPES`, the types that name the revision
        they amend;
      * it amends THIS root -- `_binds_to`, over the reference graph's own binding fields;
      * it still STANDS in a status a user's approval put it in -- `approvals.approved_statuses`,
        derived from the type's automaton, which is what keeps a REJECTED amendment out (its
        `approval_ref` survives the rejection) and an APPLIED one too;
      * its approval is IN FORCE and SIGNS THE CRITERIA -- `assert_apr_in_force` plus
        `_approval_covers_criteria`.
    Nothing here enumerates a type, a status or a kind, so the day a kit ships a second amendment
    type it arrives already resolved -- the property is held from both ends by
    `test_backlog_types.test_an_amendment_is_the_type_that_names_the_revision_it_amends`.

    WHAT THE SIGNATURE COVERS, AND WHAT IT DOES NOT -- said plainly, because "the user approved it"
    is true of the CONTENT and not of the MEMBERSHIP. The scope manifest hashes the criteria
    (`approvals._SCOPE_FIELDS`, which concedes the same narrowness at its own definition), and it
    does NOT hash `target_pr` -- so which root an amendment belongs to is not part of what anybody
    signed. Through the kernel that is closed: an edit of `target_pr` is a `HASHED_FIELDS` change,
    which bumps the revision and drops the approval. PAST the kernel it is open: a hand-edited
    `target_pr` re-aims a still-valid approval's criteria into another root's universe, and this
    reader cannot tell. Widening the manifest would kill every live approval, so it is a spec
    decision with a migration and not something to slip in here. Authorisation is untouched either
    way -- that comes from the ROOT's own approval, one frame up.

    WHERE THIS DERIVATION STOPS, and it is a residue rather than a safe edge: an amendment that
    reached its terminal `APPLIED` contributes nothing, and once archived it is not even read --
    so a LATER task against a criterion that CR minted is refused again, BUG-0040 one lifecycle
    step further on. Not widened here because `approved_statuses` answers `{APPROVED}` for CR by
    the same argument that keeps `RETIRED` out for PROC, and overriding a derivation with a special
    case is the shape this whole item is fixing. The behaviour is asserted, not promised, by
    `test_approvals_dispatch.test_an_applied_amendments_criteria_stop_counting`, so widening it
    later is a decision somebody has to take rather than a silent drift.

    The second element is what makes the refusal honest: an amendment whose criteria do NOT count
    is invisible in the item files (they read `AC-11` plainly), so the reason travels with the
    refusal instead of leaving the user to compare hashes by hand -- the failure BUG-0039 is about.
    """
    known, excluded = set(), {}
    for item_type in sorted(AMENDMENT_TYPES):
        for _stem, path in state.iter_active_items(item_type):
            try:
                item = state._read_yaml(path)
            except Exception as exc:  # noqa: BLE001 -- an unreadable amendment approves nothing
                # criteria None: unreadable means we cannot say WHICH criteria were lost, so this
                # one is named in every refusal rather than only in the ones it could explain
                excluded[os.path.basename(path)] = (None, "unreadable (%r)" % (exc,))
                continue
            if not isinstance(item, dict) or not item.get("id"):
                continue
            if not _binds_to(item_type, item, root["id"]):
                continue
            reason = _amendment_refusal(state, item, item_type)
            if reason is None:
                known |= _criteria_ids(item)
            else:
                excluded[str(item["id"])] = (_criteria_ids(item), reason)
    return known, excluded


def _amendment_hint(unknown, excluded: dict) -> str:
    """The half of the refusal that names WHY a criterion the user can READ is not in the universe.

    Only the amendments that could explain THIS refusal -- one that offers an unrecognised
    reference, or one nobody could read. Naming every excluded amendment would bury the one that
    matters under the rest of the backlog, and a reference no amendment offers is exactly the
    "exists nowhere" case this must not dress up as an approval problem.

    Without it the user meets the pilot's own confusion one level deeper: `CR-0001.yaml` says
    `AC-11` in plain sight while the gate says it exists nowhere, and the difference is a hash
    nobody can see. BUG-0039 is that failure mode in the approval texts.
    """
    if not unknown:
        return ""   # the refusal is "no acceptance_refs at all" -- no amendment explains that
    named = []
    for item_id, (criteria, reason) in sorted(excluded.items()):
        if criteria is None or criteria & set(unknown):
            named.append("%s (%s)" % (item_id, reason))
    if not named:
        return ""
    return (" Amendments of the root that could hold a missing reference, and why their criteria "
            "do not count: %s." % "; ".join(named))


def _amendment_refusal(state: ProjectState, item: dict, item_type: str):
    """Why this amendment of the root contributes no criteria, or None when it does."""
    status = item.get("status")
    if status not in approved_statuses(item_type):
        return "status %r is not a status a user's approval put it in" % status
    apr_ref = item.get("approval_ref")
    if not apr_ref:
        return "it carries no approval_ref"
    try:
        apr = read_apr(state, apr_ref)
        assert_apr_in_force(state, apr, item)
    except Exception as exc:  # noqa: BLE001 -- see below
        # BROAD ON PURPOSE, and the direction is what makes it safe: every answer this branch can
        # give NARROWS the universe, so an unforeseen failure costs a refusal a reader can see and
        # never a criterion a reader cannot. `read_apr` translates a missing file, but a corrupt
        # approval YAML or an unreadable consumed request arrives as neither StateError nor
        # ApprovalError -- and reaching the hook as an internal error would report "the harness is
        # broken" about an amendment that simply does not vouch for anything.
        return str(exc) or repr(exc)
    if not _approval_covers_criteria(item, apr.get("kind")):
        return ("its approval %s is of kind %r, whose subject manifest does not carry the "
                "criteria -- nothing signed them" % (apr_ref, apr.get("kind")))
    return None


def _known_acceptance_ids_locked(state: ProjectState, root: dict, task: dict):
    """(criterion ids a task may reference, why an amendment's were left out).

    Two hops, and they are strict in DIFFERENT ways because the items behind them differ:

    1. `derives_from`, a required TSK field naming the contract the task actually serves -- a
       bugfix task referencing the PR's AC instead of the BUG's Fix-Kriterien would be referencing
       the wrong contract entirely. This hop asks only that the origin RESOLVES. It carries no
       status and no approval term, and that is a DESIGN CHOICE with a measured reason rather than
       an oversight: a `BUG` cannot reach `APPROVED` in a repo whose approval mint is unreachable
       (H39), while the kits' own bugfix flow cuts tasks against a TRIAGED bug's Fix-Kriterien. A
       status term here would make that flow undispatchable. So the looseness is real and it is
       bounded by what it lends: the criteria of an item the PLANNER named, under a root whose own
       approval already authorised the dispatch one frame up.
       `test_approvals_dispatch.test_a_bugfix_task_may_reference_a_triaged_bugs_fix_criteria`
       holds that direction open.
    2. THE AMENDMENT HOP, which needs no `derives_from` at all, because an approved amendment
       changes the ROOT's contract rather than offering one of its own. BUG-0040 carries the field
       observation and names the audit chain it was measured on: a live project's approved change
       requests minted criteria that this gate then called nonexistent, and the task was cancelled
       for it. Re-cutting that task against ONE of the change requests would have bought its
       criteria and lost the rest, which is why the fix is a derivation over the root rather than a
       second hop.

    AND AN AMENDMENT MAY ONLY ENTER THROUGH HOP 2 -- the `continue` below. Without it hop 1 was the
    way around hop 2's whole point: `derives_from: CR-0001` on a DRAFT, never-approved CR lent
    `AC-11` and the spawn PASSED (measured 2026-08-15), so the amendment path's approval term could
    be walked past by naming the same item one field over. The exclusion reads `AMENDMENT_TYPES`,
    the same derivation hop 2 selects with, so the two halves cannot come apart.
    `test_approvals_dispatch.test_an_unapproved_amendment_named_in_derives_from_lends_nothing`
    is the red side of it.
    """
    known = _criteria_ids(root)
    for origin in field_elements(task.get("derives_from")):
        if not origin or str(origin) == root["id"]:
            continue
        try:
            origin_type, _number = parse_id(str(origin))
        except ValueError:
            continue  # free-text provenance note, not an item reference
        if origin_type in AMENDMENT_TYPES:
            continue  # an amendment's criteria are approval-gated -- hop 2 or nothing
        item, _archived = _read_item_any(state, str(origin))
        if item:
            known |= _criteria_ids(item)
    amended, excluded = _amendment_criteria_locked(state, root)
    return known | amended, excluded


def _assert_dependencies_met_locked(state: ProjectState, task: dict) -> None:
    """spec II.4 gate 2 / II.12 "offene Abhaengigkeit -> Block". A dependency is
    satisfied once its work was accepted (DONE) or QA'd (VALIDATED)."""
    open_deps = []
    for dep_id in field_elements(task.get("dependencies")):
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


def _release_lease_locked(state: ProjectState, task_id: str, to_ready: bool) -> bool:
    """Drop the lease; True when the TASK's status was reset too, False when only the lease went.

    The return value is what keeps `sweep_expired_leases` honest -- see the two lists there.
    """
    _remove_lease(state, task_id)
    task = state.read_item(task_id)
    if to_ready and task.get("status") == LEASE_MINTED_STATUS:
        task["status"] = "READY"
        state._write_yaml_atomic(state.active_path(task_id), task)
        return True
    return False
