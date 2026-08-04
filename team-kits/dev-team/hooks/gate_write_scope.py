#!/usr/bin/env python3
"""
Write-scope gate — gate layer 3 of spec II.4, and the home of both preconditions the approval
protocol depends on.

Three jobs, all on PreToolUse — the only event that can actually refuse. Registered
PreToolUse(Edit|Write|MultiEdit|NotebookEdit) for the tool writes and PreToolUse(Bash|PowerShell)
for the shell that writes the same files; the table below says which job belongs to which, and it
says it that way round because the matcher spelling belongs in settings.json, where a test reads
it, and not a second time here, where the last widening of it left this table a tool short:

  the write tools        1. `project_memory/**` is KERNEL-ONLY: no tool writes canonical state,
                            not even the orchestrator's. The one exception is `staging/**`, which
                            spec II.4 defines as explicitly non-canonical — and there a bound
                            specialist may write only under ITS OWN task's key.
                         2. a bound specialist writes only inside its task's `allowed_scope` and
                            never inside `forbidden_scope`; an UNBOUND subagent writes nothing,
                            because there is no scope to check it against.
  the shell              3. RULE 1, plus RULE 4 below, for the shell — shell writes bypass
                            Edit/Write hooks entirely (guard_harness_selfmod has said so
                            since V1), and the
                            approval protocol's condition (i) is exactly "an agent cannot invoke
                            the hooks or the kernel directly". `handle_shell` decides on what the
                            COMMAND LINE names; it never resolves the bound task, so RULE 2 —
                            `allowed_scope`/`forbidden_scope` — does not exist on this path.
                            Measured 2026-07-31 with a bound specialist whose `allowed_scope` is
                            empty: `echo pwned > src/x.py`, `rm -rf src` and `git commit -am wip`
                            pass all eight registered Bash gates, while the same target refuses
                            through Write. The line above said "the same two rules" and had said
                            it since the gate shipped. The gap is pinned, not merely written
                            down: `tools/test_hooks_v2.py` asserts it as a `known_hole` on
                            `state_write_protection.shell`, which is what keeps
                            `python scripts/harness.py doctor` from reporting that capability
                            green.
                         4. a SUBAGENT may not run the harness commands that ORDER work. See
                            `_ORDERING_COMMANDS` for what that is and how narrow it is; the
                            constitution row it makes true is the DELEGATE/ROUTE step of every
                            kit's work loop, which reserves creating the `TSK` to the lead.

WHY THE STATE DIR IS ABSOLUTE, no orchestrator exemption: `approvals/pending/**` holds mint codes
in cleartext, and a writable pending file mints a real approval with a self-consistent consumed
request behind it — the one forgery the provenance check cannot detect. `guard_pm_scope` still
ALLOWS `project_memory/**` for the lead, because in V1 the lead was the state's writer; in V2 the
kernel is, and this gate closes the tool paths to it — every Edit/Write/MultiEdit/NotebookEdit
and every shell write a command line reveals.

WHAT THIS CANNOT CLOSE, measured rather than assumed: an agent that may execute arbitrary code
can always reach the kernel. This gate refuses what a command LINE reveals — an enforcement hook in
an execution position, a copy of the enforcement layer, `python -c` importing the kernel, a
write-capable command naming the state dir. It does NOT refuse a script the agent wrote (or copied)
to an ordinary path and then ran, nor an interpreter reached indirectly (`$(which python)`, `xargs`,
a heredoc).

AND IT DOES NOT REFUSE A WRITE VERB OF THE TOOL'S OWN LANGUAGE. Measured 2026-08-03:
`sed -n 'w kk/g.py' .claude/hooks/gate_approval.py` copies a shipped gate and exits 0 here. The
`_PROGRAM_ARG_VERBS` branch catches a shell REDIRECT OPERATOR hidden inside a quoted program
(`awk 'BEGIN{print > "f"}'`), which is the same `>` this gate already reasons about; `sed`'s `w`,
`awk`'s `print > f` variants, `jq`'s output builtins, `perl -e open`, `python -c` — those are
write verbs of five different LANGUAGES, and the only way to refuse them from a command line is a
list of each language's writing words, which is the shape of check this repo keeps proving wrong
one release later. It stays open on purpose, on the same footing as the rest of this paragraph:
the containment is the permission posture, not a bigger vocabulary. `tools/test_hooks_v2.py`
asserts it as a `known_hole` on `state_write_protection.shell`, so `python scripts/harness.py
doctor` cannot report that capability green while it stands.

RULE 4 REACHES EXACTLY AS FAR AS A COMMAND LINE DOES, which is the same boundary as everything
above it and is worth saying beside the constitution row it backs: a subagent that writes a script
into its own `allowed_scope` and runs it reaches the same kernel functions, and this gate sees a
script name. What IS closed is the typed route and the `python -c` one (`_INLINE_KERNEL_RX`), and
the spawn that a self-made task would exist for is refused outright by `guard_agent_spawn`. So the
row is enforced against the surface a role actually uses and remains policy against a determined
one — not "prevented".

So condition (i) is bounded by the project's PERMISSION posture (settings.json `deny`),
not by hook logic, and `python scripts/harness.py doctor` must weigh that rather than treat this gate's presence as
sufficient. The `known_hole`-marked tests in tools/test_hooks_v2.py enumerate what is still open,
for BOTH capabilities.

NO EXIT FOR A KIT DOCUMENT, AND THE REFUSAL NOW SAYS SO. The entry gate writes the masterplan, the
first root item and `project_config.yaml` by hand, BEFORE the scaffold, when this hook is not
installed yet. It needs no exemption because of that timing — but what follows is a gap, not a
protected window, and until 2026-08-02 the refusal below described it wrongly. Measured in a
scaffolded dev project, all three routes to `product/masterplan.md`: Write rc 2, shell heredoc rc 2,
and `grep -rn masterplan .claude/kernel/*.py` finds no writer at all — while the remedy sent the
role to `python scripts/harness.py <command>`, a surface that has none. `gate_memory_complete`
meanwhile blocks merge AND push for as long as the file carries its template line, and the office
kit's `filing_plan.yaml` is the same class of file.

So the refusal distinguishes the two cases with `kernel.layout.is_project_document` — a definition
derived from the kernel writers' own path builders, not a list of file names. For canonical state
the remedy is the entry point, as before; for a kit document it says plainly that NO command writes
it and that the gap is the user's to close outside the session, which is what §0 of all three
constitutions already instructs ("a gap you report, not an edit you make"). The permission itself is
unchanged: §0 is a constitutional rule that this gate is the enforcement of, and widening it is a
constitution change, not a hook change.
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

import re  # noqa: E402
import shlex  # noqa: E402 — everything after GATE_PREAMBLE, which must stay verbatim

import _compat  # noqa: E402

HOOK = "gate_write_scope"
# NotebookEdit included: a notebook write is a file write, and a gate that does not see it scopes
# everything except notebooks (`_compat.file_paths` reads `notebook_path` for the same reason).
FILE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
SHELL_TOOLS = ("Bash", "PowerShell")
# the ONE non-canonical subtree inside the state dir (spec II.4 "Vorschlagsbereich")
STAGING = "staging"

# inline python reaching into the kernel LIBRARY. An import/attribute shape, not a bare word, so
# `python -c "print('kernel panic')"` is not a forgery accusation.
_INTERPRETER = r"(?:^|[\s|&;=(\"'/\\])(?:python[0-9.]*|py|pythonw)(?:\.exe)?"
_INLINE_KERNEL_RX = re.compile(
    _INTERPRETER + r"\s+(?:-[^\s]+\s+)*-c\b[^\n]*"
    r"(?:\b(?:from|import)\s+kernel\b|\bkernel\.(?:approvals|state|dispatch|staging)\b)",
    re.IGNORECASE)
# A commit/tag/issue MESSAGE is prose, and prose naming a protected path is not a write into it.
# `--body`/`-F` included: the remedy text asks the agent to REPORT a gate defect, and an issue body
# quoting the command would otherwise be refused by the gate it is reporting.
_MESSAGE_ARG_RX = re.compile(
    r"(?:-m|--message|-Message|--description|--body|-b|--notes|-F)\s*=?\s*"
    r"""(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')""",
    re.IGNORECASE)


