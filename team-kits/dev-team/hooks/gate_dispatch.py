#!/usr/bin/env python3
"""
Dispatch gate — gate layer 2 of spec II.4. Registered on FIVE events, because the dispatch
lifecycle is one story and splitting it across files would let the halves drift:

  PreToolUse(Agent|Task)        reconcile claims that never produced a child; refuse while the
                                installed enforcement bundle is not the one this project recorded
                                trust for (`_kernel.bundle_trust`); then validate the
                                HARNESS_DISPATCH header against the lease and CLAIM the lease for
                                this one dispatch, which opens the bind window
  SubagentStart(*)              bind that lease to the child's agent_id (gate layer 3 needs the
                                agent_id -> task mapping while the child is still running)
  PostToolUse(Agent|Task)       the spawn STARTED: re-verify the header, bind the agent_id
                                authoritatively (here the header and the agentId arrive
                                together), and move the task to IN_PROGRESS
  PostToolUseFailure(Agent|Task) the spawn did NOT start: return the task to READY at once and
                                close the bind window — an ACCELERATOR, not the guarantee
  Stop()                        reconcile again at the end of the turn, so a claim that produced
                                no child does not wait for the next spawn attempt to be noticed

WHAT THIS GATE PARSES: the header, and only the header (spec II.4). Free prompt prose is never
evidence of anything — the V1 `guard_agent_spawn` keyword check is exactly the "looks approved"
failure this replaces. A spawn without a header is refused; a spawn whose header names a task
that is not leased to it is refused.

WHICH EVENTS CAN ACTUALLY REFUSE (hooks reference, exit-code-2 table — this decides the whole
design, so it is written down rather than assumed): PreToolUse blocks. PostToolUse,
PostToolUseFailure and SubagentStart do NOT — their stderr is shown and the action stands. Stop
does block, but this gate never refuses there: a Stop that exits 2 forces the assistant to keep
going, which is not what "a lease was returned to READY" should do. So PREVENTION lives in
PreToolUse alone. In the later events this gate protects the only thing it still can: it REFUSES
TO MUTATE STATE on anything it cannot verify, and says so on stderr. Calling that a "block" would
be theatre, and theatre is what V2 is removing.

THE ROLLBACK DOES NOT DEPEND ON ANY EVENT, and it used to. Measured 2026-08-02 across twelve real
headless sessions with an observer on eleven events: `PermissionDenied` fired NOT ONCE — neither
after a hook refusal nor after a permission refusal (the stream counted the denial and no hook
saw it), while `PostToolUseFailure` registered from the same file with the same matcher shape did
fire. The claim was previously an eternal flag undone only by `PostToolUseFailure|PermissionDenied`,
so a refused spawn stranded its task for the remaining ~900 s of the lease TTL. What returns a
spent claim now is time: `dispatch.spent_claim_reason` says when a claim still stands and
`dispatch.reconcile_unstarted_dispatches` returns the task to READY when it does not. The two
events above only make that verdict arrive sooner.

AND A CLAIM IS NOT MADE UNTIL EVERY HARNESS REFUSAL IS KNOWN. Also measured: every PreToolUse
hook of one event runs to completion even when a sibling exits 2, so this gate used to spend the
lease while another gate of the same event was refusing the very same spawn. The kits therefore
register the PreToolUse(Agent|Task) gates as ONE chained command with this one LAST (see
`_gate.py`); which gates precede it is each kit's business, and office has four where dev has two.

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
# rule this gate enforces. A tool call that FAILS arrives as PostToolUseFailure; a call the
# permission layer refuses arrives as nothing at all, which is why the rollback does not wait for
# an event (see the module docstring and `dispatch.reconcile_unstarted_dispatches`).
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


def _refuse_untrusted_bundle(data):
    """No delegation while the enforcement bundle is not the one this project trusts.

    THE HOLE THIS CLOSES, measured 2026-08-01: `.claude/kit_state.json` was WRITTEN by the
    scaffold and by `kit_trust_state`, and read by exactly two places — `kernel/report.py` for the
    doctor's `hook_trust` capability and `guard_harness_selfmod` for its write-protection list.
    No authorising code path read it. An ablation over four trust states with one identical spawn
    payload produced four identical verdicts with identical reasons: the trust record was not a
    term in the decision, so a project could delegate on a bundle it had never vouched for.

    A SPAWN is where it binds, because a spawn is the moment the harness hands a task's
    `allowed_scope` to a child — the grant every downstream gate is measured against. What
    `withdrawn` means is `_kernel.bundle_trust`'s business, and deliberately: this file must not
    grow a second opinion about which trust states are which.
    """
    trust = _kernel.bundle_trust(_kernel.find_repo_root(data.get("cwd")))
    if not trust.withdrawn:
        return
    _kernel.block(
        HOOK,
        "specialist spawn refused: %s.\nDelegation hands a child the task's `allowed_scope`, and "
        "the gates that would hold it to that scope are the very files whose integrity is in "
        "question — so no spawn is authorised until somebody has vouched for the bundle again."
        % trust.reason,
        event="PreToolUse",
        remedy="open /hooks and review what changed in `.claude/hooks` and `.claude/kernel`; if "
               "the change is not yours, treat it as a finding. Re-running the scaffold "
               "reinstalls the kit files and records the reviewed bundle; then start ONE new "
               "session. ASK THE USER TO RUN IT — `gate_write_scope` refuses a WRITE-CAPABLE "
               "command line that names the enforcement layer, and starting a script is one, so "
               "this session cannot run the scaffold itself; and no number of new sessions "
               "clears the state without it. "
               "`python scripts/harness.py doctor` reports the same state as `hook_trust`.")


def handle_pre_tool_use(data):
    if data.get("tool_name") not in SPAWN_TOOLS:
        sys.exit(0)
    _refuse_untrusted_bundle(data)
    state = _state_for_prevention(data)
    if state is None:
        sys.exit(0)
    dispatch = _kernel.kernel_module("dispatch")
    tool_input = data.get("tool_input") or {}
    try:
        # BEFORE judging this spawn, and that order is the point: a claim whose bind window has
        # closed with no child is not evidence of anything, so it must not be what refuses the
        # next attempt. Reconciling here means the way out is walked by the very act of trying
        # again, without waiting for the turn to end.
        dispatch.reconcile_unstarted_dispatches(state)
        header = dispatch.parse_header(str(tool_input.get("prompt") or ""))
        dispatch.validate_dispatch(state, header, tool_input.get("subagent_type"), claim=True,
                                   prompt_id=data.get("prompt_id"))
    except dispatch.DispatchError as exc:
        _kernel.block(HOOK, "specialist spawn refused.\n%s" % exc, event="PreToolUse")
    sys.exit(0)


def _report(message):
    """Say something WITHOUT claiming to have prevented anything, and audit it.

    Deliberately not `_kernel.block`. Every event this gate uses it on is one where a refusal
    would be a lie of a different kind: on PostToolUse, PostToolUseFailure and SubagentStart exit
    2 does not block at all (the action stands and only stderr is shown), and on Stop it blocks
    something nobody asked about — the assistant finishing its turn. The real protection on the
    first three is that we DID NOT MUTATE state; on Stop it is that the mutation is a rollback.
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
    """The spawn did NOT start -> READY at once. An ACCELERATOR, not the guarantee.

    Spec II.4 wants "Fehlschlag -> sofort zurueck auf READY". A failing tool call fires
    PostToolUseFailure and this makes that immediate. It is deliberately NOT the only way back:
    measured 2026-08-02, a permission refusal delivers no hook event at all, so a task whose
    return to READY hung on one would simply never return. `handle_stop` and the reconciliation
    at the next PreToolUse cover the silent cases; this one only saves the wait.
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


def handle_stop(data):
    """End of the turn: return every claim that produced no child to READY.

    WHY THIS EVENT. It is the one that was MEASURED to arrive: `Stop` fired in all twelve real
    headless sessions of 2026-08-02, including the ones that ended after four refused tool calls,
    while `PermissionDenied` fired in none of them. A reconciliation that runs here therefore
    needs no cooperation from the failure path it is cleaning up after.

    It never refuses. Stop CAN block (exit 2 makes the assistant continue), and using that here
    would turn "a task went back to READY" into "you may not stop" — a refusal nobody asked for,
    on an event where the tool call it would be about is long over.
    """
    state = _state_for_recording(data)
    if state is None:
        sys.exit(0)
    dispatch = _kernel.kernel_module("dispatch")
    released = dispatch.reconcile_unstarted_dispatches(state)
    if released:
        _report("returned to READY — dispatched, but no subagent ever started for %s. A spawn "
                "that the permission layer or the provider refused delivers no hook event, so "
                "this is measured by the bind window closing empty, not reported by anything."
                % ", ".join(released))
    sys.exit(0)


HANDLERS = {
    "PreToolUse": handle_pre_tool_use,
    "SubagentStart": handle_subagent_start,
    "PostToolUse": handle_post_tool_use,
    "PostToolUseFailure": handle_spawn_failure,
    "Stop": handle_stop,
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
