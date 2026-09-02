#!/usr/bin/env python3
"""Repo hygiene: git must not TRACK a file it also IGNORES, a file name must not lie about whose
report it holds, a test must not leave its `sys.path` entry to the next test, a PowerShell
launcher must not be started where nobody asked whether this host has one, and a shipped kit file
must not point at a decision this store no longer holds.

WHY THIS IS THE RIGHT SUBJECT, and not "is ModuleAnalysisCache absent". A `.gitignore` rule has no
effect on a path git already tracks, so a tool trace that was committed once (a PowerShell module
cache under `Microsoft/`, a kit audit log under `project_memory/.audit/` -- both in b32ec98) stays
in every future commit no matter how many rules name it. That is precisely the state BUG-0008 was
in: the rule existed and the file was tracked anyway, so the rule was a promise the tree did not
keep. The invariant that catches it is git's own: the set of TRACKED files and the set of
IGNORED files must be disjoint. Measured with `git ls-files --cached --ignored --exclude-standard`,
which is git resolving `.gitignore` against its own index -- the running behaviour, not a string
search over the file.

THE ONE EXCLUSION IS SCOPED AND REASONED, not an allowlist of paths. `project_memory/` is canonical
state under gate 1 (`gate_lead_write_scope.py`), which refuses every tool write there for every
caller, so a `project_memory/.audit/hook_events.jsonl` that a kit hook subprocess committed cannot
be untracked from a harness session -- `git rm --cached` on it is refused before it runs. It is the
open remainder H37 Rest 2 in `docs/POST_V2_WISHLIST.md`, and the repair belongs in the kit. Anything
tracked-and-ignored OUTSIDE that tree is a new tool trace that must be untracked.
"""
import ast
import glob
import io
import os
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESEARCH = os.path.join(ROOT, "docs", "research")


