#!/usr/bin/env python3
"""Payload probe for spikes S2b/S3 (phase0-disposition.md par. 5) -- FAIL-OPEN.

Registered on several hook events in a SCRATCH repo (never in a real project),
it appends one compact JSONL line per event to probe_log.jsonl in the repo
root. evaluate_probe.py turns the log into spike verdicts.
"""
import json
import sys
import time


def _truncate(value, limit=2000):
    text = json.dumps(value, ensure_ascii=False, default=str)
    return json.loads(text) if len(text) <= limit else text[:limit] + "...[cut]"


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    try:
        record = {
            "ts": time.strftime("%H:%M:%S"),
            "event": data.get("hook_event_name"),
            "tool": data.get("tool_name"),
            "agent_id": data.get("agent_id"),
            "agent_type": data.get("agent_type"),
            "payload_keys": sorted(data.keys()),
        }
        if data.get("tool_name") == "AskUserQuestion":
            record["tool_input"] = _truncate(data.get("tool_input"))
            # both candidate field names -- the spike question IS which one
            # exists and whether answers carry a structured option identity
            record["tool_response"] = _truncate(data.get("tool_response"))
            record["toolUseResult"] = _truncate(data.get("toolUseResult"))
        elif data.get("tool_name") in ("Agent", "Task"):
            record["tool_response"] = _truncate(data.get("tool_response"))
            record["toolUseResult"] = _truncate(data.get("toolUseResult"))
        elif data.get("hook_event_name") in ("SubagentStart", "SubagentStop"):
            record["agent_name"] = data.get("agent_name")
        with open("probe_log.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
