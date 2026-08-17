#!/usr/bin/env python3
"""
The harness entry point -- the ONE thing a role runs the state kernel through (spec II.4).

    python scripts/harness.py <command> [...]

ONE SPELLING, and that is the decision rather than an accident. Those three tokens are identical
in bash and in PowerShell, and both shells are gated by the same PreToolUse hooks, so a
refusal text, a constitution and a role's report can all name the same line and it works wherever
the session runs. A wrapper at the repo root was the alternative and was rejected on the same
ground it would have been built for: a bare word, a dot-slash prefix and a `.cmd` suffix are three
spellings of one command, chosen by shell, and two surfaces in this harness have already drifted
apart exactly that way. (They are described rather than quoted here on purpose: a code span is
what a reader retypes, and `test_every_shipped_text_spells_the_entry_point_the_one_way` reads
every code span in the shipped tree that opens with the bare word.)

HOW MANY GATES "EVERY SHELL GATE" IS, since this file is byte-identical in every kit and the
number is not: it is whatever the kit registered on the `Bash|PowerShell` matcher in its own
`settings.json` -- measured 2026-07-31: dev-team 8, research-team 6, office-team 6 (and the
matcher is a TOOL LIST, so a gate registered on `Bash|PowerShell|Edit|Write|MultiEdit` counts:
reading that field as a string reported office as 5). This text used
to say "eight" five times, which was true of one kit out of three; the shipped checks read the
registration instead (`_shell_gates_of`), so the property travels and the number does not. For the
same reason the gates named below are named as examples of what THIS kit ships: office ships no
`gate_git.py` at all.

WHY IT LIVES UNDER `scripts/`. `gate_write_scope` refuses any pipeline that can write and whose
COMMAND LINE names `.claude`, `.codex` or the state directory -- because a copy of the enforcement
layer runs outside every path check, which is the shortest measured route to a forged approval.
That rule is right, and it decides where the entry point can be. Measured as real hook processes
against a scaffolded project:

    python scripts/harness.py evidence --kind test ...      every shell gate allows
    python scripts/harness.py doctor                        every shell gate allows
    python -B .claude/kernel/cli.py doctor                  refused, "names the enforcement layer"
    python scripts/harness.py --root project_memory ...     refused, "names the canonical state
                                                            directory"
    python -B -m kernel.cli evidence ...                    allowed by the gates, then
                                                            ModuleNotFoundError: the kernel
                                                            installs as `.claude/kernel`

So the entry point has to sit where a role may NAME it, and it has to resolve the state directory
itself instead of taking it from a command line that may not mention it.

WHICH IS WHY `--root` IS REFUSED HERE INSTEAD OF FORWARDED. Two independent reasons, and each
alone would be enough. It cannot be typed: the fourth line above is the measurement. And it would
be wrong if it could: `kernel/cli.py` defaults it to the RELATIVE `project_memory`, so the same
argument addresses a different directory -- usually a nonexistent one -- from any subdirectory.
The refusal is not a list of spellings either. `set_defaults()` replaces the parser's own default
with a sentinel and the SHIPPED parser then decides, so argparse's prefix matching is covered
without this file knowing anything about it. Measured against a scaffolded project, all six of
`--root x`, `--roo x`, `--ro x`, `--r x`, `--root=x` and `--r=x` come back refused with rc 2 --
argparse accepts any unambiguous prefix, and on this parser `--root` is the only long option
there is to be a prefix of.

NO BYTECODE, and `sys.dont_write_bytecode` has to stand above every kernel import for it. The
kernel installs into `.claude/kernel` and the bridge into `.claude/hooks`, both inside the tree
`hook_bundle_hash` measures with nothing excluded, so a cached import drops `.pyc` into the very
bundle this command exists to diagnose. Measured by flipping that assignment to False in a copy of
this kit outside the repo and running one `evidence` in a scaffolded project: FOURTEEN `.pyc`
appeared under `.claude/hooks` and `.claude/kernel`, which is what makes the next SessionStart
report `hooks_trust_required` -- the diagnosis command destroying what it diagnoses. Carrying the
rule in the file rather than in the invocation is what lets the sanctioned spelling be three tokens
with no flag to forget; `scripts/kit_checks.py` states the same rule for the same tree, and
`kernel/hashing.py` (BYTECODE_SUFFIXES) is what measures it.

KIT-OWNED. The scaffold overwrites this file on every run, like `scripts/kit_checks.py` and
unlike the copy-if-absent repo templates: a project keeping an old entry point would keep an old
bridge into the enforcement layer, and that is a security question rather than a comfort one.
Report a defect here; never patch it in a project.

WHAT THIS ENTRY POINT MADE REACHABLE, named because it is the direct consequence of shipping it
and a text that lists only benefits is the comment shape this kit refuses:

  * `transition` PUTS THE STATUS AUTOMATON ON EVERY ROLE'S COMMAND LINE, and what that is worth
    changed on 2026-07-31. It used to check the automaton and NOTHING else, so a role could walk a
    root item out of its DRAFT -- measured then: `python scripts/harness.py transition PR-0002
    APPROVED` passed every registered shell gate and succeeded, with a specialist's `agent_type` in
    the payload as readily as without one, while `gate_git` refused a merge for an item in its
    initial status on the ground that nothing had approved the work. `ProjectState.transition` now
    asks `approvals.assert_transition_approved` on every edge, so an edge an approval COMMITS
    (`approvals.APPROVAL_TRANSITIONS`, read backwards) needs a valid, unrevoked,
    content-matching APR of that kind before it moves.
    WHAT IS STILL ON THAT COMMAND LINE, because a paragraph that stopped at the fix would be the
    comment shape this kit refuses: every edge no approval kind commits. A role may still walk its
    own tasks through the TSK chain, and it may still take a root item to `REJECTED` or
    `SUPERSEDED` -- abandoning work is not approving it, so those edges are ungated by the same
    derivation that gates the others, and the consequence is that the supervised party can drop a
    requirement without asking. Named, not gated: gating a terminal would make an item
    unabandonable, and which of the two is worse is the harness owner's call.
    `gate_git`'s refusal is PARAPHRASED above, and deliberately so. The sentence a role actually
    reads lives in another file (`gate_git._refuse_a_status_no_delivery_can_follow`), nothing
    checks a quotation of it from here, and it may be reworded any day -- so quoting it would be
    this kit's own "a text may not claim what the code does not build", committed by the file that
    exists to say so. The first cut of this paragraph quoted words the gate does not use; read the
    wording at the source when you need it.
  * `capture` / `create-task` MAKE THE ROLE THE AUTHOR OF ITS OWN WORK ORDERS. That is what spec
    II.4 asks for, and it is also the widest of these surfaces: `allowed_scope` and
    `forbidden_scope` are gate layer 3's only inputs, so the party a specialist's writes are
    scoped by is the party that wrote the scope. Three things bound it and none of them is this
    file: the fields FREEZE once the task leaves DRAFT (`TSK_PLAN_FIELDS`), a dispatch still needs
    a user approval on the root, and `gate_write_scope` refuses a blank/`.`/bare-`*` scope entry.
    A `**` is legal and grants the repo -- deliberately, since a PM may need it, and visibly,
    since it stands in the task file the user can read.
  * NOTHING BINDS ANY OF THESE COMMANDS TO A ROLE, and that is one finding for all four rather
    than a caveat under each. The gates that could tell a specialist from the lead read a hook
    PAYLOAD (`agent_id`), and a shell command line carries no such thing -- measured against a
    scaffolded project: the `capture` line above passes every registered shell gate with a
    subagent's `agent_id` in the payload exactly as it does without one. So a bound specialist can
    capture items, plan work orders, and hand back a result for a task that is not its own. Its
    own FILE writes stay scoped (gate layer 3 does read the payload), and a spawn still needs the
    lead plus a user approval; what is unbounded is the STATE surface. Closing it needs a role
    identity the shell layer does not have, which is a harness-owner decision, not a launcher's.
  * `submit-result` MOVES A TASK ON BEHALF OF WHOEVER RUNS IT, in both directions. It checks that
    the task is IN_PROGRESS and validates the envelope; it does NOT check that the caller is the
    specialist bound to that lease -- the shell carries no agent identity a kernel call could read
    (the binding lives in the hook payload's `agent_id`, and a command line has none). So any
    role, including the lead, can hand back a result for any task in flight.
    ONE USE OF THAT IS SANCTIONED RATHER THAN MERELY POSSIBLE, and it is why `--from` exists
    (BUG-0048): a specialist whose definition grants no command-running tool cannot type this line
    at all, so it stages the envelope under its own task's key and the lead names that file. The
    kernel then stores the specialist's bytes rather than the lead's paraphrase of them. Which
    roles those are is `kernel/dispatch.hand_back_path`, and the dispatch header tells each role
    its own answer.
    AND THE SAME CALL REVOKES A RUNNING SPECIALIST'S WRITE SCOPE, which is the half that costs
    something immediately: submitting REMOVES the lease, and the lease IS the `agent_id -> task`
    mapping gate layer 3 resolves. Measured 2026-07-31 against a bound child: a write inside its
    `allowed_scope` returns rc 0 before the submit and rc 2 after it ("this subagent is not bound
    to a task"). So one command line stops another role's specialist mid-work, and the specialist
    is told it was never dispatched. Named rather than closed for the same reason as above: the
    fix is a kernel-side identity for shell callers, which does not exist today.
  * `dispatch` LEASES A TASK, and a lease is exclusive: a second claim on the same task is
    refused, so leasing a READY task and never spawning parks it until the TTL sweep returns it.
    The TTL is deliberately NOT a flag -- "kurzlebige Lease" is the property spec II.4 names, and
    a supervised party that could choose how short short is would be choosing the property.
  * `$HARNESS_KERNEL_PATH` REDIRECTS THIS COMMAND TO ANOTHER KERNEL. `_kernel.kernel_parents`
    treats the variable as AUTHORITATIVE by design (an override that silently fell back would be
    the "enforced against the wrong state" hazard), and this file inherits that. Measured: with it
    set, every shell gate allows and the foreign kernel runs. It is informational rather than a
    privilege gain -- the state root stays project-local, and anyone able to set it is already
    able to run any script -- but the sanctioned surface should say so rather than let a reader
    infer that this path is pinned.
"""
import os
import sys

