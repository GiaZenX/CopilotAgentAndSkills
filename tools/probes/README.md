# S2b/S3-Proben — Status: BEIDE ENTSCHIEDEN (2026-07-24)

> **Diese Proben mussten nicht vom User gefahren werden** (Befunde gelten für
> **Claude Code 2.1.219**; Rohbelege in `docs/reviews/evidence/2026-07-24-spike-payloads.md`).
> - **S2b** wurde per **Transkript-Forensik** entschieden (echte Klick- und
>   Freitextantworten lagen in der Session bereits vor): `toolUseResult.answers`
>   liefert nur Strings → Options-Identität existiert nicht → Mint-Code-Mechanismus.
> - **S3** wurde per **headless `claude -p`-Lauf** mit genau diesen Probe-Hooks
>   entschieden: `SubagentStart.agent_id` == Kind-`PreToolUse.agent_id`,
>   `PostToolUse(Agent).tool_response.agentId` vorhanden → verified.
>
> Verdikte + Belege: `docs/reviews/phase0-disposition.md` §5.
> Das Paket bleibt als **Regressionswerkzeug**: nach jedem Claude-Code-Update
> erneut laufen lassen, um zu prüfen, ob sich die Payload-Formen geändert haben
> (insbesondere ob `answers` irgendwann Options-Identität liefert — dann kann
> `approval_provenance` auf die strengere Definition hochgestuft werden).

## Original-Anleitung (manueller Lauf, weiterhin gültig)

Die Proben BELEGEN die zwei Plattform-Verdikte in
`docs/reviews/phase0-disposition.md` Abschnitt 5 (beide seit 2026-07-24 entschieden —
diese Anleitung dient der REGRESSIONSPRÜFUNG nach Claude-Code-Updates):

- **S2b:** Liefert PostToolUse(AskUserQuestion) die gewählte Option
  STRUKTURELL (Options-Identität) — unterscheidbar von getipptem
  „Other"-Freitext? → entscheidet, ob `approval_provenance` auf Claude
  `verified` werden kann (sonst bleibt ehrlich `audited`).
- **S3-E2E:** Trägt jeder Tool-Call eines Subagenten dieselbe `agent_id`
  wie sein `SubagentStart`-Event? → bestätigt den Lease-Bindungspunkt
  und `state_write_protection: verified`.

## Einrichtung (einmalig, ~30 Sekunden)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Offline Repos\AgentAndSkills\tools\probes\setup_probe_repo.ps1"
```

Dann im erzeugten Probe-Repo (`%TEMP%\v2-probe`) eine NEUE Claude-Code-Session
starten und beim Start die Hooks vertrauen (/hooks).

Voraussetzung: `python` liegt auf dem PATH (sonst in
`.claude/settings.json` die vier Vorkommen von `python` durch `py` ersetzen).

## Schritt 1 — S2b (zwei Fragen, ~1 Minute)

In der Probe-Session eingeben:

> Stelle mir mit AskUserQuestion eine Frage mit genau den Optionen
> „Freigeben", „Ändern", „Ablehnen". Stelle danach dieselbe Frage noch einmal.

- **Erste Frage:** Option **„Freigeben" ANKLICKEN**.
- **Zweite Frage:** über die **„Other"-Zeile** das Wort **Freigeben TIPPEN**.

## Schritt 2 — S3 (ein Subagent, ~1 Minute)

Danach eingeben:

> Spawne einen general-purpose-Subagenten, der mit dem Write-Tool eine Datei
> probe.txt mit dem Inhalt „hello" anlegt.

## Auswertung

```powershell
python evaluate_probe.py
```

Das Skript druckt die Roh-Payloads und die Verdikt-Logik:

- **S2b verified**, wenn die beiden Antwort-Payloads strukturell verschieden
  sind (geklickte Option als Identität/Index vs. Freitext-Feld). Sind sie
  ununterscheidbar (nur ein Text-String), bleibt `approval_provenance`
  auf Claude **audited** — genau die ehrliche v2.1-Haltung.
- **S3 verified**, wenn `SubagentStart.agent_id` in den PreToolUse-Events
  der Kind-Writes wieder auftaucht.

**Bei Regressionsläufen:** Jede Abweichung zur Referenz in
`docs/reviews/evidence/2026-07-24-spike-payloads.md` melden — insbesondere, wenn
`answers` plötzlich Options-Identität liefert (dann kann `approval_provenance` auf die
strengere Definition hochgestuft werden) oder wenn sich die agent_id-Bindung ändert
(dann wackelt `state_write_protection`). Beides speist die Enforcement-Capability-Matrix
(Spec II.8).
