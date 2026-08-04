#!/usr/bin/env python3
"""
The archive, read the same way by the gate that fills it and the guard that keeps it.

WHY ONE MODULE AND NOT TWO COPIES. `gate_filing` decides whether something may land IN `archive/`;
`guard_fs_tripwire` decides whether something may leave it. Both questions are the same two steps —
read what a shell command NAMES, then RESOLVE those names to a position inside the repo — and only
the first step was ever shared. The second was not, and the guard did not take it at all: it
compared the source TOKEN against the string `archive/`. Measured 2026-08-03 against the V2 hooks:

    mv archive/1-Finanzen/2026/x.pdf archive/1-Finanzen/2026/ok/    exit 2   (INSIDE the archive)
    cd archive/1-Finanzen/2026 && mv x.pdf ../../../outbox/         exit 0   (OUT of the archive)

Those two command lines are the ones `test_fs_tripwire_allows_a_move_that_stays_inside_the_archive`
and `test_fs_tripwire_blocks_a_move_out_of_the_archive_spelled_from_inside_it` run, so the numbers
above are re-measurable rather than remembered.

Both readings are wrong and they are wrong in opposite directions, which is why the audited project
wrote the second spelling into an APPROVED procedure: it was the shape that got work done. The
mechanism is not `cd`. It is "decide on the token instead of on the resolved path", and every
spelling that keeps the word `archive` out of the source token — a relative path after a `cd`, a
variable, `pushd`, a glob — reaches the same result. So the fix is the resolution, not a pattern.

NO `_kernel` HERE, deliberately. `guard_fs_tripwire` answers on every Bash and PowerShell call, and
importing the bridge arms an excepthook that turns any escaping error into exit 2. That is correct
for a fail-closed V2 gate and it is NOT that guard's contract (its own docstring: uncertainty ->
allow), so this module is stdlib plus `_compat` — the single home for lifting wrapper payloads,
which both readers need for the same reason every git gate does.

WHAT NO READER HERE CAN SEE, said once for both callers rather than twice in their docstrings:
a path a PROGRAM builds at run time (`python -c "shutil.move(...)"`), and a token whose text is not
the path the shell will use — a variable, a glob, `~`, a delayed expansion. The second case has one
answer in both places it can occur: as a path token it simply resolves to a position no rule and no
tray matches, and as the argument of a directory change it puts the working directory back to the
bases the readers started with (`reading_bases`), i.e. to what they knew before any `cd` was read
at all. Neither is a refusal; a guess about an unresolvable name would be.
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _compat  # noqa: E402

ARCHIVE = "archive"

# One invocation: everything up to the next command separator. Splitting first is what lets the
# destination — and the working directory a preceding `cd` left behind — be read per command
# instead of per line.
INVOCATION_RX = re.compile(r"[^\n;|&]+")
# Tokens, with quoted spans kept whole. Plain `.split()` was the first version and it fails on the
# ONE filename shape a business archive is full of: `mv inbox/a.pdf "archive/2026/Müller GmbH.pdf"`
# would have ended in the token `GmbH.pdf"`, which is not under archive/ — a silent pass.
TOKEN_RX = re.compile(r'"[^"]*"|\'[^\']*\'|\S+')
# A redirection target IS the file the shell creates, whatever produced the bytes — so this is a
# rule about syntax, not about a command's meaning, and it catches the forms no verb list can
# (`cat inbox/a.pdf > archive/…`).
REDIRECT_RX = re.compile(r'(?:>>?\s*|\btee\b(?:\s+-\S+)*\s+)("[^"]*"|\'[^\']*\'|[^\s;|&<>]+)')
# Copy/move commands, grouped by WHERE their calling convention puts the destination. `robocopy`
# and `xcopy` take two directories and the destination is the SECOND token; the POSIX/PowerShell
# family takes N sources and one destination, so it is the LAST. `install` is a copy that does not
# read like one, and `rsync` is a sync tool rather than a copy verb — both obey the trailing-
# destination convention, and an archive filled by `rsync -a inbox/ archive/2026/` is filed just
# as much as one filled by `mv`.
#
# The trailing-destination family is split by what happens to the SOURCE, because one caller needs
# that distinction and the other does not: filing INTO the archive is the same event however the
# bytes got there (`gate_filing` reads every family), while taking a document OUT of the archive is
# about the original CEASING to be there (`guard_fs_tripwire` reads the relocating half only, which
# is the set its string rule matched before this module existed).
RELOCATING = ("mv", "move", "move-item", "mi", "ren", "rename", "rename-item")
DUPLICATING = ("cp", "copy", "copy-item", "install", "rsync")
DEST_IS_LAST = RELOCATING + DUPLICATING
DEST_IS_SECOND = ("robocopy", "xcopy")
# The commands for which `-t` means "target directory". Scoped, NOT global: it is coreutils'
# spelling, and the same letter means something else next door — `rsync -t` preserves timestamps,
# so reading it as a destination would aim the reader at a source and let the real target through.
GNU_TARGET_DIR = ("mv", "cp", "install")
TARGET_DIR_OPTION = "target-directory"
# The commands that move the WORKING DIRECTORY. This is a set of shell BUILTINS fixed by two
# specifications — POSIX's `cd`, and PowerShell's Set-Location/Push-Location with the aliases it
# ships (`cd`, `chdir`, `sl`, `pushd`) — not a sample taken from an open world of programs, which
# is why it is written down while the copy/move verbs above are read by calling convention. A
# builtin that RETURNS somewhere (`popd`, `Pop-Location`) names no target, and the rule below
# treats "no resolvable target" as "back to the bases we started from" — so it needs no branch.
CHDIR = ("cd", "chdir", "sl", "set-location", "pushd", "push-location", "popd", "pop-location")
# A token the SHELL rewrites before the command sees it: a POSIX or PowerShell variable, a cmd
# `%VAR%` or delayed `!VAR!`, a home reference, a glob. Its literal text is not the path that will
# be used, so resolving it would be inventing a position.
EXPANSION_RX = re.compile(r"[$`*?\[~]|%[^%\s]+%|![A-Za-z_][A-Za-z0-9_]*!")

# One relocation or copy performed by one invocation. `bases` is the working directory that
# invocation runs in, as far as this module could follow it — see `_bases_after`.
Move = collections.namedtuple(
    "Move", "family sources destination destination_is_directory bases")


# ---------------------------------------------------------------- positions inside the repo
def reading_bases(root, cwd):
    """The directories a RELATIVE token may be meant against.

    An agent whose cwd is `inbox/` writes `../archive/…`, which against the repo root looks like an
    escape and against the real cwd is a filing. `_compat` learned this the hard way for Codex
    patch paths ("cwd in a subdir made a repo-root-looking patch path miss every prefix check")
    and resolves against both; the readers here do the same.
    """
    found = [root]
    if cwd and os.path.abspath(cwd) != os.path.abspath(root):
        found.append(cwd)
    return found


def resolve(root, base, token):
    """(repo-relative path, does the token NAME a directory) for one path token.

    `(None, False)` when the token does not land inside `root` at all — a different drive, or a
    climb above the repo. A trailing separator, or an existing directory, means the token IS the
    directory (`mv x.pdf archive/finance/2026/`); otherwise it names a file.
    """
    raw = str(token or "").replace("\\", "/")
    if not raw:
        return None, False
    try:
        absolute = os.path.join(base, raw)
        is_directory = raw.endswith("/") or os.path.isdir(absolute)
        relative = os.path.relpath(absolute, root).replace("\\", "/")
    except (OSError, ValueError):   # embedded NUL, different drive on Windows, …
        return None, False
    if relative == ".." or relative.startswith("../"):
        return None, False
    return relative.rstrip("/"), is_directory


def under(relative, directory):
    """Is this repo-relative path the given top-level directory, or inside it?"""
    return bool(relative) and (relative == directory
                               or relative.startswith(directory.rstrip("/") + "/"))


def position(root, base, token):
    """The repo-relative path a token names, or None if it is not inside the repo."""
    return resolve(root, base, token)[0]


def archive_directory(root, base, token):
    """The repo-relative archive DIRECTORY a filing target lands in, or None if it is not one."""
    relative, is_directory = resolve(root, base, token)
    if relative is None:
        return None
    directory = relative if is_directory else os.path.dirname(relative)
    return directory if under(directory, ARCHIVE) else None


# ---------------------------------------------------------------- reading a shell command
def command_name(token):
    return os.path.basename(str(token).replace("\\", "/")).lower()


def is_destination_flag(token):
    """Is this token PowerShell's `-Destination` parameter?

    PowerShell resolves any UNAMBIGUOUS PREFIX of a parameter name, so `-Destination`, `-Dest` and
    `-Des` are one and the same parameter — encoding the rule beats spelling three of them out.
    Three characters is where the prefix stops colliding with the common `-Debug`.
    """
    name = token.lstrip("-").split(":", 1)[0].split("=", 1)[0].lower()
    return len(name) >= 3 and "destination".startswith(name)


def target_directory_value(token, following):
    """The directory a GNU `-t` / `--target-directory` token names, or None.

    Long form: getopt_long resolves any unambiguous PREFIX of an option name, and the value is
    either glued on with `=` or the next token. Short form: an option that TAKES an argument can
    only be the last letter of a cluster (`mv -fvt archive/2026`), and its value is either glued
    to it (`-tarchive/2026`) or, again, the next token. Both are the calling convention, not a
    list of spellings — which is why `--target-dir=` and `-vt` are covered without being named.
    """
    if token.startswith("--"):
        name, _, attached = token[2:].partition("=")
        if len(name) < 3 or not TARGET_DIR_OPTION.startswith(name.lower()):
            return None
        return (attached or following or "").strip("\"'") or None
    cluster = token[1:]
    place = cluster.find("t")  # case-sensitive: `-T` is --no-target-directory, the opposite
    if place < 0:
        return None
    return (cluster[place + 1:] or following or "").strip("\"'") or None


def named_destination(tokens, gnu_target_dir=False):
    """(value, is_directory) for a destination NAMED by a flag in `tokens`, else (None, False).

    Reading the destination positionally is a Windows-first harness betting on POSIX habits:
    `Move-Item -Destination archive\\x.pdf -Path inbox\\a.pdf` is ordinary PowerShell, and under
    the last-token rule the destination was simply not the last token — measured as a clean
    bypass of the filing gate. GNU's copy/move family has the same construct in its own spelling,
    with one added fact: `-t`/`--target-directory` names a DIRECTORY, so the token IS the folder
    and not a file inside it. Either way a named parameter says which token it is, so it wins over
    position — the same precedence rule, written once for both conventions.

    `gnu_target_dir` comes from the command family (see `GNU_TARGET_DIR`) instead of being
    assumed, because `-t` only means "target" in coreutils.
    """
    for index, token in enumerate(tokens):
        if not token.startswith("-"):
            continue
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        if is_destination_flag(token):
            attached = re.split(r"[:=]", token, maxsplit=1)
            if len(attached) == 2 and attached[1]:
                return attached[1].strip("\"'"), False
            if following is not None:
                return following.strip("\"'"), False
        elif gnu_target_dir:
            value = target_directory_value(token, following)
            if value:
                return value, True
    return None, False


def _word(text):
    """One raw path token, read as the shell would hand it over — see `_tokens`."""
    return _compat.shell_words(text, lambda masked: [masked])[0]


def _tokens(invocation):
    """The invocation's words, with the shell's QUOTING resolved (`_compat.shell_words`).

    A redirect ends the argument list; leaving it in would make `>` or the log file the "last
    token" and hide the real destination.

    THE MARKS HAVE TO BE GONE BEFORE ANY PATH COMPARISON, and this reader had the same gap the
    shell gate had — measured 2026-08-04 against the running `gate_filing` with a plan that covers
    one rule, all four spellings of the SAME destination:
        mv inbox/a.pdf archive/invented/a.pdf        -> rc 2, "no rule covers archive/invented"
        mv inbox/a.pdf arch'i've/invented/a.pdf      -> rc 0
        mv inbox/a.pdf 'arch'ive/invented/a.pdf      -> rc 0
        mv inbox/a.pdf "arch"ive/invented/a.pdf      -> rc 0
    A splice defeats the tray comparison, and with it the whole Aktenplan check: the destination is
    no longer read as being under `archive/`, so the gate stands down and the filing happens with
    no rule behind it. The same splice in the VERB (`m'v'`) hid the move from `_move` outright.

    WHAT IS STILL OPEN HERE, measured in the same run and named rather than implied: the POSIX
    BACKSLASH spelling (`arch\\ive/invented/a.pdf`). `resolve` reads a backslash as a path
    SEPARATOR, which is what it is in PowerShell, and the readers in this module compare a single
    resolved position rather than every reading a shell could give — `guard_fs_tripwire` asks
    whether a source and a destination are on opposite sides of `archive/`, which is a RELATION and
    not a lookup. `_compat.shell_readings` carries the second reading for whoever closes it.
    """
    return _compat.shell_words(re.split(r"[<>]", invocation)[0], TOKEN_RX.findall)


def _operands(tokens):
    """The tokens of an invocation that could be a PATH — everything that is not itself a flag.

    A flag's VALUE is an operand by this rule (`-Path inbox/a.pdf`), and that is deliberate: the
    readers ask what each operand RESOLVES to, and a value that is not a path resolves to a
    position no rule and no tray matches. The opposite cut — "only tokens no flag introduced" —
    would drop the source of `Move-Item -Path <src> -Destination <dst>` on the floor.
    """
    return [t for t in tokens if not t.startswith("-")]


def _bases_after(tokens, current, initial):
    """The bases in effect AFTER this invocation ran (see CHDIR).

    THE DIRECTORY CHANGE IS ADDED, NEVER SUBSTITUTED, and that is what keeps a MISREAD `cd` from
    being a bypass. The command word is looked for anywhere in the invocation, exactly as the
    copy/move verb is, because a prefix may precede it — `sudo`, `env FOO=1`, and after a payload
    lift the wrapper's own words (`bash -lc  cd … && mv …`). The price of that reach is that a `cd`
    APPEARING as an argument (`echo cd /tmp`) reads as one; keeping the bases we came in with means
    the worst such a misreading can do is add a reading, and every caller here treats "lands in the
    archive under ANY reading" as the answer that counts.
    """
    arguments = _arguments(tokens, CHDIR)
    if arguments is None:
        return current
    argument = next((t for t in arguments if not t.startswith("-")), None)
    if not argument or EXPANSION_RX.search(argument):
        return list(initial)          # `popd`, a bare `cd`, `cd $DIR`: we no longer know where
    raw = argument.replace("\\", "/")
    moved = [os.path.normpath(os.path.join(base, raw)) for base in current]
    return moved + [base for base in initial if base not in moved]


def _move(tokens, bases):
    """The relocation/copy this invocation performs, or None."""
    family = next((command_name(t) for t in tokens
                   if command_name(t) in DEST_IS_SECOND or command_name(t) in DEST_IS_LAST), None)
    if family is None:
        return None
    rest = _arguments(tokens, (family,))
    named, names_a_directory = named_destination(rest, family in GNU_TARGET_DIR)
    operands = _operands(rest)
    if named is not None:
        return Move(family, [t for t in operands if t != named], named, names_a_directory, bases)
    if len(operands) < 2:
        return None       # a single token is a source with no destination: nothing is created
    if family in DEST_IS_SECOND:
        # these copy DIRECTORY to DIRECTORY and the trailing tokens are filename filters
        return Move(family, operands[:1], operands[1], True, bases)
    return Move(family, operands[:-1], operands[-1], False, bases)


def _walk(command, bases):
    """[(invocation text, tokens, bases in effect)] — one entry per invocation, in order.

    A wrapper payload is lifted first, so `bash -lc "mv … archive/…"` is read as the `mv` it is;
    the unwrapping is `_compat`'s, the same one the git gates use. An audit already recorded `-lc`
    walking past every gate that tokenised the outer line.

    This is also the ONE place a working-directory change is applied, which is what makes the
    position of a later token in the same command line readable at all.
    """
    walked = []
    current = list(bases)
    for invocation in INVOCATION_RX.findall(_compat.unwrap_shell_payload(command)):
        tokens = _tokens(invocation)
        walked.append((invocation, tokens, list(current)))
        current = _bases_after(tokens, current, bases)
    return walked


def _arguments(tokens, verbs):
    """The tokens AFTER the first token of this invocation that names one of `verbs`, or None.

    Scanned rather than taken from position 0: a prefix like `sudo` or `env FOO=1` may precede the
    command word.
    """
    for index, token in enumerate(tokens):
        if command_name(token) in verbs:
            return tokens[index + 1:]
    return None


def moves(command, bases):
    """Every relocation/copy the command performs, each with the bases its invocation ran in."""
    found = []
    for _text, tokens, current in _walk(command, bases):
        move = _move(tokens, current)
        if move is not None:
            found.append(move)
    return found


def created(command, bases):
    """[(path token, bases)] — every path the command names as a file it CREATES.

    Two syntactic forms, each read on its own terms: the destination of a copy/move (positional or
    flag-named), and a redirection target — the shell creates that one whatever produced the bytes.
    It does NOT see a write performed INSIDE another program; that residual is named in the module
    docstring and, for the filing gate, in its own.
    """
    out = []
    for invocation, tokens, current in _walk(command, bases):
        move = _move(tokens, current)
        if move is not None and move.destination:
            token = move.destination
            if move.destination_is_directory:
                # the explicit slash tells `archive_directory` the token IS the folder — without it
                # a not-yet-existing `archive/finance/2026` would be read as a FILE and the rule
                # check would run against its parent, a directory nobody is filing into
                token = token.replace("\\", "/").rstrip("/") + "/"
            out.append((token, current))
        for match in REDIRECT_RX.finditer(invocation):
            # through `_word` for the reason `_tokens` states: `cat a.pdf > arch'i've/x.pdf`
            # creates a file in the archive, and the marks have to be gone before it is compared
            out.append((_word(match.group(1)), current))
    return out


def named_by(command, bases, verbs):
    """[(path token, bases)] — every operand of an invocation whose command word is in `verbs`.

    The verbs belong to the CALLER: "which commands destroy a document" is its rule, not this
    module's. What this contributes is the same thing it contributes everywhere else — the tokens
    read with quotes kept whole, and the working directory the invocation actually ran in.
    """
    out = []
    for _text, tokens, current in _walk(command, bases):
        arguments = _arguments(tokens, verbs)
        if arguments is not None:
            out += [(token, current) for token in _operands(arguments)]
    return out
