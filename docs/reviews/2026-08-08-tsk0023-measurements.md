# Messprotokoll TSK-0023 (2026-08-08)

Nachbesserung der V1→V2-Migration nach dem FAIL-Verdikt zu TSK-0020 (F1–F3 blockierend, R1–R5 als
Reste). Fortsetzung von `docs/reviews/2026-08-07-tsk0020-measurements.md`.

Es steht hier nichts, was nicht gemessen ist. Wo eine Lesart des Auftrags nicht reproduzierbar war,
steht das ausdrücklich da (Abschnitt 8).

## 0. Wie gemessen wurde, und womit die Messung sich selbst begrenzt

- **Wogegen die Pfade in diesem Bericht zu lesen sind.** Jeder relative Pfad ohne führendes `docs/`,
  `tools/` oder `team-kits/` ist **zustandsrelativ**, also gegen das `project_memory/` des jeweils
  gemessenen Projekts zu lesen — so wie der Kernel sie druckt. Das betrifft insbesondere jedes
  `../…` (etwa `../v1-legacy-overflow/…` in R9.4): es liegt **neben** dem Zustandsverzeichnis, nicht
  neben dem Projekt. Gegen die Projektwurzel gelesen landet dasselbe Wort eine Ebene über dem
  Projekt; das ist stillschweigend erfolgreich und darum die eine Basis, die hier genannt sein muss.
  Pfade mit `docs/`, `tools/`, `team-kits/` oder `.claude/` am Anfang sind gegen die **Repo-Wurzel**
  zu lesen, absolute Pfade (`C:\…`) gegen den Host.
- **Echte Prozesse.** Jede `rc`-Zeile ist ein `subprocess`-Start des ausgelieferten
  `team-kits/dev-team/hooks/gate_memory_complete.py` mit JSON auf `stdin`, gegen ein
  Projektverzeichnis **außerhalb** dieses Repos, mit gültigem Wurzel-Item. `2` = Verweigerung,
  `0` = Durchlass.
- **Sandbox.** Alle Sonden laufen unter `C:\tmp-h23\…`, also außerhalb des Repos **und** außerhalb
  des Heimatverzeichnisses. Jede Sonde ruft `_sandbox.pin(...)` (cwd + `PWD`/`OLDPWD`/`HOME` gesetzt,
  `CDPATH`/`DIRSTACK` entfernt) und behauptet danach ihre eigene Position
  (`assert _sandbox._inside(os.getcwd(), SANDBOX)`), **bevor** eine Nutzlast läuft; jede läuft
  innerhalb `_sandbox.watch(REPO)`, das die geschützte Menge des echten Repos vorher und nachher
  hasht. Jeder Lauf dieses Pakets meldet `450 protected files … unchanged`. Skripte:
  `C:\tmp-h23\probe_before.py`, `probe_recursion.py`, `probe_r4.py`, `probe_r5.py`, `probe_r5b.py`,
  `mutate.py`.
- **Rotmessungen in einem Klon außerhalb des Repos** (`C:\tmp-h23\clone`, `team-kits` + `tools` +
  `docs` + `.git` + `README.md`): jeder Defekt einzeln wiederhergestellt, der zugehörige Test darin
  gefahren, danach die Datei aus dem echten Repo zurückkopiert (Abschnitt 7).
- **Wie ein nicht auflistbares Verzeichnis entsteht:** `icacls <dir> /deny <user>:(OI)(CI)(RD,RA)`,
  zurückgenommen mit `/remove:d`. Der Testhelfer `_unlistable` **behauptet** danach, dass
  `os.listdir` wirklich verweigert, und **fällt**, wenn der Host das nicht herstellt — ein
  übersprungener Test ist von einem bestandenen in einer Zusammenfassungszeile nicht zu
  unterscheiden.

## 1. F1 — ein Verzeichnis, das die Wanderung nicht öffnen kann

Zustand mit gültigem Wurzel-Item, darin `hidden/old_procs.yaml` mit `PROC-0001` (`status: ACTIVE`),
danach `hidden/` für den laufenden Nutzer gesperrt.

| | vorher | nachher |
|---|---|---|
| `search_coverage` | 2 Zeilen, **weder** das Verzeichnis noch die Datei | zusätzliche Zeile `hidden/` mit Verdikt `unlistable` und Grund |
| `build_plan` | `unreadable: []`, `unscanned: []` | `unreadable` nennt `hidden/` |
| `plan_is_executable` | **True** | **False** |
| `validate` | **keine** Meldung | `error hidden/` |
| `gate_memory_complete` auf `git merge` | **rc 0** | **rc 2**, die Meldung nennt `hidden` |

Der Mechanismus ist eine Eigenschaft der **Wanderung**, nicht des Klassifikators: `os.walk`
verschluckt den Fehler eines Verzeichnisses, das es nicht öffnen kann, und liefert für den ganzen
Teilbaum nichts. Der Klassifikator antwortete für jede Datei, die er bekam; diesen Teilbaum bekam er
nie. Jetzt meldet die Wanderung ihre eigenen Fehler (`onerror`), und **beide** Leser machen daraus
eine Verweigerung (`build_plan` → `unreadable`; `report` → `error`-Befund).

