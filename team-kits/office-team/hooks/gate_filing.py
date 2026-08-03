#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell|Edit|Write|MultiEdit) — nothing lands in archive/ that the filing
plan does not have a rule for.

WHAT CHANGED AND WHY. V1 checked filing_log.yaml: after the clerk wrote a `filed:` entry, the gate
asked whether the target existed. Two things ended that. `filing_log.yaml` is now a REGENERATED
scan index (spec II.9) — nobody maintains it, so there is no claim in it left to verify — and the
derivation direction was turned around: `filing_plan.yaml` is the single machine-readable truth,
the prose Ablage guideline is generated from it, not the other way round.

So the gate verifies the same thing one step earlier and against the real truth: the DESTINATION.
A document whose target matches no rule in the plan is not filed at all — spec II.9 is explicit
that it must not be moved, not renamed and not entered anywhere; the clerk asks the user with a
concrete rule proposal instead. Checking before the move is strictly stronger than checking a log
afterwards, because a wrong filing never happens rather than being reported.

WHAT THE GATE SEES, EXACTLY. One predicate ("does this destination match a rule?") behind two
readers. The tool-write reader is complete: every path an Edit/Write/MultiEdit or a Codex patch
creates goes through `_compat.file_paths`. The shell reader is not, and saying otherwise would be
the comment this repo bans. It reads the three syntactic forms in which a shell command NAMES the
file it creates — a redirection target, a flag that names the destination, and a positional
destination at the place that command's calling convention puts it (see `move_destinations`).
Wrapper payloads (`bash -lc "mv …"`) are unwrapped first through `_compat.unwrap_shell_payload`,
the same single home the git gates use: a wrapped `mv` is not a different risk, it is the same
`mv` one level down, and an audit already recorded `-lc` walking past every gate that tokenised
the outer line. It does NOT see a write performed INSIDE another program: `python -c
"shutil.copy(...)"`, `tar -x -C archive/…`, a script that files by itself. Those are the named
residual risk; they are covered by `gate_write_scope` (a shell command may not smuggle
enforcement-relevant writes) and by the fact that filing is a clerk workflow, not a scripted one.
If a project starts filing from a script, the script — not this regex — is where the rule belongs.

`guard_fs_tripwire` owns the other direction — deletes under inbox/ or archive/, and moves OUT of
archive/ — and deliberately leaves filing INTO the archive open; this gate is what makes that
opening safe.

FAIL-CLOSED, including on an empty plan: with no readable rule there is no truth to file against,
and "no plan yet" is precisely when a mis-filing is cheapest to make and dearest to undo.

WHERE THE PLAN COMES FROM, since the shipped template carries `rules: []` and this gate fails
closed on that — a fresh office project blocks on its FIRST filing. The plan is a kit DOCUMENT
(`kernel.layout.is_project_document`, like `project_config.yaml` and `product/masterplan.md`), not
canonical item state: no kernel path builder can name it, so no kernel command writes it, and
`gate_write_scope` refuses every tool write to it and says exactly that. That leaves ONE session in
a project's life in which it can be written — the global entry gate's, which runs before the kit is
installed; `user/claude/CLAUDE.md` and `user/codex/AGENTS.md` are told to fill it there from the
confirmed onboarding answers, and `tools/test_hooks.py` DERIVES that obligation from this gate
rather than from a list, so a document a gate blocks on can no longer be left out of them.

WHAT THAT DOES NOT FIX, named rather than left to be re-diagnosed as "gate too strict": a project
that was already installed with an empty plan. Nothing inside a session repairs it — the refusal
below is honest about that and points at the user, not at a command. The block itself is correct in
both cases; an unverifiable filing in a business archive is what this gate exists for.
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

import _compat  # noqa: E402

HOOK = "gate_filing"
ARCHIVE = "archive"
PLAN = "filing_plan.yaml"
# One invocation: everything up to the next command separator. Splitting first is what lets the
# destination be read per command instead of per line.
INVOCATION_RX = re.compile(r"[^\n;|&]+")
# Tokens, with quoted spans kept whole. Plain `.split()` was the first version and it fails on the
# ONE filename shape a business archive is full of: `mv inbox/a.pdf "archive/2026/Müller GmbH.pdf"`
# would have ended in the token `GmbH.pdf"`, which is not under archive/ — a silent pass.
TOKEN_RX = re.compile(r'"[^"]*"|\'[^\']*\'|\S+')
# A redirection target IS the file the shell creates, whatever produced the bytes — so this is a
# rule about syntax, not about a command's meaning, and it catches the forms no verb list can
# (`cat inbox/a.pdf > archive/…`). `guard_fs_tripwire` guards the ledger with the same rule.
REDIRECT_RX = re.compile(r'(?:>>?\s*|\btee\b(?:\s+-\S+)*\s+)("[^"]*"|\'[^\']*\'|[^\s;|&<>]+)')
# Copy/move commands, grouped by WHERE their calling convention puts the destination. `robocopy`
# and `xcopy` take two directories and the destination is the SECOND token; the POSIX/PowerShell
# family takes N sources and one destination, so it is the LAST. `install` is a copy that does not
# read like one, and `rsync` is a sync tool rather than a copy verb — both obey the trailing-
# destination convention, and an archive filled by `rsync -a inbox/ archive/2026/` is filed just
# as much as one filled by `mv`.
DEST_IS_SECOND = ("robocopy", "xcopy")
DEST_IS_LAST = ("mv", "move", "move-item", "mi", "ren", "rename", "rename-item",
                "cp", "copy", "copy-item", "install", "rsync")
