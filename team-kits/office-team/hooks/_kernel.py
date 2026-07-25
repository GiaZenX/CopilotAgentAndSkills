#!/usr/bin/env python3
"""
Shared helper: the ONE bridge from a hook process to the V2 state kernel (spec II.4).

Every V2 integrity gate needs the same four things, and each of them has exactly one correct
answer — so none of them is left to the individual hook:

  1. WHERE the kernel package is (it travels with the enforcement layer, but the harness repo
     runs its own hooks straight from the checkout — see kernel_parents()),
  2. WHERE the canonical state lives (`<repo>/project_memory`),
  3. what "empty or unreachable state" means (BLOCK — spec II.4 fail-closed; the V1
     `gate_proc_approved` bootstrap hole, where an empty store let every spawn through, is
     exactly the failure this closes),
  4. what an INTERNAL error means (also BLOCK: a hook that crashes is treated by Claude Code as
     a hook that permitted the call, so a bare traceback silently disarms the gate).

FAIL-CLOSED IS ABOUT EXIT CODE 2, NOT ABOUT "non-zero". Claude Code blocks on 2 and treats every
other code as a non-blocking error — the call proceeds. An uncaught exception exits 1, i.e.
ALLOW. That is why this module does three things a single try/except cannot:
  * `fail_closed()` catches BaseException (re-raising only SystemExit), so KeyboardInterrupt and
    MemoryError block instead of exiting 1 or 3221225786;
  * a `sys.excepthook` installed at import time turns anything raised outside the guard —
    module-level code in the gate, a failed kernel import, a half-finished kit update — into an
    exit 2 as well;
  * `block()` degrades to `os._exit(2)` if even the stderr write fails.

That covers everything AFTER `import _kernel` has SUCCEEDED — and the gap is not academic: this
module imports `_root`, `_audit` and `_compat` itself, so a half-written sibling helper (the most
likely artifact of exactly the interrupted kit update cited above) breaks `import _kernel`, the
excepthook is never installed, and the process exits 1 = allow. Nothing inside this file can fix
that, because it is not running. Every V2 gate therefore OPENS with the GATE_PREAMBLE constant
defined below — the only construct that survives its own HELPERS being broken. Copy it from the
constant, never retyped from prose; `tools/test_hooks_v2.py` asserts that every shipped V2 gate
starts with it verbatim, so it cannot be forgotten.

One boundary remains open, and it is named here so it stays a decision rather than a discovery:
the preamble cannot cover the GATE FILE ITSELF failing to compile. A gate truncated mid-write —
just as plausible an artifact of an interrupted kit update as a truncated helper — raises
SyntaxError before its first statement runs, so neither preamble nor excepthook is reached, and
the process exits 1 = allow. Nothing inside a Python file can close that; it closes one level up,
by invoking gates through a launcher whose own compile is the only one that must succeed. That
belongs to the settings.json wiring, not here.

Fail-open stays legal for COMFORT hooks only (formatting, notifications, dashboards, spec II.4);
they must not use `fail_closed()` and pass `tolerate_overflow=True` to `_compat.load()`.

LATENCY, deliberately traded (spec II.5): importing the kernel pulls in PyYAML (~tens of ms).
The spec asks integrity gates to be stdlib-first "wo vermeidbar" and puts latency at a MEASURED
p95 target (~300 ms, warn 500 ms) that is explicitly NOT a blocking gate. Hand-rolling a YAML
subset parser inside a fail-closed path would trade a measurable few tens of milliseconds for an
unmeasurable correctness risk in the one code path that must never be wrong. If the CI bench
shows the p95 target missed, the fix is a JSON sidecar written by the kernel — not a second
parser for the same files.
"""
import contextlib
import importlib
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _root import find_repo_root  # noqa: E402
import _audit  # noqa: E402
import _compat  # noqa: E402

STATE_DIRNAME = "project_memory"
KIT_STATE_FILE = "kit_state.json"
# every hook process that reaches the kernel must agree on this name; the package uses relative
# imports, so what goes on sys.path is always the PARENT of the `kernel` directory
KERNEL_PKG = "kernel"
# a bootstrap window is minutes of installer work, never a standing permission (spec II.4)
BOOTSTRAP_MAX_TTL = 3600.0
# extensions a canonical state artifact can carry (spec II.2 file structure): typed items and
# approvals are YAML, frozen design revisions are HTML, ARC/WFR diagrams are .drawio.svg
CANONICAL_SUFFIXES = (".yaml", ".yml", ".html", ".drawio.svg")


