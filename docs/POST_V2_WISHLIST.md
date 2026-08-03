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

### L5 — Der Workspace-Trust verwirft auch die `deny`-Hälfte

Gemessen in jeder headless Sitzung: `Ignoring 5 permissions.allow entries … this workspace has not
been trusted`. Verworfen wird der **ganze** `permissions`-Block, also auch `deny: Agent(project-manager)`
(kein zweiter PM), `Read(./.env*)`, `Read(**/*.key)`. Ein frisch gescaffoldetes Projekt läuft bis zum
ersten interaktiven Start ohne diese Sperren. Die Meldung nennt beide Wege hinaus, aber **nicht**,
was währenddessen fehlt. Die Neustart-Anweisung des Scaffolds erwähnt den Trust-Dialog gar nicht.

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
