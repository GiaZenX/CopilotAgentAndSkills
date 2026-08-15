#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell) — push-token gate, parity risk R1 (row 29, a MINIMUM-KEEP rule).

"Push nur nach expliziter Userfreigabe" was prose in three constitutions and nothing else, so it
survived exactly as long as the context window that held it. The disposition's answer: `git push`
requires a token minted through the SAME two-phase approval protocol as an APR, with the same mint
code — Amendment 2026-07-24 records why the option IDENTITY cannot carry it (spike S2b: a clicked
option and typed "Other" text are indistinguishable in the payload), so the entropy lives in the
option LABEL and `gate_approval` mints only on that verbatim string.

WHAT THE TOKEN IS BOUND TO: remote + branch + HEAD (`approvals.push_subject_manifest`). That makes
it single-use without a "used" flag anyone has to keep honest — approve HEAD abc123, push it, and
the next commit moves HEAD so the same approval stops matching. Re-running the identical push is a
git no-op, so allowing it costs nothing. A consumed marker would have been one more piece of
writable state deciding an enforcement question, which is the mistake the office ledger gate spent
four review rounds unlearning.

WHY IT IS A SEPARATE GATE and not an extension of `gate_git`: that hook is V1 — raw
`json.load(sys.stdin)`, V1 `project_memory/*.yaml` — and reads a passing QA report, which is an
independent condition. Both run on PreToolUse and both must pass; folding a kernel-backed check
into a hook that cannot import the kernel would have meant a second, weaker copy of the approval
logic. The disposition says "gate_git-Erweiterung"; this is that extension, in the shape phase 2
uses for every other gate.

FAIL-CLOSED ON AMBIGUITY. If the command's refspec cannot be resolved to "this HEAD, that branch",
the push is refused with an instruction to name remote and branch explicitly, rather than guessed
at. A guess here authorises publishing something the user did not see.

AND A FORCE PUSH IS REFUSED BEFORE ANY OF THAT, on `_compat.names_force_push` — the definition
`gate_git` decides on too, and before this gate's rehearsal and state-directory stand-downs both.
The manifest binds remote, branch and commit; it cannot bind "and the remote history survives", so
no approval this gate reads is able to cover one. `gate_git` is absent from the office kit
(`settings.json` there registers this gate and no `gate_git`), which is why the rule may not live
in that file alone.
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

import _compat  # noqa: E402

HOOK = "gate_push_token"
SHELL_TOOLS = ("Bash", "PowerShell")
# Force-push in every spelling. BOUND, not copied: this is `_compat.names_force_push` itself, the
# same object `gate_git` decides on, named here because a gate should say under its own roof which
# rule it enforces. This file used to know one spelling (`+refspec`, in `_resolve`) while the
# other gate knew all of them -- and the office kit installs this gate and no `gate_git` at all.
names_force_push = _compat.names_force_push
# flags that take a value AS A SEPARATE TOKEN, so the token after them is not a remote. The test
# is that separateness and nothing else: `--force-with-lease` sat here and takes no such value --
# git spells its value with `=` (`--force-with-lease=origin/main`) -- so listing it made
# `_push_arguments` swallow the remote and `_resolve` answer "cannot be pinned down". Measured
# 2026-08-02 with a live approval: `git push --force-with-lease origin main` was refused for the
# wrong reason while `--force-with-lease=origin/main` resolved and was ALLOWED. Both forms are
# now ordinary `-` flags to this reader, and both are refused by the force check in `main`.
_VALUE_FLAGS = ("--repo", "--exec", "--receive-pack", "-o", "--push-option",
                "--recurse-submodules", "--signed")
_REHEARSAL_FLAGS = ("--dry-run", "-n")


def _push_invocations(command):
    """EVERY `git push` this command runs. Deliberately NOT `wants_push_or_merge`, which also
    matches merge: a merge is local and R1 is about publishing.

    Every one of them, because `git push origin main && git push upstream main` publishes twice
    and a token minted for one says nothing about the other — the old reader stopped at the first
    match it found.

    Applicability comes from `_compat.git_invocations` — push has to be the SUBCOMMAND. This gate
    used to spell the invocation itself (`git`, then git's global options, then `push`), and that
    pattern broke on exactly the two shapes the shared reader exists for: `git "push" origin main`
    and `git pu\\<newline>sh origin main` published without any approval, because neither the raw
    text nor the prose-stripped fallback contained the word.

    `runs`, not an equality test, so a verb the shell only assembles at run time (`git $V origin
    main`) needs the approval too. R1 is a MINIMUM-KEEP rule and this is the direction it has to
    fail in: the cost of the over-trigger is one approval on a command no one writes by hand, the
    cost of the under-trigger is publishing without the user.

    CASE IS PRESERVED (`lower=False`): the tokens are read back as a remote and a BRANCH and go
    into the approval manifest, so lowercasing `feat/Login` would bind the token to a branch that
    does not exist. The reader lowercases the subcommand itself, so matching `push` is unaffected.
    """
    return [invocation for invocation in _compat.git_invocations(command, lower=False)
            if invocation.runs("push")]


