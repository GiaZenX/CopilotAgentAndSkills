#!/usr/bin/env python3
"""
retro.py — a READ-ONLY diagnostic retro for the PM.

Aggregates the facts of recent work (git history, gate blocks from the hook event log, the state
of the typed items) and appends a dated entry to project_memory/retro.yaml. It writes ONLY
retro.yaml (its own append-only diagnostic layer) — never project state, so it does not become a
second writer (§6). Run it manually, from CI, or from a scheduled agent; an Opus agent may then
read retro.yaml and turn the facts into concrete advice for the PM (and the PM's agent-memory).

FACTS, NOT VERDICTS. The item numbers below are a raw status mix per item type, taken from
`project_memory/generated/index.yaml` — the kernel's regenerated index over the typed items
(spec II.2/II.4). Reading the index rather than the item directories is what keeps this script
from carrying a second copy of the type→directory map (`kernel.backlog_types.ACTIVE_DIRS`), and
reporting the mix rather than a hand-picked "bad status" list is what keeps it from carrying a
second copy of the status automata. A new item type or a new status shows up here the day it
ships, without an edit.

Usage: python scripts/retro.py [--since "2 days ago"]
"""
import collections
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PM = os.path.join(ROOT, "project_memory")
INDEX = os.path.join(PM, "generated", "index.yaml")


def git(*args):
    try:
        r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=20)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def read(path):
    try:
        return open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""


def load_index():
    """(rows, problem) — the kernel's index rows, or a problem string naming what to do.

    A missing or unreadable index must never read as "no items": that is the false-green the
    whole harness keeps re-fixing. The caller reports the problem as a finding of its own.
    """
    if not os.path.isfile(INDEX):
        return [], ("no project_memory/generated/index.yaml — item facts unavailable (run "
                    "`harness generate-index`; until that CLI entry point ships — spec II.11 "
                    "step 4 — any kernel state write rebuilds the index)")
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return [], "pyyaml is not installed, so the item index could not be read"
    try:
        data = yaml.safe_load(read(INDEX))
    except Exception as exc:
        return [], "generated/index.yaml does not parse (%s) — regenerate it" % exc
    rows = (data or {}).get("items") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        return [], "generated/index.yaml carries no items: list — regenerate it"
    return [r for r in rows if isinstance(r, dict)], ""


def main():
    since = "7 days ago"
    if "--since" in sys.argv:
        since = sys.argv[sys.argv.index("--since") + 1]
    if not os.path.isdir(PM):
        print("[retro] no project_memory/ — nothing to review.")
        return

    commits = [ln for ln in git("log", "--since", since, "--oneline").splitlines() if ln.strip()]

    # gate blocks from the hook event log. The log also carries NON-block lifecycle events
    # (notify_agent_events: agent_completed / agent_needs_input) — count those separately, or one
    # parallel batch would misreport as "gates blocked work: notify_agent_events x37".
    blocks = collections.Counter()
    agent_events = collections.Counter()
    log = os.path.join(PM, ".audit", "hook_events.jsonl")
    if os.path.isfile(log):
        for line in read(log).splitlines():
            try:
                rec = json.loads(line)
                if rec.get("event") == "block":
                    blocks[rec.get("hook", "?")] += 1
                else:
                    agent_events[rec.get("event", "?")] += 1
            except Exception:
                pass

    rows, index_problem = load_index()
    status_mix = collections.defaultdict(collections.Counter)
    blocked = []
    for row in rows:
        status_mix[str(row.get("type") or "?")][str(row.get("status") or "?")] += 1
        if row.get("blocked_by"):
            blocked.append("%s (by %s)" % (row.get("id") or "?", row["blocked_by"]))

    findings = []
    if index_problem:
        findings.append(index_problem)
    if blocks:
        findings.append("gates blocked work: " + ", ".join("%s x%d" % (k, v) for k, v in blocks.most_common()))
    if agent_events:
        findings.append("background-agent events: " + ", ".join(
            "%s x%d" % (k, v) for k, v in agent_events.most_common()))
    for item_type in sorted(status_mix):
        findings.append("%s: %s" % (item_type, ", ".join(
            "%s x%d" % (s, n) for s, n in status_mix[item_type].most_common())))
    if blocked:
        findings.append("%d blocked item(s): %s" % (len(blocked), ", ".join(blocked[:8])))
    if blocks.get("guard_pm_scope"):
        findings.append("the PM tried to write code %d time(s) — should delegate" % blocks["guard_pm_scope"])
    if not findings:
        findings.append("clean: no gate blocks and no active items in the window")

    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    entry = (
        "  - date: %s\n"
        "    window: \"%s\"\n"
        "    commits: %d\n"
        "    active_items: %d\n"
        "    gate_blocks: %s\n"
        "    findings:\n%s\n"
        % (stamp, since, len(commits), len(rows),
           (json.dumps(dict(blocks)) if blocks else "{}"),
           "\n".join("      - %s" % json.dumps(f, ensure_ascii=False) for f in findings))
    )
    out = os.path.join(PM, "retro.yaml")
    if not os.path.isfile(out):
        open(out, "w", encoding="utf-8").write(
            "# retro.yaml — READ-ONLY diagnostic layer (written by scripts/retro.py, append-only).\n"
            "# NOT project state. The PM reads it for feedback; it is never a source of requirements.\n"
            "retros:\n")
    with open(out, "a", encoding="utf-8") as fh:
        fh.write(entry)

    print("[retro] %d commits, %d active item(s), blocks=%s" % (len(commits), len(rows), dict(blocks)))
    for f in findings:
        print("  - " + f)
    print("[retro] appended to project_memory/retro.yaml")


if __name__ == "__main__":
    main()
