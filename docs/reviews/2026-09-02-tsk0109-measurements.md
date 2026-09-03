# TSK-0109 — Messungen der Build-Phase (Finanz-Dashboard des Office-Kits, FR-0032)

Stream I, zweite Generation nach DEC-0060, Phase 2 (Opus). Phase 1 (Fable) liegt als Designpaket in
`project_memory/staging/TSK-0109/`; dieses Blatt trägt nur, was die **Build-Phase** gegen den
laufenden Code gemessen hat. Alle Läufe außerhalb des Repos unter
`C:\Offline Repos\v2-testbed\_round-scratch\TSK-0109\`, gegen Office-Projekte, die aus den
Kit-Vorlagen zusammengesetzt wurden (`scripts/`, `tools/`, `dashboards/`, Hooks, Kernel).

## 1. Parität mit `euer_report.py` — 8 von 8 Quartalen

Die Seite wird vom ausgelieferten Generator geschrieben, der Bericht vom ausgelieferten
`scripts/euer_report.py` als Prozess; verglichen werden die Zahlen, die **auf der Seite stehen**
(DOM geparst), nicht die, die eine Funktion zurückgibt.

| Zeitraum | Bericht Einnahmen / Ausgaben | Seite | Offene Posten Bericht / Seite |
|---|---|---|---|
| 2025 Q1 | 3.470,11 / 2.753,63 | gleich | 0 / 0 |
| 2025 Q2 | 4.314,12 / 2.894,99 | gleich | 0 / 0 |
| 2025 Q3 | 4.661,00 / 4.329,67 | gleich | 0 / 0 |
| 2025 Q4 | 7.327,25 / 4.319,70 | gleich | 0 / 0 |
| 2026 Q1 | 20.264,02 / 15.305,63 | gleich | 0 / 0 |
| 2026 Q2 | 25.089,25 / 19.022,12 | gleich | 2 / 2 |
| 2026 Q3 | 15.857,13 / 9.235,24 | gleich | 5 / 5 |
| 2026 Q4 | 0,00 / 0,00 | gleich | 5 / 5 |

**Was daran eine Ableitung ist und in der Design-Phase noch Zufall war.** Die Zahl der offenen
Posten des Berichts kommt aus **einer** Datei (`ledger/<Jahr>.csv`), die der Seite aus allen. In der
Fixture stimmten beide, weil kein Ledgerjahr eine offene Zeile aus einem früheren Jahr trägt — eine
Eigenschaft der Beispieldaten, keine des Codes. Der Generator zählt jetzt je Ledgerjahr
(`open_until`), und der Grund steht dort: `ledger_add.validate_cross` legt jede Zeile in die Datei
von `payment_date or doc_date`, also liegt eine **offene** Zeile in der Datei ihres Belegjahres —
genau der Datei, die der Bericht öffnet.

## 2. Rot-zuerst der Bauphase

Kopie des Baums außerhalb des Repos (`_round-scratch/TSK-0109/clone/`), je ein Defekt eingesetzt,
der eine Test gefahren, danach zurückgesetzt; Werkzeug `_round-scratch/TSK-0109/redfirst.py`.
Je Zeile der Tabelle **rot**; die beiden Enden des Aktenfach-Drahts sind einzeln mutiert, stehen
hier aber in einer Zeile.

Diese Tabelle ist der Stand der **Bauphase**. Die Zahlen, die hier bis zur Nacharbeit als
Kopfzeilen standen („zwölf/15 passed/12 von 12"), waren gegen den Baum nicht haltbar — der Prüfer
zählte 16 passed bei 13 Testfunktionen und 14 Rot-zuerst-Läufen. Der Stand nach der Nacharbeit
steht in Abschnitt 8, gemessen; hier bleibt nur, was die Bauphase wirklich gefahren hat.

| Test | eingesetzter Defekt | Ergebnis |
|---|---|---|
| `test_the_dashboard_and_euer_report_agree_on_every_quarter` | Vorzeichenregel abgeschrieben (`sign = 1` statt `euer_report.sign_of`) | RED |
| `test_the_generator_writes_exactly_one_file` | `os.replace` durch `copyfile` ersetzt — die Temp-Datei bleibt liegen | RED |
| `test_the_same_tree_renders_the_same_bytes` | `time.time()` in die Kopfzeile | RED |
| `test_the_documented_command_passes_the_write_scope_gate` | dokumentierter Befehl nennt `project_memory` | RED |
| `test_filters_narrow_rows_and_the_sum_follows` | Summe folgt den sichtbaren statt allen passenden Zeilen | RED |
| `test_dunning_candidates_follow_the_frozen_clock` | Richtung invertiert (Verbindlichkeiten bekommen den Stempel) | RED |
| `test_an_empty_project_renders_a_direction` | fehlendes `ledger/` wirft statt leer zu rendern | RED |
| `test_an_invalid_ledger_is_named_on_the_page` | Validierung übersprungen | RED |
| `test_the_threshold_verdict_switches_at_the_limits` | `>` zu `>=` an der Vorjahresgrenze | RED |
| `test_the_page_makes_no_request_beyond_itself` | Webschrift per `<link>` eingebunden | RED |
| `test_every_template_slot_is_filled` | neuer Slot in der Vorlage, vom Generator nicht gefüllt | RED |
| `test_a_kleinunternehmer_false_profile_hides_the_watch_and_null_names_the_gap` | Reiter aus der Wahrheitswertigkeit des Feldes statt aus `is not False` | RED |

## 3. Was die Sicht-Schleife gefunden hat (BUG-0076-Doktrin)

54 Bilder aus dem **gebauten** Stand, drei Zustände × fünf Reiter × 1280/390/dunkel plus Filter-,
Detail- und Mahnansicht und ein Lauf ohne Skript; Datensatz
`project_memory/staging/TSK-0109/review-build/render.json`, Konsolen-/Seitenfehler in allen 54
Läufen: **0**. Gesichtet (angesehen, nicht nur erzeugt) wurden Überblick 1280/390, Rechnungen
1280/390, Rechnungen gefiltert, Offene Posten dunkel, EÜR, Kleinunternehmer (Alarm), Überblick leer
und der Lauf ohne Skript.

Zwei Befunde, beide korrigiert und nachgerendert:

1. **Ein Betrag, zwei Schreibweisen auf einer Seite.** Das Seitenskript trennte Betrag und
   Eurozeichen mit einem geschützten Leerzeichen (U+00A0), der Generator mit einem gewöhnlichen —
   also stand die Anfangssumme anders da als dieselbe Summe nach einem Filter. Gefunden vom
   Filtertest, der die Seitenschrift gegen eine dritte, unabhängige Schreibweise vergleicht.
   Geschlossen als eine Konstante (`CURRENCY_GAP`) mit dem Grund daneben.
2. **„1 Rechnungen zu zahlen".** Deutsche Zählungen lesen sich im Singular falsch; im Bild sofort
   sichtbar, im Test nicht. Geschlossen mit `plural()`; nachgerendert und wieder angesehen.

## 4. H117 — kein Auslöser: eine Buchung bewegt die Seite nicht

Echtes Office-Projekt mit den ausgelieferten Hooks, PostToolUse als Prozess:

```
python tools/finance_dashboard.py                         rc 0   Seite d7a311abcbd6e397
python scripts/ledger_add.py --year 2026 … --open …       rc 0   L2026-0134 angehängt
gate_ledger_valid.py  (PostToolUse, Bash)                 rc 0   validiert, sonst nichts
Seite danach                                              d7a311abcbd6e397  UNVERÄNDERT
python tools/finance_dashboard.py  (erneut)               Seite c29fde2ca6ce16a2  ANDERS
```

Die vierte Zeile ist das Loch: die Seite war nach der Buchung veraltet und nichts sagte es. Der
Auslöser gehört in `gate_ledger_valid.handle_post_tool_use` — die einzige Stelle, an der beide
Schreibwege des Ledgers vorbeikommen — und diese Datei gehört Stream G; die Zeile steht wörtlich im
Build-Protokoll in `project_memory/staging/TSK-0109/`.

## 5. H118 — die zeitabhängige Hälfte rechnet im Browser

Dieselbe Datei, drei Leser:

```
Uhr 2026-09-02   Mahnstempel 2   [data-overdue-count] "2"   erstes Alter "91 Tage"
Uhr 2026-07-01   Mahnstempel 0   [data-overdue-count] "0"   erstes Alter "28 Tage"
ohne Skript      Mahnstempel 0   [data-overdue-count] "…"   erstes Alter "—"
```

Kein Wert davon steht in der Datei; alle drei entstehen beim Öffnen. Eine falsch gestellte
Rechneruhr ändert damit still die Antwort auf „muss ich mahnen" — und ohne Skript gibt die Seite
gar keine.

## 6. H119 — keine Herkunft, und der Generator ist dem Ledger-Gate kein Bericht

Projekt mit ungültigem Ledger (die BUG-0072-Form: `net 214.20 … != gross 14.28`), Hooks als
Prozesse:

```
python scripts/euer_report.py --year 2026 --quarter 3     rc 2   VERWEIGERT (_BLOCKED_SCRIPT_RX)
python tools/finance_dashboard.py                          rc 0   DURCHGELASSEN
derselbe Lauf                                              rc 0   „Ledger UNGÜLTIG" auf stdout und im Banner
Seite von Hand ergänzt: sha e2f4e8d9971e8442 -> 1528b8cbb8bd0dbd
Etwas im Baum, das das bemerken würde:                     nichts (kein Renderdatensatz)
```

## 7. Läufe der Bauphase

- `tools/test_finance_dashboard.py`: grün.
- `python -m ruff check .`: sauber.
- Sicht-Schleife: 54 Bilder, 0 Konsolen-/Seitenfehler.

## 8. Nacharbeit 1 (nach dem Prüfbericht und dem Inhaltswunsch des Nutzers)

Alle Läufe dieser Runde außerhalb des Repos unter `_round-scratch/TSK-0109/rework/`; die Werkzeuge
des Prüfers wurden gefahren, nicht nachgebaut (`stale.py`, `redfirst2.py`, `mutate.py`).

### 8.1 Die drei Zeilen (Brutto / Netto / USt) — Parität gegen Bericht **und** gegen eine dritte Lesart

Neue Fixture `crossyear` (Regelbesteuerung), Seite gegen den ausgelieferten `euer_report.py` und
gegen eine Aggregation, die `tools/test_finance_dashboard.py::csv_quarter` selbst aus der CSV
rechnet. Acht Quartale, alle drei Lesarten gleich:

| Zeitraum | Einnahmen / Ausgaben (brutto) | USt aus / Vorsteuer | Zahllast (Seite) | offene Posten |
|---|---|---|---|---|
| 2025 Q1 | 3.570,00 / 595,00 | 570,00 / 95,00 | 475,00 | 0 |
| 2025 Q4 | 0,00 / 0,00 | 0,00 / 0,00 | keine bezahlte Buchung | **2** |
| 2026 Q1 | 5.950,00 / 952,00 | 950,00 / 152,00 | 798,00 | 0 |
| 2026 Q2 | −474,00 / 200,00 | −95,00 / 0,00 | −95,00 | 0 |

(Die übrigen vier Quartale sind leer und stimmen ebenso; der Testlauf prüft alle acht.)

**Was der Nutzerwunsch in den zwei Steuerzuständen zeigt**, gemessen an den Fixtures:

| Zustand | Einnahmen | Ausgaben | Überschuss |
|---|---|---|---|
| `crossyear` (Regelbesteuerung) | 5.476,00 / 4.621,00 / 855,00 | 1.152,00 / 1.000,00 / 152,00 | 4.324,00 / 3.621,00 / **Zahllast 703,00** |
| `regular` (§ 19 UStG) | 61.210,40 / 61.210,40 / *keine USt — Kleinunternehmer § 19 UStG* | 43.562,99 / 43.562,99 / dieselbe Aussage | 17.647,41 / 17.647,41 / dieselbe Aussage, keine Zahllast |
| `alarm` (§ 19 im Profil, Grenze überschritten) | 59.511,20 / 59.511,20 / *USt nicht belastbar* | 42.254,61 / 42.254,61 / dito | 17.256,59 / 17.256,59 / dito |

**Der Befund, den die eigene Messung erzwungen hat.** Eine Aufteilung, die nur den Zeilen folgt,
druckte für `regular` (Einnahmen als `kleinunternehmer` gebucht, Ausgaben als `standard`)
**„USt-Zahllast −6.077,56 €"** — einen Erstattungsanspruch, den § 19 Abs. 1 UStG in Verbindung mit
§ 15 Abs. 2 Satz 1 Nr. 1 UStG ausschließt (Rechtsgrundlage in Abschnitt 9.5 nachgelesen). Der
Steuerzustand entscheidet deshalb, nicht die einzelne Zeile: `tax_state()`.

Die informativen Zahlen des Berichts stehen trotzdem auf der Seite (EÜR-Reiter, „Umsatzsteuer (nur
informativ)"): **zwei**, nämlich vereinnahmte USt 0,00 und Vorsteuer 6.077,56 — das ist, was
`euer_report.py` druckt. Eine **dritte** Zahl (die Differenz, als „Zahllast" beschriftet) stand
dort bis zur Nacharbeit 2 und war der zweite Druckort derselben unmöglichen Zahl; Abschnitt 9.2.
So bleibt die Parität mit dem Bericht sichtbar und die Aussage trotzdem richtig.

### 8.2 Die Zählweise der offenen Posten (Befund B1)

`trap.py` des Prüfers, nachgebaut als Fixture `crossyear`: offene Rechnung 2025, storniert durch
eine Zeile in `2026.csv` (`ledger_add.validate_cross` nimmt das ausdrücklich an, beide Dateien sind
`--validate`-gültig). Vorher sagte die Seite für 2025 Q4 **1**, der Bericht **2**.

Entschieden: **der Bericht ist die Autorität** (er liegt im `forbidden_scope` dieses Streams). Der
Generator führt jetzt zwei Lesarten — `rows` mit den Stornos aller Dateien für die eigenen
Ansichten, `report_rows` mit den Stornos **je Datei** für den EÜR-Reiter — und sagt, wo sie
auseinanderfallen: „davon 1 in einem anderen Ledgerjahr storniert; der Bericht liest nur
ledger/2025.csv". Der Vorschlag an die Merge-Runde (Naht, hier nicht gebaut) steht im
Build-Protokoll.

### 8.3 Rot-zuerst dieser Runde — 13 Defekte, 13 rote Läufe

Klon des Arbeitsbaums außerhalb des Repos (`rework/clone/`), Werkzeug `rework/redfirst.py`.

| # | eingesetzter Defekt | roter Test |
|---|---|---|
| B1a | `open_until` ohne Jahresbindung | `…agree_on_every_quarter[crossyear]` |
| B1b | offene Posten aus der ledgerweiten Statuslesart | `…agree_on_every_quarter[crossyear]` |
| A1 | § 19: Vorsteuer trotzdem abgezogen | `…agree_on_every_quarter[regular]`, `…three_lines…[regular-True]` |
| A2 | Zahllast nicht Einnahmen minus Ausgaben | `…three_lines…[crossyear-False]` |
| A3 | Null statt Aussage in der USt-Zeile | `…agree_on_every_quarter[regular]` |
| M2 | kein Vorjahr fällt still auf „within" | `…threshold…[None-2600000-previous_unknown]` |
| M3 | Balken ohne dritten Zweig | `…threshold…[None-2600000-previous_unknown]` |
| M6 | `CURRENCY_GAP` als gewöhnliches Leerzeichen | `test_filters_narrow_rows_and_the_sum_follows` |
| N8 | Streudatei wieder still übersprungen | `…a_file_in_ledger_that_no_report_reads…` |
| N9 | PyYAML-Import ohne Verweigerung | `…a_missing_pyyaml_is_a_sentence…` |
| N10 | zweites Kit mit abweichender Kopie unter `templates/repo/tools/` | `test_hooks.py::test_shared_kit_files_identical` |
| M4 | ein Gate der Kette verweigert (`gate_filing`) | `…documented_command_passes_the_write_scope_gate` |
| — | Plural: das Skript wählt immer die Mehrzahl | `…dunning_candidates…[crossyear]` |

Grundlinie nach jedem Zurücksetzen: **23 passed**.

**Die zweite Hälfte von M4**, weil ein roter Test allein nicht zeigt, dass die alte Lesart blind
war — dieselbe Mutation, zwei Leser, gemessen mit `rework/m4_counter.py`:

```
ALT (nur das letzte Wort je Eintrag):   6 Gates, alle rc 0   -> schlechtester rc: 0
NEU (die registrierte Kommandozeile):   6 Zeilen, 8 Gates    -> rc 2 auf _gate.py gate_filing.py gate_second_reading.py
```

**Die Mutationen des Prüfers**, gegen den nachgearbeiteten Baum erneut gefahren
(`verify-2/rig/redfirst2.py`, nur die Pfade umgebogen):

```
M3 CURRENCY_GAP -> Leerzeichen        4 failed, 18 passed
M4a Ordnerführer heißt README.txt     1 failed, 21 passed
M4b dashboards in document_trays.txt  1 failed, 21 passed
M5 Vorzeichenregel abgeschrieben      3 failed, 19 passed
M6 open_until ohne Jahresbindung      1 failed, 21 passed      (vorher: 16 passed, kein roter Test)
Grundlinie unverändert                23 passed
```

### 8.4 Das Gründungsjahr (Befund M2)

`business_profile.yaml` der Kit-Vorlage trägt **kein** Gründungsdatum und kein Gründungsjahr
(gelesen, nicht angenommen: unter `tax:` stehen `kleinunternehmer`, `vat_id`, `oss`,
`fiscal_year`). Also wird die Aussage verweigert statt geraten. Fixture `founding` (nur
`2026.csv`, 26.000 €, `kleinunternehmer: true`):

```
vorher   VERDICT within             „innerhalb der Grenzen — 26.000,00 von 100.000,00"
nachher  VERDICT previous_unknown   Stempel „unklar"; Balken Vorjahr gestrichelt und leer,
                                    „kein Ledger für 2025 (Grenze 25.000,00 €) — nicht belastbar";
                                    Satz nennt beide Fälle (Gründungsjahr -> 25.000 € fürs
                                    laufende Jahr, sonst fehlt nur die Datei) und die
                                    Steuerberatung
