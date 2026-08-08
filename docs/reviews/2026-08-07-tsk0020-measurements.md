# Messprotokoll TSK-0020 (2026-08-07)

Fortsetzung von `docs/reviews/2026-08-07-tsk0018-measurements.md` fuer die Migrationslinie. Dieses
Dokument traegt die Ketten zu den beiden blockierenden Befunden der Pruefung von TSK-0018 (F1: der
Leser unter der Schleife faengt eine Aufzaehlung; F2: der Vorlauf der Schleife zaehlt ebenfalls auf)
und zu den Resten F3 bis F9.

Es enthaelt keine Behauptung ohne Messung. Wo etwas anders ausfiel als im Auftrag beschrieben,
steht das ausdruecklich da (Abschnitt 7).

## Wie gemessen wurde

- **Echte Hook-Prozesse.** Jede `rc`-Zeile ist ein `subprocess`-Start des ausgelieferten
  `team-kits/dev-team/hooks/gate_memory_complete.py` mit JSON auf `stdin`, gegen ein
  Projektverzeichnis **ausserhalb** dieses Repos, mit einem gueltigen Wurzel-Item (sonst steht das
  Gate vor der ersten Anforderung still und jede Messung waere leer). `2` = Verweigerung,
  `0` = Durchlass.
- **Vorher/Nachher aus demselben Skript.** „vorher" ist der Stand vor dieser Runde, „nachher" der
  dieser; dieselbe Datei, dieselbe Zeile, derselbe Prozessaufruf.
- **Mutationen in einem Klon ausserhalb des Repos** (`C:\tmp-harness-r20`, `team-kits` + `tools` +
  `.git`): jeder gebaute Zweig einzeln zurueckgedreht, der zugehoerige Test darin gefahren
  (Abschnitt 5).

## 1. F1 -- ein Dokument in der Kodierung, die ein Windows-Editor zurueckschreibt

Kit-Dokument `project_memory/old_procs.yaml` mit einem V1-Datensatz (`PROC-0001`, `status: ACTIVE`)
und einem Umlaut im Titel, in vier Kodierungen als **Bytes** geschrieben.

| Kodierung | Merge vorher | `validate` vorher | Merge nachher | `validate` nachher |
|---|---|---|---|---|
| UTF-8 | rc 2 (Datensatz) | rc 1, Befund | rc 2 (Datensatz) | rc 1, Befund |
| UTF-8 mit BOM | rc 2 (Datensatz) | rc 1, Befund | rc 2 (Datensatz) | rc 1, Befund |
| **UTF-16 mit BOM** | **rc 2 als „internal error", Traceback, ohne Dateinamen** | **rc 1, nur eine Codec-Zeile, kein Befund** | **rc 2 (Datensatz gefunden)** | **rc 1, Befund** |
| **ANSI (cp1252) mit Umlaut** | **dasselbe** | **dasselbe** | **rc 2, Dateiname genannt, kein Traceback** | **rc 1, Befund `NOT SEARCHED`** |

Der Trockenlauf **warf** in beiden fetten Zeilen vorher `UnicodeDecodeError` aus `build_plan`
heraus; nachher liest er UTF-16 und nennt ANSI unter `UNREADABLE` (Plan nicht ausfuehrbar).

Zwei Mechanismen, und beide sind Eigenschaften statt Listen:

- **Was einen Lesevorgang beendet, ist keine Liste, die dieses Modul fuehrt.** `_read_document`
  fing `(OSError, yaml.YAMLError)`; `UnicodeDecodeError` ist ein `ValueError` und damit keines von
  beiden. Der Weg dorthin ist die Abhilfe, die die Nachbarverweigerungen selbst empfehlen (Datei
  ausserhalb der Sitzung reparieren).
