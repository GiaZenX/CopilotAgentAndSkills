"""PR-0010 (DRAFT) grows by the escalation mechanic (user 2026-09-05: 'das muss auch gebaut werden') and
the three-rung / two-axes decisions (DEC-0076, the two-axes DEC): class -> large, AC-6/AC-7 added,
AC-3 re-worded to three rungs. Body on stdin to `kernel.cli update PR-0010`."""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory", "update", "PR-0010"]

BODY = {
    "title": "G5-2 Watchers, ladders and escalation: the radar/codex watcher duo runs on a real trigger, the first codex report exists, the ladders are three rungs per provider (fable/opus/sonnet = astra/sol/terra, DEC-0076), effort is high by default and xhigh for large goals, and DEC-0034's escalation mechanic is BUILT in the dispatcher (two axes, from state)",
    "class": "large",
    "acceptance_criteria": [
        {"id": "AC-1", "text": "Trigger (FR-0088): a DEC records the chosen mechanism with the rejected alternative; after it is built, both watchers run on the trigger without a human -- measured once end to end (a run started by the mechanism writes a dated report into radar/), and a test refuses a watcher definition or README sentence that claims a schedule the repo does not build"},
        {"id": "AC-2", "text": "Codex report (FR-0088): the first report exists (radar/2026-09-05-codex.md, manual trigger); the round's own trigger produces the next one in the shipped shape; the `max` vs `ultra` effort ceiling of Sol/Terra/Astra is measured against the CLI, not copied from the contradicting docs; findings triaged into radar/decided.md with items where a change follows"},
        {"id": "AC-3", "text": "Ladders (DEC-0076): model_tiers.yaml carries exactly three rungs per provider -- claude fable / opus / sonnet, codex astra / sol / terra with the measured ids -- no `light` alias, no haiku or luna row; the generator refuses a `light`/`haiku` pin with a sentence naming DEC-0076; the .codex overlay and the constitutions' ladder sentences consistent; every pin resolving in a test (FR-0047 lineage); red-first"},
        {"id": "AC-4", "text": "BUG-0092 (both providers): the Sonnet-5 comment and the OpenAI price anchors reworded to the measured current prices, dead watch dates removed, a shipped test red on any watch date in the past inside model_tiers.yaml (red-first with today's file), the MAINTENANCE header naming the finding-to-item route"},
        {"id": "AC-5", "text": "Rollout line: the protocol states how the changed ladder and the mechanic reach the user's projects (release stamp -> global store install -> update-kit at the projects' next session start) and what a project sees if its pinned model no longer exists"},
        {"id": "AC-6", "text": "Escalation mechanic (DEC-0034 rules 1-5, two axes): at spawn the dispatcher (kernel create_lease and the kit dispatch path) derives the RUNG from the role pin and the kit endpoint (DEC-0047) and the EFFORT from the state -- high by default, xhigh when the goal's class is large, low only as the named office reading floor; rule 2: an order that FAILED climbs one rung per failure (T0 -> T1 -> T2 -> T3) with the threshold a config value carrying its DEC line and a default measured on a pilot; rule 1/3: planning and architecture start on the top rung and the build falls to the build rung once scope approval is minted and the architecture frozen / SR accepted, a CR touching the architecture lifts back for that CR; rule 4/5: design starts above the build rung, QA never below T1; the chosen rung and effort are written on the lease and shown in the session brief; measured as a process on a scaffolded pilot per kit (dev climbs to fable, office tops at opus, research climbs to fable); red-first per rule"},
        {"id": "AC-7", "text": "Decided-vs-built: DEC-0034, DEC-0047, DEC-0076 and the two-axes DEC are cited by the code that implements them, the three constitutions' ladder paragraphs say what is BUILT (no sentence claims a climb the dispatcher does not make), and the model_tiers.yaml header stops calling the mechanic an open work item"},
    ],
    "out_of_scope": [
        "Changing the Claude rung names (fable / opus / sonnet stay)",
        "A six-rung ladder or any escalation that is not derived from state (rejected by the two-axes DEC)",
    ],
}

env = dict(os.environ, PYTHONPATH="team-kits")
result = subprocess.run(KERNEL, cwd=ROOT, env=env, input=json.dumps(BODY),
                        capture_output=True, text=True, encoding="utf-8")
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
