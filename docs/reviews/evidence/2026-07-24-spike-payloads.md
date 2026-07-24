# Rohbelege der Plattform-Spikes S2b und S3 (2026-07-24)

Archiviert im Repo, weil `phase0-disposition.md` §5 seine Verdikte auf genau diese
Payloads stützt — ein Bericht über empirische Provenienz muss seine Rohdaten mitführen.
Plattform: **Claude Code 2.1.219**, Windows 11, Python 3.13.0.

---

## S2b — AskUserQuestion: Antwortstruktur (Transkript-Forensik)

Quelle: Session-Transkript dieser Arbeitssession
(`~/.claude/projects/c--Offline-Repos-AgentAndSkills/34c96b63-80c8-4a18-aa7c-54f3295de165.jsonl`
— die Session-ID ist der Identifikator; die Datei wächst weiter, eine Größenangabe wäre
irreführend), 3 AskUserQuestion-Aufrufe, ausgewertet mit einem Read-only-Skript.

`toolUseResult` hat exakt zwei Top-Level-Keys: `['answers', 'questions']`
(`questions` = Echo der gestellten Frage).

**Lauf 2 — enthält BEIDE Antwortarten nebeneinander** (gekürzt, Fragetexte gekappt):

```json
{"answers": {
  "Gibst du den Phase-0-Dispositionsbericht frei? (…)": "Freigeben — Phase 1 starten",
  "Wie sollen die 13 Paritätsrisiken R1–R13 behandelt werden? (…)": "Maximal härten",
  "Was passiert mit den 2 untracked Codex-Watcher-TOMLs unter .codex/agents/ …?":
      "Idee war: ein codex watcher und einen claude watcher, damit egal welches abo man nutzt beide genutzt werden"
}}
```

Die ersten beiden Werte sind **angeklickte Options-Labels**, der dritte ist **vom User
getippter Freitext** (über die stets vorhandene „Other"-Zeile). Beide erscheinen als
blanker String im selben Mapping `Fragetext → Antwort`.

**Verdikt S2b: NEGATIV.** Es gibt keinen Options-Index, keine Options-ID, kein
Freitext-Flag. Die v2.0-Forderung „Token bindet an die Options-Identität, nie an den
Antwort-String" ist auf dieser Plattformversion nicht implementierbar → ersetzt durch den
Mint-Code-Mechanismus (Spec II.2). Bei künftigen Claude-Code-Versionen mit dem
Probe-Paket (`tools/probes/`) nachprüfen.

---

## S3 — agent_id-Bindung (headless `claude -p` mit Probe-Hooks)

Probe-Repo `%TEMP%\v2-probe` mit `tools/probes/probe_hook.py` auf PreToolUse/PostToolUse/
SubagentStart/SubagentStop; Auftrag: ein general-purpose-Subagent legt per Write eine
Datei an. Hooks feuerten ohne Trust-Problem. `probe_log.jsonl` (gekürzt):

```json
{"event":"SubagentStart","agent_id":"aa40f492c60fd0f31","agent_type":"general-purpose",
 "payload_keys":["agent_id","agent_type","cwd","hook_event_name","prompt_id","session_id","transcript_path"]}

{"event":"PreToolUse","tool":"Write","agent_id":"aa40f492c60fd0f31","agent_type":"general-purpose",
 "payload_keys":["agent_id","agent_type","cwd","effort","hook_event_name","permission_mode",
                 "prompt_id","session_id","tool_input","tool_name","tool_use_id","transcript_path"]}

{"event":"SubagentStop","agent_id":"aa40f492c60fd0f31","agent_type":"general-purpose"}

{"event":"PostToolUse","tool":"Agent","agent_id":null,
 "tool_response":{"status":"completed","agentId":"aa40f492c60fd0f31",
                  "agentType":"general-purpose","resolvedModel":"claude-sonnet-5",
                  "totalDurationMs":20256,"totalToolUseCount":2}}
```

**Verdikt S3: VERIFIED (Ende-zu-Ende).**
- `SubagentStart.agent_id` == Kind-`PreToolUse.agent_id` == `SubagentStop.agent_id`
- `PostToolUse(Agent).tool_response` trägt strukturiert `agentId` + `agentType` + `status`
  (in v2.1 noch als „undokumentiert/unverified" geführt)
- Der Eltern-Hook trägt `agent_id: null` → Hauptagent vs. Subagent sind unterscheidbar,
  genau die Semantik, die das Write-Scope-Gate braucht (Gate-Schicht 3)

Zusätzliche Bestätigung aus derselben Session: die 9 `Agent`-Tool-Results dieser
Arbeitssession tragen alle `toolUseResult.agentId` (Keys: `agentId, canReadOutputFile,
description, isAsync, outputFile, prompt, resolvedModel, status`), z. B.
`agentId: "a9aa0aa6aef6a7c6d"` mit
`outputFile: …\tasks\a9aa0aa6aef6a7c6d.output`.

Folge: Die Lease darf an **SubagentStart** ODER an das **Agent-Result** gebunden werden;
`state_write_protection: verified` ist erreichbar (Phase-2-Verdrahtung).