- **Die Kodierungsfrage gehoert dem YAML-Leser.** Die Bytes gehen unveraendert an
  `yaml.safe_load`; ein YAML-Stream erklaert seine Kodierung per BOM. Deshalb liest UTF-16 jetzt,
  und was kein Stream ist, kommt als `ReaderError` mit dem stoerenden Byte zurueck -- benannt,
  einzeilig, ohne Pfad.

Rote Tests ohne den Fix: `test_a_kit_document_in_the_encoding_a_windows_editor_writes_is_named_not_a_traceback`,
`test_the_readers_contract_holds_for_an_empty_document_and_for_every_failure`.

## 2. F2 -- derselbe V1-Datensatz an sieben Orten

Ein Zustand je Ort, `PROC-0001` identisch, gemessen mit Trockenlauf und Validator.

| Ort | Trockenlauf vorher | Validator vorher | nachher (beide) |
|---|---|---|---|
| `old_procs.yaml` | Datensatz | Befund | unveraendert |
| `sub/old_procs.yaml` | Datensatz | Befund | unveraendert |
| `old_procs.yml` | Datensatz | Befund | unveraendert |
| `old_procs.json` | `NOT SEARCHED` | **stumm** | beide nennen ihn |
| `old_procs.yaml.bak` | `NOT SEARCHED` | **stumm** | beide nennen ihn |
| `.legacy/old_procs.yaml` | `NOT SEARCHED` | **stumm** | beide nennen ihn |
| `staging/PR-0001/old_procs.yaml` | **stumm** | **stumm** | beide nennen ihn |

**Der Auftrag sagt „zwei gemeldet, fuenf stumm"; gemessen sind es drei und vier** -- und der
Vorschlagsbereich war, anders als der Auftrag sagt, auch im **Trockenlauf** stumm: `_dotted_documents`
verlangte einen gepunkteten Pfad, `documents()` schliesst `staging/` aus, also fiel er durch beide.

Der Vorlauf ist jetzt **eine** Antwort fuer beide Leser: `migrate.search_coverage` gibt **jeder**
Datei unter der Zustandswurzel genau ein Verdikt (`searched`, `unsearched`, `kernel`, `machinery`).
Ein Ueberspringen, das nichts meldet, muss als `kernel` oder `machinery` **hingeschrieben** werden,
vor beiden Lesern, statt ein `continue` in einem von ihnen zu sein.

**Was der Validator daraus macht, und was nicht:** die vier unsearched-Klassen sind **Deckung**
(`report.record_scan_coverage`, gedruckt von `validate`, getragen von `doctor`) und **kein Befund**.
Grund, gemessen: das Forschungs-Kit liefert **27** Dateien unter `templates/project_memory/` aus,
die weder YAML noch gepunktet sind (`README.md`, `product/masterplan.md`, `reports/assets/**`,
zwei Report-Vorlagen) -- ein Befund
darueber waere in jedem Projekt dauerhaft und unaufloesbar, als Fehler ein Merge, den kein Projekt je
besteht. Was das offenlaesst, steht in Abschnitt 7.

Roter Test ohne den Fix: `test_the_dry_run_and_the_validator_answer_the_same_about_every_file`.

## 3. Die Reste

| Rest | vorher | nachher | roter Test |
|---|---|---|---|
| Der Grund nennt keinen Pfad | absoluter Pfad, mehrzeilig, im Befund zweimal | einzeilig, Pfad durch `this document` ersetzt | `…readers_contract_holds…` |
| „genau eines von zwei Ergebnissen ist leer" | falsch fuer ein LEERES Dokument (beide sind `None`) | Vertrag ueber den LESEVORGANG, gemessen | dito |
| Der Docstring zaehlt drei Aufrufer | vier (der ungezaehlte verwarf den Grund) | fuenf, aus den Aufrufstellen gelesen | `test_the_readers_docstring_names_every_caller_it_has` |
| Eine unparsbare Wand ist von einer leeren nicht unterscheidbar | beide `top-level keys: -` | `NOT READ: <Grund>` | `test_a_wall_that_does_not_parse_is_not_printed_as_a_wall_with_nothing_in_it` |
| Die Rahmung nennt die ausgefallene Pruefung | `NOT SEARCHED for V1 backlog records: …` | Ursache zuerst, Pruefung danach | `test_a_broken_document_says_what_broke_before_it_says_which_check_it_took_down` |
| Der Idempotenz-Scan uebersprang stumm | `continue` -> Datensatz waere ein zweites Mal importiert worden | benannt, Plan nicht ausfuehrbar | `test_an_unreadable_item_refuses_the_run_instead_of_importing_its_record_again` |

