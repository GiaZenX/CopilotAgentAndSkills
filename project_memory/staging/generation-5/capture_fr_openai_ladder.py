"""Capture the user's wish of 2026-09-05: the OpenAI ladder in team-kits/model_tiers.yaml is
outdated -- a new top model 'Astra' exists (user statement; to be MEASURED by the codex watcher,
which has never produced a report), and the codex ladder becomes Astra (= Fable tier) / Sol / Terra
instead of Sol / Terra / Luna. Body on stdin to `kernel.cli capture FR`. Not idempotent."""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "capture", "FR"]

BODY = {
    "title": "OpenAI ladder in model_tiers.yaml is a generation behind: map Astra (Fable-equivalent) / Sol / "
             "Terra to lead / worker / light for the codex provider, measured first by a codex-watcher run "
             "that has never happened",
    "problem": "team-kits/model_tiers.yaml lines 23 and 43-49 carry the codex ladder as GPT-5.6 Sol (lead) / "
               "Terra (worker) / Luna (light), family GA 2026-07-09. The user states 2026-09-05 that a new "
               "top model 'Astra' exists and equates it with the Fable tier; the ladder should read Astra / "
               "Sol / Terra. Nothing in this repo has measured the OpenAI lineup since July: radar/ holds 11 "
               "claude reports and ZERO codex reports -- the codex-watcher, named in the file's own "
               "MAINTENANCE header as one of the two maintainers of the table, has never run.",
    "goal": "One codex-watcher run measures the OpenAI lineup (model ids, GA dates, prices, effort vocabulary "
            "incl. `ultra`) against the vendor's own pages and writes its first dated report; then the codex "
            "ladder in model_tiers.yaml (comment line 23, `codex:` block, the effort notes) moves to Astra / "
            "Sol / Terra with the measured ids, the DEC-0034 T0-T3 mapping keeps one ordered ladder per "
            "provider, and the tier reader tests assert the pins resolve (FR-0047 lineage); why the codex "
            "watcher never ran is measured and fixed (schedule entry, trigger, or role) so the table has two "
            "maintainers in fact, not in a header.",
    "request_text": "User 2026-09-05: 'Wieso laeuft der codex watcher eigentlich nie? Es gibt mittlerweile ein "
                    "neues modell, \"astra\" das wuerde ich gleichsetzen mit fable und die leitern entsprechend "
                    "anpassen. Astra - Sol - Terra'",
    "source": "user statement 2026-09-05 ('Astra - Sol - Terra'); team-kits/model_tiers.yaml:8,13,23,43-49; "
              "radar/ listing (0 codex reports); DEC-0034; FR-0047",
    "related_pr": "PR-0008",
}

env = dict(os.environ, PYTHONPATH="team-kits")
result = subprocess.run(KERNEL, cwd=ROOT, env=env, input=json.dumps(BODY),
                        capture_output=True, text=True, encoding="utf-8")
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
