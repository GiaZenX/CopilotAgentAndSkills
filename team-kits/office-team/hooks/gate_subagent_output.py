#!/usr/bin/env python3
"""
SubagentStop() — a kit specialist may not stop without honoring its output contract.

Every role skill defines an "Output to the PM/manager" YAML block; a real failure class is the
specialist that "finishes" with prose, an apology, or nothing — and the PM builds on air. Claude
uses exit 2; Codex uses `decision: block` with a continuation reason. Scope: only OUR specialists
(an agent file exists for agent_type); utility/foreign agents pass. Verdict roles must also carry
`verdict:`.
Uncertainty -> exit 0.

THE ONE-RETRY PASS-THROUGH IS DELIBERATE, AND IT IS A HOLE THAT STAYS. `stop_hook_active` says a
stop hook already blocked this cycle, and the provider sets it on every continuation one caused --
so blocking again is not a second chance, it is an endless loop. This gate therefore lets the
SECOND stop through with whatever it carries, which means a second consecutive violation is
unblocked. What it can still do is say which of the two states it is in, and that is what BUG-0049
bought: in all 8 stops pilot 3 measured, the line read "still missing nothing" -- a give-up record
written over a retry that HAD delivered. `test_the_give_up_line_says_what_the_retry_did` measures
both states, exit 0 on the violating one included.
"""
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _root import find_repo_root
import _audit
import _compat


VERDICT_ROLES = ("quality-engineer", "reviewer")
DEFAULT_REQUIRED = ("summary",)


def main():
    # BOUNDED read (spec II.4). A raw `json.load(sys.stdin)` will happily buffer a
    # payload of any size, and an oversized one is the shape that turns a hook into
    # a memory event rather than a decision. `_compat.load` caps it at STDIN_LIMIT
    # and exits 2, because a gate that cannot read its input has not judged it.
    data = _compat.load()
    if str(data.get("hook_event_name") or "") != "SubagentStop":
        sys.exit(0)
    atype = str(data.get("agent_type") or "")
    # SCOPE FIRST, and the give-up branch below is the reason it moved up here: it used to stand
    # ahead of these two checks and so recorded a contract violation for agents this gate never
    # judges -- `Explore still missing summary` for a utility agent that owes no output block, and
    # ` still missing summary` for a stop with no agent_type at all
    # (`test_a_foreign_agent_leaves_no_give_up_record`).
    if not atype:
        sys.exit(0)
    root = find_repo_root(data.get("cwd"))
    if not os.path.isfile(os.path.join(root, ".claude", "agents", atype + ".md")):
        sys.exit(0)  # not one of our kit specialists
    required = DEFAULT_REQUIRED + (("verdict",) if atype in VERDICT_ROLES else ())
    low = str(data.get("last_assistant_message") or "").lower()
    missing = [k for k in required if (k + ":") not in low]
    if data.get("stop_hook_active"):
        # The deliberate pass-through the module docstring names. The RECORD is the whole value of
        # this branch, so it states which of the two things happened -- the retry honored the
        # contract, or this stop is the unblocked second violation -- rather than reporting a
        # give-up for both (BUG-0049; field data: bare `gave_up` lines were undiagnosable).
        try:
            _audit.record_event(
                "gate_subagent_output",
                "gave_up" if missing else "retry_delivered",
                "%s: giving up with %s still missing" % (atype, ",".join(missing)) if missing
                else "%s: retry delivered the output contract" % atype)
        except Exception:
            pass
        sys.exit(0)

    if missing:
        _audit.record("gate_subagent_output", "%s missing %s" % (atype, ",".join(missing)))
        message = (
            "[team-kit gate] Your final message is missing the output-contract key(s): %s. "
            "Do NOT run any more tools and do NOT continue working — ONLY print the YAML output "
            "block for the work you already did (see 'Output to the PM' in your skill: summary, "
            "ids, statuses%s), then stop. A real retry spent 41 minutes doing NEW work instead of "
            "restating; the PM builds on this block and prose-only endings produced work built on "
            "air.\n"
            % (", ".join(missing), ", verdict" if atype in VERDICT_ROLES else "")
        )
        _compat.stop(message, "SubagentStop")
    sys.exit(0)


if __name__ == "__main__":
    main()