Zum vorletzten: `project_config.yaml` mit **einem** YAML-Tippfehler sperrt Merge und Push -- die
Richtung ist richtig (unbekannt ist nicht leer), die Meldung sagt jetzt zuerst, dass die Datei nicht
lesbar ist, und die Abhilfe nennt **UTF-8**, weil genau das der Weg zurueck aus Abschnitt 1 ist.

## 4. Die Pfadkomposition

`ProjectState` besitzt vier Verzeichnisbauer. Gezaehlt mit einem AST-Leser ueber `team-kits/kernel/*.py`
(`os.path.join(...)` mit einer Zeichenkettenkonstante, die ein Bauer beantwortet):

| Segment | Bauer | Stellen vorher ausserhalb des Bauers | nachher |
|---|---|---|---|
| `staging` | `ProjectState.staging_root` (neu) | **4** (`report.generate_session_brief`, `report.validate_state`, `staging.staging_dir`, `staging.clear_staging`) + der Name in `layout` | 0 |
| `archive` | `ProjectState.archive_root` | **5** (`state.read_anywhere`, `state.exists_anywhere`, `state._max_number`, `report._in_archive`, `staging.clear_staging`) | 0 |
| `generated` | `ProjectState.generated_path` | **2** (`report.generate_session_brief` und `report.doctor`) | 0 |
| `legacy` | `ProjectState.legacy_root` | 0 (diese Runde davor geschlossen) | 0 |