```

Das Feld im Profil und der Onboarding-Satz sind eine Naht an Stream G, wörtlich im Build-Protokoll.

### 8.5 Der Datenstand ist kein Alterssignal (Befund M5)

Mit dem Rig des Prüfers (`stale.py`) gegen den nachgearbeiteten Baum:

```
vor der Buchung          Datenstand 30.08.2026 · … · 318 Buchungen   sha 7e5d3ec35b6de48f
Nachtrag eines Junibelegs (2026-06-05) über scripts/ledger_add.py    rc 0
Seite danach             Datenstand 30.08.2026 · … · 318 Buchungen   sha 7e5d3ec35b6de48f
nach erneutem Lauf       Datenstand 30.08.2026 · … · 319 Buchungen   sha e34e380cbcd0c096
```

Der Kopf ist **byte-identisch**; erst der erneute Lauf ändert die Buchungszahl. `ABOUT.txt` und die
H117-Begrenzung sagen das jetzt so.

### 8.6 Ränder (Befunde N8, N9)

```
2026 - Kopie.csv in ledger/   Generator rc 0, Seite: Hinweiskasten „Nicht gelesen" +
                              Zeile in der Quellenliste, Wortlaut von ledger_add.validate_file;
                              Stempel bleibt „gültig" (die Summen kommen aus den Jahresdateien)
