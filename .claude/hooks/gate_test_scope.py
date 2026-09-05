#!/usr/bin/env python3
"""
Gate 5 (FR-0086, the cost clause of DEC-0050): a full run of the declared test surface happens
ONCE, and the line says so.

THE ERROR IT CATCHES IS MEASURED, which is what DEC-0056 asks of a gate proposal before it is
built. DEC-0050 measured six full-suite runs across the rounds of ONE item -- 35 to 39 minutes
each, about four hours, and not one finding of any round came out of them. DEC-0070 measured the
same class again in five places in a single generation (~5 h), and recorded that every implementer
NAMED the rule in its report and none was stopped by it: "DEC-0050 is not a sentence in an order
any more". This gate is that sentence with a reader.

THE RULE, in the two halves FR-0086 states:

    A command line that runs the WHOLE declared test surface is refused during a round -- unless
    the line itself says it is the delivery run, by carrying `DELIVERY_RUN=<ITEM-ID>` in front of
    the runner. That prefixed line is the one the kernel records as Evidence with `run_scope: full`
    (DEC-0061), so the run the merge needs and the run this gate allows are the same run, once.

    A SELECTION is not judged at all. So is a surface the project does not declare, and so is a
    declared surface cheap enough that repeating it costs nothing (`judged_above_seconds`).

WHAT "RUNS THE WHOLE DECLARED SURFACE" MEANS, as a property and not as a list of spellings:

  * the stage RUNS a declared runner -- its verb's basename is the runner, or the runner is the
    word an interpreter's `-m` hands it. A runner NAME occurring anywhere else on the line is text
    (`grep pytest tools/` runs grep), which is the whole reason this is asked of the verb;
  * the positional words the stage hands that runner include one that IS a declared surface root
    or an ANCESTOR of one -- and a stage that hands it no positional at all names the runner's own
    rootdir, which is an ancestor of every surface. A word STRICTLY INSIDE a root (a sub-path, a
    node id `file::name`) narrows the run and is therefore a selection;
  * and no word of the stage is an option the declaration lists as one after which the line no
    longer runs the whole surface, WITH a value that is not empty. Which options those are is a
    fact about the RUNNER, so the tripwire that keeps the list honest asks the runner:
    `test_every_declared_narrowing_option_really_makes_the_runner_run_fewer_tests` runs a
    three-test fixture suite with and without each entry and counts the tests that actually ran.
    Two weaker ends stand beside it -- `test_every_declared_narrowing_option_is_one_the_runner
    _still_has` (the runner still knows the option at all) and
    `test_every_declared_narrowing_option_earns_its_place` (this gate reads the entry). The first
    cut had only those two, and neither could see that `--ff` narrows nothing: measured, seven
    declared entries left three of three fixture tests running, and `pytest tools/ --ff` was
    rc 0 against a surface declared at 3465 s.

WHY THE THRESHOLD IS DATA AND NOT A CONSTANT HERE: DEC-0056 makes the cost to the legitimate path
part of every gate decision, and a project whose whole suite runs in seconds gains nothing from
this refusal and pays a prefix word for it. `tools/test_surface.json` carries the threshold, the
declared surfaces and the record each of their durations was read out of.

THE SECOND FULL RUN. DEC-0063 (4) reads DEC-0050 as "once after the last rework, before the stamp",
and says a second full run is the alternative and not the default. So a delivery run whose item
ALREADY holds a passing Evidence with `run_scope: full` is refused too -- the prefix buys the first
one, not a repetition. It is not refused when that Evidence FAILED: a full run that yielded
findings is exactly the case DEC-0063 (4) sends back into the suites.

WHAT THIS GATE DOES NOT SEE, named rather than implied (chains in docs/POST_V2_WISHLIST.md):
  * a runner the declaration does not name, and a runner word the TEXT does not fix (`$RUNNER
    tools/`): the cheap pre-filter below looks for a declared runner's name in the line before it
    reads anything, so a line that spells the runner out of an expansion is not judged (H153);
  * an option that narrows the run and is not in the declaration: the line then reads as a full
    run and is REFUSED. That is over-refusal, answerable on the line, and it is H152;
  * a DECLARED option given a value that happens to match nothing (`--deselect does::not::exist`,
    `--ignore=<a path that is not there>`): the line reads as a selection and passes. Telling
    that apart needs a collection, which is the cost this gate exists to avoid -- H152 carries
    it with its measurement;
  * the declaration itself is not in gate 1's protected area -- it is data, not a loaded module, so
    whoever may write `tools/` may lower the threshold (H151). Per DEC-0056 that is intent, not
    error, and this gate guards against error.
"""
import glob as globmodule
import json
import os
import posixpath
import re
import sys