def _tracked_and_ignored():
    """Paths git both TRACKS and IGNORES, straight from git's own index/attribute resolution."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--ignored", "--exclude-standard"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert result.returncode == 0, result.stderr
    return [line for line in result.stdout.splitlines() if line.strip()]


def test_git_tracks_no_ignored_file_outside_canonical_state():
    """A tracked-and-ignored file is a dead ignore rule (BUG-0008): the file ships regardless.

    Goes red while `Microsoft/Windows/PowerShell/ModuleAnalysisCache` is tracked, which is the
    exact state the `Microsoft/` rule was added into and could not fix on its own -- the file had
    to be untracked (`git rm --cached`) for the rule to mean anything. `project_memory/` is excluded
    because it is gate-protected canonical state a harness session cannot untrack (H37).
    """
    if not shutil.which("git"):
        pytest.skip("git not on PATH")
    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT,
                      capture_output=True, text=True).returncode != 0:
        pytest.skip("not a git work tree")
    offenders = [path for path in _tracked_and_ignored()
                 if not path.startswith("project_memory/")]
    assert not offenders, (
        "git tracks these files while a .gitignore rule ignores them, so the rule is a no-op and "
        "the tool trace ships in every commit -- untrack each with `git rm --cached <path>`: %s"
        % offenders)


def test_the_known_out_of_scope_trace_is_still_the_only_exception():
    """The tripwire on the exclusion above, so it cannot quietly widen or go stale.

    The exclusion earns its place only as long as the audit log is the one thing it covers. If that
    file gets untracked in the kit (H37 closed), this asserts the exception is no longer needed and
    should be removed; if a SECOND ignored file appears under project_memory/, it surfaces here
    rather than hiding behind the prefix.
    """
    if not shutil.which("git"):
        pytest.skip("git not on PATH")
    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT,
                      capture_output=True, text=True).returncode != 0:
        pytest.skip("not a git work tree")
    excused = [path for path in _tracked_and_ignored()
               if path.startswith("project_memory/")]
    assert excused == ["project_memory/.audit/hook_events.jsonl"], (
        "the project_memory/ exclusion in test_git_tracks_no_ignored_file_outside_canonical_state "
        "no longer covers exactly the audit log H37 names -- update the exclusion and H37: %s"
        % excused)


def _shipped_roles():
    """The role names this repo ships, off the kit's own skill directories — never typed here.

    Longest first, so a role whose name is a prefix of another cannot swallow the longer one when
    the two are searched as alternatives.
    """
    skills = os.path.join(ROOT, "team-kits", "dev-team", "skills")
    roles = [name for name in os.listdir(skills) if os.path.isdir(os.path.join(skills, name))]
    assert len(roles) > 3, roles
    return sorted(roles, key=len, reverse=True)


def _role_reports():
    """(file name, role the NAME claims) for every research report named after a shipped role."""
    roles = _shipped_roles()
    for name in sorted(os.listdir(RESEARCH)):
        if not name.endswith(".md") or not os.path.isfile(os.path.join(RESEARCH, name)):
            continue
        claimed = [role for role in roles if name[:-len(".md")].endswith(role)]
        if claimed:
            yield name, claimed[0]


def test_every_research_role_report_is_named_after_the_role_its_own_text_is_about():
    """FR-0009: five of these six carried the name of the NEXT role in the ring.

    THE CONTENT DECIDES, and the rule is one rule for all of them: the FIRST role name a report
    mentions is the role it is about. Every one of these reports opens by naming its subject — in a
    title (`# Rolle \\`product-designer\\``) or in the `Datei:`/`Gelesen:` line that says which
    SKILL.md was read — and the six shipped files agree with that reading unanimously today, which
    is what makes it a rule rather than a guess. The role vocabulary comes from the kit's skill
    directories, so a renamed or a new role moves this check with it.

    WHY A FILE NAME IS WORTH A TEST HERE. These reports are cited by role, opened by role, and
    nothing inside them repeats the file name — so a shifted name is silent: whoever looks up one
    role's findings reads the neighbour's and has no way to notice. The shift survived from
    2026-07-27 until this check, in a repo that measures nearly everything else.

    THE WAY OUT IS NOT OPEN TODAY, and claiming it was would be the over-alarming half of the same
    house rule. A report renamed to something that is not a role name does leave the subject — but
    as long as the shipped set is exactly the floor's size, the floor is an equality in effect and
    that rename trips it. The gap opens with the FIRST report ABOVE the floor, and then silently:
    the count still holds while the renamed one sits unjudged. Both directions are measured in
    `docs/reviews/2026-08-18-tsk0076-measurements.md`. So the floor counts, it does not identify —
    whoever adds a report above it inherits this sentence.
    """
    roles = _shipped_roles()
    pattern = re.compile("|".join(re.escape(role) for role in roles), re.IGNORECASE)
    reports, offences = list(_role_reports()), []
    for name, claimed in reports:
        with open(os.path.join(RESEARCH, name), encoding="utf-8") as handle:
            match = pattern.search(handle.read())
        found = match.group(0).lower() if match else None
        if found != claimed:
            offences.append(
                "%s is filed under `%s` and its own text is about `%s`" % (name, claimed, found))
    assert len(reports) >= 6, (
        "only %d research reports are named after a shipped role — the set was six when this was "
        "written, and a subject that shrinks to nothing is how this check passes over the next "
        "shift: %s" % (len(reports), [name for name, _ in reports]))
    assert not offences, (
        "a research report is filed under the wrong role, so looking up one role's findings hands "
        "over another's and nothing in the file says so:\n  " + "\n  ".join(offences))


_LEAK_SUITE = '''\
import sys

LEAK = "/tsk-0088-leaked-import-path"


def test_one_leaks_an_import_path():
    sys.path.insert(0, LEAK)
    assert LEAK in sys.path


def test_two_must_not_inherit_it():
    assert LEAK not in sys.path, "the previous test's sys.path entry survived into this one"
'''


def test_no_test_in_this_suite_leaks_an_import_path(tmp_path):
    """A test may put a directory on `sys.path`; it may not leave it there for the next test.

    WHY THIS IS THE RIGHT SUBJECT and not "is sys.path short enough": the length that broke is a
    consequence, the leak is the cause. This suite inserts its kits directory from ~100 places with
    a bare `sys.path.insert`, and a dozen tests hand the resulting list to a child process as
    PYTHONPATH; Linux refuses an envp string past MAX_ARG_STRLEN, so on the hosted ubuntu runner
    every scaffold and installer test after the crossing point died with `OSError: [Errno 7]
    Argument list too long: 'bash'` while the Windows leg -- where those tests skip for want of a
    POSIX shell -- reported the same tree green (BUG-0069).

    MEASURED THROUGH A REAL PYTEST PROCESS over this suite's own `conftest.py`, copied rather than
    imported, so what is asserted is the fixture as it ships and not an in-process re-enactment of
    it. Red without `conftest._no_test_leaks_an_import_path`: the second generated test then sees
    the first one's entry.
    """
    shutil.copy(os.path.join(ROOT, "tools", "conftest.py"), str(tmp_path / "conftest.py"))
    with open(str(tmp_path / "test_leak.py"), "w", encoding="utf-8") as handle:
        handle.write(_LEAK_SUITE)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(tmp_path)],
        cwd=str(tmp_path), capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300)
    assert result.returncode == 0, (
        "a test left an entry on `sys.path` for the next one, which is the unbounded growth that "
        "made the hosted ubuntu leg refuse its own PYTHONPATH:\n%s%s"
        % (result.stdout, result.stderr))


_ENVIRONMENT_LEAK_SUITE = '''\
import os

LEAK = "HARNESS_KERNEL_PATH"


def test_one_leaks_an_environment_variable():
    os.environ[LEAK] = "/tsk-0091-leaked-kernel-redirect"
    assert LEAK in os.environ


def test_two_must_not_inherit_it():
    assert LEAK not in os.environ, "the previous test's environment variable survived into this one"
'''


def test_no_test_in_this_suite_leaks_an_environment_variable(tmp_path):
    """A test may set a variable; it may not leave it for the next test -- or its subprocesses.

    THE VARIABLE IN THE FIXTURE IS THE ONE THAT DID IT: `$HARNESS_KERNEL_PATH` redirects the
    entry point at another kernel and is authoritative by design, so a leaked one silently answers
    later tests out of this repo instead of out of the project they built. Measured on pristine
    HEAD: `test_kitupdate.py::test_the_bridge_reads_the_route_off_the_projects_own_entry_point`
    and its neighbour failed in every session where `test_hooks.py` ran first and passed alone.

    MEASURED THROUGH A REAL PYTEST PROCESS over this suite's own `conftest.py`, copied rather than
    imported, like the import-path leak above -- what is asserted is the fixture as it ships. Red
    without `conftest._no_test_leaks_an_environment_variable`: the second generated test sees the
    first one's variable.
    """
    shutil.copy(os.path.join(ROOT, "tools", "conftest.py"), str(tmp_path / "conftest.py"))
    with open(str(tmp_path / "test_env_leak.py"), "w", encoding="utf-8") as handle:
        handle.write(_ENVIRONMENT_LEAK_SUITE)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(tmp_path)],
        cwd=str(tmp_path), capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300)
    assert result.returncode == 0, (
        "a test left an environment variable behind for the next one; every subprocess a later "
        "test starts inherits it, which is how a kernel redirect from one file decided another "
        "file's result:\n%s%s" % (result.stdout, result.stderr))


_LAUNCHERS = ("run", "Popen", "call", "check_call", "check_output")

# The floor under the sweep below. A reader that stops recognising the form finds nothing and
# reports every module clean, which is the shape of check this repo has been burned by twice; the
# number is here so that a narrowing shows up as a failure rather than as silence. It is a FLOOR
# and not an equality on purpose -- sites come and go, blindness does not (BUG-0069).
_POWERSHELL_LAUNCH_FLOOR = 12


def _argv_head(node):
    """The list a command line starts with, past any `[...] + list(args)` concatenation."""
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        node = node.left
    return node


def _unambiguous(assigned, node):
    """`node`, or -- when it is a name this scope assigns exactly one value -- that value."""
    if isinstance(node, ast.Name):
        values = assigned.get(node.id, [])
        return values[0] if len(values) == 1 else node
    return node


def _is_powershell_argv(node, assigned):
    node = _argv_head(_unambiguous(assigned, node))
    if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
        return False
    first = _unambiguous(assigned, node.elts[0])
    return (isinstance(first, ast.Constant) and isinstance(first.value, str)
            and os.path.basename(first.value).lower().rsplit(".exe", 1)[0] == "powershell")


def _powershell_launches(tree):
    """Every `subprocess.*` call in `tree` whose program is the literal `powershell`.

    A name is followed only when every value assigned to it in that scope is such a command line.
    Ambiguity is left OUT rather than guessed at, and both directions of that are deliberate: a
    `command = <ps1 line> if nt else <sh line>` is chosen by the very `os.name` branch the sweep
    would look for, so nothing is lost, while treating it as a subject would flag every
    gate-payload runner that happens to reuse the name `command`.

    A parametrize row whose first element is the TOOL name `PowerShell` is not a command line and
    never reaches here -- the subject is what is handed to `subprocess`, not what looks like it.

    WHERE THIS READER STOPS, said rather than left to be discovered: the program has to be
    READABLE in the source, as a literal or as a name this scope binds to one. A launcher assembled
    at run time -- off a mapping, out of an environment variable, from a `which` result computed
    elsewhere -- is not a subject, and the sweep says nothing about it.
    """
    sites, seen = [], set()
    for scope in [tree] + [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        assigned = {}
        for node in ast.walk(scope):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned.setdefault(target.id, []).append(node.value)
        for node in ast.walk(scope):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in _LAUNCHERS and node.args) or id(node) in seen:
                continue
            argv = node.args[0]
            values = assigned.get(argv.id, []) if isinstance(argv, ast.Name) else [argv]
            if values and all(_is_powershell_argv(value, assigned) for value in values):
                seen.add(id(node))
                sites.append(node)
    return sites


def _asks_this_host_for_powershell(scope):
    """Does this function decide, from the HOST, whether a `powershell` exists to launch?

    Two shapes, and both are real answers rather than two spellings of one: `shutil.which
    ("powershell")` asks for the executable, and `os.name` -- in a `skipif` decorator as much as in
    an `if` -- asks for the platform that ships it. `powershell_or_skip()` needs no clause here: it
    leaves no literal command line, so it is not a subject at all.
    """
    for inner in ast.walk(scope):
        if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute) \
                and inner.func.attr == "which":
            for argument in inner.args:
                if isinstance(argument, ast.Constant) and "powershell" in str(argument.value):
                    return True
        if isinstance(inner, ast.Attribute) and inner.attr == "name" \
                and isinstance(inner.value, ast.Name) and inner.value.id == "os":
            return True
    return False


def test_no_powershell_launch_in_this_suite_runs_without_asking_the_host_for_one():
    """A `.ps1` launcher may only be started where somebody asked whether this host has one.

    Four call sites spelled `powershell` out with no such question, and on the hosted ubuntu leg --
    which carries `pwsh`, a different product, and no `powershell` -- they died with
    `FileNotFoundError` while measuring nothing (BUG-0069). Every OTHER site in this suite already
    asked, which is why this is a sweep and not a rule about one helper: the duty is the question,
    not which helper answers it.

    THE QUESTION MAY STAND ONE LEVEL UP. A helper that carries no clause of its own is accepted
    when every caller of it in the same module does -- which is what `_scaffolded` in
    `test_kitupdate.py` and `test_presets.py` rely on, and what a rule demanding the clause AT the
    launch would have called a defect in working code.
    """
    offenders, sites = [], 0
    for path in sorted(glob.glob(os.path.join(ROOT, "tools", "*.py"))):
        with open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), os.path.basename(path))
        parents = {child: node for node in ast.walk(tree)
                   for child in ast.iter_child_nodes(node)}
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        guarded = {f for f in functions if _asks_this_host_for_powershell(f)}
        callers = {}
        for function in functions:
            for inner in ast.walk(function):
                if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name):
                    callers.setdefault(inner.func.id, set()).add(function)
        for site in _powershell_launches(tree):
            sites += 1
            chain, walker = [], site
            while walker in parents:
                walker = parents[walker]
                if isinstance(walker, ast.FunctionDef):
                    chain.append(walker)
            asked = any(function in guarded for function in chain)
            if not asked and chain:
                who = callers.get(chain[-1].name, set())
                asked = bool(who) and who <= guarded
            if not asked:
                offenders.append("%s:%d (in %s)" % (
                    os.path.basename(path), site.lineno,
                    "->".join(f.name for f in reversed(chain)) or "module level"))
    assert sites >= _POWERSHELL_LAUNCH_FLOOR, (
        "this sweep found only %d PowerShell launch(es) in tools/ -- it has stopped recognising "
        "the form, and a check that sees nothing reports everything clean" % sites)
    assert not offenders, (
        "these start a PowerShell launcher without anything on the way to them asking whether this "
        "host HAS one, so on a runner without it they report FileNotFoundError instead of saying "
        "they could not measure (BUG-0069). Remedy: `test_hooks_v2.powershell_or_skip()`, or a "
        "`shutil.which(\"powershell\")` / `os.name` clause in the test or its callers:\n  "
        + "\n  ".join(offenders))


# =================== a shipped text may not point at a decision this store does not hold (FR-0052)
_DEC_ID_RX = re.compile(r"\bDEC-\d{4}\b")
# A delimited literal: a code span, or a double-quoted span. Pairing is positional, the way
# CommonMark pairs a code span; `guard_memory_budget._CODE_SPAN_RX` pairs backticks only, and the
# double quote is added here because this corpus quotes offending PROSE as well as code.
#
# NO SINGLE-QUOTE ALTERNATIVE, and it is not an oversight. It was here for one round: in English
# prose `'…'` pairs ordinary APOSTROPHES, so a possessive opens a span that runs to the next
# apostrophe and blinds the reader to everything between. A delimiter a language also uses as a
# letter cannot mark a literal. Measured over the shipped tree 2026-08-29, the alternative was the
# ONLY thing hiding one span -- and it was `team-kits/model_tiers.yaml` line 31, "DEC-0034's T3
# rung", in the very file this reader cites as the pointer form it generalises (126 pointers judged
# without it, 125 with).
_DELIMITED_RX = re.compile(r"`[^`\n]*`|\"[^\"\n]*\"")


def _dec_citations(text):
    """Every match in `text` that CITES a decision of this repo's store, as match objects.

    THE DEFINITION, because "every DEC id" is not it. A shipped kit file also EXHIBITS ids: the file
    name inside a measured command line, the literal in a byte measurement, the quoted prose a
    guard's docstring shows as its own false positive. Those are DATA the sentence is about, and in
    this tree data is written inside a delimiter. So an id is a CITATION unless it sits inside a
    delimited literal whose content is MORE than the id itself; a span that is exactly the id stays a
    citation, because that is the pointer form this round generalises (`team-kits/model_tiers.yaml`
    writes its two that way).

    WHAT THIS DOES NOT READ, said here rather than discovered later, and stated as the MECHANISM
    rather than as an example of it: ANY id inside a delimiter longer than itself is unjudged,
    whatever the delimited text is. Measured on the shipped tree 2026-08-29, twenty-two double-quoted
    spans carry an id. Six of them are the DATA this exemption is for (three measured command paths,
    three quoted illustrations). The other sixteen are text somebody READS -- thirteen kernel refusal
    and briefing messages (`kernel/cli.py`, `kernel/migrate.py`, `kernel/state.py`,
    `kernel/dispatch.py`, `kernel/checkpoints.py`) and three handover-marker literals -- and a
    pointer that rots in one of those rots in front of a user at the moment a gate refuses. The other
    direction: in bare prose the reader cannot tell a citation from an illustration, so an
    illustrative id written without delimiters is reported although nothing rots -- the same error
    direction `guard_memory_budget` chose for the same ambiguity, with the same remedy: delimit it.
    """
    exempt = [(span.start(), span.end()) for span in _DELIMITED_RX.finditer(text)
              if not _DEC_ID_RX.fullmatch(span.group(0)[1:-1].strip())]
    return [hit for hit in _DEC_ID_RX.finditer(text)
            if not any(start <= hit.start() < end for start, end in exempt)]


def _shipped_kit_files():
    """(relative path, text) for every readable file under `team-kits/` -- the shipped tree."""
    kits = os.path.join(ROOT, "team-kits")
    for base, subdirs, names in os.walk(kits):
        subdirs[:] = [name for name in subdirs if name != "__pycache__"]
        for name in sorted(names):
            path = os.path.join(base, name)
            try:
                with open(path, encoding="utf-8") as handle:
                    yield os.path.relpath(path, ROOT).replace(os.sep, "/"), handle.read()
            except (OSError, UnicodeDecodeError):
                continue


def _decisions_in_the_store():
    """The DEC ids this repo holds, off the KERNEL's own layout rather than a path typed here.

    `ProjectState.active_dir` and `archive_root` are the builders every kernel write uses, so a store
    that reorganises moves this reader with it. Read rather than asked item by item: the kernel's own
    `exists_anywhere` wants the lock held, and a test that takes the state lock writes a lock file
    into canonical state to answer a read-only question.
    """
    sys.path.insert(0, os.path.join(ROOT, "team-kits"))
    from kernel.state import ProjectState
    store = ProjectState(os.path.join(ROOT, "project_memory"))
    found = set()
    for pattern in (os.path.join(store.active_dir("DEC"), "DEC-*.yaml"),
                    os.path.join(store.archive_root(), "DEC", "*", "DEC-*.yaml")):
        found.update(os.path.basename(path)[:-len(".yaml")] for path in glob.glob(pattern))
    return found


def test_every_decision_pointer_in_a_shipped_kit_file_resolves():
    """A kit file that names a DEC as its reason must name one this store still has (FR-0052).

    WHY THE SUBJECT IS DEC AND NOT EVERY ITEM TYPE, measured rather than assumed. This round adds
    pointers in the direction `team-kits/model_tiers.yaml` already goes -- a shipped line naming the
    decision behind it -- and a pointer nobody can follow is the failure this repo keeps re-learning.
    Widening the same reader to all eighteen id prefixes was run over the tree on 2026-08-29: 59
    non-resolving spans, of which the large majority are PLACEHOLDER ids of a PROJECT's store (the
    `project_memory/README.md` layout tables, the migration fixtures, a `proc_hash.py` usage line) --
    a different question, answered by a different store. DEC is the type a kit file cites as a
    REASON, and this repo's decisions are the store that answers.

    MEASURED RED before the repair of this round, over the shipped tree: three sites, seven spans.
    `kernel/kitupdate.py` cited DEC-0001 as the decision behind the update flow, and both
    `gate_write_scope.py` comments (in all three kits) named the same id -- which BUG-0020 deleted
    from this store the night it was measured and nobody restored. The id is unallocatable, so those
    three pointers could never be followed again.
    """
    store = _decisions_in_the_store()
    assert len(store) >= 40, (
        "only %d decision items found -- the store layout moved and this reader is judging every "
        "pointer against an empty set" % len(store))
    judged, offenders = 0, []
    for rel, text in _shipped_kit_files():
        for hit in _dec_citations(text):
            judged += 1
            if hit.group(0) not in store:
                offenders.append("%s:%d %s" % (rel, text[:hit.start()].count("\n") + 1,
                                               hit.group(0)))
    assert not offenders, (
        "these shipped kit files cite a decision that is in neither decisions/active/ nor "
        "archive/DEC/, so the reason they point at cannot be read:\n  " + "\n  ".join(offenders))
    assert judged >= 100, (
        "only %d decision pointers judged across team-kits/ -- the reader stopped matching, and "
        "then every assertion above is vacuously true" % judged)


def test_the_decision_pointer_reader_can_tell_a_citation_from_a_literal():
    """The floor under `_dec_citations`, so "return every id" and "return none" both fail here.

    Without it the test above rests on nothing: a reader that yielded nothing would look identical to
    a clean tree, and one that yielded everything would go red on the four measured places where a
    kit file EXHIBITS an id instead of citing one. Each probe below is the shape of one of them.
    """
    def found(text):
        return [hit.group(0) for hit in _dec_citations(text)]

    assert found("the reason is DEC-0034") == ["DEC-0034"]          # bare prose: a citation
    assert found("`DEC-0034` records the ladder") == ["DEC-0034"]   # the model_tiers.yaml form
    # A POSSESSIVE IS NOT A DELIMITER. With `'…'` among the alternatives this line read as one
    # literal and the pointer vanished -- the regression that cost model_tiers.yaml:31 a round.
    assert found("the kit's endpoints sit on DEC-0034's ladder") == ["DEC-0034"]
    assert found("`project_memory/decisions/active/DEC-0001.yaml`") == []   # a measured path
    assert found("the literals `id: DEC-0000` and `status: VALID`") == []   # a byte measurement
    assert found('"a DEC-2100 controller" reads as a decision id') == []    # quoted prose
    assert found("`rm -f \"x/DEC-0001.yaml\"` rc 0") == []                  # a measured command


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))


# ---------------- the hole list is answerable to its own summary table --------------------------

_HOLE_ENTRY_RX = re.compile(r"^###\s+(H\d+)\b", re.MULTILINE)
# A row of the summary table: the first cell is one H-number, or the closed-list row's several.
_HOLE_ROW_RX = re.compile(r"^\|\s*(H\d+(?:\s*,\s*H\d+)*)\s*\|", re.MULTILINE)


def test_every_hole_has_a_row_in_the_summary_and_every_row_has_a_hole():
    """The overview table of `docs/POST_V2_WISHLIST.md`, against the entries it summarises.

    THE MEASURED DRIFT: the table calls itself "Die offenen Einträge auf einen Blick", and a reader
    who opens it to see what is still open gets an answer that is short by whatever the last rounds
    appended. On 2026-09-02 it was short by FIFTEEN -- H82 from TSK-0099 and everything four
    parallel streams wrote (H83-H95, H99) -- because appending an entry and adding a row are two
    acts and only the first one is obvious. Nothing could say so, which is why this exists rather
    than a rule that somebody remembers.

    HELD IN BOTH DIRECTIONS, since either half alone rots: an entry without a row is a hole missing
    from the overview, and a row without an entry is an overview promising a section that is gone.
    The subject is DERIVED from the document both times -- every `### H<n>` heading, every first
    table cell that is H-numbers -- so a renumbering moves the check with it.
    """
    path = os.path.join(ROOT, "docs", "POST_V2_WISHLIST.md")
    with io.open(path, encoding="utf-8") as handle:
        text = handle.read()
    entries = set(_HOLE_ENTRY_RX.findall(text))
    rows = {name.strip() for cell in _HOLE_ROW_RX.findall(text) for name in cell.split(",")}
    assert len(entries) >= 90, (
        "only %d hole entries found — the reader stopped matching the document" % len(entries))
    missing = sorted(entries - rows, key=lambda name: int(name[1:]))
    assert not missing, (
        "these holes have an entry but no row in the summary table, so the overview is short by "
        "them: %s" % ", ".join(missing))
    orphans = sorted(rows - entries, key=lambda name: int(name[1:]))
    assert not orphans, (
        "the summary table has rows for holes that have no entry any more: %s" % ", ".join(orphans))