ohne PyYAML                   rc 1, kein Traceback,
                              „[finance_dashboard] cannot read …: PyYAML is missing … pip install
                              -r requirements-office.txt"
ohne scripts/ (Nachbarfall)   rc 1  — dieselbe Form, derselbe Code
```

Der Prüfbericht verlangte für den PyYAML-Fall rc 2. Gewählt ist **rc 1**, weil die Verweigerung
daneben in derselben Datei rc 1 ist (oben gemessen) und der Kopfkommentar des Generators „Exit 1
only when nothing could be written" sagt; zwei Codes für zwei Formen derselben Sache wären eine
zweite Regel. Abweichung benannt, nicht stillschweigend.

### 8.7 Sicht-Schleife neu (BUG-0076)

98 Bilder aus dem gebauten Stand, fünf Zustände (`regular`, `empty`, `alarm`, `crossyear`,
`founding`), Konsolen-/Seitenfehler: **0** (`review-build/render.json`). Überblick und EÜR
zusätzlich bei 390 px dunkel, weil die drei Zeilen dort am ehesten anstoßen.

Angesehen (nicht nur erzeugt): `crossyear-ueberblick-1280`, `crossyear-ueberblick-390`,
`crossyear-euer-1280-dark`, `regular-ueberblick-1280`, `regular-euer-390-dark`,
`founding-kleinunternehmer-1280`, `alarm-ueberblick-1280`.

**Ein Befund aus der Sichtung, korrigiert und nachgerendert:** „1 **Mahnkandidaten**" — dieselbe
Klasse wie „1 Rechnungen" eine Runde zuvor, diesmal in der Hälfte, die das Seitenskript schreibt.
Beide Schreibweisen kommen jetzt aus dem Generator (`data-one`/`data-many`), das Skript wählt nur.

**Der Falz bei 390 px, gemessen** (Viewport 844, gleiche Fixture vor und nach der Änderung):

```
                       KPI-Block endet   erste Buchung