# THE IMPORT IS INSIDE THE PROTECTION -- see the same block in `gate_lead_write_scope.py` and the
# measurement in `_harness.py`'s header: a module-level import failure exits 1, and the provider
# reads that as an allow.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import _harness
except BaseException as error:  # noqa: BLE001 -- a gate that cannot load must not mean "allow"
    sys.stderr.write(
        "[harness gate] refused: the shared body of this repo's gates (.claude/hooks/_harness.py) "
        "could not be loaded (%r), so this call could not be judged. A gate that cannot decide "
        "refuses.\nRemedy: repair the file from a shell OUTSIDE Claude Code and start a new "
        "session -- it cannot be repaired from inside this one.\n" % (error,))
    sys.exit(2)


# The declaration this gate decides on -- see the module docstring for why it is a file. Spelled
# with forward slashes because it is also QUOTED in every refusal, and a reader who is being
# sent to a file should get the path in the shape the repo writes it.
DECLARATION = "tools/test_surface.json"

# How a line says it is THE delivery run. An ASSIGNMENT, because that is the one shape both shells
# this repo is driven from can put in front of a program without changing what the program is: a
# POSIX shell reads `NAME=value cmd` as an environment prefix of `cmd`, and PowerShell writes the
# same intent as a command of its own (`$env:NAME="value"; cmd`) -- which `_harness.stages` hands
# this gate as a stage with no verb, so both are read below. Gate 3 prints the exact line that
# lifts it; so does this one.
DELIVERY_MARKER = "DELIVERY_RUN"

# What the kernel calls a run over the whole surface, and the field it records it in (DEC-0061).
# Read off the kernel rather than spelled, so a change to the vocabulary lands in one place.
RUN_SCOPE_FIELD = "run_scope"
RUN_COMMAND_FIELD = "run_command"

# The interpreter option that makes the following word the program. `python -m pytest` is the way
# this repo's own documented lines spell the runner, and without this the runner would have to be
# the verb -- which it is not there.
MODULE_FLAG = "-m"


def declaration(root):
    """What this project declares as its test surface, or None when it declares nothing.

    THREE STATES AND NOT TWO, which is the correction of the first cut. A project WITHOUT the
    file is not judged -- that is the shape of PR-0004's first invariant, a runner nobody
    declared is not judged. A file that IS there is one somebody meant this gate to decide by, so
    anything about it this reader cannot use is a REFUSAL and not an allow.

    "Cannot use" is asked of the SHAPE and not only of the parser, because a JSON parser accepts
    far more than a declaration: measured 2026-09-05 through the real hook process, `[]`,
    `"tools"`, `7`, `null`, `{}` and `{"surfaces": "tools"}` were each rc 0 -- ALLOWED -- while
    only a syntax error refused. The rule is now: what is stored must be an object, and a
    `surfaces` key that is present must be a list.
    """
    path = os.path.join(root, *DECLARATION.split("/"))
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as error:  # noqa: BLE001 -- an unreadable rule is not an absent rule
        _refuse_the_declaration("could not be read (%r)" % (error,))
    if not isinstance(data, dict):
        _refuse_the_declaration("holds a %s where the declaration is an object"
                                % type(data).__name__)
    if "surfaces" in data and not isinstance(data["surfaces"], list):
        _refuse_the_declaration("holds a %s under `surfaces`, where a list of declared surfaces "
                                "belongs" % type(data["surfaces"]).__name__)
    return data


def _refuse_the_declaration(what):
    """One refusal for every shape of "the rule is there and this gate cannot use it"."""
    _harness.refuse(
        "this shell call could not be judged: %s is present but %s, so this gate cannot tell a "
        "full run of the declared test surface from a selection.\n"
        "A gate that cannot read its own rule refuses rather than waving the call through.\n"
        "Remedy: repair the declaration, or delete it -- an absent declaration means 'this "
        "project declares no test surface' and is judged by nothing." % (DECLARATION, what))


def _judged_surfaces(data):
    """The declared surfaces this gate still judges -- the cost clause of DEC-0056, as data.

    A surface whose declared duration is at or under the threshold is dropped here: repeating it
    is not the cost DEC-0050 measured, and refusing it would be a gate charging the legitimate path
    for nothing. A surface that declares NO duration is judged: silence is not a claim of cheapness.
    """
    floor = data.get("judged_above_seconds")
    floor = float(floor) if isinstance(floor, (int, float)) else 0.0
    out = []
    for entry in data.get("surfaces") or []:
        if not isinstance(entry, dict) or not entry.get("runner") or not entry.get("root"):
            continue
        seconds = entry.get("seconds")
        if isinstance(seconds, (int, float)) and float(seconds) <= floor:
            continue
        out.append(entry)
    return out


