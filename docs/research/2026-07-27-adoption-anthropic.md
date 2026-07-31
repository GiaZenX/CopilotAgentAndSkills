# Recherche: `anthropics/skills` als Adaptionsquelle für die sechs dev-team-Rollen

**Quellenstand:** `github.com/anthropics/skills` @ `main`, abgerufen 2026-07-27 via `gh api` (Tree + Blobs, nicht über Suchmaschine). Zusätzlich `agentskills.io/specification` und `code.claude.com/docs/en/skills` + `/plugin-marketplaces`.

**Gemessene Randbedingung vorweg:** `skills/frontend-design/SKILL.md` = 8 260 Bytes, 55 Zeilen, 1 336 Wörter, 30 nicht-leere Zeilen. Auf unsere Umbruchbreite (~105 Spalten) reformatiert: **121 Zeilen** — also 81 % des gesamten 150-Zeilen-Budgets einer Rolle für eine einzige Fremddatei. Wortlaut-Übernahme ist damit rechnerisch ausgeschlossen, unabhängig von der Qualität.

---

## 1. `frontend-design/SKILL.md` im Detail

### Was drinsteht
Frontmatter: `name`, `description`, `license: Complete terms in LICENSE.txt`. Fünf Abschnitte: *Ground it in the subject* · *Design principles* (Hero/Typografie/Struktur/Motion/Komplexität/Copy) · *Process: brainstorm, explore, plan, critique, build, critique again* · *Restraint and self-critique* · *More on writing in design*. Rahmenrolle: „the design lead at a small studio known for giving every client a visual identity that could not be mistaken for anyone else's."

### Was daran wirklich gut ist (mit Beleg)

