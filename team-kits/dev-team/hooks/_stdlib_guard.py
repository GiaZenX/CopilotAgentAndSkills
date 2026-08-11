#!/usr/bin/env python3
"""
Shared helper: keep a file in a hook directory from answering for a STANDARD-LIBRARY name.

THE DEFECT THIS CLOSES (BUG-0013). Every hook of this kit puts its own directory at `sys.path[0]`
while it loads — the gate preamble does it, and so does each hook's own
`sys.path.insert(0, os.path.dirname(...))`. Everything a hook imports afterwards is then answered
out of that directory first. Measured 2026-08-05 and again 2026-08-11 through real hook processes:
a no-op `shlex.py` beside the hooks left `gate_write_scope`'s tokeniser empty and it allowed
`sed -i` into the kernel with rc 0; a no-op `subprocess.py` made `gate_pipeline` read a RED quality
pipeline as green and allowed the push. Neither wrote a line of stderr.

WHY A FINDER AND NOT `sys.path` HYGIENE: the shadow exists DURING an import the shadowed module is
in the middle of, so a `sys.path` repaired afterwards is repaired too late. This sits on
`sys.meta_path` in front of the one importer that consults `sys.path`, and answers for ONE property
only — a name the running interpreter itself calls standard library (`sys.stdlib_module_names`)
that a guarded directory is currently in front of. Every other name, `_compat` and `kernel`
included, is not this module's business and resolves normally, out of a guarded directory as well.

WHERE IT IS INSTALLED, and why in two places rather than one:
  * `_gate.py`, the launcher every registered enforcement hook of this kit runs behind. That is
    what makes the protection a property of the REGISTRATION rather than of a set of hook names:
    it is in force before the launcher compiles or executes a gate at all, so it covers the hooks
    that never import `_kernel` (`gate_pipeline`, `gate_test_coverage`, `guard_no_adhoc`,
    `guard_question_context`, `guard_guidelines` reach `re`/`subprocess` on their own).
    `tools/test_hooks_v2.py::test_every_refusal_capable_registered_hook_runs_through_the_launcher`
    is what keeps that true for a hook added later.
  * `_kernel.py`, so a hook started DIRECTLY — the test suite, a person diagnosing one — is still
    guarded if it uses the bridge. What that leaves open is stated in `_gate.py` beside the same
    residual for `-B`: a hook run directly AND without `_kernel` has no guard.

THE BOOTSTRAP IS THE POINT OF THIS FILE'S IMPORT LIST. It imports `os` and `sys` and nothing else,
and it reaches `PathFinder` through `sys.meta_path` rather than through `import importlib` —
because that import is itself a standard-library import, and it would run a planted `importlib.py`
BEFORE the guard exists. Measured 2026-08-11: with the guard installed via
`import importlib.machinery`, a planted `importlib.py` executed. `sys` is built in and `os` is
imported by the interpreter's own start-up before any file of this directory can be reached, so
neither can be shadowed by a plant here.
"""
import os
import sys


def _path_finder():
    """The importer on `sys.meta_path` that resolves a name against `sys.path`, or None.

    Taken from `sys.meta_path` rather than imported: see the module docstring for why no
    `import importlib` may stand in front of this guard. None means nothing here reads `sys.path`,
    and then nothing ON `sys.path` can shadow anything — the caller has nothing to install.
    """
    for entry in sys.meta_path:
        if getattr(entry, "__name__", None) == "PathFinder" and hasattr(entry, "find_spec"):
            return entry
    return None


class _StandardLibraryWins(object):
    """Resolves a standard-library name with the guarded directories taken off `sys.path`.

    WHAT IT MAY NOT DO is refuse a legitimate import out of a guarded directory, which is why the
    question is this narrow. The other end — that no module this kit SHIPS is named after a
    standard-library module, or this finder would replace the kit's own module with the standard
    one — is pinned by
    `tools/test_hooks_v2.py::test_no_kit_module_is_named_after_a_standard_library_module`.
    """

    def __init__(self):
        self.directories = ()

    def _owns(self, entry):
        """Is this `sys.path` entry inside a guarded directory?

        `""` is resolved as the working directory, which is what the import system reads it as; a
        guarded directory that happens to BE the working directory would otherwise keep answering
        through the empty entry.
        """
        try:
            resolved = os.path.normcase(os.path.abspath(entry or os.getcwd()))
        except (OSError, ValueError):
            return False
        for directory in self.directories:
            try:
                base = os.path.normcase(os.path.abspath(directory))
            except (OSError, ValueError):
                continue
            if resolved == base or resolved.startswith(base + os.sep):
                return True
        return False

    def find_spec(self, fullname, path=None, target=None):
        # `path is not None` is a SUBMODULE lookup: it is resolved against the parent package's
        # own `__path__`, never against `sys.path`, so nothing here can shadow it.
        if path is not None or fullname.partition(".")[0] not in sys.stdlib_module_names:
            return None
        delegate = _path_finder()
        if delegate is None:
            return None
        clean = [entry for entry in sys.path if not self._owns(entry)]
        if len(clean) == len(sys.path):
            return None
        return delegate.find_spec(fullname, clean, target)


_GUARD = _StandardLibraryWins()


def install(directories):
    """Guard `directories`, and put the finder in front of `PathFinder`. Idempotent.

    Directories ACCUMULATE rather than replace: the launcher and `_kernel` both install, and a
    second call that dropped the first caller's directory would silently unguard it.
    """
    _GUARD.directories = tuple(sorted(set(_GUARD.directories) | {str(d) for d in directories}))
    if _GUARD in sys.meta_path:
        return
    delegate = _path_finder()
    if delegate is None:
        return  # nothing consults sys.path, so nothing on it can shadow anything
    sys.meta_path.insert(sys.meta_path.index(delegate), _GUARD)


def guarded_directories():
    """What is guarded right now — for a caller that wants to REPORT it, never to decide by it."""
    return _GUARD.directories
