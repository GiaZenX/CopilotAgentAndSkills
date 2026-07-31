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

Offen: ob das Diagramm **generiert** wird (aus dem Zustand, damit es nie veraltet) oder **gepflegt**
(von Hand, dafür freier in der Darstellung). Ein generiertes Bild ist ehrlich, ein gepflegtes ist
lesbarer. Die Erfahrung aus diesem Umbau spricht für generiert: jede handgepflegte Zweitfassung
eines Zustands ist hier veraltet, sobald jemand nicht hinsieht.

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
