"""Generation 5, goal G5-2 (user 2026-09-05: 'das bitte als naechstes implementieren'): the watcher duo
gets a real trigger and the OpenAI ladder moves to Astra / Sol / Terra. Captures the PR in DRAFT and
re-points FR-0088 and BUG-0092 (both currently under PR-0008) to it through `kernel.cli update`, so
model_tiers.yaml has ONE owning goal. Not idempotent -- run once."""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ENV = dict(os.environ, PYTHONPATH="team-kits")
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory"]

GOAL = {
    "title": "G5-2 Watchers and ladders: the radar/codex watcher duo runs on a real trigger (not a README sentence), the first codex report exists, and the OpenAI ladder in model_tiers.yaml is Astra / Sol / Terra with every pin measured",
    "class": "normal",
    "user_story": "As the user who relies on the weekly radar to keep this harness current, I want both watchers to actually run each week without me remembering them, the OpenAI half to produce its first report, and the model ladders to reflect the lineup that ships today (Astra as the Fable-equivalent top, then Sol, then Terra) -- so that the kits pin models that exist and the table's two maintainers exist in fact.",
    "problem": "Measured 2026-09-05: radar/ holds 11 claude reports and 0 codex reports; no cron job exists in the session and nothing in the repo schedules either watcher -- radar/README.md's 'a scheduled watcher duo runs once a week' is a claim without a mechanism; the radar runs happened when a human started them. team-kits/model_tiers.yaml still carries the July OpenAI ladder (gpt-5.6 Sol / Terra / Luna, GA 2026-07-09) and a dead Sonnet-5 price comment with a watch date in the past that three reports flagged and nobody fixed (BUG-0092: the watcher reports only, the lead may not write kit files, no item carried it). The user states a new top model Astra exists (FR-0088) -- unmeasured until the codex watcher runs.",
    "goal": "A trigger mechanism decided DEC-first (session-start routine of the lead vs an OS-level weekly task running the watchers headless -- measured for what survives a session end) starts both watchers weekly and is itself tested; the codex watcher produces its first dated report measuring the OpenAI lineup at the vendor's pages (ids, GA dates, prices, effort vocabulary incl. ultra); the codex ladder in model_tiers.yaml and the .codex overlay move to Astra (lead) / Sol (worker) / Terra (light) with the measured ids, one ordered ladder per provider (DEC-0034), the pin tests asserting every pin resolves (FR-0047 lineage); the dead price comment and watch date are gone and a test refuses a past watch date; the MAINTENANCE header names the route from a watcher finding to a change (an item, never a journal line).",
    "acceptance_criteria": [
        {"id": "AC-1", "text": "Trigger (FR-0088): a DEC records the chosen mechanism with the rejected alternative; after it is built, both watchers run on the trigger without a human -- measured once end to end (a run started by the mechanism writes a dated report into radar/), and a test refuses a watcher definition or README sentence that claims a schedule the repo does not build"},
        {"id": "AC-2", "text": "First codex report (FR-0088): radar/<date>-codex.md exists in the shipped report shape, sourced at the vendor's pages, naming the current OpenAI lineup with ids, GA dates, prices and effort vocabulary; its findings triaged into radar/decided.md with items where a change follows"},
        {"id": "AC-3", "text": "Ladder (FR-0088): model_tiers.yaml codex block = Astra lead / Sol worker / Terra light with the measured ids (or, if the measurement contradicts the user's statement, the measured lineup with the user asked ONCE via a DEC proposal), the .codex agent overlay and the DEC-0034 T0-T3 mapping consistent, every pin resolving in a test; red-first"},
        {"id": "AC-4", "text": "BUG-0092: the Sonnet-5 comment reworded to the standard price, the dead watch date removed, a shipped test red on any watch date in the past inside model_tiers.yaml (red-first with today's file), the MAINTENANCE header naming the finding-to-item route"},
        {"id": "AC-5", "text": "Rollout line: the protocol states how the changed ladder reaches the user's projects (release stamp -> global store install -> update-kit at the projects' next session start) and what a project sees if its pinned model no longer exists"},
    ],
    "invariants": [
        "A claim of automation is a mechanism the repo builds and a test reads, never a sentence",
        "A model pin resolves in model_tiers.yaml or the test is red; the ladder is one ordered list per provider (DEC-0034)",
        "A watcher finding becomes an item under the open goal at triage; journal lines carry pointers, not decisions",
    ],
    "out_of_scope": [
        "Changing the Claude ladder (Fable / Opus / Sonnet stays as is unless the radar report of the round measures a change)",
        "Building DEC-0034's escalation mechanics (T0-T3 runtime) -- decided, still not built, its own item",
    ],
    "priority": "high",
}


def kernel(args, body=None):
    result = subprocess.run(KERNEL + args, cwd=ROOT, env=ENV, input=json.dumps(body) if body else None,
                            capture_output=True, text=True, encoding="utf-8")
    print("$", " ".join(args[:2]), "->", result.returncode, (result.stdout or "").strip()[-200:])
    if result.returncode != 0:
        print((result.stderr or "").strip()[-800:])
        sys.exit(1)
    return result.stdout


out = kernel(["capture", "PR"], GOAL)
pr_id = re.search(r"PR-\d{4}", out).group(0)
for item in ("FR-0088", "BUG-0092"):
    kernel(["update", item], {"related_pr": pr_id})
print("GOAL", pr_id)