def _normalised(text):
    """A path word as this gate compares it: forward slashes, and the `.`/`..` segments resolved.

    RESOLVED AND NOT MERELY TRIMMED, which is the whole of B1's sibling defect: comparing the raw
    word let every spelling that MEANS the declared root without spelling it walk past -- measured
    2026-09-05 as hook processes, `pytest tools/.`, `pytest tools/../tools`, `pytest ./tools/.` and
    `pytest ..` were each rc 0 against a surface declared at 3465 s. `posixpath` and not `os.path`,
    because the comparison below is on forward slashes and `os.path.normpath` would hand back
    backslashes on this host.
    """
    word = str(text or "").replace("\\", "/").strip()
    if not word:
        return "."
    return posixpath.normpath(word).rstrip("/") or "."


def _is_absolute(word):
    """Does this word name a place without help from a working directory?

    THREE SHAPES AND NOT ONE, because `posixpath.isabs` answers only the first: a POSIX root (`/x`),
    a Windows drive (`C:/x`) and a UNC share (`//host/share`). The middle one is the shape gate 1
    pushes every caller of this repo into -- its refusals end with "spell the path absolutely".
    """
    here = str(word or "").replace("\\", "/")
    return here.startswith("/") or bool(re.match(r"^[A-Za-z]:/", here))


def _drive_relative(word):
    """`C:tools` -- a drive letter with no separator behind it.

    A place this reader cannot compute: it names the current directory OF THAT DRIVE, which is
    per-drive state of the shell and not something a payload carries. Measured 2026-09-05 against
    the real runner: `pytest C:tools` collected the same 4627 node ids as `pytest tools`, and this
    gate was rc 0. It is unplaceable, and unplaceable covers.
    """
    here = str(word or "").replace("\\", "/")
    return bool(re.match(r"^[A-Za-z]:(?!/)", here))


def _placed(word, repo_root, cwd):
    """Where on this filesystem the word points, or None when this reader cannot compute it.

    A RELATIVE WORD ATTACHES TO THE CALL'S OWN `cwd`, and the comparison below then happens against
    the REPO ROOT, because that is what the declared surfaces are relative to. Getting that base
    wrong is not cosmetic: measured 2026-09-05 with a payload `cwd` one level ABOVE the repo -- the
    ordinary case in this project, where work happens in worktrees and scratch trees --
    `pytest "C:/.../wt2/tools"` and `pytest wt2/tools` were both rc 0 against a surface declared at
    3465 s, while the same lines from inside the repo were rc 2 (verifier round 2, B2').
    """
    if _drive_relative(word):
        return None
    if _is_absolute(word):
        return str(word).replace("\\", "/")
    if not cwd:
        return None
    return posixpath.join(_normalised(cwd), _normalised(word))


def _brace_expanded(word):
    """Every word a shell's BRACE expansion makes of this one, or None when this reader cannot say.

    THE SECOND EXPANSION. A shell performs two on a positional path word: pathname expansion, which
    `glob.has_magic` answers for, and brace expansion, whose whole syntax is one character. Reading
    only the first is what let `<root>/{test_*,conftest}.py` through -- measured with the real shell
    and a shim that logs the runner's argv: 41 `.py` paths handed over, the whole surface, rc 0
    (merge verify round 2, R2-B4).

    WHAT IT DOES NOT DO, and says so by answering None: a brace group with no top-level comma.
    Measured with the real shell (merge verify round 3, R3-M1), those are TWO different words and
    this reader cannot tell them apart: Git Bash leaves `<root>/{test_*}.py` literal -- one
    positional -- and expands `{1..9}` to nine. Deciding that needs a range grammar this reader
    does not have, so the word is one whose expansion is unknown, and the refusal says exactly
    that. An unmatched `{` is not an expansion at all -- a shell leaves it literal -- so the word
    comes back unchanged.

    `.claude/hooks/test_gates.py::test_gate5_reads_the_brace_expansion_a_shell_would_perform`
    """
    text = str(word)
    start = text.find("{")
    if start < 0:
        return [text]
    depth, end = 0, -1
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                end = index
                break
    if end < 0:
        return [text]                       # an unmatched brace stays literal in a shell too
    parts, level, current = [], 0, ""
    for char in text[start + 1:end]:
        if char == "{":
            level += 1
        elif char == "}":
            level -= 1
        if char == "," and level == 0:
            parts.append(current)
            current = ""
            continue
        current += char
    parts.append(current)
    if len(parts) < 2:
        return None                         # a range or a single word: not this reader's syntax
    out = []
    for part in parts:
        deeper = _brace_expanded(text[:start] + part + text[end + 1:])
        if deeper is None:
            return None
        out.extend(deeper)
    return out


