#!/usr/bin/env python3
"""Turn probe_log.jsonl into the S2b/S3 spike verdicts (run inside the probe repo)."""
import json
import os
import sys


def load():
    if not os.path.exists("probe_log.jsonl"):
        print("probe_log.jsonl fehlt -- erst die Probeschritte aus dem README ausfuehren.")
        sys.exit(1)
    records = []
    with open("probe_log.jsonl", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except ValueError:
                    continue
    return records


def main():
    records = load()
    print("=== S2 -- AskUserQuestion-Provenance ===")
    pre_q = [r for r in records if r["event"] == "PreToolUse" and r["tool"] == "AskUserQuestion"]
    post_q = [r for r in records if r["event"] == "PostToolUse" and r["tool"] == "AskUserQuestion"]
    print("PreToolUse(AskUserQuestion) Ereignisse: %d" % len(pre_q))
    print("PostToolUse(AskUserQuestion) Ereignisse: %d  -> S2a %s"
          % (len(post_q), "verified" if post_q else "UNVERIFIED (feuert nicht!)"))
    for i, r in enumerate(post_q, 1):
        print("--- Antwort-Payload %d ---" % i)
        print("  payload_keys:", r.get("payload_keys"))
        print("  tool_response:", json.dumps(r.get("tool_response"), ensure_ascii=False)[:600])
        print("  toolUseResult:", json.dumps(r.get("toolUseResult"), ensure_ascii=False)[:600])
    if len(post_q) >= 2:
        print("S2b-Bewertung: Vergleiche Payload 1 (Option 'Freigeben' GEKLICKT) mit")
        print("Payload 2 ('Freigeben' via 'Other' GETIPPT). verified NUR, wenn die beiden")
        print("strukturell unterscheidbar sind (Options-Identitaet/Index vs. Freitext-Feld).")
    else:
        print("S2b: beide Laeufe noetig (Klick + getippt) -- siehe README Schritt 1.")

    print()
    print("=== S3 -- agent_id-Bindung ===")
    starts = [r for r in records if r["event"] == "SubagentStart"]
    child_tools = [r for r in records if r["event"] == "PreToolUse" and r["tool"] in ("Edit", "Write") and r.get("agent_id")]
    post_agent = [r for r in records if r["event"] == "PostToolUse" and r["tool"] in ("Agent", "Task")]
    print("SubagentStart: %d (agent_ids: %s)" % (len(starts), [r.get("agent_id") for r in starts]))
    print("Kind-Edit/Write mit agent_id: %d (agent_ids: %s)" % (len(child_tools), sorted({r["agent_id"] for r in child_tools})))
    if starts and child_tools:
        start_ids = {r.get("agent_id") for r in starts}
        child_ids = {r.get("agent_id") for r in child_tools}
        # strict: EVERY child tool-call id must stem from a SubagentStart
        # (subset, not intersection -- avoids false positives with several
        # subagents; Fable-Check 10/NIT-1)
        match = child_ids <= start_ids
        print("Kind-PreToolUse.agent_ids ⊆ SubagentStart.agent_ids: %s -> S3 %s"
              % (match, "verified (Bindungspunkt bestaetigt)" if match else "UNVERIFIED"))
    else:
        print("S3: Subagent-Schritt fehlt -- siehe README Schritt 2.")
    for r in post_agent:
        print("PostToolUse(Agent).tool_response:", json.dumps(r.get("tool_response"), ensure_ascii=False)[:400])
    print()
    print("Ergebnis bitte in docs/reviews/phase0-disposition.md Abschnitt 5 nachtragen")
    print("(S2b/S3 verified|unverified) -- das entscheidet die Capability-Matrix (II.8).")


if __name__ == "__main__":
    main()
