# Sicherheits-Downgrade & Modell-Stufen-Pinning — Rechercheertrag (FR-0047)

Sonnet-Recherche, 2026-08-16, auf Nutzerwunsch nach einem beobachteten Auto-Wechsel
(Fable 5 → Opus 4.8 nach einem Klassifikator-Flag). Quellen primär abgerufen; Unbestätigtes
ist als solches markiert.

## Verdikt in einem Satz

Den **Klassifikator** (der eine Nachricht als unsicher einstuft) kann man **nicht abschalten** —
aber die **Folge** eines Flags ist einstellbar: `switchModelsOnFlag` (Standard `true`) schaltet
still auf ein Ersatzmodell; auf `false` gesetzt **pausiert** die interaktive Sitzung und fragt,
statt still herunterzustufen (im SDK/headless: die Anfrage endet mit einer Verweigerung statt
mit einem stillen Wechsel).

## 1. Ist der Sicherheits-Wechsel abschaltbar?

- **Der Klassifikator selbst: nein, kein dokumentierter Opt-out.** Fable 5 und Opus 5 laufen
  „with safety classifiers for cybersecurity and biology content" als Eigenschaft der Modelle.
  (`code.claude.com/docs/en/model-config.md`, „Automatic model fallback")
- **Die Folge ist einstellbar** über `switchModelsOnFlag` (Standard `true`):
  - `true`: Claude Code fährt die geflaggte Anfrage still auf einem Ersatzmodell neu (Fable 5:
    Biologie-Flag → Opus 5, Cybersecurity-Flag → Opus 4.8) und „shows a notice in the transcript".
  - `false`: die **interaktive** Sitzung **pausiert** — Wahl zwischen „auf Ersatz wechseln" und
    „Prompt bearbeiten und auf dem aktuellen Modell erneut". **Im headless/SDK-Pfad** gibt es
    diese Wahl nicht — die geflaggte Anfrage **endet mit einer Verweigerung** (`stop_reason ===
    "refusal"` auf der `ResultMessage`), statt zu wechseln.
  - Umschalten: `/config` → „Switch models when a message is flagged", oder
    `"switchModelsOnFlag": false` in einer settings-Datei.
    (`code.claude.com/docs/en/model-config.md#ask-before-switching`)
- **Ehrliche Einschränkungen, nicht überzeichnet:**
  - Die Settings-Referenz (`settings.md`) **listet `switchModelsOnFlag` gar nicht** — direkt
    geprüft, und durch ein offenes GitHub-Issue bestätigt (`anthropics/claude-code#75913`).
  - Ein zweites Issue (`#67469`, „switchModelsOnFlag silently switches models without user
    notification", als Duplikat geschlossen, ohne gezeigte Lösung) meldet **genau den Fall des
    Nutzers**: eine ausdrückliche Fable-5-Wahl wechselte ohne auffindbaren Hinweis auf Opus. Also:
    das dokumentierte „shows a notice" und die gelebte Erfahrung **weichen ab** — die
    Hinweis-Zusage gilt als **dokumentiert, aber nutzerseitig unzuverlässig gemeldet**, nicht als
    gesichert.
  - Ein `CLAUDE_CODE_DISABLE_REFUSAL_FALLBACK` (von Sekundärquellen genannt) ist in
    `env-vars.md` **nicht** auffindbar — unbestätigt, vermutlich falsch.
  - Kein dokumentierter Enterprise-/API-Schalter befreit eine Organisation vom Klassifikator.
    Einziger echter Nebenhebel: steht das Ersatzmodell nicht auf der `availableModels`-Liste der
    Org, endet die geflaggte Anfrage mit einer Verweigerung statt mit einem Wechsel — das ändert
    das Ergebnis zu „Stopp", nicht zu „bleibt auf Fable". Der Doku-Hinweis für echten
    Fable-Bedarf ist nicht selfservice: „ask your Anthropic account team about trusted access
    programs" — Inhalt unbestätigt.

## 2. Modell-Pinning in der CLI (setzt nur das START-Modell, verhindert den Downgrade NICHT)

Vorrang (höchster gewinnt): `/model` (ab v2.1.153 als Default gespeichert) > `claude --model`
(sitzungsweise) > `ANTHROPIC_MODEL` (sitzungsweise) > `model`-Feld in settings (dauerhaft).
**Keiner dieser vier verhindert den Sicherheits-Downgrade** — der ist ein separater, späterer
Mechanismus; der einzige Hebel darauf ist `switchModelsOnFlag`.
(`code.claude.com/docs/en/model-config.md#setting-your-model`)

## 3. Agent SDK — Modell je Rolle, und welches Modell wirklich lief

- **Sitzung:** `model`-Feld auf `ClaudeAgentOptions` (Python) / `Options` (TS).
- **Je Subagent pinbar:** `model`-Feld der Subagent-Definition (Frontmatter oder
  `AgentDefinition`). Vorrang: `CLAUDE_CODE_SUBAGENT_MODEL` (global) > Aufruf-Parameter >
  eigenes `model`-Feld > geerbt. Bei geerbtem Modell deckelt die API auf Opus.
  (`code.claude.com/docs/en/sub-agents.md`)
- **Verrät der Stream das tatsächlich laufende Modell?** Ja, aber als **Kostenaufstellung**, nicht
  als eigenes Drift-Signal: `ResultMessage.modelUsage` / `.model_usage` ist „a map of model name
  to per-model token counts and cost", über den ganzen Baum inkl. Subagenten. Fiel eine Anfrage
  still zurück, landen ihre Tokens unter einem **anderen Schlüssel** als das angeforderte Modell.
  Die Doku verweist für genau diesen Zweck hierher: „read the actual model from the `modelUsage`
  field". (`code.claude.com/docs/en/agent-sdk/cost-tracking.md`)

## 4. Ein eigenes Ereignis für „gerade heruntergestuft"?

**Nein.** Weder die SDK-Nachrichtentypen noch die Hook-Ereignisse tragen etwas für einen
Modellwechsel. Nächster Kandidat: `SystemMessage`-Subtyp `"informational"` (plausibler Träger des
Transcript-Hinweises), aber die Doku sagt das **nicht** — unbestätigte Hypothese. Erkennung geht
nur **nachträglich** über den `modelUsage`-Vergleich; kein Push-Signal.

## 5. Realistischer Harness-Bauplan

| Fähigkeit | Status | Mechanismus |
|---|---|---|
| Modell-Stufe je Spezialist pinnen | **unterstützt** | `AgentDefinition.model` / Frontmatter, `CLAUDE_CODE_SUBAGENT_MODEL` als globaler Override |
| Erkennen: laufendes ≠ angefordertes Modell | **teilweise, nicht erstklassig** | nach jedem Zug `ResultMessage.modelUsage`-Schlüssel gegen das angeforderte Modell diffen; nachträglich, kein Echtzeit-Signal |
| Auf Drift alarmieren/protokollieren | **nicht eingebaut, selbst baubar** | kein Hook feuert; Anwendungscode muss `modelUsage` je `ResultMessage` prüfen und selbst alarmieren |
| Downgrade ganz verhindern | **nicht unterstützt** | Klassifikator nicht abschaltbar; `switchModelsOnFlag: false` macht aus „stiller Abstieg" ein „lautes Stoppen" (SDK: Verweigerung), nicht „bleibt auf Fable" |

## Fazit für den Harness

Pro Rolle sauber pinbar; den Klassifikator kann man nicht stoppen. Der einzige Weg, einen
Downgrade für einen SDK-getriebenen Harness **nicht still** zu machen, ist `switchModelsOnFlag:
false` — dann eine Verweigerung, die der Harness fangen (`stop_reason === "refusal"`) und
behandeln müsste (erneut versuchen, an den Nutzer eskalieren). Einen echten stillen Wechsel
(`switchModelsOnFlag: true`) erkennt man nur durch eigenes `modelUsage`-Diffing nach jedem Aufruf.

## Für DICH (interaktives Claude Code), sofort nutzbar

`/config` → **„Switch models when a message is flagged"** ausschalten. Dann stuft Claude Code bei
einem Flag **nicht mehr still** herunter, sondern **hält an und fragt** — genau das „nicht
automatisch runterstufen", das du wolltest. Der Klassifikator bleibt (den kann niemand
abschalten), aber die Entscheidung liegt dann bei dir statt beim Automatismus.