vorher   regular       y=658             y=1381
nachher  regular       y=773             y=1581
nachher  crossyear     y=776             y=1579
nachher  alarm         y=1026            y=1921   (der Ungültig-Kasten steht darüber)
```

Die drei Kennzahlen bleiben also bei 390 px vollständig über dem Falz (773 < 844); die erste
Buchung stand schon vorher darunter und rückt um 200 px weiter nach unten. Der Reiter EÜR hat bei
390 px einen **waagerechten** Überlauf auf 456 px — er ist **nicht** neu und kommt nicht von den
neuen Zeilen: vor und nach der Änderung derselbe Wert, breitester Knoten beide Male
`table.ledger.cats` (die Kategorientabelle). Steht als Rest für die Merge-Runde.

## 9. Nacharbeit 2 (zweiter Prüfbericht: 2 blockierende, 3 mittlere, 5 niedrige Befunde)

Läufe unter `_round-scratch/TSK-0109/rework2/`. Die Instrumente des Prüfers (`verify-3/rig/`)
wurden gefahren, nicht nachgebaut; `pristine.py` bestätigte vor der Arbeit, dass sein Baum und der
Arbeitsbaum byte-gleich waren (`differences: 0`).

### 9.1 B1 — jede Schreibweise außer `true` war Regelbesteuerung

`l_spellings.py` gegen die Fixture `regular` (Einnahmen als `kleinunternehmer` gebucht, Ausgaben
als `standard`, 19 %):

```
                       VORHER                                    NACHHER
