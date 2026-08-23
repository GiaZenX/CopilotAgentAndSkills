#!/usr/bin/env python3
"""
Ledger-validity gate (office) — spec II.9 after user decision I.3/1.

Append-only is GONE, and with it `guard_ledger_direct`, which refused every hand edit. The user's
reasoning: forbidding edits did not make the data trustworthy, it made corrections cost a reversal
entry even for a typo, and git history plus Evidence is the audit trail. So edits are allowed —
and always validation-required.

  PreToolUse(Bash|PowerShell) on commit/push/merge/tag/report   VALIDATE NOW, then allow or refuse
  PreToolUse(Agent|Task)                                        VALIDATE NOW, then allow or refuse
  PostToolUse(Edit|Write|MultiEdit|Bash|PowerShell)             early warning: validate what changed

ENFORCEMENT VALIDATES SYNCHRONOUSLY. IT DOES NOT TRUST A RECORD.
The first cut derived the block from a marker file that a PostToolUse sweep maintained, with a
size+mtime cache deciding what to re-check. Every one of those pieces turned out to be a way
through, and they were found in one review pass:

  * deleting the marker released the block PERMANENTLY, because the cache still said "seen"
  * writing a forged stamp into the cache made a corrupted file invisible to the sweep
  * `sed -i … && git commit` in ONE call committed before any sweep ran
  * `touch -r` (or plain `cp -p`, `tar -p`, `robocopy /COPY:T`) kept size and mtime, so the sweep
    skipped a rewritten file
  * a marker that could not be WRITTEN failed open while the message said everything was blocked
  * a corrupt marker with no ledger present deadlocked the repo with a remedy that could not work

The pattern is one mistake, not six: a gate whose verdict comes from a document that the guarded
party can influence is a gate on that document, not on the ledger. So the operations II.9 actually
protects — commit, push, merge, reports, dispatch — now run the validator against the ledger AT
THAT MOMENT and decide on the result. They are rare, the cost is one subprocess per ledger file,
and there is nothing left to forge. The stored state is a CACHE for the early-warning path only,
and is never consulted by the enforcing path.

WHY THE POST HALF STILL EXISTS: it cannot block (hooks reference — PostToolUse shows stderr but
does not deny), so it is not enforcement. What it buys is telling the agent that it just broke the
ledger, at the moment it broke it, instead of several tool calls later as an unexplained refusal
to commit. Spec II.9: "Ein Post-Edit-Fehler markiert den Zustand sichtbar ungueltig (behauptet
kein Rollback)."

THE VALIDATION LIVES IN `scripts/ledger_add.py --validate` — the same `validate_row` /
`validate_cross` the write path uses, so there is one definition of "valid ledger". That script is
part of the enforcement layer: `guard_harness_selfmod` blocks Edit/Write on it (verified by
`test_the_validator_is_on_the_enforcement_layer`), and this gate refuses shell writes to it.
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

import json  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402

import _compat  # noqa: E402

HOOK = "gate_ledger_valid"
FILE_TOOLS = ("Edit", "Write", "MultiEdit")
SHELL_TOOLS = ("Bash", "PowerShell")
SPAWN_TOOLS = ("Agent", "Task")
# Early-warning cache ONLY. Never read by the enforcing path, so forging it buys nothing; it is on
# guard_harness_selfmod's blocked list anyway, because a stale "everything is fine" note is still
# a lie the next reader believes.
STATE = os.path.join(".claude", "ledger_state.json")
VALIDATOR = os.path.join("scripts", "ledger_add.py")
# THE canonical ledger: `ledger/*.csv` at the repo root, nothing else. An earlier cut matched any
# path with a `ledger` component, which meant a bank export dropped in `inbox/ledger/` was judged
# against the accounting schema and blocked the whole project — and the enforcing sweep and the
# edit branch disagreed about which files they covered, so a file could be marked and then never
# re-checked. One definition, used by both.
LEDGER_DIR = "ledger"
# ...and a ledger file is `<4-digit-year>.csv`, because that is what `euer_report.py` reads
# (`ledger/%d.csv`). Any OTHER csv in the directory was an ID SOURCE for the validator's
# cross-file reversal lookup while being invisible to the report: a `scratch.csv` carrying a row
# with the reversed id made a reversal of a booking the report never sees validate clean, and the
# quarter then reported a negative total. A stray `2026 - Kopie.csv` does it by accident.
YEAR_FILE_RX = re.compile(r"^[0-9]{4}\.csv$", re.IGNORECASE)
# A ledger CSV validates in milliseconds; 20s already means something is badly wrong. The number
# used to be argued from the platform's per-hook default, which BUG-0062 measured away (see
# `_compat.HOOK_DEADLINE_SECONDS`): no registration of this gate names a `timeout` any more, so
# nothing outside this process bounds it, and these two constants are the whole bound there is.
VALIDATE_TIMEOUT = 20
# ...and a cap for the WHOLE run, so one broken file cannot turn a gate into a hung session. It is
# the process's own promise and it does not derive from anything: being killed is the one outcome
# this hook cannot turn into a refusal, and not being killed is the one thing it cannot arrange.
TOTAL_BUDGET = 40

# The follow-on operations II.9 names: "Dispatch, Commit, Merge und Reports". `git add` stays
# allowed: staging a CORRECTION is how the block gets resolved. A set of SUBCOMMANDS, matched
# through `_compat.git_invocations` and its `runs` test: the previous version spelled the whole
# invocation as a regex and therefore missed `git "commit"` on both views it searched — the raw
# text (the quotes sit where the pattern wants the verb) and the prose-stripped one (the span with
# the verb in it was deleted). What an operation IS cannot be a question about quoting, about
# which word stands in front of `git` (`sudo "git" commit -m x` reached HEAD with an INVALID
# ledger — measured, rc 0), or about whether the verb is spelled or computed.
_BLOCKED_GIT_SUBCOMMANDS = frozenset((
    "commit", "push", "merge", "rebase", "tag", "revert", "cherry-pick", "am", "format-patch",
    "bundle", "archive", "send-email"))
# ...and the report generators. `einvoice_extract` is deliberately NOT here: extracting a document
# reads nothing from the ledger, so blocking it stops the work that produces the correction.
_BLOCKED_SCRIPT_RX = re.compile(r"\beuer_report\b", re.IGNORECASE)
# The validator and the state file are enforcement, not data.
_PROTECTED_RX = re.compile(r"ledger_add\.py|ledger_state\.json", re.IGNORECASE)
# ...and a write into the DIRECTORY that holds them. `tar -xf evil.tar -C scripts/` names no
# protected FILE, so the file-level pattern saw nothing while the extraction replaced the
# validator — the same directory-destination blind spot the ledger path had in round 7, in the
# other half of the gate. Only used by `_writes_protected`, where a verb has already been judged
# non-reading, so `python scripts/ledger_add.py --validate` is unaffected.
# ...as a DESTINATION, not as a mention. Matching any path under `scripts/` refused `ruff check
# scripts/`, `bash scripts/setup.sh` and `chmod +x scripts/tool.sh` — none of which writes the
# validator. A destination is the bare directory after an extraction/output flag, after a copy or
# move, or as a redirect target; everything else is somebody doing ordinary work in that folder.
_PROTECTED_DIR_RX = re.compile(
    r"(?:-C|-d|--directory|-o|-O|--output|>|>>)\s*[\"']?(?:\./)?scripts/?(?=[\s\"';|&]|$)"
    r"|\b(?:cp|mv|copy-item|move-item|rsync|install)\b[^\n;|&]*?\s(?:\./)?scripts/?"
    r"(?=[\s\"';|&]|$)", re.IGNORECASE)
# A SECOND file called `ledger_add.py` outside `scripts/` has no legitimate reason to exist: the
# canonical one is protected, so a decoy is how you get a validator nobody guards.
_DECOY_VALIDATOR_RX = re.compile(
    r"(?<![\w/.-])(?!(?:\./)?scripts/)(?:[^\s;|&]*/)?ledger_add\.py", re.IGNORECASE)
# ...unless the command stepped INTO the directory first. `cd scripts && python ledger_add.py
# --validate …` is the sanctioned way out of a block, typed from inside the folder, and reading
# the bare name there as a decoy refused the remedy itself.
_CD_SCRIPTS_RX = re.compile(r"(?:^|[;&|])\s*cd\s+\.?/?scripts\b", re.IGNORECASE)
# A command that writes the ledger AND commits it in one breath. Validating synchronously cannot
# help here: the verdict is already stale when the same command rewrites the file afterwards, and
# the PostToolUse warning arrives after the commit is in HEAD. So this shape is refused outright,
# valid ledger or not — the remedy is to run the two halves as two calls, which costs nothing.
# Two shapes: a named CSV, and the bare DIRECTORY as a destination. The second was missing, and
# `mv export-2027.csv ledger/ && git add -A && git commit -m 'import'` therefore dropped a broken
# file into the ledger and committed it in one call -- verified end to end, with the bad row in
# HEAD. A trailing `ledger/` is the natural way to write "put the corrected export in there", and
# the explicit-filename forms were the only ones ever checked.
_LEDGER_PATH_RX = re.compile(
    # ANYTHING under the directory, not only `*.csv`: `split -l 500 big.csv ledger/part-` writes
    # a family of files whose names the pattern could not predict, and a write into the ledger
    # directory is a write into the ledger whatever the file ends up being called.
    r"\bledger/[^\s;|&]*"
    # ...and the directory named WITHOUT a trailing slash, which `cp file ledger` also writes into.
    # Bounded so it is a whole path token: `(?<![\w/.-])` keeps `/tmp/ledger` and `ledger_add.py`
    # out (`_` is a word character, so there is no boundary inside `ledger_add`), and this only
    # ever matters when `_SHELL_WRITE_RX` has already matched somewhere in the same command.
    r"|(?<![\w/.-])ledger(?=[\s;|&]|$)", re.IGNORECASE)
# ...plus the working-directory form. `gate_write_scope` in this kit already tracks `cd` carry-over
# and directory-form stars; this rule needs only the narrow case, because it decides ONE question:
# does this command write a ledger file. Missed before: `cd ledger && sed -i … 2026.csv`,
# `sed -i … ledger/*.csv`, and `ledger//2026.csv`.
_CD_LEDGER_RX = re.compile(r"(?:^|[;&|]|\bcd\s)\s*cd\s+\.?/?ledger\b", re.IGNORECASE)
# A commit MESSAGE is prose, not code. `git commit -m 'restore ledger/2026.csv from backup'` was
# refused as "this command WRITES a ledger file and then commits in the same call" -- for a command
# that writes nothing, with a remedy ("run it as two calls") that cannot be followed when there is
# only one. Worse, `git restore ledger/2026.csv && git commit -m 'undo bad edit'` -- the remedy this
# gate itself advertises -- was blocked by the same accident.
# The unquoted alternative was dropped for one round: `-m <(sed -i … ledger/2026.csv)` had its
# WRITE VERB stripped away and left the path behind, so the write-and-commit rule found nothing to
# object to -- bash performs process substitution in an unquoted argument, so the `sed` really ran.
# It is back, because `_SHELL_CODE_IN_TEXT_RX` now knows `[<>]\(` and the token no longer strips.
# Without it, `git commit -m restore -- ledger/2026.csv` was refused: a ONE-WORD message that
# happens to be a git write verb, conjoined with the path.
# ...and the FLAG NAMES are case-SENSITIVE inside an otherwise case-insensitive pattern, because a
# flag letter's case is what tells two different flags apart. Measured while widening the
# interpreter-option rule below: `-b` matched `-B`, so `python -B tools/ledger_add.py && git commit`
# had the span `-B tools/ledger_add.py` removed as if it were a commit MESSAGE -- the decoy
# validator disappeared from the view before anything judged it. Nothing here needs the folding:
# these are git's own flags, and git does not accept them in another case.
_MESSAGE_ARG_RX = re.compile(
    r"(?-i:(?:-m|--message|--body|-b|--notes|--squash-message))(?:=|\s+)"
    r"(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[^\s;|&]+)", re.IGNORECASE)


# `$(…)`, backticks and `${…}` inside a message payload are EXECUTED by the shell. Stripping the
# payload as prose therefore hid a real write: `git commit -m "$(sed -i s/119/150/
# ledger/2026.csv)"` broke the ledger and committed it in one call, and the gate allowed it —
# verified end to end, with the bad row in HEAD. A payload is prose only if it is inert.
# ...and even a quoted payload is code when the shell will expand it. `<(…)`/`>(…)` are process
# substitution, `$(…)`/backticks command substitution, `${…}`/`$NAME` parameter expansion -- the
# last one cannot write by itself but can carry a path the surrounding logic then misses.
_SHELL_CODE_IN_TEXT_RX = re.compile(r"\$\(|`|\$\{|\$[A-Za-z_]|[<>]\(")


def _payload_is_inert(payload):
    """Can the shell execute anything inside this `-m` argument?

    A SINGLE-quoted payload is inert by construction: bash performs no expansion at all inside
    single quotes -- no `$(…)`, no backticks, no `${…}`, no `$NAME`. Testing it for code shapes
    anyway refused three commit messages that write nothing (`-m 'rm ledger/2026.csv from $HOME
    was wrong'`), which is the false-positive class this whole prose filter exists to remove.
    Double-quoted and unquoted payloads get the full check.
    """
    if payload.startswith("'") and payload.endswith("'"):
        return True
    return not _SHELL_CODE_IN_TEXT_RX.search(payload)


def _without_messages(command):
    """The command with INERT `-m <text>` payloads removed — quoted PATHS and code both survive."""
    return _MESSAGE_ARG_RX.sub(
        lambda m: " " if _payload_is_inert(m.group(1)) else m.group(0),
        command or "")


# `cp ledger/2026.csv /tmp/backup.csv` COPIES OUT: the ledger is the source, the destination is
# elsewhere, and nothing in the ledger changes. Only the two-argument form is recognised, because
# that is where source and destination are unambiguous.
#
# `mv` is NOT in this list, and that is the whole distinction: a move DELETES the source. `mv
# ledger/2026.csv /tmp/ && git commit` took a year's books out of the repo and committed the
# deletion, after which `judge()` found no 2026.csv and every later check was clean -- the data
# was gone and the gate was satisfied. A copy-out is a read; a move-out is a delete.
_COPY_OUT_RX = re.compile(
    r"\b(?:cp|copy-item)\b(?:\s+-{1,2}[\w-]+)*\s+"
    r"(?P<src>[^\s;|&]+)\s+(?P<dst>[^\s;|&]+)", re.IGNORECASE)

# READ-ONLY ALLOWLIST, not a write denylist. Four review rounds in a row, the finding was "another
# spelling the denylist did not have" -- `curl -o`, `wget -O`, `tar -C`, `unzip -d`, `split`,
# `awk -i inplace`, `sort -o`, all writing into `ledger/` and committing in one call. The PATH half
# of this rule stopped generating those the moment it was rewritten from "the shapes I thought of"
# to "what a ledger path IS"; the verb half had kept the old shape. `gate_write_scope` in this same
# kit already decides this the durable way, and this is that decision, scoped to one question:
# a segment that touches a ledger path is a WRITE unless its verb is known to only read.
_READ_ONLY_VERBS = frozenset((
    "cat", "type", "bat", "head", "tail", "less", "more", "wc", "nl", "od", "xxd", "strings",
    "grep", "egrep", "fgrep", "rg", "ag", "ack", "diff", "cmp", "comm", "file", "stat",
    "ls", "dir", "tree", "basename", "dirname", "realpath", "readlink", "pwd", "du", "df",
    "uniq", "cut", "tr", "jq", "yq", "test", "echo", "printf", "base64", "column",
    # conditionally read-only -- `_LEDGER_WRITE_FLAGS` is what actually decides for these
    "sed", "awk", "gawk", "mawk", "sort", "find", "tee",
    "md5sum", "sha1sum", "sha256sum", "cksum", "cd", "pushd", "popd", "true", "false",
    # PowerShell
    "get-content", "get-childitem", "select-string", "test-path", "get-item", "resolve-path",
    "get-filehash", "compare-object", "measure-object", "select-object", "set-location",
    "import-csv", "gc", "sls", "gci", "gi", "ls-object",
))
# ...the flags that turn a reading verb into a writing one (same table `gate_write_scope` learned
# the hard way: `"--in-place".startswith("-i")` is False, so a short-flag test alone missed it)
_LEDGER_WRITE_FLAGS = {
    "sed": ("-i", "--in-place"),
    "awk": ("-i", "--in-place"),
    "gawk": ("-i", "--in-place"),
    "mawk": ("-i", "--in-place"),
    "sort": ("-o", "--output"),
    "find": ("-delete", "-exec", "-execdir", "-fprint", "-fls", "-ok"),
    "tee": ("",),          # tee always writes its argument
}
# git subcommands that cannot modify a working-tree FILE. `checkout`, `restore`, `stash`, `mv`,
# `rm`, `clean` and `apply` are absent because each of them can -- and so are `merge`, `rebase`,
# `revert`, `cherry-pick` and `am`, which a first cut listed here on the false reasoning that they
# "cannot modify a ledger file". They write working-tree files by definition. Nothing needed them
# in this set: whether those operations are permitted at all is `_BLOCKED_GIT_SUBCOMMANDS`'s
# question.
_READ_ONLY_GIT = frozenset((
    "add", "status", "diff", "log", "show", "commit", "push", "fetch", "remote", "branch",
    "config", "rev-parse", "ls-files", "blame", "describe", "tag", "bundle", "format-patch",
    "archive", "send-email", "shortlog", "grep", "cat-file",
))
# A PIPELINE IS ONE UNIT. `|` is deliberately NOT a separator: `find ledger -name 2026.csv |
# xargs sed -i …` puts the path in one stage and the write verb in the next, and judging the
# stages apart called both halves harmless — segment one had a read verb, segment two had no
# ledger path. That is the structural cost of per-segment analysis, and the pipe is the construct
# that pays it. `gate_write_scope` in this kit made the same discovery and treats a pipeline as
# one unit for exactly this reason.
_SEGMENT_SPLIT_RX = re.compile(r"&&|\|\||[;&\n]")
# A substitution OPENS a new command, so it has to open a new SEGMENT.
_SUBSTITUTION_OPEN_RX = re.compile(r"\$\(|<\(|>\(|`")
# NORMALISE BEFORE SPLITTING, rather than adding a separator case per spelling. Four ordinary
# forms tore the pipeline unit apart again and left the path in one segment with the write verb in
# the next: a backslash-newline continuation (which is simply how a long command is FORMATTED), a
# newline after the pipe, a newline inside the first stage, and `|&`. Each is the same pipeline
# written differently, so the answer is to make them one shape first — the same move that ended
# the path and verb enumerations two rounds ago. The continuation itself comes from
# `_compat.join_line_continuations` — this hook's own copy joined with a SPACE, so a continuation
# INSIDE a token (`led\<newline>ger/2026.csv`) split the very path the rule is about.
_PIPE_AMP_RX = re.compile(r"\|&")
_NEWLINE_AROUND_PIPE_RX = re.compile(r"\s*\n\s*\|\s*|\s*\|\s*\n\s*")


def _normalise_pipeline(text):
    """One shape for every way a shell can spell the same pipeline.

    THE BODY OF A LITERALLY-QUOTED HERE-DOCUMENT IS NOT A PIPELINE, and this gate was the last
    reader in the kit that still judged it as one. `_compat.literal_heredoc_free` is that rule --
    a quoted delimiter means POSIX expands nothing in the body, and a body handed to a command
    PARSER (`sh <<'EOF'`) is kept for exactly that reason. Measured in pilot 4 (`P4-12`): the
    office manager's `git commit -m "$(cat <<'EOF' … EOF)"` was refused because a line of its
    MESSAGE read "bookkeeper booked ledger entry L2025-0001" -- a ledger path plus a word this
    reader took for a verb. Nothing about that command touched a file.
    """
    text = _compat.join_line_continuations(_compat.literal_heredoc_free(text))
    text = _PIPE_AMP_RX.sub("|", text)
    text = _NEWLINE_AROUND_PIPE_RX.sub(" | ", text)
    # ...and a newline whose next line begins with a FLAG continues the same command. Splitting
    # there put `find ledger` in one segment and `-name 2026.csv | xargs sed -i` in the next,
    # so the path and the write verb were judged apart again.
    return _NEWLINE_BEFORE_FLAG_RX.sub(" ", text)


_NEWLINE_BEFORE_FLAG_RX = re.compile(r"\s*\n\s+(?=-)")
_REDIRECT_INTO_RX = re.compile(r">>?\s*[\"']?(?P<target>[^\s\"';|&]+)")
# `python scripts/ledger_add.py …` is the VALIDATED write path: it refuses bad data before it
# writes, so a row it produces is valid by construction. Every other interpreter invocation --
# another script, or any inline `-c`/`-e`/`-m` payload -- is a write this gate cannot vouch for.
# ...and the exemption is anchored to the CANONICAL path. Matching `\S*ledger_add\.py` granted it
# by BASENAME, so `python tools/ledger_add.py && git commit` and even
# `python /tmp/evil/ledger_add.py ledger/2026.csv && git commit` were waved through -- and
# `guard_harness_selfmod` protects exactly `scripts/ledger_add.py`, so writing the decoy was
# allowed. The exemption now names the same file the protection does.
# WHICH INTERPRETER OPTIONS MAY STAND BETWEEN THE INTERPRETER AND ITS SCRIPT, as a property rather
# than as the letters somebody had in mind: any option word that carries no `c`/`e`/`m` in it. Those
# three are the ones that make the interpreter read its program from the COMMAND LINE instead of the
# script, which is exactly what these patterns must never step over -- everything else (`-B`, `-E`,
# `-S`, `-u`, `-I`, `-P`, a cluster like `-Bu`) only changes how the named script is run. The old
# class `[EOSuvWx]` was a list, and `-B` was measured missing from it: `python -B scripts/harness.py
# --summary '…ledger_add.py'` stayed refused while the same line without `-B` passed. Case-sensitive
# on purpose (`(?-i:…)`) although the surrounding pattern is not: `-E` is an option, `-e` is a
# payload flag, and folding them together would give up the one distinction this makes.
_INTERPRETER_OPTIONS = r"(?:\s+(?-i:-(?![^\s]*[cem])[^\s]*))*"
_LEDGER_ADD_RUN_RX = re.compile(
    r"(?:^|[;&|(])\s*(?:python[0-9.]*|py)\b" + _INTERPRETER_OPTIONS + r"\s+"
    r"(?:\./)?scripts/ledger_add\.py\b(?![^\n]*\s-(?:c|e|m)\b)", re.IGNORECASE)
# ...and the KERNEL'S OWN ENTRY POINT, which is not a shell write either. It carries an envelope,
# a summary and a reason as ARGUMENTS -- prose that names the ledger and its validator whenever the
# work did (measured, pilot 4 `P4-12`: `submit-result --summary "… via ledger_add.py …"` was refused
# as a write to the judge, and the office manager reported a gate blocking a commit "on the word
# ledger"). What it can reach is decided by the kernel and its own gates, not by this one: no
# command of it names `ledger/*.csv`, and the one route it has to `scripts/ledger_add.py` is an
# installer run (`update-kit`/`set-preset`, each on a user-minted approval), which is exactly how
# this gate's own remedy says the validator legitimately changes. Anchored to the canonical path and
# refused an inline payload for the same measured reason as the line above: a copy elsewhere is a
# program nobody vouched for. A REDIRECT is judged before this exemption is reached, so the entry
# point with its output sent into `ledger/2026.csv` is still a write.
_ENTRY_POINT_RUN_RX = re.compile(
    r"(?:^|[;&|(])\s*(?:python[0-9.]*|py)\b" + _INTERPRETER_OPTIONS + r"\s+"
    r"(?:\./)?scripts/harness\.py\b(?![^\n]*\s-(?:c|e|m)\b)", re.IGNORECASE)


def _stages_beside_the_entry_point(segment):
    """The pipeline stages of `segment` that are NOT an entry-point invocation.

    PER STAGE, and that is a correction of this same round rather than a refinement: the exemption
    was first written as `if _ENTRY_POINT_RUN_RX.search(segment): continue`, which threw away the
    whole segment as soon as the entry point appeared ANYWHERE in it -- so every other stage of the
    pipeline came free with it. Measured: `python scripts/harness.py doctor | tee
    scripts/ledger_add.py` was exit 2 before that exemption and exit 0 after it, and the same for
    `| tee .claude/ledger_state.json` and an `xargs cp` in the second stage. What the exemption is
    ABOUT is the prose an entry-point invocation carries in its own arguments, and that lives in
    ITS stage; a neighbouring stage is a different command and is judged like any other
    (`tools/test_hooks_v2.py::test_the_same_constructs_still_refuse_a_real_write`).
    """
    return [stage for stage in segment.split("|")
            if stage.strip() and not _ENTRY_POINT_RUN_RX.search(stage)]


def _verb_of(segment):
    """The command word of a segment, lowercased and stripped of its path."""
    for token in segment.split():
        cleaned = token.strip("\"'")
        if cleaned.startswith("-"):
            continue
        # `FOO=1 cat x` -- an env-var PREFIX is not the verb. The first cut wrote
        # `"=" in cleaned.split("/")[0][:0]`, and `[:0]` is always the empty string, so the branch
        # could never be true: dead code that read as a handled case.
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", cleaned):
            continue
        # ...and the wrappers that put the real verb one token later
        base = os.path.basename(cleaned.replace("\\", "/")).lower().removesuffix(".exe")
        if base in ("env", "nohup", "command", "time", "stdbuf", "nice"):
            continue
        return base
    return ""


def _verb_only_reads(segment):
    tokens = segment.split()
    verb = _verb_of(segment)
    if verb == "git":
        following = [t for t in tokens[1:] if not t.startswith("-")]
        return bool(following) and following[0].lower() in _READ_ONLY_GIT
    if verb not in _READ_ONLY_VERBS:
        return False
    writers = _LEDGER_WRITE_FLAGS.get(verb)
    if not writers:
        return True
    for flag in writers:
        if flag == "":
            return False
        for token in tokens:
            low = token.lower()
            if low == flag or low.startswith(flag + "="):
                return False
            if (len(flag) == 2 and flag.startswith("-") and low.startswith("-")
                    and not low.startswith("--") and flag[1] in low[1:]):
                return False
    return True


def _writes_protected(command):
    """Does this command WRITE the validator or the state file (rather than read or run them)?"""
    text = _SUBSTITUTION_OPEN_RX.sub(
        " ; ", _normalise_pipeline(command or "").replace("\\", "/"))
    # ...and `cd scripts && python ledger_add.py --validate …` runs the CANONICAL validator from
    # inside its own directory, which is the sanctioned way out of a block.
    inside_scripts = _CD_SCRIPTS_RX.search(text) is not None
    for segment in _SEGMENT_SPLIT_RX.split(text):
        segment = segment.strip()
        if inside_scripts and re.search(r"ledger_add\.py", segment, re.IGNORECASE)                 and not _REDIRECT_INTO_RX.search(segment):
            continue
        if not (_PROTECTED_RX.search(segment) or _PROTECTED_DIR_RX.search(segment)):
            continue
        redirect = _REDIRECT_INTO_RX.search(segment)
        if redirect and (_PROTECTED_RX.search(redirect.group("target"))
                         or _PROTECTED_DIR_RX.search(redirect.group("target"))):
            return True
        # the kernel's entry point is not a shell write, so ITS stage is dropped -- and only its
        # stage: every other one of the pipeline is judged below exactly as before.
        stages = _stages_beside_the_entry_point(segment)
        if not stages or all(_verb_only_reads(stage) for stage in stages):
            continue
        copy = _COPY_OUT_RX.search(segment)
        if (copy and _PROTECTED_RX.search(copy.group("src"))
                and not _PROTECTED_RX.search(copy.group("dst"))):
            continue          # copying the validator OUT is a read (round-8 NIT-3)
        return True
    return False


def _writes_ledger(command):
    """Does this command write a canonical ledger file?

    PER SEGMENT, so the verb that matters is the one in the same breath as the path -- `grep -r
    ledger . > /tmp/hits && git commit` reads, and judging the whole command at once called it a
    write because `>` appeared somewhere in it.

    Slashes are collapsed first (`ledger//2026.csv` is the same path) and the working-directory
    form is handled separately, because `cd ledger && sed -i 2026.csv` names no `ledger/` path.
    """
    text = re.sub(r"/{2,}", "/", _normalise_pipeline(command or "").replace("\\", "/"))
    # Without this, ALL of `git commit -m "$(sed -i … ledger/2026.csv)"` is one segment whose verb
    # is `git commit` — read-only as far as the ledger goes — and the `sed -i` inside it is never
    # examined. That is the round-6 bypass reappearing through the round-9 rewrite, which is
    # exactly the kind of thing a rewrite is most likely to do.
    text = _SUBSTITUTION_OPEN_RX.sub(" ; ", text)
    # A DECOY validator, checked before the loop because the command need not name a ledger path
    # at all: `python tools/ledger_add.py && git commit` runs a script this gate cannot vouch for
    # and commits whatever it did. The canonical one is protected precisely so that it CAN be
    # vouched for; a second copy elsewhere is how you get one that nobody guards.
    # ...but only in a segment that does something OTHER than read it, and not when the command
    # has stepped into `scripts/` first. `cat ledger_add.py && git commit` reads it, and
    # `cd scripts && python ledger_add.py --validate …` is the sanctioned way out of a block,
    # typed from inside the directory — refusing either one blocks the remedy.
    inside_scripts = _CD_SCRIPTS_RX.search(text) is not None
    for segment in _SEGMENT_SPLIT_RX.split(text):
        if inside_scripts:
            break
        # ...asked of the stages BESIDE the entry point, so a decoy path named in ITS arguments is
        # prose while one in a neighbouring stage is still a decoy (`_stages_beside_the_entry_point`)
        stages = _stages_beside_the_entry_point(segment.strip())
        if (any(_DECOY_VALIDATOR_RX.search(stage) for stage in stages)
                and not all(_verb_only_reads(stage) for stage in stages)):
            return True
    for segment in _SEGMENT_SPLIT_RX.split(text):
        segment = segment.strip()
        if not segment or not _LEDGER_PATH_RX.search(segment):
            continue
        # a redirect INTO a ledger path is a write whatever the verb in front of it
        redirect = _REDIRECT_INTO_RX.search(segment)
        if redirect and _LEDGER_PATH_RX.search(redirect.group("target")):
            return True
        if _DECOY_VALIDATOR_RX.search(segment):
            return True                       # a second `ledger_add.py` is a validator nobody guards
        if inside_scripts and re.search(r"\bledger_add\.py\b", segment, re.IGNORECASE):
            continue          # the canonical validator, run from inside its own directory
        if _LEDGER_ADD_RUN_RX.search(segment):
            continue                          # the validated write path vouches for itself
        # ...and the entry point's OWN stage is dropped for the reason `_stages_beside_the_entry_
        # point` carries; what stands beside it is judged as before. A redirect was decided above,
        # so nothing the entry point could carry into the ledger passes here.
        stages = _stages_beside_the_entry_point(segment)
        if not stages or all(_verb_only_reads(stage) for stage in stages):
            continue                          # every stage of the pipeline only reads
        copy = _COPY_OUT_RX.search(segment)
        if (copy and _LEDGER_PATH_RX.search(copy.group("src"))
                and not _LEDGER_PATH_RX.search(copy.group("dst"))):
            continue                          # copying the ledger OUT is a read
        return True
    # ...and the working-directory form, which names no ledger path at all
    if _CD_LEDGER_RX.search(text) and re.search(r"\.csv\b", text, re.IGNORECASE):
        for segment in _SEGMENT_SPLIT_RX.split(text):
            if re.search(r"\.csv\b", segment, re.IGNORECASE) and not _verb_only_reads(segment):
                return True
    return False
_SHELL_WRITE_RX = re.compile(
    r"\b(?:sed|tee|cp|mv|rm|del|dd|truncate|install|patch|shred|ren|rename|mklink|ln)\b"
    r"|>>?|\bset-content\b|\badd-content\b|\bout-file\b|\bcopy-item\b|\bremove-item\b"
    r"|\bmove-item\b|\brename-item\b|\bnew-item\b|\bclear-content\b"
    # git can WRITE a working-tree file, which no verb list thinks of as a write
    r"|\bgit\b[^\n]*\b(?:checkout|restore|stash)\b"
    # interpreter write idioms. An earlier cut traded the blunt `perl|ruby|node` verbs for this
    # list and lost six routes with them (`perl -i -pe`, `appendFileSync`, `copyFileSync`,
    # `os.rename`, `os.replace`, `ruby -i`), so BOTH are here now: the verbs below catch the
    # in-place flag, the idioms catch an inline payload that spells the write out.
    r"|\b(?:perl|ruby|node|python[0-9.]*|py)\b[^\n]*\s-[a-z]*i\b"
    r"|\bopen\s*\([^)]*['\"][wax+]|\b(?:write|append|copy|rename)filesync\b"
    r"|\bos\.(?:remove|unlink|rename|replace|truncate|rmdir)\b|\bshutil\.\w+"
    r"|\bpathlib\b|\bunlinksync\b|\bwrite_text\b|\bwrite_bytes\b|\brenamesync\b",
    re.IGNORECASE)
# RUNNING the validator is how the agent gets out of the block, so `python scripts/ledger_add.py
# --validate …` must stay allowed. ONLY that shape: an interpreter invoked with `-c`/`-e`/`-m`
# carries its payload inline and is never exempt.
_INTERPRETER_SCRIPT_RX = re.compile(
    r"(?:^|(?<=[;&|(]))\s*(?:python[0-9.]*|py|perl|ruby|node)" + _INTERPRETER_OPTIONS +
    r"\s+(\S+\.(?:py|pl|rb|js))\b", re.IGNORECASE | re.MULTILINE)
_INLINE_CODE_RX = re.compile(r"(?:^|[;&|(])\s*(?:python[0-9.]*|py|perl|ruby|node)\s+"
                             r"[^\s]*-(?:c|e|m)\b", re.IGNORECASE | re.MULTILINE)


def _ledger_csvs_in(root):
    """Every canonical ledger file. One definition for the edit branch and the enforcing path.

    `os.listdir`, NOT `glob`: `glob.escape` fixes the metacharacter case but leaves the failure
    mode intact for the next one. A project at `.../Kunde [GmbH]/proj` made `glob` return ZERO
    files while the directory held one, and `judge()` reads "no files" as "nothing invalid" — so
    commit, push, merge, reports and dispatch were all allowed with a broken ledger in place, on a
    path an office workspace plausibly has (`[`, `]` are legal on Windows and POSIX; `*` and `?`
    extend it on POSIX). Listing the directory cannot be fooled by the project's own name.
    """
    directory = os.path.join(root, LEDGER_DIR)
    try:
        names = os.listdir(directory)
    except OSError:
        return []
    # EVERY csv here, including one whose name is not a year. The validator refuses those (they are
    # invisible to `euer_report.py` while sitting where the ledger lives), and filtering them out
    # HERE would mean the gate never presents the file whose refusal is the whole point: a stray
    # `2026 - Kopie.csv` would then be silently ignored rather than flagged, and the script's rule
    # and the gate's view would disagree again — which is the mistake that produced B6.
    return sorted(os.path.join(directory, name) for name in names
                  if name.lower().endswith(".csv"))


def _is_ledger(path, root):
    """(rel, absolute) when `path` IS one of ours, else None. Path identity, not name matching."""
    try:
        absolute = os.path.abspath(path)
        rel = os.path.relpath(absolute, root).replace("\\", "/")
    except (OSError, ValueError):
        return None
    if rel.startswith("../") or os.path.isabs(rel):
        return None  # outside the repo: not this project's ledger
    parts = rel.split("/")
    if len(parts) != 2 or parts[0].lower() != LEDGER_DIR or not parts[1].lower().endswith(".csv"):
        return None
    return rel, absolute


def _stamp(absolute):
    """Change detection for the EARLY-WARNING path only.

    Deliberately cheap and deliberately not trusted: size+mtime is defeated by `touch -r` and by
    any same-length rewrite. That was a hole while the block depended on it; now the enforcing
    path re-validates unconditionally, so the worst a defeated stamp costs is a late warning.
    """
    try:
        info = os.stat(absolute)
    except OSError:
        return None
    return "%d:%d" % (info.st_size, info.st_mtime_ns)


def _validator_argv(script, absolute):
    """The interpreter invocation, with the SCRIPT DIRECTORY off `sys.path`.

    Python puts the script's own directory at `sys.path[0]`, so running `<root>/scripts/
    ledger_add.py` made `<root>/scripts` the first import location — and `scripts/` is ordinary
    project code an agent may write. One `Write scripts/csv.py` containing `import sys;
    sys.exit(0)` therefore shadowed the stdlib module the validator imports, the validator exited
    0, and every ledger looked clean. No shell involved, and protecting `ledger_add.py` itself did
    nothing, because the bypass never touches it.

    The synchronous design makes this the WHOLE gate rather than a corner: every commit, push,
    merge, report and dispatch decision now runs this interpreter. `-P` (3.11+) drops the script
    directory; `-E` ignores `PYTHONPATH`/`PYTHONSTARTUP`; `-s` drops the user site directory; and
    `-S` skips `site` entirely, which is the only one that stops `.pth` PROCESSING.
    That last one closed a live bypass: `.venv/` is writable (the shipped `.gitignore` invites an
    in-repo venv, and `requirements-office.txt` asks for one), so two Writes — a
    `site-packages/zz_evil.pth` containing `import zz_evil`, and a `zz_evil.py` registering an
    `atexit` hook that calls `os._exit(0)` when `--validate` is in argv — made the validator exit 0
    WHILE STILL PRINTING its findings. `-S` is safe here because the validator imports stdlib only.
    Below 3.11 `-P` does not exist, so it is omitted and `python scripts/harness.py doctor` reports the gap rather
    than this file pretending to close it.
    """
    flags = ["-S", "-E", "-s"]
    if sys.version_info >= (3, 11):
        flags.insert(0, "-P")
    return [sys.executable] + flags + [script, "--validate", absolute]


def _validate(root, absolute):
    """Run the project's own validator. Anything that is not a clean exit 0 is a FINDING.

    A missing validator, a timeout, an interpreter that will not start: "nothing can judge this
    file" and "this file is fine" are the same outcome only if you are willing to ship the
    difference, and this is money data.
    """
    script = os.path.join(root, VALIDATOR)
    if not os.path.isfile(script):
        return ["%s is missing, so this ledger cannot be validated at all" % VALIDATOR]
    try:
        result = _compat.run_captured(_validator_argv(script, absolute),
                                      cwd=root, timeout=VALIDATE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return ["the validator did not finish within %ds, so this file is UNJUDGED"
                % VALIDATE_TIMEOUT]
    except OSError as exc:
        return ["the validator could not be started (%s), so this file is UNJUDGED" % exc]
    # THE OUTPUT IS READ FIRST, and an `INVALID:` line counts even on exit 0. Belt and braces
    # beside `-S`: the `.pth` bypass suppressed the exit CODE while the findings were still on
    # stderr, so anything that only forges the status now has to silence the output too.
    findings = [line.split("INVALID: ", 1)[-1] for line in (result.stderr or "").splitlines()
                if "INVALID:" in line]
    if findings:
        return findings
    if result.returncode == 0:
        return []
    return ["validator exited %d: %s" % (result.returncode, (result.stderr or "").strip()[:200])]


def judge(root):
    """Validate the ledger NOW and return {rel: findings}. The enforcing path calls this.

    No cache is consulted. That is the whole point: the previous design asked a file the guarded
    party could write whether the guarded party had broken anything.

    A TOTAL budget, not just a per-file one: 12 ledger files each taking the full per-file cap is
    241s of a session standing still on one `git add`. Running out of budget is itself a finding,
    because "we did not get to look" is not "it is fine" — and it is a finding this gate can still
    report, which is the difference between a bound it keeps itself and one imposed from outside
    (`_compat.HOOK_DEADLINE_SECONDS` carries what was measured about those).
    """
    verdicts, unreached = {}, []
    started = time.monotonic()
    targets = _ledger_csvs_in(root)
    for absolute in targets:
        rel = os.path.relpath(absolute, root).replace("\\", "/")
        # room for a FULL per-file timeout, not merely "budget left": checking `elapsed >
        # TOTAL_BUDGET` before starting let a file begin at 39.9s and run to 59.9s -- measured at
        # 52.5s for 5 files x a 13s validator, i.e. half again over the cap this line exists to
        # keep. The guaranteed bound is now TOTAL_BUDGET.
        if time.monotonic() - started > TOTAL_BUDGET - VALIDATE_TIMEOUT:
            unreached.append(rel)
            continue
        findings = _validate(root, absolute)
        if findings:
            verdicts[rel] = findings
    return verdicts, unreached