def _norm(path):
    """Case-folded, then forward-slashed — in that ORDER.

    The FS on Windows is case-insensitive, so a lexical comparison that is not was no comparison at
    all (`Project_Memory/**` was writable). And `ntpath.normcase` turns a forward slash back into
    a backslash, so slashing first and normcasing second silently undoes the slashing.
    """
    # .lower() as well as normcase: normcase is IDENTITY on darwin, and APFS is
    # case-insensitive by default, so a Windows-only fold would leave macOS exposed
    # (guard_harness_selfmod uses an unconditional .lower() for the same reason).
    return os.path.normcase(str(path)).replace("\\", "/").lower()


def _repo_relative(path, root):
    """(rel, undecidable). `rel` is the repo-relative, normcased path; `undecidable` says the
    comparison could not be made at all.

    REALPATH, not abspath: a directory junction (`mklink /J pm project_memory`, no admin needed)
    and an extended-length `\\\\?\\C:\\...` spelling both reach the same file while looking like
    another path. `_root.find_repo_root` stays lexical on purpose — only the TARGET side needs
    resolving, exactly as `_kernel._same_file` argues.
    """
    try:
        target = os.path.realpath(os.path.abspath(str(path)))
        rel = os.path.relpath(target, os.path.realpath(root))
    except (OSError, ValueError):
        return None, True
    rel = _norm(rel)
    if rel.startswith("../"):
        return None, False  # genuinely outside the repo -- other guards own that
    return rel, False


def _state_relative(rel):
    """The path relative to the state dir, or None when it is outside."""
    state = _norm(_kernel.STATE_DIRNAME)
    if rel == state:
        return ""
    prefix = state + "/"
    return rel[len(prefix):] if rel.startswith(prefix) else None


def _scope_entries(task, field):
    """Scope entries, normalised. Refuses a blank entry rather than reading it as "everything".

    `allowed_scope: [""]` (or `"."`, or `"/"`) used to grant the whole repo, while the
    empty-LIST case correctly blocked -- one stray `- ""` in a YAML list silently switched gate
    layer 3 off for that task, which is the opposite of the author's intent two lines away.
    """
    entries = []
    for raw in task.get(field) or []:
        entry = str(raw).replace("\\", "/")
        # strip a literal "./" prefix -- `lstrip("./")` strips a character SET, which turned
        # ".env" into "env" and ".github/workflows/" into "github/workflows/"
        while entry.startswith("./"):
            entry = entry[2:]
        entry = _norm(entry).strip().rstrip("/")
        if entry in ("", ".", "*"):
            _kernel.block(
                HOOK,
                "%s has an unusable %s entry (%r): blank, `.`, `/` and a bare `*` cannot "
                "mean anything definite, and were read as 'the whole repository' -- refused "
                "instead (spec II.4 is fail-closed). Write `**` if that is really the intent."
                % (task["id"], field, raw),
                remedy="name real paths; re-plan the task in DRAFT to fix its work order.")
        entries.append(entry)
    return entries


def _matches(rel, entry):
    """Prefix match, or glob match when the entry uses `*`.

    Globs are supported rather than rejected because `**` is the notation everywhere a PM reads it
    -- the constitution row, guard_pm_scope's message and this gate's own docstring all write
    `project_memory/**`. Treating it as literal text made `allowed_scope: ["src/**"]` a dead task
    and `forbidden_scope: ["secrets/**"]` silently unprotected.
    """
    if "*" not in entry:
        return rel == entry or rel.startswith(entry + "/")
    pattern = "".join(
        ".*" if part == "**" else ("[^/]*" if part == "*" else re.escape(part))
        for part in re.split(r"(\*\*|\*)", entry))
    # no trailing `(?:/.*)?`: with it, `src/*` matched `src/sub/deep/a.py` and a bare `*`
    # granted the whole repo at any depth -- only `**` may widen.
    return re.fullmatch(pattern, rel) is not None


def _bound_task(data, root):
    """The task the calling agent is bound to, or None.

    `agent_id` is present only inside a subagent call (verified in a real run and by spike S3), so
    a missing one means the ORCHESTRATOR -- scoped by guard_pm_scope, not here.
    """
    if not os.path.isdir(_kernel.state_dir(root)):
        return None
    agent_id = data.get("agent_id")
    if not agent_id:
        return None
    dispatch = _kernel.kernel_module("dispatch")
    return dispatch.task_for_agent(_kernel.open_state(root), agent_id)


def _assert_not_forbidden(rel, task):
    """`forbidden_scope` is checked BEFORE the staging exemption.

    Otherwise the two branches were exclusive and a forbid could never reach a state path, so a
    `forbidden_scope` naming the state dir was a silent no-op. A PM must be able to deny staging to
    a task -- and does so by naming it: `project_memory/staging/`, or `project_memory/` for the
    whole tree. Note that forbidding `project_memory/` therefore denies STAGING too, which is the
    honest reading; canonical state is already unconditional, so a forbid there would be redundant
    if it meant anything less.
    """
    if task is None:
        return
    for entry in _scope_entries(task, "forbidden_scope"):
        if _matches(rel, entry):
            _kernel.block(HOOK, "'%s' is in %s's forbidden_scope (%s)." % (rel, task["id"], entry),
                          remedy="this path is out of bounds for this task; report it instead of "
                                 "working around it.")


