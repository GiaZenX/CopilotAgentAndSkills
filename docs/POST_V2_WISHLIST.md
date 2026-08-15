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

### 1c. Was als ANLEITUNG eingebaut wurde — und welche Gates dabei bewusst nicht entstanden (2026-08-03)

Die Trennlinie oben ist in dieser Runde **einseitig** aufgelöst worden: die Standards sind als
Verfahren in die betroffenen Spezialisten-SKILLs gewandert, **kein einziges neues Gate**. Der Grund
ist Erfahrung und keine Aufwandsschätzung — ein Gate, das im selben Paket entsteht wie der Text, den
es prüfen soll, wird gegen den Text gebaut statt gegen die Regel.

**Wo die Anleitung gelandet ist** (alle ausserhalb des Lead-Pakets, die Ratsche in
`tools/lead_package_sizes.json` blieb also unberührt): unter
`team-kits/dev-team/skills/` die Rollen `product-designer`, `frontend-developer`,
`backend-developer`, `software-architect` und `quality-engineer`, je ein Abschnitt
„Standards … — guidance, and NOTHING below is enforced"; dazu die zwei
Textrollen des Office-Kits (`product-editor`, `shop-curator`), die die Recherche selbst als
einschlägig für den Klartext-Grundsatz vermerkt hatte. Jede Zeile ist als **Selbsttest am eigenen
Ergebnis** formuliert, nicht als Standardname.

**Eine Ehrlichkeitsschuld ist dabei mitbezahlt worden** (X1 der Synthese, gemessen):
`quality-engineer/SKILL.md` behauptete „coverage ≥ threshold globally AND per source area".
`templates/repo/scripts/quality.py` baut in `check_python` genau **einen** `--cov=`-Sockel und
**ein** `--cov-fail-under=`; `gate_test_coverage` prüft je Bereich nur, ob es dort überhaupt eine
Testdatei gibt. Der Satz ist korrigiert und durch
`tools/test_role_contracts.py::test_the_qa_coverage_claim_matches_what_quality_py_measures` gepinnt.
Im selben Satz stand `component_coverage` — ein Name, den im ganzen Baum nichts erzeugt; er ist raus.

**Die mechanisch prüfbaren Hälften, eine Zeile je Kandidat, NICHT gebaut.** Die Nummern sind die der
Synthese (`docs/research/2026-07-27-SYNTHESE.md`, §1), wo Fehlerbild und Aufwand ausformuliert
stehen; hier steht nur, was die neue SKILL-Zeile offen lässt:

- **C1/C2/C3** — axe-Lauf, Tastaturpfad und `prefers-reduced-motion`/`:focus-visible`-Präsenz im
  bereits gebooteten `browser_smoke()`. Die QA-Zeile sagt heute „ein grüner Automatenlauf ist ein
  Boden"; den Boden selbst gibt es nicht. Bedingung für den Bau: der Gate-Text darf nie
  „barrierefrei" melden, sondern nur „automatisch prüfbarer Anteil bestanden".
- **B2/B3** — Farbliterale ausserhalb genau einer Token-Datei, auf der gestagten DSN und im Build.
  Die Frontend-Zeile lässt es beim `grep` auf den eigenen Diff; ein Walker (`_frontend_sources()`)
  existiert bereits.
- **B2b** — Theme-Parität: die Tokennamensmengen unter `:root` und `[data-theme="dark"]` müssen
  gleich sein. Fängt den halbfertigen Dark Mode, den keine SKILL-Zeile fängt.
- **B4** — Präsenz der Zustandsvarianten je `data-view`. Die Designer-Zeile verlangt sie; dass sie da
  sind, ist zählbar, ob sie gut sind, nicht.
- **B5** — Platzhalter in sichtbaren Textknoten. **Warnung an den Erbauer:** die Recherche schlägt
  eine Wortliste vor, und eine Wortliste ist genau die Aufzählung, an der dieses Repo wiederholt
  bezahlt hat. Die SKILL-Zeile ist deshalb als Eigenschaft formuliert („ein sichtbarer String, der
  unverändert in ein ANDERES Produkt passt"). Wer das Gate baut, muss diese Eigenschaft
  mechanisieren oder die Liste als das benennen, was sie ist.
- **B6** — die Richtungen müssen sich auf mindestens einer deklarierten Achse unterscheiden.
- **D1** — `INV.check.ref` im State-Validator auflösen. **Der Multiplikator:** danach sind F4, F10
  und die INP-/SLO-Zeilen, die jetzt in drei SKILLs stehen, ohne neuen Gate-Code prüfbar. Solange er
  fehlt, sagen backend- und QA-SKILL ausdrücklich, dass ein fehlender Test bis zur QA unsichtbar
  bleibt.
- **D2** — assertionsfreie Tests per AST-Walk (nicht per Textsuche). Die QA-Zeile sagt heute „nichts
  in der Pipeline sucht danach".
- **D3** — Skip-/xfail-Buchhaltung aus `--junitxml`. Die QA-Zeile verlangt, die Zahl zu nennen; sie
  zu erzwingen wäre der Gate.
- **D4/D5** — der stille Frontend-Coverage-Fallback ohne `--coverage`, und Diff-Coverage gegen die
  Merge-Base statt eines höheren globalen Prozentsatzes. Nach der Korrektur oben ist D4 die einzige
  Stelle, an der die Pipeline heute noch grün meldet, was sie nicht gemessen hat.
- **A1/A2/A3/A4** — OpenAPI-Existenz und -Bindung an `SR.contract`, `application/problem+json` auf
  den deklarierten Fehlerantworten, Breaking-Change gegen die Merge-Base, `contract.kind` als
  geschlossenes Vokabular. Die Backend-Zeile prüft heute nur das Urteil („eine Route, die du
  aufrufen und im Dokument nicht finden kannst, ist Drift").
- **F9** — der Cross-Tenant-Negativtest je Operation mit Pfadparameter und `security`. Das ist die
  Fehlerklasse, die SAST strukturell nicht findet, und sie ist aus einem OpenAPI-Dokument
  vollständig aufzählbar — also erst nach A1.
- **F1/F2/F3/F6/F7** — `options_considered` ≥ 2 an richtungsgebenden Decisions, `arc_companion.scope`
  als C4-Vokabular plus beschriftete Kanten, `gate_threat_model` als Klon von
  `gate_packaging_decision`, `ARC.derives_from` nicht auf `SUPERSEDED`, SBOM bei verteiltem Artefakt.
  Von diesen ist F3 der einzige, dessen Fehlen die Architektur-SKILL heute ausdrücklich benennt.
- **F12/D8** — Migrationsform (Modelländerung ohne nummerierte Migration; `DROP`/`RENAME` ohne
  CR/DEC) und mindestens ein Test gegen die echte Engine bei deklariertem DB-Stack. D8 kostet Docker
  und muss dann **fehlschlagen** statt zu überspringen — sonst widerspricht er der QA-Regel, die er
  stützen soll.

**Was bewusst NICHT angefasst wurde, mit Grund:**

- **Die Lead-SKILLs und die Verfassungen.** Kein Standard aus der Recherche zwingt dorthin: die
  PM-Zeilen der Synthese (G3-Deutung, H1/H2, I3) hängen an Board, Meilensteinen und Mindmap — also an
  Abschnitt 2/3 dieser Liste, nicht an einem Standard. Damit blieb die Grössen-Ratsche unberührt und
  es war kein Nachziehen der Sektionspins nötig.
- **`research-team`.** Die Wunschliste nennt oben FAIR-Prinzipien, Datenversionierung und
  Reproduzierbarkeitspfade — **`docs/research/` deckt sie nicht ab.** Die zwölf Dateien dort sind
  sechs Rollenberichte (alle dev), vier Themenberichte und zwei Synthesen; keiner behandelt eine
  Research-Rolle. Etwas für `researcher`/`data-analyst`/`methodologist` zu schreiben hiesse hier
  erfinden, und die Anweisung war, es von dort zu nehmen. **Offen und benannt: eine
  Research-Rollenrecherche fehlt.**
- **Ein Präsenz-Gate auf „heuristische Evaluation durchgeführt".** Ausdrücklich nicht — sein Bestehen
  sagt nichts, und das verletzt die Hausregel in der zweiten Richtung.

**Zwei Baumbefunde derselben Runde, gemessen:**

- **Fünf der sechs Rollenberichte liegen unter dem falschen Rollennamen.** Gemessen an der ersten
  Zeile jeder Datei: `…-product-designer.md` analysiert `frontend-developer`,
  `…-frontend-developer.md` den `software-architect`, `…-software-architect.md` den
  `quality-engineer`, `…-quality-engineer.md` den `project-manager`, `…-project-manager.md` die
  `product-designer`. Nur `…-backend-developer.md` passt zu seinem Namen. Nicht umbenannt — die
  Dateien sind Belege, und ein `git mv` an Belegen ist eine Entscheidung des Users; wer sie liest,
  liest die Kopfzeile.
- **Spezialisten-SKILLs stehen unter KEINEM Sektionspin.** `test_shortening_net._pinned_files`
  bewacht Verfassung, Lead-Agentendatei, Lead-SKILL und `hooks/ENFORCEMENT.md` — die
  Spezialisten-SKILLs sind ausdrücklich draussen, und derselbe Modul-Docstring hält fest, dass ein
  gelöschter Satz aus `skills/backend-developer/SKILL.md` bei grüner Suite gemessen wurde. Der neue
  Anleitungstext ist damit **löschbar, ohne dass etwas rot wird**. `tools/test_role_contracts.py`
  pinnt nur den Ausgabekontrakt und die Coverage-Aussage, nicht die Standardabschnitte. Kandidat,
  bewusst hier statt gebaut: den Pin auf die Spezialisten-SKILLs ausdehnen — das ist eine
  Entscheidung über Kürzungsfreiheit, keine Textarbeit.

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

## 9. Der Masterplan braucht einen Zustand (2026-08-03, User)

**Das Modell des Users, in seinen Worten:** der Masterplan (MD **und** Diagramm, Punkt 3/3a) wird
zwischen ihm und dem Lead so lange durchgesprochen, bis alles Offene geklärt ist — „welche API wird
nötig sein", „wie soll das Design aussehen", „woher bekomme ich die Finanzberichte", „woher die
Kurse", „wie soll das Komitee aufgebaut sein". Erst dann die Freigabe, dann die Umsetzung, dann
autonom.

Seine Begründung ist die wichtigste Zeile dieses Abschnitts: **„Vieles fällt normalerweise erst
während der Umsetzung auf, deshalb muss man das penibel reviewen."**

**Heutiger Stand, gemessen:** der Masterplan trägt **keine Freigabe und keinen Zustand**. Die
scope-Freigabe hängt am `PR`, gehasht sind `problem`, `goal`, `acceptance_criteria`, `out_of_scope`,
`invariants`, `design_refs`. `product/masterplan.md` liegt daneben als lesbares Gesamtbild — ohne
Statusautomat, ohne Freigabe, und (Punkt 11/L1) ohne Schreiber. Er ist genau das Artefakt, das der
User als zentral beschreibt, und mechanisch ist er Prosa, die nichts bewacht.

**Das Harness behandelt späte Erkenntnis heute bestrafend statt vorbeugend:** wer nach der Freigabe
ein gehashtes Feld ändert, verliert sie, das Item fällt auf DRAFT zurück und braucht eine `CR`. Das
ist richtig und teuer. Was fehlt, ist die andere Hälfte.

**Der baubare Teil — eine Bedingung, kein Urteil:**

> Eine scope-Freigabe wird nicht angeboten, solange der Plan offene Fragen führt, die weder
> beantwortet noch ausdrücklich vertagt sind.

Der Masterplan hat die Sektion „Risiken & offene Fragen" bereits. Das Gate liest einen **Zustand**
(„steht dort noch etwas Unbeantwortetes?"), es urteilt nicht über Planqualität — dieselbe Trennlinie
wie überall im Kit. Es erzwingt genau die Runde, die der User beschreibt, **vor** der Freigabe statt
in der Umsetzung.

**Der Schnitt zwischen Mensch und Autonomie, der sich daraus ergibt:**

| Freigabe | Übergang | wer |
|---|---|---|
| `scope` | DRAFT → APPROVED | **Mensch** — die unumkehrbare Entscheidung, und der Ort des Reviews |
| `delivery` | APPROVED → IN_DELIVERY | **autonom** — durch den freigegebenen Scope begrenzt, jedes Gate prüft dagegen |
| `acceptance` | DELIVERED → ACCEPTED | **Mensch** — Urteil über das Ergebnis, blockiert aber nichts |
| `push` | (Token, an Remote+Branch+HEAD gebunden) | **Mensch** — Userentscheid 2026-08-03, ausnahmslos |

Ausdrücklich festgehalten, damit es nicht neu verhandelt wird: **ein Commit braucht keine Freigabe,
ein Push immer** (Userentscheid 2026-08-03).

## 10. Die Freigabe programmatisch erteilen — und was das verschiebt (2026-08-03)

**Gemessen:** `AskUserQuestion` existiert im `-p`-Modus nicht. 30 Werkzeuge in der Init-Zeile, keines
davon; `--tools "Read,AskUserQuestion"` liefert `['Read']` — das Werkzeug wird still fallengelassen.
Auch `--input-format stream-json` ändert daran nichts. Da `gate_approval` **nur** aus einer echten
Antwort auf eine echte `AskUserQuestion` prägt, ist die Freigabekette headless unerreichbar: kein PR
verlässt DRAFT, kein Merge, kein Push.

**Recherchiert (2026-08-03), drei Wege:**

- **PTY-Emulation** (ConPTY/winpty/`script`/`expect`) startet eine interaktive Sitzung, aber ein
  Programm müsste dann eine Terminal-Oberfläche per Bildschirmabgriff bedienen. Kein Vertrag,
  jederzeit brüchig. **Nicht gangbar.**
- **`--remote-control`** registriert sich bei der Anthropic-API und pollt nach Arbeit; braucht einen
  vollen claude.ai-Login (API-Keys ausdrücklich nicht unterstützt), und die Gegenseite ist
  claude.ai im Browser oder die Mobile-App — **ein Mensch auf einem anderen Gerät.** Verschiebt das
  Problem, löst es nicht.
- **Das Claude Agent SDK ist der dokumentierte Weg.** `AskUserQuestion` löst dort denselben
  `canUseTool`-Rückruf aus wie eine Werkzeugfreigabe; das Programm antwortet mit
  `{behavior: "allow", updatedInput: {questions, answers}}`. Kein TTY nötig. Dokumentierte Grenze:
  **in Subagenten, die über das Agent-Werkzeug gespawnt werden, ist `AskUserQuestion` nicht
  verfügbar** — nur in der Hauptsitzung.

**Was das für die Sicherheit heisst, und das ist der Kern:** heute gilt *ein Token existiert ⟹ ein
Mensch hat geantwortet*, weil `AskUserQuestion` nur einem Menschen etwas zeigen kann. Über das SDK
wird daraus *ein Token existiert ⟹ das einbettende Programm hat entschieden*. **Das SDK löst die
Vertrauensfrage nicht, es verlagert sie** — vom Provider in unseren Code.

Damit hat Punkt 8 zum ersten Mal einen konkreten Bauplatz (`canUseTool`) und die Sicherheitsfrage
eine scharfe Fassung: nicht „soll das Harness autonom laufen", sondern **wer darf der Richter sein,
und woran erkennt man hinterher, dass er es war.** Ein Token, den ein Programm geprägt hat, muss
sich von einem unterscheiden lassen, den ein Mensch geprägt hat — sonst ist die Provenienz, auf der
`doctor` seine `hook_trust`-Aussage aufbaut, nur noch eine Behauptung.

**Ungeklärt und eine Messung wert:** ob der `PermissionRequest`-Hook mit `updatedInput.answers` für
`AskUserQuestion` dasselbe kann, ohne die CLI zu verlassen. Das wäre der billigere Weg. Die Doku
zeigt das Feld generisch („any field from the tool's input schema"), nennt aber `AskUserQuestion`
nicht als Beispiel.

## 11. Löcherliste — gemessen, benannt, nicht geschlossen (Stand 2026-08-03)

Jede Zeile ist eine **Messung**, kein Verdacht. Sie stehen hier, weil sie den Umbau nicht
blockieren, aber jede von ihnen kostet jemanden später Zeit — und weil eine Aufgabenliste mit der
Sitzung stirbt, in der sie entstand.

### L1 — Drei Planungsdateien haben keinen Schreiber (härteste Autonomie-Blockade)

`product/masterplan.md`, `project_config.yaml`, `filing_plan.yaml`. `gate_write_scope` verweigert
jeden Werkzeug-Write unter `project_memory/`, die Shell-Route ebenso, und der Kernel hat für diese
Dateien keinen Schreiber. Die Verweigerung sagt das seit `876d237` **ehrlich** („no route from
inside this session — report the gap"), statt auf `validate` zu verweisen, das im selben Zustand
0 Fehler meldet.

Nicht geschlossen, weil die Sperre **Verfassungsrecht in allen drei Kits** ist und durch einen
bestehenden Test gepinnt. Die Reparatur gehört nach Stufe II.11/4, wo der Einstieg ohnehin auf V2
umgestellt wird. Für office ist es existenziell: `filing_plan.yaml` wird mit `rules: []`
ausgeliefert, also ist die Kernfunktion des Kits ab Installation tot — im Kit dokumentiert, aber
lebendig.

### L2 — Items sind unveränderlich, also ist jede „korrigiere Feld X"-Abhilfe unausführbar

Es gibt kein Kommando, das ein Feld eines angelegten Items ändert. `archive` ist der einzige Ausweg
und stand bis `876d237` in keiner Meldung. Betroffen sind heute noch: `premise_rechecks` (die
Validator-Warnung nennt ein Feld, das an einem existierenden PR nicht mehr schreibbar ist), und
`acceptance_criteria` an einem bereits freigegebenen `PROC`.

### L3 — Ein direkt gestartetes Gate verseucht sein eigenes Bündel

`python .claude/hooks/gate_dispatch.py` ohne `-B` legt `__pycache__` an, **bevor** derselbe Prozess
den Bundle-Hash bildet — es verweigert seinen eigenen Spawn, schon im ersten Lauf (gemessen).
`_gate.py` trägt `sys.dont_write_bytecode`, aber ein direkt gestartetes Gate führt `_gate.py` nie
aus. Der saubere Fix ist eine Zeile in `GATE_PREAMBLE` und damit ~15 Hookdateien × 3 Kits plus die
Preamble-Pins. Die Klasse dahinter ist grösser: **jeder** Python-Prozess auf dem Host, der
`.claude/kernel` ohne `-B` importiert, entwaffnet die Delegation eines Projekts.

### L4 — Schreibverben innerhalb einer Programmsprache

`sed -n 'w datei'` schreibt aus dem Programmtext heraus und ist kein Shell-Operator; `gate_write_scope`
fängt Umleitungs*operatoren*, nicht die Schreibverben fremder Sprachen. Dasselbe gilt für `awk`,
`jq`, `perl -e`, `python -c`. **Bewusst nicht geschlossen:** eine Liste dieser Verben wäre genau die
Aufzählung im Gewand einer Regel, gegen die dieses Repo gebaut ist — sie stimmt bis zum sechsten
Werkzeug. Ein benanntes Loch ist ehrlicher.

### L5 — Der Workspace-Trust verwirft die `allow`-Hälfte, und das Fenster ist Reibung, kein Loch

**Korrigiert am 2026-08-03; die vorige Fassung dieses Eintrags war falsch.** Sie behauptete, der
**ganze** `permissions`-Block werde verworfen und ein frisches Projekt laufe ohne die Sperren —
und schrieb „gemessen" daneben. Gemessen ist das Gegenteil (2026-08-03, claude.exe 2.1.220,
headless, ein **nie getrautes** Scratch-Projekt mit einer kit-förmigen `settings.json`): die
Sitzung meldet die `Ignoring`-Zeile und verweigert im selben Lauf `Read` auf `server.key` („File is
in a directory that is denied by your permission settings.") und den Lead-Spawn („Agent type
'project-manager' has been denied by permission rule 'Agent(project-manager)' from
projectSettings.") — die Meldung nennt Regel und Quelle. Die Gegenprobe im selben Lauf: eine
gewöhnliche `notes.txt` daneben wird gelesen, die Sperre ist also die Regel und keine Pauschale.
Das Fenster macht eine Sitzung damit **restriktiver**, nicht durchlässiger.

Was bleibt, ist das messbare Restproblem: `Ignoring N permissions.allow entries … this workspace
has not been trusted` überspringt genau die `allow`-Hälfte — **5 Einträge** in dev und research,
**2** in office (`team-kits/*/settings/settings.json`). `deny` bleibt vollständig in Kraft. Die
Folge ist **Reibung**: der Lead muss `git`, `python` und `pytest` einzeln bestätigen lassen, bis
der Workspace getraut ist. Und die Neustart-Anweisung des Scaffolds (`scaffold_team.sh` /
`scaffold_team.ps1`, die Schlusszeilen) erwähnt den Trust-Dialog mit keinem Wort — das stimmt
weiterhin und ist der eigentliche Kandidat: ein Satz mehr in derselben Meldung.

**Ausdrücklich nicht der Ausweg: die Regeln auf User-Ebene nachziehen.** Das funktioniert gemessen,
löst aber ein Problem, das es nicht gibt — die `deny`-Hälfte gilt ja bereits —, und es bezahlt mit
einer Regel, die dann in **jedem** fremden Repo des Nutzers gilt und die der Installer bei jedem
Update wieder einmergt (`user/claude/settings.json`, unioniert von `install.sh`/`install.ps1`).

### L6 — Rollenmemory ist vorgeschrieben und gesperrt

Die Verfassung verlangt „durable craft learnings"; `gate_write_scope` verweigert
`.claude/agent-memory/<rolle>/…`, sobald `submit-result` gelaufen ist — und der Spezialist schreibt
sein Memory typischerweise danach. Die zweite Verweigerung nennt ausserdem den falschen Grund
(„Hooks and settings are maintained by the scaffold"), obwohl `agent-memory` weder Zustand noch
Enforcement-Schicht ist.

### L7 — Eine Lease aus einer abgestürzten Sitzung kostet die volle TTL

`reconcile_unstarted_dispatches` greift nur, wenn der Spawn **nie startete**. Ein gestartetes,
dann abgebrochenes Kind hält seine Lease 900 s; `sweep-leases` sagt ehrlich, wie lange
(`still leased: TSK-0001 (527 s left)`), aber es gibt kein Kommando, das sie zurückgibt. Gemessen:
924 s Stillstand. Kandidat: `sweep-leases --force <TSK>` mit Journalzeile, oder eine Bindung an die
Session-ID.

### L8 — Die Push-Freigabe invalidiert sich durch ihren eigenen Datensatz

Gemessen: Mint für HEAD `6c2d5d1e` → der Lead committet den Freigabe-Datensatz → HEAD ist
`34ae1673` → `no live user approval for pushing 34ae1673`. Kostet **jedes Mal** eine zusätzliche
menschliche Freigaberunde. Kandidaten: ein Satz in §8 („die Freigabe zuletzt holen"), oder
`project_memory/approvals/**` in `.gitignore`.

### L9 — Kleinere, je einzeilig

- **`capture` kann seinen Body nicht aus `staging/` lesen** — die dokumentierte Heredoc-Form
  kollidiert mit dem Gate; der Ausweg führt Harness-Eingaben ins OS-Temp-Verzeichnis.
- **Ein BOM in `agents/<lead>.md` hebt die `agent:`-Bindung lautlos auf** (`agent_type` wird `null`),
  und kein ausgelieferter Check sieht es. PowerShell 5.1 erzeugt das BOM beim Zurückschreiben.
- **`scaffold_team.sh` schreibt das Label mit** — `kit_version` in `kit_state.json` lautet
  `"version: 2026.08.03-1"`. Wird nirgends ausgewertet, ist aber ein falsch geparster Wert im
  Vertrauensdatensatz.
- **Ein Skill, den zwei Agenten nennen, kollabiert auf ein Paar** — nur einer der beiden wird auf den
  Abrufweg geprüft. Heute nennt jedes Skill genau ein Agent, der Fall ist eine Änderung entfernt.
- **`CR.target_pr` / `BUG.related_pr` prüfen Existenz, nicht Wurzelzugehörigkeit** — ein `BUG` darf
  ein `HYP` nennen, und `_root_of` gibt dieses `HYP` als Wurzel zurück. Zwei Codestellen halten
  „related_pr == root" als Absicht fest; der Kernel erzwingt es nicht, und `validate` schweigt.
- **`withdraw-approval` fehlt** — eine geöffnete Freigabefrage lässt sich nicht zurückziehen. Gebaut,
  gemessen und wieder entfernt, weil **jedes** neue Unterkommando Ergänzungen in sechs ausgelieferten
  Texten verlangt.
- **Ein Gate, das stdin selbst leert, nimmt dem nächsten der Kette die Nutzlast** — fail-closed
  (`{}` → Verweigerung), gehalten von einem AST-Test über jeden ausgelieferten Hook.
- **Unter der Grössen-Ratsche prüft nichts, ob verschobener Text laden musste** — der Rekord schützt
  Bytes, nicht Semantik. Eine ableitbare Regel dafür ist nicht in Sicht.
- **`tar --remove-files` leert das Archiv, ohne ein Kopierer-Verb zu sein** (Rest von BUG-0002).
  `tar --remove-files -cf /tmp/a.tar archive/fin` archiviert die Quelle und **löscht sie danach** —
  eine Verschiebung aus dem Archiv, gemessen **rc 0** am `guard_fs_tripwire`-Prozess. `_filing` liest
  Kopie/Verschiebung an der Aufrufkonvention (Ziel als zweites bzw. letztes Token); `tar` hat keine,
  steht darum in keiner `DEST_IS_*`-Familie und erreicht `moved_out_of_the_archive` nie.
  `SOURCE_DELETING_FLAGS` greift erst, NACHDEM `_move` eine Familie erkannt hat — für tar gibt es
  keine. Nicht geschlossen: ein Fangen hiesse einen zweiten, nicht-kopierenden Löschpfad zu bauen
  (tar mit quell-löschendem Schalter als Löschung der genannten Operanden), was über den
  Bug-Auftrag hinausgeht. Begrenzung bis dahin: Löschen unter `archive/` per `rm`/`del` fängt die
  Delete-Regel bereits; nur der tar-interne Löschweg ist offen.

### L10 — Was ohne einen Provider unprüfbar bleibt

- Ob ein **Subagent** sein SKILL geladen bekommt. Für den Sitzungs-Agenten ist gemessen, dass er es
  **nicht** bekommt; der Spawn-Weg ist zweimal an einem Kind gescheitert, das den Auftrag ablehnte,
  bevor es antwortete. In `tools/provider_observations.json` als offen geführt.
- Ob **Codex** einen `@`-Import in `AGENTS.md` expandiert.
- Ob `AskUserQuestion` im **interaktiven** Modus genau den Payload liefert, den `gate_approval`
  erwartet. Die Gates prägen korrekt, wenn der Payload kommt (viermal gemessen mit rekonstruiertem
  Payload) — die Form des echten Werkzeugaufrufs ist ungemessen.

### L11 — Laufzeit: nicht der Zustand, sondern die Prozessanzahl

`gate_memory_complete` wächst **nicht** mit der Projektgrösse (323 ms bei 8 Items, 331 ms bei 32).
Was der Nutzer spürt, kommt woanders her: ein Bash-Werkzeugaufruf startet **acht** Python-Prozesse
für die Shell-Gates. In einem gemessenen Durchlauf waren das 149 Aufrufe × 8 = 1 192 Interpreterstarts
allein dafür; der Median stieg von 4,72 s auf 6,30 s. Der Hebel ist nicht der Zustands-Walk, sondern
die Startkosten — dieselbe Kettenform wie beim Spawn-Pfad wäre der naheliegende Kandidat.

### L12 — Eine kit-spezifische Datei kann den Inhalt eines fremden Kits bekommen, und nichts merkt es

Vorgeführt am 2026-08-03: ein Umsetzer hat `session_status.py` blind von dev über office und
research gespiegelt und dabei **119 bzw. 19 Zeilen kit-eigenen Inhalt gelöscht**. Aufgefallen ist es
an `git diff --stat`, **nicht an einem Test**.

Der Grund ist strukturell: `session_status.py` steht in `KIT_SPECIFIC_HOOKS`, also greift
`test_shared_kit_files_identical` per Konstruktion nicht — und das ist richtig, denn die Datei SOLL
sich unterscheiden. Was fehlt, ist die Gegenrichtung: **nichts behauptet, dass eine als
kit-spezifisch erklärte Datei ihren kit-spezifischen Inhalt behält.** Die Ausnahme von der
Spiegelregel ist heute eine Erlaubnis ohne Gegenstück.

Der Kandidat ist ableitbar statt getippt: eine Datei in `KIT_SPECIFIC_HOOKS` muss zwischen je zwei
Kits **verschieden** sein — sonst ist ihr Eintrag entweder falsch oder jemand hat sie gerade
plattgespiegelt. Das ist dieselbe Form wie die zweite Schleife in `_assert_mirrored`, die eine
Ausnahme verwirft, die niemand braucht — nur andersherum.

Nebenbefund derselben Runde: Pythons `write_text` dreht Zeilenenden auf CRLF, während
`.gitattributes` `*.py text eol=lf` sagt. Fünf Dateien waren betroffen und sind normalisiert;
**vorbestehend** trägt `guard_yaml_valid.py` in allen drei Kits CRLF, obwohl git sie unverändert
meldet.

### Die Einträge des V1-Imports (L13–L18, Stand 2026-08-05)

Sie kamen mit der Migrationsrunde dazu (`TSK-0016`) und tragen deshalb, was Abschnitt 12 von jedem
Eintrag verlangt: den **Mechanismus**, die **gemessene Kette**, ein **Urteil** und — solange der
Eintrag offen ist — **was stattdessen begrenzt**. Jeder von ihnen hat einen Stolperdraht in
`tools/test_migrate.py`, der den heutigen Stand misst und rot wird, sobald sich das Verhalten
bewegt; `test_every_hole_a_test_measures_is_carried_by_the_hole_list` hält Eintrag und Messung
zusammen. **Keiner der sechs ist in den drei Feldkopien erreichbar** — das ist je nachgemessen und
der Grund, warum sie Einträge sind und keine Blocker.

### L13 — Ein Typ, den der Feldvertrag kennt und die Zuordnungstabelle nicht, hat keinen Ausgang

**Mechanismus:** `migrate._is_backlog_type` ist die Vereinigung zweier Karten — `REQUIRED_FIELDS`
(dieser Kernel legt Items dieses Typs an) und `v1_types()` (die V1-Statustabelle kennt den Typ).
Ein Datensatz, dessen Typ nur in der ERSTEN steht, ist eine Harness-Lücke, und der Trockenlauf sagt
das korrekt. Was er nicht kann, ist einen Weg hindurch anbieten: der Lauf verweigert, solange der
Datensatz steht, und `validate` meldet das Dokument, das ihn hält — beide Abhilfen zeigen
aufeinander.

**Kette (gemessen 2026-08-05, dev-Scaffold außerhalb des Repos, ein Datensatz eines solchen Typs
mit `status`):** `migrate --dry-run` exit 1, `BLOCKED (1) … IS a V2 item type, but spec II.10's
mapping table has no row for it … Remedy: record it with … capture DEC and report it`; im selben
Zustand `validate` → `error … holds 1 V1 backlog record(s) … Remedy: run … migrate --dry-run`.
Welche Typen das heute sind, leitet der Stolperdraht aus den beiden Karten ab, statt sie
abzuschreiben — wächst die Tabelle eine Zeile, schrumpft die Menge mit.

**Urteil: Rest, keine Angriffskette** — aber ein Sackgassenzustand für ein Projekt, dessen V1-Store
einen solchen Datensatz trägt.

**Was stattdessen begrenzt:** der Lauf verweigert (kein stiller Durchlass) und benennt die Lücke
ausdrücklich als Harness- und nicht als Projektlücke. Der Ausweg existiert — den Datensatz vor dem
Lauf aus dem Zustandsverzeichnis nehmen —, steht aber in keiner der beiden Meldungen.

**Stolperdraht:** `test_migrate.test_a_type_the_field_contract_knows_and_the_table_does_not_has_no_way_out`

### L14 — Ein Unter-Mapping kollidiert mit seinem eigenen Elternteil

**Mechanismus:** `scan_document` zählt die Namen, die ein Mapping sich gibt, **pro Objekt**
(`self_named`, nach Objektidentität); `build_plan` zählt die Ansprüche auf eine Id **pro
Schlüssel** (`claimants`). Ein Mapping INNERHALB eines Datensatzes, das dessen Id wiederholt, ist
ein zweites Objekt mit je einem Namen: der Zweig „ein Mapping, zwei Ids" schweigt, und der
Kollisionszweig verweigert beide Einträge — über EINEN V1-Datensatz, mit einer Abhilfe, die von
zwei verschiedenen Datensätzen handelt.

**Kette (gemessen 2026-08-05):** ein `PROC-0001` mit einem `detail:`-Mapping, das `id: PROC-0001`
trägt → zwei Einträge, beide `blocked`, beide mit „appears 2 times in this run, in
procedures.yaml"; `plan_is_executable` False.

**Urteil: Rest, Über-Verweigerung.** Der Lauf schreibt nichts Falsches; er verweigert mit einer
Begründung, die den Leser auf die falsche Fährte setzt.

**Was stattdessen begrenzt:** die Verweigerung selbst ist die sichere Richtung, und der Ausweg
(die Id im Unter-Mapping im V1-File entfernen) ist ausführbar — er steht nur nicht in der Meldung.

**Stolperdraht:** `test_migrate.test_a_sub_mapping_of_a_record_collides_with_its_own_parent`

### L15 — Die Wanderkennung hängt an einem Attributnamen statt an der Eigenschaft, verweigern zu können

**Mechanismus:** `layout._can_refuse` fragt, ob ein Modul `<x>.block(...)` aufruft. Das ist eine
Schreibweise, keine Eigenschaft. Ein registriertes Hook, das den Werkzeugaufruf anders beendet,
gilt als nicht verweigerungsfähig — liest es den Pfad eines Kit-Dokuments, ist dieses Dokument
keine Wand, und ein vollständig aufgegangener Speicher wird nach `legacy/` **verschoben**. Das Gate
liest danach eine abwesende Datei, und was ein fail-closed Gate damit tut, ist nicht die Sache des
Imports.

**Kette (gemessen 2026-08-05):** ein registriertes `PreToolUse`-Hook, das über eine eigene Funktion
mit `sys.exit(2)` verweigert und `project_memory/process_definitions.yaml` zusammensetzt →
`gated_documents` leer → das Dokument steht in `absorbed_documents` und wird verschoben.
Gegenrichtung im selben Lauf: dieselbe Datei mit der erkannten Schreibweise → Wand. Wie breit die
blinde Stelle ist, im selben Lauf über die **registrierten** Hooks der Kits gezählt: dev 10 von 19,
office 9 von 18, research 9 von 17 verweigern in einer Schreibweise, die diese Erkennung nicht
sieht.

**Urteil: offen, heute ohne Kette in den Kits.** Kein ausgeliefertes Hook, das anders verweigert,
liest ein Kit-Dokument: die einzigen Leser von Kit-Dokumenten sind `gate_memory_complete`
(dev/research) bzw. `gate_filing` (office) — beide mit der erkannten Schreibweise — und
`session_status`, das nichts verweigert. Die nächste Hookdatei, die ein Dokument liest, entscheidet.

**Was stattdessen begrenzt:** allein diese Menge — zwei Dokumentleser pro Kit, gemessen, beide
sichtbar. Technisch begrenzt nichts; die Erkennung ist die einzige Instanz zwischen einem Gate und
seiner verschobenen Datei.

**Stolperdraht:** `test_migrate.test_a_hook_that_refuses_without_the_recognised_spelling_is_no_wall`

### L16 — Eine Wand, die V1-Datensätze hält, wird ein Validator-Fehler, den kein Lauf mehr auflöst

**Mechanismus:** eine Wand wird nie nach `legacy/` verschoben (richtig so — ihr Gate läse danach
eine abwesende Datei), und ein Import entfernt einen Datensatz nicht aus seinem V1-File. Eine Wand,
deren Datensätze alle importiert sind, hält sie damit weiter; `validate` meldet sie nach SR-0001 als
Fehler, und kein weiterer Lauf ändert daran etwas.

**Kette (gemessen 2026-08-05):** Wand über `process_definitions.yaml` registriert → Lauf exit 0, 16
Items → `validate`: `error … holds 1 V1 backlog record(s)` (bzw. je nach Fixture mehr) → zweiter
Trockenlauf: `NOTHING TO DO`, exit 0 → dieselbe Fehlermeldung, unverändert.

**Urteil: offen.** Der Fehler ist wahr — dieselbe Sache liegt zweimal im Projekt —, nur hat der Lauf
keinen Weg, ihn aufzulösen.

**Was stattdessen begrenzt:** die Meldung ist ein `error` und blockiert damit Merge und Push, statt
still zu bleiben; auflösbar ist sie heute nur außerhalb der Sitzung (die Datensätze im V1-File von
Hand entfernen, das Dokument bleibt als Wand liegen).

**Stolperdraht:** `test_migrate.test_a_wall_that_holds_v1_records_is_a_finding_no_run_can_clear`

### L17 — Der Abschlusskriterium-Scan liest ein zu großes Dokument nicht mehr (Rest des Fixes)

**Mechanismus:** dieser Eintrag ist der Preis der Obergrenze, die in derselben Runde eingezogen
wurde. `report._check_no_v1_records_outside_the_archive` läuft im blockierenden Merge-Gate mit;
ohne Grenze kostete er ~1,5 s je MB (gemessen: 1 MB 1,42 s · 5 MB 7,42 s · 15 MB 26,73 s · 55 MB
90,79 s), also mehr als die 60 s, nach denen ein `PreToolUse`-Hook getötet wird — und ein getötetes
Hook ist ein Durchlass. Mit der Grenze wird ein Dokument über der Marke **nicht gelesen**: ob es
V1-Datensätze hält, ist danach unbekannt.

**Kette (gemessen 2026-08-05):** ein Kit-Dokument über der Marke mit einem `PROC`-Datensatz darin →
der Parser bekommt es nicht mehr zu sehen, `validate` meldet es als Fehler mit der Wendung
`NOT SEARCHED for V1 backlog records` **in der Mitte** der Meldung (seit der Umrahmung vom
2026-08-07 führt die Ursache, und die Prüfung folgt: „It is N bytes … . It was therefore NOT
SEARCHED for V1 backlog records"); ein Dokument unter der Marke im selben Lauf wird weiterhin
gelesen und sein Datensatz weiterhin gemeldet.

**Korrektur 2026-08-07:** die früher hier notierte Kurve war unter „PyYAML with libyaml" gemessen;
dieser Pfad ruft `yaml.safe_load` und damit den **reinen Python-Loader** (`yaml.SafeLoader`),
obwohl `yaml.__with_libyaml__` True ist. Nachgemessen mit
`report._check_no_v1_records_outside_the_archive` direkt (bester von 3, ein büroartiges
`filing_log.yaml`): 1 MB 1,85 s · 2 MB 2,90 s · 4 MB 6,36 s · 8 MB 18,01 s; die erste, kalte
Lesung jeder Größe liegt Faktor 1,7–2,7 darüber (2,9–4,2 s je MB). Das Gesamtbudget von 8 MB
kostet damit **~18 s warm und ~31 s kalt** — ein Drittel bis die Hälfte der 60 s, die ein
`PreToolUse`-Hook für **alles** hat.

**Feldzahl (gemessen 2026-08-07, dieselbe Auswahl, die der Scan trifft):** `synaipse` hält 20
Kit-Dokumente mit zusammen 5 114 314 B = **63,9 % des Gesamtbudgets**, seine größte Datei
`design.yaml` 1 015 193 B = **50,8 % der Einzelgrenze**; `portfoliomanaigement` liegt bei 12,2 %
bzw. 6,3 %. Die Antwort auf „trifft ein echtes Projekt die Grenze?" lautet damit nicht *nein*,
sondern **noch nicht** — und die Abhilfe („nimm die Datei außerhalb der Sitzung heraus") ist genau
der Griff, den `gate_write_scope` innerhalb der Sitzung verbietet.

**Urteil: GESCHLOSSEN mit benanntem Rest.** Der unbegrenzte Leser ist weg; unbekannt bleibt
unbekannt.

**Was stattdessen begrenzt:** „nicht gelesen" wird als Fehler gemeldet und nicht übergangen — der
Merge bleibt also zu, statt still durchzulassen. Der Preis ist die Gegenrichtung: ein legitimes
großes Geschäftsdokument im Zustandsverzeichnis (ein gewachsenes `filing_log.yaml`) blockiert dann
Merge und Push, bis es außerhalb der Sitzung herausgenommen oder geteilt wird. Die Meldung sagt das.

**Stolperdrähte:** `test_migrate.test_a_document_too_large_to_search_is_reported_as_unsearched_and_not_read`
und `test_migrate.test_the_whole_scan_budget_names_the_documents_it_did_not_reach`

### L18 — Die Wurzelwarnung schweigt für ein Projekt, das schon vorher keines hielt

**Mechanismus:** `migrate.root_item_warnings` spricht, wenn ein Lauf das letzte aktive Wurzelitem
ins Archiv nimmt. Sie ist damit an die **Änderung** geknüpft, nicht an den Zustand, den der Lauf
hinterlässt. Ein Projekt, das vorher keines hielt, hört nichts — obwohl danach dasselbe gilt, was
DEC-0013 als gefährlich benannt hat: das Setup-Phasen-Prädikat antwortet nein, und die fünf Gates,
die es lesen, gelten nicht.

**Kette (gemessen 2026-08-05):** frisches Zustandsverzeichnis ohne Wurzelitem, ein übersetzbarer
`PROC` → `root_items_after` = `{PR: [0, 0], RQ: [0, 0]}` → `root_item_warnings` = `[]`; der
schreibende Lauf druckt dieselbe Stille.

**Urteil: Rest, keine Angriffskette** — die Gates sind in diesem Zustand ohnehin schon inaktiv, der
Lauf schaltet nichts ab. Was fehlt, ist die Ansage.

**Was stattdessen begrenzt:** `doctor` und der Sitzungsbrief melden den Zustand unabhängig vom Lauf;
DEC-0013 macht das frische Wurzelitem zur ersten Aufgabe der ersten Sitzung nach der Migration.

**Stolperdraht:** `test_migrate.test_the_root_warning_is_silent_for_a_project_that_held_no_root_item_before`

### L19 — Ein V1-Speicher außerhalb der Domäne des Suchlaufs wird benannt und blockiert nicht

**Mechanismus:** der SR-0001-Scan durchsucht die YAML-Dokumente des Zustandsverzeichnisses. Was
kein YAML-Dokument ist, im Vorschlagsbereich (`staging/`) oder unter einem gepunkteten Pfad liegt,
wird seit TSK-0020 von beiden Lesern **benannt** (`migrate.search_coverage`,
`report.record_scan_coverage`), aber nicht als Befund geführt — also verweigert kein Gate.

**Kette (gemessen 2026-08-07):** Zustand mit gültigem Wurzel-Item + `project_memory/old_procs.yaml.bak`
mit `PROC-0001` (`status: ACTIVE`) → `validate` druckt `NOT SEARCHED old_procs.yaml.bak: …`,
`gate_memory_complete` auf `git merge` **rc 0**. Dieselbe Datei als `old_procs.yaml`: rc 2.

**Urteil: OFFEN, nicht schließbar ohne einen neuen Fehlklang.** Ein Befund über diese Klasse wäre
in jedem Projekt dauerhaft und unauflösbar: das Forschungs-Kit liefert 27 nicht-YAML-Dateien unter
`project_memory/` aus (`README.md`, `product/masterplan.md`, `reports/assets/**`), Dev und Office je
zwei. Als `error` ein Merge, den kein Projekt je besteht; als `warning` ein Alarm über einen Zustand,
den niemand verlassen kann.

**Die Gegenrichtung ist teurer, und sie ist gemessen (2026-08-08):** der Vorschlagsbereich ist nicht
aus Bequemlichkeit ausgenommen. Ein für `capture` vorbereiteter Item-Body trägt eine Id und einen
`status`, ist also für denselben Erkenner ununterscheidbar von einem V1-Datensatz —
`migrate.scan_document` liest zwei gewöhnliche Vorschläge unter `staging/PR-0001/` als `TSK-0001`
und `TSK-0002`. Würde der Scan dort suchen, verweigerte das Merge-Gate jedem Projekt den Merge,
sobald zwei Vorschläge im Zustandsbaum liegen — für den Normalzustand des Arbeitens.

**Was stattdessen begrenzt:** die Datei ist nicht mehr stumm — `validate` druckt sie pro Datei mit
Grund, `doctor` trägt sie unter `record_scan_coverage`, der Trockenlauf der Migration nennt sie unter
`NOT SEARCHED`. Seit TSK-0023 nennt der Grund **jede** Bedingung, die die Datei draußen hält, samt
der zugehörigen Abhilfe (vorher führte die Abhilfe für eine Nicht-YAML-Datei unter `staging/` auf
eine Datei, die weiterhin unsearched ist). Und der eigentliche SR-0001-Fall (das zurückkopierte
Monolith) trägt seinen V1-Namen und liegt damit *in* der Domäne; unter dieses Loch fällt nur eine
Datei, die jemand zusätzlich umbenannt oder verschoben hat.

**Restfall des Vorlaufs:** eine Datei unter gepunktetem Pfad, die kein YAML-Dokument ist, gilt als
`machinery` — weder durchsucht noch genannt. Das hält `.kernel.lock`, `.audit/hook_events.jsonl` und
ein `.gitkeep` je Item-Verzeichnis aus beiden Berichten; ein dort versteckter V1-Datensatz steht in
keinem.

**Stolperdrähte:** `test_migrate.test_the_dry_run_and_the_validator_answer_the_same_about_every_file`
(letzter Block: rc 0, rot sobald der Merge dafür verweigert),
`test_migrate.test_every_spelling_of_the_proposal_area_gets_one_answer_from_both_readers` (die
Gegenrichtung) und `test_migrate.test_every_file_under_the_state_root_gets_exactly_one_search_verdict`
(der Restfall).

### L20 — Ein V1-Speicher in einem kernel-geschriebenen Bereich steht in keinem Bericht

**Mechanismus:** `migrate.search_coverage` urteilt `kernel` über den **Bereich**, nicht über den
Schreiber: alles unter einem Pfad, den ein Kernel-Bauer nennt, gilt als Schreibung des Kernels und
wird weder durchsucht noch als „nicht durchsucht" genannt. Das ist die zweite stumme Klasse neben
`machinery`, und die weitere von beiden.

**Kette (gemessen 2026-08-08):** Zustand mit gültigem Wurzel-Item, `processes: {PROC-0001: {status:
ACTIVE}}` je einmal in `generated/`, in `archive/PROC/2026/` und in `product/active/` abgelegt →
Deckung `kernel`, `record_scan_coverage` nennt keine der drei, kein V1-Befund. `gate_memory_complete`
auf `git merge`: **rc 0** für `generated/` und `archive/PROC/2026/`; für `product/active/` rc 2 —
aber aus einem anderen Grund, der Item-Validator liest die Datei als Item ohne Pflichtfelder.
Dieselben Bytes eine Ebene höher: rc 2 mit `holds 1 V1 backlog record(s)`.

**Urteil: OFFEN.** Der Ausweg wäre eine Aussage darüber, welche **Namen** ein Kernel-Bauer in einem
Bereich erzeugt (Item-Dateien, `index.yaml`, Freigabe-Ids …) — also eine Tabelle pro Bereich, und
damit genau die Aufzählung, gegen die dieses Repo gebaut ist. `legacy/` müsste ohnehin ausgenommen
bleiben: dort liegen absorbierte V1-Dokumente absichtlich.

**Was stattdessen begrenzt:** in diese Bereiche schreibt kein Werkzeug einer Sitzung —
`gate_write_scope` verweigert jeden Tool-Write unter `project_memory/`, und der Kernel legt dort nur
seine eigenen Dateien ab. Eine Datei kommt dorthin nur über eine Shell außerhalb der Sitzung oder
einen Checkout. Und der Bereich, den ein Item-Validator ohnehin abläuft (die aktiven
Item-Verzeichnisse), verweigert den Merge trotzdem — mit einer Meldung über etwas anderes.

**Stolperdraht:** `test_migrate.test_a_v1_store_inside_a_kernel_written_area_is_in_no_report`

### L21 — Die Prosa-Regel entscheidet Wort-Kovorkommen, nicht Paarung

**Mechanismus:**
`test_migrate.test_no_shipped_text_says_an_import_arrives_at_its_initial_status_full_stop`
fragt drei Wortlisten an einem Satz ab: ein Import-Wort, ein Anfangsstatus-Wort, kein Wort der
anderen Tür. Ob der Satz die Hälfte **behauptet** oder sie **verneint**, sieht keine der drei.

**Kette (gemessen 2026-08-07 an den ausgelieferten Regexen, je eine Probe):**
`Imports arrive at their INITIAL status, never at the mapped one.` — falsch über dieses Harness,
**geht durch**; `A record the table calls unfinished is imported at its initial status.` — wahr und
harmlos, **wird abgelehnt**; `Importierte Items kommen im Anfangsstatus an und tragen keine
Freigabe.` — dieselbe Behauptung auf Deutsch, **geht durch**; `Every imported PROC arrives in DRAFT
and carries no approval.` — dieselbe Behauptung mit **benanntem** Status, **geht durch**. Deckung
über das abgeleitete Korpus: 2704 Sätze in 70 Dokumenten, 56 mit Import-Wort, 2 mit
Anfangsstatus-Wort, **genau einer** wird angesehen.

**Urteil: NICHT SCHLIESSBAR mit dem Instrument.** Die Paarung zu entscheiden ist eine Lesart; ein
Prüfer, der einen richtigen Satz meldet, ist schlechter als keiner — die zweite Probe ist bereits
dieser Fall und ist der Preis der ersten.

**Was stattdessen begrenzt:** der Docstring behauptet die Paarung nicht mehr, sondern nennt alle
vier Proben; und der Test **fällt**, sobald die Zahl der angesehenen Sätze null erreicht — eine
Prüfung, die nichts ansieht, ist kein grünes Licht.

**Stolperdraht:** derselbe Test (die Vakuum-Zusicherung), rot gesehen, indem der eine angesehene
Satz in `README.md` umformuliert wurde.

### L22 — Der Plan-Digest deckt den Plan, nicht das Harness

**Mechanismus:** `migrate.plan_digest` ist über das Plan-Objekt genommen. Eine Kit-Änderung, die den
**Inhalt** des Plans bewegt, invalidiert einen vorgelegten Plan (gemessen: ein zusätzlicher Eintrag
in `backlog_types.OPTIONAL_FIELDS` bewegt den Digest bei byte-identischem `state_fingerprint`,
unveränderten Flaggen und unveränderter Registrierung). Eine Kit-Änderung **unterhalb** des Plans —
wie `execute` schreibt, was der Plan beschreibt — bewegt ihn nicht.

**Kette:** Trockenlauf lesen → Kit-Update, das nur die Schreibhälfte ändert → `--plan <digest>`
läuft durch, weil der Digest stimmt, und schreibt anders, als der gelesene Trockenlauf beschrieb.

**Urteil: OFFEN, nicht blockierend innerhalb einer Sitzung** — die Kette braucht eine
Neuinstallation zwischen den beiden Hälften.

**Was stattdessen begrenzt:** die Verweigerungsmeldung nennt Code und Tabellen jetzt als dritte Art
von Eingabe und schickt an `doctor`, das die `kit_version` berichtet; und die Gegenrichtung ist
gemessen (`test_migrate.test_moving_the_kernels_own_contract_table_alone_moves_the_digest`, zweite
Hälfte): eine Konstante ohne Verdikt bewegt den Digest nicht — der Digest ist also kein
Versionsstempel und darf nicht als einer gelesen werden.

**Stolperdraht:** `test_migrate.test_moving_the_kernels_own_contract_table_alone_moves_the_digest`

### L23 — Zitate außerhalb der II.10-Nachträge prüft nichts

**Mechanismus:**
`test_disposition.test_every_citation_in_the_migration_addenda_carries_the_wording_it_cites`
prüft nur die Nachträge, weil nur dort die Konvention „Zitat in Anführungszeichen, Paraphrase
kursiv" gilt.

**Kette (gezählt 2026-08-07 mit dem Leser derselben Datei):** 35 zitatförmige Spannen in der Spec,
7 in den Nachträgen (alle auflösbar), 28 außerhalb, davon **17 unauflösbar**. Die frühere
Begründung („zitieren die Welt außerhalb dieses Repos") hält für die Mehrzahl und **nicht** für
drei: `Prefer Mermaid over draw.io` (eigenes früheres Kit-Ruling), `je <=150 Zeilen` (eigene frühere
Zeilengrenze), `Derived 1:1 from … v1.11` (Kopfzeile des eigenen V1-Ablageplans) — Artefakte dieses
Repos, die keine Zeile hier mehr trägt.

**Urteil: OFFEN.** Ein Zitat zurückgezogenen Textes liest sich genau wie ein falsch abgeschriebenes;
das zu trennen braucht die Paarung Regel↔Abschnitt, also eine Lesart.

**Was stattdessen begrenzt:** die Konvention gilt in den Nachträgen, dort sind alle sieben Zitate
geprüft, und der Test fällt, wenn die Nachträge fast keine Zitate mehr tragen.

**Stolperdraht:**
`test_disposition.test_every_citation_in_the_migration_addenda_carries_the_wording_it_cites`

### L24 — Die Pfadregel gilt im Kernel-Paket und wird nur dort gelesen

**Mechanismus:** die Regel „ein Verzeichnisname, den ein Bauer besitzt, wird nur in diesem Bauer
zusammengesetzt" ist ein Stolperdraht über `team-kits/kernel/*.py`. Ausgelieferter Code **außerhalb**
des Pakets setzt dieselben Namen von Hand zusammen, weil dort kein `ProjectState` in der Hand liegt.

**Kette (gemessen 2026-08-08, AST-Leser über `team-kits/**/*.py` ohne das Kernel-Paket):** die Zahl
der Stellen steht **nur** im Pin `test_kernel._COMPOSITIONS_OUTSIDE_THE_PACKAGE` und wird hier
absichtlich nicht wiederholt — bis 2026-08-08 stand sie an beiden Orten, und die Prosakopie war die,
die niemand nachzieht. Die Stellen selbst: `hooks/_kernel.py` (`generated`, je Kit dreimal gespiegelt),
`templates/repo/scripts/generate_dashboard.py` (`archive`, `generated`),
`templates/repo/scripts/retro.py` (`generated`, dev und research). Jede davon ist eine zweite
Schreibweise der Antwort eines Bauers: zieht `state.generated_path` um, liest der Bridge-Code
weiter am alten Ort und meldet ein Projekt fälschlich als greenfield.

**Urteil: OFFEN, nicht blockierend** — die Kette braucht eine Umbenennung im Kernel, und der
Bridge-Pfad ist genau der, der ohne Kernel funktionieren muss (`_kernel.state_is_empty` antwortet
auch dann, wenn der Kernel nicht importierbar ist; ihn an einen Bauer zu hängen, verlegt eine
Bootstrap-Antwort auf den Kernel).

**Was stattdessen begrenzt:** die Zahl ist gepinnt, und zwar in **beiden** Richtungen — eine neue
Stelle wird rot, und die letzte verschwundene Stelle wird ebenfalls rot, damit der Eintrag nicht
als toter Text stehen bleibt. Der Docstring der Regel behauptet ihre Reichweite nicht mehr für
allen Code.

**Stolperdraht:** `test_kernel.test_the_path_rule_stops_at_the_kernel_package_and_the_rest_is_counted`

### L25 — Ein Item-Body, der sich selbst nennt, ist von einem V1-Datensatz nicht unterscheidbar

**Mechanismus:** ein V2-Item trägt `id: SR-0001` und einen `status` — genau die Form, an der
`migrate.scan_document` einen V1-Datensatz erkennt. Die beiden sind für den Erkenner dasselbe. Was
die eigenen Items eines Projekts aus dem SR-0001-Scan hält, ist allein ihr **Ort**: kernel-eigene
Bereiche werden pauschal übersprungen (L20), der Vorschlagsbereich ebenfalls (L19). Ein Body, der
woanders landet — eine Kopie, ein von Hand gesichertes Item, ein aus `staging/` hochgezogener
Vorschlag —, wird als V1-Datensatz gelesen.

**Kette (gemessen 2026-08-08):** Zustand mit gültigem Wurzel-Item, Merge rc 0 → zwei Dateien
`project_memory/notes/SR-0001.yaml` und `SR-0002.yaml` mit je `id`, `status: PROPOSED` →
`validate` meldet **zwei** `holds 1 V1 backlog record(s)`, `gate_memory_complete` auf `git merge`
**rc 2**, und innerhalb der Sitzung räumt das niemand weg: `gate_write_scope` verweigert jeden
Tool-Write unter `project_memory/`. Dieselben zwei Bodies unter `staging/PR-0001/`: rc 0.

**Urteil: OFFEN, nicht schließbar mit diesem Erkenner.** „Ist dieses Dokument ein V2-Item oder ein
V1-Datensatz?" ist an der Form nicht entscheidbar; die einzige verfügbare Antwort ist der Ort, und
den nennt die Meldung bereits.

**Was stattdessen begrenzt:** kein Werkzeug einer Sitzung schreibt dorthin, der Kernel legt Items
nur in seine eigenen Bereiche, und der Vorschlagsbereich — der einzige Ort im Zustandsbaum, an dem
eine Rolle solche Bodies wirklich erzeugt — ist genau deshalb aus dem Scan heraus. Die Verweigerung
nennt die Datei, und die Abhilfe („nimm sie außerhalb der Sitzung heraus") ist ausführbar.

**Stolperdraht:** `test_migrate.test_two_item_bodies_outside_the_kernels_own_areas_refuse_every_merge`

### L26 — Der Kopplungstest schließt das Paar nur einseitig, und die Referenz ist eine Schreibweise

**Mechanismus:** `test_migrate.test_every_hole_a_test_measures_is_carried_by_the_hole_list` läuft
über die Menge der Einträge, die ein **Test nennt** (`named`), nie über die Einträge der Liste
(`entries`). Ein Eintrag, den kein Test nennt, wird deshalb von nichts geprüft — weder auf Urteil
noch auf Begrenzung noch darauf, dass sein zitierter Stolperdraht existiert. Zweite Aufzählung im
selben Test: `_HOLE_REFERENCE` ist **eine** Schreibweise (`` `L19` in `docs/POST_V2_WISHLIST.md` ``);
eine Nennung als „getragen von `L19`" ist kein Treffer.

**Kette (gemessen 2026-08-08 im Klon außerhalb des Repos, je eine Probe):** fehlender Eintrag zu
einer Test-Nennung ⇒ **rot**; Zitat auf einen umbenannten Test ⇒ **rot**; Eintrag ohne jede
Test-Nennung (verwaist), Urteil entfernt ⇒ **grün**. Ein verwaister Eintrag ist genau die Hälfte,
für die der Docstring bis heute „BOTH DIRECTIONS" behauptete.

**Urteil: OFFEN, nicht blockierend innerhalb einer Sitzung** — die Wirkung ist ein Eintrag, der als
toter Text stehen bleibt, kein Durchlass an einem Gate. Die Richtung „Test nennt einen Eintrag, den
es nicht gibt" ist die, an der ein Paket auseinanderfällt, und die ist zu.

**Was stattdessen begrenzt:** der Docstring behauptet die zweite Richtung nicht mehr, sondern nennt
sie als Lücke mit dieser Nummer; und die Einträge dieses Pakets sind alle von einem Test genannt,
liegen also in der geprüften Hälfte.

**Stolperdraht:** `test_migrate.test_every_hole_a_test_measures_is_carried_by_the_hole_list`
(die geprüfte Richtung)

### L27 — Der DEC-0021-Stolperdraht definiert „Leser" als zwei Operationen

**Mechanismus:** der Test parst allen ausgelieferten Python-Code und sammelt jede Stelle, die
`IMPORT_MARK` aus einem Mapping **holt** — als Subscript oder als `.get`. Das ist eine Aufzählung
zweier Operationen und keine Eigenschaft; die Marke ist eine Präsenzmarke, und die liest man am
natürlichsten mit `in`.

**Kette (gemessen 2026-08-08, je ein echter Leser in `kernel/report.py` eingesetzt und der Test
gefahren):** `IMPORT_MARK in item` ⇒ **grün**; `item.pop(IMPORT_MARK, None)` ⇒ **grün**; ein
Schlüsselvergleich `if name == IMPORT_MARK` in einer Feldschleife ⇒ **grün**;
`getattr(item, IMPORT_MARK, None)` ⇒ **grün**; nur das Subscript ⇒ rot. DEC-0021 entschied gegen
jeden Leser; vier von fünf Formen kämen unbemerkt hinein.

**Urteil: OFFEN, nicht blockierend** — ein Leser dieser Marke ist kein Durchlass, sondern eine
Entscheidung, die jemand ein zweites Mal treffen müsste. Die Eigenschaft sauber zu fassen („der Name
erscheint in einer Position, die nicht die Store-Seite einer Zuweisung ist") ist machbar und wurde
hier bewusst nicht gebaut: der Test liegt im Prüfwerk, nicht im Produkt.

**Was stattdessen begrenzt:** die **Schreib**seite ist vollständig gepinnt — der Test verlangt
exakt drei Schreibstellen, also wird eine vierte Stelle, die die Marke setzt, sofort rot; und der
Docstring behauptet nicht mehr, jeder morgen hinzugefügte Leser werde rot.

**Stolperdraht:** `test_migrate.test_the_import_mark_says_where_an_item_came_from_and_claims_no_lever`

### L28 — Die `UNLISTABLE`-Zeile entsteht für jeden Walk-Fehler, auch wo nie gesucht würde

**Mechanismus:** `migrate.search_coverage` hängt seinen `onerror`-Sammler an den **ganzen** Walk.
Jeder Fehler wird eine `UNLISTABLE`-Zeile, und beide Leser verweigern darauf — unabhängig davon, ob
unter dem Verzeichnis überhaupt gesucht worden wäre. Für `staging/`, für gepunktete Pfade und für
kernel-eigene Bereiche ist die Antwort auf ein lesbares Verzeichnis „wird nicht durchsucht"; die
Antwort auf ein unlesbares ist „der ganze Lauf wird verweigert".

**Kette (gemessen 2026-08-08, `icacls /deny <user>:(OI)(CI)(RD,RA)` auf je ein Verzeichnis eines
sauberen Zustands mit Wurzel-Item, `gate_memory_complete` als Prozess auf `git merge`):**
`.audit/` lesbar ⇒ **rc 0**, gesperrt ⇒ **rc 2** und die Meldung nennt das Verzeichnis; `staging/`
lesbar ⇒ **rc 0**, gesperrt ⇒ **rc 2**, ebenso benannt. Beide Verzeichnisse werden im lesbaren
Zustand von keinem Suchlauf angesehen. Die Abhilfe der Meldung verlangt eine Shell außerhalb der
Sitzung, weil `gate_write_scope` jeden Tool-Write unter `project_memory/` verweigert.

**Urteil: OFFEN als Über-Verweigerung, kein Loch.** Fail-closed ist hier die richtige Richtung: ein
Verzeichnis, das der Walk nicht öffnen kann, hat keinen Pfad, über den sich sein Inhalt einordnen
ließe — der Name im Fehler ist alles, was existiert, und daraus „hier wäre ohnehin nicht gesucht
worden" abzuleiten hieße, dem Fehlerpfad zu vertrauen, wo gerade nichts gelesen werden konnte.

**Was stattdessen begrenzt:** die Verweigerung nennt das Verzeichnis und eine ausführbare Abhilfe,
und sie ist nicht dauerhaft — Leserechte zurückgeben löst sie auf. Die Gegenrichtung ist gemessen:
dasselbe Verzeichnis wieder lesbar ⇒ kein Befund.

**Stolperdraht:** `test_migrate.test_a_directory_the_walk_cannot_open_is_named_and_refuses_the_run`

### L29 — Die Faltung des Vorschlagsbereichs ist `str.lower`, die des Dateisystems eine andere

**Mechanismus:** `layout.is_in_proposal_area` vergleicht das erste Pfadsegment nach `str.lower()`.
Ein Windows-Dateisystem faltet mehr als Groß-/Kleinschreibung.

**Kette (gemessen 2026-08-08 auf diesem Host):** `staging/x.yaml`, `Staging/x.yaml` und
`STAGING/x.yaml` — Dateisystem öffnet, Prädikat sagt ja. `staging./x.yaml` — Dateisystem öffnet
**dieselbe** Datei, Prädikat sagt **nein**; `staging../x.yaml` öffnet nichts. Ein V1-Speicher, den
jemand unter dieser Schreibweise anspricht, wäre also `searched` statt `unsearched`.

**Urteil: OFFEN, heute nicht erreichbar.** Jeder Aufrufer im Kernel füttert das Prädikat mit einem
Namen, den `os.walk` erzeugt hat, und ein Walk liefert den Namen, den das Verzeichnis wirklich
trägt — die abweichende Schreibweise entsteht nur, wenn ein Aufrufer einen von Hand getippten Pfad
hereinreicht. Ein Rest des **Prädikats**, kein Loch im Harness.

**Was stattdessen begrenzt:** die Richtung des Fehlers ist die harmlose beider Seiten — eine Datei
würde zusätzlich durchsucht und damit **gemeldet**, nicht verschwiegen; und der Docstring des
Prädikats nennt jetzt beide Reste statt nur den der Gegenrichtung.

**Stolperdraht:**
`test_migrate.test_every_spelling_of_the_proposal_area_gets_one_answer_from_both_readers`
(die gemessene Hälfte: die Groß-/Kleinschreibung)

### L30 — Zwischen der Frage nach dem Landeplatz und dem `os.replace` bleibt eine Spanne

**Was hier bis 2026-08-09 stand, ist weg statt begrenzt.** Der Eintrag beschrieb die gedruckte
Abhilfe des Trockenlaufs: sie nannte einen Landeplatz, der im Augenblick des Lesens frei war, und
der Leser handelte später in einer Shell außerhalb der Sitzung. **DEC-0024** hat diese Klasse
konstruktiv abgeschafft — eine Abhilfe nennt heute nur noch eine **Kopie** in die Ablage unter
`staging/`, die dieses Kommando selbst besitzt und in der der Name aus dem Quellpfad abgeleitet ist
(`migrate.deposit_of`). Sie schlägt keine Bewegung mehr vor, also gibt es dort keinen Platz mehr,
den jemand später besetzen könnte. Was übrig bleibt und diesen Eintrag jetzt trägt, ist die
**eigene** Bewegung des Kommandos.

**Mechanismus:** `migrate._retire_absorbed_documents` fragt `_is_occupied(landing)`, ruft dann
`os.makedirs` und danach `os.replace`. `os.replace` hat auf keiner der beiden Plattformen, auf denen
dieses Harness läuft, eine no-clobber-Variante: es ersetzt, atomar und wortlos. Zwischen Frage und
Ersetzung liegen also zwei Aufrufe, und eine Datei, die in dieser Spanne entsteht, wird von einem
Lauf weggenommen, der gefragt und „frei" gehört hat. Der frühere Satz an dieser Stelle — die eigene
Bewegung frage „dort, wo **keine Spanne** bleibt" — war damit eine Zusicherung, die der Code nicht
baut.

**Kette (gemessen 2026-08-09):** Zustand mit einem vollständig absorbierten `a.yaml`, Plan gebaut,
`occupied_landings == []`, `plan_is_executable` True. Die Spanne wird deterministisch besetzt, indem
der Aufruf besetzt wird, der wirklich dazwischen liegt (`os.makedirs` legt zusätzlich
`legacy/a.yaml` an). Ergebnis: der Lauf endet mit rc 0, `moved` nennt `a.yaml`, und der Inhalt von
`legacy/a.yaml` ist der des Dokuments — die fremde Datei ist ohne Meldung fort.

**Urteil: OFFEN, mit den heutigen Primitiven nicht ohne Umbau schließbar.** Ein no-clobber-Zug
bräuchte `os.link` + `unlink` (schlägt mit `EEXIST` fehl) statt `os.replace`; das ist ein anderer
Zug mit anderen Dateisystem-Voraussetzungen und keine Formulierungsfrage. Diese Runde hat ihn nicht
gebaut, und der Eintrag behauptet nicht, dass er nicht nötig wäre.

**Was stattdessen begrenzt:** die Spanne ist **innerhalb einer Sitzung nicht erreichbar** —
`gate_write_scope` verweigert jeden Werkzeug-Schreibzugriff unter `project_memory/` außerhalb von
`staging/`, und `legacy/` ist kernel-geschrieben, also kann kein Aufrufer der Sitzung dort in dieser
Spanne etwas anlegen; erreichbar ist sie für einen zweiten Prozess oder einen Editor außerhalb der
Sitzung. Der Fall, dass beim **Planen** schon etwas dort liegt, ist vollständig abgedeckt: der
Trockenlauf meldet ihn vorab (`occupied_landings`), und der Lauf fragt unmittelbar vor der
Zugschleife noch einmal.

**Stolperdrähte:**
`test_migrate.test_the_move_replaces_a_file_that_appears_between_the_question_and_the_write`
(die Spanne selbst) und
`test_migrate.test_the_move_asks_again_when_the_place_was_free_while_the_plan_was_built`
(die Hälfte, die abgedeckt ist)

### L31 — „Wer hat die Datei geöffnet" ist der erste Rahmen außerhalb der Standardbibliothek

**Mechanismus:** die Zusicherung „jeder Lesezugriff dieses Moduls unter der Zustandswurzel geht
durch `_read_bytes`" wird an einem `sys.addaudithook` gemessen: beim `open`-Ereignis wird der Stapel
nach außen gegangen, und der **erste Rahmen außerhalb der Standardbibliothek** gilt als der, der die
Datei wollte. Öffnet eine Bibliothek, die nicht zur Standardbibliothek gehört, eine Zustandsdatei im
Auftrag dieses Moduls, wird der Vorgang ihr zugerechnet und ist im Ergebnis unsichtbar.

**Kette (gemessen 2026-08-09 im Klon außerhalb des Repos):** die Regel davor zählte `ast.Call` mit
`func.id == "open"` und war in **beiden** Richtungen falsch — ein echter zweiter, ungehandelter
Leser (`io.open` in `_retire_absorbed_documents`) ließ sie **grün**, eine verhaltensgleiche
Umschreibung innerhalb `_read_bytes` machte sie **rot** mit einer dann unwahren Meldung. Die neue
Messung ist in beiden Fällen richtig (rot / grün) und sieht zusätzlich `pathlib.Path.read_bytes`,
`codecs.open` und `os.open`. Was sie nicht sieht, ist der Fall oben.

**Der zweite Rest, und er ist der größere:** die Messung ist total über die **Schreibweise** und nur
über den Pfad, den **dieser eine Lauf** ausführt. Ein zweiter Leser in einem nie betretenen Zweig ist
hier grün — die abgelöste AST-Regel hätte ihn gefunden. Deshalb steht die statische Regel seit dieser
Runde **wieder daneben**, in der anderen Richtung:
`test_migrate.test_nothing_but_these_functions_can_name_a_file_of_the_state_directory`
liest die ganze **Datei** und fragt, welche Funktionen einen Pfad unter der Zustandswurzel überhaupt
**benennen** können — einen Schritt vor jedem Öffnen, also ohne Aufzählung von Öffner-Namen.
(Hier stand bis 2026-08-09 eine Deckungszahl „439 von 819 Anweisungszeilen". Sie stand an drei
Orten, nannte ihre Zählregel nicht — der Prüfer kam mit seiner eigenen auf 496 von 890 — und kein
Test hielt sie. Sie ist ersatzlos weg; was sie belegen sollte, ist jetzt die Zusicherung unten.)

**Die Korrektur dieser Runde, und sie war ein echtes Loch:** die statische Regel sieht nur, wer einen
Pfad **benennt**. Eine Funktion, die einen fertig komponierten Pfad **entgegennimmt**, benennt nichts
— `_unreadable_because(exc, path)` und `_without_path(text, path)` waren genau diese Form, lagen im
Fehlerzweig, und ein **echter zweiter Leser** in der ersten ließ **beide** Stolperdrähte grün
(gemessen 2026-08-09 im Klon außerhalb des Repos: beide Wächter rc 0, ganze Datei 125 passed,
Audithook meldete den Leser trotzdem nicht als Verletzung). Beide nehmen jetzt `rel` und komponieren
selbst, stehen damit wieder vor der Regel, und eine dritte Zusicherung im selben Test hält die
Eigenschaft statt der Liste: **kein Aufruf dieses Moduls reicht einen komponierten Zustandspfad an
eine andere Funktion desselben Moduls weiter** (`_handed_a_finished_path`).

**Urteil: OFFEN als Rest der Messung, kein Loch im Produkt.** Die Fremdbibliothek-Zurechnung
erreicht heute nichts: `yaml` ist die einzige Fremdbibliothek auf diesem Pfad, und ihr werden Bytes
übergeben, nie ein Pfad. Eine Aufzählung der erlaubten Zwischenschichten wäre wieder die Aufzählung,
gegen die dieses Repo gebaut ist.

**Was stattdessen begrenzt:** die Gegenrichtung läuft im selben Test mit — ein absichtlich
eingesetzter zweiter Leser in einem Rahmen von `migrate.py` **muss** gemeldet werden, sonst ist der
Test rot; und der Test verlangt, dass der Lauf überhaupt Zustandsdateien durch `_read_bytes`
geöffnet hat, damit „keine Verletzung" nicht heißt „es wurde nichts gelesen". Dass die beiden Regeln
sich in der Mitte treffen, ist seit dieser Runde **keine Prosa mehr, sondern eine Zusicherung
desselben Tests**: derselbe Prozess sammelt per `sys.settrace`, welche Funktionen er betreten hat,
und **jede** Funktion, die die statische Regel lizenziert, muss darunter sein. Was nach beidem
bleibt, ist ein zweiter Leser **innerhalb** einer lizenzierten Funktion, in einem Zweig, den der Lauf
nicht betritt.

**Stolperdraht:**
`test_migrate.test_every_state_file_this_module_opens_it_opens_through_read_bytes`

### L32 — Der Ablagename ist injektiv, weil er nie kürzt — und wird darum irgendwann unanlegbar

**Mechanismus:** `migrate.deposit_of` kodiert den ganzen Quellpfad in den Dateinamen und kürzt ihn
nie; genau das macht zwei Quellen zu zwei Namen (DEC-0024). Der Preis ist die Länge: `staging/` +
`v1-deposit--` + Quellpfad, kodiert in `migrate._NAME_ALPHABET` — jedes Zeichen, das nicht
Kleinbuchstabe, Ziffer, `-` oder `_` ist, wird zu einem `%xx`-Tripel in Kleinhex. Seit TSK-0023
Runde 6 gehört der **Großbuchstabe** dazu (F2: sonst faltet dieses Dateisystem zwei Ablagenamen zu
einem), er kostet also drei Zeichen statt einem. Ein Quellpfad, den das Dateisystem noch annimmt,
kann damit einen Ablagenamen erzeugen, den es nicht mehr annimmt.

**Kette (gemessen 2026-08-09 auf diesem Host):** die längste anlegbare Namenskomponente ist **255**
Zeichen, 256 antwortet `OSError: [Errno 22] Invalid argument`. Eine Quelldatei aus **248** ASCII-
Zeichen wird angelegt, ihr Ablagename ist **262** Zeichen lang und ist nicht anlegbar. Nicht-ASCII
trifft es früher, weil jedes Zeichen zu drei oder mehr Prozent-Tripeln wird: **29 CJK-Zeichen**
ergeben 235, **43 kyrillische** 247 — die nächste Handvoll darüber liegt jenseits der Grenze. Bis zu
dieser Runde druckte der Trockenlauf die Anweisung wortlos, und der Leser traf die Verweigerung des
Dateisystems statt einen Satz im Bericht.

**Urteil: OFFEN, nicht schließbar ohne den Defekt zurückzuholen, gegen den die Konstruktion gebaut
ist.** Kürzen oder Hashen macht aus zwei Quellen wieder einen Platz — das ist die Kollision, wegen
der DEC-0024 überhaupt eine Konstruktion statt einer Klausel verlangt. Ein zweistufiger Name
(Unterverzeichnis pro Quellverzeichnis) verschiebt die Grenze, macht die Ablage aber zu einem
**Verzeichnis** unter `staging/` — und das ist ein Staging-Schlüssel, den beide Leser als verwaist
melden. Diese Runde hat keinen dritten Weg gebaut und behauptet nicht, dass es keinen gibt.

**Was stattdessen begrenzt:** die Meldung sagt es jetzt dort, wo sie den Namen druckt
(`migrate.deposit_note`): um wie viele Zeichen der Name zu lang ist, dass dieses Dateisystem ihn
nicht nimmt, und dass dieses Kommando keinen kürzeren anzubieten hat und warum. Die Richtung des
Restes ist die harmlose: die Anweisung ist **nicht ausführbar**, nicht etwa ausführbar mit
Datenverlust — der Leser verliert nichts, er bekommt keinen Platz. Und die Grenze selbst steht an
genau einem Ort im Code (`migrate._NAME_MAX_CHARS`), gekoppelt an das Dateisystem statt
nacherzählt: der Stolperdraht legt die Namen wirklich an und verlangt, dass der Satz genau dann
erscheint, wenn das Anlegen scheitert — auf einem Host mit anderer Grenze wird er rot, und das ist
die richtige Antwort.

**Dieselbe Grenze trifft den Overflow-Namen 67 Zeichen früher, und dort ist die Folge größer:**
`migrate.overflow_deposit_of` (L35) kodiert nicht nur den Pfad, sondern Pfad **plus** sha256 — das
sind `%2f` und 64 Hex-Zeichen, gemessen 2026-08-09 als Differenz der beiden Namen für denselben Pfad
(`deposit_of` 37 Zeichen, `overflow_deposit_of` 104). Die Kette oben („248 ASCII → 262") liegt für
diesen Namen also 67 Zeichen früher; die blockierende Bedingung ist ein **belegter** Landeplatz unter
`legacy/`, dessen Pfad plus 67 über `_NAME_MAX_CHARS` geht. Was den Unterschied ausmacht, ist nicht
die Länge, sondern der Preis: ein unanlegbarer Datensatz-Ablagename kostet den Bulk **eines
Datensatzes**, ein unanlegbarer Overflow-Name hängt an `occupied_landings` — und solange der
Landeplatz belegt ist, ist `plan_is_executable` **falsch**, die Migration also durch keine der
gedruckten Routen mehr abschließbar. Seit BUG-0026 trägt auch `migrate.record_deposit_of` den
sha256 des Datensatz-Körpers im Namen (aus demselben Grund wie der Overflow-Name: die zugehörige
Abhilfe kürzt die Quelle, ein belegter Name muss also byte-gleiche Bytes tragen), liegt seine
Längengrenze also dieselben 67 Zeichen früher. Rest und nicht Blocker, weil die Ausfallrichtung
dieselbe harmlose ist wie oben (die Anweisung ist nicht ausführbar, sie verliert nichts) und
`deposit_note`
auch hier an der Druckstelle steht — `copy_instruction` ist der eine Komponist für beide Namen, der
Satz erscheint also für den Overflow-Namen genauso (gemessen: „That name is 40 character(s) longer
than the 255 …" für einen 200-Zeichen-Landeplatz).

**Ein weiterer Rest im selben Eintrag, weil er dieselbe Grenze betrifft:** `migrate.deposit_note`
misst nur die **Namenskomponente**, nicht den Gesamtpfad. Auf einem Host ohne Langpfad-Unterstützung
kann ein Name unter 255 Zeichen die Gesamtpfadgrenze sprengen, und dann fehlt der Satz genau dort,
wo er gebraucht wird. **Auf diesem Host nicht erreichbar** (gemessen 2026-08-09, in einem
Verzeichnisbaum außerhalb dieses Repos: Gesamtpfade von 261, 271, 321, 401, 451 und 520 Zeichen
werden alle angelegt, Namenskomponente jeweils unter 255). Nicht gebaut, weil die Grenze, die dann
gälte, auf diesem Host nicht messbar ist — und eine Zahl, die niemand hier messen kann, wäre genau
die nacherzählte Konstante, gegen die der Absatz darüber argumentiert.

**Stolperdraht:**
`test_migrate.test_a_deposit_name_too_long_to_create_says_so_where_it_is_printed`
(die Namenskomponente; für den Gesamtpfad gibt es keinen, siehe Absatz darüber)

### L33 — Eine Abhilfe, deren Ortsangabe erst zur Laufzeit entsteht, liest die statische Regel nicht

**Mechanismus:** `test_migrate.test_no_remedy_literal_this_repo_ships_names_a_place_inside_a_state_directory`
liest **Zeichenketten-Literale** des ausgelieferten Codes (`_remedy_literals`) und fragt jedes Wort
darin, ob es pfadförmig ist und eine Komponente im Zustandsverzeichnis nennt
(`_places_inside_a_state_directory`). Eine Abhilfe, die ihren Ort über einen **Formatplatzhalter**
einsetzt, hat im Literal kein solches Wort — der Ort entsteht erst beim Formatieren, und `%s` nennt
nichts.

Zwei weitere Formen fallen aus derselben Domäne, beide gemessen und beide **keine** Backtick-Frage
mehr: eine Abhilfe, die als **Name** statt als Literal übergeben wird
(`report.validate_state` reicht seit Runde 9 `migrate.THE_ONLY_UNLISTABLE_STEP` durch — die Zählung
der Parameter-Hälfte fiel dadurch von 57 auf 56), und eine, deren Empfänger unter einer Schreibweise
steht, die die Signaturauflösung nicht kennt (Alias, Attribut eines Objekts, umbenennender Import).
Die Backtick- und Leerzeichenbedingung, die bis Runde 7 hier stand, gehört **nicht mehr** zu dieser
Regel: sie sitzt in `_state_paths_in`, dem Leser des **Laufzeit**-Tests
(`test_no_remedy_the_validator_prints_names_a_place_inside_the_state_directory`), und dort wertet
`if " " in word.strip(): continue` ein Wort mit Leerzeichen weiterhin als Befehlszeile statt als
Pfad.

**Kette (gemessen 2026-08-09):** zwei solche Abhilfen existieren heute, beide nennen einen Ort im
Zustandsverzeichnis und schlagen eine **überschreibende** Bewegung darauf vor:

- `team-kits/kernel/state.py` — `corrupt item file for %s at %s … Remedy: \`git restore %s\``
- `team-kits/kernel/approvals.py` — `… Remedy: re-approve the current revision, or \`git restore %s\`
  to return to the approved content` — dort ist das Verwerfen der Nutzerbearbeitung ausdrücklich der
  Zweck.

Beide sind für die statische Regel unsichtbar; der Trockenlauf-Test daneben
(`test_no_remedy_the_validator_prints_names_a_place_inside_the_state_directory`) sieht nur, was seine
Fixtures erreichen, und erreicht keine der beiden.

**Urteil: OFFEN als Rest, nicht blockierend.** Die Kette läuft **nicht innerhalb einer Sitzung**
durch, und das ist gemessen statt geschlossen: die gedruckte Zeile selbst, als echter Hook-Prozess
mit JSON auf stdin, 2026-08-09 —

```
gate_lead_write_scope (dieses Repo)  git restore project_memory/tasks/active/TSK-0023.yaml  -> rc 2
gate_write_scope (dev/office/research, je frisch scaffoldetes Projekt)
                                     git restore project_memory/product/active/PR-0001.yaml  -> rc 2
```

Der Leser muss also eine Shell **außerhalb** der Sitzung öffnen. Und anders als bei DEC-0024 ist die
vorgeschlagene Bewegung im Fall von `approvals.py` genau das, was der Nutzer will.

**Was stattdessen begrenzt:** der Name des Tests und sein erster Satz sagen **LITERAL** statt „jede
Zeichenkette, die der ausgelieferte Code drucken kann", und sein Docstring nennt die beiden Stellen.
Die Behauptung deckt damit genau die Domäne, die die Regel wirklich liest; vorher behauptete sie
eine, die sie nicht hatte. Die Domäne selbst ist seit Runde 9 dreiteilig — Wort, `remedy`-Slot und
**Positionsargument, das in einem `remedy`-Parameter landet** — und die dritte Hälfte hat allein 56
Literale, darunter alle Befunde von `report.validate_state`.

**Stolperdraht:** keiner für die Laufzeit-Hälfte. Für die Literal-Hälfte:
`test_migrate.test_no_remedy_literal_this_repo_ships_names_a_place_inside_a_state_directory`

### L34 — Ein Empfänger, zu dem die Namen dieses Moduls an der Verwendungsstelle nicht führen, ist für die Übergaberegel unsichtbar

**Mechanismus:** `test_migrate._handed_a_finished_path` sieht eine Übergabe genau dort, wo ein
Zustandspfad und ein **Name dieses Moduls** zusammentreffen — in einem Aufrufausdruck (beide Seiten
über die Locals verfolgt: `_carries_a_state_path` für den Pfad, `_value_leads_to` für den Empfänger)
oder in einer Ablage, deren Ziel in einem Modulnamen wurzelt (`_stashed_names`). Was übrig bleibt,
ist ein Empfänger, zu dem diese Namen **an der Stelle, an der er benutzt wird**, nicht führen.

Die Grenze „eigenes gegen fremdes Modul" war bis Runde 8 die Beschreibung dieses Rests und ist
gemessen **keine** Grenze: vier gewöhnliche Routen **innerhalb** dieser Datei trugen die Bytes in
einen echten Leser, während die Regel `[]` meldete (B1). Sie sind seither gedeckt. Und die
Beschreibung, die in Runde 8 an ihre Stelle trat — „der Rest ist ein Empfänger, zu dem die Namen
dieses Moduls **an der Verwendungsstelle** nicht führen" — ist **ebenfalls widerlegt**: die
Closure-Route unten führt in einen Empfänger, den `_module_own_names` sehr wohl kennt, und wird
trotzdem nicht gesehen, weil es überhaupt keinen Aufrufausdruck gibt, der etwas überträgt.

**DEC-0029 ist die Konsequenz daraus und gilt für diesen ganzen Eintrag:** die Regel wird als
**Menge gemessener Routen** geführt (heute sechzehn im Korpus, fünf hier als offen benannt), nicht
als Deckung. Ob ein Wert in beliebigem Python eine Stelle erreicht, ist statisch nicht entscheidbar;
der Verlauf 6 → 12 → 16 → 17 ist genau das von innen gesehen.

**Kette (gemessen 2026-08-09, echter Prozess, Markerdatei, Leser gibt die gelesenen Bytes zurück):**
in `_read_bytes` gepflanzt —

```
os.environ["PARKED"] = _state_path(state, rel)      # Ablage in einem fremden Modulobjekt
_a_reader_of_a_foreign_module()                     # liest open(os.environ["PARKED"], "rb")
parked in an object of ANOTHER module               reads: YES   rule says: []

reader = _a_reader_factory()                        # Aufrufergebnis DIESES Moduls ...
functools.partial(reader, _state_path(state, rel))()   # ... als ARGUMENT an einen fremden Wrapper
out of a factory, handed to a foreign wrapper       reads: YES   rule says: []
```

Und die Route, die der Prüfer in derselben Prüfung fand, in der Runde 8 die sechzehnte einbaute — ein
`def` **innerhalb** der Wirtsfunktion, der den Pfad aus der **Closure** liest statt ihn als Argument
zu bekommen. Hier nachgemessen (2026-08-09, dieselbe Vorrichtung, echter Prozess; der Leser meldet
sich über eine **Markerdatei**, weil der Kanal die Antwort mitentscheidet — siehe direkt darunter):

```
path = _state_path(state, rel)
def _a_closure_reader():                              # kein Argument, kein Aufrufausdruck ...
    open(r"<marker>", "wb").write(open(path, "rb").read())   # ... liest aus der Closure
_a_closure_reader()
into a def that closes over the path        reads: YES   rule says: []   handed: []
```

**Und was dabei auffiel, gemessen im selben Lauf:** dieselbe Route wird **doch** gemeldet, sobald der
geschachtelte Leser seine Bytes an irgendeinen Namen dieses Moduls weiterreicht
(`_PLANTED.append(open(path, "rb").read())` → `handed: [('_read_bytes', 'path', '_PLANTED', 766)]`,
und ebenso mit einem Zwischen-Local). Das ist kein Schutz, sondern ein Zufall der Beobachtung: was
die Regel dort sieht, ist der **Aufruf, der die Bytes ablegt**, nicht die Übergabe des Pfades. Ein
Leser, der über einen Kanal außerhalb dieses Moduls meldet, ist unsichtbar — und genau das ist die
Route.

Die zweite Route ist der Preis der Asymmetrie, die B1 an die Verwendungsstelle gehängt hat: ein
Aufrufergebnis dieses Moduls zählt nur in der **Callee-Position** als Code dieses Moduls, weil dort
das Programm selbst sagt, dass der Wert aufrufbar ist. In der Argumentposition dieselbe Auflösung zu
fahren, meldet das ausgelieferte Modul mit `absorbed_documents` als Empfänger eines Pfades, den es
nie bekommt (gemessen, dieselbe Runde). Ebenfalls offen und derselben Klasse: ein Empfänger aus
`sys.modules` oder `getattr`, und ein Aufrufausdruck, der sich auf gar keinen Namen reduzieren lässt
(ein sofort angewandtes Lambda).

Zum Vergleich, im selben Lauf: **jede** Route des Korpus (`_HOW_A_PATH_TRAVELS`) — darunter die
Ablage in Attribut, Mapping, Liste und **Default-Argument** dieses Moduls, der lokale Alias des
Empfängers, deren Kreuzung, und ein `def` innerhalb der Wirtsfunktion, **der den Pfad als Argument
bekommt** — wird benannt.

**Urteil: OFFEN als Rest, nicht blockierend (DEC-0022 zum Bedrohungsmodell dieser Regel, DEC-0029
zur Anspruchshöhe).** Die Regel ist ein Stolperdraht gegen einen **zweiten Leser**, den ein Autor
dieses Moduls versehentlich hinzufügt; sie ist keine Sandbox gegen einen Autor, der ihn verstecken
will. Ein Pfad, der durch `os.environ` reist, und ein Fabrikergebnis, das durch einen fremden
Wrapper zurückgereicht wird, sind keine Schreibweisen, in die man hineinfällt — die Closure-Route
dagegen **schon**, und sie bleibt trotzdem offen: sie zu sehen hieße, Datenfluss ohne Übertragung zu
verfolgen, und genau davor endet die statische Frage.

**Was stattdessen begrenzt:** der eigentliche Schutz ist nicht dieser Draht.
`test_every_state_file_this_module_opens_it_opens_through_read_bytes` läuft mit einem Audithook und
sieht **jedes** Öffnen einer Datei unter der Zustandswurzel, egal wie der Pfad dorthin kam und egal
wie das Öffnen geschrieben ist. Was **dieser** Wächter nicht sieht, gehört ausdrücklich daneben: er
misst nur, was ein Lauf wirklich ausführt, und ist für jeden nicht betretenen Zweig blind — die
umgekehrte Hälfte des statischen Drahts. Dazu schreibt der Docstring von `_handed_a_finished_path`
den **Mechanismus** hin statt einer Liste gedeckter Schreibweisen und nennt alle fünf offenen Formen
beim Namen.

**Stolperdraht:** keiner für diese fünf Routen (das ist das Loch). Für die gedeckten:
`test_migrate.test_the_rule_against_handing_a_state_path_on_follows_the_value_and_not_the_call_shape`

### L35 — Eine gedruckte Abhilfe verlangte eine Bewegung ohne Ziel — GESCHLOSSEN durch ein konstruiertes Ziel außerhalb des Zustandsverzeichnisses (Runde 9)

**Mechanismus (was hier stand):** DEC-0024 hat zwei Klauseln. Die erste verbietet, einen Platz **im**
Zustandsverzeichnis zu nennen, den der Leser anlegen oder überschreiben müsste. Die zweite verlangt
**Kopieren statt Verschieben**, „also kann kein befolgter Rat etwas vernichten, **auch nicht die
Quelle**". Genau **eine** ausgelieferte Abhilfe verlangte weiterhin eine Bewegung: die des **belegten
Landeplatzes** im Trockenlauf (`team-kits/kernel/migrate.py`, Abschnitt *LANDING PLACE UNDER legacy/
ALREADY TAKEN*). Sie nannte kein Ziel — die Wahl lag beim Leser — aber sie nahm die Quelle weg:

```
migrate.render, belegter Landeplatz   "Remedy, per document: take the file each line above names
                                       on the right out of the state directory, from a shell
                                       outside the session, then re-run the dry run."
                                      nennt ein Ziel: nein     verlangt eine Bewegung: ja
```

Was der Leser bewegt, ist eine Datei unter `legacy/` — ein kernel-geschriebener Bereich, in dem eine
frühere Migration ihr Ergebnis abgelegt hat. Wer sie irgendwohin schiebt und dort vergisst, verliert
sie; das Decision-Item des früheren Laufs trägt nur ihren Hash, nicht ihren Inhalt.

**Entscheidung des Nutzers (2026-08-09): Ziel konstruieren.** Nicht die Ausnahme abnehmen und nicht
den Vorschlag streichen, sondern ein **konstruiertes, kollisionsfreies Ziel außerhalb des
Zustandsverzeichnisses** nennen — so wie `deposit_of` es innerhalb von `staging/` tut, nur außerhalb.
Die frühere Begründung („das Werkzeug darf kein Ziel ableiten") betraf Ziele **im** Zustandsbaum; für
ein Ziel daneben gilt sie nicht.

**Was gebaut ist:** `migrate.overflow_deposit_of(rel, digest)` — `../v1-legacy-overflow/` neben dem
Zustandsverzeichnis, darunter ein Name aus demselben Kodierer wie `deposit_of` (`_encoded_name`,
`migrate._NAME_ALPHABET`), der den **Landeplatzpfad und den sha256 des dort stehenden Inhalts** trägt.
Der Abschnitt druckt pro Zeile den einen Composer (`copy_instruction`) und danach den zweiten Schritt:
erst **kopieren**, dann — und nur dann — das Original entfernen.

```
  a.yaml                       -> legacy/a.yaml is already taken
     Remedy: COPY it -- the original stays where it is -- to
     `../v1-legacy-overflow/v1-deposit--legacy%2fa%2eyaml%2f3d51709d…`. Then, and only once that
     copy exists, remove legacy/a.yaml itself from a shell outside the session -- the copy is what
     keeps the file, and removing the original is what frees the place.
```

**Warum der Inhalt im Namen steht und nicht nur der Pfad** — das ist der Unterschied zu `deposit_of`
und eine gemessene Kette, keine Vorsicht: dort bleibt die Quelle stehen, ein belegter Name hält also
eine frühere Kopie **derselben** Datei. Hier entfernt der Leser das Original, und derselbe
Landeplatzpfad kann später andere Bytes tragen (Lauf 1 legt A ab; Leser kopiert A heraus und löscht
es; Lauf 2 legt B am selben Platz ab; Lauf 3 bietet dieselbe Abhilfe wieder an). Mit dem Pfad allein
im Namen landet die dritte Anweisung auf A. Mit dem Digest darin ist ein belegter Name eine Datei mit
**identischen Bytes**.

**Urteil: GESCHLOSSEN.** Ausgeführt und gemessen, nicht behauptet:
`test_migrate.test_the_place_a_taken_landing_is_freed_to_is_named_and_lies_outside_the_state_directory`
fährt beide Schritte auf der echten Platte — die Kopie ist byte-gleich, der Landeplatz danach frei,
der nächste Plan ausführbar — und lässt anschließend eine **zweite** Datei denselben Platz belegen:
die zweite Anweisung nennt einen anderen Namen, und die erste Kopie steht danach unverändert da.

**Was offen bleibt und hier benannt statt geschlossen wird:** zwei weitere Abhilfen von
`report.validate_state` sagen weiterhin *take the file out of the state directory* (`_bounded` für ein
Dokument über einem der beiden Lesebudgets, und die Abhilfe für ein unparsbares Dokument). Sie nennen
**kein** Ziel, überschreiben also nichts; sie können aber die Quelle kosten. Warum die hier gebaute
Konstruktion an beiden Stellen fehlt, ist **nicht derselbe Grund** — bis Runde 10 stand hier einer für
beide („diese Stellen lesen die Datei absichtlich nicht"), und für die zweite war er falsch:

- **`_bounded` — nicht verfügbar.** Der Name braucht den sha256 der Datei, und dieser Zweig
  entscheidet allein aus `os.path.getsize`, **vor** jedem Lesen — genau weil das Lesen es ist, was
  `DOCUMENT_MAX_BYTES`/`DOCUMENT_SCAN_MAX_BYTES` auf dem Pfad des Merge-Gates verbieten. Ein Digest
  wäre hier nur zum Preis des unbegrenzten Lesers zu haben, gegen den der Bund gebaut ist.
- **Unparsbares Dokument — verfügbar und nicht gebaut.** Dieser Zweig wird erst hinter `spent += size`
  erreicht, über `migrate._read_document` → `_read_bytes`; der Parse scheitert **nach** dem Lesen, die
  Bytes waren also in der Hand. Gemessen 2026-08-09 mit `sys.addaudithook` über einen echten
  `report.validate_state`-Lauf außerhalb dieses Repos: geöffnet wurden `.kernel.lock`, das Wurzelitem
  und `broken.yaml`, **nicht** aber das übergroße `big.yaml`. Der Digest hätte hier keinen einzigen
  zusätzlichen Byte-Zugriff gekostet. Was fehlt, ist der Rückweg — `_read_document` gibt die Bytes
  nicht heraus, und ein Ziel anzubieten kostet eine Signaturänderung an einem Leser mit fünf
  Aufrufstellen. Nicht gebaut; das ist ein Rest und keine Unmöglichkeit.

Dazu der Unterschied, der beide von dieser Fundstelle trennt: was sie bewegen lassen, ist ein Dokument,
das der Leser **selbst geschrieben** hat, während unter `legacy/` eine Datei liegt, für die es nach
der Installation keinen Schreiber mehr gibt. Ein Rest, kein Blocker — die Kette braucht eine Shell
außerhalb der Sitzung und die Unachtsamkeit des Lesers mit seiner eigenen Datei.

**Und ein dritter Rest, in der geschlossenen Abhilfe selbst:** der Zusatz *from a shell outside the
session* hängt in `migrate.py` (Abschnitt *LANDING PLACE UNDER legacy/ ALREADY TAKEN*) am
**Entfernen**; der **Kopie** ist keiner beigegeben, obwohl auch sie an diesem Gate vorbei muss. Gemessen
2026-08-09 gegen den ausgelieferten `gate_write_scope.py` als Prozess, in einem gescaffoldeten Projekt
außerhalb dieses Repos mit gültigem Wurzelitem: `cp`, `cp -p` mit absolutem Ziel, `Copy-Item` (relativ
und absolut) und `python -c "shutil.copy(...)"` antworten **rc 2**, das Entfernen (`rm`,
`Remove-Item`) ebenfalls rc 2, reines Lesen rc 0. Der fehlende Halbsatz wäre aber **nicht pauschal
wahr**, und deshalb steht er hier statt eingesetzt im Code: eine Umleitung, die die Quelle nur liest
und außerhalb landet (`cat < project_memory/legacy/a.yaml > ../v1-legacy-overflow/<name>`,
`Get-Content … > …`), antwortet **rc 0** — diese eine Schreibweise der Kopie gelingt in der Sitzung.
Ausfallrichtung harmlos: wer die Kopie mit einem Kopierbefehl versucht, bekommt eine Verweigerung, die
der Satz nicht ankündigt, aber keinen Verlust. Fix wäre ein Halbsatz an derselben Stelle, der die
Verweigerung nennt, ohne sie für jede Schreibweise zu behaupten.

**Was stattdessen begrenzt:** die Datei, die der Leser bewegt, ist im selben Abschnitt **beim Namen
genannt** (linke und rechte Spalte je Zeile), und der Abschnitt sagt, warum sie dort steht. Dazu die
Domäne des DEC-0024-Stolperdrahts: seit Runde 9 sind es **drei** Arten, wie dieses Repo eine Abhilfe
ausliefert — das **Wort** `Remedy` (225 Literale), der `remedy`-Slot als Schlüsselwort (92) und das
**Positionsargument, das in einem `remedy`-Parameter landet** (56, darunter alle Befunde von
`report.validate_state`) — und die Ortsangabe wird backtick-unabhängig über **alle** Pfadkomponenten
gelesen, jetzt auch bei einem Wort, dessen einziger Trenner am Ende steht (`evidence/`).
Der Spec-Satz in `docs/HARNESS_V2_SPEC.md` (e2) behauptet nicht, der Vorlauf schlage „keine Bewegung"
vor, sondern er leite **kein Ziel im Zustandsbaum** mehr ab.

**Stolperdraht:** für die Ortsangabe
`test_migrate.test_no_remedy_literal_this_repo_ships_names_a_place_inside_a_state_directory`;
für die geschlossene Bewegung
`test_migrate.test_the_place_a_taken_landing_is_freed_to_is_named_and_lies_outside_the_state_directory`;
für die unlistbare Hälfte
`test_migrate.test_the_remedy_for_a_directory_nobody_can_list_offers_no_step_that_moves_it`;
für die Eigenschaft, auf der die Trennung der beiden Reste ruht — welches der beiden Dokumente ein
Lauf öffnet und welches nicht —
`test_migrate.test_the_two_remedies_that_still_move_a_file_differ_in_whether_the_file_was_read`
(rot in beide Richtungen gemessen, siehe `docs/reviews/2026-08-08-tsk0023-measurements.md`, R10.1);
für die Reste selbst keiner.

### L36 — Ein kanonisches Verzeichnis, das niemand auflisten kann, las sich für die Gates wie „noch kein Wurzelitem" — GESCHLOSSEN (Runde 9)

**Mechanismus:** `_root.has_root_item` (in allen drei Kits) beantwortete die Frage „hat dieses Projekt
schon ein Wurzelitem?" mit `glob.glob` über `project_memory/**`. `glob` meldet ein Verzeichnis, das
es nicht öffnen kann, als **leer** — ohne Fehler. Die Antwort war dann `False`, und fünf Gates lesen
`False` als „das Projekt wird noch eingerichtet, wir gelten nicht". Ein Verzeichnis, das niemand
lesen kann, schaltete also genau die Gates ab, die das Wurzelitem schützen.

**Kette (gemessen 2026-08-09, echter Hook-Prozess, JSON auf stdin, Zustand außerhalb dieses Repos):**

```
product/active/ lesbar        gate_git.py "git merge feat/PR-0001-x"   -> rc 2 (verweigert)
product/active/ nicht listbar gate_git.py "git merge feat/PR-0001-x"   -> rc 0 (durch)   [vorher]
product/active/ nicht listbar gate_git.py "git merge feat/PR-0001-x"   -> rc 2           [nachher]
```

**Das Urteil bis Runde 8 war „OFFEN als Rest", und es war falsch.** Es stützte sich darauf, dass die
Rechteänderung aus der Sitzung heraus nicht erreichbar sei — `gate_write_scope` verweigert vier
naheliegende Zeilen (`icacls` in zwei Schreibweisen, `chmod`, `attrib`; alle rc 2, gemessen). Der
Prüfer hat das umgangen, und der Mechanismus stand als `L4` („Schreibverben innerhalb einer
Programmsprache … bewusst nicht geschlossen") zwei Bildschirmseiten weiter oben in derselben Datei:

```
python -c "import os,subprocess;p=os.path.join('project'+'_memory','product','active');
           subprocess.run(['icacls',p,'/deny','zenti:(RD,RA)'])"
alle acht Bash-Hooks rc 0  ->  die Zeile läuft  ->  gate_git rc 2 wird rc 0
```

Zweite Route ohne `-c`: `Write scripts/deny_it.py` (alle Schreibhooks rc 0 außer `guard_pm_scope`,
das die PM-Rolle betrifft), dann ausführen. Die Kette läuft damit **innerhalb einer Sitzung** durch
und ist blockierend.

**Fix:** ein Verzeichnis, das existiert und nicht auflistbar ist, ist **nicht** „noch kein
Wurzelitem". `has_root_item` listet jetzt selbst (`_root._names_matching`) und kennt drei Antworten
statt zwei: Namen gefunden, nichts da (nicht vorhanden oder kein Verzeichnis), und **keine Antwort**
— jeder andere `OSError`. Der dritte Fall zählt als Wurzelitem, weil die beiden Ausfallrichtungen
nicht symmetrisch sind: „kein Item" schaltet fünf Gates ab, „ein Item" kostet in einem Projekt, das
noch eingerichtet wird, eine Verweigerung — und eine Verweigerung sagt es.

**Stolperdraht:**
`test_migrate.test_the_remedy_for_a_directory_nobody_can_list_offers_no_step_that_moves_it`
misst beide Seiten mit dem ausgelieferten `gate_git.py` als echtem Prozess: `rc 2` bei lesbarem
Verzeichnis und `rc 2` bei unlesbarem. Fällt der Prädikat auf `glob` zurück, wird dieser Test rot.

### L37 — `validate_state` stürzt über ein kanonisches Verzeichnis, das es nicht auflisten kann

**Mechanismus:** `report._iter_active` läuft über `ProjectState.iter_active_items`, und das ruft
`os.listdir` ohne `onerror`-Behandlung. Ein kanonisches Verzeichnis ohne Leserecht liefert dort einen
ungefangenen `PermissionError`, statt ein Finding zu erzeugen. `migrate.search_coverage` behandelt
denselben Fall (`onerror` → `UNLISTABLE`); der Validator tut es nicht.

**Kette (gemessen 2026-08-09, Zustand außerhalb dieses Repos, `product/active/` ohne Leserecht):**

```
migrate.search_coverage(state)   -> Zeile "product/active/  unlistable  ..."
report.validate_state(state)     -> PermissionError [WinError 5] ... \project_memory\product\active
```

**Urteil: OFFEN als Rest, nicht blockierend.** Ein Absturz ist **laut**: kein Aufrufer liest ihn als
„keine Befunde". Die Ausfallrichtung ist damit die harmlose — anders als bei `L36`, wo dieselbe
Ursache still durchließ. Der Auslöser ist derselbe wie dort, und er ist **innerhalb einer Sitzung
erreichbar** (die `python -c`-Kette bei `L36`); was diesen Eintrag trotzdem zum Rest macht, ist
allein die Richtung des Ausfalls, nicht die Unerreichbarkeit.

**Was stattdessen begrenzt:** der Vorlauf der Migration beantwortet dieselbe Frage über denselben
Zustand und tut es vollständig (`UNLISTABLE`, blockierend), und `report.validate_state` läuft in
jedem Kit hinter einem Hook, der einen Absturz als Verweigerung weitergibt statt als Freigabe.

**Stolperdraht:**
`test_migrate.test_the_remedy_for_a_directory_nobody_can_list_offers_no_step_that_moves_it`
verlangt den `PermissionError` ausdrücklich; wird der Fall zu einem Finding, wird der Test rot.

### L38 — Die Gate-Suite dieses Repos war rot, und keine Runde hat es bemerkt

**Mechanismus:** `.claude/hooks/test_gates.py` läuft **nicht** in `python -m pytest tools/` mit; sie
wird ausdrücklich gestartet (`python -B -m pytest .claude/hooks/test_gates.py -q`). Ein Rot darin
kommt also durch jede Abnahme, die nur die Werkzeugsuite fährt. Genau das ist passiert: der Ausfall
kam mit TSK-0022 herein und hat mindestens eine ganze Runde überlebt, ohne irgendwo zu stehen.

**Kette (gemessen 2026-08-09 vom Prüfer, isoliert reproduziert):** `1 failed, 142 passed`. Gefallen
ist die **Kontrolle** eines Sandkasten-Tests — der Host stellt den Unfall nicht mehr her, gegen den
der Test gebaut ist, also sagt nicht nur eine Zusicherung nichts, sondern der ganze Test.

**Urteil: OFFEN, und nicht dieser Runde zuzurechnen.** Die Ursache liegt in `.claude/`, dem
verbotenen Bereich von TSK-0023; diese Runde fasst dort nichts an. Der Befund ist als
`project_memory/bugs/active/BUG-0014.yaml` erfasst — mit Messung, Repro und den drei
Abnahmekriterien (Test misst wieder, Ursache benannt, ein Weg der ein Rot dieser Suite bemerkt).

**Was stattdessen begrenzt:** die Suite ist rot und nicht still — wer sie fährt, sieht es sofort;
und was sie misst, sind die vier Gates dieses Repos, deren Verhalten in Abschnitt 12 mit eigenen
Ketten steht. Bis BUG-0014 abgearbeitet ist, ist der Sandkasten-Test dieser einen Datei **keine**
Deckung, und keine Runde darf ihn als solche zitieren.

**Stolperdraht:** keiner in `tools/` — das ist der Kern des Eintrags. BUG-0014 AC-3 verlangt einen.

### L39 — Der Handover-Guard folgt nicht in die Verbposition, die eine Substitution oder ein ungelisteter Wrapper besetzt — und sein Marker ist nur beim Namen geschützt (TSK-0031, TSK-0032, eingeengt in Runde 3)

**Mechanismus:** `user/claude/hooks/handover_guard.py::_handle_shell` liest eine Bash-Zeile in
Schritten, deren **Reihenfolge tragend ist**, und nur diese sind gebaut: (1) **Here-Document-Körper**
werden auf dem **rohen** Text herausgeschnitten — dort ist der Delimiter noch als quotiert oder
unquotiert lesbar; (2) Zeilenfortsetzungen werden zusammengezogen (`_CONTINUATION`), (3) erst dann
läuft `_norm`, das sonst aus jedem `\` ein `/` macht und beides unsichtbar; (4) die Zeile wird an
**unquotierten** Trennzeichen zerlegt (`_SEPARATORS` = `;`, `&`, `|`, `\n`, `\r`; die Doppelformen
`&&`/`||`/`|&` brauchen keinen eigenen Eintrag, sie sind zwei Trenner mit einer leeren Spanne
dazwischen); (5) der Verb eines Teilbefehls ist sein erstes Wort, das ein Kommandoname ist —
`VAR=value`, ein führendes `(`/`{`, die **POSIX-Schlüsselwörter** eines zusammengesetzten Kommandos
und eine kleine Wrapper-Menge werden übersprungen, und nach einem `case`-Muster (`a)`) oder einem
Funktionskopf (`f()`) beginnt eine **zweite Namensposition** (`_name_positions`); (6) als **Lesen**
gilt ein Hilfs-Flag an beliebiger Stelle (gemessen: `kernel.cli --root project_memory capture
--help` endet rc 0, es kapturt nichts) und ein Lese-**Unterkommando** nur in Unterkommando-Position
— `capture doctor` ist damit kein Lesen mehr.

**Ein Here-Document-Körper gilt nur als Daten, wenn seine Delimiter-Zeile im selben Aufruf
tatsächlich vorkommt.** Das ist die Bedingung, die eine ganze Fehlerfamilie schließt: ohne sie hat
jedes `<<`, das gar keines ist, den **gesamten Rest ungeprüft** verschluckt — gemessen an einer
Arithmetik-Verschiebung (`echo $((1<<2))`), an einem `<<` in einem **Kommentar** und an einem
quotierten `<<EOF`, das der Unbalanciert-Rückfall der Quote-Maske wieder sichtbar machte. Ergänzend
wird `<<` nur an einer **Umleitungsgrenze** anerkannt (Zeilenanfang, Leerzeichen, Trenner) und ein
unquotierter Kommentar vorher abgeschnitten; beide tragen je einen eigenen roten Fall, nämlich den,
in dem das Falsch-Delimiterwort später **doch** als Zeile auftaucht.

**Was das NICHT liest, ist die Verbposition, die von etwas besetzt ist, dem dieser Leser nicht
folgt** — eine Klasse, mehrere Schreibweisen: eine Shell, die die Zeichenkette später ausführt
(`sh -c '…'`, `bash -lc '…'`); eine **Substitution**, die den Befehl erst erzeugt (`$(…)`,
Backticks, `<(…)` — **auch in doppelten Quotes eingebettet**, denn bash führt eine
Kommandosubstitution in `"…"` aus, während dieser Leser einer quotierten Spanne nicht folgt;
gemessen `echo "a $(python … capture) b"` rc 0, „quoted" heißt also **nicht** „sicher"); ein
**Starterwort außerhalb von `_WRAPPERS`** (`nohup`, `timeout 60`, `uv run`,
`xargs -I{}`, `eval`); und jede kodierte/verschleierte Form. `_WRAPPERS` ist die eine Aufzählung,
die hier nicht schließbar ist — jedes künftige Starterwort stellt sich ebenso davor —, und genau
darum steht sie hier als Rest statt als verlängerte Liste.

**Kette (gemessen 2026-08-10/11 unter Marker, isoliertes cwd außerhalb des Repos, echter Prozess):**
Vorher rc 0, jetzt rc 2 — die drei Fortsetzungsformen (`python \⏎ -m kernel.cli create-task`,
`python -m \⏎ kernel.cli …`, `PYTHONPATH=x python -B \⏎ -m kernel.cli … capture PR`) und acht
zusammengesetzte Kommandos (`for … do`, `while read … do`, `until … do`, `if … then`, `… else …`,
`(…)`, `{ …; }`, `! …`). Weiterhin rc 2 (Regression): `&&`, `||`, `;`, `|`, `|&`, `&`, `\n`, `\r`,
sowie eine Ableitung **nach** einem Heredoc-Ende und nach einer unbalancierten Quote.
Weiterhin rc 0 und **richtig so** — `sh -c '…'`, `bash -lc '…'`, `echo $(python … capture)`,
`echo \`python … capture\``, `diff <(python … capture) /dev/null`, `nohup/timeout 60/uv run/xargs
-I{}/eval python … capture`.

**Zwei Über-Verweigerungen sind mit demselben Rework verschwunden** (vorher rc 2, jetzt rc 0):
ein über eine Fortsetzung umgebrochener **Lesebefehl** (`python scripts/harness.py \⏎ doctor`,
`python -m kernel.cli \⏎ --help`) und ein Trenner **innerhalb von Quotes**
(`echo 'a; python … capture'`). Die Vorfassung dieses Eintrags nannte quotierte Trenner als
Durchlass — das war die falsche Richtung, gemessen war es eine Über-Verweigerung. Ebenso getroffen
war der **erlaubte Planweg**: `cat > project_memory/product/masterplan.md <<'EOF' … EOF` wurde
abgelehnt, weil der Heredoc-Körper als Befehl gelesen wurde; er gilt jetzt als Daten.

**Runde 3 hat vier weitere Durchlässe geschlossen, alle am laufenden Hook gemessen** (vorher rc 0,
jetzt rc 2): die drei Falsch-Heredocs oben; ein **quotierter** Delimiter, dessen Körper mit einem
Markdown-Zeilenumbruch (`\` am Zeilenende) endete — reales bash terminiert dort an `EOF` und führt
die Folgezeile aus, der Leser hatte sie durch sein zu frühes Zusammenziehen verloren; ein
`case`-Muster und ein Funktionskopf in Verbposition (`case x in a) python … capture;; esac`,
`f() { python … capture; }`); und ein **Lesewort an beliebiger Stelle**
(`python scripts/harness.py capture doctor`, `… capture --note "doctor"`), das die ganze Zeile
entwertete.

**Runde 4 hat drei Ränder desselben Reworks geschlossen, alle gemessen.** (R3-1) Endet die
`<<`-**Umleitungszeile selbst** auf einer Fortsetzung, überbrückte das nachträgliche Zusammenziehen
den Schnitt, den das Herausschneiden des Körpers gemacht hatte, und klebte die Ableitung ins
`cat`-Segment (`cat <<'EOF' \⏎ > …masterplan.md⏎…⏎EOF⏎python … capture`, vorher rc 0). Behoben,
indem der Körper durch **gleich viele Leerzeilen** ersetzt wird statt gelöscht — die Zeilenzahl
bleibt, der Join überspannt nichts. (R3-2) Ein `)` in der **Prosa eines quotierten Arguments**
öffnete eine zweite Namensposition, sodass `git commit -m "… (siehe Plan) … python … capture"`
fälschlich rc 2 war; die Tokenisierung respektiert jetzt Quotes, ein quotiertes Wort endet auf `"`
statt auf `)`. (R3-3) Ein Hilfs-Flag in einem **quotierten Wert** (`… capture --body "see --help
…"`) entwertete die Zeile — argparse sieht dort einen Wert, kein Flag; dieselbe quote-respektierende
Tokenisierung schließt das mit, weil `--help` dann kein eigenes Token mehr ist.

**Eine dritte Klasse kam aus dem RPG-Piloten und war bis dahin unbenannt: Selbstabschaltung über
die eigene Vorbedingung.** Der Guard prüft zuerst, ob `.claude/HANDOVER_PENDING` existiert; ist die
Datei weg, ist jeder weitere Aufruf ein No-op. Gemessen am laufenden Hook (Pilot, hier reproduziert):
`rm`, `rm -f`, `del`, `mv`, `Remove-Item`, `Move-Item`, eine Umleitung auf den Marker und die
gewrappte Form waren **alle rc 0**, und ein Produktcode-Write und ein Task-Spawn direkt danach
ebenso. **Gebaut ist jetzt:** ein Segment, das den Marker **beim Namen** nennt, wird verweigert,
sofern sein Verb nicht in einer kleinen **Lese-Allowlist** steht — die Aufzählung läuft hier
absichtlich andersherum als sonst in der Datei, ein unbekanntes Verb wird also **verweigert**, damit
ein nicht gelisteter Leser Reibung kostet und kein nicht gelisteter Entferner den Guard. Alle elf
Entfernungsformen sind jetzt rc 2; `cat`, `ls`, `Get-Content`, `grep`, `test -f` bleiben rc 0.
**Nicht gebaut, gemessen und benannt:** der Marker wird erreicht, **ohne dass sein Name als Wort
vorkommt** — `mv .claude .claude_off`, `rm .claude/HANDOVER*`, `rm -f .claude/*`,
`find .claude -name 'HANDOVER*' -delete`, oder ein per Substitution zusammengesetzter Pfad (je rc 0,
gepinnt). Das zu schließen hieße, das Dateisystem zu modellieren statt Wörter zu lesen.
**Einordnung:** als Angriff **niedrig** — im Piloten hat das Modell die Löschung von sich aus als
direkten Bypass verweigert; als **Dokumentationslücke mittel**, denn der Docstring versprach
„NAMED, unclosed gaps, each measured" und nannte genau diese Klasse nicht.

**Die Kehrseite derselben Regel ist eine Über-Verweigerung, und die ist gewollt (R3-4):** weil ein
unquotiertes Nicht-Lese-Verb mit dem Markerwort verweigert wird, trifft es auch eine Zeile, die den
Marker nur **sichert** oder **erwähnt** — `cp .claude/HANDOVER_PENDING /tmp/backup` und
`git commit -m "docs: explain HANDOVER_PENDING"` sind beide rc 2. Das ist die sichere Richtung: die
Allowlist verweigert im Zweifel, damit kein ungelisteter Entferner durchkommt, und der Preis ist
Reibung auf einer seltenen, gutartigen Zeile bis zum Neustart.

**Eine neue, benannte Über-Verweigerung ist der Preis der Terminator-Bedingung:** ein
Here-Document, dessen Delimiter-Zeile **nicht im selben Werkzeugaufruf** steht, bekommt seinen
Körper als Befehle vorgelegt. Gemessen gegen reales bash: `cat <<EOF⏎python … capture` führt bash
nicht aus, dieser Leser verweigert es (rc 2); ebenso `<<EOF` (unquotiert) mit `\` am Ende der
Körperzeile, wo bash über `EOF` hinaus schluckt. Beide sind mit
`test_handover_guard_over_refuses_an_unterminated_heredoc` festgenagelt, damit der Preis sichtbar
bleibt. Die umgekehrte Richtung wäre ein Loch, und genau das war sie.

**Urteil: Ausnahme, Abnahme offen** — die verbleibende Restklasse (Substitution, ungelisteter
Wrapper, gewrappte Shell, kodiert) ist **bewusst nicht** geschlossen. Sie zu schließen hieße zu
beantworten, was eine Zeichenkette später ausführen wird; das ist das Parser-Kaninchenloch, gegen
das DEC-0029 entschieden hat. Das Bedrohungsmodell (DEC-0032) ist ein **wohlmeinender**
Einstiegsagent, der weiterarbeitet, kein Gegner, der absichtlich verschleiert.

**Was stattdessen begrenzt:** die eigentliche Grenze ist der Neustart selbst — nach ihm sind die
Kit-Gates aktiv und `gate_write_scope`/`gate_dispatch` fangen dieselben Ableitungen strukturell.
Bis dahin ist der Guard ein Gurt, kein Sandkasten (Docstring). **Sozial** ergänzt: der Einstiegsagent
folgt seiner Verfassung, die ihm die Ableitung ohnehin untersagt.

**Rote Tests ohne den Fix.** `test_hooks.py::test_handover_guard_blocks_laundered_engine_calls` —
11 Fälle kamen gegen den Vor-Rework-Hook mit rc 0 statt 2 zurück (drei Fortsetzungen, acht
zusammengesetzte Kommandos); `test_handover_guard_allows_benign_multiline_reads_and_heredoc_bodies`
— 6 Fälle kamen mit rc 2 statt 0. Für Runde 3 ist **jede einzelne Mechanik** in einer Kopie
außerhalb des Repos zurückgebaut und gemessen worden, statt einer pauschalen Behauptung:
Terminator-Bedingung → `unterminated_heredoc`; Umleitungsgrenze →
`false_heredoc_arithmetic_shift_closed`; Kommentar-Abschnitt → `false_heredoc_in_a_comment_closed`;
Reihenfolge (Heredoc vor dem Zusammenziehen) → der Planweg-Fehlalarm
`…masterplan.md <<'EOF'⏎python … capture \⏎EOF⏎ls` (rc 0 gebaut, rc 2 mit der alten Reihenfolge);
zweite Namensposition → `case_pattern`, `function_body`; Lese-Position → `read_word_as_argument`,
`read_word_as_option_value`; Marker-Regel → alle **11** Fälle von
`test_handover_guard_refuses_removing_its_own_marker` (gegen den Klon ohne die Regel rc 0 statt 2),
mit `test_handover_guard_still_lets_the_marker_be_read` als Gegenprobe und
`test_handover_guard_marker_residue_is_named_not_closed` als Pin des Rests. Dazu misst
`test_every_separator_character_is_load_bearing` das andere
Ende der Trenner-Menge über den echten Einstiegspunkt `_handle_shell` (ein eingeschleustes `@` wird
als toter Eintrag gemeldet), und
`test_handover_guard_wrapped_engine_forms_are_the_named_residue` pinnt die Restklasse.
Für Runde 4 ebenso je Mechanik zurückgebaut: Leerzeilen-Ersatz statt Löschung →
`heredoc_redirect_line_continues`(+`_into_a_pipe`) rc 0 statt 2; quote-respektierende Tokenisierung
→ `help_flag_in_a_quoted_value`, `dash_h_in_a_quoted_value` rc 0 statt 2 und der Fehlalarm
`git commit -m "… (…) … python … capture"` rc 2 statt 0.

**Runde 5 (TSK-0054, BUG-0017) — die Approval-Frage-Verweigerung fängt nur den TREUEN Marker-Relay.**
Der Guard verweigert jetzt zusätzlich eine `AskUserQuestion`, deren `tool_input` den Approval-Marker
trägt (`_APR_REQUEST_MARKER = \[APR-REQ:`), damit die Einstiegssitzung den Scope-Approval-Weg nicht
STARTET (der Mint scheiterte dort und der Agent erfand daraus `/hooks` — EVD-0020,
`docs/reviews/2026-08-12-bug0017-live-confirm.md`). Der Marker ist **byte-genau** der des echten
Emitters (`team-kits/kernel/approvals.py` schreibt `[APR-REQ:<id>]`, `gate_approval.py` liest
`\[APR-REQ:<32 hex>\]`), also nicht inert. **Der Rest — dieselbe DEC-0029-Klasse:** gefangen wird nur
ein **byte-treuer, case-exakter** Relay. Eine Halluzination, die den Marker WEGLÄSST oder verstümmelt/
kleinschreibt, ist von einer normalen Frage nicht unterscheidbar und entkommt; die Alternative wäre,
Absicht aus Freitext zu modellieren (gegen die DEC-0029 entschied) und dabei die Einstiegs-Gate-Fragen
mitzuverweigern. Narrow by design; in der Guard-Docstring benannt.

**Live gemessen 2026-08-13** (`docs/reviews/2026-08-13-tsk0054-live-confirm.md`, Rohprotokolle in
`docs/reviews/2026-08-13-tsk0054-live-logs/`): EINE echte Einstiegssitzung reichte die Kernel-Frage
mit byte-treuem `[APR-REQ:<id>]` in `tool_input` durch, der Guard verweigerte sie (rc 2,
`apr-live2.jsonl` Sätze 10/11) — **eine** gemessene Weitergabe, keine Eigenschaft des Weiterreichens;
ob die EVD-0020-Frage der Einstiegssitzung den Marker trug, ist nirgends aufgezeichnet (Rohprotokoll
gelöscht — die frühere Fassung dieses Absatzes behauptete Deckung mit einem Zitat, das nur Phase 2
belegt; korrigiert). Die Verhaltensbestätigung ist im selben Lauf erbracht: der Einstiegsagent erfand
auf dem Fortsetzungspfad kein `/hooks` und keinen Ersatz, sondern bat um den Neustart — auch mit der
`restart_required`-Diagnose vor Augen (ein Modell, ein Lauf; modellabhängige Aussage). Präzisierung
aus dem Lauf: tragend war auf dem natürlichen Pfad die ältere BUG-0016-Shell-Regel
(`request-approval` rc 2); der Marker entsteht ausschließlich im stdout der CLI (die Pending-Datei
trägt ihn nicht, gemessen), der Ask-Zweig wurde darum in vier von fünf Sitzungen gar nicht erreicht.
Er ist der Riegel für Marker-Ankunft auf anderem Weg (Datei, Paste, ungelisteter Wrapper) — zweiter
Riegel, nicht erster.

**Rest desselben Laufs (F2): der `/hooks`-vorschlagende Diagnosepfad — das `hook_trust`-Feld ist
GESCHLOSSEN (TSK-0057/BUG-0036, 2026-08-14), die KLASSE nicht.** Der alte Pauschalsatz („the kit
update is in state %r — a changed bundle needs /hooks confirmation…", für JEDEN Nicht-aktiv-Zustand)
ist ersetzt: der Grund ist zustandsgenau (frische Installation → genau EIN neuer Sessionstart, und
NUR wenn der einlösende SessionStart-Hook wirklich registriert ist — sonst Scaffold-Rat statt
Endlosschleife; verändertes Bundle → die Spec-II.8-Formulierung, die dort korrekt ist), und
Record-Inhalt kann keine eigenen Wörter mehr in den Grund schmuggeln (Form-Eigenschaft: zitiert wird
nur, was wie Name/Hash geformt ist; alles andere wird beschrieben). Elf Tests rot ohne den Fix,
Prüfer-PASS mit 1008-Zeilen-Nachweis, dass das grüne Urteil unverändert blieb; Messtabelle in
`docs/reviews/2026-08-13-tsk0057-kit-state-measurements.md`. **Bewusst NICHT übernommen** wurde der
hier früher vorgeschlagene Wortlaut „restart — /hooks is not part of this flow": eine Verneinung
trägt den Token selbst hinein; der Neustart-Zweig nennt ihn gar nicht (derselbe Präzedenzfall wie
die Marker-Zeichenkette in `CLAUDE.md`).

**Was von der Klasse offen bleibt — „ein ausgelieferter Text reicht dem Einstiegsfenster einen
`/hooks`-Schritt", Träger gemessen 2026-08-14:** die Codex-Hinweiszeile in `environment_notes`
(`team-kits/kernel/report.py:2245-2248`; ob `/hooks` für die Codex-Fläche überhaupt der richtige
Schritt ist, ist UNGEMESSEN — auf Verdacht umschreiben hieße eine vielleicht wahre gegen eine sicher
ungemessene Aussage tauschen) und die Codex-Abschlusszeile des Scaffolds
(`team-kits/gen_provider_artifacts.py:1313`); dazu `report.py:2118` als der von Spec II.8
legitimierte Träger (verändertes Bundle). Nachbarreste derselben Runde: das `kit`-Feld aus
`kit_state.json` ist das letzte wörtliche Record-Echo der doctor-Fläche (O1,
`report.py:1974-1975`), und `kit_trust_state.py:23-27` behauptet einen fehlenden Ausgang, den
`transition()` hat — als **BUG-0037** erfasst. Beide mit Messung im Review-Dokument.

### L40 — Ein Subagent erreicht `set-preset`: die Subagenten-Regel kennt nur die Klasse „bestellt Arbeit" (TSK-0064)

**Mechanismus, als Eigenschaft:** Mit TSK-0064 (`BUG-0041`) hat der Kernel einen Befehl bekommen,
der die **Durchsetzungsschicht neu installiert** — `set-preset` schreibt `project.preset` und fährt
das Scaffold, das Rollen nach `.claude/agents` legt —, ohne Arbeit zu bestellen. Die
Subagenten-Regel von `gate_write_scope` (Regel 4) erkennt aber genau die Klasse „bestellt Arbeit":
`_ORDERING_COMMANDS` ist aus den CLI-Routen abgeleitet, die `create_task`/`create_lease` erreichen,
und `set-preset` erreicht keines von beiden. Die Ableitung ist damit **intakt und zu eng zugleich**
— eine neue Befehlsklasse (installiert Durchsetzung, bestellt nichts) liegt außerhalb ihrer
Definition.

**Kette (Prüfer der TSK-0064-Runde, 2026-08-15, echte Hook-Prozesse gegen die 8 registrierten
`Bash|PowerShell`-PreToolUse-Hooks eines gescaffoldeten Projekts, aus dessen eigener
`settings.json` gelesen):** als Subagent ist `python scripts/harness.py set-preset team` und
`… request-approval preset --preset …` bei **allen 8 Hooks** durchgelassen, während `create-task`
für denselben Subagenten rc 2 ist (Regel 4 arbeitet für ihre Klasse). Was ein Subagent damit
erreicht: eine vom Nutzer signierte, noch nicht angewandte Änderung zum **selbstgewählten
Zeitpunkt** auslösen (einschließlich des Entfernens von Peer-Rollen), und eine
**Upgrade**-Freigabe (leeres `removes`) innerhalb ihrer Stunde beliebig oft wiederholen —
gemessen: zweiter und dritter Lauf rc 0, je ein voller Scaffold-Lauf mit neuem
Backup-Verzeichnis, `kit_state: restart_required`, `.claude/HANDOVER_PENDING`. Was er NICHT
erreicht, ebenfalls gemessen: einen anderen **Inhalt** als den signierten — Freigabe A gegen
Preset B, Rollendrift zwischen Mint und Set, abgelaufene Freigabe sind alle verweigert (der Hash
deckt das Ergebnis).

**Begrenzung, und ihre eigene Grenze:** sobald `.claude/HANDOVER_PENDING` steht, verweigert der
**nutzerglobale** `handover_guard.py` weitere Läufe (rc 2 für beide Befehle, rc 0 für `doctor`).
Dieser Riegel ist aber kein Kit-Hook — ein Projekt ohne die globale Datei hat ihn nicht —, und er
trägt seine eigenen benannten Reste (L39: die Verbposition, die ein Wrapper besetzt; gemessen sind
einzelne Wrapper-Schreibweisen rc 0, eine Kommandoersetzung rc 2).

**Urteil: Rest mit gemessener Kette, kein Inhalts-Loch.** Die Autorisierung selbst ist die APR des
Nutzers und deckt das Ergebnis; was der Subagent kontrolliert, ist **Zeitpunkt und Wiederholung**
einer signierten Änderung, nicht ihr Inhalt. Die Reparaturstelle ist die Subagenten-Regel der
Kits: die abgeleitete Klasse um „installiert die Durchsetzungsschicht" erweitern (aus derselben
Quelle abgeleitet, aus der `set-preset` seine Wirkung bezieht) — eine Kit-Runde, kein Repo-Gate.

### L41 — Was die Fehlermeldungen von `set-preset` nicht wissen: Skills und Provider-Artefakte im Abbruchfenster (TSK-0064)

**Mechanismus:** Nach einem abgebrochenen oder verweigerten Installationslauf liest der Kernel
zwei Dinge neu — das Besitzverzeichnis `.claude/team_kit_roles.txt` und die Rollendateien
`.claude/agents/<rolle>.md`, die es nennt (`kernel/presets._installed_state`). **Nicht** neu
gelesen werden `.claude/skills/<rolle>/`, die generierten Provider-Artefakte
(`.codex/agents/*.toml`, `.codex/hooks.json`, `.agents/skills/`) und Rollen-Artefakte, die diese
Installation nicht besitzt. Ein Abbruchfenster kann diese ungelesenen Teile in **beide**
Richtungen verfehlen: Artefakte fehlen, oder überzählige bleiben zurück.

**Kette (gemessen 2026-08-15, echtes Scaffold, Abbruch nach 1,5 s):** Prüfer der TSK-0064-Runde,
zweimal unabhängig — die Rollen waren zurück und beide Leser einig, während `.claude/skills` von
sieben Verzeichnissen auf **null** gefallen war; der Satz darüber lautete vor dem Fix „nothing is
missing". Umsetzer, Wiederholung derselben Frist — die Spiegelform: Besitzverzeichnis nennt fünf
Rollen, `.claude/agents` hält neun, `.claude/skills` sieben (Reste des halb installierten
Satzes). Beides räumt der **nächste vollständige Installerlauf** auf, er prunet nach demselben
Verzeichnis — kein dauerhafter Verlust.

**Urteil: Rest mit gemessener Kette, geschlossen ist die EHRLICHKEIT, nicht die Messung.** Seit
TSK-0064 tragen alle drei Ausgangs-Meldungen die Grenze im Klartext (`kernel/presets.UNREAD`, in
beiden Richtungen: fehlend *und* übrig) statt Vollständigkeit zu behaupten; der unbedingte Satz
ist von `test_the_outcome_messages_carry_the_limit_of_what_was_re_read` in beiden Fenstern rot
gedeckt. Wer die Skills wirklich prüfen will, lässt den Installer noch einmal laufen. Die
Schließrichtung — `_installed_state` liest auch Skill-Verzeichnisse und Provider-Artefakte —
ist eine Kit-Runde und lohnt erst, wenn das Fenster in der Praxis trifft (Pilot 4 beobachtet
den Preset-Fluss).

## 12. Löcherliste der vier Repo-Gates (Stand 2026-08-05, aus der Prüfung von TSK-0003)

Andere Baustelle als Abschnitt 11: dort geht es um die **ausgelieferten Kits**, hier um die vier
`PreToolUse`-Gates, die *dieses* Repo statt eines Kits durchsetzen (`SR-0009` — bis 2026-08-13
`SR-0006` —, `DEC-0003`).

Die Trennlinie, nach der hier entschieden wird, ist **eine Regel und keine Abwägung**:

> Eine Lücke, deren Angriffskette **innerhalb einer Sitzung** durchläuft, ist **blockierend**.
> Blockierend heißt: **geschlossen** — oder mit einer **benannten, vom Nutzer abzunehmenden
> Ausnahme**, die sagt, **warum** sie nicht schließbar ist und **was stattdessen begrenzt**.

Die zweite Hälfte ist seit TSK-0008 dabei, weil die erste allein einen dritten Zustand offenließ,
in dem drei Löcher hier je drei Runden überlebt haben: „blockierend, benannt, unverändert". Den
gibt es nicht mehr. Ein offener Eintrag unten ist entweder **geschlossen**, oder er trägt eine
**Ausnahme**, die auf die Abnahme des Nutzers wartet — und dann steht dort, was an die Stelle des
Schutzes tritt. Dieselbe Regel steht in `CLAUDE.md`.

Jeder Eintrag nennt darum drei Dinge: den **Mechanismus** (nicht die Schreibweise, mit der er
zufällig vorgeführt wurde), die **gemessene Kette** und ein **Urteil**. Die Kette steht im Eintrag
selbst; wo ein **Messprotokoll** unter `docs/reviews/` sie ausführlicher trägt, nennt der Eintrag
es — und dann trägt jenes Dokument den Eintrag auch unter seiner Nummer.
Bis 2026-08-05 stand hier stattdessen eine Zuordnung nach Nummernbereichen („H16–H23 in
`…tsk0011…`"); drei der genannten Einträge kamen dort nicht vor. Ein Verweis, den niemand prüft,
ist eine Behauptung wie jede andere — `test_gates.py::test_every_reference_to_a_measurement_leads_to_one`
prüft ihn jetzt.
H1–H10 entsprechen R1–R10 des Prüfberichts zu TSK-0003, H11–H15 kamen mit TSK-0007 dazu, H16–H18
mit TSK-0008, H19–H23 mit TSK-0011, H24–H28 mit TSK-0013, H29 mit TSK-0015, H30 mit TSK-0017,
H31–H32 mit TSK-0019, H33–H36 mit TSK-0021, H37–H38 mit TSK-0022, H39 mit TSK-0055, H40 mit
TSK-0058, H41 mit TSK-0009, H42 mit TSK-0033, H43 mit TSK-0033, H44 mit TSK-0062, H45 mit
TSK-0063.

Ein **geschlossener** Eintrag, dessen roter Test die gekreuzte Tabelle in `test_gates.py` ist, nennt
zusätzlich die **Zellen** dieser Tabelle, auf denen er steht — die von Hand geschriebenen Werte ihrer
Achsen. Der Grund ist gemessen (2026-08-07): ohne diese Kopplung ließ sich die Prüfmenge von 1440
auf 100 Zellen zusammenstreichen, ohne dass ein einziger Test dieser Datei rot wurde. Die
Stolperdrähte deckten die **erzeugten** Achsen, nicht die geschriebenen Werte.
`test_gates.py::test_every_cell_a_closed_hole_names_is_one_the_table_carries` prüft beide Enden.

**Die offenen Einträge auf einen Blick, mit dem Zustand nach der zweiten Hälfte der Regel:**

| # | Zustand | Was an die Stelle des Schutzes tritt |
|---|---|---|
| H2 | **GESCHLOSSEN** (TSK-0056), mit benannten Resten | Gate 3 urteilt über die Eigenschaft „autoriert/installiert einen Commit" statt über das Wort `commit`; Vertrag zuerst (`SR-0006`→`SR-0009`, DEC-0042); Aufzählung mit Stolperdraht gegen das installierte git; Reste: Import-Objekt (mehrschrittig, kein Ein-Aufruf-Loch), Über-Verweigerungen mit Weg durch, H11-Interpreterklasse |
| H7 | **Ausnahme, Abnahme offen** | Gate 4 prüft Form, nicht Deckung; die Reparaturstelle liegt im Kernel (`AUTOMATA` ohne `done_states`) |
| H11 | **Ausnahme, Abnahme offen** | **nichts Technisches.** Gemessen 2026-08-05: `.claude/settings.json` `permissions` trägt genau `deny: ["Agent(harness-lead)"]` und begrenzt die Shell nicht. Die Begrenzung ist **sozial** — Rollentrennung und Item. Eine wirksame Berechtigungshaltung wäre der Schnitt, ist aber eine Nutzerentscheidung und heute nicht gebaut |
| H12 | **Ausnahme, Abnahme offen** | nichts liest heute einen `allowed_scope`; wer `.claude/` schreiben darf, schreibt auch die Gates — ebenfalls **sozial** |
| H16 | **Ausnahme, Abnahme offen** | dieselbe Lage wie H11: **sozial, nicht technisch**. Die Pfad-Hälfte ist offen; von der `cd`-Hälfte ist die Bewegung geschlossen, nicht der Pfad in der Variablen |
| H21 | **Ausnahme, Abnahme offen** | dieselbe Kette wie H16 und dieselbe Begrenzung: **sozial**. Ohne Variable greift heute ein Nebengrund (die Zeile nennt den Repo-Pfad wörtlich), und ein Nebengrund ist keine Maßnahme |
| H22 | **Ausnahme, Abnahme offen** | **nichts Technisches**, dieselbe Begrenzung wie H11 — die Reparaturstelle liegt in der Read-only-Klassifikation der Kits |
| H25 | **Ausnahme, Abnahme offen** | dieselbe Lage wie H12, von der sie abhängt: wer `.claude/` schreiben darf, setzt die Frist hoch, die sich ein Gate zugesteht. **Sozial** — Rollentrennung und Item |
| H13, H14, H15, H18, H19, H23 | **Rest**, keine Angriffskette | jeweils dort benannt; H18/H19/H23 sind Über-Verweigerungen, also Reibung statt Loch, und H13/H14/H15 nennen in ihrem Eintrag, was an der Stelle steht |
| H36 | **Rest**, keine Angriffskette auf diesem Host | die Grenze ist gemessen und liegt außerhalb des Gates: die Zeilenlänge, ab der die nicht unterbrechbare Stelle die Frist reißt, kann auf diesem Host keine Shell mehr gestartet bekommen. Der Eintrag nennt, was das ändern würde |
| H32 | **Ausnahme, Abnahme offen** | geschlossen bis auf eine Hälfte, und die ist ein Sonderfall von H34: was die Kits als Prosa entfernen, liest davor niemand. **Sozial** — Rollentrennung und Item; die Reparaturstelle liegt im Kit |
| H34 | **GESCHLOSSEN** (TSK-0043), mit benannter Resthälfte | die Prosa-Entfernung der Kits ist an das **Verb** gebunden (`gate_write_scope._VerbBoundMessageRemoval`/`_stage_takes_a_message`) statt an die Flagschreibweise; der Datenverlust-Kern (`rm -f "geschützt"`, `cp -b "geschützt"`) ist zu, und weil `_harness._prose_removed` dasselbe Objekt importiert, auch das Repo-Gate, das DEC-0001 löschte. Rest: die Ersetzung IN einer echten Nachricht bleibt H32; sie zu lesen wäre die Drift H15 |
| H3 | **GESCHLOSSEN**, mit benannter Resthälfte | die Hälfte, die bleibt, ist der Fixpunkt der Konstruktion und im Eintrag beschrieben: der Digest schließt `project_memory/` aus, weil ein Urteil sonst den Baum decken müsste, in den es geschrieben wird |
| H9 | **kein Urteil möglich** | nichts, und das ist der Befund: ohne den Mechanismus aus dem Prüfbericht zu TSK-0003 gibt es keine Kette, die man einordnen könnte. Der Eintrag wartet auf diese Eingabe, nicht auf eine Entscheidung |
| H10 | **Rest**, offen ist nur die Vollständigkeit | die beiden gefundenen Hälften sind geschlossen und je durch einen roten Test gedeckt; für die dritte gibt es keinen Ersatz, sondern eine ungestellte Frage — ein erschöpfender Mutationslauf über `.claude/hooks/` |
| H37 | **GESCHLOSSEN**, mit benannten Resten (Rest 1–5 im Eintrag) | für den Mechanismus des Eintrags steht Code (`.claude/hooks/_sandbox.py`, drei Tests). Die Reste liegen sämtlich in der **Messvorrichtung**, nicht im Schutz der Gates, und jeder nennt seine Begrenzung: Rest 1 (nicht importiert = unbewacht), Rest 2 (`_audit.record_event` der Kits schreibt `project_memory/.audit/` dieses Repos — Reparaturstelle im Kit, Begrenzung **sozial**), Rest 3 (die Namensliste bleibt eine Aufzählung; `BASH_ENV` gemessen offen), Rest 4 (`watch` sieht keine Neuanlage), Rest 5 (`_inside` kanonisiert die Win32-Namensräume nicht — Gate 1 selbst ist nicht betroffen) |
| H38 | **Ausnahme, Abnahme offen** | **nichts Technisches** für den Schreibzugriff — dieselbe Begrenzung wie H34: die Prosa-Entfernung ist die der Kits (`gate_write_scope._HEREDOC_RX`). Gemessen begrenzt ist nur die Commit-Hälfte: steht der Commit auf derselben Zeile, verweigert Gate 3 sie wegen des Verbs. **Sozial** — Rollentrennung und Item |
| H39 | **Ausnahme, Abnahme offen** | kein Angriffsloch, eine Erreichbarkeitslücke der Buchführung: DEC-0041 trägt die Bedeutung von `CANCELLED`, und die Bugliste bleibt sichtbar statt leergelogen; ein Münzweg wäre eine eigene Runde mit eigener Sicherheitsabwägung |
| H40 | **Ausnahme, Abnahme offen** | der Stolperdraht gegen Zitationen abgelöster Verträge liest die `.py`-Quellen von `.claude/hooks/` — Registrierung, Rollendefinitionen, `CLAUDE.md` und `docs/` liest kein Draht; die eine gemessene Lebendzitation steht im Eintrag, ihre Behebung liegt außerhalb des TSK-0058-Scopes |
| H41 | **Rest**, keine Angriffskette | vier gemessene Grenzen des Zeiger-Wächters aus TSK-0009, je im Eintrag; keine berührt eine Gate-Entscheidung. Der lebende Bestand ist in den ersten drei Richtungen leer; die vierte (Zeiger auf Tests ANDERER Dateien, vom Leser übersprungen) trägt heute zehn Vorkommen — sieben aus dem H43-, drei aus dem H44-Eintrag —, alle von Hand aufgelöst |
| H42 | **GESCHLOSSEN** (TSK-0060, `DEC-0043`), mit benannten Resten | der Vertrag ist entschieden statt normalisiert: `INV.scope` regiert genau einen Bereich, `backlog_types.SINGLE_VALUE_FIELDS` deklariert das, `state._assert_single_value_fields` verweigert die Mehrere-Dinge-Form an beiden Türen in den aktiven Zustand und `report._check_single_value_fields` meldet sie als Fehler (gemessen: capture/update verweigert, `validate` 0 → 1 Fehler, `gate_memory_complete` rc 0 → rc 2). Die vier Leser sind unverändert. Reste: ein schon geschriebenes Item wird gemeldet statt geheilt, die Archiv-Tür nimmt die Form weiter an (DEC-0009), die Deklaration ist nicht abgeleitet, und im `office-team` schützt sie keinen Leser |
| H43 | **GESCHLOSSEN** (TSK-0059, `BUG-0038`), mit benannten Resten | die Grenze ist jetzt abgeleitet statt unsichtbar: `backlog_types.REFERENCE_LIST_FIELDS` nennt die Felder, die kein Capture-Vertrag deklariert und deren Elemente der Kernel auflöst, mit einem Stolperdraht über die laufenden Quellen an beiden Enden; alle sieben Lesestellen gehen durch `field_elements` (gemessen: 2 statt 35 Einträge im aktiven PR, Dispatch von REFUSED auf ALLOWED, `validate` von 17 auf 3 Befunde). Reste: der Skalar wird benannt statt abgewiesen, ein bereits beschädigtes Item wird gemeldet statt geheilt, und die Ableitung sieht keinen Leser hinter einem Rückgabe-Objekt — je im Eintrag |
| H44 | **Rest**, keine Angriffskette | vier gemessene Grenzen der Amendment-Ableitung aus TSK-0062, je im Eintrag: die Kriterien eines ANGEWENDETEN Änderungsantrags zählen nicht mehr (Über-Verweigerung, per Test festgehalten); die Zugehörigkeit (`target_pr`) ist nicht signiert (durch den Kernel geschlossen, offen nur vorbei an ihm — und diese Sitzungstür hält Gate 1 zu); `target_revision` wird nie als Wert verglichen (leiht ausschließlich nutzersignierten Inhalt); Hop 1 bleibt für Nicht-Amendments ohne Freigabeterm (Design, H39 — die Amendment-Hälfte ist seit dieser Runde zu) |
| H45 | **Rest** bzw. entschiedene Über-Verweigerung | zwei gemessene Grenzen der Arbiter-Härtung aus TSK-0063, je im Eintrag: die Sitzungswache verlangt die Seh-Eigenschaft auch von shell-freien Registrierungs-Prüfungen (fail-closed, auf diesem Host ohne Effekt; Schließrichtung benannt), und `_can_arbitrate` ist von keinem Test rot-fähig gedeckt (die entfernte `cd`-Probe ist unbeobachtet — H10-Klasse) |
| H1, H4, H5, H6, H8, H17, H20, H24, H26, H27, H28, H29, H30, H31, H33, H35 | **GESCHLOSSEN** | — |

### H1 — Der Digest beschreibt den Baum vor der Zeile, nicht den, den der Commit aufzeichnet — GESCHLOSSEN

**Mechanismus:** ein `PreToolUse`-Hook wird *vor* der Zeile gefragt. Jede Befehlszeile, die vor dem
`commit` noch irgendetwas am Baum tut, lässt den Commit einen Zustand aufzeichnen, den kein Urteil
je gesehen hat. Nicht `&&` ist der Mechanismus, sondern **jede** Verkettung, jede Umleitung, jeder
schreibfähige Befehl davor.

**Kette (gemessen):** Urteil aufgezeichnet → `git commit -m wip` rc 0 → dann
`echo more >> docs/note.md && git commit -m wip` **rc 0**.

**Zweite Hälfte derselben Kette, gemessen 2026-08-05
(`docs/reviews/2026-08-05-tsk0015-measurements.md`, Abschnitt 4):** eine **Pipe** ist keine
Ordnung — die Stufen laufen nebeneinander. `sed -i "s/a/b/" docs/note.md | git commit -m wip` und
`(echo more >> docs/note.md)|git commit -m wip` waren **rc 0**, weil nur die Pipelines *vor* der
committenden geprüft wurden.

**Dritte Hälfte derselben Kette, gemessen 2026-08-07
(`docs/reviews/2026-08-07-tsk0017-measurements.md`, Abschnitt 3):** die **Umleitung der committenden
Stufe** ist keine Stufe, sondern die Shell — und die richtet sie **vor** `git` ein. Mit gültigem
Urteil im Baum war `git commit -am wip > docs/note.md` **rc 0**; Ende zu Ende gemessen war
`docs/note.md` danach leer und der Commit zeichnete `docs/note.md | 1 -` auf, weil `-am` die
gekürzte Datei mitnimmt. Geprüft wurden bis dahin nur die Umleitungen der Stufen, die den Commit
**nicht** tragen — und die committende Stufe war genau die eine, die aus dieser Liste fiel.

**Urteil: blockierend, geschlossen.** `gate_commit_evidence._moves_the_tree_first` verlangt, dass
jede Pipeline **vor** der committenden nur lesend ist (Klassifikation der Kits, nicht eine zweite) —
seit TSK-0015 auch jede **Stufe der committenden Pipeline außer der, die den Commit trägt**, und
seit TSK-0017 die **Umleitungsziele der ganzen committenden Pipeline**, die tragende Stufe
eingeschlossen: nur ihr **Verb** ist der Commit. `git add -A && git commit` bleibt offen — der
Digest ist `diff HEAD` und deckt Staged wie Unstaged; ebenso eine lesende Stufe, die dem Commit
etwas zuführt (`echo wip | git commit -F -`), und eine Umleitung in das Verwerfungsgerät
(`git commit -m wip > /dev/null`). Rot ohne den Fix:
`test_gate3_refuses_a_line_that_moves_the_tree_before_it_commits`.

**Was offen bleibt, und das ist eine Grenze und keine Vollständigkeit:** dieser Eintrag deckt, was
die Read-only-Einstufung der Kits **sieht**. Ein Schreibzugriff, den sie als lesend führt, geht
durch — gemessen 2026-08-07 mit gültigem Urteil im Baum:
`sed -n "w docs/note.md" radar/note.md ; git commit -m wip` ist **rc 0**, und die Zeile
überschreibt `docs/note.md` wirklich (H22 ist die Stelle, `gate_write_scope` nennt sie im eigenen
Docstring). `CLAUDE.md` sagte dazu bis TSK-0017 „und **jede** Zeile, die den Baum vor dem Commit
noch ändert" — eine Zusicherung, die der Code nicht baut; die Zeile nennt jetzt die Stelle, die
entscheidet. Beide Enden der Grenze misst
`test_gate3_sees_what_the_kits_classification_calls_a_write_and_no_more`, den Zeiger selbst
`test_the_constitution_names_only_code_that_exists`.
Und eine Zeile, deren Commit der Leser nicht *verorten* kann (Wrapper-Payload, unauflösbares Verb),
wird als „die ganze Zeile muss lesend sein" behandelt, also eher zu streng.
`python x.py && git commit` wird verweigert, obwohl das Skript vielleicht nichts schreibt — von
einer Kommandozeile aus ist das nicht entscheidbar (siehe H11).

**Vierte Hälfte derselben Kette, gemessen 2026-08-07 (`docs/reviews/2026-08-07-tsk0019-measurements.md`,
Abschnitt 3):** ein Befehl, den eine **Kommandoersetzung** in der committenden Stufe einführt. Die
Stufe wird als Ganzes verworfen, und eine Ersetzung ist weder ihr Verb noch ihre Umleitung. Mit
gültigem Urteil im Baum war `git commit -am wip $(sed -i s/prose/POISON/ docs/note.md)` **rc 0**,
`docs/note.md` trug danach `POISON`, HEAD bewegte sich und der Commit trug es. Geschlossen über
`_harness.command_line`; der Eintrag mit der vollen Kette und der offen bleibenden Hälfte ist **H32**.

**Was die zweite Hälfte kostet, gemessen:** eine Stufe, die die Kits nicht als lesend führen,
verweigert jetzt auch **neben** einem Commit — `git commit -m wip 2>&1 | tee /dev/null` ist rc 2,
obwohl dorthin nichts geschrieben wird. Das ist die Klassifikationsgrenze aus H22 in einer neuen
Stellung, also Reibung und kein Loch.

**Und eine dritte Reibung, bis 2026-08-07 in keinem Eintrag genannt:** eine Umleitung der
committenden Stufe wird verweigert, **auch wenn ihr Ziel außerhalb des Arbeitsbaums liegt** und der
Digest es darum gar nicht liest. Gemessen mit gültigem Urteil im Baum:
`git commit -m wip > <außerhalb>/log.txt` ist **rc 2**. Enger fassen ließe sich das nur, indem Gate 3
für jedes Umleitungsziel entscheidet, ob es im Baum liegt, den der Digest deckt — machbar, aber
heute nicht gebaut; die verweigernde Richtung ist die sichere. **Reibung, kein Loch.**

### H2 — Nur das Literal `commit` — GESCHLOSSEN (TSK-0056, BUG-0034), mit benannten Resten

**Mechanismus (war):** Gate 3 fragte `Invocation.runs("commit")`. Die Eigenschaft, um die es geht,
ist aber „**diese Zeile kann einen Commit in die Branch-History autorieren oder installieren**", und
die trifft auch `merge`, `revert`, `cherry-pick`, `am`, `rebase`, `pull`, `stash`, die Klempnerei
(`commit-tree`, `hash-object -t commit`, `fast-import`) und jede Kette, die eines davon per
Kommandoersetzung mit einem Ref-Move verbindet.

**Kette (gemessen, vor dem Fix):** `git merge --no-ff other` **rc 0**, `git revert --no-edit HEAD`
**rc 0** — mit gültigem Urteil im Baum wie ohne. Ein Commit entstand, ohne dass ein Beweismittel
gefragt wurde.

**Vertrag zuerst:** `SR-0006` sagte wörtlich „Kein **Commit**"; die Erweiterung war damit eine
**Vertragsänderung**. `SR-0006` ist durch **`SR-0009`** abgelöst (DEC-0042, DEC-0007), das die
Eigenschaft als „keine Aufzeichnung von Historie ohne Urteil" definiert: gelesen am **Autor-Ende**
(nicht am Ref-Move, weil beide eine Zeile sein können), inklusive der Klempnerei, die ein
Commit-Objekt schreibt; eine Produce-First-Form (`--no-commit`) ist **nur** ausgenommen, wo sie das
Aufzeichnen für **jede** Schreibweise und Konfiguration derselben Invocation unterdrückt.

**Wie geschlossen (TSK-0056):** `gate_commit_evidence.py` verweigert jedes historyschreibende Verb
außer `commit` mit einer Abhilfe, die den Produce-First-Weg nennt (erst ohne Aufzeichnen erzeugen,
Urteil holen, über `git commit` festschreiben); der Commit-Pfad bleibt exakt so beweisgebunden wie
zuvor. Die Menge ist eine Aufzählung **mit Stolperdraht gegen das installierte git** (git benennt
sie selbst nicht treu — `--list-cmds=list-history` über- und unterzählt, gemessen): jeder Eintrag
autoriert nachweislich Historie, und ein fehlender Autor macht einen Test rot. Der normale Weg zum
Commit (`branch`, `checkout -b`, `switch`, `fetch`, `status`, `diff`, `add`) bleibt offen. Zwei
Prüferrunden: F1 (Klempner-Autor `hash-object`) und F2 (`pull --no-commit --rebase` schaltete das
Aufzeichnen wieder ein) waren im ersten Bau noch offen und sind geschlossen; die Ketten sind rc 2,
jeder Fix durch einen ohne ihn roten Test gedeckt (F1: 4 rot, F2: 8 rot).

**Urteil: GESCHLOSSEN mit benannten Resten.** Die gemessenen Ketten sind rc 2, jeder Fix durch
einen ohne ihn roten Test gedeckt, der Vertrag zuerst geändert; offen bleiben nur die unten
benannten Reste, keiner davon ein Ein-Aufruf-Fälschungsweg.

**Benannte Reste (keiner ein Ein-Aufruf-Loch):**

- **Import/Fremdautor-Objekt:** `unpack-objects`, `index-pack`, `clone`, `bundle` installieren ein
  **anderswo** autoriertes Commit-Objekt; `update-ref`/`branch -f`/`reset --hard`/`checkout -B`
  (offen per AC-2) machen daraus Branch-History. **Begrenzung:** das Objekt muss vorher existieren,
  und es in einem zweiten Repo per Werkzeugaufruf zu autorieren verweigert dasselbe Gate (jedes
  autorierende Verb ist verweigert, egal welches `-C`) — kein Ein-Aufruf-Fälschungsweg. Dieselbe
  Klasse wie `fetch`; Einfalten wäre fail-closed möglich, über-verweigert aber legitimen
  Pack-Empfang. Design-Note §8.1.
- **Über-Verweigerungen (fail-closed, Reibung statt Loch):** `merge --ff-only`, `merge --squash`,
  `merge/rebase/cherry-pick/am --abort`, `pull --no-commit --no-rebase`, `hash-object -w <blob>`,
  `stash list|show|pop`, `notes list`, sowie die Reader-Übertriggerklasse (`ls git*`,
  `echo git$VERSION`, unquotierte Prosa `echo run git merge later`). Jede trägt einen begehbaren
  Weg durch (z. B. `git merge --no-commit --ff-only …`, `git reset --hard` statt `--abort`,
  Quotierung der Prosa). Design-Note §8.2.
- **Interpreter-Klasse (H11):** `submodule foreach '<git …>'`, `bisect run <script>`, ein
  handgebautes Packfile für `index-pack` — Code, den kein Gate liest; unverändert benannt.
- **Zeitmessungstest unter Last:** `test_gate3_answers_before_its_registration_however_costly…`
  wurde in Runde 1 knapp lastabhängig; jetzt auf die volle Registrierung dimensioniert mit einem
  `BUG-0033`-Zeiger an der Assertion.

### H3 — `project_memory/` war für Werkzeuge offen — GESCHLOSSEN, mit einer benannten Resthälfte

**Mechanismus:** Gate 3 urteilt anhand eines `EVD`-Items, das *im Zustand* liegt. War der Zustand
mit Werkzeugen schreibbar, schreibt sich der Urteilende sein Urteil selbst.

**Kette (gemessen):** `Write project_memory/evidence/active/EVD-9999.yaml` mit `result: pass` und
dem aktuellen Digest **rc 0** — als Sitzungsagent *und* als Subagent; `git commit` danach offen.

**Urteil: blockierend, geschlossen.** Gate 1 verweigert den kanonischen Teil von `project_memory/`
**jedem** Aufrufer; `staging/**` bleibt offen (Spec II.4: ausdrücklich nicht-kanonisch). Das ist die
Regel, die die Kits ohnehin durchsetzen (`gate_write_scope`).

**Resthälfte, offen:** der Digest **schließt `project_memory/` aus** — er muss das, sonst könnte kein
Urteil je den Baum decken, in den es geschrieben wird. Folge: ein Commit trägt Zustandsänderungen
mit, über die kein Urteil etwas sagt, einschließlich eines archivierten Items, auf das das
Beweismittel zeigt. Das ist der Fixpunkt dieser Konstruktion und kein Defekt; schließen ließe es
sich nur mit einem Ablageort für Beweismittel **außerhalb** des Zustands.

### H4 — Ein Pfad hat mehr als einen Namen — GESCHLOSSEN, in zwei Stufen

**Mechanismus:** der geschützte Bereich wurde als **Text** verglichen. Jede zweite Schreibweise
desselben Pfades ist damit ein Weg daran vorbei — und Windows kennt mehrere, keine davon mit
Sonderrechten: eine Verzeichnisverbindung (`mklink /J`), die Langpfad-Form `\\?\`, die
Administrativ-Freigabe `\\localhost\C$\`, deren `\\?\UNC\`-Form und der 8.3-Aliasname.

**Kette (gemessen, TSK-0007):** `mklink /J kits team-kits` → `Write kits/dev-team/hooks/gate_git.py`
**rc 0**, während `team-kits/dev-team/hooks/gate_git.py` rc 2 bekam. `realpath` schloss das.

**Kette (gemessen, TSK-0008):** `realpath` schließt nur die Junction. Von **elf gemessenen
Aufrufen** über die Präfixformen — `Write` auf Kit-Datei, kanonischen Zustand und Gate-Datei in
`\\?\` und `\\localhost\C$\`, dazu `\\?\UNC\`, PowerShell `Set-Content` und `sed -i` — kamen
**neun mit rc 0 durch**, während dieselbe Datei einfach geschrieben rc 2 bekam. Einer der beiden
Treffer war Zufall: der `$` in `C$` zerlegt die Teilzeichenkettensuche und ließ einen
laufwerksrelativen Rest übrig, der zufällig auf dieselbe Datei zeigte.

**Urteil: blockierend, geschlossen — und zwar als Eigenschaft statt als Präfixtabelle.** „Dieselbe
Datei" ist, was das Dateisystem sagt: gemessen liefern alle fünf Schreibweisen derselben Kit-Datei
**ein** Paar `(st_dev, st_ino)`, während `realpath` Präfix und UNC-Host stehen lässt. `_harness`
vergleicht darum die **Identität** des tiefsten existierenden Vorfahren plus den textlichen Rest
darunter (`_anchored`, `_ancestor_identities`, `under`) — das deckt Junction, Symlink, `\\?\`,
`\\?\UNC\`, Admin-Freigabe, 8.3 und `subst` mit einer einzigen Frage, und es beantwortet weiterhin
den Pfad, den es **noch nicht gibt** (eine neue Kit-Datei), über seine Position.
Rot ohne den Fix: `test_gate1_refuses_a_protected_path_however_the_filesystem_spells_it`;
die Gegenrichtung (kein freier Pfad wird durch eine zweite Schreibweise geschützt) misst
`test_gate1_reads_a_free_path_as_free_in_every_spelling`.

### H5 — `settings.local.json` war ungeschützt — GESCHLOSSEN

**Mechanismus:** der Vertrag zählt `.claude/hooks/` und `.claude/settings.json` auf. Der Provider
liest aber **das Verzeichnis** — Berechtigungs-Overlay und Rollendefinitionen eingeschlossen.

**Kette (gemessen):** `Write .claude/settings.local.json` **rc 0**.

**Urteil: blockierend, geschlossen** — indem eine Eigenschaft an die Stelle der Aufzählung tritt:
geschützt ist `.claude/` als das, *woraus der Provider ableitet, was läuft, wer läuft und was er
darf*.

### H6 — Eine Nutzlast, die ein Gate nicht lesen kann, war ein Ja — GESCHLOSSEN, Erreichbarkeit ungemessen

**Mechanismus:** drei frühe `return`s lasen „nichts zu prüfen" statt „konnte nicht geprüft werden".

**Kette (gemessen, am Gate):** `{"tool_name":"Write","tool_input":{}}` **rc 0**; ebenso ein
Shell-Payload ohne `command` und ein `TodoWrite` ohne `todos`.

**Urteil: geschlossen** — alle drei verweigern jetzt; eine **leere** Aufgabenliste bleibt erlaubt,
das ist ein echter Aufruf. **Ehrlich dazu:** ob ein echter Werkzeugaufruf diese Form überhaupt
erzeugen kann, ist **nicht** gemessen — die Messung ist am Gate genommen, nicht am Provider.

### H7 — `carries_work` verlangt keinen erreichbaren Endzustand — OFFEN

**Mechanismus:** Gate 4 verlangt, dass ein Eintrag ein Item nennt, das Arbeit tragen **kann** (hat
einen Automaten) und **nicht terminal** ist. `SR` hat die Kette `PROPOSED → ACCEPTED` und als
einzigen Endzustand `SUPERSEDED`. Das natürliche Lebensende eines `SR` ist damit `ACCEPTED` — und
das ist kein Endzustand, also trägt ein angenommenes `SR` für Gate 4 für immer „offene Arbeit".

**Kette (neu gemessen 2026-08-14, TSK-0058-Prüfung — das frühere Literal `SR-0006:` ist seit der
Ablösung entwertet, es liefert heute rc 2 als terminales Item):** eine Aufgabenliste, in der
**jeder** Eintrag mit `SR-0009:` beginnt (`status: ACCEPTED`), ist **rc 0**, ebenso mit `SR-0001:`
(`status: PROPOSED`). Die Regel ist mit einem Präfix dauerhaft erfüllbar, ohne dass ein Eintrag
Arbeit bindet.

**Urteil: benannt, NICHT geschlossen — der Grund ist strukturell.** Was fehlt, liegt im **Kernel**:
`AUTOMATA` kennt `chain` und `terminals`, aber keinen Begriff „in diesem Zustand ist ein Item dieses
Typs **fertig**". Ohne den ist jede Reparatur geraten:

- „letzter Kettenzustand = terminal" wäre für `TSK`/`BUG`/`CR` richtig und für `FR` (`TRIAGED`),
  `PROC` (`ACTIVE`) und `HYP` (`TESTING`) falsch — dort *ist* der letzte Kettenzustand der
  Arbeitszustand;
- die Verengung auf `TSK|BUG|FR` wäre die Aufzählung zurück, gegen die `carries_work` geschrieben
  wurde.

`team-kits/**` ist auch in TSK-0008 verbotener Bereich, die Reparaturstelle also weiterhin nicht
erreichbar. **Vorschlag:** `AUTOMATA` um `done_states` erweitern und `Reference.terminal` daraus
lesen. Unabhängig davon bleibt, was Gate 4 selbst sagt: es prüft die **Form**, nie den Inhalt eines
Eintrags — ein Gate, das „ist dieser Eintrag wirklich von diesem Item gedeckt" beantworten wollte,
wäre die Sorte Prüfung, deren Bestehen nichts aussagt.

**Urteil nach der vollen Regel: benannte Ausnahme, Abnahme des Nutzers offen.** Nicht schließbar
ist sie, weil der Begriff fehlt, aus dem die Antwort käme, und er im **Kernel** fehlt, nicht im
Gate — jede Reparatur im Gate wäre entweder geraten (letzter Kettenzustand = fertig, falsch für
`FR`, `PROC`, `HYP`) oder die Aufzählung zurück, gegen die `carries_work` geschrieben wurde. Was
stattdessen begrenzt: Gate 4 hält weiterhin die **Zahl** der ungebundenen Einträge auf eins, und
`_harness.Reference.terminal` benennt die Lücke an der Stelle, an der sie entsteht. Was sie kostet,
ist gemessen (2026-08-14): eine Aufgabenliste, deren Einträge alle mit `SR-0009:` beginnen, ist
rc 0 — die Regel ist mit einem Präfix dauerhaft erfüllbar, ohne dass ein Eintrag Arbeit bindet.

### H8 — Acht Tests hingen am Status *eines* Items — GESCHLOSSEN

**Mechanismus:** `TSK-0003` stand als Literal in Gate-2-, Gate-3- und Gate-4-Tests. Damit war der
Status eines einzelnen Items eine **Vorbedingung der Messung** — und Items werden abgenommen.

**Kette (gemessen):** `status: VALIDATED` in `TSK-0003.yaml` gesetzt → alte Testdatei **2 failed**,
neue Testdatei **3 passed**.

**Urteil: geschlossen.** Die Fixture `open_item` liest die Eigenschaft aus dem Store (auflösbar,
hat einen Automaten, nicht terminal) und legt notfalls ein Item über den Kernel an.

### H9 — Inhalt in diesem Auftrag nicht enthalten

Der Prüfbericht führt ein R9; **was es besagt, stand nicht im Auftrag** — die Liste nennt „R9" ohne
Beschreibung. Es ist hier bewusst als **ungeprüft und ungeschlossen** vermerkt statt geraten zu
werden: ein erfundener Eintrag wäre schlimmer als eine benannte Lücke. Nachzureichen aus dem
Prüfbericht zu TSK-0003.

**Urteil nach der vollen Regel: kein Urteil möglich, und das ist der Befund.** Ohne Mechanismus gibt es keine
Kette, ohne Kette keine Einordnung — der Eintrag steht deshalb in keiner der beiden Spalten der
Tabelle oben. Er ist die einzige Stelle dieser Liste, an der die Regel nicht angewendet werden
kann, weil die Eingabe fehlt.

### H10 — Codehälften ohne rote Mutation — ZWEI GESCHLOSSEN, keine erschöpfende Suche

**Mechanismus:** eine Hälfte einer Fallunterscheidung, die kein Test unterscheidet, ist unbelegt —
sie lässt sich löschen, ohne dass etwas rot wird.

**Gemessen und geschlossen:**

- die **Untracked-Hälfte** des Digests (`working_tree_digest` hasht auch jede unverfolgte, nicht
  ignorierte Datei). Mutation „Schleife entfernt": vorher grün, jetzt rot über
  `test_gate3_sees_a_file_git_does_not_track_yet`.
- die **Feld-Hälfte** von `evidence_naming` („jedes Feld des Items", nicht nur `--summary`).
  Mutation „nur `summary` lesen": vorher grün, jetzt rot über
  `test_gate3_reads_the_digest_in_any_field_of_the_record`.

**Nicht geschlossen:** der Prüfbericht spricht von **drei** solchen Hälften; die dritte ist im
Auftrag nicht benannt, und es wurde **kein erschöpfender Mutationslauf** über die vier Gates
gefahren — nur die beiden oben identifizierten wurden gemessen. Ein `mutmut`-artiger Lauf über
`.claude/hooks/` ist der Kandidat, der die Frage überhaupt beantworten könnte.

**Urteil: Rest, offen ist nur die Vollständigkeit.** Die beiden gefundenen Hälften sind geschlossen
und je durch einen roten Test gedeckt; für die dritte gibt es keinen Ersatz, sondern eine
ungestellte Frage. Die Runden seither haben die Zahl weiter gesenkt, ohne sie zu beantworten: jede
gebaute Verzweigung wird seit TSK-0011 einzeln zurückgedreht und der zugehörige Test gefahren
(zuletzt zehn in `docs/reviews/2026-08-05-tsk0015-measurements.md`, Abschnitt 7) — das ist eine
Stichprobe der eigenen Arbeit, kein erschöpfender Lauf.

### H11 — Ein Interpreter führt Code aus, den kein Gate lesen kann (neu, Preis des Fixes zu F2)

**Mechanismus:** Gate 1s Shell-Hälfte erkennt einen Schreibzugriff an drei Positionen einer
Befehlszeile. Eine Ausnahme war unvermeidbar, sonst hätte das Gate die dokumentierten Befehle dieses
Repos verweigert (`PYTHONPATH=team-kits python -B -m kernel.cli …`,
`python -B -m pytest .claude/hooks/test_gates.py`, `python tools/bump_kit_version.py`): die Operanden
eines **Interpreters** gelten als Programm, nicht als Ziel. Der Inline-Text (`python -c …`) ist von
der Ausnahme ausgenommen und wird verweigert.

**Kette (gemessen, drei Schritte):** `Write scratch/w.py` (freier Bereich) **rc 0** →
`python scratch/w.py` **rc 0** → der Lauf hängt real 8 Bytes an
`team-kits/dev-team/hooks/gate_git.py` an. Zwei Werkzeugaufrufe, eine Sitzung.

**Und sie hebt Gate 3 mit auf — gemessen, nicht abgeleitet (TSK-0008, R-d).** Im selben Lauf:
`git commit -m wip` **rc 2** (Gate 3 verweigert, kein Beweismittel) → ein Skript im freien Bereich,
das `git commit` startet → `python scratch/c.py` **rc 0 bei Gate 1 UND rc 0 bei Gate 3** → `HEAD`
bewegt sich real von `7818d4b7` auf `dc6f500d`. Gate 3 fragt `Invocation.runs("commit")` an den
**Text** der Zeile, und in dieser Zeile steht kein `git`. Die Interpreter-Ausnahme ist damit nicht
nur ein Loch in Gate 1, sondern der Weg an **beiden** Gates vorbei.

**Urteil: blockierend nach der Regel — benannte Ausnahme, Abnahme des Nutzers offen.** Nicht
schließbar von einer Kommandozeile aus: dieselbe Grenze benennen die Kits für ihr
`gate_write_scope` („It does NOT refuse a script the agent wrote to an ordinary path and then
ran"), und die Ausnahme selbst ist unverzichtbar — ohne sie verweigert Gate 1 jede dokumentierte
Zeile dieses Repos (`python -B -m kernel.cli …`, `python -B -m pytest …`,
`python tools/bump_kit_version.py`).

**Was stattdessen begrenzt: nichts Technisches.** Bis 2026-08-05 stand hier und in der Tabelle oben
die **Berechtigungshaltung**. Gemessen trägt `.claude/settings.json` `permissions` genau einen
Eintrag — `deny: ["Agent(harness-lead)"]`, der einen Selbst-Spawn der Sitzungsrolle verhindert —
und **keine** Regel, die ein Shell-Werkzeug einschränkt. Die Zeile beschrieb also eine Maßnahme,
die es nicht gibt. Was heute wirklich begrenzt, sind **Rollentrennung und Item**, also Disziplin.
Eine Berechtigungshaltung, die dem Sitzungsagenten die Shell entzieht, **wäre** der wirksame
Schnitt — sie ist eine Nutzerentscheidung und genau das, worüber die Abnahme entscheidet.

### H12 — Ein Subagent kann sich die Ausnahme von Gate 2 selbst ausstellen

**Mechanismus:** Gate 2 liest die Ausnahme (`harness_item: none`) aus der Frontmatter der gespawnten
Rolle, und liest sie bei **jedem** Aufruf frisch — es ist nicht der Provider, der eine Rolle beim
Sitzungsstart lädt, sondern der Hook, der eine Datei öffnet. Gate 1 schützt `.claude/` nur gegen den
**Sitzungsagenten**; ein Subagent muss dort schreiben dürfen, weil der Auftrag des Umsetzers
regelmäßig `.claude/hooks/**` nennt und dieses Repo keinen Dispatch hat, gegen den sich ein
Subagent-Scope prüfen ließe.

**Kette (gemessen, eigener Lauf):** Spawn ohne Item **rc 2** → `harness_item: none` in
`agents/harness-implementer.md` geschrieben → derselbe Spawn **rc 0** → Zeile entfernt → **rc 2**.
Dieselbe Datei über Gate 1: Sitzungsagent **rc 2**, Subagent **rc 0**.

**Was noch daran hängt, gemessen (TSK-0008):** `.claude/hooks/` ist `sys.path[0]` jedes
Gate-Prozesses — die Datei wird als Skript gestartet, und die Präambel legt das Verzeichnis
zusätzlich nach vorn. Eine dort abgelegte `yaml.py` **läuft** darum während der Entscheidung von
Gate 3 (gemessen an einer Markierungsdatei, die das eingeschleuste Modul beim Import schreibt) —
und `yaml` ist, was das Beweismittel parst, nach dem Gate 3 urteilt. Das ist **kein zusätzlicher**
Angriffsweg: wer dort schreiben kann, kann ebenso `_harness.py` selbst ersetzen. Es gehört hierher,
weil es zeigt, dass die Grenze dieselbe ist.

**Urteil: blockierend nach der Regel — benannte Ausnahme, Abnahme des Nutzers offen.** Nicht
schließbar, weil das, was fehlt, eine Bindung „welcher Subagent darf wohin schreiben" ist; in den
Kits leisten das `dispatch` und der `allowed_scope` des Items, und beides existiert hier bewusst
nicht (`CLAUDE.md`: „keine Leases und kein Dispatch"). Ein Subagent muss `.claude/hooks/**`
schreiben dürfen — das ist der Auftrag des Umsetzers. Was stattdessen begrenzt: die
**Rollentrennung** und das Item, aus dem der Auftrag erzeugt wird; beides ist Disziplin, nicht
Durchsetzung. **Vorschlag:** `.claude/agents/**` auch für Subagenten sperren und den Umsetzer, der
eine Rolle ändern soll, auf einen ausdrücklich erweiterten `allowed_scope` verweisen — das setzt
aber voraus, dass irgendetwas den `allowed_scope` liest, und heute liest ihn nichts.

### H13 — Der Produzent ist als DATEI geschützt, nicht als Verzeichnis

**Mechanismus:** `_harness.decision_inputs` schützt genau die Dateien, aus denen die Antwort des
Gates **berechnet** wurde (gemessen über `sys.modules`, nicht getippt). Ein *neues* File neben
`tools/bump_kit_version.py` fällt nicht darunter, ebenso wenig ein Modul, das der Stempler nur in
einem Zweig lazy importiert, den dieses Gate nie betritt.

**Urteil: Rest.** Ein neues File schaltet nichts ab, solange der Stempler es nicht importiert; und
`tools/` als Ganzes ist aus nichts ableitbar, was dieses Gate liest — es wäre wieder eine
Aufzählung. Wenn `tools/` als Ganzes geschützt gehört, gehört das in den geltenden Vertrag
(`SR-0009`), nicht in einen Hook.

### H14 — Gate 3 druckt den Befehl, der es aufhebt

**Mechanismus:** die Abhilfe des Gates ist `kernel.cli evidence --result pass --summary <digest>`,
und genau die *darf* der Sitzungsagent ausführen — er muss es, denn er zeichnet das Urteil des
Prüfers auf.

**Urteil: Rest, und zwar als Entwurfsentscheidung.** Gate 3 macht einen Commit ohne Urteil zu einer
**ausdrücklichen, aufgezeichneten Handlung**, nicht zu einer unmöglichen. Ein Gate, dessen Abhilfe
nicht ausführbar wäre, würde das Repo aus seiner eigenen Historie aussperren — genau dafür existiert
`test_gate3_remedy_is_executable_and_opens_the_commit`. Wer mehr will, braucht einen zweiten Akteur,
der das Beweismittel schreibt, und der ist ein Provider-Merkmal, kein Hook.

### H15 — Gate 1 hängt jetzt an privaten Helfern eines Kit-Hooks (neu, Preis desselben Fixes)

**Mechanismus:** die Shell-Hälfte von Gate 1 und die Zeilenform-Prüfung von Gate 3 benutzen
`team-kits/<kit>/hooks/gate_write_scope` als **Modul** — Tokenizer, Pipeline-Trennung,
Read-only-Klassifikation, Redirect-Form. Das ist Absicht: eine zweite Antwort auf „ist diese Stufe
lesend" ist genau die Drift, die dieses Repo wiederholt bezahlt hat, und der Kit-Hook trägt drei
dokumentierte Umschreibungen derselben Regel. Der Preis ist eine Kopplung an **unterstrichene**
Namen (`_tokenise`, `_pipelines`, `_stage_is_read_only`, `_redirect_targets`, `_null_sinks`,
`_walk`, `_operator`, `_has_write_flag`, `_stage_verb`, `_HEREDOC_RX`, `_MESSAGE_ARG_RX`).

**Richtung des Fehlers:** wird einer davon umbenannt, wirft der Zugriff, `guarded()` macht daraus
eine **Verweigerung** — nie einen stillen Durchlass. Der Preis ist also kein Loch, sondern ein
Ausfall: jeder `Bash`- und `PowerShell`-Aufruf des Repos wird verweigert, bis jemand den Namen
nachzieht, und Gate 1 selbst sperrt `.claude/` gegen den Sitzungsagenten — repariert wird das aus
einer Shell außerhalb des Providers.

**Was dagegen steht:** `test_gates.py` startet die Gates als echte Prozesse, benutzt die Helfer also
über den laufenden Code. Eine Umbenennung im Kit macht die Suite dieses Repos rot, bevor sie jemand
im Betrieb trifft — vorausgesetzt, die Suite läuft, wenn `team-kits/` sich ändert.

**Urteil: Rest, aber mit einer Bedingung.** `python -B -m pytest .claude/hooks/test_gates.py -q`
gehört ab jetzt zu jeder Änderung an `gate_write_scope.py` dazu, nicht nur zu Änderungen an
`.claude/`. Das ist die einzige Stelle, an der die Kopplung sichtbar wird.

### H16 — Der Pfad steht in einer Variablen, das Gate liest den Text (neu, TSK-0008)

**Mechanismus:** Gate 1 liest eine Befehlszeile als **Text**. Eine Shell setzt Variablen aber erst
beim Ausführen ein. Steht der geschützte Pfad in einer Variablen, sieht das Gate `$R/team-kits/…`
und löst das gegen das Arbeitsverzeichnis auf — ein Pfad, den nichts schützt. Das ist dieselbe
Klasse wie H11: nicht das Vokabular fehlt, sondern der Zustand der Shell zum Ausführungszeitpunkt.

**Kette (gemessen, zwei Werkzeugaufrufe, eine Sitzung):**
`R="<repo>"; sed -i "s/a/b/" "$R/team-kits/kernel/state.py"` → **rc 0**. Ebenso in der
`cd`-Position: `cd "$NOWHERE" && sed -i … team-kits/kernel/state.py` → **rc 0**, weil das Literal
`$NOWHERE` als Verzeichnisname durchgereicht wird.

**Von der `cd`-Hälfte ist die BEWEGUNG geschlossen, nicht die Variable.** Ein Verzeichniswechsel
bewegt die Basis des Gates nur dorthin, wo eine Shell wirklich landet — und `$NOWHERE` ist kein
existierendes Verzeichnis. Dieselbe Zeile: **rc 2**, am 2026-08-05 mit dem Stand dieser Runde
erneut gemessen (`docs/reviews/2026-08-05-tsk0013-measurements.md`, Abschnitt 9). Enthält die
Variable dagegen ein Verzeichnis, das es GIBT, folgt das Gate ihr nicht und urteilt an der falschen
Stelle — das ist H20, und die Richtung dort ist Verweigerung. Die **Pfad**-Hälfte bleibt offen:
dort steht die Variable im Operanden eines Schreibbefehls, und was sie enthält, weiß nur die Shell.
Dieselbe Kette trägt H21 in ihrer PowerShell-Form.

**Was hier NICHT gilt, obwohl es so aussieht:** die PowerShell-Fassung
`$r = "<repo>"; Set-Content -Path "$r/team-kits/kernel/state.py" …` bekommt **rc 2** — aber aus
einem Nebengrund: die Zuweisung nennt den Repo-Wurzelpfad wörtlich, und der **enthält**
`project_memory`, also greift die Regel für kanonischen Zustand. Ein Pfad, der nur einen Teilbaum
nennt, käme genauso durch wie in Bash. Das als „PowerShell ist geschützt" zu lesen wäre die Art von
Zufallstreffer, die eine Runde später als Loch zurückkommt.

**Urteil: blockierend nach der Regel — benannte Ausnahme, Abnahme des Nutzers offen.** Nicht
schließbar von einer Kommandozeile aus: den Wert einer Variablen kennt nur die Shell, die die Zeile
ausführt, und ein Gate, das jede Zeile mit einer Variablen verweigerte, verweigerte auch
`$env:PYTHONPATH="team-kits"; python …` — die dokumentierte PowerShell-Vorsilbe dieses Repos. Was
stattdessen begrenzt, ist dasselbe wie bei H11: **nichts Technisches**, sondern Rollentrennung und
Item. Die Berechtigungshaltung stand hier als Ersatzmaßnahme und ist keine — siehe die Messung bei
H11. Eine engere Variante wäre denkbar (jede *schreibende* Stufe mit einer unaufgelösten Variablen
im Pfadoperanden verweigern) und ist bewusst **nicht** gebaut worden: sie wäre eine zweite Antwort
auf „was ist eine Schreibstufe" neben der der Kits, und die Doppelantwort ist die Drift, die H15
beschreibt.

### H17 — Die andere Schreibweise einer Funktionsdefinition — GESCHLOSSEN (TSK-0011)

**Mechanismus:** `_stage_verb` liest den **deklarierten Namen** als Verb. Ein Verb, das nichts
kennt, gilt als schreibfähig, also wurde jedes Wort des Rumpfes zum Schreibkandidaten — und
`PYTHONPATH=team-kits` nennt den Kit-Baum. `_harness.stage_body` schnitt den Kopf einer Deklaration
ab, prüfte aber nur, ob **irgendwo** im Kopf eine Klammer steht.

**Kette (gemessen, TSK-0008):** `dec () { PYTHONPATH=team-kits python -B -m kernel.cli … ; }` →
rc 0 (BUG-0012, geschlossen), `function dec { dieselbe Zeile ; }` → **rc 2**.

**Urteil: geschlossen, zusammen mit F3.** `_harness._declares_a_function` fragt jetzt nach den
**zwei Formen, die die Grammatik der Shell hat** — Name plus leere Parameterliste, und die
Schlüsselwortform — statt nach einem Zeichen. `function dec { … }` → rc 0 (gemessen 2026-08-05).
Die Gegenrichtung derselben Änderung ist F3 in `docs/reviews/2026-08-05-tsk0011-measurements.md`:
zwei Zeilen, die einen Kopf nur *aussehen ließen* wie einen, verloren dabei ihre Schreibkandidaten
und kamen mit rc 0 durch; beide sind jetzt rc 2.

### H18 — Das Repo als Operand eines Kopier- oder Archivbefehls gilt als Schreibzugriff (TSK-0008, korrigiert TSK-0011)

**Mechanismus:** ob eine Stufe lesend ist, beantwortet die Klassifikation der **Kits**
(`gate_write_scope._stage_is_read_only`), und `cp`, `robocopy`, `xcopy` und `tar` sind dort nicht
lesend — zu Recht, denn sie schreiben ihr Ziel. Gate 1 sammelt daraufhin **alle** Wörter der Stufe.
Der Eintrag hieß bis 2026-08-05 „das Repo als **Quelle**"; das war zu eng. Betroffen ist **jeder**
Operand, der einen geschützten Baum berührt — auch das **Ziel**: `cp -r docs ..` hat keine
geschützte Quelle, und der Zielpfad ist ein **Vorfahre** des Repos. Diese zweite Hälfte ist H19.

**Kette (gemessen, und in dieser Sitzung selbst aufgelaufen):**
`cp -r project_memory <außerhalb>/copy` → **rc 2**, `robocopy team-kits <außerhalb>\bk /E` → **rc 2**,
`tar -czf <außerhalb>/bk.tgz team-kits` → **rc 2** (alle drei zuletzt am 2026-08-05 gegen den Stand
dieser Runde gemessen, `docs/reviews/2026-08-05-tsk0013-measurements.md`, Abschnitt 9). Ein
Backup des eigenen Repos ist damit nicht ausführbar; die Umgehung ist ein Python-Einzeiler, also H11.

**Urteil: Rest, keine Angriffskette — und bewusst nicht hier geschlossen.** Die Fehlerrichtung ist
Über-Verweigerung. Schließen ließe es sich nur, indem Gate 1 für diese Verben entscheidet, welcher
Operand Quelle und welcher Ziel ist — und dafür gibt es **keine** Eigenschaft, nur eine Aufzählung
mit widersprüchlichen Regeln (`cp <quelle…> <ziel>` hat das Ziel hinten, `robocopy <quelle> <ziel>`
vorn). **Es gibt keine Eigenschaft, also wird es nirgends gebaut** — auch nicht im Kit: dessen
Prädikat beantwortet „ist diese Stufe lesend" und sagt über Operandenrollen nichts. (Bis 2026-08-05
stand hier, das Kit beantworte die Frage schon; das war falsch.) Die Fehlerrichtung bleibt
Über-Verweigerung, und dabei bleibt es, bis jemand eine Eigenschaft findet.

### H19 — Ein Kandidat, der einen VORFAHREN eines geschützten Baums nennt (neu, TSK-0011)

**Mechanismus:** die Zugehörigkeitsprüfung antwortet in **beide** Richtungen, und sie muss das:
`rm -rf team-kits` nennt jede geschützte Datei darunter, ohne eine davon zu buchstabieren. Die
Kehrseite ist, dass ein Kandidat, der einen Vorfahren nennt — ein einzelnes `..`, ein bloßer
Laufwerksbuchstabe, die Repo-Wurzel selbst —, als Schreibzugriff auf **alles darunter** gelesen
wird. Ein `_PATHISH`-Treffer, der nur aus `/` oder `\` besteht, reicht dafür aus.

**Kette (gemessen):** `cp -r docs ..` → **rc 2**, `cp -r docs C:/` → **rc 2**. Der Prüfer ist damit
dreimal auf rein lesenden Sonden aufgelaufen.

**Der Weg-durch daneben, und er gehört hierher, weil er die Kosten dieser Über-Verweigerung
einordnet (gemessen 2026-08-14, `gate_lead_write_scope.py` als Prozess, Zustellung des Payloads
gegen eine Kopie des Baums außerhalb des Repos):** dasselbe Kopierwerk, dessen **Befehlszeile**
keinen geschützten Pfad nennt, geht durch. `robocopy "<repo>\docs" "<repo>\team-kits\kernel" /E` ist
**rc 2** und `python -c "…copyfile('a','team-kits/kernel/state.py')"` ebenfalls **rc 2**; dieselbe
Kopie in einer Skriptdatei außerhalb des Repos, aufgerufen als `python "<außerhalb>\job.py"`, ist
**rc 0** — und das Skript schreibt dann wirklich (gegen die Kopie gemessen: `kernel/state.py`
71900 → 280470 Bytes). Der Grund ist keine Lücke dieses Eintrags, sondern die Bauart: das Gate liest
**Befehlszeilen**, nie Dateiinhalte. Damit ist die Über-Verweigerung oben Reibung für den, der
ehrlich arbeitet, und kein Schutz gegen den, der es nicht tut — begrenzt wird das wie bei H11, H12
und H16 **sozial** (Rollentrennung und Item), nicht technisch.

**Urteil: Rest, keine Angriffskette — Über-Verweigerung.** Was mit TSK-0011 geschlossen ist, ist
nicht die Verweigerung, sondern die **Behauptung** darin: bis dahin bekam ein Laufwerksbuchstabe
den Text *„this is canonical project state"*, was er nicht ist. Die Verweigerung nennt jetzt die
Richtung, die sie gesehen hat (`_harness.reaches`, `CONTAINS_NOTE`), und sagt, dass der weitere
Pfad für das verweigert wird, was **unter** ihm steht. Schließen ließe sich der Rest nur, indem das
Gate entschiede, ob ein Vorfahre als Ziel oder als Nachbar gemeint ist — dieselbe fehlende
Eigenschaft wie in H18.

### H20 — Wo das Gate einer Bewegung nicht folgen kann, bleibt es stehen (neu, TSK-0011)

**Mechanismus:** die Basis des Gates bewegt sich nur dorthin, wo eine Shell wirklich landet, und
sie tut es nur, wenn die Shell den Wechsel selbst ausführt. Was der Leser nicht auflösen kann (eine
Variable, ein Wort, das erst zur Laufzeit entsteht), was er nicht als Befehl der Shell selbst
belegen kann (ein Verzeichnisverb, das die Kits als anderes Verb melden — hinter `if`, hinter `do`,
hinter einer Array-Zuweisung) und was er nicht als Operandenliste verbuchen kann (H29) bewegt sie
**nicht**. Ist die Shell in Wahrheit doch gegangen, urteilt das Gate an der falschen Stelle.

**Kette (gemessen):** `cd "$NOWHERE" && sed -i … team-kits/kernel/state.py` → **rc 2**, obwohl die
Zeile, wenn `$NOWHERE` ein echtes Verzeichnis benennt, außerhalb des Repos schreibt. Die
Verbstellungen sind in `docs/reviews/2026-08-05-tsk0015-measurements.md` (Abschnitt 6) mit `bash`
als Schiedsrichter gemessen: die Shell geht dort hinaus, das Gate folgt nicht, rc 2. Sie sind als
Klasse in H24 beschrieben, weil sie eine gemeinsame Ursache haben. **Nicht mehr Teil dieses
Eintrags:** ein Verzeichnis mit Durchsuchrecht ohne Leserecht. Seit TSK-0015 fragt der Leser das
Betreten selbst, und die Shell geht dort hinein wie er (H28).

**Die andere Richtung derselben Konstruktion, und sie war ein Durchlass — gemessen 2026-08-07
(`docs/reviews/2026-08-07-tsk0019-measurements.md`, Abschnitt 2):** „Stehenbleiben ist fail-closed"
gilt nur, solange die Basis in dem Baum steht, in den der relative Schreibzugriff zeigt. Sobald die
Zeile einmal hinausgegangen ist, kann **jede** Bewegung, die der Leser nicht ausrechnen kann, die
sein, die wieder **hinein** geht — und dann ist Stehenbleiben die durchlassende Antwort. Sieben
Schreibweisen, eine Ursache, alle **rc 0**, während `bash` die geschützte Datei wirklich änderte,
jeweils mit `cd "<außerhalb>" ;` davor und einem relativen Schreibzugriff dahinter: `cd "$R"`,
`command cd`, `time cd`, `! cd`, `x=1 cd`, `cd -L` und `cd "<hier>" 2>&1`. Und die Grenze ist nicht
die des **Repos**: `cd docs ; command cd .. ; <relativ schreiben>` schrieb die geschützte Datei aus
einer Basis, die das Repo nie verlassen hat, ebenfalls rc 0.

**Urteil: blockierend, geschlossen — die Richtung war eine Behauptung, keine Eigenschaft.** Eine
Bewegung, deren Wirkung dieser Leser nicht ausrechnen kann, macht die Position **unbekannt**
(`_harness.WorkingDirectory.follow` → `_UNKNOWN_POSITION`), unabhängig davon, wohin sie zeigt; von
dort ist jeder relative Kandidat ein `_harness.Unplaceable` und wird für **jeden** Aufrufer
verweigert. Stehen bleibt die Basis nur noch, wo der Leser die Nicht-Bewegung **ausgerechnet** hat:
ein Verzeichnisverb, das die Shell in einem Kind ausführt, ein Wort, das für diese Shell kein Verb
ist, ein Stapel, den er vollständig gesehen hat und der leer ist. Bis TSK-0017 hatte nur `popd`
diese Antwort — die Runde hatte die Richtung als Eigenschaft erkannt und sie an ein **Verb**
gebunden statt an die Basis. Rot ohne den Fix (jeder Zweig einzeln zurückgedreht, Abschnitt 5 des
Protokolls): `test_gate1_refuses_a_line_exactly_where_the_shell_would_write`.

**Der Preis, gemessen:** 64 der 1440 Zellen der gekreuzten Tabelle sind Über-Verweigerung, und neu
darin ist, dass eine solche Zeile auch einen Schreibzugriff auf einen **freien** Pfad verweigert:
die Position ist unbekannt, nicht bloß im geschützten Baum. Das ist Reibung, und sie trifft jeden
Aufrufer, nicht nur den Sitzungsagenten. Die Bewegungs-Hälfte von H16 ist damit geschlossen, ohne
dass der Pfad in der Variablen lesbar geworden wäre.

**Die Reibung, die man auf diesem Host zuerst trifft, gemessen an der eigenen Zeile:** ein
absoluter Pfad in **POSIX-Schreibweise**. Der Bash-Werkzeugaufruf läuft hier in Git Bash, dort ist
`/c/…` ein gültiges Verzeichnis — für den Leser ist es ein Pfad auf dem aktuellen Laufwerk
(`C:\c\…`), den kein Prozess betreten kann, also gibt er die Position auf. Gemessen 2026-08-07 gegen
ein Stellvertreterprojekt: `cd /c/<projekt> && echo hi > docs/note.md` ging von **rc 0 auf rc 2**,
während dieselbe Zeile mit `cd "C:/<projekt>"` rc 0 bleibt und `cd /c/<projekt> && git rev-parse
HEAD` ebenfalls (ein lesendes Verb sammelt keine Kandidaten). Die Abhilfe steht in der Verweigerung
selbst; die dokumentierten Befehle dieses Repos tragen ohnehin kein `cd`.

**Zellen der gekreuzten Tabelle, auf denen dieser Eintrag steht:** `with the base outside it`,
`cd to a target this reader cannot name`, `cd with an option the shell accepts`,
`a move inside the tree the reader cannot compute`,
`a push this reader cannot make, and a pop the shell can`.

### H21 — `Push-Location`/`Pop-Location` fehlen im Verzeichnis-Vokabular (neu, TSK-0011)

**Mechanismus:** die Verben, die die Basis bewegen, sind `cd`, `pushd`, `popd`, `set-location` —
in `_harness._DIRECTORY_VERBS` und, unabhängig davon, in `gate_write_scope._walk` und der Zeile
daneben in `handle_shell`. Beide Aufzählungen kennen die **ausgeschriebenen** PowerShell-Formen
`Push-Location` und `Pop-Location` nicht.

**Kette (gemessen 2026-08-05, `docs/reviews/2026-08-05-tsk0013-measurements.md`, Abschnitt 9):**
`Set-Location <außerhalb> ; Push-Location "$env:R" ; Set-Content -Path team-kits/kernel/state.py …`
→ **rc 0**. Die Shell steht am Ende im Repo, das Gate glaubt sich draußen. Mit dem Repo-Pfad
**wörtlich** statt in der Variablen ist dieselbe Zeile rc 2 — aber aus einem anderen Grund: die
Kits führen `Push-Location` nicht als lesendes Verb, also wird jedes Wort der Stufe zum
Schreibkandidaten, und das Wort nennt den geschützten Baum.

**Urteil: blockierend nach der Regel — benannte Ausnahme, Abnahme des Nutzers offen.** Bis
2026-08-05 stand hier „Rest, keine Angriffskette", während der Rumpf des Eintrags die Kette
beschrieb; gemessen läuft sie. Sie läuft aus dem Grund, den H16 trägt (der Pfad steht in einer
Variablen), also ist sie **dieselbe** Kette und keine zweite. Was bleibt und diesem Eintrag gehört,
ist das fehlende Vokabular; die Reparaturstelle dafür liegt im **Kit**
(`gate_write_scope._READ_ONLY_VERBS`, `_walk` und die Verbliste in `handle_shell`), nicht hier: ein
zweites Vokabular in `_harness` wäre genau die Doppelantwort, die H15 beschreibt. `team-kits/**`
ist verbotener Bereich von TSK-0011 wie von TSK-0013. **Was stattdessen begrenzt: nichts
Technisches** — Rollentrennung und Item, dieselbe Lage wie H11 und H16. Der Nebengrund oben ist
keine Maßnahme: er hängt daran, dass jemand den Pfad ausschreibt. **Vorschlag:** als Kit-Item
aufnehmen.

### H22 — Die Read-only-Klassifikation gilt pro Stufe, der Pfad reist weiter (neu, TSK-0011)

**Mechanismus:** ob eine Stufe schreibt, beantwortet die Klassifikation der Kits **pro Stufe**, und
die Wörter einer lesenden Stufe fallen damit als Schreibkandidaten weg. Eine Pipe, eine
Kommandosubstitution und eine Patch-Datei tragen den Pfad aber über diese Grenze: die lesende Stufe
**nennt** ihn, die schreibende **benutzt** ihn, und keine der beiden zeigt beides.

**Kette (gemessen 2026-08-05, alle rc 0, alle schreiben wirklich):**
`echo team-kits/kernel/state.py | xargs sed -i "s/a/b/"`,
`echo $(sed -i "s/a/b/" team-kits/kernel/state.py)`, dieselbe Zeile in Backtick-Form, und
`git apply x.patch`, wo der Pfad in der Patch-Datei steht und in der Zeile überhaupt nicht vorkommt.

**Die Ersetzungs-Hälfte ist seit TSK-0019 geschlossen und gehört jetzt H32**, samt der Begründung,
warum das **keine** zweite Antwort auf „was ist eine Schreibstufe" ist: der Befehl, den die
Ersetzung einführt, wird von derselben Zerlegung platziert wie jeder andere und dann von derselben
Klassifikation beurteilt. Was diesem Eintrag bleibt, ist die **Pipe** und die **Patch-Datei**.

**Urteil: blockierend nach der Regel — benannte Ausnahme, Abnahme des Nutzers offen.** Nicht in
TSK-0011 geschlossen, und der Grund ist derselbe wie bei H15: die Klassifikation gehört den Kits,
und „alle Wörter aller Stufen einsammeln, sobald irgendeine schreibt" wäre eine zweite Antwort auf
„was ist eine Schreibstufe" — sie verweigerte außerdem `cat <kitdatei> | python -c …` und ähnliche
Leseketten. Die Patch-Hälfte ist von einer Kommandozeile aus gar nicht entscheidbar: was eine
Patch-Datei ändert, steht in der Datei. **Was stattdessen begrenzt: nichts Technisches** — dieselbe
Lage wie H11, also Rollentrennung und Item. **Vorschlag:** die Stufen-Grenze im Kit angehen
(`_stage_is_read_only` plus eine Weitergabe von Wörtern über die Pipe), nicht hier.

### H23 — Ein unerreichbarer Pfad kostet die Beurteilung, nicht mehr die Frist (neu, TSK-0011)

**Mechanismus:** eine Dateisystemfrage zu einem nicht erreichbaren Host kostet auf diesem Host
42,1 s und lässt sich nicht abbrechen. Seit TSK-0011 ist die **Wartezeit** begrenzt: `_harness`
liest die Frist aus der Registrierung und verweigert, wenn eine Frage nicht rechtzeitig
zurückkommt. Der Rest, der bleibt: eine Zeile, deren Kandidaten das Budget aufbrauchen, wird
**verweigert statt beurteilt** — und sie braucht dafür bis zu vier Fünftel der registrierten Zeit.

**Kette (gemessen):** ein Kandidat auf einem unerreichbaren Host → rc 0 nach 43,0 s (beurteilt);
fünf → **rc 2 nach 96,5 s** bei registrierten 120 s. Vorher: fünf → rc 0 nach 211,3 s, also nach
der Frist, was der Provider als Durchlass liest.

**Urteil: Rest, keine Angriffskette.** Die Fehlerrichtung ist Über-Verweigerung plus Wartezeit. Was
nicht geschlossen ist: das Budget ist ein **Anteil** der registrierten Zeit
(`_harness._SPENDABLE_SHARE`), keine Ableitung — der Prozessstart, gegen den man ihn ableiten
müsste, liegt vor der ersten Zeile, die der Prozess selbst sieht. Seit TSK-0013 ist der Anteil
nicht mehr allein: die Reserve ist der GRÖSSERE von Anteil und Untergrenze, weil ein Fünftel einer
kurzen Frist kleiner ist als der Prozessstart dieses Hosts — gemessen bei registrierter 1 s eine
Antwort nach 1,55 s, also nach der Frist. Und: der Zweig, der `os.stat`
unter die Frist stellt, ist **wirksam, aber nicht isoliert messbar** — zu demselben Pfad wird
zuerst `realpath` gefragt, und das blockiert mindestens so lange (21,8 s mit einer Frage am Netz,
43,0 s mit beiden). Beides steht in den Messprotokollen
(`docs/reviews/2026-08-05-tsk0011-measurements.md` für die Wartezeit,
`docs/reviews/2026-08-05-tsk0013-measurements.md` Abschnitt 5 für die Untergrenze), nicht in einem
Kommentar, der Deckung behauptet.

**Was die Untergrenze kostet, und es ist kein Loch, sondern eine Stilllegung:** unter einer
registrierten Frist, die kürzer ist als die Reserve, ist das Budget null und das Gate verweigert
jeden Aufruf, für den es das Dateisystem fragen muss. Die Registrierung dieses Repos steht auf
120 s.

### H24 — Ein Verzeichnisverb, das der Leser nicht als Verb der Zeile sieht (neu, TSK-0013)

**Mechanismus:** ob die Basis sich bewegt, entscheidet Gate 1 am **Verb der Pipeline**, und welches
Wort das ist, beantwortet der Leser der Kits (`gate_write_scope._stage_verb`). Steht das
Verzeichnisverb hinter einem reservierten Wort oder hinter einer **Array**-Zuweisung, meldet der
Leser ein anderes Wort als Verb — `do`, das erste Element der Klammer — und ein Wort, das kein
Verzeichnisverb ist, bewegt nichts.

**Kette (gemessen 2026-08-05, `bash` als Schiedsrichter über die Datei,
`docs/reviews/2026-08-05-tsk0015-measurements.md`, Abschnitt 6):**
`while true ; do cd "<außerhalb>" ; break ; done ; <relativ schreiben>` → die Shell steht außerhalb,
schreibt also **nicht** in den geschützten Baum, und das Gate verweigert trotzdem (**rc 2**).
Ebenso `if cd "<außerhalb>" ; then true ; fi ; <schreiben>` und
`arr=(a b) cd "<außerhalb>" ; <schreiben>`. **Die skalare Zuweisung gehörte bis TSK-0017 nicht
dazu:** bis TSK-0015 stand hier „hinter einer Feldzuweisung", getroffen war dann nur die
Array-Form — `x=1 cd "<außerhalb>" ; <schreiben>` war rc 0. Seit TSK-0017 ist auch sie Reibung
(gemessen `docs/reviews/2026-08-07-tsk0017-measurements.md`, Abschnitt 8: **rc 2**), und zwar als
Folge von H30: vor dem Befehlsnamen darf nur noch **Syntax** stehen, weil ein Wort dort sonst ein
Befehl sein kann, der das Verb an ein Kind gibt. Ein Leser, der die Zuweisung ausnimmt, hätte dafür
wieder eine Aufzählung dessen zu führen, was harmlos davorsteht.

**Urteil: blockierend, geschlossen — die skalare Hälfte trug eine Kette, die dieser Eintrag als
Reibung führte.** Bis 2026-08-07 stand hier „Rest, keine Angriffskette", und gemessen war
`cd "<außerhalb>" ; x=1 cd "<hier>" ; <relativ schreiben>` **rc 0**, während `bash` zurück in den
Baum ging und die geschützte Datei änderte (Abschnitt 2 des Protokolls zu TSK-0019). Geschlossen ist
sie dort, wo H20 geschlossen ist: eine Bewegung, die dieser Leser nicht ausrechnen kann, macht die
Position unbekannt. **Was als Reibung bleibt**, ist die Array-Zuweisung und das reservierte Wort
(`while … do cd …`, `if cd … then`): dort geht die Shell wirklich hinaus, das Gate verweigert
trotzdem. Enger fassen ließe sich das nur, indem `_harness` selbst entscheidet, welches Wort einer
Stufe das Verb ist — die zweite Antwort, die H15 beschreibt. **Vorschlag:** als Kit-Item aufnehmen,
zusammen mit H21. Rot ohne den Fix: `test_gate1_refuses_a_line_exactly_where_the_shell_would_write`;
die skalare Zuweisung ist seit TSK-0019 eine erzeugte Zelle der Tabelle, weil die Achse jetzt aus
den **Verzweigungen** von `_stage_verb` kommt und nicht mehr nur aus seiner Wortliste (`DEC-0018`).

**Zellen der gekreuzten Tabelle, auf denen dieser Eintrag steht:**
`cd behind 'a=b', which the kits' reader steps over -- run by the shell itself -- with the base outside it`,
`with the base outside it`.

### H25 — Die Frist, die ein Gate sich zugesteht, und die, nach der es getötet wird (neu, TSK-0013)

**Mechanismus:** `_harness.registered_timeout` liest die Frist bei **jedem Aufruf** aus
`.claude/settings.json`. Der Provider hat seine eigene beim **Sitzungsstart** gebunden. Solange
eine Sitzung läuft, sind die beiden Zahlen entkoppelt: wer die Datei schreiben darf, setzt die
Zahl hoch, die sich das Gate zugesteht, ohne die zu ändern, nach der getötet wird — und ein Gate,
das noch entscheidet, wenn der Provider aufhört zuzuhören, wird getötet, was der Provider als
„hook error, carry on", also als **Durchlass** liest.

**Kette (gemessen, `docs/reviews/2026-08-05-tsk0013-measurements.md`, Abschnitt 7):** das Gate folgt
der Datei, Aufruf für Aufruf — registrierte 6 s → Antwort nach 4,92 s, registrierte 1 s → 0,52 s,
60 s → das volle Budget. `.claude/` ist dem Sitzungsagenten verweigert und einem **Subagenten**
offen (H12, dort gemessen), und der Umsetzer arbeitet als Subagent. **Nicht gemessen und auch nicht
messbar von hier aus:** dass der Provider seine Frist beim Sitzungsstart bindet. Das ist die Zusage,
auf der dieses Repo ohnehin steht (`SR-0009`: „All four gates bind at session start"), keine Messung
dieser Runde.

**Urteil: blockierend nach der Regel — benannte Ausnahme, Abnahme des Nutzers offen.** Nicht
schließbar von einem Hook aus: die einzige Zahl, die ein Prozess lesen kann, ist die in der Datei,
und eine Kopie davon im Modul wäre die, die veraltet, sobald die Registrierung gesenkt wird. Was
stattdessen begrenzt: **nichts Technisches** — dieselbe Lage wie H12, von der diese Kette abhängt,
also Rollentrennung und Item. **Vorschlag:** `.claude/settings.json` auch für Subagenten sperren
und den Umsetzer, der die Registrierung ändern soll, auf einen ausdrücklich erweiterten
`allowed_scope` verweisen — dasselbe Vorhaben wie in H12, und es setzt dasselbe voraus: dass
irgendetwas den `allowed_scope` liest.

### H26 — Ein Trenner, den der Leser nicht als Trenner las — GESCHLOSSEN (TSK-0013, erweitert TSK-0015)

**Mechanismus:** wo ein Befehl endet, beantwortete Gate 1 mit der Trennerliste der Kits
(`gate_write_scope._PIPELINE_SEPARATORS`: `&&`, `||`, `;`). Der asynchrone Trenner steht dort
nicht, und `shlex` liefert **aneinandergrenzende** Satzzeichen als EIN Token (`);`, `)&&`), das
keiner Schreibweise gleicht. Beides hat dieselbe Folge: das Zeilenende gehört zum Verb davor — und
ein lesendes Verb sammelt keine Schreibkandidaten. Es braucht dafür keinen Verzeichniswechsel.
**Dieselbe Ursache im eigenen Leser, gefunden 2026-08-05:** der Stufenschnitt war ein VERGLEICH mit
`|` statt einer Frage an die Zeichen, also traf er `)|` nicht; und `_cuts` las jeden Lauf mit einem
`&` als asynchronen Trenner, also auch `|&` — die Pipe, die stderr mitnimmt.

**Kette (gemessen 2026-08-05, ein Werkzeugaufruf, `bash` ändert die Datei wirklich):**
`echo hi & sed -i "s/a/b/" team-kits/kernel/state.py` → **rc 0**; ebenso
`cat docs/note.md & <schreiben>`, `(echo hi);<schreiben>` und `(echo hi)&&<schreiben>`. Dieselben
Zeilen mit einem Leerzeichen vor dem Trenner waren rc 2. Dieselbe Ursache ohne jeden Schreibbefehl:
`echo hi;>team-kits/kernel/state.py` → **rc 0**, und die Zeile **kürzt die Datei** — `;>` ist weder
ein Trenner der Kits noch eine ihrer Umleitungsformen. In Gate 3 mit gültigem
Urteil im Baum: `echo more >> docs/note.md & git commit -m wip` → **rc 0**, ebenso
`(echo more >> docs/note.md);git commit -m wip`. Tabellen in
`docs/reviews/2026-08-05-tsk0013-measurements.md`, Abschnitte 2 und 4.

**Kette der zweiten Hälfte (gemessen 2026-08-05,
`docs/reviews/2026-08-05-tsk0015-measurements.md`, Abschnitt 4):**
`(echo hi)|sed -i … team-kits/kernel/state.py` → **rc 0**, die Datei ändert sich wirklich; und
`echo hi |& cd "<außerhalb>" ; <relativ schreiben>` → **rc 0**, weil der Leser hinter `|&` einen
neuen Befehl sah und dessen `cd` die Basis bewegte, während `bash` es in einem Kind ausführt und
stehen bleibt. Beide Male genügt **ein** Werkzeugaufruf.

**Urteil: blockierend, geschlossen.** `_harness.commands` schneidet die Zeile, wo die Shell sie
schneidet, und `_harness._cuts` beantwortet das an den **Zeichen** eines Satzzeichenlaufs statt an
einer Liste von Schreibweisen — seit TSK-0015 gilt dasselbe für den Stufenschnitt
(`_starts_a_stage`), und die Reihenfolge der Fragen entscheidet `|&`: ein Lauf, der noch ein `|`
trägt, ist eine Pipe und kein Trenner. Die Trennerliste der Kits bleibt die Autorität: was sie
führt und dieser Leser nicht platzieren kann, ist eine Verweigerung, kein stiller Rest. Rot ohne
den Fix (TSK-0015 zusätzlich: „ein Stufenschnitt ist das Token `|`" und „ein Lauf mit `|` und `&`
ist der asynchrone Trenner", beide über `test_gate1_refuses_a_line_exactly_where_the_shell_would
_write`):
`test_gate1_refuses_a_line_exactly_where_the_shell_would_write`,
`test_a_separator_this_reader_cannot_place_refuses_the_line` und
`test_gate3_refuses_a_line_that_moves_the_tree_before_it_commits`.

**Was der Stolperdraht selbst kostet, gemessen und seit TSK-0015 enger gefasst:** er fragte, ob
`_cuts` den Trenner platziert — und legte damit jede Zeile lahm, den Kernel-Aufruf dieses Repos
eingeschlossen, sobald die Kits einen Trenner führen, den dieser Leser sehr wohl liest. Gemessen
mit `|` in ihrer Liste: vier von vier Zeilen rc 2
(`docs/reviews/2026-08-05-tsk0015-measurements.md`, Abschnitt 4), obwohl `stages()` genau dort
schneidet und die Wörter dahinter ihr eigenes Verb bekommen. Gefragt wird jetzt nach dieser Folge
(`_placed_by_this_reader`); `>` und `NEWLINE-ISH` verweigern weiter.

**Zellen der gekreuzten Tabelle, auf denen dieser Eintrag steht:**
`a write behind a backgrounded read`, `a write behind a backgrounded write`,
`a write behind a glued terminator`, `a write behind a glued and`,
`a redirect glued to the terminator in front of it`,
`a redirect glued to a terminator behind a group`,
`a write behind a pipe glued to a bracket`, `a write behind a pipe that carries stderr too`,
`a write behind a pipe that carries stderr, glued`, `a move behind a pipe that carries stderr`,
`a move in front of a pipe that carries stderr`, `a move behind a pipe glued to a bracket`,
`glued to its terminator`, `behind a glued and`, `in a group glued to the terminator behind it`.

### H27 — Die Kindschaft eines Verzeichnisverbs hatte eine Schreibweise — GESCHLOSSEN (TSK-0013)

**Mechanismus:** ein Verzeichnisverb, das die Shell in einem **Kind** ausführt, lässt die Shell
selbst stehen. Gezählt wurde das pro Pipeline und nur an der Klammer: hinter einem Listentrenner
fing der Zähler wieder bei null an, obwohl die Klammer offen war, und die asynchrone Liste wie das
Pipelineglied kamen im Zähler überhaupt nicht vor.

**Kette (gemessen 2026-08-05, `bash` als Schiedsrichter über die Datei):** acht Zeilen, die alle in
den geschützten Baum schreiben, während das Gate der Bewegung nach draußen gefolgt war und **rc 0**
antwortete — `( true ; cd <außerhalb> ) ;`, `( true && cd … ) ;`, `( false || cd … ) ;`,
`(cd …);`, `cd … &`, `cd … & true ;`, `cd … && true &` und `cd … | true ;`, jeweils gefolgt von
einem relativen Schreibzugriff. Vier weitere Schreibweisen derselben Klasse waren schon vorher
rc 2 (`( cd … ) ;`, `( ( cd … ) ) ;`, `( pushd … ) ;`, `true | cd … ;`) und sind es geblieben.
Tabelle in `docs/reviews/2026-08-05-tsk0013-measurements.md`, Abschnitt 1.

**Urteil: blockierend, geschlossen — und als BEWEIS statt als Suche nach Gefahr.**
`_harness._runs_in_the_shell_itself` bewegt die Basis nur, wenn drei Dinge zugleich gelten (die
Liste ist nicht asynchron, die Pipeline hat eine Stufe, keine Gruppe ist an der Stelle des Verbs
offen); alles andere bleibt stehen, was die verweigernde Richtung ist. Die Gegenrichtung ist teuer
und mitgemessen: elf Zeilen, in denen die Shell wirklich geht (darunter die geschweifte Gruppe, die
kein Kind ist), bleiben rc 0. Rot ohne den Fix:
`test_gate1_refuses_a_line_exactly_where_the_shell_would_write`, gegen die Tabelle, deren Spalte
`test_the_shell_writes_where_the_table_of_line_shapes_says` aus einer echten Shell nimmt.

**Zellen der gekreuzten Tabelle, auf denen dieser Eintrag steht:** `in a group`,
`in a group opened before a terminator`, `in a group opened before an and`,
`in a group opened before an or`, `in a group inside a group`,
`in a group glued to the terminator behind it`, `in a background list`,
`in a background list with a command behind it`, `in an and-or list backgrounded at its end`,
`as the first stage of a pipeline`, `as the last stage of a pipeline`,
`in a brace group, which groups and is no child`, `after a group that closed`,
`after a group whose list went to the background`, `behind a backgrounded command`,
`with its own output redirected`, `run by the shell itself`.

### H28 — Ein Verzeichnis, das existiert und nicht betretbar ist — GESCHLOSSEN (TSK-0013, korrigiert TSK-0015)

**Mechanismus:** die Basis folgte einem `cd`, sobald das Ziel ein existierendes Verzeichnis war.
Ein Verzeichnis, dessen Betreten verweigert wird, existiert aber — die Shell bleibt trotzdem
stehen. **Betreten und Auflisten sind zwei Rechte**, und jede Frage, die nicht das Betreten selbst
ist, beantwortet das andere: mit entzogenem Durchsuchrecht (`icacls /deny <user>:(X)`) antworten
`os.path.isdir`, `os.stat`, `os.stat` des `.` darin, `os.access(X_OK)` **und** `os.scandir` mit ja,
während `os.chdir` und `bash` `Permission denied` sagen.

**Kette (gemessen 2026-08-05, `docs/reviews/2026-08-05-tsk0015-measurements.md`, Abschnitt 2):**
`cd "<durchsuchen entzogen>" ; <relativ schreiben>` — die Shell bleibt im Baum und die geschützte
Datei ändert sich, das Gate folgte der Bewegung hinaus und antwortete **rc 0**. Mit entzogenem
**Leserecht** lief dieselbe Konstruktion in die andere Richtung: die Shell geht hinaus, das Gate
blieb stehen und verweigerte einen Schreibzugriff außerhalb des Baums (Reibung).

**Urteil: blockierend, geschlossen.** `_harness._can_be_entered` **betritt** das Verzeichnis und
kehrt zurück (`os.chdir`) — die einzige der sieben gemessenen Fragen, die in **beiden** Richtungen
antwortet wie die Shell. Bis TSK-0015 stand hier das **Öffnen** des Verzeichnisses, mit genau
dieser Behauptung im Docstring; gemessen war der Eintrag damit offen, nicht geschlossen. Rot ohne
den Fix: `test_gate1_follows_a_move_a_process_can_make_and_no_other`.

### H29 — Eine Operandenliste, die dieser Leser nicht verbuchen kann (neu, TSK-0015)

**Mechanismus:** ob die Basis sich bewegt, hängt jetzt auch daran, dass der Leser die **Wörter
hinter dem Verzeichnisverb** vollständig verbucht. Er kann genau eines: das Ziel. Welche Optionen
ein eingebautes Verb annimmt, weiß nur dieses Verb — eine Liste von Flags hier wäre eine Behauptung
über `bash`, die niemand prüft —, also ist **jedes** als Option angebotene Wort und jedes zweite
Wort eine Liste, die er nicht verbuchen kann, und dann bleibt die Basis stehen. Dasselbe gilt für
einen Dateideskriptor, der als eigenes Wort vor einer Umleitung steht (`cd <ziel> 2> log`), und für
die Deskriptor-Verdopplung (`2>&1`).

**Kette (gemessen 2026-08-05, `bash` als Schiedsrichter über die Datei,
`docs/reviews/2026-08-05-tsk0015-measurements.md`, Abschnitt 6):** `cd -L "<außerhalb>" ;
<relativ schreiben>`, ebenso mit `-P`, mit `--` und mit `2>&1` → die Shell geht wirklich hinaus und
schreibt **nicht** in den geschützten Baum; das Gate bleibt stehen und verweigert (**rc 2**).

**Eine der drei Schreibweisen ist seit TSK-0017 geschlossen, und ohne jede Aufzählung:** `--` ist
keine Option, sondern das **Optionsende** der POSIX-Grammatik (Utility Syntax Guideline 10) — was
dahinter steht, ist ein Operand, wie immer es geschrieben ist. `_harness._END_OF_OPTIONS` ist diese
Definition; `cd -- "<außerhalb>" ; <relativ schreiben>` ist gemessen von rc 2 auf **rc 0** gegangen
und steht als Zelle in der gekreuzten Tabelle. Rot ohne den Fix:
`test_gate1_refuses_a_line_exactly_where_the_shell_would_write`.

**Warum die beiden anderen bleiben, jede mit ihrem eigenen Grund** — die Begründung dieses Eintrags
deckte bis TSK-0017 nur die erste:

- `cd -L` / `cd -P`: welche Optionen ein Builtin annimmt, weiß nur das Builtin. Schließbar wäre das
  nur mit einer Flagliste je Verb und Shell, also der Sorte Aufzählung, die hier jede Runde einen
  Defekt später fällig wird.
- `cd <ziel> 2>&1` und `cd <ziel> 2> log`: das ist **keine** fehlende Aufzählung, sondern eine
  Information, die die Zerlegung verliert. `shlex` gibt `2`, `>&`, `1` als drei Token zurück und
  trennt den Deskriptor vom Operator, den `bash` nur **geklebt** akzeptiert — danach ist
  `cd <ziel> 2> log` von `cd 2 > log` (ein Verzeichnis, das wirklich `2` heißt) nicht mehr zu
  unterscheiden. Den Deskriptor wegzuwerfen liefe im zweiten Fall ins Heimatverzeichnis, während
  die Shell in `2/` geht — das ist die durchlassende Richtung. Ihn zu behalten macht die Liste
  unverbuchbar, und das ist die verweigernde. Geschlossen wäre es nur über eine zweite Zerlegung
  des Rohtexts, also genau die Drift, die H15 beschreibt.

**Urteil: blockierend, geschlossen — und was bleibt, ist Über-Verweigerung.** Bis 2026-08-07 stand
hier „Rest, keine Angriffskette", und das war für **beide** verbliebenen Schreibweisen falsch:
gemessen (Abschnitt 2 des Protokolls zu TSK-0019) waren `cd "<außerhalb>" ; cd -L "<hier>" ;
<relativ schreiben>` und dieselbe Zeile mit `2>&1` je **rc 0**, während `bash` zurück in den Baum
ging und die geschützte Datei änderte. Eine Operandenliste, die dieser Leser nicht verbuchen kann,
ist seither keine Bewegung, die er **nicht macht**, sondern eine, die er nicht **ausrechnen** kann:
die Position wird unbekannt (H20). Die Gegenrichtung derselben Verbuchung war schon vorher ein
Durchlass in einem Werkzeugaufruf: `cd "<außerhalb>" x ; <schreiben>` und `cd -q "<außerhalb>" ;
<schreiben>` waren rc 0, während `bash` „too many arguments" bzw. „invalid option" sagte, **stehen
blieb** und die geschützte Datei wirklich änderte (Abschnitt 1 des Protokolls zu TSK-0015). **Was
als Reibung bleibt:** die Zeile wird auch dann verweigert, wenn die Shell wirklich draußen steht —
`cd -L` und `2>&1` tragen ihren Grund oben, je einen eigenen. **Vorschlag:** offen lassen und die
Reibung melden, wenn sie jemandem begegnet. In der gekreuzten Tabelle ist `cd -L` seit TSK-0017 eine
eigene Zelle mit **zwei** Spalten (die Shell geht, der Leser bleibt) und seit TSK-0019 in **beiden**
Richtungen gekreuzt, also 16 gemessene Zellen statt einer Fußnote. Rot ohne den Fix:
`test_gate1_refuses_a_line_exactly_where_the_shell_would_write`.

**Zellen der gekreuzten Tabelle, auf denen dieser Eintrag steht:**
`cd with an option the shell accepts`, `cd with an option the shell rejects`,
`cd with a second operand the shell rejects`, `cd behind the end of the options`,
`pushd with a second operand the shell rejects`, `a pop whose operand the shell rejects`,
`a pop with an option the shell rejects`, `a pop of an index the stack does not have`,
`a pop that only drops the entry`, `a push that only adds an entry, then a pop`.

### H30 — Ein Wort, das die Shell nicht als dieses Verb ausführt, und ein Pop ohne sichere Richtung (neu, TSK-0017)

**Mechanismus, eine Eigenschaft mit drei Gesichtern:** der Leser fragte nie, ob die Shell das Wort
als **das Verb ausführt, für das er es hält**.

1. Er übernahm die Lesart der Kits (`_stage_verb`), und die **faltet die Groß-/Kleinschreibung** und
   nimmt den **Basisnamen**. Eine POSIX-Shell macht beides nicht: `CD` ist kein Befehl, und
   `/usr/bin/cd` ist ein externes Programm, das die Shell nicht bewegt.
2. Er kannte **eine** Verbliste für jede Shell. `set-location` ist ein Verb von PowerShell und in
   `bash` ein unbekannter Befehl.
3. Er nahm das Verb, das jene Lesart **hinter einem übersprungenen Wort** findet. Ein Wort vor dem
   Befehlsnamen ist aber ein Befehl für sich, und was er mit dem Rest macht, ist seine Sache:
   `env cd` erreicht das Builtin nie.

**Kette (gemessen 2026-08-07, `bash` als Schiedsrichter über die Datei,
`docs/reviews/2026-08-07-tsk0017-measurements.md`, Abschnitt 1):** elf Zeilen, alle in **einem**
Werkzeugaufruf und ohne Vorbereitung — `CD`, `Cd`, `cD`, `PUSHD`, `PushD`, `set-location`,
`Set-Location`, `/usr/bin/cd`, `env cd`, `nice cd`, `sudo cd`, jeweils mit einem Ziel außerhalb und
einem relativen Schreibzugriff dahinter. Die Shell meldet jedes Mal *„command not found"* bzw.
*„No such file or directory"*, **bleibt stehen** und ändert die geschützte Datei wirklich; das Gate
war der Bewegung gefolgt und antwortete **rc 0**.

**Zweite Hälfte: `popd` hat keine sichere Richtung** (Abschnitt 2 desselben Protokolls). Ein Pop
geht **zurück**, also ist Stehenbleiben dort nicht die verweigernde Antwort. Mit dem Stapelkopf
außerhalb und der Basis innerhalb waren `popd x`, `popd -q`, `popd +9`, `popd -n` und ein
`pushd -n <hier> ; popd` je **rc 0**, während `bash` die Operandenliste zurückwies, im Projekt blieb
und die geschützte Datei änderte. Die sechste Zeile ist die, die keine der anderen gezeigt hätte:
`R="<hier>" ; pushd "$R" ; cd "<außerhalb>" ; popd ; <schreiben>` — der Leser kann den Push nicht
ausrechnen, die Shell macht ihn, und der **bare** Pop dahinter geht auf einen Eintrag zurück, den
der Leser nie gesehen hat.

**Urteil: blockierend, geschlossen.** Drei Zweige, alle als Definition und keiner als Liste:
`_harness._directory_role` fragt die Verbtabelle **der Shell, die der Werkzeugname nennt**
(`SHELLS`), und vergleicht für POSIX zeichengenau und ohne Basisnamen;
`_harness._is_the_command_name` verlangt, dass vor dem Wort **nur Syntax** steht
(`_SYNTAX_CHARACTERS`, aus dem Zeichensatz des Tokenisers abgeleitet); und ein Pop, den der Leser
nicht ausrechnen kann, macht die Position **unbekannt** (`_UNKNOWN_POSITION`), woraufhin jeder
relative Kandidat als `_harness.Unplaceable` für **jeden** Aufrufer verweigert wird — ein absoluter
Pfad bleibt lesbar, und ein absolutes `cd` beendet den Zustand. Rot ohne die Fixes:
`test_gate1_refuses_a_line_exactly_where_the_shell_would_write` (alle drei Zweige einzeln
zurückgedreht, Abschnitt 6 des Protokolls). Dass die Werte der beiden Achsen aus den Aufzählungen
**erzeugt** werden, aus denen der Leser entscheidet, ist `DEC-0016` und steht in
`test_the_words_the_kits_reader_steps_over_are_all_crossed` und
`test_the_shells_this_reader_knows_are_the_ones_the_registration_names`.

**Zweite Hälfte der dritten Ursache, gemessen 2026-08-07 (`docs/reviews/2026-08-07-tsk0019-measurements.md`,
Abschnitt 2):** dass der Leser bei einem Wort vor dem Befehlsnamen **stehen bleibt**, war nicht nur
Reibung. Mit der Basis außerhalb waren `command cd "<hier>"`, `time cd "<hier>"` und
`! cd "<hier>"` je **rc 0**, während `bash` wirklich zurück in den Baum ging und die geschützte
Datei änderte. Das ist dieselbe Kette wie in H20 und dort mit allen sieben Schreibweisen aufgeführt;
geschlossen ist sie dort.

**Zusammensetzung, aus der Prüfmenge erzeugt und gegen sie geprüft
(`test_the_hole_list_states_the_over_refusal_the_table_carries`):** 64 von 1449 Zellen sind
Über-Verweigerung — die Shell schreibt **nicht** in den geschützten Baum und das Gate verweigert
trotzdem. Es sind genau die Bewegungen `cd into a directory that is not there`,
`cd into a relative directory that is not there`, `cd to a target this reader cannot name`,
`cd to a tilde the quoting keeps`, `cd with a second operand the shell rejects`,
`cd with an option the shell accepts`, `cd with an option the shell rejects`,
`pushd with a second operand the shell rejects`.

Was sie gemeinsam haben, ist der Grund und nicht die Schreibweise: der Leser kann die Bewegung nicht
ausrechnen und gibt die Position darum auf (H20). Die **Zusammensetzung stand hier bis 2026-08-07
falsch, und zwar in beide Richtungen**: sie nannte die Deskriptor-Verdopplung und die Wörter, die
die Kits vor dem Befehlsnamen überspringen — keines von beiden hat eine solche Zelle (die
übersprungenen Wörter haben Zellen, deren Shell-Spalte **nichts behauptet**, was etwas anderes ist)
— und sie ließ vier Bewegungen ungenannt, die die Hälfte der Zahl ausmachen. Nur die beiden Zahlen
stimmten, und eine Runde davor war der Satz schon einmal von Hand korrigiert worden. Darum steht er
jetzt nicht mehr als Prosa da, sondern wird aus der Tabelle erzeugt und in beide Richtungen
verglichen. Enger fassen ließe die Reibung sich nur mit einer Liste der Wörter, die ein Builtin
durchreichen — genau die Form, die diesen Eintrag erzeugt hat. **Vorschlag:** offen lassen und
melden, wenn sie jemandem begegnet.

**Zellen der gekreuzten Tabelle, auf denen dieser Eintrag steht:**
`enter spelled 'CD' -- run by the shell itself -- with the base outside it`,
`cd behind 'env', which the kits' reader steps over -- run by the shell itself -- with the base outside it`,
`a push and a pop`, `a push and a pop of the top by index`,
`a push and a bare push that swaps back`, `a push and one pop too many`,
`a pop whose operand the shell rejects`, `a pop with an option the shell rejects`,
`a pop of an index the stack does not have`, `a pop that only drops the entry`,
`a push that only adds an entry, then a pop`,
`a push this reader cannot make, and a pop the shell can`,
`a pop the shell really makes, back out of the tree`.

### H31 — Eine Erweiterung, die die Quotierung unterdrückt (neu, TSK-0019)

**Mechanismus:** eine Shell **erweitert** ein Wort und entfernt **danach** dessen Quotierung. Der
Leser bekommt von `_compat.shell_readings` das Ergebnis des zweiten Schritts — das Wort, wie das
Programm es sieht — und erweiterte darauf. Damit machte er genau die Erweiterung, die die
Quotierung verhindert hatte. Nicht die Tilde ist der Mechanismus, sondern die **Reihenfolge**: jede
Erweiterung, die eine Shell wegen der Quotierung unterlässt, gehört in dieselbe Klasse.

**Kette (gemessen 2026-08-07, `bash` als Schiedsrichter über die Datei,
`docs/reviews/2026-08-07-tsk0019-measurements.md`, Abschnitt 1):** `cd "~" ; <relativ schreiben>`
→ **rc 0**; die Shell sagt `~: No such file or directory`, **bleibt stehen** und ändert die
geschützte Datei wirklich. Dasselbe für `'~'`, `\~` und `"~/"`. Ende zu Ende, ein Werkzeugaufruf und
ohne Vorbereitung: `cd "~" ; python -c "…"` schrieb `.claude/settings.json` von 2903 auf 2 Byte —
die Registrierung aller vier Gates. Dieselbe Zeile **ohne** das `cd` ist rc 2.

**Urteil: blockierend, geschlossen — und einmal falsch geschlossen gewesen.** `_harness.readings`
gibt zu jedem Wert, den eine Shell einem Programm reichen könnte, mit an, ob eine Tilde darin
**erweitert** werden darf, und stellt diese Frage an die Schreibweise, die die Shell erweitert hat
(`_harness.TYPED_READING`, von `_harness.tokenise` an die Wörter der Kits gehängt) statt an den
Text, den das Programm bekommt. Zwei Dinge fallen daraus:

* erweitert wird nur die **erste** Lesart. Die weiteren sind dasselbe Wort ohne den Backslash der
  Kits, und ein Backslash ist auch Quotierung — `\~/x` ist einer Shell ein literales `~/x`. Die
  Kits führen dieselbe Unterscheidung an derselben Stelle und aus demselben Grund
  (`gate_write_scope._operator`: ein Wort, das zu `>` **auflöst**, ist keine Umleitung);
* **wo** die Quotierung steht, entscheidet — nicht, **ob** das Wort welche trägt. Genau das war die
  Nachbesserung vom 2026-08-07: die erste Fassung fragte „ist in dieses Wort irgendeine Spanne
  eingespleißt", also nach einer Eigenschaft des **ganzen Wortes**, und machte jedes quotierte Wort
  unerweiterbar. Das war kein Preis, sondern H33 in voller Breite wieder offen (Kette dort). Jetzt
  fragt `_harness._expands_a_tilde` die **Präfixspanne** der getippten Lesart, und nur eine
  Quotierung in ihr unterdrückt. Dass die Maskierung der Kits die quotierten Trennzeichen
  unsichtbar macht, gibt dabei genau die Regel der Shell her: das Präfix endet am ersten
  **unquotierten** Trennzeichen — gemessen 2026-08-07, `~+"/team-kits"/kernel/state.py` ist rc 0
  und `bash` schreibt die Datei nicht.

Rot ohne den Fix: `test_gate1_refuses_a_line_exactly_where_the_shell_would_write` (die vier Zellen
`cd "~"`/`cd ~` in beiden Richtungen); der rote Test der zweiten Hälfte steht mit ihrer Kette und
ihrer Prüfmenge in **H33**.

**Was bleibt, benannt statt behauptet — und der Satz, der hier bis 2026-08-07 stand, war falsch.**
Er sagte, ein Wort, dessen Quotierung woanders steht als die Erweiterung (`~/"x"`), werde nicht
erweitert, und nannte das Über-Verweigerung. Beides stimmte nicht: erweitert wurde es nicht, aber
verweigert wurde es auch nicht, und dieselbe Eigenschaft ließ `~+/"team-kits"/…` durch. Heute wird
`~/"x"` erweitert wie in einer Shell (gemessen: rc 0, die Shell schreibt ins Heimatverzeichnis).
Über-Verweigerung bleibt dort, wo dieser Leser die **Stellung** der Quotierung nicht sehen kann: ein
Wort, dessen führende Tilde hinter einer Quotierung steht (`""~+/team-kits/…`), wird verweigert,
obwohl eine Shell es literal lässt — gemessen 2026-08-07, Gate rc 2 und `bash` schreibt nichts.

**Der zweite Fall, der hier bis 2026-08-08 danebenstand, und wie er entstand.** Diese Stelle nannte
zusätzlich „eine Tilde, die nicht am Wortanfang steht (`x=~+/…`)" als gemessene Über-Verweigerung.
Sie ist keine: gegen ein Stellvertreterprojekt **außerhalb** des Heimatverzeichnisses ist die Zeile
**rc 0** (gemessen 2026-08-08). Die rc 2 der Vorrunde kam aus der **Lage der Messung** — das
Stellvertreterprojekt lag unter dem Verzeichnis, das ein bloßes `~` benennt, und genau dieses
Verzeichnis ist der einzige Kandidat, den der Substring-Scan aus so einem Wort gewinnt; ein
Verzeichnis, das geschützten Zustand **enthält**, wird für die Enthaltung verweigert (H19). Damit
maß die Zeile einen Vorfahren statt der Eigenschaft. Auch die zweite Hälfte des Satzes stimmte
nicht: `bash` **erweitert** `x=~+/y` zu `x=<cwd>/y` und lässt es nicht literal.

Die Eigenschaft, die stattdessen gilt, ist als **Prüfmenge** hinterlegt statt als Satz
(`test_gate1_answers_for_a_tilde_that_does_not_start_its_word`, Subjekte aus `_tilde_leads` erzeugt):
nachdem die Shell die Quotierung entfernt hat, beginnt das Wort entweder mit einer Tilde, deren
Präfix nicht leer ist — dann kann dieser Leser es nicht verorten und verweigert jedem —, oder es
beginnt nicht damit, und dann ist hier nichts zu verweigern. Ein Vorlauf, den die Shell **entfernt**
(die leere Spanne, die jedes Anführungszeichen des Lesers bilden kann), fällt in den ersten Fall,
ein Vorlauf, den sie **behält** (jedes Zeichen aus `test_gates._word_alphabet`, darunter das `=`,
an dem `x=~+/…` hängt), in den zweiten. Über keinen der beiden erreicht `bash` die geschützte Datei;
die Prüfmenge misst auch das, und die Bau-Entscheidung, die daraus folgt, steht in
`test_gates._base_outside_the_home_directory`: jedes Stellvertreterprojekt wird außerhalb des
Heimatverzeichnisses gebaut, sonst antwortet der Vorfahre. Rot ohne diese Bau-Entscheidung: derselbe
Test, im Klon mit dem Projekt unter `tmp_path` gefahren — elf Vorläufe, deren Zeichen
`_harness._PATHISH` nicht trägt, kamen mit rc 2 heraus.

**Geschlossen ist hier die Frage, OB erweitert werden darf — nicht, WOMIT.** Der Satz oben („nicht
die Tilde ist der Mechanismus") stimmt und war zugleich die Lücke: er beschrieb die Verzweigung, und
der **Wert**, den sie einspeist, war eine fremde Funktion, die eine andere Frage beantwortet. Diese
zweite Hälfte derselben Klasse ist **H33**; sie war offen, als dieser Eintrag „geschlossen" trug.

**Zellen der gekreuzten Tabelle, auf denen dieser Eintrag steht:**
`cd to a tilde the quoting keeps`, `cd to a tilde the shell expands`,
`a write into a relative path with the span 0 separators in quoted by "`,
`a write into a relative path with the span 1 separators in escaped`.

### H32 — Ein Befehl, den eine Ersetzung einführt (neu, TSK-0019)

**Mechanismus:** eine **Kommandoersetzung** ist ein eigener Befehl in einem Wort, und die Shell
führt ihn aus, bevor das Wort den Befehl erreicht, in dem es steht. Die Zerlegung schnitt dort
nicht: sie kennt Listentrenner, Stufenschnitte und Klammern, und ein Befehl in einem **Wort** kam in
ihr nicht vor. Damit war er beiden Gates unsichtbar — Gate 1 sah eine lesende Stufe (`echo`), und
Gate 3 wirft die committende Stufe als Ganzes weg, in der die Ersetzung stand.

**Kette (gemessen 2026-08-07, `docs/reviews/2026-08-07-tsk0019-measurements.md`, Abschnitt 3):**
`echo $(sed -i "s/a/b/" team-kits/kernel/state.py)` → **rc 0**, `bash` ändert die geschützte Datei
wirklich; ebenso in Backticks und in einem doppelt quotierten Wort (`echo "$(…)"`). Mit gültigem
Urteil im Baum, Ende zu Ende: `git commit -am wip $(sed -i s/prose/POISON/ docs/note.md)` → **rc 0**,
`docs/note.md` trug danach `POISON`, **HEAD bewegte sich**, und der Commit trug das Gift.

**Urteil: blockierend; geschlossen bis auf eine Hälfte, für die eine benannte Ausnahme steht,
Abnahme des Nutzers offen.**
`_harness.command_line` platziert den Befehl einer Ersetzung mit **derselben** Zerlegung wie jeden
anderen: sein Text geht durch `commands()`, seine Stufen durch dieselben Verb- und
Read-only-Fragen. Zwei Dinge über seine Stellung sind gesetzt statt ausgerechnet, beide in
verweigernder Richtung — er läuft **vor** der Zeile, in der er steht (eine Ersetzung hinter einem
Commit wird darum beurteilt, als stünde sie davor), und er läuft in einem **Kind**, also bewegt kein
Verzeichnisverb darin die Basis der Zeile um ihn herum. Wo die Ersetzung endet, wird in **zwei**
Lesarten beantwortet (`_harness._closings`), weil ein Schließer auf dieser Ebene nicht von einem
Zeichen in der Quotierung des Rumpfes zu unterscheiden ist: die ausbalancierte und die letzte.
Gemessen, warum es beide braucht: `echo $(sed -i "s/a/)/" <kitdatei>)` balanciert am `)` im
`sed`-Skript aus, und `bash` schreibt die Datei. Rot ohne die Fixes:
`test_gate1_refuses_a_line_exactly_where_the_shell_would_write` (die erzeugten Zellen aus
`_harness.SHELLS[...]["substitutions"]` und die Zelle mit dem quotierten Schließer) und
`test_gate3_refuses_a_line_that_moves_the_tree_before_it_commits`.

**Die Hälfte, die offen bleibt, ist ein Sonderfall von H34 und wird dort geführt.** Sie wurde hier
bis 2026-08-07 als „eine Ersetzung in einem quotierten **Nachrichtenargument**" beschrieben, also
mit der Schreibweise, an der sie vorgeführt wurde. Gemessen ist der Mechanismus breiter, und der
Vorspann dieses Abschnitts verlangt genau das andersherum. Die Kette dieser Hälfte:
`git commit -m "wip $(sed -i s/a/b/ team-kits/kernel/state.py)"` ist **rc 0** in Gate 1 wie in
Gate 3, und `bash` schreibt die geschützte Datei. **Warum nicht hier geschlossen, was stattdessen
begrenzt und was der Vorschlag ist:** steht in H34.

**Zellen der gekreuzten Tabelle, auf denen dieser Eintrag steht:**
`a write in a substitution whose closer is quoted`,
`a write in a $() substitution behind a read-only verb`.

### H33 — Die erweiternde Antwort kam von einer Funktion, die eine andere Frage beantwortet (neu, TSK-0021)

**Mechanismus:** ob eine Lesart erweitert werden **darf**, ist seit H31 richtig entschieden. Was die
Erweiterung **ist**, holte der Leser aus `os.path.expanduser`. Die beiden beantworten nicht dieselbe
Frage. Eine Shell liest alles zwischen dem führenden `~` und dem ersten Trennzeichen als **einen
Präfix** und löst ihn aus ihrem eigenen Zustand auf — Arbeitsverzeichnis, Herkunftsverzeichnis,
Verzeichnisstapel, Benutzerdatenbank. Die Bibliotheksfunktion kennt davon zwei Lesarten und
**schweigt zu den übrigen nicht**: sie macht aus jedem Präfix einen absoluten Pfad unterhalb des
Heimatverzeichnisses, den nichts schützt. Das ist die gefährliche Richtung: eine falsche Antwort,
keine verweigerte (`DEC-0020`).

**Kette (gemessen 2026-08-07, `bash` als Schiedsrichter über die Datei,
`docs/reviews/2026-08-07-tsk0021-measurements.md`, Abschnitt 1):** ein Werkzeugaufruf, ohne jede
Vorbereitung — `sed -i "s/a/b/" ~0/team-kits/kernel/state.py` war **rc 0**, und `bash` änderte die
Datei wirklich; dieselbe Zeile relativ geschrieben ist rc 2. Dieselbe Form erreichte
`.claude/settings.json` (die Registrierung aller vier Gates), `.claude/hooks/_harness.py` und
`project_memory/`, also kanonischen Zustand, der **jedem** verweigert ist. Mit einer Bewegung in
derselben Zeile kamen `~-`, `~-0` und `~1` dazu. **Zwei Formen kamen nur zufällig verweigert
heraus:** `~+` und `~+0` — nicht wegen eines Schutzes, sondern weil `+` in der Zeichenklasse
`_harness._PATHISH` fehlt, sodass der Teilstring `/team-kits/…` als eigener Kandidat übrig blieb;
gemessen war der Grund der Verweigerung dann das Heimatverzeichnis als **Vorfahre**, nicht das Wort.

**Zweite Kette, gemessen 2026-08-07 nach dem ersten Fix
(`docs/reviews/2026-08-07-tsk0022-measurements.md`, Abschnitt 1):** derselbe Mechanismus war durch
**eine Quotierung irgendwo im Wort** wieder vollständig offen. `sed -i "s/a/b/"
~+/"team-kits"/kernel/state.py` war **rc 0**, und `bash` änderte die geschützte Datei wirklich —
ebenso mit `'team-kits'`, mit der Quotierung um `kernel`, um `state.py`, und auf
`.claude/settings.json`, `.claude/hooks/_harness.py` und `project_memory/…` gerichtet. Ursache: der
Fix stand auf der Frage „trägt dieses Wort **irgendwo** eine eingespleißte Spanne" — einer
Eigenschaft des ganzen Wortes —, und eine Shell entfernt Quotierung **zeichenweise**: ein `"`
hinter dem Präfix unterdrückt gar nichts.

**Urteil: blockierend, geschlossen.** `_harness._tilde_prefix` ist die Spanne, nicht eine Liste von
Schreibweisen, und `_harness._expanded` delegiert nur noch dort, wo die delegierte Antwort die der
Shell **ist** — beim leeren Präfix. Jedes andere Präfix macht das Wort zu einem
`_harness.Unplaceable`, das für **jeden** Aufrufer verweigert wird und seinen eigenen Grund trägt.
Ob überhaupt erweitert wird, entscheidet seit der zweiten Kette `_harness._expands_a_tilde` an der
**Präfixspanne der getippten Lesart** (H31), nicht an einer Eigenschaft des ganzen Wortes.
Ein `cd` mit einem solchen Ziel macht dieselbe Aussage über die Position (`WorkingDirectory._resolve`
→ unbekannt, H20). Rot ohne den Fix:
`test_gate1_places_a_tilde_word_where_the_shell_puts_it` — für die erste Kette neun Zellen zugleich
(darunter `~0`, `~00` und `~-0` ohne Vorbereitung), für die zweite jede Zelle, in der die Quotierung
hinter dem Präfix steht.

**Was das kostet, benannt statt behauptet:** Über-Verweigerung für jedes Präfix, das eine Shell sehr
wohl auflösen kann und dieser Leser nicht — auf einem POSIX-Host trifft man zuerst den
**Login-Namen** (`~jemand/…`, gemessen rc 2, Shell schreibt nichts). Dazu jedes Wort, dessen Tilde
hinter einer Quotierung steht, die die Shell **entfernt** (`""~+/…`, `''~+/…`) — auch das gemessen
rc 2 bei einer Shell, die literal bleibt. Das ist derselbe Preis wie in H20 und trifft jeden
Aufrufer. **Was hier bis 2026-08-08 fälschlich mit in dieser Klammer stand**, war `x=~+/…`: das ist
rc 0, sobald das Stellvertreterprojekt nicht unter dem Heimatverzeichnis liegt, und die rc 2 der
Vorrunde war die Enthaltung dieses Verzeichnisses (H19), nicht das Wort — die Korrektur mit ihrer
Messung und der Prüfmenge, die die Eigenschaft jetzt trägt, steht in **H31**. Die Prüfmenge dieses
Tests kreuzt beide Enden: das leere Präfix bleibt erlaubt, wo die Shell es aus dem Baum führt, und
zwar in **jeder** Quotierung und jedem Zustand.

**Subjekte der Tilde-Prüfmenge, auf denen dieser Eintrag steht (aus ihr erzeugt und in beide
Richtungen gegen sie geprüft, `test_every_tilde_subject_a_closed_hole_names_is_one_the_check_set_carries`):**
7527 Subjekte aus 3 Zuständen und 157 Präfixen, gekreuzt mit der Achse, die bis 2026-08-07 fehlte —
**wo im Zielwort die Quotierung steht**: `with no quoting in it`, `with the tilde itself escaped`,
`with the tilde itself quoted by "`, `with the tilde itself quoted by '`,
`with the rest of the tilde prefix escaped`, `with the rest of the tilde prefix quoted by "`,
`with the rest of the tilde prefix quoted by '`, `with the span 1 separators in escaped`,
`with the span 1 separators in quoted by "`, `with the span 1 separators in quoted by '`,
`with the span 2 separators in escaped`, `with the span 2 separators in quoted by "`,
`with the span 2 separators in quoted by '`, `with the span 3 separators in escaped`,
`with the span 3 separators in quoted by "`, `with the span 3 separators in quoted by '`.
Vorher waren es 471 Subjekte, von denen **keines** Quotierung im Zielwort trug.

### H34 — Die Prosa-Entfernung löscht eine quotierte Spanne hinter einer Flagschreibweise, unabhängig vom Verb (neu, TSK-0021)

**Mechanismus:** beide Gates lesen den Befehlstext erst, nachdem die **Prosa-Entfernung der Kits**
darüber gelaufen ist (`_harness._prose_removed` → `gate_write_scope._MESSAGE_ARG_RX`). Diese sucht
eine von mehreren **Flagschreibweisen** und löscht die quotierte Spanne dahinter — **irgendwo auf
der Zeile und ohne das Verb anzusehen**. Damit verschwindet nicht nur eine Commit-Nachricht, sondern
jeder quotierte Operand, der zufällig hinter einer dieser Schreibweisen steht. Bis 2026-08-07 stand
diese Lücke als „eine Ersetzung in einem quotierten Nachrichtenargument" in H32, also mit der
Schreibweise statt dem Mechanismus.

**Kette (gemessen 2026-08-07, `bash` als Schiedsrichter über die Datei,
`docs/reviews/2026-08-07-tsk0021-measurements.md`, Abschnitt 3):** ein Werkzeugaufruf, kein Commit,
keine Ersetzung — `sed -i -e "s/a/b/" -b "team-kits/kernel/state.py"` ist **rc 0**, und `bash`
ändert die geschützte Datei wirklich. `-b` ist für `sed` ein echtes Boolean, der quotierte Operand
dahinter ist die **Datei**; die Prosa-Entfernung nimmt beides zusammen weg, und das Gate sieht eine
Zeile ohne Pfad. Dieselbe Zeile ohne das Flag ist rc 2. Die Hälfte, die H32 offenließ, ist derselbe
Mechanismus mit einem Verb, das die Schreibweise wirklich als Nachricht nimmt.

**Urteil: GESCHLOSSEN (TSK-0043, BUG-0020), mit benannter Resthälfte.** Der Datenverlust-Kern ist
zu: die Prosa-Entfernung der Kits ist an das **Verb** gebunden statt an die Flagschreibweise. Aus
`gate_write_scope._MESSAGE_ARG_RX` (einer line-weiten `re.compile`) wurde `_VerbBoundMessageRemoval`,
ein Objekt mit derselben `.sub(" ", text)`-Fläche, das die quotierte Spanne nur dann leert, wenn das
Verb des Segments, in dem die Flagschreibweise steht, wirklich eine Nachricht nimmt
(`_stage_takes_a_message`: die Forge-CLIs `gh`/`hub`/`glab` und `git` in den Unterbefehlen, die ein
`-m` tragen — `commit`/`tag`/`merge`/`notes`/`stash`). Nach `rm`/`cp`/`mv`/`Remove-Item`/`git rm`
bleibt der quotierte Operand die **Datei** und wird verweigert. Weil `.claude/hooks/_harness._prose_removed`
genau dieses Objekt **importiert und `.sub(" ", …)` darauf ruft**, schließt derselbe Fix auch das
Repo-Gate, das DEC-0001 gelöscht hat — ohne eine zweite Antwort auf „was ist Prosa" in `.claude/`
(H15). Gemessen (`bash`-Schiedsrichter über den Dateieffekt, Kopie außerhalb des Repos): defekt
`rm -f "project_memory/.../DEC-0001.yaml"` rc 0 → Datei WEG und `cp x -b "team-kits/kernel/hashing.py"`
rc 0 → Datei überschrieben; nach dem Fix beide rc 2, Datei unangetastet, während `git commit -m`,
`git commit --message='…'` und `gh issue create --body "…"` mit geschütztem Pfad in der Prosa rc 0
bleiben. Rote Tests ohne den Fix:
`tools/test_hooks_v2.py::test_a_write_verbs_quoted_operand_is_a_path_not_a_removable_message`
(die Fälle `rm -f`/`rm -F`/`cp -b` fallen von rc 2 auf rc 0) und, als Gegenende des Stolperdrahts,
`tools/test_hooks_v2.py::test_a_message_bearing_verb_keeps_its_prose_exemption`.

**Resthälfte, benannt statt geschlossen — H32 (Ersetzung IN einem Nachrichtenargument):** eine
**Kommandoersetzung** innerhalb der quotierten Nachricht eines message-tragenden Verbs
(`git commit -m "wip $(sed -i s/a/b/ team-kits/kernel/state.py)"`) wird von dieser Prosa-Entfernung
weiterhin ganz weggenommen, bevor irgendein Leser sie sieht — das ist gewollt (die Nachricht IST
Prosa), aber die Ersetzung darin ist ein Befehl, den der Kit-Gate nicht mehr sieht. **Warum nicht
hier geschlossen:** die Ersetzung innerhalb einer echten Nachricht von einer innerhalb eines
verkleideten `rm -f`-Operanden zu trennen, hieße den Ersetzungs-Inhalt zu lesen — die zweite Antwort
auf „was ist Prosa", die H15 verbietet. Auf der Repo-Seite ist genau diese Hälfte über
`_harness.command_line` (die die Ersetzung als eigenen Befehl platziert) schon erfasst und als **H32**
geführt; für den **Kit**-Gate allein bleibt sie offen. **Was stattdessen begrenzt: sozial** —
Rollentrennung und Item, wie bei H11 und H22. Der zweite bekannte Rest ist H38 (Hier-Dokument-Rumpf
über `_HEREDOC_RX`), unverändert.

### H35 — Was das Lesen einer Zeile kostet, war durch keine Frist begrenzt (neu, TSK-0021)

**Mechanismus:** `_harness.substituted_lines` prüfte das Budget des Gates **einmal je Aufruf** und
sagte im eigenen Docstring, es sei dadurch begrenzt. Die Arbeit steckt aber **in** einem Aufruf: die
Kosten wachsen mit dem Produkt aus Vorkommen und Länge, weil jedes Vorkommen zwei Lesarten
(`_closings`) erzeugt und beide rekursiv weitergehen. Zwischen zwei Prüfungen lag also die ganze
Zeit. Ein Gate, das noch entscheidet, wenn der Provider aufhört zuzuhören, wird getötet — und ein
getöteter Hook ist ein **Durchlass**.

**Kette (gemessen 2026-08-07, `docs/reviews/2026-08-07-tsk0021-measurements.md`, Abschnitt 2):**
gegen die registrierten 120 s antwortete Gate 1 auf 1006 Zeichen nach 24,1 s, auf 2006 Zeichen nach
106,6 s mit **rc 0**. Ende zu Ende, ein Werkzeugaufruf und ohne Vorbereitung:
`sed -i "s/a/b/" team-kits/kernel/state.py #` gefolgt von 1200 Ersetzungs-Öffnern und einem
Schließer — 2444 Zeichen — kam erst nach **150,6 s** heraus, also **nach** der Frist, während `bash`
die geschützte Datei wirklich änderte (das `#` versteckt die Öffner vor der Shell, nicht vor dem
Gate). Die grüne Suite sagte dazu nichts: sie fuhr keine Zeile dieser Form.

**Urteil: blockierend, geschlossen.** Die Grenze sitzt jetzt **außerhalb** der Entscheidung:
`_harness._the_budget_is_spent` läuft in einem eigenen Faden neben `guarded()` und beendet den
Prozess mit dem Verweigerungscode, sobald die Frist der Registrierung verbraucht ist. Damit ist die
Zusicherung keine Eigenschaft einer einzelnen Funktion mehr, sondern des ganzen Wegs. Gemessen nach
dem Fix, dieselbe Zeile: **rc 2 nach 96,2 s** gegen dieselben 120 s registrierten — und unverändert
96,2 s bei 8006 und bei 40006 Zeichen. Rot ohne den Fix:
`test_gate1_answers_before_its_registration_however_long_the_line_takes_to_read` (gemessen: 13,02 s
gegen eine Registrierung von 2 s).

### H36 — Ein einzelner Aufruf nach C gibt den Interpreter nicht zurück (neu, TSK-0021)

**Mechanismus:** der Faden aus H35 kann nur unterbrechen, was der Interpreter zwischen zwei
Bytecodes aus der Hand gibt. Ein einzelner Aufruf in eine C-Funktion tut das nicht. Der teuerste
davon auf diesem Weg ist die Heredoc-Erkennung der Kits (`gate_write_scope._HEREDOC_RX`), deren
Kosten quadratisch mit der Zahl der Öffner wachsen.

**Kette, und wo sie endet (gemessen 2026-08-07,
`docs/reviews/2026-08-07-tsk0021-measurements.md`, Abschnitt 4):** neben der Heredoc-Erkennung kam
ein Faden dieser Bauart in 8,07 s **einmal** dran, neben der Ersetzungs-Zerlegung 517-mal in
32,61 s — die Unterbrechbarkeit ist also gemessen und nicht angenommen. Die Frist reißt diese Stelle
erst bei rund 480 000 Zeichen (129,5 s gegen 120 s registrierte). **Und genau dort endet die Kette
auf diesem Host:** eine Zeile dieser Länge bekommt keine Shell mehr gestartet — gemessen schrieb
`sed -i … <kitdatei>` mit 4000 Heredoc-Öffnern (24 042 Zeichen) die geschützte Datei wirklich und
das Gate antwortete nach 0,6 s, während ab 36 042 Zeichen die Prozesserzeugung des Betriebssystems
mit „Der Dateiname oder die Erweiterung ist zu lang" abbricht und **nichts** mehr läuft.

**Urteil: Rest, keine Angriffskette auf diesem Host** — und das ist eine Messung über die
Prozesserzeugung, keine über das Gate. **Was sie ändern würde:** ein Provider, der die Zeile über
eine **Datei** statt über ein Argument an die Shell gibt, hebt die Längengrenze auf, und dann läuft
die Kette durch; die Nutzlastgrenze der Hooks (`_compat.STDIN_LIMIT`, 16 MiB) liegt weit darüber.
**Warum nicht geschlossen:** von Python aus ist ein laufender C-Aufruf nicht unterbrechbar, und die
einzige Grenze, die von hier aus bliebe, wäre eine Längenzahl — also die Sorte Zählung, die
`substituted_lines` ausdrücklich nicht führen wollte. Die Reparaturstelle liegt im **Kit**, beim
Ausdruck selbst.

### H37 — Die Messvorrichtung selbst schreibt den Baum, den sie misst (neu, TSK-0022)

**Mechanismus:** jede Zeile beider Prüfmengen nennt ihr Ziel **relativ**
(`test_gates.RELATIVE_WRITE`), und was sie vom echten Arbeitsbaum fernhält, war **allein** das
`cwd=` an einer Stelle (`_changes_the_protected_file`). Eine Tilde löst aber nicht gegen `cwd` auf,
sondern gegen den **eigenen Zustand der Shell**, und zwei Teile davon kommen über die **Umgebung**
herein: `~+` liest `PWD`, `~-` liest `OLDPWD`. Eine Suite, die im Baum gestartet wird, den sie
misst — genau so, wie `CLAUDE.md` es vorschreibt —, reicht diesen Baum in `OLDPWD` weiter, und `~-`
ist ein Subjekt der Prüfmenge. Damit schreibt eine Zeile mit **völlig richtigem** `cwd` in den
echten Baum.

**Kette (gemessen 2026-08-07, `docs/reviews/2026-08-07-tsk0022-measurements.md`, Abschnitt 3):**
`team-kits/kernel/state.py` dieses Repos kam dreimal in zwei Tagen mit dem ersten `a` jeder ihrer
928 Zeilen durch `b` ersetzt heraus, und der Kernel importierte nicht mehr. Zweimal wurde das einem
Messskript im falschen Verzeichnis zugeschrieben. Beim dritten Mal schlug der Sitzungsriegel
(`the_repo_is_not_a_sandbox`) **während** des Laufs an und nannte die Datei, und der Mechanismus
ließ sich isolieren: mit `cwd` = Sandbox und `OLDPWD` = ein anderer Baum druckt
`printf "%s\n" ~-` den anderen Baum, und `sed -i "s/a/b/" ~-/team-kits/kernel/state.py` schreibt
die Datei **in ihm**. Das Verzeichnis war nie die ganze Antwort.

**Ein vierter Schaden, 2026-08-08 — und er zeigt, wo die Vorrichtung die Kette NICHT unterbricht**
(Abschnitt 20 desselben Protokolls). Diesmal war es die **Rotmessung**: ein Klon außerhalb des
Repos, in dem der Pin absichtlich mutiert wird. Der Klon war korrekt, der Sitzungsriegel lief mit —
aber **im Klon**, und ein Riegel im Klon sieht keinen Schaden am Original. Der Mechanismus ist
derselbe: der Messprozess wurde aus einer Shell mit `cd` gestartet, erbte damit
`OLDPWD = <dieses Repo>` (nachgemessen), und die mutierte Fassung setzte `OLDPWD` nicht. Genau ein
Präfix der 157 schreibt den `OLDPWD`-Baum (`~-`, nachgemessen), zwei Umgebungen des Laufs liefen mit
dem geerbten Wert — und der Arbeitsbaum trägt exakt **zweimal** `sed -i "s/a/b/"` über der
Index-Fassung, byte-genau nachgerechnet. **Die Lehre steht in Rest 1**: eine Rotmessung ist nicht
irgendein Skript daneben, sondern die eine Gattung Lauf, die den Schutz absichtlich ausbaut und die
feindliche Lage deshalb aus ihrer **eigenen** Umgebung bekommt.

**Urteil: blockierend, geschlossen für den Mechanismus dieses Eintrags — mit benannten Resten, die
unten einzeln stehen (Rest 1 bis Rest 5) und nicht dieselbe Klasse sind.**
`_changes_the_protected_file` **setzt** die Verzeichniszustände der Shell auf die
Sandbox — durch `_sandbox.sandbox_environment`, also mit derselben Antwort, auf der auch die
Skripte neben dieser Datei stehen —, statt sie zu erben. Rot ohne den Fix:
`test_the_arbiter_cannot_be_pointed_out_of_its_sandbox_by_the_state_a_tilde_reads` — der Test zeigt
`PWD`/`OLDPWD` absichtlich auf einen dritten Baum, fährt **jedes** Präfix des Alphabets und
verlangt, dass dieser Baum unberührt bleibt; gemessen im Klon ohne den Fix schlug er mit
`assert 'b' == 'a'` an.

**Wovon der Sitzungsriegel lebt, und wovon nicht:** er bewacht **Läufe dieser Datei**. Ein
Messskript **daneben** — die Vorrichtung eines Prüfers, ein Einzelversuch aus einer Shell — fällt
nicht darunter, solange keine Suite läuft; läuft eine, meldet der Riegel den fremden Schreibzugriff
mit (sein Docstring sagt genau das). Das ist Rest 1 unten. Ein Riegel für alles, was in diesem Repo
eine Shell startet, wäre ein Gate, und Gate 1 ist es bereits — es verweigert genau diese Zeile,
wenn sie durch ein Werkzeug kommt, und sieht nicht, was ein Python-Prozess selbst startet.

**Was stattdessen begrenzt — und was hier bis 2026-08-08 stand, war eine Zusicherung über eine
Vorrichtung, die sie nicht baute.** Der Satz nannte „jedes Messskript pinnt sein
Arbeitsverzeichnis und hasht die vom Zielpfad benannten Dateien". Beide Hälften waren gemessen
falsch: das Pinnen betraf **nur** `cwd` und ließ `OLDPWD` auf dem echten Repo stehen — genau der
Mechanismus dieses Eintrags —, und die Wachliste aus einem Spannen-Scan über die Zeilen fand von
vier geschützten Zieldateien **eine**. Was heute an der Stelle steht, ist Code neben der Suite,
`.claude/hooks/_sandbox.py`, und drei Tests messen ihn:

* `pin()` schreibt die Verzeichnis-Namen, die ein Kindprozess erbt, in `os.environ` — welche das
  sind, sagt `_sandbox.POINTED_AT_THE_SANDBOX`/`DROPPED` und **nicht dieser Eintrag**; es bleibt
  eine Aufzählung, und der Stolperdraht dazu steht unten. Dazu verweigert `pin()` eine Sandbox, die
  im Repo liegt oder es enthält. Gemessen mit Köder-Baum:
  `test_the_measurement_sandbox_leaves_a_child_shell_no_directory_word_that_names_another_tree` —
  der Kontrolllauf mit geerbtem Zustand **beschädigt** den Köder wirklich, der gepinnte lässt ihn
  unberührt und trifft dabei die eigene Sandbox. **Was hier bis 2026-08-08 stand („`pin()` setzt
  **jede** Verzeichnisangabe"), war gemessen falsch**: `HOME` und `CDPATH` waren nicht dabei, und
  beide steuern Wort-Erweiterung — `~/…` schrieb den Köder, und `cd <köder> && sed -i …` fand ihn
  über `CDPATH`. Beide sind seit dieser Runde gebaut;
* die Wachliste ist die **geschützte Menge** des Gates selbst (`_harness.ProtectedArea.verdict`
  über die Bereiche, die dieses Objekt nennt), nicht das, was eine Zeile buchstabiert;
  `test_the_measurement_watch_list_is_the_area_the_gate_protects` vergleicht sie als
  Mengen-Gleichheit gegen einen unabhängigen Lauf über den Baum, also in beide Richtungen;
* der Wiederherstellungspfad prüft sein **Ziel** und nicht seinen Prozess
  (`test_an_index_restore_refuses_a_target_outside_the_pinned_sandbox`). Vorher prüfte er nur, ob
  der Prozess gepinnt war — womit ein falsches erstes Argument in den Arbeitsbaum schrieb, also
  dieselbe Klasse, um die es hier geht.

**Was diese Vorrichtung nicht deckt — fünf benannte Reste. Keiner ist blockierend: sie liegen alle
in der Messvorrichtung, nicht im Schutz, den die Gates bauen.**

**Rest 1 — sie wirkt nur, wo ein Skript sie importiert.** Ein Prozess, der sie nicht benutzt, ist
unbewacht wie zuvor. **Warum nicht schließbar:** eine Vorrichtung kann nur bewachen, was in ihrem
eigenen Prozess entsteht. **Gemessene Kette, 2026-08-08 (der vierte Schaden oben):** die schärfste
Gestalt dieses Restes ist die **Rotmessung** selbst. Sie läuft in einem Klon außerhalb des Repos —
was sicher aussieht und es für den Klon auch ist —, aber sie **baut den Pin absichtlich aus**, und
was dann in die Lücke tritt, ist die Umgebung, aus der der Messprozess gestartet wurde. Ein Start
über `cd <sandbox> && python …` reicht dem Prozess `OLDPWD = <das Repo>` weiter; der mutierte Pin
setzt es nicht; `~-` schreibt das Original. **Was stattdessen begrenzt, und es ist Handarbeit:** die
geschützte Menge des **Originals** um jeden Rotlauf herum hashen (`_sandbox.protected_files` /
`watch`), nicht nur um die Läufe im Arbeitsbaum, und den Messprozess nicht aus einer Shell starten,
die vorher im Repo stand. Beides ist Disziplin und kein Riegel — ein Riegel dafür wäre ein Gate, und
Gate 1 sieht nicht, was ein Python-Prozess selbst startet.

**Rest 3 — die Namensliste bleibt eine Aufzählung, und sie ist an beiden Enden verdrahtet.**
`POINTED_AT_THE_SANDBOX`/`DROPPED` behaupten nicht, dass eine Shell keine weiteren Namen liest;
gemessen ist nur, was gemessen wurde. Was der Stolperdraht leistet:
`test_the_measurement_sandbox_leaves_a_child_shell_no_directory_word_that_names_another_tree` fährt
jeden Namen **einzeln zurückgestellt** und vergleicht die gemessene Menge „trägt einen Baum" gegen
`_sandbox.NOT_MEASURED_TO_CARRY_A_TREE`. Damit fällt beides auf: ein Name, der entgegen der
Behauptung doch einen Baum trägt (`PWD` oder `DIRSTACK`, sobald eine Shell sie nicht mehr selbst
herleitet), und ein Name, der für nichts behandelt wird. **Was er nicht leistet:** einen Namen
finden, den niemand in die Liste geschrieben hat — die Prüfmenge fährt genau zwei
Nutzlast-Gestalten, „Tilde-Präfix" und „relatives Wort über eine Suchliste".

**Und dahinter steht eine offene Gattung und ausdrücklich keine „dritte Gestalt": was eine Shell
beim Start aus der Umgebung liest, ist nicht auf Verzeichnis-Wörter beschränkt.** Verzeichnis-Pinning
kann diese Gattung grundsätzlich nicht begrenzen, weil ihre Mitglieder entweder ein **Programm**
einbringen oder die **Auflösungsregel** verstellen, statt ein Ziel zu nennen. Gemessen 2026-08-08,
und die folgende Aufzählung ist die Ausbeute dieser Messung, nicht der Rand der Gattung:

* `BASH_ENV` auf eine Datei gezeigt — schon `bash -c true` führt deren Inhalt aus, und die Zeile
  darin hat den Köder außerhalb der Sandbox geschrieben (`decoy='b'`), **mit** der heutigen
  Sandbox-Umgebung davor;
* `BASHOPTS=cdable_vars` — ein **Schalter**, kein Ziel: er macht jede exportierte Variable zu einem
  gültigen `cd`-Ziel, womit ein Name, den niemand für ein Verzeichniswort hält, einen Baum trägt;
* eine **exportierte Shell-Funktion** (`BASH_FUNC_sed%%=() { … }`) — wie `BASH_ENV` ein Programm
  statt eines Wortes, und sie besetzt dabei den Namen eines Befehls, den die Nutzlasten selbst
  aufrufen.

Gemessen **nicht** tragend: `ENV` (`decoy='a'`), `SHELLOPTS=posix`, `TMPDIR`, `GLOBIGNORE`,
`MAILPATH`, `HISTFILE`, `PROMPT_COMMAND`.

**Warum nicht in dieser Runde geschlossen:** einen dieser Namen in `DROPPED` zu schieben wäre je
eine Zeile, aber der Stolperdraht dieser Liste verlangt für jeden Namen eine Nutzlast-Gestalt, die
ihn misst — also weitere Prüfmengen und weitere Partitionen, und das ist eine eigene Änderung mit
eigener Rotmessung. Bis dahin wäre es ein Name, der behandelt aussieht und nicht gemessen ist, also
genau die Sorte Zusicherung, die diesen Eintrag entstehen ließ. **Was stattdessen begrenzt:** die
feindliche Lage muss ein **Elternprozess** herstellen. Gemessen 2026-08-08 in der Sitzung, die diese
Suite startet, sind `BASHOPTS`, `SHELLOPTS`, `BASH_ENV`, `ENV` und `CDPATH` dort sämtlich ungesetzt
— ebenso `OLDPWD`, das eine Shell mit einem `cd` davor allerdings sehr wohl setzt (Rest 1). Damit
läuft innerhalb einer Sitzung keine Kette durch, und nach `DEC-0022` §2 bleibt die Gattung ein Rest
statt einer Runde. Und die Kontrollhälfte desselben Tests verlangt, dass die geerbte Lage den Köder
wirklich beschädigt — die Prüfmenge fährt also nachweislich etwas.

**Rest 4 — `watch` sieht eine Bewegung, keine Neuanlage** (`.claude/hooks/_sandbox.py`, Klasse
`watch`). Die Pfadliste wird beim **Betreten** eingefroren, und verglichen werden nur Digests; eine
Datei, die ein Lauf im geschützten Baum **anlegt**, kommt in beiden Aufnahmen nicht vor.
**Gemessene Kette (2026-08-08, gegen eine Kopie dieses Baums außerhalb des Repos, 420 geschützte
Dateien):** ein von Hand angelegtes `project_memory/evidence/active/EVD-9999.yaml` — für das
`ProtectedArea.verdict` *everyone* antwortet — passierte den Riegel **still**, während die
Kontrolle (eine Änderung an `team-kits/kernel/state.py`) korrekt mit „REPO DAMAGED" anschlug. Das
ist genau die Schreibklasse, mit der `ProtectedArea` begründet, warum
`project_memory/` **jedem** verweigert wird — ein handgeschriebenes `EVD` mit `result: pass` öffnet
`git commit`. **Warum nicht in dieser Runde geschlossen:** die Reparatur ist ein Mengenvergleich
statt eines Digest-Vergleichs, also eine Änderung an der Vorrichtung mit eigener Rotmessung; sie
lag außerhalb dessen, was diese Abschlussrunde tragen sollte. **Was stattdessen begrenzt:** Gate 1
verweigert denselben Schreibzugriff, wenn er durch ein **Werkzeug** kommt — unbewacht ist allein,
was ein Python-Prozess selbst startet.

**Rest 5 — „Sandbox im Repo" ist ein Pfadvergleich, der die Win32-Namensräume nicht kanonisiert**
(`_sandbox._inside`, benutzt von `pin()` und von `restore_from_index`). Die Verweigerung steht auf
`os.path.realpath` + `os.path.commonpath`. **Gemessene Kette (2026-08-08), innerhalb der
Vorrichtung:** Groß-/Kleinschreibung (`inside=True`), `..` (`True`) und der echte 8.3-Kurzname
`C:\OFFLIN~1\AGENTA~1` (`True`) greifen — aber `\\?\C:\…` (`False`), `\\localhost\C$\…` (`False`)
und `\\?\C:\OFFLIN~1\AGENTA~1` (`False`) werden **akzeptiert**, also gepinnt, obwohl sie dieselbe
Repo-Wurzel benennen; `restore_from_index` prüft gegen dieselbe Funktion und schriebe dorthin
zurück. **Warum nicht in dieser Runde geschlossen:** derselbe Grund wie bei Rest 4 — Umfang.
**Fix-Richtung, und zwar nicht als zweite Antwort:** die Autorität steht nebenan — `_harness`
beantwortet „dieselbe Datei" über `(st_dev, st_ino)` (`_anchored`/`_identity`) statt über
Schreibweisen, und genau diese fünf Namensräume sind dort schon gemessen (TSK-0008). `_sandbox`
sollte diese Antwort benutzen, statt Namensräume aufzuzählen oder mit `os.path.splitdrive` eine
eigene zu bauen. **Was stattdessen begrenzt:** Gate 1 ist von dieser Lücke **nicht** betroffen — es
liest über `_harness` und kanonisiert die Namensräume; betroffen ist allein die Wahl der Sandbox in
einem Messskript, und die trifft der Mensch, der das Skript schreibt, nicht die Nutzlast.

**Rest 2 — eine zweite Vorrichtung schreibt denselben Bereich, und sie ist nicht die des Prüfers,
sondern die Suite der Kits (gemessen 2026-08-08).** `team-kits/*/hooks/_audit.py` (`record_event`)
legt seinen Pfad über `_root.find_repo_root()` an, und das läuft von `cwd` aufwärts bis zum ersten
`.claude`/`project_memory`/`.git` — also landet ein Kit-Hook-Prozess, der irgendwo **in** diesem
Repo gestartet wird, auf `<repo>/project_memory/.audit/`. Gemessen: die Datei
`project_memory/.audit/hook_events.jsonl` **existiert** in diesem Arbeitsbaum, ist von **keiner**
`.gitignore`-Regel gedeckt (`git check-ignore` rc 1) und ist untracked (`??`). Damit schreibt
`pytest tools/` kanonischen Zustand des Baums, den es misst, in genau den Bereich, den Gate 1
**jedem** verweigert, und der Sitzungsriegel sieht es nicht: seine Wachliste entsteht aus einer
Sandbox, in der diese Datei nicht vorkommt.

**Die Eigenschaft, und ausdrücklich keine Zählung: jeder Lauf hängt an.** Hier stand bis 2026-08-08
eine Zahl (43 Ereignisse), und sie war beim Lesen schon falsch — der Abnahmelauf derselben Runde,
die sie hingeschrieben hat, hatte drei weitere angehängt. Eine Zahl an dieser Stelle misst den
Zeitpunkt des Schreibens, nicht den Mechanismus.

**Und die Kette ist nicht erschlossen, sondern am eigenen Abnahmelauf ausgelöst worden**
(2026-08-08, Runde 2 von TSK-0022): der von `CLAUDE.md` vorgeschriebene Lauf `pytest tools/ -q` hat
`hook_events.jsonl` verlängert — ein Schreibzugriff in den für TSK-0022 **verbotenen** Bereich,
ohne dass ein Werkzeugaufruf des Umsetzers ihn ausgelöst hätte. **Der Unterschied, den ein Leser
dieser Liste erkennen soll:** das ist **kein Scope-Verstoß des Pakets**, sondern ein **Defekt der
Kits**. Gate 1 sieht diesen Schreibzugriff nie, weil er aus einem Kit-Hook-**Unterprozess** kommt
und nicht aus einem Werkzeug; das Item konnte ihn also gar nicht verbieten, und der Umsetzer konnte
ihn nicht vermeiden, ohne den vorgeschriebenen Abnahmelauf zu unterlassen. Zurückgesetzt wurde er
nicht: die Datei ist untracked, und ein Rücksetzen wäre selbst ein Eingriff in den verbotenen
Bereich. **Warum nicht hier schließbar:** die Reparaturstelle liegt im Kit (`_audit.record_event`
und die Wurzelauflösung darunter), und `team-kits/**` ist für TSK-0022 verbotener Bereich. **Was
stattdessen begrenzt:** nichts Technisches — die Datei ist sichtbar (untracked in `git status`) und
kein Beweismittel, mit dem Gate 3 urteilt; ein `EVD` entsteht dort nicht. Die Begrenzung ist damit
**sozial**, wie bei H11.

**Vorschlag:** die Messdisziplin als Pflichtfeld in jeden Prüf- und Umsetzerauftrag, zusammen mit
H11 und H12 als Rollen-/Berechtigungsentscheidung des Nutzers.

### H38 — Ein Programm, das ein Hier-Dokument einer Shell übergibt, liest keines der Gates (neu, TSK-0022)

**Mechanismus:** beide Gates lesen den Befehlstext erst, nachdem die **Prosa-Entfernung der Kits**
darüber gelaufen ist (`_harness._prose_removed`). Die entfernt neben dem Nachrichtenargument (H34)
auch **jeden Rumpf eines Hier-Dokuments** (`gate_write_scope._HEREDOC_RX`), und zwar vollständig
und ohne den Befehl davor anzusehen. Ein Rumpf ist aber nicht nur, wohin man eine Commit-Nachricht
schreibt: er ist auch der Weg, auf dem eine Shell — oder jeder andere Interpreter — ein **Programm**
bekommt. Damit ist jedes Programm, das so übergeben wird, für beide Gates unsichtbar; was es tut,
steht in einer Spanne, die vor dem ersten Leser gelöscht wird. Der Mechanismus ist die Spanne, nicht
eine Schreibweise: welches Verb davorsteht und welche Sprache im Rumpf steht, spielt keine Rolle.

**Kette (gemessen 2026-08-08, `bash` als Schiedsrichter über die Datei,
`docs/reviews/2026-08-07-tsk0022-measurements.md`, Runde 2):** ein Werkzeugaufruf, keine
Vorbereitung, kein Commit. Ein Hier-Dokument, dessen Rumpf den relativen Schreibzugriff auf
`team-kits/kernel/state.py` trägt, ist **rc 0** an Gate 1, und `bash` ändert die geschützte Datei
wirklich; dieselbe Nutzlast als Argument derselben Shell ist rc 2. Es trifft ebenso einen Rumpf, den
die Shell nicht selbst ausführt, sondern weiterreicht (ein Python-Programm im Rumpf schreibt die
Datei genauso). **Was gemessen NICHT durchläuft:** steht ein `git commit` auf derselben Zeile,
verweigert Gate 3 sie — nicht, weil es den Rumpf läse, sondern weil das Verb davor
(`bash`) in der Read-only-Klassifikation der Kits kein lesendes ist.

**Urteil: blockierend — benannte Ausnahme, Abnahme des Nutzers offen.** **Warum nicht hier
schließbar:** die Reparaturstelle liegt in `gate_write_scope._HEREDOC_RX`, also im **Kit**, und
`team-kits/**` ist für TSK-0022 verbotener Bereich. Eine zweite Antwort auf „was ist Prosa" in
`.claude/hooks/` wäre dieselbe Drift, die H15 beschreibt und die H34 an derselben Stelle schon
einmal aufgehalten hat. **Was stattdessen begrenzt: nichts Technisches für den Schreibzugriff.**
Gemessen begrenzt ist allein die Commit-Hälfte (oben), und ein Nebengrund ist keine Maßnahme. Die
Begrenzung ist **sozial** — Rollentrennung und Item —, wie bei H11, H22 und H34.

**Wodurch es auffiele:** `test_gate1_does_not_see_a_program_a_here_document_hands_a_shell` hält die
Kante in beide Richtungen fest (dieselbe Nutzlast als Argument ist rc 2, im Rumpf rc 0 **und** die
Shell schreibt wirklich) und wird rot, sobald das Loch zugeht — dann sind Eintrag und Test zusammen
zu korrigieren. Dass die Blindstelle überhaupt dort **steht**, wo gelesen wird, hält
`test_every_span_the_kits_prose_removal_takes_out_is_named_where_it_is_documented` fest: es liest die
Ausdrücke aus dem Syntaxbaum von `_prose_removed` und vergleicht sie in beide Richtungen mit dem,
was `_harness.command_line` als seine Blindstelle nennt. Bis 2026-08-08 nannte dieser Docstring von
zwei Spannen **eine** — und der Absatz, der die Warnung sein sollte, war damit selbst die
Beruhigung.

**Was dieser Stolperdraht nicht sieht, und H38 stützt sich auf ihn.** Er liest den **Syntaxbaum**
und erkennt darin genau eine Gestalt: einen Attributzugriff, dessen Name auf `_RX` endet
(`modul._X_RX.sub(...)`). **Gemessene Grenze:** eine dritte Entfernung, die über einen **lokalen
Namen** läuft, lässt ihn grün; ebenso eine Entfernung in einer **gerufenen Hilfsfunktion**, deren
Quelltext er gar nicht liest, und jeder Ausdruck, dessen Name nicht auf `_RX` endet. In allen drei
Fällen wächst die Blindstelle beider Gates, ohne dass hier oder im Docstring etwas rot wird.
**Warum nicht in dieser Runde geschlossen:** der Fix ist ein Wechsel des Messpunkts — die
**Laufzeit** statt des Quelltexts, mit zählenden Stellvertretern für jeden `*_RX` des Kit-Moduls —,
also eine eigene Änderung mit eigener Rotmessung, und sie liegt in der Vorrichtung, nicht im
Schutz. **Was stattdessen begrenzt:** die Entfernung selbst steht im **Kit**, und jede Änderung
daran geht durch den Spiegel-, Versions- und Suite-Lauf der Kits; sie entsteht nicht nebenbei.

### H39 — Endzustände, die dieses Repo nicht ehrlich erreichen kann: TSK `DONE`, BUG `VERIFIED` (neu, TSK-0055)

**Mechanismus:** zwei Kernel-Wächter setzen Bedingungen voraus, die nur ein installiertes Kit
erfüllt, und dieses Repo betreibt bewusst keins (DEC-0003). Erstens verweigert
`state.py::_transition_locked` jeden direkten Übergang IN einen lease-gestützten Zustand
(`dispatch.assert_lease_backed_transition_locked`); die TSK-Kette führt über `LEASED` und
`IN_PROGRESS`, also sind `DONE` und `VALIDATED` ohne echtes Dispatch unerreichbar. Zweitens bindet
`approvals.APPROVAL_TRANSITIONS` die Kante `BUG TRIAGED→APPROVED` an eine Freigabe in Kraft;
gemünzt wird die über den PostToolUse-Haken der Kits auf der AskUserQuestion-Antwort, und die
Registrierung dieses Repos führt nur die vier Gates — die gedruckte Abhilfe der Verweigerung
(„Frage weiterreichen, die Antwort münzt") hat hier keinen Zuhörer. `VERIFIED` ist damit für jeden
Bug unerreichbar, solange kein Münzweg existiert.

**Kette (gemessen 2026-08-13, Runde TSK-0055):** `transition BUG-0031 APPROVED` → rc 1, „…is the
transition a scope approval commits, and none is in force for BUG-0031 at revision 1 -- refused
(fail-closed)". Die TSK-Hälfte ist aus dem Quelltext belegt (Lease-Wächter in
`_transition_locked` plus Kettenform in `backlog_types.AUTOMATA`), nicht aus einem Lauf — die
Messung hätte einen echten Zustandswechsel gekostet (`DRAFT→READY` ist frei und wäre unwahr), und
ein Beleg, der den Zustand belügt, wäre teurer als die Aussage.

**Folge für die Buchführung, entschieden in DEC-0041:** erledigte Arbeitsaufträge schließen hier
als `CANCELLED` — der Lieferbeleg liegt in den EVDs und Commits, nicht im Statuswort —, und
reparierte Bugs bleiben aktiv auf `TRIAGED` stehen, statt mit `REJECTED`/`DUPLICATE` belogen zu
werden. Dieser Bestand ist sichtbar und wächst mit jedem weiteren reparierten Bug.

**Urteil: kein Angriffsloch, eine Erreichbarkeitslücke der Buchführung — benannte Ausnahme
(DEC-0041).** **Warum nicht hier schließbar:** der Münzweg wäre entweder eine Registrierung in
`.claude/settings.json` oder ein Kernel-Münzkommando in `team-kits/**` — beides dem
**Sitzungsagenten** verwehrt (Gate 1 führt beide Bereiche als session-beschränkt; ein
Umsetzer-Subagent dürfte dort schreiben, der Änderungskreis existiert genau dafür). Es fehlt also
keine Schreibbarkeit, sondern eine eigene Runde mit eigener Sicherheitsabwägung — denn ein
Kommando, das ohne Nutzerantwort münzt, wäre genau das selbst ausgestellte Ja, das die
Verweigerung wörtlich verbietet. **Was stattdessen begrenzt:** DEC-0041 trägt die Bedeutung von
`CANCELLED`, und die Bugliste bleibt ehrlich sichtbar statt leergelogen.

**Wodurch es auffiele:** entsteht ein Münzweg (Kit-Installation in diesem Repo oder ein
Kernel-Kommando), widerlegt der nächste `transition BUG-nnnn APPROVED`-Lauf die gemessene Kette —
dann ist dieser Eintrag mit der neuen Messung zu schließen und DEC-0041 abzulösen.

### H40 — Vertragszitationen außerhalb der `.py`-Quellen von `.claude/hooks/` liest kein Stolperdraht (neu, TSK-0058)

**Mechanismus:** Der TSK-0058-Stolperdraht (`test_no_statement_here_cites_a_replaced_contract_on_its_own`)
findet die Zitation eines abgelösten Vertrags in den literalen Strings und Kommentarblöcken der
`.py`-Dateien von `.claude/hooks/` — und nur dort. Vertragsprosa lebt aber auch in der
Registrierung (`.claude/settings.json`, `_comment`), in den Rollendefinitionen
(`.claude/agents/*.md`), in `CLAUDE.md` und in `docs/`. Keine dieser Flächen liest ein Draht:
eine dort stehende Lebendzitation eines archivierten Vertrags altert unbemerkt. Zweite,
schmalere Grenze im selben Draht (gemessen, TSK-0058-Prüfung F4): eine Zitation, die erst zur
**Laufzeit** aus Teilen zusammengesetzt wird (f-String, `%`-Formatierung), ist auch in den
`.py`-Quellen unsichtbar — nur die implizite Literal-Konkatenation wird gefaltet und gefangen.

**Kette (gemessen 2026-08-14):** `.claude/settings.json:2` trägt „These four PreToolUse gates are
the replacement SR-0006 specifies" — eine Lebendzitation des seit 2026-08-13 abgelösten Vertrags in
genau der Datei, aus der der Provider liest. Mutation im Klon: `SR-0006 is the contract.` in den
`_comment` eingesetzt → der Stolperdraht bleibt **grün** (1 passed). Die Datei liegt im
`forbidden_scope` von TSK-0058 (Registrierung wird in einer Zitatrunde nicht angefasst); die
Behebung des einen Satzes ist eine eigene kleine Runde.

**Urteil: benannte Ausnahme, Abnahme offen.** **Warum nicht hier schließbar:** die Reichweite des
Drahts auf Nicht-Python-Prosa auszudehnen hieße, Markdown und JSON-Kommentare als Vertragssprache
zu parsen — eine eigene Vorrichtung mit eigenen Fehlformen; und die eine bekannte Instanz liegt im
verbotenen Bereich der Runde, die den Draht gebaut hat. **Was stattdessen begrenzt:** die bekannte
Instanz steht hier mit Fundstelle; der Draht deckt die Fläche, auf der die 14 gemessenen
Statements der Fehlerklasse lagen (alle in `.py`); die Rollendefinitionen und `CLAUDE.md` zitieren
heute keinen abgelösten Vertrag als geltend (gemessen: repo-weites grep, nur ehrliche Historie).
Dazu benannt (TSK-0058-Prüfung F5): die Zehner-Aufzählung der Automaten-Typen in
`_harness.py:2076-2078` ist heute wahr und von keinem Draht auf Vollständigkeit gepinnt — ein
elfter Typ machte den Satz still falsch.

### H41 — Vier gemessene Grenzen des Zeiger-Wächters (neu, TSK-0009)

Der Wächter (`test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists`, Leser
`_points_into_this_file`) macht seit TSK-0009 einen in Backticks genannten Testnamen prüfbar:
er muss in `test_gates.py` auflösen, sonst rot. Vier Grenzen sind gemessen — drei bei der Prüfung
2026-08-14, die vierte mit TSK-0059 —, keine hat eine Angriffskette, und der lebende Bestand ist
in den ersten drei Richtungen leer; in der vierten ist er nicht leer, aber vollständig aufgelöst:

**(a) Beide-Enden-Tabellen treiben ihren eigenen Wächter.** `SPELLINGS_OF_A_POINTER` und
`THIS_FILE_ITSELF` werden von Tests iteriert, die über genau diese Tabellen laufen — schrumpft die
Tabelle (ein Eintrag gelöscht, die Ableitung auf eine Schreibweise verengt), schrumpft der Wächter
mit und bleibt grün, während der Defekt erst beim nächsten echten Vorkommen im Sweep auffällt.
Die Prosa daneben behauptet keine Vollständigkeit — der Rest ist die fehlende zweite Messrichtung,
nicht ein falscher Satz.

**(b) Leerraum-Verklebung erzeugt aus Prosa einen erfundenen Zeiger.** Der Leser klebt Leerraum
aus einem Span (nötig für Zeilenumbrüche); ein Span der Form `` `test_wort weitere wörter` `` klebt
zu einem nie definierten Bezeichner zusammen und wird als fauler Zeiger GEMELDET — eine
Fehlalarm-Klasse, keine Lücke. Bestand: 0 Vorkommen.

**(c) Unpaarige Backticks verschieben die Span-Paarung.** `re.findall` paart von links; ein
einzelner Backtick vor einem echten Zeiger macht den Namen unsichtbar — weder gelesen noch
gemeldet. Bestand: 15 Aussagen mit ungerader Backtick-Zahl, alle Code-Stringliterale, keine mit
einem Testnamen dahinter.

**(d) Zeiger auf Tests ANDERER Dateien liegen außerhalb der Reichweite, und der Bestand wächst.**
Der Leser überspringt jeden Span mit einem Punkt, weil das ein Dateiname sein kann; ein Zeiger der
Form `` `tools/test_report.py::test_x` `` wird damit von niemandem nachgeschlagen. Gemessen
2026-08-14 über den H43-Eintrag: er trägt **sieben** solcher Zeiger, und der Leser gibt über diesen
Text `set()` zurück — er sucht keinen davon. Alle sieben lösen heute auf (einzeln im AST der
genannten Datei nachgeschlagen), das ist aber Handarbeit und kein Draht. Mit dem H44-Eintrag kamen
2026-08-15 **drei** dazu, alle in `tools/test_approvals_dispatch.py`, von Hand aufgelöst (Zeilen
2841, 2858, 2930) — Bestand damit **zehn**, alle aufgelöst, weiter Handarbeit. Dieselbe Klasse wie
(a) und wie **H40**: was außerhalb der Reichweite eines Wächters zitiert wird, sammelt sich an.

**Urteil: Rest, keine Angriffskette** — die Produktionsdateien sind AST-identisch, keine Grenze
berührt eine Gate-Entscheidung. Wer eine der vier schließt, misst zuerst die Richtung, die heute
fehlt (a: Tabellen-Vollständigkeit gegen eine zweite Quelle; b: ein Nicht-Bezeichner-Span mit
`test_`-Präfix wird beschrieben statt geklebt; c: Paarung, die einen unpaarigen Auftakt überspringt;
d: ein Zeiger `<datei>::<test>` wird in JENER Datei aufgelöst statt übersprungen).

### H42 — `INV.scope` als Liste geschrieben schaltete die Testabdeckungs-Regel still ab — GESCHLOSSEN (TSK-0060)

**Mechanismus:** der Vertrag der Typen, die `capture` erzeugt (`REQUIRED_FIELDS`/`OPTIONAL_FIELDS`),
nennt Feld**namen** und keine Formen — jedes dieser Felder kann also als Skalar **und** als Liste
ankommen. (Die andere Vertragshälfte, `kernel/schemas/*.yaml`, deklariert sehr wohl `type:` je Feld;
sie gilt für die eingefrorenen ARC/WFR/DSN, nicht für `INV`.) `BUG-0015` war die eine Richtung (ein
Skalar, das ein Leser buchstabenweise iteriert); dies ist die andere. Vier Leser lesen `INV.scope`
als **einen** Pfad bzw. **einen** Namen: `dev-team/hooks/gate_test_coverage.py:177`
(`str(item.get("scope") or "")`), `dev-team/hooks/guard_guidelines.py:128-129` sammelt den Wert
**roh** ein und `:154` (`_governs`) macht daraus `str(scope or "").strip()`, und
`dev-team/templates/repo/scripts/kit_checks.py:171` (dort als Konfigurationsschlüssel) sowie `:189`.
Eine Liste ergibt dort die Zeichenkette `"['compounder/']"`, die auf keinen Pfad passt.

**Kette (gefunden in der Prüfung zu TSK-0033, `dev-team`-Hooks als Prozesse, Projekt außerhalb des
Repos; die Verhaltensangaben in diesem Absatz sind der Stand VOR dem Fix und bleiben als
Fundprotokoll stehen — die vier Leser-Zeilennummern oben gelten unverändert weiter, denn an den
Lesern hat die Behebung nichts geändert):** ein `INV` mit
`scope: compounder/` und Code ohne Tests darunter → `gate_test_coverage.py` verweigert
`git push origin main` mit rc 2 („source area 'compounder/' has code but no tests"). Dasselbe
Projekt, dasselbe `INV`, nur `scope: ["compounder/"]` → **rc 0**, und `validate` sagte über genau
diesen Zustand **0 Befunde**. `kernel.capture` nahm beide Schreibweisen an. (Der Eintrag nannte hier
zusätzlich `migrate --map INV.scope=<v1-feld>` als zweiten Weg. Das ist **eine Flagge, die die
Oberfläche annimmt und die kein Lauf benutzt**: `parse_field_map` lässt den Ausdruck zu, aber keine
Zeile von `V1_STATUS_MAPPING` erzeugt den Typ `INV`, gemessen — elf V2-Typen, `INV` nicht darunter.)

**Die zweite Richtung, in der Behebungsrunde nachgemessen und im Eintrag vorher nicht enthalten:**
dieselbe Schreibweise **erfindet** anderswo eine Verweigerung. `guard_guidelines.py` ließ das
Schreiben von `api/service.py` unter `scope: api/` durch (rc 0) und verweigert es unter
`scope: ["api/"]` (rc 2, „no INV item of this project governs it"). Eine Feldschreibweise, zwei
Gates, die verschieden entscheiden — die verlorene Verweigerung war nur die eine Hälfte.

**Urteil: GESCHLOSSEN (TSK-0060, `DEC-0043`), mit benannten Resten.** Entschieden hat der Nutzer,
und die Entscheidung ist ein **Vertrag**, keine Normalisierung: ein `INV` regiert **genau einen**
Bereich (oder nennt genau einen Knopf), wer zwei will, schreibt zwei `INV`. `field_elements` gilt
hier ausdrücklich **nicht** — das wäre der verworfene Mehrere-Bereiche-Zweig, und für
`kit_checks.invariant_knob` („mehrere Namen") ohne Bedeutung. Gebaut ist das als eine Deklaration
(`backlog_types.SINGLE_VALUE_FIELDS` mit `holds_one_thing`/`single_value_offences`), die zwei
Stellen lesen: `state._assert_single_value_fields`, aufgerufen aus `capture_preflight` und aus dem
Editierpfad `_update_item_locked`, und `report._check_single_value_fields` als **Fehler** im
Validator. „Nicht ein Wert" ist dabei als Eigenschaft geprüft (alles Iterierbare außer der
Zeichenkette), nicht als Formenliste — die Einelement-Liste fällt darum genauso durch wie ein `dict`,
denn die Leser können einen Behälter überhaupt nicht auseinandernehmen.

**Die Ausnahme, die diese Eigenschaft in der ersten Fassung noch trug, ist gemessen und
geschlossen:** `bytes` stand neben `str` in der Ausnahme, und der Prüfer hat sie durchgemessen —
`update` nahm `scope: b'api/'` an, die Leser sahen `b'api/'`, `gate_test_coverage` ging von rc 2 auf
**rc 0**, und anders als bei der Listenform sagte auch der **Validator nichts**, es gab also nicht
einmal das Auffangnetz des Merge-Gates. Über ein ausgeliefertes Kommando war das nicht erreichbar
(`harness.py update` nimmt JSON, das keine Bytes kennt, und die Migration erzeugt keinen `INV`), es
war also keine Sitzungskette, aber es war eine Eigenschaft, die dieser Absatz behauptete und der Code
nicht baute. `holds_one_thing` nimmt heute nur noch die Zeichenkette aus.

**Gemessen nach dem Fix, gegen dasselbe Projekt außerhalb des Repos:** `capture` verweigert
`["compounder/"]`, `["compounder/", "engine/"]`, `("compounder/",)`, `{"area": "compounder/"}` und
die `bytes`-Formen (`b"compounder/"`, `bytearray`, `memoryview` — Prüfrunde 2) mit der
Zwei-Item-Abhilfe im Text; `capture_preflight` — die Funktion, die `migrate` beim **Planen**
fragt (`migrate.py:2143`) — verweigert dieselbe Form, der Import stirbt also nicht mitten im Lauf;
`update` verweigert sie ebenfalls. Für ein Projekt, das ein solches Item **schon trägt**, geht
`validate` von **0 auf 1 Fehler** („scope is a list where the contract is ONE value … one area per
rule — an invariant meant to govern two areas is TWO INV items"), und `gate_memory_complete`
verweigert damit sowohl `git push origin main` als auch `git merge` mit **rc 2** (vorher rc 0).

**Die vier Leser sind unverändert — Datei wie Verhalten**, und das ist der Punkt des Vertrags: sie
bleiben Ein-Bereich-Leser und sind jetzt durch den Vertrag richtig statt durch Zufall.
Nachgemessen an den laufenden Lesern: `kit_checks.governed_source_areas` liefert `['api']` unter der
Ein-Bereich-Form und `[]` unter der Listenform, `invariant_knob` den Wert bzw. den Vorgabewert,
`gate_test_coverage` rc 2 bzw. rc 0, `guard_guidelines` rc 0 bzw. rc 2.

**Rote Tests ohne den Fix** (je im Klon außerhalb des Repos, Defekt wiederhergestellt, rot gesehen):
ohne die beiden Aufrufe in `state.py`
`tools/test_state.py::test_a_several_things_inv_scope_is_refused_at_capture_and_on_the_edit_path`
(alle fünf Schreibweisen, `bytes` eingeschlossen — gemessen: 5 failed mit beiden entfernten
Aufrufen); ohne den Validator-Aufruf
`tools/test_report.py::test_validate_names_an_inv_scope_spelled_as_several_things` (die
Ausgangsmessung steht wörtlich im Fehlschlag: `found == []`) und
`tools/test_hooks.py::test_the_shipped_readers_of_a_single_value_field_still_read_one_value` (an der
Merge-Gate-Zeile). Beide Enden der Deklaration sind ebenfalls rot gesehen: ein Eintrag auf ein Feld,
das kein Vertrag des Typs führt, und einer auf ein Feld aus `REFERENCE_LIST_FIELDS`, gegen
`tools/test_backlog_types.py::test_the_single_value_fields_are_contract_fields_nothing_resolves_elementwise`;
und ein Leser, dem man die Listenform beibringt, gegen den Leser-Test oben.

**Rest 1 — ein bereits geschriebenes Item wird gemeldet, nicht geheilt, und seine Regel bleibt
solange aus.** Gemessen: mit dem Listen-Item verweigert `gate_test_coverage` weiterhin **nichts**
(rc 0) — was an die Stelle tritt, ist die Merge-Gate-Verweigerung derselben Zeile (rc 2), das
Projekt kommt also nicht an dem Item vorbei, statt still ungeschützt zu arbeiten. Repariert wird
über den Kernel-Editierpfad; `project_memory/**` hat einen Schreiber, und der ist kein Validator.

**Rest 2 — die Archiv-Türen nehmen die Form weiter an, und zwar absichtlich; für `INV` ist das heute
allerdings kein Fall, den ein Kommando erreicht.** Gemessen: `V1_STATUS_MAPPING` erzeugt elf V2-Typen,
`INV` ist keiner davon, ein migriertes `INV` gibt es also nicht — die Archiv-Türen sind für dieses
Feld eine reine Kernel-Oberfläche. Die Platzierung (außerhalb der gemeinsamen
`_assert_capture_shape`) ist deshalb **Disziplin für den nächsten Eintrag**, dessen Typ die Migration
sehr wohl erzeugen kann: ein archivierter Datensatz ist ein **Protokoll** dessen, was war (`DEC-0004`
nimmt ihn darum vom Feldvertrag aus), `DEC-0009` lässt den unübersetzbaren **mit seiner Begründung**
archivieren statt den Lauf anzuhalten, und eine Formprüfung dort hielte den Lauf an, ohne irgendetwas
zu schützen — kein Leser dieser Felder scannt das Archiv. Beide Hälften sind gemessen und nicht
behauptet: `tools/test_state.py::test_the_archive_door_still_takes_a_record_the_active_door_refuses`
wird rot, sobald die Prüfung in `_assert_capture_shape` wandert, und
`tools/test_state.py::test_the_migration_can_produce_no_inv_so_the_archive_boundary_is_for_the_next_entry`
wird rot an dem Tag, an dem eine V1-Zeile ein `INV` erzeugt.

**Rest 3 — der Vertrag ist eine Deklaration, keine Ableitung.** Beide Enden des einen Eintrags sind
verdrahtet (Feld aus dem Vertrag des Typs gefallen bzw. Leser, der mehrere liest), aber **nichts
leitet ab, welches WEITERE Feld ein solcher Eintrag sein müsste**: ein künftiger Leser, der ein
anderes Feld als einen Wert liest, fällt keinem Draht auf. Das ist dieselbe Klasse wie `H41`/`H40` —
was außerhalb der Reichweite eines Wächters entsteht, sammelt sich an.

**Rest 4 — im `office-team` ist die Verweigerung Reibung ohne örtlichen Leser.** Die vier Leser
sitzen in `dev-team` und `research-team` (`guard_guidelines.py`, `scripts/kit_checks.py` gespiegelt,
`gate_test_coverage.py` nur im `dev-team`); das Office-Kit hat keinen. Ein Office-Projekt, das
`scope: [belege/]` tippt, wird trotzdem verwiesen — der Vertrag sitzt im Kernel, der allen drei Kits
gemeinsam ist. Das ist die ehrliche Richtung (dieselbe Bedeutung des Feldes in allen Kits), aber es
ist Reibung, die dort heute keinen Leser schützt.

**Rest 5 — zwei gezählte Zahlen in Kernel-Kommentaren, die kein Draht pinnt** (Prüfrunde 2, N2/N3):
`state.py:1254` und `tools/test_state.py:233` sagen „elf V2-Typen" — heute wahr (gemessen), aber der
Test daneben pinnt nur `"INV" not in produced`, nicht die Elf; eine zwölfte Mapping-Zeile macht die
Prosa still falsch. `backlog_types.py:683` zählt „all three readers" für die `bytes`-Messung, ohne
zu sagen welche. Beides dieselbe SR-0008-Klasse (eine Zahl an einem zweiten Ort); Korrektur bei der
nächsten Berührung dieser Dateien — die Zahl streichen, nicht nachführen.

### H43 — Was der Kernel selbst schreibt, lag außerhalb der Feldmenge, die der Sweep abgeleitet hat — GESCHLOSSEN (TSK-0059)

**Mechanismus, als Eigenschaft und nicht als Liste:** der AC-4-Sweep dieser Runde leitet seine
Feldmenge aus der Oberfläche **eines Kommandos** ab — `migrate.parse_field_map:1145-1153` lässt nur
Felder aus `REQUIRED_FIELDS ∪ OPTIONAL_FIELDS` zu, und `_item_fields:1177` kopiert über dieselbe
Vereinigung. Das ist die Menge der Felder, die ein **Aufrufer** an `capture` übergibt. Der Zustand
hat aber einen zweiten Schreiber: den Kernel selbst (`state._update_item_locked`,
`staging.freeze_*`), und die Felder, die nur der setzt, stehen in keinem der beiden Tupel. Für das
Instrument waren sie damit nicht existent — nicht „sicher", sondern **ungemessen**. Dieselbe
Buchstaben-Iteration kann dort also stehen, und sie steht dort.

**Kette (gemessen 2026-08-14, Prüfung zu TSK-0033 — der Eintrag stammt aus jener Runde, die
Behebung aus TSK-0059). Alle Zeilennummern in dieser Kette sind der Stand VOR dem Fix und bleiben
als Fundprotokoll stehen; wo der Code heute steht, sagt das Urteil weiter unten:**

* `design_refs` (auf PR/RQ) — der Erzeuger ist `kernel/staging.py:319`:
  `refs = list(root.get("design_refs") or [])`, gefolgt von
  `state._update_item_locked(root_id, {"design_refs": refs})`. Ein skalares `design_refs` wird
  damit buchstabenweise zerlegt **und in den kanonischen Zustand zurückgeschrieben** — der einzige
  Fall dieser Klasse, der den Zustand selbst beschädigt statt nur eine Antwort zu verfälschen.
  **Ganz durchgemessen 2026-08-14, ohne jede Bearbeitung am Kernel vorbei:** `capture PR` nimmt
  `design_refs: design/revisions/DSN-0001.r01.html` als Skalar an (das Feld steht in keinem
  Vertragstupel, und `capture` weist unbekannte Felder nicht ab — `dispatch.py:492` beschreibt
  denselben Weg für eine Liste); anschließend schreibt `freeze_design` **35 Einträge** in den
  aktiven PR: 34 Buchstaben plus die neue Referenz. Die Revision blieb dabei `1 → 1`, es gab also
  auch keine Hash-Invalidierung, die es auffällig gemacht hätte. Die beiden Leser dahinter:
  `kernel/cli.py:675` druckt die Bestätigungszeile als
  `design_refs: d, e, s, i, g, n, /, r, e, …`, und `kernel/dispatch.py:479`
  (`[str(ref) for ref in (root.get("design_refs") or [])]`) verweigert damit einen UI-Task gegen
  ein Design, das es sehr wohl gibt.
* `supersedes` (DEC) — `kernel/report.py:1236` und `:1270`, beide
  `for ref in item.get(DEC_SUPERSEDES_FIELD) or []`.
* `premise_rechecks` (PR/RQ/CR) — `kernel/report.py:1154` und `:1170`.

**Die Richtung, und sie ist in allen drei Fällen dieselbe:** **Über-Verweigerung bzw. ein falscher
Bericht**, keine erteilte Erlaubnis. Ein UI-Spawn wird zu Unrecht abgelehnt, eine abgelöste
Entscheidung zu Unrecht als offen geführt, eine Bestätigungszeile falsch gedruckt. Kein Gate öffnet
sich dadurch. Bis TSK-0059 stand hier als Urteil eine **benannte Ausnahme mit offener Abnahme**;
die Kette läuft innerhalb einer Sitzung durch und war damit blockierend.

**Urteil: GESCHLOSSEN (TSK-0059, `BUG-0038`), mit benannten Resten.** Der Fix sitzt an den
**Lesern**, nicht an der Tür: `backlog_types.field_elements` — die eine Definition von „wie viele
Dinge hält dieses Feld", die `BUG-0015` eingeführt hat — steht jetzt an allen sieben Stellen, im
ausgelieferten Baum nachgemessen: `kernel/staging.py:326`, `kernel/dispatch.py:479`,
`kernel/cli.py:678`, `kernel/report.py:1157`/`:1173`/`:1239`/`:1278`.
Gemessen gegen ein Projekt außerhalb des Repos, über die ausgelieferten Kommandos: `freeze-design`
schreibt nach `capture PR` mit skalarem `design_refs` **2 statt 35 Einträge** in den aktiven PR und
druckt den Pfad statt `d, e, s, i, g, n, …`; derselbe UI-Task geht von *DISPATCH REFUSED
(„references that exist nowhere: d, e, s, …")* auf **DISPATCH ALLOWED**; ein skalares `supersedes`
lässt die abgelöste Entscheidung von *„zählt weiter als geltend"* auf **abgelöst** umschlagen, und
`validate` fällt über denselben Zustand von **17 auf 3 Befunde** (16 Phantom-Fehler, je einer pro
Buchstabe, verschwinden).

**Warum Normalisieren am Leser und nicht Abweisen an `capture` — gemessen, nicht abgewogen:** eine
Abweisung an der Tür hilft dem Item nicht, das den Skalar schon trägt (der Weg dorthin ist auch
`update`, und die Archiv-Route der Migration ist vom Feldvertrag ohnehin ausgenommen), und sie
verlangt am `capture` einen Begriff für „unbekanntes Feld", den es dort bewusst nicht gibt. Der
Leserfix deckt beide Richtungen; was er nicht kann, steht unten als Rest.

**Die Grenze selbst ist jetzt abgeleitet (AC-3):** `backlog_types.REFERENCE_LIST_FIELDS` nennt die
Item-Felder, die **kein** Capture-Vertrag deklariert und deren **Elemente** der Kernel auflöst. Weil
keine Eigenschaft von `REQUIRED_FIELDS`/`OPTIONAL_FIELDS` sie erzeugen kann, ist es eine Aufzählung
— mit einem Stolperdraht, der **beide** Enden misst:
`tools/test_backlog_types.py::test_the_reference_list_fields_are_what_the_kernel_reads_elementwise`
leitet die Menge aus den laufenden Kernel-Quellen ab (jede Lesestelle in Sequenz-Kontext auf einem
Namen, den das Modul aus einer Item-Quelle gebunden hat, minus der Vertragsuniversum-Felder) und
vergleicht in beide Richtungen; gemessen: ein vierter Name in der Aufzählung → rot („declared but
not read element-wise anywhere: ['risk_refs']"), ein entfernter Name → rot („read element-wise but
not declared: ['premise_rechecks']").
`tools/test_backlog_types.py::test_every_kernel_read_of_a_reference_list_field_goes_through_field_elements`
hält danach jede abgeleitete Lesestelle an die eine Definition.

**Rote Tests ohne den Fix** (je im Klon außerhalb des Repos, Defekt wiederhergestellt, rot
gesehen). **Sieben Stellen, aber sechs zurückgedrehte Leser, und beides stimmt:** `cli.py:678`
liest sein Item aus dem **Rückgabe-Objekt** des Freeze und ist für den Stolperdraht damit
unsichtbar (Rest 3) — es hängt am Test der Freeze-Kette, nicht am Draht. Mit den sechs
zurückgedrehten Lesern
`tools/test_staging_cli.py::test_a_scalar_design_ref_survives_the_freeze_as_one_reference`,
`tools/test_report.py::test_a_scalar_supersedes_retires_the_decision_it_names`,
`tools/test_report.py::test_a_scalar_premise_recheck_is_one_recheck_not_its_letters` und der
Stolperdraht oben; mit den entfernten Validator-Prüfungen
`tools/test_report.py::test_validate_names_a_scalar_reference_list_field` und
`tools/test_report.py::test_validate_names_design_refs_that_resolve_to_nothing` (dort steht die
Ausgangsmessung wörtlich im Fehlschlag: `found == []`).

**Rest 1 — der Skalar wird benannt, nicht abgewiesen.** `capture` und `update` nehmen ihn
unverändert; `report._check_reference_list_shape` meldet ihn als **Warnung**, und das ist gemessen
und nicht vorsichtig: nach dem Leserfix löst ein Skalar als die **eine** Referenz auf, die er
buchstabiert, und kein Gate entscheidet deswegen anders. Eine stille Reparatur der Datei kommt
nicht in Frage — `project_memory/**` hat genau einen Schreiber.

**Rest 2 — ein bereits beschädigtes Item wird gemeldet, nicht geheilt.** Es trägt eine **Liste**
(von Buchstaben), fällt also durch die Formprüfung durch; dafür löst
`report._check_design_refs_resolve` jeden Eintrag mit demselben Resolver auf, den das II.6a-Gate
benutzt (`dispatch._design_ref_resolves`) — der Fall, der vorher „0 error(s), 0 warning(s)" ergab,
nennt jetzt 34 nicht auflösbare Referenzen. `supersedes` und `premise_rechecks` hatten ihre
Existenzprüfungen schon; die melden weiterhin **einen Befund pro Buchstabe**, was laut, aber
unschön ist. Repariert wird in allen drei Fällen von Hand über den Kernel-Editierpfad.
**Diese neue Fehlerklasse ist in einem Kit-Projekt ein Merge-Block, und das gehört hingeschrieben:**
`dev-team/hooks/gate_memory_complete.py:159-178` sammelt jeden `validate_state`-Befund der Stufe
`error` und `:270` verweigert damit `git push`/Merge — gemessen als echter Hook-Prozess gegen ein
Projekt außerhalb des Repos: derselbe Push ist **rc 0** mit sauberem PR und **rc 2**, sobald das
Item die buchstabenweise Liste trägt („1 finding(s): PR-0001: design_refs names 34 reference(s)…").
Ein Projekt mit einem so beschädigten Item kann nach dem Kit-Update also erst wieder mergen, wenn
das Item über den Kernel-Editierpfad korrigiert ist. Fail-closed in die ehrliche Richtung — der
Zustand war schon vorher kaputt, nur unsichtbar.

**Rest 3 — was die Ableitung nicht sieht, und das ist ihre Grenze, keine Zusicherung.** Ein Wert,
der seinen Leser über ein **Rückgabe-Objekt** statt über eine Item-Lesung erreicht, taucht in ihr
nicht auf — `kernel/cli.py:678` ist genau so eine Stelle (`result["root"]`) und hängt deshalb am
Test der Freeze-Kette statt am Stolperdraht; ebenso ein Feldname, der weder Literal noch modulweite
String-Konstante ist, und jeder Leser **außerhalb** von `team-kits/kernel/` (die Hooks und Skripte
der Kits waren der TSK-0033-Sweep). **Eine vierte Blindstelle war die verbreitetste und ist
geschlossen statt benannt:** ein Wert, der vor dem Sequenz-Kontext an einen lokalen Namen gebunden
wird (`risky = item.get(f) or []` / `for ref in risky`) — die Zwei-Schritt-Schreibweise, in der
`kernel/dispatch.py:1084` geschrieben ist. Gemessen: dieselbe eingespritzte Lesung war als
Ein-Schritt-Form an beiden Drähten rot und als Zwei-Schritt-Form an beiden **grün**; der Leser
folgt jetzt **einer** Bindung (`_key_read_aliases`), womit die Einspritzung rot wird
(`report.py:1158 (consumed by for, not field_elements)`). Was danach bleibt: **mehr als eine**
Bindung, oder ein Weg durch einen Aufruf — dort wäre der nächste Schritt eine Datenflussanalyse,
und was sie brächte, ist ungemessen. Der Sprung ist zudem ohne Gültigkeitsbereichs-Analyse, was
Kandidaten **hinzufügt** statt sie zu verschlucken (rote Gleichheit, kein stiller Verlust).
`INV.scope` war als **H42** offen: dort ist die Antwort keine Normalisierung, sondern eine
Vertragsentscheidung — sie ist mit `DEC-0043` gefallen und in TSK-0060 gebaut.

**Die Lehre über das Instrument, die hier das eigentliche Ergebnis ist:** eine Sweep-Menge, die aus
der Oberfläche eines Kommandos abgeleitet wird, misst die Leser dieses Kommandos — nicht die
Eigenschaft „ein Leser setzt eine Form voraus". Wer den Sweep wiederholt, leitet die Menge aus den
**Schreibern** des Zustands ab (`capture`, `_update_item_locked`, `staging.freeze_*`) statt aus
`parse_field_map`. Die volle Messung samt Tabelle steht in
`docs/reviews/2026-08-14-tsk0033-map-field-reader-sweep.md`, Abschnitt 5.

### H44 — Vier gemessene Grenzen der Amendment-Ableitung (neu, TSK-0062)

TSK-0062 (`BUG-0040`) hat die Kriterien freigegebener Änderungsanträge in das Dispatch-Universum
ihrer Wurzel geholt — als Ableitung über vier Terme (`dispatch._amendment_criteria_locked`), nicht
als Sonderfall. Die Prüfung hat den Fix angegriffen und vier Grenzen vermessen; keine ist eine
Angriffskette innerhalb einer Sitzung, und jede steht als benannte Grenze in dem Code, der sie hat
— dieser Eintrag ist die Sammelstelle, damit sie ein Urteil tragen statt nur ein Kommentar zu sein.
Alle Zeilennummern sind der Stand 2026-08-15 (Kits `2026.08.15-7`) und bleiben als Fundprotokoll
stehen.

**(a) Die Kriterien eines ANGEWENDETEN Änderungsantrags zählen nicht mehr.** Die Ableitung
verlangt einen Status, „in den eine Nutzer-Freigabe das Item gestellt hat"
(`approvals.approved_statuses`); für CR ist das genau `APPROVED`. Erreicht ein CR sein Terminal
`APPLIED` — oder wird archiviert —, fallen seine Kriterien wieder aus dem Universum, und ein
SPÄTER geschnittener Task gegen eines davon wird verweigert: BUG-0040, einen
Lebenszyklus-Schritt weiter. Gemessen in der Prüfung zu TSK-0062: derselbe Spawn, der unter
`APPROVED` rc 0 war, ist nach der Überführung auf `APPLIED` rc 2. Richtung: Über-Verweigerung,
fail-closed — kein Gate öffnet sich. Nicht aufgeweitet, weil ein Sonderfall über einer Ableitung
genau die Form ist, die diese Runde beseitigt hat (`dispatch.py:1023-1030` sagt es an der Stelle);
festgehalten von `tools/test_approvals_dispatch.py::test_an_applied_amendments_criteria_stop_counting`
— eine spätere Aufweitung ist damit eine Entscheidung, kein Drift.

**(b) Die ZUGEHÖRIGKEIT eines Änderungsantrags ist nicht signiert, nur sein Inhalt.** Das
Scope-Manifest hasht die Kriterien (`approvals._SCOPE_FIELDS`), nicht `target_pr` — WELCHER
Wurzel ein Antrag gehört, hat niemand unterschrieben. Durch den Kernel ist das geschlossen: eine
`update`-Änderung an `target_pr` ist eine `HASHED_FIELDS`-Änderung, hebt die Revision und lässt
die Freigabe fallen. VORBEI am Kernel ist es offen: ein von Hand umgezieltes `target_pr` trägt
die noch gültige Freigabe samt Kriterien in das Universum einer fremden Wurzel, und der Leser
kann es nicht sehen (`dispatch.py:1012-1021`). Innerhalb einer Sitzung ist der Weg nicht gangbar
— Gate 1 verweigert jedem Aufrufer den Werkzeug- wie den Shell-Schreibzugriff auf
`project_memory/` außer `staging/`; er existiert nur aus einer Shell außerhalb von Claude Code.
Die Reparaturstelle wäre eine Manifest-Erweiterung, die jede lebende Freigabe ungültig macht —
eine Spec-Entscheidung mit Migration, keine Zeile, die man hier einschiebt.

**(c) `target_revision` wird als NAME gelesen, nie als WERT verglichen.**
`backlog_types.AMENDMENT_TYPES` leitet aus dem Feldnamen ab, WER ein Amendment ist; kein Leser
vergleicht die eingetragene Revision mit der aktuellen der Wurzel. Ein gegen Revision 1
geschriebener Antrag weitet also weiter auf, nachdem die Wurzel auf Revision 2 neu freigegeben
wurde — gemessen 2026-08-15 mit einer neu freigegebenen Wurzel, deren Kriterien ersetzt waren.
Richtung: eine Aufweitung, aber jede Zeile darin ist vom Nutzer signierter Inhalt — die Freigabe
des CR selbst bleibt in Kraft, und die Autorisierung des Dispatch kommt weiterhin aus der
Wurzel-Freigabe einen Rahmen höher. Der Gleichheitsterm bleibt gemessen draußen, nicht aus
Vorsicht: gegen die Pilotkopie hätte er die fünf tragenden Anträge (alle `target_revision` 2
unter Wurzel-Revision 2) passieren lassen und genau den einen legitimen verworfen, der vom
Nutzer gegen die geplante Revision 3 freigegeben war (`backlog_types.py:526-540` trägt die
Messung). Rest: semantische Veraltung signierten Inhalts, kein unsignierter Weg.

**(d) Hop 1 (`derives_from`) leiht Kriterien ohne Status- und Freigabeterm — für
Nicht-Amendments, absichtlich.** `dispatch._known_acceptance_ids_locked` fragt an Hop 1 nur, dass
die Quelle auflöst; ein Status-Term dort würde den Bugfix-Fluss der Kits (Task gegen die
Fix-Kriterien eines TRIAGED-BUG) undispatchbar machen, denn ein BUG erreicht in diesem Repo kein
`APPROVED` (H39). Die Amendment-Hälfte dieser Lockerheit war das Loch dieser Runde und ist ZU:
`derives_from: CR-…` auf einem DRAFT-CR lieh vor dem Fix dessen Kriterien, und der Spawn passierte
(gemessen 2026-08-15) — jetzt betritt ein Amendment das Universum nur noch über Hop 2 mit vollem
Freigabeterm (`dispatch.py:1147-1148`, rote Seite
`tools/test_approvals_dispatch.py::test_an_unapproved_amendment_named_in_derives_from_lends_nothing`).
Was bleibt, ist die Nicht-Amendment-Hälfte, begrenzt durch das, was sie leiht: Kriterien eines
Items, das der PLANER im Task benannt hat, unter einer Wurzel, deren eigene Freigabe den Dispatch
schon autorisiert hat.
`tools/test_approvals_dispatch.py::test_a_bugfix_task_may_reference_a_triaged_bugs_fix_criteria`
hält die offene Richtung fest.

**Urteil: Rest, keine Angriffskette innerhalb einer Sitzung.** (a) ist Über-Verweigerung, (b)
braucht eine Shell außerhalb von Claude Code, (c) leiht nur nutzersignierten Inhalt unter einer
autorisierten Wurzel, (d) ist eine entschiedene, beidseitig getestete Design-Richtung, deren
gefährliche Hälfte diese Runde geschlossen hat. Die drei Test-Zeiger dieses Eintrags sind von
Hand aufgelöst und in H41(d) mitgezählt.

### H45 — Zwei Grenzen der Arbiter-Härtung der Gate-Suite (neu, TSK-0063)

Anlass war `BUG-0051`: seit dieser Host ein WSL-Linux trägt, gewann der Windows-eigene
`bash`-Starter die Shell-Auswahl der Suite („läuft `true`" genügte), obwohl er absolut benannte
Pfade in ein fremdes Dateisystem auflöst — die Kontrolle des Sandbox-Tests konnte den Unfall
nicht mehr vorführen. TSK-0063 ersetzt die Auswahl durch eine Eigenschaft: der Schiedsrichter
muss eine Nonce, die dieser Prozess schreibt, **durch seine eigene Umleitung inhaltlich
zurücklesen** (der Starter antwortet rc 0 mit leerem stdout — der Exit-Code war genau die
Lücke). Zwei Grenzen der Härtung sind vom Prüfer gemessen und bleiben benannt; die
Zeilennummern sind der Stand 2026-08-15.

**(a) Die Sitzungswache verlangt die Shell-Eigenschaft auch von Prüfungen, die nie eine Shell
starten.** Mechanismus: die autouse-Fixture der Suite (`test_gates.py:131-135`) arbitriert beim
Sitzungsaufbau einen sehenden Shell als Vorbedingung — ihre Wachliste wird aber **in Python**
gebaut, die Shell führt dort nur `:` aus. Auf einem Host ohne sehenden Shell fällt damit die
ganze Suite zu, einschließlich der Registrierungs-Prüfungen, die nur `.claude/settings.json`
lesen. Kette (Prüfer, 2026-08-15, PATH ohne Git, nur der System32-Starter): neue Fassung rc 1
mit **4 ERROR** — genau die vier Registrierungs-Tests —, die vorige Fassung 4 passed; der
Mechanismus trifft über die autouse-Fixture alle 243. Auf diesem Host: kein Effekt (Git Bash
vorhanden). Urteil: **Über-Verweigerung, entschieden statt erlitten** — die vorige Fassung
ließ die Wache ihre Liste mit einem blinden Shell bauen, und fail-closed ist die ehrliche
Richtung; die benannte Schließrichtung (die gewachte Datei in der Fixture direkt anlegen und
die Shell-Forderung dorthin schieben, wo wirklich eine Zeile läuft) ist eine eigene Runde.

**(b) `_can_arbitrate` ist von keinem Test rot-fähig gedeckt.** Mechanismus: die Suite kann
die neue Form (jeder absolut genannte Baum wird inhaltlich gelesen) von der alten (zusätzliche
`cd`-Probe) **auf diesem Host nicht unterscheiden** — der Prüfer hat die alte Form im Klon
wiederhergestellt und die acht einschlägigen Tests blieben in 19:51 grün. Damit ist die
entfernte `cd`-Probe unbeobachtet: eine Shell, die absolut liest und `cd` verweigert
(rbash-Klasse), würde heute arbitrieren; konstruiert argumentiert, nicht gefahren. Die
Lautstärke des Ausfalls ist nur schräg gemessen (eine Mutante machte die Tabelle rot, aber als
Timeout nach 120 s, nicht als widersprechende Zelle) — dieselbe Klasse wie H10 (Codehälften
ohne rote Mutation): eine Messlücke des Instruments, kein offenes Gate.

**Urteil: Rest bzw. entschiedene Über-Verweigerung, keine Angriffskette.** (a) ist fail-closed
in die ehrliche Richtung und auf diesem Host ohne Effekt — die Schließrichtung steht im Absatz
und ist eine eigene Runde; (b) ist eine Messlücke des Instruments, kein offenes Gate. Beide
Ketten sind vom Prüfer der TSK-0063-Runde gemessen und stehen oben im Eintrag.

### Zwei Vertragsabweichungen, die `SR-0006` nachgezogen bekommen muss — ERLEDIGT durch `SR-0009`

**(Nachtrag 2026-08-14, TSK-0058):** Beide Abweichungen sind in den geltenden Vertrag eingeflossen —
`SR-0009` fasst den Auslöser als Eigenschaft (jede Oberfläche, über die das Subjekt erreichbar ist)
und den geschützten Bereich als das, was die laufende Ableitung nennt. Der Abschnitt bleibt als
Geschichte des Befunds stehen; sein Wortlaut unten beschreibt den Stand unter `SR-0006`.

1. **Der Auslöser ist als Werkzeugliste formuliert, nicht als Eigenschaft.** `SR-0006` beschreibt
   den geschützten *Bereich* als Ableitung, den *Anlass* aber als vier Werkzeugnamen. Gate 1 folgte
   dem korrekt und war damit auf der Shell blind. Es ist jetzt zusätzlich auf `Bash|PowerShell`
   registriert — das ist **mehr, als der Vertrag sagt**.
2. **Der geschützte Bereich ist weiter als der Vertrag.** `SR-0006` nennt `.claude/hooks/` und
   `.claude/settings.json`; gebaut ist `.claude/` als Ganzes, dazu die Datei, aus der der Bereich
   abgeleitet wird, und der kanonische Teil von `project_memory/` für jeden Aufrufer. Jede dieser
   drei Erweiterungen schließt eine gemessene Kette (H3, H5, F3 des Prüfberichts) — aber sie sind
   Erweiterungen, und eine stillschweigende Vertragserweiterung ist die andere Art, falsch zu sein.
