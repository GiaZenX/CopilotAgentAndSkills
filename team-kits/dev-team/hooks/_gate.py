#!/usr/bin/env python3
"""
_gate.py — the launcher that closes the last fail-open gap: a gate file that will not COMPILE.

THE GAP, named in `_kernel.py`'s docstring as a decision rather than a discovery: every V2 gate
opens with GATE_PREAMBLE, which survives its own helpers being broken, and `_kernel` installs an
excepthook that turns anything raised at module scope into exit 2. Neither can cover the gate file
FAILING TO PARSE. A file truncated mid-write — the ordinary artifact of an interrupted kit update,
and the same failure the preamble exists for, one step earlier — raises SyntaxError before its
first statement runs. Python exits 1. Claude Code reads every code except 2 as a non-blocking
error and LETS THE CALL THROUGH. The gate is not merely absent; it is absent while looking
present, which is worse: `python scripts/harness.py doctor` still finds it registered and on disk.

"Nothing inside a Python file can close that; it closes one level up, by invoking gates through a
launcher whose own compile is the only one that must succeed." This is that launcher.

WHY THIS IS AN IMPROVEMENT AND NOT A RELOCATION. It does not make compilation infallible — this
file can be truncated too. It reduces the number of files whose compile must succeed from "every
gate, forever, including every gate anyone adds later" to exactly one, and makes that one as small
as it can be: three stdlib imports, no helpers, no module-level work. What is left is a
file short enough to read in full and stable enough that a kit update rarely rewrites it.
The trade runs the other way too, and is named here rather than discovered later: a
truncated `_gate.py` now disarms every blocking gate in the kit at once, where before it
would have disarmed one. That is the deal — one file that must hold, instead of twenty
that each might not.

CONTRACT: `python _gate.py <gate>.py [<gate>.py ...]` — compile and run each named gate in this
process as `__main__`, IN ORDER, so a gate behaves exactly as when run directly (it still reads
stdin, still exits 0 or 2, still uses its own preamble). The first gate that exits non-zero ends
the chain with that code; a gate that exits 0 hands the same payload to the next one. Anything
that goes wrong BEFORE or AROUND a gate's own logic — missing file, unreadable file, SyntaxError,
an escaping exception, an argument that names something outside this directory — exits 2.
`SystemExit` is the gate speaking, and the launcher never overrules it: it only decides whether a
ZERO means "allowed, chain over" or "allowed so far, next gate".

WHY A CHAIN EXISTS AT ALL, and it is a correction rather than a convenience. Measured 2026-08-02
in twelve real headless sessions: EVERY PreToolUse hook of one event runs to completion, even when
another one of the same event exits 2 — all five `Edit|Write` gates start within 52 ms of each
other, all eight `Bash` gates start. So a hook that does not merely JUDGE the call but CONSUMES
something on it (`gate_dispatch` spends the task's dispatch lease) spent it while a sibling was
refusing the very same call, and the refusal was invisible to it. Registering such a hook LAST in
one chained command is what makes "every refusal reason for this call is known" true at the moment
it consumes. It is a property of the registration, not of any hook name: any gate that can refuse
belongs in front of any gate that consumes, whichever kit and however many there are.
`tools/test_hooks_v2.py::test_a_refused_spawn_does_not_spend_the_lease_through_the_registered_chain`
measures it through the command settings.json really spells.

WHAT THE CHAIN DOES **NOT** BUY, so nothing here reads as more than it is: the layers BELOW the
hooks — the permission system, and the provider deciding for its own reasons — still answer after
every gate has passed. A consumption can therefore still outlive a call that never happened, and
what covers that is time plus reconciliation in `kernel/dispatch.py`, not this file.

"AS `__main__`" MEANS A REAL MODULE IN `sys.modules`, not a dict with `__name__` set to the right
string. The first cut did the latter and silently disabled every approval in every kit:
`approvals._assert_minting_caller` — the check that makes a hand-written APR worthless — requires
`sys.modules["__main__"].__file__` to BE `gate_approval.py`, and behind a launcher that left the
launcher's own module there it was `_gate.py`. `gate_approval` runs on PostToolUse, which cannot
block, so it exits 0 either way: the mint simply never happened and nothing said so. Measured as
`APPROVED` when run directly and `DRAFT` through the launcher, on the same payload.

That check is the defence, not the obstacle. So the launcher builds a genuine module object and
installs it. `__name__`, `__file__`, `__doc__`, `__spec__`, `__package__`,
`sys.argv`, `sys.path[0]`, stdin, `atexit`, `warnings` filters and pickling of
gate-defined classes then match a direct run exactly; `__loader__` and
`__cached__` do not, and nothing in the kits reads them.
"""
import os
import sys
import types