**(a) Die Kalibrierungsliste — der beste Absatz der Datei.**
> „AI-generated design right now clusters around three looks: (1) a warm cream background (near #F4F1EA) with a high-contrast serif display and a terracotta accent; (2) a near-black background with a single bright acid-green or vermilion accent; (3) a broadsheet-style layout with hairline rules, zero border-radius, and dense newspaper-like columns."

Das ist kein Listicle, sondern eine **falsifizierbare Negativaussage mit Hex-Wert**. Unser Designer-SKILL hat an derselben Stelle nur ein Urteil: „Generic ‚0815', Bootstrap-default or unstyled-component-library looks are a **FAIL**" — ein Fail-Kriterium, das niemand anwenden kann, ohne den Geschmack schon zu haben. Die Anthropic-Zeile ist inhaltlich **exakt das, was SYNTHESE B1 als „Anti-Referenzen" im Design-Anker-DEC fordert** und wofür die SYNTHESE keinen Text liefert.

**(b) Der Selbsttest mit beschriebenem Fehlschlag.**
> „if any part of it reads like the generic default you would produce for any similar page (work through a similar prompt to see if you arrive somewhere similar) rather than a choice made for this specific brief — revise that part, say what you changed and why."

Die Klammer ist eine **Prozedur** (Prompt gedanklich neu laufen lassen, Konvergenz prüfen), keine Ermahnung. Unser Äquivalent — „Fence-sitting ‚safe' defaults ARE the AI-slop to avoid" — ist ein Urteil ohne Verfahren.

**(c) Die Vorrangregel, die uns fehlt.**
> „Where the brief pins down a visual direction, follow it exactly — the brief's own words always win, including when it asks for one of these looks."

Unser SKILL regelt den *reduzierten* Fall („When the user chose the MINIMAL ambition"), aber nicht den Fall „der User will ausdrücklich den Cream-Serif-Look". Eine Zeile, echte Lücke.

**(d) Der Copy-/UX-Writing-Abschnitt — die größte echte Lücke bei uns.**
> „Words appear in a design for one reason: to make it easier to understand, and therefore easier to use. They are design material, not decoration."
> „An action keeps the same name through the whole flow, so the button that says ‚Publish' produces a toast that says ‚Published.'"
> „Treat failure and emptiness as moments for direction, not mood. […] Errors don't apologize, and they are never vague about what happened. An empty screen is an invitation to act."

`product-designer/SKILL.md` und `frontend-developer/SKILL.md` enthalten zusammen **null Zeilen** über Text im Interface. Das ist genau SYNTHESE **B5** (UI-Text-Tabelle in der DSN + Platzhalter-Sperrliste) und **B4** (Zustandsmatrix loading/empty/error) — beides bereits beschlossen, beides ohne Inhalt. Hier spart Übernahme echte Arbeit. Und „Publish → Published" ist *mechanisch prüfbar*, sobald B5s Texttabelle existiert (Verb-Paar Button ↔ Toast).

**(e) Ein benannter CSS-Defekt.**
> „It's easy to generate CSS classes that cancel each other out (especially with a type-based selector like `.section` and a element-based selector like `.cta`). This can happen often with paddings/margins between sections."

Dasselbe Genre wie unsere eigene Zeile „form controls do NOT inherit fonts by default — a real run shipped a wrong-font button because of this". Reproduzierbar, gehört in den Base-Reset-Block bzw. zum Frontend.

### Was daran Listicle bzw. für unser Harness unbrauchbar ist

- *„Match complexity to the vision. Maximalist directions need elaborate execution; minimal directions need precision […]. Elegance is executing the chosen vision well."* — Tautologie.
- *„Consider Chanel's advice: before leaving the house, take a look in the mirror and remove one accessory."* — Merksatz, unfalsifizierbar.
- *„Not taking a risk can be a risk itself!"* — das Ausrufezeichen ersetzt das Argument.
- *„Build to a quality floor **without announcing it**: responsive down to mobile, visible keyboard focus, reduced motion respected."* — **verletzt unsere Hausregel frontal.** Ein nicht benannter Qualitätsboden ist nicht gate-fähig. Wir nennen Zahlen (150–250 ms, WCAG AA, < 100 ms Perceived) und bekommen mit C1/C3 Gates dafür; Anthropic macht eine Drei-Wort-Geste in Richtung a11y.
- *„Critique your own work as you build, taking screenshots **if your environment supports it**"* — optionaler Schutz. Unser Phase-3-Review ist eine Vollmatrix („every screen/tab × light+dark × desktop+mobile width — and you SIGHT every image", 38-Screenshot-Vorfall als Begründung).
- *„Try to do a lot of this planning and iteration **in your thinking**, and only show ideas to the user when you have higher confidence it'll delight them."* — **darf nicht übernommen werden.** Das ist der dokumentierte PM-Fehler unseres eigenen Harness: „a real PM asked sign-off for a summary that existed only in its thinking (‚wie oben zusammengefasst') and the user decided blind."

### Wo unsere SKILLs klar besser sind