class KernelUnavailable(RuntimeError):
    """The state kernel could not be located or imported — integrity gates BLOCK on this."""


def _same_file(left, right):
    """Path identity for TWO PATHS TO ONE FILE.

    Deliberately realpath+normcase, unlike `_root.find_repo_root`, which stays lexical on
    purpose (resolving junctions would change path identity for prefix-comparing guards). Here
    the question is the opposite one — "is this the same file?" — and case matters: _root
    uppercases the drive letter while a sys.path entry keeps whatever case it was given, so a
    plain string compare reports the SAME kernel as a foreign installation.
    """
    if not left or not right:
        return False
    try:
        return (os.path.normcase(os.path.realpath(left))
                == os.path.normcase(os.path.realpath(right)))
    except OSError:
        return False


def kernel_parents(repo_root):
    """Candidate sys.path entries holding the `kernel` package, most specific first.

    - $HARNESS_KERNEL_PATH: explicit override (tests, installers, side-by-side V2 RC). It is
                            AUTHORITATIVE, not merely first: an override that silently falls back
                            to some other installation is the "enforced against the wrong state"
                            hazard in a different costume.
    - <repo>/.claude:       scaffolded project — the kernel travels with hooks + settings, so a
                            project always runs the kernel its hook bundle was hashed against
    - <repo>/team-kits:     the harness repo itself, running its own kits from the checkout
    - ~/.claude/team-kits:  the installed kit bundle
    """
    override = os.environ.get("HARNESS_KERNEL_PATH")
    if override:
        return [override]
    candidates = []
    if repo_root:
        candidates.append(os.path.join(repo_root, ".claude"))
        candidates.append(os.path.join(repo_root, "team-kits"))
    candidates.append(os.path.join(os.path.expanduser("~"), ".claude", "team-kits"))
    return candidates


def import_kernel(repo_root=None):
    """Import and return the `kernel` package. Raises KernelUnavailable with a remedy."""
    repo_root = repo_root or find_repo_root()
    overridden = bool(os.environ.get("HARNESS_KERNEL_PATH"))
    tried = []
    for parent in kernel_parents(repo_root):
        init = os.path.join(parent, KERNEL_PKG, "__init__.py")
        tried.append(parent)
        if not os.path.isfile(init):
            continue
        existing = sys.modules.get(KERNEL_PKG)
        if existing is not None:
            # a hook process imports the kernel exactly once; a DIFFERENT kernel already in
            # sys.modules means two installations are in play, and silently preferring either
            # one would enforce against state the other wrote
            found = getattr(existing, "__file__", None)
            if found and not _same_file(found, init):
                raise KernelUnavailable(
                    "kernel already imported from %s but this repo resolves to %s — refusing to "
                    "enforce with a foreign kernel. Remedy: run `harness doctor`; a stale "
                    "$HARNESS_KERNEL_PATH or a half-finished kit update is the usual cause."
                    % (found, init)
                )
            # re-import of an already-loaded module is a no-op, but it repairs the one state
            # Python leaves behind after a FAILED `import kernel.state` (package present,
            # submodule absent) — without it open_state() degrades to a bare AttributeError
            _import_kernel_state(init)
            return existing
        # INSERT, then pop again in `finally`. Both halves are load-bearing. Inserting at 0 is
        # what makes the resolved kernel win the import; appending instead (tried once) let any
        # earlier sys.path entry with a `kernel` package take over — a decoy planted via
        # PYTHONPATH, a site-packages distribution of that name, a stray `.claude/hooks/kernel/`
        # — and gates were handed a foreign ProjectState with no error at all. Popping it right
        # after closes the window in which `<repo>/.claude` would shadow a stdlib module for the
        # rest of the process; submodules keep resolving afterwards via the package's own
        # __path__, so `kernel_module()` is unaffected.
        added = parent not in sys.path
        if added:
            sys.path.insert(0, parent)
        try:
            _import_kernel_state(init)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    sys.path.remove(parent)
        module = sys.modules[KERNEL_PKG]
        # belt and braces: prove what we got is what we resolved. `isfile(init)` only proved a
        # kernel EXISTS there; nothing so far proved the import produced that one.
        if not _same_file(getattr(module, "__file__", None), init):
            raise KernelUnavailable(
                "resolved the kernel at %s but the import produced %s — refusing to enforce with "
                "a kernel this repo did not install. Remedy: something earlier on sys.path "
                "(PYTHONPATH, a site-packages package named `kernel`, a stray copy inside the "
                "repo) shadows it; remove it, then re-run `harness doctor`."
                % (init, getattr(module, "__file__", None) or "<unknown>")
            )
        return module
    if overridden:
        raise KernelUnavailable(
            "$HARNESS_KERNEL_PATH points at %s, which holds no `kernel` package — refusing to "
            "enforce without a kernel. Remedy: fix or unset $HARNESS_KERNEL_PATH; while it is "
            "set it is the ONLY candidate, by design." % tried[0]
        )
    raise KernelUnavailable(
        "no state kernel found (looked in: %s). Remedy: re-run the team scaffold for this repo "
        "— the kernel travels with the enforcement layer; without it no integrity gate can "
        "verify anything, so every gated call is refused." % ", ".join(tried)
    )


