# Messprotokoll TSK-0018 (2026-08-07)

Fortsetzung von `docs/reviews/2026-08-05-tsk0013-measurements.md` fuer die Migrationslinie. Dieses
Dokument traegt die Ketten zu den beiden blockierenden Befunden der Pruefung von TSK-0016 und zu
den Resten, die dieselbe Runde gemeldet hat.

Es enthaelt **keine** Behauptung ohne Messung. Wo eine Zahl steht, steht daneben, womit sie
gemessen wurde; wo etwas nicht messbar war, steht das ausdruecklich da.

## Wie gemessen wurde

- **Echte Hook-Prozesse.** Jede rc-Zeile ist ein `subprocess`-Start des ausgelieferten Skripts mit
  JSON auf `stdin`, gegen ein Projekt **ausserhalb** dieses Repos (`tempfile.mkdtemp`), dessen
  Wurzelitem durch den Kernel geschrieben wurde. `2` = Verweigerung, `0` = Durchlass.
- **Mutationen in einem Klon ausserhalb des Repos** (`C:\tmp-harness\tsk0018\m1`): der Defekt wird
  dort wiederhergestellt, der zugehoerige Test darin gefahren, das Rot gesehen, die Datei aus dem
  Arbeitsbaum zurueckkopiert.
- **Zeiten** mit `time.perf_counter`, je Punkt mehrere Laeufe, mit dem Schaetzer daneben (Minimum
  oder Median, jeweils benannt).

## 1. F1 -- ein Dokument, das der Leser nicht parsen kann, war fuer SR-0001 stumm

Gate `gate_memory_complete.py` als Prozess, eigenes Scaffold, gueltiges Wurzelitem, Zeile
`git merge feat/PR-0001-x`. Das Zusatzdokument ist `project_memory/old_procs.yaml`.

| Zustand des Zusatzdokuments | vorher | nachher |
|---|---|---|
| fehlt | rc 0 | rc 0 |
| lesbar, mit einem V1-Datensatz (`PROC-0001`, `status: ACTIVE`) | **rc 2** | **rc 2** |
| dieselbe Datei plus `  PROC-0002: {` -- der Datensatz steht im Klartext weiter drin | **rc 0** | **rc 2** |
| Tabulator-Einrueckung plus Listenelement unter einem Mapping (Syntaxfehler) | **rc 0** | **rc 2** |

Die Verweigerung nennt jetzt in beiden unteren Zeilen `NOT SEARCHED for V1 backlog records: it
could not be parsed (...)`.

**Die Ursache war die Form, nicht die vergessene Zeile.** `report._check_no_v1_records_outside_the_archive`
kannte zwei Gruende zu ueberspringen (die beiden Budgets) und meldete beide; der dritte Weg --
`_read_document` gibt einen Fehler zurueck -- fiel in ein `continue`. Der Kopfkommentar derselben
Funktion behauptete dazu die Eigenschaft ("was uebersprungen wird, wird gemeldet"). Gebaut war eine
Aufzaehlung. Der Bau ist jetzt so, dass die Eigenschaft aus der Struktur folgt: der einzige Weg zur
Datensatzsuche fuehrt durch ein Dokument, das innerhalb beider Budgets lag **und** geparst wurde;
jeder andere Weg baut dieselbe Meldung aus seinem eigenen Grund.

**Trockenlauf und Validator widersprechen sich nicht mehr.** `migrate._read_document` liefert seinen
Grund jetzt **ohne** Pfad; jeder der drei Aufrufer setzt den Namen davor, den er ohnehin hat. Vorher
stand der Pfad in der Meldung, und der Validator, dessen Befund den Pfad als `item` traegt, haette
ihn doppelt genannt.

Rote Tests ohne den Fix (Klon, Defekt wiederhergestellt):

- `tools/test_migrate.py::test_an_unparsable_document_is_unsearched_and_still_refuses_the_merge`
  -- `AssertionError: a document this scan could not read was passed over: []`, und danach der
  Gate-Prozess mit rc 0.
- `tools/test_migrate.py::test_the_dry_run_and_the_validator_name_an_unreadable_document_the_same_way`
  -- `AssertionError: []`.

## 2. F2 -- ein Verhaeltnis, das die Maschine nicht herausrechnet

`test_the_id_scan_is_linear_on_the_worst_legal_input` verglich den dichten Lauf mit einem harmlosen
Lauf gleicher Groesse und nannte den **Quotienten** maschinenunabhaengig. Der Prozessstart ist ein
**additiver** Term in beiden Zaehlern, also ist der Quotient `(start + scan) / start` und damit
vollstaendig eine Funktion der Startkosten des Rechners.