def _expansion_covers(word, root, repo_root, cwd, members):
    """A positional the SHELL expands: does the match set hand the runner the whole surface?

    THE HOLE THIS CLOSES, measured as a process on 2026-09-05 (merge verifier round 1, B2):
    `python -m pytest tools/test_*.py -q` was rc 0 while `tools/` held 40 matching files and the
    surface is declared at 3465 s -- the whole run, 42 minutes, waved through. The reader above
    placed the word as one path, found it lay INSIDE the root, and read "inside the root" as
    "narrows the run". A glob does not narrow anything; the shell replaces it with everything it
    matches, and this gate has the same filesystem the shell has.

    WHAT DECIDES IS THE DECLARATION, NOT A RULE ABOUT pytest. A surface may declare `members` --
    the glob, relative to its root, that picks the files a bare run of that root would hand the
    runner. The word covers the surface when its expansion holds every one of them. That keeps the
    fact about the runner in the data beside `options_that_narrow`, where the same argument already
    put it, and it keeps the tripwire honest at both ends: the members glob is measured against the
    RUNNER's own collection in
    `.claude/hooks/test_gates.py::test_the_declared_members_are_the_files_the_runner_really_collects`.

    A SURFACE THAT DECLARES NO MEMBERS gets the fail-closed direction and its own sentence: this
    reader cannot tell such a glob from the whole surface, so it does not wave it through. The
    kits ship no declaration at all, so that is the branch a kit project meets until it declares
    one -- named as the remainder of `H165`.

    Returns (covers, why_unplaceable, glob_word).
    """
    spellings = _brace_expanded(str(word))
    if spellings is None:
        return True, None, (str(word), "this reader cannot compute that "
                            "expansion -- a brace group with no top-level comma "
                            "is either left literal or a range, and it does not "
                            "decide which")
    # EACH SPELLING GETS THE QUESTION IT DESERVES, and the WORD covers when any of them does.
    # A spelling without pathname magic is an ordinary positional -- `{tools,docs}` expands to
    # `tools`, which IS a declared root, and asking the members comparison about a directory said
    # "selection" (measured after the first cut of this branch).
    for one in spellings:
        if globmodule.has_magic(one):
            continue
        hit, why = _covers(one, root, repo_root, cwd)
        if hit:
            return True, why, None
    globs = [one for one in spellings if globmodule.has_magic(one)]
    if not globs:
        return False, None, None
    here = [_placed(one, repo_root, cwd) for one in globs]
    if any(one is None for one in here):
        return True, str(word), None
    target = os.path.join(repo_root, *_normalised(root).split("/"))
    matched = {os.path.normcase(os.path.abspath(one))
               for spelling in here
               for one in globmodule.glob(spelling.replace("/", os.sep))}
    if not os.path.isdir(target):
        # A ROOT THAT IS A FILE is covered exactly when the expansion holds that file. No members
        # question arises -- a bare run of such a surface runs one file -- and asking one anyway
        # made a selection aimed at ANOTHER surface meet this surface's fail-closed sentence.
        return os.path.normcase(os.path.abspath(target)) in matched, None, None
    if not members:
        return True, None, (str(word), "the declared surface %r says nothing about which files a "
                                       "full run of it covers" % str(root))
    declared = {os.path.normcase(os.path.abspath(one))
                for one in globmodule.glob(os.path.join(target, *str(members).split("/")))}
    if not declared:
        return True, None, (str(word), "the declared surface %r says nothing about which files a "
                                       "full run of it covers" % str(root))
    return declared <= matched, None, None


