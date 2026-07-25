#!/usr/bin/env python3
"""
Push-token gate — parity risk R1 (row 29, a MINIMUM-KEEP rule).

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
import time  # noqa: E402

import _compat  # noqa: E402

HOOK = "gate_push_token"
SHELL_TOOLS = ("Bash", "PowerShell")
# `git push` in a command position, with git's global options consumed. Deliberately NOT
# `wants_push_or_merge`, which also matches merge: a merge is local and R1 is about publishing.
_PUSH_RX = re.compile(
    r"\bgit(?:\.exe)?\b(?:\s+(?:-c\s+\S+|--\S+(?:=\S+)?|-[a-zA-Z]\s*\S*))*\s+push\b",
    re.IGNORECASE)
# flags that take a value, so the following token is not a remote
_VALUE_FLAGS = ("--repo", "--exec", "--receive-pack", "-o", "--push-option",
                "--force-with-lease", "--recurse-submodules", "--signed")
_DRY_RUN_RX = re.compile(r"(?:^|\s)(?:--dry-run|-n)(?:\s|$)")


def _git(root, *args):
    try:
        result = _compat.run_captured(["git", "-C", root] + list(args), timeout=15)
    except Exception:  # noqa: BLE001 — no git, no worktree, no answer
        return None
    if result.returncode != 0:
        return None
    return (result.stdout or "").strip()


def _push_arguments(command):
    """The tokens after `git push`, with git's own global options removed."""
    match = _PUSH_RX.search(command)
    if not match:
        return []
    rest = command[match.end():]
    # stop at the first shell separator: `git push && echo done` pushes nothing after `&&`
    rest = re.split(r"[;&|]|\n", rest, 1)[0]
    tokens, skip = [], False
    for token in rest.split():
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


def _resolve(root, command):
    """(remote, branch, head) or (None, reason) when it cannot be pinned down."""
    head = _git(root, "rev-parse", "HEAD")
    if not head:
        return None, "this is not a git worktree, or it has no commit yet"
    current = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    tokens = _push_arguments(command)

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
    if refspec.startswith("+"):
        return None, "a `+refspec` is a force-push, which the constitution forbids outright"
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

    The APR file carries only the hash; coverage is read from the consumed REQUEST, which is where
    the manifest lives and which `revoke` MOVES out of the way. So a hand-written APR proves
    nothing, and a revoked one stops matching even though its file still exists.
    """
    approvals = _kernel.kernel_module("approvals", root)
    subject_manifest_hash = _kernel.kernel_module("hashing", root).subject_manifest_hash

    wanted_hash = subject_manifest_hash(dict(wanted))
    approvals_dir = os.path.join(state.root, "approvals")
    if not os.path.isdir(approvals_dir):
        return None
    for name in sorted(os.listdir(approvals_dir)):
        if not (name.startswith("APR-") and name.endswith(".yaml")):
            continue
        try:
            apr = state._read_yaml(os.path.join(approvals_dir, name))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(apr, dict) or apr.get("kind") != "push" or apr.get("revoked"):
            continue
        try:
            request = approvals.consumed_request(state, apr)
        except Exception:  # noqa: BLE001 — a revoked/absent request is simply not a match
            continue
        manifest = dict(request.get("subject_manifest") or {})
        expires = manifest.pop("expires", None)
        if subject_manifest_hash(manifest) != wanted_hash:
            continue
        if expires is not None and float(expires) <= time.time():
            continue
        return apr
    return None


def main():
    data = _kernel.payload(HOOK)
    if str(data.get("hook_event_name") or "") != "PreToolUse":
        sys.exit(0)
    if data.get("tool_name") not in SHELL_TOOLS:
        sys.exit(0)
    raw = str((data.get("tool_input") or {}).get("command") or "")
    if not (_PUSH_RX.search(raw) or _PUSH_RX.search(_compat.git_invocation_text(raw))):
        sys.exit(0)
    if _DRY_RUN_RX.search(raw):
        sys.exit(0)          # `--dry-run` publishes nothing; refusing it blocks the safe rehearsal

    root = _kernel.find_repo_root(data.get("cwd"))
    if not os.path.isdir(_kernel.state_dir(root)):
        sys.exit(0)          # no kernel state in this project: nothing to approve against
    # THROUGH THE BRIDGE. A bare `from kernel...` fails here: `import_kernel` puts the kernel on
    # `sys.path` only for the duration of the import and pops it again in a `finally`, precisely
    # so a project directory cannot shadow it later. The crash was caught fail-closed (exit 2),
    # which is the bridge working -- but a gate that always crashes blocks every push.
    state = _kernel.open_state(root)

    resolved, reason = _resolve(root, raw)
    if resolved is None:
        _kernel.block(
            HOOK,
            "this push cannot be pinned to one remote, branch and commit, so no approval could "
            "name what it releases: %s." % reason,
            remedy="run `git push <remote> <branch>` from the branch you mean, then request the "
                   "push approval for exactly that.")
    remote, branch, head = resolved
    wanted = {"remote": remote, "branch": branch, "head": head}
    if _live_push_approval(root, state, wanted) is None:
        _kernel.block(
            HOOK,
            "no live user approval for pushing %s to %s/%s (spec parity row 29 — a MINIMUM-KEEP "
            "rule: nothing is published without the user saying so). An approval for an earlier "
            "commit does not carry over: the token is bound to the exact HEAD, which is what "
            "makes it single-use." % (head[:8], remote, branch),
            remedy="ask the user with the approval flow (`harness approve push --remote %s "
                   "--branch %s`), relay the question verbatim, and push once they have chosen "
                   "the Freigeben option. Do not hand-write an approval file — only the "
                   "PostToolUse hook can mint one." % (remote, branch))
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