Gemessen auf diesem Host, ausgelieferter Hook als Prozess:

| | Zeit |
|---|---|
| harmloser Lauf, 200 KB | 0,0612 s |
| dichter Lauf, 200 KB | 0,7747 s |
| Quotient | **12,65** gegen eine Schranke von 5 -- rot, bei linearem Scan |

Der Test misst jetzt die **Kosten je Zeichen an zwei Groessen** und subtrahiert dabei den Start,
statt durch ihn zu teilen. Zwei Laeufe gleicher Groesse zahlen denselben Start, dieselbe
stdin-Lektuere und dieselbe Dateilektuere; ihre Differenz ist der Scan.

Ausgelieferter Stand, Median aus 3 Laeufen je Punkt, subtrahierte Scankosten:

| Groesse | 25 KB | 50 KB | 100 KB | 200 KB | 400 KB |
|---|---|---|---|---|---|
| s je KB | 0,0034 | 0,0034 | 0,0035 | 0,0038 | 0,0035 |

Quadratische Form im Klon wiederhergestellt (`\S{0,1000}` -> `\S*`), dieselben zwei Groessen des
Tests. Der Test wird damit rot.

**Die Sekunden dieser Mutante sind eine Zahl dieses LAUFS, nicht des Defekts** -- diese Zeile stand
bis zum 2026-08-07 absolut da und war damit eine Behauptung, die kein zweiter Lauf haelt. Zweimal
gemessen, derselbe Klon, derselbe Rechner:

| Lauf | 50 KB | 200 KB | s je KB | Faktor | rote Zeile |
|---|---|---|---|---|---|
| TSK-0018 | 5,96 s | 74,54 s | 0,119 / 0,364 | 3,1 | `it is not linear in the input` |
| Nachmessung TSK-0020 | 5,37 s | 76,41 s | 0,105 / 0,373 | 3,6 | `it is not linear in the input` |

Invariant ist allein die **Richtung** (ueberlinear ueber eine Vervierfachung). Auch die FORM der
Roetung ist hostabhaengig: es kann die Linearitaets-Zusicherung sein, die Stabilitaets-Lesart
darueber (wenn der Prozessstart genug rauscht) oder `subprocess.TimeoutExpired` aus `run_budget`
auf einem Rechner, der bei 200 KB mehr als dessen 120 s braucht. Alle drei sagen dasselbe: der Scan
bleibt nicht im Budget. Der Docstring des Tests sagt das jetzt so.

**Und der Name haelt jetzt, was er verspricht:** gemessen wird die Linearitaet ueber zwei Groessen,
nicht eine einzelne Groesse.

**Der Boden darunter ist gemessen, nicht gehofft.** Schaetzer je Serie ist das **Minimum** aus fuenf
Laeufen (Prozesszeit hat nur Rauschen nach oben), und der Abstand zum zweitschnellsten Lauf ist das
Mass fuer die Stabilitaet dieses Schaetzers. Liegt der Scan bei der kleinen Groesse nicht um den
Faktor 5 darueber, faellt der Test **mit dieser Lesart** aus, statt auf Rauschen zu urteilen.

Vier Laeufe unbelastet: gruen, 7,8 s. Ein Lauf unter acht rechnenden Prozessen auf diesem Host:
gruen, 11,1 s.

## 3. Die Digest-Verweigerung zaehlte drei Ursachen; ein Plan hat drei Arten von Eingabe

Gemessen: `backlog_types.OPTIONAL_FIELDS` fuer `PROC` um einen Eintrag erweitert -- kein Byte unter
dem Zustandsverzeichnis, keine Flagge, keine Registrierung beruehrt:

| | vorher | nachher |
|---|---|---|
| `migrate.state_fingerprint` | unveraendert | unveraendert |
| `layout.gated_documents` | unveraendert | unveraendert |
| `migrate.plan_digest` | **wandert** | **wandert** |
| Verweigerung nennt die Ursache | nein | ja (`CODE AND TABLES`) |
| Verweigerung nennt einen Ort, der antwortet | nein | ja (`doctor`, `kit_version`) |

Der Leser wurde vorher an `state_fingerprint` und `layout.gated_documents` geschickt; beide
antworten zu diesem Fall nichts.

Die Meldung zaehlt jetzt nicht Ursachen, sondern zerlegt: ein Plan ist eine deterministische
**Berechnung** und kann sich nur aendern, wenn eine ihrer Eingaben sich aendert -- was gelesen wurde
(Zustandsverzeichnis und Hook-Registrierung), was gesagt wurde (die Flaggen), und womit gerechnet
wurde (Code und Tabellen des Kernels). Das ist konstruktiv geschlossen; eine Dreierliste war es
nicht. Dazu sagt die Meldung jetzt ausdruecklich, was sie **nicht** kann: sagen, welche der drei
sich bewegt hat -- sie haelt den Digest des gelesenen Plans, nicht diesen Plan.