def _git(root, *args):
    try:
        result = _compat.run_captured(["git", "-C", root] + list(args), timeout=15)
    except Exception:  # noqa: BLE001 — no git, no worktree, no answer
        return None
    if result.returncode != 0:
        return None
    return (result.stdout or "").strip()


def _is_rehearsal(invocation):
    """True when THIS push is a `--dry-run` — read as a TOKEN, never as text.

    `--dry-run` publishes nothing, so refusing it would block the safe rehearsal. But the release
    it excuses is the one thing this gate exists to hold (parity row 29, MINIMUM-KEEP), so the
    question has to be answered on the part that RUNS. It was answered on a substring instead —
    the tokens were joined back into a line and searched — and a push option is an arbitrary
    string the caller chooses: `git push -o "--dry-run" origin main`,
    `git push origin main --push-option="x --dry-run y"` and `git push origin main -o "release -n
    now"` are all real pushes that measured rc 0, i.e. published with no approval at all.

    So the flag counts only as a flag: a token that IS `--dry-run`/`-n`, and not one that is the
    VALUE of a preceding option. Same `_VALUE_FLAGS` skip `_push_arguments` uses, because "which
    tokens did this push really give git" is one question and must not have two answers.
    """
    skip = False
    for token in invocation.arguments:
        if skip:
            skip = False
        elif token in _VALUE_FLAGS:
            skip = True
        elif token in _REHEARSAL_FLAGS:
            return True
    return False


def _push_arguments(invocation):
    """The POSITIONAL tokens of a `git push` — remote and refspec — with the flags that take a
    value removed. The invocation's arguments already stop at the first shell separator
    (`git push && echo done` pushes nothing after `&&`)."""
    tokens, skip = [], False
    for token in invocation.arguments:
        if skip:
            skip = False
            continue
        if token in _VALUE_FLAGS:
            skip = True
            continue
        if token.startswith("-"):
            continue
        tokens.append(token.strip("\"'"))
    return tokens


def _resolve(root, invocation):
    """(remote, branch, head) or (None, reason) when it cannot be pinned down."""
    head = _git(root, "rev-parse", "HEAD")
    if not head:
        return None, "this is not a git worktree, or it has no commit yet"
    current = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    tokens = _push_arguments(invocation)

    if not tokens:                                   # bare `git push`
        upstream = _git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        if not upstream or "/" not in upstream:
            return None, ("`git push` with no arguments and no configured upstream — name the "
                          "remote and branch so the approval can say what is being published")
        remote, branch = upstream.split("/", 1)
        return (remote, branch, head), None

    remote = tokens[0]
    if len(tokens) == 1:
        if not current or current == "HEAD":
            return None, "the worktree is in detached HEAD, so there is no branch to approve"
        return (remote, current, head), None

    refspec = tokens[1]
    if len(tokens) > 2:
        return None, ("more than one refspec in a single push — approve and run them one at a "
                      "time, so each approval names exactly what it releases")
    # No `+refspec` branch here any more. It used to be this function's own account of one force
    # spelling, and being one spelling is what let `--force` and `-f` past: `main` now asks
    # `_compat.names_force_push`, which covers `+refspec` too, and it asks BEFORE resolving. A
    # second copy here would be a second definition of the same rule with nothing keeping them
    # equal, which is how the two answers differed in the first place.
    if ":" in refspec:
        source, target = refspec.split(":", 1)
        resolved = _git(root, "rev-parse", source) if source else None
        if resolved != head:
            return None, ("the refspec pushes %r, which is not this worktree's HEAD — approve the "
                          "exact commit by checking it out first" % source)
        return (remote, target.replace("refs/heads/", ""), head), None
    return (remote, refspec, head), None


def _live_push_approval(root, state, wanted):
    """A minted, unrevoked, unexpired `push` approval whose REQUEST matches `wanted`.

    ASKED OF THE KERNEL (`approvals.live_line_approval`), which is where the rule now lives with
    its reasons: the APR file carries only the hash, so coverage is read from the consumed REQUEST
    — the tamper-evident side, and the one `revoke` MOVES out of the way. This gate carried that
    scan itself until a second line-manifest kind (`preset`) needed the same answer; two copies of
    "is this authorisation in force" is the shape that decides whether a lapsed permission still
    works, so there is one.
    """
    return _kernel.kernel_module("approvals", root).live_line_approval(state, "push", dict(wanted))


