# Nach V2: gewünschte Erweiterungen (Stand 2026-07-27)

Erfasst nach dem Umbau auf V2, **nicht** Teil der Stufen II.11/0–5. Reihenfolge ist Wunsch, nicht
Beschluss. Jeder Punkt braucht vor der Umsetzung eine eigene Entscheidung; hier steht, was gewollt
ist und was daran offen ist.

## 1. Skills der Rollen gegen anerkannte Standards härten

Anlass: Frontends sehen „KI-generiert und lieblos" aus. Das ist am UI messbar und beim Backend und
der Architektur vermutlich genauso wahr, nur schwerer zu sehen. Die Antwort ist nicht mehr Prozess,
sondern **externe Qualitätsanker**, an denen eine Rolle sich prüfen lassen muss.

Betroffen: `product-designer`, `frontend-developer`, `software-architect`, `backend-developer`,
`quality-engineer`, `project-manager` (dev-team), analog die Pendants in research/office.

Recherche läuft (2026-07-27, ein Agent je Rolle). Vorbefund aus einer Codex-Recherche, **die den
V1-Stand analysiert hat** — ihre Dateipfade (`system_requirements.yaml`, `design.yaml`,
`architecture.yaml`) existieren seit dem Lockstep nicht mehr; die genannten Standards gelten
unabhängig davon:

- Design/Frontend: WCAG 2.2, WAI-ARIA Authoring Practices, Nielsen-Heuristiken, Atomic Design,
  Design-Tokens mit Semantik statt Hex-Werten, Storybook als Komponentenvertrag, Testing-Library-
  Queries (Rolle/Label statt Implementierungsdetail), Playwright für kritische Flüsse, Core Web
  Vitals als Akzeptanzkriterium, Loading/Empty/Error als Pflicht-Zustandsmatrix je View.
- Backend/Architektur: OpenAPI-first, Contract-Tests (Pact), Clean Architecture/SOLID als
  Leitplanke, Threat Modeling + OWASP ASVS, OpenTelemetry ab Servicegrenze, Testpyramide statt
  Unit-only, Migrations-/Rollback-Disziplin.
- Betrieb/Steuerung: Branch Protection, CODEOWNERS, CodeQL, Dependency Review, SBOM/SLSA, SLOs mit
  Fehlerbudget, DORA-Metriken.
- Research: FAIR-Prinzipien, Datenversionierung, Reproduzierbarkeitspfade.

Offen: welche davon als **Regel** (INV-Item, Gate) und welche als **Anleitung** (SKILL) landen. Die
Trennlinie ist die aus der Verfassung: was mechanisch prüfbar ist, wird ein Gate; alles andere ist
Anleitung und darf nicht so tun, als wäre es erzwungen.

### 1a. Führung und Rangfolge — vom User nachgereicht (2026-07-27)

Zwei Anforderungen, die der Recherchekatalog NICHT abdeckt und die getrennt zu behandeln sind:

> „Es muss immer so designt sein, dass der Nutzer geführt wird und die wichtigsten Dinge zuerst
> ersichtlich sind."

Die Recherche liefert Anti-Slop (B1/B2/B5/B6) und Vollständigkeit (B4-Zustandsmatrix,
B7-Layoutkriterien) — also *dass nichts fehlt und nichts nach Standardausgabe aussieht*. Sie sagt
nichts darüber, **was zuerst kommt**. Das ist Komposition, nicht Konformität, und es ist die
Anforderung, die der User als Einziger beurteilen kann.

Vorschlag zur Umsetzung, im selben Muster wie der Rest:

- **SKILL, nicht Gate, für die Rangfolge selbst.** „Ist das Wichtigste zuerst sichtbar" ist Urteil.
  Ein Präsenz-Gate darauf wäre die Sorte Prüfung, deren Bestehen nichts aussagt.
