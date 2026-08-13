"""Run the DEPLOYED guard as a real process against the payload captured LIVE, then mutate.

The payload is the exact `tool_input` Claude Code delivered for the AskUserQuestion in
logs/apr-live2.jsonl (record 'use', name AskUserQuestion) -- not a fixture.
"""
import json
import os
import re
import subprocess
import sys
import time

GUARD = r"C:\Users\zenti\.claude\hooks\handover_guard.py"
COPY = r"C:\tsk0054-live\guard_mutated.py"
CWD = r"C:\tsk0054-live\apr-live2"


def captured():
    for line in open(r"C:\tsk0054-live\logs\apr-live2.jsonl", encoding="utf-8"):
        rec = json.loads(line)
        if rec["kind"] == "use" and rec["payload"].get("name") == "AskUserQuestion":
            return rec["payload"]["input"]
    raise SystemExit("no live AskUserQuestion captured")


def call(guard, tool, tool_input, cwd=CWD, label=""):
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool,
               "tool_input": tool_input, "cwd": cwd}
    start = time.time()
    proc = subprocess.run([sys.executable, "-B", guard], input=json.dumps(payload),
                          capture_output=True, text=True, encoding="utf-8")
    took = time.time() - start
    first = (proc.stderr or "").strip().splitlines()
    print("%-52s rc=%d  %.2fs  %s" % (label, proc.returncode, took,
                                      (first[0][:110] if first else "")))
    return proc.returncode


def main():
    live = captured()
    print("captured question:", live["questions"][0]["question"][:120])
    print()
    print("--- deployed guard (the package as shipped) ---")
    call(GUARD, "AskUserQuestion", live, label="live payload, marker present")
    call(GUARD, "AskUserQuestion", live, cwd=r"C:\tsk0054-live\logs",
         label="live payload, NO marker in cwd")
    plain = {"questions": [{"question": "Strukturiert über einen Project Manager arbeiten?",
                            "header": "Arbeitsmodus",
                            "options": [{"label": "Ja — strukturiert (PM)"},
                                        {"label": "Nein — frei"}]}]}
    call(GUARD, "AskUserQuestion", plain, label="entry gate's own question (must be rc 0)")

    print()
    print("--- mutation: the _handle_ask branch removed ---")
    source = open(GUARD, encoding="utf-8").read()
    mutated = source.replace(
        "    elif tool in ASK_TOOLS:\n        _handle_ask(tool_input)\n", "")
    assert mutated != source, "mutation did not apply"
    open(COPY, "w", encoding="utf-8").write(mutated)
    call(COPY, "AskUserQuestion", live, label="live payload, marker present (mutated)")

    print()
    print("--- spelling variants of the same intent (class check) ---")
    for name, mangled in (
            ("lowercase [apr-req:", lambda s: s.replace("[APR-REQ:", "[apr-req:")),
            ("space after colon", lambda s: s.replace("[APR-REQ:", "[APR-REQ: ")),
            ("marker stripped", lambda s: re.sub(r"\[APR-REQ:[0-9a-f]+\]", "", s)),
            ("APR_REQ underscore", lambda s: s.replace("[APR-REQ:", "[APR_REQ:")),
    ):
        variant = json.loads(json.dumps(live))
        variant["questions"][0]["question"] = mangled(variant["questions"][0]["question"])
        call(GUARD, "AskUserQuestion", variant, label=name)

    print()
    print("--- runtime budget (registration says timeout 10) ---")
    big = {"command": ("echo " + "x" * 200 + " && ") * 400 + "python scripts/harness.py capture"}
    call(GUARD, "Bash", big, label="Bash line of %d chars" % len(big["command"]))
    os.remove(COPY)


if __name__ == "__main__":
    main()