def _covers(word, root, repo_root, cwd):
    """Does this positional hand the runner the WHOLE of `root`? -- `(covers, why_unplaceable)`.

    "THE SAME PLACE" IS WHAT THE FILESYSTEM SAYS, not what two strings look like, and this repo
    answered that question once already: `_harness.under` compares the IDENTITY of the deepest
    EXISTING ancestor (`(st_dev, st_ino)`) plus the text below it, which is why gate 1 sees a
    junction, a symlink, the extended-length spelling and a case variant as the file they are (the measurement
    is `docs/POST_V2_WISHLIST.md` H14/H16, TSK-0007/TSK-0008). This gate had built a text
    normaliser of its own instead and inherited none of it: measured 2026-09-05 against the real
    runner, `pytest TOOLS`, `pytest Tools`, `pytest C:tools` and a junction over `tools` each
    collected the same 4627 node ids and each was rc 0 here. So the identity reader is REUSED
    rather than copied -- one answer to one question.

    FOUR OUTCOMES. The word is the root or an ancestor of it (covers); it lies INSIDE the repo and
    is not the root (a selection); it is a place this reader CAN find and that is not this repo at
    all (a selection too -- see `_placeable`); or it cannot be placed at all -- a drive-relative
    word, a `/c/...` spelling no Windows process resolves, an unmounted drive, a UNC share nobody
    serves, or no `cwd` in the payload. Only the last COVERS, because what this gate cannot place
    may be the whole surface, and it carries its own sentence: saying "this line runs the whole
    declared test surface" about a line that names another machine is a claim that is not true.
    """
    here = _placed(word, repo_root, cwd)
    if here is None:
        return True, str(word)
    target = os.path.join(repo_root, *_normalised(root).split("/"))
    if _harness.under(target, here):
        return True, None
    if _harness.under(here, repo_root):
        return False, None
    if _placeable(here):
        # A PLACE THIS READER CAN FIND, AND IT IS NOT THIS REPOSITORY -- so it is decidably not the
        # declared surface, i.e. a selection. Refusing it was the cost of the fail-closed branch and
        # it fell on the one line this repo prescribes for every red-first rig: CLAUDE.md says to
        # restore a defect in a clone OUTSIDE the repo and run the suite there, and measured
        # 2026-09-05 every such run -- a whole scratch suite AND a single file in it -- came back
        # rc 2. A LINK from outside INTO this repo does not slip through here: the identity reader
        # above answers first (measured, a junction pointed at the declared surface is rc 2).
        return False, None
    return True, str(word)


def _placeable(here):
    """Can this reader say WHERE this word is at all -- or only that it looks like a path?

    THE DEEPEST EXISTING ANCESTOR DECIDES, and a filesystem ROOT does not count as one. That is the
    line between "a suite somewhere else on this machine" and a spelling this process cannot
    resolve: `/c/Offline Repos/...` is a shell's idea of a path that Windows resolves to a
    `C:` plus a directory nobody has; a drive that is not mounted has nothing below its root either,
    and a UNC
    share nobody serves answers the same way. All three climb to a root without finding anything and
    stay unplaceable (H153); a scratch suite under a real directory is found at its first step.

    `_harness._identity` is what asks, so the question runs under this gate's deadline like every
    other filesystem question here -- a share that does not answer becomes a refusal, not a kill.
    """
    text = os.path.abspath(str(here).replace("/", os.sep))
    while True:
        head = os.path.dirname(text)
        if head == text:
            return False
        if _harness._identity(text) is not None:
            return True
        text = head


def _is_option(word):
    return str(word).startswith("-")


def _names_the_runner(word, runner):
    return os.path.basename(_normalised(word)) in (runner, runner + ".exe")


def _handed_to(stage_words, runner):
    """The words this stage hands `runner`, or None when it does not run `runner` at all.

    THE WORDS AFTER IT, and that boundary is load-bearing rather than tidy. `-m` belongs to two
    programs at once: it is the interpreter's module flag in `python -m pytest` and pytest's own
    marker filter in `pytest -m slow`. Read over the whole stage, the first of those made every
    documented full-run line of this repo look like a selection -- measured on
    `python -B -m pytest tools/ -q`, rc 0 where the refusal belongs.

    The runner is the stage's VERB or the word an interpreter's `-m` hands it. A runner name
    anywhere else is text: `grep pytest tools/` runs grep.
    """
    if not stage_words:
        return None
    if _names_the_runner(stage_words[0], runner):
        return list(stage_words[1:])
    for index, word in enumerate(stage_words[:-1]):
        if str(word) == MODULE_FLAG and _names_the_runner(stage_words[index + 1], runner):
            return list(stage_words[index + 2:])
    return None


def _positionals(handed):
    """Every word handed to the runner that is not an option.

    EVERY non-option word, and the word after a bare option is NOT skipped as its value. Skipping
    it is the reading that breaks the ordinary case: `pytest -q tools/test_hooks.py` would lose its
    only target and read as a run with no target at all, i.e. as the biggest full run there is.
    What that costs instead is an option whose VALUE looks like a surface root
    (`pytest --rootdir tools tools/test_hooks.py`) reading as a full run -- over-refusal, on the
    line, and H152 carries it.
    """
    return [str(word) for word in handed if not _is_option(str(word))]