def _import_kernel_state(init):
    """Import `kernel.state` eagerly (every caller needs it) with an accurate failure message."""
    try:
        importlib.import_module(KERNEL_PKG + ".state")
    except ImportError as exc:
        raise KernelUnavailable(
            "found the kernel at %s but a dependency is missing (%s: %s). Remedy: the kernel "
            "needs PyYAML — `pip install pyyaml` in the interpreter that runs the hooks "
            "(`python -c \"import yaml\"` reproduces it)." % (init, type(exc).__name__, exc)
        ) from None
    except Exception as exc:
        raise KernelUnavailable(
            "found the kernel at %s but importing it failed (%s: %s) — the kernel itself is "
            "damaged. Remedy: `git status` on the kit; a half-finished kit update or a partial "
            "checkout is the usual cause, and re-running the scaffold restores it."
            % (init, type(exc).__name__, exc)
        ) from None


def kernel_module(name, repo_root=None):
    """Import one kernel submodule on demand (`dispatch`, `approvals`, `report`, ...).

    Kept lazy per module so a gate pays only for what it actually needs — the whole point of the
    latency note above is that the import cost is bounded and known, not that it is free.
    """
    import_kernel(repo_root)
    return importlib.import_module("%s.%s" % (KERNEL_PKG, name))


def state_dir(repo_root=None):
    """Absolute path of the canonical state directory (may not exist yet)."""
    return os.path.join(repo_root or find_repo_root(), STATE_DIRNAME)


def state_is_empty(repo_root=None):
    """True when there is no canonical state at all — the ONE precondition for bootstrap.

    Defined as "no canonical artifact anywhere", not as a list of allowed top-level names:
    everything the kernel writes ALONGSIDE the state carries a non-canonical extension
    (`.kernel.lock` and its `.stale-*` remnants, `.audit/*.jsonl`) and `generated/**` is
    regenerable by definition. Name-listing was tried first and was wrong twice over — it
    excluded a `.lock` the kernel never creates, and an empty typed directory tree left by the
    scaffold would have closed the installer's own gate before it wrote its first item.

    CANONICAL_SUFFIXES covers more than the YAML items on purpose: spec II.2 puts frozen design
    revisions (`design/revisions/DSN-0001.html`) and the draw.io ARC/WFR artifacts in the state
    too, and a project whose YAML items were archived but whose approved revisions remain is
    emphatically not a greenfield install.

    `staging/**` is COUNTED, although spec II.4 calls it explicitly non-canonical. Deliberate:
    the question here is not "is this canonical?" but "is this a greenfield repo?", and a
    proposal in staging proves work in flight. The error direction is the safe one — it can only
    ever close the bootstrap window, never open it.
    """
    root = state_dir(repo_root)
    if not os.path.isdir(root):
        return True
    generated = os.path.join(root, "generated")
    for directory, _subdirs, files in os.walk(root):
        if directory == generated or directory.startswith(generated + os.sep):
            continue
        if any(name.lower().endswith(CANONICAL_SUFFIXES) for name in files):
            return False
    return True


def bootstrap_active(repo_root=None):
    """True only during an explicit, still-valid installer/migration bootstrap (spec II.4).

    Spec: "aktivierbar nur über den expliziten Installer-/Migrationsbefehl mit Lock, leerem
    Zielzustand und Userbestätigung" — deliberately NOT a config flag the lead could set to
    unblock itself. Enforced here:
      * the target state must be empty (the real teeth: once one canonical item exists, no
        marker re-opens the gate),
      * the marker must record an installer run and an explicit user confirmation,
      * its TTL is capped at BOOTSTRAP_MAX_TTL, so a marker cannot grant standing permission,
      * `.claude/kit_state.json` is on guard_harness_selfmod's blocked list, so an agent cannot
        write the marker with an ordinary Edit/Write in the first place.
    """
    repo_root = repo_root or find_repo_root()
    if not state_is_empty(repo_root):
        return False
    try:
        with open(os.path.join(repo_root, ".claude", KIT_STATE_FILE), encoding="utf-8") as fh:
            marker = (json.load(fh) or {}).get("bootstrap")
    except Exception:
        return False
    if not isinstance(marker, dict):
        return False  # a truthy non-dict must not raise its way past the caller's error handling
    if marker.get("user_confirmed") is not True:
        return False
    if not str(marker.get("installer_run") or "").strip():
        return False
    try:
        expires = float(marker.get("expires_at_epoch", 0))
    except (TypeError, ValueError):
        return False
    now = time.time()
    return now < expires <= now + BOOTSTRAP_MAX_TTL


