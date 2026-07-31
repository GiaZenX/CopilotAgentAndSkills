# Backlog- und Board-Informationsarchitektur — Recherche & Urteil

Gelesen: `docs/HARNESS_V2_SPEC.md` II.2/II.7/II.11, `docs/POST_V2_WISHLIST.md`, `team-kits/kernel/backlog_types.py`, `team-kits/kernel/state.py`, `team-kits/dev-team/constitution/AGENTS.md` §1/§2/§6, `team-kits/dev-team/templates/repo/scripts/generate_dashboard.py`, `team-kits/*/skills/*/SKILL.md` (Übersicht).

**Eine Vorab-Korrektur an der eigenen Wunschliste**, die den ganzen Rest verschiebt: der Satz „ein neuer Typ zöge einen Statusautomaten … nach sich" stimmt in diesem Code nicht. `state.py:445` definiert `_AUTOMATON_TYPES` als echte Teilmenge von `ACTIVE_DIRS`; `DEC` und `INV` sind typisierte Items mit Verzeichnis, Feldvertrag und Validierung, aber **ohne Automat** (`_NON_AUTOMATON_INITIAL_STATUS = {"DEC": "VALID", "INV": "unverified"}`), `ARC`/`WFR`/`DSN`/`APR`/`EVD` ebenso. Der Präzedenzfall für „Typ ohne Lebenszyklus" existiert also bereits. Das Kostenargument gegen einen neuen Typ muss deshalb neu geführt werden — es ist immer noch gültig, aber aus anderen Gründen (siehe 2.).

---

## 1. Wie Jira und Azure DevOps das Gliederungsproblem lösen

### Jira: zwei orthogonale Mechanismen, und der stärkere ist kostenpflichtig