def _narrowing_option(handed, narrowing):
    """The first word handed to the runner that the declaration calls one after which the line no
    longer runs the whole surface, or None.

    Compared on the option NAME, so `-k=x` and `--deselect=y` are the same option as their spaced
    spellings -- a shell hands both to the runner and the runner reads both.

    A VALUE THAT IS EMPTY IS NOT A SELECTION, and that is measured rather than reasoned: `-k ""`
    and `-m ""` leave the runner selecting nothing away -- three of three fixture tests still ran
    (2026-09-05). Read on the option NAME, so `-k=x` and `-k x` are the same option.

    THE LAST OCCURRENCE OF A NAME DECIDES, because that is what the runner does with it: argparse
    keeps the last value. Reading the FIRST hit was fail-open and measured so -- `-k alpha -k ""`
    and `-k alpha -k=` each ran three of three tests while this gate answered rc 0 (verifier round
    2, B1').

    WHAT THIS CANNOT DECIDE, named rather than implied: a value that is well-formed and happens to
    match nothing (`--deselect does::not::exist`). Telling that apart needs a collection, which is
    the cost this gate exists to avoid; H152 carries it.
    """
    words = [str(word) for word in handed]
    last = {}
    for index, text in enumerate(words):
        if not _is_option(text):
            continue
        name, joined, value = text.partition("=")
        if name not in narrowing:
            continue
        if joined:
            # `-k=` hands the runner an empty expression: it selects nothing away, and three of
            # three fixture tests still ran (measured)
            last[name] = text if value.strip() else None
            continue
        following = words[index + 1] if index + 1 < len(words) else None
        empty = (following is not None and not _is_option(following) and not following.strip())
        last[name] = None if empty else text          # `-k ""`: an empty WORD, same answer
    for text in last.values():
        if text is not None:
            return text
    return None


def _assignment(word):
    """(name, value) when this word is an environment assignment, else None.

    Both spellings, because both shells are registered on this gate: `NAME=value` and PowerShell's
    `$env:NAME="value"`. The value keeps no quotes -- `_harness.tokenise` already resolved the
    shell's quoting, and what is left of `"TSK-0121"` at this point is `"TSK-0121"` only when the
    quotes were themselves quoted.
    """
    text = str(word)
    if "=" not in text or text.startswith("-"):
        return None
    name, _sep, value = text.partition("=")
    name = name.strip()
    lowered = name.lower()
    if lowered.startswith("$env:"):
        name = name[len("$env:"):]
    elif lowered.startswith("env:"):
        name = name[len("env:"):]
    return name.strip(), value.strip().strip("\"'")


def _delivery_value(read, module, runner_stage):
    """What `DELIVERY_RUN` is set to in front of the runner, or None.

    TWO PLACES, because the two shells write the same intent differently and both are registered:
    an assignment among the runner stage's own words BEFORE the runner (`NAME=v pytest ...`), and a
    command of the line that runs nothing but assignments (`$env:NAME="v"; pytest ...`), which
    `_harness.stages` hands over as a stage whose verb is empty. Anything else on the line -- a
    quoted mention inside an `echo`, an assignment in a stage that does run something else -- is
    not a prefix of this runner and does not count.
    """
    for word in runner_stage:
        pair = _assignment(word)
        if pair is not None and pair[0] == DELIVERY_MARKER:
            return pair[1]
    for pipeline, _depth, _child in read:
        for stage in _harness.stages(module, pipeline):
            body = _harness.stage_body(module, stage)
            if module._stage_verb(body):
                continue
            for word in body:
                pair = _assignment(word)
                if pair is not None and pair[0] == DELIVERY_MARKER:
                    return pair[1]
    return None


def _full_run_evidence(root, item_id):
    """(evidence id, result) of an Evidence for `item_id` that records a run over the whole surface.

    The kernel's own record, not a second bookkeeping: DEC-0061 gave EVD the optional pair
    `run_command` / `run_scope`, and `run_scope: full` is what a delivery run is recorded as. The
    NEWEST such record answers -- ids are allocated ascending, so the highest one is the last run.
    """
    import yaml
    state = _harness.project_state(root)
    found = []
    for stem, path in state.iter_active_items("EVD"):
        try:
            with open(path, encoding="utf-8") as handle:
                item = yaml.safe_load(handle)
        except Exception:  # noqa: BLE001 -- an unreadable record judges nothing
            continue
        if not isinstance(item, dict):
            continue
        if str(item.get(RUN_SCOPE_FIELD) or "").strip().lower() != "full":
            continue
        related = item.get("related")
        related = related if isinstance(related, (list, tuple)) else [related]
        if item_id not in [str(one).strip() for one in related if one]:
            continue
        found.append((str(item.get("id") or stem), str(item.get("result") or "").strip().lower()))
    return sorted(found)[-1] if found else None