def _is_project_document(root, inside):
    """Is this state-relative path a kit DOCUMENT rather than canonical state?

    Asked of `kernel.layout`, which derives it from the kernel writers' own path builders — this
    gate must not carry a second opinion about what the kernel writes, and least of all a list of
    the three file names that surfaced the dead end.

    A kernel that cannot be reached answers NO, which keeps the refusal: `_kernel.kernel_module`
    raises `KernelUnavailable` and the preamble turns that into exit 2 anyway, but the explicit
    fallback says which direction this predicate fails in.
    """
    try:
        layout = _kernel.kernel_module("layout")
    except Exception:  # noqa: BLE001 — no kernel, no carve-out (fail-closed)
        return False
    return layout.is_project_document(_kernel.state_dir(root), inside)


def _assert_state_write_allowed(rel, inside, task, data, root):
    """The state dir is the kernel's. Only `staging/<own key>/` is an agent's to write."""
    parts = [p for p in inside.split("/") if p]
    if not parts or parts[0] != _norm(STAGING):
        if _is_project_document(root, inside):
            # A KIT DOCUMENT, and the honest refusal for one. Sending a role to the entry point
            # here was the measured defect: no `harness.py` command writes this file, so the
            # remedy named a route that does not exist and the merge gate that reads the file
            # blocked forever. §0 of every constitution already says what to do instead.
            _kernel.block(
                HOOK,
                "'%s' is a kit DOCUMENT inside the write-locked state directory — prose or "
                "configuration, not a typed item. Being a document is no exception: this gate "
                "refuses the write (constitution §0), and NO `python scripts/harness.py` command "
                "writes it either — the kernel has a path builder for every canonical file and "
                "none for this one. So there is no route from inside this session, and this "
                "refusal is not one to work around." % rel,
                remedy="report the gap to the user and name this file. It is filled by the entry "
                       "gate BEFORE the kit is installed, or by the user in an editor outside "
                       "this session; `init_project_memory` is copy-if-absent and will not "
                       "overwrite what they write. If a merge gate is blocking on its content, "
                       "say that in the same breath — retrying the write or the push changes "
                       "nothing.")
        _kernel.block(
            HOOK,
            "'%s' is canonical project state — only the kernel writes it (spec II.4). A tool write "
            "here would bypass the status automaton, the approval hashes and the index; and "
            "`approvals/pending/**` in particular holds mint codes, so a writable one forges a "
            "user approval outright." % rel,
            remedy="write it through the entry point: `python scripts/harness.py <command>`, "
                   "run from the project root and never with `--root` (this gate refuses a "
                   "write-capable pipeline that NAMES the state directory, and the entry point "
                   "resolves it itself). `python scripts/harness.py --help` lists the surface it "
                   "HAS, and is the ONLY authority on it -- this message used to name the members "
                   "and went stale the day three commands shipped, which is how a role learns that "
                   "an operation with a command has none. "
                   "`approve` is SPLIT rather than absent: `request-approval` opens the "
                   "kernel-generated question and the USER mints it by answering, which is "
                   "why no command mints. What spec II.4 names and the surface still lacks is "
                   "`migrate --dry-run`; that one is a gap to report. Proposals that are not "
                   "canonical yet belong in project_memory/staging/<task-id>/.")
    if len(parts) < 2:
        _kernel.block(HOOK, "'%s' would write the staging ROOT — staging is keyed per task or per "
                            "root item (spec II.4)." % rel,
                      remedy="write to project_memory/staging/<task-id>/<file>.")
    key = parts[1]
    if task is not None:
        # spec II.4 names BOTH keys: `staging/<task_id>/` for a specialist's proposal and
        # `staging/<ROOT-ID>/` for a pre-task artefact (the class-small WFR before scope approval)
        own = {_norm(task["id"]), _norm(task.get("product_requirement") or "")}
        if key not in own:
            _kernel.block(
                HOOK,
                "'%s' writes another task's staging area: this agent holds %s (root %s), not %s. "
                "Staging is per task so one specialist's proposal cannot be mistaken for another's."
                % (rel, task["id"], task.get("product_requirement"), key),
                remedy="write under project_memory/staging/%s/." % task["id"])
    elif data.get("agent_id"):
        _kernel.block(
            HOOK,
            "'%s': this subagent is not bound to any task, so there is no staging key it owns "
            "(spec II.4 gate 3). It was either started outside the dispatch gate, or two same-role "
            "dispatches made its binding ambiguous and the kernel refused to guess." % rel,
            remedy="dispatch the specialist through the harness; dispatch tasks of the SAME role "
                   "sequentially.")


def _assert_in_scope(rel, task):
    """A bound specialist writes only where its work order says (spec II.4 gate 3)."""
    allowed = _scope_entries(task, "allowed_scope")
    if not allowed:
        _kernel.block(HOOK, "%s has an empty allowed_scope, so nothing is in scope for it "
                            "(fail-closed)." % task["id"],
                      remedy="re-plan the task in DRAFT with an allowed_scope.")
    if any(_matches(rel, entry) for entry in allowed):
        return
    _kernel.block(
        HOOK,
        "'%s' is outside %s's allowed_scope (%s) — refused. A specialist writes what its work "
        "order says it writes; anything else is a scope change, and scope changes are the user's."
        % (rel, task["id"], ", ".join(allowed)),
        remedy="if this file really belongs to the task, re-plan it in DRAFT; otherwise report the "
               "gap rather than widening it.")


def handle_file_write(data):
    root = _kernel.find_repo_root(data.get("cwd"))
    paths = _compat.file_paths(data)
    if not paths:
        sys.exit(0)
    task = _bound_task(data, root)
    for path in paths:
        rel, undecidable = _repo_relative(path, root)
        if undecidable:
            _kernel.block(
                HOOK,
                "'%s' cannot be resolved against this repo, so it cannot be checked against the "
                "state directory or a task scope — refused rather than skipped (spec II.4 "
                "fail-closed)." % path,
                remedy="use a normal path inside the project.")
        if rel is None:
            continue  # genuinely outside the repo -- other guards own that question
        _assert_not_forbidden(rel, task)
        inside = _state_relative(rel)
        if inside is not None:
            _assert_state_write_allowed(rel, inside, task, data, root)
        elif task is not None:
            _assert_in_scope(rel, task)
        elif data.get("agent_id"):
            _kernel.block(
                HOOK,
                "'%s': this subagent is not bound to a task, so it has no write scope at all "
                "(spec II.4 gate 3 is fail-closed — an unattributable write is refused rather "
                "than allowed)." % rel,
                remedy="dispatch specialists through the harness so their writes can be attributed "
                       "to a task; dispatch same-role tasks sequentially.")
    sys.exit(0)


