#!/usr/bin/env python3
"""
Dispatch gate — gate layer 2 of spec II.4. Registered on FIVE events, because the dispatch
lifecycle is one story and splitting it across files would let the halves drift:

  PreToolUse(Agent|Task)        validate the HARNESS_DISPATCH header against the lease, CONSUME
                                the lease for this one dispatch, and open the bind window
  SubagentStart(*)              claim that lease for the child's agent_id (gate layer 3 needs the
                                agent_id -> task mapping while the child is still running)
  PostToolUse(Agent|Task)       the spawn STARTED: re-verify the header, bind the agent_id
                                authoritatively (here the header and the agentId arrive
                                together), and move the task to IN_PROGRESS
  PostToolUseFailure(Agent|Task),
  PermissionDenied(Agent|Task)  the spawn did NOT start: return the task to READY at once and
                                close the bind window

WHAT THIS GATE PARSES: the header, and only the header (spec II.4). Free prompt prose is never
evidence of anything — the V1 `guard_agent_spawn` keyword check is exactly the "looks approved"
failure this replaces. A spawn without a header is refused; a spawn whose header names a task
that is not leased to it is refused.

WHICH EVENTS CAN ACTUALLY REFUSE (hooks reference, exit-code-2 table — this decides the whole
design, so it is written down rather than assumed): PreToolUse blocks. PostToolUse,
PostToolUseFailure and SubagentStart do NOT — their stderr is shown and the action stands;
PermissionDenied ignores the exit code entirely. So PREVENTION lives in PreToolUse alone. In the
later events this gate protects the only thing it still can: it REFUSES TO MUTATE STATE on
anything it cannot verify, and says so on stderr. Calling that a "block" would be theatre, and
theatre is what V2 is removing.

THE PLATFORM LIMIT, stated plainly: SubagentStart carries `agent_id`, `agent_type` and
`prompt_id`, but no key back to the tool call that started it — no tool_use_id, no prompt
(verified against the S3 spike payloads and the hooks reference). So the child is matched to its
lease by ROLE, within a window narrowed by `prompt_id`. Two concurrent dispatches of the SAME
role inside ONE turn stay ambiguous, and the kernel refuses to guess rather than binding one
specialist's writes to another's allowed_scope. Consequence, honestly: such a child starts
UNBOUND (SubagentStart cannot stop it) and the write-scope gate refuses its writes. Different
roles in parallel are unaffected.

The GATE_PREAMBLE below must stay the first executable statement — see _kernel.py for why. Only
the docstring may precede it, because a docstring cannot fail.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _kernel
except BaseException as exc:  # noqa: BLE001 — a hook that cannot load must not mean "allow"
    sys.stderr.write("[team-kit hook] refused: could not load hook helpers (%r). Remedy: run "
                     "`python scripts/harness.py doctor`; a partial checkout or half-finished kit update is the "
                     "usual cause.\n" % (exc,))
    sys.exit(2)

HOOK = "gate_dispatch"
SPAWN_TOOLS = ("Agent", "Task")
# A spawn SUCCEEDED when the child was launched — not when it finished. Measured on Claude Code
# 2.1.219: a synchronous spawn reports status "completed", while `run_in_background: true` (the
# platform's own default, which a real run hit 37/37 times by omission) reports "async_launched"
# with isAsync: true. Treating anything-but-"completed" as failure sent every background
# specialist's task back to READY while the child was still running: unbound, so every write
# refused, and the freed task immediately re-leasable — breaking the very "second claim blocked"
# rule this gate enforces. Real failure arrives as PostToolUseFailure/PermissionDenied instead.
STARTED_STATUSES = ("completed", "async_launched")


def _state_for_prevention(data):
    """The project state, or a BLOCK. Only for PreToolUse, the one event that can refuse."""
    root = _kernel.find_repo_root(data.get("cwd"))
    if not os.path.isdir(_kernel.state_dir(root)):
        if _kernel.bootstrap_active(root):
            return None  # explicit installer/migration window (spec II.4)
        _kernel.block(
            HOOK,
            "no canonical project state — refusing to authorise a specialist spawn against a "
            "state that does not exist (spec II.4 fail-closed; the V1 gate let spawns through "
            "on an empty store, which is the hole this closes).",
            event="PreToolUse",
            remedy="initialise the project via the installer/scaffold, the only path that may "
                   "run with an empty state.")
    return _kernel.open_state(root)


def _state_for_recording(data):
    """The project state, or None. For the events that can only RECORD, never refuse — with no
    state there is nothing to record, and a refusal they cannot enforce would be noise."""
    root = _kernel.find_repo_root(data.get("cwd"))
    if not os.path.isdir(_kernel.state_dir(root)):
        return None
    return _kernel.open_state(root)


def handle_pre_tool_use(data):
    if data.get("tool_name") not in SPAWN_TOOLS:
        sys.exit(0)
    state = _state_for_prevention(data)
    if state is None:
        sys.exit(0)
    dispatch = _kernel.kernel_module("dispatch")
    tool_input = data.get("tool_input") or {}
    try:
        header = dispatch.parse_header(str(tool_input.get("prompt") or ""))
        dispatch.validate_dispatch(state, header, tool_input.get("subagent_type"), claim=True)
        dispatch.mark_awaiting_bind(state, header["task_id"], data.get("prompt_id"))
    except dispatch.DispatchError as exc:
        _kernel.block(HOOK, "specialist spawn refused.\n%s" % exc, event="PreToolUse")
    sys.exit(0)


def _report(message):
    """Say something on an event that cannot refuse, and audit it.

    Deliberately not `_kernel.block`: exit 2 does not block PostToolUse, PostToolUseFailure or
    SubagentStart, so exiting 2 there would dress a notification up as enforcement. The real
    protection on those events is that we DID NOT MUTATE state.
    """
    _kernel.record_note(HOOK, message)
    sys.stderr.write("[team-kit %s] %s\n" % (HOOK, message))
    sys.exit(0)


def handle_subagent_start(data):
    """Claim the pending lease for this child (spec II.4: lease -> agent_id).

    A subagent with no pending dispatch is not an error here. SubagentStart fires for every
    subagent, and gate layers 1+2 already refused the ones that had no business starting; a
    complaint here would only catch subagents the harness never dispatched while breaking every
    legitimate un-dispatched helper. Such a child simply stays UNBOUND — and gate layer 3
    refuses writes from an unbound agent, which is the part that actually holds.
    """
    state = _state_for_recording(data)
    if state is None:
        sys.exit(0)
    dispatch = _kernel.kernel_module("dispatch")
    try:
        dispatch.bind_agent_by_role(state, data.get("agent_id"), data.get("agent_type"),
                                    data.get("prompt_id"))
    except dispatch.NoPendingDispatch:
        sys.exit(0)
    except dispatch.DispatchError as exc:
        _report("this subagent was NOT bound to a task, so the write-scope gate will refuse its "
                "writes.\n%s" % exc)
    sys.exit(0)


def _verified_header(data, state, dispatch, event, require_role=True):
    """The header of a spawn, verified to BELONG to the lease it names — or no mutation.

    `tool_input.prompt` is model-controlled text, and this event cannot block. Taking the task id
    on faith would let an unvalidated spawn collect a VALID agent binding (i.e. gate layer 3
    would hand it that task's allowed_scope) whenever PreToolUse did not get to refuse — a hook
    timeout, or a settings.json whose PostToolUse matcher is wider than its PreToolUse one.

    `require_role=False` on the rollback paths only: binding an agent is a GRANT and must be
    fully identified, while returning a task to READY takes permission away, so refusing that over
    a missing payload field would strand the task for no safety gain.

    IDENTITY only (nonce, root revision, role) — not authorisation. See
    `dispatch.verify_dispatch_identity`: re-asking "is this still approved?" here would freeze a
    task whose approval was revoked mid-flight, in the exact case where recording the outcome
    matters most.
    """
    tool_input = data.get("tool_input") or {}
    try:
        header = dispatch.parse_header(str(tool_input.get("prompt") or ""))
    except dispatch.DispatchError:
        return None  # not a dispatched spawn — nothing of ours to record
    try:
        dispatch.verify_dispatch_identity(state, header, tool_input.get("subagent_type"),
                                          require_role=require_role)
    except dispatch.DispatchError as exc:
        _report("refusing to record an outcome for %s on %s: the spawn's header does not check "
                "out, so state is left untouched.\n%s" % (header["task_id"], event, exc))
    return header


def handle_post_tool_use(data):
    """The spawn STARTED: bind the child authoritatively and move the task to IN_PROGRESS.

    This is the only place where the dispatch header and the child's agentId are both present
    (spike S3), so the role-matched binding from SubagentStart is confirmed here even when it was
    right — cheap, and it makes the audit record independent of the ambiguous path.
    """
    if data.get("tool_name") not in SPAWN_TOOLS:
        sys.exit(0)
    state = _state_for_recording(data)
    if state is None:
        sys.exit(0)
    dispatch = _kernel.kernel_module("dispatch")
    header = _verified_header(data, state, dispatch, "PostToolUse")
    if header is None:
        sys.exit(0)
    response = data.get("tool_response")
    response = response if isinstance(response, dict) else {}
    agent_id = response.get("agentId")
    started = str(response.get("status") or "").lower() in STARTED_STATUSES
    try:
        if not started:
            # PostToolUse means the tool call SUCCEEDED, so an unrecognised status is a platform
            # shape we have not measured. Leave the task LEASED and say so: guessing "failed"
            # would free a task whose child may be running, guessing "started" would mark a task
            # in progress that may not be. The TTL sweep is the backstop.
            _report("spawn of %s reported an unrecognised status %r — leaving the task LEASED "
                    "rather than guessing. It returns to READY on lease timeout."
                    % (header["task_id"], response.get("status")))
        if agent_id:
            dispatch.bind_agent(state, header["task_id"], agent_id)
        dispatch.spawn_outcome(state, header["task_id"], True)
    except dispatch.DispatchError as exc:
        _report("could not record the spawn outcome for %s.\n%s" % (header["task_id"], exc))
    sys.exit(0)


def handle_spawn_failure(data):
    """The spawn did NOT start (tool failure or denied permission) -> READY at once.

    Spec II.4 wants "Fehlschlag -> sofort zurueck auf READY". A failing tool call fires
    PostToolUseFailure, and a denial fires PermissionDenied — never PostToolUse — so a gate
    listening only on PostToolUse would leave the task LEASED until the TTL sweep.
    """
    if data.get("tool_name") not in SPAWN_TOOLS:
        sys.exit(0)
    state = _state_for_recording(data)
    if state is None:
        sys.exit(0)
    dispatch = _kernel.kernel_module("dispatch")
    header = _verified_header(data, state, dispatch, "PostToolUseFailure", require_role=False)
    if header is None:
        sys.exit(0)
    try:
        dispatch.clear_awaiting_bind(state, header["task_id"])
        dispatch.spawn_outcome(state, header["task_id"], False)
    except dispatch.DispatchError as exc:
        _report("could not return %s to READY after a failed spawn.\n%s"
                % (header["task_id"], exc))
    sys.exit(0)


HANDLERS = {
    "PreToolUse": handle_pre_tool_use,
    "SubagentStart": handle_subagent_start,
    "PostToolUse": handle_post_tool_use,
    "PostToolUseFailure": handle_spawn_failure,
    "PermissionDenied": handle_spawn_failure,
}


def main():
    data = _kernel.payload(HOOK)
    event = str(data.get("hook_event_name") or "")
    handler = HANDLERS.get(event)
    if handler is None:
        sys.exit(0)  # an event this gate is not registered for is not its business
    # re-entered with the RESOLVED event: an internal error on an event that cannot block must not
    # be audited as a "block" that never blocked (see _kernel.record_note)
    with _kernel.fail_closed(HOOK, event):
        handler(data)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