**Gegenprobe, im selben Test:** eine Kernelkonstante, aus der der Plan **kein** Verdikt zieht
(`ITEM_MAX_LINES` um 300 erhoeht, kein Datensatz dieses Zustands kommt der Grenze nahe), bewegt den
Digest **nicht**. Der Digest ist ueber den Plan, nicht ueber die Version des Harness.

Roter Test ohne den Fix: `tools/test_migrate.py::test_moving_the_kernels_own_contract_table_alone_moves_the_digest`
(`assert 'CODE AND TABLES' in ...`), im Klon gegen die alte Dreier-Meldung gefahren.

## 4. Der `legacy/`-Zielpfad wurde zweimal zusammengesetzt

`render` schrieb `"legacy/" + Pfad`, `_retire_absorbed_documents` verschiebt nach
`ProjectState.legacy_path`. Beide Schreibweisen stimmen heute ueberein -- das ist eine
Uebereinstimmung zweier Zeichenketten, keine Eigenschaft, und genau die Form, die diese Runde beim
Archivpfad behoben hat (dort trennte `.lower()` die beiden auf case-sensitiven Dateisystemen).

Weil kein Eingabewert die beiden heute trennt, wird durch den **Erzeuger** gemessen: das
Legacy-Verzeichnis wird im Test auf `retired_v1` gelegt, dann muss der gedruckte Pfad folgen.

| | gedruckt | auf der Platte |
|---|---|---|
| vorher | `legacy/process_definitions.yaml` | `retired_v1/process_definitions.yaml` |
| nachher | `retired_v1/process_definitions.yaml` | `retired_v1/process_definitions.yaml` |

Roter Test ohne den Fix: `tools/test_migrate.py::test_the_legacy_path_the_dry_run_prints_is_the_one_the_run_moves_the_document_to`.

## 5. Ein Messkommentar nannte eine Bibliothek, die dieser Leser nicht benutzt

`migrate._read_document` ruft `yaml.safe_load`, und das ist `yaml.SafeLoader` -- der **reine
Python-Loader**. Auf diesem Host ist `yaml.__with_libyaml__` True und `yaml.CSafeLoader` vorhanden;
nichts auf diesem Pfad fragt danach. Die notierte Kurve stand unter "PyYAML with libyaml".

Nachgemessen mit `_check_no_v1_records_outside_the_archive` direkt, ein bueroartiges
`filing_log.yaml` aus datierten Eintraegen, Budgets fuer die Messung angehoben:

| Groesse | bester von 3 | s je MB | erster (kalter) Lauf, s je MB |
|---|---|---|---|
| 1 MB | 1,85 s | 1,85 | 3,88 |
| 2 MB | 2,90 s | 1,45 | 2,92 |
| 4 MB | 6,36 s | 1,59 | 4,24 |
| 8 MB | 18,01 s | 2,25 | 3,93 |

Die Kosten je MB sind **nicht** konstant, und der erste Lauf jeder Groesse liegt um Faktor 1,7 bis
2,7 darueber. Damit kostet das Gesamtbudget von 8 MB rund **18 s warm und 31 s kalt** -- nicht die
"zwoelf Sekunden", die der Kommentar rechnete, sondern ein Drittel bis die Haelfte der 60 s, die ein
PreToolUse-Hook fuer **alles** hat. Der Kommentar sagt das jetzt so.

## 6. Die Prosa-Regel entscheidet Wort-Kovorkommen, nicht Paarung

`test_no_shipped_text_says_an_import_arrives_at_its_initial_status_full_stop` fragt drei Wortlisten
an einem Satz ab. Der Docstring behauptete "die Paarung". Gemessen an den ausgelieferten Regexen,
eine Probe je Richtung:

| Satz | Urteil | wahr? |
|---|---|---|
| `Imports arrive at their INITIAL status, never at the mapped one.` | geht durch | **falsch** |
| `A record the table calls unfinished is imported at its initial status.` | **abgelehnt** | wahr |
| `Importierte Items kommen im Anfangsstatus an und tragen keine Freigabe.` | geht durch | falsch |
| `Every imported PROC arrives in DRAFT and carries no approval.` | geht durch | falsch |

Deckung ueber das abgeleitete Korpus, am selben Tag gezaehlt: **2704 Saetze in 70 Dokumenten**, 56
mit einem Import-Wort, 2 mit einem Anfangsstatus-Wort, und **genau einer**, der beide Listen trifft
und ueberhaupt angesehen wird.

