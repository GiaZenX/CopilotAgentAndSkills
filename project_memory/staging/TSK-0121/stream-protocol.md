# TSK-0121 — Strom G4-1 „Test discipline and hook hygiene" (PR-0004, AC-1..AC-4)

Umsetzer-Protokoll. Arbeitsbaum: `C:/Offline Repos/v2-testbed/_worktrees/g4-testgate`
(Branch `g4/testgate`, Stand 75a00d1). Scratch: `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0121/`.

## 0. Vorgefunden (gemessen, vor jeder Änderung)

| Was | Stand am 75a00d1 | Wie gemessen |
|---|---|---|
| Gate 5 (`.claude/hooks/gate_test_scope.py`) | existiert nicht; `.claude/hooks/` trägt vier Gates + `_harness.py` + `_sandbox.py` + `test_gates.py` | `ls .claude/hooks` |
| `test_gates.EXPECTED_TOOLS` | fünf Einträge (gate 1..4 + `gate_approval.py`), beidseitig gegen `.claude/settings.json` verglichen | gelesen, Zeile 419-427 |
| Kit-Haken für Testumfang | keiner. Kein Kit-Haken liest eine `pytest`-Zeile | `grep` über `team-kits/*/hooks/` |
| Deklarierte Testfläche dieses Repos | nur Prosa in `CLAUDE.md` (`python -m pytest tools/ -q`, `python -B -m pytest .claude/hooks/test_gates.py -q`), keine maschinenlesbare Erklärung | gelesen |
| `office-team/settings/settings.json` | acht Einträge auf einem Shell-Matcher, **keiner** nennt `timeout` — **mit Messung und mit Absicht** | gelesen |
| `tools/test_hooks.py::test_a_registration_names_a_window_exactly_when_its_gate_can_outlive_the_default` | ausgeliefert; verbietet ein Fenster für ein Gate ohne eigene Kindgrenze | gelesen, Zeile 2921-2987 |
| `kit_browser_checks.py` (dev + research) | byte-gleich, 205 Zeilen, prüft nur Mount-Element + Konsolenfehler + Auslieferungsfrische | `sha256` beider Dateien |
| `kit_design_render.py` | trägt C1/C2/C3 bereits gebaut (`_PAGE_PROBE`, `keyboard_path`, `conformance`) — aber nur für den gestagten DSN-Entwurf | gelesen, TSK-0119 |

**Vier Host-Abstürze während der Runde** (fremde Last, Ursache gemessen und abgestellt). Nach
jedem: Zustand von der Platte gelesen, nichts aus dem Gedächtnis neu gebaut, Spiegel-Hashes und
Parse geprüft. Kein Verlust; die Runde ist ununterbrochen fortgesetzt worden.

## 1. Der Auftragsfehler, den diese Runde zuerst gemessen hat (AC-2, erste Hälfte)

