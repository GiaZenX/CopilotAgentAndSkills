#!/usr/bin/env python3
"""
Write-scope gate — gate layer 3 of spec II.4, and the home of both preconditions the approval
protocol depends on.

Three jobs, all on PreToolUse (the only event that can actually refuse):

  Edit|Write|MultiEdit   1. `project_memory/**` is KERNEL-ONLY: no tool writes canonical state,
                            not even the orchestrator's. The one exception is `staging/**`, which
                            spec II.4 defines as explicitly non-canonical — and there a bound
                            specialist may write only under ITS OWN task's key.
                         2. a bound specialist writes only inside its task's `allowed_scope` and
                            never inside `forbidden_scope`; an UNBOUND subagent writes nothing,
                            because there is no scope to check it against.
  Bash|PowerShell        3. the same two rules, for the shell — shell writes bypass Edit/Write
                            hooks entirely (guard_harness_selfmod has said so since V1), and the
                            approval protocol's condition (i) is exactly "an agent cannot invoke
                            the hooks or the kernel directly".

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
a heredoc). So condition (i) is bounded by the project's PERMISSION posture (settings.json `deny`),
not by hook logic, and `harness doctor` must weigh that rather than treat this gate's presence as
sufficient. The `known_hole`-marked tests in tools/test_hooks_v2.py enumerate what is still open,
for BOTH capabilities.

No bootstrap exemption either, unlike gate_dispatch -- but NOT because the bootstrap goes through the
kernel. The entry gate writes the masterplan, the first root item and `project_config.yaml` by hand, and
for the prose and the config the kernel has no path at all. It needs no exemption because it runs BEFORE
the scaffold, when this hook is not installed yet. What follows from that is a gap, not a protected
window: once the kit is installed nothing can write those two files, which is why the entry gate is told
to finish them there and every later role is told to report the gap instead of editing a state file.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _kernel
except BaseException as exc:  # noqa: BLE001 — a hook that cannot load must not mean "allow"
    sys.stderr.write("[team-kit hook] refused: could not load hook helpers (%r). Remedy: run "
                     "`harness doctor`; a partial checkout or half-finished kit update is the "
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


def _assert_state_write_allowed(rel, inside, task, data):
    """The state dir is the kernel's. Only `staging/<own key>/` is an agent's to write."""
    parts = [p for p in inside.split("/") if p]
    if not parts or parts[0] != _norm(STAGING):
        _kernel.block(
            HOOK,
            "'%s' is canonical project state — only the kernel writes it (spec II.4). A tool write "
            "here would bypass the status automaton, the approval hashes and the index; and "
            "`approvals/pending/**` in particular holds mint codes, so a writable one forges a "
            "user approval outright." % rel,
            remedy="use the `harness` commands (capture / transition / approve / submit-result / "
                   "archive). Proposals that are not canonical yet belong in "
                   "project_memory/staging/<task-id>/.")
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
            _assert_state_write_allowed(rel, inside, task, data)
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
# rewritten to `;` before tokenising instead (heredoc bodies are already gone by then).
_LINE_CONTINUATION_RX = re.compile(r"\\\s*\n")
_HEREDOC_RX = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?^\2\s*$",
                         re.MULTILINE | re.DOTALL)


def _tokenise(command):
    """Tokens, with quotes preserved and shell punctuation split out.

    `punctuation_chars=True` makes `&&`, `||`, `;`, `|`, `>`, `>>` their own tokens even without
    surrounding spaces, and quoting keeps `'PR|SR'` and `'%h -> %s'` as ONE token each — so a
    quoted pipe is not a pipeline and a quoted arrow is not a redirect.
    """
    try:
        lexer = shlex.shlex(command, posix=False, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return command.split()  # unbalanced quotes: fall back rather than crash


def _pipelines(tokens):
    """Group tokens into pipelines. A `|` does NOT start a new pipeline: it is a data channel, so
    stage 1 may name a protected path while stage 2 does the writing."""
    current, out = [], []
    for token in tokens:
        if token in _PIPELINE_SEPARATORS:
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
        low = token.strip("\"'").lower()
        if "=" in low and not low.startswith("-"):
            continue  # VAR=value prefix
        if low in ("sudo", "env", "command", "exec", "time", "nice", "!"):
            continue
        if low in ("(", ")", "{", "}", "&", "&&", "||", ";", "|"):
            continue  # grouping punctuation is not a verb
        return os.path.basename(low.replace("\\", "/"))
    return ""


def _stage_is_read_only(stage):
    verb = _stage_verb(stage)
    if _has_write_flag(verb, stage[1:]):
        return False
    if verb in _PROGRAM_ARG_VERBS and any(">" in t for t in stage[1:]):
        return False  # a redirect inside the quoted program
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


def _redirect_targets(tokens):
    """Targets of `>`/`>>`, so a read-only command capturing state to /tmp stays possible."""
    targets = []
    for index, token in enumerate(tokens[:-1]):
        if token in (">", ">>") or (token.endswith(">") and token[:-1].isdigit()):
            targets.append(tokens[index + 1].strip("\"'"))
    return targets


def _names(rx, tokens):
    return any(rx.search(token) for token in tokens)


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
    args = [t.strip("\"'") for t in pipeline[1:] if not t.startswith("-")]
    if not args or args[0] == "-":
        return None  # bare `cd` (home) or `cd -` (previous)
    target = args[0].replace("\\", "/")
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
    # message ARGUMENTS and heredoc BODIES removed: both are prose. Stripping all quoted spans
    # (what `git_invocation_text` does) would remove the target path of every real write, and
    # leaving heredoc bodies in made each of their LINES look like a command.
    code_view = _HEREDOC_RX.sub(" ", _MESSAGE_ARG_RX.sub(" ", command))
    # a continued line is ONE command; every other newline is a command separator that shlex
    # would otherwise swallow as whitespace
    code_view = _LINE_CONTINUATION_RX.sub(" ", code_view).replace("\n", " ; ")
    # DEPTH, not a boolean: assigning a flag on every `cd` could not tell "left the tree" from
    # "went deeper into it", so `cd project_memory && cd approvals && echo x > a.yaml` wiped the
    # very flag that should have blocked it.
    # the working directory, relative to the repo root, as the pipelines walk it
    cwd = _repo_relative(data.get("cwd") or ".", _kernel.find_repo_root(data.get("cwd")))[0] or ""
    for pipeline in _pipelines(_tokenise(code_view)):
        stages, current = [], []
        for token in pipeline:
            if token == "|":
                stages.append(current)
                current = []
            else:
                current.append(token)
        stages.append(current)
        verbs_read_only = all(_stage_is_read_only(stage) for stage in stages if stage)
        redirects = _redirect_targets(pipeline)
        # a redirect makes a pipeline write-capable whatever its verbs: `echo x > f` writes
        writes = not verbs_read_only or bool(redirects)
        names_enforcement = _names(_ENFORCEMENT_RX, pipeline) or _inside(_ENFORCEMENT_RX, cwd)
        names_state = _names(_STATE_RX, pipeline) or _inside(_STATE_RX, cwd)
        if names_enforcement and writes:
            # a redirect counts even to an unprotected target: `cat <hook> > copy.py` IS the
            # relocation this refuses
            _refuse(pipeline, "the enforcement layer",
                    "Hooks and settings are maintained by the scaffold, never by hand — and a copy "
                    "of the layer runs outside every path check, which is the shortest measured "
                    "route to a forged approval.",
                    "reading it (cat/grep/diff/ruff/mypy) stays allowed; if a gate blocks something "
                    "legitimate, that is an infrastructure defect worth reporting.")
        if names_state and writes:
            # ONE carve-out: a read-only command capturing state to a scratch file outside both
            # protected trees. `git diff project_memory > /tmp/state.diff` is how an agent reports
            # on state, and refusing it teaches nothing except to work around the gate.
            # ...but NOT once a `cd` has put us inside the state dir: there a relative redirect
            # target names nothing and still lands in canonical state
            captures_out = (verbs_read_only and redirects and not _inside(_STATE_RX, cwd)
                            and not _inside(_ENFORCEMENT_RX, cwd)) and not any(
                _ENFORCEMENT_RX.search(t) or _STATE_RX.search(t) for t in redirects)
            if not captures_out:
                _refuse(pipeline, "the canonical state directory",
                        "project_memory has exactly one writer, the kernel — and a shell write is "
                        "the path that bypasses every Edit/Write guard.",
                        "use the `harness` commands; non-canonical proposals go to "
                        "project_memory/staging/<task-id>/.")
        if _stage_verb(pipeline) in ("cd", "pushd", "popd", "set-location"):
            # everything after `cd project_memory` is inside it, and the later pipelines no longer
            # NAME it -- that shape walked straight past a path-only check. Mirrored for the
            # enforcement layer, whose `cd .claude && cp -r hooks /tmp` had no carry-over at all.
            cwd = _walk(pipeline, cwd)
    if _INLINE_KERNEL_RX.search(code_view):
        _kernel.block(
            HOOK,
            "this command reaches into the state kernel with inline python. The kernel's vetted "
            "surface is the `harness` CLI, which goes through the status automaton and the "
            "approval checks; an ad-hoc import goes around them.",
            remedy="use `harness <command>` (or `python -m kernel.cli <command>`).")
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