Der Docstring sagt das jetzt, mit allen vier Proben, und der Test faellt, wenn diese Zahl **null**
erreicht -- eine Pruefung, die nichts ansieht, ist kein gruenes Licht. Roter Nachweis im Klon: den
einen angesehenen Satz in `README.md` umformuliert, Test rot.

Was **nicht** gebaut wurde: eine echte Paarung. Ob ein Satz die Haelfte behauptet oder sie
verneint, ist eine Lesart; ein Pruefer, der einen richtigen Satz meldet, ist schlechter als keiner
-- die zweite Probe oben ist bereits dieser Fall und ist der Preis der ersten.

## 7. Die Begruendung des Zitat-Praedikats traf nicht alle Faelle

`test_every_citation_in_the_migration_addenda_carries_the_wording_it_cites` prueft nur die
II.10-Nachtraege. Die Begruendung dafuer lautete, der Rest der Spec zitiere "die Welt ausserhalb
dieses Repos".

Gezaehlt mit dem Leser dieser Datei: **35 zitatfoermige Spannen in der Spec**, davon 7 in den
Nachtraegen (alle 7 aufloesbar) und 28 ausserhalb, davon **17 unaufloesbar**. Die Einordnung haelt
grossteils -- eine Herstellerdoku, eine Produktoberflaeche, Forschungsquellen -- und fuer mindestens
drei Spannen nicht: `Prefer Mermaid over draw.io` ist in II.6a als **eigenes frueheres Kit-Ruling**
zitiert, `je <=150 Zeilen` als **eigene fruehere Zeilengrenze**, `Derived 1:1 from ... v1.11` als
**Kopfzeile des eigenen V1-Ablageplans**. Alle drei sind Artefakte dieses Repos, die keine Zeile
hier mehr traegt.

Damit ist die Grenze nicht "alles dort draussen ist fremd", sondern: ausserhalb der Nachtraege
tragen dieselben Marken Zitate, Paraphrasen **und** Zitate zurueckgezogenen Textes, und ein Zitat
von etwas Zurueckgezogenem liest sich genau wie ein falsch abgeschriebenes. Der Docstring sagt das
jetzt so; die Zahlen sind als Lesart eines Tages gekennzeichnet und werden von nichts gepinnt.

## 8. Die Feldzahl zur Scan-Obergrenze

Gemessen am 2026-08-07 gegen die beiden echten Feldprojekte auf diesem Rechner, mit derselben
Auswahl, die der Scan trifft (`layout.is_project_document`, nur `*.yaml`/`*.yml`):

| Projekt | Kit-Dokumente | Summe | Anteil am Gesamtbudget (8 MB) | groesste Datei | Anteil an der Einzelgrenze (2 MB) |
|---|---|---|---|---|---|
| `C:\Offline Repos\synaipse` | 20 | 5 114 314 B | **63,9 %** | `design.yaml`, 1 015 193 B | **50,8 %** |
| `C:\Offline Repos\portfoliomanaigement` | 20 | 977 588 B | 12,2 % | `system_requirements.yaml`, 125 983 B | 6,3 % |

Die Antwort auf "trifft ein echtes Projekt die Grenze?" lautet damit nicht *nein*, sondern *noch
nicht*. Der Eintrag zur Scan-Obergrenze in der Loecherliste traegt diese Zahl heute nicht; sie
gehoert dorthin. Diese Runde durfte die Datei nicht anfassen (ein zweiter Umsetzer schrieb parallel
darin), deshalb steht die Zahl hier und im Bericht.

## 9. Suite

`python -B -m pytest tools/ -q`, ein Lauf, nichts parallel, Host im Leerlauf:

| Lauf | Ergebnis | Dauer |
|---|---|---|
| vor dieser Runde (Pruefbericht) | 2291 gruen, **1 rot** (Abschnitt 2) | -- |
| nachher | **2296 gruen, 12 uebersprungen** | 17:31 |

Ein frueherer Lauf dieser Runde meldete einen Fehlschlag in `tools/test_report.py` mit
`subprocess.TimeoutExpired ... gate_approval.py ... after 120 seconds`. Ursache gemessen und
benannt: zehn Rechenprozesse aus der Lastmessung zu Abschnitt 2 waren auf diesem Host nicht beendet
worden (je rund 1000 s CPU, Start 08:04). Nach ihrem Ende lief dieselbe Datei in 20 s durch und die
volle Suite gruen. Das war die Messumgebung, nicht der Code -- und es ist derselbe Mechanismus, den
Abschnitt 2 fuer den Linearitaetstest ausgeschlossen hat: dort haelt die Messung unter Last, hier
lief ein Test mit fester 120-s-Frist gegen einen ueberlasteten Rechner.