true (baseline)        keine USt — Kleinunternehmer § 19 UStG     keine USt — Kleinunternehmer § 19 UStG
yes                    keine USt — Kleinunternehmer § 19 UStG     Steuerstatus nicht belastbar
quoted "true"          −6.077,56 €                                Steuerstatus nicht belastbar
Ja                     −6.077,56 €                                Steuerstatus nicht belastbar
missing tax: block     −6.077,56 €                                Steuerstatus nicht belastbar
```

(`yes` wechselt die Seite, weil YAML es als Bool liest — es war vorher zufällig richtig und ist
jetzt aus demselben Grund richtig wie alle anderen: nur `True`/`False` sind eine Antwort.)

Und die Milderung war am falschen Ort: `m_quoted.py` zeigte für `"true"` einen Überblick **ohne
jeden Hinweis** — der Satz „Steuerstatus nicht hinterlegt" hing an `is None` und stand nur auf dem
versteckten Kleinunternehmer-Reiter. Jetzt steht der Grund auf **jedem Reiter, der Kennzahlen
zeigt** (im Test aus der Seite abgeleitet: eine Ansicht mit `data-figure` trägt ihn) und in der
Liste „Jetzt ansteht".

### 9.2 B2 — die Zahl, die es nicht geben darf, stand ein zweites Mal auf derselben Seite

`b2_proof.py`/`f_reg_euer.py` gegen `regular`:

```
VORHER   Vereinnahmte USt (standard): 0,00 € · Vorsteuer (standard): 6.077,56 €
         · Zahllast: −6.077,56 € · Reverse-Charge-Belege (§ 13b): 9
         …vier Zeilen über dem Satz „es gibt keine Zahllast".