- **GATE für das, was Rangfolge nachweisbar macht:** je View genau EIN primäres Ziel, als
  `data-primary-action` im eingefrorenen Vertrag ausgezeichnet. Fehlschlag beschreibbar: „View X
  deklariert null oder zwei primäre Aktionen." Damit ist „geführt" keine Meinung mehr, sondern
  eine Aussage, die der Entwurf trifft und der Build einhalten muss.
- **SKILL-Zeile mit Verfahren, nicht mit Adjektiv:** die Designerin benennt je View in einem Satz,
  was der Nutzer hier tun soll und woran er es zuerst sieht. Ein Entwurf, der diesen Satz nicht
  hergibt, hat keine Rangfolge — das ist der Selbsttest, analog zur Klischee-Kalibrierung.
- **In die heuristische Evaluation (B9) aufnehmen** — die Nielsen-Heuristiken decken Sichtbarkeit
  des Systemzustands und Wiedererkennung statt Erinnern ab, aber nicht „eine Sache pro Ansicht".

Offen bleibt bewusst: ob die Rangfolge in den WFR (Wireframe, vor der Gestaltung) gehört statt in
die DSN. Sachlich gehört sie dorthin — Rangfolge ist eine Struktur-, keine Stilentscheidung.

### 1b. Claude Design — nicht einbetten, aber anschlussfähig bleiben (2026-07-27)

`claude.ai/design` (Anthropic Labs, April 2026, Beta seit Juni) ist ein gehostetes Produkt: Repo und
Designdateien rein, Designsystem und Prototypen raus, iteriert über eine Leinwand mit kontextuellen
Reglern. **Nicht einbettbar** — die einzige Schnittstelle ist ein gehosteter MCP-Server mit
interaktivem Login, die Synchronisation ist bidirektional (zweite Quelle der Wahrheit neben dem
eingefrorenen Vertrag), und der Mehrwert liegt in Interaktivität, die ein Subagent nicht nutzt.

**Was wir stattdessen tun: das Bündel-FORMAT übernehmen, für null Aufwand.** Sein Übergabe-Bündel
ist strukturell unser Vertrag — `design.html` (eigenständig, CSS/JS inline), `screenshots/` (ein
Bild je Zustand), `design-notes.md` (Zielstack, Konventionen). Wenn die Designer-Rolle in
`staging/<task-id>/` genau dieses Tripel erzeugt, bleibt der Ablauf offline UND ein von Hand
exportiertes echtes Bündel lässt sich ohne Umbau einlegen.

Vor der Festschreibung als Vertragsschema: **einmal ein echtes Bündel exportieren und die
Dateinamen verifizieren.** Die Zusammensetzung stammt bislang aus Sekundärquellen.

Inhaltlich bleibt es beim Apache-2.0-Skill `anthropics/skills` → `frontend-design` (~12 Zeilen:
Klischee-Kalibrierung mit Hex-Werten, Selbsttest-Verfahren, UI-Text-Abschnitt). Das Produkt liefert
keinen lizenzfrei verwendbaren Text.

## 2. Board- und Backlog-Ansichten

Der V2-Zustand ist erstmals die richtige Datengrundlage dafür: ein Vorgang = eine Datei, typisiert,
mit Statusautomat, und Abgeschlossenes verlässt den aktiven Kontext.

Gewünscht:

- **Kanban-Board** über die aktiven Vorgänge. Abgeschlossenes ausblenden ist bereits geschenkt —
  terminale Items liegen im Archiv, nicht in `*/active/`.
- **Karten zeigen nur den Titel**, aufklappbar für die Beschreibung.
- **Backlog-Ansicht** mit Gliederung, zwei Sichten:
  - *Produktebene* — PR/FR in Kundensprache,
  - *Systemebene* — SR/TSK, gegliedert nach Bereich.
- **Timeline** mit Fortschritt und Zielen.

Zwei Dinge fehlen dafür im Zustandsmodell, beide sind Entscheidungen:

