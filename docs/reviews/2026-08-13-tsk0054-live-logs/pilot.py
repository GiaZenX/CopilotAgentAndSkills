"""Phase-1 pilot for TSK-0054 (BUG-0017 behavioural confirmation), method per
docs/reviews/2026-08-12-bug0017-live-confirm.md.

Difference from that run, declared: the LIVE global kit store on this host is dev-team
2026.08.10-1, whose scaffold does not yet write `.claude/HANDOVER_PENDING`. The store was NOT
swapped (outside the approval granted for this run), so THIS runner writes the marker at exactly
the moment the current scaffold would -- right after the turn in which the kit was installed --
so the continuation turn sees the same state a real user's session would.

Everything else follows the documented method: claude_code preset system prompt, setting_sources
user/project/local, bypassPermissions, sonnet, AskUserQuestion answered through can_use_tool with
a needle->label map written BEFORE the run. Tool RESULTS are recorded too, so a hook refusal is
visible as the provider delivered it.
"""
import argparse
import asyncio
import json
import os
import sys

MARKER = os.path.join(".claude", "HANDOVER_PENDING")
INSTALLED = ("AGENTS.md", os.path.join(".claude", "settings.json"))


class Recorder:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").close()

    def __call__(self, kind, payload):
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"kind": kind, "payload": payload},
                                    ensure_ascii=False, default=str) + "\n")


def _pick(question, options, script):
    text = ((question.get("question") or "") + " " + (question.get("header") or "")).lower()
    labels = [o.get("label", "") if isinstance(o, dict) else str(o) for o in options]
    for needle, wanted in script.items():
        if needle.lower() in text:
            for label in labels:
                if wanted.lower() in label.lower():
                    return label, "scripted"
            return (labels[0] if labels else ""), "scripted-but-no-such-option"
    return (labels[0] if labels else ""), "FALLBACK-first-option"


def _place_marker(project, record, turn):
    """What the current kit's scaffold does as its last act; this store's kit does not yet."""
    if os.path.exists(os.path.join(project, MARKER)):
        return
    if not any(os.path.exists(os.path.join(project, name)) for name in INSTALLED):
        return
    os.makedirs(os.path.join(project, ".claude"), exist_ok=True)
    with open(os.path.join(project, MARKER), "w", encoding="utf-8") as handle:
        handle.write("kit installed, session must be restarted\n")
    record("marker_placed", {"after_turn": turn, "path": os.path.join(project, MARKER)})
    print("   [runner] handover marker placed after turn %d" % turn, flush=True)


async def run(scenario, project, turns, record):
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, PermissionResultAllow

    script = scenario["answers"]

    async def can_use_tool(tool_name, input_data, context):
        if tool_name != "AskUserQuestion":
            return PermissionResultAllow()
        record("asked", {"input": input_data})
        answers, how = {}, []
        for question in input_data.get("questions") or []:
            text = question.get("question") or question.get("header") or ""
            label, source = _pick(question, question.get("options") or [], script)
            answers[text] = label
            how.append({"question": text, "answer": label, "source": source})
        updated = dict(input_data)
        updated["answers"] = answers
        record("answered", {"answers": answers, "how": how})
        return PermissionResultAllow(updated_input=updated)

    options = ClaudeAgentOptions(
        cwd=project,
        model="sonnet",
        system_prompt={"type": "preset", "preset": "claude_code"},
        setting_sources=["user", "project", "local"],
        permission_mode="bypassPermissions",
        max_budget_usd=15.0,
        can_use_tool=can_use_tool,
    )
    spent = 0.0
    async with ClaudeSDKClient(options=options) as client:
        for index, message in enumerate(turns):
            record("user", {"turn": index, "text": message})
            await client.query(message)
            async for event in client.receive_response():
                data = getattr(event, "__dict__", None) or {}
                kind = type(event).__name__
                if kind in ("AssistantMessage", "UserMessage"):
                    content = data.get("content")
                    if isinstance(content, str):
                        record("raw", {"turn": index, "kind": kind, "text": content})
                        continue
                    for block in content or []:
                        body = getattr(block, "__dict__", None) or {}
                        btype = type(block).__name__
                        if btype == "TextBlock":
                            record("say", {"turn": index, "text": body.get("text", "")})
                        elif btype == "ToolUseBlock":
                            record("use", {"turn": index, "name": body.get("name"),
                                           "input": body.get("input")})
                        elif btype == "ToolResultBlock":
                            record("result_block", {"turn": index,
                                                    "is_error": body.get("is_error"),
                                                    "content": body.get("content")})
                elif kind == "ResultMessage":
                    spent = data.get("total_cost_usd") or spent
                    record("result", {"turn": index, "cost": spent,
                                      "stop": data.get("stop_reason"),
                                      "text": data.get("result")})
            print("turn %d done, %.3f USD" % (index, spent), flush=True)
            _place_marker(project, record, index)
    return spent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario")
    parser.add_argument("--log", required=True)
    parser.add_argument("--turns", type=int, default=99)
    args = parser.parse_args()
    with open(args.scenario, encoding="utf-8") as handle:
        scenario = json.load(handle)
    project = scenario["cwd"]
    os.makedirs(project, exist_ok=True)
    record = Recorder(args.log)
    record("start", {"cwd": project, "scenario": args.scenario})
    try:
        spent = asyncio.run(run(scenario, project, scenario["phase1"][:args.turns], record))
    except Exception as exc:  # noqa: BLE001
        record("error", {"type": type(exc).__name__, "message": str(exc)})
        print("FEHLER:", type(exc).__name__, str(exc)[:400], file=sys.stderr)
        raise SystemExit(1)
    record("end", {"spent": spent})
    print("done:", args.log)


if __name__ == "__main__":
    main()