def main():
    data = _kernel.payload(HOOK)
    if str(data.get("hook_event_name") or "") != "PreToolUse":
        sys.exit(0)
    if data.get("tool_name") not in SHELL_TOOLS:
        sys.exit(0)
    raw = str((data.get("tool_input") or {}).get("command") or "")
    invocations = _push_invocations(raw)
    if not invocations:
        sys.exit(0)

    # A FORCE PUSH IS NOT A PUSH THIS GATE CAN LET AN APPROVAL COVER. The token is bound to
    # remote + branch + HEAD (`approvals.push_subject_manifest`), and that manifest says nothing
    # about whether the remote history survives — so a live approval for `origin/main @ abc123`
    # was answered rc 0 for `git push --force origin main`, which publishes the same commit AND
    # discards what other clones already have. Measured 2026-08-02 through the real hook process
    # with a minted token: `--force` and `-f` rc 0, `--force-with-lease=origin/main` rc 0, quoted
    # `"--force"` rc 0, and `--force-with-lease` rc 2 only because the flag list mis-swallowed the
    # remote.
    #
    # UNCONDITIONAL, so it stands before BOTH stand-downs this function has, and each was measured
    # rather than reasoned about. The rehearsal filter below excuses a `--dry-run` because it
    # publishes nothing — but `gate_git` refuses a rehearsed force push, and letting this gate
    # answer differently would put the same incoherence back one spelling further out, in the kit
    # where `gate_git` is not installed. The state-directory stand-down means "no state, nothing to
    # approve against", and a force push is refused with no approval in the question at all.
    #
    # ASKED OF `_compat.names_force_push`, which is also what `gate_git` decides on. Two gates
    # answering "is this a force push" from two places is the defect this replaced: this file knew
    # `+refspec` and nothing else, `gate_git` knew all of them, and `gate_git` does not ship to the
    # office kit at all.
    if names_force_push(raw):
        _kernel.block(
            HOOK,
            "force-push is refused: it rewrites history other clones already have, and a push "
            "approval cannot cover it — the token is bound to remote, branch and commit "
            "(`approvals.push_subject_manifest`) and says nothing about discarding what the "
            "remote already holds.",
            remedy="push without rewriting the remote's history — that is what `--force`, `-f`, "
                   "`--force-with-lease` and a `+refspec` all ask for. If history really has to be "
                   "rewritten, that is a user decision, not a task decision: report it and let "
                   "them run it themselves.")

    # Read off EACH push's own arguments, as TOKENS — see `_is_rehearsal`. `-n` is an ordinary flag
    # of other git commands (`git commit -n`), so a line-wide search let one of those release a
    # real push, and a search over the joined tokens let a push OPTION do the same.
    pushes = [invocation for invocation in invocations if not _is_rehearsal(invocation)]
    if not pushes:
        sys.exit(0)

    root = _kernel.find_repo_root(data.get("cwd"))
    if not os.path.isdir(_kernel.state_dir(root)):
        sys.exit(0)          # no kernel state in this project: nothing to approve against
    # THROUGH THE BRIDGE. A bare `from kernel...` fails here: `import_kernel` puts the kernel on
    # `sys.path` only for the duration of the import and pops it again in a `finally`, precisely
    # so a project directory cannot shadow it later. The crash was caught fail-closed (exit 2),
    # which is the bridge working -- but a gate that always crashes blocks every push.
    state = _kernel.open_state(root)

    for invocation in pushes:
        resolved, reason = _resolve(root, invocation)
        if resolved is None:
            _kernel.block(
                HOOK,
                "this push cannot be pinned to one remote, branch and commit, so no approval "
                "could name what it releases: %s." % reason,
                remedy="run `git push <remote> <branch>` from the branch you mean, then request "
                       "the push approval for exactly that.")
        remote, branch, head = resolved
        wanted = {"remote": remote, "branch": branch, "head": head}
        if _live_push_approval(root, state, wanted) is None:
            _kernel.block(
                HOOK,
                "no live user approval for pushing %s to %s/%s (spec parity row 29 — a "
                "MINIMUM-KEEP rule: nothing is published without the user saying so). An approval "
                "for an earlier commit does not carry over: the token is bound to the exact HEAD, "
                "which is what makes it single-use." % (head[:8], remote, branch),
                remedy="run `python scripts/harness.py request-approval push --remote %s --branch "
                       "%s` from the project root (HEAD is read from the worktree; pass `--head` "
                       "only to name a different commit), relay the printed question to the user "
                       "VERBATIM with AskUserQuestion, and push once they have chosen the "
                       "Freigeben option — answering it is what mints the token, and the mint "
                       "runs in the PostToolUse hook. Do not hand-write an approval file: it "
                       "would have no consumed request behind it and this gate reads that, not "
                       "the file." % (remote, branch))
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
