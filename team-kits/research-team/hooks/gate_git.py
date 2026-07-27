#!/usr/bin/env python3
"""
PreToolUse(Bash) gate — protects merge/push.

- Force-push is ALWAYS blocked (the constitution forbids it).
- `git push` / `git merge` are blocked once there is real work
  (an RQ entry exists) but NO passing QA/validation report yet.
  Empty/just-scaffolded repos are not gated.

Reads the hook JSON from stdin; exit 2 + stderr blocks. Any uncertainty -> exit 0.
"""
import sys
import os
import re
import glob


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _compat
from _root import find_repo_root, has_root_item
from _compat import git_invocation_text, run_captured
import _audit


def block(why):
    _audit.record("gate_git", why)
    sys.stderr.write("[team-kit gate] Blocked: %s\n" % why)
    sys.exit(2)


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception:
        return ""


def main():
    # BOUNDED read (spec II.4). A raw `json.load(sys.stdin)` will happily buffer a
    # payload of any size, and an oversized one is the shape that turns a hook into
    # a memory event rather than a decision. `_compat.load` caps it at STDIN_LIMIT
    # and exits 2, because a gate that cannot read its input has not judged it.
    data = _compat.load()
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        sys.exit(0)
    cmd = ((data.get("tool_input") or {}).get("command") or "")
    # Detection lives in _compat.git_invocation_text (single home): wrapper payloads are CODE,
    # quoted prose is not (a commit MESSAGE once re-triggered this gate — real incident).
    low = git_invocation_text(cmd)
    if not re.search(r"\bgit\b[^&|;\n]*\b(push|merge)\b", low):
        sys.exit(0)

    # force-push: always forbidden (flags AND the `+refspec` form, e.g. `git push origin +main`).
    # Checked on the RAW text: quoted flags (`git push "--force"`, `"+main"`) reach git after the
    # shell strips the quotes, so hiding them in quotes must not disarm the ban (audit finding);
    # over-triggering is acceptable for an always-forbidden action.
    raw_low = cmd.lower()
    if re.search(r"\bgit\b[^&|;\n]*\bpush\b", low) and re.search(
            r"--force(-with-lease)?|(^|[\s\"'])-f([\s\"']|$)|[\s\"']\+[\w./-]+(:|[\s\"']|$)",
            raw_low):
        block("force-push is forbidden by the team constitution.")

    cwd = find_repo_root(data.get("cwd"))
    pm = os.path.join(cwd, "project_memory")
    if not os.path.isdir(pm):
        sys.exit(0)  # nothing to gate yet

    # is there real work? (a root item exists — see `_root.has_root_item`, the ONE definition
    # five gates used to compute for themselves by grepping a monolith)
    if not has_root_item(cwd):
        sys.exit(0)

    # which RQ is being merged/pushed? (from the command, else the current branch name)
    target = None
    m = re.search(r"(RQ-\d+)", cmd, re.IGNORECASE)
    if not m:
        try:
            br = run_captured(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
                              timeout=5).stdout
            m = re.search(r"(RQ-\d+)", br, re.IGNORECASE)
        except Exception:
            m = None
    if m:
        target = m.group(1).upper()

    # require a passing QA/validation/acceptance report — bound to THIS RQ when it is known.
    # Audit finding: FILE-level text matching let an old PASS for another task plus a fresh FAIL
    # for the target coexist in one file and lift the gate. Entry-level rule: when any report
    # ENTRY is bound to the target, a BOUND entry must pass; only when no entry carries the
    # binding at all (indirect linkage) does the file-level check apply. No PyYAML -> file-level
    # fallback (fail-open philosophy).
    passing = False
    for f in glob.glob(os.path.join(pm, "*report*.yaml")):
        txt = read_text(f)
        verdict = entry_verdict(txt, target)
        if verdict is True:
            passing = True
            break
        if verdict is False:
            continue  # bound entries exist and none passes — this file cannot lift the gate
        if not re.search(r"result:\s*pass|verdict:\s*pass", txt, re.IGNORECASE):
            continue
        if target is None or re.search(re.escape(target), txt, re.IGNORECASE):
            passing = True
            break
    if not passing:
        block("no passing QA/validation report for %s in project_memory — run the QA gate "
              "(a passing review/test/acceptance report for this RQ) before merge/push."
              % (target or "this work"))

    sys.exit(0)


def entry_verdict(txt, target):
    """Entry-level pass check. Returns True (a bound entry passes), False (bound entries exist,
    none passes), or None (no bound entries / no parser -> caller falls back to file-level)."""
    if not target:
        return None
    try:
        import yaml  # type: ignore[import-untyped]
        doc = yaml.safe_load(txt)
    except Exception:
        return None
    bound_seen, bound_pass = False, False
    stack = [doc] if doc is not None else []
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            verdict = str(node.get("result", node.get("verdict", ""))).strip().lower()
            if verdict:
                bound = any(target in str(v).upper() for v in node.values())
                if bound:
                    bound_seen = True
                    if verdict == "pass":
                        bound_pass = True
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    if bound_pass:
        return True
    return False if bound_seen else None


if __name__ == "__main__":
    main()
