"""Wiring + marker-delivery probe for TSK-0054, run against the REAL global config.

Records every event raw (including tool_result blocks) so a hook refusal is visible as the
provider delivered it, not as the runner summarised it.
"""
import argparse
import asyncio
import json
import os
import sys


class Recorder:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").close()

    def __call__(self, kind, payload):
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"kind": kind, "payload": payload},
                                    ensure_ascii=False, default=str) + "\n")


async def run(cwd, turns, record):
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, PermissionResultAllow

    async def can_use_tool(tool_name, input_data, context):
        if tool_name != "AskUserQuestion":
            return PermissionResultAllow()
        record("asked", {"input": input_data})
        answers = {}
        for question in input_data.get("questions") or []:
            text = question.get("question") or question.get("header") or ""
            labels = [o.get("label", "") if isinstance(o, dict) else str(o)
                      for o in (question.get("options") or [])]
            answers[text] = labels[0] if labels else ""
        updated = dict(input_data)
        updated["answers"] = answers
        record("answered", {"answers": answers})
        return PermissionResultAllow(updated_input=updated)

    options = ClaudeAgentOptions(
        cwd=cwd,
        model="sonnet",
        system_prompt={"type": "preset", "preset": "claude_code"},
        setting_sources=["user", "project", "local"],
        permission_mode="bypassPermissions",
        max_budget_usd=8.0,
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
                        else:
                            record("block", {"turn": index, "type": btype, "body": body})
                elif kind == "ResultMessage":
                    spent = data.get("total_cost_usd") or spent
                    record("result", {"turn": index, "cost": spent,
                                      "stop": data.get("stop_reason"),
                                      "text": data.get("result")})
            print("turn %d done, %.3f USD" % (index, spent), flush=True)
    return spent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--turn", action="append", required=True)
    args = parser.parse_args()
    os.makedirs(args.cwd, exist_ok=True)
    record = Recorder(args.log)
    record("start", {"cwd": args.cwd})
    try:
        spent = asyncio.run(run(args.cwd, args.turn, record))
    except Exception as exc:  # noqa: BLE001
        record("error", {"type": type(exc).__name__, "message": str(exc)})
        print("FEHLER:", type(exc).__name__, str(exc)[:400], file=sys.stderr)
        raise SystemExit(1)
    record("end", {"spent": spent})
    print("done:", args.log)


if __name__ == "__main__":
    main()
