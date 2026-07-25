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
present, which is worse: `harness doctor` still finds it registered and on disk.

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

CONTRACT: `python _gate.py <gate>.py` — compile and run `<gate>.py` in this process as `__main__`,
so a gate behaves exactly as when run directly (it still reads stdin, still exits 0 or 2, still
uses its own preamble). Anything that goes wrong BEFORE or AROUND the gate's own logic — missing
file, unreadable file, SyntaxError, an escaping exception, an argument that names something
outside this directory — exits 2. `SystemExit` passes through untouched; that is the gate
speaking, and the launcher must never overrule it.

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


def _refuse(reason):
    text = ("[team-kit gate launcher] refused: %s — a gate that cannot RUN must not be read as "
            "permission (spec II.4 fail-closed).\nRemedy: run `harness doctor`; a partial "
            "checkout or a half-finished kit update is the usual cause.\n" % reason)
    try:
        sys.stderr.write(text)
        sys.stderr.flush()
        sys.exit(2)
    except SystemExit:
        raise
    except BaseException:
        os._exit(2)


def main():
    if len(sys.argv) < 2:
        _refuse("no gate was named on the command line")
    here = os.path.dirname(os.path.abspath(__file__))
    # Only ever a sibling, by basename. The launcher is named in settings.json, which an agent
    # cannot write — but the ARGUMENT travels in the same string, and a launcher that would run
    # any path handed to it turns one protected file into an arbitrary-script runner.
    name = os.path.basename(sys.argv[1].replace("\\", "/"))
    if not name.endswith(".py") or name.startswith("_"):
        _refuse("%r is not a gate in this directory" % sys.argv[1])
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
    # dict version cost every approval in every kit.
    module = types.ModuleType("__main__")
    module.__file__ = path
    module.__builtins__ = __builtins__
    module.__loader__ = None
    module.__spec__ = None
    module.__package__ = None
    sys.modules["__main__"] = module
    sys.argv = [path] + sys.argv[2:]
    try:
        exec(code, module.__dict__)  # noqa: S102 — running the gate IS the job
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001
        _refuse("%s failed while running (%s: %s)" % (name, type(exc).__name__, exc))
    # A gate that returns without exiting has allowed the call; say so explicitly rather than
    # relying on the interpreter's default.
    sys.exit(0)


if __name__ == "__main__":
    main()