# The commands for which `-t` means "target directory". Scoped, NOT global: it is coreutils'
# spelling, and the same letter means something else next door — `rsync -t` preserves timestamps,
# so reading it as a destination would aim the gate at a source and let the real target through.
GNU_TARGET_DIR = ("mv", "cp", "install")
TARGET_DIR_OPTION = "target-directory"
PLACEHOLDER_SEGMENT_RX = re.compile(r"^<[^<>/]+>$")


def rules(root):
    """The filing plan's rules, or a reason string why there are none to file against."""
    path = os.path.join(_kernel.state_dir(root), PLAN)
    if not os.path.isfile(path):
        return None, "%s does not exist" % PLAN
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return None, "PyYAML is not installed for the interpreter running the hooks"
    try:
        with open(path, encoding="utf-8-sig") as fh:
            plan = yaml.safe_load(fh) or {}
    except Exception as exc:  # noqa: BLE001
        return None, "%s could not be parsed (%s)" % (PLAN, exc)
    found = [r for r in (plan.get("rules") or []) if isinstance(r, dict) and r.get("path_template")]
    if not found:
        return None, "%s lists no rules yet" % PLAN
    return found, None


def rule_matches(path_template, directory):
    """Does `directory` (repo-relative, slash-separated, no trailing slash) match this rule?

    `<name>` in a path_template stands for exactly one segment — a year, a counterparty folder.
    Everything else is literal, so `archive/finance/2026` never matches `archive/finance`.
    """
    parts = [p for p in str(path_template).replace("\\", "/").strip().strip("/").split("/") if p]
    if not parts:
        return False
    pattern = "/".join("[^/]+" if PLACEHOLDER_SEGMENT_RX.match(p) else re.escape(p) for p in parts)
    return re.match("^" + pattern + "$", directory) is not None


def archive_directory(root, base, target):
    """The repo-relative archive directory a filing target lands in, or None if it is not one.

    `base` is what a RELATIVE target is resolved against. It matters: an agent whose cwd is
    `inbox/` writes `../archive/…`, which against the repo root looks like an escape and against
    the real cwd is a filing. `_compat` learned this the hard way for Codex patch paths ("cwd in a
    subdir made a repo-root-looking patch path miss every prefix check") and resolves against both;
    `check` does the same here. Both readings blocking is the fail-closed direction — an over-block
    asks the clerk to name the rule, a missed reading files the document nowhere anyone can find.

    A trailing separator, or an existing directory, means the token IS the directory (`mv x.pdf
    archive/finance/2026/`); otherwise it names the file and the directory is its parent.
    """
    if not target:
        return None
    raw = target.replace("\\", "/")
    is_dir = raw.endswith("/") or os.path.isdir(os.path.join(base, raw))
    try:
        rel = os.path.relpath(os.path.join(base, raw), root).replace("\\", "/")
    except ValueError:  # different drive on Windows: not a path inside this repo
        return None
    if rel.startswith("../") or rel == "..":
        return None
    directory = rel.rstrip("/") if is_dir else os.path.dirname(rel)
    if directory != ARCHIVE and not directory.startswith(ARCHIVE + "/"):
        return None
    return directory


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
    position = cluster.find("t")  # case-sensitive: `-T` is --no-target-directory, the opposite
    if position < 0:
        return None
    return (cluster[position + 1:] or following or "").strip("\"'") or None


