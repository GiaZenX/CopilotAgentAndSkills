# TSK-0122 — Nacharbeit zu Prüfrunde 2

Ergänzt `stream-protocol.md` und `rework-round-1.md`. Alle Zahlen gemessen; jede Mutation in einer
`.git`-losen Kopie unter `_round-scratch/TSK-0122/rig/copy-redfirst3`, vor der nächsten
zurückgesetzt.

## Rot-zuerst

| Befund | Test | sauber | mit dem wiederhergestellten Defekt |
|---|---|---|---|
| R1 (Kernel) | `tools/test_state.py::test_only_the_type_a_hole_is_can_be_captured_as_one` | rc 0 | **rc 1** |
| R1 (Prozess) | `tools/test_migrate_holes.py::test_only_a_hole_can_be_filed_as_one_from_the_command_surface` | rc 0 | **rc 1** |
| R2 | `tools/test_migrate_holes.py::test_an_empty_store_does_not_empty_a_full_index` | rc 0 | **rc 1** |

Die zweite Mutation stellt **genau den beanstandeten Defekt** wieder her — die Aufzählung von einem
(`if item_type == "TSK"`) an die Stelle der Ableitung — und der Prozess-Test wird rot.

## R1 (blockierend) — geschlossen

Der Befund war richtig und die Klasse trifft: eine Aufzählung von **einem** neben der Definition.

**Die Definition, die daneben lag, ist jetzt die Ableitung.** `backlog_types.hole_type()` liest den
Feldvertrag: **genau ein Typ** deklariert `HOLE_NUMBER_FIELD`, denn das ist, was „dieser Typ kann
eine Löchernummer tragen" heißt. Deklarieren zwei Typen es, bricht die Ableitung laut ab — das wäre
eine Vertragsentscheidung mit eigener DEC und keine Weitung, die eine Ableitung stillschweigend
schluckt.

**Die Verweigerung steht im Kernel, nicht in der CLI.** `state.assert_capturable_as_hole` wird an
zwei Stellen gefragt, und beide sind nötig:

- `state.capture` fragt sie für **jeden** Aufrufer;
- die CLI fragt sie **bevor** sie den Produzenten wählt, weil `capture TSK` gar nicht durch
  `state.capture` läuft (es geht durch `dispatch.create_task`) und das Flag dort sonst still
  ignoriert würde.

Die CLI trägt damit **keine eigene Regel** mehr. Auch `capture_migrated_hole` und
`required_fields_of` lesen jetzt `hole_type()` statt des Literals `"BUG"`.

**Gemessen als Prozess** (`capture <typ> --hole` als echter Kernel-CLI-Aufruf gegen einen Piloten):
`FR` → rc ≠ 0 mit „a hole is a BUG"; `DEC` → rc ≠ 0; `TSK` → rc ≠ 0; und **keine Nummer verbrannt**
(`next_hole_number()` bleibt `H1`). Vorher: `FR` → rc 0 `FR-0001 OPEN H3`, `DEC` → rc 0
`DEC-0001 VALID H4`.

## R2 — geschlossen

`migrate_holes._write_index` verweigert genau einen Fall: der Speicher trägt **kein** Loch und das
Dokument trägt welche. Das ist dieselbe Klasse wie die Nummernkollision — ein Verlust, den der Lauf
als Erfolg meldet.

**Die Regel ist eng gehalten und das andere Ende ist mitgemessen:** ein Index, der schrumpft, weil
ein Loch aus dem aktiven Bestand archiviert wurde, ist ein legitimer Neu-Schrieb und geht durch.
Der Test hält beide Enden.

## R3 — Satz korrigiert, Rest benannt

Der Befund ist präzise: der Code fragt den **Typ**, der Satz behauptete den **Wert**. Der Docstring
sagt jetzt „CAN an item of this type hold …" und nennt in einem eigenen Absatz, warum die Typebene
bleibt: ob die Kriterienliste an der Stelle gefüllt ist, beantwortet `validate_dispatch`, das jede
`acceptance_ref` gegen den Ursprung auflöst — eine zweite Prüfung hier wäre ein zweiter Leser
derselben Frage.