def _read_state(root):
    path = os.path.join(root, STATE)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_state(root, data):
    path = os.path.join(root, STATE)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp-%d" % os.getpid()
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False, sort_keys=True)
        os.replace(tmp, path)
    except OSError:
        pass  # an unwritable cache costs a warning, never a released block: see judge()


def _remember(root, rel, findings, stamp):
    state = _read_state(root)
    entry = {"findings": findings[:20]}
    if stamp:
        entry["stamp"] = stamp
    state[rel] = entry
    _write_state(root, state)


# -- the enforcing path -------------------------------------------------------

def _refuse_if_invalid(root, what):
    verdicts, unreached = judge(root)
    if not verdicts and not unreached:
        return
    # BROKEN and NOT-LOOKED-AT are reported as two different things. Listing the unreached files
    # as findings told the operator that all six ledgers were broken when two were slow and four
    # were never opened -- and the remedy ("correct the rows") applied to neither kind.
    detail = []
    for rel in sorted(verdicts):
        detail.append("  %s:" % rel)
        detail.extend("    - " + f for f in verdicts[rel][:6])
    if unreached:
        detail.append("  NOT CHECKED — the %ds budget for the whole ledger ran out before these "
                      "files were opened; they may be fine or broken:" % TOTAL_BUDGET)
        detail.extend("    - " + rel for rel in sorted(unreached))
    remedy = ("correct the rows, or `git restore` the file — as its OWN call, then commit in a "
              "second one; writing and committing in one command is refused separately. Nothing "
              "has to be cleared afterwards: the next attempt re-validates. "
              "`python %s --validate <file>` shows the detail." % VALIDATOR)
    if unreached:
        remedy += (" For the unchecked files, validate them one at a time — a ledger that needs "
                   "more than %ds is a defect in its own right, and this gate stops looking at "
                   "its own budget rather than leaving the session standing still."
                   % VALIDATE_TIMEOUT)
    _kernel.block(
        HOOK,
        # The headline still says INVALID when something IS invalid: splitting "broken" from
        # "not looked at" must not cost the one word that tells the reader what happened.
        "%s — %s is blocked (spec II.9). This was checked against the files just now, not read "
        "from a note.\n%s"
        % ("the ledger is INVALID right now" if verdicts
           else "the ledger could not be fully checked", what, "\n".join(detail[:24])),
        remedy=remedy)


