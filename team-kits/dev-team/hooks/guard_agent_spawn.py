#!/usr/bin/env python3
"""
PreToolUse(Agent|Task) guard — only role-based specialist spawns are allowed.

Kills the `subagent_type=None` / generic-agent spawn bug from the real test run.
The PM (main agent) MUST spawn specialists by their exact role. This hook reads the
allowed roles from the installed `./.claude/agents/*.md` basenames, so it is
kit-agnostic and always correct. Exit 2 + stderr blocks; uncertainty -> exit 0.

Also the V14 backstop: `run_in_background` MUST be set EXPLICITLY on every spawn. The platform
defaults to background, and a real run spawned 37/37 specialists that way by omission — losing
completion accounting and pushing the PM into a settings workaround. false = normal sequential
delegation; true = a deliberate parallel batch the PM fully awaits (notify_agent_events logs the
completions). Forcing the field makes the choice conscious instead of a silent default.

AND THE FIRST QUESTION OF ALL: WHO IS ASKING. Delegation belongs to the SESSION INSTANCE — the
lead bound through settings.json `agent:` — and to nothing else. Until platform 2.1.219 that was
free, because a subagent could not spawn at all; it can again (measured, see
`_compat.calling_subagent`, where a subagent spawned a further subagent in the same run). What was
holding it up HERE was not a rule but an OMISSION: only the three LEAD frontmatters list the
`Agent` tool, every specialist one leaves it out, adding one makes no test red — and `tools:` is a
Claude-only field, so on another provider the omission is not even expressible. An omission that
two dozen files have to keep agreeing on is the shape this repo has paid for repeatedly, so the
rule is stated once instead, as the property that separates the two callers: **a hook payload
names an agent OTHER than the role `settings.json` binds as `agent:` only inside a subagent.**
`_compat.calling_subagent` is that predicate and carries the measurement that backs it — including
why the shorter wording ("names an agent at all") was measurably wrong and locked the lead out of
its own project.

WHAT THIS DOES NOT BUY, both directions:
  * Only where it is REGISTERED. `gen_provider_artifacts.CODEX_UNSUPPORTED_TOOLS` declares
    `Agent`/`Task` as having no Codex equivalent, so on Codex no spawn hook runs at all and the
    rule binds through the constitution alone. The DEFINITION is provider-neutral (Codex supplies
    both fields too); the enforcement is not.
  * It reads what the provider SENDS. A provider release that stopped naming the caller would make
    a subagent look like the session instance, and this check would let it through — the failure
    direction is a missed refusal, never a lead locked out of delegating.
"""
import sys
import os
import glob


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _root import find_repo_root
import _compat
import _audit


ROLE_REMEDY = ("Spawn a specialist by its EXACT role as subagent_type (one of the installed "
               "./.claude/agents/). Never spawn a generic/unnamed agent.\n")


def block(why, remedy=ROLE_REMEDY):
    _audit.record("guard_agent_spawn", why)
    _compat.stop("[team-kit guard] Agent spawn blocked: %s\n%s" % (why, remedy), "PreToolUse")


def main():
    # BOUNDED read (spec II.4). A raw `json.load(sys.stdin)` will happily buffer a
    # payload of any size, and an oversized one is the shape that turns a hook into
    # a memory event rather than a decision. `_compat.load` caps it at STDIN_LIMIT
    # and exits 2, because a gate that cannot read its input has not judged it.
    data = _compat.load()
    if data.get("tool_name") not in ("Agent", "Task"):
        sys.exit(0)
    inp = data.get("tool_input") or {}
    sub = inp.get("subagent_type")

    # BEFORE EVERY OTHER CHECK, and before the role set is even looked up: the role set decides
    # WHICH spawn is well-formed, this decides WHETHER this caller may spawn at all. A project
    # without `.claude/agents/` exits 0 below — that must not become a hole for a subagent, which
    # is why this question is answered first and from the payload alone.
    caller = _compat.calling_subagent(data)
    if caller:
        block(
            "this call comes from a subagent (%s), and a subagent does not delegate. Only the "
            "session instance — the lead bound in settings.json `agent:` — does." % caller,
            "You are executing ONE task under a lease the lead minted for you. Spawning a second "
            "specialist would authorise it yourself: you would create the work order, mint the "
            "lease and choose the scope, which are exactly the judgements the DELEGATE/ROUTE step "
            "of your work loop reserves for the lead. If your task needs work outside your scope, "
            "hand it back: name it in `followups` of your `submit-result` envelope and let the "
            "lead order it. If you believe a subagent legitimately has to spawn, that is a gap to "
            "REPORT — it is not one to route around.\n")

    cwd = find_repo_root(data.get("cwd"))
    agents_dir = os.path.join(cwd, ".claude", "agents")
    if not os.path.isdir(agents_dir):
        sys.exit(0)  # can't determine the role set -> don't block
    roles = {os.path.splitext(os.path.basename(p))[0]
             for p in glob.glob(os.path.join(agents_dir, "*.md"))}
    # the session agent (the PM/lead) is NEVER spawnable as a subagent (constitution §1 — no second
    # PM). Read through `_compat.session_lead` so the binding has ONE parser in the kit: this hook
    # kept a second copy of it, and `calling_subagent` now decides on the same field — two readers
    # of one setting is the drift `_compat` exists to prevent.
    #
    # The fallback stays HERE and deliberately does not move into that helper: an unreadable
    # binding must make this question ("may this role be spawned?") answer "the PM still may not",
    # and the other one ("is this caller the lead?") answer "unknown". Same setting, opposite fail
    # directions.
    lead = _compat.session_lead(data.get("cwd")) or "project-manager"
    roles.discard(lead)
    if not roles:
        sys.exit(0)

    if not sub or not str(sub).strip():
        block("no subagent_type given (generic agent)")
    if str(sub) == lead:
        block("the %r (PM/lead) is the session agent and MUST NOT be spawned as a subagent" % lead)
    if str(sub) not in roles:
        block("subagent_type %r is not an installed specialist role (%s)" % (sub, ", ".join(sorted(roles))))
    if "run_in_background" not in inp:
        block("run_in_background not set — the platform silently defaults to background. Set it "
              "EXPLICITLY: `run_in_background: false` for normal sequential delegation (the default "
              "choice), `true` ONLY for a deliberate parallel batch — then NEVER advance the phase "
              "before ALL completion notifications have returned")

    # work-order minimal schema (Anthropic: every subagent needs an objective, an output format,
    # sources and boundaries — vague orders produce duplicated work and gaps). Deterministic floor:
    # the prompt must carry `objective` and `output` keys; the skills define the full template.
    prompt_low = str(inp.get("prompt") or "").lower()
    missing = [k for k in ("objective", "output") if k not in prompt_low]
    if missing:
        block("work order lacks %s — every delegation is a YAML work order with at least:\n"
              "  objective: <one sentence - what DONE looks like>\n"
              "  read_first: [the exact files to read]\n"
              "  output: <the YAML keys expected back>\n"
              "  boundaries: <what is OUT of scope>" % " + ".join("`%s:`" % k for k in missing))

    # allowed spawn -> audit it (V2): the Notification route for background completions proved dead
    # in a real environment (0 of 15 completions logged), so spawn accounting must not depend on it.
    try:
        _audit.record_event("guard_agent_spawn", "spawn",
                            "%s (run_in_background=%s)" % (sub, inp.get("run_in_background")))
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