# BEFORE the import below, and not one line lower -- see the docstring. `_kernel` pulls in the
# kernel package and PyYAML, and every module imported after this point would otherwise be cached
# into the hashed bundle.
sys.dont_write_bytecode = True

# The project root, taken from THIS FILE rather than from the cwd: `python scripts/harness.py` is
# the sanctioned spelling from the repo root, but a role that has `cd`-ed into a subtree still
# reaches the same file through a relative path, and the state directory must not move with them.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(REPO_ROOT, ".claude", "hooks")


def _fail(message, remedy):
    """Refuse with the two-part shape every gate in this kit uses. Exit code 2 = the command was
    not run; 0/1 stay reserved for what the kernel decided (see `kernel/cli.py`)."""
    sys.stderr.write("[harness] %s\nRemedy: %s\n" % (message, remedy))
    return 2


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not os.path.isfile(os.path.join(BRIDGE, "_kernel.py")):
        return _fail(
            "this project has no enforcement layer at %s, so there is no kernel to run "
            "(spec II.4: an entry point that guesses where the state lives is the "
            "'enforced against the wrong state' hazard in another costume)." % BRIDGE,
            "re-run the team scaffold for this repo; the kernel and this entry point travel "
            "together and are replaced together.")
    sys.path.insert(0, BRIDGE)
    try:
        import _kernel
    except BaseException as exc:  # noqa: BLE001 -- a broken bridge must name itself, not traceback
        return _fail(
            "the hook helpers next to the kernel could not be loaded (%r), so this command "
            "cannot reach the state." % (exc,),
            "a partial checkout or a half-finished kit update is the usual cause; re-run the "
            "team scaffold for this repo.")
    # Importing the bridge ARMS the gate excepthook, which turns any escaping exception into
    # "the hook itself failed to run" and `os._exit(2)`. This is a command a person typed, so an
    # ordinary error has to stay an ordinary error with a flushed stdout (`kit_checks.py` does
    # the same for the same reason).
    _kernel.disarm()
    try:
        cli = _kernel.kernel_module("cli", REPO_ROOT)
    except Exception as exc:
        return _fail("the state kernel could not be imported (%s: %s)." % (type(exc).__name__, exc),
                     "run the team scaffold for this repo; the message above names what is "
                     "missing.")

    here = os.path.relpath(os.path.abspath(__file__), REPO_ROOT).replace(os.sep, "/")
    if here != cli.ENTRY_POINT:
        # A copy at another path would resolve REPO_ROOT one directory off AND print usage lines
        # naming a file that is not the one running -- a text promising what the code does not do.
        return _fail(
            "this file is running as %s, but the entry point the kernel and every shipped "
            "remedy name is %s." % (here, cli.ENTRY_POINT),
            "run `%s` from the project root; the scaffold installs exactly that copy and "
            "overwrites it on every run." % cli.INVOCATION)

    # `--root` is decided by the SHIPPED parser, not by matching text: a sentinel replaces its own
    # default, so anything argparse binds to that option -- including the abbreviations `--r`,
    # `--ro`, `--roo` and the `--root=` form -- comes back as "the caller supplied it".
    parser = cli.build_parser()
    unset = object()
    parser.set_defaults(root=unset)
    parsed = parser.parse_args(argv)          # --help and usage errors exit here, as they should
    if parsed.root is not unset:
        return _fail(
            "`--root` does not belong on this command line. Two reasons, either one enough: "
            "`gate_write_scope` refuses a write-capable pipeline that NAMES the state directory, "
            "so the command becomes unrunnable for the role that needs it; and the kernel reads "
            "the flag relative to the current directory, so the same argument means a different "
            "directory from every subdirectory.",
            "drop the flag -- `%s` resolves the state directory from the project root itself "
            "(%s)." % (cli.INVOCATION, _kernel.state_dir(REPO_ROOT)))

    return cli.main(["--root", _kernel.state_dir(REPO_ROOT)] + argv)


if __name__ == "__main__":
    sys.exit(main())