**AC-2 verlangt wörtlich: „every hook entry of every kit settings.json names a timeout (the eight
office shell hooks first)". Diese Zeile ist durch eine ausgelieferte Messung widerlegt, und
`DEC-0070` führt genau diesen Satz schon als Orchestrator-Fehler der Generation 3** („an order
sentence 'every new registration carries a timeout' contradicting a shipped test (E)").

Gemessen, nicht behauptet — `tools/provider_observations.json` → `hook_deadlines`, aufgenommen
2026-08-23 gegen claude.exe 2.1.239: ein Eintrag mit `timeout: 5`, dessen Haken 20 s brauchte,
wurde **getötet, und der verweigerte Befehl lief**. Ein Eintrag **ohne** `timeout` überlebte 310 s
und 560 s und wurde erst bei 900 s getötet. Ein Fenster ist also ein **Tötungsfenster**, und ein
getöteter Haken ist ein stilles ALLOW. Die ausgelieferte Regel steht in
`tools/test_hooks.py::test_a_registration_names_a_window_exactly_when_its_gate_can_outlive_the_default`
und lautet zweiseitig: ein Fenster ist genau dann erlaubt, wenn das Gate **vor** ihm verweigert
(eigene Kindgrenze kleiner als das Fenster); kein Fenster ist genau dann erlaubt, wenn kein Gate
der Kette noch laufen kann, wenn das Vorgabefenster schliesst.

Ich habe die Forderung deshalb **nicht** ausgeführt. Gebaut ist die Eigenschaft, die dahinter
steht — siehe AC-2 in Abschnitt 4.

## 2. Plan — und der verworfene Weg in einer Zeile

Gebaut wird die **Eigenschaft** „diese Zeile fährt die ganze erklärte Testfläche, ohne dass die
Zeile sagt, dass sie der Lieferlauf ist", einmal als Gate 5 dieses Repos und einmal als Kit-Haken
×3; dazu die Prozedur-Sätze im QS-Rollentext, der Fristen-Leser der Kits, und C1/C2/C3 im
`browser_smoke()` der gebauten App.

**Verworfen (eine Zeile):** den Umfang als *Prozentsatz gestarteter Tests* zu messen — das
verlangt eine Sammlung der ganzen Suite, also genau die Kosten, gegen die das Gate existiert
(`FR-0086` Anpassung 1); die Eigenschaft „die Zeile nennt keine Auswahl" kostet nichts.

## 3. Nahttabelle (empfangen / erwartet beim Merge)

| Datei | Geteilt mit | Was ich schreibe | Was der Merge anwenden muss |
|---|---|---|---|
| `.claude/hooks/test_gates.py` | G4-2 (Löcher-Richter), G4-4 (Timing-Test) | **ein eigener Block am Dateiende**, plus drei Stellen im Bestand: `EXPECTED_TOOLS`, `_refusable`, `build_project` (alle drei sind Tabellen/Fixtures, die jedes registrierte Gate nennen müssen — unvermeidbar) | die drei Stellen zusammenführen, den Block anhängen |
| `.claude/settings.json` | — | ein neuer `Bash\|PowerShell`-Eintrag mit `timeout: 120` | — |
| `tools/test_hooks.py` | G4-2, G4-3, G4-4 | **ein eigener Block am Dateiende** (Kit-Gate, Fristen, QS-Text, C1/C2/C3) | Block anhängen |
| `tools/test_surface.json` | neu | die erklärte Testfläche dieses Repos | übernehmen |
| `tools/constitution_section_pins.json`, `docs/reviews/phase0-disposition.md` | alle Ströme, die einen gepinnten Text ändern | nachgezogene Pins für die drei `ENFORCEMENT.md` | **beide Ströme müssen ihre Pins gemeinsam neu schreiben** (`python tools/pin_constitution_sections.py --write --note …`), sonst überschreibt der zweite Merge den ersten |
| `docs/POST_V2_WISHLIST.md` | G4-2 (migriert die Löcherliste in Items) | H151, H152, H153 im **aktuellen** Format | G4-2s Migration trägt sie mit |
| `team-kits/*/VERSION` | alle Ströme | vorläufiger Stempel | Patch trägt die VERSION-Hunks **nicht** |
| `team-kits/*/hooks/_kernel.py` | **nicht als Naht benannt gewesen** — ich schreibe hinein (Fristen-Leser) | ×3 byte-gleich | beim Merge gegen andere Ströme prüfen; siehe Befund N-1 |
| `team-kits/*/hooks/session_status.py`, `_routine.py` | meine Dateien; G4-3 meldet Sätze | **unverändert** — siehe Befund N-2 | — |
| Verfassungs-Inventar der drei Kits | **G4-3** | siehe Abschnitt 8 (wörtlich) | G4-3 setzt sie; bis dahin sind zwei Tests rot |

## 4. Abnahmezeile je Kriterium, mit den roten Tests

### AC-1 (FR-0086) — ein Gate auf den UMFANG eines Testlaufs, hier und in den Kits

**Gebaut, dieses Repo:** `.claude/hooks/gate_test_scope.py` (Gate 5), registriert in
`.claude/settings.json` auf `Bash|PowerShell` mit `timeout: 120`, in `test_gates.EXPECTED_TOOLS`
eingetragen (die Suite vergleicht beide Richtungen). Die erklärte Testfläche steht als Daten in
`tools/test_surface.json`.

**Die Eigenschaft, nicht die Aufzählung.** Eine Zeile fährt die ganze erklärte Fläche, wenn
(a) die Stufe den erklärten Läufer wirklich startet — ihr Verb, oder das Wort, das ein `-m` eines
Interpreters ihm übergibt —, (b) unter ihren Stellungswörtern eines steht, das eine erklärte
Wurzel IST oder ein Vorfahr davon (kein Stellungswort = das Arbeitsverzeichnis des Läufers, also
auch ein Vorfahr), und (c) keines der Wörter eine Option ist, nach der die Zeile die Fläche nicht
mehr ganz fährt. Nur (c) ist eine Aufzählung; sie steht in der **Erklärung des Projekts**, nicht
im Gate, und trägt einen Stolperdraht an beiden Enden (Abschnitt 6).

**Gemessen als Prozesse** (Rig `_round-scratch/TSK-0121/rig/cases.py`, Stellvertreterprojekt
ausserhalb des Repos, gebaut mit `test_gates.build_project`):

| Zeile | rc | Grund |
|---|---|---|
| `python -B -m pytest tools/ -q` | 2 | „runs the WHOLE declared test surface `tools`" |
| `python -B -m pytest .claude/hooks/test_gates.py -q` | 2 | dieselbe, zweite erklärte Fläche |
| `python -B -m pytest` (kein Ziel) | 2 | Arbeitsverzeichnis = Vorfahr |
| `python -B -m pytest . -q` | 2 | Vorfahr |
| `pytest tools/` | 2 | Läufer als Verb |
| `python -B -m pytest tools/test_hooks.py -q` | 0 | Auswahl (Unterpfad) |
| `python -B -m pytest tools/test_kernel.py::test_x` | 0 | Auswahl (Knoten-Id) |
| `python -B -m pytest tools/ -k test_foo` | 0 | Auswahl (Filteroption) |
| `python -B -m pytest tools/ --collect-only` | 0 | fährt nichts |
| `grep -rn pytest tools/`, `ls tools/` | 0 | Läufername ist Text, nicht Verb |
| `DELIVERY_RUN=BUG-0001 python -B -m pytest tools/ -q` | 0 | Lieferpräfix, offenes Item |
| `DELIVERY_RUN=TSK-0003 …` / `…=NOPE-9999 …` | 2 | „leads no open work" |
| `$env:DELIVERY_RUN="BUG-0001"; …` (PowerShell) | 0 | zweite Schreibweise des Präfixes |
| dieselbe Zeile nach `evidence --run-scope full --result pass` | 2 | DEC-0063 (4) |
| dasselbe nach `--result fail` | 0 | Befunde schicken die Arbeit zurück in die Suiten |

**Ein gemessener Defekt am eigenen Bau, unterwegs behoben:** `-m` gehört zwei Programmen
gleichzeitig (Modul-Flag des Interpreters, Marker-Filter von pytest). Über die ganze Stufe
gelesen las das Gate `python -B -m pytest tools/ -q` — die dokumentierte Volllaufzeile dieses
Repos — als Auswahl und liess sie durch (**rc 0 gemessen**). Behoben durch `_handed_to`, das erst
ab dem Läuferwort liest.

**Rot zuerst, je Zweig** (Rig `rig/mutate.py`; Klon unter `_round-scratch/TSK-0121/mutant`, **ohne
`.git`**, jede Datei binär gelesen und binär zurückgeschrieben; das Rig verweigert den Lauf
ausserhalb seines eigenen Verzeichnisses). **14 von 14 RED:**

| Wiederhergestellter Defekt | Roter Test | Ausgang |
|---|---|---|
| blosser Volllauf wird nicht verweigert | `test_gate5_refuses_a_bare_full_run_of_every_declared_surface` | RED |
| Lieferpräfix wird nicht gelesen | `test_gate5_lets_the_delivery_prefix_through_in_both_shells` | RED |
| Filteroptionen zählen nicht | `test_gate5_lets_a_selection_through` | RED |
| ein Unterpfad gilt als Wurzel | `test_gate5_lets_a_selection_through` | RED |
| zweiter Volllauf wird nicht verweigert | `test_gate5_refuses_the_second_full_run_of_a_round_but_not_after_findings` | RED |
| ein FEHLGESCHLAGENER Volllauf schliesst die Runde | dieselbe | RED |
| Präfix muss kein offenes Item nennen | `test_gate5_refuses_a_delivery_prefix_that_leads_no_open_work` | RED |
| `-m`-Grenze (der gemessene Defekt oben) | `test_gate5_reads_the_module_flag_as_the_interpreters_and_the_runners_own` | RED |
| Läufer = irgendein Wort statt Verb | `test_gate5_does_not_judge_a_line_that_only_names_the_runner` | RED |
| Schwelle als Konstante statt Daten | `test_gate5_charges_nothing_to_a_project_whose_suite_runs_in_seconds` | RED |
| nicht erklärte Fläche wird beurteilt | `test_gate5_says_nothing_where_a_project_declares_no_test_surface` | RED |
| unlesbare Erklärung wird durchgelassen | dieselbe | RED |
| die Registrierung selbst entfernt | `test_the_registration_is_the_one_the_contract_asks_for` | RED |
| erklärte Wurzel deckt keine Testdatei | `test_every_test_file_of_this_repo_lies_under_a_declared_surface` | RED |

**Gebaut, Kits:** `team-kits/*/hooks/gate_test_scope.py`, **×3 byte-gleich** (sha256 `62a26ad7…`),
registriert in allen drei `settings/settings.json` auf `Bash|PowerShell` über `_gate.py`,
**ohne `timeout`** (Begründung Abschnitt 5), plus eine eigene Zeile in `hooks/ENFORCEMENT.md` je
Kit und die nachgezogenen Abschnittspins. Anwendbarkeit ist eine **Erklärung des Projekts**: ein
`INV` mit `scope: test_surface`. Ohne dieses Item urteilt der Haken über nichts — das ist
PR-0004s erste Invariante als Antwort des Gates.

**Gemessen als Prozesse auf einem echten, frisch gescaffoldeten dev-Piloten**
(`scaffold_team.ps1` mit `USERPROFILE` auf eine Scratch-Kopie der Kits — **keine Installation in
den globalen Speicher**), Pilot unter `_round-scratch/TSK-0121/pilotbase/pilot`:
`python -m pytest tests/ -q` rc 2 · `pytest` rc 2 · `tests/test_one.py` rc 0 · `-k slow` rc 0 ·
`grep -rn pytest tests/` rc 0 · `npm test` rc 0 (Läufer nicht erklärt) · `DELIVERY_RUN=PR-0001 …`
rc 0 · `DELIVERY_RUN=PR-9999 …` rc 2 · PowerShell-Präfix rc 0 · nach
`scripts/harness.py evidence --run-scope full --result pass` rc 2 mit der DEC-0063-(4)-Zeile.

### AC-2 (FR-0057) — Fristen und die Prozedur in der Rollensprache

Die wörtliche Forderung ist widerlegt (Abschnitt 1) und **nicht** gebaut. Gebaut ist die
Eigenschaft dahinter, dort wo die Messung selbst die Lücke benennt.

**Gebaut:** `_kernel.registered_window()` + `_kernel.start_the_deadline()`, aufgerufen aus
`run_gate`, **×3 byte-gleich** (sha256 `27fd0bc6…`). Das ist die Kit-Seite von
`_harness.Deadline`: das Fenster wird aus der Registrierung gelesen (kleinster zutreffender
Eintrag); fehlt es, gilt das gemessene Vorgabefenster; ein Fenster, das das Gate gar nicht
beantworten kann, wird **sofort verweigert**; ein Budget, das während der Entscheidung ausläuft,
beendet den Prozess mit einer **Verweigerung** statt mit einem Kill.

Bis dahin stand in `tools/provider_observations.json` → `hook_deadlines` wörtlich: „The kits have
no in-process deadline: nothing in `_compat` stops a gate before it is killed … that is what the
harness's own construction closes and what no kit hook does." Genau dieser Satz ist der Anlass.

**Zwei Stellungen, zwei Sätze — ein gemessener Befund am eigenen Bau.** Der erste Schnitt hatte
nur den Wachhund; sein Test war **flatterhaft in der gefährlichen Richtung**: das Gate beendete
seine billige Entscheidung vor dem Faden und lieferte **rc 0 unter einem Fenster, das es nie
hätte einhalten können** (gemessen 2026-09-04, `git status --short`). Behoben durch eine synchrone
Prüfung vor der Entscheidung. Damit die beiden Stellungen unterscheidbar bleiben — sonst wäre der
Wachhund-Test grün aus dem falschen Grund —, trägt jede ihre eigene Klausel: „before it had read
anything at all" (Fenster erhöhen) und „while it was still reading" (Aufruf teilen).

**Rollentext:** `team-kits/dev-team/skills/quality-engineer/SKILL.md`. Der Umfangssatz stand dort
bereits („in fix loops run ONLY the failing + affected tests; run the FULL suite … exactly ONCE
right before your PASS verdict"); was fehlte, war der Schritt, der ihn **durchsetzbar** macht.
Ergänzt an drei Stellen: die Lieferzeile `DELIVERY_RUN=<TSK-nnnn> <your test command>` (beide
Shells), die Aufzeichnung mit `--run-scope full --run-command`, und der Knopf `test_surface` in
Schritt 2 („Plan the tests").

**Gemessen gegen den Kit-Text, nicht in ihm gesucht:** der Test hebt die Zeilen aus dem
Rollentext und **führt sie aus** — die Lieferzeile durch den echten Gate-Prozess, die
Evidenz-Flags durch den echten Kernel, und danach die zweite Lieferzeile, die jetzt verweigert
wird.

**Rote Tests je Zweig (AC-2):** Abschnitt 6.

## 5. Warum kein `timeout` auf der neuen Kit-Registrierung — und eines auf der Repo-Seite

Die ausgelieferte Regel ist zweiseitig
(`tools/test_hooks.py::test_a_registration_names_a_window_exactly_when_its_gate_can_outlive_the_default`):
ein Fenster ist genau dort erlaubt, wo das Gate seine eigene Kindgrenze VOR ihm erreicht. Der neue
Kit-Haken startet kein Kind und wartet auf nichts — ein Fenster könnte ihn nur mitten in der
Entscheidung töten, und ein getöteter Haken ist ein Durchlass. Also trägt der Eintrag keines, und
der ausgelieferte Test bleibt grün.

Für Gate 5 dieses Repos gilt das Gegenteil, und auch das ist die dortige Regel: **jeder** Eintrag
in `.claude/settings.json` nennt ein `timeout`, weil `_harness.Deadline` es liest und ohne Frist
jeden Aufruf verweigert. Gate 5 trägt `timeout: 120` wie seine vier Nachbarn.

### AC-3 (H139) — C1/C2/C3 auf der GEBAUTEN App

**Gebaut:** `design_standards()` in `kit_browser_checks.py`, aufgerufen aus `browser_smoke()` auf
**derselben** Seite und demselben Laden, die schon den Mount-Test bestanden haben. Die drei Regeln
benutzen den Leser, mit dem auch die eingefrorene Entwurfsrevision beurteilt wird
(`kit_design_render._PAGE_PROBE`, `_probe_config`, `keyboard_path`) — keine zweite Umsetzung
derselben Regeln. Eine Probe-Auswertung für alle drei; der Reduced-Motion-Kontext wird nur
geöffnet, wenn die Seite überhaupt animiert. Verdikte **je Regel**, nicht je Lauf.
dev-team und research-team liefern die Datei weiterhin **byte-gleich** aus (sha256 `1a707745…`);
office-team liefert sie gar nicht aus (kein Frontend), `KIT_SPECIFIC_SCRIPTS` bleibt leer und
braucht keinen Eintrag.

**Zwei Regeln des Entwurfs-Lesers sind bewusst NICHT auf den Build angewandt**, und das ist der
ganze Unterschied zwischen einer eingefrorenen Revision und einem Build: das Farbliteral (ein Build
liefert legitim fremdes CSS aus) und „genau eine Primäraktion je `data-view`" (ein Build trägt
diesen Vertrag nicht). Beide zugleich gepflanzt →
`test_the_build_half_leaves_out_the_two_rules_a_build_cannot_answer` bleibt sauber.

**Gemessen mit echtem Chromium gegen einen echt ausgelieferten Build.** `browser_smoke` startet
`npx --no-install vite preview`; ein `npx` auf dem PATH beantwortet diesen Aufruf und liefert
`frontend/dist` aus. Damit läuft der **ausgelieferte** Code Ende zu Ende: seine Bereitschaftsprobe,
sein Frische-Hash (`index.html` auf der Platte gegen das, was der Server herausgibt) und sein
Playwright-Lauf. Ein node/vite-Install hätte die Maschine gemessen statt die Regel.

| Fall | Erwartet | Ausgang |
|---|---|---|
| sauberer Build | C1, C2, C3 je `ok`, kein `fail` | grün |
| `--fg:#bbbbbb` | C1 „where 4.5:1 is required" | rot auf C1 |
| `<div class="card" style="cursor:pointer">` | C2 „is in no tab order" | rot auf C2 |
| `tabindex="3"` | C2 „overrides the document order" | rot auf C2 |
| `a:focus { outline: none }` | C2 „pixel for pixel" | rot auf C2 |
| Reduced-Motion-Block entfernt | C3 „keep animating…" | rot auf C3 |
| `:focus-visible`-Regel entfernt | C3 „no :focus-visible rule" | rot auf C3 |
| Farbliteral gepflanzt | **kein** Befund | grün |
| kein `frontend/dist` | warn, kein Browserstart, < 5 s | grün |

**Ein gemessener Defekt am eigenen Messrig, unterwegs behoben und nicht als Ursache stehen
gelassen:** der erste Schatten übergab den Interpreter an `os.execv`. Auf Windows quotiert `execv`
nicht, was es zu einer Befehlszeile zusammenfügt — ein Interpreterpfad mit Leerzeichen wird
zerteilt, der Server kam nie hoch, und **alle** Fälle waren rot. Der Kommentar im Rig nennt jetzt
diese Ursache; eine erste, falsche Vermutung (Zeilenenden) stand kurz darin und ist entfernt.

**H139 ist damit geschlossen**, mit dem Test benannt (Modulpräfix):
`tools/test_hooks.py::test_the_built_app_is_judged_on_c1_c2_c3_and_each_is_red_on_its_own_violation`.

### AC-4 — die Kostenseite je Gate, gemessen (DEC-0056)

**Gate 5 dieses Repos**, echte Prozesse, Median aus je fünf Läufen (`rig/cost.py`), gegen ein
registriertes Fenster von **120 s**:

| Zeilenklasse | Median | Maximum |
|---|---|---|
| gewöhnliche Zeile ohne den Läufernamen (`git status --short`) | 0,167 s | 0,171 s |
| Läufername vorhanden, aber nicht gestartet (`grep -rn pytest tools/`) | 0,201 s | 0,202 s |
| eine Auswahl | 0,215 s | 0,384 s |
| ein blosser Volllauf (verweigert) | 0,212 s | 0,219 s |
| ein Lieferlauf mit Item-Auflösung und Evidenzsuche | 0,345 s | 0,381 s |

**Was ein Projekt zahlt, dessen ganze Suite in Sekunden läuft: nichts.** Die Schwelle ist ein
Datenwert; unter ihr urteilt das Gate über die Fläche gar nicht — gemessen in
`test_gate5_charges_nothing_to_a_project_whose_suite_runs_in_seconds` und
`test_gate_test_scope_judges_nothing_where_a_project_declares_no_surface` (drei Zustände: keine
Erklärung, eine billigere Fläche als die Schwelle, die teure Fläche).

**Was ein Projekt ohne UI für AC-3 zahlt: nichts Messbares.** Ohne `frontend/dist` kehrt
`browser_smoke` vor jedem Serverstart zurück; gemessen in
`test_a_project_without_a_built_frontend_pays_nothing_for_the_design_rules` (kein `fail`, kein
`ok`, unter 5 s).

**Kit-Haken, und hier ein Befund am eigenen Bau:** der erste Schnitt las den Invarianten-Speicher
des Projekts auf **jeder** Shell-Zeile vollständig. Gemessen 2026-09-04 an einem Speicher an der
ausgelieferten Obergrenze (sechs Items knapp unter `ITEM_MAX_BYTES`): **3,05 s** allein fürs
Parsen. Seine beiden Nachbarn zahlen das nur bei einem Code-Schreibzugriff bzw. bei Merge/Push —
dieses Gate sitzt auf jeder Zeile. Behoben durch `_could_declare`: der Kopf einer Datei entscheidet,
ob sie die Erklärung sein kann, und ein Kopf, der **nichts** sagt, wird weiterhin ganz gelesen
(fail-closed). Die zweite Richtung ist gemessen:
`test_the_declaration_is_found_even_when_its_scope_key_sits_past_the_head`.

**Die Frist jedes neuen Hakens gegen sein registriertes Fenster:** Gate 5 antwortet im schlimmsten
gemessenen Fall in 0,381 s gegen 120 s. Der Kit-Haken trägt kein Fenster (Abschnitt 5) und
antwortet innerhalb des gemessenen Vorgabefensters von 560 s; sein eigener Wachhund verweigert
jetzt, statt getötet zu werden — beides gemessen
(`test_a_window_already_spent_by_the_gates_own_start_refuses_before_it_decides`,
`test_a_gate_that_runs_past_its_window_mid_decision_refuses_instead_of_being_killed`).

## 6. Rot zuerst — die zweite und dritte Charge

Gleiches Rig, gleicher Klon ausserhalb des Repos, binär geschrieben. **24 von 24 RED** insgesamt
(14 aus Abschnitt 4 plus die folgenden 10 + 6 + 1 korrigierte):

| Wiederhergestellter Defekt | Roter Test | Ausgang |
|---|---|---|
| Kit: blosser Volllauf nicht verweigert | `test_gate_test_scope_refuses_a_bare_full_run_in_every_kit` | RED |
| Kit: Lieferpräfix nicht gelesen | `test_gate_test_scope_lets_the_delivery_prefix_through_in_both_shells` | RED |
| Kit: Filteroptionen zählen nicht | `test_gate_test_scope_lets_everything_that_is_not_a_full_run_through` | RED |
| Kit: Läufer = irgendein Wort | dieselbe | RED |
| Kit: `-m`-Grenze | `test_gate_test_scope_reads_the_module_flag_as_the_interpreters_and_the_runners_own` | RED |
| Kit: Präfix ohne offenes Item | `test_gate_test_scope_refuses_a_prefix_that_names_no_open_item` | RED |
| Kit: zweiter Volllauf | `test_gate_test_scope_refuses_the_second_full_run_but_not_after_findings` | RED |
| Kit: fehlgeschlagener Volllauf schliesst die Runde | dieselbe | RED |
| Kit: nicht erklärte Fläche beurteilt | `test_gate_test_scope_judges_nothing_where_a_project_declares_no_surface` | RED |
| Kit: Schwelle als Konstante | dieselbe | RED |
| Kit: Kopf-Scan überspringt ein unentschiedenes Item | `test_the_declaration_is_found_even_when_its_scope_key_sits_past_the_head` | RED |
| AC-2: die Frist läuft überhaupt | `test_a_window_already_spent_by_the_gates_own_start_refuses_before_it_decides` | RED |
| AC-2: der Wachhund neben der Entscheidung | `test_a_gate_that_runs_past_its_window_mid_decision_refuses_instead_of_being_killed` | RED |
| AC-2: das Fenster wird aus der Registrierung gelesen | `test_a_window_already_spent_by_the_gates_own_start_refuses_before_it_decides` | RED |
| AC-2: Vorgabefenster = die Messung | `test_the_kit_deadline_reader_carries_the_measured_default_window` | RED |
| AC-2: ein gewöhnliches Fenster lässt entscheiden | `test_an_ordinary_window_and_no_window_at_all_leave_the_gate_deciding` | RED |
| AC-2: QS-Text lehrt eine Zeile, die das Gate annimmt | `test_the_run_scope_procedure_the_qe_skill_teaches_is_one_the_apparatus_accepts` | RED |
| AC-2: QS-Text nennt den Knopf, den das Gate liest | `test_the_qe_skill_names_the_knob_the_gate_really_reads` | RED |
| AC-3: C1 auf dem Build | `test_each_planted_violation_of_the_built_app_makes_its_own_rule_fail` | RED |
| AC-3: C2 auf dem Build | dieselbe | RED |
| AC-3: C3 auf dem Build | dieselbe | RED |
| AC-3: die drei Regeln werden BERICHTET, nicht nur geprüft | dieselbe | RED |
| AC-3: die Farbliteral-Regel gehört nicht auf den Build | `test_the_build_half_leaves_out_the_two_rules_a_build_cannot_answer` | RED |
| AC-3: ein Projekt ohne UI zahlt nichts | `test_a_project_without_a_built_frontend_pays_nothing_for_the_design_rules` | RED |

**Eine Mutation war beim ersten Versuch STILL GREEN und ist damit ein eigener Befund**: den Knopfnamen
nur an EINER von zwei Stellen des Rollentexts zu verfälschen liess
`test_the_qe_skill_names_the_knob_the_gate_really_reads` grün. Die richtige Mutation ist die am
Gate (`SURFACE_SCOPE`), weil der Test genau das behauptet — „der Name, den der Text lehrt, ist der,
den der Haken liest"; damit ist er RED.

## 7. Der Stolperdraht auf der einen Aufzählung

`options_that_narrow` ist die einzige Aufzählung, auf der eines der Gates entscheidet. Beide Enden
sind gebaut, in `.claude/hooks/test_gates.py`:

* **toter Eintrag** — `test_every_declared_narrowing_option_is_one_the_runner_still_has` fragt die
  eigene Inventarliste des installierten Läufers (`pytest --help`, kein Sammellauf);
* **Eintrag, der nichts entscheidet** — `test_every_declared_narrowing_option_earns_its_place`
  fährt jeden Eintrag durch den echten Gate-Prozess und verlangt, dass dieselbe Zeile ohne ihn
  verweigert und mit ihm erlaubt wird.

**Eigener Befund, behoben:** zwei Kommentare (der Kopf von `gate_test_scope.py` und das
`_options_that_narrow`-Feld der Erklärung) nannten eine Datei `tools/test_run_scope.py`, die ich
nicht gebaut habe — eine Schutzbehauptung ohne Code. Beide zeigen jetzt auf die zwei Tests oben.
`grep -rn test_run_scope .claude tools` ist leer.

## 8. Naht an G4-3 — die Sätze, die die Verfassungen tragen müssen (wörtlich)

Zwei Tests sind rot und bleiben es, bis G4-3 sie setzt; ich darf `team-kits/*/constitution/**`
nicht anfassen:

* `tools/test_shortening_net.py::test_the_inventory_the_constitution_presents_is_the_registrations_it_ships`
* `tools/test_shortening_net.py::test_every_registered_hook_is_anchored_in_its_kits_constitution`

**Die Änderung ist ein Wort je Kit**, in die alphabetische Inventarliste der Verfassung
(`constitution/AGENTS.md`, die Zeile, die mit „starts:" beginnt):

* `dev-team` (Zeile 92): zwischen `` `gate_test_coverage`, `` und `` `gate_write_scope`, `` einfügen:
  `` `gate_test_scope`, ``
* `office-team` (Zeile 184): zwischen `` `gate_subagent_output`, `` und `` `gate_write_scope`, ``
  einfügen: `` `gate_test_scope`, ``
* `research-team` (Zeile 73): zwischen `` `gate_subagent_output`, `` und `` `gate_write_scope`, ``
  einfügen: `` `gate_test_scope`, ``

Ein erklärender Satz ist **nicht** nötig: die Zeile in `hooks/ENFORCEMENT.md` (von mir gesetzt, ×3)
ist die Stelle, auf die jede Verweigerung zeigt, und sie trägt Regel, Ausnahme und Kostenseite.

## 9. Was ich bewusst NICHT geschlossen, sondern benannt habe

1. **AC-2s wörtliche Forderung** („jeder Haken-Eintrag jedes Kits nennt ein `timeout`") ist
   **nicht ausgeführt** — sie ist durch eine ausgelieferte Messung widerlegt und steht in DEC-0070
   bereits als Orchestrator-Fehler. Der Prüfer hat die
   wörtliche Ausführung gefahren (87 Einträge bekamen `timeout: 120`):
   `test_a_registration_names_a_window_exactly_when_its_gate_can_outlive_the_default` wird rot,
   und zwar für **mindestens 15 office-team-Zeilen** und praktisch jeden Eintrag aller drei
   Kits, der kein eigenes Kind begrenzt — meine erste Angabe „fünf der acht Office-Einträge"
   war zu niedrig und ist hiermit korrigiert. Abschnitt 1 und 5.
2. **Der Implementierer-Rollentext** (AC-2 nennt „quality-engineer and implementer skills") liegt
   **ausserhalb** meines `allowed_scope`: die Positivliste nennt nur
   `team-kits/*/skills/quality-engineer/**`, und das Glob trifft nur dev-team (office hat
   `filing-reviewer`, research hat `reviewer`). Gebaut ist die QS-Hälfte; die Regel erreicht die
   übrigen Rollen aller drei Kits über die `ENFORCEMENT.md`-Zeile, auf die jede Verweigerung zeigt.
   Der Rest ist eine Naht an G4-3 (Prozedurtexte).
3. **H151** — die Erklärung, auf der Gate 5 entscheidet, liegt ausserhalb des geschützten Bereichs;
   gemessen (`Write` darauf rc 0, gesenkte Schwelle macht rc 2 zu rc 0). Benannte Ausnahme nach
   DEC-0056 mit ihren drei Begrenzungen.
4. **H152** — eine nicht erklärte Verengungsoption führt zu Über-Verweigerung; auf der Zeile
   beantwortbar, beide Enden mit Stolperdraht.
5. **H153** — ein Läufername, den erst die Shell herstellt, passiert den billigen Vorfilter;
   gemessen (`pytest tools/` rc 2 gegen `R=pytest; $R tools/` rc 0). Benannte Ausnahme nach
   DEC-0056.
6. **`session_status.py` und `_routine.py` bleiben unverändert** (Befund N-2 der Nahttabelle). Der
   Plan sah den Fristen-Leser dort vor; gebaut ist er in `_kernel.run_gate`, weil ein Sitzungsstart
   nichts **verweigern** kann und AC-2 eine Verweigerung verlangt. `_kernel.py` war in der
   Nahttabelle des Auftrags **nicht** als geteilte Datei benannt (Befund N-1) — der Merge muss sie
   gegen die anderen Ströme prüfen.
7. **`tools/constitution_section_pins.json` + `docs/reviews/phase0-disposition.md`** sind eine
   Naht, die der Auftrag nicht nennt: jeder Strom, der einen gepinnten Text ändert, schreibt beide.
   Beim Merge müssen die Pins **einmal gemeinsam** neu geschrieben werden.
8. **`test_gate3_answers_before_its_registration_however_costly_the_line_is_to_judge`** ist auf
   diesem Host unter der Parallel-Last flatterhaft — und zwar **an der Basis genauso**: im Klon
   ausserhalb des Repos am Stand 75a00d1 einmal grün (3 passed) und einmal rot (5,34 s gegen 4,50),
   in meinem Baum zweimal rot (4,99 s / 4,76 s), und zwei Varianten „Basis + genau eine meiner
   Änderungen" ebenfalls rot (4,55 s / 4,58 s). Die Variable, die entscheidet, ist die Maschine,
   nicht die Änderung — genau die Klasse, die die Zusicherung des Tests selbst benennt (BUG-0033).
   **Ich habe das zuerst falsch als eigenen Befund gemeldet und korrigiere es hier.**

## 10. Suite-Läufe (nur die lesenden, DEC-0050)

| Lauf | Ergebnis |
|---|---|
| `.claude/hooks/test_gates.py -k "gate5 or declared_surface or narrowing_option or registration or each_gate_refuses"` | 40 passed, 1 failed (der Timing-Knoten aus Punkt 8), 139 s |
| `.claude/hooks/test_gates.py -k narrowing_option` | 2 passed, 16 s |
| `tools/test_hooks.py -k "test_scope or deadline… or qe_skill or mirror or window_exactly or typed_directory or invariant_scan or browser_smoke"` | 34 passed, 40 s |
| `tools/test_hooks.py -k "built_app or planted_violation_of_the_built or without_a_built_frontend or two_rules_a_build"` | 9 passed, 55 s |
| `tools/test_role_contracts.py test_context_budget.py test_repo_hygiene.py test_kit_neutrality.py` | 102 passed, 1 failed → behoben, danach `test_repo_hygiene.py -k pointer` 4 passed |
| `tools/test_shortening_net.py` | 34 passed, 2 failed = die Naht an G4-3 (Abschnitt 8) |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |

**Die volle Suite ist NICHT gelaufen** — sie ist ein Lieferkriterium und gehört in den Merge
(DEC-0050, fünf gemessene Brüche in Generation 3, ~5 h). Das ist genau die Regel, die dieser Strom
baut.

## 11. Übergabe

* **Vorläufiger VERSION-Stempel:** dev-team `2026.09.04-4`, office-team `2026.09.04-6`,
  research-team `2026.09.04-4` (`python tools/bump_kit_version.py`).
* **Patch:** `C:/Offline Repos/v2-testbed/_round-scratch/TSK-0121/stream-testgate.patch`,
  Arbeitsbaum-Diff **ohne** die `team-kits/*/VERSION`-Hunks.
* **Spiegel:** `gate_test_scope.py` sha256 `f3ace285…` ×3, `_kernel.py` sha256 `27fd0bc6…` ×3,
  `kit_browser_checks.py` sha256 `1a707745…` (dev + research; office liefert die Datei nicht aus).
* **Scratch:** alles unter `_round-scratch/TSK-0121/` (`rig/`, `proj/`, `pilotbase/`, `mutant/`,
  `basecheck/`). Kein Commit, kein Push, keine Installation in den globalen Speicher.
* **Wanduhr / Tokens:** erste Rig-Datei 2026-09-04 06:18, letzte Datei 2026-09-05 00:07 —
  **~17 h 50 min** von der ersten bis zur letzten Schreiboperation, darin **vier**
  Host-Abstürze mit vollständigem Wiederaufsetzen von der Platte (die Ausfall- und
  Wiedereinlesezeit ist darin enthalten und nicht getrennt gemessen). ~1,3 Mio Tokens.

---

# Nacharbeit nach Prüfung 1 (FAIL: B1, B2 blockierend; F3–F7)

Der Prüfbericht liegt unter `project_memory/staging/TSK-0121/verify-round-1.md`. Jeder Punkt unten
ist gebaut, gemessen und rot-zuerst belegt; das Rig ist dasselbe (`_round-scratch/TSK-0121/rig/`,
Klon `mutant/` ohne `.git`, binär gelesen und geschrieben).

## B1 — die Aufzählung entschied über etwas, das sie nie gemessen hat

**Was falsch war, mit der Messung des Prüfers und meiner eigenen Nachmessung.** Sieben der 21
erklärten „Verengungs"-Optionen verengen nichts. Ich habe das mit einer eigenen Sonde nachgemessen
(`rig/optprobe.py`): eine Drei-Test-Suite, deren Tests ihr Laufen in eine Datei schreiben — die
Zahl der gelaufenen Tests ist also gezählt und nicht aus pytest-Prosa geparst.

```
bare: 3 tests executed
NARROWS:  -k=alpha 1 · -m=slow 1 · --deselect=<node id> 2 · --ignore=<vorhandener Pfad> 0
          --ignore-glob=*probe* 0 · --collect-only 0 · --co 0 · --fixtures 0 · --markers 0
          --version 0 · --help 0
NARROWS NOTHING (3 von 3 liefen weiter):
          --lf · --last-failed · --ff · --failed-first · --nf · --new-first
          --sw · --stepwise · --sw-skip · --stepwise-skip · -k= · -m=
          --ignore=<nicht vorhandener Pfad> · --ignore-glob=*zzz*
          (Gegenprobe, nie erklärt: -v · --tb=short · --durations=3 · -x · -q)
```

**Gebaut:**

1. Die zehn Sortier-/Cache-Einträge sind aus `tools/test_surface.json` heraus. Über-Verweigerung
   ist die sichere Richtung, und H152 trägt sie.
2. `_narrowing_option` liest jetzt den **Wert**: `-k ""`, `-m ""`, `-k=` und `-m=` verengen nicht.
   Beide Hälften, byte-gleich.
3. Der zweite Stolperdraht fragt den **Läufer** statt die Liste:
   `test_every_declared_narrowing_option_really_makes_the_runner_run_fewer_tests` fährt die
   Drei-Test-Sonde mit und ohne jeden Eintrag und zählt die Tests, die wirklich liefen. Er verlangt
   ausserdem für jeden Eintrag einen Sondenwert (`probe_values`), sonst ist er rot — damit bleibt
   das Paar in beiden Richtungen vollständig.
4. Die vier falschen Prosa-Stellen sind korrigiert:
   `docs/POST_V2_WISHLIST.md` (Tabellenzeile **und** Langabschnitt H152 neu geschrieben — der Satz
   „sie lässt nie einen Volllauf durch" ist weg), `tools/test_surface.json`
   (`_options_that_narrow`), `.claude/hooks/gate_test_scope.py` (Kopf und Restklassen-Liste).
   **Neu benannt, weil fail-open:** eine ERKLÄRTE Option mit einem wohlgeformten Wert, der nichts
   trifft (`--deselect does::not::exist`, `--ignore=<nicht vorhandener Pfad>`), liest sich als
   Auswahl. Das zu entscheiden verlangt eine Sammlung — genau die Kosten, gegen die das Gate
   existiert. Steht als zweite Restklasse in H152.

**Rot zuerst (die Gegenprobe des Prüfers ist jetzt rot):**

| Wiederhergestellter Defekt | Roter Test | Ausgang |
|---|---|---|
| `--ff` wieder in der Erklärung | `test_every_declared_narrowing_option_really_makes_the_runner_run_fewer_tests` | RED |
| `--ff` wieder in der Erklärung | `test_gate5_refuses_a_full_run_carrying_only_an_ordering_or_cache_option` | RED |
| ein erklärter Eintrag ohne Sondenwert | `test_every_declared_narrowing_option_really_makes_the_runner_run_fewer_tests` | RED |
| Wert-Regel im Repo-Gate entfernt | `test_gate5_reads_an_empty_selector_value_as_no_selection` | RED |
| Wert-Regel im Kit-Gate entfernt | `test_gate_test_scope_reads_an_empty_selector_value_as_no_selection` | RED |

## B2 — `_covers` verglich Text statt Pfade

**Gemessen vor dem Fix**, im Arbeitsbaum, als echte Gate-Prozesse: die sechs Schreibweisen
`tools/.`, `tools/./`, `./tools/.`, `tools/../tools`, `..`, `tools/../../tools` und der **absolute**
Pfad waren alle **rc 0** — 7 failed von 8, bevor eine Zeile Code geändert war. Auf der Kit-Seite
dasselbe Bild am Piloten.

**Gebaut** (beide Hälften, byte-gleich):

* `_normalised` löst `.`/`..` mit `posixpath.normpath` auf (`posixpath` und nicht `os.path`, weil
  der Vergleich auf Vorwärts-Schrägstrichen läuft);
* `_is_absolute` kennt drei Formen statt einer — POSIX-Wurzel, Windows-Laufwerk, UNC-Freigabe;
  `posixpath.isabs` beantwortet nur die erste, und die mittlere ist genau die Schreibweise, in die
  Gate 1 jeden Aufrufer drängt („Remedy: spell the path absolutely");
* ein absolutes Wort wird gegen `data["cwd"]` relativiert; ein Wort, das sich **nicht** relativieren
  lässt (anderes Laufwerk, kein `cwd` im Payload), **deckt** — fail-closed;
* `.`, `..` und alles darüber decken, was der Docstring vorher nur versprochen hatte.

**Rot zuerst:** `normpath` entfernt → RED (Repo und Kit); die Relativierung entfernt → RED;
„ein Vorfahr deckt" entfernt → RED; fail-closed auf `True`→`False` gedreht → RED. Dazu ein
Gegentest, dass eine Auswahl in jeder dieser Schreibweisen weiter passiert.

## F3 — der Docstring behauptete, die wörtliche AC-2 zu erfüllen

`start_the_deadline` sagt jetzt, was gebaut ist, in der vom Lead angenommenen Lesart: **jeder**
Aufruf hat ein Fenster, ob die Registrierung eines nennt oder nicht (ein schweigender Eintrag wird
vom gemessenen Vorgabefenster getötet); das Budget wird aus beidem abgeleitet; ein Fenster, das
das Gate nicht einhalten kann, wird verweigert. Und ausdrücklich dazu, was **nicht** gebaut ist:
ein Eintrag ohne Fenster wird nicht verweigert — er ist für ein Gate ohne eigene Kindgrenze die
richtige Registrierung, und ihn zu verweigern hiesse jeden ausgelieferten Kit-Haken zu verweigern.

## F4 — `registered_window` widersprach seinem eigenen Docstring, Richtung ALLOW

Aus „ein `None` verwirft alles" ist „der kleinste **genannte** Wert antwortet, `None` zählt als das
Vorgabefenster und ist damit nie der kleinste" geworden. Der Docstring trägt die Messung, die den
Fehler zeigt (ein Eintrag mit 1,0 s plus ein schweigender → kein Fristen-Refusal, Budget 558,5 s).

**Rot zuerst:** alte Fassung wiederhergestellt → `test_the_smallest_NAMED_window_answers_when_one_entry_states_none`
RED. Gegenrichtung als eigener Test: zwei schweigende Einträge lassen das Gate weiter entscheiden.

## F5 — „ein Gate, das seine Regel nicht lesen kann, verweigert" galt nur für einen Syntaxfehler

`declaration()` verweigert jetzt jede Gestalt, die ein JSON-Parser annimmt und dieses Gate nicht
benutzen kann: kein Objekt, oder ein `surfaces`, das keine Liste ist. `{}` bleibt bewusst ein
ALLOW — ein Objekt ohne `surfaces` erklärt keine Fläche, das ist der abwesende Fall. Der Test
fährt jetzt acht Gestalten statt einer.

**Rot zuerst:** beide neuen Verweigerungen einzeln entfernt → RED.

## F6 — der QS-Block zerschnitt einen Bestandssatz

Der eingefügte Block steht jetzt hinter „collect the result before issuing it (…)", also nach dem
Ende des Satzes; „…then grep the report FILE for details…" ist wieder in einem Stück. Nur dev-team
trägt eine `quality-engineer/SKILL.md`; die anderen beiden Kits haben diese Rolle nicht.

## F7 — zwei Sätze, die diese Runde selbst überholt hatte

* `tools/test_hooks.py` (`_own_child_limit`): aus „nothing enforces it" ist die Korrektur mit Datum
  geworden — `_kernel.start_the_deadline` leitet das Budget ab und verweigert; was ausserhalb
  beider bleibt, ist ein einzelner Aufruf nach C.
* `tools/provider_observations.json` → `what_follows_for_the_kits`: aus „what no kit hook does" ist
  „that gap is closed since 2026-09-05 (TSK-0121)" geworden, mit dem, was weiterhin unbegrenzt ist.
* `_kernel.py`s Kopfkommentar **zitiert** den Satz nicht mehr, sondern **zeigt** auf die Messung als
  Anlass.

## Ein Befund, den diese Nacharbeit selbst erzeugt und selbst gefunden hat

`import posixpath` / `import re` standen im **Präambel-Block** des Kit-Gates. Die Präambel muss
byte-gleich zu `_kernel.GATE_PREAMBLE` sein, weil `tools/test_context_budget.py::test_no_shipped_hook
_refuses_outside_the_one_funnel` sie vor dem AST-Lauf abzieht — mit den zwei Zeilen darin passte
sie nicht mehr, und das `sys.exit(2)` der Präambel wurde als Verweigerung ausserhalb des einen
Trichters gemeldet (3 failed). Die beiden Importe stehen jetzt hinter der Präambel; die Suite ist
grün (42 passed).

## Läufe der Nacharbeit (nur die lesenden)

| Lauf | Ergebnis |
|---|---|
| `.claude/hooks/test_gates.py -k "gate5 or declared_surface or narrowing_option or empty_selector or ordering_or_cache or as_a_path or absolute_target or however_it_is_spelled or registration_is_the_one"` | 42 passed, 82 s |
| `tools/test_hooks.py -k "test_scope or deadline… or as_a_path or absolute_target or empty_selector or smallest_NAMED or two_silent or mirror"` | 45 passed, 59 s |
| `tools/test_role_contracts.py tools/test_repo_hygiene.py` | 55 passed, 99 s |
| `tools/test_context_budget.py` | 42 passed, 30 s |
| `tools/test_kit_neutrality.py` | grün (im Sammellauf) |
| `tools/test_shortening_net.py` | 34 passed, 2 failed = die Naht an G4-3 (unverändert) |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| Mutationen der Nacharbeit | **13 von 13 RED** |

## Stand der Übergabe nach der Nacharbeit

* **VERSION (vorläufig):** dev `2026.09.05-2`, office `2026.09.05-2`, research `2026.09.05-2`.
* **Spiegel:** `gate_test_scope.py` sha256 `42732894…` ×3, `_kernel.py` sha256 `13e47244…` ×3,
  `kit_browser_checks.py` sha256 `1a707745…` (dev = research; office liefert die Datei nicht aus).
* **Naht-Korrektur des Prüfers übernommen:** `_kernel.py` ist **keine** Naht — TSK-0122 verbietet
  `team-kits/*/hooks/_*.py`, TSK-0123/0125 verbieten `team-kits/*/hooks/**`. Mein Befund N-1 ist
  damit gegenstandslos und wird zurückgezogen.
* **Offen und unverändert:** die zwei roten Verfassungstests (Naht an G4-3, Abschnitt 8), H151 und
  H153, sowie die zweite Restklasse von H152 (Wert trifft nichts).

---

# Nacharbeit nach Prüfung 2 (FAIL: B2′ blockierend; B2″, B1′, F8, F9)

Bericht: `project_memory/staging/TSK-0121/verify-round-2.md`. AC-2, AC-3, AC-4 und die Pflichten
5–7 sind dort PASS; AC-1 scheiterte an der Bezugsbasis des Pfadlesers, an der Identitätsklasse und
an einer Optionsschreibweise. Alles unten ist gebaut, gemessen und rot-zuerst belegt.

## B2′ — der Leser relativierte gegen `cwd`, die erklärten Wurzeln sind repo-relativ

Das ist der blockierende Befund, und er trifft den Normalfall dieses Projekts: eine Shell, die eine
Ebene über dem Repo steht (Worktree, Scratch), schrieb den absoluten Pfad — den, zu dem Gate 1 in
**jeder** Verweigerung auffordert — und fuhr die mit 3465 s erklärte Fläche bei **rc 0**.

**Gebaut:** `decide()` reicht die **Repo-Wurzel** (`_harness.repo_root(data)`, Kit:
`_kernel.find_repo_root`) als Basis durch; ein **relatives** Wort wird zuerst an `cwd` gehängt und
dann gegen die Repo-Wurzel beurteilt. Beide Hälften, byte-gleich gespiegelt.

**Rot zuerst:** die Anhängung an `cwd` entfernt →
`test_gate5_measures_the_declared_root_against_the_REPO_and_not_against_the_shells_cwd` RED,
`test_gate_test_scope_measures_against_the_PROJECT_root_and_not_the_shells_cwd` RED.

## B2″ — der Leser entschied auf Text, wo dieses Repo die Frage schon als Eigenschaft beantwortet hat

Gemessen vom Prüfer gegen den echten Läufer: `pytest TOOLS`, `Tools`, `C:tools` und eine Junction
sammeln dieselben 4627 Knoten und waren hier **rc 0**. `_harness` vergleicht seit TSK-0008 die
**Identität** des tiefsten existierenden Vorfahren (`(st_dev, st_ino)`); Gate 5 hatte einen eigenen
Text-Normierer gebaut und davon nichts geerbt.

**Gebaut, und zwar geschlossen statt nur aufgeschrieben:**

* **Repo-Hälfte:** `_covers` benutzt jetzt `_harness.under` — **eine** Antwort auf **eine** Frage,
  keine zweite Umsetzung.
* **Kit-Hälfte:** ein Kit wird ohne `_harness` ausgeliefert, also steht die Eigenschaft dort ein
  zweites Mal (`_identity`, `_anchored`, `_ancestor_identities`, `under`). Das ist im Docstring
  ausdrücklich gesagt — samt dem, was sie **nicht** ist (kein `probe`-Deadline-Wrapper; die Schranke
  ist hier der Wachhund aus `_kernel.start_the_deadline`, der eine nicht antwortende Platte in eine
  **Verweigerung** statt in einen Kill verwandelt).
* **Gegen Drift gepinnt:** `tools/test_hooks.py::test_the_kit_reader_and_the_workshops_agree_on_what_one_place_is`
  importiert **beide** Leser und ruft sie über dieselben Schreibweisen auf — Wurzel, Grossschreibung,
  Junction, Knoten-Id, Geschwister, Vorfahr. Zwei Umsetzungen einer Frage sind die Form, an der
  dieses Repo wiederholt bezahlt hat; deshalb ist der Pin gebaut und nicht versprochen.

**Drei Ausgänge statt zwei**, und der dritte ist F8: das Wort ist die Wurzel oder ein Vorfahr
(deckt) · es liegt INNERHALB des Repos und ist nicht die Wurzel (Auswahl) · es lässt sich gegen
dieses Repo **gar nicht platzieren** (anderes Laufwerk, UNC, `/c/…`, laufwerksrelativ, kein `cwd`
im Payload) → **deckt, fail-closed, mit eigenem Satz**.

**Rot zuerst:** `_harness.under` durch Textvergleich ersetzt → RED (Repo);
`under` in der Kit-Hälfte durch einen Präfix-Textvergleich ersetzt → RED (Kit, und der Drift-Pin
ebenfalls RED); den laufwerksrelativen Zweig entfernt → RED.

**Ein Nebenbefund, den die Umstellung sichtbar gemacht hat:** `tools/../../tests` ist **nicht** die
Wurzel — zwei Ebenen hoch und wieder runter landet auf einem gleichnamigen Verzeichnis ausserhalb.
Der Textleser hielt es für die Wurzel, der Identitätsleser sagt „nicht platzierbar". Die
Schreibweise ist aus der „meint die Wurzel"-Liste heraus und steht jetzt im F8-Fall — in beiden
Hälften.

## B1′ — dieselbe Option zweimal, die letzte leer

`argparse` nimmt die **letzte** Angabe; der Leser gab beim **ersten** Treffer zurück. Gemessen an
der Drei-Test-Sonde: `-k alpha -k ""` und `-k alpha -k=` fahren drei von drei Tests, das Gate war
**rc 0**. Gebaut: das letzte Vorkommen je Options-NAME entscheidet, in beiden Hälften. Die
Gegenrichtung (`-k "" -k alpha` verengt wirklich) ist ein eigener Test.

**Rot zuerst:** „erster Treffer" wiederhergestellt → `…lets_the_LAST_occurrence_of_an_option_decide`
RED in beiden Hälften.

## F8 — die fail-closed-Verweigerung behauptete etwas Falsches über die Zeile

Der nicht platzierbare Zweig hat jetzt seinen eigenen Satz („this line could not be placed against
this repository / against this project: %r names no position this gate can compare with the
declared test surface …"), samt eigenem Remedy. Der Test verlangt beides: rc 2 **und** dass der
gewöhnliche Satz („runs the WHOLE declared test surface") **nicht** darin steht.

**Rot zuerst:** den Zweig deaktiviert → `…says_so_when_it_cannot_place_a_target_at_all` RED in
beiden Hälften.

## F9 — `tools/provider_observations.json` war ganzflächig neu eingerückt

Zurückgenommen: die Datei ist byte-für-byte die von 75a00d1, und die eine geänderte Zeichenkette
ist als Text hineingetauscht. `git diff --numstat` → **1/1**, mit und ohne `--ignore-all-space`.

## Ein Befund, den diese Nacharbeit selbst erzeugt und selbst gefunden hat

Der Docstring der Kit-Hälfte nannte den Drift-Pin unter `.claude/hooks/test_gates.py`, gebaut ist
er in `tools/test_hooks.py`. `tools/test_repo_hygiene.py::test_every_test_pointer_this_repo_writes
_resolves` — der Zeiger-Prüfer dieses Repos — ist darauf rot geworden; der Zeiger ist korrigiert
und der Prüfer wieder grün (4 passed).

## Läufe der Nacharbeit (nur die lesenden, einer nach dem anderen)

| Lauf | Ergebnis |
|---|---|
| `.claude/hooks/test_gates.py -k "gate5 or …narrowing… or …path… or …absolute… or cannot_place or REPO_and_not or asks_the_filesystem or LAST_occurrence or registration_is_the_one"` | **49 passed**, 117 s |
| `tools/test_hooks.py -k "test_scope or …deadline… or qe_skill or mirror or reader_and_the_workshops"` | **51 passed**, 81 s |
| `tools/test_context_budget.py` + `tools/test_repo_hygiene.py` | 66 passed, 1 failed → Zeiger korrigiert, danach `-k pointer` **4 passed** |
| `tools/test_shortening_net.py` + `tools/test_kit_neutrality.py` | **40 passed, 2 failed** = die Naht an G4-3, unverändert |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| Mutationen der Nacharbeit | **10 von 10 RED** |

## Stand der Übergabe nach Nacharbeit 2

* **VERSION (vorläufig):** dev / office / research je `2026.09.05-4`.
* **Spiegel:** `gate_test_scope.py` sha256 `800db1a0…` ×3, `_kernel.py` `13e47244…` ×3,
  `kit_browser_checks.py` `1a707745…` (dev = research; office liefert die Datei nicht aus).
* **H152 zum zweiten Mal auf den gemessenen Stand gebracht:** die Sortier-/Cache-Klasse (Prüfung 1)
  und die Doppel-Options-Klasse (Prüfung 2) sind **geschlossen**; offen und fail-open bleibt genau
  eine Klasse — eine erklärte Option mit einem wohlgeformten Wert, der nichts trifft. Die
  Identitätsklasse ist **geschlossen** und steht deshalb nicht mehr als Restklasse dort, sondern
  als gebaute Eigenschaft mit ihrem Drift-Pin.
* **Unverändert offen:** die zwei roten Verfassungstests (Naht an G4-3), H151, H153.

---

# Abschluss nach Prüfung 3 (FAIL ohne blockierenden Befund: F10, F11)

Bericht: `project_memory/staging/TSK-0121/verify-round-3.md`. AC-1 ist im Verhalten PASS, AC-2/3/4
PASS; Pflicht 5 scheiterte an zwei Aufschreib-/Wortlautpunkten.

## F10 — jede Suite ausserhalb des Repos war rc 2, und das traf das eigene Rot-zuerst-Rig

**Was falsch war.** Der fail-closed-Zweig hielt **jeden** Ort ausserhalb der Repo-Wurzel für nicht
platzierbar. Gemessen: `pytest "<scratch>/pytestprobe/suite"` **und** eine einzelne Datei darin —
also eine Auswahl — kamen als rc 2 zurück. Das ist genau die Zeile, die `CLAUDE.md` für **jedes**
Rot-zuerst-Rig vorschreibt („den Defekt in einem Klon **ausserhalb** des Repos wiederherstellen,
Rot sehen"): mit registriertem Gate 5 hätte der Apparat jedem Umsetzer und jedem Prüfer sein
eigenes Messrig verweigert, sobald es durch das Bash-Werkzeug läuft.

**Gebaut (Entscheidung des Leads: verengen, nicht bloss aufschreiben).** Ein Ort, den der Leser
FINDEN kann und der nicht dieses Repo ist, ist entscheidbar **nicht** die erklärte Fläche, also
eine Auswahl (rc 0). „Nicht platzierbar" bleibt für: laufwerksrelativ, `/c/…`, ein nicht
eingehängtes Laufwerk, eine UNC-Freigabe, die niemand bedient, und ein Payload ohne `cwd`.

Die Eigenschaft, die beides trennt, ist gebaut und nicht geraten: **der tiefste existierende
Vorfahr entscheidet, und eine Dateisystem-Wurzel zählt nicht als einer** (`_placeable`, Kit:
`placeable`). Eine Scratch-Suite wird im ersten Schritt gefunden; `/c/…`, ein fehlendes Laufwerk
und eine tote Freigabe klettern bis zur Wurzel, ohne etwas zu finden.

**Die Behauptung, auf der die Verengung ruht, ist gemessen und nicht argumentiert:** ein Link von
aussen IN die erklärte Fläche wird vom **Identitätsleser** beantwortet, bevor die Frage nach
„aussen" überhaupt gestellt wird — eine Junction auf die Fläche ist **rc 2**, in beiden Hälften
(`test_gate5_still_sees_a_link_from_outside_into_the_declared_surface`,
`test_gate_test_scope_still_sees_a_link_from_outside_into_the_declared_surface`).

**Rot zuerst, 5 von 5 RED:** die Verengung deaktiviert → ein Rig-Lauf ausserhalb wird verweigert
(RED, beide Hälften); die Wurzel als „Ort" zugelassen → `/c/…` und die tote Freigabe werden zur
Auswahl (RED); den Identitätsleser vor der Verengung deaktiviert → die Junction von aussen in die
Fläche passiert (RED, beide Hälften).

**Nebenbefund derselben Umstellung:** `tools/../../tools` ist jetzt eine **Auswahl** statt „nicht
platzierbar" — es landet auf einem Ort, den der Leser findet, und der ist nicht dieses Repo. Die
Schreibweise ist entsprechend umsortiert, in beiden Hälften.

**H153 trägt die Restliste** mit ihrer gemessenen Kette: der Vorfilter (a) und der wirklich nicht
platzierbare Ort (b), jede Schreibweise einzeln gemessen.

## F11 — eine halbe Behauptung im Kit-Docstring

„`_harness` … case-folds the tail" stand dort als Unterschied zur Kit-Fassung. Gemessen: **beide**
rufen `os.path.normcase` an denselben zwei Stellen. Der Halbsatz ist gestrichen; der einzige
wirkliche Unterschied — der `probe`-Deadline-Wrapper — bleibt und ist richtig benannt. Der Satz
sagt jetzt ausdrücklich, dass die Faltung in **beiden** steckt und dass eine frühere Fassung sie
fälschlich als Unterschied geführt hat.

## Läufe des Abschlusses

| Lauf | Ergebnis |
|---|---|
| `.claude/hooks/test_gates.py -k "gate5 or … or lies_outside or link_from_outside or registration_is_the_one"` | **52 passed**, 112 s |
| `tools/test_hooks.py -k "test_scope or … or reader_and_the_workshops or lies_outside or link_from_outside"` | **53 passed**, 74 s |
| `tools/test_repo_hygiene.py -k "pointer or hole"` | **6 passed**, 62 s |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| Mutationen des Abschlusses | **5 von 5 RED** |

---

# (g) — die Zeile für das Generationen-Logbuch

**Strom G4-1 / TSK-0121 — „Test discipline and hook hygiene" (PR-0004, AC-1..AC-4), Umsetzer Opus.**

| Feld | Wert |
|---|---|
| **Spanne** | 2026-09-04 06:18 → 2026-09-05 02:33 ≈ **20 h 15 min** von der ersten bis zur letzten Schreiboperation |
| **davon Ausfall** | **vier Host-Abstürze** mit vollständigem Wiederaufsetzen von der Platte. Ursache gemessen und abgestellt (16-Brenner-Lastrig eines Nachbarstroms, TSK-0125). Die Ausfall- und Wiedereinlesezeit ist in der Spanne enthalten; **gearbeitet** wurde davon grob **12–13 h** (die Differenz ist Stillstand plus je ~10–20 min Wiedereinlesen) — geschätzt aus den Abständen der Dateizeiten, **nicht** mit einer Uhr gemessen, und deshalb hier als Schätzung markiert |
| **Runden** | 1 Erstbericht · 2 Nacharbeiten + 1 Abschluss · **3 Prüfungen** (FAIL blockierend / FAIL blockierend / FAIL ohne Blocker) + die kurze Runde 4 auf F10/F11 |
| **Tokens** | ≈ **1,45 Mio** Umsetzer über alle vier Runden (Erstbau ≈ 1,0 · Nacharbeit 1 ≈ 0,2 · Nacharbeit 2 ≈ 0,15 · Abschluss ≈ 0,1) |
| **Befunde je Prüfung** | Runde 1: 2 blockierend (B1, B2) + F3–F7 · Runde 2: 1 blockierend (B2′) + B2″, B1′, F8, F9 · Runde 3: F10, F11 · **alle geschlossen** |
| **Rot-zuerst-Messungen** | **52** Mutationen, jede im Klon ausserhalb des Repos, **52 RED** (14 Erstbau Repo · 18+1 Erstbau Kit/AC-2 · 6 AC-3 · 13 Nacharbeit 1 · 10 Nacharbeit 2 · 5 Abschluss). Zwei davon sind eigene Befunde, die der Umsetzer selbst gefunden hat: ein Test, der grün blieb (Knopfname an zwei Stellen), und die Präambel, die nicht mehr byte-gleich war |
| **Eigene Befunde am eigenen Bau** | 6: die `-m`-Grenze (rc 0 auf der dokumentierten Volllaufzeile) · der flatterhafte Wachhund-Test (rc 0 unter einem nicht einhaltbaren Fenster) · die 3,05-s-Speicherlesung auf jeder Shell-Zeile · die Präambel-Verschiebung (`test_no_shipped_hook_refuses_outside_the_one_funnel`) · der Zeiger auf die falsche Suite (`test_every_test_pointer_this_repo_writes_resolves`) · die falsche Ursachenzuschreibung beim `os.execv`-Rig, im Kommentar korrigiert |
| **Nähte übergeben** | an **G4-3**: zwei rote Verfassungstests (`test_every_registered_hook_is_anchored_in_its_kits_constitution`, `test_the_inventory_the_constitution_presents_is_the_registrations_it_ships`) — die Änderung ist **ein Wort je Kit** in der `starts:`-Zeile, wörtlich in Abschnitt 8; **empfangen** von G4-3: der Ereignis-Auslösesatz **H158** |
| **Nähte erwartet beim Merge** | `.claude/hooks/test_gates.py` (eigener Block + 4 Bestandsstellen), `tools/test_hooks.py` (eigener Block), `tools/test_surface.json` (neu), `tools/constitution_section_pins.json` + `docs/reviews/phase0-disposition.md` (Pins **einmal gemeinsam** neu schreiben), `docs/POST_V2_WISHLIST.md` (H151–H153, G4-2 migriert sie mit), `team-kits/*/VERSION`. **Keine Naht:** `_kernel.py` (N-1 zurückgezogen), `session_status.py`/`_routine.py` (unberührt) |
| **Löcher** | **H151** OFFEN, benannte Ausnahme (DEC-0056): die Erklärung liegt ausserhalb des geschützten Bereichs · **H152** OFFEN, **eine** Restklasse: eine erklärte Option mit wohlgeformtem Wert, der nichts trifft (Sortier-/Cache-, Leerwert-, Doppel-Options- und Identitätsklasse sind **geschlossen**) · **H153** OFFEN, zwei benannte Ausnahmen: der Vorfilter und der wirklich nicht platzierbare Ort |
| **Merge-Zeilen** | Gate 5 in `.claude/settings.json` (`Bash\|PowerShell`, `timeout: 120`) · der Kit-Haken in den drei `settings/settings.json` (**ohne** `timeout`, Begründung Abschnitt 5) · die `gate_test_scope`-Zeile in `hooks/ENFORCEMENT.md` ×3 · `tools/test_surface.json` · der Prozedur-Block in `skills/quality-engineer/SKILL.md` · die zwei roten `shortening_net`-Tests werden von G4-3s Verfassungen aufgelöst |
| **Stempel (vorläufig)** | dev / office / research je `2026.09.05-5` |
| **Spiegel** | `gate_test_scope.py` `8e5c8dff…` ×3 · `_kernel.py` `13e47244…` ×3 · `kit_browser_checks.py` `1a707745…` (dev = research; office liefert die Datei nicht aus) |

---

# Abschluss nach Prüfung 4 (F11 PASS, F10 PASS; ein nicht blockierender Befund N1)

Bericht: `project_memory/staging/TSK-0121/verify-round-4.md`.

## N1 — der Wächter der Behauptung, auf der die Lead-Entscheidung ruht, konnte nicht scheitern

**Was falsch war.** `prd_repo` **IST** `tmp_path` (die Fixture gibt es zurück). Beide Kit-Tests, die
etwas über „ausserhalb des Projekts" behaupten, legten ihr Objekt nach `tmp_path / …` — also
**innerhalb**. Der Prüfer hat das mit der Mutation gemessen, gegen die der eine Test gebaut ist:
die Aussenfrage vor den Identitätsleser gezogen — die echte Kit-Hälfte liess am Piloten eine
Junction von aussen in die erklärte Fläche durch (**rc 0**), und der Test blieb **grün**. Der
Zwilling der Repo-Hälfte (Link unter `outside_the_home_directory`) wurde unter derselben Mutation
rot. Der ausgelieferte Code war richtig; der Wächter war es nicht.

**Gebaut.** `_provably_outside(prd_repo, tmp_path, name)` legt das Verzeichnis nach
`tmp_path.parent` und **behauptet die Nicht-Enthaltenheit nicht, sondern prüft sie** — mit
`os.path.commonpath` gegen den realen Projektpfad. Beide Tests benutzen es: der Junction-Test und
der, den die Nebenbeobachtung nennt (`…lets_a_rig_run_a_suite_that_lies_outside_the_project`, der
bis dahin nur von seinem vierten Fall gerettet wurde).

**Rot zuerst — und hier ist eine Messung über meine eigene Mutation, die ich benenne, statt sie
wegzulassen.** Mein erster Mutationsversuch schrieb
`if placeable(here) and not under(here, project_root): return False, None` vor den Identitätsleser.
Der bleibt **grün** — zu Recht: die Zusatzbedingung neutralisiert den Defekt, weil eine Junction von
aussen genau *nach innen* auflöst. Erst die schlichte Umstellung, die der Prüfer beschreibt
(`if placeable(here): return False, None` **vor** `if under(target, here)`), ist der Defekt:

| Mutation | Knoten | Ausgang |
|---|---|---|
| Aussenfrage vor dem Identitätsleser, Kit-Hälfte | `tools/test_hooks.py::test_gate_test_scope_still_sees_a_link_from_outside_into_the_declared_surface` | **RED** (vorher grün) |
| dieselbe Umstellung, Repo-Hälfte | `.claude/hooks/test_gates.py::test_gate5_still_sees_a_link_from_outside_into_the_declared_surface` | **RED** |

## Läufe des Abschlusses

| Lauf | Ergebnis |
|---|---|
| `tools/test_hooks.py -k "test_scope or reader_and_the_workshops or lies_outside or link_from_outside"` | **39 passed**, 34 s |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |
| Mutationen | **2 von 2 RED** (plus eine dritte, die als untaugliche Mutation benannt ist) |

**Nachtrag zur (g)-Zeile:** Rot-zuerst-Messungen jetzt **54** (52 + 2), Runden: 1 Erstbericht,
2 Nacharbeiten + 2 Abschlüsse, **4 Prüfungen** (FAIL / FAIL / FAIL ohne Blocker / ein nicht
blockierender Befund) plus die kurze Runde 5 auf N1. Stempel unverändert `2026.09.05-5` in allen
drei Kits — `bump_kit_version.py` meldet für office und research „unchanged", weil sich in dieser
Runde nur eine Testdatei geändert hat, die in keinen Kit-Hash eingeht.