# NO BYTECODE FROM A GATE RUN. `.claude/hooks` and `.claude/kernel` are the hashed enforcement
# bundle, and everything a gate imports — `_kernel`, `_compat`, the whole kernel package — would
# otherwise be cached as `.pyc` INSIDE it: the bundle would change by being run, which is precisely
# the argument that once kept bytecode out of the hash and thereby out of the measurement (see
# `kernel.hashing.BYTECODE_SUFFIXES`). The kits register every hook as `python -B`, so in
# production this line is redundant; it is here because a gate is also run directly — by the test
# suite, by a person diagnosing one — and the measurement must not depend on how it was started.
# It must precede the gate's own preamble, which imports `_kernel`. Cost, measured: ~5 ms on a full
# kernel import.
sys.dont_write_bytecode = True


def _refuse(reason):
    text = ("[team-kit gate launcher] refused: %s — a gate that cannot RUN must not be read as "
            "permission (spec II.4 fail-closed).\nRemedy: run `python scripts/harness.py doctor`; a partial "
            "checkout or a half-finished kit update is the usual cause.\n" % reason)
    try:
        sys.stderr.write(text)
        sys.stderr.flush()
        sys.exit(2)
    except SystemExit:
        raise
    except BaseException:
        os._exit(2)


def _run_one(here, argument):
    """Run one gate as `__main__` and return its exit code (0 = allowed)."""
    # Only ever a sibling, by basename. The launcher is named in settings.json, which an agent
    # cannot write — but the ARGUMENT travels in the same string, and a launcher that would run
    # any path handed to it turns one protected file into an arbitrary-script runner.
    name = os.path.basename(argument.replace("\\", "/"))
    if not name.endswith(".py") or name.startswith("_"):
        _refuse("%r is not a gate in this directory" % argument)
    path = os.path.join(here, name)
    try:
        with open(path, "rb") as handle:
            source = handle.read()
    except OSError as exc:
        _refuse("cannot read %s (%s)" % (name, exc))
    try:
        code = compile(source, path, "exec")
    except BaseException as exc:  # noqa: BLE001 — SyntaxError is the whole point
        _refuse("%s does not compile (%s: %s)" % (name, type(exc).__name__, exc))
    # A real module in `sys.modules["__main__"]`, not a bare dict — see the module docstring; the
    # dict version cost every approval in every kit. A FRESH one per gate, for the same reason:
    # `approvals._assert_minting_caller` asks which file is `__main__`, and in a chain that has to
    # be the gate running now, not the one before it.
    module = types.ModuleType("__main__")
    module.__file__ = path
    module.__builtins__ = __builtins__
    module.__loader__ = None
    module.__spec__ = None
    module.__package__ = None
    sys.modules["__main__"] = module
    sys.argv = [path]
    try:
        exec(code, module.__dict__)  # noqa: S102 — running the gate IS the job
    except SystemExit as exc:
        # The gate spoke, and the launcher reproduces the INTERPRETER's own reading of what it
        # said rather than inventing one: None means 0, an int is the code, anything else is a
        # message on stderr plus 1. Deviating here would change what `sys.exit(...)` means for a
        # gate depending on whether it ran alone or in a chain.
        status = exc.code
        if status is None:
            return 0
        if isinstance(status, int) and not isinstance(status, bool):
            return status
        if status is True or status is False:
            return 1 if status else 0
        sys.stderr.write("%s\n" % status)
        return 1
    except BaseException as exc:  # noqa: BLE001
        _refuse("%s failed while running (%s: %s)" % (name, type(exc).__name__, exc))
    # A gate that returns without exiting has allowed the call; say so explicitly rather than
    # relying on the interpreter's default.
    return 0


def main():
    if len(sys.argv) < 2:
        _refuse("no gate was named on the command line")
    here = os.path.dirname(os.path.abspath(__file__))
    # IN ORDER, and the first refusal ends it — see the module docstring. A gate that consumes
    # state is registered last precisely so no gate after it can still refuse the call it paid for.
    for argument in sys.argv[1:]:
        status = _run_one(here, argument)
        if status:
            sys.exit(status)
    sys.exit(0)


if __name__ == "__main__":
    main()