NACHHER  Vereinnahmte USt (standard): 0,00 € · Vorsteuer (standard): 6.077,56 €
         · Reverse-Charge-Belege (§ 13b): 9
         + „Diese zwei Zahlen stehen so im EÜR-Bericht; eine Zahllast folgt daraus in diesem
           Steuerzustand nicht (Grund oben), und in der Aufstellung oben sind sie nicht als USt
           geführt."
```

Der Bericht druckt **zwei** Zahlen: `grep -c Zahllast reports/euer_2026_Q1.md` → **0**. Das Etikett
„USt-Zahllast" fällt in diesem Zustand ebenfalls weg (es behauptet dasselbe wie die Zahl); die
Zeile heißt dort schlicht „USt" und trägt den Satz.

### 9.3 Rot-zuerst dieser Runde — 13 Defekte, 13 rote Läufe

Klon außerhalb des Repos (`rework2/clone/`), Werkzeug `rework2/redfirst.py`.

| # | eingesetzter Defekt | roter Test |
|---|---|---|
| B1a | `is not True` → Regelbesteuerung (der alte Durchfall) | `…boolean_answers…` (7 Fälle), `…agree…[regular-true/missing/null]`, `…three_lines…` (3) |
| B1b | die Milderung wieder an `is None` gehängt | `…boolean_answers…[true/yes/Ja/1/""]` |
| B1c | Blocknotiz immer die allgemeine Regel (auch wo keine Zahllast gedruckt wird) | `…three_lines…` (4 Fälle) |
| B2a | die Differenz wieder bedingungslos gedruckt | `…no_zahllast…`, `…agree…[regular ×4]` |
| B2b | Etikett „USt-Zahllast" wieder auf der Satzzeile | `…three_lines…` (4 Fälle) |
| M1 | beide `raise SystemExit(1)` → `SystemExit(0)` (`n9_mut.py`-Form) | `…a_missing_pyyaml…` |
| M3a | `limit_unknown=False` | `…threshold…[previous_unknown]` |
| M3b | Überblickssatz nennt nur eine Grenze | `…threshold…[previous_unknown]` |
| N1a | Quellenzeile immer im Plural | `…reads_right_at_one` |
| N1b | Kopfzeile immer „Buchungen" | `…reads_right_at_one` |
| N1c | das Seitenskript wählt immer die Mehrzahl | `…reads_right_at_one` |
| N5 | Ableitung wieder nur an `.py` **plus** zwei Kits mit abweichender `pages/index.html` | **grün** — die Blindstelle, gemessen |
| N5+ | dieselben zwei Kits, mit der neuen Ableitung | `test_shared_kit_files_identical` **rot** |

Grundlinie nach jedem Zurücksetzen: **40 passed**.

Die letzten zwei Zeilen sind **beide Enden** desselben Lochs: derselbe gepflanzte Drift ist mit der
alten Ableitung unsichtbar und mit der neuen rot.

### 9.4 M3 — der Balken, der der Aussage widersprach

`h_founding.py`/`i_gauge.py` gegen die Fixture `founding`:

```
VORHER   GAUGE[unknown] Vorjahr 2025   kein Ledger für 2025 (Grenze 25.000,00 €) — nicht belastbar
         GAUGE[]        Laufendes Jahr 2026  26.000,00 € von 100.000,00 €  26 %  Rest 74.000,00 €
         Überblick: „26.000,00 € von 100.000,00 € laufend"
