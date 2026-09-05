"""Capture the stale model_tiers.yaml pricing comment as a BUG under PR-0008 (G5-1) -- flagged by
the radar watcher three times (2026-08-21 / 08-29 / 09-04) and never fixed because it fell between
the roles (the watcher reports only, the lead may not write kit files, no stream carried it; the
08-29 'rider fix itemized' landed in radar/decided.md, not in an item). Body on stdin to
`kernel.cli capture BUG`. Not idempotent -- run once."""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "capture", "BUG"]

BODY = {
    "title": "team-kits/model_tiers.yaml carries a dead pricing comment and a dead watch date (Sonnet 5 "
             "'intro $2/$10 until 2026-08-31') -- flagged by the radar watcher three times, fixed by nobody "
             "because the fix fell between the roles",
    "severity": "low",
    "observed": "radar/2026-09-04-claude.md item 5 (and 2026-08-29, 2026-08-21): team-kits/model_tiers.yaml "
                "line 22 reads 'Sonnet 5 $3/$15 (intro $2/$10 until 2026-08-31)' and line 24 lists "
                "'2026-08-31 Sonnet 5 intro pricing ends' as a watch date; the pricing page says $2/$10 is "
                "the permanent price and the increase will not occur; 2026-08-31 has passed. The file's own "
                "header names the two watchers as maintainers of the table's currency, but the watcher's "
                "mandate is report-only, the lead may not write a kit file (gate 1: model_tiers.yaml is in the "
                "kit hash), and no stream item carried the two lines; radar/decided.md 2026-08-29 says "
                "'rider fix itemized' -- in the journal, not in an item (the prose-instead-of-item failure).",
    "expected": "The comment states the standard price and no dead watch date; the table's MAINTENANCE header "
                "says how a watcher finding becomes a change (an item under the current goal, not a journal "
                "line), so the third-report class cannot recur; the model_tiers reader test (FR-0047 "
                "lineage) or a small tripwire refuses a watch date in the past.",
    "repro": "grep -n '2026-08-31' team-kits/model_tiers.yaml -> two hits; compare with "
             "https://platform.claude.com/docs/en/about-claude/pricing (Sonnet 5 $2/$10 standard).",
    "acceptance_criteria": [
        {"id": "AC-1", "text": "model_tiers.yaml lines 22/24 reworded to the standard price, the dead watch date removed; the Opus-4.1 line kept"},
        {"id": "AC-2", "text": "a shipped test is red on a watch date in the past inside model_tiers.yaml (red-first with today's file), so a stale trigger date cannot outlive itself again"},
        {"id": "AC-3", "text": "the MAINTENANCE header names the route from a watcher finding to a change: an item under the open goal, captured by the lead at triage -- measured against the text"},
    ],
    "related_pr": "PR-0008",
    "source": "radar/2026-09-04-claude.md item 5; radar/decided.md radar-0821-sonnet5-price-trigger",
}

env = dict(os.environ, PYTHONPATH="team-kits")
result = subprocess.run(KERNEL, cwd=ROOT, env=env, input=json.dumps(BODY),
                        capture_output=True, text=True, encoding="utf-8")
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