1. **Die Gliederungsebene über dem Requirement** („Frontend" → „Buttons" → Requirement → Tasks).
   Jira nennt das Epic/Komponente, Azure DevOps Area Path. Empfehlung: ein **Feld** (`area`,
   mehrstufig als Pfad) an PR/SR/TSK, kein neuer Item-Typ — ein neuer Typ zöge einen
   Statusautomaten, Pflichtfelder und Freigabewege nach sich, die eine reine Gliederung nicht
   braucht.
2. **Termine für die Timeline.** V2 hat Meilensteine bewusst abgeschafft, weil `progress.yaml` sie
   doppelt führte. Eine Timeline braucht sie zurück — dann aber als eigener Vorgangstyp (MST) mit
   Datum und Zielbezug, nicht als Feld in einer Sammeldatei. Das ist die Entscheidung, die vor der
   Umsetzung fallen muss.

Technisch: die Ansichten gehören nach `generated/` (regenerierbar, nicht committet), gespeist aus
`generated/index.yaml`. Der Dashboard-Generator existiert bereits als Anknüpfungspunkt.

## 3. Der Plan als Bild, nicht nur als Text

Gewünscht: die Umsetzungsschritte zusätzlich als **draw.io-Diagramm** auf einer Flughöhe ohne
Fachjargon — man soll sehen, welche Schritte nötig sind und wo man steht. Dazu eine **Mindmap**, in
der sich schnell etwas ergänzen oder verschieben lässt.

Passt in die vorhandene Werkzeugkette: ARC- und WFR-Artefakte sind bereits `.drawio.svg`, das
Format ist also schon Teil des Zustandsmodells und wird bereits versioniert.