def open_state(repo_root=None):
    """The ProjectState for this repo. Raises KernelUnavailable when there is no state dir."""
    repo_root = repo_root or find_repo_root()
    kernel = import_kernel(repo_root)
    root = state_dir(repo_root)
    if not os.path.isdir(root):
        raise KernelUnavailable(
            "no canonical state at %s — refusing to authorise anything against a state that "
            "does not exist (spec II.4 fail-closed). Remedy: initialise the project state via "
            "the installer/scaffold, which is the only path that may run with an empty state."
            % root
        )
    return kernel.state.ProjectState(root)


_PAYLOAD_CACHE = []


def payload(hook, event="PreToolUse"):
    """Bounded, normalized hook payload for an integrity gate.

    `hook` is required and comes first: with an optional name the natural positional call
    `payload("gate_dispatch")` would bind the hook NAME to `event` and silently lose the gate's
    identity. Overflow blocks inside `_compat.load()`; see STDIN_LIMIT there.

    Two properties beyond a plain `_compat.load()`, both for the same reason — every gate in this
    repo is shaped `if data.get("tool_name") != X: sys.exit(0)`, which turns an empty dict into
    ALLOW:

    * an UNREADABLE payload blocks. `_compat.load()` returns `{}` for unparseable stdin, and
      "could not be inspected" must not read as "permitted" (spec II.4: "leerer, beschädigter
      oder unbekannter Zustand blockiert"). This is the same door as the overflow case, one step
      further in.
    * the result is MEMOISED. stdin can only be drained once, so a gate that grows a helper
      calling `payload()` a second time — and a dispatch gate with a header to parse, a task to
      resolve and a scope to check is exactly that shape — would otherwise get `{}` from the
      second read and decide on it.
    """
    if not _PAYLOAD_CACHE:
        _PAYLOAD_CACHE.append(_compat.load())
    data = _PAYLOAD_CACHE[0]
    if not data:
        block(hook,
              "the hook payload could not be read or parsed, so this call could not be "
              "inspected — refused rather than waved through (spec II.4 fail-closed).",
              event=event,
              remedy="run `harness doctor`; a provider sending a payload this hook cannot parse "
                     "is a harness defect worth reporting, not something to work around.")
    return data


def record_note(hook, message):
    """Audit something WITHOUT claiming to have prevented it.

    For the events whose exit code cannot block (PostToolUse, PostToolUseFailure, SubagentStart —
    hooks reference, exit-code-2 table). A gate on those events protects state by refusing to
    MUTATE it, and this is how that refusal reaches the audit trail. Using `block()` there would
    exit 2 and look like enforcement in the log while the action went through regardless.
    """
    with contextlib.suppress(BaseException):
        _audit.record_event(hook, "note", message)


# Events whose exit code 2 actually blocks (hooks reference, "exit code 2 behavior" table). The
# rest only surface stderr, so a refusal on them is a REPORT, and the audit line must say so —
# otherwise the log claims prevention that never happened, which is the failure V2 exists to end.
BLOCKING_EVENTS = frozenset((
    "PreToolUse", "PermissionRequest", "UserPromptSubmit", "UserPromptExpansion", "Stop",
    "SubagentStop", "TeammateIdle", "TaskCreated", "TaskCompleted", "ConfigChange",
    "PostToolBatch", "PreCompact", "Elicitation", "ElicitationResult", "WorktreeCreate",
))


def block(hook, message, event="PreToolUse", remedy=None):
    """Refuse the call: audit it, then use this event's provider-specific blocking contract."""
    text = "[team-kit %s] %s" % (hook, message)
    if remedy:
        text += "\nRemedy: %s" % remedy
    if not text.endswith("\n"):
        text += "\n"
    try:
        # labelled from the EVENT, not from the call site: on a non-blocking event this exits 2 and
        # the action still proceeds, so recording it as "block" would put a prevention in the log
        # that did not occur
        _audit.record_event(hook, "block" if event in BLOCKING_EVENTS else "refused-nonblocking",
                            message)
        _compat.stop(text, event)
    except SystemExit:
        raise
    except BaseException:
        # last resort: a block that cannot be written must still BE a block. os._exit skips
        # flushing, so stderr is flushed by hand first.
        with contextlib.suppress(BaseException):
            sys.stderr.write(text)
            sys.stderr.flush()
        os._exit(2)