Die beiden `generated`-Stellen sind die, die der Docstring des Bauers selbst als seine Schreiber
nennt („The index below is one such writer; the session brief is the other") -- beide setzten den
Pfad daneben selbst zusammen. `layout.STAGING_DIRNAME` wird jetzt aus `state` re-exportiert, wo der
Bauer daneben steht.

Roter Test ohne den Fix: `tools/test_kernel.py::test_no_kernel_module_composes_a_directory_a_builder_already_owns`
(die Segmente sind aus den Bauern **abgefragt**, nicht getippt).

## 5. Mutationen -- jeder gebaute Zweig einzeln

Defekt im Klon **ausserhalb** des Repos wiederhergestellt, der zugehoerige Test darin gefahren:

| Mutation | Ergebnis |
|---|---|
| der Leser faengt wieder eine Liste von Ausnahmetypen | **rot** (2 Tests) |
| nur die woertliche Schreibweise des Pfads wird entfernt | **rot** |
| der Validator hat wieder einen eigenen Vorlauf und keine Deckungsantwort | **rot** |
| die Wandliste verwirft den Grund wieder | **rot** |
| der Idempotenz-Scan ueberspringt, was er nicht lesen kann | **rot** |
| die Verweigerung nennt die Pruefung statt der Ursache | **rot** |
| ein Modul setzt `generated/` wieder von Hand zusammen | **rot** |
| der Docstring zaehlt seine Aufrufer wieder von Hand | **rot** |

Die zweite Mutation ist eine, die dieser Runde **selbst** aufgefallen ist, bevor sie ausgeliefert
wurde: `str(FileNotFoundError)` schreibt den Pfad als Python-**Literal** (`C:\\dir\\datei`), die
YAML-Marke schreibt ihn roh. Der erste Wurf entfernte nur die zweite Schreibweise, und der eigene
Vertragstest fand es.

## 6. Die Nachmessung zu TSK-0018

Abschnitt 2 jenes Protokolls nannte die Sekunden der quadratischen Mutante absolut. Zweimal
gemessen (derselbe Klon, derselbe Rechner) kommen 3,1 und 3,6 heraus; invariant ist nur die
Richtung. Tabelle und Begruendung stehen jetzt dort und im Docstring des Tests.

## 7. Suite, Stempel, Struktur

| Lauf | Ergebnis | Dauer |
|---|---|---|
| erster Abschlusslauf `python -B -m pytest tools/ -q` | 2304 gruen, **1 rot** | 19:59 |
| nach dem Fix dieser einen Zeile | **2305 gruen, 12 uebersprungen** | 21:23 |

Der eine rote Test war
`tools/test_hooks.py::test_every_span_that_presents_the_command_surface_names_all_of_it`, und er
hat einen Text dieser Runde gefangen: zwei neue Absaetze in `report.py` nannten `validate`, `doctor`
und die Migration je in einfachen Backticks. Drei Namen der Kommandoflaeche in einem Block liest
dieser Stolperdraht als „dieser Text stellt die Flaeche vor" -- und dann muss er sie vollstaendig
vorstellen. Die Absaetze nennen die beiden Kommandos jetzt als volle Aufrufzeile
(`python scripts/harness.py validate`), was keine Flaechenvorstellung mehr ist. Das ist die Regel,
die genau fuer diesen Fall existiert, und sie hat funktioniert.

`python -m ruff check .` sauber. `python tools/bump_kit_version.py` gefahren (alle drei Kits auf
`2026.08.07-4`; der Kernel geht in den Kit-Hash ein, siehe `kernel.hashing.kit_hash_inputs`).
`python tools/validate.py`: „all structural checks passed". Gespiegelte Kit-Dateien sind nicht
beruehrt worden -- diese Runde aendert `team-kits/kernel/**` und `tools/**`, kein
kit-spezifisches Hook- oder Verfassungsfile.

## 8. Was diese Runde NICHT geschlossen hat

- **Ein V1-Speicher ausserhalb der Domaene des Suchlaufs blockiert nichts.** Gemessen: ein Zustand
  mit einem gueltigen Wurzel-Item und `project_memory/old_procs.yaml.bak` (ein V1-Datensatz darin)
  -- `record_scan_coverage` nennt die Datei, `gate_memory_complete` antwortet auf `git merge`
  **rc 0**. Dasselbe gilt fuer `staging/**` und fuer gepunktete Pfade. Vorher war dieselbe Datei in
  **keinem** Bericht; sie ist jetzt benannt und weiterhin nicht blockierend. Der Eintrag dafuer
  gehoert in die Loecherliste, die ausserhalb des Bereichs dieser Aufgabe liegt; der fertige Text
  liegt im Bericht dieser Runde. Gemessen in
  `test_the_dry_run_and_the_validator_answer_the_same_about_every_file` (letzter Block).
- **Der Restfall des Vorlaufs bleibt:** eine Datei unter einem gepunkteten Pfad, die **kein**
  YAML-Dokument ist, ist `machinery` -- weder durchsucht noch genannt. Das haelt `.kernel.lock`,
  `.audit/hook_events.jsonl` und ein `.gitkeep` je Item-Verzeichnis aus beiden Berichten; ein dort
  versteckter V1-Datensatz steht in keinem. Gemessen in
  `test_every_file_under_the_state_root_gets_exactly_one_search_verdict`.
- **Ein Feld, das eine menschliche Bestaetigung verlangt, wird von niemandem gelesen.** Alle
  importierten Items tragen `migration_confirmation_required: true`; kein Leser im Kernel, in den
  Hooks, im Sitzungsbrief oder im Dashboard wertet es aus. Nicht Auftrag dieser Runde, im Bericht
  benannt.