# --- shell analysis -----------------------------------------------------------
#
# Three designs deep, and each rewrite was forced by a measurement rather than taste:
#   1. a list of write VERBS  -> lost to the next verb every time (`cp -r .claude/hooks` refused,
#      `cp -r .claude` allowed one token away)
#   2. inverted, regex-split  -> a PIPE was read as a segment boundary, so `cat <hook> | tee copy`
#      and `ls .claude/hooks/*.py | xargs rm -f` passed — the second DELETES the enforcement layer
#   3. this one: TOKENISE first, then judge a whole PIPELINE as one unit.
# Tokenising also fixes the mirror-image failure: a quoted `|` (`grep -E 'PR|SR' project_memory/x`)
# was split into nonsense and refused, i.e. the gate blocked the exact inspection its own message
# promises stays allowed.

# Protected trees, derived from ONE list so the shell rule and guard_harness_selfmod cannot drift:
# these are the paths that guard already refuses to Edit/Write.
_ENFORCEMENT_PATHS = (".claude", ".codex", ".agents/skills", ".github/hooks", ".github/agents")
# `.github/workflows` is deliberately NOT here: guard_harness_selfmod allows it, and a shell rule
# stricter than the file rule teaches an agent to route around the shell.
_ENFORCEMENT_RX = re.compile(
    r"(?:^|[\s\"'=(/\\])(?:%s|team-kits)(?=[\\/\s\"';|&]|$)"
    % "|".join(re.escape(p).replace("/", r"[\\/]") for p in _ENFORCEMENT_PATHS),
    re.IGNORECASE)
_STATE_RX = re.compile(r"\bproject_memory\b", re.IGNORECASE)

# Verbs that cannot modify anything. Everything NOT here counts as write-capable — the fail-closed
# direction: a tool nobody has classified is refused until someone decides it is safe.
_READ_ONLY_VERBS = frozenset((
    "cat", "type", "bat", "head", "tail", "less", "more", "wc", "nl", "od", "xxd", "strings",
    "grep", "egrep", "fgrep", "rg", "ag", "ack", "diff", "cmp", "comm", "file", "stat",
    "ls", "dir", "tree", "basename", "dirname", "realpath", "readlink", "pwd", "du", "df",
    "sort", "uniq", "cut", "tr", "jq", "yq", "test", "echo", "printf", "base64", "awk",
    # conditionally read-only -- see _WRITE_FLAGS, which is what actually decides for these
    "sed", "find",
    "md5sum", "sha1sum", "sha256sum", "cd", "pushd", "popd",
    # PowerShell
    "get-content", "get-childitem", "select-string", "test-path", "get-item", "resolve-path",
    "get-filehash", "compare-object", "measure-object", "select-object", "set-location",
    # `Out-Null` is the null device in cmdlet form — the same definition `_null_sinks` states for
    # the redirect form, reached through a pipe instead of a `>`, and retaining just as little.
    "out-null",
    # analysers
    "ruff", "mypy", "pylint", "flake8", "yamllint",
))
# ...but three of them write when given the right flag, so the verb alone is not the answer.
_WRITE_FLAGS = {
    # long forms spelled out: `"--in-place".startswith("-i")` is False, so the short-flag test
    # alone let `sed --in-place` rewrite canonical state -- and a LIVE hook, which disarms the
    # gate rather than merely copying it
    "sed": ("-i", "--in-place"),
    "find": ("-delete", "-exec", "-execdir", "-fprint", "-fls", "-ok"),
    "awk": ("-i", "--in-place"),
    "sort": ("-o", "--output"),
}
# verbs whose PROGRAM is an argument, so a redirect can hide inside a quoted token where no `>`
# token ever appears (`awk 'BEGIN{print "x" > "state.yaml"}'`)
_PROGRAM_ARG_VERBS = frozenset(("awk", "gawk", "mawk", "sed", "perl", "ruby", "jq"))


# An OUTPUT REDIRECT, as a shape rather than as the spellings that happened to be listed: an
# optional file descriptor or `&` (both streams), then `>` or `>>`, then bash's optional
# force-clobber `|`. The tuple that stood here knew `>`, `>>` and `2>` and knew neither `&>` nor
# `>|`, so `cat .claude/hooks/gate_approval.py &> copy.py` and `... >| copy.py` produced no target
# at all — a read-only verb, no redirect, allowed — while the very same relocation spelled `>` was
# refused. `>&` deliberately does not match: `2>&1` duplicates a DESCRIPTOR, and its right-hand
# side is a stream number, not a file anything lands in.
#
# THIS ONE FAILS OPEN, and that is the opposite of `_null_sinks` below — read the two together.
# There, a spelling the code does not know stays a WRITE, so the set can only be too small and the
# cost is a false refusal. Here, a form the shape does not match is not a redirect at all, the
# pipeline looks read-only, and the bytes land wherever they were sent. So this shape must stay
# WIDER than any spelling in use, over-matching is the safe direction (`>>|` is meaningless to
# bash and matches anyway), and every future shell operator that lands bytes in a file is a hole
# until it is added here. Two forms are known to be outside it and are outside it deliberately:
# `>&`, above, and the write verbs a TOOL's own language carries — see the module docstring, which
# says why that second one is not this regex's problem to solve.
_REDIRECT_RX = re.compile(r"^(?:[0-9]*|&)>>?\|?$")


def _has_write_flag(verb, tokens):
    writers = _WRITE_FLAGS.get(verb)
    if not writers:
        return False
    for token in tokens:
        low = token.lower()
        for writer in writers:
            if low == writer or low.startswith(writer + "="):
                return True
            # short-flag cluster (`sed -ni`), but only for real single-letter flags
            if (len(writer) == 2 and writer.startswith("-") and low.startswith("-")
                    and not low.startswith("--") and writer[1] in low[1:]):
                return True
    return False