**Und der Stolperdraht misst mit einem anderen Orakel.** Der alte
(`test_every_file_under_the_state_root_gets_exactly_one_search_verdict`) verglich die Deckung gegen
ein **eigenes `os.walk`** — also gegen genau den Aufruf, dessen Blindheit er prüfen sollte. Gemessen
im Klon (Abschnitt 7, Zeile „F1b"): mit dem Defekt und dem alten Orakel bleibt der Test **grün**.
Das Orakel ist jetzt der **Bauprotokoll** der Fixture: `_seven_placements` gibt zurück, was es
geschrieben hat, und die Deckung wird dagegen gehalten. Der neue Test
`test_a_directory_the_walk_cannot_open_is_named_and_refuses_the_run` kennt die Datei im gesperrten
Verzeichnis, weil er sie selbst dorthin geschrieben hat.

**Was das NICHT tut, und es steht im Docstring von `search_coverage`:** `documents`,
`imported_legacy_ids` und `state_fingerprint` wandern denselben Baum mit derselben Blindheit. Nichts
macht diese drei sehend; was passiert, ist, dass der Lauf verweigert, solange ein solches
Verzeichnis existiert — also wird kein Plan gebaut, kein Digest vorgelegt und nichts geschrieben.

## 2. F2 — jede Schreibweise des Vorschlagsverzeichnisses, eine Antwort

Zustand mit `Staging/PR-0001/old_procs.yaml` (dieselbe Verzeichnis-Datei auf diesem Dateisystem):

| | vorher | nachher |
|---|---|---|
| `search_coverage` | `searched` | `unsearched` mit Grund |
| `documents()` (Inventar des Trockenlaufs) | `[]` | `[]` |
| Trockenlauf | **kein Datensatz, keine Zeile, nichts** | nennt die Datei unter `NOT SEARCHED` |
| `validate` | `error … holds 1 V1 backlog record(s)` | keine Meldung |
| Merge-Gate | **rc 2** | **rc 0** |

Die Ursache war eine dritte und vierte Schreibweise derselben Frage: `layout.is_project_document`
verglich den **gefalteten** Pfad (`_relative` faltet, mit gemessener Begründung),
`migrate._coverage_of` und `migrate.imported_legacy_ids` verglichen ihn ungefaltet. Es gibt jetzt
**eine** Antwort, `layout.is_in_proposal_area`, und alle drei fragen sie.

Der Test fährt **alle 128 Groß-/Kleinschreibungen** des Verzeichnisnamens (erzeugt als Produkt aus
`layout.STAGING_DIRNAME`, nicht aufgezählt) und behauptet je Datei die Implikation
„`SEARCHED` ⇔ im Inventar des Trockenlaufs"; eine Schreibweise fährt zusätzlich Validator,
Trockenlauf und Gate-Prozess.

**Die Gegenrichtung ist teurer und ist mitgemessen:** ein für `capture` vorbereiteter Item-Body
trägt Id und `status`, `scan_document` liest zwei gewöhnliche Vorschläge als `TSK-0001`/`TSK-0002`.
Würde der Vorschlagsbereich durchsucht, verweigerte das Merge-Gate jedem Projekt den Merge, sobald
zwei Vorschläge im Zustandsbaum liegen. Deshalb ist die Antwort `unsearched` und nicht `searched`.

## 3. F3 — der unbedingte Fang, und was wirklich wirkt

Ausnahmeklassen, die ein Dokument erzeugt (gemessen an `yaml.safe_load` mit Bytes):

| Probe | Ausnahme | `OSError`? | `yaml.YAMLError`? |
|---|---|---|---|
| ANSI (cp1252) | `ReaderError` | nein | **ja** |
| binär (0–255) | `ReaderError` | nein | **ja** |
| UTF-16 mit BOM | — (liest) | | |
| 5000-fach geschachtelt | **`RecursionError`** | nein | **nein** |

Damit ist die frühere Zusicherung falsch: die **Kodierungsklasse** wird nicht vom unbedingten Fang
getragen, sondern vom **Byte-Lesen** eine Zeile darunter — ein `ReaderError` *ist* ein `YAMLError`.
Gemessen im Klon: mit `except (OSError, yaml.YAMLError)` bleiben der Kodierungstest und der
Vertragstest **grün** (Zeile „F3b"); mit Text-Modus und einem in diesem Modul gewählten Codec wird
der Kodierungstest **rot** (Zeile „F3c").

Was der unbedingte Fang trägt, ist erreichbar: der Composer von PyYAML rekursiert je
Schachtelungsebene. Auf diesem Host (Rekursionsgrenze 1000):

| Tiefe | `_read_document` | `scan_document` |
|---|---|---|
| 100 / 200 / 300 / 400 | liest | läuft durch |
| 500 / 1000 / 2000 / 4000 | `RecursionError`, benannt | — |

Der Parser gibt also **vor** der eigenen Wanderung auf. Der Test misst das nicht als Annahme,
sondern **an der Grenze**: er halbiert die Tiefe bis zur größten, die noch liest, und lässt
`scan_document` genau dort laufen. Der Prozess bleibt danach gesund (dieselbe Sonde liest im
Anschluss ein heiles Dokument).

Neuer Docstring von `_read_document`: zwei getrennte Absätze, einer für das Byte-Lesen (Kodierung),
einer für den unbedingten Fang (`RecursionError`), jeder mit seiner Messung.

## 4. R1–R5

| Rest | Zustand | wo |
|---|---|---|
| **R1** `kernel` als zweite stumme Klasse | **benannt und gemessen**, nicht geschlossen | `L20`, Test `test_a_v1_store_inside_a_kernel_written_area_is_in_no_report` |
| **R2** jede Prosa-Wand als Parserfehler | **geschlossen** | `render` fragt `_is_yaml_document`; Test s. u. |
| **R3** Abhilfe unter `staging/` führt ins Leere | **geschlossen** | `_coverage_of` nennt **jede** Bedingung samt Abhilfe |
| **R4** Pfadregel für allen Code behauptet | **Behauptung korrigiert, Rest gezählt** | `L24`, Test in `tools/test_kernel.py` |
| **R5** zwei selbstbezügliche Verweise töten das Merge-Gate | **reproduziert und benannt** | `L25`, Test `test_two_item_bodies_outside_the_kernels_own_areas_refuse_every_merge` |

**R1, gemessen 2026-08-08.** Derselbe V1-Datensatz je einmal in `generated/`, `archive/PROC/2026/`
und `product/active/`: Deckung `kernel`, `record_scan_coverage` nennt keine der drei, kein
V1-Befund. Merge-Gate **rc 0** für die ersten beiden; für `product/active/` rc 2 — aber aus einem
anderen Grund (der Item-Validator liest die Datei als Item ohne Pflichtfelder). Dieselben Bytes eine
Ebene höher: rc 2 mit `holds 1 V1 backlog record(s)`. Der Docstring behauptet nicht mehr, ein
V1-Datensatz könne dort nicht liegen; er nennt den Rest und den Eintrag.

**R2.** `product/masterplan.md` als Wand: vorher `NOT READ: could not be read (ScannerError: …)` über
eine Datei, die genau so aussehen soll, wie sie aussieht; nachher `prose or configuration; not a
YAML document, so it has no top-level keys`. Die Gegenrichtung steht im selben Test: eine Wand, die
ein YAML-Dokument **ist** und nicht parst, sagt weiterhin `NOT READ`.

**R3.** `staging/PR-0001/old_procs.yaml.bak` vorher: „it is no YAML document … rename it back if it
is a V1 store" — die Umbenennung landet auf `staging/PR-0001/old_procs.yaml`, weiterhin unsearched,
aus einem Grund, den niemand genannt hatte. Nachher nennt der Grund beide Bedingungen und beide
Schritte („rename it back to a .yaml document **and** move it out of `staging/`").

Der erste Wurf dieses Fixes trug denselben Defekt eine Verzweigung weiter: der **gepunktete** Pfad
kehrte weiterhin früh zurück, also bekam `staging/.bak/old_procs.yaml` die Abhilfe „move it out of
the dotted path" — und landet damit im Vorschlagsbereich. Alle drei Bedingungen reihen sich jetzt
ein; der Test misst zwei doppelt ausgeschlossene Dateien und leitet die erwarteten Teilsätze aus den
einfach ausgeschlossenen ab, statt sie zu tippen.

**R4.** AST-Leser über `team-kits/**/*.py` ohne das Kernel-Paket: **7** Stellen in 6 Dateien
(`hooks/_kernel.py` je Kit, `templates/repo/scripts/generate_dashboard.py`,
`templates/repo/scripts/retro.py` in dev und research). Der Docstring der Regel behauptet ihre
Reichweite jetzt für das Kernel-Paket, und die Zahl ist in **beiden** Richtungen gepinnt: eine neue
Stelle wird rot, die letzte verschwundene ebenso. Der Testsuite-Code ist ausdrücklich nicht in der
Zählung — ein Test, der den erwarteten Pfad selbst zusammensetzt, ist das unabhängige Orakel.

**R5** siehe Abschnitt 8; die reproduzierte Kette steht als `L25`.

## 5. DEC-0021 — die Umbenennung

`migration_confirmation_required` → `imported_from_v1` (`backlog_types.IMPORT_MARK`). Drei
Schreibstellen, aus dem Code gelesen statt aufgezählt: `migrate._with_legacy`,
`state.capture_migrated_archive`, `state.capture_migrated_unresolved` — der Test behauptet genau
diese Menge und wird rot, wenn eine vierte dazukommt.

**Leser: null**, und auch das ist aus dem Code gelesen. Die Definition eines Lesers ist die
Operation, nicht das Vorkommen: ein Subscript im Load-Kontext oder ein `.get` mit dem Namen. Das
Feld in einem gedruckten Satz zu nennen ist kein Lesen — `render` und `_receipt_fields` tun genau
das und fragen kein Item.

In der Spezifikation steht die Umbenennung als **Nachtrag (f)** zu II.10, neben der Forderung, nicht
an ihrer Stelle: die Konvention dieses Repos ist, dass eine Abweichung vom Verlangten daneben
benannt wird, statt die Forderung umzuschreiben. `README.md` nennt den neuen Namen und sagt in
einem Halbsatz, was er ist.

## 6. Die Zusicherungen dieses Pakets, jede mit ihrer Messung

| Zusicherung | gemessen von |
|---|---|
| `search_coverage` gibt jedem Ding unter der Wurzel genau ein Verdikt | `test_every_file_under_the_state_root_gets_exactly_one_search_verdict` (Orakel: Bauprotokoll) |
| jedes Verdikt, das der Code erzeugt, ist im eigenen Docstring benannt — und umgekehrt | `test_every_verdict_the_run_up_can_produce_is_named_where_it_is_documented` |
| ein nicht auflistbares Verzeichnis ist benannt und blockierend | `test_a_directory_the_walk_cannot_open_is_named_and_refuses_the_run` |
| jede Schreibweise des Vorschlagsbereichs: eine Antwort | `test_every_spelling_of_the_proposal_area_gets_one_answer_from_both_readers` |
| der unbedingte Fang trägt eine erreichbare Klasse, und der Parser gibt vor der Wanderung auf | `test_a_document_nested_deeper_than_the_reader_can_follow_is_named_not_a_crash` |
| das Byte-Lesen (nicht der Fang) trägt die Kodierungsklasse | derselbe Test + Klonzeilen F3b/F3c |
| die Abhilfe nennt jede Bedingung | `test_the_remedy_for_an_unsearched_file_names_every_condition_that_keeps_it_out` |
| eine Prosa-Wand ist kein Parserfehler | `test_a_wall_that_is_prose_is_not_reported_as_a_document_that_failed_to_parse` |
| die Marke hat drei Schreiber und keinen Leser | `test_the_import_mark_says_where_an_item_came_from_and_claims_no_lever` |
| die Pfadregel gilt im Kernel-Paket, der Rest ist gezählt | `test_kernel.test_the_path_rule_stops_at_the_kernel_package_and_the_rest_is_counted` |
| Loch und Stolperdraht bleiben ein Paar — **über die ganze Suite**, nicht über eine Datei | `test_every_hole_a_test_measures_is_carried_by_the_hole_list` |

Der letzte Punkt ist derselbe Defekt wie R4, eine Datei weiter: der Kopplungstest las **eine**
Datei, also hing ein aus `test_kernel.py` oder `test_disposition.py` gemessenes Loch an nichts. Er
liest jetzt jedes `tools/test_*.py` und prüft die Zitate gegen die dort definierten Testnamen.

## 7. Rotmessungen — jeder Defekt einzeln, im Klon außerhalb des Repos

`C:\tmp-h23\mutate.py`, jede Zeile ein eigener `pytest`-Lauf im Klon:

| Mutation | Ergebnis |
|---|---|
| F1: die Wanderung meldet ihre eigenen Fehler nicht | **rot** |
| F1b: **derselbe Defekt** unter dem ALTEN Stolperdraht (eigenes `os.walk` als Orakel) | **grün** — das Orakel war blind wie der Aufruf |
| F2: der Vorschlagsbereich wird ungefaltet verglichen | **rot** |
| F3: der Leser fängt wieder eine Liste von Ausnahmetypen | **rot** |
| F3b: **dieselbe** Mutation unter dem Kodierungstest, der sie zu messen behauptete | **grün** — die Behauptung war falsch |
| F3c: der Leser dekodiert mit einem eigenen Codec statt Bytes zu übergeben | **rot** |
| R2: die Wandliste parst, was ein Gate liest | **rot** |
| R3: der Grund hört bei der ersten Bedingung auf | **rot** |
| R3b: der gepunktete Pfad kehrt früh zurück, statt sich einzureihen | **rot** |
| DEC-0021: die Marke trägt wieder ihren alten Namen | **rot** |
| L24: eine zusätzliche Komposition außerhalb des Kernel-Pakets | **rot** |
| Kopplung: ein Eintrag zitiert einen Test, den kein Modul der Suite hat | **rot** |
| **ohne jede Mutation, alle zwölf zusammen** | **grün** |

## 8. Was diese Runde NICHT geschlossen hat, und eine Lesart, die ich nicht reproduzieren konnte

- **R5 ist im Auftrag mit einem Satz beschrieben, der mehrere Lesarten zulässt** („zwei
  selbstbezügliche Verweise im Zustandsbaum töten das Merge-Gate"). Zwei davon habe ich gemessen:
  - *YAML-Selbstreferenzen* (`&A … *A`, auch zwei davon in einem Zustand): das Merge-Gate antwortet
    **korrekt rc 2** mit einem Befund über den Datensatz, kein Absturz, kein Hänger, `build_plan`
    verweigert sauber. Diese Lesart ist **widerlegt**.
  - *Selbstbenennende Item-Bodies* (`id: SR-0001` + `status` in einer Datei dieses Namens): zwei
    davon außerhalb der kernel-eigenen Bereiche erzeugen zwei Befunde und **rc 2**, und innerhalb
    einer Sitzung räumt das niemand weg. Diese Lesart ist **reproduziert** und liegt als `L25` mit
    Kette, Urteil und Begrenzung. Sie ist zugleich die Gegenrichtung des F2-Fixes: genau deshalb
    bleibt der Vorschlagsbereich aus dem Scan.
  Sollte der Prüfer eine dritte Lesart gemeint haben, ist sie hier nicht behandelt — das ist der
  offene Punkt dieses Pakets, und er steht hier statt als stillschweigende Annahme.
- **L20 (kernel-eigene Bereiche) ist nicht geschlossen.** Der Ausweg wäre eine Aussage darüber,
  welche **Namen** ein Kernel-Bauer je Bereich erzeugt — also eine Tabelle pro Bereich, und damit
  die Aufzählung, gegen die dieses Repo gebaut ist. `legacy/` müsste ohnehin ausgenommen bleiben.
- **L24 (Pfadregel) ist nicht geschlossen.** Die drei `_kernel.py`-Stellen liegen auf dem
  Bootstrap-Pfad, der ohne Kernel antworten muss; sie an einen Bauer zu hängen, verlegte eine
  kernelfreie Antwort auf den Kernel.
- **Der Restfall der Wanderung bleibt:** eine Datei unter gepunktetem Pfad, die kein YAML-Dokument
  ist, ist `machinery` — weder durchsucht noch genannt (`L19`).
- **Nicht in meinem Bereich, aber im Baum:** `.gitignore`, `project_memory/generated/index.yaml`
  und `project_memory/evidence/EVD-0002.yaml` sind zwischen `b32ec98` und diesem Paket vom
  Sitzungsagenten geschrieben worden (Zeitstempel 19:53–19:54), nicht von mir; `project_memory/**`
  und `.claude/**` sind für dieses Item verbotener Bereich.
- **Zwei Dateien außerhalb des `allowed_scope` habe ich angefasst**, weil `expected_output` 5 sie
  ausdrücklich verlangt: `docs/HARNESS_V2_SPEC.md` (Nachtrag (f) zu II.10) und `README.md` (der
  Feldname). Beides ist im `forbidden_scope` nicht enthalten; es ist trotzdem eine Abweichung vom
  `allowed_scope` und steht deshalb hier.

## 9. Suite, Stempel, Struktur

| Lauf | Ergebnis |
|---|---|
| `python -m ruff check .` | sauber |
| `python tools/bump_kit_version.py` | alle drei Kits auf `2026.08.08-2` (der Kernel geht in den Kit-Hash ein; `-1` war der Stempel vor dem R3b-Nachzug) |
| `python tools/validate.py` | „all structural checks passed" |
| `PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory validate` | 0 Fehler, Index deckungsgleich |
| `python -B -m pytest tools/ -q` | s. Abschnitt 10 |

Gespiegelte Kit-Dateien sind **nicht** berührt: diese Runde ändert `team-kits/kernel/**`, `tools/**`
und Dokumente; kein kit-spezifisches Hook- oder Verfassungsfile.

## 10. Der Abschlusslauf

`python -B -m pytest tools/ -q` — **2315 bestanden, 12 übersprungen, 0 rot, in einem Lauf**
(25:09). Während der Arbeit lief jeweils die kleinste Auswahl, die die geänderte Eigenschaft deckt
(DEC-0023).

**Es sind zwei volle Läufe geworden, und der Grund gehört hierher:** der erste (25:28, ebenfalls
2315/12) lag auf einem Baum, in dem der R3-Fix seinen eigenen Defekt eine Verzweigung weiter noch
trug — der gepunktete Pfad kehrte früh zurück, also bekam `staging/.bak/old_procs.yaml` eine
Abhilfe, die in den Vorschlagsbereich führt. Gefunden beim Nachlesen des eigenen Fixes, nicht vom
Test. Danach: Bedingung eingereiht statt früh zurückzukehren, Rotmessung „R3b" ergänzt, Kits neu
gestempelt (`2026.08.08-2`), und der Abnahmelauf **komplett wiederholt**. Der abgelieferte Baum ist
der des zweiten Laufs.

Zum Vergleich: TSK-0020 schloss mit 2305 bestanden / 12 übersprungen. Die **zehn** zusätzlichen
Tests sind genau die dieser Runde — gezählt aus dem Diff (`git diff -U0 tools/ | grep "^+def
test_"`): neun in `tools/test_migrate.py`, einer in `tools/test_kernel.py`. Drei bereits bestehende
Tests haben zusätzlich eine korrigierte Zusicherung bekommen (der Kodierungstest, der
Totalitätstest, der Kopplungstest); sie zählen nicht doppelt.

---

# Runde 2 (2026-08-08) — nach dem FAIL-Verdikt zu Runde 1

Prüfverdikt: **FAIL**, zwei blockierende Befunde (B1, B2), fünf benannte Reste (B3–B7). Was der
Prüfer bestätigt hat, ist unangetastet geblieben.

## R2.0 Sandbox dieser Runde

- Sandbox `C:\tsk0023-r2\…` — außerhalb des Repos **und** außerhalb `C:\Users\zenti`. Jede Sonde
  ruft `_sandbox.pin(SANDBOX, <leaf>)` (cwd + `PWD`/`OLDPWD`/`HOME` gesetzt, `CDPATH`/`DIRSTACK`
  entfernt) und läuft in `_sandbox.watch(REPO)`. Jeder Lauf meldete
  `… protected files … unchanged`: `450` in den ersten Sonden, `462` in den späteren. Die Differenz
  ist gezählt und nicht geraten — es sind **12** `__pycache__`-Dateien in geschützten Bäumen
  (`.claude/hooks/`, `team-kits/kernel/`), die ein Suitelauf dazwischen erzeugt hat. Alle Sonden
  laufen mit `python -B`; die Menge wächst, keine gehashte Datei hat sich bewegt.
- Skripte: `m1_b1_before.py` (B1 vorher/nachher, echte CLI-Prozesse), `m2_b2_before.py`,
  `m3_every_remedy.py` (Abhilfen mechanisch, abgeleitetes Korpus), `m4_red.py` (Rotmessungen im
  Klon), `m5_residuals.py` (die Ketten von L26–L28).
- Gesperrte ACLs (`icacls /deny`) werden in jedem Skript im `finally` mit `/remove:d` zurückgenommen
  und der Zugriff danach **nachgewiesen** (`open(...).read()`), bevor aufgeräumt wird.

## R2.1 B1 — eine Datei, die niemand öffnen kann (die F1-Klasse eine Ebene tiefer)

`icacls <doc> /deny <user>:(RD,RA)` auf **ein** Kit-Dokument eines sonst sauberen Zustands,
`kernel.cli` als echter Prozess:

| | vorher | nachher |
|---|---|---|
| `validate` | rc 1, kein Traceback, nennt die Datei | rc 1, kein Traceback, nennt die Datei |
| `migrate --dry-run` | rc 1 **mit Traceback**, `PermissionError` aus `migrate.py:433` (`_file_facts`) | rc 1, **kein Traceback**, nennt die Datei |
| `_file_facts` | `PermissionError` at migrate.py:433 | returned |
| `state_fingerprint` | `PermissionError` at migrate.py:1724 | returned |
| `build_plan` | `PermissionError` at migrate.py:433 | returned |

Gebaut als **Eigenschaft, nicht als zwei Handler**: `_read_bytes` ist jetzt der einzige Ort, an dem
dieses Modul eine Datei unter der Zustandswurzel öffnet; `_read_document`, `_file_facts` und
`state_fingerprint` gehen alle durch ihn. Beide melden in dieselbe Liste wie die
`UNLISTABLE`-Zeile (`plan["unreadable"]`), auf der `plan_is_executable` verweigert.

**Ein Nachzug, den erst der Fix erzeugt hat:** dieselbe Datei erzeugt jetzt **zwei** wahre Zeilen
(das Inventar hat keinen Hash, der Digest ist eine Datei kürzer). Die Verweigerung in `execute`
zählte Zeilen und hätte „2 documents unreadable" für **eine** Datei gesagt. `_unreadable_paths`
zählt jetzt Pfade, und die Eigenschaft, auf der das ruht („eine Zeile **beginnt** mit dem Pfad, um
den es geht" — gilt für alle fünf Erzeuger), steht als Zusicherung im Docstring **und** als
Zusicherung im Test.

Die beiden ausgelieferten Texte, die vorher das Gegenteil versprachen (`report.py` Abhilfe des
Validators, `migrate.py` Modulkopf), sind damit wahr geworden und blieben unverändert.

## R2.2 B2 — die Abhilfe wird gegen den Klassifikator geprüft, und das vierte Exemplar

Korpus **abgeleitet**, nicht aufgezählt: `layout.kernel_written_subtrees()` (fragt die Pfadbauer
selbst) × den drei Bedingungen, die `_classify` gleichzeitig halten kann → 336 Pfade, davon 184
`unsearched`. Jede Abhilfe wörtlich angewandt:

    vorher:   104 von 336 landen NICHT auf `searched`
    nachher:    0 von 184 unsearched-Pfaden — und die Meldung nennt das geprüfte Ziel

**Das vierte Exemplar der R3-Klasse steckt in diesem Korpus und ist nicht die gepunktete Form:**

    .legacy/old_procs.yaml        "move it out of the dotted path"
        -> legacy/old_procs.yaml        kernel  (stumm, L20)
    staging/tasks/active/x.yaml   "move it out of `staging/`"
        -> tasks/active/x.yaml          kernel  (stumm, L20)

Der zweite Fall ist **nicht gepunktet, ist YAML und wird von genau einer Bedingung draußen
gehalten**. Jede Formulierung, die den gepunkteten Fall beantwortet, lässt ihn stehen — das ist der
Grund, warum die Abhilfe jetzt **abgeleitet** wird statt geschrieben: `remedied_path` nimmt die
Punkte ab, gibt dem Namen eine Dokumentendung und geht dann zur Zustandswurzel hoch, bis
`_classify` wirklich `searched` sagt. Kernel-Bereiche fallen weg, weil sie **gefragt** werden, nicht
weil sie aufgezählt sind.

## R2.3 Rotmessungen (Klon `C:\tsk0023-r2\red\clone`, Kontrolle im selben Klon)

| Defekt wiederhergestellt | Test | Ergebnis |
|---|---|---|
| `_file_facts` + `state_fingerprint` + ihre drei Aufrufstellen wie vorher | `test_a_document_the_run_cannot_open_is_named_and_refuses_instead_of_crashing` | **rot** — `PermissionError` aus `migrate.py:533` |
| Abhilfe nennt kein Ziel (alter Satz) | `test_every_remedy_the_run_up_prints_lands_on_a_file_it_really_searches` | **rot** — „the message does not name the place its own rule leads to" |
| Ziel naiv abgeleitet statt geprüft (kein Hochgehen) | dieselbe | **rot** — „following its own remedy lands on `approvals/consumed/old_procs.yaml`, which is kernel" |
| nichts wiederhergestellt (Kontrolle) | beide | **grün** (2 passed) |

## R2.4 B3–B7 — gemessen, benannt, nicht gebaut

Die Ketten stammen aus dem Prüfbericht; sie sind hier **selbst nachgemessen**, mit Kontrolle. Für
`test_migrate` mit `v1_state` braucht der Klon die Historie (`git clone --no-checkout`) — ohne sie
fällt der Test aus einem Grund, der nichts mit dem Patch zu tun hat. Das ist beim ersten Anlauf
passiert und hat fünf falsche „rot" erzeugt.

- **B3 → `L26`** (Kopplungstest einseitig). Gemessen: Test nennt einen Eintrag, den es nicht gibt →
  **rot**; Eintrag zitiert einen Test, den kein Modul definiert → **rot**; **verwaister** Eintrag
  ohne Urteil und ohne Begrenzung → **grün**. Der Docstring behauptet „BOTH DIRECTIONS" nicht mehr.
- **B4 → `L27`** (Leser als zwei Operationen). Je ein echter Leser in `kernel/report.py` eingesetzt,
  Kontrolle vorweg: Kontrolle **grün**, Subscript **rot**, `in` **grün**, `pop` **grün**,
  Schlüsselvergleich **grün**, `getattr` **grün**. Der Docstring behauptet nicht mehr, jeder morgen
  hinzugefügte Leser werde rot.
- **B5 → `L28`** (`UNLISTABLE` für jeden Walk-Fehler). `gate_memory_complete` als Prozess:
  `.audit/` lesbar rc 0 → gesperrt **rc 2** (nennt es); `staging/` lesbar rc 0 → gesperrt **rc 2**
  (nennt es). Über-Verweigerung, kein Loch; Urteil und Begrenzung stehen im Eintrag.
- **B6 → `L29`** (`str.lower` ≠ Faltung des Dateisystems). Selbst gemessen: `staging`, `Staging`,
  `STAGING` — Dateisystem öffnet, Prädikat ja. `staging.` — Dateisystem öffnet **dieselbe** Datei,
  Prädikat **nein**. `staging..` — öffnet nichts. Der Residual-Absatz in `layout.py` nennt jetzt
  beide Richtungen.
- **B7 → geschlossen, kein Eintrag.** Die Zahl steht nur noch im Pin
  `test_kernel._COMPOSITIONS_OUTSIDE_THE_PACKAGE`; die Prosakopie in `L24` ist entfernt und verweist
  auf den Pin. Die Stellen selbst (qualitativ) bleiben im Eintrag stehen.

Alle vier neuen Einträge werden vom Kopplungstest wirklich geprüft: `L26`–`L29` sind je in dem
Docstring genannt, der die zugehörige Messung trägt, also in der Hälfte, die dieser Test abdeckt.

## R2.5 Abnahmelauf der Runde 2

- `python tools/bump_kit_version.py` → alle drei Kits `2026.08.08-4` (gefahren **vor** dem Urteil).
- `python -m ruff check .` → `All checks passed!`
- `python tools/validate.py` → `all structural checks passed.`
- `python -B -m pytest tools/ -q` → **2317 bestanden, 12 übersprungen**, 25:17, exit 0.

**Es sind zwei volle Läufe geworden, und warum gehört hierher.** Der erste (25:28, ebenfalls
2317/12, Kits `-3`) lag auf einem Baum, in dem zwei Zusicherungen dieses Pakets noch nicht als Test
standen: dass `_read_bytes` der **einzige** `open` dieses Moduls ist, und dass **jede** Zeile der
`unreadable`-Liste mit ihrem Pfad beginnt — die Eigenschaft, auf der `_unreadable_paths` und damit
die Zählung in der Verweigerung ruht. Beides war behauptet und nicht gemessen; beides ist jetzt im
B1-Test (AST über das geparste Modul, und ein Zustand, in dem vier der fünf Erzeuger der Liste
gleichzeitig feuern). Danach neu gestempelt (`-4`) und der Abnahmelauf **wiederholt**. Der
abgelieferte Baum ist der des zweiten Laufs.

Runde 1 schloss mit 2315/12. Die **zwei** zusätzlichen Tests sind die dieser Runde:
`test_migrate.test_a_document_the_run_cannot_open_is_named_and_refuses_instead_of_crashing` und
`test_migrate.test_every_remedy_the_run_up_prints_lands_on_a_file_it_really_searches`. Vier
bestehende Docstrings haben eine korrigierte Zusicherung bekommen (Kopplungstest, Import-Marke,
Totalitätstest, Schreibweisentest) und einer in `kernel/layout.py`; sie zählen nicht als Tests.

Laufzeit unverändert gegenüber Runde 1 (25:28 zu 25:28), obwohl `_coverage_of` für jede
`unsearched`-Datei jetzt zusätzlich `_classify` auf dem Zielpfad fragt.

**Gespiegelt wurde nichts,** und das ist kein Auslassen: geändert sind `team-kits/kernel/migrate.py`
und `team-kits/kernel/layout.py`. Das Kernel-Paket liegt genau einmal unter `team-kits/kernel/`; die
Spiegelregel gilt für `team-kits/{dev,office,research}-team/`, und dort ist keine Datei angefasst.
`git status` bestätigt das, der Spiegeltest der Suite ebenfalls.

**Aufräumen:** keine gesperrte ACL übrig — `C:\tsk0023-r2` und `…\Temp\pytest-of-zenti` abgelaufen,
`denied leftovers: 0`.

---

# Runde 3 (2026-08-09) — nach dem FAIL-Verdikt zu Runde 2

Prüfverdikt: **FAIL**, zwei blockierende Befunde (F1, F2), zwei Reste (F3, F4). Was der Prüfer
bestätigt hat, ist unangetastet geblieben — insbesondere der abgeleitete Abhilfe-Korpus, die
Abfangbreite von `_read_bytes`, L26–L29 und die `--check`-Fläche der Kits.

## R3.0 Sandbox dieser Runde

- Sandbox `C:\tsk0023-r3\…` — außerhalb des Repos **und** außerhalb `C:\Users\zenti`. Jede Sonde
  ruft `_sandbox.pin(SANDBOX, <leaf>)`, behauptet danach ihre eigene Position
  (`assert _sandbox._inside(os.getcwd(), SANDBOX)`) **bevor** eine Nutzlast läuft, und läuft in
  `_sandbox.watch(REPO)`. Jeder Lauf dieses Pakets meldete `452 protected files … unchanged`.
- Skripte: `m1_f1_before.py` (F1, echtes gescaffoldetes dev-team-Projekt), `m2_f2_before.py` (F2),
  `m3_f4_before.py` (F4, gesperrte ACLs), `m4_next_exemplars.py` (N1/N2), `probe_audit.py` (trägt
  der Audit-Haken?), `make_clone.py`, `mutate.py` (Rotmessungen).
- Gesperrte ACLs werden im `finally` mit `/remove:d` zurückgenommen und der Zugriff danach
  **nachgewiesen** (`open(...).read()`).
- Der Klon für die Rotmessungen ist ein `git clone` **mit Historie** plus dem Arbeitsbaum darüber
  (`make_clone.py`) — ohne Historie fällt `v1_state` aus einem Grund, der nichts mit dem Patch zu
  tun hat. Der Klon wurde **nach** der letzten Codeänderung neu erzeugt.

## R3.1 F1 — die Abhilfe nannte eine Wand als Ziel

Gemessen gegen ein Projekt, das aus dem ausgelieferten dev-Kit gescaffoldet ist
(`templates/project_memory` + `hooks/` + `settings/settings.json`); Wände dieser Installation:
`product/masterplan.md`, `project_config.yaml`.

| Pfad | Ziel vorher | vorhanden | Wand | Ziel nachher |
|---|---|---|---|---|
| `.legacy/project_config.yaml` | `project_config.yaml` | ja | **ja** | **keins** |
| `staging/project_config.yaml` | `project_config.yaml` | ja | **ja** | **keins** |
| `tasks.yaml.bak` | `tasks.yaml` | ja | nein | **keins** |
| `process_definitions.yml.old` | `process_definitions.yml` | ja | nein | **keins** |

Gebaut als **eine Eigenschaft, nicht zwei Sonderfälle**: ein Landeplatz muss **frei** sein
(`_is_occupied`, `os.path.lexists`). Eine Wand braucht keine eigene Klausel, weil
`layout.gated_documents` den Zustandsbaum wandert — jede Wand ist eine Datei, die **existiert**.
Das ist behauptet **und** gemessen: der Test verlangt für jede Wand dieser Installation
`_is_occupied` = wahr, und dass mindestens ein blockierter Landeplatz des Korpus eine Wand ist.

`remedied_path` liefert jetzt `(Ziel, jeder durchsuchte Platz ist belegt)`; die drei Antworten
tragen drei verschiedene Sätze, weil „kein Platz ist durchsucht" und „jeder Platz ist belegt" zwei
verschiedene Auskünfte sind.

**Der Rest, nicht schließbar und benannt:** die Auskunft gilt für den Augenblick des Lesens; der
Leser handelt später in einer Shell außerhalb der Sitzung. Eintrag `L30`, mit Urteil und Begrenzung.

## R3.2 F2 — die Quittung eines abgebrochenen Laufs behauptete „none moved"

Szenario, jede Bedingung eine echte Bedingung des Dateisystems, nichts gepatcht: `a.yaml` von einem
früheren Lauf importiert und zurückgelegt (also `already_imported`), `sub/b.yaml` neu, und an
`legacy/sub` liegt eine **Datei**, sodass `os.makedirs` das Landeverzeichnis des zweiten Dokuments
nicht bauen kann.

| | vorher | nachher |
|---|---|---|
| `a.yaml` wirklich verschoben | ja | ja |
| Quittungszeile „moved to legacy/" | `none` | `a.yaml -> legacy/a.yaml (83 B, sha256 3d51709d…)` |
| `a.yaml` unter „carried … (left in place, unrenamed and unedited)" | **ja** | nein |
| Verweigerung nennt `a.yaml` | nein | ja |

`moved` gehört jetzt dem **Aufrufer** (`execute`), `_retire_absorbed_documents` hängt an. Der
Docstring, der den Fall vorher als „NOT covered" führte, nennt jetzt den Mechanismus.

## R3.3 F4 — die Zählung endete am ersten Leerzeichen

Zwei gesperrte Dokumente mit Leerzeichen im Namen:

| | vorher | nachher |
|---|---|---|
| Einträge in `unreadable` | 4 | 4 |
| `_unreadable_paths()` | `['my']` | `['my other procedures.yaml', 'my procedures.yaml']` |
| Verweigerung | „**1** path(s) unreadable" | „**2** path(s) unreadable" |

Der Plan führt `unreadable` jetzt als **(Pfad, Grund)-Paare**, wie `unlistable_notes` es schon tat;
formatiert wird erst beim Drucken, und die gedruckte Zeile ist byte-gleich zu vorher. Der Korpus des
Tests trägt jetzt Namen mit Leerzeichen (`my broken procedures.yaml`, `my denied procedures.yaml`,
`my shut away/`) und behauptet zusätzlich die Zahl in der Verweigerung.

## R3.4 F3 — die Zusicherung „der einzige `open`" wird als Eigenschaft gemessen

Gebaut statt aufgeschoben. Die Messung läuft in einem **eigenen Prozess** (`sys.addaudithook` ist
nicht zurücknehmbar): beim `open`-Ereignis wird der Stapel nach außen gegangen, und der **erste
Rahmen außerhalb der Standardbibliothek** ist der, der die Datei wollte — eine Definition, keine
Liste von Öffnernamen. Vorgemessen mit `probe_audit.py`: `open`, `io.open`, `codecs.open`,
`os.open` und `pathlib.Path.read_bytes` werden alle demselben Rahmen zugerechnet.

Beide Richtungen, im Klon, je ein eigener pytest-Lauf (Abschnitt R3.6):

| Mutation | neue Messung | alte AST-Regel |
|---|---|---|
| echter zweiter, **ungehandelter** Leser (`io.open` in `_retire_absorbed_documents`) | **rot** | **grün** |
| verhaltensgleiche Umschreibung **innerhalb** `_read_bytes` (`io.open`) | **grün** | **rot** |

Damit ist die Behauptung des Prüfers nachgemessen und die alte Regel ersetzt. Der Docstring von
`_read_bytes` sagt jetzt, was gemessen wird. Der Rest der Definition — eine Fremdbibliothek, die im
Auftrag dieses Moduls öffnet — steht als `L31`.

## R3.5 Das nächste Exemplar der Familie (gesucht, nicht gestolpert)

Die Frage war: **welche Autorität kennt dieses Modul noch, die eine gedruckte Aussage widerlegen
könnte?** Zwei Funde, beide gemessen:

**N1 — der Zug nach `legacy/` überschreibt still.** `os.replace` ist atomar **und** stumm, und
`absorbed_documents` fragt nie, was am Ziel liegt. Gemessen: Lauf 1 verschiebt `old_procs.yaml` und
legt dessen sha256 in seine Quittung; ein zweites Dokument desselben Namens taucht auf; Lauf 2
**ersetzt** die abgelegte Kopie — der Hash der ersten Quittung nannte danach Bytes, die es nirgends
gibt, und der Trockenlauf druckte `old_procs.yaml -> legacy/old_procs.yaml` wie beim ersten Mal.
Nachher: `build_plan` führt `occupied_landings`, der Trockenlauf nennt den Fall (`ALREADY TAKEN` +
eigener Abschnitt mit Abhilfe), `plan_is_executable` ist falsch, und `_retire_absorbed_documents`
fragt unmittelbar vor dem Schreiben noch einmal. Gegenrichtung im selben Test: die abgelegte Kopie
aus dem Zustandsverzeichnis genommen ⇒ derselbe zweite Lauf legt normal ab.

**N2 — die Abhilfe nannte eine Wand als QUELLE.** Zwei der drei Wände eines dev-Kits sind Prosa, und
Prosa hat keine Dokumentendung — also ist `product/masterplan.md` `unsearched`, und die Abhilfe
lautete „rename it back to a .yaml document", Ziel `product/masterplan.yaml` (frei). Wer das tut,
lässt `gate_memory_complete` eine abwesende Datei lesen. Das ist dieselbe Klausel, die
`absorbed_documents` für den Zug nach `legacy/` schon hält, einen Schritt früher und über einen Zug,
den dieses Kommando nur **vorschlägt**. Nachher nennt die Antwort keinen Schritt und kein Ziel; das
Orakel des Tests sind die **Abhilfe-Zeichenketten des Klassifikators selbst**, und die Gegenrichtung
läuft im selben Test (Installation entfernt ⇒ dieselbe Datei ist keine Wand ⇒ die Abhilfe steht
wieder da).

Ein dritter Kandidat wurde geprüft und **verworfen**: `archive_location` kann nicht kollidieren, weil
die Id vom Kernel vergeben wird.

Der Satz für eine Wand sagt bewusst **nichts** darüber, was andere Werkzeuge mit der Datei tun: eine
`unsearched`-Datei ist beim Validator Deckung und kein Befund (`L19`), während das Merge-Gate über
eine **ungefüllte** Wand aus einem ganz anderen Grund verweigert — jede Aussage hier über „was
`validate` tut" wäre über eine der beiden und würde als die andere gelesen. Der erste Wurf dieses
Satzes trug genau diesen Fehler und ist vor dem Abnahmelauf korrigiert worden.

## R3.6 Rotmessungen (Klon `C:\tsk0023-r3\red\clone`, mit Historie, Kontrolle im selben Klon)

| Defekt wiederhergestellt | Test | Ergebnis |
|---|---|---|
| F1 der Landeplatz wird nicht gefragt | `test_no_remedy_this_command_prints_lands_on_a_file_that_is_already_there` | **rot** |
| N2 eine Wand bekommt die Abhilfe wie jede Datei | `test_a_document_a_registered_gate_reads_is_offered_no_way_to_move_or_rename_it` | **rot** |
| F2 die Zugschleife behält ihre eigene Liste | `test_a_run_that_stops_half_way_through_the_move_says_which_documents_it_moved` | **rot** |
| N1 niemand fragt, ob der Platz unter `legacy/` belegt ist | `test_a_second_document_of_the_same_name_does_not_replace_the_one_already_retired` | **rot** |
| F4 die Zählung holt den Pfad wieder aus dem Satz | `test_a_document_the_run_cannot_open_is_named_and_refuses_instead_of_crashing` | **rot** |
| F3a echter zweiter, ungehandelter Leser | `test_every_state_file_this_module_opens_it_opens_through_read_bytes` | **rot** (alte AST-Regel: **grün**) |
| F3b verhaltensgleiche Umschreibung in `_read_bytes` | derselbe | **grün** (alte AST-Regel: **rot**) |
| Kontrolle — nichts wiederhergestellt | alle sechs | **grün** (6 passed) |

## R3.7 Was diese Runde NICHT geschlossen hat

- **`L30`** (die Spanne zwischen Auskunft und `mv` des Lesers) — nicht schließbar, mit Begrenzung.
- **`L31`** (Zurechnung eines `open` an den ersten Nicht-Stdlib-Rahmen) — Rest der Messung, mit
  Gegenrichtung im selben Test.
- **`L19`/`L20`** bleiben, wie sie standen; diese Runde hat daran nichts geändert.
- **Ein bestehender Test wurde angepasst**, nicht weil er störte, sondern weil er den Feldfall von
  N1 selbst herstellte: `test_the_archive_path_takes_a_record_the_field_contract_would_refuse`
  schrieb ein **drittes** `tasks.yaml`, nachdem ein Lauf das zweite nach `legacy/tasks.yaml`
  abgelegt hatte (der Kommentar der Stelle sagte „in a fresh state", der Zustand war es nicht). Der
  Test tut jetzt, was die Verweigerung als Abhilfe nennt — die abgelegte Kopie aus dem
  Zustandsverzeichnis nehmen — und misst danach weiter, was er misst.
- **Eine Datei außerhalb des `allowed_scope` angefasst:** `docs/HARNESS_V2_SPEC.md`, Nachtrag (e) zu
  II.10, um eine Klausel („nie auf einen Platz, an dem schon etwas liegt") und einen Stolperdraht.
  Die Liste dort war nicht falsch, sondern unvollständig; sie steht trotzdem hier als Abweichung.
  `README.md` ist **nicht** angefasst: keine seiner Aussagen ist durch diese Runde unwahr geworden.

## R3.8 Abnahmelauf der Runde 3

- `python tools/bump_kit_version.py` → alle drei Kits `2026.08.09-1` (gefahren **vor** dem Urteil).
- `python -m ruff check .` → `All checks passed!`
- `python tools/validate.py` → `all structural checks passed.`
- `PYTHONPATH=team-kits python -B -m kernel.cli --root project_memory validate` → `0 error(s), 0 warning(s)`.
- `python -B -m pytest tools/ -q` → **2322 bestanden, 12 übersprungen, 0 rot, in einem Lauf**
  (24:53, exit 0), auf dem gestempelten Baum.

Runde 2 schloss mit 2317/12. Die **fünf** zusätzlichen Tests sind genau die dieser Runde:
`test_no_remedy_this_command_prints_lands_on_a_file_that_is_already_there`,
`test_a_document_a_registered_gate_reads_is_offered_no_way_to_move_or_rename_it`,
`test_a_second_document_of_the_same_name_does_not_replace_the_one_already_retired`,
`test_a_run_that_stops_half_way_through_the_move_says_which_documents_it_moved` und
`test_every_state_file_this_module_opens_it_opens_through_read_bytes` (alle in
`tools/test_migrate.py`). Der AST-Stolperdraht für „der einzige `open`" ist **entfallen** und durch
den letzten ersetzt; er zählte nie als eigener Test.

Anders als in den Runden 1 und 2 war **ein** Abnahmelauf nötig: die Selbstdurchsicht (`_coverage_of`
ohne Default für `walls`, `occupied_landings` als Pflichtschlüssel statt `.get`, der Satz über
`validate` im Wandzweig) ist **vor** dem Stempeln und vor dem Lauf passiert, nicht danach.

**Gespiegelt wurde nichts,** und das ist kein Auslassen: geändert sind `team-kits/kernel/migrate.py`,
`tools/test_migrate.py` und zwei Dokumente. Das Kernel-Paket liegt genau einmal unter
`team-kits/kernel/`; die Spiegelregel gilt für `team-kits/{dev,office,research}-team/`, und dort ist
außer den drei `VERSION`-Dateien (vom Stempler) keine Datei angefasst.

# Runde 4 (2026-08-09) — DEC-0024: die Familie wird abgeschafft, nicht weiter gejagt

Nachbesserung nach dem FAIL-Verdikt der Runde 3 (F1–F3 blockierend). **Was in den Abschnitten R1–R3
über `remedied_path` steht, ist Geschichte:** die Funktion existiert nicht mehr, und die Abschnitte
R2.2, R3.1 und R3.5 beschreiben einen Zustand, den DEC-0024 abgelöst hat. Sie bleiben stehen, weil
sie die Kette dokumentieren, die zu der Entscheidung geführt hat.

## R4.0 Sandbox dieser Runde

- Alle Sonden unter `C:\tmp-h23\`, also außerhalb des Repos **und** außerhalb des
  Heimatverzeichnisses. Jede ruft `_sandbox.pin(SANDBOX, <leaf>)`, behauptet danach ihre eigene
  Position (`assert _sandbox._inside(os.getcwd(), SANDBOX)`) **bevor** eine Nutzlast läuft, und
  läuft in `_sandbox.watch(REPO)`. Jeder Lauf dieser Runde meldete
  `457 protected files of C:\Offline Repos\AgentAndSkills unchanged`.
- Skripte: `probe_ast.py`, `probe_r4_coverage.py`, `make_clone.py`, `mutate4.py`,
  `mutate4_detail.py`, `probe_collision.py`, `probe_collision_before.py`.
- **Klon mit Historie, nach der letzten Codeänderung erzeugt:** `make_clone.py` klont das Repo
  (`git clone --no-hardlinks`, also die Historie, die `test_migrate` für den letzten V1-Monolithen
  braucht) nach `C:\tmp-h23\clone4` und legt danach den **Arbeitsbaum** darüber — der Änderungssatz
  dieses Branches ist nicht committet, ein reiner Historien-Klon würde den Code der Vorrunde messen.
- Keine ACL-Sperre war in dieser Runde nötig; nichts zurückzunehmen.

## R4.1 F3 — die Abhilfe schlägt keine Bewegung mehr vor (DEC-0024)

**Gemessener Befund der Runde 3, im Klon reproduziert** (`probe_collision.py` mit Mutation M1, also
der wiederhergestellten Ableitung aus dem Zustandsbaum):

```
  .legacy/old_procs.yaml           -> old_procs.yaml
  old_procs.yaml.bak               -> old_procs.yaml
  staging/PR-0001/old_procs.yaml   -> PR-0001/old_procs.yaml
  COLLISION: {'old_procs.yaml': ['.legacy/old_procs.yaml', 'old_procs.yaml.bak']}
  Quellen, deren Bytes wirklich am für sie genannten Platz liegen: 2 von 3
```

**Nach der Änderung, gleicher Zustand, gleiche Sonde:**

```
  .legacy/old_procs.yaml           -> staging/v1-deposit--.legacy%2Fold_procs.yaml
  old_procs.yaml.bak               -> staging/v1-deposit--old_procs.yaml.bak
  staging/PR-0001/old_procs.yaml   -> staging/v1-deposit--staging%2FPR-0001%2Fold_procs.yaml
  COLLISION: none
  Quellen, deren Bytes wirklich am für sie genannten Platz liegen: 3 von 3
```

**Was gebaut ist, als Konstruktion statt als Klausel** (`migrate.deposit_of`, `migrate.in_deposit`):
die Meldung nennt eine **Kopie** in eine Ablage unter `staging/`, deren Name aus dem Quellpfad
prozentkodiert abgeleitet ist. Ein Ziel dort ist nie eine Wand, nie kernel-geschrieben (`staging/`
ist in `layout.kernel_written_subtrees` nicht enthalten, geprüft im Test statt behauptet), und zwei
Zeilen eines Berichts können nicht denselben Namen nennen, weil `urllib.parse.quote` injektiv ist —
der Test führt `unquote` als Umkehrung aus.

**Was ersatzlos entfällt, weil es nur der Zielableitung diente:** `remedied_path` (66 Zeilen), der
Wandzweig in `_coverage_of`, die `remedy`-Hälfte jeder Bedingung in `_classify`, und der Parameter
`walls` von `search_coverage`/`_coverage_of` — der Vorlauf nennt keine Bewegung mehr, also gibt es
keine Bewegung, die er auf eine Wand richten könnte. Die Wandliste wird weiterhin **einmal** pro Lauf
gelesen, für die beiden Stellen, die wirklich eine Datei bewegen bzw. ihre Bytes lesen
(`absorbed_documents`, Wandabschnitt von `render`).

**Ein Defekt der eigenen Konstruktion, in der Selbstdurchsicht gefunden und gemessen:** `quote`
lässt den Punkt stehen, und auf diesem Host ist ein **abschließender Punkt kein Teil eines Namens**.
Gemessen: die zwei Namen `v1-deposit--foo.yaml.` und `v1-deposit--foo.yaml` sind **eine** Datei
(`os.listdir` gibt einen Eintrag zurück). Zwei lexikalisch verschiedene Ablageziele wären damit ein
Platz gewesen — dieselbe Kollision, nur eine Ebene tiefer, im Dateisystem statt im String. Der Punkt
wird deshalb mitkodiert (`.replace(".", "%2E")`, `unquote` kehrt es weiterhin um). Gemessen in beide
Richtungen im Test (M8: ohne die Kodierung `assert 1 == 2`, `['v1-deposit--procedures.yaml']`).

**Warum die Ablage ein Datei-NAME unter `staging/` ist und kein Verzeichnis:** ein Verzeichnis unter
`staging/` ist ein Staging-SCHLÜSSEL, und `report.validate_state` meldet jeden Schlüssel ohne
aktives Item als `orphaned staging dir`. Gemessen in beide Richtungen im Test
`test_the_deposit_an_instruction_names_is_no_staging_key_the_validator_reports`: die Datei erzeugt
keinen Befund, ein gleichnamiges Verzeichnis am selben Ort erzeugt einen.

**Der Preis, benannt statt verschwiegen:** die Meldung sagt nicht mehr, wohin eine Datei gehört,
damit der nächste Lauf sie durchsucht. Das steht so im Docstring von `_coverage_of`, in der
gedruckten Meldung selbst und im Spec-Nachtrag (e2).

**Idempotenz:** eine Ablagekopie ist selbst unter `staging/`, wird also weiterhin als NOT SEARCHED
benannt (die Totalität bleibt) — bekommt aber **keinen** Schritt genannt, sonst entstünde pro Lauf
eine Verschachtelungsebene. Gemessen im selben Test.

## R4.2 F1 — die zweite Richtung ist wieder da, und die Deckung ist gemessen

**Die Lücke:** die Audit-Hook-Messung ist total über die **Schreibweise** und nur über den Pfad, den
dieser eine Lauf läuft. Gemessen mit `sys.settrace` (`probe_r4_coverage.py`), gleiche Fixture wie
die Sonde: **439 von 819** Anweisungszeilen erreicht, 380 nicht. Ein zweiter Leser in einem nie
betretenen Zweig bleibt dort grün — gemessen als M3.

**Was gebaut ist:** `test_nothing_but_these_functions_can_name_a_file_of_the_state_directory` liest
die **Datei** (AST) und fragt, welche Funktionen einen Pfad unter der Zustandswurzel überhaupt
**benennen** können — einen Schritt vor jedem Öffnen. Das ist keine Aufzählung von Öffner-Namen
(daran ist die abgelöste Regel gestorben), sondern eine Definition: um eine Zustandsdatei zu lesen,
muss man sie erst benennen, und dafür gibt es in diesem Modul genau zwei Formen — den eigenen
Komponisten `_state_path` und einen Pfadbauer des Zustandsobjekts (`root`, `*_path`, `*_root`).

**Die Namensform ist selbst gemessen**, nicht angenommen:
`test_the_path_builders_of_the_state_object_all_carry_one_of_two_name_shapes` ruft jedes öffentliche
Mitglied von `ProjectState` auf und verlangt, dass jedes, das mit einem Pfad unter der Wurzel
antwortet, eine der beiden Schreibweisen trägt (M5: ein `scratch()` macht den Test rot).

**Beide Enden der unvermeidbaren Aufzählung** (die 14 Funktionen des Moduls): eine Funktion, die
einen Pfad komponiert und nicht in der Liste steht, ist rot (M3); ein Eintrag, der keinen mehr
komponiert, ist rot (M4).

**Wo sich die beiden treffen, gemessen:** alle **14** Funktionen, die die statische Regel benennt,
werden von genau dem Lauf betreten, den die Audit-Sonde macht. Dafür trägt die Fixture der Sonde
seit dieser Runde einen archivgebundenen Datensatz — ohne ihn war `archive_location` die eine
Funktion, die der Lauf nie betritt (gemessen: 13 von 14 vorher, 14 von 14 nachher; die Deckung stieg
dabei von 414/819 auf 439/819).

**Was nach beidem bleibt** und in `_read_bytes`, im Test-Docstring und in `L31` benannt ist: ein
zweiter Leser **innerhalb** einer der 14 Funktionen, in einem Zweig, den der Lauf nicht betritt.

## R4.3 F2 — der Riegel im Zug hat jetzt einen Test, der ohne ihn rot wird

**Der Befund:** `test_a_second_document_of_the_same_name_does_not_replace_the_one_already_retired`
baut seinen Plan, wenn der Landeplatz **schon** belegt ist — `plan_is_executable` verweigert dann
oben in `execute`, die Zugschleife wird nie erreicht. Gemessen als M6: ohne den `_is_occupied`-Riegel
in `_retire_absorbed_documents` bleibt dieser Test **grün**. Der Docstring behauptete beide Hälften;
er nennt jetzt die Naht.

**Was gebaut ist:** `test_the_move_asks_again_when_the_place_was_free_while_the_plan_was_built` —
Plan bauen, während der Platz frei ist (`occupied_landings == []`, `plan_is_executable` True), die
abgelegte Kopie danach zurücklegen, denselben Plan ausführen. Ergebnis: `MigrationError`, die
abgelegte Kopie unverändert (Hash gleich dem der Quittung des ersten Laufs), das Dokument steht noch
an seinem Platz. Ohne den Riegel: `DID NOT RAISE MigrationError` (M6).

**Und die Über-Behauptung in `L30` ist ersetzt.** Der Satz, die eigene Bewegung frage „unmittelbar
vor dem Schreiben … also dort, wo **keine Spanne** bleibt", war falsch: zwischen `_is_occupied`,
`os.makedirs` und `os.replace` liegen zwei Aufrufe, und `os.replace` hat keine no-clobber-Variante.
`L30` trägt jetzt diesen Mechanismus, die gemessene Kette (die Spanne wird deterministisch besetzt,
indem der Aufruf besetzt wird, der wirklich dazwischen liegt), das Urteil (offen, mit `os.replace`
nicht schließbar) und die Begrenzung (innerhalb einer Sitzung nicht erreichbar: `gate_write_scope`
verweigert jeden Werkzeug-Schreibzugriff unter `project_memory/` außerhalb `staging/`, und `legacy/`
ist kernel-geschrieben). Stolperdraht:
`test_the_move_replaces_a_file_that_appears_between_the_question_and_the_write`, rot an dem Tag, an
dem der Zug aufhört, ein blankes `os.replace` zu sein (M7).

## R4.4 Weitergesucht: gibt es noch eine gedruckte Aussage dieser Klasse?

Geprüft wurde jede gedruckte Aussage dieses Moduls, die eine Handlung des Lesers vorschlägt
(`grep` über alle `Remedy:`-Texte und alle Vorlauf-Sätze), gegen zwei Fragen: kann sie etwas
überschreiben oder verlieren, und schlägt sie eine Bewegung vor, obwohl Kopieren genügt?

| Stelle | Vorschlag | Urteil |
|---|---|---|
| `search_coverage`, `UNLISTABLE` | Leserecht geben **oder** das Verzeichnis aus dem Zustandsverzeichnis nehmen | **nennt kein Ziel**, kann also nichts überschreiben; Kopieren genügt nicht — das Verzeichnis muss aufhören, die Wanderung zu blockieren |
| `render`, belegter Landeplatz | die Datei unter `legacy/` aus dem Zustandsverzeichnis nehmen | dito; der Platz muss frei werden, eine Kopie tut das nicht |
| `_retire_absorbed_documents`, Verweigerung | dieselbe Bewegung | dito |
| Kollisions-Verweigerung (`legacy_id` doppelt) | das Dokument aus dem Zustandsverzeichnis nehmen **oder** im V1-File eine eigene Id geben | nennt kein Ziel; die Bearbeitung betrifft die eigene V1-Datei des Lesers |
| „schon importiert unter neuem Pfad" | die Kopie aus dem Zustandsverzeichnis nehmen | dito |
| oversized record | Decision-Item, Datensatz im V1-File teilen **oder** seinen Umfang nach `staging/` bewegen | nennt ein Verzeichnis, keinen Dateinamen; Kopieren genügt hier **nicht** — der Umfang muss aus dem Item verschwinden, sonst bleibt es zu groß. **Nicht geändert, hier benannt.** |
| `unresolved` | Feld im V1-File ergänzen oder `--map` | Bearbeitung der eigenen Quelle, kein zweiter Pfad |

Keine weitere Stelle nennt ein **abgeleitetes Ziel**. Die einzige, die überhaupt einen Ort nennt
(`staging/` beim oversized record), nennt ihn ohne Dateinamen und ist inhaltlich eine
Umfangsreduktion, keine Verlagerung eines Speichers — sie steht hier, damit die Entscheidung
sichtbar ist statt still.

## R4.5 Rotmessungen (Klon `C:\tmp-h23\clone4`, mit Historie, Kontrolle im selben Klon)

Kontrolle vor jeder Mutation: **9 bestanden**. Jede Mutation einzeln angewandt, Test gefahren,
Datei danach aus dem Original zurückgeschrieben; Abschlusskontrolle nach der letzten Rücknahme
wieder grün.

| # | wiederhergestellter Defekt | Test | rc |
|---|---|---|---|
| M1 | Ziel wieder aus dem Zustandsbaum abgeleitet | `test_no_instruction_this_command_prints_can_take_a_file_away` | **1** |
| M1 | dasselbe, Quell-Ende | `test_a_document_a_registered_gate_reads_is_offered_no_way_to_move_or_rename_it` | **1** |
| M2 | Ablage als Verzeichnis unter `staging/` | `test_the_deposit_an_instruction_names_is_no_staging_key_the_validator_reports` | **1** |
| M3 | zweiter Leser in `render`s WALLS-Zweig | `test_nothing_but_these_functions_can_name_a_file_of_the_state_directory` | **1** |
| M3 | derselbe Defekt, andere Regel | `test_every_state_file_this_module_opens_it_opens_through_read_bytes` | **0 (grün)** |
| M4 | toter Eintrag in der Funktionsliste | `test_nothing_but_these_functions_can_name_a_file_of_the_state_directory` | **1** |
| M5 | `ProjectState.scratch()` — Pfadbauer in anderer Schreibweise | `test_the_path_builders_of_the_state_object_all_carry_one_of_two_name_shapes` | **1** |
| M6 | `_is_occupied`-Riegel im Zug entfernt | `test_the_move_asks_again_when_the_place_was_free_while_the_plan_was_built` | **1** |
| M6 | derselbe Defekt, alter Test | `test_a_second_document_of_the_same_name_does_not_replace_the_one_already_retired` | **0 (grün)** |
| M7 | Zug auf no-clobber umgestellt (`os.link` + `remove`) | `test_the_move_replaces_a_file_that_appears_between_the_question_and_the_write` | **1** |
| M8 | Punkt im Ablagenamen wieder unkodiert | `test_no_instruction_this_command_prints_can_take_a_file_away` | **1** |

Die beiden **grünen** Zeilen sind keine Ausfälle, sondern die zwei Behauptungen dieser Runde: die
Audit-Regel sieht einen Leser in einem nie betretenen Zweig nicht (deshalb die statische Regel
daneben), und der alte Zug-Test erreicht die Zugschleife nicht (deshalb der neue). Beide stehen so
in den Docstrings, die sie betreffen.

Die Meldungen im Wortlaut (`mutate4_detail.py`), gekürzt:

```
M1  .approvals/consumed/old_procs.yaml: the instruction names consumed/old_procs.yaml,
    which is outside the area this command owns
M2  the deposit this command's own instruction names is reported as an orphaned staging key:
    [{'item': 'staging/v1-deposit', 'message': 'orphaned staging dir ...'}]
M3  these parts of `migrate.py` can name a file of the state directory and are not accounted
    for ...: {'render': [('_state_path', 2334)]}
M4  these names carry a licence to compose a state path and compose none ...: ['render']
M5  `ProjectState` names a path builder in a shape `migrate.py`'s static rule cannot see ...:
    ['scratch']
M6  Failed: DID NOT RAISE MigrationError
M7  kernel.migrate.MigrationError: the import stopped after writing 1 ...
M8  two sources are given two deposit names and this filesystem makes one file of them:
    ['v1-deposit--procedures.yaml']
```

## R4.6 Was diese Runde NICHT geschlossen hat

- **`L30`** — die Spanne zwischen `_is_occupied` und `os.replace` im eigenen Zug. Offen, mit
  Mechanismus, gemessener Kette, Urteil und Begrenzung im Eintrag. Ein no-clobber-Zug bräuchte
  `os.link` + `unlink` statt `os.replace`; das ist ein anderer Zug mit anderen
  Dateisystem-Voraussetzungen und wurde hier nicht gebaut.
- **`L31`** — zwei Reste: die Fremdbibliothek-Zurechnung (unverändert) und die Deckung des
  Audit-Laufs (439/819), die jetzt von der statischen Regel gedeckt ist. Was nach beidem bleibt,
  steht im Eintrag.
- **Die Länge des Ablagenamens.** Ein Quellpfad, dessen prozentkodierter Name länger wird, als das
  Dateisystem zulässt, erzeugt einen Namen, den der Leser nicht anlegen kann. Kürzen oder Hashen
  würde die Injektivität kosten, also genau die Eigenschaft, für die die Konstruktion da ist; das
  steht im Docstring von `deposit_of` als Eigenschaft der Konstruktion. **Nicht gemessen**, deshalb
  kein Löcherlisten-Eintrag — dort steht nur Gemessenes.
- **Der oversized-Hinweis** (`move its bulk to `staging/``) — geprüft, begründet stehen gelassen,
  in R4.4 benannt.

## R4.7 Abnahmelauf der Runde 4

- `python -m ruff check .` → sauber
- `python tools/bump_kit_version.py` → alle drei Kits auf `2026.08.09-3` (vor der Suite gefahren,
  die Suite lief auf dem gestempelten Baum)
- `python tools/validate.py` → `all structural checks passed.`
- `python -m pytest tools/ -q` → **2326 bestanden, 12 übersprungen, 0 rot, in einem Lauf**
  (25:35, exit 0)

Es waren **zwei** Abnahmeläufe nötig, und der Grund steht in R4.1: die Selbstdurchsicht fand den
Punkt-Fold der eigenen Konstruktion nach dem ersten Lauf (`-2`, ebenfalls 2326/12, 24:51). Der
zweite Lauf ist der gestempelte (`-3`).

Runde 3 schloss mit 2322/12. Die Differenz von **+4** ist die Bilanz dieser Runde: **entfallen** sind
`test_every_remedy_the_run_up_prints_lands_on_a_file_it_really_searches` und
`test_no_remedy_this_command_prints_lands_on_a_file_that_is_already_there` (beide messen eine
Zielableitung, die es nicht mehr gibt), **neu** sind
`test_no_instruction_this_command_prints_can_take_a_file_away`,
`test_the_deposit_an_instruction_names_is_no_staging_key_the_validator_reports`,
`test_nothing_but_these_functions_can_name_a_file_of_the_state_directory`,
`test_the_path_builders_of_the_state_object_all_carry_one_of_two_name_shapes`,
`test_the_move_asks_again_when_the_place_was_free_while_the_plan_was_built` und
`test_the_move_replaces_a_file_that_appears_between_the_question_and_the_write` (alle in
`tools/test_migrate.py`).

**Gespiegelt wurde nichts,** und das ist kein Auslassen: geändert sind `team-kits/kernel/migrate.py`,
`tools/test_migrate.py` und drei Dokumente. Das Kernel-Paket liegt genau einmal unter
`team-kits/kernel/`; die Spiegelregel gilt für `team-kits/{dev,office,research}-team/`, und dort ist
außer den drei `VERSION`-Dateien (vom Stempler) keine Datei angefasst.

# Runde 5 (2026-08-09) — nach dem FAIL-Verdikt zu Runde 4 (B1, B2 blockierend; B3–B5 Reste)

## R5.0 Sandbox dieser Runde

- Alle Sonden unter `C:\tmp\tsk0023r5\`, der Rotmess-Klon unter `C:\tmp\r5clone\` — beide außerhalb
  des Repos. Jede Sonde bekommt ihr Ausgabeziel relativ zu ihrer **eigenen** Datei
  (`os.path.dirname(__file__)`), schreibt also nirgendwo anders hin.
- Geschützte Dateien des echten Repos **vor und nach** allen Messläufen gehasht (`hashes.py`, 535
  Dateien unter `.claude/`, `tools/`, `team-kits/`, `docs/`, `project_memory/`). Verändert sind genau
  acht: `team-kits/kernel/migrate.py`, `team-kits/kernel/report.py`, `tools/test_migrate.py`,
  `docs/POST_V2_WISHLIST.md`, die drei `VERSION`-Dateien und `project_memory/.audit/hook_events.jsonl`
  (das schreiben die Gates selbst). **Kein** `.claude/`, **kein** kanonischer Zustand.
- Der Klon trägt die Historie (`.git` mitkopiert), weil die `v1_state`-Fixture den letzten
  V1-Monolithen aus ihr holt; ohne sie fallen 93 Tests mit „git could not read this repository's
  history" aus und jede Rotmessung an ihnen wäre wertlos.
- Sonden: `cite3.py` (Zitat-Auflösung), `audit_remedies.py` / `tokens.py` / `remlit.py`
  (Abhilfe-Bestandsaufnahme), `len.py` / `len2.py` (Namenslänge), `brief.py` (Sitzungs-Kurzinfo),
  `handoff.py` (weitergereichter Pfad), `red*.py` (Rotmessungen), `show.py` (gedruckte Meldung).

## R5.1 B1 — die Restaussage war falsch, und ein echter zweiter Leser blieb grün

**Der Befund, im Klon reproduziert.** Die 14er-Liste war die Aufzählung der Funktionen, die einen Pfad
**lexikalisch nennen**. `_unreadable_because(exc, path)` und `_without_path(text, path)` bekamen den
fertigen Pfad als Argument, nannten nichts, lagen im Fehlerzweig — und der Audit-Lauf betrat den Zweig
nie. Mit dem **kompletten Vorzustand** (alte Signaturen, alte Lizenzliste, ohne die dritte Zusicherung,
ohne das Fehlleseglied der Sonde) und einem echten, ungehandelten zweiten Leser
(`io.open(path, "rb").read()`) in `_unreadable_because`:

```
BEFORE-STATE + a real second reader, die zwei Wächter  ->  rc 0, 2 passed
```

**Gebaut ist der Fix, den der Prüfer benannt hat, plus die Eigenschaft dahinter.** Beide Funktionen
nehmen jetzt `(state, rel)` und komponieren mit `_state_path` selbst; `_without_path` steht damit in
`_NAMES_A_STATE_FILE`, `_read_document` fällt heraus (es komponiert nichts mehr — die
Tote-Einträge-Hälfte der Regel hat das gemeldet, bevor ich es von Hand fand). Damit die Regel eine
**Definition** statt einer neuen Liste ist, hält eine dritte Zusicherung im selben Test die
Eigenschaft: *kein Aufruf dieses Moduls reicht einen komponierten Zustandspfad an eine andere Funktion
desselben Moduls weiter* (`_handed_a_finished_path`, heute 0 Treffer).

```
NEW signature + derselbe Leser                          ->  rc 1, 2 failed
nur die Signaturen zurück (ohne Leser)                  ->  rc 1, 1 failed
```

**Und die Mitte ist keine Prosa mehr.** Die Behauptung „alle lizenzierten Funktionen werden von genau
diesem Lauf betreten" stand als Satz im Docstring; sie ist jetzt eine Zusicherung desselben Tests: die
Sonde sammelt per `sys.settrace` die betretenen Funktionen von `migrate.py`, und der Test verlangt,
dass jede lizenzierte darunter ist (und dass der Lauf mehr betritt als nur diese, sonst sagt der Satz
nichts). Damit der Fehlerzweig überhaupt gelaufen wird, plant die Sonde nach dem Lauf ein unparsbares
Dokument.

```
Sonde ohne das Fehlleseglied                            ->  rc 1, 1 failed
```

**Deckungszahl.** „439 von 819" stand an drei ausgelieferten Orten, nannte seine Zählregel nicht (der
Prüfer kam mit eigener Regel auf 496 von 890) und wurde von keinem Test gehalten. Sie ist **ersatzlos
entfernt**; was sie belegen sollte, ist jetzt die Zusicherung oben.

## R5.2 B2 — `staging/` als Ziel ist weg, und die Prüfung ist produktbreit

**Die Kette, die durchläuft:** `gate_write_scope` antwortet auf eine **bestehende** Datei unter
`staging/` mit rc 0 — `staging/` ist die einzige Ausnahme unter `project_memory/`. Ein befolgtes
„move its bulk to `staging/`" überschreibt also **innerhalb** der Sitzung, und *move* nimmt zusätzlich
den Umfang aus der V1-Datei. Der Prüfer hat recht: das sind zwei Handlungen.

**Gebaut:** `record_deposit_of(rel, legacy_id)` — derselbe Kodierer wie `deposit_of`, kodiert wird
`<Dokument>/<Datensatz-Id>`. Der Name kann mit keinem Dokumentnamen desselben Zustands kollidieren,
weil ein Dokument eine **Datei** ist und kein Pfad dieses Zustands eine Datei als Verzeichnisglied hat
(im Test gegen **alle** Dokumente des Zustands geprüft, nicht gegen eines). `copy_instruction(target)`
ist der **eine** Bauplan beider gedruckter Anweisungen; das Kürzen geschieht in der **eigenen
V1-Datei** des Lesers.

Vorher/nachher, gedruckt:

```
vorher:  the item would be 80452 bytes / 25 lines; ... as an error does not fit in one item:
         an item REFERENCES its detail, ... Remedy: record a Decision item, split the record in
         the V1 file or move its bulk to `staging/`, then re-run the dry run.
nachher: it does not fit in one item: it would be 80452 bytes / 25 lines; ... as an error. An item
         REFERENCES its detail and this V1 record inlines it, so the bulk belongs beside the item
         rather than in it. Remedy: COPY it -- the original stays where it is -- to
         `staging/v1-deposit--bulky%2Eyaml%2FPROC-0811`. Then shorten the record in the V1 file
         itself so that it points at that copy, and re-run the dry run.
```

Damit ist auch der Nebenbefund weg: `_too_large` lieferte einen ganzen Satz in ein `%s` mitten im Satz
(„…as an error does not fit in one item: …").

**Produktbreit statt modulbreit, in beide Richtungen gemessen:**

- **ausgeführt** — `report.validate_state` auf einem Zustand, der ihre Abhilfen erreicht: **keine** von
  ihnen nennt einen Ort innerhalb des Zustandsverzeichnisses (sie schicken hinaus oder zu einem
  Kommando). Dass der Leser dabei nicht blind ist, wird im selben Test an der einen Stelle gemessen,
  die wirklich einen Ort nennt: der Anweisung des Trockenlaufs.
- **statisch über alles Ausgelieferte** — jede Zeichenkette unter `team-kits/`, die `Remedy:` trägt
  (**221** gemessen), darf keinen Ort innerhalb eines Zustandsverzeichnisses in Backticks nennen. Die
  Segmente kommen aus `layout.kernel_written_subtrees` + `STAGING_DIRNAME`, nicht aus einer Liste.
  Heute: 0 Treffer; mit dem alten Satz: 1.

```
B2  die Übergroß-Abhilfe zurück auf `staging/`          ->  rc 1, 2 failed (1 passed)
```

Der eine Bauplan hat seinen eigenen Stolperdraht: die Wendung darf in allem Ausgelieferten **genau
einmal** vorkommen, sonst gilt, was `copy_instruction` zusichert, nicht für die zweite Stelle.

## R5.3 B3 — die Längengrenze ist jetzt gemessen und als `L32` geführt

Auf diesem Host: längster anlegbarer Namensteil **255** Zeichen, 256 antwortet
`OSError: [Errno 22] Invalid argument`. Eine Quelldatei aus **248** ASCII-Zeichen wird angelegt, ihr
Ablagename ist **262** Zeichen und ist nicht anlegbar; **29 CJK**-Zeichen ergeben 235, **43
kyrillische** 247. `deposit_note` sagt es jetzt dort, wo der Name gedruckt wird — um wie viele Zeichen
zu lang, dass dieses Dateisystem ihn nicht nimmt, und dass es keinen kürzeren gibt und warum. Der
Stolperdraht **koppelt** die Konstante ans Dateisystem, statt sie nachzuerzählen: er legt die Namen
wirklich an und verlangt, dass der Satz genau dann erscheint, wenn das Anlegen scheitert.

```
B3  die Längenklausel entfernt                           ->  rc 1, 1 failed
```

## R5.4 B4 — die Sitzungs-Kurzinfo las den Ablagenamen als Verzeichnis

```
vorher:  staging_pointers: ['staging/.gitkeep/', 'staging/PR-0001/',
                            'staging/v1-deposit--old_procs%2Eyaml%2Ebak/']
nachher: staging_pointers: ['staging/PR-0001/']
```

Derselbe `os.path.isdir`-Filter, den `validate_state` schon hatte. Der Test fragt seitdem **beide**
Leser dieselbe Frage, und der Kommentar an `_DEPOSIT_MARK` behauptet nicht mehr eine Autorität.

```
B4  der Filter entfernt                                  ->  rc 1, 1 failed
```

## R5.5 B5 — nicht das eine Wort, sondern die Kopplung

`test_every_test_the_shipped_code_cites_by_name_is_a_test_that_exists`: jeder Testname, den
**ausgelieferter** Code (`team-kits/`) in Backticks nennt, wird gegen die geparsten Testmodule
aufgelöst — Modulnamen sind keine Zitate, über zwei Zeilen umbrochene Namen werden zusammengefügt
(Tokens und Knoten, nicht Zeilen). Gemessen: **86** Zitate im Ausgelieferten, genau eines hing
(`test_the_deposit_a_remedy_names_…`). Die Suite selbst ist nicht in der Domäne, und der Grund ist
gemessen und benannt: `tools/test_hooks.py` trägt einen **Nachruf** auf einen absichtlich entfernten
Test, und einen Nachruf soll keine Regel von einem Zitat unterscheiden müssen.

```
B5  das alte Zitat zurück                                ->  rc 1, 1 failed
```

## R5.6 Was diese Runde NICHT geschlossen hat

- **`L30`** — die Spanne zwischen `_is_occupied` und `os.replace` im eigenen Zug. Unverändert offen,
  mit Urteil und Begrenzung im Eintrag.
- **`L31`** — die Fremdbibliothek-Zurechnung. Unverändert offen; der zweite Rest („der Lauf betritt nur
  einen Teil") ist durch die Zusicherung aus R5.1 auf „ein zweiter Leser **innerhalb** einer
  lizenzierten Funktion, in einem Zweig, den der Lauf nicht betritt" zusammengeschnitten.
- **`L32` (neu)** — die Länge des Ablagenamens. Nicht schließbar, ohne die Injektivität zu opfern,
  gegen die DEC-0024 gebaut ist; ein zweistufiger Name machte die Ablage zu einem Staging-Schlüssel.
  Urteil, Kette und Begrenzung stehen im Eintrag.
- **Die Domäne des Zitat-Kopplungstests** ist das Ausgelieferte, nicht die Suite. Das ist eine benannte
  Grenze, kein Versehen — siehe R5.5.

## R5.7 Abnahmelauf der Runde 5

- `python tools/bump_kit_version.py` → alle drei Kits auf `2026.08.09-5` (**nach** der letzten
  Codeänderung, die Suite lief auf dem gestempelten Baum)
- `python -m ruff check .` → `All checks passed!`
- `python tools/validate.py` → `all structural checks passed.`
- `python -m pytest tools/ -q` → **2332 bestanden, 12 übersprungen, 0 rot, in einem Lauf**
  (25:12, exit 0)

Es waren **zwei** volle Läufe, und der Grund ist genannt statt verschwiegen: der erste (24:35,
ebenfalls 2332/12) lief, bevor die Selbstdurchsicht zwei Zahlen aus einem Docstring von
`tools/test_migrate.py` nahm („die anderen vierzehn Zitate", „sechzig-und-ein-paar") und dort eine
Zusicherung ergänzte. Der **zweite** Lauf ist der, der oben steht; der Kit-Stempel ist zwischen beiden
`unchanged` geblieben, weil `tools/` nicht in den Kit-Hash eingeht.

Runde 4 schloss mit 2326/12. Die Differenz von **+6** sind sechs neue Tests, alle in
`tools/test_migrate.py`: `test_every_test_the_shipped_code_cites_by_name_is_a_test_that_exists`,
`test_the_place_an_oversized_record_is_sent_to_is_constructed_and_costs_nothing`,
`test_no_remedy_the_validator_prints_names_a_place_inside_the_state_directory`,
`test_no_remedy_this_repo_ships_names_a_place_inside_a_state_directory`,
`test_a_deposit_name_too_long_to_create_says_so_where_it_is_printed` und
`test_the_instruction_this_module_prints_has_exactly_one_composer`. Umbenannt (nicht neu) ist
`test_the_deposit_an_instruction_names_is_no_staging_key_either_reader_reports`.

**Gespiegelt wurde in Runde 5 nichts,** und das ist kein Auslassen: geändert sind
`team-kits/kernel/migrate.py`, `team-kits/kernel/report.py`, `tools/test_migrate.py` und
`docs/POST_V2_WISHLIST.md`. Das Kernel-Paket liegt genau einmal unter `team-kits/kernel/`; die
Spiegelregel gilt für `team-kits/{dev,office,research}-team/`, und dort ist außer den drei
`VERSION`-Dateien (vom Stempler) keine Datei angefasst.

# Runde 6 — F1, F2, F3, N1, N2 (2026-08-09)

Prüfverdikt der Runde 5: FAIL. Zwei blockierend (F1, F2), ein Rest mit Auflage (F3), zwei
Korrekturen (N1, N2). Alle Rotmessungen unten laufen in einem Klon **außerhalb** dieses Repos
(`C:\probe\tsk0023r6\clone`, robocopy-Kopie inkl. `.git`, weil die `v1_state`-Fixture die Historie
liest); die Sonden stehen daneben und stellen jede angefasste Datei im `finally` wieder her.

## R6.1 F1 — die dritte Zusicherung fragte die Aufrufsyntax, nicht den Wert

`_handed_a_finished_path` sah nur Aufrufe mit blankem `ast.Name`-Callee einer modul-eigenen Funktion
und nur eine Komposition, die syntaktisch im Argumentausdruck steht. Ersetzt durch einen
**Vorwärts-Taint über den Wert**: `_carries_a_state_path` folgt dem, was ein Name hält; die
Callee-Form wird nur noch gelesen, um zu beantworten, **wer** empfängt (`_root_name`). Die einzige
Stelle, an der der Fluss endet, ist ein Aufruf in den **eigenen** Code dieser Datei — dort entscheidet
die Lizenzliste; `_relative` ist lizenziert und antwortet mit einem zustandsrelativen Namen,
`_state_path` ist selbst Quelle. Dazu neu: eine **abgelegte** Modulvariable (`global`) ist eine dritte
Quelle (`_stashed_names`), sonst verlässt der Pfad die Funktion, ohne übergeben zu werden.

Gemessen an einem Leser, der wirklich Zustandsbytes liest (Kernel-Kopie in `tmp`, echter Prozess,
Marker-Datei), je Route: der Leser bekommt die Bytes **und** die Regel nennt den Halter.

```
route                              Halter                 ALT (Aufrufsyntax)  NEU (Wertfluss)
baseline                           -                      []                  []
in the argument itself             _a_second_reader       SEEN                SEEN
through a local name               _a_second_reader       blind               SEEN
through a computation              _a_second_reader       blind               SEEN
beside the reader in a wrapper     _a_second_reader       blind               SEEN
through a member of this module    _SIDECAR               blind               SEEN
parked in a name of the module     _a_reader_of_the_stash blind               SEEN
```

**Rot ohne den Fix** (alte Regel + alte Produktzeile zurück, Klon außerhalb):

```
F1  alte Regel zurueck  ->  rc 1, 1 failed, 1 passed
    test_the_rule_against_handing_a_state_path_on_follows_the_value_and_not_the_call_shape
    "a state path travels beside the reader in a wrapper into `_a_second_reader` and the rule
     does not name it"
```

**Eine Produktzeile ist mitgegangen**, und der Grund ist derselbe, den `_unreadable_because` schon
trägt: in `search_coverage` parkte der Fallback `str(state.root)` in einer lokalen Variablen, aus der
`rel` gespeist wird — für den Wertfluss sah damit jeder spätere Gebrauch von `rel` wie ein
weitergereichter Pfad aus. Der Fallback geht jetzt durch `_relative`. Verhaltensgleich, weil
`ProjectState.__init__` `root` über `os.path.abspath` absolut macht (`kernel/state.py`).

**Vier Sätze korrigiert**, die die Eigenschaft in voller Breite behaupteten:
`tools/test_migrate.py` (Docstring von `_handed_a_finished_path`, dritter Absatz von
`test_nothing_but_these_functions_can_name_a_file_of_the_state_directory`) und
`team-kits/kernel/migrate.py` (`_read_bytes`). Neu benannter Rest, weil er wirklich offen ist: ein
Aufruf, der den eigenen Code erreicht, ohne ihn zu **nennen** (`sys.modules`, `getattr`, ein sofort
angewandtes Lambda) — deliberat, nicht der geradeaus naheliegende Weg (DEC-0022).

## R6.2 F2 — der Ablagename war nicht faltungsinjektiv

`quote(rel, safe="").replace(".", "%2E")` schloss **eine** Faltung (den abschließenden Punkt). Die
Groß-/Kleinschreibung blieb offen und ist über Datensatz-Ids erreichbar, weil ein YAML-Schlüssel
case-sensitiv ist und dieses Dateisystem nicht.

Ersetzt nicht durch eine dritte Fluchtform, sondern durch das **Alphabet**
(`migrate._NAME_ALPHABET`): Kleinbuchstabe, Ziffer, `-`, `_`; alles andere — der Großbuchstabe, der
Punkt, der Schrägstrich, das Leerzeichen, `%` selbst, jedes Nicht-ASCII-Byte — wird zu `%xx` in
**Kleinhex**. Auf jedem Zeichen des Ergebnisses ist die Faltung dieses Dateisystems die Identität,
und `urllib.parse.unquote` liest die Kodierung weiterhin zurück (invertierbar, also injektiv).

Gemessen (Korpus aus drei Subjekten × fünf Faltungen, Namen **wirklich angelegt**):

```
Modell `_folded` gegen das Dateisystem, 10 Paare eines Subjekts: 0 Abweichungen, 6 Paare gefaltet
NFD/NFC faltet dieses Dateisystem NICHT -- das Modell sagt dasselbe
12 unterscheidbare Quellen -> 12 Ablagedateien
```

**Rot ohne den Fix** (alter Kodierer zurück, Klon außerhalb):

```
F2  quote(...).replace(".", "%2E") zurueck  ->  rc 1, 2 failed, 4 passed
    test_two_sources_this_filesystem_would_fold_together_get_two_deposits
      "12 sources this filesystem tells apart were given deposit names it does not"
    test_two_records_of_one_document_that_differ_only_in_case_get_two_deposits
      "one report printed 2 instructions and this filesystem holds 1 file(s) afterwards"
      ['...%2FPROC-0811a', '...%2FPROC-0811A'] -> ['v1-deposit--bulky%2Eyaml%2FPROC-0811a']
```

Die zweite dieser Messungen ist die Kette des Prüfers, end-to-end: echter Trockenlauf, zwei
blockierte Datensätze, beide Anweisungen ausgeführt, eine Datei übrig.

**Der Korpus hätte den Defekt fast nicht gesehen**, und das ist selbst eine Messung: mit einem
einzigen akzentbehafteten Subjekt bestand der alte Kodierer den neuen Test, weil das Großschreiben
dort auch die Flucht des Akzents ändert und die Namen aus Versehen auseinanderbleiben. Darum sind es
**drei** Subjekte, eines davon rein ASCII, und der Grund steht bei `_FOLDING_SUBJECTS`.

## R6.3 F3 — Name und Satz auf die gebaute Domäne eingeengt

`test_no_remedy_this_repo_ships_…` heißt jetzt `test_no_remedy_literal_this_repo_ships_…`; der Satz
"this one reads every string the shipped code can print" sagt jetzt **Zeichenketten-Konstanten**. Die
zwei zur Laufzeit zusammengesetzten Abhilfen (`kernel/state.py`, `kernel/approvals.py`, beide
`git restore <Zustandspfad>`) stehen als `L33` in `docs/POST_V2_WISHLIST.md` mit Mechanismus, Kette
und Urteil. Dass die Kette eine Shell **außerhalb** der Sitzung braucht, ist gemessen statt
angenommen — die gedruckte Zeile selbst, als echter Hook-Prozess mit JSON auf stdin:

```
gate_lead_write_scope (dieses Repo)              git restore project_memory/... -> rc 2
gate_write_scope (dev/office/research, je frisch scaffoldetes Projekt)          -> rc 2
```

## R6.4 N1 und N2

- **N1:** der Zitat-Kopplungstest löst **86** Zitate auf, nicht 80. Nachgemessen mit den Helfern des
  Tests selbst (`_tests_of_this_suite`, `_prose_of`, `_A_CITATION`), verteilt über 38 Dateien unter
  `team-kits/`; die Zahl in R5.5 ist korrigiert. Die Zusicherung im Test bleibt `> 50` — eine exakte
  Zahl dort wäre genau die Konstante, die eine Runde später nicht mehr stimmt.
- **N2:** `deposit_note` misst die Namenskomponente, nicht den Gesamtpfad. Auf diesem Host nicht
  erreichbar — gemessen außerhalb dieses Repos: Gesamtpfade von 261, 271, 321, 401, 451 und 520
  Zeichen werden alle angelegt, Namenskomponente jeweils unter 255. Halbsatz in `L32`, keine Runde.

## R6.5 Nebenbeobachtung: kleingeschriebenes Typpräfix

`proc-0811` erzeugt keine Planzeile — **gewollt und schon dokumentiert**. `migrate.V1_ID_RE` verlangt
`[A-Z]{2,4}`, und der Absatz "THE COUNTER-DIRECTION" direkt darüber nennt den Grund samt Beispielen
(`unavailable_503`, `tablet_768` in einem echten `design.yaml` sind ein Bildschirmzustand und eine
Breakpoint-Breite, keine Ids); gemessen wird es von der Stelle in `tools/test_migrate.py`, die genau
diese beiden Schlüssel in ein Dokument schreibt. Eigene Messung 2026-08-09:

```
V1_ID_RE:  PROC-0811 True | proc-0811 False | PROC-0811a True | Proc-0811 False
Plan:      PROC-0811, PROC-0811a  --  proc-0811 kommt nicht vor
Coverage:  procedures.yaml -> searched
```

Der Rest, den das lässt: ein V1-Speicher, der seine Ids **durchgehend** klein tippt, wird nicht
importiert, während sein Dokument als `searched` gilt. Ich habe dafür **keinen** Löcherlisten-Eintrag
angelegt: das ist die Definition von "id-förmig", nicht eine Lücke darin, und ein Eintrag hier wäre
eine Alarm-Behauptung über eine getroffene Entscheidung. Sieht der Prüfer das anders, ist es ein
Eintrag und keine Codeänderung.

## R6.6 Abnahmelauf der Runde 6

- `python tools/bump_kit_version.py` → alle drei Kits auf `2026.08.09-6`; ein zweiter Aufruf **nach**
  der letzten Codeänderung antwortete `unchanged`, der Lauf unten lief also auf dem gestempelten Baum
- `python -m ruff check .` → `All checks passed!`
- `python tools/validate.py` → `all structural checks passed.`
- `python -m pytest tools/ -q` → **2335 bestanden, 12 übersprungen, 0 rot, in EINEM Lauf**
  (25:26, exit 0)

Runde 5 schloss mit 2332/12. Die Differenz von **+3** sind drei neue Tests, alle in
`tools/test_migrate.py`:
`test_the_rule_against_handing_a_state_path_on_follows_the_value_and_not_the_call_shape`,
`test_two_sources_this_filesystem_would_fold_together_get_two_deposits` und
`test_two_records_of_one_document_that_differ_only_in_case_get_two_deposits`. Umbenannt (nicht neu)
ist `test_no_remedy_literal_this_repo_ships_names_a_place_inside_a_state_directory`.

`.claude/hooks/test_gates.py` ist **nicht** vollständig gefahren, und der Grund ist benannt: diese
Runde fasst keinen Gate-Hook und keine `.claude/`-Datei an. Gefahren ist daraus der eine Test, der
die von dieser Runde geänderte Datei liest —
`test_every_reference_to_a_measurement_leads_to_one` über `docs/POST_V2_WISHLIST.md`, 1 bestanden.

**Gespiegelt wurde in Runde 6 nichts,** aus demselben Grund wie in Runde 5: geändert sind
`team-kits/kernel/migrate.py`, `tools/test_migrate.py`, `docs/POST_V2_WISHLIST.md`,
`docs/HARNESS_V2_SPEC.md` und dieses Protokoll. Das Kernel-Paket liegt genau einmal unter
`team-kits/kernel/`; unter `team-kits/{dev,office,research}-team/` ist außer den drei
`VERSION`-Dateien (vom Stempler) keine Datei angefasst.

**Dieses Protokoll ist nach dem Abnahmelauf geschrieben.** Das ist absichtlich und folgenlos: von
`docs/reviews/` liest nur `phase0-disposition.md` in die Suite hinein (`tools/test_disposition.py`,
`tools/parity_sources.py`, `tools/test_shortening_net.py`, `tools/test_context_budget.py`,
`tools/record_lead_package_sizes.py`), und diese Datei ist keine davon. Ein zweiter voller Lauf hätte
darum nichts gemessen, was der erste nicht schon gemessen hat.

# Runde 7 — F1, F2, F3 (2026-08-09)

Prüfverdikt der Runde 6: FAIL. Zwei blockierend (F1, F2), ein Rest (F3). Sandkasten dieser Runde:
`C:\tsk0023-r7\repo` (Kopie von `team-kits/` und `tools/` **ohne** `.git`, darum fällt dort der eine
Test aus, dessen Fixture die Historie liest — er läuft im Abnahmelauf im Repo mit), Sonden daneben
unter `C:\tsk0023-r7\`. Die ext4-Messung läuft in WSL auf `/tmp`; dort fehlt `pytest`, darum steht
neben der Sonde ein **Stub** mit genau den drei Namen, die `tools/test_migrate.py` von pytest
benutzt (`fail`, `fixture`, `raises`) — die Testfunktion selbst läuft unverändert.

## R7.1 F1 — die Regel folgte dem Pfad und las den Empfänger weiter aus der Syntax

Zwei Blindheiten, beide gemessen an einem Leser, der wirklich Zustandsbytes zurückgibt (Kernel-Kopie
in `tmp`, echter Prozess, Markerdatei):

- **Die Ablage** war an `ast.Global` gebunden. Ein *Store*, dessen Ziel ein Attribut, ein Mapping
  oder eine Liste dieses Moduls ist, bindet keinen Namen und übergibt nichts — beide Hälften der
  Regel schwiegen. `_stashed_names` fragt jetzt den **Wurzelnamen des Ziels**: ein bloßer Name zählt
  mit `global`, ein Attribut oder Subscript zählt, wenn seine Wurzel ein Name dieses Moduls ist.
- **Der Empfänger** kam aus `_root_name(node.func)`. Ein lokaler Alias (`reader = _a_second_reader`)
  versteckte ihn vollständig. Neu ist `_stands_for`, das Spiegelbild von `_carries_a_state_path`:
  es folgt dem **Wert** des Empfängers durch die Locals (`_aliases_in`, Fixpunkt) und hört genau
  dort auf, wo der Wert das **Ergebnis** eines Aufrufs ist — sonst stünde jede aus
  `documents(state)` gebundene Schleifenvariable für `documents`.

Sonde `C:\tsk0023-r7\probe_routes.py`, elf Routen, je zwei Fragen — *liest der gepflanzte Leser
wirklich?* und *nennt die Regel den Halter?*:

```
route                                               liest  ALT (Runde 6)  NEU (Runde 7)
in the argument itself                              YES    SEEN           SEEN
through a local name                                YES    SEEN           SEEN
through a computation                               YES    SEEN           SEEN
beside the reader in a wrapper                      YES    SEEN           SEEN
through a member of this module                     YES    SEEN           SEEN
parked in a name of the module                      YES    SEEN           SEEN
parked in an attribute of a member of this module   YES    blind          SEEN
parked in a mapping of this module                  YES    blind          SEEN
parked in a list of this module                     YES    blind          SEEN
behind a local alias of the reader                  YES    blind          SEEN
behind a local alias, with the path in a local too  YES    blind          SEEN
```

Die ausgelieferte `migrate.py` meldet in **beiden** Fassungen nichts (`shipped file reports: []`) —
die neue, breitere Frage erzeugt also keine Falsch-Positiven im Produkt.

**Rot ohne den Fix** (Runde-6-Fassung von `_stashed_names` und der Empfängerzeile im Sandkasten
zurückgesetzt, neuer Korpus davor):

```
python -B -m pytest tools/test_migrate.py -q -k handing_a_state_path   ->  1 failed
  "a state path travels behind a local alias of the reader into `_a_second_reader` and the rule
   does not name it, so a reader there is licensed by nothing and reported by nothing: []"
```

**Der Rest ist jetzt aus dem Mechanismus abgeleitet statt als Schreibweisenliste behauptet.** Der
frühere Satz („Routen, die jemand absichtlich nimmt") war gemessen falsch. Neu gemessen und als
`L34` geführt: eine Ablage in einem Objekt eines **fremden** Moduls
(`os.environ["PARKED"] = _state_path(state, rel)`) — `reads: YES`, `rule says: []`.

**Der erste Anlauf dieses Fixes hatte selbst ein Loch, und zwar ein neues.** Ich hatte den Empfänger
mit derselben Wertregel gefragt wie die Ablage — und die hört bei einem **Aufruf** auf, weil der Wert
eines Aufrufs das Ergebnis ist und nicht die Funktion. In der Callee-Position ist das genau falsch:
`_a_reader_factory()(_state_path(state, rel))` wird sonst nirgends gefangen, denn der innere Aufruf
trägt keinen Pfad. Beide Richtungen sind gemessen, nicht abgewogen:

```
Variante                              ausgeliefertes migrate.py   Fabrik-Route
Aufruf überall reduziert (weit)       ['absorbed_documents']      SEEN     <- Falsch-Positiv
Aufruf nirgends reduziert (eng)       []                          blind    <- neues Loch
asymmetrisch (Runde 7, gebaut)        []                          SEEN
```

Darum zwei Funktionen: `_receives` für die Positionen, an die etwas übergeben wird (reduziert den
Aufruf), `_stands_for` für den Wert, den ein Local hält (reduziert ihn nicht). Die zwölfte
Korpus-Route (`out of a factory of this module`) ist der Stolperdraht für genau diese Asymmetrie und
wird rot, sobald man den Callee wieder mit der Wertregel fragt — gemessen.

## R7.2 F2 — der neue Stolperdraht war auf `ubuntu-latest` hart rot

`_folded` verdrahtete die Faltung dieses Hosts fest (`name.rstrip(". ").lower()`) und verlangte dann
vom Dateisystem dieselbe Antwort. `.github/workflows/ci.yml` fährt `os: [ubuntu-latest,
windows-latest]` und dort `python -m pytest tools/ -q`.

Die Enumeration `_FOLDINGS` trägt jetzt **zwei** Hälften je Eintrag — wie man die Faltung schreibt
und wie man sie rückgängig macht — und `_foldings_this_filesystem_performs` **fragt** den Host, indem
es beide Schreibweisen anlegt und zählt. Das Modell wird aus dieser Antwort gebaut (Fixpunkt, weil
ein Rückgängig-Schritt freilegen kann, was ein anderer entfernt). Die zweite Zusicherung ist nicht
mehr „hier wurde etwas gefaltet", sondern die **Kopplung**: gefaltete Paare genau dann, wenn der Host
eine Faltung meldet.

Gemessen mit `C:\tsk0023-r7\ext4_probe\run_folding_test.py` (ruft die Testfunktion selbst auf):

```
                                      NTFS (dieser Host)   ext4 (WSL /tmp)
Runde-6-Fassung (Modell fest)         GREEN                RED  — 18 Abweichungen Modell/Disk
Runde-7-Fassung (Modell erfragt)      GREEN                GREEN
```

Die 18 Abweichungen sind die Paare, die dieses Modell zusammenfaltet und ext4 nicht
(`OLD_PROCS.YAML` gegen `old_procs.yaml`, `old_procs.yaml` gegen `old_procs.yaml.` usw.).
Der zweite Leser des Modells (`test_no_instruction_this_command_prints_can_take_a_file_away`) ist
mitgezogen und auf ext4 ebenfalls grün gemessen.

**Das Produkt war nicht betroffen** und ist nicht angefasst: `deposit_of` erzeugt auf beiden
Plattformen denselben Namen, und auf einem case-sensitiven Dateisystem ist die Faltung die Identität.

## R7.3 F3 — die Domäne des DEC-0024-Drahts war eine Schreibweise

`"Remedy:" in node.value` ist eine Schreibweise, kein Merkmal. Gemessen über
`team-kits/**/*.py`:

```
Marker "Remedy:"    ->  221 Literale,  0 Verstöße
Marker \bRemedy\b   ->  224 Literale,  1 Verstoß:
                        team-kits/kernel/migrate.py:2387  `legacy/`
```

Beides geändert: die Domäne ist jetzt das **Wort** `\bRemedy\b`, und die Produktzeile nennt
`legacy/` nicht mehr. Sie sagt stattdessen, welche Datei gemeint ist (die Zeilen darüber nennen sie
je Dokument) und dass die Wahl des Ortes beim Leser liegt.

**Rot ohne den Produktfix** (alte Abhilfe im Sandkasten zurück, neue Domäne):

```
python -B -m pytest tools/test_migrate.py -q -k remedy_literal  ->  1 failed
  "these shipped remedies name a place inside a state directory ...:
   [('team-kits/kernel/migrate.py', 2387, 'legacy/')]"
```

**Die zweite Stelle derselben Familie ist nicht geschlossen, sondern benannt** (`L35`): eine
Abhilfe, die eine Bewegung **ohne Ziel** vorschlägt. Aus echten Läufen gedruckt, nicht aus der Datei
gelesen (`C:\tsk0023-r7\probe_movement_remedies.py`):

```
migrate.search_coverage, UNLISTABLE   proposes a movement: True   names a destination: False
migrate.render, belegter Landeplatz   proposes a movement: True   names a destination: False
```

Dazu der Spec-Satz in `docs/HARNESS_V2_SPEC.md` (e2): er behauptete, der Vorlauf schlage „**keine
Bewegung** mehr vor" — für die `UNLISTABLE`-Zeile stimmt das nicht. Er sagt jetzt, was er deckt:
der Vorlauf **leitet kein Ziel im Zustandsbaum mehr ab**, und wo er eine Bewegung vorschlägt, nennt
er kein Ziel.

## R7.4 Was diese Runde NICHT geschlossen hat

- **`L34`** — die Ablage in einem Objekt eines fremden Moduls. Gemessen, benannt, Urteil Rest
  (DEC-0022): die Regel ist ein Stolperdraht gegen einen versehentlich hinzugefügten zweiten Leser,
  keine Sandbox gegen einen, der ihn versteckt. Dieselbe Klasse: `sys.modules`, `getattr`, ein
  sofort angewandtes Lambda.
- **`L35`** — die Bewegung ohne benanntes Ziel. Rest, weil das Werkzeug kein Ziel ableitet und
  deshalb auch keines auf einen belegten Platz legen kann.
- **`L32`, zweiter Rest** — `deposit_note` misst die Namenskomponente, nicht den Gesamtpfad. Der
  Prüfer hat das ausdrücklich nicht geprüft; diese Runde hat es **nicht angefasst** und behauptet
  nichts darüber. Der Eintrag steht unverändert.
- **Die volle Suite auf Linux.** Gemessen ist dort nur, was in R7.2 steht: die beiden Tests, die das
  Faltungsmodell benutzen. In der WSL dieses Hosts gibt es weder `pip` noch `ensurepip`, ein
  vollständiger Suitenlauf ist dort ohne Eingriff in die Nutzerumgebung nicht herstellbar. Ob
  weitere Tests dieser Suite auf `ubuntu-latest` rot sind, ist damit **offen und ungemessen** — für
  die eine Stelle, die der Prüfer gefunden hat, ist es geschlossen.

## R7.5 Abnahmelauf der Runde 7

- `python tools/bump_kit_version.py` → alle drei Kits auf `2026.08.09-7`; nach der letzten
  Codeänderung antwortete ein zweiter Aufruf `unchanged`, der Lauf unten lief also auf dem
  gestempelten Baum
- `python -m ruff check .` → `All checks passed!`
- `python tools/validate.py` → `all structural checks passed.`
- `python -B -m pytest tools/ -q` → **2335 bestanden, 12 übersprungen, 0 rot** (24:41, exit 0)

Die Zahl ist identisch mit Runde 6 (2335/12), und das ist erwartbar: diese Runde legt **keine** neue
Testfunktion an. Die sechs neuen Routen sind Einträge im Korpus einer bestehenden Testfunktion, F2
und F3 ändern bestehende Tests.

`.claude/hooks/test_gates.py` ist wieder nicht vollständig gefahren, aus demselben Grund wie in
Runde 6 — diese Runde fasst keinen Gate-Hook und keine `.claude/`-Datei an. Gefahren ist der eine
Test, der die von dieser Runde geänderte Datei liest: `test_every_reference_to_a_measurement_leads_
to_one` über `docs/POST_V2_WISHLIST.md` (mit den neuen Einträgen `L34`/`L35`), 1 bestanden.

**Gespiegelt wurde nichts**, aus demselben Grund wie in den Runden 5 und 6: geändert sind
`team-kits/kernel/migrate.py`, `tools/test_migrate.py`, `docs/POST_V2_WISHLIST.md`,
`docs/HARNESS_V2_SPEC.md` und dieses Protokoll. Das Kernel-Paket liegt genau einmal unter
`team-kits/kernel/`; unter `team-kits/{dev,office,research}-team/` ist außer den drei
`VERSION`-Dateien (vom Stempler) keine Datei angefasst.

**Sandkästen und Sonden dieser Runde** liegen nach DEC-0026 unter
`C:\Trash\2026-08-09-tsk0023-r7-sandbox\` — nichts gelöscht, alles verschoben.

# Runde 8 — B1 bis B6 (2026-08-09)

Verdikt der Runde 7: FAIL, `B1`–`B5` blockierend, `B6` Rest. Bestätigt und **nicht angefasst**:
`absorbed_documents` ist ein echtes Falsch-Positiv (Argumentposition), das ausgelieferte
`migrate.py` meldet unter der breiteren Regel `[]`, `Remedy:` = 221 / `\bRemedy\b` = 224.

## R8.0 Sandkasten dieser Runde

- Alles unter `C:\AS-sandbox\`, also außerhalb des Repos. Der Klon `C:\AS-sandbox\tsk0023-r8` ist
  eine vollständige Kopie **mit** `.git` (die V1-Historie, die `test_migrate` braucht) plus
  Arbeitsbaum; die Rotmessungen kopieren vor jedem Lauf die geänderten Dateien aus dem Repo dorthin
  und schreiben nur **in den Klon**.
- Sonden: `probe_b1.py`, `probe_b1_fix.py`, `probe_b1_which.py`, `red_b1.py`, `red_b1_detail.py`,
  `probe_b2.py`, `probe_b2b.py`, `probe_b3.py`, `probe_b4.py`, `probe_b5.py`, `probe_l36.py`,
  `red_round8.py`.
- Nach DEC-0026 wurde **nichts gelöscht**; der Verbleib steht in R8.8.

## R8.1 B1 — die Asymmetrie hing an der Bindungsstelle

**Befund reproduziert** (`probe_b1.py`, echter Prozess, Markerdatei, gepflanzter Leser gibt die
gelesenen Bytes zurück; ausgeliefertes `migrate.py` meldet vorher `[]`):

```
a factory result in a local                          reads=True  holder named=False rule says []
a factory result in a local, path in a local too     reads=True  holder named=False rule says []
a nested def of the host function                    reads=True  holder named=False rule says []
parked in a default argument of this module          reads=True  holder named=False rule says []
```

**Fix, drei Teile.**

1. `_stands_for` ist weg. An seiner Stelle steht `_value_leads_to`, das je Name ein **Paar**
   `(Name, kam aus einem Aufruf)` führt. `_aliases_in` speichert die Paare; die **Verwendungsstelle**
   entscheidet: `_receives(..., invoked=True)` (Callee) löst „aus einem Aufruf" auf, die
   Argumentposition nicht. Grund, gemessen in beide Richtungen: in der Argumentposition ebenfalls
   aufzulösen meldet am ausgelieferten Modul `absorbed_documents`.
2. `_module_own_names` steigt in Funktionsrümpfe **ab**, sammelt dort aber nur `def`/`class`-Namen,
   keine Locals.
3. `_handed_a_finished_path` liest `node.func` als **Träger** wie jedes andere Wort des Aufrufs —
   nötig und nur nötig für die Ablage in `__defaults__` (gemessen, `probe_b1_which.py`).

**Deckung nach dem Fix** (`probe_b1_fix.py`, 16 Korpusrouten + eine Sonde): jede Route `reads=True`,
`named=True`; ausgeliefertes `migrate.py` weiter `[]`, mit und ohne Callee-Träger.

**Rotmessungen** (`red_b1.py`, Klon außerhalb des Repos, Ziel
`test_the_rule_against_handing_a_state_path_on_follows_the_value_and_not_the_call_shape`):

```
UNTOUCHED                                  rc=0  1 passed
round 7 asymmetry on the binding site      rc=1  ... out of a factory and called from a local
own names read at the top level only       rc=1  ... into a def nested in the host function
callee not read as a carrier               rc=1  ... parked in the defaults of a function ...
argument position resolves a call result   rc=1  ... shipped module: ['absorbed_documents']
RESTORED                                   rc=0  1 passed
```

**Was übrig bleibt** — und die Grenze „eigenes gegen fremdes Modul" ist gemessen **keine** Grenze,
darum steht sie so weder im Docstring von `_handed_a_finished_path` noch in `L34`. Neu gemessen und
in `L34` mit Kette aufgenommen: ein Aufrufergebnis **dieses** Moduls, das als **Argument** an einen
fremden Wrapper geht, der es dann aufruft —

```
reader = _a_reader_factory()
functools.partial(reader, _state_path(state, rel))()
out of a factory, handed to a foreign wrapper   reads: YES   rule says: []
```

## R8.2 B2 — die Domäne war eine Schreibweise, die Ortsangabe zwei

**Befund reproduziert** (`probe_b2.py` / `probe_b2b.py`, über den Parse, nicht über Zeichenketten):

```
literals with `Remedy:`      221
literals with word Remedy    224
remedy-slot constants         95     ...of which carry the word: 0
```

Mit backtick-unabhängiger Ortsangabe über **alle** Pfadkomponenten fielen 13 Fundstellen an: 7
`remedy`-Slots (`project_memory/staging/<…>`), `cli.py:509` (`staging/<key>/`) und 5 reine
**Erwähnungen** (`generated/index.yaml`, `approvals/pending/`, `archive/<TYPE>/<year>/`, `archive/`).

**Fix.** `_remedy_literals` liest beide Arten, wie dieses Repo eine Abhilfe ausliefert (Wort, und
`remedy`-Slot als Keyword-Argument oder Mapping-Schlüssel). `_places_inside_a_state_directory` liest
jedes pfadförmige Wort **ohne** Backticks und **alle** Komponenten. Alle 13 Fundstellen sind
umformuliert; die 5 Erwähnungen nennen jetzt die **Sache** statt des Pfades. Die Regel fragt damit
nach dem **Ort**, nicht nach der Absicht, und das ist eine bewusste Über-Verweigerung: der
Unterschied zwischen *schau dort nach* und *leg das dorthin* ist ein Verb, und eine Regel über Verben
wäre eine Liste. Der Docstring sagt genau das.

`gate_write_scope.py:320` wird jetzt **konstruiert**, wo der Schlüssel bekannt ist (`% task["id"]`,
wie die Nachbarzeile), und nennt sonst keinen Pfad. Dadurch sinkt die Slot-Zahl von 95 auf 92.

**Rotmessungen** (`red_round8.py`, Ziel
`test_no_remedy_literal_this_repo_ships_names_a_place_inside_a_state_directory`) — jede Verengung
**gepaart** mit dem Verstoß, den sie verdeckte:

```
B2 the offer cli.py used to print            -> RED     (erwartet RED)
B2   ...with the backtick requirement back   -> green   (erwartet green)
B2 the seven slot values back                -> RED     (erwartet RED)
B2   ...reading the first component only     -> green   (erwartet green)
B2   ...with the word-only domain            -> green   (erwartet green)
B2 both halves of the domain, floor gone     -> RED     (erwartet RED)
```

## R8.3 B3 — die `UNLISTABLE`-Abhilfe bot eine Bewegung an, die das Wurzelitem kostet

**Kette gemessen** (`probe_b3.py`, echter Lauf auf einem Zustand außerhalb dieses Repos, dessen
`product/active/` das Leserecht entzogen bekam):

```
rows while unlistable        ['product/active/']
gate_git, readable           rc=2
gate_git, after the move     rc=0        root item still there: False
```

**Fix.** `migrate.THE_ONLY_UNLISTABLE_STEP` — ein Schritt, der die **Sitzung** ändert und nichts, was
das Zustandsverzeichnis hält. Die Bewegungsalternative ist gestrichen.

**Neuer Test:** `test_the_remedy_for_a_directory_nobody_can_list_offers_no_step_that_moves_it`.
Er misst beide Enden aus einem echten Lauf (die Zeile endet an dem einen Schritt; der Schritt wirkt,
die Zeile verschwindet danach) und **führt die gestrichene Alternative aus**: `gate_git` antwortet
danach rc 0.

**Ein Fehler in der ersten Fassung dieses Tests, selbst gefunden und gemessen:** die Zusicherung las
`migrate.THE_ONLY_UNLISTABLE_STEP` zurück und war damit mit **jedem** Satz einverstanden, den das
Modul hält — die Rotmessung „B3 the movement alternative back" kam **grün** heraus. Der Satz ist
jetzt im Test **gepinnt**; die Wiederholung derselben Mutation ist RED (`red_round8.py`).

## R8.4 B4 — die Kopplung ist gestrichen, nicht ersetzt

`bool(folded_here) == bool(performed)` konnte nicht rot werden. Eine Fassung **je Eintrag** wurde
gebaut und wieder verworfen, mit Begründung: ist eine Faltung in `performed`, dann fällt ihr Paar
per Konstruktion schon unter `_folded`, also entscheidet die Zusicherung eine Zeile darüber dieselbe
Frage; auseinanderlaufen können die beiden Fragewege nur, wenn zwei Undos dieser Liste auf **einem**
Paar zusammenfallen — das tut auf NTFS und auf ext4 keines. Eine längere Schreibweise desselben
Vakuums ist keine Verbesserung. Der Docstring schreibt genau diese Begründung hin.

Was bleibt, ist die Zusicherung, die rot werden **kann**: das Modell wird aus der Antwort des Hosts
gebaut, und `disagreed` misst es gegen die Platte. Rotmessung: Modell auf die Identität verdrahtet →
`B4/B5 the model hard-wired to the identity -> RED`.

## R8.5 B5 — die „beide Enden"-Behauptung war zur Hälfte falsch

Nachgemessen (`probe_b5.py`, dieser Host, NTFS): `"upper case"` aus `_FOLDINGS` entfernt →
`1 passed`. Der Korpus wird aus `_FOLDINGS` erzeugt, also kann eine Faltung, die die Liste nicht
kennt, hier von nichts gemeldet werden. Der mittlere Halbsatz ist gestrichen. Was die Kürze der
Liste begrenzt, steht jetzt dort, wo es hingehört: `deposit_of` schreibt in
`migrate._NAME_ALPHABET` (gemessen: Kleinbuchstaben, Ziffern, `-`, `_`), und die letzte Zusicherung
legt die Ablagenamen des ganzen Korpus **auf der echten Platte** an.

## R8.6 B6 — die Routenzahl

`docs/POST_V2_WISHLIST.md` nannte an zwei Stellen „elf Routen". Beide Stellen stehen in `L34` und
sind beim Neuschreiben des Eintrags **ohne Zahl** formuliert („**jede** Route des Korpus"), damit die
nächste Korpusergänzung sie nicht wieder falsch macht.

## R8.7 Was diese Runde NICHT geschlossen hat

- **`L34`** — zwei gemessene Routen: die Ablage in einem Objekt eines fremden Moduls, und **neu** das
  Aufrufergebnis dieses Moduls als Argument an einen fremden Wrapper. Rest nach DEC-0022.
- **`L35`** — die verbliebene Bewegung ohne Ziel: die Abhilfe des belegten `legacy/`-Landeplatzes.
  Urteil **blockierend**, geführt als **benannte Ausnahme mit einer Ja/Nein-Frage an den Nutzer**;
  sie ist nicht schließbar, ohne dass der Befehl selbst einen Ort wählt, und ein Kopieren löst die
  Bedingung nicht auf.
- **`L36` (neu)** — `_root.has_root_item` liest ein Verzeichnis ohne Leserecht als „noch kein
  Wurzelitem" und schaltet damit die Gates ab, die es schützen. Gemessen: `gate_git` rc 2 → rc 0.
  Rest, und das ist gemessen statt angenommen: `gate_write_scope` verweigert alle vier naheliegenden
  Zeilen, mit denen eine Sitzung das Leserecht selbst entzöge (`icacls` ×2, `chmod`, `attrib`, je
  rc 2, echter Hook-Prozess, `probe_l36.py`).
- **`L37` (neu)** — `report.validate_state` wirft über demselben Verzeichnis einen ungefangenen
  `PermissionError` statt ein Finding. Rest, weil ein Absturz laut ist; derselbe Auslöser wie `L36`.
- **Die volle Suite auf Linux** — unverändert offen, aus demselben Grund wie in Runde 7.

## R8.8 Abnahmelauf der Runde 8

- `python tools/bump_kit_version.py` → alle drei Kits auf `2026.08.09-8`; nach der letzten
  Kit-Änderung antwortete ein weiterer Aufruf `unchanged`, der Lauf unten lief also auf dem
  gestempelten Baum
- `python -m ruff check .` → `All checks passed!`
- `python tools/validate.py` → `all structural checks passed.`
- `python -B -m pytest tools/ -q` → **2336 bestanden, 12 übersprungen, 0 rot** (27:31, exit 0)

2335 → 2336, das ist die eine neue Testfunktion
(`test_the_remedy_for_a_directory_nobody_can_list_offers_no_step_that_moves_it`).

**Ein erster, verunreinigter Lauf steht ausdrücklich hier**, weil er die einzigen zwei Rotmeldungen
dieser Runde gefunden hat: er lief los, während noch ein Docstring geändert wurde, und meldete
`2 failed, 2334 passed`. Beide Fehlschläge waren echt und kamen von den Umformulierungen aus R8.2 —
Tests, die die alte Wortwahl festhielten:

```
tools/test_staging_cli.py::test_cli_capture_refuses_a_body_over_the_item_budget
    assert ... "staging" in err        -> die Abhilfe nennt keinen Ort mehr (DEC-0024)
tools/test_state.py::test_read_item_names_remedy_for_missing
    pytest.raises(..., match="index.yaml") -> die Abhilfe nennt den generierten Index beim Namen
```

Beide sind auf die neue Eigenschaft nachgezogen, mit dem Grund im Test. Der Lauf oben ist der
saubere Wiederholungslauf danach, in **einem** Lauf.

`.claude/hooks/test_gates.py` ist nicht vollständig gefahren — diese Runde fasst keinen Gate-Hook und
keine `.claude/`-Datei an. Gefahren ist der eine Test, der die geänderte Datei liest:
`test_every_reference_to_a_measurement_leads_to_one` über `docs/POST_V2_WISHLIST.md` (mit `L34`
neugeschrieben und `L36`/`L37` neu), 1 bestanden.

**Gespiegelt** wurde `hooks/gate_write_scope.py` aus `dev-team` nach `office-team` und
`research-team`; die drei Kopien sind byte-identisch (SHA-256 `17a37f961f8e75db…`).
`gate_packaging_decision.py` gibt es nur im dev-Kit, ist also nichts zu spiegeln. Sonst sind
geändert: `team-kits/kernel/{migrate,cli,state,approvals}.py` (das Kernel-Paket liegt genau einmal),
`tools/{test_migrate,test_state,test_staging_cli}.py`, `docs/POST_V2_WISHLIST.md`,
`docs/HARNESS_V2_SPEC.md` und dieses Protokoll.

**Sandkästen und Sonden dieser Runde** liegen nach DEC-0026 unter
`C:\Trash\2026-08-09-tsk0023-r8-sandbox\` — nichts gelöscht, alles verschoben. Darin auch die beiden
Suite-Protokolle `full_suite_round8.txt` (der verunreinigte Lauf) und
`full_suite_round8_final.txt` (der Abnahmelauf).

# Runde 9 — F2, F3, F4, L35, DEC-0029 (2026-08-09)

Abschlussrunde. Zwei Nutzerentscheidungen bestimmen sie: **DEC-0029** (der statische Draht gegen
einen zweiten Leser wird als *Menge gemessener Routen* geführt, nicht als Deckung) und die
**L35-Entscheidung** („Ziel konstruieren"). Produktbefunde werden geschlossen, Behauptungen über den
eigenen Prüfapparat zurückgenommen.

## R9.0 Sandkasten dieser Runde

`C:\Trash\tsk0023-r9\` — alle Sonden und ein voller Klon des Baums (`redclone/`), in dem die Defekte
für die Rotmessungen **einzeln** wiederhergestellt wurden. Im Repo selbst wurde dafür nichts
verändert; das Skript prüft vor jedem Eingriff, dass der Fix da ist, wo es ihn erwartet, und meldet
sonst `MISSING` statt eine leere Messung zu drucken.

## R9.1 F4 — `has_root_item` las ein unlesbares Verzeichnis als „noch kein Wurzelitem"

Der Prüfer hat die Rest-Einstufung von `L36` umgangen: sie stützte sich auf vier verweigerte
Kommandozeilen, während der Mechanismus zwei Bildschirmseiten höher in derselben Datei als `L4`
(„Schreibverben innerhalb einer Programmsprache … bewusst nicht geschlossen") offen geführt wird.

```
python -c "import os,subprocess;p=os.path.join('project'+'_memory','product','active');
           subprocess.run(['icacls',p,'/deny','zenti:(RD,RA)'])"
alle acht Bash-Hooks rc 0  ->  die Zeile läuft  ->  gate_git rc 2 wird rc 0
```

**Fix:** `_root.has_root_item` listet selbst (`_root._names_matching`) und kennt drei Antworten statt
zwei — Namen gefunden, nichts da (nicht vorhanden / kein Verzeichnis), und **keine Antwort** (jeder
andere `OSError`). Der dritte Fall zählt als Wurzelitem: „kein Item" schaltet fünf Gates ab, „ein
Item" kostet in einem Projekt in Einrichtung eine Verweigerung, und die sagt es.

**Gemessen, ausgeliefertes `gate_git.py` als echter Prozess, JSON auf stdin, Zustand außerhalb des
Repos** (`test_the_remedy_for_a_directory_nobody_can_list_offers_no_step_that_moves_it`):

```
product/active/ lesbar         git merge feat/PR-0001-x   -> rc 2
product/active/ nicht listbar  git merge feat/PR-0001-x   -> rc 0   [vorher]
product/active/ nicht listbar  git merge feat/PR-0001-x   -> rc 2   [nachher]
```

Der Stolperdraht existierte schon und ist nachgezogen: er hielt bis Runde 8 `rc 0` fest und hält
jetzt `rc 2`. `L36` ist als GESCHLOSSEN umgeschrieben, `L37`s Begründung korrigiert (sie stützte sich
auf dieselbe falsche Unerreichbarkeit; sie bleibt Rest allein wegen der Ausfallrichtung).

## R9.2 F3 — zwei ausgelieferte Abhilfen von `report.validate_state`

- `report.py:349` (`item exceeds budget`) druckte *move detail to `staging/evidence` and reference
  it* — **beide** Klauseln von DEC-0024 in einem Satz. Jetzt: *keep the summary in the item and
  capture the detail as an evidence item of its own through the entry point, then reference it*.
  Kein Ort, keine Bewegung.
- `report.py:541` (`UNLISTABLE`) bot wieder *or take it out of the state directory* an — dieselbe
  Alternative, die Runde 8 am **anderen** Drucker gestrichen hatte, auf derselben Verzeichnisklasse.
  Jetzt reicht der Validator `migrate.THE_ONLY_UNLISTABLE_STEP` durch: **eine** Bedingung, **eine**
  Antwort, **ein** Ort, an dem sie steht.
- Dazu aus derselben Familie, von der erweiterten Domäne (R9.5) gefunden: `report.py:605`
  (`moved to legacy/` → *into the kernel's legacy area*), `migrate.py:2737` (`place under legacy/` →
  *place in the kernel's legacy area*), `gate_write_scope.py:962` in allen drei Kits
  (`project_memory/staging/<task-id>/` → *the task's own proposal area (spec II.4)*) und
  `proc_hash.py:95` im office-Kit (`project_memory/generated/index.yaml` / `archive/.` → *the
  generated index* / *the archive*).

## R9.3 F2 — die Kit-Abhilfe schickte in einen Bereich, den das Kit selbst verweigert

`guard_memory_budget.py:325` in allen drei Kits: *put the fact on the item itself (or in
`evidence/`)* — ein Werkzeug-Schreibzugriff dorthin ist rc 2. Jetzt: *put the fact on the item it
belongs to — the kernel captures items, and `python scripts/harness.py --help` lists the surface*.
Byte-identisch gespiegelt.

## R9.4 L35 — das konstruierte Ziel außerhalb, und ob es baubar ist

**Es ist baubar, und es ist gebaut.** `migrate.overflow_deposit_of(rel, digest)`:
`../v1-legacy-overflow/` **neben** dem Zustandsverzeichnis, darunter derselbe Kodierer wie
`deposit_of` (`_encoded_name`, `_NAME_ALPHABET`), der **Landeplatzpfad und sha256 des dort stehenden
Inhalts** trägt. Gedruckt wird der eine Composer (`copy_instruction`) und danach der zweite Schritt.

Aus einem echten Lauf:

```
  a.yaml                       -> legacy/a.yaml is already taken
     Remedy: COPY it -- the original stays where it is -- to
     `../v1-legacy-overflow/v1-deposit--legacy%2fa%2eyaml%2f3d51709d…`. Then, and only once that
     copy exists, remove legacy/a.yaml itself from a shell outside the session -- the copy is what
     keeps the file, and removing the original is what frees the place.
```

**Warum der Inhalt im Namen steht** — der Punkt, an dem die Konstruktion sich von `deposit_of`
unterscheidet: dort bleibt die Quelle stehen, ein belegter Name hält also eine frühere Kopie
derselben Datei. Hier entfernt der Leser das Original, derselbe Landeplatzpfad kann später andere
Bytes tragen, und mit dem Pfad allein im Namen landet eine spätere Anweisung auf einer früheren
Kopie. Die Kette ist im Test durchgespielt (zwei Belegungen desselben Platzes → zwei Namen, die
erste Kopie überlebt).

Der Digest steht in `plan["occupied_landings"]` (dritte Spalte), gelesen in `build_plan` über
`_read_bytes` — nicht mit einem eigenen `open`, weil beide Regeln dieses Moduls über einen zweiten
Leser sonst zuschlagen (und in der ersten Fassung auch zugeschlagen haben: `_occupant_digest` stand
in `test_nothing_but_these_functions_can_name_a_file_of_the_state_directory` und im
Übergabedraht — beides gemessen, beides der Grund für die jetzige Form).

## R9.5 Zwei Befunde am Prüfapparat, die ausgelieferte Verstöße verdeckt haben

Beide sind klein, definitionsförmig — und beide haben Produktfehler aufgedeckt (die Liste in R9.2).

1. **`_places_inside_a_state_directory` strippte die Trenner, bevor es „pfadförmig" fragte.**
   `evidence/` verlor damit genau das Zeichen, das es zu einem Pfad macht, und fiel eine Zeile
   später heraus. Der Fix fragt zuerst.
2. **Die Domäne kannte nur Wort und Schlüsselwort.** Eine Abhilfe, die als **Positionsargument** in
   einen Parameter namens `remedy` läuft, war unsichtbar — `report.validate_state` reicht sie so
   durch (`_finding(severity, item, message, remedy)`), also **alle** Befunde des Validators.
   `_remedy_literals` liest jetzt die `def`s des ganzen ausgelieferten Baums und bindet Positionen
   gegen die Signatur der Aufgerufenen.

**Vorher/nachher, über `team-kits/**/*.py` gemessen (Sonde `measure_domain.py`):**

```
Domäne alt,  Leser alt   ->  0 Fundstellen        (Wort 224, Slot 92)
Domäne alt,  Leser neu   ->  4 Fundstellen        (3× evidence/, 1× legacy/)
Domäne neu,  Leser alt   ->  6 Fundstellen
Domäne neu,  Leser neu   -> 10 Fundstellen        (+ Parameter 57)
nach den Produktfixes    ->  0 Fundstellen        (Wort 225, Slot 92, Parameter 56)
```

Die 57 → 56 sind kein Verlust, sondern eine benannte Grenze: `report.py` reicht jetzt eine
**Konstante** statt eines Literals durch, und ein Name ist für eine Literalregel unsichtbar. Das
steht in `L33`.

## R9.6 DEC-0029 angewandt — die Prosa zurückgenommen

- `_module_own_names`: „the likeliest slip of all" ist weg. Stattdessen steht dort, was das Sammeln
  eines Namens **nicht** kauft — ein geschachtelter `def`, der den Pfad aus der **Closure** liest,
  übergibt nichts, also sieht die Regel nichts.
- `_handed_a_finished_path`: „a path … reaches no code of this module that `_NAMES_A_STATE_FILE`
  does not name" ist ersetzt durch „eine Menge gemessener Routen", mit dem Verlauf 6 → 12 → 16 → 17
  und dem Hinweis, dass die Frage statisch nicht entscheidbar ist. Daneben steht ausdrücklich, dass
  der **Laufzeit**-Wächter der eigentliche Schutz ist und für nicht betretene Zweige blind bleibt.
- `_HOW_A_PATH_TRAVELS` und der Test darüber tragen denselben Satz.
- `L34` nennt die Closure-Route jetzt als gemessene Route. **Hier selbst nachgemessen**, echter
  Prozess, gepflanzter Leser in `_read_bytes`:

```
path = _state_path(state, rel)
def _a_closure_reader():
    open(r"<marker>", "wb").write(open(path, "rb").read())
_a_closure_reader()
                     reads: True   rule: []   handed: []
```

  Und die Nebenbeobachtung, die dabei fiel und die in `L34` steht: **dieselbe** Route wird doch
  gemeldet, sobald der geschachtelte Leser seine Bytes an irgendeinen Namen dieses Moduls
  weiterreicht (`_PLANTED.append(open(path, "rb").read())` → `handed: [('_read_bytes', 'path',
  '_PLANTED', 766)]`). Was die Regel dort sieht, ist der Aufruf, der die **Bytes** ablegt, nicht die
  Übergabe des Pfades — Zufall der Beobachtung, kein Schutz.

## R9.7 F5 — `L33` beschrieb nicht mehr den Code, den es nennt

Die Backtick- und Leerzeichenbedingung sitzt seit Runde 8 in `_state_paths_in` (dem Leser des
**Laufzeit**-Tests), nicht mehr in `_places_inside_a_state_directory`. `L33` sagt das jetzt und nennt
zusätzlich die zwei weiteren Formen, die aus der Literaldomäne fallen (eine Abhilfe als **Name**, und
ein Empfänger unter einer Schreibweise, die die Signaturauflösung nicht kennt).

## R9.8 Rotmessungen — jeder Fix einzeln im Klon außerhalb des Repos

`C:\Trash\tsk0023-r9\restore_defects.py` setzt je einen Defekt zurück, fährt die Tests, stellt her:

```
F4  has_root_item fails OPEN (glob)                       1 failed
F2  kit remedy sends the reader into `evidence/`          1 failed
F3a validator remedy `move detail to staging/evidence`    1 failed
F3b validator offers `or take it out …` again             1 failed
L35 occupied landing: a movement with no destination      1 failed
L35 overflow name without the occupant's content          1 failed
APP strip before the path-shaped question                 1 failed
APP keyword-only remedy domain                            1 failed
danach, alle vier Tests                                   4 passed
```

`APP strip` war beim ersten Durchgang **grün** — und das war richtig so: die Lücke ist eine
**Stille**, und nach dem Produktfix gab es nichts mehr zu verschweigen. Gemessen als Paar
(`restore_pair.py`):

```
A  Verstoß zurück, Leser gefixt        1 failed
B  Verstoß zurück, Strip-Defekt zurück 1 passed     <- die Stille
C  beides hergestellt                  1 passed
```

Damit die Stille auch allein einen Draht hat, fragt der Test den Leser jetzt direkt: ein Wort, dessen
einziger Trenner am Ende steht, muss gefunden werden. Mit dem Strip-Defekt zurück ist er rot (oben,
Zeile `APP strip`, nach dem Nachziehen).

## R9.9 Was diese Runde NICHT geschlossen hat

- **Zwei Abhilfen von `report.validate_state`** sagen weiterhin *take the file out of the state
  directory* (`_bounded` für ein Dokument über einem der beiden Lesebudgets, und die für ein
  unparsbares Dokument). Sie nennen kein Ziel, überschreiben also nichts, können aber die Quelle
  kosten. Warum die Konstruktion aus R9.4 dort fehlt, ist **für die beiden nicht derselbe Grund** —
  dieser Absatz sagte bis Runde 10 einen für beide, und für den zweiten war er falsch; die Messung
  und die Korrektur stehen in **R10.1**. Kurz: `_bounded` entscheidet vor jedem Lesen (der Digest
  wäre nur zum Preis des unbegrenzten Lesers zu haben, den `DOCUMENT_MAX_BYTES` verbietet), der
  Parse-Fehler-Zweig dagegen wird erst **nach** dem Lesen erreicht — dort ist der Digest verfügbar
  und die Konstruktion schlicht nicht gebaut. Steht in `L35`.
- **Der statische Übergabedraht** bekommt keine weitere Route (DEC-0029). Fünf offene sind in `L34`
  benannt, die Closure-Route neu darunter.
- **`L37`** (`validate_state` stürzt über ein unlistbares kanonisches Verzeichnis) bleibt Rest — ein
  Absturz ist laut, kein Aufrufer liest ihn als „keine Befunde".
- **`L33`**, **`L30`**, **`L32`** unverändert offen, jeweils mit Mechanismus und Begrenzung.

## R9.10 Abnahmelauf der Runde 9

- `python tools/bump_kit_version.py` → alle drei Kits auf `2026.08.09-11`; ein zweiter Aufruf
  antwortete `unchanged`, der Lauf unten lief also auf dem gestempelten Baum
- `python -m ruff check .` → `All checks passed!`
- `python tools/validate.py` → `all structural checks passed.`
- `python -B -m pytest tools/ -q` → **2337 bestanden, 12 übersprungen, 0 rot** (26:07, exit 0)

2336 → 2337: die eine neue Testfunktion
(`test_the_place_a_taken_landing_is_freed_to_is_named_and_lies_outside_the_state_directory`).

**Zwei verunreinigte Läufe stehen ausdrücklich hier**, weil sie zeigen, was ein Lauf über einen Baum
wert ist, der sich unter ihm bewegt: beide liefen, während noch an `_root.py` und `migrate.py`
gearbeitet wurde. Der zweite meldete `9 failed` — fünf davon Scaffold-/`validate.py`-Tests, die den
Kit-Hash gegen die `VERSION` prüfen, also genau die Klasse aus der Repo-Regel „erst stempeln, dann
urteilen". Beide sind verworfen; der Lauf oben ist der Abnahmelauf und lief nach der letzten Änderung
in **einem** Stück. Protokolle: `C:\Trash\tsk0023-r9\full_suite_round9_final.txt` und
`full_suite_round9_poisoned.txt`.

`.claude/hooks/test_gates.py` ist nicht vollständig gefahren — diese Runde fasst keine
`.claude/`-Datei an. Gefahren ist der eine Test, der die geänderte Datei liest:
`test_every_reference_to_a_measurement_leads_to_one` über `docs/POST_V2_WISHLIST.md`, 1 bestanden.

**Gespiegelt** und byte-identisch (md5 geprüft): `hooks/_root.py` (`6a6d0f03…`),
`hooks/guard_memory_budget.py`, `hooks/gate_write_scope.py` aus `dev-team` nach `office-team` und
`research-team`; `hooks/gate_git.py` nach `research-team` (das office-Kit liefert keines).
Sonst geändert: `team-kits/kernel/{migrate,report}.py` (einmal vorhanden),
`team-kits/office-team/templates/repo/scripts/proc_hash.py` (nur dieses Kit hat es),
`tools/test_migrate.py`, `docs/POST_V2_WISHLIST.md`, `docs/HARNESS_V2_SPEC.md` und dieses Protokoll.

**Sandkasten und Sonden dieser Runde** liegen nach DEC-0026 unter `C:\Trash\tsk0023-r9\` — nichts
gelöscht, alles verschoben.

# Runde 10 (2026-08-09) — der eine Blocker, und vier eingetragene Reste

Der Prüfer meldete **genau einen** Blocker (B1) und vier Reste (B2–B5). Diese Runde schließt B1 und
trägt B2–B5 ein; gebaut wurde außer dem Stolperdraht zu B1 nichts.

## R10.1 B1 — eine Unmöglichkeitsbehauptung, die der Code nicht trägt

`L35` sagte über **beide** stehengebliebenen Abhilfen von `report.validate_state`, sie „lesen die
Datei absichtlich nicht", weshalb kein sha256 für einen konstruierten Zielnamen zu haben sei. Für
`_bounded` stimmt das; für den Parse-Fehler-Zweig nicht.

**Gemessen** (eigene Sonde, `sys.addaudithook` über einen echten `report.validate_state`-Lauf, Zustand
außerhalb dieses Repos unter `C:\Trash\tsk0023-r10\sandbox\`, Sonde `probe_opens.py`/`probe_all.py`):

```
unter dem Zustandsverzeichnis geöffnet:  .kernel.lock, product/active/PR-0001.yaml, broken.yaml
big.yaml (2.112.590 Bytes > DOCUMENT_MAX_BYTES 2.000.000):  NICHT geöffnet
Befund big.yaml     -> "It is 2112590 bytes …"  + Abhilfe `_bounded`
Befund broken.yaml  -> "It could not be read (ParserError: …)" + Abhilfe "repair the file …"
```

Der Weg dahin steht im Code: `report.py` geht im `else`-Zweig durch `spent += size` und dann durch
`migrate._read_document` → `_read_bytes`; der Parse scheitert **nach** dem Lesen. Der Digest wäre dort
ohne einen einzigen zusätzlichen Byte-Zugriff zu haben.

**Eine Nebenmessung, die die Sonde selbst erst brauchbar machte:** der Kernel öffnet unter dem
Zustandswurzelverzeichnis teils über `ext_path`, also als `\\?\C:\…`. Eine Sonde, die den
Wurzelpfad mit `startswith` verankert, verliert genau diese Öffnungen — das Wurzelitem und die
`.kernel.lock` fehlten im ersten Durchgang, und die Ausfallrichtung ist die schlechte („wurde nie
geöffnet"). Der Stolperdraht sucht den Wurzelpfad deshalb **im** aufgelösten Pfad statt an seinem
Anfang.

**Gewählter Weg: die beiden Fälle sauber trennen** (die zweite der beiden angebotenen Optionen).
Nicht gebaut wurde die Konstruktion für den Parse-Zweig, und der Grund steht in `L35`: sie kostet eine
Signaturänderung an `_read_document` (fünf Aufrufstellen, plus die Verträge, die auf seiner Zweiheit
ruhen), und das Zielverzeichnis heißt `v1-legacy-overflow` — es ist für den belegten Landeplatz
benannt, nicht für ein unparsbares Kit-Dokument. In der letzten Runde eines Pakets ist das eine
Änderung mit eigener Prüffläche, kein Halbsatz. Der Rest bleibt also stehen, aber mit dem **wahren**
Grund.

**Stolperdraht (neu):**
`test_migrate.test_the_two_remedies_that_still_move_a_file_differ_in_whether_the_file_was_read`
— fährt `validate_state` als eigenen Prozess unter dem Audit-Hook und verlangt: `big.yaml` nicht
geöffnet, `broken.yaml` geöffnet, und die Menge der Abhilfen, die noch aus dem Zustandsverzeichnis
hinausschicken, ist genau diese zwei.

**Rot gemessen im Klon außerhalb des Repos** (`C:\Trash\tsk0023-r10\clone`, `restore_defects.py`;
je ein Defekt zurück, Test gefahren, Datei wiederhergestellt):

```
the bounded branch reads the document after all    1 failed
the parse verdict is reached without reading       1 failed
restored                                           1 passed
```

Die zweite Zeile ist die Welt, in der der alte Satz wahr **wäre** — dann ist der Draht ebenfalls rot,
und die Behauptung wird neu gestellt statt still zu bleiben.

## R10.2 B2 — der Overflow-Name trifft die Längengrenze 67 Zeichen früher

Gemessen (`C:\Trash\tsk0023-r10\lengths.py`, gegen den laufenden Kernel):

```
deposit_of("legacy/old_procs.yaml")          -> Name 37 Zeichen
overflow_deposit_of(dasselbe, sha256)        -> Name 104 Zeichen      Differenz 67
_NAME_MAX_CHARS                              -> 255
deposit_note(overflow_deposit_of(200-Zeichen-Landeplatz, sha256))
    -> "That name is 40 character(s) longer than the 255 this filesystem takes, …"
```

67 = `%2f` (3) + 64 Hex. Eingetragen in `L32` mit der blockierenden Bedingung und mit dem
Unterschied, der zählt: `occupied_landings` macht `plan_is_executable` falsch, ein unanlegbarer
Overflow-Name nimmt der Migration also die einzige gedruckte Route — anders als beim
`deposit_of`-Namen, wo nur ein Datensatz betroffen ist. Nicht gebaut.

## R10.3 B3 — der Hinweis „from a shell outside the session" fehlt an der Kopie

Gemessen gegen den **ausgelieferten** `team-kits/dev-team/hooks/gate_write_scope.py` als Prozess,
JSON auf stdin, gescaffoldetes Projekt außerhalb dieses Repos mit gültigem Wurzelitem
(`C:\Trash\tsk0023-r10\gate_probe.py`, `gate_probe2.py`):

```
rc 2  Bash        cp project_memory/legacy/a.yaml ../v1-legacy-overflow/<name>
rc 2  Bash        cp -p project_memory/legacy/a.yaml '<absolutes Ziel>'
rc 2  Bash        python -c "import shutil; shutil.copy(r'<abs>', r'<abs>')"
rc 2  PowerShell  Copy-Item project_memory\legacy\a.yaml ..\v1-legacy-overflow\<name>
rc 2  PowerShell  Copy-Item '<abs>' '<abs>'
rc 2  Bash        rm project_memory/legacy/a.yaml
rc 2  PowerShell  Remove-Item project_memory\legacy\a.yaml
rc 0  Bash        cat project_memory/legacy/a.yaml > ../v1-legacy-overflow/<name>
rc 0  Bash        cat < project_memory/legacy/a.yaml > ../v1-legacy-overflow/<name>
rc 0  PowerShell  Get-Content project_memory\legacy\a.yaml > ..\v1-legacy-overflow\<name>
rc 0  Bash        cat project_memory/legacy/a.yaml            (reines Lesen, Kontrolle)
```

**Abweichung vom Prüferbefund, und sie ist der Grund, den Halbsatz nicht blind einzusetzen:** „alle
Kopier-Schreibweisen rc 2" hält nicht. Die Kopierbefehle sind rc 2 — die Quelle unter
`project_memory/` genügt dem Gate —, aber eine **Umleitung**, die die Quelle nur liest und außerhalb
landet, ist rc 0. Ein eingesetzter Halbsatz „das geht nur außerhalb der Sitzung" wäre also selbst
eine Behauptung, die der Code nicht trägt. Eingetragen in `L35` mit genau dieser Zweiteilung; nicht
gebaut.

## R10.4 B4 — wogegen die Pfade dieses Berichts zu lesen sind

Der Bericht nannte seine Basis nirgends, und `../v1-legacy-overflow/…` ist der eine Pfad, dessen
falsche Basis **stillschweigend gelingt** (von der Projektwurzel aus eine Ebene über dem Projekt,
statt neben dem Zustandsverzeichnis). Steht jetzt einmal im Kopf, Abschnitt 0, erster Punkt.

## R10.5 B5 — `.claude/hooks/test_gates.py` ist rot

Nicht dieser Runde zuzurechnen (Dateien vom 2026-08-08, Ausfall aus TSK-0022) und in `.claude/`,
dem verbotenen Bereich dieses Items. Erfasst als `project_memory/bugs/active/BUG-0014.yaml`, in der
Löcherliste als `L38` mit Verweis darauf. **Nicht angefasst.**

## R10.6 Abnahmelauf der Runde 10

Siehe den Abschluss unten; geändert wurden in dieser Runde `tools/test_migrate.py`,
`docs/POST_V2_WISHLIST.md` und dieses Protokoll — **keine** Kit-Datei, also auch keine Spiegelung.

**Sandkasten, Sonden und Klon dieser Runde** liegen nach DEC-0026 unter `C:\Trash\tsk0023-r10\` —
nichts gelöscht.