def handle_pre_tool_use(data):
    root = _kernel.find_repo_root(data.get("cwd"))
    tool = data.get("tool_name")
    if tool in SPAWN_TOOLS:
        _refuse_if_invalid(root, "specialist dispatch")
    elif tool in SHELL_TOOLS:
        raw = str((data.get("tool_input") or {}).get("command") or "")
        # ONE view, the one the shell hands git: quote marks gone, their content kept. That is
        # what makes `eval "git commit -m x"` visible here without a second search over the raw
        # text — the workaround the deleted prose-stripping reader needed.
        text = _compat.git_argument_text(raw)
        blocked_op = (any(invocation.runs(*_BLOCKED_GIT_SUBCOMMANDS)
                          for invocation in _compat.git_invocations(raw))
                      or _BLOCKED_SCRIPT_RX.search(text) or _BLOCKED_SCRIPT_RX.search(raw))
        if blocked_op and _writes_ledger(_without_messages(raw)):
            _kernel.block(
                HOOK,
                "this command touches a ledger file with a writing command and then "
                "commits/pushes/reports in the SAME call. (It may only be reading it — a shell "
                "command's source and destination are not reliably distinguishable, and for money "
                "data the over-block costs one extra call while the under-block costs a bad "
                "commit.) Checking the ledger first cannot help: the verdict is stale the moment the "
                "command rewrites the file, and the warning afterwards arrives with the bad data "
                "already in HEAD (spec II.9 keeps commit blocked until the books are correct). "
                "`git restore ledger/<year>.csv && git commit` is refused for the same reason and "
                "is NOT an exception — a restored file can be a previously committed broken one.",
                remedy="split it into two calls: write (or restore) the ledger first, then commit "
                       "separately. The second call re-validates and refuses if the write broke "
                       "anything, which is the whole point.")
        if blocked_op:
            _refuse_if_invalid(root, "this command (commit/push/merge/report)")
        # a shell write to the judge itself. An interpreter running a SCRIPT is exempt (that is how
        # `--validate` gets run); an interpreter with an inline `-c`/`-e`/`-m` payload never is.
        scanned = raw if _INLINE_CODE_RX.search(raw) else _INTERPRETER_SCRIPT_RX.sub(
            lambda m: m.group(0)[:m.start(1) - m.start(0)], raw)
        # SAME allowlist decision as `_writes_ledger`. This branch kept the old write DENYLIST
        # for one round longer, so the very verbs just removed from it still worked here:
        # `curl -o scripts/ledger_add.py` installs a WORKING stub and releases the block outright
        # -- the round-3 escape, reachable again through a verb the denylist never knew.
        # the DIRECTORY too, or `tar -xf evil.tar -C scripts/` never reaches the write check at
        # all: it names no protected FILE, and the outer condition was the file pattern alone.
        if ((_PROTECTED_RX.search(scanned) or _PROTECTED_DIR_RX.search(scanned))
                and _writes_protected(raw)):
            _kernel.block(
                HOOK,
                "'%s' and '%s' are the ledger's JUDGE, not project data — a shell write to either "
                "would let the agent under a ledger block rewrite what decides the block."
                % (VALIDATOR, STATE),
                remedy="fix the ledger rows instead. If the validator itself is wrong, that is an "
                       "infrastructure defect: report it to the user; the fix belongs in the KIT "
                       "and arrives via a kit update.")
    sys.exit(0)