def named_destination(tokens, gnu_target_dir=False):
    """(value, is_directory) for a destination NAMED by a flag in `tokens`, else (None, False).

    Reading the destination positionally is a Windows-first harness betting on POSIX habits:
    `Move-Item -Destination archive\\x.pdf -Path inbox\\a.pdf` is ordinary PowerShell, and under
    the last-token rule the destination was simply not the last token — measured as a clean
    bypass of this gate. GNU's copy/move family has the same construct in its own spelling, with
    one added fact: `-t`/`--target-directory` names a DIRECTORY, so the token IS the folder and
    not a file inside it. Either way a named parameter says which token it is, so it wins over
    position — the same precedence rule, now written once for both conventions.

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


def move_destinations(command):
    """Every path a shell command names as a file it CREATES.

    Three syntactic forms, each read on its own terms — see the module docstring for what this
    deliberately does NOT reach:
      * a redirection target (`> archive/x.pdf`, `tee archive/x.pdf`) — the shell creates it;
      * a flag that NAMES the destination (`-Destination`, `-t`) — position-independent by design;
      * a positional destination, at the place that command's calling convention puts it.

    A wrapper payload is unwrapped first, so `bash -lc "mv … archive/…"` is read as the `mv` it
    is; the unwrapping is `_compat`'s, the same one the git gates use.
    """
    command = _compat.unwrap_shell_payload(command)
    out = []
    for invocation in INVOCATION_RX.findall(command):
        # A redirect ends the argument list; leaving it in would make `>` or the log file the
        # "last token" and hide the real destination.
        tokens = [t.strip("\"'") for t in TOKEN_RX.findall(re.split(r"[<>]", invocation)[0])]
        family, rest = None, []
        for index, token in enumerate(tokens):
            name = os.path.basename(token.replace("\\", "/")).lower()
            if name in DEST_IS_SECOND or name in DEST_IS_LAST:
                family, rest = name, tokens[index + 1:]
                break  # a prefix like `sudo`/`env FOO=1` may precede the command
        if family is None:
            continue
        named, names_a_directory = named_destination(rest, family in GNU_TARGET_DIR)
        if named is not None:
            # the explicit slash tells archive_directory the token IS the folder — without it a
            # not-yet-existing `archive/finance/2026` would be read as a FILE and the rule check
            # would run against its parent, i.e. against a directory nobody is filing into
            out.append(named.replace("\\", "/").rstrip("/") + "/" if names_a_directory else named)
            continue
        positional = [t for t in rest if not t.startswith("-")]
        if len(positional) < 2:
            continue  # a single token is a source with no destination: not a filing
        if family in DEST_IS_SECOND:
            # these copy DIRECTORY to DIRECTORY and the trailing tokens are filename filters; the
            # explicit slash tells archive_directory the token is the folder, not a file in it
            out.append(positional[1].replace("\\", "/").rstrip("/") + "/")
        else:
            out.append(positional[-1])
    for match in REDIRECT_RX.finditer(command):
        out.append(match.group(1).strip("\"'"))
    return out


def check(root, cwd, targets):
    bases = [root]
    if cwd and os.path.abspath(cwd) != os.path.abspath(root):
        bases.append(cwd)
    directories = []
    for target in targets:
        for base in bases:
            directory = archive_directory(root, base, target)
            if directory and directory not in directories:
                directories.append(directory)
    if not directories:
        return  # nothing is landing in the archive

    found, reason = rules(root)
    if found is None:
        _kernel.block(
            HOOK,
            "a document is being filed into %s, but there is no machine-readable filing plan to "
            "file it against: %s. The Aktenplan is the single truth for where a document belongs "
            "(spec II.9); without it a filing cannot be verified, and an unverifiable filing in a "
            "business archive is the failure this gate exists for."
            % ("/, ".join(directories) + "/", reason),
            remedy="propose the missing %s rules to the USER and stop there. The plan is a kit "
                   "document inside the write-locked state directory: no tool write reaches it "
                   "and no kernel command writes it (gate_write_scope refuses it with that "
                   "reason), so it is filled by the entry gate before the kit is installed, or "
                   "by the user in an editor outside this session. Name the rules concretely — "
                   "the fields one carries are stated in the plan's own header — and file "
                   "nothing until the file the user saves has them." % PLAN)
    unmatched = [d for d in directories
                 if not any(rule_matches(r.get("path_template"), d) for r in found)]
    if unmatched:
        _kernel.block(
            HOOK,
            "no rule in %s covers %s. A document that matches no rule is NOT filed: leave it "
            "where it is, do not rename it, do not enter it anywhere."
            % (PLAN, ", ".join(sorted(unmatched))),
            remedy="ask the user with a CONCRETE proposal — either the existing rule this "
                   "document belongs under, or a new rule for it — and file only after the user "
                   "has saved the amended plan themselves; this session cannot write it (see the "
                   "refusal above for why). Inventing a folder is how an Aktenplan stops "
                   "describing the archive.")


def main():
    # No `hook_event_name` guard: this gate is registered on PreToolUse and nowhere else, so
    # the event is settled by settings.json. Re-checking a field a provider may simply omit
    # would turn the gate into a silent exit 0 -- the failure this whole phase is about.
    data = _kernel.payload(HOOK)
    if data.get("tool_name") not in ("Bash", "PowerShell", "Edit", "Write", "MultiEdit"):
        sys.exit(0)
    cwd = str(data.get("cwd") or "")
    root = _kernel.find_repo_root(cwd)
    if data.get("tool_name") in ("Bash", "PowerShell"):
        check(root, cwd,
              move_destinations(str((data.get("tool_input") or {}).get("command") or "")))
    else:
        check(root, cwd, _compat.file_paths(data))
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