# `git` is read-only in these subcommands. `add` is included deliberately: it writes the INDEX, not
# the worktree, and refusing `git add .claude/agents/x.md` while `git add -A` stages the same file
# is an artefact, not a policy — it also blocked the documented model:/effort: resync from ever
# being committed.
_READ_ONLY_GIT = frozenset((
    "diff", "log", "show", "status", "grep", "ls-files", "blame", "cat-file", "rev-parse",
    "describe", "shortlog", "config", "add",
))
# git's global options that CONSUME an argument -- without skipping them, `git -C project_memory
# log` read the subcommand as "project_memory"
_GIT_OPTS_WITH_ARG = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path")
# `python -m <analyser>`: the analysers cannot write. `pytest` is absent from BOTH this and
# _READ_ONLY_VERBS -- it executes arbitrary code, and allowing one spelling while refusing the
# other was the inconsistency, not the strictness.
_READ_ONLY_MODULES = frozenset(("mypy", "ruff", "flake8", "pylint", "pydoc", "json.tool"))
_PIPELINE_SEPARATORS = ("&&", "||", ";")
# `\n` is NOT in that tuple, and must not be: shlex treats a newline as whitespace, so it never
# becomes a token. A newline entry there was dead code, and multi-line commands merged into ONE
# pipeline -- prefixing any refused command with `echo start` defeated the whole rule. Newlines are
# rewritten to `;` before tokenising instead (heredoc bodies are already gone by then). The line
# CONTINUATION that is not a separator comes from `_compat.join_line_continuations` — one rule,
# one place, and it covers the PowerShell backtick this hook's own copy never did.
_HEREDOC_RX = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?^\2\s*$",
                         re.MULTILINE | re.DOTALL)


# Every value an ordinary shell could hand the program for a word — `_compat.shell_readings`, which
# is where the two readings and the reason for them are stated. Aliased rather than wrapped: a
# second name for one rule is how the two copies of the last one drifted.
_readings = _compat.shell_readings


def _operator(token):
    """`token` when the shell would read it as PUNCTUATION, "" when quoting produced it.

    The mirror of `_tokenise`: once the quote marks are gone, `echo '>' file` and `echo > file`
    spell the same three characters, and only the second one redirects. Every punctuation test in
    this gate goes through here, so the two questions ("what does this word SAY" and "is this word
    SYNTAX") cannot drift apart.
    """
    return "" if getattr(token, "spliced", False) else str(token)