# -- the early-warning path ---------------------------------------------------

def handle_post_tool_use(data):
    tool = data.get("tool_name")
    root = _kernel.find_repo_root(data.get("cwd"))
    changed = []
    if tool in FILE_TOOLS:
        for path in _compat.file_paths(data):
            found = _is_ledger(path, root)
            if found:
                changed.append(found[1])
    elif tool in SHELL_TOOLS:
        if not os.path.isdir(os.path.join(root, LEDGER_DIR)):
            sys.exit(0)
        state = _read_state(root)
        for absolute in _ledger_csvs_in(root):
            rel = os.path.relpath(absolute, root).replace("\\", "/")
            if _stamp(absolute) != (state.get(rel) or {}).get("stamp"):
                changed.append(absolute)
    if not changed:
        sys.exit(0)

    # EVERY changed file, then ONE report. Reporting inside the loop exited on the first finding,
    # so a patch touching two ledgers left the second unexamined -- and `_compat.file_paths` exists
    # precisely because a multi-file patch must not slip past a single-path check.
    verdicts = {}
    for absolute in changed:
        rel = os.path.relpath(absolute, root).replace("\\", "/")
        findings = _validate(root, absolute)
        _remember(root, rel, findings, _stamp(absolute))
        if findings:
            verdicts[rel] = findings
    if not verdicts:
        sys.exit(0)
    detail = []
    for rel in sorted(verdicts):
        detail.append("  %s:" % rel)
        detail.extend("    - " + f for f in verdicts[rel][:8])
    _kernel.record_note(HOOK, "invalid after a write: %s" % ", ".join(sorted(verdicts)))
    _compat.stop(
        "[team-kit %s] the ledger is INVALID after that write. No rollback was performed; the file "
        "stands as written (spec II.9). Commit, push, merge, reports and specialist dispatch will "
        "be refused until it validates — each of those re-checks the file itself, so there is "
        "nothing to clear once you have fixed it.\n%s\n"
        "Remedy: correct the rows, or `git restore` the file — as its own call; committing in the "
        "same command is refused. `python %s --validate <file>` shows the detail." % (HOOK, "\n".join(detail[:30]), VALIDATOR),
        event="PostToolUse")


HANDLERS = {"PreToolUse": handle_pre_tool_use, "PostToolUse": handle_post_tool_use}


def main():
    data = _kernel.payload(HOOK)
    event = str(data.get("hook_event_name") or "")
    handler = HANDLERS.get(event)
    if handler is None:
        sys.exit(0)
    with _kernel.fail_closed(HOOK, event):
        handler(data)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
