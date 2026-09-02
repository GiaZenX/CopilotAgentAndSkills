# TSK-0103 — Rundenprotokoll (Stream D, research-team), Fassung 3

Auftrag aus TSK-0103 (`derives_from: FR-0029`, deckt zusätzlich FR-0042), Stream D des
DEC-0057-Parallel-Piloten. Worktree `C:\Offline Repos\v2-testbed\_worktrees\stream-research`,
Branch `stream/research` auf `c155a5f`. Scratch ausschließlich
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0103\`.

**Wanduhr (DEC-0057 g):** Start `2026-09-01T21:23:09+02:00`; Fassung 1 `22:49:50` (1 h 27 min);
Fassung 2 nach dem Prüfer-FAIL `2026-09-02T00:02:30` (+1 h 13 min); Fassung 3 (drei Prosa-Stellen)
`2026-09-02T00:23:04` (+20 min). **Gesamt 3 h 00 min**, Prüferzeit nicht enthalten; davon rund 70 min reine Suitenzeit — fünf
Läufe von `tools/test_hooks.py`, zwei davon durch den unten protokollierten Mid-Run-Edit
verworfen und einer durch die Ratschen. Keine Commits, keine volle `tools/`-Suite, keine globale
Installation.

**Zwei Prüferrunden.** Runde 1: sechs Blocker, davon zwei in Code, den ich in dieser Runde selbst
geschrieben hatte — Abschnitt 6. Runde 2: der Code war auf allen sechs richtig, es fehlten drei
Prosa-Stellen — Abschnitt 6a. Die Abschnitte davor beschreiben den Stand NACH beiden.

## 1. Was gebaut wurde

### 1.1 FR-0042 — Kettentest der Forschungskette (NEU: `tools/test_research_chain.py`)

Acht Szenarien auf einem **wirklich aufgesetzten** Forschungsprojekt: `init_project_memory.sh` +
`scaffold_team.sh` gegen ein Wegwerf-HOME unter dem Scratch (nie der globale Speicher). Getrieben
werden ausschließlich die installierten Flächen — `python scripts/harness.py …` als Einstiegspunkt,
die Haken hinter `.claude/hooks/_gate.py` mit rohem UTF-8 auf stdin, so wie `settings.json` sie
registriert.

* `test_the_research_chain_runs_from_the_question_to_a_merge_through_the_shipped_hooks`
  RQ (capture) → Scope-/Liefer-Freigabe → HYP → EXP → Liefer-Freigabe → TSK → dispatch → Spawn
  (+ Gegenrichtung rc 2 mit einer *installierten* Rolle) → PostToolUse bindet → `submit-result` →
  DONE → VALIDATED → Merge zu („no QA Evidence") → Evidenz je `QA_EVIDENCE_KINDS` → Merge auf.
* `test_a_task_on_an_experiment_cannot_name_the_question_the_experiment_hangs_from` — **H92** als
  laufende Messung, mit beiden Kernel-Lesern im selben Test.
* `test_every_experiment_needs_a_delivery_approval_whatever_its_size`
* `test_an_experiment_reaches_analyzed_unrefused_and_the_merge_is_where_the_report_is_demanded`
* `test_a_rendered_report_is_found_where_the_kit_actually_renders_it` — der Bericht heißt
  `EXP-0001-Größe-αβ.tex`, damit eine Datei drei Dinge misst: git escapt einen Nicht-ASCII-Pfad,
  das griechische Paar liegt außerhalb der Windows-Codepage, und beides zusammen ist der Weg rein
  und wieder raus.
* `test_the_stylesheet_of_a_rendered_html_report_is_not_read_as_a_result` — Stilblock **und** ein
  Start-Tag mit umgebrochenen Attributen.
* `test_prose_with_an_inequality_pair_is_not_read_as_markup` — die Gegenrichtung, je Fall mit
  eigener Kontrolle.
* `test_a_bom_in_front_of_a_heading_does_not_turn_it_into_a_claim`

**Kosten der Kette (Wanduhr):** rund **1 Minute** für die acht Szenarien — auf diesem Host 49,9 s,
auf dem Rig des Prüfers 58 s; davon rund 20–27 s einmaliges Scaffold (Modul-Fixture) und rund 9 s
der eigentliche Kettenlauf. Das ist der Aufschlag, den die volle Suite in der Merge-Runde bezahlt.

### 1.2 FR-0029 — Workflow-Pilot

`docs/pilot/2026-09-01-research-pilot.md`, im Muster der dev-Piloten (datiert, Quelle genannt, ein
Befund je nummerierter Überschrift mit der gemessenen Zeile). Befunde R1–R9.

**Angemeldete Abweichung, im Dokument ganz oben:** das ist ein **Apparat-Pilot**, kein
Persona-Pilot. Gefahren wurden alle Phasen 0–10 der Verfassung als echte Prozesse. Was diese
Methode **nicht** kann, steht ebenfalls dort: Verhaltensbefunde wie P4-2 oder P4-5. **FR-0029 ist
damit nicht erledigt** — der Persona-Lauf steht aus. Die Begründung dafür ist auf Rüge des Prüfers
korrigiert: der Stream-Auftrag verbietet die globale Installation, aber **ob** `claude --print` ein
getauschtes HOME/`CLAUDE_CONFIG_DIR` annimmt, ist schlicht **nicht gemessen** — mein eigenes Rig
zeigt ja, dass ein Wegwerf-HOME den globalen Speicher gar nicht anfasst.

### 1.3 Die Fixes — alle in `report_lint.py`, plus zwei Sätze der Verfassung

`team-kits/research-team/templates/repo/scripts/report_lint.py`:

1. **Auffinden** (`tracked_reports`): Eigenschaft statt Pfad-/Endungsliste — ein Bericht liegt
   unmittelbar in einem Verzeichnis namens `reports` und seine Bytes dekodieren als UTF-8; gefragt
   wird git mit `--cached --others --exclude-standard` und `core.quotepath=off`.
2. **Markup ist keine Behauptung** (`_without_markup`): `<style>`/`<script>` und Tags werden
   ausgeblankt, Zeilenumbrüche bleiben. **Die Regel ist in der Nacharbeit ersetzt worden** — siehe
   Abschnitt 6, B1/B6: ein Tag ist jetzt daran erkennbar, dass hinter `<` ein **Namensbuchstabe**
   steht und bis zum `>` kein zweites `<` kommt; die Zeilengrenze ist weg.
3. **Ausgabeströme auf UTF-8** — dieselbe Schreibweise wie `quality.py`, das dieses Skript als
   Unterprozess fährt.
4. **`utf-8-sig` statt `utf-8`** beim Lesen (Nacharbeit, B5).

`team-kits/research-team/constitution/AGENTS.md`, zwei Sätze, beide **kürzer** als vorher
(Abschnitt 6, B4):

* §4: „`EXP` carries the delivery approval at class `large`." → „every `EXP` carries the delivery
  approval." (53 → 42 Zeichen)
* §4 Punkt 4: „an `EXP` may not reach `ANALYZED` without its report in `evidence_refs`." → „no
  merge passes an `EXP` in `ANALYZED` without `evidence_refs`." (72 → 63 Zeichen)

**Und das Neu-Eintragen war doch nötig — auch nach unten.** Ich hatte den Deckel als *Maximum*
gelesen; `test_context_budget::test_the_recorded_ceiling_is_the_measurement_and_not_a_typed_number`
verlangt **Gleichheit** („der eingetragene Deckel IST die Messung"). Der Suitenlauf hat es
gefunden: `{'research-team': (45422, 45402)}`. Also beide Ratschen ordentlich neu eingetragen,
je mit Notiz und Journalzeile:

* `python tools/record_lead_package_sizes.py --write --note "…"` → `SHRANK research-team
  45422 B -> 45402 B (-20)`, Journal in `docs/reviews/phase0-disposition.md` §10.
* `python tools/pin_constitution_sections.py --write --note "…"` — die beiden geänderten
  Sektionen (§2 „Hard enforcement", §4 „Requirement hierarchy") waren gepinnt und meldeten
  sich als CHANGED; Journal in §9 derselben Datei.

Beide Rekord-Dateien liegen außerhalb des ursprünglichen `allowed_scope` — DEC-0057 (c) sieht
genau das vor („ratchet files may be re-recorded inside a stream to keep its suite green but are
ALWAYS re-recorded on the merge with a note"). **Die Merge-Runde muss beide erneut eintragen.**

`report_lint.py` ist research-eigen (dev und office liefern es nicht), also **kein** Spiegel und
kein Naht-Punkt; `KIT_SPECIFIC_SCRIPTS` bleibt leer. Sonst wurde keine gespiegelte Datei
angefasst — die Spiegelregel läuft in `tools/test_hooks.py` mit.

### 1.4 Löcherliste

`docs/POST_V2_WISHLIST.md` um **H92, H93, H94, H95** ergänzt, je mit Mechanismus, gemessener Kette
und Urteil, und mit den Belegen des Prüfers. Das ist eine **Scope-Erweiterung** gegenüber dem
ursprünglichen `allowed_scope` (dort standen nur `docs/pilot/**` und `docs/reviews/**`) und geht
auf die ausdrückliche Anweisung des Leads in der Nacharbeit zurück.

## 2. Die roten Messungen (Hausregel 5)

Jede einzeln, in einem frischen Klon **außerhalb** des Repos (`_round-scratch/TSK-0103/red2\`,
`red3\`, Kopie des Worktrees ohne `.git`), Defekt wiederhergestellt, `bump_kit_version.py` gefahren
(sonst verweigert das Scaffold auf den Kit-Hash und man misst den Stempel statt den Fix), Test
gefahren. Treiber: `red_runs.py`, `red_h92.py`, `red_v2.py`.

| Was zurückgedreht | Test | Beobachtet |
|---|---|---|
| `tracked_reports()`/`lint()` auf die alte Pfad- und Endungsliste | `test_a_rendered_report_is_found_where_the_kit_actually_renders_it` | FAILED — `AssertionError: [report_lint] no reports to check.` |
| Umstellung der Ausgabeströme entfernt | derselbe Test | FAILED, Zeile 403 — der Berichtsname kommt als Mojibake zurück |
| Markup-Ausblanken ganz entfernt | `test_the_stylesheet_of_a_rendered_html_report_is_not_read_as_a_result` | FAILED — `result without an n` auf der CSS-Zeile |
| **Tag-Regel zurück auf die Zeilengrenze** (kein Namensbuchstabe verlangt) | `test_prose_with_an_inequality_pair_is_not_read_as_markup` **und** `test_the_stylesheet_…` | **beide FAILED** — die Prosa-Richtung verliert ihren Befund, die Markup-Richtung bekommt einen falschen |
| **`utf-8-sig` zurück auf `utf-8`** | `test_a_bom_in_front_of_a_heading_does_not_turn_it_into_a_claim` | FAILED |
| H92 **geschlossen** statt zurückgedreht: `dispatch._assert_task_origin_matches_root` zusätzlich über `report._hangs_from` | `test_a_task_on_an_experiment_cannot_name_the_question_the_experiment_hangs_from` | FAILED, Zeile 315 — `assert 0 == 1`, `create-task` gibt `TSK-0001 DRAFT (researcher)` |

Die letzte Zeile ist die Gegenprobe zur Lücken-Behauptung: der Test wird laut, sobald die Lücke
geschlossen ist, statt still eine Deckung zu behaupten. Beim ersten Anlauf schlug er aus dem
falschen Grund fehl (mein Mutationsskript schrieb eine kaputte Fortsetzungszeile, `SyntaxError` in
`dispatch.py`); der Eintrag oben ist der wiederholte, gültige Lauf.

## 3. Suiten (DEC-0050: was die Runde berührt)

Abschlusslauf nach der letzten Nacharbeit, ohne jede Änderung während des Laufs:
`_round-scratch/TSK-0103/suite_final2.log`.

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | `All checks passed!` |
| `python tools/validate.py` | `all structural checks passed` |
| `test_repo_hygiene` + `test_context_budget` + `test_shortening_net` + `test_role_contracts` + `test_e2e` + `test_research_chain` | **140 passed** in 143,8 s |
| `tools/test_hooks.py` (trägt Spiegelregel, `report_lint`-Verdrahtung und die Kit-Versionen) | **876 passed, 13 skipped** in 827,3 s |

Volle `tools/`-Suite bewusst **nicht** gefahren — Stream-Regel und DEC-0050; sie gehört der
Merge-Runde.

**Eine Warnung für die Merge-Runde, gemessen:** zwei frühere Läufe zeigten `3 failed` in
`test_hooks.py` (`test_install_ps1_codex_*`), jedes Mal mit `research-team: kit files changed but
VERSION not bumped`. Ursache war **mein eigener Edit während des laufenden Suitenlaufs** — genau
der 2026-08-04-Fall aus CLAUDE.md, in einem einzigen Baum. Wer nachbessert, stempelt vorher und
fasst währenddessen nichts an.

**Stempel (PROVISORISCH, DEC-0057 d):** `research-team` `2026.08.31-3` → **`2026.09.02-1`**.
`dev-team` und `office-team` unverändert (`2026.08.31-6` / `2026.08.31-3`) — gegengeprüft in der
Ausgabe von `bump_kit_version.py`.

## 4. Befunde für den Lead — jetzt in der Löcherliste, nicht nur hier

| Nr. | Kern | Zuständig |
|---|---|---|
| **H92** | `report._root_of` löst EINEN Sprung auf; die von §4 dokumentierte Kette `RQ → HYP → EXP → TSK` ist nicht anlegbar. Der Kernel widerspricht sich selbst dreifach: `cli.py:484` führt `EXP` als legalen Ursprung, `cli.py:482` nennt `--product-requirement` „the PR/RQ root", und die Verweigerung formuliert ihren Ausweg transitiv („hangs from"). **Die Verfassung hat recht, der Kernel den Fehler.** | Kernel |
| **H93** | Die Freigabe, auf die der genannte Ausweg zwingt, gibt es laut §4, `INVALIDATION_TARGET` und `APPROVAL_TRANSITIONS` nicht — sie prägt trotzdem; ihr `subject_manifest` schneidet gegen `_SCOPE_FIELDS` und trifft bei `HYP` **kein einziges Feld** (der Nutzer unterschreibt Identität + Revision, keinen Inhalt); `HASHED_FIELDS` kennt kein `HYP`, sie stirbt also nie; und die Aufgabe unter der `HYP` fällt aus `accepted_without_a_verdict` heraus (`report.py:1509-1511` filtert auf `ROOT_TYPE_BY_KIT.values()`). **Sicherheitsrelevant, nicht Buchhaltung.** | Kernel |
| **H94** | Der gerenderte Bericht hat keinen Schreibweg (`gate_write_scope` rc 2 auf beiden §6-Dateien), während §17 ihn zur Vollständigkeitsbedingung macht. Der Merge blockt dabei auf einem **leeren `evidence_refs`**, nicht auf der Datei. | Kernel oder Verfassung |
| **H95** | Die Ursprungsprüfung fällt bei **mehrdeutiger** Elternschaft OFFEN aus: `_root_of` → `None`, `dispatch.py:176-177` überspringt. Aufgabe unter fremder Wurzel rc 0, `validate` 0 Fehler; einelterige Kontrolle rc 1. **Kit-unabhängig** (jeder Typ mit Eltern-LISTE) und verschwindet **nicht** mit H92 — der Prüfer hat H92 im Klon geschlossen, der Weg blieb rc 0. | Kernel |

Ohne Löchernummer, aber gleicher Klasse:

* **Naht `tools/test_hooks.py`** — `test_a_kit_checker_that_declares_a_quality_stage_is_run_by_the_pipeline`
  baut sein Prüfprojekt mit `<root>/reports/final.md`: die einzige Kombination, die der defekte
  Sucher traf, und die einzige, die ein ausgeliefertes research-Projekt nicht hat. Grün über die
  ganze Lebenszeit des Defekts. Datei außerhalb des `allowed_scope` — nicht angefasst.
* **Naht `presets.yaml` / §6** — `solo` installiert keinen `report-writer`, während §6/§17 ihm den
  Bericht zuweisen, an dem der Merge hängt. `research-engineer` fehlt in `solo` und `duo`.
  Produktentscheidung, keine Umsetzer-Reparatur.
* **Beobachtung `tools/conftest.py::mint_via_hook`** prägt über `dev-team/hooks/gate_approval.py`
  aus diesem Repo — heute byte-gleich, misst aber nicht, was es sagt, sobald ein Kit-Haken
  abweicht. Der Kettentest prägt darum über den installierten Haken.

## 5. Was ich bewusst NICHT geschlossen, sondern benannt habe

1. **H92, H93, H94, H95** — Kernel, nicht dieser Stream. Alle vier stehen mit Mechanismus,
   gemessener Kette und Urteil in `docs/POST_V2_WISHLIST.md`; H92, H93 und H95 sind dort als
   **blockierend und offen, zur Abnahme durch den Nutzer** eingetragen, weil ihre Kette innerhalb
   einer Sitzung durchläuft und ein dritter Zustand („bekannt, kommt später") nicht existiert.
2. **Die verbleibende Über-Verweigerung der Markup-Regel:** Prosa, deren `<` von einem
   **Buchstaben** gefolgt und später geschlossen wird (`wenn x<y und z>0`), wird weiter ausgeblankt.
   Begrenzt auf diese eine Spanne durch `[^<>]`, im Code benannt, nicht geschlossen.
3. **Der Persona-Pilot für das research-team** (FR-0029s eigentlicher Wunsch).
4. **Die Zählung „N report(s)"** von `report_lint` zählt die zwei ausgelieferten Vorlagen im Fach
   mit. Sie werden wirklich gelesen (und ergeben 0 Befunde), die Zahl ist also nicht falsch —
   sie hätte sich nur mit einer Namensliste („`*.template.*`") verschönern lassen, und genau die
   wäre die Aufzählung, gegen die Hausregel 1 steht. Bewusst gelassen.
5. **`_report_text` gibt bei einem rein-ASCII-PDF keine `None` zurück** — ein solches PDF wird
   gelesen wie jede andere Datei, nur ein pdflatex-PDF fällt über seine binäre Kommentarzeile
   heraus. Der Docstring sagt das jetzt so; ein `.pdf`-Ausschluss wäre wieder eine Aufzählung.

## 6. Die Nacharbeit — was der Prüfer gefunden hat

| # | Befund | Erledigt |
|---|---|---|
| **B1** | `_MARKUP_RX` löschte **Prosa**: die Zeilengrenze begrenzte das Verschlucken auf eine Zeile, verhinderte es nicht — jedes `<`…`>`-Paar in EINER Zeile galt als Tag. Gemessen an `Bei Werten < 30 … > 10 Personen.` (kein Befund) und `$n < 400$ proves …` (kein Befund), je gegen eine Kontrolle. Meine eigene Gegenprobe prüfte die **einzige** Schreibweise ohne schließendes `>`. | **behoben**: Tag = Namensbuchstabe hinter `<`, kein zweites `<` bis zum `>`. Kommentar auf das Gebaute zurückgeschnitten, Rest-Über-Verweigerung benannt. Roter Test `test_prose_with_an_inequality_pair_is_not_read_as_markup`. |
| **B6** | Dieselbe Grenze in der Gegenrichtung: `<table\n   style="width: 100%">` blieb Markup, das niemand ausblankte → falscher Befund. | **behoben mit B1** (Tags dürfen jetzt Zeilen überspannen). Fixture im Stilblock-Test erweitert; beide ausgelieferten Vorlagen weiter 0 Befunde (nachgemessen). |
| **B3** | Docstring behauptete, ein gerendertes PDF falle heraus. Ein rein-ASCII-PDF dekodiert als UTF-8 und wird gelesen. | **behoben**: Satz auf die Definition zurückgeschnitten, ohne zweite Aufzählung. |
| **B5** | `encoding="utf-8"` statt `utf-8-sig`: ein BOM vor einer Überschrift hebt die `#`-Ausnahme auf → Falsch-Positiv, BOM landet roh in der Ausgabe. | **behoben**, roter Test `test_a_bom_in_front_of_a_heading_does_not_turn_it_into_a_claim`. |
| **B4** | Meine Begründung war falsch. Der Deckel verbietet **Wachstum**, nicht **Korrektur**. | **behoben**: beide Sätze korrigiert, je kürzer als vorher. Zweiter eigener Irrtum dabei, von der Suite gefunden: der Deckel ist eine **Gleichheit**, nicht ein Maximum — beide Ratschen sind jetzt ordentlich neu eingetragen (Abschnitt 1.3). Die Docstring-Halbsätze „das Kit-Dokument sagt es noch nicht" sind gestrichen und durch die Wahrheit ersetzt (die Verfassung nennt keinen Test, weil kein Platz dafür ist — der Docstring sagt das, statt einen Zeiger zu behaupten). |
| **B2** | Neues Loch: die Ursprungsprüfung fällt bei mehrdeutiger Elternschaft OFFEN aus, kit-unabhängig, und verschwindet **nicht** mit H92. Mein Pilotsatz „R4 … verschwindet mit R1" war falsch. | **als H95 eingetragen**, Pilot R4 vollständig neu geschrieben, Zusammenfassungszeile korrigiert. Kein Fix (Kernel). |
| klein | H94 im Protokoll überzeichnet; Kettenkosten 45,7 s statt ~1 min; FR-0029-Begründung „verboten" statt „nicht gemessen". | alle drei korrigiert (oben). |

## 6a. Zweite Prüferrunde — drei Prosa-Stellen

| # | Befund | Erledigt |
|---|---|---|
| **N1** (blockierend) | Der Pilot behauptete in R8 und in der Zusammenfassungszeile weiter, die zwei Sätze seien **nicht** repariert — mit der Deckelzahl als Begründung und einem Vorschlagswortlaut, den das Paket gar nicht liefert. Das Paket hat sie repariert. | R8 komplett neu: Überschrift und Zeile auf **behoben**, beide **gelieferten** Wortlaute als Vorher/Nachher-Tabelle, Zeiger auf die Journal-Abschnitte §9/§10 in `docs/reviews/phase0-disposition.md`. **Die Zahl 45 422 ist gestrichen, nicht aktualisiert** — sie lebt in `tools/lead_package_sizes.json` und der Journalzeile. Nebenbei fiel auf, dass R7 dieselbe falsche Begründung erbte („hängt am Deckel"); dort steht jetzt der wahre Grund: welcher Ersatzort der gesegnete ist, ist eine Produktentscheidung. |
| **N2** (ein Wort) | Der Docstring nannte §4 für einen Satz, der in §2 Punkt 4 steht (`AGENTS.md:56`, Überschrift Zeile 48; §4 beginnt Zeile 90). | `§2 (point 4)`. |
| **N3** (Klausel + Spanne) | Der Kommentar sagte „`[^<>]` bounds the other one to a single span" — ein Span ist mit `DOTALL` **zeilenübergreifend**; der Prüfer hat drei geblankte Prosazeilen gemessen. | **Klausel korrigiert**, im Code und im Piloten: die Spanne endet am nächsten `<`, nicht an der Zeile und nicht am Absatz, und eine ganze Passage kann verstummen. **Die vorgeschlagene Längengrenze habe ich gemessen und verworfen** — Begründung unten. |

**Warum keine `{0,200}`-Grenze.** Der Lead schlug sie vor; ich habe sie gegen die ausgelieferten
Kits gemessen, bevor ich sie einbaute. Über jede `.html`/`.md`/`.tex` der drei Kits ist das
**längste echte Tag 70 Zeichen** lang und einzeilig, während die beiden Prosa-Fehltreffer
**88 und 220** Zeichen messen (beide in `templates/project_memory/product/masterplan.md`, ein
`<Platzhalter …>` über zwei Zeilen). **Kein Schnitt trennt die Klassen**: 200 hätte den 88er stehen
gelassen und hätte dafür jedes echte Tag über 200 Zeichen freigelegt — ein stiller Fehltreffer
wäre gegen einen lauten getauscht, die Klasse bliebe offen, und die Zahl wäre von da an zu pflegen.
Gegenprobe auch zur Alternative: eine **Tag-Grammatik** (HTML-StartTag statt `[^<>]*`) fängt den
220er, verfehlt den 88er weiterhin — sie ist der richtige Weg, aber größer als das, was in einer
Runde ohne weiteren Durchgang prüfbar ist. Der Rest steht darum als benannter Rest im Kommentar der
Regel, mit seiner wahren Reichweite. Hausregel 1: lieber eine ehrliche Grenze als eine gegriffene
Zahl.

**Läufe der Fassung 3** (nach dem Neu-Stempeln, ohne Änderung währenddessen):
`ruff` **All checks passed**, `validate.py` **all structural checks passed**,
`test_research_chain` + `test_shortening_net` + `test_context_budget` + `test_repo_hygiene`
**93 passed** (148,9 s), und die stempel- und spiegelempfindlichen Fälle aus `test_hooks.py`
(`-k "install_ps1 or mirror or quality_stage or kit_version"`) **5 passed**. Die volle
`test_hooks.py` lief in Fassung 2 grün (876/13); Fassung 3 ändert an `report_lint.py` nur einen
Kommentar plus den Stempel, und genau die Tests, die beides lesen, sind oben einzeln gefahren.

## 7. Abweichungen vom Auftragstext

1. Der Auftrag nannte `docs/pilot/2026-08-31-research-pilot.md`; gemessen und geschrieben wurde am
   **2026-09-01**. Geliefert als `docs/pilot/2026-09-01-research-pilot.md`.
2. `docs/POST_V2_WISHLIST.md` liegt nicht im ursprünglichen `allowed_scope`. Geschrieben auf
   ausdrückliche Anweisung des Leads in der Nacharbeit.
3. `tools/lead_package_sizes.json` und `tools/constitution_section_pins.json` ebenfalls nicht —
   beide sind Ratschen-Rekorde, die die Verfassungskorrektur aus B4 zwingend nach sich zieht,
   und DEC-0057 (c) erlaubt einem Stream ausdrücklich, sie zu setzen, verlangt aber ihr
   Neu-Eintragen in der Merge-Runde. Je eine Journalzeile in `docs/reviews/phase0-disposition.md`.

## 8. Übergabe

* Patch: `C:\Offline Repos\v2-testbed\_round-scratch\TSK-0103\stream-research.patch`
  (`git add -N` für die neuen Dateien, dann `git diff HEAD`).
* Geänderte Dateien: `team-kits/research-team/templates/repo/scripts/report_lint.py`,
  `team-kits/research-team/constitution/AGENTS.md`, `team-kits/research-team/VERSION`,
  `docs/POST_V2_WISHLIST.md`, `docs/reviews/phase0-disposition.md`,
  `tools/lead_package_sizes.json`, `tools/constitution_section_pins.json`.
* Neue Dateien: `tools/test_research_chain.py`, `docs/pilot/2026-09-01-research-pilot.md`.
* Nicht angefasst: `team-kits/kernel/**`, `dev-team/**`, `office-team/**`, `scaffold_team.*`,
  `install.*`, `user/**`, `.claude/**`, `project_memory/**` außer diesem Staging-Pfad,
  `tools/test_hooks.py`, `tools/test_e2e.py`.