@contextlib.contextmanager
def fail_closed(hook, event="PreToolUse"):
    """Integrity-gate body guard: ANY internal error becomes a block, never a silent pass.

    Catches BaseException, not Exception: KeyboardInterrupt (a hook timeout, a Ctrl-C) and
    MemoryError are exactly the "everything is already going wrong" moments where an unblocked
    call is worst, and they exit 1 or 3221225786 — both of which Claude Code reads as ALLOW.
    SystemExit passes through untouched; that is how allow (0) and block (2) are signalled.
    """
    try:
        yield
    except SystemExit:
        raise
    except BaseException as exc:
        # NEGATIVE limit: the INNERMOST frames. A positive limit keeps the outermost ones, where
        # frame 1 is always this contextmanager's `yield` — the line that actually failed would
        # be the first thing dropped, which is not a diagnosis.
        detail = traceback.format_exc(limit=-3).strip().replace("\n", " | ")
        block(hook,
              "internal error (%s: %s) — refused rather than passed, because a crashing hook "
              "would otherwise let the call through (spec II.4 fail-closed).\nDiagnosis: %s"
              % (type(exc).__name__, exc, detail),
              event=event,
              remedy="run `harness doctor` for the state view; if the kernel or its state is "
                     "damaged, the doctor output names the file to restore.")


# The literal preamble every V2 gate must open with (see the module docstring for why). Kept
# here as data so the test that enforces it and the gates that carry it cannot drift apart.
GATE_PREAMBLE = '''import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _kernel
except BaseException as exc:  # noqa: BLE001 — a hook that cannot load must not mean "allow"
    sys.stderr.write("[team-kit hook] refused: could not load hook helpers (%r). Remedy: run "
                     "`harness doctor`; a partial checkout or half-finished kit update is the "
                     "usual cause.\\n" % (exc,))
    sys.exit(2)
'''


def run_gate(hook, main, event="PreToolUse"):
    """Entry point for an integrity gate: `_kernel.run_gate("gate_x", main)`.

    Everything the gate does after its preamble — module-level code included, via the excepthook
    — is covered. See GATE_PREAMBLE for the one statement that has to defend itself.
    """
    with fail_closed(hook, event):
        main()
    sys.exit(0)


def reset_payload():
    """Forget the memoised payload (see `payload`).

    The companion to `disarm()`, and for the same constituency: hook processes are one-shot, so
    the memo is invisible to them, but an in-process consumer — a test, a long-lived CLI — would
    otherwise be handed the FIRST payload it ever read for the rest of its life.
    """
    del _PAYLOAD_CACHE[:]


def disarm():
    """Restore the interpreter's normal excepthook.

    For the non-hook consumers of this bridge (a CLI, the dashboard generator, migration
    tooling): armed, an ordinary ValueError would be reported as "the hook itself failed to run"
    and exit via os._exit(2), skipping atexit handlers and buffered-stdout flushes. Arming stays
    the IMPORT-TIME default because the alternative — arming inside run_gate() — would leave a
    gate's own module-level code uncovered, and that is the more dangerous of the two mistakes.
    """
    sys.excepthook = sys.__excepthook__


def _install_excepthook():
    """Turn ANY escaping exception into exit 2, not the default exit 1 (= allow).

    Covers what a context manager structurally cannot: exceptions raised at module scope before
    the gate body runs. It does NOT cover a failure of `import _kernel` itself — see
    GATE_PREAMBLE, which is the part of the answer that cannot live in this file.
    """
    def _hook(exc_type, exc, tb):
        detail = "".join(traceback.format_exception(exc_type, exc, tb, limit=-3))
        with contextlib.suppress(BaseException):
            sys.stderr.write(
                "[team-kit hook] refused: the hook itself failed to run (%s: %s) — a hook that "
                "cannot execute must not be read as permission (spec II.4 fail-closed).\n"
                "Diagnosis: %s\n"
                "Remedy: run `harness doctor`; a partial checkout or a half-finished kit update "
                "is the usual cause.\n" % (exc_type.__name__, exc, detail.strip())
            )
            sys.stderr.flush()
        os._exit(2)

    sys.excepthook = _hook


_install_excepthook()