NACHHER  GAUGE[unknown] Vorjahr 2025   kein Ledger für 2025 (Grenze 25.000,00 €) — nicht belastbar
         GAUGE[unknown] Laufendes Jahr 2026  26.000,00 € von einer Grenze, die noch nicht feststeht
                        — nicht belastbar — 25.000,00 € oder 100.000,00 €, je nach Gründungsjahr
         Überblick: „26.000,00 € von 100.000,00 € oder 25.000,00 €, je nach Gründungsjahr laufend"
```

Der Urteilssatz sagte bis dahin „dann ist der Balken … an der falschen Grenze gemessen" — er ist
mitgezogen, weil er nach dem Fix eine Beschreibung ohne Gegenstand war.

### 9.5 N2 — die Rechtsgrundlage, nachgelesen statt zitiert

Abgerufen am **2026-09-02** auf gesetze-im-internet.de:

* **§ 19 Abs. 1 UStG** (Fassung seit 1.1.2025): „Ein von einem im Inland … ansässigen Unternehmer
  bewirkter Umsatz im Sinne des § 1 Absatz 1 Nummer 1 ist **steuerfrei**, wenn der Gesamtumsatz
  nach Absatz 2 im vorangegangenen Kalenderjahr 25 000 Euro nicht überschritten hat …" — eine
  Steuerbefreiung, und der Vorsteuerabzug kommt darin **nicht** vor. Der Generator berief sich auf
  „§ 19 Abs. 1 UStG" — für den Vorsteuerausschluss die falsche Norm; ein „Satz 4", den der
  Prüfauftrag nannte, existiert in der geltenden Fassung ohnehin nicht.
* **§ 15 Abs. 2 Satz 1 Nr. 1 UStG**: vom Vorsteuerabzug ausgeschlossen ist die Steuer für Leistungen,
  die der Unternehmer für **steuerfreie Umsätze** verwendet.
* **§ 15 Abs. 3 UStG** nimmt einen Teil der steuerfreien Umsätze davon wieder aus — aber
  ausdrücklich nicht die des § 19: „Satz 1 gilt nicht für Umsätze, die auch unter Absatz 2 Satz 1
  Nummer 3 oder § 19 fallen."

Also: § 19 Abs. 1 befreit, § 15 Abs. 2 S. 1 Nr. 1 schließt den Vorsteuerabzug aus. Beide Stellen im
Generator (`money()`-Docstring und der Satz auf der Seite) tragen jetzt diese Kette.

### 9.6 Sichtung — jede Fixture, jeder Reiter, angesehen

98 Bilder, fünf Zustände, Konsolen-/Seitenfehler **0** (`review-build/render.json`).
**Angesehen** (nicht nur erzeugt) wurden diesmal 39 Bilder, nämlich jeder Reiter jeder Fixture bei
1280 plus der Lauf ohne Skript, dazu Überblick und EÜR bei 390 dunkel:

| Fixture | angesehen |
|---|---|
| `regular` | ueberblick, rechnungen, offene-posten, euer, kleinunternehmer, noscript (alle 1280); ueberblick-390-dark, euer-390-dark |
| `alarm` | dieselben acht |
| `crossyear` | ueberblick, rechnungen, offene-posten, euer, noscript (1280; kein Kleinunternehmer-Reiter, Profil `false`); ueberblick-390-dark, euer-390-dark |
| `founding` | dieselben acht wie `regular` |
| `empty` | dieselben acht wie `regular` |
| `unclear` | in der Politur-Runde dazugekommen: ueberblick, euer (1280); ueberblick-390-dark, euer-390-dark |

Der Grund für die Regel steht in der Sache selbst: „1 Buchungen" stand in
`founding-ueberblick-1280.png` der letzten Runde, das Bild war gerendert und niemand hat es
angesehen. Diese Runde ist der Befund N1 daraus.

### 9.7 Läufe

- `tools/test_finance_dashboard.py`: **40 passed** (16 → 19 Testfunktionen, 40 Fälle).
- `tools/test_repo_hygiene.py`: **9 passed**.
- `tools/test_hooks.py -k "office or dashboard or kit_owned or mirror or shared_kit"`:
  **37 passed** (6:56). **Die Auswahl der Nacharbeit 1 war zu eng**, und das ist gegen den Baum
  nachgezählt: die alte Auswahl sammelt hier 35 Tests, die neue 37, und die zwei Zusätzlichen sind
  `test_shared_kit_files_identical` — der einzige Test, den diese Arbeit in `test_hooks.py`
  ändert — sowie `test_preset_parser_changes_every_shared_kit_hash`. Die „35 passed" der
  Nacharbeit 1 waren also 35 richtige Läufe ohne den einen, auf den es ankam. (Der Prüfbericht
  nennt für dieselbe alte Auswahl 31; nachgezählt sind es auf diesem Baum 35 — der Befund selbst,
  dass der geänderte Test fehlt, ist davon unberührt und bestätigt.)
- `.claude/hooks/test_gates.py -k "hole or measurement or reference"` in einer Kopie: **8 passed** (6:52).
- `python -m ruff check .`, `python tools/validate.py`: sauber.
- Ein Zwischenlauf ohne Stempel meldete zwei rote Tests
  (`test_the_shipped_scaffold_records_the_trays_of_the_kit_it_installs`, beide Schalen) mit der
  Meldung „does not hash to the `content:` in its own VERSION" — das ist die Hausregel „erst
  stempeln, dann urteilen", kein Befund; nach `bump_kit_version.py` (Stempel **-15**) grün.

## 10. Politur (nach dem PASS: sechs N-Reste)

| Rest | Was gemessen/geändert wurde | rot ohne Fix |
|---|---|---|
| N1 | die Behauptung „ein ‚Satz 4', auf den sich der Generator berief" war selbst falsch — der Generator berief sich auf „§ 19 Abs. 1 UStG" (grep über die Nacharbeit-1-Fassung: 0 Treffer „Satz", vier Treffer „§ 19 Abs. 1 UStG"); der „Satz 4" stammt aus dem Prüfauftrag. Satz in 9.5 ersetzt | — |
| N2 | sechste Fixture `unclear` (Profil `kleinunternehmer: "true"`, Ledger von `regular`): der Zustand „unbekannt" **mit** Kennzahlen daneben hatte bis dahin kein Bild. Gerendert, angesehen — und dabei sofort ein Befund: derselbe lange Satz stand zweimal auf dem Überblick (Regelnotiz **und** „Jetzt ansteht"). Die Liste dort ist jetzt kurz und verweist nach oben | (Sichtbefund) |
| N3 | der Plural-Test war auf `-en` und auf `founding` beschränkt; jetzt eine Ableitung über **alle** Fixtures: die Paare kommen aus den `plural(...)`-Aufrufen (AST), aus den Label-Tupeln und aus `data-one`/`data-many` der Seite, ein Wort nach einer „1" muss ein Singular sein oder als unveränderlich im Korpus belegt | P1 (die Prüfer-Mutation `mut_n1b`), P2, P3, P4 |
| N4 | Zahlwörter aus drei Kommentaren gestrichen (`FOUR cases`, `FOUR verdicts, not three`, `the fourth case`) — sie waren schon einmal überholt worden; die Fälle stehen jetzt benannt statt gezählt | — |
| N5 | Backtick `vat_statement` → `vat_line_text` (das Symbol gibt es nicht mehr) | — |
| N6 | „… je nach Gründungsjahr laufend, Vorjahr: …" → „… — laufendes Jahr 26.000,00 € von 100.000,00 € oder 25.000,00 €, je nach Gründungsjahr; Vorjahr: keine Ledgerdatei für 2025" | — |
| Randnotiz | `_as_written` druckte Container als Python-`repr` (`[True]`); jetzt die Schreibweise der Datei: ein String in Anführungszeichen, eine Liste „eine Liste", eine Zuordnung „eine Zuordnung" | P0 |

Rot-zuerst dieser Runde: **5 Mutationen, 5 rote Läufe** (`rework2/redfirst.py`, Fälle P0–P4);
Grundlinie **42 passed**. P1 ist die Mutation des Prüfers (`verify-4/rig/mut_n1b.py`): sie ließ die
Suite vorher grün.

**Zwei Messfehler im Test selbst, beim Bauen der neuen Regel gefunden und behoben:** die kleine
DOM-Lesefunktion dieser Suite gibt den eigenen Text eines Knotens **vor** dem seiner Kinder zurück
und stellt damit Wörter nebeneinander, die kein Leser zusammen sieht („1 Ob" aus zwei benachbarten
Listenpunkten) — die Regel liest die Seite darum in Dokumentreihenfolge; und eine Rechtsnorm zählt
nichts, „§ 15 Abs. 2 Satz 1 Nr. 1" ist keine Mengenangabe.

Sichtung: **119 Bilder** aus sechs Zuständen, 0 Konsolen-/Seitenfehler; angesehen zusätzlich die
vier `unclear`-Bilder und der geänderte Überblick von `founding`.
