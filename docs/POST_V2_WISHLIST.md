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

**Item:** → FR-0078 — ein Gate auf genau EIN primäres Ziel je View, plus die SKILL-Zeile mit
Verfahren statt Adjektiv. Gilt für diesen Abschnitt und für Abschnitt 1 darüber.
**Geliefert in TSK-0119, als PRÜFUNG im ausgelieferten Skript und nicht als Haken:** die Designer-
Rolle schreibt je View einen Satz („hier tut der Nutzer X, und er sieht es zuerst an Y"), zeichnet
den Container mit `data-view` und das eine Element mit `data-primary-action` aus, und
`kit_design_render.py` verweigert am gerenderten DOM jeden **deklarierten** View mit null oder
mehr als einem — mit dem Satz, der die Rangfolge einfordert. Was es ausdrücklich NICHT tut: einen
View beurteilen, den niemand deklariert hat (`H140`). Warum kein Haken: `DEC-0056` baut kein Gate
für eine Fehlklasse ohne gemessenen Fall, und der einzige gemessene Fall dieser Gegend ist
`BUG-0076` (ungesehener Entwurf), den `gate_design_sighted` schon trägt — der Preis dieser Wahl
steht als `H138`.

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

**Erledigt:** → FR-0045 — in der ersten Strom-Generation geliefert (DEC-0060, TSK-0100).

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

- **C1/C2/C3** — **GEBAUT in TSK-0119 (FR-0077), auf der gestagten DSN statt im `browser_smoke()`,
  und C1 ohne axe.** Was läuft: `kit_design_render.py` lädt jeden gestagten Entwurf ein zweites Mal
  und misst am gerenderten DOM Kontrast (WCAG 4.5:1/3:1), den Tastaturpfad (jedes fokussierbare
  Element per echtem Tab erreichbar; Fokus **in Pixeln** sichtbar; nichts, was die Maus klicken kann
  und die Tastatur nicht erreicht; kein positiver `tabindex`), die `prefers-reduced-motion`-Wirkung
  (dieselbe Seite in einem Kontext mit `reduced_motion: reduce`, es darf nichts mehr animieren) und
  die Präsenz einer `:focus-visible`-Regel. Rückgabe **3** statt 0, Datensatz wird trotzdem
  geschrieben. Die Bedingung des Abschnitts ist eingehalten und gemessen: der Bericht sagt „the
  automatically checkable share", nie „barrierefrei"
  (`tools/test_design_conformance.py::test_the_report_never_calls_a_draft_accessible`).
  **Drei Abweichungen, alle gemessen statt behauptet:** (a) **kein axe-core** — axe ist ein
  npm-Paket, und das Kit liefert gar keine npm-Datei aus, in die es gehören könnte (`templates/repo/`
  trägt `requirements-dev.txt`, `ruff.toml` und `scripts/`); die eine ausgelieferte Abhängigkeitsdatei
  lag ausserhalb der Dateihoheit dieses Stroms. Gebaut ist der Anteil, der ohne Abhängigkeit läuft.
  (b) **Subjekt ist der DSN-Entwurf, nicht der Build** — `kit_browser_checks.py` liefern dev-team
  UND research-team byte-gleich aus, und research-team war diesem Strom verboten; der Entwurf ist
  ausserdem der Vertrag, den der Build umsetzt, also die frühere Stelle. Die Build-Hälfte steht als
  `H139` unten. (c) **Unsichtbarer Fokus wird in PIXELN entschieden, nicht an byte-gleichen
  computed styles**, wie C2 oben vorschlägt: mit `a:focus { outline: none }` verschiebt Chromium
  `outline-offset` von 0px auf 1px, die computed styles sind also verschieden, und auf dem Schirm
  ist nichts — gemessen, und als eigener Fall in der Suite.
- **B2/B3** — **B2 gebaut in TSK-0119, B3 NICHT (Dateihoheit, siehe `H139`).** B2 läuft im selben
  Lauf: was ein Farbliteral ist, entscheidet der CSS-Parser des Browsers und keine Notationsliste —
  ein Wert ist ein Literal, wenn `CSS.supports('color', v)` gilt, er kein `var(` enthält, er kein
  CSS-weites Schlüsselwort ist (gefragt an einer Eigenschaft, die keine Farbe nimmt) und er unter
  zwei verschiedenen geerbten Farben gleich auflöst. Erlaubt ist er an **genau einer** Stelle: als
  Wert einer Custom Property. Das ist das Token-Blatt als Eigenschaft statt als Selektorliste, also
  auch für ein Theme-Block oder eine erfundene Schreibweise gültig. B3 (Farbliterale im
  Anwendungscode über `_frontend_sources()`) bräuchte `kit_checks.py` oder `kit_browser_checks.py`
  — beide ausserhalb dieses Stroms.
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

**Item:** → FR-0077 — die mechanisch prüfbaren Hälften C1/C2/C3 und B2/B3. **Geliefert in TSK-0119**
für C1 (ohne axe), C2, C3 und B2 auf der gestagten DSN; B3 und die Build-Hälfte stehen als `H139`.
Die Zeilen oben sagen je Hälfte, was läuft und was nicht.

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

**Item:** → FR-0024 — deckt diesen Abschnitt und sagt es selbst; geliefert dagegen: FR-0030 und FR-0053, offen daneben FR-0017. Die Termine als eigener Vorgangstyp (MST) sind seither → FR-0079.

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

**Item:** → FR-0080 — Plan und Mindmap als generiertes `.drawio.svg`; das Format ist für WFR/ARC bereits in Gebrauch, das FR erweitert es.

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

**Item:** → FR-0047; **Soll-Zustand entschieden in** → DEC-0034 (bewusst nicht gebaut), Besetzungsschicht → DEC-0059. Der gebaute Stand (`model_tiers.yaml`) und DEC-0034 weichen absichtlich voneinander ab.

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

**Item:** → FR-0032 für die ANSICHT (Finanz-Dashboard, geliefert in TSK-0109). Der Kontenrahmen SKR03/SKR04 mit der Konto→EÜR-Abbildung, jahresversioniert und mit benanntem Rechtsraum, ist → FR-0081; FR-0002 deckt Ablage und Aufbewahrung, nicht den Kontenrahmen.

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

**Item:** → FR-0021 — nennt diesen Abschnitt selbst.

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

**Item:** → FR-0082 — `EVIDENCE_RESULTS` um `blocked` erweitert, `gate_git` schließt darauf wie auf `fail`, und der Ehrlichkeitssatz wird mitgebaut. Nachbar, nicht dasselbe: FR-0040.

## 8. Ein Projekt vollautonom von Anfang bis Ende (2026-08-03, User)

> „Wie bekommen wir es hin, dass ein neues Projekt vollautonom von Anfang bis Ende durchläuft — mit
> perfekter und getesteter UI, sauberem und sicherem Backend? Einen gereviewten Plan erstellen mit
> allen Wenn und Aber, alles so zerrupfen, dass am Ende ein Produktplan steht, und diesen vollautonom
> vom PM durchziehen lassen."

Das ist kein Einzelwunsch, sondern der Zweck, auf den die anderen sieben Punkte zulaufen. Deshalb
steht hier nicht „was man bauen müsste", sondern **woran heute gemessen fehlt**.

**Item:** → FR-0074; **entschieden in** → DEC-0058.

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

**Teilweise erledigt:** die scope-Freigabe bei offenen Planfragen → DEC-0058 / FR-0074. **Offen bleibt die andere Hälfte:** der Masterplan hat nach der Installation keinen Schreiber — das ist L1 dieser Liste und wird dort geführt.

## 10. Die Freigabe programmatisch erteilen — und was das verschiebt (2026-08-03)

**Gemessen:** `AskUserQuestion` existiert im `-p`-Modus nicht. 30 Werkzeuge in der Init-Zeile, keines
davon; `--tools "Read,AskUserQuestion"` liefert `['Read']` — das Werkzeug wird still fallengelassen.
Auch `--input-format stream-json` ändert daran nichts. Damit fehlt der Kette headless ihr
NUTZERKANAL: keine echte Frage, keine echte Antwort, also kein Ja, das jemand gegeben hat.

**Korrektur 2026-08-30 (TSK-0097):** dieser Absatz schloss bis dahin mit „Da `gate_approval` **nur**
aus einer echten Antwort auf eine echte `AskUserQuestion` prägt, ist die Freigabekette headless
unerreichbar". Die Prämisse ist widerlegt — der Haken prägt aus **jeder** stdin-Nutzlast, die die
Form einer Antwort hat, und die Wand, die das in einem Kit aufhält, ist `gate_write_scope` und nicht
`gate_approval`. Gemessene Kette und Gegenmessung: **H80**. Headless unerreichbar ist also der
ehrliche Weg, nicht der Mechanismus.

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

**Item:** → FR-0083 — Freigabe über das Agent SDK (`canUseTool`), und ein programmatisch geprägter Token muss von einem menschlich geprägten unterscheidbar bleiben. Die „headless unerreichbar"-Prämisse ist seit TSK-0097 widerlegt (`H80`).

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

### L6 — Rollenmemory ist vorgeschrieben und gesperrt — geschlossen am 2026-08-17 (BUG-0047, TSK-0072)

Der Eintrag war zusätzlich in einem Punkt falsch: er nannte `submit-result` als Auslöser.
Gemessen im Scaffold gegen die projekteigenen Hooks (2026-08-17) war das eigene Memory an
**jedem** Punkt gesperrt — während `IN_PROGRESS` mit „outside TSK-0001's allowed_scope", danach
mit „this subagent is not bound to a task". Es gab also kein Fenster, das `submit-result`
geschlossen hätte, sondern von Anfang an keines.

Geschlossen als **Regel 6** in `gate_write_scope` (`_own_craft_memory`): der Aufrufer schreibt
`<Providerverzeichnis>/agent-memory/<seine eigene Rolle>/**` und sonst nichts ausserhalb seines
Task-Scopes — vor und nach der Rückgabe, während der allgemeine Task-Scope danach unverändert
geschlossen bleibt. Alle drei Bedingungen sind abgeleitet (Payload-`agent_type`,
`kernel.presets.AGENTS_DIR`, `guard_memory_budget.MEMORY_DIR`).
`tools/test_hooks.py::test_a_role_writes_its_own_craft_memory_and_only_its_own` hält sechs
Richtungen, darunter fünf Verweigerungen; ein aufgeweitetes Fenster (Rolle aus dem Pfad statt aus
dem Aufrufer) wurde in einem Klon rot gemessen.

**Offen bleibt der Shell-Weg, und zwar absichtlich:** `handle_shell` löst keine Rolle auf, also
könnte ein Fenster dort nur jedes Rollenmemory für jeden Aufrufer öffnen. Die Verweigerung nennt
seit dieser Runde die Tür, die es gibt (Write/Edit-Werkzeug für einen Subagenten), statt „Hooks
and settings are maintained by the scaffold" — der falsche Grund, den dieser Eintrag zu Recht
anmerkte.

**Und offen bleibt eine Nicht-Kongruenz, die beim ersten Anlauf ein echtes Loch war** (vom
Prüfer gemessen, in derselben Runde geschlossen — zweimal, denn unter dem ersten Fix lag noch
eine Namensschicht: Gate und Wächter urteilten über verschieden geschriebene Pfade, geschlossen
als EINE Ableitung `guard_memory_budget.guard_relative` mit zwei Lesern; beide Vertreter der
Schreibweisen-Klasse — ADS-Datenstrom und 8.3-Kurzname — sind gemessen zu): das Fenster
entscheidet über **Pfad und Rolle**, der Inhaltswächter über die **Form des Payloads** — zwei
Mengen, die nicht deckungsgleich sind. Geschlossen ist das dadurch, dass das Fenster den Wächter
fragt, statt ihn anzunehmen (`guard_memory_budget.judges_this_write`), also fail-closed in
dieselbe Richtung. Was damit **verweigert statt gedeckt** ist: jede Payload-Form, die der
Wächter nicht rekonstruieren kann — ein `Edit` mit leerem oder nicht auffindbarem `old_string`,
ein `NotebookEdit`, ein Codex-`apply_patch` — jede Datei im Memory-Baum, deren Budget keine
Inhaltsregel trägt, und jedes Memory-File, das unter einer nicht-geebneten Schreibweise
adressiert wird (gemessen: `MEMORY.md::$DATA` mit sauberem Inhalt → rc 2). Ein Rollenmemory als
Notebook oder über Codex zu pflegen ist damit **nicht möglich**; das ist Über-Verweigerung mit
Ansage, kein Loch, und die Schliessrichtung wäre, den Inhalt dieser Formen im Wächter zu
modellieren (`guard_memory_budget.py`, „Modelling notebook content is phase 3"). Bewusst NICHT
angefasst: ob `guard_memory_budget.main` selbst `realpath` auflösen soll — das wäre die
Ausweitung einer Inhaltsregel mit eigener Fehlalarm-Frage und steht als eigene Entscheidung an,
nicht als Nebenwirkung dieser Runde.

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
- **Ob eine stderr-Notiz bei exit 0 das Modell erreicht, hat niemand gemessen** (TSK-0074) — der
  Plattformvertrag garantiert Text vor dem Modell nur bei exit 2; `guard_question_context` SAGT das
  in seinem Kopf, gemessen ist es nirgends. Jede exit-0-Notiz der Kits (Spawn-Hinweis, R2-Warnung)
  ist damit ein Signal unbelegter Reichweite — die schwache Klasse, und sie steht in beiden
  Kommentaren als solche.
- **Der Spawn-Hinweis feuert nur auf ein JSON-`true` als Boolean** (TSK-0074, `guard_agent_spawn`:
  die Notiz-Bedingung liest `is True`, die Pflicht-Prüfung davor nur die Anwesenheit des Feldes) —
  `"true"` als String oder `1` als Zahl passieren die Pflichtprüfung und erzeugen lautlos keine
  Notiz. Fehlrichtung ist Schweigen, gemessen im echten Hook-Prozess; benannt im Kommentar und hier.
- **`cp -r <repo>/project_memory <ziel außerhalb>` wird verweigert, obwohl nur gelesen wird**
  (TSK-0076, gemessen rc 2): Gate 1 liest jeden `cp`-Operanden als mögliches Schreibziel, und
  `project_memory` in einer schreibfähigen Zeile ist für jeden Aufrufer gesperrt. Über-Verweigerung
  der bekannten Fail-closed-Bauart (H19-Familie), kein Loch; Ausweg gemessen: ein Python-Skript
  kopiert lesend (`clone_state.py`-Muster) oder `git show HEAD:<pfad>`.
- **`git hash-object <datei>` stuft Gate 3 als historienschreibend ein — ohne `-w` schreibt es
  aber nichts** (TSK-0076, gemessen; Präzisierung Prüfer: MIT `-w` schreibt es sehr wohl ein Blob,
  die Einstufung ist also nur für die flaglose Form Über-Verweigerung). Kein Loch; Ausweg:
  `sha256sum`/PowerShell-`Get-FileHash` über die Datei bzw. `git show` + Vergleich.
- **Eine reine Lesezeile mit `grep -qE "…=+ .*(passed|failed)"` wird von Gate 1 verweigert**
  (TSK-0076-Prüfrunde, gemessen rc 2): das `.*` im quotierten Muster wird als relativer Pfad
  gelesen und auf `..` über der Repo-Wurzel aufgelöst — H19-Familie (Vorfahren-Regel), kein Loch;
  Ausweg: Muster ohne `.*`-Präfix formulieren oder die Ausgabe erst in eine Datei leiten.
- **Kernel-angehängte Aktenplan-Regeln tragen nie die optionalen Felder** (TSK-0078:
  `required_metadata`, `collision_policy`, `examples` — `add-filing-rule` hängt die fünf
  Pflichtfelder an, und kein späterer Weg ergänzt die optionalen; `filing.py` begründet es
  ehrlich, die Folge steht hier: wer sie will, schreibt die Regel vor der Installation oder
  wartet auf ein Änderungs-Kommando, das eine eigene Runde wäre).
- **Die Naht Verdikt→Bewegung der Ablage-Kette ist Verfahrens-Prosa** (TSK-0078): nichts bindet
  die zweite Clerk-Beauftragung mechanisch an die Verdikt-Datei — der Manager könnte
  paraphrasieren. Die Texte weisen es als Verfahren aus; die Begrenzung ist `gate_filing`
  (jede Bewegung wird trotzdem gegen den Plan geprüft) plus der Auditor.
- **Zwei Antworten auf „welcher Modellwert ist portabel"** (TSK-0078-Prüfer):
  `gen_provider_artifacts.py` hält die Spezialisten-Frontmatter an eine hartkodierte Menge,
  während `tools/validate.py` dieselbe Frage seit FR-0051 aus `model_tiers.yaml` ableitet.
  Nicht neu eingeführt, durch die Ableitung sichtbar geworden; Kandidat: der Generator fragt
  dieselbe Ableitung.
- **Ein Bestandsrest der Office-Wand, an HEAD wie nach TSK-0077 identisch offen** (Prüfer,
  Runde 2-4, gemessen rc 0): `A=archive/…; rm "$A"` — der Operand wird von der Shell aus einer
  Variablen derselben Zeile umgeschrieben, die der Wand-Leser nicht auflöst (dieselbe Klasse wie
  H47 am Repo-Gate; als MITFAHRER neben einer Freigabe seit TSK-0077 rc 2, allein weiter rc 0).
  Schließrichtung: die Zeilen-Zuweisungskarte. Die zweite Hälfte, die hier stand — `mv ARCHIVE/…`,
  `_filing.under` case-sensitiv, während NTFS faltet — ist seit TSK-0087 GESCHLOSSEN
  (`os.path.normcase` beidseitig in `under`, Test verzweigt selbst über `normcase` und misst
  damit das Dateisystem): der Prüfer jener Runde hatte gemessen, dass die Schreibweise nicht nur
  den Austritt, sondern auch die EINTRITTS-Wand samt der neuen Zweitlesungs-Mechanik aushebelte
  (`ARCHIVE/`- und `Archive/`-Landung rc 0 durch alle sechs Hooks, Datei real im Archiv).
- **Die Eigenschaftsaussagen der `ENFORCEMENT.md`-Zeilen haben keinen Leser** (TSK-0075, Prüfer):
  ein Draht verlangt, dass jede Warn-Art *vorkommt*, aber nicht, was über sie *behauptet* wird —
  gemessen mit einer frei erfundenen Zeile (falsche Wörter, nicht existierende Konstante, falsche
  Schwelle, gegenteilige Verhaltensaussage): 12 einschlägige Tests grün. Der Verfassungs-Draht
  derselben Runde zeigt die Bauform des Fixes (Aussage gegen den laufenden Hook messen); eine
  eigene Runde, falls gewollt. Bis dahin gilt: `ENFORCEMENT.md`-Prosa ist Wegweiser, nicht Beweis.
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
- **Sechs office-eigene Inhaltsdokumente haben gar keinen Schreibweg** (TSK-0081, gemessen als
  Ableitung über `layout.is_project_document` + `layout.partial_writers` gegen das ausgelieferte
  Template-Verzeichnis): von 10 Kit-Dokumenten tragen 2 einen Teil-Schreibweg
  (`filing_plan.yaml` über `add-filing-rule`, `project_config.yaml` über `set-preset`);
  `business_profile`, `compliance_register`, `content_guidelines`, `marketing_plan`,
  `master_data`, `product_catalog` haben keinen — sieben mit `product/masterplan.md` als
  kit-übergreifendem Fall. Sie werden im Onboarding gefüllt oder bleiben leer; die
  Bookkeeper-Texte sagen das seit TSK-0081 ehrlich. Ein echter Schreibweg nach dem
  `add-filing-rule`-Muster wäre je Dokument eine eigene Runde.
- **Ein Hook-Eintrag ohne `timeout` wird vom Provider bei ≈600 s getötet, und der Kill ist ein
  stiller Durchlass** (TSK-0082, beide Rollen unabhängig in echten Provider-Sitzungen gemessen,
  claude.exe 2.1.239: 310 s und 560 s überleben mit gehaltener Verweigerung, 900 s wird getötet
  und der verweigerte Aufruf läuft — Klammer 560/900, Sitzungsdauer datiert den Kill auf
  ~600 s; ein GESETZTES `timeout` tötet exakt an seiner Zahl, gemessen bei 5 s). Konsequenz
  gebaut statt gemerkt: die Kits registrieren kein `timeout` mehr (die BEOBACHTETE Laufzeit aller
  28 office-Einträge liegt ≤0,405 s; die größte EIGENE Kindgrenze eines Gates außer
  `gate_pipeline` ist 20 s — beides Messwerte, keine Schranken), außer wo ein Hook eine EIGENE,
  kleinere Verweigerungs-Grenze trägt — dann
  muss das Fenster echt darüber liegen (`gate_pipeline` 1800 über seiner 1500-s-Kindgrenze);
  ein Test hält die Eigenschaft, `tools/provider_observations.json` trägt die Messung.

### L10 — Was ohne einen Provider unprüfbar bleibt

- Ob ein **Subagent** sein SKILL geladen bekommt. Für den Sitzungs-Agenten ist gemessen, dass er es
  **nicht** bekommt; der Spawn-Weg ist zweimal an einem Kind gescheitert, das den Auftrag ablehnte,
  bevor es antwortete. In `tools/provider_observations.json` als offen geführt.
- Ob **Codex** einen `@`-Import in `AGENTS.md` expandiert.
- Ob `AskUserQuestion` im **interaktiven** Modus genau den Payload liefert, den `gate_approval`
  erwartet. Die Gates prägen korrekt, wenn der Payload kommt (viermal gemessen mit rekonstruiertem
  Payload) — die Form des echten Werkzeugaufrufs ist ungemessen.
- Ob der Provider einen **nutzer-globalen `SessionStart`-Hook** (`kit_bridge_notice.py`,
  TSK-0081) in eine Sitzung mit projekteigenen SessionStart-Hooks mischt und dessen
  `additionalContext` zustellt. Gemessen sind Hook-Prozess und Registrierung; kommt die Notiz
  nicht an, bleibt P4-1 für das betroffene Alt-Projekt unverändert (der menschliche Weg steht im
  README-Abschnitt „Update"). Messpunkt des Live-Testlaufs.

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
`templates/repo/scripts/generate_dashboard.py` (`generated`; seit TSK-0115 nicht mehr auch
`archive` — das Dashboard zählt das Archiv nicht mehr, DEC-0065 (1)),
`templates/repo/scripts/retro.py` (`generated`, dev und research) und seit TSK-0099
`templates/repo/scripts/kit_design_render.py` (`staging`). Jede davon ist eine zweite
Schreibweise der Antwort eines Bauers: zieht `state.generated_path` um, liest der Bridge-Code
weiter am alten Ort und meldet ein Projekt fälschlich als greenfield; zieht `staging/` um, rendert
das Design-Skript ins Leere und `gate_design_sighted` verweigert jede Vorlage, weil es den
Datensatz am alten Ort sucht.

**Urteil: OFFEN, nicht blockierend** — die Kette braucht eine Umbenennung im Kernel, und der
Bridge-Pfad ist genau der, der ohne Kernel funktionieren muss (`_kernel.state_is_empty` antwortet
auch dann, wenn der Kernel nicht importierbar ist; ihn an einen Bauer zu hängen, verlegt eine
Bootstrap-Antwort auf den Kernel). Für die drei Vorlagen-Skripte gilt dasselbe eine Stufe weiter
draußen: sie laufen **im Projekt** und stdlib-only, wie ihre eigenen Köpfe sagen — im Kit-Repo gibt
es dort keinen `ProjectState` zu fragen, und einen Kernel-Import hineinzulegen würde genau den
kernelfreien Pfad aufgeben, den dieser Eintrag beschreibt. Deshalb ist der Zuwachs eine Zahl plus
eine Zeile hier und keine Code-Änderung.

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

**Erweiterung (TSK-0067, gemessen 2026-08-16 vom Prüfer jener Runde):** dieselbe Klasse trifft
das **zweite** Kommando, das die Durchsetzungsschicht neu installiert — als Subagent
(`agent_id: sub-1`, `agent_type: backend-developer`) sind `python scripts/harness.py update-kit`
und `… request-approval kit_update` bei **allen 8** registrierten `Bash|PowerShell`-Gates rc 0,
während `create-task` für denselben Subagenten rc 2 bleibt. Ein Unterschied zur
`set-preset`-Hälfte, gemessen: die **Wiederholung trägt hier nicht** — der zweite Lauf ist rc 1
(„already runs the staged … kit"). Was der Subagent kontrolliert, ist also nur der
**Zeitpunkt**, einmalig. Daneben, als bewusster Nicht-Weg derselben Runde: ein
**Reparatur-Scaffold auf gleicher Version** (manipuliertes Bundle) hat weiterhin keine Route aus
der Sitzung — `update-kit` verweigert „already runs the staged release", und das ist gewollt:
ein Befehl, der ein Bundle neu segnet, wäre die Selbstfreigabe, die `write_kit_state.py`
verhindert; die Vertrauens-Remedy von `gate_dispatch` zeigt dort korrekt auf den Nutzer.

**Urteil: Rest mit gemessener Kette, kein Inhalts-Loch.** Die Autorisierung selbst ist die APR des
Nutzers und deckt das Ergebnis; was der Subagent kontrolliert, ist **Zeitpunkt und Wiederholung**
einer signierten Änderung, nicht ihr Inhalt (bei `update-kit` nur der Zeitpunkt, einmalig). Die
Reparaturstelle ist die Subagenten-Regel der
Kits: die abgeleitete Klasse um „installiert die Durchsetzungsschicht" erweitern (aus derselben
Quelle abgeleitet, aus der `set-preset` und `update-kit` ihre Wirkung beziehen) — eine
Kit-Runde, kein Repo-Gate.

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

**Erweiterung (TSK-0067, gemessen 2026-08-16 vom Prüfer jener Runde):** dasselbe Fenster trifft
`update-kit`, mit einer Zuspitzung durch den dortigen F1-Fix (der „nichts bewegt"-Zweig setzt
bewusst **keinen** Stopp-Marker mehr, damit ein Konfigurationsfehler nicht die Sitzung tötet):
bei einem Abbruch nach 1,4 s von ~3,4 s waren **fünf Skill-Verzeichnisse weg**, während beide
Leser „unverändert" sagten — kein Marker, Sitzung lebt. Keine Datei der Durchsetzungsschicht
bewegte sich dabei (Bundle „recorded", `agents`/`settings.json` unverändert), der Regelsatz
unter einem laufenden Kind bliebe also der der Sitzung; die Meldung trägt die Grenze selbst
(`UNREAD` nennt „the role skills" ausdrücklich), und die Remedy **heilt gemessen**:
Wiederholungslauf rc 0, Skills 0 → 5, Marker gesetzt, Stempel bewegt. Der Richtungsentscheid
ist richtig — die Vorfassung stoppte die Sitzung über einen Baum, an dem nachweislich gar
nichts war, und das war die teurere Fehlrichtung; was bleibt, ist die ehrliche Restmenge.

### L42 — Drei gemessene Grenzen der Fortsetzungs-Mechanik (TSK-0065)

TSK-0065 (`BUG-0042`, `DEC-0044`) hat den Sitzungsabbruch zweiteilig beantwortet: verwaiste
Dispatches werden beim Sitzungsstart ehrlich gefegt (Definition: die anfordernde Sitzung ist
nicht die jetzt fragende), und ein Spezialisten-Zwischenstand (`staging/<TSK>/checkpoint.yaml`)
wird vom Nachfolger nur nach dreifacher Verifikation übernommen (Identität, Vertrag über den
`expected_outputs`-Digest samt Task-/Root-Revision, Artefakt-Bytes — seit der Nachbesserung mit
Pfad-Eingrenzung und „ohne Artefakt = abwesend"). Drei Grenzen bleiben, je gemessen in der
Prüfung 2026-08-16:

**(a) Kernel-seitig fällt die Waisen-Frage bei fehlender Sitzungs-Id nicht zu.**
`dispatch.orphaned_dispatches(state, None)` — und ebenso mit `""` — liefert **jeden**
aufgezeichneten Dispatch als verwaist (gemessen von Prüfer und Umsetzer unabhängig); was davor
steht, ist allein der Kit-Hook (`_kernel.py`, gibt bei fehlender/leerer Id `None` zurück und
fegt nichts — gemessen für fehlenden Schlüssel, Leerstring und Whitespace). Die Definition
gehört in den Kernel, nicht in den einen Aufrufer; ein zweiter Kernel-Aufrufer ohne diese
Vorsicht würde alles fegen. Nebenwirkung derselben Konstruktion, als Preis des ehrlichen
Fixes: ein Dispatch im Fenster zwischen `dispatch` und Antritt (Lease existiert, trägt aber
noch keine Sitzung) wird bei jedem Sitzungsstart als „LEFT ALONE / unentscheidbar" gemeldet —
melden statt zerstören ist die richtige Richtung, aber es ist wiederkehrendes Rauschen im
Briefing und gehört mit in die Folgerunde.

**(b) Was der Datensatz ÜBER die Dateien sagt, prüft niemand.** Ein handgeschriebener
Checkpoint mit **korrekten** Digests bleibt möglich — `staging/` ist genau das Verzeichnis, in
das ein dispatchter Spezialist schreiben darf. Die Verifikation misst Baum und Task neu; die
Prosa (`note`, `next_step`) ist unverifiziert, und die Verfassung sagt dem Nachfolger „Read it,
judge it". Benannt im Modul-Docstring und im Verdikt-Text; die Begrenzung ist, dass nur
signierte Fakten (Digests, Revisionen) die Übernahme öffnen, nie die Prosa.

**(c) Ungemessen bleiben zwei Betriebsfragen:** ob eine zweite **gleichzeitige** Sitzung im
selben Projekt vom Fegen getroffen würde (der Term beweist „woanders angefordert", nicht
„Anforderer ist tot"; Begrenzung: der Sweep landet nur auf Status, an denen ein Mensch
weiterhandelt, und zerstört keine noch auflösbare Bindung), und ob der Provider einer
weiterlaufenden Sitzung über Kompaktierung/Resume je eine **neue Id** gibt (sähe von innen wie
ein Sitzungsende aus). Beides steht als „NOT measured" im Code; die Id-Frage ist ein Kandidat
für die nächste echte Provider-Messrunde (`tools/provider_observations.json`).

**Urteil: Rest, keine offene Angriffskette in dieser Konstruktion.** (a) ist durch den einzigen
existierenden Aufrufer begrenzt und seine Schließrichtung (Kernel-seitiges fail-closed) eine
kleine Folgerunde; (b) öffnet keine Übernahme, weil nur Gemessenes sie öffnet; (c) ist ehrliche
Unwissenheit mit benannter Messrichtung, keine Behauptung.

### L43 — Was die neue PM-Shell-Regel (Regel 5) nicht erreicht: Werkzeugsprache, PowerShell-Cmdlets, unauflösbare Erweiterungen, Wrapper (TSK-0070)

**Anlass:** FR-0013 — `guard_pm_scope` der Kits deckte die Schreibwerkzeuge, nicht die Shell; ein
PM konnte `echo … > services/pay.py` an ihm vorbei fahren. TSK-0070 hat die Entscheidung
gemessen getroffen (Variante b, sauberer Schnitt: Dateieigenschaft bei `guard_pm_scope`,
Kommandozeilen-Zerlegung bei `gate_write_scope`, Regel 5 greift an der **einen** Schreibposition,
die die Shell-Syntax selbst definiert — dem Ziel einer bytehaltenden Umleitung) und die
Beschwichtigungsprosa des alten Docstrings („95%-Wächter; der QA-Gate ist der harte Riegel")
durch die Messung ersetzt: der QA-Riegel fragt nur nach einem **Verdikt**, und dasselbe Lead
erzeugt Verdikte selbst — er ist also über Autorschaft blind. Was Regel 5 **nicht** erreicht,
bleibt als benannte Restklasse, beidseitig getripwired in `ENFORCEMENT.md` aller drei Kits und
im Docstring von `_assert_the_lead_lands_no_code`:

- **Werkzeugsprachliche Writes** (`cp`, `mv`, `tee`, `sed -i`, `python -c`, `rm`): die Shell
  landet dort keine Bytes selbst, das Werkzeug schreibt aus seiner eigenen Sprache/Argumentliste.
  Die L4-Klasse — eine Verbliste wäre genau die Behauptung, die schon zweimal eine Datei zu kurz
  war; darum nicht aufgezählt, sondern als Grenze benannt.
- **PowerShell-Cmdlets** (`Out-File`, `Set-Content`, `Add-Content`, `Tee-Object`): dieselbe
  Klasse in der anderen Shell, gemessen rc 0, mit eigenem Test
  (`test_a_powershell_cmdlet_write_is_the_named_residue_too`).
- **Unauflösbare Erweiterungen** als Umleitungsziel (`$(cmd)`, Backticks, eine Variable, die die
  Zeile **nicht** zuweist): B2 löst nur die **Zeilen-eigenen** Zuweisungen auf; alles, was erst
  eine laufende Shell kennt, bleibt offen. `$UNSET/pay.py` verweigert übrigens (die Endung
  überlebt im Wort — sichere Über-Verweigerung), gehört also nicht hierher.
- **Wrapper** (`sh -c '…'`, `bash -c '…'`, `eval '…'`): schalten **alle** Kommandozeilenregeln ab,
  weil der innere Befehl dem Parser verborgen bleibt — gemessen läuft so auch `sh -c 'python
  scripts/harness.py create-task'` als Subagent durch (rc 0), also dieselbe **vorbestehende**
  Klassengrenze wie Regel 4 (die Subagenten-Regel), nicht neu von Regel 5. Verwandt mit der
  Interpreter-Klasse H11 und dem Handover-Wrapper L39.

**Über-Verweigerungen, alle in der billigen Richtung, gemessen und in den Batterien:** `~/pay.py`,
`$HOME/pay.py` (nicht platzierbar → nach Dateinamen beurteilt), `Docs/…` auf einem
case-insensitiven Host, ein Ziel unter `project_memory/staging/**` (fällt in Regel 1), `3>& …`
(schreibt in bash keine Datei, wird trotzdem verweigert). Reibung, kein Loch.

**Urteil: Rest, benannte Restklasse, keine der Über-Verweigerungen ist ein Loch.** Der
Datenverlust-Kern (die bytehaltenden Umleitungsformen `>`, `>>`, `>|`, `&>`, `>&`, und das
Variablenziel derselben Zeile) ist geschlossen und rot-getestet; was bleibt, ist Werkzeugsprache
und Wrapper, deren Schließung eine Verbliste oder einen Interpreter-Leser bräuchte (L4/H11) — das
ist eine eigene Abwägung Nutzen gegen Wartungslast, keine offene Naht dieser Runde. Der harte
Rückhalt gegen lead-geschriebenen Code bleibt gemessen `gate_pipeline` bei Merge/Push (urteilt
über Qualität, nicht Autorschaft) — so benannt, nicht als Autorschaftsriegel behauptet.

### L44 — Ein Zeichen, das die Shell nie sieht, und eine Fortsetzung, die sie nicht kennt — GESCHLOSSEN (TSK-0084)

**Mechanismus, zwei Hälften derselben Ursache:** ein Leser urteilt über einen Text, den die
*benannte* Shell so nie bekommt.

1. **Das Bash-Werkzeug löscht ein blankes CR**, bevor bash parst. Gemessen 2026-08-24, indem jede
   Shell eine Zeichenkette zurückschreibt und die **Bytes** verglichen werden, über jedes
   C0-Steuerzeichen, DEL, U+0085, U+2028 und U+2029: genau **ein** Zeichen der Klasse überlebt den
   Weg nicht, das CR auf der `Bash`-Schiene, und zwar auf beiden Wegen (`bash -c <zeile>` und die
   Zeile auf stdin). Ein Backslash davor schützt damit das Zeichen **hinter** dem CR, und zwei
   Wörter **verschweißen** zu einem Pfad.
2. **`_compat._CONTINUATION_RX` war die Vereinigung beider Fortsetzungszeichen** und trug keinen
   Werkzeugnamen, entfernte also unter `tool_name: PowerShell` einen Umbruch, den PowerShell
   honoriert. PowerShell setzt über einen **Backtick** fort, nicht über einen Backslash — gemessen
   an echten Prozessen.

**Gemessene Ketten — vorher offen, jetzt zu.** In echten, außerhalb des Repos aufgesetzten
Projekten, jeweils mit Dateizeugen:

| Zeile | tool | vorher | nachher |
|---|---|---|---|
| `echo poison > project_mem\<CR>ory/approvals/APR-0001.yaml` | Bash | Gate rc 0 → bash rc 0 → das kanonische Item enthält `poison` | **Gate rc 2**, Item unverändert |
| `Get-Content README.md \<LF>Set-Content -Path .claude/settings.json -Value POISONED` | PowerShell | Gate rc 0 → `powershell.exe` rc 0 → Datei überschrieben | **Gate rc 2**, Datei unverändert |
| dieselbe Zeile mit `\`+CRLF | PowerShell | Gate rc 0 → rc 0 → Datei überschrieben | **Gate rc 2** |

Die volle Familie — 9 Umbruch-Schreibweisen × 2 Werkzeuge × 2 Kits, 36 Zeilen — zeigt nachher
**kein** einziges `POISONED`: entweder rc 2, oder rc 0 mit einer Shell, die dann nachweislich nichts
schreibt (bash führt `echo hello tee .claude/settings.json` als **einen** Befehl aus, PowerShell
antwortet auf `Get-Content README.md `<LF>Set-Content …` mit rc 1).

**Wie geschlossen.**

- Hälfte 1 als **Verweigerung**, nicht als Reparatur: `_kernel._EATEN_IN_FLIGHT` nennt pro Werkzeug
  die Zeichen, die dessen Transport löscht, und `_kernel.payload` — die eine Tür, durch die jedes
  blockierende Gate geht — verweigert eine Zeile, die eines davon trägt, mit dem Grund und einer
  Abhilfe für den Nutzer. Reparieren ginge nicht: das CR löschen hätte bash' Lesart und PowerShells
  verloren, und eine Verschweißung überquert eine Wortgrenze, wäre also eine zweite
  **Tokenisierung** der ganzen Zeile.
- Hälfte 2 als **werkzeugabhängige Fortsetzung**: `_compat._CONTINUATION_BY_TOOL` (`Bash` →
  Backslash + Umbruch, `PowerShell` → Backtick + LF), voreingestellt aus dem Werkzeugnamen der
  Nutzlast, die dieser Prozess gelesen hat (`_compat.gated_shell`) — dieselbe Antwort auf
  „nicht durch neun Aufrufstellen fädeln“, die `_LAST_PAYLOAD` für die Befehlszeile schon gibt.

**Kosten der Verweigerung, gemessen:** über alle 22 Test-Module und alle Hook-Dateien der drei Kits
(111 Dateien, geparst) trägt **keine** legitime Befehlszeile ein blankes CR. Die acht, die eines
tragen, sind ausnahmslos Angriffsformen, die ohnehin rc 2 erwarten; die übrigen Treffer sind
Zeichenklassen im Code. Ein **CRLF** wird ausdrücklich **nicht** verweigert — sein CR fällt weg und
der LF dahinter bleibt der Umbruch, den er war —, und dasselbe blanke CR auf der
**PowerShell**-Schiene ebenfalls nicht, weil PowerShell es wirklich bekommt.

**Urteil: geschlossen, in der sicheren Richtung, mit Rot-Beweis.** Laufende Behauptungen:
`tools/test_hooks_v2.py::test_a_line_carrying_a_character_its_shell_never_sees_is_refused` und
`tools/test_hooks_v2.py::test_a_continuation_the_named_shell_does_not_honour_is_not_joined`.

**Was bleibt, benannt.** Die vier `PreToolUse`-Gates **dieses** Repos (`.claude/hooks/`) erben die
werkzeugabhängige Fortsetzung, weil `_harness` die Nutzlast durch dasselbe `_compat` liest — die
CR-**Verweigerung** aber nicht, denn die sitzt in `_kernel.payload`, und `_harness` ruft
`_compat.load` direkt. `.claude/**` ist verbotener Bereich für den Umsetzer; gemessen wird das vom
Prüfer read-only.

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
TSK-0063, H46 und H47 mit TSK-0070, H48 mit TSK-0071, H49 mit TSK-0075, H50–H54 mit TSK-0080,
H55–H57 mit TSK-0081, H58–H61 mit TSK-0082, H62–H68 mit TSK-0083, H69 mit TSK-0084, H71 mit
TSK-0086, H72 mit TSK-0087, H73 mit TSK-0089, H74 mit TSK-0090, H75 mit TSK-0091, H76 mit
TSK-0092, H77 mit TSK-0093, H78 mit TSK-0094, H79 mit TSK-0096, H80 und H81 mit TSK-0097, H70 mit
TSK-0083/TSK-0084. H80 ist mit TSK-0098 geschlossen und H39 dort zur Hälfte aufgelöst; neue
Nummern hat diese Runde nicht erzeugt.

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
| H3 | **GESCHLOSSEN**, mit benannter Resthälfte | die Hälfte, die bleibt, ist der Fixpunkt der Konstruktion und im Eintrag beschrieben: der Digest schließt `project_memory/` aus, weil ein Urteil sonst den Baum decken müsste, in den es geschrieben wird |
| H7 | **Ausnahme, Abnahme offen** | Gate 4 prüft Form, nicht Deckung; die Reparaturstelle liegt im Kernel (`AUTOMATA` ohne `done_states`) |
| H9 | **kein Urteil möglich** | nichts, und das ist der Befund: ohne den Mechanismus aus dem Prüfbericht zu TSK-0003 gibt es keine Kette, die man einordnen könnte. Der Eintrag wartet auf diese Eingabe, nicht auf eine Entscheidung |
| H10 | **Rest**, offen ist nur die Vollständigkeit | die beiden gefundenen Hälften sind geschlossen und je durch einen roten Test gedeckt; für die dritte gibt es keinen Ersatz, sondern eine ungestellte Frage — ein erschöpfender Mutationslauf über `.claude/hooks/` |
| H11 | **Ausnahme, Abnahme offen** | **nichts Technisches.** Gemessen 2026-08-05: `.claude/settings.json` `permissions` trägt genau `deny: ["Agent(harness-lead)"]` und begrenzt die Shell nicht. Die Begrenzung ist **sozial** — Rollentrennung und Item. Eine wirksame Berechtigungshaltung wäre der Schnitt, ist aber eine Nutzerentscheidung und heute nicht gebaut |
| H12 | **Ausnahme, Abnahme offen** | nichts liest heute einen `allowed_scope`; wer `.claude/` schreiben darf, schreibt auch die Gates — ebenfalls **sozial** |
| H16 | **Ausnahme, Abnahme offen** | dieselbe Lage wie H11: **sozial, nicht technisch**. Die Pfad-Hälfte ist offen; von der `cd`-Hälfte ist die Bewegung geschlossen, nicht der Pfad in der Variablen |
| H13, H14, H15, H18, H19, H23 | **Rest**, keine Angriffskette | jeweils dort benannt; H18/H19/H23 sind Über-Verweigerungen, also Reibung statt Loch, und H13/H14/H15 nennen in ihrem Eintrag, was an der Stelle steht |
| H21 | **Ausnahme, Abnahme offen** | dieselbe Kette wie H16 und dieselbe Begrenzung: **sozial**. Ohne Variable greift heute ein Nebengrund (die Zeile nennt den Repo-Pfad wörtlich), und ein Nebengrund ist keine Maßnahme |
| H22 | **Ausnahme, Abnahme offen** | **nichts Technisches**, dieselbe Begrenzung wie H11 — die Reparaturstelle liegt in der Read-only-Klassifikation der Kits |
| H25 | **Ausnahme, Abnahme offen** | dieselbe Lage wie H12, von der sie abhängt: wer `.claude/` schreiben darf, setzt die Frist hoch, die sich ein Gate zugesteht. **Sozial** — Rollentrennung und Item |
| H32 | **Ausnahme, Abnahme offen** | geschlossen bis auf eine Hälfte, und die ist ein Sonderfall von H34: was die Kits als Prosa entfernen, liest davor niemand. **Sozial** — Rollentrennung und Item; die Reparaturstelle liegt im Kit |
| H34 | **GESCHLOSSEN** (TSK-0043), mit benannter Resthälfte | die Prosa-Entfernung der Kits ist an das **Verb** gebunden (`gate_write_scope._VerbBoundMessageRemoval`/`_stage_takes_a_message`) statt an die Flagschreibweise; der Datenverlust-Kern (`rm -f "geschützt"`, `cp -b "geschützt"`) ist zu, und weil `_harness._prose_removed` dasselbe Objekt importiert, auch das Repo-Gate, das DEC-0001 löschte. Rest: die Ersetzung IN einer echten Nachricht bleibt H32; sie zu lesen wäre die Drift H15 |
| H36 | **Rest**, keine Angriffskette auf diesem Host | die Grenze ist gemessen und liegt außerhalb des Gates: die Zeilenlänge, ab der die nicht unterbrechbare Stelle die Frist reißt, kann auf diesem Host keine Shell mehr gestartet bekommen. Der Eintrag nennt, was das ändern würde |
| H37 | **GESCHLOSSEN**, mit benannten Resten (Rest 1–5 im Eintrag) | für den Mechanismus des Eintrags steht Code (`.claude/hooks/_sandbox.py`, drei Tests). Die Reste liegen sämtlich in der **Messvorrichtung**, nicht im Schutz der Gates, und jeder nennt seine Begrenzung: Rest 1 (nicht importiert = unbewacht), Rest 2 (`_audit.record_event` der Kits schreibt `project_memory/.audit/` dieses Repos — Reparaturstelle im Kit, Begrenzung **sozial**), Rest 3 (die Namensliste bleibt eine Aufzählung; `BASH_ENV` gemessen offen), Rest 4 (`watch` sieht keine Neuanlage), Rest 5 (`_inside` kanonisiert die Win32-Namensräume nicht — Gate 1 selbst ist nicht betroffen) |
| H38 | **Ausnahme, Abnahme offen** | **nichts Technisches** für den Schreibzugriff — dieselbe Begrenzung wie H34: die Prosa-Entfernung ist die der Kits (`gate_write_scope._HEREDOC_RX`). Gemessen begrenzt ist nur die Commit-Hälfte: steht der Commit auf derselben Zeile, verweigert Gate 3 sie wegen des Verbs. **Sozial** — Rollentrennung und Item |
| H39 | **Ausnahme** — für `BUG` mit TSK-0098 aufgelöst (wirksam ab dem nächsten Sitzungsstart), für `TSK` unverändert | die Freigabe-Hälfte war eine Erreichbarkeitslücke, weil dieses Repo keinen Freigabe-Haken registrierte; seit TSK-0098 registriert es ihn, `approval_mint_is_wired` meldet `True`, und der Zusatzsatz an der Verweigerung fällt weg. Die REGISTRIERUNG bindet aber erst beim Sitzungsstart: bis der Nutzer neu startet, liest kein Prozess die Antwort. `DONE`/`VALIDATED` für `TSK` hängen weiter am Dispatch-Lease, das diese Werkstatt nicht fährt — dafür gilt DEC-0041 unverändert |
| H40 | **Ausnahme, Abnahme offen** | der Stolperdraht gegen Zitationen abgelöster Verträge liest die `.py`-Quellen von `.claude/hooks/` — Registrierung, Rollendefinitionen, `CLAUDE.md` und `docs/` liest kein Draht; die eine gemessene Lebendzitation steht im Eintrag, ihre Behebung liegt außerhalb des TSK-0058-Scopes |
| H41 | **Rest**, keine Angriffskette | vier gemessene Grenzen des Zeiger-Wächters aus TSK-0009, je im Eintrag; keine berührt eine Gate-Entscheidung. Der lebende Bestand ist in den ersten drei Richtungen leer; die vierte (Zeiger auf Tests ANDERER Dateien, vom Leser übersprungen) trägt heute elf Vorkommen — sieben aus dem H43-, drei aus dem H44- und einer aus dem H70-Eintrag —, alle von Hand aufgelöst |
| H42 | **GESCHLOSSEN** (TSK-0060, `DEC-0043`), mit benannten Resten | der Vertrag ist entschieden statt normalisiert: `INV.scope` regiert genau einen Bereich, `backlog_types.SINGLE_VALUE_FIELDS` deklariert das, `state._assert_single_value_fields` verweigert die Mehrere-Dinge-Form an beiden Türen in den aktiven Zustand und `report._check_single_value_fields` meldet sie als Fehler (gemessen: capture/update verweigert, `validate` 0 → 1 Fehler, `gate_memory_complete` rc 0 → rc 2). Die vier Leser sind unverändert. Reste: ein schon geschriebenes Item wird gemeldet statt geheilt, die Archiv-Tür nimmt die Form weiter an (DEC-0009), die Deklaration ist nicht abgeleitet, und im `office-team` schützt sie keinen Leser |
| H43 | **GESCHLOSSEN** (TSK-0059, `BUG-0038`), mit benannten Resten | die Grenze ist jetzt abgeleitet statt unsichtbar: `backlog_types.REFERENCE_LIST_FIELDS` nennt die Felder, die kein Capture-Vertrag deklariert und deren Elemente der Kernel auflöst, mit einem Stolperdraht über die laufenden Quellen an beiden Enden; alle sieben Lesestellen gehen durch `field_elements` (gemessen: 2 statt 35 Einträge im aktiven PR, Dispatch von REFUSED auf ALLOWED, `validate` von 17 auf 3 Befunde). Reste: der Skalar wird benannt statt abgewiesen, ein bereits beschädigtes Item wird gemeldet statt geheilt, und die Ableitung sieht keinen Leser hinter einem Rückgabe-Objekt — je im Eintrag |
| H44 | **Rest**, keine Angriffskette | vier gemessene Grenzen der Amendment-Ableitung aus TSK-0062, je im Eintrag: die Kriterien eines ANGEWENDETEN Änderungsantrags zählen nicht mehr (Über-Verweigerung, per Test festgehalten); die Zugehörigkeit (`target_pr`) ist nicht signiert (durch den Kernel geschlossen, offen nur vorbei an ihm — und diese Sitzungstür hält Gate 1 zu); `target_revision` wird nie als Wert verglichen (leiht ausschließlich nutzersignierten Inhalt); Hop 1 bleibt für Nicht-Amendments ohne Freigabeterm (Design, H39 — die Amendment-Hälfte ist seit dieser Runde zu) |
| H45 | **Rest** bzw. entschiedene Über-Verweigerung | zwei gemessene Grenzen der Arbiter-Härtung aus TSK-0063, je im Eintrag: die Sitzungswache verlangt die Seh-Eigenschaft auch von shell-freien Registrierungs-Prüfungen (fail-closed, auf diesem Host ohne Effekt; Schließrichtung benannt), und `_can_arbitrate` ist von keinem Test rot-fähig gedeckt (die entfernte `cd`-Probe ist unbeobachtet — H10-Klasse) |
| H46 | **GESCHLOSSEN** (TSK-0070), am eigenen Gate nachgemessen | `>&datei` ist im Bash eine bytehaltende Umleitung (csh-Form von `&>`), die der Umleitungs-Erkenner nicht als Ziel verbuchte; der B1-Fix (`_output_redirect_targets`, Deskriptor nur bei Zahl/`-` verworfen) hat über die Kit-Leih-Mechanik (`_from_kit`) auch das Repo-Gate geheilt — gemessen `echo x >& …` rc 0 → rc 2 an `gate_lead_write_scope.py`, `>&2` bleibt rc 0. Kein Schritt außerhalb der Sitzung nötig |
| H47 | **OFFEN, blockierend** — Schließrichtung (a) zu messen | dieselbe Klasse wie H46, aber die **Variablen**-Variante: Gate 1 leiht den Ziel-Leser des Kits, nicht dessen Zeilen-Zuweisungskarte, also ist `F=team-kits/kernel/state.py; echo x > $F` am Repo-Gate rc 0 (am Kit-Gate seit B2 rc 2). Vorbestehend, von TSK-0070 sichtbar gemacht. Schließrichtung (a): Auflösung in den geteilten Leser ziehen → Kit-Fix heilt mit; (b): Gate 1 baut die Karte selbst → Fix außerhalb der Sitzung. Welche greift, ist zu messen; der Nutzer entscheidet danach |
| H48 | **OFFEN**, nicht blockierend — bewusster Tausch (TSK-0071) | keine Angriffskette auf Zustand oder Durchsetzung: eingefroren ist nur die Anzeige. An die Stelle des Schutzes tritt die bedingte Frischezusage an allen fünf Prosastellen plus der Zeitstempel auf der Seite als Kontrolle (die Seitenfußnote nennt ihn ausdrücklich); Schließrichtung, falls die Klasse im Alltag auftritt: eine Sitzungsbrief-Zeile „Board älter als Index" |
| H49 | **offen**, nicht schließbar mit den Mitteln dieses Ereignisses (TSK-0075) | an die Stelle des Schutzes treten drei Begrenzungen: die erste Verletzung wird blockiert und präzise angeleitet; der Durchlass ist zustandsgenau protokolliert (`gave_up` vs `retry_delivered`), sodass die PM-Retro den Fall zählt statt ihn zu verlieren; die `ENFORCEMENT.md`-Zeile aller drei Kits nennt den Durchlass. Ein Zähler wäre beschreibbarer Zustand über eine Durchsetzungsfrage — bewusst nicht gebaut |
| H50 | **OFFEN als bewusster Tausch** (TSK-0080) | Preis des F1-Fixes: ein gebundenes Kind, dessen `SubagentStop` nie ankommt, ist nach dem TTL-Sweep für den Untätigkeits-Melder unsichtbar. An die Stelle des Schutzes tritt `sweep_orphaned_dispatches` beim nächsten Sitzungsstart (DEC-0044, gemessen: Waise → `FAILED`); innerhalb der laufenden Sitzung deckt nichts, und der Eintrag sagt das. Die Gegenrichtung — melden — hat einen gemessenen Fehlalarm gekostet, dessen Abhilfe einen laufenden Lauf beendet hätte |
| H51 | **offen**, nicht schließbar ohne Schleifenrisiko (TSK-0080) | die Verweigerung des Zugendes kommt höchstens einmal je Befund; danach tragen `idle_reported` auf dem Item, die Board-Karte und der Verfassungstext — die Audit-Zeile jedes weiteren Stops erreicht nach repo-eigener Messung weder Nutzer noch Modell |
| H52 | **offen**, nicht schließbar ohne Provider-Schlüssel (TSK-0080) | ohne `agent_id` wird verweigert statt geraten; ein Zombie-Dispatch hält damit rollengleiche id-lose Zuordnungen dauerhaft still. Begrenzung: der repo-eigene Messwert sagt, dass `SubagentStop` die Id trägt (der Zweig ist der Ausnahmefall), und die Verfassung verlangt gleichrollige Aufgaben sequenziell |
| H53 | **offen**, Messung gehört zum Live-Lauf (TSK-0080) | die Lebensdauer von `stop_hook_active` ist ungemessen; die Fehlrichtung ist stumm, nie schleifend, und kein ausgelieferter Text behauptet mehr als „at most once per finding" |
| H54 | **offen**, nicht blockierend (TSK-0080) | ein ungebunden LAUFENDES Kind wird nach Fensterablauf als „nichts hat diesen Lauf je verfolgt" gemeldet — die Aussage ist datensatz-wahr und die Meldung gewollt; begrenzt, weil Gate-Schicht 3 einem ungebundenen Kind ohnehin jeden Schreibzugriff verweigert, es also nichts liefern konnte, das verloren ginge |
| H55 | **offen**, von innen nicht schließbar (TSK-0081) | die Update-Brücke im Alt-Bestand läuft auf ein gesprochenes Ja statt einer geminteten Freigabe, und auch ein SUBAGENT erreicht sie (Alt-Gate: bridge rc 0, scaffold rc 2) — die Brücke liest ihren Aufrufer nicht, weil ihr niemand eine Payload gibt. Begrenzung: nur Alt-Bestand (im gehobenen Projekt verweigert sie jedem, gemessen rc 2); keine Argumente, Richtungs- und Staging-Hash-Prüfung, Backups, `project_memory` unberührt (gemessen byte-identisch) |
| H56 | **offen**, nicht blockierend — erholbar (TSK-0081) | ein mitten im Kopieren abgebrochener Brückenlauf lässt ein gemischtes Bündel ohne Rücknahme stehen (kernel_files 17→22, Stempel alt); der zweite Lauf hebt sauber (rc 0), `project_memory` unversehrt, kein Datenverlust gemessen — der Docstring der Brücke sagt „what a KILLED run leaves is not undone" |
| H57 | **offen**, am Helfer nicht schließbar (TSK-0081) | ein quotiertes Heredoc an einen INTERPRETER (`python <<'EOF'`) ist vor `gate_ledger_valid` unsichtbar, seit es `_compat.literal_heredoc_free` übernimmt — der Schreibzugriff im Körper kann den Richter des Ledgers ersetzen, und danach fängt nichts mehr (die Commit-Prüfung fährt den Validator, der dasteht; gemessen rc 0 auf kaputtem Ledger). Was begrenzt: der Werkzeug-Weg auf den Validator ist für jeden doppelt verweigert (`guard_harness_selfmod`, `gate_write_scope`), die Zeile muss vom Agenten kommen, und der ersetzte Validator steht sichtbar im Commit-Diff; `_compat.py` benennt den Verlust seit TSK-0081 ehrlich |
| H58 | **offen**, Semantik-Entscheidung des Nutzers (TSK-0082) | die Kante `TSK DONE → VALIDATED` fordert keine Evidence (`state.CONFIRMING_EVIDENCE` kennt nur BUG); die Einzeiler-Regel dort säße auf einer in drei Populationen nie begangenen Kante und machte den V1-Import `("TSK","VALIDATED")` unmöglich. Was stattdessen steht: die Validator-Warnung + das Sitzungsstart-Briefing sagen jeden abgenommenen Task ohne Verdikt an |
| H59 | **offen**, begrenzt durch die neue Ansage (TSK-0082) | nichts treibt ein Projekt in die Phasen 6–9 — der Merge ist der einzige gebaute Forderer der evidence-Schublade, und ein Solo-Projekt auf `main` merged nie (Pilot 3: 11 DONE/0 Evidence; Pilot 4 H2: 0). Die Leere ist seit TSK-0082 bei jedem Sitzungsstart GESAGT statt unsichtbar; ob das reicht, misst der Live-Testlauf |
| H60 | **offen**, begrenzt durch `gate_filing` fail-closed (TSK-0082) | `document_sources` erzwingt nichts: kein Gate liest die Liste, ein nicht begangenes Interview sieht aus wie „nichts zu melden" — aber ein leerer Plan verweigert das erste Dokument ohnehin geschlossen, und die Deckungslücke wird jedem office-Sitzungsstart angesagt |
| H61 | **offen**, Schließrichtung im Repo gebaut (TSK-0082) | kein Kit-Hook merkt selbst, dass sein Fenster abläuft — jede Grenze in einem Kit-Hook ist ein Versprechen des Hooks, keine Durchsetzung; die Konstruktion, die schließt, existiert im Harness (`.claude/hooks/_harness.py::Deadline` liest die registrierte Frist und verweigert DAVOR) und fehlt in den Kits. Begrenzt: alle beobachteten Gate-Laufzeiten ≤0,405 s und die größte eigene Kindgrenze außer gate_pipeline 20 s, beides weit unter dem ≈600-s-Fenster — als Messung, nicht als Schranke |
| H62 | **offen**, aber **veraltet**: die Belegzeilen tragen nicht mehr (rc 0 seit TSK-0083 Runde 5), der Mechanismus ist ungemessen — siehe zweiten Nachtrag im Eintrag | die Köder-Prüfung des Ledger-Gates (`_DECOY_VALIDATOR_RX`) urteilt noch über das ganze Segment, während dieselbe Frage seit TSK-0083 sonst je Stufe gestellt wird — ehrliche Argument-Prosa eines verbürgten Laufs, die einen Köder-Pfad nennt, wird verweigert, sobald das Segment auch das Ledger nennt. Der Ein-Zeilen-Kandidat wurde gemessen und NICHT genommen: er befreit zwei von drei Über-Verweigerungen, lässt die nutzersichtbare stehen (BUG-0064) und lockert zugleich die einzige Regel zwischen dem Gate und einem unbewachten Validator |
| H63 | **GESCHLOSSEN** (TSK-0083, `BUG-0064`) | das Gate verweigerte die Remedy, die sein eigener Text bewirbt. Geschlossen, indem die Ausnahme im Validator-Verzeichnis auf ihren Grund verengt wurde: dort ist der **blanke Name** die kanonische Datei, und befreit wird nur ein **Lauf** davon, nicht seine Nennung. `cd scripts && python ledger_add.py --validate ../ledger/2026.csv && git commit -m x` HEAD rc 2 → jetzt rc 0, gemessen an beiden Zwillingen; die Schließung selbst hat drei Löcher aufgemacht, die in derselben Runde geschlossen wurden (Prüfbericht Runde 4, V1–V3) |
| H64 | **offen**, Über-Verweigerung, bewusster Preis des Umleitungs-Fixes (TSK-0083) | `gate_ledger_valid` liest seit dem F3-Fix JEDES `>` eines Segments als Umleitung — auch in quotierter Argument-Prosa, auch in den Argumenten eines verbürgten Laufs, weil die Redirect-Prüfung vor der Stufenausnahme steht und die gelesene Sicht den Inhalt quotierter Spannen behält. Verweigert wird nur, wenn das Folgewort zugleich Ledger-Pfad oder geschützte Datei ist (`--note "row > ledger/2026.csv"` rc 0→rc 2; `--note "net > gross"` bleibt rc 0). Schließen hieße zu wissen, welches `>` die Shell ausführt — dieselbe Grenze wie H34s Familie, in die sichere Richtung aufgelöst |
| H65 | **offen**, Loch, vorbestehend (benannt TSK-0083) | ein Zielwort, dessen Pfad die Shell erst durch Expansion **herstellt oder beendet** (`$f`, `${…}`, `${X:-…}`, Glob), steht so nicht im Text — dieser Leser sieht nur die Schreibweise, nicht das Wort, das die Shell baut. `cp evil.py scripts/${n:-ledger_add.py}` ersetzt den Validator, rc 0. Nicht schließbar ohne den Zustand der Shell; begrenzt durch den Kit-Wächter derselben Zeile und dadurch, dass der Angreifer die Variable selbst setzen muss |
| H66 | **offen**, Loch, vorbestehend (benannt TSK-0083) | `_compat.shell_readings` sagt „jede Lesart, die eine gewöhnliche Shell dem Text geben könnte" zu und liefert nur die POSIX-Backslash-Lesart; PowerShells Backtick als Fluchtzeichen wird von keiner Lesart aufgelöst. `copy-item evil.py scr` + Backtick + `ipts/ ; git commit -m x` ist rc 0, die Kontrolle ohne Backtick rc 2. Betrifft jedes Gate, das über `shell_readings` urteilt, nicht nur das Ledger-Gate |
| H67 | **offen**, Loch, vorbestehend (benannt TSK-0083) | die Köder- und Geschwisterprüfung des Ledger-Gates wird **nur befragt, wenn dieselbe Zeile eine blockierte Operation trägt**. Ein Lauf eines unbewachten Zwillings ohne Commit und ohne Ledger-Schreibzugriff in derselben Zeile (`python tools/ledger_add.py`, `python scripts/ledger_add.py.bak ledger/2026.csv`) ist rc 0 — an beiden Zwillingen identisch, also nicht Preis einer Runde. Begrenzt: der Gewinn des Angreifers wird erst mit einer zweiten, dann geprüften Zeile wirksam |
| H68 | **offen**, Über-Verweigerung, naheliegender Fix gemessen falsch (TSK-0083) | zwei Schreibweisen, die das Ledger-Gate verweigert, obwohl sie nichts schreiben: ein **handgetippter Backslash** im Validatorpfad (`python scripts\ledger_add.py --validate ledger/2026.csv`, rc 2, weil eine der beiden Lesarten den Backslash frisst und das Gate verweigert, sobald IRGENDEINE Lesart „schreibt" sagt), und ein **quotiertes Semikolon oder ein quotierter senkrechter Strich** in Argument-Prosa, der Segment bzw. Pipeline-Stufe schneidet. Der naheliegende Fix — quotierungsbewusst trennen — ist gemessen falsch: er schluckt den Trenner, den `_SUBSTITUTION_OPEN_RX` absichtlich IN eine quotierte Spanne injiziert, und macht `BUG-0065` wieder auf |
| H69 | **offen**, Werkbank, bewusst nicht gebaut (`DEC-0022`, TSK-0084) | die Gates dieses Repos erben die CR-Härtung der Kits nur zur Hälfte: der Trenner-Teil sitzt in `_compat` und greift mit (rc 0 → rc 2), die **Verschweißung** unter dem Bash-Werkzeug hängt an `_kernel.payload`, durch das `_harness` nicht geht. Gemessen: `echo poison > project_mem<CR>ory/generated/index.yaml` → Gate rc 0 → `index.yaml` 37 318 → 7 Byte (Kopie außerhalb des Repos, HEAD-identisch). Nicht gebaut, weil der einzige Akteur hier ein Agent ist, dessen Irrtum den naheliegenden Weg nimmt — begrenzt durch die Versionsverwaltung und dadurch, dass die Datei aus den Items neu erzeugbar ist; in den ausgelieferten Kits sind **beide** Hälften zu |
| H70 | **Rest**, Messlücke des Instruments, `H10`/`H41`-Klasse (TSK-0083/TSK-0084) | der Vollständigkeits-Draht des Ledger-Gates fragt nach **Mustern** (zwei Leser, Vereinigung), also sieht er eine vierte Ausnahme nicht, die **gar kein** `re.Pattern` befragt — gemessen von Umsetzer und Prüfer unabhängig (`stage.strip().startswith("deno ")` befreit die Stufe, beide Leser grün, im Klon 1 passed), vom Lead ausdrücklich **nicht** nachgemessen. Keine offene Kette im Produkt: der Draht bewacht eine künftige Änderung. Die Frage, die es fangen müsste, ist „welche Stufe wird frei" — im Docstring benannt, als eigene Runde zurückgestellt |
| H71 | **Rest**, keine Angriffskette (TSK-0086) | vier gemessene Grenzen des Lesers der Merge-Rückstandsliste, je im Eintrag: ein Eintrag, den `open()` mit etwas anderem als `OSError` ablehnt, bricht `update-kit` nach erfolgreichem Installerlauf ab (Hook abgesichert, Kommando nicht — Einzeiler benannt); eine gelesene Liste, die zu keinem erkennbaren Eintrag dekodiert, gilt als leer und wird gelöscht (UTF-16 gemessen, so nicht ausgeliefert); der Vergleich entfernt JEDES `CR`, also auch eines mitten in der Zeile oder in einer Binärvorlage (Über-Verwerfen; Verengen brächte Leser und Installer über dieselbe Datei in Streit — genau der Bruch, der die Liste des Nutzers erzeugte); und zwei Zustände nörgeln absichtlich weiter statt zu schweigen. Der Blocker der Runde — eine **unlesbare** Liste galt als erledigt und wurde gelöscht — ist geschlossen: `unlesbar`, `leer` und `verglichen` sind seither drei Antworten |
| H72 | **Rest** (TSK-0087) | gemessene Grenzen der Vier-Augen-Wand, je im Eintrag: die Aufräum-Ausnahme vergleicht Vorlage+Dateiname statt Ort (ein Platzhalterwechsel läuft ohne Lesung, K7/K8 — Verschärfung wäre eine Nutzerentscheidung); Überschreiben eines Inbox-Dokuments ist frei (die Folge ist per Byte-Bindung geschlossen, der Verlust sichtbar); drei benannte Über-Verweigerungen; und die Verfahrens-Grenze (Blindheit, fremde Programme, Lead als Zweitleser). Keine Kette erreicht mehr das Geschlossene: ein fremdes/getauschtes Dokument unter doppelt gelesenem Namen |
| H73 | **Rest** (TSK-0089) | vier gemessene Grenzen der Entscheidungs-zuerst-Runde, je im Eintrag: jede Id in einem Begrenzer, der länger ist als sie selbst, bleibt ungeprüft (16 der 22 gequoteten Spannen sind Text, den jemand liest — 13 Kernel-Meldungen + 3 Handover-Literale; Schließrichtung benannt, eigene Runde); der Regel-Test liest nur die zwei Anker, nicht die Richtung (die Regel umgekehrt passiert ihn, gemessen); eine Überbehauptung ohne Apparat-Wort fällt nicht auf — sichtbar macht sie nur der Abschnitts-Digest, nicht die Byte-Identität; und der Klausel-Schnitt des Wächters liest `,` nicht und `.`/`:` immer als Grenze — beide Fehlrichtungen gemessen, keine trifft den heutigen Text |
| H74 | **Rest** (TSK-0090) | gemessene Grenzen der schnelleren Gate-Suite, je im Eintrag: kein Schutz gegen einen zweiten Läufer (und die Suite drückt als Nachbar selbst stärker, 10→26); der Faktor 11 war Wirtslast, der 4512-s-Leerlauf bleibt unerklärt; drei benannte Abwägungen mit Zahlen (`authored` ohne Spaltenauswahl, Frist-Phase bleibt nachbarfrei, Prüfsätze ungekürzt); Zeilennummern-Zeiger als offene Klasse (H45-Verschiebung war Fall 2). Ruhefenster-Lauf: akzeptierter DEC-0053-Rest mit zwei bereitstehenden Repo-Werkzeugen |
| H75 | **Rest** (TSK-0091) | gemessene Grenzen des E-Rechnungs-Geldpfads, je im Eintrag: der Wächter ist Arithmetik, nicht Semantik (`FR-0065` trägt die zweite Lesung); BR-CO-14 ungeprüft (in sich stimmiger, positions-widriger Kopf läuft durch, gemessen); UBL nur synthetisch belegt, Anzahlungs-Rückfall verweigert laut; XML ohne Geld-Tripel jetzt rc 2 statt still leer; die Geldleser-Klasse im Owned-Manifest ist Urteil mit zwei gepinnten Enden; ein künftiges Umgebungs-Leck wird still geheilt statt angezeigt (der Draht hält die Fixture, die Fixture heilt die Quellen — beides gemessen); und drei Randformen des Lesers mit je sicherer Richtung (ungepinnte dritte Anker-Schreibweise, Rohtext-Ausgabe der Geldfelder, unlesbarer Rundungsbetrag zählt als 0 und endet laut) |
| H76 | **Rest** (TSK-0092) | gemessene Grenzen des neuen Dokument-Schreibwegs, je im Eintrag: der Listeneintrag-Prosakanal (einziger Kanal ohne Wortlaut in der Karte, dreifach begrenzt); eine Freigabe deckt binnen ihrer Stunde ein erneutes Schreiben derselben Bytes nach Hand-Revert (Bedingung im Docstring, `filing_correction`-Lesart); kein Feldschema (die echte Nutzerdatei hätte ihr eigenes Schema verletzt); Prosa-Dokumente absichtlich schreiberlos + drei Web-Schreibrollen ohne Injektionsnotiz (Eigenschafts-Draht wäre eine kleine Runde); vier Ränder mit sicherer Richtung (toter Zweig, unerreichbare Diagnose, fünf Schreibweisen eine Position, Gate-Laufzeit an Dateigröße) und der Fixture-Schreibweg ins Repo-Audit-Log |
| H77 | **Rest** (TSK-0093) | gemessene Grenzen der Wertsprache-Regel, je im Eintrag: kein Gate erzwingt sie (Freitext); der Prosa-Test liest Anker und Ehrlichkeit, nicht Richtung und nicht Vokabelfreiheit (Umkehrung und apparat-freie Überbehauptung bleiben grün, beide Sprachen gemessen — Sichtbarkeit über den Abschnitts-Pin); `document_types` steht nackt im deutschen Satz; der Records-Clerk als einzige Nicht-Lead-Rolle mit freiem `--reason` trägt die Regel nicht (kleine eigene Runde); und eine geänderte Kartenformulierung entwertet offene Fragen fail-closed |
| H78 | **OFFEN, nicht schließbar**, mit benannter Begrenzung (TSK-0094) | ein Client-Startmodus, der die Projekteinstellungen nicht lädt, entfernt alle vier Registrierungsflächen des Kits, während die Dateiwerkzeuge im Projekt schreibfähig bleiben — drei Mitglieder gemessen, die Kette bis Merge+Push durchgefahren (`validate`: 0 Fehler auf gefälschtem Zustand), vier Ränder benannt (Einstiegspunkt beschreibbar und außerhalb des Vertrauens-Hashes, `permissions.deny` fällt unter `--restricted`, Werkzeugfläche 7→152/159 inkl. MCP, Verfassung lädt nicht). Von innen nichts baubar; Begrenzung: bewusster Start, korrigierte Kit-Prosa (`TSK-0095`), informierter Nutzer |
| H79 | **Rest** (TSK-0096) | gemessene Grenzen der Besitz-Ableitung für die Dokument-Schreibroute, je im Eintrag: eine erfundene Zweitdatei ohne `staging/`-Präfix sieht der Leser nicht (die Ableitung liest Namen, nicht Absichten); derselbe FALSCHE Routentext in allen Besitzer-Definitionen kommt durch (Gleichheit ist geprüft, Richtigkeit nicht — Sichtbarkeit über den Abschnitts-Pin der drei Lead-Dateien); und SKILL-Dateien liegen außerhalb der Ableitung, obwohl sie dieselbe Falschaussage tragen können (in dieser Runde eine gefunden und von Hand korrigiert) |
| H80 | **GESCHLOSSEN** (TSK-0098) für den benannten Unterschied, mit einem Rest, den auch das Produkt trägt | eine Befehlszeile hat jetzt eine START-Position, und eine Datei aus einem **Haken-Verzeichnis** dort zu starten ist **jedem** Aufrufer verweigert (`_harness.Executed` + `ProtectedArea.hand_driven`, Verzeichnisse abgeleitet über `kit_hooks_directories`). Nach drei Prüfrunden, die je eine eigene Kette bis `APPROVED` gegen die Vorfassung gefahren haben, ist Schritt 3 in **jeder** gemessenen Form rc 2 — beide Shells, beide Aufrufer, 63 Formen im Haupt-Rig plus 17 Subshell-Formen —, während alle dokumentierten Tageszeilen rc 0 bleiben; die Kit-Regel hätte vier von neun verweigert, darum der engere Schnitt. Mit geschlossen: dieselbe Unplatzierbarkeit in der SCHREIB-Richtung, dort seit dem Bau der Shell-Hälfte offen. Zweite Hälfte: der Freigabe-Haken der Kits ist auf beiden `AskUserQuestion`-Ereignissen registriert, der ehrliche Weg in einer Kopie Ende zu Ende gefahren. Rest mit Shell-Zeugen: ein selbst geschriebenes Skript prägt weiter (H11, in den Kits genauso), und ein Subagent darf ein Kit-Haken*verzeichnis* rekursiv kopieren. Die Subshell-Klasse ist zu, ihre Schreib-Hälfte steht bei H27 |
| H81 | **Rest**, keine Angriffskette (TSK-0097) | der Mint-Leser irrt in beide Richtungen, beide gemessen: eine Registrierung mit quotiertem Pfad, der ein **Leerzeichen** enthält, zerlegt `_invoked_scripts` nicht → `False` + Warnung, obwohl die Zeile münzt (Item `APPROVED`); ein auflösbarer Pfad mit **fehlender Datei** → `True`, kein Wort, obwohl nichts läuft. Kein Kit betroffen (alle drei registrieren über `$CLAUDE_PROJECT_DIR`, gemessen `True`); getroffen wäre ein ausgeschriebener Pfad; die Registrierung, die TSK-0098 in diesem Repo geschrieben hat, geht deshalb über `${CLAUDE_PROJECT_DIR}` und liest gemessen `True`. Nicht hier geschlossen: `_invoked_scripts` trägt auch `doctor` und die Bündel-Vertrauensprüfung, eine Erweiterung ist eine eigene Runde mit eigenen roten Tests an diesen Lesern |
| H82 | **Rest** (TSK-0099) | sieben benannte Grenzen der internen Sicht-Schleife für Design-Entwürfe, je mit gemessenem Preis der Alternative; der Kern — ein gestagter Entwurf erreicht den Nutzer nicht ohne Renderdatensatz über genau seine Bytes — ist an der laufenden Fassung rot gemessen |
| H83 | **GESCHLOSSEN** (TSK-0104), beide Ketten, mit benanntem Rest | Scaffold und Codex-Spiegel kopieren/erzeugen ein Skill-Verzeichnis jetzt nach der Eigenschaft „gehört keiner Rolle" statt nach der Preset-Rollenliste; gemessen am echten Installer in beiden Zwillingen über `team`/`duo`/`solo` und am erzeugten `.agents/skills`. Rest: das subtraktive Entfernen läuft weiter über die Rollenliste, ein zurückgezogenes Referenz-Skill bliebe im Projekt stehen |
| H84 | **Rest**, gemessene Grenzen (TSK-0100) | die Ableitung der Referenz-Skills erzwingt nichts: der Fehler ist vorhergesagt und nicht gemessen, der Dispatch-Header gewährt nichts, die Fluchttür ist Prosa, die zweite Stolperdraht-Richtung ist an der Ableitung tautologisch, und die Kreuzmenge ist die des KITS und nicht die eines Projekts mit abgewähltem Preset |
| H85 | **Rest**, gemessene Grenzen (TSK-0100) | die Herkunftsprüfung sieht keine UNMARKIERTE Textänderung (kein Test dieser Suite geht ins Netz; ersetzt durch `source_commit`/`source_blob_sha1` im Frontmatter), `NOTICES.md` reist nicht ins Projekt, das Bündelschema ist an EINEM echten Export gemessen, ein Bündel ohne `_ds_manifest.json` findet der Suchlauf nicht, und der INHALT eines Design-Systems wird nicht beurteilt — nichts davon ist ein Gate |
| H86 | **Rest** (TSK-0101) | drei Grenzen EINES V1-Erkenners, den `migrate` und `report` schon benutzen — ein Speicher außerhalb des Zustandsverzeichnisses, ein umbenannter darin, einer im Kernelbereich; sie zu schließen hieße eine zweite Definition von „V1-Datensatz" zu schreiben. (e) ist geschlossen und steht als Warnschild: eine Meldung ist kein Schutz |
| H87 | **GESCHLOSSEN** (TSK-0104), mit gewolltem Rest | `pin-kit`/`unpin-kit`/`rollback-kit` auf der Kommandofläche, ein `pinned`-Verdikt in der Sitzungsmeldung, die Zeilen in `README.md` und den drei Verfassungen. Die drei Kommandos DRUCKEN und handeln nicht — eine Sitzung darf einen Hebel ziehen, der Verweigerung hinzufügt, nie einen, der sie wegnimmt. Rest by design: die Pin-Datei legt der Nutzer an und löscht sie |
| H88 | **Rest** (TSK-0101, ergänzt TSK-0104) | der Rollback ist byte-gleich nur über die aufgezeichnete Menge; ältere Sicherungen tragen keine und werden mit Grund verweigert statt geraten, und die Rückstandsliste des NEUEN Kits überlebt seine Rücknahme. (a3) neu und nachgemessen: ein ABSOLUTES Wort in der `RESTORE_SET` wird von den Zwillingen verschieden beantwortet (rc 0 bzw. rc 1 über eine unbehandelte Ausnahme), kein Zwilling schreibt außerhalb. (a4) GESCHLOSSEN in TSK-0104: eine Manifestzeile, die weder in `RESTORABLE` steht noch eine Kopie in der Sicherung hat, wird vor dem ersten Löschen verweigert (beide Zwillinge, rot-zuerst); Rest: ein fremdes Manifest nur aus `RESTORABLE`-Pfaden bleibt ununterscheidbar, und über den Kopie-Zweig auch eine `KEPT_ONLY`-Datei (`.claude/settings.local.json`) mit der älteren Kopie überschreibbar |
| H89 | **Rest, benannt** (TSK-0102) | ohne `git` kann die Vier-Augen-Buchung Alt- von Neuzeilen nicht unterscheiden und TRITT ZURÜCK statt zu verweigern; die Gegenrichtung säße auf genau dem Commit, der die Zeilen zu Altzeilen macht. Begrenzt durch: der Rückzug wird je Datei ins Audit-Log geschrieben, und die Verfassung macht `git` zur Pflicht |
| H90 | **Rest, benannt** (TSK-0102) | zwei identische Buchungen EINES Belegs teilen sich ein Lesepaar, solange keine `invoice_no` gesetzt ist; mit ihr greift `ledger_add.validate_cross`. Gehört in die Duplikatsregel des Validators, nicht in dieses Gate |
| H91 | **Rest, benannt** (TSK-0102) | der gerenderte Aktenplan-Baum zeigt den PLAN und nicht die Platte — er beschreibt die Form mit `<year>`-Platzhaltern. Der Abgleich Plan↔Platte ist die Prüfung des `project-auditor` |
| H92 | **GESCHLOSSEN** (TSK-0106) | `report.origin_root_conflict` beurteilt einen Ursprung TRANSITIV: er gehört zur Wurzel, wenn jeder seiner Elternpfade dort endet. `RQ → HYP → EXP → TSK` legt an und dispatcht end-to-end; der Pin-Test ist invertiert. Rot ohne den Fix: `test_kernel.test_a_task_may_derive_from_an_experiment_two_levels_under_its_root`, `test_report.test_a_task_on_an_origin_two_levels_under_its_root_is_fine` |
| H93 | **GESCHLOSSEN** (TSK-0106) | `approvals._assert_the_pair_commits_an_edge` verweigert jede item-abgeleitete Freigabe, deren `(Typ, Art)` in `APPROVAL_TRANSITIONS` fehlt — die `HYP`-Freigabe ist damit nicht mehr anforderbar, und der Ausweg, der zu ihr zwang, existiert seit H92 nicht mehr. Rot ohne den Fix: `test_approvals_dispatch.test_a_hypothesis_cannot_be_given_a_scope_approval`, `test_approvals_dispatch.test_no_item_type_can_be_approved_on_a_kind_that_commits_no_edge` |
| H94 | **offen, nur noch die Verfassungszeile** (TSK-0106) | der Schreibweg existiert und ist gemessen (`freeze-report`, `staging.freeze_report`); begrenzt wird der Rest dadurch, dass §6/§17 den Befehl nicht NENNEN — ein Report-Writer muss ihn heute von der Kernel-Hilfe erfahren. Seam-Item für Stream E, sonst nichts offen |
| H95 | **GESCHLOSSEN** (TSK-0106) | Mehrdeutigkeit fällt ZU: ein Ursprung gehört zur Wurzel nur, wenn JEDER Elternpfad dort endet; die Verweigerung nennt den Elternteil, der wegführt. Miterledigt: ein Ursprung ganz OHNE Bindung (ein fremdes Wurzel-Item) wurde ebenso durchgelassen. Rot ohne den Fix: `test_kernel.test_an_origin_with_a_parent_outside_the_root_is_refused_at_creation`, `test_kernel.test_a_task_may_not_derive_from_a_ROOT_item_of_another_tree` |
| H99 | **Ausnahme, Abnahme offen** (TSK-0102) | `H11`s Interpreterklasse hebt die Vier-Augen-Buchung mit auf: ein Skript trägt eine ungelesene Zeile nach `HEAD` (dauerhaft ausgenommen) und prägt die zweite Lesung. Begrenzt durch: die Fehlklasse, für die `FR-0065` gebaut ist (Versehen), läuft vollständig durch die Schicht; das Vehikel ist eine Datei im Arbeitsbaum und damit im Commit sichtbar; und der Buchungs-Store ist erste-Zeile-gewinnt, eine Prägung verlangt also drei bewusste Schritte |
| H105 | **GESCHLOSSEN** (TSK-0105) für NEUE Installationen, mit benanntem Rest | das Rollengedächtnis war ein Kanal zwischen erster und zweiter Buchungslesung, den `gate_second_booking` nicht sieht — der Schlüssel `memory:` ist aus jeder Rolle entfernt, deren Lesung frisch sein muss (Verdict-Rollen und jede `writer_role` eines Kernel-Schemas, abgeleitet, rot gemessen). Rest: die SCHREIBSEITE bleibt offen (sechs Hook-Stufen rc 0 auch ohne Schlüssel); ein Gedächtnisbaum, den eine frühere Kit-Version schrieb, bleibt beim Update liegen (kein Installer, Scaffold oder Kernel-Pfad nennt `agent-memory`, gemessen), und ob der Provider ihn ohne Schlüssel lädt, ist nicht gemessen — Naht: `kitupdate` |
| H106 | **Rest, benannt** (TSK-0105) | der Umfang eines QS-Laufs ist Prosa: kein Feld im Evidence-Datensatz und kein Hook zählt, ob die Suite einmal oder zehnmal lief. Begrenzt durch den Rollentext — Beschreibung und Skill, beide Hälften per Test gehalten —, die Verfassungsklausel am GATE-Schritt und die Leiter des PM |
| H107 | **Rest, benannt** (TSK-0105) | der Design-Brief trennt ZIEL von SCHREIBWEISE nur als Prosa: eine Prozessregel, die in den Brief gerät, fängt nichts, weil das Decision-Item Freitext ist. Begrenzt durch die beiden Enden — der PM schreibt die Hälften getrennt und schickt eine Prozessregel ins `INV`, der Designer gibt eine, die ihn erreicht, als Befund zurück |
| H108 | **offen**, nicht blockierend (TSK-0106) | eine Evidenz, die GAR KEINEN Laufumfang erklärt, zählt weiter wie bisher — die Erklärungspflicht lässt sich auf einem unveränderlichen Typ nicht nachträglich erzwingen. Begrenzt: neue Evidenz kann die Erklärung tragen (`--run-scope`), und ein erklärter Teillauf öffnet keinen Merge mehr; der Rest ist eine Vertragsentscheidung (erfasst als `DEC-0061`, VALID) |
| H109 | **offen**, nicht blockierend (TSK-0106) | „auflösbar" heißt für den Kernel: die Datei ist da und definiert den Namen — GEPARST, nicht gefahren. Ein Test, der existiert und übersprungen wird (`skip`, ein Marker, eine Runner-Konfiguration), gilt darum als vorhanden, und `INV.verified` sagt dann mehr als es weiß. Begrenzt: die Erklärung ist an genau einer Stelle (`report.invariant_check_resolution`), sie fällt bei jeder anderen Abweichung zu (fehlende Datei, fehlender Name), und der Umfang eines Laufs ist bereits die Frage von FR-0040/H108 |
| H110 | **offen**, bewusste Über-Öffnung (TSK-0106) | einen Check, dessen Datei der Kernel nicht parsen kann (ein Testfile in einer anderen Sprache), beantwortet er mit UNENTSCHIEDEN: eine Warnung, kein Merge-Blocker. Fail-closed wäre hier ein Merge-Verbot ohne Ausweg für jedes Projekt, dessen Tests nicht Python sind. Begrenzt: der Produzent verifiziert nichts, was er nicht lesen kann, die Warnung nennt die Grenze, und für lesbare Checks bleibt der Blocker scharf |
| H111 | **offen**, Dokumentationslücke des Apparats (TSK-0107) | die Freigabe-Art, auf der die Auditor-Routine laut aller drei Verfassungen reitet (`routine`, ersatzweise `analysis`), hat in keinem Kit einen Erzeuger: `request-approval` bietet neun Arten an, keine davon ist eine der beiden. Rolle, Trigger und Takt des Auditors sind damit in eine Freigabe gehasht, die niemand anlegen kann. Folge für diese Runde: das Fristenregister NENNT Rolle und Takt im Code, statt sie abzuleiten. Kernel + Verfassungstexte, `FR-0038` |
| H112 | **Rest, benannt** (TSK-0107) | der Laufdatensatz der Routine ist ein Nebenprodukt des Ereignis-Logs und sagt „ein Subagent dieser Rolle hat aufgehört", nicht „ein Audit ist gelaufen". Zwei Grenzen: eine rotierte Log-Generation liest sich als „nie gelaufen" (sichere Richtung, rot gemessen), und ein AUFGEBENDER Lauf zählt als Lauf und unterdrückt die Wochenmeldung (unsichere Richtung). Begrenzt durch: `gate_subagent_output` schreibt `gave_up` ins selbe Log |
| H113 | **Rest, benannt** (TSK-0107; Grenze 2026-09-02 nachgemessen) | das Fristenregister kennt kein „erledigt": nichts im Kit hält fest, dass eine Voranmeldung abgegeben oder ein Aufbewahrungsjahr geprüft wurde, also steht ein Eintrag, bis seine QUELLE sich ändert. Über-Meldung, nicht Schweigen. Ein „erledigt" wäre kanonischer Zustand, also Kernel |
| H114 | **offen**, kein Modellpfad (TSK-0108) | nach einem Verzeichniswechsel läuft die Registrierung des Ziels, aber die Hook-DATEIEN des Startorts (`${CLAUDE_PROJECT_DIR}` bleibt stehen, und genau so buchstabieren die Kits ihre Kommandozeilen) — gemessen über BEIDE Wege, `/cd` und die Steuer-Anfrage `set_cwd` der VS-Code-Erweiterung. Begrenzt durch: kein Werkzeug des Modells löst den Wechsel aus, er kommt vom Client. Auf dem `/cd`-Weg geht ein Trust-Dialog voran, aber nur vor dem ERSTEN Wechsel in ein Verzeichnis (gemessen: Erst-Dialog `m2a.log`, späterer Wechsel dialogfrei `m4.log`). Auf dem `set_cwd`-Weg ist gemessen nur der dialogfreie Wechsel an ein bereits vertrautes Ziel; ob an einem unbekannten Ziel ein Dialog erscheint, ist NICHT gemessen |
| H115 | **offen**, kein Angriffspfad (TSK-0108) | ein Verzeichniswechsel bringt Subagenten und `agent:`-Bindung des Ziels NICHT mit, obwohl der Changelog „agents" nennt — gemessen am Task-Fehler, an der Gegenprobe mit Neustart und am Wechsel über `set_cwd`. Begrenzt durch: die Zeremonie behält ihren Neustart, der Schaden ist eine falsche Erwartung; Client-Verhalten, hier nicht schließbar |
| H116 | **Ausnahme, Abnahme offen** (TSK-0108) | die Hook-Registrierung wird mitten in der Sitzung neu gelesen, sogar zwischen zwei Werkzeugaufrufen EINER Runde (gemessen) — `H12`s Fläche erweitert sich von „welcher Code urteilt" auf „ob überhaupt etwas urteilt". Begrenzt durch: dasselbe wie `H12` (Rollentrennung, Item) plus die Sichtbarkeit der geänderten `settings.json` im Diff |
| H117 | **Rest, benannt** (TSK-0109) | nichts startet den Generator nach einer Buchung; der Datenstand im Kopf trägt das **nicht**, weil er nur das jüngste Ledgerdatum ist (ein Nachtrag lässt ihn byte-identisch, gemessen). Begrenzt allein durch den Ordnerführer `dashboards/ABOUT.txt`, der den Befehl nennt und die Lücke ausspricht; der Auslöser ist ein Seam-Item an Stream G (`gate_ledger_valid.handle_post_tool_use`) |
| H118 | **Rest, benannt** (TSK-0109) | die Seite sagt beides selbst: „gerechnet beim Öffnen der Seite aus der Uhr dieses Rechners" und woher die 30 Tage kommen (§ 286 Abs. 3 BGB); ohne Skript bleibt der Strich stehen statt eine Zahl zu behaupten |
| H119 | **Rest, benannt** (TSK-0109) | zwei Folgen einer Wurzel: (1) `_BLOCKED_SCRIPT_RX` kennt den Generator nicht, er läuft gegen einen ungültigen Ledger — begrenzt dadurch, dass er selbst validiert und den Befund wörtlich ins Banner schreibt, die Summen sichtbar lässt und als nicht belastbar bezeichnet; (2) es gibt kein Gegenstück zu `render.json`/`gate_design_sighted`, eine von Hand geschriebene `dashboards/finanzen.html` ist von einer erzeugten nicht zu unterscheiden — begrenzt dadurch, dass der nächste Lauf sie atomar überschreibt und der Ordnerführer das sagt. Nach DEC-0056 kein Härtungsziel |
| H120 | **kein Loch mit Kette — von Nachbarn gedeckt, benannt** (TSK-0111) | die Haken-Spiegelregel `test_hooks._assert_mirrored` fragt für einen Namen nur, ob die Kopien der liefernden Kits gleich sind — ob ein Kit ihn gar nicht liefert, fragt keine ihrer beiden Schleifen. `format_on_write.py` (dev und research, nicht office) ist dort kein Befund, mit Absicht. Präsenz entscheidet die Registrierung, und zwei Nachbartests halten beide Richtungen (gemessen, Eintrag unten). Für die Skills ist die Präsenz-Hälfte gebaut (`tools/test_shared_skill_contract.py`) |
| H121 | **GESCHLOSSEN** (TSK-0111 gemessen, TSK-0114 behoben) | der Leser der Löcherliste (`test_gates._hole_entries` plus die Backtick-Suche in `test_gates.test_every_test_the_hole_list_names_is_one_that_exists`) kannte keinen Code-Zaun: drei Backticks waren ihm drei Begrenzer, also paarte alles hinter dem ersten Zaun eines Eintrags gegen den falschen — jedes Zitat dort war UNGEPRÜFT, ein falsches Grün. `_prose_of` schneidet die Zäune jetzt vor der Paarung heraus, `_tests_by_module` löst einen Namen auch gegen `tools/test_*.py` auf (der Nachbarbefund aus TSK-0109), und H46 trägt sein Präfix. Rot ohne den Fix: `test_gates.test_every_test_the_hole_list_names_is_one_that_exists` mit einem Geist-Namen hinter einem Zaun (vorher 1 passed, nachher 1 failed) |
| H122 | **Rest, benannt** (TSK-0110, in TSK-0114 nummeriert) | der Melder über ungelesene Prosa unter `docs/` fragt, was **git trägt** (`test_repo_hygiene._carried_files`, `git ls-files -c -o --exclude-standard`): eine Nennung in einer IGNORIERTEN Datei — ein Laufprotokoll, `project_memory/.audit/`, ein erzeugtes Dashboard — sieht er nicht und meldet die Datei als ungelesen. Begrenzt durch: der Docstring des Melders sagt genau diesen Satz statt des größeren, der Melder warnt und blockt nie, und auf diesem Baum gibt es außerhalb der Werkzeug-Caches keine einzige nicht getragene Datei — das blinde Feld ist heute leer |
| H123 | **verkleinert, gemessen, der Rest ist benannt** (TSK-0113/TSK-0114; TSK-0116 misst neu) | die Flaggen-Form ist größtenteils GESCHLOSSEN: seit TSK-0116 liest die Regel ein zerstörendes Wort an JEDER Stelle einer Aufrufung, also auch in einer Flagge — `find archive -name x.pdf -delete` und `tar --remove-files … archive/…` sind am Piloten gegen alle acht registrierten Office-Haken von **ALLOW** auf **rc 2** gemessen. OFFEN bleibt genau eine Teilklasse: eine Flagge, die im ZIEL statt in der Quelle löscht (`robocopy … /MIR`, `rsync --delete inbox/ archive/2026/`). Der Grund ist die REIHENFOLGE der Lesungen — `_filing` erkennt beide als Kopierer, der Kopier-/Bewegungszweig beantwortet die Aufrufung und kehrt zurück, bevor nach einem zerstörenden Wort gesucht wird. Begrenzt durch: die Klasse steht namentlich im Kopf des Wächters, Verfassung und Rollentext zeigen dorthin statt die Wand absolut zu behaupten; die Reihenfolge selbst ist beidseitig gemessen (`tools/test_hooks.py::test_a_filing_move_with_a_source_deleting_copier_flag_is_judged_as_a_move`) |
| H124 | **Rest, benannt** (TSK-0113, in TSK-0114 nummeriert) | die Fristenmeldung liest die Uhr der lokalen Maschine einmal je Sitzungsstart (`_duties.briefing`, `datetime.date.today()`): eine Sitzung über Mitternacht behält die Antwort von gestern, und zwei Maschinen in verschiedenen Zonen antworten im selben Moment verschieden. Begrenzt durch: kein Angriff und kein Datenverlust — eine Meldung wechselt einen Tag zu früh oder zu spät —, die Tagesgrenze selbst ist beidseitig gemessen, und der Nutzer entscheidet ohnehin über jede Frist |
| H125 | **GESCHLOSSEN** (TSK-0114 gemessen, TSK-0116 behoben, Nacharbeit 1 nachgemessen) | die Lösch-Regel des Archiv-Wächters stand auf einer AUFZÄHLUNG von sieben Verben; jedes andere zerstörende Verb ging durch. An ihre Stelle tritt eine Eigenschaft: die REICHWEITE einer Zerstörung trifft ein Fach von Rang, gelesen in BEIDEN Richtungen — die Position liegt IM Fach, oder ein Fach liegt IN der Position. Am Piloten gegen alle acht auf Bash und PowerShell registrierten Office-Haken als Prozesse gemessen, HEAD e45c0ca gegen diese Runde: `unlink`, `git clean -fdx` (mit und ohne Pfad), `Clear-Content`, `clc`, `find -delete` und `tar --remove-files` von **ALLOW** auf **rc 2**; die VORFAHREN-Form ebenso — `git clean -fdx .`, `git clean -fdx ./`, `git clean -fdx -e docs`, `rm -rf .`, `find . -delete`, `Remove-Item -Recurse -Force .` (auch als PowerShell) und `shred .`, alle acht von ALLOW auf rc 2 (Nacharbeit 1, Prüferbefund B1). Die zwei Kontrollen bleiben rc 2; acht Über-Verweigerungs-Kontrollen bleiben rc 0, darunter `git clean -fdx` in einem Projekt OHNE Fach von Rang, dieselbe Zeile mit `cwd=docs` und `cd docs && git clean -fdx`. Rot ohne den Fix: `tools/test_hooks.py::test_a_destruction_that_names_an_ANCESTOR_of_a_tray_is_the_same_destruction`. Geschlossen ist die BENANNTE und die VORFAHREN-Form; **nicht gedeckt** und im Eintrag einzeln gemessen: Operanden, die eine Pipe übergibt (`xargs rm -rf`), ein Verzeichnis-LINK auf ein Fach, die GLOB-Schreibweise (`rm -rf *`), ein Verzeichniswechsel, der landet aber nicht wirkt (`H144`), und die Vokabelliste der zerstörenden Wortstämme (`H129`) |
| H126 | **Rest, verkleinert** (TSK-0115 gemessen, TSK-0120 Naht gebaut) | die Ablaufregel für eine offene Freigabe-Anfrage steht DREIMAL: in `approvals.open_requests` (je Datei über `pending_request`), in `report.generate_session_brief` und seit TSK-0115 in `board.open_requests`. Der Grund ist der Importgraph — `approvals` importiert `state`, `state` importiert `board`, ein Import zurück schlösse den Zyklus. Drei Leser stehen dabei auf ZWEI Uhren: `approvals.open_requests` (über `has_expired`) und der Brief lesen beide `time.time()`, die Tafel ihren eigenen Seitenstempel. Gemessen an einem Store mit einer Anfrage von 2 s Laufzeit: Tafel **1**, Brief drei Sekunden später **0**, Tafel auf der Platte weiter **1**, nach dem nächsten Zustandsschreiben **0**. Begrenzt durch: `test_board.test_the_board_and_the_session_brief_agree_on_the_open_requests` hält die zwei Leser im selben Moment gegeneinander, und die Tafel sagt in ihrem eigenen Kopf, dass ihr Stempel der Vergleichspunkt ist. Naht an Strom C: ein OPTIONALES zweites Argument `now=None` an der **vorhandenen** `approvals.open_requests`, das die Tafel setzt und die drei Haken-Aufrufer weglassen |
| H127 | **OFFEN, gemessen — halb geschlossen** (TSK-0115; TSK-0120 gab den Diagrammen ihren Auslöser) | eine Handänderung an einem erzeugten Diagramm sieht zwischen zwei Zustandsschreibvorgängen niemand: `plan_diagram.is_pristine` unterscheidet `pristine`/`hand-edited`/`stale` und wird von keinem Gate und keinem Validator gerufen — nur von `tools/test_plan_diagram.py`. Gemessen an den zwei Dateien über dem echten Zustand dieses Repos (289 Items): frisch `pristine`; ein `<text>` per ElementTree ergänzt → `hand-edited`; dieselben Bytes gegen einen verschobenen Status → `stale`; und in einem laufenden Projekt meldet das nichts davon. Begrenzt durch: `generated/` ist in jedem Kit ignoriert, also erreicht eine Handänderung weder einen Commit noch eine zweite Maschine, und der nächste Schreibvorgang überschreibt sie — sobald die Auslöserzeile aus dem Protokoll von TSK-0115 in `state._write_board` steht; bis dahin schreibt überhaupt nur dieses Modul die zwei Dateien. Naht-Vorschlag an C: `report.validate_state` meldet `stale`/`hand-edited` als Warnung |
| H129 | **Rest, benannt** (TSK-0116) | die Hälfte der Zerstörungsregel, die sagt WAS zerstört, bleibt eine Vokabelliste (`guard_fs_tripwire.NAMING_DESTRUCTION` / `SWEEPING_DESTRUCTION`): ob ein Programm eine Datei entfernt, ist eine Tatsache über das Programm und aus der Befehlszeile nicht ableitbar — ein `PreToolUse`-Haken läuft VOR der Zeile und hat kein Nachher zu vergleichen. Begrenzt durch: jeder Eintrag ist an BEIDEN Enden gemessen (`tools/test_hooks.py::test_every_destroying_stem_is_load_bearing_at_both_ends`), die Stämme werden über JEDES Wort einer Aufrufung und nach Wortstamm gelesen (Kommandowort, Flagge, Unterbefehl), sodass jede Verb-Substantiv-Form ohne eigene Nennung trägt — ein ALIAS jedoch nur, wenn er selbst ein Stamm ist (`ri`, `clc` sind es; gemessen) —, und nach `DEC-0056` ist der Gegner der IRRTUM und nicht der Vorsatz |
| H130 | **Rest, benannt** (TSK-0116) | die zweite ehrliche Form einer Aufbewahrung — `retention: null` für ein Fach ohne zählbare Frist, die die Vorlage ausdrücklich erlaubt — ist über `add-filing-rule` NICHT erreichbar: `approvals.filing_rule_subject_manifest` verweigert schon die FRAGE nach einer Regel ohne Aufbewahrung, also kann keine Freigabe dafür entstehen. Gemessen in `tools/test_kernel.py::test_a_retention_the_deadline_register_cannot_read_is_refused_before_it_reaches_the_plan`. Begrenzt durch: der Kernel-Leser akzeptiert die leere Form (dieselbe Messung), eine von Hand geschriebene Regel darf sie tragen, und das Fristenregister meldet eine Regel ohne Aufbewahrung gar nicht erst. `kernel/approvals.py` liegt im `forbidden_scope` dieses Stroms |
| H131 | **Rest, benannt** (TSK-0116) | die Zeilennummern der Anlage EÜR, die das Kit ausliefert (`templates/project_memory/master_data.yaml`, `euer_form:`), stammen aus öffentlichen Ausfüllhilfen und NICHT aus dem amtlichen Vordruck; zwei der gelesenen Quellen widersprachen sich bei der Werbe-Zeile (51 gegen 54), und zwischen zwei Formularjahren verschieben sich die Nummern messbar. Begrenzt durch: Formularjahr und Herkunft stehen IM Vokabular, beide Leser drucken sie neben jede Zeilensumme, im Code steht keine Nummer und kein Jahr — eine Korrektur ist eine Zeile in einer Nutzerdatei (`tools/test_finance_dashboard.py::test_a_fresh_project_ships_a_category_vocabulary_the_p4_12_stall_cannot_recur_on`) |
| H132 | **OFFEN als benannte Verbreiterung** (TSK-0117, FR-0074) | die Plan-Freigabe (`approvals.PLAN_KIND`) bricht absichtlich die Ein-Item-Bindung: EINE Antwort lässt jedes Ziel ihrer Liste die Kante `DRAFT -> APPROVED` gehen. Am Piloten außerhalb des Repos mit dem ausgelieferten `gate_approval.py` als Prozess gemessen: zwei Ziele, eine Frage, beide danach APPROVED und beide mit demselben `approval_ref`; `IN_DELIVERY` bleibt verweigert. Begrenzt durch: nur die Scope-Frage (Lieferung und Abnahme bleiben je Ziel), den Hash über die Liste UND über das Scope-Manifest jedes Ziels (ein geändertes Ziel fällt aus der Deckung, die übrigen bleiben), die Verweigerung einer leeren Liste, und eine Frage, die jedes Ziel namentlich nennt statt zu zählen. NICHT begrenzt: die Länge der Liste — dreißig Ziele sind eine Frage |
| H133 | **OFFEN als benannte Verbreiterung** (TSK-0117, FR-0083) | die zweite Mint-Route (`kernel/sdk_approval.py`, der Einstieg aus dem Agent-SDK-`canUseTool`) kann die dritte Bedingung von `approvals._assert_minting_caller` nicht tragen — das einbettende Programm IST `__main__` —, also prägt jedes Programm, das das Paket importiert und die Brücke ruft. Gemessen am Piloten: Haken-Route `minted_via: user_answer_via_approval_hook`, Brücken-Route `program_answer_via_agent_sdk`, ein fremdes Skript weiterhin verweigert. Begrenzt durch: den Stempel auf jedem Datensatz und die Karte, die ihn vorliest; die Kernel-Verweigerung jeder Art aus `approvals.IRREVERSIBLE_KINDS` für die Programm-Route (an `push` gemessen, danach kein lebendes Token); und `gate_git`, das als Prozess jeden Merge über einen so freigegebenen Vorgang verweigert. NICHT begrenzt: der vorsätzliche Fälscher, gegen den schon die Haken-Route nichts wert war |
| H134 | **OFFEN, nicht schließbar** (TSK-0117, FR-0082) | `blocked` ist ein Zustand und keine Messung: niemand prüft nach, ob der Browser wirklich fehlte. Gemessen am Piloten mit dem ausgelieferten `gate_git.py` als Prozess: ein `blocked` ohne Satz wird vom Kernel verweigert, mit Satz aufgenommen, und der Merge verweigert rc 2 und zitiert den Satz samt „nichts wurde geprüft". Begrenzt durch: ein falsches `blocked` kauft nichts (es schließt wie ein `fail`), der Datensatz ist unveränderlich, und die Einschränkung steht im Vokabular-Kommentar, in der Hilfe der Flagge und in der Verweigerung selbst. NICHT begrenzt: die Wahrheit der Begründung, in beide Richtungen |
| H135 | **Rest, benannt** (TSK-0118; Leser seit TSK-0120 `kernel.scopes`) | die Zeugen-Hälfte der Überlappungsprüfung ist eine STICHPROBE, keine Sprache: `witnesses` füllt jeden Wildcard-Lauf mit EINEM Platzhalter-Segment, also findet sie eine Überlappung nur dort, wo ein so gebildeter Pfad im anderen Scope liegt. Zwei Aufträge, die sich nur in einer Region überlappen, in die kein Zeuge fällt, und deren Dateien es heute noch nicht gibt, kommen durch. Gemessen (`_round-scratch/TSK-0118/probe_h135.py`, beide Aufträge durch den Kernel erfasst): `a/*x` gegen `a/y*` — **rc 0** bei leerem `a/`, **rc 2**, sobald `a/yx` im Baum liegt. Begrenzt durch: die Baum-Hälfte fängt denselben Fall ab dem ersten passenden Dateinamen, das Werkzeug verweigert in keinem Projekt etwas (Werkstatt-Instrument), und der Schnitt ist nach `DEC-0062` ohnehin ein Urteil ohne Gate |
| H136 | **GESCHLOSSEN** (TSK-0118 gemessen, TSK-0117 gebaut, TSK-0120 nachgemessen) | die Vor-Dispatch-Prüfung hat in einem Kit-Projekt KEINEN ausführbaren Weg: `gate_write_scope` verweigert jede schreibfähige Zeile, die die Durchsetzungsschicht nennt, und ein Skill-Verzeichnis wird nach `.claude/skills/` installiert. Am ausgelieferten Haken als Prozess über einem dev-team-Projekt gemessen (`_round-scratch/TSK-0118/probe_cmdline.py`, `probe_cmdline2.py`): `python .claude/skills/parallel-streams/check_scope_overlap.py` **rc 2**, dieselbe Zeile mit `.agents/skills/...` **rc 2**, `python scripts/kit_checks.py` rc 0, `python scripts/harness.py check-scopes` rc 0. Der Kit-Text behauptet darum nichts: Verfassungsabsatz und Skill sagen, dass nichts ein überlappendes Paar verweigert, und dieser Satz ist selbst gemessen (`tools/test_parallel_streams.py::test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap`). Begrenzt durch: genau diese Ehrlichkeit — der Weg, der rc 0 bleibt, ist ein Kernel-Verb hinter `scripts/harness.py`, und das ist die wörtliche Anforderung an den Kernel-Strom |
| H137 | **Rest, benannt** (TSK-0118) | der Modul-Docstring von `hooks/_routine.py` sagt, jede Verfassung reite die Auditor-Rolle auf einem wöchentlichen Rhythmus — das stimmt für keine der drei mehr: dev und research nennen beim `project-auditor` gar keinen Takt, und die Office-Rollenzeile hat ihn in dieser Runde verloren (N2). Der Takt steht damit an genau einer Stelle, `_routine.audit_period_id` (eine ISO-Woche), und der Docstring behauptet einen zweiten Ort. `team-kits/*/hooks/**` ist forbidden_scope dieses Items, die Datei ist dreifach gespiegelt. Begrenzt durch: kein Verhalten hängt am Docstring, der Takt selbst ist beidseitig gemessen (`tools/test_routine_feed.py::test_a_run_in_an_earlier_week_leaves_the_routine_due`), und dass kein Rollen- oder Verfassungstext ihn ein zweites Mal nennt, ist `tools/test_parallel_streams.py::test_no_text_that_describes_the_audited_role_states_the_cadence_the_code_owns` |
| H138 | **AUSNAHME, vom Nutzer abgenommen 2026-09-03** (TSK-0119) | die Konformitätsbefunde von `kit_design_render.py` verweigern nichts: der Renderer meldet sie mit **rc 3** und schreibt `review/render.json` trotzdem, und `gate_design_sighted` liest genau diesen Datensatz — der Haken fragt „wurde gerendert“, nicht „ist er in Ordnung“. Gemessen: Entwurf mit Kontrast 1,92:1 → Renderer rc 3, Haken **rc 0**. Begrenzt durch: Rückgabewert + gedruckter Befund, die drei Rückgabewerte einzeln in der `product-designer`-SKILL-Zeile, und die ENFORCEMENT-Zeile, die das Nicht-Urteil ausdrücklich sagt. Kein Gate, weil `DEC-0056` (b) für diese Fehlklasse keinen gemessenen Fall kennt. Der Nutzer hat die Ausnahme am 2026-09-03 erteilt (`DEC-0069`) („melden reicht vorerst“); sie FÄLLT beim ersten echten Fall, in dem ein Entwurf MIT Befunden trotzdem gebaut oder eingefroren wurde |
| H139 | **OFFEN, gemessen, nicht in diesem Strom schliessbar** (TSK-0119) | die BUILD-Hälfte von `FR-0077` (C1/C2/C3 im `browser_smoke()`, B3 über `kit_checks._frontend_sources()`) ist nicht gebaut: beide Wirtsdateien liefern dev-team und research-team **byte-gleich** aus (sha256 gemessen), und `research-team/**` war diesem Strom verboten. Gebaut ist die frühere Stelle, der gestagte DSN-Entwurf. Begrenzt durch: den eingefrorenen Vertrag selbst und den Fidelity-Review der Phase 3 — Urteil, keine Messung |
| H140 | **Rest, benannt** (TSK-0119) | die Rangfolge-Regel urteilt über `[data-view]`-Container, also über das, was der Entwurf DEKLARIERT: dasselbe Markup mit zwei `data-primary-action` ist **rc 3** mit `data-view` und **rc 0** ohne. Und der Kontrast schweigt über Text auf Bild/Verlauf/halbdurchsichtiger Schicht — als `NOT DECIDABLE` gedruckt, weder Befund noch bestanden. Begrenzt durch: die SKILL-Zeile macht das Auszeichnen zum Verfahrensschritt, die undecidable-Zeile wird gedruckt, und beide Hälften der zweiten Grenze hält ein Test |
| H141 | **Rest, benannt** (TSK-0118, Nacharbeit 1) | `tools/test_parallel_streams.py`s `_CADENCE_IN_PROSE` ist eine AUFZÄHLUNG von Takt-Adverbien (`weekly`, `daily`, `monthly`, `every week` …). Ein Takt, der anders geschrieben ist, ist ihr unsichtbar: als Zahl von Tagen, als Wochentag, als Umschreibung, als Dauer-Token, oder deutsch gebeugt. Gemessen (`_round-scratch/TSK-0118/probe_h141.py`): `weekly` **feuert**, während `runs once a week`, `on Mondays`, `every seven days`, `runs each Monday morning`, `cadence: 7d` und `wöchentliche` **still** bleiben. Begrenzt durch: der Leser trägt seine Grenze im eigenen Docstring und führt fünf der sechs blinden Formen als eigene Testzeilen mit; das Subjekt ist EIN Rollentext plus die Verfassungsblöcke, die ihn nennen, also eine kleine gelesene Fläche; und „ist dieser Satz eine Taktangabe“ ist Weltwissen, keine Ableitung aus dem Baum — ein Test, der es behäuptete, wäre die nächste Aufzählung |
| H142 | **Rest, benannt** (TSK-0118, Nacharbeit 1) | die Überlappungsprüfung unterscheidet seit dieser Nacharbeit, was der Aufrufer GENANNT hat (ein `--root`, das kein Verzeichnis ist, und eine `--only`-Id, die kein Auftrag trägt → rc 1) von dem, was niemand genannt hat (Standard-Wurzel außerhalb eines Projekts → rc 0). Offen bleibt die Mitte: eine genannte Route, die AUFLÖST und trotzdem kein Paar ergibt — `--only TSK-0001` allein — ist rc 0 mit „NOTHING WAS COMPARED“. Gemessen (`_round-scratch/TSK-0118/probe_m4_m5.py`): Tippfehler-Wurzel rc 1, unbekannte Id rc 1, eine echte Id rc 0, Standardwurzel ohne Projekt rc 0. Begrenzt durch: die Meldung sagt in allen Fällen, dass nichts verglichen wurde, und teilt kein Wort mit „disjoint“ (`tools/test_parallel_streams.py::test_a_route_the_caller_named_has_to_resolve_and_one_nobody_named_does_not`); strenger geht es nicht, ohne den Lauf ohne Argumente außerhalb eines Projekts zu brechen, den `tools/test_hooks_v2.py::test_a_repo_tool_that_imports_the_kit_tree_leaves_no_bytecode_in_it` fährt |
| H143 | **Rest, benannt** (TSK-0118, Nacharbeit 1) | eine erklärte Naht, die die GESAMTE Ownership eines der beiden Aufträge deckt, wird seit dieser Nacharbeit verweigert (rc 1) — eine, die nur einen TEIL der Überlappung deckt, während beide Aufträge anderswo noch etwas besitzen, deckt diesen Teil weiter zu. Gemessen (`_round-scratch/TSK-0118/probe_m4_m5.py` und die letzte Sonde in `tools/test_parallel_streams.py::test_a_seam_that_swallows_an_orders_whole_ownership_is_refused`): `--seam "**"` und `--seam "src/**"` über zwei Aufträgen auf `src/**` sind rc 1, während `--seam "src/**"` über `src/**`+`lib/**` gegen `src/**`+`docs/**` rc 0 bleibt, obwohl `src/a.py` beiden gehört. Begrenzt durch: die Naht ist eine ERKLÄRUNG des Orchestrators und wird gedruckt, nicht verschwiegen — jeder gedeckte Pfad steht als `seam`-Zeile im Bericht —, und die Merge-Runde wendet genau diese Liste an, also ist eine falsch erklärte Naht dort ein Befund gegen den Schnitt (`DEC-0062` (5)) |
| H144 | **GESCHLOSSEN, mit fünf benannten Über-Verweigerungen** (TSK-0116 Nacharbeit 3 gemessen, TSK-0120 Naht S9 gebaut, Nacharbeit 1–3 nachgeschärft) | die Verengung, die das Fegen gegen das wirkliche Arbeitsverzeichnis misst (`H125`, `M1`), folgt auch einem Verzeichniswechsel, der zwar LANDET, aber für die nächste Aufrufung nicht wirkt: ein `&&`, das kurzschließt, und ein `cd` in einer Pipe-Stufe oder hinter `&` (beides Subshells). Gemessen über alle acht registrierten Office-Haken, mit `rm -rf .` allein bei rc 2: `false && cd outbox ; rm -rf .`, `ls` in eine Pipe an `cd outbox` mit folgendem `rm -rf .`, `cd outbox` in eine Pipe an `rm -rf .` und `cd outbox & rm -rf .` sind **rc 0**. Begrenzt durch: die Formen, in denen der Wechsel gar nicht landet, sind geschlossen (`cd nichtda`, ein Tippfehler, `cd ..` → rc 2), die Gegenrichtung ist unberührt (ein wirklicher `cd` verengt weiter, `cd archive && rm -rf .` bleibt rc 2), und nach `DEC-0056` ist der Gegner der IRRTUM — ein Tippfehler schreibt kein `& ` vor sein `rm` |
| H145 | **GESCHLOSSEN bis auf die Unentscheidbarkeit** (Prüfung TSK-0119) | ein verlinktes Blatt wirft unter `file://` beim Lesen von `cssRules`, und der stumme `catch` machte daraus ein leeres Blatt: Farbliteral nur dort → **rc 0**, `:focus-visible` nur dort → **rc 3** mit „declares no :focus-visible rule at all“ — eine Anschuldigung über eine wirkende Regel. Jetzt `UNDECIDED` mit dem Namen des Blattes, und die Absage-Aussage wird unterdrückt. Offen bleibt: die Regeln des Blattes sind nicht beurteilbar |
| H146 | **GESCHLOSSEN bis auf die Gruppen-Komposition** (Prüfung TSK-0119) | der Kontrast rechnete `0 < opacity < 1` als deckend (`.card { opacity: .05 }` → **rc 0**, falsch grün) und sah erzeugten Text nie (`::before { content }` → **rc 0**). Jetzt wird die kumulierte Deckkraft in die Alpha gefaltet und `::before`/`::after` mitgemessen. Offen: ein verblasstes Element MIT eigenem Hintergrund ist `UNDECIDED`, weil die Gruppe als Einheit komponiert wird |
| H147 | **OFFEN, gemessen** (TSK-0117 Nacharbeit 1, DEC-0064) | welche Datums-Schreibweisen ein `MST` annimmt, entscheidet der Interpreter: `backlog_types.normalised_date` ist `date.fromisoformat`, und die liest `20261001` erst ab 3.11 — dieselbe Erfassung wird auf einer Maschine angenommen und auf einer anderen verweigert. Am Piloten gemessen (3.13): `2026-10-01` und `20261001` angenommen, beide gespeichert als `2026-10-01`; `Oktober`, `2026-13-01`, `2026-10-01T00:00`, `''` und `None` verweigert. Begrenzt durch: die WIRKUNG ist weg — was angenommen wird, wird normiert gespeichert, also trägt ein Tag genau eine Schreibweise und jede Sortierung nach `due` stimmt; die Verweigerung nennt die Form, die überall gilt. NICHT begrenzt: dass die Annahme selbst versionsabhängig ist |
| H148 | **OFFEN, gemessen, bewusst nicht geschlossen** (TSK-0117 Nacharbeit 1, DEC-0062) | eine deklarierte Naht darf breiter sein als das, was zwei Aufträge wirklich teilen. `kernel.scopes.owns_anything_outside` verweigert nur den Totalfall — eine Naht, die einem der beiden Aufträge KEINE eigene Ownership lässt. Mit `check-scopes` als Prozess gemessen: `**` auf beiden → rc 2 („NOT A SEAM … owning nothing of its own“), `docs/**` bei zwei Aufträgen, die nur `docs/**` besitzen → rc 2, `team-kits/**` bei Aufträgen mit eigenem Rest → **rc 0**, die echte Naht `team-kits/*/VERSION` → rc 0. Begrenzt durch: beide Aufträge müssen sie deklarieren, sie ist mit dem Arbeitsauftrag eingefroren, und jede zugedeckte Zeile wird einzeln gedruckt. NICHT geschlossen, weil die naheliegende Regel („nicht mehr als die tatsächliche Schnittmenge“) die legitime Glob-Naht `team-kits/*/VERSION` verbieten würde. ZWEITE Restklasse, gemessen: `pair_seam` schneidet Zeichenketten, `_matches` vergleicht Dateimengen — `docs/` und `docs/**` sind demselben Prädikat dieselbe Menge und der Naht zwei Nahtangaben, also rc 2 mit der gewöhnlichen OVERLAP-Meldung statt eines Hinweises auf die Schreibweise. Fail-closed, kein Loch — eine schlechtere Auskunft |
| H150 | **GESCHLOSSEN, mit benannter Über-Verweigerung** (Merge-Prüfer TSK-0120, N1; Altbestand, auch an `e45c0ca`) | ein Verzeichniswechsel, den der Leser nicht AUSRECHNEN kann und der die Shell zu einem Fach von Rang zurückbringt, ließ die Fege-Basis harmlos stehen: `pushd outbox > /dev/null ; popd ; rm -rf .` fegte die Projektwurzel bei **rc 0**, während `rm -rf .` allein rc 2 ist — gemessen über jeden auf `Bash` registrierten Office-Haken als Prozess, an `e45c0ca` ebenso wie am gemergten Baum. `_filing.directory_change` meldet `popd` als „nicht berechenbar“ und gibt kein Ziel heraus, also gab es nichts, was die Position hätte bewegen können. Geschlossen mit derselben Mechanik wie `H144`: eine unberechenbare Änderung macht die Position UNBEKANNT, und die Projektwurzel — die jedes Fach enthält — tritt als Kandidat neben die alte. Begrenzt durch: der Preis, `cd outbox ; cd $X ; rm -rf .` und `cd outbox ; cd ; rm -rf .` sind rc 2, obwohl diese Shell wirklich außerhalb jedes Fachs stehen kann |
| H1, H4, H5, H6, H8, H17, H20, H24, H26, H27, H28, H29, H30, H31, H33, H35 | **GESCHLOSSEN** | — |

**H128 und H149 sind reserviert und unbenutzt.** Generation 3 hat je Strom Nummern vorab
vergeben, damit fünf gleichzeitig laufende Ströme sich keine geben können; Strom A brauchte
seine dritte (H128) und seine vierte (H149) nicht. Sie werden nicht nachbelegt: eine Nummer,
die zweimal etwas anderes bedeutet, macht jeden älteren Zeiger auf sie falsch. Die Lücke ist
die Buchführung dieser Reservierung und kein verlorener Eintrag.

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

**Und seit TSK-0098 reicht dieselbe Kette bis zu einer Freigabe, die niemand erteilt hat.** Der
Freigabe-Haken der Kits ist ein Programm; ein Skript, das ihn mit einer selbst gebauten Nutzlast
startet, prägt. Gemessen 2026-08-31 (`residues.py`, echte Shell, echter Kernel, Wegwerf-Projekt):
`python probe_start.py` — **rc 0 bei Gate 1 für beide Aufrufer** —, danach steht das Item auf
`APPROVED` mit `approval_ref: APR-0001`. H80 hat jede **Befehlszeilen**-Form dieser Kette
geschlossen; diese hier bleibt, und sie bleibt aus demselben Grund wie eh und je: es ist der Weg,
auf dem dieses Repo seine eigenen Haken MISST (`tools/test_hooks.py::run_hook_process`), und die
Kits tragen ihn genauso. Die Klasse ist damit teurer als der Eintrag bis dahin sagte — nicht mehr
nur „ein Skript schreibt eine geschützte Datei", sondern „ein Skript stellt eine Freigabe aus".

**Und sie hebt Gate 3 mit auf — gemessen, nicht abgeleitet (TSK-0008, R-d).** Im selben Lauf:
`git commit -m wip` **rc 2** (Gate 3 verweigert, kein Beweismittel) → ein Skript im freien Bereich,
das `git commit` startet → `python scratch/c.py` **rc 0 bei Gate 1 UND rc 0 bei Gate 3** → `HEAD`
bewegt sich real von `7818d4b7` auf `dc6f500d`. Gate 3 fragt `Invocation.runs("commit")` an den
**Text** der Zeile, und in dieser Zeile steht kein `git`. Die Interpreter-Ausnahme ist damit nicht
nur ein Loch in Gate 1, sondern der Weg an **beiden** Gates vorbei.

**Und seit TSK-0102 hebt sie die BUCHUNGS-Schicht mit auf.** Die Vier-Augen-Buchung (FR-0065)
urteilt über Zeilen, die noch nicht in `HEAD` stehen, und ihre Attestierungen liegen in einem
Verzeichnis, in das keine direkte Schreibweise reicht — beides ruht auf derselben Interpreter-
Ausnahme wie Gate 3 oben. Ein Skript trägt eine ungelesene Zeile nach `HEAD` (dauerhaft ausgenommen)
und prägt außerdem den zweiten „Lauf", den die Schicht zählt. Beide Ketten mit ihren Zahlen: `H99`.

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

**Der Ausloeser ist NICHT auf diese Schreibweise beschraenkt, und die zweite gemessene Form ist
alltaeglicher (TSK-0098, Pruefbefund):** ein Ziel, das es noch nicht gibt. `cd "noch-nicht-da" &&
ls` verlor die Position ebenso, weil der Leser das Betreten selbst fragt und ein Verzeichnis ohne
Existenz nicht betretbar ist. Dass ein LESENDES Verb dahinter trotzdem verweigert wurde, kam
allerdings nicht von der Bewegung, sondern von der ersten Fassung der START-Position: sie las das
VERB jeder Stufe als Datei im Arbeitsverzeichnis, und aus einer unbekannten Position ist jedes
trennzeichenlose Verb unplatzierbar. Seit `_harness._verb_as_a_file` steht der Verb-Platz nur noch
einem Wort MIT Trennzeichen offen, und die Zeile ist wieder rc 0 (gemessen 2026-08-31, beide
Aufrufer, beide Shells;
`test_gate1_does_not_read_a_bare_verb_as_a_file_in_the_working_directory` haelt es). Was bleibt,
ist die eigentliche Aussage dieses Eintrags: ein relativer SCHREIB- oder START-Kandidat hinter
einer solchen Bewegung wird verweigert.

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

### H27 — Die Kindschaft eines Verzeichnisverbs hatte eine Schreibweise — GESCHLOSSEN (TSK-0013, duale Hälfte TSK-0098)

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

**Die DUALE Hälfte, gefunden vom Prüfer und geschlossen am 2026-08-31 (TSK-0098).** Dieser
Eintrag schließt den Schreibzugriff AUSSERHALB der Klammer -- die Shell ist nie gegangen, also
darf die Basis nicht mitgehen. Was dabei offen blieb, ist der Schreibzugriff INNERHALB derselben
Klammer: dort ist die Bewegung für jeden Befehl der Gruppe echt, und dieser Leser urteilte
weiter von der unbewegten Elternbasis aus. Gemessen, jede Zeile flach **rc 2** und in Klammern
**rc 0**, und zwar für **jeden** Aufrufer:
`(cd .claude/hooks && rm gate_todo_items.py)`, `(cd .claude/hooks && sed -i "s/a/b/"
gate_todo_items.py)`, `(cd project_memory && sed -i "s/a/b/" bugs/active/BUG-nnnn.yaml)` und
`(cd team-kits && sed -i "s/a/b/" kernel/state.py)` (dieses für den Lead). Gegen `HEAD` derselbe
Befund -- die Hälfte war seit dem Bau der Shell-Hälfte offen und ist von TSK-0098 nicht
eingeführt worden. Die START-Richtung derselben Ursache steht in **H80**; sie hat geprägt.

**Gebaut ist eine SCOPE-Verwaltung und keine Verweigerung:** `WorkingDirectory.follow` geht in die
Gruppe mit (`_open_scope`), und `settle` bringt die Basis zurück, sobald eine spätere Pipeline
auf kleinerer Tiefe steht. Der kürzere Fix -- die Position verlieren, wie bei einer Bewegung in
einer fremden Shell -- hätte `(cd tools && python bump_kit_version.py)` verweigert, also eine
Lieferzeile dieses Repos. Zwei Leser mussten dafür mit: `_walk` bekommt die Pipeline **ab dem
Verb** (mit der Klammer davor las es `cd` selbst als Ziel und gab die Position auf), und
`_the_move_in_a_later_stage` findet ein `cd`, das in der empfangenden Stufe einer Pipe steht
(`true | (cd <hooks> && python …)`). Rot ohne den Fix:
`test_gate1_refuses_maintaining_a_hook_file_from_a_shell` und die Subshell-Zellen von
`test_gate1_refuses_starting_a_hook_from_every_caller`; die Gegenrichtung hält
`test_gate1_comes_back_out_of_a_group_it_walked_into`.

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

**Nachtrag TSK-0098:** die Tilde ist nicht mehr die einzige Konstruktion, die ein Wort
unplatzierbar macht. `_harness._UNRESOLVED` gibt dieselbe Antwort für ein Wort, das eine Shell aus
einer Expansion oder aus dem Dateisystem erst baut — und einige der Zeichen, die dieser Eintrag als
harmlose Vorsätze vor einer Tilde führt (`*`, `[`, `{`, `?`), sind genau jene. Ein Wort wie
`*~/team-kits/kernel/state.py` wird darum jetzt verweigert, obwohl die Tilde darin nicht am Anfang
steht; `test_gate1_answers_for_a_tilde_that_does_not_start_its_word` fragt beide Leser statt nur
diesen einen. Wo bash das Muster auf nichts abbildet und das Wort literal lässt, ist das eine
Über-Verweigerung — und die fail-closed-Richtung, aus demselben Grund wie hier.

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
gemünzt wird die über den PostToolUse-Haken der Kits auf der AskUserQuestion-Antwort. **Bis
TSK-0098 führte die Registrierung dieses Repos nur die eigenen Gates**, und die gedruckte Abhilfe
der Verweigerung („Frage weiterreichen, die Antwort münzt") hatte hier keinen Zuhörer; seit
TSK-0098 steht der Haken der Kits auf beiden AskUserQuestion-Ereignissen — wirksam ab dem nächsten
Sitzungsstart, siehe den Absatz am Ende dieses Eintrags.

**Was dieser Absatz bis 2026-08-30 zusätzlich behauptete und was daran falsch war (TSK-0097):**
er endete mit „`VERIFIED` ist damit für jeden Bug unerreichbar, solange kein Münzweg existiert".
Der erste Teil stimmt für den ehrlichen Weg, der zweite ist widerlegt. Ein Münzweg existiert und
lief in dieser Runde durch: `request-approval` ist reiner Kernel und schreibt die offene Anfrage in
jedem Projekt, der Münz-Code steht im Klartext in `approvals/pending/<id>.yaml`, und der
ausgelieferte Haken lässt sich mit einer selbst gebauten Nutzlast von Hand fahren. Die Lücke ist
also nicht „es fehlt ein Weg", sondern „der vorhandene Weg bindet an keine Nutzerantwort" — die
Angriffshälfte steht als **H80**, dieser Eintrag behält nur die Buchführungshälfte. Der Kernel
sagt die Buchführungshälfte seit TSK-0097 selbst: `approvals._unwired_mint_note` hängt an genau
diese Verweigerung den Satz, dass hier keine Antwort des Nutzers münzt, gelesen aus der
Registrierung (`report.approval_mint_is_wired`).

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

**Urteil: kein Angriffsloch, eine Erreichbarkeitslücke der Buchführung — für `BUG` seit TSK-0098
aufgelöst (Registrierung, wirksam nach Neustart), für `TSK` weiter benannte Ausnahme (DEC-0041).**
**Warum es bis dahin nicht geschlossen wurde:** der Münzweg wäre eine Registrierung in
`.claude/settings.json` oder ein Kernel-Münzkommando in `team-kits/**` — beides dem
**Sitzungsagenten** verwehrt (Gate 1 führt beide Bereiche als session-beschränkt; ein
Umsetzer-Subagent darf dort schreiben, der Änderungskreis existiert genau dafür, und genau so ist
es in TSK-0098 geschehen). Es fehlte also keine Schreibbarkeit, sondern eine Runde mit eigener
Sicherheitsabwägung — denn ein Kommando, das ohne Nutzerantwort münzt, wäre genau das selbst
ausgestellte Ja, das die Verweigerung wörtlich verbietet. Gebaut wurde deshalb **kein** solches
Kommando, sondern die Registrierung, die die Antwort des Nutzers zum einzigen Münzweg macht.
**Was für die `TSK`-Hälfte stattdessen begrenzt:** DEC-0041 trägt die Bedeutung von `CANCELLED`,
und die Bugliste bleibt ehrlich sichtbar statt leergelogen.

**Was TSK-0098 daran aufgelöst hat, und was nicht.** Der Auslöser dieses Absatzes ist eingetreten:
`.claude/settings.json` registriert den Freigabe-Haken der Kits auf `PreToolUse` und `PostToolUse`
von `AskUserQuestion`, `report.approval_mint_is_wired` meldet für dieses Repo **`True`** (gemessen
2026-08-31 gegen die geschriebene Registrierung), und der Zusatzsatz an der Verweigerung entfällt
damit von selbst. Zwei Einschränkungen, beide gemessen und keine davon kosmetisch:

* **Der Leser ist der Datei voraus.** `approval_mint_is_wired` liest die REGISTRIERUNG, der
  Provider bindet Haken beim **Sitzungsstart**. Solange der Nutzer die Sitzung nicht neu gestartet
  hat, sagt der Leser `True`, während kein Prozess die Antwort liest. Was den Unterschied auflöst,
  ist ein Neustart und nichts sonst.
* **Die `BUG`-Hälfte hängt ohnehin nicht an der Freigabe allein.** `VERIFIED` verlangt zusätzlich
  einen `test`-Nachweis mit der Bug-Id (`state.CONFIRMING_EVIDENCE`); die Freigabe öffnet nur die
  Kante `TRIAGED → APPROVED`.

Die **`TSK`-Hälfte bleibt offen und unverändert**: `DONE`/`VALIDATED` liegen hinter einem echten
Dispatch-Lease, das dieses Repo bewusst nicht fährt, und dafür gilt DEC-0041 weiter. Der frühere
Wortlaut dieses Absatzes nannte als Auslöser „ein Münzweg (Kit-Installation oder
Kernel-Kommando)"; das war zu weit gefasst und hat den unehrlichen Weg mitgemeint, der längst
existierte — der ist seit TSK-0098 zu, siehe H80.

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
2841, 2858, 2930); mit dem H70-Eintrag 2026-08-24 **einer** mehr, in `tools/test_hooks_v2.py`
(Zeile 10505), ebenfalls von Hand aufgelöst — Bestand damit **elf**, alle aufgelöst, weiter
Handarbeit. Dieselbe Klasse wie
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
starten.** Mechanismus: die autouse-Fixture der Suite (`test_gates.py:132-136`; Stand TSK-0090 —
eine Import-Zeile jener Runde hat den Block um eins verschoben) arbitriert beim
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

### H46 — `>&datei` ist eine bytehaltende Umleitung, die Gate 1 nicht als Schreibzugriff sah — GESCHLOSSEN (TSK-0070, über die Kit-Leih-Mechanik mitgeheilt)

**Mechanismus:** Der Umleitungs-Erkenner von Gate 1 (`.claude/hooks/_harness`, dieselbe
Regex-Klasse `_REDIRECT_RX` wie im Kit-Gate) liest hinter `>` nur `>`, `|` oder Zeilenende. Die
Schreibweise `>&WORT` ist im Bash aber genau dann **keine** Deskriptor-Verdopplung, sondern die
csh-Form von `&>datei` (beide Ströme in die Datei), wenn `WORT` **keine** Zahl und nicht `-` ist.
Der Lexer liefert `>&` als ein Token, das Muster verwirft es, das Folgewort wird nie als Ziel
verbucht — und damit läuft **jede** Pfadregel dieses Gates ins Leere, nicht nur eine.

**Kette (Lead gemessen 2026-08-16, als Gate-Entscheidung über echten Prozess, NICHTS
ausgeführt):**
```
echo x >& project_memory/decisions/active/DEC-9999.yaml   → rc 0  (durchgelassen)
echo x >  project_memory/decisions/active/DEC-9999.yaml   → rc 2  (verweigert)
```
Der Prüfer der TSK-0070-Runde hat dieselbe Schreibweise gegen `.claude/hooks/gate_git.py`,
`.claude/settings.json` und `team-kits/kernel/state.py` als rc 0 gemessen (ebenfalls nur die
Entscheidung, im Sandkasten mit echtem Bash als Datenverlust belegt: `gate_git.py` von 23 436
auf 6 Byte). Der Sitzungsagent kann damit kanonischen Zustand, die Durchsetzungsschicht und
den Kit-Hash-Eingang an Gate 1 vorbei überschreiben — die gesamte Eigenschaft, auf der dieses
Repo steht.

**Wo der Fix saß — gemessen an der Leih-Mechanik, nicht angenommen:** Gate 1 hat **keine
eigene** Umleitungs-Regex. `.claude/hooks/_harness.py:982-984` (`_from_kit("gate_write_scope")`)
leiht die Kommandozeilen-Lesung aus dem **Kit-Modul** `team-kits/<kit>/hooks/gate_write_scope.py`
— genau, damit keine zweite Regex driftet (H15). Die Reparaturstelle war also
`gate_write_scope._REDIRECT_RX` in `team-kits/`, im `allowed_scope` des Umsetzers; Hooks lesen
ihre Dateien bei jedem Aufruf frisch.

**Der Fix, als Eigenschaft und nicht als Aufzählung:** `_REDIRECT_RX` um `[0-9]*>&` erweitert
(`gate_write_scope.py:611`), ein `_is_descriptor`-Leser (`:614`) und **ein** Ziel-Leser
`_output_redirect_targets` (`:627`), durch den alle drei Aufrufstellen gehen; das Folgewort wird
nur verworfen, wenn es ein Deskriptor ist (`^[0-9]+$` oder `-`). Der korrigierte Test
`test_hooks_v2.test_a_descriptor_duplication_is_a_redirect_but_a_file_after_gt_amp_is_a_write`
misst den Datei-Fall.

**Urteil: GESCHLOSSEN (TSK-0070), am eigenen Gate NACHGEMESSEN.** Der B1-Fix in `team-kits/` hat
das Repo-Gate über die Leih-Mechanik **mitgeheilt**, und das ist nicht mehr Erwartung, sondern
gemessen (Lead und Prüfer unabhängig, echter Prozess gegen `.claude/hooks/gate_lead_write_scope.py`):
```
echo x >& project_memory/decisions/active/DEC-9999.yaml   rc 2   (vorher rc 0)
echo x >& .claude/hooks/gate_lead_write_scope.py          rc 2
echo x >& team-kits/kernel/state.py                       rc 2
echo x >&2                                                rc 0   (Deskriptor-Dup, korrekt frei)
```
Kein Schritt außerhalb der Sitzung war nötig — die geteilte Regex trägt beide Kopien. Was diese
Runde NICHT mitgeheilt hat, ist die **Variablen-Variante derselben Klasse** am Repo-Gate: siehe
**H47**.

### H47 — Das Repo-Gate leiht den Ziel-Leser des Kits, aber nicht dessen Zeilen-Zuweisungskarte: `F=…; > $F` schreibt kanonischen Zustand an Gate 1 vorbei — OFFEN (neu, TSK-0070)

**Mechanismus:** TSK-0070 hat kit-seitig zwei Dinge gebaut — den `>&`-Ziel-Leser (B1, den Gate 1
über `_from_kit` leiht, siehe H46) **und** die Variablen-Auflösung (B2: `_line_assignments`
baut die `NAME=value`-Karte der ganzen Zeile, `_resolve` substituiert `$NAME` vor dem Urteil).
Die Auflösung sitzt aber im **Regel-5-Leadprüfer des Kits**, nicht im geteilten Ziel-Leser. Gate 1
hat seinen **eigenen** `_subjects`-Weg und baut **keine** Zuweisungskarte — also leiht es B1 mit,
B2 nicht.

**Kette (Prüfer der TSK-0070-Runde, 2026-08-16, echter Prozess gegen
`.claude/hooks/gate_lead_write_scope.py`, NICHTS ausgeführt):**
```
F=team-kits/kernel/state.py; echo x > $F   → rc 0  (durchgelassen)
echo x > team-kits/kernel/state.py         → rc 2  (verweigert)
```
Dieselbe Klasse wie H46: eine in einer Sitzung durchlaufende Schreibbahn des Sitzungsagenten auf
kanonischen Zustand / Durchsetzungsschicht / Kit-Hash-Eingang, hier über ein Umleitungsziel in
einer Variablen, die dieselbe Zeile zuweist. Am **Kit-Gate** ist diese Form seit TSK-0070
verweigert (B2 gemessen); nur die **Repo-Kopie** trägt sie noch.

**Zwei Schließrichtungen, und welche greift, ist zu messen:** (a) die Auflösung wandert in den
**geteilten** Ziel-Leser, den Gate 1 ohnehin leiht (`_output_redirect_targets` bekäme die
`_line_assignments`-Karte als Eingabe) — dann heilt ein **Kit-Fix** das Repo-Gate mit, wie bei
H46, und die Reparaturstelle liegt im `allowed_scope` eines Umsetzers; (b) Gate 1 baut die
Zuweisungskarte in `_harness` selbst — das liegt in `.claude/hooks/`, also außerhalb jeder
Sitzung, und wäre der Ausweg „von außen". Welche der beiden nötig ist, hängt daran, ob sich die
Auflösung sauber in den geteilten Leser ziehen lässt, ohne den Kit-Gate-Pfad zu verbiegen —
ungemessen.

**Urteil: OFFEN, blockierend, mit benannter Zwischenbegrenzung.** Die Kette läuft in einer
Sitzung durch, es gibt keinen dritten Zustand. Die Begrenzung bis zum Fix: die Lücke ist
**vorbestehend** (das Kit hatte an HEAD gar keine Variablen-Auflösung, also hatte das Repo-Gate
sie nie — TSK-0070 hat sie kit-seitig gebaut und dabei den Unterschied sichtbar gemacht), und die
Rollentrennung hält sie sozial (der Sitzungsagent schreibt Zustand über den Kernel, nicht über
eine Umleitung). Der Nutzer entscheidet nach der Messung von Richtung (a): fällt sie aus, ist es
ein Fix von außerhalb der Sitzung wie H46 in seiner ursprünglichen Form.

### H48 — Ein offener Lesehandle friert das Board für die Dauer der Sitzung ein; das einzige aktive Signal ist eine im Hook-Pfad praktisch ungelesene stderr-Zeile — OFFEN als bewusster Tausch (neu, TSK-0071)

**Mechanismus:** Seit TSK-0071 rendert der Kernel bei jeder Index-Regeneration auch
`generated/board.html` (`kernel/state.py`, `_write_board`). Der Schreibweg ist atomar
(`os.replace`), und auf Windows scheitert `os.replace` gegen eine Datei, die irgendein Prozess
auch nur **lesend** offen hält. Der Fail-Soft derselben Runde fängt das ab: der
Zustandsschreibvorgang **gelingt**, die Seite behält Inhalt und Zeitstempel, die Warnung geht
auf stderr. Genau dieser Fang erzeugt die neue Klasse: solange der Handle gehalten wird, ist die
Seite eingefroren — und eine nicht geschriebene Seite kann ihr eigenes Scheitern nicht anzeigen,
nur ihren stehen gebliebenen Zeitstempel.

**Kette (Prüfer der TSK-0071-Runde, 2026-08-16/17, echter Kernel gegen eine Store-Kopie
außerhalb des Repos):**
```
Lesehandle auf board.html halten; capture →  ok (PR-0002 captured)
  page kept its old stamp: True    index current: True
  Warnung wörtlich auf stderr
```
Vorher (ohne Fail-Soft) war dieselbe Konstellation schlimmer: `PermissionError [WinError 5]`
ließ **jeden** Zustandsschreibvorgang scheitern — der Tausch dieser Runde ist also
Kernel-läuft-weiter gegen Seite-kann-einfrieren, und er ist absichtlich so herum gewählt.
Gemessen mit einem gewöhnlichen Lesehandle; ein echter Browser gegen eine `file://`-Seite ist
ungemessen.

**Warum die stderr-Zeile kein verlässliches Signal ist:** In den Kit-Projekten läuft der
Renderer auch in Hook-Unterprozessen (`gate_approval` beim Mint, `gate_dispatch` beim
Spawn-Ausgang); `_gate.py` leitet stderr nicht um, und die Registrierungen dieser Einträge
nennen kein `timeout`. Die Zeile existiert, aber praktisch liest sie dort niemand.

**Urteil: OFFEN, nicht blockierend — bewusster Tausch mit benannter Begrenzung.** Keine
Angriffskette auf Zustand oder Durchsetzung: Zustand, Index und alle Gates arbeiten korrekt
weiter; eingefroren ist ausschließlich die Anzeige. Die Begrenzung: der Zeitstempel auf der
Seite ist die Kontrolle (die Seitenfußnote sagt das seit dieser Runde ausdrücklich), und die
bedingte Frischezusage steht an allen fünf Prosastellen. Ein aktives Signal im Sitzungsbrief
(„Board älter als Index") wäre die Schließrichtung, wenn sich die Klasse im Alltag zeigt.

### H49 — Die zweite Vertragsverletzung eines Subagenten läuft ungebremst durch (neu, TSK-0075)

**Mechanismus:** `gate_subagent_output` blockiert einen Spezialisten, der ohne seinen
Ausgabeblock stoppt. Der Provider setzt auf der dadurch ausgelösten Fortsetzung
`stop_hook_active`, und der Hook ehrt dieses Flag: er beendet mit 0, statt erneut zu blockieren.
Wäre es anders, liefe der Subagent in eine Endlosschleife, denn das Flag steht auf jeder
weiteren Fortsetzung ebenfalls. Damit ist genau die **zweite** aufeinanderfolgende Verletzung
ungeblockt — der PM baut dann doch auf Prosa.

**Kette (gemessen 2026-08-17, echter Hook-Prozess, Projekt außerhalb des Repos,
`docs/reviews/2026-08-17-tsk0075-measurements.md`, Abschnitt 1):** `SubagentStop` mit
`stop_hook_active: true` und der Nachricht `all done!` → **rc 0**, Protokoll
`gave_up — backend-developer: giving up with summary still missing`. In Pilot 3 wurde die Kette
nicht durchlaufen: alle 8 gemessenen Fälle waren gelieferte Wiederholungen (B13).

**Urteil: offen, nicht schließbar mit den Mitteln dieses Ereignisses.** Was stattdessen begrenzt:
(a) es braucht **zwei** Verletzungen hintereinander, die erste wird blockiert und mit einer
Anweisung beantwortet, die nur den Ausgabeblock verlangt; (b) der Durchlass ist seit TSK-0075
**zustandsgenau protokolliert** — `gave_up` heißt jetzt wirklich aufgegeben, `retry_delivered`
heißt, die Sperre hat gewirkt —, sodass die Retro des PM den Fall zählen kann statt ihn im
Rauschen von acht Fehlmeldungen zu verlieren; (c) ein Zähler pro Subagentenlauf wäre
beschreibbarer Zustand, der eine Durchsetzungsfrage entscheidet, und ist deshalb bewusst nicht
gebaut. Die `ENFORCEMENT.md`-Zeile aller drei Kits nennt den Durchlass seit derselben Runde.

### H50 — Ein gebundenes Kind ohne `SubagentStop` ist nach dem TTL-Sweep unsichtbar — OFFEN als bewusster Tausch (neu, TSK-0080)

**Mechanismus:** Der Untätigkeits-Melder (`kernel.dispatch.idle_dispatches`) urteilt nur aus
positiven Datensätzen: dem vermerkten Kind-Ende (`SubagentStop`) oder einer vorliegenden Lease,
die nie ein Kind gebunden hat und deren Fenster ablief. Stirbt ein **gebundenes** Kind, ohne dass
der Provider je ein `SubagentStop` liefert, existiert kein Datensatz, der es von einem
arbeitenden unterscheidet — und nach `sweep_expired_leases` ist auch die Lease weg. Von da an
meldet nichts mehr.

**Kette (gemessen 2026-08-22, Prüfer Runde 2, echte Hook-Prozesse, Projekt außerhalb des
Repos):** gebundenes Kind, nie ein `SubagentStop` → `Stop` nach der TTL **rc 0** →
`sweep_expired_leases` räumt die Lease → Status `IN_PROGRESS`, Lease weg → jeder weitere `Stop`
**rc 0**, `idle_dispatches()` leer. Das ist die BUG-0042-Sackgasse; die Zwischenfassung dieser
Runde fing sie nach einer TTL — und kostete dafür einen gemessenen Fehlalarm auf ein
**laufendes** Kind, dessen Remedy (`FAILED`) den Lauf unbuchbar machte (`task_for_agent` → None,
`submit_result` verweigert).

**Urteil: OFFEN als bewusster Tausch.** Melden ohne Datensatz heißt raten, und die geratene
Meldung hat nachweislich einen lebenden Lauf beendet. Was an die Stelle des Schutzes tritt:
`sweep_orphaned_dispatches` beim nächsten Sitzungsstart (DEC-0044) stellt die Waise ehrlich auf
`FAILED` (gemessen, Prüfer proj-h50c) — **innerhalb der laufenden Sitzung deckt nichts**; die
Verfassungspflicht des Absatzes greift erst auf einen Befund, und dieser Fall erzeugt keinen.
Schließrichtung, falls die Klasse im Alltag auftritt: ein Lebenszeichen-Kanal
des Providers (Prozess-Handle oder Heartbeat), den dieses Repo heute nicht hat.

### H51 — Nach der einen Verweigerung schweigt der Melder für denselben Befund — offen (neu, TSK-0080)

**Mechanismus:** `gate_dispatch` verweigert das Zugende höchstens **einmal je Befund**
(`mark_idle_reported` vergleicht die gespeicherte Begründung; bei `stop_hook_active` hält es
still) — ein verweigerter Stop wird vom Provider mit Weitermachen beantwortet, ohne die Schranke
wäre es eine Schleife. Ein Lead, der die Verweigerung liest und trotzdem weiter wartet, wird
nicht erneut angehalten.

**Kette (gemessen 2026-08-22, Umsetzer und Prüfer unabhängig):** Stop #1 rc 2 mit Befund →
Stop #2 rc 0, stderr leer → fünf weitere Zugenden rc 0, Task bleibt `IN_PROGRESS`. Die
Audit-Zeile jedes weiteren Stops läuft, erreicht aber nach dem repo-eigenen Messwert
(`tools/provider_observations.json`, `hook_output_channels`: exit-0-stderr) weder Nutzer noch
Modell.

**Urteil: offen, nicht schließbar ohne Schleifenrisiko.** Was stattdessen begrenzt: der Befund
steht als `idle_reported` dauerhaft im Item und auf der Board-Karte, und der Verfassungstext
trägt die Pflicht, ihm nachzugehen.

### H52 — Ein Zombie-Dispatch hält rollengleiche id-lose Zuordnungen dauerhaft still — offen (neu, TSK-0080)

**Mechanismus:** Ein `SubagentStop` ohne `agent_id` wird nur zugeordnet, wenn **genau ein**
Dispatch der Rolle als Eigentümer in Frage kommt (`_dispatches_a_stop_could_belong_to`;
gebundene, ungebundene und fristüberschrittene zählen alle mit — der Ausschluss Abgelaufener
öffnete die gemessene spiegelbildliche Fehlzuordnung auf den frischen Dispatch). Ein gebundenes
Kind, das nie stoppt (H50-Fall), bleibt darum für immer möglicher Eigentümer: jede spätere
id-lose Meldung derselben Rolle ist mehrdeutig und wird verweigert — als exit-0-stderr, also
faktisch nur eine Audit-Zeile.

**Kette (gemessen 2026-08-22, Prüfer Runde 2):** Zombie-Dispatch + zwei Folgerunden mit frischen
gleichrolligen Dispatches → `attributed=[]` in beiden Runden, Stop rc 0; fremde Rolle
unbetroffen.

**Urteil: offen, nicht schließbar ohne Provider-Schlüssel** (dieselbe Plattformgrenze wie
`bind_agent_by_role`): Verweigern statt Raten ist die Richtung, die keinen laufenden Lauf trifft.
Begrenzung: der repo-eigene Messwert (`docs/reviews/evidence/2026-07-24-spike-payloads.md`) sagt,
dass `SubagentStop` die Id trägt — der id-lose Zweig ist der Ausnahmefall —, und die Verfassung
verlangt gleichrollige Aufgaben sequenziell.

### H53 — Die Lebensdauer von `stop_hook_active` ist ungemessen — offen (neu, TSK-0080)

**Mechanismus:** Der Melder hält still, wenn der Provider den Stop als bereits blockiert
markiert. Ob dieser Schlüssel nur die unmittelbar ausgelöste Fortsetzung trägt oder länger
steht, ist hier nicht gemessen (`provider_observations.json` führt ihn nicht). Bliebe er
sitzungslang stehen, schwiege der Melder für **alle** weiteren Befunde derselben Sitzung.

**Kette (gemessen 2026-08-22):** gemessen ist nur das Hook-Verhalten — Stop mit
`stop_hook_active: true` → rc 0. Die Provider-Seite braucht eine echte Sitzung.

**Urteil: offen, Messung gehört zum Live-Lauf** (BUG-0058 AC-2). Die Fehlrichtung ist stumm, nie
schleifend, und kein ausgelieferter Text behauptet mehr als „at most once per finding" — die
Zusage, die auch beim klebrigen Schlüssel wahr bleibt.

### H54 — Ein ungebunden laufendes Kind wird als „nie verfolgt" gemeldet — offen, nicht blockierend (neu, TSK-0080)

**Mechanismus:** Der Waisen-Term meldet eine Lease, die nie ein Kind gebunden hat und deren
Fenster ablief. Ein Kind, das gestartet, aber nie gebunden wurde (Antwortform ohne `agentId`),
läuft dann noch — und der Befund nennt seinen Dispatch trotzdem, mit dem Satz „nothing here was
ever tracking a run on it".

**Kette (gemessen 2026-08-22, Prüfer Runde 2):** ungebunden laufendes Kind, Fenster abgelaufen →
Stop **rc 2** mit genau diesem Wortlaut.

**Urteil: offen, nicht blockierend — die Meldung ist gewollt und datensatz-wahr** (verfolgt hat
den Lauf wirklich nichts). Begrenzung des Schadens: Gate-Schicht 3 verweigert einem ungebundenen
Kind ohnehin jeden Schreibzugriff; es konnte nichts liefern, das durch ein `FAILED` verloren
ginge. Die Verfassungen sagen die Einschränkung seit dieser Runde ausdrücklich („A bound child
that outlived its lease is none of those and is not named").

### H55 — Die Alt-Bestand-Brücke läuft ohne gemintete Freigabe, und ein Subagent erreicht sie — offen (neu, TSK-0081)

**Mechanismus:** Im Alt-Bestand (bis Kit 2026.08.14-9) existiert die Freigabeart `kit_update`
nicht — es gibt nichts zu minten, und kein Hook dort kann erzwingen, dass der PM den Nutzer
fragt. Die Brücke (`~/agents-and-skills/update_kit.py`) liest ihren Aufrufer nicht, weil ihre
Eingabe keine Payload trägt; das Alt-`gate_write_scope` verweigert Subagenten nur die
**ordnenden** Kommandos, und eine Bootstrap-Zeile ist keines.

**Kette (gemessen 2026-08-22, Prüfer, alle acht Alt-Gates als echte Prozesse):** Scaffold-Zeile
→ rc 2 (`gate_write_scope`); Bootstrap-Zeile, auch als SUBAGENT → **rc 0**. Ein Spezialist im
Alt-Projekt kann damit die Durchsetzungsschicht neu installieren, ohne dass jemand gefragt
wurde — vor dieser Runde war derselbe Weg über die Scaffold-Zeile verwehrt.

**Urteil: offen, von innen nicht schließbar** — der Alt-Hooksatz ist fix, und eine
Aufrufer-Prüfung in der Brücke bräuchte eine Payload, die sie nicht bekommt. Was begrenzt,
je gemessen: die Brücke nimmt keine Argumente, prüft Richtung (Downgrade rc 2) und
Staging-Hash (manipuliertes Staging rc 2), legt Backups an, lässt `project_memory`
byte-identisch und **verweigert in jedem gehobenen Projekt** (rc 2 mit dem Freigabe-Weg) —
der ungefragte Lauf kann also nur das tun, was die eine genehmigte Hebung auch getan hätte.

### H56 — Ein abgebrochener Brückenlauf lässt ein gemischtes Bündel stehen — offen, erholbar (neu, TSK-0081)

**Mechanismus:** Die Brücke fährt den Installer des gestagten Kits und nimmt bei einem Kill
nichts zurück; der Scaffold rollt nur zurück, wenn er selbst verweigert.

**Kette (gemessen 2026-08-22, Prüfer):** `taskkill /T` mitten im Kopieren → `kernel_files`
17→22, `kitupdate` schon da, Stempel noch alt, kein Neustart-Marker. Danach: zweiter
Brückenlauf **rc 0**, Hebung vollständig, `project_memory` unversehrt (20 Dateien).

**Urteil: offen, nicht blockierend** — der Zustand ist erholbar und verliert nichts; der
Docstring der Brücke sagt „what a KILLED run leaves is not undone". Schließrichtung, falls je
nötig: Kopieren in ein Temporärverzeichnis mit atomarem Tausch — ein eigener Entwurf.

### H57 — Ein Interpreter-Heredoc ist vor `gate_ledger_valid` unsichtbar (neu, Preis des TSK-0081-Fixes)

**Mechanismus:** `_compat.literal_heredoc_free` entfernt den Körper eines **quotierten**
Heredocs, bevor der Leser urteilt; stehen bleibt nur, was eine **Shell** parst
(`_STDIN_PARSER_RX`). Ein Interpreter (`python`, `perl`), der sein Programm von der
Standardeingabe liest, ist keine Shell — sein Heredoc-Körper verschwindet mitsamt dem
Schreibzugriff darin. Für die Gates, die den Helfer schon nutzten, war das gemessen
verlustfrei; `gate_ledger_valid` übernimmt ihn seit TSK-0081, und dort ist es das nicht.

**Kette (gemessen 2026-08-22, drei Träger, echte Hook-Prozesse):**
`python <<'EOF' … open('scripts/ledger_add.py','w') … EOF`, dasselbe mit `python3` und `perl` —
je HEAD rc 2 → jetzt **rc 0**; das Ziel ist der Validator, den dieses Gate schützt.
Kontrollen: `sh`/`bash -s`/`env bash <<'EOF'` mit echtem `cp` rc 2, unquotiertes `<<EOF` rc 2.

**Urteil: offen, am Helfer nicht schließbar**, ohne dass er entscheidet, welche Programme ihre
Standardeingabe ausführen — für Shells ist das eine geschlossene Menge, für Interpreter nicht
(die H11-Klasse dieses Repos, am Kit-Gate). Was wirklich begrenzt, gemessen (Prüfer,
Schlussschleife): der **Werkzeug**-Schreibzugriff auf den Validator ist für jeden Aufrufer
doppelt verweigert (`guard_harness_selfmod` rc 2; für Subagenten zusätzlich `gate_write_scope`
rc 2) — offen ist genau der Shell-/Interpreter-Weg, und **danach fängt nichts mehr**: die
Commit-Prüfung fährt den Validator, der dann dasteht — ein ersetzter Richter sagt rc 0 auf
einem kaputten Ledger (gemessen, Commit und Push rc 0). Der Rest der Begrenzung ist die
H11-Klasse selbst: die Zeile muss vom Agenten kommen, und der ersetzte Validator steht sichtbar
im Diff des Commits. `_compat.py` benennt den zweiten Leser und seinen Verlust seit dieser
Runde ausdrücklich.

### H58 — `TSK DONE → VALIDATED` fordert keine Evidence — offen als Semantik-Entscheidung (neu, TSK-0082)

**Mechanismus:** `state.CONFIRMING_EVIDENCE = {"BUG": "test"}` — für TSK ist die bestätigende
Kante ungewacht, obwohl Verfassung §4/Phase 9 und die QE-SKILL das Verdikt versprechen.
`transition TSK-nnnn VALIDATED` läuft ohne jede Evidence durch; der Status behauptet
„QA bestätigt", niemand hat gemessen.

**Kette (gemessen 2026-08-23, Umsetzer):** die Kante wurde in DREI Populationen praktisch nie
begangen (V1-Felddaten 422 DONE : 1 VALIDATED; Pilot 3: 11 DONE, 0 VALIDATED; dieses Repo:
81 archivierte TSK, alle CANCELLED). Die Einzeiler-Regel (`CONFIRMING_EVIDENCE["TSK"]`) machte
den V1-Import `("TSK","VALIDATED")` unmöglich (`state.migration_writable_statuses` sagt es
selbst voraus, der Wächter-Test wird rot).

**Urteil: offen — eine Semantik-Entscheidung des Nutzers, keine Reparatur.** Was stattdessen
steht (TSK-0082, beide Richtungen gemessen): `report.accepted_without_a_verdict` warnt je
abgenommenem Task ohne bestandenes Lieferverdikt (Kante abgeleitet über `confirming_edge`,
office über `ROOT_TYPE_BY_KIT` ausgenommen, wo das Verdikt unerfüllbar wäre), und das
Sitzungsstart-Briefing der dev/research-Kits sagt denselben Satz.

### H59 — Nichts treibt ein Projekt in die Phasen 6–9 — offen, die Leere ist jetzt gesagt (neu, TSK-0082)

**Mechanismus:** Die evidence-Schublade hat zwei Forderer, und beide sitzen hinter Stellen, die
ein kleines Projekt nie erreicht: `gate_git` fordert beim MERGE (ein Solo-Projekt auf `main`
merged nie), und die `DONE → VALIDATED`-Kante wird nicht begangen (H58). Kein Gate zwingt den
PM zum QA-Schritt.

**Kette (gemessen, Piloten):** Pilot 3 endete mit 11 DONE-Tasks und 0 Evidence bei laufendem
Produkt; Pilot 4 Hälfte 2 ohne existierendes evidence-Verzeichnis. Die Schublade ist
UNERREICHT, nicht tot (54 Datensätze in diesem Repo; `gate_git`, `report.qa_verdicts` und der
project-auditor lesen sie).

**Urteil: offen.** Begrenzt durch die TSK-0082-Ansage: die Warnung des Validators und das
Sitzungsstart-Briefing machen die Leere sichtbar statt still. Ob die Ansage ein Projekt
wirklich in die QA-Phase bewegt, ist der Messpunkt des Live-Testlaufs.

### H60 — `document_sources` erzwingt nichts — offen, doppelt begrenzt (neu, TSK-0082)

**Mechanismus:** Die neue Ableitung (Interview-Richtungen → `business_profile.document_sources`
→ Deckungsvergleich gegen die Planregeln) hat keinen erzwingenden Leser: kein Gate liest die
Liste, und ein nicht begangenes Interview hinterlässt eine leere Liste, die aussieht wie
„nichts zu melden".

**Kette:** Onboarding füllt die Liste nicht → `filing_coverage_briefing` schweigt → der erste
Vorfall ist wieder ein von `gate_filing` gestopptes Dokument (die Pilot-4-H3-Form).

**Urteil: offen.** Doppelt begrenzt, beides gemessen: `gate_filing` scheitert bei leerem Plan
ohnehin GESCHLOSSEN (das erste Dokument wird verweigert, mit eigener Meldung und dem
`request-approval filing_rule`-Ausweg), und die Deckungslücke einer GEFÜLLTEN Liste wird jedem
office-Sitzungsstart angesagt (echter Hook-Prozess, beide Richtungen, Fixture = der
Hälfte-3-Antwortsatz).

### H61 — Kein Kit-Hook merkt, dass sein Fenster abläuft — offen, Schließrichtung gebaut (neu, TSK-0082)

**Mechanismus:** Weder das ≈600-s-Default-Fenster noch ein registriertes `timeout` wird von
irgendeinem Kit-Hook zur Laufzeit bemerkt — die ganze TSK-0082-Konstruktion ruht darauf, dass
jede Gate-Laufzeit weit unter dem Fenster bleibt. Das ist heute gemessen wahr und wird von
nichts erzwungen: ein Gate, dessen Aufwand mit fremdem Input wächst (die Wrapper-Options-Kurve
in `_compat.py` nennt 65 s bei 26 Wörtern), läuft in genau dieses Fenster, und ein Kill dort
ist ein stiller Durchlass (L9-Messung).

**Kette (gemessen 2026-08-23, beide Rollen, echte Provider-Sitzungen):** Hook ohne `timeout`
schläft 900 s → getötet, der verweigerte Aufruf läuft, die Sitzung meldet Erfolg — nichts im
Hook und nichts in den Kits hat den Ablauf bemerkt oder gemeldet.

**Urteil: offen, mit gebauter Schließrichtung.** Dieses Repo besitzt die Konstruktion bereits:
`.claude/hooks/_harness.py::Deadline` liest die eigene registrierte Frist und verweigert
BEVOR sie abläuft (`_the_budget_is_spent` läuft neben jeder Entscheidung). In die Kits ist sie
nicht übernommen — eine eigene Runde, wenn gewollt. Bis dahin begrenzen die Messwerte
(beobachtete Laufzeiten ≤0,405 s, größte eigene Kindgrenze außer `gate_pipeline` 20 s, beides
≪ 560 s) und der Eigenschaftstest, der die Relation Kindgrenze↔Fenster statisch hält —
Messwerte, keine Laufzeit-Schranken, und die Quellstellen (`_compat`-Konstante,
Beobachtungsdatei `what_follows_for_the_kits`) sagen genau das.

### H62 — Die Köder-Prüfung des Ledger-Gates urteilt segmentweit — offen, Kandidat gemessen und zurückgestellt (neu, TSK-0083)

**Mechanismus:** Seit TSK-0083 stellt `gate_ledger_valid` die Frage „schreibt diese Zeile?" je
Pipeline-**Stufe** (`_stages_beside_the_vouched_runs`), die Köder-Frage aber weiter je
**Segment** (`_DECOY_VALIDATOR_RX` in `_writes_ledger`): nennt die Argument-Prosa eines
verbürgten Laufs einen Pfad, der nur so **aussieht** wie der Validator (`tools/ledger_add.py`),
wird das ganze Segment verweigert, sobald es auch das Ledger nennt.

**Kette (gemessen 2026-08-23, Prüfer und Umsetzer unabhängig, echte Hook-Prozesse):**
`python scripts/ledger_add.py --validate ledger/2026.csv --note "see tools/ledger_add.py"` und
`python scripts/harness.py evidence --summary "see tools/ledger_add.py for ledger/2026.csv"` —
je rc 2; die Kontrolle ohne Ledger-Nennung im Segment rc 0. Der Ein-Zeilen-Kandidat (die
Köder-Prüfung ebenfalls über die verbürgten Stufen stellen) wurde im Klon **angewandt und
vermessen**, nicht geraten: er befreit die beiden Zeilen oben, ließ damals die
nutzersichtbare Über-Verweigerung stehen (`H63`) und nimmt zugleich der Köder-Regel ihre
Reichweite in genau den Stufen, die seit dieser Runde als verbürgt gelten.

**Nachtrag 2026-08-24 (TSK-0083, Runden 3/4):** `H63` ist auf einem anderen Weg geschlossen —
nicht über die Köder-Reichweite, sondern über den Grund der Ausnahme im Validator-Verzeichnis.

**Zweiter Nachtrag 2026-08-24 (Prüfer, TSK-0084): die beiden Belegzeilen oben tragen nicht mehr.**
Beide sind auf dem gelieferten Stand **rc 0** (HEAD rc 2 → jetzt rc 0), mit und ohne
`&& git commit`, bei gültigem wie ungültigem Ledger — die Köder-Frage wird seit Runde 5 je
**Stufe** gestellt, und der Docstring von `_stages_beside_the_vouched_runs` sagt selbst, dass ein
Köderpfad in der Prosa einer verbürgten Stufe Prosa ist. **Ungemessen ist, ob der Mechanismus in
einer anderen Schreibweise überlebt**; nur die Belegzeilen sind nachgemessen. Der Eintrag steht
darum als **veraltet, nicht als geschlossen** — ein Eintrag ohne tragende Kette ist so wenig wert
wie eine Kette ohne Eintrag, und ihn stillschweigend abzuhaken wäre dieselbe Unehrlichkeit in die
andere Richtung. Wer ihn schließen will, misst zuerst den Mechanismus, nicht die zwei Zeilen.

**Urteil: offen, Über-Verweigerung, kein Loch.** Nichts geht verloren — die Zeilen sind
lästig verweigert, nicht still durchgelassen. Eine Lösung, die alle drei Über-Verweigerungen
zusammen behebt, gehört in die Runde von `BUG-0064`, nicht als Nebeneffekt hierher; die
F4-Messtabelle liegt im Abnahmeprotokoll `staging/TSK-0083/`.

### H63 — Das Ledger-Gate verweigert seine eigene beworbene Remedy — GESCHLOSSEN (TSK-0083, `BUG-0064`)

**Geschlossen am 2026-08-24.** Der Wortlaut unten beschreibt den Befund; wie er geschlossen
wurde und was die Schließung gekostet hat, steht direkt darunter.

**Mechanismus:** In `_writes_ledger` läuft die Köder-Prüfung **vor** der
`inside_scripts`-Ausnahme. Ein blankes `ledger_add.py` nach `cd scripts` beginnt nicht mit
`scripts/` und zählt darum als Köder — genau die Aufrufform, die der Kommentar des Gates
selbst „the sanctioned way out of a block" nennt und deren Richtung die Verweigerung
(„fix the ledger rows instead") dem Nutzer empfiehlt.

**Kette (gemessen 2026-08-23, Umsetzer, echter Hook-Prozess, identisch am HEAD — also
vorbestehend, nicht Preis der Runde):**
`cd scripts && python ledger_add.py --validate ../ledger/2026.csv && git commit -m x` → rc 2.
Kontrollen: die kanonische Schreibweise vom Projektstamm
(`python scripts/ledger_add.py --validate ledger/2026.csv`) rc 0; der echte Köder
(`python tools/ledger_add.py …`) rc 2.

**Urteil: GESCHLOSSEN** (2026-08-24, TSK-0083 Runden 3/4) — der Befund und der Weg dorthin
stehen unten, weil die Schließung selbst drei Löcher aufgemacht hat und das die Lehre ist.

**Der Befund damals war: offen, Über-Verweigerung mit eigenem Item.** Ein Büro-Nutzer, der in einer
Ledger-Sperre steckt, kann den beworbenen Ausweg nicht tippen — das ist die
Pilot-3-`BUG-0039`-Klasse (eine Verweigerung, deren Rat nicht begehbar ist), darum trägt sie
`BUG-0064` mit Abnahmekriterien statt nur dieser Zeile.

**Wie geschlossen (2026-08-24, TSK-0083 Runden 3/4):** nicht dadurch, dass die Ausnahme
weiter gefasst wurde, sondern dadurch, dass sie auf ihren **Grund** verengt wurde. Im
Verzeichnis des Validators ist der **blanke Name** die kanonische Datei — `tools/ledger_add.py`
dagegen ist aus jedem Arbeitsverzeichnis eine andere Datei. Befreit wird darum nur ein **Lauf**
des blanken Namens, geprüft mit derselben Konstruktion, die den kanonischen Lauf vom
Projektstamm erkennt (`_canonical_run` mit leerem Verzeichnis), nicht seine bloße **Nennung**.
Gemessen: `cd scripts && python ledger_add.py --validate ../ledger/2026.csv && git commit -m x`
HEAD rc 2 → jetzt rc 0, mit eigenem Test; die kanonische Schreibweise vom Projektstamm bleibt
rc 0, der echte Köder `python tools/ledger_add.py …` bleibt rc 2.

**Was die Schließung gekostet hat, und warum das hier steht:** die erste Fassung dieser
Ausnahme fragte nach der Nennung statt nach dem Lauf und öffnete damit ein Loch, das der Prüfer
bis zum Ende durchgespielt hat — im Validator-Verzeichnis war danach **jede** Operation auf dem
blanken Namen frei, bis hin zu `cd scripts && cp ../evil.py ledger_add.py`, also dem Ersetzen
des Richters durch eine Attrappe, die immer „in Ordnung" sagt; der zuvor verweigerte Commit
lief danach rc 0 durch. Dazu kamen zwei weitere geöffnete Löcher (ein quotiertes Metazeichen im
Dateinamen als Wortende gelesen; `cd` in **irgendein** Verzeichnis mit dem Präfix `scripts`).
Alle drei sind in derselben Runde geschlossen und mit rot gesehenen Tests belegt (Prüfbericht
Runde 4, V1–V3). Der Eintrag bleibt als Geschichte stehen: eine Über-Verweigerung zu beheben
ist eine Lockerung, und eine Lockerung ist der teuerste Änderungstyp an einem Wächter.

### H64 — Jedes `>` eines Segments ist dem Ledger-Gate eine Umleitung, auch quotierte Prosa — offen, Über-Verweigerung als bewusster Preis (neu, TSK-0083)

**Mechanismus:** Der F3-Fix der Runde (`_redirect_targets`, `finditer`) liest **alle**
Umleitungsziele eines Segments, und zwar auf einer Sicht, die den Inhalt quotierter Spannen
behält; die Redirect-Prüfung steht vor der Stufenausnahme der verbürgten Läufe. Ein `>` in
ehrlicher Argument-Prosa ist damit von einem echten Redirect nicht unterscheidbar — verweigert
wird, sobald das Folgewort ein Ledger-Pfad oder eine geschützte Datei ist.

**Kette (gemessen 2026-08-23, Umsetzer, echte Hook-Prozesse, HEAD → jetzt):**
`python scripts/ledger_add.py add --note "net > gross and row > ledger/2026.csv" && git commit -m x`
rc 0 → **rc 2**; Kontrolle `--note "net > gross"` (Folgewort kein geschützter Pfad) bleibt rc 0;
ein einzelnes `>` vor einem Ledger-Pfad war schon vor der Runde rc 2.

**Urteil: offen, Über-Verweigerung, kein Loch — und bewusst so herum.** Schließen hieße zu
entscheiden, welches `>` die Shell ausführt und welches Prosa bleibt; genau diese
Unterscheidung entfernt die Kit-Vorverarbeitung (die H34-Familie), und die Gegenrichtung —
quotierte Redirect-Ziele **nicht** zu lesen — war das Datenverlust-Loch, das F3 geschlossen
hat (Ledger geleert, Commit rc 0). Der Ausweg für den getroffenen Nutzer steht in der
Verweigerung selbst: den Satz ohne das wörtliche Pfad-Nachwort formulieren.

### H65 — Ein Wort, das die Shell erst durch Expansion herstellt, sieht dieser Leser nicht — offen, Loch, vorbestehend (benannt TSK-0083)

**Mechanismus:** Jeder Pfadleser dieses Gates urteilt über den **Text**, den der Nutzer
geschrieben hat. Stellt die Shell das Zielwort erst her — `$f`, `${…}`, `${X:-…}`, ein Glob —,
dann steht das Wort, auf das die Operation wirkt, nirgends im Text. Das ist keine Frage der
Zeichenklasse und nicht durch ein weiteres Zeichen im Muster zu beheben: es fehlt der Zustand
der Shell, und den hat ein `PreToolUse`-Hook nicht. Bis zur Korrektur in TSK-0083 begründete
der Kopfkommentar des Gates das Gegenteil (`scripts/$X` sei sonst „das nackte Verzeichnis") —
bei ungesetzter Variable **ist** es das nackte Verzeichnis, die Begründung war von der Messung
widerlegt.

**Kette (gemessen 2026-08-23, Prüfer, Dateisystem-Zeuge in einer Sandbox mit `evil.py` und
`scripts/ledger_add.py`; am HEAD identisch, also vorbestehend):**

```
cp evil.py scripts/${f}                      rc 0   scripts/ = [evil.py, ledger_add.py]
cp evil.py ${X:-scripts/}                    rc 0   scripts/ = [evil.py, ledger_add.py]
cp evil.py scripts/$f                        rc 0   scripts/ = [evil.py, ledger_add.py]
n=led; cp evil.py scripts/${n}ger_add.py     rc 0   Validator danach: EVIL
```

Ebenso `tar -xf evil.tar -C scripts/$d` und `mv evil.py scripts/$f`, je mit `&& git commit -m x`
rc 0. Die letzte Zeile ist die schwere: sie ersetzt den Validator selbst.

**Korrektur 2026-08-24 (Prüfer, TSK-0084):** Die vierte Zeile stand hier zuerst als
`cp evil.py scripts/${n:-ledger_add.py}` — **falsch, das ist rc 2**. Der Vorgabewert einer
Ersetzung **buchstabiert** den Namen, und `_PROTECTED_RX` liest den Text; die Zeile wird also
genau dort verweigert, wo der Mechanismus dieses Eintrags gerade **nicht** greift. Sie ist
ersetzt durch eine, die den Namen nie buchstabiert. Der Mechanismus stimmte, das Beispiel
widerlegte ihn — genau der Fehler, den dieser Eintrag bei anderen misst.

**Urteil: offen, nicht schließbar an dieser Stelle.** Was stattdessen begrenzt: der Angreifer
muss die Variable im selben Aufruf selbst setzen oder auf eine ungesetzte bauen — beides steht
sichtbar in der Zeile, die der Nutzer freigibt; und die Zeile durchläuft weiterhin die übrigen
Wächter derselben Kette. Der Kopfkommentar des Gates benennt die Lücke seit TSK-0083 als offen,
ohne einen Grund zu behaupten, den die Messung widerlegt.

### H66 — `shell_readings` sagt „jede Lesart" zu und liefert nur die POSIX-Lesart — offen, Loch, vorbestehend (benannt TSK-0083)

**Mechanismus:** `_compat.shell_readings` verspricht im eigenen Kommentar „EVERY reading an
ordinary shell could give the text" und führt `_ESCAPE_CHARS = ('\\', '`')`. Gebaut ist nur die
POSIX-Backslash-Lesart. PowerShells Fluchtzeichen — der Backtick — wird von keiner Lesart
aufgelöst, also sieht jeder Leser, der auf `shell_readings` aufsetzt, einen Pfad, den die Shell
so nie zusammensetzt. Das betrifft **jedes** Gate, das über diese Funktion urteilt, nicht nur
das Ledger-Gate; sichtbar wurde es dort.

**Kette (gemessen 2026-08-23, Prüfer, `tool_name: "PowerShell"` über die volle registrierte
Kette; am HEAD identisch):** `copy-item evil.py scr` + Backtick + `ipts/ ; git commit -m x` →
rc 0. Kontrolle ohne Backtick (`copy-item evil.py scripts/ ; git commit -m x`) → rc 2.

**Urteil: offen.** Die Behauptung ist das eigentliche Problem — ein Kommentar, der Deckung
zusagt, die der Code nicht baut. Zu schließen ist es in beide Richtungen: die Backtick-Lesart
bauen, oder die Zusage auf das Gebaute stellen und die Lücke hier führen. Bis dahin begrenzt:
die POSIX-Lesart deckt den Weg, den `Bash` nimmt, und Windows-Nutzer erreichen dieselben
Operationen über die geprüfte Schreibweise; der Angriff verlangt eine bewusst gesetzte
Fluchtsequenz mitten im Pfad.

### H67 — Köder und Geschwister werden nur befragt, wenn dieselbe Zeile schon blockiert — offen, Loch, vorbestehend (benannt TSK-0083)

**Mechanismus:** Die Prüfung, ob eine Zeile einen **Zwilling** des Validators oder einen
Köderpfad benutzt, wird im Ledger-Gate nur dann gestellt, wenn dieselbe Zeile ohnehin eine
blockierte Operation trägt (ein Commit, ein Schreibzugriff aufs Ledger, ein Schreibzugriff auf
eine geschützte Datei). Eine Zeile, die den unbewachten Zwilling nur **laufen lässt**, wird
nicht befragt. **Halbiert seit TSK-0083:** der Geschwister-Fall (ein Nachbarname wie
`ledger_add.py.bak`) ist zu, weil der Wortende-Anker dort greift; offen ist nur noch der Köder
mit **eigenem Verzeichnis**, den kein Anker vom kanonischen Pfad unterscheidet, solange nichts
in der Zeile die Frage überhaupt stellt.

**Kette (gemessen 2026-08-23/24, Prüfer und Umsetzer unabhängig, an beiden Zwillingen
identisch — also nicht Preis einer Runde):** `python tools/ledger_add.py …` rc 0. Die Zeile
nennt weder einen Ledger-Pfad in schreibender Stellung noch eine geschützte Datei, also
erreicht sie die Entscheidung nicht.

**Korrektur 2026-08-24 (Prüfer, TSK-0084): die zweite Hälfte dieses Eintrags ist zu.** Hier
standen zuerst zwei weitere Beispiele, und eines davon trägt nicht mehr:
`python scripts/ledger_add.py.bak ledger/2026.csv` ist HEAD rc 0 → **jetzt rc 2** — der
Geschwister-Anker aus `TSK-0083` greift dort. Offen ist nur noch der **Köder mit eigenem
Verzeichnis** (`tools/…`), also die Zeile oben. Die Liste ist entsprechend gekürzt: ein
Beispiel, das die Behauptung nicht mehr trägt, ist genau die Aufzählung, vor der die Hausregel
warnt.

**Urteil: offen, mit begrenzter Wirkung.** Der Gewinn des Angreifers wird erst mit einer
**zweiten** Zeile wirksam, und die wird geprüft: der eigentliche Schaden (ein Commit auf einem
kaputten Ledger, ein Schreibzugriff auf den Validator) trägt dann die blockierte Operation und
wird befragt. Was hier durchläuft, ist der Lauf allein. Zu schließen wäre es, indem die
Zwillingsfrage unabhängig von der blockierten Operation gestellt wird — das ist eine
Verschärfung und gehört gemessen in eine eigene Runde, nicht als Nebeneffekt hierher.

### H68 — Zwei Schreibweisen, die verweigert werden, ohne zu schreiben — offen, Über-Verweigerung, naheliegender Fix gemessen falsch (TSK-0083)

**Mechanismus:** Das Ledger-Gate urteilt über **alle** Lesarten, die die Vorverarbeitung dem
Text geben kann, und verweigert, sobald **irgendeine** davon „schreibt" sagt. Das ist die
gebaute Richtung und die sichere. Sie trifft zwei harmlose Schreibweisen mit:

1. **Handgetippter Backslash im Validatorpfad.** Eine der beiden Lesarten verbraucht den
   Backslash, aus `scripts\ledger_add.py` wird `scriptsledger_add.py` — kein kanonischer Lauf
   mehr, also fällt die Verbürgung weg und der Ledger-Pfad in derselben Zeile zählt als
   Schreibzugriff. Gemessen: `python scripts\ledger_add.py --validate ledger/2026.csv && git commit -m x`
   HEAD rc 0 → jetzt rc 2; beide Pfade mit Backslash bzw. beide mit Schrägstrich bleiben rc 0.
   Nicht mehr enthalten ist der schlimmere Teil dieses Befunds: das Gate **bewarb** diese
   Schreibweise in seiner eigenen Verweigerung, weil es den Validatorpfad plattformabhängig
   zusammensetzte. Der Pfad ist jetzt fest in Schrägstrich-Schreibweise, und ein Test leitet
   die geprüfte Zeile aus dem **gedruckten** Text der Verweigerung ab statt aus einer zweiten
   Handabschrift.
2. **Quotiertes `;` oder `|` in Argument-Prosa** schneidet weiterhin Segment bzw.
   Pipeline-Stufe: `--summary "reversed; see scripts/ledger_add.py"` und `--note "a|b"` sind
   rc 2, vor der Runde wie danach.
3. **Quotierte Argument-Prosa mit einem Wagenrücklauf**, seit `TSK-0083`/`TSK-0084` — dieselbe
   Ursache, derselbe Preis: `--summary "reversed<CR>see scripts/ledger_add.py" && git commit`
   ist rc 2, und ohne Commit geht dieselbe Zeile von rc 0 auf rc 2. Der Wagenrücklauf **musste**
   ein Trenner werden, weil PowerShell ihn als einen behandelt und ein einziger Aufruf sonst das
   Kassenbuch vergiftete (`BUG-0066`); dass er dabei auch in quotierter Prosa schneidet, ist der
   bewusst gewählte, sichere Ausgang derselben Abwägung wie in den beiden Fällen darüber.

**Warum nicht geschlossen:** Der naheliegende Fix — quotierungsbewusst trennen — ist
**gemessen falsch**. Er schluckt genau den Trenner, den `_SUBSTITUTION_OPEN_RX` absichtlich
**in** eine quotierte Spanne injiziert, um eine Kommandoersetzung sichtbar zu machen, und macht
damit `BUG-0065` wieder auf (eine Ersetzung schmuggelt einen Schreibzugriff ins
Validator-Verzeichnis). Diese Begründung steht als Docstring am Ort der Entscheidung, nicht nur
hier.

**Urteil: offen, Über-Verweigerung, kein Loch.** Nichts geht verloren; der getroffene Nutzer
formuliert den Satz ohne das wörtliche Pfad- oder Trennzeichen-Nachwort, und die kanonischen
Schreibweisen funktionieren alle. Dieselbe Familie wie `H64` und `H34`: die Grenze ist, dass
niemand ohne den Zustand der Shell weiß, welches Zeichen sie ausführt und welches sie liest.

### H69 — Die Gates dieses Repos erben die halbe CR-Härtung der Kits — offen, Werkbank, `DEC-0022` (TSK-0084)

**Mechanismus:** `TSK-0084` hat zwei verschiedene Defekte derselben Zeichenfamilie geschlossen.
Die Gates dieses Repos teilen sich mit den Kits die Vorbereitung (`_compat`), aber nicht die Tür,
an der die zweite Hälfte hängt:

1. **Geerbt und damit zu:** der Wagenrücklauf als **Anweisungstrenner** unter PowerShell. Die
   Normalisierung sitzt in `_compat`, also greift sie hier mit — gemessen rc 0 → rc 2.
2. **Nicht geerbt und damit offen:** die **Verschweißung** unter dem Bash-Werkzeug. Die
   Verweigerung dafür sitzt in `_kernel.payload`, und `_harness` liest die Nutzlast direkt über
   `_compat.load`, geht also nicht durch diese Tür.

**Kette (gemessen 2026-08-24, Prüfer, read-only in einer Kopie außerhalb des Repos, am
HEAD-Zwilling identisch — also vorbestehend):**
`echo poison > project_mem<CR>ory/generated/index.yaml` → Gate rc 0 → bash rc 0 → `index.yaml`
von 37 318 auf 7 Byte, Inhalt `poison`. Der Wagenrücklauf verschwindet im Eingabeleser dieser
bash, bevor sie parst; zwei Wörter verschweißen zu einem Pfad, den kein Leser des Gates je zu
sehen bekam.

**Urteil: offen, und bewusst NICHT gebaut.** Die Kette läuft in einer Sitzung durch, aber
`DEC-0022` trennt die Beweislast nach Schaden, und für die Werkbank gilt dort: der einzige
Akteur ist ein Agent, der Anweisungen folgt, und **sein Irrtum nimmt den geradeaus naheliegenden
Weg**. Ein unsichtbares Steuerzeichen mitten in einem Pfad ist kein naheliegender Irrtum, sondern
ein absichtlich gebauter — und wer hier absichtlich baut, ist der Sitzungsagent selbst, dem der
Zweck der Fessel gerade nicht abhandengekommen ist. Der Nutzer hat genau das eingewandt
(„wieso solltest du angreifen? das macht man ja nicht absichtlich"), und der Einwand ist nach
unserer eigenen Entscheidung richtig; die zuerst geplante Handback-Zeile ist daraufhin
zurückgezogen worden. **Was begrenzt:** der Schaden ist eine Datei, die aus der
Versionsverwaltung zurückkommt; die getroffene Datei ist erzeugt und aus den Items neu
herstellbar; und in den **ausgelieferten** Kits — wo ein echter Angreifer existiert, nämlich ein
Inhalt, den der Agent liest und der als Anweisung getarnt ist — sind **beide** Hälften zu. Der
einzige nicht-absichtliche Weg hierher ist Text mit Windows-Zeilenenden, der in eine
Befehlszeile kopiert wird; auch der endet an der Versionsverwaltung.

### H70 — Der Vollständigkeits-Draht des Ledger-Gates fragt nach MUSTERN, also sieht er eine Ausnahme ohne Muster nicht — offen, Messlücke des Instruments (TSK-0083/TSK-0084)

**Mechanismus, als Klasse und nicht als Schreibweise:**
`tools/test_hooks_v2.py::test_every_vouching_run_pattern_is_named_here`
soll verhindern, dass eine vierte Ausnahme in `_stages_beside_the_vouched_runs` eine Stufe befreit,
ohne in der geführten Liste zu stehen. Er fragt das über **Muster**: `_patterns_consulted_by` folgt
Namen durch den geparsten Quelltext (alle Pfade, nur auflösbare Namen), `_patterns_called_by`
instrumentiert jedes modulweite `re.Pattern` und zeichnet auf, welche beim Laufen wirklich gefragt
werden (alle Namen, nur die Pfade der Sonden); der Test nimmt die **Vereinigung**. Eine Ausnahme,
die **gar kein** `re.Pattern` befragt, wird von beiden Fragen nicht erfasst — sie befreit die Stufe
und der Draht bleibt grün. Dasselbe gilt für ein Muster, das nur bei einer Eingabe **außerhalb** des
Sondenkorpus gefragt würde.

**Kette — FREMDE Messung, von beiden Rollen unabhängig gefahren, vom Lead nicht nachgemessen:**
Umsetzer (Durchgang 4, `rework3/m_fd2.py`, beide Leser aus der ausgelieferten Datei geparst) und
Prüfer messen dieselbe Zeile: eine Ausnahme, geschrieben als
`stage.strip().startswith("deno ")`, befreit die Stufe, Namensleser grün, laufender Leser grün,
Vereinigung grün. Mit echtem pytest im Klon gepflanzt: **1 passed** — der Draht schweigt. Die vier
Muster-Konstruktionen daneben (direkt benannt, Tupel von Mustern, modulweites Lambda, über
`globals()`, Tupel von Prädikats-Funktionen) sind je **1 failed**, der Draht trägt dort also.
**Der Lead hat den Fall NICHT selbst nachgemessen**, und der Versuch gehört zum Befund: vier
Anläufe mit einer selbstgebauten Sonde meldeten „blind" auch für die Formen, die beide Rollen
übereinstimmend als rot gemessen hatten — die Sonde war falsch, nicht der Code. Das ist der Grund,
warum hier die fremde Messung steht und keine eigene: ein fünfter Anlauf hätte das Instrument
noch einmal neu gebaut, das bereits zweimal unabhängig gebaut dasteht.

**Urteil: Rest, Messlücke des INSTRUMENTS, keine offene Kette im Produkt.** Dieselbe Klasse wie
`H10` (Codehälften ohne rote Mutation) und `H41` (die Grenzen des Zeiger-Wächters): der Draht
bewacht eine **künftige** Änderung, und seine Blindstelle wird erst zur Lücke, wenn jemand eine
Ausnahme ohne Muster schreibt und niemand es bemerkt. Was an seiner Stelle steht, ist im Docstring
von `_patterns_called_by` benannt und ist die andere Frage: **welche Stufe wird frei** — die die
Verhaltenstests für die von ihnen aufgezählten Verben stellen. Die Schließrichtung wäre, genau
diese Frage zu automatisieren (eine Ausnahme, die eine schreibende Stufe befreit, muss rot werden,
unabhängig davon, womit sie entscheidet); das ist eine eigene Runde und war es nicht wert, sie an
das Ende dieser zu hängen. **Warum überhaupt ein Eintrag:** der Draht hat in zwei Prüfrunden
**dreimal** eine Vollständigkeit behauptet, die er nicht baute — jedes Mal, weil die Antwort eine
Aufzählung von Schreibweisen war. Der Docstring sagt das jetzt; dieser Eintrag ist die Stelle, an
der es beim nächsten Lesen der offenen Lücken auffällt.

### H71 — Was der Leser der Merge-Rückstandsliste NICHT entscheiden kann — offen, vier gemessene Grenzen (TSK-0086)

**Anlass, und er ist der beste Grund für einen Eintrag:** `BUG-0068` kam aus dem **Live-Gebrauch**
des Nutzers an seinem echten Büro-Projekt. Er aktualisierte es selbst, bekam vom Manager
`cp`-Zeilen fürs Terminal gereicht und fragte nach, ob das so richtig sei. Es war es nicht — und
aus der einen Rückfrage wurden **fünf** Reparaturen, von denen **zwei erst durch die Fixes für die
ersten drei entstanden**. Was danach an Grenzen bleibt, steht hier, damit die nächste Runde nicht
wieder bei null anfängt.

**(a) Ein Eintrag, den `open()` mit etwas anderem als `OSError` ablehnt, reißt den Kommandolauf
ab.** Mechanismus als Eigenschaft, nicht als Schreibweise: der Vergleich baut aus jedem Eintrag
einen Pfad, und ein Wert, der schon beim Öffnen an einer **anderen** Ausnahme scheitert, läuft an
`except OSError` vorbei. Der Hook ist abgesichert (`_kernel.pending_merge_backlog` fängt
`BaseException` → `None` → Datei-Fallback, Nag da, Datei bleibt — gemessen), **`_pending_templates`
nicht**: `update-kit` endet dann nach einem **erfolgreichen** Installerlauf mit einer Ausnahme und
meldet ein geglücktes Update als Fehlschlag. Gemessen 2026-08-28 (Prüfer, NUL-Byte in einem
Eintrag): `rc 1`, `ValueError: embedded null character`. Neue Fläche dieser Runde — vorher wurde
aus einem Eintrag nie ein Pfad gebaut. Schließrichtung ist ein Einzeiler
(`except (OSError, ValueError)`), bewusst nicht mehr an das Ende dieser Runde gehängt.

**(b) Eine gelesene Liste, die zu keinem erkennbaren Eintrag dekodiert, gilt als leer und wird
gelöscht.** Schärfer als die frühere Formulierung „von Hand geleert": es genügt, dass die Datei
**lesbar** ist und ihr Inhalt für diesen Leser nach nichts aussieht, was mit `- ` beginnt.
Gemessen an einer UTF-16-Liste, die gelöscht wird. Beide Installer schreiben UTF-8, die Form ist
also **nicht ausgeliefert**; die Grenze steht trotzdem hier, weil „lesbar" und „verstanden" zwei
verschiedene Fragen sind und der Code heute nur die erste stellt.

**(c) Der Vergleich entfernt JEDES `CR`, nicht nur Zeilenenden.** Zwei Dateien, die sich nur durch
ein einzelnes `CR` **innerhalb** einer Zeile unterscheiden, gelten als gleich; eine **binäre**
Vorlage (`.woff2`), die ein `0x0D` gewinnt oder verliert, ebenso. Richtung ist
Über-**Verwerfen**: eine Kit-Reparatur, die aus nichts als so einem Byte bestünde, würde nicht mehr
gemeldet. Warum nichts das verengt, steht im Docstring von `_same_but_for_line_endings` und ist
gemessen: verengte man es, wären dieser Leser und die beiden Installer sich über **dieselbe Datei**
uneins — genau der Bruch, der die vier passenden Skripte auf die Liste des Nutzers gebracht hat.

**(d) Zwei Zustände, die absichtlich nörgeln, statt zu schweigen.** `update-kit` löscht eine
vollständig aufgelöste Liste **nicht selbst**, sondern sagt, dass der nächste Sitzungsstart sie
entfernt — der Prozess, der gerade sein eigenes Kit ersetzt hat, ist der schlechteste Ort für diese
Löschung. Und ein alter Eintrag nörgelt weiter, wenn die Ablage inzwischen auf eine **neuere**
Version gerückt ist, auch wenn er zur damaligen Vorlage passte; dann liegt wirklich eine
Kit-Reparatur an, und `session_status` meldet im selben Atemzug „KIT UPDATE AVAILABLE".

**Urteil: Rest, keine Angriffskette, drei davon Über-Verwerfen und einer ein Abbruch.** Keiner
verliert stillschweigend eine Kit-Reparatur ohne Spur — das war der Blocker dieser Runde
(eine **unlesbare** Liste galt als erledigt und wurde gelöscht) und ist geschlossen: `unlesbar`,
`leer` und `verglichen` sind seither drei verschiedene Antworten, eine ungelesene Liste erreicht
`resolved` auf keinem Weg, und der Eskalationszähler wird für sie nicht zurückgesetzt. Was
bleibt, ist (a) als lauter Abbruch und (b)/(c)/(d) als Rauschen bzw. Über-Vorsicht.

### H72 — Was die Vier-Augen-Wand NICHT bindet — offen, gemessene Grenzen der Zweitlesungs-Mechanik (TSK-0087)

**Anlass:** `FR-0035` verlangte den Vier-Augen-Mechanismus wörtlich („ein Hook der das Verschieben
sperrt …"), `TSK-0087` hat ihn gebaut: kein Eintritt ins Archiv ohne zwei unabhängige, an die
**Bytes** des Dokuments gebundene Lesungen; Uneinigkeit legt beide Lesungen dem Nutzer vor. Der
Prüfer hat die Wand in zwei Runden mit über vierzig Linien angegriffen; was durchlief, wurde
geschlossen (archivinterne Wäsche, Pfad-statt-Dokument-Bindung, `ARCHIVE/`-Faltung,
Freigabe-als-Waschgang). Diese Grenzen blieben, jede gemessen:

**(a) Die `an_entry`-Ausnahme vergleicht Vorlage und Dateiname, nicht den Ort.** Eine Bewegung,
die Regel (`path_template`) und Dateinamen behält, gilt als Aufräumen und braucht keine Lesung —
auch wenn sie einen **parametrisierten Platzhalter** wechselt: `mv …/2026/x.pdf …/2027/x.pdf` ist
rc 0 (K7), und so eine Bewegung kann auf einem Ziel landen, das bereits ein anderes, doppelt
gelesenes Dokument trägt — das wird ersetzt (K8; die Byte-Bindung läuft nicht, das Gate steht
vorher ab, und `guard_fs_tripwire` erlaubt Bewegungen im Archiv seit 2026-08-03 bewusst). Der
Docstring des Gates sagt seit der Abnahme, was der Code vergleicht, statt „ein Ordner wird
aufgeräumt" zu behaupten. Schließrichtung, wenn gewollt: den Platzhalterwechsel als Eintritt
werten — das ist eine Verschärfung mit eigener Kostenfrage (jede Jahresumsortierung bräuchte
zwei Lesungen), also eine Nutzerentscheidung, keine Nacharbeit.

**(b) Das Überschreiben eines INBOX-Dokuments ist frei.** `echo >`, Tool-`Write` und `cp` darüber
sind rc 0 — `guard_fs_tripwire` verweigert das **Löschen** unter `inbox/`, nicht das Überschreiben.
Die teure Folge („zwei Lesungen holen, Dokument tauschen, ablegen") ist seit TSK-0087 durch die
Byte-Bindung geschlossen: die Lesungen verfallen mit den Bytes („1 of 2 attested readings no
longer match its bytes", gemessen K1/K3). Offen bleibt das Überschreiben selbst — ein Dokument
kann im Eingang zerstört werden, bevor es je gelesen wurde. Begrenzung: der Verlust ist sichtbar
(die Ablage scheitert, weil keine Lesung mehr passt), nicht still.

**(c) Über-Verweigerungen, benannt und gewollt, Richtung sicher:** ein Dokument über 64 MB
bekommt keinen Byte-Stempel und wird darum verweigert statt ungebunden zugelassen (K6); ein
relatives Wort, das zwei existierende Dokumente meinen kann, verlangt die Lesungen für **beide**
(K10, die Verweigerung nennt die Streudatei); ein `Write`/Redirect direkt ins Archiv wird immer
verweigert, auch mit passenden Lesungen — eine Ablage **verschiebt** ein Dokument (§2.5); und die
Verweigerung im „kein Digest"-Zweig unterscheidet seit der Abnahme „getauscht" von „nicht
bindbar" (Rest C der Prüfrunde), damit keine Rolle einen Tausch sucht, den es nicht gab.

**(d) Was kein Hook sehen kann, bleibt Verfahren:** Blindheit des zweiten Lesers ist nicht
erzwingbar (kein Hook beobachtet einen Read; steht im Gate, im Store-Leser, in §2.5 und in
`ENFORCEMENT.md`); ein Datensatz aus einem fremden Programm (`python -c`) bekommt keinen Stempel
und zählt nicht (sichere Richtung); eine Befehlszeile, die den Store nirgends nennt, sieht kein
Gate — dieselbe benannte Grenze wie bei `kit_state.json`; und der Lead als zweiter Lauf zählt als
zwei Läufe, obwohl er den ersten Bericht gesehen haben kann — die Unabhängigkeit misst Provenienz
(zwei `agent_id`s), nicht Unwissenheit.

**Urteil: Rest.** Keine der Ketten erreicht mehr, was die Runde geschlossen hat: ein fremdes oder
getauschtes Dokument unter einem doppelt gelesenen Namen abzulegen. (a) und (b) sind echte, enge
Restwege mit benannter Begrenzung und je einer Schließrichtung, die eine eigene Entscheidung
verlangt; (c) ist Über-Vorsicht; (d) ist die ehrlich ausgewiesene Grenze zwischen Mechanismus und
Verfahren.

### H73 — Was die Entscheidungs-zuerst-Runde NICHT misst — offen, drei gemessene Grenzen (TSK-0089)

**Anlass:** `FR-0052` bringt die Regel „erst die Entscheidungen, dann der Code" in die Lead-Texte
aller drei Kits — auf die Fläche, die beim Antworten wirklich geladen ist, mit dem ehrlichen Satz,
dass kein Hook das erzwingen kann (Freitext ist für Gates unsichtbar, `DEC-0029`/R2-Klasse). Der
Prüfer hat den Wächter der Runde blind erwischt (ein 90-Zeichen-Fenster las fast jede
Überbehauptung als verneint — geschlossen: Klauselgrenze statt Byte-Zahl, vier Rot-Formen
gemessen); was danach bleibt, jede Grenze gemessen:

**(a) Jede Id in einem Begrenzer, der länger ist als sie selbst, bleibt ungeprüft.** Der
Zeiger-Leser (`tools/test_repo_hygiene.py`) urteilt über 126 DEC-Verweise in ausgelieferten
Kit-Dateien und lässt gequotete Spannen aus, weil dieser Korpus auch beleidigende Prosa und
gemessene Kommandozeilen zitiert. Gemessen: 22 doppelt gequotete Spannen tragen eine Id, 6 davon
sind gewollte Daten — die anderen **16 sind Text, den jemand liest**: 13
Kernel-Verweigerungs-/Briefing-Meldungen (`cli.py:602/777/905`, `migrate.py` ×7,
`state.py:1382`, `dispatch.py:1019`, `checkpoints.py:296`) und 3 Handover-Marker-Literale
(`scaffold_team.sh`/`.ps1`, `kitupdate.py:461`). Eine dort verrottende Id liest der **Nutzer** im
Moment einer Verweigerung. Schließrichtung: die Meldungs-Literale als eigene Klasse lesen
(String-Literal in Python-Quelle ≠ Prosazitat in Markdown) — eine eigene Runde, nicht dieser
Rest angehängt.

**(b) Der Regel-Test liest vom Inhalt nur die zwei Anker, nicht die Richtung.** Die Regel
**umgekehrt** hingeschrieben („erst der Code, dann die Entscheidungen") passiert beide Tests —
gemessen, in allen sechs Kopien. Was er hält: der Block existiert auf der geladenen Fläche, die
drei Kopien sind byte-identisch, und keine Überbehauptung im Apparat-Vokabular überlebt. Was er
nicht hält: Richtung und Gehorsam — Gehorsam kann kein Text-Test halten, Richtung könnte einer,
wenn er die Reihenfolge der Anker im Satz läse; nicht gebaut, weil der Satzbau dafür stabil sein
müsste und die Regel dann am Test klebt statt der Test an der Regel.

**(c) Eine Überbehauptung, die den Apparat nicht benennt, fällt nicht auf.** Der
Ehrlichkeits-Wächter prüft Erwähnungen von `gate`/`guard`/`hook`/`notify`/`permission` auf
verneinende Klauseln; „die Harness verweigert eine Antwort ohne Nachschlag" nennt keines dieser
Wörter und bliebe grün. Was eine umgeschriebene Regel heute **sichtbar** macht (nicht verweigert):
der Abschnitts-Digest von `test_shortening_net.py` erzwingt ein Neu-Anheften mit schriftlicher
Notiz; die Byte-Identität der drei Kopien schweigt, wenn alle drei gleich geändert werden.

**(d) Der Klausel-Schnitt des Ehrlichkeits-Wächters liest `,` nicht als Grenze und `.`/`:` immer
als eine** (`tools/test_role_contracts.py`, Schnitt an `.;:\n`). Beide Fehlrichtungen vom Prüfer
gemessen, keine trifft den ausgelieferten Text: ein Komma-verbundener Nachsatz reitet auf der
Verneinung davor mit („no hook measures this, and a gate refuses…" bleibt grün) — eine zweite
unfangbare Form neben (c); und umgekehrt schneidet jeder Punkt oder Doppelpunkt aus Abkürzung
(„e.g."), Code-Span oder Abschnittsnummer („§2.5") den Vorlauf und meldet einen ehrlichen Satz
als Überbehauptung — Über-Verweigerung, die laut scheitert und einen späteren ehrlichen
Umschreiber zur Umformulierung schickt.

**Urteil: Rest.** (a) ist die eine echte Lücke mit Leserichtung zum Nutzer und trägt ihre
Schließrichtung; (b), (c) und (d) sind die ehrlich ausgewiesenen Grenzen eines Prosa-Tests — die
Alternative wäre die Behauptung, ein Text-Test könne Verhalten messen, und genau die Behauptung
verbietet dieses Repo sich.

### H74 — Was die schnellere Gate-Suite NICHT schützt — offen, gemessene Grenzen (TSK-0090)

**Anlass:** `FR-0011` wollte die Wandzeit je Runde runter, ohne eine Messung zu verfälschen.
Geliefert: Prozessarten laufen gebündelt (−20…−27 % je Fenster, Spaltenauswahl Faktor 32–44),
die Frist-Phase kann **innerhalb eines pytest-Prozesses** strukturell keine Nachbarn bekommen
(jeder Thread wird gejoint, jeder Pool schließt), und die geteilte Prüfkopie trägt seit der
Abnahme einen Finalizer, der **jede** Bewegung in ihr rot macht — geändert, neu und gelöscht,
alle drei Richtungen gemessen. Was bleibt, jede Grenze gemessen und im Messdokument
(`docs/reviews/2026-08-29-tsk0090-measurements.md`) geführt:

**(a) Gegen einen ZWEITEN Läufer schützt nichts** — `pytest -n` (xdist ist auf dem Host
importierbar) oder ein zweiter gleichzeitiger Lauf der Suite sind nicht abgedeckt, und die
Suite ist nach dem Umbau selbst ein **schwererer Nachbar** (Spitzen-Nebenläufigkeit 10 → 26
Kindprozesse bei gleicher Gesamtzahl). Die Frist-Tests kippen unter externen Nachbarn in beiden
Fassungen — das ist `BUG-0033`, dort geführt; neu ist nur, dass diese Suite als Nachbar mehr
drückt.

**(b) Der Faktor 11 war nie im Code** — per AST-Vergleich sind die heißen Tests über drei
Monatsstände byte-gleich; was sich bewegte, war die Wirtslast (3,6× weniger Shell-Zeilen/s
zwischen zwei Fenstern desselben Tages). Der 4512-s-**Leerlauf**-Lauf vom 2026-08-13 bleibt
unerklärt — benannt, nicht wegerklärt.

**(c) Bewusst nicht gebaut:** `authored` hat keine Spaltenauswahl (ein `-k` auf einen der vier
Autoren-Tests zahlt alle 40 Szenarien: 16,53 s statt 12,09 s — durch eine Fixture begrenzt,
anders als der Faktor 33 der Zellen); `unreachable_cost` (21,03 s) wird nicht in die Bündel
vorgeholt, weil die Frist-Phase nachbarfrei bleiben muss; die Prüfsätze selbst (~9000
Shell-Zeilen + ~1600 Gate-Prozesse) sind nicht gekürzt — ihre Größe hängt an Einträgen dieser
Liste.

**(d) Zeilennummern als Zeiger sind eine offene Klasse.** Die H45-Verschiebung dieser Runde
(eine Import-Zeile, Zeiger von Hand nachgezogen) ist der zweite Fall; nichts misst, ob ein
`datei:zeile`-Zeiger in dieser Liste noch auf das zeigt, was er meinte. Schließrichtung wäre
ein Anker-Test derselben Bauart wie die Backtick-Testnamen-Drähte — eigene Runde, falls gewollt.

**Urteil: Rest.** (a) trägt seine Begrenzung (ein Läufer, ein Prozess — die dokumentierte
Aufrufform), (b) ist Wirtsphysik plus ein ehrlich unerklärter Einzelfall, (c) sind benannte
Abwägungen mit Zahlen, (d) ist eine Klasse mit benannter Bauart. Ruhefenster-Lauf: akzeptierter
Rest nach `DEC-0053`, zwei Repo-Werkzeuge (`tools/gate_suite_rates.py`,
`tools/gate_suite_margins.py`) stehen dafür bereit.

### H75 — Was der E-Rechnungs-Leser NICHT prüft — offen, gemessene Grenzen des Geldpfads (TSK-0091)

**Anlass:** `BUG-0072`, Live-Fund im echten Projekt des Nutzers — der Kit-Extraktor las aus einer
ZUGFeRD/CII-Rechnung den Positionswert statt der Dokumentsumme (14,28 statt 214,20) und gab das
stille Falsch-Tripel mit rc 0 zurück; **alle vier** strukturierten E-Rechnungen des Archivs waren
betroffen, gebucht wurde dank der Rechenprobe im Buchungs-Richter nichts Falsches. Die Runde hat
den Leser strukturell verankert, die Dokument-Identität (EN 16931 BR-CO-15, `BT-112 = BT-109 +
BT-110`; Rundungsbetrag nur auf dem BR-CO-16-Rückfall) als lauten Wächter gebaut und den Prüfer
zweimal überlebt — der dabei mit der Norm selbst gegenlas und eine Über-Verweigerung UND eine
Segnung fing, bevor sie auslieferbar waren. Was bleibt, jede Grenze gemessen:

**(a) Der Wächter ist Arithmetik, keine Semantik.** Drei in sich stimmige Zahlen vom **falschen**
Dokument bestehen. Steht als ein Satz am Wächter und in der Bookkeeper-SKILL; die zweite Lesung
gegen den Beleg ist `FR-0065` (Buchungs-Vier-Augen) und keine Extraktor-Aufgabe.

**(b) BR-CO-14 wird nicht gegengerechnet** (Σ `ApplicableTradeTax/CalculatedAmount` =
`TaxTotalAmount`): ein Kopf, der in sich stimmt, aber den Positionen widerspricht, läuft durch —
gemessen (Zeilensumme 3,00 unter einem 100,00-Kopf → rc 0). Kein Kommentar behauptet anderes.

**(c) UBL ist nur synthetisch belegt.** Im echten Korpus existiert keine einzige XRechnung-UBL;
die UBL-Hälfte lebt aus Fixtures. Und der UBL-Rückfall auf `PayableAmount` verweigert bei
**Anzahlung** (`BT-113 ≠ 0`) laut, statt zu rekonstruieren — Über-Verweigerung, nie still.

**(d) Verhaltensänderung, gewollt:** ein strukturiertes XML **ohne** Geld-Tripel liefert jetzt
rc 2 statt rc 0 mit „MISSING" — ein Nicht-Rechnungs-Dokument im Anhang wird laut zurückgewiesen
statt leer durchgereicht.

**(e) Die „Geldleser"-Klasse im Owned-Manifest ist ein Urteil, kein Test.** Gepinnt sind die
Guard-Eigenschaft (`tools/test_kitupdate.py::test_every_guarded_repo_template_is_refreshed_by_the_scaffold`)
und das tote Listenende (`tools/test_kitupdate.py::test_every_kit_owned_path_is_shipped_by_some_kit`);
dass ein Skript, das Geld liest, kit-eigen zu sein hat, bleibt begründete Entscheidung im
Manifest-Kopf.

**(f) Ein neues Umgebungs-Leck wird still geheilt statt angezeigt.** Der Rundenbeifang (zwei rote
Tests auf unberührtem HEAD: `tools/test_hooks.py` ließ `HARNESS_KERNEL_PATH` prozessweit stehen,
und der Einstiegspunkt behandelt sie als autoritativ) ist nach dem Hausmuster geschlossen — die
Fixture stellt die Umgebung nach jedem Test **wieder her**, statt im Teardown zu behaupten (eine
Behauptung liefe, bevor `monkeypatch` sein eigenes Werk zurücknimmt, und würde die Tests anzeigen,
die es richtig machen). Preis, im Fixture-Docstring benannt: ein künftiges Leck fällt nicht auf,
es wird geheilt. Was der Draht
`tools/test_repo_hygiene.py::test_no_test_in_this_suite_leaks_an_environment_variable` hält, ist
die **Fixture selbst** (entfernt → rot, gemessen); die Quellen heilt die Fixture — mit den zwei
bekannten Quellen auf blanke Zuweisung zurückgedreht bleibt der Draht grün, auch das gemessen.

**(g) Drei Randformen des Lesers, vom Prüfer gemessen, Richtung je sicher:** die dritte
Schreibweise der Anker-Klasse ist ungepinnt (UBL-`LegalMonetaryTotal`/`LineExtensionAmount`:
Anker durch Ganzbaumsuche ersetzt lässt alle 14 einvoice-Tests grün — Fehlrichtung ist die laute
Wächter-Verweigerung); ein gedrucktes Geldfeld ist der **Rohtext** des Dokuments, nicht die
geprüfte Dezimalzahl (`1E+2` und `100.005` erscheinen wörtlich auf stdout, geprüft wird die
normalisierte Zahl); und ein unlesbarer `RoundingAmount` auf dem Rückfallpfad zählt still als 0 —
was dort zur lauten Verweigerung führt, nicht zu einer stillen Zahl.

**Urteil: Rest.** (a) trägt seinen Verweis auf das offene Item, (b)–(d) sind benannte Grenzen mit
sicherer Richtung (laut oder durchgereicht-und-gesagt), (e) ist eine Entscheidung mit zwei
gepinnten Enden, (f) ist eine begründete Bauform mit benanntem Preis.

### H76 — Was der neue Dokument-Schreibweg NICHT bindet — offen, gemessene Grenzen (TSK-0092)

**Anlass:** `BUG-0070/0071/0074` + `FR-0066` — vier Live-Funde in zwei Tagen: der Nutzer tippte
dreimal YAML von Hand und verlor einmal drei Wireframes an ein Einfrieren, das den ganzen
Vorschlagsbereich leerte. Die Runde baute die Routen (Regel-Listen-Erzeugung; das generische
`apply-proposal` über die 18 schreiberlosen Kit-Dokumente; Freeze verzehrt nur noch die eine
Datei; Web für den Produkt-Redakteur) und überlebte zwei harte Prüfrunden, in denen der Prüfer
den neuen Hebel an seiner Naht traf: `compare` las strukturell, `apply` schrieb byteweise —
Inline-Kommentare, eingeschleuste Prosa, Schlüssel-Umbau und der Ablageplan-Vorbeiweg an der
strengen Route wurden alle geschlossen (Skelett-Prüfung: jeder Wert wird über die Parser-Spannen
ausgeblendet, jede verbleibende Zeile muss in Reihenfolge überleben; neue Kommentare und
Füllwerte stehen im **Wortlaut** in der Freigabekarte; ein Pfad, den ein benannter Teilschreiber
besitzt, verweigert mit dessen Namen). Was bleibt, jede Grenze gemessen:

**(a) Der Listeneintrag-Prosakanal.** Felder eines Eintrags, der einer bestehenden Liste
hinzugefügt wird, erscheinen als `1 Eintrag hinzu`, nicht im Wortlaut — der **einzige**
verbliebene Kanal, auf dem Rollen-Prosa ohne Wortlaut in der Karte ins Dokument reist. Begrenzt
durch: die Prüfsumme bindet die Vorschlagsbytes, höchstens 8 Stellen je Freigabe, und die Karte
sagt selbst, dass Werte in der Vorschlagsdatei stehen; die anfragende Rolle schuldet das Zeigen
(Prosa, kein Gate).

**(b) Eine Freigabe deckt innerhalb ihrer Stunde ein erneutes Schreiben derselben Bytes**, wenn
der Nutzer das Dokument von Hand zurücksetzt (gemessen: apply → Editor-Revert → apply, rc 0 ohne
neue Frage). Bedingung steht seit der Abnahme im Docstring; ein „verbraucht"-Marker wäre
wieder schreibbarer Zustand, der eine Durchsetzungsfrage entscheidet — dieselbe Lesart wie
`filing_correction`. Grenze: die Uhr (3600 s) und dass exakt die freigegebenen Bytes landen.

**(c) Kein Feldschema.** Der Kernel kennt die Pflichtfelder einer Kategorie nicht — ein
Vorschlag darf eine Kategorie ohne `euer_line` ergänzen. Absichtlich: die echte Datei des
Nutzers trägt Felder, die das Template nicht kennt; ein kernelseitiges Schema hätte **seine
eigene Datei** verweigert. Was stattdessen gilt: nichts geht verloren, alles Neue wird gezeigt.

**(d) Prosa-Dokumente bleiben schreiberlos, absichtlich** (3× README, 3× Masterplan, 2
Report-Templates — 8 der 18): dadurch bleibt die Aussage der globalen Einstiegsdatei über den
Masterplan wahr. Und drei web-fähige Schreibrollen tragen die Injektionsnotiz noch nicht
(`compliance-researcher`, `marketing-planner`, `shop-curator`) — die Eigenschaft „Web +
Schreibrecht ⇒ Notiz" wäre der richtige Draht, eine eigene kleine Runde; auf Codex hat ohnehin
keine Kit-Rolle Netz (`network = false` im generierten Profil, gemessen).

**(e) Vier Randbefunde des Prüfers, Richtung je sicher:** `clear_staging(promoted)` ist ein
toter Zweig ohne Aufrufer (nur ein AST-Test hält die Abwesenheit); die `moved`-Diagnose in
`documents.apply` ist über die CLI unerreichbar (ein zwischenzeitlich geändertes Ziel verweigert
korrekt, nur ohne den erklärenden Satz); eine Datei ist unter fünf Schreibweisen dieselbe
Freigabe-Position (`MASTER_DATA.YAML`, `./…`, `…/`, `staging/../…`, `…::$DATA`) — jede braucht
ihre eigene Freigabe, keine Eskalation; und die Laufzeit des verweigernden Gates hängt neu an
der Größe der Nutzerdatei (0,25 s bei 633 B, 5,8 s bei 2,8 MB — kein Kill-Risiko beim
Kit-Default, aber eine neue Abhängigkeit). Dazu vorbestehend, jetzt gemessen: Kit-Hooks aus
Test-Fixtures schreiben ins Audit-Log **dieses** Repos, wenn kein `CLAUDE_PROJECT_DIR` gesetzt
ist — der Mechanismus gehört hierher, die wachsende Zeilenzahl in keinen Kommentar.

**Urteil: Rest.** (a) und (b) tragen Begrenzung und Begründung, (c) und (d) sind Entscheidungen
mit benanntem Warum, (e) sind Ränder mit sicherer Fehlrichtung. Der Kern der Runde — kein
Verlust, kein unangekündigter Inhalt, kein Vorbeiweg an einer strengeren Route — ist von zwei
Prüfrunden gemessen.

### H77 — Was die Wertsprache-Regel NICHT hält — offen, gemessene Grenzen (TSK-0093)

**Anlass:** `BUG-0073`, Live-Screenshot des Nutzers — eine Freigabe-Karte erreichte ihn als
deutsch-englisches Gewebe, weil der Manager die Feldwerte englisch verfasste und keine Fläche
sagte, welche Sprache **Werte** tragen. Die Runde legte die Regel auf beide Lead-Flächen aller
drei Kits (verstehen = Deutsch; abgleichen = die Schreibweise des Dings, denn Übersetzen ändert,
WAS freigegeben wird), warnte auf der geladenen Fläche vor dem Kürzungsschnitt (Deutsch läuft
länger — „sag es kürzer, statt den Schnitt wählen zu lassen") und verengte eine Karten-Klausel,
die dem Nutzer das Gegenteil dessen sagte, was zwei Zeilen darüber stand. Was bleibt, gemessen:

**(a) Kein Gate kann die Wertsprache erzwingen** — ein englischer Aufruf rendert unverändert
rc 0. Die Regel lebt in Prosa und in der Formatter-Naht; steht so in beiden Fassungen.

**(b) Der Prosa-Test liest Anker und Ehrlichkeit, nicht Richtung und nicht Vokabelfreiheit.**
Der **umgekehrte** Regeltext bleibt grün; eine Überbehauptung **ohne** Apparat-Wort bleibt grün,
in beiden Sprachen gemessen („The harness refuses…" / „Die Verfassung erzwingt das."). Der
Grund, es nicht zu schließen, steht im Test: eine Liste von Behauptungsverben wäre die zweite,
schlechtere Aufzählung; sichtbar macht so einen Edit der Abschnitts-Pin. Vom Prüfer dazu
gemessen, sprachgleich in beiden Sprachen: ein **bejahendes Idiom mit Verneinungswort in
derselben Klausel** („Ohne Zweifel verweigert ein Gate…" / „Without doubt a gate refuses…")
liest der Wächter als verneint — die F5-Erweiterung hat die Klasse aufs Deutsche ausgedehnt,
nicht geöffnet.

**(c) `document_types` ist der eine getippte Wert, den der Kernel nackt in den deutschen Satz
setzt** (ohne Etikett, ohne `»…«`) — heute nur als Naht erkennbar, weil Klassennamen technisch
aussehen; eine deutschsprachige Klasse wäre vom Rahmen ununterscheidbar. Gemessen, nicht
umgebaut (das Item verlangte messen statt nachbauen).

**(d) Der Records-Clerk trägt die Regel nicht** — und er ist, vom Prüfer über alle drei Kits
abgegrenzt, die **einzige** Nicht-Lead-Rolle, die ein freies `--reason` selbst tippt; sein
englischer Grund landet unübersetzt in der deutschen Karte. Die Runde legte die Regel bewusst
auf die Lead-Flächen; die Clerk-Lücke ist real, benannt und klein umrissen. Ebenso: ein Wert,
der über ein **gestagtes Dokument** in die Karte kommt, ist in der SKILL-Fassung genannt, in
der geladenen Kurzform nicht — und der Stager ist oft ein Spezialist.

**(e) Jede Änderung an einer Kartenformulierung entwertet offene, noch unbeantwortete
Freigabe-Fragen** — `gate_approval` vergleicht zeichenweise, die alte Frage passt nach einem
Kit-Update nicht mehr auf den neu gebauten Text. Nicht neu, aber von dieser Runde ehrlich als
Folge benannt: fail-closed (die Rolle stellt neu), nie ein Durchlass.

**Urteil: Rest.** (a) und (b) sind die ausgewiesenen Grenzen eines Prosa-Tests mit benanntem
Sichtbarkeits-Mechanismus, (c) ist eine gemessene Naht mit heutiger Erkennbarkeit, (d) trägt
seine kleine Schließrichtung (ein Absatz in einer Rolle, eigene Mini-Runde), (e) ist
Über-Vorsicht in die sichere Richtung.

### H78 — Ein Startmodus, der die Projekteinstellungen nicht lädt, entfernt den ganzen Durchsetzungsapparat — offen, von innen nicht schließbar (TSK-0094)

**Der Mechanismus, in einem Satz** (so formuliert der Prüfer, und so gehört er gelesen —
`--restricted` ist nur die Schreibweise, an der es auffiel): **jeder Client-Startmodus, der die
Projekteinstellungen nicht lädt, entfernt alle vier Registrierungsflächen eines Kits, während die
Dateiwerkzeuge im Projekt schreibfähig bleiben.**

**Anlass:** Newsletter-Zeile zu 2.1.248, vom Nutzer weitergereicht; die Vermutung war „vielleicht
laufen die Hooks dann nicht" und ist gemessen worden — von beiden Rollen unabhängig, auf CLI
2.1.251, gegen frisch gescaffoldete Projekte außerhalb des Repos.

**Drei gemessene Mitglieder der Klasse** (`--restricted`, `--safe-mode`, `--setting-sources user`)
— in der Durchsetzungsfrage einheitlich, sonst nicht:

| | Kontrolle | `--restricted` | `--safe-mode` | `--setting-sources user` |
|---|---|---|---|---|
| Projekt-Hooks feuern | 10 | **0** | **0** | **0** |
| Write nach `project_memory/` | verweigert | **angelegt** | **angelegt** | **angelegt** |
| Bash ohne Zusatzflagge | ja | nein | **ja** | – |
| `bypassPermissions` | – | rc 1 | **rc 0** | – |
| Schreiben außerhalb des Arbeitsverzeichnisses | – | verweigert | **gelungen** | – |
| Werkzeuge (`init.tools`) | **7** | 152 | 30 | **159** |

**Die Kette, gegen die laufenden Gates getrieben, beide Enden gemessen:** vorher verweigert
`gate_git` den Merge eines DRAFT-Vorhabens (rc 2) — danach genügen vier gewöhnliche
Dateioperationen (Status auf `IN_DELIVERY`, drei `EVD`-Dateien mit `result: pass`), und Merge
**und** Push laufen rc 0, während `kernel.cli validate` **0 Fehler** meldet (Warnungen je nach Rig
0 oder 1; die Fehlerzahl ist die Aussage, und sie ist in beiden Messungen null). Grund:
der Kernel liest Items per `os.listdir` — eine hingelegte Datei **ist** Zustand. Die
eingeschränkte Sitzung hat diese vier Operationen beim Prüfer **selbst** ausgeführt; die
Selbstverweigerung, die der Umsetzer zuerst sah, ist Modellzufall und keine Grenze.

**Vier benannte Ränder, je gemessen:** `scripts/harness.py` — der Einstiegspunkt, den **jede**
Gate-Verweigerung als Ausweg vorschreibt — ist so beschreibbar und liegt **außerhalb** des
Vertrauens-Hashes (`hook_bundle_hash` identisch mit und ohne die eingefügte Zeile), also sieht
die nächste normale Sitzung die Vergiftung nicht; dass sie ihn dann ausführt, ist ausdrücklich
**nicht** gemessen. Der Modus **öffnet** außerdem: unter `--restricted` fällt die
`permissions.deny`-Liste des Kits mit, ein `.env`-Geheimnis wird im Klartext gelesen (unter
`--safe-mode` greift sie weiter — die Klasse fällt hier auseinander). Die Werkzeugfläche wächst
von 7 (die `tools:` der gebundenen Rolle) auf 152–159, inklusive der MCP-Server des Nutzers mit
schreibenden Werkzeugen. Und die Verfassung selbst lädt nicht — ein gepflanzter Token kommt in
der Kontrolle wörtlich zurück, im Modus `ABSENT`.

**Warum es offen bleibt und was stattdessen begrenzt:** von innen ist nichts baubar — alle vier
Registrierungsflächen eines Kits fallen weg, und die einzige Fläche, die weiterbindet, ist die
Aufrufzeile selbst, also die des Angreifers. `claude --help` beschreibt „managed settings" als
weiter geltend; diese Fläche ist hier **nicht gemessen** und wird darum in keiner Kit-Prosa als
Gegenmittel genannt. Was diese Runde liefert, ist deshalb **Ehrlichkeit statt Schutz**: die drei
Verfassungssätze, die heute „jeder Werkzeug-Schreibzugriff wird verweigert" behaupten, werden auf
das korrigiert, was der Code baut (`TSK-0095`). Der Nutzer wurde direkt informiert, mit der einen
praktischen Folge: in einem Kit-Projekt nicht mit einem solchen Modus starten.

**Nicht gemessen und benannt:** interaktive TUI (alle Läufe headless `-p`), managed settings
(Verzeichnis existiert auf dem Wirt nicht und wurde bewusst nicht angelegt), Enterprise-Policy,
`.mcp.json`, SDK-Erreichbarkeit, sechs der acht `Bash|PowerShell`-Gates. **Ein Konfundierer,
ausdrücklich:** in **allen** Läufen beider Rollen war `permissions.allow` inaktiv („this
workspace has not been trusted"), also ist jede Aussage darüber, **warum** ein Bash-Befehl
freigegeben wurde, für diese Runde unentscheidbar — die Kit-Seite bleibt davon unberührt: kein
Gate sieht einen geschachtelten Start, und die `python -c`-Schreibweise liegt innerhalb der
erlaubten Muster.

**Zwei Reste aus der Ehrlichkeits-Nachrüstung** (`TSK-0095`, vom Prüfer gemessen): dieselbe
absolute Behauptung steht weiter **außerhalb** der sechs korrigierten Texte — nachgezählt **78**
satzweise Reichweite-Aussagen in 42 Dateien, **54 ohne jede Bedingung**, darunter die drei
**Lead-Rollendateien** (`agents/project-manager.md:24` dev/research, `agents/office-manager.md:24`,
dazu `records-clerk.md` und `skills/bookkeeper/SKILL.md:42`), `README.md:439/:534` und die globalen
Einstiegsdateien unter `user/`. Die Gewichtung ist die unangenehme: die ehrliche Bodenzeile liegt
in `hooks/ENFORCEMENT.md`, das **nichts** lädt, die absolute Behauptung in den Rollendateien, die
bei **jedem** Sitzungsstart und jedem Spawn laden. Und der Leser, der die Korrektur hält, ist
selbst eine Zwei-Substantiv-Aufzählung (`every|any|all|no` × `tool write|mechanism that runs`):
eine einzelne umformulierte Rückkehr zur absoluten Fassung („refuses every write a tool performs
there") ist ihm unsichtbar — gemessen grün; rot wird nur die vollständige Erblindung.

**Urteil: OFFEN, nicht schließbar, mit benannter Begrenzung** — die dritte Zustandsform, die
`CLAUDE.md` erlaubt: warum nicht schließbar (der Apparat wird vom Client abgeschaltet, bevor eine
Kit-Datei gelesen wird) und was stattdessen begrenzt (die Modi müssen bewusst gestartet werden;
die Kit-Prosa hört auf, das Gegenteil zu behaupten; der Nutzer weiß es).

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

### H79 — Was die Besitz-Ableitung der Dokument-Schreibroute NICHT bindet — offen, gemessene Grenzen (TSK-0096)

**Anlass:** `BUG-0075`, live im echten Office-Projekt des Nutzers am 2026-08-30, einen Tag nach
`apply-proposal` (H76): der Produkt-Redakteur überarbeitete eine Inhaltsregel, legte sie als PROSA
unter einem NEUEN Namen (`claims_policy.proposed.md`) in den Vorschlagsbereich und bat den Nutzer,
sie von Hand in `content_guidelines.yaml` einzusetzen — eine zweite Autorität neben dem Kit-Dokument
und dieselbe Sackgasse, die `BUG-0071` am Vortag geschlossen hatte. Ursache: von den Rollen, die in
§6 ein Kit-Dokument BESITZEN, kannte die Mehrzahl das Kommando in der eigenen Definition gar nicht.
Die Runde macht das Kennen der Route zu einer EIGENSCHAFT des Besitzes: die Besitzer werden aus der
Besitztabelle der Verfassung × `documents.accepts` abgeleitet, und drei Prüfungen in
`tools/test_role_contracts.py` (Abschnitt 7) halten beide Richtungen — Besitzer ohne Route, Route
ohne Besitz, Route auf ein Dokument, das das Kommando verweigert. Eine vierte, vom Prüfer
gemessene Lücke ist in derselben Runde GESCHLOSSEN worden: ein schreibbares Kit-Dokument, für das
die Tabelle KEINEN Besitzer nennt, schuldete die Route niemandem; das ist jetzt ein eigener Befund
je Kit (rot gemessen an einem eingelegten `supplier_terms.yaml`). Was bleibt, jede Grenze gemessen:

**(a) Eine erfundene Zweitdatei ohne `staging/`-Präfix ist unsichtbar.** Die Ableitung fordert für
jedes besessene Dokument die Spanne `staging/<TSK-ID>/<eigener Dateiname>` im Routen-Absatz und
verbietet dort jede andere Spanne mit diesem Präfix — genau der Livefall, mechanisch gesagt. Ein
Rollentext, der zusätzlich eine Datei OHNE dieses Präfix nennt (`claims_policy.proposed.md` blank
im Satz), verletzt keine dieser beiden Bedingungen und bleibt grün; der Prüfer hat das als V5
gemessen. Begrenzt durch: der Absatz nennt die richtige Datei, also hat die Rolle keinen Anlass
mehr, eine zweite zu erfinden — das ist eine Absicht und keine Garantie, und der Docstring des
Tests sagt es in diesen Worten. Was es zu einer Garantie machen würde, wäre ein Leser für „jede
Dateinamen-artige Spanne im Absatz", also eine Endungsliste; genau die Aufzählung, die dieses Repo
als Defektquelle führt.

**(b) Derselbe FALSCHE Routentext in allen Besitzer-Definitionen kommt durch.** Geprüft wird, dass
der Vorlauf jedes Routen-Absatzes — alles bis zu seinem ersten Satz, der eine gestagte Datei nennt —
in allen Kits identisch ist; RICHTIG ist er dadurch nicht. Gemessen in dieser Runde: eine
umformulierte Behauptung in EINEM Kit ist rot (die frühere Schnittmengen-Fassung ließ sie durch, das
ist der Grund für die Gleichheits-Fassung); dieselbe Umformulierung in ALLEN ist grün, und der
Prüfer hat das als V9 unabhängig bestätigt. Begrenzt durch: die Änderung muss in jeder
Besitzer-Definition zugleich gemacht werden, und drei davon sind Lead-Dateien, über denen der
Abschnitts-Pin liegt (`tools/pin_constitution_sections.py`, das jede übernommene Änderung mit einer
Journalzeile quittiert) — Sichtbarkeit, keine Verweigerung, dieselbe Lesart wie bei H77 (a).

**(c) SKILL-Dateien liegen außerhalb der Ableitung.** Geprüft wird `agents/<rolle>.md`, weil das die
Datei ist, die der Provider der Rolle einspielt; ein SKILL ist registriert und NICHT injiziert
(gemessen 2026-08-02, `tools/provider_observations.json`). Ein SKILL kann darum weiterhin das
Gegenteil des Routen-Absatzes behaupten, ohne dass etwas rot wird — in dieser Runde genau einmal
gefunden (`office-team/skills/bookkeeper/SKILL.md` Schritt 4 behauptete, kein Kommando nenne
`master_data.yaml`, und schickte den Nutzer in den Texteditor) und von Hand korrigiert, nicht durch
einen Draht. Denselben Rang hat die Verfassung: `research-team/constitution/AGENTS.md` §2 Regel 7 trug
bis zu dieser Nacharbeit „`research_guidelines.yaml` still has NO writer at all" für ein Dokument,
das die Runde dem Methodologen zuweist — und die Verfassung übertrumpft die Rollendatei. Beides
gehört in denselben Draht: „keine Instruktionsfläche eines Kits behauptet Schreiberlosigkeit für
ein Dokument, das `documents.accepts` annimmt". Das ist der naheliegende nächste Schritt und
bewusst nicht in dieser Runde gebaut — er berührt Verfassungen und SKILLs aller drei Kits und
braucht seine eigene Rot-Messung.

**Urteil: Rest.** (a) ist Absicht statt Garantie, mit benanntem Preis der Alternative; (b) trägt
Begrenzung und Sichtbarkeit; (c) ist eine benannte, nicht gebaute Erweiterung mit zwei in dieser
Runde von Hand geschlossenen Fundstellen. Der Kern — wer die Route schuldet, welche Datei sie nennt,
welche Zweitschreiber sie mitnennen muss, und dass kein schreibbares Dokument ohne Besitzer bleibt —
ist abgeleitet und mit acht Mutationen des Umsetzers plus acht des Prüfers rot gemessen.

### H80 — Der Freigabe-Haken ließ sich in dieser Werkstatt von Hand fahren — GESCHLOSSEN (TSK-0098), mit benannten Resten

**Mechanismus:** `approvals.mint` nimmt nur einen Aufrufer an — den Freigabe-Haken, als sich selbst
gestartet (`_assert_minting_caller`). Dass *nur der Provider* diesen Haken startet, kann
Bibliothekscode nicht feststellen; das steht im Docstring des Kernels und ist als `known_hole`
erfasst. In den Kits schließt eine ZWEITE Wand diese Tür: `gate_write_scope` verweigert jede
Befehlszeile, die den Durchsetzungsapparat in einer schreibfähigen Stufe nennt. Die Gates dieses
Repos hatten diese Wand nicht: `gate_lead_write_scope` stufte eine Stufe, die eine Datei
AUSFÜHRT, als lesend ein — für den Sitzungsagenten wie für jeden Subagenten.

**Kette (gemessen 2026-08-30, Runde TSK-0097, Wegwerf-Projekt außerhalb des Repos):**
1. `request-approval scope BUG-nnnn` — reiner Kernel, ohne Haken, ohne Kit: schreibt
   `approvals/pending/<id>.yaml`, rc 0.
2. `cat project_memory/approvals/pending/<id>.yaml` — der Münz-Code steht dort im Klartext;
   `gate_lead_write_scope` rc 0.
3. `python team-kits/dev-team/hooks/gate_approval.py < forged.json`, Nutzlast allein aus (1) und
   (2) gebaut — `gate_lead_write_scope` rc 0 (für den Sitzungsagenten **und** für einen
   Umsetzer-Subagenten gemessen), der Haken antwortet
   `[team-kit gate_approval] approval APR-0001 recorded for BUG-0001`, und das Item steht danach
   auf `APPROVED` mit `approval_ref: APR-0001`.
Gegenmessung im Kit, identische Zeile aus (3) gegen `team-kits/dev-team/hooks/gate_write_scope.py`:
**rc 2**, „this command names the enforcement layer in a pipeline that can write". Dieselbe Zeile
ist im Kit verweigert und hier erlaubt. Die Suite selbst fährt diesen Aufruf als Vorrichtung
(`tools/conftest.py::mint_via_hook`) — er ist also nicht exotisch, sondern ein Einzeiler.

**Was gebaut wurde (TSK-0098), als EIGENSCHAFT und nicht als Pfadliste:** eine Befehlszeile hat
eine START-Position — die Datei, die eine Stufe ausführt —, und sie ist ein eigener Gegenstand
(`_harness.Executed`, gefüllt von `_harness._executed_words`). `ProtectedArea.hand_driven`
beurteilt diese Position gegen die **Haken-Verzeichnisse** (den Provider-Baum dieses Repos plus das
`hooks/`-Verzeichnis jedes Kits, abgeleitet über `_harness.kit_hooks_directories`) und verweigert
sie **jedem** Aufrufer. Der Grund für „jedem": wer Durchsetzungscode ÄNDERN darf, ist die Frage des
Änderungskreises und ein Subagent darf es; wer den **Provider spielen** darf, ist keine Rollenfrage.

Was danach zwei Prüfrunden gekostet hat, ist die Frage, WO in einer Zeile ein Programm anfängt.
Die Antworten stehen im Code, jede mit ihrer Messung im Docstring: der Verb-Platz, aber nur
wenn das Wort überhaupt eine Datei nennt (`_verb_as_a_file` — ein Wort ohne Trennzeichen sucht eine
Shell über `PATH`); die Operanden eines Interpreters, gefragt an seinem OPTIONSTEIL statt an allem
dahinter (`_option_part`); der Interpreter, den ein Wrapper oder eine zweite Shell startet
(`_command_positions`, mit der Lesend-Bedingung, die einen Lesebefehl frei lässt); jeder Operand
einer Stufe, deren Verb dieser Leser gar nicht benennen kann; und ein Interpreter, dem ein anderes
Programm sein Programm aus einer Datei reicht (`_handed_a_program_from_elsewhere`). Dazu zwei Leser
für eine Stufe, deren Verb er gar nicht sieht: die Wörter hinter einer schließenden Klammer, die
diese Stufe nie geöffnet hat (`_after_an_unopened_closer` — eine Ersetzung mit einem `;` darin wird
mittendurch geschnitten), und ein Verb, das erst zur Laufzeit feststeht
(`_resolves_the_verb_at_runtime`). Daneben zwei Antworten, die NICHT in der START-Position sitzen
und beide Richtungen zugleich betreffen: ein Wort, das eine Shell erst baut, ist unplatzierbar
(`_UNRESOLVED`, gefragt nur wo `_could_name_a_path` es zulässt), und eine Bewegung INNERHALB einer
Zeile, die an eine zweite Shell geht, kostet die Position (`_moves_inside_an_inline_program`).

**Warum die Einstufung der Kits nicht übernommen werden konnte, gemessen statt behauptet
(2026-08-31, `probe_lines.py`, echte Hook-Prozesse gegen ein Wegwerf-Projekt):** die Kit-Regel
(„nennt den Apparat in einer schreibfähigen Stufe") verweigert **vier von neun** gemessenen
Zeilen dieses Repos — `python -B -m pytest .claude/hooks/test_gates.py -q`, die Kernel-Zeile in
beiden Schreibweisen, `request-approval` und jede weitere Zeile, die `project_memory` oder
`.claude` nennt. Der Schnitt liegt deshalb nicht bei „nennt einen geschützten Baum", sondern bei
„führt eine Datei aus einem Haken-Verzeichnis aus". Ergebnis auf denselben Zeilen: alle
Tagesbefehle rc 0, `python tools/bump_kit_version.py` und `python tools/validate.py` eingeschlossen
— und das ist der Kern des Schnitts, denn was ein gestartetes Programm schreibt, sagt keine
Befehlszeile (H11).

**Die Kette jetzt (gemessen 2026-08-31 nach drei Prüfrunden, `battery.py` mit 63 Formen und
`subshell.py` mit 17, je × zwei Shells × beide Aufrufer):** Schritt 3 ist in **jeder** gemessenen
Schreibweise rc 2 für Lead und Subagent. Die erste Fassung dieses Absatzes war zu früh geschrieben
— drei Prüfrunden haben sie mit je eigenen Ketten bis `APPROVED` widerlegt, und was sie fanden,
steht jetzt als Liste, weil eine Liste, die einmal falsch war, ihre Fälle nennen muss:
* der einfache Weg: relativ, absolut mit Leerzeichen im Pfad, Quotierung mitten im Wort, `-B`,
  hinter `cd <hooks>`, als Empfänger einer Pipe, ohne Interpreter davor (`./<hook>`);
* ein **Optionswort HINTER dem Skript** (`python <hook> -c`, `-m`, `-abc`, `-M`) — die Frage „läuft
  hier ein Modul" wurde über alles hinter dem Interpreter gestellt, also auch über die Argumente
  des Skripts, und ein einziges Wort löschte den ganzen Scan (`_option_part`);
* ein Wort, das die **Shell erst baut**: `"$PWD/<hook>"`, `"${PWD}/<hook>"`, `"$(pwd)/<hook>"`,
  `H=<hook>; python $H`, dazu die Muster `te*m-kits/…`, `…/gate_approva?.py`,
  `…/gate_approva[l].py`, `team-kits/{dev-team,office-team}/…` (`_UNRESOLVED`);
* ein **Wrapper-Verb** vor dem Interpreter: `timeout`, `nohup`, `stdbuf`, `env`, `eval`,
  `find -exec`, und die Argumentliste aus einer Datei (`xargs -a list.txt python`, die einzige
  dieser Formen, die den Haken auch wirklich geprägt hat);
* eine **zweite Shell**, mit und ohne Bewegung darin: `bash -lc "python <hook>"`,
  `sh -c "cd <hooks> && python gate_approval.py"` (die zweite hat geprägt);
* PowerShells **Aufrufoperator mit einem Ausdruck** statt eines Programmnamens,
  `& ('pyt'+'hon') <hook>` — in dieser Runde selbst gefunden, nicht gemeldet, und mit echtem
  PowerShell als Zeugen, dass die Zeile wirklich startet;
* eine **Subshell**, die zuerst hineingeht: `(cd <hooks> && python gate_approval.py)` und jede
  gemessene Schwester davon — mit `;` statt `&&`, geschachtelt, hinter einer Pipe, im
  Hintergrund. Die Klammer bewegt den Elternprozess nicht, und genau deshalb urteilte dieser Leser
  weiter von dort aus, während der Befehl IN der Klammer aus dem bewegten Verzeichnis startet.
  Das ist die duale Hälfte von **H27**, die dort mit ihrer Schreib-Richtung steht, und sie hat
  geprägt.

Schritt 1 und 2 bleiben rc 0 — sie sind Kernel und Lesen, und daran ändert diese Runde nichts.

**Die zweite Hälfte: der EHRLICHE Weg existiert jetzt.** `.claude/settings.json` registriert den
Freigabe-Haken der Kits auf beiden `AskUserQuestion`-Ereignissen, mit `timeout`, über
`${CLAUDE_PROJECT_DIR}` gebildet (leerzeichenfrei, siehe **H81**) und auf die Kit-Datei zeigend
statt auf eine Kopie — `approvals.mint` nimmt den Haken nur an, wenn er als er selbst neben seinem
eigenen `_kernel.py` läuft. In einer Wegwerf-Kopie Ende zu Ende gefahren (`probe_mint.py`):
`approval_mint_is_wired` `False`→`True`, `request-approval` ohne die Warnung, wortgleiche
Weiterreichung rc 0, umformulierte rc 2, die Antwort der Plattform prägt `APR-0001` und geht die
Kante selbst (Item danach `APPROVED`, der Handübergang meldet „illegal transition APPROVED →
APPROVED"). **Nicht gemessen und nicht behauptet:** ein echter Klick eines echten Nutzers — die
`answers` schreibt in einer Sitzung die Plattform; die Sonde hat sie in der Kopie selbst gesetzt.

**Urteil: GESCHLOSSEN (TSK-0098) für den Unterschied, den dieser Eintrag benennt — mit einem Rest,
den auch das Produkt trägt.** Keine Befehlszeile prägt hier mehr eine Freigabe, in keiner
gemessenen Form und für keinen Aufrufer; die Werkstatt steht damit auf derselben Wand wie ein
ausgeliefertes Kit und trägt dessen benannten Rest. Dass **ein Skript** es weiter kann, ist keine
Nachlässigkeit dieser Runde, sondern die Klasse **H11**, die die Kits gleichermaßen tragen und die
dort um genau diese Messung erweitert ist.

**Reste, jeder mit einem Zeugen aus einer echten Shell (`residues.py`, Wegwerf-Projekt, echter
Kernel) — „prägt" heißt: das Item stand danach auf `APPROVED`:**

| Rest | Gate lead / sub | Shell | prägt? |
|---|---|---|---|
| **R1** ein selbst geschriebenes Skript startet den Haken (`python probe_start.py`) | 0 / 0 | rc 0 | **ja** |
| **R2** `python -m runpy <hook>` | 0 / 0 | rc 1 | nein — `-m` nimmt einen MODUL-, keinen Pfadnamen |
| **R3** `python -c "…runpy.run_path(<hook>)"` | 2 / 0 | rc 0 | nein — `_assert_minting_caller` nimmt `run_path` nicht an |
| **R4** ein Kit-Haken**verzeichnis** rekursiv kopieren und die Kopie starten | 2 / 0 | rc 0 | **ja** |
| **R5** `sh <<'EOF' … python <hook> … EOF` | 0 / 0 | rc 2 | nein — das Heredoc verbraucht die stdin, die der Haken für die Nutzlast braucht |
| **R6** `python <(cat <hook>)` (Prozessersetzung) | **2 / 2** | rc 2 | nein — der Haken liefe unter dem Dateinamen der Ersetzung; seit der Subshell-Runde ohnehin verweigert |

**Was daraus folgt, ohne Beschönigung.** **R1** ist die einzige Form, die JEDEM offensteht, und sie
ist zugleich der Weg, auf dem dieses Repo seine Haken misst. **R4** trifft nur einen
**Subagenten** und nur die rekursive Form über ein Verzeichnis: eine Haken-DATEI zu kopieren ist
seit dieser Runde jedem verweigert (gemessen: `cp <hook-datei> x` rc 2/2, `cp -r .claude/hooks copy`
rc 2/2), offen bleibt `cp -r team-kits/<kit>/hooks copy` (rc 2 für den Lead, 0 für den Subagenten),
weil das Wort das Haken-Verzeichnis SELBST nennt und ein Verzeichnis in der START-Position kein
gestartetes Programm ist. Beide Reste geben einem Subagenten nichts, was R1 ihm nicht ohnehin gibt.
**R2 stand in der ersten Fassung dieses Eintrags als offener Startweg — das war falsch**, mit
derselben Strenge falsch wie ein verschwiegenes Loch: der zweite Prüfer hat gemessen, dass die
Zeile gar nichts startet. Seither trägt jeder Rest hier seinen Shell-Zeugen.

**Über-Verweigerungen, die diese Runde bewusst in Kauf nimmt (alle gemessen):**
* ein Haken-Pfad, der einem Skript als **Argument** übergeben wird, ist rc 2
  (`python probe.py .claude/hooks/gate_approval.py`); der Leser kann Argument und Programm nicht
  trennen, ohne den Fall `python -W ignore <hook>` zu verlieren;
* eine Datei in einem Haken-Verzeichnis, die kein Haken ist, ist in der START-Position trotzdem
  rc 2: `python .claude/hooks/test_gates.py`. Der dokumentierte Weg
  (`python -B -m pytest .claude/hooks/test_gates.py -q`) bleibt rc 0;
* **kein Shell-Befehl pflegt mehr eine Haken-Datei**: kopieren, verschieben, löschen oder ein
  `sed -i` darauf ist jedem verweigert, auch dem Subagenten, dem das Werkzeug `Edit` dieselbe Datei
  offenhält. Das ist der Preis dafür, dass eine Stufe, deren Verb dieser Leser nicht benennen kann,
  ihre Operanden als Start liest — und es ist dieselbe Regel, die die Kits für ihren eigenen Apparat
  aussprechen;
* ein Wort, das eine Shell erst baut, ist **auch dort** verweigert, wo es harmlos wäre:
  `$`, `*`, `?`, `[` und `{` machen ein Wort unplatzierbar, ohne dass Quotierung gelesen wird
  (`_UNRESOLVED` sagt, warum die vier Konstruktionen dafür zu verschieden quotiert werden).
  **Gefragt wird das aber nur, wo das Wort überhaupt einen Pfad benennen könnte** —
  mit Trennzeichen, oder an einer Programmstelle (`_could_name_a_path`). Die erste Fassung
  fragte jedes Wort und verweigerte damit `[ $i -ge 3 ]`, also jede Warteschleife, mit der
  diese Runde ihre eigenen Hintergrundläufe abgefragt hat; `$i` ist dort Daten und kein
  Gegenstand.

**Was diese Runde ZUSÄTZLICH geschlossen hat, ohne dass es hier gefordert war:** dieselbe
Unplatzierbarkeit fehlte in der SCHREIB-Richtung, seit die Shell-Hälfte gebaut wurde —
`sed -i "s/a/b/" "$PWD/team-kits/kernel/state.py"` war rc 0, während die relative Schreibweise
derselben Datei rc 2 war. Der Fix sitzt in `_candidates`, durch das beide Positionen laufen, also
ist die Schreib-Hälfte mit geschlossen; `test_gate1_refuses_a_word_it_cannot_resolve_in_the_write_position`
hält sie.

**Wodurch ein Rückfall auffiele:** `test_gates.py::test_gate1_refuses_starting_a_hook_from_every_caller`
(gekreuzt über die abgeleiteten Haken-Verzeichnisse, dreizehn Startformen und beide Aufrufer),
`…::test_gate1_refuses_a_word_it_cannot_resolve` über die sieben Schreibweisen, die eine Shell erst
baut, `…::test_gate1_refuses_a_powershell_call_operator_starting_a_hook` und
`…::test_gate1_refuses_the_line_that_minted_an_approval_nobody_gave` für die Zeile dieses Eintrags.
Jede dieser Aufzählungen hat ihren Zeugen aus einer echten Shell —
`…::test_a_start_shape_really_starts_a_program`,
`…::test_an_unresolved_word_really_changes_in_a_shell` und
`…::test_the_powershell_call_operator_really_starts_a_program` —, denn eine Form, die nichts
startet, ist eine Wand vor nichts. Die Gegenrichtung halten
`…::test_gate1_leaves_a_file_outside_the_hook_directories_startable`,
`…::test_gate1_leaves_a_wrapped_module_run_alone`,
`…::test_gate1_does_not_read_a_bare_verb_as_a_file_in_the_working_directory` und
`…::test_gate1_does_not_read_a_directory_as_a_started_file`.

### H81 — Der Mint-Leser irrt in BEIDE Richtungen: eine unzerlegbare Zeile warnt zu viel, eine fehlende Datei zu wenig (neu, TSK-0097)

**Mechanismus:** `report.approval_mint_is_wired` beantwortet „kann eine Antwort des Nutzers hier
etwas bewirken" und entscheidet damit zwei Sätze, die eine Rolle liest (der stderr-Hinweis an
`request-approval` und der Zusatz an der Transition-Verweigerung). Ob eine Registrierung den Haken
FÄHRT, fragt er `report._invoked_scripts`. Dieser Leser findet ein `.py` nur, wenn er die Zeile in
Wörter zerlegen kann; eine quotierte Spanne mit einem **Leerzeichen** darin zerlegt er nicht. Die
Datei-Existenz fragt er umgekehrt gar nicht — das tat `_wired_hooks`, und genau diese Bedingung
wurde bewusst fallengelassen, weil sie zur Blockier-Frage gehört.

**Kette (gemessen 2026-08-31, `probe_n3.py`, echte Hook-Prozesse, Wegwerf-Projekte):**

| Registrierung | `_invoked_scripts` | Leser | was wirklich passiert |
|---|---|---|---|
| `python -B "$CLAUDE_PROJECT_DIR/.claude/hooks/gate_approval.py"` (Kit-Form) | `['gate_approval.py']` | `True` | münzt, Item `APPROVED` |
| `python -B "C:/…/n3/quoted-space/.claude/hooks/gate_approval.py"` mit Leerzeichen im Pfad | `[]` | **`False`** | **münzt trotzdem**, Item `APPROVED` |
| auflösbarer Pfad, Datei **fehlt** | `['gate_approval.py']` | **`True`** | nichts läuft |
| `echo "see gate_approval.py"` | `[]` | `False` | nichts läuft (richtig) |

Die erste Fehlrichtung ist eine **Über-Warnung**: die Rolle wird aufgefordert, die Lücke zu melden,
statt die Frage weiterzureichen — eine stehengebliebene Runde, keine erfundene Freigabe. Die zweite
ist eine **Unter-Warnung**: es wird geschwiegen, wo nichts münzen kann.

**Wen es trifft:** kein ausgeliefertes Kit. Alle drei registrieren über `$CLAUDE_PROJECT_DIR`, also
steht in der Zeile selbst kein Leerzeichen — gemessen, alle drei `settings/settings.json` gegen die
eigenen `hooks/`-Bäume: `True`. Getroffen wäre ein Projekt, in dem jemand den Pfad **ausschreibt**,
und das ist genau der Fall, den die H80-Empfehlung an den Nutzer erzeugt hätte: dieses Repo liegt
unter `C:\Offline Repos\AgentAndSkills`. **Und dieses Repo ist seit TSK-0098 selbst ein Projekt mit
einer solchen Registrierung** — sie ist über `${CLAUDE_PROJECT_DIR}` gebildet, und genau deshalb
liest `approval_mint_is_wired` hier `True` (gemessen 2026-08-31 gegen die geschriebene Datei,
deren Projektpfad ein Leerzeichen enthält). Die ausgeschriebene Form wäre dieselbe Wirkung mit der
falschen Auskunft gewesen.

**Urteil: Rest, keine Angriffskette — benannte Grenze.** Keine der beiden Richtungen erzeugt eine
Freigabe; die eine hält eine Runde an, die andere schweigt. **Warum nicht hier geschlossen:**
`_invoked_scripts` ist auch der Leser hinter `_wired_hooks` → `capability_matrix` → `doctor` und
hinter der Vertrauensprüfung des Hook-Bündels. Ihn um quotierte Spannen zu erweitern verschiebt,
was `doctor` für **jedes** Projekt meldet, und braucht eigene rote Tests an diesen Lesern — eine
eigene Runde, nicht ein Zusatz in einer Runde über Endzustände. Ein zweiter Zerleger nur für den
Mint-Leser wäre die zweite Antwort auf „was fährt diese Zeile", also genau die Drift, gegen die
`_invoked_scripts` als einzige Antwort existiert. **Was stattdessen begrenzt:** beide Richtungen
stehen im Docstring des Lesers, die Registrierung dieses Repos ist seit TSK-0098 selbst
leerzeichenfrei gebildet, und die Kits sind gemessen nicht betroffen.

**Wodurch es auffiele:** `probe_n3.py` im Rundenverzeichnis fährt die vier Zeilen der Tabelle; ein
Lauf sagt, ob sich der Leser bewegt hat.

### H82 — Was die interne Sicht-Schleife für Design-Entwürfe NICHT bindet — offen, gemessene Grenzen (TSK-0099)

**Anlass:** `BUG-0076`, live im echten Projekt des Nutzers (Canyon, 2026-08-30, Kit 2026.08.24-7):
der PM legte dem Nutzer zweimal eine Design-Fassung vor, die niemand je gerendert hatte. Beide
Runden wurden an Dingen abgelehnt, die nur Pixel zeigen; danach hat der NUTZER selbst die interne
Screenshot-Prüfung angefordert. Gemessen am ausgelieferten Kit: jede Screenshot-Pflicht hing an
„after implementation", die Entwurfsphasen sagten nur „iterate with the user", und die Rolle
Product-Designer hatte gar kein Kommando-Werkzeug. Die Runde baut `gate_design_sighted` (dev-team,
`PreToolUse(AskUserQuestion)` + `SubagentStop`), `scripts/kit_design_render.py` und gibt dem
Designer `Bash`.

**Ein Befund der ersten Fassung ist GESCHLOSSEN und steht hier, weil er die Leserichtung
begründet:** der erste Auslöser zerlegte die Nachricht in Wort-Token und löste jedes als Pfad auf.
Der Prüfer maß an EINEM ungerenderten Entwurf: repo-relativ rc 2, aber absoluter Pfad, `file://`,
quotiert, alles mit Leerzeichen rc 0 — das Token-Muster schloss `:` und Leerraum aus. Das reale
Projekt liegt unter `C:/Offline Repos/gewerbe/...`, also MIT Leerzeichen. Der Gate liest jetzt vom
Dateisystem zum Text: es zählt die gestagten `.html` auf und fragt, ob die Nachricht ihren
Dateinamen oder ihren staging-relativen Pfad enthält, kleingeschrieben. Nachgemessen, je rc 2:
repo-relativ, absolut (beide Trennzeichen), `file://`, quotiert, Markdown-Link, nackter Dateiname,
GROSS, Leerzeichen im Dateinamen, Leerzeichen im Unterordner — 0,15 bis 0,28 s je Lauf.

Was **nicht** geschlossen ist, jede Grenze gemessen:

**(a) Eine Nennung, die den Dateinamen nicht ausschreibt, sieht das Gate nicht.** Gemessen je rc 0:
nur der Ordner („alles unter `project_memory/staging/TSK-0007/`") und der Name ohne Endung. Dazu
ein zweiter Weg derselben Klasse: der PM soll den Kontext laut PM-SKILL als sichtbaren Text VOR die
Frage setzen, und die Nutzlast eines `PreToolUse(AskUserQuestion)` ist genau die Frage — der Text
davor steht nicht darin. Über `transcript_path` wäre er erreichbar; bewusst nicht gelesen, weil er
unbegrenzt groß und providerförmig ist und eine Nennung von vor drei Zügen nicht die Nennung
DIESER Frage ist. Begrenzt durch: die Frage muss ohnehin selbsttragend sein
(`guard_question_context`), und wer dem Nutzer etwas zum Öffnen gibt, schreibt den Dateinamen hin.
Absicht, keine Garantie.

**(b) Über-Verweigerung derselben Mechanik: ein gestagter Entwurf, der den Dateinamen einer
Quelldatei trägt.** Gemessen: liegt `staging/TSK-0009/index.html` im Projekt, verweigert eine Frage
über `src/index.html` mit rc 2; ohne diesen Entwurf rc 0. Preis der Alternative: nur noch ganze
Pfade zu vergleichen, und genau das war die Fassung, die alle Windows- und Leerzeichen-Schreibweisen
durchließ.

**(c) Der Renderdatensatz ist Selbstauskunft genau des Agenten, über den geurteilt wird.** Er
schreibt `review/render.json` und die Bilder selbst; ein handgeschriebener Datensatz mit korrektem
sha256 und einem 20-Byte-„Bild" öffnet die Tür (gemessen, rc 0). Der Gate belegt damit die HERKUNFT
der Bytes — dass ein Browser lief, ist ebenso wenig belegt wie dass jemand hingesehen hat. Das
sagen die ENFORCEMENT-Zeile, der Hook-Kopf und der Renderer jetzt in diesen Worten; eine frühere
Fassung schrieb „the record proves provenance", was zu stark war. Gebaut wurde nur die billige
Hälfte: Bildpfade müssen INNERHALB des Staging-Items liegen (`_contained_child`) — ein
`../../../../Windows/win.ini` als „Bild" ist rc 2 statt rc 0. Das Muster aus `FR-0035`: Herkunft
ist messbar, Blindheit nicht.

**(d) Die Stopp-Tür urteilt weiter über zu viele Rollen.** Erste Fassung: über JEDEN Subagenten —
gemessen rc 2 für `Explore` und für einen Stopp ohne `agent_type`. Jetzt gebunden an die
Eigenschaft „diese Rolle hätte rendern können", gelesen aus der installierten Rollendatei; gemessen
rc 0 für `software-architect` (kein Kommando-Werkzeug), `Explore` und ohne `agent_type`, rc 2 für
`product-designer`, `frontend-developer`, `quality-engineer`, `devops-engineer`. Die letzten beiden
sind die verbleibende Über-Reichweite: eine shell-tragende Rolle, die einen gestagten Entwurf nur
ZITIERT, wird mitgeurteilt. Der genaue Schnitt wäre `kernel.dispatch.task_for_agent` — der braucht
die Kernel-Brücke und mit ihr den `GATE_PREAMBLE`-Umbau des ganzen Hooks; nach `DEC-0056` mehr
Gerüst als der Restfall wert ist. Die Fragetür ist die Garantie, die Stopp-Tür scheitert nur früher.
Nebenwirkung dieser Reichweite, geerbt und darum leicht zu übersehen: bei einer Verweigerung bricht
die `SubagentStop`-Kette VOR `gate_dispatch` ab, das Ende des Kindes wird also nicht gebucht — bei
`gate_subagent_output` ist das gewollt (das Kind arbeitet weiter), hier trifft es jetzt auch Rollen,
die mit dem Entwurf nichts zu tun haben.

**(e) Was `Bash` in dieser Rolle NICHT begrenzt.** Der Prüfer maß als gebundener Subagent über alle
acht registrierten Shell-Gates: das Schreib-WERKZEUG auf `src/app.py` ist rc 2, aber
`echo x > src/app.py`, `sed -i`, `cp`, `python -c open(...)`, `curl`, `cat .env` sind rc 0; nur
`docker system prune -f` und `git push` verweigern. Die Rolle, deren Text „You NEVER write
production code" sagt, kann Produktionscode also aus der Shell schreiben — das ist eine Regel, die
sie hält, keine, die etwas verweigert. Der Rollentext behauptete bis zu dieser Nacharbeit das
Gegenteil („keeps your writes inside your task's `allowed_scope`") und zeigt jetzt auf
`ENFORCEMENT.md`, das den Rest schon korrekt führte. Eingegrenzt ist die vom Refusal
vorgeschriebene Zeile selbst: 32 Läufe (zwei Zeilenformen × zwei Aufrufer × acht Gates) rc 0,
während die Pfadform derselben CLI an `gate_write_scope` rc 2 ist — deshalb nimmt das Skript eine
Task-Id statt eines Pfades.

**(f) Der Designer erreicht jetzt den Kernel-Einstiegspunkt.** Mit `Bash` beantwortet der Kernel
`hand_back` für die Rolle mit `self` (abgeleitet, gemessen in
`tools/test_role_contracts.py::test_the_product_designer_can_look_at_its_own_draft_and_says_what_that_costs`).
Damit ist `freeze-design` aus der Designer-Sitzung erreichbar, und kein Gate verweigert einen
Freeze ohne Freigabe — „der PM friert ein, nie du" ist eine Regel ohne Draht dahinter. Nach
`DEC-0056` die bewusst benannte Ausnahme statt einer Härtungsrunde: der Handelnde wäre die eigene
Rolle, kein Fremder.

**(g) Ohne Browser fällt die Entwurfsphase aus, laut statt leise.** Fehlt Playwright oder Chromium,
endet `kit_design_render.py` mit Exit 2 und der Installationszeile und schreibt KEINEN Datensatz
(gemessen für „kein Staging-Verzeichnis" und „kein `.html` gestaget"; keiner der beiden Läufe
hinterließ eine `render.json`) — das Gate verweigert die Vorlage dann weiter. Bewusst gewählter
Preis: eine stille Degradierung würde genau die falsche Sicherheit erzeugen, die `BUG-0076`
beschreibt. Gemildert dadurch, dass dev-team `playwright` seit dem Browser-Smoke ohnehin in
`requirements-dev.txt` führt — dieselbe Abhängigkeit, keine neue.

**(h) Auf `SubagentStop` gilt die Ein-Retry-Durchreiche, und sie wird geteilt.** Setzt der Provider
`stop_hook_active`, lässt das Gate den zweiten Stopp durch (sonst Endlosschleife) — dieselbe
bewusste Lücke wie bei `gate_subagent_output`, und beide Gates teilen sich die eine Wiederholung,
weil das Flag pro Fortsetzung und nicht pro Gate gesetzt wird. Gemessen: erster Stopp rc 2, zweiter
rc 0 mit `gave_up` im Audit. Die Fragetür hat keine solche Durchreiche.

**(i) Nur dev-team bekommt die Schleife, und research-team ist eine benannte Ausnahme.** Die
Eigenschaft ist gebaut („welche Rolle schreibt laut ihrem eigenen Abschnitt *Files you WRITE* eine
HTML nach `staging/`"); sie trifft dev-team UND research-team, dessen Report-Writer `EXP-*.html`
stagt, „so every report can be eyeballed in a browser". Ausgenommen mit Grund im Test
(`DESIGN_LOOP_EXEMPT`): diese HTML ist die optionale Schnellansicht des `.tex`/PDF, das eingereicht
wird, und wird nach INHALT beurteilt — die Fehlerklasse aus `BUG-0076` (ein nach dem AUSSEHEN
gewähltes Artefakt erreicht den Nutzer ungesehen) existiert dort nicht. Die Ausnahme ist in beide
Richtungen gepinnt: hört research auf, HTML zu stagen, wird der Eintrag rot. Die Vorgängerfassung
des Tests behauptete diese Eigenschaft und maß eine Wortsuche nach `freeze-design`, an der
research vorbeilief — vom Prüfer gefunden.

**Urteil: Rest.** (a), (b), (d) und (f) sind benannte Grenzen mit gemessenem Preis der jeweiligen
Alternative; (c) ist zur billigen Hälfte gebaut und zur teuren ehrlich benannt; (e) ist eine
bewusst erkaufte Fläche, deren Grenzen jetzt dort stehen, wo die Rolle sie liest; (g) ist eine
Entscheidung gegen stille Degradierung; (h) ist geerbt und dokumentiert; (i) trägt eine begründete,
beidseitig gepinnte Ausnahme. Der Kern — ein gestagter Entwurf erreicht den Nutzer nicht ohne
Renderdatensatz über genau seine Bytes, in jeder Schreibweise seines Namens — ist an der laufenden
Fassung rot gemessen.

---

### H83 — Ein Referenz-Skill erreichte nur Projekte auf dem Preset `all` — GESCHLOSSEN (TSK-0104), beide Ketten, mit benanntem Rest

**Mechanismus (Stand vor TSK-0104).** Die Skill-Schleife beider Scaffold-Zwillinge filterte
Skill-VERZEICHNISSE über die Preset-Rollenliste: `scaffold_team.sh` ruft `in_preset "$name" || continue`, `scaffold_team.ps1`
prüft `$presetRoles -notcontains $_.Name`. Beides ist richtig für ein Rollen-Skill, dessen Name
eine Rolle IST — und falsch für ein Referenz-Skill, das per Definition zu keiner Rolle gehört
(Verfassung §1a). Bei `PRESET_ROLES=""` (das Preset `team`, intern `all`) trifft der Filter nicht,
darum fällt es nur unter `solo` und `duo` auf.

**Gemessene Kette**, echter Scaffold-Lauf gegen ein Wegwerf-`$HOME` unter
`_round-scratch/TSK-0100/scaffold/` (kein Eingriff in den globalen Store, DEC-0057 d), Kit aus dem
Strom mit elf Skill-Verzeichnissen:

| Preset | installierte Skills | `frontend-design` | `webapp-testing` |
|---|---|---|---|
| `team` | 11 | ja | ja |
| `solo` | 5 (backend-developer, project-auditor, project-manager, quality-engineer, software-architect) | **nein** | **nein** |

Die Folge trifft genau die Ableitung, die diese Runde gebaut hat: `kernel.references` liest
`.claude/skills/*/SKILL.md` des PROJEKTS, also nennt der Auftrag eines `solo`-Projekts nichts, und
die Verfassung §1a beschreibt dort eine Mechanik ohne Inhalt. Kein Datenverlust, kein
Sicherheitsloch — eine Auslieferungslücke.

**Warum sie im Strom offen blieb.** `scaffold_team.sh` / `.ps1` standen in `forbidden_scope`
dieses Stroms (`TSK-0100`); der Parallelstrom `TSK-0101` besaß sie. Ein Umweg über `presets.yaml` — die
Referenz-Skills als Preset-Einträge zu führen — ist keine Alternative, sondern ein zweiter Defekt:
`tools/validate.py` Schritt 6/7 verlangt, dass jeder explizite Preset-Eintrag eine echte Kit-Rolle
ist, und die Rollen-Manifestdatei `.claude/team_kit_roles.txt` steuert das subtraktive Entfernen.

**ZWEITE, UNABHÄNGIGE KETTE DERSELBEN LÜCKE — der Codex-Spiegel, und die trifft AUCH das Preset
`team`.** `.agents/skills/` wird nicht kopiert, sondern **erzeugt**, und zwar pro ROLLE:
`gen_provider_artifacts.py` läuft über die installierten Rollendateien, gefiltert durch
`.claude/team_kit_roles.txt`. Ein Referenz-Skill hat keine Rolle, also erzeugt der Generator es
nie. Gemessen am selben echten Scaffold, Preset `team`: `.claude/skills` trägt zwölf Verzeichnisse
(elf Kit-Skills plus das eingeworfene Design-System), `.agents/skills` trägt **neun** — genau die
installierten Rollen. Folge: drei ausgelieferte Texte behaupteten „Codex reads
`.agents/skills/<name>/SKILL.md`" über Skills, die dort nie ankamen. TSK-0100 hat die drei Sätze
auf den damaligen Stand korrigiert („keine native Kopie"); TSK-0104 hat den Generator geändert
und damit dieselben drei Sätze ein zweites Mal — sie sagen jetzt wieder, dass die Kopie da ist,
und ihre Grundlage steht gegen den laufenden Generator
(`tools/test_reference_skills.py::test_the_codex_mirror_is_generated_per_skill_directory`).
Dass ein Satz in EINER Runde zweimal umgeschrieben werden musste, ist der Preis dafür, die
Aussage und nicht nur ihre Grundlage zu pflegen — und genau der Grund, warum die Grundlage
gepinnt ist. Der Routen-Test dieser Runde
las den KIT-Baum und war deshalb über alle drei Sätze grün; sein Docstring sagt das jetzt.

**Der Schnitt, den TSK-0104 gemacht hat**, als Eigenschaft und nicht als Namensliste, an
**zwei** Stellen statt einer: (1) die Skill-Schleife beider Scaffold-Zwillinge kopiert ein
Verzeichnis, wenn es im Preset steht ODER wenn das Kit für seinen Namen **keine Rollendatei**
(`agents/<name>.md`) ausliefert — genau die Definition von „gehört keiner Rolle"; (2)
`team-kits/gen_provider_artifacts.py` spiegelt nach derselben Eigenschaft statt nur über
`roles`. **(2) ist eine Nahtdatei außerhalb JEDES Stroms** — kein Strom darf sie anfassen, also
muss die Merge-Runde es tun, sonst bleibt die Codex-Hälfte offen, auch nachdem die Scaffold-Hälfte
zu ist. Dazu je ein Test, der einen `solo`-Lauf bzw. das erzeugte `.agents/skills` MISST statt die
Zeile zu lesen.

**Was den Schaden bis dahin begrenzt — und die erste Fassung dieses Absatzes war schlicht falsch.**
Sie behauptete, `solo`/`duo` installierten `product-designer` und `frontend-developer` ohnehin
nicht. Gemessen an echten Scaffold-Läufen stimmt das nicht: `duo` installiert **sieben** Rollen
**einschließlich `frontend-developer`**, und `quality-engineer` steckt in `solo` **und** `duo` —
also sind genau die Rollen da, für die abgeleitet würde, und die Verzeichnisse fehlen. Die Lage ist
nicht gemildert, sie ist voll da.

**Wie sie sich ÄUSSERT, ebenfalls gemessen, weil die naheliegende Vermutung falsch ist:** der
Header nennt **keine** toten Skills. Die Ableitung liest das `.claude/skills` des PROJEKTS, nicht
den Kit-Baum, also liefert `for_task` dort die leere Liste und der Schlüssel `references` bleibt
weg. Nachgemessen an den drei echten Projekten: `duo`/`frontend-developer`/`type: ui` → `[]`,
`duo`/`quality-engineer`/`type: test` → `[]`, `solo`/`quality-engineer` → `[]`, während dieselben
Fragen im `team`-Projekt `['frontend-design', 'webapp-testing']` bzw. `['webapp-testing']`
beantworten. Der Ausfall ist also **stille Abwesenheit einer Fähigkeit**, kein hängender Zeiger —
schlechter als ein Fehler, den man sieht, und der Grund, warum der Eintrag offen bleibt statt als
Randfall zu gelten.

**GESCHLOSSEN in TSK-0104, beide Ketten, je gegen einen laufenden Prozess gemessen.**

* **Scaffold-Hälfte:** beide Zwillinge überspringen ein Skill-Verzeichnis nur noch dann, wenn das
  Kit für seinen Namen eine `agents/<name>.md` ausliefert UND das Preset diese Rolle nicht führt.
  Die Frage „ist dieser Name eine Rolle" wird an das `agents/`-Verzeichnis des Kits gestellt, nicht
  an eine Liste, also ist ein morgen dazukommendes Referenz-Skill am Tag seiner Auslieferung
  gedeckt.
* **Codex-Hälfte:** `gen_provider_artifacts.native_skill_sources` ist der eine Gegenstand des
  Spiegels — jedes unmittelbare Kind von `.claude/skills/` mit einer `SKILL.md`, also dieselbe
  Definition, nach der beide Provider ein Skill erkennen. Ausdrücklich mit erfasst: ein Bündel, das
  der NUTZER dort ausgepackt hat (`FR-0045` lädt genau dazu ein) — die gewollte Richtung, denn die
  Alternative wäre, dass die beiden Provider verschiedene Skills sehen.
* **Rot gemessen** in einem Klon außerhalb des Repos, je eine Mutation zurück auf den Stand von
  `c155a5f`: `tools/test_reference_skills.py::test_a_reference_skill_reaches_every_preset_and_not_
  only_team` fährt den ECHTEN Installer in beiden Zwillingen über die Presets `team`, `duo` und
  `solo` und prüft beide Enden — jedes Skill ohne Rolle kommt überall an, und ein Rollen-Skill
  außerhalb des Presets weiterhin nicht (sonst wäre die Prüfung von einem Installer erfüllt, der
  alles kopiert). Derselbe Test misst den erzeugten `.agents/skills`-Baum gegen das, was im Projekt
  liegt; `::test_the_codex_mirror_is_generated_per_skill_directory` hält die Ableitung im Generator.

**Rest, benannt:** das subtraktive Entfernen beim Preset-Wechsel läuft weiter über die ROLLEN-Liste
(`.claude/team_kit_roles.txt`). Ein Referenz-Skill wird also nie entfernt — richtig, solange das
Kit es ausliefert, und ungemessen für den Fall, dass ein Kit ein Referenz-Skill wieder abschafft:
das Verzeichnis bliebe im Projekt stehen. Kein Datenverlust, keine Kette; ein Eintrag für die Runde,
die ein Referenz-Skill zurückzieht.

**Urteil: GESCHLOSSEN (TSK-0104), beide Ketten — mit dem einen benannten Rest.** Die Scaffold-Hälfte
und die Codex-Hälfte sind je als Eigenschaft geschlossen und je mit einem Test rot gemessen, der den
echten Installer bzw. den erzeugten Spiegel fährt; was bleibt, ist der subtraktive Rückbau eines
zurückgezogenen Referenz-Skills — kein Datenverlust, keine Kette, gehört der Runde, die so ein
Skill zurückzieht.

### H84 — Was die Ableitung der Referenz-Skills NICHT bindet — offen, gemessene Grenzen (TSK-0100)

**Anlass:** `FR-0071`, Nutzerfrage „wie entscheidet der PM wann welche eingesetzt werden? Nicht dass
er blauäugig immer dieselben nutzt?". Gebaut: `kernel/references.py` liest die
`reference_for:`-Erklärung jedes Skills gegen `assigned_role` und `type` der Aufgabe;
`create_lease` legt das Ergebnis in die Lease, `dispatch_header` trägt es in die eine Zeile des
Prompts, die den Spezialisten wörtlich erreicht.

**(a) Der Fehler, den das fängt, ist VORHERGESAGT und nicht gemessen.** `DEC-0056` verlangt den
gemessenen Anlass; hier gibt es ihn nicht: bis zu dieser Runde deklarierte jede der 27 Rollen genau
ein Skill mit ihrem eigenen Namen, es gab also nichts zu wählen und keinen Fehlgriff zu beobachten.
Das ist ausdrücklich eine Vorkehrung zur Bauzeit, und der Preis ist entsprechend klein gehalten:
eine Datei Kernel-Code, ein Frontmatter-Block je Skill, kein Gate. Der erste Pilot-Transkript-Lauf,
in dem eine Rolle ein nicht genanntes Skill öffnet, ist die fehlende Messung.

**(b) Der Header ist ein Zeiger und erzwingt nichts.** `parse_header` liest drei Schlüssel, und
`references` ist keiner davon (gemessen in
`tools/test_reference_skills.py::test_the_dispatch_header_names_the_reference_skills_the_task_derives`).
Ob die Rolle das genannte Skill je öffnet, sieht niemand — dieselbe Klasse wie die Sicht-Pflicht aus
`H82(c)`: die Herkunft ist messbar, das Hinsehen nicht.

**(c) Die Fluchttür ist Prosa.** Verfassung §1a erlaubt ausdrücklich, ein nicht genanntes Skill zu
öffnen, und verlangt dafür eine Zeile im `evidence` des Ergebnisumschlags. Nichts prüft das. Die
Alternative — die Fluchttür schließen — wäre eine Verweigerung, die nichts durchsetzen kann
(`allowed-tools`/`disallowed-tools` sind providerspezifisch und pro Zug, gemessen im Juli-Bericht
§3(5)), also eine Regel, die nur wie erzwungen LIEST.

**(d) Die zweite Richtung des Stolperdrahts ist an der Ableitung tautologisch.** Solange
`for_task` seine Namen aus den Skill-VERZEICHNISSEN nimmt, löst jeder ausgegebene Name auf. Der
Test dazu ist ein Boden unter dieser Konstruktion und wird rot, sobald ein Name von woanders
hereinkommt (gemessen: eine `for_task`, die einen Literalnamen hinzufügt, ist rot). Die Richtung,
die HEUTE brechen kann — ein ausgelieferter TEXT schickt eine Rolle zu einem Skill, das es nicht
gibt — trägt ein anderer Leser
(`tools/test_reference_skills.py::test_every_skill_retrieval_route_a_shipped_kit_file_spells_resolves`),
und der liest nur die Codex-Pfadschreibweise. Die Claude-Schrägstrich-Form ist bewusst ausgelassen
und der Grund ist gemessen: `/hooks`, `/model` und `/schedule` stehen als PROVIDER-Kommandos in den
ausgelieferten Verfassungen und PM-Skills, ein Leser dieser Form meldet in allen drei Kits
Nicht-Skills als fehlend. Preis: eine Datei, die nur die Schrägstrich-Form anbietet, ist ungedeckt.

**(e) Die Kreuzmenge ist die des Kits, nicht die der Wirklichkeit.** Der Stolperdraht fragt
`roles × TASK_TYPES` aus dem ausgelieferten Baum. Ein Projekt, das eine Rolle abwählt (Preset,
`H83`), erzeugt weniger Aufträge als der Test annimmt — der Test misst „erreichbar für IRGENDEINEN
Auftrag dieses Kits", nicht „erreichbar in DIESEM Projekt".

**Urteil: Rest, keine Angriffskette — benannte Grenzen eines Zeigers.** (a)–(e) sind Grenzen der
Ableitung, die nur einen HINWEIS erzeugt und keine Erlaubnis; die Fehlrichtung ist überall ein
fehlender Zeiger, nie ein falscher Zugriff. Was heute brechen kann (ein Text schickt zu einem
Skill, das es nicht gibt), trägt der genannte Routen-Test; die Claude-Schrägstrich-Form bleibt mit
gemessenem Grund ungedeckt.

### H85 — Was die Herkunfts- und Bündelprüfungen NICHT sehen — offen, gemessene Grenzen (TSK-0100)

**Anlass:** `FR-0068`/`FR-0070` (zwei fremde Skills unter Apache-2.0 übernommen) und `FR-0045` (das
Bündelschema aus einem echten Claude-Design-Export).

**(a) Eine UNMARKIERTE Änderung am übernommenen Text fällt nicht auf.** Der Test hält die
`[MOD-n]`-Marken im Text und die Liste am Ende gegeneinander — beide Richtungen, gemessen rot. Was
er nicht kann, ist die größere Hälfte: einen Satz, der geändert wurde, ohne eine Marke zu setzen.
Dafür bräuchte er die Original-Bytes, und keine Prüfung dieser Suite geht ins Netz. Was gebaut
wurde, ist stattdessen die Nachvollziehbarkeit: `source_commit` + `source_blob_sha1` im Frontmatter
jedes übernommenen Skills, gemessen gegen die GitHub-Blob-Hashes beim Ziehen (identisch), sodass
eine spätere Runde neu zieht und diffed. Ein Test, der das täte, wäre ein Netzzugriff in der Suite —
bewusst nicht gebaut.

**(b) `NOTICES.md` reist nicht mit.** Die Datei liegt in der Wurzel dieses Repos und wird vom
Scaffold nicht in ein Projekt kopiert. Was die Apache-2.0-§4-Pflichten im INSTALLIERTEN Projekt
erfüllt, liegt im Skill-Verzeichnis selbst und reist mit: die `LICENSE.txt` daneben, der
Änderungshinweis im Kopf der `SKILL.md`, die Marken im Text. §4(d) greift nicht — die
Upstream-Ordner tragen kein `NOTICE` (zweimal gemessen, 2026-07-27 und 2026-08-31). Die Tabelle ist
Buchhaltung für Leser DIESES Repos, und die Datei sagt das über sich selbst.

**(c) Das Bündelschema ist an EINEM Export gemessen, und der Pfad-Leser hat zwei benannte
Grenzen.** 184 Einträge, Typ „design system", vom Nutzer geliefert. Ob ein PROTOTYP-/Handoff-Export
dieselbe Form hat, ist ungemessen und stand schon so in `FR-0045`. Die Prüfung ist entsprechend
zurückhaltend: sie verlangt drei Dateien und eine abgeleitete Eigenschaft (jeder Pfad, den der
Index NENNT, existiert), nicht die 33 Komponenten und 309 Token dieses einen Bündels. Gemessen: am
echten Archiv 105 pfadförmige Werte, alle auflösend, Ergebnis `ok`; acht Mutationen desselben
Archivs je `rc 2` mit benanntem Fehlteil. Die zwei Grenzen: **(c1)** die Existenzprüfung ist
`os.path.isfile` und damit dateisystemabhängig — ein Index, der `Tokens/Colors.css` schreibt, wo
`tokens/colors.css` liegt, ist auf Windows/macOS `rc 0` und auf einem case-sensitiven Host
`rc 2`. Ein eigener Fall-Vergleich wäre eine zweite Antwort auf „existiert diese Datei" neben der
des Betriebssystems und ist bewusst nicht gebaut. **(c2)** die Regel „ein Schlüssel, der auf
`path`/`paths` endet oder `files` heißt, nennt eine Datei" greift auch in **unbekannte** Schlüssel:
ein künftiger `*Path`, der eine URL, ein Verzeichnis oder einen optionalen Ort benennt, wird als
fehlende Datei gemeldet. Der Boden unter dem Leser prüft, dass er am SCHLÜSSEL entscheidet und
nicht am Aussehen des Wertes — er prüft nicht, dass jeder künftige Schlüssel dieser Form wirklich
eine Datei meint.

**(d) Ein Bündel ohne `_ds_manifest.json` findet der Suchlauf nicht.** Der Index IST der
Erkennungsschlüssel — er ist die einzige Datei, die sonst nichts in einem Skill-Verzeichnis hat, und
das ist es, was einen halb ausgepackten Export von einem Rollen-Skill unterscheidbar macht. Der
Preis steht in der Meldung des Suchlaufs selbst („nenne den Ordner auf der Kommandozeile") und ist
in beide Richtungen gemessen: der genannte Ordner wird mit „`_ds_manifest.json` is missing"
verweigert, während der Suchlauf über die elf echten dev-team-Skills `rc 0` und „kein Design-System"
sagt.

**Die zweite Hälfte davon ist gebaut, weil sie billig war, und ihre Grenze steht hier:** das
häufigste Auspack-Ergebnis ist ein WRAPPER-Ordner (das Archiv landet in einem neuen Ordner, das
Bündel liegt eine Ebene tiefer). Vorher meldete die Prüfung dafür drei „X is missing"-Zeilen über
einen Ordner, dessen Inhalt völlig in Ordnung ist. Sie sagt jetzt „das Bündel liegt eine Ebene
tiefer, in `<name>`" — gebunden an eine BENANNTE Form (hier kein Rückgrat, genau ein Kind mit
Index), damit der Hinweis einen echten Fehlteil nicht verschluckt; beide Richtungen sind gemessen
(zwei Kandidatenkinder oder ein bloß fehlender Index bekommen weiter die echte Antwort). **Nicht
gebaut:** eine zweite Ebene. Ab dort wäre es kein Hinweis auf einen bekannten Fehler mehr, sondern
eine Suche, deren Fehlschlag niemand beschreiben kann. Der SUCHLAUF selbst steigt weiterhin nicht
hinab — ein Wrapper unter dem Skill-Verzeichnis bleibt für ihn unsichtbar, und die Meldung „nenne
den Ordner" ist der Weg dorthin.

**(e) Der Inhalt des Design-Systems wird nicht beurteilt.** Kontrast, Token-Qualität, ob die
Komponenten zum Produkt passen — nichts davon liest diese Prüfung, und sie ist kein Gate: nichts
verweigert eine Aufgabe, weil sie `rc 2` gab. Sie ist die laute, frühe Antwort auf „ist das Ding
überhaupt benutzbar".

**Urteil: Rest, keine Angriffskette — benannte Grenzen einer Prüfung, die kein Gate ist.** (a) bis
(e) sagen, was der Bündel-Leser nicht sieht (Netz, Dateisystem-Schreibweise, unbekannte Pfadschlüssel,
zweite Ebene, Inhalt); jede Grenze fällt in die laute Richtung (`rc 2` mit benanntem Teil) oder in
eine benannte Nicht-Prüfung, nie in eine stille Annahme.

---

### H86 — Was die Bestandsklassifikation NICHT sieht — offen, gemessene Grenzen (TSK-0101)

**Anlass:** `FR-0044`/N13. Der Installer klassifizierte den vorgefundenen Bestand gar nicht; die
Seitenkontrolle vom 2026-08-16 konnte den No-write-Nachweis nicht führen, weil ihr ein echter
V1-Bestand fehlte (§5.6). Die drei Feldkopien unter `C:/Offline Repos/v2-pilot` SIND welche —
gemessen 2026-09-01: alle drei tragen `.claude/kit_version` und `.claude/team_kit_roles.txt` wie ein
V2-Projekt (der Vor-Kernel-Installer schrieb beide, `git show 9e4419b~1:team-kits/scaffold_team.sh`),
und keine einzige Datei liegt im Bereich des Kernels. Was der Leser in ihnen findet, als
Datensatz für alle Leser dieser Zahl: **synaipse 632** V1-Backlog-Datensätze in 7 Monolithen
(`tasks.yaml` 264, `system_requirements.yaml` 224, `decisions.yaml` 69, `feature_requests.yaml` 48,
`product_requirements.yaml` 17, `change_requests.yaml` 6, `bugs.yaml` 4), **portfolio 285** in
denselben 7, **BuyPlugGo 16** in `process_definitions.yaml`. Die Gegenmessung mit dem Installer VOR dieser
Runde, gegen dieselbe synaipse-Kopie: rc 0, 128 neue Dateien, 64 geänderte, eine gelöschte
(`.claude/hooks/auto_dashboard.py`), `.claude/kernel` installiert — über einen Zustand, den kein
V2-Kommando lesen kann und in den danach kein Werkzeug mehr schreiben darf. Nach der Runde: alle
drei rc 1, Baum-Hash vorher/nachher identisch (1602 / 4010 / 2590 Dateien).

Die Klassifikation liest ZWEI unabhängige Dinge über das Zustandsverzeichnis — ob der Kernel dort
einen eigenen Bereich hat, und ob ein V1-Datensatz in einem durchsuchbaren Dokument liegt — und die
vier Verdikte sind deren Kreuzprodukt. Was sie **nicht** sieht, je gemessen:

**(a) Ein V1-Bestand AUSSERHALB des Zustandsverzeichnisses.** `docs/old/tasks.yaml` mit einem
`TSK-0001` → Verdikt `greenfield`. Gemessen ist das Verdikt; dass ein greenfield-Verdikt den
Installer schreiben lässt, ist die Gegenrichtung derselben Runde
(`tools/test_kitupdate.py::test_a_greenfield_project_still_installs`). Dieselbe Klasse, die `N11` schon für
`gate_write_scope` festgehalten hat: geschützt ist der ORT, nicht der Datensatz. Begrenzt durch:
der Bestand, um den es geht, ist der eines INSTALLIERTEN Kits, und dessen Zustand lag in beiden
Generationen unter `project_memory/`. Ein Projekt, das seinen V1-Speicher nach `docs/` verschoben
hat, hat ihn bereits als Altpapier behandelt.

**(b) Ein umbenannter oder versteckter V1-Speicher IM Zustandsverzeichnis.**
`project_memory/tasks.yaml.bak` mit einem `TSK-0002` → `greenfield`. Das ist geerbt und nicht neu:
`migrate.search_coverage` führt genau diese Datei als `unsearched`, und der Rest steht als `L19`
dort. Diese Runde übernimmt den Leser bewusst statt einen zweiten zu schreiben — ein eigener hätte
den Installer und den Validator über dieselbe Datei verschieden urteilen lassen.

**(c) Ein V1-Datensatz im Bereich des Kernels** (`L20`) — wer eine Monolithdatei nach
`product/active/` kopiert, wird von keinem der beiden Leser genannt.

**(d) Der Preis der Lesung wird bezahlt, auch wenn nichts gefunden wird.** Gemessen, warm:
synaipse 2,9–3,1 s über 20 Dokumente, BuyPlugGo 0,95–1,03 s über 14, portfolio 0,77–0,92 s. Der
Bereich des Kernels wird NICHT gelesen (die Item-Dateien sind `KERNEL`), sonst wäre es die
Größenordnung des Zustands statt die der Dokumente. Die Schranken sind `report.DOCUMENT_MAX_BYTES`
und `DOCUMENT_SCAN_MAX_BYTES`, importiert statt abgeschrieben.

**(e) GESCHLOSSEN, und der Eintrag bleibt, weil die erste Fassung dieses Absatzes das Gegenteil
behauptete.** Bis zur Nacharbeit vom 2026-09-01 landete ein Dokument, das die Lesung nicht öffnen
konnte, in `unreadable` und **sonst nirgends**: die Meldung sagte „diese Einschätzung kann zu kurz
sein", das VERDIKT blieb `greenfield`, und der Installer lief durch. Gemessen vom Prüfer an einer
echten BuyPlugGo-Kopie mit EINER unbalancierten `[` in `process_definitions.yaml`: rc 0, +132/−1/~58
Dateien, `.claude/kernel` installiert, Monolithe unverändert daneben — also genau der Zustand, den
(a)–(c) als „von innen kein Weg zurück" beschreiben. Zwei Kommentare im Code behaupteten dabei
Schutz, den er nicht baute. Jetzt ist die unvollständige Lesung ein **eigenes Verdikt**
(`unknown`), und zwar an genau der Stelle, an der sie die Entscheidung ändern kann: liegt schon ein
V1-Datensatz vor, steht das Verdikt ohnehin fest; besitzt der Kernel einen eigenen Bereich, sind
die beiden Reste `v2` und `mixed` und beide werden geschrieben; nur wenn beides fehlt, stehen sich
`greenfield` und `v1` gegenüber — und das ist die eine Stelle, an der „nicht hingesehen" nicht als
„nichts gefunden" aufgelöst werden darf. Rot gemessen an der ENTSCHEIDUNG (Baum-Hash vor/nach einem
echten Installerlauf, beide Zwillinge): `tools/test_kitupdate.py::test_a_stock_whose_reading_did_
not_complete_is_not_written_over`; die Gegenrichtung, damit daraus keine Über-Verweigerung wird:
`tools/test_kitupdate.py::test_a_reading_that_did_not_complete_over_a_LIVE_v2_project_still_installs`.

**Urteil: Rest.** (a)–(c) sind Grenzen EINES Lesers, den zwei andere Stellen dieses Kernels schon
benutzen; sie zu schließen hieße, eine zweite Definition von „V1-Datensatz" zu schreiben, und genau
das ist der Defekt, den `report._check_no_v1_records_outside_the_archive` ausdrücklich vermeidet.
(d) ist kein Loch, sondern der bezahlte Preis, hier mit Zahl. (e) ist geschlossen und steht als
Warnschild: eine Meldung ist kein Schutz.

---

### H87 — Pin und Rollback hatten keinen Kernel-Befehl, und der Pin schwieg in der Sitzungsmeldung — GESCHLOSSEN (TSK-0104), mit benanntem Rest

**Anlass:** `FR-0041`/N8. Gebaut ist der MECHANISMUS: `.claude/kit_pin` verweigert sowohl
`update-kit` als auch den von Hand gestarteten Installer, und `scaffold_team --rollback` /
`-Rollback` spielt das vorige Bundle zurück. Nicht gebaut ist die BEDIENFLÄCHE, und zwar aus einem
Auftragsgrund, nicht aus einem technischen: die Kommandofläche liegt in `team-kits/kernel/cli.py`,
und dieser Stream (`DEC-0057`, Strom B) darf keine andere Kernel-Datei als `kitupdate.py` anfassen.

Gemessen am ausgelieferten Einstiegspunkt der Feldkopie: 25 Unterkommandos, `has_pin: false`,
`has_rollback: false`. Was ein Nutzer heute also tun muss, um zu pinnen: die Datei
`.claude/kit_pin` mit `version: <stand>` aus einer Shell AUSSERHALB der Sitzung anlegen, und zum
Lösen löschen. Das ist bewusst nicht die Sitzung — `gate_write_scope` verweigert dort jeden
Werkzeug-Schreibzugriff auf `.claude/`, und ein Pin, den der Agent selbst setzen könnte, wäre
schlimmer als keiner.

**Der Preis, den der Pin dafür zahlt, dass er den Nag NICHT abschaltet** (die Markerklasse aus
`BUG-0078`): die Sitzungsmeldung rechnet ihr Angebot aus `kitupdate.relation` und kennt diese Datei
nicht. Gemessen am ausgelieferten `session_status.py` als Prozess, gegen ein gepinntes Projekt
(installiert 2026.09.01-2, gestaged 2099.12.31-9): der Text sagt „KIT UPDATE AVAILABLE … On their OK
you install it YOURSELF" und nennt den Pin mit keinem Wort. Die Kette läuft also so: der PM schlägt
das Update vor, der Nutzer sagt ja, die Freigabe wird geprägt — und ERST `update-kit` verweigert und
nennt den Pin. Das ist die laute Reihenfolge, nicht die stille: nichts wird installiert, und der
Nutzer erfährt vom eigenen Pin. Der Preis ist eine überflüssige Frage an den Nutzer und eine
geprägte Freigabe, die nichts öffnet. Die Gegenrichtung — den Nag abschalten — wäre genau
`BUG-0078`: eine Datei, die eine Meldung dauerhaft verstummen lässt, ohne dass jemand davon weiß.

**Was fehlte, benannt als Naht für die Merge-Runde:** `pin-kit` / `unpin-kit` / `rollback-kit` auf
`kernel/cli.py`, ein Satz in `session_status.py`, der den Pin nennt statt das Update anzubieten, und
die Zeile in `README.md`s Kommandoflächen-Liste. Alle drei lagen außerhalb des erlaubten Bereichs
dieses Stroms; TSK-0104 hat alle drei gebaut (unten).

**Was der Pin seit der Nacharbeit vom 2026-09-01 zusätzlich hält**, weil beides an ihm vorbeiging
und beides gemessen ist: (1) er vergleicht ein **Bundle**, nicht eine Versionszeichenkette —
`bump_kit_version.py` stempelt alle drei Kits auf denselben Stand, also ging ein KIT-TAUSCH glatt
durch (gepinnt auf `dev-team 2026.09.01-4`, `scaffold_team office-team` → rc 0, +114 Dateien,
Durchsetzungsschicht und Verfassung ersetzt, Pin schweigt); verglichen wird jetzt das Kit plus jedes
Stempelfeld, das der Datensatz **nennt**. (2) Er verweigert auch den **Rollback** — der ersetzt das
installierte Bundle genauso wie ein Update. Vorher: gepinnt auf 2099.12.31-9, `--rollback` → rc 0,
Stempel 2026.09.01-4, Pin bleibt stehen — und danach ließ der Pin **weder** Update **noch**
Reparatur durch, weil das einzige zugelassene Bundle nicht mehr installiert war.

**GESCHLOSSEN in TSK-0104, alle drei Stellen.**

* **Drei Kommandos auf der Fläche:** `pin-kit`, `unpin-kit`, `rollback-kit`. Sie **drucken und
  handeln nicht**, und das ist die Entscheidung und keine halbe Umsetzung. Die Eigenschaft dahinter:
  eine Sitzung darf einen Hebel ziehen, der nur Verweigerung HINZUFÜGT, nie einen, der sie
  WEGNIMMT. Einen Pin zu lösen nimmt weg — er ist das Einzige, was zwischen dieser Sitzung und einer
  ersetzten Durchsetzungsschicht steht —, und ein Rollback ersetzt diese Schicht so gut wie ein
  Update, wofür `update-kit` eine geprägte Freigabe braucht, die für einen Rollback keine
  Freigabeart deckt. Was die drei liefern, ist genau das, was der Eintrag als fehlend benannte:
  Bequemlichkeit und eine frühere Ansage — der Pfad der Pin-Datei mit den zwei Zeilen dieses
  Projekts, die Pin-Datei zum Löschen, die Sicherung mit ihrer Zeile. Gemessen als Baum-Hash um
  alle drei Aufrufe, gepinnt und ungepinnt:
  `tools/test_kitupdate.py::test_the_kit_pin_routes_print_and_never_write`.
* **Die Sitzungsmeldung nennt den Pin** statt das Update anzubieten: `_kernel.kit_update_verdict`
  kennt ein fünftes Verdikt `pinned`, und es trifft genau den EINEN Satz, der bisher nach einem OK
  fragte — die drei anderen sagen ohnehin „nicht installieren". Der Nag wird nicht stummgeschaltet
  (das wäre `BUG-0078`s Markerklasse); dieselbe Tatsache kommt einen Schritt früher, zusammen mit
  dem Wortlaut des Pins. Gemessen am ausgelieferten Haken als Prozess:
  `tools/test_kitupdate.py::test_a_pinned_project_hears_about_its_pin_instead_of_an_offer`.
* **`README.md`** trägt die vier neuen Kommandos in der Kommandoflächen-Liste und zwei Absätze zu
  Pin und Rollback; die drei Verfassungen tragen die Liste ebenfalls
  (`tools/test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it`
  erzwingt beides).

**Rest, benannt und gewollt:** die Pin-DATEI legt weiterhin nur der Nutzer an und löscht sie
weiterhin nur er, aus einer Shell oder einem Dateimanager außerhalb der Sitzung. Das ist keine
Restlücke, sondern die Aussage des Mechanismus: ein Pin, den der Agent selbst setzen oder lösen
könnte, wäre keiner. Wer das ändern will, braucht eine eigene Freigabeart — ein Eingriff in
`approvals.APR_KINDS`, die Schemata und alle drei Verfassungen, also Gerüst über dem Haus
(`DEC-0056`) und eine eigene Runde.

**Urteil: GESCHLOSSEN (TSK-0104) für beide Hälften des Eintrags — mit dem einen gewollten Rest.**
Die Kommandofläche trägt die Verben (sie drucken und handeln nicht, und jeder Text sagt das), die
Sitzungsmeldung nennt den Pin statt des Angebots, beides rot gemessen am ausgelieferten Haken und
an der Fläche; der Rest ist die Aussage des Mechanismus, kein Loch.

---

### H88 — Der Rollback ist byte-gleich nur über die aufgezeichnete Menge, und ältere Sicherungen tragen keine — offen, gemessen (TSK-0101)

**Anlass:** `FR-0041`/N8, zweite Hälfte. Der Installer schrieb seine Sicherungen seit jeher nach
`.claude/backups/<stempel>`, aber kein Befehl spielte sie zurück, und die Sicherungsliste und die
Wiederherstellungsliste im Skript waren zwei getrennte Aufzählungen. Jetzt ist es EINE Menge
(`RESTORABLE` / `$restorable`), die Sicherung schreibt sie als `RESTORE_SET` IN die Sicherung, und
der Rollback spielt die Menge, die die damalige Sicherung aufgezeichnet hat.

**(a) Was der Rollback nicht rückgängig macht, wird genannt statt verschwiegen.** Gemessen an der
synaipse-Feldkopie: 15 aufgezeichnete Pfade, byte-gleich; und die Zeile
`[rollback] left as they are (not part of the recorded set): .claude/agent-memory
.claude/claude-security-guidance.md .claude/HANDOVER_PENDING .claude/kit_last_seen_version
.claude/kit_update_pending.repo .claude/project_path.state`. Zwei davon sind Absicht (der Marker
steht, weil sich das Bundle unter der laufenden Sitzung erneut geändert hat; das Gedächtnis des
Agenten gehört ihm), die Merge-Rückstandsliste ist der echte Rest: sie ist die Liste des NEUEN
Kits und überlebt dessen Rücknahme.

**(a2) Das Manifest einer Sicherung ist DATA, und der Zwilling, der es liest, ist nicht
zwingend der, der es schrieb.** Gemessen in der Nacharbeit: mit `../victim.txt` in einer
`RESTORE_SET` verglich der POSIX-Zwilling das Wort **textuell** gegen `$REPO/`, ließ es passieren,
und sein `rm -rf` löschte bei rc 0 eine Datei **außerhalb** des Repositoriums — während der
PowerShell-Zwilling dieselbe Zeile über `GetFullPath` verweigerte. Beide verweigern jetzt ein Wort
mit `..`-Bestandteil, und zwar bevor irgendetwas gelöscht wird (die Zeilen werden erst alle geprüft,
dann zurückgespielt). Rot gemessen in beiden Leserichtungen, mit der LÖSCHUNG als erster Zusicherung:
`tools/test_kitupdate.py::test_neither_twin_replays_a_snapshot_that_points_out_of_the_repository`.

**(b) Eine Sicherung von VOR dieser Runde trägt kein `RESTORE_SET` und wird nicht zurückgespielt.**
Gemessen als Verweigerung mit Grund; die Alternative — „spiel alles zurück, was drinliegt" — hätte
Dateien überschrieben, die der Installer nur LIEST (`settings.local.json`, `AGENTS.override.md`),
also fremde Bearbeitungen. Betrifft jedes heute im Feld stehende Projekt genau einmal: die erste
Installation nach dieser Runde legt die erste zurückspielbare Sicherung an.

**(c) Ein Defekt, der dabei aufgefallen ist und geschlossen wurde, steht hier, weil er die Grenze
begründet:** `.claude/kit_state.json` — der Vertrauensdatensatz über das Hook-Bundle, den der Lauf
selbst neu schreibt — war weder gesichert noch wiederhergestellt. Ein Abbruch nach
`write_kit_state.py` stellte also das ALTE Bundle wieder her und ließ den Hash des NEUEN daneben
stehen; `doctor` misst `hook_trust` dann gegen ein Bundle, das nicht da ist. Er ist jetzt Teil der
Menge, rot gemessen (`tools/test_kitupdate.py::test_a_rollback_restores_the_previous_bundle_byte_
for_byte` fällt ohne ihn, und seit der Nacharbeit auch
`tools/test_kitupdate.py::test_an_aborted_install_puts_the_trust_record_back_with_the_bundle`, der
den ABBRUCH wirklich fährt statt ihn zu behaupten — der Kommentar im Installer nannte bis dahin
einen Testnamen, den es nicht gab).

**(a3) Die beiden Zwillinge beantworten ein ABSOLUTES Wort in der `RESTORE_SET` nicht gleich**
(neu, TSK-0104, aus einem Prüferrest von TSK-0101, hier nachgemessen statt zitiert). Die Regel im
Code heißt „kein `..`" — eine Aufzählung, wo die Eigenschaft „eine `RESTORE_SET`-Zeile ist
repo-relativ" lautet. Gemessen 2026-09-02 mit genau einer absoluten Zeile in einem echten Manifest,
echter Installer, beide Zwillinge: der POSIX-Zwilling liest sie als repo-relativ (der Aufrufer
übergibt `$REPO/$line`), findet unter diesem Namen nichts in der Sicherung und endet bei **rc 0**
mit unverändertem Baum; der PowerShell-Zwilling endet bei **rc 1**, aber über eine unbehandelte
`GetFullPath`-Ausnahme statt über seine eigene Verweigerung. **Und der POSIX-Zwilling meldet dabei
ERFOLG**: „replayed … (1 recorded path(s))" und „Rollback done." über einen Lauf, der nichts
zurückgespielt hat — dieselbe stille Richtung, die dieser Eintragsstapel bei `H83` als „schlechter
als ein sichtbarer Fehler" einstuft; der Nutzer hält seinen Rollback für gelaufen. **Kein Zwilling
schreibt außerhalb des Repositoriums** — das ist der Unterschied zu (a2), wo eine Datei wirklich gelöscht wurde. Nicht
geschlossen, weil der Fix zwei Zwillinge und einen eigenen roten Lauf je Zwilling braucht (die
PowerShell-Hälfte müsste zusätzlich die Ausnahme zu einer Verweigerung machen) und diese Runde eine
MERGE-Runde ist; die beiden Kommentare sagen jetzt, was gilt, statt Gleichheit zu behaupten.

**(a4) Eine Sicherungs-Aufzeichnung, die NICHT von diesem Installer stammt, löschte Projektdateien
ersatzlos — GESCHLOSSEN (TSK-0104), beide Zwillinge.** `restore_from_snapshot` /
`Restore-FromSnapshot` löschen das Ziel, BEVOR sie nach einer Kopie in der Sicherung sehen.
Gemessen 2026-09-02 an echten Installationen, beide Zwillinge: eine `RESTORE_SET` mit der einzigen
Zeile `docs/note.md` (repo-INTERN, also von jeder Sicherheitsprüfung korrekt durchgelassen), keine
Kopie in der Sicherung → **rc 0, „Rollback done.", Datei weg**.

**Die Lösch-vor-Prüfen-Reihenfolge ist trotzdem richtig, und der falsche Aufrufer hätte hier
beinahe eine falsche Begründung getragen.** Eine wirklich frische Installation schreibt **gar keine**
`RESTORE_SET` (die Sicherung entsteht nur, wenn es etwas zu sichern gab). Die Gestalt „14 von 15
Zeilen ohne Kopie, 12 davon im Projekt" gehört zum ABBRUCH-Rückbau, der die Menge `RESTORABLE`
direkt gegen eine leere Sicherung fährt — dort ist Löschen ohne Ersatz zwingend, und dieser Pfad
liest keine fremden Daten. Der ROLLBACK-Pfad sieht das Manifest der ZWEITEN Installation: gemessen
**15 Zeilen, 2 ohne Kopie** (`.github/hooks`, `.github/agents`, vom Installer angelegt), **0 davon
im Projekt vorhanden**. Auch dort gilt: eine Zeile, die der Installer besitzt, MUSS entfernt werden
dürfen.

**Gebaut, und der Trennschnitt ist ein zweiter, unabhängiger Besitznachweis:** das Manifest kann
nicht sein eigener Beweis sein — es ist das Zweifelhafte. `RESTORABLE` / `$restorable` ist der
Nachweis: die Menge, die das Skript selbst sichert. **Eine Manifestzeile passiert, wenn sie in
dieser Menge steht ODER die Sicherung eine Kopie von ihr hält**; nur wer beides nicht ist, wird
verweigert, mit Nennung der Zeile, in der Schleife, die ohnehin alle Zeilen liest BEVOR die erste
gelöscht wird. Die zweite Hälfte hält die Vorwärtskompatibilität: eine ältere Sicherung, die einen
inzwischen aus `RESTORABLE` gestrichenen Pfad nennt, trägt ihre eigene Kopie und bleibt spielbar.
Gemessen: `RESTORABLE` 15 Namen, Manifest 15 Zeilen, **keine Zeile außerhalb**, also **null
Fehlverweigerungen** an einer echten zweiten Installation. Der Kommentar steht an genau dieser
Schleife in beiden Zwillingen.

**Dabei ist ein zweiter, älterer Defekt aufgefallen und mitgeschlossen — eine BOM.** Der
PowerShell-Zwilling schreibt sein eigenes `RESTORE_SET` **mit** UTF-8-BOM (Bytes `efbbbf`, gemessen).
Der POSIX-Zwilling strippte `CR`, aber nicht die BOM, also war die ERSTE aufgezeichnete Zeile für
ihn ein Name, den es nicht gibt: gemessen am ausgelieferten Kreuzfall **rc 0, „Rollback done.", und
der erste Pfad wurde nie zurückgespielt** — ein Rollback, der Erfolg meldet und eine Datei
auslässt. (Genau daran ist die erste Prüfmessung dieser Runde vorbeigelaufen.) Die BOM wird
**gestrippt und nicht verweigert**, und das ist gemessen entschieden: sie stammt vom eigenen
Zwilling, eine Verweigerung träfe also die eigenen Sicherungen — mit der Besitzregel, aber ohne den
Abstrich verweigert der POSIX-Zwilling das Manifest seines Zwillings bei rc 1. Nach dem Bau spielen
alle vier Schreiber/Leser-Paarungen die erste Zeile korrekt zurück.

**Rot gemessen, je Zwilling** (`tools/test_kitupdate.py::test_neither_twin_replays_a_manifest_line_
it_does_not_own`): Besitzregel entfernt → beide Zwillinge rot (rc 0 statt Verweigerung, Datei weg);
BOM-Abstrich entfernt → POSIX-Zwilling rot. Die Gegenrichtung (ältere Sicherung mit eigener Kopie)
läuft im selben Test, damit die Verweigerung nicht von einem Installer erfüllt wird, der alles
ablehnt.

**Was NICHT geschlossen ist, und dafür gibt es keinen Ersatz:** ein Manifest, das ausschließlich
Pfade aus `RESTORABLE` nennt, aber von fremder Hand stammt, ist von einem echten nicht zu
unterscheiden — dagegen hülfe nur ein Herkunftsnachweis über die Zeilen. Der Schaden wäre dann
allerdings auf die Menge begrenzt, die der Installer ohnehin ersetzt — **plus** die `KEPT_ONLY`-Dateien
(`AGENTS.override.md`, `.claude/settings.local.json`): `backup_local` sichert auch sie, also passiert
ihre Manifestzeile über den Kopie-Zweig, und die Nutzerdatei wird mit der älteren Kopie
überschrieben (gemessen 2026-09-02, beide Zwillinge, `{"old": 1}`). Überschreiben, nicht Löschen;
dieselbe Vorbedingung (fremdes Manifest, `H11`); schließbar mit einer Zeile je Zwilling (den
Kopie-Zweig um `KEPT_ONLY` verengen), in TSK-0104 nicht mehr gemacht. Begrenzt wird das übrige
durch `gate_write_scope` über `.claude/`: eine veränderte Aufzeichnung setzt eine Shell außerhalb
der Sitzung oder einen Defekt voraus, also `H11`s Klasse.

**Urteil: Rest.** Jede Grenze mit dem Ort, an dem sie ausgesprochen ist: (a) und (b) spricht der
Befehl selbst aus, wenn er sie trifft; (a3) steht als Kommentar an `assert_safe_repo_path` in
beiden Zwillingen, mit dieser Messung; (a4) ist GESCHLOSSEN, und sein Kommentar steht an der
Manifest-Schleife des Rollback-Zweigs in beiden Zwillingen (dort, wo die Regel läuft), rot
gemessen je Zwilling; (a2) und (c) sind ebenfalls geschlossen, beide rot gemessen. Offen bleibt
nur der Herkunftsnachweis, benannt am Ende von (a4).

### H89 — Ohne `git` kann die Vier-Augen-Buchung alte von neuen Zeilen nicht unterscheiden und tritt zurück (neu, TSK-0102, FR-0065)

**Mechanismus.** `gate_second_booking` urteilt nur über Ledger-Zeilen, die noch nicht in `HEAD`
stehen. Das ist die Migrationsantwort: ein echtes Buch trägt Zeilen, die vor dieser Schicht gebucht
wurden, und ein Mechanismus, der jede davon verweigert, ist schlechter als keiner (`FR-0065` sagt
genau das). Die Grundlinie ist damit nichts Aufgezähltes und nichts, was sich prägen ließe — der
einzige Weg nach `HEAD` ist ein Commit, und der Commit ist einer der Momente, an denen dieses Gate
steht. Wo `git` aber gar nicht antwortet — nicht installiert, oder ein Verzeichnis, das kein
Arbeitsbaum ist —, gibt es diese Unterscheidung nicht.

**Gemessene Kette.** Ein gescaffoldetes Office-Projekt ohne `git init`, mit einer ungelesenen Zeile
im Ledger: `git commit -m books` durch die volle registrierte Kette → **rc 0**. Dieselbe Zeile mit
`git init` (ohne Commit) → rc 2 mit der Vier-Augen-Verweigerung. Gemessen 2026-09-01,
`tools/test_hooks.py::test_a_ledger_git_cannot_answer_for_stands_the_booking_gate_down_and_says_so`
hält die Rückzugsrichtung fest.

**Warum nicht geschlossen.** Die Gegenrichtung — verweigern, wenn nichts unterscheidbar ist — legt
genau das Projekt still, das den Ausweg am nötigsten braucht: die Verweigerung säße auf dem Commit,
der die Zeilen zu Altzeilen gemacht hätte. Das ist derselbe Fehler, den der Kopf von
`gate_ledger_valid` als „a corrupt marker with no ledger present deadlocked the repo" führt.

**Was stattdessen begrenzt.** Der Rückzug ist nicht still: er wird pro Datei in das Audit-Log des
Projekts geschrieben (`project_memory/.audit/hook_events.jsonl`, `gate_second_booking … stood down
for …`), also dorthin, wo ein Prüfer nachliest, ob eine Schicht überhaupt hingesehen hat. Und die
Voraussetzung ist keine exotische: die Verfassung des Office-Kits macht `git` zur Pflicht (§9,
Commit nach jedem abgeschlossenen PROC-Lauf), das Kit liefert `.gitignore` und `gate_push_token`
mit. Ein Office-Projekt ohne `git` hat ohnehin keinen Prüfpfad — was diese Schicht dort verliert,
hat es vorher schon verloren.

**Urteil: Rest, benannt.** Nicht blockierend nach der Hausregel — die Angriffskette verlangt, dass
der Nutzer sein Projekt ohne Versionsverwaltung führt, und dann fehlt der Nachweis vor dieser
Schicht.

### H90 — Zwei identische Buchungen EINES Belegs teilen sich ein Lesepaar (neu, TSK-0102, FR-0065)

**Mechanismus.** `_bookings` verbindet Lesungen und Zeilen über die Spalte `source` (den Beleg) und
prüft dann Feld für Feld auf Übereinstimmung. Die Spalte `id` ist bewusst ausgenommen (sie entsteht
erst beim Schreiben). Zwei Zeilen, die sich NUR in der `id` unterscheiden, sind damit beide von
demselben Lesepaar gedeckt — also eine Doppelbuchung desselben Belegs, die diese Schicht durchlässt.

**Gemessene Kette.** Zwei Zeilen mit identischen Feldern außer `id`, beide OHNE `invoice_no`, ein
Lesepaar aus zwei Läufen: `git commit` durch die volle registrierte Kette → **rc 0** (gemessen
2026-09-01 in einer Kopie außerhalb des Repos). Mit gesetzter `invoice_no` greift stattdessen
`ledger_add.validate_cross` („duplicate invoice … booked 2 times") und `gate_ledger_valid`
verweigert — die Lücke besteht also genau dort, wo der Beleg keine Rechnungsnummer trägt (Quittung,
Kassenbon).

**Warum nicht hier geschlossen.** Doppelbuchungen sind die Frage des VALIDATORS, nicht der
Vier-Augen-Schicht: die eine fragt „stimmt diese Zeile mit dem Beleg überein", die andere „steht
diese Zeile schon einmal in den Büchern". Die Erkennung im Validator um belegfreie Zeilen zu
erweitern (gleicher Beleg + gleicher Betrag + gleiches Datum = Verdacht) ist ein eigener Eingriff
in `ledger_add.validate_cross` mit eigener Fehlklasse — eine legitime Doppelzahlung derselben
Rechnung existiert —, und in dieser Runde nicht gemessen.

**Was stattdessen begrenzt.** Der Fall braucht einen Beleg ohne Rechnungsnummer UND zwei Zeilen mit
sonst identischen Feldern; die EÜR-Summe wird dadurch doppelt gezählt, was der Bericht-Kommentar
des Bookkeepers („duplicate suspicion") ausdrücklich sucht. Kein Gate misst das.

**Urteil: Rest, benannt** — mit dem Vorschlag, ihn in die Duplikatsregel des Validators zu legen
und nicht in dieses Gate.

### H91 — Der gerenderte Aktenplan-Baum zeigt den PLAN, nicht die Platte (neu, TSK-0102, FR-0031)

**Mechanismus.** `scripts/filing_plan.py --tree` und der Ablage-Abschnitt der
Verfahrensdokumentation rendern die `path_template`s der Regeln. Das ist gewollt — der Baum IST der
Plan, so hat der Nutzer es gesteuert — aber es heißt auch: ein Ordner, der unter `archive/`
tatsächlich EXISTIERT und von keiner Regel gedeckt ist, kommt in dem Bild, das dem Nutzer als
„sichtbare Wahrheit" vorgelegt wird, nirgends vor.

**Gemessene Kette.** Projekt mit einer Regel `archive/supplier_invoice/<year>/`, dazu ein real
angelegtes `archive/alte_ablage/2019/x.pdf`: `--tree` gibt rc 0 aus und zeigt ausschließlich den
Regelbaum; die Zeichenkette `alte_ablage` steht nirgends darin (gemessen 2026-09-01). Ebenso zeigt
der Baum Platzhalter (`<year>`) und keine wirklichen Jahresordner — er beschreibt die Form, nicht
den Bestand.

**Warum nicht geschlossen.** Ein Abgleich Plan↔Platte ist eine andere Frage als „wie sieht die
Ablage aus" und gehört zu einer Prüfung (der `project-auditor` prüft laut Verfassung den Archivbaum
gegen `filing_plan.yaml`), nicht zum Renderer. Ihn hier einzubauen hieße, den Renderer beim
Onboarding über einen leeren Archivbaum urteilen zu lassen.

**Was stattdessen begrenzt.** `gate_filing` verweigert jede Ablage, die keine Regel deckt — ein
ungedeckter Ordner kann also nur aus der Zeit vor dem Kit stammen oder von Hand außerhalb der
Werkzeuge entstanden sein. Die Ausgabe des Renderers sagt in ihrer Kopfzeile ausdrücklich, dass sie
das Archiv „as `project_memory/filing_plan.yaml` describes it" zeigt.

**Urteil: Rest, benannt.**

### H92 — Der Wurzel-Leser des Kernels löste EINEN Sprung auf, die Forschungskette ist zwei tief — GESCHLOSSEN (TSK-0106)

**Mechanismus:** `report._root_of` beantwortet „woran hängt dieses Item" mit dem **einen
unmittelbaren Elternteil** (`parents[0] if len(parents) == 1 else None`), während
`report._hangs_from` dieselbe Frage **transitiv** beantwortet.
`dispatch._assert_task_origin_matches_root` benutzt den ersten. Damit ist die Hierarchie, die die
research-Verfassung §4 vorschreibt — `RQ → HYP → EXP → TSK` — nicht anlegbar: der Ursprung `EXP`
hat für die Prüfung die Wurzel `HYP`, für jede andere Stelle die Wurzel `RQ`.

**Kette (gemessen 2026-09-01 in einem frisch gescaffoldeten research-Projekt, Rohdaten unter
`_round-scratch/TSK-0103/`):**

```
$ python scripts/harness.py create-task --product-requirement RQ-0001 --derives-from EXP-0001 ...
rc=1  derives_from EXP-0001 belongs to HYP-0001, not to this task's root RQ-0001 -- refused at
      creation (spec II.8). ... Remedy: create the task under HYP-0001, or name an origin that
      hangs from RQ-0001

HYP-0001 parents=['RQ-0001']   _root_of=RQ-0001    _hangs_from(RQ-0001)=True
EXP-0001 parents=['HYP-0001']  _root_of=HYP-0001   _hangs_from(RQ-0001)=True
```

**Wer hier recht hat, ist entschieden, und es ist nicht der Kernel.** `cli.py:484` führt `EXP`
selbst als legalen Ursprung („the item whose criteria this task serves (root, BUG, CR, EXP)"),
`cli.py:482` nennt `--product-requirement` „the PR/RQ root this task serves", und die Verweigerung
oben formuliert ihren eigenen Ausweg **transitiv** („name an origin that hangs from RQ-0001").
Drei Stellen des Kernels beschreiben also das Verhalten, das `_root_of` nicht liefert.

Warum es nie ein Test gesehen hat: im dev-Kit liegt jeder Aufgaben-Ursprung genau eine Ebene unter
der Wurzel (`PR → SR → TSK`, `PR → BUG`, `PR → CR`), da fallen die beiden Leser nie auseinander.
Das research-Kit ist das einzige ausgelieferte mit einer tieferen Kette.

Als laufende Messung war die Lücke in `tools/test_research_chain.py` gepinnt, mit der Auflage im
eigenen Docstring, den Test zu INVERTIEREN, sobald sie geschlossen ist. Das ist in derselben
Änderung geschehen — siehe unten.

**Was gebaut wurde (TSK-0106), als EIGENSCHAFT statt als zweiter Sprung:** `_root_of` ist ersetzt
durch `report.origin_root_conflict`, und die Frage lautet nicht mehr „welches Item ist die Wurzel
dieses Ursprungs", sondern „gehört dieser Ursprung zu DIESER Wurzel". Beantwortet wird sie mit
`_reaches_on_every_path` — dieselbe Wanderung wie `_hangs_from`, aber mit `all` statt `any`, weil
der Vergleich eine Zugehörigkeit braucht und keine Erreichbarkeit. Beide Aufrufer benutzen
dieselbe Funktion (`dispatch._assert_origins_belong_to_root_locked` importiert sie), also kann der
Anlege-Weg nicht verweigern, was `validate` durchlässt.

**Gegenmessung (2026-09-02, im Klon außerhalb des Repos, alte Ein-Sprung-Fassung
wiederhergestellt):** `test_kernel.test_a_task_may_derive_from_an_experiment_two_levels_under_its
_root` fällt mit der ursprünglichen Verweigerung „belongs to HYP-0001", und
`test_report.test_a_task_on_an_origin_two_levels_under_its_root_is_fine` mit einem Validator-Error
auf demselben Item. Auf dem gescaffoldeten research-Projekt läuft die Kette jetzt end-to-end durch
(`tools/test_research_chain.py`, 10 Tests grün) — und der Pin-Test dieser Lücke ist invertiert, wie
sein eigener Docstring es verlangt hatte: er heißt jetzt
`test_a_task_may_name_an_experiment_two_levels_under_the_question_it_serves` und misst beide
Richtungen, den Erfolg und die weiterhin richtige Verweigerung unter einer fremden Frage.

**Urteil: geschlossen, mit Rot-Beweis.** Die Kette läuft nicht mehr; die zwei Auswege, die sie
erzwang, sind mit H93 und H95 zugleich geschlossen. Was NICHT mitgeschlossen ist und auch nicht
behauptet wird: dass `evidence_covers` seine eigene `any`-Wanderung behält — das ist Absicht und
steht an `_reaches_on_every_path` als der Unterschied, den die beiden Fragen haben.

### H93 — Die Freigabe, auf die der genannte Ausweg zwang, gibt es laut Kernel und Verfassung nicht, sie unterschrieb keinen Inhalt und sie starb nie — GESCHLOSSEN (TSK-0106)

**Mechanismus:** Der Ausweg, den die H92-Verweigerung nennt („create the task under HYP-0001"),
führt auf eine Aufgabe, deren Wurzel eine `HYP` ist. `dispatch` verlangt dafür eine Scope-Freigabe
auf der `HYP`. Drei Stellen sagen, dass es die nicht gibt: die research-Verfassung §4 („`HYP` rides
on the RQ's scope approval and carries no approval of its own"),
`backlog_types.INVALIDATION_TARGET` („HYP deliberately absent") und
`approvals.APPROVAL_TRANSITIONS`, das kein `("HYP", …)`-Paar führt. `request-approval scope
HYP-0001` läuft trotzdem, und der Haken prägt.

**Kette (gemessen 2026-09-01, echte Hook-Prozesse):**

```
$ python scripts/harness.py dispatch TSK-0002
rc=1  no user approval authorises dispatching TSK-0002 under HYP-0001 ...
      Remedy: obtain the scope approval for HYP-0001, ...
$ python scripts/harness.py request-approval scope HYP-0001   -> rc 0, Frage wird gestellt
   gate_approval.py (PostToolUse)                             -> approval APR-0004 recorded
$ python scripts/harness.py dispatch TSK-0002                 -> rc 0, HARNESS_DISPATCH ...

$ harness update HYP-0001 {"statement": "GEAENDERT: ..."}  -> rev 1, approval_ref: APR-0004
$ harness update RQ-0001  {"motivation": "GEAENDERT"}      -> rev 2, approval_ref: -, Status DRAFT
```

**Drei Eigenschaften, und die dritte ist die schlimmste:**

1. Der Nutzer unterschreibt **keinen Inhalt**. `item_subject_manifest` schneidet für `scope` gegen
   `approvals._SCOPE_FIELDS`; eine `HYP` trägt davon **kein einziges** Feld. Der sha256, den die
   Frage nennt, läuft also über Identität und Revision, nicht über die Aussage der Hypothese.
2. Die Freigabe **stirbt nie**. `HASHED_FIELDS` führt kein `HYP`, also bewegt keine Änderung an
   `statement` oder `testable_prediction` die Revision, und nichts entwertet die Freigabe. Wer die
   Hypothese nach der Freigabe umdreht, dispatcht weiter unter der alten Zustimmung — die
   Gegenprobe an der `RQ` in derselben Messung zeigt, wie es aussähe, wenn es griffe.
3. Die Aufgabe **entzieht sich der QA-Schuldprüfung**. `report.accepted_without_a_verdict` sammelt
   nur Aufgaben, deren Wurzeltyp in `ROOT_TYPE_BY_KIT.values()` liegt (`report.py:1509-1511`,
   `delivery_roots`). Eine Aufgabe unter einer `HYP` fällt heraus und wird nie als „akzeptiert ohne
   Urteil" gemeldet.

**Was gebaut wurde (TSK-0106), an der TüR statt an den drei Symptomen:**
`approvals._assert_the_pair_commits_an_edge` läuft, sobald `create_pending_request` den Gegenstand
AUS DEM ITEM bildet, und verweigert jedes `(Typ, Art)`, das `APPROVAL_TRANSITIONS` nicht führt.
Damit ist die Frage gar nicht mehr stellbar — der Nutzer sieht keine Freigabe-Frage, deren Antwort
nichts kauft (dieselbe Form, die BUG-0039 festhält). Der Gegenstand wird VOR der Prüfung gebildet,
damit eine Art, die überhaupt nicht item-abgeleitet ist, ihre eigene Verweigerung behält.

**Warum nicht der andere Weg (HYP in `HASHED_FIELDS`, echter Gegenstand):** die drei Stellen, die
BUG-0084 nennt, sagen einstimmig, dass es diese Freigabe nicht gibt — Verfassung §4,
`INVALIDATION_TARGET` („HYP deliberately absent") und `APPROVAL_TRANSITIONS`. Eine Freigabe zu
BAUEN, die drei Verträge verneinen, wäre eine Spec-Änderung, keine Fehlerbehebung.

**Was von Punkt 3 bleibt, und es bleibt absichtlich:** `report.accepted_without_a_verdict` leitet
seine Wurzeltypen weiterhin aus `ROOT_TYPE_BY_KIT` ab — die Zeile war bereits abgeleitet, nicht
aufgezählt (der Befund las den abgeleiteten WERT `{PR, RQ}`). Eine Aufgabe unter einer `HYP` fällt
also weiter heraus, und das ist richtig so: das Kit, dessen Projekte an keiner solchen Wurzel
hängen, kann die Schuld nicht bezahlen (das büro-Kit ist der gemessene Fall). Der Ausweg dorthin
ist zu, nicht der Filter aufgeweicht. Neu gemessen wird die INKLUSIONS-Richtung, die vorher nichts
prüfte: `test_report.test_a_task_under_every_kit_root_is_asked_for_its_delivery_verdict` fällt,
sobald man `delivery_roots` durch die Aufzählung `{"PR"}` ersetzt (im Klon nachgemessen).

**Gegenmessung (2026-09-02, Klon außerhalb des Repos):** ohne den Aufruf im Anforderungspfad ist
`test_approvals_dispatch.test_a_hypothesis_cannot_be_given_a_scope_approval` rot („DID NOT RAISE");
mit dem Aufruf, aber einer um `HYP`/`SR` erweiterten Ausnahme im Urteil ist zusätzlich
`test_approvals_dispatch.test_no_item_type_can_be_approved_on_a_kind_that_commits_no_edge` rot. Die
beiden Enden sind getrennt mutiert, weil ein Stolperdraht, dessen eines Ende aus dem anderen folgt,
Prosa ist (DEC-0060 Regel 4).

**Urteil: geschlossen, mit Rot-Beweis.** Was NICHT geschlossen ist und hier steht, statt im
Kommentar zu fehlen: ein Paar, das die Tabelle FÜHRT, verspricht nur die KANTE, nicht dass sein
Gegenstand den Inhalt des Items beschreibt — `PROC/scope` und beide `delivery`-Gegenstände decken
ein Feld ihres Typs oder keines (gemessen über alle zehn Paare, an `APPROVAL_TRANSITIONS`
niedergeschrieben). Das ist die alte, benannte Enge von `_SCOPE_FIELDS` und wird von dieser Runde
nicht berührt.

### H94 — Der gerenderte Forschungsbericht hatte keinen Schreibweg, während der Merge auf ihm bestand — Weg gebaut (TSK-0106), Verfassungszeile offen

**Mechanismus:** Die research-Verfassung §6 gibt `reports/EXP-*.{tex,pdf,html}` und
`reports/fzulg_application_RQ-*.md` dem **Report-Writer**; §17 macht den gerenderten Bericht zur
Vollständigkeitsbedingung eines Experiments. Der Merge hängt daran:
`report._check_experiment_reports` (`report.py:1543-1560`) meldet als **error**, was in `ANALYZED`
steht und **leere** `evidence_refs` hat, und `gate_memory_complete` liest den Validator auf der
Merge-Zeile. Gleichzeitig verweigert `gate_write_scope` jeden Werkzeug-Schreibzugriff unter
`project_memory/` und macht für dieses Fach keine Ausnahme — §0 der Verfassung sagt das
ausdrücklich.

**Kette (gemessen 2026-09-01, `gate_write_scope.py` hinter `_gate.py`, echte Payloads):**

```
Write project_memory/reports/EXP-0002.tex                   -> rc 2
Write project_memory/reports/fzulg_application_RQ-0001.md   -> rc 2
Write project_memory/staging/TSK-0001/EXP-0002.tex          -> rc 0
Write reports/EXP-0002.tex                                  -> rc 0
```

Wortlaut der Verweigerung: „the TOOL route into such a file does not exist … No `python
scripts/harness.py` command writes this one either, so this write has no route from inside this
session." Der angebotene Ausweg — „filled by the entry gate BEFORE the kit is installed, or by the
user in an editor outside this session" — passt auf die Masterplan-Klasse, aber nicht auf einen
Bericht je Experiment, den es beim Onboarding noch nicht gibt.

**Genau formuliert, damit es nicht überzeichnet ist:** der Merge blockt auf einem **leeren Feld**,
nicht auf der Existenz einer Datei. Ein `evidence_refs`, das eine Evidenz nennt, die den Bericht
vertritt, genügt ihm — und diese Evidenz kann ein Artefakt unter `staging/<TSK-ID>/` oder in einem
`reports/` außerhalb des Zustandsverzeichnisses referenzieren. Was fehlt, ist nicht der Merge,
sondern der Weg an den Ort, den §6 und §17 nennen.

**Was gebaut wurde (TSK-0106):** `staging.freeze_report`, als vierte Freeze-Operation und damit
auf der Kommandozeile am Tag ihrer Entstehung — `cli.FREEZE_OPERATIONS` leitet Name, `--help` und
Body-Vertrag aus der Signatur ab. Der Report-Writer rendert wie bisher nach
`staging/<TSK-ID>/<name>` (rc 0, unverändert) und `python scripts/harness.py freeze-report` legt
die Bytes in `reports/` ab. Drei Eigenschaften, die aus dem Kopieren eine Zustandsänderung machen:
der Pfad wird an `evidence_refs` des Gegenstands angehängt, WENN dessen Feldvertrag dieses Feld
führt (abgeleitet aus `DECLARED_REQUIRED_FIELDS`, heute die `EXP` — genau das Feld, auf dem
`gate_memory_complete` den Merge blockt); ein Projekt ohne dieses Fach wird verweigert statt
beschenkt; und ein bereits abgelegter Bericht wird NIE überschrieben, weil ausgeliefertes Material
die Klasse ist, die DEC-0056 (c) auf voller Sorgfalt hält.

**Gegenmessung (2026-09-02, Klon außerhalb des Repos, `freeze-report` wieder ausgetragen, Kit im
Klon neu gestempelt, damit der Scaffold nicht schon an der Signatur scheitert):**
`tools/test_research_chain.py -k reaches_the_tray` ist rot mit rc 2 und einer Befehlsliste ohne
`freeze-report` — der Zustand vor dieser Runde. Grün misst derselbe Test die ganze Kette an
echten Prozessen: Werkzeug-Schreibzugriff auf das Fach rc 2 (bleibt richtig), auf `staging/` rc 0,
`freeze-report` rc 0, Datei im Fach, `evidence_refs` gesetzt, `scripts/report_lint.py` findet den
Bericht unter seinem Namen — der zweite Leser desselben Fachs, womit die Kernel-Konstante und die
Form, die der Lint sucht, aneinander gebunden sind — und der Merge blockt danach nicht mehr auf
`ANALYZED without evidence_refs`.

**Urteil: offen, und was offen ist, ist genau eine Zeile Verfassungstext.** Der Weg existiert und
ist gemessen; §6 und §17 NENNEN ihn nicht, also findet ein Report-Writer ihn heute nur über
`harness.py --help`. Diese Zeile gehört Stream E (Verfassungen sind `forbidden_scope` dieser
Runde) und steht als Seam-Item im TSK-0106-Protokoll. **Was heute begrenzt:** nichts an der Sache
mehr — der Weg ist da; begrenzt ist nur, wie schnell die Rolle ihn findet. **Unberührt
weiterbestehend:** das Preset `solo` installiert keinen `report-writer` (`presets.yaml`), also
fehlt in dieser Aufstellung die Rolle, nicht der Weg.

### H95 — Die Ursprungsprüfung des Dispatchs fiel bei MEHRDEUTIGER Elternschaft offen aus, in allen Kits — GESCHLOSSEN (TSK-0106)

**Mechanismus:** `report._root_of` gibt `None` zurück, sobald ein Item **mehr als ein**
Bindungsfeld gefüllt hat (`report.py:934-941`, `parents[0] if len(parents) == 1 else None`).
`dispatch._assert_task_origin_matches_root` prüft `if origin_root and origin_root != root["id"]`
(`dispatch.py:176-177`) — bei `None` wird die Prüfung stillschweigend übersprungen. Die Prüfung,
die verhindern soll, dass eine Aufgabe gegen die Kriterien einer **fremden** Wurzel gemessen wird,
fällt also nicht zu, sondern auf.

**Kette (gemessen 2026-09-01 vom Prüfer in seinem eigenen Rig):**

```
$ harness capture EXP {"derives_from": ["HYP-0001", "RQ-0001"], ...}  -> EXP-0004, _root_of = None
$ harness create-task --product-requirement RQ-0002 --derives-from EXP-0004 ...  -> rc 0
$ harness validate                                                    -> 0 error(s)
   Kontrolle, dasselbe Experiment einelterig:                         -> rc 1
```

**Zwei Eigenschaften, die es größer machen als es aussieht:**

* **Kit-unabhängig.** Betroffen ist jeder Typ, dessen Bindungsfeld eine LISTE tragen darf —
  `SR.derives_from` zum Beispiel —, nicht nur die research-Kette.
* **Es verschwindet nicht mit H92.** Der Prüfer hat H92 im Klon geschlossen (transitiver Term in
  `_assert_task_origin_matches_root`); der Weg oben blieb rc 0. Die erste Fassung dieses Befundes
  im Pilotdokument behauptete das Gegenteil und war falsch.

**Was gebaut wurde (TSK-0106):** `report.origin_root_conflict` kennt `None` als Antwort nicht
mehr. Ein Ursprung gehört zur Wurzel, wenn JEDER seiner Elternpfade dort endet
(`_reaches_on_every_path`, `all` statt `any`, zyklensicher, und eine Sackgasse ist ein Nicht-
Ankommen wie jedes andere). Drei Fälle, drei Sätze: alle Pfade führen hin → angenommen; keiner
→ „belongs to X"; ein Teil → die MEHRDEUTIGKEIT wird benannt, samt dem Elternteil, der wegführt,
weil die Abhilfe eine andere ist als beim Fremdwurzel-Fall.

**Miterledigt, und von dieser Runde selbst gefunden statt gemeldet:** derselbe `None` stand auch
für „GAR KEIN Elternteil". Ein Ursprung, der selbst eine Wurzel ist — ein zweites `PR` — wurde
unter jeder anderen Wurzel angenommen, mit exakt demselben Schaden (der Dispatch-Gate löst
`acceptance_refs` gegen den Ursprung auf). Sichtbar wurde es daran, dass sieben Fixture-Zustände in
`tools/test_approvals_dispatch.py` rot wurden, die `PR-0001` als Ursprung unter einer anderen
Wurzel nannten, weil das nie jemand verweigert hatte. Die Fixtures nennen jetzt ihre eigene Wurzel;
der Fall hat einen eigenen Test.

**Gegenmessung (2026-09-02, Klon außerhalb des Repos, alte Ein-Sprung-Fassung wiederhergestellt):**
`test_kernel.test_an_origin_with_a_parent_outside_the_root_is_refused_at_creation` — „DID NOT RAISE
DispatchError"; `test_kernel.test_a_task_may_not_derive_from_a_ROOT_item_of_another_tree` ebenso;
`test_report.test_an_origin_that_reaches_the_root_through_only_one_of_its_parents_is_refused` —
kein Finding. Die Gegenrichtung ist eigens gemessen, damit die Verweigerung nicht in „jeder
mehrelterige Ursprung ist verboten" verfällt: die Kette, die das research-E2E läuft, hängt an
Hypothese UND Frage und bleibt anlegbar
(`test_kernel.test_an_origin_whose_parents_all_hang_from_the_root_is_still_creatable`).

**Urteil: geschlossen, mit Rot-Beweis, in beide Richtungen gemessen.** Was NICHT mitgeschlossen
ist: `_hangs_from` behält sein `any` — es beantwortet die andere Frage („erreichbar", für die
Bindung einer Evidenz an ihre Wurzel), und die beiden zusammenzulegen wäre dieselbe Verwechslung
in die andere Richtung.

### H99 — H11 hebt die Vier-Augen-Buchung mit auf: ein Skript trägt eine ungelesene Zeile nach `HEAD` und prägt die zweite Lesung (neu, TSK-0102, FR-0065)

**Mechanismus.** `gate_second_booking` ruht auf zwei Annahmen, und beide sind Ableitungen aus
`H11`s Interpreter-Ausnahme, nicht aus einer eigenen Schranke:

1. **Die Grundlinie ist `HEAD`**, und was `HEAD` bewegt, sieht die Schicht nur so weit, wie
   `gate_ledger_valid.requires_a_sound_ledger` einen Commit an der *Befehlszeile* erkennt. Ein
   Commit, den ein SKRIPT ausführt, steht nicht in dieser Zeile — dieselbe Stelle, an der `H11`
   schon Gate 3 aushebelt.
2. **Die Attestierung liegt in `project_memory/.books/`**, wohin `gate_write_scope` jede *direkte*
   Schreibweise verweigert — aber nicht das Skript, das sie ausführt.

Bis zu dieser Runde behaupteten `_bookings.py`, die ENFORCEMENT-Zeile und ein Test-Docstring
wortgleich das Gegenteil: „no snapshot can be minted: the only way into `HEAD` is a commit, and a
commit is one of the moments this gate stands in". Das ist gemessen falsch und der Satz ist an allen
drei Stellen gestrichen; was dort jetzt steht, ist die Ableitung als das, was sie ist.

**Kette A, gemessen (2026-09-01, eigenes Rig gegen die Kette aus der ausgelieferten
`settings.json`, Wegwerf-Projekt außerhalb des Repos), ungelesene 14,28-Zeile im Ledger:**

```
git commit -am books                       rc 2   VERWEIGERT (Vier-Augen)
printf 'git add -A\ngit commit -m books\n' > release.sh    rc 0
bash release.sh                            rc 0   DURCHGELASSEN
  → die ungelesene Zeile steht in HEAD
git commit -m more   (echter Commit)       rc 0   DURCHGELASSEN — die Zeile ist ab jetzt
                                                   dauerhaft ausgenommen, mit NULL Lesungen
```

**Kette B, gemessen, dasselbe Vehikel gegen die Attestierung.** Zuerst jede DIREKTE Schreibweise
gegen `project_memory/.books/readings.jsonl`, alle **rc 2**: `echo >>`, `cp`, ein Glob
(`.books/*.jsonl`), `sed -i`, `tee -a`, `python -c`, `cd project_memory && echo >>` — dazu ein
`Write` und ein Append-Redirect aus der Runde selbst. Dann:

```
ein attestierter Lauf, Zeile 14,28        rc 2   VERWEIGERT (eine Lesung, zwei nötig)
bash mint.sh   (heredoc-Append an den Store)   rc 0   DURCHGELASSEN
git commit -m books                        rc 0   DURCHGELASSEN — die falsche 14,28 ist gebucht
```

**Eine Begrenzung, die beim Nachmessen sichtbar wurde und die die Kette teurer macht, als sie
aussieht:** der Store ist **erste-Zeile-gewinnt je (Datensatz, sha256)**. Eine gefälschte Zeile über
DENSELBEN Datensatz ändert darum gar nichts (gemessen: Commit blieb rc 2). Wer prägen will, muss den
Datensatz erst KOPIEREN und die Kopie attestieren — die Kopie selbst ist ein gewöhnlicher
`staging/`-Schreibzugriff und braucht keinen Trick. Es sind also drei bewusste Schritte, nicht einer.

**Warum nicht geschlossen.** Genau aus `H11`s Grund, und dieses Gate kann ihn nicht enger machen als
die beiden Gates, auf denen es aufsitzt: die Interpreter-Ausnahme ist unverzichtbar (ohne sie
verweigert Gate 1 jede dokumentierte Zeile dieses Repos), sie liegt in `gate_write_scope` und in
`gate_ledger_valid`, und beides sind Dateien, die diese Schicht nicht besitzt. Eine eigene Antwort
hier — etwa „jeder Interpreteraufruf verweigert, wenn ein Ledger unlesbare Zeilen trägt" — wäre
Gerüst über dem Haus (DEC-0056) und würde das Kit für jede legitime Skriptnutzung stilllegen.

**Was stattdessen begrenzt.**
* **Absicht statt Versehen.** Beide Ketten verlangen, dass jemand eine Skriptdatei schreibt und sie
  fährt. Kein Irrtum eines Bookkeepers landet hier; die Fehlklasse, für die FR-0065 gebaut ist
  (BUG-0072: der Extraktor liest die falsche Zahl), läuft vollständig durch die Schicht.
* **Sichtbarkeit im Commit.** Das Vehikel ist eine Datei im Arbeitsbaum. `release.sh`/`mint.sh`
  stehen im Diff, den Gate 3 hasht und den ein Prüfer liest — anders als eine Befehlszeile, die
  nirgends bleibt.
* **Rollentrennung und Item**, also dasselbe, was `H11` selbst als einzige verbleibende Begrenzung
  nennt: keine technische.

**Urteil: blockierend nach der Hausregel — die Kette läuft innerhalb einer Sitzung durch. Als
benannte Ausnahme geführt, Abnahme des Nutzers offen**, mit demselben Begründungsstand wie `H11`,
dessen Klasse sie ist. Der Zusatz gegenüber `H11` ist die FOLGE: dort war es „ein Skript schreibt
eine geschützte Datei" und „ein Skript stellt eine Freigabe aus", hier ist es „ein Skript hebt die
Vier-Augen-Prüfung der Zahlen auf, die ans Finanzamt gehen" — und die ausgenommene Zeile bleibt
ausgenommen, auch wenn nie wieder ein Skript läuft.

### H105 — Das Rollengedächtnis des Bookkeepers war ein Kanal zwischen erster und zweiter Lesung, den `gate_second_booking` nicht sieht — GESCHLOSSEN (TSK-0105, FR-0064), mit benanntem Rest

**Mechanismus.** `gate_second_booking` zählt Lesungen je LAUF — zwei `booking_reading`-Datensätze aus
zwei verschiedenen Läufen (office-Verfassung §2.3) —, und die zweite Lesung ist ein zweiter Spawn
DERSELBEN Rolle. Ein Rollengedächtnis (`memory: project` im Frontmatter) lädt der Provider zu Beginn
jedes Laufs dieser Rolle; was der erste Lauf hineinschreibt, hat der zweite gelesen, bevor er das
Dokument öffnet. Das Gate vergleicht Läufe, nicht Aufmerksamkeiten — seine ENFORCEMENT-Zeile sagt
das über sich selbst —, und dieser Kanal lag außerhalb seines Blicks. Bis zu dieser Runde trug
`agents/bookkeeper.md` den Schlüssel, ebenso `quality-engineer.md` (dev) und `reviewer.md`
(research), deren Urteil die Frische aus demselben Grund braucht: ein Urteil, das die Freigaben der
letzten Runde erinnert, ist keine frische Lesung (FR-0064; im echten Projekt Canyon_3.4.0 hielt das
Gedächtnis der QS-Rolle elf Themen, drei davon Gate-Entscheidungen).

**Kette (gemessen 2026-09-02, die ausgelieferten office-Hooks 2026.09.02-10 als echte Prozesse
gegen ein Wegwerfprojekt unter `_round-scratch/TSK-0105/memory-channel-proj`; Payload
`agent_type: bookkeeper`, `Write` nach `.claude/agent-memory/bookkeeper/amazon-invoice-footer.md`):**

```
Notiz mit den Zahlen EINES Belegs (Rechnung 302-4471: brutto 214,20 / netto 180,00 / 19 %),
gegen JEDE der sechs auf Write registrierten Stufen der office-settings.json, je als eigener Prozess:
  gate_write_scope.py               rc 0   DURCHGELASSEN  (Regel 6: eigenes Rollengedächtnis)
  guard_memory_budget.py            rc 0   DURCHGELASSEN  (die Inhaltsregel kennt Item-Ids, keine Zahlen)
  guard_no_adhoc.py                 rc 0   DURCHGELASSEN
  guard_pm_scope.py                 rc 0   DURCHGELASSEN
  guard_harness_selfmod.py          rc 0   DURCHGELASSEN  (das Gedächtnis ist die gewollte Ausnahme)
  gate_filing + gate_second_reading rc 0   DURCHGELASSEN  (kein Ablage-Ziel)
dieselbe Notiz + "booked under TSK-0007"
  guard_memory_budget.py            rc 2   VERWEIGERT — wegen der Id, nicht wegen der Zahlen
```

**Was geschlossen ist, und womit.** Der Schlüssel ist aus jeder Rolle entfernt, deren Lesung frisch
sein muss, und WELCHE das sind, ist abgeleitet und nicht aufgezählt: die Verdict-Rollen aus
`gate_subagent_output.VERDICT_ROLES` (die Konstante, auf der der Hook entscheidet) und jede
`writer_role` eines Kernel-Schemas (die Datensätze, die ein Gate je Lauf zählt oder eine zweite
Rolle beurteilt). Gehalten von
`tools/test_role_contracts.py::test_no_role_whose_reading_must_be_fresh_carries_a_craft_memory`;
rot gemessen im Klon mit dem Schlüssel zurück auf `quality-engineer.md` (1 failed), zurück auf
`bookkeeper.md` (1 failed) und mit dem Pflichtsatz „Consult your agent memory" zurück im
Reviewer-Text ohne Schlüssel (1 failed); Grundlinie 5 passed.

**Rest, benannt.** (a) **Die Schreibseite bleibt offen**: dieselbe Notiz gegen dieselben sechs
Stufen NACH der Schlüssel-Entfernung — alle rc 0. Regel 6 des Schreib-Gates öffnet das Fenster an
der Existenz der Rollendatei, nicht am Schlüssel (gemessen: `agents/bookkeeper.md` entfernt,
`gate_write_scope` rc 2). Abgestellt ist damit das LADEN im nächsten Lauf, und das tut der
Provider anhand des Frontmatters — gemessen ist hier das Frontmatter, nicht der Provider. Enger
würde es in `gate_write_scope` (Regel 6 liest den Schlüssel mit): eine Hook-Datei, außerhalb dieses
Streams, als Nahtstelle gemeldet. (b) **Ein Gedächtnisbaum, den eine frühere Kit-Version dieser Rolle
geschrieben hat, bleibt liegen**: kein Installer (`install.sh`/`.ps1`), kein Scaffold
(`scaffold_team.sh`/`.ps1`) und kein Kernel-Pfad (`kernel/*.py`) nennt `agent-memory` — gemessen per
grep durch den Prüfer —, also nimmt ein Update auf -11 den Schlüssel und lässt den Baum stehen;
Canyon_3.4.0 trägt heute zwölf solche Dateien für `quality-engineer`. Ob der Provider ein
vorhandenes Verzeichnis OHNE Schlüssel lädt, ist ausdrücklich nicht gemessen. Für bestehende
Installationen ist das Laden damit am Frontmatter abgestellt und am Provider offen; das Entfernen
beim Update ist Kernelarbeit (`kitupdate`), außerhalb dieses Streams, als Nahtstelle gemeldet. Ein
Verzeichnis, das ein Nutzer von Hand anlegt, ist derselbe Fall. (c) Was das Gedächtnis dieser Rollen an Handwerk hielt (im echten
Projekt: Playwright-Fallen, ein ablaufendes Dev-Server-Token) geht dem Projekt verloren; es gehört
ins Skill der Rolle. Ob ein Urteil durch das Erinnern je gedriftet ist, wurde NICHT gemessen — die
Entscheidung stützt sich auf den gemessenen Kanal, nicht auf eine gemessene Drift.

**Urteil: GESCHLOSSEN (TSK-0105) für NEUE Installationen; für bestehende ist das Laden am
Frontmatter abgestellt und am Provider nicht gemessen, mit benanntem Rest auf der Schreibseite**
— der Kanal, für den die Vier-Augen-Regel gebaut ist (ein Versehen des ersten Lesers färbt den
zweiten), ist am Schlüssel abgestellt und per Ableitung gehalten; der Baum, den ein älteres Kit
schrieb, ist die Grenze dieser Messung.

### H106 — Der Umfang eines QS-Laufs ist Prosa: kein Feld und kein Hook zählt, ob die Suite einmal oder zehnmal lief (neu, TSK-0105, FR-0057)

**Mechanismus.** Das Maß aus DEC-0050 — betroffene Tests, solange die Runde offen ist; der volle
Lauf EINMAL vor dem Urteil — steht seit dieser Runde dort, wo die Verdict-Rolle es liest: in der
`description` ihres Frontmatters (was ein Spawn zuerst sieht) und im `## Do` ihres Skills, dazu als
Klausel am GATE-Schritt der Verfassung (§5a.7) und als Leiter im PM-Skill. Nichts davon liest ein
Hook. Der Evidence-Datensatz trägt `--summary` (Freitext) und `--artifact-ref` (einen Pfad); ein
Feld für den Umfang oder die Nummer eines Laufs gibt es nicht, und kein Hook zählt Befehlszeilen
über eine Sitzung.

**Kette (gemessen).** Im echten Projekt Canyon_3.4.0 (dev-Kit 2026.08.24-7, 46 Tasks) ist die
EINZIGE Spur dessen, was die QS lief, ihr eigenes Staging: `staging/TSK-0044/gate_run_log.md`
zählt 15 Instrumente für einen Gate-Lauf, `quality_full_run.txt` EINEN vollen Pipeline-Lauf
(141,63 s, im Hintergrund) — also das Maß, das Schritt 3 des QS-Skills vorschreibt; die Nachweise
der Entwickler (dort `EVD-0028`, `EVD-0033`) blieben auf dem betroffenen Stack
(`quality.py --only liquid`). Das Gegenbeispiel ist dieses Repo selbst: an TSK-0083 lief die volle
Suite in sechs Runden mit, rund vier Stunden, und kein Befund kam aus ihr (DEC-0050). Beides sieht
kein Gate; beides steht nur in Protokollen.

**Was stattdessen begrenzt.** Der Rollentext, beide Hälften, per Test gehalten:
`tools/test_role_contracts.py::test_every_verdict_role_states_the_scope_of_its_runs` — rot
gemessen im Klon: „affected" aus der QS-Beschreibung gestrichen (1 failed), der
Staged-Testing-Satz aus dem `## Do` des QS-Skills geschnitten (1 failed), der Umfangssatz aus dem
Reviewer-Skill geschnitten (1 failed). Ein Zähl-Gate wäre Kernelarbeit — ein Feld im
Evidence-Schema, das Teillauf von Volllauf unterscheidet, wonach FR-0040 fragt — und Gerüst über dem
Haus, solange der gemessene Fehler im Kit-Projekt nicht auftritt (DEC-0056 b).

**Urteil: Rest, benannt** — keine Kette öffnet innerhalb einer Sitzung etwas; der Fehler ist
Kosten, nicht Zustand, und der Ort, an dem er zählbar würde, ist der Kernel.

### H107 — Der Design-Brief trennt das ZIEL von der SCHREIBWEISE nur als Prosa: eine Prozessregel im Brief fängt nichts (neu, TSK-0105, FR-0069)

**Mechanismus.** Der Brief ist seit dieser Runde ein Decision-Item mit zwei Hälften — die aus dem
Repo abgeleitete (Stack, Palette, Typografie, Produktvokabular, bestehende Site) und die gefragte
(Ambition — bei Exploration mit den Referenzen in ihrem Freitext —, was es erreichen soll und für
wen, Ton, was es nicht werden darf) —,
geschrieben vom PM nach EINEM Frageaufruf und gelesen vom Designer. Ein Decision-Item ist
Freitext: nichts parst die Hälften, nichts erkennt eine Prozessregel („keine Shop-Daten hart
codieren", ein Dateibudget) darin, und nichts hindert den PM, sie in den Designauftrag zu tragen.

**Kette (gemessen, im echten Projekt Canyon_3.4.0, dessen Items hier gemeint sind).** Die dortige
`DEC-0002` hielt die Wahl der Richtung fest, mit der Notiz des Inhabers, dass Preisangaben in der
Vorschau Platzhalter seien und nie Shop-Daten hart codiert werden dürfen; der PM machte daraus im
Arbeitsauftrag eine sichtbare Platzhalter-Markierung; die dortige `DEC-0011` hält die Ablehnung
fest („sieht komplett trash und null hochwertig aus") und benennt als Ursache den eigenen
Auftrag. Der einzige Brief davor war die Ambitionsfrage (die dortige `DEC-0001`). Beides trägt
FR-0069.

**Was stattdessen begrenzt.** Beide Enden sind benannt, nicht eins: der PM-Skill (a0) schreibt die
Hälften getrennt und sagt, dass eine Prozessregel ein `INV` ist und nie ein Designauftrag; das
Designer-Skill („Read first") gibt eine Prozessregel, die den Brief erreicht hat, als Befund in
`followups` zurück, statt sie zu zeichnen. Der PM-Absatz hängt am Sektions-Pin
(`tools/constitution_section_pins.json`, PM-Skill „Work loop"), der Designer-Absatz an keinem;
ein Gate liest keinen von beiden. Kosten des legitimen Wegs: ein Repo-Lesen vor der ersten
Designfrage, ein Frageaufruf mit vier Punkten statt einem.

**Urteil: Rest, benannt** — die Fehlklasse ist gemessen (zweimal im selben Projekt), der Fang ist
Prosa an beiden Enden, und ein Parser über ein Decision-Item wäre die Heuristik über Prosa, die
FR-0010 und FR-0012 ausgeschlossen haben.

### H108 — Eine Evidenz, die ihren Laufumfang GAR NICHT erklärt, zählt weiter als Volllauf (neu, TSK-0106, FR-0040)

**Mechanismus.** `EVD` trägt seit dieser Runde ein Laufprotokoll (`run_command` + `run_scope`,
`backlog_types.RUN_SCOPES`), und `report._delivery_evidence` lässt einen PASS, der sich als
`selection` erklärt, nicht mehr als Merge-Beleg durch. Das Feld ist OPTIONAL, und daran hängt der
Rest: eine Evidenz, die nichts erklärt, wird behandelt wie vor der Änderung. Ein Teillauf, der
schweigt, öffnet also weiterhin einen Merge.

**Warum es nicht einfach zur Pflicht wird, gemessen statt vermutet.** `EVD` ist ein
`IMMUTABLE_TYPE`: kein Kommando ändert ein Feld daran, und ein Pflichtfeld gilt für GESPEICHERTE
Items, nicht nur für neue (`DECLARED_REQUIRED_FIELDS` speist die Feld-Pflichtschleife des
Validators). Allein dieses Repository hält **76 aktive** Evidenz-Datensätze (`ls
project_memory/evidence | wc -l`, 2026-09-02); jeder von ihnen würde am Tag der Pflicht zu einem
Validator-Error, den kein Kommando reparieren kann — und `gate_memory_complete` blockt auf
Validator-Errors jeden Merge und jeden Push. Die Alternative, die Pflicht an die BEFEHLSZEILE zu
hängen (`--run-command` als `required=True`), ist gemessen ebenfalls teuer: die ausgelieferten
Rollen- und Verfassungstexte aller drei Kits nennen `harness.py evidence` ohne diese Flags, und
diese Texte sind `forbidden_scope` dieser Runde — ein Kit, dessen eigene Anleitung ein Kommando
lehrt, das jetzt fehlschlägt, ist schlechter als die Luecke.

**Was heute stattdessen begrenzt:**
* ein erklärter Teillauf öffnet keinen Merge mehr (`test_report.test_a_pass_from_a_partial_run_is
  _not_merge_evidence_and_a_fail_still_is`), und die Erklärung ist auf der Kommandozeile da, wo die
  Rolle sie tippt;
* ein Teillauf, der FEHLSCHLÄGT, zählt weiterhin — die Asymmetrie ist gebaut, nicht behauptet;
* die Hälfte des Paares kann nicht fehlen: `run_scope` ohne `run_command` wird beim `capture`
  verweigert, also gibt es keine Umfangs-Behauptung ohne die Zeile, an der man sie prüft.

**Urteil: offen, nicht blockierend, und die Entscheidung gehört dem Nutzer.** Es ist keine
Umgehung: wer nichts erklärt, bekommt den Stand von gestern, nicht mehr. Was die Pflicht kostet und
wer sie trägt, ist eine Vertragsänderung an einem unveränderlichen Typ — die Entscheidung dazu ist
als `DEC-0061` erfasst (VALID), wie FR-0040 es verlangt („DEC first"). Zur Abnahme durch den Nutzer.

### H109 — „Sammelbar" ist geparst und nicht gefahren: ein übersprungener Test gilt als vorhanden (neu, TSK-0106, FR-0039)

**Mechanismus.** `INV.verified` hat seit dieser Runde einen Produzenten
(`state.record_invariant_verification`) und einen Merge-Blocker
(`report._check_invariant_checks`, ein Validator-Error, auf dem `gate_memory_complete` jeden Push
anhält). Beide fragen dieselbe Stelle: `report.invariant_check_resolution` liest `check.ref` als
`<pfad>::<name>`, öffnet die Datei relativ zur Projektwurzel und PARST sie — der Check ist
aufgelöst, wenn die Datei den Namen definiert. Ob dieser Test bei einem Lauf auch **ausgeführt**
wird, sieht der Kernel nicht: ein `@pytest.mark.skip`, ein Marker, den die Projektkonfiguration
abwählt, oder eine Parametrisierung, die keinen Fall erzeugt, ändern nichts an der Definition.

**Gemessene Kette** (2026-09-02, Stellvertreterprojekt außerhalb des Repos, drei Zustände
derselben Datei):

| Zustand von `tests/test_rules.py` | Kernel | Läufer |
|---|---|---|
| `def test_pure(): pass` | `verified`, keine Befunde | 1 passed |
| dieselbe Funktion mit `@pytest.mark.skip` | `verified`, keine Befunde | **1 skipped** |
| Funktion umbenannt | `unverified` + Error „names … does not define" | 1 passed (anderer Test) |

Die mittlere Zeile ist das Loch: der Läufer hat den Test nicht ausgeführt, der Kernel nennt die
Invariante trotzdem verifiziert. Die dritte Zeile zeigt, dass die Rückrichtung greift, und steht
als Test in
`test_state.test_an_invariant_is_verified_by_its_check_and_unverified_when_it_stops_resolving`.

**Warum nicht gefahren wird.** Was ein Testlauf kostet und welcher Läufer im Projekt gilt, ist eine
Tatsache über das Projekt und nicht über den Kernel — dasselbe Argument, das `RUN_SCOPES` für den
Umfang eines Laufs trägt (FR-0040). Ein Kernel, den drei Kits teilen, dürfte dafür weder `pytest`
voraussetzen noch beim Validieren einen fremden Prozess starten; `validate_state` läuft in einem
blockierenden Merge-Gate.

**Was heute stattdessen begrenzt:**
* die Auflösung steht an EINER Stelle, und beide Leser (Produzent und Validator) fragen sie —
  ein Auseinanderlaufen von „verifiziert" und „blockiert" ist ausgeschlossen;
* jede andere Abweichung fällt zu: keine Datei, kein Name, kein `ref`, kein `check` → Error;
* die Rückrichtung ist gebaut: verschwindet der Name, nimmt der Produzent die Verifikation zurück.

**Urteil: offen, nicht blockierend.** Der Rest ist die Differenz zwischen „der Test steht da" und
„der Test läuft", und die zu schließen heißt, im Kernel einen Testlauf zu starten. Das ist eine
Entscheidung über die Bauart, keine Nacharbeit an dieser Runde — und sie hängt an derselben Frage
wie H108.

### H110 — Einen Check, den der Kernel nicht lesen kann, beantwortet er mit UNENTSCHIEDEN (neu, TSK-0106, FR-0039)

**Mechanismus.** Die Auflösung oben parst die Datei, die `check.ref` nennt. Für eine Datei, die
kein Python ist — `src/rules.test.ts`, eine Go- oder Rust-Datei —, kann sie die Frage nicht
beantworten. Sie gibt darum `None` zurück, und der Validator macht daraus eine **Warnung**: kein
Merge wird angehalten, und der Produzent lässt das Item `unverified`.

**Gemessene Kette und warum die Gegenrichtung schlimmer ist.** Beim Bauen zuerst fail-closed
gemessen (der unlesbare Fall als „nicht aufgelöst"): ein Projekt mit
`check.ref: src/rules.test.ts::is pure` bekommt einen Validator-Error, `gate_memory_complete`
blockt darauf jeden Merge und jeden Push, und **kein Kommando im Projekt kann das je klären** —
die Datei ist da, der Test ist da, der Kernel kann ihn nur nicht lesen. Das ist die Fehlerklasse,
die dieses Repo an mehreren Stellen ausdrücklich verbietet („als Error blockiert es jeden Merge und
kann nie erfüllt werden"), und eine Regel, die niemand erfüllen kann, wird umgangen statt befolgt.
Die Messung steht als Test:
`test_report.test_an_invariant_whose_check_this_kernel_cannot_read_blocks_nothing`.

**Was heute stattdessen begrenzt:**
* der Produzent verifiziert NICHT auf ein Achselzucken: `resolved is True` und nichts anderes
  schreibt `verified`, ein unlesbarer Check bleibt `unverified`;
* die Warnung sagt, wessen Frage das ist, statt zu schweigen — sie nennt die Datei und den Grund;
* für alles, was der Kernel lesen kann, bleibt der Blocker scharf: fehlende Datei und fehlender
  Name sind weiterhin Errors;
* **und der Exitcode trägt den Zustand nicht weiter** (Nacharbeit 1): `verify-invariants` zählt
  nur, was nachweislich NICHT aufgelöst ist. Vorher zählte es „alles außer verified" und gab
  darum rc 1, während `validate` im selben Moment rc 0 mit einer Warnung gab — für ein Projekt,
  dessen Tests nicht Python sind, ein dauerhaftes Fehlsignal aus genau dem Kommando, auf das die
  Rollentexte es schicken. Unentscheidbare bekommen eine eigene Zeile, die diese Nummer nennt
  (`test_staging_cli.test_verify_invariants_records_what_the_check_resolves_to_and_exits_on_the_gap`).

**Urteil: offen als bewusste Über-Öffnung, nicht blockierend.** Geschlossen wird sie erst mit einer
Antwort auf die Frage aus H109 — wer den Test wirklich fährt. Bis dahin ist der ehrliche Zustand
„der Kernel weiß es nicht" und nicht „der Kernel verbietet es".

### H111 — Die Freigabe, auf der die Auditor-Routine reitet, hat in keinem Kit einen Erzeuger (neu, TSK-0107, FR-0038)

**Mechanismus.** Alle drei Verfassungen und alle drei `project-auditor`-Rollen sagen denselben Satz:
der Auditor wird auf einer `APR.kind: routine` für die Wurzel seiner Audit-Aufgabe gespawnt, oder
auf einer `APR.kind: analysis`, die diese Aufgabe listet; beide tragen ein Ablaufdatum, beide sind
widerrufbar, und die `routine` hasht **Rolle, Read-only-Scope, Trigger und Takt**
(`approvals.ROUTINE_MANIFEST_FIELDS`). Genau diese vier Felder wären die Ableitungsquelle für ein
Fristenregister, das fragt „wann muss der Auditor wieder laufen".

**Gemessen (2026-09-02, gegen die ausgelieferten Module dieses Baums, Wegwerf-Projekt außerhalb des
Repos):**

```
approvals.APR_KINDS             : analysis, scope, delivery, acceptance, routine, push,
                                  preset, kit_update, filing_correction, filing_rule,
                                  document_proposal
approvals.item_derived_kinds()  : scope, delivery, acceptance
request-approval  Art-Auswahl   : acceptance, delivery, document_proposal, filing_correction,
                                  filing_rule, kit_update, preset, push, scope
```

`routine` und `analysis` stehen in **keiner** der beiden letzten Zeilen. Sie sind keine
item-abgeleiteten Arten (ihr Manifest ist aus einer Item-Id nicht baubar — eine Analysefrage, ein
Read-only-Scope und ein Takt stehen in keinem Item), und `request-approval` bietet genau die Arten
an, für die es ein Manifest bauen kann. Es gibt keinen zweiten Weg: weder `kernel/cli.py` noch das
Kit-Skript `scripts/harness.py` nennt das Wort `routine` überhaupt. `kernel/dispatch.py` räumt an
seiner eigenen Stelle bereits ein, dass Trigger und Takt zwar gehasht, aber von keinem Gate gelesen
werden — was hier dazukommt, ist, dass sie auch nie geschrieben werden können.

**Folge, und sie steht im Code dieser Runde** (seit `TSK-0112` in der gespiegelten
`hooks/_routine.py` aller drei Kits, nicht mehr nur im Office-Kit)**:** `_routine.AUDIT_ROLE` NENNT die Rolle und
`_routine.audit_period_id` NENNT den Takt (eine ISO-Woche), statt beide aus der Freigabe zu lesen.
Ein Register, das die Freigabe befragt hätte, hätte in jedem existierenden Projekt nichts gefunden
und nie gemeldet. Der Kommentar an der Konstante trägt diese Messung, und
`tools/test_routine_feed.py::test_no_routine_approval_can_be_minted_in_any_kit_today`
wird rot, sobald ein Weg dazukommt.

**Warum hier nicht geschlossen.** Die Arten liegen in `kernel/approvals.py` und `kernel/cli.py`, die
Sätze in den drei Verfassungen und den drei Rollentexten — beides fremde Dateilisten dieser
Generation (Ströme F und E). Ein Erzeuger, den dieser Strom nebenher baut, wäre eine zweite
Definition dessen, was eine Routine-Freigabe ist.

**Was stattdessen begrenzt.**
* **Die Erinnerung fällt nicht aus.** Das Register meldet den fälligen Audit-Lauf bei jedem
  Sitzungsstart, unabhängig von jeder Freigabe. Was fehlt, ist die vom Nutzer unterschriebene
  Bindung von Rolle und Takt, nicht die Sichtbarkeit.
* **Read-only bleibt read-only.** Was den Auditor lesend hält, sind seine Werkzeuge und sein
  Arbeitsauftrag, nicht diese Freigabe — die Rollentexte sagen das selbst.

**Urteil: offen, keine Angriffskette — eine Lücke im dokumentierten Weg.** Zwei Nahtstellen sind
benannt: Strom F entscheidet, ob `routine`/`analysis` eine Kommandofläche bekommen oder ob der Satz
in den Verfassungen fällt; Strom E lässt den Verfassungssatz auf die Code-Konstante zeigen, statt
„wöchentlich" ein zweites Mal zu schreiben.

### H112 — Der Laufdatensatz der Routine ist ein Nebenprodukt und sagt nicht, was er zu sagen scheint (neu, TSK-0107, FR-0038)

**Mechanismus.** FR-0038 verlangt „einen aufgezeichneten Zeitpunkt des letzten Audit-Laufs und eine
Wochen-Id gegen Doppelläufe". Dieser Strom durfte keinen Hook registrieren
(`settings/settings.json` liegt außerhalb seines Bereichs) und keinen der gespiegelten Hooks
ändern, die den `SubagentStop` sehen. Der Datensatz wird deshalb **abgeleitet**: aus dem
`subagent_stop`-Ereignis, das `notify_agent_events` ohnehin nach
`project_memory/.audit/hook_events.jsonl` schreibt. Die Kette ist gemessen und nicht angenommen —
`tools/test_routine_feed.py::test_the_routine_reads_the_run_record_the_shipped_hook_really_writes`
fährt genau diesen Hook als
Prozess und liest sein Ergebnis durch `_routine.last_run` zurück, damit eine Umbenennung dort rot
wird statt blind zu machen.

Was der Datensatz WIRKLICH sagt, ist „ein Subagent dieser Rolle hat aufgehört". Daraus folgen zwei
Grenzen, und sie zeigen in verschiedene Richtungen:

**(a) Rotation — sichere Richtung, rot gemessen.** `_audit` schiebt das Log bei `ROTATE_BYTES` zur
Seite und behält fünf Generationen; `_routine.last_run` liest nur die lebende. Ein Lauf, der älter
ist, liest sich als „nie gelaufen", und die Routine wird als fällig gemeldet. Nörgeln ist für eine
Erinnerung, die nur vorschlägt, die richtige Ausfallrichtung, und
`tools/test_routine_feed.py::test_a_rotated_event_log_makes_the_routine_read_as_due_rather_than_as_run`
hält sie fest. Die
Generationen mitzulesen hieße bei jedem Sitzungsstart bis zu 6 MB zu öffnen — für den Normalfall
eines frischen Projekts der teure Zweig.

**(b) Ein aufgebender Lauf zählt als Lauf — unsichere Richtung, NICHT geschlossen.**
`gate_subagent_output` lässt den ZWEITEN Stop einer Rolle absichtlich durch (`stop_hook_active`; ein
zweites Blockieren wäre eine Endlosschleife, das steht in seinem eigenen Docstring). Dieser Stop
wird von `notify_agent_events` aufgezeichnet, und das Register liest ihn als Lauf — die Meldung
dieser Woche bleibt aus, obwohl der Auditor nichts geliefert hat. **Gemessene Kette** (2026-09-02,
beide ausgelieferten Hooks als Prozesse auf DERSELBEN `SubagentStop`-Nutzlast, Wegwerf-Projekt
außerhalb des Repos, danach das ausgelieferte Routine-Modul befragt):

```
vor jedem Stop:                       routine due = True
gate_subagent_output rc=0   notify_agent_events rc=0
   log: event=gave_up         reason=project-auditor: giving up with summary still missing
   log: event=subagent_stop   reason=project-auditor
_routine.last_run liest:               2026-09-02 13:59:29   (unreadable: None)
nach dem Aufgeben:                    routine due = False
```

Beide Zeilen stehen im selben Log; die zweite löscht die Meldung, die erste sagt, dass nichts
geliefert wurde, und niemand verbindet sie.

**Warum (b) nicht geschlossen ist.** Die beiden Zeilen müssten verknüpft werden: `gate_subagent_output`
schreibt bei genau diesem Fall `event: gave_up` mit der Rolle im `reason` in DASSELBE Log. Ein
gemeinsamer Schlüssel fehlt aber — beide Zeilen tragen nur einen Zeitstempel auf Sekunden, und die
beiden Hooks hängen an demselben Ereignis in unbestimmter Reihenfolge. Einen Schlüssel einzuführen
heißt, zwei gespiegelte Hooks zu ändern, also dieselbe Datei in drei Kits — außerhalb dieses Stroms,
und eine Zeitstempel-Heuristik wäre genau die Art Vermutung, die dieses Repo als Defekt führt.

**Was stattdessen begrenzt.** Die Aufgabe steht im selben Log als `gave_up` und ist für einen
Menschen sichtbar; und der Manager sieht das Ergebnis eines Audits ohnehin an seinem
Evidence-Datensatz — eine ausgebliebene Meldung ist kein ausgebliebenes Audit.

**Urteil: Rest, benannt.** Keine Angriffskette; ein falsch-negatives Nicht-Nörgeln in einer Fläche,
die nur vorschlägt. Nahtstelle für den Strom, der die gespiegelten Hooks besitzt.

### H113 — Das Fristenregister kennt kein „erledigt" (neu, TSK-0107, FR-0034)

**Mechanismus.** Das Register leitet ab, was GESCHULDET ist. Ob es GETAN wurde, hält im Kit nichts
fest: es gibt keinen Datensatz „diese Voranmeldung ist abgegeben", keinen „dieses Aufbewahrungsjahr
ist geprüft" und keinen „diese Rechnung wurde angemahnt". Zwei der fünf Zuflüsse haben deshalb keine
eigene Abschaltbedingung und stehen, bis ihre QUELLE sich ändert:

* eine Steuer-Frist steht, bis die nächste Periode schließt — bei vierteljährlicher Abgabe also bis
  zu drei Monate, auch wenn am Tag danach abgegeben wurde;
* ein Aufbewahrungsjahr steht, bis der Jahresordner verschwunden ist.

Die anderen drei tragen ihre Erledigung in der Quelle selbst: eine bezahlte Rechnung bekommt ihr
`payment_date`, eine Wiedervorlage ihr neues `review_by`, und der Audit-Lauf ist der Datensatz aus
`H112`.

**Warum nicht geschlossen.** Ein „erledigt" ist kanonischer Zustand — ein Feld oder ein Item-Typ —
und damit Kernel; und seine FORM ist eine offene Entscheidung (ein Eintrag je Abgabe? ein Datum im
Profil? ein Item?), keine Implementierungsfrage, die dieser Strom nebenher beantworten dürfte.

**Was stattdessen begrenzt — die Fassung vom 2026-09-02, nachdem die erste hier nachweislich zu
weit ging.** Der ursprüngliche Satz lautete „das Register meldet nur die AKTUELLE Pflicht und
sammelt keine Vergangenheit". Gemessen war das falsch: ein Archiv mit einem Jahresordner je
Geschäftsjahr seit 2005 unter EINER Aufbewahrungsregel ergab 13 Pflichten, alle aus der
Vergangenheit, und der Sitzungsstart-Absatz nannte daraufhin die fällige Steuerfrist gar nicht mehr
(`TSK-0113`; als Prozess über den ausgelieferten Hook gemessen: 15 Pflichten, 13 davon
Vergangenheitsordner, die Voranmeldung nicht im Absatz).

Was heute begrenzt, ist gebaut statt behauptet, und beide Hälften sind gemessen:

* **Kein Zufluss greift über seine eigene Vergangenheit zurück.** Der Steuer-Zufluss nennt die
  zuletzt geschlossene Periode; der Aufbewahrungs-Zufluss nennt EINE Prüfpflicht je REGEL — mit dem
  ältesten Jahr und der Anzahl darin — statt einer je Jahresordner
  (`tools/test_office_duties.py::test_a_rule_with_many_years_past_retention_is_one_duty_that_names_the_oldest_and_the_count`).
* **Kein Zufluss kann einen anderen aus dem Absatz drängen.** Die Plätze der Sitzungsstart-Meldung
  werden reihum je QUELLE vergeben statt streng nach Datum
  (`tools/test_office_duties.py::test_no_feed_can_take_every_slot_of_the_briefing_from_another`).

Was ein Zufluss weiterhin VIELFACH melden kann, sind viele verschiedene offene Posten — je eine
unbezahlte Rechnung, je eine Wiedervorlage. Das ist keine angehäufte Vergangenheit, sondern die
Gegenwart eines Geschäfts; die Reihum-Vergabe sorgt dafür, dass sie den Absatz nicht allein füllt.

**Urteil: Rest, benannt.** Über-Meldung, nie Schweigen — und seit `TSK-0113` gilt das auch für den
Absatz, den der Manager wirklich liest, und nicht nur für die Liste dahinter.

### H114 — Nach `/cd` läuft die Registrierung des ZIELVERZEICHNISSES, aber die Hook-DATEIEN des Startverzeichnisses (neu, TSK-0108, FR-0059)

**Mechanismus.** Seit Claude Code 2.1.246 tauscht `/cd` Einstellungen, Hooks, Skills und MCP-Server
gegen die des Zielverzeichnisses aus. `${CLAUDE_PROJECT_DIR}` bleibt dabei — laut Doku absichtlich —
auf dem **Startverzeichnis** stehen. Jede Hook-Kommandozeile, die unsere Kits und dieses Repo
schreiben, buchstabiert ihren Pfad genau damit
(`python -B "${CLAUDE_PROJECT_DIR}/.claude/hooks/<gate>.py"`). Beides zusammen ergibt ein Paar, das
niemand gewollt hat: **welche** Hooks registriert sind, entscheidet das Ziel; **welcher Code** dann
läuft, entscheidet der Start.

**Kette, gemessen (2026-09-02, eigenes Rig außerhalb des Repos, Client 2.1.258; Protokoll in
`docs/reviews/2026-09-02-cd-measurement.md`, Befund 5).** Zwei Projekte, beide mit derselben
`${CLAUDE_PROJECT_DIR}`-Schreibweise registriert, jede Skriptkopie meldet ihre Herkunft:

```
Sitzung startet in dirA, Bash-Aufruf      → tag REG-A, script_path …\dirA\.claude\hooks\log_hook.py
/cd  …\dirB   (Trust-Dialog bestätigt)
derselbe Bash-Aufruf                      → tag REG-B, script_path …\dirA\.claude\hooks\log_hook.py
```

Die zweite Zeile ist das Loch: Argument und Registrierung aus `dirB`, ausgeführte Datei aus `dirA`.
Für zwei Kit-Projekte heißt das, dass die Gates des Startprojekts über die Arbeit im Zielprojekt
urteilen — und wenn das Startprojekt ein präpariertes Verzeichnis ist, urteilt gar nichts.

**Zweiter gemessener Weg in dieselbe Zeile, ohne `/cd` und ohne Dialog (Befund 16 desselben
Protokolls).** Die VS-Code-Erweiterung hat kein `/cd` — sie startet das Binary im
`stream-json`-Transport, in dem es das Kommando gar nicht gibt — und bewegt die Sitzung stattdessen
mit der Steuer-Anfrage `{"subtype":"set_cwd","path":…}`. An einem Ziel, das früher einmal bestätigt
wurde, antwortet die schon **ohne** jedes Vertrauensfeld mit `status: ok, changed: true`, und die
nächste Hook-Zeile ist dieselbe wie oben: Registrierung `REG-B`, Skript aus `dirA`.

**Urteil: offen, NICHT durch einen Modellpfad erreichbar.** Weder `/cd` noch `set_cwd` ist ein
Werkzeug des Modells — das erste ist ein lokales Kommando der Oberfläche (in dieser Runde für den
`-p`-Transport nachgemessen: „/cd isn't available in this environment"), das zweite eine
Steuer-Anfrage auf stdin des Client-Prozesses, den das Modell nicht beschreibt. Der Wechsel kommt
also vom Client. **Was stattdessen begrenzt, und die zwei Wege stehen unterschiedlich da:**

Auf dem **`/cd`-Weg** geht der Dialog aus Befund 2 voran, der die `.claude/settings.json` des Ziels
ausdrücklich nennt und dessen Vorauswahl auf „No, stay put" steht — aber **nur vor dem ERSTEN
Wechsel in ein Verzeichnis**. Ein späterer `/cd` in dasselbe, inzwischen bestätigte Verzeichnis
läuft dialogfrei durch: gemessen im Lauf `m4.log`, dessen Steuerskript (`pty-m4.txt`) zwischen dem
`/cd` und der nächsten Eingabe **keinen** Tastendruck sendet.

Auf dem **`set_cwd`-Weg** ist überhaupt nur der dialogfreie Wechsel an ein **bereits vertrautes**
Ziel gemessen (`ext3.log`: `status: ok, changed: true`, ohne jedes Vertrauensfeld). Ob an einem
**unbekannten Ziel** ein Dialog erscheint, ist **NICHT gemessen** — belegt ist dort nur die
Fehlermeldung, die einen zweistufigen Handschlag beschreibt (`ext2.log`). Und wann die Erweiterung
den Wechsel überhaupt schickt, ist ebenfalls nicht gemessen.

Drei Fassungen dieses Absatzes haben den Dialog stärker gemacht, als er ist: die erste nannte
ihn ohne Einschränkung, die zweite schrieb ihn dem `/cd`-Weg pauschal zu, die dritte behandelte die
zwei Wege als einen. Diese Fassung trennt sie; wer sie ändert, ändert auch die Tabellenzeile und
§2 des Messdokuments mit.

**Was ein Fix bräuchte** (Kit-Bereich, deshalb hier nur benannt): eine Schreibweise der
Hook-Kommandozeile, die dem Wechsel folgt. Der Prozess des Hooks läuft nach dem Wechsel mit dem
Arbeitsverzeichnis des ZIELS (gemessen: `process_cwd` = `dirB`), ein relativer Pfad
(`.claude/hooks/…`) würde also mitwandern — mit dem bekannten Preis, dass die Sitzung auch in einem
Unterverzeichnis stehen kann, weshalb die Kits den absoluten Pfad überhaupt gewählt haben.

### H115 — `/cd` bringt die Subagenten und die `agent:`-Bindung des Ziels NICHT mit, obwohl der Changelog „agents" nennt (neu, TSK-0108, FR-0059)

**Mechanismus.** Der Changelog-Eintrag zu 2.1.246 führt „skills, and agents" unter dem, was nach
einem `/cd` sofort greift. Gemessen greifen Hooks, Einstellungen, Skills und MCP-Server sofort — die
**Rollenliste** und die **`agent:`-Bindung der Sitzung** nicht.

**Messung (2026-09-02, Rig wie oben; `docs/reviews/2026-09-02-cd-measurement.md`, Befunde 6, 7, 13,
14).** In einer Sitzung, die nachweislich im Ziel steht (deren Hooks feuern), antwortet das
Task-Werkzeug auf den nur dort vorhandenen Subagenten:

```
Error: Agent type 'prober-b' not found. Available agents: agent-a, claude, claude-code-guide, …
```

und der gebundene Sitzungsagent bleibt der des Startverzeichnisses. Dasselbe noch einmal über den
Weg, den die VS-Code-Erweiterung nimmt: nach einem `set_cwd` nach `dirB` lautet der Befehl des
gebundenen Agenten weiter `echo REPORT-BINDING token=AGENT-A` (Befund 16). Eine im laufenden
Verzeichnis **neu abgelegte** Rollendatei greift dagegen ohne Neustart — die Rollenliste wird also
nachgelesen, sie folgt nur keinem Wechsel.

Die Gegenprobe ist in dieser Runde zweimal gefahren worden, und die erste war falsch: sie tauschte
`agent:` in einem Verzeichnis, das die genannte Rolle gar nicht enthielt, und konnte deshalb „nicht
nachgelesen" nicht von „löst nicht auf" trennen. Mit der Rollendatei am Platz bleibt die laufende
Sitzung trotzdem bei `AGENT-A` (Befund 14), und eine **Fortsetzung** derselben Sitzung
(`--continue`) bindet auf `AGENT-B` (Befund 17).

**Urteil: offen, kein Angriffspfad, und für uns eher eine gute Nachricht.** Es ist der Grund, warum
die Install-/Update-Zeremonie der Kits ihre Bitte um einen Neustart behält — was eine laufende
Sitzung nicht tut, ist nachbinden. Gemessen erfüllt **auch ein Fortsetzen** diese Bitte, nicht nur
ein kalter Start; der Wortlaut der Zeremonie sagt heute nur das eine und ist als Nahtstelle
gemeldet. Der Schaden ist eine **Erwartung**, die aus dem Changelog entsteht — wer ihm glaubt, hält
eine bewegte Sitzung für die des Zielprojekts. **Was stattdessen begrenzt:** die Messung oben und
der Satz in der Zeremonie; schließen lässt sich das hier nicht, es ist Client-Verhalten.

### H116 — Die Hook-REGISTRIERUNG wird mitten in der Sitzung neu gelesen — auch zwischen zwei Werkzeugaufrufen einer Runde (neu, TSK-0108, FR-0059)

**Mechanismus.** `CLAUDE.md` dieses Repos trägt den Satz „Was beim Sitzungsstart bindet, ist die
Registrierung" — und leitet daraus ab, dass eine geänderte `.claude/settings.json` erst in der
nächsten Sitzung wirkt. Auf 2.1.258 stimmt das nicht mehr: die Registrierung wird nachgelesen, ohne
`/cd`, ohne Neustart und ohne Dialog.

**Kette, gemessen (2026-09-02, Rig außerhalb des Repos;
`docs/reviews/2026-09-02-cd-measurement.md`, Befund 12).** Viermal in zwei Verzeichnissen und in
beiden Berechtigungsmodi (`bypassPermissions` und Standardmodus mit `--allowedTools Bash`) wirkte
ein Tausch der Datei ab dem nächsten Werkzeugaufruf. Entscheidend ist der fünfte Lauf, in dem die
Sitzung die Datei **selbst** schreibt und beide Aufrufe zu **einer** Runde gehören:

```
Werkzeugaufruf 1   cp …/settings-A2.json …/dirA/.claude/settings.json   → alte Registrierung (REG-A)
Werkzeugaufruf 2   echo mid-turn-probe                                   → NEUE Registrierung (A2)
```

Ein sechster Lauf zeigt dasselbe im **headless**-Transport, also ohne Oberfläche: der Treiber
tauscht die Datei zwischen zwei Runden, und der nächste Werkzeugaufruf trägt den neuen Tag
(`A2` → `A3`, `reb1.jsonl`). Die Fläche ist damit nicht an die interaktive Sitzung gebunden.

**Was das an bestehenden Löchern ändert.** `H12` hält seit langem fest, dass Gate 1 `.claude/` nur
gegen den **Sitzungsagenten** schützt und ein Subagent dort schreiben darf, und dass die Hook-Datei
bei jedem Aufruf frisch gelesen wird — wer dort schreibt, ändert also längst, **welcher Code**
urteilt. Neu ist die andere Hälfte derselben Fläche: über `settings.json` lässt sich ein Gate
**abmelden**, und das wirkt ebenfalls sofort. Ein abgemeldetes Gate verweigert nicht und hinterlässt
keine Spur; ein geändertes tut wenigstens noch etwas. Diese Runde hat die Provider-Hälfte gemessen
(sofortiges Nachlesen); die Gate-Hälfte („ein Subagent darf dort schreiben") ist aus Gate 1s eigenem
Kopfkommentar und aus `H12` übernommen und **nicht neu gemessen** — ein Gate lässt sich aus einer
Sitzung heraus nicht starten (`H80`).

**Urteil: benannte Ausnahme derselben Klasse wie `H12`, Abnahme des Nutzers offen.** Nicht in
diesem Stream schließbar: der Schnitt liegt in `.claude/` und in der Frage, gegen was sich ein
Subagent-Scope prüfen ließe — dieselbe Antwort wie bei `H12` („keine Leases und kein Dispatch").
**Was stattdessen begrenzt:** Rollentrennung und Item, wie bei `H12`, plus die Sichtbarkeit im Diff
— eine geänderte `settings.json` steht im Arbeitsbaum und damit in jedem Paket, das der Prüfer
liest. **Was diese Runde nicht durfte:** den Satz in `CLAUDE.md` korrigieren; er ist als Nahtstelle
gemeldet.

### H117 — Nichts startet den Generator: eine Buchung bewegt die Seite nicht (neu, TSK-0109, FR-0032)

**Mechanismus.** Der Ledger hat keinen Kernel-Schreiber. Seine beiden Schreibwege —
`scripts/ledger_add.py` und die erlaubte Handbearbeitung — kommen an genau einer Stelle vorbei,
`gate_ledger_valid.handle_post_tool_use`, und die validiert die geänderte Datei und tut sonst
nichts. `dashboards/finanzen.html` ist damit so aktuell wie sein letzter Lauf von Hand — dieselbe
Grundlinie, die FR-0030 für das Dev-Dashboard gemessen hat („nichts lief es, also war es
standardmäßig veraltet").

**Kette, gemessen** (2026-09-02, echtes Office-Projekt außerhalb des Repos, ausgelieferte Hooks als
Prozesse; Protokoll `docs/reviews/2026-09-02-tsk0109-measurements.md`, Abschnitt 4):

```
python tools/finance_dashboard.py                    rc 0   Seite d7a311abcbd6e397
python scripts/ledger_add.py --year 2026 … --open …  rc 0   L2026-0134 angehängt
gate_ledger_valid.py (PostToolUse, Bash)             rc 0   validiert, sonst nichts
Seite danach                                                d7a311abcbd6e397  UNVERÄNDERT
python tools/finance_dashboard.py (erneut)                  c29fde2ca6ce16a2  ANDERS
```

**Warum diese Runde es nicht schließt.** Der Auslöser gehört in eine Datei, die dieser Stream nicht
besitzt (`team-kits/office-team/hooks/gate_ledger_valid.py` gehört Stream G), und der Hook darf nach
dem Präzedenzfall des Ledger-Validators nur kit-eigenen Code starten, wofür eine Zeile in
`team-kits/repo_kit_owned.txt` nötig ist — eine Datei ohne Scope, Stream K. Beide Zeilen stehen
wörtlich im Build-Protokoll unter `project_memory/staging/TSK-0109/`; die Merge-Runde legt sie an.
Ein Auslöser, den dieser Stream selbst gebaut hätte, wäre eine Änderung an einem fremden Hook
mitten in einer Parallelgeneration — genau der Fall, den DEC-0057 (a) ausschließt.

**Was stattdessen begrenzt — und was davon NICHT trägt.**
* **Der Datenstand im Kopf ist KEIN Alterssignal.** Er ist das jüngste Datum, das der Ledger trägt,
  nicht der Zeitpunkt des Renderns — er bewegt sich also nur, wenn die neue Buchung jünger ist als
  alles Bisherige. Gemessen 2026-09-02 (Rig `stale.py`): ein im September nachgetragener Junibeleg
  ließ den Kopf **byte-identisch** (`Datenstand 30.08.2026 · … · 318 Buchungen`, sha
  `7e5d3ec3…`); erst der erneute Lauf schrieb `319 Buchungen` und einen anderen Hash. Ein
  Nachtrag ist der Seite also nicht anzusehen. Bis 2026-09-02 stand hier und im Ordnerführer, eine
  veraltete Seite sage es selbst; beides ist auf diese Messung zurückgeführt.
* **Der Befehl steht im Ordner.** `dashboards/ABOUT.txt` nennt `python tools/finance_dashboard.py`
  und sagt ausdrücklich, dass die Seite sich nicht selbst neu baut und dass der Datenstand die
  Frage nicht beantwortet. Dass diese Zeile durch alle Shell-Gates des Office-Kits kommt, ist
  gemessen — durch die **registrierten Kommandozeilen**, also durch den Starter `_gate.py` mit
  seiner ganzen Gate-Liste, nicht nur durch das letzte Wort jedes Eintrags
  (`test_finance_dashboard.py::test_the_documented_command_passes_the_write_scope_gate`; bis
  2026-09-02 maß dieselbe Behauptung sechs von acht Gates).
* **Kein Datenverlust.** Eine veraltete Anzeige ist keine falsche Buchung: der Ledger und die
  Berichte sind unberührt, die Seite ist reine Anzeige.

**Urteil: Rest, benannt — keine Angriffskette, die innerhalb einer Sitzung durchläuft, sondern eine
Aktualitätslücke mit zwei Seam-Items (Stream G, Stream K), die die Merge-Runde schließen kann.**
Bis dahin darf kein ausgelieferter Text „automatisch neu erzeugt" behaupten; die Texte dieser Runde
tun es nicht.

### H118 — Das Alter offener Posten und jeder Mahnstempel entstehen erst im Browser (neu, TSK-0109, FR-0032)

**Mechanismus.** Der Ledger kennt kein Fälligkeitsdatum und `business_profile.yaml` keine
Zahlungsfrist (gemessen an den ausgelieferten Vorlagen). Die Seite ist außerdem eine reine Funktion
der Daten — sie trägt bewusst keinen Erzeugungszeitpunkt —, also kann sie „älter als 30 Tage" nicht
zum Renderzeitpunkt entscheiden. Beides zusammen heißt: das Alter, die Zahl der Mahnkandidaten und
jeder Stempel „mahnen" werden beim Öffnen aus der Uhr des Betrachters gerechnet, und die Frist ist
eine Konstante im Generator (§ 286 Abs. 3 BGB).

**Kette, gemessen** (dieselbe Datei, drei Leser; Protokoll
`docs/reviews/2026-09-02-tsk0109-measurements.md`, Abschnitt 5):

```
Uhr 2026-09-02   Mahnstempel 2   [data-overdue-count] "2"   erstes Alter "91 Tage"
Uhr 2026-07-01   Mahnstempel 0   [data-overdue-count] "0"   erstes Alter "28 Tage"
ohne Skript      Mahnstempel 0   [data-overdue-count] "…"   erstes Alter "—"
```

Eine falsch gestellte Rechneruhr ändert damit still die Antwort auf „muss ich mahnen"; ohne Skript
gibt die Seite gar keine.

**Warum nicht geschlossen.** Die naheliegende Gegenrichtung — das Alter beim Rendern ausrechnen —
kostet den Determinismus, auf dem `test_finance_dashboard.py::test_the_same_tree_renders_the_same_bytes`
steht: dieselben Daten ergäben je nach Renderzeitpunkt andere Bytes, und zwei Kopien der Seite
wären nicht mehr vergleichbar. Die Frist selbst gehört ins Profil und nicht in den Generator; das
ist ein Seam-Item an Stream G (ein Feld unter `tax`), wörtlich im Build-Protokoll unter
`project_memory/staging/TSK-0109/`.

**Was stattdessen begrenzt.**
* **Die Seite sagt beide Hälften.** Unter der Liste steht, dass das Alter beim Öffnen aus der Uhr
  dieses Rechners gerechnet wird, woher die 30 Tage kommen, und dass ohne Skript der Strich stehen
  bleibt und kein Posten den Stempel trägt.
* **Ohne Skript wird nichts behauptet.** Die Spalte bleibt bei „—" und der Zähler bei „…", statt
  eine Null zu zeigen, die als „nichts zu mahnen" gelesen würde. Gemessen, siehe oben.
* **Die Zahl steht an genau einer Stelle** (`PAYMENT_TERM_DAYS`), und die Seite druckt sie an jeder
  Stelle, an der sie wirkt — sie ist nicht in Prosa zweitkopiert.

**Urteil: Rest, benannt — keine Angriffskette; eine Anzeige, deren zeitabhängige Hälfte beim Leser
entsteht, mit beiden Hälften auf der Seite benannt und einem Seam-Item für die Frist.**

### H119 — Keine Herkunft, und dem Ledger-Gate ist der Generator kein Bericht (neu, TSK-0109, FR-0032)

**Mechanismus.** Zwei Dinge, die aus derselben Wurzel kommen — es gibt nichts, was eine erzeugte
Seite von einer geschriebenen unterscheidet:

1. `gate_ledger_valid._BLOCKED_SCRIPT_RX` kennt `euer_report`, nicht `finance_dashboard`. Der
   Generator läuft also gegen einen ungültigen Ledger, wo der Bericht verweigert wird.
2. Es gibt kein Gegenstück zu `render.json` / `gate_design_sighted`: eine von Hand geschriebene
   `dashboards/finanzen.html` ist von einer generierten nicht zu unterscheiden.

**Kette, gemessen** (Projekt mit der BUG-0072-Form `net 214.20 … != gross 14.28`, Hooks als
Prozesse; Protokoll `docs/reviews/2026-09-02-tsk0109-measurements.md`, Abschnitt 6):

```
python scripts/euer_report.py --year 2026 --quarter 3   rc 2   VERWEIGERT
python tools/finance_dashboard.py                       rc 0   DURCHGELASSEN
derselbe Lauf                                           rc 0   „Ledger UNGÜLTIG" auf stdout und im Banner
Seite von Hand ergänzt   sha e2f4e8d9971e8442 -> 1528b8cbb8bd0dbd
Etwas im Baum, das das bemerken würde                          nichts
```

**Warum nicht geschlossen.** Für (1) wäre die Aufnahme in den Ausdruck eine Änderung an einem Hook,
den dieser Stream nicht besitzt (Stream G), und sie ist auch nicht offensichtlich richtig: der
Bericht geht ans Finanzamt, die Seite ist die Anzeige, in der man den Fehler **findet** — eine
Verweigerung würde dem Nutzer genau das Werkzeug nehmen, mit dem er die kaputte Zeile sucht. Der
Generator validiert deshalb selbst. Für (2) gilt DEC-0056: ein Herkunftsnachweis gegen jemanden,
der die Datei absichtlich von Hand schreibt, ist Gerüst über dem Haus; die Fehlklasse, gegen die
gebaut wird, ist der Irrtum, und ein Irrtum schreibt keine 336-KB-HTML-Datei.

**Was stattdessen begrenzt.**
* **Die Seite ist ihr eigener Bericht über den Ledgerzustand.** Bei einem Befund steht ein rotes
  Banner mit den ersten sechs Befunden im Wortlaut des Validators, dazu der Stempel „ungültig" im
  Überblick und der Satz, dass die Summen nicht belastbar sind. Gemessen gegen den laufenden
  Validator (`test_finance_dashboard.py::test_an_invalid_ledger_is_named_on_the_page`).
* **Die Summen bleiben stehen**, weil die kaputte Zeile gefunden werden muss — sie werden bezeichnet,
  nicht versteckt.
* **Eine Handänderung überlebt den nächsten Lauf nicht**, und der Ordnerführer sagt das: der
  Generator schreibt die Datei atomar neu, jedes Mal.

**Urteil: Rest, benannt — nach DEC-0056 kein Härtungsziel; die Anzeige verweigert nicht, sondern
benennt, und die eine Hälfte, die ein Gate sein könnte, ist ein Seam an Stream G mit einer offenen
Abwägung.**

### H120 — Die Haken-Spiegelregel hat keine Präsenz-Hälfte; für die Haken entscheidet die Registrierung, und das halten zwei Nachbartests (neu, TSK-0111)

**Mechanismus.** `tools/test_hooks._assert_mirrored` beantwortet für einen Namen genau eine Frage:
sind die Kopien in den Kits, die ihn liefern, byte-gleich — oder nennt `KIT_SPECIFIC_HOOKS` einen
Grund? Ob ein Kit den Namen überhaupt liefert, fragt keine seiner beiden Schleifen: der Zweig
`if len(copies) < 2 or name in exceptions: continue` überspringt einen Namen, den nur ein Kit
liefert, und die Ausnahmeschleife prüft nur, ob eine gelistete Ausnahme noch nötig ist. Präsenz
ist damit in beide Richtungen unbeurteilt — ein fehlendes Kit ist kein Befund, ein zusätzliches
auch nicht. Genau dieser Schnitt saß bis TSK-0111 auch in der Skill-Spiegelregel und war dort ein
Befund (B1 des Prüfers: eine `references/extra.md` in EINER Kopie eines geteilten Skills, sechs
Suiten grün); dort ist die Präsenz-Hälfte seither gebaut
(`test_shared_skill_contract._assert_one_directory`, gegen die Menge der liefernden Kits). Für die
Haken ist sie **nicht** gebaut, und dieser Eintrag sagt, warum das kein Loch mit Kette ist.

**Der lebende Fall — die zweite Richtung, nicht die erste.** `format_on_write.py` liegt in
`dev-team/hooks/` und `research-team/hooks/`, nicht in `office-team/hooks/`. Sie liegt also in ZWEI
Kits und fällt nicht in den `len(copies) < 2`-Zweig; was die Regel bei ihr nicht fragt, ist das
fehlende dritte Kit. Byte-verglichen wird sie ebenfalls nicht, weil `KIT_SPECIFIC_HOOKS` sie als
absichtlich kit-spezifisch führt („formats the languages a kit actually produces") — und die beiden
Kopien unterscheiden sich wirklich, sonst würde die Ausnahmeschleife die Ausnahme als überflüssig
melden. Kein Test sagt das Fehlen in office — und keiner soll: office registriert die Datei nicht.

**Kette, gemessen (2026-09-02, Kopie des Worktrees außerhalb des Repos, vier Tests als Auswahl —
`test_hooks_v2.test_every_registered_hook_script_is_shipped_by_its_kit`,
`test_hooks.test_shared_kit_files_identical`,
`test_hooks.test_every_hook_documented_in_its_constitution`,
`test_hooks.test_every_hook_an_entry_gate_names_is_shipped_by_every_kit_in_that_blocks_scope`):**

```
Baseline                                              4 passed
(a) dev-team/hooks/format_on_write.py gelöscht        1 failed: test_hooks_v2::test_every_registered_hook_script_is_shipped_by_its_kit
                                                      (der Spiegel-Test bleibt grün — er sieht das Fehlen nicht)
(b) office-team/hooks/extra_hook.py gepflanzt         1 failed: test_hooks::test_every_hook_documented_in_its_constitution
                                                      (der Spiegel-Test bleibt grün — ein Name in einem Kit ist ihm nichts)
zurückgesetzt                                         4 passed
```

Beide Richtungen der Präsenz-Frage haben also einen Halter, nur nicht den Spiegel: ein registrierter
Name muss ausgeliefert sein (a), ein ausgelieferter Name muss in der Verfassung des Kits eine
Regel-Heimat haben (b). Was KEIN Test hält, ebenfalls gemessen: eine Datei, die ein Kit ausliefert,
dokumentiert und nicht registriert — (c) `extra_hook.py` gepflanzt UND eine Zeile mit ihrem Namen an
die Office-Verfassung gehängt: die vier Tests oben **4 passed**, `tools/test_hooks_v2.py -k shipped`
**16 passed** und ein Roter, der nicht den Haken sieht, sondern die gepflanzte Verfassungszeile
(`test_hooks_v2.test_the_shipped_lead_packages_are_within_their_own_record`, Größen-Ratsche des
Lead-Pakets). Das ist totes Gewicht, kein Durchsetzungsverlust, und steht hier als Grenze.

**Warum die Präsenz-Hälfte im Spiegel nicht gebaut ist.** Die Haken-Mengen sind je Kit **per
Konstruktion** verschieden — office liefert elf eigene (`_bookings.py`, `_filing.py`,
`_readings.py`, `gate_filing.py`, `gate_ledger_valid.py`, `gate_proc_approved.py`,
`gate_second_booking.py`, `gate_second_reading.py`, `guard_fs_tripwire.py`,
`record_booking_reading.py`, `record_filing_reading.py` — elf Dateien, gemessen am 2026-09-02 mit
`comm` über die drei Verzeichnisse), dev und research je ihre Gates ohne Office-Gegenstück. Eine
Präsenz-Regel bräuchte für jede davon einen Ausnahmeeintrag mit Grund — die Aufzählung, die
`test_hooks.test_shared_kit_files_identical` in seiner ersten Fassung war und aus der es
umgeschrieben wurde. Bei den Skills liegt der Fall anders: ein geteilter Skill ist EIN Verzeichnis,
und welche Kits es liefern, sagt seine eigene Deklaration (`reference_for.roles`); dort ist die
Menge ableitbar, hier nicht.

**Was stattdessen begrenzt.** Die Registrierung (a) und die Verfassungs-Dokumentation (b), beide als
Tests; der Docstring von `test_hooks.test_shared_kit_files_identical` nennt beide seit dieser Runde.

**Urteil: kein Loch mit Kette innerhalb einer Sitzung — von Nachbarn gedeckt, mit einer benannten
Grenze (ausgeliefert + dokumentiert + nicht registriert = totes Gewicht, das niemand meldet).** Keine
Abnahme des Nutzers nötig; der Eintrag steht, damit der nächste, der die Skill-Regel liest und die
Haken-Regel daneben hält, die Asymmetrie nicht als Versehen liest.

### H121 — Der Leser der Löcherliste kennt keinen Code-Zaun; jedes Zitat hinter einem Zaun ist ungeprüft (neu, TSK-0111)

**Mechanismus.** `test_gates.test_every_test_the_hole_list_names_is_one_that_exists` sammelt die
Zitate eines Eintrags, indem es den ganzen Rumpf mit `re.findall` nach Paaren von Backticks
absucht, über Zeilengrenzen hinweg (`re.DOTALL`). Ein Code-Zaun ist für Markdown ein Block, für
diese Suche aber **drei Begrenzer**: der erste öffnet, der zweite schließt eine leere Spanne, der
dritte öffnet erneut — und schließt erst am nächsten Backtick, also am ersten Zitat NACH dem Zaun.
Der Rumpf des Blocks wird damit selbst zu einer Spanne, und ab dort ist die Paarung um eins
verschoben: was der Autor als Zitat geschrieben hat, liest der Test als Zwischentext, und was
Zwischentext ist, liest er als Zitat. Beide Zaun-Hälften tun das — die öffnende wie die
schließende —, weshalb die Verschiebung nach dem ersten Zaun bestehen bleibt und nicht am zweiten
zurückspringt. Ein nackter, nicht auflösender Testname hinter einem Zaun wird deshalb **nicht**
gemeldet: falsches Grün.

**Kette, gemessen (2026-09-02, Kopie des Worktrees außerhalb des Repos, derselbe Geist-Name zweimal
in den H120-Eintrag gepflanzt, gefahren wurde nur der eine Test):**

| Fall | Ergebnis |
|---|---|
| Baseline | 1 passed |
| (a) Geist-Name VOR dem Zaun | **1 failed** |
| (b) derselbe Geist-Name HINTER dem Zaun | **1 passed** — der Draht schweigt |
| zurückgesetzt | 1 passed |

**Umfang.** Zweimal gemessen, über den Leser selbst und nicht über eine Textsuche, und die
zweite Zahl ist die der ausgelieferten Liste:

| Stand | Einträge | davon mit Zaun |
|---|---|---|
| 2026-09-02, Worktree von TSK-0111 (vor der Merge-Runde) | 97 | 10 — H46, H47, H48, H65, H92, H93, H94, H95, H99, H120 |
| 2026-09-03, gemergter Baum, nach Nacharbeit 1 | 117 | 19 — dazu H105, H111, H112, H114, H115, H116, H117, H118, H119 |

Die erste Zeile zählte, BEVOR dieser Eintrag in der Liste stand; er selbst trägt keinen Zaun.
In allen bis auf einen steht hinter dem Zaun kein nackter Testname; in einem schon.

**Die lebende Instanz — erledigt.** H46 nannte hinter seinem Zaun den Test, der den Datei-Fall
misst, nackt geschrieben und ohne Modulpräfix. Der Name lebt (in `tools/test_hooks_v2.py`), aber die
Auflösungsregel suchte einen nackten Namen ausschließlich in `test_gates.py` selbst; er wäre also
ein falsches ROT gewesen — zwei Defekte, die sich gegenseitig aufhoben, weshalb die Reihenfolge
eines Fixes nicht beliebig war: wer den Leser repariert, schreibt im selben Zug das Präfix in H46.
TSK-0114 hat beides in EINER Änderung getan.

**Dieser Eintrag war auch ein Befund über den vorigen.** Von den sieben Modulpräfixen, die TSK-0111
in H120 geschrieben hat, hielt der Draht nur die **vier vor** dem Zaun; die **drei dahinter** standen
unbewacht. Gemessen an derselben Kopie: eines der drei wieder auf die nackte Schreibweise
zurückgesetzt → **1 passed**, der Test schwieg. Seit dem Fix in TSK-0114 werden alle sieben gelesen.

**Herkunft.** Gefunden vom Prüfer in den Nachprüfungen 3 und 4 dieser Runde (die Kette oben ist
seine, in der Kopie des Umsetzers nachgefahren); die Spannen-Sicht stammt aus
`_round-scratch/TSK-0111/rework3/p_spans.py`, das dieselben Helfer wie der Test benutzt und druckt,
was er wirklich paart. Abgrenzung zum Nachbarbefund aus Strom I: dort geht es um das
AUFLÖSUNGSZIEL eines Namens (ein `tools/`-Name, nackt geschrieben, wird zum falschen Rot); hier geht
es um den LESER, der das Zitat gar nicht erst sieht — falsches Grün, die teurere Richtung, weil
niemand davon erfährt.

**Was stattdessen begrenzte.** Drei Dinge, alle klein: der Fehler saß in der Prüfung und nicht im
ausgelieferten Produkt; nur ein Sechstel der Einträge trägt überhaupt einen Zaun (Tabelle oben);
und ein Eintrag, der ohne Zaun auskommt, war vollständig geprüft — dieser hier hat deshalb
keinen, seine Messung steht als Tabelle.

**Der Fix (TSK-0114), zusammen mit dem Nachbarbefund aus Strom I.** `_prose_of` schneidet die
Zäune aus dem Rumpf, bevor irgendetwas gepaart wird; `_tests_by_module` löst einen zitierten
Namen gegen `test_gates.py` UND jede `tools/test_*.py` auf; `_cited_test` liest die vier
Schreibweisen als eine Frage — der Name nackt, mit einem Modulnamen davor, mit einem Dateipfad
und doppeltem Doppelpunkt, oder mit Auslassungspunkten an der Stelle des Moduls —, und H46
trägt sein Präfix.

**Nachgeschärft in derselben Runde, nach der Prüfung** (2026-09-03), weil die erste Fassung an
drei Stellen zu grob war und der Prüfer sie gepflanzt hat:

* Der Korpus ist der Eintrag **und die Zeile der Zusammenfassungstabelle**, die ihn beurteilt
  (`test_gates._hole_citation_sources`) — die Tabelle zitiert selbst, und keines dieser Zitate
  wurde gelesen.
* Eine Zaun-Zeile ist eine Zeile, die NUR aus ihrem Marker besteht (plus Infostring); eine Zeile
  mit einer kurzen Code-Spanne aus drei Backticks mitten im Satz ist keine. Vorher war sie eine,
  und dann entschied die ANZAHL solcher Zeilen: ungerade laut, gerade still.
* Gepaart wird nach LAUFLÄNGE — eine Spanne öffnet mit n Backticks und schließt mit genau n,
  wie es Markdown selbst tut. Ein Dreier-Lauf mitten im Satz verschob sonst jede Paarung
  dahinter. Dieselbe Schärfe macht zwei Prosa-Idiome sichtbar, die keine Nennung sind und darum
  ausgenommen bleiben: eine Spanne, deren INHALT einen Backtick trägt (eine Spanne, die eine
  Spanne zeigt), und das nackte Präfix `test_`.
* `~~~` gilt als Zaun wie drei Backticks; vorher war diese Schreibweise unbekannt.

Der Leser prüft damit **127 Zitate statt 43**, gezählt wie der Test zählt: je Eintrag die MENGE
seiner Spannen, also entdoppelt (undedoppelt sind es 140). Die Zusammenfassungszeilen bringen
heute kein Zitat bei, das nicht ohnehin im Eintrag stünde — der Wert des erweiterten Korpus
liegt nicht in dieser Zahl, sondern darin, dass eine Zeile, die morgen als einzige einen Namen
nennt, gelesen wird (Pflanzung A6).

**Rot zuerst, sechs Pflanzungen in einer Kopie außerhalb des Repos** (2026-09-02; gefahren wurde je
der eine Test, links die Fassung aus `HEAD`, rechts die reparierte):

| Pflanzung in den Eintrag dieses Nachbarn | vor dem Fix | nach dem Fix |
|---|---|---|
| nichts (Grundlinie) | 1 passed | 1 passed |
| Geist-Name VOR dem Zaun | **1 failed** | **1 failed** |
| Geist-Name HINTER dem Zaun | 1 passed — falsches Grün | **1 failed** |
| lebender `tools/`-Test, nackt | **1 failed** — falsches Rot | 1 passed |
| lebender `tools/`-Test, modulqualifiziert | 1 passed — übersprungen, nie geprüft | 1 passed |
| Geist-Name, modulqualifiziert | 1 passed — falsches Grün | **1 failed** |

Die vierte Zeile stand auch ohne Pflanzung im Baum: H83 nennt
`test_reference_skills.test_the_codex_mirror_is_generated_per_skill_directory`, und dieser Name
löst in `test_gates.py` nicht auf.

**Rot zuerst, zweite Runde** (2026-09-03, Pflanzungen des Merge-Prüfers, dieselbe Kopie):

| Pflanzung | nach dem ersten Schritt | nach der Nachschärfung |
|---|---|---|
| nichts (Grundlinie) | 1 passed | 1 passed |
| Geist-Name in der ZEILE der Zusammenfassungstabelle | 1 passed — falsches Grün | **1 failed** |
| Geist-Name zwischen zwei Zeilen mit Inline-Dreier-Lauf | 1 passed — falsches Grün | **1 failed** |
| Geist-Name hinter einem `~~~`-Zaun | 1 failed | **1 failed** |
| Geist-Name INNERHALB eines Zauns (beide Marker) | 1 passed | 1 passed — der benannte Preis |

**Urteil: GESCHLOSSEN (TSK-0114), beide Grenzen in einer Änderung, beide Richtungen gemessen,
nach der Prüfung um drei Schreibweisen nachgeschärft.** Was der Leser weiterhin NICHT liest,
steht in seinem eigenen Docstring, und es sind DREI Dinge, alle der Preis eines Schnitts:

1. ein Zitat INNERHALB eines Zauns ist keine Spanne, gleich mit welchem der beiden Marker der
   Zaun geschrieben ist;
2. ein Modul, das zu Auslassungspunkten abgekürzt ist, wird in jeder Testdatei dieses Repos
   gesucht, kann also gegen eine Datei auflösen, die der Autor nicht meinte;
3. eine Zeile der Zusammenfassungstabelle wird nur gelesen, wenn sie in genau drei Zellen
   zerfällt. Trägt eine ihrer Zellen einen senkrechten Strich INNERHALB einer Code-Spanne, zählt
   der Leser vier Zellen und lässt die Zeile still fallen — ein Geist-Name dort bliebe unbemerkt.
   Am 2026-09-03 an der ausgelieferten Liste gemessen: **keine einzige** Zeile hat diese Form, das
   blinde Feld ist heute also leer. Der Merge-Prüfer hat die Klasse gefunden; sie steht hier statt
   im Leser, weil eine Änderung an ihm einen weiteren Volllauf der Gate-Suite kostet und nichts
   von dem, was heute in der Liste steht, davon berührt wird.

Gegen alle drei steht kein Code, sondern dieselbe Schreibregel wie zuvor — der Zaun ist für das,
was lief, das Zitat gehört in die Prosa, und eine Tabellenzelle trägt keinen senkrechten Strich.

### H122 — Der Melder über ungelesene Prosa fragt, was git TRÄGT, und nicht, was auf der Platte liegt (neu, TSK-0110, FR-0036)

**Mechanismus.** `test_repo_hygiene.test_docs_prose_nothing_reads_any_more_is_reported_not_failed`
nennt eine Datei unter `docs/`, die seit `_DOCS_GRACE_DAYS` niemand mehr anfasst und die NICHTS
nennt. Sein Korpus ist `test_repo_hygiene._carried_files`, also
`git ls-files -c -o --exclude-standard`. Eine ignorierte Datei steht darin nicht. Nennt sie ein
Dokument, sieht der Melder die Nennung nicht und meldet das Dokument als ungelesen.

**Kette.** Eine ignorierte Datei — ein Laufprotokoll, etwas unter `project_memory/.audit/`, ein
erzeugtes Dashboard — nennt `docs/x.md`; kein getragener Verweis zeigt sonst dorthin; nach der
Karenzzeit nennt der Hinweis `docs/x.md` als ungelesen; eine Runde verschiebt sie nach
`docs/archive/<jahr>/`; die Nennung in der ignorierten Datei zeigt ins Leere.

**Was stattdessen begrenzt.** Drei Dinge, und das erste ist eine Messung und keine Hoffnung: auf
diesem Baum gibt es außerhalb der Werkzeug-Caches **keine einzige** nicht getragene Datei, das
blinde Feld ist also leer und nicht bloß klein (Strom J, `rework1/n1_ignored_corpus.py`). Zweitens
sagt der Docstring des Melders genau den kleineren Satz — „nichts, was git trägt, nennt die Datei"
—, nicht den größeren. Drittens ist der Melder eine Warnung: er blockt keine Runde, und die
Verschiebung ist ohnehin eine Einzelentscheidung, die auf Zweifel unterbleibt.

**Herkunft.** Strom J (TSK-0110), Befund N1 der Nachprüfung, in der Nacharbeit als Grenze in den
Docstring geschrieben. Der Strom durfte die Löcherliste nicht schreiben; die Merge-Runde TSK-0114
vergibt die Nummer.

**Urteil: Rest, benannt — nicht blockierend.** Den Korpus auf die Platte auszuweiten, hieße jedes
Werkzeug-Cache-Verzeichnis mitzulesen; das war die Fassung VOR dieser Runde, und sie hat einen
Melder ergeben, dessen Korpus fünf von Hand genannte Verzeichnisse waren. Geschlossen wird das an
dem Tag, an dem etwas Ignoriertes wirklich Dokumente nennt — bis dahin ist der kleinere Satz der
wahre.

### H123 — Eine Löschung mit einer FLAGGE kommt am Archiv-Wächter vorbei — seit TSK-0116 nur noch, wenn sie im ZIEL löscht (TSK-0113, FR-0050)

**Mechanismus, wie er bis TSK-0116 stand.** `guard_fs_tripwire` hat zwei Regeln: eine Löschung
unter `inbox/` oder `archive/` und eine Bewegung AUS `archive/` heraus. Beide fragten nach einem
Lösch-VERB (`DELETE_VERBS`) am Kopf der Stufe. Ein Befehl, der seine Treffer über eine
FLAGGE entfernt, trägt keines: die Zeile beginnt mit `find`, mit `tar` oder mit `python`, und
die Löschung steht in einem Argument. Seit TSK-0116 gibt es kein `DELETE_VERBS` mehr; was an
seine Stelle trat und was davon übrig bleibt, steht zwei Absätze weiter.

**Kette von damals, am Wächter jener Runde gemessen** (2026-09-02, Merge-Baum, echtes Dokument unter
`archive/finance/2026/`, der Haken als Prozess auf einem Vorlagenprojekt außerhalb des Repos,
NICHTS ausgeführt — gemessen wurde die Entscheidung):

| Befehlszeile | Wächter |
|---|---|
| eine Suche, die ihre Treffer mit einer Lösch-Flagge entfernt | **rc 0** |
| ein Archivierer mit quelllöschender Flagge | **rc 0** |
| eine Löschung innerhalb eines anderen Programms | **rc 0** |
| dieselbe Löschung mit einem Lösch-Verb | rc 2 |
| eine Bewegung aus dem Archiv heraus | rc 2 |

**Was TSK-0116 daran geschlossen hat, gemessen.** Die Regel liest ein
zerstörendes Wort seither an JEDER Stelle einer Aufrufung — Kommandowort, Flagge,
Unterbefehl — statt nur am Kopf. Am Piloten außerhalb des Repos, gegen alle acht auf
`Bash|PowerShell` registrierten Office-Haken als Prozesse, HEAD e45c0ca gegen diese Runde:

| Befehlszeile | HEAD e45c0ca | TSK-0116 |
|---|---|---|
| `find archive -name x.pdf -delete` | ALLOW | **rc 2** |
| `tar --remove-files -cf out.tar archive/finance/2026/invoice.pdf` | ALLOW | **rc 2** |

**Was OFFEN bleibt, und es ist eine Teilklasse und keine Vollständigkeit.** Eine Flagge, die im
ZIEL statt in der Quelle löscht: `robocopy inbox archive/… /MIR`, `rsync --delete inbox/
archive/2026/`. Der Grund ist die REIHENFOLGE der Lesungen und nicht die Vokabelliste —
`_filing` erkennt beide als Kopierer, also beantwortet der Kopier-/Bewegungszweig die Aufrufung und
kehrt zurück, bevor irgendein zerstörendes Wort gesucht wird. Diese Reihenfolge ist kein
Versehen: eine Kopie IN das Archiv ist die gewöhnliche Ablage dieses Kits, und ohne den Vorrang
würde `rsync --remove-source-files inbox/x archive/…` als Löschung unter `inbox/`
verweigert. Beide Enden davon sind gemessen
(`tools/test_hooks.py::test_a_filing_move_with_a_source_deleting_copier_flag_is_judged_as_a_move`).

**Was stattdessen begrenzt.** Die Klasse steht namentlich im Kopf des Wächters, mit dieser
Reihenfolge als Grund; Verfassung und Rollentext des `records-clerk` zeigen seit TSK-0114 dorthin,
statt eine Zusage zu geben, die die Wand nicht hält. Eine Löschung in einem anderen
Programm (`python -c` mit `os.remove`) bleibt ebenfalls unsichtbar und gehört zu `H129`, nicht
hierher.

**Herkunft.** Prüferbefund P3 der Runde TSK-0107, in TSK-0113 als P12 im Wächterkopf
benannt, in TSK-0114 gegen den gemergten Baum neu gefahren, in TSK-0116 auf den Rest verkleinert.

**Urteil: verkleinert, gemessen, der Rest ist benannt.** Die allgemeinere Klasse — ein
zerstörendes Verb, das die Liste des Wächters gar nicht kannte — stand als `H125` und
ist geschlossen; was von ihrer Vokabelliste bleibt, steht als `H129`. Keiner der drei
Einträge steht für einen anderen ein.

### H124 — Die Fristenmeldung liest eine Uhr, die keinem Feld dieses Kits gehört (neu, TSK-0113, FR-0034)

**Mechanismus.** `_duties.briefing` nimmt `datetime.date.today()` der lokalen Maschine, einmal je
Sitzungsstart, und vergleicht jede Frist gegen diesen einen Wert. Die Zeitzone des Geschäfts steht
in keinem Feld des Kits, und die Sitzung liest ihre Uhr nicht noch einmal.

**Kette.** Zwei Richtungen, beide folgenlos für Zustand und Durchsetzung: eine Sitzung, die über
Mitternacht läuft, behält die Antwort von gestern — eine Frist, die heute DUE wird, bleibt in
dieser Sitzung stumm; und zwei Maschinen in verschiedenen Zonen beantworten denselben Moment
verschieden, sodass die Meldung des Nutzers und die eines Vertreters an einem Tag im Jahr
auseinanderfallen können.

**Was stattdessen begrenzt.** Die Tagesgrenze selbst ist gemessen und beidseitig gehalten
(`test_routine_feed.test_the_routine_is_due_again_on_the_monday_after_a_run` für den Takt der
Routine; die fünf Grenzfälle des Registers sind je einzeln rot gemessen). Das Register
SCHLÄGT VOR und entscheidet nichts: jede Frist geht durch den Nutzer. Und eine Meldung, die einen
Tag zu früh kommt, ist die sichere Richtung.

**Herkunft.** Strom G (TSK-0113), Rest 3 aus Abschnitt 9 seines Protokolls, ausdrücklich der
Merge-Runde zur Nummerierung übergeben.

**Urteil: Rest, benannt — nicht blockierend, und ohne Feld nicht schließbar.** Eine Zeitzone ist
eine Eigenschaft des Geschäfts; sie zu raten wäre falscher als sie nicht zu haben. Der Weg dahin
ist eine Onboarding-Frage und ein Feld in `business_profile.yaml`, also dieselbe Kette wie bei
`tax.filings` — und die gehört einer Runde, die das Interview anfasst, nicht dieser.

### H125 — Die Lösch-Regel des Archiv-Wächters war eine Verbliste, und jedes Verb daneben ging durch — GESCHLOSSEN (TSK-0114 gemessen, TSK-0116 behoben)

**Mechanismus, wie er bis TSK-0116 stand.** `guard_fs_tripwire` entschied „ist das eine
Löschung?" an einer AUFZÄHLUNG: `DELETE_VERBS = ("rm", "rmdir", "del", "erase", "rd",
"remove-item", "ri")`. Das war eine Liste von Schreibweisen, kein Begriff, und sie trug keinen
Stolperdraht an ihren Enden — nichts maß, ob ein Verb fehlt, und nichts maß, ob ein
gelistetes Verb noch etwas fängt.

**Gemessene Kette** (2026-09-03, Pilot außerhalb des Repos unter
`_round-scratch/TSK-0116/`, mit der ausgelieferten `.gitignore` des Office-Kits und einem echten
Beleg unter `archive/finance/2026/`; alle **acht** auf `Bash|PowerShell` registrierten Office-Haken
als Prozesse über `tools/test_hooks.py::run_hook_process` gefahren — eine Zeile erreicht das
Werkzeug nur, wenn alle acht sie durchlassen. NICHTS ausgeführt, gemessen wurde die
Entscheidung. Rigs: `_round-scratch/TSK-0116/probe_h125_v2.py` für diese Tabelle, `probe_h125_v3.py` für die Nacharbeit unten):

| Befehlszeile | HEAD e45c0ca | TSK-0116 |
|---|---|---|
| `unlink` auf den Beleg | ALLOW | **rc 2** |
| `git clean -fdx` über den ganzen Baum | ALLOW | **rc 2** |
| `git clean -fdx archive` | ALLOW | **rc 2** |
| `Clear-Content` auf den Beleg | ALLOW | **rc 2** |
| `find archive -name x.pdf -delete` (Flaggen-Form) | ALLOW | **rc 2** |
| `tar --remove-files … archive/…` (Flaggen-Form) | ALLOW | **rc 2** |
| `clc` auf den Beleg (Alias von Clear-Content) | ALLOW | **rc 2** |
| KONTROLLE `rm` auf denselben Beleg | rc 2 | rc 2 |
| KONTROLLE Bewegung aus dem Archiv | rc 2 | rc 2 |

Die beiden Flaggen-Formen gehören `H123` und sind dort mit derselben Messung eingetragen; sie
stehen hier, weil dieselbe Änderung sie mitgenommen hat.

**Die VORFAHREN-Form, Nacharbeit 1 (Prüferbefund B1), derselbe Pilot, dieselben acht Haken.**
Der erste Schnitt las die Reichweite nur in EINER Richtung — „liegt der Operand unter einem
Fach" — und nie die andere, „liegt ein Fach unter dem Operanden". Damit war jede Zeile, die die
Projektwurzel oder das Arbeitsverzeichnis benannte, ALLOW, während dieselbe Zeile ohne den
Punkt rc 2 war. Dass beide dieselbe Zerstörung sind, sagt der Befehl selbst: `git clean -ndx`
und `git clean -ndx .` drucken zeichengleich „Would remove archive/…".

| Befehlszeile | HEAD e45c0ca | erster Schnitt | Nacharbeit 1 |
|---|---|---|---|
| `git clean -fdx .` | ALLOW | ALLOW | **rc 2** |
| `git clean -fdx ./` | ALLOW | ALLOW | **rc 2** |
| `git clean -fdx -e docs` | ALLOW | ALLOW | **rc 2** |
| `rm -rf .` | ALLOW | ALLOW | **rc 2** |
| `find . -name '*.pdf' -delete` | ALLOW | ALLOW | **rc 2** |
| `Remove-Item -Recurse -Force .` (Bash und PowerShell) | ALLOW | ALLOW | **rc 2** |
| `shred .` | ALLOW | ALLOW | **rc 2** |

Verschärfend war der Verweigerungstext des ersten Schnitts: er nannte „Run the destruction with
the paths it should really touch, outside inbox/ and archive/" und schickte damit den Irrtum
geradewegs in die Umgehung. Er sagt jetzt ausdrücklich, dass das Benennen von Wurzel oder
Arbeitsverzeichnis dieselbe Verweigerung ist und ein Umschreiben der Zeile kein Weg heraus.

**Die Über-Verweigerung, abgewogen und gemessen** — dieselben acht Haken, derselbe Pilot:

| Befehlszeile | HEAD e45c0ca | TSK-0116 |
|---|---|---|
| `rm outbox/draft.txt` (Löschung außerhalb jedes Fachs) | ALLOW | ALLOW |
| `git clean -fdx docs` (Fegen an den Fächern vorbei) | ALLOW | ALLOW |
| `ls archive/finance/2026` | ALLOW | ALLOW |
| `cat` auf den Beleg | ALLOW | ALLOW |
| `clear` (das Terminal) | ALLOW | ALLOW |
| `git clean -fdx` in einem Projekt OHNE Fach von Rang | ALLOW | ALLOW |
| dieselbe Zeile mit `cwd=docs` | ALLOW | ALLOW |
| `cd docs && git clean -fdx` | ALLOW | ALLOW |
| `cd outbox && rm -rf .` | ALLOW | ALLOW |
| alle acht Vorfahren-Formen in einem Projekt OHNE Fach von Rang | ALLOW | ALLOW |

Die letzten vier Zeilen sind die Abwägung selbst. Eine Zerstörung reicht so weit wie das,
was sie benennt — und wenn sie nichts benennt, so weit wie das Verzeichnis, in dem sie läuft
(`guard_fs_tripwire.swallows_a_tray`, gegen die Basis aus `where_it_runs`). Ob diese Reichweite ein
Fach von Rang trifft, beantwortet das Dateisystem. Eine Wand ohne etwas dahinter wird umgangen;
deshalb wird in einem Projekt ohne Ablage nichts verweigert und in einem Unterverzeichnis, das kein
Fach enthält, ebenso wenig.

**Was an ihre Stelle trat, und was davon eine Definition ist.** Die Regel hat zwei Hälften und
nur eine ist eine Definition:

* **WO** (Definition, und die Hälfte, die `git clean` schließt): eine Zerstörung
  REICHT an eine Menge von Positionen — die benannten Pfade, und wenn sie keine nennt, das
  Arbeitsverzeichnis. Verweigert wird, wenn diese Reichweite ein Fach von Rang trifft, und das
  wird in BEIDEN Richtungen gelesen: die Position liegt IM Fach, oder ein Fach liegt IN der
  Position. Die zweite Richtung ist die Nacharbeit; ohne sie war die Vorfahren-Form ALLOW.
* **WAS** (Vokabelliste, und sie bleibt eine): ob ein Programm eine Datei entfernt oder leert, ist
  eine Tatsache über das Programm. Geändert hat sich die FORM der Liste — sie wird
  über jedes Wort einer Aufrufung gelesen (Kommandowort, Flagge, Unterbefehl) und nach
  Wortstamm statt nach exakter Schreibweise. Der Rest steht als `H129`, mit Messung.

**Die Frist, gegen die registrierte gemessen.** Die Office-Registrierung nennt für **keinen**
ihrer acht `Bash|PowerShell`-Einträge ein `timeout` (aus `settings/settings.json` gelesen, nicht
erinnert) — die Frist ist also das Standardfenster des Providers, das dieselbe Datei mit ~600 s
gemessen dokumentiert, und `_compat.HOOK_DEADLINE_SECONDS = 60.0` ist das Budget, das die Haken sich
selbst geben. Zwei Zahlen, weil zwei Fragen: der langsamste EINZELNE Haken-Prozess war
0,280 s (fünf Läufe der Zeile, die den Freigabespeicher wirklich öffnet, `time_worst_hook.py`;
der Prüfer maß auf seinem Piloten 0,899 s), und die langsamste ZEILE über alle acht Haken
zusammen war **1,276 s** (`probe_rework2.py`, 25 Zeilen × 8 Haken × 2 Bäume; der Prüfer maß
0,565 s). Ein Aufruf besteht aus allen acht, also ist die zweite die Zahl, gegen die geurteilt
wird — 2,1 % des Selbstbudgets von 60 s.

**`DEC-0056` gilt und spricht für den Bau, nicht dagegen.** Sie nimmt Unumkehrbares aus, und ein
gelöschter Beleg ist unumkehrbar; der Gegner ist hier der IRRTUM (`git clean` als
Aufräum-Reflex), nicht der Vorsatz.

**Herkunft.** Merge-Prüfung von TSK-0114 (2026-09-03), Befund B1; vom Umsetzer derselben Runde
gegen den ausgelieferten Baum nachgefahren (`_round-scratch/TSK-0114/probe_h125.py`).

**Die Basis, gegen die gemessen wird — und die Verengung, die sie zuerst kostete
(Nacharbeit 1 und 2).** Die Reichweite wird gegen die Basis gelesen, in der die Zeile wirklich
läuft (`where_it_runs`); sonst wäre jedes `git clean` in jedem Unterverzeichnis eines
Office-Projekts eine Verweigerung, und genau diese Über-Verweigerung bringt einen Nutzer dazu,
die Punkt-Schreibweise zu lernen. Der erste Schnitt dieser Verengung folgte `_filing`s eigener
Basis-Fortschreibung, die ein `cd` ÜBERALL in einer Aufrufung liest — auch eines, das nur ein
Argument ist. Gemessen war das eine aktive Unter-Verweigerung: `echo cd outbox ; rm -rf .`,
`grep -r cd outbox ; rm -rf .`, `ls cd outbox && rm -rf .` und `echo cd docs ; git clean -fdx`
waren rc 0, während `rm -rf .` allein rc 2 war. **Geschlossen in Nacharbeit 2**: die Basis wird
nur von einer Aufrufung fortgeschrieben, deren KOMMANDOWORT ein Verzeichniswechsel ist und die
`_filing.directory_change` als berechenbar meldet (`moves_the_working_directory`). Alle vier Zeilen
sind jetzt rc 2, die vier Kontrollen (`echo "cd outbox"`, `printf 'cd outbox'`, `echo cd $X`,
`echo cd archive`) bleiben rc 2, und M1 bleibt in beiden Richtungen: `cwd=docs` und
`cd docs && git clean -fdx` rc 0, `cd archive && git clean -fdx` rc 2,
`cd outbox && rm -rf .` rc 0, `cd $DIR && rm -rf .` rc 2 (unberechenbar → die Basis bleibt
stehen).

**Was dieser Eintrag NICHT deckt — die Klassen, die bis heute GEMESSEN sind** (Nacharbeit 2 und
3, derselbe Pilot, alle acht Haken). Der Satz sagt ausdrücklich nicht, dass es keine weiteren
gibt: er nennt, was nachgemessen wurde, und die vierte Zeile kam erst durch die dritte Prüfung
dazu. Für die ersten drei antworten HEAD und diese Runde identisch, es ist also nichts, was diese
Runde verschlechtert hätte:

| Klasse | Befehlszeile | HEAD | diese Runde |
|---|---|---|---|
| Operanden aus einer PIPE | `ls archive` weitergereicht an `xargs rm -rf` | rc 0 | rc 0 |
| dieselbe, mit Nullbyte-Trennung | `find . -print0` an `xargs -0 rm -rf` | rc 0 | rc 0 |
| dieselbe in PowerShell | `Get-ChildItem -Recurse` an `Remove-Item -Force` | rc 0 | rc 0 |
| Verzeichnis-LINK auf ein Fach | `rm belege/finance/2026/invoice.pdf` | rc 0 | rc 0 |
| derselbe Link als Ganzes | `rm -rf belege` | rc 0 | rc 0 |
| derselbe Link als ARBEITSVERZEICHNIS | `cd belege ; rm -rf .` | rc 0 | rc 0 |
| dieselbe, eine Ebene tiefer | `cd belege/finance ; rm -rf .` | rc 0 | rc 0 |
| dieselbe, fegend | `cd belege ; git clean -fdx` | rc 0 | rc 0 |
| GLOB-Form der Vorfahren-Zerstörung | `rm -rf *` | rc 0 | rc 0 |
| dieselbe, mit Punkt | `rm -rf ./*` | rc 0 | rc 0 |
| dieselbe, fegend | `git clean -fdx *` | rc 0 | rc 0 |
| ein `cd`, das LANDET, aber nicht wirkt (`H144`) | `cd outbox & rm -rf .` | rc 0 | **rc 2** (seit der Naht S9 der Merge-Runde) |

(a) **Die Pipe.** Das zerstörende Wort steht auf der Zeile, aber die Pfade, auf die es wirkt,
sind die AUSGABE der vorherigen Stufe — kein Wort der Zeile benennt sie. Die WO-Hälfte liest
nur Wörter, also liest sie „nennt nichts", und ein NENNENDES Wort, das nichts nennt,
zerstört nach dieser Regel nichts (dieselbe Begründung, die `clear` durchlässt — für
`xargs` ist sie falsch). Das ist weder `H129` (das Wort steht in der Liste) noch der
`python -c`-Fall (kein anderes Programm führt die Löschung aus).

(b) **Der Link.** Eine Junction `belege/ → archive/` macht denselben Beleg unter zwei Pfaden
erreichbar; `_filing.position` NORMALISIERT einen Pfad, sie löst ihn nicht auf. Derselbe Beleg
ist über den echten Pfad rc 2 und über den Link rc 0. Der Kopf des Wächters spricht unter
„WHAT OUT OF ARCHIVE MEANS" von jeder Schreibweise, DEREN TEXT DER PFAD IST — der Text eines
Links ist nicht der Pfad, und genau das steht seit Nacharbeit 2 in seiner Restliste.
**Die schwerere Hälfte ist der Link als ARBEITSVERZEICHNIS** (Prüferbefund M3, in Nacharbeit 4
auf eigenem Piloten nachgemessen): nach `cd belege` steht die Shell im Archiv, und die
Vorfahren-Form kostet dann nicht einen Beleg, sondern das ganze Fach — während derselbe Wechsel
über den echten Pfad rc 2 ist. Es ist dieselbe Klasse und keine neue Nummer: die Verengung aus
`M1` misst gegen ein Verzeichnis, dessen Namen sie nicht auflöst.

(c) **Der Glob.** `rm -rf *` ist die alltäglichste Schreibweise genau der Zerstörung, die
dieser Eintrag schließt. Der Mechanismus ist die Restliste des Wächters — ein Wort, das die
Shell vor dem Befehl umschreibt, ist nicht der Pfad, den der Befehl bekommt —, und dieser Eintrag
nennt ihn seit Nacharbeit 2 auch selbst, statt sich auf einen Verweis zu verlassen.

(d) **Ein Verzeichniswechsel, der landet, aber nicht wirkt** — `&&`-Kurzschluss, Pipe-Stufe,
Hintergrund. Er stand als eigener Eintrag `H144`, weil er eine Unter-Verweigerung dieser Runde war
und kein Altbestand: die Verengung, die `M1` billig macht, folgte ihm. **Seit der Merge-Runde
TSK-0120 ist er geschlossen**, in beiden Richtungen — der Wechsel, der nicht wirkt, und der
Wechsel, der ZURÜCK zu einem Fach führt —, und `H150` nimmt die Form dazu, die gar kein Ziel
ergibt (`popd`). Die Formen, in denen der Wechsel nicht LANDET (`cd nichtda`, ein Tippfehler,
`cd ..`), sind seit Nacharbeit 3 geschlossen. Diese Klasse zählt darum unten NICHT mehr zu den
nicht gedeckten.

**Urteil: GESCHLOSSEN für die benannte und die Vorfahren-Form; nicht gedeckt sind DREI der vier Klassen der Tabelle oben — Pipe, Link, Glob — und die Vokabelliste (`H129`). Die vierte (`H144`, ein Wechsel, der landet und nicht wirkt) ist seit TSK-0120 geschlossen, mit dem Preis, den `H144` und `H150` nennen.** Rot ohne den Fix:
`tools/test_hooks.py::test_the_archive_guard_refuses_a_destruction_that_is_not_spelled_rm` (sechs
Zeilen, jede einzeln),
`tools/test_hooks.py::test_a_destruction_that_names_an_ANCESTOR_of_a_tray_is_the_same_destruction`
(sieben Zeilen, jede einzeln, beide Tool-Namen),
`tools/test_hooks.py::test_an_exclusion_flag_does_not_narrow_a_sweep` für beide Enden der
Ausschluss-Flaggen, `tools/test_hooks.py::test_a_sweep_is_refused_only_where_a_tray_of_record_lies_under_it`
für beide Enden der Abwägung und der Basis, und
`tools/test_hooks.py::test_every_destroying_stem_is_load_bearing_at_both_ends` für den
Stolperdraht, den die alte Verbliste nie hatte.

### H126 — Die Ablaufregel für eine offene Anfrage steht dreimal, und die drei Leser stehen auf zwei Uhren (neu, TSK-0115, FR-0075)

**Mechanismus.** Seit FR-0075 beantwortet die Tafel „was wartet auf dich?" — dafür muss sie
`approvals/pending/` lesen und die Regel anwenden, die eine abgelaufene Anfrage nicht mehr als
offen zählt. Dieselbe Regel steht schon an zwei Stellen: `approvals.open_requests` fragt sie je
Datei über `pending_request`, `report.generate_session_brief` schreibt sie für den Sitzungsbrief
noch einmal aus. Die Tafel ist die dritte. Sie kann die erste nicht rufen, und der Grund ist
struktureller Natur: `approvals` importiert `state`, `state` importiert `board` — ein Import
zurück schlösse den Importgraphen des Pakets zu einem Zyklus. Drei Kopien einer Regel driften;
das ist die Fehlklasse.

Dazu kommt ein zweiter Unterschied, der auch nach einer geteilten Funktion bliebe: die drei Leser
stehen auf ZWEI Uhren. `approvals.open_requests` fragt `has_expired`, und das liest `time.time()`;
der Sitzungsbrief liest dieselbe Uhr beim Sitzungsstart; die Tafel liest den Stempel des
Zustandsschreibvorgangs, aus dem sie entstanden ist (`board._clock` — sie liest bewusst keine Uhr,
damit die Seite eine reine Funktion des Zustands bleibt und mit ihrem eigenen Index übereinstimmt).
Genau darum ist die Naht ein OPTIONALES `now`: die zwei Uhren bleiben zwei, aber die Regel wird
eine.

**Gemessene Kette** (2026-09-03, Store außerhalb des Repos, eine Anfrage mit 2 s Laufzeit über
`approvals.create_pending_request`, nichts von Hand geschrieben):

| Schritt | „wartet auf dich" |
|---|---|
| Tafel, im selben Moment geschrieben | **1** |
| Sitzungsbrief, drei Sekunden später | **0** |
| dieselbe Tafel auf der Platte, unverändert | **1** |
| Tafel nach dem nächsten Zustandsschreiben | **0** |

**Was stattdessen begrenzt.** Erstens der Paritätstest
`test_board.test_the_board_and_the_session_brief_agree_on_the_open_requests`: er baut einen Store
mit zwei offenen und einer abgelaufenen Anfrage, erzeugt Tafel und Brief im selben Moment und
vergleicht die Id-Mengen — verliert einer der beiden die Ablaufregel, wird er rot (in einer Kopie
außerhalb des Repos gemessen: `board.open_requests` gibt `[]` zurück → rot). Zweitens sagt die
Tafel in ihrem eigenen Kopf, dass ihr Zeitstempel der Vergleichspunkt ist und eine ältere Seite
eine ältere Antwort trägt. Was das NICHT begrenzt: dass beide Stellen dieselbe Regel *sind*.

**Naht an Strom C** (gemeldet, hier nicht geschrieben): `approvals.open_requests` **existiert
bereits** (`team-kits/kernel/approvals.py`, Signatur `open_requests(state)`), und die drei
`gate_approval.py` der Kits rufen sie mit **einem** Argument. Die Naht ist deshalb ein
**optionales** zweites Argument an der vorhandenen Funktion — `def open_requests(state, now=None)`
—, das die Tafel setzt und die Haken weglassen; keine neue Funktion.

Wörtlich angewandt gemessen (2026-09-03, Kopie außerhalb des Repos, beide Formen gegen dieselben
drei Tests):

| Form | Kanal-Test (1) | Ablauf-Test (2) | Parität (3) |
|---|---|---|---|
| `open_requests(state, now)` (Pflichtargument) | **rot** | **rot** | grün |
| `open_requests(state, now=None)` | grün | grün | grün |

(1) `tools/test_hooks_v2.py::test_a_relay_in_the_models_own_words_still_reaches_the_user`,
(2) `tools/test_hooks_v2.py::test_an_expired_request_is_not_open_and_a_reworded_relay_goes_silent`,
(3) `tools/test_board.py::test_the_board_and_the_session_brief_agree_on_the_open_requests`.
Daran hängt die zweite Lehre: der Paritätstest der Tafel sieht diesen Schaden **nicht**. Die Naht
braucht darum zwei Schiedsrichter, und der zweite ist (2).

**Stand nach der Merge-Runde TSK-0120: die REGEL ist eine, die Uhren bleiben zwei.** Die Naht ist
gebaut — `approvals.has_expired(request, now=None)` ist die eine Definition, `open_requests` und
`pending_request` reichen `now` durch, und die drei Leser fragen sie statt zu vergleichen: der
Sitzungsbrief (`report.generate_session_brief`), die Tafel (`board.open_requests`, über einen
aufgeschobenen Import, wie ihn `state.py` selbst dreimal benutzt) und die Haken. Die Tafel liest
weiter ihren Seitenstempel und der Brief die Wanduhr — das ist Absicht und der Grund, warum `now`
optional ist. Die WALK bleibt getrennt: die Tafel liest die Dateien selbst, durch `_flat`, weil ein
Anfragedatei eine handgeschriebene Datei ist. Beim Nachmessen fiel ein VIERTER Leser auf, den kein
Strom sehen konnte: `approvals.mint` verglich selbst und stieg auf einem unlesbaren Stempel mit
einem nackten `ValueError` aus (`float("soon")`) statt fail-closed zu verweigern — gemessen
`_round-scratch/TSK-0120/probe_expiry_readers.py`, vorher `ValueError`/`TypeError`, nachher
`ApprovalError` wie `pending_request`. Stolperdraht:
`tools/test_approvals_dispatch.py::test_every_reader_of_the_expiry_rule_asks_this_one` — er liest
am geparsten Paket, welche Funktion überhaupt gegen die Uhr vergleicht, und fährt die vier
unlesbaren Stempelformen durch alle Leser.

**Urteil: Rest, benannt — verkleinert auf die zwei Uhren.** Kein Angriff, kein Datenverlust — eine
Zahl kann zwischen zwei Berichten auseinanderlaufen, und die Kette dahin ist der normale Ablauf
einer Frist, nicht ein Fehler. Was blieb: zwei Uhren, mit Absicht.

### H127 — Eine Handänderung an einem erzeugten Diagramm sieht zwischen zwei Zustandsschreibvorgängen niemand (neu, TSK-0115, FR-0080)

**Mechanismus.** `kernel/plan_diagram.py` erzeugt `plan.drawio.svg` und `mindmap.drawio.svg` als
reine Funktion der Items und legt auf die Wurzel ein `data-source-digest`, mit dem
`plan_diagram.is_pristine` drei Fälle unterscheidet: unberührt, von Hand geändert, veraltet. Diese
Funktion ruft **niemand außer den Tests**. Kein Gate liest sie, `report.validate_state` liest sie
nicht, kein Kommando meldet ihr Urteil. Wer eine der zwei Dateien in draw.io öffnet, etwas
verschiebt und speichert, bekommt von diesem Apparat kein Wort — und verliert die Arbeit beim
nächsten Schreiben.

**Gemessene Kette** (2026-09-03, über den echten Zustand dieses Repos, 289 Items, Kopie außerhalb
des Repos):

| Zustand der Datei | `is_pristine` | wer sagt es einem laufenden Projekt |
|---|---|---|
| frisch geschrieben | `pristine` | — |
| ein `<text>` per ElementTree ergänzt (so speichert draw.io) | `hand-edited` | **niemand** |
| dieselben Bytes gegen einen verschobenen PR-Status | `stale` | **niemand** |

**Was stattdessen begrenzt.** `generated/` ist in der `.gitignore` jedes Kits: die Dateien werden
nie committet, eine Handänderung erreicht also weder eine Historie noch eine zweite Maschine. Und
der nächste Zustandsschreibvorgang überschreibt sie — **sobald** die eine Auslöserzeile aus dem
Protokoll dieser Runde in `state._write_board` steht. Bis dahin gilt die ehrlichere Fassung: die
zwei Dateien entstehen überhaupt nur, wenn jemand `plan_diagram.render_all` ruft, und nichts
behauptet an irgendeiner Stelle etwas anderes.

**Naht-Vorschlag an Strom C** (Vorschlag, keine Zusage): `report.validate_state` meldet `stale` und
`hand-edited` als Warnung. Das ist kein Gate — es hält niemanden auf — sondern die eine Stelle, an
der ein Projekt beim nächsten Bericht davon erfährt.

**Stand nach der Merge-Runde TSK-0120: die HÄLFTE ist geschlossen.** Die Auslöserzeile steht in
`state._write_board` — in einem `try` von SICH, damit die Meldung der Tafel nicht einen Verlust
behauptet, den eine nicht gezeichnete Grafik verursacht hat —, also entstehen die zwei Dateien bei
jedem Zustandsschreiben und der nächste Schreibvorgang überschreibt eine Handänderung wirklich.
Beide Enden: `tools/test_plan_diagram.py::test_a_state_write_leaves_both_diagrams_beside_the_board`.
`kernel.cli generate-index` nennt seitdem alle vier erzeugten Pfade, und der Schiedsrichter dafür
zählt nicht mehr, sondern leitet ab
(`tools/test_board.py::test_the_documented_command_names_every_artefact_it_writes`).

**Urteil: OFFEN, gemessen — die MELDUNG fehlt weiterhin.** Was zu, was offen ist: die Dateien
entstehen und veralten nicht mehr still, aber `plan_diagram.is_pristine` ruft nach wie vor nur der
Test. Wer zwischen zwei Zustandsschreibvorgängen von Hand ändert, hört kein Wort — er verliert die
Änderung jetzt nur zuverlässiger. Der Ort, an dem die Meldung liefe, ist `report.validate_state`.

### H129 — Was eine Zerstörung ist, bleibt eine Vokabelliste (neu, TSK-0116, FR-0050)

**Mechanismus.** Die WO-Hälfte der Zerstörungsregel ist eine Definition, die WAS-Hälfte
nicht: `guard_fs_tripwire.NAMING_DESTRUCTION` und `SWEEPING_DESTRUCTION` sind Wortstämme. Ob ein
Programm eine Datei entfernt, ist eine Tatsache über dieses Programm und aus der Befehlszeile
nicht ableitbar — ein `PreToolUse`-Haken läuft VOR der Zeile und hat kein Nachher, gegen das
er vergleichen könnte. Ein Programm, dessen Kommandowort, Flaggen und Unterbefehle keinen dieser
Stämme tragen, geht durch; dasselbe gilt für eine Löschung innerhalb eines anderen
Programms (`python -c` mit `os.remove`).

**Kette (gemessen, TSK-0116, derselbe Pilot):** `python -c "import os; os.remove('archive/…')"`
ist **rc 0** durch alle acht Haken — unverändert gegenüber HEAD, und im Kopf des
Wächters als erster Punkt unter „WHAT THIS DOES NOT SEE" benannt.

**Zwei Formen, die dazugehören, und beide sind gemessen.** Ein ALIAS trägt nur, wenn er
selbst ein Stamm ist: `Clear-Content` wird über `clear` gelesen, sein kanonischer Alias `clc`
war es nicht und ging rc 0 durch (Prüferbefund N2) — er steht seit der Nacharbeit in der
Liste, wie `ri` neben `Remove-Item`. Und ein Befehl, der eine Datei durch SCHREIBEN leert
(`Set-Content`, `sc`, `Out-File`, `dd of=…`, eine Umleitung), wird von dieser Regel überhaupt
nicht gelesen: sie fragt nach einem zerstörenden Wort, und keines dieser Worte ist eines.
Gemessen rc 0; die Umleitungs-Hälfte davon steht seit längerem im Kopf des Wächters.

**Was stattdessen begrenzt.** Drei Dinge, jedes gemessen: (1) jeder Eintrag ist an BEIDEN Enden
gemessen — die ausgelieferte Liste verweigert eine Zeile, und eine Kopie des Wächters ohne
genau diesen Eintrag lässt dieselbe Zeile durch
(`tools/test_hooks.py::test_every_destroying_stem_is_load_bearing_at_both_ends`, ein Fall je
Eintrag); (2) die Stämme werden über jedes Wort einer Aufrufung gelesen, also trägt jede
Flagge (`-delete`, `--remove-files`) und jeder Unterbefehl (`git clean`) ohne eigene Nennung;
(3) `DEC-0056`: der Gegner dieser Wand ist der IRRTUM, und ein Irrtum schreibt kein eigenes
Programm.

**Urteil: Rest, benannt — nicht schließbar auf der Ebene der Befehlszeile.** Was diesen
Eintrag schließen würde, ist eine Antwort auf der Ebene des Dateisystems, und die kann ein
Haken, der vor dem Befehl läuft, nicht geben.

### H130 — Die leere Aufbewahrung ist über `add-filing-rule` nicht erreichbar (neu, TSK-0116, FR-0049)

**Mechanismus.** Die Vorlage des Aktenplans nennt zwei ehrliche Formen für `retention`: eine
zählbare Spanne, oder `null` für ein Fach, dessen Uhr nicht am Jahresende beginnt. Seit
dieser Runde verweigert `kernel.filing.retention_refusal` alles dazwischen — aber die leere Form
ist über den sanktionierten Weg gar nicht zu bekommen: `approvals.filing_rule_subject_manifest`
verweigert schon die FRAGE nach einer Regel ohne Aufbewahrung, also kann keine Freigabe dafür
entstehen und `filing.apply` wird nie erreicht.

**Kette (gemessen):**
`tools/test_kernel.py::test_a_retention_the_deadline_register_cannot_read_is_refused_before_it_reaches_the_plan`
misst beides in einem: `filing.retention_refusal("")` ist `None` (der Leser nimmt die leere Form an)
und `approvals.filing_rule_subject_manifest(retention="")` wirft `ApprovalError`.

**Die zweite Hälfte desselben Eintrags: WELCHE Einheit zählt, ist eine Vokabelliste.**
`retention_span` und `_duties._retention_years` erkennen `y`, `yr`, `yrs`, `year`, `years`, `j`,
`jahr`, `jahre` — und sonst nichts. Gemessen mit Abhilfe verweigert werden darum `"10 Jahren"`,
die YAML-Ganzzahl `10`, `"10a"`, `"P10Y"`, `"zehn Jahre"` und `"6 Monate"`. Das ist eine geführte
Über-Verweigerung und kein stiller Verlust: die Verweigerung nennt die zwei Formen und ein
Beispiel. Sie zu erweitern heißt, sie in BEIDEN Lesern zu erweitern — der Kernel darf keinen
Kit-Haken importieren —, und dass die beiden eine Definition bleiben, misst
`tools/test_office_duties.py::test_the_kernel_and_the_duty_register_read_a_retention_the_same_way`
an den kompilierten Mustern selbst.

**Was stattdessen begrenzt.** Eine von Hand geschriebene Regel darf die leere Form tragen, und das
Fristenregister meldet eine Regel ohne Aufbewahrung gar nicht erst als unlesbar — sie
überspringt es stumm und richtig. Der Schaden ist also kein falscher Zustand, sondern ein Weg,
den ein Ablage-Fach ohne zählbare Frist nicht gehen kann.

**Urteil: Rest, benannt — nicht in diesem Strom schließbar.** `kernel/approvals.py` liegt im
`forbidden_scope` von TSK-0116; die Naht ist an Strom C gemeldet, wortwörtlich im
Strom-Protokoll.

### H131 — Die Zeilennummern der Anlage EÜR stammen nicht aus dem amtlichen Vordruck (neu, TSK-0116, FR-0076)

**Mechanismus.** Das Kit liefert seit dieser Runde ein Standardvokabular aus, in dem jede Kategorie
die Zeilennummer der Anlage EÜR trägt
(`team-kits/office-team/templates/project_memory/master_data.yaml`, Block `euer_form:`). Die Zahlen
stammen aus öffentlichen Ausfüllhilfen, gelesen am 2026-09-03; der amtliche Vordruck und
seine Anleitung wurden NICHT gelesen und werden nicht mitgeliefert.

**Kette (gemessen beim Lesen der Quellen):** zwei der gelesenen Ausfüllhilfen widersprachen sich
bei der Werbe-Zeile (51 gegen 54), und dieselbe Beschriftung stand zwischen zwei Formularjahren auf
verschiedenen Zeilen (Waren/Roh-/Hilfsstoffe: 25 in einer undatierten Hilfe, 27 für 2024 und
2025). Eine falsche Nummer landet in einer Aufstellung, die für die Steuerberatung gedacht ist.

**Was stattdessen begrenzt.** Formularjahr und Herkunft stehen IM Vokabular und nicht im Code, beide
Leser (`scripts/euer_report.py`, `tools/finance_dashboard.py`) drucken sie neben jede Zeilensumme,
und im Code steht keine Zeilennummer und kein Jahr — eine Korrektur ist genau eine Zeile in
einer Nutzerdatei. Dieselbe Doktrin trägt schon die Aufbewahrungsfrist im Aktenplan („kein
primärer Rechtstext gelesen, Ausgangspunkt für das Gespräch mit der
Steuerberatung"). Der Bericht trägt seinen Rechtshinweis auf jeder Seite. Gemessen:
`tools/test_finance_dashboard.py::test_a_fresh_project_ships_a_category_vocabulary_the_p4_12_stall_cannot_recur_on`
hält fest, dass Jahr und Herkunft im Vokabular stehen und jede Kategorie eine Zeilennummer
trägt.

**Urteil: Rest, benannt — nicht ohne primäre Quelle schließbar.** Was ihn schlösse,
ist ein gelesener amtlicher Vordruck je Formularjahr, und das ist eine Pflege-Aufgabe pro Jahr und
keine Codezeile.

### H132 — Eine Antwort autorisiert jetzt N Ziele statt eines (neu, TSK-0117, FR-0074)

**Mechanismus.** Bis zu dieser Runde war jede item-gebundene Freigabe an GENAU EIN Item gebunden:
`approvals.assert_apr_in_force` verglich `apr["item"]` mit der Id des Vorgangs, und ein `scope`-Ja
konnte nichts anderes freigeben. Die Plan-Freigabe (`approvals.PLAN_KIND`) bricht diese Bindung
absichtlich: ihr Subjekt ist eine LISTE, und ein einziger Klick lässt jedes Ziel darin die Kante
`DRAFT -> APPROVED` gehen. Damit hängt die Breite der Erlaubnis nicht mehr an der Frage, sondern
an der Zahl der offenen Ziele im Speicher zum Zeitpunkt der Frage.

**Gemessene Kette** (2026-09-03, Pilotprojekt außerhalb des Repos,
`_round-scratch/TSK-0117/m1_plan.py`; der Haken `gate_approval.py` als echter Prozess):

| Schritt | Ergebnis |
|---|---|
| zwei Ziele erfasst, `request-approval plan` | eine Frage, die BEIDE Ziele namentlich nennt |
| Antwort über den ausgelieferten Haken | `APR-0001`, rc 0 |
| `transition PR-0001 APPROVED` | rc 0, `approval_ref: APR-0001` |
| `transition PR-0002 APPROVED` | rc 0, `approval_ref: APR-0001` — **eine Antwort, zwei Ziele** |
| `transition PR-0001 IN_DELIVERY` | verweigert: „a delivery approval commits" |

**Was stattdessen begrenzt, und zwar gemessen.** (1) Nur die Scope-Frage: Lieferung und Abnahme
bleiben je Ziel — dieselbe Messung, letzte Zeile. (2) Der Hash geht über die Liste UND über das
Scope-Manifest jedes einzelnen Ziels, also über dessen Akzeptanzkriterien: ein geändertes Ziel
fällt aus der Deckung, während die übrigen gedeckt bleiben (`m2_plan_invalidate.py`: `PR-0002`
nach einer Änderung wieder DRAFT und erneut gefragt, `PR-0001` weiter gedeckt). Das gilt auch für
eine Änderung AM KERNEL VORBEI, weil der Vergleich den Hash aus dem aktuellen Inhalt neu rechnet.
(3) Ein Ziel, das nach der Freigabe erfasst wird, steht nicht in der Liste und ist nicht gedeckt.
(4) Eine Plan-Freigabe über eine LEERE Liste wird verweigert, bevor jemand gefragt wird.
(5) Die Frage nennt jedes Ziel mit Id, Titel und Revision — nie eine Zahl.

**Was das NICHT begrenzt.** Die Länge der Liste. Ein Projekt mit dreißig offenen Zielen stellt
EINE Frage, deren Text dreißig Zeilen lang ist, und ein Nutzer, der sie nicht zu Ende liest,
unterschreibt dennoch alle dreißig. Der Kernel kann das nicht messen — er weiß nicht, was gelesen
wurde —, und eine künstliche Obergrenze wäre eine Zahl ohne Messung dahinter. Ebenfalls nicht
begrenzt: die Felder, die das Scope-Manifest ohnehin nicht trägt (`approvals._SCOPE_FIELDS`); eine
Änderung daran fällt hier so wenig auf wie bei einer Einzelfreigabe.

**Urteil: OFFEN als benannte Verbreiterung, nicht als Defekt.** Sie ist der Preis, den FR-0074
ausdrücklich kauft (gemessen: drei Nutzerfreigaben je Ziel, also dreißig Fragen bei zehn Zielen),
und die Gegenrechnung steht in der Entscheidung `DEC-0068`, die der Nutzer daraufhin getroffen
hat (die Vorlage `project_memory/staging/TSK-0117/dec-plan-approval.json` bleibt als historischer
Stand liegen und ist nicht mehr der Maßstab). Was ein Nutzer entscheiden musste, war nicht
„schließen oder nicht", sondern ob er die Breite will; sie ist gewollt, hier benannt, und die
Lieferseite trägt die Kontrolle.

### H133 — Der SDK-Weg prägt ohne die dritte Bedingung, und jedes Programm, das die Brücke ruft, prägt (neu, TSK-0117, FR-0083)

**Mechanismus.** `approvals._assert_minting_caller` kannte eine Route und drei Bedingungen: ein
geladenes `_kernel`-Brückenmodul, der unmittelbare Aufrufer IST die Haken-Datei, und `__main__` ist
dieselbe Datei. Die zweite Route (`kernel/sdk_approval.py`, der Einstieg aus `canUseTool`) kann die
dritte Bedingung nicht tragen: das einbettende Programm IST `__main__`, per Konstruktion. Geprüft
wird dort nur der unmittelbare Aufrufer. Damit prägt jedes Programm, das dieses Paket importiert
und `mint_from_can_use_tool` ruft — ohne Haken, ohne Provider, ohne Nutzer.

**Gemessene Kette** (2026-09-03, `_round-scratch/TSK-0117/m3_sdk.py`, Pilot außerhalb des Repos):

| Aufrufer | Ergebnis |
|---|---|
| ausgelieferter `gate_approval.py` als Prozess | `APR-0001`, `minted_via: user_answer_via_approval_hook` |
| `sdk_approval.mint_from_can_use_tool` | `APR-0002`, `minted_via: program_answer_via_agent_sdk` |
| derselbe Ruf für eine `push`-Freigabe | verweigert („cannot take back") |
| `approvals.mint` direkt aus einem fremden Skript | verweigert (kein Brückenmodul) |

**Was stattdessen begrenzt, gemessen.** (1) Der Stempel: jede Freigabe trägt ihre Route, und
`approvals.approval_card` liest sie aus dem Datensatz — ein Auditor sieht hinterher, wer der
Richter war. (2) Der Kernel verweigert dem Programm jede Art aus `approvals.IRREVERSIBLE_KINDS`,
also alles, was das Projekt nicht selbst zurücknehmen kann; gemessen an `push`, mit der
Gegenprobe, dass danach kein lebendes Push-Token existiert. (3) `gate_git` verweigert als Prozess
jeden Merge/Push über einen Vorgang, dessen vorgezeigte Freigabe ein Programm geprägt hat
(`m4_gate.py`, rc 2). (4) Für einen Aufrufer, der die Brücke NICHT ruft, ändert sich nichts.

**Was das NICHT begrenzt, und der Vorgänger-Satz gilt weiter.** Gegen einen VORSÄTZLICHEN Fälscher
war schon die Haken-Route nichts wert (`_assert_minting_caller` sagt das seit 2026-07-25 in ihrem
eigenen Kopf: jede der drei Bedingungen ist prozessinterner Zustand, den der Aufrufer umschreiben
kann). Was diese Runde wirklich verbreitert, ist die VERSEHENTLICHE Fläche: ein Import genügt.
Ebenfalls offen bleibt, was `H80` beschreibt — dass der Haken selbst aus jeder stdin-Nutzlast
prägt, die die Form einer Antwort hat.

**Urteil: OFFEN als benannte Verbreiterung.** Sie ist der Zweck von FR-0083 und der Grund, warum
der Stempel überhaupt existiert: das SDK löst die Vertrauensfrage nicht, es verlagert sie (§10).
Nicht schließbar von innen, aus demselben Grund wie bei der Haken-Route — prozessinterner Zustand
prüft prozessinternen Zustand. Wer sie enger will, braucht eine Grenze AUSSERHALB des Prozesses
(eine Berechtigungsregel, die einem Agenten den freien Interpreter verwehrt), und das ist dieselbe
Bedingung (ii), die `report.capability_matrix` seit jeher als `approval_provenance: unverified`
meldet.

### H134 — `blocked` ist ein Zustand, keine Messung (neu, TSK-0117, FR-0082)

**Mechanismus.** `backlog_types.EVIDENCE_RESULTS` kennt seit dieser Runde einen dritten Ausgang.
Der Kernel verlangt zu einem `blocked` den Satz, der sagt, WAS den Lauf verhindert hat
(`state.capture_preflight`), und `gate_git` liest ihn vor und sagt dazu, dass nichts geprüft wurde.
Niemand misst nach, ob der Browser wirklich fehlte. Der Wert macht aus einer Ehrlichkeitspflicht
einen Zustand; er fügt der Frage „ist das wahr?" nichts hinzu.

**Gemessene Kette** (2026-09-03, `_round-scratch/TSK-0117/m4_gate.py`, ausgelieferter `gate_git.py`
als Prozess auf einem Piloten außerhalb des Repos):

| Schritt | Ergebnis |
|---|---|
| `evidence --result blocked` ohne Satz | Kernel verweigert und nennt die Flagge |
| dasselbe mit `--blocked-reason "no Chromium on this runner"` | `EVD-0003 test: blocked` |
| `git merge feat/PR-0001-x` | rc 2; die Verweigerung zitiert den Satz und sagt „Nothing was checked" |

**Was stattdessen begrenzt.** Ein falsches `blocked` KAUFT nichts: es schließt den Merge genau so
wie ein `fail`, also gewinnt eine Rolle dadurch keinen Schritt, den sie sonst nicht hätte. Was es
verändert, ist allein die Auskunft an einen späteren Leser — und die trägt seit dieser Runde den
Satz, dass sie eine Aussage der Rolle ist und keine Messung des Harness. Der Datensatz ist
unveränderlich (`IMMUTABLE_TYPES`), also bleibt die Behauptung mit ihrem Urheber stehen.

**Was das NICHT begrenzt.** Die Wahrheit der Begründung. Und den umgekehrten Fall: ein Lauf, der in
Wahrheit rot war, kann als `blocked` gebucht werden; die Schranke merkt es nicht, weil beide
schließen — der Unterschied trifft erst den Menschen, der das Protokoll später liest.

**Urteil: OFFEN und nicht schließbar, weil außerhalb der Reichweite des Harness.** Das ist die
Grenze, die die Wunschliste §7 selbst zur Bedingung des Baus gemacht hat; sie steht hier, im
Vokabular-Kommentar an `EVIDENCE_RESULTS`, in der Hilfe der Befehlsflagge und in der Verweigerung
des Merges — an keiner davon als Schutzbehauptung, sondern als Einschränkung.

### H135 — Der Zeugen-Halbteil der Überlappungsprüfung ist eine Stichprobe, keine Sprache (neu, TSK-0118, FR-0021)

**Mechanismus.** Die Überlappungsprüfung (seit TSK-0120 nur noch `kernel.scopes`) fragt
„gehört dieser Pfad beiden Aufträgen?“ mit
EINEM Prädikat (`gate_write_scope._matches`) über ZWEI Universen: die Dateien, die der Baum heute
trägt, und je einen Zeugen pro Scope-Eintrag. Ein Zeuge entsteht, indem jeder Wildcard-Lauf durch
EIN Platzhalter-Segment ersetzt wird (`src/**` wird `src/_`). Das deckt den häufigen Fall — zwei
Aufträge, die dasselbe noch leere Verzeichnis beanspruchen — und es deckt nicht die Sprache: wo
sich zwei Muster nur in einer Region schneiden, in die kein so gebildeter Pfad fällt, sieht die
Zeugen-Hälfte nichts.

**Gemessene Kette** (2026-09-03, `_round-scratch/TSK-0118/probe_h135.py`; beide Aufträge durch
`ProjectState.capture` erfasst, der Prüfer als Prozess gefahren):

| Auftrag A | Auftrag B | Baum | rc |
|---|---|---|---|
| `allowed_scope: [a/*x]` | `allowed_scope: [a/y*]` | ohne `a/` | **0** (kein Befund) |
| dieselben | dieselben | mit `a/yx` | 2, `file a/yx` |

`a/yx` liegt in beiden Scopes; die Zeugen sind `a/_x` und `a/y_`, und keiner von beiden liegt im
Scope des anderen.

**Was stattdessen begrenzt.** Drei Dinge, und keines davon behauptet Vollständigkeit: die
Baum-Hälfte fängt genau diesen Fall, sobald die erste passende Datei existiert — also
spätestens, wenn ein Strom sie anlegt und der nächste Schnitt geprüft wird; das Werkzeug
verweigert nirgends etwas, es ist ein Instrument des Orchestrators vor dem Spawn; und der Schnitt
selbst ist nach `DEC-0062` ein Urteil, dessen Stolperdraht die Nahttabelle der Merge-Runde ist.
Die vollständige Antwort wäre ein Schnitt-Test über zwei Glob-Sprachen (Automaten statt
Stichprobe); das ist ein eigener Bau und nach `DEC-0056` kein Gerüst, das dieses Haus trägt.

**Urteil: Rest, benannt.** Der Docstring von `witnesses` nennt genau diese Grenze mit demselben
Beispiel, und dieser Eintrag ist die Messung dazu.

### H136 — Die Vor-Dispatch-Prüfung hat in einem Kit-Projekt keinen ausführbaren Weg (neu, TSK-0118, FR-0021)

**Mechanismus.** `gate_write_scope` verweigert jede Befehlszeile, die die Durchsetzungsschicht
nennt und in einer schreibfähigen Stufe steht — unabhängig davon, ob sie wirklich schreibt. Ein
Skill wird vom Scaffold nach `.claude/skills/<name>/` kopiert und vom Codex-Generator nach
`.agents/skills/<name>/` gespiegelt. Beide Pfade nennen die Schicht. Ein Prüfskript IM Skill — der
einzige Ort, an dem es aus dem `allowed_scope` dieses Items überhaupt landen könnte — ist damit
eine Zeile, die niemand ausführen darf.

**Gemessene Kette** (2026-09-03, dev-team-Projekt aus den Kit-Vorlagen außerhalb des Repos, der
ausgelieferte Haken als Prozess mit JSON auf stdin; `_round-scratch/TSK-0118/probe_cmdline.py` und
`probe_cmdline2.py`):

| Befehlszeile | rc |
|---|---|
| `python .claude/skills/parallel-streams/check_scope_overlap.py` | **2** — „names the enforcement layer in a pipeline that can write“ |
| dieselbe Zeile mit `.agents/skills/parallel-streams/...` | **2** |
| `python scripts/kit_checks.py` | 0 |
| `python scripts/harness.py check-scopes` | 0 |
| `git ls-files` | 0 |

**Was stattdessen begrenzt.** Dass kein Text etwas anderes behauptet, und dass dieser Satz selbst
gemessen ist: der Verfassungsabsatz in allen drei Kits und die Abschnitte 2 und 7 des
`parallel-streams`-Skills sagen, dass nichts ein überlappendes Paar verweigert, und
`tools/test_parallel_streams.py::test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap`
führt zwei Aufträge mit demselben `allowed_scope` über den echten Dispatch bis `LEASED`. Für die
Werkstatt selbst ist die Prüfung gebaut (`tools/check_scope_overlap.py` — seit TSK-0120 die
Kommandozeile vor `kernel.scopes`) und hat auf dem echten
Generation-3-Schnitt geantwortet.

**Stand nach der Merge-Runde TSK-0120: GESCHLOSSEN für die Frage, die der Titel stellt.** Das
Kernel-Verb, das dieser Eintrag als die richtige der beiden Antworten benannt hat, ist gebaut
(Strom C, `kernel/scopes.py` + `check-scopes`), und in der Werkstatt gemessen: der Lauf über die
fünf Aufträge dieser Generation nennt 15 überlappende Paare und endet rc 2. Es gibt damit einen
ausführbaren Weg in einem Kit-Projekt — `python scripts/harness.py check-scopes` —, und der Weg,
den dieser Eintrag als versperrt gemessen hat (ein Skript IM Skill-Verzeichnis), bleibt versperrt
und muss es nicht mehr sein. Die zweite Kopie ist in derselben Runde verschwunden:
`tools/check_scope_overlap.py` trägt kein Prädikat mehr, sondern nur noch die Kommandozeile davor.

**Urteil: GESCHLOSSEN — die Frage dieses Eintrags ist der ausführbare WEG, und den gibt es.** Was
daneben offen bleibt, ist ein anderer Satz und gehört nicht in diesen Eintrag: nichts VERWEIGERT
einen überlappenden Schnitt — die Prüfung ist ein Kommando, kein Gate; `create_lease` und `gate_dispatch` lassen zwei
Aufträge mit demselben `allowed_scope` bis `LEASED` durch (C-2/C-3 aus Strom D, nicht gebaut,
Generation 4). Der Kit-Text behauptet weiterhin nichts anderes, und das ist gemessen
(`tools/test_parallel_streams.py::test_nothing_shipped_refuses_two_tasks_whose_scopes_overlap`).

### H137 — Ein Haken-Docstring nennt einen Takt, den keine Verfassung mehr nennt (neu, TSK-0118, N2)

**Mechanismus.** Der Takt des Auditors steht im Code: `_routine.audit_period_id` beantwortet „ist
er in dieser Periode gelaufen?“ mit einer ISO-Wochen-Id, und der Rumpf der drei
`agents/project-auditor.md` sagt seit E3, der Takt stehe im Code und nicht ein zweites Mal dort.
Der MODUL-Docstring derselben mitgelieferten Datei sagt daneben, jede Verfassung reite die Rolle
auf einem wöchentlichen Rhythmus.

**Gemessene Kette** (2026-09-03, über den ausgelieferten Baum): vor dieser Runde nannte genau EINE
der drei Verfassungen einen Takt — die Rollenzeile in `office-team/constitution/AGENTS.md` —,
dev und research nennen beim `project-auditor` keinen. Diese Runde hat die Office-Zeile und die
`description` aller drei Rollendateien auf den Rumpfsatz gebracht (N2), also nennt jetzt KEINE
Verfassung einen Takt, während der Docstring drei behauptet.

**Was stattdessen begrenzt.** Kein Verhalten hängt an dem Satz: er ist ein Docstring, kein Leser
wertet ihn aus. Der Takt selbst ist beidseitig gemessen
(`tools/test_routine_feed.py::test_a_run_in_an_earlier_week_leaves_the_routine_due` und
`tools/test_routine_feed.py::test_the_routine_is_due_again_on_the_monday_after_a_run`), und dass
ihn kein Rollen- oder Verfassungstext ein zweites Mal nennt, hält
`tools/test_parallel_streams.py::test_no_text_that_describes_the_audited_role_states_the_cadence_the_code_owns`.

**Urteil: Rest, benannt, in diesem Item nicht schließbar.** `team-kits/*/hooks/**` steht im
`forbidden_scope` dieses Items, und die Datei ist in allen drei Kits byte-identisch — die
Korrektur ist ein Dreifach-Spiegel plus Stempel und gehört in die Runde, die diese Datei besitzt.

### H138 — Die Konformitätsbefunde des Renderers verweigern nichts: der Datensatz beantwortet eine andere Frage (neu, TSK-0119, FR-0077/FR-0078)

**Mechanismus.** `kit_design_render.py` prüft den gerenderten Entwurf seit TSK-0119 gegen den
mechanisch entscheidbaren Anteil der Design-Standards und meldet Befunde mit **rc 3**. Der
Datensatz `review/render.json` wird dabei **trotzdem** geschrieben, und `gate_design_sighted` liest
genau ihn — der Haken fragt „wurde dieser Entwurf gerendert", nicht „ist er in Ordnung". Eine Rolle,
die den Rückgabewert ignoriert, präsentiert also einen Entwurf mit Befunden, ohne dass irgendetwas
verweigert.

**Gemessene Kette** (2026-09-03, Projekt ausserhalb des Repos, ausgeliefertes Skript und
ausgelieferter Haken je als Prozess):

| Schritt | Ergebnis |
|---|---|
| Entwurf mit Kontrast 1,92:1 gestagt, `python scripts/kit_design_render.py TSK-0007` | **rc 3**, Befund gedruckt, `review/render.json` geschrieben |
| `gate_design_sighted` auf eine `AskUserQuestion`, die diesen Entwurf nennt | **rc 0** — der Haken lässt durch |

Gehalten von `tools/test_design_conformance.py::test_a_record_is_written_even_when_the_checks_find_something_and_the_sighting_gate_still_opens`,
und zwar in beide Richtungen: der Test wird auch rot, wenn der Renderer anfängt, den Datensatz bei
einem Befund zurückzuhalten.

**Warum das so gebaut ist und nicht als Gate.** `DEC-0056` (b): ein Gate wird nur für eine
Fehlklasse gebaut, für die ein Fall gemessen vorliegt. Der einzige gemessene Fall dieser Gegend ist
`BUG-0076` — ein Entwurf, den niemand gesehen hat —, und den trägt `gate_design_sighted` bereits.
Für „ein Entwurf mit einem Kontrastfehler erreicht den Nutzer" gibt es in diesem Repo keinen
gemessenen Vorfall; ein Haken darauf wäre Gerüst über dem Haus. Ein Zurückhalten des Datensatzes
wäre ausserdem die schlechtere Verweigerung: die Meldung, die der Designer dann läse, hiesse
„nobody has rendered this draft", und er suchte den Fehler an der falschen Stelle.

**Was stattdessen begrenzt.** Der Rückgabewert und der gedruckte Befund je Entwurf; die
`product-designer`-SKILL-Zeile, die die drei Rückgabewerte einzeln erklärt und `3` als
Vertragsdefekt benennt; und die Zeile in `hooks/ENFORCEMENT.md`, die ausdrücklich sagt, dass dieser
Haken darüber **nicht** urteilt. Nicht begrenzt: nichts hindert eine Rolle daran, den
Rückgabewert nicht zu lesen — dieselbe Klasse wie jede andere Prosa-Pflicht dieses Kits.

**Urteil: BENANNTE AUSNAHME, vom Nutzer abgenommen am 2026-09-03 (`DEC-0069`)** — nicht „kommt später“, sondern der Zustand, den `DEC-0056` für diese Klasse als Ergebnis vorsieht.
Der Nutzer hat sie auf genau dieses Beispiel hin erteilt: ein Entwurf mit Kontrast 2,1:1 und zwei
Hauptknöpfen erzeugt rc 3, der Umschlag trägt es, der PM schickt zurück — und nichts hindert das
Einfrieren. Sein Wort: „melden reicht vorerst“; der Datensatz dazu ist `DEC-0069`, und was dort steht, steht nicht noch einmal hier. **Die Bedingung, unter der die Ausnahme fällt**, ist
ebenfalls abgenommen: der erste echte Fall, in dem ein Entwurf MIT Befunden trotzdem gebaut oder
eingefroren wurde, macht daraus ein Gate. Wer diesen Fall sieht, trägt ihn hier ein und hebt die
Ausnahme; bis dahin ist diese Zeile die einzige Stelle, an der die Grenze steht.

### H139 — Die BUILD-Hälfte der Standard-Härtung ist nicht gebaut, weil ihre beiden Wirtsdateien in ein fremdes Kit gespiegelt sind (neu, TSK-0119, FR-0077)

**Mechanismus.** `FR-0077` verlangt die mechanisch prüfbaren Hälften; die Synthese verortet C1/C2/C3
im schon gebooteten `browser_smoke()` und B3 (Farbliterale im Anwendungscode) auf dem Walker
`kit_checks._frontend_sources()`. Beide Wirtsdateien liefern **dev-team und research-team
byte-gleich** aus, `research-team/**` stand im `forbidden_scope` von TSK-0119, und eine einseitige
Änderung bricht die Spiegelregel (`tools/test_hooks.py::test_shared_kit_files_identical`).
Gebaut wurde deshalb die frühere Stelle: der gestagte DSN-Entwurf, dessen Renderer `dev-team`
allein ausliefert.

**Gemessen** (2026-09-03, sha256 der ausgelieferten Dateien, gekürzt):

| Datei | dev-team | research-team |
|---|---|---|
| `templates/repo/scripts/kit_browser_checks.py` | `fa3d1cfca4` | `fa3d1cfca4` |
| `templates/repo/scripts/kit_checks.py` | `0fbe55bf08` | `0fbe55bf08` |
| `templates/repo/scripts/quality.py` | `3e3e11f368` | `3e3e11f368` |
| `templates/repo/scripts/kit_design_render.py` | — (kein Spiegel, nur dev-team) | — (liefert es nicht) |

**Was dadurch heute ungeprüft bleibt, benannt statt weggeredet:** ein Frontend, das die eingefrorene
DSN NICHT einhält, wird von nichts gemessen — Kontrast, Tastaturpfad, reduzierte Bewegung und
Farbliterale werden am Vertrag geprüft, nicht am Erzeugnis. Der Vertrag ist die frühere und
billigere Stelle, aber er ist nicht dieselbe.

**Was stattdessen begrenzt.** Der Vertrag selbst: die eingefrorene DSN trägt die Werte, und der
`quality-engineer` vergleicht in der Fidelity-Runde Screenshots des Builds gegen die Mockups. Das
ist Urteil, keine Messung, und diese Zeile sagt genau das.

**Urteil: OFFEN, gemessen, nicht in diesem Strom schliessbar.** Der Fix ist ein Bau an
`kit_browser_checks.py` + `kit_checks.py` MIT der Spiegelung nach `research-team` (oder mit einem
`KIT_SPECIFIC_SCRIPTS`-Eintrag samt Grund — der wäre heute keiner, denn ein Research-Projekt mit
Frontend hat dieselbe Pflicht). Das gehört in eine Runde, deren Dateihoheit beide Kits umfasst.

### H140 — Die Rangfolge-Prüfung urteilt über das, was der Entwurf DEKLARIERT, und der Kontrast schweigt über das, was er nicht ausrechnen kann (neu, TSK-0119, FR-0077/FR-0078)

**Mechanismus.** Zwei Grenzen desselben Bauprinzips („lies den Teil, der läuft"), beide in der
stillen Richtung:

1. **Rangfolge.** Die Regel „genau ein primäres Ziel je View" wird über `[data-view]`-Container
   entschieden. Ein Mockup, das **keinen** View deklariert, hat für diese Regel keinen View — die
   Prüfung schweigt nicht mehr, seit `N8` in der Nacharbeit gebaut wurde — der Ausweg aus der
   Regel bleibt, sie nicht anzuwenden, aber er ist sichtbar: der Lauf druckt eine
   `NOT DECIDABLE`-Zeile über den ganzen Entwurf („no [data-view] container, so the
   one-primary-goal rule judged nothing here") und schreibt sie in den Datensatz. Nicht
   beurteilt und beurteilt-und-in-Ordnung sind damit unterscheidbar. Gehalten von
   `tools/test_design_conformance.py::test_a_draft_that_declares_no_view_says_so_instead_of_saying_nothing`.
2. **Kontrast.** Steht Text über einem Bild oder einem Verlauf oder über einer halbdurchsichtigen
   Schicht, gibt es keine zweite Farbe zum Rechnen. Diese Stellen werden als `NOT DECIDABLE`
   gedruckt und in den Datensatz geschrieben — sie zählen weder als Befund noch als bestanden.

**Gemessene Kette** (2026-09-03, ausgeliefertes Skript als Prozess, ein Projekt ausserhalb des
Repos, ein und dasselbe Markup mit ZWEI `data-primary-action`):

| Entwurf | rc | Befund |
|---|---|---|
| Container trägt `data-view="uebersicht"` | **3** | „view 'uebersicht' declares 2 primary action(s)" |
| derselbe Container ohne `data-view` | **0** | keiner |
| Text über `linear-gradient(#fff, #eee)` | **0** | `NOT DECIDABLE … a background image or gradient behind the text` |

**Was stattdessen begrenzt.** Für (1): die `product-designer`-SKILL-Zeile macht das Auszeichnen zum
Verfahrensschritt und sagt in einem Satz, dass die Prüfung „die Rangfolge beurteilt, die du
behauptet hast, nie die, die du übersprungen hast" — und der Fidelity-Review der Phase 3 vergleicht
die sichtbare Inventarliste gegen die Mockups. Für (2): die Zeile wird gedruckt, also sieht der
Designer, welche Stellen er selbst ansehen muss; gehalten von
`tools/test_design_conformance.py::test_a_value_the_check_cannot_decide_is_named_and_is_not_a_finding`,
das beide Hälften prüft — der Satz muss erscheinen UND der Lauf muss 0 bleiben.

**Drei weitere Mechanismen derselben Klasse, in der Nacharbeit gemessen und benannt statt
geschlossen** (Prüfung von TSK-0119, M3/M5/M6):

3. **„Fokus sichtbar“ heißt hier „die beiden PNGs sind byte-verschieden“.** Die Messtechnik ist stabil
   (gegengeprüft), die DEFINITION ist die Grenze: ein Fokusring in der Hintergrundfarbe
   (`outline: 3px solid var(--bg)`) und eine Farbänderung um EINE Kanaleinheit sind beide
   byte-verschieden und beide unsichtbar — gemessen **rc 0**. Der Fix wäre eine Schwelle über der
   Kanaldifferenz statt Byte-Ungleichheit; das braucht einen PNG-Dekoder, den dieses Kit nicht
   ausliefert. Was stattdessen begrenzt: die Regel fängt weiter den häufigen Fall (`outline: none`,
   gar keine Regel), und der Designer sieht den Fokus in Schritt 2 der SIGHT-Schleife selbst.
4. **Die Sonde liest den DEKLARATIVEN Zustand des Light DOM, einmal, beim Laden.** Kein Shadow
   Root, kein Zustand, den ein Skript nach dem Laden herstellt, und kein Handler, den ein Skript
   anhängt (`addEventListener`); das `onclick` der Auszeichnung selbst wird seit der Nacharbeit
   gelesen. Ein selbständiger Design-Entwurf ist genau so ein Dokument — deshalb ist die Grenze
   hier billig; für einen gebauten App wäre sie es nicht (das ist `H139`).
5. **Farbliterale in SVG-Präsentationsattributen sind seit der Nacharbeit GESCHLOSSEN**, und zwar
   als Eigenschaft statt als Attributliste: ein Attribut zählt, wenn dieser Browser seinen NAMEN
   als CSS-Eigenschaft mit diesem Wert annimmt (`CSS.supports(name, value)`). `<rect fill="#ff0000">`
   war vorher rc 0, ist jetzt rc 3; `class`, `id` und `d` fallen von selbst heraus, und
   `fill="var(--brand)"` bleibt rc 0. Gehalten von
   `tools/test_design_conformance.py::test_a_colour_literal_in_a_presentation_attribute_is_one_too`,
   das beide Richtungen misst.

**Urteil: Rest, benannt.** (1) ist keine schliessbare Lücke, sondern die Grenze jeder Prüfung über
eine Deklaration: einen View ohne Auszeichnung könnte nur ein Urteil erkennen, und ein Urteil ist
genau das, was §1a der Designerin lässt. (2) ist ein echtes Rechenproblem und in der lauten
Richtung offen (eine Farbe schätzen wäre eine Zahl, die niemand nachrechnen kann).

### H141 — Der Takt-Leser ist eine Aufzählung von Adverbien (neu, TSK-0118 Nacharbeit 1, N2)

**Mechanismus.** `tools/test_parallel_streams.py::test_no_text_that_describes_the_audited_role_states_the_cadence_the_code_owns`
hält die Regel „der Takt steht im Code, nicht ein zweites Mal im Rollentext“. Ob ein Satz
einen Takt nennt, entscheidet `_CADENCE_IN_PROSE` — eine Liste von Adverbien. Die Klasse
„eine Periode, anders geschrieben“ steht nicht darin, und „ist dieser Satz eine
Taktangabe“ ist Weltwissen, das sich aus dem Baum nicht ableiten lässt.

**Gemessene Kette** (2026-09-03, `_round-scratch/TSK-0118/probe_h141.py`, der Leser des
ausgelieferten Suite-Stands):

| Text | Leser |
|---|---|
| `weekly / event-triggered READ-ONLY reviewer` (die Wendung, die diese Runde entfernt hat) | **feuert** |
| `runs once a week` | still |
| `on Mondays` | still |
| `every seven days` | still |
| `runs each Monday morning` | still |
| `cadence: 7d` | still |
| `wöchentliche` (gebeugt) | still |

**Was stattdessen begrenzt.** Drei Dinge. Der Leser trägt seine Grenze im eigenen Docstring und
führt die blinden Formen als eigene, grüne Testzeilen mit — die Grenze
ist damit gelesener Code, nicht Prosa. Das Subjekt ist klein und bekannt: EIN Rollentext je Kit plus
die Verfassungsblöcke, die ihn nennen; ein Autor, der dort eine Umschreibung einführt, tut
das gegen den Rumpfsatz derselben Datei. Und der Schaden ist eine Doppelnennung, kein Angriff: der
Takt selbst bleibt beidseitig gemessen
(`tools/test_routine_feed.py::test_a_run_in_an_earlier_week_leaves_the_routine_due`).

**Urteil: Rest, benannt.** Die vollständige Antwort wäre ein Sprachmodell-Urteil über
Prosa oder eine größere Aufzählung; das eine ist kein Test, das andere derselbe Defekt
eine Runde später. Nach `DEC-0056` ist beides Gerüst über dem Haus.

### H142 — Eine genannte Route, die auflöst und trotzdem kein Paar ergibt, bleibt rc 0 (neu, TSK-0118 Nacharbeit 1, FR-0021)

**Mechanismus.** Die Werkstatt-Kommandozeile trennt seit dieser Nacharbeit zwei Klassen: was der
Aufrufer GENANNT hat, muss auflösen (rc 1), was niemand genannt hat, ist kein Fehler (rc 0). Die
Trennung ist nötig, weil der Lauf ohne Argumente außerhalb eines Projekts eine gemessene
Anforderung ist. Dazwischen liegt ein Fall, den keine der beiden Regeln fängt: `--only` mit
genau einer echten Id — die Route löst auf, ein Paar entsteht trotzdem nicht.

**Gemessene Kette** (2026-09-03, `_round-scratch/TSK-0118/probe_m4_m5.py`, der Prüfer als
Prozess über einem durch den Kernel erfassten Projekt):

| Aufruf | rc |
|---|---|
| `--root <pfad>-typo` | **1**, „no such directory“ |
| `--only TSK-0001 TSK-0404` | **1**, nennt `TSK-0404` |
| `--only TSK-0001` | 0, „NOTHING WAS COMPARED“ |
| ohne Argumente außerhalb eines Projekts | 0, „NOTHING WAS COMPARED“ |

**Was stattdessen begrenzt.** Die Meldung: in jedem dieser Fälle steht „NOTHING WAS
COMPARED“ und niemals das Wort „disjoint“ — die beiden Antworten teilen kein Wort,
und beide Enden davon sind gemessen
(`tools/test_parallel_streams.py::test_a_route_the_caller_named_has_to_resolve_and_one_nobody_named_does_not`).
Strenger geht es nicht, ohne den argumentlosen Lauf zu brechen, den
`tools/test_hooks_v2.py::test_a_repo_tool_that_imports_the_kit_tree_leaves_no_bytecode_in_it`
fährt.

**Urteil: Rest, benannt.** Wer `--only` mit einer Id ruft, hat nicht nach einem Vergleich gefragt;
das als Fehler zu werten wäre eine zweite Regel neben der einen, die hier trägt.

### H143 — Eine Naht, die einen TEIL der Überlappung deckt, deckt ihn weiterhin zu (neu, TSK-0118 Nacharbeit 1, FR-0021)

**Mechanismus.** Eine erklärte Naht (`--seam`) wird von der Überlappungsprüfung
abgezogen, weil `DEC-0062` (5) genau dafür da ist: Dateien, die kein Strom allein besitzen kann,
werden vorher benannt und in der Merge-Runde angewendet. Seit dieser Nacharbeit wird eine Naht
verweigert, die die GESAMTE Ownership eines der beiden Aufträge deckt — dann wäre die
Prüfung ein Nichts mit grünem Anstrich. Eine Naht, die nur einen TEIL der Überlappung
deckt, während beide Aufträge anderswo noch etwas besitzen, bleibt zulässig — und
deckt diesen Teil zu.

**Gemessene Kette** (2026-09-03, `_round-scratch/TSK-0118/probe_m4_m5.py` plus die dritte Sonde in
`tools/test_parallel_streams.py::test_a_seam_that_swallows_an_orders_whole_ownership_is_refused`):

| Aufträge | Naht | rc |
|---|---|---|
| `src/**` gegen `src/**`, `src/a.py` im Baum | `**` | **1**, „swallows a whole ownership“ |
| dieselben | `src/**` | **1** |
| `src/**`+`notes/holes.md` gegen `lib/**`+`notes/holes.md` | `notes/holes.md` | 0 (die Naht, um die es geht) |
| `src/**`+`lib/**` gegen `src/**`+`docs/**`, `src/a.py` im Baum | `src/**` | 0 — `src/a.py` bleibt gedeckt |

**Was stattdessen begrenzt.** Die Naht ist eine ERKLÄRUNG des Orchestrators und keine Ableitung
des Werkzeugs: sie steht auf der Kommandozeile (bis `seam_scope` als Item-Feld existiert, siehe die
Anforderung an den Kernel-Strom im Rundenprotokoll), jeder von ihr gedeckte Pfad wird als
`seam`-Zeile GEDRUCKT statt verschwiegen, und die Merge-Runde wendet genau diese Liste an. Eine zu
weit erklärte Naht ist dort ein Befund gegen den SCHNITT — der Stolperdraht, den
`DEC-0062` (5) für diesen Fall vorsieht.

**Urteil: Rest, benannt.** Die Alternative wäre, eine Naht nur noch auf Dateiebene zuzulassen
(keine Wildcards). Das ist eine Entscheidung über die Form der Nahttabelle und gehört zu
`seam_scope`, nicht in dieses Werkzeug.

### H144 — Die Verengung folgt einem Verzeichniswechsel, der landet, aber nicht wirkt (neu, TSK-0116, FR-0050)

**Mechanismus.** Damit `git clean -fdx` in einem Unterverzeichnis kein Fehlalarm ist, misst die
Reichweite einer Zerstörung gegen das Verzeichnis, in dem die Zeile wirklich läuft
(`guard_fs_tripwire.where_it_runs`, `moves_the_working_directory`; `H125`, Befund M1). Diese
Fortschreibung fragt seit Nacharbeit 3, ob das Kommandowort ein Wechsel ist, ob das Ziel berechenbar
ist und ob es als Verzeichnis INNERHALB des Projekts existiert. Was sie nicht fragen kann, ist, ob
der Wechsel für die nächste Aufrufung überhaupt WIRKT: ein `&&` kann kurzschließen, und
ein `cd` in einer Pipe-Stufe oder hinter `&` läuft in einer Subshell und lässt die Shell
stehen, wo sie war.

**Kette (gemessen, Nacharbeit 3, Pilot außerhalb des Repos, alle acht auf Bash und PowerShell
registrierten Office-Haken als Prozesse, nichts ausgeführt; `rm -rf .` allein ist rc 2):**

| Befehlszeile | Urteil |
|---|---|
| `false && cd outbox ; rm -rf .` | **rc 0** |
| `ls` in eine Pipe an `cd outbox`, danach `rm -rf .` | **rc 0** |
| `cd outbox` in eine Pipe an `rm -rf .` | **rc 0** |
| `cd outbox & rm -rf .` | **rc 0** |
| KONTROLLE `cd nichtda ; rm -rf .` (landet nicht) | rc 2 |
| KONTROLLE `cd docs2 ; rm -rf .` (Tippfehler) | rc 2 |
| KONTROLLE `cd .. ; rm -rf .` (landet außerhalb) | rc 2 |
| KONTROLLE `cd archive && rm -rf .` | rc 2 |
| KONTROLLE `cd outbox && rm -rf .` | rc 0 |

**Warum es nicht in dieser Runde schließbar ist.** Alle vier brauchen den TRENNER zwischen zwei
Aufrufungen — `&&`, `|`, `&`, `;` sind vier verschiedene Antworten auf die Frage „wirkt der
Wechsel für das, was danach kommt". `_filing._walk` schneidet die Zeile mit `INVOCATION_RX` und
gibt den Trenner nicht heraus; `office-team/hooks/_*.py` liegt im `forbidden_scope` dieses Stroms.
Die Anforderung ist als Naht an Strom C/D gemeldet und steht wörtlich im Stromprotokoll
(`project_memory/staging/TSK-0116/stream-protocol.md`, Abschnitt 12.3).

**Was stattdessen begrenzt.** Drei Dinge, jedes gemessen: (1) die Hälfte, in der der Wechsel gar
nicht landet, ist geschlossen — und das ist die Unfallform, die `DEC-0056` meint (ein Tippfehler
im Verzeichnisnamen), `tools/test_hooks.py::test_a_directory_change_that_never_lands_does_not_move_the_sweep`;
(2) die Gegenrichtung ist unberührt: ein wirklicher `cd` verengt weiter, und `cd archive && rm -rf
.` bleibt rc 2; (3) nach `DEC-0056` ist der Gegner der IRRTUM, und ein Irrtum schreibt kein `&`,
keine Pipe und kein `false &&` vor sein `rm`.

**Stand nach der Merge-Runde TSK-0120: GESCHLOSSEN, mit einem benannten Preis.** Die Naht S9 ist
gebaut: `_filing._walk` gibt je Aufrufung ein VIERTES Feld heraus — den Trenner, der davor stand,
gelesen aus derselben Zerlegung, die `INVOCATION_RX` ohnehin macht (`finditer` statt `findall`,
der Zwischenraum IST der Operator) —, und `_filing.changes_the_calling_shell` liest ihn: ein
Wechsel wird nur fortgeschrieben, wenn der Trenner davor weder `&` noch `|` trägt (sonst ist das
Laufen nicht sicher) und der Trenner dahinter nicht das EINZEICHIGE `|` oder `&` ist (sonst läuft
der Wechsel in einer Subshell). Gemessen an einem Pilotprojekt über den ausgelieferten Wächter als
Prozess, vorher/nachher (`_round-scratch/TSK-0120/s9_probe.py`):

| Befehlszeile | vorher | nachher |
|---|---|---|
| `false && cd outbox ; rm -rf .` | rc 0 | **rc 2** |
| `ls \| cd outbox ; rm -rf .` | rc 0 | **rc 2** |
| `cd outbox \| rm -rf .` | rc 0 | **rc 2** |
| `cd outbox & rm -rf .` | rc 0 | **rc 2** |
| KONTROLLE `cd outbox && rm -rf .` | rc 0 | rc 0 |
| KONTROLLE `cd outbox ; rm -rf .` | rc 0 | rc 0 |
| KONTROLLE `cd docs && git clean -fdx` | rc 0 | rc 0 |
| KONTROLLE `cd archive && rm -rf .` | rc 2 | rc 2 |
| KONTROLLE `rm -rf .` | rc 2 | rc 2 |
| KONTROLLE `cd nichtda ; rm -rf .` | rc 2 | rc 2 |
| KONTROLLE `echo cd outbox ; rm -rf .` | rc 2 | rc 2 |

**Die erste Fassung dieser Naht war nur in EINER Richtung fail-closed** — Befund B1 der
Merge-Prüfung. Sie hat den unsicheren Wechsel übersprungen und die alte Position stehen lassen,
und eine stehen gelassene Position ist genau so lange harmlos, wie der übersprungene Wechsel von
einem Fach WEG führt. Führt er ZURÜCK, bleibt eine harmlose Basis stehen, während die Shell auf
der Wurzel fegt. Gemessen über jeden Haken, den das Office-Kit auf `Bash` registriert, als
Prozesse (`_round-scratch/TSK-0120/verify_tools/b1_repro.py`), mit `rm -rf .` allein bei rc 2:

| Befehlszeile | erste Fassung der Naht | nach der Nacharbeit |
|---|---|---|
| `cd outbox && cd .. && rm -rf .` | rc 0 | **rc 2** |
| `cd outbox && cd .. ; rm -rf .` | rc 0 | **rc 2** |
| `cd outbox ; true && cd .. ; rm -rf .` | rc 0 | **rc 2** |
| `pushd outbox > /dev/null ; popd ; rm -rf .` | rc 0 | **rc 2** |
| KONTROLLE `cd outbox ; cd .. ; rm -rf .` | rc 2 | rc 2 |

Die vierte Zeile ist Altbestand und nicht diese Naht — sie steht als `H150` mit ihrer eigenen
Kette —, wird aber von derselben Mechanik geschlossen und ist darum hier mitgemessen.

**Was der Fix ist:** die Position ist eine MENGE möglicher Positionen. Ein sicherer Wechsel
ERSETZT sie, jeder andere FÜGT hinzu, und die Zerstörung wird verweigert, sobald IRGENDEIN
Kandidat ein Fach von Rang enthält. Das ist die Lesart, die der Satz „fail-closed“ vorher schon
behauptet hat, und die der Code nicht gebaut hat.

**Eine zweite Verkürzung derselben Stelle, gefunden von der Wiederholungsprüfung (B2).** Die erste
Fassung der Menge hat den nächsten Wechsel aus dem NEUESTEN Kandidaten ausgerechnet und ihn bei
einem sicheren Wechsel durch dieses eine Ergebnis ersetzt. Ein RELATIVES Ziel bedeutet aber von
jedem Kandidaten aus etwas anderes: `cd ../outbox` landet von `docs` aus im `outbox` des Projekts
und von der Wurzel aus AUSSERHALB. Nach einem unsicheren Wechsel ist der neueste Kandidat gerade
die Position, an der die Shell vielleicht nie war — und der Wurzel-Kandidat fiel weg. Schiedsrichter
war eine echte bash (`_round-scratch/TSK-0120/verify_tools/shell_truth.py`), nicht eine Überlegung:

| Befehlszeile | echte bash steht danach in | Haken vorher | Haken nachher |
|---|---|---|---|
| `cd docs \| true ; cd ../outbox ; rm -rf .` | der Wurzel | **rc 0** | **rc 2** |
| `false && cd docs ; cd ../outbox ; rm -rf .` | der Wurzel | **rc 0** | **rc 2** |
| `cd docs \| true ; cd ../docs/inner ; rm -rf .` | der Wurzel | **rc 0** | **rc 2** |
| KONTROLLE `cd docs ; cd ../outbox ; rm -rf .` | `outbox` | rc 0 | rc 0 |

Seitdem wird der Wechsel aus JEDEM Kandidaten ausgerechnet, und die Menge trägt die Ergebnisse
aller.

**Der Preis, und es sind vier Über-Verweigerungen** — jede gemessen, jede fail-closed:
`true && cd outbox ; rm -rf .`, `cd outbox ; cd .. | true ; rm -rf .`,
`cd outbox ; cd $X ; rm -rf .` und `pushd outbox ; pushd sub ; popd ; rm -rf .` (mit vorhandenem
`outbox/sub`; echte bash steht danach in `outbox`, der Wächter verweigert). Ob die linke Seite
eines `&&` geglückt ist, wohin ein `cd $X` führt und was ein `popd` vom Stapel nimmt, sind keine
Eigenschaften der Befehlszeile — der Zweifel wird fail-closed beantwortet. Die 18 legitimen
Kontrollen sind unverändert.

**Der fünfte Preis gehört POWERSHELL**, und er entsteht aus einer Regel, die für die andere Shell
richtig ist: `changes_the_calling_shell` liest ein einzeichiges `|` als „Subshell“, weil eine
Bash-Pipeline eine ist. Eine PowerShell-Pipeline ist keine — sie läuft im selben Prozess —, also
verweigert die Regel dort mehr, als sie müsste. Gemessen über die auf `PowerShell` registrierten
Haken als Prozesse (dritte Merge-Prüfung):
`Set-Location docs | Out-Null ; Set-Location ../outbox ; rm -rf .` ist **rc 2**, während die Shell
wirklich in `outbox` steht; `Set-Location outbox ; rm -rf .` bleibt rc 0 und
`Set-Location archive ; rm -rf .` rc 2. Fail-closed und darum kein Loch, aber ein Preis, der hier
steht statt unbenannt zu bleiben.

**Was hier KEIN Preis ist, gemessen:** ein absoluter `cd`. Der Wächter folgt ihm vollständig — die
dritte Merge-Prüfung hat es in einem leerzeichenfreien Piloten gemessen
(`C:/tmp_nospace_probe/office`, danach gelöscht): `cd C:/…/office/outbox ; rm -rf .` ist rc 0,
quotiert ebenso rc 0, und `cd C:/…/office/archive ; rm -rf .` ist rc 2. In dieser Klasse gibt es
also keine Über-Verweigerung. Was wie eine aussah, ist etwas anderes: trägt der Pfad ein
Leerzeichen und steht unquotiert da, ist er rc 2 — und das ist die richtige Antwort, denn eine echte
bash antwortet auf dieselbe Zeile `cd: too many arguments` und bleibt stehen, weil ein unquotiertes
Wort mit Leerzeichen auch für sie zwei Argumente sind.

**Alle Enden, und welcher Test welche Hälfte hält — gemessen, nicht behauptet.** Der Fix hat vier
Hälften, und keine davon hält ein einzelner Test:

| Hälfte | gehalten von |
|---|---|
| ein unsicherer Wechsel FÜGT einen Kandidaten hinzu | `tools/test_hooks.py::test_a_change_the_shell_may_not_have_made_leaves_both_positions_open` |
| ein unberechenbarer Wechsel fügt die Wurzel hinzu (`H150`) | derselbe |
| die Zerstörung fragt JEDEN Kandidaten, nicht nur den neuesten | `tools/test_hooks.py::test_a_directory_change_the_shell_never_performs_does_not_move_the_sweep` |
| der Wechsel wird aus JEDEM Kandidaten ausgerechnet (B2) | `tools/test_hooks.py::test_a_relative_change_is_computed_from_every_position_it_could_start_in` |

Jede Zeile ist in einer Kopie außerhalb des Repos einzeln rot gemessen worden, und jede genau in
ihrem eigenen Test: die Rückkehr zur Lesart der Nacharbeit 1 und die Berechnung aus dem neuesten
Kandidaten machen ausschließlich den B2-Test rot, während die drei anderen grün bleiben.

**Urteil: GESCHLOSSEN in beiden Richtungen; der Preis sind fünf benannte Über-Verweigerungen** — vier in der Bash-Lesart, eine in PowerShell.
Was daneben offen BLEIBT, gehört `H125` und nicht hierher: Operanden aus einer Pipe, ein
Verzeichnis-Link auf ein Fach, und die Glob-Vorfahrenform.

### H145 — Ein Blatt, dessen Regeln das Dokument nicht lesen darf, war für die Prüfung ein leeres Blatt — GESCHLOSSEN bis auf die verbleibende Unentscheidbarkeit (neu, Prüfung TSK-0119, FR-0077)

**Mechanismus.** Die Sonde von `kit_design_render.py` läuft über `document.styleSheets` und fragt
jedes Blatt nach `cssRules`. Unter `file://` wirft ein VERLINKTES Blatt dabei einen `SecurityError`.
Der erste Bau hat diesen Wurf stumm verschluckt — das Blatt zählte damit als leer, während seine
Regeln vollständig in Kraft waren. Das erzeugte zwei Fehler auf einmal, in beide Richtungen.

**Gemessene Kette** (Prüfung von TSK-0119, ausgeliefertes Skript als Prozess auf einem Projekt
außerhalb des Repos, Entwurf mit `<link rel="stylesheet" href="tokens.css">`):

| Was nur im verlinkten Blatt stand | Urteil vor dem Fix |
|---|---|
| Farbliteral `#ff00ff` | **rc 0** — kein Wort, obwohl die Regel wirkt |
| `:focus-visible`-Regel | **rc 3** mit „the draft declares no :focus-visible rule at all" — eine Anschuldigung über eine Regel, die genau dort steht |

Das widersprach zugleich dem Kopfkommentar des Skripts, der sagt, Unentscheidbares werde als
`UNDECIDED` gelistet.

**Was jetzt läuft.** Der `catch` schreibt einen `undecided`-Eintrag mit `sheet.href` („this document
may not read that stylesheet's rules, so every colour literal and every :focus-visible rule in it is
IN EFFECT and unjudged"), und die Absage-Aussage wird **qualifiziert statt
unterdrückt**: sie lautet „no :focus-visible rule in the sheets this run could read (N sheet(s)
unreadable, named below — the rule may be in one of them)" und bleibt ein Befund. Rot ohne den
Fix:
`tools/test_design_conformance.py::test_a_stylesheet_this_document_may_not_read_is_undecided_and_never_an_accusation`
misst beide Hälften.

**Die Gegenlücke des ersten Fixes, gemessen und geschlossen.** Der erste Bau ließ den Befund ganz
fallen, sobald IRGENDEIN Blatt unlesbar war — global statt qualifiziert. Ein Entwurf ohne jede
`:focus-visible`-Regel plus ein verlinktes, völlig unbeteiligtes `print.css` kam damit **rc 0**
zurück (Wiederholungsprüfung TSK-0119). Was ein unlesbares Blatt wegnimmt, ist das Wort „at
all", nicht der Befund. Rot ohne diesen zweiten Fix:
`tools/test_design_conformance.py::test_an_unreadable_sheet_does_not_buy_a_draft_out_of_the_focus_rule_finding`.

**Die zweite Gegenlücke, gemessen und geschlossen (dritte Prüfung).** Der Regel-Walk stieg über
`rule.cssRules` ab; ein `@import` hält seine Regeln aber unter `rule.styleSheet.cssRules` und
wurde nie betreten. Weil das IMPORTIERENDE Blatt lesbar ist, entstand dabei auch kein Eintrag in
`unreadable_sheets` — also kam die Absage-Aussage UNqualifiziert heraus, während die einzige
`:focus-visible`-Regel des Entwurfs eine Ebene tiefer stand und wirkte, und ein Farbliteral dort
stumm durchging. Gemessen: inline `@import url("theme.css")` mit beidem → **rc 3** mit dem
unqualifizierten Satz und ohne `NOT DECIDABLE`-Zeile. Der Walk betritt `styleSheet.cssRules`
jetzt im selben `try/catch` und schiebt im `catch` denselben Eintrag mit dem `href` des Imports.
Rot ohne diesen Fix (beide Richtungen, ein Lauf je Richtung):
`tools/test_design_conformance.py::test_an_imported_sheet_this_document_may_not_read_is_recorded_like_any_other`
und `tools/test_design_conformance.py::test_an_imported_sheet_that_can_be_read_is_read` — die
zweite misst den lesbaren Fall (`data:`-Import), in dem die Regel gefunden und das Literal
gemeldet werden muss.

**Was OFFEN bleibt, und das ist alles, was dieser Eintrag noch trägt.** Die Regeln jedes Blattes,
das dieses Dokument nicht lesen darf — verlinkt oder importiert —, sind **nicht beurteilbar**: ein Farbliteral darin wird nicht gefunden, ein Kontrast, den
es setzt, wird über die gerenderten computed styles zwar mitgemessen, aber die Token-Disziplin nicht.
Was stattdessen begrenzt: die Zeile nennt das Blatt beim Namen, und die Designer-SKILL verlangt
ohnehin eine **selbstständige** HTML (CSS inline), in der dieser Fall gar nicht entsteht — er trifft
den Entwurf, der die Konvention verlässt.

**Urteil: Anschuldigung und Schweigen GESCHLOSSEN, die Unentscheidbarkeit OFFEN und benannt.**

### H146 — Der Kontrast sah zwei Sorten Text nicht: verblasste Elemente und erzeugten Text — GESCHLOSSEN bis auf die Gruppen-Komposition (neu, Prüfung TSK-0119, FR-0077)

**Mechanismus.** Zwei Blindstellen der ersten Kontrastfassung, beide in der stillen Richtung:

1. **`opacity` unter 1 galt als deckend.** Die Sichtbarkeitsfrage ging an `checkVisibility`, das nur
   „ganz unsichtbar" von „sichtbar" trennt; alles dazwischen wurde mit voller Farbe gerechnet.
2. **Text, den ein Pseudo-Element erzeugt** (`::before { content: "Neu" }`), hängt an keinem
   Kindknoten und wurde deshalb von der Textsuche nie gesehen.

**Gemessene Kette** (Prüfung von TSK-0119, dieselbe Umgebung):

| Entwurf | Urteil vor dem Fix |
|---|---|
| `.card { opacity: .05 }` mit Text darin | **rc 0** — falsch grün, der Text ist nicht zu entziffern |
| `::before { content: "Neu"; color: #bbbbbb }` auf weiß | **rc 0** — nie beurteilt |

**Was jetzt läuft.** Die Deckkraft der ganzen Vorfahrenkette wird als Produkt in die Alpha des
Textes gefaltet, und der Befund nennt sie („at opacity 0.05"); `::before` und `::after` werden über
`getComputedStyle(el, part)` mitgemessen, mit ihrer eigenen Deckkraft und ihrem eigenen Hintergrund.
Rot ohne den Fix: `tools/test_design_conformance.py::test_a_faded_element_is_judged_on_the_colour_the_reader_gets`
und `tools/test_design_conformance.py::test_text_a_pseudo_element_generates_is_text`.

**Die Umkehrung des ersten Fixes, gemessen und geschlossen.** `rendered()` wurde über das ELEMENT
gefragt, nie über das Pseudo-Element — also bekam `::before { display: none }` auf einer gut
sichtbaren Karte Kontrastbefunde („contrast 1.00:1 … at opacity 0", Textprobe leer), genau die
Umkehrung der Regel eine Verzweigung darüber. `checkVisibility` reicht nicht an ein
Pseudo-Element, also werden dessen eigene `display`, `visibility` und `opacity` gefragt, und ein
leerer `content`-String erzeugt eine Box und keinen Text. Rot ohne diesen zweiten Fix:
`tools/test_design_conformance.py::test_a_pseudo_element_nobody_can_see_is_not_judged_either`
(vier Fälle); die Gegenrichtung hält
`tools/test_design_conformance.py::test_a_pseudo_element_inside_a_hidden_element_stays_unjudged`.

**Die zweite Umkehrung, gemessen und geschlossen (dritte Prüfung).** Die Menge der geprüften
Pseudo-Elemente war `["::before", "::after"]` — eine Aufzahlung ohne Stolperdraht. Gemessen:
`.inp::placeholder { color: var(--faint) }` auf einem `<input placeholder="Suchbegriff">` und
`li::marker { color: var(--faint) }` waren beide **rc 0**; der Platzhalter ist der klassische
Kontrastfehler eines Mockups. Beide sind jetzt in der Menge, und jeder Eintrag sagt, WIE der Text
ihn erreicht — `::before`/`::after` über `content`, `::placeholder` über das Attribut,
`::marker` über den Listenstil; für die letzten beiden rechnet `content` zu `normal`, eine
einzige Regel wäre also für drei von vier falsch gewesen. Rot ohne den Fix:
`tools/test_design_conformance.py::test_the_text_of_a_placeholder_is_text` und
`tools/test_design_conformance.py::test_the_bullet_of_a_list_is_text`, beide mit Gegenrichtung
im selben Test (kein Attribut / `list-style-type: none` → rc 0).

**Diese Menge bleibt eine LISTE, und sie hat keinen Stolperdraht — der Grund steht im Code.**
CSS schließt die Menge der Pseudo-Elemente (erfinden kann sie niemand), aber das DOM bietet
keinen Weg zu fragen, welche ein Element HAT: `getComputedStyle(el, part)` antwortet für jede
Schreibweise, gültige wie ungültige. Es gibt also nichts, wogegen eine Liste zu messen wäre,
und keine Messung, die einen toten oder einen fehlenden Eintrag fände. **Was das kostet, ist
damit der Rest dieses Eintrags:** ein textführendes Pseudo-Element, das dort nicht steht, wird
nicht beurteilt.

**Was ausserdem OFFEN bleibt.** Trägt ein verblasstes Element **zusätzlich einen eigenen
Hintergrund**, wird
die ganze Gruppe als Einheit komponiert, und die Rechnung wäre eine Schätzung. Dieser Fall wird als
`UNDECIDED` gedruckt („a faded element that paints its own background — the group is composited as a
unit") statt still gerechnet. Ebenfalls offen: ein `content`, das nur ein Bild ist (`url(...)`),
wird übersprungen — dort gibt es keinen Text zum Messen.

**Was stattdessen begrenzt.** Die `UNDECIDED`-Zeile nennt die Stelle, und Schritt 2 der
SIGHT-Schleife verlangt ohnehin, dass der Designer jedes PNG ansieht.

**Urteil: beide gemessenen Blindstellen GESCHLOSSEN, die Gruppen-Komposition OFFEN und benannt.**

### H147 — Welche Datums-Schreibweisen ein Meilenstein annimmt, entscheidet der Interpreter (neu, TSK-0117 Nacharbeit 1, DEC-0064)

**Mechanismus.** `state.capture_preflight` prüft ein Datumsfeld mit
`backlog_types.normalised_date`, und das ist `datetime.date.fromisoformat`. Welche Formen diese
Funktion liest, hat sich über die Python-Versionen erweitert: `2026-10-01` liest jede, die kompakte
Form `20261001` erst 3.11+. Dieselbe Erfassung wird also auf einer Maschine angenommen und auf
einer anderen verweigert, ohne dass irgendetwas im Projekt sich geändert hätte.

**Gemessene Kette** (2026-09-03, Pilot außerhalb des Repos, Python 3.13 auf diesem Host):

| Eingabe | Urteil hier (3.13) | Urteil auf 3.10 |
|---|---|---|
| `2026-10-01` | angenommen, gespeichert als `2026-10-01` | angenommen |
| `20261001` | angenommen, gespeichert als `2026-10-01` | **verweigert** (`ValueError`) |
| `Oktober`, `2026-13-01`, `2026-10-01T00:00`, `''`, `None` | verweigert | verweigert |

**Was stattdessen begrenzt — und diese Absätze standen einmal zu absolut hier.** Was angenommen
wird, wird **normiert** gespeichert; beide schreibenden Verben lesen dafür DENSELBEN Leser
(`state._dates_in`, gerufen von `capture_preflight`/`capture` und von `_update_item_locked`), also
kann keines von beiden eine Schreibweise prüfen und eine andere ablegen. Solange ein Datum durch
eines dieser beiden Verben in den Speicher kommt, trägt ein Tag dort eine Schreibweise, und jeder
Leser, der nach `due` sortiert, bekommt dieselbe Reihenfolge.

Die frühere Fassung sagte das ohne diese Bedingung — „genau eine Schreibweise", „allein die Frage,
ob eine Eingabe durchkommt", „der gespeicherte Datensatz bleibt lesbar" — und war damit gegen die
Messung falsch: `update` las das Feld damals gar nicht, also war `update MST-0001
{"due": "Weihnachten"}` rc 0 und gespeichert, `{"due": "20261225"}` legte eine zweite Schreibweise
desselben Tages ab, und `{"due": null}` schrieb genau das `None` zurück, das die Erfassung eben
verweigert hatte (gemessen als Prozess, `vrig2/w5b_update.py` des Prüfers). Das ist geschlossen und
mit `tools/test_state.py::test_the_update_path_reads_a_date_field_exactly_as_capture_does`
gehalten; der Satz steht hier mit seiner Bedingung, damit er nicht wieder mehr behauptet, als
gemessen ist.

**Was das NICHT begrenzt.** Ein Projekt, das auf 3.13 einen Meilenstein mit `20261001` erfasst,
und ein Prüfer auf 3.10, der dieselbe Zeile nachfährt: der zweite bekommt eine Verweigerung für
einen Datensatz, den der Speicher bereits trägt. Und ebenso wenig begrenzt ist ein Schreiber
AUSSERHALB dieser beiden Verben — ein von Hand editiertes Item, ein Import — denn dieser Leser
sitzt an den Verben und nicht am Datensatz.

**Urteil: OFFEN, gemessen, nicht in dieser Runde schließbar.** Der Fix wäre eine eigene
Datumsgrammatik im Kernel statt der Standardbibliothek — also genau die Regel, die
`backlog_types.DATE_FIELDS` bewusst NICHT schreibt („was als Datum gilt, ist die Antwort der
Standardbibliothek, kein Muster, das dieser Kernel pflegt"). Wer sie will, kauft eine Grammatik,
die niemand sonst pflegt, gegen eine Streuung, die nur das Erfassen trifft.

### H148 — Eine Naht kann noch immer breiter sein als das, was zwei Aufträge wirklich teilen (neu, TSK-0117 Nacharbeit 1, DEC-0062)

**Mechanismus.** `kernel.scopes` subtrahiert die deklarierte Naht, bevor es ein Paar beurteilt, und
verweigert seit der Nacharbeit eine Deklaration, die einem der beiden Aufträge **keine** eigene
Ownership übrig lässt (`owns_anything_outside`). Das fängt den Totalfall (`**`, oder eine Liste
aller Einträge). Es fängt NICHT die Zwischenstufe: eine Naht, die mehr abdeckt als das, was die
beiden wirklich gemeinsam haben, solange jedem noch irgendein Pfad bleibt.

**Gemessene Kette** (2026-09-03, `check-scopes` als Prozess auf einem Piloten außerhalb des Repos):

| Naht auf beiden Aufträgen | Urteil |
|---|---|
| `**` | rc 2, „NOT A SEAM: … leaves TSK-0001 owning nothing of its own" |
| `docs/**` bei zwei Aufträgen, die nur `docs/**` besitzen | rc 2 (derselbe Satz) |
| `team-kits/**` bei Aufträgen, die `team-kits/kernel/**` bzw. `team-kits/dev-team/hooks/**` besitzen und daneben noch `tools/**` bzw. `docs/**` | **rc 0** — die Naht deckt die ganze Kollision zu, obwohl geteilt nur ein Teil davon ist |

**Was stattdessen begrenzt.** Die Naht steht in beiden Aufträgen (`seam_scope` wird nur
subtrahiert, wenn **beide** sie deklarieren), sie ist eingefroren wie der übrige Arbeitsauftrag
(`TSK_PLAN_FIELDS`), sie wird in der Ausgabe **jede Zeile einzeln** gedruckt — also sieht der
Leser, was die Deklaration wirklich zudeckt — und die Merge-Runde wendet sie nachweislich an. Eine
zu breite Naht ist damit sichtbar, nicht still.

**Was das NICHT begrenzt.** Dass sie zu breit IST. Der Kernel kann „so breit wie nötig" nicht
messen: er weiß nicht, welche Dateien die Ströme im Merge wirklich anfassen werden, nur welche sie
anfassen dürften.

**Urteil: OFFEN, gemessen, bewusst nicht geschlossen.** Die naheliegende Regel — „eine Naht darf
nicht mehr abdecken als die tatsächliche Schnittmenge" — wäre in dieser Runde baubar und ist NICHT
gebaut, weil sie die legitime Form der Naht verbietet: die echte Generation-3-Naht ist
`team-kits/*/VERSION`, ein Glob über alle Kits, während die tatsächliche Schnittmenge zweier
Ströme oft nur eine einzelne `VERSION` ist. Wer die Regel enger zieht, muss vorher messen, welche
der heute deklarierten Nähte sie verbieten würde.

**Die zweite Restklasse: zwei Schreibweisen DESSELBEN Verzeichnisses sind der Naht zwei Nähte.**
Seit Nacharbeit 2 faltet `scope_entries` Groß-/Kleinschreibung, also ist `Docs/**` gegen `docs/**`
eine Naht. Die Form-Differenz bleibt: `pair_seam` schneidet Zeichenketten, während `_matches`
Dateimengen vergleicht — und `docs/` und `docs/**` sind demselben Prädikat dieselbe Menge.
Gemessen (`_round-scratch/TSK-0117/n4_seamspell.py`, `check-scopes` als Prozess):

| Naht der beiden Aufträge | Prädikat über `docs/x.md` | Urteil |
|---|---|---|
| beide `docs/**` | — | rc 0, `disjoint` |
| `docs/` (normalisiert zu `docs`) vs `docs/**` | beide **True** | **rc 2**, gewöhnliche OVERLAP-Meldung |

**Kein Loch, sondern eine schlechtere Auskunft.** Die Richtung ist fail-closed: die Naht zählt
nicht, das Paar bleibt eine Kollision, niemand bekommt eine Erlaubnis, die er nicht deklariert hat.
Was fehlt, ist der Satz — der Leser hört „ihr überlappt" und sucht nach einer Datei, die er aus
einem Scope nehmen soll, während in Wahrheit dieselbe Naht zweimal verschieden geschrieben steht.
Der Fix wäre, die Naht als MENGE statt als Zeichenkette zu schneiden (jede Seite gegen die Einträge
der anderen mit `_matches` prüfen); er ist hier nicht gebaut, weil er dieselbe Abwägung trifft wie
der Absatz darüber — `team-kits/*/VERSION` deckt `team-kits/dev-team/VERSION` mengenmäßig ab, und
ob das eine gemeinsame Naht oder eine einseitig breitere ist, entscheidet keine Mengenrelation.

### H150 — Ein Verzeichniswechsel, den niemand ausrechnen kann, ließ die Fege-Basis stehen (neu, Merge-Prüfung TSK-0120, N1)

**Mechanismus.** Die Reichweite einer Zerstörung wird gegen das Verzeichnis gemessen, in dem die
Zeile wirklich läuft. `moves_the_working_directory` fragt dafür `_filing.directory_change`, und die
antwortet auf `popd`, ein bares `cd` oder `cd $DIR` mit „nicht berechenbar" — es gibt kein Ziel,
dem man folgen könnte. Bis zur Nacharbeit dieser Runde hieß das für den Aufrufer: die Position
bleibt, wo sie war. Das ist genau so lange richtig, wie die Position, die stehen bleibt, die
gefährlichere ist. Bringt der unberechenbare Wechsel die Shell ZURÜCK zu einem Fach von Rang, ist
die stehen gebliebene die harmlose — und die Zerstörung wird gegen sie gemessen.

**Gemessene Kette** (Merge-Prüfer TSK-0120, jeder auf `Bash` registrierte Office-Haken als Prozess,
über einem Piloten mit echtem Beleg unter `archive/`; nachgemessen vom Umsetzer mit
`_round-scratch/TSK-0120/verify_tools/b1_repro.py` und `n1_probe.py`):

| Befehlszeile | an `e45c0ca` | nach der Naht S9 | nach dieser Nacharbeit |
|---|---|---|---|
| `pushd outbox > /dev/null ; popd ; rm -rf .` | **rc 0** | **rc 0** | **rc 2** |
| KONTROLLE `rm -rf .` | rc 2 | rc 2 | rc 2 |
| KONTROLLE `cd outbox ; rm -rf .` | rc 0 | rc 0 | rc 0 |
| KONTROLLE `cd archive && rm -rf .` | rc 2 | rc 2 | rc 2 |

Es ist **Altbestand** und keine Unter-Verweigerung dieser Generation: an `e45c0ca` antwortet die
Zeile ebenso rc 0. Der Befund der Merge-Prüfung ist, dass der Kopf des Wächters
(`moves_the_working_directory`, „UNCOMPUTABLE STAYS UNMOVED") den NUTZEN dieser Regel nannte und
ihre Kosten nicht.

**Wie es geschlossen ist.** Mit derselben Mechanik, die `H144` schließt, und darum ohne eigenen
Mechanismus: eine unberechenbare Änderung macht die Position UNBEKANNT, und von einer unbekannten
Position aus kann die Shell überall stehen, wohin diese Zeile sie gebracht haben könnte. Die eine
Position, für die das immer gilt, ist die Projektwurzel — und die enthält jedes Fach. Sie tritt
darum als Kandidat neben die alte, und die Zerstörung wird verweigert, sobald irgendein Kandidat
ein Fach von Rang enthält.

**Was das kostet, benannt:** drei weitere Über-Verweigerungen — `cd outbox ; cd $X ; rm -rf .`,
`cd outbox ; cd ; rm -rf .` und `pushd outbox ; pushd sub ; popd ; rm -rf .` sind rc 2, obwohl
diese Shell wirklich in `outbox` steht. Die dritte ist von der Wiederholungsprüfung nachgereicht
(M5) und mit einer echten bash als Schiedsrichter bestätigt: nach `pushd outbox ; pushd sub ; popd`
steht sie in `outbox`, der Wächter verweigert. Alle drei sind gemessen, und die 18 legitimen
Kontrollen sind unverändert.

Dazu kommt der fünfte Preis, der PowerShell gehört: eine PowerShell-Pipeline ist keine Subshell,
`changes_the_calling_shell` liest ein einzeichiges `|` aber als eine — die vollständige Kette und
die Messung stehen in `H144`. Und was KEIN Preis ist, steht ebenfalls dort: ein absoluter `cd` wird
vollständig gefolgt, in einem leerzeichenfreien Piloten gemessen.

**Beide Enden:**
`tools/test_hooks.py::test_a_change_the_shell_may_not_have_made_leaves_both_positions_open` —
die `pushd`/`popd`-Form ist dort eine der vier gemessenen Zeilen, und die Rücknahme genau dieser
Hälfte (die Wurzel tritt nicht mehr hinzu) macht ihn rot, in einer Kopie außerhalb des Repos
gemessen.

**Urteil: GESCHLOSSEN, mit benannter Über-Verweigerung.**

