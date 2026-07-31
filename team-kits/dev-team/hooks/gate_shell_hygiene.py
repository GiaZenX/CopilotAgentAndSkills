#!/usr/bin/env python3
"""
PreToolUse(Bash|PowerShell) — shell-hygiene gate, parity risks R10 and R11, promoted from
"optional" to FIRM by the user's "maximal härten" decision of 2026-07-24.

Two rules, one hook, because they share the only thing that matters for cost: they both trigger on
a shell command and would otherwise be two process spawns per Bash call.

R10 — FOREIGN DOCKER PROJECTS ARE OFF-LIMITS (devops SKILL §3). The incident it comes from: an OOM
hunt stopped a NEIGHBOUR project's production database. Compose projects share one daemon, so
`docker stop <name>` reaches anything on the machine, and a model debugging a memory problem has
every reason to look at the biggest container it can see.

R11 — NEVER WORK ON A DIRTY TREE (constitution §8: "offer Commit/Stash/Discard first"). Scoped to
the operations that can LOSE the uncommitted work — merge, rebase, `reset --hard`, a branch
switch, pull. `git checkout -b`, `git stash` and `git add` stay open: those are how the agent gets
the tree clean, and a rule that blocks its own remedy is a deadlock.

BOTH FAIL OPEN WHEN THEY CANNOT SEE. No docker daemon means the destructive command will fail on
its own; no git worktree means there is no uncommitted work to protect. This is deliberate and
different from the ledger gate: there, "cannot tell" hides broken money data, so it refuses. Here,
"cannot tell" means the hazard does not exist in this environment, and refusing would block
ordinary work to protect nothing.
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

HOOK = "gate_shell_hygiene"
SHELL_TOOLS = ("Bash", "PowerShell")


def _shell_view(command):
    """What the SHELL hands the program, for the rules below that still read words out of the
    text (`_compat.git_argument_text` — the name says git, the view is not git-specific).

    Quote marks gone, their content kept, line continuations resolved, wrapper payloads lifted,
    and one line per reading of the escape character, because the same eight hooks gate the
    `PowerShell` tool and PowerShell escapes with a backtick. Case is PRESERVED: a container name
    is case-sensitive and goes straight into `docker inspect`; the patterns below are IGNORECASE
    where they need to be.
    """
    return _compat.git_argument_text(command, lower=False)


# -- R10 ----------------------------------------------------------------------
# Verbs that STOP or DESTROY. `docker ps/logs/inspect/stats/build/run` are absent: reading is how
# you find out what is going on, and a gate that blocks diagnosis gets worked around.
_DOCKER_DESTRUCTIVE_RX = re.compile(
    r"\bdocker(?:\.exe)?\s+(?:compose\s+)?"
    r"(?P<verb>stop|kill|rm|rmi|restart|down|prune|pause)\b", re.IGNORECASE)
# `prune` and a bare `system prune` take everything on the daemon, so there is no target to check:
# by construction they reach other people's projects.
_PRUNE_RX = re.compile(r"\bdocker(?:\.exe)?\s+(?:system|volume|network|image|container)?\s*prune\b",
                       re.IGNORECASE)
_COMPOSE_LABEL = "com.docker.compose.project"

# -- R11 ----------------------------------------------------------------------
# Operations that can lose uncommitted work, as SUBCOMMANDS read by `_compat.git_invocations`.
# This hook kept its own regexes for one round too long and therefore kept both defects the shared
# reader was written to end — measured as real hook processes on a dirty tree: `git reset --hard
# HEAD~1` blocked while `git "reset" --hard HEAD~1`, `git rese''t --hard HEAD~1`,
# `git reset --ha\<newline>rd HEAD~1`, `git "merge" feat/x` and `git "checkout" main` all ran, and
# the last of those was blocked by NO hook in the kit. A pattern is a list of spellings; what an
# operation IS cannot be a question about quoting.
_DIRTY_RISK_SUBCOMMANDS = frozenset(("merge", "rebase", "pull", "cherry-pick", "revert", "am"))
# `checkout -b` / `switch -c` CREATE a branch and carry the changes along, which is safe and
# routine; only a switch to an EXISTING ref is in scope.
_SWITCH_SUBCOMMANDS = frozenset(("checkout", "switch"))
_CREATE_BRANCH_FLAGS = frozenset(("-b", "-B", "-c", "-C"))
# `git checkout -- <path>` and `git checkout <ref> -- <path>` restore FILES; that is a deliberate
# discard, which the constitution names as one of the three offers.
_PATHSPEC = "--"


def _git(root, *args):
    try:
        result = _compat.run_captured(["git", "-C", root] + list(args), timeout=15)
    except Exception:  # noqa: BLE001
        return None
    return (result.stdout or "").strip() if result.returncode == 0 else None


def _docker_targets(view):
    """Names/ids given to a destructive docker verb, minus its flags.

    Read off `_shell_view`, so `docker "stop" db` names the same container the bare spelling does.
    The split on a newline also bounds the answer to ONE reading of the escape character — the
    view holds one reading per line."""
    match = _DOCKER_DESTRUCTIVE_RX.search(view)
    if not match:
        return []
    rest = re.split(r"[;&|]|\n", view[match.end():], maxsplit=1)[0]
    return [token.strip("\"'") for token in rest.split()
            if not token.startswith("-") and token.strip("\"'")]


def _compose_project_of(root, name):
    """The compose project a container/volume belongs to, or None when it cannot be determined."""
    for kind in ("container", "volume"):
        out = _compat.run_captured(
            ["docker", kind, "inspect", "--format",
             "{{ index .Config.Labels \"%s\" }}" % _COMPOSE_LABEL if kind == "container"
             else "{{ index .Labels \"%s\" }}" % _COMPOSE_LABEL, name],
            cwd=root, timeout=20)
        if out.returncode == 0:
            value = (out.stdout or "").strip()
            return value if value and value != "<no value>" else ""
    return None


def _our_compose_projects(root):
    """What this repo's compose project is called. Compose defaults to the DIRECTORY name."""
    names = {os.path.basename(os.path.abspath(root)).lower()}
    # ...and whatever an explicit name says, since a folder rename silently detaches every volume
    for env_file in (".env", os.path.join("docker", ".env")):
        try:
            with open(os.path.join(root, env_file), encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    if line.strip().upper().startswith("COMPOSE_PROJECT_NAME"):
                        names.add(line.split("=", 1)[-1].strip().strip("\"'").lower())
        except OSError:
            continue
    names.discard("")
    return names


def _check_docker(root, view):
    # PRUNE is checked FIRST and independently: `docker system prune` / `docker volume prune` put
    # a subcommand where the destructive-verb pattern expects the verb, so gating the prune check
    # behind that pattern meant the two most dangerous forms — the ones that by construction reach
    # every project on the daemon — were the only ones never examined.
    if _PRUNE_RX.search(view):
        _kernel.block(
            HOOK,
            "`docker prune` removes resources across the WHOLE daemon, so it cannot be scoped to "
            "this project — a real OOM hunt once stopped a neighbour project's production "
            "database this way (devops SKILL §3).",
            remedy="remove this project's own resources by name, or `docker compose down` inside "
                   "the repo. If a machine-wide prune is really what you want, that is the user's "
                   "call to make and to run.")
    if not _DOCKER_DESTRUCTIVE_RX.search(view):
        return          # reading (`ps`, `logs`, `inspect`, `build`, `up`) is never this gate's business
    targets = _docker_targets(view)
    if not targets:
        return          # `docker compose down` with no target: scoped to this directory already
    ours = _our_compose_projects(root)
    for target in targets:
        project = _compose_project_of(root, target)
        if project is None:
            continue    # no daemon, or no such object: the command will fail on its own
        if project.lower() not in ours:
            _kernel.block(
                HOOK,
                "%r belongs to compose project %r, not to this repo (%s). Foreign Docker projects "
                "are off-limits: containers and volumes share one daemon, so this reaches another "
                "project's data — a real OOM hunt stopped a NEIGHBOUR project's production "
                "database exactly here (devops SKILL §3)."
                % (target, project or "<none>", "/".join(sorted(ours))),
                remedy="act on this project's own containers, or ask the user explicitly before "
                       "touching anything else on the daemon.")


def _switches_branch(invocation):
    """A switch to an EXISTING ref — the only checkout/switch shape that can lose work."""
    arguments = invocation.arguments
    if any(token in _CREATE_BRANCH_FLAGS or token == _PATHSPEC for token in arguments):
        return False    # creating a branch carries changes along; `--` restores files on purpose
    return bool(arguments)


def _dirty_risk_verb(command):
    """The name of the operation that can lose uncommitted work, or None.

    One pass over the same invocation reader every other git gate uses, so the three rules cannot
    disagree with each other about what counts as `reset --hard`. An invocation whose verb the
    shell builds at run time answers YES to all of them (`GitInvocation.runs`), which is the
    fail-closed reading: the rule protects data that is gone once the command runs.
    """
    for invocation in _compat.git_invocations(command):
        if invocation.runs(*_DIRTY_RISK_SUBCOMMANDS):
            # `%s`, not `+`: an unresolved verb is `_compat.UNRESOLVED_SUBCOMMAND`, which is an
            # object precisely so no command text can spell it — it renders, it does not concatenate
            return (invocation.subcommand if invocation.resolved
                    else "git %s" % (invocation.subcommand,))
        if invocation.runs("reset") and "--hard" in invocation.arguments:
            return "reset --hard"
        if invocation.runs(*_SWITCH_SUBCOMMANDS) and _switches_branch(invocation):
            return "branch switch"
    return None


def _check_dirty(root, command):
    verb = _dirty_risk_verb(command)
    if verb is None:
        return
    status = _git(root, "status", "--porcelain")
    if not status:
        return          # clean, or not a worktree at all
    # `split(None, 1)` rather than `line[3:]`: porcelain is `XY<space>PATH`, but `_git` strips the
    # output, so the leading space of an unstaged ` M a.txt` is already gone and a fixed offset
    # eats the first character of the filename ("a.txt" was reported as ".txt").
    changed = [line.split(None, 1)[-1] for line in status.splitlines()[:5] if line.split()]
    _kernel.block(
        HOOK,
        "the worktree has uncommitted changes and `%s` can lose them (constitution §8: never work "
        "on a dirty tree).\n%s%s"
        % (verb, "\n".join("  - " + name for name in changed),
           "\n  … and more" if len(status.splitlines()) > 5 else ""),
        remedy="offer the user Commit, Stash or Discard first — that is the sequence the "
               "constitution names — then run this again. `git add`, `git stash` and "
               "`git checkout -b` stay open so you can get there.")


def main():
    data = _kernel.payload(HOOK)
    if str(data.get("hook_event_name") or "") != "PreToolUse":
        sys.exit(0)
    if data.get("tool_name") not in SHELL_TOOLS:
        sys.exit(0)
    raw = str((data.get("tool_input") or {}).get("command") or "")
    root = _kernel.find_repo_root(data.get("cwd"))
    _check_docker(root, _shell_view(raw))
    _check_dirty(root, raw)
    sys.exit(0)


if __name__ == "__main__":
    _kernel.run_gate(HOOK, main)