def _lex(masked):
    """The masked line split into tokens, with shell punctuation as tokens of its own.

    `punctuation_chars=True` makes `&&`, `||`, `;`, `|`, `>`, `>>` their own tokens even without
    surrounding spaces, and the masked spans keep `'PR|SR'` and `'%h -> %s'` one token each — a
    quoted pipe is not a pipeline and a quoted arrow is not a redirect.
    """
    try:
        lexer = shlex.shlex(masked, posix=False, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return masked.split()  # unbalanced quotes: fall back rather than crash


def _tokenise(command):
    """Tokens as the SHELL resolves them — `_compat.shell_words` with this gate's lexer.

    THE COMPARISON READS THE RESOLVED STRING, NOT THE TYPED ONE, and `_compat` carries why, with
    the measurement: a splice anywhere in the DIRECTORY part of a path defeated every prefix check
    in this gate at once (`echo x > '.cl'aude/hooks/gate_write_scope.py` — allowed by all
    registered gates, file overwritten in a real bash), while the same path spelled plainly was
    refused. `$C/hooks/...` looked covered only because the assignment `C=.claude` names the tree
    in the same line.

    What the resolution costs this gate is one distinction it has to keep making for itself: a word
    that RESOLVES to `>` is not a redirect. `_operator` is that, and every punctuation test here
    goes through it.
    """
    return _compat.shell_words(command, _lex)


def _pipelines(tokens):
    """Group tokens into pipelines. A `|` does NOT start a new pipeline: it is a data channel, so
    stage 1 may name a protected path while stage 2 does the writing."""
    current, out = [], []
    for token in tokens:
        if _operator(token) in _PIPELINE_SEPARATORS:
            if current:
                out.append(current)
            current = []
        else:
            current.append(token)
    if current:
        out.append(current)
    return out


def _stage_verb(stage):
    for token in stage:
        low = str(token).lower()
        if "=" in low and not low.startswith("-"):
            continue  # VAR=value prefix
        if low in ("sudo", "env", "command", "exec", "time", "nice", "!"):
            continue
        if _operator(token).lower() in ("(", ")", "{", "}", "&", "&&", "||", ";", "|"):
            continue  # grouping punctuation is not a verb
        return os.path.basename(low.replace("\\", "/"))
    return ""


def _stage_is_read_only(stage):
    verb = _stage_verb(stage)
    if _has_write_flag(verb, stage[1:]):
        return False
    # a REDIRECT OPERATOR hiding INSIDE the quoted program, where no `>` token ever appears. The
    # shell's OWN redirect operators are excluded from the search, or this branch would answer for
    # them too and answer wrongly: `awk '{print $1}' .claude/settings.json 2>/dev/null` has a `>`
    # token and no embedded redirect at all, and calling the stage write-capable for it put these
    # six verbs outside the null-sink rule that every other read-only verb now follows.
    # An operator is ALL this looks for: `sed -n 'w kk/g.py'` writes a file with no `>` anywhere
    # and passes — see the module docstring, which states why that stays open.
    if verb in _PROGRAM_ARG_VERBS and any(">" in t for t in stage[1:]
                                          if not _REDIRECT_RX.match(_operator(t))):
        return False
    if verb.startswith("python") or verb in ("py", "pythonw"):
        for index, token in enumerate(stage[:-1]):
            if token == "-m":
                return stage[index + 1].strip("\"'").lower() in _READ_ONLY_MODULES
        return False
    if verb == "git":
        rest = list(stage[1:])
        while rest and rest[0].startswith("-"):
            option = rest.pop(0)
            if option in _GIT_OPTS_WITH_ARG and rest:
                rest.pop(0)
        return bool(rest) and rest[0].lower() in _READ_ONLY_GIT
    return verb in _READ_ONLY_VERBS


# --- rule 4: ordering work is the orchestrator's act -------------------------
#
# WHAT MAKES A SUBCOMMAND "ORDERING" rather than "writing", because the wider split does not
# survive contact: the commands a specialist hands its OWN finished work back with write too, and
# it has to be able to run them — so "the writing ones, except those" would be two lists holding
# each other up. The property is narrower and it is the one the work loop states: an ordering
# command CREATES THE WORK ORDER somebody executes, or LEASES one for a spawn. In kernel terms
# that is the two producers
# `dispatch.create_task` and `dispatch.create_lease`, and the CLI routes reaching them are what
# stands below.
#
# THE MAP IS DERIVED, NOT TYPED, and that is what keeps it from being the next stale tuple:
# `tools/test_hooks_v2.py::test_the_ordering_commands_are_the_cli_routes_to_the_task_producers`
# parses `kernel/cli.py` and asserts these keys ARE the `args.command` branches that reach those
# two functions. A fourth route added to the CLI turns that test red on the day it ships.
# The value narrows a command by its first positional (`capture` reaches the task producer only
# for `TSK`; `capture EVD` is an ordinary item and stays allowed); an empty value means the
# subcommand qualifies on its own.
_ORDERING_COMMANDS = {"create-task": (), "capture": ("tsk",), "dispatch": ()}
# `os.path.basename(kernel.cli.ENTRY_POINT)` and the module spelling of the same CLI. Both are
# pinned against the kernel by the same test — the gate keeps its own copy so that a Bash call does
# not pay for importing argparse and every field schema just to answer "is this the harness".
_HARNESS_SCRIPT = "harness.py"
_KERNEL_CLI_MODULE = "kernel.cli"


def _harness_argv(stage):
    """The argument list a stage hands to the kernel CLI, or None when it is not a CLI invocation.

    STRUCTURAL, never a bare word anywhere in the line: `grep -rn create-task docs/` and
    `cat scripts/harness.py` name the same strings and order nothing, and refusing a role's own
    reading is how a gate teaches people to route around it. So the entry point has to be in an
    EXECUTION position — the stage's verb is a python, or the script itself is the verb.
    """
    tokens = [str(t) for t in stage]
    verb = _stage_verb(stage)
    pythonish = verb.startswith("python") or verb in ("py", "pythonw")
    if not pythonish and verb != _HARNESS_SCRIPT:
        return None
    for index, token in enumerate(stage):
        # EVERY reading, for the reason `_tokenise` gives: `scripts/'har'ness.py` and
        # `scripts/har\\ness.py` both start the entry point, and rule 4 read neither as it.
        if any(os.path.basename(reading.replace("\\", "/")).lower() == _HARNESS_SCRIPT
               for reading in _readings(token)):
            return tokens[index + 1:]
    if pythonish:
        for index, token in enumerate(tokens[:-1]):
            if token == "-m" and tokens[index + 1].lower() == _KERNEL_CLI_MODULE:
                return tokens[index + 2:]
    return None


def _ordering_command(stage):
    """The ordering subcommand this stage would run, or "".

    The subcommand is the FIRST POSITIONAL, which is what argparse reads too. A `--root
    project_memory` in front of it shifts that position and this returns nothing — deliberately
    not compensated for here: the installed shim refuses `--root` outright, and a pipeline naming
    the state directory is already refused by rule 1, so compensating would be a second opinion
    about a line that never reaches the kernel.
    """
    argv = _harness_argv(stage)
    if not argv:
        return ""
    positional = [str(token) for token in argv if not token.startswith("-")]
    if not positional:
        return ""
    command = positional[0].lower()
    if command not in _ORDERING_COMMANDS:
        return ""
    qualifiers = _ORDERING_COMMANDS[command]
    if not qualifiers:
        return command
    if len(positional) > 1 and positional[1].lower() in qualifiers:
        return "%s %s" % (command, positional[1].lower())
    return ""


def _null_sinks(tool):
    """The redirect targets that RETAIN NOTHING for this shell on this host.

    The question a redirect raises is not which operator was used but whether the bytes end up
    somewhere a reader can pick them up. Exactly one target is DEFINED to keep nothing — the
    operating system's discard device — so redirecting into it is the shell suppressing output,
    which is a read-side concern; every other target keeps the bytes and is a write, including an
    unprotected one (`cat <hook> > copy.py` is the relocation this gate exists to refuse).

    PER SHELL AND PER HOST, because the same word is a device in one and an ordinary FILE in
    another, and getting that backwards would open the hole this closes. Measured 2026-08-03 on
    this Windows host: PowerShell has no `/dev/null` — it resolves a leading-slash path against the
    CURRENT DRIVE, and a redirect into one landed its bytes in a real file there, so `> /dev/null`
    on any host carrying `C:\\dev` is the relocation this gate refuses, spelled to look harmless.
    Git Bash meanwhile discarded both `> /dev/null` and `> NUL`, the latter because `nul` is a
    Win32 reserved device name no file can be created under. On POSIX the reverse holds: `> NUL`
    there is an ordinary file in the working directory.

    A SPELLING THIS DOES NOT KNOW STAYS A WRITE (`nul:`, `\\\\.\\NUL`, a shell alias), so the set can
    only be too small — the cost of that is a false refusal a user can report, not a route out of
    the tree.
    """
    # `os.devnull` is Python's name for the device of the host this gate runs on — `/dev/null` on
    # POSIX, `nul` on Windows — so the base of the set is a definition rather than a spelling.
    names = {_norm(os.devnull)}
    if tool == "PowerShell":
        names.add("$null")
    elif os.name == "nt":
        names.add("/dev/null")  # the Bash tool on Windows is a POSIX shell over a Win32 filesystem
    return names


def _redirect_targets(tokens, sinks):
    """Targets of an output redirect that RETAIN what is written — see `_null_sinks`.

    PER TARGET, not per pipeline: `cat <hook> > /dev/null > copy.py` still has one retaining
    target and is still refused. The `sinks` argument has no default on purpose — a caller that
    forgot it would silently get the old, over-refusing behaviour back.
    """
    targets = []
    for index, token in enumerate(tokens[:-1]):
        if _REDIRECT_RX.match(_operator(token)):
            target = tokens[index + 1]
            if _norm(target) not in sinks:
                targets.append(target)
    return targets


def _names(rx, tokens):
    """Does any word of `tokens` name this tree, under ANY reading a shell could give it?"""
    return any(rx.search(reading) for token in tokens for reading in _readings(token))


# An INPUT redirect, and only the file form of it: `<`, `0<`. `<<` opens a here-document and `<<<`
# a here-string — neither names a file to read — and `<&` duplicates a descriptor.
_INPUT_REDIRECT_RX = re.compile(r"^[0-9]*<$")
# The one subtree of the state directory a proposal legitimately comes OUT of. Spec II.4 defines
# `staging/**` as explicitly non-canonical: what is written there is a draft, and the only thing
# anyone can do with a draft is hand it to the kernel.
_STAGING_SOURCE_RX = re.compile(r"project_memory[\\/]+staging[\\/]", re.IGNORECASE)


def _read_sources(pipeline, stages):
    """The tokens of this pipeline that name a file it READS rather than one it writes.

    Two shapes, and they are the two the shell has: the operand of an INPUT redirect, and an
    argument of a stage whose verbs cannot modify anything (`_stage_is_read_only`, which already
    answers for a write FLAG on an otherwise read-only verb). A read-only stage's own redirect
    TARGETS are excluded — `cat a > b` reads `a` and writes `b`, and counting `b` here would hand
    the carve-out below exactly the relocation it must refuse.
    """
    sources = set()
    for index, token in enumerate(pipeline[:-1]):
        if _INPUT_REDIRECT_RX.match(_operator(token)):
            sources.add(str(pipeline[index + 1]))
    for stage in stages:
        if not stage or not _stage_is_read_only(stage):
            continue
        written = {index + 1 for index, token in enumerate(stage[:-1])
                   if _REDIRECT_RX.match(_operator(token))}
        sources.update(str(token) for index, token in enumerate(stage)
                       if index and index not in written)
    return sources


def _only_reads_staging(pipeline, stages):
    """Is EVERY mention of the state directory in this pipeline a read of `staging/**`?

    THE ROUTE OUT OF `staging/` IS THIS ONE, and without it there is none. The architect role has
    no shell to run the kernel with by design: it leaves a proposal in `staging/<task-id>/` and the
    lead books it in. Both spellings the kits document for that hand the file to the entry point as
    STANDARD INPUT — `python scripts/harness.py capture SR < project_memory/staging/…` and
    `cat project_memory/staging/… | python scripts/harness.py capture SR` — and both were refused,
    measured against the real hook: the pipeline can write (the entry point is not a read-only
    verb) and it names the state directory, which is all rule 1 asked. So the proposal directory
    the spec puts inside the state tree had no exit at all.

    A READ IS NOT A WRITE, and that is the whole of the widening — the direction every part of it
    keeps narrow:
      * only `staging/**`, never a canonical path. `capture < project_memory/product/active/…`
        stays refused: reading canonical state INTO a writing pipeline is how a forged item would
        be smuggled back in through the entry point's own door.
      * only when the state directory is named NOWHERE ELSE. One redirect TARGET, one `cp`
        destination, one argument of a writing verb, and this answers no.
      * a word that is a read source AND a redirect target is not a read: `capture < staging/a.json
        > staging/a.json` names one string twice, and membership alone would have read the second
        mention off the first and opened a shell write INTO the state tree.
      * never once a `cd` has put the pipeline inside the state tree, because a relative target
        there names nothing this reader can compare (see the caller).
    """
    named = [token for token in pipeline if _names(_STATE_RX, [token])]
    if not named:
        return False
    sources = _read_sources(pipeline, stages)
    written = {str(pipeline[index + 1]) for index, token in enumerate(pipeline[:-1])
               if _REDIRECT_RX.match(_operator(token))}
    return all(str(token) in sources and str(token) not in written
               and all(_STAGING_SOURCE_RX.search(reading) for reading in _readings(token)
                       if _STATE_RX.search(reading))
               for token in named)


def _walk(pipeline, cwd):
    """The working directory a `cd`/`pushd`/`popd` leaves us in, or None when it is unknown.

    Tracking the PATH rather than a depth, because the two cheaper models each got a real case
    wrong: a boolean could not tell "left the tree" from "went deeper into it", and a depth counter
    could not enter a TWO-SEGMENT tree in two steps (`cd .github && cd hooks` armed nothing,
    because `.github` alone is not a protected path) nor unwind inside one argument
    (`cd project_memory/../src` counted as entering). A path answers all three by construction:
    whether we are inside a protected tree is then the same question the direct-naming check asks.

    None means "somewhere we cannot name" -- an absolute target, a bare `cd`, `cd -`, or `popd`.
    Conservatively treated as outside: over-blocking every command after a `popd` would refuse
    ordinary work, and the direct-naming check still covers anything that spells the path out.
    """
    verb = _stage_verb(pipeline)
    if verb == "popd":
        return None
    args = [t for t in pipeline[1:] if not t.startswith("-")]
    if not args or args[0] == "-":
        return None  # bare `cd` (home) or `cd -` (previous)
    # OF THE READINGS THIS WORD HAS, THE ONE THAT LANDS IN A PROTECTED TREE. Same doctrine as
    # `_names`: the text does not say which shell runs it, and a gate that is unsure must see the
    # reading that matters — `cd .cl\\aude` really enters the enforcement layer in a POSIX shell,
    # and reading it as an ordinary directory name armed nothing for the write that followed.
    readings = _readings(args[0])
    target = next((r for r in readings
                   if _ENFORCEMENT_RX.search(r) or _STATE_RX.search(r)), readings[0])
    target = target.replace("\\", "/")
    if (target.startswith("/") or target.startswith("~")
            or (len(target) > 1 and target[1] == ":")):
        return None  # absolute: outside anything we can reason about relatively
    segments = [] if cwd is None else [p for p in cwd.split("/") if p]
    for segment in [p for p in target.split("/") if p not in ("", ".")]:
        if segment == "..":
            if not segments:
                return None  # walked out above the point we were tracking from
            segments.pop()
        else:
            segments.append(segment)
    return "/".join(segments)


def _inside(rx, cwd):
    return bool(cwd) and rx.search(cwd) is not None


def handle_shell(data):
    command = str((data.get("tool_input") or {}).get("command") or "")
    if not command.strip():
        sys.exit(0)
    # message ARGUMENTS and heredoc BODIES removed: both are prose. Stripping ALL quoted spans
    # would remove the target path of every real write (`echo x > "project_memory/a.yaml"`), and
    # leaving heredoc bodies in made each of their LINES look like a command.
    code_view = _HEREDOC_RX.sub(" ", _MESSAGE_ARG_RX.sub(" ", command))
    # a continued line is ONE command; every other newline is a command separator that shlex
    # would otherwise swallow as whitespace. The continuation is removed, not spaced — this hook
    # kept its own copy of that rule and its own copy of the bug, so `echo x >
    # project_mem\<newline>ory/approvals/APR-0001.yaml` read as two words and named no state path.
    code_view = _compat.join_line_continuations(code_view).replace("\n", " ; ")
    # DEPTH, not a boolean: assigning a flag on every `cd` could not tell "left the tree" from
    # "went deeper into it", so `cd project_memory && cd approvals && echo x > a.yaml` wiped the
    # very flag that should have blocked it.
    # the working directory, relative to the repo root, as the pipelines walk it
    cwd = _repo_relative(data.get("cwd") or ".", _kernel.find_repo_root(data.get("cwd")))[0] or ""
    # WHICH SHELL decides which redirect targets keep the bytes — see `_null_sinks`.
    sinks = _null_sinks(data.get("tool_name"))
    # WHO IS ASKING (rule 4). One definition for the whole kit — `_compat.calling_subagent` carries
    # the measurement and the reason it tests truthiness rather than key presence.
    caller = _compat.calling_subagent(data)
    for pipeline in _pipelines(_tokenise(code_view)):
        stages, current = [], []
        for token in pipeline:
            if _operator(token) == "|":
                stages.append(current)
                current = []
            else:
                current.append(token)
        stages.append(current)
        if caller:
            for stage in stages:
                ordered = stage and _ordering_command(stage)
                if ordered:
                    _kernel.block(
                        HOOK,
                        "`%s` ORDERS work, and this call comes from a subagent (%s). Creating the "
                        "task or leasing one for a spawn is the orchestrator's act: the work "
                        "order, its `allowed_scope` and the lease are the lead's judgements "
                        "to make, and a specialist that makes them for itself is authorising "
                        "itself." % (ordered, caller),
                        remedy="hand the need BACK instead: name it in `followups` of your "
                               "result envelope and let the lead order it. Nothing you run to "
                               "report, prove or return your OWN work is affected by this rule; "
                               "`python scripts/harness.py --help` is the authority on what the "
                               "surface has.")
        verbs_read_only = all(_stage_is_read_only(stage) for stage in stages if stage)
        redirects = _redirect_targets(pipeline, sinks)
        # a redirect that RETAINS makes a pipeline write-capable whatever its verbs: `echo x > f`
        # writes. A redirect into the null device retains nothing and is therefore not one — see
        # `_null_sinks` for why that is a property of the target and not a list of harmless forms.
        writes = not verbs_read_only or bool(redirects)
        names_enforcement = _names(_ENFORCEMENT_RX, pipeline) or _inside(_ENFORCEMENT_RX, cwd)
        names_state = _names(_STATE_RX, pipeline) or _inside(_STATE_RX, cwd)
        if names_enforcement and writes:
            # a RETAINING redirect counts even to an unprotected target: `cat <hook> > copy.py` IS
            # the relocation this refuses. Suppressing output is not that, and this branch used to
            # make no distinction — measured three times in one lifecycle run, each on a pure read
            # (`ls .claude/agents/ 2>/dev/null`), each costing the role a detour. What separates
            # the two is `_null_sinks`, and NOT the state branch's `captures_out` carve-out: that
            # one allows a read-only pipeline to redirect into any unprotected file, which is
            # precisely `cat <hook> > copy.py`.
            _refuse(pipeline, "the enforcement layer",
                    "Hooks and settings are maintained by the scaffold, never by hand — and a copy "
                    "of the layer runs outside every path check, which is the shortest measured "
                    "route to a forged approval.",
                    "reading it (cat/grep/diff/ruff/mypy) stays allowed, including with the output "
                    "suppressed (`2>/dev/null`, `> NUL`, `> $null`); what is refused is the bytes "
                    "LANDING somewhere — a copy, a redirect into a real file, an in-place edit. If "
                    "a gate blocks something legitimate, that is an infrastructure defect worth "
                    "reporting.")
        if names_state and writes:
            # ONE carve-out: a read-only command capturing state to a scratch file outside both
            # protected trees. `git diff project_memory > /tmp/state.diff` is how an agent reports
            # on state, and refusing it teaches nothing except to work around the gate.
            # ...but NOT once a `cd` has put us inside the state dir: there a relative redirect
            # target names nothing and still lands in canonical state
            captures_out = (verbs_read_only and redirects and not _inside(_STATE_RX, cwd)
                            and not _inside(_ENFORCEMENT_RX, cwd)
                            and not _names(_ENFORCEMENT_RX, redirects)
                            and not _names(_STATE_RX, redirects))
            # ...and the mirror of it on the way IN: a proposal being handed to the entry point.
            # Both carve-outs stand down inside the state tree for the same reason — there a
            # relative path names the tree without spelling it, so nothing here can compare it.
            reads_staging = (not _inside(_STATE_RX, cwd) and not _inside(_ENFORCEMENT_RX, cwd)
                             and _only_reads_staging(pipeline, stages))
            if not captures_out and not reads_staging:
                _refuse(pipeline, "the canonical state directory",
                        "project_memory has exactly one writer, the kernel — and a shell write is "
                        "the path that bypasses every Edit/Write guard.",
                        "use the entry point (`python scripts/harness.py <command>`, from the "
                        "project root; `python scripts/harness.py --help` lists the surface); "
                        "non-canonical proposals go to project_memory/staging/<task-id>/.")
        if _stage_verb(pipeline) in ("cd", "pushd", "popd", "set-location"):
            # everything after `cd project_memory` is inside it, and the later pipelines no longer
            # NAME it -- that shape walked straight past a path-only check. Mirrored for the
            # enforcement layer, whose `cd .claude && cp -r hooks /tmp` had no carry-over at all.
            cwd = _walk(pipeline, cwd)
    if _INLINE_KERNEL_RX.search(code_view):
        _kernel.block(
            HOOK,
            "this command reaches into the state kernel with inline python. The kernel's vetted "
            "surface is the installed entry point, which goes through the status automaton and "
            "the approval checks; an ad-hoc import goes around them.",
            remedy="use `python scripts/harness.py <command>` — installed kit-owned in every "
                   "scaffolded project and run from the project root. Do NOT add `--root`: this "
                   "gate refuses a write-capable pipeline that names the state directory, and "
                   "the entry point resolves it itself. Importing the kernel package by its own "
                   "name is no alternative either — it installs under `.claude/`, so that import "
                   "fails in a project. `python scripts/harness.py --help` lists the surface; a "
                   "command spec II.4 names and the surface lacks is a gap to report, never one "
                   "to route around this gate for.")
    sys.exit(0)


def _refuse(pipeline, what, why, remedy):
    _kernel.block(HOOK, "this command names %s in a pipeline that can write (`%s`). %s"
                  % (what, " ".join(pipeline)[:160], why), remedy=remedy)


def main():
    data = _kernel.payload(HOOK)
    # The early exit is what makes the missing `fail_closed(HOOK, event)` re-entry safe: every
    # reachable block() below really is a PreToolUse block, so the audit label cannot lie. Widening
    # this filter (e.g. registering the gate on PermissionRequest) MUST add the re-entry, or the
    # mislabelling gate_dispatch documents comes back.
    if str(data.get("hook_event_name") or "PreToolUse") != "PreToolUse":
        sys.exit(0)
    tool = data.get("tool_name")
    if tool in FILE_TOOLS:
        handle_file_write(data)
    elif tool in SHELL_TOOLS:
        handle_shell(data)
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
