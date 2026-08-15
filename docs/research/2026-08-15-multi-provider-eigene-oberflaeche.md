# Multi-Provider-Harness + eigene Oberfläche — Rechercheertrag (FR-0023 / FR-0024)

Zwei getrennte Sonnet-Recherchen, 2026-08-15, auf Nutzerwunsch. Web-Quellen primär abgerufen wo
angegeben; intern Gemessenes ist als solches markiert. Alles Unverifizierte trägt das Wort.

## Kernergebnis in einem Satz

Die Nutzer-Skizze — **ein** Harness (Claude-Code-Kreislauf) als Motor, fremde Modelle je Sitzung
dahinter, eigene Desktop-Oberfläche davor — ist baubar; die Anthropic-Hälfte ist in-house bereits
gemessen, die Abo-Frage ist je Anbieter verschieden und bei zweien echt gedeckt (Kimi, Qwen — mit
je einem ehrlichen Haken).

## 1. Die Abo-/Routen-Matrix (Recherche 1)

| Anbieter | Route in den Claude-Code-Kreislauf | Abo nutzbar? | Haken |
|---|---|---|---|
| **Anthropic** | nativ (ist der Kreislauf) | **Ja — heute** (in-house gemessen: Piloten laufen auf Max via `claudeAiOauth`; Support-Artikel: die angekündigte SDK-Einschränkung ist „pausiert") | Politik-Risiko: Pause ≠ Rücknahme (Radar beobachtet). NIE für Dritte: „on behalf of their users" durch Plan-Credentials ist ausdrücklich untersagt (`code.claude.com/docs/en/legal-and-compliance`) |
| **Kimi/Moonshot** | **natives Anthropic-Endpoint**, doppelt: Pay-per-Use `api.moonshot.ai/anthropic` + Abo-Endpoint `api.kimi.com/coding/` | **Ja** — Kimi-Code-Abo (~19 $/M aufwärts) trägt die eigene Endpoint-Adresse (cline#12399) | Feldberichte: langsam (~34 tok/s), Hänger, **falsch gemeldete Tool-Erfolge** — genau die Klasse, die unsere Gates angreifen müssen |
| **Qwen/DashScope** | **natives Anthropic-Endpoint** je Plan (`…/apps/anthropic`, primär abgerufen) | **Ja** — Coding Plan (~50 $/M) listet Claude Code offiziell als Client, eigenes Key-Format `sk-sp-…` | **ToS wörtlich**: „interactive coding tools (not scripts or batch calls) … personal use only" — Spannungsfeld mit headless Dispatch, ungeklärt |
| **DeepSeek** | natives Anthropic-Endpoint `api.deepseek.com/anthropic` | Frage entfällt — **es gibt kein Abo**, nur Pay-per-Token (billig) | Konsistenz über lange Sessions, Kanten im Tool-Loop (verdent.ai); Compliance-Hinweis Datenresidenz |
| **Google/Gemini** | KEIN Anthropic-Format — zwingend Proxy (LiteLLM u. ä.) | **Nein** — AI-Pro/Ultra-Abo ist laut Googles eigener Doku auf Gemini-CLI/Code-Assist beschränkt („not designed for external API endpoint consumption", primär) | API-Key + Proxy der einzige Weg; Feldbericht: Format-Mismatch erzeugt irreführende Fehlermeldungen |
| **OpenAI** | kein Anthropic-Format — zwingend Proxy | **Nein/strittig** — „Sign in with ChatGPT" laut Primärdoku nur für Codex-eigene Clients; gegenteilige Blogs sind Sekundärquellen, Community meldet Sperrungen | Für unsere Codex-Fläche (fremde CLI + Übersetzungsschicht) bereits gemessen — das ist der andere, funktionierende Weg |
| **Qoder** | ist selbst ein Modell-KONSUMENT (Alibaba-IDE), kein Anbieter mit Außen-Zugang | Nein — nur ein unreifes Reverse-Engineering-Projekt (`sontianye/qoder-api`), Muster der gesperrten OAuth-Extraktoren | grau bis verboten, keine Qualitätsdaten |
| **Lokal** (Ollama, LM Studio, vLLM, llama.cpp) | **alle vier inzwischen mit nativem Anthropic-Endpoint** (Ollama offiziell seit 2026-01-16; llama.cpp braucht `--jinja` für Tool-Use) | Frage entfällt — selbst gehostet | Tool-Calling ist die Schwachstelle kleiner Modelle; ≥32K Kontext Minimum, 64K praktikabel |

**Auflösung des scheinbaren Abo-Widerspruchs (beide Recherchen zusammen):** *Eigene* Nutzung des
eigenen Abos durch die Agent SDK ist heute gedeckt (Support-Artikel „pausing the changes … still
draw from your subscription"); *Dritte durch das eigene Abo bedienen* ist verboten
(legal-and-compliance). Für die Desktop-App des Nutzers (Selbstnutzung): okay mit benanntem
Risiko. Für einen Kundendienst (z. B. Shop-Assistent): API, nie Abo.

## 2. Architektur der eigenen Oberfläche (Recherche 2)

- **Motor**: Agent SDK, je Sitzung ein eigener Subprozess mit eigener `env`
  (`ANTHROPIC_BASE_URL`/Key) → **Provider-Besetzung je Spezialist ist der dokumentierte
  Normalfall**, kein Trick. Grenze: eine Sitzung = ein Endpunkt für ihre Lebensdauer
  (env wird beim Start gelesen, nie neu — sdk-python#573); Subagenten erben den Endpunkt,
  nur das Modell ist je Subagent wählbar.
- **In-house schon gemessen** (Piloten): Preset-Systemprompt, echte Hooks feuern, `can_use_tool`
  beantwortet AskUserQuestion (59/59), Kosten/Ratenfenster im Stream. **Neu zu bauen, aber
  dokumentiert**: Token-Streaming in die UI (`include_partial_messages`), Sitzungs-Fortsetzung
  (`resume=`), Steuern mitten im Zug (`interrupt()` — Tiefe strittig, Issue #70, unverifiziert).
- **AskUserQuestion erreicht keine Subagenten** (offizielle Grenze) — deckt sich mit der Kit-Regel
  „nur der PM spricht mit dem Nutzer".
- **Der Sicherheits-Bonus**: eine eigene Oberfläche rendert `systemMessage`-Stream-Records
  sichtbar — exakt der Kanal, dessen Terminal-Blindstelle BUG-0039 real gekostet hat
  (in-house gemessen, `tools/provider_observations.json`).
- **Nutzungsfenster**: parallele Sitzungen teilen sich das EINE Abo-Fenster (5-h- + Wochendeckel)
  — Parallelität kostet Fenster, nicht Geld (DEC-0027-Klasse).
- **Hülle**: Tauri (klein/schnell, aber Sidecar-Umweg für den SDK-Prozess) vs. Electron (größer,
  nativer Node-Weg) — offener Abwägungspunkt, keine Quelle entscheidet ihn.
- **Vorbilder statt Nullstart**: `siteboon/claudecodeui` (13,3k Sterne, täglich gepflegt,
  wickelt bereits mehrere CLI-Motoren), `musistudio/claude-code-router` (36,7k Sterne, reifste
  Provider-Routing-Schicht). LiteLLM-Warnung: zwei PyPI-Versionen trugen 2026 Schadsoftware —
  Einsatz nur mit Prüfung.

## 3. Erste Scheibe (bestätigte Reihenfolge)

1. Read-only-Kanban aus `project_memory/generated/index.yaml` (kein SDK nötig, null Risiko).
2. EINE dauerhafte PM-Sitzung mit der gemessenen Pilot-Konfiguration; Stream-Rendering inkl.
   sichtbarem `systemMessage`; AskUserQuestion als eigenes Dialog-Widget.
3. Konfig-Trennung via eigenem Config-Verzeichnis (der gemessene Pilot-Mechanismus, dauerhaft).
4. Danach erst: Roh-Eingang mit Anhängen (braucht den B10/FR-0019-Übergabeweg) und
   Mehr-Provider-Besetzung (je Anbieter eine Messrunde: Protokoll-Disziplin der Modelle an den
   Gates — die Feldberichte zu Kimi/Qwen zeigen, warum das Pflicht ist).

## Nachtrag: die zwei Stern-Projekte im Detail (READMEs primär abgerufen, 2026-08-15)

**`siteboon/claudecodeui` („CloudCLI", ~13,3k Sterne)** — Web-/Mobil-Oberfläche über lokalen
CLI-Agenten: Chat, Datei-Explorer mit Live-Editing, Git-Integration (stagen, committen, Branch),
integriertes Terminal, Browser-Sessions, Sitzungs-Verwaltung (Fortsetzen, Historie),
Plugin-System, MCP-Konfiguration. Wickelt Claude Code, Cursor CLI und Codex. Spricht mit Claude
Code, indem es direkt `~/.claude` liest/schreibt (kein SDK-Layer). Web + Mobil + optionale
Desktop-Hülle; self-hosted oder Cloud (~7 €/M). **Was fehlt (unsere Lücke):** kein Kanban, kein
Backlog, keine Item-Verwaltung — Projektmanagement nur über ein optionales Fremd-Plugin.

**`musistudio/claude-code-router` (~36,7k Sterne)** — lokales Modell-Gateway + Kontrollzentrum:
Agenten-Profile (Claude Code, Codex, Kimi CLI, u. v. m.) mit Modell-Overrides je Profil,
Provider-Verwaltung (Presets, Protokoll-Probing, Modell-Discovery, Credential-Pools), Routing
über Bedingungen/Prefixe/Rewrites/geordnete Fallbacks, Laufzeit-Modellwechsel, Dashboard mit
Latenz/Tokens/geschätzten Kosten/Agent-Traces, eigene Client-Keys mit Limits. Eigene
Browser-/Electron-Oberfläche. **Einordnung:** deckt fast die komplette Provider-Schicht unserer
FR-0023 ab — aber keinerlei Backlog/PM-Workflow, und kein Budget-**Zwang** (nur Anzeige; unser
DEC-0027-Riegel bleibt eigene Arbeit).

**Die Lücke, die keiner von beiden füllt, ist exakt unser Kern:** typisiertes Backlog,
Item-Kanban, „+ Anfrage"-Eingang, PM-Klärstrecke, Beweis-/Gate-Disziplin. Die Oberflächen- und
Routing-Schichten existieren als reife Vorbilder; der Projekt-Verstand darüber ist unser
Alleinstellungsmerkmal.

## Quellen

Vollständige Quellenlisten mit Abrufdaten in den beiden Rechercheberichten (Task-Ausgaben
2026-08-15); Schlüssel-Primärquellen: code.claude.com/docs/en/authentication,
/legal-and-compliance, support.claude.com/…/15036540, learn.chatgpt.com/docs/auth,
help.aliyun.com/en/model-studio/claude-code, docs.qwencloud.com/coding-plan/overview,
google-gemini.github.io/gemini-cli (Quota), ollama.com/blog/claude,
lmstudio.ai/docs/developer/anthropic-compat, github.com/musistudio/claude-code-router,
github.com/siteboon/claudecodeui, anthropics/claude-agent-sdk-python#573,
claude-agent-sdk-typescript#70 (unverifiziert).