**Was die beiden zusammen nicht fangen**, steht als **zweite Restklasse in H155** mit der gemessenen
Kette (BUG mit `acceptance_criteria: []` → `architect_step_owed=False` → Haken rc 0) und der
Begrenzung.

## R4 — Protokollzahlen

Alle sechs benannten Stellen korrigiert; die Läufe sind auf den **letzten** Stand nachgemessen:

| Stelle | jetzt |
|---|---|
| Stempel | **2026.09.05-4** (nach dieser Nacharbeit erneut gestempelt) |
| Migration | **143 written / 143 prose files** |
| Dokumentzeilen | **2441** nach der Migration; das ausgelieferte Dokument hat **9300** |
| Einträge | **143** |
| Gate-Knoten über leerem Bestand | **sieben von sieben rot** |
| `rework-round-1.md` „9199 → 2441" | in diesem Bericht ersetzt durch die gemessenen Zahlen |

Die hartkodierte Zeile im Messskript (`m7_full_ac4.py`, „was 9199") ist entfernt: das Skript LIEST
die Zeilenzahl vor der Migration, statt sie zu tippen — genau die Klasse, die R4 benennt.

## R5 — Nahttabelle korrigiert

Die Kopfzahlen (18/10/5) waren richtig; die Aufschlüsselung ist ersetzt durch die vom Prüfer
nachgerechnete: **geändert** sind `_anchors`, `test_every_reference_to_a_measurement_leads_to_one`,
`test_every_check_this_apparatus_claims_in_its_own_prose_is_one_that_exists`,
`test_every_cell_a_closed_hole_names_is_one_the_table_carries` und
`test_every_tilde_subject_a_closed_hole_names_is_one_the_check_set_carries`. `TABLE_TEST`,
`TILDE_TEST`, `CELLS_RX` und `SUBJECTS_RX` sind **byte-identisch**; `OVER_REFUSAL_HOLE` ist **neu**
(der alte `OVER_REFUSAL_ENTRY` ist entfernt); `_assert_it_is_the_same_hole` gehört
`tools/migrate_holes.py` und nicht dieser Datei.

## R6, R7 — erledigt

- **R6** Der letzte Zähler der F14-Klasse („9 SRs against 120 work orders") ist aus
  `dispatch.py` entfernt; der Satz sagt jetzt, dass diese Messung der Runde gehört, die sie macht.
- **R7** Der `--hole`-Hinweis auf stderr nennt `--root <state> --reindex` ohne `--related-pr` —
  die Flagge, die derselbe Fix optional gemacht hat.

## Läufe nach dieser Nacharbeit

| Lauf | Ergebnis |
|---|---|
| Migration Ende zu Ende, frische Kopie ohne `.git` | **143 written / 143 prose files**, Dokument → 2441 Zeilen; zweiter Lauf **1,77 s, 0 written**, byte-identisch; `validate` **0 Fehler / 66 Warnungen** (= vorher) |
| Gate-Knoten `-k "hole or holes or _hole or reference_to_a_measurement"` gegen die migrierte Kopie | **7 passed** (150 s) |
| `tools/test_state.py test_backlog_types.py test_migrate_holes.py test_parallel_scopes.py test_parallel_streams.py test_report.py test_kernel.py` | **417 passed** (79 s) |
| `tools/test_approvals_dispatch.py` | **193 passed** (77 s) |
| `.claude/hooks/test_gates.py -k "claims_in_its_own_prose or names_only_code_that_exists"` | **2 passed** |
| `python -m ruff check .` | All checks passed |
| `python tools/validate.py` | all structural checks passed |

Stempel **2026.09.05-4**. Patch **4162 Zeilen, 18 Dateien**, ohne VERSION-Hunks.

## Zur Rücknahme von F13

Zur Kenntnis genommen: der Prüfer hat F13 aus Runde 1 zurückgezogen (sein grep war zu wörtlich).
Der Assertionstext und Abschnitt 7 des Protokolls sagen trotzdem weiterhin, dass der Lauf aus einer
Shell außerhalb von Claude Code kommt — das bleibt richtig und nützlich, unabhängig davon, dass der
ursprüngliche Befund keiner war.