~~Offen: ob das Diagramm **generiert** wird oder **gepflegt**.~~ **Beantwortet durch
`docs/research/2026-07-27-plan-als-diagramm.md`: generiert.** Der übliche Einwand („generiert sieht
schlecht aus") heisst technisch „ein Programm kann keinen Graphen layouten" — das stimmt, die
mxGraph-Layoutalgorithmen leben im Editor, nicht in einer Python-Bibliothek. **Ein Umsetzungsplan ist
aber kein Graph, den man layouten muss.** Er ist ein Raster: Spalten sind Stufen, Zeilen sind
Vorgänge, Koordinaten sind eine Multiplikation. Damit fällt der einzige echte Nachteil weg. Ein
`.drawio.svg` ist ein gültiges SVG mit dem `<mxfile>`-XML im `content`-Attribut, derselbe
Layoutdurchgang kann also beide Hälften ausgeben — reines Python, kein Chromium, keine JVM. Mermaid
und PlantUML sind genau daran gescheitert: sie zögen eine fremde Laufzeit in einen Hook-Pfad, der
heute mit nichts als Python auskommt.

**Heutiger Stand, gemessen (2026-07-27):** die Werkzeugkette aus Spec II.6a existiert **als Zusage,
nicht als Datei** — `git ls-files | grep drawio` liefert null Treffer, es gibt kein Vorlagendiagramm
und kein `.vscode/extensions.json`-Template. Die einzige maschinelle Prüfung ist ein `ET.parse()` in
`kernel/staging.py`, während das Feld daneben `render_check: True` heisst. Das behauptet mehr, als es
prüft — dieselbe Klasse, die dieser Umbau an sechs anderen Stellen gefunden hat.

### 3a. Nachtrag des Users (2026-08-03): der Zweck, und wo er der Ablage widerspricht

> „Weil so fallen schneller Unstimmigkeiten oder Missverständnisse auf als mit einer reinen
> Masterplan-MD-Datei."

Das ist ein **schärferer Zweck** als „sehen, wo man steht", und er entscheidet zwei Dinge, die bisher
offen waren:

**Erstens den Adressaten.** Ein Bild, das `SR-0004 → TSK-0011 (blocked by APR-0002)` zeigt, findet
keine Missverständnisse — es setzt voraus, dass der Leser die Typen kennt. Ein Bild, das „Anmeldung
funktioniert, bevor irgendetwas anderes gebaut wird" zeigt, findet sie. Die Flughöhe aus dem Absatz
oben ist damit keine Stilfrage, sondern die Funktionsbedingung: **wer den Jargon braucht, um das Bild
zu lesen, kann damit den Plan nicht mehr prüfen.**

**Zweitens die Ablage — und hier steht der Wunsch gegen die bisherige Empfehlung.** Der User will
Masterplan **und** Diagramm immer lokal im jeweiligen Repo. Die Recherche legt das Bild nach
`generated/` und committet es ausdrücklich **nicht** (Spec II.2: Ausgabe, kein Zustand — und genau
dadurch kann es nie veralten). Beides zusammen geht nur mit einer Entscheidung:

- **regeneriert bei jedem Zustandswechsel** — dann ist es immer aktuell, aber ein frischer Clone ist
  erst nach dem ersten Lauf bebildert;
- **mitcommittet mit Frischeprüfung** — dann ist es sofort da, kann aber veralten, und es braucht ein
  Gate, das die Abweichung meldet (dasselbe Muster wie die Delivery-Freshness aus II.12/R6).

**Empfehlung: mitcommittet mit Frischeprüfung**, weil der Zweck es verlangt. Ein Bild, das
Missverständnisse finden soll, muss jemand ansehen können, der das Repo gerade erst geöffnet und noch
nichts ausgeführt hat. Ein `generated/`-Artefakt ist für den Fortschrittsblick richtig und für den
Verständnisblick zu spät.

## 4. Effort-Stufen pro Rolle statt pro Modell (2026-07-31, User)

Vorschlag des Users: **alle Subagenten auf Opus**, und nur am Effort drehen. Modelltier ändert die
Fähigkeit, Effort die Gründlichkeit — ein Regler ist einfacher zu begründen als zwei.

Die Stufe sollte an **Unumkehrbarkeit** hängen, nicht an Dienstalter. Eine Entscheidung, die alles
Nachgelagerte einschränkt (Datenmodell, Architektur, der Plan), kostet bei einem Fehlgriff einen
Neubau; eine Implementierung innerhalb eines festen Scopes mit einem Test als Abnahmekriterium ist
prüfbar, und eine billigere Stufe plus Prüfung ist dort die bessere Ökonomie als eine teure Stufe
plus Hoffnung.

Daraus:

- **PM/Orchestrator, Architekt, Designer: `max`**, solange Plan, Architektur und Erstdesign stehen.
- **Danach Architekt und Orchestrator auf `xhigh`.** Wichtig: der Auslöser sollte **aus dem Zustand
  abgeleitet** sein, nicht aus der Zeit — der Harness kennt ihn bereits: sobald die scope-Freigabe
  geprägt und die Architektur-Items eingefroren bzw. die SRs akzeptiert sind, ist die Arbeit des
  Architekten inkrementell. Und eine `CR`, die die Architektur berührt, hebt ihn für diese CR
  zurück auf `max` — sonst ist die Stufe eine Einbahnstrasse und der späte Umbau bekommt die
  billige Stufe.
- **Frontend/Backend/DevOps: `low`–`medium`** ist vertretbar — aber nur unter der Bedingung im
  nächsten Punkt.
- **QA NICHT billig.** QA ist das, was die billigen Stufen erst tragfähig macht. Beleg aus dem
  V2-Umbau selbst: der Prüfer auf hoher Stufe fand in JEDER Runde, was der Umsetzer übersehen
  hatte, und zweimal fand er Tests, die gar nicht scheitern konnten. Wer den Prüfer verbilligt,
  verliert das Netz, mit dem er den Umsetzer verbilligt hat.

**Was das wirklich kostet:** Effort steht heute statisch in der Agentendefinition
(`.claude/agents/*.md`-Frontmatter). Eine zustandsabhängige Stufe heisst, dass der **Dispatcher sie
beim Spawn wählt** — das ist neue Mechanik im Kernel, nicht eine Konfigurationszeile. Das ist der
eigentliche Arbeitsposten dieses Punktes.

## 5. Finanz-Vorlagen für das Office-Kit (2026-07-31, User)

Vorschlag: Vorlagen für **Bilanz, EÜR, Ledger**, weil Finanzen über Unternehmen hinweg nahezu
gleich sind — Produkte, Shop-Verwaltung und dergleichen dagegen spezifisch und Sache des
Office-Managers. Die Grenze ist richtig gezogen.

Präzisierung: der **Code** ist bereits generisch — `scripts/ledger_add.py`, `euer_report.py`,
`einvoice_extract.py` liegen im Kit. Neu erfunden wird jedes Mal das **Datenmodell**: der
Kontenrahmen (SKR03/SKR04), die Zuordnung Konto → EÜR-Zeile, die Gliederung der Bilanz. Die Vorlage
sollte also der Kontenrahmen plus die Abbildung sein, nicht ein weiteres Skript.

Zwei Bedingungen, sonst wird die Vorlage selbst zur Falschbehauptung:

- **Jahresversioniert.** Formulare und Zuordnungen ändern sich jährlich; eine Vorlage ohne Jahr ist
  ab dem nächsten Stichtag still falsch.
- **Rechtsraum benannt.** Eine Vorlage, die stillschweigend Deutschland annimmt, behauptet etwas,
  das sie nicht trägt — dieselbe Hausregel wie im Code.

**Nachtrag des Users (2026-07-31): gemeint ist vor allem die ANSICHT** — ein HTML-Dashboard, das
EÜR, Bilanz und Ledger darstellt. Das ist der fehlende Teil, nicht die Rechnung: `euer_report.py`
produziert die Zahlen bereits, es fehlt die Sicht darauf. Anknüpfungspunkt ist derselbe wie bei den
Board-Ansichten in Abschnitt 2 — `scripts/generate_dashboard.py` plus die HTML-Vorlage existieren,
gespeist würde die Finanzsicht aus den Ledger-CSVs statt aus `generated/index.yaml`.

Dabei gilt dieselbe Regel wie für die Board-Sichten, und im Finanzkontext ist sie strenger: die
Ansicht gehört nach `generated/`, **regenerierbar und nicht committet**. Eine committete Bilanz ist
eine zweite Wahrheit neben dem Ledger, und das Ledger ist der Beleg. Dazu eine Bedingung aus der
Erfahrung dieses Umbaus: die Ansicht muss **ihre Quelle und ihren Stichtag nennen**, sonst liest
jemand eine veraltete Zahl als aktuelle — dasselbe „abgeleitete Zahl ohne Ableitung", das im
Plandokument gefunden wurde, nur in einem Kontext, in dem Irrtümer Geld kosten.

Ergänzungsvorschlag zur generischen Seite: **Belegablage und Aufbewahrung** (GoBD) ist genauso
wenig unternehmensspezifisch wie die Finanzstruktur und hat mit `filing_plan.yaml` bereits einen
Ort im Kit.

## 6. Mehrere Spezialisten derselben Rolle parallel (2026-07-31, User)

**Heutiger Stand, gemessen:** verschiedene Rollen parallel ja, **dieselbe Rolle parallel nein.**
`kernel/dispatch.py` verweigert bei zwei wartenden Leases derselben Rolle mit `AmbiguousBinding`:
die Plattform gibt `SubagentStart` keinen Schlüssel, um die Kinder auseinanderzuhalten, und ein
Fehlgriff liesse einen Spezialisten unter fremdem `allowed_scope` laufen. Fail-closed statt Raten —
richtig, aber es ist eine Grenze, keine Absicht.

**Wünschenswert ist es klar:** drei unabhängige Frontend-Tasks parallel ist der Normalfall, und die
Lease-Mechanik (exklusiver Claim, TTL, Rückfall auf READY) trägt Parallelität bereits.

**Der Ansatz ist benennbar:** die Lease trägt eine **Nonce**, und die reist im
`HARNESS_DISPATCH`-Header im Prompt des Kindes. Bindet die Auflösung über die Nonce statt über den
Rollennamen, fällt die Grenze — vorausgesetzt, das Kind kann seine Nonce vor dem ersten
gescopeten Write nachweisen. Das ist die Messung, die vor der Umsetzung fällig ist (Spike S3 hat
`SubagentStart.agent_id == Kind-PreToolUse.agent_id` bereits belegt; offen ist der Weg von der
Nonce zur `agent_id`).

## 7. Ein dritter Evidence-Ausgang: `blocked` (2026-08-01, aus der Paritätsmatrix Zeile 99)

**Heutiger Stand, gemessen:** `EVIDENCE_RESULTS` (`team-kits/kernel/backlog_types.py`) kennt genau
`pass` und `fail`, und die Begründung daneben ist die richtige — ein Gate kann ein
„inconclusive" nicht auswerten, und ein Teillauf ist keine Merge-Evidenz. Der Fall, den das nicht
abdeckt, ist ein anderer: ein e2e-Lauf, der **umgebungsbedingt nicht stattgefunden** hat (kein
Browser, kein Gerät, kein Netz). Die Rolle muss ihn heute als `fail` buchen, und danach steht im
Store ein rotes Ergebnis, dem niemand mehr ansieht, ob wirklich etwas rot war oder ob nichts lief.
Genau das ist die Auskunft, die beim Lesen des Stores gebraucht wird.

**Wunsch:** `EVIDENCE_RESULTS += "blocked"`, und `gate_git` verweigert einen Merge, dessen neueste
`test`-Evidence `blocked` ist — dieselbe Behandlung wie `fail` an der Schranke, aber eine andere
Aussage im Store. Der Unterschied zu „inconclusive" ist, dass die Schranke nicht raten muss:
`blocked` schliesst, wie `fail` schliesst; nur der Grund ist ein anderer und bleibt lesbar.

**Aufwand: M.** Ein Wert im Frozenset, das Feldkontrakt-Schema, `gate_git`s Lesart der neuesten
Evidence je `kind`, die Rollen-SKILLs, die sagen, wann welcher Ausgang zu buchen ist, und die
Doktor-/Report-Sicht, die heute zweiwertig zählt.

**Der Satz, der dazugehört:** ob der zugrundeliegende Lauf wirklich übersprungen hat, bleibt
ausserhalb der Reichweite des Harness. Niemand misst nach, ob der Browser wirklich fehlte. Das Feld
macht aus einer Ehrlichkeitspflicht einen Zustand, keine Messung — es verbessert, was ein späterer
Leser erfährt, und es fügt der Frage „ist das wahr?" nichts hinzu. Wer es einbaut, muss diesen Satz
mit einbauen, sonst liest der nächste `blocked` als geprüfte Tatsache.

## 8. Ein Projekt vollautonom von Anfang bis Ende (2026-08-03, User)

> „Wie bekommen wir es hin, dass ein neues Projekt vollautonom von Anfang bis Ende durchläuft — mit
> perfekter und getesteter UI, sauberem und sicherem Backend? Einen gereviewten Plan erstellen mit
> allen Wenn und Aber, alles so zerrupfen, dass am Ende ein Produktplan steht, und diesen vollautonom
> vom PM durchziehen lassen."

Das ist kein Einzelwunsch, sondern der Zweck, auf den die anderen sieben Punkte zulaufen. Deshalb
steht hier nicht „was man bauen müsste", sondern **woran heute gemessen fehlt**.

### Der Massstab existiert bereits, er hiess nur anders

Beim ersten Durchlauf des Lebenszyklus am Stück (2026-08-02, Testbed) musste ein Mensch **dreimal**
aus dem Harness ausbrechen, um bis zu einem Merge zu kommen: den Masterplan von Hand schreiben, eine
leere `requirements.txt` anlegen, `archive` raten. Ein autonomer Lauf hat diese Auswege nicht — er
folgt der Anweisung, die nicht hilft, und wiederholt sich.

**Damit ist Autonomiereife prüfbar statt gefühlt: die Zahl der Stellen, an denen zuletzt ein Mensch
improvisieren musste.** Sie ist endlich, sie wird bei jedem Durchlauf neu gemessen, und sie muss null
werden. Jede Sackgasse ist ein Autonomie-Stopper, unabhängig davon, wie klein sie aussieht.

### Was nach heutigem Stand fehlt

**Die Schreibsperre auf den Planungsdateien.** `masterplan.md`, `project_config.yaml` und
`filing_plan.yaml` haben keinen Schreiber (Wurzel 1 + Stufe II.11/4). Ein autonomer PM kann seinen
eigenen Plan nicht füllen. Härteste Blockade von allen.

**Anweisungen, die das Gate nicht aufheben.** Items sind nach dem Anlegen unveränderlich, also ist
jede Abhilfe der Form „korrigiere Feld X" strukturell unausführbar. Ein Mensch rät `archive`; ein
autonomer Lauf rät nicht.

**Die Freigaben — und das ist die Designentscheidung, nicht ein Defekt.** Das Harness prägt einen
Token NUR aus einer echten Antwort auf eine echte Frage. Das ist der Kern seiner Sicherheit und
zugleich genau das, was „vollautonom" ausschliesst. Die Frage lautet nicht „wie schalten wir das
ab", sondern **welche Freigabeklassen ein autonomer Richter erteilen darf und welche am Menschen
bleiben.** Scope und Delivery sind vermutlich verschieden zu behandeln; ein Push wahrscheinlich nie.
Ohne diese Entscheidung ist der Rest dieses Abschnitts akademisch.

**Das UI-Review mit Screenshots existiert nicht.** Die Design-Pipeline (Wireframe → Ambition →
Richtungen → Mockups → Fidelity) steht in der Verfassung ausdrücklich als **Prosa ohne Gate**. Kein
Mechanismus rendert, vergleicht oder urteilt. Der grösste echte Neubau: Headless-Render, Bild-Diff
gegen den eingefrorenen Mockup, und ein Richter über die Abweichung. II.12/R5 nennt einen
UI-Inventar-Snapshot — der fängt entfernte Elemente, nicht Aussehen.

**Das Backend-Testen hat einen Boden, keinen Beweis.** `quality.py` fährt Ruff, Mypy, Pytest, Bandit,
pip-audit, Dateibudget. Das schliesst Schlamperei aus, nicht Fehler. Für „sauber und sicher" fehlen
ein e2e-Lauf, der als solcher zählt (heute ist ein übersprungener Lauf nicht darstellbar — Punkt 7),
und eine Abdeckungsaussage über die *richtigen* Zeilen.

**Und die Planungsstufe selbst.** Das Kit kennt Masterplan → PR → SR → TSK. Was fehlt, ist die Stufe
davor: ein **gereviewter Plan**, der die kritischen Stellen benennt, bevor irgendetwas zerlegt wird.
Genau das, was für diesen V2-Umbau von Hand entstand — Paritätsmatrix, Löschlizenzen, benannte
Grenzen — nur als Produktplan. Punkt 3a gehört dazu: der Plan muss als Bild lesbar sein, sonst prüft
ihn niemand.

### Die Reihenfolge, die sich daraus ergibt

1. Sackgassen schliessen (Wurzel 1, Stufe II.11/4) — ohne das ist jeder weitere Punkt wirkungslos.
2. Die Freigabefrage entscheiden — sie bestimmt, was „autonom" überhaupt heissen darf.
3. Die Planungsstufe bauen, samt Bild (Punkt 3/3a).
4. UI-Review und e2e-Beweis (Punkt 1, Punkt 7).
5. Erst dann ein Durchlauf, dessen Ergebnis etwas über das Produkt aussagt statt über das Harness.