| Achse | Anthropic | Unser `product-designer` |
|---|---|---|
| Divergenz | **eine** Richtung („Work in two passes"), Divergenz nur als Selbstkritik gegen drei bekannte Klischees | „**2–3 genuinely different, named directions** — distinct moods, all at top-tier quality, **NOT three shades of one idea**", je mit realem Hex, realem Font-Paar, realem Motion-Wert („120 ms ease-out, slight overshoot" vs. „220 ms cross-fade") |
| Entscheidbarkeit durch den User | keine — der Skill berät den Bauenden | „ONE file under `staging/<task-id>/` … that renders ALL directions side by side as real tiles … and **a real button and card with a live hover/press transition at the stated timing. This is what makes ‚choose a design' real instead of picking a name.**" |
| Vertrag nach unten | strukturell keiner — Designer *ist* der Bauende | „**Mandatory: extend the staged preview into PER-VIEW SCREEN MOCKUPS** … Frozen, this file **IS** the visual contract … (a real run ‚recolored' four slices because no per-view contract existed)" |
| Zahlen | genau drei Hex-Klischees, sonst keine | 150–250 ms, 4/8-pt-Scale, 12/14/16/20/24/32/48, < 100 ms, WCAG AA in **beiden** Themes, Token-Liste light+dark |
| Nachkontrolle | „screenshots if your environment supports it" | Phase 3: Vollmatrix + **Inventar-Diff** („a removed/replaced element without a CR is a deviation, never a detail") |

**Ehrliche Antwort auf die gestellte Frage: Nein — die Anthropic-SKILL schlägt unseren Designer nicht.** Sie ist ein besseres *Briefing für einen einzelnen kreativen Agenten*; unsere ist ein *Prozess mit Artefakten, einem Entscheider und einem nachgelagerten Konsumenten*. Sie enthält aber drei Dinge, die uns fehlen.

### Was wir konkret nehmen (≈ 12 Zeilen)

1. **Klischee-Kalibrierung (4 Z.)** → Phase 1 des Designers, und als Anti-Referenz-Inhalt für B1. **Nicht** als Gate: „warmes Creme mit Serif" ist ein *Look*, kein Literal — ein Gate darauf wäre ein Gate, dessen Fehlschlag man nicht beschreiben kann. (Der einzige gate-fähige Rest: der konkrete Hex `#F4F1EA` und, aus `web-artifacts-builder`, `Inter` + „uniform rounded corners" — die passen in B2/B3.)
2. **Brief-gewinnt-Vorrangregel (1 Z.)** → neben den MINIMAL-Absatz.
3. **UX-Writing (6–8 Z.)** → als **Inhalt für B5** (Beschriftung/Button/Leerzustand/Fehler, Verbkonsistenz Button↔Toast, „errors don't apologize / never vague", „an empty screen is an invitation to act"). Wegen Budget gehört der Großteil davon in `references/ui-copy.md` (siehe §3), im Körper bleibt der Zeiger + die Sperrliste.
4. **CSS-Spezifitätsfalle (1 Z.)** → `frontend-developer`, neben die Font-Inherit-Zeile.

Alles Übrige: ignorieren.

---

## 2. Die übrigen Skills des Repos — je eine Zeile + Rollen-Mapping

| Skill | Größe | Lizenz | Was es ist | Unsere Rolle |
|---|---|---|---|---|
| `webapp-testing` | 3,9 KB | Apache-2.0 | Playwright-Rezept + `scripts/with_server.py` als Black-Box-Helper, Entscheidungsbaum statisch/dynamisch | quality-engineer, frontend-developer |
| `skill-creator` | 33 KB | Apache-2.0 (LICENSE.txt; **kein `license:`-Frontmatter**) | Meta-Skill: Skills schreiben, evaluieren, gegen Baseline benchmarken | project-auditor / Phase II.11/3 |
| `brand-guidelines` | 2,2 KB | Apache-2.0 | Anthropics eigene Hex/Font-Liste, reiner Inhalt ohne Methode | product-designer (nur als *Form* eines B1-Ankers) |
| `theme-factory` | 3,1 KB | Apache-2.0 | 10 Preset-Themes + Vier-Schritt-Auswahlprotokoll (Showcase zeigen → fragen → warten → anwenden) | product-designer |
| `canvas-design` | 12 KB | Apache-2.0 | „Design-Philosophie als .md zuerst, dann visuell ausdrücken" für Poster/PNG/PDF | product-designer (marginal) |
| `algorithmic-art` | 20 KB | Apache-2.0 | p5.js-Generativkunst mit Seed-Determinismus + Viewer-Template | keine |
| `web-artifacts-builder` | 3,1 KB | Apache-2.0 | React/Tailwind/shadcn-Scaffold + Bundle-zu-Einzeldatei-Skripte | frontend-developer (**eine** Zeile: „avoid excessive centered layouts, purple gradients, uniform rounded corners, and Inter font") |
| `slack-gif-creator` | 7,8 KB | Apache-2.0 | GIF-Constraints + Validierungsutilities für Slack | keine |
| `mcp-builder` | 9,1 KB | Apache-2.0 | Wie man MCP-Server entwirft (Tool-Granularität, Fehlermeldungen, Evaluation) | software-architect/backend — nur als Projekt-Domäneninhalt, keine Rollenregel |
| `internal-comms` | 1,5 KB | Apache-2.0 | Router: Comms-Typ erkennen → `examples/<typ>.md` laden | project-manager (als *Muster*, siehe §3) |
| `doc-coauthoring` | 16 KB | **KEINE** | Drei-Stufen-Workflow: Context Gathering → Refinement → Reader Testing | project-manager — **nicht adoptierbar** |
| `claude-api` | 72 KB + ~40 Referenzdateien | Apache-2.0 | Claude-API/SDK-Referenz mit sehr aggressivem TRIGGER/SKIP-Description | research-engineer, backend-developer |
| `docx` / `pdf` / `pptx` / `xlsx` | 7–21 KB + Skripte/XSDs | **proprietär** | Office/PDF-Manipulation mit gebündelten Python-Skripten | office-team — **hartes Nein** |

---

## 3. Autorenkonventionen, die unabhängig vom Inhalt übernehmenswert sind

**(1) `references/` als Antwort auf das 150-Zeilen-Budget — mit einer Einschränkung, die ausgesprochen werden muss.**
Spec: „Metadata (~100 tokens) … Instructions (< 5000 tokens recommended) … Resources (as needed)" und „Keep your main `SKILL.md` under 500 lines. Move detailed reference material to separate files." `internal-comms` ist die Minimaldemonstration: 40 Zeilen Routing, die vier Dateien unter `examples/` benennen.
**Bei uns kostenlos verfügbar:** `scaffold_team.ps1:487` kopiert Skill-Ordner mit `Copy-Item $_.FullName $d -Recurse -Force` — ein `references/`-Unterordner reist heute schon mit, ohne eine Zeile Infrastruktur.
**Die Einschränkung:** Eine Regel in `references/` ist eine Regel, die das Modell vielleicht nicht liest. Für eine *erzwungene* Regel ist das die Degradierung in genau den Fehler, den dieses Harness benennt. Der ehrliche Schnitt: **Regeln mit Gate dürfen nach `references/` wandern** (das Gate ist die Durchsetzung, der Text die Erklärung); **Regeln ohne Gate bleiben in den 150 Zeilen oder werden gelöscht.** Dieselbe Zweiteilung, die die Paritätsmatrix ohnehin braucht — und sie ergänzt die Matrix um eine dritte Kategorie neben „durch Gate ersetzt" und „gestrichen": „nach `references/` verschoben, weiterhin autorisiert, durch Gate X gedeckt".

**(2) `description` als Trigger-Fläche, bewusst „pushy" und mit explizitem SKIP.**
`skill-creator`: „currently Claude has a tendency to ‚undertrigger' skills […] instead of ‚How to build a simple fast dashboard…', you might write ‚…**Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics** … even if they don't explicitly ask for a "dashboard."'" `claude-api` treibt es weiter: eine zweiteilige TRIGGER/SKIP-Description mit einem *ausführbaren* Skip-Test (`grep -rE 'openai|langchain_openai|…'`).
**Befund über unsere eigenen Dateien:** alle neun Descriptions enden auf „Preloaded into the X subagent." Das ist wahr und als Trigger wertlos — für preloaded Subagent-Skills triggert die Description ohnehin nicht (Doku: „Subagents with preloaded skills work differently: the full skill content is injected at startup"). Der Nutzen ist bei uns also **kleiner als es aussieht** und beschränkt sich auf `project-manager` (Session-Agent) und alles, was per `/name` aufgerufen wird. Kostet null Körperbudget (Frontmatter, 1 024 Zeichen erlaubt) — dort könnte statt der Preload-Notiz die Abgrenzung „wann NICHT diese Rolle" stehen.

**(3) Gebündelte `scripts/` als Black Box.**
`webapp-testing`: „**Always run scripts with `--help` first** … DO NOT read the source until you try running the script first and find that a customized solution is absolutely necessary. These scripts can be very large and thus pollute your context window. They exist to be called directly as black-box scripts rather than ingested into your context window."
Spec und Claude-Code-Doku erlauben das ausdrücklich (`scripts/` ist erstklassiges Verzeichnis; Claude Code substituiert sogar `${CLAUDE_SKILL_DIR}` in `allowed-tools`, damit ein gebündeltes Skript ohne Prompt läuft).
**Trotzdem nicht übernehmen:** unsere ausführbaren Helfer leben in `templates/repo/scripts/` und `hooks/`, werden von Gates aufgerufen und sind von `gate_write_scope`/Hashing erfasst. Ein zweites Executable neben der SKILL wäre ein Skript, das die Gates nicht kennen. Übernehmen: die **Regel** („`--help`, Quelle nicht lesen") für unser bestehendes `scripts/quality.py`.

**(4) Prosa statt MUSS-Wand.**
`skill-creator`: „Try to explain to the model **why** things are important in lieu of heavy-handed musty MUSTs." Unsere SKILLs sind dicht an fett/VERSALIEN-Imperativen. Ich führe das als Beobachtung, nicht als Empfehlung: unsere Dichte existiert, *weil* Regeln ignoriert wurden, und die SYNTHESE-Kopfregel lautet selbst „bloated rule files get ignored". Wo es zählt, machen wir es bereits nach ihrer Methode — „form controls do NOT inherit fonts by default — **a real run shipped a wrong-font button because of this**" ist Anthropics Stil in unserer Datei.

**(5) `allowed-tools` / `disallowed-tools` / `context: fork` — kennen, aber nicht darauf bauen.**
`disallowed-tools` könnte theoretisch `AskUserQuestion` aus jedem Spezialisten entfernen — heute eine Prosaregel („you do NOT talk to the user yourself"). Zwei Gründe dagegen: (a) das Feld ist Claude-Code-spezifisch, in der Agent-Skills-Spec steht nur `allowed-tools` und dort als *experimental* — der Codex-Mirror bekäme nichts, und II.4 verlangt beweisbare Provider-Parität; (b) Doku: „The restriction clears when you send your next message" — eine Pro-Turn-Gewährung ist keine Pro-Subagent-Garantie. Das wäre exakt ein Schutz, der nur als erzwungen *liest*.

**(6) Der Eval-Loop aus `skill-creator`** (With-Skill- vs. Baseline-Subagentläufe, Assertions, `benchmark.json`, Analyst-Pass) ist die einzige publizierte Methode, die die Frage „hat diese SKILL-Änderung das Verhalten überhaupt verändert?" beantwortet — genau die Frage, die die Paritätsmatrix für eine entfernte *Prosa*regel nicht beantworten kann. Besonders das Konzept **„assertions that always pass regardless of skill (non-discriminating)"** ist unser D2-Defekt („ein Test, der nicht rot werden kann"), formuliert für Prompts statt für Code. Vor der Phase-3-Kürzung einmal lesen; die Infrastruktur (Subagent-Fanout, Viewer, Workspace-Baum) nicht adoptieren.

---

## 4. Lizenz — und was sie erlaubt

- **Kein Repository-Root-LICENSE.** `gh api repos/anthropics/skills/license` → HTTP 404. Lizenzierung erfolgt **pro Skill-Ordner**.
- **`skills/frontend-design/LICENSE.txt` = Apache License 2.0**, Volltext, endend mit „END OF TERMS AND CONDITIONS" (10 174 B; ohne Anhang, ohne genannten Rechteinhaber *in* der Datei). Ebenso Apache-2.0 (11 345 B, mit Anhang): `algorithmic-art`, `brand-guidelines`, `canvas-design`, `claude-api`, `internal-comms`, `mcp-builder`, `skill-creator`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`, `webapp-testing`.
  **Erlaubt:** Nutzung, Modifikation, Weiterverbreitung — auch in unseren Kits, die per Scaffold in fremde Repos kopiert werden (das *ist* Weiterverbreitung, nicht bloß Eigennutzung). **Pflichten §4:** Lizenzkopie mitgeben, geänderte Dateien als geändert kennzeichnen, bestehende Attribution/NOTICE erhalten (in den Skill-Ordnern liegt **kein** NOTICE; das Root-`THIRD_PARTY_NOTICES.md` betrifft deren eigene Abhängigkeiten, nicht uns). Patentgewährung §3 inklusive, **kein Copyleft** — unser eigener Text bleibt unter unseren Bedingungen.
  → *Praxisregel:* Ideen (die Klischee-Feststellung, die UX-Writing-Handwerksregeln) lösen keine Pflicht aus; alles über eine Wendung hinaus wörtlich → eine Attributionszeile (`anthropics/skills`, Apache-2.0, „modified") in einem `NOTICES.md` des Kits. Kostet nichts und entspricht der Ehrlichkeitsregel des Harness.
- **`skills/docx|pdf|pptx|xlsx/LICENSE.txt` = proprietär**, und ausdrücklich: „users may not: — Extract these materials from the Services or retain copies of these materials outside the Services — Reproduce or copy these materials … — **Create derivative works based on these materials** — Distribute, sublicense, or transfer …". **Nicht adoptierbar, nicht kopierbar, auch nicht paraphrasiert in ein ausgeliefertes Kit.**
- **`skills/doc-coauthoring/` — keine LICENSE.txt, kein `license:`-Frontmatter.** Bei fehlendem Root-LICENSE ist das per Default „all rights reserved". Nach der Vorgabe dieses Auftrags („an unlicensed GitHub file is not adoptable by default"): **nicht adoptierbar.** Bemerkenswert, weil ausgerechnet dessen Inhalt (Context Gathering → Refinement → Reader Testing) auf unseren PM abbildet.
- **Selbsteinordnung des Herausgebers**, die alles begrenzt (README): „**These skills are provided for demonstration and educational purposes only.** … These skills are meant to illustrate patterns and possibilities." Das ist die Aussage der Autoren selbst, dass es sich nicht um produktive Regeldateien handelt.

---

## 5. Verdikt pro Rolle

**`product-designer` — ADAPTIEREN, ~12 Zeilen, ausschließlich als Inhalt für zwei bereits beschlossene SYNTHESE-Punkte.**
Nehmen: Klischee-Kalibrierung (füllt B1s „Anti-Referenzen"), Brief-gewinnt-Vorrang, UX-Writing (füllt B5s Texttabelle und B4s Leer-/Fehlerzustand). Nicht nehmen: „planning in your thinking", „screenshots if your environment supports it", „quality floor without announcing it". Begründung: unsere Phase-0/1/2/3-Kette, das gerenderte Preview und der eingefrorene Per-View-Vertrag sind strikt stärker; die Anthropic-Datei liefert Vokabular genau an den zwei Stellen, wo die SYNTHESE ein Loch identifiziert und keinen Text hat. Wegen Budget: Sperrliste + Vorrangregel in den Körper, Texttabellen-Detail nach `references/ui-copy.md` (gedeckt durch das B5-Mini-Gate).

**`frontend-developer` — ADAPTIEREN, 2 Zeilen.**
CSS-Spezifitätsfalle (`.section` vs. `.cta` heben Padding/Margin auf) und die Anti-Slop-Zeile aus `web-artifacts-builder` (kein Purple-Gradient, keine uniformen Radien, kein Inter). Beide sind benannte, reproduzierbare Defekte im Genre unserer Font-Inherit-Zeile; die Inter-/Radius-Hälfte ist zudem gate-fähig unter B3. Aus `webapp-testing` die Black-Box-Regel für `scripts/quality.py` — nicht das Skript.

**`backend-developer` — IGNORIEREN. Nichts adoptierenswert.**
Das Repo hat keine Backend-Rollendatei. `mcp-builder` ist die einzige benachbarte Datei und ist Domäneninhalt für ein Projekt, das einen MCP-Server baut, keine Rollenregel. Das ist die Stelle, an der die SYNTHESE recht hat und das Ökosystem schweigt: für A1/A2 (`api_ref` + RFC 9457) gibt es keinen publizierten Skill zum Abschreiben — die Quellen sind OAS 3.1 und der RFC selbst, beide bereits benannt.

**`software-architect` — IGNORIEREN. Nichts adoptierenswert.**
Kein Architektur-Skill im Repo. (`mcp-builder` wäre allenfalls eine `references/`-Datei *innerhalb eines Projekts*, nie eine Rollenregel.)

**`quality-engineer` — ADAPTIEREN, 3 Zeilen, plus `skill-creator` einmal lesen.**
Aus `webapp-testing`: `wait_for_load_state('networkidle')` vor jeder DOM-Inspektion (benannte Flake-Quelle, die unser C2-Keyboard-Pfad treffen wird) und die Black-Box-Skriptregel. Aus `skill-creator`: das Konzept **„non-discriminating assertion"** — eine Assertion, die mit und ohne Skill besteht — als ein Satz im Assertions-/Flake-Abschnitt; das ist D2 für Prompts statt für Code. Die Eval-Infrastruktur nicht adoptieren.

**`project-manager` — INHALTLICH IGNORIEREN, EINE KONVENTION ÜBERNEHMEN.**
`doc-coauthoring` ist der einzige inhaltlich passende Kandidat und **unlizenziert** → raus. `internal-comms` ist lizenziert, aber 40 Zeilen Routing über Anthropic-interne Comms-Formate; übernehmenswert ist das **Router-Muster** (Körper = Router, Detail in `examples/*.md`) — und das ist die `references/`-Konvention aus §3, keine PM-Regel. Praktische Relevanz: `project-manager/SKILL.md` hat **220 Zeilen** und muss auf 150; das Router-Muster ist der Weg dorthin, ohne Regeln zu löschen, die die Paritätsmatrix danach verbuchen müsste.

**Rollenübergreifend, der eigentliche Ertrag dieser Recherche:** Die `references/`-Aufteilung samt der Gate/kein-Gate-Regel dafür, was dorthin wandern darf, gehört in die Phase-II.11/3-Checkliste — sie verändert, was „entfernte Regel" in der Paritätsmatrix bedeutet, und sie kostet null Infrastruktur, weil `scaffold_team.ps1` Skill-Ordner bereits rekursiv kopiert.

**Was nicht überlebt, in einem Satz:** `frontend-design` unterstellt einen Agenten, der mit dem User spricht, sich Notizen in seinem eigenen Gedächtnis macht und selbst baut, was er entworfen hat. In V2 spricht die Designerin nicht mit dem User (der PM tut es), darf nur `staging/<task-id>/` schreiben, und II.5 verbietet Projektzustand im Agent-Memory ausdrücklich. Der *Prozess* der Datei überlebt nur halbiert; ihre *Sätze* überleben gut. Deshalb lautet das Verdikt: Sätze adoptieren, Prozess nicht.

**Relevante lokale Pfade:** `c:\Offline Repos\AgentAndSkills\team-kits\dev-team\skills\product-designer\SKILL.md` (150 Z.), `...\frontend-developer\SKILL.md` (59 Z.), `...\quality-engineer\SKILL.md` (146 Z.), `...\project-manager\SKILL.md` (220 Z. — über Budget), `c:\Offline Repos\AgentAndSkills\docs\research\2026-07-27-SYNTHESE.md` (B1/B4/B5/B6, §3 „was nicht zu tun ist"), `c:\Offline Repos\AgentAndSkills\docs\HARNESS_V2_SPEC.md` §II.5 (Zeilen 485–515) und §II.11/3 (Zeilen 777–781), `c:\Offline Repos\AgentAndSkills\team-kits\scaffold_team.ps1` Zeile 480–489 (rekursive Skill-Kopie).