def _delivery_line(tool, command):
    """The exact line to run when THIS is the delivery run -- printed, the way gate 3 prints its
    remedy, so the way through the refusal is a line somebody can copy rather than a rule to
    reconstruct."""
    if str(tool or "") == "PowerShell":
        return '$env:%s="<ITEM-ID>"; %s' % (DELIVERY_MARKER, command.strip())
    return "%s=<ITEM-ID> %s" % (DELIVERY_MARKER, command.strip())


def _mentions_a_runner(command, runners):
    """Cheap pre-filter: could this line name one of the declared runners at all?

    Asked of the RAW text with its quoting characters removed, so `py""test` and `py\\test` are
    still seen; a runner the text does not fix at all (`$RUNNER tools/`) is not, and that is the
    gap H153 carries. It exists because this gate sits on every shell call beside two others that
    already read the line, and the reading is the whole cost -- see AC-4 in the round protocol for
    what the pre-filter buys, measured.
    """
    flat = "".join(char for char in str(command or "") if char not in "\"'\\`")
    return any(runner in flat for runner in runners)


def decide():
    data = _harness.payload()
    command = str((data.get("tool_input") or {}).get("command") or "")
    if not command.strip():
        # A CALL THIS GATE CANNOT READ IS NOT A CALL IT MAY ALLOW -- the same verdict gate 3 and
        # gate 4 reach for a payload of the shape they are registered on that carries no subject.
        _harness.refuse(
            "this tool call could not be inspected: the payload of a shell tool carries no "
            "command line, so there is nothing to read.\n"
            "Remedy: if this is a legitimate call in a shape the gate does not read, report it -- "
            "the gate refuses rather than guessing, and a guess here is a silent allow.")
    root = _harness.repo_root(data)
    declared = declaration(root)
    if not declared:
        return
    surfaces = _judged_surfaces(declared)
    if not surfaces:
        return
    runners = {str(entry["runner"]) for entry in surfaces}
    if not _mentions_a_runner(command, runners):
        return
    narrowing = declared.get("options_that_narrow") or {}

    module = _harness.shell_reader(data)
    compat = _harness.compat(data)
    read = _harness.command_line(module, compat, data, command)
    for pipeline, _depth, _child in read:
        for stage in _harness.stages(module, pipeline):
            body = _harness.stage_body(module, stage)
            words = [str(word) for word in body]
            for entry in surfaces:
                runner = str(entry["runner"])
                handed = _handed_to(words, runner)
                if handed is None:
                    continue
                if _narrowing_option(handed, set(narrowing.get(runner) or ())) is not None:
                    continue
                targets = _positionals(handed)
                verdicts = []
                for word in targets:
                    if globmodule.has_magic(str(word)) or "{" in str(word):
                        verdicts.append(_expansion_covers(
                            word, entry["root"], root, data.get("cwd"), entry.get("members")))
                        continue
                    covers, why = _covers(word, entry["root"], root, data.get("cwd"))
                    verdicts.append((covers, why, None))
                if targets and not any(covers for covers, _why, _glob in verdicts):
                    continue
                unplaceable = next(
                    (why for covers, why, _glob in verdicts if covers and why), None)
                unreadable_glob = next(
                    (one for covers, _why, one in verdicts if covers and one), None)
                _judge(data, root, command, entry, read, module, body, unplaceable,
                       unreadable_glob)


