"""Capture the user refinement of 2026-09-05: the OFFICE kit deliberately runs the lower ladder -- no fable
except for the office-developer, otherwise opus / sonnet at medium (default) / high (large) instead of
high / xhigh. Refines DEC-0047 (office endpoints) and DEC-0077 (effort axis). Then PR-0010 AC-6 is
re-worded per kit. Two kernel calls on stdin bodies. Not idempotent -- run once."""
import json
import os
import subprocess
import sys

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ENV = dict(os.environ, PYTHONPATH="team-kits")
KERNEL = [sys.executable, "-B", "-m", "kernel.cli", "--root", "project_memory"]

DEC = {
    "title": "Buero-Kit laeuft bewusst die niedrigere Leiter: kein fable ausser fuer den office-developer, sonst "
             "opus / sonnet mit Aufwand medium (Standard) / high (grosse Ziele) statt high / xhigh -- "
             "Verfeinerung von DEC-0047 und DEC-0077",
    "context": "USER DECISION 2026-09-05, immediately after DEC-0077 (two axes, escalation built): 'nur im "
               "buero kit reichen niedrigere stufen bewusst also kein fable (ausser fuer den entwickler) und "
               "sonst opus und sonnet auf medium/high statt high xhigh'. DEC-0047 already made the ladder "
               "endpoints per kit (office compressed with opus-high as its top rung and a sonnet-LOW reading "
               "floor); DEC-0077 set the effort axis high / xhigh for every kit. Measured office pins today: "
               "office-manager and office-developer = lead (opus), every other office role = worker "
               "(sonnet), two roles low (the filing floor). The office kit's work is documents, bookkeeping "
               "and correspondence -- volume over depth; the one role that builds code is the "
               "office-developer.",
    "decision": "(1) office-team endpoints: the top rung is opus for every office role EXCEPT the "
                "office-developer, which may climb to fable under DEC-0034's escalation (stuck orders, "
                "architecture-touching CRs) like a dev-team builder; no other office role ever runs on "
                "fable. (2) office-team effort axis: `medium` by default, `high` when the goal's class is "
                "large; `xhigh` is not an office effort; the sonnet-LOW filing floor of DEC-0047 stays as the "
                "named exception. (3) NO GENERALISATION (user: 'die stufen nicht generalisieren sondern je "
                "kit eben definieren'): EVERY kit declares its OWN ladder -- rungs, endpoints, effort pair, "
                "named exceptions -- in its own declaration beside its constitution; dev-team and "
                "research-team each declare theirs (today both high / xhigh climbing to fable, but two "
                "declarations that may diverge, not one shared rule); office-team declares the ladder of "
                "(1)/(2). (4) The dispatcher READS the kit's declaration; the kernel carries no per-kit "
                "branch and no default ladder of its own -- a kit without a declaration is refused at "
                "dispatch with a sentence, a fourth kit declares its own without a kernel change; "
                "model_tiers.yaml keeps only the provider translation of the rung names (DEC-0076). (5) Built by "
                "PR-0010 AC-6 together with the mechanic; the office constitution's ladder paragraph says "
                "this (and only this).",
    "consequences": "Office projects cost less per round by design and never escalate a bookkeeper onto the "
                    "top rung; the office-developer keeps the full climb because code is where the cheap "
                    "rung fails. Cost: one more per-kit declaration to keep current; the kit's ladder "
                    "paragraph must match the declaration (a test reads both). Rejected: one global effort "
                    "pair for all kits (over-pays the office kit's routine work); fable for the "
                    "office-manager (the user keeps it at opus).",
    "source": "user message 2026-09-05; DEC-0047; DEC-0077; DEC-0034; office role pins read 2026-09-05; PR-0010",
}

AC6 = {"id": "AC-6", "text": "Escalation mechanic (DEC-0034 rules 1-5, two axes -- DEC-0077, office refinement DEC below): at spawn the dispatcher (kernel create_lease and the kit dispatch path) derives the RUNG from the role pin and the kit's declared endpoints and the EFFORT from the state -- dev/research: high by default, xhigh when the goal's class is large, climb to fable; office: medium by default, high when the goal's class is large, top rung opus for every role except the office-developer (which climbs to fable), sonnet-LOW filing floor as the named exception; EVERY kit declares its OWN ladder (rungs, endpoints, effort pair, exceptions) beside its constitution and the dispatcher READS it -- no per-kit branch and no default ladder in the kernel, a kit without a declaration is refused at dispatch; dev and research each declare theirs; rule 2: an order that FAILED climbs one rung per failure (T0 -> T1 -> T2 -> T3) with the threshold a config value carrying its DEC line and a default measured on a pilot; rule 1/3: planning and architecture start on the kit's top rung and the build falls to the build rung once scope approval is minted and the architecture frozen / SR accepted, a CR touching the architecture lifts back for that CR; rule 4/5: design starts above the build rung, QA never below T1; the chosen rung and effort are written on the lease and shown in the session brief; measured as a process on a scaffolded pilot per kit; red-first per rule"}


def kernel(args, body):
    result = subprocess.run(KERNEL + args, cwd=ROOT, env=ENV, input=json.dumps(body),
                            capture_output=True, text=True, encoding="utf-8")
    print("$", " ".join(args), "->", result.returncode, (result.stdout or "").strip()[-200:])
    if result.returncode != 0:
        print((result.stderr or "").strip()[-800:])
        sys.exit(1)
    return result.stdout


out = kernel(["capture", "DEC"], DEC)
dec_id = out.split()[0]
with open(os.path.join(ROOT, "project_memory", "product", "active", "PR-0010.yaml"), encoding="utf-8") as fh:
    pr = yaml.safe_load(fh)
acs = [ac for ac in pr["acceptance_criteria"] if ac["id"] != "AC-6"]
AC6["text"] = AC6["text"].replace("office refinement DEC below", "office refinement %s" % dec_id)
acs.insert(5, AC6)
kernel(["update", "PR-0010"], {"acceptance_criteria": acs})
print("DEC", dec_id)