**Typ-Hierarchie.** Jira hat exakt drei feste Ebenen: „By default, Jira is set up with three levels of work type hierarchy: a level for larger pieces of work (level 1, by default called **Epic**), a level for standard work items (level 0, called **Story**), and a level for smaller pieces of work (level -1, called **Subtask**)." Alles oberhalb von Epic — also genau die Ebene, die der User will — ist Premium/Enterprise, muss vom Admin konfiguriert werden, und die Doku warnt: „**once these changes are made, they cannot be undone**" (https://support.atlassian.com/jira-cloud-administration/docs/configure-the-issue-type-hierarchy/, https://support.atlassian.com/jira-software-cloud/docs/configure-custom-hierarchy-levels-in-advanced-roadmaps/). Dass Atlassian eine reine Gliederungsebene hinter eine Bezahlschranke und hinter eine irreversible Admin-Operation stellt, ist selbst ein Befund: sie ist teuer, nicht billig.

**Komponenten.** „Jira components help you group work items in your space around product features, departments, or workstreams" — „Jira components are only available in company-managed spaces, and are scoped to the space they're created in" (https://support.atlassian.com/jira-software-cloud/docs/what-are-jira-components/). Das ist ein **Feld mit kontrolliertem Vokabular**: nur Admins legen Werte an, alle anderen wählen aus. Verschachtelung kennt die Doku nicht — Atlassian bewirbt „Subkomponenten" in einem Blogpost (https://www.atlassian.com/blog/jira/organize-jira-issues-subcomponents), d. h. per Namenskonvention, nicht als Datenmodell.

**Labels.** Freitext, global über alle Projekte. Die Community-Diagnose dazu ist der eigentlich lehrreiche Teil: „they are case sensitive and do not allow spaces, so if you search on the Label field the values of Cat, cats, cat, catt, Cats, catz, etc. would all be different values, and some issues would not show up depending on the typos or case used" (https://community.atlassian.com/forums/Jira-questions/What-is-the-difference-between-labels-and-components-and-how/qaq-p/1122277). Das ist keine Anekdote, das ist das Standardversagen unkontrollierter Vokabulare.

### Azure DevOps: drei orthogonale Mechanismen, sauber getrennt

Der Kernsatz: „**Area paths group work items by team, product, or feature area. Iteration paths group work into sprints, milestones, or other time-related periods. Both fields support hierarchical paths.**" (https://learn.microsoft.com/en-us/azure/devops/organizations/settings/about-areas-iterations?view=azure-devops)

- **Area Path** = Datentyp `TreePath`, Knoten mit `\` getrennt, „Path hierarchy depth: Must be fewer than 14 levels deep", bis 10.000 pro Projekt, ein Wert pro Work Item. Genau die Gliederung, die der User meint. Explizite Warnung der Doku: „**Avoid creating an overly complex area structure.**" Und: „Deleting **Area Path** values or reconfiguring **Iteration Path** values causes **irreversible data loss**" in allen historischen Charts; löschen geht nur, „when they're no longer used by any work items".
- **Iteration Path** = derselbe Datentyp, aber für Zeit. Entscheidender Satz für Punkt 3: „**Iterations don't enforce any rules.** For example, you can assign a task to an iteration without closing or completing it during that iteration."
- **Portfolio-Backlogs** = Epic → Feature → Backlog Item, eine *Typ*-Hierarchie mit Rollup (https://learn.microsoft.com/en-us/azure/devops/boards/backlogs/backlogs-overview?view=azure-devops). Dort steht auch die Regel, die der Harness übernehmen sollte: „**Keep each work item type in a flat list, and link parents and children only across different types** — for example, epic to feature, feature to story, story to task. Avoid same-type hierarchies like story-to-story, bug-to-bug, or task-to-task." Und: Rollup ist abgeleitet („Progress bar: Percentage of descendant items closed or completed").

Der Zweck der Portfolio-Ebene ist in derselben Doku explizit **Mehr-Team-Koordination**: „Long-running initiatives that span teams or are too large for a single team backlog", „A typical structure pairs two management teams with three development teams."

### Was in einem kleinen Team seinen Unterhalt verdient

| Mechanismus | Urteil für diesen Harness |
|---|---|
| **Pfad-FELD (Area Path)** | **Verdient es.** Es ist exakt „Frontend → Buttons", kostet einen Feldwert, hat keinen Lebenszyklus, keine Freigabe, kein Archiv. |
| **Kontrolliertes Vokabular für dieses Feld** | **Verdient es.** Ohne das bekommt man in vier Wochen `frontend`, `Frontend`, `FE`, `ui/buttons`. |
| **Typ-Ebene über dem Requirement (Epic/Initiative)** | **Verdient es nicht.** Ihr Zweck ist Rollup über *mehrere Teams mit getrennten Backlogs*. Hier gibt es ein Team und einen Backlog. Jira selbst behandelt sie als irreversiblen Admin-Eingriff. |
| **Labels/Tags (frei)** | **Verdient es nicht.** Der Harness hat mit `TASK_TYPES`/`EVIDENCE_KINDS` bereits die Gegenposition eingenommen und in `state.py:479` begründet: ein Freitextwert *überspringt* eine Prüfung, statt sie zu verletzen. |
| **Iteration Path / Sprints** | **Verdient es nicht.** Kein Takt, keine Kapazität, kein Velocity-Begriff im Modell. |
| **Stack Rank / Drag-Reihenfolge** | **Verdient es nicht** — Begründung in Punkt 4. |

---

## 2. Feld oder Item-Typ? — beide Seiten, gegen die Kosten von V2 gerechnet

### Was für das FELD spricht

1. **Es ist der anerkannte Bauplan.** ADO modelliert die Gliederung als `TreePath`-Feld, nicht als Item. Jira modelliert sie als Komponentenfeld. Die Typ-Hierarchie ist bei beiden ein *anderes* Werkzeug für ein *anderes* Problem (Rollup über Teams).
2. **Die Kosten in V2 sind wirklich klein und alle Anschlusspunkte existieren:**
   - `backlog_types.REQUIRED_FIELDS` — **nicht** anfassen; `area` ist optional.
   - `state.py:479 _CLOSED_VOCABULARY` — ein Eintrag pro tragendem Typ. Der Mechanismus prüft bereits **Capture *und* Edit** und begründet im Docstring genau warum („a value refused at capture and then written by an edit is not refused at all").
   - `state.py:413 _regenerate_index_locked` — `area` in die Indexzeile.
   - `generate_dashboard.py` — Group-by in der Ansicht.
   - Kein Automat, kein `approval_ref`, kein Archivpfad, keine ID-Sequenz.
3. **Eine harte Nebenentscheidung, die getroffen und protokolliert werden muss:** `area` gehört **nicht** in `HASHED_FIELDS` (`backlog_types.py:322`). Sonst entwertet jedes Umsortieren die Scope-Freigabe und setzt das PR auf `DRAFT` zurück. Eine Gliederung ist keine Zusage an den Kunden. Dasselbe Argument in ADO-Sprache: dort ist das Löschen eines Area Paths deshalb so teuer, weil er zum Join-Key der Historie gemacht wurde — diesen Fehler nicht wiederholen.

### Was für den TYP spricht (und warum es am Ende nicht reicht)

Ehrlich, in absteigender Stärke:

- **Ein Feld kann nichts tragen.** Sobald „Frontend" einen Owner, eine Beschreibung, eigene Invarianten oder eine Design-System-Referenz haben soll, ist das Feld am Ende. Ein Item könnte das.
- **Referenzintegrität bekommt man beim Typ geschenkt.** `_assert_origins_resolve` prüft heute schon, ob `TSK.derives_from` und `EVD.related` auflösen. Ein `AREA`-Item wäre automatisch in dieser Maschinerie; ein Feld braucht eine eigene Prüfung gegen eine Registry.
- **Der Automat ist nicht das Problem** (siehe Vorbemerkung — `DEC`/`INV` beweisen es).

Die realen Kosten des Typs sind andere und sie sind höher:

1. **Ein Typ lädt einen Status ein.** Es gibt `AREA-0003`, also will jemand sie schließen. Dann verbirgt eine geschlossene Area Items, deren eigener Status aktiv sagt — zwei Quellen für dieselbe Aussage „lebt das noch". V2s ganze Ordnung lautet: Lebendigkeit = in welchem Verzeichnis die Datei liegt.
2. **ADOs eigene Regel spricht dagegen:** „Keep each work item type in a flat list, and link parents and children only across different types." Eine mehrstufige Area („Frontend/Buttons") wäre als Typ eine `AREA→AREA`-Selbstverschachtelung — genau das Muster, vor dem die Doku warnt und bei dem in ADO nur noch die Blattknoten auf Boards erscheinen.
3. **Löschen wird zum Problem.** ADO: Pfade dürfen nur gelöscht werden, „when they're no longer used by any work items". Mit einem Typ muss man das bauen, inklusive Verwaisungs-Handling im Archiv. Mit einem Feld + Registry ist Umbenennen eine Kernel-Operation, die N Items mitzieht — ein Schreibvorgang, keine Objektlebensdauer.

### Empfehlung

**Feld `area` (Pfad-String), plus eine Registry — und die Registry ist der Teil, den die Wunschliste vergisst.** Ohne Registry ist `area` ein Jira-Label und man hat die fünf Schreibweisen von „Frontend".

**Ein konkreter Defekt, den ich dabei gefunden habe:** Die naheliegende Heimat der Registry, `project_memory/project_config.yaml`, ist nach der Installation **von niemandem mehr beschreibbar**. `gate_write_scope` verweigert jeden Tool-Write in `project_memory/**`, und der Kommentar im Hook (Zeile 37 ff.) sagt es selbst: „The entry gate writes the masterplan, the first root item and `project_config.yaml` by hand … It needs no exemption because it runs BEFORE" der Installation. Eine Taxonomie, die man nach dem Bootstrap nicht mehr erweitern kann, ist eine, um die herum die Leute arbeiten. Also braucht die Registry einen **Kernel-Schreibpfad** (`harness area add|rename|remove`, Ziel z. B. `product/areas.yaml`) — das ist die einzige nennenswerte Implementierungsarbeit an diesem Punkt.

### GATE oder SKILL

| Regel | Einstufung | Begründung |
|---|---|---|
| `area` muss ein Wert aus der Registry sein | **GATE** | Mengenzugehörigkeit. Bestehender Mechanismus `_CLOSED_VOCABULARY`, Capture- *und* Edit-Pfad. |
| Pfadsyntax + Tiefenlimit (Vorschlag: max. 3) | **GATE** | Prüfung mechanisch. Die *Zahl* ist ein Urteil (ADO: „<14", plus „avoid an overly complex area structure") — sie gehört in die Config, die Prüfung in den Kernel. |
| Umbenennen zieht alle referenzierenden Items mit, oder wird verweigert, solange Items darauf zeigen | **GATE** | ADOs Regel, mechanisch prüfbar. |
| `area` nicht in `HASHED_FIELDS` | **GATE** (als Testfall) | „Ändere `area` an einem APPROVED PR → Freigabe bleibt" ist ein Test, der scheitern kann. |
| **Welche** Areas es gibt, und dass sie die Produktstruktur beschreiben, nicht die Zuständigkeit | **SKILL** (PM) | Urteil. Wichtig: eine Area namens „Backend" dupliziert `TSK.assigned_role` — ADO vermischt Area und Team, weil ADO Teams hat; hier gibt es Rollen, und das Feld existiert bereits. |
| Produktebene in Kundensprache | **SKILL** (PM) | Nicht prüfbar. Ein Gate, das nach Fachjargon grept, wäre Theater. |

---

## 3. Meilensteine: das Mindeste — und wie es nicht zum zweiten `progress.yaml` wird

### Das veröffentlichte Minimum

GitHub Milestones sind das kleinste ernstzunehmende Modell: Titel, Beschreibung, Fälligkeitsdatum — und der Fortschritt ist **abgeleitet**, nicht gespeichert: „The milestone's completion percentage", „The number of open and closed issues and pull requests associated with the milestone" (https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones). Der Roadmap-Layout positioniert Items aus Datums-/Iterationsfeldern und zeigt Meilensteine als **vertikale Marker**, nicht als Container (https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout).

Und die Regel, die dieser Harness wörtlich zitieren sollte, steht in GitHubs Best Practices: „**To prevent information from getting out of sync, maintain a single source of truth. For example, track a target ship date in a single location instead of spread across multiple fields.**" (https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects)

### Konkreter Vorschlag für V2

`MST` als typisiertes Item **ohne Automat** (Muster `DEC`), `ACTIVE_DIRS["MST"] = "milestones/active"`:

```
REQUIRED_FIELDS["MST"] = ("title", "target_date", "goal")
```

- `target_date`: ISO-8601 `YYYY-MM-DD`, sonst Refusal. (Ohne diesen Gate landen „Q3" und „Ende Sommer" im Feld und die Timeline lässt sie stumm weg.)
- `goal`: ein Satz Prosa in Kundensprache. Das ist die „Zielbezug"-Hälfte des Wunsches — und der Scrum Guide hat dafür bereits den Begriff: das Product Goal ist ein Zustand, kein Datum (https://scrumguides.org/scrum-guide.html).
- **Kein `status`, kein `progress`, keine `items`-Liste.**

**Die wichtigste Einzelentscheidung ist die Richtung der Kante.** Der MST darf **nicht** seine Items auflisten. Die Mitgliedschaft ist ein Feld `milestone: MST-0001` **am Wurzel-Item** (PR/RQ/BUG/CR) — nicht an SR/TSK, die erben über ihre Wurzel, genau wie `root_revision` heute denormalisiert wird. Gründe:

- Jira, ADO und GitHub machen es alle so (Feld am Work Item, nicht Liste am Container).
- Eine Liste im MST kann ein Item nennen, das archiviert oder nie existiert hat — das ist per Definition eine zweite Behauptung darüber, was zum Release gehört.
- Nur mit der Kante am Item ist der Meilenstein **vollständig aus `generated/` berechenbar**. Mit der Liste bräuchte man einen Join, den zwei Seiten pflegen.

### Die drei Regeln, die verhindern, dass es `progress.yaml` wird — alle mechanisch prüfbar, also GATES

1. **`MST` darf keine Statusaussage über andere Items tragen.** Ein Feldvertrag mit *verbotenen* Schlüsseln (`progress`, `percent`, `items`, `done`, `status`). Der Kernel refusiert heute schon unbekannte und kernel-eigene Felder beim Capture — das ist dieselbe Stelle.
2. **`milestone:` darf nur einen existierenden, nicht archivierten MST nennen.** Wiederverwendung von `_assert_origins_resolve`.
3. **Nur Wurzeltypen dürfen `milestone:` tragen.** Ein TSK mit eigenem Datum würde einer Aufgabe einen Termin geben, den ihr PR nicht hat.

Dazu, als vierter Gate-Testfall: `target_date` **nicht** in `HASHED_FIELDS`. Ein Termin zu verschieben darf keine Scope-Freigabe entwerten — sonst wird das Verschieben eines Datums teurer als das Ändern eines Akzeptanzkriteriums, und niemand pflegt es mehr.

**Offener Punkt, den ich nicht wegargumentiere:** ohne Status bewegt nichts den MST ins Archiv. Zwei ehrliche Optionen — (a) ein expliziter Kernel-Befehl `harness milestone close` verschiebt die Datei (kein Status, aber ein bewusster Akt), oder (b) das `DEC`-Muster mit zwei Werten `PLANNED|CLOSED` ohne Kette. Ich empfehle (a), weil (b) die Tür zu „und dann brauchen wir noch AT_RISK" öffnet. Das ist eine Entscheidung, keine Ableitung.

### Und was „Fortschritt" auf der Timeline eigentlich sein sollte

Ein Datum ist kein Fortschritt. Der veröffentlichte Standard dafür ist der **Kanban Guide** (Prokanban.org/Scrum.org), der vier Flow-Metriken verpflichtend macht (https://kanbanguides.org/english/):

- **WIP** — „The number of work items started but not finished"
- **Throughput** — „The number of work items finished per unit of time"
- **Work Item Age** — „The elapsed time between when a work item started and the current date"
- **Cycle Time** — „The elapsed time between when a work item started and when a work item finished"

Der Punkt für diesen Harness: **drei davon sind heute schon berechenbar, ohne ein einziges neues Zustandsfeld.** Der Kernel stempelt bereits `created` auf jedes Item (`state.py:293`) und `leased_at`/`started`/`completed` auf TSK (`dispatch.py:130/488/533`). WIP, Cycle Time und Work Item Age fallen daraus ab. Throughput braucht ein Abschlussdatum auch für nicht-TSK-Items — das steht heute nur in Git (Commit-Zeitpunkt der Archivierung), was ausreicht und ausdrücklich der V2-Linie entspricht („Historie liegt in Git").

Work Item Age ist dabei die Metrik, die „wo stehen wir" wirklich beantwortet: sie zeigt das Item, das seit 19 Tagen `IN_PROGRESS` ist. Ein Prozentbalken tut das nie.

**GATE/SKILL:** Die Metriken sind ein Renderer — **kein Gate**. Die *Service Level Expectation* aus dem Kanban Guide („a forecast of how long it should take a work item to flow from started to finished") würde ich als **SKILL** kennzeichnen und ehrlich als dünn adoptiert markieren: in einem Ein-Personen-Projekt mit Agenten-Durchsatz ist die Stichprobe zu klein für eine Perzentil-Aussage.

---

## 4. Board/Backlog-Rendering: was nach `generated/`, was echter Zustand

**Die Trennlinie:** Zustand ist, was ein Mensch entschieden hat und was nicht neu berechnet werden kann. Alles andere ist Projektion.

| Echter Zustand (typisierte Item-Dateien, Kernel schreibt) | `generated/` (regenerierbar, nie committet) |
|---|---|
| `area` am Item; die Area-Registry | Der Gliederungsbaum, die Spalten, jede Zählung, jeder Prozentwert |
| `milestone` am Wurzel-Item; das `MST`-Item (Titel, Datum, Ziel) | Meilenstein-Fortschritt, Rollups pro Area/Meilenstein |
| `priority` (existiert bereits als Pflichtfeld an PR/RQ) | Sortierung innerhalb einer Spalte, Flow-Metriken, „zuletzt fertig" |
| Die Kernel-Zeitstempel | Aufgeklappt/zugeklappt, Filterzustand, Seitenzahl |

**Drei Grenzfälle, mit Urteil:**

1. **Spaltendefinition = Code, nicht Konfiguration.** Die Spalten sind `AUTOMATA[type]`. `generate_dashboard.py` leitet heute schon korrekt ab („WHICH statuses count as finished is deliberately not written here — that is `AUTOMATA[type].terminals`, so a chain change moves the board with it"). Das darf nicht rückgängig gemacht werden. Der Kanban Guide verlangt genau *eine* Definition of Workflow mit „one or more defined states that the work items flow through" — eine projektspezifische Spaltendatei wäre eine zweite.

2. **Kartenreihenfolge innerhalb einer Spalte: verlockender Zustand, darf keiner werden.** ADO speichert dafür ein verstecktes `Stack Rank`/`Backlog Priority` und warnt: „Don't use bulk modify to change *Backlog Priority* or *Stack Rank*. Bulk modify assigns the same value to every selected item, **which wipes out the relative ordering**." In einem Store mit einer Datei pro Item ist es schlimmer: eine Karte umsortieren schreibt N Dateien, und zwei Branches, die beide sortieren, produzieren N Konflikte. **Deterministisch sortieren nach `(priority, created, id)`.** Der Preis ist ehrlich zu nennen: **kein Drag-and-Drop-Reordering.** Das ist der richtige Preis.

3. **Karte zeigt nur den Titel, klappt für die Beschreibung auf** — das ist Progressive Disclosure im Sinne von Nielsen: „Initially, show users only a few of the most important options. Offer a larger set of specialized options upon request" (https://www.nngroup.com/articles/progressive-disclosure/). Es ist zugleich exakt das, was II.7 technisch ohnehin fordert („Details lazy, kein Archiv/Volltext im initialen DOM") und was Jira mit „up to three additional fields" pro Karte hart begrenzt (https://support.atlassian.com/jira-software-cloud/docs/customize-cards/). Empfehlung als **GATE**, weil messbar: Der Generator darf pro Karte höchstens Titel + drei abgeleitete Felder in das initiale DOM schreiben; Volltext kommt erst beim Aufklappen aus dem eingebetteten JSON. Das ist eine Zeilen-/Feldzahl, also prüfbar — im Gegensatz zu „die Karte soll übersichtlich sein" (**SKILL**).

### Die Ausfallmodi, wenn man die Grenze falsch zieht

**(a) Der Klassiker — und dieses Repo hat ihn erlebt.** `progress.yaml` und das committete `dashboard_history/` waren Renderings, die Autorität erwarben. Der Mechanismus ist verallgemeinerbar: **jede Datei, die (1) committet ist, (2) menschenlesbar ist und (3) eine anderswo ableitbare Tatsache wiederholt, wird zu der Datei, die gelesen wird** — und wenn ein Schreibvorgang scheitert, überlebt die abgeleitete. Deshalb ist „nicht committet" in II.2 keine Aufräumregel, sondern der Schutzmechanismus.

**(b) Der spezifische Ausfallmodus eines *Boards*, und der gefährlichste hier: das Board schreibt.** Ein Kanban-Board ohne Drag-and-Drop-Statuswechsel fühlt sich kaputt an, also wird jemand es bauen. In dem Moment ist der Renderer ein Übergangspfad, der `assert_transition` umgeht — und der Automat, dessen ganze Existenzberechtigung ist, dass Übergänge nur durch den Kernel gehen (`backlog_types.py:5`), ist wirkungslos. II.7 sagt „Dashboard schreibt keinen Status" bereits; das Board ist die eine Funktion, bei der dieser Satz auf die Probe gestellt wird. Zulässige Auflösung: die Karte bietet einen Button, der `harness transition …` *als Kommando anzeigt oder ausführt* und die Refusal des Kernels sichtbar macht — nie eine Datei anfasst.

**(c) Der subtile: die Registry aus den Items ableiten.** Wenn „alle vorkommenden `area`-Werte" die Gliederung bilden, geht zweierlei verloren — die **Reihenfolge** der Gliederung und die **leere Area**. „Frontend/Buttons ist geplant, aber noch leer" ist dann nicht darstellbar, und der Knoten verschwindet vom Board, sobald sein letztes Item archiviert wird. Genau deshalb ist die Registry Zustand und der Baum Projektion.

### Eine konkrete kleine Änderung, die sonst teuer wird

`generated/index.yaml` trägt heute nur `id, type, title, status, revision, approval_ref, blocked_by` (`state.py:429-439`). Board und Timeline brauchen `area`, `milestone`, `priority` und die TSK-Zeitstempel **in der Indexzeile**. Sonst muss der Renderer jede Item-Datei parsen, und die Optimierung, die `generate_dashboard.py` ausdrücklich verteidigt („a 10,000-item project must not cost 10,000 YAML parses to show 50 rows"), ist hin. Die Änderung ist ein Dutzend Zeilen in `_regenerate_index_locked`.

Nebenbei: `generate_dashboard.VIEWS` routet jeden Typ; ein nicht zugewiesener Typ landet mit Warnung unter „Other". Ein neuer `MST`-Typ muss dort also bewusst einsortiert werden — der Mechanismus, der das erzwingt, existiert schon.

---

## 5. Prior Art: Boards direkt aus Dateien

**Backlog.md** (MIT, https://github.com/MrLesk/Backlog.md) — das nächstliegende Vorbild: eine Markdown-Datei pro Task mit YAML-Frontmatter unter `backlog/tasks/`, Terminal-Kanban (`backlog board`) plus Web-UI (`backlog browser`), Akzeptanzkriterien und „Definition of Done" als erstklassige Felder, Meilensteine und Abhängigkeiten, explizit für Agenten gebaut. **Kopierenswert:** Akzeptanzkriterien als strukturiertes, vom CLI prüfbares Feld; das CLI als einziger Schreiber; die Oberfläche liest nur. **Was es für diesen Harness falsch macht:** (1) die Web-UI *schreibt* beim Drag-and-Drop in die Markdown-Dateien zurück — genau die Grenze, die V2 nicht überschreiten darf; (2) ein `ordinal`-Feld für die Drag-Reihenfolge, also das Stack-Rank-in-Dateien-Problem aus Punkt 4; (3) erledigte Tasks bleiben im Ordner, und die Statuslage über Branches wird mit Heuristiken (`checkActiveBranches`, `activeBranchDays`, `remoteOperations`) rekonstruiert — V2s `archive/` plus ein Automat ist strikt besser und darf dafür nicht eingetauscht werden; (4) Statuswerte sind konfigurierbare Strings, es gibt also gar keinen Automaten. Adoption ist real, aber jung, und dasselbe README kursiert unter mehreren Forks (bradcstevens, cytrowski) — als Designreferenz nutzen, nicht als Abhängigkeit.

**todo.txt** (Spezifikation: https://github.com/todotxt/todo.txt, http://todotxt.org/) — die älteste veröffentlichte Dateiformat-Antwort auf genau die Gliederungsfrage: `+project` und `@context` als mehrwertige Tags, plus Priorität `(A)`–`(Z)`. **Richtig:** Gruppierung ist ein wiederholbares Tag, kein Typ; das Format *ist* die ganze Spezifikation. **Falsch für hier:** gar kein kontrolliertes Vokabular (dasselbe Versagen wie Jira-Labels), keine Verschachtelung, und `(A)`–`(Z)` ist eine Ordinalzahl im Kostüm einer Kategorie.

**git-bug** (https://github.com/git-bug/git-bug) — Issues als Git-Objekte, CLI/TUI/Web, offline-first, „no files are added in your project". **Das lehrreiche Gegenbeispiel:** es löst Merge-Konflikte, indem es den Arbeitsbaum ganz verlässt — um den Preis, dass der Zustand für jedes Werkzeug unsichtbar wird, das Dateien liest (grep, diff, Review, Hooks). V2 hat sich bewusst umgekehrt entschieden. Bezeichnend: ein Project Board ist dort seit Jahren „geplant" — ein Board über einem eigenen Store ist mehr Arbeit als ein Board über Dateien.

**Die Markdown-Kanban-Familie** (Obsidian Kanban und die VS-Code-Varianten): ein Board = *eine* Datei, Spalten als `## Überschrift`, Karten als Listeneinträge. **Der entscheidende Fehler für ein Multi-Agenten-Repo:** die Spaltenzugehörigkeit ist die Zeilenposition in einer einzigen Datei. Jeder Statuswechsel ist ein Diff auf dieselbe Datei, zwei parallele Agenten kollidieren bei jedem Zug. V2s Datei-pro-Item ist die Behebung — nicht dorthin zurückfallen, auch nicht für `generated/`.

**GitHub Projects** (nicht dateibasiert, aber die Regeln sind zitierfähig): Meilenstein als **Marker** auf der Timeline statt als Container, Position aus Datums-/Iterations-*Feldern*, „maintain a single source of truth", und „Projects automatically stay up to date with GitHub data … The less you need to remember to do manually, the more likely your project will stay up to date." Das ist genau die Begründung dafür, Ansichten abzuleiten statt zu pflegen.

**Azure DevOps als Negativbeispiel zum Mitkopieren:** „Deleting Area Path values … causes irreversible data loss" in den historischen Charts. Lehre: den Gruppierungswert nie zum Join-Key der Historie machen. In V2 ist die Historie Git, also ist das schon vermieden — aber es begründet, warum ein Area-Rename eine Kernel-Operation sein muss, die Items mitzieht, und kein Registry-Edit, der sie verwaisen lässt.

---

## Zusammenfassung: die GATE/SKILL-Linie für dieses Thema

**GATES (mechanisch prüfbar → Hook/Test/Kernel-Refusal)**
1. `area` nur aus der deklarierten Registry (Capture *und* Edit, via `_CLOSED_VOCABULARY`).
2. `area`-Pfadsyntax und Tiefenlimit; Limit konfigurierbar, Prüfung im Kernel.
3. Area-Rename zieht referenzierende Items mit — oder wird verweigert, solange welche existieren.
4. `area` und `MST.target_date` **nicht** in `HASHED_FIELDS` (als Test formuliert: Änderung entwertet keine Freigabe).
5. `MST.target_date` ist ISO-8601 `YYYY-MM-DD`.
6. `MST` darf keine Felder `progress`/`percent`/`items`/`done`/`status` tragen (verbotene Schlüssel im Feldvertrag).
7. `milestone:` löst auf einen existierenden, nicht archivierten MST auf — und nur Wurzeltypen (PR/RQ/BUG/CR) dürfen es tragen.
8. Board/Timeline schreiben nichts: kein Statuswechsel außerhalb von `harness transition`.
9. Karte im initialen DOM: Titel + höchstens drei abgeleitete Felder; Volltext nur lazy.
10. Board, Gliederung, Timeline, alle Zählungen liegen ausschließlich unter `generated/` und sind nicht committet.

**SKILLS (Urteil → Anleitungstext, der nicht behaupten darf, erzwungen zu sein)**
- Welche Areas es gibt, wie tief man wirklich gliedert, und dass die Area die Produktstruktur beschreibt und nicht die Zuständigkeit (die steht in `TSK.assigned_role`).
- Dass die Produktebene in Kundensprache formuliert ist und die Systemebene die technische.
- Wann ein Meilenstein gerechtfertigt ist und was ein Ziel von einem Datum unterscheidet.
- Wie man Work Item Age liest (welches Item hängt), statt auf einen Prozentbalken zu schauen — und die Service Level Expectation aus dem Kanban Guide, ausdrücklich als „für kleine Stichproben schwach" markiert.

**Sources:**
- [Azure DevOps: How are area and iteration paths used?](https://learn.microsoft.com/en-us/azure/devops/organizations/settings/about-areas-iterations?view=azure-devops)
- [Azure DevOps: Use backlogs to manage projects](https://learn.microsoft.com/en-us/azure/devops/boards/backlogs/backlogs-overview?view=azure-devops)
- [Atlassian: Configure the work type hierarchy](https://support.atlassian.com/jira-cloud-administration/docs/configure-the-issue-type-hierarchy/)
- [Atlassian: Configure custom hierarchy levels in your plan](https://support.atlassian.com/jira-software-cloud/docs/configure-custom-hierarchy-levels-in-advanced-roadmaps/)
- [Atlassian: What are Jira components?](https://support.atlassian.com/jira-software-cloud/docs/what-are-jira-components/)
- [Atlassian: Customize cards](https://support.atlassian.com/jira-software-cloud/docs/customize-cards/)
- [Atlassian Community: labels vs components](https://community.atlassian.com/forums/Jira-questions/What-is-the-difference-between-labels-and-components-and-how/qaq-p/1122277)
- [GitHub Docs: Best practices for Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/best-practices-for-projects)
- [GitHub Docs: About milestones](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones)
- [GitHub Docs: Customizing the roadmap layout](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/customizing-the-roadmap-layout)
- [Kanban Guide (kanbanguides.org)](https://kanbanguides.org/english/)
- [NN/g: Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
- [NN/g: Taxonomy 101](https://www.nngroup.com/articles/taxonomy-101/)
- [Backlog.md](https://github.com/MrLesk/Backlog.md)
- [todo.txt format](https://github.com/todotxt/todo.txt)
- [git-bug](https://github.com/git-bug/git-bug)