def _judge(data, root, command, entry, read, module, runner_stage, unplaceable=None,
           unreadable_glob=None):
    """This stage runs the whole of one declared surface. Three answers, in the order FR-0086 gives
    them: no prefix, a prefix naming nothing open, and a prefix whose round already has its run."""
    named = _delivery_value(read, module, runner_stage)
    if named is None and unplaceable:
        # ITS OWN SENTENCE, because the ordinary one would be FALSE about this line: a word on
        # another drive, a UNC share or a `/c/...` spelling does not run `tools`, and saying so
        # sends the reader to `judged_above_seconds` for a problem that is not there (F8).
        _harness.refuse(
            "this line could not be placed against this repository: %r names no position this "
            "gate can compare with the declared test surface `%s` -- another drive, a UNC share, "
            "a drive-relative word, or a shell whose working directory the payload does not "
            "carry.\n"
            "It is therefore read as one that MIGHT run the whole surface, which is the "
            "fail-closed direction: what this gate cannot place, it does not wave through.\n"
            "Remedy: spell the target as a path under this repository, or -- if this really is a "
            "run of something else entirely -- run it from a shell whose working directory lies "
            "inside the project it belongs to."
            % (unplaceable, entry["root"]))
    if named is None and unreadable_glob:
        # ITS OWN SENTENCE for the same reason the unplaceable branch has one: saying "this runs
        # the whole surface" about `root/test_x*.py` would be a claim this reader has not made.
        _harness.refuse(
            "this line hands the runner a word the SHELL expands (%r), and %s -- so this gate "
            "cannot tell the expansion apart from the whole surface.\n"
            "It is read as one that MIGHT run it, which is the fail-closed direction.\n"
            "Remedy: name the files without a wildcard, or add `members` to that surface in %s -- "
            "the glob, relative to the root, that picks the files a bare run of it would run."
            % (unreadable_glob[0], unreadable_glob[1], DECLARATION))
    if named is None:
        _harness.refuse(
            "this line runs the WHOLE declared test surface `%s` (%s), and nothing on it says "
            "this is the delivery run.\n"
            "DURING a round only the suites that read what the round changed are run; the FULL "
            "run is a delivery criterion and happens ONCE, after the last rework and before the "
            "stamp and the commit (DEC-0050). That is measured, not preferred: six repetitions of "
            "one suite inside one item's rounds produced no finding at all, and generation 3 paid "
            "the same class five more times (DEC-0070).\n"
            "This surface is declared at %g s in %s (%s).\n"
            "\n"
            "Remedy -- pick the one that is true:\n"
            "  * it is a round run: name what you changed, e.g. `%s <the suite that reads it>` "
            "or a `-k` selection;\n"
            "  * it IS the delivery run: say so ON the line, and the kernel records exactly this "
            "line as the Evidence the merge needs (DEC-0061):\n"
            "        %s\n"
            "    then, after it is green:\n"
            "        PYTHONPATH=team-kits python -B -m kernel.cli --root %s evidence \\\n"
            "            --kind test --result pass --related <ITEM-ID> \\\n"
            "            --summary \"full run\" --artifact-ref <path> \\\n"
            "            --%s full --%s \"<the line above, verbatim>\"\n"
            "  * this surface is not worth judging any more: `judged_above_seconds` in %s is the "
            "knob, and lowering it under %g s stops this refusal for it."
            % (entry["root"], entry["runner"], float(entry.get("seconds") or 0),
               DECLARATION, entry.get("measured_in") or "no record named",
               entry["runner"], _delivery_line(data.get("tool_name"), command),
               _harness.STATE_ROOT, RUN_SCOPE_FIELD.replace("_", "-"),
               RUN_COMMAND_FIELD.replace("_", "-"), DECLARATION,
               float(entry.get("seconds") or 0)))
    known = _harness.automata(root)
    references = [ref for ref in _harness.resolve_references(root, named)
                  if ref.found and ref.carries_work(known) and not ref.terminal(known)]
    if not references:
        _harness.refuse(
            "this line calls itself the delivery run (`%s=%s`), but %r leads no open work under "
            "%s/.\n"
            "The delivery run is the run ONE item's merge rests on (DEC-0061), so the prefix names "
            "that item -- a prefix that names nothing is a full run with a word in front of it.\n"
            "Remedy: put the id of the open item this delivery run belongs to in the prefix, e.g. "
            "`%s=TSK-nnnn %s`."
            % (DELIVERY_MARKER, named, named, _harness.STATE_ROOT, DELIVERY_MARKER,
               command.strip()))
    item_id = references[0].text
    recorded = _full_run_evidence(root, item_id)
    if recorded is not None and recorded[1] == "pass":
        _harness.refuse(
            "%s already has a PASSING full run on record (%s, `%s: full`), so this would be the "
            "second one of the same round.\n"
            "DEC-0063 (4) reads DEC-0050 as: the full suite runs once after the last rework and "
            "before the stamp; when that run itself yields findings, their fixes are followed by "
            "FULL runs of every suite that READS the changed files -- a second full run is the "
            "alternative, not the default.\n"
            "Remedy: run the suites that read what changed since %s, in full, and record them; "
            "or, if the tree really moved far enough that only the whole surface answers, say so "
            "in the round protocol and record THAT run against a new item."
            % (item_id, recorded[0], RUN_SCOPE_FIELD, recorded[0]))


if __name__ == "__main__":
    _harness.guarded(decide)
